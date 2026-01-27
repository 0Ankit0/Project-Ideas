# Edge Cases - Validation & Review

### 5.1. Conflicting Validation Rules
* **Scenario**: Two validation rules contradict each other.
* **Impact**: Documents are blocked unnecessarily.
* **Solution**:
    * **Governance**: Rule precedence and versioning.
    * **Testing**: Pre-deploy rule validation tests.

### 5.2. Review Queue Backlog
* **Scenario**: Review tasks accumulate faster than reviewers can process.
* **Impact**: SLA breaches and delayed exports.
* **Solution**:
    * **Prioritization**: Route high-priority docs first.
    * **Capacity**: Add reviewers or temporarily lower thresholds.

### 5.3. Reviewer Edits Not Saved
* **Scenario**: Network or session issues drop edits.
* **Impact**: Lost work and user frustration.
* **Solution**:
    * **Autosave**: Draft saving and retry on failure.
    * **Audit**: Show last saved timestamp.

### 5.4. Incomplete Review Decisions
* **Scenario**: Reviewer approves with missing required fields.
* **Impact**: Invalid exports.
* **Solution**:
    * **Validation**: Block approval unless required fields are complete.
    * **UI**: Highlight missing fields with actionable prompts.