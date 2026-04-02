# EMIS - Business Process Flow & Activity Diagrams

## 1. Student Admission & Enrollment Process

### Overview
This flowchart shows the complete process from application submission to student enrollment.

```mermaid
flowchart TD
    Start([Prospective Student]) --> A1[Visit Website]
    A1 --> A2[Create Account]
    A2 --> A3[Fill Application Form]
    A3 --> A4{Complete All<br/>Required Fields?}
    A4 -->|No| A3
    A4 -->|Yes| A5[Upload Documents]
    A5 --> A6{Documents<br/>Valid?}
    A6 -->|No| A5
    A6 -->|Yes| A7[Pay Application Fee]
    A7 --> A8{Payment<br/>Successful?}
    A8 -->|No| A7
    A8 -->|Yes| A9[Submit Application]
    A9 --> A10[Receive Application Number]
    
    A10 --> B1[Admissions Office Reviews]
    B1 --> B2{Documents<br/>Complete?}
    B2 -->|No| B3[Request Additional Docs]
    B3 --> B4[Applicant Submits Docs]
    B4 --> B1
    
    B2 -->|Yes| B5[Evaluate Application]
    B5 --> B6[Enter Scores/Rating]
    B6 --> B7{Decision}
    
    B7 -->|Reject| C1[Send Rejection Email]
    C1 --> End1([Application Closed])
    
    B7 -->|Shortlist| D1[Add to Merit List]
    D1 --> D2[Invite for Interview/Test]
    D2 --> D3[Conduct Assessment]
    D3 --> D4{Pass Assessment?}
    D4 -->|No| C1
    D4 -->|Yes| D5[Offer Admission]
    
    D5 --> E1[Send Acceptance Letter]
    E1 --> E2[Student Accepts Offer]
    E2 --> E3[Pay Admission Fee]
    E3 --> E4{Payment<br/>Received?}
    E4 -->|No| E3
    E4 -->|Yes| E5[Create Student Record]
    E5 --> E6[Generate Student ID]
    E6 --> E7[Assign to Program & Batch]
    E7 --> E8[Create User Account]
    E8 --> E9[Send Welcome Email]
    E9 --> E10[Student Enrolled]
    E10 --> End2([Process Complete])
    
    style Start fill:#4A90E2,color:#fff
    style End1 fill:#E74C3C,color:#fff
    style End2 fill:#27AE60,color:#fff
    style A9 fill:#F39C12
    style B7 fill:#9B59B6,color:#fff
    style D4 fill:#9B59B6,color:#fff
    style E10 fill:#27AE60,color:#fff
```

## 2. Course Registration Process

```mermaid
flowchart TD
    Start([Student Login]) --> A1{Registration<br/>Period Open?}
    A1 -->|No| End1([Wait for Registration])
    A1 -->|Yes| A2{Outstanding<br/>Fees?}
    A2 -->|Yes| A3[Clear Dues First]
    A3 --> End2([Cannot Register])
    
    A2 -->|No| B1[View Available Courses]
    B1 --> B2[Select Course]
    B2 --> B3{Prerequisites<br/>Met?}
    B3 -->|No| B4[Show Error Message]
    B4 --> B1
    
    B3 -->|Yes| B5{Course<br/>Full?}
    B5 -->|Yes| B6[Join Waitlist?]
    B6 -->|Yes| B7[Add to Waitlist]
    B7 --> B1
    B6 -->|No| B1
    
    B5 -->|No| B8{Schedule<br/>Conflict?}
    B8 -->|Yes| B9[Show Conflict Warning]
    B9 --> B1
    
    B8 -->|No| C1[Add to Cart]
    C1 --> C2{Add More<br/>Courses?}
    C2 -->|Yes| B1
    
    C2 -->|No| D1[Review Cart]
    D1 --> D2{Credit Hours<br/>Valid?}
    D2 -->|No| D3[Adjust Selections]
    D3 --> B1
    
    D2 -->|Yes| D4[Confirm Registration]
    D4 --> E1[Create Enrollments]
    E1 --> E2[Generate Timetable]
    E2 --> E3[Calculate Fees]
    E3 --> E4[Send Confirmation Email]
    E4 --> E5[Registration Complete]
    E5 --> End3([Success])
    
    style Start fill:#4A90E2,color:#fff
    style End1 fill:#95A5A6,color:#fff
    style End2 fill:#E74C3C,color:#fff
    style End3 fill:#27AE60,color:#fff
    style E5 fill:#27AE60,color:#fff
```

## 3. Grade Submission & Processing

```mermaid
flowchart TD
    Start([Faculty Login]) --> A1[View Assigned Courses]
    A1 --> A2[Select Course]
    A2 --> A3{Grading<br/>Period Open?}
    A3 -->|No| End1([Wait for Grading Period])
    
    A3 -->|Yes| B1[View Student List]
    B1 --> B2{Bulk Upload<br/>or Manual?}
    
    B2 -->|Bulk| C1[Download Template]
    C1 --> C2[Fill Grades Offline]
    C2 --> C3[Upload CSV File]
    C3 --> C4{File<br/>Valid?}
    C4 -->|No| C5[Show Errors]
    C5 --> C2
    C4 -->|Yes| D1
    
    B2 -->|Manual| D1[Enter Grades One by One]
    D1 --> D2{All Students<br/>Graded?}
    D2 -->|No| D3[Mark Incomplete]
    D3 --> D4
    D2 -->|Yes| D4[Review All Grades]
    
    D4 --> D5{Grades<br/>Correct?}
    D5 -->|No| D1
    D5 -->|Yes| E1[Submit Grades]
    E1 --> E2[Confirm Submission Warning]
    E2 --> E3{Confirm?}
    E3 -->|No| D1
    
    E3 -->|Yes| F1[Lock Grades]
    F1 --> F2[Calculate Student GPAs]
    F2 --> F3[Update Transcripts]
    F3 --> F4[Send Notifications to Students]
    F4 --> F5[Log Submission]
    F5 --> End2([Grades Posted])
    
    F5 --> G1{Need to<br/>Change Grade?}
    G1 -->|Yes| G2[Request Modification]
    G2 --> G3[Admin Reviews Request]
    G3 --> G4{Approved?}
    G4 -->|Yes| G5[Update Grade]
    G5 --> F2
    G4 -->|No| End3([Request Denied])
    
    style Start fill:#7B68EE,color:#fff
    style End1 fill:#95A5A6,color:#fff
    style End2 fill:#27AE60,color:#fff
    style End3 fill:#E74C3C,color:#fff
```

## 4. Fee Payment & Collection Process

```mermaid
flowchart TD
    Start([Student/Parent Login]) --> A1[View Fee Statement]
    A1 --> A2{Outstanding<br/>Balance?}
    A2 -->|No| End1([No Payment Needed])
    
    A2 -->|Yes| B1[Select Payment Amount]
    B1 --> B2{Amount<br/>Valid?}
    B2 -->|No| B3[Show Minimum Amount]
    B3 --> B1
    
    B2 -->|Yes| C1[Select Payment Method]
    C1 --> C2[Initiate Payment]
    C2 --> C3[Redirect to Gateway]
    C3 --> C4[Enter Payment Details]
    C4 --> C5{Gateway<br/>Response?}
    
    C5 -->|Timeout| C6[Retry Payment?]
    C6 -->|Yes| C1
    C6 -->|No| End2([Payment Cancelled])
    
    C5 -->|Failed| C7[Show Error Message]
    C7 --> C6
    
    C5 -->|Success| D1[Verify Payment Signature]
    D1 --> D2{Signature<br/>Valid?}
    D2 -->|No| D3[Alert IT & Finance]
    D3 --> D4[Manual Verification]
    D4 --> D5{Verified?}
    D5 -->|No| End3([Payment Rejected])
    D5 -->|Yes| E1
    
    D2 -->|Yes| E1[Update Student Balance]
    E1 --> E2[Create Payment Record]
    E2 --> E3[Generate Receipt]
    E3 --> E4[Send Receipt via Email]
    E4 --> E5[Notify Finance Department]
    E5 --> E6[Update Dashboard]
    E6 --> End4([Payment Successful])
    
    End4 --> F1[Daily Reconciliation]
    F1 --> F2{Gateway Balance<br/>= System Balance?}
    F2 -->|No| F3[Investigate Discrepancy]
    F3 --> F4[Resolve Issues]
    F4 --> F5[Generate Reports]
    F2 -->|Yes| F5
    F5 --> End5([Reconciliation Complete])
    
    style Start fill:#4A90E2,color:#fff
    style End1 fill:#95A5A6,color:#fff
    style End2 fill:#F39C12,color:#fff
    style End3 fill:#E74C3C,color:#fff
    style End4 fill:#27AE60,color:#fff
    style End5 fill:#27AE60,color:#fff
```

## 5. Library Book Circulation

```mermaid
flowchart TD
    Start([Student/Faculty]) --> A1[Search Library Catalog]
    A1 --> A2{Book<br/>Found?}
    A2 -->|No| End1([Search Again])
    
    A2 -->|Yes| B1{Book<br/>Available?}
    B1 -->|No| B2[Reserve Book]
    B2 --> B3[Add to Waitlist]
    B3 --> End2([Wait for Availability])
    
    B1 -->|Yes| C1[Visit Library]
    C1 --> C2[Present Library Card]
    C2 --> C3{User Has<br/>Pending Fines?}
    C3 -->|Yes| C4[Pay Fines First]
    C4 --> C5{Fines<br/>Cleared?}
    C5 -->|No| End3([Cannot Issue Book])
    C5 -->|Yes| D1
    
    C3 -->|No| D1{Borrowing<br/>Limit Reached?}
    D1 -->|Yes| D2[Return Books First]
    D2 --> End4([Cannot Issue More])
    
    D1 -->|No| E1[Issue Book]
    E1 --> E2[Set Due Date]
    E2 --> E3[Update Book Status]
    E3 --> E4[Send Confirmation]
    E4 --> End5([Book Issued])
    
    End5 --> F1[Student Uses Book]
    F1 --> F2{Due Date<br/>Approaching?}
    F2 -->|Yes| F3[Send Return Reminder]
    F3 --> F4
    F2 -->|No| F4[Wait]
    F4 --> F5{Book<br/>Returned?}
    
    F5 -->|No| F6{Overdue?}
    F6 -->|Yes| F7[Calculate Fine]
    F7 --> F8[Add Fine to Account]
    F8 --> F9[Send Overdue Notice]
    F9 --> F5
    F6 -->|No| F4
    
    F5 -->|Yes| G1[Return Book]
    G1 --> G2[Inspect Book]
    G2 --> G3{Book<br/>Damaged?}
    G3 -->|Yes| G4[Assess Damage Fine]
    G4 --> G5[Add Fine to Account]
    G5 --> G6
    G3 -->|No| G6{Overdue<br/>Fine?}
    G6 -->|Yes| G7[Collect Fine]
    G7 --> G8{Fine<br/>Paid?}
    G8 -->|No| G9[Fine Remains Pending]
    G9 --> H1
    G8 -->|Yes| H1
    G6 -->|No| H1[Mark Book Returned]
    
    H1 --> H2[Update Book Status]
    H2 --> H3{Waitlist<br/>Empty?}
    H3 -->|No| H4[Notify Next in Queue]
    H4 --> End6([Book Available for Next])
    H3 -->|Yes| End7([Book Back in Circulation])
    
    style Start fill:#4A90E2,color:#fff
    style End1 fill:#95A5A6,color:#fff
    style End2 fill:#F39C12,color:#fff
    style End3 fill:#E74C3C,color:#fff
    style End4 fill:#E74C3C,color:#fff
    style End5 fill:#27AE60,color:#fff
    style End6 fill:#27AE60,color:#fff
    style End7 fill:#27AE60,color:#fff
```

## 6. Attendance Marking Process

```mermaid
flowchart TD
    Start([Class Begins]) --> A1[Faculty Login to App]
    A1 --> A2[Select Course & Section]
    A2 --> A3[Select Date & Time Slot]
    A3 --> A4[View Class Roster]
    A4 --> A5{Marking<br/>Method?}
    
    A5 -->|Manual| B1[Mark Each Student]
    B1 --> B2[Present/Absent/Late]
    B2 --> B3{All Students<br/>Marked?}
    B3 -->|No| B1
    B3 -->|Yes| C1
    
    A5 -->|Mark All Present| C1[Save Attendance]
    
    A5 -->|Biometric| D1[Students Scan Fingerprint]
    D1 --> D2[System Auto-Marks Present]
    D2 --> D3{Class Time<br/>Over?}
    D3 -->|No| D1
    D3 -->|Yes| D4[Mark Remaining Absent]
    D4 --> C1
    
    C1 --> C2[Sync to Database]
    C2 --> C3[Update Attendance Records]
    C3 --> C4[Calculate Attendance %]
    C4 --> C5{Student Below<br/>Minimum %?}
    C5 -->|Yes| C6[Flag at-risk Student]
    C6 --> C7[Notify Student & Advisor]
    C7 --> C8
    C5 -->|No| C8[Log Attendance]
    C8 --> End1([Attendance Recorded])
    
    End1 --> E1{Student Has<br/>Leave Application?}
    E1 -->|Yes| E2[Check Leave Dates]
    E2 --> E3{Leave Approved<br/>for This Date?}
    E3 -->|Yes| E4[Mark as Authorized Absence]
    E4 --> E5[Update Attendance Record]
    E5 --> E6[Recalculate %]
    E6 --> End2([Attendance Updated])
    E3 -->|No| End2
    E1 -->|No| End2
    
    style Start fill:#7B68EE,color:#fff
    style End1 fill:#27AE60,color:#fff
    style End2 fill:#27AE60,color:#fff
```

## 7. Report Generation Process

```mermaid
flowchart TD
    Start([User Request]) --> A1[Select Report Type]
    A1 --> A2{Report<br/>Category?}
    
    A2 -->|Academic| B1[Student Performance/<br/>Grades/Attendance]
    A2 -->|Financial| B2[Revenue/Expenses/<br/>Outstanding Dues]
    A2 -->|HR| B3[Payroll/Leave/<br/>Employee Stats]
    A2 -->|Custom| B4[Select Data Source]
    
    B1 --> C1
    B2 --> C1
    B3 --> C1
    B4 --> C1[Configure Filters]
    
    C1 --> C2[Select Date Range]
    C2 --> C3[Select Programs/Departments]
    C3 --> C4[Select Columns/Metrics]
    C4 --> C5[Preview Report]
    C5 --> C6{Satisfied<br/>with Preview?}
    C6 -->|No| C1
    
    C6 -->|Yes| D1[Generate Report]
    D1 --> D2{Large<br/>Dataset?}
    D2 -->|Yes| D3[Queue Background Job]
    D3 --> D4[Send Email When Ready]
    D4 --> End1([Report Emailed])
    
    D2 -->|No| E1[Execute Query]
    E1 --> E2[Format Data]
    E2 --> E3[Apply Styling]
    E3 --> E4[Select Export Format]
    E4 --> E5{Format?}
    
    E5 -->|PDF| F1[Generate PDF]
    E5 -->|Excel| F2[Generate Excel]
    E5 -->|CSV| F3[Generate CSV]
    
    F1 --> G1[Download/View]
    F2 --> G1
    F3 --> G1
    G1 --> G2{Save Report<br/>Template?}
    G2 -->|Yes| G3[Save Configuration]
    G3 --> G4[Name Template]
    G4 --> End2([Report Saved])
    G2 -->|No| End3([Report Downloaded])
    
    style Start fill:#E74C3C,color:#fff
    style End1 fill:#27AE60,color:#fff
    style End2 fill:#27AE60,color:#fff
    style End3 fill:#27AE60,color:#fff
```

## Summary

This document provides detailed flowcharts and activity diagrams for 7 critical business processes:

1. **Student Admission & Enrollment**: End-to-end process from application to enrollment
2. **Course Registration**: Student course selection and enrollment workflow
3. **Grade Submission & Processing**: Faculty grade entry and GPA calculation
4. **Fee Payment & Collection**: Online payment processing and reconciliation
5. **Library Book Circulation**: Book issue and return process with fine management
6. **Attendance Marking**: Multiple methods of attendance tracking
7. **Report Generation**: Configurable report creation and export

Each diagram shows decision points, validation steps, error handling, and success/failure paths to guide implementation and testing.
