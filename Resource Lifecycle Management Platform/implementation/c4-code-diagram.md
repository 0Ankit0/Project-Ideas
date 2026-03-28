# C4 Code Diagram

```mermaid
flowchart TB
  ResourceRequestController --> ResourceRequestAppService --> ResourceRequestAggregate
  ResourceRequestAppService --> PolicyEvaluator
  ResourceRequestAppService --> ResourceRepository
  LifecycleWorker --> CloudProvisioningAdapter
  LifecycleWorker --> EventPublisher
```
