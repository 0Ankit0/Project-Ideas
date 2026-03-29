# Use Case Descriptions - Learning Management System

## UC-01: Discover and Enroll in a Course
**Primary Actor**: Learner  
**Goal**: Find a relevant course and gain access according to tenant policy.

**Preconditions**:
- Learner is authenticated within a valid tenant.
- Course is discoverable to the learner's role and audience.

**Main Flow**:
1. Learner searches or browses the catalog.
2. System displays course details, prerequisites, schedule, instructor, and availability.
3. Learner requests enrollment or is auto-enrolled according to policy.
4. System validates prerequisites, seat limits, and enrollment windows.
5. Learner receives access confirmation and next-step notifications.

**Exceptions**:
- E1: Enrollment window closed -> learner is blocked or waitlisted.
- E2: Prerequisite unmet -> learner is shown missing requirements.

---

## UC-02: Consume Learning Content and Track Progress
**Primary Actor**: Learner

**Main Flow**:
1. Learner opens an enrolled course.
2. System renders the course outline, current progress, deadlines, and required items.
3. Learner launches a lesson or resource.
4. System records view, time, completion, and checkpoint events.
5. Completion rules are re-evaluated after each relevant event.

**Postconditions**:
- Learner progress is updated for the course, module, and lesson.

---

## UC-03: Submit Quiz or Assignment
**Primary Actor**: Learner

**Main Flow**:
1. Learner opens an assessment.
2. System validates access timing, attempt limits, and prerequisite completion.
3. Learner submits answers or uploads assignment artifacts.
4. System records the attempt and triggers auto-grading or review workflow.
5. Learner sees submission confirmation.

**Exceptions**:
- E1: Attempt limit exceeded -> submission is rejected.
- E2: Time window expired -> attempt is auto-submitted or blocked according to policy.

---

## UC-04: Review Submission and Publish Grade
**Primary Actor**: Instructor or Teaching Assistant / Reviewer

**Main Flow**:
1. Reviewer opens the grading queue.
2. System displays submissions, rubric criteria, prior attempts, and learner context.
3. Reviewer assigns scores, comments, and feedback.
4. System records audit history and recalculates gradebook aggregates.
5. Grade and feedback are published to the learner.

---

## UC-05: Author and Publish Course Content
**Primary Actor**: Content Admin / Author

**Main Flow**:
1. Author creates or edits a draft course version.
2. Author adds modules, lessons, resources, and assessments.
3. Author configures prerequisites, completion criteria, and metadata.
4. System runs validation checks for missing required configuration.
5. Authorized user publishes the course for eligible audiences.

---

## UC-06: Monitor Cohort Performance and At-Risk Learners
**Primary Actor**: Instructor or Tenant Admin

**Main Flow**:
1. User opens the cohort dashboard.
2. System displays enrollment counts, completion percentages, assessment outcomes, and inactivity indicators.
3. User filters by course, cohort, learner group, or date range.
4. User exports data or initiates outreach for at-risk learners.

---

## UC-07: Issue Certificate on Completion
**Primary Actor**: System Internal Trigger

**Trigger**: Completion rules satisfied

**Main Flow**:
1. System evaluates learner completion, required grades, attendance, and mandatory lessons.
2. System generates certificate metadata and a verifiable issuance record.
3. Learner and relevant staff are notified.
4. Certificate becomes visible in learner history and admin reporting.

---

## UC-08: Configure Tenant Policies and Integrations
**Primary Actor**: Tenant Admin or Platform Admin

**Main Flow**:
1. Admin updates enrollment rules, branding, grading scales, notification templates, or integrations.
2. System validates conflicts and scope boundaries.
3. Changes are versioned and applied according to effective dates.
4. Audit logs capture actor, before/after state, and scope.

## Implementation Details: Use-Case Contract Template

For each use case include:
1. Preconditions and authorization scope.
2. Main path plus compensation path.
3. Events emitted and idempotency behavior.
4. Audit entries and data retention class.
5. User-facing status for delayed/failed dependencies.
