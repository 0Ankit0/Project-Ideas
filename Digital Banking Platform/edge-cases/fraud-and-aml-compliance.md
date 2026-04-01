# Edge Cases: Fraud and AML Compliance — Digital Banking Platform

---

## False Positive Fraud Block on Legitimate Large Transaction

### Scenario
A long-standing customer with a 6-year account history attempts to wire $87,000 to a title company as a down payment for a home purchase. Their typical transaction volume is under $5,000. The fraud ML model scores the transaction at 0.91 (HIGH risk) and automatically blocks it. The customer's mortgage closing is scheduled for 9:00 AM the next day.

### Failure Mode
The block is technically correct per the ML model's decision boundary, but it is a false positive — the transaction is entirely legitimate. The automatic block generates customer distress, a missed closing deadline, and potential financial harm (the customer may lose their rate lock or earnest money deposit). The customer calls frantically, but the fraud hold release process takes 24–48 hours in the standard workflow.

### Impact
- **Customer:** Extreme distress, potential financial loss ($50,000 earnest money deposit forfeiture if closing deadline missed), reputational harm to the bank.
- **Financial:** Customer attrition risk (high-value customer with $87K liquidity). Potential litigation if provable damages result from the delay.
- **Operational:** Customer service escalation (Level 3 complaint), executive escalation likely.
- **Model quality:** False positive reduces model precision metric; each false positive must be logged for retraining.

### Detection
- False positive detection is inherently retrospective — it is identified during the customer appeal process.
- Proactive signals: customer account age > 3 years, average daily balance > $25,000, no prior fraud history, and a known real estate transaction pattern (title company MCC, property address corroborates wire destination) are all signals the model should weight.
- Customer contact via call center is the primary detection mechanism in this scenario.

### Mitigation
- **Expedited review SLA:** Any fraud hold on a transaction > $25,000 for a customer with > 2-year account age and clean history → automatic escalation to Level 2 fraud analyst within 30 minutes (not 24–48 hours standard SLA). Fraud analyst has authority to release without committee approval.
- **Pre-transaction advisory:** For large wire initiations, prompt the customer: "This is a large transfer. If this is for a real estate closing or significant purchase, please call us at [number] to pre-authorize. This reduces the chance of a delay." Proactive friction reduces surprises.
- **Contextual features in model:** Incorporate destination BIC/ABA against known title company database (ALTA member list), customer-stated purpose, and prior conversations flagged in CRM.
- **Step-up instead of hard block:** For transactions in the 0.75–0.95 fraud score range, prefer step-up authentication (video call with ID verification, or secure upload of wire instructions/purchase agreement) over outright block.
- **Release mechanism:** Customers must be able to self-serve an expedited human review request via app — not just via phone. Target SLA: < 2 hours for review completion.

### Recovery
1. Level 2 analyst reviews within 30 minutes: checks account history, calls customer, verifies wire instructions against provided closing disclosure.
2. On verification: release hold, re-submit wire. Flag false positive in fraud system for model feedback loop.
3. If closing was delayed: customer success team contacts customer. If any provable financial harm (e.g., rate lock extension fee): reimburse as goodwill gesture.
4. Model feedback: log (transaction_id, features, outcome=FALSE_POSITIVE, analyst_notes) to `fraud.feedback` Kafka topic → Featurespace model retraining pipeline.
5. Policy review: evaluate whether blocking threshold should be raised for customers with > 5-year history and clean record; model recalibration cadence (monthly).

---

## AML Alert Storm During Market Volatility Event

### Scenario
A major geopolitical event causes extraordinary equity market volatility. From 9:30 AM to 11:00 AM, 127,000 customers move large balances between accounts (liquidating brokerage positions, transferring to savings, moving to money market). The AML transaction monitoring rules engine fires 14,200 alerts in 90 minutes — a normal day sees 300–400 alerts. The alert queue overwhelms the AML team (12 analysts), who normally process 30–50 alerts per day.

### Failure Mode
The AML team cannot review 14,200 alerts in the 30-day SAR filing window. Alerts age without review. Some alerts that deserve investigation are buried in the queue. The institution faces regulatory risk for failing to investigate and file SARs where required. If the system auto-escalates all alerts, the AML team is completely paralyzed.

### Impact
- **Regulatory:** FinCEN may cite the institution for failure to maintain effective AML controls if alerts are not reviewed within required windows. Potential $10M+ BSA penalty.
- **Operational:** AML team burnout, errors from manual processing under pressure, missed genuine suspicious activity.
- **Customer:** Legitimate customers may be incorrectly flagged and have accounts restricted if auto-action is applied to unreviewed alerts.

### Detection
- Alert volume monitoring: dashboard shows real-time alert count vs. daily baseline. >500% spike triggers immediate AML management notification.
- Alert aging dashboard: shows median alert age vs. 30-day SAR deadline. If median age > 20 days, escalate to Chief Compliance Officer.

### Mitigation
- **Alert triaging and scoring:** Not all alerts are equal. AML system must score each alert by: (a) alert type (structuring vs. large cash vs. sanctions vs. velocity), (b) customer risk rating, (c) amount, (d) novelty (first-time pattern vs. recurring). Only CRITICAL and HIGH alerts require analyst review; MEDIUM alerts enter a 48-hour auto-disposition queue (system gathers evidence, analyst reviews only if evidence score remains ambiguous).
- **Market event suppression rules:** Maintain a library of suppression rules that activate during known market events (earnings seasons, geopolitical events, FOMC announcements). These rules elevate the threshold for velocity alerts temporarily (e.g., "large balance movement from brokerage" alert suppressed if equity VIX > 30).
- **Overflow staffing plan:** Pre-agreed surge staffing contract with a third-party AML managed services provider (e.g., KPMG, Deloitte financial crimes team). Activate when alert volume > 300% of daily average for > 2 hours.
- **Auto-disposition framework:** Low-risk alerts (customer risk = LOW, amount < $25,000, pattern matches known non-suspicious behavior) can be auto-closed with documented rationale — these are defensible to regulators if audit trail is maintained.
- **SAR deadline tracker:** Automated Jira ticket for every alert aged > 20 days with an assigned analyst and due date. Escalates to CCO if unworked at 25 days.

### Recovery
1. AML manager declares alert storm — activates overflow staffing protocol.
2. Apply retroactive suppression rules to classify market-volatility-driven alerts as low-risk; auto-close with documented rationale.
3. Remaining high-risk alerts prioritized by analyst queue. Overflow team processes medium-risk alerts.
4. 30-day deadline tracker: any alert approaching deadline gets priority regardless of risk score.
5. Regulatory disclosure: if institution cannot process all alerts within regulatory windows, proactively disclose to examiner with documented remediation plan (better than having examiners discover unprocessed alerts).
6. Post-event: recalibrate transaction monitoring rules to reduce false-positive rate in volatile market conditions. Submit rule change through model risk management governance process.

---

## Sanctions List Update Lag — OFAC / UN List Not Yet Reflected

### Scenario
OFAC publishes an update to the SDN (Specially Designated Nationals) list at 8:42 AM ET, adding a previously undesignated entity. Our AML screening system (ComplyAdvantage) has a 4-hour refresh cadence. Between 8:42 AM and 12:30 PM, our system processes 37 transactions totaling $284,000 to and from parties who match the newly designated entity.

### Failure Mode
The 37 transactions are screened against a stale OFAC list and pass (result: CLEAR). Post-refresh at 12:30 PM, the entity appears as a sanctions hit — but the transactions have already been processed and funds delivered. OFAC regulations require that U.S. persons block property of designated parties "as soon as practicable" after designation. Processing transactions in the interim constitutes an apparent OFAC violation.

### Impact
- **Regulatory:** Civil money penalty risk — OFAC calculates penalties per transaction ($20M+ under IEEPA for egregious violations). Even non-egregious violations may result in $500K+ penalties per transaction.
- **Operational:** Must file Voluntary Self-Disclosure (VSD) with OFAC to mitigate penalty exposure.
- **Financial:** Funds may need to be blocked and reported; if already transferred internationally, recall attempts required.

### Detection
- OFAC publishes SDN list changes via RSS feed and email notification (OFAC mailing list subscription).
- ComplyAdvantage publishes an update notification via their API when list refreshes.
- Post-refresh screening: when AML system refreshes, retroactively re-screen transactions from the prior 6 hours against the new list — any that now HIT trigger an immediate alert.

### Mitigation
- **Reduce refresh cadence:** Move from 4-hour to 15-minute refresh using ComplyAdvantage's streaming API (available on enterprise tier). OFAC list changes are rare but impactful — minimum refresh cadence.
- **OFAC email alert integration:** Subscribe to OFAC push notifications (email/RSS). On receipt of update notification, trigger an immediate out-of-band list refresh — do not wait for scheduled cycle.
- **Real-time screening API:** For high-value transactions (> $10,000), call ComplyAdvantage's real-time API (not cached results) as a secondary check. Accept latency increase (200–300ms) for this risk tier.
- **Post-refresh retroactive scan:** On every list refresh, re-screen all transactions from the prior 8 hours. Configurable window. Any newly-HIT transactions trigger immediate hold and compliance escalation.
- **Voluntary Self-Disclosure playbook:** Pre-written OFAC VSD template, legal team pre-briefed. VSD reduces OFAC penalty by 50% on average. File within 10 business days of discovery.

### Recovery
1. Post-refresh re-screen identifies 37 transactions that now match SDN entity.
2. Immediately block any accounts or pending transactions associated with the designated entity.
3. Legal team engaged within 1 hour. OFAC compliance counsel reviews facts.
4. Prepare and file Voluntary Self-Disclosure within 10 business days.
5. Recall initiated for any international wires (SWIFT gpi Recall if applicable).
6. For domestic ACH: R05 (Unauthorized Debit) return or R07 return initiated.
7. OFAC compliance: block funds in designated account per OFAC blocking requirements; file OFAC-blocked property report within 10 business days.
8. Upgrade refresh cadence to real-time as emergency remediation.

---

## Structuring Detection Edge Cases — Smurfing Across Accounts

### Scenario
A sophisticated money laundering operation involves 23 individuals (smurfs) opening accounts at the platform over a 6-week period. Each account conducts cash-equivalent transactions just below $10,000 (typically $9,500–$9,700) — the CTR reporting threshold. The accounts appear unrelated based on individual profiles, but they share IP address ranges, device fingerprints, and all transfer funds to the same destination account in rotating patterns.

### Failure Mode
Rule-based AML monitoring detects structuring on a single-customer basis (no individual account crosses $10,000). The cross-account relationship analysis requires graph-based analytics that are not part of the standard rule-set. Each account individually appears compliant; collectively they represent organized structuring activity (31 U.S.C. § 5324).

### Impact
- **Regulatory:** Failure to detect and report structuring is a BSA violation. FinCEN may penalize the institution for inadequate transaction monitoring controls.
- **Financial:** Money laundering proceeds flowing through the platform.
- **Reputational:** Association with money laundering if discovered by law enforcement and publicly disclosed.

### Detection
- **Graph analytics:** Build a relationship graph linking accounts by: shared IP address, shared device fingerprint, shared phone number, shared SSN prefix, same enrollment cohort. Run community detection algorithm (Louvain or Girvan-Newman) weekly.
- **Aggregated structuring rule:** Daily aggregation across accounts in the same graph community. If aggregate exceeds $10,000 from a cluster of accounts to a common destination within 24 hours → structuring alert.
- **Velocity anomaly:** 23 new accounts in 6 weeks all sending $9,500–$9,700 to the same destination ACH routing+account number → specific rule: "multiple originators, same destination, sub-threshold amounts."

### Mitigation
- **Entity resolution:** Link accounts with probabilistic matching on device fingerprint (exact match), phone number (fuzzy match after normalization), IP ASN (same residential ISP subnet), enrollment IP geolocation (within 5km of each other). Assign a shared `entity_group_id`.
- **Aggregated CTR:** If aggregate cash-equivalent transactions for an entity group exceed $10,000 in a day, file a CTR for the group. FinCEN CTR instructions require filing for aggregated transactions.
- **Joint SAR:** If structuring pattern confirmed across entity group: file a single SAR covering all 23 accounts. Coordinate with FinCEN if criminal referral is appropriate.
- **Account suspension:** Suspend all accounts in the group pending investigation. Risk: some accounts may be held by innocently recruited smurfs (unaware participants) — bereavement team handling required.
- **New account monitoring:** Accounts < 90 days old face tighter sub-threshold velocity monitoring (5 transactions per day > $5,000 triggers alert).

### Recovery
1. Graph analytics identifies entity group → alert fires → AML analyst assigned.
2. Analyst reviews relationship graph, transaction patterns, destination account.
3. If structuring confirmed: suspend all 23 accounts simultaneously (coordinated update to prevent fund movement during investigation).
4. SAR filed within 30 days for the group.
5. Law enforcement referral (BSA Section 356 — voluntary referral; or mandatory if SAR indicates criminal activity imminently harmful).
6. Funds recovery: if transfers still in ACH float, initiate R10 returns. If transferred, file FinCEN Form 8300 equivalent and coordinate with law enforcement for civil forfeiture.

---

## Correspondent Banking Chain Compliance Failure

### Scenario
The platform processes international wires through a correspondent banking relationship. For a $450,000 international wire to Singapore, the payment traverses: Platform → US Correspondent Bank → Singapore Correspondent Bank → Beneficiary Bank. The Singapore correspondent bank fails their own AML screening on the beneficiary and returns the wire. However, the return reason is coded ambiguously, and our platform does not recognize it as AML-related versus a simple routing error.

### Failure Mode
The wire is returned with code "Reason: BENEFICIARY UNABLE TO BE CREDITED" — which could mean account closed, insufficient information, or AML rejection. Our system treats it as a routing error and automatically attempts re-submission with a corrected beneficiary account number (provided by the customer). The second attempt also goes to the same beneficiary who is AML-blocked in Singapore.

### Impact
- **Regulatory:** Repeated attempts to transfer funds to an AML-blocked party may constitute willful disregard of AML controls — OFAC/FinCEN enforcement risk.
- **Financial:** $450,000 in limbo during the investigation period.
- **Customer:** Legitimate customer (if the rejection is erroneous) is blocked from sending a large transfer.
- **Operational:** Correspondent bank relationships may be strained if the platform repeatedly submits problematic payments.

### Detection
- SWIFT return message parsing: extract and interpret all SWIFT reason codes, including proprietary codes used by correspondent banks. Maintain a mapping table of reason codes to root cause categories (AML, account error, format error, sanctions).
- Pattern detection: same beneficiary account returned twice within 30 days → mandatory compliance review before third submission.

### Mitigation
- **Return reason classification:** Invest in comprehensive SWIFT MT199 / ISO 20022 return reason parsing. Any return that cannot be definitively classified as "non-AML" is treated as potentially AML-related and routed to compliance.
- **Beneficiary screening:** Screen the beneficiary against OFAC/UN/EU lists before each submission. If the beneficiary is in a high-risk jurisdiction (FATF grey list or black list countries), require enhanced due diligence.
- **Correspondent bank communication:** Establish a direct compliance hotline with key correspondent banks. On ambiguous returns, call the correspondent bank compliance team directly before re-submitting.
- **Re-submission hold:** Automatic 24-hour hold on any re-submission of a previously returned international wire > $100,000. Compliance officer must review and approve.
- **FATF jurisdiction check:** Singapore is a well-regulated jurisdiction, but the ultimate beneficiary's country of origin matters. Trace the full correspondent chain — if any intermediary is in a high-risk jurisdiction, apply enhanced controls.

### Recovery
1. Compliance officer reviews return reason, contacts Singapore correspondent bank compliance team.
2. Confirms whether return is AML-related or administrative error.
3. If AML: suspend re-submission, file SAR if threshold met, notify customer that transfer cannot proceed (without revealing SAR — tipping off prohibition).
4. If administrative error: resolve the underlying issue (beneficiary account details), re-submit with compliance sign-off.
5. Update SWIFT reason code mapping table with the new code encountered.
6. Review correspondent banking due diligence for all correspondent relationships annually.

---

## First-Party Fraud — Synthetic Identity

### Scenario
A synthetic identity was created using a real SSN (belonging to a minor who has no credit history), a fabricated name, and a realistic constructed address. The fraudster spent 8 months building a credit profile, making small on-time payments on a secured credit product. They then applied for a $40,000 personal loan, were approved based on the manufactured credit history, received the funds, and stopped all payments. The account defaults.

### Failure Mode
First-party fraud is the hardest fraud type to detect because the "customer" behaves legitimately throughout the credit-building phase. Fraud scores during the application are LOW (built-up history, reasonable patterns). The fraud only becomes apparent at charge-off.

### Impact
- **Financial:** $40,000 credit loss (charge-off). Industry-wide first-party fraud costs US banks $6B+ annually.
- **Regulatory:** If the SSN belongs to a child and was used without the child's knowledge, it is identity theft — reportable to FinCEN and the FTC.
- **Victim:** The child whose SSN was used will face credit file complications when they turn 18.

### Detection
- **SSN issuance validation:** Cross-reference SSN with Social Security Administration's CBSV (Consent Based SSN Verification) service. Verify that the SSN belongs to a person with the stated name and DOB.
- **Credit file age vs. application age:** FICO score exists but credit file is only 8 months old? Flag for enhanced review — thin credit files with rapid bureau file creation are a synthetic identity signal.
- **Identity velocity:** Same SSN or address used to open accounts at multiple institutions within 12 months (detected via consortium data from Early Warning Services — Chex Systems). Consortium fraud scores > 600 → decline.
- **Velocity of credit applications:** Multiple credit pulls (hard inquiries) within 90 days is a red flag.
- **Biometric re-verification:** At loan application, require liveness check with document verification again (not just at account opening) — if the "customer" cannot pass liveness, synthetic identity confirmed.

### Mitigation
- **SSA CBSV check:** Mandatory for all credit applications > $10,000. $0.05 per verification — cheap insurance.
- **Consortium membership:** Subscribe to Chex Systems, Early Warning Services, LexisNexis Fraud Defense Network. Cross-institutional synthetic identity signals dramatically improve detection.
- **Machine-readable zone (MRZ) validation:** At KYC, validate ID document MRZ checksum and cross-reference name/DOB/document number against issuing authority where possible.
- **Address history analysis:** Synthetic identities often use addresses that do not appear in any historical records. Cross-check address against USPS, property records, prior credit history.
- **Model feature:** Add "credit file age vs. inquiry count vs. account age" features to underwriting model. Thin new files with multiple recent inquiries across institutions receive significant risk penalty.

### Recovery
1. Charge-off logged. Fraud investigation team reviews the account — determines synthetic identity.
2. File police report and provide to credit bureaus to suppress the fraudulent credit tradeline.
3. Notify the SSN owner (the child's parents if minor) that their SSN was used fraudulently. Provide free credit monitoring.
4. Report to FinCEN if proceeds from synthetic identity fraud exceed $5,000 (SAR).
5. Consortium: report the synthetic identity profile to Chex Systems / EWS to prevent reuse at other institutions.
6. Model improvement: add detection features identified during this investigation to fraud model retraining dataset.

---

## SAR Filing Deadline Miss — FinCEN 30-Day Requirement

### Scenario
An AML analyst flags a suspicious transaction pattern on Day 1. A SAR case is opened. Due to staff turnover and workload, the case remains in `UNDER_INVESTIGATION` status. On Day 29, a compliance manager notices the aging dashboard and realizes the SAR must be filed tomorrow. The analyst who originally worked the case is no longer employed at the bank. Case notes are sparse.

### Failure Mode
If the SAR is not filed by Day 30, the institution is in technical violation of 31 CFR § 1020.320(b)(3). FinCEN can fine institutions for late SAR filings. However, a well-documented reason for delay (investigation complexity) may be considered a mitigating factor if the SAR is filed within the 30-day extension window.

### Impact
- **Regulatory:** Late SAR filing is a BSA violation. Civil money penalties up to $25,000 per day of violation (BSA Section 5321). Examiners scrutinize SAR timeliness as a key AML program indicator.
- **Operational:** Incomplete case file — analyst who worked it is gone. Remaining team must reconstruct investigation on Day 29–30.
- **Institutional:** Pattern of late SAR filings → MRA (Matter Requiring Attention) or formal enforcement action.

### Detection
- **Automated SLA tracker:** Every AML case gets a FinCEN filing deadline (Day 30 from detection, extendable to Day 60 for complex cases with documented reason). Jira tickets auto-created; SLA field visible on dashboard.
- **Escalation ladder:** Day 20: analyst reminder. Day 23: team lead review. Day 25: CCO notification. Day 28: legal and compliance director escalation. Day 29: executive notification.

### Mitigation
- **Case documentation standards:** Every AML case requires mandatory fields completed before it can remain in UNDER_INVESTIGATION status for > 7 days: (1) investigator assigned, (2) summary of suspicious activity, (3) key transactions identified, (4) initial SAR narrative draft. Enforced by workflow system — cannot advance without completion.
- **30-day extension procedure:** If investigation genuinely complex, document the extension reason in the case file and note that a 60-day window applies. Extension must be documented — not just assumed.
- **Staff turnover continuity:** On employee offboarding, all open AML cases must be reassigned within 1 business day. Case management system sends alert to manager when investigator terminates with open cases.
- **Emergency SAR procedure:** A "rapid SAR" template for cases approaching deadline where full investigation is incomplete. File the SAR with available information; FinCEN allows amendment within 60 days to add additional details. Filing an incomplete SAR on time is better than not filing.

### Recovery
1. Day 29: CCO and compliance director review the case. Reconstruct facts from transaction records, Kafka audit trail, and any existing notes.
2. Draft SAR narrative from available evidence — use emergency SAR template.
3. File SAR via BSA E-Filing by Day 30. Even a partial SAR satisfies the filing deadline.
4. If Day 30 is missed (rare): file as soon as possible with a cover explanation of the delay. Self-report to primary regulator examiner that a late filing occurred and corrective actions taken.
5. Corrective action: implement all SAR tracking controls listed in mitigation. Conduct look-back for other cases approaching deadline.
6. Training: mandatory AML deadline training for all compliance staff; annual certification.

---

## Cross-Cutting Fraud and AML Controls

The following controls apply universally across all fraud and AML edge cases and represent permanent architectural safeguards.

**Fraud Model Governance:**
- Model risk management (MRM) policy: every fraud/AML model requires (a) validation by a model validator independent of the development team, (b) ongoing performance monitoring (monthly), (c) annual full revalidation.
- Champion/Challenger framework: production model (champion) runs in parallel with candidate model (challenger) on 10% of traffic. If challenger outperforms champion on precision/recall for 30 consecutive days → promote challenger.
- Model drift detection: PSI (Population Stability Index) calculated weekly on input feature distributions. PSI > 0.25 → model retrain triggered.
- False positive rate target: < 0.5% of all screened transactions. Current FPR published on internal risk dashboard.

**AML Program Four Pillars (BSA/FinCEN):**
1. **Policies and Procedures:** Written BSA/AML/OFAC policy approved by Board of Directors annually. Procedures documented for every transaction type and customer segment.
2. **Designated Compliance Officer:** BSA Officer appointed by Board, reports directly to CEO and Board Audit Committee. Deputy BSA Officer designated.
3. **Training:** All employees receive annual BSA/AML training. Customer-facing roles: quarterly. New hires: within 30 days of joining.
4. **Independent Testing:** Annual independent audit of AML program (internal audit or external auditor). Findings tracked to remediation completion.

**Suspicious Activity Reporting Reference:**
| SAR Threshold | Transaction Type | Filing Deadline | Extension |
|--------------|-----------------|-----------------|-----------|
| $5,000+ | Insider fraud (bank employee) | 30 days from detection | + 30 days (documented) |
| $5,000+ | General suspicious activity | 30 days from detection | + 30 days (documented) |
| $25,000+ | Structuring | 30 days from detection | + 30 days (documented) |
| Any amount | Terrorist financing | Immediately upon detection | No extension |

**OFAC Compliance Metrics Dashboard:**
- Sanctions list refresh lag: target < 15 minutes (real-time streaming API)
- Screening coverage: 100% of outbound transactions, 100% of new customers, 100% of name/address changes
- False positive rate: monitored monthly; target < 99.5% false positive rate (< 0.5% true positive)
- Blocked property reports: filed within 10 business days of blocking
- VSD filings (if applicable): filed within 10 business days of discovery

**Fraud-AML Coordination Protocol:**
When a transaction is flagged by BOTH the fraud engine (score > 0.85) AND the AML screener (sanctions HIT), a coordinated response is required:
1. Fraud team and AML team both notified within 15 minutes.
2. Joint investigation team formed — AML leads (regulatory obligation), Fraud team supports.
3. Single case record in case management system — no duplicate investigations.
4. SAR filing responsibility: AML team (even if fraud team identified the activity).
5. Customer communication: AML team controls (tipping-off prohibition applies).
6. Law enforcement referral: joint decision by BSA Officer and Head of Fraud.

---

## Fraud and AML Technology Stack Reference

**Fraud Detection:**
| Component | Technology | SLA | Fallback |
|-----------|-----------|-----|---------|
| Real-time scoring | Featurespace ARIC (gRPC) | 200ms P99 | Rule-based fallback scoring |
| Feature store | Redis Cluster (velocity counts) | 5ms P99 | Stale features (5-min TTL) |
| Model serving | TorchServe (PyTorch ensemble) | 150ms P99 | Previous model version |
| Shadow model | Sardine (parallel scoring) | No blocking SLA | N/A |
| Feedback loop | Kafka → retraining pipeline | T+24h | Manual label injection |

**AML Transaction Monitoring:**
| Component | Technology | Frequency | Coverage |
|-----------|-----------|-----------|---------|
| Sanctions screening | ComplyAdvantage API | Real-time per transaction | OFAC, UN, EU, HMT, PEP |
| Transaction monitoring rules | Drools rules engine | Real-time (event-driven) | All transaction types |
| Graph-based structuring detection | Neo4j (or Amazon Neptune) | Nightly batch | All accounts linked by entity |
| Adverse media monitoring | ComplyAdvantage news feed | Daily refresh | All customers |
| CTR aggregation | Kafka Streams | Real-time | All cash-equivalent transactions |
| SAR case management | Actimize (or Feedzai) | Real-time case creation | All flagged alerts |

**Key Performance Indicators (Fraud and AML):**
| KPI | Target | Measurement Frequency |
|-----|--------|-----------------------|
| Fraud detection rate (sensitivity) | > 92% | Monthly model evaluation |
| False positive rate | < 0.5% | Monthly model evaluation |
| Average fraud score latency | < 200ms P99 | Real-time (1-minute window) |
| AML alert false positive rate | < 90% | Monthly |
| SAR filing on-time rate | 100% | Monthly |
| CTR filing on-time rate | 100% | Daily |
| OFAC list refresh lag | < 15 minutes | Real-time monitoring |
| AML model review cadence | Annual + event-triggered | Model Risk Management |
