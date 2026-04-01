# Edge Cases: Telemetry Ingestion — IoT Device Management Platform

## Introduction

Telemetry ingestion at IoT scale is defined by properties that distinguish it sharply from standard API traffic: the data source is inherently bursty (devices buffer locally and flush on reconnect), the senders are resource-constrained (limited RAM, no retry loop management, firmware-level serialization bugs), the network path is unreliable (intermittent connectivity causes buffered backlog), and the volume is enormous (50,000 devices each sending 10 readings per minute = 500,000 messages per minute at steady state, with potential spikes to 5× that during reconnect storms).

These characteristics create failure modes that do not exist in web application backends. A single firmware bug rolled out to a large fleet generates a systematic stream of malformed messages that must be quarantined without blocking valid data from healthy devices. Out-of-order timestamps from reconnecting devices can cause time-series database writes to fail silently or trigger spurious alerting rules. Duplicate messages — an unavoidable consequence of QoS 1 delivery — must be deduplicated without introducing a write bottleneck.

The platform's telemetry ingestion pipeline is designed around the principle of "reject early, quarantine everything, discard nothing." Messages that cannot be processed are never dropped silently — they are routed to a structured dead-letter queue with machine-readable rejection metadata, enabling both automated retry and human-operator review. Every edge case in this document represents a scenario where this principle was tested, refined, or extended.

---

## Message Queue Overflow During Device Swarm Activation

### Scenario Description

Grid power restoration events — a utility grid recovering from an outage, a factory power cycle, a building management system resuming operations — bring large device fleets online simultaneously. A fleet of 50,000 devices that was offline for 5 minutes each wakes up at approximately the same moment and executes an identical sequence: establish TLS connection to EMQX, authenticate, publish CONNACK event, flush locally-buffered telemetry.

For a 5-minute outage and a device sampling at 2Hz, each device has 600 buffered readings. 50,000 devices flushing 600 messages each within a 30-second window generates 30,000,000 messages in 30 seconds — a sustained rate of 1,000,000 messages per second. The platform's design-capacity for steady-state ingestion is 50,000 messages per second; this swarm represents a 20× spike.

The EMQX MQTT broker absorbs the connection storm and begins forwarding messages to the Kafka bridge. The Kafka producer's in-memory buffer (default: 32MB per bridge instance) fills within 10 seconds. EMQX begins applying backpressure to the message receive loop, which causes per-client PUBACK delays to increase. Devices awaiting PUBACK for QoS 1 messages stop sending new messages (QoS 1 flow control: in-flight window = 10 messages per device). The storm effectively throttles itself, but the in-flight messages continue to pile up in Kafka partitions faster than consumers can process them.

### Trigger Conditions

- Grid power restoration after planned or unplanned outage affecting devices in a geographic region
- EMQX cluster restart after maintenance (all devices reconnect within the reconnect backoff window)
- Network partition recovery (devices were connected to isolated network segment)
- Factory line power-on at shift start (if devices buffer telemetry when no network is available)
- NTP synchronization restoring timestamps after clock drift causes devices to defer publishing

### Impact

- **Kafka consumer lag:** `telemetry-raw` consumer group lag grows from 0 to 2,000,000+ messages within 5 minutes. Alert `KAFKA-LAG-001` fires. p99 latency for alert rule evaluation degrades from 500ms to 5–10 minutes.
- **InfluxDB write throughput:** Batch writer queue (default max: 10,000 pending batches) fills within 2 minutes. InfluxDB write error rate increases as the batch writer applies backpressure. Memory usage on the batch writer pod increases significantly; OOM risk if the pod's limit is set too conservatively.
- **Rules engine staleness:** `telemetry-alerts-cg` consumer group experiences lag proportional to the backlog. Alert evaluations are delayed by the lag duration. A real threshold breach during the backlog period may fire a delayed alert (minutes after the event) or be superseded by the corrected value arriving later.
- **Downstream services:** API queries to `GET /devices/{id}/telemetry/latest` return stale data for the duration of the backlog processing period.

### Detection

- **Alert `KAFKA-LAG-001`:** `telemetry-raw` consumer group max lag > 100,000 messages for any consumer group for > 2 minutes.
- **Alert `INGEST-RATE-001`:** EMQX publish rate > 200,000 messages/second (4× steady-state throughput) for > 30 seconds.
- **Alert `INFLUX-QUEUE-001`:** InfluxDB batch writer pending queue depth > 5,000 for > 60 seconds.
- **Dashboard:** `Telemetry Ingestion Health` Grafana dashboard shows real-time Kafka lag per consumer group, EMQX message rates, and InfluxDB write throughput in a single pane.
- **Log pattern:** `WARN emqx_bridge_backpressure applied=true queue_depth=<n>` — indicates EMQX bridge is applying backpressure to the MQTT receive loop.

### Mitigation

**Per-client EMQX rate limiting:** Each device is limited to 1,000 published messages per second by the EMQX rate-limit plugin (configurable per device model and per organization). Devices that exceed this limit receive PUBACK with no error but their messages are queued at the broker rather than immediately forwarded to the Kafka bridge, smoothing the burst.

**Kafka auto-scaling consumer group (KEDA):** The `telemetry-timeseries-cg` consumer group is managed by KEDA (Kubernetes Event-Driven Autoscaler) with the Kafka lag metric as the scaling trigger. Configuration: `lagThreshold: 50000`, `minReplicaCount: 4`, `maxReplicaCount: 32`. When lag exceeds 50,000, KEDA adds consumer replicas (up to 32, matching the number of `telemetry-raw` partitions). Scale-up response time: 60–90 seconds.

**Telemetry batch API:** The device SDK supports a batch publish format: a single MQTT message containing an array of readings, reducing broker overhead by 10× per device. Devices using the batch API publish one message containing 600 readings vs. 600 individual messages, reducing per-message overhead (MQTT fixed header, QoS 1 flow control, Kafka key extraction) by an order of magnitude.

**InfluxDB circuit breaker:** The InfluxDB batch writer circuit breaker opens when pending write queue depth exceeds 10,000. In the open state, new batches from the Kafka consumer are held in a local retry buffer (disk-backed ring buffer, max 2GB). This prevents the batch writer pod from OOM-killing itself while InfluxDB catches up. Kafka offsets are not committed for batches in the retry buffer, ensuring reprocessing.

### Recovery Procedure

1. Confirm the swarm source via `GET /admin/metrics/mqtt?group_by=client_ip_range` — identify which IP range or MQTT client ID pattern represents the reconnecting fleet.
2. If consumer lag is > 1,000,000 and KEDA has not yet scaled: manually scale the consumer group `kubectl scale deployment telemetry-timeseries-consumer --replicas=32`.
3. Monitor InfluxDB write error rate: `GET /internal/influxdb/metrics?metric=write_error_rate`. If > 5%, check circuit breaker state; if OPEN, the retry buffer is active and no intervention is needed.
4. Verify EMQX per-client rate limiting is active: `GET /internal/emqx/rate-limit/status`. Confirm per-client limit is enforced.
5. Monitor lag drain: Kafka consumer lag should reduce by at least 10% per minute once the storm peak passes. If lag is not draining, check consumer group health: `kafka-consumer-groups.sh --describe --group telemetry-timeseries-cg`.
6. After lag clears (< 1,000 messages), verify rules engine has caught up: `GET /internal/rules-engine/lag`. Confirm `last_evaluated_at` is within 60 seconds of current time for all active alert rules.
7. Review delayed alerts fired during the backlog period: `GET /alerts?status=fired&fired_after=<storm_start>&fired_before=<lag_clear_time>`. Notify affected organizations that alerts during this window may have been delayed.

### Preventive Measures

- Require device SDK version 2.3+ which implements staggered reconnect with random backoff after disconnection (base: 5s, cap: 300s, jitter: full). This reduces the reconnect storm from a simultaneous spike to a 300-second distributed ramp.
- Provision `telemetry-raw` with 32 Kafka partitions (current). Ensure consumer group has capacity up to 32 replicas (KEDA max = 32). Increase partition count to 64 if steady-state consumer group lag exceeds 10,000 for more than 5 minutes per day.
- Schedule `telemetry-timeseries-cg` scale-up preemptively before known grid restoration events (coordinate with grid operators for planned restoration windows).
- Configure InfluxDB `max_concurrent_compactions = 4` and `cache-max-memory-size = 4GB` to ensure the TSM engine does not bottleneck on compaction during write storms.

---

## Out-of-Order Timestamps

### Scenario Description

IoT devices frequently operate with intermittent connectivity. A sensor installed in a remote location with cellular connectivity may lose signal for hours at a time, buffering readings locally in flash or SRAM. When connectivity is restored, the device publishes the backlog with the original device-side timestamps — timestamps that may be many hours or days in the past relative to the server's clock.

The platform's time-series database (InfluxDB / TimescaleDB) organizes data into time-bounded shards. InfluxDB uses a default shard duration of 24 hours for the telemetry retention policy. A shard is "hot" (accepting writes) for its duration, then "warm" and finally "cold" (sealed). Out-of-order writes to cold shards are rejected by default because the TSM (Time-Structured Merge Tree) engine must reopen and re-compact the shard — an expensive operation that can impact write throughput on current hot shards.

Separately, the rules engine evaluates alert conditions using time windows relative to the evaluation trigger time. If telemetry with an old device_timestamp arrives and is processed by the `telemetry-alerts-cg` consumer group (which does not filter by device_timestamp), the rules engine may evaluate the old value as if it were current, firing a spurious alert or suppressing a real one depending on the direction of the stale value.

### Trigger Conditions

- Device reconnects after > 6 hours of offline time with locally-buffered telemetry
- Device clock is not NTP-synchronized and drifts significantly over time (common in low-power devices that sleep the RTC to conserve battery)
- Device firmware bug that records timestamps in local timezone without UTC offset metadata
- Device deliberately back-fills historical data from offline logging (e.g., after deploying new firmware that enables telemetry)
- Satellite IoT connectivity (Iridium, Starlink terminal) with high latency and periodic blackout windows

### Impact

- **InfluxDB write failures:** Out-of-order writes to shards older than 24 hours are rejected with `partial write: points beyond retention policy`. The affected data points are logged to the DLQ. Data gaps appear in historical telemetry charts.
- **Spurious alert firing:** Rules engine receives old telemetry with a value that breaches a threshold. Fires an alert for a condition that occurred hours ago and may have already self-corrected. On-call engineer investigates an already-resolved condition.
- **Alert suppression:** Worse, if the old value is within normal range and a current value (which is out-of-threshold) arrives later in the Kafka partition, the rules engine sees the old value first and does not fire an alert.
- **Dashboard confusion:** `device_timestamp` and `server_ingest_timestamp` diverge visibly. Users see telemetry charts with apparent gaps followed by a burst of historical data appearing at the wrong point on the x-axis.

### Detection

- **Metric `telemetry_timestamp_delta_histogram`:** Histogram of `server_ingest_timestamp - device_timestamp` per organization. Normal: p99 < 10 seconds. Out-of-order threshold: delta > 3600 seconds (1 hour). Alert `TELEM-OOO-001` fires when p95 delta > 3600s for any organization.
- **InfluxDB metric:** `influxdb_write_out_of_order_errors_total` counter. Alert when rate > 100/minute.
- **Rules engine metric:** `spurious_alert_candidate_count` — rules engine tracks cases where an alert fires for data more than `max_alert_data_age_seconds` (default: 300s) behind wall clock. These are logged as candidates for review.
- **Log pattern:** `WARN out_of_order_write device_id=<id> device_timestamp=<t> delta_seconds=<n>` in InfluxDB batch writer.

### Mitigation

**Configurable timestamp acceptance window:** The TelemetryService accepts writes with `device_timestamp` up to 7 days in the past (configurable per organization: `min` 1 hour, `max` 30 days). Writes with `device_timestamp` older than the acceptance window are quarantined rather than written. The acceptance window is stored in the organization's telemetry configuration and enforced in the Kafka consumer before attempting the InfluxDB write.

**Dual timestamp storage:** Every telemetry record stores both `device_timestamp` (from device payload) and `server_ingest_timestamp` (applied by the TelemetryService at ingestion time). InfluxDB uses `server_ingest_timestamp` as the primary index timestamp (avoiding out-of-order shard issues). `device_timestamp` is stored as a tag field and used for accurate data visualization and export.

**Alert rule timestamp mode:** Alert rules support two evaluation modes:
- `timestamp_mode: server` — Rule evaluates using `server_ingest_timestamp`. Prevents out-of-order data from triggering spurious alerts. Default for all new rules.
- `timestamp_mode: device` — Rule evaluates using `device_timestamp`. Useful for rules that must reflect the actual event time (e.g., safety-critical threshold violations). Opt-in, with explicit acknowledgment that spurious alerts are possible.

Rules with `timestamp_mode: device` additionally support `require_recent_data: true` and `max_data_age_seconds: 300`, which suppresses evaluation if the most recent data point for the device (by `server_ingest_timestamp`) is older than 300 seconds.

**InfluxDB TSM optimization:** Configure `max-values-per-tag = 0` (unlimited) and enable `tsm-use-madv-willneed = true` to improve performance for out-of-order workloads that force shard reopening.

### Recovery Procedure

1. Identify the device(s) generating out-of-order telemetry: `GET /devices?filter=telemetry_timestamp_delta_p95_gt=3600&organization_id=<org_id>`.
2. Check the device's telemetry configuration for acceptance window: `GET /devices/{id}/telemetry-config`.
3. If the backlog represents legitimate historical data (e.g., sensor deployed offline for days then brought online): set `accept_historical_data: true` and `max_data_age_days: 30` for this device via `PATCH /devices/{id}/telemetry-config`.
4. Replay quarantined messages from the DLQ for this device: `POST /internal/dlq/replay?device_id=<id>&topic=telemetry-raw-dlq&reason_code=OUT_OF_ORDER_TIMESTAMP`.
5. Verify InfluxDB accepted the backfill writes: `GET /devices/{id}/telemetry?from=<oldest_timestamp>&to=<newest_timestamp>&limit=100`.
6. Review and dismiss any spurious alerts that fired during the backfill: `GET /alerts?device_id=<id>&status=firing&timestamp_mode=device`. For each: `POST /alerts/{alert_id}/dismiss?reason=out_of_order_data_backfill`.
7. If the device clock is drifting (device_timestamp consistently ahead or behind server by a fixed offset): update device shadow to trigger NTP resync: `PUT /devices/{id}/shadow {"desired": {"ntp_sync_immediate": true}}`.

### Preventive Measures

- Require NTP synchronization in device firmware with a startup check: device does not begin publishing telemetry until NTP sync is confirmed (configurable grace period: 30 seconds for initial connectivity).
- Configure device SDK to include `timestamp_source: "device_rtc"` or `timestamp_source: "ntp_synced"` in each telemetry message. TelemetryService applies additional validation for `device_rtc` timestamps (widens suspicion threshold for large offsets).
- Set InfluxDB shard duration to 1 hour for high-frequency telemetry measurements (> 10Hz) to reduce the performance cost of out-of-order shard reopening.

---

## Duplicate Telemetry

### Scenario Description

MQTT QoS 1 guarantees at-least-once delivery. This means that when a network partition occurs between a device and EMQX after the device publishes a message but before it receives the PUBACK, the device will retransmit the message with the DUP flag set. The EMQX broker delivers both the original and the retransmission to the Kafka bridge as separate messages. This is correct MQTT behavior — it is the responsibility of the subscriber (in this case, the TelemetryService) to handle duplicates.

In practice, devices with poor connectivity (cellular, LoRaWAN backhaul, congested WiFi) generate significant duplicate rates — observed as high as 2–5% on some industrial sensor deployments. At 50,000 devices publishing 10 messages/minute, a 2% duplicate rate represents 10,000 duplicate messages per minute continuously.

The InfluxDB time-series database is idempotent for exact duplicates: a write of the same measurement, tag set, timestamp, and field values overwrites the existing point without error. This handles the simple case. The complex case is near-duplicates: same device, same timestamp, slightly different field values. This occurs when sensor hardware reads slightly different values between the original transmission and the retransmission (e.g., an ADC that samples on every read call). Near-duplicates result in data pollution: if the duplicate write wins, the stored value changes silently.

### Trigger Conditions

- Network congestion causing PUBACK delivery delay beyond the device's retransmit timeout (typically 5–30 seconds in firmware)
- EMQX broker restart with in-flight QoS 1 messages: broker does not persist QoS 1 session state by default across restarts, causing devices to retransmit unacknowledged messages on reconnect
- MQTT 3.1.1 clean session = false: broker persists queued messages for offline devices; on reconnect, previously-delivered messages may be re-queued
- Device firmware bug where the DUP flag is not set on retransmissions (treated as new messages by broker, no deduplication at broker level)
- Double-publish bug in device firmware (message published twice in the same code path)

### Impact

- **Exact duplicates:** Silently overwritten by InfluxDB. No data corruption. Minor write amplification (2×).
- **Near-duplicates:** One of the two values is silently discarded; which value wins depends on write order, which is non-deterministic across Kafka partition reordering. Calculated aggregates (averages, p99s) are slightly incorrect.
- **Rules engine double-firing:** If a threshold crossing is represented twice (two near-duplicate messages where both breach the threshold), the rules engine may fire two alert notifications for the same event. Two PagerDuty incidents opened for one physical event.
- **Audit log inflation:** Duplicate telemetry records in the immutable audit S3 bucket inflate storage costs and complicate compliance reporting.

### Detection

- **Metric `telemetry_duplicate_rate`:** TelemetryService tracks the rate of messages rejected by the deduplication cache (Redis SET NX check). Alert `TELEM-DUP-001` when rate > 5% of total message volume per device for > 5 minutes.
- **Near-duplicate detection:** A background analysis job (`near-dup-analyzer`) runs every 15 minutes, scanning for InfluxDB time series where the same timestamp has been written with different values within the last hour. Publishes `telemetry.near_duplicate_detected` events for operator review.
- **Kafka offset anomaly:** Kafka message `message_id` field tracked in Redis. If the same `message_id` appears in different Kafka partitions (possible due to EMQX bridge rebalancing), it indicates a systematic duplication issue at the broker level.
- **Log pattern:** `DEBUG dedup_cache_hit message_id=<uuid> device_id=<id>` — DEBUG level by default, promoted to INFO when hit rate exceeds 1% per device.

### Mitigation

**UUID message_id in telemetry payload:** The Platform Device SDK generates a UUID v4 `message_id` for every telemetry message. The TelemetryService, upon receiving a message, performs `SET NX telemetry:dedup:<message_id> 1 EX 300` in Redis. If the SET returns 0 (key already exists), the message is an exact or near-duplicate and is discarded (not written to InfluxDB) with a `DUPLICATE_MESSAGE_ID` counter increment. The 5-minute TTL balances deduplication coverage against Redis memory usage.

For devices using firmware that does not support `message_id` (older SDK versions < 1.8): the TelemetryService generates a deterministic message_id from `HMAC-SHA256(device_id + ":" + device_timestamp + ":" + payload_hash)` for deduplication purposes.

**MQTT 5.0 message expiry interval:** Devices connecting with MQTT 5.0 protocol include a `Message Expiry Interval` of 60 seconds in the PUBLISH packet. EMQX discards queued messages older than 60 seconds without delivering them to subscribers, eliminating retransmits that arrive too late to be useful.

**InfluxDB idempotency as second-line defense:** For messages that pass the Redis dedup check (e.g., different `message_id` but same content — double-publish bug), InfluxDB exact-duplicate idempotency ensures no data corruption for exact duplicates. Near-duplicates still result in last-write-wins behavior.

### Recovery Procedure

1. Identify the device(s) with elevated duplicate rate: `GET /admin/metrics/telemetry?metric=duplicate_rate&group_by=device_id&threshold=0.05`.
2. For each affected device, check the firmware version: `GET /devices/{id}`. If firmware version < 1.8 (no `message_id` support): initiate OTA update to latest SDK.
3. If the duplicate rate is caused by a specific MQTT session configuration (clean_session = false with problematic QoS 1 messages): update the device shadow to force clean session on next reconnect: `PUT /devices/{id}/shadow {"desired": {"mqtt_clean_session": true, "reconnect_required": true}}`.
4. For near-duplicate data pollution, if confirmed by the `near-dup-analyzer` report: perform targeted InfluxDB DELETE for the polluted time range and replay from the audit S3 bucket (which preserves the first-received value for each timestamp).
   ```
   POST /internal/influxdb/delete
   {"device_id": "<id>", "measurement": "<m>", "from": "<t1>", "to": "<t2>"}
   ```
5. After deletion, replay from audit log: `POST /internal/telemetry/replay-from-audit?device_id=<id>&from=<t1>&to=<t2>&conflict_policy=first_write_wins`.
6. Verify the near-duplicate alert fired only once: `GET /alerts?device_id=<id>&status=all&from=<t1>`. Close duplicate alert instances manually with `POST /alerts/{id}/close?reason=near_duplicate_dedup_applied`.

### Preventive Measures

- Mandate `message_id` field in telemetry payload schema for all new device model registrations. Validation enforced by SchemaValidator; payloads without `message_id` from devices on SDK >= 2.0 are rejected with `MISSING_MESSAGE_ID`.
- Set Redis deduplication TTL to match the device's maximum retransmit timeout × 2 (current: 300s; if device retransmit timeout is > 150s, increase TTL accordingly). Monitor per-device retransmit timeout via device shadow attribute `mqtt_retransmit_timeout_ms`.
- Configure EMQX `mqtt.max_inflight = 10` (default) to limit per-client in-flight QoS 1 messages, reducing the maximum duplicate window to the in-flight window × transmission time.

---

## Malformed Payload

### Scenario Description

Device firmware is written in C or C++ on constrained microcontrollers, often without comprehensive test coverage or static analysis tooling. Firmware bugs that introduce malformed telemetry payloads are common across the lifecycle of a large fleet. A firmware update that changes a temperature sensor's output format from `float32` to `int16` without updating the serialization code produces payloads where temperature is encoded as an integer, breaking schema validation. A buffer overflow in the JSON serializer truncates payloads at unpredictable positions, producing invalid JSON. An uninitialized variable produces `NaN` or `Infinity` for numeric fields on certain code paths.

These bugs typically manifest across entire device cohorts: all devices running the same firmware version exhibit the same malformed payload pattern simultaneously. The SchemaValidator (deployed as a Kafka Streams processor in the `telemetry-raw` pipeline) detects the malformed messages and routes them to the DLQ. If the malformation rate is high enough (> 80% of a device cohort's messages are malformed), the effective telemetry data rate for that cohort drops to near zero — operators see all devices in the cohort appear "silent" on the dashboard while the devices are actually actively publishing.

### Trigger Conditions

- Firmware update that changes the telemetry schema without a corresponding schema registry update
- Uninitialized variable producing IEEE 754 special values (NaN, +Infinity, -Infinity) for sensor readings
- Buffer overflow or underflow in device-side JSON serialization causing truncated or corrupted payloads
- Device payload exceeding the platform's configured `max_payload_bytes = 262144` (256KB) limit enforced by EMQX
- Device publishing to wrong topic format (e.g., `devices/123/telemetry` instead of `devices/d-abc123/telemetry`) causing routing failure
- Encoding mismatch: device publishes binary CBOR payload to a topic configured for JSON

### Impact

- **Device cohort silence:** All devices running the affected firmware version have their telemetry routed to the DLQ. Dashboard shows all devices as "no recent data" despite active MQTT connections.
- **Alert suppression:** Alert rules that require `require_recent_data: true` suppress notifications because no valid data arrives within the evaluation window. Real threshold violations go undetected.
- **DLQ volume spike:** `telemetry-raw-dlq` receives high message volume. Retention period (7 days) may be exceeded if volume is extremely high, causing oldest DLQ messages to be expired before review.
- **Operator investigation load:** High-volume DLQ events from multiple devices require triage to identify the root cause (firmware version correlation).

### Detection

- **Alert `TELEM-MALFORM-001`:** `schema_validation_failure_rate` for any device > 10% of messages over 5 minutes.
- **Alert `TELEM-MALFORM-002`:** `schema_validation_failure_rate` for any device model (cohort) > 5% over 15 minutes — indicates firmware-level issue, not individual device fault.
- **DLQ volume alert:** `telemetry-raw-dlq` message production rate > 1,000/minute triggers `DLQ-VOLUME-001`.
- **Firmware correlation dashboard:** The `Telemetry Quality` Grafana dashboard includes a panel showing `schema_failure_rate` grouped by `firmware_version`. A new firmware version appearing with elevated failure rate is immediately visible.
- **EMQX metric:** `emqx_messages_dropped_packet_too_large` counter — alerts on rate > 10/minute.
- **Log pattern:** `ERROR schema_validation_failed device_id=<id> firmware_version=<v> field=<f> expected=<type> got=<type>` in SchemaValidator.

### Mitigation

**EMQX payload size enforcement:** `max_packet_size = 262144` bytes enforced at the MQTT protocol layer. Oversized packets are rejected with `DISCONNECT 0x95` (Packet Too Large in MQTT 5.0). The device receives a clean error code and can log the rejection — no data reaches the broker.

**Schema validation in Kafka Streams:** The SchemaValidator reads from `telemetry-raw` and validates each message against the device model's registered JSON Schema (stored in the Schema Registry, linked to device model version). Invalid messages are produced to `telemetry-raw-dlq` with structured rejection metadata. Valid messages are produced to `telemetry-validated`. Downstream consumers (`telemetry-timeseries-cg`, `telemetry-alerts-cg`) consume from `telemetry-validated`, ensuring malformed messages never reach InfluxDB or the rules engine.

**Firmware version correlation and automatic alert:** The DeviceService monitors `schema_failure_rate` grouped by `firmware_version`. If a firmware version transitions from `failure_rate < 1%` to `failure_rate > 10%` within 1 hour of a new firmware version appearing in the fleet (detected via device shadow `firmware_version` attribute), it automatically creates a `FIRMWARE_TELEMETRY_ISSUE` incident and sends notifications to the organization's admin contacts.

**Schema evolution policy:** The Schema Registry enforces backward compatibility for schema updates. A schema change that breaks existing device payloads (e.g., changing a field type from string to float) is rejected by the registry with `SCHEMA_INCOMPATIBLE_CHANGE`. Additive changes (new optional fields) are accepted. This prevents accidental schema mismatches from platform-side schema updates.

### Recovery Procedure

1. Identify the firmware version causing the malformed payloads: `GET /admin/metrics/telemetry/schema-failures?group_by=firmware_version&interval=1h`.
2. Check the schema failure detail to understand the specific malformation: `GET /internal/dlq/messages?topic=telemetry-raw-dlq&limit=10&device_model_id=<id>` — read the `rejection_detail` field.
3. Create an OTA deployment to push a corrected firmware version to affected devices: `POST /ota/deployments` targeting the affected firmware version cohort with the corrected firmware version.
4. For DLQ messages that can be replayed once the firmware is corrected (i.e., the device will re-publish the data on next telemetry cycle): no action needed — DLQ messages represent the malformed format that cannot be decoded.
5. If the malformed payloads contain recoverable data (e.g., payload is valid JSON but has a wrong field type that can be coerced): write a DLQ replay processor: `POST /internal/dlq/replay-transform?topic=telemetry-raw-dlq&transform_script=<script_id>&device_model_id=<id>`. The transform script performs type coercion before re-injecting into `telemetry-validated`.
6. After OTA deploys to > 90% of affected devices, verify schema failure rate has returned to < 1%: `GET /admin/metrics/telemetry?metric=schema_failure_rate&firmware_version=<new_version>`.
7. Review alert suppression period: identify any alert rules that may have missed threshold violations during the malformed period: `GET /alerts?status=suppressed&device_model_id=<id>&from=<issue_start>&to=<issue_resolved>`.

### Preventive Measures

- Require schema registration in the Schema Registry before any firmware version can be deployed via OTA. The OTAService validates that the firmware version's declared schema is registered and compatible with the previous version.
- Include telemetry validation as a test case in device firmware CI/CD: the firmware build pipeline must publish a sample telemetry payload to a staging Schema Registry and confirm it passes validation.
- Enable `json_strict_mode` in EMQX to reject non-JSON payloads for topics configured as JSON. Reduces the volume of binary/CBOR payloads accidentally published to JSON topics.

---

## Time-Series Database Write Failure

### Scenario Description

InfluxDB is the primary store for all telemetry data on the platform. It receives write requests from the `telemetry-timeseries-cg` Kafka consumer group via a batch writer service. The batch writer accumulates points from the Kafka consumer into batches of up to 5,000 points (configurable) and submits them to InfluxDB via the HTTP write API every 1 second or when the batch fills, whichever comes first.

Write failures occur in several forms. An InfluxDB node failure during a batch submission may partially commit the batch — some points are written to the WAL (Write-Ahead Log) before the failure, others are not. The InfluxDB HTTP response is either an error (5xx) or a timeout, but the caller cannot determine how many points (if any) were committed. A Kafka offset commit after this ambiguous response would cause those points to be skipped forever; not committing the offset causes the entire batch to be retried, creating potential duplicates for points that were committed before the failure.

A second scenario involves InfluxDB cluster leader election. When the InfluxDB cluster (configured as a 3-node cluster for HA) performs a leader election (triggered by network partition, node failure, or planned maintenance), the election window takes 30–60 seconds. During this window, write requests to the leader candidate fail with `503 Service Unavailable`. All write requests queued during the election window must be retried after the new leader is established.

### Trigger Conditions

- InfluxDB data node failure (disk full, OOM kill, hardware failure)
- InfluxDB cluster leader election triggered by network partition or planned node maintenance
- InfluxDB compaction backpressure: TSM compaction queue overflows, write path blocked
- PostgreSQL connection pool exhaustion causing write API HTTP gateway to fail (if InfluxDB uses a PostgreSQL-backed metadata store)
- S3/MinIO failure for InfluxDB WAL backup (if WAL replication is enabled)
- Kubernetes pod eviction due to node memory pressure during high-throughput write storms

### Impact

- **Data loss risk:** Minimal, if retry logic is correct. The batch writer uses at-least-once delivery with idempotent InfluxDB writes — retried points overwrite existing points without error. The only data loss scenario is if the retry buffer overflows (max: 2GB disk-backed buffer, ~10 minutes of data at peak throughput) and the retry buffer is cleared due to pod restart before InfluxDB recovers.
- **Consumer lag:** Kafka offsets are not committed during write failures. `telemetry-timeseries-cg` lag grows at the ingestion rate × failure duration.
- **Dashboard staleness:** `GET /devices/{id}/telemetry/latest` returns increasingly stale data. Operators may incorrectly assume devices are offline.
- **Alert rule evaluation:** The `telemetry-alerts-cg` is independent of the InfluxDB writer and continues evaluating. However, any alert rules that query InfluxDB for aggregate functions (e.g., rolling average over 1 hour) receive stale data.

### Detection

- **Alert `INFLUX-WRITE-001`:** InfluxDB write error rate > 1% over 60-second window.
- **Alert `INFLUX-WRITE-002`:** Batch writer retry buffer depth > 50% (1GB of 2GB capacity) for > 5 minutes.
- **Alert `KAFKA-LAG-002`:** `telemetry-timeseries-cg` lag growth rate > 0 for > 2 minutes while InfluxDB write error rate > 0 (confirms the lag is caused by write failures, not processing slowness).
- **InfluxDB health endpoint:** `GET http://influxdb:8086/health` polled every 10 seconds. Response status 503 triggers immediate alert and circuit breaker opening.
- **Log pattern:** `ERROR influxdb_write_failed batch_size=<n> error=<message> retry_count=<n>` in batch writer service.

### Mitigation

**At-least-once delivery with idempotent writes:** The batch writer commits the Kafka offset only after receiving a confirmed `204 No Content` response from InfluxDB. On any non-2xx response or timeout, the batch is placed in the retry buffer and the offset is not committed. InfluxDB's write idempotency (same series + timestamp = overwrite) ensures retried batches do not create duplicate data.

**Circuit breaker with disk-backed retry buffer:** The batch writer circuit breaker opens after 5 consecutive InfluxDB write failures or when the write error rate exceeds 10% in a 30-second window. In the OPEN state, the consumer continues reading from Kafka but routes batches to a disk-backed retry buffer (`/var/lib/telemetry-writer/retry-buffer`) rather than attempting InfluxDB writes. The consumer group lag grows during this period, but no data is lost. The circuit breaker enters HALF-OPEN after 60 seconds, sends a probe write (1-point batch), and transitions to CLOSED on success.

**Write timeout and retry configuration:**
- InfluxDB write HTTP timeout: 5 seconds
- Retry attempts: 3
- Retry backoff: 1s, 2s, 4s (exponential, no jitter — fixed backoff acceptable for database retries within the same writer pod)
- Maximum retry age: 5 minutes (batches older than 5 minutes are moved to the DLQ with `INFLUX_WRITE_TIMEOUT` reason)

**InfluxDB HA cluster:** 3-node InfluxDB cluster with automatic leader election. Minimum quorum = 2 nodes. Single-node failure does not interrupt write availability. Data replication factor = 2 (every point written to 2 nodes). Recovery from single-node failure requires no operator action.

### Recovery Procedure

1. Confirm the failure cause via InfluxDB cluster status: `GET http://influxdb-admin:8086/api/v2/health` on each node. Identify which node(s) are unhealthy.
2. If a node is down (OOM, disk full, hardware): check Kubernetes pod status: `kubectl get pods -n telemetry -l app=influxdb`. If pod is in `CrashLoopBackOff`, check logs: `kubectl logs influxdb-<pod> --previous`.
3. If disk full: expand the InfluxDB PVC (if on a dynamic storage provider): `kubectl patch pvc influxdb-data-0 -p '{"spec":{"resources":{"requests":{"storage":"500Gi"}}}}'`. Confirm the node resumes.
4. Monitor circuit breaker state: `GET /internal/telemetry-writer/circuit-breaker/state`. Confirm it transitions to CLOSED within 60 seconds of InfluxDB recovery.
5. Drain the retry buffer: once the circuit breaker closes, the retry buffer drains automatically. Monitor via `GET /internal/telemetry-writer/retry-buffer/depth`. Confirm it decreases to 0.
6. Confirm Kafka consumer lag returns to < 10,000: `kafka-consumer-groups.sh --describe --group telemetry-timeseries-cg`.
7. If any batches exceeded the 5-minute maximum retry age and were routed to the DLQ: replay them after confirming InfluxDB is stable: `POST /internal/dlq/replay?topic=telemetry-raw-dlq&reason_code=INFLUX_WRITE_TIMEOUT&from=<failure_start>&to=<failure_end>`.
8. Verify data continuity: for 3 representative devices, query InfluxDB for the failure window: `GET /devices/{id}/telemetry?from=<failure_start>&to=<failure_end>`. Confirm no unexplained gaps.

### Preventive Measures

- Configure InfluxDB disk usage alert at 70% capacity (alert) and 85% (critical). At 85%, initiate emergency data compaction and archive old retention buckets to S3 Cold Storage.
- Enable InfluxDB WAL replication to S3 for point-in-time recovery. WAL segment files uploaded to `s3://telemetry-wal-backup/<node_id>/` every 60 seconds. Maximum data loss on catastrophic cluster failure: 60 seconds.
- Size the retry buffer generously relative to expected recovery time: at 50,000 points/second peak write rate, a 2GB buffer holds approximately 8 minutes of data. If InfluxDB outages routinely exceed 8 minutes (e.g., cluster election takes 5 minutes), increase buffer to 8GB.
- Schedule InfluxDB maintenance windows during low-telemetry periods (overnight), and pre-scale the retry buffer before planned maintenance.
