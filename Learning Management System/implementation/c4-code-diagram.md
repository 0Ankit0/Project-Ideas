# C4 Code Diagram - Learning Management System

```mermaid
flowchart TB
    subgraph api[apps/api]
        controllers[Controllers]
        guards[Auth Guards]
        commands[Command Handlers]
        queries[Query Handlers]
    end

    subgraph domain[packages/domain]
        identity[Identity Module]
        courses[Courses Module]
        enrollments[Enrollments Module]
        assessments[Assessments Module]
        grading[Grading Module]
        progress[Progress Module]
        certificates[Certificates Module]
    end

    subgraph worker[apps/worker]
        notifications[Notification Jobs]
        progressProjector[Progress Projector]
        gradingQueue[Grading Queue Workers]
        certificatesJobs[Certificate Jobs]
    end

    controllers --> guards
    controllers --> commands
    controllers --> queries
    commands --> identity
    commands --> courses
    commands --> enrollments
    commands --> assessments
    commands --> grading
    commands --> progress
    commands --> certificates
    queries --> courses
    queries --> enrollments
    queries --> progress
    notifications --> enrollments
    progressProjector --> progress
    gradingQueue --> grading
    certificatesJobs --> certificates
```

## Implementation Details: Code-Level Module Rules

- Keep command handlers free of read-model dependencies.
- Keep projectors side-effect free except projection writes.
- Cross-module calls go through explicit interfaces, not direct persistence access.
