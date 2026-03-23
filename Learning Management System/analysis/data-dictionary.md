# Data Dictionary - Learning Management System

| Entity | Key Fields | Description |
|--------|------------|-------------|
| Tenant | id, name, status, brandingConfig | Organization using the LMS |
| User | id, tenantId, email, accountType, status | Authenticated learner or staff user |
| RoleAssignment | userId, scopeType, scopeId, roleName | Scoped permission grant |
| Course | id, tenantId, title, category, status, ownerId | Top-level learning offering |
| CourseVersion | id, courseId, versionNo, state, publishedAt | Versioned content snapshot |
| Module | id, courseVersionId, title, sequence | Group of lessons or assessments |
| Lesson | id, moduleId, type, duration, completionRule | Individual learning unit |
| Cohort | id, courseId, name, scheduleType, startsAt, endsAt | Delivery grouping for learners |
| Enrollment | id, learnerId, cohortId, status, enrolledAt, completedAt | Learner-course membership record |
| Assessment | id, moduleId, assessmentType, passingScore, attemptLimit | Quiz, exam, or assignment definition |
| AssessmentAttempt | id, assessmentId, learnerId, status, startedAt, submittedAt, score | Learner submission attempt |
| GradeRecord | id, learnerId, assessmentId, publishedScore, gradedBy, publishedAt | Published grading outcome |
| ProgressRecord | id, learnerId, lessonId, status, percentComplete, lastSeenAt | Lesson or content progress tracking |
| Certificate | id, learnerId, courseId, issuedAt, verificationCode | Completion credential |
| LiveSession | id, cohortId, providerRef, startsAt, joinUrl | Synchronous learning event |
| Notification | id, recipientId, templateKey, channel, status, sentAt | Outbound learner or staff communication |
| AuditLog | id, actorId, action, entityType, entityId, createdAt | Immutable operational history |
