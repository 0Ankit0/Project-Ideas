# Sequence Diagrams — Job Board and Recruitment Platform

## Overview

These four sequence diagrams cover the most technically complex workflows in the platform: AI-powered resume parsing, pipeline stage transitions with notification propagation, third-party background check integration, and calendar-aware interview slot booking with conflict detection.

---

## 1. AI Resume Parsing Flow

Triggered when a candidate submits an application. The resume file is stored durably in S3 before any parsing begins. The parsing pipeline is asynchronous — the application record is created immediately with status `RECEIVED` and enriched once the AI pipeline completes.

```mermaid
sequenceDiagram
    autonumber
    actor Candidate
    participant ApplicationService
    participant S3BucketService
    participant AIMLService
    participant TextExtractor
    participant NLPParser
    participant SkillMatcher
    participant ApplicationDB

    Candidate->>ApplicationService: POST /applications {jobId, candidateId, resumeFile, coverLetterFile}
    ApplicationService->>ApplicationService: validate payload (file type: PDF/DOCX, max 5MB)

    ApplicationService->>ApplicationDB: INSERT application {status=RECEIVED, aiScore=null}
    ApplicationDB-->>ApplicationService: applicationId

    ApplicationService->>S3BucketService: uploadResume(file, candidateId, applicationId)
    S3BucketService->>S3BucketService: generate s3Key = resumes/{candidateId}/{applicationId}/{uuid}.{ext}
    S3BucketService-->>ApplicationService: {s3Key, presignedUrl, eTag}

    ApplicationService->>ApplicationDB: UPDATE resume SET s3Key, fileType, fileSizeBytes
    ApplicationService-->>Candidate: 202 Accepted {applicationId, status: RECEIVED}

    Note over ApplicationService,AIMLService: Async pipeline begins via internal event queue

    ApplicationService->>AIMLService: POST /parse-resume {applicationId, s3Key, jobId}
    AIMLService->>S3BucketService: getObject(s3Key)
    S3BucketService-->>AIMLService: raw file bytes

    AIMLService->>TextExtractor: extract(fileBytes, fileType)
    alt fileType == PDF
        TextExtractor->>TextExtractor: PDFBox.extractText(fileBytes)
    else fileType == DOCX
        TextExtractor->>TextExtractor: Apache POI.extractText(fileBytes)
    end
    TextExtractor-->>AIMLService: plainText (cleaned, whitespace-normalised)

    AIMLService->>NLPParser: parseEntities(plainText)
    NLPParser->>NLPParser: run named entity recognition (spaCy / custom model)
    NLPParser->>NLPParser: extract work experiences (company, title, dates, bullets)
    NLPParser->>NLPParser: extract education (institution, degree, field, year)
    NLPParser->>NLPParser: extract certifications and licences
    NLPParser->>NLPParser: extract languages spoken
    NLPParser->>NLPParser: extract raw skill mentions
    NLPParser-->>AIMLService: ParsedEntities {skills[], workExperiences[], education[], certifications[]}

    AIMLService->>AIMLService: inferSeniorityLevel(workExperiences)
    AIMLService->>AIMLService: computeTotalYearsExperience(workExperiences)

    AIMLService->>SkillMatcher: matchSkills(rawSkills, jobId)
    SkillMatcher->>ApplicationDB: SELECT requirements WHERE jobId = :jobId
    ApplicationDB-->>SkillMatcher: List<JobRequirement> {skill, level, isMandatory, yearsRequired}
    SkillMatcher->>SkillMatcher: normaliseSkills using taxonomy (aliases: "JS" → "JavaScript")
    SkillMatcher->>SkillMatcher: computeMandatorySkillCoverage()
    SkillMatcher->>SkillMatcher: computeOptionalSkillBonus()
    SkillMatcher->>SkillMatcher: applyExperienceWeighting()
    SkillMatcher->>SkillMatcher: applyEducationBonus()
    SkillMatcher-->>AIMLService: {matchScore: 0.87, skillMatchBreakdown: {Java: 1.0, Spring: 0.9, ...}}

    AIMLService->>ApplicationDB: INSERT ai_parsing_results {applicationId, resumeId, skills, workExperiences, matchScore, modelVersion}
    ApplicationDB-->>AIMLService: resultId

    AIMLService->>ApplicationDB: UPDATE applications SET aiScore=0.87, aiExtractedSkills=[...], isParsed=true WHERE applicationId=:id
    ApplicationDB-->>AIMLService: 1 row updated

    AIMLService-->>ApplicationService: {resultId, aiScore: 0.87, status: PARSED}

    ApplicationService->>ApplicationDB: UPDATE applications SET status=SCREENING WHERE applicationId=:id AND aiScore >= autoScreenThreshold
    Note over ApplicationService,ApplicationDB: If score < threshold, status remains RECEIVED for manual review
```

---

## 2. Pipeline Stage Transition with Notifications

Triggered when a recruiter moves a candidate from one pipeline stage to the next. The transition is governed by a rule engine that enforces ordering, prerequisite completion (e.g., scorecard submission), and auto-action triggers such as sending templated emails and updating the candidate-facing portal.

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter
    participant ATSService
    participant PipelineRuleEngine
    participant ApplicationDB
    participant EventBus
    participant NotificationService
    participant EmailService
    participant CandidatePortal

    Recruiter->>ATSService: PATCH /applications/{applicationId}/stage {targetStageId, notes}
    ATSService->>ApplicationDB: SELECT application WHERE applicationId = :id
    ApplicationDB-->>ATSService: application {currentStageId, status, candidateId, jobId}

    ATSService->>ApplicationDB: SELECT pipeline stage WHERE stageId = :targetStageId
    ApplicationDB-->>ATSService: targetStage {orderIndex, requiresScorecard, stageType, sendAutoEmail}

    ATSService->>ApplicationDB: SELECT pipeline stage WHERE stageId = :currentStageId
    ApplicationDB-->>ATSService: currentStage {orderIndex, stageType}

    ATSService->>PipelineRuleEngine: validateTransition(application, currentStage, targetStage)

    PipelineRuleEngine->>PipelineRuleEngine: assertTargetStageInSamePipeline()
    PipelineRuleEngine->>PipelineRuleEngine: assertForwardOrAllowedBackwardMove(currentIndex, targetIndex)
    PipelineRuleEngine->>PipelineRuleEngine: assertApplicationNotHiredOrRejected(status)

    alt targetStage.requiresScorecard == true
        PipelineRuleEngine->>ApplicationDB: SELECT feedback WHERE roundId IN (rounds for current stage) AND isSubmitted = true
        ApplicationDB-->>PipelineRuleEngine: submittedFeedbacks[]
        PipelineRuleEngine->>PipelineRuleEngine: assertAllRequiredFeedbackSubmitted(submittedFeedbacks)
    end

    alt validation fails
        PipelineRuleEngine-->>ATSService: ValidationError {code, message}
        ATSService-->>Recruiter: 422 Unprocessable Entity {error}
    else validation passes
        PipelineRuleEngine-->>ATSService: TransitionApproved

        ATSService->>ApplicationDB: BEGIN TRANSACTION
        ATSService->>ApplicationDB: UPDATE applications SET currentStageId=:targetStageId, lastActivityAt=NOW()
        ATSService->>ApplicationDB: INSERT stage_transition_log {applicationId, fromStageId, toStageId, actorId, timestamp, notes}
        ATSService->>ApplicationDB: COMMIT TRANSACTION
        ApplicationDB-->>ATSService: success

        ATSService->>EventBus: publish(stage.changed, {applicationId, candidateId, jobId, fromStage, toStage, recruiterName})
        EventBus-->>ATSService: eventId (ack)

        ATSService-->>Recruiter: 200 OK {applicationId, newStageId, transitionId}

        Note over EventBus,NotificationService: Async — event consumer picks up stage.changed

        EventBus->>NotificationService: consume(stage.changed, payload)
        NotificationService->>ApplicationDB: SELECT email_template WHERE triggerEvent='stage.changed' AND stageId=:targetStageId AND companyId=:companyId
        ApplicationDB-->>NotificationService: EmailTemplate {subject, bodyHtml, variables}

        NotificationService->>ApplicationDB: SELECT candidate WHERE candidateId = :candidateId
        ApplicationDB-->>NotificationService: candidate {firstName, lastName, email}

        NotificationService->>NotificationService: render(template, {candidateName, jobTitle, stageName, companyName, portalLink})

        NotificationService->>EmailService: sendEmail({to, subject, bodyHtml, bodyText, replyTo})
        EmailService->>EmailService: route via SendGrid / SES
        EmailService-->>NotificationService: {messageId, status: queued}

        NotificationService->>CandidatePortal: PATCH /portal/applications/{applicationId} {stageLabel, stageOrder, updatedAt}
        CandidatePortal-->>NotificationService: 200 OK

        NotificationService->>ApplicationDB: INSERT notification_log {applicationId, candidateId, channel: EMAIL, status: SENT, messageId}
    end
```

---

## 3. Background Check Integration Flow

Initiated by an HR Admin after an offer letter has been approved and sent. The platform integrates with the Checkr API to run criminal, employment, and education verification checks. Candidate consent is collected before any data is transmitted. Checkr delivers results via a signed webhook callback.

```mermaid
sequenceDiagram
    autonumber
    actor HRAdmin
    participant OfferService
    participant BackgroundCheckService
    participant CheckrAPI
    participant CandidatePortalService
    participant NotificationService
    participant OfferDB

    HRAdmin->>OfferService: POST /offers/{offerId}/background-check/initiate
    OfferService->>OfferDB: SELECT offer WHERE offerId = :id
    OfferDB-->>OfferService: offer {status: SENT, candidateId, applicationId, baseSalary}

    OfferService->>OfferService: assertOfferStatus(SENT or ACCEPTED)

    OfferService->>BackgroundCheckService: initiateCheck(offerId, candidateId)
    BackgroundCheckService->>OfferDB: SELECT background_check WHERE offerId = :id AND candidateId = :id
    OfferDB-->>BackgroundCheckService: existingCheck (may be null)

    alt check already exists
        BackgroundCheckService-->>OfferService: 409 Conflict {message: "Background check already initiated"}
        OfferService-->>HRAdmin: 409 Conflict
    else no existing check
        BackgroundCheckService->>OfferDB: INSERT background_check {offerId, candidateId, status: PENDING_CONSENT}
        OfferDB-->>BackgroundCheckService: checkId

        BackgroundCheckService->>CandidatePortalService: POST /portal/consent-request {checkId, candidateId, checkTypes: [CRIMINAL, EMPLOYMENT, EDUCATION]}
        CandidatePortalService->>CandidatePortalService: generate consent form with legal disclosures (FCRA compliance)
        CandidatePortalService-->>BackgroundCheckService: {consentRequestId, consentUrl}

        BackgroundCheckService->>NotificationService: sendConsentRequest(candidateId, consentUrl)
        NotificationService->>NotificationService: render background check consent email
        NotificationService-->>BackgroundCheckService: emailQueued

        BackgroundCheckService-->>OfferService: {checkId, status: PENDING_CONSENT, consentUrl}
        OfferService-->>HRAdmin: 202 Accepted {checkId, message: "Awaiting candidate consent"}
    end

    Note over CandidatePortalService,BackgroundCheckService: Candidate reviews disclosures and submits consent form

    CandidatePortalService->>BackgroundCheckService: POST /checks/{checkId}/consent {candidateId, consentTimestamp, ipAddress}
    BackgroundCheckService->>OfferDB: UPDATE background_check SET candidateConsented=true, consentedAt=NOW(), consentIp=:ip

    BackgroundCheckService->>CheckrAPI: POST /v1/invitations {candidateEmail, packageSlug: "tasker_pro", callbackUrl}
    CheckrAPI-->>BackgroundCheckService: {invitationId, invitationUrl, status: "pending"}

    BackgroundCheckService->>OfferDB: UPDATE background_check SET externalCheckId=:invitationId, status=INITIATED, initiatedAt=NOW()
    BackgroundCheckService-->>CandidatePortalService: {status: INITIATED, message: "Check has been initiated via Checkr"}

    Note over CheckrAPI,BackgroundCheckService: Checkr performs checks asynchronously (1–5 business days)

    CheckrAPI->>BackgroundCheckService: POST /webhooks/checkr {checkId, candidateId, status: "clear", reportId, completedAt}
    BackgroundCheckService->>BackgroundCheckService: verifyWebhookSignature(X-Checkr-Signature, secret)

    alt signature invalid
        BackgroundCheckService-->>CheckrAPI: 401 Unauthorized
    else signature valid
        BackgroundCheckService->>CheckrAPI: GET /v1/reports/{reportId}
        CheckrAPI-->>BackgroundCheckService: {reportUrl, summary, status: "clear", checks: [...]}

        BackgroundCheckService->>OfferDB: UPDATE background_check SET status=COMPLETED, resultSummary=:summary, reportS3Key=:key, completedAt=NOW()

        BackgroundCheckService->>NotificationService: notify(HRAdmin, checkId, result: CLEAR)
        NotificationService->>NotificationService: render "Background Check Complete" email
        NotificationService-->>HRAdmin: email: "Background check returned CLEAR. Offer countersignature is now unblocked."

        BackgroundCheckService-->>CheckrAPI: 200 OK

        alt result == CLEAR
            BackgroundCheckService->>OfferService: unlockCountersignature(offerId)
            OfferService->>OfferDB: UPDATE offers SET backgroundCheckPassed=true
        else result == CONSIDER or ADVERSE
            BackgroundCheckService->>OfferService: flagForHRReview(offerId, reportSummary)
            OfferService->>OfferDB: UPDATE offers SET backgroundCheckStatus=REQUIRES_REVIEW
            OfferService->>NotificationService: notify(HRAdmin, ADVERSE_ACTION_REQUIRED, offerId)
        end
    end
```

---

## 4. Calendar Slot Booking with Conflict Detection

Triggered when a recruiter schedules an interview and proposes time slots to a candidate. The service checks interviewer availability across both Google Calendar and Outlook Calendar, runs conflict detection, presents available slots to the candidate, and upon selection creates calendar events and generates a video conferencing link.

```mermaid
sequenceDiagram
    autonumber
    actor Recruiter
    participant InterviewService
    participant CalendarService
    participant GoogleCalendarAPI
    participant OutlookCalendarAPI
    participant ConflictDetector
    participant VideoLinkGenerator
    participant NotificationService

    Recruiter->>InterviewService: POST /interviews {applicationId, stageId, interviewerIds[], proposedSlots[], durationMinutes, videoProvider}
    InterviewService->>InterviewService: validate interviewerIds, proposedSlots length ≥ 3

    InterviewService->>CalendarService: getInterviewerAvailability(interviewerIds[], proposedSlots[], durationMinutes)

    loop for each interviewerId
        CalendarService->>CalendarService: resolve calendar provider for interviewer (Google or Outlook)

        alt provider == GOOGLE
            CalendarService->>GoogleCalendarAPI: POST /calendars/primary/freebusy {timeMin, timeMax, items: [{id: calendarId}]}
            GoogleCalendarAPI-->>CalendarService: {busy: [{start, end}, ...]}
        else provider == OUTLOOK
            CalendarService->>OutlookCalendarAPI: POST /me/calendar/getSchedule {schedules: [email], startTime, endTime, availabilityViewInterval: 30}
            OutlookCalendarAPI-->>CalendarService: {value: [{scheduleItems: [{status, start, end}]}]}
        end

        CalendarService->>CalendarService: normalise to unified BusyPeriod[] format
    end

    CalendarService-->>InterviewService: Map<interviewerId, BusyPeriod[]>

    InterviewService->>ConflictDetector: detectConflicts(proposedSlots[], interviewerBusyPeriods, durationMinutes)

    loop for each proposedSlot
        ConflictDetector->>ConflictDetector: expand slot to [start, start+duration]
        ConflictDetector->>ConflictDetector: check overlap with each interviewer's busy periods
        ConflictDetector->>ConflictDetector: check platform-wide buffer (15 min between back-to-back)
        ConflictDetector->>ConflictDetector: check interviewer daily interview limit (max 4/day)

        alt no conflicts for all interviewers
            ConflictDetector->>ConflictDetector: mark slot as AVAILABLE
        else at least one conflict
            ConflictDetector->>ConflictDetector: mark slot as CONFLICT {conflictingInterviewerId, reason}
        end
    end

    ConflictDetector-->>InterviewService: {availableSlots: [...], conflictedSlots: [...]}

    alt zero available slots
        InterviewService-->>Recruiter: 409 Conflict {message: "No proposed slots are available for all interviewers", conflictDetails: [...]}
    else at least one available slot
        InterviewService->>InterviewService: create Interview record {status: AWAITING_CANDIDATE_SELECTION}
        InterviewService->>InterviewService: persist availableSlots with interview

        InterviewService->>NotificationService: sendSlotSelectionEmail(candidateId, availableSlots, selectionUrl, expiresAt)
        NotificationService->>NotificationService: render slot picker email with timezone-aware display
        NotificationService-->>InterviewService: emailQueued

        InterviewService-->>Recruiter: 201 Created {interviewId, availableSlots, status: AWAITING_CANDIDATE_SELECTION}
    end

    Note over InterviewService,NotificationService: Candidate clicks slot selection link in email

    actor Candidate
    Candidate->>InterviewService: POST /interviews/{interviewId}/confirm-slot {selectedSlotId, timezone}
    InterviewService->>InterviewService: assertSlotStillAvailable(selectedSlotId)
    InterviewService->>InterviewService: assertSelectionNotExpired(expiresAt)

    InterviewService->>VideoLinkGenerator: generateLink(interviewId, provider, startTime, durationMinutes, participantEmails[])

    alt provider == ZOOM
        VideoLinkGenerator->>VideoLinkGenerator: Zoom API: POST /users/{userId}/meetings {topic, start_time, duration, settings}
        VideoLinkGenerator-->>InterviewService: {meetingUrl, meetingId, password, dialInNumbers}
    else provider == TEAMS
        VideoLinkGenerator->>VideoLinkGenerator: MS Graph API: POST /me/onlineMeetings {subject, startDateTime, endDateTime, participants}
        VideoLinkGenerator-->>InterviewService: {joinUrl, meetingId, conferenceId}
    end

    InterviewService->>CalendarService: createCalendarEvents(interviewId, selectedSlot, interviewerIds[], candidateEmail, meetingLink)

    loop for each interviewer
        alt provider == GOOGLE
            CalendarService->>GoogleCalendarAPI: POST /calendars/primary/events {summary, start, end, attendees, conferenceData, reminders}
            GoogleCalendarAPI-->>CalendarService: {eventId, htmlLink}
        else provider == OUTLOOK
            CalendarService->>OutlookCalendarAPI: POST /me/events {subject, start, end, attendees, onlineMeeting, body}
            OutlookCalendarAPI-->>CalendarService: {id, webLink}
        end
    end

    CalendarService-->>InterviewService: {calendarEventIds: Map<interviewerId, eventId>}

    InterviewService->>InterviewService: UPDATE interview SET status=SCHEDULED, meetingLink, calendarEventIds, confirmedSlot
    InterviewService->>InterviewService: UPDATE application SET status=INTERVIEW_SCHEDULED

    InterviewService->>NotificationService: sendConfirmations(interviewers[], candidate, interviewDetails)
    NotificationService->>NotificationService: send interviewer calendar invite emails with scorecard link
    NotificationService->>NotificationService: send candidate confirmation email with meeting link, location/dial-in, prep tips
    NotificationService-->>InterviewService: allEmailsQueued

    InterviewService-->>Candidate: 200 OK {interviewId, confirmedSlot, meetingLink, status: SCHEDULED}
```

---

## Notes on Async Boundaries

| Flow | Sync / Async | Mechanism |
|---|---|---|
| Resume upload | Sync (upload), Async (parsing) | Internal event queue / SQS |
| Stage transition | Sync (DB write), Async (notifications) | Kafka `stage.changed` topic |
| Background check initiation | Sync | REST + DB |
| Checkr result delivery | Async (webhook) | Signed HTTPS POST from Checkr |
| Slot confirmation | Sync | REST |
| Calendar event creation | Sync (within request) | Parallel API calls |
