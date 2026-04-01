# User Stories

**Version:** 1.0 | **Status:** Approved | **Last Updated:** 2025-07-15

---

## Table of Contents

1. [Sales Rep Stories](#1-sales-rep-stories)
2. [Sales Manager Stories](#2-sales-manager-stories)
3. [RevOps Analyst Stories](#3-revops-analyst-stories)
4. [CRM Administrator Stories](#4-crm-administrator-stories)
5. [Marketing Manager Stories](#5-marketing-manager-stories)

---

## Overview

This document captures all user stories for the CRM Platform organised by persona. Each story follows the format:

> **US-XXX** | As a [Persona], I want to [action] so that [benefit].

Acceptance criteria follow the Given/When/Then structure. Priority levels: **Must Have**, **Should Have**, **Nice to Have**.

---

## 1. Sales Rep Stories

---

**US-001** | As a **Sales Rep**, I want to capture a new lead directly from a prospect's website visit so that I can begin the qualification process without leaving the CRM.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** I am logged in as a Sales Rep  
  **When** I navigate to the Leads module and click "New Lead"  
  **Then** a lead creation form is displayed with fields for first name, last name, email, phone, company, job title, and lead source

- **Given** I submit the form with all required fields populated  
  **When** the form is submitted  
  **Then** a Lead record is created with status `New`, assigned to me according to the territory rule, and I receive an in-app confirmation notification

- **Given** I submit the form with the email field blank  
  **When** the form is submitted  
  **Then** the system returns a validation error highlighting the email field as required and no lead is created

---

**US-002** | As a **Sales Rep**, I want to qualify a lead and convert it to a Contact, Account, and Deal in one step so that I do not have to manually create three separate records.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** a Lead with status `New` or `Contacted` exists in my queue  
  **When** I click "Qualify & Convert" on the Lead record  
  **Then** a conversion dialog opens pre-populated with the lead's company name (as Account name), contact details, and a new Deal name defaulting to "[Company] — [Lead Source]"

- **Given** I confirm the conversion with an existing Account selected  
  **When** the conversion is submitted  
  **Then** a new Contact is created linked to the existing Account, a Deal is created in the first stage of the default pipeline, and the Lead status is updated to `Converted` with links to all three created/associated records

- **Given** the conversion operation encounters a database error mid-transaction  
  **When** the error occurs  
  **Then** the entire transaction is rolled back, no partial records are created, and an error message is displayed with a reference ID for support

---

**US-003** | As a **Sales Rep**, I want to log a call with a prospect directly from the Contact record so that the interaction is immediately visible in the activity timeline.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** I am viewing a Contact record  
  **When** I click "Log Call" in the activity bar  
  **Then** a log call panel opens with fields for call date/time, duration, outcome (Connected, Left Voicemail, No Answer, Wrong Number), call direction (Inbound/Outbound), and notes

- **Given** I save a completed call log with outcome "Connected" and notes  
  **When** the log is saved  
  **Then** the activity appears at the top of the Contact's timeline, the Contact's "Last Activity Date" field updates to today's date, and any associated open Deal's next activity date is updated

- **Given** I associate the call log to two records simultaneously (one Contact and one Deal)  
  **When** the log is saved  
  **Then** the activity appears on the timeline of both the Contact record and the Deal record

---

**US-004** | As a **Sales Rep**, I want to advance a deal from "Proposal Sent" to "Negotiation" in the pipeline so that the pipeline view accurately reflects my deal's progress.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** I have a Deal in "Proposal Sent" stage and all entry criteria for "Negotiation" are met (proposal document attached, minimum deal age 3 days elapsed)  
  **When** I drag the Deal card to "Negotiation" or change the Stage field on the Deal record  
  **Then** the Stage updates immediately, the stage probability populates automatically, a `DealStageChanged` event is fired, and a stage change activity log is created on the Deal's timeline

- **Given** the "Negotiation" stage requires a decision maker Contact to be linked but none is present  
  **When** I attempt to advance the Deal  
  **Then** a stage gate blocker modal lists the unmet criteria; the advance is blocked until criteria are satisfied or a manager override is applied

- **Given** a Sales Manager has applied a stage gate override  
  **When** I view the Deal record  
  **Then** a yellow "Stage Gate Overridden" badge is displayed with the manager's name and justification note visible on hover

---

**US-005** | As a **Sales Rep**, I want to submit my monthly forecast so that my manager has visibility into my expected revenue for the period.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** a forecast period is open and I have not yet submitted  
  **When** I navigate to Forecasting and open the current period  
  **Then** I see my deal pipeline grouped by forecast category (Committed, Best Case, Pipeline, Omitted) with deal-level amounts and close dates pre-populated from my open deals

- **Given** I enter a Committed amount of $50,000, Best Case of $75,000, and Pipeline of $120,000  
  **When** I click "Submit Forecast"  
  **Then** the submission is accepted, the forecast status changes to `Submitted`, my manager receives a notification, and my forecast is locked for editing pending manager review

- **Given** I attempt to enter a Committed amount ($80,000) greater than my Best Case amount ($75,000)  
  **When** I click "Submit Forecast"  
  **Then** a validation error is displayed: "Committed amount cannot exceed Best Case amount" and the forecast is not submitted

---

**US-006** | As a **Sales Rep**, I want to see all email correspondence with a Contact in the CRM activity timeline so that I have full conversation context without switching to my email client.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** I have connected my Google Workspace account via OAuth  
  **When** I send an email to a Contact whose email address is registered in the CRM  
  **Then** the email thread appears in the Contact's activity timeline within 5 minutes, showing subject, sender, recipient, timestamp, and a preview of the body

- **Given** a Contact replies to my email  
  **When** the reply is received in my Gmail inbox  
  **Then** the reply is appended to the existing email thread in the CRM activity timeline within 5 minutes; the Contact's "Last Email Date" field is updated

- **Given** an email is received from an address that matches two different Contact records  
  **When** the sync processes the email  
  **Then** the email is associated to all matching Contact records and a triage notification indicates the multi-match association

---

**US-007** | As a **Sales Rep**, I want to be notified when a prospect opens my email so that I can time a follow-up call while the deal is top of mind.

**Priority:** Should Have

**Acceptance Criteria:**

- **Given** I send an email via the CRM email composer with tracking enabled  
  **When** the recipient opens the email  
  **Then** I receive an in-app notification and optionally an email alert (configurable in my notification preferences) within 60 seconds of the open event

- **Given** the same recipient opens the email five times  
  **When** each open event is tracked  
  **Then** the activity timeline shows all open events with individual timestamps; the notification is sent only for the first open event to avoid alert fatigue

- **Given** I view the Deal associated with the tracked email  
  **When** I open the Deal's engagement panel  
  **Then** I see a summary showing total opens, total clicks, last opened timestamp, and links clicked

---

**US-008** | As a **Sales Rep**, I want to view all my tasks due today across all deals and contacts in a single view so that I can prioritise my day without navigating individual records.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** I am logged in as a Sales Rep  
  **When** I navigate to the "My Tasks" view  
  **Then** all tasks assigned to me and due today (or overdue) are listed, sorted by due date ascending, with the associated Contact or Deal name, task type, and priority displayed

- **Given** I complete a task by clicking the checkmark  
  **When** the task is marked complete  
  **Then** it moves to a "Completed Today" section, the task count badge on the navigation icon decrements, and the completion timestamp is recorded on the task record

- **Given** I have no tasks due today  
  **When** I open the "My Tasks" view  
  **Then** a confirmation message is shown: "No tasks due today — great work!" and upcoming tasks (due in the next 7 days) are listed in a secondary section

---

## 2. Sales Manager Stories

---

**US-009** | As a **Sales Manager**, I want to view my entire team's pipeline on a single Kanban board so that I can identify stalled deals and intervene proactively.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** I am logged in as a Sales Manager  
  **When** I navigate to the Team Pipeline view  
  **Then** all open deals owned by my direct reports are displayed across pipeline stages, grouped by rep, with deal amount, close date, and days-in-stage visible on each card

- **Given** a deal has been in the same stage for more than 14 days  
  **When** I view the Kanban board  
  **Then** that deal card is highlighted with a stagnation indicator showing the number of days in stage

- **Given** I click on any deal card  
  **When** the deal record opens  
  **Then** I can view the full deal record, activity timeline, and add a coaching note without being redirected away from the Kanban board context

---

**US-010** | As a **Sales Manager**, I want to review and approve my team's forecast submissions so that the consolidated forecast accurately reflects my team's revenue commitment.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** one or more of my direct reports have submitted their forecasts  
  **When** I navigate to the Forecast Approval view  
  **Then** I see a rollup table showing each rep's Committed, Best Case, and Pipeline amounts alongside their quota attainment percentage and prior period submission

- **Given** I approve a rep's forecast  
  **When** I click "Approve"  
  **Then** the forecast status changes to `Approved`, a point-in-time snapshot is locked, the rep receives a confirmation notification, and the approved amount is added to my team rollup

- **Given** I reject a rep's forecast with the comment "Committed amount too aggressive given Q3 pipeline coverage"  
  **When** I click "Reject with Comment"  
  **Then** the forecast returns to `Draft` status, the rep sees the rejection and my comment, and the rep is required to revise and resubmit within 48 hours

---

**US-011** | As a **Sales Manager**, I want to assign territories to new sales reps joining my team so that their accounts and leads are automatically routed to them.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** a new Sales Rep user has been created in the system  
  **When** I navigate to Territory Management and assign the new rep to an existing territory  
  **Then** all Accounts belonging to that territory are updated with the new rep as owner; all open Leads matching the territory criteria are reassigned to the new rep within 30 minutes

- **Given** the territory has Deals currently owned by the departing rep  
  **When** the reassignment executes  
  **Then** open Deals are transferred to the new rep; closed Deals retain the original owner for historical reporting; the new rep receives a summary notification listing all transferred records

- **Given** a territory reassignment conflicts with an existing named-account assignment  
  **When** the system detects the conflict  
  **Then** the named-account exclusion is preserved, the conflicting record is flagged in the reassignment preview, and the manager must explicitly override or exclude the conflicting account before finalising

---

**US-012** | As a **Sales Manager**, I want to see a quota attainment dashboard for my team so that I can coach underperforming reps before the quarter closes.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** quotas have been set for all my direct reports for the current quarter  
  **When** I open the Team Quota Dashboard  
  **Then** a table shows each rep's quarterly quota, closed won amount to date, attainment percentage, remaining days in quarter, and projected attainment based on current pipeline weighted by close date probability

- **Given** a rep is below 50% attainment with less than 30 days remaining in the quarter  
  **When** I view the dashboard  
  **Then** that rep's row is highlighted in amber (50–74% attainment) or red (below 50% attainment) to draw my attention

- **Given** I click on a rep's name in the dashboard  
  **When** the drill-down opens  
  **Then** I see the rep's deal-level breakdown showing each deal's stage, amount, close date, and probability contributing to the attainment calculation

---

**US-013** | As a **Sales Manager**, I want to override a stage gate blocker for a deal so that I can unblock a rep when there is valid business justification.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** a Deal is blocked from advancing due to an unmet stage gate criterion  
  **When** I navigate to the Deal record and click "Manager Override"  
  **Then** a mandatory justification text field is displayed; I must enter a minimum of 20 characters before the override can be applied

- **Given** I submit a valid justification  
  **When** the override is applied  
  **Then** the Deal advances to the target stage, an override event is logged in the audit trail with my name, timestamp, and justification, and the Deal record displays a persistent "Stage Gate Override" indicator

---

**US-014** | As a **Sales Manager**, I want to receive a weekly pipeline digest email so that I have a concise summary of my team's pipeline health before my Monday morning team meeting.

**Priority:** Should Have

**Acceptance Criteria:**

- **Given** the weekly digest job runs every Monday at 07:00 in my configured timezone  
  **When** the email is generated  
  **Then** it includes: total pipeline value vs. prior week, new deals added, deals that advanced stages, deals that slipped their close date, deals stagnant > 14 days, and top 5 deals by amount with their current stage

- **Given** I have opted out of the weekly digest in my notification preferences  
  **When** Monday digest generation runs  
  **Then** no email is sent to me but the digest remains available as an in-app report under Reports > Pipeline Digest

---

**US-015** | As a **Sales Manager**, I want to set individual monthly and quarterly revenue quotas for each of my direct reports so that attainment can be tracked automatically.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** I navigate to the Quota Management section  
  **When** I select a rep and a quota period  
  **Then** I can enter a monthly quota amount and a quarterly quota amount independently; existing quotas are editable until the period's start date after which they require RevOps Analyst approval to change

- **Given** I save a quota change  
  **When** the change is persisted  
  **Then** the rep's home dashboard reflects the new quota immediately; the previous quota value is retained in the audit trail with the change timestamp and my user ID; the rep receives a notification of the updated quota

---

**US-016** | As a **Sales Manager**, I want to add a coaching note to a rep's deal so that my feedback is visible to the rep in context without requiring a separate meeting.

**Priority:** Should Have

**Acceptance Criteria:**

- **Given** I am viewing a Deal owned by one of my direct reports  
  **When** I click "Add Coaching Note"  
  **Then** a note editor opens, prefixed with a "Coaching" badge, allowing rich text input; the note is visible to the deal owner and all managers in the hierarchy but not to other reps

---

## 3. RevOps Analyst Stories

---

**US-017** | As a **RevOps Analyst**, I want to configure pipeline stages with entry and exit gate criteria so that deals progress through a consistent, quality-controlled sales process.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** I am in the Pipeline Configuration view  
  **When** I add a new stage "Technical Evaluation" and configure entry criteria: "Technical Requirements Document attached" and "Minimum deal age: 5 days"  
  **Then** the criteria are saved and enforced immediately for all new deal stage advancement attempts; existing deals in a prior stage are not retroactively affected

- **Given** I change the default probability of a stage from 50% to 60%  
  **When** the change is saved  
  **Then** all deals in that stage (that have not been manually overridden) update their probability to 60% within 5 minutes; weighted forecast values are recalculated

---

**US-018** | As a **RevOps Analyst**, I want to review and resolve duplicate Contact records identified by the deduplication engine so that the CRM data quality remains high.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** the dedup engine has flagged a Contact pair with 72% match confidence  
  **When** I open the Dedup Review queue  
  **Then** the pair is displayed side-by-side with all matching fields highlighted, a confidence score, and the matching criteria that triggered the flag (e.g., "Same email domain + 88% name similarity")

- **Given** I decide to merge the two records  
  **When** I designate the master record and click "Merge"  
  **Then** all activities, deals, and campaign memberships from the duplicate are transferred to the master; the duplicate is soft-deleted; the merge operation is recorded in the audit log with my user ID, timestamp, and the IDs of both records

- **Given** I decide the two records are genuinely different people  
  **When** I click "Not a Duplicate"  
  **Then** the pair is marked as a confirmed non-duplicate and will not be surfaced again by the dedup engine; this decision is logged and can be reversed by a CRM Administrator

---

**US-019** | As a **RevOps Analyst**, I want to define territory rules using multi-criteria logic so that accounts are automatically routed to the correct rep.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** I create a territory rule: Industry = "Financial Services" AND Annual Revenue >= $10M AND Region = "North America"  
  **When** the rule is activated  
  **Then** all existing accounts matching the criteria are assigned to the territory within 1 hour; new accounts matching the criteria are assigned within 5 minutes of creation

- **Given** an account matches two territory rules simultaneously  
  **When** the assignment engine evaluates it  
  **Then** the rule with the highest priority number (as configured in the territory rule ordering) wins; the conflict is logged; the RevOps Analyst receives a conflict notification

---

**US-020** | As a **RevOps Analyst**, I want to perform a bulk territory reassignment so that I can efficiently realign the sales organisation after a team restructure.

**Priority:** Should Have

**Acceptance Criteria:**

- **Given** I navigate to the Territory Reassignment tool and select source territory "West Coast — Mid Market" and target territory "Pacific — Enterprise"  
  **When** I click "Preview Reassignment"  
  **Then** a summary shows: X Accounts, Y open Deals, Z active Leads, and W open Activities that will be reassigned; I can download this list as CSV before confirming

- **Given** I confirm the bulk reassignment  
  **When** the operation processes more than 1,000 records  
  **Then** it runs as a background job; I receive an in-app notification and email when complete; the job status is visible in the Operations log; all reassigned records show the new territory and owner in the audit trail

---

**US-021** | As a **RevOps Analyst**, I want to build a custom report on opportunity pipeline coverage by territory so that I can advise leadership on territory balance.

**Priority:** Should Have

**Acceptance Criteria:**

- **Given** I open the Report Builder  
  **When** I select Deals as the primary object and add dimensions: Territory, Pipeline Stage, Close Month and metrics: Count of Deals, Sum of Amount, Average Days in Stage  
  **Then** the report query executes and returns results within 10 seconds; results are displayed as a pivot table and optionally as a stacked bar chart

- **Given** I save the report and schedule it to run every Monday at 06:00  
  **When** the scheduled run executes  
  **Then** an email with the report attached as CSV and PDF is sent to the distribution list I configured; the report run history shows the last 10 executions with run time and row count

---

**US-022** | As a **RevOps Analyst**, I want to track GDPR erasure requests through a managed workflow so that compliance obligations are met within the 30-day window.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** a GDPR erasure request is submitted via the compliance portal  
  **When** the request is received  
  **Then** an erasure task is created in the Compliance Workflow queue with a 30-day due date countdown; all records linked to the subject's email address across Leads, Contacts, Email Activities, and Campaign Memberships are identified and listed on the task

- **Given** the erasure is executed  
  **When** I click "Execute Erasure"  
  **Then** all PII fields are irreversibly overwritten with anonymised tokens; the Contact record is retained as a shell for audit trail continuity; a completion timestamp and operator ID are recorded in the immutable erasure log; a confirmation is sent to the requester

---

## 4. CRM Administrator Stories

---

**US-023** | As a **CRM Administrator**, I want to create a custom picklist field "Customer Success Tier" on the Account object so that Sales Reps can categorise accounts for prioritisation.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** I navigate to Settings > Custom Fields > Account  
  **When** I create a new picklist field named "Customer Success Tier" with options: Platinum, Gold, Silver, Bronze  
  **Then** the field appears in the Account form, list view columns (configurable), API responses, and the Report Builder within 60 seconds of saving; no deployment is required

- **Given** I mark the field as required  
  **When** a Sales Rep attempts to save an Account record without selecting a value  
  **Then** the form returns a validation error and the record is not saved

- **Given** I later deprecate the "Bronze" picklist option  
  **When** the option is marked inactive  
  **Then** existing records with "Bronze" retain their value but "Bronze" is no longer available as a selection for new or edited records

---

**US-024** | As a **CRM Administrator**, I want to configure an integration with our Slack workspace so that Sales Reps receive deal stage change notifications in their designated Slack channel.

**Priority:** Should Have

**Acceptance Criteria:**

- **Given** I enter the Slack Incoming Webhook URL in the Integrations settings  
  **When** I test the connection  
  **Then** a test message "CRM Platform connected" appears in the configured Slack channel within 30 seconds

- **Given** the integration is active and a Deal advances to "Closed Won"  
  **When** the stage change is saved  
  **Then** a Slack message is posted to the configured channel within 60 seconds, containing: deal name, amount, account name, rep name, and a deep link to the Deal record

---

**US-025** | As a **CRM Administrator**, I want to manage user roles and permissions so that each persona has access only to the CRM objects and actions appropriate to their function.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** I create a new role "Junior Sales Rep" with read/write access to Leads and Contacts but read-only access to Deals, and no access to Territory or Forecast modules  
  **When** I assign this role to a user  
  **Then** the user's navigation menu only shows permitted modules; API calls to restricted endpoints return HTTP 403; the permission change is logged in the audit trail

- **Given** a user's role is changed from "Sales Rep" to "Sales Manager"  
  **When** the change is saved  
  **Then** the new permissions take effect on the user's next page load or API request, without requiring re-authentication; all previously permitted actions remain auditable under their original role context

---

**US-026** | As a **CRM Administrator**, I want to perform a bulk data import of Contacts from a CSV file so that I can migrate data from a legacy system.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** I upload a CSV file with 25,000 Contact rows  
  **When** the file is uploaded  
  **Then** a pre-import validation report identifies: missing required fields (row-level), malformed email addresses, duplicate emails within the file, and emails already existing in the CRM — all before any records are created

- **Given** I confirm the import after reviewing the validation report  
  **When** the import executes  
  **Then** valid rows create Contact records; rows with errors are skipped; a completion report shows created count, skipped count, and a downloadable error CSV with per-row error messages; duplicate detection runs on each imported contact

---

**US-027** | As a **CRM Administrator**, I want to view and query the audit log so that I can investigate suspicious activity and respond to security incidents.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** I navigate to the Audit Log viewer  
  **When** I filter by user "john.doe@company.com", object type "Contact", and date range "2025-07-01 to 2025-07-15"  
  **Then** all audit events matching the criteria are returned and displayed in a paginated table showing timestamp, operation, object ID, changed fields (before/after values), and source IP

- **Given** I attempt to delete an audit log entry  
  **When** the delete is attempted via API or UI  
  **Then** HTTP 405 (Method Not Allowed) is returned and the entry is not modified; this restriction applies to all user roles including CRM Administrator

---

**US-028** | As a **CRM Administrator**, I want to configure the lead scoring model so that the scoring rules reflect our current ideal customer profile.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** I navigate to Settings > Lead Scoring  
  **When** I add a new rule "Job Title contains 'VP' or 'Director': +15 points"  
  **Then** the rule is saved and applied to all future lead scoring evaluations; I can optionally trigger a retroactive rescore of all existing open leads

- **Given** I deactivate a scoring rule  
  **When** the rule is marked inactive  
  **Then** it no longer contributes to lead scores on new evaluations; existing lead scores are not immediately changed but will update on the next evaluation trigger

---

## 5. Marketing Manager Stories

---

**US-029** | As a **Marketing Manager**, I want to create a dynamic segment of Contacts based on industry, company size, and engagement score so that I can target the right audience for a product launch campaign.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** I navigate to Segments and create a new segment with criteria: Industry = "Technology" AND Employee Count >= 500 AND Lead Score >= 60  
  **When** the segment is saved  
  **Then** the estimated member count is displayed immediately; the segment is dynamic and membership updates automatically as contact data changes; I can preview the first 50 members before creating a campaign

- **Given** I add a new criterion "No email activity in last 90 days"  
  **When** the segment recalculates  
  **Then** the estimated member count updates within 30 seconds reflecting the additional filter

---

**US-030** | As a **Marketing Manager**, I want to launch a 3-step email drip campaign so that I can nurture leads over a 2-week period without manual intervention.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** I create a campaign with three email steps: Step 1 sends immediately, Step 2 sends 5 days after Step 1 if the contact has not replied, Step 3 sends 7 days after Step 2 if the contact has not clicked a link  
  **When** the campaign is activated  
  **Then** Step 1 sends to all eligible segment members at the scheduled time; Steps 2 and 3 respect the conditional delays and exclusion rules; contacts who reply before Step 2 are automatically removed from the remaining sequence

- **Given** I click "Launch Campaign"  
  **When** the launch is confirmed  
  **Then** a pre-send checklist validates: segment not empty, email steps all have subject lines and body content, sender address is authenticated (SPF/DKIM verified), and unsubscribe link is present in each email step

---

**US-031** | As a **Marketing Manager**, I want to view real-time campaign analytics so that I can adjust messaging based on engagement data.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** a campaign is active and sending  
  **When** I open the Campaign Analytics dashboard  
  **Then** I see metrics updated within 5 minutes: emails sent, delivered, bounced (soft/hard), open rate, unique open rate, click rate, click-to-open rate, unsubscribes, and spam complaints, displayed as both numbers and percentages

- **Given** the open rate for Step 1 is below 20%  
  **When** I identify this in the analytics  
  **Then** I can pause the campaign to create an A/B variant of Step 1 subject line; pausing is reflected in the campaign status within 60 seconds; contacts who have already received Step 1 are not re-sent

---

**US-032** | As a **Marketing Manager**, I want to ensure unsubscribe requests are processed immediately so that we remain CAN-SPAM and GDPR compliant.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** a Contact clicks the unsubscribe link in a campaign email  
  **When** the link is clicked  
  **Then** the Contact's `unsubscribed` flag is set to `true` within 10 seconds; a `ContactUnsubscribed` event is fired; the contact is excluded from all future campaign sends immediately; a confirmation page is displayed to the contact confirming their unsubscribe

- **Given** I attempt to manually add an unsubscribed Contact to a new campaign segment  
  **When** the campaign launches  
  **Then** the contact is automatically excluded from the send; a warning appears in the campaign pre-send checklist noting that X contacts in the segment are unsubscribed and will be excluded

---

**US-033** | As a **Marketing Manager**, I want to coordinate the lead handoff threshold with the Sales team so that Marketing-qualified leads are only passed to Sales when they meet the agreed-upon criteria.

**Priority:** Should Have

**Acceptance Criteria:**

- **Given** I navigate to Lead Handoff Settings  
  **When** I set the MQL (Marketing Qualified Lead) threshold to "Lead Score >= 75 AND Job Title contains VP/Director/C-Level AND Company Size >= 100 employees"  
  **Then** leads meeting all criteria are automatically promoted to MQL status and appear in the Sales team's lead assignment queue; leads not meeting the threshold remain in the Marketing nurture segment

- **Given** a lead's score increases from 70 to 78 due to new behavioural signals  
  **When** the scoring engine runs  
  **Then** if all MQL criteria are now met, the lead is immediately re-evaluated and promoted to MQL status; the assigned Sales Rep receives a notification of the MQL conversion

---

**US-034** | As a **Marketing Manager**, I want to manage the global email suppression list so that known-invalid and opted-out addresses are never sent campaign emails.

**Priority:** Must Have

**Acceptance Criteria:**

- **Given** I navigate to Email Settings > Suppression List  
  **When** I upload a CSV of email addresses to suppress  
  **Then** all uploaded addresses are added to the global suppression list within 60 seconds; any campaign send to these addresses is automatically blocked regardless of the contact's individual unsubscribe status

- **Given** a campaign results in a hard bounce for a specific email address  
  **When** the bounce is processed  
  **Then** the address is automatically added to the suppression list and the Contact's `email_deliverable` field is set to `false`; a suppression event is logged in the contact's activity timeline

---

**US-035** | As a **Marketing Manager**, I want to track which campaign influenced a closed-won deal so that I can report on marketing ROI.

**Priority:** Should Have

**Acceptance Criteria:**

- **Given** a Contact is a member of an active campaign and is also associated with a Deal that closes as Won  
  **When** the deal is marked Closed Won  
  **Then** the campaign is recorded as a "campaign influence" on the Deal record with the touch date and campaign name; a Deal can have multiple campaign influences (first touch, last touch, multi-touch attribution)

- **Given** I open the Campaign Analytics for a specific campaign  
  **When** I view the "Pipeline Influence" tab  
  **Then** I see total influenced pipeline value, total influenced closed-won amount, and a list of influenced deals with amounts and close dates, allowing me to calculate the campaign's contribution to revenue
