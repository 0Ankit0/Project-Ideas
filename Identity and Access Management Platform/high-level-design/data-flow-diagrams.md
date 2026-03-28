# Data Flow Diagrams

## Authentication and Token Flow
```mermaid
flowchart LR
    Client[Client App] --> Authz[/authorize]
    Authz --> Login[Credential + MFA Validation]
    Login --> Code[Authorization Code]
    Code --> Token[/token Exchange]
    Token --> Access[(Access/Refresh Tokens)]
    Access --> Resource[Protected API]
```

## Provisioning and Audit Flow
```mermaid
flowchart LR
    Source[HR/SCIM Event] --> Provision[Provisioning Service]
    Provision --> IdentityStore[(Identity Store)]
    Provision --> EventBus[(Event Bus)]
    EventBus --> Audit[Audit Aggregator]
    Audit --> SIEM[SIEM/SOC]
```
