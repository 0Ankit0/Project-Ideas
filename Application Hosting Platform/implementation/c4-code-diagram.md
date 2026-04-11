# C4 Code Diagram (Deployment Domain)

## Traceability
- Requirements: [`../requirements/requirements.md`](../requirements/requirements.md)
- High-level architecture: [`../high-level-design/c4-diagrams.md`](../high-level-design/c4-diagrams.md)
- Detailed deployment design: [`../detailed-design/deployment-engine-and-build-pipeline.md`](../detailed-design/deployment-engine-and-build-pipeline.md)
- Execution workflow: [`./implementation-guidelines.md`](./implementation-guidelines.md)

```mermaid
classDiagram
  class DeploymentController {
    +createDeployment(request)
    +rollback(deploymentId)
  }

  class DeploymentService {
    +validatePolicy()
    +orchestrateRollout()
    +recordStatus()
  }

  class RolloutPlanner {
    +planCanary()
    +planBlueGreen()
  }

  class HealthGate {
    +evaluateReadiness()
    +evaluateErrorBudget()
  }

  class ArtifactStore {
    +fetchByDigest()
    +verifySignature()
  }

  class DeploymentRepository {
    +save()
    +findById()
    +listByApp()
  }

  DeploymentController --> DeploymentService
  DeploymentService --> RolloutPlanner
  DeploymentService --> HealthGate
  DeploymentService --> ArtifactStore
  DeploymentService --> DeploymentRepository
```

## Deployment Workflow

```mermaid
flowchart LR
  Req[Deploy Request] --> Ctrl[DeploymentController]
  Ctrl --> Svc[DeploymentService]
  Svc --> Art[ArtifactStore verify]
  Svc --> Plan[RolloutPlanner]
  Plan --> Gate[HealthGate]
  Gate --> Repo[DeploymentRepository]
  Gate --> Result{SLO pass?}
  Result -->|Yes| Live[Promote Live]
  Result -->|No| Roll[Rollback]
```

### Invariants
- Controller layer is policy-only; it cannot mutate cluster state directly.
- Artifact verification must succeed before rollout planning.

### Operational acceptance criteria
- Code-level architecture lint checks enforce dependency direction.
- Rollback path is covered by automated integration tests.

---

**Status**: Complete  
**Document Version**: 2.0
