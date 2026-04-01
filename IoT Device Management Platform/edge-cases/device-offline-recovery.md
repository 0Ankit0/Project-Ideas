# Edge Cases: Device Offline and Recovery

This document catalogs edge cases that arise when IoT devices lose connectivity for extended periods and subsequently reconnect to the platform. Offline scenarios are among the most complex operational challenges in IoT platforms because they combine time-based state divergence, buffered data consistency, credential expiry, and reconciliation requirements across multiple subsystems.

---

## Device Offline for Extended Period With Massive Telemetry Backlog on Reconnect

**Scenario**

A remote agricultural soil sensor is deployed in a location with intermittent connectivity. After a 12-day network outage, the device reconnects with 86,400 locally buffered telemetry readings that it begins uploading immediately—roughly one reading per minute for 12 days. The device publishes all messages as rapidly as the MQTT connection allows.

**Detection**

The platform detects a reconnect event via the MQTT broker connection callback. The Device Registry is updated with a new `lastConnectedAt` timestamp. The ingestion pipeline observes an anomalous per-device message rate that far exceeds the device's normal telemetry frequency. The rate limiter in the Message Router flags the device as a high-volume reconnect burst.

**Handling**

1. The ingestion pipeline's per-device rate limiter activates for the reconnecting device, applying a configurable ingestion quota (e.g., 10 messages/second for standard devices, overridable for known backlog-capable devices).
2. Messages exceeding the quota are not dropped but are placed in a priority-reduced queue with a higher processing latency, ensuring other devices' telemetry is not starved.
3. The device SDK is expected to implement cooperative backlog uploads: it publishes batches with a configurable inter-batch delay and respects MQTT PUBACK flow control (outstanding unacknowledged messages are limited by the `receiveMaximum` negotiated in the CONNECT packet).
4. The time-series database writer detects that the incoming messages have historical timestamps (many days in the past) and tags them with a `backfill: true` metadata flag.
5. Backfilled data is stored with its original device-reported timestamp rather than the server-side ingestion timestamp, preserving temporal accuracy for historical analysis.

**Prevention**

Devices should be configured with a maximum local buffer size that prevents unbounded storage consumption during extended offline periods. When the buffer is full, the device applies a configurable eviction policy: drop oldest (default for non-critical sensors), drop newest (for devices where recent data is irrelevant without historical context), or block new readings (for critical sensors where data loss is unacceptable).

---

## Device Clock Skew Causing Out-of-Order Telemetry Timestamps

**Scenario**

A device without a real-time clock module uses an estimated timestamp based on uptime since last boot. After a power cycle during a 3-day offline period, the device's clock is reset to a default epoch value (1970-01-01) until it can synchronize via NTP. The device publishes telemetry with timestamps in 1970, which are ingested and written to the time-series database, corrupting historical queries and dashboards.

**Detection**

The ingestion pipeline's Enrichment Processor validates incoming message timestamps against a configurable reasonable range: messages with timestamps more than 24 hours in the past (excluding known backfill scenarios) or any timestamp in the future (relative to server time) are flagged as having suspect clock skew. A message timestamped before the device's provisioning date is definitively invalid.

**Handling**

1. Messages with suspect timestamps are tagged with `clockSkew: true` and the server-side ingestion timestamp is stored alongside the device-reported timestamp.
2. The device-reported timestamp is preserved as `deviceTimestamp` and the server-side timestamp is stored as `serverTimestamp`, allowing both values to be queried.
3. For dashboards and queries by default, the server-side timestamp is used when `deviceTimestamp` is flagged as suspect.
4. The platform sends a configuration command to the device with the current server UTC time and instructs the device to synchronize its clock. Subsequent messages should have accurate timestamps.
5. An alert is raised if a device consistently publishes clock-skewed messages over multiple sessions, which may indicate a hardware RTC failure requiring field service.

**Prevention**

Device firmware should integrate NTP synchronization as an early step in the post-connection initialization sequence, before beginning telemetry publishing. The device SDK provides a `syncClock()` method that performs NTP synchronization and waits for a successful response before returning. Devices should store the last known good time in non-volatile memory so that a power cycle during a period of connectivity loss results in a reasonably accurate estimated time rather than a default epoch reset.

---

## Device Reconnects With Stale Cached Credentials (Certificate Expired While Offline)

**Scenario**

A device has been offline for 13 months. Its X.509 device certificate had a 12-month validity period and expired 1 month ago while the device was offline. When the device reconnects, the MQTT broker rejects the TLS handshake because the certificate has expired. The device cannot communicate with the platform and cannot receive a new certificate through its normal channel.

**Detection**

The MQTT broker logs a TLS handshake failure with reason `CERTIFICATE_EXPIRED` for the device's connection attempt. The broker publishes a connection failure event to the platform's security event stream, which is consumed by the Device Registry. The Device Registry updates the device's connectivity status to `ConnectionFailed: CertificateExpired`.

**Handling**

1. The Device Registry queries for all devices whose certificates are within 30 days of expiry (or already expired) on a scheduled basis and initiates proactive renewal.
2. For devices that are already offline with expired certificates, the renewal notification cannot be delivered through the normal MQTT channel.
3. If the device supports an out-of-band certificate renewal mechanism (e.g., a dedicated lightweight bootstrap channel or a certificate renewal API reachable without client certificate authentication), the platform delivers a renewal token via that channel.
4. The bootstrap channel uses short-lived (1-hour TTL) renewal tokens tied to the device's last known certificate fingerprint. The device presents its expired certificate + token, and the platform verifies the token and issues a new certificate.
5. The Device Registry notifies the operator for any device that has no out-of-band renewal path and requires manual intervention.

**Prevention**

The platform implements a certificate expiry monitoring job that runs daily, identifying all device certificates expiring within a configurable lead time (default: 60 days). Renewal notifications are sent to online devices well before expiry. For devices that come online within the 30-day pre-expiry window, renewal is triggered automatically. Certificate validity periods should be set to at least 24 months for device certificates, reducing the risk of expiry during extended offline periods.

---

## Network Partition: Device Thinks It Is Connected but Messages Are Silently Dropped

**Scenario**

A device maintains an active TCP connection to the MQTT broker, but a misconfigured network device (a stateful firewall) silently drops packets in one direction after the connection has been idle for 30 minutes. The device's TCP stack believes the connection is active (no RST received), and the device continues publishing telemetry—but no messages reach the broker. The device does not detect the issue because the TCP connection appears open.

**Detection**

MQTT keep-alive packets (PINGREQ/PINGRESP) detect network partitions that silently drop packets. When the device sends a PINGREQ and does not receive a PINGRESP within the keep-alive timeout, the MQTT client library closes the connection and attempts reconnection.

On the platform side, the Device Registry detects the issue when the device's last telemetry timestamp is significantly older than expected given the device's keep-alive interval plus a tolerance window. This triggers a `PossiblePartition` status flag.

**Handling**

1. The MQTT client library on the device is configured with a keep-alive interval of 60 seconds and a keep-alive timeout of 1.5× the keep-alive interval (90 seconds). This means a network partition is detected within 90 seconds under normal conditions.
2. The device closes the broken TCP connection, performs exponential backoff reconnection, and re-establishes the MQTT session (Clean Start: false for session resumption).
3. Messages published during the partition period at QoS 1 or QoS 2 are either resent (if still in the device's outbound buffer) or lost (if the buffer was overwritten by newer messages). The device's outbound buffer size and eviction policy determine how much data can be recovered after reconnection.
4. The platform reconciles the telemetry gap by requesting that the device upload its local buffer (if the device supports buffered telemetry upload) for the estimated partition period.

**Prevention**

Network infrastructure should be configured with appropriate TCP keepalive settings to prevent stateful firewall sessions from silently expiring active connections. Device deployments in environments with known stateful firewall issues should use a shorter MQTT keep-alive interval (30 seconds) to detect partitions faster, at the cost of slightly higher control plane traffic.

---

## Device Reconnects After Firmware Update Without Platform Knowledge (Version Mismatch)

**Scenario**

A device is manually updated by a field technician using a USB cable to load a firmware version not tracked in the platform. When the device reconnects, it reports firmware version 5.1.0-custom, but the platform's Device Registry shows the device's last known firmware version as 4.9.2. The platform has no deployment record for this version transition, creating an untracked state.

**Detection**

On reconnection, the device publishes its current firmware version, hardware revision, and configuration checksum in its hello payload. The Device Registry compares the reported firmware version against the last known firmware version. A discrepancy without a corresponding deployment record is flagged as an `UnmanagedFirmwareUpdate` event.

**Handling**

1. The Device Registry records the new firmware version as the device's current version, overwriting the last known version.
2. The `UnmanagedFirmwareUpdate` event is published to the audit trail and the security event stream.
3. An operator alert is raised informing the device group's owner that a device's firmware was updated outside the managed deployment process.
4. The platform evaluates whether any active deployment campaigns targeting this device need to be re-evaluated given the new firmware version—if the campaign's firmware version is already installed, the device is marked as succeeded for that deployment.
5. For devices in regulated environments (e.g., medical or safety-critical), an unmanaged firmware update may trigger a compliance violation flag that requires the operator to acknowledge and provide justification before the device is allowed to resume normal operation.

**Prevention**

Physical access controls and device attestation can reduce the incidence of unmanaged firmware updates. Devices should report a hardware attestation token (TPM-based or secure element-based) along with their firmware version, allowing the platform to verify that the reported version corresponds to a firmware binary signed by the platform's authorized signing certificate.

---

## Duplicate Device Registration After Hardware Replacement With Same Device ID

**Scenario**

A field technician replaces a failed sensor (device ID `sensor-0451`) with a new hardware unit, but programs the new hardware with the same device ID as the original unit to minimize reconfiguration effort. The new unit generates a new certificate during its provisioning process. When the new unit attempts to register, the Device Registry already has a record for `sensor-0451` with a different certificate fingerprint.

**Detection**

The Device Registry detects a registration request for an existing device ID with a certificate fingerprint that does not match the registered certificate. This constitutes a potential security incident (impersonation attempt) or a legitimate hardware replacement scenario. The system cannot automatically distinguish between the two without additional context.

**Handling**

1. The registration request is blocked and the new device receives a `409 Conflict: DeviceIdAlreadyRegistered` response.
2. A security alert is generated indicating a registration conflict for `sensor-0451` with a new certificate fingerprint, which may indicate either a hardware replacement or an impersonation attempt.
3. A platform operator must review the conflict alert and take one of two actions:
   - **Authorize hardware replacement**: Operator explicitly decommissions the old certificate fingerprint and approves the new device registration under the same device ID. The old device's history is preserved and linked to the new registration.
   - **Reject as security incident**: Operator rejects the registration and escalates to the security team for investigation.
4. After authorization, the new device's certificate is registered and the old certificate is revoked in the CA.

**Prevention**

Device IDs should be derived from hardware-specific identifiers (serial number, MAC address, TPM identity) that are intrinsic to the hardware unit and cannot be programmatically assigned by a technician. For replacement scenarios, the platform should expose a formal "device replacement" workflow that handles the certificate transition, data migration, and audit trail in a structured manner.

---

## Device Floods Platform on Reconnect With Buffered Events (Backpressure Handling)

**Scenario**

10,000 devices in a regional network experience a 4-hour outage simultaneously. All devices reconnect within a 2-minute window and immediately begin uploading their locally buffered telemetry at maximum throughput. The combined reconnect burst generates 50× the normal ingestion volume, overwhelming the ingestion pipeline's processing capacity and causing database write timeouts.

**Detection**

The ingestion pipeline's metrics exporter reports a sudden spike in message queue depth (Kafka consumer lag), ingestion processing latency, and database write error rate. The platform's operational monitoring dashboard alerts on all three metrics simultaneously, indicating a coordinated reconnect burst.

**Handling**

1. The MQTT broker enforces per-device connection rate limits (maximum N new connections per second from the same IP subnet) to spread the reconnect storm across a longer time window.
2. The MQTT broker's `receiveMaximum` parameter (default: 10 in-flight messages per session) limits the number of unacknowledged messages per device, providing natural backpressure from the broker to the device.
3. The ingestion pipeline activates its circuit breaker when queue depth exceeds the configured threshold, pausing acknowledgment of new messages (QoS 1 PUBACK withheld) to signal backpressure to the MQTT broker. The broker in turn signals backpressure to devices by withholding PUBACKs.
4. The time-series database write path activates its overflow routing, directing messages that exceed the write buffer to an overflow object store (S3/Blob) for asynchronous replay after the burst subsides.
5. The platform's auto-scaling group for ingestion workers activates within 2–3 minutes, adding processing capacity to absorb the burst.

**Prevention**

Device firmware should implement jittered reconnect backoff: after detecting a reconnection (clean connection rather than session resumption), the device waits a random delay drawn from a configurable range (e.g., 0–300 seconds) before beginning backlog upload. This spreads the reconnect burst across a longer window without requiring platform-side coordination.

---

## Multiple Reconnect Attempts Causing Session Collision

**Scenario**

A device with an unstable network connection rapidly connects and disconnects, creating multiple MQTT sessions in rapid succession. Each new connection establishes a new session before the previous session's cleanup completes. The platform has multiple concurrent records for the same device ID, causing shadow state updates to be applied out of order.

**Detection**

The MQTT broker detects multiple concurrent connection attempts from the same `clientId` (which equals the device ID) and terminates the older session when a new one is established (MQTT 5.0 `TAKE_OVER` behavior). The Device Registry receives multiple rapid connection and disconnection events in quick succession for the same device ID.

**Handling**

1. The MQTT broker enforces exclusive session ownership: only one session per `clientId` is active at any time. A new connection with the same `clientId` causes the existing session to be forcibly disconnected before the new session is accepted.
2. The Device Registry uses optimistic locking (version field on the device record) when processing connection events. Out-of-order events (e.g., a `Disconnected` event for a session that was already superseded) are discarded.
3. Shadow state updates carry a session identifier, allowing the Shadow Store to reject updates from stale sessions.
4. The platform's rate limiter applies a per-device connection rate limit (maximum 5 connection attempts per minute). Devices exceeding this limit have their new connection attempts rejected with a `CONNECT_RATE_EXCEEDED` error, and a backoff period is enforced.
5. An operator alert is generated for devices exhibiting persistent connection instability, as this may indicate a network infrastructure problem or a device firmware bug in the connection management code.

**Prevention**

Device firmware should implement exponential backoff with jitter for reconnection attempts, starting with a minimum backoff of 1 second and increasing to a maximum of 5 minutes. The SDK's default reconnection policy implements this behavior, and developers should not override it with aggressive reconnection strategies.

---

## Offline Device Included in Active Firmware Deployment (Deployment State Reconciliation)

**Scenario**

A firmware deployment campaign targets the "factory-floor-sensors" group and begins rolling out. 15% of devices in the group are offline at the time of deployment. These devices remain offline throughout the campaign's scheduled duration. The deployment completes for the online devices but the offline devices' statuses remain at `Notified` indefinitely.

**Detection**

The Deployment Orchestrator tracks per-device deployment status. After the campaign's configured timeout window (e.g., 30 days), devices that have not progressed beyond `Notified` are identified as stale pending devices. The progress tracker reports the campaign as `PartiallyComplete` rather than `Complete`.

**Handling**

1. When an offline device reconnects, the Device Registry publishes a `DeviceReconnected` event to the event bus. The Deployment Orchestrator subscribes to this event and checks whether the reconnected device has any pending deployments.
2. If the device reconnects within the campaign's active window, the firmware notification is re-sent immediately.
3. If the campaign has expired but the device is still running the target firmware version (below the deployment's target version), the platform creates a follow-up deployment task for that device.
4. The original campaign is marked `Complete` once all online devices have been processed. Offline devices are logged as `OfflineAtCompletion` with a reference to the follow-up deployment task.
5. The follow-up deployment task remains active until the device reconnects and completes the update, or until an operator explicitly closes it.

**Prevention**

Deployment campaigns should specify a minimum online percentage requirement before the campaign is marked complete. If the offline device percentage exceeds the configured maximum acceptable offline rate (e.g., 20%), the campaign is paused and an operator must decide whether to proceed, extend the deadline, or cancel and reschedule when more devices are expected to be online.

---

## Split-Brain: Device State on Platform Diverges From Actual Device State

**Scenario**

The device shadow for `pump-controller-0012` shows `desired.pumpActive: true` and `reported.pumpActive: true`. However, the pump's actual hardware state is stopped—a power surge reset the device's microcontroller, clearing its in-memory state, but the device's MQTT client session persisted (the broker cached the session), so no reconnection event occurred and the shadow was never updated to reflect the reset.

**Detection**

The platform does not directly detect the split-brain state because the device appears connected and the shadow appears consistent. Detection relies on indirect signals:
- The pump's flow rate telemetry drops to zero while `pumpActive: true` is reported in the shadow.
- A watchdog heartbeat that the pump controller sends every 60 seconds stops arriving (because the microcontroller reset cleared the heartbeat task).
- A rules engine rule detects the anomaly: `pumpActive == true AND flowRate == 0 FOR 5 MINUTES`.

**Handling**

1. The rules engine rule fires and creates an alert: `DeviceStateDivergence: pump-controller-0012`.
2. The alert includes the contradictory state: shadow reports running, telemetry indicates stopped.
3. An operator can issue a shadow sync command: the platform publishes a `desired.pumpActive` = current intended state update, which triggers the device to re-evaluate and update its `reported` state.
4. The device receives the shadow delta (desired != reported) and re-applies the desired state, effectively reconciling the split-brain.
5. If the device is not responsive to shadow updates (fully frozen state), the operator can issue a reboot command to force a full device state reinitialize from the desired shadow on next boot.

**Prevention**

Devices should implement a periodic state attestation mechanism: every N minutes, the device compares its actual hardware state against the last `reported` shadow values and publishes an updated `reported` state if discrepancies are found. This self-healing state report closes split-brain windows without requiring platform-side detection. The device SDK provides a `reportState(actualState)` method that should be called at configurable intervals from the device's main loop.

---

## Summary Table

| Edge Case | Severity | Primary Detection Signal | Recovery Strategy |
|---|---|---|---|
| Extended offline backlog | Medium | Anomalous per-device message rate | Rate limiting, backpressure, overflow store |
| Clock skew out-of-order timestamps | Medium | Timestamp vs. provisioning date validation | Dual timestamps, NTP sync command |
| Expired certificate on reconnect | High | TLS handshake failure log | Out-of-band certificate renewal bootstrap |
| Silent network partition | Medium | MQTT keep-alive timeout | Reconnect with session resumption |
| Unmanaged firmware update | Medium | Firmware version mismatch on hello | Operator review, audit trail, attestation |
| Duplicate device ID after hardware replacement | High | Certificate fingerprint conflict on registration | Formal hardware replacement workflow |
| Reconnect flood backpressure | High | Kafka lag, DB write errors | MQTT flow control, circuit breaker, auto-scale |
| Session collision | Medium | Rapid connect/disconnect events | Exclusive session ownership, connection rate limit |
| Offline device in active deployment | Low | Stale `Notified` status after campaign timeout | Follow-up deployment task on reconnect |
| Split-brain device state | High | Rules engine anomaly detection | Shadow sync command, periodic state attestation |
