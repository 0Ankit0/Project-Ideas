# Event Catalog

This catalog lists high-value domain events for Rental Management System. Events should be immutable, timestamped, and correlated to a business entity.

## Event Design Conventions
- Naming: `domain.entity.action.v1`
- Include `event_id`, `correlation_id`, `occurred_at`, `actor`, and `source`.
- Include previous and new state when a transition occurs.

## Core Events
| Event | Trigger | Consumers |
|---|---|---|
| `lifecycle.record.created.v1` | New business record is initialized | Workflow engine, analytics |
| `lifecycle.record.state_changed.v1` | Record state transition succeeds | Notifications, reporting, audit |
| `lifecycle.record.exception_raised.v1` | Rule conflict or validation failure | Operations console, alerting |
| `lifecycle.record.exception_resolved.v1` | Recovery/mitigation completed | Monitoring, SLA dashboards |
| `lifecycle.record.closed.v1` | Record reaches terminal/settled state | Billing, archives, compliance export |

## Reliability Expectations
- Producers must support at-least-once delivery with idempotent consumers.
- Replay should be possible by date range and correlation id.
- Dead-letter handling must preserve payload and error context for triage.
