# System Sequence Diagrams — Survey and Feedback Platform

## Overview

System Sequence Diagrams (SSDs) document the interactions between external actors and the platform as a black box, then progressively reveal service-level participants for key use cases. Each diagram captures a specific end-to-end system interaction with realistic message labels, HTTP methods, payload hints, and conditional/loop flows.

The five diagrams cover the most critical user journeys:
- **SSD-001**: Survey creation and publication workflow
- **SSD-002**: Survey response submission with real-time analytics
- **SSD-003**: Email distribution campaign creation and delivery
- **SSD-004**: OAuth 2.0 login flow (Google SSO)
- **SSD-005**: Asynchronous report generation and download

Notation conventions: solid arrows (`->>`) indicate synchronous calls; dashed arrows (`-->>`) indicate responses or callbacks. `activate`/`deactivate` marks show when a participant is processing. `alt`, `opt`, and `loop` blocks show conditional and iterative behaviour.

---

## SSD-001: Create and Publish Survey

This sequence covers a survey creator building a survey in the SPA, saving it, adding questions, and publishing it to make it live for respondents.

```mermaid
sequenceDiagram
    actor Creator as Survey Creator
    participant Browser
    participant APIGW as API Gateway
    participant SurveySvc as Survey Service
    participant DB as PostgreSQL
    participant Redis
    participant Queue as Celery Queue
    participant EmailSvc as Notification Service

    Creator->>Browser: Navigate to "New Survey", enter title and settings
    Browser->>+APIGW: POST /api/surveys {title, settings, workspace_id}
    APIGW->>APIGW: Validate JWT, check workspace membership
    APIGW->>+SurveySvc: Forward POST /surveys
    SurveySvc->>SurveySvc: Validate payload via Pydantic v2 model
    SurveySvc->>+DB: INSERT INTO surveys (id, workspace_id, title, status='draft')
    DB-->>-SurveySvc: survey_id returned
    SurveySvc-->>-APIGW: 201 Created {survey_id, status: draft}
    APIGW-->>-Browser: 201 Created {survey_id, status: draft}
    Browser-->>Creator: Survey builder opens with new survey_id

    loop For each question (1..N)
        Creator->>Browser: Add question (type, text, options, validation)
        Browser->>+APIGW: POST /api/surveys/{survey_id}/questions {type, text, order}
        APIGW->>+SurveySvc: Forward POST /surveys/{id}/questions
        SurveySvc->>+DB: INSERT INTO questions (id, survey_id, type, text, order_index)
        DB-->>-SurveySvc: question_id returned
        SurveySvc-->>-APIGW: 201 Created {question_id}
        APIGW-->>-Browser: 201 Created {question_id}
    end

    Creator->>Browser: Click "Publish Survey"
    Browser->>+APIGW: PATCH /api/surveys/{survey_id}/publish
    APIGW->>+SurveySvc: Forward PATCH /surveys/{id}/publish
    SurveySvc->>+DB: SELECT survey with questions WHERE id = survey_id
    DB-->>-SurveySvc: Survey + questions list

    alt Survey has fewer than 1 question
        SurveySvc-->>APIGW: 422 Unprocessable Entity {error: min_questions_required}
        APIGW-->>Browser: 422 Unprocessable Entity
        Browser-->>Creator: Show validation error
    else Survey valid for publication
        SurveySvc->>+DB: UPDATE surveys SET status='published', published_at=NOW()
        DB-->>-SurveySvc: OK
        SurveySvc->>Redis: PUBLISH survey:{survey_id}:events {type: published}
        SurveySvc->>+Queue: Enqueue task notify_collaborators(survey_id, event=published)
        Queue-->>-SurveySvc: task_id
        SurveySvc-->>-APIGW: 200 OK {survey_id, status: published, public_url}
        APIGW-->>-Browser: 200 OK {public_url}
        Browser-->>Creator: Show success + shareable survey URL
        Queue->>+EmailSvc: Execute notify_collaborators task
        EmailSvc->>EmailSvc: Render Jinja2 email template
        EmailSvc-->>-Queue: Task complete (notifications sent)
    end
```

---

## SSD-002: Submit Survey Response

This sequence covers a respondent loading a published survey, answering questions, and submitting — with real-time analytics updating in the background.

```mermaid
sequenceDiagram
    actor Respondent
    participant Browser as Browser/PWA
    participant CDN as AWS CloudFront
    participant APIGW as API Gateway
    participant ResponseSvc as Response Service
    participant SurveySvc as Survey Service
    participant DB as PostgreSQL
    participant Mongo as MongoDB
    participant Redis
    participant Kinesis as AWS Kinesis
    participant Lambda as Analytics Lambda
    participant DynDB as DynamoDB

    Respondent->>Browser: Open survey public URL
    Browser->>+CDN: GET /s/{survey_slug}
    CDN-->>-Browser: Serve cached survey shell HTML

    Browser->>+APIGW: GET /api/surveys/{survey_id}/public
    APIGW->>+SurveySvc: GET /surveys/{id}/public
    SurveySvc->>+DB: SELECT survey + questions + options WHERE id=survey_id AND status=published
    DB-->>-SurveySvc: Survey definition
    SurveySvc-->>-APIGW: 200 OK {survey, questions, settings}
    APIGW-->>-Browser: Survey definition JSON

    Browser->>+APIGW: POST /api/responses/sessions {survey_id}
    APIGW->>+ResponseSvc: POST /responses/sessions
    ResponseSvc->>+Redis: GET idempotency_token (check for duplicate)
    Redis-->>-ResponseSvc: nil (no duplicate)
    ResponseSvc->>+DB: SELECT response_count vs response_limit
    DB-->>-ResponseSvc: Count within limit
    ResponseSvc->>+Mongo: INSERT session {id, survey_id, started_at, status: in_progress}
    Mongo-->>-ResponseSvc: session_id
    ResponseSvc-->>-APIGW: 201 Created {session_id, token}
    APIGW-->>-Browser: 201 {session_id}
    Browser-->>Respondent: Render first survey page

    Respondent->>Browser: Answer all questions and click Submit
    Browser->>+APIGW: POST /api/responses/{session_id}/submit {answers[], idempotency_token}
    APIGW->>+ResponseSvc: POST /responses/{session_id}/submit

    ResponseSvc->>+Redis: SET idempotency_token (NX, TTL 24h)
    Redis-->>-ResponseSvc: OK (token set, not duplicate)

    opt Conditional logic evaluation
        ResponseSvc->>+SurveySvc: GET /surveys/{id}/rules
        SurveySvc-->>-ResponseSvc: ConditionalRules[]
        ResponseSvc->>ResponseSvc: Evaluate rules against answers
    end

    ResponseSvc->>+Mongo: UPDATE session answers[], status: completed, completed_at: NOW()
    Mongo-->>-ResponseSvc: OK
    ResponseSvc->>+DB: UPDATE response_sessions SET status=completed, completed_at=NOW()
    DB-->>-ResponseSvc: OK

    ResponseSvc->>+Kinesis: PutRecord {survey_id, session_id, completed_at, respondent_type}
    Kinesis-->>-ResponseSvc: SequenceNumber

    ResponseSvc-->>-APIGW: 200 OK {session_id, thank_you_message}
    APIGW-->>-Browser: 200 OK
    Browser-->>Respondent: Display thank-you page

    Note over Kinesis,DynDB: Async analytics pipeline (< 5s latency)
    Kinesis->>+Lambda: Trigger with batch of response records
    Lambda->>Lambda: Aggregate: response_count++, update completion_rate
    Lambda->>+DynDB: UpdateItem survey:{survey_id} metrics (conditional write)
    DynDB-->>-Lambda: OK
    Lambda-->>-Kinesis: Batch processed
```

---

## SSD-003: Email Distribution Campaign

This sequence covers a workspace member creating an email campaign, launching it, and the platform distributing survey invitations to all contacts in the audience list.

```mermaid
sequenceDiagram
    actor Creator as Survey Creator
    participant Browser
    participant APIGW as API Gateway
    participant DistSvc as Distribution Service
    participant DB as PostgreSQL
    participant Redis
    participant CeleryWorker as Celery Worker
    participant SendGrid
    actor Respondent as Respondent Email Inbox

    Creator->>Browser: Create new campaign (survey, audience list, subject, schedule)
    Browser->>+APIGW: POST /api/distribution/campaigns {survey_id, audience_list_id, subject, scheduled_at}
    APIGW->>+DistSvc: POST /campaigns
    DistSvc->>+DB: SELECT plan entitlements for workspace (check channel limit)
    DB-->>-DistSvc: Plan: max 10K emails/hr throttle
    DistSvc->>+DB: INSERT INTO campaigns (id, survey_id, audience_list_id, status=draft)
    DB-->>-DistSvc: campaign_id
    DistSvc-->>-APIGW: 201 Created {campaign_id, status: draft}
    APIGW-->>-Browser: 201 Created

    Creator->>Browser: Click "Launch Campaign"
    Browser->>+APIGW: POST /api/distribution/campaigns/{campaign_id}/launch
    APIGW->>+DistSvc: POST /campaigns/{id}/launch

    DistSvc->>+DB: SELECT survey WHERE id=survey_id AND status=published
    DB-->>-DistSvc: Survey confirmed published

    alt Survey not published
        DistSvc-->>APIGW: 409 Conflict {error: survey_not_published}
        APIGW-->>Browser: 409 Conflict
    else Survey published
        DistSvc->>+DB: UPDATE campaigns SET status=sending, launched_at=NOW()
        DB-->>-DistSvc: OK
        DistSvc->>+DB: SELECT contacts FROM audience_list WHERE not unsubscribed
        DB-->>-DistSvc: contact_list[] (e.g., 5000 contacts)
        DistSvc->>+Redis: Enqueue task send_campaign_batch(campaign_id, contacts[], throttle=1000/hr)
        Redis-->>-DistSvc: task_id
        DistSvc-->>-APIGW: 200 OK {campaign_id, status: sending, recipient_count: 5000}
        APIGW-->>-Browser: 200 OK

        loop For each contact batch (throttled 1000/hr)
            CeleryWorker->>+DB: Fetch next 1000 contacts for campaign
            DB-->>-CeleryWorker: contact batch[]
            loop For each contact in batch
                CeleryWorker->>CeleryWorker: Generate personalised survey URL with tracking token
                CeleryWorker->>CeleryWorker: Render Jinja2 email template with contact fields
                CeleryWorker->>+SendGrid: POST /mail/send {to, subject, html_body, tracking_id}
                SendGrid-->>-CeleryWorker: 202 Accepted {message_id}
                CeleryWorker->>+DB: INSERT campaign_delivery_log (contact_id, message_id, sent_at)
                DB-->>-CeleryWorker: OK
            end
        end

        SendGrid->>+APIGW: POST /api/distribution/webhooks/sendgrid {event: delivered, message_id}
        APIGW->>+DistSvc: POST /webhooks/sendgrid
        DistSvc->>+DB: UPDATE delivery_log SET delivered_at=NOW() WHERE message_id=message_id
        DB-->>-DistSvc: OK
        DistSvc-->>-APIGW: 200 OK
        APIGW-->>-SendGrid: 200 OK

        SendGrid->>Respondent: Email delivered to inbox
        Respondent->>Respondent: Opens email, clicks survey link
    end
```

---

## SSD-004: OAuth 2.0 Login Flow (Google SSO)

This sequence documents the complete OAuth 2.0 authorisation code flow for a user authenticating via Google SSO.

```mermaid
sequenceDiagram
    actor User
    participant Browser
    participant APIGW as API Gateway
    participant AuthSvc as Auth Service
    participant DB as PostgreSQL
    participant Redis
    participant Google as Google OAuth 2.0

    User->>Browser: Click "Sign in with Google"
    Browser->>+APIGW: GET /api/auth/oauth/google/authorize
    APIGW->>+AuthSvc: GET /auth/oauth/google/authorize
    AuthSvc->>AuthSvc: Generate state=CSRF token, nonce, code_verifier (PKCE)
    AuthSvc->>+Redis: SET oauth_state:{state} = {nonce, code_verifier} TTL 10min
    Redis-->>-AuthSvc: OK
    AuthSvc-->>-APIGW: 302 Redirect to Google with client_id, redirect_uri, scope, state, code_challenge
    APIGW-->>-Browser: 302 Redirect
    Browser->>+Google: GET /o/oauth2/v2/auth?client_id=...&state=...&scope=openid email profile
    Google-->>-Browser: Show Google consent screen

    User->>Browser: Approve permissions
    Browser->>+Google: POST consent approval
    Google-->>-Browser: 302 Redirect to redirect_uri?code=AUTH_CODE&state=STATE

    Browser->>+APIGW: GET /api/auth/oauth/google/callback?code=AUTH_CODE&state=STATE
    APIGW->>+AuthSvc: GET /auth/oauth/google/callback

    AuthSvc->>+Redis: GET oauth_state:{state}
    Redis-->>-AuthSvc: {nonce, code_verifier} (state validated)

    alt State mismatch or expired
        AuthSvc-->>APIGW: 400 Bad Request {error: invalid_state}
        APIGW-->>Browser: 400 Bad Request
        Browser-->>User: Show error page
    else State valid
        AuthSvc->>+Google: POST /token {code, client_id, client_secret, redirect_uri, code_verifier}
        Google-->>-AuthSvc: {access_token, id_token, refresh_token, expires_in}
        AuthSvc->>AuthSvc: Verify id_token signature, extract sub, email, name, picture

        AuthSvc->>+DB: SELECT user WHERE auth_provider=google AND auth_provider_id=sub
        DB-->>-AuthSvc: User record (or nil for new user)

        alt New user (first SSO login)
            AuthSvc->>+DB: INSERT INTO users (id, email, full_name, auth_provider, auth_provider_id)
            DB-->>-AuthSvc: user_id
        else Existing user
            AuthSvc->>+DB: UPDATE users SET last_login_at=NOW(), full_name=name
            DB-->>-AuthSvc: OK
        end

        AuthSvc->>AuthSvc: Generate JWT access_token (RS256, exp: 15min) and refresh_token (exp: 7d)
        AuthSvc->>+Redis: SET session:{user_id} = refresh_token_hash TTL 7d
        Redis-->>-AuthSvc: OK
        AuthSvc->>+Redis: DEL oauth_state:{state}
        Redis-->>-AuthSvc: OK
        AuthSvc-->>-APIGW: 200 OK {access_token, refresh_token, user: {id, email, name, workspace_id}}
        APIGW-->>-Browser: Set-Cookie: refresh_token (httpOnly, secure, SameSite=Strict); Body: {access_token, user}
        Browser-->>User: Redirect to dashboard, user authenticated
    end
```

---

## SSD-005: Generate and Download Report

This sequence covers an analyst requesting a PDF report, the platform generating it asynchronously, and the analyst downloading it via a signed CloudFront URL.

```mermaid
sequenceDiagram
    actor Analyst
    participant Browser
    participant APIGW as API Gateway
    participant ReportSvc as Report Service
    participant DB as PostgreSQL
    participant Mongo as MongoDB
    participant Redis
    participant CeleryWorker as Celery Worker
    participant S3 as AWS S3
    participant CF as CloudFront

    Analyst->>Browser: Select survey, configure report filters (date range, format=PDF)
    Browser->>+APIGW: POST /api/reports {survey_id, format: pdf, filters: {date_from, date_to}}
    APIGW->>APIGW: Validate JWT, verify analyst role claim
    APIGW->>+ReportSvc: POST /reports

    ReportSvc->>+DB: SELECT survey WHERE id=survey_id AND workspace_id=workspace_id
    DB-->>-ReportSvc: Survey confirmed, ownership verified

    ReportSvc->>+DB: INSERT INTO reports (id, survey_id, status=queued, format, filters, requested_by)
    DB-->>-ReportSvc: report_id

    ReportSvc->>+Redis: Enqueue Celery task generate_report(report_id)
    Redis-->>-ReportSvc: task_id

    ReportSvc-->>-APIGW: 202 Accepted {report_id, status: queued, poll_url: /api/reports/{report_id}}
    APIGW-->>-Browser: 202 Accepted {report_id}
    Browser-->>Analyst: Show "Report is generating..." status card

    Note over CeleryWorker,S3: Async report generation pipeline
    CeleryWorker->>+DB: SELECT report config WHERE id=report_id
    DB-->>-CeleryWorker: {survey_id, format, filters}

    CeleryWorker->>+DB: SELECT survey, questions, campaigns WHERE survey_id=...
    DB-->>-CeleryWorker: Survey metadata

    CeleryWorker->>+Mongo: Aggregate answer documents WHERE survey_id=... AND completed_at BETWEEN filters
    Mongo-->>-CeleryWorker: Aggregated response dataset

    CeleryWorker->>CeleryWorker: Compute NPS, CSAT, completion rate, per-question distributions
    CeleryWorker->>CeleryWorker: Render WeasyPrint HTML template with charts (SVG via matplotlib)
    CeleryWorker->>CeleryWorker: Generate PDF binary

    CeleryWorker->>+S3: PutObject reports/{workspace_id}/{report_id}.pdf (SSE-KMS encrypted)
    S3-->>-CeleryWorker: ETag, VersionId

    CeleryWorker->>+DB: UPDATE reports SET status=completed, s3_key=..., completed_at=NOW()
    DB-->>-CeleryWorker: OK

    CeleryWorker->>+Redis: PUBLISH report:{report_id}:events {status: completed}
    Redis-->>-CeleryWorker: OK

    loop Analyst polls for status (every 3s)
        Browser->>+APIGW: GET /api/reports/{report_id}
        APIGW->>+ReportSvc: GET /reports/{report_id}
        ReportSvc->>+DB: SELECT report WHERE id=report_id
        DB-->>-ReportSvc: Report with status
        ReportSvc-->>-APIGW: 200 OK {report_id, status: completed/queued/generating}
        APIGW-->>-Browser: Status response
    end

    Browser-->>Analyst: Show "Download Report" button (status=completed)
    Analyst->>Browser: Click "Download Report"
    Browser->>+APIGW: GET /api/reports/{report_id}/download
    APIGW->>+ReportSvc: GET /reports/{report_id}/download

    ReportSvc->>+DB: SELECT report WHERE id=report_id AND status=completed
    DB-->>-ReportSvc: s3_key confirmed

    opt Report expired (download_url TTL elapsed)
        ReportSvc->>ReportSvc: Log expiry event, return 410 Gone
        ReportSvc-->>APIGW: 410 Gone {error: report_expired}
        APIGW-->>Browser: 410 Gone
        Browser-->>Analyst: Show "Report expired, regenerate" message
    end

    ReportSvc->>+CF: Generate signed CloudFront URL for s3_key (TTL 5 minutes)
    CF-->>-ReportSvc: Signed URL with Policy and Signature
    ReportSvc->>+DB: UPDATE reports SET download_url=..., expires_at=NOW()+5min
    DB-->>-ReportSvc: OK
    ReportSvc-->>-APIGW: 200 OK {download_url, expires_at}
    APIGW-->>-Browser: 200 OK {download_url}
    Browser->>+CF: GET {signed_download_url}
    CF-->>-Browser: PDF binary stream (Content-Disposition: attachment)
    Browser-->>Analyst: PDF download begins
```

---

## Interaction Patterns

The five SSDs illustrate four recurring integration patterns used throughout the platform:

### Pattern 1: Synchronous Request-Response (SSD-001, SSD-002)
Short-lived operations (survey CRUD, response submission) complete within a single HTTP request-response cycle. FastAPI services process the request, persist state, and return within SLA (p99 < 200ms). Pydantic v2 validation rejects malformed payloads before any database writes occur.

### Pattern 2: Asynchronous Task Queue (SSD-003, SSD-005)
Long-running operations (email dispatch for thousands of contacts, PDF generation) are submitted as Celery tasks and return `202 Accepted` immediately. Callers poll a status endpoint or subscribe to a SSE channel to receive completion notifications. Tasks include correlation IDs (report_id, campaign_id) for deduplication and status tracking.

### Pattern 3: OAuth 2.0 Authorization Code + PKCE (SSD-004)
The standard OAuth 2.0 authorization code flow is implemented with PKCE (Proof Key for Code Exchange) to prevent authorization code interception attacks. State tokens and PKCE verifiers are stored in Redis with a 10-minute TTL and deleted after use to prevent replay. JWTs use RS256 asymmetric signing — the Auth Service holds the private key; other services validate using the JWKS public endpoint.

### Pattern 4: Event-Driven Analytics Pipeline (SSD-002)
Response submission writes to MongoDB synchronously, then publishes a lightweight event to Kinesis asynchronously. The Lambda consumer aggregates events in real time and writes pre-computed metrics to DynamoDB, enabling sub-50ms analytics query times regardless of response volume. This separates the write-path latency (response submission) from the read-path latency (analytics dashboard queries).

---

## Operational Policy Addendum

### OPA-SSD-001: API Response Time SLOs
The platform maintains the following p99 latency targets measured at the ALB: Survey CRUD operations ≤ 150ms; Response submission ≤ 200ms; Analytics dashboard query ≤ 300ms (DynamoDB path) or ≤ 500ms (aggregation path on cache miss); Report status poll ≤ 100ms; OAuth callback ≤ 500ms (including Google token exchange). SLO breaches trigger CloudWatch alarms with PagerDuty notification within 60 seconds. SLO compliance is reported weekly in the engineering operations review.

### OPA-SSD-002: Idempotency and Duplicate Submission Prevention
All state-mutating API operations that may be retried by clients (response submission, campaign launch) require an `Idempotency-Key` header (UUID v4). The server stores the idempotency key in Redis with the outcome (HTTP status + response body hash) for 24 hours. Identical requests within the 24-hour window return the cached response without re-executing the operation. Clients are responsible for generating a new idempotency key for intentional retries after a corrected submission.

### OPA-SSD-003: JWT Token Lifecycle Management
Access tokens have a 15-minute expiry. Refresh tokens have a 7-day expiry and are stored as HMAC-SHA256 hashes in Redis (not as plaintext). Token refresh occurs silently in the SPA using an axios interceptor that detects 401 responses and calls `POST /api/auth/token/refresh` before retrying the original request. On logout, the refresh token is deleted from Redis (server-side revocation), rendering it immediately invalid regardless of its remaining TTL. Forced logout (e.g., due to suspicious activity) invalidates all active refresh tokens for a user by deleting all Redis keys matching `session:{user_id}:*`.

### OPA-SSD-004: External Service Circuit Breakers
All calls to external services (Google OAuth, SendGrid, Twilio, Stripe, HubSpot) are wrapped with `tenacity` retry policies and circuit breakers. Initial retry delays are 1s, 3s, 9s with jitter. After 5 consecutive failures within a 60-second window, the circuit opens and subsequent calls fail fast with a cached error response for 30 seconds before attempting a probe. Circuit state transitions (open → half-open → closed) are logged with structured events and trigger CloudWatch metrics for operational visibility. Response submission (SSD-002) bypasses circuit breaker checks for non-essential calls (e.g., HubSpot sync) to maintain sub-200ms p99 latency on the critical path.
