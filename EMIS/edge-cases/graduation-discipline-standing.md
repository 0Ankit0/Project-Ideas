# Edge Cases — Graduation, Discipline & Academic Standing

> Edge cases for graduation processing, degree conferral, student discipline, and academic standing determination.

---

## Graduation & Degree Conferral

### EC-GRAD-001: Degree Audit Passes but Student Has Unreported Incomplete Grade

| Field | Detail |
|---|---|
| **Failure Mode** | A course instructor has not submitted a final grade (still marked as INCOMPLETE in the system), but the degree audit logic only checks for enrolled courses with grades. The audit passes because the INCOMPLETE course is not flagged as a failed requirement. |
| **Impact** | Student receives diploma without completing all coursework. Accreditation audit finds discrepancy. Diploma must be revoked or held — reputational and legal risk. |
| **Detection** | Pre-graduation report that cross-checks enrollment records (ACTIVE status) against grade records (SUBMITTED/PUBLISHED status). Alert if any enrollment for the graduating student has no corresponding grade record. |
| **Mitigation / Recovery** | 1. Place graduation application on hold. 2. Contact instructor for grade submission. 3. Re-run degree audit after grade received. 4. If diploma already issued, initiate formal hold and contact student. |
| **Prevention** | Degree audit query must explicitly check: `NOT EXISTS (SELECT 1 FROM enrollment WHERE student_id = ? AND status IN ('ACTIVE', 'INCOMPLETE') AND grade_id IS NULL)`. Add mandatory "no pending grades" assertion to audit pipeline. |

### EC-GRAD-002: Concurrent Graduation Applications for Same Student

| Field | Detail |
|---|---|
| **Failure Mode** | Student submits graduation application twice (double-click, browser retry, or API retry without idempotency). Two applications created, potentially leading to duplicate diploma numbers and duplicate alumni records. |
| **Impact** | Duplicate diplomas issued. Alumni database corruption. Verification system returns ambiguous results. |
| **Detection** | Unique constraint on (student_id, program_id, expected_graduation_semester). Monitor for constraint violations. |
| **Mitigation / Recovery** | 1. Reject second application with CONFLICT error. 2. If both were processed, invalidate the duplicate diploma number. 3. Merge duplicate alumni records. |
| **Prevention** | Add database unique constraint: `UNIQUE(student_id, program_id) WHERE status NOT IN ('REJECTED', 'WITHDRAWN')`. Enforce idempotency key on graduation application endpoint. |

### EC-GRAD-003: Honors Classification Changes After Diploma Generation

| Field | Detail |
|---|---|
| **Failure Mode** | A grade appeal is resolved after graduation, changing the student's CGPA. The new CGPA changes the honors classification (e.g., from Cum Laude to Magna Cum Laude, or from Magna Cum Laude to no honors). |
| **Impact** | Diploma has incorrect honors designation. Student may have grounds for complaint if honors were downgraded post-graduation. |
| **Detection** | Post-graduation grade change event triggers CGPA recalculation. System compares new honors classification against diploma record. |
| **Mitigation / Recovery** | 1. Flag discrepancy for registrar review. 2. If honors upgraded, issue replacement diploma with new number. 3. If honors downgraded, legal review required before action. 4. Original diploma number marked as superseded (not invalidated). |
| **Prevention** | Block grade appeals for courses in semesters where the student has already been conferred a degree, unless SUPER_ADMIN override. Add warning in grade appeal system when student is a graduate. |

### EC-GRAD-004: Diploma Verification Service Returns Incorrect Data

| Field | Detail |
|---|---|
| **Failure Mode** | Public diploma verification endpoint returns data for a revoked or superseded diploma, showing it as valid. |
| **Impact** | Fraudulent use of revoked diploma goes undetected. Employer or institution relies on false verification. |
| **Detection** | Quarterly audit of verification responses against diploma status in database. Automated test that queries revoked diplomas and asserts `valid: false`. |
| **Mitigation / Recovery** | 1. Immediately patch verification query to check diploma status. 2. Notify any verification requesters who queried the revoked diploma in the last 90 days. |
| **Prevention** | Verification query must always join with diploma status and return `valid: false` for any status other than ACTIVE. Cache invalidation on diploma status change. |

---

## Student Discipline

### EC-DISC-001: Panel Member Has Undisclosed Conflict of Interest

| Field | Detail |
|---|---|
| **Failure Mode** | A discipline panel member is the accused student's academic advisor or has a personal relationship, but does not self-declare the conflict. Hearing proceeds with biased panel. |
| **Impact** | Decision may be overturned on appeal due to procedural violation. Legal liability for the institution. Student's rights violated. |
| **Detection** | System cross-checks panel member IDs against student's advisor_id, course instructor IDs, and departmental relationships. Flag any matches. |
| **Mitigation / Recovery** | 1. If discovered before hearing, replace panel member. 2. If discovered after decision, offer new hearing with unbiased panel. 3. Document the conflict and institutional response in case file. |
| **Prevention** | Automated conflict check at panel assignment time: query advisor assignments, current/past course enrollments, and departmental relationships. Require explicit "no conflict" attestation from each panel member. |

### EC-DISC-002: Sanction Enforcement Fails to Withdraw Student from Courses

| Field | Detail |
|---|---|
| **Failure Mode** | Suspension decision is recorded, but the automated workflow to withdraw the student from courses fails (Celery task crashes, network error, or service unavailable). Student remains enrolled and attends classes despite suspension. |
| **Impact** | Suspended student continues to earn grades (invalid). Other students' class experience affected. Institutional policy violated. Grades earned during suspension may need to be voided. |
| **Detection** | Reconciliation job (daily) that checks all students with SUSPENSION/EXPULSION sanction status against their enrollment status. Alert if any suspended student has ACTIVE enrollments. |
| **Mitigation / Recovery** | 1. Immediately withdraw student from all courses (grade: W). 2. Void any attendance or grades recorded after sanction effective date. 3. Notify affected instructors. 4. Investigate task failure root cause. |
| **Prevention** | Sanction enforcement uses saga pattern: decision → withdraw courses → block registration → deactivate access. Each step has compensation. Reconciliation job runs daily as safety net. |

### EC-DISC-003: Appeal Filed After Window Closes Due to Notification Delay

| Field | Detail |
|---|---|
| **Failure Mode** | Decision notification email was delayed (SMTP outage, spam filter). Student claims they didn't receive notification within the expected timeframe, so their 10-business-day window effectively started late. Appeal rejected as late. |
| **Impact** | Student denied due process. Potential legal challenge. Institutional reputation damage. |
| **Detection** | Compare notification delivery timestamp (from delivery log) against appeal deadline. If notification was delivered less than 10 business days before the deadline, flag for review. |
| **Mitigation / Recovery** | 1. Check notification delivery log for the decision notification. 2. If delivery was delayed >24 hours, extend appeal deadline by the delay duration. 3. If notification bounced/failed, reset appeal window from re-delivery date. |
| **Prevention** | Decision notification must be delivered via at least 2 channels (email + in-app). Appeal deadline calculation should use `MAX(decision_date + 10 business days, notification_delivered_at + 10 business days)`. Track delivery confirmation before starting appeal countdown. |

---

## Academic Standing

### EC-STAND-001: Standing Calculation Runs with Incomplete Grades

| Field | Detail |
|---|---|
| **Failure Mode** | Batch standing calculation is triggered (end of semester) but some courses still have grades in DRAFT or SUBMITTED (not PUBLISHED) status. Students' standing is calculated on partial data. |
| **Impact** | Students may be incorrectly placed on probation or suspension based on incomplete GPA. Dean's List may include/exclude students incorrectly. Standing-based restrictions (credit limits) applied unfairly. |
| **Detection** | Pre-calculation check: count of enrollments without PUBLISHED grades for the semester. If count > 0, block calculation and alert registrar. |
| **Mitigation / Recovery** | 1. Do not run standing calculation until all grades are PUBLISHED. 2. If calculation already ran with partial data, mark all standings for the semester as PROVISIONAL. 3. Re-run after all grades published. 4. Notify affected students that standings are provisional. |
| **Prevention** | Standing calculation service must assert: `SELECT COUNT(*) FROM enrollment e WHERE e.semester_id = ? AND e.status = 'ACTIVE' AND NOT EXISTS (SELECT 1 FROM grade g WHERE g.enrollment_id = e.id AND g.status = 'PUBLISHED') = 0`. Block calculation if assertion fails. |

### EC-STAND-002: Student on Probation Exceeds Credit Limit Due to Race Condition

| Field | Detail |
|---|---|
| **Failure Mode** | Probationary student (max 12 credits) registers for courses in rapid succession, submitting multiple enrollment requests before the credit total check updates. Total enrolled credits exceed the limit. |
| **Impact** | Student overloaded despite academic restrictions. If they struggle, the overload worsens their academic situation. Policy violation in accreditation audit. |
| **Detection** | Credit hour check uses `SELECT SUM(credit_hours) FROM enrollment WHERE student_id = ? AND semester_id = ? AND status = 'ACTIVE' FOR UPDATE` to lock and verify. Post-registration reconciliation job checks totals. |
| **Mitigation / Recovery** | 1. Identify over-enrolled students via reconciliation. 2. Contact student to drop excess courses. 3. If past add/drop deadline, escalate to department head for forced withdrawal. |
| **Prevention** | Enrollment service must use `SELECT FOR UPDATE` on student's enrollment records during credit calculation. Apply database check constraint: create a trigger or materialized view that enforces per-student per-semester credit limits atomically. |

### EC-STAND-003: Dean's List Includes Student with Disciplinary Sanction

| Field | Detail |
|---|---|
| **Failure Mode** | Dean's List automation checks GPA and credit hours but does not check disciplinary records. A student with a current disciplinary probation appears on the Dean's List. |
| **Impact** | Institutional embarrassment. Published honor list includes student under sanction. May need to issue correction. |
| **Detection** | Post-generation audit that joins Dean's List with active disciplinary cases. |
| **Mitigation / Recovery** | 1. Remove student from published Dean's List. 2. Issue correction if list was already distributed. 3. Notify student privately. |
| **Prevention** | Dean's List query must include: `AND NOT EXISTS (SELECT 1 FROM disciplinary_case dc WHERE dc.student_id = s.id AND dc.status NOT IN ('DISMISSED', 'CLOSED') AND dc.sanction IS NOT NULL)`. Add to automated test suite. |

### EC-STAND-004: Maximum Time-to-Degree Override Without Proper Authorization

| Field | Detail |
|---|---|
| **Failure Mode** | A student exceeding maximum time-to-degree gets an extension approved by a staff member without Academic Board authorization. System doesn't enforce the approval level. |
| **Impact** | Policy violation. Student may accumulate additional semesters of fees. Accreditation risk if completion rates are affected. |
| **Detection** | Audit log review: time-to-degree extensions must have `approved_by` role = ACADEMIC_BOARD or SUPER_ADMIN. Alert if lower role approves. |
| **Mitigation / Recovery** | 1. Flag the extension for Academic Board ratification. 2. If Board rejects, student must be given one semester to complete or withdraw. |
| **Prevention** | Extension approval endpoint must check `request.user.role in ('ACADEMIC_BOARD', 'SUPER_ADMIN')`. Enforce at service layer, not just UI. |
