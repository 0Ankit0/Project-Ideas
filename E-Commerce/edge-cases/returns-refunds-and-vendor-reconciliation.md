# Returns, Refunds, and Vendor Reconciliation

## Failure Mode
Return accepted physically but refund state and vendor payout adjustment diverge across systems.

## Impact
Financial mismatches, vendor disputes, and delayed customer refunds.

## Detection
Daily settlement diff report finds return-complete orders lacking matching refund and payout adjustment events.

## Recovery / Mitigation
Run compensating ledger entries, freeze affected payout batch, and apply exception queue with dual approval closure.
