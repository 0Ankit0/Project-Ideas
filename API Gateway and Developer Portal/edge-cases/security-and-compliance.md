# Edge Cases: Security and Compliance

## Overview

This document catalogues critical security and compliance edge cases for the API Gateway and
Developer Portal. The platform enforces authentication via HMAC-SHA256 API keys and OAuth 2.0 with
JWT bearer tokens. Infrastructure-level protection is provided by AWS WAF and CloudFront at the
edge. Data privacy obligations include GDPR for EU consumers and configurable regional data residency
requirements for enterprise accounts.

Security edge cases in this domain fall into three broad categories:

1. **Availability attacks** — WAF misconfiguration, DDoS patterns, and downgrade attacks that cause
   legitimate consumers to be blocked or traffic to be intercepted.
2. **Integrity and authentication attacks** — replay attacks, algorithm confusion, and credential
   leakage that allow adversaries to impersonate legitimate consumers.
3. **Compliance and privacy conflicts** — scenarios where security obligations (audit log retention)
   conflict with privacy rights (GDPR erasure), or where a remediation action (logging) introduces
   the vulnerability it is trying to detect (PII leakage).

Each scenario is documented with precise failure mechanics, business impact, detection strategy,
recovery procedure, and preventive architecture controls.

---

## Edge Cases

---

### EC-SEC-001: WAF Rate Limiting Rule Blocks Legitimate High-Volume Enterprise Customer IP Range

**Background:** WAF over-blocking of legitimate traffic is an under-documented failure mode in
security-focused architectures. The risk is especially acute for enterprise API consumers who
route all traffic through corporate NAT gateways, concentrating what may be thousands of individual
developers' requests behind a single IP. WAF rules designed to block volumetric attacks must
explicitly account for legitimate high-volume sources via an IP allowlist maintained as a first-
class operational artefact.

| Field | Detail |
|-------|--------|
| **Failure Mode** | An AWS WAF rate-based rule is configured to block any IP address that exceeds 2,000 requests per 5-minute window across the CloudFront distribution. A large enterprise customer operating a data pipeline that legitimately generates 50,000 requests per minute from a fixed NAT gateway IP (all traffic egresses through a single corporate IP) triggers the rule. AWS WAF blocks the IP at the CloudFront edge, and the customer receives HTTP 403 Forbidden responses for all requests — including health checks, authentication requests, and API calls — with no gateway-level context about the block reason. The customer's operations team sees a complete API outage from their perspective. |
| **Impact** | Total loss of API access for the enterprise customer for the duration of the WAF block (WAF rate-based rule block duration defaults to 5 minutes but can compound if traffic continues). For enterprise customers with SLA-backed uptime guarantees, a 5-minute outage may constitute a breach of the contracted uptime SLA, triggering financial penalties. Customer trust is severely damaged when a paying customer is blocked by the platform's own protection mechanisms, particularly if the block persists undetected for longer than 5 minutes due to alerting latency. |
| **Detection** | CloudFront access logs streamed to S3 and queried via Amazon Athena detect a step-change in 403 response rates for a specific IP or CIDR range. Prometheus metric `cloudfront_4xx_rate_by_ip` fires an alert when any single IP's 403 rate exceeds 95% of its request volume for more than 60 seconds. The gateway's authentication service emits `auth_request_cloudfront_blocked` events (populated from a custom response header injected by CloudFront) which trigger a PagerDuty alert to the account management team when the blocked IP is in the enterprise customer IP whitelist. |
| **Mitigation / Recovery** | Immediately add the enterprise customer's IP or CIDR range to a WAF IP set configured as an `ALLOW` rule with a higher priority than the rate-based block rule. WAF rule evaluation is priority-ordered; the explicit ALLOW bypasses the rate-based rule within seconds of the change. Notify the enterprise customer's technical contact with an explanation and apology. For any SLA breach, escalate to account management to initiate the contractual remedy process. Review all enterprise customer IP ranges against existing WAF rules to proactively identify other at-risk customers. |
| **Prevention** | Maintain a managed WAF IP set `enterprise-customer-allowed-ips` populated from the enterprise customer registry in PostgreSQL, automatically synchronised via an EventBridge-triggered Lambda function whenever a new enterprise account is provisioned or updates their IP range. Assign this IP set the highest WAF rule priority (priority 0) with an unconditional `ALLOW` action, ensuring it is evaluated before any rate-based or managed rule group rules. Establish an SLA-aware onboarding checklist that includes WAF IP allowlisting as a required step for any enterprise customer with egress volume exceeding 1,000 req/min. |

**Operational Notes:**
- The enterprise IP allowlist must be version-controlled in Terraform and reviewed quarterly.
- WAF rule changes must require peer review from both security and platform engineering teams.
- Test the allowlist by running a load test from the enterprise customer's IP range post-change.
- Document the allowlist maintenance procedure in the enterprise customer onboarding playbook.
- Monitor for allowlist entries that have not generated traffic in 90 days for cleanup.

---

### EC-SEC-002: HMAC Signature Replay Attack Within Validity Window (No Nonce/Timestamp Validation)

**Background:** HMAC replay attacks are particularly insidious because they require no cryptographic
weakness — the attacker does not need to know the signing secret. All they need is a single valid
signed request, which can be obtained via passive network observation, a compromised proxy, or even
an HTTP client library that logs outgoing requests. The nonce+timestamp combination closes this
vulnerability definitively and is a standard requirement in API signature specifications such as
AWS Signature Version 4.

| Field | Detail |
|-------|--------|
| **Failure Mode** | The HMAC-SHA256 API key authentication scheme signs the canonical request (method + path + body hash + `Date` header) with the consumer's API secret. However, the gateway validates only the HMAC signature and does not check for a nonce or enforce a request timestamp freshness window. An attacker who can observe a valid signed request — via network interception, a compromised proxy log, or a leaked HTTP request from a client application — can replay the exact same request with the same signature headers any number of times within the network transmission window, as the signature remains mathematically valid for any future request with the same parameters. |
| **Impact** | An attacker who captures a signed write request (e.g., `POST /orders` or `POST /transfers`) can replay it indefinitely to create duplicate orders, duplicate financial transactions, or exhaust the victim consumer's quota. For financial API consumers, replayed transaction requests represent direct monetary fraud. Even for read requests, quota exhaustion via replay is a form of service disruption. The attack requires no knowledge of the consumer's API secret, only the ability to observe one valid request in transit. |
| **Detection** | The gateway currently has no nonce-based deduplication, so replay attacks generate successful responses that are indistinguishable from legitimate requests in standard metrics. Detection relies on anomaly monitoring: Prometheus alert `api_key_request_rate_anomaly` fires on unexpected RPS spikes, and Grafana "Request Body Hash Distribution" can reveal repeated identical body hashes for write endpoints, which should be statistically near-zero for legitimate traffic. AWS WAF custom rules can flag requests with identical `X-Signature` header values arriving from different IP addresses. |
| **Mitigation / Recovery** | Immediately deploy a nonce-based deduplication layer: require a `X-Request-Nonce` header (cryptographically random, 128-bit UUID) on all signed requests. The gateway stores nonces in Redis with a TTL equal to the request freshness window (e.g., 5 minutes). Any request with a previously seen nonce within the TTL window is rejected with HTTP 400 and error code `ERR_DUPLICATE_NONCE`. Additionally enforce a timestamp freshness check: the `Date` header must be within ±300 seconds of the gateway's current time, preventing replay outside the 5-minute window. Rotate API secrets for any consumer suspected to have had their signed requests intercepted. |
| **Prevention** | Add nonce and timestamp validation to the HMAC authentication specification as mandatory fields before any external consumers are onboarded. Document the canonical signed string format as: `METHOD\nPATH\nDATE_RFC2822\nNONCE\nSHA256(BODY)`. Enforce this in the API key authentication middleware with unit tests for replayed nonce rejection and timestamp staleness rejection. Publish a signed request SDK for all supported languages (Node.js, Python, Go, Java) that automatically generates fresh nonces and correct timestamps, preventing developer-side implementation errors. Include replay attack scenarios in the annual penetration testing scope. |

**Operational Notes:**
- The nonce Redis key namespace (`nonce:{keyId}:{nonce}`) must be separate from rate-limit keys.
- Nonce storage TTL must equal the timestamp validity window (e.g., 300 seconds).
- Publish the updated HMAC canonical string format to all SDK consumers with a migration guide.
- Include replay attack scenarios in the annual penetration test scope.
- Monitor `ERR_DUPLICATE_NONCE` rate as a metric; sustained non-zero values indicate active replay.

---

### EC-SEC-003: Sensitive Data (PII, API Keys) Accidentally Logged in Request/Response Body Logging

**Background:** Sensitive data leakage via logging is one of the most common security incidents in
API platforms, and one of the most preventable. Debug logging in production is the highest-risk
configuration — it captures the full request/response lifecycle including body content that in
normal operation would never be stored. The defence must be structural: sensitive data must be
redacted before reaching the logging infrastructure, not after. Post-hoc log scrubbing is
unreliable because data may have already been indexed and replicated.

| Field | Detail |
|-------|--------|
| **Failure Mode** | The gateway enables request/response body logging at the DEBUG level for troubleshooting purposes. A developer debugging an integration issue enables DEBUG logging on a production gateway instance via the dynamic log level API. The logged request bodies contain consumer PII fields (email addresses, phone numbers, billing addresses submitted to upstream partner APIs) and in one case, a consumer mistakenly passes their API secret in the request body rather than the `Authorization` header. These sensitive fields are captured in CloudWatch Logs, forwarded to the Grafana Loki log aggregator, indexed for full-text search, and retained for 90 days per the default log retention policy. Any team member with CloudWatch access can now search and retrieve this data. |
| **Impact** | API keys captured in logs can be immediately used by any internal user with log access to impersonate the affected consumer, accessing their data and consuming their quota fraudulently. PII captured in logs creates a GDPR compliance breach: the data is stored beyond its authorised purpose (operational logging vs. personal data processing), shared with log aggregation services not listed as sub-processors in the privacy policy, and may be transmitted across regions if the log aggregation infrastructure is multi-region. The supervisory authority notification obligation is triggered within 72 hours of discovering the breach. |
| **Detection** | A log scanning Lambda function runs every 5 minutes on new CloudWatch Log streams, applying regex patterns to detect common PII forms (email addresses: `[\w.+\-]+@[\w\-]+\.\w+`, phone numbers: `\+?[1-9]\d{7,14}`, API key format: `gw_[a-zA-Z0-9]{32}`) and secrets (Bearer tokens, private key PEM headers). Matches emit a `sensitive_data_in_logs_detected` CloudWatch alarm classified as SEV-1. AWS Macie continuous discovery on the S3 log archive bucket also scans for PII patterns and sends findings to AWS Security Hub. |
| **Mitigation / Recovery** | Immediately: (1) Disable DEBUG logging on the affected instance and revert to INFO level. (2) Revoke and rotate all API keys whose values appear in the logs. (3) Delete the affected log streams from CloudWatch and Loki within 1 hour of detection. (4) Assess whether the PII exposure meets the GDPR Art. 33 notification threshold (likely yes); prepare a Data Breach Notification with the specifics of what data was exposed, how many data subjects, and what controls are in place. (5) Audit all team members' CloudWatch log access since the exposure window. Notify affected consumers of the credential compromise. |
| **Prevention** | Implement a structured logging filter in the Fastify request logger that scrubs all request/response body fields matching a denylist of sensitive field names (`password`, `api_key`, `client_secret`, `authorization`, `token`, `ssn`, `credit_card`, `email`, `phone`) before the log entry is written. Use `pino-redact` with a configured path list for nested field scrubbing. Never log raw request/response bodies at any log level in production; log only headers (with `Authorization` header value replaced by `[REDACTED]`), path, method, status code, and duration. Enforce this through a mandatory pre-commit hook that fails if any logging call passes `req.body` directly to a log function. |

**Operational Notes:**
- The pino-redact path configuration must be reviewed on every schema change to request/response.
- The log scanning Lambda must run in the same region as the CloudWatch Log Group.
- AWS Macie findings must be integrated into the security incident workflow in PagerDuty.
- Conduct a quarterly log content audit by sampling 100 random log entries across all services.
- Include a `grep -r 'req.body'` static analysis rule in the pre-commit hook for logging calls.

---

### EC-SEC-004: JWT Algorithm Confusion Attack (RS256 Key Treated as HS256 Symmetric Key)

**Background:** The JWT algorithm confusion vulnerability (CVE class: JWT None/Algorithm Confusion)
was first publicly documented in 2015 and has been independently rediscovered in dozens of
production systems since. It is caused by JWT libraries that trust the `alg` field in the token
header rather than enforcing a server-configured expected algorithm. The fix is a single line of
code, but the consequences of not applying it are complete authentication bypass. Every JWT
validation implementation must be audited for this pattern during code review.

| Field | Detail |
|-------|--------|
| **Failure Mode** | The gateway validates OAuth 2.0 JWT access tokens using RS256 (asymmetric RSA signature), fetching the public key from the JWKS endpoint (`/.well-known/jwks.json`). An attacker crafts a malicious JWT with the `alg` header field set to `HS256` (symmetric HMAC) instead of `RS256` and signs the token using the gateway's RS256 public key as the HMAC secret. If the JWT validation library is configured to accept any algorithm specified in the token header (rather than requiring a specific expected algorithm), the library attempts HS256 validation using the public RSA key as the HMAC secret — a key that is publicly available from the JWKS endpoint — and the validation succeeds. The attacker has forged an arbitrary JWT with any claims they choose, including elevated `scope` values or impersonated `sub` identities. |
| **Impact** | The attacker can impersonate any API consumer by creating a JWT with the target consumer's `sub` claim, granting them full access to that consumer's resources and API quota. The attack also allows privilege escalation by setting elevated `scope` values in the forged token. The gateway has no cryptographic basis to detect this forgery because, from HS256's perspective, the signature is mathematically valid. This is a complete authentication bypass affecting all consumers who use OAuth 2.0 tokens, and the attack can be executed by anyone who can read the public JWKS endpoint. |
| **Detection** | The JWT validation middleware logs the `alg` header value for every token validation event. A Prometheus counter `jwt_algorithm_mismatch_total{expected="RS256", received="HS256"}` fires an alert immediately when any token with a non-RS256 algorithm is presented. This alert is classified as SEV-1 / security incident. AWS WAF custom rules can be configured to inspect the Authorization header for base64-decoded JWT headers containing `"alg":"HS256"` and block such requests at the edge before they reach the gateway. |
| **Mitigation / Recovery** | Immediately deploy a patch to the JWT validation middleware that explicitly specifies `algorithms: ['RS256']` in the `jsonwebtoken.verify()` or equivalent library call, causing the library to reject any token with a non-RS256 algorithm header regardless of whether the signature would otherwise validate. WAF rules should be updated to block HS256 algorithm tokens at the edge as a defence-in-depth measure. Rotate all OAuth 2.0 client secrets and RSA key pairs as a precaution. Audit access logs for the affected window to identify any forged tokens that may have already succeeded, looking for abnormal access patterns from `sub` values with suspicious `iat` timestamps. |
| **Prevention** | Configure the JWT validation library with an explicit, hardcoded algorithm allowlist containing only `['RS256']`. Never pass `algorithms: undefined` or derive the algorithm from the token header. Add a unit test that asserts token validation throws an error when presented with an HS256-signed token, an RS384-signed token, and a token with `"alg":"none"`. Document the algorithm confusion vulnerability class in the security onboarding guide for all engineers working on authentication code. Include algorithm confusion attacks in the annual penetration testing scope and in automated SAST rules. |

**Operational Notes:**
- The `algorithms: ['RS256']` parameter is the single most important JWT security configuration.
- The unit test for HS256 rejection must be run on every CI build, not just security test runs.
- Document the vulnerability class in the security engineer onboarding guide with a code example.
- Review all JWT validation sites in the codebase (use `grep -r 'jwt.verify'`) for compliance.
- Add algorithm confusion to the SAST rule set and verify it catches the vulnerable pattern.

---

### EC-SEC-005: SSRF Vulnerability in Webhook URL Validation Allows Access to Internal VPC Services

**Background:** Server-Side Request Forgery (SSRF) via webhook URL registration is a well-known
vulnerability class (OWASP Top 10 2021: A10 — Server-Side Request Forgery). The DNS rebinding
variant is particularly dangerous because it bypasses naive "check IP before request" mitigations.
The only reliable defence is to re-validate the resolved IP at delivery time, use a network-
isolated delivery service, and enforce security group egress rules that physically prevent access
to internal VPC resources from the webhook delivery path.

| Field | Detail |
|-------|--------|
| **Failure Mode** | The Developer Portal allows consumers to register webhook URLs to receive API event notifications. The webhook URL is validated via a `HEAD` request at registration time to confirm the endpoint is reachable. The URL validation logic checks only that the host resolves to a public IP address using a single DNS lookup, but does not account for DNS rebinding attacks or private IP ranges returned after the initial check. An attacker registers a webhook URL pointing to a domain they control. At registration time, DNS resolves to a public IP (passing validation). After the registration is approved, the attacker updates their DNS record to resolve to an internal VPC IP address (e.g., `10.0.0.1`, the RDS PostgreSQL instance, or the ElastiCache endpoint). Subsequent webhook delivery attempts by the gateway make HTTP requests to the internal service. |
| **Impact** | The attacker can probe and in some cases interact with internal VPC services that are not exposed to the public internet. The AWS ECS task making the webhook delivery request has an IAM role with VPC network access; requests from this task to internal services (RDS, ElastiCache, internal ECS services) bypass all VPC security group rules that normally restrict inbound public traffic. Sensitive data from internal service HTTP responses (e.g., ElastiCache health endpoints, internal API diagnostic endpoints) may be returned to the attacker via the webhook delivery response metadata. In extreme cases, writable internal endpoints (e.g., an admin API without authentication) could be modified. |
| **Detection** | Network-level monitoring via AWS VPC Flow Logs detects connections from ECS task ENIs to private IP address ranges that are not the expected RDS or ElastiCache endpoints. An alert fires on any VPC Flow Log entry where the source is an ECS webhook-delivery task and the destination is a non-public, non-approved internal IP. The gateway's webhook delivery code logs the resolved IP address for every delivery attempt; Prometheus metric `webhook_delivery_internal_ip_target_total` fires a SEV-1 alert immediately on any non-zero value. |
| **Mitigation / Recovery** | Immediately suspend the offending webhook registration and revoke the consumer's API key pending investigation. Patch the webhook URL validation to resolve the hostname to its final IP address using an isolated DNS resolver and reject any response containing RFC-1918 addresses (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local addresses (`169.254.0.0/16`), loopback (`127.0.0.0/8`), and the ECS task metadata endpoint (`169.254.170.2`). Enable VPC Flow Logs on all ECS task subnets and configure an alerting rule for unexpected internal destination traffic from webhook delivery tasks. Conduct a full review of all registered webhook URLs for SSRF indicators. |
| **Prevention** | Use a dedicated, network-isolated ECS task for webhook delivery that has no VPC route to internal services — the task's security group outbound rules allow only HTTPS (443) to `0.0.0.0/0` and explicitly deny all traffic to RFC-1918 CIDR ranges at the security group level (using egress deny rules). Perform DNS resolution at validation time and at delivery time in a hardened resolver library (`ssrf-req-filter` or equivalent for Node.js) that blocks private IPs. Re-validate the resolved IP on every delivery attempt, not just at registration. Add SSRF URL validation to the security code review checklist and implement a static analysis rule that prevents direct use of `fetch`/`axios`/`http.request` with unchecked user-supplied URLs in webhook delivery code. |

**Operational Notes:**
- The webhook delivery security group egress rule must be reviewed in every quarterly security audit.
- Log the resolved destination IP for every webhook delivery attempt for post-incident analysis.
- The SSRF filter library (`ssrf-req-filter`) must be pinned to a specific version in package.json.
- Add SSRF to the security code review checklist for any code that makes outbound HTTP requests.
- Test the DNS rebinding defence using a controlled rebinding domain in the staging environment.

---

### EC-SEC-006: GDPR Deletion Request for Consumer Data While Audit Logs Must Be Retained for 7 Years

**Background:** The GDPR erasure vs. audit log retention conflict is one of the most practically
complex compliance challenges in regulated API platforms. It arises from the intersection of two
independently valid legal obligations that point in opposite directions. The resolution requires
a legal opinion confirming the applicable retention obligation, followed by a technical
implementation that achieves pseudonymisation of the PII component while preserving the audit
event metadata. This solution must be reviewed by a qualified Data Protection Officer.

| Field | Detail |
|-------|--------|
| **Failure Mode** | A Developer Portal consumer submits a GDPR Article 17 Right to Erasure request, asking for all their personal data to be deleted. The platform's privacy automation processes the request and schedules deletion of the consumer's account record, API keys, application records, and usage analytics from PostgreSQL and Redis. However, the same consumer's email address, IP addresses, and request metadata are embedded throughout immutable audit log records in the CloudWatch Logs archive and the PostgreSQL `audit_events` table, which must be retained for 7 years under financial services compliance obligations (PCI-DSS, SOX). The deletion job cannot delete these records without violating the mandatory retention policy. The platform faces a direct, unresolvable conflict between GDPR Art. 17 (right to erasure) and the legal retention obligation under financial regulations. |
| **Impact** | Non-compliance with the GDPR erasure request exposes the platform to a supervisory authority complaint and potential fines under GDPR Art. 83 (up to 4% of global annual turnover or €20 million). Conversely, deleting audit logs to comply with GDPR violates financial services retention obligations and exposes the platform to regulatory fines from financial regulators. Without a clear, documented legal basis for retaining data despite the erasure request, the platform has no defensible position if challenged by either regulator simultaneously. |
| **Detection** | The GDPR request processing system flags all erasure requests where the consumer has audit log records as `PARTIAL_ERASURE_CONFLICT` status. A dedicated legal compliance dashboard tracks all open conflicts between erasure requests and retention obligations. The privacy team receives an automated task in the compliance ticketing system for each conflict requiring human review and a documented legal basis determination within 5 business days. |
| **Mitigation / Recovery** | Respond to the erasure request within the 30-day GDPR deadline, documenting the legal basis for retaining audit log data under GDPR Art. 17(3)(b): "for compliance with a legal obligation which requires processing by Union or Member State law." Delete all non-legally-required personal data (account profile, contact details, API key metadata not needed for audit purposes), providing a complete list of what was deleted and what was retained with the legal justification. Pseudonymise the consumer's identifying information in retained audit records: replace email addresses with a one-way HMAC hash derived from the consumer ID, rendering the data no longer directly identifying while preserving the audit trail integrity. |
| **Prevention** | Design the audit log schema from inception to separate personally identifying information from audit event metadata. Store PII fields in a dedicated `audit_pii` table linked via a pseudonymous ID, allowing the PII table to be erased on GDPR request while the audit event metadata (timestamps, actions, resource IDs) is retained. Document the retention conflict resolution policy in the Privacy Policy and in the Data Protection Impact Assessment (DPIA), establishing clear legal bases for each data category. Include a GDPR compliance review in the onboarding checklist for any new data storage system. |

**Operational Notes:**
- The pseudonymisation HMAC key must be stored in AWS Secrets Manager, not in code or config.
- The legal basis for retaining pseudonymised audit data must be reviewed annually by the DPO.
- Erasure request processing must be audited end-to-end with a test data subject in staging.
- Document the exact data categories retained vs. erased in the Records of Processing Activities.
- The 30-day GDPR response deadline must be tracked in the compliance ticketing system.

---

### EC-SEC-007: TLS 1.0/1.1 Downgrade Attack on Gateway Edge Listener

**Background:** TLS version downgrade attacks exploit the backward-compatibility negotiation
built into the TLS handshake protocol. While TLS 1.3 makes downgrade attacks significantly harder
through its Finished message protection, the real risk is that TLS 1.0/1.1 support in the
server's advertised cipher suite list makes the negotiation vulnerable to MITM downgrade on
unprotected networks. The fix is simple and should have been applied at initial deployment;
finding it in production represents a configuration debt that must be remediated immediately.

| Field | Detail |
|-------|--------|
| **Failure Mode** | The CloudFront distribution in front of the API Gateway is configured with a security policy of `TLSv1` (the permissive default in some CloudFront configurations), which advertises support for TLS 1.0, TLS 1.1, TLS 1.2, and TLS 1.3 in the ServerHello cipher suite negotiation. An attacker performing a MITM attack on an unsecured network (hotel Wi-Fi, conference network) can execute a BEAST or POODLE-style downgrade by manipulating the ClientHello to negotiate TLS 1.0. Once the connection is downgraded to TLS 1.0, the attacker can exploit known vulnerabilities in the CBC cipher modes supported by TLS 1.0 to decrypt portions of the encrypted traffic, potentially recovering HMAC signatures or session tokens from the request stream. |
| **Impact** | Session tokens, HMAC signatures, and in some cases API key material transmitted over a downgraded TLS 1.0 connection are vulnerable to partial decryption attacks with known TLS 1.0 vulnerabilities (BEAST: CBC block-boundary exploitation). Successful decryption allows the attacker to capture authentication credentials from the victim developer's Developer Portal session or API requests, enabling account takeover and API key theft. Consumers operating in regulated industries (PCI-DSS, HIPAA) are contractually prohibited from transmitting cardholder data or PHI over TLS 1.0/1.1 connections; any such transmission detected by their own compliance scanning generates an automatic audit finding. |
| **Detection** | AWS CloudFront access logs include the `tlsVersion` field for every request. A CloudWatch Logs Insights query runs every hour aggregating requests by TLS version; a Prometheus metric `cloudfront_tls_version_distribution` tracks the percentage of requests using each TLS version. An alert fires immediately if any request is served over TLS 1.0 or TLS 1.1, as these should be zero under a correctly configured policy. AWS Security Hub's CIS AWS Foundations Benchmark check for TLS configuration is enabled and reports findings to the security dashboard. |
| **Mitigation / Recovery** | Immediately update the CloudFront distribution's security policy to `TLSv1.2_2021`, which enforces TLS 1.2 minimum and prefers TLS 1.3, completely removing support for TLS 1.0 and TLS 1.1. This change propagates to all CloudFront edge locations within 15 minutes. Notify consumers that TLS 1.0/1.1 support has been permanently removed and provide a migration deadline of 90 days (effectively immediate, as TLS 1.2 has been supported since 2008). Rotate all session tokens and HMAC secrets for consumers who connected over the affected window, as a precaution against any potential credential exposure. |
| **Prevention** | Set CloudFront security policy to `TLSv1.2_2021` as a required value in the Terraform infrastructure-as-code module for all CloudFront distributions, enforced via a Terraform `validation` block that fails if any lower policy is specified. Add an AWS Config rule `cloudfront-viewer-policy-https` to detect and alert on any CloudFront distribution not configured with TLS 1.2 minimum. Include TLS configuration in the monthly infrastructure security review checklist. Run OWASP ZAP TLS cipher suite scan in the CI/CD pipeline against the staging CloudFront distribution to catch regressions before production deployment. |

**Operational Notes:**
- The `TLSv1.2_2021` CloudFront security policy supports TLS 1.2 and 1.3 and modern cipher suites.
- Run the OWASP ZAP TLS scan against staging CloudFront in CI to catch regressions early.
- Notify enterprise consumers of TLS 1.0/1.1 removal with 90 days notice for compliance planning.
- The AWS Config rule must alert to the security team Slack channel for immediate visibility.
- Cross-reference with the PCI-DSS compliance audit checklist, which mandates TLS 1.2 minimum.

---

### EC-SEC-008: Leaked OAuth client_secret in Public GitHub Repository Requires Emergency Rotation

**Background:** OAuth client_secret leakage in public source code repositories is the most
common credential exposure vector, according to GitHub's secret scanning data. The platform must
treat all credentials as potentially compromised at any time and provide an emergency rotation
capability that can be exercised in under 60 seconds. The 90-day expiry on client secrets is a
defence-in-depth measure that limits the blast radius of any leakage that goes undetected by
automated scanning.

| Field | Detail |
|-------|--------|
| **Failure Mode** | A developer at a partner organisation accidentally commits their application's OAuth 2.0 `client_id` and `client_secret` in a `config.json` file to a public GitHub repository. The commit is detected by GitHub's secret scanning feature and also by automated bots that continuously scrape public repositories for credential patterns. Within minutes of the commit, the credentials appear in credential-stuffing databases. Attackers begin using the stolen `client_secret` to request OAuth access tokens via the `client_credentials` grant flow, impersonating the legitimate partner application and accessing API resources under the partner's quota and permissions. |
| **Impact** | The attacker can generate valid OAuth access tokens with the same scopes as the legitimate partner application. All API requests authenticated with these tokens are billed to the partner's account and attributed to their usage quota. Depending on the scopes granted to the OAuth application, the attacker may be able to read private data belonging to the partner's end users, create fraudulent API resources, or exhaust the partner's quota causing a service disruption for their production application. The partner's end users may be exposed to data access by an unauthorised third party, triggering a GDPR breach notification obligation for the partner. |
| **Detection** | GitHub Advanced Security secret scanning is configured on the partner's repository with a push protection rule that blocks commits containing known credential patterns. If a commit passes through (e.g., force push bypassing protection), GitHub sends a real-time alert to the platform's registered secret scanning partner endpoint (`POST /webhooks/secret-scanning`). This endpoint immediately queues a credential rotation job with `priority: critical` in BullMQ. Separately, an anomaly detection rule in the OAuth token issuance service fires when a single `client_id` issues more than 10 tokens within 5 minutes outside business hours. |
| **Mitigation / Recovery** | Within 60 seconds of detection: (1) Immediately revoke the compromised `client_secret` in the PostgreSQL `oauth_clients` table and delete all active access tokens issued with this credential from Redis. (2) Generate a new `client_secret` and deliver it to the partner's registered security contact via an encrypted, time-limited secure link (not email). (3) Audit all API requests made with the compromised credential since the commit timestamp, identifying any requests that do not match the partner's normal usage patterns. (4) If data access anomalies are found, notify the partner within 24 hours to assess GDPR breach notification obligations. (5) The partner is required to delete the commit from GitHub history and verify no other secrets are in their repository. |
| **Prevention** | Register the platform's OAuth credential patterns (`client_secret` format: `oas_[a-zA-Z0-9]{40}`) as a custom secret pattern with GitHub's secret scanning partner programme, enabling automatic push blocking and real-time webhook alerts across all public and private repositories of registered partner organisations. Provide partners with a pre-commit hook script that uses `detect-secrets` to scan staged files for credential patterns before commit. Document the emergency credential rotation procedure in the partner onboarding guide and test the end-to-end rotation flow quarterly as a security drill. Implement short-lived OAuth client secrets with a default expiry of 90 days, requiring periodic rotation, so that any leaked secret has a bounded lifetime even if detection fails. |

**Operational Notes:**
- The emergency rotation SLA is 60 seconds from detection to credential revocation. Test this quarterly.
- The secure credential delivery link must expire in 15 minutes to minimise interception window.
- Maintain a runbook in the security wiki with the exact steps for OAuth credential rotation.
- Register all credential patterns with GitHub Secret Scanning partner programme proactively.
- Review the 90-day expiry policy with the security team; some environments may require 30 days.

---

## Summary Table

| ID | Title | Severity | Attack Category | Compliance Impact | Recovery Time |
|----|-------|----------|-----------------|-------------------|---------------|
| EC-SEC-001 | WAF Blocks Legitimate Enterprise Customer | High | Availability | SLA breach | 5–15 min |
| EC-SEC-002 | HMAC Signature Replay Attack | Critical | Authentication bypass | Fraud, quota abuse | 30–60 min |
| EC-SEC-003 | PII/API Key Leakage via Debug Logging | Critical | Data exposure | GDPR Art. 33 breach | 1–4 hr |
| EC-SEC-004 | JWT Algorithm Confusion (RS256→HS256) | Critical | Authentication bypass | Full auth bypass | 15–30 min |
| EC-SEC-005 | SSRF via Webhook URL | Critical | Internal network access | Data exfiltration risk | 1–2 hr |
| EC-SEC-006 | GDPR Erasure vs. Audit Log Retention | High | Compliance conflict | Dual regulatory exposure | Days–weeks |
| EC-SEC-007 | TLS 1.0/1.1 Downgrade Attack | High | Transport interception | PCI-DSS violation | 15–30 min |
| EC-SEC-008 | OAuth client_secret Leaked to GitHub | Critical | Credential compromise | GDPR breach potential | 1–4 hr |

---

## Testing and Validation

| Test Scenario | Target Edge Case | Expected Outcome | Frequency |
|---------------|-----------------|------------------|-----------|
| Send 5,000 req/min from an enterprise allowlisted IP | EC-SEC-001 | Requests pass through; no WAF block | Per WAF-rule change |
| Replay a captured HMAC-signed request | EC-SEC-002 | Second request rejected with `ERR_DUPLICATE_NONCE` | Per auth-change |
| Enable DEBUG logging and send a request with `email` in body | EC-SEC-003 | Log entry shows `[REDACTED]` for email field | Per logger-change |
| Present an HS256-signed JWT to the gateway | EC-SEC-004 | Request rejected with `invalid_algorithm` error | Per JWT-library update |
| Register a webhook URL that DNS-rebinds to 10.0.0.1 | EC-SEC-005 | Delivery blocked; `internal_ip_target` alert fires | Per webhook-change |
| Submit GDPR erasure request for account with audit logs | EC-SEC-006 | PII erased; pseudonymised audit records retained | Annually |
| Test CloudFront TLS negotiation with TLS 1.1 client | EC-SEC-007 | Connection rejected; TLS 1.2 minimum enforced | Per infra change |
| Simulate GitHub secret scanning webhook for leaked secret | EC-SEC-008 | Secret revoked within 60 seconds; new secret issued | Quarterly drill |

---

## Revision History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0 | 2025-01-01 | Security Engineering | Initial security edge cases |
| 1.1 | 2025-01-20 | Security Engineering | Added EC-SEC-006 GDPR compliance scenario |

---

## Related Edge Cases and Compliance Cross-References

| Security Edge Case | Related Operational/Portal Case | Shared Risk |
|-------------------|--------------------------------|-------------|
| EC-SEC-001 (WAF over-blocking) | EC-OPS-002 (Mixed deployment versions) | Edge infrastructure configuration |
| EC-SEC-003 (PII in logs) | EC-OPS-005 (OTel collector crash) | Observability pipeline data handling |
| EC-SEC-005 (SSRF via webhooks) | EC-OPS-004 (Redis memory exhaustion) | Internal network access risk |
| EC-SEC-006 (GDPR vs. audit retention) | EC-OPS-003 (Partition table rollover) | Long-term data storage integrity |
| EC-SEC-008 (Leaked OAuth secret) | EC-PORTAL-003 (Delete live application) | Credential revocation pipeline |

All security edge cases must be reviewed as part of the annual SOC 2 Type II audit preparation.
The detection and mitigation controls described in each case map directly to SOC 2 Common
Criteria CC6 (Logical and Physical Access Controls) and CC7 (System Operations).
