# Edge Cases: Transaction Processing — Digital Banking Platform

---

## Duplicate Transaction Detection Failure (Idempotency Key Collision)

### Scenario
A customer submits a $2,500 transfer via the mobile app. The app experiences a network timeout after the HTTP request leaves the device but before the response arrives. The app's retry logic fires after 5 seconds, submitting an identical payload. Both requests arrive at the Transfer Service within 8ms of each other — close enough that neither request has written its idempotency key to Redis before the other reads.

### Failure Mode
Redis `SET idempotency:key NX EX 86400` uses atomic SETNX, but if two processes simultaneously check "does this key exist" before either writes it — a TOCTOU race — both see "no key" and both proceed to process the transfer. The customer is debited $5,000 instead of $2,500. Both ACH entries are submitted to the ODFI.

### Impact
- **Financial:** $2,500 erroneous debit. If customer does not have sufficient balance, second transfer may overdraw the account, triggering NSF fees.
- **Customer:** Double charge complaint, trust damage.
- **Regulatory:** Reg E: once customer reports the unauthorized duplicate, the institution must investigate and resolve within 10 business days, issue provisional credit within 5 business days.
- **Operational:** Two ACH entries already submitted — one must be returned via R05/R06 (unauthorized/returned per ODFI's request), which requires coordination with the ODFI.

### Detection
- Post-processing reconciliation: daily job compares (customer_id, amount, destination, submitted_at window ±60s) — any duplicates trigger alert.
- Real-time monitoring: Kafka stream processor watches `transfers.initiated` topic for duplicate (customer_id, payee_id, amount) within a 60-second window and raises alert.
- Balance monitoring: > $500 unexpected debit drop on a single account within 5 minutes triggers fraud review.

### Mitigation
- **Lua script atomicity:** Replace two-step check-then-set with a single atomic Redis Lua script: `if redis.call('get', KEYS[1]) then return 0 else redis.call('setex', KEYS[1], 86400, ARGV[1]) return 1 end`. This executes atomically in a single Redis command, eliminating the race.
- **Database fallback:** Write idempotency key to PostgreSQL (unique constraint on `idempotency_key` column) with `INSERT ... ON CONFLICT DO NOTHING` — if insert affected 0 rows, return the cached response. DB is authoritative; Redis is a performance layer.
- **Exponential backoff with jitter:** Client-side retry: wait 1s + random(0–500ms), then 2s + jitter, then 4s — reduces thundering herd amplifying duplicates.
- **Request deduplication window:** Reject requests with the same idempotency key after 24 hours (match on both key and request body hash — if body differs, return 422 Unprocessable).

### Recovery
1. Reconciliation job flags duplicate ACH entry.
2. Initiate ACH return for the duplicate via Modern Treasury / ODFI: file R06 (returned per ODFI's request) within 2 business days.
3. Once ACH return credit arrives (~1–2 business days), post correcting credit to customer account.
4. Reverse any NSF fees triggered by overdraft.
5. Notify customer proactively: "We identified a duplicate transaction and have reversed it. Your account balance has been corrected."

---

## Partial Transfer Failure — Debit Succeeds, Credit Times Out

### Scenario
A $15,000 Fedwire transfer is initiated. The Transfer Service successfully debits the source account (journal entry written to Aurora, balance updated). The Fedwire submission to the Federal Reserve FedLine system times out after 30 seconds — our system receives no confirmation. The $15,000 is now debited from the customer but has not been sent via Fedwire.

### Failure Mode
Without a compensating transaction, the $15,000 is in limbo. The source account shows $15,000 less than expected. The money is neither in transit nor at the destination. The Transfer Service marks the transaction as `UNKNOWN` (no success or failure signal). If the retry logic blindly retries, the Federal Reserve may have actually processed the initial message (the timeout was on our end), resulting in a duplicate Fedwire submission.

### Impact
- **Financial:** $15,000 removed from customer balance, destination never receives funds. If retry causes double submission: $15,000 duplicated at receiving bank.
- **Customer:** Immediate trust crisis — large sum disappeared from their balance.
- **Operational:** Fed operations team must manually investigate IMAD/OMAD for the failed submission.
- **Regulatory:** Fedwire operating rules require error resolution within the same business day where possible.

### Detection
- Transfer Service monitors outgoing Fedwire requests with a 45-second deadline. On timeout, status transitions to `SETTLEMENT_UNCERTAIN`.
- Alert: any `SETTLEMENT_UNCERTAIN` transaction > $10,000 triggers immediate PagerDuty P1 incident.
- Saga orchestrator (Temporal): records the debit step as completed and Fedwire step as `timed_out`. Visibility in Temporal web UI.

### Mitigation
- **Saga pattern with compensating transactions:** Every transfer is modelled as a Saga. Steps: (1) Debit source, (2) Submit payment rail, (3) Credit destination. Each step has a defined compensating transaction: (1) Re-credit source, (2) Cancel/return via rail, (3) Debit destination. On timeout at step 2, the saga executor initiates the compensating transaction for step 1 (re-credit source).
- **Idempotent Fedwire submission:** Before re-submitting, query the Fed's status inquiry service with the IMAD from the original message to check if it was processed. Only re-submit if the Fed confirms no record of the original IMAD.
- **Suspense account:** Pending transfers in `SETTLEMENT_UNCERTAIN` are held in a suspense GL entry — the debit is recognized but pending settlement. Reconciliation job resolves or reverses suspense entries within 2 hours.
- **Hard timeout with automatic reversal:** If no settlement confirmation within 4 business hours, automatically trigger the compensating re-credit and mark the transfer `FAILED`. Customer notified.

### Recovery
1. Saga orchestrator detects timeout → initiates compensating re-credit immediately.
2. Re-credit posted to source account — customer balance restored.
3. Operations team queries Fed status inquiry for original IMAD. If Fed processed it (race condition), initiate recall request (Fed Recall/Return procedures).
4. If Fed did not process it (clean timeout), no further action needed — customer is made whole by step 1.
5. Incident post-mortem: investigate root cause of Fedwire timeout (network issue, Fed system slow period, our timeout too short). Adjust timeout threshold and add more granular alerting.

---

## ACH Return Code After Funds Already Credited to Recipient

### Scenario
The platform credits the recipient's account immediately (Real-Time ACH or early credit before RDFI confirmation — a product decision to improve UX). Two business days later, the ODFI submits an ACH return code R01 (Insufficient Funds) for the original debit. The originating customer's account was debited correctly, but the entry was returned by the RDFI because the destination bank rejected it. The recipient has already spent $1,800 of the $2,200 credit.

### Failure Mode
The credit was optimistically posted. The return means the funds were never actually transferred — the credit must be reversed, but the recipient has only $400 remaining in their account. A $1,800 deficit is created. The originating customer's debit was also reversed by the ACH return, so neither party ultimately paid or received — but the recipient's account is now $1,800 negative.

### Impact
- **Financial:** $1,800 credit loss if the recipient cannot repay. Standard ACH return risk inherent in early credit products.
- **Customer:** Recipient's account goes to -$1,800 — may cause downstream NSF on their bill payments.
- **Credit risk:** Early-credit product inherently carries return risk; risk appetite must be calibrated to return rate.
- **Regulatory:** The platform must follow ACH operating rules for return handling; improper handling may result in NACHA penalties.

### Detection
- Modern Treasury / ACH processor delivers R-code return webhook within 2 business days of settlement.
- Kafka consumer processes return webhook: publishes `ach.return.received` event.
- Alert: R01 returns on recipient accounts that already received early credit → P1 incident.
- Return rate monitoring: daily report on return rates by R-code, ACH originator, time of day.

### Mitigation
- **Risk-based early credit eligibility:** Only credit early for customers with a > 90-day relationship and a positive return rate history. New accounts: hold funds for 2 business days (standard ACH settlement).
- **Provisional credit disclosure:** Clearly disclose that early-credited funds are provisional: "Available now, subject to final settlement in 2 business days." Terms and conditions govern recovery rights.
- **Return reserve:** Maintain an expected loss reserve for early-credit returns based on historical return rates (typically 0.3% for PPD ACH). Reserve funded by the early-credit fee charged to customers.
- **Recovery workflow:** On R01/R02/R03 return: (1) reverse provisional credit on recipient account; (2) notify recipient; (3) initiate repayment plan if deficit > $0 — debit from next incoming credit or set up payment arrangement; (4) if recipient account balance insufficient, classify as credit loss and route to collections.
- **Re-origination decision:** If return is R01 (insufficient funds) and originating customer wants to retry, require ACH verification (micro-deposit or Plaid instant bank verification) before re-origination.

### Recovery
1. ACH return webhook received → Kafka event published → Return Processor consumer handles.
2. Reverse provisional credit: debit recipient account with memo "ACH Return - R01 - Ref: TXN-XXXX".
3. If recipient balance goes negative: overdraft protection applies if enrolled; otherwise classify as unauthorized overdraft with repayment demand.
4. Re-credit originating sender account (the original sender's debit is reversed by the RDFI automatically — confirm via reconciliation).
5. Notify both parties: originating sender ("Your transfer of $2,200 was returned — funds restored to your account. Please verify the recipient's account details."), recipient ("A recent deposit of $2,200 has been reversed per bank regulations.").

---

## Currency Conversion Rate Stale at Settlement — FX Rate Change Greater Than 2%

### Scenario
A customer initiates an international wire transfer of €10,000 to Germany. The EUR/USD rate is quoted at 1.0850 at 9:15 AM. The exchange rate is locked for 4 hours per the product terms. At 1:45 PM, the transfer is ready for settlement, but ECB published an emergency rate change following macroeconomic news — EUR/USD is now 1.1072, a 2.04% increase. If settled at the original rate, the bank loses $222 on this single transaction.

### Failure Mode
If the settlement engine uses the cached conversion rate without checking for expiry or rate drift, it settles at the stale rate. At scale (thousands of FX transfers), a rate movement event causes systematic losses. If the system instead re-prices at settlement and the customer was given a firm quote, the re-pricing violates the terms disclosed to the customer.

### Impact
- **Financial:** Per-transaction loss of up to $222 on this example; extrapolated across a portfolio during a volatile event, losses could be material (e.g., 1,000 transactions × $200 = $200,000 loss in one day).
- **Regulatory:** If the rate change is not disclosed when re-pricing occurs, UDAAP (Unfair, Deceptive, or Abusive Acts or Practices) risk.
- **Customer:** If charged a different rate than quoted, customer complaints, chargeback risk, regulatory scrutiny.

### Detection
- FX rate monitor: polls ECB/Bloomberg/Reuters rate feed every 30 seconds. If current rate deviates > 1.5% from locked rate on any pending transfer, alert fires immediately.
- Settlement engine: on each settlement attempt, compute rate delta = |current_rate - locked_rate| / locked_rate. If > 2%, route to FX risk management workflow.

### Mitigation
- **Rate lock with hedge:** When a firm rate is quoted to a customer, immediately purchase an FX forward or option from the treasury desk to hedge the exposure. The cost of the hedge is built into the customer spread.
- **Rate validity window:** Quote is valid for 30 minutes (not 4 hours for large amounts > $10,000). This reduces the hedging window and therefore hedging cost.
- **Rate breach protocol:** If rate moves > 2% before settlement: (a) for amounts < $5,000: absorb the loss (within product risk tolerance); (b) for amounts $5,000–$50,000: notify customer, offer re-priced rate or cancellation at no fee; (c) for amounts > $50,000: mandatory re-pricing with customer consent required before settlement proceeds.
- **Circuit breaker:** If EUR/USD rate moves > 3% in any 30-minute window, pause all EUR FX settlements and escalate to treasury desk for manual review.
- **FX loss limit:** Daily FX mark-to-market loss limit: $50,000 per currency pair. If breached, halt new FX quote issuance until treasury review.

### Recovery
1. FX risk system detects rate breach → auto-pauses settlement on affected transactions.
2. Treasury team reviews in-flight positions and hedging status.
3. Customer notification (where required by policy): "Market conditions have changed since your transfer was initiated. Your transfer of €10,000 is available at the new rate of 1.1072. Please confirm to proceed or cancel for a full refund."
4. If customer accepts new rate: re-price and settle. If customer declines: cancel, refund USD, no cancellation fee.
5. Post-event: update rate lock duration policy if systematic losses occurred; review hedge strategy with treasury.

---

## Transaction Processing Backlog at End-of-Day Cut-off

### Scenario
It is 2:45 PM ET on a Tuesday — the same-day ACH cut-off for the ODFI (Originating Depository Financial Institution) is at 3:00 PM. The message queue (Kafka topic `transfers.to-ach`) has 47,000 pending transfers that accumulated since 2:00 PM due to a Transfer Service pod restart (a rolling update deployed at an unfortunate time). Only 12,000 transfers can be included in the same-day ACH batch in the 15-minute window.

### Failure Mode
Transfers submitted after the 3:00 PM cut-off are classified as next-day ACH. Customers who expected same-day credit (and whose payees expected same-day receipt — e.g., for rent due today) instead have a 1-business-day delay. If the backlog is not handled systematically, the Transfer Service may try to include late transfers in the same-day batch incorrectly, causing NACHA batch errors or the ODFI rejecting the batch entirely.

### Impact
- **Customer:** Same-day promise broken for ~35,000 customers. Potential cascading effects: late rent payments, failed business payrolls if transfer was a payroll disbursement.
- **Operational:** NACHA batch files may be malformed if cut-off logic is not enforced; ODFI may reject or partially process.
- **Financial:** Customer service volume spike; potential fee reversals for service failure.
- **SLA:** Breach of product SLA for same-day ACH.

### Detection
- Kafka consumer lag monitoring: alert fires when `transfers.to-ach` consumer lag exceeds 10,000 messages.
- Time-remaining alert: at T-30 minutes before ACH cut-off, if current lag × average processing time > 30 minutes, alert fires.
- SLA tracker: dashboard showing estimated processing time vs. ACH cut-off time.

### Mitigation
- **Priority queue:** Partition `transfers.to-ach` by priority: (1) time-sensitive (same-day, payroll, bill pay due today), (2) standard. Priority 1 consumers run at 2× replica count during peak hours.
- **Pre-cut-off surge capacity:** Scheduled HPA override at 2:00 PM ET: scale Transfer Service to 20 replicas (from standard 8) until 3:30 PM ET daily.
- **Cut-off enforcer:** At T-5 minutes before cut-off (2:55 PM), the NACHA batch assembler stops accepting new entries for the same-day batch regardless of queue state. All remaining entries are automatically re-classified as next-day ACH.
- **Customer communication:** For transfers reclassified: automated notification within 5 minutes: "Your transfer of $1,200 has been reclassified to next-day delivery due to high processing volume. Expected arrival: [tomorrow's date]."
- **Rolling updates policy:** Prohibit pod rolling updates between 1:30 PM and 4:00 PM ET on business days (ACH peak window). Enforce via OPA Gatekeeper admission webhook.

### Recovery
1. Identify transfers caught in backlog via Kafka consumer group status.
2. Reclassify affected transfers from `PROCESSING` (same-day) to `PROCESSING` (next-day) — update effective_date in ACH entry.
3. Build next-day ACH batch with all reclassified transfers + normal next-day transfers.
4. Send proactive customer notifications.
5. Review SLA — if breach justifies compensation (e.g., late fees incurred by customer), escalate to customer service for individual case handling.
6. Post-incident: implement scheduled HPA override (step 2 of mitigation) and cut-off enforcer.

---

## Interbank Settlement Failure — Fed System Unavailable

### Scenario
The Federal Reserve's FedACH system experiences an unplanned outage from 10:15 AM to 2:30 PM ET on a Wednesday. The platform has 1,847 pending ACH credits and 623 Fedwire messages queued for the morning batch that cannot be submitted. The outage affects all ODFI-initiated transactions.

### Failure Mode
ACH and Fedwire queues accumulate. If the system blindly retries all pending messages simultaneously when FedACH comes back online at 2:30 PM, it creates a thundering herd that may overwhelm our ODFI's FedLine connection (bandwidth limited) or hit rate limits. Duplicate submission risk is high if retry logic doesn't account for any partially processed state on the Fed's side.

### Impact
- **Customer:** All ACH credits and Fedwire payments delayed by up to 4+ hours. High-value Fedwire ($100M+) transfers may miss intraday liquidity windows for counterparties.
- **Operational:** Every inbound ACH credit also delayed — recipients across all banks affected, not just our platform.
- **Financial:** Potential intraday overdrafts for corporate customers who relied on Fedwire inflows for their own outbound payments.
- **Systemic:** Fed outages are rare (99.9%+ uptime historically) but impact every financial institution simultaneously.

### Detection
- FedLine health check: ping FedLine endpoint every 60 seconds. Three consecutive failures → alert + declare payment rail outage incident.
- Payment Rail Status Dashboard: real-time status of ACH, Fedwire, RTP, SWIFT rails with uptime SLA tracking.
- Fed publishes outage notifications via FedLine ticker — parse and ingest automatically.

### Mitigation
- **Queue with exponential backoff:** Payment rail outage → Kafka messages remain in topic, consumer pauses retry loop, waits with exponential backoff (1m, 2m, 4m, 8m, max 30m intervals).
- **Customer notification:** At T+30 minutes of outage, notify all customers with pending same-day transfers: "Payment processing is delayed due to a temporary Federal Reserve system issue. Your transfer will be processed as soon as the service is restored."
- **Priority ordering for recovery burst:** On Fed recovery, process in priority order: (1) Fedwire high-value (time-critical), (2) same-day ACH, (3) next-day ACH batches. Throttle submission rate to 80% of FedLine capacity to avoid overwhelming ODFI.
- **Intraday credit facility:** For corporate customers with confirmed inflows from Fedwire who are blocked, offer intraday credit to cover liquidity gap while Fedwire is down.
- **Same-day → next-day conversion:** If Fed outage persists past 3:00 PM same-day ACH cut-off, all pending same-day entries automatically re-classified as next-day with customer notification.

### Recovery
1. Fed restores FedACH at 2:30 PM. Consumer resumes, health check passes after 3 consecutive successes.
2. Process in priority order with throttled burst. Target: all pending Fedwire cleared by 4:00 PM, all pending ACH cleared by 5:00 PM.
3. Update affected transfers to `COMPLETED` as confirmations arrive. Send settlement notifications to customers.
4. Same-day ACH cut-off: coordinate with ODFI for extended cut-off window (some ODFIs offer 1-hour extension for Fed outage scenarios — confirm in advance).
5. End-of-day reconciliation: compare expected vs. actual settled transactions — resolve any gaps.
6. Outage report: document timeline, customer impact count, financial impact, actions taken.

---

## Real-Time Gross Settlement (RTGS) Timeout for Large-Value Transfer

### Scenario
A corporate customer initiates a $4.2 million Fedwire transfer at 4:45 PM ET — 15 minutes before the Fedwire Funds Service closes at 5:00 PM ET (for third-party transfers; the service fully closes at 6:30 PM). The payment is submitted but the OMAD (Output Message Accountability Data — proof of settlement) has not been received by 5:05 PM.

### Failure Mode
The transfer cannot be confirmed as settled. At 5:00 PM, no new third-party Fedwire transfers are accepted. The debit has been written to the corporate account. The OMAD never arrives — the Federal Reserve may have processed it (OMAD in transit) or may have timed out the entry. The corporate customer's counterparty expected the funds today — a failure to settle affects their own settlement obligations.

### Impact
- **Financial:** $4.2 million in the customer's account is debited but settlement is uncertain. If funds were processed by Fed but OMAD delayed — funds delivered to counterparty but we have no confirmation. If not processed — $4.2M must be re-credited.
- **Customer:** Corporate treasurer in panic — they have a legal obligation to counterparty for same-day settlement.
- **Counterparty:** If RTGS fails at 4:45 PM, the counterparty cannot re-receive funds via any other rail until tomorrow.
- **Reputational:** High-value corporate clients have zero tolerance for RTGS failures — account at risk.

### Detection
- Fedwire OMAD expected within 30 minutes of submission during normal hours.
- Alert: any Fedwire transfer > $1M without OMAD confirmation within 45 minutes → immediate P0 incident.
- After-hours monitoring: dedicated on-call engineer for Fedwire RTGS operations from 3:00 PM to 6:30 PM ET.

### Mitigation
- **Cut-off buffer:** Reject new Fedwire submissions > $1M after 4:30 PM ET (30-minute buffer before 5:00 PM cut-off). Communicate to customers: "Fedwire transfers above $1M must be submitted by 4:30 PM to guarantee same-day settlement."
- **IMAD-based status inquiry:** Query Federal Reserve status inquiry service using IMAD (Input Message Accountability Data) generated at submission. If Fed confirms processing, record OMAD from inquiry response.
- **Correspondent bank escalation:** Contact ODFI/correspondent bank ops team directly (dedicated phone line for > $1M Fedwire issues) — they can query Fed directly.
- **Same-day alternative:** For amounts < $500,000, offer same-day domestic wire via RTP (The Clearing House Real-Time Payments) which operates 24/7/365 — no cut-off.
- **Pre-submission check:** Before accepting large Fedwire at cut-off risk, display warning: "This transfer is close to the Fedwire cut-off time. Would you like to proceed with today's submission or schedule for tomorrow morning?"

### Recovery
1. Trigger P0 incident response. Assign Fedwire operations engineer and customer success manager for the corporate client.
2. Query Fed status inquiry service with IMAD. If OMAD returned from inquiry: record it, mark transfer COMPLETED. Done.
3. If no OMAD from inquiry: Fed did not process the transfer. Re-credit customer account. Initiate reversal of debit.
4. Notify corporate customer immediately: "Your $4.2M Fedwire was not processed before cut-off. Funds have been restored. Options: submit tomorrow morning at 8:00 AM, or contact your counterparty to arrange alternative settlement."
5. If counterparty suffers loss due to failed settlement, work with corporate client's legal team on remediation options.
6. Post-incident: review cut-off enforcement logic, add 30-minute buffer as a mandatory control.

---

## Cross-Cutting Transaction Processing Controls

The following controls apply universally across all transaction edge cases and represent permanent architectural safeguards rather than scenario-specific responses.

**Idempotency Architecture:**
- All write operations (transfers, payments, card authorizations) require a client-supplied or system-generated `idempotency_key` (UUID v4 format).
- Key storage: Redis SETNX with 24-hour TTL (primary). PostgreSQL unique constraint on `transactions(idempotency_key)` as authoritative fallback.
- On duplicate request with same key: return the cached response from the original request (HTTP 200 with `X-Idempotent-Replay: true` header). No re-processing.
- Key format contract: `{service_prefix}-{customer_id}-{timestamp_ms}-{random_suffix}`.

**Double-Entry Ledger Integrity:**
- Every financial movement is recorded as a pair of journal entries (debit + credit). The sum of all journal entries must equal zero at all times.
- Constraint: `SELECT SUM(amount) FROM journal_entries` must return 0.00. Any non-zero result = critical data integrity incident.
- Checked: nightly batch + on-demand during incident investigation.
- PostgreSQL constraint: `CHECK (amount != 0)` on journal_entries — zero-amount entries blocked at DB level.

**Transaction Finality Rules:**
| State | Reversible? | Who Can Reverse | Window |
|-------|------------|-----------------|--------|
| INITIATED | Yes | Customer, System | Any time before PROCESSING |
| PROCESSING | Yes (with consequences) | Compliance, Legal | Before ACH file transmitted |
| PENDING_SETTLEMENT | Limited | Operations (via ODFI) | Before NACHA cut-off |
| COMPLETED (ACH) | Via R-code return only | RDFI | 60 days (R05/R07) |
| COMPLETED (Fedwire) | Via recall request | Federal Reserve | Same business day |
| COMPLETED (RTP) | No automatic reversal | Dispute only | N/A |

**Reconciliation Schedule:**
| Reconciliation | Frequency | Tolerance | Alert Threshold |
|----------------|-----------|-----------|-----------------|
| Aurora ↔ Core Banking (Mambu) | Every 4 hours | $0.01 | Any discrepancy |
| Suspense account balance | Every 1 hour | $0.00 | Any balance > $0 |
| ACH settled vs. posted | Nightly by 6 AM | $0.00 | Any unmatched entry |
| Fedwire OMAD vs. posted | Real-time | $0.00 | Any unconfirmed > 30 min |
| Card authorization holds vs. posted | Nightly | $0.00 | Aged holds > 7 days |

**Payment Rail Health Dashboard:**
Real-time status monitoring for all rails with automatic P1 alert on degradation:

| Rail | Provider | Health Endpoint | SLA | Alert Threshold |
|------|---------|----------------|-----|-----------------|
| Same-Day ACH | Modern Treasury | `/health` ping | 99.9% | 2 consecutive failures |
| Fedwire | FedLine | TCP port check | 99.99% | 1 failure during business hours |
| RTP (Real-Time Payments) | TCH | REST `/health` | 99.99% | 1 failure |
| International SWIFT | Correspondent bank | Heartbeat | 99.5% | 3 consecutive failures |
| Card Network (Visa) | Marqeta JIT | `/ping` | 99.99% | 1 failure |

**Cut-off Times Reference:**
| Payment Type | Cut-off (ET) | Settlement |
|-------------|-------------|-----------|
| Same-Day ACH (first window) | 10:30 AM | Same day |
| Same-Day ACH (second window) | 2:45 PM | Same day |
| Next-Day ACH | 8:00 PM | Next business day |
| Fedwire (third-party) | 5:00 PM | Same day |
| Fedwire (bank-to-bank) | 6:00 PM | Same day |
| RTP (Real-Time Payments) | 24/7/365 | Immediate |
| International SWIFT | 4:30 PM | T+1 to T+5 |
