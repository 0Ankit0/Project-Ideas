# User Stories

## Traceability
- Requirements baseline: [`./requirements.md`](./requirements.md)
- Business rules: [`../analysis/business-rules.md`](../analysis/business-rules.md)
- Delivery design: [`../detailed-design/delivery-orchestration-and-template-system.md`](../detailed-design/delivery-orchestration-and-template-system.md)
- Edge handling: [`../edge-cases/README.md`](../edge-cases/README.md)

## Epic A: Transactional Notification Delivery

1. As a product service, I want to submit a transactional message with an idempotency key so retries from my system do not create duplicate customer notifications.
   - Acceptance criteria: duplicate submissions within the deduplication window return the original `message_id`; caller receives current status and correlation ID.
2. As a platform operator, I want transactional messages to bypass campaign throttles so OTP and security alerts are not delayed by promotional traffic.
   - Acceptance criteria: P0 traffic is routed to dedicated priority lanes; queue pressure from P2 traffic does not violate P0 latency SLOs.
3. As a support analyst, I want to trace a message from API request to final provider outcome so I can explain delivery failures without combing through raw logs.
   - Acceptance criteria: query by `message_id` reveals request metadata, dispatch attempts, provider responses, and audit trail.

## Epic B: Template Governance and Localization

4. As a campaign manager, I want to publish versioned templates with locale fallback so the same campaign can render correctly across regions.
   - Acceptance criteria: sends pin immutable template versions; fallback chain is visible in preview and runtime audit metadata.
5. As a compliance reviewer, I want regulated templates to require dual approval so financial and legal messaging cannot be changed unilaterally.
   - Acceptance criteria: publish action is blocked until all required approvers sign off; approval history is immutable.
6. As a developer, I want preview endpoints to validate variables before publish so broken templates fail before reaching production traffic.
   - Acceptance criteria: preview reports missing, type-invalid, and unused variables with field-level diagnostics.

## Epic C: Consent, Suppression, and Preferences

7. As an end user, I want my opt-out preference to stop future promotional messages quickly so I am not spammed after unsubscribing.
   - Acceptance criteria: new promotional sends are blocked within the propagation target; audit trail records opt-out source and time.
8. As a tenant admin, I want per-category and per-channel consent rules so I can comply with regional regulations and business preferences.
   - Acceptance criteria: policy engine evaluates channel, category, geography, and quiet hours before dispatch.
9. As a legal analyst, I want evidence of consent changes and suppression decisions so I can answer regulatory inquiries.
   - Acceptance criteria: export contains actor/source, timestamps, policy reason, and related message impact where available.

## Epic D: Provider Routing and Resilience

10. As an SRE, I want provider failover to preserve message identity so a brownout at one SMS vendor does not create duplicate business events.
   - Acceptance criteria: failover creates a new dispatch attempt under the same `message_id` and idempotency context.
11. As a platform operator, I want weighted routing by geography and channel so I can optimize for reliability, latency, and cost.
   - Acceptance criteria: routing policy is configurable by tenant segment, region, and priority tier.
12. As an engineer, I want callback ingestion to reconcile delayed and duplicate provider callbacks so message status remains correct under provider retries.
   - Acceptance criteria: callback handler verifies signature/replay window and ignores already-processed provider events safely.

## Epic E: Operations and Recovery

13. As an operator, I want DLQ replay to require approval and preserve original message lineage so recovery actions are safe and auditable.
   - Acceptance criteria: replay creates a new dispatch attempt, logs actor/reason, and never mutates the original request record.
14. As an on-call engineer, I want queue backlog and callback delay alerts by priority lane so I can react before transactional traffic violates SLOs.
   - Acceptance criteria: alerts include tenant impact, queue depth, lag, and affected provider/channel dimensions.
15. As a data analyst, I want delivery and conversion events in the warehouse so I can compare provider performance and campaign effectiveness.
   - Acceptance criteria: analytical events are correlated to the canonical `message_id` and delivery lifecycle.

## Non-Functional Story Themes

- Availability: transactional flows remain available during single-provider incidents and single-AZ failures.
- Privacy: message content is minimized in logs, with tokenized identifiers and controlled evidence access.
- Observability: every message lifecycle transition emits correlation IDs and tenant-scoped metrics.

## Definition of Done for Story Completion

- Story acceptance criteria are demonstrable through automated tests, observable runtime signals, or both.
- Operationally sensitive stories include runbook updates and alert definitions.
- Compliance-sensitive stories include audit evidence and retention expectations.
