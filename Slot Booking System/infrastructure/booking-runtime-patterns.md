# Booking Runtime Infrastructure Patterns

## 1) Availability Cache Architecture

### Goals
- Sub-50ms availability reads under peak traffic.
- Prevent stale inventory from being shown for longer than the documented consistency window.
- Minimize primary database load during demand spikes.

### Multi-layer cache design
1. **L1 in-process cache (per API pod, 1-3s TTL)**
   - Key: `availability:{resource_id}:{date}:{policy_hash}`
   - Purpose: absorb repeated reads for the same resource/day burst.
2. **L2 distributed cache (Redis/MemoryStore/ElastiCache, 15-60s TTL)**
   - Canonical hot-read store for slot counts and hold counters.
   - Stores both computed availability snapshots and per-slot counters.
3. **Authoritative booking ledger (PostgreSQL)**
   - Source of truth for confirmed bookings and hold rows.
   - Cache is invalidated/updated from booking domain events.

### Write/update strategy
- **Write-through for reserve/release paths** where slot counters must change immediately.
- **Event-driven refresh** for derived calendars (day/week views) using outbox + stream processor.
- **Versioned cache payloads** (`availability_version`) so stale writers do not overwrite newer state.

### Anti-stale controls
- Include `as_of_utc` and `consistency_window_ms` in API response metadata.
- Background reconciliation worker compares DB counters vs cache counters and repairs drift.
- If drift > threshold, force-read from DB and repopulate cache.

---

## 2) Lock Service Strategy

### Lock types
- **Soft hold lock (business lock, TTL-backed)**: used during reserve flow.
- **Short critical-section lock (technical mutex, <=2s)**: used only for atomic transitions requiring serialization.

### Recommended approach
- Primary: **Redis atomic Lua/CAS operations** for high-throughput slot hold operations.
- Fallback: **DB row-level `SELECT ... FOR UPDATE`** for lock service degradation mode.
- Lock key format: `slot_hold:{resource_id}:{slot_start_epoch}`.

### Safety requirements
- Lock payload must include `owner_booking_token`, `expires_at_utc`, and monotonic `fencing_token`.
- Any writer that applies state transitions must validate fencing token to prevent split-brain writes.
- Lock extension is bounded (e.g., max 2 renewals) to avoid starving other users.

---

## 3) Messaging Topology

### Channels
- **Command queue**: reserve/confirm/cancel commands (ordered per booking aggregate key).
- **Domain event bus**: `SlotHeld`, `SlotExpired`, `BookingConfirmed`, `BookingCancelled`, `RefundInitiated`, `RefundSettled`.
- **DLQ + parking-lot queue** for poison messages.

### Partitioning and ordering
- Partition key: `booking_id` for booking lifecycle events, `resource_id` for availability rebuild events.
- Ensure per-key ordering for state-machine transitions.
- Consumers must be idempotent and checkpoint only after durable side effects.

### Delivery guarantees
- At-least-once delivery from broker.
- Exactly-once *effect* via dedup table (`message_id`, `consumer_name`) with TTL or archival.
- Outbox pattern from transactional DB writes to publish events without dual-write anomalies.

---

## 4) Anti-hotspot Scaling Pattern

### Problem
Popular providers/time windows create read/write hotspots on a small keyspace.

### Pattern
1. **Time-bucket sharding**: split counters by `(resource_id, date, 15min_bucket)`.
2. **Virtual shard keys**: hash suffix (`slot_key#v0..vN`) for high-contention slots.
3. **Queue-based serialization by shard**: enqueue reserve attempts by hot shard to smooth bursts.
4. **Adaptive TTL + jitter**: avoid synchronized cache expiry stampedes.
5. **Token-bucket admission control** per resource to protect downstream DB/PSP.

### Operational playbook
- Detect hotspot when `lock_contention_rate` or `retry_rate` crosses threshold.
- Auto-enable higher virtual-shard fanout and stricter client retry backoff.
- Temporarily degrade expensive read models (e.g., disable month view) during extreme surges.

---

## 5) Non-functional Acceptance Criteria (Infrastructure View)

- **Throughput**
  - Sustain >= **2,000 reserve attempts/sec** regionally for 15 minutes.
  - Sustain >= **500 confirms/sec** with payment callbacks enabled.
- **Latency (p95)**
  - Availability read p95 <= **120ms**.
  - Reserve p95 <= **180ms** (excluding external payment processing).
  - Confirm status update p95 <= **200ms** once PSP callback is received.
- **Consistency window**
  - Availability UI may lag authoritative ledger by at most **2 seconds** under normal load.
  - Under degraded mode, lag must remain <= **10 seconds** with user-visible freshness timestamp.

