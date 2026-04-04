# EMIS - Data Flow Diagrams

## Overview

Data Flow Diagrams (DFD) show how data moves through the EMIS system, transforming as it flows between processes, data stores, and external entities.

## Context Level DFD (Level 0)

```mermaid
graph LR
    subgraph External_Entities["External Entities"]
        Student[Student]
        Faculty[Faculty]
        Admin[Administrator]
        Parent[Parent]
        PaymentGW[Payment Gateway]
        EmailSvc[Email Service]
    end
    
    EMIS((EMIS<br/>System))
    
    Student -->|Application Data| EMIS
    Student -->|Course Registration| EMIS
    Student -->|Assignment Submission| EMIS
    Student -->|Fee Payment Request| EMIS
    
    EMIS -->|Acceptance/Rejection| Student
    EMIS -->|Course Schedule| Student
   EMIS -->|Grades & Transcript| Student
    EMIS -->|Payment Receipt| Student
    
    Faculty -->|Course Content| EMIS
    Faculty -->|Attendance Data| EMIS
    Faculty -->|Grades| EMIS
    
    EMIS -->|Student List| Faculty
    EMIS -->|Teaching Schedule| Faculty
    
    Admin -->|System Configuration| EMIS
    Admin -->|User Management| EMIS
    
    EMIS -->|Reports & Analytics| Admin
    EMIS -->|System Status| Admin
    
    Parent -->|Fee Payment| EMIS
    EMIS -->|Student Progress Report| Parent
    EMIS -->|Notifications| Parent
    
    EMIS -->|Payment Request| PaymentGW
    PaymentGW -->|Payment Confirmation| EMIS
    
    EMIS -->|Email/SMS| EmailSvc
    
    style EMIS fill:#2C3E50,color:#fff
    style Student fill:#4A90E2,color:#fff
    style Faculty fill:#7B68EE,color:#fff
    style Admin fill:#E74C3C,color:#fff
    style Parent fill:#F39C12,color:#fff
    style PaymentGW fill:#27AE60,color:#fff
    style EmailSvc fill:#95A5A6,color:#fff
```

## Level 1 DFD - Major Processes

```mermaid
graph TB
    subgraph External["External Entities"]
        Student[Student]
        Faculty[Faculty]
        Admin[Admin]
        Parent[Parent]
        PaymentGW[Payment Gateway]
    end
    
    subgraph Processes["Core Processes"]
        P1[1.0<br/>User Authentication<br/>& Authorization]
        P2[2.0<br/>Admission<br/>Processing]
        P3[3.0<br/>Course<br/>Management]
        P4[4.0<br/>Enrollment<br/>Processing]
        P5[5.0<br/>Learning<br/>Management]
        P6[6.0<br/>Assessment<br/>& Grading]
        P7[7.0<br/>Fee<br/>Management]
        P8[8.0<br/>Payment<br/>Processing]
        P9[9.0<br/>Reporting<br/>& Analytics]
        P10[10.0<br/>Notification<br/>Service]
    end
    
    subgraph DataStores["Data Stores"]
        DS1[(D1: Users)]
        DS2[(D2: Students)]
        DS3[(D3: Courses)]
        DS4[(D4: Enrollments)]
        DS5[(D5: Grades)]
        DS6[(D6: Payments)]
        DS7[(D7: Content)]
        DS8[(D8: Notifications)]
    end
    
    Student -->|Login Credentials| P1
    Faculty -->|Login Credentials| P1
    Admin -->|Login Credentials| P1
    Parent -->|Login Credentials| P1
    
    P1 -->|Auth Token| Student
    P1 -->|Auth Token| Faculty
    P1 <-->|User Data| DS1
    
    Student -->|Application| P2
    P2 -->|Admission Decision| Student
    P2 <-->|Applicant Data| DS2
    
    Admin -->|Course Definition| P3
    P3 <-->|Course Data| DS3
    P3 -->|Course Catalog| Student
    
    Student -->|Registration Request| P4
    P4 -->|Enrollment Confirmation| Student
    P4 <-->|Enrollment Data| DS4
    P4 -->|Course Data| DS3
    
    Faculty -->|Course Content| P5
    Student -->|Assignment Submission| P5
    P5 <-->|Content & Submissions| DS7
    P5 -->|Learning Materials| Student
    
    Faculty -->|Grades| P6
    P6 <-->|Grade Data| DS5
    P6 -->|Enrollment Data| DS4
    P6 -->|Transcript| Student
    
    Admin -->|Fee Structure| P7
    P7 <-->|Fee Data| DS6
    P7 -->|Fee Statement| Student
    P7 -->|Fee Statement| Parent
    
    Student -->|Payment Request| P8
    Parent -->|Payment Request| P8
    P8 -->|Payment Info| PaymentGW
    PaymentGW -->|Payment Confirmation| P8
    P8 <-->|Payment Records| DS6
    P8 -->|Receipt| Student
    
    Admin -->|Report Request| P9
    P9 -->|Student Data| DS2
    P9 -->|Grade Data| DS5
    P9 -->|Payment Data| DS6
    P9 -->|Reports| Admin
    
    P2 -->|Admission Notification| P10
    P4 -->|Enrollment Notification| P10
    P6 -->|Grade Notification| P10
    P8 -->|Payment Notification| P10
    P10 <-->|Notification Queue| DS8
    P10 -->|Notifications| Student
    P10 -->|Notifications| Parent
    
    style P1 fill:#3498DB,color:#fff
    style P2 fill:#9B59B6,color:#fff
    style P3 fill:#E67E22,color:#fff
    style P4 fill:#1ABC9C,color:#fff
    style P5 fill:#E74C3C,color:#fff
    style P6 fill:#F39C12,color:#fff
    style P7 fill:#27AE60,color:#fff
    style P8 fill:#16A085,color:#fff
    style P9 fill:#D35400,color:#fff
    style P10 fill:#8E44AD,color:#fff
```

## Level 2 DFD - Course Registration Process

```mermaid
graph TB
    Student[Student]
    
    subgraph Course_Registration["Course Registration (Process 4.0)"]
        P4_1[4.1<br/>Check Fee<br/>Clearance]
        P4_2[4.2<br/>Fetch Available<br/>Courses]
        P4_3[4.3<br/>Validate<br/>Prerequisites]
        P4_4[4.4<br/>Check Course<br/>Capacity]
        P4_5[4.5<br/>Check Schedule<br/>Conflicts]
        P4_6[4.6<br/>Create<br/>Enrollments]
        P4_7[4.7<br/>Calculate<br/>Fees]
        P4_8[4.8<br/>Generate<br/>Timetable]
    end
    
    DS_Student[(D2: Students)]
    DS_Course[(D3: Courses)]
    DS_Enrollment[(D4: Enrollments)]
    DS_Payment[(D6: Payments)]
    DS_Fee[(D7: Fee Structure)]
    
    Student -->|Registration Request| P4_1
    P4_1 -->|Student ID| DS_Student
    DS_Student -->|Student Data| P4_1
    P4_1 -->|Fee Status| DS_Payment
    DS_Payment -->|Payment History| P4_1
    
    P4_1 -->|Clearance Status| P4_2
    P4_2 -->|Query Courses| DS_Course
    DS_Course -->|Course List| P4_2
    P4_2 -->|Available Courses| Student
    
    Student -->|Selected Courses| P4_3
    P4_3 -->|Check Prerequisites| DS_Course
    P4_3 -->|Student Transcript| DS_Enrollment
    
    P4_3 -->|Validated Courses| P4_4
    P4_4 -->|Check Capacity| DS_Course
    P4_4 -->|Enrollment Count| DS_Enrollment
    
    P4_4 -->|Capacity OK| P4_5
    P4_5 -->|Existing Schedule| DS_Enrollment
    P4_5 -->|New Schedule| DS_Course
    
    P4_5 -->|No Conflicts| P4_6
    P4_6 -->|Enrollment Records| DS_Enrollment
    
    P4_6 -->|Enrolled Courses| P4_7
    P4_7 -->|Fee Structure| DS_Fee
    P4_7 -->|Fee Amount| DS_Payment
    
    P4_6 -->|Enrollments| P4_8
    P4_8 -->|Course Schedules| DS_Course
    P4_8 -->|Timetable| Student
    
    P4_7 -->|Fee Invoice| Student
    
    style P4_1 fill:#3498DB,color:#fff
    style P4_2 fill:#9B59B6,color:#fff
    style P4_3 fill:#E67E22,color:#fff
    style P4_4 fill:#1ABC9C,color:#fff
    style P4_5 fill:#E74C3C,color:#fff
    style P4_6 fill:#F39C12,color:#fff
    style P4_7 fill:#27AE60,color:#fff
    style P4_8 fill:#16A085,color:#fff
```

## Level 2 DFD - Payment Processing

```mermaid
graph TB
    Student[Student]
    Parent[Parent]
    PaymentGW[Payment Gateway]
    Bank[Bank]
    
    subgraph Payment_Processing["Payment Processing (Process 8.0)"]
        P8_1[8.1<br/>Display Fee<br/>Statement]
        P8_2[8.2<br/>Initiate<br/>Payment]
        P8_3[8.3<br/>Generate<br/>Transaction ID]
        P8_4[8.4<br/>Process Gateway<br/>Response]
        P8_5[8.5<br/>Verify Payment<br/>Signature]
        P8_6[8.6<br/>Update<br/>Balance]
        P8_7[8.7<br/>Generate<br/>Receipt]
        P8_8[8.8<br/>Reconcile<br/>Payments]
    end
    
    DS_Payment[(D6: Payments)]
    DS_Student[(D2: Students)]
    DS_Account[(D9: Accounts)]
    DS_Receipt[(D10: Receipts)]
    
    Student -->|View Statement| P8_1
    Parent -->|View Statement| P8_1
    P8_1 -->|Student ID| DS_Student
    P8_1 -->|Account Balance| DS_Account
    P8_1 -->|Fee Statement| Student
    P8_1 -->|Fee Statement| Parent
    
    Student -->|Payment Amount| P8_2
    Parent -->|Payment Amount| P8_2
    P8_2 -->|Payment Details| P8_3
    
    P8_3 -->|Transaction ID| DS_Payment
    P8_3 -->|Payment Request| PaymentGW
    
    PaymentGW -->|Payment Response| P8_4
    P8_4 -->|Response Data| P8_5
    
    P8_5 -->|Verified Payment| P8_6
    P8_6 -->|Update Balance| DS_Account
    P8_6 -->|Payment Record| DS_Payment
    
    P8_6 -->|Payment Confirmed| P8_7
    P8_7 -->|Receipt Data| DS_Receipt
    P8_7 -->|Receipt PDF| Student
    P8_7 -->|Receipt PDF| Parent
    
    PaymentGW -->|Daily Settlement| Bank
    Bank -->|Bank Statement| P8_8
    P8_8 -->|Payment Records| DS_Payment
    P8_8 -->|Reconciliation Report| DS_Payment
    
    style P8_1 fill:#3498DB,color:#fff
    style P8_2 fill:#9B59B6,color:#fff
    style P8_3 fill:#E67E22,color:#fff
    style P8_4 fill:#1ABC9C,color:#fff
    style P8_5 fill:#E74C3C,color:#fff
    style P8_6 fill:#F39C12,color:#fff
    style P8_7 fill:#27AE60,color:#fff
    style P8_8 fill:#16A085,color:#fff
```

## Level 2 DFD - Grade Processing

```mermaid
graph TB
    Faculty[Faculty]
    Student[Student]
    Admin[Administrator]
    
    subgraph Grade_Processing["Assessment & Grading (Process 6.0)"]
        P6_1[6.1<br/>Fetch Student<br/>Roster]
        P6_2[6.2<br/>Enter/Upload<br/>Grades]
        P6_3[6.3<br/>Validate<br/>Grades]
        P6_4[6.4<br/>Submit<br/>Grades]
        P6_5[6.5<br/>Calculate<br/>GPA]
        P6_6[6.6<br/>Update<br/>Transcript]
        P6_7[6.7<br/>Generate<br/>Grade Reports]
    end
    
    DS_Course[(D3: Courses)]
    DS_Enrollment[(D4: Enrollments)]
    DS_Grade[(D5: Grades)]
    DS_Student[(D2: Students)]
    DS_Transcript[(D11: Transcripts)]
    
    Faculty -->|Course ID| P6_1
    P6_1 -->|Course Sections| DS_Course
    P6_1 -->|Enrolled Students| DS_Enrollment
    P6_1 -->|Student Roster| Faculty
    
    Faculty -->|Grade Data| P6_2
    P6_2 -->|Grade Sheet| P6_3
    
    P6_3 -->|Validated Grades| P6_4
    P6_4 -->|Lock Grades| DS_Grade
    P6_4 -->|Grade Records| DS_Grade
    
    P6_4 -->|Submitted Grades| P6_5
    P6_5 -->|Course Grades| DS_Grade
    P6_5 -->|Student Enrollments| DS_Enrollment
    P6_5 -->|Updated GPA| DS_Student
    
    P6_5 -->|Grade Updates| P6_6
    P6_6 -->|Transcript Data| DS_Transcript
    
    P6_6 -->|Grade Notification| Student
    
    Admin -->|Report Request| P6_7
    P6_7 -->|Grade Data| DS_Grade
    P6_7 -->|Student Data| DS_Student
    P6_7 -->|Grade Reports| Admin
    
    Student -->|Transcript Request| P6_6
    P6_6 -->|Transcript PDF| Student
    
    style P6_1 fill:#3498DB,color:#fff
    style P6_2 fill:#9B59B6,color:#fff
    style P6_3 fill:#E67E22,color:#fff
    style P6_4 fill:#1ABC9C,color:#fff
    style P6_5 fill:#E74C3C,color:#fff
    style P6_6 fill:#F39C12,color:#fff
    style P6_7 fill:#27AE60,color:#fff
```

## Graduation Application & Degree Conferral Flow

```mermaid
flowchart TD
    Student[Student] -->|Submit Graduation Application| P1[Receive Application]
    P1 -->|Store Application| DS1[(Graduation Applications)]
    P1 --> P2[Run Degree Audit]
    P2 -->|Query Transcript| DS2[(Enrollments & Grades)]
    P2 -->|Store Audit Result| DS3[(Degree Audit Records)]
    P2 --> C1{Credits Complete?}
    C1 -->|No| P3[Mark Ineligible]
    C1 -->|Yes| C2{GPA Meets Threshold?}
    C2 -->|No| P3
    C2 -->|Yes| C3{Any Holds or Pending Grades?}
    C3 -->|Yes| P3
    P3 -->|Deficiency Report| P4[Notify Student: Ineligible]
    P4 --> Student
    C3 -->|No| P5[Mark Eligible & Approve]
    P5 -->|Update Status| DS1
    P5 --> P6[Generate Diploma Record]
    P6 -->|Diploma Data| DS4[(Diploma Records)]
    P6 --> P7[Update Alumni Status]
    P7 -->|Status Update| DS5[(Student Records)]
    P7 --> P8[Notify Student: Approved]
    P8 --> Student

    style Student fill:#4A90E2,color:#fff
    style P1 fill:#3498DB,color:#fff
    style P2 fill:#9B59B6,color:#fff
    style P3 fill:#E74C3C,color:#fff
    style P4 fill:#E74C3C,color:#fff
    style P5 fill:#27AE60,color:#fff
    style P6 fill:#F39C12,color:#fff
    style P7 fill:#1ABC9C,color:#fff
    style P8 fill:#27AE60,color:#fff
    style C1 fill:#F39C12,color:#fff
    style C2 fill:#F39C12,color:#fff
    style C3 fill:#F39C12,color:#fff
```

## Student Discipline Case Flow

```mermaid
flowchart TD
    Reporter[Reporter] -->|File Incident Report| P1[Receive Incident Report]
    P1 -->|Store Case| DS1[(Disciplinary Cases)]
    P1 --> P2[Investigate Case]
    P2 --> P3[Schedule Hearing]
    P3 -->|Store Hearing| DS2[(Hearing Records)]
    P3 --> P4[Panel Reviews Case]
    P4 --> C1{Violation Confirmed?}
    C1 -->|No| P5[Close Case]
    P5 -->|Update Status| DS1
    C1 -->|Yes| P6[Apply Sanction]
    P6 -->|Store Sanction| DS3[(Sanction Records)]
    P6 --> P7[Notify Student]
    P7 --> Student[Student]
    P7 --> C2{Appeal Filed?}
    C2 -->|No| P8[Close Case]
    P8 -->|Update Status| DS1
    C2 -->|Yes| P9[Review Appeal]
    P9 --> C3{Appeal Decision}
    C3 -->|Upheld| P8
    C3 -->|Modified| P10[Modify Sanction]
    P10 -->|Update Sanction| DS3
    P10 --> P8
    C3 -->|Overturned| P11[Remove Sanction]
    P11 -->|Update Sanction| DS3
    P11 --> P8

    style Reporter fill:#95A5A6,color:#fff
    style Student fill:#4A90E2,color:#fff
    style P1 fill:#3498DB,color:#fff
    style P2 fill:#9B59B6,color:#fff
    style P3 fill:#E67E22,color:#fff
    style P4 fill:#1ABC9C,color:#fff
    style P5 fill:#27AE60,color:#fff
    style P6 fill:#E74C3C,color:#fff
    style P7 fill:#F39C12,color:#fff
    style P8 fill:#27AE60,color:#fff
    style P9 fill:#9B59B6,color:#fff
    style P10 fill:#E67E22,color:#fff
    style P11 fill:#1ABC9C,color:#fff
    style C1 fill:#F39C12,color:#fff
    style C2 fill:#F39C12,color:#fff
    style C3 fill:#F39C12,color:#fff
```

## Grade Appeal Escalation Flow

```mermaid
flowchart TD
    Student[Student] -->|Submit Grade Appeal| P1[Receive Grade Appeal]
    P1 -->|Store Appeal| DS1[(Grade Appeals)]
    P1 --> P2[Faculty Review]
    P2 --> C1{Faculty Decision}
    C1 -->|Grade Modified| P3[Update Grade]
    P3 -->|New Grade| DS2[(Grade Records)]
    P3 --> P8[Notify Student: Resolved]
    C1 -->|Rejected| P9[Notify Student: Rejected]
    C1 -->|Escalated| P4[Dept Head Review]
    P4 --> C2{Dept Head Decision}
    C2 -->|Grade Modified| P3
    C2 -->|Rejected| P9
    C2 -->|Escalated| P5[Committee Review]
    P5 --> C3{Committee Decision}
    C3 -->|Grade Modified| P6[Update Grade with New Value]
    P6 -->|New Grade| DS2
    P6 --> P7[Notify Student: Modified]
    C3 -->|Upheld Original| P9
    P8 --> Student
    P7 --> Student
    P9 --> Student

    style Student fill:#4A90E2,color:#fff
    style P1 fill:#3498DB,color:#fff
    style P2 fill:#9B59B6,color:#fff
    style P3 fill:#27AE60,color:#fff
    style P4 fill:#E67E22,color:#fff
    style P5 fill:#E74C3C,color:#fff
    style P6 fill:#27AE60,color:#fff
    style P7 fill:#1ABC9C,color:#fff
    style P8 fill:#1ABC9C,color:#fff
    style P9 fill:#95A5A6,color:#fff
    style C1 fill:#F39C12,color:#fff
    style C2 fill:#F39C12,color:#fff
    style C3 fill:#F39C12,color:#fff
```

## Faculty Recruitment Flow

```mermaid
flowchart TD
    Dept[Department] -->|Request Position| P1[Create Job Posting]
    HR[HR Admin] -->|Define Requirements| P1
    P1 -->|Store Posting| DS1[(Job Postings)]
    P1 --> P2[Publish Posting]
    P2 --> Applicant[Applicant]
    Applicant -->|Submit Application| P3[Receive Application]
    P3 -->|Store Application| DS2[(Job Applications)]
    P3 --> P4[Screen Applications]
    P4 --> P5[Shortlist Candidates]
    P5 -->|Update Status| DS2
    P5 --> P6[Schedule Interviews]
    P6 -->|Store Schedule| DS3[(Interview Schedules)]
    P6 --> P7[Conduct Interviews]
    P7 --> C1{Suitable Candidate?}
    C1 -->|No| P8[Re-open or Close Posting]
    P8 -->|Update Posting| DS1
    C1 -->|Yes| P9[Extend Offer]
    P9 -->|Store Offer| DS4[(Offer Letters)]
    P9 -->|Send Offer| Applicant
    Applicant -->|Response| C2{Offer Accepted?}
    C2 -->|No| P8
    C2 -->|Yes| P10[Begin Onboarding]
    P10 -->|Create Record| DS5[(Employee Records)]
    P10 --> P11[Close Posting as Filled]
    P11 -->|Update Posting| DS1

    style Dept fill:#7B68EE,color:#fff
    style HR fill:#E74C3C,color:#fff
    style Applicant fill:#4A90E2,color:#fff
    style P1 fill:#3498DB,color:#fff
    style P2 fill:#9B59B6,color:#fff
    style P3 fill:#E67E22,color:#fff
    style P4 fill:#1ABC9C,color:#fff
    style P5 fill:#F39C12,color:#fff
    style P6 fill:#3498DB,color:#fff
    style P7 fill:#9B59B6,color:#fff
    style P8 fill:#95A5A6,color:#fff
    style P9 fill:#27AE60,color:#fff
    style P10 fill:#1ABC9C,color:#fff
    style P11 fill:#27AE60,color:#fff
    style C1 fill:#F39C12,color:#fff
    style C2 fill:#F39C12,color:#fff
```

## Transfer Credit Evaluation Flow

```mermaid
flowchart TD
    Student[Student] -->|Submit Transcript| P1[Receive Transfer Credit Request]
    P1 -->|Store Request| DS1[(Transfer Credit Requests)]
    P1 --> P2[Evaluate Each Course]
    P2 --> P3[Check Articulation Agreements]
    P3 -->|Query Agreements| DS2[(Articulation Agreements)]
    P3 --> C1{Agreement Exists?}
    C1 -->|Yes| P4[Apply Pre-approved Mapping]
    C1 -->|No| P5[Manual Course Evaluation]
    P4 --> P6[Map to Internal Course]
    P5 --> C2{Course Equivalent?}
    C2 -->|No| P7[Reject Credit Item]
    C2 -->|Yes| P6
    P6 -->|Store Mapping| DS3[(Transfer Credit Items)]
    P7 -->|Store Rejection| DS3
    P6 --> P8[Apply Credit Limits]
    P7 --> P8
    P8 --> C3{Within 40% Max?}
    C3 -->|No| P9[Cap at Maximum Allowed]
    C3 -->|Yes| P10[Approve Transfer Credits]
    P9 --> P10
    P10 -->|Update Record| DS4[(Student Records)]
    P10 --> P11[Notify Student]
    P11 --> Student

    style Student fill:#4A90E2,color:#fff
    style P1 fill:#3498DB,color:#fff
    style P2 fill:#9B59B6,color:#fff
    style P3 fill:#E67E22,color:#fff
    style P4 fill:#1ABC9C,color:#fff
    style P5 fill:#E74C3C,color:#fff
    style P6 fill:#F39C12,color:#fff
    style P7 fill:#95A5A6,color:#fff
    style P8 fill:#3498DB,color:#fff
    style P9 fill:#E67E22,color:#fff
    style P10 fill:#27AE60,color:#fff
    style P11 fill:#1ABC9C,color:#fff
    style C1 fill:#F39C12,color:#fff
    style C2 fill:#F39C12,color:#fff
    style C3 fill:#F39C12,color:#fff
```

## Scholarship Disbursement Flow

```mermaid
flowchart TD
    Student[Student] -->|Submit Application| P1[Receive Scholarship Application]
    P1 -->|Store Application| DS1[(Scholarship Applications)]
    P1 --> P2[Check Eligibility]
    P2 -->|Query Programs| DS2[(Scholarship Programs)]
    P2 --> C1{Eligible?}
    C1 -->|No| P3[Reject Application]
    P3 --> P12[Notify Student: Rejected]
    P12 --> Student
    C1 -->|Yes| P4[Committee Review]
    P4 --> C2{Award Decision}
    C2 -->|Rejected| P3
    C2 -->|Waitlisted| P5[Add to Waitlist]
    P5 -->|Update Status| DS1
    C2 -->|Approved| P6[Validate Stacking Rules]
    P6 --> C3{Stacking OK?}
    C3 -->|No| P7[Adjust Award Amount]
    C3 -->|Yes| P8[Create Scholarship Award]
    P7 --> P8
    P8 -->|Store Award| DS3[(Scholarship Awards)]
    P8 --> P9[Schedule Disbursement]
    P9 -->|Store Disbursement| DS4[(Aid Disbursements)]
    P9 --> P10[Apply Funds to Student Account]
    P10 -->|Update Balance| DS5[(Student Accounts)]
    P10 --> P11[Notify Student: Awarded]
    P11 --> Student
    P9 --> P13[Renewal Check Each Semester]
    P13 --> C4{Meets Renewal Criteria?}
    C4 -->|Yes| P9
    C4 -->|No| P14[Suspend or Revoke Award]
    P14 -->|Update Award| DS3

    style Student fill:#4A90E2,color:#fff
    style P1 fill:#3498DB,color:#fff
    style P2 fill:#9B59B6,color:#fff
    style P3 fill:#E74C3C,color:#fff
    style P4 fill:#E67E22,color:#fff
    style P5 fill:#F39C12,color:#fff
    style P6 fill:#1ABC9C,color:#fff
    style P7 fill:#E67E22,color:#fff
    style P8 fill:#27AE60,color:#fff
    style P9 fill:#3498DB,color:#fff
    style P10 fill:#16A085,color:#fff
    style P11 fill:#27AE60,color:#fff
    style P12 fill:#E74C3C,color:#fff
    style P13 fill:#9B59B6,color:#fff
    style P14 fill:#E74C3C,color:#fff
    style C1 fill:#F39C12,color:#fff
    style C2 fill:#F39C12,color:#fff
    style C3 fill:#F39C12,color:#fff
    style C4 fill:#F39C12,color:#fff
```

## Data Store Descriptions

| Store ID | Name | Description | Key Entities |
|----------|------|-------------|--------------|
| D1 | Users | All system users | User accounts, roles, permissions |
| D2 | Students | Student records | Student profiles, status, academic info |
| D3 | Courses | Course catalog | Programs, courses, sections, schedules |
| D4 | Enrollments | Student enrollments | Semester enrollments, course enrollments |
| D5 | Grades | Assessment data | Grades, GPA, exam results |
| D6 | Payments | Financial transactions | Payments, transactions, receipts |
| D7 | Content | Learning materials | Course content, assignments, submissions |
| D8 | Notifications | Communication queue | Notifications, announcements, emails |
| D9 | Accounts | Student accounts | Balances, fee structures, invoices |
| D10 | Receipts | Payment receipts | Receipt PDFs, payment confirmations |
| D11 | Transcripts | Academic transcripts | Transcript records, certificates |

## Data Flow Characteristics

### Input Data Flows
- **User Input**: Forms, file uploads, selections
- **External Services**: Payment confirmations, email delivery status
- **System Generated**: Auto-calculated values, timestamps

### Processing Data Flows
- **Validation**: Data verification and business rule enforcement
- **Transformation**: Data format conversion, calculations
- **Enrichment**: Adding computed fields, lookups

### Output Data Flows
- **User Output**: HTML pages, PDFs, JSON responses
- **External Services**: Email/SMS content, payment requests
- **Storage**: Database writes, file saves

### Control Flows
- **Authentication**: User login, token validation
- **Authorization**: Permission checks, role verification
- **Workflow**: State transitions, approval chains

## Data Transformation Examples

1. **Application to Student**:
   - Input: Application data
   - Transform: Validate, generate student ID, create user account
   - Output: Student record

2. **Course Registration to Enrollment**:
   - Input: Selected courses
   - Transform: Validate prerequisites, check capacity, resolve conflicts
   - Output: Enrollment records, timetable

3. **Grades to GPA**:
   - Input: Individual course grades
   - Transform: Calculate weighted average, determine letter grade
   - Output: Semester GPA, cumulative GPA

4. **Payment Request to Receipt**:
   - Input: Payment amount, method
   - Transform: Generate transaction ID, process payment, update balance
   - Output: Payment receipt, updated account

## Summary

The Data Flow Diagrams show:
- **Level 0**: System as a black box with external entities
- **Level 1**: Major processes and data stores
- **Level 2**: Detailed sub-processes for critical workflows

These diagrams help understand data movement, transformation points, and dependencies across the EMIS system, serving as a blueprint for implementation and integration.
