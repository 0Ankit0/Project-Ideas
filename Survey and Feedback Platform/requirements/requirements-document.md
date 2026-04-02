# Requirements Document — Survey and Feedback Platform

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Overview](#2-system-overview)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [System Constraints](#5-system-constraints)
6. [Acceptance Criteria](#6-acceptance-criteria)
7. [Operational Policy Addendum](#operational-policy-addendum)

---

## 1. Introduction

### 1.1 Purpose

This document defines the complete set of functional and non-functional requirements for the **Survey and Feedback Platform** — an enterprise-grade multi-tenant SaaS application that enables organizations to design surveys, distribute them across multiple channels, collect responses at scale, and derive actionable intelligence through real-time analytics and automated reporting.

This document serves as the primary contract between product, engineering, QA, and stakeholders and is the authoritative reference for all design, development, and acceptance testing activities.

### 1.2 Scope

The platform encompasses:
- A drag-and-drop form/survey builder supporting 20+ question types
- Multi-channel distribution (email, link, embed, QR, SMS)
- Anonymous and identified response collection with offline PWA support
- Real-time analytics dashboards with NPS, CSAT, sentiment, and cross-tabulation
- Scheduled PDF/Excel/CSV report generation with white-label support
- Audience management with GDPR/CCPA consent tracking
- Template library with 100+ industry templates
- Native integrations (Slack, HubSpot, Salesforce, Zapier) and REST API
- Multi-workspace collaboration with role-based access control
- Subscription billing with Free, Starter, Business, and Enterprise plans

**Out of Scope:** Native iOS/Android mobile apps (PWA only), on-premise deployment (cloud-only SaaS), direct A/B testing infrastructure (third-party), and custom ML model training.

### 1.3 Definitions and Acronyms

| Term / Acronym | Definition |
|---|---|
| **Survey** | A structured set of questions distributed to collect feedback or data from respondents |
| **Form** | A structured data collection artifact (may be used interchangeably with Survey) |
| **Response** | A single completed or partial submission from a respondent |
| **Workspace** | An isolated tenant environment containing surveys, contacts, members, and settings |
| **Distribution** | A configured channel through which a survey is sent to respondents |
| **NPS** | Net Promoter Score — a customer loyalty metric derived from a single 0–10 rating question |
| **CSAT** | Customer Satisfaction Score — a metric from a satisfaction rating question |
| **CES** | Customer Effort Score — a metric from an effort rating question |
| **PII** | Personally Identifiable Information |
| **GDPR** | General Data Protection Regulation (EU 2016/679) |
| **CCPA** | California Consumer Privacy Act |
| **DSR** | Data Subject Request |
| **SSO** | Single Sign-On |
| **JWT** | JSON Web Token |
| **SLA** | Service Level Agreement |
| **RTO** | Recovery Time Objective |
| **RPO** | Recovery Point Objective |
| **MH** | Must Have — mandatory for MVP launch |
| **H** | High priority — required before general availability |
| **M** | Medium priority — targeted for first major release |
| **L** | Low priority — planned for roadmap |

### 1.4 Overview

The platform is structured around the concept of **workspaces** — each organization or team operates within its own isolated workspace. Within a workspace, **Survey Creators** build and distribute surveys, **Respondents** submit feedback, **Analysts** interpret the data, and **Workspace Admins** manage membership and settings. A **Super Admin** manages the platform globally.

---

## 2. System Overview

### 2.1 Product Description

The Survey and Feedback Platform is a cloud-native, multi-tenant SaaS solution hosted on AWS. The backend is built with FastAPI (Python 3.11) using async SQLAlchemy for PostgreSQL 15, MongoDB 7 for document storage, and Redis 7 for caching and Celery task brokering. The frontend is React 18 + TypeScript with Zustand for state management and Recharts for data visualization. Analytics are streamed via AWS Kinesis → Lambda → DynamoDB. File storage uses AWS S3 with CloudFront CDN.

### 2.2 Stakeholders

| Stakeholder | Role | Primary Concerns |
|---|---|---|
| Survey Creator | Platform end-user | Easy form building, broad distribution, clear analytics |
| Respondent | Platform end-user (external) | Fast, accessible survey experience, data privacy |
| Analyst | Platform end-user | Data accuracy, export flexibility, visual insights |
| Workspace Admin | Platform end-user | Member management, billing, integration config |
| Super Admin | Internal operator | Platform health, tenant isolation, compliance |
| Product Team | Internal | Feature completeness, user engagement metrics |
| Engineering Team | Internal | Scalability, maintainability, test coverage |
| Legal/Compliance | Internal | GDPR, CCPA, CAN-SPAM, TCPA compliance |
| Enterprise Customers | External buyers | SLA, SSO, white-label, dedicated support |

### 2.3 Assumptions

1. All workspaces are cloud-hosted; no on-premise deployment is required.
2. Respondents may be internal employees or external customers; both are supported.
3. The platform will handle up to 10,000 concurrent response submissions without horizontal scaling intervention.
4. Email delivery is handled by SendGrid (transactional) and Amazon SES (bulk campaigns).
5. SMS distribution requires workspace admin acknowledgment of TCPA compliance before activation.
6. The platform will comply with GDPR, CCPA, CAN-SPAM, and WCAG 2.1 AA accessibility standards.
7. PostgreSQL is the system of record; MongoDB stores survey structure (JSON documents) for flexibility.

---

## 3. Functional Requirements

### 3.1 Form Builder (FR-FORM)

| ID | Requirement | Priority | Source |
|---|---|---|---|
| FR-FORM-001 | The system shall provide a drag-and-drop canvas where question blocks can be reordered by dragging | MH | Product |
| FR-FORM-002 | The system shall support at least 20 question types: Short Text, Long Text, Single Choice (radio), Multiple Choice (checkbox), Dropdown, Rating Scale, Likert Scale, NPS (0–10), CSAT (1–5 stars), Date/Time, File Upload, Image Choice, Matrix/Grid, Ranking, Slider, Phone Number, Email, URL, Number, and Signature | MH | Product |
| FR-FORM-003 | The system shall support conditional logic rules: show/hide a question or page based on the value of a previous answer | MH | Product |
| FR-FORM-004 | The system shall support branching/skip logic: redirect respondents to a specific page or end the survey based on an answer | MH | Product |
| FR-FORM-005 | The system shall support answer piping: insert a previous answer's text into a subsequent question's label | H | Product |
| FR-FORM-006 | The system shall support multi-page surveys with configurable progress indicators (percentage bar, step count, none) | MH | Product |
| FR-FORM-007 | The system shall provide a real-time side-by-side preview pane that reflects the current survey state for both desktop and mobile viewports | H | UX |
| FR-FORM-008 | The system shall support survey themes: custom colors, fonts, logo upload, and background image via the brand settings panel | H | Product |
| FR-FORM-009 | The system shall enforce character limits on text question responses (configurable min/max) | MH | Product |
| FR-FORM-010 | The system shall support required/optional flags per question and display validation errors inline | MH | Product |
| FR-FORM-011 | The system shall support question grouping into labeled sections/pages with configurable page-level display logic | H | Product |
| FR-FORM-012 | The system shall support multilingual survey creation: a creator can add translations for each language; the respondent's browser locale determines the default language shown | M | Product |
| FR-FORM-013 | The system shall maintain full version history for surveys; a creator can view diffs between versions and restore a previous version | H | Product |
| FR-FORM-014 | The system shall allow duplicate/copy of individual questions and entire surveys | MH | Product |
| FR-FORM-015 | The system shall support importing survey structures from JSON (platform export format) and from Google Forms (via OAuth import) | M | Product |

### 3.2 Survey Distribution (FR-DIST)

| ID | Requirement | Priority | Source |
|---|---|---|---|
| FR-DIST-001 | The system shall generate a unique, shareable public URL for each published survey; the creator can configure it as open (anyone can respond) or invite-only (token required) | MH | Product |
| FR-DIST-002 | The system shall provide an email campaign feature: creators upload or select a contact list, compose an invitation email, and schedule delivery | MH | Product |
| FR-DIST-003 | The system shall support iframe embed code generation with configurable width, height, and auto-resize options | H | Product |
| FR-DIST-004 | The system shall generate a QR code (PNG and SVG) for any survey URL; QR codes shall be downloadable and embeddable in print materials | H | Product |
| FR-DIST-005 | The system shall support SMS distribution via Twilio: send survey links to phone numbers in a contact list | H | Product |
| FR-DIST-006 | The system shall support scheduled distribution: creators can set a future date/time for an email or SMS campaign to be sent automatically | H | Product |
| FR-DIST-007 | The system shall support automated reminder emails: send a follow-up email to non-respondents after a configurable delay (e.g., 3 days) | H | Product |
| FR-DIST-008 | The system shall track link-level analytics per distribution channel: opens, clicks, starts, completions, and drop-off rates | MH | Product |
| FR-DIST-009 | The system shall enforce response quotas: creators can set a maximum number of responses after which the survey closes automatically | M | Product |
| FR-DIST-010 | The system shall support survey expiry: creators can set a date/time after which the survey URL returns a closed message | H | Product |

### 3.3 Response Collection (FR-RESP)

| ID | Requirement | Priority | Source |
|---|---|---|---|
| FR-RESP-001 | The system shall support anonymous response collection: no user account or email is required; only a session token is issued | MH | Product |
| FR-RESP-002 | The system shall support identified response collection: respondents authenticate via email magic link or SSO before submitting | H | Product |
| FR-RESP-003 | The system shall support partial save: a respondent's in-progress answers are saved to the backend every 30 seconds and can be resumed on any device via a resume link | H | Product |
| FR-RESP-004 | The system shall provide an offline-capable Progressive Web App (PWA): responses are stored in IndexedDB when offline and synced automatically when connectivity is restored | H | Product |
| FR-RESP-005 | The system shall implement response deduplication for identified respondents: if the same authenticated user submits twice, the second submission is flagged and blocked or allowed based on creator settings | H | Product |
| FR-RESP-006 | The system shall implement anonymous deduplication via browser fingerprinting + cookie tracking; duplicate attempt is flagged in the response log | M | Product |
| FR-RESP-007 | The system shall stream each submitted response as an event to AWS Kinesis Data Streams for real-time processing | MH | Engineering |
| FR-RESP-008 | The system shall support file upload questions (photos, documents up to 25 MB); uploaded files are stored in AWS S3 and accessible to the workspace admin | H | Product |
| FR-RESP-009 | The system shall render surveys as accessible forms compliant with WCAG 2.1 AA: keyboard navigable, screen reader compatible, color contrast ≥ 4.5:1 | H | Legal |
| FR-RESP-010 | The system shall capture and display response metadata: submission timestamp, device type, browser, country (from IP geolocation, hashed), channel, and completion time | H | Product |

### 3.4 Analytics (FR-ANLY)

| ID | Requirement | Priority | Source |
|---|---|---|---|
| FR-ANLY-001 | The system shall display a real-time summary dashboard per survey showing: total responses, completion rate, average completion time, and response trend over time | MH | Product |
| FR-ANLY-002 | The system shall automatically calculate and display NPS score (Promoters − Detractors) with trend chart and segment breakdown | MH | Product |
| FR-ANLY-003 | The system shall automatically calculate CSAT and CES scores from appropriate question types | H | Product |
| FR-ANLY-004 | The system shall run sentiment analysis on free-text responses using AWS Comprehend and display positive/neutral/negative distributions per question | H | Product |
| FR-ANLY-005 | The system shall generate a word cloud from free-text responses, with word frequency weighting and configurable stop-word filtering | H | Product |
| FR-ANLY-006 | The system shall support cross-tabulation: analysts can pivot any two questions (e.g., "NPS score by department") and view the resulting table and heatmap | H | Product |
| FR-ANLY-007 | The system shall support response filtering: filter the analytics view by date range, distribution channel, respondent segment, country, device type, and custom attributes | MH | Product |
| FR-ANLY-008 | The system shall display per-question analytics: choice frequency charts (bar/pie), average scores for rating questions, histogram for numeric responses | MH | Product |
| FR-ANLY-009 | The system shall support comparison view: compare two date ranges or two survey versions side by side | M | Product |
| FR-ANLY-010 | The system shall provide a response-level data table with search, sort, filter, and per-response drill-down view | MH | Product |
| FR-ANLY-011 | The system shall calculate and display drop-off analytics: show at which question respondents abandon the survey | H | Product |
| FR-ANLY-012 | The system shall support saving custom analytics views (filters + chart configuration) as named dashboards within a workspace | M | Product |

### 3.5 Report Generation (FR-REPT)

| ID | Requirement | Priority | Source |
|---|---|---|---|
| FR-REPT-001 | The system shall export survey results as a PDF report containing: survey metadata, summary statistics, per-question charts, and an appendix of raw responses | MH | Product |
| FR-REPT-002 | The system shall export survey results as an Excel (XLSX) workbook with separate sheets for summary statistics, per-question data, and raw responses | MH | Product |
| FR-REPT-003 | The system shall export raw response data as CSV with configurable column mapping (question IDs or labels) | MH | Product |
| FR-REPT-004 | The system shall support scheduled reports: a creator can configure a daily, weekly, or monthly report that is automatically generated and emailed to specified recipients | H | Product |
| FR-REPT-005 | The system shall support white-label PDF reports: workspace admins on Business/Enterprise plans can upload a logo and configure brand colors applied to all generated PDF reports | H | Enterprise |
| FR-REPT-006 | The system shall store generated report files in AWS S3 and provide a time-limited download link (expires after 24 hours) | H | Engineering |
| FR-REPT-007 | The system shall provide a report history view showing all previously generated reports with status (generating, ready, failed), download link, and generation timestamp | M | Product |
| FR-REPT-008 | The system shall support cross-survey aggregate reports: combine responses from multiple surveys into a single report (Enterprise plan feature) | L | Enterprise |

### 3.6 Audience Management (FR-AUDT)

| ID | Requirement | Priority | Source |
|---|---|---|---|
| FR-AUDT-001 | The system shall allow workspace admins to import contacts via CSV upload (required fields: email; optional: name, phone, custom attributes) | MH | Product |
| FR-AUDT-002 | The system shall support manual contact creation and editing via a UI form | MH | Product |
| FR-AUDT-003 | The system shall support dynamic segmentation: define a segment by attribute filters (e.g., country = "Germany" AND plan = "Pro") that auto-updates as new contacts are added | H | Product |
| FR-AUDT-004 | The system shall track GDPR consent per contact: record consent timestamp, consent text version, and channel (email, SMS); display consent status in the contact record | MH | Legal |
| FR-AUDT-005 | The system shall maintain a full opt-in/opt-out history per contact, including the mechanism (unsubscribe link click, API call, admin override) | MH | Legal |
| FR-AUDT-006 | The system shall suppress opted-out contacts automatically from all future email and SMS distributions within the workspace | MH | Legal |
| FR-AUDT-007 | The system shall support contact deduplication: detect duplicate email addresses on import and prompt the admin to merge or skip | H | Product |
| FR-AUDT-008 | The system shall support GDPR data subject requests (DSR) initiated from the contact record: export all data for a contact, or delete all contact data with a documented audit trail | MH | Legal |

### 3.7 Template Library (FR-TMPL)

| ID | Requirement | Priority | Source |
|---|---|---|---|
| FR-TMPL-001 | The system shall provide a curated library of at least 100 pre-built survey templates organized by industry category (NPS, CSAT, HR, Education, Healthcare, Retail, Events, Market Research) | H | Product |
| FR-TMPL-002 | The system shall allow any survey to be saved as a workspace template and shared with all workspace members | H | Product |
| FR-TMPL-003 | The system shall allow workspace admins to designate certain workspace templates as "default" templates visible to all members on the new survey creation screen | M | Product |
| FR-TMPL-004 | The system shall provide template preview functionality: a creator can preview all questions in a template before using it | H | Product |
| FR-TMPL-005 | The system shall allow Enterprise workspace admins to publish templates to a private organizational template marketplace accessible only to their workspaces | L | Enterprise |
| FR-TMPL-006 | The system shall track template usage metrics (how many surveys were created from each template) and surface them in the Super Admin analytics dashboard | M | Product |

### 3.8 Webhook & API Integration (FR-INTG)

| ID | Requirement | Priority | Source |
|---|---|---|---|
| FR-INTG-001 | The system shall provide a webhook configuration UI: workspace admins can register a URL, select trigger events (response.submitted, survey.published, report.ready), and configure a secret for HMAC signature verification | MH | Product |
| FR-INTG-002 | The system shall deliver webhook payloads with retry logic: up to 5 retries with exponential backoff; failed deliveries logged with response code and error body | MH | Engineering |
| FR-INTG-003 | The system shall provide a native Slack integration: post a configurable notification to a specified channel when a new response is received or when a survey threshold (e.g., NPS drops below 30) is met | H | Product |
| FR-INTG-004 | The system shall provide a native HubSpot integration: sync contact data and push survey responses as HubSpot contact notes or custom properties | H | Product |
| FR-INTG-005 | The system shall provide a native Salesforce integration: create/update Salesforce contacts and push survey responses as Salesforce activities | H | Enterprise |
| FR-INTG-006 | The system shall provide a Zapier integration via Zapier's developer platform, exposing response.submitted and survey.published as Zapier triggers | H | Product |
| FR-INTG-007 | The system shall expose a fully documented REST API (OpenAPI 3.1 spec) allowing external systems to: create surveys, retrieve responses, manage contacts, trigger distributions, and fetch analytics | MH | Product |
| FR-INTG-008 | The system shall support API key authentication for server-to-server integrations; keys are workspace-scoped and can be revoked from the workspace settings panel | MH | Engineering |

### 3.9 Team Collaboration (FR-TEAM)

| ID | Requirement | Priority | Source |
|---|---|---|---|
| FR-TEAM-001 | The system shall support multi-workspace architecture: each workspace is fully isolated with its own surveys, contacts, members, settings, and billing | MH | Product |
| FR-TEAM-002 | The system shall support role-based access control (RBAC) with five roles: Survey Creator, Respondent, Analyst, Workspace Admin, Super Admin | MH | Product |
| FR-TEAM-003 | The system shall allow workspace admins to invite members via email; invitations expire after 7 days | MH | Product |
| FR-TEAM-004 | The system shall support survey-level commenting: workspace members can leave timestamped comments on a survey (not visible to respondents) | M | Product |
| FR-TEAM-005 | The system shall maintain a workspace-level activity audit log: record all actions (survey created, distribution sent, member invited, setting changed) with actor, timestamp, and IP | H | Compliance |
| FR-TEAM-006 | The system shall notify relevant workspace members via email/in-app notification when a survey receives its first response, reaches a milestone (100 responses), or when a scheduled report is ready | M | Product |
| FR-TEAM-007 | The system shall support co-editing notifications: if two users open the same survey in the builder simultaneously, display a warning banner indicating who else is currently editing | M | Product |
| FR-TEAM-008 | The system shall allow workspace admins to transfer survey ownership to another workspace member | M | Product |

### 3.10 Billing & Subscriptions (FR-BILL)

| ID | Requirement | Priority | Source |
|---|---|---|---|
| FR-BILL-001 | The system shall support four subscription tiers: Free, Starter ($29/month), Business ($99/month), and Enterprise (custom pricing) with clearly defined feature gates per tier | MH | Business |
| FR-BILL-002 | The system shall integrate with Stripe for subscription management: create/update/cancel subscriptions, handle payment methods, and process invoices | MH | Business |
| FR-BILL-003 | The system shall enforce usage limits per plan: response quota, active survey count, workspace members, email sends per month, and storage (S3) | MH | Business |
| FR-BILL-004 | The system shall display a real-time usage dashboard to workspace admins showing current usage vs. plan limits with visual progress bars | H | Product |
| FR-BILL-005 | The system shall send automated email notifications at 80% and 100% of any usage limit; at 100%, additional usage is blocked with a plan upgrade prompt | H | Business |
| FR-BILL-006 | The system shall support annual billing at a 20% discount; switching between monthly and annual updates the Stripe subscription at next billing cycle | H | Business |
| FR-BILL-007 | The system shall support coupon/promo code redemption at checkout via Stripe coupon API | M | Business |
| FR-BILL-008 | The system shall provide a full billing history view: all invoices, amounts, status (paid/overdue), and downloadable PDF invoices via Stripe invoice portal | MH | Business |

---

## 4. Non-Functional Requirements

### 4.1 Performance (NFR-PERF)

| ID | Requirement | Priority | Source |
|---|---|---|---|
| NFR-PERF-001 | The survey response submission API endpoint shall respond within 300 ms at the 95th percentile under a load of 1,000 concurrent submissions | MH | Engineering |
| NFR-PERF-002 | The form builder UI shall load and render a survey with up to 50 questions within 2 seconds on a standard broadband connection (20 Mbps) | H | UX |
| NFR-PERF-003 | The analytics dashboard shall load and display summary statistics for up to 100,000 responses within 3 seconds using pre-aggregated DynamoDB data | H | Engineering |
| NFR-PERF-004 | PDF report generation for a survey with 10,000 responses shall complete within 60 seconds as a background Celery task | H | Engineering |
| NFR-PERF-005 | Email campaign distribution of 100,000 recipients shall be enqueued and begin delivery within 60 seconds; full delivery shall complete within 4 hours | H | Engineering |

### 4.2 Security (NFR-SEC)

| ID | Requirement | Priority | Source |
|---|---|---|---|
| NFR-SEC-001 | All API endpoints shall enforce JWT authentication (RS256 algorithm) with 15-minute access token expiry and 30-day refresh token rotation | MH | Security |
| NFR-SEC-002 | All data in transit shall be encrypted using TLS 1.2 or higher; TLS 1.0 and 1.1 shall be disabled on all load balancers and APIs | MH | Security |
| NFR-SEC-003 | All data at rest shall be encrypted using AES-256: RDS storage encryption, S3 SSE-KMS, ElastiCache encryption at rest, and DynamoDB encryption | MH | Security |
| NFR-SEC-004 | The platform shall implement rate limiting: 100 requests per minute per IP for unauthenticated endpoints; 1,000 requests per minute per authenticated user | MH | Security |
| NFR-SEC-005 | The platform shall pass an OWASP Top 10 vulnerability assessment with no critical or high findings prior to production launch | MH | Security |
| NFR-SEC-006 | All user-supplied HTML in custom survey themes and confirmation messages shall be sanitized using a server-side whitelist (DOMPurify equivalent) to prevent XSS | MH | Security |
| NFR-SEC-007 | The platform shall enforce multi-factor authentication (TOTP or email OTP) for Workspace Admin and Super Admin accounts | H | Security |
| NFR-SEC-008 | AWS WAF rules shall be configured to block SQL injection, XSS, and common scanner signatures on all public-facing endpoints; alerts shall be generated for rule triggers exceeding 50 events per minute | H | Security |

### 4.3 Scalability (NFR-SCAL)

| ID | Requirement | Priority | Source |
|---|---|---|---|
| NFR-SCAL-001 | The backend API shall be horizontally scalable via AWS ECS Fargate auto-scaling based on CPU (target: 60%) and request count metrics | MH | Engineering |
| NFR-SCAL-002 | The platform shall support at least 10,000 concurrent survey respondents submitting responses simultaneously without degradation | H | Engineering |
| NFR-SCAL-003 | The database layer shall support read replicas for PostgreSQL (RDS Read Replica) and Redis (ElastiCache cluster mode) to distribute read load from analytics queries | H | Engineering |
| NFR-SCAL-004 | The Kinesis Data Stream shall be configured with sufficient shards to sustain 10,000 response events per second without throttling | H | Engineering |
| NFR-SCAL-005 | The Celery worker pool shall auto-scale based on queue depth: scale out when queue depth exceeds 1,000 tasks; scale in when depth drops below 100 tasks | H | Engineering |

### 4.4 Compliance (NFR-COMP)

| ID | Requirement | Priority | Source |
|---|---|---|---|
| NFR-COMP-001 | The platform shall comply with GDPR: implement consent management, data subject request (DSR) processing, data minimization, right to erasure, and data processing agreements (DPAs) for Business/Enterprise customers | MH | Legal |
| NFR-COMP-002 | The platform shall comply with CCPA: provide a "Do Not Sell My Personal Information" mechanism and respond to California consumer data requests within 45 days | MH | Legal |
| NFR-COMP-003 | All survey invitation emails shall comply with CAN-SPAM Act: include sender identification, physical mailing address, and a one-click unsubscribe mechanism | MH | Legal |
| NFR-COMP-004 | SMS distribution shall comply with TCPA: require explicit written consent acknowledgment by workspace admins before SMS activation; honor opt-out keywords within 10 minutes | MH | Legal |
| NFR-COMP-005 | The survey respondent interface shall meet WCAG 2.1 Level AA accessibility requirements: keyboard navigation, ARIA labels, color contrast ≥ 4.5:1, screen reader compatibility | H | Legal |

### 4.5 Availability (NFR-AVAIL)

| ID | Requirement | Priority | Source |
|---|---|---|---|
| NFR-AVAIL-001 | The platform shall achieve 99.9% uptime SLA for Business plan customers, measured monthly, excluding scheduled maintenance windows | MH | Business |
| NFR-AVAIL-002 | The platform shall achieve 99.95% uptime SLA for Enterprise plan customers, with scheduled maintenance requiring 4-week advance notice | MH | Business |
| NFR-AVAIL-003 | The Recovery Time Objective (RTO) for the primary API and database shall be ≤ 30 minutes, achieved via RDS Multi-AZ automatic failover | MH | Engineering |
| NFR-AVAIL-004 | The Recovery Point Objective (RPO) for the primary database shall be ≤ 5 minutes via RDS point-in-time recovery; Redis data loss shall not exceed 60 seconds via AOF persistence | MH | Engineering |

---

## 5. System Constraints

| Constraint | Description |
|---|---|
| **Cloud-Only** | The platform must be deployable exclusively on AWS; no on-premise or multi-cloud deployment is required |
| **Programming Languages** | Backend: Python 3.11 only. Frontend: TypeScript 5 with React 18. Infrastructure: Terraform HCL |
| **Database Versions** | PostgreSQL 15 (AWS RDS), MongoDB 7 (Atlas), Redis 7 (AWS ElastiCache) — no older versions |
| **File Size Limit** | Survey file uploads are capped at 25 MB per file, 100 MB per survey response session, and 10 GB per workspace (configurable by plan) |
| **Email Sending Domains** | All email campaigns must use a domain authenticated with SPF, DKIM, and DMARC records; unauthenticated domains are blocked |
| **Browser Support** | The frontend must support: Chrome 110+, Firefox 110+, Safari 16+, Edge 110+. Internet Explorer is not supported |
| **Third-Party Dependencies** | Payment processing is exclusively via Stripe. SMS is exclusively via Twilio. Sentiment analysis uses AWS Comprehend only |
| **API Rate Limits** | The public REST API enforces a hard ceiling of 10,000 requests per hour per API key; no exceptions without Enterprise contract SLA |
| **Tenant Isolation** | All workspace data must be logically isolated; cross-workspace data access is only permitted to Super Admin role via audited internal API |

---

## 6. Acceptance Criteria

### 6.1 Form Builder Acceptance Criteria
- A survey creator can create a 10-question survey with at least 5 different question types using the drag-and-drop builder in under 5 minutes on a standard workstation.
- Conditional logic rules correctly show/hide questions in both preview mode and live survey mode across Chrome, Firefox, and Safari.
- Version history correctly captures each save event and allows restoring a previous version without data loss.

### 6.2 Distribution Acceptance Criteria
- An email campaign to 1,000 recipients is fully enqueued within 30 seconds of the creator clicking "Send."
- A QR code generated for a survey URL correctly redirects to the survey when scanned with iOS (Camera app) and Android (Google Lens).
- Reminder emails are not sent to contacts who have already submitted a response.

### 6.3 Response Collection Acceptance Criteria
- A respondent completing a survey on a mobile device (iOS Safari) can partially save, close the browser, and resume from the exact question they left on using the resume link.
- An offline response submitted while the device has no network is automatically synced within 10 seconds of connectivity being restored.
- Duplicate response detection (identified mode) blocks a second submission from the same authenticated user and logs the attempt.

### 6.4 Analytics Acceptance Criteria
- The NPS dashboard correctly calculates and displays the score within 5 seconds of the last response being submitted.
- Cross-tabulation of two questions with up to 10 options each renders correctly as a table and heatmap.
- Sentiment analysis results for free-text responses are available within 60 seconds of response submission.

### 6.5 Security Acceptance Criteria
- All endpoints return 401 for requests with expired or missing JWT tokens.
- Attempting to access another workspace's survey data via the API returns 403 for all roles except Super Admin.
- OWASP ZAP scan reports no critical or high severity findings against the staging environment prior to production launch.

---

## Operational Policy Addendum

### 1. Response Data Privacy Policies

**GDPR Compliance Framework**
- All identified survey response data for EU residents is processed under a lawful basis (consent or legitimate interest), documented per workspace.
- Data subject requests must be acknowledged within 72 hours and fulfilled within 30 days; the platform provides automated tools to export and delete contact/response data.
- Sub-processors (AWS, SendGrid, Twilio, Stripe) are listed in the platform's public DPA, available at `/legal/dpa`.
- All workspace admins are prompted to complete a Data Protection Impact Assessment (DPIA) checklist before enabling identified response collection at scale (>10,000 respondents).

**CCPA Rights Management**
- A "Do Not Sell" request suppresses the contact from all data exports shared with third-party integrations (HubSpot, Salesforce).
- Consumer data requests are logged in the audit trail with requester identity and fulfillment timestamp.

**Data Minimization and PII Controls**
- IP addresses are hashed (SHA-256 with workspace-specific salt) at the point of capture; plaintext IPs are never stored.
- File upload responses containing potential PII (photos, documents) are stored in private S3 buckets with per-request signed URLs; direct public URLs are never issued.

---

### 2. Survey Distribution Policies

**CAN-SPAM and GDPR Email Requirements**
- Every outbound survey email must contain: sender name, physical mailing address (workspace admin configures this in settings), subject line that is not deceptive, and a functioning one-click unsubscribe link.
- Opt-out requests via unsubscribe link are processed within 10 business days (platform processes them within seconds; the legal maximum is honored as the SLA).
- Suppression list is checked before every campaign send; no overrides are permitted by any user role.

**SMS TCPA Compliance**
- Workspace admins must check a compliance acknowledgment checkbox and upload evidence of consent before the SMS distribution channel is unlocked.
- Opt-out keywords (STOP, END, CANCEL, UNSUBSCRIBE, QUIT) trigger immediate contact suppression.

**Anti-Abuse Measures**
- Email campaigns with an invalid or missing "From" domain authentication are blocked at the send stage.
- Accounts that receive SPAM complaints exceeding 0.1% on any campaign are automatically suspended pending review.

---

### 3. Analytics and Retention Policies

**Retention Schedule**

| Data Category | Active Retention | Archive | Deletion |
|---|---|---|---|
| Identified responses | Subscription term | S3 Glacier (90-day grace) | On workspace deletion or DSR |
| Anonymous responses | 36 months | Aggregated form only | Raw data purged after 36 months |
| Audit logs | 24 months | S3 encrypted | Purged at 24 months |
| Email logs | 12 months | None | Purged at 12 months |
| Analytics aggregates | 18 months (DynamoDB) | S3 Parquet | Retained in aggregate indefinitely |

**k-Anonymity Enforcement**
- Analytics views and exports suppress any segment with fewer than 5 responses to prevent re-identification of individual respondents.
- This threshold is configurable to a minimum of 3 for Enterprise plans with a documented internal justification.

**Third-Party Analytics Processing**
- Free-text responses sent to AWS Comprehend for sentiment analysis are processed transiently; no data is retained by Comprehend beyond the API response.
- Workspace admins may disable sentiment analysis at the workspace level; this setting is respected by all new distributions immediately.

---

### 4. System Availability Policies

**Uptime Commitments**

| Tier | Monthly Uptime Target | Measurement Method |
|---|---|---|
| Free | 99.5% | Synthetic monitoring via AWS CloudWatch |
| Starter | 99.7% | Synthetic monitoring + external probe (Pingdom) |
| Business | 99.9% | Synthetic monitoring + Datadog APM |
| Enterprise | 99.95% | Dedicated monitoring + SLA credit mechanism |

**Maintenance Windows**
- Scheduled maintenance for schema migrations and infrastructure updates occurs during low-traffic windows: Sundays 02:00–06:00 UTC.
- Enterprise customers are notified 28 days in advance and given a 7-day window to request a reschedule.
- Zero-downtime deployments are the standard for application code changes; only schema migrations or infrastructure changes may require brief maintenance.

**Incident Response SLA**
- P1 (full platform outage): Engineering on-call acknowledged within 15 minutes; status page updated within 30 minutes; postmortem published within 5 business days.
- P2 (major feature degraded): Acknowledged within 1 hour; resolved within 4 hours.
- P3 (minor degradation): Acknowledged within 4 hours; resolved within 48 hours.

**Backup Verification**
- Automated backup restoration tests are executed monthly in the staging environment to verify RTO/RPO targets.
- Results of restoration tests are documented in the operations log and available to Enterprise customers on request.
