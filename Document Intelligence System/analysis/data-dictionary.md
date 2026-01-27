# Data Dictionary - Document Intelligence System

## Core Entities

### Document
- **id**: UUID
- **source**: upload | api | batch
- **filename**: string
- **mimeType**: string
- **pageCount**: int
- **status**: uploaded | processing | review | completed | failed
- **createdAt**: ISO 8601

### OCRResult
- **id**: UUID
- **documentId**: UUID
- **text**: string
- **layout**: json
- **confidence**: float (0–1)

### Classification
- **id**: UUID
- **documentId**: UUID
- **documentType**: string
- **confidence**: float (0–1)

### Entity
- **id**: UUID
- **documentId**: UUID
- **type**: string (e.g., vendor, date, amount)
- **value**: string
- **confidence**: float (0–1)

### KeyValue
- **id**: UUID
- **documentId**: UUID
- **field**: string
- **value**: string
- **confidence**: float (0–1)
- **normalizedValue**: string (optional)

### Table
- **id**: UUID
- **documentId**: UUID
- **rows**: array
- **headers**: array
- **confidence**: float (0–1)

### ReviewTask
- **id**: UUID
- **documentId**: UUID
- **assignedTo**: string
- **status**: open | in_progress | completed
- **createdAt**: ISO 8601

### ReviewEdit
- **id**: UUID
- **documentId**: UUID
- **field**: string
- **oldValue**: string
- **newValue**: string
- **editedBy**: string
- **editedAt**: ISO 8601

### ExportJob
- **id**: UUID
- **documentIds**: array
- **format**: json | csv | xml
- **status**: queued | running | completed | failed
- **createdAt**: ISO 8601