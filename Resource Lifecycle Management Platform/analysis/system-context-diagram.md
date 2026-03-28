# System Context Diagram

```mermaid
flowchart LR
  Requestor[Requestor] --> RLMP[Resource Lifecycle Management Platform]
  Operator[Platform Operator] --> RLMP
  RLMP --> Cloud[Cloud Providers]
  RLMP --> CMDB[CMDB/Asset Registry]
  RLMP --> IAM[Identity Platform]
  RLMP --> FinOps[Cost/FinOps]
```
