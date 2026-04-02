# Edge Cases — Academic Operations

Domain-specific failure modes, impact assessments, and mitigation strategies for all core academic workflows.

Edge case IDs in this file are permanent: **EC-ACAD-001 through EC-ACAD-010**.

---

## EC-ACAD-001 — Grade Submission During System Outage

| Field | Detail |
|---|---|
| **Failure Mode** | Faculty attempts to submit grades during a planned or unplanned API outage. |
| **Impact** | Grade submission window may close before the system recovers. Faculty unable to meet grading deadline. Students blocked from seeing results; GPA recalculation delayed. |
| **Detection** | HTTP 503 responses on grade submission endpoint; CloudWatch alarm on API 5xx rate > 1%; ECS task health check failures. |
| **Mitigation / Recovery** | (1) Portal shows offline banner with estimated recovery time. (2) Grade entry form auto-saves to browser localStorage on each keystroke. (3) On system recovery, portal offers to replay locally saved grades. (4) Exam officer can manually extend grading window for affected faculty via admin panel. |
| **Prevention** | Multi-AZ ECS deployment ensures single-AZ outages do not affect API availability. Planned maintenance windows scheduled outside grading periods as defined in the academic calendar. |

---

## EC-ACAD-002 — Concurrent Grade Amendment Race Condition

| Field | Detail |
|---|---|
| **Failure Mode** | Two faculty members (or a faculty member and an exam officer) simultaneously submit amendments to the same Grade record. |
| **Impact** | Last-write-wins without optimistic locking leads to a silently lost amendment. One amendment is overwritten without notification. Audit trail shows incorrect actor for the surviving change. |
| **Detection** | Custom metric on grade amendment conflict rate. AuditLog analysis showing overlapping timestamps on same record. |
| **Mitigation / Recovery** | (1) Grade model uses `version` integer field (optimistic locking). (2) Amendment endpoint checks `If-Match: "version_N"` header; responds 409 CONFLICT if version mismatch. (3) Conflicting user receives error with current state and must re-fetch before retrying. (4) Both amendment attempts are logged in AuditLog for compliance review. |
| **Prevention** | Grade amendment requires HOD approval, making concurrent edits from different actors uncommon. Database-level row locking (`SELECT FOR UPDATE`) on grade records during amendment workflow. |

---

## EC-ACAD-003 — Prerequisites Verified but Not Actually Completed

| Field | Detail |
|---|---|
| **Failure Mode** | A student's prerequisite course is marked PASSED in one semester, but the grade is later amended to FAILED due to an error correction. The student is now enrolled in an advanced course without having truly met the prerequisite. |
| **Impact** | Student is in an advanced course without foundational knowledge. May fail. Academic integrity concern. |
| **Detection** | Nightly batch job re-validates all active enrollments against current published grades. Flags mismatches. |
| **Mitigation / Recovery** | (1) Nightly job generates `enrollment_validity_report` and alerts the registrar. (2) Registrar may force-drop the enrollment or grant a waiver with documented approval. (3) Student is notified and given an opportunity to appeal. |
| **Prevention** | Prerequisite check re-executed after any grade amendment that affects a course used as a prerequisite. Registrar notified immediately of any grade change that may invalidate downstream enrollments. |

---

## EC-ACAD-004 — Timetable Conflict After Faculty Reassignment

| Field | Detail |
|---|---|
| **Failure Mode** | Faculty A is assigned to Section X (Monday 9–10 AM). Admin later assigns Faculty A to Section Y, which overlaps the same timeslot. The system allows the second assignment without checking the full teaching schedule. |
| **Impact** | Faculty A is double-booked. One section will have no instructor. Students discover the conflict only when class starts. |
| **Detection** | `TeachingLoadChecker.check_schedule_conflict(faculty_id, timeslots)` runs synchronously on every section update. |
| **Mitigation / Recovery** | (1) API returns 422 `SCHEDULE_CONFLICT` with details of the conflicting sections. (2) Admin must resolve by reassigning one section to another faculty member. (3) If discovered post-deployment, registrar generates a conflict report and resolves within 24 hours. |
| **Prevention** | Timetable generation algorithm incorporates faculty availability as a hard constraint. Integration tests cover reassignment scenarios. |

---

## EC-ACAD-005 — Attendance Record Submitted Twice for Same Session

| Field | Detail |
|---|---|
| **Failure Mode** | Faculty submits attendance for a session. The network request times out on the client side. Faculty clicks "Submit" again, creating a duplicate attendance session. |
| **Impact** | Attendance percentages are doubled. Students appear present twice. Threshold calculations are skewed. |
| **Detection** | Database UNIQUE constraint on `(section_id, date, session_type)`. API returns 409 CONFLICT on duplicate. |
| **Mitigation / Recovery** | (1) 409 CONFLICT response includes `session_id` of the existing session and a link to edit it. (2) Faculty can correct or amend the existing session rather than creating a duplicate. |
| **Prevention** | POST endpoint uses idempotency key `Idempotency-Key: hash(faculty_id + section_id + date + session_type)`. Subsequent requests with the same key return the original response. |

---

## EC-ACAD-006 — GPA Calculation Triggered on Partial Grade Publish

| Field | Detail |
|---|---|
| **Failure Mode** | Faculty publishes grades for only some students in a section (e.g., 20 of 40 students), and the GPA recalculation runs immediately, computing an incomplete semester GPA for affected students. |
| **Impact** | Incomplete GPA is stored and visible to students and parents. May trigger erroneous academic standing alerts (probation, scholarship loss). |
| **Detection** | GPA Engine checks `published_grades_count / total_enrolled` ratio before persisting results. |
| **Mitigation / Recovery** | (1) GPA Engine marks record as `PROVISIONAL` if any section in the semester has incomplete grades. (2) Provisional GPA is visible only to admin/registrar, not students. (3) Final GPA computed and published only when all grade windows for the semester are closed. |
| **Prevention** | Grade publishing UI shows warning if the publish action will result in partial grades for the section. Registrar configures a "GPA calculation date" for each semester, preventing premature finalisation. |

---

## EC-ACAD-007 — Course Withdrawal After Census Date

| Field | Detail |
|---|---|
| **Failure Mode** | Student attempts to withdraw from a course after the official census date (the deadline after which a W grade is recorded). The system is configured incorrectly and allows withdrawal without assigning the W grade. |
| **Impact** | No W grade on transcript. Tuition refund policy may be incorrectly applied. Enrollment counts for the course are understated. Accreditation audit may flag irregular records. |
| **Detection** | Enrollment service checks calendar event `CENSUS_DATE` and selects workflow accordingly: DROPPED (before census) vs WITHDRAWN with W grade (after census). |
| **Mitigation / Recovery** | (1) If incorrect withdrawal detected post-semester, registrar corrects transcript with W grade and adds AuditLog entry. (2) Finance team reviews refund eligibility retroactively. |
| **Prevention** | Academic calendar `CENSUS_DATE` event is a required event type. Enrollment service raises a `CalendarEventMissing` error during semester setup validation if it is absent. End-to-end tests cover both pre- and post-census withdrawal paths. |

---

## EC-ACAD-008 — Section Closure with Active Enrollments

| Field | Detail |
|---|---|
| **Failure Mode** | Admin deactivates a CourseSection (due to faculty unavailability) that still has active student enrollments. |
| **Impact** | Students are left enrolled in a non-functional section. They cannot attend classes, submit assignments, or sit exams. |
| **Detection** | Section deactivation endpoint checks `Enrollment.objects.filter(section=section, status=ACTIVE).exists()`. |
| **Mitigation / Recovery** | (1) API returns 422 `SECTION_HAS_ACTIVE_ENROLLMENTS` with count. (2) Admin must first migrate enrollments to another section or bulk-drop them with student notification before deactivating. (3) Emergency deactivation override available to SUPER_ADMIN with mandatory reason code and AuditLog entry. |
| **Prevention** | Section deactivation workflow requires a mandatory replacement-section ID or a confirmed bulk-drop acknowledgement. Automated tests cover the soft-delete path. |

---

## EC-ACAD-009 — Duplicate Exam Scheduling for Same Section

| Field | Detail |
|---|---|
| **Failure Mode** | Exam officer creates two MIDTERM exams for the same section in the same semester (e.g., due to manual data entry error or double click). |
| **Impact** | Students see two conflicting midterm entries. Faculty receives two grade submission windows. GPA engine processes double grade entries. |
| **Detection** | Database UNIQUE constraint on `(section_id, exam_type, semester_id)` for terminal exams (MIDTERM, FINAL). API returns 409 CONFLICT. |
| **Mitigation / Recovery** | (1) 409 CONFLICT response includes `exam_id` of the existing exam. (2) Operator reviews and cancels the duplicate via admin panel. (3) Cancellation triggers student notification if admit cards were already issued. |
| **Prevention** | Exam creation UI shows existing exams for the selected section and exam type before allowing submission. |

---

## EC-ACAD-010 — Academic Calendar Event Overlap

| Field | Detail |
|---|---|
| **Failure Mode** | Two academic calendar events of incompatible types overlap (e.g., `EXAM_PERIOD` and `SEMESTER_BREAK` overlap; or two `REGISTRATION_WINDOW` events for the same program in the same year overlap). |
| **Impact** | Enrollment service applies incorrect registration window. Exam scheduling allows exams during a semester break. Fee deadline calculations produce wrong dates. |
| **Detection** | Calendar event creation and update endpoints run `CalendarOverlapChecker.check(event_type, start_date, end_date, program_id)` synchronously. |
| **Mitigation / Recovery** | (1) API returns 409 `EVENT_OVERLAP` with the conflicting event ID. (2) Admin must adjust dates before the new event can be saved. (3) If an overlap is discovered in a live semester, the registrar resolves by extending or truncating one event and broadcasting an announcement. |
| **Prevention** | Acceptance tests validate the academic calendar for every combination of conflicting event types. A calendar-validation job runs nightly and alerts the registrar of any detected overlaps. |

---

## Operational Policy Addendum

### Academic Integrity Policies
All grade amendments require dual approval (faculty + HOD) and are permanently logged in the AuditLog with old/new values, actor ID, IP address, and reason code. No grade may be amended more than 60 days after the semester end date without SUPER_ADMIN override. Every override triggers an automated notification to the Academic Standards Committee.

### Student Data Privacy Policies
Attendance records, grade records, and GPA data are classified as Sensitive Personal Data under PDPA and FERPA. Access is role-gated: PARENT role can only view data for linked students who have granted explicit, revocable consent. Faculty can only query grade data within their assigned sections. All access is audited. Data is never included in aggregate analytics without pseudonymisation.

### Fee Collection Policies
Academic holds (blocking enrollment) are applied only for overdue invoices beyond the grace period (7 calendar days after due date). A hold cannot be applied during an active `EXAM_PERIOD` calendar event. Removing a hold requires full payment or an approved payment plan, documented by FINANCE_STAFF.

### System Availability During Academic Calendar
The EMIS platform is classified as Mission-Critical during the following calendar events: `REGISTRATION_WINDOW`, `EXAM_PERIOD`, `GRADE_SUBMISSION_WINDOW`, and `MERIT_LIST_DATE`. During these periods, no planned maintenance windows are scheduled. Emergency maintenance requires explicit sign-off from the Registrar and CTO.
