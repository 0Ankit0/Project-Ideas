# EMIS - Use Case Descriptions

## UC14: Register for Courses (Student Course Registration)

### Basic Information
- **Use Case ID**: UC14
- **Use Case Name**: Register for Courses
- **Primary Actor**: Student
- **Secondary Actors**: System, Administrator
- **Stakeholders and Interests**:
  - Student: Wants to enroll in desired courses for the semester
  - Faculty: Wants adequate enrollment for course viability
  - Administrator: Wants smooth registration process with no conflicts
  - System: Enforces business rules and constraints

### Preconditions
- Student is logged into the system
- Student account is active and in good standing
- Registration period is open for the current semester
- Student has completed previous semester requirements (if applicable)
- Student has cleared any outstanding fees (if required by policy)

### Postconditions
**Success End Condition**:
- Student is enrolled in selected courses
- Course enrollments are recorded in the database
- Student receives confirmation email
- Course enrollment count is updated
- Student's timetable is generated
- Fee structure is updated based on enrolled courses

**Failure End Condition**:
- Student is not enrolled in any courses
- System state remains unchanged
- Error message is displayed to student

### Main Success Scenario (Basic Flow)

1. Student navigates to course registration page
2. System displays current semester and registration deadline
3. System retrieves student's program and current semester number
4. System displays list of available courses for student's program and semester
5. Student searches/filters courses by code, name, or category
6. System displays course details (code, name, credits, faculty, schedule, seats available)
7. Student selects a course to enroll
8. System validates prerequisites are met
9. System validates course capacity is available
10. System checks for timetable conflicts
11. System adds course to student's cart
12. Student repeats steps 5-11 for additional courses
13. Student reviews enrolled courses in cart
14. System displays total credit hours and estimated fees
15. Student confirms registration
16. System validates minimum and maximum credit hour limits
17. System creates enrollment records
18. System generates updated timetable
19. System calculates course-based fees
20. System sends confirmation email to student
21. System displays success message with enrolled courses
22. Use case ends

### Alternative Flows

**3a. Student has not selected program or semester**:
- 3a1. System displays error message "Cannot proceed with registration"
- 3a2. System prompts administrator to complete student profile
- 3a3. Use case ends in failure

**6a. No courses available for student's semester**:
- 6a1. System displays message "No courses available for registration"
- 6a2. System suggests contacting academic advisor
- 6a3. Use case ends

**8a. Prerequisites not satisfied**:
- 8a1. System displays error "Prerequisite courses not completed: [list]"
- 8a2. System prevents adding course to cart
- 8a3. Student returns to step 5

**9a. Course is full (no seats remaining)**:
- 9a1. System displays message "Course is full (0 seats available)"
- 9a2. System offers waitlist option (if enabled)
- 9a3. Student can join waitlist or return to step 5

**10a. Timetable conflict detected**:
- 10a1. System displays error "Schedule conflict with [Course Name] on [Day] at [Time]"
- 10a2. System prevents adding course to cart
- 10a3. System suggests alternative sections (if available)
- 10a4. Student returns to step 5

**16a. Credit hours below minimum or above maximum**:
- 16a1. System displays error "Credit hours [X] outside allowed range [Min-Max]"
- 16a2. System prevents confirmation
- 16a3. Student returns to step 5 to adjust selections

**16b. Registration deadline has passed**:
- 16b1. System displays error "Registration period has ended"
- 16b2. System suggests contacting administrator for late registration
- 16b3. Use case ends in failure

### Special Requirements
- **Performance**: Course list should load within 2 seconds
- **Usability**: Interface must be mobile-responsive
- **Accessibility**: Support screen readers for visually impaired students
- **Concurrency**: Handle multiple students registering for same course simultaneously
- **Data Validation**: All inputs sanitized to prevent SQL injection

### Technology and Data Variations
- **Data Storage**: Course enrollments stored in `SemesterEnrollment` and `CourseEnrollment` models
- **Notifications**: Email sent via configured SMTP or can use SMS if enabled
- **Payment Integration**: Fee calculation may trigger payment gateway for immediate payment

### Frequency of Occurrence
- Occurs 2-3 times per year (once per semester)
- Peak load during first week of registration period
- Approximately 100-5000 students (depending on institution size)

### Open Issues
- Should system allow enrollment in courses from other programs (electives)?
- What is the policy for overriding capacity limits?
- Should students be able to register for courses outside their current semester?

---

## UC17: Enter Grades (Faculty Grade Submission)

### Basic Information
- **Use Case ID**: UC17
- **Use Case Name**: Enter Grades
- **Primary Actor**: Faculty
- **Secondary Actors**: System, Administrator
- **Stakeholders and Interests**:
  - Faculty: Wants efficient grade entry process
  - Student: Wants accurate and timely grade posting
  - Administrator: Wants grades submitted before deadline
  - Registrar: Needs grades for transcript generation

### Preconditions
- Faculty is logged into the system
- Faculty is assigned to the course
- Semester has progressed to grading period
- Course enrollment is finalized
- Grade entry period is open

### Postconditions
**Success End Condition**:
- All student grades are recorded
- Grades are locked (pending approval for changes)
- Students are notified of grade posting
- GPA calculations are updated
- Transcript reflects new grades

**Failure End Condition**:
- Grades not saved
- Students not notified
- System state unchanged

### Main Success Scenario

1. Faculty navigates to grade entry section for their courses
2. System displays list of courses taught by faculty
3. Faculty selects a course
4. System displays list of enrolled students with existing grades (if any)
5. System displays grade scale (A+, A, B+, etc.) and weightage
6. Faculty enters grade for each student
7. System validates grade value against allowed scale
8. Faculty can add comments/notes for individual students (optional)
9. Faculty reviews all grades for accuracy
10. Faculty clicks "Submit Grades"
11. System prompts for confirmation "Once submitted, grades cannot be changed without approval"
12. Faculty confirms submission
13. System validates all students have grades assigned
14. System locks grades for editing
15. System recalculates student GPAs
16. System updates transcripts
17. System sends notification to students "Grades posted for [Course Name]"
18. System displays success message
19. Use case ends

### Alternative Flows

**4a. No students enrolled**:
- 4a1. System displays "No students enrolled in this course"
- 4a2. Use case ends

**7a. Invalid grade entered**:
- 7a1. System displays error "Invalid grade. Allowed values: [list]"
- 7a2. Faculty corrects grade and returns to step 6

**13a. Some students missing grades**:
- 13a1. System displays warning "Grades missing for [N] students: [list]"
- 13a2. System asks "Submit anyway or return to entry?"
- 13a3. If faculty chooses return, go to step 6
- 13a4. If faculty chooses submit, system marks missing grades as "Incomplete (I)" and continues

**After step 14: Faculty needs to change submitted grade**:
- 14a1. Faculty requests grade change through "Request Grade Modification"
- 14a2. System prompts for reason and new grade
- 14a3. System creates change request for administrator approval
- 14a4. Administrator reviews and approves/rejects
- 14a5. If approved, system updates grade and notifies student
- 14a6. Use case ends

### Special Requirements
- **Audit Trail**: All grade entries and changes must be logged with timestamp and user
- **Bulk Upload**: System should support CSV upload for large classes
- **Offline Capability**: Faculty should be able to download roster, enter grades offline, and upload later

---

## UC28: Pay Fees (Student Fee Payment)

### Basic Information
- **Use Case ID**: UC28
- **Use Case Name**: Pay Fees
- **Primary Actor**: Student or Parent
- **Secondary Actors**: Payment Gateway, System, Finance Staff
- **Stakeholders and Interests**:
  - Student/Parent: Wants secure and convenient payment
  - Institution: Wants timely fee collection and accurate reconciliation
  - Payment Gateway: Processes transaction and charges commission

### Preconditions
- User is logged into the system
- Student has outstanding fee balance
- Payment gateway is configured and operational
- Payment methods are available (credit card, bank transfer, etc.)

### Postconditions
**Success End Condition**:
- Payment is processed successfully
- Student balance is updated
- Payment receipt is generated
- Finance system is updated
- Student and finance staff notified

**Failure End Condition**:
- Payment not processed
- Balance unchanged
- Transaction may need reversal if partially processed

### Main Success Scenario

1. Student navigates to "Fee Payment" section
2. System displays current fee summary:
   - Total fees for semester
   - Payments received
   - Outstanding balance
   - Due date
3. Student clicks "Make Payment"
4. System displays payment amount options:
   - Full payment
   - Partial payment (if allowed)
   - Installment amount (if applicable)
5. Student selects payment amount
6. System validates minimum payment amount
7. Student selects payment method (Credit Card / Debit Card / Net Banking / UPI)
8. Student clicks "Proceed to Pay"
9. System generates unique transaction ID
10. System redirects to payment gateway with encrypted payment details
11. Student enters payment credentials on gateway page
12. Payment gateway processes transaction
13. Payment gateway returns success response with payment reference
14. System verifies payment signature and authenticity
15. System updates student balance
16. System creates payment record with details
17. System generates PDF receipt
18. System sends receipt via email to student and parent
19. System notifies finance department
20. System displays success page with receipt download link
21. Use case ends

### Alternative Flows

**2a. No outstanding balance**:
- 2a1. System displays "No pending fees. Balance: Rs. 0"
- 2a2. Use case ends

**6a. Payment amount below minimum**:
- 6a1. System displays error "Minimum payment: Rs. [X]"
- 6a2. Student returns to step 5

**12a. Payment gateway timeout or error**:
- 12a1. Payment gateway returns error code
- 12a2. System displays error message "Payment failed: [Reason]"
- 12a3. System logs failed transaction
- 12a4. Student can retry payment or use different method
- 12a5. Return to step 7 or use case ends

**13a. Payment gateway returns failure**:
- 13a1. System displays "Payment failed. Please try again"
- 13a2. System does not update balance
- 13a3. Student can retry
- 13a4. Use case ends

**14a. Payment signature verification fails**:
- 14a1. System flags transaction as suspicious
- 14a2. System does NOT update balance
- 14a3. System alerts finance and IT teams
- 14a4. Manual verification required
- 14a5. Use case ends

**After step 13: Student claims payment deducted but system shows failed**:
- Resolution flow:
  - Student contacts finance with transaction ID
  - Finance staff initiates payment reconciliation
  - System queries payment gateway for transaction status
  - Gateway confirms payment success
  - Finance manually applies payment and generates receipt
  - Student notified

### Special Requirements
- **Security**: All payment data must be encrypted (PCI DSS compliance)
- **Transaction Timeout**: Payment gateway session expires after 15 minutes
- **Idempotency**: Duplicate payment submissions must be prevented
- **Reconciliation**: Daily automated reconciliation with gateway
- **Multi-Currency**: Support international payments (if applicable)

---

## UC10: Review Applications (Admissions Processing)

### Basic Information
- **Use Case ID**: UC10
- **Use Case Name**: Review Applications
- **Primary Actor**: Admissions Officer
- **Secondary Actors**: System, Admissions Committee, Applicant
- **Stakeholders and Interests**:
  - Admissions Officer: Wants efficient application review process
  - Applicant: Wants fair and timely evaluation
  - Institution: Wants to select qualified candidates

### Preconditions
- Admissions officer is logged into system
- Applications have been submitted
- Application deadline has passed (or review has begun)
- Admissions officer has appropriate permissions

### Postconditions
**Success End Condition**:
- Application status updated (Shortlisted/Rejected)
- Applicant notified of decision
- Application notes and scores recorded
- Merit list can be generated from reviewed applications

**Failure End Condition**:
- Application remains in "Under Review" status
- No decision recorded

### Main Success Scenario

1. Admissions officer navigates to application management
2. System displays list of applications filtered by status "Submitted"
3. Officer applies filters (program, date range, Score range)
4. System displays filtered application list
5. Officer selects an application to review
6. System displays application details:
   - Personal information
   - Academic background (grades, test scores)
   - Uploaded documents
   - Statement of purpose
   - Recommendation letters (if applicable)
7. Officer reviews all submitted information
8. Officer downloads and verifies documents
9. Officer enters evaluation scores based on rubric
10. System calculates total weighted score
11. Officer adds review comments/notes
12. Officer selects decision: Shortlist / Reject / Hold
13. Officer clicks "Submit Review"
14. System updates application status
15. System logs review with timestamp and reviewer name
16. If decision is Reject:
    - System sends rejection email to applicant
17. If decision is Shortlist:
    - Application moved to shortlisted pool
    - Applicant notified they are under consideration (or invited for interview/test)
18. System displays next application for review
19. Officer continues reviewing or exits
20. Use case ends

### Alternative Flows

**8a. Documents are incomplete or invalid**:
- 8a1. Officer marks application as "Documents Required"
- 8a2. System sends email to applicant requesting specific documents
- 8a3. Application status set to "Pending Documents"
- 8a4. Use case ends for this application

**12a. Officer selects "Hold" status**:
- 12a1. System prompts for reason
- 12a2. Officer enters reason (e.g., "Pending committee review")
- 12a3. Application marked as "On Hold"
- 12a4. No email sent to applicant
- 12a5. Continue to step 18

**After step 17: Bulk application processing**:
- Alternative: Officer can select multiple applications and perform bulk actions
- Bulk reject with reason
- Bulk shortlist
- System processes each application and sends notifications

### Special Requirements
- **Blind Review**: Option to hide applicant name for unbiased review
- **Multi-Reviewer**: Some applications may require review by multiple officers
- **Audit Trail**: Complete history of reviews, status changes, communications

---

## UC22: Upload Course Content (LMS Content Management)

### Basic Information
- **Use Case ID**: UC22
- **Use Case Name**: Upload Course Content
- **Primary Actor**: Faculty
- **Secondary Actors**: System, Students
- **Stakeholders and Interests**:
  - Faculty: Wants easy content publishing
  - Students: Want timely access to learning materials
  - Institution: Wants organized content repository

### Preconditions
- Faculty is logged in
- Faculty is assigned to the course
- Course exists in system
- Semester is active

### Postconditions
**Success End Condition**:
- Content uploaded and stored
- Content visible to enrolled students (based on visibility settings)
- Students notified of new content
- Content indexed for search

**Failure End Condition**:
- Content not uploaded
- Students not notified
- No changes to course content

### Main Success Scenario

1. Faculty navigates to LMS section
2. System displays courses taught by faculty
3. Faculty selects a course
4. System displays course content organized by modules/weeks
5. Faculty clicks "Add Content"
6. System displays content upload form
7. Faculty enters content details:
   - Title
   - Description
   - Module/Week
   - Content type (Lecture, Reading, Video, Assignment)
8. Faculty uploads file(s) or provides external link
9. System validates file type and size
10. Faculty sets visibility:
    - Immediately visible
    - Scheduled release (date/time)
    - Visible only to specific groups
11. Faculty sets access permissions (view, download, comment)
12. Faculty clicks "Publish"
13. System uploads file to storage
14. System creates content record in database
15. System generates content URL
16. If visibility is immediate, system notifies enrolled students
17. System displays success message
18. Content appears in course module
19. Use case ends

### Alternative Flows

**9a. File type not allowed**:
- 9a1. System displays error "File type .xyz not supported"
- 9a2. System lists allowed types (PDF, DOCX, PPTX, MP4, etc.)
- 9a3. Faculty returns to step 8

**9b. File size exceeds limit**:
- 9b1. System displays error "File size exceeds 50MB limit"
- 9b2. System suggests using external link or cloud storage
- 9b3. Faculty returns to step 8

**13a. Upload fails due to network error**:
- 13a1. System displays error "Upload failed. Please try again"
- 13a2. Faculty can retry upload
- 13a3. Return to step 8 or use case ends

**Alternative: Faculty uploads video**:
- System may process video (transcoding, thumbnail generation)
- Processing occurs in background
- Faculty notified when processing complete

### Special Requirements
- **Supported Formats**: PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX, MP4, MP3, ZIP
- **File Size Limit**: 50MB per file (configurable)
- **Storage**: Files stored securely with access control
- **Versioning**: System maintains version history if content is updated
- **Accessibility**: Support for closed captions on videos

---

## UC51: Apply for Graduation

### Basic Information
- **Use Case ID**: UC51
- **Use Case Name**: Apply for Graduation
- **Primary Actor**: Student
- **Secondary Actors**: Registrar, Department Head, System
- **Stakeholders and Interests**:
  - Student: Wants to complete degree requirements and receive diploma
  - Registrar: Wants to verify all graduation criteria are satisfied
  - Department Head: Wants to confirm departmental requirements are met
  - Institution: Wants accurate conferral records and alumni tracking

### Preconditions
- Student is logged into the system
- Student account is active and in good standing
- Student is in their final semester (as per program duration)
- Student has no administrative or financial holds on their account
- Graduation application period is open

### Postconditions

#### Success End Condition
- Graduation application is approved
- Degree is conferred and recorded in the system
- Diploma is generated and queued for printing
- Honors designation is assigned (if applicable)
- Alumni record is created in the alumni system
- Student status is updated to "Graduated"
- Transcript is marked as final

#### Failure End Condition
- Graduation application is rejected with detailed reasons
- Student is notified of outstanding requirements
- Student status remains "Active"
- No degree is conferred

### Main Success Scenario
1. Student navigates to the graduation application section
2. System displays graduation eligibility status and checklist
3. Student reviews eligibility criteria (credits completed, GPA, core requirements)
4. System runs preliminary eligibility check against degree requirements
5. System displays degree audit summary showing completed and pending requirements
6. Student reviews the degree audit for accuracy
7. Student selects degree program and expected graduation term
8. Student fills in graduation application form (preferred name on diploma, ceremony attendance)
9. Student submits graduation application
10. System creates application record with status "Submitted"
11. System runs automated degree audit against catalog requirements
12. System verifies minimum GPA requirement is met
13. System verifies total credit hours meet program minimum
14. System verifies all core, elective, and general education requirements are satisfied
15. System forwards application to Department Head for review
16. Department Head reviews application and department-specific requirements
17. Department Head approves and forwards to Registrar
18. Registrar performs final review of all requirements
19. Registrar approves graduation application
20. System updates application status to "Approved"
21. System generates diploma record with student name and degree details
22. System calculates and assigns honors designation (Summa Cum Laude, Magna Cum Laude, Cum Laude)
23. System creates alumni record with graduation details
24. System updates student status to "Graduated"
25. System sends confirmation email to student with graduation details
26. Use case ends

### Alternative Flows

**11a. Automated audit fails — missing requirements detected**
1. System identifies unmet requirements (missing courses, insufficient credits, low GPA)
2. System generates deficiency report listing each unmet requirement
3. System updates application status to "Deficiency Found"
4. System notifies student via email with deficiency details
5. Student can resolve deficiencies and resubmit, or withdraw application
6. Use case ends

**9a. Financial hold blocks application submission**
1. System detects outstanding financial balance on student account
2. System displays error "Cannot submit graduation application: outstanding balance of [amount]"
3. System provides link to fee payment section
4. Student must clear balance before resubmitting
5. Use case ends

**19a. Student withdraws application**
1. Student navigates to graduation application and selects "Withdraw"
2. System prompts for confirmation and optional reason
3. Student confirms withdrawal
4. System updates application status to "Withdrawn"
5. System notifies Registrar and Department Head
6. Use case ends

### Special Requirements
- **Audit Accuracy**: Degree audit must reflect real-time course completion and grade data
- **Honors Calculation**: Honors thresholds must be configurable per program (e.g., 3.9 Summa, 3.7 Magna, 3.5 Cum Laude)
- **Diploma Generation**: Support for multilingual diploma templates
- **Data Integrity**: Graduation records must be immutable once conferred

### Technology and Data Variations
- **Degree Audit Engine**: Automated matching of completed courses against catalog requirements
- **Diploma Templates**: PDF generation with institutional branding and digital signatures
- **Alumni Integration**: Alumni record synced to external alumni management system if configured

### Frequency of Occurrence
Occurs 2-4 times per year aligned with semester/term endings. Peak volume during spring graduation cycle. Approximately 10-30% of student body per graduation cycle.

### Open Issues
- Should students be allowed to apply for graduation before their final semester begins?
- How should double-major or dual-degree students be handled in the audit?
- What is the deadline for withdrawal without penalty?

---

## UC52: Report and Process Disciplinary Case

### Basic Information
- **Use Case ID**: UC52
- **Use Case Name**: Report and Process Disciplinary Case
- **Primary Actor**: Faculty/Staff (reporter), Discipline Committee
- **Secondary Actors**: Student (accused), Administrator
- **Stakeholders and Interests**:
  - Faculty/Staff: Wants to report misconduct and ensure campus safety
  - Student (accused): Wants fair hearing and due process
  - Discipline Committee: Wants thorough investigation and just outcomes
  - Institution: Wants policy enforcement and safe learning environment

### Preconditions
- Reporter (Faculty/Staff) is logged into the system
- Incident involves a currently enrolled student
- Disciplinary policy and sanction framework are configured in the system
- Discipline Committee members are registered in the system

### Postconditions

#### Success End Condition
- Disciplinary case is fully processed and closed
- Decision and sanctions are recorded in student's disciplinary record
- All parties are notified of the outcome
- Sanctions are applied to the student's account (if applicable)
- Appeal window is opened per policy

#### Failure End Condition
- Case is dismissed due to insufficient evidence or procedural error
- No sanctions applied
- Case record retained for documentation purposes

### Main Success Scenario
1. Faculty/Staff navigates to the disciplinary reporting section
2. Reporter selects "Report New Incident"
3. System displays incident report form
4. Reporter enters incident details (date, time, location, description, witnesses)
5. Reporter identifies the accused student(s) by name or student ID
6. Reporter uploads supporting evidence (photos, documents, screenshots)
7. Reporter selects violation category (academic dishonesty, misconduct, harassment, etc.)
8. Reporter submits the incident report
9. System creates case record with status "Reported" and assigns case number
10. System notifies the Discipline Committee chairperson
11. Committee chairperson reviews the report and assigns an investigator
12. Investigator gathers additional evidence and interviews involved parties
13. System updates case status to "Under Investigation"
14. Investigator submits investigation findings
15. Committee chairperson reviews findings and schedules a hearing
16. System sends hearing notice to accused student at least 5 business days in advance
17. System performs conflict of interest check on panel members
18. System assigns hearing panel (3-5 members with no conflicts)
19. Hearing is conducted; both parties present their case
20. Panel deliberates and reaches a decision (responsible/not responsible)
21. Panel selects appropriate sanction if found responsible (warning, probation, suspension, expulsion)
22. System records decision and sanction details
23. System applies sanction to student's account (e.g., academic probation flag, suspension hold)
24. System notifies all parties of the decision
25. System opens appeal window (typically 10 business days)
26. Use case ends

### Alternative Flows

**20a. Student appeals the decision**
1. Student submits appeal within the appeal window with grounds (procedural error, new evidence, disproportionate sanction)
2. System creates appeal record linked to original case
3. Appeal is reviewed by a separate appeal officer or panel
4. Appeal officer upholds, modifies, or overturns the original decision
5. System updates case record with appeal outcome
6. System notifies all parties
7. Use case ends

**14a. Case dismissed due to insufficient evidence**
1. Investigator finds insufficient evidence to proceed
2. Committee chairperson reviews and agrees
3. System updates case status to "Dismissed"
4. System notifies reporter and accused student
5. Case record is retained but no sanctions applied
6. Use case ends

**11a. Interim suspension applied**
1. Committee determines student poses immediate threat to campus safety
2. System applies interim suspension to student's account immediately
3. Student is denied access to campus facilities and systems
4. Full investigation and hearing proceed on expedited timeline
5. Flow continues from step 12

**22a. Multiple prior violations detected**
1. System flags that student has prior disciplinary records
2. Panel reviews history when determining sanction
3. Enhanced sanctions may be applied per progressive discipline policy
4. Flow continues from step 22

### Special Requirements
- **Due Process**: Accused student must receive written notice at least 5 business days before hearing
- **Conflict of Interest**: Panel members must have no prior relationship with involved parties; system must verify
- **Confidentiality**: All case details restricted to authorized participants only; FERPA compliance required
- **Audit Trail**: Complete log of all actions, communications, and decisions with timestamps

### Technology and Data Variations
- **Evidence Storage**: Encrypted file storage for uploaded evidence with access controls
- **Notification Channels**: Email and in-system notifications; registered mail for formal hearing notices
- **Sanction Integration**: Sanctions reflected in student status, enrollment eligibility, and hold system

### Frequency of Occurrence
Variable; typically 5-50 cases per semester depending on institution size. Academic dishonesty cases peak during midterm and final exam periods.

### Open Issues
- Should anonymous reporting be supported?
- What is the retention period for dismissed case records?
- How should cases involving students from multiple departments be handled?

---

## UC53: Submit Grade Appeal

### Basic Information
- **Use Case ID**: UC53
- **Use Case Name**: Submit Grade Appeal
- **Primary Actor**: Student
- **Secondary Actors**: Faculty, Department Head, Academic Appeals Committee
- **Stakeholders and Interests**:
  - Student: Wants fair reconsideration of a grade believed to be incorrect
  - Faculty: Wants to defend grading decisions or correct genuine errors
  - Department Head: Wants departmental grading standards upheld
  - Academic Appeals Committee: Wants impartial resolution of grade disputes

### Preconditions
- Student is logged into the system
- Grades for the relevant semester have been published
- Appeal is submitted within 15 calendar days of grade publication
- Student has not previously appealed the same grade (unless new evidence exists)

### Postconditions

#### Success End Condition
- Grade appeal is resolved with a final decision
- If grade is modified, transcript and GPA are updated
- Original grade is retained in audit history (immutable)
- All parties are notified of the outcome

#### Failure End Condition
- Appeal is rejected (deadline passed, insufficient grounds)
- Original grade remains unchanged
- Student is notified of rejection reason

### Main Success Scenario
1. Student navigates to academic records and views published grades
2. Student selects a course grade to appeal
3. System displays grade appeal form
4. Student selects appeal grounds (calculation error, bias, policy violation, missing work not considered)
5. Student provides detailed explanation of the appeal
6. Student uploads supporting evidence (graded assignments, rubrics, correspondence)
7. Student submits the grade appeal
8. System validates appeal is within the 15-day filing deadline
9. System creates appeal record with status "Filed" and assigns case number
10. System notifies the course Faculty of the appeal
11. Faculty reviews appeal and supporting evidence within 7 business days
12. Faculty responds with decision (agree to modify, deny with justification)
13. System records Faculty's response
14. If Faculty agrees to modify: flow proceeds to step 22
15. If Faculty denies: system notifies student of denial with Faculty's justification
16. Student requests escalation to Department Head
17. System forwards appeal and all documentation to Department Head
18. Department Head reviews within 7 business days and issues recommendation
19. If Department Head recommends modification: flow proceeds to step 22
20. If unresolved: system escalates to Academic Appeals Committee
21. Committee reviews all documentation and conducts hearing within 14 business days
22. Final decision is recorded (grade modified or original grade upheld)
23. If grade is modified, system updates grade in transcript
24. System recalculates student's semester GPA and cumulative GPA
25. System retains original grade in audit trail as immutable record
26. System notifies student, faculty, and department of final outcome
27. Use case ends

### Alternative Flows

**12a. Faculty agrees and modifies grade at first review**
1. Faculty reviews evidence and acknowledges error
2. Faculty submits grade modification through appeal system
3. System records modification with Faculty's justification
4. Flow proceeds to step 23

**21a. Committee orders re-examination**
1. Committee determines grade cannot be fairly assessed from existing evidence
2. Committee orders a re-examination or re-evaluation of student's work
3. System schedules re-examination and notifies student and faculty
4. Re-examination is conducted and new grade is assigned
5. Flow proceeds to step 23

**8a. Appeal deadline has passed**
1. System detects appeal is filed beyond the 15-day window
2. System displays error "Appeal deadline expired. Grade published on [date], deadline was [date]"
3. System suggests student contact the Dean's office for exceptional circumstances
4. Use case ends

### Special Requirements
- **Filing Deadline**: Appeals must be submitted within 15 calendar days of grade publication
- **Immutable Original Grade**: The original grade must never be deleted; it is retained in audit history
- **Audit Trail**: All actions, decisions, and communications are logged with timestamps and user IDs
- **Confidentiality**: Appeal details are visible only to involved parties

### Technology and Data Variations
- **Document Management**: Uploaded evidence stored securely with versioning
- **GPA Calculation**: Automatic recalculation triggered by any grade modification
- **Notification**: Email notifications with in-system tracking; escalation reminders sent if deadlines approach

### Frequency of Occurrence
Relatively infrequent; typically 1-5% of enrolled students file appeals per semester. Volume increases after fall and spring final grade publication.

### Open Issues
- Should there be a fee for filing an appeal to discourage frivolous submissions?
- Can a student appeal a grade after graduation if it affects honors eligibility?
- How should appeals for courses taught by adjunct faculty who have left the institution be handled?

---

## UC54: Post Faculty Job and Recruit

### Basic Information
- **Use Case ID**: UC54
- **Use Case Name**: Post Faculty Job and Recruit
- **Primary Actor**: HR Administrator
- **Secondary Actors**: Department Head, Interview Panel, Candidate
- **Stakeholders and Interests**:
  - HR Administrator: Wants streamlined recruitment workflow and compliance
  - Department Head: Wants qualified faculty hired for departmental needs
  - Interview Panel: Wants organized evaluation and comparison of candidates
  - Candidate: Wants transparent and timely application process
  - Institution: Wants quality hires within budget

### Preconditions
- HR Administrator is logged into the system
- Department has submitted a faculty hiring request
- Position budget has been allocated
- Job posting template and evaluation criteria are configured

### Postconditions

#### Success End Condition
- Position is filled with a qualified candidate
- Offer is accepted and background check is passed
- New faculty record is created in the HR system
- Onboarding process is initiated
- Position status is updated to "Filled"

#### Failure End Condition
- No suitable candidate found; position remains open or is cancelled
- Offer rejected by candidate; process restarts from shortlisting or posting
- Background check fails; offer is rescinded

### Main Success Scenario
1. HR Administrator navigates to the recruitment module
2. HR Administrator creates a new faculty position posting
3. System displays position form (title, department, qualifications, responsibilities, salary range)
4. HR Administrator fills in position details and required qualifications
5. HR Administrator submits position for budget approval
6. Department Head and Finance approve the budget allocation
7. System updates position status to "Approved"
8. HR Administrator sets application deadline and publishes the posting
9. System publishes job posting on the institution's career portal and configured job boards
10. Candidates submit applications through the portal (CV, cover letter, publications, references)
11. System stores applications and sends acknowledgment emails to candidates
12. Application deadline passes; system closes the posting for new submissions
13. System runs automated screening against minimum qualification criteria
14. System generates a ranked list of candidates meeting minimum requirements
15. HR Administrator and Department Head review screened applications
16. Committee shortlists candidates for interviews
17. System updates shortlisted candidates' status and sends interview invitations
18. HR Administrator schedules interviews (date, time, panel members, room)
19. System sends interview details to candidates and panel members
20. Interview panel conducts interviews and records evaluation scores
21. Panel submits consolidated evaluation with ranking and recommendation
22. HR Administrator and Department Head select the top candidate
23. HR Administrator generates and extends offer letter (salary, start date, terms)
24. System sends offer to candidate via email with acceptance deadline
25. Candidate accepts the offer through the portal
26. System initiates background verification process
27. Background check is completed successfully
28. System creates new faculty record in HR system
29. System initiates onboarding workflow (ID, email, system access, orientation schedule)
30. System updates position status to "Filled"
31. Use case ends

### Alternative Flows

**25a. Candidate rejects the offer**
1. Candidate declines the offer through the portal or via communication
2. System updates candidate status to "Offer Declined"
3. HR Administrator reviews remaining shortlisted candidates
4. If suitable alternate exists, flow returns to step 23
5. If no alternate, flow returns to step 8 (re-post) or position is cancelled
6. Use case ends

**27a. Background check fails**
1. Background verification reveals disqualifying information
2. System flags the candidate and notifies HR Administrator
3. HR Administrator rescinds the offer with documented reason
4. System updates candidate status to "Offer Rescinded"
5. Flow returns to step 22 to select alternate candidate
6. Use case ends

**6a. Position cancelled before posting**
1. Budget is not approved or department withdraws request
2. System updates position status to "Cancelled"
3. HR Administrator is notified
4. Use case ends

**24a. Offer acceptance deadline expires**
1. Candidate does not respond within the acceptance deadline
2. System updates candidate status to "Offer Expired"
3. System notifies HR Administrator
4. Flow returns to step 22 to select alternate candidate
5. Use case ends

### Special Requirements
- **Equal Opportunity**: System must ensure job postings comply with non-discrimination policies
- **Data Privacy**: Candidate personal data must be handled per data protection regulations
- **Panel Assignment**: Minimum 3 panel members required; system validates panel composition
- **Document Retention**: All applications and evaluation records retained per institutional policy

### Technology and Data Variations
- **Job Boards**: Integration with external job portals (LinkedIn, Indeed, academic job boards) via API
- **Video Interviews**: Support for virtual interview scheduling with video conferencing links
- **Evaluation Forms**: Configurable scoring rubrics per position type

### Frequency of Occurrence
Varies by institution size; typically 5-30 faculty positions posted per academic year. Recruitment cycles typically run 2-4 months each.

### Open Issues
- Should internal candidates receive preferential scoring or a separate track?
- How should failed searches (no suitable candidate) be documented and escalated?
- What is the policy for re-opening a position after a candidate rejects an offer?

---

## UC55: Manage Academic Session

### Basic Information
- **Use Case ID**: UC55
- **Use Case Name**: Manage Academic Session
- **Primary Actor**: Administrator
- **Secondary Actors**: Department Head, Faculty, Students
- **Stakeholders and Interests**:
  - Administrator: Wants to configure and manage the academic calendar efficiently
  - Department Head: Wants to plan course offerings within the session framework
  - Faculty: Wants clear semester dates for course planning and grade submission
  - Students: Want predictable academic schedule for registration and planning

### Preconditions
- Administrator is logged into the system with appropriate privileges
- Previous academic year data is available (if applicable)
- Institutional academic calendar policies are defined

### Postconditions

#### Success End Condition
- Academic year and semesters are created and configured
- Calendar dates (registration, classes, exams, grading) are set
- Course offerings are configured for each semester
- Semester lifecycle progresses through all stages and is archived

#### Failure End Condition
- Academic session configuration is incomplete
- Dependent processes (registration, grading) cannot proceed
- System reverts to draft state

### Main Success Scenario
1. Administrator navigates to academic session management
2. Administrator creates a new academic year (e.g., 2025-2026)
3. System generates academic year record with status "Draft"
4. Administrator creates semesters within the academic year (Fall, Spring, Summer)
5. For each semester, Administrator sets key calendar dates:
   - Registration start and end dates
   - Classes start and end dates
   - Add/drop deadline
   - Midterm examination period
   - Final examination period
   - Grade submission deadline
   - Results publication date
6. System validates date sequences (no overlaps, logical ordering)
7. Administrator publishes the academic calendar
8. System notifies Department Heads that session planning is open
9. Department Heads configure course offerings for each semester (courses, sections, faculty assignments)
10. Department Heads submit course offering plans for approval
11. Administrator reviews and approves course offerings
12. System opens registration window on the configured start date
13. Students register for courses during the registration period
14. System activates the semester on the classes start date
15. Semester progresses through instruction period
16. System activates exam period on configured exam start date
17. Examination period concludes
18. System opens grading period for faculty
19. Faculty submit grades before the submission deadline
20. System calculates academic standing for all students (good standing, probation, dismissal)
21. System publishes results on the configured publication date
22. Administrator reviews completion status and closes the semester
23. System archives semester data and updates student records
24. Use case ends

### Alternative Flows

**19a. Grade submission deadline extended**
1. Administrator determines faculty need additional time
2. Administrator extends grade submission deadline through the system
3. System updates calendar and notifies all faculty of the new deadline
4. Flow continues from step 19

**15a. Blackout period enforced**
1. Administrator declares a blackout period (holiday, emergency) during the semester
2. System blocks scheduling of classes and exams during the blackout window
3. System adjusts remaining calendar dates if needed
4. System notifies faculty and students of the schedule change
5. Flow continues from step 15

**14a. Emergency closure**
1. An emergency requires temporary campus closure (natural disaster, pandemic)
2. Administrator activates emergency closure mode
3. System suspends all active semester timelines
4. System notifies all users of the closure
5. When resolved, Administrator resumes or reconfigures semester dates
6. Flow continues from adjusted point in the semester lifecycle

### Special Requirements
- **Calendar Validation**: System must prevent overlapping or logically inconsistent dates
- **Cascading Updates**: Changes to academic dates must propagate to dependent schedules (exams, grading)
- **Multi-Year Support**: System must support planning multiple academic years in advance
- **Timezone Handling**: All dates stored in institutional timezone with UTC reference

### Technology and Data Variations
- **Calendar Export**: Support iCal export for students and faculty to sync with personal calendars
- **Academic Year Models**: Support semester, trimester, and quarter systems via configuration
- **Integration**: Sync academic calendar with LMS and communication systems

### Frequency of Occurrence
Academic year creation occurs once per year. Semester management occurs 2-4 times per year. Calendar adjustments may occur ad hoc throughout each semester.

### Open Issues
- Should the system support overlapping semesters (e.g., summer term overlapping with fall registration)?
- How should mid-semester program changes be handled in the academic calendar?
- What approval workflow is needed for calendar modifications after publication?

---

## UC56: Evaluate Transfer Credits

### Basic Information
- **Use Case ID**: UC56
- **Use Case Name**: Evaluate Transfer Credits
- **Primary Actor**: Registrar
- **Secondary Actors**: Student, Department Head
- **Stakeholders and Interests**:
  - Registrar: Wants to accurately evaluate and map transfer credits per institutional policy
  - Student: Wants maximum eligible credits transferred to reduce time to degree
  - Department Head: Wants to ensure transferred courses meet departmental standards
  - Institution: Wants consistent application of transfer policies

### Preconditions
- Student is admitted or enrolled as a transfer student
- Student has submitted official transcripts from previous institution(s)
- Transcripts have been verified as authentic
- Transfer credit policy and articulation agreements are configured in the system

### Postconditions

#### Success End Condition
- Transfer courses are evaluated and mapped to equivalent institutional courses
- Approved transfer credits are applied to student's degree audit
- Student's remaining degree requirements are updated
- Student is notified of evaluation results

#### Failure End Condition
- Transfer credits are denied with documented reasons
- Student's degree audit remains unchanged
- Student is notified of denial and appeal options

### Main Success Scenario
1. Registrar navigates to the transfer credit evaluation module
2. Registrar selects the transfer student's record
3. System displays submitted transcripts and previously evaluated credits (if any)
4. Registrar reviews each course from the source institution:
   - Course name, code, credit hours, and grade earned
5. Registrar checks existing articulation agreements for direct course equivalencies
6. System displays matching equivalencies from articulation database (if available)
7. Registrar maps each transfer course to an equivalent institutional course
8. System validates the mapping (credit hours, course level compatibility)
9. Registrar applies transfer rules:
   - Maximum 40% of total degree credits may be transferred
   - Minimum grade of B required for transfer eligibility
   - Course must have been completed within the last 7 years
10. System calculates total transfer credits against the 40% cap
11. Registrar approves eligible courses and rejects ineligible ones with documented reasons
12. Registrar submits the evaluation
13. System applies approved transfer credits to the student's academic record
14. System updates the student's degree audit to reflect transferred courses
15. System recalculates remaining degree requirements
16. System sends notification to student with evaluation results (approved courses, denied courses with reasons)
17. Use case ends

### Alternative Flows

**6a. No direct equivalent exists — partial credit considered**
1. Registrar cannot find a direct institutional equivalent for the course
2. Registrar consults with the relevant Department Head
3. Department Head reviews course syllabus and recommends:
   - Accept as elective credit
   - Accept as partial fulfillment of a requirement
   - Deny transfer
4. Registrar records the recommendation and decision
5. Flow continues from step 9

**11a. Student appeals denied credits**
1. Student reviews evaluation results and disagrees with a denial
2. Student submits appeal with additional documentation (syllabus, course description)
3. Registrar and Department Head review appeal
4. Decision is updated if appeal is approved
5. System updates degree audit accordingly
6. Use case ends

**10a. Transfer credits exceed the 40% maximum**
1. System detects that approved credits would exceed the transfer limit
2. System warns Registrar of the overage
3. Registrar prioritizes which credits to accept (core courses first, then electives)
4. Registrar adjusts approvals to fit within the cap
5. Flow continues from step 11

### Special Requirements
- **Articulation Database**: Maintain a searchable database of pre-approved course equivalencies
- **Policy Enforcement**: System must enforce transfer rules (40% cap, minimum B grade, recency)
- **Documentation**: All evaluation decisions must include justification and be stored permanently
- **Transcript Verification**: Only officially verified transcripts are eligible for evaluation

### Technology and Data Variations
- **Transcript Formats**: Support electronic transcripts (EDI/XML) and scanned paper transcripts
- **Articulation Agreements**: Import/export agreements with partner institutions in bulk
- **Course Catalog Matching**: Fuzzy matching algorithm to suggest potential equivalencies

### Frequency of Occurrence
Occurs each admission cycle for transfer students. Typically 5-20% of incoming students are transfers. Each evaluation involves 5-15 courses on average.

### Open Issues
- Should credits from international institutions require additional validation (WES, NACES)?
- How should pass/fail courses from the source institution be handled?
- Should the 7-year recency rule be waived for returning adult learners?

---

## UC57: Process Scholarship Application

### Basic Information
- **Use Case ID**: UC57
- **Use Case Name**: Process Scholarship Application
- **Primary Actor**: Financial Aid Administrator
- **Secondary Actors**: Student, System
- **Stakeholders and Interests**:
  - Student: Wants financial assistance to fund education
  - Financial Aid Administrator: Wants efficient and fair scholarship allocation
  - Institution: Wants to distribute scholarship funds equitably and within budget
  - Donors: Want scholarship criteria honored and funds used as intended

### Preconditions
- Student is logged into the system and is currently enrolled
- Scholarship programs are configured with eligibility criteria and fund amounts
- Scholarship application period is open
- Financial Aid Administrator has appropriate permissions

### Postconditions

#### Success End Condition
- Scholarship application is processed and award decision is made
- Awarded scholarship is disbursed (fee adjustment or stipend)
- Student's financial record is updated
- Renewal criteria are set for ongoing scholarships

#### Failure End Condition
- Application is rejected due to ineligibility or fund depletion
- Student is notified of rejection with reasons
- No financial adjustment is made

### Main Success Scenario
1. Student navigates to the scholarship section
2. System displays available scholarships with eligibility criteria and deadlines
3. Student browses scholarships and selects one to view details
4. System displays scholarship details (amount, criteria, required documents, deadline)
5. Student checks eligibility against displayed criteria
6. System runs automated eligibility check (GPA, enrollment status, financial need, demographics)
7. System confirms student meets basic eligibility requirements
8. Student fills in scholarship application form
9. Student uploads required documents (income certificate, essays, recommendation letters)
10. Student submits the scholarship application
11. System validates completeness of application and required documents
12. System creates application record with status "Submitted"
13. Financial Aid Administrator reviews submitted applications
14. Administrator verifies supporting documents and student records
15. System calculates a scoring/ranking based on configured criteria (GPA weight, need weight, essay score)
16. Administrator reviews ranked list and makes award decisions
17. Administrator approves scholarship award for selected students
18. System determines disbursement method:
    - Fee adjustment (reduces outstanding balance)
    - Stipend (direct payment to student)
19. System applies fee adjustment or queues stipend payment
20. System updates student's financial aid record
21. System sends award notification to student with scholarship details and conditions
22. System sets renewal check criteria for each subsequent semester (maintain GPA, enrollment status)
23. Use case ends

### Alternative Flows

**6a. Auto-awarded merit scholarship**
1. System identifies students meeting automatic merit criteria (e.g., GPA ≥ 3.8)
2. System automatically generates scholarship awards without application
3. Administrator reviews and approves auto-awards in bulk
4. Flow continues from step 18

**16a. Scholarship fund depleted**
1. Total requested awards exceed available fund balance
2. System warns Administrator of remaining balance
3. Administrator adjusts award amounts or selects fewer recipients
4. Waitlisted students are notified of fund exhaustion
5. Use case ends

**22a. Scholarship revoked due to GPA drop**
1. System runs semester-end renewal check
2. Student's GPA falls below the required threshold
3. System flags the student for scholarship review
4. Administrator reviews and confirms revocation
5. System updates scholarship status to "Revoked" and notifies student
6. System adjusts future semester billing accordingly
7. Use case ends

**10a. Multiple scholarships with stacking rules**
1. Student has applied for or received multiple scholarships
2. System checks stacking rules (some scholarships cannot be combined)
3. System displays stacking conflicts to Administrator
4. Administrator resolves conflicts (student chooses or system applies highest value)
5. Flow continues from step 17

### Special Requirements
- **Fair Allocation**: Scholarship criteria and scoring must be transparent and auditable
- **Fund Tracking**: System must track remaining balance per scholarship fund in real time
- **Stacking Rules**: Configurable rules for combining multiple scholarships
- **Renewal Automation**: Automatic semester-end eligibility check for renewal scholarships

### Technology and Data Variations
- **Need Analysis**: Integration with financial need assessment tools or FAFSA equivalent
- **Disbursement**: Fee adjustment integrated with finance module; stipend via bank transfer or check
- **Reporting**: Generate scholarship utilization reports for donors and institutional leadership

### Frequency of Occurrence
Scholarship cycles occur 2-4 times per year (once per semester plus special cycles). Application volumes vary from dozens to hundreds per cycle depending on available scholarships.

### Open Issues
- Should scholarship awards be visible on the student's public profile or transcript?
- How should mid-semester enrollment changes (drop below full-time) affect active scholarships?
- What appeals process exists for students denied a scholarship?

---

## UC58: Book and Manage Room

### Basic Information
- **Use Case ID**: UC58
- **Use Case Name**: Book and Manage Room
- **Primary Actor**: Faculty/Staff
- **Secondary Actors**: Facility Manager, Administrator
- **Stakeholders and Interests**:
  - Faculty/Staff: Wants convenient room reservation for meetings, events, and classes
  - Facility Manager: Wants efficient room utilization and conflict-free scheduling
  - Administrator: Wants oversight of institutional space usage
  - Students: Want events and classes held in appropriate spaces

### Preconditions
- User (Faculty/Staff) is logged into the system
- Rooms and their attributes (capacity, amenities, location) are configured in the system
- Room availability calendar is up to date
- User has permission to book rooms (or request approval for restricted spaces)

### Postconditions

#### Success End Condition
- Room is booked and confirmed for the requested date/time
- Booking appears on the room's calendar
- User and relevant parties receive confirmation notification
- Room is released after the event/booking period ends

#### Failure End Condition
- Booking is rejected due to conflict, policy violation, or denial of approval
- User is notified of rejection with alternative suggestions
- Room calendar remains unchanged

### Main Success Scenario
1. User navigates to the room booking section
2. User enters search criteria (date, time range, minimum capacity, required amenities)
3. System searches available rooms matching the criteria
4. System displays list of available rooms with details (name, building, floor, capacity, amenities, photos)
5. User selects a room from the available list
6. System displays the room's detailed calendar for the requested date
7. User fills in booking details (event name, description, expected attendees, setup requirements)
8. User submits the booking request
9. System checks for scheduling conflicts with existing bookings
10. System confirms no conflicts exist
11. System creates booking record with status "Confirmed"
12. System updates the room's availability calendar
13. System sends confirmation notification to the user via email
14. System sends notification to Facility Manager for resource preparation
15. Event occurs at the booked time
16. System marks booking as "Completed" after the end time passes
17. Use case ends

### Alternative Flows

**9a. Scheduling conflict detected**
1. System detects the room is already booked for the requested time
2. System displays conflict details and suggests alternative available time slots
3. System also suggests other available rooms matching the user's criteria
4. User selects an alternative or cancels the request
5. If alternative selected, flow returns to step 7

**8a. Recurring booking requested**
1. User selects "Recurring Booking" option
2. User specifies recurrence pattern (daily, weekly, biweekly) and end date
3. System checks availability for all recurring dates
4. System displays any dates with conflicts
5. User confirms bookings for conflict-free dates and adjusts conflicting ones
6. System creates booking records for all confirmed dates
7. Flow continues from step 11

**11a. Approval required for special spaces (auditorium, lab, conference hall)**
1. System identifies the room requires administrative approval
2. System creates booking request with status "Pending Approval"
3. System notifies the Facility Manager or Administrator
4. Approver reviews the request and approves or denies
5. If approved, flow continues from step 11
6. If denied, system notifies the user with reason and alternative suggestions
7. Use case ends

**12a. User cancels an existing booking**
1. User navigates to "My Bookings" and selects a booking to cancel
2. System prompts for cancellation reason
3. User confirms cancellation
4. System updates booking status to "Cancelled"
5. System frees the room on the availability calendar
6. System notifies Facility Manager of the cancellation
7. Use case ends

**9b. Maintenance conflict**
1. System detects the room is scheduled for maintenance during the requested time
2. System displays maintenance window and suggests alternative rooms or times
3. User selects an alternative
4. Flow returns to step 7

### Special Requirements
- **Real-Time Availability**: Room calendar must reflect bookings in real time to prevent double-booking
- **Amenity Filtering**: Support filtering by projector, whiteboard, video conferencing, AC, accessibility
- **Cancellation Policy**: Bookings can be cancelled up to 24 hours before the scheduled time
- **Capacity Enforcement**: System must prevent booking a room with capacity less than expected attendees

### Technology and Data Variations
- **Calendar Integration**: Support iCal/Google Calendar sync for booked rooms
- **Digital Signage**: Integration with room display panels showing current and next booking
- **QR Code Check-in**: Optional check-in via QR code at the room door to confirm occupancy

### Frequency of Occurrence
High frequency; dozens to hundreds of bookings per week depending on institution size. Peak usage during semester start, exam periods, and event seasons.

### Open Issues
- Should no-show bookings (unoccupied rooms) be automatically released after a grace period?
- How should priority conflicts between academic and administrative bookings be resolved?
- Should students be allowed to book rooms for study groups or club activities?

---

## Summary

This document provides detailed use case descriptions for 13 critical use cases in the EMIS system:

1. **UC14: Register for Courses** - Student course enrollment workflow
2. **UC17: Enter Grades** - Faculty grade submission process
3. **UC28: Pay Fees** - Student fee payment with gateway integration
4. **UC10: Review Applications** - Admissions application evaluation
5. **UC22: Upload Course Content** - LMS content management
6. **UC51: Apply for Graduation** - Degree conferral and diploma generation
7. **UC52: Report and Process Disciplinary Case** - Conduct violation investigation and hearing
8. **UC53: Submit Grade Appeal** - Grade dispute resolution with escalation
9. **UC54: Post Faculty Job and Recruit** - Faculty hiring and onboarding workflow
10. **UC55: Manage Academic Session** - Academic year and semester lifecycle management
11. **UC56: Evaluate Transfer Credits** - Transfer credit evaluation and mapping
12. **UC57: Process Scholarship Application** - Financial aid application and disbursement
13. **UC58: Book and Manage Room** - Room reservation and facility scheduling

Each use case follows the standard template with:
- Basic information and actors
- Preconditions and postconditions
- Main success scenario (happy path)
- Alternative flows (exceptions and variations)
- Special requirements
- Frequency and open issues

These detailed descriptions serve as specifications for development and test case creation.
