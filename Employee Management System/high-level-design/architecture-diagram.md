# High-Level Architecture Diagram

## Overview
This document describes the high-level architecture of the Employee Management System. The system runs as a modular monolith with domain-separated modules, async task processing, WebSocket notifications, and integrations with biometric devices, banking, and ERP systems.

---

## System Architecture Overview

```mermaid
graph TB
    subgraph "Clients"
        ESS[Employee Self-Service\nWeb / Mobile]
        MSS[Manager Self-Service\nWeb]
        HRPortal[HR Portal\nWeb]
        PayrollUI[Payroll Dashboard\nWeb]
        AdminUI[Admin Console\nWeb]
    end

    subgraph "Edge"
        CDN[CDN]
        WAF[WAF]
        LB[Load Balancer]
    end

    subgraph "Application"
        API[REST API Service]

        subgraph "Backend Modules"
            IAM[IAM & Auth]
            Employees[Employee Management]
            LeaveAttendance[Leave & Attendance]
            Payroll[Payroll]
            Performance[Performance & Goals]
            Benefits[Benefits & Compensation]
            Notifications[Notifications & WebSocket]
            Reports[Reports & Analytics]
            Admin[Admin & Configuration]
        end

        Worker[Async Task Worker]
    end

    subgraph "Data"
        DB[(PostgreSQL)]
        Redis[(Redis Cache)]
        Storage[(Object Storage)]
        Queue[(Task Queue)]
    end

    subgraph "External Services"
        BiometricSys[Biometric / RFID System]
        BankSystem[Banking / Disbursement]
        ERPSystem[ERP / Accounting]
        EmailSvc[Email Service]
        SMSSvc[SMS Gateway]
        PushSvc[Push Notification]
        IdP[Identity Provider\nSSO]
    end

    ESS --> CDN
    MSS --> CDN
    HRPortal --> CDN
    PayrollUI --> CDN
    AdminUI --> CDN

    CDN --> WAF
    WAF --> LB
    LB --> API

    API --> IAM
    API --> Employees
    API --> LeaveAttendance
    API --> Payroll
    API --> Performance
    API --> Benefits
    API --> Notifications
    API --> Reports
    API --> Admin

    IAM --> DB
    Employees --> DB
    LeaveAttendance --> DB
    Payroll --> DB
    Performance --> DB
    Benefits --> DB
    Notifications --> DB
    Reports --> DB
    Admin --> DB

    IAM --> Redis
    LeaveAttendance --> Redis
    Payroll --> Redis

    Employees --> Storage
    Payroll --> Storage
    Reports --> Storage

    Payroll --> Queue
    Reports --> Queue
    Notifications --> Queue
    Queue --> Worker

    Worker --> EmailSvc
    Worker --> SMSSvc
    Worker --> PushSvc
    Worker --> BankSystem

    API --> IdP
    BiometricSys --> API
    API <--> ERPSystem
```

---

## Runtime Interaction Model

```mermaid
graph LR
    Client[Client Request] --> API[REST API Router]
    API --> Domain[Domain Service / Repository]
    Domain --> DB[(PostgreSQL)]
    Domain --> Redis[(Redis Cache)]

    Domain --> Event[Domain Event / Notification]
    Event --> Queue[(Task Queue)]
    Queue --> Worker[Async Worker]
    Worker --> WS[WebSocket Manager]
    Worker --> Msg[Email / SMS / Push]
    Worker --> Bank[Banking System]

    BiometricDevice[Biometric Device] --> API
    API --> External[ERP / SSO]
```

---

## Key Backend Module Responsibilities

| Module | Main Responsibilities |
|--------|-----------------------|
| IAM | JWT auth, SSO integration, 2FA, RBAC, session management |
| Employee Management | Employee profiles, org structure, onboarding, offboarding, documents |
| Leave & Attendance | Leave requests, approvals, balances, attendance recording, timesheets, shifts |
| Payroll | Payroll runs, salary computation, deductions, payslips, bank transfer, compliance |
| Performance & Goals | Appraisal cycles, goal setting, KRA ratings, PIP, 360-degree feedback |
| Benefits & Compensation | Benefit plans, enrolment, salary structures, revision workflows |
| Notifications | In-app, email, SMS, push; WebSocket fanout for real-time updates |
| Reports & Analytics | HR, payroll, leave, performance reports; executive dashboards |
| Admin & Configuration | Roles, permissions, system settings, audit logs, integrations |

---

## Current Architecture Notes

- The system is designed as a modular monolith that can be decomposed into microservices if scale demands
- Payroll processing and bulk report generation are handled asynchronously via task queue
- Biometric punch events are ingested via REST API with offline buffering support
- SSO integration supports SAML 2.0 and OAuth 2.0 for enterprise clients
