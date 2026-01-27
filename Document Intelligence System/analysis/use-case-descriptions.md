# Use Case Descriptions - Document Intelligence System

## UC-01: Upload Document
**Primary Actor**: Document Processor  
**Description**: Upload document for automated processing

**Preconditions**:
- User is authenticated
- File type and size limits are known

**Main Flow**:
1. User selects file (PDF/image)
2. System validates file type and size
3. System uploads to storage
4. System generates document ID
5. System queues for processing
6. User receives confirmation with document ID

**Alternate Flows**:
- A1: Invalid file type → reject with supported types
- A2: File too large → reject with max size guidance

**Exceptions**:
- E1: Storage unavailable → retry and notify user

**Postconditions**:
- Document stored and queued

**Success Criteria**: Document uploaded and queued for processing

---

## UC-02: Process Document (System Internal)
**Trigger**: Document uploaded  
**Description**: AI pipeline processes document

**Preconditions**:
- Document exists in storage
- OCR and extraction services are available

**Main Flow**:
1. System retrieves document from queue
2. **OCR Engine** extracts text from images
3. **Document Classifier** identifies document type
4. **NER Pipeline** extracts entities
5. **Key-Value Extractor** maps fields to schema
6. **Validator** checks accuracy, assigns confidence scores
7. System saves extracted data
8. System notifies user of completion

**Alternate Flows**:
- A1: OCR confidence low → route to review
- A2: Ambiguous document type → request human selection

**Exceptions**:
- E1: OCR fails → mark as failed and notify
- E2: Downstream service unavailable → retry with backoff

**Postconditions**:
- Structured data stored with confidence scores

**Success Criteria**: Data extracted with confidence scores

---

## UC-03: Review & Correct Extractions
**Primary Actor**: Reviewer  
**Description**: Validate and fix extraction errors

**Preconditions**:
- Review task exists
- Reviewer has appropriate permissions

**Main Flow**:
1. Reviewer opens document in review UI
2. System displays side-by-side: document image + extracted fields
3. System highlights low-confidence fields
4. Reviewer edits incorrect values
5. System marks fields as manually corrected
6. Reviewer approves document
7. System updates extraction data

**Alternate Flows**:
- A1: Reviewer rejects document → send back to processing

**Exceptions**:
- E1: Document not found → show error and requeue

**Postconditions**:
- Corrections stored and audit logged

**Success Criteria**: Corrections saved, document approved

---

## UC-04: Train Custom NER Model
**Primary Actor**: Data Scientist  
**Description**: Improve entity extraction accuracy

**Preconditions**:
- Labeled data available
- Training environment accessible

**Main Flow**:
1. Data Scientist prepares labeled training data
2. Selects NER architecture (spaCy, Transformers)
3. Configures hyperparameters
4. System trains model on labeled data
5. System evaluates on test set
6. Data Scientist reviews metrics (precision, recall, F1)
7. Deploys model to production

**Alternate Flows**:
- A1: Metrics below threshold → reject model

**Exceptions**:
- E1: Training failure → capture logs and notify

**Postconditions**:
- Model registered and versioned

**Success Criteria**: New model deployed with improved accuracy

---

## UC-05: Configure Document Types
**Primary Actor**: System Admin  
**Description**: Define schemas and required fields per document type

**Preconditions**:
- Admin permissions available

**Main Flow**:
1. Admin creates document type
2. Defines required fields and validation rules
3. Saves schema and activates type

**Postconditions**:
- New document type is available in processing pipeline

**Success Criteria**: New type becomes selectable and valid

---

## UC-06: Export Extracted Data
**Primary Actor**: Analyst  
**Description**: Export structured data for downstream systems

**Preconditions**:
- Documents processed successfully

**Main Flow**:
1. Analyst selects documents and format
2. System creates export job
3. Export completes and link is provided

**Postconditions**:
- Export file stored and audit logged

**Success Criteria**: Data exported in requested format
