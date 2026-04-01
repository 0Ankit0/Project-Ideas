# Edge Cases — Assessment and Grading

> **Scope:** Covers timed assessments, auto-grading, manual review, grade publication, rubrics, idempotency, clock skew, question corrections, score bounds, and bulk regrade campaigns.

---

## 1. Learner Loses Network During Timed Assessment Mid-Submission

**Failure Mode:** The learner's browser loses connectivity after answering questions but before the `POST /submissions` request completes. The server never receives the payload; the client timer may still count down. On reconnect the learner sees a blank or partially saved state.

**Impact:** Learner loses answered questions for that attempt; if attempt limits are enforced, the unsubmitted attempt may count as consumed. For high-stakes assessments this directly affects certification eligibility. Affects an estimated 1–3% of assessment sessions on mobile networks.

**Detection:**
- Monitor `attempt.state = ABANDONED` records where `answered_count > 0` but no submission event exists within the attempt window.
- Alert on spike in client-side `submission_error` events (JS error boundary logs).
- Track ratio of `attempt_started` to `submission_received` events per assessment per hour; alert if ratio drops below 0.92.

**Mitigation/Recovery:**
- Auto-save individual answers to server-side draft store every 30 seconds via `PATCH /attempts/{id}/draft`.
- On reconnect, client fetches draft and resumes from last saved state; timer continues from server-authoritative remaining time.
- Mark network-interrupted attempts as `state = DRAFT_RECOVERY` rather than consuming the attempt count until explicit submission or expiry.
- Operator playbook: manually reset attempt count for learners with documented network failures upon instructor approval.

---

## 2. Auto-Grading Score Differs from Instructor Manual Review

**Failure Mode:** The auto-grading engine scores a free-text or regex-matched answer using an outdated keyword list or faulty partial-credit formula, producing a score that the instructor later overrides by 10+ points (e.g., auto-grade returns 55/100, instructor awards 78/100).

**Impact:** Learner may have been blocked from the next module or denied a certificate based on incorrect auto-grade. Restoring access after the fact creates support tickets and erodes trust in automated scoring. Typical resolution takes 2–5 business days.

**Detection:**
- Flag any manual override where `abs(manual_score - auto_score) / max_score > 0.15`; route to QA queue.
- Log `grade_override` events with `reviewer_id`, `before_score`, `after_score`, and `reason_code`.
- Weekly divergence report: p90 of `|auto − manual|` per rubric version; alert if p90 > 10 points.

**Mitigation/Recovery:**
- Auto-grading models must be versioned; pin each submission to the model version active at submission time.
- When override divergence exceeds threshold, flag rubric version for re-validation before next assessment cohort.
- Provide learners with grade dispute workflow (max 72 h SLA); notify them automatically when their grade changes post-override.

---

## 3. Grade Published to Wrong Learner Context (Wrong Cohort)

**Failure Mode:** Instructor uses the bulk publish endpoint and passes the wrong `cohort_id` parameter (or the UI pre-fills a stale value). Grades intended for Cohort B are published and visible to Cohort A learners.

**Impact:** Learners in Cohort A see incorrect grades, potentially inflated or deflated. Cohort B learners see no grades. Depending on data sensitivity, this may constitute a FERPA/GDPR data incident. Incident response and re-publication take 4–8 hours.

**Detection:**
- `grade_published` events: join against enrollment records and alert if `learner_id` is not enrolled in the `cohort_id` attached to the grade.
- Monitor for abnormal spike in grade-related support tickets within 15 minutes of a publish event.
- Hourly integrity check: `SELECT COUNT(*) FROM grades g LEFT JOIN enrollments e ON g.learner_id = e.learner_id AND g.cohort_id = e.cohort_id WHERE e.id IS NULL`.

**Mitigation/Recovery:**
- Require server-side confirmation step before bulk publish: return preview list with learner count; instructor must confirm within 60 seconds.
- Immediately retract mis-published grades by setting `visible = false` on detection; notify affected learners of a data correction.
- Log incident to compliance audit trail; assess whether data-breach notification obligations are triggered.

---

## 4. Attempt Limit Changed Retroactively

**Failure Mode:** Admin updates `max_attempts` from 2 to 3 on a live assessment after some learners have already used both attempts. The system retrospectively grants or denies access inconsistently depending on whether the policy change is applied to historical records.

**Impact:** Learners who exhausted attempts before the change may remain locked out while later learners benefit from the new limit. Creates equity complaints and support escalations. Conversely, reducing the limit retroactively may confuse learners who expect more attempts.

**Detection:**
- Alert when `assessment.max_attempts` is modified on an assessment with `enrollment.status = ACTIVE`.
- Monitor support ticket keywords: "retry", "attempt limit", "locked out" following an assessment config change.

**Mitigation/Recovery:**
- Snapshot attempt limit into each `attempt` record at creation time (`attempt.limit_at_creation`); policy changes only apply to attempts started after the change.
- Provide admin UI with explicit "Apply to existing learners" toggle, disabled by default, with confirmation modal showing affected learner count.
- When increasing limit, automatically notify learners who had exhausted their prior limit that additional attempts are now available.

---

## 5. Rubric Edited During Active Grading Cycle

**Failure Mode:** Instructor adds, removes, or re-weights rubric criteria while graders are actively scoring submissions in the same grading cycle. Graders working before the change score against old criteria; graders after the change score against new criteria. Result: inconsistent scores across the same cohort.

**Impact:** Up to 30–40% of submissions may be graded on different criteria, making scores non-comparable. May require full regrade, adding 2–5 days of instructor work.

**Detection:**
- `rubric.updated_at` timestamp compared against `grading_session.started_at`; alert if rubric changes while any grading session is `IN_PROGRESS`.
- Track `rubric_version_id` on each scored criterion; flag submissions where `rubric_version_id` differs within the same assessment cycle.

**Mitigation/Recovery:**
- Lock rubric for editing once grading cycle begins (`rubric.state = LOCKED`); surface prominent warning to instructors.
- If a rubric change is critical, require admin to first end the active grading cycle, then start a new cycle with the updated rubric.
- Provide a regrade tool that re-scores only the submissions graded against the old rubric version.

---

## 6. Duplicate Submission Request (Idempotency Failure)

**Failure Mode:** Network retry or double-click causes the client to send `POST /submissions` twice within milliseconds. Without idempotency enforcement, the server creates two submission records for the same attempt, potentially grading both and recording the higher (or lower) score.

**Impact:** Duplicate grade records corrupt leaderboards, completion logic, and transcripts. If both submissions are graded, only one should win — but the wrong one may surface.

**Detection:**
- Alert on `attempt_id` appearing more than once in `submissions` table within a 5-second window.
- Monitor `duplicate_submission_rejected` counter; sudden drop may indicate idempotency guard is broken.

**Mitigation/Recovery:**
- Require `Idempotency-Key` header on all submission endpoints; return `200 OK` with the existing submission for duplicate keys within a 24-hour window.
- Store idempotency keys in Redis with TTL = 24 h; reject duplicates at the API gateway before hitting the grading engine.
- Periodic cleanup job: detect and tombstone duplicate submission records, preserving the earliest `created_at`.

---

## 7. Server-Side and Client-Side Clock Skew on Assessment Timer

**Failure Mode:** Learner's device clock is ahead by 3–5 minutes. The client-side timer shows time remaining, but the server has already marked the attempt as expired. Learner submits answers, server rejects with `410 Attempt Expired`.

**Impact:** Learner is denied credit for completed work; support escalations; potential legal exposure for high-stakes certifications.

**Detection:**
- Log `Clock-Offset` header (populated by client on each request using `Date` header comparison); alert if offset > 120 seconds.
- Track `submission_rejected_expired` events where `submitted_at < attempt.expires_at + 300s` (within 5-minute grace).

**Mitigation/Recovery:**
- Timer is server-authoritative: `expires_at` is stored server-side and returned to client; client displays countdown using `expires_at - server_now`, not a local timer.
- Apply a configurable server-side grace period (default 60 s) for submissions received after `expires_at` to account for network latency.
- On session start, return `X-Server-Time` header; client adjusts its local display using the delta.

---

## 8. Factually Incorrect Question Found After Submissions

**Failure Mode:** A question in a published quiz contains a factually wrong "correct" answer. Discovered after 200+ submissions have been graded. The affected question scores must be corrected for all past submissions.

**Impact:** Up to 100% of submissions may have incorrect scores for that question. Learners who failed due to this question may need course access restored. Regrade and notification campaign required.

**Detection:**
- Instructor reports via the "Question Challenge" workflow; review queue monitored with SLA of 2 business days.
- Anomaly detection: if a question has >80% incorrect response rate, flag for instructor review automatically.

**Mitigation/Recovery:**
- Implement "invalidate question" action: marks question as void, redistributes its weight to remaining questions or awards full credit to all learners for that item.
- Run async bulk-regrade job scoped to the question ID; update all affected `submission_answer` records and recompute total scores.
- Notify affected learners via in-app and email with corrected scores within 24 hours of the regrade completion.

---

## 9. Score Overflow: Submitted Score Exceeds `max_score`

**Failure Mode:** Partial-credit bonus logic contains a calculation bug (e.g., bonus multiplied instead of added) causing `computed_score = 130` when `max_score = 100`. The overflow score is stored and propagates to transcripts and GPA calculations.

**Impact:** Learner appears to have achieved an impossible score; transcript integrity is compromised; downstream GPA calculations may be inflated or throw exceptions.

**Detection:**
- Database constraint: `CHECK (score >= 0 AND score <= max_score)` on the `submission_scores` table; constraint violations generate alerts.
- API response validator: reject any grade write where `score > assessment.max_score`; log to `grade_validation_errors` metric.

**Mitigation/Recovery:**
- Clamp score at the application layer before persistence: `final_score = min(computed_score, max_score)`.
- If overflow records are already persisted, run a data-fix migration: `UPDATE submission_scores SET score = max_score WHERE score > max_score`.
- Post-fix, audit all downstream transcript aggregations and recompute affected GPAs.

---

## 10. Bulk Regrade Produces Inconsistent Results for a Subset

**Failure Mode:** A bulk regrade campaign (triggered by rubric correction) processes 5,000 submissions in parallel. Due to a race condition or worker crash mid-batch, 312 submissions are graded twice or not at all. The final score distribution contains duplicates and gaps.

**Impact:** Some learners receive two conflicting grade notifications; others see no update. Certificate eligibility may be incorrectly granted or denied for the affected subset.

**Detection:**
- Regrade job emits `regrade_completed` event per submission; reconcile against `regrade_job.expected_count` at job completion.
- Alert if `completed_count / expected_count < 0.999` or if any `submission_id` appears in regrade output more than once.
- Post-job integrity query: `SELECT submission_id, COUNT(*) FROM regrade_results GROUP BY submission_id HAVING COUNT(*) > 1`.

**Mitigation/Recovery:**
- Use exactly-once semantics for regrade jobs: claim submissions with a `regrade_claim_id` (optimistic lock) before processing; skip already-claimed records.
- Regrade job is idempotent: re-running on the same `campaign_id` only processes submissions not yet in `COMPLETE` state.
- After job completion, run automated reconciliation script and page on-call if mismatch > 0.1%; provide operator rerun command for failed subset.
| Auto-grading differs from instructor override | Score disputes and confusion | Preserve original score, override reason, and final published grade clearly |
| Reviewer publishes grade to wrong learner context | Privacy and correctness risk | Use strong submission identity checks and confirmation steps |
| Attempt limit changes after learners already started | Fairness and audit concerns | Version assessment rules and apply effective-date behavior explicitly |
| Rubric edited during active grading cycle | Inconsistent scores across learners | Lock rubric versions for active review sessions |


## Implementation Details: Grading Integrity Controls

- Persist rubric snapshot at submission start and grading completion.
- Support moderation workflows with first/second reviewer and tie-break policy.
- Record score provenance (`auto`, `manual`, `override`) per criterion.
