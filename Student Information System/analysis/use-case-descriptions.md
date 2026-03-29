# Use Case Descriptions

## Overview
Detailed descriptions for the primary use cases in the Student Information System.

---

## UC-01: Enroll in Course

| Field | Detail |
|-------|--------|
| **Use Case ID** | UC-01 |
| **Use Case Name** | Enroll in Course |
| **Actor** | Student |
| **Preconditions** | Student is authenticated; enrollment window is open |
| **Postconditions** | Student is enrolled in the course; seat count decremented |
| **Trigger** | Student selects a course and clicks "Enroll" |

### Main Flow
1. Student browses the course catalog
2. Student selects a desired course section
3. System checks enrollment window status
4. System validates student's prerequisites
5. System checks seat availability
6. System creates enrollment record
7. System decrements available seat count
8. System sends enrollment confirmation email
9. System updates student's timetable

### Alternative Flows
- **4a. Prerequisites Not Met**: System displays missing prerequisites; enrollment blocked
- **5a. Course Full**: System offers waitlist option; student joins waitlist
- **3a. Window Closed**: System displays registration window dates; enrollment blocked

### Exception Flows
- **System Unavailable**: Display maintenance message; enrollment not processed

---

## UC-02: Record Grades

| Field | Detail |
|-------|--------|
| **Use Case ID** | UC-02 |
| **Use Case Name** | Record Grades |
| **Actor** | Faculty |
| **Preconditions** | Faculty is authenticated; grade entry window is open |
| **Postconditions** | Grades saved in system; GPA recalculated |
| **Trigger** | Faculty opens grade entry for a course |

### Main Flow
1. Faculty navigates to their course roster
2. Faculty selects "Enter Grades" for the course
3. System displays the student list with grade entry fields
4. Faculty enters grades for each student
5. Faculty saves draft grades
6. Faculty reviews and submits final grades
7. System validates grade format and completeness
8. System saves grades and triggers GPA recalculation
9. System notifies students of grade publication

### Alternative Flows
- **4a. Bulk Import**: Faculty uploads CSV file with student IDs and grades
- **6a. Incomplete Grades**: System warns about missing entries before submission
- **5a. Save Draft**: System saves partial grades without publishing

### Exception Flows
- **7a. Validation Error**: System highlights invalid grade entries; faculty corrects them

---

## UC-03: Mark Attendance

| Field | Detail |
|-------|--------|
| **Use Case ID** | UC-03 |
| **Use Case Name** | Mark Attendance |
| **Actor** | Faculty |
| **Preconditions** | Faculty is authenticated; class session exists for today |
| **Postconditions** | Attendance recorded; low-attendance alerts sent if threshold breached |
| **Trigger** | Faculty opens attendance marking for a class session |

### Main Flow
1. Faculty selects course and session date
2. System displays enrolled student list
3. Faculty marks each student as Present, Absent, or Late
4. System saves attendance records
5. System calculates updated attendance percentage per student
6. System checks against minimum attendance threshold (75%)
7. System sends alerts for students below threshold
8. System updates parent/guardian if alert triggered

### Alternative Flows
- **3a. QR Code Mode**: Students scan QR code to self-mark; faculty reviews and confirms
- **3b. Biometric Integration**: System reads biometric data for automated attendance

---

## UC-04: Pay Fees

| Field | Detail |
|-------|--------|
| **Use Case ID** | UC-04 |
| **Use Case Name** | Pay Fees |
| **Actor** | Student |
| **Preconditions** | Student is authenticated; fee invoice exists for current semester |
| **Postconditions** | Payment recorded; receipt generated; invoice marked paid |
| **Trigger** | Student navigates to fee payment section |

### Main Flow
1. Student views outstanding fee invoice
2. Student selects "Pay Now"
3. System displays payment amount and breakdown
4. Student selects payment method (card, net banking, UPI)
5. System redirects to payment gateway
6. Student completes payment on gateway
7. Payment gateway sends callback to system
8. System verifies payment status
9. System updates invoice to "Paid"
10. System generates payment receipt
11. System sends confirmation email and SMS to student

### Alternative Flows
- **4a. Installment Plan**: Student selects partial payment; system applies to plan
- **7a. Payment Failed**: System displays failure reason; student retries

---

## UC-05: Issue Transcript

| Field | Detail |
|-------|--------|
| **Use Case ID** | UC-05 |
| **Use Case Name** | Issue Transcript |
| **Actor** | Registrar, Student |
| **Preconditions** | Student has completed at least one semester; all grades are published |
| **Postconditions** | Official transcript generated and delivered |
| **Trigger** | Student submits transcript request |

### Main Flow
1. Student submits transcript request with purpose and delivery method
2. System checks for any holds (fee dues, grade locks)
3. System queues the request for registrar review
4. Registrar reviews student record completeness
5. Registrar approves the transcript request
6. System generates PDF transcript with all academic records
7. System applies registrar's digital signature
8. System delivers transcript via selected method (download/email)
9. System logs the transcript issuance in student record

### Alternative Flows
- **2a. Account Hold**: System notifies student of hold; transcript blocked until resolved
- **8a. Physical Copy**: System queues for physical printing and postal delivery

---

## UC-06: Process Degree Audit

| Field | Detail |
|-------|--------|
| **Use Case ID** | UC-06 |
| **Use Case Name** | Process Degree Audit |
| **Actor** | Student, Academic Advisor |
| **Preconditions** | Student is enrolled in a degree program |
| **Postconditions** | Degree audit report generated showing progress toward graduation |
| **Trigger** | Student or advisor requests degree audit |

### Main Flow
1. Student or advisor navigates to degree audit
2. System retrieves student's degree program requirements
3. System maps completed courses to degree requirements
4. System identifies fulfilled and unfulfilled requirements
5. System calculates remaining credit hours
6. System projects estimated graduation date
7. System generates degree audit report
8. Student and advisor can view and download the report

---

## UC-07: Apply for Financial Aid

| Field | Detail |
|-------|--------|
| **Use Case ID** | UC-07 |
| **Use Case Name** | Apply for Financial Aid |
| **Actor** | Student, Admin |
| **Preconditions** | Student is authenticated; financial aid window is open |
| **Postconditions** | Aid application submitted; student notified of status |
| **Trigger** | Student selects "Apply for Financial Aid" |

### Main Flow
1. Student opens financial aid application
2. System displays available aid programs with eligibility criteria
3. Student selects applicable aid type
4. Student fills in financial details and uploads supporting documents
5. Student submits application
6. System assigns application to admin review queue
7. Admin reviews application and documents
8. Admin approves or rejects with comments
9. System notifies student of decision
10. System applies approved aid to student fee account

---

## UC-08: Publish Grades

| Field | Detail |
|-------|--------|
| **Use Case ID** | UC-08 |
| **Use Case Name** | Publish Grades |
| **Actor** | Registrar |
| **Preconditions** | Faculty has submitted grades; grade review period is complete |
| **Postconditions** | Grades published; students and parents notified |
| **Trigger** | Registrar initiates grade publication for the semester |

### Main Flow
1. Registrar opens grade review dashboard
2. System displays courses with submitted grades
3. Registrar verifies completeness and validity of all grades
4. Registrar approves grades for publication
5. System marks grades as published
6. System calculates semester GPA and updates CGPA
7. System updates academic standing for all students
8. System sends grade publication notifications to students and parents
9. System makes grades visible in student portals

## Implementation-Ready Addendum for Use Case Descriptions

### Purpose in This Artifact
Adds preconditions, postconditions, alternate flows, and exception handling.

### Scope Focus
- Extended use-case detail
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

