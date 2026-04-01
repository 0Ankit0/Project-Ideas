# Credit Note Edge Cases — Subscription Billing and Entitlements Platform

## Introduction

A credit note (also called a credit memo) is a formal accounting document issued by the billing platform to reduce the amount a customer owes. Credit notes are issued in several scenarios: a customer is overcharged and the error must be corrected; a customer cancels or downgrades and is entitled to a prorated refund; a service credit is granted as a goodwill gesture or SLA compensation; or an invoice line item is disputed and resolved in the customer's favor.

Credit notes interact with the billing system's accounting ledger, the payment gateway's refund workflow, and the customer's invoice history in ways that are not always intuitive. The accounting principle is straightforward: a credit note reduces the balance owed on one or more invoices. The implementation is complex because invoices may be in different states (draft, finalized, paid, voided), because accounts may carry balances in multiple currencies, and because credits may have expiry dates that create time-pressure on application.

In jurisdictions where invoices are tax-inclusive documents (e.g., EU VAT-registered businesses), credit notes must also carry the corresponding tax adjustment, which adds a layer of regulatory complexity. An incorrect credit note is not merely a billing error — it is an incorrect accounting document that may need to be formally voided and reissued with a new document number.

A well-designed credit note system must handle the following invariants:
- **Credit note amount ≤ original invoice amount** (overshoot is an error)
- **Credit application must be idempotent** (applying the same credit twice is an error)
- **Expired credits must not be applied** (even if the credit balance is non-zero)
- **Credit notes in multi-currency accounts must be applied in the matching currency**
- **All credit note operations must be audit-logged with actor, timestamp, and justification**

---

## Failure Mode Table

| Failure Mode | Impact | Detection | Mitigation / Recovery |
|---|---|---|---|
| **CN-1: Credit note amount exceeds original invoice amount** | Overshoot produces a negative balance on the invoice (the customer is "owed" money by the platform beyond the original charge), creating an accounting liability. In some systems, this produces a negative invoice balance that carries forward as a credit on future invoices — but if the system is not designed for this, it produces a ledger inconsistency. | Validate at credit note creation: `credit_note.amount ≤ invoice.original_amount`. Alert: `credit_note_overshoot_attempted customer_id=X invoice_id=Y credit_amount=Z invoice_amount=W`. Monitor `invoices` for `balance < 0`. | 1. Enforce server-side validation: `if credit_note.amount > invoice.remaining_balance: reject with HTTP 422 and error code CREDIT_OVERSHOOT`. 2. The admin UI must show real-time remaining balance and disable the "Issue Credit" button if the amount exceeds it. 3. For credits that must exceed the invoice amount (e.g., overpayment refund), process the excess as a direct refund to the original payment method, not as a credit note. 4. If an overshoot credit was issued incorrectly, void the credit note, issue a corrected credit note for the correct amount, and process a direct refund for any excess already posted. |
| **CN-2: Applying credit from credit note to invoice in different currency** | A customer has a credit note denominated in EUR (issued for an EU invoice) and an outstanding USD invoice. Applying the EUR credit to the USD invoice requires a currency conversion at an exchange rate that may not match the rate at which the original invoice was issued, creating an accounting discrepancy. | Monitor `credit_note_applications` for records where `credit_note.currency ≠ invoice.currency`. Alert: `cross_currency_credit_application_attempted customer_id=X`. | 1. Block cross-currency credit application by default: return HTTP 422 with `error: CURRENCY_MISMATCH`. 2. If cross-currency application is a business requirement, use the exchange rate from the credit note issuance date (not application date) and document the FX adjustment in a separate accounting journal entry. 3. Route all cross-currency credit applications to finance team for manual review and approval. 4. Do not automate cross-currency credit application. |
| **CN-3: Issuing credit note on a finalized but unpaid invoice** | A finalized invoice is in a fixed state — its amounts and tax have been calculated and locked. Issuing a credit note on a finalized-but-unpaid invoice is valid (it reduces the amount owed), but the system must not reduce the finalized invoice amount directly. Instead, the credit note creates a separate document that offsets the balance. If the system incorrectly modifies the finalized invoice amount, the audit trail is broken. | Monitor `invoices` for `status = finalized AND amount_modified_after_finalization = true`. Alert: `finalized_invoice_amount_modified invoice_id=X`. Verify `credit_note.applies_to_invoice` is populated with a separate document reference, not an in-place invoice edit. | 1. Finalized invoices must be immutable: do not update `invoice.amount` after finalization. 2. Issue a credit note as a separate document with `applies_to_invoice_id` referencing the original invoice. 3. The customer's account ledger reflects the net balance (invoice amount minus credit note amount). 4. If an invoice amount was incorrectly modified after finalization: void the invoice, reissue a corrected invoice with the original amount, then issue the credit note against the reissued invoice. |
| **CN-4: Issuing credit note on an already-paid invoice** | A customer paid an invoice in full. A billing error is later discovered (e.g., they were charged for a plan they cancelled). A credit note is issued. The credit note cannot be applied to the paid invoice (balance is already zero). The credit must be either refunded to the original payment method or applied as a credit balance to a future invoice. If neither is done, the customer has "credit" but no way to use it. | Monitor `credit_notes` where `applies_to_invoice.status = paid` and `credit_application_method` is null. Alert: `unresolved_credit_note_on_paid_invoice customer_id=X credit_note_id=Y`. | 1. When issuing credit on a paid invoice, present two options: a) Refund to original payment method (preferred for errors > $10), b) Apply as account credit balance for future invoices. 2. Default to option (a) for credit notes issued by the system (e.g., proration corrections). 3. Default to option (b) for goodwill credits issued by customer success. 4. Always confirm the selected disposition with the customer via email. 5. Credit balances not applied within 12 months are reviewed for expiry handling per account terms. |
| **CN-5: Partial credit application across multiple invoices** | A credit note for $100 is issued and the customer has three outstanding invoices: $40, $35, and $30. The $100 credit should be applied in full across all three. If the application logic fails mid-way (e.g., after applying $40 to invoice 1 and $35 to invoice 2, the system crashes), the credit is partially applied and the credit note's remaining balance is inconsistent. | Monitor `credit_notes` where `amount_applied ≠ amount_issued AND applied_status ≠ partial`. Alert: `credit_note_partial_application_stale credit_note_id=X last_updated=T`. Track `credit_note_application_events` for incomplete sequences. | 1. Implement multi-invoice credit application as an atomic transaction: all invoice updates succeed or all roll back. 2. Use a database transaction spanning all `invoice_balance_update` operations for a single credit application. 3. If the transaction fails mid-way, the credit note status is rolled back to `unapplied`. 4. Apply credits to oldest outstanding invoices first (FIFO) unless the customer specifies otherwise. 5. Emit `event=credit_applied invoice_id=X amount=Y credit_note_id=Z remaining_credit=W` for each invoice updated. |
| **CN-6: Credit note expiry edge cases (credit expires before being fully applied)** | A $500 credit note is issued with a 90-day expiry. The customer has $200 in invoices due within the first month and then goes quiet. When the remaining $300 would apply to their next invoice on day 95, the credit has expired. The customer loses $300 in credit they were owed. If this is an error correction credit (not a promotional credit), expiry is inappropriate. | Monitor `credit_notes` approaching expiry with unapplied balance > $0. Alert: `credit_note_expiry_within_7_days unapplied_balance > 0 credit_note_id=X`. Differentiate `credit_type`: `error_correction` (should not expire) vs `promotional` (may expire). | 1. Error correction credit notes must not have expiry dates — they represent a debt the platform owes the customer. 2. Promotional credit notes may have expiry dates, but customers must be notified 14 days before expiry. 3. For credits expiring within 7 days with unapplied balance: trigger an automatic application to the oldest outstanding invoice. If no outstanding invoice exists, issue a refund to the original payment method. 4. For credits that have already expired with unapplied balance: route to finance team for manual disposition (refund vs. reissue vs. write-off). |
| **CN-7: Credit note issued for cancelled subscription with pending invoice** | A customer cancels their subscription. A final invoice is generated for the current billing period (prorated). A credit note is issued to offset the proration owed back to the customer. However, the subscription is now cancelled, and the credit has no future invoices to apply to. The credit sits as an unapplied balance indefinitely unless explicitly refunded. | Query `credit_notes` where `subscription.status = cancelled AND credit_application_status = unapplied`. Alert: `orphaned_credit_note_on_cancelled_subscription customer_id=X credit_note_id=Y`. Schedule check: run daily. | 1. Cancellation workflow must include a credit disposition step: at subscription cancellation, if a credit note will be issued (e.g., proration), immediately queue a refund to the original payment method for the credit amount. 2. Do not emit a credit note that will be immediately orphaned — emit a refund instead. 3. For existing orphaned credits: process refunds automatically for amounts > $1. Write off amounts < $1 to the revenue adjustment account. 4. Notify customer: "Your subscription has been cancelled. A refund of $X will appear on your statement within 5-10 business days." |
| **CN-8: Multiple credit notes issued against same invoice line item** | Two customer success agents, handling the same customer complaint independently, both issue credit notes against the same invoice line item — a $50 charge for a feature that was unavailable. The customer receives $100 in credit against a $50 charge. This produces a negative balance on the invoice and a revenue leakage of $50. | Monitor `credit_note_line_items` for duplicate references: same `invoice_line_item_id` credited more than once. Alert: `duplicate_credit_on_line_item invoice_line_item_id=X total_credited=Y line_item_amount=Z` where Y > Z. | 1. Add a server-side constraint: total credits issued against a single `invoice_line_item_id` cannot exceed the line item's original amount. Return HTTP 422 if exceeded. 2. Credit note creation UI must display existing credits against the selected line item before allowing a new credit. 3. For duplicate credits already issued: void the duplicate credit note, send the customer a corrected account statement, and document the internal error in the credit note audit log. 4. Implement a credit note approval workflow for amounts > $50 to prevent uncoordinated issuance. |
| **CN-9: Credit note creation race condition (two admins issuing simultaneously)** | Two customer success agents receive the same complaint and simultaneously begin creating a credit note for the same invoice. Both pass validation (credit amount ≤ remaining balance at read time) but both commit, resulting in two credits that together exceed the invoice balance. | Monitor for credit notes issued within a 60-second window against the same `invoice_id` by different users. Alert: `concurrent_credit_notes_detected invoice_id=X`. Row-level locking on `invoice` should prevent this, but alert if it occurs. | 1. Use `SELECT FOR UPDATE` (row-level lock) on the invoice record when creating a credit note. This serializes concurrent credit note creation. 2. Credit note creation must validate the current (locked) remaining balance, not a cached value. 3. The second concurrent request will either see a reduced remaining balance and adjust, or will fail validation and return HTTP 409. 4. Admin UI: display a "credit note in progress" indicator on the invoice if a lock is held by another user. 5. For any race-condition duplicates that slipped through: void the excess credit note and document. |
| **CN-10: Credit note on invoice that has been voided** | An invoice is voided (due to a billing error, double-billing, or administrative correction). A credit note is then issued against the voided invoice. A credit against a voided invoice is semantically nonsensical — the invoice has already been nullified. The credit produces phantom account balance that may apply to future invoices incorrectly. | Query `credit_notes` where `applies_to_invoice.status = voided`. Alert: `credit_note_on_voided_invoice credit_note_id=X invoice_id=Y`. This should be blocked at creation time. | 1. Validate invoice status before credit note creation: `if invoice.status == voided: reject with error INVOICE_VOIDED`. 2. Void the entire credit note if it was issued against a voided invoice. 3. If the customer is owed money due to the voiding scenario, issue a direct refund to their payment method — not a credit note. 4. Emit `event=credit_note_rejected reason=invoice_voided` for audit. |
| **CN-11: Credit application order conflict (multiple credits, different expiry dates)** | A customer has three pending credit notes: $30 (expires in 5 days), $50 (expires in 30 days), and $20 (no expiry). A $75 invoice becomes due. The system applies credits FIFO by creation date, using the $50 first, then the $20, leaving the $30 credit expiring in 5 days unused. The $30 credit then expires and is lost. | Compare credit application order against expiry-date-aware ordering. Alert: `credit_applied_in_non_optimal_order customer_id=X expiring_credit_unused=true`. Run daily reconciliation for accounts with multiple credits and pending invoices. | 1. Credit application order: apply soonest-expiring credits first. Within the same expiry date, apply oldest credits first (FIFO). 2. Implement a credit application optimizer that selects credits to minimize total credit expiry loss for each invoice application. 3. Notify customers 7 days before any credit expires with a clear statement of the expiry date and remaining balance. 4. Finance team monthly report: list all credits that expired with unapplied balance in the prior month, segmented by credit type. |
| **CN-12: Credit note amount is exactly equal to account balance owed** | A customer's total outstanding balance is exactly $150.00. A credit note is issued for exactly $150.00. The expected outcome is a zero balance. If the credit application logic uses floating-point arithmetic and the calculation produces $149.9999999 or $150.0000001, the customer may appear to owe a penny or have a $0.00000001 credit — both of which produce incorrect invoice states and potential erroneous dunning triggers. | Monitor accounts where `total_outstanding_balance - credit_applied = non_zero_sub_cent_amount` after a full-balance credit. Alert: `full_balance_credit_residual_nonzero customer_id=X residual=E`. | 1. Use decimal arithmetic (not floating-point) for all credit application calculations. Python `Decimal`, Java `BigDecimal`, or equivalent. 2. For full-balance credit application, use `credit_applied = invoice.remaining_balance` (integer cent arithmetic) rather than `credit_applied = credit_note.amount`. This eliminates floating-point residuals. 3. After credit application, verify `invoice.remaining_balance == 0` exactly. If non-zero by sub-cent amount, apply a zero-value adjustment to normalize. 4. Add unit test: `credit_note_amount = invoice.balance = $150.00 → post_application_balance = $0.00 exactly`. |

---

## Credit Note Approval Workflow

All credit notes must follow the approval workflow defined below. The workflow tier is determined by credit note type and amount.

### Tier 1: Automatic Approval (No Human Review Required)

**Criteria**: System-generated credit notes, amount ≤ $25, type = `proration_correction` or `service_credit`.

**Process**: Credit note is issued and applied automatically. Customer is notified by email. Audit log entry is created with `actor=system`.

**Examples**: Proration adjustments under $25. System-generated SLA credits.

### Tier 2: Single Agent Approval

**Criteria**: Manually issued credit notes, amount $25–$200, type = any.

**Process**:
1. Customer success agent creates a draft credit note in the admin console.
2. System validates eligibility (invoice status, amount limits, currency match).
3. Agent submits for self-approval if authorized, or routes to team lead.
4. Agent must enter a justification (minimum 20 characters) and attach a support ticket ID.
5. Credit note is issued on approval.

**Escalation**: If the original invoice was > 90 days ago, route to Finance for additional approval.

### Tier 3: Finance Team Approval

**Criteria**: Amount > $200, or any credit note on an annual plan invoice, or cross-currency credit application.

**Process**:
1. Customer success agent creates a draft credit note.
2. Draft is automatically routed to the Finance approval queue.
3. Finance reviews within 1 business day (SLA).
4. Finance approves, rejects, or modifies the amount.
5. Credit note is issued on Finance approval.

**SLA**: Finance team must act on all Tier 3 credit notes within 1 business day. Breached SLAs are escalated to the Finance Manager.

### Approval Audit Requirements

All credit note approvals — regardless of tier — must record the following in the `credit_note_audit_log` table:

```
credit_note_id       UUID
invoice_id           UUID
amount               DECIMAL(12,2)
currency             VARCHAR(3)
credit_type          ENUM(proration_correction, service_credit, goodwill, error_correction, other)
issued_by            UUID (user_id)
approved_by          UUID (user_id, null for Tier 1)
approval_tier        ENUM(1, 2, 3)
justification        TEXT
support_ticket_id    VARCHAR(50)
issued_at            TIMESTAMP WITH TIME ZONE
applied_at           TIMESTAMP WITH TIME ZONE (null if unapplied)
voided_at            TIMESTAMP WITH TIME ZONE (null if active)
void_reason          TEXT (null if active)
```

This audit log is an immutable append-only table. Records must not be deleted or updated. Voiding is represented by a new record with `voided_at` populated, not by deleting or modifying the original record.
