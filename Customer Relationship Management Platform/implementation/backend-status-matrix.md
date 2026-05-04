# Backend Status Matrix — Customer Relationship Management Platform

## Purpose

This matrix translates the CRM documentation set into implementation-ready backend scope. Status values reflect design completeness, not current code existence.

## Status Legend

| Status | Meaning |
|---|---|
| Ready | Documentation is sufficient to implement the endpoint or job without major product discovery. |
| Ready with provider dependency | Internal design is complete; production rollout additionally requires third-party credentials, quotas, or sandbox validation. |
| Deferred extension | The capability is intentionally documented as a later extension and should not block v1.0 core build. |

---

## 1. Transactional APIs

| Capability | Contract Surface | Owning Service | Status | Key Dependencies | Minimum Done Criteria |
|---|---|---|---|---|---|
| Lead capture via forms/API | `POST /api/v1/leads` | Lead Service | Ready | RBAC bypass for public form mode, captcha, dedupe keys | Idempotent writes, consent evidence, audit trail, outbox event |
| Lead import job creation | `POST /api/v1/import-jobs` | Import Service | Ready | file storage, schema mapper, dedupe engine | preview, validate, partial success reporting |
| Lead qualification | `POST /api/v1/leads/{id}/qualify` | Lead Service | Ready | scoring history, owner permissions | reason codes, SLA updates, timeline event |
| Lead conversion | `POST /api/v1/leads/{id}/convert` | Lead Service | Ready | account/contact/opportunity services | atomic transaction, lineage, duplicate safeguards |
| Account CRUD | `/api/v1/accounts` | Account Service | Ready | territory lookup, field-level permissions | optimistic locking, soft delete, audit |
| Contact CRUD | `/api/v1/contacts` | Contact Service | Ready | account ownership, communication preferences | unique email normalization, timeline links |
| Opportunity CRUD | `/api/v1/opportunities` | Opportunity Service | Ready | pipeline config, account/contact refs | version control, multi-currency validation |
| Opportunity stage transition | `POST /api/v1/opportunities/{id}/stage-transitions` | Opportunity Service | Ready | stage policy engine, forecast service | stage history, gate evidence, 409 on stale version |
| Forecast submit | `POST /api/v1/forecast-periods/{id}/snapshots/{ownerId}:submit` | Forecast Service | Ready | opportunity snapshot builder | lock after submit, rationale required |
| Forecast approve or request revision | `POST /api/v1/forecast-snapshots/{id}:approve` | Forecast Service | Ready | manager hierarchy, audit | approval chain, revision comments, rollup refresh |
| Territory preview | `POST /api/v1/territory-reassignments:preview` | Forecast and Territory Service | Ready | account filters, opportunity locks | deterministic preview and impact report |
| Territory execution | `POST /api/v1/territory-reassignments` | Forecast and Territory Service | Ready | approved preview snapshot, notification service | future-dated execution, reconciliation output |
| Campaign create and schedule | `/api/v1/campaigns` | Campaign Service | Ready | segment engine, sender identity config | compliance validation, scheduled send support |
| Campaign launch or pause | `POST /api/v1/campaigns/{id}:launch` / `:pause` | Campaign Service | Ready | queue dispatcher, suppression ledger | no opted-out sends, pause affects queued recipients only |
| Segment CRUD | `/api/v1/segments` | Campaign Service | Ready | filter parser, preview query engine | nested AND/OR filters, preview count |
| Duplicate review queue | `GET/POST /api/v1/duplicates/*` | Merge Service | Ready | dedupe explanations, source snapshots | manual approve/reject, unmerge window |
| Custom field definition | `/api/v1/admin/custom-fields` | Admin Service | Ready | config versioning, search reindex | publish workflow, backfill hooks |
| OAuth connection setup | `POST /api/v1/integrations/oauth-connections` | Integration Service | Ready with provider dependency | Google/Microsoft apps, secrets vault | encrypted token refs, health status |
| Webhook registration | `/api/v1/webhooks` | Integration Service | Ready | HMAC signing, delivery worker | endpoint validation, retry policy |
| GDPR erasure request | `POST /api/v1/privacy/erasure-requests` | Privacy Service | Ready | legal hold policy, downstream delete tasks | subject verification, lineage traversal, audit evidence |
| Data export request | `POST /api/v1/export-jobs` | Export Service | Ready | object storage, signed URL service | RBAC-aware manifest, expiry enforcement |

---

## 2. Background Jobs and Sagas

| Job | Trigger | Owning Service | Status | Failure Strategy | Minimum Done Criteria |
|---|---|---|---|---|---|
| Lead scoring worker | lead created or updated | Lead Service | Ready | retry with idempotent score history append | score breakdown persisted and queryable |
| Dedupe candidate generation | lead/contact/account write | Lead or Account Service | Ready | retry and quarantine bad normalization payloads | exact and fuzzy candidates with explanations |
| Auto-merge executor | high-confidence candidate approved by policy | Merge Service | Ready | pair-level locking, dead-letter on restricted conflicts | atomic merge ledger and relationship repoint |
| Unmerge executor | admin requests restore within policy window | Merge Service | Ready | snapshot validation, manual review fallback | restored record and reverse lineage |
| Forecast rollup recalculation | opportunity delta or approval event | Forecast Service | Ready | append exception row when frozen | reproducible rollup totals by hierarchy |
| Forecast freeze | schedule at period close | Forecast Service | Ready | rerunnable close job, finance alert on failure | immutable archive and freeze flag |
| Territory preview builder | API command | Forecast and Territory Service | Ready | cancellable batch job | stable impacted-record counts |
| Territory reassignment executor | effective date reached | Forecast and Territory Service | Ready | retry unlocked subset, manual-review queue for blocked rows | ownership changes plus reconciliation summary |
| Campaign recipient expansion | campaign scheduled or resumed | Campaign Service | Ready | pause-safe batching | suppression-aware recipient snapshot |
| Campaign send dispatcher | campaign in sending state | Campaign Service | Ready with provider dependency | per-recipient retry, provider backoff | provider IDs stored for all send attempts |
| Engagement tracking normalizer | provider webhook | Campaign Service | Ready with provider dependency | replay ledger and poison-message quarantine | open, click, bounce, complaint, unsubscribe handling |
| Email delta sync | provider hint or polling schedule | Activity Sync Service | Ready with provider dependency | cursor checkpointing and reauth flow | deduped timeline entries |
| Calendar delta sync | provider hint or polling schedule | Activity Sync Service | Ready with provider dependency | recurrence-aware replay and conflict queue | meeting upsert and attendee-safe merge |
| Export materializer | export job queued | Export Service | Ready | chunk large jobs, resume from batch cursor | encrypted output and manifest |
| GDPR erasure executor | request approved | Privacy Service | Ready | idempotent delete/anonymize steps, downstream task retries | operational redaction complete and evidence stored |
| Outbox relay | new unpublished outbox row | Shared Platform Worker | Ready | exactly-once publish not required, at-least-once with idempotent consumers | durable publish timestamps and retry counters |
| Search projection updater | domain events | Shared Platform Worker | Ready | replay from outbox or compacted topic | account/contact/opportunity/activity search freshness |

---

## 3. External Integration Readiness

| Integration | Scope | Status | Blocking External Work | Internal Readiness Notes |
|---|---|---|---|---|
| Google Workspace | email and calendar sync | Ready with provider dependency | OAuth app registration, Pub/Sub/webhook setup, quota approval | provider IDs, cursor model, token refresh, replay logic already specified |
| Microsoft 365 | email and calendar sync | Ready with provider dependency | Azure app registration, Graph subscriptions, tenant consent | same internal adapter model as Google with provider-specific translation |
| Email delivery provider | campaigns and transactional email | Ready with provider dependency | verified sending domain, bounce/complaint webhooks | suppression and tracking model fully specified |
| ERP or finance system | closed-won handoff and account enrichment | Ready with provider dependency | contract for payload mapping and replay endpoint | use outbox, signed webhooks, reconciliation queue |
| Identity provider | SSO and optional SCIM | Ready with provider dependency | enterprise IdP metadata and group mapping | auth/policy design ready; SCIM remains optional for v1.0 |
| Slack or Teams | notifications | Ready with provider dependency | webhook or bot registration | non-blocking alerts only |
| Warehouse export | analytics feeds | Ready with provider dependency | target schema agreement and credentials | CDC/export manifests and tenant-safe transforms defined |

---

## 4. Deferred or Optional Extensions

| Capability | Status | Reason |
|---|---|---|
| ML-assisted lead scoring model | Deferred extension | v1.0 ships with deterministic rule engine; model inference can plug into the same score history contract later. |
| Native SMS campaign execution | Deferred extension | communication preference and campaign abstractions support it, but provider contracts are not finalized. |
| AI-generated deal coaching | Deferred extension | outside current README scope and not required for core CRM build. |

## Acceptance Criteria

- Every API or job in the CRM scope has an owner, readiness state, and done criteria.
- “Ready” rows can be assigned directly to engineering teams without reopening product discovery.
- Provider-dependent work is separated from internal implementation so teams can parallelize effectively.
