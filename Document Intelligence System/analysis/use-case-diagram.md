# Use Case Diagram - Document Intelligence System

```mermaid
graph TB
    subgraph Actors
        USER((Document<br/>Processor))
        REVIEWER((Reviewer))
        ADMIN((System Admin))
        DS((Data Scientist))
        API((API Consumer))
    end
    
    subgraph "Document Intelligence System"
        UC1[Upload Document]
        UC2[View Extracted Data]
        UC3[Correct Errors]
        UC4[Export Data]
        UC5[Configure Rules]
        UC6[Train Models]
        UC7[API Upload]
        UC8[API Retrieve]
    end
    
    USER --> UC1
    USER --> UC2
    REVIEWER --> UC3
    USER --> UC4
    ADMIN --> UC5
    DS --> UC6
    API --> UC7
    API --> UC8
```

## Actor Summary

| Actor | Primary Actions |
|-------|----------------|
| Document Processor | Upload documents, view extracted data |
| Reviewer | Validate and correct extractions |
| System Admin | Configure extraction rules |
| Data Scientist | Train and optimize AI models |
| API Consumer | Programmatic document processing |
