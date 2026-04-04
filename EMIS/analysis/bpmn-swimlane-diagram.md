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

## 7. Graduation & Degree Conferral Process

Cross-departmental workflow for processing graduation applications.

```mermaid
graph TB
    subgraph Student["Student"]
        S1[View Degree Progress]
        S2[Submit Graduation Application]
        S3[Receive Notification]
    end

    subgraph System["IT System (Automated)"]
        SYS1[Run Degree Audit]
        SYS2[Determine Honors]
        SYS3[Generate Diploma Number]
        SYS4[Calculate Final GPA/CGPA]
    end

    subgraph Department["Department"]
        D1[Verify Student Records]
        D2[Confirm Course Completion]
        D3[Department Head Approval]
    end

    subgraph Registrar["Registrar Office"]
        R1[Review Application]
        R2[Final Approval]
        R3[Issue Diploma]
        R4[Finalize Transcript]
        R5[Update Student Status]
    end

    subgraph Finance["Finance Department"]
        F1[Clear Financial Holds]
        F2[Verify Fee Clearance]
    end

    S1 --> S2
    S2 --> SYS1
    SYS1 --> SYS4
    SYS4 --> D1
    D1 --> D2
    D2 --> D3
    D3 --> R1
    R1 --> F1
    F1 --> F2
    F2 --> R2
    R2 --> SYS2
    SYS2 --> SYS3
    SYS3 --> R3
    R3 --> R4
    R4 --> R5
    R5 --> S3

    style S1 fill:#4A90E2,color:#fff
    style SYS1 fill:#34495E,color:#fff
    style D1 fill:#7B68EE,color:#fff
    style R1 fill:#27AE60,color:#fff
    style F1 fill:#F39C12,color:#fff
```

## 8. Faculty Recruitment & Onboarding Process

Cross-departmental workflow for hiring faculty from requisition to onboarding.

```mermaid
graph TB
    subgraph Dept["Requesting Department"]
        DP1[Submit Position Request]
        DP2[Review Shortlist]
        DP3[Participate in Interviews]
        DP4[Submit Evaluation]
    end

    subgraph Finance["Finance & Budget"]
        FN1[Review Budget Allocation]
        FN2[Approve/Reject Budget]
    end

    subgraph HR["Human Resources"]
        HR1[Create Job Posting]
        HR2[Publish to Portal]
        HR3[Screen Applications]
        HR4[Shortlist Candidates]
        HR5[Schedule Interviews]
        HR6[Extend Offer Letter]
        HR7[Background Verification]
        HR8[Create Employee Record]
        HR9[Send Onboarding Checklist]
    end

    subgraph Candidate["Candidate"]
        C1[Submit Application]
        C2[Attend Interview]
        C3[Accept/Reject Offer]
        C4[Submit Documents]
    end

    subgraph IT["IT Department"]
        IT1[Create User Account]
        IT2[Grant System Access]
        IT3[Provision Email]
    end

    DP1 --> FN1
    FN1 --> FN2
    FN2 --> HR1
    HR1 --> HR2
    HR2 --> C1
    C1 --> HR3
    HR3 --> HR4
    HR4 --> DP2
    DP2 --> HR5
    HR5 --> C2
    C2 --> DP3
    DP3 --> DP4
    DP4 --> HR6
    HR6 --> C3
    C3 --> HR7
    HR7 --> HR8
    HR8 --> IT1
    IT1 --> IT2
    IT2 --> IT3
    IT3 --> HR9
    HR9 --> C4

    style DP1 fill:#7B68EE,color:#fff
    style FN1 fill:#F39C12,color:#fff
    style HR1 fill:#27AE60,color:#fff
    style C1 fill:#4A90E2,color:#fff
    style IT1 fill:#34495E,color:#fff
```

## 9. Disciplinary Case Adjudication Process

Cross-departmental workflow for handling student discipline cases.

```mermaid
graph TB
    subgraph Reporter["Reporter (Faculty/Staff)"]
        RP1[Report Incident]
        RP2[Provide Evidence]
    end

    subgraph System["IT System"]
        SYS1[Create Case Number]
        SYS2[Notify Stakeholders]
        SYS3[Check Conflict of Interest]
        SYS4[Enforce Sanctions]
    end

    subgraph Committee["Discipline Committee"]
        DC1[Review Evidence]
        DC2[Investigate]
        DC3[Schedule Hearing]
        DC4[Conduct Hearing]
        DC5[Deliberate]
        DC6[Issue Decision]
    end

    subgraph Student_Actor["Student (Accused)"]
        ST1[Receive Notice]
        ST2[Attend Hearing]
        ST3[Receive Decision]
        ST4[File Appeal]
    end

    subgraph Appeals["Appeals Board"]
        AP1[Review Appeal]
        AP2[Render Decision]
    end

    subgraph Enrollment["Academic Operations"]
        EN1[Withdraw from Courses]
        EN2[Block Registration]
        EN3[Restore Access]
    end

    RP1 --> RP2
    RP2 --> SYS1
    SYS1 --> SYS2
    SYS2 --> DC1
    SYS2 --> ST1
    DC1 --> DC2
    DC2 --> SYS3
    SYS3 --> DC3
    DC3 --> ST1
    ST1 --> ST2
    ST2 --> DC4
    DC4 --> DC5
    DC5 --> DC6
    DC6 --> ST3
    DC6 --> SYS4
    SYS4 --> EN1
    EN1 --> EN2
    ST3 --> ST4
    ST4 --> AP1
    AP1 --> AP2
    AP2 --> EN3

    style RP1 fill:#E74C3C,color:#fff
    style SYS1 fill:#34495E,color:#fff
    style DC1 fill:#7B68EE,color:#fff
    style ST1 fill:#4A90E2,color:#fff
    style AP1 fill:#F39C12,color:#fff
    style EN1 fill:#27AE60,color:#fff
```

## 10. Academic Semester Lifecycle Process

Cross-departmental workflow for managing the complete semester lifecycle.

```mermaid
graph TB
    subgraph Admin["Administration"]
        AD1[Create Academic Year]
        AD2[Create Semester]
        AD3[Set Calendar Dates]
        AD4[Open Registration]
        AD5[Activate Semester]
        AD6[Start Exam Period]
        AD7[Open Grading Window]
        AD8[Close Semester]
    end

    subgraph DeptHead["Department Heads"]
        DH1[Configure Course Offerings]
        DH2[Assign Faculty to Sections]
        DH3[Approve Room Assignments]
    end

    subgraph Faculty_Actor["Faculty"]
        FA1[Accept Teaching Load]
        FA2[Conduct Classes]
        FA3[Submit Grades]
    end

    subgraph Students_Actor["Students"]
        STU1[Register for Courses]
        STU2[Attend Classes]
        STU3[Take Exams]
        STU4[View Results]
    end

    subgraph System["IT System"]
        SYS1[Publish Course Catalog]
        SYS2[Calculate GPA/CGPA]
        SYS3[Determine Standing]
        SYS4[Generate Dean's List]
        SYS5[Publish Results]
    end

    AD1 --> AD2
    AD2 --> AD3
    AD3 --> DH1
    DH1 --> DH2
    DH2 --> DH3
    DH3 --> SYS1
    SYS1 --> AD4
    AD4 --> STU1
    STU1 --> AD5
    AD5 --> FA1
    FA1 --> FA2
    FA2 --> STU2
    STU2 --> AD6
    AD6 --> STU3
    STU3 --> AD7
    AD7 --> FA3
    FA3 --> SYS2
    SYS2 --> SYS3
    SYS3 --> SYS4
    SYS4 --> SYS5
    SYS5 --> STU4
    STU4 --> AD8

    style AD1 fill:#E74C3C,color:#fff
    style DH1 fill:#7B68EE,color:#fff
    style FA1 fill:#27AE60,color:#fff
    style STU1 fill:#4A90E2,color:#fff
    style SYS1 fill:#34495E,color:#fff
```

## 11. End-to-End Admission to Enrollment Process

Cross-departmental workflow covering the complete admission cycle from opening through student enrollment, including entrance examination, merit list, scholarship, payment, and conversion.

```mermaid
graph TB
    subgraph Admin_Lane["Administration"]
        AD1[Create Admission Cycle]
        AD2[Configure Cycle Details]
        AD3[Publish Cycle to Portal]
        AD4[Configure Entrance Exam]
        AD5[Schedule Exam Date]
        AD6[Conduct Entrance Exam]
        AD7[Finalize Scores]
        AD8[Generate Merit List]
        AD9[Publish Merit List]
    end

    subgraph Applicant_Lane["Applicant / Student"]
        AP1[Visit Portal]
        AP2[Fill Application Form]
        AP3[Upload Documents]
        AP4[Pay Application Fee]
        AP5[Submit Application]
        AP6[Take Entrance Exam]
        AP7[View Merit List]
        AP8[Accept Admission Offer]
        AP9[Pay Fees]
    end

    subgraph Admissions_Lane["Admissions Staff"]
        AS1[Review Applications]
        AS2[Verify Documents]
        AS3[Shortlist Applicants]
        AS4[Dispatch Offers]
        AS5[Initiate Conversion]
        AS6[Verify Conversion Checklist]
    end

    subgraph Finance_Lane["Finance Department"]
        FI1[Verify Application Fee]
        FI2[Generate Fee Invoice]
        FI3[Apply Scholarship Deduction]
        FI4[Verify Bill Clearance]
        FI5[Confirm All Bills Cleared]
    end

    subgraph System_Lane["System (Automated)"]
        SY1[Publish to External Portal]
        SY2[Generate Application Number]
        SY3[Auto-Score Exam]
        SY4[Rank Applicants by Score]
        SY5[Determine Cutoff]
        SY6[Auto-Award Scholarships]
        SY7[Create Student Record]
        SY8[Generate Student ID]
        SY9[Create Semester Enrollment]
        SY10[Assign Classroom]
        SY11[Assign Faculty to Subjects]
        SY12[Send Welcome Notification]
    end

    AD1 --> AD2
    AD2 --> AD3
    AD3 --> SY1
    SY1 --> AP1

    AP1 --> AP2
    AP2 --> AP3
    AP3 --> AP4
    AP4 --> FI1
    FI1 -->|Verified| AP5
    AP5 --> SY2
    SY2 --> AS1

    AS1 --> AS2
    AS2 -->|Valid| AS3
    AS2 -->|Invalid| AP3

    AS3 --> AD4
    AD4 --> AD5
    AD5 --> AP6
    AP6 --> AD6
    AD6 --> SY3
    SY3 --> AD7
    AD7 --> SY4
    SY4 --> SY5
    SY5 --> AD8
    AD8 --> AD9
    AD9 --> AP7

    AP7 --> SY6
    SY6 --> AS4
    AS4 --> AP8

    AP8 --> FI2
    FI2 --> FI3
    FI3 --> AP9
    AP9 --> FI4
    FI4 -->|Outstanding| AP9
    FI4 -->|Cleared| FI5

    FI5 --> AS5
    AS5 --> AS6
    AS6 -->|All Checks Pass| SY7
    AS6 -->|Checks Fail| AS5

    SY7 --> SY8
    SY8 --> SY9
    SY9 --> SY10
    SY10 --> SY11
    SY11 --> SY12

    style AD1 fill:#E74C3C,color:#fff
    style AP1 fill:#4A90E2,color:#fff
    style AS1 fill:#7B68EE,color:#fff
    style FI1 fill:#27AE60,color:#fff
    style SY1 fill:#34495E,color:#fff
```

## Summary

This document provides BPMN-style swimlane diagrams for 11 cross-departmental workflows:

1. **Student Admission Process**: Multi-stakeholder workflow from application to enrollment
2. **Fee Payment & Collection**: Payment processing across student, system, gateways, and finance
3. **Course Registration**: Complex workflow involving students, advisors, academics, and finance
4. **Grade Processing & Transcript Generation**: Grade submission, approval, and record-keeping
5. **Employee Payroll Processing**: Monthly payroll across HR, finance, and accounting
6. **Library Book Procurement & Cataloging**: Book acquisition workflow
7. **Graduation & Degree Conferral Process**: Cross-departmental graduation application and diploma issuance
8. **Faculty Recruitment & Onboarding Process**: End-to-end faculty hiring from requisition to onboarding
9. **Disciplinary Case Adjudication Process**: Student discipline case handling with appeals workflow
10. **Academic Semester Lifecycle Process**: Complete semester management from creation to closure
11. **End-to-End Admission to Enrollment Process**: Complete admission cycle with entrance exam, merit list, scholarship auto-award, payment clearance, and applicant-to-student conversion across Admin, Applicant, Admissions, Finance, and System

Each diagram clearly shows:
- Responsibilities of each actor/department (swimlanes)
- Handoffs between departments
- Decision points and approvals
- System automation points
- Integration touchpoints

These diagrams are valuable for understanding dependencies, identifying bottlenecks, and defining department responsibilities.
