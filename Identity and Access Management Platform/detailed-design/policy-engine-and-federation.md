# Policy Engine & Federation Deep-Dive

## Part 1: Policy Engine

### 1.1 RBAC/ABAC Hybrid Evaluation Algorithm

The IAM Platform uses a hybrid model: roles provide coarse-grained access control and are always evaluated first (fast path), while attribute-based conditions refine or override role-derived permissions (slow path). An explicit `Deny` from any active policy always wins regardless of the evaluation order.

**Pseudocode:**

```
function evaluate(subject, action, resource, environment) -> Decision:

  // --- Phase 1: Build context ---
  roles        := resolveRoles(subject)          // direct + group-derived
  permissions  := resolvePermissions(roles)       // flattened from role_permissions
  subjectAttrs := resolveSubjectAttributes(subject)
  resourceAttrs := resolveResourceAttributes(resource)

  // --- Phase 2: Load active policies ---
  policies := loadActivePolicies(subject.tenant_id)  // from cache or DB
  statements := flattenStatements(policies)           // sorted by priority ASC

  // --- Phase 3: RBAC short-circuit (no ABAC conditions) ---
  if action in permissions AND noConditionedDenyExists(statements, subject, action, resource):
    return Decision{
      result:     "Allow",
      reason:     "RBAC permission match",
      matched:    [],
      obligations: collectObligations(statements, subject, action, resource, "Allow")
    }

  // --- Phase 4: Full ABAC evaluation ---
  allowed    := []
  denied     := []
  applicable := []

  for stmt in statements:
    if not principalMatches(stmt.principals, subject, roles):
      continue
    if not actionMatches(stmt.actions, action):
      continue
    if not resourceMatches(stmt.resources, resource):
      continue

    condResult := evaluateConditions(stmt.conditions, subjectAttrs, resourceAttrs, environment)

    if condResult == INDETERMINATE:
      if stmt.effect == "Deny":
        // Indeterminate Deny on a privileged action: fail closed
        return Decision{result: "Deny", reason: "Indeterminate condition on Deny statement", matched: [stmt.statement_id]}
      // Indeterminate Allow: skip statement, do not count as match
      continue

    if condResult == TRUE:
      applicable = append(applicable, stmt)
      if stmt.effect == "Deny":
        denied = append(denied, stmt)
      else:
        allowed = append(allowed, stmt)

  // --- Phase 5: Deny-overrides combination ---
  if len(denied) > 0:
    return Decision{
      result:     "Deny",
      reason:     "Explicit Deny statement matched",
      matched:    map(denied, s => s.statement_id),
      obligations: []
    }

  if len(allowed) > 0:
    return Decision{
      result:     "Allow",
      reason:     "ABAC Allow statement matched",
      matched:    map(allowed, s => s.statement_id),
      obligations: collectObligations(allowed, subject, action, resource, "Allow")
    }

  // --- Phase 6: Default deny ---
  return Decision{
    result:  "Deny",
    reason:  "No applicable Allow statement found",
    matched: []
  }
```

**Key design decisions:**

- **Priority ordering:** Statements are sorted by ascending `priority` integer. Lower numbers are evaluated first, giving operators control over short-circuit behavior for common-case statements.
- **Indeterminate fail-closed:** If a condition evaluation throws an error (e.g., resource attribute service unavailable) and the statement effect is `Deny`, the overall decision is `Deny`. If the effect is `Allow`, the statement is skipped, and evaluation continues.
- **RBAC short-circuit:** Before running the full ABAC loop, the engine checks whether the flattened role permission set covers the requested action and no conditioned `Deny` exists. This keeps the common case at sub-5ms.
- **Group expansion:** `resolveRoles` performs a breadth-first traversal of `group_members` → `group_roles` and merges with direct `user_roles`. The result is cached per-request.

---

### 1.2 Policy Statement JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://api.iam-platform.example.com/schemas/policy-statement.json",
  "title": "PolicyStatement",
  "type": "object",
  "required": ["statementId", "effect", "actions", "resources"],
  "additionalProperties": false,
  "properties": {
    "statementId": {
      "type": "string",
      "pattern": "^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$",
      "description": "Human-readable label; unique within a policy. Used in audit traces."
    },
    "effect": {
      "type": "string",
      "enum": ["Allow", "Deny"],
      "description": "Whether this statement grants or denies the specified actions."
    },
    "principals": {
      "type": "array",
      "description": "List of principal selectors. Omit or use ['*'] to match all principals in the tenant.",
      "items": {
        "type": "string",
        "examples": [
          "user:3fa85f64-5717-4562-b3fc-2c963f66afa6",
          "role:admin",
          "group:engineering",
          "service_account:ci-deploy-bot",
          "*"
        ]
      },
      "minItems": 1
    },
    "actions": {
      "type": "array",
      "description": "List of action selectors. Wildcards supported: 'documents:*', '*'.",
      "items": {
        "type": "string",
        "pattern": "^[a-z0-9_*]+:[a-z0-9_*]+$"
      },
      "minItems": 1
    },
    "resources": {
      "type": "array",
      "description": "List of resource selectors. ARN-style or '*' for all.",
      "items": {
        "type": "string",
        "examples": [
          "arn:iam:documents:*",
          "arn:iam:documents:doc-123",
          "*"
        ]
      },
      "minItems": 1
    },
    "conditions": {
      "type": "object",
      "description": "Optional map of condition operators to condition keys and values.",
      "additionalProperties": {
        "type": "object",
        "additionalProperties": true
      },
      "examples": [
        {
          "StringEquals": { "subject.department": "Engineering" },
          "IpAddress": { "environment.ip": ["10.0.0.0/8", "172.16.0.0/12"] }
        }
      ]
    },
    "obligations": {
      "type": "array",
      "description": "List of obligations that must be fulfilled when this statement matches and is applicable.",
      "items": {
        "$ref": "#/$defs/obligation"
      }
    },
    "priority": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10000,
      "default": 100,
      "description": "Evaluation order within the policy. Lower values are evaluated first."
    }
  },
  "$defs": {
    "obligation": {
      "type": "object",
      "required": ["type"],
      "additionalProperties": false,
      "properties": {
        "type": {
          "type": "string",
          "enum": ["log_access", "notify_owner", "require_audit_trail",
                   "watermark_document", "rate_limit", "require_justification"]
        },
        "params": {
          "type": "object",
          "additionalProperties": true
        }
      }
    }
  }
}
```

---

### 1.3 Condition Operators Reference

| Operator | Operand Types | Description | Example |
|---|---|---|---|
| `StringEquals` | string | Exact string match (case-sensitive) | `{"StringEquals": {"subject.department": "Legal"}}` |
| `StringNotEquals` | string | Exact string non-match | `{"StringNotEquals": {"subject.status": "suspended"}}` |
| `StringEqualsIgnoreCase` | string | Case-insensitive exact match | `{"StringEqualsIgnoreCase": {"resource.region": "us-east-1"}}` |
| `StringLike` | string | Glob pattern match (`*` and `?` supported) | `{"StringLike": {"subject.email": "*@example.com"}}` |
| `StringNotLike` | string | Negated glob pattern | `{"StringNotLike": {"resource.name": "tmp-*"}}` |
| `NumericEquals` | number | Exact numeric equality | `{"NumericEquals": {"subject.assurance_level": 2}}` |
| `NumericGreaterThan` | number | Numeric greater-than | `{"NumericGreaterThan": {"resource.file_size_mb": 100}}` |
| `NumericLessThanEquals` | number | Numeric less-than-or-equal | `{"NumericLessThanEquals": {"subject.failed_login_count": 0}}` |
| `DateEquals` | ISO 8601 | Exact date match | `{"DateEquals": {"environment.date": "2025-01-15"}}` |
| `DateLessThan` | ISO 8601 | Date before the given value | `{"DateLessThan": {"environment.time": "2025-12-31T23:59:59Z"}}` |
| `DateGreaterThan` | ISO 8601 | Date after the given value | `{"DateGreaterThan": {"subject.created_at": "2024-01-01T00:00:00Z"}}` |
| `Bool` | boolean | Boolean equality | `{"Bool": {"subject.mfa_verified": true}}` |
| `IpAddress` | CIDR list | IP address is within any of the listed CIDR ranges | `{"IpAddress": {"environment.ip": ["10.0.0.0/8"]}}` |
| `NotIpAddress` | CIDR list | IP address is outside all listed CIDR ranges | `{"NotIpAddress": {"environment.ip": ["203.0.113.0/24"]}}` |
| `ArnEquals` | ARN string | Exact ARN match | `{"ArnEquals": {"resource.arn": "arn:iam:documents:doc-secret"}}` |
| `ArnLike` | ARN glob | ARN glob pattern | `{"ArnLike": {"resource.arn": "arn:iam:documents:*"}}` |
| `SetContains` | array | Subject/resource attribute set contains all specified values | `{"SetContains": {"subject.groups": ["finance", "compliance"]}}` |
| `SetIntersects` | array | Subject/resource attribute set contains at least one specified value | `{"SetIntersects": {"subject.roles": ["admin", "super_admin"]}}` |
| `Null` | boolean | Checks whether the attribute key is present (false = present, true = absent) | `{"Null": {"subject.department": false}}` |

Conditions within the same statement are combined with logical **AND**. Multiple values in a single condition key are combined with logical **OR** (i.e., "any of these values matches").

---

### 1.4 Policy Evaluation Algorithm — Step by Step

1. **Context assembly:** Build the evaluation context from the inbound request: `subject` (user/service-account ID, resolved roles, profile attributes), `action` (e.g., `documents:delete`), `resource` (type, ID, owner, metadata), `environment` (IP, timestamp, client ID, assurance level).

2. **Policy bundle load:** Load all `active` policies for the tenant from the PolicyCache (Redis). On cache miss, query PostgreSQL and populate the cache with the compiled bundle. The bundle key is `sha256(tenant_id + sorted(policy_ids + versions))`.

3. **Statement flattening:** Merge all `policy_statements` across all active policies into a single ordered list, sorted by ascending `priority`. Statements from the same priority tier are evaluated in `policy_id` lexicographic order for determinism.

4. **Principal matching:** For each statement, check whether any principal selector in `principals` matches the subject. Selectors are matched as follows:
   - `*` matches any principal.
   - `user:<uuid>` matches exact user ID.
   - `role:<name>` matches if the role is in the subject's effective role set.
   - `group:<name>` matches if the subject is a member of the group.
   - `service_account:<name>` matches by service account name.

5. **Action matching:** Check whether the requested action matches any selector in `actions`. The `*` wildcard matches all characters; `documents:*` matches any action in the `documents` namespace.

6. **Resource matching:** Check whether the requested resource ARN matches any selector in `resources`. Glob matching is applied.

7. **Condition evaluation:** Evaluate all condition blocks using the operators table above. Each attribute key is resolved against `subjectAttrs`, `resourceAttrs`, or `environmentAttrs` based on its prefix (`subject.`, `resource.`, `environment.`). Unknown attribute keys return `Null = true` (the attribute is absent).

8. **Combination (Deny-overrides):** After iterating all applicable statements, if any `Deny` statement matched, the final decision is `Deny`. If only `Allow` statements matched, the decision is `Allow`. If no statement matched, the decision is `Deny` (default-deny).

9. **Obligation collection:** For each matched `Allow` statement, collect all `obligations` items. Dispatch them asynchronously via the ObligationHandler.

10. **Explain trace construction:** Produce a structured trace listing: matched statement IDs, condition evaluation results (per key), decision, obligations, and total evaluation duration in milliseconds.

---

### 1.5 Policy Bundle Lifecycle

```
draft ──► review ──► approved ──► active ──► deprecated
  │                                              ▲
  └──────────────────────────────────────────────┘
                    (re-draft via new version)
```

| Status | Description | Who Can Transition | Allowed Operations |
|---|---|---|---|
| `draft` | Being authored; not evaluated | Policy author | Edit, add/remove statements, delete |
| `review` | Submitted for peer review | Policy author | Read only; reviewer may comment |
| `approved` | Reviewed and approved | Policy reviewer (separate from author) | Activate |
| `active` | Evaluated against all real decisions | Tenant admin | Deactivate (→ deprecated) |
| `deprecated` | Retired; not evaluated | System | Read only; archive |

**Rules:**
- Only one version of a named policy can be `active` at any time per tenant.
- Activation of a new version atomically deprecates the previous active version.
- `approved → active` transition flushes the policy cache for the tenant and publishes a `PolicyActivated` event.
- A `draft` with open simulation failures blocks the `review` transition.
- System-managed policies (`is_system = true`) cannot be modified or deleted by tenant admins.

---

### 1.6 Obligation Types Reference

| Type | Fulfillment | Parameters | Description |
|---|---|---|---|
| `log_access` | Synchronous (before response) | `level: "info" \| "warn" \| "critical"` | Record an access log entry with full context in the audit stream |
| `require_audit_trail` | Synchronous (gate) | `reason_required: bool` | Block the action until the caller supplies a `X-Access-Reason` header |
| `notify_owner` | Async | `channels: ["email", "slack"]` | Send notification to resource owner(s) |
| `watermark_document` | Async | `watermark_text: string` | Embed a user-specific watermark on document download |
| `rate_limit` | Synchronous (gate) | `requests: int, window_seconds: int` | Apply an additional per-principal rate limit for this resource |
| `require_justification` | Synchronous (gate) | `min_length: int` | Require a free-text justification in the request body field `justification` |

---

## Part 2: Federation

### 2.1 SAML 2.0 Assertion Processing Pipeline

```
IdP POST Assertion
       │
       ▼
┌─────────────────────────────┐
│ 1. HTTP Binding Parse        │  Decode base64, inflate (deflate encoding), parse XML
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 2. Signature Validation      │  Verify XMLDSig over <samlp:Response> or <saml:Assertion>
│                              │  Validate X.509 cert matches pinned provider certificate
│                              │  Verify certificate chain and expiry
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 3. Structural Validation     │  Require: Issuer, NameID, AuthnStatement, AudienceRestriction
│                              │  Verify Issuer == provider.entity_id
│                              │  Verify Audience contains this SP's entity ID
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 4. Temporal Validation       │  NotBefore - 5min <= NOW <= NotOnOrAfter + 5min (clock skew)
│                              │  AuthnInstant must be within 15 minutes of NOW
│                              │  SessionNotOnOrAfter enforced if present
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 5. Replay Prevention         │  Check InResponseTo == stored AuthnRequest ID (SP-initiated)
│                              │  Store Assertion ID in nonce cache (Redis) with TTL = NotOnOrAfter
│                              │  Reject if Assertion ID already present in nonce cache
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 6. Attribute Extraction      │  Extract NameID value and Format
│                              │  Extract configured attribute statements
│                              │  Apply provider.attribute_mappings to normalize to internal schema
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 7. Identity Linking          │  Look up user by (tenant_id, mapped_email or external_id)
│                              │  JIT provision if: provider allows JIT + user not found
│                              │  Reject if account status != active
└─────────────┬───────────────┘
              │
              ▼
   Session created; tokens issued
```

**Error handling:** Any failure in steps 2–6 returns HTTP 403 with a SAML-specific error code and is written to the audit log. The error message shown to the end user contains only a correlation ID to prevent information leakage.

---

### 2.2 OIDC Token Validation Pipeline

```
Authorization Code / ID Token received
              │
              ▼
┌─────────────────────────────┐
│ 1. JWKS Key Retrieval        │  Fetch JWKS from provider.jwks_uri
│                              │  Cache keyset with max-age from Cache-Control header
│                              │  On `kid` not found: force-refresh once (rotation detection)
│                              │  Fail if kid still missing after refresh
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 2. Signature Verification    │  Select key by `kid` header from JWKS
│                              │  Supported algorithms: RS256, RS384, RS512, ES256, ES384
│                              │  Reject HS256 and `alg:none` unconditionally
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 3. Claims Validation         │  iss == provider.issuer (exact match)
│                              │  aud contains this client_id (or is a string equal to it)
│                              │  exp > NOW (reject expired tokens)
│                              │  iat <= NOW + 60s (reject far-future tokens)
│                              │  nonce == stored nonce (if authorization_code flow)
│                              │  at_hash present and valid (if access token accompanies ID token)
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 4. Claim Mapping             │  Apply provider.claim_mappings to extract identity attributes
│                              │  Map to internal user schema (email, display_name, external_id)
│                              │  Validate required mapped claims are present and non-empty
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 5. Identity Linking          │  Identical to SAML step 7
└─────────────────────────────┘
```

---

### 2.3 JWT Claim Mapping Configuration

Claim mapping rules are stored per OIDC/SAML provider in `saml_providers.attribute_mappings` and `oauth_clients.metadata`. The schema below defines the mapping rule format.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://api.iam-platform.example.com/schemas/claim-mapping.json",
  "title": "ClaimMappingConfiguration",
  "type": "object",
  "required": ["version", "rules"],
  "properties": {
    "version": {
      "type": "integer",
      "enum": [1],
      "description": "Schema version for forward compatibility."
    },
    "rules": {
      "type": "array",
      "description": "Ordered list of claim mapping rules. First matching rule wins.",
      "items": {
        "type": "object",
        "required": ["source_claim", "target_attribute"],
        "additionalProperties": false,
        "properties": {
          "source_claim": {
            "type": "string",
            "description": "JWT claim name or SAML attribute name (e.g., 'email', 'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress')."
          },
          "target_attribute": {
            "type": "string",
            "enum": ["email", "display_name", "external_id", "department",
                     "job_title", "phone_number", "locale", "groups", "custom"],
            "description": "Internal user attribute to populate."
          },
          "custom_attribute_key": {
            "type": "string",
            "description": "Required when target_attribute is 'custom'. Key in user.profile JSONB."
          },
          "transform": {
            "type": "string",
            "enum": ["none", "lowercase", "uppercase", "trim",
                     "extract_domain", "split_first", "split_last"],
            "default": "none",
            "description": "Optional transformation applied to the source value before mapping."
          },
          "required": {
            "type": "boolean",
            "default": false,
            "description": "If true, the assertion is rejected when this claim is missing."
          },
          "default_value": {
            "type": "string",
            "description": "Value to use when the source claim is absent and required is false."
          }
        }
      }
    },
    "jit_provisioning": {
      "type": "object",
      "description": "Controls Just-in-Time user provisioning from this provider.",
      "properties": {
        "enabled": { "type": "boolean", "default": false },
        "default_roles": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Role names to assign to JIT-provisioned users."
        },
        "default_org_id": {
          "type": "string",
          "format": "uuid",
          "description": "Organization to place JIT-provisioned users in."
        },
        "update_on_login": {
          "type": "boolean",
          "default": true,
          "description": "Re-apply mapped attribute values on every login."
        }
      }
    }
  }
}
```

**Example claim mapping for Azure AD SAML:**

```json
{
  "version": 1,
  "rules": [
    {
      "source_claim": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
      "target_attribute": "email",
      "transform": "lowercase",
      "required": true
    },
    {
      "source_claim": "http://schemas.microsoft.com/identity/claims/displayname",
      "target_attribute": "display_name",
      "transform": "trim",
      "required": true
    },
    {
      "source_claim": "http://schemas.microsoft.com/ws/2008/06/identity/claims/groups",
      "target_attribute": "groups",
      "required": false
    },
    {
      "source_claim": "department",
      "target_attribute": "custom",
      "custom_attribute_key": "department",
      "transform": "none"
    }
  ],
  "jit_provisioning": {
    "enabled": true,
    "default_roles": ["viewer"],
    "update_on_login": true
  }
}
```

---

### 2.4 Federation Trust Chain

#### Certificate Pinning Strategy

Every SAML provider and OIDC provider stores a `certificate_pem` (SAML) or a pinned JWKS fingerprint (OIDC). These are set at configuration time and must be explicitly rotated by a tenant admin with the `saml_providers:update` or `oauth_clients:update` permission.

- **SAML:** The SP validates the assertion signature against the exact DER-encoded certificate stored in `saml_providers.certificate_pem`. Certificate chain validation (CA → leaf) is performed but is not sufficient alone — the leaf certificate must match the pinned value.
- **OIDC:** The SP fetches the JWKS from the discovery document. The `kid` field identifies the active key. If the provider rotates keys, the new key must have a different `kid`; the platform forces a JWKS refresh on unknown `kid`.

#### Metadata Refresh Schedule

| Protocol | Refresh Interval | Pre-Expiry Alert | Emergency Disable |
|---|---|---|---|
| SAML metadata URL | Every 24 hours | 30 days before certificate expiry | `PATCH /saml/providers/{id}` sets `status = inactive` |
| OIDC discovery | Every 60 minutes | N/A (JWKS keys have no fixed expiry) | `PATCH /oauth/clients/{id}` sets `status = suspended` |

**Overlap window:** When a provider rotates its signing certificate, both the old and new certificates are accepted for a 48-hour overlap window. The operator must upload the new certificate to the provider configuration before the old one expires. After the overlap window closes, the old certificate is rejected.

#### Trust Downgrade Prevention

- The platform will not lower the required assurance level for an existing federation connection without explicit admin confirmation and an audit event.
- If the IdP metadata is unreachable at refresh time, the connection enters `status = error` and login via that provider is blocked after a 1-hour grace period. A `FederationMetadataRefreshFailed` alert is sent to `saml_providers.contact_email`.
- Partial trust (e.g., expired cert but valid signature) is treated as a hard failure — the platform does not accept degraded trust chains.

---

### 2.5 SCIM Schema Mapping

#### SCIM 2.0 User Schema → Internal User Model

| SCIM Attribute | SCIM Type | Internal Field | Notes |
|---|---|---|---|
| `id` | string | `user_id` | SCIM ID is set to `user_id` UUID |
| `externalId` | string | `external_id` | IdP-assigned identifier |
| `userName` | string | `email` | Must be a valid email address |
| `name.formatted` | string | `display_name` | Used if `displayName` absent |
| `displayName` | string | `display_name` | Preferred over `name.formatted` |
| `emails[primary=true].value` | string | `email` | Authoritative email |
| `active` | boolean | `status` | `true → active`, `false → suspended` |
| `phoneNumbers[primary=true].value` | string | `profile.phone_number` | Stored in JSONB profile |
| `title` | string | `profile.job_title` | Stored in JSONB profile |
| `department` (enterprise) | string | `profile.department` | Enterprise schema extension |
| `organization` (enterprise) | string | `org_id` | Resolved by name lookup |
| `manager.value` (enterprise) | string | `profile.manager_id` | Stored in JSONB profile |
| `meta.created` | dateTime | `created_at` | Read-only; set by platform |
| `meta.lastModified` | dateTime | `updated_at` | Read-only; set by platform |

#### SCIM 2.0 Group Schema → Internal Group Model

| SCIM Attribute | SCIM Type | Internal Field | Notes |
|---|---|---|---|
| `id` | string | `group_id` | SCIM ID is set to `group_id` UUID |
| `externalId` | string | — | Stored in `groups.metadata.external_id` |
| `displayName` | string | `name` | |
| `members[].value` | string | `group_members.user_id` | Bulk-synced; ADD/REMOVE operations |
| `members[].display` | string | — | Not stored; derived on read |
| `meta.created` | dateTime | `created_at` | Read-only |
| `meta.lastModified` | dateTime | `updated_at` | Read-only |

#### Custom Attribute Extension Schema

The platform defines the extension schema `urn:ietf:params:scim:schemas:extension:iam:2.0:User` for IAM-specific attributes not covered by RFC 7643.

```json
{
  "id": "urn:ietf:params:scim:schemas:extension:iam:2.0:User",
  "name": "IAMUser",
  "description": "IAM Platform extensions to the SCIM 2.0 User schema.",
  "attributes": [
    {
      "name": "mfaRequired",
      "type": "boolean",
      "multiValued": false,
      "description": "Whether MFA is required for this user at login.",
      "required": false,
      "mutability": "readWrite",
      "returned": "default"
    },
    {
      "name": "assuranceLevel",
      "type": "integer",
      "multiValued": false,
      "description": "Minimum assurance level (1–3) required for this user's sessions.",
      "required": false,
      "mutability": "readWrite",
      "returned": "default"
    },
    {
      "name": "sourceDirectory",
      "type": "string",
      "multiValued": false,
      "description": "Identifier of the SCIM directory that manages this user.",
      "required": false,
      "mutability": "readOnly",
      "returned": "default"
    },
    {
      "name": "roles",
      "type": "complex",
      "multiValued": true,
      "description": "Role assignments managed via SCIM. Each value is a role name.",
      "required": false,
      "mutability": "readWrite",
      "returned": "request",
      "subAttributes": [
        { "name": "value", "type": "string" },
        { "name": "expiresAt", "type": "dateTime" }
      ]
    }
  ]
}
```

#### Attribute Source-of-Truth Matrix

| Attribute | Source of Truth | SCIM Can Write | IAM API Can Write | Notes |
|---|---|---|---|---|
| `email` | SCIM directory | Yes | No (if SCIM-managed) | IAM blocks email change if `source_directory` is set |
| `display_name` | SCIM directory | Yes | No (if SCIM-managed) | Same ownership rule |
| `status` | IAM Platform | No (direct write) | Yes | SCIM `active=false` triggers IAM suspension via event |
| `profile.department` | SCIM directory | Yes | No (if SCIM-managed) | |
| `profile.job_title` | SCIM directory | Yes | No (if SCIM-managed) | |
| `mfa_required` | IAM Platform | Via extension | Yes | SCIM extension attribute write is allowed |
| `roles` | IAM Platform | Via extension | Yes | SCIM role sync is additive; removals require IAM API |
| `external_id` | SCIM directory | On create only | No | Immutable after first set |
| `org_id` | IAM Platform | No | Yes | Organization assignment is IAM-only |

**Ownership rule:** When `users.source_directory` is set, the SCIM directory is the authoritative source for all profile attributes listed as "SCIM Can Write = Yes". Direct writes to those attributes via the IAM Users API are rejected with `USER_007 - Attribute managed by SCIM directory`. Drift reconciliation runs every 15 minutes and emits correction events for any attributes modified outside their authoritative source.
