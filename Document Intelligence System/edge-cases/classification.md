# Edge Cases - Classification

### 3.1. Ambiguous Document Type
* **Scenario**: A document matches multiple templates.
* **Impact**: Incorrect schema selection and bad extraction.
* **Solution**:
    * **Thresholds**: Require a minimum confidence gap between top classes.
    * **Review**: Route to manual document type selection.

### 3.2. New Document Templates
* **Scenario**: A new template is introduced without training data.
* **Impact**: Misclassification and extraction errors.
* **Solution**:
    * **Fallback**: Use a generic template and flag for review.
    * **Data**: Capture samples for incremental training.

### 3.3. Multi-Document Files
* **Scenario**: A single PDF contains multiple document types.
* **Impact**: Classifier outputs a single label for mixed content.
* **Solution**:
    * **Segmentation**: Detect section boundaries and classify per segment.
    * **UI**: Allow manual split and reclassify.