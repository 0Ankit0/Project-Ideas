# Implementation Playbook

## 1. Delivery Goal
Ship a production-ready system for **real-time anomaly detection with <1s detection latency**.

### Target KPIs
- Detection Latency < 1s, False Positive Rate < 5%, True Positive Rate > 95%
- Availability target: 99.9%
- Mean time to recovery (MTTR): < 30 minutes

## 2. Implementation Scope (Must-Have)
Core services to implement:
- Ingestion, Feature Pipeline, Model Scoring, Alerting, Case Management
- Admin and operator console
- Monitoring, alerting, and audit logging
- Security controls (authentication, authorization, encryption)

## 3. Environment Setup
### Local
1. Install runtime dependencies as listed in `implementation/code-guidelines.md` (or `implementation/implementation-guidelines.md`).
2. Start required infrastructure (DB, cache, queue, search, object store) using Docker Compose.
3. Configure `.env` with local credentials and feature flags.
4. Seed baseline data for development and demo scenarios.

### Non-Production / Production
1. Provision cloud resources from `infrastructure/cloud-architecture.md`.
2. Configure network, subnets, WAF, and private endpoints from `infrastructure/network-infrastructure.md`.
3. Deploy workloads according to `infrastructure/deployment-diagram.md`.
4. Enable centralized logs, metrics, and traces.

## 4. Build Plan by Workstream
### A) Backend APIs
- Implement all endpoints from `detailed-design/api-design.md`.
- Add request/response validation, idempotency, pagination, filtering, and error contracts.
- Add retries, circuit breakers, and timeouts for downstream dependencies.

### B) Data Layer
- Implement schema from `detailed-design/erd-database-schema.md`.
- Add migrations and rollback scripts.
- Add indexes for read-heavy and write-heavy paths.
- Define retention and archival policies.

### C) Domain Logic
- Implement lifecycle and transitions from `detailed-design/state-machine-diagram.md`.
- Implement orchestration from `detailed-design/sequence-diagram.md` (or equivalent diagrams).
- Enforce all rules from `analysis/business-rules.md`.

### D) Frontend / Consumer Integration
- Implement consumer journeys from `analysis/use-case-descriptions.md` and `analysis/activity-diagram.md` (or equivalent).
- Add optimistic UI states, loading states, and error states.
- Add accessibility and localization support where applicable.

### E) Security & Compliance
- Enforce least-privilege IAM and role-based access control.
- Encrypt data in transit (TLS 1.2+) and at rest.
- Add audit trails for privileged and business-critical operations.
- Implement controls from `edge-cases/security-and-compliance.md`.

### F) Reliability & Operations
- Implement operational safeguards from `edge-cases/operations.md`.
- Add SLO dashboards and alerting thresholds.
- Add runbooks for incident triage and service restoration.

## 5. Testing Strategy (Release Blocking)
- Unit tests for domain logic and adapters.
- Integration tests for DB/cache/queue/external provider integrations.
- API contract tests for all public endpoints.
- End-to-end tests for top business flows and edge-cases.
- Load and stress tests aligned with documented performance targets.
- Security tests: authz/authn checks, OWASP top risks, secrets scanning.

## 6. Data & Migration Readiness
- Initial seed strategy and synthetic data generation.
- Backfill and replay strategy for historical data.
- Zero-downtime migration approach (expand-and-contract).
- Verified restore drills for backups.

## 7. CI/CD & Release Management
- CI gates: lint, type checks, unit tests, integration tests, SAST.
- Build immutable artifacts and sign releases.
- Progressive rollout: canary/blue-green with automatic rollback.
- Post-deploy smoke tests and synthetic monitoring.

## 8. Go-Live Readiness Checklist
- [ ] All required APIs implemented and contract-validated.
- [ ] Database migrations verified in staging.
- [ ] Critical edge-cases validated from `edge-cases/` docs.
- [ ] On-call rotation, escalation matrix, and runbooks active.
- [ ] Backups and restore tested successfully.
- [ ] Security review and threat model sign-off completed.
- [ ] Performance/load targets achieved in pre-production.
- [ ] Observability dashboards and alerts operational.

## 9. Handover Artifacts
- Architecture decision records (ADRs)
- API collections and schema definitions
- Operational runbooks and incident playbooks
- Environment variable catalog and secrets ownership
- Release checklist and rollback SOP

## 10. Definition of Done
System is considered implementation-ready and production-capable when:
1. Functional and non-functional requirements are traceable to tests.
2. All critical paths and edge-cases have automated test coverage.
3. Deployment and rollback are fully automated and repeatable.
4. Security, reliability, and operational controls are verified in staging.
5. Stakeholders sign off on KPI and acceptance criteria.

## Purpose and Scope
Operationalizes rollout strategy, canary checks, rollback criteria, and post-release validation.

## Assumptions and Constraints
- Canary traffic can be isolated by tenant and risk level.
- Rollout metrics are available in near real-time.
- Rollback command path is pre-tested before release day.

### End-to-End Example with Realistic Data
Release `2026.03.2`: 5% canary for 30 minutes; gates: latency p95 <=250 ms, precision drop <1.5%, PSI<0.2. If gate fails, auto-rollback and open incident with diff summary.

## Decision Rationale and Alternatives Considered
- Adopted progressive rollout to reduce blast radius.
- Rejected big-bang deploy due historical incident rate.
- Integrated quality + reliability gates for balanced promotion decisions.

## Failure Modes and Recovery Behaviors
- Canary good but full rollout degrades -> staged promotion pauses and scales by cohort.
- Rollback fails partially -> execute switchback playbook and freeze deploy pipeline.

## Security and Compliance Implications
- Playbook requires key/secret rotation checks before promotion.
- Release evidence package retained for compliance with model version hashes.

## Operational Runbooks and Observability Notes
- Post-release watch window and ownership roster are mandatory.
- Runbook includes emergency disable switches for high-risk policies.


## 11. Model Versioning Contract

### Version Identifier
`<algorithm>-<major>.<minor>.<patch>+<feature_set_hash>-<train_date>`

Example: `iforest-3.4.1+fset_a91c2d-2026-04-11`

### Required Model Metadata
- `model_id` (immutable UUID)
- `model_version` (semantic + feature hash)
- `feature_set_id` and `feature_schema_version`
- `training_data_snapshot_id` and checksum
- `metrics` (precision/recall/F1/AUC/calibration)
- `approved_by` and approval timestamp
- `rollback_parent_version`

### Compatibility Rules
- **Major** version changes require shadow + canary.
- **Minor** changes require canary only.
- **Patch** changes allowed with accelerated canary if no schema/runtime changes.
- Scoring service must reject models with incompatible feature schema.

## 12. Canary and Shadow Rollout Process

1. Register candidate model and validate metadata contract.
2. Start **shadow** mode (0% user impact, 100% mirrored traffic) for minimum 24 hours or 1M events.
3. Evaluate shadow gates:
   - weighted F1 regression <= 1.0%
   - p95 latency increase <= 10%
   - no severe explainability contract failures.
4. Start **canary** traffic: 1% -> 5% -> 20% -> 50% -> 100%.
5. Promotion gates at each step use 15-minute and 60-minute windows.
6. Any failed gate triggers automatic rollback and incident creation.

## 13. Drift Detection Thresholds

| Signal | Threshold | Window | Action |
|---|---|---|---|
| Population Stability Index (PSI) | > 0.20 warning, > 0.30 critical | 24h rolling | warning opens ticket, critical blocks promotions |
| Jensen-Shannon Divergence | > 0.10 warning, > 0.15 critical | 24h | same as above |
| Score distribution shift (KS test p-value) | < 0.01 | 6h | trigger drift investigation |
| Precision proxy drop | > 3% absolute | 24h | start expedited retraining evaluation |
| False-positive rate increase | > 2x baseline | 12h | apply temporary suppression profile |

## 14. Retraining Trigger Policy

Retraining starts when **any critical trigger** or **two warning triggers** are observed.

### Critical Triggers
- PSI > 0.30 for >= 2 consecutive windows.
- Precision proxy drop > 5% absolute for >= 6h.
- False-positive storm for tier-1 tenants sustained >= 30m.
- Feature schema drift marked breaking.

### Warning Triggers
- PSI > 0.20 once.
- Delayed label backlog > 48h for > 20% of new anomalies.
- Shadow-candidate outperforms primary by >= 2% weighted F1 for 3 days.

### Guardrails
- Minimum retrain interval per model family: 24h (except Sev1 override).
- Retrain jobs must use point-in-time correct data snapshot.
- All retrains generate a model card delta vs current production model.

## 15. Rollback Playbooks

### A) Model Quality Regression Rollback
1. Freeze promotions and mark candidate as `blocked`.
2. Shift traffic to last-known-good model version.
3. Enable conservative threshold overlay to prevent false-positive storm.
4. Start incident with quality diff report and cohort impact.
5. Require post-incident approval before re-attempting rollout.

### B) Model Runtime Failure Rollback
1. Detect elevated 5xx/timeout from scoring adapter.
2. Route to fallback model or rules-only scoring profile.
3. Roll back serving manifest to prior stable digest.
4. Reconcile queued events and annotate degraded decisions.

### C) Feature Contract Break Rollback
1. Detect feature schema mismatch at scoring boundary.
2. Disable new feature version reads and pin previous `feature_set_id`.
3. Trigger backfill correction workflow.
4. Resume progressive rollout only after parity checks pass.
