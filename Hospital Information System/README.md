# Hospital Information System Design Documentation

> Comprehensive system design documentation for patient identity, admissions, clinical orders, care workflows, and discharge.

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
- **Patient Access Clerk** - participates in Hospital workflows
- **Physician** - participates in Hospital workflows
- **Nurse** - participates in Hospital workflows
- **Care Coordinator** - participates in Hospital workflows
- **Compliance Auditor** - participates in Hospital workflows

### Key Features
- Patient registration and identity resolution with auditability and operational controls
- Admission-transfer-discharge with auditability and operational controls
- Order placement and fulfillment with auditability and operational controls
- Care documentation and handoff with auditability and operational controls
- Discharge and follow-up coordination with auditability and operational controls

## Diagram Generation

Diagrams are authored in Mermaid where applicable; export via VS Code Mermaid preview, mermaid.live, or Mermaid CLI.

## Getting Started

1. Read `requirements/requirements.md` and `requirements/user-stories.md` to confirm scope and release boundaries.
2. Follow `analysis/` and `high-level-design/` to understand system boundaries, dependencies, and architecture choices.
3. Use `detailed-design/` and `implementation/` to plan engineering breakdown, milestones, and readiness checks.
4. Review `edge-cases/` before implementation to include detection and recovery logic in initial delivery.

## Documentation Status

- ✅ Full Wave 1 documentation scaffold is present for this project.
- ✅ Includes domain deep-dive (`detailed-design/clinical-records-and-care-workflows.md`) and operational edge-case pack.
- ⏳ Keep diagrams and status matrix synchronized with implementation changes.
