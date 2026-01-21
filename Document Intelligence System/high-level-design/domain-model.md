# Domain Model - Document Intelligence System

```mermaid
erDiagram
    DOCUMENT ||--o{ PAGE : contains
    DOCUMENT ||--|| EXTRACTION : has
    DOCUMENT {
        uuid id PK
        string filename
        string documentType
        string status
        timestamp uploadedAt
    }
    
    PAGE {
        uuid id PK
        uuid documentId FK
        int pageNumber
        string imageUrl
        string ocrText
        json ocrMetadata
    }
    
    EXTRACTION ||--o{ ENTITY : contains
    EXTRACTION ||--o{ KEY_VALUE : contains
    EXTRACTION ||--o{ TABLE : contains
    EXTRACTION {
        uuid id PK
        uuid documentId FK
        float avgConfidence
        string status
        timestamp extractedAt
    }
    
    ENTITY {
        uuid id PK
        uuid extractionId FK
        string entityType
        string value
        float confidence
        json boundingBox
    }
    
    KEY_VALUE {
        uuid id PK
        uuid extractionId FK
        string key
        string value
        float confidence
        boolean manuallyVerified
    }
    
    TABLE {
        uuid id PK
        uuid extractionId FK
        json headers
        json rows
        int pageNumber
    }
    
    ML_MODEL ||--o{ EXTRACTION : generates
    ML_MODEL {
        uuid id PK
        string modelType
        string version
        json metrics
        timestamp trainedAt
    }
    
    CORRECTION ||--|| KEY_VALUE : corrects
    CORRECTION {
        uuid id PK
        uuid keyValueId FK
        string oldValue
        string newValue
        uuid reviewerId
        timestamp correctedAt
    }
```

**Key Entities**:
- **Document**: Uploaded file (PDF/image)
- **Page**: Individual page with OCR text
- **Extraction**: Complete extraction result
- **Entity**: Named entity (name, date, amount)
- **Key-Value**: Field-value pair
- **Table**: Tabular data
- **ML Model**: OCR/NER/Classification model
- **Correction**: Human review correction
