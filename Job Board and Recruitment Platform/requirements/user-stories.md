# User Stories — Job Board and Recruitment Platform

**Version:** 1.0  
**Status:** Approved  
**Owner:** Product Management — Talent Acquisition Platform  
**Last Reviewed:** 2025-01

---

## Roles

| Role | Description |
|---|---|
| **Recruiter** | Internal talent acquisition professional managing requisitions end-to-end |
| **Hiring Manager** | Department lead who opens requisitions and evaluates candidates for their team |
| **Candidate** | External job seeker applying for open positions |
| **HR Admin** | HR operations professional managing platform configuration and compliance |
| **Executive** | VP Talent / CHRO consuming analytics without performing day-to-day recruiting |

---

## Job Posting and Requisition

### US-01: Create a New Job Requisition
**Role:** Recruiter  
**Story:** As a Recruiter, I want to create a new job requisition with structured fields so that all relevant information about the role is captured consistently and is ready for the approval workflow.  
**Acceptance Criteria:**
- Given I am logged in as a Recruiter, when I navigate to "Create Job" and complete all required fields (title, department, hiring manager, employment type, location, number of openings, description), then the draft requisition is saved and assigned a unique requisition ID.
- Given I am filling out the requisition form, when I stop editing for more than 30 seconds, then the draft is auto-saved and a "Draft saved" indicator appears without disrupting my input.
- Given I have completed the form, when I click "Submit for Approval", then the first approver in the chain receives an email notification and an in-platform notification, and the requisition status changes to "Pending Approval".
- Given I attempt to submit without completing a required field, when I click "Submit for Approval", then the form highlights the missing fields with inline error messages and does not submit.

---

### US-02: Approve or Reject a Job Requisition
**Role:** Hiring Manager  
**Story:** As a Hiring Manager, I want to review and approve or reject requisitions submitted for my team so that only accurate and budget-approved roles get posted publicly.  
**Acceptance Criteria:**
- Given a requisition requires my approval, when I receive the notification, then I can view the full requisition detail (title, description, salary range, location, start date) and the approval chain history before taking action.
- Given I review the requisition, when I click "Approve", then the requisition advances to the next approver (or to "Active" if I am the final approver), and the Recruiter receives a notification.
- Given I find an error in the requisition, when I click "Reject" and enter a mandatory comment explaining the issue, then the requisition is returned to the Recruiter with "Rejected" status and my comment is visible on the requisition timeline.
- Given a requisition is pending my approval, when 48 hours pass without action, then the system sends me a reminder notification escalating urgency.

---

### US-03: Configure Pay Transparency Display
**Role:** HR Admin  
**Story:** As an HR Admin, I want to configure which job posting locations require mandatory salary range disclosure so that the platform automatically complies with state and national pay transparency laws without requiring recruiters to remember jurisdiction-specific rules.  
**Acceptance Criteria:**
- Given I open the "Pay Transparency" configuration page, when I select a jurisdiction (e.g., California, New York, Colorado), then I can set whether the salary range is "Always Display", "Never Display", or "Recruiter Decides".
- Given a job is posted in a mandatory-disclosure jurisdiction, when the recruiter attempts to hide the salary range, then the system prevents the change, displays a compliance warning message, and does not allow publishing without a salary range.
- Given a job is posted with a valid salary range in a mandatory-disclosure state, when the posting goes live, then the salary range is visible to candidates on the job listing and on all syndicated board postings.

---

### US-04: Distribute Job to External Boards
**Role:** Recruiter  
**Story:** As a Recruiter, I want the platform to automatically post approved jobs to LinkedIn, Indeed, and Glassdoor so that I don't need to manually re-post on each board and can reach a broader candidate audience immediately.  
**Acceptance Criteria:**
- Given a job posting is approved and activated, when the platform triggers syndication, then all boards enabled for the tenant receive the posting within 5 minutes and the requisition detail page shows "Live" status per board.
- Given a job board returns an API error during syndication, when the syndication fails, then I receive an in-platform notification and email with the board name and error description, and I can manually retry syndication from the requisition detail page.
- Given I close a job posting in the platform, when the closure is processed, then the platform sends a deletion or expiry request to all external boards where the job is live and confirms each board's status updates to "Removed".
- Given I want to distribute to a specific board only, when I deselect boards before activating, then only the selected boards receive the posting and the others remain inactive for that requisition.

---

### US-05: Clone an Existing Job Posting
**Role:** Recruiter  
**Story:** As a Recruiter, I want to clone an existing job posting so that I can quickly create a similar requisition for a recurring role without re-entering all the details from scratch.  
**Acceptance Criteria:**
- Given I open any existing requisition (in any status), when I click "Clone", then a new draft is created with the same job title, description, screening questions, salary range, and pipeline template, with today's date and a "Draft" status.
- Given a cloned draft is created, when I open it, then no candidate applications, evaluation data, or historical activity from the original are copied over.
- Given I clone a closed job, when the clone draft is created, then the system notifies me that I should review the job description and compensation details for accuracy before re-submitting for approval.

---

### US-06: Add Screening Questions to a Job Posting
**Role:** Recruiter  
**Story:** As a Recruiter, I want to attach custom screening questions to a job posting so that I can quickly filter out candidates who don't meet the minimum requirements without manually reviewing every resume.  
**Acceptance Criteria:**
- Given I am editing a job posting, when I add a Yes/No question and mark it as a "Knockout" question with the required answer set to "Yes", then any candidate who answers "No" has their application automatically labelled "Disqualified" and routed to the Rejected stage.
- Given I add a multiple-choice question, when I configure it with 4 answer options, then candidates see a dropdown with those options and cannot submit without selecting one if the question is required.
- Given a candidate's application is auto-rejected by a knockout question, when I view the application in the pipeline, then the rejection label indicates "Knockout: [Question Text]" so I understand why it was auto-rejected.

---

## Candidate Applications

### US-07: Apply for a Job
**Role:** Candidate  
**Story:** As a Candidate, I want to apply for a job in a simple, mobile-friendly form so that I can submit my application quickly without encountering technical barriers.  
**Acceptance Criteria:**
- Given I visit a job listing page, when I click "Apply Now", then the application form loads within 2 seconds and is fully functional on a mobile browser.
- Given I complete and submit the application form, when the submission is successful, then I receive a confirmation email within 2 minutes containing my application reference number, the job title, and a link to the candidate portal.
- Given I attempt to submit the form without uploading a resume, when I click "Submit Application", then the form shows an inline error on the resume upload field and does not submit.
- Given I have already submitted an application for the same job, when I attempt to apply again with the same email address, then the system displays "You've already applied to this position" and links me to my application status in the candidate portal.

---

### US-08: Upload and Update My Resume
**Role:** Candidate  
**Story:** As a Candidate, I want to upload my resume and have it automatically parsed so that I don't need to manually fill in my work history and skills in the application form.  
**Acceptance Criteria:**
- Given I upload a PDF resume, when parsing completes within 30 seconds, then my work history, education, and skills fields are pre-populated in the application form for me to review and confirm.
- Given parsed data contains an error (e.g., wrong job title extracted), when I edit the pre-populated field and save, then the corrected value is stored and the original parsed value is preserved for audit.
- Given my resume parsing fails, when I submit the application anyway, then my application is still accepted with the original file attached and is flagged for manual review by the recruiter.
- Given I am logged into the candidate portal, when I upload a new resume version, then my updated resume is used for all future applications while existing applications retain the resume version uploaded at the time of application.

---

### US-09: Track My Application Status
**Role:** Candidate  
**Story:** As a Candidate, I want to view the current status of all my applications in one place so that I know where I stand without needing to email the recruiter for updates.  
**Acceptance Criteria:**
- Given I log into the candidate portal, when I view "My Applications", then I see a list of all positions I've applied to with status labels (Applied, Under Review, Interview Scheduled, Offer Extended, Rejected, Withdrawn) and the date of the last update.
- Given my application moves to a new stage, when the stage change is processed, then I receive an email notification within 5 minutes informing me of the update and the portal status is updated accordingly.
- Given my application is rejected, when I view the portal, then I see "Application Unsuccessful" with a polite generic message; I do not see internal rejection reasons or recruiter notes.

---

### US-10: Perform a GDPR Data Erasure Request
**Role:** Candidate  
**Story:** As a Candidate, I want to request the deletion of all my personal data so that I can exercise my right to erasure under GDPR if I no longer want the company to hold my information.  
**Acceptance Criteria:**
- Given I am logged into the candidate portal, when I navigate to "Privacy Settings" and click "Request Data Deletion", then I am shown a confirmation explaining what data will be deleted and what anonymized data will be retained for compliance.
- Given I confirm the deletion request, when I click "Confirm Delete", then the system logs the request, sends me an acknowledgement email, and completes the deletion within 30 days.
- Given the deletion is processed, when I attempt to log in with my previous email address, then the account is not found and I receive no error message that reveals whether the account existed.
- Given my data is erased, when an HR Admin runs aggregate reporting, then my anonymized data (e.g., application outcome without name) still contributes to funnel statistics without any PII.

---

### US-11: Request a GDPR Data Export
**Role:** Candidate  
**Story:** As a Candidate, I want to export a copy of all the personal data the platform holds about me so that I can verify what information has been collected and exercise my right to data portability.  
**Acceptance Criteria:**
- Given I am logged into the candidate portal, when I navigate to "Privacy Settings" and click "Export My Data", then the system acknowledges the request and tells me the export will be ready within 72 hours.
- Given the export is ready, when I receive the email notification, then I can download a JSON file containing my profile, applications, communications received, and consent records.
- Given the exported file, when I open it, then no other candidate's data is present and all my PII fields are correctly included.

---

## ATS Pipeline Management

### US-12: Move Candidates Between Pipeline Stages
**Role:** Recruiter  
**Story:** As a Recruiter, I want to drag and drop candidate cards between pipeline stages on a Kanban board so that I can quickly update the pipeline status without navigating away from the overview.  
**Acceptance Criteria:**
- Given I am viewing the Kanban pipeline for a requisition, when I drag a candidate card from "Applied" to "Phone Screen", then the candidate's stage is updated immediately, an activity log entry is created, and a stage-change notification email is sent to the candidate if that notification type is enabled.
- Given another recruiter is viewing the same pipeline simultaneously, when I move a candidate, then their board updates within 5 seconds without requiring a manual refresh.
- Given I drag a candidate to the "Rejected" stage, when the card is dropped, then a modal prompts me to select a rejection reason before confirming the move.

---

### US-13: Bulk Advance Screened Candidates
**Role:** Recruiter  
**Story:** As a Recruiter, I want to select multiple candidates and advance them to the next stage in bulk so that I can efficiently process large volumes of applications after an initial screening session.  
**Acceptance Criteria:**
- Given I switch to the list view of the pipeline, when I select 15 candidate checkboxes and click "Bulk Advance", then a preview dialog shows all 15 names and the target stage before I confirm.
- Given I confirm the bulk advance, when the action is processed, then all 15 candidates are moved to the specified stage and each receives a stage notification email within 5 minutes.
- Given one of the 15 candidates is already in the target stage, when the bulk action runs, then that candidate is skipped without error and I see a summary: "14 advanced, 1 skipped (already in stage)".

---

### US-14: Apply Tags to Candidates
**Role:** Recruiter  
**Story:** As a Recruiter, I want to tag candidates with descriptive labels so that I can quickly filter and identify specific subsets of candidates across the pipeline.  
**Acceptance Criteria:**
- Given I open a candidate card, when I type a tag name in the tag input field and press Enter, then the tag is applied to the candidate and is visible as a colored chip on the candidate card.
- Given a tag exists in the company's tag library, when I start typing its name, then an autocomplete dropdown shows matching tags so I select an existing one rather than creating a duplicate.
- Given I want to filter the pipeline by a tag, when I click a tag chip in the filter bar, then the Kanban board displays only candidates with that tag across all stages.

---

### US-15: Configure a Custom Pipeline Template
**Role:** HR Admin  
**Story:** As an HR Admin, I want to create custom pipeline templates for different hiring tracks so that each department can use a workflow that reflects their unique evaluation process.  
**Acceptance Criteria:**
- Given I navigate to "Pipeline Templates" in admin settings, when I create a new template with stages: Applied → Recruiter Screen → Technical Interview → Cultural Fit Interview → Offer → Hired, then I can save it and assign it as the default for the Engineering department.
- Given a pipeline template is in use on an active requisition, when I attempt to delete a stage that has candidates in it, then the system prevents the deletion and displays a message explaining how many candidates are in that stage.
- Given I set a stage SLA threshold (e.g., "Recruiter Screen" must be completed within 3 days), when a candidate spends more than 3 days in that stage, then the recruiter receives an SLA warning notification and the card is highlighted in the Kanban view.

---

### US-16: Configure Automatic Stage Transition Rules
**Role:** HR Admin  
**Story:** As an HR Admin, I want to configure automation rules that move candidates automatically based on criteria so that recruiters spend less time on administrative triage and more time on high-value interactions.  
**Acceptance Criteria:**
- Given I configure a rule: "If AI resume match score ≥ 80, advance from Applied to Recruiter Screen", when a candidate with a score of 85 applies, then they are automatically moved to Recruiter Screen within 2 minutes and the activity log notes "Auto-advanced by rule: Score ≥ 80".
- Given I configure a knockout question, when a candidate triggers it, then they are auto-rejected within 2 minutes of submission, the activity log notes the automation rule, and the recruiter can override the rejection if needed.
- Given a recruiter overrides an auto-rejected candidate, when they click "Undo Rejection" and select a different stage, then the override is logged with the recruiter's name and the candidate is moved to the selected stage.

---

### US-17: Search the Candidate Database with Boolean Logic
**Role:** Recruiter  
**Story:** As a Recruiter, I want to search the full candidate database with Boolean queries so that I can identify past applicants and sourced candidates who match a new role I'm trying to fill.  
**Acceptance Criteria:**
- Given I enter the query `("software engineer" OR "backend developer") AND ("Node.js" OR "Python") AND NOT "frontend"` in the candidate search bar, when I execute the search, then results are returned within 1 second showing candidates whose resumes or profiles match the query.
- Given the search returns results, when I view the result list, then each result shows the candidate's name, last activity date, current application status, and a resume snippet with my query terms highlighted.
- Given I want to narrow results, when I apply a filter for "Location: within 50 miles of San Francisco", then the result list updates immediately to show only candidates within the specified radius.

---

## Interview Management

### US-18: Schedule an Interview with Calendar Availability Check
**Role:** Recruiter  
**Story:** As a Recruiter, I want to check interviewer availability from their Google Calendar and propose time slots to the candidate so that scheduling doesn't require multiple back-and-forth emails.  
**Acceptance Criteria:**
- Given I initiate "Schedule Interview" for a candidate, when I select the interviewer and a date range, then the system fetches the interviewer's free/busy data from Google Calendar and displays available 1-hour slots within the range.
- Given I select 3 available slots and click "Send to Candidate", when the candidate receives the email, then they see the 3 proposed times in their local timezone with a "Select Your Time" link.
- Given the candidate clicks the scheduling link, when they select a slot and confirm, then a calendar invite is automatically sent to both the candidate and the interviewer, including the video conferencing link.
- Given the candidate's preferred slot is no longer available at the time they click (e.g., interviewer booked another meeting), when they attempt to confirm, then the system displays an error and prompts them to choose another slot.

---

### US-19: Complete an Interview Scorecard
**Role:** Hiring Manager  
**Story:** As a Hiring Manager, I want to submit structured interview feedback through a scorecard form immediately after the interview so that my evaluation is captured while the conversation is fresh and contributes to a fair, data-driven hiring decision.  
**Acceptance Criteria:**
- Given I completed an interview and a scorecard is assigned to the round, when I log into the platform, then an "Interview Feedback Due" prompt appears on my dashboard with a direct link to the scorecard for that candidate.
- Given I open the scorecard, when I submit ratings for each competency dimension and select an overall recommendation (Strong Yes / Yes / No / Strong No), then the feedback is locked for editing after 7 days and is visible to other interviewers only after they have submitted their own scorecard.
- Given I fail to submit the scorecard within 24 hours of the interview, when 24 hours pass, then I receive an email reminder. If I fail to submit within 48 hours, the recruiter is notified.
- Given the scorecard is submitted, when the recruiter views the candidate's profile, then they can see all submitted scorecards in an aggregated view showing ratings per competency and each interviewer's overall recommendation.

---

### US-20: Generate a Video Conferencing Link for an Interview
**Role:** Recruiter  
**Story:** As a Recruiter, I want the platform to automatically generate a unique Zoom meeting link for each scheduled video interview so that I don't need to manually create meetings and copy links into calendar invites.  
**Acceptance Criteria:**
- Given I schedule a video interview and the company's Zoom integration is enabled, when I confirm the schedule, then a unique Zoom meeting URL is auto-generated and embedded in the calendar invite sent to both the candidate and the interviewer.
- Given the Zoom OAuth token has expired, when the system attempts to generate a link, then it silently refreshes the token and retries without requiring recruiter intervention.
- Given the Zoom API is unavailable, when link generation fails, then the system falls back to prompting the recruiter to manually enter a meeting URL and flags the interview as "Link Required".

---

### US-21: Reschedule an Interview
**Role:** Candidate  
**Story:** As a Candidate, I want to request a reschedule for an interview I can no longer attend so that I don't have to miss the opportunity due to an unavoidable schedule conflict.  
**Acceptance Criteria:**
- Given I log into the candidate portal and see an upcoming interview, when I click "Request Reschedule", then I am prompted to briefly note the reason and confirm the request.
- Given I submit the reschedule request, when the recruiter receives the notification, then they can propose new time slots which are sent back to me through the scheduling flow.
- Given the recruiter proposes new slots, when I select and confirm one, then updated calendar invites are sent to me and all interviewers, and the old calendar invite is cancelled.

---

### US-22: Conduct a Panel Interview with Multiple Interviewers
**Role:** Recruiter  
**Story:** As a Recruiter, I want to assign multiple interviewers to a single interview round so that a panel interview can be scheduled and tracked as a single coordinated event.  
**Acceptance Criteria:**
- Given I create an interview round with 3 interviewers selected, when I schedule the interview, then the availability check queries all 3 interviewers' calendars simultaneously and shows only time slots where all 3 are free.
- Given the panel interview is confirmed, when calendar invites are sent, then all 3 interviewers and the candidate receive the same invite with all panelists listed.
- Given each panelist submits their individual scorecard, when I view the candidate's interview summary, then all 3 scorecards are displayed side-by-side for comparison.

---

## Offer Management

### US-23: Generate an Offer Letter from a Template
**Role:** Recruiter  
**Story:** As a Recruiter, I want to generate an offer letter by selecting a company-approved template and confirming auto-populated details so that I can produce a professional, legally reviewed offer document in under 5 minutes.  
**Acceptance Criteria:**
- Given I navigate to "Create Offer" on a candidate's profile, when I select the "Full-Time Engineer — US" template, then the form pre-populates candidate name, job title, start date, and compensation from the candidate's record and the requisition.
- Given I review the pre-populated fields and confirm, when I click "Generate Preview", then a PDF preview renders in the browser within 10 seconds showing the formatted offer letter.
- Given the preview looks correct, when I click "Submit for Approval", then the first approver in the offer approval chain receives a notification with a link to review the offer PDF.
- Given I select the wrong start date, when I correct it and re-generate the preview, then the updated PDF reflects the change without requiring me to re-enter other fields.

---

### US-24: Approve an Offer Letter
**Role:** Hiring Manager  
**Story:** As a Hiring Manager, I want to review and approve offer letters for my team before they are sent to candidates so that the compensation and terms align with our team budget and leveling guidelines.  
**Acceptance Criteria:**
- Given an offer is submitted for my approval, when I receive the notification, then I can view the full offer PDF inline in the platform and see the approval chain history before taking action.
- Given I review the offer and the compensation is within budget, when I click "Approve", then the offer advances to the next approver (or is sent to the candidate if I am the final approver).
- Given the salary is above the approved budget, when I click "Reject" and note the reason, then the offer is returned to the recruiter with "Rejected" status, my comment is visible on the offer timeline, and the recruiter receives a notification.

---

### US-25: Sign an Offer Letter Digitally
**Role:** Candidate  
**Story:** As a Candidate, I want to review and sign my offer letter electronically so that I can accept the offer securely without needing to print, sign, and scan a document.  
**Acceptance Criteria:**
- Given my offer letter is approved and sent, when I receive the email, then I can open and read the full offer document within the DocuSign/HelloSign interface before signing.
- Given I read the offer and wish to accept, when I click the signature field and sign, then the platform is notified of my acceptance within 60 seconds and my application status updates to "Offer Accepted".
- Given I want to decline the offer, when I click "Decline" in the candidate portal, then I can optionally provide a reason and the recruiter is notified immediately with my decision.
- Given the offer has an expiry date of tomorrow and I have not signed, when I log into the portal, then I see a prominent countdown banner urging me to act before the offer expires.

---

### US-26: Track Offer Negotiation
**Role:** Recruiter  
**Story:** As a Recruiter, I want to record a candidate's counter-offer and revise the compensation in the platform so that the full negotiation history is documented and any revised offer goes through the proper approval chain.  
**Acceptance Criteria:**
- Given a candidate declines the original offer and submits a counter, when I click "Record Counter-Offer" and enter the candidate's proposed salary, then the counter detail is added to the offer negotiation timeline.
- Given I revise the offer with a new salary, when the revised salary exceeds the original by more than 10%, then the platform automatically routes the revised offer back through the full approval chain.
- Given we are on the 3rd negotiation round, when I attempt to create a 4th round, then the system blocks the action and displays a message requiring HR Admin override before proceeding.

---

### US-27: Initiate a Background Check After Offer Acceptance
**Role:** HR Admin  
**Story:** As an HR Admin, I want the platform to automatically trigger a Checkr background check when a candidate accepts their offer so that the check is initiated without a manual step and I can monitor results in the platform.  
**Acceptance Criteria:**
- Given an offer is signed and the Checkr integration is enabled, when the offer status changes to "Accepted", then a background check order is automatically submitted to Checkr within 5 minutes using the check package configured for that job's level.
- Given the background check is submitted, when I view the candidate's offer detail page, then the Checkr status (Pending / In Progress / Clear / Consider) is visible with a timestamp of the last update.
- Given Checkr returns a "Consider" result, when the status is received via webhook, then I receive an in-platform and email notification, and the candidate's page displays a banner noting that manual review under FCRA adverse action procedures is required.

---

## Analytics and Reporting

### US-28: View the Hiring Funnel for a Requisition
**Role:** Recruiter  
**Story:** As a Recruiter, I want to view a visual funnel report for each open requisition so that I can quickly identify which stage is causing candidate drop-off and take corrective action.  
**Acceptance Criteria:**
- Given I open a requisition's analytics tab, when the page loads, then I see a funnel chart showing the count and percentage of candidates at each pipeline stage from Applied through Hired.
- Given I see a high drop-off rate between "Phone Screen" and "Technical Interview", when I hover over the drop-off arrow, then I see a breakdown of drop-off reasons (rejected, withdrew, no response) so I can diagnose the issue.
- Given the pipeline has had no activity in 7 days, when I view the funnel, then a warning banner prompts me to review stalled candidates.

---

### US-29: View Time-to-Hire Metrics on the Dashboard
**Role:** Recruiter  
**Story:** As a Recruiter, I want to see my time-to-hire metrics on my dashboard so that I can benchmark my performance against team averages and identify roles where the hiring process is taking too long.  
**Acceptance Criteria:**
- Given I log into the recruiter dashboard, when the dashboard loads, then I see my average time-to-hire (excluding weekends) for the current quarter alongside the team average and the 30-day trend.
- Given I click on the time-to-hire card, when the detail view opens, then I see a breakdown per requisition showing the date applied, date hired, and total days.
- Given a role has been open for more than twice the department average time-to-fill, when I view the dashboard, then the requisition is flagged with an orange indicator and surfaces in a "Needs Attention" section.

---

### US-30: View Source Attribution and Cost-Per-Hire
**Role:** HR Admin  
**Story:** As an HR Admin, I want to see which recruitment channels are generating the most hires at the lowest cost so that I can optimize the company's job board spend and sourcing strategy.  
**Acceptance Criteria:**
- Given I navigate to "Source Analytics" and enter the monthly job board spend per channel, when I view the Source ROI report, then I see cost-per-application and cost-per-hire for each source over my selected date range.
- Given LinkedIn has a high cost-per-hire compared to employee referrals, when I view the report, then I can export it as a CSV to share with the talent ops team for budget planning.
- Given a new job board is added and starts generating applications, when its applications begin flowing in, then it automatically appears as a source in the analytics report.

---

### US-31: Generate an EEO-1 Report
**Role:** HR Admin  
**Story:** As an HR Admin, I want to generate an EEO-1 Component 1 report from the platform so that I can fulfill federal reporting obligations without manually compiling data from multiple spreadsheets.  
**Acceptance Criteria:**
- Given I navigate to "Compliance Reports" and select "EEO-1 Report", when I select the reporting period and click "Generate", then the report renders a breakdown of all hired employees by job category, race/ethnicity, and gender.
- Given the report is generated, when I click "Export", then a CSV file is produced in the standard EEO-1 Component 1 format compatible with the EEOC online filing system.
- Given I review the data, when a job category is missing EEO classification on some requisitions, then the report highlights the gap and links me to the requisitions that need to be updated.

---

### US-32: Schedule a Weekly Hiring Report for Executives
**Role:** HR Admin  
**Story:** As an HR Admin, I want to schedule a weekly hiring summary report that is automatically emailed to the executive team every Monday morning so that leadership stays informed without needing to log into the platform.  
**Acceptance Criteria:**
- Given I navigate to "Scheduled Reports" and create a new schedule, when I select the "Executive Hiring Summary" report template, set the frequency to "Weekly on Monday at 8:00 AM", and add executive email addresses, then the schedule is saved and confirmed.
- Given the scheduled time arrives, when the system generates the report, then a PDF is emailed to all configured recipients within 5 minutes of the scheduled time.
- Given a report fails to generate (e.g., data error), when the failure occurs, then I receive an admin alert notification and the executives receive a fallback email noting the report is delayed.

---

### US-33: View Executive Talent Acquisition Dashboard
**Role:** Executive  
**Story:** As a CHRO, I want a high-level dashboard showing hiring velocity, headcount plan progress, and diversity metrics so that I can make strategic talent decisions and report to the board with confidence.  
**Acceptance Criteria:**
- Given I log into the executive dashboard, when the dashboard loads, then I see four key metrics above the fold: open roles, hires this quarter, average time-to-fill, and offer acceptance rate, with trend arrows compared to the previous quarter.
- Given I want to drill into diversity data, when I click the "Diversity" tab, then I see pipeline representation by gender and race/ethnicity at each stage with comparison against company targets.
- Given I want to see department-level breakdown, when I filter by "Department: Engineering", then all metrics on the dashboard update to show engineering-specific data.

---

## Candidate Portal and Experience

### US-34: Create a Candidate Profile and Apply with One Click
**Role:** Candidate  
**Story:** As a Candidate, I want to create a profile and apply to multiple jobs without re-entering my information each time so that the process is fast and I can explore all relevant opportunities.  
**Acceptance Criteria:**
- Given I register on the candidate portal and upload my resume, when parsing completes, then my profile is populated with my work history, education, and skills.
- Given my profile is complete, when I click "Apply" on a second job, then the application form is pre-populated with my saved profile data and I only need to answer job-specific screening questions.
- Given I update my resume on my profile, when a recruiter views my profile on a new application, then they see the latest resume; my resume on existing in-progress applications is unaffected.

---

### US-35: Opt Into a Talent Pool
**Role:** Candidate  
**Story:** As a Candidate, I want to opt into a talent pool for future roles even if there's no current opening that matches my experience so that I can be considered proactively when a relevant position opens.  
**Acceptance Criteria:**
- Given I visit the company's careers page and see a "Join Our Talent Community" option, when I click it and submit my email and resume, then I receive a confirmation email and my profile is added to the company's talent pool with opt-in consent recorded.
- Given a recruiter creates a new requisition that matches my skills, when they run a search and find my profile, then my profile is visible with a "Talent Community" tag indicating I opted in.
- Given I want to withdraw from the talent pool, when I click "Unsubscribe" in any email or visit the portal settings, then my consent is revoked and I am removed from active talent pool searches within 24 hours.

---

## Compliance and Data Privacy

### US-36: Anonymize Candidate Data Per GDPR Right to Erasure
**Role:** HR Admin  
**Story:** As an HR Admin, I want to process a verified GDPR erasure request by anonymizing a candidate's PII so that we comply with the regulation within 30 days while retaining aggregate data for analytics.  
**Acceptance Criteria:**
- Given a verified erasure request is logged, when I review and approve it in the "Data Requests" dashboard, then the system replaces the candidate's name, email, phone, address, and resume with anonymized placeholders within the configured window.
- Given the anonymization is complete, when I query the candidate's former record, then no PII is retrievable and the audit log records the erasure event with the timestamp and acting admin.
- Given the candidate had multiple applications across different tenants, when erasure is processed, then only the data belonging to the tenant that received the request is erased; other tenants' data is unaffected.

---

### US-37: Manage Candidate Consent Records
**Role:** HR Admin  
**Story:** As an HR Admin, I want to view and manage the consent records for each candidate so that I can demonstrate GDPR compliance to auditors and respond to regulatory inquiries.  
**Acceptance Criteria:**
- Given I search for a candidate in the compliance panel, when I view their record, then I see a consent history log showing: consent type, consent text version, collection timestamp, IP address, and current status (Active, Withdrawn, Expired).
- Given a candidate withdraws marketing consent, when the withdrawal is processed, then all future marketing-category emails are suppressed for that candidate and the suppression is reflected in the consent log.
- Given I export consent records for an audit, when I click "Export Consent Log", then a CSV is generated containing all candidate consent records for the selected date range in a format acceptable for a GDPR audit.

---

## HR Admin Configuration

### US-38: Configure Role Permissions
**Role:** HR Admin  
**Story:** As an HR Admin, I want to configure which actions are available to each role so that recruiters and hiring managers only have access to the capabilities relevant to their responsibilities.  
**Acceptance Criteria:**
- Given I navigate to "Roles & Permissions" settings, when I view the Hiring Manager role, then I see a matrix of permissions (view candidate profile, submit scorecard, view salary range, approve offer, etc.) with toggles for each.
- Given I disable "View Salary Range" for the Hiring Manager role, when a Hiring Manager views a candidate profile, then the salary range field is hidden and the API call for that field returns a 403.
- Given I enable a new permission for a role, when the change is saved, then affected users receive the updated permission on their next API call within 60 seconds without requiring a logout.

---

### US-39: Manage Offer Letter Templates
**Role:** HR Admin  
**Story:** As an HR Admin, I want to create and manage offer letter templates with merge fields so that recruiters can generate legally reviewed, consistently formatted offers without copying and pasting from Word documents.  
**Acceptance Criteria:**
- Given I navigate to "Offer Templates" and create a new template, when I use the rich-text editor and insert merge fields like `{{CANDIDATE_NAME}}` and `{{BASE_SALARY}}`, then the system validates that all inserted merge fields are recognized and marks unrecognized tokens as errors.
- Given I save the template and mark it as active, when a recruiter generates an offer using it, then all merge fields are replaced with the correct values from the candidate and requisition records.
- Given I need to update the template due to a legal change, when I update and save the new version, then existing in-progress offers that used the old version are unaffected, and only newly created offers use the new version.

---

### US-40: Connect and Test a Job Board Integration
**Role:** HR Admin  
**Story:** As an HR Admin, I want to connect our LinkedIn and Indeed API credentials in the platform and verify the connection before enabling job syndication so that I can ensure job posts will distribute successfully.  
**Acceptance Criteria:**
- Given I navigate to "Integrations > Job Boards", when I enter our LinkedIn API key and click "Test Connection", then the system makes a test API call and displays "Connection Successful" with the account name and last verified timestamp.
- Given the LinkedIn API key is invalid, when I click "Test Connection", then the system displays the API error message returned by LinkedIn (e.g., "401 Unauthorized: Invalid API key") so I can troubleshoot.
- Given I enable a job board integration, when the next job is activated, then it is automatically submitted to that board and the status appears on the requisition detail page within 5 minutes.

---

### US-41: Set Up and Manage Email Notification Templates
**Role:** HR Admin  
**Story:** As an HR Admin, I want to customize the email notification templates sent to candidates so that all communications reflect our employer brand and include the correct information for each event.  
**Acceptance Criteria:**
- Given I navigate to "Email Templates", when I select the "Application Received" template and edit the subject line and body, then a preview renders showing the email as it will appear to candidates.
- Given I insert the merge field `{{COMPANY_NAME}}` in the template body, when a candidate receives the email, then the merge field is replaced with the actual company name for that tenant.
- Given I save a template, when I send a test email to my own address, then I receive the email within 2 minutes with all merge fields populated with sample data.

---

### US-42: Configure Background Check Packages Per Job Level
**Role:** HR Admin  
**Story:** As an HR Admin, I want to map specific Checkr background check packages to job levels so that the appropriate level of screening is triggered automatically based on the role, without the recruiter needing to manually select a package each time.  
**Acceptance Criteria:**
- Given I navigate to "Background Checks > Packages", when I assign the "Enhanced – Criminal + Employment + Education + Credit" package to "Senior" and above job levels, then any offer accepted for a Senior+ role automatically triggers this package.
- Given I assign the "Standard – Criminal + Employment" package to "Individual Contributor" roles, when an offer is accepted for an IC-level role, then the standard package is triggered without recruiter intervention.
- Given a new Checkr package is added to our Checkr account, when I sync packages in the platform settings, then the new package appears in the mapping configuration within 30 seconds.

---

### US-43: Audit Recruiter Actions on a Candidate Profile
**Role:** HR Admin  
**Story:** As an HR Admin, I want to view a complete, immutable audit log of all actions taken on a candidate's profile so that I can investigate any compliance concerns or candidate complaints.  
**Acceptance Criteria:**
- Given I search for a candidate in the audit log, when I view their profile audit trail, then I see every action in chronological order: application submitted, stage changes, emails sent, notes added, tags applied, resume viewed, and offer actions.
- Given a recruiter views a candidate's PII fields, when the read is logged, then the log entry shows the recruiter's name, their IP address, and the fields accessed.
- Given I attempt to delete an audit log entry, when I take any action, then the deletion is blocked and an error message states the audit log is immutable.

---

### US-44: Manage Multi-Company Tenant Settings
**Role:** HR Admin  
**Story:** As an HR Admin for a staffing agency managing multiple client companies, I want to configure separate company profiles within the platform so that each client's jobs, candidates, and pipelines are completely isolated.  
**Acceptance Criteria:**
- Given I navigate to "Company Settings", when I create a new company profile with its own subdomain, branding, and RBAC configuration, then the new company workspace is accessible only to users assigned to that company.
- Given a recruiter is assigned to Company A, when they log in, then they can only see Company A's requisitions, candidates, and settings — Company B's data is not accessible or visible in any API call.
- Given a candidate applies to Company A, when Company B's recruiter performs a candidate search, then the Company A candidate does not appear in Company B's results.

---

*End of User Stories — v1.0*
