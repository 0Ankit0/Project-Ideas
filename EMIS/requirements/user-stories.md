# EMIS - User Stories

## Epic 1: User Management & Authentication

### US-1.1: User Registration
**As a** system administrator  
**I want to** register new users with appropriate roles  
**So that** they can access the system based on their responsibilities

**Acceptance Criteria:**
- Admin can create users with roles: Student, Faculty, Staff, Parent, Admin
- Email and username must be unique
- Password must meet complexity requirements
- User receives welcome email with credentials

### US-1.2: Secure Login
**As a** system user  
**I want to** securely log in to the system  
**So that** I can access my personalized dashboard

**Acceptance Criteria:**
- Users can log in with username/email and password
- Invalid credentials show appropriate error message
- Account locks after 5 failed attempts
- Successful login redirects to role-based dashboard

### US-1.3: Role-Based Access Control
**As a** system administrator  
**I want to** configure granular permissions for different roles  
**So that** users only access features relevant to their responsibilities

**Acceptance Criteria:**
- Permissions can be assigned at module and feature level
- Users see only authorized menu items
- Unauthorized access attempts are logged and blocked
- Super admin can override all permissions

## Epic 2: Student Management

### US-2.1: Student Enrollment
**As an** admissions officer  
**I want to** enroll accepted applicants as students  
**So that** they can begin their academic journey

**Acceptance Criteria:**
- System auto-generates unique student ID (STU-YYYY-XXXXX)
- Student is linked to accepted application
- Program, batch, and semester are assigned
- Student portal access is created automatically

### US-2.2: Student Profile Management
**As a** student  
**I want to** view and update my profile information  
**So that** the institution has my current details

**Acceptance Criteria:**
- Students can update contact information and emergency contacts
- Students cannot modify academic information (program, batch)
- Profile changes are logged for audit
- Parents can view student profile but not edit

### US-2.3: Academic Progress Tracking
**As a** faculty advisor  
**I want to** view student academic progress  
**So that** I can provide appropriate guidance

**Acceptance Criteria:**
- View current and past semester enrollments
- See grades, GPA, and credit hours completed
- Track attendance percentage
- Identify at-risk students based on performance

### US-2.4: Student Status Management
**As a** department head  
**I want to** update student academic status  
**So that** records accurately reflect current standing

**Acceptance Criteria:**
- Can change status: Active, On Leave, Graduated, Withdrawn, Suspended, Expelled
- Status change requires reason/notes
- Automated workflows trigger (e.g., deactivate enrollment on graduation)
- Status history is maintained

## Epic 3: Admissions

### US-3.1: Online Application Submission
**As a** prospective student  
**I want to** submit my application online  
**So that** I can apply without visiting campus

**Acceptance Criteria:**
- Multi-step application form with validation
- Upload required documents (transcripts, ID, photos)
- Application number generated upon submission
- Confirmation email sent to applicant

### US-3.2: Application Review Workflow
**As an** admissions officer  
**I want to** review and process applications systematically  
**So that** decisions are made efficiently and fairly

**Acceptance Criteria:**
- Applications routed based on program
- Status tracking: Submitted, Under Review, Shortlisted, Rejected, Accepted
- Comments and notes can be added
- Bulk actions for application processing

### US-3.3: Merit List Generation
**As an** admissions director  
**I want to** generate merit lists based on criteria  
**So that** selection is transparent and merit-based

**Acceptance Criteria:**
- Configure ranking criteria (test scores, grades, etc.)
- Generate ranked list automatically
- Export merit list for publication
- Send acceptance/rejection emails automated emails in bulk

### US-3.4: Admission Cycle Configuration
**As an** admin  
**I want to** configure and publish admission cycles with open/close dates  
**So that** prospective students can apply within the designated window

**Acceptance Criteria:**
- Set admission open and close dates per program
- Configure program-wise seat limits and eligibility criteria
- Publish admission cycle to make it visible on the public portal
- Only one admission cycle active per program at a time

### US-3.5: Public Admission Notice
**As a** prospective student  
**I want to** see admission open notices on the public portal  
**So that** I can apply to the college during the admission window

**Acceptance Criteria:**
- Admission open notice displayed on external-facing portal
- Notice visible only to non-enrolled prospective users
- Shows program details, seat availability, and application deadline
- Direct link to online application form

### US-3.6: Entrance Examination Configuration
**As an** admin  
**I want to** configure entrance examinations with question banks and auto-scoring  
**So that** applicants can be evaluated fairly and efficiently

**Acceptance Criteria:**
- Create entrance exam with question bank, time limit, and passing criteria
- Support auto-scoring for objective questions
- Schedule exam for applicants who submitted applications
- Record scores per applicant for merit list generation

### US-3.7: Auto-Generate Merit List
**As an** admin  
**I want to** the system to auto-generate merit lists from entrance exam scores  
**So that** applicants are ranked transparently based on their performance

**Acceptance Criteria:**
- Generate ranked merit list from entrance exam/interview scores
- Support configurable weightage for different scoring criteria
- Publish merit list for applicant visibility
- All exam scores must be finalized before merit list generation

### US-3.8: Scholarship Auto-Award Configuration
**As an** admin  
**I want to** configure scholarship auto-award rules linked to the merit list  
**So that** scholarships are awarded automatically to top-performing applicants

**Acceptance Criteria:**
- Configure how many top merit-list students receive scholarships
- Set scholarship amount and type (fixed per semester or full coverage for N semesters)
- System auto-awards scholarships to top N students upon admin confirmation
- Student must not already hold a scholarship for the same program

### US-3.9: Applicant-to-Student Conversion
**As an** admissions staff member  
**I want to** a dedicated page to convert accepted applicants to students after verifying all bills are cleared  
**So that** the enrollment process is streamlined and error-free

**Acceptance Criteria:**
- Dedicated conversion interface on management dashboard
- System validates all account section bills are cleared (zero outstanding)
- System verifies all required documents are verified
- System checks offer letter has been accepted
- Conversion blocked if any validation fails with clear error message
- Upon conversion, student record is created and applicant status updated

## Epic 4: Course & Program Management

### US-4.1: Program Definition
**As an** academic dean  
**I want to** define degree programs with curriculum  
**So that** students follow structured learning paths

**Acceptance Criteria:**
- Create program with name, code, duration, degree type
- Define program semesters and required courses
- Set credit hour requirements for graduation
- Configure prerequisite chains

### US-4.2: Course Catalog Management
**As a** department head  
**I want to** manage course catalog  
**So that** course offerings are up-to-date

**Acceptance Criteria:**
- Create/edit courses with code, credits, description
- Set course prerequisites and corequisites
- Mark courses as elective or required
- Define maximum enrollment capacity

### US-4.3: Course Registration
**As a** student  
**I want to** register for courses each semester  
**So that** I can build my class schedule

**Acceptance Criteria:**
- View available courses and sections
- Check prerequisite requirements automatically
- Add courses to cart and confirm registration
- Get error if course is full or has conflicts

### US-4.4: Add/Drop Courses
**As a** student  
**I want to** modify my course registration during add/drop period  
**So that** I can adjust my course load

**Acceptance Criteria:**
- Drop courses before deadline without penalty
- Add courses if seats available
- Financial adjustments applied automatically
- Transcript shows dropped courses with appropriate marking

## Epic 5: Timetable & Scheduling

### US-5.1: Class Schedule Creation
**As a** timetable coordinator  
**I want to** create conflict-free class schedules  
**So that** faculty and students can attend all their classes

**Acceptance Criteria:**
- Assign courses to time slots and rooms
- Detect and prevent conflicts (faculty, room, student)
- View schedules by faculty, room, or section
- Publish timetables to students and faculty

### US-5.2: Room Management
**As a** facility manager  
**I want to** manage room inventory and allocation  
**So that** classes are assigned appropriate venues

**Acceptance Criteria:**
- Define rooms with capacity and facilities (projector, lab equipment)
- Check room availability before assignment
- Handle room conflicts and double-booking alerts
- Generate room utilization reports

## Epic 6: Exams & Grading

### US-6.1: Exam Scheduling
**As an** exam controller  
**I want to** schedule exams with optimal spacing  
**So that** students have adequate preparation time

**Acceptance Criteria:**
- Create exam calendar with dates and times
- Assign exam venues with invigilation
- Avoid scheduling conflicts for students
- Publish exam schedule to all stakeholders

### US-6.2: Grade Entry
**As a** faculty member  
**I want to** enter grades for my courses  
**So that** students receive timely feedback

**Acceptance Criteria:**
- View enrolled students for my courses
- Enter numerical or letter grades
- Submit grades before deadline
- Grades locked after submission (requires approval to change)

### US-6.3: GPA Calculation
**As a** student  
**I want to** see my GPA calculated automatically  
**So that** I can track my academic performance

**Acceptance Criteria:**
- Semester GPA calculated from current semester grades
- Cumulative GPA includes all semesters
- GPA calculation follows institution's grading scale
- Transcript shows both semester and cumulative GPA

### US-6.4: Transcript Generation
**As a** student  
**I want to** download my official transcript  
**So that** I can apply for jobs or further education

**Acceptance Criteria:**
- Transcript shows all completed courses and grades
- Includes GPA, credits earned, and degree awarded (if graduated)
- PDF format with institution branding
- Digital signature/watermark for authenticity

## Epic 7: Attendance Management

### US-7.1: Daily Attendance Marking
**As a** faculty member  
**I want to** mark attendance for my classes  
**So that** attendance records are maintained

**Acceptance Criteria:**
- View class roster with enrolled students
- Mark present/absent/late for each student
- Edit attendance within 24 hours
- Attendance auto-syncs to student records

### US-7.2: Attendance Reports
**As a** faculty member  
**I want to** view attendance summaries for my students  
**So that** I can identify habitual absentees

**Acceptance Criteria:**
- View attendance percentage per student
- Filter by date range or course
- Export attendance reports
- Flag students below minimum attendance requirement

### US-7.3: Leave Application
**As a** student  
**I want to** apply for leave online  
**So that** my absence is recorded as authorized

**Acceptance Criteria:**
- Submit leave application with dates and reason
- Attach supporting documents (medical certificate)
- Faculty approves/rejects leave
- Approved leave doesn't count toward absence

## Epic 8: Learning Management System (LMS)

### US-8.1: Course Content Upload
**As a** faculty member  
**I want to** upload course materials  
**So that** students can access learning resources

**Acceptance Criteria:**
- Upload PDFs, videos, presentations
- Organize content by modules/weeks
- Set visibility and access permissions
- Students notified when new content is added

### US-8.2: Assignment Submission
**As a** student  
**I want to** submit assignments online  
**So that** I don't need to physically submit coursework

**Acceptance Criteria:**
- View assignment details and deadline
- Upload submission files (multiple formats supported)
- Receive confirmation of submission
- Late submissions flagged automatically

### US-8.3: Assignment Grading
**As a** faculty member  
**I want to** grade submitted assignments  
**So that** students receive feedback on their work

**Acceptance Criteria:**
- View all submissions for an assignment
- Download submissions in bulk
- Enter grades and comments
- Students notified when grades are released

### US-8.4: Discussion Forums
**As a** student  
**I want to** participate in course discussion forums  
**So that** I can collaborate with peers and ask questions

**Acceptance Criteria:**
- Create new discussion threads
- Reply to existing discussions
- Faculty can moderate and pin important threads
- Email notifications for new replies

### US-8.5: Online Quizzes
**As a** faculty member  
**I want to** create and administer online quizzes  
**So that** I can assess student understanding

**Acceptance Criteria:**
- Create quiz with multiple question types (MCQ, True/False, Short Answer)
- Set time limit and attempt restrictions
- Auto-grading for objective questions
- Results available immediately after submission

## Epic 9: Finance & Fee Management

### US-9.1: Fee Structure Configuration
**As a** finance administrator  
**I want to** define fee structures for different programs  
**So that** students are charged correctly

**Acceptance Criteria:**
- Create fee heads (tuition, lab, library, hostel)
- Set amounts per program, semester, or course
- Configure installment plans
- Apply discounts and scholarships

### US-9.2: Fee Collection
**As a** student  
**I want to** pay my fees online  
**So that** I can avoid payment in-person

**Acceptance Criteria:**
- View outstanding fee balance
- Pay via multiple payment methods (card, bank transfer, gateway)
- Download payment receipt immediately
- Balance updated in real-time

### US-9.3: Fee Reminders
**As a** finance officer  
**I want to** send automated fee payment reminders  
**So that** students pay on time

**Acceptance Criteria:**
- Reminders sent at configurable intervals (7 days, 3 days, 1 day before due)
- Reminders via email and SMS
- Stop reminders once payment is received
- Escalation reminders for overdue payments

### US-9.4: Financial Reporting
**As a** finance director  
**I want to** generate financial reports  
**So that** I can monitor institutional finances

**Acceptance Criteria:**
- Revenue reports by program, semester, fee type
- Outstanding dues report
- Payment collection trends
- Export reports to Excel for further analysis

## Epic 10: Library Management

### US-10.1: Book Catalog Management
**As a** librarian  
**I want to** manage the library catalog  
**So that** users can discover available resources

**Acceptance Criteria:**
- Add books with ISBN, title, author, publisher, category
- Track multiple copies of the same book
- Mark books as available, issued, or damaged
- Search catalog by title, author, ISBN, or keywords

### US-10.2: Book Issuance
**As a** student  
**I want to** borrow books from the library  
**So that** I can use them for study

**Acceptance Criteria:**
- Search and reserve books online
- Librarian issues book and sets due date
- System tracks borrowed books per user
- Enforce borrowing limits (e.g., max 3 books)

### US-10.3: Book Return & Fines
**As a** librarian  
**I want to** process book returns and calculate fines  
**So that** books are returned on time

**Acceptance Criteria:**
- Mark book as returned
- Auto-calculate fine for overdue books
- Add fine to student account
- Send return reminders before due date

## Epic 11: HR Management

### US-11.1: Employee Onboarding
**As an** HR manager  
**I want to** onboard new employees systematically  
**So that** all paperwork is completed efficiently

**Acceptance Criteria:**
- Create employee profile with personal and professional details
- Generate employee ID automatically
- Upload documents (resume, ID proof, certificates)
- Assign department and reporting manager

### US-11.2: Payroll Processing
**As an** HR officer  
**I want to** process monthly payroll  
**So that** employees are paid accurately and on time

**Acceptance Criteria:**
- Define salary components (basic, allowances, deductions)
- Calculate net salary based on attendance and leaves
- Generate payslips in PDF format
- Export payroll data for bank transfer

### US-11.3: Leave Management
**As an** employee  
**I want to** apply for leave online  
**So that** my leave is tracked officially

**Acceptance Criteria:**
- View leave balance (casual, sick, earned)
- Submit leave application with dates and type
- Manager approves/rejects leave
- Approved leave deducted from balance

## Epic 12: Hostel Management

### US-12.1: Room Allocation
**As a** hostel warden  
**I want to** allocate rooms to students  
**So that** accommodation is managed efficiently

**Acceptance Criteria:**
- View available rooms by hostel and floor
- Assign students to rooms based on gender and program
- Track room occupancy and capacity
- Generate room allocation lists

### US-12.2: Mess Management
**As a** student  
**I want to** opt in/out of mess services  
**So that** I'm charged appropriately

**Acceptance Criteria:**
- Select mess plan (full board, breakfast only, none)
- View monthly mess menu
- Provide feedback on food quality
- Mess charges reflected in fee statement

## Epic 13: Transport Management

### US-13.1: Route Management
**As a** transport manager  
**I want to** define transport routes and stops  
**So that** students know pickup/drop points

**Acceptance Criteria:**
- Create routes with multiple stops and timings
- Assign vehicles and drivers to routes
- View route maps
- Publish routes to students

### US-13.2: Transport Allocation
**As a** student  
**I want to** apply for transport facility  
**So that** I can commute to campus

**Acceptance Criteria:**
- Submit transport application with preferred pickup point
- Administrator approves and assigns route
- Transport fee added to student account
- Receive bus pass/ID

## Epic 14: Notifications & Communication

### US-14.1: Announcement Broadcasting
**As an** administrator  
**I want to** send announcements to all users or specific groups  
**So that** important information reaches everyone

**Acceptance Criteria:**
- Create announcement with title and body
- Select target audience (all, students, faculty, by program/batch)
- Schedule announcement or send immediately
- Delivery via email, SMS, and in-app notification

### US-14.2: Event Notifications
**As a** student  
**I want to** receive notifications about upcoming events  
**So that** I don't miss important deadlines

**Acceptance Criteria:**
- Automated notifications for exam schedules, assignment deadlines, fee due dates
- Customizable notification preferences
- Mark notifications as read
- View notification history

## Epic 15: Analytics & Reporting

### US-15.1: Student Performance Analytics
**As an** academic dean  
**I want to** analyze student performance trends  
**So that** I can identify areas for improvement

**Acceptance Criteria:**
- View GPA distribution across programs and batches
- Identify top performers and at-risk students
- Track pass/fail rates by course
- Visualize trends over semesters

### US-15.2: Attendance Analytics
**As a** program coordinator  
**I want to** analyze attendance patterns  
**So that** I can improve student engagement

**Acceptance Criteria:**
- View average attendance by course and batch
- Identify courses with low attendance
- Track individual student attendance trends
- Generate attendance compliance reports

### US-15.3: Custom Report Builder
**As a** data analyst  
**I want to** create custom reports with filters  
**So that** I can answer specific questions

**Acceptance Criteria:**
- Select data source (students, courses, finance)
- Apply filters (date range, program, status)
- Choose columns and grouping
- Export report in PDF/Excel format

## Epic 16: Content Management & Portal

### US-16.1: Website Content Management
**As a** marketing officer  
**I want to** update website content without technical help  
**So that** information stays current

**Acceptance Criteria:**
- Edit pages using WYSIWYG editor
- Upload images and documents
- Publish/unpublish content
- Preview changes before publishing

### US-16.2: Student Portal
**As a** student  
**I want to** access all my information in one place  
**So that** I have a centralized hub

**Acceptance Criteria:**
- Dashboard shows upcoming classes, assignments, and notifications
- Quick links to common tasks (register courses, pay fees, check grades)
- Personalized content based on student profile
- Mobile-responsive design

### US-16.3: Parent Portal
**As a** parent  
**I want to** monitor my child's academic progress  
**So that** I can support their education

**Acceptance Criteria:**
- View student's grades and GPA
- Check attendance records
- See fee payment status
- Receive notifications about important events

## Epic 17: Inventory Management

### US-17.1: Asset Tracking
**As an** inventory manager  
**I want to** track all institutional assets  
**So that** equipment is accounted for

**Acceptance Criteria:**
- Register assets with unique ID, category, location, value
- Track asset status (available, in-use, under-maintenance, disposed)
- Assign assets to departments/users
- Generate asset registers and depreciation reports

### US-17.2: Stock Management
**As a** store keeper  
**I want to** manage consumable inventory  
**So that** stock levels are maintained

**Acceptance Criteria:**
- Track stock items (stationery, lab supplies)
- Record stock inward and outward movements
- Set reorder levels and get low-stock alerts
- Generate stock valuation reports

## Epic 18: Academic Session & Semester Management

### US-18.1: Create Academic Year
**As an** administrator  
**I want to** create and configure academic years with semesters  
**So that** all academic operations are organized within defined time periods

**Acceptance Criteria:**
- Create academic year with name, start date, end date
- Define semesters within the year (Fall, Spring, Summer)
- Set registration windows, add/drop deadlines, grading periods per semester
- Configure blackout periods for maintenance and exams
- Activate/deactivate semesters
- Only one academic year can be ACTIVE at a time

### US-18.2: Manage Semester Course Offerings
**As a** department head  
**I want to** configure which courses are offered each semester  
**So that** students can plan their registration

**Acceptance Criteria:**
- Select courses from the catalog to offer in a semester
- Define number of sections per course
- Assign faculty to course sections
- Set room and time slot assignments
- Publish course offerings to students
- Carry forward offerings from previous semesters as template

### US-18.3: Close Academic Semester
**As an** administrator  
**I want to** close a semester after all grades are submitted  
**So that** results are finalized and the semester is archived

**Acceptance Criteria:**
- Verify all grades submitted for all course sections
- Flag courses with missing grades and notify responsible faculty
- Trigger GPA/CGPA recalculation for all enrolled students
- Determine academic standing for each student
- Publish semester results
- Archive semester data and prevent further modifications
- Generate semester-end reports (pass/fail rates, GPA distribution)

### US-18.4: Semester Progression Assignment
**As an** admin  
**I want to** assign students to specific semesters (next or repeat) after a semester ends  
**So that** I can control semester progression based on each student's academic performance

**Acceptance Criteria:**
- View list of students eligible for semester progression
- Select next semester or repeat previous semester for each student
- System does not auto-progress students; admin must explicitly assign
- Bulk assignment option for students progressing to the same semester

### US-18.5: Classroom Enrollment Assignment
**As an** admin  
**I want to** enroll students in classrooms during semester assignment  
**So that** each student has a designated section for the semester

**Acceptance Criteria:**
- Assign students to specific classrooms/sections during enrollment
- Classroom assignment is mandatory; enrollment blocked without it
- View classroom capacity and current enrollment count
- Support bulk classroom assignment

### US-18.6: Faculty-to-Subject Assignment
**As a** department head  
**I want to** assign faculty to subjects per classroom per semester  
**So that** teaching responsibilities are clear and there are no scheduling conflicts

**Acceptance Criteria:**
- Assign faculty members to subjects for specific classrooms
- System checks faculty teaching load does not exceed maximum credit hours
- System detects timetable conflicts with other assigned subjects
- Faculty assignment persists for the entire semester

### US-18.7: Semester Repeat for Failed Students
**As an** admin  
**I want to** allow students who failed exams to repeat the previous semester with my approval  
**So that** they get a second chance to meet academic requirements

**Acceptance Criteria:**
- Identify students who failed one or more courses or had attendance issues
- Admin can approve semester repeat with documented reason
- Student is re-enrolled in the previous semester's courses
- Academic records clearly indicate repeated semester

## Epic 19: Graduation & Degree Conferral

### US-19.1: Apply for Graduation
**As a** student  
**I want to** apply for graduation when I've met all requirements  
**So that** my degree can be conferred

**Acceptance Criteria:**
- View degree audit showing completed vs remaining requirements
- Submit graduation application during graduation application window
- System verifies: total credits, required courses, minimum GPA, no holds, no pending grades
- Application routed to department for verification
- Track application status (Submitted, Under Review, Approved, Rejected)
- Receive notification of approval/rejection with reasons

### US-19.2: Conduct Degree Audit
**As a** registrar  
**I want to** run degree audits for graduating students  
**So that** only eligible students receive degrees

**Acceptance Criteria:**
- Automated check of all program requirements against student transcript
- Identify missing courses, insufficient credits, GPA shortfalls
- Handle course substitutions and transfer credits in audit
- Generate audit report with pass/fail status for each requirement
- Batch audit for all applicants in a graduation cycle
- Override capability for exceptional cases with approval chain

### US-19.3: Generate Diploma and Credentials
**As a** registrar  
**I want to** generate diplomas and digital credentials for graduates  
**So that** students receive official proof of their degrees

**Acceptance Criteria:**
- Generate diploma PDF with student name, program, honors, date
- Assign unique diploma number for verification
- Generate digital credential with QR code for online verification
- Support batch diploma generation for convocation
- Record honors/distinctions (Summa Cum Laude: GPA ≥ 3.9, Magna Cum Laude: ≥ 3.7, Cum Laude: ≥ 3.5)
- Create alumni record upon degree conferral

## Epic 20: Student Discipline & Conduct

### US-20.1: Report Disciplinary Incident
**As a** faculty member or staff  
**I want to** report a student conduct violation  
**So that** appropriate action can be taken

**Acceptance Criteria:**
- Submit incident report with date, description, evidence (file attachments)
- Classify violation severity (Minor, Major, Severe)
- Identify involved students and witnesses
- System creates disciplinary case with unique case number
- Notify discipline committee and involved student
- Track case status from report through resolution

### US-20.2: Manage Disciplinary Hearing
**As a** discipline committee chair  
**I want to** schedule and conduct hearings  
**So that** cases are resolved fairly

**Acceptance Criteria:**
- Schedule hearing with date, time, location, panel members
- Notify student of hearing with charges and rights
- Record hearing notes and evidence presented
- Enter hearing decision with sanctions
- Available sanctions: written warning, disciplinary probation, suspension (1-4 semesters), expulsion, fine, community service
- Student can submit appeal within 10 business days
- Apply academic holds for suspended/expelled students

### US-20.3: Process Disciplinary Appeal
**As a** student  
**I want to** appeal a disciplinary decision  
**So that** I can contest an unfair ruling

**Acceptance Criteria:**
- Submit appeal with grounds (procedural error, new evidence, disproportionate sanction)
- Appeal reviewed by appeals board (different from original panel)
- Possible outcomes: uphold, modify sanction, reverse decision, order new hearing
- Final decision is binding and recorded permanently
- Academic holds adjusted based on appeal outcome

## Epic 21: Academic Standing & Progress

### US-21.1: View Academic Standing
**As a** student  
**I want to** view my academic standing each semester  
**So that** I know if I need to improve my performance

**Acceptance Criteria:**
- Display current standing: Good Standing, Academic Warning, Probation, Suspension
- Show GPA trend across semesters
- Show Dean's List eligibility (GPA ≥ 3.5 with ≥ 12 credit hours, no incomplete grades)
- Display any active academic holds or restrictions
- Show progress toward degree completion (percentage, remaining credits)
- Access academic improvement plan if on probation

### US-21.2: Manage At-Risk Students
**As an** academic advisor  
**I want to** identify and track at-risk students  
**So that** early intervention can improve outcomes

**Acceptance Criteria:**
- Dashboard showing students with declining GPA, low attendance, missing assignments
- Configurable risk indicators per program
- Record intervention actions (advising sessions, tutoring referrals, counseling)
- Track improvement over subsequent semesters
- Generate at-risk student reports for department heads
- Automated alerts when student GPA drops below warning threshold

## Epic 22: Grade Dispute & Appeal

### US-22.1: Submit Grade Appeal
**As a** student  
**I want to** appeal a grade I believe is incorrect  
**So that** my academic record accurately reflects my performance

**Acceptance Criteria:**
- Submit appeal specifying course, exam, current grade, expected grade, justification
- Upload supporting evidence (exam paper photos, assignment copies)
- Appeal filed within 15 days of grade publication
- Appeal routed to course faculty first, then department head if unresolved
- Track appeal status with timeline
- Receive notification of outcome with detailed reasoning

### US-22.2: Process Revaluation Request
**As a** faculty member  
**I want to** review and process grade revaluation requests  
**So that** grades are fair and accurate

**Acceptance Criteria:**
- View pending revaluation requests with student evidence
- Re-examine student work and enter revised marks or uphold original
- Provide written justification for decision
- If grade changes, system auto-recalculates GPA/CGPA
- Escalation to department head if student disputes faculty decision
- Final decision by Academic Appeals Committee is binding

## Epic 23: Faculty Recruitment

### US-23.1: Post Job Opening
**As an** HR administrator  
**I want to** create and publish faculty job postings  
**So that** qualified candidates can apply

**Acceptance Criteria:**
- Create position with department, designation, qualifications, experience requirements
- Set application deadline and required documents
- Publish to institution career portal and optionally external job boards
- Track number of applications received
- Close applications after deadline
- Define screening criteria and minimum qualifications

### US-23.2: Track and Evaluate Applicants
**As an** HR administrator  
**I want to** manage the recruitment pipeline  
**So that** hiring decisions are systematic and fair

**Acceptance Criteria:**
- View all applications with screening status (Applied, Screened, Shortlisted, Interview, Offered, Hired, Rejected)
- Filter and sort by qualifications, experience, screening score
- Schedule interviews with panel members and room booking
- Record interview scores using structured evaluation rubric
- Generate offer letters with salary, benefits, joining date
- Track offer acceptance/rejection
- Complete background verification before final hire

### US-23.3: Onboard New Faculty
**As an** HR administrator  
**I want to** onboard newly hired faculty  
**So that** they can start working with all systems configured

**Acceptance Criteria:**
- Generate employee ID and user account
- Onboarding checklist (document submission, ID card, system access, orientation)
- Assign to department with designation and reporting structure
- Set up payroll with salary components
- Schedule orientation and training sessions
- Set probation period with review milestones
- Grant system access based on role

## Epic 24: Department & Program Administration

### US-24.1: Manage Department Structure
**As an** administrator  
**I want to** define and manage institutional department hierarchy  
**So that** the organization structure is accurately represented

**Acceptance Criteria:**
- Create departments with name, code, parent (faculty/school)
- Assign department head with term start/end dates
- Track sanctioned vs filled positions per department
- Define academic committees with member assignments
- Generate department organizational chart
- Manage inter-department relationships and shared resources

### US-24.2: Manage Curriculum Changes
**As a** department head  
**I want to** propose and track curriculum modifications  
**So that** programs stay current and relevant

**Acceptance Criteria:**
- Submit curriculum change proposal (add/remove/modify courses, prerequisites, credit hours)
- Route through approval chain (department → academic board → senate)
- Track proposal status with version history
- Apply changes prospectively (existing students grandfathered)
- Generate impact analysis (affected students, prerequisite chains)
- Maintain curriculum version history per program

## Epic 25: Room & Facility Management

### US-25.1: Manage Room Inventory
**As a** facility manager  
**I want to** maintain a complete room and facility database  
**So that** space allocation is efficient

**Acceptance Criteria:**
- Register rooms with building, floor, number, capacity, type (classroom/lab/auditorium/conference/office)
- Track amenities per room (projector, whiteboard, AC, computers, wheelchair access)
- Record maintenance history and current condition
- Set availability schedules (available hours, blocked periods)
- View facility utilization reports (occupancy rates, peak hours)
- Track equipment assigned to each room

### US-25.2: Book Rooms
**As a** faculty member or staff  
**I want to** book rooms for classes, meetings, and events  
**So that** I have confirmed space for my activities

**Acceptance Criteria:**
- Search available rooms by date, time, capacity, amenities
- Submit booking request with purpose and expected attendees
- Automatic conflict detection (no double-booking)
- Approval workflow for special spaces (auditoriums, conference halls)
- Recurring booking support (weekly classes)
- Cancel or modify bookings with notification to stakeholders
- Integration with timetable system for academic scheduling

## Epic 26: Transfer Credits & Equivalency

### US-26.1: Submit Transfer Credit Application
**As a** transfer student  
**I want to** apply for credit transfer from my previous institution  
**So that** I don't repeat courses I've already completed

**Acceptance Criteria:**
- Submit application with official transcripts from source institution
- List courses for transfer evaluation with grades and credit hours
- Upload course syllabi for equivalency assessment
- Track application status (Submitted, Under Review, Partially Approved, Approved, Rejected)
- View approved transfer credits on academic record
- Transfer credits reflected in degree audit

### US-26.2: Evaluate Transfer Credits
**As a** registrar  
**I want to** evaluate and approve transfer credit requests  
**So that** only equivalent courses are credited

**Acceptance Criteria:**
- Review submitted transcripts and course syllabi
- Map external courses to internal equivalents using articulation agreements
- Apply transfer rules (maximum 40% credits transferable, minimum B grade)
- Approve/reject individual courses with justification
- Record approved equivalencies for future reference
- Update student's degree audit with approved transfers
- Handle GPA for transfers (configurable: include or exclude from GPA)

## Epic 27: Scholarship & Financial Aid

### US-27.1: Apply for Financial Aid
**As a** student  
**I want to** apply for scholarships and financial aid  
**So that** I can fund my education

**Acceptance Criteria:**
- Browse available scholarships with eligibility criteria
- Submit application with required documents (income proof, merit certificates)
- System auto-checks eligibility based on GPA, program, financial need
- Track application status (Applied, Under Review, Awarded, Rejected, Waitlisted)
- View awarded aid with amount and conditions
- Accept or decline aid offers

### US-27.2: Manage Scholarship Programs
**As a** financial aid administrator  
**I want to** configure and manage scholarship programs  
**So that** funds are distributed fairly and tracked properly

**Acceptance Criteria:**
- Define scholarships with: name, type (merit/need/athletic/departmental), criteria, amount, fund limit
- Set renewal criteria (minimum GPA, course load, good standing)
- Review and approve applications with scoring rubric
- Track fund utilization and remaining balance
- Process disbursement (apply to invoice or direct stipend)
- Auto-revoke scholarships when renewal criteria not met (with warning period)
- Generate donor reports and utilization statistics
- Package multiple aid types with total cap enforcement

## Summary

Total Epics: **27**  
Total User Stories: **88**

These user stories cover the core functionality across all major modules of the EMIS system. Each story follows the standard format and includes clear acceptance criteria to guide development and testing.
