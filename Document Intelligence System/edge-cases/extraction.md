# Edge Cases - Extraction (NER/KV/Tables)

### 4.1. Overlapping Entities
* **Scenario**: Entities overlap (e.g., date within address string).
* **Impact**: Entity boundaries are wrong and fields are mis-mapped.
* **Solution**:
    * **Rules**: Apply entity precedence and boundary constraints.
    * **Review**: Highlight overlaps for manual correction.

### 4.2. Missing Required Fields
* **Scenario**: Mandatory fields are not found.
* **Impact**: Incomplete output and downstream failures.
* **Solution**:
    * **Validation**: Flag missing fields and route to review.
    * **UI**: Prompt reviewers to fill required fields.

### 4.3. Table Split Across Pages
* **Scenario**: Tables span multiple pages.
* **Impact**: Rows are duplicated or misaligned.
* **Solution**:
    * **Detection**: Track headers and continue table across pages.
    * **Normalization**: Merge rows using column alignment rules.

### 4.4. Non-Standard Layouts
* **Scenario**: Fields appear in unusual positions.
* **Impact**: Key-value extraction fails.
* **Solution**:
    * **Modeling**: Use layout-aware models and spatial features.
    * **Fallback**: Trigger manual review when layout confidence is low.

### 4.5. Currency and Date Ambiguity
* **Scenario**: Ambiguous formats like 01/02/2026 or $ vs €.
* **Impact**: Incorrect normalization and reporting.
* **Solution**:
    * **Locale**: Use document metadata or tenant locale to parse.
    * **Validation**: Flag ambiguous values for confirmation.