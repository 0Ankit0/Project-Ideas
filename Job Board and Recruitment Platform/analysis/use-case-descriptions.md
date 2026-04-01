# Use Case Descriptions — Job Board and Recruitment Platform

---

## UC-01: Post and Publish Job

### UC-01: Post and Publish Job

| Field | Description |
|---|---|
| **Use Case ID** | UC-01 |
| **Name** | Post and Publish Job |
| **Actor(s)** | Primary: Recruiter; Secondary: Hiring Manager, HR Admin, System, External Job Boards |
| **Trigger** | Recruiter initiates a new job requisition or a Hiring Manager submits a job request through the platform |
| **Pre-conditions** | 1. Recruiter is authenticated and has the `recruiter` or `senior-recruiter` role. 2. At least one active ATS pipeline template exists. 3. Job board syndication credentials are configured in Settings. |
| **Post-conditions** | 1. Job posting is in `PUBLISHED` status and visible on the public job board. 2. Syndication tasks have been dispatched to all configured external job boards. 3. An audit log entry records who published the job and at what time. 4. Recruiter and Hiring Manager receive a confirmation notification. |
| **Priority** | High |
| **Frequency** | ~50 new job postings per month per organisation; peak during Q1 and Q3 headcount cycles |

**Main Success Scenario:**

1. Recruiter navigates to **Jobs → New Job** and selects job family, department, and hiring manager.
2. Recruiter fills in the job description form: title, location (remote/hybrid/on-site), employment type, salary band, required skills, nice-to-have skills, and number of openings.
3. Recruiter configures screening questions (up to 10 questions; types: yes/no, short-answer, multiple-choice, file-upload).
4. Recruiter selects an ATS pipeline template to associate with the job (e.g., "Engineering – Standard 5-Stage").
5. Recruiter selects external job boards for syndication (LinkedIn, Indeed, Glassdoor, ZipRecruiter) and sets application deadline.
6. Recruiter clicks **Submit for Approval**; system transitions job status from `DRAFT` to `PENDING_APPROVAL` and sends an email notification to all HR Admins.
7. HR Admin opens the approval queue, reviews job description for compliance (salary band within policy, EEO statement present, job title matches approved taxonomy).
8. HR Admin clicks **Approve**; system transitions status to `APPROVED`.
9. System publishes the job on the internal job board instantly and enqueues a Kafka message `job.publish_to_boards` for the syndication worker.
10. Syndication worker calls LinkedIn Jobs API, Indeed Publisher API, Glassdoor API, and ZipRecruiter API sequentially; records `externalJobId` and `syndicationStatus` for each board.
11. System sends a "Job Published" in-app and email notification to Recruiter and Hiring Manager with deep links to the live postings on each board.
12. Job application counter initialises to 0; ATS pipeline for the job is activated and ready to receive candidates.

**Alternative Flows:**

- **AF-1 (HR Admin Rejects Job):** At step 8, HR Admin clicks **Request Changes** and adds a comment. System transitions status back to `DRAFT` and notifies the Recruiter with the rejection reason. Recruiter edits and re-submits from step 2.
- **AF-2 (Schedule Future Publication):** At step 5, Recruiter sets a future `publishAt` date/time. After HR Admin approval at step 8, system schedules a cron trigger for the specified time before executing steps 9–12.
- **AF-3 (Internal-Only Posting):** Recruiter deselects all external job boards at step 5. Steps 10 and the external syndication notification in step 11 are skipped; job is only visible on the internal career portal.
- **AF-4 (Clone from Existing Job):** Recruiter selects **Clone Job** from an existing published job. System pre-fills all fields from the source job. Recruiter adjusts relevant fields and continues from step 3.

**Exception Flows:**

- **EF-1 (Syndication API Failure):** At step 10, if one or more job board APIs return an error, the system logs the failure, marks that board's syndication status as `FAILED`, and raises an alert in the Recruiter's notification centre. A retry is attempted after 30 minutes (up to 3 retries). The job is still considered published on boards that succeeded.
- **EF-2 (Missing Mandatory Fields):** At step 6, if the job description is missing EEO statement, salary band, or employment type, the system blocks submission and highlights the missing fields with inline validation errors.
- **EF-3 (Approval Timeout):** If no HR Admin approves or rejects within 5 business days, the system escalates to the HR Admin's manager and sends daily reminders.

**Business Rules:**

- BR-1: Every job must include an EEO/equal opportunity statement before it can be submitted for approval.
- BR-2: Salary band must fall within the approved compensation range for the job grade; the system validates against the HR compensation table.
- BR-3: A maximum of 3 active postings for the same job title in the same department is allowed simultaneously.
- BR-4: External syndication is only permitted for jobs with `employmentType = FULL_TIME | PART_TIME | CONTRACT`; internships must remain internal unless explicitly overridden by HR Admin.
- BR-5: All job titles must match an entry in the approved job taxonomy maintained by HR Admin.

---

## UC-02: Apply for Job

### UC-02: Apply for Job

| Field | Description |
|---|---|
| **Use Case ID** | UC-02 |
| **Name** | Apply for Job |
| **Actor(s)** | Primary: Candidate; Secondary: System |
| **Trigger** | Candidate clicks **Apply Now** on a published job listing from any channel (internal portal, LinkedIn, Indeed, direct link) |
| **Pre-conditions** | 1. Job is in `PUBLISHED` status and application deadline has not passed. 2. Job has not exceeded the maximum application cap (if set). |
| **Post-conditions** | 1. A new `Application` record is created with status `NEW`. 2. Candidate's resume is stored in S3 and queued for AI parsing. 3. Candidate receives a confirmation email with application reference number. 4. Recruiter receives a real-time notification of the new application. |
| **Priority** | High |
| **Frequency** | 100–500 applications per job per posting; high burst during the first 48 hours after publication |

**Main Success Scenario:**

1. Candidate browses the job board, uses keyword search and filters (location, job type, salary range, department), and clicks on a job listing to view the full description.
2. Candidate clicks **Apply Now**; system checks if the candidate has an existing account by prompting Sign In or Continue as Guest.
3. Candidate signs in with email/password or SSO (Google, LinkedIn OAuth). If new, candidate completes a lightweight registration: name, email, phone, password.
4. System pre-fills the application form with data from the candidate's existing profile (if available): name, contact details, LinkedIn URL, current employer.
5. Candidate uploads their resume (PDF, DOCX, or DOC; max 10 MB). System performs file-type and size validation and generates a secure pre-signed S3 upload URL.
6. Candidate optionally uploads a cover letter.
7. Candidate answers the job's custom screening questions. System validates required questions are answered before allowing progression.
8. Candidate reviews the filled application summary and clicks **Submit Application**.
9. System creates the `Application` record, assigns a unique application reference number (e.g., `APP-2024-00342`), and sets initial status to `NEW`.
10. System publishes a Kafka event `application.created` consumed by the AI Parsing Service and the Notification Service.
11. AI Parsing Service (FastAPI/GPT-4o) parses the resume asynchronously and updates the candidate's structured profile within 60 seconds.
12. Notification Service sends a confirmation email to the candidate (via SendGrid) containing the application reference number, job title, company name, and a link to the candidate portal to track status.
13. Recruiter's ATS dashboard updates in real time (WebSocket push) showing the new application in the `New Applications` column.

**Alternative Flows:**

- **AF-1 (Apply via LinkedIn Easy Apply):** Candidate clicks Apply on LinkedIn; LinkedIn sends a webhook payload to the platform's ingestion endpoint. System creates an `Application` record pre-populated with LinkedIn profile data. Steps 2–8 are skipped. Process continues from step 9.
- **AF-2 (Returning Candidate — Resume Already on File):** At step 5, system detects the candidate has previously uploaded a resume. Candidate is offered the option to use the existing resume or upload a new one.
- **AF-3 (Duplicate Application):** At step 8, if the candidate has already applied to the same job (same `candidateId` + `jobId`), system displays an error: "You have already applied to this position on [date]." Submission is blocked.
- **AF-4 (Application Cap Reached):** At step 1, if the job's `maxApplications` limit has been reached, the **Apply Now** button is disabled and replaced with "Applications Closed – Position is no longer accepting applications."

**Exception Flows:**

- **EF-1 (File Upload Failure):** At step 5, if the S3 upload fails, system displays an error and allows the candidate to retry. After 3 failed attempts, system offers an email submission fallback.
- **EF-2 (AI Parsing Service Timeout):** At step 11, if the AI service does not respond within 120 seconds, the application is accepted and stored; the parsing is retried via a dead-letter queue mechanism. The recruiter is notified that AI scoring may be delayed.
- **EF-3 (Email Delivery Failure):** At step 12, if SendGrid returns a non-2xx response, the notification is queued for retry (exponential back-off, 3 attempts). Failure is logged in the audit trail.

**Business Rules:**

- BR-1: Candidates may not apply to the same job more than once during the active posting period.
- BR-2: Accepted file formats are restricted to PDF, DOCX, and DOC only; maximum file size is 10 MB.
- BR-3: All applications must capture a valid email address for communication purposes; phone number is optional.
- BR-4: Screening questions marked as `required` and `disqualifying` (i.e., a "No" answer immediately disqualifies) are evaluated automatically upon submission.
- BR-5: Applications submitted after the job's `applicationDeadline` are rejected with an appropriate error message; no exceptions without HR Admin override.

---

## UC-03: AI Resume Screening

### UC-03: AI Resume Screening

| Field | Description |
|---|---|
| **Use Case ID** | UC-03 |
| **Name** | AI Resume Screening |
| **Actor(s)** | Primary: System; Secondary: Recruiter, Hiring Manager |
| **Trigger** | `application.created` Kafka event is published after a candidate submits an application with a resume |
| **Pre-conditions** | 1. Application record exists in `NEW` status. 2. Resume file is accessible in S3. 3. Job requirements (required skills, nice-to-have skills, years of experience, education level) are populated. 4. OpenAI API key is valid and rate limits are available. |
| **Post-conditions** | 1. Candidate profile is updated with structured extracted data (skills, work history, education, certifications). 2. Application has an AI match score (0–100) and a confidence level. 3. Application is tagged `AI_TOP_CANDIDATE` if score ≥ 75 or `AI_BELOW_THRESHOLD` if score < 40. 4. Recruiter can see AI score and extracted skills in the ATS pipeline. |
| **Priority** | High |
| **Frequency** | Triggered for 100% of applications that include a resume file; asynchronous, target SLA: < 60 seconds per resume |

**Main Success Scenario:**

1. AI Parsing Service (FastAPI on Python 3.11) receives the `application.created` Kafka event containing `applicationId`, `jobId`, `resumeS3Key`.
2. Service fetches the resume file from S3 using a pre-signed URL.
3. Service converts the file to plain text: PDFs via `pdfminer.six`, DOCX via `python-docx`.
4. Service sends the extracted text to OpenAI GPT-4o with a structured prompt that instructs it to extract: full name, contact info, skills (with proficiency levels), work experience entries (company, title, start date, end date, description), education entries, certifications, and languages.
5. GPT-4o returns a structured JSON response; service validates the schema using Pydantic models.
6. Service fetches the job requirements from the internal Job Service API: `requiredSkills[]`, `preferredSkills[]`, `minYearsExperience`, `requiredEducationLevel`.
7. Service computes a match score using a weighted algorithm:
   - Required skills coverage: 40% weight
   - Total years of relevant experience vs. minimum: 30% weight
   - Preferred skills coverage: 20% weight
   - Education level match: 10% weight
8. Service generates a natural-language summary: "Candidate has 7 of 9 required skills (missing: Kubernetes, Terraform). 5 years of relevant experience exceeds the 3-year minimum. Strong match."
9. Service publishes a `resume.parsed` Kafka event and updates the Application record via the Application Service API with: `aiScore`, `aiConfidence`, `extractedProfile`, `aiSummary`.
10. Application Service applies auto-tagging rules: score ≥ 75 → `AI_TOP_CANDIDATE`; score 40–74 → `AI_REVIEWED`; score < 40 → `AI_BELOW_THRESHOLD`.
11. If auto-advance rule is configured (e.g., "Auto-move AI_TOP_CANDIDATE to Phone Screen"), Application Service moves the candidate to the next pipeline stage and notifies the Recruiter.
12. Recruiter's ATS dashboard updates the candidate card with the AI score badge, extracted skills chips, and the AI summary tooltip.

**Alternative Flows:**

- **AF-1 (No Resume Uploaded):** If the application was submitted without a resume (e.g., via LinkedIn Easy Apply with no attachment), the AI Parsing Service marks the application `AI_SCORE_UNAVAILABLE` and notifies the Recruiter to request a resume manually.
- **AF-2 (Non-English Resume):** GPT-4o detects a non-English resume; service translates the text first via the OpenAI translation prompt, then proceeds with parsing. A `translationWarning` flag is set on the candidate record.
- **AF-3 (Recruiter Overrides AI Score):** After step 12, Recruiter reviews the AI score and disagrees. They click **Override Score**, enter a manual score (0–100) and a reason. System logs the override in the audit trail and uses the manual score for subsequent sorting.

**Exception Flows:**

- **EF-1 (OpenAI API Error / Rate Limit):** At step 4, if the OpenAI API returns a 429 or 5xx error, the service retries with exponential back-off (1s, 2s, 4s, max 3 retries). After 3 failures, the event is placed on the dead-letter queue and the Recruiter is notified that AI scoring is pending.
- **EF-2 (Malformed / Unreadable Resume):** If text extraction at step 3 fails (corrupted file, image-only PDF), the service marks the application `AI_PARSE_FAILED`, stores the error reason, and notifies the Recruiter to request a new resume from the candidate.
- **EF-3 (GPT-4o Returns Invalid Schema):** At step 5, if the Pydantic validation fails, the service logs the raw response, falls back to regex-based skill extraction, and sets `aiConfidence = LOW`.

**Business Rules:**

- BR-1: AI scores are advisory only; no candidate may be automatically rejected solely on the basis of an AI score without recruiter confirmation.
- BR-2: The AI scoring model and prompt version are versioned; all scores are stored with the `modelVersion` used to produce them for auditability.
- BR-3: Extracted PII (contact information) is stored encrypted at rest (AES-256) and is never sent to third-party analytics systems.
- BR-4: Auto-advance rules can only move candidates forward in the pipeline; backward movement requires a human action.
- BR-5: AI summary text must not include references to age, gender, ethnicity, or any protected characteristics detected in the resume.

---

## UC-04: Schedule Interview

### UC-04: Schedule Interview

| Field | Description |
|---|---|
| **Use Case ID** | UC-04 |
| **Name** | Schedule Interview |
| **Actor(s)** | Primary: Recruiter; Secondary: Candidate, Hiring Manager (as Interviewer), System, Google Calendar / Outlook, Zoom |
| **Trigger** | Recruiter moves a candidate to an interview stage in the ATS pipeline and clicks **Schedule Interview** |
| **Pre-conditions** | 1. Candidate is in an interview-stage (e.g., "Phone Screen", "Technical Interview", "Final Round"). 2. Interview panel members are assigned to the job. 3. Panel members have connected their Google Calendar or Outlook calendar via OAuth. |
| **Post-conditions** | 1. Interview event is created in all participants' calendars. 2. Zoom/Teams meeting link is embedded in the calendar invite. 3. Candidate receives scheduling confirmation email with interview details. 4. Interview record is created in the system with status `SCHEDULED`. |
| **Priority** | High |
| **Frequency** | ~3–5 interviews scheduled per hired candidate; peak scheduling on Tuesday–Thursday mornings |

**Main Success Scenario:**

1. Recruiter opens a candidate's application in the ATS pipeline and clicks **Schedule Interview**.
2. Recruiter selects the interview type (Phone Screen / Technical / Behavioural / Panel / Final), sets the expected duration (30 / 45 / 60 / 90 minutes), and selects interview panel members from the job's assigned users.
3. System calls the Google Calendar Free/Busy API and Microsoft Graph free/busy API for each panel member to retrieve their availability for the next 10 business days.
4. System computes overlapping free slots that satisfy the duration requirement and the company's scheduling policy (interviews only 9 AM–5 PM in the candidate's timezone; minimum 30-minute buffer between interviews).
5. System presents the top 5 available time slots to the Recruiter for review. Recruiter may accept the suggestions or manually select a different time.
6. Recruiter clicks **Send Time Slots to Candidate**. System generates a unique scheduling link (valid for 48 hours) and sends it to the Candidate via email (SendGrid template `interview-scheduling`).
7. Candidate opens the email, clicks the scheduling link, reviews the proposed time slots, and selects one.
8. System confirms the selected slot by calling:
   - Google Calendar API (or Microsoft Graph) to create calendar events for all panel members and the candidate.
   - Zoom Meetings API (or Teams Graph API) to create a meeting and retrieve the join URL.
9. System embeds the Zoom/Teams join URL in all calendar invites and sends confirmation emails to all participants with interview preparation guidelines.
10. Interview record is created in the database with `status = SCHEDULED`, `scheduledAt`, `interviewers[]`, `videoConferenceUrl`, `interviewType`.
11. Recruiter's ATS pipeline card updates to show the scheduled interview date/time badge.
12. System schedules two automated reminders: 24 hours before and 1 hour before the interview, sent to both candidate and interviewers.

**Alternative Flows:**

- **AF-1 (No Available Slots in 10-Day Window):** At step 4, if no overlapping free slots are found, system notifies the Recruiter and suggests either extending the search window to 20 days or reducing the panel size.
- **AF-2 (Candidate Does Not Select Within 48 Hours):** The scheduling link expires. System notifies the Recruiter, who can regenerate the link with a new 48-hour window.
- **AF-3 (Recruiter Manually Schedules):** Recruiter bypasses candidate self-scheduling by directly picking a slot and sending a non-interactive calendar invite. Candidate receives the invite but cannot change the time.
- **AF-4 (In-Person Interview):** Recruiter selects "In-Person" mode. Steps 8b (Zoom/Teams API) are skipped. Interview location/room details are included in the calendar invite instead.

**Exception Flows:**

- **EF-1 (Calendar API OAuth Token Expired):** At step 3, if a panel member's OAuth token is expired, system flags that interviewer as "Calendar Disconnected" and notifies the Recruiter. The Recruiter can either ask the interviewer to reconnect or exclude them from the panel.
- **EF-2 (Zoom API Failure):** At step 8, if Zoom returns an error, system falls back to Microsoft Teams if configured. If both fail, a placeholder "Video link TBD" is used and the Recruiter is alerted to manually add a link.
- **EF-3 (Calendar Event Creation Conflict — Race Condition):** At step 8, if another event is created in the same slot between availability check and event creation, the Google Calendar API returns a conflict error. System detects this, fetches updated availability, and re-presents the Recruiter with alternative slots.

**Business Rules:**

- BR-1: Interviews cannot be scheduled on weekends or public holidays (configurable per country/locale).
- BR-2: Panel members must have at least one completed scorecard training module before they can be added to an interview panel.
- BR-3: The scheduling link sent to candidates must expire within 72 hours and be single-use.
- BR-4: All interview records are retained for 2 years for compliance auditing.
- BR-5: Video conference links must be unique per interview; shared/reused links are not allowed.

---

## UC-05: Submit Interview Scorecard

### UC-05: Submit Interview Scorecard

| Field | Description |
|---|---|
| **Use Case ID** | UC-05 |
| **Name** | Submit Interview Scorecard |
| **Actor(s)** | Primary: Hiring Manager (as Interviewer); Secondary: Recruiter, System |
| **Trigger** | Interview has been completed (status transitions to `COMPLETED`) OR the interviewer manually opens the scorecard form |
| **Pre-conditions** | 1. An interview record in `SCHEDULED` or `COMPLETED` status exists for the candidate. 2. The Hiring Manager is listed as an interviewer for this interview. 3. A scorecard template is configured for the interview type. |
| **Post-conditions** | 1. Scorecard is stored with the interviewer's ratings and recommendation. 2. Aggregate interview score is recalculated across all submitted scorecards. 3. Recruiter and other interviewers are notified that a new scorecard has been submitted. 4. If all expected interviewers have submitted, hiring recommendation is generated. |
| **Priority** | High |
| **Frequency** | 2–5 scorecards per interview round; 6–15 scorecards per hired candidate |

**Main Success Scenario:**

1. At the scheduled interview end time, system automatically transitions the interview status from `SCHEDULED` to `COMPLETED` and sends the interviewer an in-app notification and email with a direct link to the scorecard form.
2. Interviewer (Hiring Manager) opens the scorecard form, which is pre-populated with: candidate name, job title, interview type, and competency framework for the role.
3. Interviewer rates the candidate on each defined competency using a 1–5 Likert scale (1 = Significantly Below Bar, 5 = Significantly Exceeds Bar). Competencies may include: Technical Depth, Problem Solving, Communication, Culture Fit, Leadership Potential (as applicable per role level).
4. Interviewer adds optional free-text notes for each competency to support the numeric rating.
5. Interviewer selects a hiring recommendation from: **Strong Hire**, **Hire**, **Lean Hire**, **No Decision**, **Lean No Hire**, **No Hire**, **Strong No Hire**.
6. Interviewer enters an overall summary comment (min 50 characters) to prevent empty submissions.
7. Interviewer clicks **Submit Scorecard**. System validates all required competencies are rated and a recommendation is selected.
8. System saves the scorecard, marks the interviewer's submission status as `SUBMITTED`, and logs the submission timestamp.
9. System recalculates the aggregate score across all submitted scorecards for this interview round using the weighted average formula defined in the scorecard template.
10. System checks if all expected interviewers for this interview round have submitted their scorecards.
11. If all scorecards are submitted, system generates a **Hiring Recommendation Summary** showing individual ratings by competency, overall aggregate score, and a consensus recommendation based on majority vote.
12. Recruiter and Hiring Manager receive a notification with a link to the Hiring Recommendation Summary.

**Alternative Flows:**

- **AF-1 (Interviewer Submits Before Interview Completes):** An interviewer opens the scorecard form proactively during or immediately after the interview. The system allows early submission; the interview status remains `SCHEDULED` until the scheduled end time.
- **AF-2 (Interviewer Requests Additional Round):** At step 5, Interviewer selects "No Decision" and ticks the "Request Additional Round" checkbox. System flags the candidate for a follow-up interview and notifies the Recruiter to schedule a new round.
- **AF-3 (Scorecard Amendment):** Within 2 hours of submission, an interviewer can edit their scorecard. After 2 hours, edits require Recruiter approval and are logged in the audit trail with the reason for amendment.

**Exception Flows:**

- **EF-1 (SLA Breach — Scorecard Not Submitted Within 48 Hours):** System sends reminders at 24h and 44h post-interview. If still not submitted at 48h, System escalates to the Recruiter and flags the interview round as `SCORECARD_OVERDUE`. Recruiter can force-close the round with a note, or contact the interviewer directly.
- **EF-2 (Split Decision — Highly Divergent Scores):** At step 9, if the standard deviation of individual scores exceeds the configured threshold (e.g., σ > 1.5), system flags the round as `SPLIT_DECISION` and notifies the Recruiter, who may schedule a debrief call.
- **EF-3 (Incomplete Scorecard Submission Attempt):** At step 7, if required competencies are not rated, system highlights the unfilled fields and blocks submission.

**Business Rules:**

- BR-1: Interviewers cannot view other interviewers' scorecards until they have submitted their own, preventing anchoring bias.
- BR-2: Scorecards are immutable after the 2-hour amendment window unless overridden by HR Admin.
- BR-3: Scorecard templates are role-specific and managed by HR Admin; recruiters cannot modify competency definitions.
- BR-4: All scorecards are retained for 3 years as part of the hiring audit trail.
- BR-5: The aggregate scoring algorithm weights must sum to 1.0; configuration is validated when the scorecard template is saved.

---

## UC-06: Generate and Send Offer Letter

### UC-06: Generate and Send Offer Letter

| Field | Description |
|---|---|
| **Use Case ID** | UC-06 |
| **Name** | Generate and Send Offer Letter |
| **Actor(s)** | Primary: Recruiter; Secondary: HR Admin (approval), System, DocuSign, Candidate |
| **Trigger** | Hiring decision is made ("Hire") and candidate is moved to the "Offer" stage in the ATS pipeline |
| **Pre-conditions** | 1. Candidate has a final interview recommendation of "Hire" or "Strong Hire". 2. At least one offer letter template exists for the job family and level. 3. Recruiter has the `generate-offer` permission. 4. DocuSign integration is configured with a valid API key. |
| **Post-conditions** | 1. Offer letter PDF is stored in S3. 2. DocuSign envelope is created and sent to the candidate. 3. Offer record is created with status `SENT`. 4. Candidate receives an email notification with a link to view and sign the offer. 5. Audit log records the offer generation, approval chain, and send event. |
| **Priority** | High |
| **Frequency** | 1 offer per hire; ~20–30 offers per month for a mid-size organisation |

**Main Success Scenario:**

1. Recruiter opens the candidate's profile in the "Offer" ATS stage and clicks **Generate Offer Letter**.
2. System presents available offer letter templates for the job family/level. Recruiter selects the appropriate template (e.g., "Full-Time Engineering Offer – US").
3. System pre-fills dynamic fields from the candidate and job records: candidate full name, job title, department, start date (editable), reporting manager, work location.
4. Recruiter enters compensation details: base salary, signing bonus (if any), annual target bonus percentage, equity grant (number of options, vesting schedule), benefits package reference.
5. System validates the entered salary against the approved compensation band for the job grade. If salary exceeds the band maximum, an error is shown and HR Admin override is required.
6. Recruiter sets the offer expiry date (default: 5 business days from send date) and adds any special conditions (relocation package, remote work agreement reference).
7. Recruiter clicks **Submit for Approval**. System creates an approval workflow task assigned to the HR Director (or delegate) and notifies them by email.
8. HR Admin / HR Director reviews the offer details in the approval queue, verifies compensation compliance, and clicks **Approve Offer**.
9. System generates the offer letter PDF by merging the template with the approved data using a PDF generation service (PDFKit/WeasyPrint).
10. System stores the PDF in S3 (`offers/{jobId}/{candidateId}/{offerId}.pdf`) with server-side encryption.
11. System calls the DocuSign eSignature API to create an envelope: uploads the PDF, sets the candidate as the sole signer, places signature/initial/date fields at defined anchor positions.
12. DocuSign sends an email to the candidate with the subject "Your Offer from [Company Name] – Action Required."
13. Candidate opens the email, clicks **Review and Sign**, views the offer letter in the DocuSign UI, and digitally signs it.
14. DocuSign sends a `envelope-completed` webhook to the platform. System updates the Offer record status to `ACCEPTED` and notifies the Recruiter.
15. System automatically transitions the candidate to the "Offer Accepted" pipeline stage and triggers the background check initiation workflow (UC-07).

**Alternative Flows:**

- **AF-1 (Candidate Negotiates Terms):** At step 13, candidate clicks **Decline to Sign** and sends a counter-proposal via the candidate portal. System notifies the Recruiter with the counter-proposal details. Recruiter reviews, consults Hiring Manager, and either re-generates the offer with revised terms (loop back to step 4) or declines negotiation.
- **AF-2 (Offer Expires Without Response):** At the offer expiry date, if the DocuSign envelope status is still `SENT`, system marks the Offer as `EXPIRED`, notifies the Recruiter, and moves the candidate back to the "On Hold" stage.
- **AF-3 (Verbal Offer First):** Recruiter records a verbal offer in the system before generating the formal letter. Verbal offer details are logged with a timestamp for audit purposes.

**Exception Flows:**

- **EF-1 (DocuSign API Failure):** At step 11, if the DocuSign API returns an error, system queues the send for retry (3 attempts, 10-minute intervals). If all retries fail, Recruiter is notified to send the offer manually and upload the signed copy.
- **EF-2 (Compensation Exceeds Band — Override Required):** At step 5, if the entered salary exceeds the approved band, the system blocks progression. Recruiter must request an exception from HR Admin, who can approve an out-of-band offer with a documented justification.
- **EF-3 (Template Field Mismatch):** At step 9, if required template variables are unpopulated (e.g., equity grant details are missing for a role that requires them), system displays an error listing the missing fields and blocks PDF generation.

**Business Rules:**

- BR-1: Every offer letter must be reviewed and approved by an HR Director or delegate before being sent to the candidate.
- BR-2: Offer letters may not be sent more than 30 calendar days before the proposed start date.
- BR-3: All offer negotiations and counter-proposals must be recorded in the system; verbal agreements without a system record are not binding.
- BR-4: Signed offer letters (completed DocuSign envelopes) are retained for 7 years per employment law requirements.
- BR-5: If a candidate declines an offer, the system prompts the Recruiter to record a decline reason for reporting purposes.

---

## UC-07: Initiate Background Check

### UC-07: Initiate Background Check

| Field | Description |
|---|---|
| **Use Case ID** | UC-07 |
| **Name** | Initiate Background Check |
| **Actor(s)** | Primary: Recruiter; Secondary: System, Checkr (Background Check Provider), Candidate, HR Admin |
| **Trigger** | Candidate accepts the offer letter (UC-06 post-condition) OR Recruiter manually clicks **Initiate Background Check** from the candidate profile |
| **Pre-conditions** | 1. Candidate has a signed offer letter (Offer status = `ACCEPTED`). 2. Checkr API credentials are configured. 3. Background check package for the job role is defined (e.g., "Standard Criminal + Employment Verification"). |
| **Post-conditions** | 1. A background check record is created in the system. 2. Candidate receives an email invitation from Checkr to provide consent and additional details. 3. Recruiter and HR Admin receive notifications of initiation and eventual results. 4. If check clears, system transitions candidate to "Cleared for Onboarding" stage. |
| **Priority** | High |
| **Frequency** | 1 per hired candidate; ~20–30 per month |

**Main Success Scenario:**

1. System (or Recruiter) triggers background check initiation. System calls the Checkr API's `POST /v1/invitations` endpoint with the candidate's name, email, date of birth, and the predefined check package ID.
2. Checkr creates a candidate record and sends a background check consent email to the candidate with a Checkr-hosted link.
3. System creates a `BackgroundCheck` record with status `INVITATION_SENT`, stores the Checkr `invitationId` and `candidateId`, and updates the ATS pipeline stage to "Background Check in Progress."
4. Recruiter and HR Admin receive a notification confirming that the background check has been initiated.
5. Candidate receives the Checkr email, clicks the link, and is guided through Checkr's consent and information collection form (SSN, address history, authorization signature).
6. Checkr begins processing the background check package (criminal record search, employment verification, education verification) based on the selected package.
7. System polls the Checkr API every 4 hours (via a scheduled worker) to check report status updates.
8. Checkr sends a `report.completed` webhook to the platform's Checkr webhook endpoint when the report is ready.
9. System receives the webhook, fetches the full report summary from `GET /v1/reports/{reportId}`, and updates the `BackgroundCheck` record with the `status` (CLEAR / CONSIDER / DISPUTE) and `completedAt`.
10. If status = `CLEAR`: System transitions the candidate to "Cleared for Onboarding," notifies Recruiter and HR Admin, and triggers the HRIS onboarding record creation workflow.
11. If status = `CONSIDER`: System notifies HR Admin with the report details. HR Admin reviews and decides to proceed or initiate adverse action. Recruiter is notified of the outcome.
12. HR Admin makes the final decision; outcome is recorded in the system with a reason.

**Alternative Flows:**

- **AF-1 (Candidate Does Not Complete Consent Within 5 Days):** System sends reminder emails at 2 days and 4 days. At 5 days, Recruiter is notified and can extend the deadline or withdraw the check invitation. If withdrawn, the offer may be rescinded per HR policy.
- **AF-2 (Recruiter Selects Different Check Package):** Recruiter can override the default package (e.g., add "MVR – Motor Vehicle Record" for a driver role or "Credit Check" for a finance role). Override is logged and requires HR Admin acknowledgment.
- **AF-3 (International Candidate):** Checkr routes to an international background check partner. Additional processing time (10–15 business days) is communicated to the Recruiter; the standard SLA timers are extended accordingly.

**Exception Flows:**

- **EF-1 (Checkr API Error on Initiation):** At step 1, if Checkr returns a 4xx or 5xx error, system retries once after 5 minutes. If the retry fails, Recruiter is notified to initiate the check manually via the Checkr portal and record the `reportId` in the system.
- **EF-2 (Webhook Not Received — Report Stale):** At step 8, if no webhook is received within 15 business days, system sends an alert to the Recruiter and HR Admin and flags the background check as `STALE`. System resumes polling on an hourly basis.
- **EF-3 (CONSIDER Result — Adverse Action Required):** At step 11, if HR Admin decides not to hire, system triggers an adverse action workflow: candidate is notified per the FCRA / applicable law requirements, including a pre-adverse action notice (5-day waiting period) and the Checkr dispute process information.

**Business Rules:**

- BR-1: Background checks must not begin before the candidate has signed the offer letter (consent via DocuSign is not a substitute for Checkr's separate FCRA-compliant consent).
- BR-2: Only HR Admin can make the final hire/no-hire decision based on a `CONSIDER` background check result; Recruiters cannot make this determination.
- BR-3: Background check data (report details) is stored in the system for 7 years but is accessible only to HR Admin and Recruiters with elevated permissions.
- BR-4: The platform never stores the candidate's full SSN; it is transmitted directly to Checkr's API over TLS and not persisted locally.
- BR-5: All adverse action communications must comply with the Fair Credit Reporting Act (FCRA) in the US and equivalent local laws in other jurisdictions.

---

## UC-08: View Diversity Analytics

### UC-08: View Diversity Analytics

| Field | Description |
|---|---|
| **Use Case ID** | UC-08 |
| **Name** | View Diversity Analytics |
| **Actor(s)** | Primary: HR Admin; Secondary: Executive / CHRO, Recruiter (limited view) |
| **Trigger** | HR Admin navigates to **Analytics → Diversity & Inclusion Dashboard** |
| **Pre-conditions** | 1. HR Admin has the `analytics:diversity:read` permission. 2. At least 30 days of application data exists (to protect individual privacy; counts below 5 are suppressed). 3. Voluntary EEO/diversity survey responses are collected from candidates during the application process. |
| **Post-conditions** | 1. HR Admin views diversity breakdown at each pipeline stage for the selected time period and filters. 2. HR Admin can export the report as CSV or PDF. 3. Export event is logged in the audit trail. |
| **Priority** | Medium |
| **Frequency** | Monthly by HR Admin; quarterly by CHRO; ad-hoc during board reporting cycles |

**Main Success Scenario:**

1. HR Admin navigates to **Analytics → Diversity & Inclusion** from the main navigation.
2. System renders the dashboard with default filters: current quarter, all departments, all job families, all pipeline stages.
3. HR Admin views the **Representation Funnel Chart**: a horizontal funnel showing the percentage of candidates identifying as each gender identity (Male, Female, Non-binary, Prefer not to say) and each ethnicity category (White, Black/African American, Hispanic/Latino, Asian, Pacific Islander, American Indian, Two or More Races, Prefer not to say) at each pipeline stage: Applied → Screened → Interviewed → Offered → Hired.
4. HR Admin inspects the **Drop-off Analysis**: for each demographic group, the system shows the attrition rate between consecutive stages (e.g., "Hispanic/Latino candidates have a 42% drop-off rate between Screened and Interviewed vs. 28% overall average").
5. HR Admin views the **Source Diversity Panel**: which sourcing channels (LinkedIn, Indeed, Glassdoor, employee referral, direct) contribute candidates from underrepresented groups and at what conversion rates.
6. HR Admin applies filters: Department = "Engineering", Date Range = "Last 6 months". Dashboard re-renders with filtered data.
7. HR Admin views the **Time-to-Hire by Demographic** chart to detect potential bias in processing speed across groups.
8. HR Admin clicks on a data point (e.g., "Asian Female → Technical Interview stage") to drill down to anonymised aggregated statistics. Individual candidate identities are never shown in the analytics view.
9. HR Admin clicks **Export Report**, selects format (CSV or PDF), and clicks **Generate**. System queues the report generation job.
10. System generates the report (typically within 30 seconds), stores it in S3, and sends the HR Admin an email with a time-limited download link (valid 24 hours).
11. HR Admin downloads and shares the report with the CHRO or external DE&I consultants as needed.

**Alternative Flows:**

- **AF-1 (CHRO Views Executive Dashboard):** The CHRO accesses a simplified, read-only version of the diversity dashboard showing company-wide KPIs only (no drill-down). The CHRO cannot export raw data; they can only export the executive summary PDF.
- **AF-2 (Insufficient Data — Privacy Suppression):** At step 3, if a demographic group has fewer than 5 individuals in a pipeline stage, the cell is displayed as "<5" rather than the exact number, and the drop-off rate for that group is not calculated. A tooltip explains the suppression policy.
- **AF-3 (Custom Demographic Groupings):** HR Admin can configure custom groupings (e.g., aggregate "Non-binary" and "Prefer not to say" into "Other/Undisclosed") for reporting alignment with local regulatory categories.

**Exception Flows:**

- **EF-1 (Export Generation Timeout):** At step 9, if the report generation job exceeds 5 minutes (e.g., large date range with millions of records), system notifies the HR Admin and falls back to an asynchronous generation with email delivery. The HR Admin can check the "My Reports" section for the download link.
- **EF-2 (No EEO Survey Data):** If fewer than 20% of candidates have completed the voluntary EEO survey, system displays a prominent banner warning that diversity metrics may not be statistically representative and recommends promoting voluntary survey completion on the application form.
- **EF-3 (Permission Denial — Recruiter Access):** A Recruiter attempts to access the full diversity dashboard. System shows only an aggregated, non-demographic funnel view with no individual group breakdowns.

**Business Rules:**

- BR-1: EEO/diversity survey data is always collected on a voluntary basis. Non-completion must not affect application status or AI score.
- BR-2: Individual candidate demographic data is never surfaced in the ATS pipeline view; it is only accessible in aggregate analytics reports with a minimum cell size of 5.
- BR-3: Diversity data exports are audited; every export event is logged with the exporter's user ID, timestamp, filters applied, and intended use (if provided).
- BR-4: Diversity analytics are available only to HR Admin, CHRO, and users with an explicit `analytics:diversity:read` grant; it is not available to Recruiters or Hiring Managers by default.
- BR-5: The platform's diversity data model follows EEOC reporting categories as the default, with the ability to add custom categories for jurisdictions outside the US.
- BR-6: All demographic data is stored separately from the main candidate profile in a segregated table with column-level encryption and access controls.
