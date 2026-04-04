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

## 8. Graduation Application & Degree Conferral

The end-to-end process from student graduation application through degree conferral.

```mermaid
flowchart TD
    Start([Student Initiates Graduation]) --> A1[View Degree Progress]
    A1 --> A2{All Requirements\nMet?}
    A2 -->|No| A3[View Missing Requirements]
    A3 --> End1([Cannot Apply Yet])
    A2 -->|Yes| A4[Submit Graduation Application]
    A4 --> A5[System Runs Automated Degree Audit]
    A5 --> A6{Audit Result}
    A6 -->|FAILED| A7[Show Missing Requirements]
    A7 --> A8{Student Addresses\nDeficiencies?}
    A8 -->|Yes| A4
    A8 -->|No| End2([Application Rejected])
    A6 -->|PASSED| A9[Route to Department for Verification]
    A9 --> A10{Department\nApproves?}
    A10 -->|No| A11[Return with Feedback]
    A11 --> End2
    A10 -->|Yes| A12[Route to Registrar]
    A12 --> A13{Registrar\nApproves?}
    A13 -->|No| End2
    A13 -->|Yes| A14[Determine Honors Classification]
    A14 --> A15{CGPA Check}
    A15 -->|≥ 3.90| A16[Summa Cum Laude]
    A15 -->|≥ 3.70| A17[Magna Cum Laude]
    A15 -->|≥ 3.50| A18[Cum Laude]
    A15 -->|< 3.50| A19[No Honors]
    A16 --> A20[Generate Diploma]
    A17 --> A20
    A18 --> A20
    A19 --> A20
    A20 --> A21[Assign Diploma Number]
    A21 --> A22[Finalize Transcript]
    A22 --> A23[Update Student Status to GRADUATED]
    A23 --> A24[Create Alumni Record]
    A24 --> A25[Notify Student]
    A25 --> End3([Degree Conferred])

    style Start fill:#E74C3C,color:#fff
    style End1 fill:#F39C12,color:#fff
    style End2 fill:#E74C3C,color:#fff
    style End3 fill:#27AE60,color:#fff
```

## 9. Disciplinary Case Processing

The workflow for handling student disciplinary incidents from report through resolution.

```mermaid
flowchart TD
    Start([Incident Reported]) --> A1[Faculty/Staff Submits Report]
    A1 --> A2[System Creates Case - REPORTED]
    A2 --> A3[Notify Discipline Committee]
    A3 --> A4[Notify Student of Report]
    A4 --> A5[Committee Reviews Evidence]
    A5 --> A6{Sufficient Evidence?}
    A6 -->|No| A7[Dismiss Case]
    A7 --> End1([Case Dismissed])
    A6 -->|Yes| A8[Begin Investigation]
    A8 --> A9[Assign Panel Members]
    A9 --> A10{Conflict of\nInterest Check}
    A10 -->|Conflict Found| A11[Reassign Panel]
    A11 --> A9
    A10 -->|No Conflict| A12[Schedule Hearing]
    A12 --> A13[Notify Student ≥5 Business Days]
    A13 --> A14[Conduct Hearing]
    A14 --> A15[Record Evidence & Testimony]
    A15 --> A16[Panel Deliberates]
    A16 --> A17{Decision}
    A17 -->|Not Responsible| A7
    A17 -->|Responsible| A18[Determine Sanction]
    A18 --> A19{Sanction Type}
    A19 -->|Warning| A20[Issue Written Warning]
    A19 -->|Probation| A21[Apply Disciplinary Probation]
    A19 -->|Suspension| A22[Withdraw from Courses]
    A22 --> A23[Block Registration]
    A19 -->|Expulsion| A24[Permanent Block]
    A24 --> A23
    A20 --> A25[Notify Student of Decision]
    A21 --> A25
    A23 --> A25
    A25 --> A26[Start 10-Day Appeal Window]
    A26 --> A27{Student Appeals?}
    A27 -->|No| A28[Close Case]
    A28 --> End2([Case Closed])
    A27 -->|Yes| A29[Submit Appeal]
    A29 --> A30[Assign Appeals Board]
    A30 --> A31[Review Appeal]
    A31 --> A32{Appeal Outcome}
    A32 -->|Upheld| A28
    A32 -->|Modified| A33[Apply Modified Sanction]
    A33 --> A28
    A32 -->|Reversed| A34[Remove Sanctions]
    A34 --> A35[Restore Enrollment]
    A35 --> A28
    A32 -->|New Hearing| A12

    style Start fill:#E74C3C,color:#fff
    style End1 fill:#F39C12,color:#fff
    style End2 fill:#27AE60,color:#fff
```

## 10. Grade Appeal & Revaluation

The multi-level grade appeal process with mandatory escalation.

```mermaid
flowchart TD
    Start([Student Disputes Grade]) --> A1[View Published Grade]
    A1 --> A2{Within 15-Day\nDeadline?}
    A2 -->|No| End1([Deadline Passed - Cannot Appeal])
    A2 -->|Yes| A3[Submit Grade Appeal]
    A3 --> A4[Upload Supporting Evidence]
    A4 --> A5[Route to Course Faculty]
    A5 --> A6[Faculty Reviews - 7 Day Window]
    A6 --> A7{Faculty Decision}
    A7 -->|Agrees - Modifies Grade| A8[Record New Grade]
    A8 --> A9[Preserve Original Grade in History]
    A9 --> A10[Recalculate GPA/CGPA]
    A10 --> A11[Notify Student]
    A11 --> End2([Appeal Resolved - Grade Modified])
    A7 -->|Upholds Original| A12[Escalate to Department Head]
    A7 -->|No Response in 7 Days| A12
    A12 --> A13[Dept Head Reviews - 7 Day Window]
    A13 --> A14{Dept Head Decision}
    A14 -->|Modifies Grade| A8
    A14 -->|Upholds| A15[Escalate to Academic Appeals Committee]
    A14 -->|No Response in 7 Days| A15
    A15 --> A16[Committee Reviews - 14 Day Window]
    A16 --> A17{Committee Decision}
    A17 -->|Grade Modified| A8
    A17 -->|Re-examination Ordered| A18[Schedule Re-exam]
    A18 --> A19[Student Takes Re-exam]
    A19 --> A20[New Grade Recorded]
    A20 --> A10
    A17 -->|Upheld - Final| A21[Notify Student - Decision Final]
    A21 --> End3([Appeal Resolved - Grade Upheld])

    style Start fill:#E74C3C,color:#fff
    style End1 fill:#F39C12,color:#fff
    style End2 fill:#27AE60,color:#fff
    style End3 fill:#27AE60,color:#fff
```

## 11. Faculty Recruitment Pipeline

The end-to-end faculty recruitment process from position creation to onboarding.

```mermaid
flowchart TD
    Start([Department Requests Position]) --> A1[Create Position Request]
    A1 --> A2[Budget Approval - Dept Head + Dean + Finance]
    A2 --> A3{Approved?}
    A3 -->|No| End1([Position Request Denied])
    A3 -->|Yes| A4[HR Creates Job Posting]
    A4 --> A5[Publish to Career Portal]
    A5 --> A6[Receive Applications]
    A6 --> A7[Auto-Screen Applications]
    A7 --> A8{Meets Minimum\nQualifications?}
    A8 -->|No| A9[Notify Candidate - Screened Out]
    A9 --> End2([Application Rejected])
    A8 -->|Yes| A10[Add to Shortlist Pool]
    A10 --> A11[HR Reviews Shortlist]
    A11 --> A12[Schedule Interviews]
    A12 --> A13{Panel Composition\nValid?}
    A13 -->|No| A14[Adjust Panel - Need Dept + External + HR]
    A14 --> A12
    A13 -->|Yes| A15[Book Interview Room]
    A15 --> A16[Notify Candidate & Panel]
    A16 --> A17[Conduct Interview]
    A17 --> A18[Panel Submits Evaluations]
    A18 --> A19[Aggregate Scores]
    A19 --> A20{Scores Above\nThreshold?}
    A20 -->|No| A9
    A20 -->|Yes| A21[HR Extends Offer]
    A21 --> A22[Send Offer Letter - 15 Day Validity]
    A22 --> A23{Candidate Response}
    A23 -->|Accepts| A24[Background Verification]
    A24 --> A25{Verification\nPassed?}
    A25 -->|No| A26[Rescind Offer]
    A26 --> End2
    A25 -->|Yes| A27[Create Employee Record]
    A27 --> A28[Provision User Account]
    A28 --> A29[Send Onboarding Checklist]
    A29 --> A30[Set Probation Period]
    A30 --> End3([Faculty Onboarded])
    A23 -->|Rejects| A31[Consider Next Candidate]
    A31 --> A11
    A23 -->|No Response| A32[Offer Expired]
    A32 --> A31

    style Start fill:#E74C3C,color:#fff
    style End1 fill:#F39C12,color:#fff
    style End2 fill:#E74C3C,color:#fff
    style End3 fill:#27AE60,color:#fff
```

## 12. Academic Semester Lifecycle Management

The complete lifecycle of an academic semester from creation to archival.

```mermaid
flowchart TD
    Start([Admin Creates Semester]) --> A1[Set Semester Dates]
    A1 --> A2[Configure Registration Window]
    A2 --> A3[Set Add/Drop Deadline]
    A3 --> A4[Set Grading Window]
    A4 --> A5[Department Heads Configure Course Offerings]
    A5 --> A6[Assign Faculty to Sections]
    A6 --> A7[Set Room Assignments]
    A7 --> A8[Publish Course Catalog]
    A8 --> A9[Open Registration]
    A9 --> A10[Students Register for Courses]
    A10 --> A11{Registration\nWindow Closed?}
    A11 -->|No| A10
    A11 -->|Yes| A12[Activate Semester]
    A12 --> A13[Classes Begin]
    A13 --> A14[Add/Drop Period Active]
    A14 --> A15{Add/Drop\nDeadline Passed?}
    A15 -->|No| A14
    A15 -->|Yes| A16[Lock Enrollments]
    A16 --> A17[Regular Classes Continue]
    A17 --> A18[Enter Exam Period]
    A18 --> A19[Block Enrollment Changes]
    A19 --> A20[Conduct Exams]
    A20 --> A21[Open Grading Window]
    A21 --> A22[Faculty Submit Grades]
    A22 --> A23{All Grades\nSubmitted?}
    A23 -->|No| A24[Send Reminders to Faculty]
    A24 --> A22
    A23 -->|Yes| A25[Close Grading Window]
    A25 --> A26[Calculate GPA/CGPA for All Students]
    A26 --> A27[Determine Academic Standing]
    A27 --> A28[Generate Dean's List]
    A28 --> A29[Publish Results]
    A29 --> A30[Notify Students]
    A30 --> A31[Close Semester]
    A31 --> A32[Archive Semester Data]
    A32 --> End1([Semester Archived])

    style Start fill:#E74C3C,color:#fff
    style End1 fill:#27AE60,color:#fff
```

## 13. Transfer Credit Evaluation

The workflow for evaluating and approving transfer credits from external institutions.

```mermaid
flowchart TD
    Start([Transfer Student Submits Request]) --> A1[Upload Official Transcripts]
    A1 --> A2[Upload Course Syllabi]
    A2 --> A3[Submit Transfer Application]
    A3 --> A4[Registrar Receives Application]
    A4 --> A5{Articulation Agreement\nExists?}
    A5 -->|Yes| A6[Auto-Map Using Agreement]
    A5 -->|No| A7[Manual Equivalency Review]
    A7 --> A8[Compare Syllabi with Internal Courses]
    A8 --> A9{Equivalent Course\nFound?}
    A9 -->|Yes| A6
    A9 -->|No| A10[Reject - No Equivalent]
    A6 --> A11{Grade ≥ B?}
    A11 -->|No| A12[Reject - Grade Insufficient]
    A11 -->|Yes| A13{Total Transfers\n≤ 40%?}
    A13 -->|No| A14[Reject - Transfer Limit Exceeded]
    A13 -->|Yes| A15{Residency Requirement\nMet?}
    A15 -->|No| A16[Reject - Residency Violation]
    A15 -->|Yes| A17[Approve Transfer Credit]
    A17 --> A18[Update Student Record]
    A18 --> A19[Update Degree Audit]
    A19 --> A20[Notify Student]
    A20 --> End1([Transfer Credits Applied])
    A10 --> A21[Notify Student - Rejected]
    A12 --> A21
    A14 --> A21
    A16 --> A21
    A21 --> A22{Student Appeals?}
    A22 -->|Yes| A7
    A22 -->|No| End2([Transfer Rejected])

    style Start fill:#E74C3C,color:#fff
    style End1 fill:#27AE60,color:#fff
    style End2 fill:#E74C3C,color:#fff
```

## 14. Scholarship Application & Lifecycle

The workflow for scholarship application, disbursement, and renewal.

```mermaid
flowchart TD
    Start([Student Explores Scholarships]) --> A1[Browse Available Scholarships]
    A1 --> A2[Check Eligibility Criteria]
    A2 --> A3{Eligible?}
    A3 -->|No| End1([Not Eligible])
    A3 -->|Yes| A4{Auto-Award\nScholarship?}
    A4 -->|Yes| A5[System Auto-Awards Based on GPA]
    A4 -->|No| A6[Student Submits Application]
    A6 --> A7[Upload Supporting Documents]
    A7 --> A8[Financial Aid Reviews Application]
    A8 --> A9[Score and Rank Applicants]
    A9 --> A10{Approved?}
    A10 -->|No| End2([Application Rejected])
    A10 -->|Yes, Fund Available| A5
    A10 -->|Yes, No Fund| A11[Waitlist Application]
    A11 --> A12{Fund Replenished?}
    A12 -->|Yes| A5
    A12 -->|No| End2
    A5 --> A13[Award Scholarship]
    A13 --> A14[Notify Student]
    A14 --> A15{Disbursement\nMethod}
    A15 -->|Fee Adjustment| A16[Apply to Fee Invoice]
    A15 -->|Direct Payment| A17[Process Stipend Payment]
    A16 --> A18[Invoice Balance Reduced]
    A17 --> A18
    A18 --> A19[Semester Ends]
    A19 --> A20[Check Renewal Criteria]
    A20 --> A21{Criteria Met?}
    A21 -->|Yes| A22[Renew for Next Semester]
    A22 --> A19
    A21 -->|First Failure| A23[Issue Warning - Grace Period]
    A23 --> A19
    A21 -->|Second Consecutive Failure| A24[Revoke Scholarship]
    A24 --> A25[Reverse Fee Adjustment]
    A25 --> A26[Notify Student]
    A26 --> End3([Scholarship Revoked])

    style Start fill:#E74C3C,color:#fff
    style End1 fill:#F39C12,color:#fff
    style End2 fill:#E74C3C,color:#fff
    style End3 fill:#E74C3C,color:#fff
```

## 15. Student Admission to Enrollment

The complete workflow from admission cycle opening to student enrolled in semester with classroom and faculty assignments.

```mermaid
flowchart TD
    Start([Admin Opens Admission Cycle]) --> A1[Configure Cycle Details]
    A1 --> A2[Set Program, Dates, Seat Limit]
    A2 --> A3[Publish Cycle to Portal]
    A3 --> A4([Cycle Published])

    A4 --> B1[Student Visits Portal]
    B1 --> B2[Fill Application Form]
    B2 --> B3[Upload Documents]
    B3 --> B4[Pay Application Fee]
    B4 --> B5[Submit Application]
    B5 --> B6([Application Submitted])

    B6 --> C1[Admissions Reviews Application]
    C1 --> C2{Documents\nComplete?}
    C2 -->|No| C3[Request Additional Documents]
    C3 --> B3
    C2 -->|Yes| C4[Evaluate Application]
    C4 --> C5{Decision}
    C5 -->|Reject| C6[Send Rejection Notification]
    C6 --> End1([Application Rejected])
    C5 -->|Shortlist| C7[Shortlist Applicant]

    C7 --> D1{Entrance Exam\nRequired?}
    D1 -->|No| D8[Use Application Score]
    D1 -->|Yes| D2[Schedule Entrance Exam]
    D2 --> D3[Conduct Entrance Exam]
    D3 --> D4{Auto-Score\nEnabled?}
    D4 -->|Yes| D5[System Auto-Scores]
    D4 -->|No| D6[Manual Scoring]
    D5 --> D7[Finalize Scores]
    D6 --> D7
    D7 --> D8

    D8 --> E1[Generate Merit List]
    E1 --> E2[Assign Ranks Based on Scores]
    E2 --> E3[Calculate Cutoff Score]
    E3 --> E4[Publish Merit List]
    E4 --> E5{Student Rank\n≤ Seat Limit?}
    E5 -->|No| E6[Waitlist or Reject]
    E6 --> End2([Not Selected])
    E5 -->|Yes| E7[Send Admission Offer]

    E7 --> F1{Top N Merit\nStudent?}
    F1 -->|Yes| F2[Auto-Award Scholarship]
    F2 --> F3[Scholarship Linked to Student]
    F1 -->|No| F3

    F3 --> G1[Student Accepts Offer]
    G1 --> G2[Generate Fee Invoice]
    G2 --> G3{Scholarship\nAwarded?}
    G3 -->|Yes| G4[Auto-Deduct Scholarship from Invoice]
    G4 --> G5[Student Pays Remaining Balance]
    G3 -->|No| G5[Student Pays Full Invoice]
    G5 --> G6{All Bills\nCleared?}
    G6 -->|No| G7[Notify Outstanding Balance]
    G7 --> G5
    G6 -->|Yes| G8[Bills Cleared]

    G8 --> H1[Staff Initiates Conversion]
    H1 --> H2{Documents Verified\n& Offer Accepted?}
    H2 -->|No| H3[Return Error to Staff]
    H3 --> End3([Conversion Failed])
    H2 -->|Yes| H4[Create Student Record]
    H4 --> H5[Generate Student ID]
    H5 --> H6[Create Semester Enrollment]
    H6 --> H7[Assign Classroom]
    H7 --> H8[Assign Teachers to Subjects]
    H8 --> H9[Send Welcome Email]
    H9 --> End4([Student Enrolled])

    style Start fill:#4A90E2,color:#fff
    style A4 fill:#F39C12,color:#fff
    style B6 fill:#F39C12,color:#fff
    style End1 fill:#E74C3C,color:#fff
    style End2 fill:#E74C3C,color:#fff
    style End3 fill:#E74C3C,color:#fff
    style End4 fill:#27AE60,color:#fff
    style C5 fill:#9B59B6,color:#fff
    style E5 fill:#9B59B6,color:#fff
    style F1 fill:#9B59B6,color:#fff
    style G6 fill:#9B59B6,color:#fff
    style H2 fill:#9B59B6,color:#fff
```

## 16. Semester Progression & Repeat

The workflow for assigning students to next semester or repeating a previous semester.

```mermaid
flowchart TD
    Start([Semester Ends]) --> A1[Admin Reviews Student Results]
    A1 --> A2[System Calculates GPA/CGPA]
    A2 --> A3[Determine Academic Standing]
    A3 --> A4{Passed All\nCourses?}

    A4 -->|Yes| B1[Check Progression Eligibility]
    B1 --> B2{Financial\nHolds?}
    B2 -->|Yes| B3[Notify Student of Hold]
    B3 --> B4[Student Clears Hold]
    B4 --> B2
    B2 -->|No| B5{Academic Standing\nOK?}
    B5 -->|No| B6[Place on Academic Probation]
    B6 --> B7{Admin Approves\nProgression?}
    B7 -->|No| C1
    B7 -->|Yes| B8[Assign Next Semester]
    B5 -->|Yes| B8
    B8 --> B9[Create Semester Enrollment]
    B9 --> B10[Assign Classroom]
    B10 --> B11[Notify Student]
    B11 --> End1([Progressed to Next Semester])

    A4 -->|No| C1{Admin Approves\nRepeat?}
    C1 -->|No| C2[Student Counseling]
    C2 --> C3{Student Withdraws?}
    C3 -->|Yes| End2([Student Withdrawn])
    C3 -->|No| C1
    C1 -->|Yes| C4[Assign Repeat Semester]
    C4 --> C5[Create Enrollment with is_repeat=true]
    C5 --> C6[Assign Classroom]
    C6 --> C7[Notify Student]
    C7 --> End3([Repeating Semester])

    style Start fill:#4A90E2,color:#fff
    style End1 fill:#27AE60,color:#fff
    style End2 fill:#E74C3C,color:#fff
    style End3 fill:#F39C12,color:#fff
    style A4 fill:#9B59B6,color:#fff
    style C1 fill:#9B59B6,color:#fff
    style B5 fill:#9B59B6,color:#fff
```

## Summary

This document provides detailed flowcharts and activity diagrams for 16 critical business processes:

1. **Student Admission & Enrollment**: End-to-end process from application to enrollment
2. **Course Registration**: Student course selection and enrollment workflow
3. **Grade Submission & Processing**: Faculty grade entry and GPA calculation
4. **Fee Payment & Collection**: Online payment processing and reconciliation
5. **Library Book Circulation**: Book issue and return process with fine management
6. **Attendance Marking**: Multiple methods of attendance tracking
7. **Report Generation**: Configurable report creation and export
8. **Graduation Application & Degree Conferral**: Student graduation through degree conferral and alumni record creation
9. **Disciplinary Case Processing**: Incident report through hearing, sanctions, and appeals
10. **Grade Appeal & Revaluation**: Multi-level grade appeal with escalation and re-examination
11. **Faculty Recruitment Pipeline**: Position creation through hiring and onboarding
12. **Academic Semester Lifecycle Management**: Semester creation through grading and archival
13. **Transfer Credit Evaluation**: External credit evaluation with articulation agreements
14. **Scholarship Application & Lifecycle**: Scholarship application, disbursement, and renewal
15. **Student Admission to Enrollment**: Complete admission cycle from opening through entrance exam, merit list, scholarship, payment, and conversion to enrolled student
16. **Semester Progression & Repeat**: Student progression to next semester or repeat assignment with eligibility checks

Each diagram shows decision points, validation steps, error handling, and success/failure paths to guide implementation and testing.
