# EMIS - BPMN & Swimlane Diagrams

## 1. Student Admission Process (Cross-Department)

### Overview
This BPMN swimlane diagram shows how the admission process flows across different departments and actors.

```mermaid
graph TB
    subgraph Applicant["Applicant (Student)"]
        A1[Fill Application Form]
        A2[Upload Documents]
        A3[Pay Application Fee]
        A4[Submit Application]
        A8[Accept/Decline Offer]
        A9[Pay Admission Fee]
    end
    
    subgraph IT_System["IT System (Automated)"]
        S1[Generate Application Number]
        S2[Send Confirmation Email]
        S3[Validate Documents]
        S4[Calculate Scores]
        S5[Generate Merit List]
        S6[Send Acceptance Letter]
        S7[Create Student Record]
        S8[Generate Student ID]
    end
    
    subgraph Admissions_Office["Admissions Office"]
        AD1[Review Application]
        AD2[Request Additional Docs]
        AD3[Evaluate Credentials]
        AD4[Make Decision]
        AD5[Process Admission]
    end
    
    subgraph Faculty_Committee["Faculty/Committee"]
        F1[Conduct Interview]
        F2[Review Test Results]
        F3[Final Approval]
    end
    
    subgraph Finance_Dept["Finance Department"]
        FI1[Verify Application Fee]
        FI2[Verify Admission Fee]
        FI3[Create Fee Structure]
        FI4[Generate Invoice]
    end
    
    subgraph Academic_Dept["Academic Department"]
        AC1[Assign to Program]
        AC2[Allocate Section]
        AC3[Assign Faculty Advisor]
    end
    
    A1 --> A2 --> A3 --> A4
    A4 --> S1 --> S2
    S2 --> FI1
    FI1 -->|Fee Verified| AD1
    FI1 -->|Fee Not Received| AD2
    AD2 --> A2
    
    AD1 --> S3
    S3 -->|Valid| AD3
    S3 -->|Invalid| AD2
    
    AD3 --> S4
    S4 --> AD4
    AD4 -->|Shortlist| F1
    AD4 -->|Direct Accept| S5
    AD4 -->|Reject| S2
    
    F1 --> F2 --> F3
    F3 -->|Approved| S5
    F3 -->|Rejected| S2
    
    S5 --> S6 --> A8
    A8 -->|Accept| A9
    A8 -->|Decline| S2
    
    A9 --> FI2
    FI2 -->|Verified| AD5
    AD5 --> S7 --> S8
    S8 --> AC1 --> AC2 --> AC3
    AC3 --> FI3 --> FI4
    
    style A1 fill:#4A90E2,color:#fff
    style S1 fill:#34495E,color:#fff
    style AD1 fill:#E74C3C,color:#fff
    style F1 fill:#7B68EE,color:#fff
    style FI1 fill:#27AE60,color:#fff
    style AC1 fill:#F39C12,color:#fff
```

## 2. Fee Payment & Collection Workflow

```mermaid
graph TB
    subgraph Student_Parent["Student/Parent"]
        SP1[Login to Portal]
        SP2[View Fee Statement]
        SP3[Initiate Payment]
        SP4[Enter Payment Details]
        SP5[Confirm Transaction]
        SP6[Download Receipt]
    end
    
    subgraph System["System"]
        SYS1[Display Outstanding Balance]
        SYS2[Generate Transaction ID]
        SYS3[Redirect to Gateway]
        SYS4[Receive Payment Response]
        SYS5[Verify Signature]
        SYS6[Update Balance]
        SYS7[Generate Receipt]
        SYS8[Send Notifications]
    end
    
    subgraph Payment_Gateway["Payment Gateway"]
        PG1[Process Payment]
        PG2[Deduct Amount from Account]
        PG3[Send Confirmation]
        PG4[Transfer to Institution]
    end
    
    subgraph Finance_Office["Finance Office"]
        FO1[Receive Payment Notification]
        FO2[Verify Transaction]
        FO3[Update Accounting System]
        FO4[Reconcile Daily Payments]
        FO5[Generate Financial Reports]
    end
    
    subgraph Bank["Bank"]
        BK1[Credit Institution Account]
        BK2[Send Bank Statement]
    end
    
    subgraph Academic_Office["Academic Office"]
        AO1[Check Fee Clearance Status]
        AO2[Allow Course Registration]
        AO3[Release Exam Admit Card]
    end
    
    SP1 --> SP2 --> SYS1
    SYS1 --> SP3 --> SYS2
    SYS2 --> SYS3 --> SP4
    SP4 --> PG1 --> PG2
    PG2 --> SP5 --> PG3
    PG3 --> SYS4 --> SYS5
    SYS5 -->|Valid| SYS6
    SYS5 -->|Invalid| FO1
    SYS6 --> SYS7 --> SYS8
    SYS8 --> FO1
    SYS8 --> SP6
    
    FO1 --> FO2 --> FO3
    PG4 --> BK1 --> BK2
    BK2 --> FO4 --> FO5
    
    SYS6 --> AO1
    AO1 -->|Cleared| AO2
    AO1 -->|Cleared| AO3
    
    style SP1 fill:#4A90E2,color:#fff
    style SYS1 fill:#34495E,color:#fff
    style PG1 fill:#E8F5E9
    style FO1 fill:#27AE60,color:#fff
    style BK1 fill:#FFE0B2
    style AO1 fill:#F39C12,color:#fff
```

## 3. Course Registration Process (Multi-Department)

```mermaid
graph TB
    subgraph Student["Student"]
        ST1[Login to Portal]
        ST2[View Available Courses]
        ST3[Select Courses]
        ST4[Add to Cart]
        ST5[Confirm Registration]
        ST6[View Timetable]
    end
    
    subgraph System["System"]
        SY1[Check Fee Status]
        SY2[Fetch Course List]
        SY3[Validate Prerequisites]
        SY4[Check Capacity]
        SY5[Check Conflicts]
        SY6[Create Enrollments]
        SY7[Generate Timetable]
        SY8[Calculate Fees]
        SY9[Send Confirmation]
    end
    
    subgraph Finance["Finance"]
        FI1[Verify Fee Clearance]
        FI2[Block Registration if Dues]
        FI3[Add Course Fees to Account]
    end
    
    subgraph Academic_Dept["Academic Department"]
        AD1[Define Course Offerings]
        AD2[Set Enrollment Limits]
        AD3[Assign Faculty]
        AD4[Approve Overrides]
    end
    
    subgraph Faculty_Advisor["Faculty Advisor"]
        FA1[Review Student Registration]
        FA2[Approve Course Selection]
        FA3[Suggest Alternatives]
    end
    
    subgraph Timetable_Office["Timetable Office"]
        TO1[Allocate Classrooms]
        TO2[Resolve Conflicts]
        TO3[Publish Master Timetable]
    end
    
    ST1 --> SY1
    SY1 --> FI1
    FI1 -->|Cleared| ST2
    FI1 -->|Dues Pending| FI2
    
    AD1 --> AD2 --> AD3
    AD3 --> SY2
    SY2 --> ST2
    
    ST3 --> SY3
    SY3 -->|Failed| FA3
    SY3 -->|Passed| SY4
    SY4 -->|Full| AD4
    SY4 -->|Available| SY5
    AD4 -->|Approved| SY5
    AD4 -->|Rejected| FA3
    
    SY5 -->|No Conflict| ST4
    SY5 -->|Conflict| FA3
    FA3 --> ST3
    
    ST5 --> FA1
    FA1 -->|Needs Review| FA2
    FA1 -->|Auto-Approved| SY6
    FA2 -->|Approved| SY6
    FA2 -->|Rejected| ST3
    
    SY6 --> SY7
    SY7 --> TO1
    TO1 --> TO2
    TO2 --> TO3
    TO3 --> ST6
    
    SY6 --> SY8
    SY8 --> FI3
    FI3 --> SY9
    
    style ST1 fill:#4A90E2,color:#fff
    style SY1 fill:#34495E,color:#fff
    style FI1 fill:#27AE60,color:#fff
    style AD1 fill:#F39C12,color:#fff
    style FA1 fill:#7B68EE,color:#fff
    style TO1 fill:#E74C3C,color:#fff
```

## 4. Grade Processing & Transcript Generation

```mermaid
graph TB
    subgraph Faculty["Faculty"]
        FAC1[Enter Grades]
        FAC2[Review Grades]
        FAC3[Submit Grades]
        FAC4[Request Grade Change]
    end
    
    subgraph System["System"]
        SYS1[Display Student Roster]
        SYS2[Validate Grade Entries]
        SYS3[Lock Grades]
        SYS4[Calculate GPA]
        SYS5[Update Transcripts]
        SYS6[Send Notifications]
        SYS7[Log Changes]
    end
    
    subgraph Department_Head["Department Head"]
        DH1[Review Submitted Grades]
        DH2[Approve Grade Changes]
        DH3[Resolve Disputes]
    end
    
    subgraph Exam_Office["Exam Office"]
        EO1[Open Grading Period]
        EO2[Monitor Submissions]
        EO3[Send Reminders]
        EO4[Close Grading Period]
        EO5[Generate Grade Sheets]
        EO6[Archive Records]
    end
    
    subgraph Student["Student"]
        STU1[View Grades]
        STU2[Request Revaluation]
        STU3[Download Transcript]
    end
    
    subgraph Registrar["Registrar Office"]
        REG1[Verify Transcripts]
        REG2[Issue Official Transcripts]
        REG3[Maintain Grade Records]
    end
    
    EO1 --> FAC1
    SYS1 --> FAC1
    FAC1 --> FAC2
    FAC2 --> SYS2
    SYS2 -->|Valid| FAC3
    SYS2 -->|Invalid| FAC1
    
    FAC3 --> SYS3
    SYS3 --> DH1
    DH1 -->|Approved| SYS4
    DH1 -->|Issues Found| FAC1
    
    SYS4 --> SYS5
    SYS5 --> SYS6
    SYS6 --> STU1
    SYS6 --> EO2
    
    EO2 --> EO3
    EO3 --> FAC1
    EO2 --> EO4
    EO4 --> EO5
    EO5 --> EO6
    
    STU1 --> STU2
    STU2 --> DH3
    DH3 --> FAC4
    FAC4 --> DH2
    DH2 -->|Approved| SYS7
    DH2 -->|Rejected| STU1
    SYS7 --> SYS4
    
    STU1 --> STU3
    STU3 --> REG1
    REG1 --> REG2
    REG2 --> REG3
    
    style FAC1 fill:#7B68EE,color:#fff
    style SYS1 fill:#34495E,color:#fff
    style DH1 fill:#E74C3C,color:#fff
    style EO1 fill:#F39C12,color:#fff
    style STU1 fill:#4A90E2,color:#fff
    style REG1 fill:#27AE60,color:#fff
```

## 5. Employee Payroll Processing

```mermaid
graph TB
    subgraph HR_Department["HR Department"]
        HR1[Collect Attendance Data]
        HR2[Process Leave Applications]
        HR3[Update Employee Records]
        HR4[Prepare Payroll Data]
        HR5[Review Payroll]
        HR6[Submit for Processing]
    end
    
    subgraph Attendance_System["Attendance System"]
        AT1[Capture Daily Attendance]
        AT2[Calculate Working Days]
        AT3[Generate Attendance Report]
    end
    
    subgraph Finance["Finance Department"]
        FIN1[Verify Payroll Data]
        FIN2[Calculate Deductions]
        FIN3[Calculate Net Salary]
        FIN4[Generate Payslips]
        FIN5[Prepare Bank Transfer File]
        FIN6[Process Payment]
    end
    
    subgraph Management["Management"]
        MGT1[Approve Payroll]
        MGT2[Review Reports]
    end
    
    subgraph Bank["Bank"]
        BNK1[Process Salary Transfer]
        BNK2[Credit Employee Accounts]
        BNK3[Send Confirmation]
    end
    
    subgraph Employee["Employee"]
        EMP1[View Payslip]
        EMP2[Raise Query]
        EMP3[Download Tax Documents]
    end
    
    subgraph Accounts["Accounts Department"]
        ACC1[Record Expense]
        ACC2[Update Ledger]
        ACC3[Generate TDS Challan]
        ACC4[File Tax Returns]
    end
    
    AT1 --> AT2 --> AT3
    AT3 --> HR1
    HR2 --> HR3
    HR1 --> HR4
    HR3 --> HR4
    HR4 --> HR5
    HR5 --> HR6
    
    HR6 --> FIN1
    FIN1 --> FIN2
    FIN2 --> FIN3
    FIN3 --> FIN4
    FIN4 --> MGT1
    
    MGT1 -->|Approved| FIN5
    MGT1 -->|Rejected| HR4
    
    FIN5 --> FIN6
    FIN6 --> BNK1
    BNK1 --> BNK2
    BNK2 --> BNK3
    
    BNK3 --> EMP1
    FIN4 --> EMP1
    EMP1 --> EMP2
    EMP2 --> HR1
    
    FIN6 --> ACC1
    ACC1 --> ACC2
    FIN3 --> ACC3
    ACC3 --> ACC4
    
    FIN4 --> EMP3
    EMP3 --> MGT2
    
    style HR1 fill:#27AE60,color:#fff
    style AT1 fill:#34495E,color:#fff
    style FIN1 fill:#F39C12,color:#fff
    style MGT1 fill:#E74C3C,color:#fff
    style BNK1 fill:#FFE0B2
    style EMP1 fill:#4A90E2,color:#fff
    style ACC1 fill:#9B59B6,color:#fff
```

## 6. Library Book Procurement & Cataloging

```mermaid
graph TB
    subgraph Faculty_Dept["Faculty/Department"]
        FAC1[Request New Books]
        FAC2[Provide Recommendations]
    end
    
    subgraph Library_Committee["Library Committee"]
        LC1[Review Requests]
        LC2[Approve Procurement]
        LC3[Allocate Budget]
    end
    
    subgraph Library_Staff["Library Staff"]
        LIB1[Prepare Purchase Order]
        LIB2[Contact Vendors]
        LIB3[Receive Books]
        LIB4[Verify Quality]
        LIB5[Catalog Books]
        LIB6[Generate Barcodes]
        LIB7[Shelve Books]
        LIB8[Update Catalog System]
    end
    
    subgraph Finance["Finance Department"]
        FIN1[Verify Budget Availability]
        FIN2[Process Payment]
        FIN3[Issue Invoice]
    end
    
    subgraph Vendor["Book Vendor"]
        VEN1[Receive Order]
        VEN2[Prepare Books]
        VEN3[Deliver Books]
        VEN4[Provide Invoice]
    end
    
    subgraph IT_System["IT System"]
        SYS1[Update Inventory]
        SYS2[Generate Reports]
        SYS3[Make Books Searchable]
    end
    
    subgraph Students_Faculty["Users"]
        USR1[Search New Arrivals]
        USR2[Reserve Books]
    end
    
    FAC1 --> LC1
    FAC2 --> LC1
    LC1 --> LC2
    LC2 --> LC3
    LC3 --> FIN1
    
    FIN1 -->|Approved| LIB1
    FIN1 -->|Rejected| FAC1
    
    LIB1 --> LIB2
    LIB2 --> VEN1
    VEN1 --> VEN2
    VEN2 --> VEN3
    VEN3 --> LIB3
    
    LIB3 --> LIB4
    LIB4 -->|Quality OK| LIB5
    LIB4 -->|Damaged| VEN1
    
    LIB5 --> LIB6
    LIB6 --> LIB7
    LIB7 --> LIB8
    LIB8 --> SYS1
    SYS1 --> SYS3
    SYS3 --> USR1
    USR1 --> USR2
    
    VEN4 --> FIN2
    FIN2 --> FIN3
    
    SYS1 --> SYS2
    SYS2 --> LC1
    
    style FAC1 fill:#7B68EE,color:#fff
    style LC1 fill:#E74C3C,color:#fff
    style LIB1 fill:#27AE60,color:#fff
    style FIN1 fill:#F39C12,color:#fff
    style VEN1 fill:#E8F5E9
    style SYS1 fill:#34495E,color:#fff
    style USR1 fill:#4A90E2,color:#fff
```

## Summary

This document provides BPMN-style swimlane diagrams for 6 cross-departmental workflows:

1. **Student Admission Process**: Multi-stakeholder workflow from application to enrollment
2. **Fee Payment & Collection**: Payment processing across student, system, gateways, and finance
3.**Course Registration**: Complex workflow involving students, advisors, academics, and finance
4. **Grade Processing & Transcript Generation**: Grade submission, approval, and record-keeping
5. **Employee Payroll Processing**: Monthly payroll across HR, finance, and accounting
6. **Library Book Procurement & Cataloging**: Book acquisition workflow

Each diagram clearly shows:
- Responsibilities of each actor/department (swimlanes)
- Handoffs between departments
- Decision points and approvals
- System automation points
- Integration touchpoints

These diagrams are valuable for understanding dependencies, identifying bottlenecks, and defining department responsibilities.
