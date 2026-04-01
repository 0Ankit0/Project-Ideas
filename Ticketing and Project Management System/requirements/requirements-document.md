# Requirements Document — Ticketing and Project Management System

| Field       | Value                              |
|-------------|-------------------------------------|
| Version     | 2.1.0                               |
| Status      | Approved                            |
| Date        | 2025-07-14                          |
| Authors     | Platform Engineering, Product Team  |
| Reviewers   | CTO, Head of Engineering, QA Lead   |
| Document ID | REQ-TPMS-001                        |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Functional Requirements](#2-functional-requirements)
   - 2.1 Ticket Management (FR-001 – FR-012)
   - 2.2 Sprint and Board Management (FR-013 – FR-022)
   - 2.3 SLA Management (FR-023 – FR-030)
   - 2.4 Comments and Attachments (FR-031 – FR-036)
   - 2.5 Integrations (FR-037 – FR-044)
   - 2.6 Reporting and Analytics (FR-045 – FR-050)
3. [Non-Functional Requirements](#3-non-functional-requirements)
4. [Constraints and Assumptions](#4-constraints-and-assumptions)
5. [Acceptance Criteria Summary](#5-acceptance-criteria-summary)

---

## 1. Introduction

### 1.1 Purpose

This document specifies all functional and non-functional requirements for the **Ticketing and Project Management System (TPMS)**. It serves as the authoritative reference for engineering, QA, product, and stakeholder teams throughout the full development lifecycle. All acceptance testing shall be measured against requirements listed herein.

### 1.2 Scope

TPMS is a multi-tenant, cloud-native project management platform that supports agile software development workflows. The system provides:

- Hierarchical ticket management (Epic → Story → Task → SubTask) with full workflow state machine enforcement
- Scrum and Kanban board management with sprint planning, velocity tracking, and burndown visualization
- Configurable SLA policies with automated escalation cascades
- Real-time collaboration via comments, @mentions, and file attachments
- Deep integrations with GitHub, GitLab, Slack, CI/CD pipelines, and SSO providers
- Portfolio-level roadmaps, reporting dashboards, and custom analytics

The system is explicitly **out of scope** for: billing and invoicing, HR management, customer ticketing (helpdesk), and hardware asset tracking.

### 1.3 Stakeholders

| Stakeholder             | Role                                       | Interest                                                      |
|-------------------------|--------------------------------------------|---------------------------------------------------------------|
| Development Teams       | Primary users                              | Create/manage tickets, collaborate, track work                |
| Project Managers        | Planners and reporters                     | Sprint planning, velocity tracking, SLA compliance            |
| Engineering Leads       | Workflow and board owners                  | Workflow configuration, team capacity, code integration       |
| Product Owners          | Roadmap and backlog owners                 | Backlog grooming, epic/story management, roadmap views        |
| Admin Users             | System configurators                       | User management, roles, webhooks, field configuration         |
| Clients / Reporters     | External ticket submitters                 | Submit and track bugs/requests                                |
| Security and Compliance | Audit and data governance                  | SOC 2 audit logs, GDPR controls, encryption compliance        |
| DevOps / SRE            | Platform operators                         | Availability, scaling, alerting, backup/recovery              |

### 1.4 Definitions

| Term                    | Definition                                                                                         |
|-------------------------|----------------------------------------------------------------------------------------------------|
| Ticket                  | A unit of work; may be a Bug, Story, Task, Epic, or SubTask                                        |
| Sprint                  | A time-boxed iteration (1–4 weeks) within a Scrum board                                            |
| SLA Policy              | A time-bound service agreement specifying response and resolution windows per priority              |
| Workflow                | A directed graph of states and transitions governing ticket progression                            |
| Epic                    | A large body of work decomposed into Stories and Tasks                                             |
| Story Points            | Abstract unit of effort estimation using the Fibonacci scale (1,2,3,5,8,13,21)                    |
| WIP Limit               | Maximum number of tickets allowed in a Kanban column simultaneously                               |
| Velocity                | Sum of story points completed during a sprint                                                      |
| SLA Breach              | Event when ticket resolution time exceeds the defined SLA window                                   |
| Workspace               | Top-level tenant boundary; contains projects, users, and billing configuration                     |

---

## 2. Functional Requirements

### 2.1 Ticket Management

#### FR-001 — Ticket Type Support
**Priority:** Must Have | **Module:** Ticket Management

The system shall support the following ticket types, each with distinct fields, icons, and workflow templates:

| Type    | Description                                    | Default Workflow Template       |
|---------|------------------------------------------------|---------------------------------|
| Bug     | A defect or unexpected system behaviour        | Bug Lifecycle Workflow          |
| Story   | A user-facing feature request                  | Story Lifecycle Workflow        |
| Task    | A generic unit of technical or operational work| Standard Task Workflow          |
| Epic    | A high-level feature grouping multiple stories | Epic Lifecycle Workflow         |
| SubTask | A decomposed unit of a parent story or task    | Inherits parent's workflow      |

#### FR-002 — Mandatory Fields by Ticket Type
**Priority:** Must Have | **Module:** Ticket Management

Each ticket type shall enforce the following mandatory fields. Submission with missing mandatory fields shall return HTTP 422 with a field-level error map.

| Ticket Type | Mandatory Fields                                                                 |
|-------------|----------------------------------------------------------------------------------|
| Bug         | title, description, steps_to_reproduce, severity, environment, affected_version  |
| Story       | title, description, acceptance_criteria, story_points                            |
| Task        | title, description, assignee                                                     |
| Epic        | title, description, business_objective, target_quarter                           |
| SubTask     | title, parent_ticket_id, assignee                                                |

#### FR-003 — Priority Levels
**Priority:** Must Have | **Module:** Ticket Management

Tickets shall support four priority levels with configurable SLA mappings:

- **Critical** — System down; immediate response required
- **High** — Major functionality impaired; response within 4 hours
- **Medium** — Partial degradation; response within 1 business day
- **Low** — Minor issue; response within 3 business days

Priority shall be configurable per workspace and may be overridden by SLA policy definitions.

#### FR-004 — Workflow State Machine
**Priority:** Must Have | **Module:** Ticket Management

Ticket status transitions shall be governed by a configurable, directed acyclic graph (DAG). Each project shall define its own workflow. The system shall:

- Reject any transition not defined in the active workflow for the ticket's type (BR-01)
- Support global default workflows per ticket type
- Log each transition with actor, timestamp, previous state, and new state in the immutable audit log
- Enforce role-based transition guards (e.g., only Team Lead may transition to "Approved")

#### FR-005 — Bulk Ticket Operations
**Priority:** Should Have | **Module:** Ticket Management

The system shall support bulk operations on up to 500 tickets per request:

| Operation        | Description                                             |
|------------------|---------------------------------------------------------|
| Bulk Assign      | Reassign selected tickets to a specified user           |
| Bulk Label       | Add or remove labels from selected tickets              |
| Bulk Transition  | Move selected tickets to a specified status             |
| Bulk Delete      | Archive selected tickets (Admin only)                   |
| Bulk Priority    | Update priority on selected tickets                     |

All bulk operations shall produce an audit log entry per ticket and return a partial success report if any ticket in the batch fails validation.

#### FR-006 — Custom Fields
**Priority:** Should Have | **Module:** Ticket Management

Projects shall support custom fields of the following types:

| Field Type    | Validation Rules                                   |
|---------------|----------------------------------------------------|
| Text          | Max 500 characters                                 |
| Number        | Configurable min/max bounds                        |
| Date          | ISO 8601 format; configurable past/future limits   |
| Dropdown      | Admin-managed option list; max 100 options         |
| Multi-select  | Admin-managed option list; max 50 values per ticket|
| URL           | RFC 3986 validation                                |
| User          | Must reference active workspace member             |

Custom fields shall be searchable and filterable via the API and UI. Field definitions shall be project-scoped. Cross-project field templates shall be configurable at workspace level.

#### FR-007 — Story Point Estimation
**Priority:** Must Have | **Module:** Ticket Management

Story points shall be restricted to the Fibonacci scale: **1, 2, 3, 5, 8, 13, 21**. The system shall:

- Reject story point values not in the approved set via API validation
- Display a selection widget in the UI (not a freeform input)
- Sum story points at Epic and Sprint levels for capacity and velocity calculations
- Allow "unpointed" state (null) for newly created tickets

#### FR-008 — Parent-Child Ticket Hierarchy
**Priority:** Must Have | **Module:** Ticket Management

Tickets shall support the following hierarchy:

```
Roadmap
  └─ Epic
       └─ Story / Task
            └─ SubTask
```

Rules:
- An Epic may contain unlimited Stories and Tasks
- A Story or Task may contain up to 20 SubTasks
- SubTasks cannot have child tickets
- Closing an Epic is blocked until all child Stories and Tasks are in a terminal state (BR-09)
- Deleting a parent ticket requires confirmation and cascades to all children

#### FR-009 — Audit History
**Priority:** Must Have | **Module:** Ticket Management

The system shall maintain a full, immutable audit trail for all ticket mutations, capturing:

- Changed field name, old value, and new value
- Actor user ID, IP address, and user-agent
- Timestamp (UTC, microsecond precision)
- Source (UI, API, automation, webhook)

Audit records shall be retained per NFR-008 and shall not be editable or deletable by any user role.

#### FR-010 — @Mention Notifications
**Priority:** Must Have | **Module:** Ticket Management

The system shall detect `@username` tokens in ticket descriptions, comments, and acceptance criteria. On save:

- Validate each mention against active workspace members
- Queue an in-app and email notification per mentioned user
- Surface unread @mention count in the navigation UI
- Support `@team-name` to fan-out to all team members

#### FR-011 — Duplicate Ticket Detection
**Priority:** Should Have | **Module:** Ticket Management

On ticket creation, the system shall perform fuzzy-match detection against open tickets in the same project:

- Compute TF-IDF similarity on title and description
- Surface top 3 potential duplicates (similarity score ≥ 0.75) before submission
- Allow user to link as duplicate or proceed with creation
- Duplicate links shall be bidirectional and reflected in both ticket views

#### FR-012 — Import from CSV and Jira
**Priority:** Should Have | **Module:** Ticket Management

The system shall support bulk import of tickets from:

- **CSV**: Configurable column mapping UI; validation report before commit; max 10,000 rows per import job
- **Jira XML Export**: Full fidelity import of issues, comments, attachments, sprints, and custom fields via the Jira backup XML format

Import jobs shall run asynchronously and provide progress tracking and a final import report (success count, failure count, failure reasons).

---

### 2.2 Sprint and Board Management

#### FR-013 — Scrum Board with Sprints
**Priority:** Must Have | **Module:** Sprint Management

The system shall provide Scrum boards with the following capabilities:

- Create, name, set start/end dates and story point capacity for sprints
- Active sprint view showing ticket cards in workflow columns
- Sprint header displaying: goal, capacity (used/total), days remaining
- One active sprint per board at a time (concurrent sprints on separate boards allowed per FR-021)

#### FR-014 — Kanban Board with WIP Limits
**Priority:** Must Have | **Module:** Board Management

Kanban boards shall:

- Display workflow states as columns
- Enforce configurable WIP limits per column (reject drag-drop that would exceed limit with a visual warning)
- Support cumulative flow diagram view
- Not require sprints; tickets flow continuously through columns

#### FR-015 — Sprint Capacity Enforcement
**Priority:** Must Have | **Module:** Sprint Management

When adding tickets to a sprint:

- Display current total story points vs. sprint capacity
- Warn (yellow) when > 80% capacity reached
- Hard-block (red) addition when capacity would be exceeded, unless Lead or Admin overrides
- Sprint capacity shall default to team velocity average (configurable override)

#### FR-016 — Velocity Tracking
**Priority:** Must Have | **Module:** Sprint Management

The system shall calculate and persist sprint velocity:

- Velocity = sum of story points on tickets in "Done" state at sprint close
- Display velocity trend chart across last 10 sprints
- Calculate rolling average velocity used for capacity suggestions
- Export velocity data in CSV and JSON formats

#### FR-017 — Backlog Prioritization
**Priority:** Must Have | **Module:** Sprint Management

The backlog view shall support:

- Drag-and-drop reordering with optimistic UI updates
- Keyboard-accessible reordering (Alt+Up/Down)
- Bulk move to sprint with capacity preview
- Grouping by Epic, Priority, or Label
- Filter by assignee, label, type, and sprint

#### FR-018 — Real-Time Burndown Charts
**Priority:** Must Have | **Module:** Sprint Management

Burndown charts shall:

- Update within 5 seconds of ticket story point changes or status transitions
- Display ideal burndown line, actual burndown line, and scope change markers
- Show scope creep events (tickets added after sprint start) as markers
- Be printable/exportable as PNG and PDF

#### FR-019 — Sprint Retrospective Notes
**Priority:** Should Have | **Module:** Sprint Management

Each sprint shall support a structured retrospective document with:

- "Went Well", "Improvement Areas", "Action Items" sections
- Action items linkable to tickets
- Retrospective locked after 30 days post-sprint-close
- Viewable by all team members; editable by Lead and Admin

#### FR-020 — Incomplete Sprint Ticket Handling
**Priority:** Must Have | **Module:** Sprint Management

When closing a sprint, the system shall:

- Identify all tickets not in a terminal state
- Present a modal to move uncompleted tickets to: (a) next active sprint, (b) a new sprint, or (c) backlog
- Require Lead or Admin to confirm sprint close
- Record a sprint close audit event with the disposition of each uncompleted ticket

#### FR-021 — Parallel Sprints
**Priority:** Should Have | **Module:** Sprint Management

The system shall support multiple simultaneous active sprints across separate boards within the same project. Each board maintains its own sprint lifecycle, capacity, and velocity independently.

#### FR-022 — Sprint Goals and Objectives
**Priority:** Should Have | **Module:** Sprint Management

Sprints shall have a `sprint_goal` text field (max 500 characters) that:

- Is displayed prominently on the board header
- Is required before sprint start (configurable per project)
- Is included in sprint summary reports and retrospective documents

---

### 2.3 SLA Management

#### FR-023 — Configurable SLA Policies
**Priority:** Must Have | **Module:** SLA Management

Admins shall define SLA policies per project per priority:

| Policy Field         | Description                                                  |
|----------------------|--------------------------------------------------------------|
| response_time        | Time to first response (in business hours)                   |
| resolution_time      | Time to resolution (in business hours)                       |
| business_hours_calendar | Reference to workspace business hours schedule           |
| escalation_contacts  | L1, L2, L3 escalation users/groups                          |
| pause_on_statuses    | List of statuses that pause the SLA clock                    |

#### FR-024 — SLA Clock Pause and Resume
**Priority:** Must Have | **Module:** SLA Management

The SLA clock shall:

- Pause automatically when a ticket transitions to any status listed in the policy's `pause_on_statuses` (default: "On Hold", "Waiting for Customer")
- Resume automatically on the next ticket update (comment, status change) after pausing (BR-02)
- Record each pause/resume event with timestamp and duration in the SLA event log

#### FR-025 — SLA Warning Notifications
**Priority:** Must Have | **Module:** SLA Management

The system shall:

- Calculate remaining SLA time continuously via background worker
- Trigger L1 warning notification at 80% SLA time elapsed (BR-07)
- Deliver warnings via: in-app notification, email, and configured Slack channel

#### FR-026 — SLA Breach Escalation Cascade
**Priority:** Must Have | **Module:** SLA Management

On SLA breach (100% elapsed):

- **L1**: Notify assignee and direct manager with urgency flag
- **L2**: Notify L2 contacts (Team Lead, Engineering Manager) at 100% + 15 min if unresolved
- **L3**: Notify L3 contacts (VP Engineering, Account Manager) at 100% + 60 min if still unresolved
- Each escalation shall be logged in the SLA breach record with timestamp and actor

#### FR-027 — SLA Metrics Dashboards
**Priority:** Must Have | **Module:** SLA Management

Dashboards shall display:

- SLA compliance rate (%) per project, priority, and assignee
- Current open tickets at risk (> 80% elapsed)
- Current open tickets in breach (> 100% elapsed)
- Mean time to resolution (MTTR) by priority
- Average SLA elapsed percentage at resolution

#### FR-028 — SLA Timezone Configuration
**Priority:** Must Have | **Module:** SLA Management

SLA calculations shall respect workspace-level timezone settings. Business hours calendars shall support:

- Configurable working days (e.g., Mon–Fri)
- Configurable working hours per day (e.g., 09:00–17:00)
- Public holidays calendar with manual and iCal import
- Timezone specified in IANA format (e.g., `America/New_York`)

#### FR-029 — Business Hours Calendar
**Priority:** Must Have | **Module:** SLA Management

Each SLA policy shall reference a business hours calendar. Time elapsed outside business hours shall not count toward SLA consumption. Multiple calendars shall be supported per workspace for global teams.

#### FR-030 — SLA Breach History for Compliance
**Priority:** Must Have | **Module:** SLA Management

SLA breach records shall be:

- Immutable once written
- Queryable by: project, priority, assignee, date range, breach severity
- Exportable in CSV and JSON
- Retained per the data retention policy (NFR-005)

---

### 2.4 Comments and Attachments

#### FR-031 — Rich Text Comments
**Priority:** Must Have | **Module:** Collaboration

Comments shall support a Markdown-based rich text editor with:

- Bold, italic, strikethrough, inline code, code blocks (with syntax highlighting)
- Ordered and unordered lists, blockquotes, tables
- Image inline embedding (references uploaded attachments)
- Preview mode before submission

#### FR-032 — Virus Scanning of Attachments
**Priority:** Must Have | **Module:** Collaboration

All uploaded files shall be asynchronously scanned using a ClamAV-compatible virus scanner before being made available for download. Files in "pending scan" state shall display a scanning indicator. Infected files shall be quarantined and the uploader notified.

#### FR-033 — Attachment Size Limits
**Priority:** Must Have | **Module:** Collaboration

Attachment constraints (BR-10):

| Limit           | Value    |
|-----------------|----------|
| Per-file limit  | 10 MB    |
| Per-ticket limit| 100 MB   |

Uploads exceeding these limits shall be rejected at the API boundary with HTTP 413 and a descriptive error message. Rejected uploads shall not consume storage quota.

#### FR-034 — @Mention Notifications in Comments
**Priority:** Must Have | **Module:** Collaboration

Comment @mentions shall:

- Auto-complete username from workspace member directory as user types
- Notify mentioned users via in-app, email, and Slack (if configured)
- Render as hyperlinks to the user's profile in the comment body
- Respect user notification preference settings

#### FR-035 — Comment Edit History
**Priority:** Should Have | **Module:** Collaboration

All comment edits shall be versioned. Edited comments shall display an "edited" indicator with the last-edited timestamp. Any workspace member may view the full edit history. Edit history shall be immutable.

#### FR-036 — Comment Deletion Rules
**Priority:** Must Have | **Module:** Collaboration

Comment deletion shall be permitted only:

- By the comment author within 15 minutes of creation (BR-11)
- By Admin at any time

Deleted comments shall be soft-deleted; content replaced with "[deleted]" but thread structure preserved. Deletion is recorded in the audit log.

---

### 2.5 Integrations

#### FR-037 — GitHub/GitLab Integration
**Priority:** Must Have | **Module:** Integrations

The system shall:

- Parse commit messages and PR titles for ticket references (e.g., `PROJ-123`)
- Display linked PRs, commits, and branches on the ticket detail page
- Update ticket status on PR merge (configurable automation rule)
- Support GitHub App and GitLab OAuth installation flows

#### FR-038 — Slack Notifications
**Priority:** Must Have | **Module:** Integrations

Slack integration shall:

- Post to configured channels on: ticket creation, assignment, status transition, @mention, SLA warning/breach
- Support per-project channel mapping
- Include deep-link back to the ticket in the TPMS UI
- Respect notification throttling (max 1 message per ticket per 5 minutes for status changes)

#### FR-039 — CI/CD Pipeline Status
**Priority:** Should Have | **Module:** Integrations

Tickets shall display CI/CD pipeline status for linked branches/PRs:

- Fetch build status from GitHub Actions, Jenkins, GitLab CI via webhook events
- Display statuses: pending, running, passed, failed, cancelled
- Link to full pipeline run logs in the external system

#### FR-040 — SSO via SAML 2.0 and OIDC
**Priority:** Must Have | **Module:** Security

The system shall:

- Support SP-initiated and IdP-initiated SAML 2.0 flows
- Support OIDC Authorization Code Flow with PKCE
- Map IdP group claims to TPMS roles (configurable attribute mapping)
- Support Just-in-Time (JIT) provisioning of new users from IdP
- Enforce SCIM 2.0 for user lifecycle management (create, update, deactivate)

#### FR-041 — Outbound Webhooks
**Priority:** Must Have | **Module:** Integrations

The system shall deliver webhook payloads for the following events:

- Ticket created, updated, deleted, transitioned
- Comment added, edited, deleted
- Sprint started, closed
- SLA warning triggered, SLA breach occurred
- Attachment uploaded

Webhooks shall: use HMAC-SHA256 request signing, retry up to 5 times with exponential backoff (BR-12), log each delivery attempt and response code, and provide a UI for replay of failed deliveries.

#### FR-042 — Jira Migration
**Priority:** Should Have | **Module:** Integrations

The system shall import from Jira backup XML with:

- Issue types mapped to TPMS ticket types
- Custom field definitions recreated as TPMS custom fields
- Sprints, boards, and backlogs recreated
- User accounts matched by email; unmatched users mapped to a "Migrated User" placeholder
- Attachments downloaded from Jira and re-uploaded to TPMS storage
- Full migration report with per-issue success/failure detail

#### FR-043 — Email-to-Ticket
**Priority:** Should Have | **Module:** Integrations

Each project shall have a configurable inbound email address. Inbound emails shall:

- Create a ticket of configurable type (default: Bug)
- Map email subject to ticket title, email body to description
- Attach email attachments as ticket attachments (subject to FR-033 limits)
- Set reporter to matched workspace user or create a guest reporter record
- Spam-filtered using configurable keyword blocklist

#### FR-044 — Time Tracking Integrations
**Priority:** Nice to Have | **Module:** Integrations

The system shall integrate with Toggl and Harvest via OAuth 2.0:

- Allow users to start/stop timers from the TPMS ticket UI
- Sync time entries to TPMS time log
- Tag time entries with ticket ID in the external tool

---

### 2.6 Reporting and Analytics

#### FR-045 — Velocity Charts
**Priority:** Must Have | **Module:** Reporting

Velocity charts shall display:

- Bar chart: story points committed vs. completed per sprint
- Line overlay: rolling 3-sprint average velocity
- Scope creep indicator: points added after sprint start
- Filterable by team and assignee

#### FR-046 — Burndown and Burnup Charts
**Priority:** Must Have | **Module:** Reporting

Per sprint:

- **Burndown**: Remaining story points over calendar days with ideal line
- **Burnup**: Completed story points vs. total scope over calendar days
- Scope change events annotated on chart timeline
- Data refresh every 60 seconds during active sprint

#### FR-047 — SLA Compliance Reports
**Priority:** Must Have | **Module:** Reporting

Reports shall include:

- SLA compliance rate by project, priority, assignee, and date range
- Breach count and MTTR breakdown
- Trend view (week-over-week, month-over-month)
- Exportable in PDF, CSV, and Excel formats

#### FR-048 — Time Tracking Reports
**Priority:** Should Have | **Module:** Reporting

Time tracking reports shall support:

- Total time logged per ticket, sprint, epic, and project
- Billable vs. non-billable hours split
- Time logged by user
- Export in CSV, Excel, and integration formats (Toggl/Harvest)

#### FR-049 — Custom Dashboard Builder
**Priority:** Should Have | **Module:** Reporting

The dashboard builder shall support:

- Drag-and-drop widget layout (grid-based)
- Widget types: ticket count, velocity chart, burndown chart, SLA gauge, activity feed, custom query table
- Per-user and shared team dashboards
- Dashboard export as PDF snapshot

#### FR-050 — Roadmap View
**Priority:** Must Have | **Module:** Reporting

The roadmap shall display:

- Horizontal Gantt-style timeline for Epics and Milestones
- Configurable time scale: month, quarter, year
- Dependency arrows between Epics
- Colour-coded by status and team
- Snapshot export as PNG and PDF

---

## 3. Non-Functional Requirements

### Performance

#### NFR-001 — API Read Latency
The system shall serve API read endpoint responses with p99 latency < 300ms under a sustained load of 10,000 requests per minute per region. Latency shall be measured at the API gateway, excluding client network time.

#### NFR-002 — Concurrent User Capacity
The system shall support 50,000 concurrent authenticated WebSocket and HTTP sessions without degradation in response time. Load tests shall validate this at 110% capacity (55,000 sessions) with < 5% error rate.

#### NFR-003 — Full-Text Search Latency
Ticket search queries shall return results within 500ms at p95 under normal load (< 30,000 concurrent searches). Search is powered by Elasticsearch with per-workspace index sharding.

### Availability and Reliability

#### NFR-004 — System Availability
The system shall maintain 99.9% uptime (≤ 8.76 hours downtime per year), excluding pre-announced maintenance windows (max 4 hours/month). SLA shall be measured via synthetic monitoring from three geographic regions.

#### NFR-005 — Data Durability
PostgreSQL primary data shall have 99.999% durability via synchronous streaming replication to at least two standby replicas in different availability zones. Object storage (attachments) shall have 11-nines durability via S3-compatible storage.

### Security

#### NFR-006 — Encryption
- **In Transit**: TLS 1.3 minimum; TLS 1.2 permitted only for legacy integration agents; TLS 1.0/1.1 disabled
- **At Rest**: AES-256-GCM for database columns storing PII; S3 SSE-KMS for attachments; secrets stored in HashiCorp Vault

#### NFR-007 — GDPR Compliance
The system shall:
- Provide data export (all user data) within 72 hours of request
- Execute right-to-erasure within 30 days (with audit trail of erasure)
- Maintain data processing consent records with timestamped revisions
- Support data residency configuration per workspace (EU-only, US-only)

#### NFR-008 — Audit Log Requirements (SOC 2 Type II)
All state-mutating API calls shall generate immutable audit records in a dedicated append-only store. Audit logs shall be queryable by: user, resource type, action, and timestamp range. Retention: 3 years minimum.

### Scalability

#### NFR-009 — Horizontal Scaling
All stateless application services shall run as Kubernetes Deployments with Horizontal Pod Autoscaler (HPA) targeting 70% CPU utilization. Cluster autoscaler shall provision new nodes within 3 minutes of sustained demand.

#### NFR-010 — Database Backup and Recovery
- Automated full backups every 6 hours; incremental every 30 minutes
- Point-in-time recovery (PITR) granularity: 5 minutes
- Recovery tested monthly with RTO verification
- Backup storage encrypted and replicated to a separate region

### Integration and Performance

#### NFR-011 — Search Index Freshness
New and updated tickets shall appear in full-text search results within 10 seconds of the write operation (p95). Elasticsearch index consumer shall process Kafka events in near-real-time.

#### NFR-012 — Webhook Delivery Latency
Webhook deliveries shall complete within 5 seconds (p95) of the triggering event. Failed deliveries shall be retried per BR-12 without counting retries in the p95 measurement.

#### NFR-013 — File Upload Throughput
The system shall sustain aggregate file upload throughput of ≥ 50MB/s across all concurrent uploads. Upload pre-signed URLs shall be valid for 15 minutes.

### Access Control and Rate Limiting

#### NFR-014 — API Authentication and Rate Limiting
All API endpoints shall require authentication (API key or OAuth 2.0 Bearer token). Rate limiting: 1,000 requests/minute per workspace for standard tier; 5,000/minute for enterprise tier. Rate limit headers (X-RateLimit-*) shall be returned on every response.

#### NFR-015 — Multi-Region Failover
The system shall support active-passive multi-region failover with:
- **RTO**: < 15 minutes for full failover
- **RPO**: < 5 minutes (aligned with PITR granularity)
- Automated DNS failover via Route 53 health checks
- Failover drills performed quarterly with documented results

---

## 4. Constraints and Assumptions

### Technical Constraints

| ID   | Constraint                                                                                  |
|------|---------------------------------------------------------------------------------------------|
| C-01 | The system shall be deployed on AWS (primary) with multi-AZ configuration                  |
| C-02 | PostgreSQL 15+ shall be used as the primary relational database                             |
| C-03 | Elasticsearch 8+ shall be used for full-text search                                         |
| C-04 | All services shall be containerized (Docker) and orchestrated via Kubernetes                |
| C-05 | The REST API shall conform to OpenAPI 3.1 specification                                     |
| C-06 | Real-time updates shall use WebSockets (Socket.IO or raw WS) on ticket and board views      |
| C-07 | Frontend shall be a React 18+ single-page application                                       |
| C-08 | Mobile applications (iOS/Android) shall use the same REST API as the web client             |

### Business Constraints

| ID   | Constraint                                                                                         |
|------|----------------------------------------------------------------------------------------------------|
| C-09 | Closed tickets shall be archived after 90 days and retained for 3 years (BR-05)                   |
| C-10 | The system shall not store payment card data (PCI-DSS out of scope)                               |
| C-11 | Initial release shall support English only; i18n architecture required for future localisation     |
| C-12 | API versioning shall use URI path versioning (`/api/v1/`, `/api/v2/`)                             |

### Assumptions

| ID   | Assumption                                                                                       |
|------|--------------------------------------------------------------------------------------------------|
| A-01 | All users have modern browser support (Chrome 110+, Firefox 110+, Safari 16+, Edge 110+)        |
| A-02 | Enterprise customers manage their own SSO IdP configuration                                      |
| A-03 | Object storage (S3) is available with < 50ms latency for pre-signed URL generation              |
| A-04 | Email delivery SLA (via SendGrid/SES) is outside TPMS operational responsibility                 |
| A-05 | Virus scanning service maintains > 99.5% availability; scan failures default to quarantine       |
| A-06 | GitHub/GitLab webhook events will be delivered within 60 seconds of the triggering git event     |

---

## 5. Acceptance Criteria Summary

| Requirement | Acceptance Criteria Summary                                                                 | Test Type          |
|-------------|---------------------------------------------------------------------------------------------|--------------------|
| FR-001      | All 5 ticket types created, saved, and retrieved with type-specific fields populated        | Integration        |
| FR-002      | Submission without mandatory fields returns HTTP 422 with per-field error keys             | Integration        |
| FR-004      | Invalid status transition returns HTTP 409; valid transitions logged with full metadata     | Integration        |
| FR-007      | Story point values outside Fibonacci set rejected at API with HTTP 422                     | Unit + Integration |
| FR-015      | Adding ticket exceeding sprint capacity blocked for Member; overrideable by Lead           | Integration        |
| FR-024      | SLA elapsed time frozen during "On Hold"; resumes on next update with correct accumulation | Integration        |
| FR-026      | L1 notification fired at 80%; L2 at 100%; L3 at 100% + 60min with correct recipients      | E2E + Integration  |
| FR-032      | Uploaded EICAR test file quarantined and uploader notified within 60 seconds               | Integration        |
| FR-033      | 10.1MB file rejected HTTP 413; 11th file on 100MB-full ticket rejected HTTP 413            | Integration        |
| FR-036      | Author delete at 16min after creation blocked; Admin delete succeeds at any time           | Integration        |
| FR-041      | Webhook delivery retried 5x on 5xx responses; HMAC signature verifiable by consumer       | Integration        |
| NFR-001     | p99 read latency < 300ms at 10,000 req/min sustained (load test verified)                  | Performance        |
| NFR-002     | 55,000 concurrent sessions < 5% error rate (load test verified)                            | Performance        |
| NFR-006     | TLS 1.0/1.1 rejected; TLS 1.3 negotiated by default (verified via sslyze)                 | Security           |
| NFR-009     | HPA scales pods within 2 minutes of sustained 70%+ CPU; node provisioned within 3 min     | Infrastructure     |
| NFR-015     | Failover drill completes within 15 minutes with < 5 minutes data loss                      | DR Test            |
