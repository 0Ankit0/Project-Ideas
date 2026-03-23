# Event Catalog - Learning Management System

| Event | Producer | Consumers | Description |
|-------|----------|-----------|-------------|
| tenant.user_invited | Identity Service | Notification Service | Tenant user invited to LMS |
| course.published | Course Service | Catalog Search, Notification, Reporting | Course available to audience |
| enrollment.created | Enrollment Service | Notification, Reporting | Learner enrolled in course or cohort |
| lesson.progress_updated | Progress Service | Reporting, Recommendation, Notification | Learner progress checkpoint recorded |
| assessment.started | Assessment Service | Monitoring, Timer Service | Timed or tracked attempt began |
| assessment.submitted | Assessment Service | Auto-Grading, Review Queue | Attempt completed |
| grade.published | Grading Service | Learner Portal, Notification, Reporting | Final or provisional grade released |
| learner.at_risk_detected | Analytics Service | Instructor Dashboard, Notification | Engagement or performance risk surfaced |
| certificate.issued | Certification Service | Learner Portal, Notification, Reporting | Completion credential created |
| live_session.scheduled | Scheduling Service | Notification, Calendar Integration | Synchronous session scheduled |
| admin.policy_changed | Admin Service | Audit, Policy Engine | Rules or templates updated |
