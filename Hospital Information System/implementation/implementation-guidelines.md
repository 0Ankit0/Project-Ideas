# Implementation Guidelines

## Purpose
Provide implementation guidance for building the **Hospital Information System** microservices, APIs, integrations, and operational controls in a consistent and release-ready way.

## Engineering Principles
1. **Source-of-truth ownership**: each service owns its schema, state machine, and public contracts.
2. **Transactional outbox**: every event emitted from a mutating workflow comes from a committed outbox record.
3. **Idempotent commands**: mutating APIs and consumers must tolerate retried requests and replayed events.
4. **Fail secure**: if authorization, consent evaluation, or audit capture is unavailable, PHI-bearing operations fail closed unless approved emergency mode applies.
5. **Observable by default**: correlation ID, actor, patient, encounter, and facility context are included in logs, traces, and audit envelopes.

## Service Implementation Standards

| Concern | Required Standard |
|---|---|
| API style | REST for client and partner requests, gRPC only for internal latency-sensitive checks such as CDS or eligibility |
| Data access | Repository pattern per bounded context, no direct cross-service SQL |
| Events | Avro or JSON schema under version control, compatibility checks in CI |
| Validation | request schema validation plus domain rule validation before write |
| Concurrency | optimistic locking for record edits, version checks for long-lived forms |
| Security | RBAC plus ABAC for sensitive compartments, mTLS for internal traffic |
| Audit | immutable append for PHI reads, writes, corrections, merges, break-glass, replay actions |
| Logging | structured JSON with PHI redaction and event classification |

## Domain-Specific Coding Requirements
- **Patient Service** must centralize EMPI matching, MRN issuance, alias lineage, consent registry, and merge or unmerge orchestration.
- **ADT Service** must own bed occupancy calculations, transfer queue logic, room cleaning status, and ADT message generation.
- **Clinical Service** must own encounter lifecycle, note states, diagnoses, care team assignments, and shared order shell model.
- **Pharmacy Service** must own formulary cache, verification queue, dispense states, MAR event creation, and controlled substance audit.
- **Lab and Radiology Services** must own order execution state, result versioning, critical alert detection, and outbound result corrections.
- **Billing and Insurance Services** must consume authoritative events, build charge and claim projections, and preserve every payer interaction version.

## Implementation Roadmap

| Wave | Scope | Exit Gate |
|---|---|---|
| Wave 1 | Patient identity, registration, consent, audit, staff directory | search-before-create, MRN issuance, consent checks, PHI audit logs |
| Wave 2 | ADT, bed board, transfer history, discharge basics | admission, transfer, discharge journeys proven end to end |
| Wave 3 | Encounters, notes, diagnoses, order entry, FHIR patient and encounter resources | signed note immutability and order state machine validated |
| Wave 4 | Pharmacy, lab, radiology workflows, critical results, medication administration | closed-loop order to result and MAR evidence validated |
| Wave 5 | Billing, insurance, coding handoff, claim workflows | clean claim generation and denial rework validated |
| Wave 6 | Downtime tooling, replay tooling, resilience hardening, DR drill | downtime reconciliation and regional failover drill complete |

## Required Test Strategy

| Level | Required Coverage |
|---|---|
| Unit | domain invariants, state transitions, match scoring, charge rules, consent decisions |
| Integration | database transactions, outbox publishing, partner connector translation, queue consumer idempotency |
| Contract | OpenAPI, FHIR resources, HL7 messages, Kafka schema compatibility |
| Workflow | registration to admission, med order to administration, critical result escalation, discharge to claim |
| Resilience | retry, replay, duplicate message, timeout, downstream outage, partial failure |
| Security | RBAC, ABAC, break-glass, audit fail-secure, log redaction, certificate rotation |

## Readiness Gates for Each Service
1. OpenAPI and event schemas published with examples.
2. State machine documented and covered by automated tests.
3. Audit events mapped for every privileged and PHI-touching action.
4. Dashboards and alerts exist for latency, errors, saturation, queue lag, and data freshness.
5. Runbook covers outage, replay, rollback, and manual reconciliation.
6. Production configuration reviewed for secrets, certificates, and egress dependencies.

## Implementation Patterns
- Use a shared correlation middleware that injects request ID, actor claims, patient context, and facility context into logs and audit envelopes.
- Model corrections as new versions with superseding links, not in-place mutation of signed or fulfilled records.
- Use sagas only for cross-service workflows where one service remains the source of truth and compensating actions are explicit.
- Keep FHIR adapters thin. Resource validation and mapping live in adapter layer, business rules stay in domain services.
- Persist downtime-entered records with provenance fields so reconciliation can distinguish them from online transactions.

## Security and Compliance Checklist
- MFA enabled for clinical, billing, admin, and support roles.
- Break-glass API requires reason code, free-text justification, TTL, and retrospective reviewer assignment.
- PHI fields redacted from logs, traces, analytics events, and notification payloads by default.
- Consent and privacy flags cached only with short TTL and explicit invalidation on update.
- Merge, unmerge, correction, replay, and bulk export commands require elevated roles and dual approval where policy dictates.

## Release Checklist
- Migration rehearsal passed against production-like data volume.
- Rollback steps tested or documented as no-downgrade with mitigation plan.
- Clinical operations sign-off obtained for workflow changes touching patient safety.
- Interface mapping test evidence attached for HL7, FHIR, and payer integrations.
- Post-release verification covers census, active orders, MAR, critical result queue, claims queue, and audit ingestion.

