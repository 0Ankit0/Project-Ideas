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
