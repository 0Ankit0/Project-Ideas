# User Stories — Survey and Feedback Platform

---

## Table of Contents

- [Overview](#overview)
- [Survey Creator User Stories](#survey-creator-user-stories)
- [Respondent User Stories](#respondent-user-stories)
- [Analyst User Stories](#analyst-user-stories)
- [Workspace Admin User Stories](#workspace-admin-user-stories)
- [Super Admin User Stories](#super-admin-user-stories)
- [Story Map](#story-map)
- [Operational Policy Addendum](#operational-policy-addendum)

---

## Overview

### Story Format

Each user story follows the standard format:

> **As a** [role], **I want to** [action/goal], **so that** [business value or outcome].

Every story includes:
- **Acceptance Criteria** — Specific, testable conditions that must be true for the story to be considered complete (DONE).
- **Priority** — MH (Must Have / MVP), H (High / GA release), M (Medium), L (Low / roadmap).

Stories are organized by role and grouped by functional domain. Each ID is unique and traceable to functional requirements in `requirements-document.md`.

---

## Survey Creator User Stories

### Domain: Form Building

---

**US-CREATOR-001**
**As a** Survey Creator, **I want to** build a survey by dragging and dropping question blocks onto a canvas, **so that** I can design professional surveys quickly without writing any code.

**Acceptance Criteria:**
- Dragging a question type from the left panel and dropping it on the canvas adds it to the survey at the drop position.
- Questions can be reordered by drag-and-drop; the order is immediately reflected in the live preview.
- A minimum of 20 question types are available in the drag-and-drop panel.
- Changes are auto-saved every 30 seconds; a "Saved" indicator is displayed after each save.
- The undo/redo stack supports at least 20 operations.

**Priority:** MH

---

**US-CREATOR-002**
**As a** Survey Creator, **I want to** configure conditional display rules for questions (e.g., show Question 5 only if the respondent answered "Yes" to Question 3), **so that** respondents only see questions relevant to their previous answers.

**Acceptance Criteria:**
- A logic rule editor is accessible from each question block via a "Logic" button.
- The rule builder supports operators: equals, does not equal, contains, is greater than, is less than, is answered, is not answered.
- Rules can reference any preceding question on any page of the survey.
- The survey preview pane reflects conditional logic behavior in real time.
- Surveys with circular logic dependencies display a warning and block publishing until resolved.

**Priority:** MH

---

**US-CREATOR-003**
**As a** Survey Creator, **I want to** add branching/skip logic to jump respondents to a specific page or end the survey based on their answers, **so that** I can create multi-path surveys tailored to different audience segments.

**Acceptance Criteria:**
- Branching can be configured at the page level: "If [condition], jump to [page N / end of survey]."
- Multiple branching rules per page are supported; rules are evaluated top-to-bottom.
- The survey flow diagram (if implemented) visually represents the branching paths.
- Branching logic is correctly applied during live survey completion; respondents are not shown skipped pages.
- The preview pane allows testing specific branching paths by simulating different answer values.

**Priority:** MH

---

**US-CREATOR-004**
**As a** Survey Creator, **I want to** pipe a respondent's previous answer into a later question's text (e.g., "You rated us {Q1_answer}/10. What's the main reason for your score?"), **so that** surveys feel personalized and contextually relevant.

**Acceptance Criteria:**
- A variable picker UI in the question label editor allows inserting piping tokens for any preceding question.
- Piped values render correctly in the live survey for single-choice, text, and number question types.
- If the referenced question was skipped or left blank, the piped value renders as a configurable fallback string (e.g., "your score").
- Piping tokens are visible (highlighted) in the builder but render as plain text in the respondent view.

**Priority:** H

---

**US-CREATOR-005**
**As a** Survey Creator, **I want to** create a multi-page survey with a configurable progress indicator, **so that** I can organize long surveys into logical sections and keep respondents engaged with their completion progress.

**Acceptance Criteria:**
- Pages can be added, renamed, reordered, and deleted from the builder.
- The progress indicator can be set to: percentage bar, "Page X of Y" counter, or hidden.
- Page-level display conditions can be configured to skip entire pages based on previous answers.
- Each page is rendered as a separate screen to the respondent, with "Back" and "Next" navigation buttons.
- The "Back" button restores all previously entered answers on the preceding page.

**Priority:** MH

---

**US-CREATOR-006**
**As a** Survey Creator, **I want to** apply a custom brand theme (colors, fonts, logo, background) to my survey, **so that** the survey looks consistent with my organization's visual identity and builds respondent trust.

**Acceptance Criteria:**
- The theme editor supports: primary color (hex input + color picker), button color, background color, font selection (from a curated list of Google Fonts), and logo upload (PNG/SVG, max 2 MB).
- Theme changes are reflected immediately in the survey preview.
- The theme is applied to the public-facing survey URL and all PDF report exports.
- A "Reset to default" option restores the workspace default theme.
- Theme customization is available to Starter plan and above; Free plan displays the platform branding.

**Priority:** H

---

**US-CREATOR-007**
**As a** Survey Creator, **I want to** view and restore previous versions of my survey, **so that** I can safely experiment with changes and recover from accidental edits.

**Acceptance Criteria:**
- The version history panel lists all saved versions with timestamp and actor name.
- Clicking a version shows a read-only diff view highlighting added/removed/changed questions.
- Restoring a version creates a new version entry (the restore is itself versioned) rather than overwriting history.
- Version history is retained for the lifetime of the survey.
- The currently published version is clearly marked in the version list.

**Priority:** H

---

**US-CREATOR-008**
**As a** Survey Creator, **I want to** create a survey from a pre-built template, **so that** I can get started quickly without designing a survey from scratch.

**Acceptance Criteria:**
- The "New Survey" screen presents template categories (NPS, CSAT, HR, Event, etc.) with thumbnail previews.
- Selecting a template opens a full preview showing all questions before confirming.
- Confirming copies the template's question structure into a new draft survey that the creator can fully edit.
- Creating from a template does not modify the original template.
- Workspace templates and platform-curated templates are displayed in separate sections.

**Priority:** H

---

### Domain: Distribution

---

**US-CREATOR-009**
**As a** Survey Creator, **I want to** send survey invitation emails to a contact list with a scheduled delivery time, **so that** I can reach respondents at the optimal time for maximum response rates.

**Acceptance Criteria:**
- The distribution wizard allows selecting an existing contact list or a saved segment.
- The email editor provides subject line, body text with merge tags ({first_name}, {survey_link}), and a "Send Test" button.
- Scheduled delivery supports date, time, and timezone selection.
- A confirmation screen shows the estimated recipient count (excluding suppressed contacts) before the creator confirms.
- After scheduling, the campaign appears in the Distributions tab with status "Scheduled" and can be cancelled up to 10 minutes before the scheduled time.

**Priority:** MH

---

**US-CREATOR-010**
**As a** Survey Creator, **I want to** generate a QR code for my survey, **so that** I can distribute it in physical materials like event flyers or product packaging.

**Acceptance Criteria:**
- The "Share" panel provides a "Download QR Code" button that generates a PNG and an SVG version.
- The QR code links to the survey's public URL and correctly redirects to the survey when scanned.
- The creator can select a QR code color and optionally embed the workspace logo in the center.
- The generated file is downloadable directly from the browser (no additional email step required).

**Priority:** H

---

**US-CREATOR-011**
**As a** Survey Creator, **I want to** configure automated reminder emails for non-respondents, **so that** I can increase response rates without manually tracking who hasn't replied.

**Acceptance Criteria:**
- The reminder is configurable with: delay after initial send (1–30 days), custom subject line, and custom email body.
- The system automatically excludes contacts who have already submitted a response when sending reminders.
- Up to 3 reminder emails per distribution campaign are supported.
- The reminder schedule is displayed in the campaign detail view, and each sent reminder is logged in the distribution activity feed.
- Reminders respect the workspace suppression list and do not send to opted-out contacts.

**Priority:** H

---

**US-CREATOR-012**
**As a** Survey Creator, **I want to** set a response quota and an expiry date for my survey, **so that** I can control the data collection window and automatically close the survey when I have enough responses.

**Acceptance Criteria:**
- The survey settings panel provides fields for: maximum response count and survey expiry date/time.
- When the quota is reached, the survey URL serves a configurable "Survey closed" message instead of the survey form.
- When the expiry date passes, the survey is automatically closed regardless of response count.
- The creator receives an in-app and email notification when the quota or expiry is reached.
- Closed surveys can be re-opened manually by the creator at any time.

**Priority:** H

---

### Domain: Analytics & Reports

---

**US-CREATOR-013**
**As a** Survey Creator, **I want to** view a real-time analytics dashboard for my survey showing total responses, completion rate, and response trends, **so that** I can monitor my survey's performance as data comes in.

**Acceptance Criteria:**
- The dashboard loads and displays live data within 5 seconds of opening.
- Summary cards show: total responses, completion rate (%), average completion time, and drop-off rate.
- A time-series chart shows response volume over time (day/week/month granularity, switchable).
- The dashboard auto-refreshes every 30 seconds without a manual page reload.
- All charts display correctly on both desktop (1920×1080) and tablet (768px) viewports.

**Priority:** MH

---

**US-CREATOR-014**
**As a** Survey Creator, **I want to** export my survey results as a PDF report, **so that** I can share a polished summary with stakeholders who don't have platform access.

**Acceptance Criteria:**
- Clicking "Export PDF" enqueues a background task and shows a progress indicator.
- The generated PDF includes: survey title, date range, response count, per-question summary charts (bar/pie for choice questions, histogram for rating questions), and a raw response appendix.
- The PDF respects the workspace brand theme (logo, primary color) for Business and Enterprise plans.
- A download link for the generated PDF is emailed to the creator and available in the Reports History section for 24 hours.
- PDF generation for a survey with up to 10,000 responses completes within 60 seconds.

**Priority:** MH

---

**US-CREATOR-015**
**As a** Survey Creator, **I want to** export raw response data as a CSV file, **so that** I can perform custom analysis in Excel or other data tools.

**Acceptance Criteria:**
- The CSV export includes one row per response with columns for: response ID, submission timestamp, all question answers (one column per question), device type, country, and completion time.
- Question column headers use the question label text by default, with an option to use question IDs.
- File encoding is UTF-8 with BOM to ensure correct rendering in Microsoft Excel.
- The export respects any active filters (date range, channel, etc.) applied in the analytics view.
- Large exports (>50,000 rows) are generated as background tasks with an email notification when ready.

**Priority:** MH

---

**US-CREATOR-016**
**As a** Survey Creator, **I want to** schedule recurring automated reports, **so that** stakeholders automatically receive updated data without me manually running exports each week.

**Acceptance Criteria:**
- Report scheduling supports: daily, weekly (day of week selectable), and monthly (day of month selectable) frequencies.
- The creator can specify a list of recipient email addresses (not limited to platform users).
- Each scheduled report email includes a summary of key metrics in the email body and a PDF or CSV attachment.
- The scheduled report can be paused or deleted from the Reports section.
- The first scheduled run executes within 5 minutes of the scheduled time; subsequent runs are accurate to within 15 minutes.

**Priority:** H

---

**US-CREATOR-017**
**As a** Survey Creator, **I want to** configure a webhook that fires when a new response is submitted, **so that** I can trigger real-time actions in my CRM or other business tools without manual data transfers.

**Acceptance Criteria:**
- The webhook configuration form requires: target URL, trigger event selection, and an optional secret for HMAC-SHA256 signature verification.
- On each new submission, the platform sends an HTTP POST to the configured URL with the full response payload in JSON.
- The system retries failed deliveries up to 5 times with exponential backoff (1 min, 2 min, 4 min, 8 min, 16 min).
- A delivery log shows each delivery attempt: timestamp, HTTP status code returned, and latency.
- The creator can send a test payload from the webhook config page to verify the endpoint before activating.

**Priority:** H

---

**US-CREATOR-018**
**As a** Survey Creator, **I want to** duplicate an existing survey, **so that** I can reuse a proven structure for a similar data collection effort without rebuilding it from scratch.

**Acceptance Criteria:**
- Clicking "Duplicate" on a survey creates a complete copy including all questions, logic rules, theme, and settings, with the title prefixed "Copy of [original name]."
- The duplicate is created in "Draft" status regardless of the original's status.
- The duplicate does not inherit the original's responses or distribution history.
- The duplicated survey is immediately editable.
- The action is completed within 5 seconds for surveys with up to 50 questions.

**Priority:** MH

---

**US-CREATOR-019**
**As a** Survey Creator, **I want to** preview my survey exactly as respondents will see it, including all themes and logic behavior, **so that** I can verify the experience before publishing.

**Acceptance Criteria:**
- The preview opens in a full-screen modal or new browser tab rendering the exact survey UI the respondent will see.
- Preview mode allows navigating through all pages and simulating conditional logic by entering test answers.
- The preview correctly applies the configured theme (colors, font, logo).
- Preview mode does not record responses in the database.
- The preview renders correctly on desktop (1440px), tablet (768px), and mobile (375px) using a viewport simulator in the builder.

**Priority:** MH

---

**US-CREATOR-020**
**As a** Survey Creator, **I want to** view the drop-off analytics for my survey showing at which question respondents abandon, **so that** I can identify and fix problematic questions that reduce completion rates.

**Acceptance Criteria:**
- The drop-off analytics view shows a funnel chart with the number and percentage of respondents who reached each question.
- Questions with drop-off rates greater than 20% above the average are highlighted in orange/red.
- The drop-off rate is calculated from all started sessions (including partial saves) in the selected date range.
- Clicking a question in the drop-off funnel scrolls the analytics to that question's detailed breakdown.
- Data is available within 5 minutes of the most recent response submission.

**Priority:** H

---

## Respondent User Stories

---

**US-RESP-001**
**As a** Respondent, **I want to** complete a survey on my mobile phone without creating an account, **so that** I can share my feedback quickly and without friction.

**Acceptance Criteria:**
- The survey URL loads and renders correctly on iOS Safari 16+ and Android Chrome 110+ without any account requirement.
- All question types render correctly at 375px viewport width with touch-friendly input targets (minimum 44px).
- The submit button is visible and accessible on the last page without requiring excessive scrolling.
- Submission completes without an account; a session token is issued transparently.
- Confirmation screen is displayed after successful submission.

**Priority:** MH

---

**US-RESP-002**
**As a** Respondent, **I want to** save my partially completed survey and resume it later, **so that** I don't lose my progress if I get interrupted.

**Acceptance Criteria:**
- Partial progress is auto-saved every 30 seconds while the respondent is on the survey.
- On the last auto-save, a "Resume this survey later" link is displayed prominently.
- Clicking the resume link (sent via email or saved from the page) restores the exact page and all previously entered answers.
- Resume links remain valid for 30 days from initial creation.
- Resuming on a different device from the original correctly restores all entered answers.

**Priority:** H

---

**US-RESP-003**
**As a** Respondent, **I want to** complete a survey even when I have no internet connection, **so that** I can submit feedback from locations with poor connectivity (trade shows, field sites, etc.).

**Acceptance Criteria:**
- The survey PWA can be installed from a mobile browser and opens fully without network access once loaded.
- Responses entered offline are stored in the browser's IndexedDB.
- When connectivity is restored, pending offline responses are automatically submitted within 10 seconds.
- A banner in the survey UI indicates when the user is in offline mode.
- After successful online sync, the offline cache is cleared and the respondent sees the standard confirmation screen.

**Priority:** H

---

**US-RESP-004**
**As a** Respondent, **I want to** receive clear validation messages when I enter incorrect or incomplete data, **so that** I understand what I need to fix before I can proceed.

**Acceptance Criteria:**
- Required questions that are left blank display an inline error message ("This field is required") when the respondent attempts to proceed.
- Text fields with character limits display a character counter and an error when the limit is exceeded.
- Date fields validate the format and display an error for invalid dates.
- All error messages are announced by screen readers (ARIA live regions).
- Validation does not prevent the respondent from correcting their answer; the error clears as soon as the condition is resolved.

**Priority:** MH

---

**US-RESP-005**
**As a** Respondent, **I want to** withdraw my consent and request deletion of my submitted responses, **so that** I can exercise my GDPR right to erasure.

**Acceptance Criteria:**
- Identified survey confirmation pages include a link to the Privacy/DSR portal.
- At the DSR portal, the respondent can submit an erasure request by providing their email address (verified via OTP).
- The request is logged in the platform audit trail with timestamp.
- The respondent's data is deleted or anonymized within 30 days of the verified request.
- The respondent receives an email confirmation when the erasure is complete.

**Priority:** MH

---

**US-RESP-006**
**As a** Respondent, **I want to** see a clear privacy notice explaining how my data will be used before I start the survey, **so that** I can make an informed decision about whether to participate.

**Acceptance Criteria:**
- If the survey is configured as "identified" (collects email or name), a consent banner is displayed on the first page.
- The consent banner includes: data controller name, purpose of data collection, a link to the full privacy policy, and an explicit opt-in checkbox.
- The survey cannot be submitted without the consent checkbox being checked on identified surveys.
- The consent checkbox is not pre-checked; affirmative consent is required.
- Anonymous surveys display a brief privacy notice without a consent checkbox.

**Priority:** MH

---

**US-RESP-007**
**As a** Respondent, **I want to** complete a survey that is accessible via keyboard and screen reader, **so that** respondents with disabilities can participate equally.

**Acceptance Criteria:**
- All question inputs and navigation controls are reachable and operable via keyboard Tab/Enter/Space/Arrow keys.
- All form elements have associated ARIA labels that correctly describe the question and input purpose.
- Focus management correctly moves to the first question on a new page after clicking "Next."
- Color is not the sole means of conveying information (e.g., error states include both color and an icon/text).
- Survey passes automated WCAG 2.1 AA checks (axe-core) with zero violations.

**Priority:** H

---

**US-RESP-008**
**As a** Respondent, **I want to** receive a confirmation email after submitting a survey (if I provided my email), **so that** I have a record that my feedback was received.

**Acceptance Criteria:**
- If the respondent provided an email address during an identified survey, a confirmation email is sent within 60 seconds of submission.
- The confirmation email includes: survey title, submission timestamp, and an optional custom "thank you" message configured by the creator.
- The email includes a link to the DSR portal for GDPR rights.
- If the creator has configured a custom redirect URL, the confirmation email is suppressed in favor of the redirect.
- Confirmation emails are sent from the workspace's authenticated sending domain.

**Priority:** M

---

**US-RESP-009**
**As a** Respondent, **I want to** see a custom thank-you message and optional redirect after completing a survey, **so that** I know my submission was successful and am guided to the next step.

**Acceptance Criteria:**
- The creator can configure a custom "Thank You" page with: title, body text (rich text), and an optional redirect URL with a configurable delay (0–10 seconds).
- If no custom message is configured, a default "Thank you for your response!" screen is displayed.
- The thank-you page respects the survey's brand theme.
- If a redirect URL is configured, a countdown is displayed before the redirect.
- The thank-you page is accessible (meets WCAG 2.1 AA).

**Priority:** H

---

**US-RESP-010**
**As a** Respondent, **I want to** clearly see when a survey has closed or expired, **so that** I'm not confused when I try to access a survey link that is no longer active.

**Acceptance Criteria:**
- Accessing a closed or expired survey URL displays a custom "Survey Closed" page (configurable by the creator) with a clear explanation.
- The closed page is branded with the workspace theme.
- The closed page does not show any partial survey content.
- A contact email for the survey owner is optionally displayed (configurable by the creator).
- Accessing a survey that was never published returns a generic "Survey not found" page that does not reveal any survey metadata.

**Priority:** MH

---

## Analyst User Stories

---

**US-ANALYST-001**
**As an** Analyst, **I want to** view an NPS dashboard with score trend over time and segment breakdown, **so that** I can track customer loyalty changes and understand which segments drive the score.

**Acceptance Criteria:**
- The NPS dashboard shows: current NPS score (prominently), Promoters/Passives/Detractors counts and percentages, and a line chart of NPS score over time (daily/weekly/monthly).
- The NPS calculation correctly classifies 9–10 as Promoters, 7–8 as Passives, 0–6 as Detractors.
- The segment filter allows breaking down NPS by any respondent attribute (department, country, plan, etc.).
- The trend chart supports date range selection with a calendar picker.
- The dashboard loads within 3 seconds for surveys with up to 100,000 responses.

**Priority:** MH

---

**US-ANALYST-002**
**As an** Analyst, **I want to** run cross-tabulation analysis between any two survey questions, **so that** I can identify correlations (e.g., "How does NPS vary by product tier?").

**Acceptance Criteria:**
- The cross-tab tool allows selecting any two questions from the same survey as row and column variables.
- The output is a pivot table showing response counts and percentages for each combination.
- A color-coded heatmap overlay is available to visually identify high/low concentration cells.
- Cross-tab results can be exported as CSV or PNG (chart).
- Cross-tab queries for surveys up to 50,000 responses complete within 10 seconds.

**Priority:** H

---

**US-ANALYST-003**
**As an** Analyst, **I want to** view sentiment analysis results for free-text responses, **so that** I can understand the emotional tone of feedback at scale without reading every individual response.

**Acceptance Criteria:**
- Each free-text question displays a sentiment distribution bar (% Positive, % Neutral, % Negative).
- Clicking on a sentiment category (e.g., "Negative") filters the response table to show only responses with that sentiment classification.
- Sentiment scores are displayed per response in the individual response detail view.
- Sentiment analysis results are available within 60 seconds of response submission.
- The workspace admin can disable sentiment analysis; when disabled, the analysis UI is hidden.

**Priority:** H

---

**US-ANALYST-004**
**As an** Analyst, **I want to** see a word cloud generated from free-text responses, **so that** I can quickly identify the most commonly mentioned themes and topics.

**Acceptance Criteria:**
- The word cloud renders for any free-text question with at least 10 responses.
- Word size is proportional to frequency.
- Common stop words (the, and, is, etc.) are excluded by default; a configurable stop-word list is available.
- Clicking a word in the cloud filters the response table to show responses containing that word.
- The word cloud can be exported as a PNG image.

**Priority:** H

---

**US-ANALYST-005**
**As an** Analyst, **I want to** filter the analytics view by date range, distribution channel, country, device type, and respondent attributes, **so that** I can isolate specific audience segments for deeper analysis.

**Acceptance Criteria:**
- The filter panel is accessible from all analytics views (summary, per-question, response table).
- Applied filters are displayed as removable chips in the filter bar.
- Filtering dynamically updates all visible charts and statistics within 3 seconds.
- Multiple filters are applied with AND logic by default; OR logic is available per filter group.
- The current filter state is preserved when navigating between analytics sub-pages within the same survey.
- Filters can be saved as named views and recalled from a dropdown.

**Priority:** MH

---

**US-ANALYST-006**
**As an** Analyst, **I want to** export a filtered subset of raw response data as Excel (XLSX), **so that** I can perform pivot table analysis in Microsoft Excel without manual data cleaning.

**Acceptance Criteria:**
- The XLSX export includes: Summary sheet (key metrics), Per-Question Data sheet (aggregated distributions), and Raw Responses sheet (one row per response).
- Column headers use question labels; the Raw Responses sheet includes all metadata columns (timestamp, device, country, channel).
- Applied filters are reflected in the export (only filtered data is included).
- The export respects the workspace's k-anonymity suppression settings.
- Large exports (>100,000 rows) are generated asynchronously with an email notification.

**Priority:** H

---

**US-ANALYST-007**
**As an** Analyst, **I want to** compare analytics between two date ranges side by side, **so that** I can measure the impact of changes or campaigns on survey results.

**Acceptance Criteria:**
- The comparison view allows selecting two independent date ranges (Range A and Range B).
- Side-by-side charts are displayed for NPS score, CSAT, completion rate, and per-question distributions.
- A "delta" indicator shows the change between the two ranges (e.g., NPS: +7 points).
- The comparison view is available for all surveys with at least 5 responses in each selected range.
- Comparison state (selected ranges) can be shared via a URL with encoded parameters.

**Priority:** M

---

**US-ANALYST-008**
**As an** Analyst, **I want to** drill down into individual responses, **so that** I can review the full context of specific submissions and identify interesting or anomalous responses.

**Acceptance Criteria:**
- The response data table supports sorting by any column (submission date, NPS score, completion time, sentiment).
- Clicking a row opens a detailed response view showing all answers, metadata (device, country, channel, duration), and sentiment classification.
- The detailed view includes navigation arrows to move to the next/previous response in the current filtered set.
- Individual responses can be flagged for follow-up.
- Analyst can add internal notes to a response (not visible to the respondent).

**Priority:** H

---

**US-ANALYST-009**
**As an** Analyst, **I want to** save a custom analytics dashboard configuration, **so that** I can quickly return to my standard analysis view without re-applying filters and chart settings each time.

**Acceptance Criteria:**
- Clicking "Save Dashboard" saves the current filter state, selected chart types, and date range as a named dashboard.
- Saved dashboards are accessible from a dropdown on the analytics page.
- Up to 10 saved dashboards per survey are supported.
- Dashboards can be renamed and deleted.
- Saved dashboards are visible to all workspace members with Analyst or higher role.

**Priority:** M

---

**US-ANALYST-010**
**As an** Analyst, **I want to** view drop-off and engagement metrics per question, **so that** I can identify which questions cause respondents to abandon the survey.

**Acceptance Criteria:**
- The drop-off view shows a waterfall/funnel chart with the respondent count reaching each question.
- Drop-off percentage is shown between each consecutive question.
- Average time spent per question is displayed.
- Questions with anomalously high drop-off rates (>2 standard deviations above the survey average) are flagged.
- Data includes both partial (abandoned) and complete responses.

**Priority:** H

---

**US-ANALYST-011**
**As an** Analyst, **I want to** view geographic distribution of responses on a world map, **so that** I can understand where my respondents are coming from.

**Acceptance Criteria:**
- A choropleth world map shows response density by country.
- Hovering over a country displays: country name, response count, and completion rate.
- Clicking a country filters the entire analytics view to responses from that country.
- Countries with fewer than 5 responses are grouped as "Other" to respect k-anonymity.
- The map is accessible (keyboard-navigable table view available as an alternative).

**Priority:** M

---

**US-ANALYST-012**
**As an** Analyst, **I want to** configure and view CSAT and CES scores with trend charts, **so that** I can track customer satisfaction and effort over time alongside NPS.

**Acceptance Criteria:**
- CSAT is calculated as (number of ratings 4–5 / total ratings) × 100, displayed as a percentage.
- CES is displayed as the average score from the effort question (typically 1–7 scale).
- Both scores are displayed with trend charts supporting day/week/month granularity.
- CSAT and CES scores are visible on the main analytics summary card alongside NPS.
- If the survey does not contain an NPS, CSAT, or CES question, the respective card is hidden.

**Priority:** H

---

## Workspace Admin User Stories

---

**US-ADMIN-001**
**As a** Workspace Admin, **I want to** invite new members to my workspace by email and assign them a role, **so that** I can collaborate with my team and grant appropriate access levels.

**Acceptance Criteria:**
- The invite form accepts one or more email addresses and a role selection (Survey Creator, Analyst, Workspace Admin).
- An invitation email is sent to each address within 60 seconds; the email contains a unique accept link valid for 7 days.
- Pending invitations are listed in the Members panel with the ability to resend or revoke.
- Accepting an invitation creates the user account (if new) and adds them to the workspace with the assigned role.
- The inviting admin is notified via email when an invited member accepts.

**Priority:** MH

---

**US-ADMIN-002**
**As a** Workspace Admin, **I want to** manage the workspace subscription and billing, **so that** I can upgrade, downgrade, or cancel the plan and view invoices.

**Acceptance Criteria:**
- The Billing section displays: current plan, billing period, next invoice date, and current usage (responses, seats, storage) vs. plan limits.
- An "Upgrade" button opens the Stripe-hosted checkout for plan upgrades.
- Downgrading a plan takes effect at the end of the current billing period; an in-app warning lists features that will be lost.
- All past invoices are listed with status (paid, overdue) and a "Download PDF" link for each.
- Workspace admins can update the payment method via the Stripe customer portal.

**Priority:** MH

---

**US-ADMIN-003**
**As a** Workspace Admin, **I want to** configure integrations (Slack, HubSpot, Salesforce, webhooks) for my workspace, **so that** response data automatically flows into our business tools.

**Acceptance Criteria:**
- The Integrations page lists all available integrations with connection status (Connected, Not Connected).
- Each integration has a setup wizard that guides the admin through OAuth authorization or API key entry.
- Connected integrations can be tested with a "Send Test Event" button.
- Each integration can be individually disconnected without affecting other integrations.
- Integration configuration (which surveys trigger which actions) is editable after initial setup.

**Priority:** H

---

**US-ADMIN-004**
**As a** Workspace Admin, **I want to** import a contact list from a CSV file, **so that** I can use my existing customer database for survey distribution without manual data entry.

**Acceptance Criteria:**
- The import wizard accepts CSV files with configurable column mapping (map CSV columns to contact fields).
- Required field: email address. Optional fields: first name, last name, phone, and up to 10 custom attributes.
- The import preview shows the first 5 rows and validation errors (invalid email format, missing required field) before confirming.
- Duplicate emails within the import file and against existing contacts are flagged; the admin can choose to skip or update duplicates.
- Import progress is shown with a progress bar; large imports (>10,000 rows) run as a background task with an email notification on completion.

**Priority:** MH

---

**US-ADMIN-005**
**As a** Workspace Admin, **I want to** view the workspace activity audit log, **so that** I can track all actions taken in the workspace for compliance and security purposes.

**Acceptance Criteria:**
- The audit log lists all workspace events: survey created/published/deleted, distribution sent, member invited/removed, settings changed, integration connected/disconnected.
- Each entry shows: timestamp, actor (name + email), action type, and affected resource.
- The log is filterable by actor, action type, and date range.
- The log is read-only; no entries can be deleted by any workspace role.
- The log can be exported as CSV for the last 90 days.

**Priority:** H

---

**US-ADMIN-006**
**As a** Workspace Admin, **I want to** configure workspace-level branding (logo, colors, custom domain), **so that** all surveys and reports from our workspace reflect our brand identity.

**Acceptance Criteria:**
- Workspace branding settings include: logo upload (PNG/SVG, max 2 MB), primary color, button color, and custom email sending domain.
- Custom domain configuration includes a DNS verification step with CNAME/TXT record instructions.
- Once configured, all survey URLs under the workspace use the custom domain.
- All exported PDF reports automatically use the workspace logo and color settings.
- Brand settings changes take effect for all new distributions and surveys immediately; existing published survey URLs continue to work.

**Priority:** H

---

**US-ADMIN-007**
**As a** Workspace Admin, **I want to** configure GDPR consent settings for the workspace, **so that** all surveys automatically include appropriate consent mechanisms and our data practices are documented.

**Acceptance Criteria:**
- The GDPR settings panel allows: enabling/disabling global consent collection, configuring the consent text (rich text editor), and linking to the organization's privacy policy URL.
- When global consent is enabled, all new surveys automatically include the consent banner on the first page.
- The consent text version is tracked; changing the text creates a new version, and existing responses retain the consent text version they agreed to.
- The workspace data retention period is configurable (1–36 months for identified responses).
- Workspace admins can trigger a bulk DSR export or deletion from the GDPR settings panel.

**Priority:** MH

---

**US-ADMIN-008**
**As a** Workspace Admin, **I want to** manage workspace API keys, **so that** our developers can build custom integrations with the platform's REST API.

**Acceptance Criteria:**
- The API Keys panel allows creating named keys with configurable permission scopes (read-only, read-write, admin).
- Created keys are displayed in full only once at creation; subsequent views show only the last 4 characters.
- Each key can be revoked immediately from the API Keys panel.
- Key usage is logged (last used timestamp, total request count in the last 30 days).
- Up to 10 API keys per workspace are supported on Business/Enterprise plans; 2 keys on Starter; 0 keys on Free plan.

**Priority:** H

---

**US-ADMIN-009**
**As a** Workspace Admin, **I want to** configure single sign-on (SSO) for my workspace using Google Workspace or Microsoft Entra ID, **so that** my team can log in with their corporate credentials without separate passwords.

**Acceptance Criteria:**
- SSO configuration supports OAuth 2.0 with Google Workspace and Microsoft Entra ID (Azure AD).
- The setup wizard provides step-by-step instructions for configuring the OAuth app in Google/Microsoft admin consoles.
- Once SSO is configured and enforced, workspace members cannot log in with email/password — only SSO is accepted.
- Existing members are migrated to SSO on their next login.
- SSO enforcement is a toggle that can be disabled if misconfigured; the admin is warned of the impact before enabling enforcement.

**Priority:** H

---

**US-ADMIN-010**
**As a** Workspace Admin, **I want to** view and manage the workspace's usage metrics in real time, **so that** I can proactively plan upgrades and avoid hitting plan limits that disrupt our operations.

**Acceptance Criteria:**
- The usage dashboard shows current consumption vs. plan limits for: total responses (current billing period), active surveys, workspace members, email sends (current month), and storage used.
- Each metric is displayed as a progress bar with numeric values (e.g., "8,432 / 10,000 responses").
- Metrics are updated in real time (within 5 minutes of any new usage event).
- When any metric exceeds 80% of the limit, a warning banner appears on the workspace dashboard.
- The admin can click "Upgrade Plan" directly from any limit warning.

**Priority:** H

---

## Super Admin User Stories

---

**US-SUPERADMIN-001**
**As a** Super Admin, **I want to** view a global platform dashboard showing all tenants, active users, total responses, and system health, **so that** I can monitor the overall health and growth of the platform.

**Acceptance Criteria:**
- The global dashboard shows: total workspaces, total active users (last 30 days), total responses ingested (current month), system error rate, and API latency (p50/p95/p99).
- Workspaces can be searched and filtered by plan, creation date, and activity status.
- Clicking a workspace opens the workspace detail view with full visibility into its surveys, members, and usage.
- The dashboard data is refreshed every 60 seconds.
- The dashboard is accessible only to users with the Super Admin role.

**Priority:** MH

---

**US-SUPERADMIN-002**
**As a** Super Admin, **I want to** impersonate a workspace admin to troubleshoot reported issues, **so that** I can reproduce and resolve customer-reported problems without requiring their credentials.

**Acceptance Criteria:**
- Impersonation requires selecting a target user from the user management panel and confirming a reason (logged in the audit trail).
- While impersonating, a persistent banner is shown: "You are impersonating [user name]. Click here to exit."
- All actions taken during impersonation are logged in the platform audit trail under the Super Admin's identity with an "impersonation" flag.
- Exiting impersonation returns to the Super Admin's own session immediately.
- Impersonation sessions automatically expire after 60 minutes.

**Priority:** H

---

**US-SUPERADMIN-003**
**As a** Super Admin, **I want to** manage platform-wide feature flags, **so that** I can enable/disable features for specific plans, workspaces, or globally for testing and phased rollouts.

**Acceptance Criteria:**
- The feature flag panel lists all flags with their current state (enabled globally, enabled per plan, enabled for specific workspaces, disabled).
- Flags can be toggled globally, per plan tier, or for an individual workspace override.
- Flag changes take effect within 60 seconds without requiring a deployment.
- A change history log is maintained for all flag modifications including actor, timestamp, and before/after state.
- Feature flags are evaluated server-side; the frontend reflects the flag state via the API response.

**Priority:** H

---

**US-SUPERADMIN-004**
**As a** Super Admin, **I want to** view the global platform audit log across all workspaces, **so that** I can investigate security incidents and compliance issues that span multiple tenants.

**Acceptance Criteria:**
- The global audit log aggregates events from all workspaces, including Super Admin actions.
- The log is filterable by: workspace, actor, action type, date range, and IP address.
- Sensitive events (impersonation, DSR fulfillment, workspace deletion, plan override) are highlighted.
- The log is append-only and tamper-evident (stored in an append-only S3 bucket with object lock).
- The log can be exported as JSON or CSV for up to 90 days of data.

**Priority:** H

---

**US-SUPERADMIN-005**
**As a** Super Admin, **I want to** manually adjust a workspace's plan and usage limits, **so that** I can accommodate special Enterprise contracts and extend limits for promotional purposes.

**Acceptance Criteria:**
- The workspace edit panel allows Super Admins to: set a custom plan override, set custom limits for each usage metric, and add or remove plan features independently.
- Plan overrides are logged in the audit trail with a required justification field.
- Custom limits are enforced immediately; existing over-limit usage is not retroactively blocked.
- Overridden workspaces are marked with an "Override" badge in the tenant list.
- Overrides can be set with an optional expiry date after which the workspace reverts to its standard plan limits.

**Priority:** H

---

**US-SUPERADMIN-006**
**As a** Super Admin, **I want to** manage the platform's public template library (add, edit, unpublish templates), **so that** all platform users have access to high-quality, vetted survey templates.

**Acceptance Criteria:**
- The template management panel lists all platform templates with their publish status (draft, published, archived).
- Super Admins can create new templates from scratch or promote a workspace survey to a platform template.
- Published templates immediately appear in all workspaces' template library (no cache invalidation delay >5 minutes).
- Unpublishing a template hides it from the library; existing surveys created from it are not affected.
- Template usage statistics (# of surveys created from each template across all workspaces) are displayed.

**Priority:** M

---

**US-SUPERADMIN-007**
**As a** Super Admin, **I want to** trigger and monitor database maintenance tasks (backups, cleanups, analytics backfills), **so that** I can ensure data integrity and platform hygiene without direct database access.

**Acceptance Criteria:**
- The maintenance panel lists scheduled and on-demand tasks: database backup, response cleanup (purge deleted workspace data), analytics aggregate backfill, and audit log archival.
- Each task can be triggered manually with a confirmation dialog.
- Task execution status (running, completed, failed) is visible with a progress indicator for long-running tasks.
- Task execution history shows start time, end time, status, and a summary of records affected.
- Failed tasks generate a P2 alert and notify the engineering on-call via PagerDuty.

**Priority:** M

---

**US-SUPERADMIN-008**
**As a** Super Admin, **I want to** manage email sending domain authentication and deliverability settings at the platform level, **so that** the platform's email sending reputation is maintained and compliance with CAN-SPAM is enforced.

**Acceptance Criteria:**
- The email settings panel shows all workspace sending domains with their SPF, DKIM, and DMARC verification status.
- Domains failing verification are flagged; email campaigns from unverified domains are blocked automatically.
- The Super Admin can send a domain verification reminder email to the relevant workspace admin.
- Platform-level bounce and spam complaint rates are displayed (aggregated across all workspaces) with alerts if bounce rate exceeds 5% or complaint rate exceeds 0.1%.
- Workspaces exceeding complaint thresholds are automatically suspended from sending and flagged for Super Admin review.

**Priority:** H

---

## Story Map

The story map organizes user stories into epics and their corresponding user story groupings, showing the full product journey from left to right.

### Epic Overview

| Epic | Domain | Key User Stories |
|---|---|---|
| **E1: Onboarding & Auth** | Auth, Workspace Setup | US-ADMIN-001, US-ADMIN-009, US-SUPERADMIN-001 |
| **E2: Form Building** | Survey Design | US-CREATOR-001 through US-CREATOR-008 |
| **E3: Distribution** | Multi-Channel | US-CREATOR-009 through US-CREATOR-012 |
| **E4: Response Collection** | Respondent Experience | US-RESP-001 through US-RESP-010 |
| **E5: Analytics & Insights** | Reporting, BI | US-ANALYST-001 through US-ANALYST-012, US-CREATOR-013 |
| **E6: Reporting & Export** | Data Export | US-CREATOR-014, US-CREATOR-015, US-CREATOR-016, US-ANALYST-006 |
| **E7: Integrations** | Webhooks, CRM | US-CREATOR-017, US-ADMIN-003 |
| **E8: Team & Workspace** | Collaboration | US-ADMIN-001, US-ADMIN-005, US-ADMIN-007 |
| **E9: Billing & Plans** | Monetization | US-ADMIN-002, US-ADMIN-010 |
| **E10: Platform Admin** | Operations | US-SUPERADMIN-001 through US-SUPERADMIN-008 |

### Sprint-Ready Story Groups by Phase

**Phase 1 — Foundation (Sprints 1–4):**
US-ADMIN-001, US-ADMIN-009, US-SUPERADMIN-001, US-ADMIN-002, US-RESP-001, US-RESP-004, US-RESP-006

**Phase 2 — Core Survey Engine (Sprints 5–10):**
US-CREATOR-001 through US-CREATOR-008, US-CREATOR-018, US-CREATOR-019, US-RESP-007, US-RESP-009, US-RESP-010

**Phase 3 — Distribution & Collection (Sprints 11–16):**
US-CREATOR-009 through US-CREATOR-012, US-RESP-002, US-RESP-003, US-RESP-005, US-RESP-008

**Phase 4 — Analytics & Reporting (Sprints 17–22):**
US-ANALYST-001 through US-ANALYST-012, US-CREATOR-013 through US-CREATOR-016

**Phase 5 — Integrations & Admin (Sprints 23–28):**
US-CREATOR-017, US-ADMIN-003 through US-ADMIN-010, US-SUPERADMIN-002 through US-SUPERADMIN-008

---

## Operational Policy Addendum

### 1. Response Data Privacy Policies

**Respondent Rights Implementation**
- User stories US-RESP-005 and US-RESP-006 directly implement GDPR Articles 7 (consent), 17 (right to erasure), and 15 (right of access). These stories are classified MH and must be completed before any identified response collection feature ships to production.
- The consent banner in US-RESP-006 must present the legal basis for processing as configured by the Workspace Admin (US-ADMIN-007). The two stories have a hard dependency tracked in the sprint board.
- US-RESP-005 implements the platform's DSR (Data Subject Request) workflow: the respondent-initiated erasure request flows into the workspace admin view (US-ADMIN-007) and the Super Admin audit log (US-SUPERADMIN-004), creating a full chain of custody for compliance.

**PII Handling in User Stories**
- No user story shall be implemented in a way that exposes raw IP addresses in the frontend. IP geolocation is processed server-side and presented only as country-level data.
- US-RESP-008 (confirmation email) must use the workspace's verified sending domain; stories are blocked from closure if the email compliance check (US-SUPERADMIN-008) is not implemented first.

---

### 2. Survey Distribution Policies

**Anti-Spam Enforcement in Stories**
- US-CREATOR-009 (email campaign) must enforce the pre-send suppression list check as an acceptance criterion. This is a compliance requirement, not optional UX.
- US-CREATOR-011 (reminder emails) must explicitly exclude respondents who have already submitted; this is a compliance requirement under GDPR (no unnecessary re-contact) as well as a product quality expectation.
- US-CREATOR-010 (QR code) does not require a suppression check since it is a passive link; however, the landing page must include the standard consent banner if the survey is configured as identified.

**SMS Stories**
- Any user story involving SMS distribution (not currently in this set but planned for Phase 3) requires a gating acceptance criterion: the workspace admin must have completed the TCPA compliance acknowledgment before the SMS send is permitted.

---

### 3. Analytics and Retention Policies

**k-Anonymity in Analytics Stories**
- US-ANALYST-002 (cross-tabulation), US-ANALYST-003 (sentiment breakdown), and US-ANALYST-011 (geographic map) all must enforce the k-anonymity threshold of k=5 at the data layer.
- The platform's k-anonymity logic is implemented as a shared analytics utility (`app/utils/anonymity.py`) and must be invoked by all analytics export and display endpoints.
- This constraint is documented as a non-negotiable acceptance criterion on US-ANALYST-002, US-ANALYST-005, US-ANALYST-006, and US-ANALYST-011.

**Sentiment Analysis Data Governance**
- US-ANALYST-003 and US-ANALYST-004 (word cloud) must only pass text to AWS Comprehend after verifying that the workspace has not opted out via the setting in US-ADMIN-007.
- Free-text responses containing potentially sensitive content (email addresses, phone numbers detected via regex) are flagged and excluded from word cloud rendering; this is an implicit acceptance criterion for US-ANALYST-004.

---

### 4. System Availability Policies

**Story Prioritization Based on SLA**
- All stories tagged MH (Must Have) represent the minimum viable feature set required to meet the 99.9% SLA commitments on the Business plan. These stories must be completed and passing automated tests before production launch.
- US-RESP-003 (offline PWA) and US-RESP-002 (partial save/resume) are H priority features that directly support availability from the respondent's perspective — they prevent data loss during infrastructure degradation and are treated as P2 incidents if unavailable.
- The analytics pipeline stories (US-ANALYST-001 through US-ANALYST-005) depend on the Kinesis → Lambda → DynamoDB infrastructure being operational. These stories have an infrastructure acceptance criterion: the pipeline must process events within 60 seconds of submission under a 1,000 req/min load.

**Performance Acceptance Criteria Standards**
- All MH stories that involve an API response must include a performance acceptance criterion of ≤ 300 ms at p95 for the primary API operation.
- All H stories involving dashboard loading must include a performance acceptance criterion of ≤ 3 seconds at p95 on broadband.
- These performance criteria are validated in the QA environment using k6 load testing before each story is accepted into the release.
