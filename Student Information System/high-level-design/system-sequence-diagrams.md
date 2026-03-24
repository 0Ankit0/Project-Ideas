# System Sequence Diagrams

## Overview
System-level sequence diagrams showing black-box interactions between actors and the Student Information System for key business scenarios.

---

## Course Enrollment Sequence

```mermaid
sequenceDiagram
    actor Student
    participant SIS as Student Information System
    participant PayGW as Payment Gateway

    Student->>SIS: Browse course catalog
    SIS-->>Student: Return available courses

    Student->>SIS: Select course and request enrollment
    SIS-->>SIS: Validate prerequisites, check seats, detect conflicts
    SIS-->>Student: Confirm enrollment and updated timetable
    SIS-->>Student: Send enrollment confirmation email
```

---

## Grade Submission and Publication Sequence

```mermaid
sequenceDiagram
    actor Faculty
    actor Registrar
    participant SIS as Student Information System
    actor Student
    actor Parent

    Faculty->>SIS: Submit final grades for course
    SIS-->>Faculty: Acknowledge submission
    SIS-->>Registrar: Notify grades pending review

    Registrar->>SIS: Review and approve grades
    SIS-->>SIS: Calculate GPA and CGPA
    SIS-->>SIS: Update academic standing
    SIS-->>Student: Notify grade publication
    SIS-->>Parent: Send grade notification
    SIS-->>Faculty: Confirm grades published
```

---

## Fee Payment Sequence

```mermaid
sequenceDiagram
    actor Student
    participant SIS as Student Information System
    participant PayGW as Payment Gateway

    Student->>SIS: View outstanding fee invoice
    SIS-->>Student: Return invoice details

    Student->>SIS: Initiate payment
    SIS->>PayGW: Create payment session
    PayGW-->>SIS: Return payment URL
    SIS-->>Student: Redirect to payment gateway

    Student->>PayGW: Complete payment
    PayGW->>SIS: Send payment callback
    SIS-->>SIS: Verify and record payment
    SIS-->>SIS: Update invoice status to Paid
    SIS-->>Student: Send receipt via email and SMS
```

---

## Attendance Alert Sequence

```mermaid
sequenceDiagram
    actor Faculty
    participant SIS as Student Information System
    actor Student
    actor Parent
    actor Advisor as Academic Advisor

    Faculty->>SIS: Mark class attendance
    SIS-->>SIS: Calculate attendance percentage

    alt Attendance below warning threshold
        SIS-->>Student: Send attendance warning
        SIS-->>Parent: Send parent alert
    end

    alt Attendance below critical threshold
        SIS-->>Student: Send critical alert
        SIS-->>Advisor: Notify advisor
        SIS-->>Parent: Send urgent alert
    end
```

---

## Transcript Request Sequence

```mermaid
sequenceDiagram
    actor Student
    participant SIS as Student Information System
    actor Registrar

    Student->>SIS: Submit transcript request
    SIS-->>SIS: Check for active account holds

    alt Account has holds
        SIS-->>Student: Notify of holds
    else No holds
        SIS-->>Registrar: Queue transcript request
        Registrar->>SIS: Review and approve request
        SIS-->>SIS: Generate PDF with digital signature
        SIS-->>Student: Deliver transcript (download/email)
        SIS-->>Student: Send delivery confirmation
    end
```

---

## Student Admission Sequence

```mermaid
sequenceDiagram
    actor Applicant
    participant SIS as Student Information System
    actor Admin
    actor Advisor as Academic Advisor

    Applicant->>SIS: Submit admission application
    SIS-->>Admin: Notify new application

    Admin->>SIS: Review and approve application
    SIS-->>Applicant: Send admission offer

    Applicant->>SIS: Accept offer and pay confirmation fee
    SIS-->>SIS: Create student account and assign ID
    SIS-->>Advisor: Assign student to advisor
    SIS-->>Applicant: Send login credentials
    SIS-->>Applicant: Open enrollment window notification
```

---

## Exam Schedule and Hall Ticket Sequence

```mermaid
sequenceDiagram
    actor Admin
    participant SIS as Student Information System
    actor Student
    actor Faculty

    Admin->>SIS: Create and publish exam schedule
    SIS-->>SIS: Check for conflicts and allocate halls
    SIS-->>Student: Send exam schedule notification
    SIS-->>Faculty: Send invigilation duty notification

    Student->>SIS: Request hall ticket
    SIS-->>SIS: Validate attendance eligibility

    alt Not Eligible
        SIS-->>Student: Notify attendance debarment
    else Eligible
        SIS-->>Student: Generate and deliver hall ticket
    end
```
