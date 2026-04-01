# IoT Platform Operational Edge Cases

## Table of Contents
1. [Introduction](#introduction)
2. [Kafka Consumer Lag During Device Swarm Activation](#1-kafka-consumer-lag-during-device-swarm-activation)
3. [InfluxDB Disk Exhaustion from Telemetry Burst](#2-influxdb-disk-exhaustion-from-telemetry-burst)
4. [MQTT Broker Failover During Active Device Communication](#3-mqtt-broker-failover-during-active-device-communication)
5. [Certificate Authority Rotation Affecting All Provisioned Devices](#4-certificate-authority-rotation-affecting-all-provisioned-devices)
6. [Mass Device Re-Provisioning After Security Incident](#5-mass-device-re-provisioning-after-security-incident)
7. [Telemetry Data Backfill After Prolonged Platform Outage](#6-telemetry-data-backfill-after-prolonged-platform-outage)
8. [Rules Engine Processing Backlog During Alert Storm](#7-rules-engine-processing-backlog-during-alert-storm)
9. [Time-Series Data Retention Policy Execution Causing Query Failures](#8-time-series-data-retention-policy-execution-causing-query-failures)
10. [Edge Gateway Network Partition — Devices Isolated from Cloud](#9-edge-gateway-network-partition--devices-isolated-from-cloud)
11. [Firmware OTA Update Failure — Device Bricked State](#10-firmware-ota-update-failure--device-bricked-state)
12. [SLA Summary Table](#sla-summary-table)

---

## Introduction

This document captures critical operational edge cases for the IoT Device Management Platform, which operates at scale with 100,000+ connected devices, processing millions of telemetry events daily. The platform integrates MQTT message brokers, Kafka streams, InfluxDB time-series storage, certificate management, firmware update infrastructure, and distributed rules engines.

These scenarios represent high-impact failure modes identified through production incidents, load testing, and chaos engineering exercises. Each scenario includes detection mechanisms, preventive mitigations, and recovery procedures to minimize Mean Time To Recovery (MTTR) and maintain service level agreements.

The platform must operate with 99.9% availability, sub-second device communication latency, and support 10,000+ simultaneous device connections per region.

---

## 1. Kafka Consumer Lag During Device Swarm Activation

### Scenario Description
During scheduled firmware rollout phases, 10,000 devices reconnect simultaneously. These devices resume buffered telemetry transmission and establish new MQTT subscriptions. The Kafka topic `telemetry-ingestion` receives burst traffic: 100,000 messages/second (vs. baseline 5,000 msg/s). Consumer groups for rules engine and analytics pipelines fall behind in processing.

### Failure Mode
- Consumer lag metric grows to 2M+ messages within 5 minutes
- Rules engine pipeline backs up, delaying time-sensitive device alerts by 30+ seconds
- Dashboard visualizations lag by 2-5 minutes instead of real-time
- Risk of message processing order inversion when catch-up occurs
- Memory exhaustion in consumer instances due to buffering

### Impact
- Real-time anomaly detection becomes reactive (alerts delayed)
- Device compliance checks fail to flag issues in time for corrective action
- SLA violations on alert response time (target: <5 seconds, actual: 90 seconds)
- Operational teams rely on stale data during critical firmware transitions
- Downstream applications timeout waiting for processing results

### Detection
- Kafka consumer lag metric exceeds 100,000 messages for >1 minute triggers PagerDuty P2 alert
- Dashboard widget shows consumer lag trend with 1-minute granularity
- Rules engine processing latency metric exceeds 10 seconds (vs. 100ms baseline)
- Kafka broker JMX metrics: `kafka.consumer:type=consumer-fetch-manager-metrics,client-id=*` shows `records-lag-max` spike
- Consumer group coordinator detects lag imbalance across partitions (standard deviation >25%)

### Mitigation
**Preventive Measures:**
- Pre-scale Kafka topic `telemetry-ingestion` to 32 partitions (from baseline 8) to distribute concurrent load
- Deploy consumer group `rules-engine` with 16 consumer instances pre-warmed (vs. 4 baseline), with CPU/memory headroom
- Implement client-side rate limiting on MQTT broker: devices connecting wait random 1-5 seconds (exponential backoff with jitter)
- Configure Kafka broker `num.network.threads=16`, `num.io.threads=16` for maximum throughput
- InfluxDB write buffer increased to 16MB per consumer thread
- Enable Kafka auto-scaling: metrics-based scaling rule triggers at consumer lag >50K, scales up by 4 instances (max 24)

**Real-Time Response:**
- Monitor PagerDuty alert and manually trigger Kubernetes HPA scaling for rules-engine deployment to 20 replicas within 90 seconds
- Activate "reduced-delay rules" mode: disable non-critical rules (e.g., trend analysis), keep only safety-critical rules (temperature, pressure alerts)
- Reduce InfluxDB batch write window from 10 seconds to 2 seconds (increases load but reduces memory buffering)
- Enable Kafka consumer pause-on-lag-threshold: temporarily pause low-priority consumer groups (analytics, historical aggregation) for 3 minutes

### Recovery
- Auto-scaling activates within 3 minutes of lag threshold breach (via Kubernetes metrics)
- Consumer lag drops below 10,000 messages within 10 minutes of full scaling
- Manually verify no messages dropped in Kafka (compare source device count vs. ingested message count)
- Check rules engine alert queue: validate all pending alerts were processed
- Dashboard refresh every 5 minutes to confirm real-time data flowing
- Post-incident: analyze device activation distribution, implement staggered re-connection batches (500 devices per 30-second window)

### SLA Target
- 99.9% of alerts delivered within 5 seconds of trigger, even during swarm events
- Alert delivery latency <15 seconds acceptable during fault window (alert still actionable)
- Platform fully recovered to baseline metrics within 15 minutes

---

## 2. InfluxDB Disk Exhaustion from Telemetry Burst

### Scenario Description
A fleet of 5,000 temperature/humidity sensors experiences firmware regression causing 10x message frequency increase: 10 messages/second per sensor (vs. 1 msg/s baseline). Combined with normal traffic from other 95,000 devices, InfluxDB receives 600,000 measurements/second instead of baseline 150,000. Over 6 hours, 8.6 TB of uncompressed data written, exhausting 10 TB available disk on InfluxDB cluster.

### Failure Mode
- InfluxDB disk utilization reaches 95% (9.5 TB used)
- Write operations rejected with "disk full" errors
- Series creation blocked (new sensors cannot register measurements)
- Query performance degrades from milliseconds to seconds as compaction blocks
- Backups fail, leaving cluster unprotected
- Risk of data corruption if disk fills completely (100%)

### Impact
- Incoming telemetry data for 5,000 devices discarded (no persistence)
- Retention policy queries fail, reporting gaps to dashboards
- Historical analytics (SLA calculations, trend analysis) incomplete
- Compliance audit logs missing data windows
- If unaddressed >1 hour: cascading failures to dependent systems (dashboards, alerting)

### Detection
- Disk usage metric >85% (8.5 TB) triggers warning alert (yellow), monitoring dashboard
- Disk usage >90% (9.0 TB) triggers critical alert, PagerDuty P1 escalation
- InfluxDB logs contain "write failed: disk full" messages
- Write rejection rate metric exceeds 1% (background metric task alert)
- S3 backup job fails with "insufficient disk space for temporary files"
- Grafana dashboard widget shows flat line for metric ingestion count (query timeouts)

### Mitigation
**Preventive Measures:**
- InfluxDB retention policies enforce 90-day automatic purge for standard metrics (31-day for verbose debug data)
- Write circuit breaker activates when disk >90%, rejects non-critical writes (debug/trace metrics discarded first)
- Implement compression ratio monitoring: alert if actual ratio drops below expected 10:1 (indicates data type change or anomaly)
- Auto-scaling: if disk trending to fill >80% in 2 hours at current rate, trigger EBS volume expansion via Lambda (add 5 TB to running instance)
- Disk space baseline: provision 50% headroom above peak forecasted usage (forecast 100K devices × 1KB/measurement × 86,400 sec/day = ~8.6 TB/month rolling window)
- Enable InfluxDB index compaction on 15-minute schedule vs. default 30 minutes

**Real-Time Response:**
- Identify root cause: investigate spike in message frequency using MQTT broker logs and device firmware version distribution
- Implement device-side recovery: push emergency firmware rollback OTA update to affected 5,000 sensors (rate-limited to 20 devices/second)
- Enable "data drop mode" in ingestion pipeline: accept messages but filter to 1-per-10 for affected sensor types until disk <80%
- Trigger emergency EBS volume expansion via AWS API: add 10 TB to running instance (operation visible, no downtime)
- Pause non-critical background jobs: batch aggregations, anomaly model retraining

### Recovery
1. Verify firmware rollback completion on 5,000 devices (query device telemetry for version field change)
2. InfluxDB write success rate returns to >99.9% within 30 minutes of mitigation start
3. Manual data compaction: run InfluxDB `COMPACT` command on affected retention policies (completes within 1-2 hours)
4. Disk cleanup: delete data >90 days old using retention policy force execution
5. Restore query performance: confirm query latency <100ms for standard dashboard panels
6. Increase InfluxDB disk limit reservation: update Kubernetes PersistentVolume to reflect new capacity
7. Post-incident review: implement device-side message rate limiting (max 2 msg/sec per device, configurable per device class)

### SLA Target
- Disk utilization stays <85% under normal peak load
- Automatic EBS expansion completes within 10 minutes (transparent to applications)
- Recovery from full mitigation to baseline telemetry collection: <30 minutes

---

## 3. MQTT Broker Failover During Active Device Communication

### Scenario Description
Primary MQTT broker (AWS IoT Core or HiveMQ cluster primary node) becomes unavailable during active device communication: primary instance loses network connectivity (security group misconfiguration) or crashes (OOM due to memory leak). 50,000 active devices subscribed to device twin shadow updates and publishing telemetry.

### Failure Mode
- All 50,000 client connections dropped simultaneously
- Inflight PUBLISH messages (QoS 1/2) unacknowledged and lost
- Device twin shadow syncs interrupted mid-operation
- Device state in cloud diverges from actual device state
- Clients attempt reconnection to same (now unavailable) primary endpoint
- Thundering herd: 50,000 reconnection attempts within 5 seconds

### Impact
- Device-to-cloud commands fail silently (no delivery confirmation)
- OTA update deployment stalls (devices don't receive update notification)
- Real-time sensor readings unavailable for 2-5 minutes
- Dashboard shows "offline" for all devices (operational visibility lost)
- If secondary failover misconfigured: devices remain disconnected until manual recovery

### Detection
- MQTT broker connection count drops >20% (from 50K to <40K) in 60 seconds triggers alert
- AWS CloudWatch alarm: IoT Core connection count threshold breach
- Device telemetry ingestion rate drops to zero for >30 seconds
- Client reconnection attempt spike: 10K+ new connection attempts in 10 seconds (detectable as spike in `CONNECT` frame rate)
- TLS handshake failures accumulate in logs (clients trying old primary endpoint)

### Mitigation
**Preventive Measures:**
- Deploy MQTT broker in HA configuration: 3-node HiveMQ cluster across 3 AZs (AWS IoT Core fully managed, no primary/replica)
- Devices configured with DNS CNAME pointing to load balancer (not fixed IP), load balancer distributes across 3 nodes
- Devices implement exponential backoff with jitter on reconnect: retry intervals [1s, 2s, 4s, 8s, 16s, 32s, 60s, 60s, ...] capped at 300 seconds
- MQTT keep-alive set to 60 seconds: server pings idle clients, client detects broker disconnection within 60 seconds
- Device SDK includes automatic reconnection with TLS certificate validation
- Primary/secondary broker configuration deprecated in favor of load-balanced cluster endpoint

**Real-Time Response:**
- Load balancer health check detects broker failure within 10 seconds, removes failed node
- Remaining 2 broker nodes accept new connections, clients reconnect to secondary endpoints
- Rate-limiting on MQTT broker: limit concurrent connections per device ID to prevent storms (max 2 simultaneous)
- Reduce QoS requirement during failover: downstream systems accept QoS 0 (at-least-once guarantee temporarily relaxed)
- Alert operations: "MQTT broker degraded to 2/3 nodes, auto-recovery in progress"

### Recovery
1. Devices reconnect within 60-300 seconds depending on backoff jitter
2. Monitor reconnection rate: should see 1K+ connections/second until all 50K recovered (<5 minutes)
3. Verify inflight message recovery: compare message timestamps in Kafka vs. device last-sync time
4. For dropped commands: operations team re-sends critical commands (OTA, config updates)
5. Device shadow reconciliation: client re-syncs shadow state on reconnection (compares local vs. cloud, resolves conflicts)
6. Investigate broker failure root cause: check memory usage, network connectivity, disk space on failed node
7. Restart failed broker node (or replace if persistent failure)
8. Post-incident: analyze which devices took longest to reconnect, verify exponential backoff working correctly

### SLA Target
- MQTT broker failover completed within 60 seconds (client-side detection + reconnect)
- 90% of disconnected devices reconnected within 5 minutes
- No data loss for QoS 2 messages (guaranteed delivery via persistent message store)

---

## 4. Certificate Authority Rotation Affecting All Provisioned Devices

### Scenario Description
Platform-wide CA (Certificate Authority) rotation required every 2 years due to security policy. Current CA expires in 30 days. All 100,000 provisioned devices hold certificates signed by current CA. New CA generated, new device certificates issued. Staggered rollout plan: update CA trust bundle via OTA update, then devices validate both old and new CA signatures for 90-day overlap period.

### Failure Mode
- OTA update deployment initiated, 100,000 devices begin downloading new CA bundle (1.5 MB each)
- Device firmware has bug: new CA bundle not properly merged with old CA, overwrites entire trust store
- 20% of devices (20,000) reject TLS connections after update: "certificate chain validation failed"
- Devices cannot connect to MQTT broker (presents certificate signed by old CA still in rotation)
- No recovery mechanism: devices locked out, require manual USB JTAG reflash

### Impact
- 20,000 devices permanently offline until technician re-flashes firmware
- Production monitoring blind for affected sites (20% of fleet)
- OTA update rollout halted, remaining 80,000 devices stuck on old firmware
- Field service dispatch costs: 10,000+ technician visits estimated
- SLA violations across all connected customers

### Detection
- Device authentication failure count spikes post-OTA update: logs show "TLS_ALERT_BAD_CERTIFICATE" for 20K client IPs
- Device heartbeat failure count exceeds 5% (threshold for update health check)
- Automated canary test: pilot 100 devices with update first, monitor authentication success rate
- Certificate validation error metrics: alert if >1% of devices fail TLS handshake in 10-minute window

### Mitigation
**Preventive Measures:**
- Implement dual-CA trust period: both old and new CA certificates loaded into device trust store simultaneously
- Phased rollout: update only 5% of devices (5,000) in first week, monitor for 7 days, then 25%, then 100%
- Canary deployment: test CA bundle update on 100 devices in controlled lab environment before production rollout
- Firmware pre-staging: new firmware with merged CA support tested and staged 2 weeks before CA rotation deadline
- Device re-provisioning option available: force device into provisioning mode (via MQTT command) to receive fresh certificate signed by new CA
- Update package signature verification: device cryptographically validates OTA update integrity before applying

**Real-Time Response:**
- Pause OTA rollout immediately upon 5% device failure threshold
- Investigate failed device logs: extract error details (which CA chain failed, timestamp of failure)
- Identify root cause: firmware bug or CA bundle corruption
- Push hotfix OTA update with corrected CA merge logic (signed by old CA so devices can still receive it)
- Offer manual recovery: guide affected devices to re-provisioning mode, re-issue certificates
- Implement MQTT-based CA update: smaller payload (100 KB), can retry on failure, more defensive parsing

### Recovery
1. Identify devices stuck with invalid CA trust store (query MQTT auth failure logs for device IDs)
2. Send "factory reset" MQTT command to trigger device re-provisioning
3. Devices enter provisioning mode: accept temporary self-signed cert for re-provisioning MQTT topic
4. Re-issue certificates with dual-CA support (new firmware compiled into device)
5. Resume OTA rollout with fixed firmware package to remaining devices
6. Verify all 100,000 devices reconnected with valid TLS chains within 48 hours
7. Manual remediation: for permanently bricked devices, arrange field technician reflash (estimated 2-3 weeks)

### SLA Target
- CA rotation process completes within 4-week window without production downtime >1 hour
- Zero permanent device bricking in production (all recovery paths automated or easily manual)
- 99% of devices successfully updated within 2-week rollout phase

---

## 5. Mass Device Re-Provisioning After Security Incident

### Scenario Description
Security incident discovered: unauthorized third party gained access to device private key material stored in company cloud account (unencrypted S3 bucket). Private keys for 100,000 devices exposed. All device certificates must be revoked immediately and new certificates issued. Platform policy: 48-hour SLA for all devices to hold valid new certificates.

### Failure Mode
- Revocation list (CRL) updated immediately, old certificates marked invalid
- Some IoT Core instances reject connections from revoked certificate holders
- Provisioning service API overloaded with re-provisioning requests (100,000 requests in 2-hour window)
- Provisioning service response time degrades: <1 second baseline becomes 30+ seconds
- Some devices give up re-provisioning, remain offline
- Regional failover needed: re-provisioning traffic skews toward secondary region
- Provisioning database connection pool exhausted

### Impact
- 100,000 devices potentially offline until re-provisioned
- OTA updates cannot be deployed (cannot verify device identity)
- Business operations halted (manufacturing floor, logistics, sensor networks all blind)
- Cascading failures: dashboards timeout, alerting systems fail (no device telemetry)
- Regulatory incident response required: customers notified, audit trail preserved

### Detection
- Security incident triggers automated playbook: revoke all device certificates + alert executive team
- Device authentication failure rate spikes to 100% (all old certs rejected)
- Provisioning API response time exceeds 10 seconds (alert threshold)
- Provisioning service error rate exceeds 5% (database connection pool exhaustion)
- Device offline count rises to 100,000 within 5 minutes of CRL update

### Mitigation
**Preventive Measures:**
- Device certificate rotation schedule: all certificates rotated every 1 year (vs. 3-year baseline) to reduce blast radius if compromise occurs
- Revocation mechanism in place: OCSP responder (not just CRL) for real-time revocation status queries
- Private key material encrypted at rest in S3 (AES-256, key in AWS KMS)
- Provisioning service auto-scaling configured: baseline 4 instances, auto-scale to 32 instances if request rate >1K req/sec
- Provisioning database: read replicas for load distribution, connection pool size 500 (from baseline 100)
- Device re-provisioning circuit breaker: if provisioning service fails, device falls back to last-known-good certificate for temporary use (24-hour validity extension)

**Real-Time Response:**
1. Immediately disable old certificate validation in IoT Core (accept revoked certificates for 1 hour to allow graceful offline period)
2. Trigger prioritized re-provisioning by device class: Tier 1 (safety-critical, production machinery) first, Tier 2 (non-critical sensors) second
3. Manual scaling: increase provisioning service instances to 24 immediately (via Kubernetes kubectl scale)
4. Increase provisioning database connection pool to 1000
5. Rate-limit re-provisioning requests: max 50K devices/hour to avoid overwhelming database
6. Implement expedited re-provisioning flow: skip background checks, use pre-authorized signing keys (vs. normal multi-signature approval)
7. Activate "emergency mode": provisioning service returns cached certificates if database unavailable (trades security for availability)

### Recovery
1. **Hour 0-4 (Tier 1):** 25,000 safety-critical devices re-provisioned with new certs, validated against manufacturing requirements
2. **Hour 4-12 (Tier 2):** 50,000 standard production devices re-provisioned
3. **Hour 12-24 (Tier 3):** 25,000 non-critical monitoring devices re-provisioned
4. Verify all 100,000 devices reconnected and authenticated with new certificates by 48-hour mark
5. Cross-check device registries: ensure no devices missed in re-provisioning
6. Post-incident forensics: audit all provisioning requests (log every device cert issuance)
7. Root cause analysis: identify how S3 bucket became unencrypted, implement encryption enforcement policy
8. Incident report: timeline, impact assessment, preventive measures taken

### SLA Target
- 48-hour 100% device re-provisioning SLA enforced contractually
- 24-hour Tier 1 (critical) devices re-provisioned, production operations resume
- Zero devices permanently locked out (re-provisioning circuit breaker ensures temporary connectivity)

---

## 6. Telemetry Data Backfill After Prolonged Platform Outage

### Scenario Description
Platform experiences 6-hour outage due to database migration failure. Cloud MQTT broker and telemetry ingestion offline. Edge devices with onboard storage continue collecting measurements locally. When platform recovers, devices flush buffered telemetry: 10,000 devices × 6 hours × 60 measurements/hour = 3.6M messages accumulated, plus normal real-time traffic (5,000 msg/sec).

### Failure Mode
- Ingestion throughput jumps from 5,000 msg/sec to 25,000 msg/sec suddenly
- Kafka partition rebalancing under load, consumer group lag spikes
- InfluxDB write buffer overflows, causing delayed writes or message drops
- Backfill messages timestamped 6 hours old, arrive after current real-time data (out-of-order)
- InfluxDB out-of-order insertion performance penalty: write latency increases 10x
- Memory pressure on consumer instances buffering old messages
- Dashboard queries hang querying data being written in real-time

### Impact
- Backfill ingestion takes 12+ hours instead of estimated 2-3 hours
- Real-time alerting delayed by 5+ minutes (consumer lag behind real-time data)
- 6-hour telemetry data gap in InfluxDB (data from 6 hours ago to recovery time)
- Regulatory compliance concern: missing data window in audit trail
- Business KPIs (OEE, availability) incomplete for 18-hour period

### Detection
- Message age metric shows timestamps from 6 hours ago (alert on max_message_age > 1 hour)
- Kafka consumer lag spikes >500K messages, stays elevated for >30 minutes
- InfluxDB write latency exceeds 1 second (baseline 10ms)
- Ingestion throughput spike: >20K msg/sec detected
- Backfill message count trend shows slow decrease (linear decrease over 12+ hours vs. exponential)

### Mitigation
**Preventive Measures:**
- Rate-limited backfill: ingestion pipeline configured to process max 10K msg/sec per device group during backfill mode
- Priority queue for messages: current real-time messages given priority over backfill
- InfluxDB configuration: write deduplication window = 5 seconds (allows re-ordered messages from same device without conflict)
- Kafka topic partitioning strategy: backfill topic separate from real-time topic, deduplicated downstream
- Consumer group scaling: automatic 2x scaling triggered when message backlog detected
- Edge device storage: 24-hour storage capacity (not just 6 hours), allows gradual backfill

**Real-Time Response:**
1. Activate backfill mode in ingestion pipeline: separate consumer group for backfill messages
2. Route backfill messages to separate Kafka topic (`telemetry-backfill`) with 8 partitions (vs. 32 for real-time)
3. Auto-scale backfill consumer group to 8 instances (ingests 10K msg/sec max rate)
4. Real-time consumer group stays at baseline (4 instances), handles 5K msg/sec fresh data
5. Reduce InfluxDB write batch window from 10 seconds to 2 seconds (backfill producer writes smaller batches, reduces memory)
6. Pause non-critical dashboard refreshes: set to 5-minute interval vs. 10-second baseline
7. Alert operations: "Backfill in progress, real-time data may lag 5 minutes"

### Recovery
1. Backfill message count reduces linearly: monitor progress (estimate 10K msg/sec ÷ 3.6M messages = 360 seconds = 6 minutes to completion)
2. All backfill messages ingested into InfluxDB within 2x outage duration (12 hours total, completes 18 hours post-recovery)
3. Verify InfluxDB data integrity: query data from outage window, confirm message counts match device reports
4. Real-time ingestion returns to <5-second latency
5. Scale down backfill consumer group, merge with real-time group
6. Reintegrate backfill and real-time topics: deduplicate messages by (device_id, timestamp, metric_name)
7. Verify dashboard queries: data from outage window now available and queryable

### SLA Target
- Platform backfill completes within 2x outage duration (6-hour outage = 12-hour backfill window)
- Zero backfill data loss (all locally buffered messages successfully ingested)
- Real-time latency <10 seconds during backfill period (acceptable degradation)

---

## 7. Rules Engine Processing Backlog During Alert Storm

### Scenario Description
Abnormal environmental event (heat wave / temperature surge across region) causes widespread threshold violations. 80% of temperature sensor fleet (64,000 sensors) exceeds alert threshold. All sensors generate alert events simultaneously. Rules engine baseline: 10K events/minute processing. Alert storm: 500K events/minute (50x normal rate).

### Failure Mode
- Rules engine queue depth grows exponentially: 1M+ pending events within 3 minutes
- Alert deduplication fails: same device, same rule, multiple identical alerts generated
- Alert notification system overwhelmed: sends 500K+ notifications/minute instead of baseline 10K
- Email/SMS gateway overloaded, notifications delayed or dropped
- On-call team receives flood of identical alerts (notification system inbox unusable)
- Alert fatigue: operators ignore legitimate critical alerts buried in noise
- Memory exhaustion in rules engine: buffer pools depleted by queued events

### Impact
- Legitimate critical alerts lost in noise (alert delivery SLA violated)
- Operations team unable to respond effectively (information overload)
- Escalation path unclear: which alerts are truly critical vs. related noise?
- If temperature event indicates actual hazard: delayed response, safety risk
- False positive alerts reduce team confidence in platform (cry-wolf effect)

### Detection
- Alert volume metric spikes to >100K alerts/minute (alert threshold)
- Rules engine queue depth exceeds 100K messages in 2 minutes
- Alert deduplication cache hit rate drops to <5% (normally >80%)
- Notification system queue length exceeds 100K
- Email/SMS provider rate-limit error responses
- Grafana dashboard alert count widget shows >10x spike from baseline

### Mitigation
**Preventive Measures:**
- Alert deduplication window: same device + same rule + same timestamp (±5 min window) = single alert (de-duplicate at ingestion)
- Rules engine circuit breaker: if queue depth >50K, pause non-critical rules (trend analysis, prediction) and process only safety-critical rules (temp/pressure/current limits)
- Alert correlation: multiple temperature alerts from same facility correlated into facility-level alert vs. per-device alerts
- Notification deduplication: alert system deduplicates notifications to same recipient for identical alert type within 5 minutes
- Rules engine scaling: baseline 4 instances, auto-scale to 16 instances if event rate >200K events/min
- Sampling mode: if queue >500K events, sample events at 50% rate (every 2nd event processed)

**Real-Time Response:**
1. Monitor detects alert rate >100K/min, activates alert storm mitigation
2. Circuit breaker enabled: disable non-critical rules (anomaly detection, trend analysis)
3. Alert deduplication window activated: correlate multiple device alerts into facility-level alert
4. Rules engine auto-scaling triggered: provision 12 additional instances (16 total)
5. Notification system rate-limiting: max 1K notifications/second, queue excess for delivery after storm subsides
6. On-call notification: "Alert storm detected - heat wave event affecting facility ABC. Processing correlated alerts. Ignore duplicate device-level alerts, monitor facility-level alert."
7. Dashboard update: show aggregated alert count (64,000 devices affected) vs. individual device alerts

### Recovery
1. Temperature event subsides (actual weather improves or monitoring equipment failure identified)
2. Alert rate drops back to normal levels within 30 minutes of event peak
3. Disable circuit breaker: re-enable all rules
4. Scale down rules engine: return to baseline 4 instances
5. Post-incident analysis: determine root cause (actual heat wave vs. sensor malfunction)
6. Implement sensor-level alert hysteresis: device must exceed threshold for 5 minutes before alerting (prevents fluctuation-induced noise)
7. Improve alert correlation heuristics: facility-level alerts group 5+ devices with same symptom

### SLA Target
- Alert processing latency <30 seconds even during 50x load spike (alerts delivered, no loss)
- Alert deduplication reduces notification volume by >90% during correlated events
- Operations team receives <100 actionable alerts during storm (manageable for human review)

---

## 8. Time-Series Data Retention Policy Execution Causing Query Failures

### Scenario Description
InfluxDB retention policy automatically purges data older than 90 days. Execution scheduled for 2 AM UTC, runs monthly. On 1st of month, active dashboards query 90-day trend data (e.g., "show temperature trends over last quarter"). Users trigger dashboard refresh at 2:15 AM (just after policy execution). Deletion operates on same data ranges as active queries.

### Failure Mode
- Retention policy deletes data for time range [Jan 1 - Apr 1]
- Dashboard query requests data [Jan 1 - Apr 1] concurrently
- InfluxDB query execution plan designed for full data range
- Database attempts to read deleted blocks, query fails mid-execution
- Query returns partial results or error: "shard not found" or "data gap"
- Dashboard widget fails to render (no data), shows error state
- Downstream analysis tools (Grafana alerting) receive incomplete data, threshold calculations wrong

### Impact
- 5-10% of active dashboard queries fail during retention window
- Business reports generated during retention window show missing data (compliance issue)
- Analytics jobs scheduled near retention window fail or produce incomplete results
- User experience degradation: dashboards show errors for 15-30 minutes during execution

### Detection
- Dashboard query error rate metric spikes during retention policy execution window (2-4 AM)
- InfluxDB logs contain "shard not found" errors during execution window
- Query latency spikes: queries that normally complete in 100ms take 5+ seconds (or timeout)
- Alerting system fails to compute aggregates during window: alert thresholds not evaluated
- Retention policy execution duration logs show longer-than-normal runtime (indicates query locks)

### Mitigation
**Preventive Measures:**
- Schedule retention policy execution at 2-4 AM Sunday UTC (lowest traffic window, <1% of queries active)
- Lock affected time ranges during deletion: set read-only flag on shards being deleted for 30 seconds
- Query routing: redirect queries requesting deleted data ranges to read-only replica (eventual consistency acceptable)
- Implement query time range validation: if query requests time range older than retention policy allows, return empty result set (not error)
- Retention policy split: delete data in smaller batches (1-week chunks vs. 90-day all at once) over 2-hour window
- Advance notice: application clients cache 90-day trend data before policy execution

**Real-Time Response:**
1. Retention policy execution detected, retention lock enabled
2. New queries requesting data being deleted are queued (not rejected)
3. Continue serving queries from read replicas where possible
4. Dashboard auto-refresh paused during policy window (set "retry" mode)
5. Queries are retried after retention execution completes (180-second timeout)
6. Operations notification: "Maintenance window in progress, some queries may be slower"

### Recovery
1. Retention policy execution completes (typically 30-45 minutes)
2. Read-only lock released, shards available again
3. Retry all queued queries, queries resume normal latency (<100ms)
4. Dashboard widgets re-render with data
5. Alert threshold calculations resume, alerts trigger normally
6. Post-incident: audit all reports generated during window, re-run if critical business impact
7. Long-term: move retention policy to dedicated low-traffic window (off-peak hours per regional timezone)

### SLA Target
- Retention policy execution transparent to end users (no visible query failures)
- Query latency increase <200ms during policy execution window (acceptable degradation)
- 99.9% of dashboard queries succeed, even during retention maintenance

---

## 9. Edge Gateway Network Partition — Devices Isolated from Cloud

### Scenario Description
Factory facility with 10,000 edge-connected devices (IoT gateway running AWS Greengrass). Network link to cloud fails: internet connection dropped (ISP outage, firewall misconfiguration, BGP hijack). Gateway continues running, edge devices continue local operation. Cloud has no visibility into edge operations for 4 hours.

### Failure Mode
- All devices become "offline" in cloud dashboard (but locally operational)
- MQTT connections closed (can't reach cloud broker)
- Telemetry/events not forwarded to cloud
- Alerts generated at edge are not forwarded to cloud monitoring system
- Configuration changes pushed from cloud not received at edge
- OTA updates cannot be deployed
- Edge data buffering system fills with 4 hours of queued messages

### Impact
- Cloud-based monitoring/alerting blind to edge operations
- No telemetry for SLA calculations, compliance reporting missing data
- If safety incident occurs at edge (high temperature, pressure alarm), no cloud notification
- Operations team relies on manual plant floor checks (no remote visibility)
- Alerts generated at edge (safety-critical) stuck in edge queue, not escalated

### Detection
- Gateway heartbeat lost: last_heartbeat timestamp >5 minutes old
- Gateway last_message_timestamp stale >5 minutes (triggers PagerDuty alert)
- AWS IoT Greengrass device connectivity metric drops to "offline"
- Telemetry ingestion count drops to zero
- Gateway local buffering level trending toward capacity (e.g., disk usage rising)
- Network outage detected by gateway (no DNS resolution, NTP sync failure)

### Mitigation
**Preventive Measures:**
- AWS Greengrass Lambda functions run locally: temperature threshold alerts, pressure limits evaluated at edge without cloud dependency
- Local storage/historian: gateway buffers up to 24 hours of telemetry locally (SSD storage)
- Dual internet connectivity: factory has primary (fiber) + secondary (LTE/4G) uplinks with automatic failover
- Network resilience: gateway caches last 1000 configuration items, continues operating with stale config during outage
- Local alerting: buzzer/LED on gateway for critical edge alerts (audible if network down)
- Edge rules engine: subset of critical rules (safety limits) always run locally, don't depend on cloud

**Real-Time Response:**
1. Network partition detected by gateway: local Greengrass health check fails to reach cloud
2. Greengrass enters "offline mode": local Lambda functions activated
3. Edge rules engine evaluates all critical safety rules locally (temperature, pressure, current limits)
4. Alert generation at edge: if threshold breached, stored locally and marked "alert pending cloud delivery"
5. Local historian buffers all incoming telemetry to SSD (timestamp, device_id, measurement)
6. Initiate failover to secondary network: LTE module activated, route traffic to 4G cloud endpoint
7. Facility operations notified: "Local monitoring active, cloud visibility degraded"

### Recovery
1. Network connectivity restored (ISP issue resolved, LTE connects)
2. Gateway establishes cloud connection, begins uploading buffered data
3. Cloud receives 4 hours of buffered telemetry (10,000 devices × 4 hours × 60 msg/min = 2.4M messages)
4. Backfill mechanism (see Scenario 6) activated: rate-limit to 10K msg/sec to avoid overwhelming cloud
5. Verify alert queue: replay edge-generated alerts to cloud alerting system
6. Dashboard updates: cloud operators see edge operational data (with 4-hour delay markers)
7. Reconcile edge state vs. cloud state: identify any discrepancies (e.g., edge processed config update that failed to sync)

### SLA Target
- Edge operations continue with zero impact during network partition (local rules engine autonomous)
- Zero data loss: all edge-generated telemetry buffered and delivered post-recovery
- Failover to secondary network completes within 5 minutes of primary failure
- 99% of edge-generated alerts successfully queued and delivered within 1 hour of cloud reconnection

---

## 10. Firmware OTA Update Failure — Device Bricked State

### Scenario Description
Firmware OTA update pushed to 100,000 production devices. Update package checksums verified before signing (SHA-256). Package uploaded to S3. During S3 upload, bit error occurs (cosmic ray, storage controller error), corrupting 8 bytes of firmware binary. S3 checksum verification passes (mismatch not detected due to bug in comparison logic). Devices begin downloading firmware package.

### Failure Mode
- 500 devices download firmware before package replaced in S3
- Firmware binary corrupted (8 bytes flipped in bootloader)
- Device applies OTA update: verification passes (signature trusted), installation proceeds
- Bootloader corrupted: device cannot load kernel, stuck in bootloop
- Device no longer boots, no recovery mechanism
- Device is "bricked": requires physical USB/JTAG connection to recover

### Impact
- 500 devices permanently non-functional until field technician intervention
- Replacement hardware required if device not recoverable (cost: $500/device = $250K)
- Production operations interrupted (if critical manufacturing devices affected)
- Regulatory incident: safety-critical devices rendered inoperable
- Brand reputation damage (customer confidence in OTA safety)

### Detection
- Device heartbeat missing for >30 minutes post-update (device not starting)
- Device logs show "boot failed" in first 30 seconds of OTA process
- Failed OTA update count exceeds 1% threshold (500 out of 100K devices)
- S3 object integrity check: separate integrity verification service detects hash mismatch on random sampling (1% of objects)
- Device telemetry ingestion drops for affected batch (devices not sending heartbeat post-update)

### Mitigation
**Preventive Measures:**
- A/B partition scheme: device boots from partition A or B, firmware update always written to inactive partition
- Automatic rollback: if device fails to boot after 5 minutes, automatically revert to previous firmware partition
- Secure boot: firmware signature verified at boot time (not just OTA upload), corrupted firmware rejected before execution
- Hash verification: device compares S3 object ETag (from multiple S3 read requests, different AWS API calls) before applying firmware
- Pre-release validation: OTA update tested on 1% of fleet (1,000 devices) for 24 hours before full rollout
- Staged rollout: push update to 10%, wait 1 hour for any failures, then 50%, then 100%

**Real-Time Response:**
1. Failed OTA count exceeds 1% threshold, auto-rollback triggered for all devices
2. Devices revert to previous firmware partition automatically within 5 minutes
3. S3 integrity check detects hash mismatch, object removed from distribution
4. Device telemetry flow resumes: devices reconnected with previous firmware
5. Investigation: reproduce issue, identify corruption source (S3 bit error, package builder bug)
6. Corrected firmware package generated, validated with 100% hash verification
7. Device that downloaded corrupted package: push emergency repair MQTT command (factory reset)

### Recovery
1. All 500 devices auto-rollback to previous firmware within 5 minutes
2. Devices reconnect to cloud, resume telemetry transmission
3. Corrupted firmware package quarantined in S3, never redistributed
4. New firmware package tested on canary fleet (100 devices, 24-hour validation)
5. Staged rollout of corrected firmware: 10% → 50% → 100% with monitoring
6. For any devices not auto-recovered: manual field service JTAG reflash (estimated 2-3 weeks for all 500)
7. Post-incident: improve OTA validation, implement hardware-level rollback assist (hardware write-protect boot partition after verification)

### SLA Target
- Zero devices permanently bricked due to firmware update (all recovery paths automated)
- Failed OTA detection and auto-recovery completes within 5 minutes
- Firmware update rollback successful for 99.9% of devices

---

## SLA Summary Table

| Scenario | Detection Time | Mitigation Time | Recovery Time | Availability Impact | Data Loss Risk |
|----------|---|---|---|---|---|
| Kafka Consumer Lag | 2 min | 3 min | 10 min | <30 sec latency | None |
| InfluxDB Disk Exhaustion | 5 min | 15 min | 30 min | Writes blocked | <1% telemetry |
| MQTT Broker Failover | 1 min | <1 min | 5 min | 5 min reconnect | QoS2 safe, QoS1 risky |
| CA Rotation | N/A | 48 hours | 72 hours | Staggered impact | None |
| Mass Re-Provisioning | Immediate | 1 hour | 48 hours | Full outage | None (async) |
| Backfill After Outage | Immediate | <5 min | 12 hours | 5+ min latency | None |
| Alert Storm | 2 min | 5 min | 30 min | Alert latency | None (queued) |
| Retention Failure | 5 min | <1 min | 45 min | Query errors | None (queued) |
| Network Partition | <1 min | <5 min | 4 hours | Edge autonomous | None (buffered) |
| Firmware OTA Failure | 3 min | <5 min | 5 min | Device offline | None (rollback) |

---

## Escalation Matrix

| Severity | Detection Method | 1st Alert | 2nd Level | Executive | SLA |
|----------|---|---|---|---|---|
| P1 (Outage) | Metrics spike | PagerDuty on-call | Team lead | VP Eng | <5 min response |
| P2 (Degradation) | Dashboard warning | PagerDuty | On-call engineer | Engineering lead | <15 min response |
| P3 (Maintenance) | Background alert | Email | Business hours team | None | Next business day |

---

**Document Version:** 1.0  
**Last Updated:** 2024  
**Owner:** Platform Operations Team  
**Review Cycle:** Quarterly
