# EMIS - Entity-Relationship Diagram & Database Schema

## Overview

This document provides the complete database schema for EMIS system, showing all tables, columns, relationships, and constraints.

## Core Schema - Users & Authentication

```mermaid
erDiagram
    user_management_user {
        uuid id PK
        varchar username UK
        varchar email UK
        varchar password
        varchar first_name
        varchar last_name
        varchar role
        varchar phone
        boolean is_active
        boolean is_staff
        boolean is_superuser
        timestamp last_login
        timestamp created_at
        timestamp updated_at
    }
    
    user_management_role {
        uuid id PK
        varchar name UK
        text description
        boolean is_active
        timestamp created_at
    }
    
    user_management_permission {
        uuid id PK
        varchar name UK
        varchar codename UK
        varchar content_type
        text description
    }
    
    user_management_user_roles {
        uuid id PK
        uuid user_id FK
        uuid role_id FK
    }
    
    user_management_role_permissions {
        uuid id PK
        uuid role_id FK
        uuid permission_id FK
    }
    
    user_management_user ||--o{ user_management_user_roles : "has"
    user_management_role ||--o{ user_management_user_roles : "assigned_to"
    user_management_role ||--o{ user_management_role_permissions : "has"
    user_management_permission ||--o{ user_management_role_permissions : "granted_to"
```

## Academic Schema - Students & Faculty

```mermaid
erDiagram
    students {
        uuid id PK
        varchar student_id UK
        uuid user_id FK
        uuid program_id FK
        uuid current_semester_enrollment_id FK
        uuid application_id FK
        varchar batch
        varchar section
        varchar gender
        date date_of_birth
        varchar phone
        text address_line1
        text address_line2
        varchar city
        varchar state
        varchar postal_code
        varchar country
        varchar father_name
        varchar mother_name
        varchar guardian_first_name
        varchar emergency_contact_name
        varchar emergency_contact_phone
        varchar student_status
        integer current_program_semester_number
        timestamp created_at
        timestamp updated_at
        boolean is_active
    }
    
    faculty {
        uuid id PK
        varchar faculty_id UK
        uuid user_id FK
        uuid department_id FK
        varchar designation
        varchar qualification
        text research_interests
        date joining_date
        varchar employment_type
        decimal salary
        timestamp created_at
        timestamp updated_at
        boolean is_active
    }
    
    staff {
        uuid id PK
        varchar staff_id UK
        uuid user_id FK
        uuid department_id FK
        varchar designation
        date joining_date
        varchar employment_type
        decimal salary
        timestamp created_at
        timestamp updated_at
        boolean is_active
    }
    
    parent {
        uuid id PK
        uuid user_id FK
        uuid student_id FK
        varchar relation_type
        varchar occupation
        varchar phone
        timestamp created_at
    }
    
    students ||--|| user_management_user : "extends"
    faculty ||--|| user_management_user : "extends"
    staff ||--|| user_management_user : "extends"
    parent ||--|| user_management_user : "extends"
    parent }o--|| students : "monitors"
```

## Academic Schema - Programs & Courses

```mermaid
erDiagram
    programs {
        uuid id PK
        varchar code UK
        varchar name
        varchar degree_type
        integer duration_semesters
        integer total_credits_required
        text description
        uuid department_id FK
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }
    
    program_semesters {
        uuid id PK
        uuid program_id FK
        integer semester_number
        varchar semester_name
        integer min_credits
        integer max_credits
        timestamp created_at
    }
    
    courses {
        uuid id PK
        varchar code UK
        varchar name
        integer credits
        text description
        varchar course_type
        uuid department_id FK
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }
    
    course_prerequisites {
        uuid id PK
        uuid course_id FK
        uuid prerequisite_course_id FK
    }
    
    program_semester_courses {
        uuid id PK
        uuid program_semester_id FK
        uuid course_id FK
        boolean is_required
        timestamp created_at
    }
    
    programs ||--o{ program_semesters : "has"
    program_semesters ||--o{ program_semester_courses : "includes"
    courses ||--o{ program_semester_courses : "offered_in"
    courses ||--o{ course_prerequisites : "has"
    courses ||--o{ course_prerequisites : "prerequisite_for"
```

## Academic Schema - Enrollment & Scheduling

```mermaid
erDiagram
    academic_years {
        uuid id PK
        varchar year_code UK
        date start_date
        date end_date
        boolean is_current
        timestamp created_at
    }
    
    academic_semesters {
        uuid id PK
        uuid academic_year_id FK
        varchar semester_type
        date start_date
        date end_date
        date registration_start
        date registration_end
        boolean is_current
        timestamp created_at
    }
    
    semester_enrollments {
        uuid id PK
        uuid student_id FK
        uuid academic_semester_id FK
        uuid program_semester_id FK
        integer program_semester_number
        boolean is_active
        decimal semester_gpa
        decimal cumulative_gpa
        integer credits_enrolled
        integer credits_earned
        varchar status
        timestamp created_at
        timestamp updated_at
    }
    
    course_sections {
        uuid id PK
        uuid course_id FK
        uuid academic_semester_id FK
        uuid faculty_id FK
        uuid room_id FK
        varchar section_code
        integer capacity
        integer enrolled_count
        varchar status
        timestamp created_at
    }
    
    course_enrollments {
        uuid id PK
        uuid semester_enrollment_id FK
        uuid course_section_id FK
        varchar enrollment_status
        varchar letter_grade
        decimal grade_points
        decimal numeric_grade
        timestamp enrolled_at
        timestamp dropped_at
    }
    
    class_schedules {
        uuid id PK
        uuid course_section_id FK
        varchar day_of_week
        time start_time
        time end_time
        uuid room_id FK
        timestamp created_at
    }
    
    academic_years ||--o{ academic_semesters : "contains"
    academic_semesters ||--o{ semester_enrollments : "has"
    academic_semesters ||--o{ course_sections : "offers"
    students ||--o{ semester_enrollments : "enrolls_in"
    semester_enrollments ||--o{ course_enrollments : "contains"
    course_sections ||--o{ course_enrollments : "accepts"
    courses ||--o{ course_sections : "has_sections"
    faculty ||--o{ course_sections : "teaches"
    course_sections ||--o{ class_schedules : "scheduled_as"
```

## Facilities Schema

```mermaid
erDiagram
    buildings {
        uuid id PK
        varchar name
        varchar code UK
        integer floors
        text address
        timestamp created_at
    }
    
    rooms {
        uuid id PK
        varchar room_number UK
        uuid building_id FK
        integer capacity
        varchar room_type
        text facilities
        boolean is_available
        timestamp created_at
    }
    
    buildings ||--o{ rooms : "contains"
```

## Admissions Schema

```mermaid
erDiagram
    applications {
        uuid id PK
        varchar application_number UK
        uuid program_id FK
        varchar applicant_name
        varchar applicant_email
        varchar applicant_phone
        text address
        varchar status
        decimal application_fee
        decimal test_score
        decimal total_score
        text documents
        timestamp submitted_at
        timestamp reviewed_at
        uuid reviewed_by_id FK
        text review_notes
        timestamp created_at
    }
    
    applications ||--|| programs : "applies_to"
    applications ||--o| students : "converts_to"
```

## Exams & Grading Schema

```mermaid
erDiagram
    exams {
        uuid id PK
        uuid course_section_id FK
        varchar exam_type
        varchar title
        datetime exam_date
        integer duration_minutes
        decimal total_marks
        uuid room_id FK
        text instructions
        timestamp created_at
    }
    
    grades {
        uuid id PK
        uuid course_enrollment_id FK
        uuid exam_id FK
        decimal marks_obtained
        decimal marks_total
        varchar grade_type
        timestamp graded_at
        uuid graded_by_id FK
    }
    
    grading_schemes {
        uuid id PK
        varchar name
        text description
        boolean is_active
    }
    
    grading_scheme_ranges {
        uuid id PK
        uuid grading_scheme_id FK
        varchar letter_grade
        decimal min_percentage
        decimal max_percentage
        decimal grade_points
    }
    
    exams ||--|| course_sections : "for"
    grades ||--|| course_enrollments : "assigned_to"
  grades ||--o| exams : "from"
    grading_schemes ||--o{ grading_scheme_ranges : "defines"
```

## Finance Schema

```mermaid
erDiagram
    fee_structures {
        uuid id PK
        uuid program_id FK
        uuid academic_semester_id FK
        decimal total_amount
        boolean is_active
        timestamp created_at
    }
    
    fee_heads {
        uuid id PK
        uuid fee_structure_id FK
        varchar head_name
        decimal amount
        varchar fee_type
        boolean is_mandatory
    }
    
    student_accounts {
        uuid id PK
        uuid student_id FK
        decimal balance
        decimal total_charged
        decimal total_paid
        decimal total_outstanding
        timestamp updated_at
    }
    
    payments {
        uuid id PK
        varchar payment_id UK
        uuid student_id FK
        uuid student_account_id FK
        decimal amount
        varchar payment_method
        varchar gateway_name
        varchar transaction_id
        varchar status
        datetime payment_date
        text gateway_response
        timestamp created_at
    }
    
    transactions {
        uuid id PK
        uuid student_account_id FK
        uuid payment_id FK
        varchar transaction_type
        decimal amount
        decimal balance_after
        text description
        timestamp transaction_date
    }
    
    invoices {
        uuid id PK
        varchar invoice_number UK
        uuid student_id FK
        uuid fee_structure_id FK
        decimal amount
        date due_date
        varchar status
        timestamp created_at
    }
    
    fee_structures ||--o{ fee_heads : "contains"
    programs ||--o{ fee_structures : "has"
    students ||--|| student_accounts : "has"
    student_accounts ||--o{ transactions : "records"
    students ||--o{ payments : "makes"
    payments ||--o{ transactions : "creates"
    students ||--o{ invoices : "receives"
```

## Library Schema

```mermaid
erDiagram
    books {
        uuid id PK
        varchar isbn UK
        varchar title
        varchar author
        uuid publisher_id FK
        integer publication_year
        uuid category_id FK
        text description
        timestamp created_at
    }
    
    book_copies {
        uuid id PK
        uuid book_id FK
        varchar barcode UK
        varchar status
        varchar location
        varchar condition
        timestamp created_at
    }
    
    publishers {
        uuid id PK
        varchar name
        varchar country
        timestamp created_at
    }
    
    book_categories {
        uuid id PK
        varchar name
        varchar code UK
        timestamp created_at
    }
    
    circulations {
        uuid id PK
        uuid book_copy_id FK
        uuid student_id FK
        uuid issued_by_id FK
        date issue_date
        date due_date
        date return_date
        uuid returned_to_id FK
        varchar status
        timestamp created_at
    }
    
    library_fines {
        uuid id PK
        uuid circulation_id FK
        decimal amount
        varchar fine_type
        boolean is_paid
        date paid_date
        timestamp created_at
    }
    
    books ||--o{ book_copies : "has"
    publishers ||--o{ books : "publishes"
    book_categories ||--o{ books : "categorizes"
    book_copies ||--o{ circulations : "circulated_as"
    students ||--o{ circulations : "borrows"
    circulations ||--o| library_fines : "incurs"
```

## LMS Schema

```mermaid
erDiagram
    lms_content {
        uuid id PK
        uuid course_section_id FK
        varchar title
        varchar content_type
        text description
        varchar file_path
        integer module_number
        integer order
        datetime published_at
        uuid created_by_id FK
        timestamp created_at
    }
    
    lms_assignments {
        uuid id PK
        uuid course_section_id FK
        varchar title
        text description
        datetime due_date
        decimal max_marks
        boolean allow_late_submission
        decimal late_penalty_percent
        uuid created_by_id FK
        timestamp created_at
    }
    
    lms_submissions {
        uuid id PK
        uuid assignment_id FK
        uuid student_id FK
        varchar file_path
        text submission_text
        datetime submitted_at
        decimal marks
        text feedback
        varchar status
        uuid graded_by_id FK
        datetime graded_at
    }
    
    lms_quizzes {
        uuid id PK
        uuid course_section_id FK
        varchar title
        text description
        integer duration_minutes
        integer max_attempts
        decimal total_marks
        datetime available_from
        datetime available_until
        boolean shuffle_questions
        uuid created_by_id FK
        timestamp created_at
    }
    
    lms_questions {
        uuid id PK
        uuid quiz_id FK
        text question_text
        varchar question_type
        integer marks
        integer order
        timestamp created_at
    }
    
    lms_answers {
        uuid id PK
        uuid question_id FK
        text answer_text
        boolean is_correct
        integer order
    }
    
    lms_quiz_attempts {
        uuid id PK
        uuid quiz_id FK
        uuid student_id FK
        datetime started_at
        datetime submitted_at
        decimal score
        integer attempt_number
        text answers_json
    }
    
    lms_discussions {
        uuid id PK
        uuid course_section_id FK
        varchar topic
        boolean is_pinned
        uuid created_by_id FK
        timestamp created_at
    }
    
    lms_posts {
        uuid id PK
        uuid discussion_id FK
        uuid user_id FK
        uuid parent_post_id FK
        text content
        timestamp posted_at
    }
    
    course_sections ||--o{ lms_content : "has"
    course_sections ||--o{ lms_assignments : "has"
    lms_assignments ||--o{ lms_submissions : "receives"
    students ||--o{ lms_submissions : "submits"
    course_sections ||--o{ lms_quizzes : "has"
    lms_quizzes ||--o{ lms_questions : "contains"
    lms_questions ||--o{ lms_answers : "has"
    lms_quizzes ||--o{ lms_quiz_attempts : "attempted"
    students ||--o{ lms_quiz_attempts : "attempts"
    course_sections ||--o{ lms_discussions : "has"
    lms_discussions ||--o{ lms_posts : "contains"
    lms_posts ||--o{ lms_posts : "replies_to"
```

## Attendance Schema

```mermaid
erDiagram
    attendance_sessions {
        uuid id PK
        uuid course_section_id FK
        date session_date
        time start_time
        time end_time
        uuid marked_by_id FK
        timestamp created_at
    }
    
    attendance_records {
        uuid id PK
        uuid attendance_session_id FK
        uuid student_id FK
        varchar status
        text remarks
        timestamp marked_at
    }
    
    leave_applications {
        uuid id PK
        uuid student_id FK
        date start_date
        date end_date
        integer total_days
        varchar leave_type
        text reason
        varchar status
        uuid approved_by_id FK
        datetime approved_at
        timestamp created_at
    }
    
    course_sections ||--o{ attendance_sessions : "has"
    attendance_sessions ||--o{ attendance_records : "contains"
    students ||--o{ attendance_records : "recorded_for"
    students ||--o{ leave_applications : "applies"
```

## HR & Payroll Schema

```mermaid
erDiagram
    hr_employees {
        uuid id PK
        varchar employee_id UK
        uuid user_id FK
        uuid department_id FK
        varchar designation
        date joining_date
        date termination_date
        varchar employment_type
        varchar employment_status
        timestamp created_at
    }
    
    hr_departments {
        uuid id PK
        varchar name
        varchar code UK
        uuid head_id FK
        timestamp created_at
    }
    
    hr_payroll_periods {
        uuid id PK
        integer year
        integer month
        date start_date
        date end_date
        varchar status
        timestamp created_at
    }
    
    hr_salaries {
        uuid id PK
        uuid employee_id FK
        uuid payroll_period_id FK
        decimal basic_salary
        decimal allowances
        decimal deductions
        decimal gross_salary
        decimal net_salary
        date payment_date
        varchar status
        timestamp created_at
    }
    
    hr_leaves {
        uuid id PK
        uuid employee_id FK
        varchar leave_type
        date start_date
        date end_date
        integer days
        varchar status
        text reason
        uuid approved_by_id FK
        datetime approved_at
        timestamp created_at
    }
    
    hr_attendance {
        uuid id PK
        uuid employee_id FK
        date date
        time check_in
        time check_out
        integer hours_worked
        varchar status
        timestamp created_at
    }
    
    hr_departments ||--o{ hr_employees : "employs"
    hr_employees ||--o{ hr_salaries : "receives"
    hr_payroll_periods ||--o{ hr_salaries : "contains"
    hr_employees ||--o{ hr_leaves : "applies"
    hr_employees ||--o{ hr_attendance : "records"
```

## Hostel & Transport Schema

```mermaid
erDiagram
    hostels {
        uuid id PK
        varchar name
        varchar hostel_type
        integer capacity
        uuid warden_id FK
        timestamp created_at
    }
    
    hostel_rooms {
        uuid id PK
        uuid hostel_id FK
        varchar room_number
        integer capacity
        varchar room_type
        boolean is_available
        timestamp created_at
    }
    
    hostel_room_allocations {
        uuid id PK
        uuid room_id FK
        uuid student_id FK
        date allocation_date
        date vacate_date
        varchar status
        timestamp created_at
    }
    
    transport_routes {
        uuid id PK
        varchar route_name
        varchar route_code UK
        decimal monthly_fee
        timestamp created_at
    }
    
    transport_stops {
        uuid id PK
        uuid route_id FK
        varchar stop_name
        time pickup_time
        integer sequence_number
    }
    
    transport_vehicles {
        uuid id PK
        varchar vehicle_number UK
        varchar vehicle_type
        integer capacity
        uuid driver_id FK
        timestamp created_at
    }
    
    transport_vehicle_assignments {
        uuid id PK
        uuid vehicle_id FK
        uuid route_id FK
        date effective_from
        date effective_to
    }
    
    transport_allocations {
        uuid id PK
        uuid student_id FK
        uuid route_id FK
        uuid stop_id FK
        date allocation_date
        varchar status
        timestamp created_at
    }
    
    hostels ||--o{ hostel_rooms : "has"
    hostel_rooms ||--o{ hostel_room_allocations : "allocated_as"
    students ||--o{ hostel_room_allocations : "assigned_to"
    transport_routes ||--o{ transport_stops : "has"
    transport_vehicles ||--o{ transport_vehicle_assignments : "assigned_in"
    transport_routes ||--o{ transport_vehicle_assignments : "served_by"
    students ||--o{ transport_allocations : "uses"
    transport_routes ||--o{ transport_allocations : "allocates"
```

## Inventory Schema

```mermaid
erDiagram
    inventory_categories {
        uuid id PK
        varchar name
        varchar code UK
        timestamp created_at
    }
    
    inventory_assets {
        uuid id PK
        varchar asset_id UK
        uuid category_id FK
        varchar name
        text description
        decimal purchase_price
        date purchase_date
        uuid assigned_to_dept_id FK
        varchar status
        timestamp created_at
    }
    
    inventory_stock_items {
        uuid id PK
        varchar item_code UK
        uuid category_id FK
        varchar name
        integer quantity_available
        integer reorder_level
        varchar unit
        decimal unit_price
        timestamp created_at
    }
    
    inventory_stock_movements {
        uuid id PK
        uuid stock_item_id FK
        varchar movement_type
        integer quantity
        decimal unit_price
        datetime movement_date
        uuid performed_by_id FK
        text remarks
        timestamp created_at
    }
    
    inventory_categories ||--o{ inventory_assets : "categorizes"
    inventory_categories ||--o{ inventory_stock_items : "categorizes"
    inventory_stock_items ||--o{ inventory_stock_movements : "tracks"
```

## Notifications Schema

```mermaid
erDiagram
    notifications {
        uuid id PK
        uuid user_id FK
        varchar title
        text message
        varchar notification_type
        varchar priority
        boolean is_read
        datetime read_at
        timestamp created_at
    }
    
    notification_deliveries {
        uuid id PK
        uuid notification_id FK
        varchar channel
        varchar status
        text error_message
        datetime sent_at
    }
    
    announcements {
        uuid id PK
        varchar title
        text content
        varchar target_audience
        datetime published_at
        datetime expires_at
        uuid created_by_id FK
        timestamp created_at
    }
    
    user_management_user ||--o{ notifications : "receives"
    notifications ||--o{ notification_deliveries : "delivered_via"
```

## Key Database Constraints & Indexes

### Primary Keys
- All tables use UUID as primary key
- UUIDs provide globally unique identifiers
- Better for distributed systems and security

### Unique Constraints
- `username`, `email` (users table)
- `student_id` (students)
- `faculty_id` (faculty)
- `course_code` (courses)
- `program_code` (programs)
- Application numbers, payment IDs, ISBNs, etc.

### Foreign Key Constraints
- ON DELETE CASCADE: For dependent records (e.g., enrollments when student deleted)
- ON DELETE SET NULL: For optional references
- ON DELETE PROTECT: For critical references (e.g., cannot delete program with students)

### Indexes
Performance-critical indexes:
- `student_id`, `faculty_id`, `employee_id` (frequently queried)
- `email`, `username` (for login)
- Foreign keys (automatic in PostgreSQL)
- `created_at`, `updated_at` (for sorting/filtering)
- Composite indexes on (`student_id`, `academic_semester_id`)
- Full-text search indexes on `title`, `description` fields

### Check Constraints
- GPA between 0.0 and 4.0
- Credits > 0
- Enrollment dates logical (start before end)
- Amounts >= 0 for financial fields

## Database Statistics

- **Total Tables**: ~75+ tables
- **Core Modules**: 25 Django apps
- **Relationships**: Hundreds of foreign key relationships
- **Estimated Size**: Varies by institution (10GB - 100GB+)

## Summary

This comprehensive database schema supports all EMIS modules with:
- Proper normalization (3NF)
- Clear relationships and constraints
- Performance indexes
- Audit trails (created_at, updated_at)
- Soft deletes (is_active flags)
- UUID primary keys for security and scalability
