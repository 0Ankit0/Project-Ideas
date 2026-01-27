# Edge Cases - API & UI

### 6.1. Large Export Requests
* **Scenario**: User exports thousands of documents at once.
* **Impact**: API timeouts and UI freezes.
* **Solution**:
    * **Async**: Use export jobs with status polling.
    * **Limits**: Enforce max export size per request.

### 6.2. Pagination Drift
* **Scenario**: Results change during pagination.
* **Impact**: Users see duplicates or missing items.
* **Solution**:
    * **Pagination**: Use cursor-based pagination with stable sorting.
    * **Consistency**: Snapshot query time for large exports.

### 6.3. Token Expiration Mid-Review
* **Scenario**: Session expires while a reviewer is editing.
* **Impact**: Edits lost or actions fail.
* **Solution**:
    * **Auth**: Refresh token flow and autosave drafts.
    * **UI**: Prompt for re-authentication without losing work.