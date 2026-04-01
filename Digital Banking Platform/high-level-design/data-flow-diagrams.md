---
Document ID: DBP-DFD-010
Version: 1.0.0
Status: Approved
Owner: Platform Engineering — Data Architecture
Last Updated: 2025-01-15
Classification: Internal
---

# Data Flow Diagrams — Digital Banking Platform

This document presents level-2 data flow diagrams for the three primary processing pipelines:
transaction processing, KYC data handling, and the notification delivery pipeline. Each diagram
is followed by a data classification table, a per-store retention policy, and an access control
matrix defining which services may read or write each data store.

---

## Transaction Data Flow

The transaction data flow illustrates the movement of payment data from the initial customer
request through fraud assessment, account hold, Core Banking ledger posting, payment rail
submission, and downstream consumption by notification, audit, and reporting systems.

```mermaid
flowchart LR
    A([Customer App])            -->|Transfer request
JSON / HTTPS TLS 1.3|      B{API Gateway
Kong}
    B                            -->|JWT claims + request
HTTP/2 gRPC|            C[TransactionService
Java Spring Boot]
    C                            -->|Balance query
gRPC|                          D[AccountService
Java Spring Boot]
    D                            -->|Balance + status
gRPC response|              C
    C                            -->|Transaction context
REST JSON|               E[FraudService
Python FastAPI]
    E                            -->|Risk score + recommendation
REST JSON|       C
    E                            -->|Read / write risk vectors
Redis protocol|    F[(Redis
Risk Cache)]
    C                            -->|Debit instruction
gRPC|                      D
    D                            -->|Debit confirmation
gRPC response|            C
    D                            -->|Account write
JDBC / SQL|                    G[(Account DB
PostgreSQL)]
    C                            -->|Ledger entry
ISO 20022 REST|                 H[Core Banking
Internal API]
    H                            -->|Ledger confirmation
REST|                    C
    C                            -->|Payment submission
REST|                     I[Payment Rail
ACH / SWIFT]
    I                            -->|Rail reference + ETA
REST|                   C
    C                            -->|Transaction write
JDBC / SQL|                J[(Transaction DB
PostgreSQL)]
    C                            -->|Publish event
Kafka Producer|                K[[Kafka MSK
banking.transfers.events]]
    K                            -->|Consume event
Kafka Consumer|                L[NotificationService
Go]
    K                            -->|Consume event
Kafka Consumer|                M[AuditService
Java]
    K                            -->|Consume event
Kafka Consumer|                N[ReportingService
Java]
    M                            -->|Audit write
JDBC|                            O[(Audit DB
PostgreSQL)]
    N                            -->|Metrics write
JDBC|                          P[(Reporting DB
Redshift)]
    L                            -->|Push / SMS / email
HTTPS|                    Q([Customer Notification])
```

### Transaction Data Classification

| Data Element           | Classification    | PCI DSS Scope | Contains PII | Sensitivity Level |
|------------------------|-------------------|---------------|--------------|-------------------|
| Full PAN               | PCI — CHD         | In scope       | No           | Critical          |
| Card token             | PCI — Reduced     | Reduced scope  | No           | High              |
| Account number         | PCI — CHD         | In scope       | No           | Critical          |
| Customer name          | PII               | No             | Yes          | High              |
| Transaction amount     | Financial         | No             | No           | High              |
| IP address             | PII               | No             | Yes          | Medium            |
| Device fingerprint     | PII               | No             | Yes          | Medium            |
| Rail reference number  | Financial         | No             | No           | Medium            |
| Ledger entry ID        | Internal          | No             | No           | Low               |

### Transaction Data Retention

| Data Store                              | Data Retained                      | Hot Retention              | Cold / Archive Retention     | Archival Medium              |
|-----------------------------------------|------------------------------------|----------------------------|------------------------------|------------------------------|
| Transaction DB (PostgreSQL)             | Full transaction records           | 13 months                  | —                            | —                            |
| Kafka (`banking.transfers.events`)      | Event payload                      | 7 days                     | 365 days                     | S3 via Kafka Connect S3 Sink |
| Account DB (PostgreSQL)                 | Balance history, holds, statements | Indefinite (active)        | 7 years post account closure | S3 Glacier                   |
| Audit DB (PostgreSQL)                   | Immutable audit log entries        | 7 years                    | 10 years                     | S3 Glacier Deep Archive      |
| Reporting DB (Redshift)                 | Aggregated metrics and summaries   | 13 months rolling          | 7 years                      | Redshift RA3 managed storage |
| Redis Risk Cache                        | Risk vectors, velocity counters    | 24 h TTL (auto-expire)     | Not archived                 | —                            |

### Transaction Data Access Control Matrix

| Service            | Account DB              | Transaction DB     | Redis Cache        | Kafka Topic        | Audit DB           | Reporting DB       |
|--------------------|-------------------------|--------------------|--------------------|--------------------|--------------------|--------------------|
| TransactionService | R (balance) W (debit/credit) | R / W (owner)  | No access          | Publish            | No access          | No access          |
| AccountService     | R / W (owner)           | No access          | No access          | No access          | No access          | No access          |
| FraudService       | R (balance, history)    | R (history)        | R / W              | Subscribe          | No access          | No access          |
| AuditService       | No access               | R                  | No access          | Subscribe          | W (owner)          | No access          |
| ReportingService   | No access               | R                  | No access          | Subscribe          | R                  | W (owner)          |
| NotificationService| No access               | No access          | No access          | Subscribe          | No access          | No access          |
| Admin Portal       | R (masked PAN only)     | R (masked)         | No access          | No access          | R                  | R                  |

---

## KYC Data Flow

The KYC data flow describes the path of sensitive identity documents and biometric data from
customer upload through secure storage, external provider processing, risk assessment, and
final customer profile update across bounded contexts.

```mermaid
flowchart TD
    A([Customer])                -->|Upload documents
Base64 / HTTPS TLS 1.3|      B{API Gateway
Kong}
    B                            -->|Forward submission
HTTP/2|                     C[KYCService
Python FastAPI]
    C                            -->|Store document
AWS SDK SSE-AES256|             D[(Document Store
AWS S3 Encrypted)]
    D                            -->|s3Key + versionId|                              C

    subgraph Provider_Processing [KYC Provider Processing — Onfido]
        E[Onfido API v3]         -->|Fetch doc from S3
Presigned URL HTTPS|         D
        E                        --> F[OCR Engine
Document Extraction]
        E                        --> G[Liveness Engine
Biometric Check]
        E                        --> H[PEP / Sanctions DB
Watchlist Screening]
        F                        -->|Extracted fields|                               E
        G                        -->|Liveness result|                                E
        H                        -->|Watchlist result|                               E
    end

    C                            -->|Presigned URL + applicant data
REST|           E
    E                            -->|Webhook result HMAC-signed
HTTPS|              C

    C                            -->|Assess compliance risk
gRPC|                   I[ComplianceService
Java Spring Boot]
    I                            -->|Tier recommendation
gRPC response|             C
    C                            -->|Write KYC record
SQLAlchemy / SQL|             J[(KYC DB
PostgreSQL)]
    C                            -->|Publish event
Kafka Producer|                  K[[Kafka MSK
identity.kyc.events]]

    K                            -->|Consume
Kafka Consumer|                        L[NotificationService
Go]
    K                            -->|Consume
Kafka Consumer|                        M[AuditService
Java]
    K                            -->|Consume
Kafka Consumer|                        N[AccountService
Java]
    K                            -->|Consume
Kafka Consumer|                        O[ReportingService
Java]

    N                            -->|Upgrade KYC tier
JDBC|                         P[(Account DB
PostgreSQL)]
    M                            -->|Compliance audit entry
JDBC|                   Q[(Audit DB
PostgreSQL)]
    L                            -->|Multi-channel notification
HTTPS|              R([Customer])
```

### KYC Data Classification

| Data Element             | Classification | PCI DSS Scope | Contains PII | Sensitivity Level |
|--------------------------|----------------|---------------|--------------|-------------------|
| Passport / ID image      | PII — Biometric| No            | Yes          | Critical          |
| Selfie / liveness video  | PII — Biometric| No            | Yes          | Critical          |
| Full name                | PII            | No            | Yes          | High              |
| Date of birth            | PII            | No            | Yes          | High              |
| Address                  | PII            | No            | Yes          | High              |
| Document number          | PII            | No            | Yes          | High              |
| KYC tier assigned        | Internal       | No            | No           | Medium            |
| Risk score               | Internal       | No            | No           | Medium            |
| PEP / Sanctions result   | Compliance     | No            | Partial      | High              |
| S3 object key            | Internal       | No            | No           | Low               |

### KYC Data Retention

| Data Store                          | Data Retained                    | Hot Retention    | Cold / Archive Retention | Archival Medium      |
|-------------------------------------|----------------------------------|------------------|--------------------------|----------------------|
| S3 (Document Store)                 | Identity documents, selfie video | Indefinite       | 7 years post closure     | S3 Glacier           |
| KYC DB (PostgreSQL)                 | KYC records, status, tier        | Indefinite       | 7 years                  | S3 Glacier           |
| Kafka (`identity.kyc.events`)       | KYC event payloads               | 7 days           | 7 years                  | S3 via Kafka Connect |
| Audit DB (PostgreSQL)               | KYC compliance audit log         | 7 years          | 10 years                 | S3 Glacier Deep      |

### KYC Data Access Control Matrix

| Service            | S3 Document Store       | KYC DB (PostgreSQL) | Kafka Topic        | Audit DB     | Account DB (KYC tier) |
|--------------------|-------------------------|---------------------|--------------------|--------------|------------------------|
| KYCService         | R / W (owner)           | R / W (owner)       | Publish            | No access    | No access              |
| ComplianceService  | R (read-only)           | R                   | No access          | W            | No access              |
| AccountService     | No access               | No access           | Subscribe          | No access    | W (tier update only)   |
| AuditService       | No access               | R                   | Subscribe          | W (owner)    | No access              |
| ReportingService   | No access               | R                   | Subscribe          | R            | No access              |
| NotificationService| No access               | No access           | Subscribe          | No access    | No access              |
| Admin Portal       | R (compliance review)   | R                   | No access          | R            | R                      |

---

## Notification Pipeline

The notification pipeline describes the flow from any upstream domain event through the
multi-channel delivery system — covering push, SMS, email, and in-app channels — through
to delivery confirmation, DLQ handling, and audit logging.

```mermaid
flowchart LR
    A([Any Service
Event Source])   -->|Publish domain event
Kafka Producer|     B[[Kafka MSK
Multiple Topics]]
    B                                -->|Consume event
Kafka Consumer Group|      C[NotificationService
Go Consumer]
    C                                -->|Resolve template
REST|                   D[Template Engine
Handlebars / Go text/template]
    D                                -->|Rendered content|                          C
    C                                -->|Push notification
HTTPS FCM / APNS|       E[Push Gateway
Firebase FCM
Apple APNS]
    C                                -->|SMS message
HTTPS REST|                   F[SMS Gateway
Twilio]
    C                                -->|Email HTML + text
HTTPS REST|             G[Email Gateway
SendGrid]
    C                                -->|In-app message write
PostgreSQL|          H[(In-App Store
PostgreSQL)]
    E                                -->|Delivery receipt
HTTPS callback|          C
    F                                -->|Delivery status
HTTPS webhook|            C
    G                                -->|Delivery event
HTTPS webhook|             C
    C                                -->|Write delivery record
JDBC|               I[(Delivery DB
PostgreSQL)]
    C                                -->|Failed delivery
Kafka Producer|           J[[DLQ
notifications.dlq]]
    J                                -->|Retry consume
Scheduled worker|           C
    C                                -->|Audit log entry
JDBC|                     K[(Audit DB
PostgreSQL)]
    E                                -->|Push delivered
App SDK|                   L([Customer Device])
    F                                -->|SMS delivered
Telco network|              L
    G                                -->|Email delivered
SMTP relay|               L
```

### Notification Data Classification

| Data Element             | Classification | Contains PII | Sensitivity Level | Notes                                        |
|--------------------------|----------------|--------------|-------------------|----------------------------------------------|
| Customer mobile number   | PII            | Yes          | High              | Used for SMS delivery; masked in logs        |
| Customer email address   | PII            | Yes          | High              | Used for email delivery; masked in logs      |
| Push device token        | PII            | Yes          | Medium            | Rotated by OS; not stored beyond active session |
| Notification content     | Internal       | Partial      | Medium            | May contain transaction amounts              |
| Delivery status          | Internal       | No           | Low               | Receipt codes only                           |
| Template ID              | Internal       | No           | Low               | References template registry                 |

### Notification Data Retention

| Data Store                         | Data Retained                      | Hot Retention    | Cold Retention | Archival Medium      |
|------------------------------------|------------------------------------|------------------|----------------|----------------------|
| Delivery DB (PostgreSQL)           | Notification delivery records      | 90 days          | 2 years        | S3 Glacier           |
| In-App Store (PostgreSQL)          | In-app notification messages       | 30 days (unread) | 90 days total  | —                    |
| Kafka (`notifications.dlq`)        | Failed notification payloads       | 14 days          | Not archived   | —                    |
| Audit DB (PostgreSQL)              | Notification audit log             | 7 years          | 10 years       | S3 Glacier Deep      |

### Notification Data Access Control Matrix

| Service              | Delivery DB     | In-App Store    | DLQ Topic       | Audit DB        | External Gateways    |
|----------------------|-----------------|-----------------|-----------------|-----------------|----------------------|
| NotificationService  | R / W (owner)   | R / W (owner)   | Publish         | W               | Publish (HTTPS)      |
| Retry Worker         | R / W           | No access       | Subscribe / Ack | W               | Publish (HTTPS)      |
| AuditService         | R               | No access       | No access       | W (owner)       | No access            |
| Admin Portal         | R               | R               | No access       | R               | No access            |
| Customer App         | No access       | R (own data)    | No access       | No access       | Receive only         |
