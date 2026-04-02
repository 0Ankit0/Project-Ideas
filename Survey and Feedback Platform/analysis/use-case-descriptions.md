# Use-Case Descriptions — Survey and Feedback Platform

## Overview

This document provides structured, detailed descriptions of the fifteen most critical use cases identified for the Survey and Feedback Platform. Each entry follows a standardized template that captures actor interactions, preconditions, step-by-step scenarios, alternative and exception flows, business rules, and non-functional requirements. These descriptions serve as the authoritative reference for developers, QA engineers, and product owners during implementation and verification.

The use cases covered here (UC-001 through UC-015) represent the core functional backbone of the platform — from survey authoring and distribution through response collection, analytics, and compliance management.

---

## UC-001: Create Survey from Scratch

**Use Case ID:** UC-001
**Use Case Name:** Create Survey from Scratch
**Actor(s):** Survey Creator

**Preconditions:**
- The Survey Creator is authenticated and holds an active session token.
- The Creator has the `creator` or `admin` role within the target workspace.
- The workspace subscription allows at least one additional active survey (quota not exceeded).

**Postconditions:**
- A new survey record is persisted in the PostgreSQL `surveys` table with status `draft`.
- A default first page is created in the `survey_pages` table linked to the survey.
- The survey is visible in the Creator's survey list under "My Surveys."
- An audit log entry is written recording the creation event, timestamp, and actor ID.

**Main Success Scenario:**
1. Creator navigates to the workspace dashboard and clicks **New Survey**.
2. System displays a modal with two options: *Start from Scratch* and *Use Template*. Creator selects **Start from Scratch**.
3. System renders the Survey Builder interface with an empty canvas showing one default page and a title field.
4. Creator enters a survey title (1–200 characters) and optionally a description (0–1000 characters).
5. Creator configures global survey settings: language, theme color, progress bar display, and back-button visibility.
6. Creator clicks **Save Draft**.
7. System validates that the title is not empty and within character limits.
8. System persists the survey record with `status = draft`, `created_at = now()`, and `created_by = creator_id`.
9. System returns the survey's unique `survey_id` and redirects the Creator to the question editor for the newly created survey.
10. System writes an audit log entry: `action=survey.created, survey_id=<id>, actor=<creator_id>`.

**Alternative Flows:**
- **AF-001a — Auto-save enabled:** If the Creator has not clicked Save Draft but the workspace has auto-save enabled, the system silently persists the draft every 30 seconds after the first keystroke, displaying a "Saved" indicator in the toolbar. No user action required.
- **AF-001b — Title already used:** If a survey with the same title already exists in the workspace, the system shows an inline warning banner ("A survey with this title already exists") but does not block creation. Creator may proceed with duplicate title.

**Exception Flows:**
- **EF-001a — Subscription quota exceeded:** If the workspace has reached the maximum active survey limit for its plan, the system displays a blocking modal: "You've reached your survey limit. Upgrade to create more surveys." The form is disabled until the Workspace Admin upgrades the plan.
- **EF-001b — Database write failure:** If the persistence call fails (network error, DB timeout), the system displays a toast notification: "Failed to save survey. Please try again." The form state is preserved in the browser's local storage for up to 24 hours so the Creator can retry without losing data.
- **EF-001c — Session expired mid-creation:** If the Creator's session expires during form filling, the system intercepts the save attempt, displays a login modal, and resumes the save after re-authentication.

**Business Rules:**
- BR-001.1: Survey title is mandatory and must be between 1 and 200 characters.
- BR-001.2: A workspace on the Starter plan may not have more than 5 active surveys simultaneously.
- BR-001.3: All new surveys are created in `draft` status; they cannot receive responses until explicitly published.
- BR-001.4: Survey creation is workspace-scoped; a Creator cannot create surveys outside their assigned workspace.

**Non-Functional Requirements:**
- The survey creation POST endpoint must respond within 300 ms at the 95th percentile under normal load.
- The Survey Builder UI must render completely within 1.5 seconds on a 4G mobile connection.
- Draft auto-save must not cause perceptible UI lag; the save operation must be executed asynchronously in a background microtask.

---

## UC-002: Add Question with Conditional Logic

**Use Case ID:** UC-002
**Use Case Name:** Add Question with Conditional Logic
**Actor(s):** Survey Creator

**Preconditions:**
- A survey in `draft` or `paused` status exists and is open in the Survey Builder.
- The Creator is authenticated and has write access to the survey.

**Postconditions:**
- A new question record is persisted in the `survey_questions` table with correct `page_id`, `position`, and `question_type`.
- If conditional logic was configured, one or more `logic_rules` records are persisted referencing the question's `question_id`.
- The survey preview reflects the new question and conditional routing.

**Main Success Scenario:**
1. Creator clicks **+ Add Question** on the desired survey page.
2. System presents a question type picker: Single Choice, Multiple Choice, Short Text, Long Text, Rating Scale (1–10), NPS (0–10), Likert Scale, File Upload, Date/Time, Dropdown, Matrix/Grid, Slider.
3. Creator selects a question type (e.g., Single Choice).
4. Creator enters the question text and optional description/helper text.
5. For choice-based questions, Creator adds answer options (minimum 1, maximum 50 per question).
6. Creator marks the question as required or optional.
7. Creator opens the **Logic** panel and clicks **Add Logic Rule**.
8. System displays a condition builder: *If [answer to this question] [operator] [value] → [action: show/skip/end survey] [target question/page]*.
9. Creator configures: "If answer is Option A → Skip to Question 5."
10. Creator may add up to 10 logic rules per question using AND/OR combinators.
11. Creator clicks **Save Question**.
12. System validates the question structure: required fields present, options have non-empty text, logic rule targets exist within the survey.
13. System persists the question and logic rules; recalculates question positions on the page.
14. System updates the live preview to show the new question in its correct position.

**Alternative Flows:**
- **AF-002a — Duplicate question:** Creator may right-click an existing question and select *Duplicate*, which creates an identical question (including options) at the next position. Logic rules are not duplicated.
- **AF-002b — Drag-and-drop reorder:** Creator may drag questions to new positions. System recalculates `position` values for all affected questions and persists the updated order in a single batch update.
- **AF-002c — Multi-page surveys:** Creator may add a page break between questions, grouping questions into pages. Conditional logic may target entire pages as skip targets.

**Exception Flows:**
- **EF-002a — Circular logic detected:** If a logic rule would create an infinite loop (e.g., Q3 shows Q5 which shows Q3), the system highlights the conflicting rules in red and displays: "Circular logic detected. Please review your rules." Saving is blocked until the conflict is resolved.
- **EF-002b — Target question deleted:** If a question referenced by a logic rule is subsequently deleted, the system marks the orphaned rule with a warning badge and presents the Creator with options to update or remove the rule at next save.
- **EF-002c — Option limit exceeded:** If the Creator attempts to add more than 50 options to a single choice question, the system disables the "Add Option" button and shows a tooltip: "Maximum 50 options allowed."

**Business Rules:**
- BR-002.1: Every question must have non-empty question text (max 1,000 characters).
- BR-002.2: Answer options for choice questions must each be non-empty and unique within the question (case-insensitive).
- BR-002.3: Conditional logic rules cannot reference questions on earlier pages (forward-skip only).
- BR-002.4: NPS questions are limited to one per survey.
- BR-002.5: File Upload questions are only available on Growth and Enterprise plans.

**Non-Functional Requirements:**
- Logic validation must run client-side in real time as the Creator configures rules, with no server round-trip required until save.
- Question save operation must complete in under 500 ms at the 99th percentile.
- The logic rule builder UI must support keyboard navigation for accessibility compliance (WCAG 2.1 AA).

---

## UC-003: Publish and Distribute Survey via Email Campaign

**Use Case ID:** UC-003
**Use Case Name:** Publish and Distribute Survey via Email Campaign
**Actor(s):** Survey Creator

**Preconditions:**
- The survey is in `draft` status and has at least one question.
- The Creator has an active audience segment with at least one valid email contact.
- The workspace has a verified sender email identity (SES domain/email verification complete).
- Workspace subscription allows the required email send volume.

**Postconditions:**
- Survey status transitions from `draft` to `active`.
- An email campaign record is created in `distribution_campaigns` with delivery status tracking.
- Individual emails are queued in the Celery task queue for delivery via AWS SES.
- A distribution event is written to the audit log.

**Main Success Scenario:**
1. Creator completes the survey and clicks **Publish & Distribute** from the survey builder toolbar.
2. System runs pre-publication validation: checks at least one question exists, no unresolved logic warnings, title is set.
3. System displays the Distribution Wizard with three steps: *Audience*, *Email Content*, *Schedule*.
4. Creator selects an existing audience segment or creates a new one.
5. System displays the contact count for the selected segment and estimates email volume.
6. Creator customizes the email subject line and optional body text (or uses the default template).
7. Creator selects *Send Now* or *Schedule for Later* (date/time picker shown for scheduled sends).
8. Creator reviews the summary screen: survey title, audience size, sender identity, send time.
9. Creator clicks **Confirm and Send**.
10. System transitions survey to `active` status, creates the campaign record, and enqueues email tasks in Celery.
11. System displays a confirmation screen: "Your survey is live. Emails are being delivered."
12. Celery workers dequeue tasks, render per-recipient personalized emails with unique response links, and dispatch via SES.
13. SES delivery events (sent, bounced, opened, clicked) are streamed back via SNS → webhook receiver and update the campaign delivery table.

**Alternative Flows:**
- **AF-003a — Link-only distribution:** If Creator selects *Get Shareable Link* instead of email, system generates a UUID-based URL and skips the email campaign wizard. Survey is still published to `active`.
- **AF-003b — Scheduled send:** Campaign is created with `status = scheduled` and a Celery beat task fires at the configured UTC timestamp. Creator receives an in-app notification and email confirmation 15 minutes before send.
- **AF-003c — Segment updated post-schedule:** If contacts are added to the audience segment after the campaign is scheduled but before send time, the system includes the new contacts in the final send batch.

**Exception Flows:**
- **EF-003a — SES sending limit reached:** If the workspace's daily SES quota is exhausted, the system queues remaining emails and resumes delivery at 00:00 UTC. Creator is notified via in-app and email.
- **EF-003b — Survey validation failure:** If the pre-publication check finds unresolved issues (e.g., question with no options), the wizard is blocked with an itemized error list and a link back to the builder.
- **EF-003c — Sender identity not verified:** If the workspace sender email is not SES-verified, the system shows a blocking alert with instructions to complete SES domain verification. Distribution is disabled until resolved.

**Business Rules:**
- BR-003.1: A survey must have at least 1 question before it can be published.
- BR-003.2: The sender email identity must be verified in AWS SES before any distribution campaign can be sent.
- BR-003.3: Each recipient in an email campaign receives a unique, single-use survey link token.
- BR-003.4: Contacts marked as unsubscribed or bounced are automatically excluded from campaign delivery.
- BR-003.5: An email campaign cannot target more than 100,000 contacts in a single send on the Growth plan.

**Non-Functional Requirements:**
- Email campaign enqueue operation must complete in under 2 seconds for any audience size.
- Individual email rendering and SES dispatch must achieve a throughput of at least 5,000 emails per minute per workspace.
- Campaign delivery status must be queryable via the dashboard within 60 seconds of first SES delivery event.

---

## UC-004: Submit Survey Response (Respondent)

**Use Case ID:** UC-004
**Use Case Name:** Submit Survey Response
**Actor(s):** Respondent

**Preconditions:**
- The respondent has a valid survey link (public URL or email-embedded token link).
- The survey is in `active` status, has not expired, and has not reached its response quota.
- The respondent has not already submitted a response from the same link token (for token-bound links).

**Postconditions:**
- A response record is created in `survey_responses` with `status = completed`.
- All individual answer records are persisted in `response_answers`.
- A `response.submitted` event is published to the Kinesis Data Stream.
- Any configured webhooks are enqueued for delivery.
- The respondent sees a thank-you/confirmation screen.

**Main Success Scenario:**
1. Respondent opens the survey link in a browser.
2. System validates the link: checks survey `active` status, expiry, quota, and token uniqueness.
3. System renders the first survey page with question 1 visible.
4. Respondent answers each question following conditional logic; inapplicable questions are hidden automatically.
5. For multi-page surveys, respondent clicks **Next** to advance pages; system validates all required questions on the current page before allowing navigation.
6. On the final page, respondent reviews a summary (if configured) and clicks **Submit**.
7. System performs final validation: all required questions answered, file uploads completed, input formats valid.
8. System writes the response record and answer records in a database transaction.
9. System publishes a `response.submitted` event to Kinesis with the response ID and survey ID.
10. System displays the thank-you page (custom message configured by Creator, or platform default).
11. In the background, the Kinesis consumer Lambda updates aggregated analytics in DynamoDB.
12. Celery delivers any registered webhooks within 30 seconds.

**Alternative Flows:**
- **AF-004a — Anonymous survey:** No token validation is performed. Multiple submissions from the same browser/device are allowed unless the Creator has enabled browser-fingerprint deduplication.
- **AF-004b — Respondent uses back button:** Respondent may navigate back to previous pages. Previous answers are preserved and editable until final submission.
- **AF-004c — Language selection:** If the survey is configured for multiple languages, respondent sees a language selector at the start. The survey renders in the selected language.

**Exception Flows:**
- **EF-004a — Survey expired:** System displays a static page: "This survey is no longer accepting responses. It closed on [date]."
- **EF-004b — Quota reached:** System displays: "This survey has reached its maximum number of responses. Thank you for your interest."
- **EF-004c — Duplicate submission:** If the token has already been used, system displays: "You have already submitted a response to this survey."
- **EF-004d — Network failure during submission:** System retries the submission POST up to 3 times with exponential backoff. If all retries fail, the response is cached in the browser's IndexedDB and the user is shown: "Your response has been saved locally. Please try submitting again when you're back online."

**Business Rules:**
- BR-004.1: A single-use token-based link may only be used for one completed submission.
- BR-004.2: All questions marked as required must have a non-null, non-empty answer before submission is accepted.
- BR-004.3: File uploads in responses are stored in AWS S3 under the workspace's isolated bucket prefix.
- BR-004.4: Response submission is accepted only for surveys in `active` status.
- BR-004.5: Geolocation metadata (IP-derived country, region) is captured for all non-anonymous surveys.

**Non-Functional Requirements:**
- Survey page must render (LCP) within 2.5 seconds on a 3G connection.
- Response submission endpoint must handle 10,000 concurrent submissions without degradation.
- Kinesis event publication must be non-blocking; submission confirmation must not wait for analytics pipeline completion.

---

## UC-005: View Real-Time Analytics Dashboard

**Use Case ID:** UC-005
**Use Case Name:** View Real-Time Analytics Dashboard
**Actor(s):** Survey Creator, Analyst

**Preconditions:**
- The actor is authenticated with Creator or Analyst role in the workspace.
- The target survey has at least one submitted response.
- The actor has navigated to the survey's Analytics tab.

**Postconditions:**
- The dashboard is rendered with current metrics reflecting all responses up to 30 seconds prior.
- No mutations to response or survey data occur (read-only operation).

**Main Success Scenario:**
1. Actor selects a survey from their survey list and clicks the **Analytics** tab.
2. System fetches summary metrics from the DynamoDB analytics store: total responses, completion rate, average completion time, drop-off rate by question.
3. System renders the overview cards: Responses (total + trend sparkline), Completion Rate (%), Avg. Time (mm:ss), NPS Score (if applicable).
4. System renders per-question visualizations: bar charts for single/multiple choice, word clouds for open text, histograms for numeric ratings, geographic heatmap for location data.
5. Actor optionally applies filters: date range picker, audience segment selector, device type filter, answer-based filter (show only responses where Q2 = "Option A").
6. System re-queries DynamoDB with the filter parameters and re-renders all visualizations within 2 seconds.
7. Actor may click on any question chart to drill down into individual response-level data.
8. Dashboard auto-refreshes every 30 seconds while the tab is active (WebSocket subscription to real-time update channel).

**Alternative Flows:**
- **AF-005a — No responses yet:** System renders empty-state illustrations with messaging: "No responses yet. Share your survey to start collecting data."
- **AF-005b — Analyst role:** All controls are identical but the **Edit Survey** and **Delete Survey** buttons are absent from the page.
- **AF-005c — Export data:** Actor clicks **Export** and is redirected to the export dialog (UC-006).

**Exception Flows:**
- **EF-005a — DynamoDB query timeout:** If the analytics query exceeds 5 seconds, system displays a "Loading data..." skeleton and retries. If three consecutive retries fail, a banner displays: "Analytics are temporarily unavailable. Raw response data is still accessible via export."
- **EF-005b — WebSocket disconnect:** If the WebSocket connection drops, the system falls back to 60-second polling intervals and shows a small indicator: "Live updates paused."

**Business Rules:**
- BR-005.1: Analytics data may lag up to 30 seconds behind submission time due to Kinesis pipeline processing.
- BR-005.2: Analysts may not access analytics for surveys outside their workspace.
- BR-005.3: Word clouds for open-text questions exclude stop words and apply profanity filtering.
- BR-005.4: NPS gauge is only rendered if the survey contains an NPS question type.

**Non-Functional Requirements:**
- Initial dashboard render must complete within 1.5 seconds for surveys with fewer than 100,000 responses.
- Filter application must re-render the dashboard within 2 seconds at the 95th percentile.
- The WebSocket real-time channel must support 500 concurrent dashboard viewers per survey.

---

## UC-006: Export Survey Report as PDF

**Use Case ID:** UC-006
**Use Case Name:** Export Survey Report as PDF
**Actor(s):** Analyst, Survey Creator

**Preconditions:**
- The actor is authenticated with Analyst or Creator role.
- The target survey has at least one submitted response.
- The workspace subscription includes report export (not available on Starter free tier).

**Postconditions:**
- A PDF file is generated containing a formatted report with charts, summary statistics, and filtered data.
- The PDF is stored in AWS S3 under the workspace's export prefix.
- A pre-signed S3 URL with 30-minute TTL is returned to the actor for download.
- An export event is logged to the audit trail.

**Main Success Scenario:**
1. Actor opens the Analytics dashboard and clicks **Export Report**.
2. System presents the Export Report dialog with configuration options: *Format* (PDF / Excel), *Date Range*, *Include Charts* (toggle), *Include Raw Response Table* (toggle), *Apply Current Filters* (toggle).
3. Actor selects PDF format and configures options.
4. Actor clicks **Generate Report**.
5. System enqueues a report generation Celery task and immediately returns a `job_id`.
6. UI shows a progress indicator: "Generating your report… this may take up to 60 seconds."
7. Celery worker: queries filtered response data from PostgreSQL; renders chart images using server-side Matplotlib/ReportLab; composes the PDF with workspace branding, table of contents, executive summary, per-question sections with charts, and raw data appendix.
8. Celery uploads the finished PDF to S3 and updates the job record with `status = complete` and the S3 key.
9. System notifies the actor via WebSocket event; UI replaces the progress indicator with a **Download** button.
10. Actor clicks **Download**; system generates a pre-signed S3 URL and triggers browser download.

**Alternative Flows:**
- **AF-006a — Excel export:** Process is identical; worker generates an `.xlsx` file using `openpyxl` with separate sheets for summary, per-question data, and raw responses.
- **AF-006b — Scheduled report:** Workspace Admin may configure a recurring report (daily/weekly/monthly) that auto-generates and emails a download link to specified recipients.

**Exception Flows:**
- **EF-006a — Report generation timeout:** If the Celery task exceeds 10 minutes (large dataset), the job is marked `failed` and the actor receives an email with instructions to export with a narrower date range filter.
- **EF-006b — S3 upload failure:** System retries the S3 upload up to 3 times. On persistent failure, the actor is notified with an option to retry generation.
- **EF-006c — Feature not available on Starter:** System displays an upgrade prompt before the export dialog is shown.

**Business Rules:**
- BR-006.1: Exported PDFs include the workspace logo, survey title, export timestamp, and "Generated by [Platform Name]" footer.
- BR-006.2: Raw response table in PDF is capped at 1,000 rows to maintain file size; remainder is accessible via Excel export.
- BR-006.3: Pre-signed S3 download URLs expire after 30 minutes.
- BR-006.4: Export jobs are retained for 30 days in the job history; generated files are deleted after 30 days.

**Non-Functional Requirements:**
- PDF generation for a report with up to 10,000 responses must complete within 60 seconds.
- Generated PDF file size must not exceed 50 MB; if exceeded, charts are compressed to lower DPI.
- The export endpoint must respond within 200 ms (the actual generation is async).

---

## UC-007: Manage Team Members and Roles

**Use Case ID:** UC-007
**Use Case Name:** Manage Team Members and Roles
**Actor(s):** Workspace Admin

**Preconditions:**
- The actor is authenticated with the Workspace Admin role.
- The workspace has an active subscription.

**Postconditions:**
- The invited user receives an invitation email with a 48-hour accept link.
- Upon acceptance, a `workspace_members` record is created with the assigned role.
- Role changes are immediately reflected in the member's session permissions on next request (enforced server-side, not just UI).

**Main Success Scenario:**
1. Admin navigates to **Workspace Settings → Team Members**.
2. Admin clicks **Invite Member**.
3. Admin enters the invitee's email address and selects a role: Creator, Analyst, Admin.
4. Admin optionally adds a personal message to the invitation email.
5. Admin clicks **Send Invitation**.
6. System validates the email format and checks the invitee is not already a workspace member.
7. System creates a `workspace_invitations` record with a UUID token and 48-hour TTL.
8. Celery enqueues an invitation email task; SES delivers the email containing the accept link.
9. Invitee clicks the link, is directed to a registration/login page (if not already a platform user), and upon authentication, the invitation is accepted and the membership record is created.
10. Admin can see the new member in the team list with status "Active."

**Alternative Flows:**
- **AF-007a — Change role of existing member:** Admin clicks the role dropdown next to a member's name and selects a new role. System updates the `workspace_members` record immediately. A notification email is sent to the affected member.
- **AF-007b — Remove member:** Admin clicks *Remove* and confirms. System soft-deletes the membership record, revokes active sessions for that user in the workspace, and sends a removal notification email.
- **AF-007c — Resend invitation:** Admin may resend an expired or unopened invitation. System invalidates the previous token and issues a fresh 48-hour token.

**Exception Flows:**
- **EF-007a — Seat limit reached:** If the workspace has exhausted its seat quota for the current plan, the Invite button is disabled with a tooltip: "Member limit reached. Upgrade to add more team members."
- **EF-007b — Invitee already a member:** System displays: "This email address is already a member of this workspace."
- **EF-007c — Admin cannot remove themselves:** System prevents the last admin from removing their own admin role, displaying: "You are the only admin. Assign another admin before removing yourself."

**Business Rules:**
- BR-007.1: An invitation link expires after 48 hours.
- BR-007.2: A workspace must always have at least one member with the Admin role.
- BR-007.3: Seat limits are enforced per plan: Starter — 3 members, Growth — 15 members, Enterprise — unlimited.
- BR-007.4: Role changes take effect immediately server-side; the next API request by the affected member will reflect the new permissions.

**Non-Functional Requirements:**
- Invitation email must be delivered within 60 seconds of the invite action.
- Role change authorization check latency must not exceed 10 ms (cached in Redis).

---

## UC-008: Configure Webhook Integration

**Use Case ID:** UC-008
**Use Case Name:** Configure Webhook Integration
**Actor(s):** Workspace Admin

**Preconditions:**
- The actor is authenticated with the Workspace Admin role.
- The workspace subscription includes webhook integrations (Growth or Enterprise plan).

**Postconditions:**
- A `webhooks` record is created with the target URL, selected event triggers, and HMAC signing secret.
- The webhook is immediately active; future trigger events will be delivered to the configured URL.

**Main Success Scenario:**
1. Admin navigates to **Workspace Settings → Integrations → Webhooks**.
2. Admin clicks **Add Webhook**.
3. System displays the webhook configuration form.
4. Admin enters the target URL (must be HTTPS).
5. Admin selects trigger events from a checklist: `response.submitted`, `response.partial_saved`, `survey.published`, `survey.closed`.
6. System auto-generates a signing secret (32-byte hex); Admin may optionally replace it.
7. Admin clicks **Save Webhook**.
8. System validates the URL format and performs a test ping (HTTP POST with a `webhook.test` event payload) to verify the endpoint is reachable and returns HTTP 200.
9. System saves the webhook record and displays it in the webhook list with status "Active."
10. Admin can view the signing secret once and then it is masked. Admin may rotate the secret at any time.

**Alternative Flows:**
- **AF-008a — Test delivery:** Admin may click **Send Test Event** at any time to re-send a test payload to the configured URL and inspect the delivery result (HTTP status, response body, latency).
- **AF-008b — Disable webhook:** Admin may toggle a webhook to "Inactive" without deleting it, suspending delivery temporarily.

**Exception Flows:**
- **EF-008a — URL not reachable:** If the test ping fails (connection refused, DNS error, non-200 response), system displays: "Endpoint not reachable. Please verify the URL and ensure it returns HTTP 200 for POST requests." Saving is blocked.
- **EF-008b — Non-HTTPS URL:** System rejects HTTP URLs with: "Webhook URL must use HTTPS."
- **EF-008c — Webhook limit reached:** Growth plan allows up to 5 webhooks per workspace. If the limit is reached, the Add button is disabled.

**Business Rules:**
- BR-008.1: All webhook deliveries must be to HTTPS endpoints only.
- BR-008.2: All payloads are signed with HMAC-SHA256 using the signing secret; the signature is included in the `X-Survey-Signature` header.
- BR-008.3: Failed webhook deliveries are retried with exponential backoff: 30s, 2min, 10min, 1hr, 24hr (maximum 5 attempts).
- BR-008.4: After 5 consecutive delivery failures, the webhook is automatically deactivated and the Workspace Admin is notified.

**Non-Functional Requirements:**
- Webhook delivery must be initiated within 10 seconds of the trigger event.
- The delivery pipeline must handle 1,000 concurrent webhook deliveries per workspace.

---

## UC-009: Upgrade Subscription Plan

**Use Case ID:** UC-009
**Use Case Name:** Upgrade Subscription Plan
**Actor(s):** Workspace Admin

**Preconditions:**
- The actor is authenticated with Workspace Admin role.
- The workspace is currently on a lower-tier plan (Starter → Growth, or Growth → Enterprise).

**Postconditions:**
- The workspace subscription record is updated to the new plan.
- Stripe subscription is created or updated; a pro-rated invoice is generated.
- New plan features and limits are immediately available to all workspace members.
- A billing event is logged to the audit trail.

**Main Success Scenario:**
1. Admin navigates to **Workspace Settings → Billing**.
2. System displays the current plan, usage metrics (surveys used, members, responses), and available upgrade options.
3. Admin clicks **Upgrade to Growth** (or Enterprise).
4. System displays the plan comparison modal with pricing, feature differences, and the calculated pro-rated charge.
5. Admin enters or confirms payment method (credit card via Stripe Elements, or existing card on file).
6. Admin clicks **Confirm Upgrade**.
7. System calls the Stripe API to create or update the subscription.
8. Stripe processes the payment and returns a successful `payment_intent.succeeded` event via webhook.
9. System's Stripe webhook handler updates the `workspace_subscriptions` table to the new plan tier.
10. System sends a confirmation email with the invoice receipt.
11. Admin is returned to the Billing page showing the new plan status.

**Alternative Flows:**
- **AF-009a — Downgrade:** Admin may downgrade by selecting a lower plan. System calculates the credit for unused time and applies it to the next billing cycle. Downgrade takes effect at the end of the current billing period.
- **AF-009b — Enterprise custom quote:** For Enterprise, Admin fills a contact form; Sales team follows up. No immediate plan change occurs.

**Exception Flows:**
- **EF-009a — Payment declined:** If Stripe returns a payment failure, system displays the Stripe error message and prompts for a new payment method. No plan change occurs.
- **EF-009b — Stripe webhook delay:** If the `payment_intent.succeeded` event is delayed beyond 60 seconds, system displays a "Payment processing" state and retries confirmation. Admin is emailed once confirmed.

**Business Rules:**
- BR-009.1: Plan upgrades take effect immediately upon successful payment.
- BR-009.2: Pro-rated charges are calculated based on the remaining days in the current billing cycle.
- BR-009.3: All billing events are retained in the audit log for 7 years for financial compliance.

**Non-Functional Requirements:**
- Stripe checkout flow must complete within 3 seconds from confirmation click to plan activation.
- Payment data must never be stored on platform servers; all card data is handled exclusively by Stripe Elements.

---

## UC-010: Create Audience Segment

**Use Case ID:** UC-010
**Use Case Name:** Create Audience Segment
**Actor(s):** Survey Creator

**Preconditions:**
- The actor is authenticated with Creator or Admin role.
- The workspace has not exceeded the audience segment limit for its plan.

**Postconditions:**
- A new `audience_segments` record is persisted with its contact list.
- The segment is immediately available for selection in the distribution wizard.

**Main Success Scenario:**
1. Creator navigates to **Audience → Segments → Create Segment**.
2. Creator enters a segment name and optional description.
3. Creator chooses the segment build method: *Manual*, *CSV Import*, or *Dynamic Filter*.
4. For CSV Import: Creator uploads a CSV file containing at minimum an `email` column; optional columns: `first_name`, `last_name`, custom metadata fields.
5. System parses the CSV, validates email formats, deduplicates entries, and reports import results: records imported, invalid emails skipped, duplicates merged.
6. Creator reviews the import report and clicks **Confirm and Create Segment**.
7. System persists the segment and its contacts.
8. System checks all contacts against the global unsubscribe list and marks suppressed contacts.
9. Creator can see the segment in the Audience list with contact count, creation date, and suppression stats.

**Alternative Flows:**
- **AF-010a — Dynamic filter segment:** Creator defines filter criteria (e.g., "contacts who did not complete Survey X" or "contacts in Region = Europe"). System evaluates the filter and shows the matching count. The segment re-evaluates at send time to capture updated contact data.
- **AF-010b — Manual selection:** Creator searches and selects individual contacts from the workspace contact directory.

**Exception Flows:**
- **EF-010a — CSV parsing error:** If the CSV lacks an `email` column header, system displays: "CSV must contain an 'email' column. Please review the file format guide."
- **EF-010b — All emails invalid:** If no valid emails are found after parsing, system prevents segment creation.

**Business Rules:**
- BR-010.1: Email addresses must conform to RFC 5322 format.
- BR-010.2: Contacts in the global unsubscribe list are automatically excluded from all distribution campaigns.
- BR-010.3: Segment contact limit: Starter — 500 contacts, Growth — 50,000, Enterprise — unlimited.

**Non-Functional Requirements:**
- CSV files up to 50 MB must be parsed and imported within 30 seconds.
- Dynamic segment evaluation at send time must complete within 10 seconds for up to 100,000 contacts.

---

## UC-011: Use Survey Template

**Use Case ID:** UC-011
**Use Case Name:** Use Survey Template
**Actor(s):** Survey Creator

**Preconditions:**
- The actor is authenticated with Creator or Admin role.
- At least one template is available in the system template library or workspace template library.

**Postconditions:**
- A new survey in `draft` status is created, pre-populated with the template's questions, logic, and settings.
- The original template record is unchanged.

**Main Success Scenario:**
1. Creator clicks **New Survey → Use Template**.
2. System displays the Template Library with category filters: Customer Satisfaction, Employee Engagement, Event Feedback, NPS, Product Research, Education, HR, Custom.
3. Creator browses templates and clicks **Preview** on a template of interest.
4. System renders a read-only preview of the template questions.
5. Creator clicks **Use This Template**.
6. System creates a deep copy of the template: new survey record, copied pages, questions (with options and logic), and settings. All IDs are regenerated.
7. System opens the Survey Builder with the copied survey in draft state, ready for customization.

**Alternative Flows:**
- **AF-011a — Save as workspace template:** Creator may save any of their own surveys as a workspace template for team reuse by clicking **Save as Template** from the survey builder.

**Exception Flows:**
- **EF-011a — Template deprecated:** If a template was deprecated after the Creator started a preview, clicking *Use* shows: "This template is no longer available. Please choose another."

**Business Rules:**
- BR-011.1: System templates are managed by the Super Admin and are available to all workspaces.
- BR-011.2: Workspace templates are private to the workspace that created them.
- BR-011.3: Using a template does not create any licensing or attribution obligation.

**Non-Functional Requirements:**
- Template deep-copy operation must complete within 1 second regardless of template complexity.

---

## UC-012: Embed Survey Widget on Website

**Use Case ID:** UC-012
**Use Case Name:** Embed Survey Widget on Website
**Actor(s):** Survey Creator

**Preconditions:**
- The survey is in `active` status.
- The actor has Creator or Admin role.

**Postconditions:**
- An embed configuration record is created associating the widget with the survey.
- A JavaScript snippet is available for the Creator to copy and paste into their website.

**Main Success Scenario:**
1. Creator opens the survey and navigates to **Distribute → Embed**.
2. System displays embed configuration options: *Inline* (renders within a page container), *Popup* (triggered by button click or page scroll), *Slide-in* (slides in from corner on trigger).
3. Creator selects embed type and configures trigger conditions (e.g., popup after 30 seconds, or after 50% scroll depth).
4. Creator sets an optional display frequency: *Once per visitor* or *Always*.
5. System generates a `<script>` tag containing the survey's embed token and configuration parameters.
6. Creator copies the snippet and pastes it into their website's HTML.
7. The platform CDN serves the embed JavaScript from CloudFront; the widget renders the survey in an iframe.

**Alternative Flows:**
- **AF-012a — iFrame embed:** Creator may opt for a plain `<iframe>` tag instead of the JS snippet for simpler CMS integrations.

**Exception Flows:**
- **EF-012a — Survey deactivated:** If the survey is closed after embedding, the widget renders a configurable fallback message ("This survey is closed") or a blank container based on Creator preference.

**Business Rules:**
- BR-012.1: Embed tokens are workspace-scoped and non-transferable.
- BR-012.2: The embedded survey enforces the same quota, expiry, and duplicate submission rules as the direct link.

**Non-Functional Requirements:**
- Embed JavaScript bundle must be under 50 KB gzipped and load in under 500 ms.
- The widget iframe must not block the host page's main thread.

---

## UC-013: Resume Partial Response

**Use Case ID:** UC-013
**Use Case Name:** Resume Partial Response
**Actor(s):** Respondent

**Preconditions:**
- The respondent previously opened a token-based survey link, answered at least one question, and navigated away without submitting.
- The survey is still in `active` status.
- The survey Creator has enabled the *Save Progress* feature for the survey.

**Postconditions:**
- The respondent is returned to the question where they left off, with all previously entered answers pre-populated.

**Main Success Scenario:**
1. Respondent reopens the original survey link.
2. System detects a `partial_response` record linked to the link token with `status = in_progress`.
3. System asks: "You have a saved response. Do you want to continue where you left off?" with options *Continue* and *Start Over*.
4. Respondent selects **Continue**.
5. System loads the partial response data and renders the survey starting at the last unanswered required question, pre-populating all previously answered questions.
6. Respondent completes remaining questions and submits.
7. System updates the response record from `in_progress` to `completed`.

**Alternative Flows:**
- **AF-013a — Start Over:** Respondent selects *Start Over*; system discards the partial response and presents a fresh survey.

**Exception Flows:**
- **EF-013a — Survey closed since partial save:** System informs the respondent the survey is closed and that their partial response cannot be completed.
- **EF-013b — Partial save expired:** Partial responses expire after 30 days. If expired, system presents a fresh survey start.

**Business Rules:**
- BR-013.1: Partial response auto-save triggers after each question answer, with a debounce of 3 seconds.
- BR-013.2: Only token-based (non-anonymous) surveys support resume. Anonymous surveys always start fresh.

**Non-Functional Requirements:**
- Partial response load must display the first previously answered question within 1 second.

---

## UC-014: Generate NPS Report

**Use Case ID:** UC-014
**Use Case Name:** Generate NPS Report
**Actor(s):** Analyst, Survey Creator

**Preconditions:**
- The survey contains at least one NPS-type question.
- At least 10 NPS responses have been submitted (minimum statistically meaningful sample).

**Postconditions:**
- An NPS report is rendered displaying the overall NPS score, promoter/passive/detractor percentages, trend over time, and verbatim comments from detractors.

**Main Success Scenario:**
1. Actor navigates to the survey's Analytics tab and selects the **NPS Report** view.
2. System queries DynamoDB for aggregated NPS buckets (promoters: 9–10, passives: 7–8, detractors: 0–6) and the trend time series.
3. System renders the NPS gauge (score range: −100 to +100) with the formula: NPS = %Promoters − %Detractors.
4. System renders the breakdown bar showing percentages for each category.
5. System renders a trend line chart showing NPS score over the survey's active period (daily granularity).
6. Actor may apply date range and segment filters; chart updates dynamically.
7. System surfaces verbatim open-text answers from detractors (if a follow-up open-text question exists) in a paginated list.
8. Actor may export the NPS report as PDF (delegates to UC-006).

**Alternative Flows:**
- **AF-014a — Insufficient responses:** If fewer than 10 NPS responses exist, a banner is shown: "NPS score is not yet statistically meaningful. Collect at least 10 responses."

**Exception Flows:**
- **EF-014a — NPS question deleted post-response:** If the NPS question was removed from a survey that was later re-published, the report shows NPS data only for responses collected under the version containing the NPS question.

**Business Rules:**
- BR-014.1: NPS is calculated as: NPS = (promoters / total) × 100 − (detractors / total) × 100, rounded to the nearest integer.
- BR-014.2: NPS trend is computed in UTC daily buckets.

**Non-Functional Requirements:**
- NPS dashboard must load within 1 second for surveys with up to 1 million responses.
- Trend chart must render up to 365 data points without pagination.

---

## UC-015: Manage GDPR Consent for Respondents

**Use Case ID:** UC-015
**Use Case Name:** Manage GDPR Consent for Respondents
**Actor(s):** Workspace Admin

**Preconditions:**
- The actor is authenticated with Workspace Admin role.
- The workspace has GDPR Compliance features enabled (Growth or Enterprise plan).

**Postconditions:**
- Consent records are viewable and auditable.
- Data deletion requests are processed within the legally required 72-hour window.
- A compliance audit trail entry is created for every action.

**Main Success Scenario:**
1. Admin navigates to **Workspace Settings → Compliance → GDPR**.
2. System displays the consent management dashboard: pending requests, processed requests, and consent record search.
3. A data subject submits a deletion request via the public GDPR request form linked from the workspace's privacy policy page.
4. System creates a `gdpr_requests` record with `type = deletion` and notifies the Admin via email and in-app notification.
5. Admin reviews the request, confirms the subject's identity by cross-referencing email with response records.
6. Admin clicks **Process Deletion** and confirms the irreversible action.
7. System triggers a Celery task that: anonymizes all response records linked to the email (replaces PII with `[DELETED]`), deletes S3 file uploads linked to the responses, removes the contact from all audience segments, suppresses the email address globally.
8. System marks the request `status = completed` with a timestamp.
9. System sends an automated confirmation email to the data subject: "Your data has been deleted as requested."
10. Admin can export a compliance report listing all processed requests.

**Alternative Flows:**
- **AF-015a — Consent withdrawal only:** If the data subject requests withdrawal of consent without full deletion, system records the withdrawal but retains anonymized response data.
- **AF-015b — Access request:** Data subject may request an export of their data; system generates a JSON export of all linked responses.

**Exception Flows:**
- **EF-015a — Subject identity mismatch:** If the Admin cannot verify the data subject's identity, they may place the request on hold and request additional identification, documenting the reason in the system.
- **EF-015b — Processing deadline breach:** If a deletion request remains unprocessed for 48 hours, the system escalates with a high-priority notification to the Admin and logs the delay in the compliance audit trail.

**Business Rules:**
- BR-015.1: GDPR deletion requests must be processed within 72 hours of receipt.
- BR-015.2: Anonymization replaces all PII fields with the string `[DELETED]`; aggregated analytics counts are preserved.
- BR-015.3: Processed deletion requests and their audit records are retained for 7 years for regulatory compliance.
- BR-015.4: A confirmation email must be sent to the data subject within 24 hours of processing.

**Non-Functional Requirements:**
- The full anonymization pipeline for a single data subject must complete within 15 minutes.
- The GDPR compliance dashboard must load within 2 seconds.
- All compliance actions must produce audit log entries that are immutable (append-only log store).

---

## Operational Policy Addendum

### 1. Response Data Privacy Policies

Response data is governed by the data processing agreement accepted by each workspace at the time of subscription. The platform acts as a **data processor** on behalf of the workspace, which is the **data controller**. All response data is isolated per workspace and accessed only under explicit authorization.

**Data Minimization:** The platform collects only the data fields explicitly defined in the survey. Survey Creators are prohibited from requesting sensitive categories of personal data (health, financial, political, religious) without enabling a dedicated *Sensitive Data* compliance flag, which triggers additional storage encryption and access audit logging.

**Cross-Border Transfers:** Workspaces operating in the EU may configure data residency to AWS `eu-west-1`. Data stored in EU-residency workspaces does not replicate to US-region infrastructure. SCCs (Standard Contractual Clauses) cover any residual cross-border data flows.

**Third-Party Sharing:** Response data is never shared with third parties for advertising or profiling purposes. Webhook deliveries constitute controlled data sharing under the workspace's direct configuration and are subject to the workspace's own DPA with the receiving system.

### 2. Survey Distribution Policies

All email distribution originating from the platform must comply with applicable anti-spam legislation including CAN-SPAM (US), CASL (Canada), and GDPR Article 6 (EU). The platform's email infrastructure enforces the following technical controls:

- **Sender Authentication:** All outbound emails are sent from SES-verified domains with DKIM signing and SPF records. DMARC policy is set to `p=quarantine`.
- **List Hygiene:** Bounce events (hard bounces) automatically suppress the affected email address globally. Soft bounces are retried three times before suppression.
- **Unsubscribe Handling:** Unsubscribe requests are processed in real time. The suppression applies globally across all workspaces, not just the workspace that sent the email.
- **Rate Limits:** To protect sender reputation, the platform implements per-workspace per-hour send rate limits enforced at the Celery queue layer.

### 3. Analytics and Retention Policies

The analytics pipeline is designed to provide real-time insights without compromising respondent privacy. Aggregated metrics stored in DynamoDB do not contain individual PII — they represent counts, averages, and distributions.

**Access Logging:** Every analytics dashboard view is logged with actor ID, workspace ID, survey ID, and filter parameters applied. This log is retained for 12 months.

**Data Portability:** Workspace Admins may request a full export of all workspace data (surveys, responses, analytics) in JSON format. Exports are generated asynchronously and delivered via a secure S3 pre-signed URL within 24 hours.

**Anonymization Threshold:** For workspaces with fewer than 5 responses, per-question analytics are hidden and replaced with "Insufficient responses to display analytics" to prevent reverse-engineering of individual responses.

### 4. System Availability Policies

The platform is hosted on AWS ECS Fargate with auto-scaling policies configured to maintain response time SLAs. The following operational policies govern system availability:

**Incident Response:** All P1 incidents (full outage or data integrity issues) trigger immediate PagerDuty alerts to the on-call engineering team with a 5-minute acknowledgment SLA and 30-minute mitigation SLA.

**Backup and Recovery:** PostgreSQL RDS performs automated daily snapshots retained for 35 days. Point-in-time recovery is available within a 5-minute granularity for the past 7 days. MongoDB Atlas performs continuous backups with 5-minute RPO.

**Capacity Planning:** Auto-scaling triggers are configured to add ECS Fargate tasks when average CPU utilization exceeds 70% for more than 2 minutes. The platform is load-tested quarterly to verify capacity at 3× projected peak load.

**Status Communication:** Platform status is published at `status.[platform-domain].com` with real-time incident updates. Workspace Admins are automatically subscribed to status notifications for their region.
