# System Context Diagram - Learning Management System

```mermaid
flowchart LR
    learners[Learners]
    staff[Instructors, Reviewers, Authors, Admins]
    idp[Identity Provider / SSO]
    notify[Email / Chat / Push Services]
    live[Live Session Provider]
    storage[Media and File Storage]
    analytics[Analytics / BI]

    subgraph lms[Learning Management System]
        learnerPortal[Learner Portal]
        staffWorkspace[Staff Workspace]
        api[Application API]
        search[Catalog and Analytics Search]
    end

    learners --> learnerPortal
    staff --> staffWorkspace
    learnerPortal --> api
    staffWorkspace --> api
    api --> idp
    api --> notify
    api --> live
    api --> storage
    api --> analytics
    api --> search
```

## Context Notes

- Learners primarily interact through the catalog, course player, assessment, and account workflows.
- Staff use dedicated operational surfaces for authoring, grading, cohort management, and reporting.
- The LMS integrates with identity, media storage, live-session tooling, notifications, and analytics platforms.
