# C4 Code Diagram

This code-level view expands lifecycle orchestration modules for provisioning, updates, and retirement.

## Code-Level Structure
```mermaid
flowchart TB
  subgraph Interface
    ResourceRequestController
    LifecycleController
    ApprovalController
  end

  subgraph Application
    ResourceRequestAppService
    LifecycleAppService
    ApprovalAppService
    WorkflowAppService
  end

  subgraph Domain
    ResourceRequestAggregate
    ResourceAggregate
    LifecyclePolicy
    ApprovalRule
  end

  subgraph Infrastructure
    ResourceRepository
    RequestRepository
    CloudProvisioningAdapter
    CMDBAdapter
    EventPublisher
  end

  ResourceRequestController --> ResourceRequestAppService --> ResourceRequestAggregate
  LifecycleController --> LifecycleAppService --> ResourceAggregate
  ApprovalController --> ApprovalAppService --> ApprovalRule
  LifecycleAppService --> WorkflowAppService --> LifecyclePolicy
  ResourceRequestAppService --> RequestRepository
  LifecycleAppService --> ResourceRepository
  WorkflowAppService --> CloudProvisioningAdapter
  LifecycleAppService --> CMDBAdapter
  LifecycleAppService --> EventPublisher
```

## Critical Runtime Sequence: Provision Resource
```mermaid
sequenceDiagram
  autonumber
  actor Requestor
  participant API as ResourceRequestController
  participant APP as LifecycleAppService
  participant CLOUD as CloudProvisioningAdapter
  participant CMDB as CMDBAdapter

  Requestor->>API: request provision
  API->>APP: validate + start workflow
  APP->>CLOUD: provision resource
  CLOUD-->>APP: resource identifiers
  APP->>CMDB: register asset
  APP-->>API: provision complete
```

## Notes
- Persist workflow state transitions for replay and audit.
- Keep cloud adapter actions idempotent using request correlation identifiers.
