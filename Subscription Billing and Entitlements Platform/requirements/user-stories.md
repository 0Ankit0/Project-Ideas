# User Stories — Subscription Billing and Entitlements Platform

## Overview

This document captures user stories for all roles that interact with the Subscription Billing and Entitlements Platform. Each story is accompanied by acceptance criteria that define the observable, testable conditions for story completion. Stories are organised by functional domain.

---

## Roles

| Role | Abbreviation | Description |
|---|---|---|
| Account Owner | AO | The customer who owns the billing account |
| Billing Admin | BA | Internal operator managing plans, billing, and credits |
| Developer | DEV | Engineer integrating the platform APIs into a product |
| Finance Manager | FM | Internal operator responsible for revenue reporting |
| Customer Success | CS | Internal operator managing subscriber health |

---

## Plan Selection and Trial

---

**US-001: Start a Free Trial**
**As an** Account Owner, **I want to** select a plan with a free trial and activate my subscription without entering a payment method immediately, **so that** I can evaluate the product before committing to a paid subscription.

**Acceptance Criteria:**
- Given a Published Plan with a 14-day trial period configured
- When the Account Owner creates a subscription selecting that plan without a payment method
- Then the subscription is created in Trialing state with trial_end_date set to now + 14 days
- And no invoice is generated and no payment method charge is initiated
- When the Account Owner adds a payment method before the trial ends
- Then the payment method is stored and associated with the subscription
- When the trial end date arrives
- Then the system transitions the subscription to Active and generates the first invoice for the full billing period
- And the Account Owner receives a trial-ending reminder email 3 days before trial_end_date

---

**US-002: Select a Plan with Annual Billing Discount**
**As an** Account Owner, **I want to** choose between monthly and annual billing when subscribing, **so that** I can save money by committing to annual billing upfront.

**Acceptance Criteria:**
- Given a Plan that offers both monthly and annual billing intervals
- When the Account Owner views the plan catalog
- Then both billing intervals are shown with their respective prices and the annual savings percentage
- When the Account Owner selects the annual billing option and confirms subscription
- Then the subscription is created with billing_interval = annual and the annual price is applied
- And the first invoice reflects the full annual amount
- And the subscription next_billing_date is set to 12 months from the billing cycle anchor

---

**US-003: View Available Plans**
**As an** Account Owner, **I want to** browse all available plans with their features and pricing, **so that** I can choose the plan that best matches my team's needs.

**Acceptance Criteria:**
- Given at least one Published Plan exists in the catalog
- When the Account Owner calls the plan catalog API or visits the plan selection page
- Then only Published PlanVersions are returned (Deprecated and Archived plans are not shown)
- And each plan entry includes the plan name, description, price breakdown, billing interval options, trial duration, and list of feature entitlements
- And the prices are shown in the Account's billing currency
- And plans are ordered by price ascending by default

---

## Trial Management and Conversion

---

**US-004: Receive Trial Expiry Warning**
**As an** Account Owner, **I want to** receive advance notice before my trial expires, **so that** I have time to add a payment method and avoid service interruption.

**Acceptance Criteria:**
- Given a subscription in Trialing state with trial_end_date 3 days away
- When the system runs the daily notification job
- Then an email is sent to the Account Owner's billing email with: trial end date, plan name, price that will be charged, and a direct link to add a payment method
- Given trial_end_date is 1 day away
- Then a second reminder email is sent with the same information

---

**US-005: Convert Trial to Paid Without Interruption**
**As an** Account Owner, **I want my** subscription to convert automatically to paid when my trial ends, **so that** I do not lose access to the product.

**Acceptance Criteria:**
- Given a subscription in Trialing state with a valid payment method on file
- When the trial_end_date is reached
- Then the subscription state transitions to Active
- And an invoice is generated for the current billing period starting from the trial end date
- And the payment method is charged within 1 minute of invoice finalisation
- And the Account Owner receives an invoice email confirming the first charge
- And entitlement grants remain active with no gap in access

---

**US-006: Handle Trial Expiry with No Payment Method**
**As an** Account Owner **who has not added a payment method**, **I want to** be notified clearly when my trial expires, **so that** I know I need to add a payment method to continue using the service.

**Acceptance Criteria:**
- Given a subscription in Trialing state with no payment method on file
- When the trial_end_date is reached
- Then the subscription is not immediately cancelled
- And a grace period of 24 hours is started
- And the Account Owner receives an email with a link to add a payment method
- And entitlement checks continue to return granted during the grace period
- If the Account Owner adds a payment method within the grace period, the subscription transitions to Active and charges the first invoice
- If no payment method is added within the grace period, the subscription transitions to Cancelled and entitlements are revoked

---

## Usage Tracking and Viewing

---

**US-007: Report API Usage from an Application**
**As a** Developer, **I want to** submit usage events from my application to the billing platform, **so that** my customers are accurately charged for their API consumption.

**Acceptance Criteria:**
- Given a valid API key and a subscription_id for an Active subscription
- When the Developer sends a POST to /v1/usage with fields: subscription_id, dimension = "api_calls", quantity = 150, idempotency_key = "evt_abc123", timestamp = ISO-8601 string
- Then the API responds with HTTP 202 Accepted and a confirmation body including the idempotency_key
- When the same idempotency_key is submitted a second time
- Then the API still responds with HTTP 202 but the usage is not double-counted
- And the usage summary for the subscription reflects the quantity of 150, not 300

---

**US-008: View Current Period Usage**
**As an** Account Owner, **I want to** see how much of my plan's usage allowance I have consumed this billing period, **so that** I can manage my spending and avoid surprise invoices.

**Acceptance Criteria:**
- Given a subscription with active usage metering on the "api_calls" dimension
- When the Account Owner views the usage dashboard or calls GET /v1/subscriptions/{id}/usage
- Then the response includes: dimension name, units consumed this period, plan limit (or "unlimited"), percentage consumed, and billing period start and end dates
- And the data reflects usage submitted within the last 60 seconds
- And if usage exceeds 80% of a hard cap, a warning indicator is shown

---

## Invoice Review and Download

---

**US-009: View Invoice History**
**As an** Account Owner, **I want to** see a list of all my past invoices with their status, **so that** I can track my billing history and identify any issues.

**Acceptance Criteria:**
- Given an Account with at least one finalised invoice
- When the Account Owner calls GET /v1/invoices
- Then the response returns a paginated list of invoices ordered by invoice date descending
- Each invoice entry includes: invoice number, issue date, due date, total amount, currency, and status (Draft, Finalised, Paid, Void, Uncollectible)
- Filtering by status and date range is supported via query parameters

---

**US-010: Download an Invoice PDF**
**As an** Account Owner, **I want to** download a PDF copy of any finalised invoice, **so that** I can submit it to my finance team for reimbursement or accounting purposes.

**Acceptance Criteria:**
- Given a finalised invoice with a rendered PDF
- When the Account Owner calls GET /v1/invoices/{id}/pdf
- Then the response is a redirect to a time-limited secure URL (expiry 15 minutes) pointing to the invoice PDF
- The PDF includes: vendor name and address, customer billing name and address, invoice number, issue date, due date, line items with descriptions and amounts, tax breakdown, and total due
- And the PDF is generated within 60 seconds of invoice finalisation

---

## Payment Method Management

---

**US-011: Add a Credit Card**
**As an** Account Owner, **I want to** add a credit card as my payment method, **so that** my subscription renews automatically without manual action each billing cycle.

**Acceptance Criteria:**
- Given an Account with no payment method on file
- When the Account Owner completes the hosted card entry form (tokenisation handled by the payment gateway JS library)
- Then the gateway token is returned and stored as a PaymentMethod associated with the Account
- The card's last 4 digits, brand, and expiry month/year are stored for display purposes
- No raw card number is stored in the platform database
- The new card is set as the default payment method for the Account

---

**US-012: Remove a Payment Method**
**As an** Account Owner, **I want to** remove a payment method from my account, **so that** I can replace outdated or expired cards.

**Acceptance Criteria:**
- Given an Account with multiple payment methods on file
- When the Account Owner deletes a non-default payment method via DELETE /v1/payment-methods/{id}
- Then the PaymentMethod record is soft-deleted and no longer returned in active payment method lists
- When the Account Owner attempts to delete the default payment method
- And at least one other payment method exists on the Account
- Then the system requires them to designate a new default before deletion proceeds
- When the Account Owner attempts to delete the only payment method on an Active subscription
- Then the deletion is rejected with a 422 error explaining that an active subscription requires a payment method

---

## Payment Failure and Recovery

---

**US-013: Receive Payment Failure Notification**
**As an** Account Owner, **I want to** be immediately notified when a payment fails, **so that** I can take action before my subscription is at risk of cancellation.

**Acceptance Criteria:**
- Given an Active subscription with an invoice awaiting payment
- When the payment gateway returns a failure response (e.g., insufficient_funds)
- Then the subscription transitions to PastDue
- And within 5 minutes an email is sent to the Account Owner containing: the invoice amount, the failure reason in plain language, the next retry date, a direct link to update the payment method, and a link to the hosted payment page
- And a webhook event payment.failed is emitted to all configured webhook endpoints for the Account

---

**US-014: Recover from Payment Failure via Updated Card**
**As an** Account Owner, **I want to** update my expired card and immediately trigger a payment retry, **so that** my subscription is restored to Active without waiting for the next scheduled dunning retry.

**Acceptance Criteria:**
- Given a subscription in PastDue state with an outstanding invoice
- When the Account Owner updates their default payment method to a new valid card
- Then the system initiates an immediate payment retry against the outstanding invoice using the new payment method
- If the retry succeeds, the subscription transitions back to Active
- And entitlement access is restored immediately
- And the Account Owner receives a payment success confirmation email
- And the dunning retry schedule is cancelled since payment was recovered

---

## Entitlement Checks

---

**US-015: Check Feature Access in Real Time**
**As a** Developer, **I want to** query the entitlement API before allowing a user to access a premium feature, **so that** only subscribers on the correct plan can use restricted functionality.

**Acceptance Criteria:**
- Given a subscription with an active EntitlementGrant for feature key "advanced_analytics"
- When the Developer calls GET /v1/entitlements/check?subscription_id={id}&feature=advanced_analytics
- Then the response is HTTP 200 with body { "granted": true, "feature": "advanced_analytics" }
- Given a subscription on a plan that does not include "advanced_analytics"
- When the Developer calls the same endpoint
- Then the response is HTTP 200 with body { "granted": false, "feature": "advanced_analytics" }
- And the response time is under 10ms at p99

---

**US-016: Enforce Quota Limit for Seat Entitlement**
**As a** Developer, **I want to** check whether a new seat can be added to a subscription before provisioning a user account, **so that** customers cannot exceed their plan's seat limit.

**Acceptance Criteria:**
- Given a subscription on a plan with seat_limit = 5 and currently 5 active seats
- When the Developer calls GET /v1/entitlements/check?subscription_id={id}&feature=seats
- Then the response includes { "granted": false, "limit": 5, "current_usage": 5, "remaining": 0 }
- Given the subscription has only 3 active seats
- When the same call is made
- Then the response includes { "granted": true, "limit": 5, "current_usage": 3, "remaining": 2 }

---

## Coupon Application

---

**US-017: Apply a Coupon Code at Subscription Creation**
**As an** Account Owner, **I want to** apply a promotional coupon code when starting my subscription, **so that** I receive the advertised discount on my billing.

**Acceptance Criteria:**
- Given a valid CouponCode with code = "LAUNCH50", discount_type = percentage, discount_value = 50, duration = 3 months
- When the Account Owner submits a subscription creation request including coupon_code = "LAUNCH50"
- Then a DiscountApplication is created linking the coupon to the subscription
- And the first 3 invoices for the subscription each include a discount line item reducing the invoice total by 50%
- And the 4th invoice has no discount applied
- When an invalid or expired coupon code is submitted
- Then the subscription creation fails with HTTP 422 and an error message "Coupon code is invalid or expired"

---

## Plan Upgrade and Downgrade

---

**US-018: Upgrade to a Higher Tier Plan Mid-Cycle**
**As an** Account Owner, **I want to** upgrade my subscription to a higher plan tier immediately, **so that** I can unlock additional features and capacity without waiting for my next billing date.

**Acceptance Criteria:**
- Given a subscription Active on Plan A (monthly, $50/month) with 15 days remaining in the billing period
- When the Account Owner submits a plan change request to Plan B ($100/month) with effective = immediate
- Then the system calculates proration: credit for unused days on Plan A = (15/30) x $50 = $25.00, charge for remaining days on Plan B = (15/30) x $100 = $50.00
- And a new invoice is generated with a net charge of $25.00
- And the subscription's PlanVersion is updated to Plan B's current version
- And new EntitlementGrants from Plan B are activated immediately
- And Plan A entitlement grants that are not in Plan B are revoked

---

**US-019: Downgrade to a Lower Tier Plan at Period End**
**As an** Account Owner, **I want to** downgrade to a cheaper plan at the end of my current billing period, **so that** I retain my current features until I have paid for, while reducing future costs.

**Acceptance Criteria:**
- Given a subscription Active on Plan A ($100/month)
- When the Account Owner submits a plan change request to Plan B ($50/month) with effective = end_of_period
- Then the plan change is scheduled and a pending_plan_change record is stored
- And the Account Owner sees a notification: "Your plan will change to Plan B on {next_billing_date}"
- And the current period invoice continues with Plan A pricing
- When the billing period ends
- Then the subscription is moved to Plan B's PlanVersion
- And the next invoice is generated with Plan B pricing
- And entitlements are updated to match Plan B at the start of the new period

---

## Credit Note Issuance

---

**US-020: Issue a Credit Note for a Billing Error**
**As a** Billing Admin, **I want to** issue a credit note against an incorrectly priced invoice, **so that** the customer is compensated and the billing record reflects the corrected amount.

**Acceptance Criteria:**
- Given a finalised, unpaid invoice INV-1001 for $200.00
- When the Billing Admin creates a credit note via POST /v1/credit-notes with invoice_id = INV-1001, amount = 50.00, reason = "billing_error"
- Then a CreditNote is created with a unique credit note number, linked to INV-1001
- And a credit of $50.00 is applied to the Account's credit balance
- And when the next invoice is generated, the credit is automatically applied to reduce the invoice total
- And the Account Owner receives an email confirming the credit note issuance with the credit note PDF

---

## Dunning Status Monitoring

---

**US-021: Monitor Accounts in Dunning**
**As a** Customer Success representative, **I want to** view a list of all subscriptions currently in PastDue state with their dunning progress, **so that** I can proactively reach out to at-risk customers before they are cancelled.

**Acceptance Criteria:**
- Given multiple subscriptions in PastDue state at different stages of their dunning cycle
- When the Customer Success representative views the dunning dashboard or calls GET /v1/dunning/active
- Then a list is returned showing: Account name, subscription ID, invoice amount outstanding, initial failure date, number of retry attempts made, next retry date, and days until cancellation threshold
- The list is sortable by days-until-cancellation ascending to prioritise the most at-risk accounts
- A manual "Mark as Resolved" action is available to exit dunning when payment is confirmed outside the automated retry flow

---

## Tax Exemption

---

**US-022: Upload a Tax Exemption Certificate**
**As an** Account Owner, **I want to** upload a tax exemption certificate for my organisation, **so that** applicable taxes are not charged on future invoices.

**Acceptance Criteria:**
- Given an Account in a US state that permits tax exemption with a valid exemption certificate
- When the Account Owner uploads a PDF certificate via PUT /v1/accounts/{id}/tax-exemptions with jurisdiction = "US-CA" and expiry_date
- Then the certificate is stored and associated with the Account for the specified jurisdiction
- And invoices generated after approval with billing address in US-CA do not include state sales tax
- And the InvoiceLineItem for tax shows $0.00 with a note referencing the exemption certificate ID
- When the certificate's expiry_date is passed
- Then the system resumes calculating tax for that jurisdiction and notifies the Account Owner to renew the certificate

---

## Revenue Recognition Reporting

---

**US-023: Export Monthly Revenue Recognition Schedule**
**As a** Finance Manager, **I want to** export a revenue recognition schedule for a given month, **so that** I can post deferred revenue entries to the general ledger accurately.

**Acceptance Criteria:**
- Given multiple Active annual subscriptions with prepaid invoices
- When the Finance Manager calls GET /v1/revenue-recognition?period=2025-06 in CSV format
- Then the export contains one row per recognition event with: account ID, subscription ID, invoice ID, recognition date, recognised amount, deferred amount remaining, revenue category, and currency
- Annual prepaid subscriptions show 1/12 of the annual invoice amount recognised per month
- Monthly subscriptions show the full invoice amount recognised in the invoice month
- The total recognised amount column matches the revenue figure in the month-end financial report

---

## Subscription Pause and Resume

---

**US-024: Pause a Subscription During Off-Season**
**As an** Account Owner, **I want to** pause my subscription for up to 3 months, **so that** I am not charged during a period when I am not using the service.

**Acceptance Criteria:**
- Given an Active subscription on a Plan that allows pausing
- When the Account Owner submits a pause request via POST /v1/subscriptions/{id}/pause with resume_date = 90 days from now
- Then the subscription transitions to Paused state
- And no invoices are generated and no charges are made during the pause period
- And entitlement grants are revoked (unless the plan specifies pause-through access)
- And a Paused confirmation email is sent to the Account Owner including the scheduled resume date
- When the resume_date arrives
- Then the subscription automatically transitions back to Active
- And entitlement grants are reinstated
- And the next invoice is generated for the billing period starting from the resume date
