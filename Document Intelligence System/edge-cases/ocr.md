# Edge Cases - OCR

### 2.1. Low-Quality Scans
* **Scenario**: Scanned documents are blurry or skewed.
* **Impact**: OCR accuracy drops and extraction errors increase.
* **Solution**:
    * **Preprocessing**: Apply de-skew, denoise, and contrast enhancement.
    * **Routing**: Send low-confidence results to review.

### 2.2. Mixed Languages
* **Scenario**: A document contains multiple languages.
* **Impact**: OCR misreads characters and yields low confidence.
* **Solution**:
    * **Detection**: Auto-detect language per page or region.
    * **Processing**: Use multi-language OCR models when needed.

### 2.3. Rotated or Upside-Down Pages
* **Scenario**: Pages are rotated by 90/180 degrees.
* **Impact**: OCR output is garbled or empty.
* **Solution**:
    * **Orientation**: Detect and correct orientation before OCR.
    * **Validation**: Reject pages with unresolved orientation errors.

### 2.4. Handwritten Content
* **Scenario**: Forms include handwritten fields.
* **Impact**: OCR fails to recognize text.
* **Solution**:
    * **Fallback**: Route to handwriting-capable OCR or manual review.
    * **UI**: Highlight fields that need human confirmation.