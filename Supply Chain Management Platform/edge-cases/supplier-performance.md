# Edge Cases — Supplier Performance Management

This document covers edge cases in supplier performance scoring, monitoring, and lifecycle management within the Supply Chain Management Platform (SCMP). Each scenario describes failure modes, their downstream impact, detection mechanisms, and the system's automated and manual response procedures.

---

## Supplier Disputes Performance Score

**Scenario**: A supplier formally disputes their quarterly performance score, claiming the underlying data is incorrect — for example, alleging that certain delivery delays were caused by the buyer's own warehouse refusing dock appointments, not by the supplier.

**Impact**: Unresolved disputes erode trust between the procurement organization and the supplier, introduce risk of contract renegotiation or termination, and may expose the organization to legal liability if the disputed score influences contract renewal decisions or financial penalties. Additionally, if an incorrect score is published and used for tier classification, procurement decisions downstream may be flawed.

**Detection**: The dispute is initiated through one of two channels: (1) the supplier submits a formal dispute through the Supplier Portal using the "Dispute Score" action on their performance dashboard, or (2) the supplier contacts their assigned procurement manager directly, who then raises the dispute within the internal procurement workflow module. The system recognizes a dispute submission as a trigger event.

**Handling Steps**:
1. Supplier submits dispute with written justification and supporting evidence (e.g., carrier proof-of-delivery, dock appointment logs, email correspondence).
2. Procurement manager receives a dispute review task in their workflow queue with a 5-business-day SLA.
3. Score publication is frozen — the disputed score is not disseminated to downstream consumers (contract renewal module, risk tier engine, vendor ranking reports).
4. Data steward extracts raw scoring inputs: all POs included in the period, their confirmed delivery dates, goods receipt timestamps, and the scoring formula applied.
5. Procurement manager compares raw data against the supplier's submitted evidence.
6. If evidence is valid, a score amendment is created with corrected data and reason code.
7. If the dispute is rejected, the original score is restored with a documented rationale and communicated to the supplier.
8. Supplier is notified of the outcome via portal notification and email.

**System Behavior**:
- Score record `status` field set to `DISPUTED` upon submission.
- Scores with `DISPUTED` status are excluded from risk tier recalculations, vendor ranking reports, and contract renewal triggers until resolved.
- A `ScoreDisputeWorkflow` entity is created, linking the score ID, submitting supplier ID, procurement manager ID, submitted evidence references, and resolution outcome.
- All state transitions (submitted → under_review → resolved/rejected) are written to the immutable audit log with actor, timestamp, and reason.
- Resolved disputes that resulted in score amendments are flagged with `AMENDED` status and retain a pointer to both the original and corrected score records.

---

## Force Majeure Events Affecting Delivery KPIs

**Scenario**: A natural disaster, pandemic, port strike, or other force majeure event causes widespread delivery delays for a supplier across a specific date range. The delays are documented as beyond the supplier's operational control.

**Impact**: If delivery KPIs during the affected period are included in the quarterly performance score without adjustment, the score is artificially depressed. Penalizing a supplier for events beyond their control damages the procurement relationship, may violate the force majeure clause in the supplier contract, and could result in unjustified tier downgrades or contract non-renewal.

**Detection**: Force majeure is flagged through one of three entry points: (1) the procurement manager manually activates a force majeure period in the admin console after reviewing a supplier-submitted notice; (2) the supplier submits a force majeure declaration through the portal, triggering a procurement review task; or (3) a risk intelligence feed integration (where configured) raises an event covering a geographic region and date range that matches the supplier's primary shipment origin.

**Handling Steps**:
1. Procurement manager reviews force majeure notice and validates that it covers a legitimate, documented event.
2. A `ForceEvent` record is created with: supplier ID, affected date range (start/end), event type classification, approving manager ID, and affected PO count.
3. The scoring engine re-evaluates which POs fall within the force majeure date range for the affected supplier.
4. Matching POs are excluded from the on-time delivery, lead time adherence, and fill rate calculations for the affected period.
5. The system calculates two parallel scores: the original score (all POs) and the adjusted score (force majeure POs excluded).
6. Both scores are retained in the system; the adjusted score is used for risk tier calculation and reporting.
7. Score record is annotated with a `FORCE_MAJEURE_ADJUSTED` flag and a reference to the `ForceEvent` record.

**System Behavior**:
- `ForceEvent` entity stored with full audit trail of creation and approval.
- Scoring engine's PO filter query includes a check: exclude orders where `delivery_window` overlaps with any approved `ForceEvent` for the same supplier.
- Reports display both original and adjusted scores side-by-side with a disclosure note explaining the exclusion.
- Excluded POs are listed in an audit appendix accessible to procurement managers and auditors.
- No automatic re-scoring occurs without explicit procurement manager approval of the force majeure event.

---

## Statistical Significance for New or Infrequent Suppliers

**Scenario**: A supplier has completed fewer than 5 purchase orders within a quarter, making the performance metrics statistically unreliable. A single late delivery in a 3-order quarter yields a 67% on-time rate, which is not meaningfully comparable to a 95% rate from a supplier with 200 orders.

**Impact**: Publishing statistically unreliable scores as if they were equivalent to high-volume supplier scores creates misleading comparisons in vendor rankings, may unfairly trigger tier downgrades, and could discourage new supplier onboarding if early scores carry disproportionate weight.

**Detection**: At scoring time, the scoring engine evaluates the completed order count for the supplier within the scoring period. If the count falls below the configured minimum threshold (default: 5 completed orders; configurable per commodity category in admin settings), the low-sample condition is triggered.

**Handling Steps**:
1. Scoring engine identifies supplier as below minimum sample threshold.
2. Score is calculated and stored but tagged with `status = INSUFFICIENT_DATA`.
3. System expands the rolling window to 12 months and recalculates score using all available historical data within that window.
4. If 12-month rolling data also falls below threshold, the score is presented as raw counts (e.g., "3 of 4 orders on-time") rather than as a percentage score.
5. Procurement team receives a notification listing all suppliers scored as `INSUFFICIENT_DATA` for the period, with recommendation to extend observation before risk tier assignment.
6. Score is withheld from vendor ranking reports that compare suppliers within the same commodity category.

**System Behavior**:
- `score.status = 'INSUFFICIENT_DATA'` prevents the score from being used as input to risk tier downgrade logic.
- Supplier profile displays a confidence indicator badge ("Limited Data — Score Based on N Orders") alongside the score.
- Procurement manager can manually override and accept the score for tier calculation with documented justification.
- Override action is logged in the audit trail with manager ID, timestamp, and stated rationale.
- Minimum threshold value is stored in `scoring_config` table, editable by system administrators with version history retained.

---

## Supplier Merger or Acquisition

**Scenario**: A supplier in the system is acquired by another company, or two existing supplier entities merge. Historical performance data, open purchase orders, and active contracts are split across two supplier records, creating ambiguity about which entity should be used going forward.

**Impact**: Procurement staff may inadvertently issue POs against the deprecated supplier entity. Historical performance data becomes fragmented, making trend analysis unreliable. Active contracts may reference entities that no longer have legal standing. Payment processing may be directed to incorrect bank accounts.

**Detection**: The procurement team is notified via supplier communication, legal notification, or news monitoring integration. A procurement manager manually initiates the merger workflow in the supplier management module after verifying the change with legal counsel.

**Handling Steps**:
1. Procurement manager initiates a Supplier Merger workflow from the admin console, designating a "surviving" supplier entity and one or more "merged" entities.
2. Legal team attaches documentation (acquisition agreement, new legal entity registration) to the workflow.
3. System audit identifies all open POs, active contracts, and pending invoices referencing merged entity IDs.
4. Procurement manager reviews and approves migration of open POs and active contracts to the surviving entity.
5. Merged supplier records are marked as `MERGED` with a `merged_into` pointer to the surviving supplier ID.
6. Historical performance data is retained under the original entity IDs; a combined performance view is generated by querying all linked entity IDs.
7. Supplier contacts are migrated or linked at the user account level; supplier portal access for merged accounts is revoked with notification.
8. Downstream systems (ERP, payment processor) are notified via `SupplierMerged` event with old-to-new ID mapping.

**System Behavior**:
- Merged supplier records set to `status = MERGED`; excluded from new PO supplier selection dropdowns.
- API lookups by merged supplier ID return a 301-equivalent response body pointing to surviving entity.
- All historical data (POs, invoices, scorecards, audit logs) remains queryable under original entity IDs for audit purposes.
- Combined performance dashboard available via `/suppliers/{survivingId}/performance?include_merged=true`.
- `SupplierMerged` domain event published to Kafka topic for consumption by downstream services.

---

## Multi-Country Supplier with Varying Regional Performance

**Scenario**: A global supplier operates fulfillment centers in multiple regions. Their North America operations achieve consistent 98% on-time delivery, while their Asia-Pacific operations average 74% on-time delivery. A single global aggregated score of 86% masks the significant regional disparity and misleads regional procurement teams.

**Impact**: Regional procurement managers in Asia-Pacific make decisions based on a global score that overstates local performance. Supply chain risk in the APAC region is underestimated. Conversely, the North American team may face pressure to switch suppliers based on a global score that understates their regional experience.

**Detection**: The system calculates variance across regional performance breakdowns as part of the scoring run. If the standard deviation of regional on-time delivery rates exceeds a configurable threshold (default: 15 percentage points), a regional variance alert is generated.

**Handling Steps**:
1. Scoring engine calculates performance metrics broken down by delivery region (derived from destination warehouse country code on the purchase order).
2. Both a global aggregate score and per-region scores are stored for each supplier per scoring period.
3. Variance threshold check runs after score calculation; if exceeded, a `RegionalVarianceAlert` is raised and assigned to the global category manager.
4. Regional procurement managers are granted access to their region's scorecard view as their primary dashboard.
5. Category manager reviews whether the supplier should be managed as a single entity or split into regional supplier entities for scoring purposes.
6. If split is approved, regional supplier entities are created as linked sub-entities of the parent supplier record.

**System Behavior**:
- Performance score model stores both `global_score` and a `regional_scores` JSON object keyed by region code.
- Supplier profile UI presents a regional breakdown chart alongside the global score.
- Risk tier calculation can be configured to use global score, regional score, or worst-region score, per commodity category policy.
- `RegionalVarianceAlert` event triggers a task in the category manager's workflow queue.
- Regional sub-entities share the parent supplier's master data (legal name, tax ID, bank details) but maintain independent performance histories.

---

## Performance Data Gaps Due to Integration Failures

**Scenario**: An ERP or warehouse management system integration failure causes goods receipt confirmation data to be missing for a defined period. The scoring engine cannot accurately calculate delivery performance because received-date records are absent for a subset of purchase orders.

**Impact**: Scores calculated over an incomplete dataset are artificially deflated (unconfirmed receipts counted as non-delivered) or cannot be computed at all. Either outcome results in unfair supplier evaluation and potential procurement decisions based on corrupted data.

**Detection**: A pre-scoring data completeness validation job runs 24 hours before each scheduled scoring run. It compares the expected order count (based on issued POs with expected delivery dates in the scoring window) against the actual confirmed goods receipt count. A gap ratio exceeding 5% triggers a data completeness warning; exceeding 15% triggers a scoring hold.

**Handling Steps**:
1. Pre-scoring validation job identifies the gap and logs details: affected date range, integration system source, estimated missing record count.
2. Alert dispatched to the data engineering team and procurement operations lead.
3. Scoring run status set to `PENDING_DATA`; scheduled scoring job paused.
4. Data engineering team investigates integration logs to determine if data can be recovered or is permanently lost.
5. If data is recoverable: integration replayed, records backfilled, scoring run rescheduled.
6. If data is confirmed lost: affected period marked with `DATA_GAP` status; scoring exclusion documented; impacted POs listed in a gap report.
7. Scoring run proceeds with documented exclusions; scores annotated with gap disclosure note.
8. Procurement managers notified of the gap, affected suppliers, and data quality caveat on resulting scores.

**System Behavior**:
- `scoring_run` record has `status` field with values: `SCHEDULED`, `PENDING_DATA`, `IN_PROGRESS`, `COMPLETED`, `COMPLETED_WITH_GAPS`, `FAILED`.
- Pre-scoring validation writes a `DataCompletenessReport` record for every scoring run, stored for audit purposes.
- Scores computed with `DATA_GAP` exclusions are annotated with the `INCOMPLETE_DATA` flag and are excluded from automated risk tier changes.
- Gap report is downloadable by procurement managers and data stewards from the admin console.
- Integration health dashboard shows real-time data completeness metrics per source system.

---

## Rapid Performance Degradation Detection

**Scenario**: A previously high-performing supplier (90+ score) experiences a sudden severe decline — multiple late deliveries within a single week — due to a production issue, logistics partner failure, or financial distress. The standard quarterly review cycle would not surface this risk for weeks or months.

**Impact**: Delayed detection of supply chain risk can result in stockouts, production line stoppages, or missed customer commitments. Early warning is critical to enable proactive mitigation: identifying alternative suppliers, adjusting safety stock, or engaging with the supplier directly.

**Detection**: A continuous monitoring job runs daily and calculates a rolling 30-day performance score for every active supplier. A degradation alert is triggered if: (a) the rolling 30-day score drops more than 20 points compared to the previous 30-day period, or (b) three or more consecutive late deliveries are recorded for the same supplier within any 14-day window.

**Handling Steps**:
1. Monitoring job publishes a `SupplierPerformanceDegradation` event to the alerting topic.
2. Notification dispatched to the category manager and procurement manager responsible for the supplier.
3. A performance review task is automatically created in the workflow module with HIGH priority and a 48-hour response SLA.
4. Procurement manager assesses current open POs and expected delivery dates at risk.
5. System generates a supply risk report showing: all open POs with the affected supplier, estimated impact on downstream demand, and recommended alternative suppliers from the approved vendor list.
6. Category manager determines whether to initiate a supplier performance improvement plan or activate contingency sourcing.
7. Supplier may receive an automated or manual communication requesting an explanation and corrective action plan.

**System Behavior**:
- `SupplierPerformanceDegradation` event includes: supplier ID, triggering metric, current rolling score, previous period score, delta, and the list of contributing late delivery events.
- Supplier dashboard displays a real-time warning banner visible to all users accessing the supplier's profile.
- Alert history is retained on the supplier record for trend analysis.
- Escalation rules are configurable: critical suppliers (tier 1) may trigger immediate escalation to CPO level.
- Monitoring job output is observable via the operations dashboard; job run history and alert counts are displayed per supplier.

---

## Score Recalculation After Data Correction

**Scenario**: A warehouse supervisor identifies that a goods receipt was recorded with incorrect quantities due to a data entry error (e.g., 500 units recorded as received when only 50 were delivered). The error is corrected in the warehouse management system, but performance scores calculated using the original data remain in place.

**Impact**: The original score may have unfairly rewarded or penalized the supplier based on incorrect fill rate data. Downstream decisions (risk tier assignments, contract renewals) made using the stale score are potentially invalid. Financial accruals based on the incorrect receipt quantity may also be affected.

**Detection**: A goods receipt amendment event is generated when a warehouse supervisor modifies a previously confirmed GR record. The amendment includes: original values, corrected values, reason code (e.g., `DATA_ENTRY_ERROR`, `COUNT_DISCREPANCY`), and approving supervisor ID. The amendment event triggers a recalculation flag on all performance scores that included the affected PO.

**Handling Steps**:
1. GR amendment recorded with full before/after audit trail, reason code, and supervisor authorization.
2. System identifies all performance score records that included the amended GR in their calculation window.
3. Affected score records are marked `STALE` with a reference to the triggering amendment event.
4. A score recalculation job is queued for each affected scoring period.
5. Recalculation job recomputes scores using corrected data; new score records created with `RECALCULATED` status.
6. If recalculated scores differ materially from original scores (configurable threshold, default ±5 points), a procurement manager review task is generated.
7. Supplier is notified via portal if their score changed as a result of the correction, with a summary of the change and reason.
8. Downstream consumers (risk tier engine, contract renewal module) are notified of score updates via `PerformanceScoreRevised` event.

**System Behavior**:
- Immutable audit log records every GR amendment with cryptographic hash for tamper detection.
- Score recalculation uses event sourcing: the scoring engine replays the corrected event stream to derive the updated score.
- Original score records are retained with `SUPERSEDED` status; recalculated scores reference the original via `supersedes_score_id`.
- Risk tier assignments that were based on a now-superseded score are flagged for review; they are not automatically changed without procurement manager confirmation.
- All notifications to suppliers regarding score corrections include the amendment reference ID and the name of the authorizing supervisor for traceability.
