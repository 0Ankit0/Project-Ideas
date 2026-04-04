# Edge Cases — Recruitment, Transfer Credits, Scholarships & Facilities

> Edge cases for faculty recruitment, transfer credit evaluation, scholarship management, and room/facility booking.

---

## Faculty Recruitment

### EC-RECRUIT-001: Candidate Hired but Background Check Returns After Onboarding

| Field | Detail |
|---|---|
| **Failure Mode** | Background verification takes longer than expected. HR proceeds with onboarding before verification completes. Verification later returns negative results (falsified qualifications). |
| **Impact** | Unqualified faculty teaching courses. Grades given by unqualified instructor may be challenged. Institutional liability. Employment termination process needed. |
| **Detection** | Daily check: employees in PROBATION status whose background_check_status is still PENDING after 30 days, or FAILED at any time. |
| **Mitigation / Recovery** | 1. Immediately suspend teaching responsibilities. 2. Assign replacement instructor. 3. Review all grades issued by the instructor. 4. Initiate employment termination per HR policy. 5. Notify affected students and offer re-evaluation option. |
| **Prevention** | Enforce policy: no classroom assignment until background check status = PASSED. Add system constraint: `teaching_assignments.faculty_id` must reference employee with `background_check_status = 'PASSED'`. Allow limited orientation activities during verification period. |

### EC-RECRUIT-002: Offer Extended to Multiple Candidates for Single Position

| Field | Detail |
|---|---|
| **Failure Mode** | Race condition: two HR staff members independently extend offers to different candidates for the same single-vacancy position. Both candidates accept. |
| **Impact** | Over-hiring beyond budget. One offer must be rescinded — legal and reputational risk. |
| **Detection** | Offer count check: `SELECT COUNT(*) FROM job_application WHERE posting_id = ? AND status IN ('OFFERED', 'HIRED')` should not exceed `job_posting.vacancies`. |
| **Mitigation / Recovery** | 1. Identify which offer was extended first (timestamp). 2. Honor the first offer. 3. Contact second candidate with apology and explanation. 4. Offer alternative position if available. |
| **Prevention** | Atomic check at offer time: `SELECT vacancies - (SELECT COUNT(*) FROM job_application WHERE posting_id = ? AND status IN ('OFFERED', 'HIRED')) AS remaining FOR UPDATE`. Reject if remaining ≤ 0. |

---

## Transfer Credits

### EC-TRANSFER-001: Transfer Credits Exceed Limit After Approved Batch

| Field | Detail |
|---|---|
| **Failure Mode** | Multiple transfer credit applications are approved individually, each passing the 40% limit check. But cumulatively, they exceed the limit because each check only considered previously approved credits, not concurrently pending approvals. |
| **Impact** | Student has more transfer credits than policy allows. Degree audit may be inaccurate. Accreditation finding. |
| **Detection** | Post-approval reconciliation: `SELECT SUM(credits_awarded) FROM transfer_credit WHERE student_id = ? AND status = 'APPROVED'` must be ≤ 40% of program total. |
| **Mitigation / Recovery** | 1. Identify excess credits. 2. Contact student and registrar. 3. Student must choose which transfer credits to retain within limit. 4. Update degree audit. |
| **Prevention** | Transfer approval must use `SELECT FOR UPDATE` on student's transfer credit records. Total check must include both APPROVED and UNDER_REVIEW credits. |

### EC-TRANSFER-002: Articulation Agreement Expires Mid-Evaluation

| Field | Detail |
|---|---|
| **Failure Mode** | Transfer credit evaluation begins under a valid articulation agreement. By the time registrar approves, the agreement has expired. Auto-mapped equivalencies may no longer be valid. |
| **Impact** | Credits approved under expired agreement terms. Source institution may have changed curriculum. |
| **Detection** | Check agreement expiry date at approval time (not just at submission). |
| **Mitigation / Recovery** | 1. Flag for registrar review. 2. Verify current curriculum at source institution. 3. If still equivalent, approve with manual justification. 4. If changed, re-evaluate. |
| **Prevention** | Agreement validity check at both submission and approval time. Warn registrar if agreement expires within 30 days. |

---

## Scholarships & Financial Aid

### EC-SCHOL-001: Scholarship Disbursement Applied to Wrong Invoice

| Field | Detail |
|---|---|
| **Failure Mode** | Scholarship fee adjustment is applied to the wrong semester's invoice (previous semester instead of current). Student's current semester shows unpaid, triggering financial hold. Previous semester shows overpayment. |
| **Impact** | Student blocked from registration due to false financial hold. Accounting discrepancy. Student frustration and support escalation. |
| **Detection** | Reconciliation: scholarship_award.semester_id must match linked_invoice.semester_id. Alert on mismatch. |
| **Mitigation / Recovery** | 1. Reverse the incorrect fee adjustment. 2. Apply to correct invoice. 3. Release any incorrectly applied financial hold. 4. Notify student of correction. |
| **Prevention** | Disbursement service must validate: `invoice.semester_id = scholarship_award.semester_id`. Reject with clear error if mismatched. |

### EC-SCHOL-002: Scholarship Fund Over-Committed Due to Concurrent Awards

| Field | Detail |
|---|---|
| **Failure Mode** | Two financial aid administrators award scholarships from the same fund simultaneously. Each checks fund balance independently and sees sufficient funds. Combined awards exceed fund total. |
| **Impact** | Fund overdrawn. Donor reporting shows negative balance. Some awards may need to be rescinded. |
| **Detection** | Check: `fund_utilized > fund_total` after each award. Alert immediately. |
| **Mitigation / Recovery** | 1. Identify which award caused the overcommit (last timestamp). 2. Contact student and explain situation. 3. Either secure additional funding or waitlist the over-committed award. |
| **Prevention** | Award operation must use `SELECT fund_total, fund_utilized FROM scholarship_program WHERE id = ? FOR UPDATE`. Calculate remaining atomically. Reject if `fund_utilized + award_amount > fund_total`. |

### EC-SCHOL-003: Auto-Award Scholarship Triggers During Grade Correction

| Field | Detail |
|---|---|
| **Failure Mode** | A grade correction temporarily raises a student's GPA above the auto-award threshold. Auto-award system fires and grants scholarship. The grade is then corrected back (it was a data entry error), dropping GPA below threshold. Student has already received award notification. |
| **Impact** | Scholarship awarded based on incorrect data. Revocation process needed. Student disappointment and potential complaint. |
| **Detection** | Auto-award should not trigger on grade amendments — only on official semester-end grade publication events. |
| **Mitigation / Recovery** | 1. Run eligibility re-check after any grade amendment. 2. If no longer eligible, place award in PENDING_REVIEW. 3. Admin reviews before disbursement. |
| **Prevention** | Auto-award scheduler runs only on `standing.determined.v1` event (semester end), NOT on individual grade change events. Add 24-hour cooling period after any grade change before auto-award eligibility check. |

---

## Room & Facility Management

### EC-FACILITY-001: Exam Scheduling Preempts Confirmed Room Booking Without Notice

| Field | Detail |
|---|---|
| **Failure Mode** | Exam scheduling system books a room that already has a confirmed non-academic booking. The existing booking is silently overwritten. The original booker shows up to find the room occupied by an exam. |
| **Impact** | Disrupted meeting/event. Loss of trust in booking system. Potential cascade (missed deadlines, rescheduling chaos). |
| **Detection** | Booking conflict notification: when exam scheduling preempts a booking, the system must log the preemption and notify the original booker at least 7 days in advance. |
| **Mitigation / Recovery** | 1. Notify original booker immediately of preemption. 2. Offer alternative room suggestions. 3. Log the preemption with reason (exam priority). |
| **Prevention** | Preemption policy: exam scheduling can preempt non-academic bookings only with ≥7 days notice. System must send notification before confirming the preemption. If <7 days, require admin approval. |

### EC-FACILITY-002: Recurring Booking Creates Conflict on Holiday

| Field | Detail |
|---|---|
| **Failure Mode** | Weekly recurring booking is created for "every Monday for 16 weeks." Some Mondays fall on institutional holidays. The booking system creates entries for holiday dates, conflicting with the holiday block. |
| **Impact** | Room shows as booked on holidays (misleading). If another event is planned for the holiday, it sees no availability. |
| **Detection** | Booking creation should cross-check with academic calendar holiday entries. |
| **Mitigation / Recovery** | 1. Identify recurring bookings that overlap with holidays. 2. Cancel those specific instances. 3. Notify the booker. |
| **Prevention** | Recurring booking generation must skip dates that match entries in `academic_calendar WHERE event_type = 'HOLIDAY'`. Add validation at booking creation time. |

### EC-FACILITY-003: Room Capacity Exceeded Due to Combined Booking

| Field | Detail |
|---|---|
| **Failure Mode** | Two adjacent time slots in the same room are booked by different groups. One group's event runs over, and both groups are in the room simultaneously, exceeding fire safety capacity. |
| **Impact** | Fire safety violation. Insurance liability. Student/faculty safety risk. |
| **Detection** | Physical capacity monitoring (if IoT sensors available) or incident reports. System-level: ensure minimum 15-minute buffer between bookings in same room. |
| **Mitigation / Recovery** | 1. Enforce booking end times. 2. Security personnel check room turnover. 3. Report incidents for policy review. |
| **Prevention** | System enforces 15-minute buffer between consecutive bookings in the same room. Add constraint: `new_booking.start_time >= existing_booking.end_time + interval '15 minutes'` for same room and date. |
