# Data Dictionary

This data dictionary defines the core entities and data semantics for Rental Management System. It focuses on asset availability, booking, contract, condition checks, and settlement.

## Core Domains
- Identity and access (users, roles, tenants/departments)
- Transactions and lifecycle records
- Financial and audit traces
- Notification and integration payloads

## Key Data Quality Rules
- Use immutable identifiers and created/updated timestamps on all top-level entities.
- Record actor/source metadata for every state-changing event.
- Keep monetary values and units explicit (currency, tax mode, rounding policy).
- Store status fields as controlled vocabularies, not free text.

## Critical Entities
| Entity | Purpose | Required Fields |
|---|---|---|
| Account/User | Actor identity and authorization context | `id`, `status`, `role`, `created_at` |
| Primary Record | Central business object for lifecycle tracking | `id`, `state`, `owner_id`, `effective_at` |
| Transaction/Event | Immutable activity journal entry | `event_id`, `entity_id`, `event_type`, `occurred_at` |
| Settlement/Outcome | Financial or operational closure details | `reference_id`, `amount`, `result`, `closed_at` |

## Retention and Audit Notes
- Preserve business and compliance records according to policy windows.
- Ensure audit logs are append-only and queryable by actor, entity, and date range.
