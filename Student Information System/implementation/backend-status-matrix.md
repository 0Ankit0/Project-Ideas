# Backend Status Matrix

## Overview
This matrix tracks the implementation status of all key SIS backend capabilities across domain modules.

---

## Authentication and Identity Module

| Feature | Status | Notes |
|---------|--------|-------|
| JWT authentication | ✅ Implemented | Access and refresh token flow |
| SSO / LDAP integration | ✅ Implemented | Institutional login support |
| OTP enable/verify/disable | ✅ Implemented | For admin and registrar accounts |
| Role-based access control | ✅ Implemented | Student, Faculty, Admin, Registrar, Advisor, Parent |
| Password reset via email | ✅ Implemented | Expiring reset link |
| Parent account linking | ✅ Implemented | Requires student approval |

---

## Student Management Module

| Feature | Status | Notes |
|---------|--------|-------|
| Student registration and profile | ✅ Implemented | Includes document upload |
| Student status lifecycle | ✅ Implemented | Applicant → Active → Graduated/Withdrawn |
| Academic advisor assignment | ✅ Implemented | Admin assigns advisor during onboarding |
| Parent/guardian portal | ✅ Implemented | Read-only access to grades, attendance, fees |
| Student search and filtering | ✅ Implemented | Admin and advisor access |

---

## Course and Curriculum Module

| Feature | Status | Notes |
|---------|--------|-------|
| Course catalog management | ✅ Implemented | Admin CRUD with department and level |
| Prerequisite configuration | ✅ Implemented | Multi-level prerequisite chains supported |
| Department and program management | ✅ Implemented | Department head assignment included |
| Degree program requirements | ✅ Implemented | Mandatory and elective requirement types |
| Course section scheduling | ✅ Implemented | Semester-year based sections with room and schedule |
| Syllabus upload | ✅ Implemented | Stored in object storage |

---

## Enrollment Module

| Feature | Status | Notes |
|---------|--------|-------|
| Enrollment window management | ✅ Implemented | Admin-controlled open/close with drop deadline |
| Prerequisite validation at enrollment | ✅ Implemented | Blocks enrollment if prerequisites not met |
| Seat availability check | ✅ Implemented | Real-time seat count management |
| Schedule conflict detection | ✅ Implemented | Detects overlapping section schedules |
| Course drop within deadline | ✅ Implemented | Within enrollment window drop period |
| Waitlist management | ✅ Implemented | Auto-promotion on seat availability |
| Waitlist notifications | ✅ Implemented | Position updates and auto-enrollment alerts |
| Enrollment override by advisor | ✅ Implemented | Advisor-approved exception handling |

---

## Grades and Academic Records Module

| Feature | Status | Notes |
|---------|--------|-------|
| Grade entry by faculty | ✅ Implemented | Manual and bulk CSV import |
| Draft and final grade submission | ✅ Implemented | Faculty saves draft before submitting |
| Registrar grade review and publish | ✅ Implemented | Approval workflow with return-for-correction |
| GPA and CGPA calculation | ✅ Implemented | Recalculated on each grade publication |
| Academic standing classification | ✅ Implemented | Good Standing / Warning / Probation / Suspended |
| Grade amendment workflow | ✅ Implemented | Faculty request + registrar approval |
| Degree audit generation | ✅ Implemented | Maps completed courses to program requirements |
| Transcript request and generation | ✅ Implemented | PDF with digital signature |
| Transcript delivery (download/email) | ✅ Implemented | Secure link with expiry |

---

## Attendance Module

| Feature | Status | Notes |
|---------|--------|-------|
| Session creation and attendance marking | ✅ Implemented | Per class session with Present/Absent/Late |
| Attendance percentage calculation | ✅ Implemented | Per course per student |
| Low attendance alerts to student | ✅ Implemented | Below 80% warning and below 75% critical |
| Low attendance alerts to parent/advisor | ✅ Implemented | Triggered on critical threshold breach |
| QR code attendance | ✅ Implemented | Session-specific short-lived QR code |
| Biometric attendance integration | 🔜 Planned | External device API integration pending |
| Leave application and approval | ✅ Implemented | Faculty approval with excused absence marking |
| Exam eligibility based on attendance | ✅ Implemented | Hall ticket blocked below threshold |

---

## Fee and Financial Aid Module

| Feature | Status | Notes |
|---------|--------|-------|
| Fee structure definition | ✅ Implemented | Per program, semester, and year |
| Automated fee invoice generation | ✅ Implemented | Generated on semester start |
| Online fee payment | ✅ Implemented | Bank transfer, cards, UPI via gateway |
| Installment payment plans | ✅ Implemented | Configurable partial payment |
| Payment receipt generation | ✅ Implemented | PDF receipt stored and emailed |
| Financial aid application | ✅ Implemented | Student applies; admin reviews and approves |
| Aid disbursement to invoice | ✅ Implemented | Approved aid credited to net payable |
| Fee collection reports | ✅ Implemented | Admin dashboard with export |
| ERP / finance sync | 🔜 Planned | External finance system integration pending |

---

## Exam Management Module

| Feature | Status | Notes |
|---------|--------|-------|
| Exam schedule creation | ✅ Implemented | Admin creates per course section |
| Conflict detection for student exams | ✅ Implemented | Prevents overlapping exam assignments |
| Hall allocation and seating | ✅ Implemented | Auto-assigned hall and seat number |
| Exam schedule publication | ✅ Implemented | Triggers student and faculty notifications |
| Hall ticket generation | ✅ Implemented | PDF with eligibility check |
| Exam eligibility validation | ✅ Implemented | Blocks ineligible students from hall ticket |

---

## Communication and Notification Module

| Feature | Status | Notes |
|---------|--------|-------|
| Announcements with target groups | ✅ Implemented | Course, department, or all-college |
| Internal messaging | ✅ Implemented | Threaded messaging between users |
| Email notifications | ✅ Implemented | SES-based transactional emails |
| SMS notifications | ✅ Implemented | Critical alerts and OTP |
| Push notifications | ✅ Implemented | FCM/APNs via student mobile app |
| Websocket live updates | ✅ Implemented | Grade publication, enrollment changes, alerts |
| Notification preferences | ✅ Implemented | Student-managed channel preferences |

---

## Reports and Analytics Module

| Feature | Status | Notes |
|---------|--------|-------|
| Institution dashboard | ✅ Implemented | Enrollment, fee, and academic KPIs |
| Enrollment statistics report | ✅ Implemented | By department, program, semester |
| Grade distribution report | ✅ Implemented | Per course, section, and faculty |
| Attendance summary report | ✅ Implemented | Per course with at-risk student list |
| Fee collection report | ✅ Implemented | Paid, pending, and overdue breakdown |
| Custom report export (CSV/PDF) | ✅ Implemented | Admin and faculty export |
| Scheduled report generation | 🔜 Planned | Automated periodic report delivery |

## Implementation-Ready Addendum for Backend Status Matrix

### Purpose in This Artifact
Adds status fields for lifecycle, grading consistency, RBAC scope, contracts.

### Scope Focus
- Capability readiness matrix
- Enrollment lifecycle enforcement relevant to this artifact
- Grading/transcript consistency constraints relevant to this artifact
- Role-based and integration concerns at this layer

#### Implementation Rules
- Enrollment lifecycle operations must emit auditable events with correlation IDs and actor scope.
- Grade and transcript actions must preserve immutability through versioned records; no destructive updates.
- RBAC must be combined with context constraints (term, department, assigned section, advisee).
- External integrations must remain contract-first with explicit versioning and backward-compatibility strategy.

#### Acceptance Criteria
1. Business rules are testable and mapped to policy IDs in this artifact.
2. Failure paths (authorization, policy window, downstream sync) are explicitly documented.
3. Data ownership and source-of-truth boundaries are clearly identified.
4. Diagram and narrative remain consistent for the scenarios covered in this file.

