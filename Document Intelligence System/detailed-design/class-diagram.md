# Class Diagram - Document Intelligence System

## Python AI Classes

```mermaid
classDiagram
    class DocumentProcessor {
        -OCREngine ocrEngine
        -Classifier classifier
        -NERPipeline nerPipeline
        -Validator validator
        +processDocument(documentId) ExtractionResult
        +getStatus(documentId) ProcessingStatus
    }
    
    class OCREngine {
        <<interface>>
        +extractText(imagePath) OCRResult
    }
    
    class TesseractOCR {
        -tesseractPath str
        -language str
        +extractText(imagePath) OCRResult
        +setLanguage(lang)
    }
    
    class CloudOCR {
        -apiKey str
        -service str
        +extractText(imagePath) OCRResult
        -callAPI(image) Response
    }
    
    class DocumentClassifier {
        -model Any
        -labelEncoder LabelEncoder
        +classify(text) str, float
        +train(texts, labels)
        +save(path)
        +load(path)
    }
    
    class NERPipeline {
        -spacyModel spacy.Language
        -customRules Dict
        +extractEntities(text, docType) List~Entity~
        +addCustomRule(pattern, label)
        -postProcess(entities) List~Entity~
    }
    
    class KeyValueExtractor {
        -patterns Dict
        -mlModel Optional
        +extractPairs(text, docType) List~KeyValue~
        +addPattern(docType, pattern)
    }
    
    class TableDetector {
        -cvModel Any
        +detectTables(imagePath) List~Table~
        +extractTableData(tableRegion) DataFrame
    }
    
    class Validator {
        -rules Dict
        +validate(extraction) ValidationResult
        +calculateConfidence(extraction) float
        +checkBusinessRules(data, docType) List~Error~
    }
    
    OCREngine <|-- TesseractOCR
    OCREngine <|-- CloudOCR
    DocumentProcessor --> OCREngine
    DocumentProcessor --> DocumentClassifier
    DocumentProcessor --> NERPipeline
    DocumentProcessor --> KeyValueExtractor
    DocumentProcessor --> TableDetector
    DocumentProcessor --> Validator
```

## Data Classes

```mermaid
classDiagram
    class Document {
        +str documentId
        +str filename
        +str fileUrl
        +str documentType
        +ProcessingStatus status
        +DateTime uploadedAt
    }
    
    class OCRResult {
        +str text
        +float confidence
        +List~BoundingBox~ boxes
        +Dict metadata
    }
    
    class Entity {
        +str entityType
        +str value
        +float confidence
        +BoundingBox location
        +int startChar
        +int endChar
    }
    
    class KeyValue {
        +str key
        +str value
        +float confidence
        +bool manuallyVerified
    }
    
    class Table {
        +List~str~ headers
        +List~List~str~~ rows
        +int pageNumber
        +BoundingBox location
    }
    
    class ExtractionResult {
        +str documentId
        +str documentType
        +List~Entity~ entities
        +List~KeyValue~ keyValues
        +List~Table~ tables
        +float avgConfidence
        +ValidationResult validation
    }
```

**Key Python Libraries**:
- Tesseract-OCR: Open-source OCR
- spaCy: Industrial-strength NLP
- Hugging Face Transformers: Pre-trained NER models
- OpenCV: Image processing
- pdfplumber: PDF text extraction
- pandas: Data manipulation
