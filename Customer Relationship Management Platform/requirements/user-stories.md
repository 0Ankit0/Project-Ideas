# User Stories — Customer Relationship Management Platform

**Version:** 1.0  
**Status:** Approved  
**Last Updated:** 2025-07-15

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Lead Management Stories](#2-lead-management-stories)
3. [Contact and Account Management Stories](#3-contact-and-account-management-stories)
4. [Opportunity and Pipeline Stories](#4-opportunity-and-pipeline-stories)
5. [Activity and Communication Stories](#5-activity-and-communication-stories)
6. [Campaign and Marketing Stories](#6-campaign-and-marketing-stories)
7. [Forecasting and Territory Stories](#7-forecasting-and-territory-stories)
8. [Configuration and Administration Stories](#8-configuration-and-administration-stories)
9. [Integration and API Stories](#9-integration-and-api-stories)
10. [Data Quality and Compliance Stories](#10-data-quality-and-compliance-stories)
11. [Story Mapping](#11-story-mapping)

---

## 1. Introduction

### 1.1 Purpose

This document captures user stories for the CRM Platform from the perspective of each actor (Sales Rep, Sales Manager, Marketing Manager, CRM Administrator, RevOps Analyst, System Integrator). Each story follows the format: **As a [role], I want [capability] so that [benefit]**, with Given/When/Then acceptance criteria and priority classification.

### 1.2 Story Prioritization

| Priority | Label | Description |
|---|---|---|
| P0 | Must Have | Critical for MVP; system is unusable without this feature |
| P1 | Should Have | High value; planned for v1.0 release |
| P2 | Nice to Have | Lower value; may be deferred to v1.1+ |

### 1.3 Acceptance Criteria Format

All stories use **Given/When/Then** format:
- **Given:** Preconditions and context
- **When:** Action or event trigger
- **Then:** Expected outcome and side effects

---

## 2. Lead Management Stories

### US-001 — Capture Lead from Web Form

**As a** Marketing Manager  
**I want** to embed a lead capture form on our website  
**So that** prospects can submit their contact information and be automatically added to our CRM

**Priority:** P0  
**Story Points:** 5  
**Related FR:** FR-001

**Acceptance Criteria:**

**Given** I have configured a lead capture form with fields: First Name, Last Name, Email, Company, Phone  
**When** a prospect visits the form, fills all required fields, and clicks "Submit"  
**Then** the system creates a new Lead record with status "New", assigns it to the default queue, sends a confirmation email to the prospect, and triggers the lead scoring engine

**Given** the form includes reCAPTCHA v3 integration  
**When** a bot attempts to submit the form with a low reCAPTCHA score (< 0.5)  
**Then** the submission is rejected with a user-friendly error message, and a security event is logged

**Given** a prospect submits a form with an email address that already exists in the CRM  
**When** the submission is processed  
**Then** the system detects the duplicate, increments the lead_submission_count field on the existing Lead, and does NOT create a duplicate Lead record

---

### US-002 — Customize Web Form Fields

**As a** Marketing Manager  
**I want** to customize which fields appear on my lead capture form  
**So that** I can collect the specific information relevant to my campaigns

**Priority:** P1  
**Story Points:** 3  
**Related FR:** FR-001

**Acceptance Criteria:**

**Given** I am logged into the CRM as a Marketing Manager  
**When** I navigate to Settings → Lead Forms → Create Form  
**Then** I see a form builder UI where I can drag-and-drop fields (text, email, phone, dropdown, checkbox, text area) onto the form canvas

**Given** I have added fields to the form  
**When** I mark a field as "Required"  
**Then** the form displays a red asterisk next to the field label, and submission is blocked if the field is empty

**Given** I have finished configuring the form  
**When** I click "Save & Get Embed Code"  
**Then** the system generates a JavaScript snippet that I can copy and paste into my website's HTML

---

### US-003 — Submit Lead via API

**As a** System Integrator  
**I want** to submit leads to the CRM via a REST API  
**So that** I can integrate our marketing automation platform with the CRM

**Priority:** P0  
**Story Points:** 3  
**Related FR:** FR-002

**Acceptance Criteria:**

**Given** I have obtained an API key with "leads:write" scope  
**When** I send a POST request to `/api/v1/leads` with JSON payload `{"first_name": "John", "last_name": "Doe", "email": "john@example.com", "company": "Acme Corp"}`  
**Then** the system responds with HTTP 201, returns the created Lead ID, and includes a `Location` header pointing to the new resource

**Given** I send a POST request with an invalid email format  
**When** the request is processed  
**Then** the system responds with HTTP 422 and a JSON error payload: `{"error": "VALIDATION_ERROR", "fields": {"email": "Invalid email format"}}`

**Given** I include an `Idempotency-Key` header in my request  
**When** I retry the same request within 24 hours  
**Then** the system returns the original Lead ID (HTTP 200) instead of creating a duplicate

---

### US-004 — Bulk Import Leads from CSV

**As a** RevOps Analyst  
**I want** to bulk import leads from a CSV file  
**So that** I can onboard large lead lists from trade shows or purchased databases

**Priority:** P1  
**Story Points:** 8  
**Related FR:** FR-003

**Acceptance Criteria:**

**Given** I have a CSV file with 10,000 rows and columns: First Name, Last Name, Email, Company, Phone, Source  
**When** I navigate to Leads → Import → Upload CSV, select the file, and map CSV columns to CRM fields  
**Then** the system displays a preview of the first 10 rows with mapped values

**Given** the preview looks correct  
**When** I click "Validate Import"  
**Then** the system validates all 10,000 rows and displays a validation report showing: total rows, valid rows, invalid rows, and a list of errors (row number, field, error message)

**Given** the validation report shows 9,500 valid rows and 500 invalid rows  
**When** I click "Import Valid Rows" and confirm  
**Then** the system creates a background job, imports the 9,500 valid rows, emails me a completion summary, and provides a downloadable CSV of the 500 failed rows with error details

---

### US-005 — View Lead Score

**As a** Sales Rep  
**I want** to see each lead's score (0-100) in the lead list view  
**So that** I can prioritize my outreach to the hottest leads first

**Priority:** P1  
**Story Points:** 2  
**Related FR:** FR-004

**Acceptance Criteria:**

**Given** I am viewing the Leads list page  
**When** the page loads  
**Then** each lead row displays a score badge with color coding: 0-30 (red), 31-70 (yellow), 71-100 (green)

**Given** I click on a lead score badge  
**When** the detail panel opens  
**Then** I see a breakdown of how the score was calculated (e.g., "+20 Company Size > 1000 employees, +15 Industry Match, +10 Email Domain Match, +5 Page Visits = 50 total")

---

### US-006 — Configure Lead Scoring Rules

**As a** RevOps Analyst  
**I want** to configure the lead scoring rule set  
**So that** the scoring algorithm reflects our ideal customer profile

**Priority:** P1  
**Story Points:** 8  
**Related FR:** FR-004

**Acceptance Criteria:**

**Given** I navigate to Settings → Lead Scoring → Rules  
**When** the page loads  
**Then** I see a list of existing scoring rules with columns: Rule Name, Condition, Points, Active (yes/no)

**Given** I click "Add Rule"  
**When** I fill in: Rule Name = "Enterprise Size", Condition = "Company.employee_count > 1000", Points = 20, Active = Yes  
**Then** the system saves the rule and immediately applies it to all existing leads (background job)

**Given** a new lead is created with company employee_count = 1500  
**When** the lead scoring engine evaluates the rules  
**Then** the lead receives +20 points from the "Enterprise Size" rule

---

### US-007 — Auto-Assign Lead to Sales Rep

**As a** RevOps Analyst  
**I want** to configure automatic lead assignment rules based on territory and lead attributes  
**So that** leads are routed to the right rep without manual intervention

**Priority:** P0  
**Story Points:** 8  
**Related FR:** FR-005

**Acceptance Criteria:**

**Given** I configure an assignment rule: "If Lead.country = 'USA' AND Lead.state = 'California', assign to User 'John Smith'"  
**When** a new lead is created with country = "USA" and state = "California"  
**Then** the system sets lead.owner_id = John Smith's user ID, changes lead.status to "Assigned", and sends an email notification to John Smith

**Given** I configure a round-robin rule: "Distribute leads with source = 'Web Form' evenly among users in pool ['Alice', 'Bob', 'Carol']"  
**When** three consecutive leads with source = "Web Form" are created  
**Then** the system assigns them in order: Lead 1 → Alice, Lead 2 → Bob, Lead 3 → Carol, Lead 4 → Alice, etc.

**Given** a lead does not match any assignment rule  
**When** the lead is created  
**Then** the system leaves lead.owner_id as NULL and places the lead in the "Unassigned Leads" queue

---

### US-008 — Convert Lead to Contact and Opportunity

**As a** Sales Rep  
**I want** to convert a qualified lead into a contact, account, and opportunity  
**So that** I can begin managing the sales process in the pipeline

**Priority:** P0  
**Story Points:** 8  
**Related FR:** FR-006

**Acceptance Criteria:**

**Given** I am viewing a lead detail page for a qualified lead  
**When** I click "Convert Lead"  
**Then** the system displays a conversion wizard with steps: 1) Link or Create Account, 2) Create Opportunity (optional), 3) Map Custom Fields

**Given** I choose "Create New Account" and enter account name = "Acme Corp"  
**And** I choose "Create Opportunity" with amount = $50,000, close date = 2025-12-31, stage = "Qualification"  
**When** I click "Convert"  
**Then** the system creates a Contact record (from lead data), an Account record, an Opportunity record, sets lead.status = "Converted", and redirects me to the new Contact detail page

**Given** the lead has custom field values: "Campaign Source" = "Trade Show 2025"  
**When** I convert the lead and the field mapping includes "Campaign Source" → Opportunity.custom_fields  
**Then** the new Opportunity has custom_field "Campaign Source" = "Trade Show 2025"

---

### US-009 — View Converted Lead History

**As a** Sales Rep  
**I want** to view the original lead record even after conversion  
**So that** I can reference the lead source and initial touchpoint data

**Priority:** P1  
**Story Points:** 2  
**Related FR:** FR-006

**Acceptance Criteria:**

**Given** I have converted a lead to a contact  
**When** I view the Contact detail page  
**Then** I see a "Converted from Lead" section showing: lead source, lead created date, lead score at conversion, and a link to the archived lead record

**Given** I click the link to the archived lead record  
**When** the lead detail page loads  
**Then** I see a read-only view of the original lead data with a banner indicating "This lead was converted to Contact [Name] on [Date]"

---

## 3. Contact and Account Management Stories

### US-010 — Create Contact Manually

**As a** Sales Rep  
**I want** to manually create a contact record  
**So that** I can add prospects I met at events or through cold outreach

**Priority:** P0  
**Story Points:** 3  
**Related FR:** FR-007

**Acceptance Criteria:**

**Given** I navigate to Contacts → New Contact  
**When** I fill in: First Name = "Jane", Last Name = "Smith", Email = "jane@example.com", Account = "Example Corp", Phone = "+1-555-0123"  
**And** I click "Save"  
**Then** the system creates the contact, assigns contact.owner_id = my user ID, and redirects me to the contact detail page

**Given** I attempt to create a contact with an email that already exists  
**When** I click "Save"  
**Then** the system displays an error: "A contact with this email already exists. View existing contact or merge duplicate."

---

### US-011 — Edit Contact Information

**As a** Sales Rep  
**I want** to update contact details when I learn new information  
**So that** the CRM data stays current and accurate

**Priority:** P0  
**Story Points:** 2  
**Related FR:** FR-007

**Acceptance Criteria:**

**Given** I am viewing a contact detail page  
**When** I click "Edit", update the phone number from "+1-555-0123" to "+1-555-9999", and click "Save"  
**Then** the system updates the contact record, logs the change in the audit trail with my user ID and timestamp, and triggers a `ContactUpdated` domain event

**Given** another user is simultaneously editing the same contact  
**When** I attempt to save my changes after the other user has saved  
**Then** the system displays a conflict warning: "This record was modified by [User Name] at [Time]. Please refresh and reapply your changes."

---

### US-012 — Create Account Record

**As a** Sales Rep  
**I want** to create an account (company) record  
**So that** I can associate multiple contacts with their organization

**Priority:** P0  
**Story Points:** 3  
**Related FR:** FR-008

**Acceptance Criteria:**

**Given** I navigate to Accounts → New Account  
**When** I fill in: Account Name = "Global Tech Inc", Domain = "globaltech.com", Industry = "Technology", Employee Count = 5000, Annual Revenue = $500M  
**And** I click "Save"  
**Then** the system creates the account, auto-assigns account.territory_id based on territory rules, assigns account.owner_id = my user ID, and redirects me to the account detail page

**Given** the account domain = "globaltech.com" matches an existing account  
**When** I click "Save"  
**Then** the system displays a warning: "An account with this domain already exists. View existing account or continue anyway."

---

### US-013 — View Contact 360° Timeline

**As a** Sales Rep  
**I want** to see all activities, emails, meetings, and deals related to a contact on a single page  
**So that** I have full context before my next interaction

**Priority:** P1  
**Story Points:** 5  
**Related FR:** FR-009

**Acceptance Criteria:**

**Given** I am viewing a contact detail page for a contact with 100 activities (calls, emails, meetings, notes)  
**When** the page loads  
**Then** the activity timeline displays the most recent 20 activities in reverse chronological order with infinite scroll for older items

**Given** the contact has activities of type: Call (10), Email (50), Meeting (5), Note (35)  
**When** I filter the timeline by activity type = "Call"  
**Then** the timeline displays only the 10 call activities

**Given** the contact has 5 open deals and 3 closed deals  
**When** I scroll to the "Related Deals" section  
**Then** I see cards for all 8 deals with: deal name, amount, stage, close date, progress bar (for open deals), and win/loss reason (for closed deals)

---

## 4. Opportunity and Pipeline Stories

### US-014 — Configure Sales Pipeline

**As a** CRM Administrator  
**I want** to create a custom sales pipeline with stages that match our sales process  
**So that** reps can track deals through our standardized methodology

**Priority:** P0  
**Story Points:** 5  
**Related FR:** FR-010

**Acceptance Criteria:**

**Given** I navigate to Settings → Pipelines → New Pipeline  
**When** I enter: Pipeline Name = "Enterprise Sales", Stages = ["Discovery", "Technical Evaluation", "Proposal", "Negotiation", "Closed Won", "Closed Lost"] with probabilities [20%, 40%, 60%, 80%, 100%, 0%]  
**And** I click "Save"  
**Then** the system creates the pipeline and makes it available for selection when creating new deals

**Given** the pipeline has stages with order: 1) Discovery, 2) Technical Evaluation, 3) Proposal  
**When** a rep creates a new deal and selects stage = "Proposal"  
**Then** the system allows this (stages can be entered at any point, not strictly sequential)

---

### US-015 — Create Opportunity

**As a** Sales Rep  
**I want** to create a new opportunity when a prospect expresses interest  
**So that** I can track the deal through the pipeline and forecast revenue

**Priority:** P0  
**Story Points:** 3  
**Related FR:** FR-011

**Acceptance Criteria:**

**Given** I navigate to Opportunities → New Opportunity  
**When** I fill in: Opportunity Name = "Acme Corp - Platform License", Account = "Acme Corp", Amount = $100,000, Currency = USD, Close Date = 2025-12-31, Stage = "Qualification", Pipeline = "Standard Sales"  
**And** I click "Save"  
**Then** the system creates the opportunity, sets opportunity.owner_id = my user ID, sets probability = stage default probability, and redirects me to the opportunity detail page

**Given** I create an opportunity with amount = $100,000 and stage probability = 60%  
**When** the opportunity is saved  
**Then** the system calculates weighted_amount = $100,000 × 0.60 = $60,000 and stores it for forecast rollup calculations

---

### US-016 — Edit Opportunity Details

**As a** Sales Rep  
**I want** to update opportunity details as the deal progresses  
**So that** my forecast and pipeline view reflect the current state

**Priority:** P0  
**Story Points:** 2  
**Related FR:** FR-011

**Acceptance Criteria:**

**Given** I am viewing an opportunity detail page  
**When** I click "Edit", update amount from $100,000 to $120,000, update close date from 2025-12-31 to 2025-11-30, and click "Save"  
**Then** the system updates the opportunity, recalculates weighted_amount, logs the changes in the audit trail, and triggers an `OpportunityUpdated` event

**Given** the opportunity amount was changed  
**When** the update is saved  
**Then** the forecast rollup for my manager is automatically recalculated to include the new amount

---

### US-017 — Move Deal to Next Stage

**As a** Sales Rep  
**I want** to drag-and-drop deals between stages in a kanban view  
**So that** I can quickly update deal progress

**Priority:** P0  
**Story Points:** 5  
**Related FR:** FR-012

**Acceptance Criteria:**

**Given** I am viewing the Pipeline Kanban board with stages: Discovery, Qualification, Proposal, Negotiation, Closed Won  
**When** I drag a deal card from "Qualification" column to "Proposal" column  
**Then** the system updates opportunity.stage_id, updates opportunity.probability to the "Proposal" stage's default probability, creates a DealStageHistory record, and triggers a `DealStageChanged` event

**Given** I move a deal to the "Closed Won" stage  
**When** the drop completes  
**Then** the system validates that amount > 0 and close_date is set; if validation fails, the system reverts the drag and displays an error message

**Given** I move a deal to the "Closed Lost" stage  
**When** the drop completes  
**Then** the system displays a modal prompting me to select a loss reason: ["Competitor", "Budget", "Timing", "No Decision", "Other"] and enter optional notes

---

### US-018 — Submit Individual Forecast

**As a** Sales Rep  
**I want** to submit my revenue forecast for the current quarter  
**So that** my manager can review and approve my commit

**Priority:** P1  
**Story Points:** 5  
**Related FR:** FR-013

**Acceptance Criteria:**

**Given** I navigate to Forecasting → My Forecast → Q4 2025  
**When** the page loads  
**Then** the system displays three forecast categories with auto-calculated totals from my pipeline: Committed ($200K), Best Case ($350K), Pipeline ($500K)

**Given** the auto-calculated Committed amount is $200K but I want to commit $180K  
**When** I manually adjust the Committed field to $180K and click "Submit Forecast"  
**Then** the system creates a ForecastSubmission record with status = "Submitted", locks my forecast from further edits, notifies my manager, and displays a confirmation message

**Given** I have already submitted my forecast  
**When** my manager requests a revision  
**Then** the system changes forecast status to "Revision Requested", allows me to edit the amounts, and I can re-submit

---

### US-019 — Review Team Forecast as Manager

**As a** Sales Manager  
**I want** to review my team's submitted forecasts  
**So that** I can approve them and roll them up into my own forecast

**Priority:** P1  
**Story Points:** 5  
**Related FR:** FR-013

**Acceptance Criteria:**

**Given** I navigate to Forecasting → Team Forecasts → Q4 2025  
**When** the page loads  
**Then** I see a table of all my direct reports with columns: Rep Name, Committed, Best Case, Pipeline, Status (Draft, Submitted, Approved)

**Given** one of my reps has submitted a forecast with Committed = $180K  
**When** I click "Review" and examine the breakdown  
**Then** I see a list of opportunities included in the Committed category with: opportunity name, amount, close date, stage, probability

**Given** I agree with the rep's forecast  
**When** I click "Approve"  
**Then** the system changes forecast status to "Approved", locks the rep's forecast, includes it in my rolled-up forecast, and sends a confirmation email to the rep

---

## 5. Activity and Communication Stories

### US-020 — Log a Call

**As a** Sales Rep  
**I want** to log a phone call with a contact  
**So that** there's a record of our conversation and agreed-upon next steps

**Priority:** P0  
**Story Points:** 3  
**Related FR:** FR-014

**Acceptance Criteria:**

**Given** I am viewing a contact detail page  
**When** I click "Log Call", fill in: Subject = "Discovery Call", Duration = 30 minutes, Notes = "Discussed pricing and timeline. Next step: send proposal by Friday", and click "Save"  
**Then** the system creates an Activity record with type = "Call", links it to the contact, adds it to the contact's timeline, and triggers an `ActivityLogged` event

**Given** the call notes mention a next step  
**When** I save the call log  
**Then** the system prompts me: "Create a follow-up task?" with options [Yes, No]; if I click Yes, it opens a task creation form pre-filled with due_date = 3 days from now

---

### US-021 — Create Task with Reminder

**As a** Sales Rep  
**I want** to create a task with a due date and reminder  
**So that** I don't forget to follow up on important action items

**Priority:** P0  
**Story Points:** 3  
**Related FR:** FR-014

**Acceptance Criteria:**

**Given** I navigate to Tasks → New Task  
**When** I fill in: Subject = "Send Proposal to Acme Corp", Related To = Opportunity "Acme Corp - Platform License", Due Date = 2025-08-01, Reminder = 1 day before, Assigned To = Me  
**And** I click "Save"  
**Then** the system creates the task, sets task.status = "Open", and schedules a reminder notification for 2025-07-31

**Given** the task due date is 2025-08-01 and today is 2025-07-31  
**When** the reminder scheduler runs  
**Then** I receive a browser notification and an email: "Task Reminder: Send Proposal to Acme Corp is due tomorrow"

**Given** the task is completed  
**When** I check the "Mark Complete" checkbox on the task detail page  
**Then** the system sets task.status = "Completed", task.completed_at = current timestamp, and removes the task from my "Open Tasks" list

---

### US-022 — Sync Emails from Gmail

**As a** Sales Rep  
**I want** my Gmail emails to sync automatically with the CRM  
**So that** all client communications are logged without manual data entry

**Priority:** P1  
**Story Points:** 8  
**Related FR:** FR-015

**Acceptance Criteria:**

**Given** I navigate to Settings → Integrations → Email → Connect Gmail  
**When** I authorize the CRM to access my Gmail via OAuth  
**Then** the system stores my OAuth token, starts polling my inbox every 5 minutes, and displays "Gmail connected" status

**Given** I send an email from Gmail to jane@example.com (a known contact in the CRM)  
**When** the email sync job runs  
**Then** the system creates an Activity record with type = "Email", subject = email subject, description = email body, linked to Contact "Jane Smith", and displays it on her timeline

**Given** I receive an email reply from jane@example.com  
**When** the email sync job runs  
**Then** the system matches the email thread by subject and In-Reply-To header, groups it with the original email, and marks it as an inbound email

**Given** my Gmail OAuth token expires  
**When** the system attempts to sync emails  
**Then** the sync fails, the system sends me a notification: "Gmail sync failed: Re-authorize your account", and displays a "Re-connect" button in the UI

---

### US-023 — Create Meeting from CRM and Sync to Calendar

**As a** Sales Rep  
**I want** to create a meeting in the CRM and have it automatically added to my Google Calendar  
**So that** I don't have to duplicate data entry across systems

**Priority:** P1  
**Story Points:** 8  
**Related FR:** FR-016

**Acceptance Criteria:**

**Given** I navigate to Calendar → New Meeting  
**When** I fill in: Title = "Product Demo with Acme Corp", Start Time = 2025-08-05 10:00 AM, Duration = 60 minutes, Attendees = ["jane@example.com"], Related To = Opportunity "Acme Corp"  
**And** I click "Save"  
**Then** the system creates a Meeting activity in the CRM, sends a calendar invite to jane@example.com, and adds the meeting to my Google Calendar via the Google Calendar API

**Given** I update the meeting time in the CRM from 10:00 AM to 11:00 AM  
**When** I save the update  
**Then** the system updates the Google Calendar event, sends an updated calendar invite to all attendees, and logs the change in the activity timeline

**Given** I cancel the meeting in the CRM  
**When** I click "Cancel Meeting" and confirm  
**Then** the system marks the activity as cancelled, sends a cancellation notice to attendees, and removes the event from my Google Calendar

---

## 6. Campaign and Marketing Stories

### US-024 — Create Email Campaign

**As a** Marketing Manager  
**I want** to create an email campaign targeting a segment of contacts  
**So that** I can nurture leads and drive engagement

**Priority:** P1  
**Story Points:** 8  
**Related FR:** FR-017

**Acceptance Criteria:**

**Given** I navigate to Campaigns → New Campaign  
**When** I enter: Campaign Name = "Q3 Product Launch", Segment = "Enterprise Prospects", Template = "Product Announcement", Subject = "Introducing Our New Platform", Scheduled Send = 2025-08-15 09:00 AM  
**And** I click "Save"  
**Then** the system creates the campaign with status = "Scheduled", validates that the segment has > 0 contacts, and displays a preview of the email

**Given** the scheduled send time is 2025-08-15 09:00 AM  
**When** the campaign scheduler runs at that time  
**Then** the system changes campaign status to "Sending", creates a CampaignSend record for each contact in the segment, and begins sending emails in batches of 1000 per minute

**Given** a contact in the segment has email_opt_out = true  
**When** the campaign send job processes that contact  
**Then** the system skips sending the email to that contact and logs a "Skipped - Opted Out" status in the CampaignSend record

---

### US-025 — Preview Email with Merge Fields

**As a** Marketing Manager  
**I want** to preview how merge fields will render in my campaign emails  
**So that** I can ensure personalization is correct before sending

**Priority:** P1  
**Story Points:** 3  
**Related FR:** FR-017

**Acceptance Criteria:**

**Given** I am editing an email template with merge fields: "Hi {{first_name}}, we noticed you work at {{company}}..."  
**When** I click "Preview"  
**Then** the system displays the email with sample data: "Hi John, we noticed you work at Acme Corp..."

**Given** I select a specific contact from the segment for preview  
**When** I click "Preview with Contact: Jane Smith"  
**Then** the system renders the email with Jane Smith's actual data: "Hi Jane, we noticed you work at Global Tech Inc..."

---

### US-026 — Build Dynamic Segment with Filters

**As a** Marketing Manager  
**I want** to create a dynamic segment of contacts based on filter criteria  
**So that** my campaign always targets the most up-to-date audience

**Priority:** P1  
**Story Points:** 5  
**Related FR:** FR-018

**Acceptance Criteria:**

**Given** I navigate to Segments → New Segment  
**When** I select: Segment Type = "Dynamic", Filters = "Contact.title CONTAINS 'VP' AND Contact.account.industry = 'Technology' AND Contact.lead_score >= 70"  
**And** I click "Preview"  
**Then** the system displays a count of matching contacts (e.g., "125 contacts match this segment") and shows the first 10 contacts

**Given** the segment is saved as "High-Value Tech VPs"  
**When** I use this segment in a campaign 7 days later  
**Then** the system re-evaluates the filters and includes any newly created contacts that now match the criteria

**Given** I want to create a static segment (snapshot)  
**When** I select Segment Type = "Static" and apply the same filters  
**Then** the system saves a snapshot of the current matching contact IDs and does NOT re-evaluate on future use

---

### US-027 — Track Campaign Email Metrics

**As a** Marketing Manager  
**I want** to see open rates, click rates, and bounce rates for my campaigns  
**So that** I can measure campaign effectiveness and optimize future sends

**Priority:** P1  
**Story Points:** 5  
**Related FR:** FR-019

**Acceptance Criteria:**

**Given** I have sent a campaign to 1,000 contacts  
**When** I navigate to Campaigns → "Q3 Product Launch" → Metrics  
**Then** I see a dashboard with: Sent (1,000), Delivered (980), Bounced (20), Opened (350, 35.7% open rate), Clicked (75, 7.7% click rate), Unsubscribed (5)

**Given** a contact opens the email  
**When** the email client loads the embedded tracking pixel  
**Then** the system logs an "Email Opened" event, increments the campaign's open count, and updates the CampaignSend record with opened_at timestamp

**Given** a contact clicks a link in the email  
**When** the link redirects through the CRM's tracking URL (e.g., crm.example.com/r/abc123)  
**Then** the system logs an "Email Clicked" event, increments the campaign's click count, records the clicked URL, and redirects the contact to the destination URL

**Given** a contact clicks the "Unsubscribe" link  
**When** the unsubscribe page loads  
**Then** the system sets contact.email_opt_out = true, logs an "Unsubscribed" event, and displays a confirmation message: "You have been unsubscribed from future emails"

---

## 7. Forecasting and Territory Stories

### US-028 — Create Territory with Assignment Rules

**As a** RevOps Analyst  
**I want** to create a territory and define assignment rules  
**So that** accounts are automatically assigned to the correct sales rep

**Priority:** P1  
**Story Points:** 8  
**Related FR:** FR-020

**Acceptance Criteria:**

**Given** I navigate to Settings → Territories → New Territory  
**When** I enter: Territory Name = "West Coast Enterprise", Owner = "John Smith", Assignment Rules = "Account.billing_address.state IN ['CA', 'WA', 'OR'] AND Account.employee_count > 1000"  
**And** I click "Save"  
**Then** the system creates the territory and triggers a background job to re-evaluate all existing accounts against the new rule

**Given** a new account is created with billing_address.state = "CA" and employee_count = 1500  
**When** the account is saved  
**Then** the system auto-assigns account.territory_id = "West Coast Enterprise" and account.owner_id = John Smith's user ID

**Given** an account's employee count is updated from 500 to 1200  
**When** the update is saved  
**Then** the territory assignment rules are re-evaluated, the account is reassigned to "West Coast Enterprise", and the previous owner receives a notification

---

### US-029 — Rebalance Territories Annually

**As a** RevOps Analyst  
**I want** to preview and execute a territory rebalancing plan  
**So that** I can reassign accounts fairly at the start of each fiscal year

**Priority:** P1  
**Story Points:** 8  
**Related FR:** FR-020

**Acceptance Criteria:**

**Given** I navigate to Settings → Territories → Rebalance  
**When** I update assignment rules and click "Preview Rebalance"  
**Then** the system runs a dry-run simulation and displays: "120 accounts will be reassigned: 45 from Territory A to Territory B, 75 from Territory C to Territory D"

**Given** the preview looks correct  
**When** I click "Execute Rebalance" and set effective_date = 2026-01-01  
**Then** the system creates TerritoryReassignment records for each affected account, schedules the reassignments to take effect on 2026-01-01, and sends email notifications to affected reps

**Given** the effective date has arrived  
**When** the rebalancing job runs  
**Then** the system updates account.territory_id and account.owner_id for all affected accounts, logs the changes in the audit trail, and notifies reps of their new account assignments

---

### US-030 — View Forecast Rollup as VP

**As a** VP of Sales  
**I want** to view a rolled-up forecast across all teams  
**So that** I can understand total pipeline and commit for the quarter

**Priority:** P1  
**Story Points:** 5  
**Related FR:** FR-021

**Acceptance Criteria:**

**Given** I navigate to Forecasting → Rollup View → Q4 2025  
**When** the page loads  
**Then** I see a hierarchical view: VP Total → Director 1 Total, Director 2 Total → Manager 1 Total, Manager 2 Total, ... → Rep 1, Rep 2, ...

**Given** the rollup shows: Total Committed = $5M, Total Best Case = $8M, Total Pipeline = $12M  
**When** one of my managers approves a rep's revised forecast with Committed increased by $100K  
**Then** the rollup updates in real-time to show: Total Committed = $5.1M

**Given** I want to see variance vs. quota  
**When** I toggle "Show Quota Comparison"  
**Then** the system displays an additional column: Quota ($6M), Committed ($5M), Variance (-$1M, -16.7%)

---

## 8. Configuration and Administration Stories

### US-031 — Define Custom Field on Contact

**As a** CRM Administrator  
**I want** to create a custom field on the Contact entity  
**So that** we can track industry-specific data unique to our business

**Priority:** P1  
**Story Points:** 5  
**Related FR:** FR-022

**Acceptance Criteria:**

**Given** I navigate to Settings → Custom Fields → Contact → New Field  
**When** I enter: Field Label = "Customer Segment", Field Type = "Picklist", Options = ["Enterprise", "Mid-Market", "SMB"], Required = Yes  
**And** I click "Save"  
**Then** the system creates the custom field with API name = "customer_segment_c", adds it to the Contact create/edit forms, and displays it on the Contact detail page

**Given** the custom field is created  
**When** a user creates a new Contact  
**Then** the "Customer Segment" dropdown appears on the form and is required before saving

**Given** I want to delete the custom field  
**When** I navigate to Settings → Custom Fields → Contact → "Customer Segment" → Delete  
**Then** the system prompts: "This field is used on 1,500 Contact records. Deleting it will permanently remove all data. Are you sure?" and requires confirmation

---

### US-032 — Create Lookup Custom Field

**As a** CRM Administrator  
**I want** to create a custom field that references another entity  
**So that** users can link related records (e.g., Contact → Contract)

**Priority:** P1  
**Story Points:** 8  
**Related FR:** FR-022

**Acceptance Criteria:**

**Given** I navigate to Settings → Custom Fields → Opportunity → New Field  
**When** I enter: Field Label = "Related Contract", Field Type = "Lookup", Related Entity = "Contract"  
**And** I click "Save"  
**Then** the system creates the custom field, and when users edit an Opportunity, they see a "Related Contract" field with typeahead search to select a Contract record

**Given** I select a Contract in the lookup field  
**When** I save the Opportunity  
**Then** the system stores the foreign key (contract_id) and displays the linked Contract name as a clickable link on the Opportunity detail page

---

### US-033 — Review Duplicate Contact Queue

**As a** RevOps Analyst  
**I want** to review potential duplicate contacts flagged by the system  
**So that** I can merge them and maintain data quality

**Priority:** P1  
**Story Points:** 5  
**Related FR:** FR-023

**Acceptance Criteria:**

**Given** the duplicate detection engine has flagged 50 potential duplicate pairs  
**When** I navigate to Data Quality → Duplicate Contacts  
**Then** I see a list of duplicate pairs with: Contact A name, Contact A email, Contact B name, Contact B email, Confidence Score (50-100%), Actions [Merge, Not a Duplicate]

**Given** I click "Merge" on a duplicate pair  
**When** the merge UI loads  
**Then** I see a side-by-side comparison of all fields (name, email, phone, title, account, custom fields) with radio buttons to select the winning value for each field

**Given** I select the winning values and click "Confirm Merge"  
**When** the merge executes  
**Then** the system creates a MergeHistory record, soft-deletes the losing Contact, updates all related activities and deals to point to the winning Contact, and removes the pair from the duplicate queue

---

### US-034 — Auto-Merge High-Confidence Duplicates

**As a** RevOps Analyst  
**I want** to configure automatic merging of high-confidence duplicates  
**So that** obvious duplicates are handled without manual review

**Priority:** P2  
**Story Points:** 8  
**Related FR:** FR-023

**Acceptance Criteria:**

**Given** I navigate to Settings → Data Quality → Duplicate Rules  
**When** I enable "Auto-merge duplicates with confidence >= 95%"  
**And** I save the setting  
**Then** the duplicate detection engine automatically merges any future duplicate pairs with confidence >= 95% and sends me a daily summary email

**Given** two contacts are created with identical email addresses (100% confidence duplicate)  
**When** the duplicate detection job runs  
**Then** the system automatically merges the newer contact into the older contact, retaining all activities from both, and logs the merge in the MergeHistory table

---

## 9. Integration and API Stories

### US-035 — Obtain OAuth Access Token

**As a** System Integrator  
**I want** to authenticate with the CRM API using OAuth 2.0  
**So that** I can securely access CRM data on behalf of a user

**Priority:** P0  
**Story Points:** 5  
**Related FR:** FR-024

**Acceptance Criteria:**

**Given** I have registered an OAuth application in the CRM and obtained a client_id and client_secret  
**When** I redirect the user to the CRM's OAuth authorization URL with my client_id and requested scopes  
**Then** the user sees a consent screen: "Application X is requesting access to your CRM data: Read Contacts, Write Leads. Allow or Deny?"

**Given** the user clicks "Allow"  
**When** the OAuth flow completes  
**Then** the CRM redirects back to my application's redirect_uri with an authorization code

**Given** I exchange the authorization code for an access token  
**When** I POST to `/api/v1/oauth/token` with code, client_id, client_secret, and grant_type = "authorization_code"  
**Then** the system responds with HTTP 200 and JSON: `{"access_token": "...", "refresh_token": "...", "expires_in": 3600}`

**Given** my access token has expired  
**When** I POST to `/api/v1/oauth/token` with refresh_token and grant_type = "refresh_token"  
**Then** the system issues a new access token and a new refresh token, invalidates the old refresh token, and responds with HTTP 200

---

### US-036 — Subscribe to Webhook Events

**As a** System Integrator  
**I want** to receive real-time notifications when CRM events occur  
**So that** I can trigger workflows in external systems

**Priority:** P1  
**Story Points:** 8  
**Related FR:** FR-025

**Acceptance Criteria:**

**Given** I navigate to Settings → Webhooks → New Webhook  
**When** I enter: URL = "https://myapp.example.com/webhooks/crm", Events = ["LeadCaptured", "DealStageChanged"], Secret = "my-secret-key"  
**And** I click "Save"  
**Then** the system creates the webhook subscription and sends a test payload to my URL to verify connectivity

**Given** a new lead is captured in the CRM  
**When** the `LeadCaptured` event is emitted  
**Then** the system sends an HTTP POST to my webhook URL with JSON payload: `{"event": "LeadCaptured", "lead_id": "...", "email": "...", "timestamp": "..."}` and an `X-CRM-Signature` header with HMAC-SHA256 signature

**Given** my webhook URL is temporarily unavailable (HTTP 503)  
**When** the webhook delivery fails  
**Then** the system retries 3 times with exponential backoff (1s, 5s, 25s), logs the failure, and marks the webhook as "Failed" in the UI

**Given** I want to manually retry a failed webhook  
**When** I navigate to Webhooks → "My Webhook" → Failed Deliveries → "Retry"  
**Then** the system re-sends the webhook payload immediately

---

## 10. Data Quality and Compliance Stories

### US-037 — Import Contacts with Field Mapping

**As a** RevOps Analyst  
**I want** to import a CSV of contacts with custom field mapping  
**So that** I can onboard data from external systems

**Priority:** P1  
**Story Points:** 8  
**Related FR:** FR-026

**Acceptance Criteria:**

**Given** I have a CSV file with columns: "Full Name", "Email Address", "Company Name", "Job Title"  
**When** I navigate to Contacts → Import, upload the file, and map: "Full Name" → first_name + last_name, "Email Address" → email, "Company Name" → account.name, "Job Title" → title  
**Then** the system displays a preview showing: "John Doe" split into first_name = "John", last_name = "Doe", email = "john@example.com", account lookup by name = "Acme Corp", title = "VP of Sales"

**Given** the CSV has 5,000 rows and the validation passes  
**When** I click "Import"  
**Then** the system creates a background job, imports the contacts, and emails me a summary: "Import completed: 4,950 contacts created, 50 errors. Download error report."

---

### US-038 — Assign Role-Based Permissions

**As a** CRM Administrator  
**I want** to assign users to roles with specific permissions  
**So that** I can control who can view, edit, or delete CRM data

**Priority:** P0  
**Story Points:** 5  
**Related FR:** FR-027

**Acceptance Criteria:**

**Given** I navigate to Settings → Users → "John Smith" → Edit  
**When** I assign Role = "Sales Rep"  
**And** the "Sales Rep" role has permissions: Leads (Create, Read, Update), Contacts (Read Own, Update Own), Deals (Read Own, Update Own)  
**Then** John Smith can create leads, read and update his own contacts and deals, but cannot view other reps' data

**Given** I assign Role = "Sales Manager" to Jane Doe  
**When** the "Sales Manager" role has permissions: Contacts (Read Team, Update Team), Deals (Read Team, Update Team)  
**Then** Jane Doe can view and edit all contacts and deals owned by her team members

---

### US-039 — View Audit Log for Record Changes

**As a** CRM Administrator  
**I want** to view the audit log for a specific record  
**So that** I can see who made changes and when

**Priority:** P0  
**Story Points:** 3  
**Related FR:** FR-028

**Acceptance Criteria:**

**Given** I am viewing a Contact detail page  
**When** I click "View Audit Log"  
**Then** I see a table of all changes: Date/Time, User, Field Changed, Old Value, New Value

**Given** the contact's email was changed from "old@example.com" to "new@example.com" by John Smith on 2025-07-10  
**When** I view the audit log  
**Then** I see an entry: "2025-07-10 14:23:45 | John Smith | email | old@example.com | new@example.com"

---

### US-040 — Export Audit Log for Compliance

**As a** CRM Administrator  
**I want** to export the audit log for a date range  
**So that** I can provide it to auditors for compliance reviews

**Priority:** P0  
**Story Points:** 3  
**Related FR:** FR-028

**Acceptance Criteria:**

**Given** I navigate to Settings → Audit Log  
**When** I select date range = 2025-01-01 to 2025-12-31, entity type = "All", and click "Export"  
**Then** the system creates a background job, generates a CSV file with all audit log entries, and emails me a download link

**Given** the exported CSV is opened in Excel  
**When** I review the columns  
**Then** I see: Timestamp, User ID, User Name, Entity Type, Entity ID, Event Type, IP Address, Old Values (JSON), New Values (JSON)

---

### US-041 — Process GDPR Data Erasure Request

**As a** CRM Administrator  
**I want** to permanently erase a contact's personal data upon request  
**So that** we comply with GDPR right to be forgotten

**Priority:** P0  
**Story Points:** 8  
**Related FR:** FR-029

**Acceptance Criteria:**

**Given** I receive a GDPR erasure request for contact email = "jane@example.com"  
**When** I navigate to Contacts → Search "jane@example.com" → Actions → Request Erasure  
**Then** the system displays a confirmation dialog: "This will permanently delete all personal data for Jane Smith. This action cannot be undone. Continue?"

**Given** I confirm the erasure  
**When** the erasure job runs  
**Then** the system deletes the Contact record, deletes related Activities, anonymizes audit log entries (replaces name/email with "REDACTED"), retains Deal records but removes contact association, and sends a confirmation email to the requester

**Given** the contact has open deals worth $500K  
**When** I attempt to erase the contact  
**Then** the system warns: "This contact has 2 open deals totaling $500K. Proceed with erasure?" and requires explicit confirmation

---

### US-042 — Export CRM Data for Portability

**As a** CRM Administrator  
**I want** to export all CRM data for our tenant  
**So that** we can migrate to another system or comply with GDPR data portability

**Priority:** P1  
**Story Points:** 8  
**Related FR:** FR-030

**Acceptance Criteria:**

**Given** I navigate to Settings → Data Export → Full Export  
**When** I select entities = ["Leads", "Contacts", "Accounts", "Deals", "Activities"], format = "JSON", and click "Export"  
**Then** the system creates a background job, exports all data with relationships intact, and emails me a download link (expires in 7 days)

**Given** the export file is downloaded  
**When** I open the JSON file  
**Then** I see nested objects: each Contact includes embedded activities array, each Deal includes related account and contact objects

---

## 11. Story Mapping

### Story Mapping to Requirements

| User Story ID | Requirement ID | Priority | Story Points |
|---|---|---|---|
| US-001 | FR-001 | P0 | 5 |
| US-002 | FR-001 | P1 | 3 |
| US-003 | FR-002 | P0 | 3 |
| US-004 | FR-003 | P1 | 8 |
| US-005 | FR-004 | P1 | 2 |
| US-006 | FR-004 | P1 | 8 |
| US-007 | FR-005 | P0 | 8 |
| US-008 | FR-006 | P0 | 8 |
| US-009 | FR-006 | P1 | 2 |
| US-010 | FR-007 | P0 | 3 |
| US-011 | FR-007 | P0 | 2 |
| US-012 | FR-008 | P0 | 3 |
| US-013 | FR-009 | P1 | 5 |
| US-014 | FR-010 | P0 | 5 |
| US-015 | FR-011 | P0 | 3 |
| US-016 | FR-011 | P0 | 2 |
| US-017 | FR-012 | P0 | 5 |
| US-018 | FR-013 | P1 | 5 |
| US-019 | FR-013 | P1 | 5 |
| US-020 | FR-014 | P0 | 3 |
| US-021 | FR-014 | P0 | 3 |
| US-022 | FR-015 | P1 | 8 |
| US-023 | FR-016 | P1 | 8 |
| US-024 | FR-017 | P1 | 8 |
| US-025 | FR-017 | P1 | 3 |
| US-026 | FR-018 | P1 | 5 |
| US-027 | FR-019 | P1 | 5 |
| US-028 | FR-020 | P1 | 8 |
| US-029 | FR-020 | P1 | 8 |
| US-030 | FR-021 | P1 | 5 |
| US-031 | FR-022 | P1 | 5 |
| US-032 | FR-022 | P1 | 8 |
| US-033 | FR-023 | P1 | 5 |
| US-034 | FR-023 | P2 | 8 |
| US-035 | FR-024 | P0 | 5 |
| US-036 | FR-025 | P1 | 8 |
| US-037 | FR-026 | P1 | 8 |
| US-038 | FR-027 | P0 | 5 |
| US-039 | FR-028 | P0 | 3 |
| US-040 | FR-028 | P0 | 3 |
| US-041 | FR-029 | P0 | 8 |
| US-042 | FR-030 | P1 | 8 |

**Total User Stories:** 42  
**Total Story Points:** 233

### Epic Summary

| Epic | User Stories | Total Story Points |
|---|---|---|
| Lead Management | US-001 to US-009 | 49 |
| Contact and Account Management | US-010 to US-013 | 13 |
| Opportunity and Pipeline | US-014 to US-019 | 25 |
| Activity and Communication | US-020 to US-023 | 22 |
| Campaign and Marketing | US-024 to US-027 | 21 |
| Forecasting and Territory | US-028 to US-030 | 21 |
| Configuration and Administration | US-031 to US-034 | 26 |
| Integration and API | US-035 to US-036 | 13 |
| Data Quality and Compliance | US-037 to US-042 | 43 |

---

*This user story document is maintained by the Product Management team in collaboration with Sales, Marketing, and RevOps stakeholders. All stories are validated against real user workflows and are sized for implementation in 2-week sprints.*
