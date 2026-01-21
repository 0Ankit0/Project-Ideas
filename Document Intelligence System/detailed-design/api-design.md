# API Design - Document Intelligence System

**Base URL**: `https://api.example.com/v1`  
**Auth**: Bearer Token

---

## Upload Document
**POST** `/documents`

**Request** (multipart/form-data):
```
file: [PDF/Image file]
documentType: "invoice" (optional)
```

**Response**: `202 Accepted`
```json
{
  "documentId": "uuid",
  "status": "queued",
  "estimatedTime": "30 seconds"
}
```

---

## Get Document Status
**GET** `/documents/{documentId}/status`

**Response**: `200 OK`
```json
{
  "documentId": "uuid",
  "status": "completed",
  "progress": 100,
  "extractionId": "uuid"
}
```

---

## Get Extracted Data
**GET** `/documents/{documentId}/extraction`

**Response**: `200 OK`
```json
{
  "documentId": "uuid",
  "documentType": "invoice",
  "avgConfidence": 0.92,
  "entities": [
    {"type": "vendor", "value": "ABC Corp", "confidence": 0.95},
    {"type": "amount", "value": "1250.00", "confidence": 0.98}
  ],
  "keyValues": [
    {"key": "invoice_number", "value": "INV-001", "confidence": 0.99},
    {"key": "total", "value": "1250.00", "confidence": 0.98}
  ],
  "tables": [
    {"headers": ["Item", "Qty", "Price"], "rows": [["Widget", "5", "250"]]}
  ]
}
```

---

## Update Extraction (Correction)
**PATCH** `/documents/{documentId}/extraction`

**Request**:
```json
{
  "keyValues": [
    {"key": "invoice_number", "value": "INV-002", "manuallyVerified": true}
  ]
}
```

**Response**: `200 OK`

---

## Batch Upload
**POST** `/documents/batch`

**Request**:
```json
{
  "documents": [
    {"fileUrl": "s3://...", "documentType": "invoice"},
    {"fileUrl": "s3://...", "documentType": "receipt"}
  ]
}
```

**Response**: `202 Accepted`
```json
{
  "batchId": "uuid",
  "documentIds": ["uuid1", "uuid2"],
  "status": "queued"
}
```

---

## Export Data
**GET** `/documents/{documentId}/export`

**Query Params**:
- `format`: json | csv | xml

**Response**: Extracted data in requested format

---

## Webhook Configuration
**POST** `/webhooks`

**Request**:
```json
{
  "url": "https://your-app.com/webhook",
  "events": ["document.completed", "document.failed"]
}
```

---

## Error Responses

```json
{
  "error": {
    "code": "INVALID_FILE_TYPE",
    "message": "Only PDF and image files are supported"
  }
}
```

| Code | HTTP | Description |
|------|------|-------------|
| INVALID_FILE_TYPE | 400 | Unsupported file format |
| FILE_TOO_LARGE | 413 | File exceeds 10MB limit |
| DOCUMENT_NOT_FOUND | 404 | Document ID doesn't exist |
| PROCESSING_FAILED | 500 | AI processing error |
| LOW_CONFIDENCE | 422 | Extraction confidence too low |
