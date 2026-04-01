# Dunning Retry Edge Cases — Subscription Billing and Entitlements Platform

## Introduction

Dunning is the process of systematically communicating with customers and retrying payment collection after an initial invoice payment failure. The term originates from the historical practice of sending increasingly urgent letters to debtors; in modern SaaS billing, it is a state machine that governs retry timing, customer notification, entitlement degradation, and ultimately subscription suspension or cancellation.

The default dunning cycle for this platform is:

| Day | Action | Customer Communication |
|-----|--------|------------------------|
| Day 0 | Payment fails; invoice marked `payment_failed` | Email: "Payment failed — please update your payment method" |
| Day 1 | First automatic retry | Email: "We tried again — payment still declined" (on failure) |
| Day 3 | Second automatic retry | Email: "Action required — subscription at risk" |
| Day 7 | Third automatic retry; entitlement downgrade to read-only | Email: "Service degraded — please update payment method immediately" |
| Day 14 | Final retry; on failure, subscription suspended | Email: "Subscription suspended — update payment to restore service" |
| Day 21 | Subscription cancelled if no recovery (configurable) | Email: "Subscription cancelled — we're sorry to see you go" |

This cycle is configurable per plan and per customer segment. Enterprise customers may have a 30-day grace period. Monthly plans may have a 10-day cycle. The dunning engine must handle each customer according to their specific dunning configuration, not a global default.

The dunning engine is a state machine with external dependencies: the payment gateway, the email delivery service, the scheduler, and the entitlement engine. Failures in any of these dependencies produce failure modes that compound. A missed retry leaves an invoice uncollected. A double-fired retry charges a customer twice. A failed email leaves a customer unaware their service is at risk. Each of these scenarios is documented below.

---

## Failure Mode Table

| Failure Mode | Impact | Detection | Mitigation / Recovery |
|---|---|---|---|
| **DUN-1: Payment method expires between dunning steps (card expiry mid-cycle)** | A customer's card is valid at day 0 (declined for insufficient funds, not expiry) but expires between day 3 and day 7 dunning steps. The day 7 retry fails with a `card_expired` decline code instead of `insufficient_funds`. The dunning engine may not distinguish these decline codes, causing the same retry strategy to be applied to an unresolvable failure state. | Monitor payment gateway decline codes across dunning retry events. Alert: `dunning_retry_decline_code = card_expired AND dunning_step > 1`. Query `payment_methods` where `expiry_date < current_date` and `subscription.dunning_state = active`. | 1. At each dunning retry, re-validate payment method expiry before submitting to payment gateway. 2. If `expiry_date < current_date`: skip gateway attempt, immediately notify customer with a card-expired-specific message (not the generic retry message), and pause the retry timer for 48 hours to allow payment method update. 3. Do not count a skipped-due-to-expiry attempt as a dunning step exhausted. 4. Resume the dunning sequence from the current step once a new valid payment method is added. |
| **DUN-2: Customer updates payment method during active dunning cycle** | A customer adds a new credit card while the dunning engine is in state `day_3_retry_scheduled`. The next scheduled retry (day 7) will run against the old payment method, not the new one, because the dunning job cached the payment method ID at cycle start. Revenue loss if the retry fails unnecessarily; customer frustration at being contacted again after updating their method. | Monitor `payment_method_updates` events joined with `subscriptions` where `dunning_state = active`. Alert if a payment method update occurs and the next scheduled dunning step is more than 30 minutes in the future without a triggered immediate retry. Log: `event=payment_method_updated_during_dunning subscription_id=X`. | 1. On any `payment_method.updated` event: if subscription is in active dunning cycle, immediately trigger an out-of-sequence retry with the new payment method. Do not wait for the scheduled dunning step. 2. On successful immediate retry: mark invoice `paid`, clear dunning state, restore full entitlements, send "Payment successful — thank you" email. 3. On failed immediate retry with new method: restart the dunning clock from day 0 with the new method. 4. Log all out-of-sequence retries with `trigger=payment_method_update` for auditability. |
| **DUN-3: Dunning email delivery failure (SendGrid bounce, inbox full)** | The dunning email for day 7 ("service degraded") fails to deliver due to a hard bounce or full inbox. The customer never receives the notification that their service has been degraded. They discover service degradation unexpectedly, escalate to support, and dispute. Support cannot find a delivery record for the notification. | Monitor SendGrid delivery webhooks for dunning email events. Alert: `dunning_email_delivery_status = bounced OR failed AND dunning_step >= 3`. Log all dunning email send attempts with `message_id`, `recipient`, `dunning_step`, `delivery_status`. | 1. Implement multi-channel dunning notifications: email primary, SMS secondary (if opted in), in-app banner tertiary. 2. On email bounce, attempt SMS within 1 hour. On SMS failure, display in-app banner at next login. 3. Store delivery attempt log in `dunning_notifications` table with channel, status, and timestamp. 4. Before applying entitlement degradation at day 7, verify at least one notification channel was successfully delivered. If none succeeded, delay entitlement degradation by 24 hours and escalate to customer success team. 5. Never apply service suspension without confirmed notification delivery. |
| **DUN-4: Dunning step fires twice due to scheduler double-trigger** | The cron job or distributed task scheduler fires the day 3 dunning step twice within a short window (due to at-least-once delivery semantics or scheduler restart). The payment gateway receives two charge requests for the same invoice. The customer is charged twice. Chargeback risk is high. | Monitor `dunning_retry_events` for duplicate records: same `subscription_id`, same `invoice_id`, same `dunning_step`, within a 5-minute window. Alert: `dunning_double_fire_detected subscription_id=X`. Payment gateway idempotency logs will also show duplicate charge attempts. | 1. Use idempotency keys on all payment gateway charge requests: `idempotency_key = "dunning:{invoice_id}:{dunning_step}"`. The gateway deduplicates on this key. 2. Before executing a dunning step: acquire a distributed lock `dunning:{invoice_id}:{step}` with TTL equal to retry timeout. If lock exists, skip execution and log `skipped_duplicate`. 3. For any double-charge that occurred: immediately issue a full refund for the duplicate charge, notify the customer with an apology and explanation, and file an internal incident report. 4. Verify payment gateway idempotency key usage in all dunning retry code paths. |
| **DUN-5: Subscription cancelled by customer during active dunning cycle** | A customer manually cancels their subscription while they are in the dunning cycle (e.g., day 7). The cancellation sets `subscription.status = cancelled`. The dunning engine, if it does not check subscription status before each retry, will continue firing dunning steps against a cancelled subscription, potentially charging a customer who has already cancelled. | Monitor `dunning_retry_events` for records where `subscription.status = cancelled`. Alert: `dunning_retry_on_cancelled_subscription subscription_id=X`. This should never occur. | 1. Add subscription status check as first step in dunning job execution: `if subscription.status in [cancelled, terminated]: skip_all_remaining_steps(); clear_dunning_state()`. 2. On customer cancellation during active dunning: immediately purge all pending dunning tasks from the job queue using `subscription_id` as the queue filter. 3. If an outstanding invoice remains unpaid at cancellation: mark invoice as `written_off` or pursue via accounts-receivable process per business policy, not via dunning. 4. Send final invoice statement to customer's email of record for financial closure. |
| **DUN-6: Account deleted during active dunning cycle** | An account is hard-deleted (e.g., GDPR erasure request) while the subscription is in an active dunning cycle. The dunning job fires for a `subscription_id` whose associated account no longer exists, resulting in null-pointer exceptions or failed job executions that leave the dunning state machine in an inconsistent state. | Monitor dunning job error logs for `account_not_found` or `customer_not_found` errors. Alert: `dunning_job_error_type = entity_not_found`. Monitor `dunning_tasks` queue for tasks referencing deleted customer IDs. | 1. Account deletion workflow must include: query `dunning_tasks` queue for pending tasks by `customer_id`, cancel all matching tasks before deletion completes. 2. Dunning job must begin with a customer existence check: if customer not found, log `skipped_deleted_account` and mark invoice as `uncollectible`. 3. Archive the invoice record in a `deleted_account_invoices` table before account deletion for financial reconciliation. 4. Ensure GDPR erasure workflow completes dunning cleanup atomically with the customer record deletion. |
| **DUN-7: Payment gateway returns ambiguous result (timeout, 200 but no confirmation)** | The dunning retry charge request times out at the network layer or receives an HTTP 200 response from the gateway but no `charge.succeeded` confirmation event via webhook. The billing system does not know if the charge was processed. Marking the invoice as paid risks revenue loss if the charge failed; marking it as unpaid and retrying risks a double charge. | Monitor payment gateway charge requests for responses where `status = timeout OR (http_status = 200 AND charge_event_received = false)`. Alert: `billing_gateway_ambiguous_response_count > 0`. Set alert latency at 5 minutes post-charge-attempt if no webhook event received. | 1. For ambiguous results: do not update invoice status immediately. Wait for the gateway webhook event (up to 10 minutes). 2. If no webhook received after 10 minutes: query the gateway's charge status API using the charge ID. Use the polled result authoritatively. 3. If gateway status API also returns ambiguous: mark invoice `payment_status = pending_verification`, halt dunning, and alert on-call billing engineer. 4. Never retry a dunning step until the previous step's payment outcome is definitively resolved. 5. Store the raw gateway response body for all ambiguous results for later reconciliation. |
| **DUN-8: Dunning cycle starts on invoice that has already been paid (race condition)** | An invoice is paid via a separate channel (e.g., customer pays via bank transfer, CSM applies a credit) at the same time the dunning scheduler picks up the invoice for its day 1 retry. The dunning engine processes the retry against an invoice that is `status = paid`, potentially issuing a duplicate charge. | Monitor dunning job execution for `invoice.status = paid` at time of retry. Alert: `dunning_retry_on_paid_invoice subscription_id=X invoice_id=Y`. This should be caught by the pre-retry invoice status check. | 1. Dunning retry job must begin with an invoice status check: `if invoice.status in [paid, voided, written_off]: cancel_dunning_cycle(); log_event(dunning_cancelled_invoice_paid)`. 2. Use row-level locking on the invoice record when checking status and initiating charge: `SELECT FOR UPDATE` to prevent concurrent payment and retry. 3. Payment gateway idempotency key provides a final safety net against double charge. 4. For any dunning cycle that was cancelled due to prior payment: emit `event=dunning_cancelled_prior_payment` and update `invoice.dunning_state = resolved_external`. |
| **DUN-9: Multiple subscriptions on same account all enter dunning simultaneously** | A customer with three active subscriptions (e.g., base platform + two add-ons) has their payment method decline on month-end. All three subscriptions enter dunning simultaneously. The customer receives three separate dunning email sequences. Customer experience: confused by three simultaneous dunning threads. Customer service: high ticket volume. Risk: customer cancels all three to stop the emails. | Monitor accounts where `dunning_subscriptions_count > 1` and `dunning_state = active` for all. Alert: `billing_multi_subscription_dunning_account_id=X count=N`. | 1. Implement account-level dunning consolidation: when multiple subscriptions on the same account enter dunning simultaneously (within 24 hours), create a single consolidated dunning thread targeting the shared payment method. 2. A single payment method update should trigger retry on all subscriptions simultaneously. 3. Send one consolidated email per dunning step (not N emails). 4. Entitlement degradation and suspension timelines should be synchronized across all subscriptions on the account. 5. Assign the account to a single customer success owner during the multi-subscription dunning period. |
| **DUN-10: Dunning retry succeeds but webhook delivery to customer system fails** | The payment is collected successfully. The billing system emits a `subscription.payment_succeeded` webhook to the customer's registered endpoint. The webhook delivery fails (customer server is down). The customer's integration relies on this webhook to restore service access in their own system. Their internal systems show the subscription as suspended even though payment has been collected. | Monitor webhook delivery status for `subscription.payment_succeeded` events. Alert: `webhook_delivery_failed event_type=subscription.payment_succeeded subscription_id=X`. Track `webhook_delivery_attempts` counter per event. | 1. Implement exponential backoff webhook retry: attempt 1 at T+0, attempt 2 at T+5m, attempt 3 at T+30m, attempt 4 at T+2h, attempt 5 at T+24h. 2. After 5 failed attempts, send an email to the account's technical contact with the event payload and instructions to manually re-sync subscription state. 3. Expose a `GET /subscriptions/{id}/state` API endpoint that customers can poll to verify subscription status independent of webhooks. 4. Log all webhook delivery attempts and outcomes in `webhook_delivery_log` with `event_id`, `attempt_number`, `http_response_code`, `latency_ms`. |
| **DUN-11: Grace period expires while customer is in process of updating payment method** | The dunning grace period (e.g., 14 days) expires at 11:59 PM UTC. The customer begins updating their payment method at 11:45 PM and completes the update at 12:05 AM UTC — 6 minutes after grace period expiry. The system suspended the subscription at midnight, and the payment retry triggered by the new payment method fails because the subscription is now `suspended`, not `active`. | Monitor `subscription_state_changes` for transitions from `active_dunning` to `suspended` within 1 hour of a `payment_method.updated` event. Alert: `dunning_suspension_race_payment_update_detected subscription_id=X`. | 1. Implement a 15-minute grace window around grace period expiry: if a payment method update event occurs within 15 minutes before or after grace period expiry, delay suspension for 30 minutes to allow the triggered retry to complete. 2. If retry succeeds within the extension window, restore full subscription status and cancel suspension. 3. Suspension workflow must check `dunning_extension_active` flag before executing. 4. Customer communication: "We noticed you updated your payment method just as your grace period expired. We are retrying your payment now — if successful, your service will be restored immediately." |
| **DUN-12: Dunning step scheduled on weekend/holiday with different retry behavior** | Some payment networks have lower authorization rates on weekends (fewer bank fraud teams online). Some enterprise customers' accounts payable teams do not process payments on weekends. A dunning step scheduled on Saturday may have a higher failure rate than the same step on Monday. If the dunning engine does not account for this, it may exhaust retry attempts faster than necessary. | Track dunning retry success rate by day-of-week. Alert if `dunning_retry_success_rate_weekend < dunning_retry_success_rate_weekday × 0.8`. Log: `event=dunning_retry day_of_week=Saturday success=false`. | 1. Add a business day awareness configuration to the dunning engine. For enterprise customers: if a dunning step falls on a Saturday or Sunday, delay to Monday 9 AM in the customer's billing timezone. 2. For SMB/consumer customers: weekend retries are acceptable and no delay is applied. 3. Track success rates by day-of-week per customer segment. If weekend success rate is significantly lower, escalate the configuration change to the billing product team. 4. Always allow immediate out-of-sequence retry when customer updates payment method, regardless of day. |

---

## Dunning Configuration Reference

The dunning engine is configured per-plan and per-customer-segment. The following reference describes all configurable parameters and their valid ranges.

### Global Dunning Defaults

```yaml
dunning:
  retry_schedule:
    - day: 1
      action: retry_payment
      notify: true
      notification_template: dunning_day1
    - day: 3
      action: retry_payment
      notify: true
      notification_template: dunning_day3
    - day: 7
      action: retry_payment
      notify: true
      notification_template: dunning_day7_degraded
      entitlement_action: degrade_to_readonly
    - day: 14
      action: retry_payment
      notify: true
      notification_template: dunning_day14_suspend
      entitlement_action: suspend
    - day: 21
      action: cancel_subscription
      notify: true
      notification_template: dunning_day21_cancelled
  grace_period_days: 14
  max_retry_attempts: 4
  idempotency_key_format: "dunning:{invoice_id}:{dunning_step}"
  payment_method_update_triggers_immediate_retry: true
  business_day_aware_for_segments:
    - enterprise
    - government
  weekend_delay_target: monday_9am_customer_tz
```

### Per-Plan Override Example

```yaml
dunning_overrides:
  plan_id: enterprise-annual
  retry_schedule:
    - day: 3
      action: retry_payment
      notify: true
      notification_template: dunning_enterprise_day3
    - day: 14
      action: retry_payment
      notify: true
      entitlement_action: none
    - day: 30
      action: suspend
      notify: true
      notification_template: dunning_enterprise_day30_suspend
    - day: 60
      action: cancel_subscription
  grace_period_days: 30
```

### Critical Operational Rules

1. **Idempotency is non-negotiable**: Every payment retry must use an idempotency key that includes the invoice ID and dunning step number. This is the last line of defense against double charges.

2. **Invoice status must be checked before every retry**: Not just at dunning cycle start. Between dunning steps, invoices can be paid by other means. Check status at execution time.

3. **Distributed locks must be used**: The distributed lock `dunning:{invoice_id}:{step}:lock` must be acquired before executing any dunning step. Lock TTL should be set to the maximum expected payment gateway response time (60 seconds) plus 50% buffer.

4. **Entitlement changes must be logged**: Any entitlement degradation or suspension triggered by dunning must create a record in `entitlement_change_log` with `trigger=dunning`, `dunning_step=N`, `timestamp`, and `actor=system`.

5. **Customer communication must precede entitlement changes**: Notification delivery (or confirmed delivery failure) must be recorded before entitlement degradation is applied. Service should never be degraded silently.

6. **Cancellation requires human review for high-value accounts**: For accounts with annual contract value > $10,000, the day-21 cancellation step must be routed to a customer success manager for manual review before execution. Automated cancellation on high-value accounts is disabled.

### Dunning State Machine States

| State | Description | Valid Transitions |
|-------|-------------|-------------------|
| `not_started` | No payment failure; default state | → `day_0_failed` |
| `day_0_failed` | Initial payment failure recorded | → `day_1_pending`, `resolved` |
| `day_1_pending` | Waiting for day 1 retry | → `day_1_retried` |
| `day_1_retried` | Day 1 retry executed | → `day_3_pending`, `resolved` |
| `day_3_pending` | Waiting for day 3 retry | → `day_3_retried` |
| `day_3_retried` | Day 3 retry executed | → `day_7_pending`, `resolved` |
| `day_7_pending` | Waiting for day 7 retry; entitlements degraded | → `day_7_retried` |
| `day_7_retried` | Day 7 retry executed | → `day_14_pending`, `resolved` |
| `day_14_pending` | Waiting for day 14 retry; suspension imminent | → `day_14_retried` |
| `day_14_retried` | Day 14 retry executed; subscription suspended | → `suspended`, `resolved` |
| `suspended` | Subscription suspended; awaiting payment | → `day_21_pending`, `resolved` |
| `resolved` | Payment collected; dunning cleared | — (terminal) |
| `cancelled` | Subscription cancelled; dunning terminated | — (terminal) |
| `written_off` | Invoice marked uncollectible; dunning terminated | — (terminal) |
