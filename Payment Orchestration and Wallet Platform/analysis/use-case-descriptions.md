# Use Case Descriptions — Payment Orchestration and Wallet Platform

This document describes the primary business use cases in implementation-ready form. Each use case identifies actors, preconditions, trigger, main success path, alternate flows, and resulting events so teams can derive APIs, sagas, and operational tooling consistently.

## 1. Use Case Index

| Use Case | Goal | Primary Actors | Core Services |
|---|---|---|---|
| UC-01 | Create and confirm a payment intent | Merchant backend, Customer | API Gateway, Orchestration, Risk, Vault, PSP Adapter |
| UC-02 | Capture an authorized payment | Merchant Operator | Orchestration, Ledger, Settlement |
| UC-03 | Top up or transfer wallet funds | Customer, Platform | Wallet, Ledger, FX, Risk |
| UC-04 | Release merchant payout | Treasury Analyst, Compliance Officer | Payout, Wallet, AML, Ledger, Bank Rail |
| UC-05 | Issue full or partial refund | Merchant Support Agent | Refund, PSP Adapter, Ledger, Webhook |
| UC-06 | Process chargeback lifecycle | PSP, Risk Analyst, Merchant Operator | Dispute, Ledger, Wallet, Evidence Store |
| UC-07 | Run settlement and reconciliation | Finance Manager | Settlement, Reconciliation, Ledger |
| UC-08 | Approve merchant onboarding for payouts | Merchant Admin, Compliance Officer | Merchant Config, KYC Provider, AML, Payout |

## 2. UC-01 Create and Confirm a Payment Intent

**Goal:** Accept a payment request, route it to the correct PSP, and create a single auditable payment intent without duplicate charging.

**Primary actors:** Merchant backend, Customer, PSP, Risk service

**Preconditions:**
- Merchant API key and JWT are valid.
- Merchant is enabled for the requested currency and payment method.
- Customer payment method is tokenized or PSP-hosted collection is available.

**Trigger:** `POST /v1/payment-intents` followed by `POST /v1/payment-intents/{id}/confirm` or a combined auto-confirm flag.

**Main success path:**
1. Gateway authenticates the caller and enforces rate limits.
2. Orchestration service creates the payment intent in `CREATED` state and stores the idempotency key.
3. Risk service returns `ALLOW`.
4. Routing engine scores eligible PSPs and persists the selected primary route plus fallback candidates.
5. Vault returns a token or confirms an existing token reference.
6. PSP adapter submits the authorization request.
7. Provider returns success with provider reference.
8. Orchestration records an `AUTHORIZED` state and emits `payment.authorized.v1`.
9. Merchant receives synchronous response and later a webhook with the same correlation identifiers.

**Alternate and error flows:**
- If risk returns `REVIEW`, intent moves to `REVIEW_REQUIRED` and no PSP call occurs.
- If provider times out before returning an authorization reference, the attempt becomes `PSP_RESULT_UNKNOWN`; the platform polls provider status before any reroute.
- If provider returns a reroutable transport failure, orchestration submits one fallback attempt within the retry budget.
- If 3DS2 is required, payment intent moves to `ACTION_REQUIRED` and stores the challenge payload.
- If the same idempotency key is retried with identical payload, the original response is replayed.

**Postconditions:**
- Exactly one surviving successful authorization exists per intent.
- Attempt history, routing rationale, and risk decision are audit logged.

**Events produced:** `payment.intent.created.v1`, `payment.review_required.v1`, `payment.authorized.v1`, `payment.authorization_failed.v1`

## 3. UC-02 Capture an Authorized Payment

**Goal:** Convert an authorization into settled funds and create the proper receivable and merchant liability entries.

**Primary actors:** Merchant Operator, Orchestration service, Ledger service, Settlement service

**Preconditions:**
- Payment intent is `AUTHORIZED` or `PARTIALLY_CAPTURED`.
- Authorization has not expired.
- Requested capture amount is within the uncaptured authorized amount.

**Trigger:** `POST /v1/payment-intents/{id}/capture`

**Main success path:**
1. Orchestration service validates allowable capture amount.
2. Provider capture call is submitted using the original provider reference.
3. Provider acknowledges the capture.
4. Ledger posts capture recognition journal lines for gross, fees, and merchant pending funds.
5. Orchestration updates capture totals and emits `payment.captured.v1`.
6. Settlement service consumes the event and places the capture into the next eligible batch.

**Alternate and error flows:**
- Partial capture leaves the payment in `PARTIALLY_CAPTURED` until full capture or auth expiry.
- Capture retries with the same idempotency key replay the original provider outcome.
- If ledger posting fails after provider capture succeeds, the payment moves to `OPERATIONS_HOLD` and payout eligibility is blocked until replay succeeds.
- If capture is requested after auth expiry, the request is rejected and the intent is voided.

**Postconditions:**
- Captured amount is reflected in both the payment aggregate and the ledger.
- Settlement batch candidate exists for the captured amount.

**Events produced:** `payment.captured.v1`, `ledger.journal.posted.v1`, `settlement.candidate.created.v1`

## 4. UC-03 Top Up or Transfer Wallet Funds

**Goal:** Support wallet credits, debits, and wallet-to-wallet transfers with clear balance bucket movement.

**Primary actors:** Customer, Wallet service, Ledger service, FX service

**Preconditions:**
- Wallet exists and is not frozen for the requested operation.
- Currency sub-wallet exists or can be lazily provisioned.
- Required AML or velocity checks have passed.

**Trigger:** `POST /v1/wallets/{id}/credit`, `POST /v1/wallets/{id}/debit`, `POST /v1/wallets/{id}/transfer`, or `POST /v1/wallets/{id}/convert`

**Main success path:**
1. Wallet service validates balance and freeze conditions.
2. For FX operations, FX service locks the rate used for the transfer.
3. Ledger posts the balanced journal.
4. Wallet read model updates `available`, `pending_in`, `pending_out`, or `reserved` as required.
5. Caller receives the resulting balance snapshot and transaction references.

**Alternate and error flows:**
- Insufficient balance returns a validation error without creating a journal.
- If destination wallet update fails, the entire transfer transaction rolls back.
- A wallet on compliance hold accepts inbound credits but rejects outbound movements.
- Cross-currency conversion fails if the referenced rate lock expired or the rate became stale.

**Postconditions:**
- Wallet balances remain derivable from journal entries.
- Transfer and FX metadata are queryable for audit and reconciliation.

## 5. UC-04 Release Merchant Payout

**Goal:** Move cleared merchant funds to a bank rail without violating KYC, AML, reserve, or reconciliation controls.

**Primary actors:** Treasury Analyst, Compliance Officer, Payout service, Bank rail adapter

**Preconditions:**
- Merchant wallet has sufficient `available` balance.
- Merchant onboarding is `VERIFIED`.
- No blocking AML or sanctions case is open.
- No unresolved high-severity reconciliation break exists for the merchant.

**Trigger:** Scheduled payout window or `POST /v1/payouts`

**Main success path:**
1. Payout service reserves the requested funds by moving them from `available` to `pending_out`.
2. AML screening runs for threshold-triggering payouts.
3. Bank rail adapter creates the outbound transfer.
4. Ledger posts payout initiation journal lines.
5. On bank confirmation, payout status becomes `PAID` and `pending_out` is cleared.

**Alternate and error flows:**
- If KYC is stale, payout is created in `PENDING_REVIEW` and funds remain reserved.
- If bank dispatch times out, payout becomes `RAIL_RESULT_UNKNOWN`; the platform queries bank status before retrying.
- If the bank returns the payout later, a payout return journal moves funds from clearing back to merchant `available` or `reserved` based on risk policy.

**Postconditions:**
- Bank dispatch outcome and ledger state stay aligned through reconciliation.
- Merchant receives webhook and console status updates.

## 6. UC-05 Issue Full or Partial Refund

**Goal:** Return captured funds to the customer without exceeding captured amount or losing auditability.

**Primary actors:** Merchant Support Agent, Refund service, PSP adapter, Ledger service

**Preconditions:**
- Payment is captured or settled.
- Refundable amount remains.
- Refund window has not expired.

**Trigger:** `POST /v1/payment-intents/{id}/refunds`

**Main success path:**
1. Refund service calculates remaining refundable amount.
2. A refund record is created using the caller idempotency key.
3. Original PSP adapter submits the refund.
4. Ledger posts refund reserve or reversal entries based on whether funds are already settled to the merchant.
5. Payment intent totals are updated and a refund webhook is emitted.

**Alternate and error flows:**
- Partial refund keeps the payment in `PARTIALLY_REFUNDED`.
- Duplicate refund requests with same key replay the first result.
- If provider webhook arrives before synchronous response, the webhook path still resolves the same refund record idempotently.
- If refund fails after merchant funds were reserved, a compensating journal releases the reserve.

## 7. UC-06 Process Chargeback Lifecycle

**Goal:** Intake a dispute, manage evidence deadlines, and automatically apply financial consequences.

**Primary actors:** PSP webhook source, Risk Analyst, Merchant Operator, Ledger service

**Preconditions:**
- Original payment exists and has a provider reference.
- Network case ID is unique per provider.

**Trigger:** Provider dispute webhook or file ingest

**Main success path:**
1. Webhook intake validates signature and stores raw payload.
2. Chargeback record is created in `OPEN` or `NEEDS_RESPONSE`.
3. Merchant reserve is increased or merchant wallet balance is held.
4. Evidence tasks and SLA timers are created.
5. On provider verdict, the case is closed as `WON` or `LOST`.
6. If lost, ledger posts chargeback principal and fee debits automatically.

**Alternate and error flows:**
- Duplicate provider case events are deduplicated by provider case ID and event ID.
- If evidence arrives after the deadline, the package is stored but marked late and not auto-submitted.
- If the merchant has insufficient available balance, the shortfall is recorded as a negative reserve receivable and payouts remain blocked.

## 8. UC-07 Run Settlement and Reconciliation

**Goal:** Close the business day by matching ledger activity to PSP and bank data.

**Primary actors:** Finance Manager, Settlement service, Reconciliation service

**Preconditions:**
- Capture events exist for the settlement date.
- PSP clearing files and bank statement files are accessible or scheduled.

**Trigger:** Nightly scheduler or operator rerun request

**Main success path:**
1. Settlement service groups captures by merchant, provider, currency, and business date.
2. Batch totals for gross, fees, refunds, chargebacks, and net are stored.
3. Reconciliation service ingests provider files and bank files.
4. Matching engine classifies each line as reconciled or broken.
5. Finance team reviews high-severity breaks and posts supervised adjustments when needed.
6. Run is attested and exported for finance close.

**Alternate and error flows:**
- Missing provider file keeps the run in `WAITING_ON_PROVIDER`.
- A bank statement delay creates `TIMING` breaks rather than false losses.
- A rerun reuses immutable input snapshots unless explicitly rebuilt by finance.

## 9. UC-08 Approve Merchant Onboarding for Payouts

**Goal:** Verify merchant identity and enable payout and wallet-risk-sensitive features.

**Primary actors:** Merchant Admin, Compliance Officer, KYC provider, AML provider

**Preconditions:**
- Merchant account exists in `DRAFT` or `SUBMITTED` state.
- Required business profile fields and beneficial owner data are provided.

**Trigger:** Merchant submits onboarding package or updates missing information.

**Main success path:**
1. Merchant profile is validated for completeness.
2. KYC provider screens business identity and beneficial owners.
3. AML provider screens names and bank accounts.
4. Compliance officer reviews exceptions.
5. Merchant is marked `VERIFIED`; payout and wallet debit permissions are enabled.

**Alternate and error flows:**
- Missing or expired documents move the profile to `ACTION_REQUIRED`.
- Sanctions matches move the profile to `RESTRICTED` and block payouts.
- Provider outage leaves the profile in `PROVIDER_PENDING` but allows safe read-only merchant configuration updates.

## 10. Cross-Use-Case Event and SLA Rules

- Online create or confirm operations must complete within 5 seconds including routing retries.
- Ledger posting is part of the critical path for any financial outcome that changes merchant-facing balances.
- Any use case that reaches an ambiguous external state must record the ambiguity explicitly and stop automatic retries until status is known.
- Every use case must be operable from an immutable event history plus deterministic replay logic.
