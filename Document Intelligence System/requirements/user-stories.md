# User Stories - Document Intelligence System

> **Domain Independence**: Stories use generic terms adaptable to invoices, resumes, medical records, contracts, etc.

---

## User Personas

| Persona | Description | Goals |
|---------|-------------|-------|
| **Document Processor** | Person who uploads & processes documents | Automate manual data entry |
| **Reviewer** | Person who validates extractions | Ensure accuracy before export |
| **System Admin** | Configure extraction rules | Optimize system performance |
| **Data Scientist** | Train and improve AI models | Increase extraction accuracy |
| **API Consumer** | Developer integrating the system | Access extracted data programmatically |

---

## Epic 1: Document Upload & Processing

### US-1.1: Upload Document
**As a** document processor  
**I want to** upload documents via web interface  
**So that** the system can extract data automatically

**Acceptance Criteria:**
- [ ] Support PDF, JPEG, PNG, TIFF formats
- [ ] Drag-and-drop upload support
- [ ] Batch upload up to 100 documents
- [ ] Show upload progress
- [ ] Validate file size (< 10MB)

---

### US-1.2: Track Processing Status
**As a** document processor  
**I want to** see real-time processing status  
**So that** I know when data is ready

**Acceptance Criteria:**
- [ ] Status shows: Uploaded → OCR → Classification → Extraction → Complete
- [ ] Progress percentage displayed
- [ ] Estimated time remaining
- [ ] Error notifications with details

---

## Epic 2: Data Extraction & Review

### US-2.1: View Extracted Data
**As a** reviewer  
**I want to** see side-by-side document and extracted data  
**So that** I can verify accuracy

**Acceptance Criteria:**
- [ ] Split view: document image + extracted fields
- [ ] Highlight extracted text on document
- [ ] Show confidence scores per field
- [ ] Color-code by confidence (green > 90%, yellow 70-90%, red < 70%)

---

### US-2.2: Correct Extraction Errors
**As a** reviewer  
**I want to** edit incorrect extractions  
**So that** the data is accurate

**Acceptance Criteria:**
- [ ] Click to edit any field
- [ ] Indicate manual correction vs. auto-extract
- [ ] Save corrections
- [ ] System learns from corrections (optional)

---

### US-2.3: Flag for Manual Review
**As a** document processor  
**I want** low-confidence extractions flagged automatically  
**So that** I focus review efforts efficiently

**Acceptance Criteria:**
- [ ] Auto-flag documents with avg confidence < 80%
- [ ] Flag specific fields with confidence < 70%
- [ ] Filter view to show only flagged items

---

## Epic 3: Document Classification

### US-3.1: Automatic Document Classification
**As a** document processor  
**I want** documents classified automatically  
**So that** correct extraction rules are applied

**Acceptance Criteria:**
- [ ] System identifies document type (invoice, resume, etc.)
- [ ] Classification confidence score shown
- [ ] Allow manual override if misclassified
- [ ] Support for custom document types

**Domain Examples:**
- Invoice: Classify as "Purchase Invoice" vs. "Sales Invoice"
- Resume: Classify by job category (IT, Sales, etc.)
- Medical: Classify as "Lab Report", "Prescription", "Diagnosis"

---

## Epic 4: Entity Extraction

### US-4.1: Extract Key Entities
**As a** document processor  
**I want** important entities extracted automatically  
**So that** I don't manually type them

**Acceptance Criteria:**
- [ ] Extract names, dates, amounts, addresses
- [ ] Normalize formats (dates to ISO, amounts to decimal)
- [ ] Link related entities
- [ ] Show entity type and confidence

**Domain-Specific Entities:**
- Invoice: Vendor name, Invoice #, Total amount, Tax
- Resume: Candidate name, Skills, Education, Experience years
- Medical: Patient name, Diagnosis codes, Medications, Dosages
- Contract: Parties, Terms, Effective date, Obligations

---

## Epic 5: Configuration & Model Training

### US-5.1: Configure Extraction Rules
**As a** system admin  
**I want to** define custom extraction fields  
**So that** the system extracts domain-specific data

**Acceptance Criteria:**
- [ ] Add custom field definitions
- [ ] Set validation rules per field
- [ ] Define required vs. optional fields
- [ ] Test rules on sample documents

---

### US-5.2: Train Custom Models
**As a** data scientist  
**I want to** train models on labeled data  
**So that** extraction accuracy improves

**Acceptance Criteria:**
- [ ] Upload training dataset
- [ ] Label entities and fields
- [ ] Train NER and classification models
- [ ] Evaluate model performance
- [ ] Deploy new model version

---

## Epic 6: API & Integration

### US-6.1: API Document Upload
**As an** API consumer  
**I want to** upload documents via REST API  
**So that** I can automate processing from my system

**Acceptance Criteria:**
- [ ] POST endpoint accepts file upload
- [ ] Returns document ID
- [ ] Supports async processing
- [ ] Webhook notification on completion

---

### US-6.2: Retrieve Extracted Data
**As an** API consumer  
**I want to** fetch extracted data in JSON format  
**So that** I can integrate with my application

**Acceptance Criteria:**
- [ ] GET endpoint returns structured data
- [ ] Include confidence scores
- [ ] Support filtering by field
- [ ] Export as JSON, CSV, or XML

---

## Story Map

```
┌──────────────────────────────────────────────────────────────┐
│                    DOCUMENT JOURNEY                           │
├────────────┬────────────┬────────────┬────────────────────────┤
│   UPLOAD   │  EXTRACT   │   REVIEW   │      INTEGRATE         │
├────────────┼────────────┼────────────┼────────────────────────┤
│ US-1.1     │ US-2.1     │ US-2.2     │ US-6.1                 │
│ Upload Doc │ View Data  │ Correct    │ API Upload             │
├────────────┼────────────┼────────────┼────────────────────────┤
│ US-1.2     │ US-3.1     │ US-2.3     │ US-6.2                 │
│ Track      │ Classify   │ Flag Low   │ Get Data               │
│ Status     │            │ Confidence │                        │
├────────────┼────────────┼────────────┼────────────────────────┤
│            │ US-4.1     │ US-5.1     │                        │
│            │ Extract    │ Config     │                        │
│            │ Entities   │ Rules      │                        │
└────────────┴────────────┴────────────┴────────────────────────┘
```

---

## Priority Matrix (MoSCoW)

| Must Have | Should Have | Could Have |
|-----------|-------------|------------|
| US-1.1, 1.2 | US-2.3 | US-5.2 |
| US-2.1, 2.2 | US-3.1 | |
| US-4.1 | US-5.1 | |
| US-6.1, 6.2 | | |
