# Edge Cases – Policy Issuance and Underwriting

This document covers edge cases in the policy origination lifecycle, from application submission through underwriting decision and policy number assignment. These cases involve rule engine conflicts, timing anomalies, reinsurance constraints, and data integrity risks that must be handled correctly to ensure valid, legally binding policies are issued.

---

### EC-PIU-001: Incomplete Application Data Submission

**Severity:** P2

**Description:**
An applicant or broker begins filling out a multi-step application form and submits or navigates away before all required fields are completed. The system may receive a partial payload — for example, personal details and vehicle information present, but no coverage selection or beneficiary designation. In some integration patterns, a broker portal may POST the first half of the application before the user completes step two.

**Trigger Condition:**
- User closes browser mid-flow after step 2 of a 5-step application wizard.
- Broker API integration sends application in multiple API calls and the final call fails or is not sent.
- Network interruption during form submission results in only part of the JSON payload reaching the server.

**Expected System Behavior:**
The system must save the partial application in a `DRAFT` state, not in a `SUBMITTED` or `PENDING_UNDERWRITING` state. A draft must not be forwarded to the underwriting rule engine. The applicant or broker must receive a clear response enumerating the missing required fields. A session-linked draft recovery mechanism must allow resumption from the last completed step. Draft applications not completed within 30 days must be archived and the applicant notified.

**Failure Mode if Not Handled:**
- Underwriting engine receives incomplete data and either crashes, throws a null-pointer exception, or silently produces an incorrect risk score based on missing values defaulting to zero.
- A policy is incorrectly issued without mandatory coverage terms, creating an invalid contract that cannot be enforced.
- Duplicate draft records accumulate in the database if the user retries submission, leading to orphaned applications and confused application status.

**Mitigation/Implementation Notes:**
- Implement server-side validation at each step boundary with a well-defined required-fields schema per product type.
- Use a `PolicyApplicationStatus` enum: `DRAFT`, `SUBMITTED`, `PENDING_UNDERWRITING`, `REFERRED`, `ACCEPTED`, `DECLINED`, `BOUND`.
- Store draft application state in a dedicated `draft_applications` table with a TTL index.
- Return HTTP 422 Unprocessable Entity with a structured field-level error response on incomplete submission.
- Emit a `ApplicationDraftSaved` domain event so downstream services (e.g., CRM, email) can trigger nudge campaigns without polling.

---

### EC-PIU-002: Conflicting Underwriting Rules

**Severity:** P1

**Description:**
The underwriting rule engine evaluates applicants against a set of product-specific risk rules. On occasion, two or more rules with overlapping conditions produce contradictory outcomes for the same applicant — one rule mandates `ACCEPT` (e.g., long customer tenure bonus) while another mandates `DECLINE` (e.g., three or more at-fault accidents in 24 months). Without explicit conflict resolution logic, the outcome is non-deterministic and potentially incorrect.

**Trigger Condition:**
- A product manager adds a new "loyalty discount" rule without reviewing interactions with existing exclusion rules.
- A batch rule update is deployed during business hours, and some in-flight applications are evaluated against an inconsistent rule set spanning the old and new versions.
- An applicant sits in a demographic segment that is covered by rules from two different underwriting product lines simultaneously (e.g., life + critical illness bundled product).

**Expected System Behavior:**
The rule engine must apply an explicit conflict resolution strategy — typically "most restrictive wins" for risk decisions. Where two binding decisions conflict, the system must escalate the application to a human underwriter review queue with a `REFERRED` status, attaching the conflicting rule IDs and their individual outputs. The conflict must be logged and reported to the rules management team. The applicant must receive an acknowledgement that their application is under review, not a final decision.

**Failure Mode if Not Handled:**
- A high-risk applicant is incorrectly issued a policy because an `ACCEPT` rule overrides a `DECLINE` rule without escalation.
- Non-deterministic rule ordering causes the same applicant data to produce different decisions on repeated submissions, undermining audit trail integrity.
- A regulatory audit finds that underwriting decisions cannot be explained or traced, resulting in compliance findings.

**Mitigation/Implementation Notes:**
- Assign an explicit priority score (1–100) to every underwriting rule. Lower priority rules cannot override higher priority rules.
- Implement a `RuleConflictDetector` that runs post-evaluation and logs all cases where two or more rules produce outcomes of different decision types on the same application.
- Version underwriting rule sets with semantic versioning. Pin each application evaluation to the rule set version active at the time of submission.
- Provide a rule conflict report in the underwriter dashboard, updated daily.
- Write unit tests for all known conflicting rule pairs as part of the rule engine CI pipeline.

---

### EC-PIU-003: Simultaneous Duplicate Applications

**Severity:** P1

**Description:**
An applicant or broker submits two identical applications within a very short window — typically a few seconds — often caused by double-clicking a submit button, a broker integration retrying a failed HTTP request, or a front-end bug that fires the submission event twice. Both requests may be processed concurrently by different API instances, resulting in two separate applications entering the underwriting pipeline for the same risk.

**Trigger Condition:**
- Front-end submit button not disabled after first click; user double-clicks.
- Broker REST integration retries a POST `/applications` request because of a transient HTTP 500, but the first request had already succeeded.
- Load balancer routes the two identical requests to different API server instances with no shared locking.

**Expected System Behavior:**
The system must detect and reject or deduplicate the second submission within the same idempotency window (recommended: 60 seconds). The API must support an `Idempotency-Key` header. If the second request carries the same idempotency key, the system must return the response from the first request without creating a new record. If no idempotency key is present, the system must check for an existing `DRAFT` or `SUBMITTED` application for the same applicant, same product, and same inception date and return a conflict response (HTTP 409).

**Failure Mode if Not Handled:**
- Two policies are issued for the same risk, doubling the insurer's liability exposure without corresponding premium income.
- Two underwriting decisions are made, potentially with different outcomes, creating a disputed contract.
- Reinsurance placement is made twice for the same risk, causing reinsurer invoice discrepancies.

**Mitigation/Implementation Notes:**
- Implement idempotency key support at the API gateway level, backed by a Redis cache with a 60-second TTL.
- Add a unique constraint on `(applicant_id, product_id, proposed_inception_date, submission_fingerprint)` in the `policy_applications` table.
- `submission_fingerprint` is a hash of the application payload canonical form, computed server-side.
- Return HTTP 409 Conflict with a `location` header pointing to the existing application resource if a duplicate is detected.
- Instrument and alert on duplicate application attempts — elevated rates may indicate broker integration bugs or malicious probing.

---

### EC-PIU-004: Backdated Policy Request

**Severity:** P2

**Description:**
A broker requests that a policy be issued with an effective (inception) date in the past — for example, requesting on 15 March that coverage begin on 1 March. This is sometimes legitimate (e.g., evidence of insurance for a vehicle already in use, retroactive fleet additions) but can also represent fraud or an attempt to submit a claim for a loss that occurred before the application.

**Trigger Condition:**
- Broker submits application via API with `inception_date` field set to a date 14 days prior to the submission date.
- Policy endorsement backdating requested after a loss event has occurred.
- System clock discrepancy between broker portal and underwriting system causes a technically backdated submission.

**Expected System Behavior:**
The system must enforce a maximum allowable backdate window, typically defined per product line (e.g., 0 days for personal lines, up to 30 days for commercial fleet with documented evidence). Applications with an inception date outside the allowed window must be rejected with a clear error. Applications within the window must be flagged for underwriter review, not auto-bound. The system must check whether any FNOL or claim has been registered for the applicant or related risk within the backdated coverage period; if so, the application must be escalated with a fraud flag.

**Failure Mode if Not Handled:**
- Coverage is backdated to before a known loss event, creating a fraudulent claim exposure.
- Reinsurance treaties are violated because backdated policies fall outside the treaty period.
- Premium calculations are incorrect because earned premium, return premium, and installment schedules are computed relative to the inception date.

**Mitigation/Implementation Notes:**
- Validate `inception_date` at the API layer: reject if `inception_date < (submission_date - max_backdate_days[product_type])`.
- Cross-reference the applicant identity and the insured risk against the FNOL and claims databases for the backdated period.
- Require documented justification (uploaded evidence) for any backdated request within the permitted window.
- Log all backdated requests in a dedicated audit table for anti-fraud review.
- Generate a mandatory underwriter task for all backdated applications; auto-bind must be disabled.

---

### EC-PIU-005: High-Risk Applicant on Boundary Score

**Severity:** P2

**Description:**
An applicant's computed risk score falls exactly on the accept/refer threshold defined in the underwriting rules — for instance, the threshold is 650 and the applicant scores exactly 650. Simultaneously, the threshold itself may be updated by an actuary during the business day as part of a rate revision, meaning that an application submitted at 09:00 and one submitted at 14:00 with identical data could receive different decisions.

**Trigger Condition:**
- Applicant risk score equals the configured threshold boundary value exactly.
- Underwriting threshold is updated via the admin console while applications are in-flight in the rule evaluation queue.
- Floating-point arithmetic in the scoring model produces a score of 649.9999 or 650.0001, ambiguously straddling the boundary.

**Expected System Behavior:**
Boundary-equal scores must consistently resolve to a defined default outcome — either always `REFER` or always `ACCEPT` — documented in the product rules configuration. The decision must be based on the rule set version active at the moment the application entered the underwriting queue, not the moment the decision is computed (which may be later). Threshold changes must take effect only for applications entering the queue after the change timestamp, not those already in the queue.

**Failure Mode if Not Handled:**
- Inconsistent decisions for materially identical risks, creating fair-treatment regulatory exposure.
- An actuary updates the threshold to reduce exposure, but in-flight applications still get auto-bound under the old threshold, causing higher-than-modelled risk uptake.
- Floating-point boundary ambiguity causes different outcomes on different CPU architectures or JVM versions.

**Mitigation/Implementation Notes:**
- Define boundary behaviour explicitly in the rule configuration: `boundary_condition: INCLUDE_UPPER | EXCLUDE_UPPER`.
- Use fixed-precision decimal arithmetic (e.g., `BigDecimal` in Java, `Decimal` in Python) for all risk score computations.
- Snapshot the active rule set version ID onto the application record when it enters the underwriting queue; evaluations must use this snapshotted version.
- Emit a `ThresholdBoundaryHit` event whenever a score is within ±1 point of any threshold, for actuarial monitoring.

---

### EC-PIU-006: Reinsurance Capacity Exhausted

**Severity:** P1

**Description:**
The insurer operates under proportional and non-proportional reinsurance treaties that define maximum capacity per risk or per aggregate period. When a new policy would cause the total ceded exposure under a treaty to exceed the agreed capacity limit, the system must detect this before binding the policy. Failure to detect capacity exhaustion results in writing unprotected risk above the retention limit.

**Trigger Condition:**
- A large commercial property policy is submitted. Its sum insured, when added to current ceded exposure under the relevant facultative treaty, would push the treaty over its agreed capacity.
- Multiple brokers submit policies simultaneously, each individually within capacity, but collectively exhausting it in a race condition.
- Annual treaty renewal has not yet been confirmed, but the system continues placing risk under the expiring treaty.

**Expected System Behavior:**
Before binding any policy that has a reinsurance placement, the system must perform a real-time capacity check against the reinsurance ledger. If capacity is exhausted, the policy must be held in a `PENDING_REINSURANCE` queue and the underwriter notified immediately. The system must not auto-bind the policy. The capacity check must be performed under a write lock on the relevant treaty record to prevent concurrent over-placement.

**Failure Mode if Not Handled:**
- The insurer writes risk above treaty capacity, bearing 100% of any loss that should have been reinsured — a potentially catastrophic solvency event.
- Reinsurance premium invoices are incorrect, triggering dispute resolution with reinsurers.
- Solvency II capital calculations are incorrect because unprotected exposure is not reflected in the SCR.

**Mitigation/Implementation Notes:**
- Maintain a `reinsurance_capacity_ledger` table with a row-level lock during policy binding for treaty capacity checks.
- Implement a `ReinsuranceCapacityService` that returns `AVAILABLE`, `TIGHT` (within 5% of limit), or `EXHAUSTED` with remaining capacity in the response.
- For `TIGHT` status, alert the reinsurance team via PagerDuty integration.
- Use optimistic locking with a version counter on treaty records; detect and retry on version conflict.
- Provide a real-time capacity dashboard for the reinsurance operations team.

---

### EC-PIU-007: Policy Number Collision

**Severity:** P1

**Description:**
Policy numbers are permanent, externally visible identifiers that appear on schedules, certificates of insurance, court documents, and regulatory filings. Although UUIDs or structured sequential numbers are generally collision-resistant, edge cases arise: hash-based short codes can collide; sequential number generators can reset after database restore; distributed systems can generate the same number independently before synchronising.

**Trigger Condition:**
- A disaster recovery restore rolls back the sequence generator in the policy number table, causing the next generated number to have already been used.
- A microservice instance starts with a stale local cache of the last-used number sequence and generates duplicates before synchronising with the primary store.
- A short, human-friendly policy number format (e.g., 8-character alphanumeric) suffers a birthday-problem collision after issuing sufficient policies.

**Expected System Behavior:**
Policy number generation must enforce uniqueness at the database level via a unique constraint on the `policy_number` column. The generation algorithm must use a database sequence (not application-level counters) to guarantee monotonic, unique values. On collision detection (unique constraint violation), the system must automatically retry generation up to three times with a different seed before raising an alert. The failed generation attempt must be logged.

**Failure Mode if Not Handled:**
- Two policies share the same number. Claims filed against one number may be applied to the wrong policy, causing incorrect payouts.
- The insurer is unable to produce a unique policy document for regulatory or legal proceedings.
- Certificate of insurance verification APIs return ambiguous results when policy number is used as a lookup key.

**Mitigation/Implementation Notes:**
- Use `BIGSERIAL` or equivalent database-native sequence for policy number generation — never application-managed counters.
- Add a `UNIQUE` index on `policies.policy_number`.
- In DR runbooks, explicitly document the post-restore procedure for resetting sequences to `MAX(policy_number) + 1` before resuming operations.
- Expose a `GET /policies/{policyNumber}/exists` endpoint for integration partners to verify uniqueness externally.
- Monitor for collision retry events; more than two in any 24-hour window should trigger a root-cause investigation.

---

### EC-PIU-008: Currency Mismatch on Multi-Currency Policy

**Severity:** P2

**Description:**
Multi-national commercial policies may be denominated in one currency (e.g., USD) while the policyholder's payment account, broker's reporting currency, and the insurer's functional currency are all different (e.g., EUR, GBP, SGD). A mismatch occurs when premium payments, claim settlements, or endorsement adjustments are processed in a currency different from the policy denomination without explicit conversion logic.

**Trigger Condition:**
- A European broker submits a USD-denominated commercial marine policy but sends the premium payment in EUR.
- An endorsement is processed that increases the sum insured without recalculating the premium in the policy's native currency.
- Exchange rates in the system are stale (not updated for 24 hours) and a payment is processed at an incorrect rate.

**Expected System Behavior:**
The system must maintain a canonical policy currency and store all financial values in that currency. When a payment is received in a different currency, the system must apply the rate-of-exchange as of the payment value date using a real-time or intraday rate feed. The applied rate and the source of the rate must be stored on every financial transaction record. If the rate feed is unavailable, the system must hold the payment in a `PENDING_FX_CONVERSION` state rather than applying a stale rate beyond a configurable staleness threshold (default: 4 hours).

**Failure Mode if Not Handled:**
- Premium income is understated or overstated in the insurer's financial statements due to incorrect FX conversion.
- A claim settlement is paid in the wrong currency, causing financial loss to either the claimant or the insurer.
- IFRS 17 monetary unit assumptions are violated, producing incorrect contractual service margin calculations.

**Mitigation/Implementation Notes:**
- Store `currency_code` (ISO 4217) on every policy, premium schedule, claim, and financial transaction record.
- Integrate a real-time FX rate provider (e.g., ECB, Bloomberg FX) with a fallback to a secondary provider.
- Implement `FxRateService` with staleness detection: if the latest rate is older than `max_rate_age_hours`, return `RATE_UNAVAILABLE` rather than the stale rate.
- Use multi-currency ledger design: record both `original_amount + original_currency` and `converted_amount + policy_currency + applied_rate + rate_timestamp` on every financial line.
- Generate a daily FX reconciliation report comparing converted totals against the rate feed.
