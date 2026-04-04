# Class Diagram — Education Management Information System

This document provides UML class diagrams for the five core EMIS domains, showing key attributes, methods, and inter-class relationships.

---

## 1. User and Authentication Domain

```mermaid
classDiagram
    class BaseModel {
        +UUID id
        +datetime created_at
        +datetime updated_at
        +bool is_active
    }

    class User {
        +str username
        +str email
        +str password_hash
        +UserRole role
        +str phone
        +bool is_staff
        +bool is_superuser
        +datetime last_login
        +get_full_name() str
        +has_permission(perm: str) bool
        +check_password(raw: str) bool
        +set_password(raw: str) None
    }

    class Role {
        +str name
        +str code
        +str description
        +get_permissions() list
    }

    class Permission {
        +str name
        +str codename
        +str resource
        +str action
    }

    class UserRole {
        <<enumeration>>
        SUPER_ADMIN
        ADMIN
        FACULTY
        STUDENT
        PARENT
        HR_STAFF
        FINANCE_STAFF
        LIBRARY_STAFF
        HOSTEL_WARDEN
        TRANSPORT_MANAGER
    }

    class APIKey {
        +str key_hash
        +str label
        +UserRole scoped_role
        +datetime expires_at
        +str[] allowed_ips
        +bool is_active
        +is_expired() bool
        +verify(raw_key: str) bool
    }

    class AuditLog {
        +str table_name
        +UUID record_id
        +AuditAction action
        +UUID actor_id
        +str actor_role
        +dict old_values
        +dict new_values
        +str reason_code
        +str ip_address
        +datetime occurred_at
    }

    BaseModel <|-- User
    BaseModel <|-- Role
    BaseModel <|-- Permission
    BaseModel <|-- APIKey
    BaseModel <|-- AuditLog
    User "1" --> "1" UserRole : has role
    User "many" --> "many" Permission : granted
    APIKey "many" --> "1" User : belongs to
    AuditLog "many" --> "1" User : actor
```

---

## 2. Academic Domain

```mermaid
classDiagram
    class Program {
        +str code
        +str name
        +DegreeType degree_type
        +int duration_semesters
        +int total_credits_required
        +int min_credit_hours_per_semester
        +int max_credit_hours_per_semester
        +UUID department_id
        +bool is_active
        +get_active_curriculum() ProgramCurriculum
        +get_enrolled_students() QuerySet
    }

    class ProgramSemester {
        +UUID program_id
        +int semester_number
        +str semester_name
        +int min_credits
        +int max_credits
        +get_required_courses() list
        +get_elective_courses() list
    }

    class Course {
        +str code
        +str name
        +int credit_hours
        +CourseType course_type
        +bool is_elective
        +int max_enrollment
        +UUID department_id
        +str description
        +get_prerequisites() list[Course]
        +get_active_sections(semester_id) QuerySet
        +is_prerequisite_of(other: Course) bool
    }

    class CourseSection {
        +UUID course_id
        +str section_code
        +UUID faculty_id
        +UUID semester_id
        +UUID room_id
        +int max_enrollment
        +int current_enrollment
        +has_available_seats() bool
        +increment_enrollment_count() None
        +decrement_enrollment_count() None
        +get_time_slots() list[TimetableSlot]
    }

    class Enrollment {
        +UUID student_id
        +UUID section_id
        +UUID semester_id
        +EnrollmentStatus status
        +datetime enrolled_at
        +datetime dropped_at
        +UUID grade_id
        +is_droppable() bool
        +is_within_add_drop_window() bool
        +drop() None
        +withdraw() None
    }

    class EnrollmentStatus {
        <<enumeration>>
        ACTIVE
        DROPPED
        WITHDRAWN
        WF
        COMPLETED
        FAILED
        INCOMPLETE
    }

    class DegreeType {
        <<enumeration>>
        BACHELOR
        MASTER
        PHD
        DIPLOMA
        CERTIFICATE
    }

    Program "1" *-- "many" ProgramSemester : contains
    Program "1" --> "many" Course : offers
    Course "1" *-- "many" CourseSection : offered as
    Course "many" --> "many" Course : prerequisites
    CourseSection "1" --> "many" Enrollment : has
    Enrollment --> EnrollmentStatus
    Program --> DegreeType
```

---

## 3. Student and Admissions Domain

```mermaid
classDiagram
    class Student {
        +str student_id
        +UUID user_id
        +UUID program_id
        +str batch
        +StudentStatus status
        +date date_of_birth
        +date admission_date
        +date expected_graduation_date
        +calculate_cgpa() Decimal
        +get_current_semester_number() int
        +get_semester_enrollments(sem_id) QuerySet
        +has_financial_hold() bool
        +is_eligible_for_registration() bool
        +can_graduate() bool
    }

    class StudentStatus {
        <<enumeration>>
        ACTIVE
        ON_LEAVE
        GRADUATED
        WITHDRAWN
        SUSPENDED
        EXPELLED
    }

    class Application {
        +UUID applicant_user_id
        +UUID program_id
        +int intake_year
        +ApplicationStatus status
        +datetime submitted_at
        +date enrollment_deadline
        +int rank
        +calculate_merit_score() Decimal
        +is_enrollment_deadline_passed() bool
        +transition_to(new_status: ApplicationStatus) None
    }

    class ApplicationStatus {
        <<enumeration>>
        DRAFT
        SUBMITTED
        UNDER_REVIEW
        SHORTLISTED
        WAITLISTED
        ACCEPTED
        REJECTED
        EXPIRED
        ENROLLED
    }

    class Document {
        +UUID application_id
        +DocumentType document_type
        +str file_path
        +DocumentStatus status
        +UUID verified_by_id
        +datetime verified_at
        +is_verified() bool
    }

    class MeritListEntry {
        +UUID merit_list_id
        +UUID application_id
        +int rank
        +Decimal merit_score
        +bool offer_sent
        +datetime offer_sent_at
    }

    class Parent {
        +UUID student_id
        +UUID user_id
        +str relationship
        +bool has_portal_access
        +bool consent_given_by_student
        +datetime consent_given_at
        +can_view_grades() bool
    }

    Student --> StudentStatus
    Application --> ApplicationStatus
    Application "1" *-- "many" Document : has
    Application "1" --> "1" MeritListEntry : ranked in
    Student "many" --> "many" Parent : monitored by
```

---

## 4. Assessment Domain

```mermaid
classDiagram
    class Exam {
        +str name
        +ExamType exam_type
        +UUID section_id
        +UUID semester_id
        +date scheduled_date
        +time start_time
        +int duration_minutes
        +Decimal total_marks
        +Decimal passing_marks
        +bool grading_window_open
        +is_grading_window_open() bool
        +open_grading_window() None
        +close_grading_window() None
        +get_grade_distribution() dict
    }

    class ExamType {
        <<enumeration>>
        MIDTERM
        FINAL
        QUIZ
        ASSIGNMENT
        PRACTICAL
    }

    class Grade {
        +UUID enrollment_id
        +UUID exam_id
        +Decimal marks_obtained
        +str letter_grade
        +Decimal grade_points
        +GradeStatus status
        +UUID submitted_by_id
        +datetime published_at
        +datetime amended_at
        +compute_letter_grade() str
        +compute_grade_points() Decimal
        +publish() None
        +amend(new_marks, reason, approver_id) None
    }

    class GradeStatus {
        <<enumeration>>
        DRAFT
        SUBMITTED
        PUBLISHED
        AMENDED
    }

    class GPARecord {
        +UUID student_id
        +UUID semester_id
        +Decimal semester_gpa
        +Decimal cumulative_gpa
        +int credit_hours_attempted
        +int credit_hours_earned
        +datetime calculated_at
        +recalculate() None
    }

    class GradeScale {
        +str institution_id
        +str scale_name
        +list entries
        +get_letter_grade(marks_pct: Decimal) str
        +get_grade_points(letter: str) Decimal
    }

    class GradeDispute {
        +UUID grade_id
        +UUID student_id
        +str dispute_reason
        +DisputeStatus status
        +UUID resolved_by_id
        +datetime resolved_at
        +str resolution_notes
    }

    Exam --> ExamType
    Exam "1" --> "many" Grade : produces
    Grade --> GradeStatus
    Grade "many" --> "1" GPARecord : contributes to
    GradeScale --> Grade : governs
    Grade "1" --> "0..1" GradeDispute : may have
```

---

## 5. Finance Domain

```mermaid
classDiagram
    class FeeStructure {
        +UUID program_id
        +int applicable_year
        +str version
        +bool is_active
        +datetime effective_from
        +get_fee_heads() list[FeeHead]
        +calculate_total_for_student(student) Decimal
    }

    class FeeHead {
        +UUID fee_structure_id
        +str name
        +FeeHeadType head_type
        +Decimal amount
        +bool is_refundable
        +bool is_mandatory
    }

    class FeeHeadType {
        <<enumeration>>
        TUITION
        LAB
        LIBRARY
        HOSTEL
        TRANSPORT
        EXAM
        ACTIVITY
        ADMISSION
    }

    class FeeInvoice {
        +str invoice_number
        +UUID student_id
        +UUID semester_id
        +UUID fee_structure_version_id
        +Decimal subtotal
        +Decimal discount_amount
        +Decimal total_amount
        +Decimal amount_paid
        +InvoiceStatus status
        +date due_date
        +datetime issued_at
        +get_outstanding_balance() Decimal
        +apply_scholarship(amount, reason) None
        +mark_overdue() None
        +can_be_refunded() bool
    }

    class InvoiceStatus {
        <<enumeration>>
        DRAFT
        ISSUED
        PARTIALLY_PAID
        PAID
        OVERDUE
        WRITTEN_OFF
        REFUNDED
    }

    class PaymentTransaction {
        +UUID invoice_id
        +PaymentGateway gateway
        +str gateway_transaction_id
        +Decimal amount
        +str currency
        +PaymentStatus status
        +datetime initiated_at
        +datetime confirmed_at
        +str receipt_url
        +str idempotency_key
        +is_confirmed() bool
        +generate_receipt_pdf() str
    }

    class PaymentGateway {
        <<enumeration>>
        STRIPE
        RAZORPAY
        BANK_TRANSFER
        CASH
    }

    class Refund {
        +UUID payment_transaction_id
        +Decimal refund_amount
        +str reason_code
        +UUID authorized_by_id
        +RefundStatus status
        +str gateway_refund_id
        +datetime processed_at
        +process() None
    }

    class Scholarship {
        +UUID student_id
        +str scholarship_name
        +Decimal discount_percentage
        +Decimal max_discount_amount
        +date valid_from
        +date valid_until
        +UUID[] applicable_fee_heads
        +calculate_discount(invoice: FeeInvoice) Decimal
    }

    FeeStructure "1" *-- "many" FeeHead : contains
    FeeHead --> FeeHeadType
    FeeInvoice --> InvoiceStatus
    FeeInvoice "1" *-- "many" FeeLineItem : has
    FeeInvoice "1" --> "many" PaymentTransaction : paid via
    PaymentTransaction --> PaymentGateway
    PaymentTransaction "1" --> "0..1" Refund : may have
    Scholarship "many" --> "many" FeeInvoice : applied to
```

---

### Graduation & Degree Management

```mermaid
classDiagram
    class GraduationApplication {
        +UUID id
        +str application_number
        +UUID student_id
        +UUID program_id
        +date expected_graduation_date
        +GraduationStatus status
        +UUID degree_audit_id
        +HonorsClassification honors_classification
        +str diploma_number
        +datetime applied_at
        +UUID approved_by_id
        +datetime conferred_at
        +str rejection_reason
        +submit() GraduationApplication
        +run_audit() DegreeAudit
        +approve(approver_id: UUID) None
        +reject(reason: str) None
        +confer_degree() None
    }

    class DegreeAudit {
        +UUID id
        +UUID student_id
        +UUID program_id
        +AuditType audit_type
        +AuditStatus status
        +int total_credits_required
        +int total_credits_completed
        +int total_credits_transferred
        +bool required_courses_met
        +bool elective_credits_met
        +bool cgpa_requirement_met
        +bool residency_requirement_met
        +bool holds_cleared
        +list missing_requirements
        +run_audit() AuditStatus
        +check_credits() bool
        +check_courses() bool
        +check_gpa() bool
        +check_residency() bool
        +check_holds() bool
    }

    class GraduationStatus {
        <<enumeration>>
        SUBMITTED
        UNDER_REVIEW
        AUDIT_PASSED
        AUDIT_FAILED
        APPROVED
        REJECTED
        CONFERRED
    }

    class HonorsClassification {
        <<enumeration>>
        SUMMA_CUM_LAUDE
        MAGNA_CUM_LAUDE
        CUM_LAUDE
        NONE
    }

    GraduationApplication --> GraduationStatus
    GraduationApplication --> HonorsClassification
    GraduationApplication "1" --> "1" DegreeAudit : linked to
```

### Student Discipline

```mermaid
classDiagram
    class DisciplinaryCase {
        +UUID id
        +str case_number
        +UUID student_id
        +UUID reported_by_id
        +date incident_date
        +ViolationCategory violation_category
        +Severity severity
        +CaseStatus status
        +str description
        +list evidence_file_ids
        +UUID assigned_committee_id
        +Sanction sanction
        +dict sanction_details
        +date decision_date
        +str decision_rationale
        +date appeal_deadline
        +bool is_sealed
        +create_case() DisciplinaryCase
        +assign_committee(committee_id: UUID) None
        +schedule_hearing(date: date, panel: list) None
        +issue_decision(sanction: Sanction, rationale: str) None
        +enforce_sanction() None
        +seal_record() None
    }

    class DisciplinaryAppeal {
        +UUID id
        +UUID case_id
        +UUID student_id
        +AppealGrounds grounds
        +str appeal_statement
        +list evidence_file_ids
        +AppealStatus status
        +AppealOutcome outcome
        +Sanction modified_sanction
        +str decision_rationale
        +UUID decided_by_id
        +submit() DisciplinaryAppeal
        +decide(outcome: AppealOutcome) None
    }

    class ViolationCategory {
        <<enumeration>>
        ACADEMIC_INTEGRITY
        MISCONDUCT
        HARASSMENT
        PROPERTY_DAMAGE
        SUBSTANCE_ABUSE
        OTHER
    }

    class Severity {
        <<enumeration>>
        MINOR
        MAJOR
        SEVERE
    }

    class Sanction {
        <<enumeration>>
        WARNING
        PROBATION
        SUSPENSION
        EXPULSION
        FINE
        COMMUNITY_SERVICE
    }

    class CaseStatus {
        <<enumeration>>
        REPORTED
        UNDER_INVESTIGATION
        HEARING_SCHEDULED
        HEARING_COMPLETED
        DECISION_ISSUED
        APPEALED
        APPEAL_DECIDED
        CLOSED
    }

    DisciplinaryCase --> ViolationCategory
    DisciplinaryCase --> Severity
    DisciplinaryCase --> Sanction
    DisciplinaryCase --> CaseStatus
    DisciplinaryCase "1" --> "0..1" DisciplinaryAppeal : may have
    DisciplinaryAppeal --> AppealOutcome
```

### Academic Standing

```mermaid
classDiagram
    class AcademicStanding {
        +UUID id
        +UUID student_id
        +UUID semester_id
        +Decimal semester_gpa
        +Decimal cumulative_gpa
        +StandingLevel standing
        +StandingLevel previous_standing
        +bool deans_list
        +int credit_hours_attempted
        +int credit_hours_earned
        +dict restrictions
        +datetime determined_at
        +determine_standing() StandingLevel
        +check_deans_list() bool
        +apply_restrictions() None
    }

    class StandingLevel {
        <<enumeration>>
        GOOD_STANDING
        ACADEMIC_WARNING
        PROBATION
        SUSPENSION
        DISMISSAL
    }

    AcademicStanding --> StandingLevel
```

### Grade Appeal

```mermaid
classDiagram
    class GradeAppeal {
        +UUID id
        +str appeal_number
        +UUID student_id
        +UUID enrollment_id
        +UUID exam_id
        +str original_grade
        +RequestedAction requested_action
        +str justification
        +list evidence_file_ids
        +AppealStatus status
        +EscalationLevel current_level
        +AppealOutcome outcome
        +str new_grade
        +str resolution_notes
        +UUID resolved_by_id
        +datetime filed_at
        +datetime deadline
        +submit() GradeAppeal
        +escalate() None
        +resolve(outcome: AppealOutcome, new_grade: str) None
    }

    class EscalationLevel {
        <<enumeration>>
        FACULTY
        DEPARTMENT_HEAD
        COMMITTEE
    }

    class RequestedAction {
        <<enumeration>>
        REVALUATION
        RE_EXAMINATION
        GRADE_CHANGE
    }

    GradeAppeal --> EscalationLevel
    GradeAppeal --> RequestedAction
```

### Faculty Recruitment

```mermaid
classDiagram
    class JobPosting {
        +UUID id
        +str position_number
        +str title
        +UUID department_id
        +str designation
        +EmploymentType employment_type
        +str description
        +dict qualifications
        +int experience_years_min
        +Decimal salary_range_min
        +Decimal salary_range_max
        +int vacancies
        +datetime application_deadline
        +PostingStatus status
        +bool is_internal_only
        +dict screening_criteria
        +publish() None
        +close() None
        +auto_screen(application: JobApplication) int
    }

    class JobApplication {
        +UUID id
        +str application_number
        +UUID posting_id
        +str applicant_name
        +str applicant_email
        +UUID resume_file_id
        +dict qualifications
        +ApplicationStatus status
        +int screening_score
        +bool screening_passed
        +list interview_evaluations
        +Decimal overall_score
        +dict offer_details
        +datetime offer_deadline
        +apply() JobApplication
        +shortlist() None
        +schedule_interview(date: datetime, panel: list) None
        +extend_offer(details: dict) None
        +hire() None
        +reject(reason: str) None
    }

    class InterviewEvaluation {
        +UUID id
        +UUID application_id
        +UUID evaluator_id
        +int teaching_score
        +int research_score
        +int domain_knowledge_score
        +int communication_score
        +Decimal overall_score
        +str comments
        +str recommendation
        +submit() InterviewEvaluation
    }

    class PostingStatus {
        <<enumeration>>
        DRAFT
        PUBLISHED
        CLOSED
        FILLED
        CANCELLED
    }

    class ApplicationStatus {
        <<enumeration>>
        APPLIED
        SCREENED
        SHORTLISTED
        INTERVIEW_SCHEDULED
        INTERVIEWED
        OFFERED
        HIRED
        REJECTED
        WITHDRAWN
        EXPIRED
    }

    JobPosting --> PostingStatus
    JobPosting "1" --> "many" JobApplication : receives
    JobApplication --> ApplicationStatus
    JobApplication "1" --> "many" InterviewEvaluation : evaluated by
```

### Room & Facility Management

```mermaid
classDiagram
    class Room {
        +UUID id
        +str room_code
        +str building
        +int floor
        +str room_number
        +RoomType room_type
        +int capacity
        +list amenities
        +bool is_wheelchair_accessible
        +RoomStatus status
        +check_availability(date: date, start: time, end: time) bool
        +get_utilization(start_date: date, end_date: date) Decimal
    }

    class RoomBooking {
        +UUID id
        +UUID room_id
        +UUID booked_by_id
        +BookingType booking_type
        +str purpose
        +date booking_date
        +time start_time
        +time end_time
        +int expected_attendees
        +bool is_recurring
        +dict recurrence_pattern
        +BookingStatus status
        +book() RoomBooking
        +cancel() None
        +confirm() None
    }

    class RoomType {
        <<enumeration>>
        CLASSROOM
        LAB
        AUDITORIUM
        CONFERENCE
        OFFICE
        LIBRARY
        EXAM_HALL
    }

    Room --> RoomType
    Room "1" --> "many" RoomBooking : has
```

### Transfer Credits

```mermaid
classDiagram
    class TransferCredit {
        +UUID id
        +UUID student_id
        +str source_institution
        +str source_course_code
        +str source_course_name
        +int source_credits
        +str source_grade
        +UUID equivalent_course_id
        +int credits_awarded
        +TransferStatus status
        +UUID evaluated_by_id
        +str evaluation_notes
        +bool counts_toward_gpa
        +bool counts_toward_graduation
        +submit() TransferCredit
        +evaluate(status: TransferStatus, equivalent: UUID) None
        +appeal() None
    }

    class ArticulationAgreement {
        +UUID id
        +str institution_name
        +date effective_date
        +date expiry_date
        +list course_mappings
        +bool is_active
        +find_mapping(external_code: str) CourseMapping
    }

    class TransferStatus {
        <<enumeration>>
        SUBMITTED
        UNDER_REVIEW
        APPROVED
        REJECTED
        APPEALED
    }

    TransferCredit --> TransferStatus
    ArticulationAgreement "1" --> "many" TransferCredit : facilitates
```

### Scholarship & Financial Aid

```mermaid
classDiagram
    class ScholarshipProgram {
        +UUID id
        +str name
        +ScholarshipType scholarship_type
        +str description
        +dict eligibility_criteria
        +Decimal award_amount
        +Decimal award_percentage
        +int max_recipients
        +Decimal fund_total
        +Decimal fund_utilized
        +dict renewal_criteria
        +bool is_auto_award
        +bool is_active
        +check_eligibility(student_id: UUID) bool
        +check_fund_balance() Decimal
        +award(student_id: UUID, amount: Decimal) ScholarshipAward
    }

    class ScholarshipAward {
        +UUID id
        +UUID scholarship_id
        +UUID student_id
        +UUID semester_id
        +AwardStatus status
        +Decimal award_amount
        +DisbursementMethod disbursement_method
        +UUID linked_invoice_id
        +RenewalStatus renewal_status
        +apply() ScholarshipAward
        +approve(amount: Decimal) None
        +disburse(invoice_id: UUID) None
        +check_renewal() RenewalStatus
        +revoke(reason: str) None
    }

    class ScholarshipType {
        <<enumeration>>
        MERIT
        NEED_BASED
        ATHLETIC
        DEPARTMENTAL
        DONOR
        GOVERNMENT
    }

    class AwardStatus {
        <<enumeration>>
        APPLIED
        UNDER_REVIEW
        AWARDED
        REJECTED
        DISBURSED
        REVOKED
        WAITLISTED
    }

    ScholarshipProgram --> ScholarshipType
    ScholarshipProgram "1" --> "many" ScholarshipAward : awards
    ScholarshipAward --> AwardStatus
```

### Department & Curriculum

```mermaid
classDiagram
    class Department {
        +UUID id
        +str code
        +str name
        +str parent_faculty
        +UUID head_id
        +date head_term_start
        +date head_term_end
        +int sanctioned_positions
        +int filled_positions
        +str accreditation_status
        +date accreditation_expiry
        +assign_head(faculty_id: UUID, term_start: date, term_end: date) None
        +get_statistics() dict
    }

    class CurriculumChangeProposal {
        +UUID id
        +str proposal_number
        +UUID program_id
        +UUID proposed_by_id
        +ChangeType change_type
        +str description
        +str justification
        +dict impact_analysis
        +ProposalStatus status
        +UUID effective_semester_id
        +submit() CurriculumChangeProposal
        +advance(approval_notes: str) None
        +reject(reason: str) None
    }

    class ChangeType {
        <<enumeration>>
        ADD_COURSE
        REMOVE_COURSE
        MODIFY_COURSE
        MODIFY_PREREQUISITES
        MODIFY_CREDITS
        RESTRUCTURE
    }

    class ProposalStatus {
        <<enumeration>>
        DRAFT
        DEPT_REVIEW
        ACADEMIC_BOARD
        SENATE
        APPROVED
        REJECTED
    }

    Department "1" --> "many" CurriculumChangeProposal : proposes
    CurriculumChangeProposal --> ChangeType
    CurriculumChangeProposal --> ProposalStatus
```

---

### Admission Cycle & Examination Management

```mermaid
classDiagram
    class AdmissionCycle {
        +UUID id
        +UUID program_id
        +str name
        +date open_date
        +date close_date
        +int seat_limit
        +bool entrance_exam_required
        +CycleStatus status
        +datetime published_at
        +publish() None
        +close() None
        +complete() None
    }

    class CycleStatus {
        <<enumeration>>
        DRAFT
        PUBLISHED
        CLOSED
        COMPLETED
    }

    class EntranceExam {
        +UUID id
        +UUID cycle_id
        +str title
        +int duration_minutes
        +Decimal total_marks
        +Decimal passing_marks
        +bool auto_score
        +ExamStatus status
        +schedule(exam_date: date) None
        +startExam() None
        +finalizeScores() None
    }

    class ExamStatus {
        <<enumeration>>
        CONFIGURED
        SCHEDULED
        IN_PROGRESS
        COMPLETED
        SCORES_FINALIZED
    }

    class ExamResult {
        +UUID id
        +UUID exam_id
        +UUID applicant_id
        +Decimal score
        +int rank
        +datetime submitted_at
    }

    class MeritList {
        +UUID id
        +UUID cycle_id
        +int total_ranked
        +Decimal cutoff_score
        +MeritListStatus status
        +generate() MeritList
        +publish() None
        +autoAwardScholarships(top_n: int) list
    }

    class MeritListStatus {
        <<enumeration>>
        DRAFT
        PUBLISHED
    }

    class MeritListEntry {
        +UUID id
        +UUID merit_list_id
        +UUID applicant_id
        +int rank
        +Decimal composite_score
        +bool scholarship_eligible
    }

    AdmissionCycle --> CycleStatus
    AdmissionCycle "1" --> "0..1" EntranceExam : has
    AdmissionCycle "1" --> "0..1" MeritList : produces
    EntranceExam --> ExamStatus
    EntranceExam "1" --> "many" ExamResult : has
    MeritList --> MeritListStatus
    MeritList "1" --> "many" MeritListEntry : contains
```

---

### Semester Progression Management

```mermaid
classDiagram
    class SemesterProgressionService {
        +assignNextSemester(student_id: UUID, semester_id: UUID) SemesterEnrollment
        +repeatSemester(student_id: UUID, repeat_semester_number: int) SemesterEnrollment
        +checkEligibility(student_id: UUID) EligibilityResult
        +bulkAssign(student_ids: list, semester_id: UUID) list
    }

    class EligibilityResult {
        +bool eligible
        +str reason
        +int current_semester
        +int next_semester
        +str recommended_action
    }

    class ClassroomAssignment {
        +UUID id
        +UUID student_id
        +UUID semester_id
        +UUID classroom_id
        +UUID assigned_by
        +datetime assigned_at
    }

    class FacultySubjectAssignment {
        +UUID id
        +UUID faculty_id
        +UUID subject_id
        +UUID classroom_id
        +UUID semester_id
        +datetime assigned_at
        +validate() bool
        +checkLoadLimit() bool
    }

    SemesterProgressionService --> EligibilityResult : returns
    SemesterProgressionService "1" --> "many" ClassroomAssignment : creates
    FacultySubjectAssignment --> ClassroomAssignment : linked via classroom
```
