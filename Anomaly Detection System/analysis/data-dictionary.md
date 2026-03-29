# Data Dictionary

This data dictionary is the canonical reference for **Anomaly Detection System**. It defines shared terminology, entity semantics, and governance controls required to keep anomaly detection workflows consistent across teams and services.

## Scope and Goals
- Establish a stable vocabulary for architecture, API, analytics, and operations teams.
- Define minimum required fields for core entities and expected relationship boundaries.
- Document data quality and retention controls needed for production readiness.

## Core Entities
| Entity | Description | Required Attributes |
|---|---|---|
| TenantOrOrganization | Top-level ownership boundary for data segregation | `org_id, name, status, region, created_at` |
| UserOrActor | Human/system principal that performs actions | `actor_id, org_id, role, status, last_active_at` |
| PrimaryRecord | Main lifecycle object handled by the platform | `record_id, org_id, state, owner_id, created_at, updated_at` |
| ChildTransaction | Operational transaction or sub-step linked to primary record | `txn_id, record_id, txn_type, amount_or_value, occurred_at` |
| PolicyOrRule | Versioned policy configuration that influences decisions | `policy_id, scope, version, effective_from, effective_to` |
| AuditEvent | Append-only evidence for state changes and controls | `audit_id, record_id, actor_id, action, reason_code, occurred_at` |

## Canonical Relationship Diagram
```mermaid
erDiagram
    TENANTORORGANIZATION ||--o{ USERORACTOR : owns
    TENANTORORGANIZATION ||--o{ PRIMARYRECORD : contains
    PRIMARYRECORD ||--o{ CHILDTRANSACTION : has
    POLICYORRULE ||--o{ PRIMARYRECORD : governs
    PRIMARYRECORD ||--o{ AUDITEVENT : audited_by
    USERORACTOR ||--o{ AUDITEVENT : performs
```

## Data Quality Controls
1. All write paths enforce required-field validation and referential integrity for mandatory foreign keys.
2. External imports must include provenance metadata (`source_system`, `source_ref`, `ingested_at`).
3. Status/state fields use controlled vocabularies and reject unknown values.
4. Duplicate detection runs on natural keys where business identity collisions are likely.
5. Sensitive fields carry classification tags to drive masking, encryption, and export behavior.

## Retention and Audit
- Operational records remain online for active workflow windows and support forensic queries.
- Historical records move to archive tiers by policy without breaking traceability.
- Audit events are immutable and linked through correlation ids for incident analysis.

## Purpose and Scope
Defines field semantics, type constraints, ranges, units, and lineage for operational and model data.

## Assumptions and Constraints
- All producers use schema registry with compatibility checks.
- Dictionary entries include owner, source-of-truth, and PII tag.
- Feature columns have freshness and nullability guarantees.

### End-to-End Example with Realistic Data
`event_id` (string, immutable), `feature_velocity_5m` (int, 0-500), `anomaly_score` (float, 0-1), `model_version` (string, semantic + hash), `disposition` (enum pending/true_positive/false_positive/benign).

## Decision Rationale and Alternatives Considered
- Added units/range columns to prevent silent interpretation errors.
- Rejected “free text definition only” format due insufficient data contract rigor.
- Linked dictionary to event catalog for lineage traceability.

## Failure Modes and Recovery Behaviors
- Producer sends out-of-range value -> schema validator rejects and records violation metric.
- Undocumented column appears -> ingestion blocks until dictionary updated.

## Security and Compliance Implications
- PII-tagged fields require encryption and restricted access annotations.
- Dictionary includes retention/deletion policy by field class.

## Operational Runbooks and Observability Notes
- Data quality dashboard reads dictionary constraints as runtime checks.
- Runbook explains schema rollback and replay when violations spike.
