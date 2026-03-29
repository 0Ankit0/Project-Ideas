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

## Purpose and Scope
Describes edge behavior consistency between analyst UI and backend APIs under unusual or degraded conditions.

## Assumptions and Constraints
- UI state machine mirrors backend case state transitions.
- Client retries are idempotent and visible in audit logs.
- Error messages are actionable but non-sensitive.

### End-to-End Example with Realistic Data
Analyst clicks “Escalate” on `CASE-192`; UI sends `POST /cases/CASE-192/escalations`, receives 202, and timeline updates to `Escalated` with SLA countdown. If backend is degraded, UI displays explicit degraded badge and retry affordance.

## Decision Rationale and Alternatives Considered
- Aligned UI transitions with backend events to avoid phantom states.
- Rejected optimistic UI updates without server confirmation for critical actions.
- Kept consistent error code mapping across web and API clients.

## Failure Modes and Recovery Behaviors
- UI stale cache shows closed case as open -> forced refresh on conflicting ETag.
- API timeout after user action -> client polls operation status endpoint before duplicate submit.

## Security and Compliance Implications
- UI hides sensitive evidence unless role and reason are validated server-side.
- Frontend telemetry excludes raw identifiers and secrets.

## Operational Runbooks and Observability Notes
- Frontend error budget and backend API SLO are monitored together.
- Runbook includes browser-session repro steps and API trace correlation.
