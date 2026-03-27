# Identity and Access Management Platform Design Documentation

> Comprehensive system design documentation for authentication, federation, authorization policy evaluation, SCIM, and recovery.

## Documentation Structure

| Phase | Folder | Description |
|---|---|---|
| 1 | [requirements](./requirements/) | Scope, FR/NFR, acceptance criteria, and user stories |
| 2 | [analysis](./analysis/) | Actors, use cases, context boundaries, activity/swimlane flows |
| 3 | [high-level-design](./high-level-design/) | Architecture decisions, domain model, sequence and DFD views |
| 4 | [detailed-design](./detailed-design/) | Internal components, data models, APIs, lifecycle/state behavior |
| 5 | [infrastructure](./infrastructure/) | Deployment topology, networking, security, cloud primitives |
| 6 | [implementation](./implementation/) | Delivery plan, code organization, and backend capability matrix |

## System Overview

### Actors
- **End User** - participates in IAM workflows
- **Identity Admin** - participates in IAM workflows
- **Security Engineer** - participates in IAM workflows
- **Application Owner** - participates in IAM workflows
- **Auditor** - participates in IAM workflows

### Key Features
- Authentication and session lifecycle with auditability and operational controls
- Token issuance and revocation with auditability and operational controls
- Federation login with auditability and operational controls
- Scim provisioning and deprovisioning with auditability and operational controls
- Policy decision evaluation with auditability and operational controls

## Diagram Generation

Diagrams are authored in Mermaid where applicable; export via VS Code Mermaid preview, mermaid.live, or Mermaid CLI.

## Getting Started

1. Read `requirements/requirements.md` and `requirements/user-stories.md` to confirm scope and release boundaries.
2. Follow `analysis/` and `high-level-design/` to understand system boundaries, dependencies, and architecture choices.
3. Use `detailed-design/` and `implementation/` to plan engineering breakdown, milestones, and readiness checks.
4. Review `edge-cases/` before implementation to include detection and recovery logic in initial delivery.

## Documentation Status

- ✅ Full Wave 1 documentation scaffold is present for this project.
- ✅ Includes domain deep-dive (`detailed-design/policy-engine-and-federation.md`) and operational edge-case pack.
- ⏳ Keep diagrams and status matrix synchronized with implementation changes.
