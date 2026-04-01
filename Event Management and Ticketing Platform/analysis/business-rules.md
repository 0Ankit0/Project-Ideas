# Business Rules — Event Management and Ticketing Platform

## Enforceable Rules

### BR-001: Hold Timeout

When an attendee initiates checkout, selected tickets are placed in a hold state to reserve
inventory temporarily. Each hold is registered in Redis with a TTL of exactly 600 seconds
(10 minutes). The corresponding `Ticket.status` transitions to `held` and
`TicketType.quantity_held` is incremented atomically using a Lua script to prevent race conditions
under concurrent load.

Hold expiry is enforced at three points in the system. First, at ticket selection, the inventory
service checks for a valid Redis hold key before creating a new hold and rejects stale requests
immediately. Second, at checkout form submission, the order service re-validates the hold TTL
before initiating payment capture with Stripe. Third, a background worker subscribes to Redis
keyspace expiry notifications and also polls every 60 seconds to flip any orphaned `Ticket` records
from `held` to `cancelled`, decrementing `quantity_held` accordingly.

Requests that attempt to proceed to payment on an expired hold receive HTTP `410 Gone` with a
structured error body containing `error_code: HOLD_EXPIRED`. The response instructs the client
to restart the checkout flow from the ticket selection screen. Hold extensions are not supported
to prevent inventory squatting by bots or scalpers.

### BR-002: Refund Eligibility Window

Refund eligibility is governed by two fields on `Event`: `refund_policy` and
`refund_cutoff_hours`. When `refund_policy` is `none`, all refund requests are rejected regardless
of timing with `error_code: REFUNDS_NOT_ALLOWED`. When the policy is `full` or `partial`, the
window closes when `now() >= event.start_time - (refund_cutoff_hours * 3600)`. Requests received
after the cutoff return HTTP `422 Unprocessable Entity` with `error_code: REFUND_WINDOW_CLOSED`.

Event cancellation overrides all organizer-defined policies. When `Event.status` transitions to
`cancelled`, the refund service initiates automatic full refunds for all orders in `confirmed`
status. These system-initiated refunds bypass the cutoff window check and are tagged with
`reason: event_cancelled` and `refund_method: original_payment_method`. Orders that already
received partial refunds under a `partial` policy receive top-up refunds for the outstanding
balance.

Refund requests are processed as asynchronous jobs. The worker calls Stripe's Refund API and
updates `Refund.status` to `processed` on success or `failed` on gateway error. Failed refunds
are retried with exponential backoff (initial delay 30 s, multiplier 2, max 3 attempts). After
the third failure the record is permanently marked `failed` and the operations team is alerted
via PagerDuty.

### BR-003: Dynamic Pricing Triggers

The dynamic pricing engine evaluates three independent triggers against each `TicketType`. Trigger
(a) activates when inventory scarcity is detected: `quantity_available / quantity_total < 0.20`.
Trigger (b) activates on temporal urgency: when `event.start_time - now() < threshold_days * 86400`
(default threshold: 7 days, organizer-configurable). Trigger (c) activates on demand velocity:
when the rolling ticket-sale rate exceeds 50 tickets per hour for three or more consecutive
one-hour measurement windows.

When any trigger fires, the engine computes a multiplier and updates `TicketType.price`. Price
increases are hard-capped at `3 × base_price`, where `base_price` is the value recorded when the
ticket type was first activated for sale. Price decreases cannot fall below a `cost_floor` value
the organizer specifies per ticket type. All price changes are appended to the `price_history`
table recording the trigger reason, previous price, new price, and UTC timestamp.

Organizers may opt out of dynamic pricing per ticket type by setting
`dynamic_pricing_enabled = false`. When disabled no automated adjustments occur, but organizers
may still change prices manually via the dashboard. Manually set prices bypass the multiplier cap
but remain bounded by the cost floor.

### BR-004: Transfer Rules

Ticket transfers are permitted only when `TicketType.is_transferable = true`. The transfer
initiates a state machine transition: the source ticket moves to `transferred`, a new `Ticket`
record is created with `transferred_from_ticket_id` pointing to the source, and a fresh QR code
hash is generated using a new HMAC signature keyed on the new ticket ID. The original QR hash is
invalidated immediately; any scan of the old code returns HTTP `410 Gone`.

Transfers are blocked when fewer than 120 minutes remain before `Event.start_time`. The transfer
service validates this constraint at request time using UTC arithmetic and returns
`error_code: TRANSFER_WINDOW_CLOSED` when violated. Transfers also require the destination to be
a fully registered platform account; transfers to unregistered email addresses are not supported.
Free (comped) tickets — defined as `TicketType.price = 0` with `is_transferable` explicitly set
to `false` at creation — are non-transferable by default.

Each ticket may be transferred at most once. The transfer service verifies
`transferred_from_ticket_id IS NULL` on the source ticket before proceeding. A ticket that is
already itself the product of a transfer cannot be re-transferred. All transfer events are
written to the audit log with both the source and destination attendee IDs and the timestamp.

### BR-005: No-Show Policy

An attendee is classified as a no-show when their ticket has no `CheckIn` record within 30 minutes
after `Event.start_time`. The no-show detection job runs at `start_time + 30 minutes`, scanning
all `Ticket` records in `confirmed` status for the event that lack a corresponding `CheckIn` row,
and transitions those tickets to `status = no_show` tracked in `ticket_metadata`.

No-show tickets are ineligible for refunds. When the refund service evaluates a request for a
no-show ticket it returns HTTP `422` with `error_code: NO_SHOW_INELIGIBLE`. Organizers configure
whether vacated no-show slots are released back to available inventory via
`Event.release_noshows` (boolean, default `false`). For general admission events with
`release_noshows = true`, `TicketType.quantity_sold` is decremented, increasing
`quantity_available` and unblocking any waitlist sales pipeline.

### BR-006: Capacity Limits

The combined count of `Ticket` records in `held`, `confirmed`, and `used` status for an event
must never exceed `Event.max_capacity`. Capacity is tracked in real time by the inventory service
via a Redis counter keyed as `capacity:{event_id}`. The counter is incremented atomically at hold
creation using a Lua script and decremented when holds expire or tickets are cancelled.

When the counter reaches `floor(0.95 * max_capacity)`, the inventory service publishes a
`CapacityThresholdReached` domain event with `thresholdPercent: 95`. When the counter reaches
`max_capacity`, all new hold creation requests return HTTP `409 Conflict` with
`error_code: EVENT_SOLD_OUT` and `Event.status` transitions to `sold_out`. This transition is
idempotent; concurrent requests for the final remaining seats are serialised through a Redis
distributed lock with a 5-second acquisition timeout.

### BR-007: Organizer Payout Rules

Organizer payouts are disbursed a configurable number of calendar days after `Event.end_time`.
The default hold period is 7 days; organizers may configure between 7 and 30 days via
`Event.payout_hold_days`. The payout worker runs daily and selects events where
`end_time + (payout_hold_days * 86400 seconds) <= now()` and `payout_released_at IS NULL` and
no `Refund` records for the event are in `pending` or `processing` status.

Platform fees are deducted before disbursement. The net payout is
`SUM(orders.subtotal) - SUM(orders.platform_fee) + SUM(orders.tax)` for all confirmed orders,
minus the total of all processed refunds. Stripe Connect is used for disbursement; the organizer's
connected Stripe account must be fully verified before a payout can be initiated.

OFAC sanctions screening runs against the organizer's legal name and bank details before every
payout. The payout is held in `blocked_pending_screening` state until a `clear` result is received
from the screening provider (SLA: 60 seconds for automated checks, 24 hours for manual review
escalations). Payouts are additionally blocked when an active Stripe dispute (chargeback) exists
on any `PaymentIntent` associated with the event.

### BR-008: Duplicate Scan Prevention

Each `Ticket` may produce exactly one `CheckIn` record. The `check_ins.ticket_id` column carries a
`UNIQUE` database constraint as a final safety net, but primary enforcement happens at the
application layer: the check-in service executes `SELECT ... FOR UPDATE` on the ticket row,
verifies `status = confirmed`, and transitions status to `used` atomically before inserting the
`CheckIn` record within the same database transaction.

A second scan attempt for a ticket already in `used` status returns HTTP `409 Conflict`. The
response body includes the original `scanned_at` timestamp, `scanner_device_id`, and `gate_id`.
Scanner devices display a clearly differentiated "ALREADY SCANNED" screen showing the first scan's
metadata, which deters both honest mistakes and fraud attempts at the gate.

Offline scan conflicts — where two devices scan the same ticket while disconnected from the
network — are resolved during the sync phase. The first `CheckIn` record uploaded to the server
wins. Subsequent conflicting records are stored with `sync_status = conflict` and routed to a
supervisor review queue in the organizer dashboard. Supervisors may dismiss the conflict after
reviewing device logs or escalate for fraud investigation.

### BR-009: Max Tickets Per Order

The quantity of tickets of any single `TicketType` within one order may not exceed
`TicketType.max_per_order`. This limit is enforced at hold creation: if the requested quantity
exceeds `max_per_order`, the hold service returns HTTP `400 Bad Request` with
`error_code: QUANTITY_EXCEEDS_LIMIT`. The check also applies to incremental cart updates before
checkout is confirmed.

A global per-attendee cap of 20 tickets per event across all ticket types is enforced to deter
bulk purchasing for resale. The inventory service computes `confirmed_count_for_attendee +
requested_quantity` and rejects the hold if the result exceeds the cap. The global cap is
configurable per event by platform administrators via `Event.attendee_ticket_cap`.

### BR-010: Coupon Code Validation

Coupon codes are validated synchronously at checkout initiation, before the hold is committed to
Redis. The coupon service checks five conditions in sequence: (a) the code exists and is active;
(b) the code is within its validity window (`valid_from <= now() <= valid_until`); (c) remaining
usage count is greater than zero (`usage_count < max_uses`); (d) the code is applicable to the
event (event-scoped or global); (e) the requesting attendee has not already used this code.

Usage count is incremented atomically via a Redis counter with a database write-behind, preventing
race conditions when multiple attendees redeem the same code simultaneously. Coupon discounts
cannot reduce an order total below zero; any excess discount is silently capped at the order
subtotal. If validation fails, checkout continues without the discount and a non-blocking warning
is returned in the response so the attendee can correct the code.

### BR-011: Age Restriction Verification

When `Event.age_restriction` is set, attendees must provide their date of birth during checkout.
Age is computed as `floor((now() - date_of_birth) / 365.25)`. If the computed age is below
`age_restriction`, the checkout request is rejected with HTTP `403 Forbidden` and
`error_code: AGE_RESTRICTION_NOT_MET`. Date of birth is stored on the `Attendee` record as a
`DATE` column and is never surfaced in public API responses.

At-door age verification remains the responsibility of event staff. The check-in app displays an
age-verification badge indicating whether the attendee passed the digital check. For
high-compliance events (e.g., 21+ venues in the US), organizers may enable
`require_id_verification = true`, which triggers a third-party identity verification flow before
the ticket is confirmed.

### BR-012: Organizer Verification Before Publishing

An event may not transition from `draft` to `published` unless all five conditions hold:
(a) the organizer's email address is verified; (b) a valid payment destination (Stripe Connect
account) is linked and fully onboarded; (c) the event record passes structural validation —
non-empty title, `end_time > start_time`, and at least one `TicketType` in `active` status;
(d) a `Venue` is specified for `in_person` and `hybrid` events; (e) a `streaming_url` is
provided for `virtual` and `hybrid` events.

The publish endpoint evaluates all conditions synchronously and returns a structured array of
violations if any condition fails, allowing the organizer to correct multiple issues in one pass.
Large-capacity events (total `TicketType.quantity_total > 5000`) trigger an additional
platform-review step, placing the event in a `pending_review` sub-state visible only to admins.
The event is not discoverable or purchasable until a platform reviewer approves and advances
it to `published`.

## Rule Evaluation Pipeline

The following diagram shows the sequential gate checks the inventory service performs during
hold creation. A request must pass every gate to receive a valid hold; failure at any gate short-
circuits the flow with the corresponding error response.

```mermaid
flowchart TD
    A([Hold Request Received]) --> B{Organizer verified?\nBR-012}
    B -- No --> E1([403 Organizer Not Verified])
    B -- Yes --> C{Event status = on_sale?}
    C -- No --> E2([409 Event Not On Sale])
    C -- Yes --> D{Capacity available?\nBR-006}
    D -- No --> E3([409 Event Sold Out])
    D -- Yes --> F{qty <= max_per_order?\nBR-009}
    F -- No --> E4([400 Quantity Exceeds Limit])
    F -- Yes --> G{Attendee ticket cap OK?\nBR-009}
    G -- No --> E5([400 Attendee Cap Exceeded])
    G -- Yes --> H{Age restriction met?\nBR-011}
    H -- No --> E6([403 Age Restriction Not Met])
    H -- Yes --> I{Sale window open?\nTicketType.sale_start_at}
    I -- No --> E7([422 Tickets Not Yet On Sale])
    I -- Yes --> J{Coupon provided?}
    J -- Yes --> K[Validate coupon\nBR-010]
    K -- Invalid --> L[Continue without discount]
    K -- Valid --> M[Apply discount to session]
    L --> N[Atomically increment\nquantity_held in DB]
    M --> N
    J -- No --> N
    N --> O[Set Redis key\nhold:{holdId} TTL=600s]
    O --> P[Publish TicketHoldCreated\ndomain event]
    P --> Q([201 Hold Created])
```

## Exception and Override Handling

### Admin Overrides

Platform administrators may bypass any enforceable rule by attaching a signed override token to
their API request. Override tokens are issued through the admin console after the administrator
supplies a mandatory justification text (minimum 20 characters). Each token encodes the set of
rule IDs being bypassed, the issuing admin's ID, the target resource (event ID, order ID, or
wildcard), and a TTL (default 30 minutes, configurable up to 4 hours for scheduled maintenance
windows).

Override tokens are validated by the relevant service on every request; an expired token causes
the operation to fail cleanly without partial state changes. Tokens cannot be delegated or
re-issued by non-admin principals. Every invocation of an override token appends a row to the
`audit_log` with `is_override = true`, the rule IDs bypassed, the justification text, the token
TTL, and the outcome (success or failure with reason).

### Organizer Overrides

Organizers may apply a limited set of self-service overrides scoped to their own events. Eligible
overrides are: extending the refund window by up to 48 hours beyond the configured cutoff
(BR-002); extending the transfer window by up to 60 minutes before event start (BR-004); and
adjusting the payout hold period within the 7–30 day range (BR-007). Organizer overrides take
effect immediately but are subject to a 24-hour platform review window during which an
administrator may revoke the override if it violates the terms of service.

Organizer overrides are recorded in `audit_log` with actor role `organizer`, the rule ID, the
original value, the overridden value, and a UTC timestamp. Revoked overrides revert the affected
field to its previous value and send an email notification to the organizer explaining the reason
for revocation.

### Escalation Paths

When a rule conflict cannot be resolved through self-service, the organizer submits a manual
support ticket via the help portal. The support ticket is linked to the affected event and order
IDs and routed to the operations team queue. Operations staff may apply an admin override after
reviewing the request, with the justification text logged in both the support ticket and the
audit trail.

Financial disputes (chargebacks, large refund requests, OFAC screening holds) escalate to a
dedicated finance review queue that integrates with the internal ticketing system. The finance
team has a 4-hour SLA to respond to payout-blocking disputes during business hours and a
24-hour SLA outside business hours. Escalated disputes that remain unresolved after 7 calendar
days trigger an automated notification to the platform's Head of Finance.

## Enforced Rule Summary

1. Ticket holds expire after 10 minutes; unreleased holds are automatically returned to inventory.
2. Refunds are only permitted up to 48 hours before event start; no refunds within 48 hours except for cancellations.
3. Dynamic pricing surges are capped at 3x base price; surge triggers when inventory drops below 20%.
4. Ticket transfers require both parties to be registered users; transfers are blocked within 24 hours of event.
5. No-show for reserved seating releases the seat to standby list 30 minutes after event start.
6. Venue capacity hard limits cannot be exceeded; overselling is blocked at the inventory service level.
7. Organiser payouts are processed 5 business days after event completion pending dispute window.
8. High-demand onsales require virtual waiting room activation when concurrent checkout demand exceeds 500 users.
