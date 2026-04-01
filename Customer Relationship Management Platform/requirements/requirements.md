# Requirements Specification — Customer Relationship Management Platform

**Version:** 1.0  
**Status:** Approved  
**Last Updated:** 2025-07-15

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Functional Requirements](#2-functional-requirements)
   - 2.1 Lead Management
   - 2.2 Contact and Account Management
   - 2.3 Opportunity and Deal Management
   - 2.4 Activity and Communication
   - 2.5 Campaign Management
   - 2.6 Forecasting and Territory Management
   - 2.7 Custom Fields and Data Model
   - 2.8 Integrations and API
   - 2.9 Deduplication and Data Quality
   - 2.10 Security and Access Control
3. [Non-Functional Requirements](#3-non-functional-requirements)
4. [Traceability Matrix](#4-traceability-matrix)

---

## 1. Introduction

### 1.1 Purpose

This document defines the complete set of functional and non-functional requirements for the Enterprise Customer Relationship Management (CRM) Platform. It is the authoritative reference for product development, quality assurance, and stakeholder acceptance testing. All stated requirements are binding unless explicitly marked as out-of-scope.

### 1.2 Scope

The CRM Platform encompasses lead lifecycle management from initial capture through qualification and conversion; contact and account relationship management; opportunity tracking within configurable sales pipelines; activity logging across calls, emails, meetings, and tasks; revenue forecasting with manager approval workflows; territory assignment and rebalancing; and multi-channel campaign execution. The platform exposes a REST API and a web-based UI, and integrates with external systems including email providers, calendar services, ERP systems, identity providers, and communication tools.

**In Scope for v1.0:**
- Web-based UI with responsive design
- RESTful API with OAuth 2.0 authentication
- Lead capture via web forms, API, and CSV import
- Lead scoring using rule-based and ML-enhanced models
- Contact and account 360° view with activity timeline
- Multi-pipeline opportunity management with drag-drop stage progression
- Email and calendar bidirectional sync with Gmail and Outlook
- Automated email campaigns with A/B testing
- Territory management with rule-based assignment
- Revenue forecasting with multi-level rollups
- Duplicate detection and merge workflow
- Custom fields on core entities
- Integration framework with webhooks
- Audit logging and GDPR compliance

**Out of Scope for v1.0:**
- Native mobile applications (iOS/Android)
- AI-generated deal coaching recommendations
- CPQ (Configure Price Quote) integration
- Social media monitoring and engagement
- Telephony/VoIP integration

### 1.3 Definitions

| Term | Definition |
|---|---|
| Lead | An unqualified prospect record captured from an inbound source before assignment to a sales rep. |
| Contact | A qualified individual associated with an Account; created upon lead conversion or direct entry. |
| Account | An organisation or company with which the business has or seeks a commercial relationship. |
| Deal / Opportunity | A potential revenue event tracked through pipeline stages with a probability, close date, and amount. |
| Pipeline | A named sequence of Stages representing the sales process for a category of deals. |
| Stage | A discrete step within a Pipeline with defined entry criteria, exit criteria, and a win probability. |
| Activity | Any logged interaction with a Contact or Account: call log, email, meeting, task, or note. |
| Territory | A geographic, industry, or account-size-based grouping that determines which Sales Rep owns an Account. |
| Forecast | A rep's or manager's revenue estimate for a future period, expressed as Committed, Best Case, and Pipeline amounts. |
| Segment | A dynamic or static list of Contacts or Accounts that satisfy a set of filter criteria, used for campaigns. |
| CustomField | A tenant-defined metadata field appended to a core CRM object. |
| Tenant | The top-level organizational entity representing a customer company using the CRM platform. |
| MQL | Marketing Qualified Lead — a lead that meets defined criteria for sales engagement. |
| SQL | Sales Qualified Lead — a lead accepted by sales for active pursuit. |

---

## 2. Functional Requirements

### 2.1 Lead Management

#### FR-001 — Lead Capture via Web Form

**Priority:** P0 (Must Have)  
**Description:** The system MUST provide an embeddable JavaScript snippet that renders a configurable lead capture form on external websites. Forms submit to a public API endpoint that creates a Lead record in the tenant's database.

**Acceptance Criteria:**
- Form fields are configurable per tenant (name, email, phone, company, custom fields)
- Form validation runs client-side and server-side
- reCAPTCHA v3 integration prevents bot submissions (score threshold configurable)
- Submission triggers `LeadCaptured` domain event
- Submission response includes tracking ID for subsequent API calls
- Form styling is customizable via CSS variables

**Validation Rules:**
- Email field MUST match RFC 5321 format
- Phone field MUST match E.164 international format or tenant-specific regex
- Required fields are enforced before submission
- Duplicate email within same tenant triggers deduplication workflow (see FR-022)

**Related Use Cases:** UC-001, UC-002  
**Related NFRs:** NFR-002 (API latency)

---

#### FR-002 — Lead Capture via REST API

**Priority:** P0 (Must Have)  
**Description:** The system MUST expose a `POST /api/v1/leads` endpoint that accepts JSON lead payloads authenticated via API key or OAuth 2.0 access token.

**Acceptance Criteria:**
- Endpoint accepts standard lead fields (first_name, last_name, email, phone, company, source, custom fields)
- Response includes created Lead ID and HTTP 201 status
- Invalid payloads return HTTP 422 with field-level error details
- Endpoint enforces tenant isolation (authenticated principal's tenant)
- Endpoint rate limit: 100 requests per minute per API key
- Idempotency key header (`Idempotency-Key`) prevents duplicate submissions within 24-hour window

**Related Use Cases:** UC-001  
**Related NFRs:** NFR-001 (multi-tenancy), NFR-002 (performance)

---

#### FR-003 — Lead Bulk Import via CSV

**Priority:** P1 (Should Have)  
**Description:** The system MUST provide a CSV import wizard that maps CSV columns to Lead fields, validates rows, and creates Leads in batches.

**Acceptance Criteria:**
- Import wizard allows file upload (max 10 MB, max 50,000 rows)
- User maps CSV headers to system fields (drag-drop or dropdown)
- Preview displays first 10 rows with mapped values
- Validation report shows errors per row (invalid email, missing required field, etc.)
- User can skip invalid rows or abort entire import
- Import creates background job with progress tracking
- Import completion triggers email notification to user
- Import creates audit log entry with file name, row count, success count, failure count

**Validation Rules:**
- Email field required and must be valid
- Duplicate emails within same CSV file are flagged
- Import aborts if >20% of rows fail validation

**Related Use Cases:** UC-001  
**Related NFRs:** NFR-003 (scalability)

---

#### FR-004 — Lead Scoring Engine

**Priority:** P1 (Should Have)  
**Description:** The system MUST automatically assign a numeric score (0-100) to each Lead upon creation and update the score when Lead attributes change.

**Acceptance Criteria:**
- Scoring engine evaluates rule-based criteria (firmographic, demographic, behavioral)
- Rules are configurable per tenant (weighted sum of conditions)
- Default rules: company size (+20 if >1000 employees), industry match (+15), email domain match (+10), page visit count (+1 per visit up to 20)
- Score computation completes within 5 seconds of Lead creation
- Score updates trigger `LeadScoreUpdated` event
- Lead list UI displays score with color coding (0-30 red, 31-70 yellow, 71-100 green)
- Historical score changes are logged in activity timeline

**Extensibility:** ML-based scoring model integration point (v1.1)

**Related Use Cases:** UC-002  
**Related NFRs:** NFR-002 (performance)

---

#### FR-005 — Lead Assignment Rules

**Priority:** P0 (Must Have)  
**Description:** The system MUST support configurable assignment rules that automatically assign Leads to Sales Reps based on criteria such as geography, industry, company size, or lead source.

**Acceptance Criteria:**
- Assignment rules are evaluated in priority order (rank 1, 2, 3, ...)
- First matching rule assigns the Lead to the specified User or Territory
- Rules support AND/OR conditions (e.g., "Country = USA AND Industry = Technology")
- Rules support round-robin assignment within a pool of eligible reps
- Assignment triggers `LeadAssigned` event and email notification to assigned rep
- Manual override allows reassignment to different rep with reason code
- Unmatched Leads are assigned to a default queue or left unassigned

**Related Use Cases:** UC-002  
**Related NFRs:** NFR-004 (configurability)

---

#### FR-006 — Lead Conversion to Contact and Opportunity

**Priority:** P0 (Must Have)  
**Description:** The system MUST provide a "Convert Lead" action that creates a Contact record, optionally an Account record, and optionally an Opportunity record, then marks the Lead as converted.

**Acceptance Criteria:**
- Conversion wizard prompts for: create new Account or link to existing Account, create Opportunity (yes/no), Opportunity details (amount, close date, stage)
- Conversion is atomic: all records are created in a single database transaction
- Lead status changes to "Converted" (immutable)
- Lead's custom field values are copied to Contact and Opportunity based on tenant-defined field mapping
- Conversion triggers `LeadConverted` event
- Converted Lead remains viewable but is excluded from active lead lists

**Related Use Cases:** UC-003  
**Related NFRs:** NFR-001 (data integrity)

---

### 2.2 Contact and Account Management

#### FR-007 — Contact CRUD Operations

**Priority:** P0 (Must Have)  
**Description:** The system MUST provide Create, Read, Update, Delete operations for Contact records via UI and API.

**Acceptance Criteria:**
- Contact fields: first_name, last_name, email, phone, mobile, title, account_id, owner_id, lead_source, custom fields
- Email field is unique per tenant (validation enforced)
- Update triggers `ContactUpdated` event
- Delete is soft delete (deleted_at timestamp); Contact is excluded from UI but retained for audit trail
- Contact detail page shows: basic info, related Deals, activity timeline, custom fields, email threads

**Related Use Cases:** UC-004  
**Related NFRs:** NFR-001 (multi-tenancy)

---

#### FR-008 — Account CRUD Operations

**Priority:** P0 (Must Have)  
**Description:** The system MUST provide Create, Read, Update, Delete operations for Account (organization) records via UI and API.

**Acceptance Criteria:**
- Account fields: name, domain, industry, employee_count, annual_revenue, billing_address, shipping_address, account_owner_id, territory_id, custom fields
- Account detail page shows: basic info, contacts list, open deals, closed deals, activity timeline, custom fields
- Update triggers `AccountUpdated` event
- Delete is soft delete; Account deletion also soft-deletes all child Contacts and Deals (cascade)
- Account merge capability (see FR-023)

**Related Use Cases:** UC-004  
**Related NFRs:** NFR-001 (multi-tenancy)

---

#### FR-009 — Contact and Account 360° View

**Priority:** P1 (Should Have)  
**Description:** The system MUST provide a unified detail page for each Contact and Account that aggregates all related data: activities, deals, emails, notes, tasks, custom fields, and change history.

**Acceptance Criteria:**
- Page layout: left column (basic info, custom fields), center column (activity timeline), right column (related deals, quick actions)
- Activity timeline displays all logged activities (calls, emails, meetings, notes) in reverse chronological order
- Timeline is filterable by activity type and date range
- Email threads are grouped and expandable
- Deal cards show stage, amount, probability, close date, and progress bar
- Page loads within 2 seconds for accounts with up to 1000 activities

**Related Use Cases:** UC-005  
**Related NFRs:** NFR-002 (performance)

---

### 2.3 Opportunity and Deal Management

#### FR-010 — Pipeline Configuration

**Priority:** P0 (Must Have)  
**Description:** The system MUST allow CRM Administrators to create and configure multiple named Pipelines, each with custom Stages.

**Acceptance Criteria:**
- Pipeline fields: name, description, is_default, stages array
- Stage fields: name, probability_percent, is_closed_won, is_closed_lost, order_index
- Stage order is user-defined (drag-drop in UI)
- Each Pipeline must have exactly one "Closed Won" stage and one "Closed Lost" stage
- Pipeline cannot be deleted if any active Deals reference it
- Pipeline changes trigger `PipelineConfigured` event

**Related Use Cases:** UC-006  
**Related NFRs:** NFR-004 (configurability)

---

#### FR-011 — Deal Creation and Management

**Priority:** P0 (Must Have)  
**Description:** The system MUST provide Create, Read, Update, Delete operations for Deal (Opportunity) records via UI and API.

**Acceptance Criteria:**
- Deal fields: name, account_id, contact_id (primary), amount, currency, probability, close_date, stage_id, pipeline_id, owner_id, description, custom fields
- Amount field supports multiple currencies (USD, EUR, GBP, etc.) with exchange rate lookup
- Probability is auto-populated from Stage configuration but can be manually overridden
- Deal list view supports filtering by stage, owner, close date range, amount range
- Deal detail page shows: basic info, activity timeline, stage history, quote lines (if applicable)
- Update triggers `DealUpdated` event

**Related Use Cases:** UC-006  
**Related NFRs:** NFR-001 (multi-tenancy)

---

#### FR-012 — Deal Stage Progression

**Priority:** P0 (Must Have)  
**Description:** The system MUST allow users to move Deals between Stages via drag-drop in a kanban board UI or via a dropdown selector in the detail page.

**Acceptance Criteria:**
- Stage change updates deal.stage_id, deal.probability, and deal.stage_changed_at
- Stage change creates a DealStageHistory record (deal_id, from_stage_id, to_stage_id, changed_by, changed_at)
- Stage change triggers `DealStageChanged` event
- Moving to "Closed Won" stage requires validation: amount > 0, close_date <= today
- Moving to "Closed Lost" stage prompts for loss reason (competitor, budget, timing, no decision, other)
- Closed deals are excluded from active pipeline views but remain in reporting

**Related Use Cases:** UC-006  
**Related NFRs:** NFR-002 (performance)

---

#### FR-013 — Deal Forecasting

**Priority:** P1 (Should Have)  
**Description:** The system MUST provide a forecasting module where Sales Reps submit Committed, Best Case, and Pipeline forecast amounts for each fiscal period.

**Acceptance Criteria:**
- Forecast periods are monthly or quarterly (tenant-configurable)
- Forecast categories: Committed (high confidence, close_date in period, probability >= 80%), Best Case (includes Committed + probable deals), Pipeline (all open deals in period)
- Rep submits forecast via UI form; submission creates ForecastSubmission record with status "Draft"
- Rep can edit draft forecast until "Submit" action, which changes status to "Submitted"
- Manager reviews submitted forecasts and can "Approve" or "Request Revision"
- Approved forecasts are locked and included in manager's rollup forecast
- Forecast dashboard shows: submitted amount, approved amount, actual closed amount (updated real-time), variance

**Related Use Cases:** UC-007  
**Related NFRs:** NFR-004 (configurability)

---

### 2.4 Activity and Communication

#### FR-014 — Activity Logging (Calls, Emails, Meetings, Notes, Tasks)

**Priority:** P0 (Must Have)  
**Description:** The system MUST allow users to log activities associated with Contacts, Accounts, and Deals. Activity types: Call, Email, Meeting, Note, Task.

**Acceptance Criteria:**
- Activity fields: type, subject, description, related_to_type, related_to_id, created_by, created_at, completed_at (for tasks), attendees (for meetings), call_duration_seconds (for calls)
- Activities appear on the related entity's timeline
- Tasks have status: Open, In Progress, Completed, Cancelled
- Tasks have due_date field; overdue tasks are highlighted in UI
- Activity creation triggers `ActivityLogged` event

**Related Use Cases:** UC-005  
**Related NFRs:** NFR-002 (performance)

---

#### FR-015 — Email Sync (Gmail and Outlook)

**Priority:** P1 (Should Have)  
**Description:** The system MUST support bidirectional email synchronization with Gmail (via Gmail API) and Outlook (via Microsoft Graph API) using OAuth 2.0 authentication.

**Acceptance Criteria:**
- User authorizes email access via OAuth flow
- System polls user's inbox every 5 minutes for new emails
- Emails with recognized Contact email addresses are automatically associated with that Contact's timeline
- User can manually associate emails with Contacts, Accounts, or Deals from within the CRM
- Sent emails from CRM are logged in the Activity timeline
- Email threads are grouped by subject and In-Reply-To header
- Email sync errors (OAuth token expiry, API quota exceeded) trigger user notification

**Related Use Cases:** UC-005  
**Related NFRs:** NFR-009 (integration), NFR-010 (reliability)

---

#### FR-016 — Calendar Sync (Google Calendar and Outlook Calendar)

**Priority:** P1 (Should Have)  
**Description:** The system MUST support bidirectional calendar synchronization with Google Calendar and Outlook Calendar using OAuth 2.0 authentication.

**Acceptance Criteria:**
- User authorizes calendar access via OAuth flow
- Meetings created in CRM are added to user's calendar with attendees
- Meetings created in external calendar are imported to CRM if attendees include known Contacts
- Meeting updates (time, attendees, location) are bidirectionally synced
- Meeting cancellations are synced and marked as cancelled in CRM
- Calendar sync errors trigger user notification

**Related Use Cases:** UC-005  
**Related NFRs:** NFR-009 (integration), NFR-010 (reliability)

---

### 2.5 Campaign Management

#### FR-017 — Email Campaign Creation

**Priority:** P1 (Should Have)  
**Description:** The system MUST provide a campaign builder UI that allows Marketing Managers to create email campaigns with audience segments, email templates, and send schedules.

**Acceptance Criteria:**
- Campaign fields: name, description, segment_id, template_id, from_name, from_email, subject, scheduled_send_at, status (draft, scheduled, sending, sent, paused, cancelled)
- Campaign builder includes WYSIWYG email editor with merge fields (e.g., {{first_name}}, {{company}})
- User can preview email with sample Contact data
- User can schedule immediate send or future send date/time
- Campaign execution creates CampaignSend record per recipient Contact
- Send respects Contact's email_opt_out flag (no emails to opted-out Contacts)

**Related Use Cases:** UC-008  
**Related NFRs:** NFR-003 (scalability)

---

#### FR-018 — Campaign Segment Builder

**Priority:** P1 (Should Have)  
**Description:** The system MUST provide a segment builder UI that allows users to create dynamic or static Contact/Account lists based on filter criteria.

**Acceptance Criteria:**
- Segment types: Dynamic (re-evaluated on each use), Static (snapshot at creation time)
- Filter criteria: field comparisons (equals, not equals, contains, greater than, less than, in, not in), date ranges, custom field values
- Filters support AND/OR logic with grouping (nested conditions)
- Segment preview shows matching record count and first 10 records
- Segments can be saved and reused across campaigns
- Segment modification triggers re-evaluation for dynamic segments

**Related Use Cases:** UC-008  
**Related NFRs:** NFR-004 (configurability)

---

#### FR-019 — Campaign Email Tracking (Opens, Clicks, Bounces, Unsubscribes)

**Priority:** P1 (Should Have)  
**Description:** The system MUST track email engagement metrics for each campaign: opens, clicks, bounces, and unsubscribes.

**Acceptance Criteria:**
- Email open tracking via 1x1 pixel image embed (tracks first open per recipient)
- Link click tracking via redirect URL with unique tracking token
- Bounce handling via SMTP bounce message parsing or webhook from email service provider
- Unsubscribe link included in every campaign email (footer)
- Unsubscribe action sets Contact.email_opt_out = true and logs unsubscribe event
- Campaign dashboard shows: sent count, delivered count, open rate, click rate, bounce rate, unsubscribe count

**Compliance:**
- Unsubscribe link must be visible and functional (CAN-SPAM Act compliance)
- Unsubscribe must be honored immediately (GDPR compliance)

**Related Use Cases:** UC-008  
**Related NFRs:** NFR-012 (compliance)

---

### 2.6 Forecasting and Territory Management

#### FR-020 — Territory Hierarchy and Assignment

**Priority:** P1 (Should Have)  
**Description:** The system MUST support a hierarchical territory structure where Accounts are assigned to Territories based on configurable rules, and Territories are owned by Sales Reps.

**Acceptance Criteria:**
- Territory fields: name, description, parent_territory_id, owner_id (Sales Rep or Manager), assignment_rules
- Assignment rules: geographic (country, state, city, postal code), firmographic (industry, employee count, annual revenue), custom field conditions
- Territory hierarchy supports unlimited depth (e.g., Global > North America > USA > West > California)
- Account.territory_id is auto-assigned when Account is created or updated based on matching rules
- Territory reassignment (annual rebalancing) creates TerritoryReassignment records with old_territory_id, new_territory_id, effective_date
- Reassignment can be previewed (dry-run mode) before committing

**Related Use Cases:** UC-009  
**Related NFRs:** NFR-004 (configurability)

---

#### FR-021 — Revenue Forecast Rollup

**Priority:** P1 (Should Have)  
**Description:** The system MUST aggregate individual rep forecasts into manager and VP-level rollups based on reporting hierarchy.

**Acceptance Criteria:**
- Forecast rollup is computed hierarchically: Rep → Manager → Director → VP → CRO
- Rollup includes: total committed, total best case, total pipeline, number of deals, weighted probability sum
- Rollup updates in real-time as reps submit or revise forecasts
- Rollup dashboard shows breakdown by rep with variance vs. quota
- Forecast snapshots are saved at period-end (immutable historical record)

**Related Use Cases:** UC-007  
**Related NFRs:** NFR-002 (performance), NFR-011 (data accuracy)

---

### 2.7 Custom Fields and Data Model

#### FR-022 — Custom Field Definition

**Priority:** P1 (Should Have)  
**Description:** The system MUST allow CRM Administrators to define custom fields on core entities: Lead, Contact, Account, Deal, Activity.

**Acceptance Criteria:**
- Custom field types: Text (single line), Text Area (multi-line), Number, Currency, Date, Picklist (single-select), Multi-select Picklist, Checkbox, URL, Email, Lookup (foreign key to another entity)
- Custom field attributes: label, API name, required (yes/no), default value, help text, visibility (all users or specific roles)
- Custom field API name auto-generated from label (e.g., "Customer Segment" → "customer_segment_c")
- Custom fields appear in create/edit forms, detail pages, and list views
- Custom fields are searchable and filterable
- Custom field values are stored in JSONB column (flexible schema) or EAV model (normalized schema)

**Related Use Cases:** UC-010  
**Related NFRs:** NFR-004 (configurability)

---

#### FR-023 — Duplicate Detection and Merge

**Priority:** P1 (Should Have)  
**Description:** The system MUST automatically detect potential duplicate Contact and Account records using fuzzy matching on name, email, phone, and domain fields.

**Acceptance Criteria:**
- Duplicate detection runs on record creation and update
- Matching algorithm: email exact match (100% confidence), phone exact match (90% confidence), name + company fuzzy match (Levenshtein distance < 3, 70% confidence)
- High-confidence duplicates (>= 90%) are automatically merged (configurable)
- Medium-confidence duplicates (50-89%) are flagged in a manual review queue
- Merge UI shows side-by-side comparison of field values with user-selectable "winning" values
- Merge operation creates MergeHistory record with merged_record_id, surviving_record_id, merged_at, merged_by
- Merged record is soft-deleted; all related activities and deals are reassigned to surviving record

**Related Use Cases:** UC-011  
**Related NFRs:** NFR-011 (data accuracy)

---

### 2.8 Integrations and API

#### FR-024 — REST API with OAuth 2.0 Authentication

**Priority:** P0 (Must Have)  
**Description:** The system MUST expose a RESTful API for all CRUD operations on core entities, authenticated via OAuth 2.0 (Authorization Code flow for user context, Client Credentials flow for server-to-server).

**Acceptance Criteria:**
- API versioning via URL path (e.g., /api/v1/leads)
- Authentication via JWT access token in Authorization header
- Access token TTL: 1 hour (configurable)
- Refresh token TTL: 30 days (configurable)
- Token introspection endpoint: `POST /api/v1/oauth/introspect`
- Token revocation endpoint: `POST /api/v1/oauth/revoke`
- API responses use standard HTTP status codes (200, 201, 400, 401, 403, 404, 422, 500)
- Error responses include structured JSON with error code, message, and field-level details (if applicable)

**Related Use Cases:** All  
**Related NFRs:** NFR-001 (multi-tenancy), NFR-002 (performance), NFR-007 (security)

---

#### FR-025 — Webhook Subscriptions

**Priority:** P1 (Should Have)  
**Description:** The system MUST allow users to create webhook subscriptions that post domain event payloads to external URLs when specified events occur.

**Acceptance Criteria:**
- Webhook fields: url, events (array of event types), secret (for HMAC signature), status (active, paused)
- Supported events: LeadCaptured, LeadConverted, ContactCreated, ContactUpdated, DealStageChanged, ActivityLogged, CampaignSent
- Webhook delivery: HTTP POST to configured URL with JSON payload
- Webhook signature: HMAC-SHA256 of payload body using webhook secret, sent in X-CRM-Signature header
- Retry policy: 3 attempts with exponential backoff (1s, 5s, 25s)
- Failed webhooks are logged with failure reason; user can manually retry from UI
- Webhook delivery logs are retained for 30 days

**Related Use Cases:** UC-012  
**Related NFRs:** NFR-009 (integration), NFR-010 (reliability)

---

### 2.9 Deduplication and Data Quality

#### FR-026 — Data Import with Field Mapping

**Priority:** P1 (Should Have)  
**Description:** The system MUST provide a data import wizard for bulk import of Contacts, Accounts, and Deals from CSV or Excel files with user-defined field mapping.

**Acceptance Criteria:**
- Supported file formats: CSV, XLS, XLSX (max 10 MB, max 50,000 rows)
- Import wizard steps: 1) Upload file, 2) Map columns to fields, 3) Preview, 4) Validate, 5) Import
- User can map columns to standard fields or custom fields
- Validation rules: required fields, data type checks, foreign key validation (e.g., Account lookup by name)
- Import creates background job with progress updates
- Import summary: total rows, success count, error count, skipped count
- Import errors are downloadable as CSV with row number and error message per row

**Related Use Cases:** UC-013  
**Related NFRs:** NFR-003 (scalability), NFR-011 (data accuracy)

---

### 2.10 Security and Access Control

#### FR-027 — Role-Based Access Control (RBAC)

**Priority:** P0 (Must Have)  
**Description:** The system MUST enforce role-based access control where Users are assigned Roles, and Roles define permissions for each entity and operation.

**Acceptance Criteria:**
- Default roles: System Admin, Sales Manager, Sales Rep, Marketing Manager, Read-Only User
- Permissions: Create, Read, Update, Delete, Export for each entity type (Lead, Contact, Account, Deal, Activity, Campaign, etc.)
- Object-level permissions: "View All" (all records), "View Team" (records owned by user or team members), "View Own" (records owned by user only)
- Field-level permissions: read-only or hidden for sensitive fields (e.g., Deal.amount hidden from Marketing Manager)
- Permission checks enforced at API layer and UI layer
- Permission denial returns HTTP 403 with explanation

**Related Use Cases:** All  
**Related NFRs:** NFR-007 (security), NFR-001 (multi-tenancy)

---

#### FR-028 — Audit Logging

**Priority:** P0 (Must Have)  
**Description:** The system MUST log all create, update, delete, and export operations on core entities to an immutable audit log.

**Acceptance Criteria:**
- Audit log fields: event_type, entity_type, entity_id, user_id, timestamp, ip_address, user_agent, old_values (JSON), new_values (JSON)
- Audit log entries are append-only (no updates or deletes)
- Audit log is queryable via UI (Admin only) and API
- Audit log retention: minimum 1 year, configurable up to 7 years
- Audit log export to CSV or JSON for compliance audits

**Related Use Cases:** All  
**Related NFRs:** NFR-012 (compliance), NFR-007 (security)

---

#### FR-029 — GDPR Data Erasure

**Priority:** P0 (Must Have)  
**Description:** The system MUST provide a "Right to be Forgotten" workflow that permanently deletes all personal data for a Contact upon request.

**Acceptance Criteria:**
- Erasure request initiated by Admin user via UI or API
- Erasure request creates ErasureRequest record with status "Pending", "In Progress", "Completed", "Failed"
- Erasure deletes: Contact record, related Activities, email history, Campaign interactions
- Erasure anonymizes: Audit log entries (replace name/email with "REDACTED"), Deal history (retain deal amount but remove contact association)
- Erasure completion triggers email confirmation to requester
- Erasure cannot be undone (irreversible)

**Compliance:** GDPR Article 17 (Right to Erasure)

**Related Use Cases:** UC-014  
**Related NFRs:** NFR-012 (compliance)

---

#### FR-030 — Data Export (for portability)

**Priority:** P1 (Should Have)  
**Description:** The system MUST allow users to export their CRM data (Leads, Contacts, Accounts, Deals, Activities) in CSV or JSON format.

**Acceptance Criteria:**
- Export UI allows user to select entity type, fields to include, and date range filter
- Export creates background job with progress tracking
- Export file is downloadable from UI or sent via email link (expires in 7 days)
- Export includes all accessible records based on user's role permissions
- Export file format: CSV (flat), JSON (nested relationships), or Excel (multi-sheet)

**Compliance:** GDPR Article 20 (Right to Data Portability)

**Related Use Cases:** UC-015  
**Related NFRs:** NFR-012 (compliance), NFR-003 (scalability)

---

## 3. Non-Functional Requirements

### NFR-001 — Multi-Tenancy and Data Isolation

**Priority:** P0 (Must Have)  
**Description:** The system MUST enforce strict tenant isolation. No API request or database query may access or return data belonging to a different tenant.

**Acceptance Criteria:**
- All database tables include tenant_id column (UUID, indexed)
- All database queries include WHERE tenant_id = :current_tenant_id
- Tenant context is derived from authenticated user's session
- Cross-tenant access attempts are logged as security events

**Validation:** Penetration testing with multi-tenant scenarios

---

### NFR-002 — Performance and Latency

**Priority:** P0 (Must Have)  
**Description:** The system MUST meet the following performance targets under normal load:

| Operation | Target Latency (p95) | Target Latency (p99) |
|---|---|---|
| API read request (single record) | < 200 ms | < 500 ms |
| API write request (single record) | < 500 ms | < 1 s |
| List view page load (50 records) | < 1 s | < 2 s |
| Detail page load (360° view) | < 2 s | < 4 s |
| Search query (full-text) | < 1 s | < 2 s |

**Acceptance Criteria:**
- Performance is measured in production-like environment with representative data volume (1M Contacts, 500K Deals)
- Performance is measured under load (100 concurrent users per tenant)

---

### NFR-003 — Scalability

**Priority:** P1 (Should Have)  
**Description:** The system MUST support the following scale targets:

| Metric | Target |
|---|---|
| Tenants | 10,000+ |
| Users per tenant | 1,000+ |
| Contacts per tenant | 10M+ |
| Deals per tenant | 5M+ |
| Activities per tenant | 50M+ |
| API requests per second (global) | 10,000+ |

**Acceptance Criteria:**
- Horizontal scaling: system can scale by adding compute and database nodes
- Database partitioning by tenant_id for large tenants (> 1M contacts)
- Caching layer (Redis) for frequently accessed data (user sessions, lookup tables)

---

### NFR-004 — Configurability

**Priority:** P1 (Should Have)  
**Description:** The system MUST support tenant-level configuration for: custom fields, pipelines, stages, assignment rules, lead scoring rules, territory rules, email templates, and workflow automations.

**Acceptance Criteria:**
- Configuration changes take effect immediately (no application restart required)
- Configuration changes are versioned (audit trail of config changes)
- Configuration can be exported and imported (for migration or backup)

---

### NFR-005 — Availability and Uptime

**Priority:** P0 (Must Have)  
**Description:** The system MUST achieve 99.9% uptime (monthly basis), measured as (total minutes - downtime minutes) / total minutes.

**Acceptance Criteria:**
- Scheduled maintenance windows are excluded from uptime calculation
- Unplanned downtime is minimized via redundancy and automated failover
- System status page publicly displays uptime and incident history

---

### NFR-006 — Disaster Recovery

**Priority:** P0 (Must Have)  
**Description:** The system MUST support disaster recovery with the following targets:

| Metric | Target |
|---|---|
| Recovery Time Objective (RTO) | < 4 hours |
| Recovery Point Objective (RPO) | < 1 hour |

**Acceptance Criteria:**
- Automated daily backups of database and file storage
- Backups are stored in geographically separate region
- Restore procedure is documented and tested quarterly
- Database uses continuous replication to standby instance

---

### NFR-007 — Security

**Priority:** P0 (Must Have)  
**Description:** The system MUST implement industry-standard security controls:

- Data in transit: TLS 1.3 encryption for all HTTP traffic
- Data at rest: AES-256 encryption for database and file storage
- Authentication: OAuth 2.0 with multi-factor authentication (MFA) support
- Password policy: minimum 12 characters, complexity requirements, bcrypt hashing (cost factor 12)
- API rate limiting: 100 requests per minute per user, 1000 requests per minute per tenant
- SQL injection prevention: parameterized queries only
- XSS prevention: output encoding, Content Security Policy headers
- CSRF prevention: CSRF tokens for state-changing requests

**Validation:** Annual third-party security audit

---

### NFR-008 — Observability

**Priority:** P1 (Should Have)  
**Description:** The system MUST provide comprehensive observability through logs, metrics, and traces.

**Acceptance Criteria:**
- Structured JSON logs (correlation ID, timestamp, severity, service name, user ID, tenant ID)
- Metrics: request rate, error rate, latency percentiles (p50, p95, p99), database query duration, queue depth
- Distributed tracing: OpenTelemetry-compatible trace spans for all API requests
- Dashboards: service health, API performance, database performance, queue health, error rate trends
- Alerting: automated alerts for error rate > 1%, latency p99 > 5s, queue depth > 10000

---

### NFR-009 — Integration Compatibility

**Priority:** P1 (Should Have)  
**Description:** The system MUST integrate with:

- Email providers: Gmail (via Gmail API), Outlook (via Microsoft Graph API)
- Calendar providers: Google Calendar, Outlook Calendar
- Identity providers: Okta, Auth0, Azure AD (via SAML 2.0 or OIDC)
- Communication tools: Slack, Microsoft Teams (via webhooks and bot APIs)
- Data warehouses: Snowflake, BigQuery, Redshift (via data export connectors)

**Acceptance Criteria:**
- Integration setup requires minimal configuration (OAuth flow, API keys)
- Integration errors are user-visible with actionable error messages

---

### NFR-010 — Reliability and Error Handling

**Priority:** P0 (Must Have)  
**Description:** The system MUST handle transient errors gracefully with retries and circuit breakers.

**Acceptance Criteria:**
- API client errors (4xx) are not retried
- API server errors (5xx) and network errors are retried up to 3 times with exponential backoff
- External API calls use circuit breaker pattern (open circuit after 5 consecutive failures, half-open after 60s)
- Failed background jobs are retried up to 5 times before moving to dead-letter queue
- User-visible errors include correlation ID for support troubleshooting

---

### NFR-011 — Data Accuracy and Consistency

**Priority:** P0 (Must Have)  
**Description:** The system MUST maintain data accuracy and consistency across all operations.

**Acceptance Criteria:**
- Database transactions use SERIALIZABLE isolation level for financial calculations (forecast rollups, deal amount summations)
- Optimistic locking for concurrent updates (version field on all mutable entities)
- Idempotency keys for write operations to prevent duplicate submissions
- Data validation at API layer, service layer, and database layer (constraints)

---

### NFR-012 — Compliance (GDPR, CAN-SPAM, SOC 2)

**Priority:** P0 (Must Have)  
**Description:** The system MUST comply with GDPR (data protection), CAN-SPAM (email marketing), and SOC 2 Type II (security and availability) standards.

**Acceptance Criteria:**
- GDPR: data processing agreement, data erasure workflow (FR-029), data portability (FR-030), consent management, breach notification procedure
- CAN-SPAM: unsubscribe link in all marketing emails, unsubscribe honored within 10 days, physical address in email footer
- SOC 2 Type II: annual audit, access controls, encryption, incident response plan, change management process

**Validation:** Annual compliance audits by certified third parties

---

### NFR-013 — Internationalization (i18n)

**Priority:** P2 (Nice to Have)  
**Description:** The system SHOULD support multiple languages and locales in the UI.

**Acceptance Criteria:**
- UI text is externalized in language files (English, Spanish, French, German)
- User can select preferred language in settings
- Date, time, number, and currency formats respect user's locale
- Right-to-left (RTL) language support (Arabic, Hebrew)

---

### NFR-014 — Accessibility (WCAG 2.1 Level AA)

**Priority:** P1 (Should Have)  
**Description:** The system SHOULD comply with WCAG 2.1 Level AA accessibility standards.

**Acceptance Criteria:**
- All interactive elements are keyboard navigable
- Color contrast ratio meets minimum 4.5:1 for text
- Images include alt text
- Form fields include labels and ARIA attributes
- Screen reader compatible

**Validation:** Automated accessibility testing (axe-core) and manual testing with screen reader

---

### NFR-015 — Documentation

**Priority:** P1 (Should Have)  
**Description:** The system MUST include comprehensive documentation for developers, administrators, and end users.

**Acceptance Criteria:**
- API documentation: OpenAPI 3.0 specification with request/response examples
- Admin documentation: setup guide, configuration guide, troubleshooting guide
- User documentation: feature guides, video tutorials, FAQ
- Developer documentation: architecture overview, code conventions, deployment guide, runbook

---

## 4. Traceability Matrix

| Requirement ID | Requirement Name | Related Use Cases | Related User Stories | Priority |
|---|---|---|---|---|
| FR-001 | Lead Capture via Web Form | UC-001 | US-001, US-002 | P0 |
| FR-002 | Lead Capture via REST API | UC-001 | US-003 | P0 |
| FR-003 | Lead Bulk Import via CSV | UC-001 | US-004 | P1 |
| FR-004 | Lead Scoring Engine | UC-002 | US-005, US-006 | P1 |
| FR-005 | Lead Assignment Rules | UC-002 | US-007 | P0 |
| FR-006 | Lead Conversion to Contact and Opportunity | UC-003 | US-008, US-009 | P0 |
| FR-007 | Contact CRUD Operations | UC-004 | US-010, US-011 | P0 |
| FR-008 | Account CRUD Operations | UC-004 | US-012 | P0 |
| FR-009 | Contact and Account 360° View | UC-005 | US-013 | P1 |
| FR-010 | Pipeline Configuration | UC-006 | US-014 | P0 |
| FR-011 | Deal Creation and Management | UC-006 | US-015, US-016 | P0 |
| FR-012 | Deal Stage Progression | UC-006 | US-017 | P0 |
| FR-013 | Deal Forecasting | UC-007 | US-018, US-019 | P1 |
| FR-014 | Activity Logging | UC-005 | US-020, US-021 | P0 |
| FR-015 | Email Sync | UC-005 | US-022 | P1 |
| FR-016 | Calendar Sync | UC-005 | US-023 | P1 |
| FR-017 | Email Campaign Creation | UC-008 | US-024, US-25 | P1 |
| FR-018 | Campaign Segment Builder | UC-008 | US-026 | P1 |
| FR-019 | Campaign Email Tracking | UC-008 | US-027 | P1 |
| FR-020 | Territory Hierarchy and Assignment | UC-009 | US-028, US-029 | P1 |
| FR-021 | Revenue Forecast Rollup | UC-007 | US-030 | P1 |
| FR-022 | Custom Field Definition | UC-010 | US-031, US-032 | P1 |
| FR-023 | Duplicate Detection and Merge | UC-011 | US-033, US-034 | P1 |
| FR-024 | REST API with OAuth 2.0 | All | US-035 | P0 |
| FR-025 | Webhook Subscriptions | UC-012 | US-036 | P1 |
| FR-026 | Data Import with Field Mapping | UC-013 | US-037 | P1 |
| FR-027 | Role-Based Access Control | All | US-038, US-39 | P0 |
| FR-028 | Audit Logging | All | US-040 | P0 |
| FR-029 | GDPR Data Erasure | UC-014 | US-041 | P0 |
| FR-030 | Data Export | UC-015 | US-042 | P1 |

---

**Total Functional Requirements:** 30  
**Total Non-Functional Requirements:** 15  
**Total Requirements:** 45

---

*This document is maintained by the Product Management team. All requirement changes must be reviewed and approved by stakeholders before implementation.*
