# Sequence Diagrams

## Overview
Internal sequence diagrams showing object-level interactions within the Employee Management System.

---

## 1. Leave Application - Internal Flow

```mermaid
sequenceDiagram
    participant Router as LeaveRouter
    participant Service as LeaveService
    participant PolicyValidator as LeavePolicyValidator
    participant BalanceRepo as LeaveBalanceRepository
    participant RequestRepo as LeaveRequestRepository
    participant HolidayRepo as HolidayRepository
    participant NotifService as NotificationService

    Router->>Service: applyLeave(employeeId, request)
    Service->>PolicyValidator: validate(employeeId, request)
    PolicyValidator->>BalanceRepo: getBalance(employeeId, leaveTypeId)
    BalanceRepo-->>PolicyValidator: LeaveBalance
    PolicyValidator->>HolidayRepo: getHolidays(locationCode, period)
    HolidayRepo-->>PolicyValidator: List~Holiday~
    PolicyValidator-->>Service: ValidationResult

    alt Validation Fails
        Service-->>Router: 422 ValidationError
    else Validation Passes
        Service->>RequestRepo: create(leaveRequest)
        RequestRepo-->>Service: LeaveRequest
        Service->>BalanceRepo: reservePending(employeeId, leaveTypeId, days)
        Service->>NotifService: notifyManager(request)
        NotifService-->>Service: OK
        Service-->>Router: 201 Created
    end
```

---

## 2. Payroll Run - Internal Flow

```mermaid
sequenceDiagram
    participant Router as PayrollRouter
    participant RunService as PayrollRunService
    participant EmployeeRepo as EmployeeRepository
    participant SalaryRepo as SalaryStructureRepository
    participant AttendanceRepo as AttendanceRepository
    participant TaxEngine as TaxCalculationEngine
    participant PayslipService as PayslipService
    participant NotifService as NotificationService
    participant BankAdapter as BankTransferAdapter

    Router->>RunService: initiate(period, initiatedBy)
    RunService->>RunService: lockPeriodData(period)
    RunService->>EmployeeRepo: getActiveEmployees()
    EmployeeRepo-->>RunService: List~Employee~

    loop For each Employee
        RunService->>SalaryRepo: getStructure(employeeId, period)
        SalaryRepo-->>RunService: SalaryStructure
        RunService->>AttendanceRepo: getLOPDays(employeeId, period)
        AttendanceRepo-->>RunService: lopDays
        RunService->>TaxEngine: computeDeductions(salary, declarations)
        TaxEngine-->>RunService: DeductionBreakdown
        RunService->>RunService: computeNetPay(gross, deductions)
    end

    RunService-->>Router: PayrollRunSummary + Exceptions

    Router->>RunService: approve(runId, approverId)
    RunService->>PayslipService: generateAll(runId)
    PayslipService->>NotifService: deliverPayslips(employeeList)
    RunService->>BankAdapter: submitTransferFile(runId)
    BankAdapter-->>RunService: Acknowledgement
    RunService-->>Router: 200 Finalized
```

---

## 3. Appraisal Review - Internal Flow

```mermaid
sequenceDiagram
    participant Router as AppraisalRouter
    participant ReviewService as ReviewService
    participant GoalRepo as GoalRepository
    participant KRARepo as KRARepository
    participant ReviewRepo as ReviewRepository
    participant RatingEngine as RatingCalculationEngine
    participant NotifService as NotificationService

    Router->>ReviewService: submitSelfAssessment(reviewId, ratings)
    ReviewService->>ReviewRepo: get(reviewId)
    ReviewRepo-->>ReviewService: PerformanceReview
    ReviewService->>KRARepo: getForCycle(cycleId)
    KRARepo-->>ReviewService: List~KRA~
    ReviewService->>ReviewRepo: saveKRARatings(reviewId, ratings)
    ReviewService->>ReviewRepo: updateStatus(reviewId, SELF_SUBMITTED)
    ReviewService->>NotifService: notifyManager(reviewId)
    ReviewService-->>Router: 200 OK

    Router->>ReviewService: submitManagerReview(reviewId, ratings, recommendation)
    ReviewService->>ReviewRepo: saveManagerRatings(reviewId, ratings)
    ReviewService->>RatingEngine: computeWeightedScore(kraRatings, weights)
    RatingEngine-->>ReviewService: overallScore
    ReviewService->>ReviewRepo: updateStatus(reviewId, MANAGER_SUBMITTED)
    ReviewService->>NotifService: notifyHR(reviewId)
    ReviewService-->>Router: 200 OK

    Router->>ReviewService: finalize(reviewId, hrUserId)
    ReviewService->>ReviewRepo: lockRatings(reviewId)
    ReviewService->>ReviewRepo: updateStatus(reviewId, FINALIZED)
    ReviewService->>NotifService: notifyEmployee(reviewId)
    ReviewService-->>Router: 200 OK
```

---

## 4. Attendance Punch - Internal Flow

```mermaid
sequenceDiagram
    participant BiometricAPI as BiometricEndpoint
    participant AttendanceService as AttendanceService
    participant ShiftService as ShiftService
    participant AttendanceRepo as AttendanceRepository
    participant NotifService as NotificationService

    BiometricAPI->>AttendanceService: recordPunch(employeeId, timestamp, type)
    AttendanceService->>ShiftService: getActiveShift(employeeId, date)
    ShiftService-->>AttendanceService: Shift

    alt Check-In
        AttendanceService->>AttendanceRepo: createRecord(employeeId, date, checkIn)
        AttendanceRepo-->>AttendanceService: AttendanceRecord
        AttendanceService->>AttendanceService: flagIfLate(checkIn, shiftStart)
        alt Late Arrival
            AttendanceService->>NotifService: notifyManager(employeeId, lateFlag)
        end
    else Check-Out
        AttendanceService->>AttendanceRepo: updateCheckOut(recordId, checkOut)
        AttendanceService->>AttendanceService: calculateWorkedHours(checkIn, checkOut)
        AttendanceService->>AttendanceRepo: saveWorkedHours(recordId, hours)
    end

    AttendanceService-->>BiometricAPI: 201 Created
```
