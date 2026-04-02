# Class Diagram — Survey and Feedback Platform

## Overview

This document models the platform's object-oriented design across six layers:

| Layer        | Description                                                            |
|--------------|------------------------------------------------------------------------|
| Domain       | Core business entities — Survey, Question, Response                    |
| Service      | Application services orchestrating domain operations                   |
| Repository   | Data-access layer abstracting PostgreSQL, MongoDB, and Redis           |
| Schema       | FastAPI Pydantic v2 request/response contracts                         |
| Enum         | Typed enumerations for all constrained attributes                      |
| Value Object | Immutable configuration and settings objects                           |

All Python methods are `async` by default (FastAPI + async SQLAlchemy). Repositories follow
the Unit of Work pattern. No cross-aggregate object references — only UUID identifiers cross
aggregate boundaries.

---

## Core Domain Classes

```mermaid
classDiagram
    class Survey {
        +UUID id
        +UUID workspace_id
        +str title
        +str description
        +SurveyStatus status
        +UUID created_by
        +SurveySettings settings
        +datetime created_at
        +datetime published_at
        +datetime expires_at
        +publish() None
        +archive() None
        +pause() None
        +duplicate() Survey
        +get_completion_rate() float
        +is_active() bool
        +get_question_count() int
    }

    class SurveyStatus {
        <<enumeration>>
        DRAFT
        PUBLISHED
        PAUSED
        ARCHIVED
        EXPIRED
    }

    class SurveySettings {
        <<value object>>
        +bool show_progress_bar
        +bool allow_anonymous
        +bool allow_multiple_submissions
        +bool shuffle_questions
        +str redirect_url
        +str welcome_message
        +str thank_you_message
        +int response_limit
    }

    class Question {
        +UUID id
        +UUID survey_id
        +QuestionType question_type
        +str title
        +str description
        +int position
        +bool is_required
        +QuestionSettings settings
        +validate_answer(value str) bool
        +reorder(new_position int) None
        +clone() Question
    }

    class QuestionType {
        <<enumeration>>
        SHORT_TEXT
        LONG_TEXT
        SINGLE_CHOICE
        MULTIPLE_CHOICE
        RATING
        NPS
        CSAT
        DATE
        FILE_UPLOAD
        MATRIX
        RANKING
    }

    class QuestionOption {
        +UUID id
        +UUID question_id
        +str label
        +str value
        +int position
        +bool is_other
    }

    class ConditionalRule {
        +UUID id
        +UUID survey_id
        +UUID trigger_question_id
        +str trigger_value
        +ActionType action_type
        +UUID target_question_id
        +evaluate(answer Answer) bool
    }

    class ActionType {
        <<enumeration>>
        SHOW
        HIDE
        SKIP
        END_SURVEY
    }

    Survey "1" *-- "0..*" Question : contains
    Survey "1" *-- "0..*" ConditionalRule : defines
    Survey "1" -- "1" SurveySettings : configured by
    Survey "1" -- "1" SurveyStatus : has status
    Question "1" *-- "0..*" QuestionOption : has options
    Question "1" -- "1" QuestionType : typed as
    ConditionalRule "1" -- "1" ActionType : performs
```

---

## Response Domain Classes

```mermaid
classDiagram
    class ResponseSession {
        +UUID id
        +UUID survey_id
        +UUID respondent_id
        +str ip_address
        +datetime started_at
        +datetime completed_at
        +SessionStatus status
        +str channel
        +complete() None
        +mark_partial() None
        +disqualify(reason str) None
        +get_time_spent_seconds() int
        +get_completion_percentage() float
    }

    class SessionStatus {
        <<enumeration>>
        IN_PROGRESS
        COMPLETED
        PARTIAL
        DISQUALIFIED
    }

    class Answer {
        +UUID id
        +UUID session_id
        +UUID question_id
        +str value_text
        +float value_numeric
        +dict value_jsonb
        +datetime answered_at
        +get_display_value() str
        +is_empty() bool
    }

    class Respondent {
        +UUID id
        +UUID workspace_id
        +str email
        +str first_name
        +str last_name
        +dict metadata
        +bool gdpr_consent
        +datetime unsubscribed_at
        +is_subscribed() bool
        +anonymize() None
        +export_data() dict
    }

    ResponseSession "1" *-- "1..*" Answer : captures
    ResponseSession "0..*" -- "0..1" Respondent : associated with
    ResponseSession "1" -- "1" SessionStatus : has
```

---

## Distribution Domain Classes

```mermaid
classDiagram
    class Campaign {
        +UUID id
        +UUID survey_id
        +DistributionChannel channel
        +CampaignStatus status
        +UUID audience_list_id
        +datetime scheduled_at
        +datetime sent_at
        +CampaignSettings settings
        +schedule(send_at datetime) None
        +send_now() None
        +pause() None
        +cancel() None
        +get_delivery_stats() DeliveryStats
    }

    class CampaignStatus {
        <<enumeration>>
        DRAFT
        SCHEDULED
        SENDING
        SENT
        PAUSED
        CANCELLED
        FAILED
    }

    class DistributionChannel {
        <<enumeration>>
        EMAIL
        SMS
        WHATSAPP
        WEB_EMBED
        QR_CODE
        API
    }

    class AudienceList {
        +UUID id
        +UUID workspace_id
        +str name
        +datetime created_at
        +add_contact(contact Contact) None
        +remove_contact(contact_id UUID) None
        +import_csv(file_path str) int
        +get_active_contacts() list
        +get_size() int
    }

    class Contact {
        +UUID id
        +UUID workspace_id
        +str email
        +str first_name
        +str last_name
        +dict metadata
        +GDPRConsent gdpr_consent
        +datetime unsubscribed_at
        +is_reachable() bool
        +unsubscribe() None
        +update_metadata(key str, value str) None
    }

    class GDPRConsent {
        <<enumeration>>
        GIVEN
        WITHDRAWN
        NOT_ASKED
    }

    Campaign "1" -- "1" CampaignStatus : has
    Campaign "1" -- "1" DistributionChannel : sent via
    Campaign "0..*" -- "0..1" AudienceList : targets
    AudienceList "1" o-- "0..*" Contact : contains
    Contact "1" -- "1" GDPRConsent : has
```

---

## Analytics Domain Classes

```mermaid
classDiagram
    class AnalyticsService {
        -SurveyRepository survey_repo
        -ResponseRepository response_repo
        -DynamoDBClient dynamo_client
        +calculate_nps(survey_id UUID, date_range DateRange) NPSResult
        +calculate_csat(survey_id UUID) CSATResult
        +calculate_response_rate(campaign_id UUID) float
        +run_cross_tab(q1_id UUID, q2_id UUID) CrossTabResult
        +generate_word_cloud(question_id UUID) list
        +get_completion_funnel(survey_id UUID) FunnelData
        +get_live_metrics(survey_id UUID) LiveMetrics
        +build_trend_chart(survey_id UUID, metric str) TrendData
    }

    class MetricSnapshot {
        +UUID survey_id
        +datetime captured_at
        +int total_responses
        +int complete_responses
        +float completion_rate
        +float avg_time_spent_sec
        +float nps_score
        +float csat_score
        +dict question_summaries
        +to_dict() dict
    }

    class Dashboard {
        +UUID id
        +UUID workspace_id
        +str title
        +list widgets
        +datetime last_refreshed_at
        +add_widget(widget DashboardWidget) None
        +remove_widget(widget_id UUID) None
        +refresh() None
        +export_pdf() bytes
    }

    class ReportDefinition {
        +UUID id
        +UUID survey_id
        +str title
        +str report_type
        +str format
        +str s3_key
        +str status
        +UUID created_by
        +datetime created_at
        +get_download_url(expires_in int) str
        +regenerate() None
    }

    AnalyticsService ..> MetricSnapshot : produces
    Dashboard "1" o-- "1..*" ReportDefinition : contains
```

---

## Service Layer Classes

```mermaid
classDiagram
    class SurveyService {
        -SurveyRepository repo
        -RedisCache cache
        -EventBus event_bus
        +create_survey(workspace_id UUID, dto SurveyCreateDTO) Survey
        +update_survey(survey_id UUID, dto SurveyUpdateDTO) Survey
        +publish_survey(survey_id UUID) Survey
        +archive_survey(survey_id UUID) None
        +duplicate_survey(survey_id UUID) Survey
        +add_question(survey_id UUID, dto QuestionCreateDTO) Question
        +reorder_questions(survey_id UUID, positions list) None
        +set_conditional_rules(survey_id UUID, rules list) None
        +get_survey_with_questions(survey_id UUID) Survey
    }

    class ResponseService {
        -ResponseRepository repo
        -DeduplicationService dedup
        -KinesisProducer kinesis
        -WebhookService webhooks
        +start_session(survey_id UUID, channel str) ResponseSession
        +submit_answer(session_id UUID, dto AnswerDTO) Answer
        +complete_session(session_id UUID) ResponseSession
        +get_session(session_id UUID) ResponseSession
        +export_responses(survey_id UUID, fmt str) bytes
    }

    class DistributionService {
        -CampaignRepository repo
        -EmailProvider email_provider
        -SMSProvider sms_provider
        -AudienceRepository audience_repo
        +create_campaign(survey_id UUID, dto CampaignCreateDTO) Campaign
        +schedule_campaign(campaign_id UUID, send_at datetime) Campaign
        +send_campaign_now(campaign_id UUID) None
        +get_delivery_stats(campaign_id UUID) DeliveryStats
        +import_contacts(list_id UUID, file_path str) int
    }

    class AuthService {
        -UserRepository user_repo
        -RedisTokenStore token_store
        +login(email str, password str) TokenPair
        +oauth_login(provider str, code str) TokenPair
        +magic_link_login(email str) None
        +refresh_tokens(refresh_token str) TokenPair
        +logout(refresh_token str, access_jti str) None
        +verify_access_token(token str) TokenClaims
        +get_current_user(claims TokenClaims) User
    }

    class WebhookService {
        -WebhookRepository repo
        -CeleryApp celery
        +register_endpoint(workspace_id UUID, dto WebhookDTO) WebhookEndpoint
        +emit_event(event_type str, payload dict) None
        +deliver(endpoint_id UUID, payload dict) bool
        +get_delivery_logs(endpoint_id UUID) list
        +rotate_secret(endpoint_id UUID) str
    }
```

---

## FastAPI Pydantic Schema Classes

```mermaid
classDiagram
    class SurveyCreateRequest {
        +str title
        +str description
        +SurveySettingsSchema settings
        +list questions
        +model_config ConfigDict
        +model_validator() SurveyCreateRequest
    }

    class SurveyResponse {
        +UUID id
        +UUID workspace_id
        +str title
        +str status
        +int question_count
        +datetime created_at
        +datetime published_at
        +model_config ConfigDict
    }

    class QuestionCreateRequest {
        +str question_type
        +str title
        +bool is_required
        +int position
        +list options
        +QuestionSettingsSchema settings
        +field_validator() str
    }

    class ResponseSubmitRequest {
        +UUID session_id
        +UUID question_id
        +str value_text
        +float value_numeric
        +dict value_jsonb
        +model_validator() ResponseSubmitRequest
    }

    class TokenPairResponse {
        +str access_token
        +str refresh_token
        +str token_type
        +int expires_in
    }

    class ErrorResponse {
        +str error_code
        +str message
        +list details
        +str request_id
        +str doc_url
    }

    SurveyCreateRequest "1" *-- "0..*" QuestionCreateRequest : includes
```

---

## Repository Pattern Classes

```mermaid
classDiagram
    class BaseRepository {
        #AsyncSession session
        +get_by_id(id UUID) object
        +list_all(filters dict) list
        +save(entity object) object
        +delete(id UUID) None
        +begin_transaction() AsyncContextManager
    }

    class SurveyRepository {
        +get_with_questions(survey_id UUID) Survey
        +list_by_workspace(workspace_id UUID, status str) list
        +get_published(survey_id UUID) Survey
        +update_status(survey_id UUID, status str) None
        +count_by_workspace(workspace_id UUID) int
    }

    class ResponseRepository {
        +get_session_with_answers(session_id UUID) ResponseSession
        +count_completed(survey_id UUID) int
        +list_sessions(survey_id UUID, page int) list
        +get_answer_distribution(question_id UUID) dict
        +save_session_with_answers(session ResponseSession) ResponseSession
    }

    class UserRepository {
        +find_by_email(email str) User
        +get_workspace_members(workspace_id UUID) list
        +add_member(workspace_id UUID, user_id UUID, role str) None
        +update_role(workspace_id UUID, user_id UUID, role str) None
    }

    class CampaignRepository {
        +list_by_survey(survey_id UUID) list
        +get_scheduled(before datetime) list
        +update_status(campaign_id UUID, status str) None
        +save_delivery_stats(campaign_id UUID, stats dict) None
    }

    BaseRepository <|-- SurveyRepository : extends
    BaseRepository <|-- ResponseRepository : extends
    BaseRepository <|-- UserRepository : extends
    BaseRepository <|-- CampaignRepository : extends
```

---

## Operational Policy Addendum

### 1. Domain Model Governance

All domain entity classes are immutable after construction; state changes go through named
command methods (e.g., `survey.publish()`, `session.complete()`). The `Survey` entity acts
as the aggregate root for the survey bounded context. No cross-aggregate object references —
only `UUID` identifiers cross boundaries, enforced by a lint rule (`no-cross-aggregate-import`).
Anemic domain model anti-pattern is explicitly prohibited; business logic belongs in entity
methods, not in service classes.

### 2. Service Boundary Rules

Each service class owns exactly one bounded context. Within the same process, inter-service
communication uses the internal `EventBus` backed by `asyncio.Queue`. Cross-process
communication uses Celery tasks (for job dispatch) or Kinesis events (for streaming analytics).
Services must never import each other's classes directly — circular imports are a build-time
error enforced via `import-linter` with a `contracts.ini` configuration.

### 3. Schema Versioning Policy

All Pydantic request schemas carry a `schema_version: int = 1` field. Breaking field changes
increment the major API version prefix (`/api/v2/`). Additive field additions are
backward-compatible and require no version bump. Deprecated fields are annotated with a
`@model_validator(mode='before')` that emits a structured deprecation warning at INFO level
and are removed no sooner than two minor releases after deprecation notice.

### 4. Testing Requirements

- **Domain classes:** 100 % unit test coverage; zero database I/O; all methods exercised via
  pytest with in-memory objects.
- **Service classes:** Integration tests against a live PostgreSQL instance provided by the
  `pytest-postgresql` fixture, running in an isolated schema per test function.
- **Repository classes:** Contract tests with a seeded test database; each test rolls back
  via a transaction savepoint to preserve isolation.
- **Pydantic schemas:** Property-based tests using Hypothesis covering edge-case inputs
  (empty strings, Unicode surrogates, max-length boundaries).
- **Factory fixtures:** `tests/factories/` uses `factory_boy` with `SQLAlchemyModelFactory`
  to generate fully-populated entities with sensible defaults.
