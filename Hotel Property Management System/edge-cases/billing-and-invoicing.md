# Hotel Property Management System — Edge Cases: Billing and Invoicing

## Overview

Billing accuracy is the most legally and financially consequential domain in hotel operations. A folio is a legal financial document. Every charge posted, adjusted, or voided creates an entry in a chain of custody that may be audited by the guest, the company, the OTA, the credit card issuer, the tax authority, or — in the event of a dispute — a court. Edge cases in billing are not merely inconvenient; they expose the hotel to chargeback losses, tax penalties, and accounting reconciliation failures. This file documents six critical billing edge cases with full audit trail requirements, financial impact assessments, and recovery procedures.

---

## EC-BIL-001 — Folio Split Failure (Guest Account vs Company Account)

*Category:* Billing and Invoicing
*Severity:* High
*Likelihood:* High (corporate accounts with split billing are extremely common)
*Affected Services:* FolioService, AccountingService, CorporateAccountService, CheckoutService

**Description**
A corporate guest's folio is configured as a split: the company's direct-bill account (city ledger) covers room and tax, while the guest's personal credit card covers incidentals (minibar, spa, F&B, phone). At checkout, the folio split fails — either the entire balance is charged to the guest's personal card, the entire balance is posted to the company account (including non-approved incidentals), or the system fails mid-split and leaves a partially settled folio in an inconsistent state.

**Trigger Conditions**

1. A split folio profile is configured for the reservation: `billing_profile = SPLIT, company_account_id = CA-5502, personal_card_token = TOKEN-xyz`.
2. Company account covers `ROOM_RATE, ROOM_TAX` charge codes; personal card covers `RESTAURANT, MINIBAR, SPA, PHONE, MISC`.
3. At checkout, `FolioService.split_and_settle()` is called.
4. One of the following causes a failure:
   - Company account is over its credit limit.
   - The personal card is declined.
   - The network call to the accounting system times out mid-split.
   - A charge code is ambiguous (e.g., a "room service" charge that could be room-related or F&B-related, depending on configuration).

**Expected System Behaviour**

1. `FolioService.split_and_settle()` begins by validating pre-conditions:
   - `CorporateAccountService.check_credit_limit(account_id, room_total)` → must return `APPROVED`.
   - PaymentService pre-authorisation of personal card for incidental total: `PaymentService.pre_auth(card_token, amount=incidental_total)` → must return `APPROVED`.
2. If both pre-conditions pass, the split is executed as a database transaction:
   a. Folio lines matching company codes are transferred to a new sub-folio: `FOLIO-{reservation_id}-COMPANY`.
   b. Folio lines matching personal codes remain in sub-folio: `FOLIO-{reservation_id}-PERSONAL`.
   c. Company sub-folio is posted to city ledger: `AccountingService.post_to_city_ledger(account_id, folio_id, amount)`.
   d. Personal sub-folio is charged to the card.
3. Both operations are wrapped in a compensating saga: if the city ledger post fails after the personal card is charged, a reversal is automatically initiated.
4. On success: two invoices are generated — one for the company (sent to `company_billing_email`) and one for the guest (sent to `guest_email`).

**Failure Mode — Company Account Over Limit**
- Pre-condition check fails. `CorporateAccountService` returns `CREDIT_LIMIT_EXCEEDED`.
- Entire folio falls back to personal card.
- Guest is informed and must decide whether to pay personally or contact their company's accounts department.
- This is a common source of corporate account disputes.

**Failure Mode — Mid-Split Timeout**
- Personal card is charged successfully. City ledger post times out.
- If the saga does not correctly reverse the personal charge, the guest is charged for the company portion.
- The folio is left in state `SPLIT_PARTIAL` — a dangerous inconsistent state.

**Audit Trail Requirements**
Every folio action — creation, line posting, split, payment, adjustment, void — must create an immutable audit log entry with: timestamp (UTC), agent ID, action type, before-value, after-value, and system component. The audit trail must be queryable: `GET /audit/folio/{folio_id}` returns the complete chronological history.

**Accounting Reconciliation Steps**
1. All `SPLIT_PARTIAL` folios appear on the daily exception report.
2. Accounts Receivable reviews each case, confirms which portion was settled, and posts the missing portion manually.
3. If the company was under-billed (company received incidentals it should not have), a corrective invoice is issued.
4. All corrections are posted with a `MANUAL_RECONCILIATION` flag for the monthly audit.

**Resolution**

1. Identify all folios in `SPLIT_PARTIAL` state.
2. For each: review the audit trail to determine which legs of the split completed.
3. Complete the failed leg manually or via API retry.
4. Verify final balances match the original folio total (guest total + company total = original total).

**Prevention**
- Implement the split as a saga with explicit compensation actions for each step.
- Pre-validate company credit limit before any checkout action begins (not just at split time).
- Flag ambiguous charge codes during folio setup, not at checkout time.
- Add a daily pre-checkout report: "These reservations have split folios checking out tomorrow — verify company account credit limits."

**Test Cases**
- *TC-1:* Clean split — company approved, personal card approved. Assert two invoices are generated and both accounts are correctly charged.
- *TC-2:* Company account over credit limit. Assert fallback to personal card is offered, not silently applied.
- *TC-3:* City ledger post times out after personal card is charged. Assert saga reversal fires and folio is restored to `UNSETTLED` state for manual processing.

---

## EC-BIL-002 — Payment Decline at Checkout (Card Declined)

*Category:* Billing and Invoicing
*Severity:* High
*Likelihood:* Medium
*Affected Services:* PaymentService, FolioService, CheckoutService, FrontDeskService, DebtRecoveryService

**Description**
At checkout, the guest's credit card on file is declined. This may occur because the card's credit limit is exceeded (particularly for long stays with high incidental spend), the card has been reported stolen and frozen since check-in, the card expired during the stay, or the payment gateway returns an error. The hotel has already provided services; it now needs to collect payment before releasing the guest — while remaining professional and avoiding accusatory language.

**Trigger Conditions**

1. Guest initiates checkout (at front desk or via express checkout).
2. `PaymentService.charge(card_token, amount, idempotency_key)` returns a decline code.
3. The folio has a positive outstanding balance.

**Expected System Behaviour**

1. `PaymentService.charge()` returns `{status: "DECLINED", decline_code: "INSUFFICIENT_FUNDS", is_retriable: false}`.
2. `CheckoutService` does NOT complete the checkout. Reservation remains in `CHECKED_IN` status. Room remains in `OCCUPIED` status.
3. If in express checkout flow (app): guest receives in-app message: "Payment for your stay of ${total} could not be processed. Please update your payment method or visit the front desk to complete checkout."
4. If at front desk: agent receives a discreet on-screen message (not visible to the guest): "Card declined — INSUFFICIENT_FUNDS. Do not announce. Offer alternative payment methods privately."
5. System records `PAYMENT_DECLINE_INCIDENT` on the folio.
6. Agent privately informs the guest: "I'm having a small issue processing that card — could we try another method or a different card?"
7. Guest provides a new payment method. Agent runs the new card.
8. If the guest is unable to provide payment:
   a. Front Office Manager is notified immediately.
   b. Guest is asked to contact their bank.
   c. If the folio is under $500: the hotel allows the guest to leave and initiates debt recovery via the existing card-on-file and formal invoice.
   d. If the folio is over $500: the hotel requests the guest remain until payment is arranged, within the limits of local law.

**Idempotency Requirements**
Every payment attempt must carry a unique `idempotency_key` derived from `folio_id + attempt_number + timestamp`. If the network times out after a charge attempt, the system must use the idempotency key to check whether the charge was processed before retrying — to avoid double-charging.

**Audit Trail Requirements**
- Every decline event: timestamp, decline code, card token (masked), amount, idempotency key.
- Every retry attempt: same fields plus the reason for retry.
- Any manual override or debt waiver: supervisor ID, reason, authorised amount.

**Resolution**

*Immediate (in-person):*
1. Offer the guest up to 3 alternative payment methods: a different credit card, debit card, cash, or bank transfer.
2. If guest agrees to a payment plan (e.g., half now, half in 7 days): document the arrangement in the folio and issue a partial receipt.

*Short-term:*
3. Send a formal invoice to the guest's email with a payment link valid for 14 days.
4. Log the folio as `OUTSTANDING_DEBT` in the accounts receivable system.

*Long-term (30+ days unpaid):*
5. Refer to external debt recovery with all documentation (folio, audit trail, communication history).

**Prevention**
- Run a silent pre-authorisation test at 50% of the folio balance on the evening before departure.
- If the pre-auth fails, notify the guest the night before checkout so they can resolve the issue without time pressure.
- Flag any card with an expiry date within 30 days of the checkout date at check-in time.

**Test Cases**
- *TC-1:* Card declined at checkout. Assert checkout is not completed and front-desk task is created.
- *TC-2:* Agent processes a new card successfully. Assert checkout completes and original declined-card event is in the audit trail.
- *TC-3:* Network timeout after charge request. Assert idempotency key is used to check charge status before any retry, preventing double-charge.

---

## EC-BIL-003 — City Ledger Dispute (Corporate Account Billing Error)

*Category:* Billing and Invoicing
*Severity:* High
*Likelihood:* Medium
*Affected Services:* AccountingService, CorporateAccountService, FolioService, DisputeManagementService

**Description**
A corporate account (city ledger) receives its monthly statement and disputes specific line items: charges that were not pre-approved in the corporate rate agreement (e.g., spa charges billed to the company instead of the guest), room rates charged above the negotiated corporate rate, or duplicate charges for stays that were cancelled. The dispute triggers a formal reconciliation process between the hotel's accounts receivable team and the company's accounts payable team.

**Trigger Conditions**

1. A corporate account submits a written dispute (email or dispute portal) for a specific charge or set of charges on their monthly statement.
2. The disputed amount exceeds the account's auto-resolve threshold (typically $100).
3. A `CITY_LEDGER_DISPUTE` record is created in DisputeManagementService.

**Expected System Behaviour**

1. Accounts Receivable agent receives the dispute and creates a case: `POST /disputes {account_id, invoice_id, disputed_lines: [...], dispute_reason: "...", submitted_by: "..."}`.
2. DisputeManagementService automatically queries the folio audit trail for each disputed line and creates a summary report.
3. If the dispute is clearly valid (e.g., a charge with code `SPA` was posted to a company account that has a `ROOM_TAX_ONLY` billing profile): an automatic credit is issued and the account is notified within 24 hours.
4. If the dispute requires investigation: a 10-business-day response SLA is applied.
5. All communications (emails, phone notes, resolution decisions) are logged against the dispute record.
6. On resolution: either a credit note is issued to the company account, or a detailed justification is sent explaining why the charge stands.

**Audit Trail Requirements**
- Original posting: agent ID, timestamp, charge code, amount, source (manual, POS, automated).
- Any adjustments: who requested, who approved, timestamp, reason.
- The audit trail must be immutable — corrections are made via new transactions (credit notes or supplementary charges), never by modifying historical records.

**Accounting Reconciliation Steps**
1. Pull the full folio for each disputed stay.
2. Verify the billing profile against the corporate rate agreement.
3. Verify each charge against the rate agreement's approved charge codes.
4. Calculate the correct amount vs. the billed amount.
5. If a discrepancy exists: issue a credit note for the difference and update the account's open balance.
6. Review the billing profile configuration for the account to prevent recurrence.

**Resolution**

1. Valid dispute (hotel error): issue credit note within 24 hours, update billing profile, investigate how the error occurred.
2. Invalid dispute (charge is correct): send a detailed breakdown with the folio audit trail as evidence within 10 business days.
3. Partially valid dispute: issue partial credit and document the reasoning for each disputed line.

**Prevention**
- Charge code validation at the time of posting: if a charge code is not in the company's approved list, a warning is shown to the agent before posting.
- Monthly pre-statement review: before sending the statement, run a validation check comparing all posted charges against each account's approved charge codes.
- Corporate account billing profiles should require supervisor approval to modify, with a full audit trail of changes.

**Test Cases**
- *TC-1:* SPA charge posted to a company account with a ROOM_TAX_ONLY profile. Assert the posting generates a warning to the agent.
- *TC-2:* Valid dispute submitted. Assert auto-credit fires within 24 hours if the dispute matches a billing profile violation.
- *TC-3:* Invalid dispute. Assert a detailed response with folio audit trail is generated within the 10-day SLA.

---

## EC-BIL-004 — Tax Calculation Error (Wrong Tax Rate Applied)

*Category:* Billing and Invoicing
*Severity:* High
*Likelihood:* Medium
*Affected Services:* TaxService, FolioService, NightAuditService, AccountingService, ReportingService

**Description**
A tax rate change (new city tourism tax, VAT rate adjustment, or room tax exemption for long-stay guests) is not applied correctly to reservations. This results in guests being charged the wrong tax rate — either undercharged (creating a tax liability for the hotel) or overcharged (creating a refund liability and potential regulatory issue). Tax errors are particularly dangerous because they accumulate silently across many folios before they are detected, often only during a periodic tax audit.

**Trigger Conditions**

1. A tax rate is updated in the system but the change is not applied retroactively to already-posted nightly charges.
2. A guest qualifies for a tax exemption (e.g., a stay exceeding 30 nights is exempt from tourism tax in many jurisdictions) but the exemption is not triggered automatically.
3. A reservation spans a tax rate change date (e.g., check-in before the rate change, check-out after) and the system does not split the tax calculation correctly.
4. A manual folio adjustment is posted without recalculating the associated tax.

**Expected System Behaviour**

1. TaxService maintains a tax rule table with effective dates: `{tax_code, rate, effective_from, effective_to, jurisdiction, applies_to_charge_codes}`.
2. Every nightly charge is calculated at the tax rate effective on the night's date, not the booking date.
3. For long-stay exemptions: TaxService evaluates `total_stay_nights >= exemption_threshold` at the time of each nightly charge. If the threshold is crossed, the exemption is applied from the threshold night forward.
4. When a tax rate is updated in TaxService, the system audits all future-dated but already-posted charges (e.g., advance charges for long-stay reservations) and recalculates.
5. NightAuditService runs a tax validation check: `SELECT SUM(amount * tax_rate) FROM folio_lines WHERE night_date = yesterday GROUP BY tax_code` — compare against the expected tax based on the TaxService rate for that date.

**Failure Mode**
- Old tax rate is applied to new bookings because the TaxService cache was not invalidated after the rate update.
- Long-stay exemption does not trigger because the reservation length is evaluated at booking time (when it was < 30 nights) rather than at each nightly audit (when it has exceeded 30 nights).
- The hotel submits tax returns with incorrect figures, triggering a tax authority audit.

**Detection**
- *Monitoring:* `tax_audit.variance_amount` — alert if the nightly tax reconciliation variance exceeds $10 (indicating a systemic error, not rounding).
- *Log Pattern:* `ERROR TaxService - Tax rate mismatch: folio_line_id={id} applied_rate={r1} expected_rate={r2} variance={amount}`.
- *Audit:* Monthly tax reconciliation report compares total tax collected with the expected total at the published rates.

**Accounting Reconciliation Steps**

1. Run a full tax audit for the affected date range: `SELECT folio_line_id, charge_date, amount, applied_tax_rate, expected_tax_rate FROM folio_lines WHERE ABS(applied_tax_rate - expected_tax_rate) > 0.001`.
2. For each affected folio: calculate the correct tax, post a corrective adjustment (`TAX_ADJUSTMENT_CREDIT` or `TAX_ADJUSTMENT_CHARGE`).
3. If guests were overcharged: issue refunds with an explanatory note in the guest folio and an email notification.
4. If guests were undercharged: the hotel absorbs the shortfall (it is not acceptable to back-charge guests for the hotel's tax calculation error).
5. File an amended tax return if the variance affected a reporting period that has already been submitted.

**Resolution**

1. Fix the tax rate in TaxService and invalidate the tax rate cache.
2. Identify all affected folios (date range from rate change to discovery).
3. Apply corrective adjustments per the reconciliation steps above.
4. Notify the tax authority proactively if the variance exceeds the reportable threshold.

**Prevention**
- Tax rate changes require a 4-eyes approval process: one agent proposes the change, a Finance Manager approves it.
- The approval triggers an automatic cache invalidation and a confirmation that all future-dated charges are recalculated.
- Automated nightly tax reconciliation with alerting for any variance > $10.

**Test Cases**
- *TC-1:* Tax rate is updated from 10% to 12%. Assert all future-dated nightly charges are recalculated at 12%.
- *TC-2:* Guest's stay reaches 30 nights (exemption threshold). Assert nightly charge on night 31 has 0% tourism tax.
- *TC-3:* Reservation spans a tax rate change date. Assert nights before the change are at the old rate and nights from the change date are at the new rate.

---

## EC-BIL-005 — Voided Charge Creates Negative Balance

*Category:* Billing and Invoicing
*Severity:* Medium
*Likelihood:* Medium
*Affected Services:* FolioService, PaymentService, AuditService, AccountingService

**Description**
An agent voids a charge on a folio (e.g., a minibar charge that the guest disputes, claiming the items were not consumed). If the folio has already been settled (the full balance was charged to the guest's card), voiding the charge creates a negative balance — the hotel owes the guest a refund. If the folio has not been settled, voiding the charge reduces the outstanding balance. Either scenario requires a complete audit trail and — in the settled case — an active refund transaction back to the guest's card.

**Trigger Conditions**

1. Agent voids a charge using `POST /folio/{folio_id}/void {line_id, reason}`.
2. The voided charge has an associated settled payment (i.e., the guest has already been charged).
3. The resulting folio balance after the void is negative.

**Expected System Behaviour**

1. When a void is requested, the system calculates the post-void balance.
2. If the balance becomes negative (i.e., the folio is settled), the system automatically creates a `REFUND_PENDING` record.
3. The agent receives a confirmation prompt: "Voiding this charge will create a refund of ${amount} to the guest's card ending in {last4}. Confirm?"
4. On confirmation: `PaymentService.refund(payment_transaction_id, amount)` is called.
5. The audit trail records: agent ID, supervisor override (if required — voids above $X require supervisor approval), reason code, the original charge line, the void entry, and the refund transaction ID.
6. Guest receives an email confirmation of the void and refund within 30 minutes.
7. The refund typically clears in 3–5 business days; the email includes this timeline.

**Audit Trail Requirements**
- Original charge: timestamp, amount, charge code, source (POS system, manual, rule engine), posting agent.
- Void: timestamp, voiding agent, supervisor approval (if required), reason code from a defined list (GUEST_DISPUTE, POSTING_ERROR, MANAGER_COMP, SERVICE_FAILURE).
- Refund: transaction ID from PaymentService, amount, card token (masked), status, processing timestamp.
- The complete chain must be queryable and must be retained for 7 years (PCI and accounting retention policy).

**Failure Mode**
- A void is processed but the refund transaction fails silently. The folio shows a negative balance, the audit trail shows a void, but no refund has reached the guest. The guest calls to ask about their refund and the hotel has no record of the PaymentService refund transaction.
- An agent voids a charge without supervisor approval when the amount exceeds the threshold — a control failure that allows potential fraud.

**Detection**
- *Monitoring:* `folio.negative_balance_count` — should be 0 after daily reconciliation. Any folio with a settled negative balance for > 24 hours triggers an alert.
- *Log Pattern:* `WARN FolioService - Void creates negative balance: folio_id={id} void_amount={amount} current_balance={balance}`.
- *Audit:* Daily report of all voids with reasons — reviewed by Revenue Manager for unusual patterns.

**Prevention**
- Voids above $100 require supervisor approval (configurable threshold).
- Refund transaction must be confirmed (not fire-and-forget) before the void is marked complete.
- Negative balance detection in the daily folio reconciliation job.

**Test Cases**
- *TC-1:* Void a $50 minibar charge on a settled folio. Assert a $50 refund is initiated to the card and the folio balance is 0 (void + refund cancel out).
- *TC-2:* Void a $150 charge without supervisor approval when the threshold is $100. Assert the void is blocked and a supervisor approval request is created.
- *TC-3:* Refund PaymentService call fails after the void is recorded. Assert the folio is flagged as `NEGATIVE_BALANCE_UNRESOLVED` and a front-desk task is created.

---

## EC-BIL-006 — Multi-Currency Folio with Exchange Rate Change

*Category:* Billing and Invoicing
*Severity:* Medium
*Likelihood:* Medium
*Affected Services:* FolioService, CurrencyService, PaymentService, AccountingService

**Description**
A guest checks in and the hotel records their preferred settlement currency as USD, while the hotel's base currency is EUR. During a 14-night stay, the EUR/USD exchange rate fluctuates by 3%. Charges posted throughout the stay are converted at different daily rates. At checkout, the total in USD may differ from the sum of daily converted amounts, depending on how the system handles currency conversion: at posting time or at settlement time.

**Trigger Conditions**

1. Guest's `preferred_currency` differs from the hotel's `base_currency`.
2. The stay duration is > 3 nights (long enough for exchange rate fluctuations to be noticeable).
3. Charges are posted in the hotel's base currency and displayed/settled in the guest's currency.

**Expected System Behaviour**

1. CurrencyService maintains daily exchange rates (updated at 09:00 from a trusted FX source).
2. Each folio line is stored in the base currency with the exchange rate at the time of posting recorded alongside it.
3. The folio display for the guest shows the converted amount at the applicable daily rate.
4. At checkout, the settlement amount is calculated as the sum of each line's original base-currency amount × its applicable exchange rate. This means the guest pays the rate that was published on each charge's posting date.
5. The settlement currency total is fixed at the start of the settlement transaction and does not fluctuate during payment processing.
6. The invoice shows both the base currency total and the settlement currency total, with each daily rate used.

**Failure Mode**
- All charges are converted at the checkout day's exchange rate rather than the posting date's rate.
- This can result in the guest being overcharged (if their currency weakened during the stay) or undercharged (if their currency strengthened).
- The discrepancy is typically small but is a regulatory issue in jurisdictions requiring exchange rate disclosure at time of transaction.

**Resolution**
- If a guest disputes the exchange rate applied: show the folio with per-line rates and the source of those rates.
- If the system applied the wrong rate: issue a corrective credit or charge for the difference.
- The hotel's margin on currency exchange is a legitimate revenue line but must be disclosed (typically shown as a "currency conversion fee" or built into the exchange rate spread).

**Accounting Reconciliation Steps**
1. End-of-day FX reconciliation: base currency total settled vs. expected base currency equivalent.
2. Any FX gain or loss is posted to the FX variance account, not to room revenue.
3. Monthly FX reconciliation report reviewed by Finance Manager.

**Prevention**
- CurrencyService stores the exchange rate with each folio line as an immutable field.
- The guest's invoice must show both the base currency amount and the settlement currency amount for each significant line.
- Offer guests the option to lock in an exchange rate at check-in (pre-authorisation in base currency).

**Test Cases**
- *TC-1:* 14-night stay with charges posted at varying daily rates. Assert settlement total equals the sum of per-line base amounts × per-line rates.
- *TC-2:* Exchange rate changes by 5% between check-in and checkout. Assert charges posted before the change use the old rate.
- *TC-3:* Guest requests an invoice in base currency. Assert the system generates a base-currency invoice without any conversion.

---

## Edge Case Summary Matrix

| ID | Title | Severity | Likelihood | Priority | Audit Trail Required | Financial Recovery Path |
|----|-------|----------|------------|----------|---------------------|------------------------|
| EC-BIL-001 | Folio Split Failure | High | High | P2 | Yes — saga compensation log | Manual reconciliation; corrective invoice |
| EC-BIL-002 | Payment Decline at Checkout | High | Medium | P2 | Yes — all decline codes + retries | Alternative payment; debt recovery |
| EC-BIL-003 | City Ledger Dispute | High | Medium | P2 | Yes — immutable folio lines | Credit note or justification within SLA |
| EC-BIL-004 | Tax Calculation Error | High | Medium | P2 | Yes — TaxService rate history | Corrective adjustment; amended tax return |
| EC-BIL-005 | Voided Charge Negative Balance | Medium | Medium | P3 | Yes — void + refund chain | Automatic refund; supervisor approval |
| EC-BIL-006 | Multi-Currency Exchange Discrepancy | Medium | Medium | P3 | Yes — per-line FX rates | Corrective credit; FX variance account |
