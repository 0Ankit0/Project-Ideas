# Use Case Descriptions - Document Intelligence System

## UC-01: Upload Document
**Actor**: Document Processor  
**Description**: Upload document for automated processing

**Main Flow**:
1. User selects file (PDF/image)
2. System validates file type and size
3. System uploads to storage
4. System generates document ID
5. System queues for processing
6. User receives confirmation with document ID

**Success**: Document uploaded and queued for processing

---

## UC-02: Process Document (System Internal)
**Trigger**: Document uploaded  
**Description**: AI pipeline processes document

**Main Flow**:
1. System retrieves document from queue
2. **OCR Engine** extracts text from images
3. **Document Classifier** identifies document type
4. **NER Pipeline** extracts entities
5. **Key-Value Extractor** maps fields to schema
6. **Validator** checks accuracy, assigns confidence scores
7. System saves extracted data
8. System notifies user of completion

**Success**: Data extracted with confidence scores

---

## UC-03: Review & Correct Extractions
**Actor**: Reviewer  
**Description**: Validate and fix extraction errors

**Main Flow**:
1. Reviewer opens document in review UI
2. System displays side-by-side: document image + extracted fields
3. System highlights low-confidence fields
4. Reviewer edits incorrect values
5. System marks fields as manually corrected
6. Reviewer approves document
7. System updates extraction data

**Success**: Corrections saved, document approved

---

## UC-04: Train Custom NER Model
**Actor**: Data Scientist  
**Description**: Improve entity extraction accuracy

**Main Flow**:
1. Data Scientist prepares labeled training data
2. Data Scientist selects NER architecture (spaCy, Transformers)
3. Data Scientist configures hyperparameters
4. System trains model on labeled data
5. System evaluates on test set
6. Data Scientist reviews metrics (precision, recall, F1)
7. Data Scientist deploys model to production

**Success**: New model deployed with improved accuracy
