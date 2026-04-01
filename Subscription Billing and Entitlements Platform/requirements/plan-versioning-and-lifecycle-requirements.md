# Plan Versioning and Lifecycle Requirements

## 1. Introduction

This document defines the detailed requirements governing how subscription plans are versioned, how plan lifecycle state transitions occur, how subscribers are insulated from plan changes through grandfathering and version locking, and how billing cycles and proration are managed across plan changes. These requirements govern the behaviour of the Plan Service and Subscription Service and are the authoritative reference for any design or implementation decisions related to plan evolution.

---

## 2. Plan Lifecycle States

### 2.1 State Definitions

**PVL-001** — A Plan must always exist in exactly one of the following lifecycle states: **Draft**, **Published**, **Deprecated**, or **Archived**. State transitions are governed by the rules in section 2.2.

**PVL-002** — A Plan in **Draft** state is being configured by a Billing Admin. No subscriber may select a Draft Plan. A Draft Plan may be edited freely, including changing prices, features, and trial configuration, without creating a new PlanVersion.

**PVL-003** — A Plan transitions to **Published** state when a Billing Admin explicitly publishes it. At the moment of publication, the system must create an immutable PlanVersion record capturing the complete state of the Plan at that moment, including all Prices, Entitlements, trial configuration, and billing intervals. The publish action is audited with the admin identity and timestamp.

**PVL-004** — A Plan in **Published** state is available for new subscriptions. It is returned by the public plan catalog API. A Published Plan may not be directly edited in a way that modifies subscriber-facing attributes; a new Draft must be created and published, which creates a new PlanVersion.

**PVL-005** — A Plan transitions to **Deprecated** state when a Billing Admin marks it as deprecated, typically after a replacement plan has been Published. A Deprecated Plan is hidden from the public plan catalog API. Existing subscriptions on Deprecated PlanVersions remain active and are not automatically migrated. No new subscriptions may be created on a Deprecated Plan.

**PVL-006** — A Plan transitions to **Archived** state when it has no active or paused subscriptions and has been Deprecated for at least 90 days. Archived Plans are read-only. No new subscriptions may be created. Archived Plans are retained permanently for historical billing reference. The Archived transition may be triggered manually by a Billing Admin or automatically by the system after the 90-day deprecation hold period.

### 2.2 Allowed State Transitions

| From State | To State | Trigger | Conditions |
|---|---|---|---|
| Draft | Published | Admin publish action | Plan must have at least one active Price and one billing interval defined |
| Published | Deprecated | Admin deprecate action | No mandatory condition; admin may deprecate at any time |
| Published | Draft | Not allowed | A Published plan cannot revert to Draft; edits must create a new version |
| Deprecated | Archived | Admin archive or system auto-archive | No active or paused subscriptions reference this plan |
| Deprecated | Published | Not allowed | A Deprecated plan cannot be re-published; a new plan must be created |
| Archived | Any | Not allowed | Archived is a terminal state |

---

## 3. Plan Versioning

### 3.1 Version Creation

**PVL-007** — Every time a Billing Admin publishes changes to an existing Published Plan, the system must create a new PlanVersion with a version number incremented by 1 from the highest existing PlanVersion for that Plan. Version numbers are positive integers starting at 1.

**PVL-008** — A PlanVersion record must be immutable once created. No field on a PlanVersion — including prices, feature entitlements, trial duration, billing interval, or currency amounts — may be modified after the PlanVersion is created. Any change requires a new PlanVersion.

**PVL-009** — Each PlanVersion must store: plan_id, version_number, status (Active, Deprecated), created_at timestamp, published_by (admin user ID), effective_from date, and a complete snapshot of all Prices and Entitlements as they were at publication time.

**PVL-010** — The system must maintain the full version history of all PlanVersions for a Plan indefinitely. Billing Admins must be able to retrieve any historical PlanVersion via the API for audit and dispute resolution purposes.

### 3.2 Version Locking

**PVL-011** — At the moment a Subscription is created, the system must record the plan_version_id of the PlanVersion that was current at that time. This is the subscription's locked PlanVersion. All billing for that subscription, including recurring charges, usage rating, and proration calculations, must use the prices and entitlements from the locked PlanVersion unless the subscriber explicitly upgrades.

**PVL-012** — Version locking must be atomic with subscription creation. The system must not create a subscription and then separately record the plan version; both must be written in the same database transaction to prevent race conditions where a plan version change between the two writes would cause a version mismatch.

**PVL-013** — The system must expose the locked_plan_version_id field on every Subscription in all API responses, allowing Developers to verify which version a subscriber is on.

### 3.3 Grandfathering

**PVL-014** — When a Billing Admin publishes a new PlanVersion (e.g., increasing the monthly price), existing subscriptions locked to previous PlanVersions must not be automatically migrated to the new version. They continue to be billed at the prices defined in their locked PlanVersion indefinitely until explicitly migrated.

**PVL-015** — Grandfathering applies to all pricing components: flat fees, per-seat rates, tiered rates, usage rates, and any included usage allowances. A subscriber on a grandfathered PlanVersion retains all entitlements and pricing from that version even if the current version removes or restricts those features.

**PVL-016** — The system must provide a Billing Admin report that lists all active subscriptions grouped by PlanVersion, showing the version number, the count of subscribers, and the monthly recurring revenue attributable to each version. This enables Admins to assess migration impact.

---

## 4. Subscription Lifecycle States

### 4.1 State Definitions

**PVL-017** — A Subscription must always exist in exactly one of the following lifecycle states: **Trialing**, **Active**, **PastDue**, **Paused**, **Cancelled**, or **Expired**.

**PVL-018** — **Trialing**: The subscription is within the free trial period. No invoices are generated. Entitlement grants are active per the plan's trial entitlement configuration. The subscription will auto-transition to Active when the trial period ends if a payment method is present.

**PVL-019** — **Active**: The subscription is in good standing. Invoices are generated at the end of each billing period. Entitlement grants are fully active. The subscription renews automatically at the next billing date.

**PVL-020** — **PastDue**: A payment has failed and the DunningCycle is in progress. The subscription continues to operate (entitlements remain active during the dunning window unless the plan's dunning_revoke_entitlements flag is set to true). If payment is recovered, the subscription returns to Active. If all dunning retries are exhausted, the subscription moves to Cancelled.

**PVL-021** — **Paused**: The Account Owner has paused the subscription. No invoices are generated and no charges are made. Entitlement grants are revoked unless the plan specifies pause-through access for specific features. The subscription will resume on the configured resume_date.

**PVL-022** — **Cancelled**: The subscription has been ended, either by the Account Owner, by a Billing Admin, or automatically by the system after dunning exhaustion. Entitlement grants are revoked. A Cancelled subscription cannot be reactivated; a new subscription must be created. Cancellation is recorded with the cancellation reason and actor.

**PVL-023** — **Expired**: Used for fixed-term subscriptions (those with a defined end_date at creation, as opposed to open-ended recurring subscriptions). When the end_date is reached, the subscription moves to Expired. Entitlement grants are revoked. No further charges are made. Expired subscriptions are distinct from Cancelled subscriptions in revenue reporting.

### 4.2 Allowed Subscription State Transitions

| From State | To State | Trigger | Notes |
|---|---|---|---|
| Trialing | Active | Trial period ends, payment method present | System-initiated at trial_end_date |
| Trialing | Cancelled | Trial period ends, no payment method after grace | Grace period is configurable, default 24 hours |
| Trialing | Cancelled | Account Owner requests cancellation | Immediate; no charge |
| Active | PastDue | Payment charge fails | System-initiated on payment failure |
| Active | Paused | Account Owner or admin pause request | Requires plan to allow pausing |
| Active | Cancelled | Account Owner or admin cancels (immediate) | Prorated refund issued if applicable |
| Active | Cancelled | Account Owner cancels at period end | Subscription stays Active until period end, then Cancelled |
| Active | Expired | End_date reached (fixed-term only) | System-initiated |
| PastDue | Active | Payment succeeds during dunning | System-initiated on successful retry or manual payment |
| PastDue | Cancelled | All dunning retries exhausted | System-initiated; cancellation reason = dunning_exhausted |
| Paused | Active | Resume_date reached or manual resume | System-initiated or admin-initiated |
| Paused | Cancelled | Account Owner or admin cancels while paused | Immediate; no charge |
| Cancelled | (none) | Terminal state | New subscription must be created to re-subscribe |
| Expired | (none) | Terminal state | New subscription must be created to re-subscribe |

---

## 5. Migration Rules

### 5.1 Voluntary Migration

**PVL-024** — An Account Owner or Billing Admin may migrate a subscription from a grandfathered PlanVersion to a newer PlanVersion at any time by performing a plan change. The plan change must specify: the target plan_version_id, the effective date (immediate or end_of_period), and the proration behaviour (prorate or no_prorate).

**PVL-025** — When an Account Owner initiates an upgrade from a grandfathered version to a higher-priced current version, the system must display the price difference clearly before confirmation, including any proration for the remainder of the current billing period.

### 5.2 Administrative Migration

**PVL-026** — A Billing Admin may initiate a bulk migration of subscribers from a deprecated PlanVersion to a newer PlanVersion. Bulk migrations must be performed in batches with a configurable batch size and delay to avoid database overload. The migration must be fully audited and reversible within 30 days of execution via individual subscription rollbacks.

**PVL-027** — Before executing a bulk migration, the system must generate a preview report showing: total affected subscriptions, billing impact per subscriber (price increase or decrease), total MRR impact, and the list of subscriber email addresses for notification. The Billing Admin must confirm after reviewing the report.

**PVL-028** — All migrated subscribers must receive an email notification at least 14 days before the migration effective date, describing the upcoming price or feature change and providing a link to cancel if they do not wish to continue.

---

## 6. Billing Cycle Management

**PVL-029** — The system must support the following billing intervals: monthly, annual, quarterly, semi-annual, and custom (defined as a fixed number of days between 7 and 365). The billing interval is set at the PlanVersion level and applies to all subscriptions on that version.

**PVL-030** — The billing cycle anchor is set at subscription creation as the day of month (or exact date for annual plans) when invoices are generated and payment is collected. The anchor must be respected across all future renewals. For monthly plans created on the 29th, 30th, or 31st, the system must use the last day of the month for months shorter than the anchor day.

---

## 7. Proration Rules

### 7.1 Proration on Upgrade

**PVL-031** — When a subscription upgrades to a higher-priced plan mid-cycle with effective = immediate, the system must calculate proration as follows:
- Credit for unused time on old plan: `credit = (days_remaining_in_period / total_days_in_period) x old_plan_price`
- Charge for remaining time on new plan: `charge = (days_remaining_in_period / total_days_in_period) x new_plan_price`
- Net invoice amount: `net = charge - credit`
- If net > 0, an invoice is generated and charged immediately.
- If net <= 0, a credit is applied to the Account's credit balance.

**PVL-032** — Days are calculated using the calendar day boundary in the Account's billing timezone (UTC by default). The day of the plan change counts as a day on the new plan.

### 7.2 Proration on Downgrade

**PVL-033** — When a subscription downgrades to a lower-priced plan mid-cycle with effective = immediate, the system must calculate proration using the same formula as upgrade. The resulting credit is applied to the Account's credit balance and offset against the next invoice. No refund to the payment method is initiated unless the Billing Admin explicitly requests a refund.

**PVL-034** — When a downgrade is scheduled for effective = end_of_period, no proration occurs in the current period. The subscriber pays the full current plan price for the remainder of the period and begins paying the new plan price at the next billing cycle start.

### 7.3 Proration on Cancellation

**PVL-035** — When a subscription is cancelled with effective = immediate and the plan's refund_on_immediate_cancel policy is set to prorated, the system must calculate a prorated refund for the unused portion of the prepaid period and initiate a refund to the payment method used for the most recent invoice payment.

**PVL-036** — When a plan's refund_on_immediate_cancel policy is set to none, no refund is issued on immediate cancellation. The subscriber loses access immediately and no credit or refund is generated.
