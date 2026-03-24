# C4 Diagrams

## Overview
C4 model diagrams for the Employee Management System at context and container levels.

---

## Level 1 - System Context Diagram

```mermaid
graph TB
    Employee((Employee\nPortal User))
    Manager((Manager\nPortal User))
    HR((HR Staff\nPortal User))
    Payroll((Payroll Officer\nPortal User))
    Admin((System Admin))

    EMS[Employee Management System\nWeb & Mobile Application\nwith REST API Backend]

    BiometricSystem[Biometric / RFID System\nAttendance Hardware]
    ERPSystem[ERP / Accounting System\nSAP / QuickBooks / Tally]
    BankSystem[Banking System\nSalary Disbursement]
    EmailSMSSvc[Email / SMS / Push\nNotification Services]
    IdP[Identity Provider\nSAML 2.0 / OAuth 2.0 SSO]

    Employee -->|Self-service: leave, payslips, timesheets, appraisals| EMS
    Manager -->|Approvals, team management, appraisals| EMS
    HR -->|Employee lifecycle, policies, org structure| EMS
    Payroll -->|Payroll runs, compliance, payslips| EMS
    Admin -->|System config, roles, audit| EMS

    BiometricSystem -->|Attendance punches| EMS
    EMS -->|Salary bank transfer| BankSystem
    EMS <-->|Employee data, payroll journals| ERPSystem
    EMS -->|Payslips, alerts, OTP| EmailSMSSvc
    EMS <-->|Enterprise SSO| IdP
```

---

## Level 2 - Container Diagram

```mermaid
graph TB
    subgraph "Employee Management System"
        WebApp[Web Application\nReact / Next.js\nSSR with API integration]
        MobileApp[Mobile App\nReact Native\nAttendance, Leave, Payslips]
        API[API Service\nFastAPI / Node.js\nREST, JWT Auth, RBAC]
        Worker[Async Worker\nCelery / BullMQ\nPayroll, Notifications, Reports]
        WSManager[WebSocket Manager\nReal-time notification push]

        DB[(Relational Database\nPostgreSQL\nPrimary data store)]
        Cache[(Cache\nRedis\nSessions, leave balances, rate limits)]
        TaskQueue[(Task Queue\nRedis / RabbitMQ\nAsync job coordination)]
        Storage[(Object Storage\nS3-compatible\nDocuments, payslips, reports)]
    end

    Employee((Employee))
    Manager((Manager))
    HR((HR Staff))
    Payroll((Payroll Officer))

    BiometricSystem[Biometric System]
    BankSystem[Banking System]
    ERPSystem[ERP System]
    Messaging[Email / SMS / Push]

    Employee -->|HTTPS| WebApp
    Employee -->|HTTPS| MobileApp
    Manager -->|HTTPS| WebApp
    HR -->|HTTPS| WebApp
    Payroll -->|HTTPS| WebApp

    WebApp -->|REST/JSON| API
    MobileApp -->|REST/JSON| API
    API -->|Read/Write| DB
    API -->|Get/Set| Cache
    API -->|Enqueue Jobs| TaskQueue
    API -->|Store/Retrieve| Storage
    API <-->|WebSocket| WSManager

    TaskQueue --> Worker
    Worker -->|Send| Messaging
    Worker -->|Transfer File| BankSystem
    Worker -->|Sync| ERPSystem

    BiometricSystem -->|REST Push| API
```

---

## Technology Choices

| Container | Technology Options | Rationale |
|-----------|-------------------|-----------|
| Web Application | React + Next.js | SSR for performance; strong ecosystem |
| Mobile App | React Native | Cross-platform; shares business logic |
| API Service | FastAPI (Python) or Node.js | High performance; async support |
| Database | PostgreSQL | ACID compliance; strong relational support for payroll |
| Cache | Redis | Fast session and balance caching |
| Task Queue | Celery + Redis / BullMQ + Redis | Reliable async payroll and notification processing |
| Object Storage | AWS S3 / MinIO | Scalable, secure document and payslip storage |
| WebSocket | Socket.IO / FastAPI WebSocket | Real-time in-app notifications |
