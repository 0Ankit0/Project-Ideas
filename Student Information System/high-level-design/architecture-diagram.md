# High-Level Architecture Diagram

## Overview
This document describes the high-level architecture for the Student Information System (SIS). The system is designed as a modular monolith with clear domain boundaries, REST API, async notification tasks, websocket fanout, and integrations with external payment, identity, library, and communication providers.

---

## System Architecture Overview

```mermaid
graph TB
    subgraph "Clients"
        StudentWeb[Student Web Portal]
        StudentMobile[Student Mobile App]
        FacultyApp[Faculty Portal]
        AdminApp[Admin Dashboard]
        ParentApp[Parent Portal]
    end

    subgraph "Edge"
        CDN[CDN]
        WAF[WAF]
        LB[Load Balancer]
    end

    subgraph "Application"
        API[FastAPI Monolith]

        subgraph "Backend Modules"
            IAM[IAM / Auth]
            Students[Student Management]
            Courses[Course & Curriculum]
            Enrollment[Enrollment & Scheduling]
            Academics[Grades & Records]
            Attendance[Attendance Tracking]
            Fees[Fee & Financial Aid]
            Exams[Exam Management]
            Communication[Announcements & Messaging]
            Reports[Reports & Analytics]
            Notify[Notifications + Websocket Fanout]
        end
    end

    subgraph "Data"
        DB[(PostgreSQL)]
        Redis[(Redis)]
        Storage[(Object Storage)]
    end

    subgraph "External Services"
        PaymentGW[Payment Providers]
        LDAPProvider[LDAP / SSO Provider]
        LibrarySystem[Library Management System]
        ERPSystem[ERP / Finance System]
        Messaging[Email / SMS / Push]
        BiometricDevice[Biometric Devices]
    end

    StudentWeb --> CDN
    StudentMobile --> CDN
    FacultyApp --> CDN
    AdminApp --> CDN
    ParentApp --> CDN

    CDN --> WAF
    WAF --> LB
    LB --> API

    API --> IAM
    API --> Students
    API --> Courses
    API --> Enrollment
    API --> Academics
    API --> Attendance
    API --> Fees
    API --> Exams
    API --> Communication
    API --> Reports
    API --> Notify

    IAM --> DB
    Students --> DB
    Courses --> DB
    Enrollment --> DB
    Academics --> DB
    Attendance --> DB
    Fees --> DB
    Exams --> DB
    Communication --> DB
    Reports --> DB
    Notify --> DB

    IAM --> Redis
    Enrollment --> Redis
    Courses --> Redis

    Students --> Storage
    Academics --> Storage
    Exams --> Storage
    Reports --> Storage

    Fees --> PaymentGW
    IAM --> LDAPProvider
    Enrollment --> LibrarySystem
    Fees --> ERPSystem
    Notify --> Messaging
    Attendance --> BiometricDevice
```

---

## Runtime Interaction Model

```mermaid
graph LR
    Client[Client Request] --> API[FastAPI Router]
    API --> Domain[Domain Service / Repository]
    Domain --> DB[(PostgreSQL)]
    Domain --> Redis[(Redis)]

    Domain --> Event[Persisted Domain Event / Notification]
    Event --> Notify[Notification Dispatcher]
    Notify --> WS[Websocket Manager]
    Notify --> Msg[Email / SMS / Push]

    Domain --> External[Payment / Auth / Library Provider]
```

---

## Key Backend Responsibilities

| Module | Main Responsibilities |
|--------|-----------------------|
| IAM | JWT auth, SSO/LDAP integration, OTP, role-based access control |
| Student Management | Student profiles, admission workflow, parent account linking |
| Course & Curriculum | Course catalog, departments, degree programs, prerequisites |
| Enrollment & Scheduling | Course registration, waitlists, timetable generation, conflict detection |
| Grades & Records | Grade entry, GPA/CGPA calculation, academic standing, degree audit |
| Attendance Tracking | Session attendance, biometric integration, leave management, alerts |
| Fee & Financial Aid | Fee structures, invoicing, payment processing, scholarship management |
| Exam Management | Exam scheduling, hall allocation, hall tickets, seating plans |
| Announcements & Messaging | Announcements, internal messaging, event management |
| Reports & Analytics | Enrollment, grade, attendance, and financial reports; dashboards |
| Notifications | Persisted notifications, websocket fanout, email/SMS/push delivery |

---

## Current Design Decisions

- The system is documented as a modular monolith with clear domain module separation
- Authentication supports both local credentials and LDAP/SSO for institutional identity
- Attendance supports both manual marking and biometric/QR-code based automation
- Notification fanout covers grade publication, attendance alerts, fee reminders, and exam events
