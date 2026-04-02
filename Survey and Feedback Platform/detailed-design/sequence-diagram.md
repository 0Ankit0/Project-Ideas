# Sequence Diagrams — Survey and Feedback Platform

## Overview

This document contains five sequence diagrams covering the most critical flows in the platform.

| ID      | Flow                                        | Primary Stakeholder   |
|---------|---------------------------------------------|-----------------------|
| SD-001  | Survey Builder — Save with Conditional Logic | Survey Editor         |
| SD-002  | Response Submission with Real-Time Analytics | Respondent + Analyst  |
| SD-003  | Webhook Delivery with Exponential Retry      | Platform + Integrator |
| SD-004  | JWT Auth and Refresh Token Rotation          | All Authenticated Users|
| SD-005  | Async Report Generation and Delivery         | Analyst               |

**Notation conventions:**

| Symbol     | Meaning                                    |
|------------|--------------------------------------------|
| `->>`      | Synchronous request (solid arrow)          |
| `-->>`     | Response or async return (dashed arrow)    |
| `alt/else` | Conditional branch                         |
| `loop`     | Repeated operation                         |
| `opt`      | Optional operation                         |
| `Note over`| Cross-participant annotation               |

All API endpoints are authenticated via JWT Bearer token unless otherwise stated.
Internal service-to-service calls are in-process function invocations unless annotated
with a queue or stream label.

---

## SD-001: Survey Builder — Save Survey with Conditional Logic

**Trigger:** An editor saves changes to a survey including question reordering and
conditional skip rules in the drag-and-drop builder.
**Pre-condition:** User holds `editor` or `admin` role in the workspace; survey exists
with `status = draft` or `status = paused`.
**Post-condition:** Survey is persisted, Redis cache is invalidated, and a version snapshot
is created in MongoDB.

```mermaid
sequenceDiagram
    autonumber
    participant FE   as Frontend
    participant API  as SurveyAPI
    participant SVC  as SurveyService
    participant VAL  as ConditionalLogicValidator
    participant REPO as SurveyRepository
    participant PG   as PostgreSQL
    participant RD   as Redis

    FE->>API: PUT /api/v1/surveys/{id} {title, questions[], rules[]}
    API->>SVC: update_survey(survey_id, workspace_id, dto)
    SVC->>VAL: validate_conditional_rules(questions, rules)

    alt Rule validation fails — cycle or missing target detected
        VAL-->>SVC: ValidationError {cycle_detected, offending_rule_id}
        SVC-->>API: raise SurveyValidationError(422)
        API-->>FE: 422 Unprocessable Entity {error_code, field_errors}
    else Rule validation passes
        VAL-->>SVC: rules_valid = True
        SVC->>REPO: begin_unit_of_work()
        REPO->>PG: BEGIN TRANSACTION
        REPO->>PG: UPDATE surveys SET title, settings WHERE id = ?
        REPO->>PG: DELETE questions WHERE survey_id AND id NOT IN new_ids
        REPO->>PG: UPSERT questions ON CONFLICT (id) DO UPDATE position, title
        REPO->>PG: DELETE conditional_rules WHERE survey_id = ?
        REPO->>PG: INSERT conditional_rules (trigger_question_id, action_type, target_question_id)
        REPO->>PG: COMMIT
        PG-->>REPO: transaction committed OK
        REPO-->>SVC: SurveyEntity {id, questions, rules}
        SVC->>RD: DEL survey:{id}:meta survey:{id}:questions
        RD-->>SVC: 2 keys deleted
        SVC->>SVC: create_version_snapshot(survey_entity) — async MongoDB write
        SVC-->>API: SurveyDTO
        API-->>FE: 200 OK {survey: SurveyDTO, version: 4}
    end
```

---

## SD-002: Response Submission with Real-Time Analytics

**Trigger:** A respondent submits the final answer on the last page of the survey.
**Pre-condition:** A `response_session` row exists with `status = in_progress`.
**Post-condition:** Session is marked complete, answers persisted, event streamed to Kinesis,
and the analyst dashboard is updated via WebSocket within 2 seconds.

```mermaid
sequenceDiagram
    autonumber
    participant RB   as RespondentBrowser
    participant CDN  as CloudFront
    participant API  as ResponseAPI
    participant SVC  as ResponseService
    participant DEDUP as DeduplicationService
    participant REPO as ResponseRepository
    participant PG   as PostgreSQL
    participant KP   as KinesisProducer
    participant KS   as Kinesis
    participant LAM  as AnalyticsLambda
    participant DDB  as DynamoDB
    participant WS   as WebSocketServer
    participant AB   as AnalystBrowser

    RB->>CDN: POST /r/{survey_id}/submit {session_id, answers[]}
    CDN->>API: forward (x-forwarded-for, cf-ray headers)
    API->>SVC: submit_response(session_id, answers_dto)
    SVC->>DEDUP: check_duplicate(survey_id, respondent_fingerprint)

    alt Duplicate submission detected
        DEDUP-->>SVC: DUPLICATE {first_submitted_at}
        SVC-->>API: raise DuplicateResponseError(409)
        API-->>CDN: 409 Conflict {error_code: ALREADY_SUBMITTED}
        CDN-->>RB: 409 Your response was already recorded
    else Unique response
        DEDUP-->>SVC: UNIQUE — set dedup sentinel in Redis
        SVC->>REPO: save_session_and_answers(session, answers)
        REPO->>PG: UPDATE response_sessions SET status=completed, completed_at=NOW()
        REPO->>PG: INSERT INTO answers (session_id, question_id, value_text, value_numeric, value_jsonb)
        PG-->>REPO: commit OK
        REPO-->>SVC: ResponseSessionEntity
        SVC->>KP: publish(ResponseSubmittedEvent {survey_id, session_id, workspace_id})
        KP->>KS: PutRecord(PartitionKey=survey_id, Data=event_json)
        KS-->>KP: SequenceNumber acknowledged
        KP-->>SVC: event_published = True
        SVC-->>API: ResponseDTO {session_id, completed_at}
        API-->>CDN: 201 Created
        CDN-->>RB: 201 OK {session_id, thank_you_url}
    end

    Note over KS,LAM: Asynchronous pipeline — target latency under 2 s
    KS->>LAM: trigger(records_batch, shard_id)
    LAM->>DDB: UpdateItem PK=survey#{id} SK=metrics ADD total_responses 1
    DDB-->>LAM: UpdateItemResponse
    LAM->>WS: push_event(survey_id, live_metrics_payload)
    WS->>AB: WS frame: metrics_updated {total, completion_rate, nps_score}
```

---

## SD-003: Webhook Delivery with Exponential Retry

**Trigger:** `ResponseService` emits a `response.completed` domain event after a session
is successfully persisted.
**Pre-condition:** At least one `webhook_endpoints` row with `is_active = true` subscribed
to the `response.completed` event type for the workspace.
**Post-condition:** HTTP delivery succeeds and is logged, or the event enters the dead-letter
queue after three failed attempts.

```mermaid
sequenceDiagram
    autonumber
    participant RS as ResponseService
    participant WH as WebhookService
    participant CW as CeleryWorker
    participant RD as Redis
    participant EP as ExternalEndpoint
    participant AL as AuditLog

    RS->>WH: emit_event("response.completed", {session_id, survey_id, answers_summary})
    WH->>RD: LPUSH celery:default deliver_webhook_task {endpoint_id, payload, attempt=1}
    RD-->>WH: queued
    WH-->>RS: event_queued (fire-and-forget)

    Note over CW: Celery worker picks up task from Redis broker
    CW->>WH: get_endpoint_config(endpoint_id)
    WH-->>CW: EndpointConfig {url, secret_hash, timeout_ms=5000}
    CW->>CW: compute_hmac_sha256(secret_hash, payload_json)

    loop Attempt 1 to 3 with backoff: 0 s, 60 s, 300 s
        CW->>EP: POST url {X-Signature, X-Event-Type, X-Delivery-ID, body=payload}
        alt HTTP 2xx received
            EP-->>CW: 200 OK
            CW->>AL: insert(event=delivery_success, endpoint_id, attempt, http_status=200)
            AL-->>CW: logged
        else HTTP 4xx — non-retryable client error
            EP-->>CW: 400 Bad Request
            CW->>AL: insert(event=delivery_failed_permanent, endpoint_id, reason=client_error)
            AL-->>CW: logged
        else HTTP 5xx or connection timeout
            EP-->>CW: 503 Service Unavailable
            CW->>RD: ZADD webhook:retry:{delivery_id} next_attempt_unix {task_payload}
            RD-->>CW: scheduled
            CW->>AL: insert(event=delivery_retry_scheduled, endpoint_id, attempt_n, next_at)
        end
    end

    opt All 3 attempts exhausted without success
        CW->>RD: LPUSH webhook:dead_letter {endpoint_id, payload, error_history[]}
        RD-->>CW: pushed to dead-letter queue
        CW->>AL: insert(event=dead_letter, endpoint_id, final_error, all_attempts)
    end
```

---

## SD-004: JWT Auth + Refresh Token Flow

**Trigger:** User submits login credentials; later the access token expires and the client
silently refreshes it; finally the user explicitly logs out.
**Pre-condition:** User account exists and `is_verified = true`.
**Post-condition:** On logout, both the refresh token and the access token JTI are revoked
in Redis so they cannot be reused even if intercepted.

```mermaid
sequenceDiagram
    autonumber
    participant CL  as Client
    participant API as AuthAPI
    participant SVC as AuthService
    participant UR  as UserRepository
    participant PG  as PostgreSQL
    participant RT  as RedisTokenStore

    CL->>API: POST /api/v1/auth/login {email, password}
    API->>SVC: authenticate(email, password)
    SVC->>UR: find_by_email(email)
    UR->>PG: SELECT id, email, password_hash, is_verified FROM users WHERE email = ?
    PG-->>UR: UserRecord
    UR-->>SVC: User entity

    alt Invalid credentials or account not verified
        SVC-->>API: raise AuthenticationError(401)
        API-->>CL: 401 Unauthorized {error_code: INVALID_CREDENTIALS}
    else Valid credentials
        SVC->>SVC: bcrypt.verify(password, password_hash)
        SVC->>SVC: sign_jwt(sub=user_id, roles, workspace_ids, exp=NOW+15min)
        SVC->>SVC: generate_opaque_refresh_token(nbytes=32)
        SVC->>RT: SETEX refresh:{sha256(token)} 604800 {user_id, issued_at}
        RT-->>SVC: OK
        SVC-->>API: TokenPair {access_token, refresh_token, expires_in=900}
        API-->>CL: 200 OK {access_token, refresh_token, token_type=Bearer}
    end

    Note over CL: 15 minutes later — access token expires
    CL->>API: POST /api/v1/auth/refresh {refresh_token}
    API->>SVC: rotate_refresh_token(refresh_token)
    SVC->>RT: GET refresh:{sha256(token)}
    RT-->>SVC: {user_id, issued_at} or NIL

    opt Token not found or already used (replay attack)
        SVC-->>API: raise TokenExpiredError(401)
        API-->>CL: 401 Unauthorized {error_code: REFRESH_TOKEN_EXPIRED}
    end

    SVC->>RT: DEL refresh:{old_token_sha256}
    SVC->>SVC: sign_new_jwt + generate_new_refresh_token
    SVC->>RT: SETEX refresh:{new_token_sha256} 604800 {user_id}
    RT-->>SVC: OK
    SVC-->>API: NewTokenPair
    API-->>CL: 200 OK {new_access_token, new_refresh_token}

    Note over CL: User initiates explicit logout
    CL->>API: POST /api/v1/auth/logout {refresh_token} Authorization: Bearer access_token
    API->>SVC: revoke_session(refresh_token, access_token_jti)
    SVC->>RT: DEL refresh:{token_sha256}
    SVC->>RT: SETEX blacklist:{access_jti} 960 "revoked"
    RT-->>SVC: both keys written
    SVC-->>API: session revoked
    API-->>CL: 204 No Content
```

---

## SD-005: Async Report Generation

**Trigger:** An analyst requests a PDF summary report for a survey with optional date-range
and metric filters.
**Pre-condition:** Survey has at least one completed response session.
**Post-condition:** PDF is stored in S3, the report row is updated to `status = READY`, and
the analyst receives an email containing a pre-signed S3 download URL valid for 1 hour.

```mermaid
sequenceDiagram
    autonumber
    participant AN  as Analyst
    participant API as ReportAPI
    participant SVC as ReportService
    participant PG  as PostgreSQL
    participant CW  as CeleryWorker
    participant DA  as DataAggregator
    participant PDF as PDFGenerator
    participant S3  as AWSS3
    participant SNS as SNSNotification

    AN->>API: POST /api/v1/reports {survey_id, type=summary, format=pdf, date_range}
    API->>SVC: create_report(workspace_id, analyst_id, dto)
    SVC->>PG: INSERT INTO reports (status=PENDING, survey_id, workspace_id) RETURNING id
    PG-->>SVC: report_id
    SVC->>CW: enqueue_task(generate_report, {report_id, survey_id, date_range, analyst_email})
    CW-->>SVC: task_id accepted
    SVC-->>API: ReportDTO {report_id, task_id, status=PENDING}
    API-->>AN: 202 Accepted {report_id, poll_url: /reports/{id}/status}

    Note over CW: Worker picks up task from Celery queue (async)
    CW->>PG: UPDATE reports SET status=PROCESSING WHERE id = report_id
    CW->>DA: aggregate(survey_id, date_range, metrics=[nps, csat, completion_rate, top_answers])
    DA->>PG: SELECT sessions, answers, computed aggregates with GROUP BY question_id
    PG-->>DA: ResultSet {rows, computed_nps, chart_data}
    DA-->>CW: AggregatedData object

    alt Aggregation fails — query timeout or insufficient data
        DA-->>CW: AggregationError {reason}
        CW->>PG: UPDATE reports SET status=FAILED, error_message = ?
        CW->>SNS: publish(report_failed_topic, {analyst_email, report_id, reason})
    else Aggregation succeeds
        CW->>PDF: render(template=summary_v2, data=AggregatedData, branding=WorkspaceBranding)
        PDF-->>CW: pdf_bytes (2–8 MB typical)
        CW->>S3: PutObject(Bucket=reports-bucket, Key=reports/{workspace_id}/{report_id}.pdf)
        S3-->>CW: {ETag, VersionId}
        CW->>PG: UPDATE reports SET status=READY, s3_key=reports/{workspace_id}/{report_id}.pdf
        CW->>S3: GeneratePresignedUrl(key, ExpiresIn=3600)
        S3-->>CW: presigned_url
        CW->>SNS: publish(report_ready_topic, {analyst_email, report_id, presigned_url})
        SNS-->>CW: message_id
    end

    Note over AN: Analyst receives email with 1-hour download link
```

---

## Error Handling Patterns

The following patterns apply consistently across all sequence flows described above.

### Idempotency Keys

All `POST` mutating endpoints accept an `Idempotency-Key` header. The first response is
cached in Redis at `idempotency:{key}` for 24 hours. Subsequent requests with the same key
return the cached response without re-executing the handler. This prevents duplicate
submissions on network retries.

### Circuit Breaker on External Calls

Calls to external webhook endpoints, email providers, and SMS gateways are wrapped in a
circuit breaker (Tenacity library, state stored in Redis at `circuit:{service_name}`).
Three consecutive failures open the circuit for 60 seconds. While open, the service returns
a synthetic `503` and logs a `CIRCUIT_OPEN` audit event rather than hammering the downstream.

### Structured Error Responses

All API errors follow the `ErrorResponse` schema:
```json
{
  "error_code": "SURVEY_NOT_FOUND",
  "message": "Survey abc123 does not exist or is not accessible in this workspace.",
  "details": [],
  "request_id": "req_01J4...",
  "doc_url": "https://docs.surveyplatform.io/errors/SURVEY_NOT_FOUND"
}
```
HTTP status codes map to error categories: `400` validation, `401` auth, `403` authorisation,
`404` not found, `409` conflict, `422` domain rule violation, `429` rate-limit, `5xx` platform.

### Distributed Tracing

Every inbound HTTP request generates a `trace_id` (UUID v7, monotonic) that propagates
via the `X-Trace-ID` header to all downstream services, Celery task metadata, Kinesis
event payloads, and CloudWatch log entries. This enables end-to-end correlation of a single
response submission from the CDN edge to DynamoDB analytics write.

---

## Operational Policy Addendum

### 1. SLA & Timeout Policy

| Operation                       | P50 Target | P99 Target | Hard Timeout |
|---------------------------------|-----------|-----------|--------------|
| Survey render (GET)             | 80 ms     | 300 ms    | 5 s          |
| Response submission (POST)      | 120 ms    | 500 ms    | 10 s         |
| Webhook delivery attempt        | —         | —         | 5 s          |
| Report generation (background)  | 30 s      | 5 min     | 15 min       |
| Auth login                      | 150 ms    | 600 ms    | 5 s          |
| Live analytics push             | 500 ms    | 2 s       | 5 s          |

All FastAPI endpoints declare explicit `timeout` middleware. Celery tasks have `soft_time_limit`
(triggers `SoftTimeLimitExceeded`) and `time_limit` (SIGKILL) configured per the table above.

### 2. Idempotency Requirements

- Response submission: idempotent on `session_id`; duplicate sessions return `409`.
- Campaign send: idempotent on `(campaign_id, recipient_email)`; re-sends are suppressed by
  the delivery-log deduplication check before SMTP/SMS dispatch.
- Webhook delivery: each delivery event has a `delivery_id` (UUID); the external endpoint
  receives `X-Delivery-ID` to allow client-side deduplication.
- Report generation: calling `POST /reports` twice with identical parameters within 5 minutes
  returns the existing `PENDING` or `PROCESSING` report rather than creating a duplicate.

### 3. Circuit Breaker Policy

Services protected by circuit breakers:

| Service          | Failure Threshold | Open Duration | Half-Open Probe |
|------------------|-------------------|---------------|-----------------|
| External webhooks | 3 consecutive 5xx | 60 s          | 1 request       |
| Email provider    | 5 within 2 min    | 120 s         | 1 request       |
| SMS gateway       | 5 within 2 min    | 120 s         | 1 request       |
| PDF renderer      | 2 consecutive err | 30 s          | 1 request       |

Circuit state is stored in Redis (`circuit:{service}:state`, TTL = open duration) so all
Celery workers share the same breaker state rather than each maintaining independent counters.

### 4. Observability Requirements

Every sequence flow emits the following telemetry:

- **Structured logs:** JSON to CloudWatch Logs; mandatory fields — `trace_id`, `span_id`,
  `service`, `level`, `message`, `duration_ms`, `http_status` (where applicable).
- **Metrics:** Custom CloudWatch metrics — `response_submission_count`, `webhook_delivery_latency_ms`,
  `report_generation_duration_ms`, `auth_failure_count` — with `workspace_id` and `survey_id`
  dimensions where the cardinality is bounded.
- **Distributed traces:** AWS X-Ray segments for all HTTP handlers and Celery tasks; sub-segments
  for every database query and external HTTP call.
- **Alerts:** PagerDuty alarm triggers when `webhook_dead_letter_queue_depth > 10` or
  `auth_failure_count > 50 per minute` or any `5xx` error rate exceeds 1 % over 5 minutes.
