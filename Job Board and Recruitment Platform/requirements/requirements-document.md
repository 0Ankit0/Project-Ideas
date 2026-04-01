# Requirements Document — Job Board and Recruitment Platform

**Version:** 1.0  
**Status:** Approved  
**Owner:** Product Management — Talent Acquisition Platform  
**Last Reviewed:** 2025-01

---

## 1. Introduction

### 1.1 Purpose

This document specifies the functional and non-functional requirements for the Job Board and Recruitment Platform (hereafter "the Platform"). It serves as the authoritative contract between product, engineering, design, and compliance teams. All features built for the v1 release must satisfy the requirements stated here, and any deviation requires a change request with sign-off from the Product Owner and affected stakeholders.

### 1.2 Scope

The Platform covers the full recruitment lifecycle for enterprise and mid-market companies: job requisition creation, multi-board job distribution, candidate application intake, AI-assisted resume parsing, ATS pipeline management, interview scheduling and structured feedback, offer generation and digital signing, background check initiation, and cross-functional hiring analytics. The system is multi-tenant, supporting many companies with strict data isolation.

Out of scope for v1: payroll processing, onboarding workflow automation beyond handoff triggers, learning & development integrations, and internal mobility / promotion workflows.

### 1.3 Stakeholders

| Stakeholder | Role |
|---|---|
| Talent Acquisition Leads | Primary system users; define workflow requirements |
| Hiring Managers | Secondary users; validate candidate review UX requirements |
| HR Administrators | Platform configuration and compliance requirements |
| Engineering Team | Technical feasibility, implementation |
| Legal / Compliance | GDPR, EEO/OFCCP, pay transparency law requirements |
| Security Team | Data protection, audit, penetration testing |
| Finance | Subscription billing, per-seat pricing model |

### 1.4 Definitions

| Term | Definition |
|---|---|
| Requisition | An approved request to hire for a specific role |
| Job Posting | The public-facing advertisement for a requisition |
| Application | A candidate's submission for a specific job posting |
| Pipeline | The ordered set of stages a candidate moves through for a given requisition |
| Stage | A discrete step in the hiring pipeline (e.g., "Phone Screen", "Technical Interview") |
| Scorecard | A structured evaluation form tied to an interview round |
| Offer | A formal employment proposal sent to a selected candidate |
| Disposition | The recorded outcome for a candidate at any stage (Advance, Reject, On Hold) |
| Tenant | A single company account with isolated data within the multi-tenant platform |

---

## 2. Functional Requirements

---

### 2.1 Job Posting Management

#### FR-01: Job Requisition Creation
The system shall allow users with the Recruiter or HR Admin role to create a new job requisition. Required fields: job title, department, hiring manager, employment type (Full-Time, Part-Time, Contract, Internship), work location (On-site / Hybrid / Remote), target start date, number of openings, and job description (rich text). Optional fields: salary range (minimum, maximum, currency), equity range, bonus type, internal job code, cost center, and EEO job category. Drafts must be auto-saved every 30 seconds to prevent data loss.

#### FR-02: Job Approval Workflow
The system shall enforce a configurable multi-step approval workflow before a job posting goes live. HR Admins shall define approval chains at the company level (e.g., Recruiter submits → Hiring Manager approves → HR Admin approves → Auto-publish). Each approver shall receive an email notification and in-platform notification when action is required. Approvers shall be able to approve, reject (with a mandatory comment), or delegate approval. The system shall display the current approval status on the requisition detail page. Approved postings that are not published within 14 days must re-enter the approval chain.

#### FR-03: Rich Job Description Authoring
The job description editor shall support rich text formatting: headings, bold, italic, bulleted lists, numbered lists, hyperlinks, and table insertion. The system shall provide a library of company-managed job description templates that recruiters can select and customize. Template fields (e.g., `{{DEPARTMENT}}`, `{{LOCATION}}`) shall be auto-populated from the requisition form. The description shall have a minimum length validation of 150 characters.

#### FR-04: Salary Range Management and Pay Transparency
The system shall store salary ranges as a minimum-maximum pair with a specified currency and pay period (Annual, Monthly, Hourly). HR Admins shall configure per-jurisdiction pay transparency rules that automatically control whether the salary range is displayed publicly on job postings. States/provinces with mandatory pay disclosure laws (e.g., California, New York, Colorado, Washington, UK) must have range display enabled by default and the recruiter must not be able to hide it. The system shall log when a salary range is edited and by whom.

#### FR-05: Job Posting Publishing and Status Lifecycle
A job posting shall move through the following statuses: Draft → Pending Approval → Approved → Active → Paused → Closed → Archived. Transitions shall be logged with a timestamp and acting user. Recruiters shall be able to pause an active posting (stops accepting new applications but retains existing ones), close a posting (stops accepting applications, triggers rejection emails to open applicants per company settings), and archive a closed posting (removes it from dashboards but retains data for compliance). A closed posting shall not be directly re-opened; a clone action shall create a new draft requisition.

#### FR-06: Job Posting Distribution to External Boards
Upon activation, the system shall automatically syndicate job postings to all external job boards that the company has enabled and configured. Supported boards at launch: LinkedIn Jobs, Indeed, Glassdoor, ZipRecruiter. Each integration shall use the board's official API (e.g., LinkedIn Job Postings API, Indeed Publisher API). The system shall display the syndication status (Pending, Live, Failed, Expired) per board on the requisition detail page. Failed syndications shall trigger an alert to the owning recruiter with the error message from the third-party board. The system shall poll each board every 4 hours to confirm the posting remains live.

#### FR-07: Job Board Credential Management
HR Admins shall be able to connect and manage API credentials for each supported job board per tenant. Credentials shall be stored encrypted at rest and shall never be exposed in API responses or UI. Admins shall be able to test the connection and view the last successful sync timestamp.

#### FR-08: Job Cloning
Recruiters shall be able to clone an existing job posting (in any status) to create a new draft with identical field values (except for dates and posting status). Cloning shall preserve the job description, salary range, screening questions, and pipeline template but shall not copy existing applications or candidate data.

#### FR-09: Custom Screening Questions
Recruiters shall be able to attach up to 10 custom screening questions to a job posting. Question types supported: Yes/No, Multiple Choice (single select), Multiple Choice (multi-select), Short Text (max 500 chars), Long Text (max 2000 chars), File Upload, and Numeric. Questions can be marked as Required or Optional. Yes/No questions can be designated as "Knockout" questions — if a candidate answers contrary to the required value, their application is automatically marked with a "Disqualified" label and routed to the Rejected stage.

#### FR-10: Internal and External Visibility
Each job posting shall be designatable as External (visible on public careers page and syndicated to job boards), Internal (visible only to logged-in employees via a separate internal careers view), or Both. Internal postings shall require employee authentication before the application form is accessible. The careers page widget shall be embeddable on any company website via a JavaScript snippet.

---

### 2.2 Candidate Applications

#### FR-11: Application Submission
Candidates shall be able to apply to a job posting by completing an application form. The form shall include: full name, email, phone number, location, LinkedIn profile URL (optional), portfolio/website URL (optional), resume upload (required), cover letter (optional — text or file upload), answers to any custom screening questions, and Equal Employment Opportunity (EEO) self-identification fields (collected separately and never viewable by recruiters or hiring managers — only accessible to HR Admins for reporting). The application form shall be responsive and functional on mobile devices.

#### FR-12: Resume Upload and Storage
The system shall accept resume uploads in PDF, DOCX, DOC, and RTF formats up to 10 MB in size. Resumes shall be stored in encrypted object storage (S3) with a per-tenant access policy. Candidates shall be able to replace their resume on file without creating a duplicate application. The system shall retain original uploaded resumes indefinitely (subject to GDPR retention policies) alongside parsed structured data.

#### FR-13: AI-Powered Resume Parsing
Immediately upon resume upload, the system shall trigger an asynchronous resume parsing job. The parser shall extract: full name, email, phone, address, LinkedIn URL, professional summary, work experience entries (company name, title, dates, description, location), education entries (institution, degree, field of study, graduation year), skills list, certifications, languages, and publications. Parsed data shall be stored in structured fields in the candidate profile. Candidates shall be able to review and edit parsed data through the candidate portal. Parsing failures shall be logged and the recruiter shall see a "Manual Review Required" indicator; the application must not be lost.

#### FR-14: Duplicate Application Prevention
The system shall prevent a candidate from submitting more than one active application for the same job posting. If a candidate with a matching email address attempts to apply again, the system shall display a message informing them they have already applied and provide a link to their application status in the candidate portal. The system shall also flag when a candidate has been rejected from the same role within the past 180 days and display this to the recruiter during review.

#### FR-15: Application Confirmation Email
Upon successful application submission, the system shall send an automated confirmation email to the candidate's registered email address within 2 minutes. The email shall include: job title, company name, application reference number, estimated response timeline (if configured by the recruiter), link to the candidate portal to track status, and unsubscribe / GDPR consent links. Email templates shall be customizable per tenant through the HR Admin dashboard.

#### FR-16: Application Status Notifications
The system shall send automated email notifications to candidates at the following status transitions: application received (FR-15), moved to interview stage, interview scheduled (with calendar invite attachment), offer extended, offer accepted, offer declined, application withdrawn by candidate, and application rejected. Each notification type shall have a configurable template in the HR Admin settings. Recruiters shall be able to suppress individual notifications before a stage transition if needed.

#### FR-17: Candidate Portal
The system shall provide a password-protected, mobile-responsive candidate portal accessible at a company-specific subdomain (e.g., `careers.company.com/portal`). Candidates shall be able to: view a dashboard of all their applications and statuses, access the interview schedule for upcoming interviews, view and sign offer letters, upload updated resumes or documents on request, manage communication preferences, and submit GDPR data requests. The portal shall support SSO login via Google and LinkedIn OAuth.

#### FR-18: Candidate Profile and Database
All candidate applications shall populate a searchable, tenant-isolated candidate database. Each candidate record shall include: contact information, all applications (current and historical), resume file and parsed data, interviewer feedback (private — not shown to candidate), timeline of all actions taken, tags applied by recruiters, and internal notes. Candidate records shall not be deleted when an application is closed; they are retained for future sourcing. Candidates who have never applied can be manually added by recruiters (for sourced/headhunted talent).

#### FR-19: Boolean Resume Search
Recruiters shall be able to search the candidate database using Boolean operators (AND, OR, NOT) across multiple fields: full text of resume, skills, job titles, companies, education institutions, and tags. The search results shall display match score, last activity date, current application status, and a resume snippet with query term highlights. Results shall be filterable by: years of experience, location (within X miles / country), education level, employment type preference, and availability.

#### FR-20: Referral Tracking
The system shall support an employee referral program where existing employees can submit referrals for open positions. Referral submissions shall include the referred candidate's contact information, the position, and the referring employee ID. Referred candidates' applications shall be tagged with "Employee Referral" and the referrer's name (visible to recruiters but not to hiring managers). The system shall track the disposition of referred candidates to support referral bonus payouts and report on referral-to-hire conversion rates.

---

### 2.3 ATS Pipeline Management

#### FR-21: Pipeline Stage Configuration
HR Admins and Recruiters shall be able to configure custom hiring pipeline templates at the company level. Each pipeline template shall consist of ordered stages with configurable names, types (Screening, Assessment, Interview, Offer, Hired, Rejected), and optional SLA thresholds in days. Pipeline templates shall be assignable to job postings at creation time. The system shall provide a default pipeline template. Stages cannot be deleted from an active pipeline template if candidates currently occupy that stage.

#### FR-22: Kanban Pipeline View
The primary ATS view for a requisition shall be a Kanban board displaying candidates as cards in their current stage column. Recruiters shall be able to drag-and-drop candidate cards between stages. Each card shall display: candidate name, current stage duration, latest application activity, resume match score (if AI ranking is enabled), and quick-action icons (view profile, send email, schedule interview, reject). The board shall support real-time updates — if another recruiter moves a candidate, the view shall refresh without requiring a manual page reload.

#### FR-23: List Pipeline View
In addition to the Kanban view, the system shall provide a sortable, filterable list/table view of all candidates for a requisition. Columns: candidate name, stage, source, applied date, days in current stage, last activity, assigned recruiter, and tags. The list shall support multi-select for bulk actions. Columns shall be configurable per user.

#### FR-24: Bulk Application Actions
Recruiters shall be able to select multiple candidates and apply the following bulk actions: advance to next stage, move to specific stage, send bulk email (from template), apply tag, remove tag, assign to recruiter, reject (with reason), archive, export to CSV. Bulk actions shall be logged in each candidate's activity timeline. A preview of the selected candidates must be shown before any destructive bulk action (reject, archive) is confirmed.

#### FR-25: Automatic Stage Transition Rules
HR Admins shall be able to configure automation rules per pipeline stage. Supported triggers: resume match score exceeds threshold (e.g., score ≥ 80 → auto-advance to Phone Screen), screening question knockout answered (→ auto-reject), SLA threshold exceeded (→ notify recruiter), assessment score received (→ auto-advance or auto-reject based on threshold). Automation rules shall create an activity log entry indicating the action was taken automatically and the rule that triggered it. Recruiters shall be able to override any automated decision.

#### FR-26: Candidate Tagging
Recruiters shall be able to create and apply custom tags to any candidate profile within their tenant. Tags shall be color-coded and searchable. Examples: "Top Talent", "Re-engage", "Passive Candidate", "Technical Hold", "Diversity Priority". Tags shall persist across applications — if a candidate applies to multiple roles, their tags are visible on all application records. HR Admins shall manage the company-wide tag taxonomy.

#### FR-27: Candidate Pool Management
Recruiters shall be able to create named candidate pools (talent pipelines) that exist independently of specific job openings. Candidates can be added to one or more pools manually or via automated rules. Pools can be linked to a future requisition when it opens, pre-populating the pipeline with sourced candidates. Pool members shall receive opt-in consent requests before being contacted, with the consent status recorded.

#### FR-28: Rejection Reason Tracking
When a candidate is moved to a rejected stage, the system shall require the recruiter to select a rejection reason from a configurable list (e.g., "Overqualified", "Underqualified", "Failed Technical Screen", "Withdrew", "Compensation Mismatch", "Position Filled", "No Response"). Rejection reasons shall be captured for every candidate across all stages and used in diversity, funnel, and compliance reporting. Rejection reasons shall never be displayed to candidates (who receive only a generic declination message unless the recruiter chooses to add a personalized note).

#### FR-29: Recruiter Assignment and Collaboration
Multiple recruiters shall be able to be assigned to a single requisition. Each recruiter shall see the full pipeline. The recruiter designated as the "lead" shall be responsible for SLA compliance and reporting. Any recruiter on a requisition shall be able to perform pipeline actions. @mention functionality shall allow recruiters to tag colleagues in internal notes, triggering a notification.

#### FR-30: Activity Timeline
Every candidate application shall have a comprehensive activity timeline displaying all events in chronological order: application submitted, email sent/received, stage changes (manual and automatic), tags applied/removed, notes added, interviews scheduled, feedback submitted, offers generated, documents signed, and GDPR requests. Timeline entries shall display the acting user (or "System" for automated actions) and the timestamp.

---

### 2.4 Interview Management

#### FR-31: Interview Creation
Recruiters shall be able to create one or more interview rounds for a candidate at any pipeline stage. For each round, they shall specify: interview type (Phone Screen, Video, On-site, Panel, Technical Assessment, Take-Home Project), duration, interviewer(s) (one or more users), scorecard template, and any instructions for the candidate. Rounds shall be ordered and the system shall prevent scheduling a later round before an earlier round is completed unless explicitly overridden.

#### FR-32: Multi-Round Interview Workflow
A structured interview plan shall be attachable to a job posting, defining the required rounds in order. When a candidate is advanced to an interview stage, the system shall generate the full interview plan for that candidate, prompting the recruiter to schedule each round in sequence. The system shall track the status of each round: Not Scheduled, Scheduled, Completed, Cancelled, Rescheduled.

#### FR-33: Interviewer Availability and Calendar Integration
The system shall integrate with Google Calendar (via Google Calendar API) and Microsoft Outlook/Exchange (via Microsoft Graph API) to read interviewer free/busy data. When scheduling an interview, the system shall display available time slots for all required interviewers within a recruiter-specified date range. Schedulers shall be able to propose 2–5 time slots to the candidate via email, and the candidate shall confirm their preferred slot through the candidate portal without requiring a login if a tokenized link is used.

#### FR-34: Automated Calendar Invite Generation
Upon interview confirmation, the system shall automatically generate and send calendar invitations to all parties (candidate and all interviewers). Invitations shall include: interview type, job title, interviewer names, duration, location (physical address or video conferencing link), and candidate's resume as an attachment. If the interview is via video, the system shall auto-generate a meeting link using the configured video conferencing provider (Zoom or Microsoft Teams) and embed it in the invite.

#### FR-35: Structured Interview Scorecards
Each interview round shall have an associated scorecard template. Scorecard templates shall be created and managed by HR Admins and shall contain: a list of competency dimensions (e.g., "Technical Depth", "Communication", "Problem Solving"), a rating scale (1–5 or custom), a free-text recommendation field, and an overall hire recommendation (Strong Yes, Yes, No, Strong No). Interviewers shall submit their scorecard through the platform. Scorecards shall be visible to all interviewers on the same requisition only after they have submitted their own scorecard, to prevent bias anchoring.

#### FR-36: Interview Feedback Submission
Interviewers shall receive an email and in-platform reminder to submit scorecard feedback within 24 hours of interview completion. If feedback is not submitted within 48 hours, a second reminder shall be sent and the recruiter shall be notified. The recruiter shall be able to mark a scorecard as "Not Required" for administrative reasons (e.g., candidate withdrew before the interview took place). Feedback shall be locked for editing 7 days after submission unless an HR Admin unlocks it with a recorded reason.

#### FR-37: Video Interview Link Generation
The system shall support two modes for video interviews: (a) auto-generated links via Zoom API or Microsoft Teams API, creating a unique meeting room per interview, and (b) manual URL entry by the recruiter. Auto-generated links shall be created at least 30 minutes before the scheduled interview time. The system shall handle Zoom/Teams OAuth token refresh automatically.

#### FR-38: Interview Rescheduling and Cancellation
Recruiters and candidates shall both be able to request interview reschedules or cancellations. A candidate rescheduling request through the portal shall notify the recruiter, who must confirm the new time. Recruiter-initiated reschedules shall automatically notify the candidate and all interviewers and update the calendar invitations. Cancellations shall send cancellation notices to all parties and update the calendar invitations. A rescheduled interview shall require a new time to be confirmed before the candidate notification is sent. Cancellation reasons shall be recorded.

---

### 2.5 Offer Management

#### FR-39: Offer Letter Generation from Template
Recruiters shall be able to generate an offer letter by selecting a company-managed template and confirming auto-populated fields: candidate name, job title, department, reporting manager, start date, base salary, bonus target, equity grant, benefits summary, offer expiry date, and office location. Templates shall be created and managed by HR Admins using a rich-text editor with merge field tokens. Multiple templates shall be maintainable per company (e.g., by employment type or jurisdiction). A PDF preview shall be generated before the offer is sent for approval.

#### FR-40: Offer Approval Chain
Before an offer letter is sent to a candidate, it must pass through the company's configured offer approval chain. HR Admins shall define approval chains per employee level or department (e.g., Entry Level: Hiring Manager → HR; Senior: Hiring Manager → VP → HR → Finance). Each approver shall receive a notification and shall be able to approve or reject with a comment. If an approver rejects, the offer returns to the recruiter for revision. Escalation rules shall auto-approve if an approver does not respond within the configured SLA (default: 48 hours) and the next approver in the chain is notified.

#### FR-41: Digital Offer Signing
Once approved, the offer letter shall be sent to the candidate via the configured e-signature provider (DocuSign or HelloSign). The candidate shall receive an email with a link to review and sign the document. The platform shall display offer status: Sent, Viewed, Signed, Declined, Countered, Expired. Signed documents shall be stored in encrypted object storage and linked to both the candidate record and the requisition. The recruiter and HR Admin shall receive a notification upon each status change.

#### FR-42: Offer Negotiation Tracking
If a candidate declines the offer or submits a counter-proposal, the recruiter shall be able to record the negotiation detail, revise the offer (triggering a modified approval chain if compensation changes), and re-send the updated offer. The system shall maintain a full negotiation history: original offer values, counter values, revised offer values, and the final accepted values. A maximum of 3 negotiation rounds shall be enforced per offer; beyond this, an HR Admin override is required.

#### FR-43: Offer Expiry Enforcement
Offer letters shall have a mandatory expiry date set at generation time. The system shall send reminder emails to the candidate 48 hours and 24 hours before expiry. If the candidate has not signed by the expiry date, the offer shall automatically transition to "Expired" status, the recruiter and HR Admin shall be notified, and the candidate shall be sent a notification that their offer has lapsed. Extending an expired offer requires creating a new offer with a new approval cycle. The recruiter shall not be able to override expiry without HR Admin permission.

#### FR-44: Background Check Initiation
Upon offer acceptance, the system shall automatically trigger a background check order through the Checkr API using the company's configured check package. The check package (e.g., "Standard – Criminal + Employment Verification" or "Enhanced – Plus Education and Credit") shall be selectable per job level by HR Admins. Checkr shall return status updates via webhook, which the system shall display on the offer/candidate detail page. Status values: Pending, In Progress, Consider, Clear, Dispute. If the result is "Consider", the recruiter is notified and an adverse action workflow is surfaced per FCRA requirements.

---

### 2.6 Analytics and Reporting

#### FR-45: Time-to-Hire and Time-to-Fill Metrics
The system shall calculate and display time-to-hire (days from application submitted to offer accepted) and time-to-fill (days from job posted to offer accepted) for each requisition and aggregated across department, recruiter, job level, and time period. The calculations shall exclude weekends and company holidays (configurable per tenant). These metrics shall be displayed on the Recruiter Dashboard in real time and in the executive analytics module with trend lines over selectable date ranges.

#### FR-46: Source Attribution and ROI
The system shall track the original application source for every candidate (LinkedIn, Indeed, Glassdoor, ZipRecruiter, Company Careers Page, Employee Referral, Recruiter Sourced, Other). Source attribution shall be derived from UTM parameters on the careers page, job board API tags, and recruiter-manual source selection. The analytics module shall report cost-per-application and cost-per-hire by source (using job board spend data entered by HR Admins) to calculate source ROI. Reports shall be filterable by date range, department, and job level.

#### FR-47: Pipeline Conversion Funnel Analytics
The system shall provide a visual funnel report for any requisition, department, or company-wide scope showing the candidate conversion rate at each pipeline stage: Applied → Screened → Phone Screen → Interview → Offer → Hired. Drop-off rates shall be highlighted. The funnel shall be viewable by date range and segmentable by source, recruiter, department, and job level. This report shall be a key component of the Talent Operations dashboard.

#### FR-48: Diversity and EEO Reporting
The system shall generate EEO-1 Component 1 reports (job category × race/ethnicity × gender) and OFCCP Internet Applicant data reports based on self-identification data collected at application. All diversity reports shall be accessible only to users with the HR Admin role. EEO data shall be stored separately from recruiter-visible candidate data with a separate access control layer. The system shall allow HR Admins to export EEO data as a CSV in the standard EEO-1 format.

#### FR-49: Recruiter Performance Reports
The system shall provide a recruiter-facing and manager-facing performance report showing per-recruiter metrics: number of active requisitions, applications reviewed, phone screens completed, interviews scheduled, offers extended, offers accepted, average time-to-fill, and response time SLA compliance (time from application submission to first recruiter action). These reports shall be visible to the individual recruiter and to HR Admins. Team lead views shall show all recruiters they manage.

#### FR-50: Scheduled Report Delivery
HR Admins and Executives shall be able to configure scheduled report delivery. Any standard report can be scheduled for daily, weekly, or monthly delivery. Reports shall be delivered as PDF or CSV attachments via email to a configurable list of recipients. Recipients do not need a platform account to receive the scheduled reports. The system shall log delivery status (sent, failed) for audit purposes.

---

## 3. Non-Functional Requirements

---

### 3.1 Performance

#### NFR-01: API Response Latency
All REST API endpoints shall respond within 200 milliseconds at the 95th percentile (p95) under the specified peak load conditions (10,000 concurrent users). Endpoints handling file uploads and asynchronous operations (resume parsing, job syndication) are exempt from this SLA but shall acknowledge the request within 200ms and return a job ID for polling.

#### NFR-02: Resume Parsing Throughput
Resume parsing (extraction of structured data from uploaded document) shall complete within 30 seconds for 95% of submissions. Parsing jobs shall be queued and processed by dedicated worker processes. The queue depth shall be monitored and workers shall auto-scale when queue depth exceeds 100 items. A parsing timeout after 60 seconds shall log the failure and surface a manual review flag on the application.

#### NFR-03: Job Syndication Latency
Job postings approved for external distribution shall be submitted to all configured job boards within 5 minutes of activation. Board-specific API rate limits shall be respected and job syndication shall retry with exponential backoff on transient failures (max 3 retries). Definitive failures shall alert the owning recruiter.

#### NFR-04: Search Query Performance
Candidate Boolean search queries shall return results within 1 second at p95 for tenant databases containing up to 1 million candidate records. Elasticsearch index refresh intervals shall be configured to ensure newly uploaded resumes appear in search results within 60 seconds of parsing completion.

#### NFR-05: Page Load Performance
The recruiter dashboard and candidate portal shall achieve a Largest Contentful Paint (LCP) of under 2.5 seconds and a Time to Interactive (TTI) of under 3 seconds on a 4G mobile connection, measured against Chrome's Lighthouse tool in simulated throttling conditions.

---

### 3.2 Scalability

#### NFR-06: Concurrent User Support
The system shall support 10,000 concurrent authenticated users without degradation below the performance SLAs defined in NFR-01. Load tests shall be run quarterly to validate this threshold. Kubernetes horizontal pod autoscaling shall maintain p95 response times during burst traffic events (e.g., a large company opening a high-volume role).

#### NFR-07: Candidate Database Scale
The platform shall support up to 1,000,000 candidate records per tenant without performance degradation in search, pipeline queries, or profile rendering. PostgreSQL table partitioning and Elasticsearch index sharding strategies shall be designed to accommodate this scale from launch.

#### NFR-08: Application Volume
The platform shall process up to 100,000 job applications per month across all tenants without degradation of application submission latency below 500ms p95. Resume parsing workers shall scale automatically to handle monthly application volume spikes.

#### NFR-09: Multi-Tenant Isolation
The system shall maintain complete data isolation between tenants at the database, API, and search index layers. Row-Level Security (RLS) policies in PostgreSQL and index-level tenant filtering in Elasticsearch shall prevent cross-tenant data leakage. Multi-tenant isolation shall be validated as part of the security regression test suite.

---

### 3.3 Availability and Reliability

#### NFR-10: Uptime SLA
The platform shall achieve 99.9% uptime measured monthly (maximum 43.8 minutes of unplanned downtime per month), excluding scheduled maintenance windows. Scheduled maintenance shall occur during off-peak hours (Saturday 02:00–06:00 UTC) and announced at least 72 hours in advance via the status page and in-app banner.

#### NFR-11: Recovery Time Objective (RTO)
In the event of a critical failure (database node failure, availability zone outage), the system shall recover to a fully operational state within 4 hours (RTO = 4h). Failover to a standby database node shall be automatic and shall complete within 30 seconds.

#### NFR-12: Recovery Point Objective (RPO)
Database backups shall be taken continuously via PostgreSQL streaming replication with point-in-time recovery (PITR). The RPO shall be 1 hour — no more than 1 hour of data shall be lost in a worst-case failure scenario. Daily full backups shall be retained for 30 days; weekly backups for 12 months.

#### NFR-13: Background Job Reliability
Asynchronous background jobs (resume parsing, email delivery, job syndication, webhook dispatch) shall be executed with at-least-once delivery semantics. Failed jobs shall be retried with exponential backoff and placed in a dead-letter queue after 3 failures, triggering an alert to the on-call engineer. Job execution history shall be retained for 7 days for debugging.

---

### 3.4 Security

#### NFR-14: Role-Based Access Control
The system shall enforce RBAC with the following roles and permissions hierarchy: Super Admin > HR Admin > Recruiter > Hiring Manager > Candidate. Permission checks shall be enforced at the API layer on every request. Frontend role restrictions are supplementary and shall not be the sole enforcement mechanism. Permission changes shall take effect within 60 seconds without requiring a user to log out.

#### NFR-15: Data Encryption
All data at rest shall be encrypted using AES-256. All data in transit shall be encrypted using TLS 1.2 or higher (TLS 1.3 preferred). Database connection strings, API keys, and other secrets shall be stored in a secrets manager (AWS Secrets Manager or HashiCorp Vault) and never hardcoded in application code or environment files in version control.

#### NFR-16: Authentication Security
User authentication shall require email + password or SSO (Google, Microsoft, Okta, SAML 2.0). Passwords shall be hashed using bcrypt (cost factor ≥ 12). Multi-factor authentication (TOTP or SMS) shall be available and enforceable by HR Admins for their tenant. Session tokens shall expire after 8 hours of inactivity. Failed login attempts shall be rate-limited: 10 attempts per 15 minutes per IP and per account, triggering a temporary lockout and notification to the account owner.

#### NFR-17: PII Data Masking and Access Logging
Personally Identifiable Information (PII) fields (Social Security Number if collected for background checks, date of birth, passport number) shall be masked in API responses to all roles except HR Admin. All reads, writes, and exports of PII fields shall be logged to an immutable audit log with user ID, timestamp, action, and record reference. The audit log shall be retained for 3 years.

#### NFR-18: SOC 2 Type II Compliance
The platform's operational controls shall satisfy the requirements for SOC 2 Type II certification across the Security, Availability, and Confidentiality trust service criteria. Evidence collection for the annual SOC 2 audit shall be supported by the platform's audit log, access control reports, and infrastructure monitoring configuration.

#### NFR-19: Vulnerability Management
The platform's third-party dependencies shall be scanned for known vulnerabilities (CVE) on every CI build using automated tooling (e.g., npm audit, Snyk, Trivy for Docker images). Critical vulnerabilities (CVSS ≥ 9.0) shall be remediated within 72 hours. High vulnerabilities (CVSS 7.0–8.9) within 7 days. Penetration testing shall be conducted at least annually by a qualified third party.

---

### 3.5 Compliance

#### NFR-20: GDPR — Right to Erasure
The system shall support a GDPR "Right to Erasure" workflow. Candidates and employees may submit an erasure request through the candidate portal or via a support channel. Upon validation, the system shall delete or anonymize all PII associated with the requesting person within 30 days. Anonymization shall replace identifiable fields with hashed tokens while retaining non-identifiable data (e.g., application outcomes without name/email) for aggregate analytics. Erasure events shall be logged in the audit log.

#### NFR-21: GDPR — Data Portability
Candidates shall be able to request a full export of their personal data in a machine-readable format (JSON) from the candidate portal. The export shall include: profile data, all applications, all communications received, interview history (excluding internal feedback), and consent records. The export shall be generated within 72 hours of the request.

#### NFR-22: GDPR — Consent Management
The system shall record explicit consent at the time of application for: (a) processing their application data, (b) retaining their data for future recruitment consideration (separate, opt-in consent), and (c) marketing communications. Consent records shall store the consent text version, IP address, timestamp, and method (checkbox, signature). Withdrawn consent shall suppress future marketing emails and flag the candidate record for data retention review.

#### NFR-23: EEO/OFCCP Compliance
The system shall capture OFCCP Internet Applicant data (IARs) for all positions that meet Internet Applicant criteria. Disposition codes shall be recorded at every pipeline stage exit, supporting OFCCP audit readiness. EEO-1 data shall be collected through voluntary self-identification forms, stored separately from applicant screening data, and accessible only to HR Admins. The system shall never expose EEO data to AI ranking models.

#### NFR-24: Pay Transparency Law Compliance
The salary range display logic (FR-04) shall be kept current with applicable state and national pay transparency legislation. The platform shall maintain a jurisdiction compliance matrix (updated quarterly) that maps job posting locations to applicable laws and enforces mandatory disclosure rules automatically.

---

### 3.6 Accessibility

#### NFR-25: WCAG 2.1 AA Compliance
All customer-facing interfaces (candidate portal, recruiter dashboard, careers page widget) shall conform to WCAG 2.1 Level AA. This includes: sufficient color contrast ratios (4.5:1 for normal text), full keyboard navigability, screen reader compatibility (ARIA labels on all interactive elements), skip navigation links, visible focus indicators, and no content that flashes more than 3 times per second. Automated accessibility tests shall be run in CI using axe-core or Lighthouse.

---

### 3.7 Integrations

#### NFR-26: OAuth 2.0 for Calendar Integrations
Calendar integrations (Google Calendar, Microsoft Outlook) shall use OAuth 2.0 Authorization Code Flow. The platform shall store refresh tokens securely and handle token rotation automatically. Users shall be able to revoke calendar access from within their profile settings, which shall immediately invalidate the stored tokens.

#### NFR-27: Webhook-Based Job Board Sync
Job board integrations shall support webhook-based notifications for board-initiated events (e.g., job expired, application received via the board). Incoming webhooks shall be verified using the board's signing secret. Webhook events shall be idempotent — duplicate deliveries shall not create duplicate records.

#### NFR-28: REST API for Third-Party Integration
The platform shall expose a documented REST API (OpenAPI 3.0 specification) for enterprise customers to integrate with internal HRIS systems. API access shall require API key authentication with per-key rate limiting (1,000 requests per minute per key). The API shall support at minimum: job posting CRUD, application retrieval, pipeline stage updates, and candidate data export.

---

## 4. Constraints and Assumptions

### 4.1 Constraints

1. **Multi-tenancy:** The platform must support multiple companies on a shared infrastructure; single-tenant deployments are out of scope for v1.
2. **Browser Support:** The platform must support the last two major versions of Chrome, Firefox, Safari, and Edge. Internet Explorer is not supported.
3. **Mobile:** The candidate portal must be fully functional on mobile browsers. The recruiter dashboard must be usable (not necessarily full-featured) on tablet-sized screens (768px+).
4. **File Size:** Resume and document file size limits are capped at 10 MB per file. Total document storage per tenant shall be limited by the subscription plan.
5. **Email Deliverability:** The platform shall use a third-party email delivery service (SendGrid) and shall not attempt to deliver email directly via SMTP. Email templates shall comply with CAN-SPAM and GDPR opt-out requirements.
6. **Job Board API Terms:** Integration behaviour shall comply with each job board's API terms of service. Automated scraping of job boards is prohibited; only official API integrations shall be used.

### 4.2 Assumptions

1. Enterprise customers will provide their own DocuSign or HelloSign accounts and API credentials for e-signature functionality. The platform will proxy the signing workflow but not provide signing capacity from its own account.
2. Checkr API access will be provisioned per tenant after the tenant completes Checkr's permissible purpose agreement directly with Checkr.
3. The platform assumes candidates have valid email addresses as the primary communication channel. SMS notifications are a stretch goal for a future release.
4. AI resume ranking scores are advisory and will always be surfaced as a secondary signal, never as the sole automated decision-maker. The platform explicitly discloses the use of AI ranking on the job application page.
5. HR Admins for each tenant are responsible for maintaining their own EEO job categories and pay grades. The platform provides the tools; accuracy of categorization is the tenant's responsibility.
6. Initial launch targets English-language UI. Internationalization (i18n) framework will be implemented from the start to facilitate future language additions, but non-English locales are out of scope for v1.
