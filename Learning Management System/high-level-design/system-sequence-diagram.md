# System Sequence Diagram - Learning Management System

This document captures the four primary cross-service system sequences that span multiple bounded contexts. Each sequence shows all participating services, the happy path, alternative/error paths, and the audit events emitted at each critical step.

---

## 1. Enrollment Creation Flow

Covers policy evaluation, seat validation, prerequisite checking, and confirmation notification. The `Policy Engine` is the authoritative gate; the `Enrollment Service` never writes without a `APPROVED` policy outcome.

```mermaid
sequenceDiagram
    autonumber
    actor L as Learner
    participant P as Learner Portal
    participant GW as API Gateway
    participant E as Enrollment Service
    participant PE as Policy Engine
    participant CS as Course Service
    participant NS as Notification Service
    participant AL as Audit Log

    L->>P: Click "Enroll" on cohort page
    P->>GW: POST /api/v1/enrollments\n{cohortId, userId, idempotencyKey}
    GW->>GW: Authenticate JWT, extract tenantId + userId
    GW->>E: forward validated request

    E->>AL: ENROLLMENT_REQUESTED {userId, cohortId, requestId}

    E->>PE: EvaluateEnrollmentPolicy\n{userId, cohortId, tenantId}
    PE->>CS: GetCohortDetails(cohortId)
    CS-->>PE: {seatCapacity, seatsUsed, startsAt, endsAt,\n prerequisiteCourseIds[], enrollmentPolicy}

    alt cohort is full (seatsUsed >= seatCapacity)
        PE-->>E: DENIED {reason: SEAT_LIMIT_EXCEEDED}
        E->>AL: ENROLLMENT_DENIED {reason: SEAT_LIMIT_EXCEEDED}
        E-->>GW: 409 Conflict {code: SEAT_LIMIT_EXCEEDED}
        GW-->>P: 409 + user-friendly message
        P-->>L: "This cohort is full. Join the waitlist?"
    else enrollment window closed
        PE-->>E: DENIED {reason: ENROLLMENT_WINDOW_CLOSED}
        E->>AL: ENROLLMENT_DENIED {reason: ENROLLMENT_WINDOW_CLOSED}
        E-->>GW: 422 Unprocessable {code: ENROLLMENT_WINDOW_CLOSED}
        GW-->>P: 422 + message
        P-->>L: "Enrollment for this cohort has closed."
    else prerequisites not satisfied
        PE->>CS: GetLearnerCompletions(userId, prerequisiteCourseIds[])
        CS-->>PE: {completedCourseIds[]}
        PE->>PE: diff(prerequisiteCourseIds, completedCourseIds) → missingIds[]
        PE-->>E: DENIED {reason: PREREQUISITES_NOT_MET, missingIds[]}
        E->>AL: ENROLLMENT_DENIED {reason: PREREQUISITES_NOT_MET, missingIds}
        E-->>GW: 422 {code: PREREQUISITES_NOT_MET, missingCourses[]}
        GW-->>P: 422 + prerequisite list
        P-->>L: "Complete these courses first: ..."
    else idempotency key already used
        E->>E: lookup(idempotencyKey) → existing enrollmentId
        E-->>GW: 200 OK {enrollmentId, status: ACTIVE} (replay)
        GW-->>P: 200 (replayed)
        P-->>L: "You are already enrolled."
    else all checks pass
        PE-->>E: APPROVED
        E->>E: INSERT enrollment {status: ACTIVE}
        E->>CS: IncrementSeatCount(cohortId)
        E->>AL: ENROLLMENT_CREATED {enrollmentId, userId, cohortId}
        E->>NS: PublishEvent(ENROLLMENT_CONFIRMED)\n{userId, cohortId, startsAt}
        NS-->>L: Email/push: "You're enrolled! Course starts {startsAt}"
        E-->>GW: 201 Created {enrollmentId, status: ACTIVE}
        GW-->>P: 201
        P-->>L: Enrollment confirmation page
    end
```

---

## 2. Assessment Submission and Auto-Grading Flow

Covers idempotent submission, timer enforcement, answer persistence, auto-grading dispatch, and score publication. The submission endpoint is idempotent on `attemptId`; re-submitting the same `attemptId` replays the last acknowledged response.

```mermaid
sequenceDiagram
    autonumber
    actor L as Learner
    participant P as Learner Portal
    participant GW as API Gateway
    participant AS as Assessment Service
    participant TM as Timer Service
    participant GS as Grading Service
    participant PS as Progress Service
    participant EB as Event Bus
    participant AL as Audit Log

    L->>P: Click "Submit Assessment"
    P->>GW: POST /api/v1/attempts/{attemptId}/submit\n{answers[], submittedAt, clientChecksum}
    GW->>AS: forward

    AS->>AS: load attempt by attemptId
    alt attemptId not found or not owned by userId
        AS-->>GW: 404 Not Found
        GW-->>P: 404
        P-->>L: "Attempt not found."
    else attempt already in SUBMITTED/GRADED state (idempotent replay)
        AS-->>GW: 200 OK {attemptId, status, score} (replay)
        GW-->>P: 200 replayed
        P-->>L: Previous submission result shown
    else attempt is EXPIRED (timer exceeded)
        TM->>AS: TimerExpired event already processed
        AS-->>GW: 422 {code: ATTEMPT_EXPIRED}
        GW-->>P: 422
        P-->>L: "Time expired. Saved answers were auto-submitted."
    else submission is valid
        AS->>TM: CancelTimer(attemptId)
        AS->>AS: persist answers, set status → SUBMITTED
        AS->>AL: ATTEMPT_SUBMITTED {attemptId, userId, assessmentId, submittedAt}

        AS->>AS: determine gradingMode (AUTO | MANUAL | HYBRID)

        alt gradingMode = AUTO
            AS->>GS: AutoGrade(attemptId, answers[], answerKey)
            GS->>GS: score each question, sum weighted marks
            GS->>GS: persist GradeRecord {attemptId, score, breakdown[]}
            GS->>AL: ATTEMPT_AUTO_GRADED {attemptId, score, passedThreshold}
            GS->>EB: publish(GRADE_RECORDED) {attemptId, score, passed}
            EB->>PS: onGradeRecorded → recalculate course progress
            PS->>PS: update ProgressRecord {percentComplete, completionStatus}
            PS->>EB: publish(PROGRESS_UPDATED) {enrollmentId, percentComplete}
            GS-->>AS: {score, passed, feedback[]}
            AS-->>GW: 200 {attemptId, status: GRADED, score, passed}
            GW-->>P: 200
            P-->>L: Score displayed immediately
        else gradingMode = MANUAL or HYBRID
            AS->>GS: EnqueueManualReview(attemptId)
            GS->>AL: MANUAL_REVIEW_QUEUED {attemptId, assignedReviewerId}
            AS-->>GW: 202 Accepted {attemptId, status: PENDING_REVIEW,\n estimatedReviewHours: 48}
            GW-->>P: 202
            P-->>L: "Submitted. Your instructor will review within 48 hours."
        end
    end
```

---

## 3. Manual Grading and Grade Release Flow

Covers reviewer assignment, rubric scoring, grade override, approval gate, and grade release with full audit trail. All mutations to a `GradeRecord` are append-only revisions; no in-place updates.

```mermaid
sequenceDiagram
    autonumber
    actor R as Reviewer (Instructor)
    participant SW as Staff Workspace
    participant GW as API Gateway
    participant GS as Grading Service
    participant AS as Assessment Service
    participant PS as Progress Service
    participant NS as Notification Service
    participant AL as Audit Log
    participant EB as Event Bus

    R->>SW: Open review queue
    SW->>GW: GET /api/v1/grading/queue?reviewerId={id}
    GW->>GS: GetAssignedAttempts(reviewerId)
    GS-->>SW: [{attemptId, learnerName, submittedAt, rubricId}]

    R->>SW: Select attempt, open rubric
    SW->>GW: GET /api/v1/attempts/{attemptId}/rubric
    GW->>GS: GetRubricWithAnswers(attemptId)
    GS-->>SW: {rubric{}, answers[], autoGradedItems[]}

    R->>SW: Score each rubric criterion, add feedback
    SW->>GW: PUT /api/v1/grading/attempts/{attemptId}\n{criteriaScores[], feedback, reviewerNote}
    GW->>GS: SaveDraftGrade(attemptId, reviewerId, criteriaScores[], feedback)

    alt attempt locked by another reviewer
        GS-->>GW: 409 {code: ATTEMPT_LOCKED, lockedBy}
        GW-->>SW: 409
        SW-->>R: "Being reviewed by {name}. You can observe only."
    else score falls below minimum justified threshold
        GS->>GS: validate(criteriaScores) → validationErrors[]
        GS-->>GW: 422 {code: SCORE_VALIDATION_FAILED, errors[]}
        GW-->>SW: 422
        SW-->>R: Inline rubric validation errors shown
    else valid draft saved
        GS->>GS: persist DraftGradeRevision {revisionId, reviewerId, scores[], status: DRAFT}
        GS->>AL: DRAFT_GRADE_SAVED {attemptId, revisionId, reviewerId}
        GS-->>GW: 200 {revisionId, status: DRAFT}
        GW-->>SW: 200
        SW-->>R: "Draft saved."
    end

    R->>SW: Click "Release Grade"
    SW->>GW: POST /api/v1/grading/attempts/{attemptId}/release\n{revisionId}
    GW->>GS: ReleaseGrade(attemptId, revisionId, releasedBy)

    GS->>GS: finalize GradeRecord {status: RELEASED, finalScore, releasedAt}
    GS->>AL: GRADE_RELEASED {attemptId, revisionId, finalScore, releasedBy, releasedAt}
    GS->>AS: UpdateAttemptStatus(attemptId, GRADED)
    GS->>EB: publish(GRADE_RELEASED) {attemptId, enrollmentId, finalScore, passed}

    EB->>PS: onGradeReleased → recalculate progress
    PS->>PS: update ProgressRecord, evaluate completion
    PS->>EB: publish(PROGRESS_UPDATED)

    EB->>NS: onGradeReleased → notify learner
    NS-->>R: (no learner notification to reviewer)

    GS-->>GW: 200 {attemptId, status: GRADED, score: finalScore}
    GW-->>SW: 200
    SW-->>R: "Grade released to learner."

    Note over NS: Learner receives email/push:\n"Your submission has been graded. Score: X/Y"
```

---

## 4. Certificate Issuance Flow

Covers completion rule evaluation, certificate generation, secure storage, and learner notification. The `Certification Service` is the sole authority for issuing credentials; it verifies integrity before writing.

```mermaid
sequenceDiagram
    autonumber
    participant EB as Event Bus
    participant CS as Certification Service
    participant PS as Progress Service
    participant CRS as Course Service
    participant OB as Object Storage
    participant NS as Notification Service
    participant AL as Audit Log
    actor L as Learner

    EB->>CS: consume(PROGRESS_UPDATED)\n{enrollmentId, percentComplete, userId, courseId}

    CS->>PS: GetCompletionStatus(enrollmentId)
    PS-->>CS: {percentComplete, requiredItemsComplete[], assessmentsPassed[]}

    CS->>CRS: GetCompletionRules(courseId)
    CRS-->>CS: {minPassingScore, requiredAssessments[], requiredModules[],\n minAttendance, passingThreshold}

    CS->>CS: EvaluateCompletionRules(completionStatus, rules)

    alt completion criteria not yet met
        CS->>AL: COMPLETION_CHECK_FAILED {enrollmentId, unmetCriteria[]}
        Note over CS: No further action; wait for next PROGRESS_UPDATED event
    else learner already has an active certificate for this enrollment
        CS->>AL: CERTIFICATE_ALREADY_EXISTS {enrollmentId, certificateId}
        Note over CS: Idempotent — skip issuance
    else all criteria satisfied
        CS->>CS: generate verificationCode (UUID v4 + HMAC-signed)
        CS->>CS: build certificate payload\n{learnerName, courseName, completedAt,\n issuerName, verificationCode}
        CS->>OB: PUT /certificates/{verificationCode}.pdf\n(signed PDF with QR code)

        alt object storage write fails
            OB-->>CS: 503 Storage Unavailable
            CS->>AL: CERTIFICATE_GENERATION_FAILED {enrollmentId, reason: STORAGE_ERROR}
            CS->>EB: publish(CERTIFICATE_RETRY_REQUESTED) {enrollmentId, retryCount}
            Note over CS: Will retry up to 3 times with exponential backoff
        else PDF stored successfully
            OB-->>CS: 200 {objectUrl, eTag}
            CS->>CS: INSERT CertificateRecord\n{enrollmentId, userId, courseId, verificationCode,\n objectUrl, status: ISSUED, issuedAt}
            CS->>AL: CERTIFICATE_ISSUED {certificateId, enrollmentId, verificationCode, issuedAt}
            CS->>NS: PublishEvent(CERTIFICATE_ISSUED)\n{userId, courseTitle, downloadUrl, verificationCode}
            NS-->>L: Email: "Congratulations! Your certificate is ready.\n[Download] [Share on LinkedIn]"
            CS->>EB: publish(CERTIFICATE_ISSUED) {certificateId, userId, courseId}
            Note over EB: Downstream: analytics, employer integrations,\n badge platforms consume this event
        end
    end
```

---

## Sequence Non-Functional Budgets

| Sequence | Step | Target Latency (p95) | Timeout / Fallback |
|---|---|---|---|
| Enrollment creation | End-to-end (sync) | < 500 ms | Return denial reason with code |
| Enrollment creation | Policy evaluation | < 150 ms | Fail closed (deny) on timeout |
| Assessment submission | Submission ACK | < 700 ms | Accept + async grading queue |
| Assessment submission | Auto-grading | < 5 s | Return `PENDING_GRADE`, poll endpoint |
| Manual grade release | Full flow | < 2 s | Optimistic lock, retry prompt |
| Certificate issuance | PDF generation + storage | < 10 s | Retry queue (max 3 attempts) |
| Certificate issuance | Notification dispatch | < 30 s async | Dead-letter queue + manual retry |

## Idempotency Contract

| Endpoint | Idempotency Key | Behavior on Duplicate |
|---|---|---|
| `POST /enrollments` | `Idempotency-Key` header | Replay last `201` or `409` response |
| `POST /attempts/{id}/submit` | `attemptId` (path param) | Replay last acknowledged response |
| `PUT /grading/attempts/{id}` | `revisionId` in body | Upsert draft revision, no duplicates |
| `POST /grading/attempts/{id}/release` | `revisionId` in body | Idempotent — re-release returns current state |
| Certificate issuance (async) | `enrollmentId` | Skip if certificate already `ISSUED` |

## Audit Events Reference

| Event | Emitted By | Consumed By | Retention |
|---|---|---|---|
| `ENROLLMENT_REQUESTED` | Enrollment Service | Audit Log | 7 years |
| `ENROLLMENT_DENIED` | Enrollment Service | Audit Log, Analytics | 7 years |
| `ENROLLMENT_CREATED` | Enrollment Service | Audit Log, Analytics, Notification | 7 years |
| `ATTEMPT_SUBMITTED` | Assessment Service | Audit Log | 7 years |
| `ATTEMPT_AUTO_GRADED` | Grading Service | Audit Log, Progress Service | 7 years |
| `MANUAL_REVIEW_QUEUED` | Grading Service | Audit Log | 7 years |
| `DRAFT_GRADE_SAVED` | Grading Service | Audit Log | 7 years |
| `GRADE_RELEASED` | Grading Service | Audit Log, Progress, Notification | 7 years |
| `COMPLETION_CHECK_FAILED` | Certification Service | Audit Log | 7 years |
| `CERTIFICATE_ISSUED` | Certification Service | Audit Log, Analytics, Notification | Permanent |
| `CERTIFICATE_GENERATION_FAILED` | Certification Service | Audit Log, Retry Queue | 7 years |
