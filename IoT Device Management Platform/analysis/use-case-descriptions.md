# Use Case Descriptions — IoT Device Management Platform

## Document Purpose

This document provides full structured use case specifications for the IoT Device Management Platform. Each primary use case follows a complete template covering actors, pre/postconditions, main success scenario, alternative flows, exception flows, referenced business rules, non-functional requirements, and UI/UX notes. Secondary use cases are specified at briefer depth. Cross-cutting concerns common to all use cases are captured in the final section.

---

## UC-01 — Provision Device

**Brief Description**
A Device Operator or Platform Admin registers a new IoT device with the platform using X.509 certificate-based mutual TLS. The flow covers bootstrap credential exchange, certificate signing request (CSR) submission, operational certificate issuance by the Certificate Authority, Device Registry entry creation, and Device Shadow initialisation.

**Actors**
- Primary: Device Operator
- Secondary: Device Hardware, Certificate Authority, Platform Admin (approval gate when tenant quota is near limit)

**Preconditions**
1. The device's serial number (format: `[A-Z]{3}[0-9]{9}`) has been registered in the Allowed Serial Number list by Platform Admin.
2. A tenant-specific Bootstrap CA certificate has been installed on the device at manufacturing time.
3. The device has network connectivity reaching the platform MQTT endpoint on port 8883.
4. The tenant's device quota has not been reached (checked against `tenant.device_quota` in the configuration store).
5. The Device Operator holds the `device:provision` permission in their JWT claims.
6. The EMQX broker's `emqx_auth_http` plugin is reachable at `http://auth-service:8080/authenticate`.

**Postconditions**
1. A Device Registry record exists with status `PROVISIONED` and contains the device's serial number, tenant ID, operational certificate thumbprint, and creation timestamp.
2. The operational X.509 certificate (validity: 365 days, key algorithm: ECDSA-P256) has been issued and stored in the Certificate Service's Vault-backed store.
3. A Device Shadow document exists in the shadow store (Redis + PostgreSQL) with empty `desired` and `reported` state sections and a `version` of 1.
4. A `platform.device.provisioned` event has been published to Kafka topic `platform-events` with the device ID, tenant ID, and provisioning timestamp.
5. The device is subscribed to its operational MQTT topic namespace: `dt/{tenantId}/{deviceId}/#` and `cmd/{tenantId}/{deviceId}/#`.
6. An audit log record has been written capturing the operator's identity, source IP, and timestamp.

**Main Success Scenario**
1. The device powers on and reads its bootstrap certificate from secure storage (TPM or secure element).
2. The device connects to `mqtts://provision.iot.platform:8883` using the bootstrap certificate for mutual TLS (TLS 1.3, cipher suite: `TLS_AES_256_GCM_SHA384`).
3. EMQX invokes the `emqx_auth_http` plugin, which calls `POST /authenticate` on the Auth Service with the certificate thumbprint. The Auth Service validates the certificate chain against the Tenant Bootstrap CA and confirms the serial number is in the allowed list.
4. The device publishes a JSON payload to `$platform/provision/{serialNumber}` containing the CSR (PEM-encoded, ECDSA-P256 key), firmware version, hardware model, and geographic region hint.
5. The Device Service consumes the message, validates the CSR fields (CN must equal `device:{serialNumber}:{tenantId}`), and checks tenant quota against the configuration store.
6. The Device Service calls the Certificate Service gRPC endpoint `CertificateService.SignCSR` (internal port 50051), which forwards the CSR to the configured Certificate Authority (ACME or internal SCEP/EST).
7. The Certificate Authority signs the certificate and returns the PEM-encoded operational certificate chain. The Certificate Service stores the certificate in Vault at path `secret/tenants/{tenantId}/devices/{deviceId}/cert` and records metadata in PostgreSQL.
8. The Device Service creates a Device Registry record in PostgreSQL (`device_registry` table) with status `PROVISIONING`.
9. The Device Service publishes the signed certificate and MQTT connection parameters back to the device via `$platform/provision/{serialNumber}/response` with a 30-second message TTL.
10. The device stores the operational certificate, disconnects from the provisioning endpoint, and reconnects to `mqtts://devices.iot.platform:8883` using the operational certificate.
11. The Device Service detects the reconnection event (via EMQX webhook `client.connected`) and transitions the Device Registry record to `PROVISIONED`.
12. The Device Service publishes a `platform.device.provisioned` event to Kafka and initialises the Device Shadow document with default desired state from the fleet policy (if the device has been pre-assigned to a group).

**Alternative Flows**

*AF-01: PSK-based provisioning for resource-constrained devices*
At step 2, if the device presents a Pre-Shared Key identity (MQTT username `psk:{serialNumber}:{secret}`) instead of a client certificate, EMQX routes the connection to the PSK authentication handler. The Auth Service validates the PSK against the pre-registered secret in the provisioning database. The flow continues from step 4 with the same CSR submission, but the Device Service marks the device with `auth_method: PSK` and issues a lower-trust operational credential.

*AF-02: QR code-assisted provisioning via mobile app*
Before step 1, a Device Operator scans the device's QR code using the platform mobile app. The app calls `POST /api/v1/devices/claim` with the encoded serial number and an operator token. The Device Service creates a provisioning intent record with a 10-minute TTL. When the device connects at step 2, it includes an `X-Claim-Token` header in the MQTT CONNECT packet's password field, allowing the platform to associate the device with the operator's tenant without requiring the operator to manually enter a serial number.

*AF-03: Bulk provisioning via CSV upload*
A Platform Admin uploads a CSV file containing serial numbers, model codes, and target group IDs. The platform creates provisioning intent records for each row and sends a bulk activation notification to the field team. Individual devices complete the X.509 handshake asynchronously as they come online. The Admin receives a completion report via email when all devices in the batch reach `PROVISIONED` status.

*AF-04: Re-provisioning an existing device after factory reset*
At step 5, the Device Service detects an existing Device Registry record for the serial number with status `DECOMMISSIONED` or `FACTORY_RESET`. It creates a new operational certificate, archives the old certificate record, and resets the Device Shadow. The original device ID is preserved to maintain historical telemetry linkage.

**Exception Flows**

*EX-01: Serial number not in allowed list*
At step 3, the Auth Service returns `403 Forbidden`. EMQX closes the MQTT connection with reason code `0x87 Not Authorized`. The device applies exponential backoff (base: 60 s, max: 3600 s) before retrying. The platform logs a `PROVISION_REJECTED_UNKNOWN_SERIAL` security event.

*EX-02: Tenant quota exceeded*
At step 5, the quota check returns `QUOTA_EXCEEDED`. The Device Service publishes an error response to `$platform/provision/{serialNumber}/response` with code `QUOTA_EXCEEDED`. A `platform.tenant.quota.exceeded` event is published to Kafka, triggering a notification to the Platform Admin. The provisioning attempt is recorded in the audit log.

*EX-03: Certificate Authority unreachable*
At step 6, the gRPC call to the Certificate Service returns `UNAVAILABLE` after three retries with 500 ms exponential backoff. The Device Service transitions the provisioning attempt to `PENDING` state and schedules a retry in 60 seconds via a Kafka delayed-message pattern (retention: 5 minutes). The device receives an `HTTP 503`-equivalent MQTT error and retries according to its backoff schedule.

*EX-04: CSR validation failure*
At step 5, if the CSR's CN field does not match the expected pattern `device:{serialNumber}:{tenantId}`, the Device Service rejects the request with code `CSR_INVALID`. The rejection is logged as a security event. If this occurs three times from the same device within 5 minutes, the serial number is temporarily blocked and a `SUSPICIOUS_PROVISIONING_ATTEMPT` alert is raised.

**Business Rules Referenced**
- BR-001: Device serial numbers must match the tenant's approved manufacturer list before provisioning is permitted.
- BR-005: Bootstrap certificates must expire within 30 days; operational certificates must expire within 365 days.
- BR-012: A single tenant may not exceed its provisioned device quota without explicit Platform Admin approval.
- BR-019: All provisioning events must be recorded in the immutable audit log with actor identity, timestamp (UTC), and source IP address.

**Non-Functional Requirements**
- The provisioning handshake (steps 2–9) must complete within 10 seconds under normal load.
- The Device Service must handle 500 concurrent provisioning flows without degradation.
- Provisioning events must be delivered to Kafka within 2 seconds of the Device Registry update.
- Audit log writes must be synchronous and must not be skipped even if the downstream audit store is temporarily slow (circuit-breaker pattern with local buffer).

**UI/UX Notes**
- The web portal displays a real-time provisioning status indicator on the device detail page, polling `GET /api/v1/devices/{deviceId}/status` every 3 seconds during the provisioning flow.
- Failed provisioning attempts show a colour-coded error card with the rejection reason code and a "Retry Provisioning" button that pre-fills the serial number.
- The QR code scanning workflow (AF-02) must work offline for serial number capture, uploading the claim token once connectivity is restored.

---

## UC-02 — Push Firmware Update

**Brief Description**
A Fleet Manager creates an OTA deployment job to push a new firmware binary to a target device group. The platform orchestrates a canary-first rollout strategy, monitors per-device update health, and automatically rolls back the deployment if the failure rate exceeds the configured threshold.

**Actors**
- Primary: Fleet Manager
- Secondary: Device Hardware, OTA Service, Platform Admin (for firmware binary upload), Operations Engineer (monitoring)

**Preconditions**
1. The firmware binary has been uploaded to Object Storage by Platform Admin and the platform has verified its ECDSA-P256 signature against the tenant's firmware signing public key.
2. The firmware binary record in the database has status `APPROVED` (requires a two-party approval for production tenants: Platform Admin + Security Officer).
3. The target device group exists and contains at least one device with status `PROVISIONED` or `ACTIVE`.
4. All devices in the group are running firmware version lower than the target version (or a subset filter is applied).
5. The Fleet Manager holds the `ota:deploy` permission.
6. No other OTA deployment is currently `IN_PROGRESS` for the target group.

**Postconditions**
1. An OTA deployment job record exists with a terminal status: `COMPLETED`, `PARTIALLY_COMPLETED` (>95% success), or `ROLLED_BACK`.
2. Each device that successfully installed the firmware has its `firmware_version` field updated in the Device Registry.
3. Devices that failed to update retain their previous firmware version and have an `OTA_FAILURE` event in their history.
4. A deployment summary report is available at `GET /api/v1/ota/deployments/{deploymentId}/report`.
5. If rollback was triggered, all devices that had applied the new firmware have been instructed to revert to the previous version.

**Main Success Scenario**
1. Fleet Manager navigates to OTA → Create Deployment, selects the target firmware version and device group, sets canary percentage to 5%, failure threshold to 10%, and rollout wave intervals to 30 minutes.
2. Fleet Manager submits the deployment; the platform creates an OTA deployment record with status `SCHEDULED` and generates a signed download URL (S3 pre-signed URL, 24-hour validity) for the firmware binary.
3. The OTA Service selects the canary cohort (5% of target devices, prioritising devices with recent telemetry activity and geographic spread) and publishes `cmd/{tenantId}/{deviceId}/ota` MQTT messages to each canary device containing the firmware metadata and pre-signed download URL.
4. Each canary device downloads the firmware binary over HTTPS (TLS 1.3) from Object Storage, verifies the SHA-256 checksum and ECDSA-P256 signature, writes the binary to the inactive partition, and reports `DOWNLOAD_COMPLETE` status via `dt/{tenantId}/{deviceId}/ota/status`.
5. Each device reboots into the new firmware partition. The bootloader validates the image signature before completing the boot. The new firmware publishes `INSTALL_SUCCESS` with the new version string within 120 seconds of reboot.
6. The OTA Service evaluates canary health after 30 minutes: success rate, connectivity rate, telemetry freshness, and error-rate delta compared to the baseline pre-deployment window.
7. Health check passes. The OTA Service expands the rollout to 25% of the remaining devices, waits 30 minutes, then expands to 75%, waits 30 minutes, then completes with 100%.
8. The OTA Service marks the deployment `COMPLETED` and publishes a `platform.ota.deployment.completed` event to Kafka.
9. The Fleet Manager receives a completion notification via email/webhook and views the deployment report.

**Alternative Flows**

*AF-01: Manual wave approval*
The Fleet Manager configures the deployment with `approval_mode: MANUAL`. After each wave completes, the deployment pauses at `WAVE_COMPLETE` status. The Fleet Manager must explicitly approve the next wave via the portal or `POST /api/v1/ota/deployments/{id}/waves/{waveId}/approve`. This mode is required for production device groups in regulated tenants.

*AF-02: Scheduled deployment*
The Fleet Manager sets a deployment start time in the future (minimum 5 minutes ahead). The OTA Service stores the job in `SCHEDULED` state and uses a Quartz-compatible job scheduler to trigger the canary wave at the specified time, respecting the device group's maintenance window configuration.

*AF-03: Device offline during deployment*
A device targeted in wave 1 is offline when the MQTT notification is sent. The OTA Service stores the notification in a pending-commands queue (TTL: 72 hours). When the device reconnects, it receives the queued command and proceeds with download. Its status is tracked separately from the main wave progress counter.

*AF-04: Emergency rollback initiated by Fleet Manager*
At any point during the rollout, the Fleet Manager can trigger an immediate rollback via `POST /api/v1/ota/deployments/{id}/rollback`. The OTA Service stops all pending wave notifications and sends `cmd/{tenantId}/{deviceId}/ota/rollback` to all devices that have applied the new firmware. Devices reboot into the previous partition.

**Exception Flows**

*EX-01: Firmware checksum mismatch on device*
At step 4, a device reports `CHECKSUM_FAILED` via the OTA status topic. The OTA Service increments the failure counter for the current wave. If the failure counter exceeds the threshold (default: 10%), automatic rollback is triggered.

*EX-02: Device fails to boot new firmware (boot loop detected)*
The device's watchdog detects three consecutive failed boots of the new firmware partition and falls back to the previous partition automatically (A/B partition scheme). The device reports `INSTALL_FAILED` with reason `BOOT_LOOP` to the platform. The OTA Service records the failure and excludes this device from future waves of the same deployment.

*EX-03: Object Storage pre-signed URL expires*
If a device attempts to download the firmware after the 24-hour URL expiry, the HTTPS GET returns 403. The device reports `DOWNLOAD_FAILED` with reason `URL_EXPIRED`. The OTA Service generates a fresh pre-signed URL (validity: 1 hour) and republishes the command to the device.

*EX-04: Automatic rollback threshold exceeded*
At step 6 or any subsequent wave evaluation, if the failure rate exceeds the configured threshold, the OTA Service transitions the deployment to `ROLLING_BACK` state, sends rollback commands to all updated devices, and publishes a `platform.ota.deployment.rolledback` event. The Fleet Manager receives a critical alert with the failure analysis report.

**Business Rules Referenced**
- BR-023: Firmware binaries must carry a valid ECDSA-P256 signature before they can be deployed.
- BR-024: Production-tier tenants require two-person approval for firmware binary promotion.
- BR-027: OTA deployments must begin with a canary cohort of at least 1% of the target fleet.
- BR-031: Automatic rollback must be triggered when the per-wave failure rate exceeds the deployment's configured threshold (range: 5%–50%).

**Non-Functional Requirements**
- OTA MQTT notification delivery latency must be under 5 seconds for 99th percentile.
- Firmware download throughput per device must sustain 1 Mbps from Object Storage.
- The OTA Service must support 10,000 concurrent device update flows per tenant.
- Rollback commands must be delivered to all affected devices within 60 seconds of threshold breach.

**UI/UX Notes**
- The deployment progress view auto-refreshes every 10 seconds, showing a heat-map of device states (pending/downloading/installing/success/failed) overlaid on a geographic map if devices have location metadata.
- The rollback button is rendered as a destructive action (red, confirmation modal required) and is only visible to users with `ota:rollback` permission.

---

## UC-03 — Configure Alert Rule

**Brief Description**
A Fleet Manager or Platform Admin defines a threshold-based, anomaly-detection, or rate-of-change alert rule against device telemetry metrics. The rule is stored in the Rules Engine and evaluated in near-real-time as telemetry flows through the Kafka processing pipeline.

**Actors**
- Primary: Fleet Manager
- Secondary: Platform Admin, Developer/Integrator (via API), Operations Engineer (recipient)

**Preconditions**
1. The target device group or individual device exists and has published at least one telemetry message (schema registered in Schema Registry).
2. The Fleet Manager holds the `alert:write` permission.
3. The telemetry metric being targeted has a registered schema in the platform's Confluent-compatible Schema Registry.
4. At least one notification channel (email, SMS, webhook, PagerDuty) has been configured for the tenant.

**Postconditions**
1. An alert rule record exists in the Rules Engine database with status `ACTIVE`.
2. The Rules Engine Kafka Streams application has reloaded the rule set (hot reload within 10 seconds of rule creation).
3. A test evaluation is available showing the rule result against the last 5 minutes of historical telemetry.
4. An audit log record captures the rule creation with the author's identity and the full rule JSON payload.

**Main Success Scenario**
1. Fleet Manager opens Alerting → Create Rule and selects rule type `THRESHOLD`.
2. Fleet Manager selects the target scope (device group: `factory-floor-line-3`), metric name (`temperature_celsius`), condition (`GREATER_THAN`), threshold value (85.0), and evaluation window (5 minutes, any single sample).
3. Fleet Manager sets the notification channels: email to `ops-team@example.com` and PagerDuty service key `pd-svc-12345`, severity `HIGH`.
4. Fleet Manager configures the cooldown period (30 minutes) to suppress repeated alerts for the same device.
5. Fleet Manager optionally enables auto-resolve: if the condition is no longer met for 10 consecutive minutes, the alert closes automatically.
6. Fleet Manager saves the rule. The platform validates the rule JSON against the `AlertRule` schema and assigns a rule ID (`rule_{uuid}`).
7. The Alert Service persists the rule in PostgreSQL and publishes a `platform.alert.rule.created` event to Kafka topic `platform-events`.
8. The Rules Engine Kafka Streams application picks up the event, deserialises the rule, and injects it into the hot-reloadable rule set without restarting the processing topology.
9. The portal displays a rule preview showing the alert condition evaluated against the last 5 minutes of telemetry, with a green "No current violations" or an amber "Would have fired N times in the past 5 minutes" indicator.
10. The Fleet Manager activates the rule (status transitions from `DRAFT` to `ACTIVE`).

**Alternative Flows**

*AF-01: Anomaly detection rule*
At step 2, Fleet Manager selects rule type `ANOMALY_DETECTION`. They configure the baseline window (7 days), sensitivity level (medium: 2.5 standard deviations), and minimum sample count (20 samples). The Rules Engine uses a CUSUM algorithm applied to the sliding baseline computed by InfluxDB's `movingAverage()` Flux function.

*AF-02: Rate-of-change rule*
Fleet Manager selects `RATE_OF_CHANGE` rule type, specifying metric `battery_voltage`, change threshold (`-0.5V per hour`), and evaluation window (60 minutes). The Rules Engine computes the derivative using Kafka Streams' sliding window aggregation.

*AF-03: Composite rule with AND/OR conditions*
Fleet Manager constructs a rule with multiple conditions joined by `AND`: `temperature_celsius > 80 AND humidity_percent > 90`. The Rules Engine evaluates both conditions within the same evaluation window and fires only when both are simultaneously true.

*AF-04: Rule creation via REST API*
A Developer/Integrator submits `POST /api/v1/alert-rules` with a fully formed rule JSON body including OAuth 2.0 bearer token. The response includes the created rule ID and a HAL `_links.self` reference. The flow continues from step 7.

**Exception Flows**

*EX-01: Referenced metric schema not registered*
At step 6, the schema validation step queries the Schema Registry and finds no schema for the specified metric name. The platform returns `422 Unprocessable Entity` with error code `METRIC_SCHEMA_NOT_FOUND`. The user is directed to the metric catalog where they can register the schema.

*EX-02: Notification channel delivery failure*
After the rule fires and the Alert Service dispatches a notification, the email/webhook endpoint returns a non-2xx response. The Alert Service retries with exponential backoff (3 attempts, 30-second intervals). After all retries are exhausted, the alert is marked `NOTIFICATION_FAILED` and a platform-level operational alert is raised for the Operations Engineer.

*EX-03: Rules Engine hot-reload failure*
At step 8, the Rules Engine fails to parse the new rule (e.g., corrupted Kafka message). The Rules Engine logs the error, publishes a `platform.rules.reload.failed` event, and continues processing with the previous rule set. The Platform Admin receives an operational alert. The new rule remains in `DRAFT` status until the reload succeeds.

*EX-04: Cooldown period manipulation*
If a Fleet Manager attempts to set the cooldown to 0 seconds for a HIGH-severity rule, the validation layer enforces a minimum cooldown of 5 minutes to prevent notification flooding. A warning banner is shown in the portal.

**Business Rules Referenced**
- BR-040: Alert rules must specify at least one active notification channel before activation.
- BR-041: HIGH and CRITICAL severity alerts must have a minimum cooldown of 5 minutes.
- BR-042: Alert rule changes must be recorded in the audit log including the before and after state of the rule JSON.
- BR-045: Anomaly detection rules require at least 7 days of baseline data before activation.

**Non-Functional Requirements**
- Alert evaluation latency (telemetry ingestion to alert firing) must be under 3 seconds for threshold rules at the 99th percentile.
- The Rules Engine must support up to 10,000 active rules per tenant without exceeding 500 ms Kafka Streams processing lag.
- Rule hot reload must complete within 10 seconds of the `platform.alert.rule.created` event.

**UI/UX Notes**
- The rule builder uses a visual condition editor with metric auto-complete populated from the tenant's Schema Registry.
- The preview chart in step 9 is rendered inline using a lightweight time-series chart component (ECharts) showing the metric with alert threshold overlaid.
- Rule status badges use a traffic-light colour system: grey (DRAFT), green (ACTIVE/no fire), amber (ACTIVE/firing), red (ACTIVE/critical firing).

---

## UC-04 — Monitor Telemetry Dashboard

**Brief Description**
A Device Operator or Operations Engineer views near-real-time telemetry data from one or more devices through the platform's monitoring dashboard. The dashboard streams live data via WebSocket and supports ad-hoc historical queries against InfluxDB.

**Actors**
- Primary: Device Operator, Operations Engineer
- Secondary: Developer/Integrator (embeds dashboard widgets via iframe or SDK)

**Preconditions**
1. The user holds the `telemetry:read` permission scoped to the target device or group.
2. The target device(s) have published telemetry within the past 24 hours.
3. The WebSocket endpoint `wss://api.iot.platform/ws/v1/telemetry` is available.

**Postconditions**
1. The user has viewed current telemetry values and trend charts for the selected metrics.
2. No system state changes; this is a read-only use case.

**Main Success Scenario**
1. Device Operator navigates to the device detail page and selects the "Telemetry" tab.
2. The portal opens a WebSocket connection to `wss://api.iot.platform/ws/v1/telemetry` with a JWT Bearer token in the `Sec-WebSocket-Protocol` header.
3. The portal sends a subscription message: `{"action": "subscribe", "deviceId": "dev_abc123", "metrics": ["temperature_celsius", "battery_voltage", "rssi_dbm"]}`.
4. The Telemetry Service registers the subscription and immediately pushes the last known value for each metric from the Redis hot-path cache (max staleness: 5 seconds).
5. As new telemetry arrives from the device, the Telemetry Service fans out the messages to all active WebSocket subscriptions within 500 ms of Kafka consumption.
6. The portal renders live updating charts. Each metric panel shows: current value, sparkline (last 60 minutes), min/max/average for the current 1-hour window, and alert status indicator.
7. Device Operator selects a historical time range (last 24 hours) for one metric. The portal calls `GET /api/v1/devices/{deviceId}/telemetry?metric=temperature_celsius&start=2024-01-15T00:00:00Z&end=2024-01-15T23:59:59Z&resolution=5m` which queries InfluxDB using a Flux query with a `5m` aggregation window.
8. The historical data is rendered as a line chart alongside the live stream.
9. Device Operator closes the dashboard tab. The portal sends an unsubscribe message and the WebSocket connection is closed gracefully.

**Alternative Flows**

*AF-01: Fleet-level telemetry view*
Fleet Manager opens the fleet dashboard, which aggregates telemetry across all devices in a group. The WebSocket subscription includes a `groupId` parameter. The Telemetry Service fans out data for all group members. Aggregated statistics (p50/p95/p99 across the fleet) are computed server-side.

*AF-02: Telemetry export*
Device Operator clicks "Export" on the historical chart. The portal calls `POST /api/v1/telemetry/exports` with time range, device list, and format (`CSV` or `Parquet`). The export job runs asynchronously, and the user receives a download link via email when the export is ready (max wait: 10 minutes for up to 30-day exports).

**Exception Flows**

*EX-01: WebSocket connection dropped*
The portal implements automatic WebSocket reconnection with exponential backoff (base: 1 s, max: 30 s, jitter: ±500 ms). While disconnected, the portal displays a "Reconnecting…" banner. Upon reconnect, it re-sends the subscription message and fetches the gap data via REST API.

*EX-02: No telemetry data in selected range*
The InfluxDB query returns an empty result set. The portal displays "No data available for this time range" with a suggestion to widen the range or check the device's connectivity status.

**Business Rules Referenced**
- BR-050: Telemetry data is retained in InfluxDB for 30 days with 1-second resolution, then in TimescaleDB for 2 years with 5-minute continuous aggregates.
- BR-053: Telemetry access is tenant-scoped; cross-tenant telemetry reads are prohibited regardless of user role.

**Non-Functional Requirements**
- WebSocket push latency (Kafka consumption to browser rendering) must be under 500 ms at the 95th percentile.
- Historical query response for a single metric over 24 hours must complete in under 2 seconds.
- The dashboard must support 500 concurrent WebSocket connections per tenant without degradation.

**UI/UX Notes**
- Charts auto-scale Y-axis based on the data range with a 10% padding.
- Alert threshold lines are overlaid on metric charts when an active alert rule exists for the metric.
- The dashboard supports dark mode and is accessible to WCAG 2.1 AA standards.

---

## UC-05 — Execute Remote Command

**Brief Description**
A Device Operator or Developer/Integrator sends a structured command (reboot, log-capture, self-test, config-push, or custom) to an individual device. The platform delivers the command via MQTT and tracks execution status.

**Actors**
- Primary: Device Operator
- Secondary: Device Hardware, Developer/Integrator

**Preconditions**
1. The target device has status `ACTIVE` (connected to MQTT broker within the last 5 minutes).
2. The operator holds the `command:execute` permission for the target device or its parent group.
3. The command type is in the device model's allowed-command list (defined in the device profile).
4. No other command of the same type is pending for the device (de-duplication check).

**Postconditions**
1. A command record exists with terminal status `COMPLETED`, `FAILED`, or `TIMED_OUT`.
2. The command result payload (stdout/stderr, exit code, or structured response) is stored in the Command History store (PostgreSQL, 90-day retention).
3. A `platform.command.completed` event has been published to Kafka.
4. An audit log entry records the operator's identity, command type, parameters, and outcome.

**Main Success Scenario**
1. Device Operator navigates to the device detail page → Remote Commands → New Command.
2. Operator selects command type `LOG_CAPTURE` and parameters: `{"log_level": "DEBUG", "duration_seconds": 300, "component": "ota-agent"}`.
3. The portal calls `POST /api/v1/devices/{deviceId}/commands` with the command payload and a request timeout preference (default: 300 seconds).
4. The Command Service validates the command against the device's command profile, checks operator permissions, and performs the de-duplication check.
5. The Command Service creates a command record in PostgreSQL with status `PENDING` and a unique command ID (`cmd_{uuid}`).
6. The Command Service publishes the command to `cmd/{tenantId}/{deviceId}/execute` MQTT topic with QoS 1 and a message expiry interval of 300 seconds.
7. The MQTT broker delivers the command to the connected device. The device acknowledges receipt with a `PUBACK` (QoS 1 delivery confirmation).
8. The device executes the command and publishes the result to `dt/{tenantId}/{deviceId}/command-response` within the execution window, including the command ID, status (`SUCCESS`), and a base64-encoded log payload.
9. The Command Service consumes the response from Kafka, matches it to the pending command record by command ID, and transitions the record to `COMPLETED`.
10. The portal WebSocket subscription notifies the operator of completion. The operator clicks "View Result" to download the log archive.

**Alternative Flows**

*AF-01: Command to an offline device (queued)*
At step 6, if the device is offline, the MQTT broker retains the message (QoS 1, session persistence). The command record remains `PENDING` until the device reconnects. The operator sees a "Queued" indicator. If the device does not reconnect within the TTL window, the command transitions to `TIMED_OUT`.

*AF-02: Bulk command to device group*
A Fleet Manager calls `POST /api/v1/groups/{groupId}/commands` with the command payload. The Command Service creates individual command records for each device in the group (up to 1,000 devices; larger groups require pagination via async job). Commands are dispatched in batches of 100 with 100 ms intervals to avoid MQTT broker overload.

*AF-03: Command via REST API by Developer/Integrator*
Developer/Integrator submits the same `POST /api/v1/devices/{deviceId}/commands` request using an OAuth 2.0 bearer token. The response includes a `Location` header pointing to `GET /api/v1/commands/{commandId}` for polling status. Alternatively, the developer can subscribe to the `command.status.changed` webhook event.

**Exception Flows**

*EX-01: Device does not respond within TTL*
At step 8, no response is received within the TTL window. The Command Service transitions the command to `TIMED_OUT` and publishes a `platform.command.timedout` event. If this device has timed out on three consecutive commands within 1 hour, a `DEVICE_UNRESPONSIVE` alert is raised.

*EX-02: Command execution failure on device*
The device publishes a response with status `FAILED` and an error code (e.g., `INSUFFICIENT_STORAGE`). The Command Service records the failure with the error payload.

*EX-03: Command rejected by device firmware*
The device firmware rejects the command as unauthorised (the command type requires a higher firmware permission level than the device's current firmware supports). The device publishes `REJECTED` with reason `PERMISSION_DENIED_BY_DEVICE`.

*EX-04: Duplicate command detected*
At step 4, the de-duplication check finds a `PENDING` command of the same type. The API returns `409 Conflict` with the existing command ID. The operator can choose to cancel the existing command before resubmitting.

**Business Rules Referenced**
- BR-060: Remote commands must be delivered via QoS 1 MQTT to ensure at-least-once delivery.
- BR-061: Command payloads must not exceed 256 KB.
- BR-062: All remote command executions must be logged in the audit trail with the full command parameters.
- BR-065: Operators may not execute `FACTORY_RESET` or `DECOMMISSION` commands without Fleet Manager co-approval.

**Non-Functional Requirements**
- Command delivery latency (API submission to MQTT broker publish) must be under 500 ms.
- Command response tracking must support 50,000 concurrent pending commands per tenant.
- Command history must be queryable with sub-second response for the last 90 days.

**UI/UX Notes**
- Command result payloads larger than 10 KB are stored in Object Storage and presented as a download link rather than inline text.
- The command status indicator uses animated icons: spinning clock (PENDING), green checkmark (COMPLETED), red X (FAILED), grey hourglass (TIMED_OUT).

---

## UC-06 — Integrate via SDK

**Brief Description**
A Developer/Integrator connects an external application to the platform using the REST API, MQTT API, WebSocket streaming, or the platform's officially supported SDKs (Python, JavaScript, Java, Go). They generate API credentials, register event subscriptions, and access device data programmatically.

**Actors**
- Primary: Developer/Integrator
- Secondary: Platform Admin (credential approval for production environments)

**Preconditions**
1. The developer has a valid platform account with `developer` role in the target tenant.
2. The tenant has an active API subscription tier that includes the requested API surface area.
3. The developer has read the API changelog and confirmed they are integrating against a stable API version (v1 or v2; v0 is deprecated).

**Postconditions**
1. The developer has obtained OAuth 2.0 client credentials (`client_id` + `client_secret`) or an API key.
2. At least one successful API call has been made and logged.
3. If webhooks are configured, at least one test delivery has been sent and acknowledged.

**Main Success Scenario**
1. Developer navigates to Settings → API Access → Create Client Application.
2. Developer enters application name, description, and requested OAuth 2.0 scopes (`telemetry:read`, `device:read`, `command:execute`).
3. Platform generates `client_id` and `client_secret` and presents them once (secret not recoverable after this screen).
4. Developer exchanges credentials for an access token via `POST https://auth.iot.platform/oauth2/token` (RFC 6749 §4.4 client credentials grant). Token TTL: 3600 seconds.
5. Developer calls `GET /api/v1/devices?groupId={groupId}` with the bearer token. The API gateway validates the token, checks scopes, and returns a paginated device list (HAL+JSON, page size default 50).
6. Developer subscribes to the `device.telemetry.received` webhook event via `POST /api/v1/webhooks` with their HTTPS endpoint URL and a shared HMAC-SHA256 secret.
7. The platform sends a test delivery to the webhook URL with event type `webhook.test` and expects a 200 response within 10 seconds.
8. Developer reads the OpenAPI 3.1 specification from `GET /api/v1/openapi.json` and generates a typed client using their SDK generator of choice.
9. Developer streams live telemetry by opening a WebSocket connection to `wss://api.iot.platform/ws/v1/telemetry` and subscribing to a device group.

**Alternative Flows**

*AF-01: Using the official Python SDK*
Developer installs `pip install iot-platform-sdk`. The SDK handles OAuth 2.0 token refresh, WebSocket reconnection, and Kafka consumer group management behind a simple event-driven API. Developer writes: `client = IotPlatformClient(client_id, client_secret, tenant_id)` and `client.on_telemetry(callback_fn)`.

*AF-02: MQTT direct integration*
Developer uses a standard MQTT client library (e.g., Eclipse Paho) to connect to `mqtts://api.iot.platform:8883` using an API-key-derived MQTT username/password pair. They subscribe to `dt/{tenantId}/+/telemetry` to receive all tenant telemetry.

**Exception Flows**

*EX-01: Token expiry during long-running session*
The SDK automatically refreshes the token 60 seconds before expiry. If the refresh fails (network issue), the SDK queues requests and retries the refresh with exponential backoff. After 5 failed refresh attempts, the SDK raises an `AuthenticationExpiredError`.

*EX-02: Webhook endpoint returns non-200*
The platform retries webhook delivery with exponential backoff: 1 min, 5 min, 30 min, 2 h, 24 h. After 5 failed deliveries, the webhook is marked `SUSPENDED` and the developer receives an email notification.

*EX-03: Rate limit exceeded*
The API gateway enforces per-client rate limits (default: 1,000 requests/minute). When exceeded, the gateway returns `429 Too Many Requests` with a `Retry-After` header. The SDK honours the `Retry-After` value and pauses request dispatch.

*EX-04: Scope mismatch*
Developer attempts to call `POST /api/v1/devices/{deviceId}/commands` but the token lacks `command:execute` scope. The API returns `403 Forbidden` with error code `INSUFFICIENT_SCOPE`. The developer must re-generate credentials with the required scope.

**Business Rules Referenced**
- BR-070: API client secrets must be stored hashed (Argon2id) in the database; the plaintext is shown only once at creation time.
- BR-071: OAuth 2.0 access tokens must have a maximum TTL of 3,600 seconds.
- BR-072: Webhook endpoints must use HTTPS with a valid TLS certificate; HTTP endpoints are rejected.
- BR-075: API rate limits are enforced per client ID and are configurable per tenant subscription tier.

**Non-Functional Requirements**
- REST API p99 response time must be under 200 ms for read operations and under 500 ms for write operations.
- WebSocket streaming must support 10,000 concurrent connections per tenant cluster.
- SDK token refresh must complete within 2 seconds under normal network conditions.

**UI/UX Notes**
- The API credentials page shows a masked secret with a copy-to-clipboard button and a one-time reveal button.
- The OpenAPI documentation is rendered interactively using Swagger UI at `/docs/api` with a built-in "Try it out" feature that uses the developer's current session token.

---

## UC-07 — Revoke Device Certificate

**Brief Description**
Security Officer revokes an operational X.509 certificate for a device that has been compromised, decommissioned, or whose certificate has expired. The Certificate Service updates the CRL, notifies EMQX to disconnect the device, and publishes an audit event.

**Actors**
- Primary: Security Officer
- Secondary: Platform Admin

**Preconditions**
1. Security Officer holds the `certificate:revoke` permission.
2. A valid operational certificate exists for the device with status `ACTIVE`.
3. A revocation reason is provided (RFC 5280 CRLReason: `keyCompromise`, `cessationOfOperation`, `superseded`, `affiliationChanged`, or `unspecified`).

**Main Success Scenario**
1. Security Officer navigates to Certificate Management → Device Certificates, searches for the device, and selects "Revoke Certificate."
2. Security Officer selects revocation reason `keyCompromise` and enters an optional comment.
3. The Certificate Service updates the certificate status to `REVOKED` in PostgreSQL, adds the certificate serial number to the CRL, and triggers a CRL re-publication to the configured CDN URL (`https://crl.iot.platform/tenant/{tenantId}.crl`).
4. The Certificate Service calls EMQX's management API (`DELETE /api/v5/clients/{clientId}`) to immediately disconnect the device.
5. The Certificate Service publishes a `platform.certificate.revoked` event to Kafka.
6. The Device Registry record for the device is updated with status `CERTIFICATE_REVOKED` and the device is prevented from reconnecting until a new certificate is issued.
7. An audit log entry is created with the Security Officer's identity, timestamp, certificate serial number, and revocation reason.

**Key Alternative Flows**
- *Bulk revocation*: Security Officer can revoke all certificates for a compromised manufacturer batch by uploading a serial number list. The Certificate Service processes each revocation atomically within a database transaction.
- *OCSP update*: In addition to CRL update, the Certificate Service sends an OCSP status update to the configured OCSP responder so that devices performing OCSP stapling receive immediate revocation status.

---

## UC-08 — Decommission Device

**Brief Description**
A Fleet Manager or Platform Admin permanently removes a device from the platform. All device data is retained for audit and historical analysis per the data retention policy, but the device can no longer connect or publish telemetry.

**Preconditions**
1. The device has status `PROVISIONED`, `ACTIVE`, or `CERTIFICATE_REVOKED`.
2. The actor holds `device:decommission` permission.
3. A decommission reason is required.

**Main Success Scenario**
1. Actor submits `POST /api/v1/devices/{deviceId}/decommission` with `{"reason": "hardware_failure", "comment": "..."}`.
2. The Device Service revokes the operational certificate (calls Certificate Service internally), disconnects the device from EMQX, and sets the Device Registry status to `DECOMMISSIONED`.
3. The device is removed from all group memberships. Pending commands are cancelled. Active alert rules targeting only this device are deactivated.
4. A `platform.device.decommissioned` event is published to Kafka. Telemetry data is retained in InfluxDB/TimescaleDB per the tenant's retention policy (default: 2 years).
5. An audit entry is created.

**Key Alternative Flows**
- *Bulk decommission*: Actor uploads a CSV of device IDs. The platform processes each asynchronously and sends a completion report.
- *Scheduled decommission*: Actor sets a future decommission date. The platform sends a device-level warning command 24 hours before the scheduled date.

---

## UC-09 — Create Device Group

**Brief Description**
A Fleet Manager defines a logical group to organise devices by geography, device type, firmware cohort, or business unit. Groups are the primary targeting unit for OTA deployments, alert rules, and fleet policies.

**Preconditions**
1. The Fleet Manager holds `group:write` permission.
2. The group name is unique within the tenant (case-insensitive).

**Main Success Scenario**
1. Fleet Manager calls `POST /api/v1/groups` with `{"name": "factory-a-line-3", "tags": {"location": "factory-a", "line": "3"}, "deviceProfileId": "dp_industrial_v2"}`.
2. The Group Service validates the name uniqueness, creates the group record, and publishes `platform.group.created` to Kafka.
3. Fleet Manager assigns devices to the group via `POST /api/v1/groups/{groupId}/members` (individual or bulk).
4. The group becomes immediately available as a target in OTA deployment, alert rule, and command APIs.

**Key Alternative Flows**
- *Dynamic group via tag query*: Fleet Manager defines a group with a tag-based membership rule (e.g., `location=factory-a AND firmware_version<2.0`). Membership is evaluated dynamically at query time.

---

## UC-10 — Schedule OTA Rollout

**Brief Description**
A Fleet Manager creates an OTA deployment job with a future start time and a multi-wave rollout schedule, including maintenance windows, canary percentages, and per-wave health thresholds.

**Preconditions**
1. Firmware binary has status `APPROVED`.
2. Target device group exists and contains at least one device.
3. Fleet Manager holds `ota:deploy` permission.

**Main Success Scenario**
1. Fleet Manager creates a deployment with start time 24 hours in the future, canary at 2%, waves at 10%/30%/60%/100% with 1-hour intervals, failure threshold 5%, and maintenance window 22:00–06:00 UTC.
2. The OTA Service schedules the job and stores the wave plan. At the scheduled start time (within the maintenance window), the canary wave is dispatched.
3. Each subsequent wave is automatically dispatched after the health check passes and the wave interval elapses, but only if the current time falls within the maintenance window. Otherwise, dispatch is deferred to the next maintenance window.

---

## UC-11 — View Audit Log

**Brief Description**
Security Officer or Platform Admin queries the immutable audit log for security investigations, compliance audits, and operational troubleshooting.

**Preconditions**
1. Actor holds `audit:read` permission.
2. The audit log service is available.

**Main Success Scenario**
1. Actor calls `GET /api/v1/audit-logs?entityType=DEVICE&entityId={deviceId}&start=2024-01-01T00:00:00Z&end=2024-01-31T23:59:59Z&page=1&size=100`.
2. The Audit Service queries the append-only PostgreSQL `audit_events` table (partitioned by month) and returns the results with event type, actor identity, source IP, entity affected, before/after state hash, and timestamp.
3. Actor can export the filtered results as PDF or JSON for submission to the compliance team.
4. For IEC 62443-2-1 compliance reporting, a pre-built report template is available at `GET /api/v1/audit-logs/reports/iec-62443`.

---

## Cross-Cutting Concerns

### Authentication and Authorisation

All API use cases require a valid JWT (issued by the platform's OIDC provider) or OAuth 2.0 bearer token. The JWT contains `tenant_id`, `user_id`, `role`, and explicit `permissions` claims. Role-based defaults are expanded to permission sets at token issuance time. The API gateway validates the JWT signature (RS256, key ID matched from JWKS endpoint) and enforces scope requirements before routing to downstream services. Device-originated MQTT connections are authenticated via mutual TLS (client certificate validation against the tenant's operational CA).

### Idempotency

All write API operations accept an `Idempotency-Key` header (UUID v4). The API gateway stores the key and response in a Redis cache (TTL: 24 hours) and returns the cached response for duplicate requests. This is critical for OTA deployment creation and certificate revocation to prevent double-execution under network retry conditions.

### Audit Logging

Every state-changing operation across all use cases writes a structured audit event to the `platform.audit` Kafka topic, which is consumed by the Audit Service and persisted to an append-only PostgreSQL table. Audit records include: event type, actor identity (user ID or device ID), tenant ID, source IP, target entity (type + ID), action, before-state hash (SHA-256 of the previous record), and after-state hash. Audit records are immutable; deletion is not supported.

### Multi-Tenancy Isolation

All use cases are scoped to a single tenant. Tenant isolation is enforced at the API gateway (JWT claim check), at the database layer (row-level security policies on all PostgreSQL tables), at the Kafka layer (topic-level ACLs using tenant-prefixed topic names), at the MQTT layer (EMQX ACL rules using `{tenantId}` in topic patterns), and at the InfluxDB layer (separate bucket per tenant).

### Rate Limiting and Quotas

API rate limiting is enforced per `client_id` using a sliding window counter in Redis. MQTT message rate limiting is enforced by EMQX's built-in rate limiter per client connection (`rate_limit.max_conn_rate: 5000 msgs/s` globally, `1000 msgs/s` per device by default). Quota breaches at the tenant level (device count, message volume, storage) trigger `platform.tenant.quota.warning` events at 80% and `platform.tenant.quota.exceeded` at 100%.

### Error Response Format

All REST API error responses follow the RFC 7807 Problem Details format:

```json
{
  "type": "https://iot.platform/errors/DEVICE_NOT_FOUND",
  "title": "Device Not Found",
  "status": 404,
  "detail": "No device with ID 'dev_abc123' exists in tenant 'tenant_xyz'.",
  "instance": "/api/v1/devices/dev_abc123",
  "traceId": "01J2K3M4N5P6Q7R8S9T0"
}
```
