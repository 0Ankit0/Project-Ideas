# Class Diagrams

## Overview
Detailed class diagrams for the core modules of the Employee Management System.

---

## 1. Employee & Organization Module

```mermaid
classDiagram
    class User {
        +int id
        +String email
        +String hashedPassword
        +bool isSuperuser
        +bool otpEnabled
        +bool otpVerified
        +DateTime createdAt
        +login(email, password) Token
        +logout() void
        +enableOTP() void
    }

    class Employee {
        +int id
        +int userId
        +String employeeId
        +String firstName
        +String lastName
        +String phone
        +Date dateOfBirth
        +Date dateOfJoining
        +Date dateOfLeaving
        +EmploymentStatus status
        +int departmentId
        +int designationId
        +int gradeId
        +int reportingManagerId
        +String locationCode
        +getFullName() String
        +isActive() bool
        +getYearsOfService() float
    }

    class Department {
        +int id
        +String name
        +String code
        +int parentDepartmentId
        +int costCenterId
        +int headEmployeeId
        +getChildren() List~Department~
        +getHeadCount() int
    }

    class Designation {
        +int id
        +String title
        +int gradeId
        +String level
    }

    class Grade {
        +int id
        +String code
        +String name
        +float minSalary
        +float maxSalary
    }

    class OnboardingChecklist {
        +int id
        +int employeeId
        +DateTime completedAt
        +getProgress() float
    }

    class OnboardingTask {
        +int id
        +int checklistId
        +String title
        +String assignedRole
        +int assignedUserId
        +bool isCompleted
        +Date dueDate
        +DateTime completedAt
        +complete(userId) void
    }

    User "1" --> "1" Employee : linked to
    Employee "many" --> "1" Department : belongs to
    Employee "many" --> "1" Designation : holds
    Designation "many" --> "1" Grade : mapped to
    Employee "many" --> "1" Employee : reports to
    Employee "1" --> "1" OnboardingChecklist : has
    OnboardingChecklist "1" --> "many" OnboardingTask : contains
```

---

## 2. Leave Management Module

```mermaid
classDiagram
    class LeaveType {
        +int id
        +int policyId
        +String name
        +String code
        +float annualEntitlement
        +bool isPaid
        +bool carryForwardAllowed
        +float maxCarryForward
        +bool encashmentAllowed
        +int minNoticeDays
        +int maxConsecutiveDays
    }

    class LeaveBalance {
        +int id
        +int employeeId
        +int leaveTypeId
        +int year
        +float entitled
        +float accrued
        +float used
        +float pending
        +float lapsed
        +float carriedForward
        +getAvailable() float
        +canApply(days) bool
    }

    class LeaveRequest {
        +int id
        +int employeeId
        +int leaveTypeId
        +Date startDate
        +Date endDate
        +float calculatedDays
        +String reason
        +LeaveStatus status
        +int approverId
        +String approverComment
        +DateTime submittedAt
        +DateTime decidedAt
        +approve(approverId, comment) void
        +reject(approverId, comment) void
        +cancel() void
        +calculateDays(holidays) float
    }

    class HolidayCalendar {
        +int id
        +String name
        +String locationCode
        +int year
    }

    class Holiday {
        +int id
        +int calendarId
        +Date date
        +String name
        +bool isOptional
    }

    LeaveBalance "many" --> "1" LeaveType
    LeaveRequest "many" --> "1" LeaveType
    LeaveRequest "many" --> "1" LeaveBalance : deducts from
    HolidayCalendar "1" --> "many" Holiday
```

---

## 3. Payroll Module

```mermaid
classDiagram
    class SalaryStructure {
        +int id
        +int employeeId
        +float basicPay
        +float hra
        +float transportAllowance
        +float medicalAllowance
        +float specialAllowance
        +float grossCtc
        +Date effectiveFrom
        +Date effectiveTo
        +computeGross() float
    }

    class PayrollRun {
        +int id
        +String period
        +Date periodStart
        +Date periodEnd
        +PayrollRunStatus status
        +int initiatedBy
        +DateTime initiatedAt
        +DateTime finalizedAt
        +initiate() void
        +finalize(approvedBy) void
        +getExceptions() List~PayrollException~
    }

    class PayrollRecord {
        +int id
        +int runId
        +int employeeId
        +float basicPay
        +float hra
        +float otherAllowances
        +float grossPay
        +float lopDays
        +float lopDeduction
        +float overtimePay
        +float pfEmployee
        +float pfEmployer
        +float esiEmployee
        +float esiEmployer
        +float tds
        +float totalDeductions
        +float reimbursements
        +float bonuses
        +float netPay
        +computeNetPay() float
    }

    class Payslip {
        +int id
        +int recordId
        +String pdfUrl
        +DateTime generatedAt
        +bool isDelivered
        +DateTime deliveredAt
        +generate() String
        +deliver(email) void
    }

    class TaxDeclaration {
        +int id
        +int employeeId
        +int financialYear
        +float section80c
        +float hra
        +float other
        +float totalDeclared
        +DeclarationStatus status
    }

    class ExpenseClaim {
        +int id
        +int employeeId
        +String category
        +float amount
        +String receiptUrl
        +ClaimStatus status
        +int approverId
        +int payrollRunId
        +DateTime submittedAt
        +approve(approverId) void
        +reject(approverId, reason) void
    }

    PayrollRun "1" --> "many" PayrollRecord
    PayrollRecord "many" --> "1" SalaryStructure
    PayrollRecord "1" --> "1" Payslip
    PayrollRecord "many" --> "many" ExpenseClaim : includes
    Employee --> TaxDeclaration : files
```

---

## 4. Performance Management Module

```mermaid
classDiagram
    class AppraisalCycle {
        +int id
        +String name
        +CycleType type
        +Date startDate
        +Date endDate
        +Date selfAssessmentDeadline
        +Date managerReviewDeadline
        +CycleStatus status
        +launch() void
        +close() void
    }

    class Goal {
        +int id
        +int employeeId
        +int cycleId
        +String title
        +String description
        +float weightage
        +float progressPercent
        +GoalStatus status
        +Date deadline
        +updateProgress(percent, notes) void
    }

    class KRA {
        +int id
        +int cycleId
        +String name
        +float weightage
    }

    class PerformanceReview {
        +int id
        +int cycleId
        +int employeeId
        +int reviewerId
        +float selfScore
        +float managerScore
        +float finalScore
        +ReviewStatus status
        +String managerRecommendation
        +submitSelfAssessment(ratings, comments) void
        +submitManagerReview(ratings, comments, recommendation) void
        +finalize(hrUserId) void
        +computeWeightedScore() float
    }

    class KRARating {
        +int id
        +int reviewId
        +int kraId
        +float selfRating
        +String selfComment
        +float managerRating
        +String managerComment
        +float finalRating
    }

    class PIP {
        +int id
        +int employeeId
        +int initiatedBy
        +Date startDate
        +Date endDate
        +String objectives
        +PIPStatus status
        +DateTime closedAt
        +String outcome
        +initiateCheckIn(notes) void
        +close(outcome) void
    }

    AppraisalCycle "1" --> "many" PerformanceReview
    AppraisalCycle "1" --> "many" Goal
    AppraisalCycle "1" --> "many" KRA
    PerformanceReview "1" --> "many" KRARating
    KRArating "many" --> "1" KRA
    Employee --> PIP : subject of
```
