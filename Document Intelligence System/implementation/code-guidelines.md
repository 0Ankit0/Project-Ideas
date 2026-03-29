# Code Guidelines - Document Intelligence System

## Python Project Structure

```
document-intelligence/
├── src/
│   ├── api/                   # FastAPI endpoints
│   │   ├── __init__.py
│   │   ├── documents.py
│   │   └── extractions.py
│   ├── ai/                    # AI/ML components
│   │   ├── __init__.py
│   │   ├── ocr.py
│   │   ├── classifier.py
│   │   ├── ner.py
│   │   └── key_value.py
│   ├── workers/               # Celery workers
│   │   ├── __init__.py
│   │   └── processor.py
│   ├── models/                # Data models
│   │   ├── __init__.py
│   │   └── entities.py
│   └── utils/
├── tests/
├── requirements.txt
└── README.md
```

## OCR Implementation

```python
from abc import ABC, abstractmethod
import pytesseract
from PIL import Image

class OCREngine(ABC):
    """Abstract base for OCR implementations"""
    
    @abstractmethod
    def extract_text(self, image_path: str) -> dict:
        pass

class TesseractOCR(OCREngine):
    """Open-source Tesseract OCR"""
    
    def __init__(self, language='eng'):
        self.language = language
        
    def extract_text(self, image_path: str) -> dict:
        image = Image.open(image_path)
        
        # Get OCR data with confidence
        ocr_data = pytesseract.image_to_data(
            image,
            lang=self.language,
            output_type=pytesseract.Output.DICT
        )
        
        # Extract text and calculate avg confidence
        text = pytesseract.image_to_string(image, lang=self.language)
        confidences = [c for c in ocr_data['conf'] if c != -1]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'text': text.strip(),
            'confidence': avg_confidence / 100,  # Normalize to 0-1
            'metadata': ocr_data
        }
```

## NER Pipeline

```python
import spacy
from typing import List, Dict

class NERPipeline:
    """Named Entity Recognition using spaCy"""
    
    def __init__(self, model_name='en_core_web_sm'):
        self.nlp = spacy.load(model_name)
        
    def extract_entities(self, text: str, doc_type: str = None) -> List[Dict]:
        doc = self.nlp(text)
        
        entities = []
        for ent in doc.ents:
            entities.append({
                'type': ent.label_,
                'value': ent.text,
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': self._calculate_confidence(ent)
            })
            
        # Apply domain-specific post-processing
        if doc_type:
            entities = self._postprocess(entities, doc_type)
            
        return entities
        
    def _calculate_confidence(self, entity) -> float:
        # Simple heuristic: longer entities are more confident
        return min(1.0, 0.7 + len(entity.text.split()) * 0.1)
        
    def _postprocess(self, entities: List[Dict], doc_type: str) -> List[Dict]:
        # Domain-specific entity filtering/normalization
        if doc_type == 'invoice':
            # Keep only invoice-relevant entities
            relevant_types = ['PERSON', 'ORG', 'MONEY', 'DATE']
            entities = [e for e in entities if e['type'] in relevant_types]
            
        return entities
```

## Document Classifier

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import joblib

class DocumentClassifier:
    """ML-based document classification"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.model = RandomForestClassifier(n_estimators=100)
        
    def train(self, texts: List[str], labels: List[str]):
        X = self.vectorizer.fit_transform(texts)
        self.model.fit(X, labels)
        
    def classify(self, text: str) -> tuple:
        X = self.vectorizer.transform([text])
        
        # Get prediction and confidence
        prediction = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        confidence = max(probabilities)
        
        return prediction, confidence
        
    def save(self, path: str):
        joblib.dump({
            'vectorizer': self.vectorizer,
            'model': self.model
        }, path)
        
    def load(self, path: str):
        data = joblib.load(path)
        self.vectorizer = data['vectorizer']
        self.model = data['model']
```

## FastAPI Endpoint

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI()

class ExtractionResult(BaseModel):
    documentId: str
    documentType: str
    entities: list
    keyValues: list
    avgConfidence: float

@app.post("/documents", status_code=202)
async def upload_document(file: UploadFile = File(...)):
    # Validate file type
    if not file.filename.endswith(('.pdf', '.jpg', '.png','.jpeg')):
        raise HTTPException(400, "Invalid file type")
        
    # Save to storage
    document_id = str(uuid.uuid4())
    file_path = await save_to_storage(file, document_id)
    
    # Queue for processing
    await queue_processing_job(document_id, file_path)
    
    return {
        "documentId": document_id,
        "status": "queued",
        "estimatedTime": "30 seconds"
    }

@app.get("/documents/{document_id}/extraction")
async def get_extraction(document_id: str):
    extraction = await get_from_database(document_id)
    
    if not extraction:
        raise HTTPException(404, "Document not found")
        
    return extraction
```

## Dependencies

```txt
# Core
fastapi>=0.95.0
uvicorn>=0.21.0
celery>=5.2.0
pydantic>=1.10.0

# AI/ML
pytesseract>=0.3.10
spacy>=3.5.0
scikit-learn>=1.2.0
tensorflow>=2.11.0  # optional

# Image Processing
Pillow>=9.4.0
opencv-python>=4.7.0
pdf2image>=1.16.3

# Database
psycopg2-binary>=2.9.5
sqlalchemy>=2.0.0

# Storage
boto3>=1.26.0  # for S3
```
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

### Engineering Extensions
- Require deterministic inference wrappers, schema-validated prediction payloads, and explicit version tagging for every model/prompt/policy invocation.
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

### Engineering Guardrails
- All inference interfaces must be pure/deterministic for identical model snapshot and input payload.
- Do not merge feature code without typed schema changes for prediction and feedback records.
- Enforce backwards compatibility for message contracts over at least one minor release window.
- Every ML decision path must emit structured logs with correlation id and stage timestamp.

