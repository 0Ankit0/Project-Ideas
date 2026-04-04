# EMIS - Domain Model

## Overview

The domain model represents the key business entities and their relationships in the EMIS system. This is a conceptual model focusing on the problem domain rather than technical implementation.

## Core Domain Model

```mermaid
erDiagram
    User ||--o{ Student : "is"
    User ||--o{ Faculty : "is"
    User ||--o{ Staff : "is"
    User ||--o{ Parent : "is"
    User {
        uuid id PK
        string username
        string email
        string password_hash
        string role
        boolean is_active
        datetime created_at
    }
    
    Student ||--o{ SemesterEnrollment : "has"
    Student ||--|| Program : "enrolled_in"
    Student ||--o| Application : "from"
    Student ||--o{ Parent : "monitored_by"
    Student {
        uuid id PK
        string student_id UK
        uuid user_id FK
        uuid program_id FK
        string batch
        string status
        date date_of_birth
    }
    
    Program ||--o{ Course : "offers"
    Program ||--o{ ProgramSemester : "has"
    Program {
        uuid id PK
        string code UK
        string name
        string degree_type
        int duration_semesters
        int total_credits_required
    }
    
    ProgramSemester ||--o{ Course : "includes"
    ProgramSemester {
        uuid id PK
        uuid program_id FK
        int semester_number
        string semester_name
    }
    
    Course ||--o{ CourseSection : "has"
    Course ||--o{ Course : "prerequisite"
    Course {
        uuid id PK
        string code UK
        string name
        int credits
        string description
        string course_type
    }
    
    CourseSection ||--|| Faculty : "taught_by"
    CourseSection ||--|| Room : "held_in"
    CourseSection ||--o{ CourseEnrollment : "has"
    CourseSection ||--o{ ClassSchedule : "scheduled_as"
    CourseSection {
        uuid id PK
        uuid course_id FK
        uuid faculty_id FK
        uuid room_id FK
        int capacity
        int enrolled_count
        string section_code
    }
    
    SemesterEnrollment ||--o{ CourseEnrollment : "contains"
    SemesterEnrollment ||--|| AcademicSemester : "in"
    SemesterEnrollment {
        uuid id PK
        uuid student_id FK
        uuid academic_semester_id FK
        uuid program_semester_id FK
        boolean is_active
        decimal gpa
        int credits_enrolled
    }
    
    CourseEnrollment ||--|| Student : "for"
    CourseEnrollment ||--|| CourseSection : "in"
    CourseEnrollment ||--o| Grade : "has"
    CourseEnrollment {
        uuid id PK
        uuid semester_enrollment_id FK
        uuid course_section_id FK
        string status
        decimal grade_points
        string letter_grade
    }
    
    Faculty ||--o{ CourseSection : "teaches"
    Faculty ||--o{ Student : "advises"
    Faculty {
        uuid id PK
        uuid user_id FK
        string faculty_id UK
        uuid department_id FK
        string designation
        string qualification
    }
    
    Application ||--o| Student : "becomes"
    Application ||--|| Program : "for"
    Application {
        uuid id PK
        string application_number UK
        uuid program_id FK
        string status
        decimal score
        datetime submitted_at
        string applicant_name
        string applicant_email
    }
    
    AcademicSemester ||--o{ SemesterEnrollment : "has"
    AcademicSemester ||--|| AcademicYear : "part_of"
    AcademicSemester {
        uuid id PK
        uuid academic_year_id FK
        string semester_type
        date start_date
        date end_date
        boolean is_current
    }
    
    AcademicYear {
        uuid id PK
        string year_code UK
        date start_date
        date end_date
        boolean is_current
    }
    
    Room ||--|| Building : "in"
    Room {
        uuid id PK
        string room_number UK
        uuid building_id FK
        int capacity
        string room_type
    }
    
    Building {
        uuid id PK
        string name
        string code UK
        int floors
    }
    
    ClassSchedule {
        uuid id PK
        uuid course_section_id FK
        string day_of_week
        time start_time
        time end_time
    }
    
    Grade ||--|| Exam : "from"
    Grade {
        uuid id PK
        uuid course_enrollment_id FK
        uuid exam_id FK
        decimal marks_obtained
        decimal marks_total
    }
    
    Exam ||--|| CourseSection : "for"
    Exam {
        uuid id PK
        uuid course_section_id FK
        string exam_type
        datetime exam_date
        int duration_minutes
        decimal total_marks
    }
```

## Financial Domain

```mermaid
erDiagram
    Student ||--o{ FeeStructure : "has"
    Student ||--o{ Payment : "makes"
    Student ||--|| Account : "has"
    
    FeeStructure ||--|| Program : "for"
    FeeStructure ||--o{ FeeHead : "contains"
    FeeStructure {
        uuid id PK
        uuid program_id FK
        uuid semester_id FK
        decimal total_amount
        boolean is_active
    }
    
    FeeHead {
        uuid id PK
        uuid fee_structure_id FK
        string head_name
        decimal amount
        string fee_type
    }
    
    Account ||--o{ Transaction : "has"
    Account {
        uuid id PK
        uuid student_id FK
        decimal balance
        decimal total_charged
        decimal total_paid
    }
    
    Payment ||--|| Transaction : "creates"
    Payment ||--|| PaymentGateway : "via"
    Payment {
        uuid id PK
        uuid student_id FK
        string payment_id UK
        decimal amount
        string payment_method
        string status
        datetime payment_date
    }
    
    Transaction {
        uuid id PK
        uuid account_id FK
        string transaction_type
        decimal amount
        string description
        datetime transaction_date
    }
    
    PaymentGateway {
        uuid id PK
        string name
        string gateway_type
        boolean is_active
    }
```

## Library Domain

```mermaid
erDiagram
    Book ||--o{ BookCopy : "has"
    Book ||--|| Category : "in"
    Book ||--|| Publisher : "published_by"
    Book {
        uuid id PK
        string isbn UK
        string title
        string author
        int publication_year
    }
    
    BookCopy ||--o{ Circulation : "involved_in"
    BookCopy {
        uuid id PK
        uuid book_id FK
        string barcode UK
        string status
        string location
    }
    
    Circulation ||--|| Student : "by"
    Circulation ||--|| Staff : "processed_by"
    Circulation ||--o| Fine : "generates"
    Circulation {
        uuid id PK
        uuid book_copy_id FK
        uuid student_id FK
        uuid staff_id FK
        date issue_date
        date due_date
        date return_date
        string status
    }
    
    Fine {
        uuid id PK
        uuid circulation_id FK
        decimal amount
        boolean is_paid
        date paid_date
    }
    
    Category {
        uuid id PK
        string name
        string code UK
    }
    
    Publisher {
        uuid id PK
        string name
        string country
    }
```

## HR Domain

```mermaid
erDiagram
    Employee ||--|| User : "is"
    Employee ||--|| Department : "works_in"
    Employee ||--o{ Salary : "receives"
    Employee ||--o{ Leave : "applies"
    Employee ||--o{ Attendance : "has"
    
    Employee {
        uuid id PK
        uuid user_id FK
        string employee_id UK
        uuid department_id FK
        string designation
        date joining_date
        string employment_type
    }
    
    Department {
        uuid id PK
        string name
        string code UK
        uuid head_id FK
    }
    
    Salary ||--|| PayrollPeriod : "for"
    Salary {
        uuid id PK
        uuid employee_id FK
        uuid payroll_period_id FK
        decimal basic_salary
        decimal allowances
        decimal deductions
        decimal net_salary
        date payment_date
    }
    
    PayrollPeriod {
        uuid id PK
        int year
        int month
        date start_date
        date end_date
        string status
    }
    
    Leave {
        uuid id PK
        uuid employee_id FK
        string leave_type
        date start_date
        date end_date
        int days
        string status
        string reason
    }
    
    Attendance {
        uuid id PK
        uuid employee_id FK
        date date
        time check_in
        time check_out
        string status
    }
```

## Hostel & Transport Domain

```mermaid
erDiagram
    Hostel ||--o{ Room : "has"
    Room ||--o{ RoomAllocation : "allocated_as"
    
    Hostel {
        uuid id PK
        string name
        string hostel_type
        int capacity
        uuid warden_id FK
    }
    
    RoomAllocation ||--|| Student : "for"
    RoomAllocation {
        uuid id PK
        uuid room_id FK
        uuid student_id FK
        date allocation_date
        date vacate_date
        string status
    }
    
    TransportRoute ||--o{ RouteStop : "has"
    TransportRoute ||--o{ VehicleAssignment : "served_by"
    TransportRoute {
        uuid id PK
        string route_name
        string route_code UK
        decimal monthly_fee
    }
    
    RouteStop {
        uuid id PK
        uuid route_id FK
        string stop_name
        time pickup_time
        int sequence_number
    }
    
    Vehicle ||--o{ VehicleAssignment : "assigned_in"
    Vehicle {
        uuid id PK
        string vehicle_number UK
        string vehicle_type
        int capacity
        uuid driver_id FK
    }
    
    VehicleAssignment {
        uuid id PK
        uuid vehicle_id FK
        uuid route_id FK
        date effective_from
        date effective_to
    }
    
    Student ||--o| TransportAllocation : "has"
    TransportAllocation {
        uuid id PK
        uuid student_id FK
        uuid route_id FK
        uuid stop_id FK
        date allocation_date
        string status
    }
```

## LMS Domain

```mermaid
erDiagram
    CourseSection ||--o{ Content : "has"
    CourseSection ||--o{ Assignment : "has"
    CourseSection ||--o{ Quiz : "has"
    CourseSection ||--o{ Discussion : "has"
    
    Content {
        uuid id PK
        uuid course_section_id FK
        string title
        string content_type
        string file_path
        int module_number
        datetime published_at
    }
    
    Assignment ||--o{ Submission : "receives"
    Assignment {
        uuid id PK
        uuid course_section_id FK
        string title
        string description
        datetime due_date
        decimal max_marks
        boolean allow_late
    }
    
    Submission ||--|| Student : "by"
    Submission {
        uuid id PK
        uuid assignment_id FK
        uuid student_id FK
        string file_path
        datetime submitted_at
        decimal marks
        string feedback
        string status
    }
    
    Quiz ||--o{ QuizAttempt : "has"
    Quiz ||--o{ Question : "contains"
    Quiz {
        uuid id PK
        uuid course_section_id FK
        string title
        int duration_minutes
        int max_attempts
        decimal total_marks
    }
    
    QuizAttempt ||--|| Student : "by"
    QuizAttempt {
        uuid id PK
        uuid quiz_id FK
        uuid student_id FK
        datetime started_at
        datetime submitted_at
        decimal score
        int attempt_number
    }
    
    Question ||--o{ Answer : "has"
    Question {
        uuid id PK
        uuid quiz_id FK
        string question_text
        string question_type
        int marks
    }
    
    Answer {
        uuid id PK
        uuid question_id FK
        string answer_text
        boolean is_correct
    }
    
    Discussion ||--o{ Post : "contains"
    Discussion {
        uuid id PK
        uuid course_section_id FK
        string topic
        boolean is_pinned
        datetime created_at
    }
    
    Post ||--|| User : "by"
    Post ||--o{ Post : "reply_to"
    Post {
        uuid id PK
        uuid discussion_id FK
        uuid user_id FK
        uuid parent_post_id FK
        string content
        datetime posted_at
    }
```

## Attendance Domain

```mermaid
erDiagram
    CourseSection ||--o{ AttendanceSession : "has"
    AttendanceSession ||--o{ AttendanceRecord : "contains"
    
    AttendanceSession {
        uuid id PK
        uuid course_section_id FK
        date session_date
        time start_time
        time end_time
        uuid marked_by_id FK
    }
    
    AttendanceRecord ||--|| Student : "for"
    AttendanceRecord {
        uuid id PK
        uuid attendance_session_id FK
        uuid student_id FK
        string status
        string remarks
    }
    
    Student ||--o{ LeaveApplication : "applies"
    LeaveApplication {
        uuid id PK
        uuid student_id FK
        date start_date
        date end_date
        string reason
        string status
        uuid approved_by_id FK
    }
```

## Inventory Domain

```mermaid
erDiagram
    Asset ||--|| Category : "in"
    Asset ||--|| Department : "assigned_to"
    Asset {
        uuid id PK
        string asset_id UK
        uuid category_id FK
        string name
        decimal purchase_price
        date purchase_date
        uuid assigned_to_dept_id FK
        string status
    }
    
    StockItem ||--|| Category : "in"
    StockItem ||--o{ StockMovement : "has"
    StockItem {
        uuid id PK
        string item_code UK
        uuid category_id FK
        string name
        int quantity_available
        int reorder_level
        string unit
    }
    
    StockMovement {
        uuid id PK
        uuid stock_item_id FK
        string movement_type
        int quantity
        datetime movement_date
        uuid performed_by_id FK
        string remarks
    }
```

## Notification Domain

```mermaid
erDiagram
    User ||--o{ Notification : "receives"
    Notification ||--o{ NotificationDelivery : "delivered_via"
    
    Notification {
        uuid id PK
        uuid user_id FK
        string title
        string message
        string notification_type
        string priority
        datetime created_at
        boolean is_read
    }
    
    NotificationDelivery {
        uuid id PK
        uuid notification_id FK
        string channel
        string status
        datetime sent_at
    }
    
    Announcement ||--o{ User : "targeted_to"
    Announcement {
        uuid id PK
        string title
        string content
        datetime published_at
        datetime expires_at
        string target_audience
    }
```

## Academic Session Domain

```mermaid
classDiagram
    class AcademicYear {
        UUID id
        String name
        Date start_date
        Date end_date
        AcademicYearStatus status
    }

    class AcademicYearStatus {
        <<enumeration>>
        PLANNING
        ACTIVE
        COMPLETED
        ARCHIVED
    }

    class Semester {
        UUID id
        UUID academic_year_id
        String name
        SemesterType type
        Date start_date
        Date end_date
        SemesterStatus status
    }

    class SemesterType {
        <<enumeration>>
        FALL
        SPRING
        SUMMER
    }

    class SemesterStatus {
        <<enumeration>>
        PLANNING
        REGISTRATION_OPEN
        ACTIVE
        EXAM_PERIOD
        GRADING
        COMPLETED
        ARCHIVED
    }

    class RegistrationWindow {
        UUID id
        UUID semester_id
        Date open_date
        Date close_date
        WindowType type
    }

    class WindowType {
        <<enumeration>>
        REGULAR
        LATE
        ADD_DROP
    }

    class AcademicCalendarEvent {
        UUID id
        UUID semester_id
        String name
        String event_type
        Date start_date
        Date end_date
        Boolean is_holiday
    }

    AcademicYear "1" --> "*" Semester
    Semester "1" --> "*" RegistrationWindow
    Semester "1" --> "*" AcademicCalendarEvent
```

## Graduation & Degree Domain

```mermaid
classDiagram
    class GraduationApplication {
        UUID id
        UUID student_id
        UUID semester_id
        GraduationStatus status
        DateTime applied_at
        Date decision_date
        String honors_designation
    }

    class GraduationStatus {
        <<enumeration>>
        SUBMITTED
        UNDER_REVIEW
        ELIGIBLE
        INELIGIBLE
        APPROVED
        CONFERRED
    }

    class DegreeAudit {
        UUID id
        UUID graduation_application_id
        Integer total_credits_required
        Integer total_credits_earned
        Decimal cgpa
        Boolean all_courses_complete
        Boolean no_holds
        Boolean no_pending_grades
        Boolean is_eligible
        Date audit_date
    }

    class DiplomaRecord {
        UUID id
        UUID student_id
        String diploma_number
        String program_name
        Date conferral_date
        String honors
        DiplomaStatus status
    }

    class DiplomaStatus {
        <<enumeration>>
        GENERATED
        DISPATCHED
        DELIVERED
    }

    GraduationApplication "1" --> "1" DegreeAudit
    GraduationApplication "1" --> "0..1" DiplomaRecord
```

## Student Discipline Domain

```mermaid
classDiagram
    class DisciplinaryCase {
        UUID id
        UUID student_id
        UUID reported_by
        String offense_type
        CaseSeverity severity
        String description
        CaseStatus status
        Date reported_date
    }

    class CaseSeverity {
        <<enumeration>>
        MINOR
        MODERATE
        MAJOR
        CRITICAL
    }

    class CaseStatus {
        <<enumeration>>
        REPORTED
        UNDER_INVESTIGATION
        HEARING_SCHEDULED
        HEARING_COMPLETED
        SANCTIONED
        APPEALED
        CLOSED
        SEALED
    }

    class DisciplinaryHearing {
        UUID id
        UUID case_id
        DateTime scheduled_date
        String location
        String panel_members
        String hearing_outcome
        String minutes
    }

    class Sanction {
        UUID id
        UUID case_id
        SanctionType type
        Date start_date
        Date end_date
        String conditions
    }

    class SanctionType {
        <<enumeration>>
        WARNING
        PROBATION
        SUSPENSION
        EXPULSION
        COMMUNITY_SERVICE
        FINE
    }

    class DisciplineAppeal {
        UUID id
        UUID case_id
        UUID student_id
        String grounds
        DisciplineAppealStatus status
        Date submitted_date
        Date decision_date
    }

    class DisciplineAppealStatus {
        <<enumeration>>
        SUBMITTED
        UNDER_REVIEW
        UPHELD
        MODIFIED
        OVERTURNED
    }

    DisciplinaryCase "1" --> "*" DisciplinaryHearing
    DisciplinaryCase "1" --> "*" Sanction
    DisciplinaryCase "1" --> "0..1" DisciplineAppeal
```

## Academic Standing Domain

```mermaid
classDiagram
    class AcademicStandingRecord {
        UUID id
        UUID student_id
        UUID semester_id
        Decimal semester_gpa
        Decimal cgpa
        StandingType standing
        Date determined_date
        String notes
    }

    class StandingType {
        <<enumeration>>
        GOOD_STANDING
        PROBATION
        ACADEMIC_WARNING
        SUSPENSION
        DISMISSAL
        DEANS_LIST
        PRESIDENTS_LIST
    }

    class ProbationContract {
        UUID id
        UUID standing_record_id
        UUID student_id
        String conditions
        Decimal min_gpa_target
        Integer max_semesters
        UUID advisor_id
        Date signed_date
    }

    AcademicStandingRecord "1" --> "0..1" ProbationContract
```

## Grade Appeal Domain

```mermaid
classDiagram
    class GradeAppeal {
        UUID id
        UUID student_id
        UUID enrollment_id
        UUID course_id
        String original_grade
        String requested_action
        String reason
        String evidence_urls
        AppealStatus status
        Date submitted_date
    }

    class AppealStatus {
        <<enumeration>>
        SUBMITTED
        FACULTY_REVIEW
        DEPT_HEAD_REVIEW
        COMMITTEE_REVIEW
        RESOLVED
        REJECTED
        WITHDRAWN
    }

    class AppealReview {
        UUID id
        UUID appeal_id
        UUID reviewer_id
        ReviewerRole reviewer_role
        ReviewDecision decision
        String new_grade
        Date review_date
        String comments
    }

    class ReviewerRole {
        <<enumeration>>
        FACULTY
        DEPT_HEAD
        COMMITTEE
    }

    class ReviewDecision {
        <<enumeration>>
        UPHELD
        MODIFIED
        ESCALATED
    }

    GradeAppeal "1" --> "*" AppealReview
```

## Faculty Recruitment Domain

```mermaid
classDiagram
    class JobPosting {
        UUID id
        UUID department_id
        String title
        PositionType position_type
        String description
        String qualifications
        String salary_range
        PostingStatus status
        Date posted_date
        Date deadline
    }

    class PositionType {
        <<enumeration>>
        FULL_TIME
        PART_TIME
        ADJUNCT
        VISITING
    }

    class PostingStatus {
        <<enumeration>>
        DRAFT
        PUBLISHED
        CLOSED
        FILLED
        CANCELLED
    }

    class JobApplication {
        UUID id
        UUID posting_id
        String applicant_name
        String email
        String resume_url
        String cover_letter
        ApplicationStatus status
    }

    class ApplicationStatus {
        <<enumeration>>
        RECEIVED
        SCREENING
        SHORTLISTED
        INTERVIEW_SCHEDULED
        INTERVIEWED
        OFFER_EXTENDED
        ACCEPTED
        REJECTED
        WITHDRAWN
    }

    class InterviewSchedule {
        UUID id
        UUID application_id
        DateTime interview_date
        String panel_members
        InterviewType interview_type
        String feedback
        Decimal score
    }

    class InterviewType {
        <<enumeration>>
        PHONE
        VIDEO
        IN_PERSON
        DEMO_LECTURE
    }

    class OfferLetter {
        UUID id
        UUID application_id
        Decimal salary
        Date start_date
        String terms
        OfferStatus status
    }

    class OfferStatus {
        <<enumeration>>
        DRAFT
        SENT
        ACCEPTED
        DECLINED
        EXPIRED
    }

    JobPosting "1" --> "*" JobApplication
    JobApplication "1" --> "*" InterviewSchedule
    JobApplication "1" --> "0..1" OfferLetter
```

## Transfer Credits Domain

```mermaid
classDiagram
    class TransferCreditRequest {
        UUID id
        UUID student_id
        String source_institution
        RequestStatus status
    }

    class RequestStatus {
        <<enumeration>>
        SUBMITTED
        UNDER_EVALUATION
        PARTIALLY_APPROVED
        APPROVED
        REJECTED
    }

    class TransferCreditItem {
        UUID id
        UUID request_id
        String external_course_name
        String external_course_code
        Integer credits
        String grade
        UUID equivalent_course_id
        EvaluationStatus evaluation_status
        UUID evaluator_id
    }

    class EvaluationStatus {
        <<enumeration>>
        PENDING
        APPROVED
        REJECTED
    }

    class ArticulationAgreement {
        UUID id
        String institution_name
        Date valid_from
        Date valid_to
        AgreementStatus status
    }

    class AgreementStatus {
        <<enumeration>>
        ACTIVE
        EXPIRED
    }

    class ArticulationMapping {
        UUID id
        UUID agreement_id
        String external_course
        UUID internal_course_id
        String credit_mapping
    }

    TransferCreditRequest "1" --> "*" TransferCreditItem
    ArticulationAgreement "1" --> "*" ArticulationMapping
```

## Scholarship & Financial Aid Domain

```mermaid
classDiagram
    class ScholarshipProgram {
        UUID id
        String name
        ScholarshipType type
        Decimal amount
        String eligibility_criteria
        Integer max_recipients
        Boolean renewable
        ProgramStatus status
    }

    class ScholarshipType {
        <<enumeration>>
        MERIT
        NEED_BASED
        ATHLETIC
        DEPARTMENTAL
    }

    class ProgramStatus {
        <<enumeration>>
        ACTIVE
        INACTIVE
    }

    class ScholarshipApplication {
        UUID id
        UUID program_id
        UUID student_id
        UUID academic_year_id
        ApplicationStatus status
        Date applied_date
    }

    class ApplicationStatus {
        <<enumeration>>
        SUBMITTED
        UNDER_REVIEW
        APPROVED
        REJECTED
        WAITLISTED
    }

    class ScholarshipAward {
        UUID id
        UUID application_id
        UUID student_id
        Decimal amount
        String disbursement_schedule
        AwardStatus status
        Boolean renewal_eligible
    }

    class AwardStatus {
        <<enumeration>>
        AWARDED
        ACTIVE
        SUSPENDED
        REVOKED
        COMPLETED
    }

    class AidDisbursement {
        UUID id
        UUID award_id
        Decimal amount
        Date disbursement_date
        UUID semester_id
        DisbursementStatus status
    }

    class DisbursementStatus {
        <<enumeration>>
        PENDING
        PROCESSED
        FAILED
    }

    ScholarshipProgram "1" --> "*" ScholarshipApplication
    ScholarshipApplication "1" --> "0..1" ScholarshipAward
    ScholarshipAward "1" --> "*" AidDisbursement
```

## Facility Management Domain

```mermaid
classDiagram
    class Facility {
        UUID id
        String name
        String building
        FacilityType type
        Integer capacity
        String amenities
        Boolean is_active
    }

    class FacilityType {
        <<enumeration>>
        CLASSROOM
        LAB
        AUDITORIUM
        CONFERENCE
        LIBRARY
        SPORTS
    }

    class RoomBooking {
        UUID id
        UUID facility_id
        UUID booked_by
        String purpose
        DateTime start_time
        DateTime end_time
        BookingStatus status
        BookingPriority priority
    }

    class BookingStatus {
        <<enumeration>>
        REQUESTED
        APPROVED
        REJECTED
        CANCELLED
        COMPLETED
    }

    class BookingPriority {
        <<enumeration>>
        ACADEMIC
        EXAM
        EVENT
        MAINTENANCE
    }

    class MaintenanceRequest {
        UUID id
        UUID facility_id
        UUID reported_by
        String issue_description
        MaintenancePriority priority
        MaintenanceStatus status
    }

    class MaintenancePriority {
        <<enumeration>>
        LOW
        MEDIUM
        HIGH
        CRITICAL
    }

    class MaintenanceStatus {
        <<enumeration>>
        REPORTED
        ASSIGNED
        IN_PROGRESS
        COMPLETED
    }

    Facility "1" --> "*" RoomBooking
    Facility "1" --> "*" MaintenanceRequest
```

## Key Domain Concepts

### 1. User Hierarchy
- **User**: Base entity for all system users
- **Student, Faculty, Staff, Parent**: Specialized user types
- **Role-Based Access**: Each user type has specific permissions

### 2. Academic Structure
- **Program**: Degree program (e.g., BS Computer Science)
- **ProgramSemester**: Semesters within a program
- **Course**: Course offerings
- **CourseSection**: Specific instances of courses
- **SemesterEnrollment**: Student enrollment in a semester
- **CourseEnrollment**: Student enrollment in specific courses

### 3. Academic Calendar
- **AcademicYear**: Fiscal/academic year
- **AcademicSemester**: Fall, Spring, Summer semesters
- **Registration Period**: Time windows for course registration
- **Grading Period**: Windows for grade submission

### 4. Financial Flow
- **FeeStructure**: Defined fees per program/semester
- **Account**: Student financial account
- **Payment**: Fee payment transactions
- **Transaction**: All financial movements

### 5. Assessment
- **Exam**: Scheduled examinations
- **Grade**: Student exam/course grades
- **GPA Calculation**: Weighted average of grades

### 6. Learning Management
- **Content**: Course materials
- **Assignment**: Coursework submissions
- **Quiz**: Online assessments
- **Discussion**: Course forums

## Business Rules

1. **Student Enrollment**:
   - Student must be accepted before enrollment
   - Must clear previous semester dues
   - Cannot exceed maximum credit hours

2. **Course Registration**:
   - Prerequisites must be satisfied
   - No schedule conflicts allowed
   - Course capacity cannot be exceeded

3. **Grade Processing**:
   - Only assigned faculty can enter grades
   - Grades locked after submission
   - Changes require approval

4. **Fee Payment**:
   - Partial payments allowed if configured
   - Receipts generated automatically
   - Outstanding dues prevent registration

5. **Library Circulation**:
   - Maximum borrowing limit enforced
   - Fines calculated for overdue books
   - Outstanding fines prevent new borrowing

6. **Attendance**:
   - Minimum attendance percentage required
   - Authorized absences don't count Against percentage
   - Low attendance triggers warnings

## Summary

The domain model captures the core business concepts and their relationships across all major modules of EMIS. It provides a shared vocabulary for developers, business analysts, and stakeholders while serving as the foundation for database design and API contracts.
