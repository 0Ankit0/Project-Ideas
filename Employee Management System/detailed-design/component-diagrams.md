# Component Diagrams

## Overview
Component diagrams showing the software module structure of the Employee Management System.

---

## Backend Component Diagram

```mermaid
graph TB
    subgraph "API Gateway Layer"
        Router[API Router\n/api/v1]
        Auth[Auth Middleware\nJWT Validation + RBAC]
        RateLimit[Rate Limiter]
    end

    subgraph "Domain Modules"
        IAMModule[IAM Module\nAuth, Sessions, 2FA, SSO]
        EmployeeModule[Employee Module\nProfiles, Org, Documents, Onboarding, Offboarding]
        LeaveModule[Leave Module\nRequests, Approvals, Balances, Holidays]
        AttendanceModule[Attendance Module\nPunches, Shifts, Timesheets, Comp-Off]
        PayrollModule[Payroll Module\nRuns, Computation, Payslips, Tax, Compliance]
        PerformanceModule[Performance Module\nCycles, Goals, KRAs, Reviews, PIP]
        BenefitsModule[Benefits Module\nPlans, Enrolments, Compensation]
        NotifModule[Notification Module\nIn-App, Email, SMS, Push, WebSocket]
        ReportModule[Report Module\nHR, Payroll, Leave, Performance Reports]
        AdminModule[Admin Module\nRoles, Config, Audit Logs, Integrations]
    end

    subgraph "Shared Services"
        PolicyEngine[Policy Engine\nLeave & Payroll Rules]
        TaxEngine[Tax Calculation Engine\nTDS, PF, ESI]
        DocumentService[Document Service\nUpload, Download, Expiry Tracking]
        WorkflowEngine[Workflow Engine\nApproval Chains & Escalations]
        EventBus[Domain Event Bus\nAsync Event Dispatch]
    end

    subgraph "Infrastructure"
        DB[(PostgreSQL)]
        Cache[(Redis)]
        Storage[(Object Storage)]
        Queue[(Task Queue)]
    end

    Router --> Auth
    Auth --> RateLimit
    RateLimit --> IAMModule
    RateLimit --> EmployeeModule
    RateLimit --> LeaveModule
    RateLimit --> AttendanceModule
    RateLimit --> PayrollModule
    RateLimit --> PerformanceModule
    RateLimit --> BenefitsModule
    RateLimit --> ReportModule
    RateLimit --> AdminModule

    LeaveModule --> PolicyEngine
    PayrollModule --> TaxEngine
    EmployeeModule --> DocumentService
    LeaveModule --> WorkflowEngine
    PayrollModule --> WorkflowEngine

    IAMModule --> DB
    EmployeeModule --> DB
    LeaveModule --> DB
    AttendanceModule --> DB
    PayrollModule --> DB
    PerformanceModule --> DB
    BenefitsModule --> DB
    NotifModule --> DB
    ReportModule --> DB
    AdminModule --> DB

    IAMModule --> Cache
    LeaveModule --> Cache
    PayrollModule --> Cache

    DocumentService --> Storage
    PayrollModule --> Storage
    ReportModule --> Storage

    LeaveModule --> EventBus
    PayrollModule --> EventBus
    PerformanceModule --> EventBus
    EventBus --> Queue
    Queue --> NotifModule
```

---

## Frontend Component Diagram

```mermaid
graph TB
    subgraph "Employee Self-Service (ESS)"
        ESSDashboard[Dashboard]
        ESSLeave[Leave Management\nApply, History, Balance]
        ESSAttendance[Attendance\nView, Regularize, Timesheet]
        ESSPayslip[Payslips\nView, Download]
        ESSPerformance[Performance\nGoals, Self-Assessment, Rating]
        ESSProfile[My Profile\nPersonal Info, Documents]
    end

    subgraph "Manager Self-Service (MSS)"
        MSSDashboard[Team Dashboard]
        MSSApprovals[Approvals\nLeave, Timesheet, Comp-Off]
        MSSPerformance[Performance\nAppraisals, PIP]
        MSSSchedule[Shift Roster]
        MSSReports[Team Reports]
    end

    subgraph "HR Portal"
        HREmployees[Employee Management\nCreate, Edit, Transfer, Offboard]
        HROnboarding[Onboarding\nChecklists & Tasks]
        HRPolicies[Policies\nLeave, Appraisal Config]
        HROrgChart[Org Chart]
        HRReports[HR Reports\nHeadcount, Attrition]
    end

    subgraph "Payroll Dashboard"
        PayrollRuns[Payroll Runs]
        PayrollReview[Review & Approve]
        PayrollCompliance[Compliance Reports\nForm 16, PF, ESI]
        PayrollReports[Payroll Analytics]
    end

    subgraph "Admin Console"
        AdminRoles[Roles & Permissions]
        AdminConfig[System Config]
        AdminAudit[Audit Logs]
        AdminIntegrations[Integrations]
    end

    subgraph "Shared Components"
        APIClient[API Client\nREST + Auth Interceptor]
        Notifications[Notification Bell\nIn-App Notifications]
        AuthProvider[Auth Context\nJWT Management]
    end

    ESSDashboard --> APIClient
    MSSDashboard --> APIClient
    HREmployees --> APIClient
    PayrollRuns --> APIClient
    AdminRoles --> APIClient
    APIClient --> AuthProvider
```
