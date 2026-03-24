# C4 Code Diagram

## Overview
C4 Level 4 code-level diagrams for key classes within the Employee Management System's most critical modules.

---

## Payroll Calculation Engine - Code Diagram

```mermaid
classDiagram
    class PayrollRunService {
        -EmployeeRepository employeeRepo
        -SalaryStructureRepository salaryRepo
        -AttendanceRepository attendanceRepo
        -TaxEngine taxEngine
        -PayrollRepository payrollRepo
        -PayslipService payslipService
        -NotificationDispatcher notifDispatcher
        +initiate(period, initiatedBy) PayrollRun
        +getExceptions(runId) List~PayrollException~
        +override(runId, employeeId, overrides) void
        +approve(runId, approverId) void
        -processEmployee(run, employee) PayrollRecord
        -lockPeriodData(period) void
    }

    class SalaryCalculator {
        -TaxEngine taxEngine
        +computeGross(structure) float
        +computeLOP(lopDays, workingDays, gross) float
        +computeNetPay(gross, deductions) float
        +buildRecord(employee, structure, attendance) PayrollRecord
    }

    class TaxEngine {
        -TaxSlabRepository taxSlabRepo
        +computeTDS(annualIncome, declarations) float
        +computePFEmployee(basic) float
        +computePFEmployer(basic) float
        +computeESIEmployee(gross) float
        +computeESIEmployer(gross) float
        +computeGratuityAccrual(basic, yearsOfService) float
    }

    class PayslipService {
        -StorageService storageService
        -EmailService emailService
        -PayslipRepository payslipRepo
        +generate(record) Payslip
        +generateAll(runId) List~Payslip~
        +deliver(payslip, email) void
        +deliverAll(runId) void
        -renderPDF(record) bytes
    }

    PayrollRunService --> SalaryCalculator : uses
    PayrollRunService --> PayslipService : triggers
    SalaryCalculator --> TaxEngine : delegates tax computation
```

---

## Leave Application Service - Code Diagram

```mermaid
classDiagram
    class LeaveApplicationService {
        -LeavePolicyEngine policyEngine
        -LeaveBalanceRepository balanceRepo
        -LeaveRequestRepository requestRepo
        -HolidayRepository holidayRepo
        -NotificationDispatcher notifDispatcher
        +apply(employeeId, request) LeaveRequest
        +cancel(requestId, employeeId) void
        -calculateDays(start, end, holidays) float
    }

    class LeavePolicyEngine {
        -LeavePolicyRepository policyRepo
        +validate(employeeId, request, balance) ValidationResult
        -checkMinNoticePeriod(request, policy) bool
        -checkMaxConsecutiveDays(request, policy) bool
        -checkNoOverlap(employeeId, request) bool
        -checkBalance(balance, requestedDays, policy) bool
    }

    class LeaveApprovalService {
        -LeaveRequestRepository requestRepo
        -LeaveBalanceRepository balanceRepo
        -NotificationDispatcher notifDispatcher
        +approve(requestId, approverId, comment) void
        +reject(requestId, approverId, comment) void
        +delegate(requestId, fromApproverId, toApproverId) void
    }

    class LeaveBalanceService {
        -LeaveBalanceRepository balanceRepo
        -LeavePolicyRepository policyRepo
        +getBalance(employeeId, leaveTypeId) LeaveBalance
        +accrueMonthly(employeeId) void
        +processYearEnd(year) void
        +deduct(employeeId, leaveTypeId, days) void
        +restorePending(employeeId, leaveTypeId, days) void
    }

    LeaveApplicationService --> LeavePolicyEngine : validates
    LeaveApplicationService --> LeaveBalanceService : checks balance
    LeaveApprovalService --> LeaveBalanceService : deducts on approval
```

---

## Performance Review Service - Code Diagram

```mermaid
classDiagram
    class ReviewService {
        -ReviewRepository reviewRepo
        -KRARepository kraRepo
        -RatingEngine ratingEngine
        -NotificationDispatcher notifDispatcher
        +submitSelfAssessment(reviewId, employeeId, ratings) void
        +submitManagerReview(reviewId, managerId, ratings, recommendation) void
        +finalize(reviewId, hrUserId) void
        -validateReviewOwnership(reviewId, employeeId) void
        -validateReviewWindow(cycleId, phase) void
    }

    class RatingEngine {
        +computeWeightedScore(kraRatings, kras) float
        +applyDistributionCurve(teamReviews, curve) List~AdjustedReview~
    }

    class GoalService {
        -GoalRepository goalRepo
        -NotificationDispatcher notifDispatcher
        +create(employeeId, cycleId, goalData) Goal
        +updateProgress(goalId, employeeId, percent, notes) void
        +getTeamGoals(managerId, cycleId) List~Goal~
        -checkOwnership(goalId, employeeId) void
    }

    class PIPService {
        -PIPRepository pipRepo
        -NotificationDispatcher notifDispatcher
        +initiate(employeeId, managerId, pipData) PIP
        +recordCheckIn(pipId, managerId, notes) PIPCheckIn
        +close(pipId, managerId, outcome) void
        -notifyHR(pip) void
    }

    ReviewService --> RatingEngine : computes score
    ReviewService --> GoalService : reads goal progress
```
