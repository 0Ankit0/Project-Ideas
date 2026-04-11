# Returns, Refunds, and Vendor Reconciliation

## Failure Mode
Return accepted physically but refund state and vendor payout adjustment diverge across systems.

## Impact
Financial mismatches, vendor disputes, and delayed customer refunds.

## Detection
Daily settlement diff report finds return-complete orders lacking matching refund and payout adjustment events.

## Recovery / Mitigation
Run compensating ledger entries, freeze affected payout batch, and apply exception queue with dual approval closure.

---

## Failure Mode
Partial shipment with backorder is later cancelled for unavailable lines, but refund computes against full order instead of unfulfilled subset.

## Impact
Over-refund risk, vendor payout leakage, and settlement disputes.

## Detection
Refund validator detects requested refund amount exceeds refundable balance for fulfilled lines.

## Recovery / Mitigation
Bind refund eligibility to line-level fulfillment state; require backordered/cancelled lines as the only refundable principal in this scenario.

---

## Failure Mode
Refund reversal required after suspected fraud/chargeback win but refund already marked final internally.

## Impact
Ledger divergence and customer balance inconsistencies.

## Detection
Dispute operations event indicates reversal condition with no corresponding reversing ledger entry.

## Recovery / Mitigation
Support explicit `REFUND_REVERSED` workflow with audited approvals, reversing ledger entries, and customer/vendor notification.
