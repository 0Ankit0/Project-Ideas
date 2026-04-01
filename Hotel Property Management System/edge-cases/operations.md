# Hotel Property Management System — Edge Cases: Operations

## Overview

Operational edge cases are infrastructure and process failures that affect the hotel's ability to run the PMS at all — not individual reservations or guests, but the system-wide processes that everything else depends on. Night audit, database availability, channel manager continuity, multi-property synchronisation, backup restoration, and service-level cascading failures are documented here. These are the edge cases that wake up engineers at 03:00 and that determine the hotel's Recovery Time Objective (RTO) and Recovery Point Objective (RPO) in practice. Each case includes a blast radius assessment, an immediate response runbook, escalation paths, and RTO/RPO targets.

---

## EC-OPS-001 — Night Audit Job Failure (Partial Execution)

*Category:* Operations
*Severity:* Critical
*Likelihood:* Low (but impact is extremely broad when it occurs)
*Affected Services:* NightAuditService, FolioService, ReservationService, ReportingService, TaxService, InvoicingService

**Description**
The night audit is the most critical scheduled job in hotel operations. It runs daily between 01:00 and 03:00 and performs: date advance (rolling the PMS system date forward), nightly room rate posting (posting each occupied room's rate to the corresponding folio), no-show processing, tax calculation and posting, loyalty points calculation, trial balance generation, and report distribution. A partial execution means some of these tasks completed and some did not. The failure mode is dangerous because partial state is worse than no state — some folios may have been charged and others not, creating a financial inconsistency that is difficult to detect and expensive to correct.

**Trigger Conditions**

1. The night audit job crashes midway through execution (OOM error, database connection drop, unhandled exception in a processing step).
2. The job completes but one or more steps report errors that are silently swallowed (no exception propagation, no alerting).
3. The database is under heavy load from an unexpected concurrent process, causing the night audit to time out.
4. The job is manually cancelled by a staff member who did not understand its significance.

**Expected System Behaviour**

1. NightAuditService is designed as a saga with explicit checkpoints: each step (date advance, rate posting, no-show processing, tax posting, reporting) writes a checkpoint record before and after execution.
2. Checkpoints: `{job_id, step_name, status: 'STARTED'|'COMPLETED'|'FAILED', started_at, completed_at, records_processed, records_failed}`.
3. If the job crashes mid-execution, the checkpoint table shows which steps completed and which did not.
4. On the next execution (automatic retry at T+30 minutes or manual re-run), the job reads the checkpoint table and skips already-completed steps.
5. Idempotency: each step must be idempotent — running a completed step again produces no additional effect (rate posting checks for existing posts before creating new ones; no-show processing checks for existing no-show charges).
6. Alert `NightAuditFailure` fires within 5 minutes of a step failure. Severity: Critical. On-call engineer + Night Audit Manager are paged.

**Blast Radius**
A complete night audit failure affects:
- **Revenue:** Room rates are not posted to folios. Guests who check out the next morning may be undercharged.
- **Date Advance:** The PMS date does not advance. All transactions on the failed date appear under the prior date in reports.
- **No-Show Processing:** No-show charges are not applied, resulting in revenue loss.
- **Tax Posting:** Tax liabilities are not recorded for the night.
- **Reports:** Management reports for the night are not generated. Department heads start their shift without revenue data.
- **Loyalty Points:** Loyalty points for the night's stays are not calculated.

**Immediate Response Runbook**

1. **T+0:** `NightAuditFailure` alert fires. On-call engineer checks the checkpoint table.
2. **T+5 min:** Identify the failed step(s). Check the error log for the cause.
3. **T+10 min:** Assess whether the failure is safe to retry (idempotent) or requires manual correction first.
4. **T+15 min:** If safe: trigger a manual re-run of the failed step(s) via the admin API: `POST /night-audit/retry {job_id, from_step: "RATE_POSTING"}`.
5. **T+30 min:** Verify completion: all checkpoint records show `COMPLETED`. No records remain in `STARTED` or `FAILED` state.
6. **T+60 min:** Review the generated reports. Cross-check total charges posted against the occupancy report × average rate. Variance > 1% triggers a manual folio audit.

**Escalation Path**
- T+0 to T+30: On-call engineer + Night Audit Manager.
- T+30 to T+60: Head of Finance is notified if rate posting or tax posting failed.
- T+60+: General Manager is informed before the morning handover.

**RTO/RPO Targets**
- *RTO:* Night audit must complete by 06:00 (before the morning shift starts and the first checkouts occur). If the audit is not complete by 05:30, the morning shift supervisor is briefed on the incomplete state.
- *RPO:* The checkpoint table provides a recovery point for each step. In the worst case, only the failed step must be re-run; no data from completed steps is lost.

**Post-Incident Review**
1. Root cause analysis within 24 hours.
2. Review: was the failure caught by monitoring before or after the morning shift started?
3. Was the retry successful without data corruption?
4. Update the audit job's error handling to prevent silent failures.
5. Add or improve alerting for the specific failure mode identified.

**Test Cases**
- *TC-1:* Simulate a crash midway through the RATE_POSTING step. Assert that re-running the job resumes from RATE_POSTING and does not double-post rates for rooms that were already processed.
- *TC-2:* Simulate the entire night audit completing successfully. Assert all checkpoints show COMPLETED and a trial balance is generated.
- *TC-3:* Night audit runs on the wrong PMS date due to a date advance failure. Assert the system detects the date mismatch and alerts before any charges are posted.

---

## EC-OPS-002 — Database Failover During Check-In Peak (8–9 AM)

*Category:* Operations
*Severity:* Critical
*Likelihood:* Low
*Affected Services:* DatabaseCluster, ReservationService, FolioService, CheckInService, All services with database dependency

**Description**
The hotel PMS database primary node fails during the morning check-in peak (08:00–09:00). The database cluster must perform an automatic failover to a replica. During the failover window — typically 15–60 seconds — all database writes fail. Check-ins are interrupted, folio transactions may fail, and any operation that requires a database write is blocked. If services do not handle the brief unavailability gracefully, cascading errors can extend the impact far beyond the failover window.

**Trigger Conditions**

1. Primary database node experiences a hardware failure, kernel panic, network partition, or OOM kill.
2. The database cluster's automatic failover mechanism promotes a replica to primary.
3. The failover window is 15–60 seconds (depending on the cluster technology: PostgreSQL Patroni, MySQL Group Replication, etc.).
4. Services with open database connections receive connection errors during the failover.

**Expected System Behaviour**

1. **Connection Pool Behaviour:** The connection pool (PgBouncer, HikariCP) detects failed connections and enters reconnect mode. New queries are held in a brief retry queue (up to 5 seconds) rather than immediately failing.
2. **Retry Logic:** Each service uses a retry policy for database connection failures: 3 retries with 1-second intervals. Total wait: up to 5 seconds before a request fails.
3. **Read Replica Routing:** Read operations (availability queries, folio display) are routed to read replicas and are not affected by the primary node failure.
4. **Write Buffering:** For non-critical writes (loyalty points, analytics events), a write buffer queue absorbs requests during the failover window. These are processed once the new primary is available.
5. **Critical Write Path:** Check-in, folio posting, and payment transactions are not buffered. They are retried up to 3 times. If they fail, the user receives an error and is asked to retry.
6. **Health Check:** Services run a database health check every 5 seconds. When the new primary is available, the health check passes, the connection pool is refreshed, and normal operation resumes.
7. **Alert:** `DatabasePrimaryFailover` fires within 30 seconds of the primary going down. Severity: Critical. On-call DBA and engineer are paged.

**Guest Impact**
- During the 15–60 second failover window: check-in transactions may fail and need to be retried.
- Front desk agent sees a brief "system unavailable" error on their workstation.
- Express checkout via app may show a "please try again" message.
- No data loss occurs because write buffering and retry logic ensure all transactions eventually complete.

**Immediate Response Runbook**

1. **T+0:** `DatabasePrimaryFailover` alert fires. On-call DBA confirms the failover is in progress.
2. **T+30 sec:** New primary is elected. Connection pools reconnect. Services resume normal operation.
3. **T+2 min:** DBA verifies replication lag on the new replica(s): `SELECT * FROM pg_stat_replication`.
4. **T+5 min:** DBA reviews for any transactions that failed during the failover window: check service error logs for `DatabaseConnectionException` during the T+0 to T+60 window.
5. **T+10 min:** Front Desk Supervisor is informed: "Brief system interruption at {time}. All operations resumed. Re-process any transactions that showed an error during {time window}."
6. **T+30 min:** Investigate the root cause of the primary failure.

**Escalation Path**
- T+0 to T+5 min: On-call engineer + DBA.
- T+5 min to T+30 min: Engineering Manager is notified.
- T+30 min+: CTO is informed if the root cause is a hardware failure or if the failover took longer than 60 seconds.

**RTO/RPO Targets**
- *RTO:* Database available within 60 seconds of primary failure (automatic failover target).
- *RPO:* Replication lag at the time of failover determines RPO. Target: < 5 seconds of lag (meaning < 5 seconds of potentially lost writes). In practice, synchronous replication with 1 replica provides RPO ≈ 0.

**Post-Incident Review**
1. Determine why the primary failed.
2. Review the maximum replication lag in the 30 minutes before the failure.
3. Assess whether any guest-visible transactions were lost.
4. Test failover procedure quarterly in a staging environment.

**Test Cases**
- *TC-1:* Kill the primary database during a check-in operation. Assert the check-in retries and completes within 10 seconds after the failover.
- *TC-2:* Simulate a 60-second failover. Assert all read operations continue via replica during this window.
- *TC-3:* A folio posting fails during the failover window. Assert it is retried and no duplicate charge is posted when the database recovers.

---

## EC-OPS-003 — Channel Manager Complete Outage (12+ Hours)

*Category:* Operations
*Severity:* Critical
*Likelihood:* Low
*Affected Services:* ChannelManager, AllOTAAdapters, ReservationService, RevenueManagementService, InventoryService

**Description**
The channel manager — the subsystem responsible for distributing inventory and rates across all OTA channels — experiences a complete outage lasting 12 or more hours. This is distinct from a brief API hiccup (see EC-API-006): a 12-hour outage is a major operational event that affects the hotel's revenue management, inventory control, and booking intake. Manual fallback procedures must be activated and sustained for an extended period. This case documents the extended-duration runbook including escalation, financial impact assessment, and the recovery verification procedure.

**Trigger Conditions**

1. Channel manager service is completely unreachable for > 1 hour.
2. All attempts to restart the service or restore connectivity have failed.
3. The outage is expected to continue for an unknown duration (infrastructure failure, vendor platform incident, etc.).

**Expected System Behaviour — Extended Outage Protocol**

**Phase 1: Detection and Immediate Response (0–30 minutes)**
1. `ChannelManagerOutage` alert fires. Engineering team confirms the outage is not transient.
2. All OTA adapters switch to "passive mode" — accept inbound webhooks but do not attempt outbound updates.
3. The offline queue is actively accumulating inventory update events.
4. Revenue Manager is notified: manual OTA management must begin immediately.

**Phase 2: Manual Channel Management (30 minutes – 12 hours)**
5. Revenue Manager logs into each OTA extranet portal manually (credentials held in secure vault).
6. For each OTA: review the current availability shown vs. the actual PMS inventory.
7. If the PMS is at > 85% occupancy: close availability on all OTAs to prevent overbooking.
8. If the PMS has significant availability: manually match the OTA availability to the PMS count (time-consuming but necessary to avoid lost revenue).
9. Manual rate updates: if rates were scheduled to change during the outage, the Revenue Manager applies them manually in each OTA portal.
10. Every manual action is logged in the incident record with timestamp and OTA.

**Phase 3: Extended Outage Assessment (> 4 hours)**
11. General Manager and Revenue Management Director are informed.
12. Financial impact assessment: estimate revenue lost due to incorrect availability displayed on OTAs.
13. If the channel manager vendor is external (SaaS product): contact vendor support for ETA on resolution.
14. If the channel manager is internal: escalate to CTO. Evaluate failover to a secondary channel manager.

**Phase 4: Recovery (Outage resolved)**
15. Channel manager service is restored.
16. Before enabling automated sync: Revenue Manager reviews the offline queue contents — rate changes and availability updates that accumulated during the outage.
17. Stale or commercially incorrect rate changes are removed from the queue before replay.
18. The offline queue is replayed gradually (rate-limited to avoid OTA API rate limits).
19. Post-recovery audit: verify that all OTAs show the correct availability and rates. Confirm no double bookings occurred during the outage.

**Blast Radius**
- **Revenue:** OTAs showing stale (too high) availability may result in overbooking. OTAs showing stale (too low) availability result in lost bookings.
- **Rate Parity:** Manual updates across multiple OTAs may introduce rate disparities. OTAs may penalise the hotel for rate parity violations.
- **Staff Load:** Revenue Manager's entire day is consumed by manual channel management.
- **Booking Accuracy:** Bookings received during the outage may need manual inventory reconciliation.

**RTO/RPO Targets**
- *RTO:* Channel manager restored within 4 hours for internal infrastructure failures.
- *RPO:* All inventory events are persisted in the offline queue. No events are lost. The RPO for inventory state is the sync lag at the time of the last successful update before the outage.

**Post-Incident Review**
1. Root cause analysis within 48 hours.
2. Quantify revenue impact: bookings lost due to stale zero-availability display; overbooking risk from stale positive-availability display.
3. Review whether the manual fallback procedure was executed correctly and efficiently.
4. Assess whether a secondary/failover channel manager should be provisioned.

**Test Cases**
- *TC-1:* Channel manager outage for 2 hours with hotel at 90% occupancy. Assert offline queue accumulates updates and manual stop-sell alert fires within 30 minutes.
- *TC-2:* Recovery after 4-hour outage. Assert the offline queue replay does not apply stale rate changes automatically — Revenue Manager approval is required.
- *TC-3:* A booking is received via OTA during the outage on a date that is fully occupied in the PMS. Assert the double-booking detection runs during post-recovery audit.

---

## EC-OPS-004 — Multi-Property Configuration Sync Failure

*Category:* Operations
*Severity:* High
*Likelihood:* Low
*Affected Services:* MultiPropertyService, ConfigurationService, ReservationService, RatePlanService, TaxService

**Description**
A hotel group manages multiple properties from a single HPMS instance. Configuration data — tax rates, rate plans, room categories, housekeeping workflows, loyalty tier definitions — can be managed at the group level and pushed to individual properties, or managed independently per property. A multi-property sync failure occurs when a configuration change at the group level is not correctly applied to one or more properties. The result is inconsistent behaviour across properties: one property uses the correct new tax rate, another uses the old rate; one property offers the new promotional rate, another does not.

**Trigger Conditions**

1. A group-level configuration change is initiated: `POST /group-config/{group_id}/sync {config_type: "TAX_RATES", effective_date: "..."}`.
2. The sync job pushes the change to all properties but fails silently for one or more properties (database write failure, network partition, or schema mismatch between property database versions).
3. No alerting exists for partial sync failures — the job reports success because the majority of properties were updated.

**Expected System Behaviour**

1. Multi-property sync is implemented as a scatter/gather operation:
   - The group-level change is broadcast to all properties.
   - Each property acknowledges the receipt and application of the change.
   - The scatter/gather coordinator waits for all acknowledgements within a 60-second window.
2. Properties that do not acknowledge within 60 seconds are flagged as `SYNC_PENDING`.
3. `MultiPropertySyncFailure` alert fires if any property remains in `SYNC_PENDING` after 2 retries.
4. The alert includes: `{group_id, config_type, failed_properties: ["Property-A", "Property-B"]}`.
5. The Revenue Management team is notified before any config change takes effect: if not all properties are in sync, the effective date of the change can be postponed.

**Inconsistent State Risks**
- Tax rate mismatch: one property charges 10% tourism tax, another charges 12%. Creates audit discrepancies and guest complaints about inconsistent pricing.
- Rate plan mismatch: a promotional rate is bookable at some properties but not others. Creates guest confusion and potential complaints if the advertised rate is unavailable.
- Loyalty tier mismatch: tier benefits differ across properties within the same brand. Creates high-value guest dissatisfaction.

**Immediate Response Runbook**
1. Identify which properties have the sync failure.
2. Review the error log for each failed property: schema version mismatch? Database down? Network partition?
3. Resolve the underlying issue for each failed property.
4. Trigger a manual sync for the failed properties: `POST /group-config/{group_id}/sync/retry {property_ids: [...], config_type: "..."}`.
5. Verify that all properties now show the same configuration: `GET /group-config/{group_id}/config-audit` — all properties should show the same version hash.

**RTO/RPO Targets**
- *RTO:* All properties in sync within 30 minutes of a configuration change being applied to the first property.
- *RPO:* Configuration changes are idempotent. Re-applying a change that already succeeded is safe.

**Post-Incident Review**
1. Root cause: which property failed and why?
2. Was the inconsistent configuration visible to guests?
3. Was any revenue impact caused by the inconsistency?
4. Update the sync job to report partial failures more aggressively.

**Test Cases**
- *TC-1:* Tax rate change pushed to 5 properties; 1 property's database is temporarily unavailable. Assert SYNC_PENDING alert fires for that property and the other 4 have the new rate.
- *TC-2:* Failed property comes back online. Assert the sync retry is automatically triggered and the property is updated.
- *TC-3:* Schema version mismatch prevents sync. Assert the alert includes the schema version information to assist debugging.

---

## EC-OPS-005 — Backup Restoration Failure During Disaster Recovery

*Category:* Operations
*Severity:* Critical
*Likelihood:* Rare
*Affected Services:* BackupService, DatabaseCluster, All HPMS Services, DisasterRecoveryService

**Description**
A catastrophic failure — datacenter fire, ransomware attack, complete infrastructure loss — requires the hotel PMS to be restored from backup. The disaster recovery team begins the restoration process and discovers that the most recent backup is corrupted, the restoration process is taking longer than expected, or the restored data is inconsistent. This is the edge case that tests whether the hotel's disaster recovery plan is real or aspirational. The documentation here is the difference between a 2-hour outage and a 2-week outage.

**Trigger Conditions**

1. A disaster event requires full PMS restoration from backup.
2. During restoration, one or more of the following is discovered:
   a. The backup file is corrupted (hash mismatch on verification).
   b. The backup is from a point further in the past than expected (backup job had been silently failing for days).
   c. The restoration process fails partway through (disk space exhaustion, schema migration error).
   d. The restored database is inconsistent (referential integrity violations, missing records).

**Expected System Behaviour — Backup Integrity**

1. All backups are automatically verified immediately after creation:
   - Checksum verification: `SHA256(backup_file)` matches the stored hash.
   - Restoration test: once weekly, a backup is restored to a test environment and a set of data integrity checks are run.
   - Retention check: at least 7 daily backups + 4 weekly backups + 12 monthly backups are retained and verified.
2. The backup job publishes a health metric `backup.last_successful_backup_age_hours` — alert fires if this exceeds 26 hours (allowing a 2-hour window around the nightly backup job).

**Expected System Behaviour — Restoration Process**

1. **Point-in-Time Recovery:** If the most recent backup is < 24 hours old, apply the Write-Ahead Log (WAL) archive to restore to the exact point before the disaster. RPO ≈ seconds.
2. **Restoration Steps:**
   a. Provision a new database instance.
   b. Restore from the most recent verified backup.
   c. Apply WAL archive up to the point of disaster.
   d. Run integrity checks: foreign key validation, balance reconciliation, reservation state consistency.
   e. Restore application services against the recovered database.
   f. Run smoke tests: attempt a check-in, a folio query, a reservation search.
   g. Bring the system online for read-only access first, then write access after the integrity checks pass.

**Failure Mode — Corrupted Backup**
If the latest backup is corrupted:
1. Fall back to the previous day's backup.
2. Accept data loss from the period between the previous backup and the disaster (RPO degraded from seconds to up to 24 hours).
3. Manually reconstruct transactions from the past 24 hours using: paper records, OTA booking webhooks (re-delivered by OTAs on request), POS receipt archives, and manual guest records.

**Escalation Path**
- T+0: DR incident declared. On-call engineer + DBA begin restoration.
- T+30 min: If restoration is not on track, Engineering Manager and CTO are involved.
- T+1 hour: General Manager and hotel ownership are informed. Communications plan for guests with upcoming arrivals is activated.
- T+4 hour+: If system is not restored, activate the business continuity plan (manual paper-based operations).

**RTO/RPO Targets**
- *RTO Target:* Full PMS available within 4 hours of declaring a DR event.
- *RPO Target:* Maximum 30 minutes of data loss (achieved via WAL streaming replication).
- *Degraded RPO:* If the latest backup is corrupted: up to 24 hours of data loss. This is the documented worst-case scenario.

**Business Continuity Plan (Manual Operations)**
If the PMS cannot be restored within 4 hours:
1. Front desk switches to manual paper check-in forms.
2. All reservation confirmations are verified via OTA extranet portals.
3. Revenue is tracked on paper folios and reconciled when the PMS is restored.
4. Housekeeping operates from a printed room assignment list.
5. All manual records are entered into the PMS after restoration.

**Post-Incident Review**
1. Full post-mortem within 72 hours.
2. Root cause: why did the disaster occur? Why did the backup fail (if applicable)?
3. Was the RPO and RTO actually met?
4. What manual processes had to be activated? How can they be reduced?
5. DR drill update: schedule a drill within 30 days to test the corrected procedure.

**Test Cases**
- *TC-1:* A backup is created and immediately corrupted. Assert the backup health check detects the corruption and alerts within 30 minutes.
- *TC-2:* Full DR restoration from a 48-hour-old backup (WAL archive available). Assert the restoration completes within 4 hours and the data is current to within 5 minutes of the disaster.
- *TC-3:* Integrity check after restoration finds a referential integrity violation. Assert the smoke tests detect the issue and the system does not go online until the violation is resolved.

---

## EC-OPS-006 — Cascading Failure: FolioService Overload Causes ReservationService Degradation

*Category:* Operations
*Severity:* Critical
*Likelihood:* Low
*Affected Services:* FolioService, ReservationService, PaymentService, APIGateway, All dependent services

**Description**
A traffic spike — driven by a major event checkout, a promotional campaign response, or a batch import job running unexpectedly during peak hours — causes FolioService to become overloaded. FolioService starts responding slowly. Services that call FolioService begin to queue their requests. Their thread pools fill up. Services that depend on those services also start queuing. Within minutes, a FolioService performance degradation has cascaded into a system-wide slowdown — even for services that do not directly use FolioService. This is the cascade failure antipattern, and it is the most difficult operational failure mode to diagnose and contain.

**Trigger Conditions**

1. FolioService processes a spike in concurrent requests (e.g., 500 simultaneous folio finalisation requests at 11:00 checkout time).
2. FolioService response time increases from < 200 ms to > 5 seconds.
3. Services calling FolioService (CheckoutService, ReservationService, NightAuditService) have synchronous, blocking calls with no timeout configured.
4. The blocking calls fill the caller services' thread pools.
5. API Gateway requests to the affected services begin timing out.
6. A monitoring alert fires, but the initial alert appears to be about ReservationService — masking the true root cause (FolioService).

**Expected System Behaviour**

1. **Timeouts:** Every service-to-service HTTP call has a configured timeout (default: 3 seconds for FolioService calls). After 3 seconds without a response, the calling service returns an error to its caller — it does not wait indefinitely.
2. **Circuit Breakers:** CheckoutService has a circuit breaker on the FolioService dependency. After 50% error rate over 10 seconds, the circuit breaker opens: CheckoutService fails fast for folio operations (returns HTTP 503 immediately) rather than waiting for timeouts.
3. **Bulkheads:** The CheckoutService thread pool for FolioService calls is isolated from its thread pool for other operations. Even if all FolioService threads are exhausted, the CheckoutService can still handle non-folio operations.
4. **Load Shedding:** FolioService's request queue has a maximum depth. When the queue is full, new requests are rejected with HTTP 429 (Too Many Requests) rather than being queued indefinitely.
5. **Auto-Scaling:** FolioService is configured for horizontal auto-scaling. When CPU > 80% for 2 consecutive minutes, a new replica is provisioned. The provisioning time is < 90 seconds.

**Cascade Prevention Mechanisms**
- Timeout at every service boundary (synchronous calls).
- Circuit breaker on every downstream dependency.
- Bulkhead pattern: separate thread pools for each downstream dependency.
- Load shedding on overloaded services.
- Backpressure propagation: if FolioService is overloaded, it signals callers to slow down rather than silently queuing.

**Immediate Response Runbook**

1. **T+0:** Monitoring detects elevated API Gateway error rate and p99 latency spike.
2. **T+2 min:** SRE reviews the service dependency graph. Identifies FolioService as the common upstream of all degraded services.
3. **T+3 min:** SRE checks FolioService metrics: CPU at 100%, request queue depth at maximum, p99 latency = 15 seconds.
4. **T+5 min:** Trigger FolioService emergency scaling: `kubectl scale deployment folio-service --replicas=10`.
5. **T+7 min:** Load begins distributing across new replicas. FolioService latency begins to drop.
6. **T+10 min:** FolioService p99 latency returns to < 500 ms. Circuit breakers begin transitioning to HALF_OPEN.
7. **T+12 min:** Circuit breakers close. Dependent services resume normal operation.
8. **T+15 min:** SRE verifies all services are green. Checks for any failed transactions during the degradation window.

**Blast Radius**
Without cascade prevention: a FolioService slowdown can bring down the entire PMS within 5 minutes.
With cascade prevention: impact is contained to folio operations. Check-ins (which don't require folio access at the moment of check-in) continue normally. Checkouts are degraded for the duration of the FolioService recovery.

**RTO/RPO Targets**
- *RTO:* Full recovery within 15 minutes of detecting the cascade.
- *RPO:* No data loss — queued requests eventually succeed. No transactions are lost; they are either retried or fail fast and the guest is asked to retry.

**Post-Incident Review**
1. Root cause: what triggered the FolioService traffic spike?
2. Were circuit breakers and timeouts functioning as designed?
3. Was the cascade contained or did it propagate further than expected?
4. Review auto-scaling thresholds: should scaling have started earlier?
5. Document the cascade pattern in the runbook for future reference.

**Test Cases**
- *TC-1 (Chaos Engineering):* Artificially slow FolioService to 5-second response times. Assert that CheckoutService's circuit breaker opens within 30 seconds and ReservationService remains unaffected.
- *TC-2:* Send 1000 concurrent requests to FolioService (10× normal load). Assert auto-scaling provisions additional replicas and p99 latency stays below 2 seconds.
- *TC-3:* Circuit breaker opens. Assert that CallerService returns HTTP 503 immediately rather than timing out after 3 seconds. Measure the fail-fast response time: should be < 50 ms.

---

## Edge Case Summary Matrix

| ID | Title | Severity | Likelihood | Priority | Detection Method | RTO Target | RPO Target |
|----|-------|----------|------------|----------|-----------------|------------|------------|
| EC-OPS-001 | Night Audit Partial Failure | Critical | Low | P1 | Checkpoint table + dead man's switch alert by 03:00 | Complete by 06:00 | Per-step checkpoint |
| EC-OPS-002 | Database Failover During Peak | Critical | Low | P1 | Primary failure detection < 30 sec | 60 seconds | < 5 seconds |
| EC-OPS-003 | Channel Manager 12h+ Outage | Critical | Low | P1 | ChannelManagerOutage alert + outage duration tracking | 4 hours (internal infra) | Offline queue replay |
| EC-OPS-004 | Multi-Property Config Sync Failure | High | Low | P2 | Scatter/gather acknowledgement tracking | 30 minutes | Idempotent (zero loss) |
| EC-OPS-005 | Backup Restoration Failure | Critical | Rare | P1 | Weekly restoration test + backup age alert | 4 hours | 30 min (WAL); 24h (degraded) |
| EC-OPS-006 | Cascading FolioService Failure | Critical | Low | P1 | Service dependency graph + p99 spike alert | 15 minutes | No data loss |
