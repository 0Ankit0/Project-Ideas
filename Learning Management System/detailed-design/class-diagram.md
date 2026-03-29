# Class Diagram - Learning Management System

```mermaid
classDiagram
    class Tenant {
      +UUID id
      +string name
      +string status
    }
    class User {
      +UUID id
      +string email
      +string accountType
      +string status
    }
    class Course {
      +UUID id
      +string title
      +string category
      +string status
    }
    class CourseVersion {
      +UUID id
      +int versionNo
      +string state
    }
    class Module {
      +UUID id
      +string title
      +int sequence
    }
    class Lesson {
      +UUID id
      +string type
      +int durationMinutes
    }
    class Cohort {
      +UUID id
      +string name
      +datetime startsAt
      +datetime endsAt
    }
    class Enrollment {
      +UUID id
      +string status
      +datetime enrolledAt
    }
    class Assessment {
      +UUID id
      +string assessmentType
      +int attemptLimit
      +float passingScore
    }
    class AssessmentAttempt {
      +UUID id
      +string status
      +float score
    }
    class ProgressRecord {
      +UUID id
      +string status
      +float percentComplete
    }
    class Certificate {
      +UUID id
      +string verificationCode
      +datetime issuedAt
    }

    Tenant "1" --> "many" User
    Tenant "1" --> "many" Course
    Course "1" --> "many" CourseVersion
    CourseVersion "1" --> "many" Module
    Module "1" --> "many" Lesson
    Module "1" --> "many" Assessment
    Course "1" --> "many" Cohort
    User "1" --> "many" Enrollment
    Cohort "1" --> "many" Enrollment
    User "1" --> "many" AssessmentAttempt
    Assessment "1" --> "many" AssessmentAttempt
    User "1" --> "many" ProgressRecord
    User "1" --> "many" Certificate
```

## Implementation Details: Domain Object Constraints

- Value objects: `Score`, `Progress`, `TimeWindow`, `PolicyOutcome`.
- Entities enforce invariants at construction (no invalid empty tenant scope, no negative max points).
- Domain services perform policy evaluation without side effects.
