# Activity Diagrams — Survey and Feedback Platform

## Overview

This document presents six activity diagrams that model the key operational flows of the Survey and Feedback Platform. Each diagram uses Mermaid flowchart TD (top-down) syntax to represent process steps, decision gates, parallel execution paths, and start/end states. Together these diagrams provide developers, QA engineers, and business analysts with a precise visual reference for implementing and testing the platform's core workflows.

Activity diagrams map directly to the use cases defined in `analysis/use-case-diagram.md` and the detailed descriptions in `analysis/use-case-descriptions.md`. Decision nodes with Yes/No branches correspond to business rules documented in those files.

**Notation Guide:**
- `([...])` — Start / End terminal node
- `[...]` — Activity / Process step
- `{...}` — Decision gate (diamond)
- `[[...]]` — Subprocess / called activity

---

## 1. Survey Creation Flow

This flow covers the complete path from a Survey Creator logging into the platform through building a survey and publishing it for distribution. It models the primary success scenario with key decision branches for authentication method, template vs. scratch creation, question logic, and pre-publication validation.

```mermaid
flowchart TD
    A([Start]) --> B[Navigate to Platform URL]
    B --> C{Already\nAuthenticated?}
    C -- No --> D{Auth Method?}
    D -- Email/Password --> E[Enter Credentials]
    D -- OAuth SSO --> F[Redirect to Google/Microsoft]
    D -- Magic Link --> G[Request Magic Link Email]
    F --> H[OAuth Callback — Validate Token]
    G --> I[Click Link in Email]
    E --> J[POST /auth/login — Validate JWT]
    H --> J
    I --> J
    J --> K{Credentials\nValid?}
    K -- No --> L[Display Auth Error]
    L --> B
    K -- Yes --> M[Load Workspace Dashboard]
    C -- Yes --> M
    M --> N[Click New Survey]
    N --> O{Start Method?}
    O -- From Scratch --> P[Enter Survey Title and Description]
    O -- From Template --> Q[Open Template Library]
    Q --> R[Browse and Preview Template]
    R --> S[Click Use This Template]
    S --> T[Deep-Copy Template to New Draft Survey]
    T --> U[Open Survey Builder — Pre-Populated]
    P --> V[Configure Global Settings\nlanguage, theme, progress bar]
    V --> W[Save Draft Survey — POST /surveys]
    U --> W
    W --> X[Add Question — Select Type]
    X --> Y[Enter Question Text and Options]
    Y --> Z{Add Conditional\nLogic?}
    Z -- Yes --> AA[Open Logic Builder]
    AA --> AB[Define Condition: If Answer → Action Target]
    AB --> AC{Circular Logic\nDetected?}
    AC -- Yes --> AD[Highlight Conflict — Block Save]
    AD --> AB
    AC -- No --> AE[Save Logic Rules]
    AE --> AF{Add Another\nQuestion?}
    Z -- No --> AF
    AF -- Yes --> X
    AF -- No --> AG[Preview Survey in Respondent View]
    AG --> AH{Preview\nAcceptable?}
    AH -- No --> AI[Return to Builder — Edit Questions]
    AI --> X
    AH -- Yes --> AJ[Configure Distribution Settings\nexpiry, quota, anonymous mode]
    AJ --> AK[Click Publish and Distribute]
    AK --> AL{Pre-Publication\nValidation Pass?}
    AL -- No --> AM[Display Validation Errors]
    AM --> AI
    AL -- Yes --> AN[Transition Survey to Active Status]
    AN --> AO[Launch Distribution Wizard]
    AO --> AP([End — Survey Live])
```

---

## 2. Survey Response Submission Flow

This flow models the complete respondent journey from receiving a survey link through completing and submitting the response. It includes conditional logic routing, partial save behaviour, file upload handling, and offline resilience.

```mermaid
flowchart TD
    A([Start — Respondent Opens Survey Link]) --> B[System Validates Link Token]
    B --> C{Link Valid?}
    C -- Expired --> D[Display: Survey Closed Page]
    D --> ZZ([End])
    C -- Quota Reached --> E[Display: Max Responses Reached]
    E --> ZZ
    C -- Already Used --> F[Display: Already Submitted]
    F --> ZZ
    C -- Valid --> G{Partial Response\nExists?}
    G -- Yes --> H[Prompt: Continue or Start Over?]
    H -- Continue --> I[Load Partial Response State]
    H -- Start Over --> J[Initialize Fresh Response Session]
    G -- No --> J
    I --> K[Render Survey at Last Unanswered Question]
    J --> L[Render Survey Page 1]
    K --> M[Respondent Answers Current Question]
    L --> M
    M --> N[Auto-Save Answer — Debounce 3s]
    N --> O{Question Has\nConditional Logic?}
    O -- Yes --> P[Evaluate Logic Rules Client-Side]
    P --> Q{Logic Action?}
    Q -- Show Next --> R[Show Target Question]
    Q -- Skip to Page --> S[Jump to Target Page]
    Q -- End Survey --> T[Jump to Submit Screen]
    R --> U{More Questions\non This Page?}
    S --> U
    O -- No --> U
    U -- Yes --> M
    U -- No --> V{More Pages?}
    V -- Yes --> W[Show Next Page Button]
    W --> X{All Required Questions\nAnswered?}
    X -- No --> Y[Highlight Unanswered Fields]
    Y --> M
    X -- Yes --> AA[Navigate to Next Page]
    AA --> M
    V -- No --> T
    T --> AB{File Upload\nQuestion Present?}
    AB -- Yes --> AC[Upload File to S3 via Pre-Signed URL]
    AC --> AD{Upload\nSucceeded?}
    AD -- No --> AE[Show Upload Error — Retry]
    AE --> AC
    AD -- Yes --> AF[Final Validation — All Required Answered]
    AB -- No --> AF
    AF --> AG{Validation\nPass?}
    AG -- No --> AH[Highlight Missing Answers]
    AH --> M
    AG -- Yes --> AI[Submit Response — POST /responses]
    AI --> AJ{Submission\nSucceeded?}
    AJ -- No --> AK[Cache in IndexedDB — Retry with Backoff]
    AK --> AL{Max Retries\nReached?}
    AL -- No --> AI
    AL -- Yes --> AM[Show: Saved Locally Message]
    AM --> ZZ
    AJ -- Yes --> AN[Display Thank-You Page]
    AN --> AO[Publish response.submitted to Kinesis]
    AO --> AP[Enqueue Webhook Delivery Tasks]
    AP --> ZZ([End — Response Recorded])
```

---

## 3. Email Distribution Campaign Flow

This flow covers the full lifecycle of an email distribution campaign: from the Creator initiating distribution through audience selection, scheduling, sending, and delivery event processing.

```mermaid
flowchart TD
    A([Start — Creator Clicks Publish and Distribute]) --> B[Pre-Publication Survey Validation]
    B --> C{Validation\nPass?}
    C -- No --> D[Display Itemized Error List]
    D --> E[Return to Survey Builder]
    E --> ZZ([End — Not Published])
    C -- Yes --> F[Transition Survey to Active Status]
    F --> G[Open Distribution Wizard — Step 1: Audience]
    G --> H{Select Segment\nor Create New?}
    H -- Create New --> I[Open Create Segment Dialog]
    I --> J[Upload CSV or Define Filter]
    J --> K[Validate and Import Contacts]
    K --> L[Return Segment with Contact Count]
    L --> M[Wizard Step 2: Email Content]
    H -- Existing Segment --> M
    M --> N[Enter Email Subject Line]
    N --> O[Customize Email Body — Optional]
    O --> P[Preview Email Rendering]
    P --> Q[Wizard Step 3: Schedule]
    Q --> R{Send Timing?}
    R -- Send Now --> S[Set send_at = now]
    R -- Schedule --> T[Configure Date and Time in UTC]
    T --> U[Create Campaign — status = scheduled]
    S --> V[Create Campaign Record in DB]
    U --> W[Celery Beat Schedules Send Task]
    W --> X{Scheduled Time\nReached?}
    X -- Not Yet --> X
    X -- Yes --> Y[Dequeue Campaign Send Task]
    V --> Y
    Y --> AA[Fetch Active Contacts from Segment]
    AA --> AB[Exclude Unsubscribed and Bounced Contacts]
    AB --> AC[Render Per-Recipient Email with Unique Token]
    AC --> AD[Batch Dispatch via AWS SES]
    AD --> AE{SES Daily\nQuota Remaining?}
    AE -- No --> AF[Queue Overflow — Resume at 00:00 UTC]
    AF --> AE
    AE -- Yes --> AG[SES Delivers Emails]
    AG --> AH[SNS Delivery Events → Webhook Receiver]
    AH --> AI{Event Type?}
    AI -- Sent --> AJ[Update delivery_status = sent]
    AI -- Opened --> AK[Update opened_at Timestamp]
    AI -- Bounced Hard --> AL[Suppress Email Globally]
    AL --> AM[Update delivery_status = bounced]
    AI -- Unsubscribed --> AN[Suppress Email Globally]
    AN --> AO[Update delivery_status = unsubscribed]
    AJ --> AP{All Recipients\nProcessed?}
    AK --> AP
    AM --> AP
    AO --> AP
    AP -- No --> AG
    AP -- Yes --> AQ{Reminder\nConfigured?}
    AQ -- Yes --> AR{48 Hours Since\nOriginal Send?}
    AR -- No --> AR
    AR -- Yes --> AS[Send Reminder to Non-Respondents — Max 2x]
    AS --> AT[Create Reminder Campaign Record]
    AT --> AC
    AQ -- No --> AU[Mark Campaign as Completed]
    AU --> AV([End — Campaign Complete])
```

---

## 4. Report Generation Flow

This flow models the asynchronous report generation pipeline: from the Analyst requesting a report through data aggregation, chart rendering, PDF/Excel composition, S3 upload, and download delivery.

```mermaid
flowchart TD
    A([Start — Actor Clicks Export Report]) --> B{Feature Available\nfor Plan?}
    B -- No --> C[Display Upgrade Prompt]
    C --> ZZ([End])
    B -- Yes --> D[Display Export Configuration Dialog]
    D --> E[Select Format: PDF or Excel]
    E --> F[Configure Date Range and Filters]
    F --> G[Toggle Include Charts and Raw Table]
    G --> H[Click Generate Report]
    H --> I[POST /reports/generate — Receive job_id]
    I --> J[Show Progress Indicator in UI]
    J --> K[Celery Worker Picks Up Report Job]
    K --> L[Query Filtered Responses from PostgreSQL]
    L --> M{Large Dataset?\nOver 10k responses}
    M -- Yes --> N[Stream Data in Batches of 1000]
    M -- No --> O[Load All Data into Memory]
    N --> P[Aggregate Summary Statistics]
    O --> P
    P --> Q{Format?}
    Q -- PDF --> R[Render Chart Images via Matplotlib]
    R --> S[Compose PDF Structure\nCover, TOC, Summary Cards]
    S --> T[Add Per-Question Sections with Charts]
    T --> U{Include Raw\nResponse Table?}
    U -- Yes --> V[Append Raw Response Appendix — Max 1000 rows]
    U -- No --> W[Apply Workspace Branding and Footer]
    V --> W
    W --> X[Finalize PDF via ReportLab]
    X --> Y{Size Over 50 MB?}
    Y -- Yes --> Z[Re-Render Charts at Lower DPI]
    Z --> X
    Y -- No --> AA[Upload to S3 — workspace/exports/]
    Q -- Excel --> AB[Create XLSX Workbook via openpyxl]
    AB --> AC[Write Summary Sheet]
    AC --> AD[Write Per-Question Data Sheets]
    AD --> AE[Write Raw Responses Sheet]
    AE --> AA
    AA --> AF{S3 Upload\nSucceeded?}
    AF -- No --> AG[Retry Upload — Max 3 Attempts]
    AG --> AH{Retry\nExhausted?}
    AH -- Yes --> AI[Mark Job Failed — Notify Actor via Email]
    AI --> ZZ
    AH -- No --> AA
    AF -- Yes --> AJ[Update Job Record — status = complete]
    AJ --> AK[Send WebSocket Event to Actor UI]
    AK --> AL[UI Shows Download Button]
    AL --> AM[Actor Clicks Download]
    AM --> AN[Generate Pre-Signed S3 URL — 30 min TTL]
    AN --> AO[Browser Downloads File]
    AO --> AP[Log Export Event to Audit Trail]
    AP --> ZZ([End — Report Downloaded])
```

---

## 5. User Registration and Workspace Setup Flow

This flow covers new user onboarding: from initial registration through email verification, workspace creation, team invitation, and subscription plan configuration.

```mermaid
flowchart TD
    A([Start — User Visits Registration Page]) --> B{Registration\nMethod?}
    B -- Email/Password --> C[Enter Name, Email, Password]
    C --> D[Validate Password Strength\nMin 8 chars, 1 uppercase, 1 number]
    D --> E{Password\nStrong Enough?}
    E -- No --> F[Display Password Requirements]
    F --> C
    E -- Yes --> G[POST /auth/register — Create Pending User]
    G --> H[Send Email Verification Link via SES]
    H --> I[User Clicks Verification Link]
    I --> J[Validate Email Verification Token]
    J --> K{Token Valid\nand Not Expired?}
    K -- No --> L[Display: Link Expired — Resend Option]
    L --> H
    K -- Yes --> M[Activate User Account]
    B -- OAuth SSO --> N[Redirect to Google or Microsoft]
    N --> O[OAuth Callback — Exchange Code for Token]
    O --> P[Extract Email and Profile from ID Token]
    P --> Q{User Already\nRegistered?}
    Q -- Yes --> R[Log In Existing User]
    R --> ZZ([End — Logged In])
    Q -- No --> M
    M --> S[Redirect to Workspace Creation Screen]
    S --> T[Enter Workspace Name and Select Industry]
    T --> U[Upload Workspace Logo — Optional]
    U --> V[POST /workspaces — Create Workspace Record]
    V --> W[Set Admin Role for Registering User]
    W --> X[Display Team Invitation Screen]
    X --> Y{Invite Team\nMembers Now?}
    Y -- Skip --> AA[Proceed to Plan Selection]
    Y -- Yes --> AB[Enter Team Member Emails and Roles]
    AB --> AC[Send Invitation Emails via SES]
    AC --> AD{More Members\nto Invite?}
    AD -- Yes --> AB
    AD -- No --> AA
    AA --> AE[Display Plan Comparison: Starter / Growth / Enterprise]
    AE --> AF{Select Plan?}
    AF -- Starter Free --> AG[Activate Starter Plan — No Payment]
    AF -- Growth --> AH[Open Stripe Checkout — Enter Card]
    AH --> AI[Stripe Processes Payment]
    AI --> AJ{Payment\nSucceeded?}
    AJ -- No --> AK[Display Payment Error — Retry]
    AK --> AH
    AJ -- Yes --> AL[Activate Growth Plan — Update Subscription]
    AG --> AM[Display Workspace Dashboard — Onboarding Checklist]
    AL --> AM
    AM --> AN[Show Quick-Start Wizard]
    AN --> ZZ([End — Workspace Ready])
```

---

## 6. Webhook Delivery Flow

This flow models the full webhook delivery pipeline: from a triggering event through payload construction, HMAC signing, HTTP delivery, retry logic on failure, and automatic deactivation after repeated failures.

```mermaid
flowchart TD
    A([Start — response.submitted Event Fired]) --> B[Query Active Webhooks for Workspace]
    B --> C{Any Webhooks\nConfigured?}
    C -- No --> ZZ([End — No Delivery Needed])
    C -- Yes --> D[For Each Webhook: Create Delivery Task]
    D --> E[Serialize Response Payload as JSON]
    E --> F[Add Event Metadata\nevent_type, timestamp, survey_id]
    F --> G[Compute HMAC-SHA256 Signature]
    G --> H[Set X-Survey-Signature Header]
    H --> I[Set X-Survey-Event Header]
    I --> J[Attempt HTTP POST to webhook.url]
    J --> K{HTTP Response\nStatus?}
    K -- 2xx Success --> L[Mark Delivery Attempt = success]
    L --> M[Update Last Success Timestamp]
    M --> ZZ
    K -- Timeout --> N[Mark Attempt = failed]
    K -- 4xx Error --> N
    K -- 5xx Error --> N
    K -- Connection Error --> N
    N --> O[Increment failure_count]
    O --> P{failure_count\n>= 5?}
    P -- Yes --> Q[Deactivate Webhook — status = inactive]
    Q --> R[Send Alert Email to Workspace Admin]
    R --> ZZ
    P -- No --> S{Determine Retry\nDelay by Attempt}
    S -- Attempt 1 --> T[Wait 30 Seconds]
    S -- Attempt 2 --> U[Wait 2 Minutes]
    S -- Attempt 3 --> V[Wait 10 Minutes]
    S -- Attempt 4 --> W[Wait 1 Hour]
    S -- Attempt 5 --> X[Wait 24 Hours]
    T --> Y[Re-Enqueue Celery Retry Task]
    U --> Y
    V --> Y
    W --> Y
    X --> Y
    Y --> J
```

---

## Flow Descriptions

### 1. Survey Creation Flow
The survey creation flow begins with the Creator authenticating (via credentials, OAuth SSO, or magic link) and ends with the survey being transitioned to `active` and the Distribution Wizard launched. Key branches include choosing between scratch creation and template import, adding conditional logic (with circular-loop detection), previewing the survey, and passing pre-publication validation. Auto-save is an implicit background activity throughout the builder session.

### 2. Survey Response Submission Flow
This flow handles the full lifecycle of a single respondent session. The system validates the link token against multiple failure conditions before rendering the survey. Conditional logic is evaluated client-side in real time. The auto-save mechanism (debounced at 3 seconds per answer) enables partial response recovery. The final submission includes file upload completion, full validation, database transaction, Kinesis event publication, and asynchronous webhook delivery.

### 3. Email Distribution Campaign Flow
The distribution flow manages the complete email campaign lifecycle. It integrates with AWS SES for delivery and processes SES event callbacks (delivered, opened, clicked, bounced, unsubscribed) to maintain delivery status at the per-recipient level. The flow handles daily send quota enforcement with automatic overflow queuing and supports up to two reminder sends per recipient.

### 4. Report Generation Flow
Report generation is an entirely asynchronous flow coordinated by Celery. The web request initiates the job and returns immediately with a `job_id`; the UI polls via WebSocket for completion. The worker handles both PDF and Excel formats, manages large datasets through streaming pagination, enforces a 50 MB PDF size ceiling through DPI reduction, and delivers the file via a time-limited S3 pre-signed URL.

### 5. User Registration and Workspace Setup Flow
This flow covers two registration paths (email/password and OAuth SSO) and merges at the point of workspace creation. The onboarding wizard is designed for progressive commitment: team invitations and plan selection are optional during initial setup but are surfaced via the post-setup checklist. Stripe payment integration handles plan upgrades with immediate activation on successful payment.

### 6. Webhook Delivery Flow
Webhook delivery is decoupled from the response submission path via Celery. The delivery pipeline builds a signed payload and executes the HTTP POST. On failure, it implements a five-stage exponential backoff schedule (30s → 2min → 10min → 1hr → 24hr). After five consecutive failures, the webhook is automatically deactivated to protect consumer endpoints from continued failed requests, and the Workspace Admin is notified.

---

## Exception Paths

### Authentication Exceptions
- **Expired magic link:** The system prompts the user to request a new magic link. Previous link tokens are invalidated immediately upon reuse attempt.
- **OAuth provider unavailable:** If Google or Microsoft OAuth is unreachable, the system falls back to showing the email/password form with a notice about SSO unavailability.
- **Brute-force lockout:** After 10 failed login attempts within 15 minutes, the account is locked for 30 minutes. An unlock email is sent automatically.

### Survey Submission Exceptions
- **Survey deleted during active session:** If the survey is deleted by the Creator while a respondent is mid-completion, the next page load returns a 404 and the respondent is shown a "Survey no longer available" message.
- **File upload S3 pre-signed URL expired:** Pre-signed upload URLs expire after 15 minutes. If expired, the system generates a fresh URL and retries the upload transparently.
- **Concurrent submission conflict:** If two tabs submit the same token simultaneously, the second submission receives a 409 Conflict response and is shown the "already submitted" message.

### Distribution Exceptions
- **Segment contacts all suppressed:** If all contacts in the target segment are suppressed (unsubscribed or bounced), the campaign is created with `status = completed` immediately and the Creator is notified that zero emails were sent.
- **SES account suspended:** If AWS SES suspends the workspace's sending identity, all outbound email tasks are paused and the Workspace Admin receives an urgent notification with remediation steps.

### Webhook Exceptions
- **DNS resolution failure:** Treated as a connection error; triggers the retry backoff schedule.
- **Payload size exceeds 1 MB:** The system truncates open-text answer fields to 500 characters in the webhook payload. A `truncated: true` flag is included in the payload metadata.
- **Signing secret rotated during delivery:** If the signing secret is rotated, in-flight deliveries use the old secret. Retries use the current secret.

---

## Operational Policy Addendum

### 1. Response Data Privacy Policies

Activity flows involving response collection (Flow 2) must comply with the workspace's data processing configuration. When a survey is configured for anonymous responses, the geolocation capture step in Flow 2 is bypassed entirely — the system sets both IP address and location fields to `null` before persisting the response record. The auto-save partial response mechanism stores only question IDs and answer values; no PII is written to the partial save record for anonymous surveys.

For non-anonymous surveys, the IP address captured during submission is used solely for geographic analytics and is stored in truncated form (/24 prefix for IPv4, /48 prefix for IPv6) unless the workspace has explicitly opted into full IP logging for fraud prevention purposes. Full IP storage requires explicit GDPR documentation within the workspace's privacy policy configuration.

Data collected through embedded survey widgets (Flow 6 configuration) is subject to the same response privacy rules as direct-link submissions. The embed origin domain is recorded as metadata but is not exposed in analytics views accessible to Analysts.

### 2. Survey Distribution Policies

The email distribution flow (Flow 3) enforces CAN-SPAM and GDPR compliance at the infrastructure level. The platform's SES sending configuration includes a `List-Unsubscribe` header in every email, enabling one-click unsubscribe in supported email clients (Gmail, Outlook) independent of the unsubscribe link embedded in the email body.

Scheduled campaigns may be cancelled by the Creator up to 5 minutes before the scheduled send time. Cancellations within the 5-minute window may result in partial delivery if Celery workers have already begun enqueuing individual email tasks. In this case, the campaign status is updated to `partially_cancelled` and the Creator is shown the final delivery count.

Distribution to internal employees is subject to the same suppression rules as external distribution. Employees who have unsubscribed from survey emails cannot be force-resubscribed by a Workspace Admin; only the employee can re-subscribe via their notification preferences.

### 3. Analytics and Retention Policies

The report generation flow (Flow 4) produces artifacts subject to the following retention policy: generated PDF and Excel files are stored in S3 under the `[workspace-id]/exports/` prefix with a lifecycle rule that permanently deletes files after 30 days. The job record in PostgreSQL is retained for the same 30-day period as an auditable history of export activity. Pre-signed download URLs are valid for 30 minutes from generation; after expiry, the Analyst must regenerate the URL from the export history page.

Aggregated analytics data (DynamoDB) is retained independently of the export lifecycle and is available for dashboard queries for the full retention period defined by the workspace's subscription tier. Deletion of a survey does not immediately purge its aggregated analytics; a 30-day grace period applies to allow Admins to export data before it is purged.

### 4. System Availability Policies

All six activity flows have been designed with graceful degradation in mind. The response submission flow (Flow 2) is the highest-priority flow and is protected by an independent Redis-backed submission queue that accepts writes even when the primary PostgreSQL database is under maintenance. Writes queued in Redis are replayed to PostgreSQL within 5 minutes of database restoration.

The webhook delivery flow (Flow 6) operates entirely within the Celery worker fleet, which is separate from the web API fleet. This ensures that high webhook delivery load does not affect survey rendering or submission API response times. Worker auto-scaling is configured to add Celery workers when the queue depth exceeds 10,000 pending tasks for more than 60 seconds.

Report generation workers (Flow 4) are isolated on a dedicated Celery queue (`report-generation`) with a maximum concurrency of 10 workers per workspace to prevent any single workspace from monopolizing generation capacity. Jobs that exceed the 10-minute timeout are automatically retried once with a reduced dataset (last 30 days of data) and the actor is notified of the scope reduction.
