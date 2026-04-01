# Use Case Descriptions — Subscription Billing and Entitlements Platform

## Document Information

| Field | Value |
|---|---|
| Version | 1.0 |
| Domain | Subscription Billing and Entitlements |
| Scope | UC-001 through UC-012 |

---

## UC-001: Subscribe to Plan

| Field | Detail |
|---|---|
| **Use Case ID** | UC-001 |
| **Name** | Subscribe to Plan |
| **Description** | An Account Owner selects a billing plan from the catalog, optionally provides a payment method, and initiates a subscription. The platform creates the subscription record, provisions entitlements, and sends a confirmation notification. If the plan includes a free trial, the subscription begins in trial state without charging the payment method. |
| **Primary Actor** | Account Owner |
| **Secondary Actors** | Payment Gateway, Tax Service, Email Notification Service |
| **Trigger** | Account Owner submits a subscription creation request via the customer portal or API. |

### Preconditions

1. The Account Owner has a verified account with a confirmed email address.
2. The selected plan exists in the active plan catalog with status `ACTIVE`.
3. If the plan requires a payment method, a valid tokenized payment method has been attached to the account (or is submitted as part of this request).
4. The account does not already have an active subscription to the same plan within the same billing group.

### Postconditions

1. A new `Subscription` record exists with status `TRIALING` (if trial enabled) or `ACTIVE`.
2. Entitlements corresponding to the plan's feature grants are provisioned in the Entitlement Service and are immediately accessible.
3. A `SubscriptionStarted` domain event is published to the event bus.
4. A welcome/confirmation email is dispatched to the Account Owner's verified email address.
5. If an initial charge was collected, a `Payment` record exists with status `SUCCEEDED` and a corresponding `Invoice` with status `PAID`.

### Normal Flow

1. Account Owner selects a plan from the plan catalog endpoint (`GET /v1/plans`).
2. Account Owner submits `POST /v1/subscriptions` with `plan_id`, `account_id`, optional `coupon_code`, and optional `payment_method_id`.
3. Platform validates the request: plan exists and is active, account is in good standing, no conflicting active subscription exists.
4. If a coupon code is supplied, the platform validates it (UC-010 invoked as sub-flow). The discount is attached to the subscription.
5. Platform calls the Tax Service with the account's billing address and the plan's product tax code to determine the applicable tax rate.
6. If the plan has no trial and requires immediate payment:
   a. Platform calculates the prorated or full-period charge amount.
   b. Platform generates a draft invoice (`Invoice.status = DRAFT`).
   c. Platform calls `POST /v1/payments` to charge the stored payment method via the Payment Gateway.
   d. On payment success, the invoice is marked `PAID` and a payment receipt event is emitted.
7. Platform creates the `Subscription` record with `status = ACTIVE` (or `TRIALING` if trial applies), setting `current_period_start`, `current_period_end`, `trial_end` (if applicable), and `next_billing_date`.
8. Platform calls the Entitlement Service to provision all feature grants defined in the plan's entitlement template.
9. Platform publishes a `SubscriptionStarted` event.
10. Platform dispatches a confirmation email via the Email Notification Service.
11. Platform returns `201 Created` with the full subscription object.

### Alternative Flows

**AF-001A — Free Trial Subscription (No Immediate Charge)**
At step 6, if the plan includes a trial period (`trial_days > 0`), the platform skips payment collection. The subscription is created with `status = TRIALING`. The `trial_end` field is set to `now + trial_days`. No invoice is generated. The platform schedules a trial expiry job to fire 24 hours before `trial_end`.

**AF-001B — Subscription via API Key (Developer Flow)**
The request is authenticated with an API key rather than a user session. The `account_id` must match the API key's account scope. The flow proceeds identically to the normal flow from step 3 onward.

**AF-001C — Coupon Applied at Subscription Time**
At step 4, if the coupon is valid and applicable to the selected plan, the discount (percentage or fixed amount) is recorded on the subscription. The charge calculated in step 6a reflects the discounted amount. The coupon's `redemption_count` is incremented atomically.

### Exception Flows

**EX-001A — Plan Not Found or Inactive**
At step 3, if the plan does not exist or has status `ARCHIVED` or `INACTIVE`, the platform returns `404 Not Found` with error code `PLAN_NOT_FOUND` or `422 Unprocessable Entity` with `PLAN_INACTIVE`. No subscription is created.

**EX-001B — Payment Method Invalid or Declined**
At step 6c, if the Payment Gateway returns a decline, the platform marks the draft invoice as `PAYMENT_FAILED`, does not create the subscription, and returns `402 Payment Required` with the gateway decline code. The Account Owner is prompted to update their payment method.

**EX-001C — Tax Service Unavailable**
At step 5, if the Tax Service returns an error or times out after the configured retry policy (3 attempts, 2 s backoff), the platform falls back to the account's pre-configured default tax rate. An alert is fired to the operations monitoring system. The subscription proceeds with the fallback rate, and the discrepancy is flagged for manual reconciliation.

**EX-001D — Duplicate Subscription**
At step 3, if an active subscription to the same plan already exists for the account, the platform returns `409 Conflict` with error code `SUBSCRIPTION_ALREADY_EXISTS`.

### Business Rules Referenced

- **BR-001:** A subscription must reference exactly one active plan at any point in time.
- **BR-002:** Trial periods are non-renewable; an account that has previously trialled a plan cannot start a new trial on the same plan.
- **BR-003:** Payment is collected at the start of each billing period (advance billing) unless the plan is configured for arrears billing (usage-based plans).
- **BR-004:** The initial charge amount for a mid-month start is prorated to the end of the current billing period when the plan has `proration_behaviour = PRORATE`.

---

## UC-002: Trial-to-Paid Conversion

| Field | Detail |
|---|---|
| **Use Case ID** | UC-002 |
| **Name** | Trial-to-Paid Conversion |
| **Description** | When a trial subscription reaches its `trial_end` date, the platform automatically attempts to convert the subscription to a paying subscription by collecting the first period's payment. If payment succeeds, the subscription becomes active. If payment fails or no payment method is on file, the platform initiates a grace period and dunning sequence. |
| **Primary Actor** | System Scheduler |
| **Secondary Actors** | Payment Gateway, Email Notification Service |
| **Trigger** | Scheduled job fires at `trial_end - 24h` (warning) and at `trial_end` (conversion attempt). |

### Preconditions

1. A `Subscription` record exists with `status = TRIALING`.
2. The current timestamp is at or past the subscription's `trial_end` timestamp.
3. The plan associated with the subscription requires a payment method for continued access.

### Postconditions

**Success path:** Subscription `status` transitions to `ACTIVE`. A `PAID` invoice exists for the first billing period. Entitlements remain active. A conversion confirmation email is sent.

**Failure path:** Subscription `status` transitions to `PAST_DUE`. Dunning sequence initiates (UC-007). If dunning exhausts all retries, subscription `status` transitions to `CANCELED` and entitlements are revoked.

### Normal Flow

1. At `trial_end - 24 hours`: Scheduler fires the `TrialExpiryWarning` job.
   a. Platform fetches the subscription and verifies `status = TRIALING`.
   b. Platform sends a trial expiry warning email via the Email Notification Service with a "Add payment method" call-to-action.
2. At `trial_end`: Scheduler fires the `TrialExpired` job.
   a. Platform fetches the subscription and re-validates `status = TRIALING` (idempotency guard against manual conversions).
   b. Platform checks whether a default payment method exists on the account.
   c. Platform generates an invoice for the first full billing period at the plan's recurring price.
   d. Platform applies any active subscription-level discounts (coupons, credits) to the invoice.
   e. Platform calls the Tax Service to compute tax on the invoice line items.
   f. Platform calls the Payment Gateway to charge the default payment method.
   g. On payment success: invoice is marked `PAID`, subscription `status` is set to `ACTIVE`, `current_period_start` and `current_period_end` are updated, a `TrialConverted` event is published, and a confirmation email is sent.
3. Platform returns control to the scheduler. The next billing cycle is scheduled at `current_period_end`.

### Alternative Flows

**AF-002A — No Payment Method on File**
At step 2b, if no payment method exists, the platform transitions the subscription to `PAST_DUE` without attempting a charge. An email prompting the Account Owner to add a payment method is sent. The dunning sequence begins at Day 0 (UC-007, AF-007A path).

**AF-002B — Account Owner Converts Manually Before Trial Ends**
If the Account Owner adds a payment method and explicitly converts before `trial_end`, the scheduler job at `trial_end` detects `status ≠ TRIALING` and exits without action.

### Exception Flows

**EX-002A — Payment Declined at Conversion**
At step 2f, if the charge is declined, the platform marks the invoice as `PAYMENT_FAILED`, transitions subscription to `PAST_DUE`, and initiates UC-007.

**EX-002B — Plan Retired During Trial**
If the plan associated with the trial was retired before `trial_end`, the scheduler logs a critical error, halts the job, and pages the on-call team. The subscription is left in `TRIALING` with a `requires_manual_review` flag set.

### Business Rules Referenced

- **BR-002:** Trial periods are non-renewable.
- **BR-005:** A subscription in `PAST_DUE` retains entitlement access for a configurable grace period (default: 3 days) before entitlements are suspended.
- **BR-006:** The trial conversion invoice covers the full upcoming billing period, not the trial period.

---

## UC-003: Upgrade/Downgrade Plan (with Proration)

| Field | Detail |
|---|---|
| **Use Case ID** | UC-003 |
| **Name** | Upgrade / Downgrade Plan with Proration |
| **Description** | An Account Owner or Billing Admin changes a subscription from one plan to another. The platform calculates a prorated credit for unused time on the current plan and a prorated charge for time on the new plan within the current billing period. The entitlement set is updated immediately. |
| **Primary Actor** | Account Owner, Billing Admin |
| **Secondary Actors** | Payment Gateway, Tax Service, Email Notification Service |
| **Trigger** | `PATCH /v1/subscriptions/{id}` with a new `plan_id`. |

### Preconditions

1. The subscription exists with `status = ACTIVE`.
2. The target plan exists with `status = ACTIVE`.
3. The target plan is not the same as the current plan.
4. The account has a valid payment method on file (for upgrades requiring an immediate charge).

### Postconditions

1. The subscription's `plan_id` is updated to the new plan.
2. A prorated invoice or credit note is generated and settled.
3. Entitlements are updated to reflect the new plan's feature grants.
4. A `SubscriptionPlanChanged` event is published.
5. A plan change confirmation email is sent.

### Normal Flow

1. Actor submits `PATCH /v1/subscriptions/{id}` with `{ "plan_id": "<new_plan_id>", "proration_behaviour": "IMMEDIATE" }`.
2. Platform validates: subscription is `ACTIVE`, new plan exists and is `ACTIVE`, new plan ≠ current plan.
3. Platform calculates the proration:
   - `days_remaining = current_period_end - today`
   - `days_in_period = current_period_end - current_period_start`
   - `unused_credit = (current_plan_price / days_in_period) × days_remaining`
   - `new_plan_charge = (new_plan_price / days_in_period) × days_remaining`
   - `net_amount = new_plan_charge - unused_credit`
4. Platform calls the Tax Service with the net proration amount and the account's billing address.
5. If `net_amount > 0` (upgrade — charge the difference):
   a. Platform generates a proration invoice with line items for the credit and charge.
   b. Platform calls the Payment Gateway to charge `net_amount + tax`.
   c. On success, invoice is marked `PAID`.
6. If `net_amount < 0` (downgrade — issue a credit):
   a. Platform generates a credit note for `|net_amount|`.
   b. The credit is applied to the account's credit balance, which offsets future invoices.
7. Platform updates the subscription record: `plan_id = new_plan_id`, `updated_at = now`.
8. Platform calls the Entitlement Service: revokes entitlements no longer in the new plan, provisions entitlements newly granted by the new plan.
9. Platform publishes `SubscriptionPlanChanged` event.
10. Platform dispatches a plan change confirmation email.
11. Platform returns `200 OK` with the updated subscription object.

### Alternative Flows

**AF-003A — Deferred Proration (Effective at Next Billing Cycle)**
If the request includes `"proration_behaviour": "NONE"` or `"NEXT_PERIOD"`, the plan change is scheduled for the `current_period_end`. No proration invoice or credit is generated. Entitlements remain on the current plan until the scheduled effective date. A scheduled change record is written. The Account Owner receives an email confirming the pending change and its effective date.

**AF-003B — Billing Admin Override**
A Billing Admin may override the default proration calculation by supplying an explicit `proration_override_amount`. The system records the override with the admin's identity in the audit log.

### Exception Flows

**EX-003A — Upgrade Charge Declined**
At step 5b, if the payment is declined, the plan change is rolled back. Subscription remains on the current plan. A `PlanChangePaymentFailed` event is published. The Account Owner receives an email prompting them to update their payment method.

**EX-003B — Downgrade Blocked by Entitlement Conflict**
If the new plan's entitlement limits are lower than the account's current usage (e.g., the account has 15 active seats but the new plan allows 10), the platform returns `422 Unprocessable Entity` with error code `ENTITLEMENT_LIMIT_EXCEEDED` and a list of conflicting entitlements. The downgrade is rejected until the account reduces usage below the new plan's limits.

### Business Rules Referenced

- **BR-007:** Proration is calculated in days, not hours, using calendar days.
- **BR-008:** Proration credits resulting from a downgrade are applied to the account credit balance, not refunded to the payment method, unless explicitly requested.
- **BR-009:** Entitlement changes for upgrades are effective immediately. Entitlement changes for downgrades are effective at the scheduled change date (next billing cycle) unless `immediate_downgrade = true` is specified.

---

## UC-004: Record Usage Event

| Field | Detail |
|---|---|
| **Use Case ID** | UC-004 |
| **Name** | Record Usage Event |
| **Description** | A Developer or integrated system sends a metered usage event to the platform. The platform validates the event, aggregates it against the subscription's usage meter, and makes the aggregated value available for invoice generation at the end of the billing period. |
| **Primary Actor** | Developer (API) |
| **Secondary Actors** | None |
| **Trigger** | `POST /v1/usage` with a usage event payload. |

### Preconditions

1. The subscription referenced in the event exists with `status = ACTIVE` or `TRIALING`.
2. The `meter_id` referenced in the event corresponds to a meter defined on the subscription's plan.
3. The API key used for authentication has `usage:write` scope for the referenced account.

### Postconditions

1. A `UsageRecord` is persisted with the event's quantity, timestamp, idempotency key, and metadata.
2. The meter's aggregated value for the current billing period is updated.
3. If the usage causes a threshold breach (configurable alert thresholds), a `UsageThresholdExceeded` event is published.

### Normal Flow

1. Developer calls `POST /v1/usage` with `{ "subscription_id": "...", "meter_id": "...", "quantity": 100, "timestamp": "2024-06-15T14:00:00Z", "idempotency_key": "evt_abc123" }`.
2. Platform authenticates the API key and verifies scope.
3. Platform validates the payload: `subscription_id` and `meter_id` exist and are compatible, `quantity > 0`, `timestamp` is within the current or immediately preceding billing period (late event window: 24 hours).
4. Platform checks the idempotency key against the `UsageRecord` table. If a record with this key already exists, the platform returns `200 OK` with the original record (idempotent response).
5. Platform persists the `UsageRecord`.
6. Platform updates the billing period's usage aggregate for the meter using an atomic increment.
7. Platform checks whether any configured usage alert thresholds (50%, 80%, 100%) have been crossed. If so, a `UsageThresholdExceeded` event is published.
8. Platform returns `201 Created` with the usage record ID and current period aggregate.

### Alternative Flows

**AF-004A — Batch Usage Submission**
Developer calls `POST /v1/usage/batch` with an array of up to 1,000 usage events. The platform processes each event atomically. Partial success is supported: the response includes a per-event result array with success or failure codes. Failed events do not roll back successful ones.

**AF-004B — Late Event (Outside Current Period)**
If the event `timestamp` is more than 24 hours before the current period start (a late event), the platform writes the record with a `late_event = true` flag and a reference to the historical billing period. Late events trigger a reconciliation task to amend the historical invoice with an adjustment invoice.

### Exception Flows

**EX-004A — Meter Not Found**
At step 3, if the `meter_id` does not exist on the referenced plan, the platform returns `422 Unprocessable Entity` with `METER_NOT_FOUND`.

**EX-004B — Subscription Not Active**
If the subscription is in `CANCELED`, `PAUSED`, or `EXPIRED` state, usage events are rejected with `409 Conflict` and error code `SUBSCRIPTION_NOT_METERING`.

### Business Rules Referenced

- **BR-010:** Usage events submitted with identical idempotency keys within a 30-day window are deduplicated.
- **BR-011:** Usage is aggregated using the meter's defined aggregation function: `SUM`, `MAX`, `LAST`, or `COUNT_DISTINCT`.
- **BR-012:** Usage records cannot be deleted; corrections must be submitted as negative-quantity adjustment events.

---

## UC-005: Generate Monthly Invoice

| Field | Detail |
|---|---|
| **Use Case ID** | UC-005 |
| **Name** | Generate Monthly Invoice |
| **Description** | At the end of each billing period, the platform generates an invoice for every active subscription due for renewal. The invoice includes recurring plan fees, usage-based charges, applicable discounts, credits from account balance, and tax. |
| **Primary Actor** | System Scheduler |
| **Secondary Actors** | Tax Service |
| **Trigger** | Billing period end date is reached for a subscription. |

### Preconditions

1. The subscription has `status = ACTIVE` and `next_billing_date = today`.
2. The subscription has not already been invoiced for the current period (idempotency guard).

### Postconditions

1. An `Invoice` record with `status = OPEN` exists for the billing period.
2. All line items (recurring fees, usage charges, discounts, credits, taxes) are correctly calculated and recorded.
3. A `InvoiceGenerated` event is published.
4. Payment collection is initiated (UC-006).

### Normal Flow

1. Scheduler fires `BillingCycleEnd` job for the subscription.
2. Platform fetches the subscription, plan, and all pending adjustments (credit notes, account credit balance).
3. Platform calculates the recurring line item: `plan.unit_price × quantity` (for seat-based plans) or `plan.base_price` (for flat plans).
4. Platform fetches all `UsageRecord` entries for the billing period and calculates usage charges per meter using the plan's pricing tiers (flat, graduated, or volume pricing).
5. Platform applies any active coupon discounts.
6. Platform applies any available account credit balance (up to the invoice subtotal).
7. Platform calls the Tax Service with the itemised line items and the account's billing address to compute taxes per jurisdiction.
8. Platform computes the final invoice total: `subtotal - discounts - credits + tax`.
9. Platform creates the `Invoice` record with `status = OPEN` and all line items.
10. Platform publishes `InvoiceGenerated` event.
11. Platform advances the subscription's `current_period_start` and `current_period_end` to the next billing period.
12. Platform triggers UC-006 (Process Payment) to collect payment immediately.

### Alternative Flows

**AF-005A — Invoice Fully Covered by Credits**
At step 8, if the total after credits and discounts is ≤ 0, the invoice is marked `PAID` with zero amount collected. No payment attempt is made. An invoice receipt is sent.

**AF-005B — Annual Plan Anniversary Invoice**
For annual plans, the scheduler fires annually. The invoice includes the full annual fee. The same proration and discount logic applies.

### Exception Flows

**EX-005A — Tax Service Error**
Tax Service is unavailable. Platform applies the fallback tax rate and flags the invoice with `tax_calculation_method = FALLBACK`. Finance is alerted for manual review.

**EX-005B — Usage Data Incomplete**
If a known usage meter has no records for the period (possible data pipeline delay), the platform waits up to the configured `usage_collection_deadline` (default: 2 hours after period end) before finalising the invoice. After the deadline, the invoice is generated with available data and flagged for potential amendment.

### Business Rules Referenced

- **BR-013:** Invoices are immutable once status transitions past `DRAFT`. Amendments are made via adjustment invoices or credit notes.
- **BR-014:** Graduated pricing tiers are applied cumulatively; volume pricing applies the tier rate to the entire quantity.
- **BR-015:** Account credit balance is applied before any tax is calculated.

---

## UC-006: Process Payment

| Field | Detail |
|---|---|
| **Use Case ID** | UC-006 |
| **Name** | Process Payment |
| **Description** | The platform attempts to collect payment for an open invoice by charging the account's default payment method through the configured Payment Gateway. |
| **Primary Actor** | System Scheduler, Account Owner (manual payment) |
| **Secondary Actors** | Payment Gateway |
| **Trigger** | Invoice status is `OPEN` and payment collection is initiated by the billing cycle job or by the Account Owner clicking "Pay Now". |

### Preconditions

1. An `Invoice` with `status = OPEN` exists with `amount_due > 0`.
2. A default payment method is on file for the account.
3. No payment attempt for this invoice is currently `PENDING`.

### Postconditions

**Success:** Invoice `status = PAID`. Payment record exists with `status = SUCCEEDED`. `SubscriptionRenewed` event is published. Receipt email is sent.

**Failure:** Payment record exists with `status = FAILED`. Invoice remains `OPEN`. Dunning sequence is initiated (UC-007).

### Normal Flow

1. Platform creates a `PaymentAttempt` record with `status = PENDING` and an idempotency key derived from `invoice_id + attempt_number`.
2. Platform calls the Payment Gateway's charge API with the payment method token, amount, currency, and idempotency key.
3. Payment Gateway processes the charge and returns a result synchronously (or via webhook within 30 seconds).
4. On success:
   a. Platform updates `PaymentAttempt.status = SUCCEEDED` and records the gateway transaction ID.
   b. Platform updates `Invoice.status = PAID` and sets `paid_at = now`.
   c. Platform publishes `PaymentSucceeded` event.
   d. Platform dispatches payment receipt email.
5. Platform returns result.

### Alternative Flows

**AF-006A — Manual Payment via Account Owner**
Account Owner calls `POST /v1/invoices/{id}/pay`. Platform validates the invoice is `OPEN` and belongs to the account. Flow continues from step 1.

### Exception Flows

**EX-006A — Payment Declined**
At step 3, gateway returns a decline code. Platform updates `PaymentAttempt.status = FAILED`, records the decline code and reason. Dunning initiates.

**EX-006B — Gateway Timeout**
Gateway does not respond within 30 seconds. Platform marks the attempt `UNKNOWN`. A webhook reconciliation job resolves the status within 5 minutes using the gateway's transaction lookup API.

### Business Rules Referenced

- **BR-016:** Each payment attempt must carry a unique idempotency key. Gateway idempotency prevents double-charging on retry.
- **BR-017:** The platform must never store raw card numbers. All payment method references are tokenized by the Payment Gateway.

---

## UC-007: Handle Failed Payment and Dunning

| Field | Detail |
|---|---|
| **Use Case ID** | UC-007 |
| **Name** | Handle Failed Payment and Dunning |
| **Description** | When a payment attempt fails, the platform initiates a configurable dunning sequence: scheduled automatic retries, customer notifications, and eventual subscription cancellation if all retries are exhausted. |
| **Primary Actor** | System Scheduler |
| **Secondary Actors** | Payment Gateway, Email Notification Service |
| **Trigger** | A `PaymentAttempt` record transitions to `FAILED`. |

### Preconditions

1. An invoice with `status = OPEN` exists with one or more failed payment attempts.
2. The subscription is not already `CANCELED`.

### Postconditions

**Recovery:** Invoice is `PAID`. Subscription remains or returns to `ACTIVE`. Entitlements are restored if suspended.

**Exhaustion:** Subscription is `CANCELED`. Entitlements are revoked. `SubscriptionCanceled` event published with reason `DUNNING_EXHAUSTED`.

### Normal Flow

1. Payment failure event received. Platform sets subscription `status = PAST_DUE`.
2. Platform sends "Payment failed" notification email with invoice link and "Update Payment Method" CTA.
3. Dunning scheduler registers the following retry schedule (configurable):
   - Day 1: Retry #1
   - Day 3: Retry #2
   - Day 7: Retry #3
   - Day 14: Final retry #4
4. At each retry time, platform executes UC-006 against the same open invoice.
5. On any successful retry, platform: sets subscription `status = ACTIVE`, clears the dunning record, sends a recovery confirmation email.
6. If all retries fail, platform transitions subscription `status = CANCELED`, revokes all entitlements via the Entitlement Service, publishes `SubscriptionCanceled`, and sends a cancellation notice.

### Alternative Flows

**AF-007A — Customer Updates Payment Method During Dunning**
Account Owner updates their payment method while in dunning. Platform immediately retries payment on the new method outside the scheduled retry window. If successful, dunning is cleared and the subscription is restored.

### Exception Flows

**EX-007A — Subscription Manually Cancelled During Dunning**
If the Account Owner cancels the subscription while dunning is active, the dunning sequence is terminated. No further retries occur.

### Business Rules Referenced

- **BR-005:** Entitlements are suspended (not revoked) after `grace_period_days` (default: 3) of PAST_DUE status.
- **BR-018:** The dunning schedule is configurable per plan. Enterprise plans default to a 30-day dunning window with 6 retries.

---

## UC-008: Check Entitlement Access

| Field | Detail |
|---|---|
| **Use Case ID** | UC-008 |
| **Name** | Check Entitlement Access |
| **Description** | A Developer queries the Entitlement Service to determine whether an account has access to a specific feature or resource, and what quota limit applies. The response is used to gate feature access within the integrated application. |
| **Primary Actor** | Developer (API) |
| **Secondary Actors** | None |
| **Trigger** | `GET /v1/entitlements/check?account_id={id}&feature_key={key}` |

### Preconditions

1. The account exists and has at least one subscription.
2. The `feature_key` corresponds to a defined feature in the feature catalog.

### Postconditions

1. The caller receives a boolean `has_access` flag and, for metered features, the current usage and limit values.

### Normal Flow

1. Developer calls `GET /v1/entitlements/check?account_id=acct_123&feature_key=api_calls`.
2. Platform authenticates the API key and verifies it has `entitlements:read` scope for the account.
3. Platform queries the Entitlement Service for all active grants matching `account_id + feature_key`.
4. Platform evaluates the grant: checks subscription `status` (must be `ACTIVE` or within grace period), checks feature `enabled = true`, checks quota (`current_usage < limit` for metered features).
5. Platform returns `200 OK` with `{ "has_access": true, "feature_key": "api_calls", "limit": 10000, "current_usage": 4320, "resets_at": "2024-07-01T00:00:00Z" }`.

### Alternative Flows

**AF-008A — Cached Entitlement Response**
For performance, the Entitlement Service caches grant evaluations with a TTL of 60 seconds. Callers can pass `Cache-Control: no-cache` to force a fresh evaluation on critical paths.

### Exception Flows

**EX-008A — No Active Subscription**
If no active subscription grants the feature, platform returns `{ "has_access": false, "reason": "NO_ACTIVE_GRANT" }` with `200 OK`. Callers should not treat this as an error.

**EX-008B — Feature Key Not Found**
`feature_key` does not exist in the catalog. Platform returns `404 Not Found` with `FEATURE_NOT_FOUND`.

### Business Rules Referenced

- **BR-019:** Entitlement checks must complete within 50 ms at the 99th percentile. Results are cached in Redis with a 60-second TTL.
- **BR-020:** An account with `status = PAST_DUE` retains entitlement access during the configured grace period.

---

## UC-009: Issue Credit Note

| Field | Detail |
|---|---|
| **Use Case ID** | UC-009 |
| **Name** | Issue Credit Note |
| **Description** | A Billing Admin or Finance Manager issues a credit note against a paid invoice to acknowledge an overpayment, service disruption, or billing error. The credit is applied to the account's credit balance and offsets future invoices. |
| **Primary Actor** | Billing Admin, Finance Manager |
| **Secondary Actors** | Email Notification Service |
| **Trigger** | `POST /v1/credit-notes` |

### Preconditions

1. The referenced invoice exists with `status = PAID`.
2. The credit amount does not exceed the invoice's paid total.
3. The actor has `credit_notes:write` permission.

### Postconditions

1. A `CreditNote` record exists referencing the original invoice.
2. The account's credit balance is incremented by the credit amount.
3. A `CreditNoteIssued` event is published.
4. The Account Owner receives a credit note notification email.

### Normal Flow

1. Actor submits `POST /v1/credit-notes` with `{ "invoice_id": "inv_123", "amount": 50.00, "reason": "SERVICE_DISRUPTION", "memo": "Compensating for 4-hour outage on 2024-06-12" }`.
2. Platform validates permissions, invoice existence, and credit amount.
3. Platform creates `CreditNote` with `status = ISSUED` and increments `account.credit_balance` atomically.
4. Platform publishes `CreditNoteIssued` event.
5. Platform dispatches credit note email with PDF attachment.
6. Platform returns `201 Created` with the credit note object.

### Business Rules Referenced

- **BR-021:** Credit notes are immutable after creation. To reverse a credit note, a debit adjustment must be created referencing the credit note.
- **BR-022:** Credit balance is consumed in FIFO order across invoices.

---

## UC-010: Apply Coupon Code

| Field | Detail |
|---|---|
| **Use Case ID** | UC-010 |
| **Name** | Apply Coupon Code |
| **Description** | An Account Owner or Billing Admin applies a coupon code to a subscription or checkout flow. The coupon provides a discount (percentage or fixed amount) for a defined duration. |
| **Primary Actor** | Account Owner, Billing Admin |
| **Secondary Actors** | None |
| **Trigger** | Coupon code field submitted during subscription creation or via `POST /v1/subscriptions/{id}/coupons`. |

### Preconditions

1. The coupon code exists with `status = ACTIVE`.
2. The coupon has not exceeded its `max_redemptions` limit.
3. The coupon's `expires_at` is in the future (or null for no expiry).
4. The coupon is applicable to the target plan (if plan-restricted).
5. The account has not previously redeemed this coupon (if single-use-per-account).

### Postconditions

1. A `CouponRedemption` record exists linking the coupon to the subscription.
2. The coupon's `redemption_count` is incremented.
3. Future invoices for the subscription reflect the discount for the coupon's duration.

### Normal Flow

1. Actor submits the coupon code.
2. Platform validates the coupon: active, not expired, redemption limit not reached, plan compatibility, account-level uniqueness.
3. Platform creates `CouponRedemption` record and atomically increments `coupon.redemption_count`.
4. Platform attaches the discount to the subscription's discount list.
5. Platform returns the validated discount details: `{ "coupon_id": "...", "discount_type": "PERCENTAGE", "discount_value": 20, "duration": "REPEATING", "duration_in_months": 3 }`.

### Exception Flows

**EX-010A — Coupon Expired or Exhausted**
Platform returns `422 Unprocessable Entity` with `COUPON_INVALID` and the specific reason (`EXPIRED`, `REDEMPTION_LIMIT_REACHED`, `ALREADY_REDEEMED`).

### Business Rules Referenced

- **BR-023:** Multiple coupons cannot be stacked on the same subscription unless the coupons have `stackable = true`.
- **BR-024:** Coupon discounts are applied after account credit balance and before tax calculation.

---

## UC-011: Pause and Resume Subscription

| Field | Detail |
|---|---|
| **Use Case ID** | UC-011 |
| **Name** | Pause and Resume Subscription |
| **Description** | An Account Owner pauses their subscription, halting billing and optionally suspending entitlements for a specified period. The subscription can be manually resumed or automatically resumed at a configured date. |
| **Primary Actor** | Account Owner, Billing Admin |
| **Secondary Actors** | Email Notification Service |

### Preconditions (Pause)

1. Subscription `status = ACTIVE`.
2. The plan allows pausing (`plan.allow_pause = true`).
3. The pause duration does not exceed the plan's maximum pause period (default: 90 days).

### Normal Flow — Pause

1. Actor submits `POST /v1/subscriptions/{id}/pause` with optional `{ "resume_at": "2024-09-01" }`.
2. Platform validates the request and calculates the pause end date.
3. Platform sets subscription `status = PAUSED`, records `paused_at` and `resume_at`.
4. Platform suspends entitlements (access denied without revoking grants).
5. Platform advances `next_billing_date` to `resume_at`.
6. Platform sends a pause confirmation email.

### Normal Flow — Resume

1. Actor submits `POST /v1/subscriptions/{id}/resume` or the scheduler fires at `resume_at`.
2. Platform sets subscription `status = ACTIVE`, clears `paused_at`.
3. Platform restores entitlement access.
4. Platform recalculates `next_billing_date` based on the resumed billing cycle.
5. Platform sends a resume confirmation email.

### Business Rules Referenced

- **BR-025:** Billing does not accrue during a pause. The billing period is extended by the pause duration.
- **BR-026:** Accounts are limited to 2 pause events per rolling 12-month period.

---

## UC-012: Cancel Subscription

| Field | Detail |
|---|---|
| **Use Case ID** | UC-012 |
| **Name** | Cancel Subscription |
| **Description** | An Account Owner or Billing Admin cancels a subscription. Cancellation may be immediate or at the end of the current billing period. Upon effective cancellation, entitlements are revoked and billing stops. |
| **Primary Actor** | Account Owner, Billing Admin |
| **Secondary Actors** | Email Notification Service |

### Preconditions

1. Subscription `status` is `ACTIVE`, `TRIALING`, or `PAST_DUE`.

### Postconditions

1. Subscription `status = CANCELED`.
2. All entitlements are revoked.
3. `SubscriptionCanceled` event is published.
4. Cancellation confirmation email is sent.

### Normal Flow

1. Actor submits `DELETE /v1/subscriptions/{id}` with optional `{ "cancel_at_period_end": true }`.
2. If `cancel_at_period_end = true`: Platform sets `cancel_at = current_period_end` and `status` remains `ACTIVE` until that date. Account retains access until period end.
3. If `cancel_at_period_end = false`: Immediate cancellation. Subscription transitions to `CANCELED`. Entitlements are revoked immediately.
4. Platform publishes `SubscriptionCanceled` event with reason `CUSTOMER_REQUESTED`.
5. Platform sends cancellation confirmation email with reactivation link (valid for 30 days).

### Alternative Flows

**AF-012A — Reactivation Within 30 Days**
If the Account Owner reactivates within 30 days of cancellation, the platform can restore the subscription on the same plan without requiring a new payment method setup.

### Exception Flows

**EX-012A — Cancellation of Subscription with Active Commitments**
If the subscription has a minimum commitment period that has not elapsed (e.g., annual contract), the platform enforces an early termination fee or blocks the cancellation with a `409 Conflict` response unless a Billing Admin overrides it.

### Business Rules Referenced

- **BR-027:** Upon cancellation, no further invoices are generated for the cancelled subscription.
- **BR-028:** Cancellation at period end preserves access through the paid period. No refund is issued for the remaining period unless UC-009 (Issue Credit Note) is explicitly invoked.
- **BR-029:** A cancelled subscription record is retained for 7 years for audit purposes and cannot be deleted.
