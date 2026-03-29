# Activity Diagrams

## Overview
Activity diagrams showing the business process flows for key operations in the Student Information System.

---

## Course Enrollment Flow

```mermaid
flowchart TD
    Start([Student opens enrollment portal]) --> CheckWindow{Enrollment<br>Window Open?}
    CheckWindow -->|No| ShowDates[Display Registration Dates]
    ShowDates --> End1([Cannot Enroll])

    CheckWindow -->|Yes| BrowseCatalog[Browse Course Catalog]
    BrowseCatalog --> SearchFilter{Search or<br>Browse?}
    SearchFilter -->|Search| SearchResults[View Search Results]
    SearchFilter -->|Browse| DeptList[View Department Courses]
    SearchResults --> SelectCourse[Select Course]
    DeptList --> SelectCourse

    SelectCourse --> ViewDetails[View Course Details]
    ViewDetails --> CheckPrereq{Prerequisites<br>Met?}
    CheckPrereq -->|No| ShowPrereq[Show Missing Prerequisites]
    ShowPrereq --> BrowseCatalog
    CheckPrereq -->|Yes| CheckSeats{Seats<br>Available?}

    CheckSeats -->|No| OfferWaitlist{Join<br>Waitlist?}
    OfferWaitlist -->|No| BrowseCatalog
    OfferWaitlist -->|Yes| JoinWaitlist[Join Waitlist]
    JoinWaitlist --> WaitlistConfirm[Show Waitlist Position]
    WaitlistConfirm --> End2([Waitlisted])

    CheckSeats -->|Yes| CheckConflict{Schedule<br>Conflict?}
    CheckConflict -->|Yes| ShowConflict[Show Timetable Conflict]
    ShowConflict --> BrowseCatalog
    CheckConflict -->|No| ConfirmEnroll[Confirm Enrollment]

    ConfirmEnroll --> ProcessEnroll[Create Enrollment Record]
    ProcessEnroll --> DecrementSeat[Decrement Seat Count]
    DecrementSeat --> UpdateTimetable[Update Student Timetable]
    UpdateTimetable --> SendConfirmation[Send Confirmation Email]
    SendConfirmation --> ShowSuccess[Display Success Message]
    ShowSuccess --> End3([Enrolled Successfully])
```

---

## Grade Recording and Publication Flow

```mermaid
flowchart TD
    Start([Faculty opens grade entry]) --> SelectCourse[Select Course]
    SelectCourse --> OpenGradeWindow{Grade Entry<br>Window Open?}
    OpenGradeWindow -->|No| ShowClosed[Show Closed Message]
    ShowClosed --> End1([Cannot Enter Grades])

    OpenGradeWindow -->|Yes| ViewRoster[View Student Roster]
    ViewRoster --> EntryMethod{Entry<br>Method}
    EntryMethod -->|Manual| EnterManually[Enter Grades Individually]
    EntryMethod -->|CSV| UploadCSV[Upload Grade CSV]

    UploadCSV --> ValidateCSV{CSV Valid?}
    ValidateCSV -->|No| ShowErrors[Show Validation Errors]
    ShowErrors --> UploadCSV
    ValidateCSV -->|Yes| PreviewGrades[Preview Imported Grades]

    EnterManually --> ReviewGrades[Review All Grades]
    PreviewGrades --> ReviewGrades

    ReviewGrades --> AnyMissing{Any Missing<br>Grades?}
    AnyMissing -->|Yes| MarkIncomplete[Mark as Incomplete]
    MarkIncomplete --> ReviewGrades
    AnyMissing -->|No| SaveDraft{Save Draft<br>or Submit?}

    SaveDraft -->|Save Draft| DraftSaved[Draft Saved]
    DraftSaved --> End2([Continue Later])

    SaveDraft -->|Submit| SubmitGrades[Submit Final Grades]
    SubmitGrades --> NotifyRegistrar[Notify Registrar]
    NotifyRegistrar --> RegistrarReview[Registrar Reviews Grades]

    RegistrarReview --> GradesApproved{Approved?}
    GradesApproved -->|No| ReturnForCorrection[Return to Faculty]
    ReturnForCorrection --> ReviewGrades
    GradesApproved -->|Yes| PublishGrades[Publish Grades]

    PublishGrades --> CalculateGPA[Calculate GPA/CGPA]
    CalculateGPA --> UpdateStanding[Update Academic Standing]
    UpdateStanding --> NotifyStudents[Notify Students]
    NotifyStudents --> NotifyParents[Notify Parents]
    NotifyParents --> End3([Grades Published])
```

---

## Fee Payment Flow

```mermaid
flowchart TD
    Start([Student views fee invoice]) --> CheckDue{Fees Due?}
    CheckDue -->|No| ShowPaid[Show Paid Status]
    ShowPaid --> End1([No Action Required])

    CheckDue -->|Yes| SelectPayment[Select Payment Method]
    SelectPayment --> PaymentChoice{Payment<br>Method}

    PaymentChoice -->|Full Payment| FullAmount[Pay Full Amount]
    PaymentChoice -->|Installment| CheckInstallment{Installment<br>Plan Available?}

    CheckInstallment -->|No| FullAmount
    CheckInstallment -->|Yes| SelectInstallment[Choose Installment Plan]
    SelectInstallment --> InstallmentAmount[Set Installment Amount]

    FullAmount --> ChooseGateway[Choose Payment Gateway]
    InstallmentAmount --> ChooseGateway

    ChooseGateway --> RedirectGateway[Redirect to Gateway]
    RedirectGateway --> ProcessPayment{Payment<br>Success?}

    ProcessPayment -->|No| PaymentFailed[Show Failure Message]
    PaymentFailed --> RetryOption{Retry?}
    RetryOption -->|Yes| SelectPayment
    RetryOption -->|No| End2([Payment Abandoned])

    ProcessPayment -->|Yes| RecordPayment[Record Payment in System]
    RecordPayment --> UpdateInvoice[Update Invoice Status]
    UpdateInvoice --> GenerateReceipt[Generate Receipt]
    GenerateReceipt --> SendNotification[Send Email/SMS Receipt]
    SendNotification --> CheckScholarship{Scholarship<br>Applied?}

    CheckScholarship -->|Yes| ApplyAid[Apply Financial Aid Credit]
    ApplyAid --> End3([Payment Complete])
    CheckScholarship -->|No| End3
```

---

## Attendance Marking Flow

```mermaid
flowchart TD
    Start([Faculty opens class session]) --> SelectSession[Select Course and Date]
    SelectSession --> CheckSession{Session<br>Exists?}
    CheckSession -->|No| CreateSession[Create Session Record]
    CreateSession --> DisplayRoster
    CheckSession -->|Yes| DisplayRoster[Display Student Roster]

    DisplayRoster --> MarkingMethod{Attendance<br>Method}

    MarkingMethod -->|Manual| ManualMark[Mark Each Student Manually]
    MarkingMethod -->|QR Code| GenerateQR[Generate QR Code]
    MarkingMethod -->|Biometric| ReadBiometric[Read Biometric Data]

    GenerateQR --> Studentscan[Students Scan QR]
    Studentscan --> AutoMark[Auto-mark Present]
    AutoMark --> FacultyReview[Faculty Reviews Marks]

    ReadBiometric --> AutoProcess[Auto-process Biometric]
    AutoProcess --> FacultyReview

    ManualMark --> ReviewMarks[Review Attendance Marks]
    FacultyReview --> ReviewMarks

    ReviewMarks --> SaveAttendance{Save<br>Attendance}
    SaveAttendance -->|Cancel| End1([Attendance Not Saved])
    SaveAttendance -->|Confirm| RecordAttendance[Save Attendance Records]

    RecordAttendance --> CalculatePercent[Calculate Attendance %]
    CalculatePercent --> CheckThreshold{Below 75%<br>Threshold?}

    CheckThreshold -->|No| End2([Attendance Saved])
    CheckThreshold -->|Yes| SendStudentAlert[Alert Student]
    SendStudentAlert --> SendParentAlert[Alert Parent/Guardian]
    SendParentAlert --> AlertAdvisor[Notify Academic Advisor]
    AlertAdvisor --> End3([Attendance Saved + Alerts Sent])
```

---

## Student Registration Flow

```mermaid
flowchart TD
    Start([New Student Applies]) --> FillApplication[Fill Admission Application]
    FillApplication --> UploadDocuments[Upload Required Documents]
    UploadDocuments --> PayAdmissionFee[Pay Admission Fee]
    PayAdmissionFee --> SubmitApplication[Submit Application]

    SubmitApplication --> AdminReview[Admin Reviews Application]
    AdminReview --> DocumentsVerified{Documents<br>Valid?}
    DocumentsVerified -->|No| RequestDocs[Request Missing Documents]
    RequestDocs --> UploadDocuments
    DocumentsVerified -->|Yes| AdmissionDecision{Admission<br>Decision}

    AdmissionDecision -->|Rejected| NotifyRejection[Notify Rejection with Reason]
    NotifyRejection --> End1([Application Rejected])

    AdmissionDecision -->|Accepted| SendOffer[Send Admission Offer]
    SendOffer --> StudentAccepts{Student<br>Accepts Offer?}
    StudentAccepts -->|No| End2([Offer Declined])
    StudentAccepts -->|Yes| PayConfirmation[Pay Confirmation Fee]

    PayConfirmation --> CreateAccount[Create Student Account]
    CreateAccount --> AssignStudentID[Assign Student ID]
    AssignStudentID --> AssignProgram[Assign Degree Program]
    AssignProgram --> AssignAdvisor[Assign Academic Advisor]
    AssignAdvisor --> SendCredentials[Send Login Credentials]
    SendCredentials --> OpenEnrollment[Open Course Enrollment]
    OpenEnrollment --> End3([Registration Complete])
```

---

## Transcript Request Flow

```mermaid
flowchart TD
    Start([Student requests transcript]) --> CheckHolds{Account<br>Holds?}
    CheckHolds -->|Yes| ShowHolds[Show Active Holds]
    ShowHolds --> ResolveHolds[Resolve Holds]
    ResolveHolds --> CheckHolds

    CheckHolds -->|No| SelectPurpose[Select Transcript Purpose]
    SelectPurpose --> SelectDelivery[Select Delivery Method]
    SelectDelivery --> PayFee{Transcript<br>Fee Required?}
    PayFee -->|Yes| MakePayment[Make Payment]
    MakePayment --> SubmitRequest[Submit Request]
    PayFee -->|No| SubmitRequest

    SubmitRequest --> RegistrarQueue[Registrar Review Queue]
    RegistrarQueue --> VerifyRecords{Records<br>Complete?}

    VerifyRecords -->|No| NotifyStudent[Notify Student of Issue]
    NotifyStudent --> End1([Request On Hold])

    VerifyRecords -->|Yes| GeneratePDF[Generate Transcript PDF]
    GeneratePDF --> ApplySignature[Apply Digital Signature]
    ApplySignature --> DeliveryMethod{Delivery<br>Method}

    DeliveryMethod -->|Download| UploadSecure[Upload to Secure Portal]
    UploadSecure --> NotifyDownload[Notify Student to Download]

    DeliveryMethod -->|Email| SendEmail[Send via Secure Email]

    DeliveryMethod -->|Physical| QueuePrint[Queue for Printing]
    QueuePrint --> PostDelivery[Post/Courier Dispatch]

    NotifyDownload --> End2([Transcript Issued])
    SendEmail --> End2
    PostDelivery --> End2
```

## Implementation-Ready Addendum for Activity Diagrams

### Purpose in This Artifact
Adds missing decision nodes for holds, overrides, and downstream recalculations.

### Scope Focus
- Activity coverage closure
- Enrollment lifecycle enforcement relevant to this artifact
- Grading/transcript consistency constraints relevant to this artifact
- Role-based and integration concerns at this layer

### Supplemental Mermaid (Artifact-Specific)
```mermaid
flowchart TD
    A[Enroll Request]-->B{Financial Hold?}
    B--Yes-->C[Block + Notify]
    B--No-->D{Prereq Satisfied?}
    D--No-->E[Petition Path]
    D--Yes-->F[Seat Allocation]
    F-->G[Emit EnrollmentConfirmed]
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

