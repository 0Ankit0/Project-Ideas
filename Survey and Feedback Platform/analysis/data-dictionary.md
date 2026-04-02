# Data Dictionary — Survey and Feedback Platform

## Overview

This data dictionary documents all persistent entities, their attributes, data types, constraints,
and relationships for the Survey and Feedback Platform. It serves as the authoritative reference for
database schema design, API contract definition, and data governance.

**Conventions:**
- UUIDs are v4 unless noted. All UUID primary keys are stored as `uuid` in PostgreSQL.
- Timestamps are stored as `TIMESTAMPTZ` (UTC) in PostgreSQL and as ISO 8601 strings in API responses.
- Soft-deletable entities carry `deleted_at TIMESTAMPTZ NULL` (NULL = active, non-NULL = deleted).
- `JSONB` columns follow documented schemas validated at the application layer via Pydantic v2.
- MongoDB documents use BSON ObjectId for `_id`; platform exposes them as 24-char hex strings.
- Monetary amounts are stored as integers in the smallest currency unit (e.g., cents for USD).

---

## Core Entities

### Workspace

Represents a tenant account. All surveys, members, and settings belong to a workspace.

| Attribute | Data Type | Constraints | Description | Example Value |
|---|---|---|---|---|
| id | UUID | PK, NOT NULL | Globally unique workspace identifier | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| name | VARCHAR(255) | NOT NULL | Human-readable display name | `"Acme Corp Research"` |
| slug | VARCHAR(80) | UNIQUE, NOT NULL | URL-safe workspace identifier used in routing | `"acme-corp"` |
| owner_user_id | UUID | FK → User.id, NOT NULL | User who owns and controls the workspace | `"f47ac10b-58cc-4372-..."` |
| plan_tier | VARCHAR(20) | NOT NULL, DEFAULT 'free' | Current subscription tier | `"business"` |
| data_residency | VARCHAR(20) | NOT NULL, DEFAULT 'us-east-1' | AWS region for data storage | `"eu-west-1"` |
| logo_s3_key | VARCHAR(512) | NULL | S3 object key for workspace logo | `"logos/acme-corp/logo.png"` |
| custom_domain | VARCHAR(253) | UNIQUE, NULL | Custom survey domain (e.g., surveys.acme.com) | `"surveys.acme.com"` |
| settings | JSONB | NOT NULL, DEFAULT '{}' | Workspace-wide settings (branding, defaults) | `{"primary_color":"#0057FF"}` |
| sso_config | JSONB | NULL | SAML/OIDC configuration for Enterprise SSO | `{"provider":"okta","metadata_url":"..."}` |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Workspace creation timestamp | `"2024-03-15T10:23:00Z"` |
| deleted_at | TIMESTAMPTZ | NULL | Soft-delete timestamp; NULL means active | `null` |

---

### User / UserProfile

A platform user with login credentials. One user may belong to multiple workspaces via WorkspaceMember.

| Attribute | Data Type | Constraints | Description | Example Value |
|---|---|---|---|---|
| id | UUID | PK, NOT NULL | Globally unique user identifier | `"d290f1ee-6c54-4b01-..."` |
| email | VARCHAR(320) | UNIQUE, NOT NULL | Primary email address (login identifier) | `"jane.doe@acme.com"` |
| email_verified | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether email address has been verified | `true` |
| full_name | VARCHAR(255) | NULL | Display name | `"Jane Doe"` |
| avatar_s3_key | VARCHAR(512) | NULL | S3 key for profile photo | `"avatars/d290f1ee.jpg"` |
| password_hash | VARCHAR(120) | NULL | bcrypt hash (cost 12); NULL if SSO-only | `"$2b$12$..."` |
| auth_provider | VARCHAR(30) | NOT NULL, DEFAULT 'email' | Primary authentication method | `"google_oauth"` |
| google_sub | VARCHAR(255) | UNIQUE, NULL | Google OAuth subject identifier | `"108204483772..."`|
| microsoft_oid | VARCHAR(255) | UNIQUE, NULL | Microsoft Entra Object ID | `"7d3e5a2f-..."` |
| mfa_enabled | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether TOTP MFA is active | `true` |
| mfa_totp_secret | VARCHAR(64) | NULL | TOTP base32 secret (encrypted at rest) | `"JBSWY3DPEHPK3PXP"` |
| magic_link_token_hash | VARCHAR(128) | NULL | Hash of the most recent magic link token | `"sha256:ab34cd..."` |
| magic_link_expires_at | TIMESTAMPTZ | NULL | Expiry of the active magic link token | `"2024-06-01T14:00:00Z"` |
| last_login_at | TIMESTAMPTZ | NULL | Most recent successful authentication | `"2024-05-30T09:12:00Z"` |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Account creation timestamp | `"2024-01-10T08:00:00Z"` |
| deleted_at | TIMESTAMPTZ | NULL | Soft-delete timestamp | `null` |

---

### Survey

The top-level definition of a survey, including metadata, configuration, and lifecycle state.

| Attribute | Data Type | Constraints | Description | Example Value |
|---|---|---|---|---|
| id | UUID | PK, NOT NULL | Unique survey identifier | `"c3d4e5f6-..."` |
| workspace_id | UUID | FK → Workspace.id, NOT NULL, INDEX | Owning workspace | `"a1b2c3d4-..."` |
| created_by | UUID | FK → User.id, NOT NULL | User who created the survey | `"d290f1ee-..."` |
| title | VARCHAR(512) | NOT NULL | Survey display title | `"Q4 Customer NPS Survey"` |
| description | TEXT | NULL | Optional internal description | `"Quarterly pulse for enterprise customers"` |
| slug | VARCHAR(80) | UNIQUE, NOT NULL | Public URL slug (`/s/{slug}`) | `"cust-nps-q4-2024"` |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'draft' | Lifecycle status (see SurveyStatus enum) | `"published"` |
| is_anonymous | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether PII is stripped from responses | `false` |
| password_hash | VARCHAR(120) | NULL | bcrypt hash for password-protected surveys | `null` |
| response_limit | INTEGER | NULL, CHECK > 0 | Max responses before auto-close; NULL = no limit | `500` |
| expires_at | TIMESTAMPTZ | NULL | Survey expiry datetime (UTC) | `"2024-12-31T23:59:59Z"` |
| welcome_page | JSONB | NULL | Welcome page content (Markdown body, image S3 key) | `{"body":"## Welcome..."}` |
| thank_you_page | JSONB | NULL | Thank-you page content and optional redirect config | `{"body":"Thanks!","redirect_url":null}` |
| settings | JSONB | NOT NULL, DEFAULT '{}' | Survey-level settings (theme, progress bar, etc.) | `{"show_progress_bar":true}` |
| logic_schema_version | VARCHAR(10) | NOT NULL, DEFAULT '1.0' | Version of branching logic schema used | `"2.1"` |
| published_at | TIMESTAMPTZ | NULL | Timestamp when status changed to 'published' | `"2024-06-01T12:00:00Z"` |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp | `"2024-05-28T10:00:00Z"` |
| updated_at | TIMESTAMPTZ | NOT NULL | Last modification timestamp | `"2024-05-30T15:30:00Z"` |
| deleted_at | TIMESTAMPTZ | NULL | Soft-delete timestamp | `null` |

---

### Question

An individual question within a survey. Ordered by `position` within the survey.

| Attribute | Data Type | Constraints | Description | Example Value |
|---|---|---|---|---|
| id | UUID | PK, NOT NULL | Unique question identifier | `"e5f6a7b8-..."` |
| survey_id | UUID | FK → Survey.id, NOT NULL, INDEX | Parent survey | `"c3d4e5f6-..."` |
| type | VARCHAR(40) | NOT NULL | Question type (see QuestionType enum) | `"nps"` |
| title | TEXT | NOT NULL | Question text shown to the respondent | `"How likely are you to recommend us?"` |
| description | TEXT | NULL | Optional helper text shown below the title | `"On a scale of 0-10."` |
| position | INTEGER | NOT NULL | Ordering index within the survey (1-based) | `3` |
| is_required | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether the respondent must answer | `true` |
| config | JSONB | NOT NULL, DEFAULT '{}' | Type-specific configuration (scale, options, etc.) | `{"min_label":"Not likely","max_label":"Very likely"}` |
| logic_rules | JSONB | NULL | Array of ConditionalLogicRule references | `[{"rule_id":"..."}]` |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp | `"2024-05-28T10:05:00Z"` |
| deleted_at | TIMESTAMPTZ | NULL | Soft-delete timestamp (question removed from survey) | `null` |

---

### QuestionOption

An individual selectable option for Multiple Choice, Single Select, Ranking, or Matrix questions.

| Attribute | Data Type | Constraints | Description | Example Value |
|---|---|---|---|---|
| id | UUID | PK, NOT NULL | Unique option identifier | `"f6a7b8c9-..."` |
| question_id | UUID | FK → Question.id, NOT NULL, INDEX | Parent question | `"e5f6a7b8-..."` |
| label | TEXT | NOT NULL | Display text shown to the respondent | `"Strongly Agree"` |
| value | VARCHAR(255) | NOT NULL | Internal value stored with the response | `"strongly_agree"` |
| position | SMALLINT | NOT NULL | Display ordering index (1-based) | `1` |
| is_other | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether this is the "Other (please specify)" option | `false` |
| score | NUMERIC(5,2) | NULL | Numeric score used in weighted calculations | `5.0` |

---

### ConditionalLogicRule

A single branching logic rule that controls question visibility or survey flow based on a condition.

| Attribute | Data Type | Constraints | Description | Example Value |
|---|---|---|---|---|
| id | UUID | PK, NOT NULL | Unique rule identifier | `"a7b8c9d0-..."` |
| survey_id | UUID | FK → Survey.id, NOT NULL, INDEX | Parent survey (for fast lookup) | `"c3d4e5f6-..."` |
| source_question_id | UUID | FK → Question.id, NOT NULL | The question whose answer triggers this rule | `"e5f6a7b8-..."` |
| operator | VARCHAR(30) | NOT NULL | Comparison operator (see LogicOperator enum) | `"equals"` |
| operand_value | JSONB | NOT NULL | Value to compare against the answer | `{"value":"strongly_agree"}` |
| action | VARCHAR(30) | NOT NULL | Action to take when condition is true | `"show_question"` |
| target_question_id | UUID | FK → Question.id, NULL | Target question for show/hide/skip actions | `"b8c9d0e1-..."` |
| target_page | INTEGER | NULL | Target page index for jump-to-page action | `null` |
| nesting_depth | SMALLINT | NOT NULL, DEFAULT 1 | Computed nesting depth (validated on save) | `2` |

---

### SurveyDistribution (Campaign)

Represents a configured distribution campaign for a survey via a specific channel.

| Attribute | Data Type | Constraints | Description | Example Value |
|---|---|---|---|---|
| id | UUID | PK, NOT NULL | Unique distribution campaign identifier | `"b8c9d0e1-..."` |
| survey_id | UUID | FK → Survey.id, NOT NULL, INDEX | Survey being distributed | `"c3d4e5f6-..."` |
| workspace_id | UUID | FK → Workspace.id, NOT NULL, INDEX | Owning workspace | `"a1b2c3d4-..."` |
| channel | VARCHAR(20) | NOT NULL | Distribution channel (see DistributionChannel enum) | `"email"` |
| name | VARCHAR(255) | NOT NULL | Human-readable campaign name | `"Q4 NPS — Enterprise Segment"` |
| audience_list_id | UUID | FK → AudienceList.id, NULL | Recipient audience list (null for public/QR) | `"c9d0e1f2-..."` |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'draft' | Campaign status | `"sent"` |
| scheduled_at | TIMESTAMPTZ | NULL | Scheduled dispatch time; NULL = immediate | `"2024-06-01T09:00:00Z"` |
| sent_at | TIMESTAMPTZ | NULL | Actual dispatch timestamp | `"2024-06-01T09:00:07Z"` |
| sender_name | VARCHAR(255) | NULL | From-name for email campaigns | `"Acme Research Team"` |
| sender_email | VARCHAR(320) | NULL | Verified from-address for email campaigns | `"surveys@acme.com"` |
| subject_line | VARCHAR(998) | NULL | Email subject line | `"We'd love your feedback!"` |
| stats | JSONB | NOT NULL, DEFAULT '{}' | Live stats: sent, delivered, opened, clicked, bounced | `{"sent":500,"delivered":487}` |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp | `"2024-05-30T11:00:00Z"` |

---

### ResponseSession

Tracks a single respondent's session for a survey (opened → in-progress → submitted).
Stored in MongoDB for flexible partial-response schema.

| Attribute | Data Type | Constraints | Description | Example Value |
|---|---|---|---|---|
| _id | ObjectId | PK | MongoDB document identifier | `"6657a3bc2f1e4a001234abcd"` |
| survey_id | UUID (string) | NOT NULL, INDEX | Survey being responded to | `"c3d4e5f6-..."` |
| distribution_id | UUID (string) | NULL, INDEX | Campaign that delivered the link | `"b8c9d0e1-..."` |
| respondent_email | String | NULL | Email of authenticated respondent | `"user@example.com"` |
| respondent_token_hash | String | NULL | SHA-256 hash of the JWT invitation token | `"ab34cd56..."` |
| ip_hash | String | NOT NULL | BLAKE2b hash of IP + UA + survey_id + date | `"3f7a9e2b..."` |
| status | String | NOT NULL, DEFAULT 'in_progress' | Session status (see ResponseStatus enum) | `"submitted"` |
| current_page | Integer | NOT NULL, DEFAULT 1 | Last page the respondent was viewing | `3` |
| partial_answers | Object | NOT NULL, DEFAULT {} | Map of question_id → raw answer value | `{"e5f6...": 9}` |
| started_at | Date | NOT NULL | Session open timestamp | `ISODate("2024-06-02T14:10:00Z")` |
| submitted_at | Date | NULL | Final submission timestamp | `ISODate("2024-06-02T14:18:33Z")` |
| expires_at | Date | NOT NULL | Partial session TTL (7-day default) | `ISODate("2024-06-09T14:10:00Z")` |

---

### Response (Individual Answer Record)

A committed, immutable answer to a single question from a completed ResponseSession.
Stored in PostgreSQL for queryability and strong consistency.

| Attribute | Data Type | Constraints | Description | Example Value |
|---|---|---|---|---|
| id | UUID | PK, NOT NULL | Unique answer record identifier | `"d0e1f2a3-..."` |
| session_id | VARCHAR(24) | NOT NULL, INDEX | MongoDB ResponseSession._id reference | `"6657a3bc2f1e4a001234abcd"` |
| survey_id | UUID | FK → Survey.id, NOT NULL, INDEX | Parent survey | `"c3d4e5f6-..."` |
| question_id | UUID | FK → Question.id, NOT NULL | Answered question | `"e5f6a7b8-..."` |
| answer_value | JSONB | NOT NULL | Normalized answer payload (type-specific) | `{"score":9}` |
| score | NUMERIC(7,4) | NULL | Computed numeric score for scored question types | `9.0000` |
| file_s3_key | VARCHAR(512) | NULL | S3 object key for file-upload answers | `"uploads/acme/d0e1f2a3.pdf"` |
| source | VARCHAR(20) | NOT NULL, DEFAULT 'web' | Response origin: web, api, import, sdk | `"web"` |
| submitted_at | TIMESTAMPTZ | NOT NULL | Submission timestamp | `"2024-06-02T14:18:33Z"` |

---

### AudienceList

A named list of contacts used as the target audience for a distribution campaign.

| Attribute | Data Type | Constraints | Description | Example Value |
|---|---|---|---|---|
| id | UUID | PK, NOT NULL | Unique audience list identifier | `"c9d0e1f2-..."` |
| workspace_id | UUID | FK → Workspace.id, NOT NULL, INDEX | Owning workspace | `"a1b2c3d4-..."` |
| name | VARCHAR(255) | NOT NULL | Human-readable list name | `"Enterprise Tier Customers Q4"` |
| contact_count | INTEGER | NOT NULL, DEFAULT 0 | Denormalized count of active contacts | `1247` |
| source | VARCHAR(30) | NOT NULL | Import source: csv_upload, api, hubspot, salesforce | `"csv_upload"` |
| tags | TEXT[] | NULL | Array of workspace-defined classification tags | `["enterprise","2024-q4"]` |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp | `"2024-05-20T08:00:00Z"` |
| deleted_at | TIMESTAMPTZ | NULL | Soft-delete timestamp | `null` |

---

### Contact

An individual recipient within an AudienceList. Sensitive PII stored encrypted at rest (AES-256).

| Attribute | Data Type | Constraints | Description | Example Value |
|---|---|---|---|---|
| id | UUID | PK, NOT NULL | Unique contact identifier | `"e1f2a3b4-..."` |
| workspace_id | UUID | FK → Workspace.id, NOT NULL, INDEX | Owning workspace | `"a1b2c3d4-..."` |
| audience_list_id | UUID | FK → AudienceList.id, NOT NULL, INDEX | Parent audience list | `"c9d0e1f2-..."` |
| email | VARCHAR(320) | NOT NULL | Email address (encrypted, indexed on hash) | `"contact@example.com"` |
| email_hash | CHAR(64) | NOT NULL, INDEX | SHA-256 of lowercase email for deduplication | `"5d41402abc4b..."` |
| first_name | VARCHAR(255) | NULL | First name (encrypted) | `"Alice"` |
| last_name | VARCHAR(255) | NULL | Last name (encrypted) | `"Smith"` |
| phone | VARCHAR(20) | NULL | Phone number in E.164 format (encrypted) | `"+14155552671"` |
| custom_attributes | JSONB | NOT NULL, DEFAULT '{}' | Workspace-defined merge fields | `{"account_tier":"enterprise"}` |
| opt_in_sms | BOOLEAN | NOT NULL, DEFAULT FALSE | Documented SMS opt-in consent status | `true` |
| opt_in_at | TIMESTAMPTZ | NULL | Timestamp of most recent opt-in event | `"2024-04-10T09:00:00Z"` |
| unsubscribed_at | TIMESTAMPTZ | NULL | Timestamp of unsubscribe event; NULL = subscribed | `null` |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp | `"2024-05-20T08:02:00Z"` |

---

### ReportDefinition

A saved analytics report configuration for a workspace, including filters and visualization settings.

| Attribute | Data Type | Constraints | Description | Example Value |
|---|---|---|---|---|
| id | UUID | PK, NOT NULL | Unique report definition identifier | `"f2a3b4c5-..."` |
| workspace_id | UUID | FK → Workspace.id, NOT NULL, INDEX | Owning workspace | `"a1b2c3d4-..."` |
| survey_id | UUID | FK → Survey.id, NULL | Scoped survey; NULL for cross-survey reports | `"c3d4e5f6-..."` |
| created_by | UUID | FK → User.id, NOT NULL | Report author | `"d290f1ee-..."` |
| name | VARCHAR(255) | NOT NULL | Report display name | `"Q4 NPS Trend by Region"` |
| filter_config | JSONB | NOT NULL | Cross-filter dimensions and date range config | `{"date_range":"last_90_days","filters":[...]}` |
| chart_config | JSONB | NOT NULL | Recharts visualization type and axes config | `{"type":"line","x_axis":"submitted_at"}` |
| schedule | JSONB | NULL | Auto-delivery schedule (cron + recipients) | `{"cron":"0 9 * * 1","recipients":["..."]}` |
| last_generated_at | TIMESTAMPTZ | NULL | Most recent report generation timestamp | `"2024-06-03T09:00:00Z"` |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp | `"2024-05-15T11:00:00Z"` |

---

### WebhookEndpoint

A workspace-configured HTTP endpoint that receives signed event payloads.

| Attribute | Data Type | Constraints | Description | Example Value |
|---|---|---|---|---|
| id | UUID | PK, NOT NULL | Unique webhook endpoint identifier | `"a3b4c5d6-..."` |
| workspace_id | UUID | FK → Workspace.id, NOT NULL, INDEX | Owning workspace | `"a1b2c3d4-..."` |
| url | VARCHAR(2048) | NOT NULL | Destination HTTPS URL | `"https://hooks.acme.com/survey-results"` |
| secret_hash | VARCHAR(128) | NOT NULL | bcrypt hash of signing secret (for validation display) | `"$2b$12$..."` |
| event_types | TEXT[] | NOT NULL | Array of subscribed event type strings | `["response.submitted","survey.closed"]` |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether the endpoint is enabled | `true` |
| failure_count | SMALLINT | NOT NULL, DEFAULT 0 | Consecutive delivery failures since last success | `0` |
| last_triggered_at | TIMESTAMPTZ | NULL | Most recent delivery attempt timestamp | `"2024-06-02T14:18:38Z"` |
| last_success_at | TIMESTAMPTZ | NULL | Most recent successful delivery timestamp | `"2024-06-02T14:18:39Z"` |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp | `"2024-04-01T10:00:00Z"` |

---

### SubscriptionPlan

A platform-defined subscription plan template. One row per billing tier per billing cycle.

| Attribute | Data Type | Constraints | Description | Example Value |
|---|---|---|---|---|
| id | UUID | PK, NOT NULL | Unique plan identifier | `"b4c5d6e7-..."` |
| tier | VARCHAR(20) | NOT NULL, UNIQUE | Plan tier identifier | `"business"` |
| display_name | VARCHAR(100) | NOT NULL | Billing page display name | `"Business"` |
| stripe_price_id_monthly | VARCHAR(100) | NOT NULL | Stripe Price ID for monthly billing | `"price_1Nz3Km..."` |
| stripe_price_id_annual | VARCHAR(100) | NOT NULL | Stripe Price ID for annual billing | `"price_1Nz3La..."` |
| response_quota_monthly | INTEGER | NULL | Monthly response quota; NULL = unlimited | `10000` |
| active_survey_limit | INTEGER | NULL | Max active surveys; NULL = unlimited | `null` |
| seat_limit | INTEGER | NULL | Max workspace members; NULL = unlimited | `25` |
| features | JSONB | NOT NULL | Feature flag map for this tier | `{"branching_logic":true,"api_access":true}` |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Plan creation timestamp | `"2023-01-01T00:00:00Z"` |

---

### WorkspaceSubscription

Tracks the active and historical subscription state for a workspace.

| Attribute | Data Type | Constraints | Description | Example Value |
|---|---|---|---|---|
| id | UUID | PK, NOT NULL | Unique subscription record identifier | `"c5d6e7f8-..."` |
| workspace_id | UUID | FK → Workspace.id, NOT NULL, INDEX | Subscribed workspace | `"a1b2c3d4-..."` |
| plan_id | UUID | FK → SubscriptionPlan.id, NOT NULL | Active plan | `"b4c5d6e7-..."` |
| stripe_customer_id | VARCHAR(100) | NOT NULL | Stripe Customer object ID | `"cus_Nz3KmL..."` |
| stripe_subscription_id | VARCHAR(100) | UNIQUE, NOT NULL | Stripe Subscription object ID | `"sub_Nz3KmL..."` |
| billing_cycle | VARCHAR(10) | NOT NULL | Billing frequency | `"annual"` |
| status | VARCHAR(20) | NOT NULL | Stripe subscription status | `"active"` |
| current_period_start | TIMESTAMPTZ | NOT NULL | Start of the current billing period | `"2024-01-01T00:00:00Z"` |
| current_period_end | TIMESTAMPTZ | NOT NULL | End of the current billing period | `"2024-12-31T23:59:59Z"` |
| response_count_this_period | INTEGER | NOT NULL, DEFAULT 0 | Responses consumed in current period | `4372` |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Subscription creation timestamp | `"2024-01-01T00:00:01Z"` |

---

### AuditLog

Immutable record of every administrative action in the platform. Append-only.

| Attribute | Data Type | Constraints | Description | Example Value |
|---|---|---|---|---|
| id | BIGSERIAL | PK, NOT NULL | Monotonically increasing audit log entry ID | `1048576` |
| workspace_id | UUID | NOT NULL, INDEX | Workspace context of the action | `"a1b2c3d4-..."` |
| actor_user_id | UUID | NULL | User performing the action; NULL for system jobs | `"d290f1ee-..."` |
| actor_type | VARCHAR(20) | NOT NULL | Actor kind: user, service, system | `"user"` |
| action | VARCHAR(80) | NOT NULL | Dot-notation action identifier | `"survey.published"` |
| resource_type | VARCHAR(40) | NOT NULL | Affected resource type | `"survey"` |
| resource_id | UUID | NOT NULL | Affected resource identifier | `"c3d4e5f6-..."` |
| before_state | JSONB | NULL | Resource state before the action | `{"status":"draft"}` |
| after_state | JSONB | NULL | Resource state after the action | `{"status":"published"}` |
| ip_address | INET | NULL | Actor IP address | `"203.0.113.45"` |
| user_agent | TEXT | NULL | Actor browser/client user agent string | `"Mozilla/5.0..."` |
| request_trace_id | VARCHAR(128) | NULL | Distributed trace ID for log correlation | `"3f7a9e2b-..."` |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Event timestamp | `"2024-06-01T12:00:05Z"` |

---

## Enumerated Types

### QuestionType
| Value | Description |
|---|---|
| `multiple_choice` | Select one or more from a predefined list |
| `single_select` | Select exactly one from a predefined list (radio) |
| `short_text` | Free-text response up to 500 characters |
| `long_text` | Free-text response up to 10,000 characters |
| `rating_scale` | Numeric scale (configurable range 1–10) |
| `nps` | Net Promoter Score 0–10 scale |
| `csat` | Customer Satisfaction Score 1–5 scale |
| `yes_no` | Binary Yes/No question |
| `matrix` | Grid of sub-questions against a shared scale |
| `ranking` | Drag-and-drop reordering of a set of options |
| `file_upload` | File attachment upload (Starter+) |
| `slider` | Continuous numeric slider (Starter+) |
| `date_time` | Date and/or time picker (Starter+) |
| `payment` | Stripe payment collection step (Business+) |
| `consent_checkbox` | GDPR-compliant explicit consent tick-box |
| `display_text` | Non-question display block (heading, instructions) |

### SurveyStatus
| Value | Description |
|---|---|
| `draft` | Not yet published; invisible to respondents |
| `published` | Active and accepting responses |
| `paused` | Temporarily closed; link shows paused message |
| `closed` | Manually closed; no new responses accepted |
| `expired` | Automatically closed after expiry date |
| `archived` | Soft-archived; removed from active list |

### DistributionChannel
| Value | Description |
|---|---|
| `email` | SendGrid email campaign with personalized links |
| `sms` | Twilio SMS with survey link |
| `web_embed` | iFrame or JavaScript SDK embed |
| `qr_code` | QR code pointing to public survey URL |
| `public_link` | Shareable public URL (no personalization) |
| `api` | Programmatic distribution via REST API |

### ResponseStatus
| Value | Description |
|---|---|
| `in_progress` | Respondent has started but not submitted |
| `submitted` | Respondent completed and submitted the survey |
| `expired` | Partial session exceeded the 7-day TTL |
| `disqualified` | Respondent failed age gate or screener |

### WorkspaceRole
| Value | Description |
|---|---|
| `owner` | Full access including billing and workspace deletion |
| `admin` | Full access except workspace deletion and billing |
| `editor` | Create and edit surveys; manage distributions |
| `analyst` | Read-only analytics and data export access |
| `viewer` | Read-only access to surveys and basic summaries |

### SubscriptionTier
| Value | Description |
|---|---|
| `free` | No cost; limited features and quotas |
| `starter` | Entry-level paid tier |
| `business` | Full-featured mid-market tier |
| `enterprise` | Custom contract; unlimited seats and SSO |

### LogicOperator
| Value | Description |
|---|---|
| `equals` | Answer exactly matches operand value |
| `not_equals` | Answer does not match operand value |
| `contains` | Text answer contains the operand substring |
| `greater_than` | Numeric answer is greater than operand |
| `less_than` | Numeric answer is less than operand |
| `is_answered` | Question was answered (any non-null value) |
| `is_not_answered` | Question was skipped or left blank |

---

## Relationships

| Relationship | Cardinality | Notes |
|---|---|---|
| Workspace → User (Owner) | Many-to-one | `workspace.owner_user_id → user.id` |
| Workspace → WorkspaceMember | One-to-many | Junction table with role; one User may belong to many Workspaces |
| Workspace → Survey | One-to-many | All surveys scoped to a workspace |
| Survey → Question | One-to-many | Ordered by `position`; CASCADE delete on survey hard-delete |
| Question → QuestionOption | One-to-many | Applies to choice-based question types |
| Question → ConditionalLogicRule | One-to-many | `source_question_id` and `target_question_id` both FK to Question |
| Survey → SurveyDistribution | One-to-many | One survey may have multiple campaigns |
| SurveyDistribution → AudienceList | Many-to-one | Multiple campaigns may share an audience list |
| AudienceList → Contact | One-to-many | Contacts in an audience list |
| ResponseSession → Response | One-to-many | One session produces one Response row per answered question |
| Survey → Response | One-to-many | Indexed for analytics queries |
| Workspace → AuditLog | One-to-many | All workspace actions produce audit records |
| Workspace → WorkspaceSubscription | One-to-one (active) | Historical rows allowed; current plan identified by status='active' |
| WorkspaceSubscription → SubscriptionPlan | Many-to-one | Multiple workspaces may share the same plan template |

---

## Index Strategy

| Table | Index | Type | Purpose |
|---|---|---|---|
| survey | `(workspace_id, status, deleted_at)` | B-tree composite | Active survey listing per workspace |
| survey | `slug` | B-tree UNIQUE | Public URL slug lookup |
| question | `(survey_id, position)` | B-tree composite | Ordered question retrieval for rendering |
| response | `(survey_id, submitted_at)` | B-tree composite | Time-range analytics queries |
| response | `(survey_id, question_id)` | B-tree composite | Per-question aggregation |
| response_session | `(survey_id, status)` | B-tree composite (MongoDB) | Completion rate analytics |
| contact | `email_hash` | B-tree | Email deduplication and suppression lookup |
| contact | `(workspace_id, unsubscribed_at)` | Partial B-tree | Active contact listing |
| audit_log | `(workspace_id, created_at)` | B-tree composite | Audit trail retrieval by workspace and time |
| audience_list | `workspace_id` | B-tree | Audience list management queries |
| workspace_subscription | `stripe_subscription_id` | B-tree UNIQUE | Stripe webhook event routing |

---

## Operational Policy Addendum

### 1. Response Data Privacy Policies
All PII stored in the Contact table (email, first_name, last_name, phone) is encrypted at the
column level using AWS KMS-backed AES-256 encryption via the `pgcrypto` extension with a
workspace-specific data key. Key rotation is performed annually. Email hashes use SHA-256 with a
per-workspace salt for deterministic deduplication without exposing the plaintext.

### 2. Survey Distribution Policies
ContactS uploaded via CSV import are validated against a regex and MX record check before insertion.
Duplicates within the same audience list are detected via `email_hash` and silently de-duplicated.
Contacts from suppressed or globally unsubscribed emails are filtered at insert time to prevent
them from ever appearing in a sendable audience list.

### 3. Analytics and Retention Policies
The `response` table is partitioned by `submitted_at` using PostgreSQL declarative range partitioning
with monthly partitions. Old partitions past the workspace retention window are detached and dropped
by the nightly lifecycle job. DynamoDB analytics records use `workspace_id#survey_id` as the
partition key and `metric_type#timestamp_bucket` as the sort key for efficient time-range queries.

### 4. System Availability Policies
Read replicas are provisioned on RDS PostgreSQL for all Business and Enterprise workspaces.
Analytics dashboard queries and export jobs are routed exclusively to read replicas to protect
primary write throughput. Connection pooling is provided by PgBouncer in transaction mode (max 200
server connections per replica). MongoDB (DocumentDB) uses a 3-node replica set with automatic
primary election on failure.
