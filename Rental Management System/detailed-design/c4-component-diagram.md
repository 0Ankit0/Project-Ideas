# C4 Component Diagram

## Overview
C4 Level 3 — Component diagram showing the internal components of the REST API container in the rental management system.

---

## REST API Components

```mermaid
graph TB
    subgraph "REST API Container"
        subgraph "API Layer"
            Router[Request Router]
            AuthMiddleware[Auth Middleware<br>JWT Validation + RBAC]
            ValidationMiddleware[Validation Middleware<br>Schema + Business Rules]
            RateLimiter[Rate Limiter]
            WebhookHandler[Webhook Handler<br>Payment + E-Sign]
        end

        subgraph "IAM Component"
            AuthController[Auth Controller]
            AuthService[Auth Service]
            TokenManager[Token Manager<br>JWT Issue + Revoke]
            OTPService[OTP Service]
            IDVerifyService[ID Verification Service]
        end

        subgraph "Asset & Listing Component"
            AssetController[Asset Controller]
            AssetService[Asset Service]
            CategoryService[Category Service]
            AvailabilityService[Availability Service]
            SearchService[Search Service]
        end

        subgraph "Booking Component"
            BookingController[Booking Controller]
            BookingService[Booking Service]
            AvailabilityLockService[Availability Lock Service<br>Redis-backed]
        end

        subgraph "Pricing Component"
            PricingController[Pricing Controller]
            PricingEngine[Pricing Engine]
            TaxCalculator[Tax Calculator]
        end

        subgraph "Agreement Component"
            AgreementController[Agreement Controller]
            AgreementService[Agreement Service]
            TemplateRenderer[Template Renderer]
            ESignService[E-Sign Integration Service]
        end

        subgraph "Payment Component"
            PaymentController[Payment Controller]
            InvoiceService[Invoice Service]
            PaymentService[Payment Service]
            PayoutService[Payout Service]
            DepositService[Deposit Service]
            ChargeService[Additional Charge Service]
        end

        subgraph "Assessment Component"
            AssessmentController[Assessment Controller]
            AssessmentService[Assessment Service]
            ComparisonEngine[Comparison Engine<br>Pre vs Post]
            ReportGenerator[Assessment Report Generator]
        end

        subgraph "Maintenance Component"
            MaintenanceController[Maintenance Controller]
            MaintenanceService[Maintenance Service]
            PreventiveService[Preventive Service Manager]
        end

        subgraph "Reporting Component"
            ReportController[Report Controller]
            ReportService[Report Service]
            ExportBuilder[Export Builder<br>PDF + CSV]
        end

        subgraph "Notification Component"
            EventBus[Domain Event Bus]
            NotificationService[Notification Service]
            WSManager[WebSocket Manager]
        end

        subgraph "Shared Infrastructure"
            ORM[ORM / Repository Layer]
            StorageAdapter[Storage Adapter]
            PayGWAdapter[Payment Gateway Adapter]
            ESignAdapter[E-Signature Adapter]
            IDAdapter[Identity Verification Adapter]
            MessagingAdapter[Messaging Adapter<br>Email + SMS + Push]
        end
    end

    Router --> AuthMiddleware
    AuthMiddleware --> ValidationMiddleware
    ValidationMiddleware --> AuthController
    ValidationMiddleware --> AssetController
    ValidationMiddleware --> BookingController
    ValidationMiddleware --> PricingController
    ValidationMiddleware --> AgreementController
    ValidationMiddleware --> PaymentController
    ValidationMiddleware --> AssessmentController
    ValidationMiddleware --> MaintenanceController
    ValidationMiddleware --> ReportController
    RateLimiter --> Router

    AuthService --> TokenManager
    AuthService --> OTPService
    AuthService --> IDVerifyService
    IDVerifyService --> IDAdapter

    AssetService --> AvailabilityService
    AssetService --> SearchService
    BookingService --> AvailabilityLockService
    BookingService --> PricingEngine
    BookingService --> DepositService
    PricingEngine --> TaxCalculator

    AgreementService --> TemplateRenderer
    AgreementService --> ESignService
    ESignService --> ESignAdapter

    InvoiceService --> PaymentService
    PaymentService --> PayGWAdapter
    DepositService --> PayGWAdapter
    PayoutService --> PayGWAdapter

    AssessmentService --> ComparisonEngine
    AssessmentService --> ReportGenerator
    ReportGenerator --> StorageAdapter

    BookingService --> EventBus
    AgreementService --> EventBus
    PaymentService --> EventBus
    AssessmentService --> EventBus
    MaintenanceService --> EventBus

    EventBus --> NotificationService
    NotificationService --> WSManager
    NotificationService --> MessagingAdapter

    AuthService --> ORM
    AssetService --> ORM
    BookingService --> ORM
    AgreementService --> ORM
    PaymentService --> ORM
    AssessmentService --> ORM
    MaintenanceService --> ORM
    ReportService --> ORM
    NotificationService --> ORM

    AssetService --> StorageAdapter
    AgreementService --> StorageAdapter
    AssessmentService --> StorageAdapter
    ReportService --> StorageAdapter
    ExportBuilder --> StorageAdapter

    WebhookHandler --> PaymentService
    WebhookHandler --> ESignService
```

---

## Component Responsibilities Summary

| Component | Key Responsibility |
|-----------|-------------------|
| Auth Middleware | Validates JWT; enforces RBAC per route |
| Auth Service | Register, login, OTP, token lifecycle |
| Asset Service | Asset CRUD, availability management, search |
| Availability Lock Service | Redis-backed transactional availability reservation |
| Pricing Engine | Multi-tier rate calculation, peak pricing, tax |
| Booking Service | Booking creation, confirmation, modification, cancellation, return |
| Agreement Service | Template rendering, e-sign dispatch, webhook handling, PDF storage |
| Invoice Service | Invoice generation, line items, receipt generation |
| Payment Service | Gateway integration, webhook processing, refunds |
| Deposit Service | Deposit hold, deduction, settlement, refund |
| Charge Service | Post-rental additional charge lifecycle |
| Assessment Service | Pre/post checklist, photo storage, comparison, report generation |
| Maintenance Service | Request lifecycle, staff assignment, cost tracking |
| Notification Service | Event-driven notifications; WebSocket push; email/SMS dispatch |
| Report Service | Revenue, utilisation, tax summary report generation and export |
