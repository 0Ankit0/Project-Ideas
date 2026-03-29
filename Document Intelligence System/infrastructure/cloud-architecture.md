# Cloud Architecture - Document Intelligence System

## AWS Architecture

```mermaid
graph TB
    subgraph "AWS Cloud"
        subgraph "Compute"
            ECS[ECS Fargate<br/>API Servers]
            EC2[EC2 GPU<br/>Workers]
        end
        
        subgraph "AI Services"
            TEXTRACT[AWS Textract<br/>OCR]
            COMPREHEND[Amazon Comprehend<br/>NER Optional]
        end
        
        subgraph "Data"
            RDS[(RDS PostgreSQL)]
            S3[S3 Buckets<br/>Documents]
            SQS[SQS<br/>Job Queue]
            ELASTICACHE[(ElastiCache)]
        end
        
        subgraph "Monitoring"
            CLOUDWATCH[CloudWatch]
        end
    end
    
    ALB[Application LB] --> ECS
    ECS --> S3
    ECS --> RDS
    ECS --> SQS
    
    SQS --> EC2
    EC2 --> TEXTRACT
    EC2 --> RDS
    EC2 --> S3
```

## GCP Architecture

```mermaid
graph TB
    subgraph "Google Cloud"
        subgraph "Compute"
            GKE[GKE<br/>Kubernetes]
            COMPUTE[Compute Engine<br/>GPU Nodes]
        end
        
        subgraph "AI Services"
            VISION[Vision AI<br/>OCR]
            NL[Natural Language AI<br/>NER Optional]
        end
        
        subgraph "Data"
            CLOUD_SQL[(Cloud SQL)]
            GCS[Cloud Storage]
            PUB_SUB[Pub/Sub]
        end
    end
    
    LB[Cloud Load Balancing] --> GKE
    GKE --> GCS
    GKE --> CLOUD_SQL
    GKE --> PUB_SUB
    
    PUB_SUB --> COMPUTE
    COMPUTE --> VISION
    COMPUTE --> GCS
```

## Provider Mapping

| Component | AWS | GCP | Azure |
|-----------|-----|-----|-------|
| Container Runtime | ECS/EKS | GKE | AKS |
| OCR Service | Textract | Vision AI | Form Recognizer |
| NER (Optional) | Comprehend | Natural Language AI | Text Analytics |
| GPU Compute | EC2 P3/G4 | Compute Engine GPU | NC-series VMs |
| Database | RDS PostgreSQL | Cloud SQL | Azure PostgreSQL |
| Storage | S3 | Cloud Storage | Blob Storage |
| Queue | SQS | Pub/Sub | Service Bus |
| Cache | ElastiCache | Memorystore | Azure Cache |

## Cost Estimation (AWS)

| Tier | Monthly Cost | Specs |
|------|--------------|-------|
| **Starter** | ~$800 | API: t3.medium x2, Workers: CPU-only, Textract API |
| **Growth** | ~$2500 | Auto-scaling, g4dn.xlarge GPU x2, RDS Multi-AZ |
| **Enterprise** | ~$8000+ | Multi-region, p3.2xlarge GPU x4, HA |

**Key Cost Drivers**:
- GPU instances for AI models
- Cloud OCR API usage (pay per page)
- Document storage (S3)
- Data transfer (outbound)
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

### Cloud Architecture Extensions
- Map GPU/CPU workload separation, model artifact storage, feature/feedback data lake zones, and private networking for model endpoints and review tooling.
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

### Runtime Topology Guidance
- Separate inference GPU node pools from orchestration and review services with autoscaling boundaries.
- Use private service endpoints for OCR/LLM providers where supported; deny public egress by default.
- Mirror model registry and artifact store cross-region for recovery without stale policy versions.

### Mermaid: Cloud Reference Architecture
```mermaid
flowchart LR
    U[Users] --> CDN --> API
    API --> MQ[Queue]
    MQ --> WK[Workers]
    WK --> GPU[GPU Inference]
    WK --> DB[(Operational DB)]
    WK --> OBJ[(Object Storage)]
    DB --> BI[Monitoring/BI]
```

