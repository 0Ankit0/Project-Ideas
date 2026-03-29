# Deployment Diagram - Document Intelligence System

```mermaid
graph TB
    subgraph "Application Tier"
        API1[API Server<br/>FastAPI]
        API2[API Server<br/>FastAPI]
        WORKER1[Worker<br/>Python/Celery]
        WORKER2[Worker<br/>Python/Celery]
    end
    
    subgraph "AI Services"
        OCR[OCR Service<br/>Tesseract/GPU]
        NER[NER Service<br/>spaCy/GPU]
        CLS[Classifier<br/>TensorFlow]
    end
    
    subgraph "Data & Storage"
        DB[(PostgreSQL)]
        S3[S3 Bucket]
        QUEUE[RabbitMQ]
        REDIS[(Redis)]
    end
    
    subgraph "Monitoring"
        PROM[Prometheus]
        GRAF[Grafana]
    end
    
    LB[Load Balancer] --> API1
    LB --> API2
    
    API1 --> S3
    API1 --> DB
    API1 --> QUEUE
    API1 --> REDIS
    
    QUEUE --> WORKER1
    QUEUE --> WORKER2
    
    WORKER1 --> OCR
    WORKER1 --> NER
    WORKER1 --> CLS
    WORKER1 --> DB
    
    API1 --> PROM
    PROM --> GRAF
```

## Kubernetes Deployment

```yaml
# API Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: document-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: doc-intelligence-api:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url

---
# Worker Deployment with GPU
apiVersion: apps/v1
kind: Deployment
metadata:
  name: processing-worker
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: worker
        image: doc-intelligence-worker:latest
        resources:
          requests:
            memory: "8Gi"
            cpu: "4"
            nvidia.com/gpu: 1
          limits:
            memory: "16Gi"
            cpu: "8"
            nvidia.com/gpu: 1
```

## Node Specifications

| Service | CPU | RAM | GPU | Purpose |
|---------|-----|-----|-----|---------|
| API Server | 2 vCPU | 4GB | - | Handle HTTP requests |
| Processing Worker | 4 vCPU | 8GB | T4/V100 | AI processing |
| OCR Service | 4 vCPU | 8GB | Optional | Text extraction |
| NER Service | 4 vCPU | 8GB | T4 | Entity extraction |
| Database | 4 vCPU | 16GB | - | PostgreSQL |
| RabbitMQ | 2 vCPU | 4GB | - | Message queue |
---

## AI/ML Operations Addendum

### Extraction & Classification Pipeline Detail
- Ingestion normalizes PDFs/images (de-skew, orientation correction, denoise, page splitting) before OCR inference, and preserves page-level provenance (`document_id`, `page_no`, `checksum`) for reproducibility.
- OCR outputs word-level tokens with bounding boxes and confidence, then layout reconstruction builds reading order, sections, tables, and key-value candidates for downstream models.
- Classification runs as a two-stage ensemble: coarse document family classifier followed by template/domain subtype classifier; routing controls which extraction graph, validation rules, and post-processors execute.
- Extraction combines multiple strategies (template anchors, layout-aware transformer NER, regex/rule validators, and table parsers) with conflict resolution and source attribution at field level.

### Confidence Thresholding Logic
- Every predicted artifact (doc type, entity, field, table cell) carries calibrated confidence; calibration is maintained per model version using held-out reliability sets (temperature scaling/isotonic).
- Thresholds are policy-driven and tiered: **auto-accept**, **review-required**, and **reject/reprocess** bands, configurable per document type and field criticality (e.g., totals, IDs, legal dates).
- Composite confidence uses weighted signals: model probability, OCR quality, extraction-rule agreement, cross-field consistency checks, and historical drift indicators.
- Dynamic threshold overrides apply during incidents (e.g., OCR degradation or new template rollout) with explicit expiry, audit log entries, and rollback playbooks.

### Human-in-the-Loop Review Flow
- Low-confidence or policy-flagged documents enter a reviewer queue with SLA tiers, reason codes, and pre-highlighted spans/bounding boxes to minimize correction time.
- Reviewer edits are captured as structured feedback (`before`, `after`, `reason`, `reviewer_role`) and linked to model/version metadata for supervised retraining datasets.
- Dual-review and adjudication is required for high-risk fields or regulated document classes; disagreements are labeled and retained for error analysis.
- Review outcomes feed active-learning samplers that prioritize uncertain/novel templates while enforcing PII minimization and role-based masking in annotation tools.

### Model Lifecycle Governance
- Model registry tracks lineage across datasets, feature pipelines, prompts/config, evaluation reports, approval status, and deployment environment.
- Promotion gates enforce quality thresholds (classification F1, field-level precision/recall, calibration error, latency/cost SLOs) plus fairness and security checks before production release.
- Runtime monitoring covers drift (input schema, token distributions, template novelty), confidence shifts, reviewer override rates, and business KPI regressions with automated alerts.
- Rollout strategy uses canary/shadow deployments, version pinning per tenant/workflow, and deterministic rollback with incident postmortems and governance sign-off.

### Deployment Extensions
- Define rollout units for model-serving pods, policy service replicas, and reviewer queue processors with blue/green and canary controls.
---


## Implementation-Ready Deep Dive

### Operational Control Objectives
| Objective | Target | Owner | Evidence |
|---|---|---|---|
| Straight-through processing rate | >= 75% for baseline templates | ML Ops Lead | Weekly quality report |
| Critical-field precision | >= 99% on regulated fields | Applied ML Engineer | Offline eval + reviewer sample audit |
| Reviewer turnaround SLA | P95 < 2 business hours | Review Ops Manager | Queue dashboard + SLA breach alerts |
| Rollback readiness | < 15 min rollback execution | Platform SRE | Change ticket + rollback drill logs |

### Implementation Backlog (Must-Have)
1. Implement per-field threshold policy engine with policy versioning and tenant/document-type overrides.
2. Add calibrated confidence tracking table and nightly reliability job with ECE/Brier drift alarms.
3. Introduce reviewer work allocation service (skill-based routing, dual-review for high-risk forms).
4. Create retraining dataset contracts (gold labels, weak labels, rejected examples, hard-negative mining).
5. Establish model governance workflow (proposal -> validation -> canary -> promotion -> archive).

### Production Acceptance Checklist
- [ ] End-to-end traceability from uploaded file to exported structured payload.
- [ ] Full audit trail for every manual correction and model/policy decision.
- [ ] Canary release + rollback automation validated in staging and production-like data.
- [ ] Drift/quality SLO dashboards wired to paging policy and incident template.
- [ ] Security controls for PII redaction, purpose-limited access, and retention enforcement.

### Deployment Policies
- Pin each deployment to `model_snapshot_id` and `policy_bundle_id` to guarantee reproducibility.
- Use immutable release manifests and signed SBOMs for all serving containers and workers.
- Enforce progressive delivery with automatic abort on error/quality SLO breach.

### Mermaid: Deployment Topology
```mermaid
flowchart TB
    subgraph K8s
      GW[API Pods]
      ORCH[Orchestrator Pods]
      INF[Inference Pods]
      POL[Policy Pods]
      REV[Review Worker Pods]
    end
    GW-->ORCH-->INF-->POL
    POL-->REV
```

