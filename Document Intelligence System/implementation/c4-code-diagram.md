# C4 Code Diagram

```mermaid
flowchart TB
  DocumentController --> DocumentAppService --> DocumentAggregate
  OCRService --> OCRAdapter
  ExtractionService --> NLPAdapter
  DocumentAppService --> ExtractionService
  DocumentAppService --> DocumentRepository
```
