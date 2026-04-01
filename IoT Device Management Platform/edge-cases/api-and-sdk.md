# Edge Cases: API and SDK Usage

This document catalogs edge cases arising from API consumption and SDK integration patterns in the IoT Device Management Platform. These cases cover scenarios where the contract between the platform and its developer consumers is stressed by versioning mismatches, resource exhaustion, network constraints, and failure-mode behaviors.

---

## SDK Version Mismatch Between Device Firmware and Platform API Version

**Scenario**

A device fleet is running firmware compiled against SDK version 2.4.1. The platform API is updated to version 3.0, which introduces a breaking change: the telemetry message schema now requires a `schemaVersion` field, and the command response format has changed. Devices running the old SDK continue to publish telemetry and receive commands using the v2 message format.

**Impact**

Schema validation failures cause device telemetry to be routed to the dead-letter queue, resulting in silent data loss from the perspective of the operator. Command responses from devices using the v2 format are rejected by the v3 response handler, and commands appear to time out even when the device successfully executes them.

**Handling**

1. The platform maintains API version compatibility for a minimum deprecation window (2 major versions, 18-month minimum). The ingestion pipeline continues to accept v2-format messages alongside v3 messages during the compatibility window, using the presence/absence of the `schemaVersion` field to determine which parser to apply.
2. The Device Registry stores the SDK version reported by each device in the hello payload. The platform identifies devices running deprecated SDK versions and surfaces them in the "Devices Requiring Update" dashboard.
3. When a device running a deprecated SDK version connects, the MQTT broker publishes a compatibility warning message on the device's config topic, instructing the firmware team to plan an SDK upgrade.
4. The platform publishes a migration guide with the API changelog and provides a compatibility adapter library that allows devices using the old SDK to continue functioning with minimal changes to application code.
5. After the deprecation window expires, the platform rejects v2 messages with a structured error response that includes a migration documentation URL.

**Prevention**

The SDK includes a built-in API version negotiation handshake in the CONNECT sequence. The device reports its SDK version and the platform responds with the supported API version range and whether the device's SDK is current, deprecated, or unsupported. Device firmware teams receive automated alerts when their devices' SDK versions enter the deprecated range.

---

## API Rate Limit Exceeded by Legitimate High-Frequency Telemetry Device

**Scenario**

An industrial vibration sensor samples at 1,000 Hz and publishes aggregated 100ms telemetry bundles (10 readings per message) at 10 messages/second. The platform's default API rate limit for device telemetry is 5 messages/second per device. The device's telemetry is throttled, causing 50% of its readings to be dropped.

**Impact**

Missing telemetry samples can cause anomaly detection algorithms to miss high-frequency fault signatures that only appear in high-resolution vibration data. The device's effective sampling resolution is halved, degrading predictive maintenance accuracy.

**Handling**

1. The platform's rate limiting system is tiered: a default quota applies to all devices, and per-device or per-device-type quota overrides can be configured by administrators.
2. When a device consistently approaches its rate limit (80%+ utilization over a 5-minute window), the ingestion pipeline generates a `RateLimitApproach` alert for the device's operator, suggesting a quota review.
3. The operator can submit a quota increase request through the platform portal. The request is evaluated against the device's provisioned tier and the tenant's aggregate quota.
4. For devices in the high-frequency telemetry tier, the quota is automatically set at provisioning time based on the device type's expected throughput characteristics configured in the device type catalog.
5. Rate-limited messages are not silently dropped; the device receives a `PUBACK` with reason code `0x96 Message Rate Too High` (MQTT 5.0), which the SDK interprets and surfaces to the application as a throttling signal. The application can respond by increasing its local aggregation window.

**Prevention**

Device architects should profile expected telemetry rates during device type design and configure the appropriate device type quota in the platform before provisioning devices. The platform's device type catalog includes a `maxTelemetryRateHz` field that is used to provision the appropriate ingestion quota automatically.

---

## Bulk Device Registration API Call With Partial Failures

**Scenario**

An operator submits a bulk device registration request containing 5,000 devices via the REST API. 4,847 devices register successfully, but 153 fail due to a mix of reasons: 91 have duplicate device IDs already in the registry, 42 have malformed certificate CSRs, and 20 fail due to a transient CA service timeout during certificate issuance.

**Impact**

If the API returns a single success/failure response for the entire batch, the operator cannot determine which individual registrations succeeded or failed, requiring manual reconciliation. If the entire batch is rolled back on any failure, the 4,847 successful registrations are lost and must be re-submitted.

**Handling**

1. The bulk registration API implements partial success semantics: each device registration in the batch is attempted independently, and the response includes a per-device result array with success/failure status and error details for each device.
2. The API response uses HTTP 207 Multi-Status to signal that the batch had mixed results.
3. The response body includes:
   - `successCount`: 4,847
   - `failureCount`: 153
   - `results[]`: array with one entry per input device, each with `deviceId`, `status` (success/failed), `error` (if failed), and `registrationId` (if success).
4. The operator can filter the results for failed registrations and address each failure class separately: re-submit the 20 CA-timeout failures (transient), fix the 42 malformed CSRs (data error), and resolve the 91 duplicates through the appropriate de-duplication workflow.
5. Successful registrations are committed and not affected by failures in other batch items.

**Prevention**

The bulk registration API supports a dry-run mode (`?dryRun=true`) that validates all device records in the batch without committing any registrations. Operators should use dry-run mode to identify validation errors before submitting a large bulk registration, reducing the likelihood of partial-failure batches.

---

## Long-Polling Command Endpoint Timeout During Device Sleep Cycle

**Scenario**

A device implements a power-saving strategy where it sleeps for 15 minutes between telemetry uploads and command polls. It uses HTTP long-polling (rather than persistent MQTT) to check for pending commands, with a 30-second long-poll timeout. The platform's load balancer has a 60-second idle connection timeout. During the 15-minute sleep period, issued commands queue up, and when the device polls, it receives no commands because its long-poll window is shorter than the connection timeout of intermediate network infrastructure.

**Impact**

Commands are delivered only when they happen to be queued within the device's narrow polling window. Commands issued between polling cycles are delayed by up to 15 minutes. In time-sensitive scenarios (e.g., "open emergency valve"), this delay is unacceptable.

**Handling**

1. The platform recommends MQTT over persistent HTTP long-polling for devices with command delivery latency requirements. MQTT sessions can be maintained with a keep-alive interval tailored to the device's duty cycle.
2. For devices constrained to HTTP, the platform's command polling API supports a pull model: `GET /devices/{deviceId}/commands/pending` returns all queued commands immediately without holding the connection open. The device polls at its wake interval.
3. For devices with strict power budgets that use deep sleep (disconnecting TCP entirely between cycles), the platform supports an SMS or push notification wake signal that alerts the device to wake early and poll when a high-priority command is pending.
4. The platform documents the command delivery latency expectations for each connectivity model: MQTT (seconds), HTTP long-poll (seconds to minutes), HTTP periodic poll (up to one poll cycle interval), SMS wake (carrier-dependent, typically 30–60 seconds).
5. Command TTLs are set to expire only after a time window significantly longer than the expected maximum delivery latency for the device's connectivity model.

**Prevention**

During device provisioning, operators configure the device's connectivity model (`persistent`, `periodic-poll`, `deep-sleep`) in the Device Registry. The Command Service uses this information to set appropriate command TTLs and delivery expectations, preventing operators from inadvertently issuing time-sensitive commands to devices incapable of receiving them within the required window.

---

## SDK Connection Pool Exhaustion on High-Throughput Device

**Scenario**

A gateway device aggregates telemetry from 500 downstream sensors and publishes to the platform on behalf of each sensor. The gateway SDK creates one MQTT connection per logical device (per sensor), resulting in 500 concurrent MQTT connections from a single physical host. The SDK's internal connection pool reaches its maximum connection limit, and new connection attempts block indefinitely.

**Impact**

Connection pool exhaustion causes telemetry publishing to stall, creating a growing backlog of sensor readings on the gateway. If the backlog exceeds the gateway's local buffer capacity, telemetry data is lost. The gateway application may also deadlock if blocking connection acquisition is performed on the same thread as telemetry collection.

**Handling**

1. The SDK provides a multiplexed connection mode where multiple logical device sessions share a smaller pool of physical MQTT connections. Topic-based routing on the shared connections distinguishes between logical devices.
2. The SDK enforces a maximum connection pool size configurable at initialization (default: 50 connections). When the pool is exhausted, the SDK applies backpressure to the caller rather than blocking indefinitely—the `publish()` call returns a `ConnectionPoolExhausted` error immediately.
3. The gateway application should handle this error by queuing the message locally and retrying after a backoff period.
4. For gateway use cases specifically, the platform provides a batch telemetry submission API: a single MQTT message can carry telemetry for multiple logical devices using a structured envelope format, eliminating the need for per-device connections.
5. The SDK's connection pool metrics (active connections, queued requests, pool saturation) are exposed via a local Prometheus endpoint, enabling the gateway application to monitor pool health.

**Prevention**

The SDK documentation includes a gateway usage guide recommending the batch telemetry API for any device aggregating more than 10 downstream devices. The SDK initialization includes a connection count estimate parameter that triggers a warning log if the expected connection count approaches the pool limit.

---

## API Authentication Token Expiry During Long-Running SDK Operation

**Scenario**

The SDK authenticates using a short-lived JWT access token (15-minute TTL) obtained via the platform's OAuth2 client credentials flow. A device performing a large bulk shadow update operation begins the operation just before token expiry. Midway through the operation, the token expires and the platform returns `401 Unauthorized` for the remaining requests in the batch.

**Impact**

Partial completion of a bulk shadow update can leave device shadows in an inconsistent intermediate state. The device must determine which updates were applied and re-submit only the failed ones—a complex reconciliation task if the operation was not designed with partial failure in mind.

**Handling**

1. The SDK implements proactive token refresh: it schedules a token refresh 60 seconds before the current token's expiry (configurable). For a 15-minute token, refresh is attempted at the 14-minute mark.
2. If a refresh is in flight when an API call is made, the SDK queues the API call and executes it after the new token is obtained.
3. If a token expires unexpectedly (e.g., the refresh request failed), the SDK catches the 401 response, immediately attempts a fresh token acquisition, and retries the failed request once with the new token.
4. For bulk operations, the SDK exposes transactional bulk APIs that the platform executes atomically: either all updates in the batch succeed, or none are applied. This eliminates partial-completion inconsistency.
5. Shadow update operations include an `etag` based on the shadow version, allowing idempotent retries: re-submitting a shadow update with the same `etag` is a no-op if the update was already applied.

**Prevention**

Platform tokens issued to devices use longer TTLs than tokens issued to human users, reflecting the automated nature of device operations. Device tokens default to 24-hour TTL (refreshed every 23 hours), while human user tokens default to 15-minute TTL. The platform's API enforces distinct token scopes for device vs. user operations.

---

## SDK Retry Storm: All Devices Retry Simultaneously After Platform Outage

**Scenario**

The platform experiences a 45-minute MQTT broker outage. All 250,000 connected devices detect the disconnect simultaneously and begin reconnection attempts using the default SDK configuration—a fixed 5-second reconnect interval. When the broker recovers, all 250,000 devices attempt to reconnect within a 5-second window, sending 50,000 connection requests per second to a cluster dimensioned for normal steady-state connection churn.

**Impact**

The reconnect storm can overwhelm the MQTT broker's TLS handshake processing capacity, causing new connection attempts to time out even after the broker has recovered. The broker appears to recover, then immediately re-degrades under reconnect load. MQTT sessions with pending messages generate a secondary write storm to the time-series database as devices upload their buffered telemetry simultaneously.

**Handling**

1. The SDK implements exponential backoff with full jitter for reconnection: the reconnect delay is computed as `random(0, min(cap, base * 2^attempt))` where `base=1s`, `cap=300s`. This distributes reconnect attempts over a time window proportional to the number of disconnected devices.
2. The MQTT broker implements a connection rate limiter (configurable, default: 1,000 new connections/second) that queues excess connection attempts rather than rejecting them, ensuring a smooth reconnect absorption even under storm conditions.
3. The platform's auto-scaling policy for the MQTT broker cluster activates during the outage recovery phase, scaling out additional broker instances before the reconnect storm arrives.
4. The platform publishes a "service recovered" notification via a status page and push notification channel; devices configured to monitor the status page can use this as a hint to begin reconnection earlier than their backoff timer would otherwise allow.

**Prevention**

The SDK's default reconnection configuration uses jittered exponential backoff, and this default must not be overridden by device application code to a fixed-interval retry. The SDK documentation explicitly warns against synchronous fixed-interval reconnection patterns and includes a code example of correct jittered backoff implementation.

---

## GraphQL Query Complexity Limit Exceeded for Fleet-Wide Device Query

**Scenario**

A developer writes a GraphQL query to retrieve device status, latest telemetry, active alerts, pending commands, firmware version, and group membership for all 100,000 devices in a tenant. The query's computed complexity score (based on field depth × estimated result set size) exceeds the platform's maximum query complexity limit of 10,000 and is rejected.

**Impact**

Developers who need fleet-wide visibility cannot retrieve the data they need in a single query and must design paginated or fragmented query strategies, increasing development complexity. Over-restrictive limits can push developers toward REST bulk APIs or direct database queries that bypass platform access controls.

**Handling**

1. The platform returns a structured error response including the computed complexity score, the limit, and a link to the query optimization guide.
2. The developer guide recommends:
   - Using pagination with cursor-based continuation (`first: 100, after: <cursor>`) rather than loading the full fleet in one query.
   - Selecting only required fields to reduce complexity score (avoiding `__all__` style selections).
   - Using dedicated export APIs for bulk data retrieval scenarios (fleet-wide CSV/JSON export with async job pattern).
3. The platform provides an `@estimate` query directive that returns the complexity score without executing the query, allowing developers to tune their query before hitting the limit in production.
4. For internal monitoring use cases (e.g., fleet health dashboards), the platform exposes pre-computed aggregate API endpoints that serve fleet-wide summaries without requiring complex ad-hoc queries.

**Prevention**

The GraphQL schema includes field-level complexity hints in the documentation, and the developer portal's GraphQL Explorer displays a real-time complexity estimate as the query is being composed. This allows developers to identify high-complexity queries before deployment.

---

## Webhook Delivery Failures for Alert Notifications to Third-Party Systems

**Scenario**

The platform is configured to deliver alert notifications to a third-party incident management webhook endpoint. The incident system's webhook handler experiences a deployment issue and begins returning `500 Internal Server Error` responses. The platform accumulates a backlog of undelivered webhook payloads while continuing to generate new alert events at normal volume.

**Impact**

Alert notifications are silently lost if the platform does not implement durable webhook delivery. The incident management system does not create incidents for real device failures, and on-call engineers are not paged. The SLO for alert-to-page latency is breached.

**Handling**

1. The platform's Webhook Service implements durable delivery with retry: failed webhook deliveries are queued in a persistent outbox and retried with exponential backoff (1s, 2s, 4s, ... up to 5 minutes between retries).
2. The webhook delivery state machine records each delivery attempt with the HTTP response code and timestamp.
3. After a configurable number of consecutive failures (default: 10 over 30 minutes), the webhook endpoint is marked as `Degraded` and the platform switches to a fallback notification channel (email or SMS) for alerts with critical or emergency severity.
4. The webhook endpoint owner is notified of the delivery failures via an alternative channel (email to the webhook owner's registered email address).
5. When the webhook endpoint recovers and begins returning 2xx responses, the platform replays the backlogged deliveries in order, ensuring no alerts are permanently lost.

**Prevention**

Webhook endpoint health is monitored via periodic probe requests (configurable, default: every 5 minutes). Webhook owners can configure a fallback notification channel in the platform's webhook settings, which is activated automatically when the primary endpoint becomes unavailable.

---

## SDK Operating in Restricted Network (Firewall Blocking MQTT Port 8883, Fallback to WSS)

**Scenario**

A device is deployed in a corporate network where the security policy blocks all outbound connections except HTTP (80) and HTTPS (443). The standard MQTT-over-TLS port (8883) is blocked by the firewall. The device SDK's initial connection attempt to port 8883 times out after 30 seconds.

**Impact**

Without a fallback mechanism, the device cannot connect to the platform at all, rendering it non-functional. The network restriction is common in enterprise environments and industrial facilities with strict egress policies.

**Handling**

1. The SDK implements automatic protocol fallback: after a configurable connection timeout (default: 10 seconds) for the primary MQTT/TLS (port 8883) connection attempt, the SDK automatically tries MQTT over WebSockets over TLS (MQTTS/WSS) on port 443.
2. The MQTT broker exposes a WebSocket listener on port 443 (`wss://broker.platform.example.com/mqtt`) in addition to the standard TLS listener on port 8883.
3. MQTT over WSS has slightly higher overhead than native MQTT/TLS (WebSocket framing overhead) but maintains full MQTT protocol semantics including QoS, retained messages, and clean/persistent sessions.
4. The SDK logs the fallback event at the INFO level to inform firmware developers that port 8883 is blocked in the deployment environment.
5. If both port 8883 and port 443 WSS are blocked, the SDK reports `NO_VIABLE_TRANSPORT` and surfaces this to the application code, which should log a persistent diagnostic for field investigation.

**Prevention**

The device deployment guide includes a network requirements section listing the required firewall rules for full platform functionality, with explicit notes about the WSS fallback for restricted environments. New device deployments in enterprise environments should be validated with the platform's network connectivity checker tool before mass deployment.

---

## Summary Table

| Edge Case | Severity | Primary Impact | Key Mitigation |
|---|---|---|---|
| SDK version mismatch | High | Silent data loss, command failures | API versioning, compatibility window, SDK version alerts |
| Rate limit exceeded by legitimate device | Medium | Telemetry data loss | Tiered quotas, device type-based provisioning |
| Bulk registration partial failure | Medium | Reconciliation complexity | HTTP 207 Multi-Status per-item results |
| Long-poll timeout during sleep cycle | Medium | Command delivery delay | MQTT persistence, pull-model polling API |
| Connection pool exhaustion | High | Telemetry stall, gateway deadlock | Multiplexed connections, batch telemetry API |
| Auth token expiry mid-operation | Medium | Partial shadow state inconsistency | Proactive token refresh, idempotent operations |
| SDK retry storm after outage | High | Broker re-degradation on recovery | Jittered exponential backoff, connection rate limiter |
| GraphQL complexity limit exceeded | Low | Developer experience friction | Complexity estimate directive, export APIs |
| Webhook delivery failures | High | Silent alert loss, SLO breach | Durable outbox delivery, fallback notification channel |
| Firewall blocking MQTT port 8883 | Medium | Device cannot connect | Automatic WSS fallback on port 443 |
