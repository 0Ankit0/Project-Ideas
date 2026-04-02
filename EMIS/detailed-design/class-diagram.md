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
