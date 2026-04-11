# Sequence Diagram - Learning Management System (Detailed)

This document provides low-level sequence diagrams showing internal service steps, database interactions, retry logic, and error handling for three critical flows.

---

## 1. Enrollment Validation Pipeline

Shows each internal step within the Enrollment Service and Policy Engine, including database reads, cache hits, error classification, and the idempotency key check.

```mermaid
sequenceDiagram
    autonumber
    participant GW as API Gateway
    participant ES as Enrollment Service
    participant IDK as Idempotency Store\n(Redis)
    participant PE as Policy Engine
    participant CS as Course Service
    participant DB as PostgreSQL\n(Enrollment DB)
    participant RD as Redis\n(Seat Counter)
    participant KF as Kafka
    participant AL as Audit Log

    GW->>ES: POST /enrollments\n{userId, cohortId, tenantId, idempotencyKey}

    %% Step 1: Idempotency check
    ES->>IDK: GET idempotency:{tenantId}:{key}
    alt key exists (duplicate request)
        IDK-->>ES: {status: 201, body: {enrollmentId}}
        ES-->>GW: 201 (replayed response)
        Note over ES,GW: Short-circuit — no DB write
    else key not found
        IDK-->>ES: null
        ES->>IDK: SET idempotency:{tenantId}:{key} = PROCESSING\nEX 300s (5 min TTL)
    end

    %% Step 2: Load cohort
    ES->>CS: GetCohort(cohortId, tenantId)
    alt cohort not found or belongs to different tenant
        CS-->>ES: 404 / 403
        ES->>IDK: DEL idempotency key (rollback lock)
        ES-->>GW: 404 {code: COHORT_NOT_FOUND}
    else cohort found
        CS-->>ES: {cohort: {seatCapacity, seatsUsed, enrollmentWindow,\n deliveryWindow, courseVersionId, prerequisiteCourseIds[]}}
    end

    %% Step 3: Check enrollment window
    ES->>PE: CheckEnrollmentWindow(cohort.enrollmentWindow)
    alt window closed
        PE-->>ES: DENIED {reason: ENROLLMENT_WINDOW_CLOSED}
        ES->>AL: ENROLLMENT_DENIED {reason: ENROLLMENT_WINDOW_CLOSED, userId, cohortId}
        ES->>IDK: SET key = DENIED (final state, TTL 24h)
        ES-->>GW: 422 {code: ENROLLMENT_WINDOW_CLOSED}
    else window open
        PE-->>ES: PASS
    end

    %% Step 4: Check seat availability (optimistic lock via Redis)
    ES->>RD: WATCH seats:{cohortId}
    ES->>RD: GET seats:{cohortId}
    alt seats exhausted (seatsUsed >= seatCapacity)
        ES->>AL: ENROLLMENT_DENIED {reason: SEAT_LIMIT_EXCEEDED}
        ES->>IDK: SET key = DENIED
        ES-->>GW: 409 {code: SEAT_LIMIT_EXCEEDED}
    else seats available
        RD-->>ES: {seatsUsed: N, seatCapacity: M}
    end

    %% Step 5: Check prerequisites
    ES->>PE: CheckPrerequisites(userId, prerequisiteCourseIds[])
    PE->>DB: SELECT enrollmentId FROM enrollments\nWHERE userId=? AND courseId IN (?) AND status='COMPLETED'
    DB-->>PE: {completedCourseIds[]}
    PE->>PE: diff(required, completed) → missing[]
    alt prerequisites not met
        PE-->>ES: DENIED {reason: PREREQUISITES_NOT_MET, missing[]}
        ES->>AL: ENROLLMENT_DENIED {reason: PREREQUISITES_NOT_MET, missing}
        ES->>IDK: SET key = DENIED
        ES-->>GW: 422 {code: PREREQUISITES_NOT_MET, missingCourses[]}
    else prerequisites satisfied
        PE-->>ES: APPROVED
    end

    %% Step 6: Write enrollment (transaction)
    ES->>DB: BEGIN TRANSACTION
    ES->>DB: INSERT INTO enrollments\n{id, userId, cohortId, courseId, status: ACTIVE,\n enrolledAt, expiresAt, idempotencyKey}
    ES->>DB: UPDATE cohorts SET seatsUsed = seatsUsed + 1\nWHERE id = cohortId AND seatsUsed < seatCapacity
    alt DB optimistic lock failure (concurrent enrollment)
        DB-->>ES: UPDATE returned 0 rows
        ES->>DB: ROLLBACK
        ES->>IDK: SET key = DENIED {reason: SEAT_LIMIT_EXCEEDED}
        ES-->>GW: 409 {code: SEAT_LIMIT_EXCEEDED}
    else commit success
        ES->>DB: COMMIT
        ES->>RD: INCR seats:{cohortId} (sync Redis counter)
        ES->>AL: ENROLLMENT_CREATED {enrollmentId, userId, cohortId, tenantId}
        ES->>KF: produce(enrollment-events, ENROLLMENT_CREATED\n{enrollmentId, userId, cohortId, courseId})
        ES->>IDK: SET key = CREATED:{enrollmentId} TTL 24h
        ES-->>GW: 201 Created {enrollmentId, status: ACTIVE}
    end
```

---

## 2. Assessment Attempt Lifecycle

Shows the full lifecycle from start to grade release, including timer management, answer persistence, auto/manual grading branch, database state transitions, and retry on transient failures.

```mermaid
sequenceDiagram
    autonumber
    actor L as Learner
    participant GW as API Gateway
    participant AS as Assessment Service
    participant DB_AS as PostgreSQL\n(Assessment Store)
    participant RD as Redis\n(Timer + Lock)
    participant GS as Grading Service
    participant DB_GS as PostgreSQL\n(Grade Store)
    participant PS as Progress Service
    participant DB_PS as PostgreSQL\n(Progress Store)
    participant KF as Kafka

    %% ── Phase 1: Start attempt ──────────────────────────────────
    L->>GW: POST /api/v1/assessments/{assessmentId}/attempts
    GW->>AS: StartAttempt(assessmentId, enrollmentId, userId)

    AS->>DB_AS: SELECT COUNT(*) FROM attempts\nWHERE assessmentId=? AND userId=? AND status != EXPIRED
    DB_AS-->>AS: attemptCount = N
    alt N >= assessment.attemptLimit
        AS-->>GW: 422 {code: ATTEMPT_LIMIT_EXCEEDED}
        GW-->>L: "No attempts remaining."
    else within limit
        AS->>DB_AS: INSERT attempt {id, status: IN_PROGRESS, attemptNumber: N+1,\n startedAt, expiresAt = startedAt + timeLimitMinutes}
        AS->>RD: SET timer:{attemptId} EX timeLimitSeconds (TTL-based expiry)
        AS->>KF: produce(assessment-events, ATTEMPT_STARTED {attemptId, userId, assessmentId})
        AS-->>GW: 201 {attemptId, expiresAt, questions[]}
        GW-->>L: Question set + timer
    end

    %% ── Phase 2: Save answers (incremental) ─────────────────────
    loop For each answer saved
        L->>GW: PUT /api/v1/attempts/{attemptId}/answers/{questionId}\n{answerValue}
        GW->>AS: SaveAnswer(attemptId, questionId, answerValue)
        AS->>RD: EXISTS timer:{attemptId}
        alt timer expired
            RD-->>AS: null (key gone)
            AS->>AS: AutoSubmitExpiredAttempt(attemptId)
            AS->>DB_AS: UPDATE attempts SET status=SUBMITTED, submittedAt=now()\nWHERE id=attemptId AND status=IN_PROGRESS
            AS->>KF: produce(assessment-events, ATTEMPT_EXPIRED {attemptId})
            AS-->>GW: 422 {code: ATTEMPT_EXPIRED, message: "Time expired."}
        else timer active
            AS->>DB_AS: INSERT OR REPLACE answer_artifacts\n{attemptId, questionId, answerValue, savedAt}
            AS-->>GW: 204 No Content
        end
    end

    %% ── Phase 3: Submit ─────────────────────────────────────────
    L->>GW: POST /api/v1/attempts/{attemptId}/submit\n{clientChecksum}
    GW->>AS: SubmitAttempt(attemptId, userId)

    AS->>DB_AS: SELECT * FROM attempts WHERE id=attemptId FOR UPDATE
    alt attempt not IN_PROGRESS
        DB_AS-->>AS: status = SUBMITTED (idempotent replay)
        AS-->>GW: 200 {attemptId, status: already submitted}
    else status = IN_PROGRESS
        AS->>RD: DEL timer:{attemptId}
        AS->>DB_AS: UPDATE attempts SET status=SUBMITTED, submittedAt=now()
        AS->>KF: produce(assessment-events, ATTEMPT_SUBMITTED {attemptId, gradingMode})
    end

    %% ── Phase 4a: Auto-grading path ─────────────────────────────
    alt gradingMode = AUTO
        KF->>GS: consume(assessment-events, ATTEMPT_SUBMITTED)
        GS->>DB_AS: SELECT questions + answers + answerKey\nWHERE attemptId=?
        DB_AS-->>GS: {questions[], artifacts[], answerKey{}}
        loop for each question
            GS->>GS: score = AutoGradingEngine.score(question, artifact)
        end
        GS->>DB_GS: INSERT grade_records\n{attemptId, revisionNo: 1, finalScore, maxScore,\n passed, gradeSource: AUTO_GRADED, status: RELEASED, gradedAt}
        GS->>DB_AS: UPDATE attempts SET status = GRADED
        GS->>KF: produce(grading-events, GRADE_RELEASED {attemptId, enrollmentId, finalScore, passed})
        AS-->>GW: 200 {attemptId, status: GRADED, score, passed}
        GW-->>L: Score displayed

    %% ── Phase 4b: Manual grading path ───────────────────────────
    else gradingMode = MANUAL or HYBRID
        KF->>GS: consume(assessment-events, ATTEMPT_SUBMITTED)
        GS->>DB_GS: INSERT grading_queue {attemptId, assignedReviewerId, status: PENDING}
        GS->>KF: produce(grading-events, MANUAL_REVIEW_QUEUED {attemptId, reviewerId})
        AS-->>GW: 202 {attemptId, status: PENDING_REVIEW, estimatedReviewHours: 48}
        GW-->>L: "Submitted. Review within 48 hours."

        Note over GS: Reviewer scores via Staff Workspace (separate flow)
        GS->>DB_GS: INSERT grade_records {revisionNo, status: RELEASED, releasedAt}
        GS->>KF: produce(grading-events, GRADE_RELEASED {attemptId, enrollmentId, finalScore, passed})
    end

    %% ── Phase 5: Progress update ────────────────────────────────
    KF->>PS: consume(grading-events, GRADE_RELEASED)
    PS->>DB_PS: SELECT progress_records WHERE enrollmentId=?
    DB_PS-->>PS: {currentRecord}
    PS->>PS: recalculate(lessonProgress[], gradeRecords[]) → updatedRecord
    PS->>DB_PS: UPDATE progress_records SET percentComplete, completionStatus, lastActivityAt
    PS->>KF: produce(progress-events, PROGRESS_UPDATED {enrollmentId, percentComplete, completionStatus})

    alt completionStatus = COMPLETED
        Note over KF: Certificate Worker consumes PROGRESS_UPDATED\nand triggers certificate issuance flow
    end
```

---

## 3. Progress Event Processing Pipeline

Shows the path of a lesson completion event from the client through the API, message queue, worker, and projection — including retry logic and idempotency.

```mermaid
sequenceDiagram
    autonumber
    actor L as Learner
    participant SW as Learner Portal\n(Client)
    participant GW as API Gateway
    participant PRS as Progress Service
    participant DB_P as PostgreSQL\n(Progress Store)
    participant KF as Kafka\n(progress-events)
    participant PW as Projection Worker
    participant ES as Elasticsearch
    participant DLQ as Dead Letter Queue

    %% ── Step 1: Client sends lesson completion event ────────────
    L->>SW: Reach end of lesson / click "Mark Complete"
    SW->>SW: Buffer event (offline-safe)\n{lessonId, enrollmentId, progressSeconds, completedAt}
    SW->>GW: POST /api/v1/enrollments/{enrollmentId}/progress/lessons/{lessonId}\n{progressSeconds, completedAt, clientEventId}

    GW->>PRS: RecordLessonProgress(enrollmentId, lessonId, progressSeconds, eventId)

    %% ── Step 2: Idempotency check ───────────────────────────────
    PRS->>DB_P: SELECT id FROM lesson_progress\nWHERE enrollmentId=? AND lessonId=? AND status=COMPLETED
    alt already completed (idempotent)
        DB_P-->>PRS: {existing record}
        PRS-->>GW: 200 {status: already recorded}
        GW-->>SW: 200
    else first completion
        DB_P-->>PRS: null
        PRS->>DB_P: INSERT lesson_progress\n{enrollmentId, lessonId, status: COMPLETED,\n progressSeconds, completedAt}
        PRS->>DB_P: SELECT COUNT(completed) / COUNT(total)\nFROM lesson_progress JOIN modules ... WHERE enrollmentId=?
        DB_P-->>PRS: {lessonsCompleted, modulesCompleted, percentComplete}
        PRS->>DB_P: UPDATE progress_records\nSET lessonsCompleted, modulesCompleted, percentComplete, lastActivityAt
        PRS->>KF: produce(progress-events)\n{enrollmentId, lessonId, percentComplete,\n completionStatus, tenantId, eventId}
        PRS-->>GW: 204 No Content
        GW-->>SW: 204
        SW-->>L: Lesson marked complete and progress bar updated
    end

    %% ── Step 3: Projection Worker consumes event ────────────────
    KF->>PW: consume(progress-events) {offset, partition}
    PW->>PW: check deduplication store for eventId
    alt eventId already processed
        PW->>KF: commit offset (skip)
        Note over PW: Idempotent — no re-indexing
    else new event
        PW->>ES: POST /_bulk\n[update learner-progress index,\n update enrollment-status index]
        alt ES write success
            ES-->>PW: 200 {items: [{result: updated}]}
            PW->>PW: record eventId as processed
            PW->>KF: commit offset
        else ES write failure (503 / network error)
            ES-->>PW: 503 / timeout
            PW->>PW: retry with exponential backoff\n(attempts: 1, 2, 4, 8, 16 seconds)
            alt retry 1-3 succeeds
                ES-->>PW: 200
                PW->>KF: commit offset
            else all 3 retries exhausted
                PW->>DLQ: produce(dead-letter-queue)\n{originalEvent, error, attempts: 3, failedAt}
                PW->>KF: commit offset (poison pill avoidance)
                Note over DLQ: Ops team receives alert;\nmanual replay after ES recovery
            end
        end
    end

    %% ── Step 4: Completion trigger ──────────────────────────────
    alt completionStatus transitions to COMPLETED
        KF->>PW: progress-events consumed by Certificate Worker
        Note over PW: Triggers separate certificate issuance flow
    end
```

---

## Retry and Error Handling Reference

| Operation | Retry Strategy | Max Attempts | On Exhaustion |
|---|---|---|---|
| Enrollment seat UPDATE (optimistic lock) | Immediate retry | 3 | Return `SEAT_LIMIT_EXCEEDED` |
| Grading Worker — auto-grade | Exponential backoff (1s, 2s, 4s) | 3 | Publish to DLQ; alert on-call |
| Projection Worker — ES index | Exponential backoff (1s, 2s, 4s, 8s, 16s) | 5 | Publish to DLQ; continue consuming |
| Certificate Worker — PDF generation | Linear retry (5s, 5s, 5s) | 3 | Publish to DLQ; alert on-call |
| Notification Worker — email dispatch | Exponential backoff (30s, 60s, 120s) | 5 | Publish to DLQ; learner sees "pending" |
| Progress lesson write | None (idempotent re-try by client) | Client-driven | Client shows "saved offline" |

## Database Interaction Summary

| Service | Tables Written | Tables Read | Transaction Scope |
|---|---|---|---|
| Enrollment Service | `enrollments`, `cohorts.seatsUsed` | `enrollments`, `cohorts`, `completions` | Single transaction (enrollment + seat) |
| Assessment Service | `attempts`, `answer_artifacts` | `attempts`, `assessments`, `questions` | Single transaction per answer save |
| Grading Service | `grade_records`, `grade_criterion_scores` | `attempts`, `answer_artifacts`, `questions`, `rubric_criteria` | Single transaction per grade record |
| Progress Service | `lesson_progress`, `progress_records` | `lesson_progress`, `progress_records`, `modules`, `lessons` | Single transaction per lesson event |
| Certification Service | `certificates` | `progress_records`, `completion_rules`, `certificates` | Single transaction per certificate insert |
