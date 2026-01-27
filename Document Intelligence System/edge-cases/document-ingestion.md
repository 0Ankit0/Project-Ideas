# Edge Cases - Document Ingestion

### 1.1. Corrupted File Upload
* **Scenario**: A user uploads a corrupted or partial PDF/image.
* **Impact**: OCR fails or produces empty output.
* **Solution**:
    * **Validation**: Verify file integrity and attempt basic parsing.
    * **UI**: Show a clear error and request re-upload.

### 1.2. Unsupported File Type
* **Scenario**: A file type outside the allowed list is uploaded.
* **Impact**: Processing fails and user confusion increases.
* **Solution**:
    * **Validation**: Enforce MIME type and extension checks.
    * **UI**: Display supported formats explicitly.

### 1.3. Oversized Batch Upload
* **Scenario**: A batch exceeds size or count limits.
* **Impact**: Queue overload and slow processing.
* **Solution**:
    * **Limits**: Enforce file count and size caps.
    * **UX**: Provide partial acceptance with a failure report.

### 1.4. Duplicate Document
* **Scenario**: The same document is uploaded multiple times.
* **Impact**: Redundant processing and duplicate records.
* **Solution**:
    * **Detection**: Hash documents to detect duplicates.
    * **Policy**: Mark duplicates and optionally skip processing.

### 1.5. Storage Outage
* **Scenario**: Object storage becomes temporarily unavailable.
* **Impact**: Uploads fail and documents are lost.
* **Solution**:
    * **Retry**: Use resumable uploads and exponential backoff.
    * **Fallback**: Queue uploads locally until storage is restored.