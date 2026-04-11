# Data Flow Diagram - Anomaly Detection System

## Level 0: Context

```mermaid
flowchart LR
    SOURCE((Data Sources)) -->|Metrics| ADS[Anomaly<br/>Detection<br/>System]
    ADS -->|Alerts| USERS((Operators))
```

## Level 1: Main Processes

```mermaid
flowchart TB
    SOURCE((Data Sources))
    USERS((Operators))
    
    P1[1.0<br/>Data<br/>Ingestion]
    P2[2.0<br/>Feature<br/>Engineering]
    P3[3.0<br/>Anomaly<br/>Detection]
    P4[4.0<br/>Alert<br/>Processing]
    P5[5.0<br/>Model<br/>Management]
    P6[6.0<br/>Feedback &<br/>Labeling]
    P7[7.0<br/>Audit &<br/>Compliance]
    
    D1[(Raw Data)]
    D2[(Features)]
    D3[(Anomalies)]
    D4[(Models)]
    D5[(Alert Rules)]
    D6[(Feedback)]
    D7[(Webhook Endpoints)]
    D8[(Audit Logs)]
    
    SOURCE -->|Metrics| P1
    P1 -->|Data Points| D1
    D1 -->|Raw| P2
    P2 -->|Computed| D2
    D2 -->|Features| P3
    D4 -->|Model| P3
    P5 -->|Model Versions| D4
    P3 -->|Anomalies| D3
    D3 -->|Anomalies| P4
    D5 -->|Rules| P4
    D7 -->|Webhooks| P4
    P4 -->|Notifications| USERS
    USERS -->|Feedback Labels| P6
    P6 -->|Feedback| D6
    D6 -->|Labeled Data| P5
    P1 -->|Audit Event| P7
    P3 -->|Audit Event| P7
    P4 -->|Audit Event| P7
    P5 -->|Audit Event| P7
    P6 -->|Audit Event| P7
    P7 -->|Records| D8
```

## Level 2: Anomaly Detection (3.0)

```mermaid
flowchart TB
    P3_1[3.1<br/>Load<br/>Model]
    P3_2[3.2<br/>Score<br/>Data]
    P3_3[3.3<br/>Apply<br/>Threshold]
    P3_4[3.4<br/>Create<br/>Anomaly]
    
    D2[(Features)]
    D3[(Anomalies)]
    D4[(Models)]
    
    D2 --> P3_2
    D4 --> P3_1
    P3_1 --> P3_2
    P3_2 --> P3_3
    P3_3 -->|Above Threshold| P3_4
    P3_4 --> D3
```

## Purpose and Scope
Describes data lineage, trust boundaries, and transformation stages from raw events to analyst-facing artifacts.

## Assumptions and Constraints
- Raw payload retention differs from derived feature retention.
- PII tokenization happens before model-serving zone.
- Every transform stage emits lineage metadata.

### End-to-End Example with Realistic Data
Raw event with `email`/`device_id` enters restricted zone, tokenization service outputs hashed IDs, feature builder computes aggregates, scoring consumes derived features only, case UI retrieves redacted evidence.

## Decision Rationale and Alternatives Considered
- Chose dual-zone data design for security and performance.
- Rejected direct UI access to raw data store.
- Lineage IDs propagated end-to-end for replay and audit.

## Failure Modes and Recovery Behaviors
- Tokenization service outage -> hold high-sensitivity flows; allow low-sensitivity flows with policy exceptions disabled.
- Lineage metadata loss -> block downstream promotion until restored.

## Security and Compliance Implications
- DFD annotates data-classification transitions at each edge.
- Retention/deletion obligations are attached to sink nodes.

## Operational Runbooks and Observability Notes
- Lineage completeness and tokenization error rate are on compliance dashboards.
- Runbook covers replay with lineage integrity checks.


## Bounded Contexts and Ownership

| Bounded Context | Core Responsibilities | Owned Data | Upstream Dependencies | Downstream Consumers |
|---|---|---|---|---|
| Ingestion Context | Source auth, schema enforcement, idempotent event intake | Raw event envelope, source schema version, ingest status | Producers, source registry | Feature context, audit context |
| Feature Context | Online/offline feature computation and freshness checks | Feature vectors, feature lineage, freshness metadata | Ingestion context, feature store | Detection context, training context |
| Detection Context | Real-time scoring, policy thresholds, anomaly decisioning | Score outputs, decision reason codes, model invocation metadata | Feature context, model context | Alerting context, case management |
| Model Management Context | Train/validate/register/deploy/monitor models | Model artifacts, model cards, validation metrics | Feature context, feedback context | Detection context, governance context |
| Alerting Context | Rule evaluation, dedup, channel dispatch, escalation | Alert state, channel receipts, suppression windows | Detection context, rule config | Operators, incident systems |
| Feedback Context | Label collection, analyst annotations, weak-label synthesis | Labels, adjudication metadata, confidence level | Alerting context, operator actions | Model management context |
| Governance & Audit Context | End-to-end lineage, compliance evidence, audit trails | Immutable audit events, lineage graph, retention metadata | All contexts | Compliance reporting, incident review |

## Event and Data Flow (Canonical Topics)

| Flow | Transport | Contract | SLA Budget | Notes |
|---|---|---|---|---|
| `raw.metrics.v1` -> `features.online.v2` | Kafka | Avro + schema registry compatibility `BACKWARD_TRANSITIVE` | < 120 ms p95 | Breaking schema changes blocked pre-ingest. |
| `features.online.v2` -> `scores.realtime.v2` | gRPC + protobuf | Feature vector + feature freshness stamp | < 80 ms p95 | Freshness > 120s marks score degraded. |
| `scores.realtime.v2` -> `anomalies.detected.v1` | Kafka | Decision payload + model/version IDs | < 40 ms p95 | Includes calibrated confidence interval. |
| `anomalies.detected.v1` -> `alerts.dispatch.v1` | Kafka | Alert candidate + dedup key | < 60 ms p95 | Dedup window default: 10 min per tenant/source. |
| `feedback.labels.v1` -> `training.candidates.v1` | Kafka + batch compaction | Label + provenance + adjudication state | < 15 min end-to-end | Delayed labels are backfilled incrementally. |

## Model Lifecycle Stages and Quality Gates

| Stage | Entry Criteria | Exit Criteria | Evidence Produced |
|---|---|---|---|
| Train | Approved dataset snapshot + feature definition hash | Training job success + reproducible artifact hash | Training run metadata, hyperparameters, artifact digest |
| Validate | Candidate model from train stage | Precision/recall/F1 + calibration + bias checks pass | Evaluation report, model card, risk classification |
| Deploy | Validation approved + change ticket + rollback target set | Canary/shadow success gates pass | Deployment record, traffic split evidence |
| Monitor | Model active in staging/prod | Drift/quality/latency within SLO or retraining trigger raised | Continuous metrics, drift reports, alert timeline |

### Mandatory Lifecycle Gates
- **Train -> Validate**: dataset checksum and feature parity check (online vs offline skew < 2%).
- **Validate -> Deploy**: no regression > 1.5% on weighted F1 against current production model.
- **Deploy -> Monitor**: 30-minute canary + 24-hour shadow comparison before full promotion.
- **Monitor -> Retrain**: trigger when drift/quality thresholds are violated for sustained interval.

## Feature Store Interaction Contract

- **Online store (Redis/Aerospike class)**: low-latency feature reads for scoring, strict TTL, write-through from stream features.
- **Offline store (lakehouse/parquet class)**: training and backfill datasets, point-in-time correct joins, lineage retention >= 400 days.
- **Parity controls**:
  - Feature definitions are versioned (`feature_set_id`, `feature_version`).
  - Every score logs `feature_set_id`, `freshness_ms`, and offline snapshot reference.
  - Promotion is blocked if online/offline feature parity tests fail.

## Feedback Loop Design

```mermaid
flowchart LR
    OP[Operator Label / Triage] --> FB[Feedback API]
    FB --> Q[(feedback.labels.v1)]
    Q --> ADJ[Adjudication + Delay Handling]
    ADJ --> FS[Label Store]
    FS --> TRIG[Retrain Trigger Evaluator]
    TRIG --> TRAIN[Training Pipeline]
    TRAIN --> REG[Model Registry]
    REG --> DEP[Canary/Shadow Deployment]
    DEP --> MON[Production Monitoring]
    MON --> OP
```

**Design notes**:
- Labels are confidence-scored (`human_verified`, `heuristic`, `imported`) before entering training candidates.
- Delayed labels are merged with event-time alignment so they do not contaminate recent-window online metrics.
- False-positive clusters create a temporary threshold policy overlay while retraining is in progress.
