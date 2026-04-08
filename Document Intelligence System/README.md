# Document Intelligence System

An enterprise-grade, AI-powered platform for automated document ingestion, OCR processing, intelligent classification, structured data extraction, and compliant export to downstream ERP and database systems.

## Documentation Structure

Project root artifact: [`traceability-matrix.md`](./traceability-matrix.md) provides cross-phase requirement-to-implementation linkage.


```
Document Intelligence System/
├── README.md                          # This file — project overview and navigation
├── traceability-matrix.md
├── requirements/
│   ├── requirements-document.md       # Functional (FR-01–FR-35) and non-functional requirements
│   └── user-stories.md                # 20 user stories across 6 personas with acceptance criteria
├── analysis/
│   ├── use-case-diagram.md            # Mermaid use-case diagram — actors and system boundaries
│   ├── use-case-descriptions.md       # UC-01–UC-08 full structured descriptions
│   ├── system-context-diagram.md      # C4 Level-1 context diagram with external systems
│   ├── activity-diagram.md            # Activity diagrams: processing pipeline, review, retraining
│   ├── bpmn-swimlane-diagram.md       # BPMN swimlane: full pipeline and review workflow
│   ├── data-dictionary.md             # Entity field tables, ER diagram, data quality controls
│   ├── business-rules.md              # BR-01–BR-09 rules, evaluation pipeline, override handling
│   └── event-catalog.md               # 13 domain events, contracts, SLOs, sequence diagram
├── high-level-design/
│   ├── system-sequence-diagram.md     # System-level sequence: submission, OCR+class, review+export
│   ├── domain-model.md                # Mermaid class diagram of all core entities
│   ├── data-flow-diagram.md           # DFD Level 0 and Level 1
│   ├── architecture-diagram.md        # Layered architecture with technology choices
│   └── c4-context-container.md        # C4 Level 1 + Level 2 diagrams
├── detailed-design/
│   ├── class-diagram.md               # Python class hierarchy with OCR/ML components
│   ├── sequence-diagram.md            # 5 detailed sequence diagrams
│   ├── state-machine-diagram.md       # Document, ReviewTask, ModelVersion state machines
│   ├── erd-database-schema.md         # Full PostgreSQL DDL with indexes and constraints
│   ├── component-diagram.md           # Component diagram with service interfaces
│   ├── api-design.md                  # Full REST API spec with JSON examples
│   └── c4-component.md                # C4 Level 3 for OCR, Extraction, Review services
├── infrastructure/
│   ├── deployment-diagram.md          # Kubernetes deployment with GPU node pools
│   ├── network-infrastructure.md      # VPC, security zones, subnets
│   └── cloud-architecture.md          # AWS/GCP cloud architecture with ML services
├── implementation/
│   ├── code-guidelines.md             # Python standards, project structure, code examples
│   ├── c4-code-diagram.md             # C4 Level 4 code structure for Document Worker
│   └── implementation-playbook.md     # 8-phase delivery plan with milestones
└── edge-cases/
    ├── README.md                      # Overview table of all edge cases
    ├── document-ingestion.md          # Corrupted PDF, oversized batch, duplicates, etc.
    ├── ocr.md                         # Low DPI, rotation, handwriting, provider timeout
    ├── classification.md              # Ambiguous type, new template, multi-doc file
    ├── extraction.md                  # Missing fields, table spanning pages, NER overlap
    ├── validation-and-review.md       # Rule conflicts, SLA breach, concurrent edits
    ├── api-and-ui.md                  # Large export, cursor expiry, JWT mid-upload
    ├── security-and-compliance.md     # PII exposure, IDOR, audit gap, retention violation
    └── operations.md                  # OCR outage, GPU exhaustion, model drift, Kafka lag
```

## Key Features

| Feature | Description |
|---|---|
| **Multi-format Ingestion** | PDF, TIFF, JPEG, PNG, Word (.docx), Excel (.xlsx) — up to 500 MB per batch |
| **Cloud OCR** | AWS Textract and Google Vision API with confidence scoring; Tesseract fallback |
| **Document Classification** | Fine-tuned LayoutLM model — invoice, contract, receipt, medical record, tax form, ID document |
| **Structured Extraction** | Template-based and model-based field extraction with per-field confidence |
| **Validation Engine** | Rule-based validation: regex, cross-field, lookup table, and ML-scored validation |
| **Human-in-the-Loop Review** | Priority queue with SLA enforcement (P1 ≤ 4 h, P2 ≤ 24 h, P3 ≤ 72 h) |
| **PII Redaction** | NER-based auto-detection and redaction of SSN, DOB, bank account numbers |
| **ERP Export** | Signed export manifests to SAP, Oracle, and generic REST/SFTP endpoints |
| **MLOps Pipeline** | Retraining with ≥500 validated samples per class and ≥80% inter-annotator agreement |
| **Audit Trail** | Immutable audit log for every state transition, review decision, and export event |

## Getting Started

- Review [`traceability-matrix.md`](./traceability-matrix.md) first to navigate requirement-to-implementation coverage across phases.
### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker / Kubernetes
- AWS account (Textract) or GCP account (Vision API)

### Quick Start

```bash
# Clone and install
git clone https://github.com/your-org/document-intelligence-system
cd document-intelligence-system
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env: DATABASE_URL, AWS_ACCESS_KEY_ID, OCR_PROVIDER, REDIS_URL

# Run database migrations
alembic upgrade head

# Start services
docker-compose up -d redis postgres
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Submit a test batch
curl -X POST http://localhost:8000/batches \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@invoice_sample.pdf" \
  -F "metadata={\"source\":\"accounts_payable\",\"priority\":\"P2\"}"
```

### Environment Variables

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@localhost/dis` |
| `REDIS_URL` | Redis for task queue and cache | `redis://localhost:6379/0` |
| `OCR_PROVIDER` | `textract`, `google_vision`, or `tesseract` | `textract` |
| `AWS_REGION` | AWS region for Textract | `us-east-1` |
| `S3_BUCKET` | Document storage bucket | `dis-documents-prod` |
| `MLFLOW_TRACKING_URI` | MLflow server URL | `http://mlflow:5000` |
| `PII_REDACTION_ENABLED` | Enable auto-PII redaction (BR-05) | `true` |
| `ENCRYPTION_KEY` | AES-256 key for PII field encryption | `base64-encoded-32-byte-key` |

## Documentation Status

- ✅ Traceability coverage is available via [`traceability-matrix.md`](./traceability-matrix.md).
| Document | Status | Last Updated |
|---|---|---|
| Requirements Document | ✅ Complete | 2025-01 |
| User Stories | ✅ Complete | 2025-01 |
| Use Case Diagram | ✅ Complete | 2025-01 |
| Use Case Descriptions | ✅ Complete | 2025-01 |
| System Context Diagram | ✅ Complete | 2025-01 |
| Activity Diagrams | ✅ Complete | 2025-01 |
| BPMN Swimlane Diagrams | ✅ Complete | 2025-01 |
| Data Dictionary | ✅ Complete | 2025-01 |
| Business Rules | ✅ Complete | 2025-01 |
| Event Catalog | ✅ Complete | 2025-01 |
| System Sequence Diagrams | ✅ Complete | 2025-01 |
| Domain Model | ✅ Complete | 2025-01 |
| Data Flow Diagram | ✅ Complete | 2025-01 |
| Architecture Diagram | ✅ Complete | 2025-01 |
| C4 Context + Container | ✅ Complete | 2025-01 |
| Class Diagram | ✅ Complete | 2025-01 |
| Sequence Diagrams | ✅ Complete | 2025-01 |
| State Machine Diagrams | ✅ Complete | 2025-01 |
| ERD / Database Schema | ✅ Complete | 2025-01 |
| Component Diagram | ✅ Complete | 2025-01 |
| API Design | ✅ Complete | 2025-01 |
| C4 Component Diagram | ✅ Complete | 2025-01 |
| Deployment Diagram | ✅ Complete | 2025-01 |
| Network Infrastructure | ✅ Complete | 2025-01 |
| Cloud Architecture | ✅ Complete | 2025-01 |
| Code Guidelines | ✅ Complete | 2025-01 |
| C4 Code Diagram | ✅ Complete | 2025-01 |
| Implementation Playbook | ✅ Complete | 2025-01 |
| Edge Cases — Ingestion | ✅ Complete | 2025-01 |
| Edge Cases — OCR | ✅ Complete | 2025-01 |
| Edge Cases — Classification | ✅ Complete | 2025-01 |
| Edge Cases — Extraction | ✅ Complete | 2025-01 |
| Edge Cases — Validation & Review | ✅ Complete | 2025-01 |
| Edge Cases — API & UI | ✅ Complete | 2025-01 |
| Edge Cases — Security & Compliance | ✅ Complete | 2025-01 |
| Edge Cases — Operations | ✅ Complete | 2025-01 |

---

*Document Intelligence System — Production Documentation v1.0*
