# Operations Edge Cases

## Failure Mode

Four distinct operational failure scenarios are addressed:

**(a) Carrier API outage**: the external carrier integration endpoint becomes unavailable, blocking all shipment confirmation calls. Labels cannot be generated, and shipment status cannot be updated.

**(b) Kafka / Event bus lag**: the message broker consumer group falls behind, causing downstream services (OMS, replenishment, reporting) to process stale events. Order status updates and inventory signals are delayed.

**(c) Database replication lag**: the read replica falls behind the primary, causing read-heavy services (ATP queries, wave planning) to serve stale inventory data. Over-allocation or under-allocation decisions are made on incorrect data.

**(d) Wave planner worker crash mid-execution**: the wave planning process crashes after emitting some pick tasks but before completing the full wave. Partial reservations are committed; the remaining wave lines are orphaned; the crashed worker holds no locks and leaves no cleanup.

---

## Impact

| Scenario | Business Impact | SLA Risk |
|---|---|---|
| Carrier API outage | Shipments queued; carrier cut-off may be missed | High — SLA breach if outage > 30 min before cut-off |
| Event bus lag > 30 s | Order status stale; replenishment signals delayed | Medium — degraded visibility; SLA breach if lag > 5 min |
| DB replica lag > 5 s | ATP reads return incorrect values; wave planning over-allocates | High — potential double-booking of stock |
| Wave planner crash | Orphaned reservations block stock; remaining lines not picked | High — order fulfillment partially blocked |

---

## Detection

- **Carrier API**: HTTP error rate > 10% on carrier integration endpoints → alert `CarrierAPIErrorHigh` (Sev-1 if cut-off < 1 h away, else Sev-2).
- **Event bus**: consumer group lag > 30 s → alert `EventBusLagHigh` (Sev-2); lag > 5 min → escalate to Sev-1.
- **DB replica**: replica lag > 5 s → alert `DBReplicaLagHigh` (Sev-2); primary unreachable → Sev-1.
- **Wave planner**: orphaned reservation count (reservations with no active wave or worker assignment) > 0 for > 5 minutes → alert `OrphanedReservationsDetected` (Sev-2).
- **Wave planner**: wave status stuck in `PLANNING` for > 10 minutes → alert `WavePlannerStuck`.

---

## Mitigation

**Scenario (a) — Carrier API outage:**
1. **On-call Engineer**: confirm carrier API health via status page and direct health-check probe.
2. **On-call Engineer**: switch the carrier integration to circuit-open mode: `POST /carriers/{carrierId}/circuit-open`.
3. **Operations Lead**: queue all pending shipments in the `carrier_retry_queue` with a 5-minute retry interval.
4. **Operations Lead**: if outage persists > 30 minutes, evaluate rerouting to an alternate carrier for SLA-critical shipments.

**Scenario (b) — Event bus lag:**
5. **On-call Engineer**: check consumer group health; identify slow consumers or partition imbalance.
6. **On-call Engineer**: scale up consumer replicas: `kubectl scale deployment event-consumer --replicas=N`.
7. **Operations Lead**: throttle wave release to reduce inbound event volume until lag normalises.

**Scenario (c) — DB replica lag:**
8. **On-call Engineer**: switch ATP-read services to read from the primary temporarily: `POST /config/db-read-source { "source": "primary" }`.
9. **On-call Engineer**: investigate replica lag cause (network I/O, long-running transaction on primary).
10. **DBA**: if replica is irrecoverably behind, promote a fresh replica from the latest primary snapshot.

**Scenario (d) — Wave planner crash:**
11. **On-call Engineer**: identify the crashed wave via `SELECT * FROM waves WHERE status = 'PLANNING' AND updated_at < NOW() - INTERVAL '10 minutes'`.
12. **On-call Engineer**: run the orphaned-reservation cleanup job: `POST /jobs/orphan-reservation-cleanup { "wave_id": "..." }`.
13. **On-call Engineer**: resume or re-trigger wave planning from the last committed checkpoint.

---

## Recovery

**Carrier outage:**
1. Monitor carrier API health endpoint until error rate drops < 5%.
2. Drain the `carrier_retry_queue` in FIFO order; confirm each shipment receives a carrier tracking number.
3. **Checkpoint**: zero shipments remain in `LABEL_PENDING` status for > 5 minutes.
4. Close circuit: `POST /carriers/{carrierId}/circuit-close`; resume normal shipment flow.

**Event bus lag:**
1. Monitor consumer lag metric until it returns to < 10 s.
2. **Checkpoint**: confirm all downstream services (OMS, replenishment) have processed events up to the current offset.
3. Resume normal wave release rate.

**DB replica lag:**
1. Monitor `replica_lag_seconds` metric until it drops to < 1 s.
2. Switch ATP-read services back to replica: `POST /config/db-read-source { "source": "replica" }`.
3. **Checkpoint**: run the ATP invariant check against both primary and replica; confirm no discrepancy.

**Wave planner crash:**
1. After orphan cleanup, run ATP invariant check to confirm no negative ATP from leaked reservations.
2. **Checkpoint**: `SELECT COUNT(*) FROM reservations WHERE status = 'ORPHANED'` → must return 0.
3. Re-plan the wave from the last committed checkpoint or from scratch if checkpoint is unavailable.
4. Confirm the new wave emits tasks for all previously un-tasked order lines.

---

## Incident Playbook Summary

| Scenario | Detect | Contain | Recover | Verify |
|---|---|---|---|---|
| Carrier outage | Error rate > 10% | Circuit-open; queue shipments | Drain retry queue on recovery | Zero `LABEL_PENDING` > 5 min |
| Event bus lag | Consumer lag > 30 s | Scale consumers; throttle wave | Drain to current offset | Lag < 10 s; downstream services current |
| DB replica lag | Replica lag > 5 s | Read from primary | Replica catches up | ATP parity primary vs. replica |
| Wave planner crash | `PLANNING` status > 10 min | Orphan cleanup job | Re-plan wave from checkpoint | Zero orphaned reservations; wave complete |

---

## Operational Runbook: Wave Planner Crash

1. Identify crashed wave: `SELECT wave_id, status, created_at, updated_at FROM waves WHERE status = 'PLANNING' AND updated_at < NOW() - INTERVAL '10 minutes'`.
2. List orphaned reservations: `SELECT * FROM reservations WHERE wave_id = ? AND status = 'ACTIVE' AND worker_id IS NULL`.
3. Cancel orphaned reservations: `UPDATE reservations SET status = 'CANCELLED', cancelled_reason = 'ORPHAN_CLEANUP' WHERE wave_id = ? AND worker_id IS NULL`.
4. Release ATP for cancelled reservations: run `POST /inventory/recompute-atp { "wave_id": "..." }`.
5. Mark the crashed wave as `FAILED`: `UPDATE waves SET status = 'FAILED', failure_reason = 'WORKER_CRASH' WHERE wave_id = ?`.
6. Re-trigger wave planning: `POST /waves { "order_ids": [...], "zone_ids": [...], "priority": "HIGH" }`.
7. Monitor the new wave until all tasks reach `ASSIGNED` status.
8. Confirm no orders were permanently dropped from the wave by comparing original order line count to new wave task count.

---

## Carrier Outage Failover Procedure

1. Confirm carrier outage is external (status page) vs. internal (WMS integration bug).
2. If external: open circuit immediately; queue all `LABEL_PENDING` shipments.
3. Identify SLA-critical shipments (carrier cut-off within 2 hours): `SELECT * FROM shipments WHERE status = 'LABEL_PENDING' AND promised_ship_date <= NOW() + INTERVAL '2 hours'`.
4. For SLA-critical shipments: evaluate alternate carrier availability via `GET /carriers?route={origin}&destination={dest}&sla=SAME_DAY`.
5. If alternate carrier available: reroute SLA-critical shipments; regenerate labels.
6. Notify operations team of all rerouted shipments for physical re-sort if carrier changes require different dock doors.
7. On carrier recovery: drain the retry queue; confirm all queued shipments receive original carrier labels.

---

## Event Bus Lag Recovery Procedure

1. Identify the lagging consumer group: `kafka-consumer-groups.sh --describe --group wms-events`.
2. Check for partition skew: one partition receiving disproportionate volume → trigger rebalance.
3. Scale consumer replicas to match partition count (1:1 ratio recommended).
4. If lag is caused by a slow downstream service (e.g., OMS), apply back-pressure: pause wave release until downstream catches up.
5. Monitor `consumer_group_lag_seconds` every 30 s; confirm downward trend.
6. When lag < 10 s: resume normal operations; confirm all downstream service offset commits are current.

---

## On-Call Escalation Checklist

- [ ] Incident severity assessed (Sev-1/2/3/4).
- [ ] Incident commander assigned within 5 minutes (Sev-1/2).
- [ ] Containment steps started within 15 minutes.
- [ ] Status update posted to `#ops-incidents` every 15 minutes (Sev-1) or 30 minutes (Sev-2).
- [ ] Downstream teams notified (OMS, carrier partners, customer support) if customer-visible impact.
- [ ] Recovery verification checkpoints completed before declaring resolution.
- [ ] Post-incident review scheduled within 2 business days (Sev-1) or 5 business days (Sev-2).

---

## Post-Incident Review Template

```
## Incident Summary
- Incident ID:
- Severity:
- Duration (detected → resolved):
- Services affected:

## Timeline
- [timestamp] First detection signal
- [timestamp] On-call acknowledged
- [timestamp] Containment applied
- [timestamp] Recovery started
- [timestamp] Incident resolved

## Root Cause
(Describe the technical root cause)

## Impact Summary
- Orders affected:
- SLA breaches:
- Financial impact:

## What Went Well

## What Could Be Improved

## Corrective Actions
| Action | Owner | Due Date |
|---|---|---|
| ... | ... | ... |
```

---

## Related Business Rules

- **BR-06 (Carrier Fallback)**: SLA-critical shipments must have an alternate carrier evaluated when the primary carrier API is unavailable for > 15 minutes.
- **BR-10 (Deterministic Exception Handling)**: every operational failure must produce a loggable, recoverable state — no silent failures.

---

## Test Scenarios to Add

| # | Scenario | Expected Outcome |
|---|---|---|
| T-OP-01 | Carrier API returns 503 for all calls | Circuit opens; shipments queued; alert fires |
| T-OP-02 | Event bus consumer lag reaches 45 s | `EventBusLagHigh` alert fires; wave throttled |
| T-OP-03 | DB replica lag reaches 10 s | ATP reads switch to primary; alert fires |
| T-OP-04 | Wave planner process killed mid-execution | Orphaned reservations detected within 5 min; cleanup job runs |
| T-OP-05 | Orphan cleanup job runs; ATP invariant still violated | Escalation alert fires; engineer paged |
| T-OP-06 | Carrier recovery after 45-min outage | Retry queue drained in FIFO order; all shipments labelled within 10 min |
