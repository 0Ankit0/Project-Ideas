# Subscription Billing and Entitlements Platform Design Documentation

> Comprehensive system design documentation for recurring pricing, usage metering, invoicing, dunning, and entitlement enforcement.

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
- **Billing Admin** - participates in Subscription Billing workflows
- **Finance Analyst** - participates in Subscription Billing workflows
- **Subscriber Admin** - participates in Subscription Billing workflows
- **Product Manager** - participates in Subscription Billing workflows
- **Support Specialist** - participates in Subscription Billing workflows

### Key Features
- Subscription creation and renewal with auditability and operational controls
- Usage ingestion and rating with auditability and operational controls
- Invoice generation and collection with auditability and operational controls
- Dunning retry orchestration with auditability and operational controls
- Entitlement grant and revoke with auditability and operational controls


## Cross-Cutting Deep-Dive Additions

- [Requirements: Plan/versioning + lifecycle controls](./requirements/plan-versioning-and-lifecycle-requirements.md)
- [Analysis: Entitlement and reconciliation flows](./analysis/reconciliation-and-entitlement-flows.md)
- [HLD: Billing lifecycle and commercial versioning](./high-level-design/billing-lifecycle-and-versioning.md)
- [Detailed design: Versioning, invoice/proration, entitlements, recovery](./detailed-design/plan-versioning-invoice-proration-entitlements.md)
- [Infrastructure: Reconciliation and recovery architecture](./infrastructure/reconciliation-and-recovery-architecture.md)
- [Implementation: Reconciliation and recovery playbook](./implementation/reconciliation-and-recovery-playbook.md)

## Diagram Generation

Diagrams are authored in Mermaid where applicable; export via VS Code Mermaid preview, mermaid.live, or Mermaid CLI.

## Getting Started

1. Read `requirements/requirements.md` and `requirements/user-stories.md` to confirm scope and release boundaries.
2. Follow `analysis/` and `high-level-design/` to understand system boundaries, dependencies, and architecture choices.
3. Use `detailed-design/` and `implementation/` to plan engineering breakdown, milestones, and readiness checks.
4. Review `edge-cases/` before implementation to include detection and recovery logic in initial delivery.

## Documentation Status

- ✅ Full Wave 1 documentation scaffold is present for this project.
- ✅ Includes domain deep-dive (`detailed-design/usage-metering-and-entitlements.md`) and operational edge-case pack.
- ⏳ Keep diagrams and status matrix synchronized with implementation changes.

## Beginner Reading Guide
If you are new to subscription systems, use this order:
1. **Start with requirements** to learn what the business needs and why controls exist.
2. **Read analysis** to see business flow and ownership (finance, billing, support).
3. **Read high-level design** to understand how services collaborate.
4. **Read detailed design** for schemas, APIs, and algorithms.
5. **Read infrastructure and implementation** to understand operations, alerts, and rollout.

### Core Terms (Quick Glossary)
- **Plan**: a product package sold to a customer (e.g., Pro).
- **Plan Version**: a frozen snapshot of plan rules/prices used for audit-safe history.
- **Proration**: partial-cycle credit/debit when a customer changes plan mid-cycle.
- **Entitlement**: what the customer is allowed to access right now.
- **Reconciliation**: process that verifies billing, payments, ledger, and entitlements agree.

