# Class Diagram - Learning Management System

This document provides the comprehensive object-oriented design of the LMS domain layer, including all domain classes with full attributes and methods, inheritance hierarchies, interfaces, enumerations, and value objects.

---

## Core Domain Class Diagram

```mermaid
classDiagram
    %% ─── Enumerations ───────────────────────────────────────────
    class TenantStatus {
        <<enumeration>>
        ACTIVE
        SUSPENDED
        DEPROVISIONED
    }

    class UserAccountType {
        <<enumeration>>
        LEARNER
        INSTRUCTOR
        REVIEWER
        TENANT_ADMIN
        SUPER_ADMIN
    }

    class CourseState {
        <<enumeration>>
        DRAFT
        IN_REVIEW
        PUBLISHED
        ARCHIVED
    }

    class AssessmentType {
        <<enumeration>>
        QUIZ
        EXAM
        ASSIGNMENT
        PEER_REVIEW
        SURVEY
    }

    class GradingMode {
        <<enumeration>>
        AUTO
        MANUAL
        HYBRID
    }

    class EnrollmentStatus {
        <<enumeration>>
        INVITED
        ACTIVE
        COMPLETED
        DROPPED
        EXPIRED
        REACTIVATED
    }

    class AttemptStatus {
        <<enumeration>>
        IN_PROGRESS
        SUBMITTED
        PENDING_REVIEW
        GRADED
        EXPIRED
    }

    class GradeSource {
        <<enumeration>>
        AUTO_GRADED
        MANUAL_GRADED
        OVERRIDDEN
    }

    class GradeStatus {
        <<enumeration>>
        DRAFT
        RELEASED
        OVERRIDDEN
    }

    class CertificateStatus {
        <<enumeration>>
        PENDING
        ISSUED
        EXPIRED
        REVOKED
    }

    class LessonType {
        <<enumeration>>
        VIDEO
        TEXT
        SLIDE
        SCORM
        LIVE_SESSION
    }

    class QuestionType {
        <<enumeration>>
        MULTIPLE_CHOICE
        MULTI_SELECT
        TRUE_FALSE
        SHORT_ANSWER
        ESSAY
        FILE_UPLOAD
        MATCHING
    }

    class CompletionStatus {
        <<enumeration>>
        NOT_STARTED
        IN_PROGRESS
        COMPLETED
        FAILED
    }

    %% ─── Value Objects ───────────────────────────────────────────
    class Score {
        <<value object>>
        +float value
        +float max
        +Score(value: float, max: float)
        +float percentage() float
        +bool isPassingGiven(threshold: float) bool
        +Score add(other: Score) Score
    }

    class TimeWindow {
        <<value object>>
        +DateTime opensAt
        +DateTime closesAt
        +TimeWindow(opensAt: DateTime, closesAt: DateTime)
        +bool isOpen(at: DateTime) bool
        +bool isClosed(at: DateTime) bool
        +Duration duration() Duration
    }

    class PolicyOutcome {
        <<value object>>
        +string decision
        +string reason
        +string[] missingItemIds
        +PolicyOutcome approved() PolicyOutcome$
        +PolicyOutcome denied(reason: string, missing: string[]) PolicyOutcome$
        +bool isApproved() bool
    }

    class VerificationCode {
        <<value object>>
        +string code
        +string hmacSignature
        +VerificationCode generate(enrollmentId: UUID) VerificationCode$
        +bool verify(code: string, secret: string) bool
    }

    class ContentLocator {
        <<value object>>
        +string bucket
        +string objectKey
        +string cdnUrl
        +string presignedUrl(ttlSeconds: int) string
    }

    class AttemptTimer {
        <<value object>>
        +DateTime startedAt
        +int timeLimitMinutes
        +DateTime expiresAt
        +AttemptTimer start(at: DateTime, limitMinutes: int) AttemptTimer$
        +bool isExpired(at: DateTime) bool
        +int remainingSeconds(at: DateTime) int
    }

    %% ─── Interfaces ──────────────────────────────────────────────
    class ICompletionEvaluator {
        <<interface>>
        +bool evaluate(progress: ProgressRecord, rule: CompletionRule) bool
        +string[] unmetCriteria(progress: ProgressRecord, rule: CompletionRule) string[]
    }

    class IGradingStrategy {
        <<interface>>
        +GradeRecord grade(attempt: AssessmentAttempt, context: GradingContext) GradeRecord
    }

    class IEnrollmentPolicy {
        <<interface>>
        +PolicyOutcome evaluate(request: EnrollmentRequest, cohort: Cohort, user: User) PolicyOutcome
    }

    class ICertificateGenerator {
        <<interface>>
        +ContentLocator generate(certificate: Certificate) ContentLocator
    }

    class INotificationPublisher {
        <<interface>>
        +void publish(event: DomainEvent, recipients: User[]) void
    }

    %% ─── Tenant & Identity ───────────────────────────────────────
    class Tenant {
        +UUID id
        +string name
        +string slug
        +TenantStatus status
        +JsonObject settings
        +DateTime createdAt
        +Tenant create(name: string, slug: string) Tenant$
        +void suspend() void
        +void reactivate() void
        +bool isActive() bool
    }

    class User {
        +UUID id
        +UUID tenantId
        +string email
        +string displayName
        +string passwordHash
        +UserAccountType accountType
        +string status
        +DateTime lastLoginAt
        +User register(tenantId: UUID, email: string, type: UserAccountType) User$
        +void changeEmail(newEmail: string) void
        +void deactivate() void
        +bool hasRole(role: string, scopeId: UUID) bool
    }

    class RoleAssignment {
        +UUID id
        +UUID userId
        +UUID tenantId
        +string role
        +UUID scopeId
        +string scopeType
        +DateTime assignedAt
        +DateTime revokedAt
        +bool isActive() bool
    }

    %% ─── Catalog & Authoring ─────────────────────────────────────
    class Course {
        +UUID id
        +UUID tenantId
        +string title
        +string slug
        +string category
        +string description
        +CourseState state
        +UUID activeVersionId
        +DateTime createdAt
        +Course create(tenantId: UUID, title: string) Course$
        +CourseVersion createVersion(authorId: UUID) CourseVersion
        +void publish(versionId: UUID) void
        +void archive() void
        +CourseVersion activeVersion() CourseVersion
    }

    class CourseVersion {
        +UUID id
        +UUID courseId
        +int versionNo
        +CourseState state
        +UUID authorId
        +DateTime publishedAt
        +DateTime archivedAt
        +CourseVersion newDraft(courseId: UUID, authorId: UUID) CourseVersion$
        +void submitForReview() void
        +void publish() void
        +void archive() void
        +Module addModule(title: string, sequence: int) Module
        +CompletionRule setCompletionRule(rule: CompletionRule) CompletionRule
        +bool isPublished() bool
    }

    class CompletionRule {
        +UUID id
        +UUID courseVersionId
        +float minPassingScore
        +bool requireAllModules
        +int minAttendancePercent
        +UUID[] requiredAssessmentIds
        +bool isSatisfiedBy(progress: ProgressRecord) bool
        +string[] unmetCriteria(progress: ProgressRecord) string[]
    }

    class Module {
        +UUID id
        +UUID courseVersionId
        +string title
        +int sequence
        +bool isRequired
        +DateTime createdAt
        +Lesson addLesson(title: string, type: LessonType) Lesson
        +Assessment addAssessment(type: AssessmentType) Assessment
        +void reorder(newSequence: int) void
    }

    class Lesson {
        +UUID id
        +UUID moduleId
        +string title
        +LessonType type
        +int durationMinutes
        +int sequence
        +ContentLocator content
        +Lesson create(moduleId: UUID, title: string, type: LessonType) Lesson$
        +void updateContent(locator: ContentLocator) void
        +void reorder(newSequence: int) void
    }

    %% ─── Assessment Design ───────────────────────────────────────
    class Assessment {
        +UUID id
        +UUID moduleId
        +UUID courseVersionId
        +string title
        +AssessmentType assessmentType
        +GradingMode gradingMode
        +int attemptLimit
        +int timeLimitMinutes
        +Score maxScore
        +float passingScore
        +Assessment create(moduleId: UUID, type: AssessmentType) Assessment$
        +Question addQuestion(type: QuestionType, points: float) Question
        +Rubric attachRubric(rubric: Rubric) Rubric
        +bool isAutoGradable() bool
        +bool exceedsAttemptLimit(attemptCount: int) bool
    }

    class Question {
        +UUID id
        +UUID assessmentId
        +QuestionType questionType
        +float points
        +JsonObject content
        +JsonObject correctAnswer
        +int sequence
        +Question create(assessmentId: UUID, type: QuestionType) Question$
        +Score scoreAnswer(answer: JsonObject) Score
        +void reorder(newSequence: int) void
    }

    class Rubric {
        +UUID id
        +UUID assessmentId
        +string name
        +RubricCriterion[] criteria
        +Rubric create(assessmentId: UUID, name: string) Rubric$
        +RubricCriterion addCriterion(name: string, maxPoints: float) RubricCriterion
        +Score maxScore() Score
    }

    class RubricCriterion {
        +UUID id
        +UUID rubricId
        +string name
        +float maxPoints
        +JsonObject scoringGuide
        +Score validate(earnedPoints: float) Score
    }

    %% ─── Cohort & Enrollment ─────────────────────────────────────
    class Cohort {
        +UUID id
        +UUID courseId
        +UUID courseVersionId
        +string name
        +int seatCapacity
        +int seatsUsed
        +TimeWindow enrollmentWindow
        +TimeWindow deliveryWindow
        +DateTime createdAt
        +Cohort create(courseId: UUID, versionId: UUID, name: string) Cohort$
        +bool hasAvailableSeats() bool
        +bool isEnrollmentOpen() bool
        +void incrementSeats() void
        +void decrementSeats() void
    }

    class Enrollment {
        +UUID id
        +UUID userId
        +UUID cohortId
        +UUID courseId
        +EnrollmentStatus status
        +DateTime enrolledAt
        +DateTime completedAt
        +DateTime expiresAt
        +string idempotencyKey
        +Enrollment create(userId: UUID, cohortId: UUID, key: string) Enrollment$
        +void activate() void
        +void complete() void
        +void drop(reason: string) void
        +void expire() void
        +void reactivate(newExpiry: DateTime) void
        +bool isActive() bool
        +bool hasExpired() bool
    }

    %% ─── Progress Tracking ───────────────────────────────────────
    class LessonProgress {
        +UUID id
        +UUID enrollmentId
        +UUID lessonId
        +CompletionStatus status
        +int progressSeconds
        +DateTime completedAt
        +LessonProgress start(enrollmentId: UUID, lessonId: UUID) LessonProgress$
        +void advance(seconds: int) void
        +void complete() void
    }

    class ProgressRecord {
        +UUID id
        +UUID enrollmentId
        +float percentComplete
        +int modulesCompleted
        +int lessonsCompleted
        +CompletionStatus completionStatus
        +DateTime lastActivityAt
        +ProgressRecord initialize(enrollmentId: UUID) ProgressRecord$
        +void recalculate(lessonProgress: LessonProgress[], grades: GradeRecord[]) void
        +bool meetsCompletionRule(rule: CompletionRule) bool
    }

    %% ─── Assessment Attempt & Grading ────────────────────────────
    class AssessmentAttempt {
        +UUID id
        +UUID assessmentId
        +UUID enrollmentId
        +UUID userId
        +int attemptNumber
        +AttemptStatus status
        +AttemptTimer timer
        +DateTime submittedAt
        +AssessmentAttempt start(assessmentId: UUID, enrollmentId: UUID, n: int) AssessmentAttempt$
        +void saveAnswer(questionId: UUID, value: JsonObject) void
        +void submit(submittedAt: DateTime) void
        +void expire() void
        +bool isSubmittable() bool
        +bool isTimedOut(at: DateTime) bool
    }

    class AnswerArtifact {
        +UUID id
        +UUID attemptId
        +UUID questionId
        +JsonObject answerValue
        +string answerType
        +DateTime savedAt
    }

    class GradeRecord {
        +UUID id
        +UUID attemptId
        +int revisionNo
        +Score finalScore
        +GradeSource gradeSource
        +UUID reviewerId
        +GradeStatus status
        +string feedback
        +DateTime gradedAt
        +DateTime releasedAt
        +GradeRecord autoGrade(attemptId: UUID, score: Score) GradeRecord$
        +GradeRecord manualGrade(attemptId: UUID, reviewerId: UUID) GradeRecord$
        +void release(releasedBy: UUID) void
        +void override(newScore: Score, reason: string, by: UUID) GradeRecord
        +bool isReleased() bool
        +bool passed(threshold: float) bool
    }

    class GradeCriterionScore {
        +UUID id
        +UUID gradeRecordId
        +UUID criterionId
        +float score
        +string feedback
    }

    %% ─── Certification ───────────────────────────────────────────
    class Certificate {
        +UUID id
        +UUID enrollmentId
        +UUID userId
        +UUID courseId
        +VerificationCode verificationCode
        +ContentLocator pdfLocation
        +CertificateStatus status
        +DateTime issuedAt
        +DateTime expiresAt
        +DateTime revokedAt
        +string revokedReason
        +Certificate issue(enrollmentId: UUID, userId: UUID, courseId: UUID) Certificate$
        +void revoke(reason: string, revokedBy: UUID) void
        +bool isValid() bool
        +bool isExpired(at: DateTime) bool
    }

    %% ─── Domain Services ─────────────────────────────────────────
    class EnrollmentPolicyEvaluator {
        <<domain service>>
        -IEnrollmentPolicy[] policies
        +PolicyOutcome evaluate(request: EnrollmentRequest, cohort: Cohort, user: User) PolicyOutcome
        -PolicyOutcome checkSeats(cohort: Cohort) PolicyOutcome
        -PolicyOutcome checkWindow(cohort: Cohort) PolicyOutcome
        -PolicyOutcome checkPrerequisites(user: User, versionId: UUID) PolicyOutcome
    }

    class AutoGradingEngine {
        <<domain service>>
        +implements IGradingStrategy
        +GradeRecord grade(attempt: AssessmentAttempt, context: GradingContext) GradeRecord
        -Score scoreQuestion(question: Question, answer: AnswerArtifact) Score
        -Score aggregate(scores: Score[]) Score
    }

    class CompletionEvaluator {
        <<domain service>>
        +implements ICompletionEvaluator
        +bool evaluate(progress: ProgressRecord, rule: CompletionRule) bool
        +string[] unmetCriteria(progress: ProgressRecord, rule: CompletionRule) string[]
    }

    %% ─── Relationships ───────────────────────────────────────────
    Tenant "1" --o "many" User : has
    Tenant "1" --o "many" Course : owns
    User "1" --o "many" RoleAssignment : holds
    Course "1" --o "many" CourseVersion : versioned as
    Course "1" --o "many" Cohort : delivered via
    CourseVersion "1" --o "many" Module : contains
    CourseVersion "1" --|| CompletionRule : governed by
    Module "1" --o "many" Lesson : contains
    Module "1" --o "many" Assessment : includes
    Assessment "1" --o "many" Question : composed of
    Assessment "1" --o "1" Rubric : scored by
    Rubric "1" --o "many" RubricCriterion : defines
    Cohort "1" --|| CourseVersion : uses
    Cohort "1" --o "many" Enrollment : contains
    User "1" --o "many" Enrollment : holds
    Enrollment "1" --o "many" LessonProgress : tracks
    Enrollment "1" --|| ProgressRecord : summarised by
    Enrollment "1" --o "many" AssessmentAttempt : generates
    Assessment "1" --o "many" AssessmentAttempt : received by
    AssessmentAttempt "1" --o "many" AnswerArtifact : captures
    AssessmentAttempt "1" --o "many" GradeRecord : scored in
    GradeRecord "1" --o "many" GradeCriterionScore : broken down by
    Enrollment "1" --o "1" Certificate : may earn
    AutoGradingEngine ..|> IGradingStrategy : implements
    CompletionEvaluator ..|> ICompletionEvaluator : implements
    EnrollmentPolicyEvaluator ..> PolicyOutcome : returns
    GradeRecord ..> Score : uses
    AssessmentAttempt ..> AttemptTimer : uses
    Cohort ..> TimeWindow : uses
    Certificate ..> VerificationCode : uses
    Certificate ..> ContentLocator : uses
    Lesson ..> ContentLocator : uses
```

---

## Value Object Invariants

| Value Object | Invariants |
|---|---|
| `Score` | `value >= 0`, `value <= max`, `max > 0` |
| `TimeWindow` | `closesAt > opensAt` |
| `PolicyOutcome` | `decision ∈ {APPROVED, DENIED}`; if `DENIED`, `reason` must be non-empty |
| `VerificationCode` | Immutable after creation; HMAC computed from `enrollmentId + secret` |
| `AttemptTimer` | `expiresAt = startedAt + timeLimitMinutes`; immutable after construction |
| `ContentLocator` | `bucket` and `objectKey` must be non-empty; `presignedUrl()` is not stored |

## Interface Contracts Summary

| Interface | Implementing Classes | Contract |
|---|---|---|
| `IGradingStrategy` | `AutoGradingEngine`, `RubricScoringService` | Must return a valid `GradeRecord` or throw a typed domain exception |
| `ICompletionEvaluator` | `CompletionEvaluator` | Pure function — no side effects; must return same result for same inputs |
| `IEnrollmentPolicy` | `SeatPolicy`, `WindowPolicy`, `PrerequisitePolicy` | Returns `PolicyOutcome`; must not write to any store |
| `ICertificateGenerator` | `PdfCertificateGenerator` | Generates PDF and stores in object storage; returns `ContentLocator` |
| `INotificationPublisher` | `KafkaNotificationPublisher` | Fire-and-forget; caller does not wait for delivery confirmation |
