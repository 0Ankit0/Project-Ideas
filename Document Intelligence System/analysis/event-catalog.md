# Event Catalog - Document Intelligence System

| Event | Producer | Consumers | Description |
|-------|----------|-----------|-------------|
| document.uploaded | API/UI | Processing Queue | Document accepted and stored |
| ocr.completed | OCR Service | Classification Service | OCR result available |
| document.classified | Classifier | Extraction Pipeline | Document type identified |
| entities.extracted | NER Service | Validation Service | Entities extracted |
| keyvalues.extracted | KV Service | Validation Service | Key-value pairs extracted |
| tables.extracted | Table Service | Validation Service | Table extraction complete |
| validation.failed | Validation Service | Review Queue | Low-confidence or rule failures |
| review.completed | Review UI | Export Service | Manual corrections completed |
| export.completed | Export Service | Notification | Export file ready |