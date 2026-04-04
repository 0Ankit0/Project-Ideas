# Edge Cases — Admission and Application

Domain-specific failure modes, impact assessments, and mitigation strategies for the admission cycle, entrance examination, merit list generation, scholarship auto-award, and applicant-to-student conversion workflows.

Edge case IDs in this file are permanent: **EC-ADMIT-001 through EC-ADMIT-006**.

---

## EC-ADMIT-001 — Admission Cycle Published But No Entrance Exam Configured

| Field | Detail |
|---|---|
| **Failure Mode** | Admin publishes an admission cycle with `entrance_exam_required = true` but does not configure an entrance exam (no exam template, date, or scoring rubric attached). Applicants submit applications and pay application fees, but cannot take the exam. Merit list generation is blocked because there are no scores to rank. |
| **Impact** | Admission pipeline stalls — applicants are stuck post-application with no path forward. Delayed admissions cascade into late enrollment, classroom assignment backlog, and semester start disruption. Application fee refund requests increase support burden. Institutional reputation risk if delays become public. |
| **Detection** | Pre-publish validation check: `SELECT ac.id FROM admission_cycle ac WHERE ac.entrance_exam_required = true AND NOT EXISTS (SELECT 1 FROM entrance_exam ee WHERE ee.admission_cycle_id = ac.id AND ee.status = 'CONFIGURED')`. Alert: `emis.admission.published_without_exam`. |
| **Mitigation / Recovery** | (1) Confirm the incident — identify which admission cycle was published without exam configuration. (2) Temporarily unpublish the cycle from the external portal to prevent additional applications. (3) Configure the entrance exam (template, schedule, scoring rubric). (4) Re-publish the cycle and notify all existing applicants of the exam schedule. (5) If application fees were charged, extend the application window to compensate for lost time. (6) Write incident report and update this document if new findings. |
| **Prevention** | Block the publish action if `entrance_exam_required = true` but no exam is configured. The `AdmissionCycleService.publish()` method must call `validate_exam_configuration()` before setting `status = 'PUBLISHED'`. UI disables the publish button with a tooltip explaining the missing configuration. Add integration test that attempts publish without exam config and asserts 422 `EXAM_NOT_CONFIGURED`. |

---

## EC-ADMIT-002 — Entrance Exam Score Tie in Merit List

| Field | Detail |
|---|---|
| **Failure Mode** | Multiple applicants achieve identical composite scores on the entrance examination. The merit list generation algorithm has no tiebreaker logic configured, resulting in arbitrary or non-deterministic ordering (e.g., based on database insertion order or hash). Applicants ranked below the tied group may be unfairly displaced, and scholarship auto-award boundaries become ambiguous. |
| **Impact** | Unfair merit ordering creates applicant disputes and potential legal challenges. Scholarship auto-awards to "top N" students produce inconsistent results across regenerations. Institutional credibility is undermined if ranking appears arbitrary. |
| **Detection** | Duplicate score detection during merit list generation: `SELECT composite_score, COUNT(*) AS tied_count FROM merit_list WHERE admission_cycle_id = ? GROUP BY composite_score HAVING COUNT(*) > 1`. Alert: `emis.admission.merit_list_score_tie`. |
| **Mitigation / Recovery** | (1) Confirm the incident — identify tied applicants and their positions in the merit list. (2) Apply tiebreaker criteria in priority order: previous academic record GPA → entrance exam sub-scores (subject-wise) → application submission timestamp (earlier submission wins). (3) Regenerate the merit list with tiebreaker applied. (4) If the merit list was already published, notify affected applicants of the revised ranking with explanation. (5) Document the tiebreaker criteria used in the cycle's audit log. (6) Write incident report and update this document if new findings. |
| **Prevention** | Require tiebreaker rule configuration as a mandatory step in admission cycle setup. The `MeritListService.generate()` method must apply `AdmissionCycle.tiebreaker_rules` (ordered list of criteria) before finalizing rankings. Add constraint: `admission_cycle.tiebreaker_rules IS NOT NULL` enforced at database level. UI shows a tiebreaker configuration step during cycle creation with sensible defaults (academic record > sub-scores > timestamp). |

---

## EC-ADMIT-003 — Merit List Published But Scholarship Fund Insufficient

| Field | Detail |
|---|---|
| **Failure Mode** | Admin configures auto-award for the top 20 merit students, but the scholarship fund only has sufficient balance to cover 15 awards. The auto-award process either fails entirely (blocking all awards) or awards all 20 with 5 unfunded — creating obligations the institution cannot honour. |
| **Impact** | Top-ranking students do not receive promised scholarships, causing trust erosion and potential legal liability. If unfunded awards are disbursed, the scholarship fund goes negative, creating accounting discrepancies and donor reporting issues. Delayed scholarship communication affects students' financial planning for enrollment. |
| **Detection** | Fund balance check before auto-award execution: `SELECT (sp.fund_total - sp.fund_utilized) AS fund_remaining, (? * sp.award_amount * sp.award_duration_semesters) AS required_amount FROM scholarship_program sp WHERE sp.id = ?`. Alert: `emis.admission.scholarship_fund_shortfall` when `required_amount > fund_remaining`. |
| **Mitigation / Recovery** | (1) Confirm the incident — calculate exact shortfall amount and number of affected students. (2) Halt auto-award execution before disbursement. (3) Warn admin of the shortfall with exact figures. (4) Allow admin to choose: partial award (top 15 only), proportional reduction across all 20, or fund top-up request to finance department. (5) Once funding is resolved, resume auto-award for remaining students. (6) Notify all affected applicants of their scholarship status. (7) Write incident report and update this document if new findings. |
| **Prevention** | Validate fund balance at auto-award configuration time: `fund_remaining >= (top_n × award_amount × award_duration_semesters)`. Block auto-award config if insufficient with error `SCHOLARSHIP_FUND_INSUFFICIENT`. The `ScholarshipAutoAwardService.configure()` method must perform this check. Re-validate at execution time (fund may have been utilized between config and execution). UI shows real-time fund balance and projected utilisation during auto-award setup. |

---

## EC-ADMIT-004 — Applicant Conversion With Race Condition on Bill Payment

| Field | Detail |
|---|---|
| **Failure Mode** | Staff clicks the "Convert to Student" button on the dashboard while the applicant's last bill payment is still being processed by the payment gateway. The conversion service checks `outstanding_balance > 0`, finds the unpaid invoice (payment is in-flight), and blocks the conversion with `OUTSTANDING_BALANCE` error — even though the student has actually initiated and completed payment at the gateway level. |
| **Impact** | Conversion is blocked despite the student having paid. Staff retries repeatedly, creating frustration. If staff waits and retries later, the conversion window may close. Student onboarding is delayed, potentially missing semester start. |
| **Detection** | Payment status check with pending transaction awareness: `SELECT i.id, i.amount_due, COALESCE(p.status, 'NONE') AS payment_status FROM invoice i LEFT JOIN payment p ON p.invoice_id = i.id WHERE i.applicant_id = ? AND i.amount_due > 0 AND (p.status IS NULL OR p.status IN ('PENDING', 'PROCESSING'))`. Alert: `emis.admission.conversion_blocked_pending_payment`. |
| **Mitigation / Recovery** | (1) Confirm the incident — check if the applicant has a payment in `PENDING` or `PROCESSING` status. (2) Show pending payments prominently in the conversion UI so staff can see the payment is in-flight. (3) Allow conversion with a `payment_pending` flag: `applicant.conversion_status = 'CONVERTED_PAYMENT_PENDING'`. (4) Register a webhook listener for the pending payment; auto-complete the conversion (clear the flag) once payment is confirmed. (5) If payment ultimately fails, notify staff and revert conversion status. (6) Write incident report and update this document if new findings. |
| **Prevention** | Conversion validation must distinguish between "unpaid" and "payment in-flight". The `ApplicantConversionService.validate_financials()` method must check `Payment.status` for the outstanding invoice. If status is `PENDING` or `PROCESSING`, allow conversion with `payment_pending` flag instead of blocking. Payment gateway webhook confirmation must trigger a re-validation that clears the flag. Add integration test simulating concurrent payment + conversion. |

---

## EC-ADMIT-005 — Applicant Conversion After Admission Cycle Closed and Seats Full

| Field | Detail |
|---|---|
| **Failure Mode** | An accepted applicant delays bill payment past the expected clearance window. By the time the applicant clears all bills and staff attempts conversion, all available seats in the program have been filled by other converted students. The applicant has a valid acceptance letter but cannot be enrolled. |
| **Impact** | Accepted applicant cannot enroll despite having completed all requirements — creates a dispute and potential legal challenge. Institutional reputation is damaged. Applicant may lose an academic year. Revenue loss if applicant seeks admission elsewhere. |
| **Detection** | Seat count check at conversion time: `SELECT p.max_intake, COUNT(s.id) AS converted_count FROM program p LEFT JOIN student s ON s.program_id = p.id AND s.admission_cycle_id = ? WHERE p.id = ? GROUP BY p.max_intake HAVING COUNT(s.id) >= p.max_intake`. Alert: `emis.admission.conversion_seats_exhausted`. |
| **Mitigation / Recovery** | (1) Confirm the incident — verify seat count and applicant's acceptance status. (2) Maintain a waitlist ordered by acceptance date. (3) If a seat opens (another converted student withdraws or defers), allow waitlisted applicant to convert. (4) Admin override available for exceptional cases (e.g., applicant delayed due to medical emergency) with mandatory documentation and department head approval. (5) If no seat becomes available, offer deferral to next admission cycle with guaranteed acceptance. (6) Write incident report and update this document if new findings. |
| **Prevention** | Set a bill clearance deadline in the admission cycle configuration: `admission_cycle.bill_clearance_deadline`. Auto-cancel acceptance if bills are not cleared within the window — send warning notifications at 7 days, 3 days, and 1 day before deadline. Released seats become available for waitlisted applicants. The `AdmissionCycleService.enforce_deadlines()` cron job runs daily during the clearance window. UI shows real-time seat availability and clearance deadline countdown to both staff and applicants. |

---

## EC-ADMIT-006 — Scholarship Auto-Deduction Exceeds Invoice Amount

| Field | Detail |
|---|---|
| **Failure Mode** | A student receives a full merit scholarship (100% tuition coverage) via auto-award and also holds a department-specific scholarship. During invoice generation, both scholarships are applied as fee adjustments. The total deduction exceeds the invoice amount, producing a negative balance — effectively implying the institution owes the student money. |
| **Impact** | Negative invoice amount creates an accounting error. Financial reports show incorrect revenue. If the negative amount is processed as a refund, the institution loses money on a scholarship meant to waive fees, not pay the student. Audit findings for scholarship fund misuse. |
| **Detection** | Stacking validation during invoice generation: `SELECT i.gross_amount, SUM(sa.deduction_amount) AS total_deductions FROM invoice i JOIN scholarship_adjustment sa ON sa.invoice_id = i.id WHERE i.student_id = ? AND i.semester_id = ? GROUP BY i.gross_amount HAVING SUM(sa.deduction_amount) > i.gross_amount`. Alert: `emis.finance.scholarship_deduction_exceeds_invoice`. |
| **Mitigation / Recovery** | (1) Confirm the incident — identify the student, invoice, and overlapping scholarships. (2) Cap total scholarship deduction at the invoice gross amount: `total_deduction = MIN(sum_of_scholarships, invoice.gross_amount)`. (3) Reduce the newest (most recently awarded) scholarship proportionally to fit within the cap — this aligns with BR-SCHOLARSHIP-001 stacking policy. (4) Recalculate and reissue the invoice with corrected adjustments. (5) Notify the student and financial aid office of the adjustment. (6) Write incident report and update this document if new findings. |
| **Prevention** | Enforce stacking limits during auto-award configuration: `InvoiceService.apply_scholarships()` must calculate cumulative deductions and cap at `invoice.gross_amount`. The `ScholarshipStackingValidator` must reject configurations where projected total deductions exceed 100% of tuition. Add database constraint: `CHECK (invoice.net_amount >= 0)` to prevent negative invoices at the data level. During auto-award, check existing scholarships for the student before awarding additional ones. |

---

## Operational Policy Addendum

### Admission Data Integrity Policies
All applicant-to-student conversions require explicit STAFF or ADMIN action with verification of financial clearance. Conversions are logged in AuditLog with the converting staff member's ID, timestamp, and applicant financial status at conversion time. Bulk conversions generate a per-applicant success/failure report.

### Merit List Publication Policies
Merit lists must not be published until tiebreaker rules have been applied and verified. Published merit lists are immutable — corrections require a new version with a changelog entry. All merit list versions are retained for audit purposes. Score recalculations (e.g., due to exam answer key corrections) trigger automatic merit list regeneration with notification to all affected applicants.

### Scholarship Auto-Award Policies
Auto-award execution requires admin confirmation after the system displays the projected fund utilisation. Awards are provisional for 48 hours after execution, during which admin can review and revoke individual awards. After the provisional period, awards are finalised and disbursement-eligible. Fund balance alerts are sent to the finance team when utilisation exceeds 80% of the fund total.
