# System Sequence Diagrams — Job Board and Recruitment Platform

This document captures the four most critical end-to-end flows in the platform using UML sequence diagrams. Each diagram traces every network hop, service call, and asynchronous event so that engineers can reason about latency budgets, failure modes, and contract boundaries before writing a single line of code.

---

## 1. Job Posting and Distribution

A recruiter drafts a job, routes it through an approval workflow, and the system automatically syndicates the approved posting to external job boards. The flow enforces a two-step gate: first, an internal HR admin must approve the content; only then does the Integration Service fan out to LinkedIn, Indeed, and any other configured boards.

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter
    participant APIGW as API Gateway
    participant JobSvc as Job Service
    participant ApprovalSvc as Approval Service
    participant IntegrationSvc as Integration Service
    participant LinkedIn as LinkedIn API
    participant Indeed as Indeed API
    participant NotifSvc as Notification Service

    Recruiter->>APIGW: POST /jobs (draft payload, JWT)
    APIGW->>APIGW: Validate JWT, enforce rate limit
    APIGW->>JobSvc: createJob(recruiterId, draftPayload)
    JobSvc->>JobSvc: Validate required fields (title, description, location, salary range)
    JobSvc->>JobSvc: Persist job record (status=DRAFT, version=1)
    JobSvc-->>APIGW: 201 Created {jobId, status: DRAFT}
    APIGW-->>Recruiter: 201 Created {jobId, status: DRAFT}

    Recruiter->>APIGW: PATCH /jobs/{jobId}/submit (JWT)
    APIGW->>JobSvc: submitForApproval(jobId, recruiterId)
    JobSvc->>JobSvc: Transition status DRAFT → PENDING_APPROVAL
    JobSvc->>ApprovalSvc: createApprovalRequest(jobId, approvalType=JOB_POST)
    ApprovalSvc->>ApprovalSvc: Assign to HR Admin queue, set SLA = 24 h
    ApprovalSvc-->>JobSvc: {approvalRequestId, assignedTo: hr-admin@company.com}
    JobSvc->>NotifSvc: publishEvent(JOB_PENDING_APPROVAL, {jobId, approvalRequestId})
    NotifSvc->>NotifSvc: Render email template APPROVAL_REQUIRED
    NotifSvc-->>Recruiter: Email — "Job submitted for approval"
    NotifSvc-->>ApprovalSvc: Email to HR Admin — "New job awaiting approval"
    JobSvc-->>APIGW: 200 OK {status: PENDING_APPROVAL}
    APIGW-->>Recruiter: 200 OK {status: PENDING_APPROVAL}

    Note over ApprovalSvc: HR Admin reviews job content in dashboard

    ApprovalSvc->>ApprovalSvc: HR Admin POSTs decision=APPROVED with notes
    ApprovalSvc->>JobSvc: approvalDecision(jobId, decision=APPROVED, reviewerId)
    JobSvc->>JobSvc: Transition status PENDING_APPROVAL → PUBLISHED
    JobSvc->>JobSvc: Set publishedAt timestamp, increment version
    JobSvc->>IntegrationSvc: distributeJob(jobId, targets=[LINKEDIN, INDEED])
    IntegrationSvc->>IntegrationSvc: Map job fields to LinkedIn schema
    IntegrationSvc->>LinkedIn: POST /v2/jobPostings (OAuth2 Bearer)
    LinkedIn-->>IntegrationSvc: 201 {linkedinJobId: "urn:li:job:123456"}
    IntegrationSvc->>IntegrationSvc: Map job fields to Indeed schema
    IntegrationSvc->>Indeed: POST /publisher/v2/job-postings (API Key)
    Indeed-->>IntegrationSvc: 200 {indeedJobKey: "abc-def-789"}
    IntegrationSvc->>JobSvc: updateExternalReferences(jobId, [{board: LINKEDIN, externalId: "urn:li:job:123456"}, {board: INDEED, externalId: "abc-def-789"}])
    JobSvc-->>IntegrationSvc: 200 OK
    IntegrationSvc->>NotifSvc: publishEvent(JOB_DISTRIBUTED, {jobId, boards: [LINKEDIN, INDEED]})
    NotifSvc->>NotifSvc: Render email template JOB_LIVE
    NotifSvc-->>Recruiter: Email — "Your job is live on LinkedIn and Indeed"
    IntegrationSvc-->>JobSvc: distributionComplete {results: [{board: LINKEDIN, status: SUCCESS}, {board: INDEED, status: SUCCESS}]}
    JobSvc-->>APIGW: 200 OK {status: PUBLISHED, externalBoards: [...]}
```

---

## 2. Application Submission and AI Screening

A candidate applies for a job. The platform stores the resume in S3, triggers asynchronous AI parsing, scores the parsed profile against the job requirements, and surfaces the result to the recruiter — all without the candidate waiting for the full pipeline.

```mermaid
sequenceDiagram
    autonumber
    actor Candidate
    participant APIGW as API Gateway
    participant AppSvc as Application Service
    participant StorageSvc as Storage Service (S3)
    participant AISvc as AI/ML Service
    participant ATSSvc as ATS Service
    participant NotifSvc as Notification Service

    Candidate->>APIGW: POST /jobs/{jobId}/apply (multipart: resume.pdf, coverLetter, answers, JWT)
    APIGW->>APIGW: Validate JWT, rate-limit (max 5 applications per hour per candidate)
    APIGW->>AppSvc: submitApplication(candidateId, jobId, metadata, files)
    AppSvc->>AppSvc: Check duplicate — has candidate already applied to this jobId?
    AppSvc->>AppSvc: Persist application record (status=SUBMITTED, appliedAt=now())
    AppSvc->>StorageSvc: uploadResume(applicationId, resume.pdf)
    StorageSvc->>StorageSvc: Generate S3 key: resumes/{candidateId}/{applicationId}/resume.pdf
    StorageSvc->>StorageSvc: Store file with server-side AES-256 encryption
    StorageSvc-->>AppSvc: {s3Key, s3Bucket, eTag, sizeBytes}
    AppSvc->>StorageSvc: uploadCoverLetter(applicationId, coverLetter.pdf)
    StorageSvc-->>AppSvc: {s3Key, s3Bucket, eTag}
    AppSvc->>AppSvc: Update application record with document references
    AppSvc->>AISvc: triggerResumeParseAsync(applicationId, s3Key, jobId)
    Note over AISvc: Processing is asynchronous — response is immediate
    AISvc-->>AppSvc: {taskId: "parse-task-uuid", estimatedMs: 8000}
    AppSvc->>ATSSvc: createPipelineEntry(applicationId, jobId, stage=NEW)
    ATSSvc->>ATSSvc: Place application in job pipeline at stage NEW
    ATSSvc-->>AppSvc: {pipelineEntryId}
    AppSvc->>NotifSvc: publishEvent(APPLICATION_RECEIVED, {applicationId, candidateId, jobId})
    NotifSvc-->>Candidate: Email — "Application received for {jobTitle}"
    AppSvc-->>APIGW: 202 Accepted {applicationId, status: SUBMITTED}
    APIGW-->>Candidate: 202 Accepted {applicationId, message: "Application submitted successfully"}

    Note over AISvc: AI/ML Service processes asynchronously

    AISvc->>StorageSvc: getObject(s3Key) — download resume PDF
    StorageSvc-->>AISvc: resume.pdf binary stream
    AISvc->>AISvc: Extract raw text via PDF parser
    AISvc->>AISvc: Run NLP pipeline — tokenise, POS tag, NER
    AISvc->>AISvc: Extract skills (technical + soft) using skill taxonomy
    AISvc->>AISvc: Parse work experience (company, title, duration, responsibilities)
    AISvc->>AISvc: Parse education (institution, degree, field, graduation year)
    AISvc->>AISvc: Retrieve job requirements for jobId
    AISvc->>AISvc: Compute match score (0–100) across skill overlap, experience years, education level
    AISvc->>AppSvc: resumeParsed(applicationId, {skills[], experience[], education[], matchScore, rawText})
    AppSvc->>AppSvc: Store structured profile data, update matchScore on application record
    AppSvc->>ATSSvc: updateScreeningResult(applicationId, matchScore, autoAdvance= matchScore >= 70)
    ATSSvc->>ATSSvc: If matchScore >= 70 → transition stage NEW → SCREENING_PASSED
    ATSSvc->>ATSSvc: If matchScore < 40 → transition stage NEW → AUTO_REJECTED
    ATSSvc-->>AppSvc: {newStage}
    AppSvc->>NotifSvc: publishEvent(APPLICATION_SCREENED, {applicationId, matchScore, newStage})
    NotifSvc->>NotifSvc: If newStage=AUTO_REJECTED → queue candidate rejection email (delay 24 h)
    NotifSvc-->>AppSvc: Event acknowledged
    AppSvc->>NotifSvc: publishEvent(RECRUITER_REVIEW_NEEDED, {recruiterId, applicationId, matchScore})
    NotifSvc-->>AppSvc: Recruiter notified via in-app + email
```

---

## 3. Interview Scheduling with Calendar Sync

The recruiter proposes available time slots, the candidate chooses one, and the system automatically creates calendar events for all participants and provisions a Zoom meeting link — eliminating all manual back-and-forth.

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter
    participant APIGW as API Gateway
    participant InterviewSvc as Interview Service
    participant CalendarSvc as Calendar Service
    participant GCal as Google Calendar API
    participant ZoomAPI as Zoom API
    actor Candidate
    participant NotifSvc as Notification Service

    Recruiter->>APIGW: POST /interviews/propose (applicationId, interviewers[], proposedSlots[], JWT)
    APIGW->>InterviewSvc: proposeInterviewSlots(applicationId, interviewers, slots)
    InterviewSvc->>CalendarSvc: checkAvailability(interviewers[], slots[])
    loop For each interviewer
        CalendarSvc->>GCal: GET /calendars/{email}/freeBusy (timeMin, timeMax, OAuth2)
        GCal-->>CalendarSvc: {busy: [{start, end}]}
    end
    CalendarSvc->>CalendarSvc: Compute intersection of free windows across all interviewers
    CalendarSvc-->>InterviewSvc: {availableSlots: [{start, end, allInterviewersFree: true}]}
    InterviewSvc->>InterviewSvc: Persist interview record (status=SLOTS_PROPOSED, slots=[])
    InterviewSvc->>NotifSvc: publishEvent(INTERVIEW_SLOTS_PROPOSED, {interviewId, candidateId, availableSlots})
    NotifSvc->>NotifSvc: Render slot-selection email with unique self-service link
    NotifSvc-->>Candidate: Email — "Please select an interview time" with slot picker link
    InterviewSvc-->>APIGW: 201 {interviewId, status: SLOTS_PROPOSED, expiresAt: +48h}
    APIGW-->>Recruiter: 201 {interviewId, slotsProposed: 3}

    Note over Candidate: Candidate clicks link, selects preferred slot

    Candidate->>APIGW: POST /interviews/{interviewId}/confirm-slot (selectedSlotId, JWT)
    APIGW->>InterviewSvc: confirmSlot(interviewId, selectedSlotId, candidateId)
    InterviewSvc->>InterviewSvc: Validate slot is still available and within expiry window
    InterviewSvc->>InterviewSvc: Transition status SLOTS_PROPOSED → SCHEDULED
    InterviewSvc->>CalendarSvc: createCalendarEvent(interviewId, interviewers[], candidateEmail, slot)
    CalendarSvc->>GCal: POST /calendars/primary/events (summary, attendees, start, end, conferenceData)
    GCal-->>CalendarSvc: {eventId, htmlLink, conferenceData: {hangoutLink}}
    CalendarSvc->>ZoomAPI: POST /v2/users/me/meetings (topic, start_time, duration, agenda, JWT)
    ZoomAPI-->>CalendarSvc: {meetingId, joinUrl, password, hostUrl}
    CalendarSvc->>GCal: PATCH /calendars/primary/events/{eventId} (add Zoom link to description)
    GCal-->>CalendarSvc: 200 OK updated event
    CalendarSvc-->>InterviewSvc: {googleEventId, zoomMeetingId, joinUrl, hostUrl}
    InterviewSvc->>InterviewSvc: Persist calendar references on interview record
    InterviewSvc->>NotifSvc: publishEvent(INTERVIEW_SCHEDULED, {interviewId, slot, joinUrl, attendees[]})
    NotifSvc->>NotifSvc: Render confirmation email with calendar attachment (.ics)
    NotifSvc-->>Candidate: Email — "Interview confirmed: {date}, Zoom link: {joinUrl}"
    NotifSvc-->>Recruiter: Email — "Interview scheduled with {candidateName}"
    loop For each interviewer
        NotifSvc-->>InterviewSvc: Email interviewer with agenda, candidate resume link, host Zoom URL
    end
    InterviewSvc->>NotifSvc: scheduleReminder(interviewId, T-24h, T-1h, audience=[CANDIDATE, INTERVIEWERS])
    NotifSvc-->>InterviewSvc: Reminders queued
    InterviewSvc-->>APIGW: 200 OK {status: SCHEDULED, zoomJoinUrl, googleEventLink}
    APIGW-->>Candidate: 200 OK {message: "Interview confirmed", details: {...}}
```

---

## 4. Offer Letter Generation and Signing

The recruiter generates a personalised offer letter, it travels through a director-level approval workflow, and is dispatched via DocuSign for electronic signing. Upon completion, the HRIS is automatically notified to begin onboarding.

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter
    participant APIGW as API Gateway
    participant OfferSvc as Offer Service
    participant ApprovalSvc as Approval Service
    participant DocuSign as DocuSign API
    actor Candidate
    participant NotifSvc as Notification Service
    participant HRISSvc as HRIS Service

    Recruiter->>APIGW: POST /offers (applicationId, salary, startDate, equity, benefits[], JWT)
    APIGW->>OfferSvc: generateOffer(applicationId, offerParams)
    OfferSvc->>OfferSvc: Fetch job, candidate, and company data
    OfferSvc->>OfferSvc: Select offer letter template by jobLevel (e.g., IC3, MANAGER)
    OfferSvc->>OfferSvc: Merge template with offer params → rendered HTML/PDF
    OfferSvc->>OfferSvc: Persist offer record (status=DRAFT, version=1)
    OfferSvc-->>APIGW: 201 {offerId, status: DRAFT, previewUrl}
    APIGW-->>Recruiter: 201 {offerId, previewUrl}

    Recruiter->>APIGW: POST /offers/{offerId}/submit (JWT)
    APIGW->>OfferSvc: submitOfferForApproval(offerId, recruiterId)
    OfferSvc->>OfferSvc: Validate offer completeness (all required fields present)
    OfferSvc->>ApprovalSvc: createApprovalRequest(offerId, approvalType=OFFER_LETTER, requiredLevel=HR_DIRECTOR)
    ApprovalSvc->>ApprovalSvc: Identify HR Director approver via RBAC policy
    ApprovalSvc->>ApprovalSvc: Set SLA = 8 business hours
    ApprovalSvc-->>OfferSvc: {approvalRequestId, assignedTo: hr-director@company.com}
    OfferSvc->>NotifSvc: publishEvent(OFFER_PENDING_APPROVAL, {offerId, approvalRequestId})
    NotifSvc-->>Recruiter: Email — "Offer submitted for approval"
    NotifSvc-->>ApprovalSvc: Email to HR Director — "Offer requires your approval"
    OfferSvc-->>APIGW: 200 OK {status: PENDING_APPROVAL}
    APIGW-->>Recruiter: 200 OK {status: PENDING_APPROVAL}

    Note over ApprovalSvc: HR Director reviews compensation against band policy

    ApprovalSvc->>ApprovalSvc: HR Director approves with optional comp adjustments
    ApprovalSvc->>OfferSvc: approvalDecision(offerId, decision=APPROVED, adjustments={salary: 95000})
    OfferSvc->>OfferSvc: Apply any compensation adjustments, re-render PDF
    OfferSvc->>OfferSvc: Transition status PENDING_APPROVAL → APPROVED
    OfferSvc->>DocuSign: createEnvelope(document=offerPDF, signers=[{email: candidate, role: CANDIDATE}, {email: hr-director, role: COMPANY}])
    DocuSign-->>OfferSvc: {envelopeId, status: SENT, signingUrl: candidateUrl}
    OfferSvc->>OfferSvc: Persist envelopeId on offer record, transition status → SENT_TO_CANDIDATE
    OfferSvc->>NotifSvc: publishEvent(OFFER_SENT, {offerId, candidateId, envelopeId})
    NotifSvc->>NotifSvc: Render offer delivery email with personalised signing link
    NotifSvc-->>Candidate: Email — "Your offer letter is ready to sign"
    OfferSvc-->>APIGW: 200 OK {status: SENT_TO_CANDIDATE}
    APIGW-->>Recruiter: 200 OK {status: SENT_TO_CANDIDATE}

    Note over Candidate: Candidate reviews and signs the offer letter in DocuSign

    DocuSign->>OfferSvc: Webhook POST /webhooks/docusign (envelopeId, event=RECIPIENT_COMPLETED, signerRole=CANDIDATE)
    OfferSvc->>OfferSvc: Validate webhook HMAC signature
    OfferSvc->>OfferSvc: Transition status SENT_TO_CANDIDATE → CANDIDATE_SIGNED
    OfferSvc->>NotifSvc: publishEvent(CANDIDATE_SIGNED, {offerId, candidateId})
    NotifSvc-->>Recruiter: Email + in-app — "Candidate has signed the offer"
    Note over DocuSign: HR Director counter-signs via DocuSign

    DocuSign->>OfferSvc: Webhook POST /webhooks/docusign (envelopeId, event=ENVELOPE_COMPLETED)
    OfferSvc->>DocuSign: GET /envelopes/{envelopeId}/documents (download signed PDF)
    DocuSign-->>OfferSvc: signedOfferPDF binary
    OfferSvc->>OfferSvc: Store signed PDF in S3, update offer record with signedDocumentUrl
    OfferSvc->>OfferSvc: Transition status CANDIDATE_SIGNED → FULLY_EXECUTED
    OfferSvc->>HRISSvc: triggerOnboarding(candidateId, offerId, {startDate, jobTitle, department, salary})
    HRISSvc->>HRISSvc: Create employee record in HRIS (status=PRE_HIRE)
    HRISSvc->>HRISSvc: Trigger IT provisioning workflow (laptop, email, accounts)
    HRISSvc-->>OfferSvc: {employeeId, onboardingTasksCreated: 12}
    OfferSvc->>NotifSvc: publishEvent(OFFER_FULLY_EXECUTED, {offerId, candidateId, employeeId})
    NotifSvc-->>Candidate: Email — "Welcome! Here is your onboarding information"
    NotifSvc-->>Recruiter: Email — "Offer fully executed. Onboarding initiated."
    OfferSvc-->>APIGW: 200 OK {status: FULLY_EXECUTED, employeeId}
```
