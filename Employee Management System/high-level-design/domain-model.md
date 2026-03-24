# Domain Model

## Overview
The domain model captures the key entities, their attributes, and relationships within the Employee Management System.

---

## Core Domain Model

```mermaid
classDiagram
    class Employee {
        +String employeeId
        +String firstName
        +String lastName
        +String email
        +String phone
        +Date dateOfBirth
        +Date dateOfJoining
        +EmploymentStatus status
        +Grade grade
        +Department department
        +Designation designation
        +Employee reportingManager
    }

    class Department {
        +int id
        +String name
        +String code
        +CostCenter costCenter
        +Department parent
    }

    class Designation {
        +int id
        +String title
        +Grade grade
    }

    class LeaveBalance {
        +Employee employee
        +LeaveType type
        +float entitled
        +float used
        +float pending
        +float available
    }

    class LeaveRequest {
        +int id
        +Employee employee
        +LeaveType type
        +Date startDate
        +Date endDate
        +float days
        +String reason
        +LeaveStatus status
        +Employee approver
    }

    class AttendanceRecord {
        +int id
        +Employee employee
        +Date date
        +DateTime checkIn
        +DateTime checkOut
        +float workedHours
        +AttendanceStatus status
    }

    class PayrollRun {
        +int id
        +String period
        +PayrollRunStatus status
        +Date processedAt
        +Date finalizedAt
    }

    class PayrollRecord {
        +int id
        +PayrollRun run
        +Employee employee
        +float basicPay
        +float grossPay
        +float totalDeductions
        +float netPay
    }

    class Payslip {
        +int id
        +PayrollRecord record
        +String pdfUrl
        +Date generatedAt
    }

    class AppraisalCycle {
        +int id
        +String name
        +CycleType type
        +Date startDate
        +Date endDate
        +CycleStatus status
    }

    class PerformanceReview {
        +int id
        +AppraisalCycle cycle
        +Employee employee
        +Employee reviewer
        +float overallScore
        +ReviewStatus status
    }

    class Goal {
        +int id
        +Employee employee
        +AppraisalCycle cycle
        +String title
        +float weightage
        +float progressPercent
        +GoalStatus status
    }

    Employee "1" --> "1" Department
    Employee "1" --> "1" Designation
    Employee "many" --> "1" Employee : reports to
    Employee "1" --> "many" LeaveBalance
    Employee "1" --> "many" LeaveRequest
    Employee "1" --> "many" AttendanceRecord
    Employee "1" --> "many" PayrollRecord
    Employee "1" --> "many" PerformanceReview
    Employee "1" --> "many" Goal
    PayrollRun "1" --> "many" PayrollRecord
    PayrollRecord "1" --> "1" Payslip
    AppraisalCycle "1" --> "many" PerformanceReview
    AppraisalCycle "1" --> "many" Goal
```

---

## Payroll Domain Model

```mermaid
classDiagram
    class SalaryStructure {
        +int id
        +Employee employee
        +float basicPay
        +float hra
        +float transportAllowance
        +float medicalAllowance
        +float specialAllowance
        +Date effectiveFrom
    }

    class PayrollRecord {
        +int id
        +PayrollRun run
        +Employee employee
        +SalaryStructure salaryStructure
        +float grossPay
        +float lopDeduction
        +float pfEmployee
        +float pfEmployer
        +float esiEmployee
        +float esiEmployer
        +float tds
        +float totalDeductions
        +float netPay
    }

    class ExpenseClaim {
        +int id
        +Employee employee
        +String category
        +float amount
        +String receiptUrl
        +ClaimStatus status
        +Date submittedAt
    }

    class Bonus {
        +int id
        +Employee employee
        +BonusType type
        +float amount
        +String remarks
        +PayrollRun payrollRun
    }

    PayrollRecord "1" --> "1" SalaryStructure
    PayrollRecord "many" --> "1" PayrollRun
    PayrollRecord "many" --> "many" ExpenseClaim : includes
    PayrollRecord "many" --> "many" Bonus : includes
```

---

## Leave & Attendance Domain Model

```mermaid
classDiagram
    class LeavePolicy {
        +int id
        +String name
        +String applicableTo
    }

    class LeaveType {
        +int id
        +LeavePolicy policy
        +String name
        +float annualEntitlement
        +bool carryForwardAllowed
        +float maxCarryForward
        +bool encashmentAllowed
    }

    class LeaveAccrual {
        +int id
        +Employee employee
        +LeaveType type
        +float accruedDays
        +Date accrualDate
    }

    class Shift {
        +int id
        +String name
        +Time startTime
        +Time endTime
        +ShiftType type
    }

    class ShiftAssignment {
        +int id
        +Employee employee
        +Shift shift
        +Date effectiveFrom
        +Date effectiveTo
    }

    class Timesheet {
        +int id
        +Employee employee
        +Date weekStart
        +TimesheetStatus status
        +float totalHours
    }

    class TimesheetEntry {
        +int id
        +Timesheet timesheet
        +Date date
        +String projectCode
        +float hours
        +String notes
    }

    LeavePolicy "1" --> "many" LeaveType
    LeaveType "1" --> "many" LeaveAccrual
    Shift "1" --> "many" ShiftAssignment
    Timesheet "1" --> "many" TimesheetEntry
```
