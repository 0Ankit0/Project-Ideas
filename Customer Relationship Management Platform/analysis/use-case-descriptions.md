# Use Case Descriptions — Customer Relationship Management Platform

## Document Information

| Field | Value |
|---|---|
| Version | 2.0 |
| Domain | Enterprise multi-tenant CRM |
| Scope | UC-001 through UC-015 |
| Primary outcome | Implementation-ready workflow descriptions with alternate, failure, and compliance behavior |

---

## UC-001 — Capture Lead

| Field | Detail |
|---|---|
| Use Case ID | UC-001 |
| Primary Actors | Prospect, Marketing Manager, System Integrator |
| Supporting Actors | Lead Intake Service, Spam Protection, Duplicate Detection Engine |
| Trigger | A prospect submits a web form, an external system posts to the lead API, or a user starts a CSV import. |
| Related Requirements | FR-001, FR-002, FR-003 |

### Preconditions
1. Tenant has configured capture source, required fields, and consent copy.
2. Public endpoint, API key, or import session is active and tenant-scoped.
3. Required standard and custom field definitions exist and are versioned.

### Postconditions
1. A lead intake record and canonical lead record exist or the request resolves idempotently to an existing record.
2. Source metadata, consent evidence, and raw payload hash are stored for audit.
3. Lead scoring and dedupe evaluation are queued.

### Normal Flow
1. Source submits lead payload with source metadata and optional idempotency key.
2. CRM validates captcha or API credentials, field schema, consent requirements, and tenant routing.
3. CRM normalizes email, phone, company domain, and custom fields.
4. CRM persists the lead, intake record, and activity timeline event in one transaction.
5. CRM returns tracking ID or created lead resource.
6. CRM enqueues scoring, dedupe, and assignment jobs with the same correlation ID.

### Alternative and Exception Flows
- **AF-001A — Bulk import:** invalid rows are isolated into an error report while valid rows continue in background batches.
- **AF-001B — Idempotent retry:** same idempotency key returns the original lead without re-running irreversible side effects.
- **EX-001A — Consent missing:** request is rejected with `422 CONSENT_REQUIRED` and no lead is created.
- **EX-001B — Spam threshold triggered:** request is rejected or quarantined depending on tenant anti-abuse policy.
- **EX-001C — Tenant over ingestion limit:** API returns `429 RATE_LIMITED`, UI surfaces retry window, and import job pauses.

### Acceptance Criteria
- Lead source, campaign attribution, and lawful-basis metadata remain queryable after later conversion or merge.
- No duplicate lead is created for a successful retried request with the same key.

---

## UC-002 — Score and Assign Lead

| Field | Detail |
|---|---|
| Use Case ID | UC-002 |
| Primary Actors | Sales Rep, RevOps Analyst |
| Supporting Actors | Scoring Engine, Assignment Service, Notification Service |
| Trigger | A new or updated lead requires score recalculation or routing. |
| Related Requirements | FR-004, FR-005 |

### Preconditions
1. Lead exists in `NEW`, `WORKING`, or `QUALIFIED` state.
2. Active scoring and assignment rules are published for the tenant.
3. Target users and queues have capacity metadata and availability status.

### Postconditions
1. Lead score history contains a reproducible scoring breakdown.
2. Owner, queue, or territory assignment is updated with reason codes.
3. Notifications and SLA timers are started for the assignee.

### Normal Flow
1. Scoring engine evaluates firmographic, demographic, and behavioral inputs.
2. Duplicate detection runs before assignment to prevent routing transient duplicates.
3. Assignment service evaluates priority rules, fallback queues, and round-robin pools.
4. CRM persists score snapshot, assignment result, and timeline event.
5. Assignee receives notification with score explanation and source context.

### Alternative and Exception Flows
- **AF-002A — Manual override:** manager or RevOps overrides owner and must provide reason and expiry policy.
- **AF-002B — Queue assignment:** when no rule matches, lead goes to the tenant default queue and remains visible in unassigned views.
- **EX-002A — Scoring dependency unavailable:** CRM stores the lead, sets score status `PENDING_RECALCULATION`, and retries asynchronously.
- **EX-002B — Assignee inactive:** lead routes to manager queue and flags `assignment_exception = inactive_user`.

### Acceptance Criteria
- Score transitions are historically auditable and can be replayed from source events.
- Assignment outcomes are deterministic for the same rule set and normalized input.

---

## UC-003 — Convert Lead

| Field | Detail |
|---|---|
| Use Case ID | UC-003 |
| Primary Actors | Sales Rep |
| Supporting Actors | Account Service, Contact Service, Opportunity Service, Audit Service |
| Trigger | User selects **Convert Lead** on a qualified lead. |
| Related Requirements | FR-006 |

### Preconditions
1. Lead status is `QUALIFIED` or equivalent tenant-defined convertible state.
2. User has permission to create accounts, contacts, and opportunities in the tenant.
3. Conversion mappings for standard and custom fields are active.

### Postconditions
1. Lead is immutable except for audit annotations and lineage pointers.
2. Contact and account exist and reference the original lead.
3. Optional opportunity exists with initial pipeline, stage, amount, and owner.

### Normal Flow
1. User chooses whether to create or link an account.
2. CRM shows duplicate candidates for account and contact before commit.
3. User optionally creates an opportunity and selects pipeline, stage, amount, close date, and forecast category.
4. CRM copies mapped standard/custom fields and writes lineage references.
5. CRM commits lead status change, new records, and conversion audit in a single transaction.
6. CRM emits `LeadConverted` and refreshes related views.

### Alternative and Exception Flows
- **AF-003A — Contact-only conversion:** account already exists and no opportunity is created.
- **AF-003B — Existing open opportunity:** user links lead to an existing opportunity instead of creating a new one when permitted by policy.
- **EX-003A — Duplicate conflict during commit:** transaction aborts and user must resolve duplicate candidates before retry.
- **EX-003B — Field mapping validation fails:** CRM blocks conversion and lists unmapped required target fields.

### Acceptance Criteria
- Conversion is atomic and leaves no partial account/contact/opportunity records.
- Original attribution, consent, and score-at-conversion remain attached to the archived lead.

---

## UC-004 — Manage Account and Contact

| Field | Detail |
|---|---|
| Use Case ID | UC-004 |
| Primary Actors | Sales Rep, Sales Manager |
| Supporting Actors | Account Service, Contact Service, RBAC Policy Engine |
| Trigger | User creates, updates, reassigns, or views canonical account/contact records. |
| Related Requirements | FR-007, FR-008 |

### Preconditions
1. User is authorized for entity scope and sensitive fields.
2. Canonical uniqueness rules for email, domain, and tenant are enforced.
3. Territory and owner lookup data are available.

### Postconditions
1. Account/contact record reflects the new canonical state and version number.
2. Ownership, relationship graph, and audit trail are updated.
3. Any downstream sync or search projection update is queued.

### Normal Flow
1. User creates or edits account/contact details.
2. CRM validates uniqueness, owner scope, and field-level permissions.
3. CRM updates related lookup references such as territory, parent account, and primary contact.
4. CRM writes immutable audit entry and emits outbox event.
5. UI refreshes 360 panels and related lists using the new version token.

### Alternative and Exception Flows
- **AF-004A — Soft delete:** delete action sets `deleted_at` and removes record from operational views while preserving audit and linkage data.
- **AF-004B — Manager mass reassignment:** ownership updates are performed as jobs with preview and approval.
- **EX-004A — Optimistic lock failure:** save is rejected with current version and diff summary.
- **EX-004B — Restricted field edit:** unauthorized field changes are ignored and surfaced as permission violations.

### Acceptance Criteria
- Canonical identity fields remain unique within tenant scope after normalization.
- Historical owner, territory, and parent-account relationships are reconstructable from audit logs.

---

## UC-005 — Manage Activity Timeline and Sync

| Field | Detail |
|---|---|
| Use Case ID | UC-005 |
| Primary Actors | Sales Rep |
| Supporting Actors | Activity Service, Email Connector, Calendar Connector |
| Trigger | User logs an activity manually or CRM receives email/calendar events from connected providers. |
| Related Requirements | FR-009, FR-014, FR-015, FR-016 |

### Preconditions
1. Related lead, contact, account, or opportunity exists and is readable by the user.
2. If sync is enabled, OAuth connection is active and provider scopes are granted.
3. Timeline retention and redaction policies are loaded.

### Postconditions
1. Activity appears in the unified timeline with immutable source metadata.
2. Linked records are updated with latest activity timestamps and next-step hints.
3. Sync cursors or webhook checkpoints are advanced only after durable persistence.

### Normal Flow
1. User logs task, call, meeting, note, or outbound email from the CRM UI, or provider sends inbound change.
2. CRM normalizes participants, timestamps, provider IDs, and recurrence details.
3. Matching logic links the activity to contact, account, and opportunity context.
4. CRM writes activity, search projection update, and timeline event.
5. UI displays chronological entry with source badge and permission-safe content preview.

### Alternative and Exception Flows
- **AF-005A — Manual relink:** user re-associates an email or meeting to a different record while keeping provider metadata unchanged.
- **AF-005B — Private event masking:** calendar events marked private show time blocks but hide description/body from unauthorized viewers.
- **EX-005A — Token expired:** connection enters `REAUTH_REQUIRED`, sync halts, and user notification includes reconnect CTA.
- **EX-005B — Replay or duplicate webhook:** idempotency keys suppress duplicate timeline entries while advancing the processed-event ledger.

### Acceptance Criteria
- Timeline ordering is stable even when provider events arrive out of order.
- Email/calendar sync preserves provider source-of-truth IDs and never creates duplicate activities for the same external event instance.

---

## UC-006 — Manage Opportunity Pipeline

| Field | Detail |
|---|---|
| Use Case ID | UC-006 |
| Primary Actors | Sales Rep, RevOps Analyst |
| Supporting Actors | Opportunity Service, Pipeline Policy Engine |
| Trigger | User creates an opportunity or moves it through a stage transition. |
| Related Requirements | FR-010, FR-011, FR-012 |

### Preconditions
1. Pipeline and stage definitions are active for the tenant.
2. User has edit rights for the opportunity and target stage.
3. Required linked account/contact records exist.

### Postconditions
1. Opportunity state, probability, history, and forecast classification are updated.
2. Stage evidence and validation results are stored with the transition.
3. Downstream forecast recalculation and notifications are queued.

### Normal Flow
1. User creates or opens an opportunity in a chosen pipeline.
2. CRM validates stage gate criteria such as next step, amount, contact role, or close date.
3. CRM applies the stage transition, records history row, and recalculates derived fields.
4. CRM updates kanban/list views and emits event for reporting/forecast consumers.

### Alternative and Exception Flows
- **AF-006A — Manual probability override:** permitted roles may override stage default probability; override reason is stored.
- **AF-006B — Multi-pipeline transfer:** opportunity is rehomed to a different pipeline only through an explicit transfer workflow that remaps stage and preserves history.
- **EX-006A — Closed-won validation failure:** CRM blocks transition if amount, close date, or required commercial evidence is missing.
- **EX-006B — Concurrent edits:** second writer receives `409 VERSION_CONFLICT` and must refresh before retrying.

### Acceptance Criteria
- Every stage change stores actor, from stage, to stage, prior probability, new probability, and validation evidence references.
- Closed states are append-only unless a governed reopen workflow is used.

---

## UC-007 — Submit and Approve Forecast

| Field | Detail |
|---|---|
| Use Case ID | UC-007 |
| Primary Actors | Sales Rep, Sales Manager |
| Supporting Actors | Forecast Service, Opportunity Service, Audit Service |
| Trigger | Forecast period opens for submissions or a user submits a revision. |
| Related Requirements | FR-013, FR-021 |

### Preconditions
1. Fiscal period exists and is in `OPEN` submission state.
2. Opportunity ownership, territory attribution, and FX rates for the period are available.
3. User belongs to the hierarchy for the snapshot being edited.

### Postconditions
1. Forecast snapshot is saved as draft, submitted, approved, revised, or frozen.
2. Rollup rows are recalculated for each manager level.
3. Variance, coverage, and exception metrics are available for dashboards and audit.

### Normal Flow
1. CRM assembles the candidate opportunity set for the period.
2. Sales rep reviews auto-derived committed, best-case, and pipeline numbers.
3. Rep enters manual adjustments and rationale, then submits.
4. Forecast service locks the submitted snapshot and sends it to the manager queue.
5. Manager approves or requests revision with comments.
6. Approved snapshots roll up through the hierarchy and freeze at the configured cutoff.

### Alternative and Exception Flows
- **AF-007A — Manager override:** manager can adjust rollup commentary or forecast category mapping without editing the rep's raw snapshot.
- **AF-007B — Late opportunity change:** post-submission opportunity deltas appear in an exception panel until resubmission or manager override resolves them.
- **EX-007A — Frozen period edit attempt:** CRM rejects the mutation and directs user to reopen workflow if policy allows.
- **EX-007B — Hierarchy mismatch:** rollup pauses and flags orphaned manager chain until user or territory data is repaired.

### Acceptance Criteria
- Approved and frozen forecast states are reproducible from immutable snapshot lines.
- Manager rollups show included rep snapshots, exception counts, and manual override reasons.

---

## UC-008 — Build and Execute Campaign

| Field | Detail |
|---|---|
| Use Case ID | UC-008 |
| Primary Actors | Marketing Manager |
| Supporting Actors | Campaign Service, Segment Engine, Email Delivery Provider |
| Trigger | Marketing user drafts or schedules a campaign. |
| Related Requirements | FR-017, FR-018, FR-019 |

### Preconditions
1. Sender identity, domain configuration, and unsubscribe footer are approved.
2. Segment definition is valid and previewable.
3. Contact consent and suppression ledgers are current.

### Postconditions
1. Campaign definition and segment snapshot are persisted.
2. Recipient sends are generated only for eligible contacts.
3. Delivery, bounce, click, and unsubscribe telemetry updates campaign analytics and contact state.

### Normal Flow
1. Marketing manager designs content, merge fields, and schedule.
2. CRM evaluates the segment and excludes suppressed contacts.
3. CRM locks the recipient snapshot at send time and creates one send record per eligible contact.
4. Email provider sends messages and returns provider IDs.
5. CRM ingests engagement events and updates campaign dashboards and contact communication preferences.

### Alternative and Exception Flows
- **AF-008A — A/B variant:** campaign splits recipients across variants and tracks metrics separately.
- **AF-008B — Pause and resume:** sends already handed to the provider continue; queued sends pause until resume.
- **EX-008A — Unsubscribe before scheduled send:** recipient is skipped and send record becomes `SUPPRESSED`.
- **EX-008B — Provider bounce or complaint:** contact communication status is downgraded and future campaigns honor suppression immediately.

### Acceptance Criteria
- Every campaign email carries a visible unsubscribe link and postal footer.
- Analytics distinguish provider acceptance from CRM-level eligibility and suppression decisions.

---

## UC-009 — Manage Territory Assignment

| Field | Detail |
|---|---|
| Use Case ID | UC-009 |
| Primary Actors | RevOps Analyst, Sales Manager |
| Supporting Actors | Territory Service, Forecast Service, Notification Service |
| Trigger | A territory rule is evaluated for an account or a reassignment plan is approved. |
| Related Requirements | FR-020 |

### Preconditions
1. Territory hierarchy and assignment rules are published.
2. Account attributes used by rules are normalized and complete enough for evaluation.
3. Reassignment policy defines how open opportunities, tasks, and forecast credit move.

### Postconditions
1. Account and optionally open opportunity ownership reflect the active territory rules.
2. Historical territory assignment row is written with effective dating.
3. Impacted managers and reps receive notifications and exception tasks.

### Normal Flow
1. Territory service evaluates rules in priority order on account create/update or plan preview.
2. CRM shows impacted records, quota movement, and split-credit exceptions.
3. Authorized approver confirms the effective date.
4. Job executes reassignments and emits downstream tasks for forecast, activities, and campaigns.
5. Reconciliation report confirms success or flags records requiring manual review.

### Alternative and Exception Flows
- **AF-009A — Dry run:** system calculates impact without mutating ownership.
- **AF-009B — Future-dated reassignment:** records remain under current owner until the effective date job runs.
- **EX-009A — Opportunity locked for approval:** ownership change is deferred until approval or explicit override.
- **EX-009B — User deactivated mid-job:** assignment falls back to territory queue and manager review task is opened.

### Acceptance Criteria
- Reassignment preserves historical territory lineage and period-specific forecast attribution.
- Preview and execution counts must match or produce a variance report.

---

## UC-010 — Configure Schema and Rules

| Field | Detail |
|---|---|
| Use Case ID | UC-010 |
| Primary Actors | CRM Administrator, RevOps Analyst |
| Supporting Actors | Configuration Service, Policy Engine |
| Trigger | Admin changes custom fields, pipelines, field permissions, scoring rules, or assignment logic. |
| Related Requirements | FR-022, FR-027 |

### Preconditions
1. Admin holds tenant-level configuration permission.
2. No incompatible migration is pending for the same object type.
3. Validation rules and field-level visibility policies are defined.

### Postconditions
1. New configuration version is published with audit trail.
2. Dependent caches and rule evaluators refresh safely.
3. Any required backfill or reindex job is scheduled.

### Normal Flow
1. Admin edits configuration in staged mode.
2. CRM validates naming, visibility, required-state conflicts, and downstream impact.
3. Admin publishes configuration.
4. CRM versions the change, queues backfills, and emits configuration-changed event.

### Alternative and Exception Flows
- **AF-010A — Draft-only save:** admin can save a draft without activating it.
- **EX-010A — Breaking change to required field:** publish is blocked until default or migration mapping is supplied.
- **EX-010B — Field-level permission conflict:** publish is blocked if an automation or integration requires a field hidden from its service identity.

### Acceptance Criteria
- Every configuration change is attributable to an actor and version.
- Changes take effect without application redeploy and without cross-tenant impact.

---

## UC-011 — Detect and Merge Duplicates

| Field | Detail |
|---|---|
| Use Case ID | UC-011 |
| Primary Actors | RevOps Analyst, CRM Administrator |
| Supporting Actors | Deduplication Engine, Merge Service, Audit Service |
| Trigger | System identifies duplicate candidates or user opens a merge review queue. |
| Related Requirements | FR-023 |

### Preconditions
1. Candidate records exist within the same tenant and are not under legal hold.
2. Match explanation and confidence score are available.
3. Merge policy defines auto-merge, restricted fields, and unmerge window.

### Postconditions
1. Surviving record is canonical and source record is soft-merged with lineage.
2. Relationships, activities, and opportunities are repointed according to policy.
3. Merge decision, field winners, and source snapshot are auditable.

### Normal Flow
1. Deduplication engine generates candidate pair and confidence explanation.
2. Medium-confidence pair enters review queue; high-confidence pair may auto-merge if tenant policy allows.
3. Reviewer selects surviving record and field winners.
4. CRM executes atomic merge, writes merge ledger, and reindexes search.
5. Downstream systems receive merge event with stable lineage references.

### Alternative and Exception Flows
- **AF-011A — Reject pair:** reviewer marks pair as distinct and suppresses repeat matching for a configurable period.
- **AF-011B — Unmerge:** authorized admin restores source record from snapshot during the allowed window.
- **EX-011A — Concurrent merge collision:** second merge attempt aborts if either record is already locked or merged.
- **EX-011B — Restricted field conflict:** merge pauses for admin review when the records differ on compliance-sensitive fields such as consent or legal hold flags.

### Acceptance Criteria
- Merge behavior is deterministic, atomic, and reversible within the documented policy window.
- The surviving record retains a complete lineage of merged sources and transferred relationships.

---

## UC-012 — Configure Integrations and Webhooks

| Field | Detail |
|---|---|
| Use Case ID | UC-012 |
| Primary Actors | CRM Administrator, System Integrator |
| Supporting Actors | Integration Service, Secret Vault, Webhook Delivery Service |
| Trigger | Admin connects an external provider or registers a webhook subscription. |
| Related Requirements | FR-024, FR-025 |

### Preconditions
1. Tenant has integration entitlement and admin permission.
2. Redirect URIs, provider credentials, and webhook endpoints are configured.
3. Secret storage and signing key rotation are available.

### Postconditions
1. Integration connection is stored with status and scopes.
2. Health checks, webhooks, and backfill cursors are initialized.
3. Failures are visible in admin diagnostics.

### Normal Flow
1. Admin initiates OAuth or secret-based connector setup.
2. CRM stores encrypted credentials and connection metadata.
3. CRM validates provider access or webhook reachability.
4. Connector schedules initial sync or test event delivery.
5. Admin dashboard shows connection health, scopes, and last successful sync.

### Alternative and Exception Flows
- **AF-012A — Scoped webhook subscription:** integrator registers only selected event types and tenant partitions.
- **EX-012A — Token scope insufficient:** connection is created in warning state and blocked from production use until reauthorized.
- **EX-012B — Webhook endpoint validation fails:** subscription remains disabled and last error is retained for remediation.

### Acceptance Criteria
- Connector health can be determined without inspecting provider dashboards.
- Secrets are never displayed after initial save and rotate without breaking in-flight jobs.

---

## UC-013 — Import Data with Mapping

| Field | Detail |
|---|---|
| Use Case ID | UC-013 |
| Primary Actors | RevOps Analyst |
| Supporting Actors | Import Service, Validation Engine, Deduplication Engine |
| Trigger | User uploads CSV/XLS/XLSX file for leads, contacts, accounts, or opportunities. |
| Related Requirements | FR-026 |

### Preconditions
1. File size, type, and row limits are within tenant policy.
2. Target object schema and custom field definitions are published.
3. User has permission to create the selected object type.

### Postconditions
1. Import job exists with row-level validation results.
2. Successful rows create or update records with preserved source lineage.
3. Failed rows remain downloadable with deterministic error codes.

### Normal Flow
1. User uploads file and maps source columns to CRM fields.
2. CRM validates required fields, formats, foreign keys, and dedupe keys.
3. User reviews preview and starts import.
4. Background workers process rows in batches with per-row status.
5. CRM publishes completion summary and downloadable failure report.

### Alternative and Exception Flows
- **AF-013A — Update existing records:** import mode uses external ID or canonical key to upsert instead of create.
- **EX-013A — Excessive error ratio:** job auto-pauses or aborts when the tenant-configured error threshold is exceeded.
- **EX-013B — Duplicate rows inside same file:** later duplicate rows are marked failed with pointer to first occurrence.

### Acceptance Criteria
- Imports are restartable from the last committed batch.
- Row-level outcomes are traceable to file, sheet, line number, and correlation ID.

---

## UC-014 — Execute GDPR Erasure

| Field | Detail |
|---|---|
| Use Case ID | UC-014 |
| Primary Actors | CRM Administrator |
| Supporting Actors | Privacy Service, Audit Service, Export/Sync Services |
| Trigger | Admin submits a right-to-erasure request for a data subject. |
| Related Requirements | FR-029 |

### Preconditions
1. Identity of the data subject is verified.
2. Legal-hold and retention checks have been performed.
3. Downstream connectors capable of storing replicated personal data are registered.

### Postconditions
1. Personal data is deleted or irreversibly anonymized according to policy.
2. Downstream systems receive erasure commands or reconciliation tasks.
3. Audit log retains non-PII evidence of the erasure workflow.

### Normal Flow
1. Admin opens a subject profile and starts erasure workflow.
2. CRM computes impact across contacts, activities, campaign events, provider sync artifacts, and exports.
3. Admin reviews blocking conditions and confirms.
4. Privacy service deletes or anonymizes data in the primary store and issues downstream deletion tasks.
5. CRM marks request completed and stores compliance evidence.

### Alternative and Exception Flows
- **AF-014A — Legal hold:** request remains pending with documented hold reason and approval chain.
- **EX-014A — Connector cannot confirm deletion:** request completes with exception item and retriable downstream task.
- **EX-014B — Subject merged previously:** privacy service follows merge lineage to erase all surviving and source identifiers.

### Acceptance Criteria
- Erasure removes personal data from operational views, campaign eligibility, and search indexes.
- Audit evidence proves who approved the erasure and what was retained lawfully.

---

## UC-015 — Export Tenant Data

| Field | Detail |
|---|---|
| Use Case ID | UC-015 |
| Primary Actors | CRM Administrator |
| Supporting Actors | Export Service, Storage Service, Audit Service |
| Trigger | Authorized user requests a scoped export for portability, analytics, or compliance. |
| Related Requirements | FR-030 |

### Preconditions
1. User has export permission for requested objects and fields.
2. Requested date range and object scope comply with policy.
3. Secure download storage and expiry policy are configured.

### Postconditions
1. Export job and manifest exist with field-level scope and filters.
2. Output file is stored encrypted and available until expiry.
3. Export event is written to the audit log and can be tied to a human approver when required.

### Normal Flow
1. Admin selects object types, filters, file format, and optional relationship expansion.
2. CRM validates permissions and estimates job size.
3. Export service materializes a tenant-scoped snapshot and writes manifest metadata.
4. CRM stores encrypted result in object storage and notifies the requester.
5. Download link expires automatically and access is logged.

### Alternative and Exception Flows
- **AF-015A — Scheduled recurring export:** supported only for approved service accounts and managed destinations.
- **EX-015A — Request includes restricted fields:** export fails fast with field-level permission report.
- **EX-015B — Export exceeds threshold:** job is chunked into multiple files and manifest tracks sequence.

### Acceptance Criteria
- Export output contains only records visible to the requester within the tenant.
- Expired exports are unrecoverable without rerunning the job.
