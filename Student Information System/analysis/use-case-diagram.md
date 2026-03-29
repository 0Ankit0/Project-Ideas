# Use Case Diagram

## Overview
This document contains use case diagrams for all major actors in the Student Information System.

---

## Complete System Use Case Diagram

```mermaid
graph TB
    subgraph Actors
        Student((Student))
        Faculty((Faculty))
        Advisor((Academic Advisor))
        Admin((Admin Staff))
        Registrar((Registrar))
        Parent((Parent/Guardian))
        PaymentGW((Payment Gateway))
        SMSProvider((SMS Provider))
        EmailProvider((Email Provider))
    end

    subgraph "Student Information System"
        UC1[Browse Course Catalog]
        UC2[Enroll in Courses]
        UC3[View Grades]
        UC4[View Attendance]
        UC5[Pay Fees]
        UC6[Download Transcript]
        UC7[View Timetable]
        UC8[Manage Profile]

        UC10[Manage Course Content]
        UC11[Record Grades]
        UC12[Mark Attendance]
        UC13[View Student Reports]
        UC14[Send Announcements]

        UC20[View Student Progress]
        UC21[Approve Overrides]
        UC22[Create Improvement Plans]

        UC30[Manage Users]
        UC31[Manage Courses]
        UC32[Manage Fee Structures]
        UC33[View Analytics]
        UC34[Manage Calendar]

        UC40[Publish Grades]
        UC41[Issue Transcripts]
        UC42[Manage Graduation]
    end

    Student --> UC1
    Student --> UC2
    Student --> UC3
    Student --> UC4
    Student --> UC5
    Student --> UC6
    Student --> UC7
    Student --> UC8

    Faculty --> UC10
    Faculty --> UC11
    Faculty --> UC12
    Faculty --> UC13
    Faculty --> UC14

    Advisor --> UC20
    Advisor --> UC21
    Advisor --> UC22

    Admin --> UC30
    Admin --> UC31
    Admin --> UC32
    Admin --> UC33
    Admin --> UC34

    Registrar --> UC40
    Registrar --> UC41
    Registrar --> UC42

    Parent --> UC3
    Parent --> UC4
    Parent --> UC5

    UC5 --> PaymentGW
    UC5 --> SMSProvider
    UC6 --> EmailProvider
```

---

## Student Use Cases

```mermaid
graph LR
    Student((Student))

    subgraph "Account Management"
        UC1[Register Account]
        UC2[Login/Logout]
        UC3[Manage Profile]
        UC4[Reset Password]
        UC5[Link Parent Account]
    end

    subgraph "Course Enrollment"
        UC6[Browse Course Catalog]
        UC7[View Course Details]
        UC8[Enroll in Course]
        UC9[Drop Course]
        UC10[Join Waitlist]
        UC11[View My Enrollments]
    end

    subgraph "Academics"
        UC12[View Grades]
        UC13[View CGPA]
        UC14[View Degree Audit]
        UC15[Download Transcript]
        UC16[View Exam Schedule]
        UC17[View Hall Ticket]
    end

    subgraph "Attendance"
        UC18[View Attendance Records]
        UC19[Apply for Leave]
        UC20[Track Leave Status]
    end

    subgraph "Fee Management"
        UC21[View Fee Invoice]
        UC22[Pay Fees Online]
        UC23[View Payment History]
        UC24[Download Receipt]
        UC25[Apply for Financial Aid]
    end

    subgraph "Communication"
        UC26[View Announcements]
        UC27[Message Faculty]
        UC28[Manage Notification Preferences]
    end

    Student --> UC1
    Student --> UC2
    Student --> UC3
    Student --> UC4
    Student --> UC5
    Student --> UC6
    Student --> UC7
    Student --> UC8
    Student --> UC9
    Student --> UC10
    Student --> UC11
    Student --> UC12
    Student --> UC13
    Student --> UC14
    Student --> UC15
    Student --> UC16
    Student --> UC17
    Student --> UC18
    Student --> UC19
    Student --> UC20
    Student --> UC21
    Student --> UC22
    Student --> UC23
    Student --> UC24
    Student --> UC25
    Student --> UC26
    Student --> UC27
    Student --> UC28
```

---

## Faculty Use Cases

```mermaid
graph LR
    Faculty((Faculty))

    subgraph "Profile & Schedule"
        UC1[Manage Faculty Profile]
        UC2[View Teaching Schedule]
        UC3[View Course Roster]
        UC4[Set Office Hours]
    end

    subgraph "Course Management"
        UC5[View Assigned Courses]
        UC6[Upload Course Materials]
        UC7[Manage Course Content]
        UC8[View Syllabus]
    end

    subgraph "Grade Management"
        UC9[Enter Student Grades]
        UC10[Bulk Import Grades]
        UC11[Submit Final Grades]
        UC12[Request Grade Amendment]
        UC13[View Grade Distribution]
    end

    subgraph "Attendance Management"
        UC14[Mark Class Attendance]
        UC15[View Attendance Summary]
        UC16[Generate Attendance Report]
        UC17[Review Leave Requests]
    end

    subgraph "Communication"
        UC18[Post Announcement]
        UC19[Reply to Student Messages]
        UC20[Send Course Notifications]
    end

    subgraph "Reports"
        UC21[View Student Performance]
        UC22[View Course Analytics]
        UC23[Export Reports]
    end

    Faculty --> UC1
    Faculty --> UC2
    Faculty --> UC3
    Faculty --> UC4
    Faculty --> UC5
    Faculty --> UC6
    Faculty --> UC7
    Faculty --> UC8
    Faculty --> UC9
    Faculty --> UC10
    Faculty --> UC11
    Faculty --> UC12
    Faculty --> UC13
    Faculty --> UC14
    Faculty --> UC15
    Faculty --> UC16
    Faculty --> UC17
    Faculty --> UC18
    Faculty --> UC19
    Faculty --> UC20
    Faculty --> UC21
    Faculty --> UC22
    Faculty --> UC23
```

---

## Admin Use Cases

```mermaid
graph LR
    Admin((Admin Staff))

    subgraph "User Management"
        UC1[Manage Students]
        UC2[Manage Faculty]
        UC3[Manage Admin Roles]
        UC4[Handle Account Issues]
    end

    subgraph "Academic Administration"
        UC5[Manage Course Catalog]
        UC6[Manage Departments]
        UC7[Manage Degree Programs]
        UC8[Configure Enrollment Windows]
        UC9[Manage Classroom Allocation]
    end

    subgraph "Fee Administration"
        UC10[Define Fee Structures]
        UC11[Apply Scholarships]
        UC12[View Collection Reports]
        UC13[Process Financial Aid]
        UC14[Manage Refunds]
    end

    subgraph "Academic Calendar"
        UC15[Create Academic Calendar]
        UC16[Schedule Exams]
        UC17[Manage Events]
        UC18[Publish Holiday List]
    end

    subgraph "Reporting"
        UC19[View Institution Dashboard]
        UC20[Generate Custom Reports]
        UC21[Monitor System Usage]
        UC22[Export Data]
    end

    subgraph "System Settings"
        UC23[Manage System Configuration]
        UC24[View Audit Logs]
        UC25[Manage Integrations]
        UC26[Backup & Restore]
    end

    Admin --> UC1
    Admin --> UC2
    Admin --> UC3
    Admin --> UC4
    Admin --> UC5
    Admin --> UC6
    Admin --> UC7
    Admin --> UC8
    Admin --> UC9
    Admin --> UC10
    Admin --> UC11
    Admin --> UC12
    Admin --> UC13
    Admin --> UC14
    Admin --> UC15
    Admin --> UC16
    Admin --> UC17
    Admin --> UC18
    Admin --> UC19
    Admin --> UC20
    Admin --> UC21
    Admin --> UC22
    Admin --> UC23
    Admin --> UC24
    Admin --> UC25
    Admin --> UC26
```

---

## Registrar Use Cases

```mermaid
graph LR
    Registrar((Registrar))

    subgraph "Grade Management"
        UC1[Review Submitted Grades]
        UC2[Publish Final Grades]
        UC3[Approve Grade Amendments]
        UC4[Lock Grade Records]
    end

    subgraph "Transcript Management"
        UC5[Process Transcript Requests]
        UC6[Issue Official Transcripts]
        UC7[Digitally Sign Transcripts]
        UC8[Manage Transcript Delivery]
    end

    subgraph "Enrollment Oversight"
        UC9[View Enrollment Statistics]
        UC10[Override Enrollment Rules]
        UC11[Manage Enrollment Deadlines]
    end

    subgraph "Graduation"
        UC12[Process Graduation Applications]
        UC13[Verify Degree Completion]
        UC14[Manage Graduation Clearance]
        UC15[Generate Graduation List]
    end

    subgraph "Records"
        UC16[Manage Student Records]
        UC17[Archive Historical Records]
        UC18[Respond to Verification Requests]
    end

    Registrar --> UC1
    Registrar --> UC2
    Registrar --> UC3
    Registrar --> UC4
    Registrar --> UC5
    Registrar --> UC6
    Registrar --> UC7
    Registrar --> UC8
    Registrar --> UC9
    Registrar --> UC10
    Registrar --> UC11
    Registrar --> UC12
    Registrar --> UC13
    Registrar --> UC14
    Registrar --> UC15
    Registrar --> UC16
    Registrar --> UC17
    Registrar --> UC18
```

---

## Use Case Relationships

```mermaid
graph TB
    subgraph "Include Relationships"
        Enroll[Enroll in Course] -->|includes| CheckPrerequisites[Check Prerequisites]
        Enroll -->|includes| CheckSeatAvailability[Check Seat Availability]
        Enroll -->|includes| UpdateEnrollmentRecord[Update Enrollment Record]

        PayFees[Pay Fees] -->|includes| GenerateInvoice[Generate Invoice]
        PayFees -->|includes| ProcessPayment[Process via Gateway]

        IssueTranscript[Issue Transcript] -->|includes| VerifyGrades[Verify All Grades]
        IssueTranscript -->|includes| ApplyDigitalSignature[Apply Digital Signature]
    end

    subgraph "Extend Relationships"
        ViewGrades[View Grades] -.->|extends| DownloadGradeCard[Download Grade Card]
        ViewGrades -.->|extends| ViewGPABreakdown[View GPA Breakdown]

        MarkAttendance[Mark Attendance] -.->|extends| SendLowAttendanceAlert[Send Low Attendance Alert]
        MarkAttendance -.->|extends| BlockFromExam[Block from Exam]

        EnrollCourse[Enroll Course] -.->|extends| JoinWaitlist[Join Waitlist]
    end
```

## Implementation-Ready Addendum for Use Case Diagram

### Purpose in This Artifact
Maps each actor to constrained actions and approval boundaries.

### Scope Focus
- Use-case responsibility expansion
- Enrollment lifecycle enforcement relevant to this artifact
- Grading/transcript consistency constraints relevant to this artifact
- Role-based and integration concerns at this layer

### Supplemental Mermaid (Artifact-Specific)
```mermaid
graph TD
    Student-->Enroll
    Faculty-->SubmitGrades
    Advisor-->ApprovePetitions
    Registrar-->FinalizeCorrections
    Integrations-->SyncEvents
```

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

