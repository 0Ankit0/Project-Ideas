# Edge Cases - API & UI

### 6.1. Pagination Inconsistency
* **Scenario**: Items are missing or repeated across pages.
* **Impact**: Users see inconsistent results and cannot reconcile totals.
* **Solution**:
	* **Pagination**: Use cursor-based pagination with stable ordering.
	* **Consistency**: Return `nextCursor` only when more data exists.

### 6.2. Expired Tokens
* **Scenario**: A user’s token expires mid-action.
* **Impact**: Failed actions and poor user experience.
* **Solution**:
	* **Auth**: Support refresh tokens and graceful re-auth.
	* **UI**: Display clear prompts when sessions expire.

### 6.3. Long-Running Queries
* **Scenario**: Users request large time ranges.
* **Impact**: API timeouts and UI freezes.
* **Solution**:
	* **Async**: Provide export jobs with status polling.
	* **Limits**: Enforce max range per request.

### 6.4. Concurrent Updates
* **Scenario**: Multiple admins edit the same rule.
* **Impact**: Overwrites and lost changes.
* **Solution**:
	* **Locking**: Use optimistic concurrency with version checks.
	* **UI**: Show conflict resolution prompts.

### 6.5. Timezone Mismatch in UI
* **Scenario**: Charts display incorrect time offsets.
* **Impact**: Operators misinterpret incident timing.
* **Solution**:
	* **Display**: Show user-local time with UTC toggle.
	* **Consistency**: Store all timestamps in UTC.