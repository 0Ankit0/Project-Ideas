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

## Summary

This document provides detailed use case descriptions for 5 critical use cases in the EMIS system:

1. **UC14: Register for Courses** - Student course enrollment workflow
2. **UC17: Enter Grades** - Faculty grade submission process
3. **UC28: Pay Fees** - Student fee payment with gateway integration
4. **UC10: Review Applications** - Admissions application evaluation
5. **UC22: Upload Course Content** - LMS content management

Each use case follows the standard template with:
- Basic information and actors
- Preconditions and postconditions
- Main success scenario (happy path)
- Alternative flows (exceptions and variations)
- Special requirements
- Frequency and open issues

These detailed descriptions serve as specifications for development and test case creation.
