# C4 Component Diagram - Backend as a Service Platform

```mermaid
flowchart TB
    subgraph backend[Backend Application]
        auth[Auth and Scope Guard]
        projectsApi[Projects API]
        bindingsApi[Bindings API]
        authApi[Auth Facade API]
        dataApi[Data API]
        storageApi[Storage API]
        functionsApi[Functions API]
        eventsApi[Events API]
        adminApi[Admin API]
        migration[Migrations Orchestrator]
        projector[Usage and Audit Projector]
    end

    auth --> projectsApi
    auth --> bindingsApi
    auth --> authApi
    auth --> dataApi
    auth --> storageApi
    auth --> functionsApi
    auth --> eventsApi
    auth --> adminApi
    bindingsApi --> migration
    storageApi --> projector
    functionsApi --> projector
    eventsApi --> projector
    migration --> projector
```

## Component Interaction Addendum

- **Contract Validator Component:** schema validation, version negotiation, idempotency replay.
- **Isolation Guard Component:** scope extraction, policy checks, tenant boundary enforcement.
- **Lifecycle Orchestrator:** manages state transitions for binding, migration, release.
- **Error Mapper:** normalizes adapter/provider errors to platform taxonomy.
- **SLO Publisher:** emits per-request metrics tagged by tenant/project/env/capability.
