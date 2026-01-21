# ERD / Database Schema - Document Intelligence System

```mermaid
erDiagram
    documents ||--o{ pages : contains
    documents ||--|| extractions : has
    extractions ||--o{ entities : contains
    extractions ||--o{ key_values : contains
    extractions ||--o{ tables : contains
    users ||--o{ documents : uploads
    users ||--o{ corrections : makes
    
    documents {
        uuid id PK
        uuid userId FK
        string filename
        string fileUrl
        string documentType
        string status
        timestamp uploadedAt
    }
    
    pages {
        uuid id PK
        uuid documentId FK
        int pageNumber
        string imageUrl
        text ocrText
        jsonb ocrMetadata
    }
    
    extractions {
        uuid id PK
        uuid documentId FK
        string documentType
        float avgConfidence
        string status
        timestamp extractedAt
    }
    
    entities {
        uuid id PK
        uuid extractionId FK
        string entityType
        string value
        float confidence
        jsonb boundingBox
    }
    
    key_values {
        uuid id PK
        uuid extractionId FK
        string key
        string value
        float confidence
        boolean manuallyVerified
    }
    
    tables {
        uuid id PK
        uuid extractionId FK
        jsonb headers
        jsonb rows
        int pageNumber
    }
    
    users {
        uuid id PK
        string email
        string name
        string role
    }
    
    corrections {
        uuid id PK
        uuid keyValueId FK
        uuid userId FK
        string oldValue
        string newValue
        timestamp correctedAt
    }
```

## Table Definitions

### documents
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    document_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'uploaded',
    uploaded_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_user_status (user_id, status),
    INDEX idx_type (document_type)
);
```

### extractions
```sql
CREATE TABLE extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    document_type VARCHAR(50),
    avg_confidence FLOAT,
    status VARCHAR(20) DEFAULT 'pending',
    extracted_at TIMESTAMP DEFAULT NOW()
);
```

### entities
```sql
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extraction_id UUID NOT NULL REFERENCES extractions(id),
    entity_type VARCHAR(50) NOT NULL,  -- 'person', 'date', 'amount', etc.
    value TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    bounding_box JSONB,  -- {x, y, width, height}
    INDEX idx_extraction (extraction_id),
    INDEX idx_type (entity_type)
);
```

### key_values
```sql
CREATE TABLE key_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extraction_id UUID NOT NULL REFERENCES extractions(id),
    key VARCHAR(100) NOT NULL,
    value TEXT,
    confidence FLOAT NOT NULL,
    manually_verified BOOLEAN DEFAULT FALSE,
    INDEX idx_extraction (extraction_id),
    INDEX idx_key (key)
);
```

## Enum Definitions

| Enum | Values |
|------|--------|
| document_status | uploaded, queued, processing, completed, failed, needs_review |
| extraction_status | pending, completed, reviewed, approved |
| entity_type | person, organization, date, amount, address, email, phone |
| user_role | processor, reviewer, admin, data_scientist |
