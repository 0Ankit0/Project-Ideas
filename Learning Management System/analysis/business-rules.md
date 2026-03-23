# Business Rules - Learning Management System

## Tenant and Access Rules
- Users may access only tenant-scoped data unless they hold platform-level administrative permissions.
- Course visibility depends on publication state, audience targeting, and enrollment policy.
- Privileged actions such as grading overrides, certificate revocation, and policy changes require audit logging.

## Enrollment and Access Rules
- Learners may not access restricted content until prerequisite lessons or enrollments are satisfied.
- Cohort-based courses may enforce start and end dates, whereas self-paced courses may use rolling availability windows.
- Dropped or expired enrollments retain historical progress and grading data but lose active-learning access unless policy states otherwise.

## Assessment and Grading Rules

| Rule Area | Baseline Rule |
|-----------|---------------|
| Attempt limits | Defined per assessment and enforced before new attempt creation |
| Auto-graded items | Published immediately or after review depending on policy |
| Manual grading | Requires authorized reviewer or instructor |
| Passing logic | Based on configured score thresholds and required items |
| Grade override | Must retain original score, override reason, actor, and timestamp |

## Completion and Certification Rules
- Course completion may require lesson completion, assessment thresholds, attendance, and mandatory acknowledgments.
- Certificates may be issued only after all required completion rules are satisfied.
- Certificate revocation or reissue must retain auditable history.

## Content Governance Rules
- Published course versions must remain stable for enrolled learners unless tenant policy allows in-flight updates.
- Draft content cannot be learner-visible.
- Deleting content with learner history should archive or deactivate rather than hard-delete when records are required for reporting.
