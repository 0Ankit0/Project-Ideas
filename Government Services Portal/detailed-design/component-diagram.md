# Component Diagram — Government Services Portal

## 1. Overview

This document describes the component architecture of the Government Services Portal at the module and package level. Components are the deployable and developable units of the system — Django apps, Next.js page groups, shared utility modules, Celery task packages, and infrastructure services. Understanding component boundaries is essential for safe parallel development, deployment isolation, and blast radius limitation during incidents.

The portal is organized into three principal component groups:
1. **Backend Components** — Django REST Framework API server, organized into Django apps by domain
2. **Frontend Components** — Next.js 14 App Router application, organized by page route and shared component library
3. **Infrastructure Components** — AWS managed services and networking layer

Each component has a clearly defined public interface (exposed endpoints or imported modules), a set of internal responsibilities, and a documented dependency on other components.

---

## 2. Backend Component Diagram

```mermaid
flowchart TD
    subgraph External["External Clients"]
        CB[Citizen Browser\nNext.js Frontend]
        OB[Officer Browser\nNext.js Frontend]
        PGWHK[ConnectIPS Webhook]
        DLWHK[Nepal Document Wallet (NDW) Webhook]
    end

    subgraph Gateway["Ingress Layer"]
        ALB[AWS ALB\nHTTPS Listener]
        WAF[AWS WAF\nRate Limiting / IP Blocking]
        NGINX[Nginx\nReverse Proxy\nStatic Headers\nGzip]
    end

    subgraph DjangoAPI["Django API Server (ECS Fargate)"]
        subgraph CoreApps["Core Django Apps"]
            AUTH[auth_app\nNIDOTPView\nJWTRefreshView\nNepal Document Wallet (NDW)OAuthView]
            CORE[core\nBaseModel\nPermissions\nExceptions\nPagination]
            SVCS[services\nServiceListView\nServiceDetailView\nEligibilityCheckView]
            APPS[applications\nApplicationCreateView\nApplicationSubmitView\nApplicationDetailView\nOfficerQueueView]
            PAYS[payments\nPaymentInitiateView\nWebhookHandlerView\nChallanDownloadView]
            DOCS[documents\nDocumentUploadView\nDocumentVerifyView\nPresignedURLView]
            NOTIF[notifications\nNotificationListView\nMarkReadView]
            GRIEV[grievances\nGrievanceCreateView\nGrievanceDetailView\nGrievanceUpdateView]
            ADMCN[admin_console\nDeptManagementView\nStaffUserView\nServiceConfigView]
            RPTS[reports\nSLAReportView\nApplicationStatsView\nPaymentReportView]
        end

        subgraph SharedUtils["Shared Utilities"]
            SM[state_machine\nWorkflowEngine\nStateProtectionMixin\nSignals]
            ENC[encryption\nAESGCMEncryptor\nKMSKeyProvider\nHasher]
            AUDT[audit_logger\nSignalReceiver\nAuditLogWriter]
            CACHE[cache_layer\nRedisCacheManager\nCacheKeyBuilder]
            PERMS[permissions\nIsCitizen\nIsOfficer\nIsDeptHead\nIsSuperAdmin\nIsAuditor]
        end

        subgraph ExternalAdapters["External Service Adapters"]
            AADHAAR[aadhaar_adapter\nUIDAPIClient\nOTPManager]
            DL[digilocker_adapter\nOAuthClient\nDocumentPuller\nCertificatePusher]
            PAYGOV[paygov_adapter\nConnectIPSClient\nChallanGenerator\nWebhookVerifier]
            S3[s3_adapter\nS3Uploader\nPresignedURLGenerator\nKMSEncryptionWrapper]
            DSC[dsc_adapter\nPKCS7Signer\nDSCKeyLoader\nFingerprintComputer]
            SMS[sms_adapter\nFast2SMSClient\nMSG91Client\nSMSRouter]
            EMAIL[email_adapter\nSESClient\nTemplateRenderer]
        end

        subgraph CeleryTasks["Celery Task Modules"]
            ATASKS[application_tasks\nsend_acknowledgment\ncheck_sla_breaches\nauto_assign_officer]
            PTASKS[payment_tasks\nprocess_payment_webhook\nsend_payment_confirmation\nreconcile_challans]
            NTASKS[notification_tasks\nsend_notification\nretry_failed_notifications]
            CTASKS[certificate_tasks\ngenerate_and_issue_certificate\nretry_digilocker_push]
            GTASKS[grievance_tasks\nacknowledge_grievance\ncheck_grievance_sla\nauto_escalate]
            MTASKS[maintenance_tasks\narchive_old_audit_logs\ncreate_quarter_partition\ncleanup_expired_drafts]
        end
    end

    subgraph DataStores["Data Stores"]
        PG[(PostgreSQL 15\nRDS Multi-AZ)]
        REDIS[(Redis 7\nElastiCache Cluster)]
        S3BUCKET[(AWS S3\nDocuments + Certs)]
        KMS[AWS KMS\nEncryption Keys]
    end

    subgraph ExternalServices["External Government APIs"]
        NASC (National Identity Management Centre)[NASC (National Identity Management Centre)\nNID Auth API]
        DLAPI[Nepal Document Wallet (NDW) API]
        PGAPI[ConnectIPS API]
        FASTSMS[SMS Gateway\nFast2SMS / MSG91]
        AWSSES[AWS SES\nEmail]
    end

    CB --> WAF
    OB --> WAF
    PGWHK --> WAF
    DLWHK --> WAF
    WAF --> ALB
    ALB --> NGINX
    NGINX --> AUTH
    NGINX --> SVCS
    NGINX --> APPS
    NGINX --> PAYS
    NGINX --> DOCS
    NGINX --> NOTIF
    NGINX --> GRIEV
    NGINX --> ADMCN
    NGINX --> RPTS

    AUTH --> CORE
    APPS --> CORE
    PAYS --> CORE
    DOCS --> CORE
    GRIEV --> CORE

    AUTH --> AADHAAR
    AUTH --> DL
    AUTH --> ENC
    AUTH --> CACHE

    APPS --> SM
    APPS --> DOCS
    APPS --> PAYS
    APPS --> ATASKS

    PAYS --> PAYGOV
    PAYS --> PTASKS
    PAYS --> CACHE

    DOCS --> S3
    DOCS --> ENC

    GRIEV --> GTASKS
    GRIEV --> SM

    ADMCN --> PERMS
    RPTS --> PG

    SM --> AUDT
    SM --> NTASKS
    SM --> CTASKS

    ATASKS --> PG
    ATASKS --> REDIS
    PTASKS --> PG
    NTASKS --> SMS
    NTASKS --> EMAIL
    NTASKS --> PG
    CTASKS --> DSC
    CTASKS --> S3
    CTASKS --> DL
    CTASKS --> PG
    GTASKS --> PG
    GTASKS --> NTASKS

    AADHAAR --> NASC (National Identity Management Centre)
    DL --> DLAPI
    PAYGOV --> PGAPI
    SMS --> FASTSMS
    EMAIL --> AWSSES
    S3 --> S3BUCKET
    ENC --> KMS

    CoreApps --> PG
    CoreApps --> REDIS
```

---

## 3. Frontend Component Diagram

```mermaid
flowchart TD
    subgraph NextJS["Next.js 14 App Router (CloudFront + ECS)"]
        subgraph Pages["Pages / Route Groups"]
            LAND[Landing Page\napp/page.tsx\nService search\nFeatured services]
            LOGIN[Login Page\napp/login/page.tsx\nNID OTP\nEmail OTP]
            DASH[Dashboard\napp/dashboard/page.tsx\nApplication summary\nNotification center]
            CAT[Service Catalog\napp/services/page.tsx\nFilter by category/dept]
            SVCDT[Service Detail\napp/services/[code]/page.tsx\nEligibility check\nApply button]
            APPFRM[Application Form\napp/apply/[code]/page.tsx\nMulti-step wizard]
            PAYP[Payment Page\napp/pay/[id]/page.tsx\nGateway selection]
            STATUS[Status Tracker\napp/status/[id]/page.tsx\nTimeline view]
            DOCVLT[Document Vault\napp/documents/page.tsx\nDiplocker integration]
            GRIEV[Grievance Portal\napp/grievances/page.tsx\nFiling + tracking]
            CERT[Certificate View\napp/certificates/[id]/page.tsx\nDownload + verify]
            ADMIN[Admin Console\napp/admin/page.tsx\nOfficer dashboard\nReports]
        end

        subgraph SharedComponents["Shared Component Library"]
            AUTHPROV[AuthProvider\ncomponents/auth/\nJWT management\nRefresh interceptor\nSession expiry handler]
            APICL[ApiClient\nlib/api-client.ts\nAxios instance\nAuth interceptor\nError normalizer]
            FORMBLD[FormBuilder\ncomponents/forms/FormBuilder.tsx\nJSON Schema driven\nConditional sections\nMulti-step wizard engine]
            DOCUP[DocumentUploader\ncomponents/documents/DocumentUploader.tsx\nDrag and drop\nProgress indicator\nFile type validation]
            PAYWID[PaymentWidget\ncomponents/payments/PaymentWidget.tsx\nGateway selection\nConnectIPS redirect\nChallan download]
            STMTLN[StatusTimeline\ncomponents/applications/StatusTimeline.tsx\nWorkflow step visualizer\nSLA indicator]
            NOTIF[NotificationCenter\ncomponents/notifications/\nBell icon + dropdown\nUnread count badge]
            A11Y[AccessibilityLayer\ncomponents/a11y/\nARIA live regions\nSkip-nav links\nFocus trap manager\nHigh-contrast toggle]
            I18N[I18nProvider\nlib/i18n/\nNext-intl integration\n12 Nepali languages]
            ERRBND[ErrorBoundary\ncomponents/ErrorBoundary.tsx\nFallback UI\nSentry integration]
        end

        subgraph StateManagement["Zustand Province Stores"]
            AUTHST[authStore\nstores/authStore.ts\ncitizen profile\naccess_token in memory\nis_authenticated]
            APPST[applicationStore\nstores/applicationStore.ts\ncurrent application\nform draft province\nstep completion map]
            NOTIFST[notificationStore\nstores/notificationStore.ts\nunread_count\nnotifications list\nSSE connection]
            UIST[uiStore\nstores/uiStore.ts\nloading provinces\nmodal visibility\ntoast queue]
        end

        subgraph NextAPIs["Next.js API Routes (BFF)"]
            AUTHAPI[app/api/auth/\nToken refresh proxy\nCookie management\nCSRF token]
            UPAPI[app/api/upload/\nPresigned URL proxy\nDirect S3 upload coordination]
        end
    end

    LOGIN --> AUTHPROV
    DASH --> AUTHPROV
    APPFRM --> FORMBLD
    APPFRM --> DOCUP
    APPFRM --> AUTHPROV
    PAYP --> PAYWID
    STATUS --> STMTLN
    DASH --> NOTIF
    DASH --> STMTLN
    DOCVLT --> DOCUP

    AUTHPROV --> AUTHST
    AUTHPROV --> APICL
    AUTHPROV --> AUTHAPI

    FORMBLD --> APPST
    FORMBLD --> APICL

    NOTIF --> NOTIFST
    NOTIF --> APICL

    PAYWID --> APPST
    PAYWID --> APICL

    DOCUP --> UPAPI
    DOCUP --> APICL

    Pages --> A11Y
    Pages --> I18N
    Pages --> ERRBND
    Pages --> UIST

    APICL --> AUTHAPI
```

---

## 4. Infrastructure Component Diagram

```mermaid
flowchart TD
    subgraph PublicInternet["Public Internet"]
        CITIZENS[Citizens & Officers\nWeb Browsers]
        NASC (National Identity Management Centre)[NASC (National Identity Management Centre) API\nexternal.uidai.gov.in]
        DLGOV[Nepal Document Wallet (NDW) API\napi.digilocker.gov.in]
        PGOV[ConnectIPS\npaygov.gov.in]
        SMSAPI[SMS Gateway\nFast2SMS / MSG91]
    end

    subgraph AWSCloud["AWS Cloud (ap-south-1)"]
        subgraph EdgeLayer["Edge / CDN Layer"]
            CF[CloudFront Distribution\nNext.js static assets\nSSL termination\nCaching headers]
            R53[Route 53\nDNS\nHealthcheck routing]
            WAFV2[AWS WAF v2\nOWASP rule groups\nGeo-blocking\nRate limiting 100 req/min per IP]
        end

        subgraph PublicSubnet["Public Subnets (AZ-a, AZ-b)"]
            ALB[Application Load Balancer\nHTTPS :443\nHTTP→HTTPS redirect\nSticky sessions off]
            NATGW[NAT Gateway\nOutbound internet access for ECS tasks]
        end

        subgraph PrivateSubnet["Private Subnets (AZ-a, AZ-b)"]
            subgraph ECSCluster["ECS Fargate Cluster"]
                DJTSK[Django API Tasks\n2 vCPU / 4GB\nMin: 2, Max: 10\nAuto-scaling by CPU/req]
                NXTSK[Next.js Tasks\n1 vCPU / 2GB\nMin: 2, Max: 8]
                CLTSK[Celery Worker Tasks\n2 vCPU / 4GB\nMin: 3 workers (doc,notif,cert)\nMax: 12]
                CLBSK[Celery Beat Task\n0.25 vCPU / 512MB\nSingle instance scheduler]
            end

            subgraph DataTier["Data Tier"]
                RDS[RDS PostgreSQL 15\nMulti-AZ\ndb.r6g.xlarge\nEncrypted at rest]
                RDSRO[RDS Read Replica\nReporting queries\nAudit log reads]
                REDIS[ElastiCache Redis 7\nCluster mode enabled\ncache.r6g.large x 3\nIn-transit + at-rest encryption]
            end
        end

        subgraph StorageSecurity["Storage & Security"]
            S3DOCS[S3 Bucket\ngsp-documents-prod\nSSE-KMS\nVersioning enabled\nObject Lock for certs]
            S3STATIC[S3 Bucket\ngsp-static-assets-prod\nPublic read\nCloudFront OAC]
            S3LOGS[S3 Bucket\ngsp-access-logs-prod\nALB + CloudFront logs]
            KMS[AWS KMS\nCustomer Managed Key\nAuto-rotate yearly]
            SM[AWS Secrets Manager\nDSC PFX key\nDB credentials\nConnectIPS API key\nNID credentials]
            ECR[Amazon ECR\nDjango image\nNext.js image\nVulnerability scanning]
        end

        subgraph Observability["Observability"]
            CW[CloudWatch\nApplication logs\nCustom metrics\nAlarms]
            XRAY[AWS X-Ray\nDistributed tracing]
            SNS[SNS + PagerDuty\nIncident alerts]
        end

        subgraph CICD["CI/CD"]
            GHA[GitHub Actions\nBuild + Test\nDocker build + push ECR]
            CDP[AWS CodeDeploy\nBlue/Green ECS deployment]
        end
    end

    CITIZENS --> R53
    R53 --> CF
    CF --> WAFV2
    WAFV2 --> ALB
    ALB --> DJTSK
    ALB --> NXTSK

    DJTSK --> RDS
    DJTSK --> REDIS
    DJTSK --> S3DOCS
    DJTSK --> SM
    DJTSK --> KMS

    CLTSK --> RDS
    CLTSK --> REDIS
    CLTSK --> S3DOCS
    CLTSK --> SM

    DJTSK --> NATGW
    CLTSK --> NATGW
    NATGW --> NASC (National Identity Management Centre)
    NATGW --> DLGOV
    NATGW --> PGOV
    NATGW --> SMSAPI

    DJTSK --> REDIS
    CLTSK --> REDIS
    CLBSK --> REDIS

    RDS --> RDSRO
    S3DOCS --> KMS

    ECR --> DJTSK
    ECR --> NXTSK
    ECR --> CLTSK

    GHA --> ECR
    GHA --> CDP
    CDP --> DJTSK

    DJTSK --> CW
    DJTSK --> XRAY
    CW --> SNS
```

---

## 5. Component Dependency Table

| Component | Depends On | Exposes API | Protocol |
|---|---|---|---|
| auth_app | aadhaar_adapter, digilocker_adapter, cache_layer, encryption, core | REST endpoints: /api/v1/auth/* | HTTPS/JSON |
| services | core, permissions | REST endpoints: /api/v1/services/* | HTTPS/JSON |
| applications | core, services, payments, documents, state_machine, audit_logger, application_tasks | REST endpoints: /api/v1/applications/* | HTTPS/JSON |
| payments | core, paygov_adapter, cache_layer, payment_tasks | REST endpoints: /api/v1/payments/* | HTTPS/JSON |
| documents | core, s3_adapter, encryption, notification_tasks | REST endpoints: /api/v1/applications/{id}/documents/* | HTTPS/JSON (multipart) |
| notifications | core, sms_adapter, email_adapter | REST endpoints: /api/v1/notifications/* | HTTPS/JSON |
| grievances | core, state_machine, grievance_tasks | REST endpoints: /api/v1/grievances/* | HTTPS/JSON |
| admin_console | core, permissions, services, applications | REST endpoints: /api/v1/admin/* | HTTPS/JSON |
| reports | core, permissions, PostgreSQL read replica | REST endpoints: /api/v1/reports/* | HTTPS/JSON |
| state_machine | applications (ServiceApplication model), audit_logger, notification_tasks | Python API: WorkflowEngine class | Python import |
| application_tasks | applications, notifications, PostgreSQL, Redis | Celery tasks | Redis broker |
| certificate_tasks | applications, dsc_adapter, s3_adapter, digilocker_adapter, notifications | Celery tasks | Redis broker |
| payment_tasks | payments, applications, notifications | Celery tasks | Redis broker |
| notification_tasks | notifications, sms_adapter, email_adapter | Celery tasks | Redis broker |
| grievance_tasks | grievances, notifications | Celery tasks | Redis broker |
| AuthProvider (Next.js) | ApiClient, authStore, AUTHAPI route | React context | In-process |
| ApiClient (Next.js) | Django REST API | Axios HTTP client | HTTPS/JSON |
| FormBuilder (Next.js) | applicationStore, ApiClient | React component | Props/Events |
| DocumentUploader (Next.js) | ApiClient, UPAPI route, S3 | React component | Props/Events |
| PaymentWidget (Next.js) | ApiClient, applicationStore | React component | Props/Events |
| RDS PostgreSQL | KMS (encryption) | SQL | TCP/5432 (private subnet) |
| Redis ElastiCache | — | Redis protocol | TCP/6379 (private subnet) |
| S3 Documents bucket | KMS | AWS SDK / HTTPS | HTTPS/S3 API |
| AWS WAF | ALB | Rule evaluation | AWS-internal |
| CloudFront | S3 static, ALB (Next.js) | HTTP/2 CDN | HTTPS |

---

## 6. Inter-Component Communication

### 6.1 Synchronous Communication (Request/Response)

All synchronous communication between the frontend and backend uses **HTTPS REST** over the public ALB. The Django API uses DRF's content negotiation; all responses are `application/json`. The Next.js frontend uses an `ApiClient` (Axios instance) that:
- Attaches the JWT access token from in-memory `authStore` as a Bearer token header
- Intercepts 401 responses and triggers silent token refresh via the `/api/auth/` Next.js API route
- Normalizes error response shapes from the Django error standard into UI-consumable error objects

Django views to PostgreSQL use synchronous Django ORM calls. Queries are executed within the Gunicorn worker thread. All queries run within the same VPC subnet; there is no public internet hop. Connection pooling via PgBouncer (sidecar in ECS task) limits the active connections to RDS.

### 6.2 Asynchronous Communication (Celery)

Views that trigger background work call `.delay()` on Celery tasks, which serializes the task payload to JSON and pushes it to the **Redis broker**. Celery workers run in separate ECS Fargate tasks, partitioned by queue name. This ensures that a surge in certificate generation tasks (CPU-intensive) does not starve notification tasks (I/O-bound).

The task result backend is also Redis. Results are stored with a 1-hour TTL. Views that need task outcomes (rare) poll the result backend. Typically, tasks update the PostgreSQL database directly and views re-query the database.

### 6.3 Real-Time Notifications (SSE)

The Notification Center in the Next.js frontend maintains a **Server-Sent Events** connection to `/api/v1/notifications/stream/`. The Django view holds the SSE connection open using an async generator that polls Redis pub/sub for new notification events for the authenticated citizen. When a Celery task creates a notification, it also publishes to the Redis pub/sub channel `notifications:{citizen_id}`. The SSE stream receives the event and pushes it to the browser without a page reload.

### 6.4 Webhook Ingestion (ConnectIPS, Nepal Document Wallet (NDW))

ConnectIPS and Nepal Document Wallet (NDW) webhooks arrive at dedicated endpoints (`/api/v1/payments/webhook/paygov/` and `/api/v1/auth/digilocker/webhook/`). These endpoints bypass JWT authentication but implement HMAC-SHA256 signature verification using the respective vendor secrets stored in AWS Secrets Manager. After signature verification, the webhook body is enqueued as a Celery task (`process_payment_webhook.delay(...)`) and the endpoint returns `HTTP 200` immediately to prevent gateway retries. All webhook payloads are stored in `audit_logs.metadata` before task dispatch for replay capability.

---

## 7. Operational Policy Addendum

### 7.1 Component Isolation and Blast Radius Policy

Each Django app is an independently deployable unit that can be disabled via a Django feature flag without deploying new code. If the `payments` app experiences issues, the `applications` app continues to serve read operations. Circuit breakers are configured at the `ExternalAdapter` level: if `paygov_adapter` trips the circuit breaker, the `PaymentInitiateView` returns `HTTP 503 SERVICE_UNAVAILABLE` with a retry-after header. Citizens are informed via the UI that online payment is temporarily unavailable and directed to the offline challan option.

### 7.2 Frontend Component Accessibility Policy

All frontend components must conform to WCAG 2.1 Level AA. The `AccessibilityLayer` component is included in the root layout and provides: skip-to-content link, ARIA live region for dynamic status updates, focus trap management for modals, and a high-contrast mode toggle that persists in `localStorage`. Government portal requirements mandate support for screen readers (NVDA, JAWS) and keyboard-only navigation. Every form rendered by `FormBuilder` must have associated `<label>` elements, error announcements via `aria-describedby`, and logical tab order. Component accessibility compliance is verified by axe-core in the CI pipeline.

### 7.3 Component Version and Dependency Policy

Django app internal APIs (models, service classes) may change freely within a sprint as long as tests pass. Cross-app imports follow the dependency graph enforced by `import-linter`. Any change to a shared utility (`state_machine`, `encryption`, `audit_logger`) requires a cross-team review. The Next.js API client interface is versioned; breaking changes require a version bump in `lib/api-client.ts` and corresponding backend endpoint updates in the same PR. Third-party dependencies are pinned in `requirements.txt` and `package-lock.json`; updates are batched monthly and tested before merge.

### 7.4 Infrastructure Component Scaling Policy

ECS Fargate auto-scaling is configured with target tracking: Django API tasks scale at 70% CPU utilization, Celery worker tasks scale at 80% CPU utilization. The minimum task count (2 Django, 3 Celery, 2 Next.js) ensures availability during AZ failure. Scaling cooldown is 120 seconds to prevent thrashing. RDS instance class upgrades require a maintenance window; connection pool size is adjusted proportionally in the PgBouncer config. Redis cluster shard count scales horizontally; keyspace is partitioned by prefix (`session:`, `otp_txn:`, `payment_lock:`, `notifications:`) to enable targeted eviction policies per prefix.
