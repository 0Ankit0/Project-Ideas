# User Stories — IoT Device Management Platform

## Overview

This document captures the functional requirements for the IoT Device Management Platform as user stories. Stories follow the format: **As a [role], I want to [action], so that [benefit].**

### Roles

| Role | Description |
|------|-------------|
| Platform Admin | Manages the platform itself: tenants, global settings, system health |
| Device Engineer | Integrates and provisions physical devices onto the platform |
| Fleet Manager | Oversees groups of devices, monitors health, schedules operations |
| Security Officer | Enforces security policies, manages certificates and access controls |
| Operations Engineer | Monitors live telemetry, responds to alerts, runs diagnostics |
| Developer | Builds applications on top of the platform APIs and SDKs |

---

## Device Provisioning

### US-001
- **ID:** US-001
- **Role:** Device Engineer
- **Story:** As a Device Engineer, I want to register a new device by supplying its serial number and hardware model, so that the platform creates a unique device identity and credentials before deployment.
- **Acceptance Criteria:**
  - Device record is created with a globally unique `deviceId` upon successful registration.
  - Platform generates an X.509 certificate and private key for the device, returned in the API response only once.
  - Attempting to register the same serial number a second time returns HTTP 409 Conflict.
  - Device status is set to `PENDING` until the device connects for the first time.

### US-002
- **ID:** US-002
- **Role:** Device Engineer
- **Story:** As a Device Engineer, I want to bulk-provision up to 10,000 devices via a CSV upload, so that I can on-board large production batches without making individual API calls.
- **Acceptance Criteria:**
  - CSV upload endpoint accepts files up to 50 MB.
  - Platform processes the file asynchronously and returns a job ID immediately.
  - A downloadable result file is available once processing is complete, with per-row success/failure status.
  - Rows with invalid data are skipped and reported; valid rows are provisioned successfully.

### US-003
- **ID:** US-003
- **Role:** Device Engineer
- **Story:** As a Device Engineer, I want to associate a device with a specific firmware version at provisioning time, so that the device boots with a known-good baseline without requiring an immediate OTA update.
- **Acceptance Criteria:**
  - Firmware version reference is stored in the device record.
  - If the specified firmware version does not exist in the firmware registry, the provisioning request is rejected with HTTP 422.
  - The device's desired shadow state is initialized with the specified firmware version.

### US-004
- **ID:** US-004
- **Role:** Platform Admin
- **Story:** As a Platform Admin, I want to decommission a device and revoke all its credentials, so that retired hardware cannot reconnect to the platform.
- **Acceptance Criteria:**
  - Decommissioned device certificate is added to the CRL within 60 seconds.
  - Active MQTT sessions for the device are terminated immediately upon decommission.
  - Device status is set to `DECOMMISSIONED` and cannot transition to any other state.
  - All pending OTA jobs targeting the decommissioned device are cancelled automatically.

### US-005
- **ID:** US-005
- **Role:** Device Engineer
- **Story:** As a Device Engineer, I want to assign a device to one or more logical groups at provisioning time, so that fleet-level policies and OTA campaigns apply automatically.
- **Acceptance Criteria:**
  - A device can belong to a maximum of 20 groups simultaneously.
  - Group membership is reflected immediately in group-level fleet dashboards.
  - Removing a device from a group does not delete the device record.

---

## Fleet Management

### US-006
- **ID:** US-006
- **Role:** Fleet Manager
- **Story:** As a Fleet Manager, I want to view a real-time dashboard showing the online/offline ratio, firmware distribution, and alert counts across my entire fleet, so that I can assess overall fleet health at a glance.
- **Acceptance Criteria:**
  - Dashboard refreshes automatically every 30 seconds without a full page reload.
  - Online/offline status is based on last heartbeat within a configurable window (default 5 minutes).
  - Firmware distribution chart updates within 2 minutes of a successful OTA update.
  - Alert count badge links to a filtered alert list.

### US-007
- **ID:** US-007
- **Role:** Fleet Manager
- **Story:** As a Fleet Manager, I want to create dynamic device groups using tag-based queries, so that devices matching certain criteria are automatically included or excluded as their attributes change.
- **Acceptance Criteria:**
  - Query syntax supports AND/OR operators and tag key-value matching.
  - Dynamic group membership is re-evaluated every 60 seconds.
  - Static and dynamic groups coexist; a device can belong to both types simultaneously.

### US-008
- **ID:** US-008
- **Role:** Fleet Manager
- **Story:** As a Fleet Manager, I want to export a CSV report of all devices with their last-seen timestamp, firmware version, and connection status, so that I can perform offline analysis or compliance reporting.
- **Acceptance Criteria:**
  - Export is generated asynchronously; user is notified via email when ready.
  - CSV includes: deviceId, serialNumber, firmwareVersion, status, lastSeenAt, groupNames.
  - Export respects the user's current filter and search context.

### US-009
- **ID:** US-009
- **Role:** Fleet Manager
- **Story:** As a Fleet Manager, I want to search for devices by serial number, tag, firmware version, or location metadata, so that I can quickly locate specific devices during incident response.
- **Acceptance Criteria:**
  - Search returns results within 500 ms for fleets up to 100,000 devices.
  - Partial string matching is supported for serial number and tag values.
  - Results display device online status and most recent telemetry timestamp.

### US-010
- **ID:** US-010
- **Role:** Fleet Manager
- **Story:** As a Fleet Manager, I want to apply a tag to all devices in a selected group in a single operation, so that I can quickly label devices for a campaign or maintenance window.
- **Acceptance Criteria:**
  - Bulk tag operation applies to all devices within the group at time of execution.
  - Each device may have up to 50 tag key-value pairs.
  - Existing tags with the same key are overwritten; all other tags remain unchanged.

---

## Device Shadow / Digital Twin

### US-011
- **ID:** US-011
- **Role:** Device Engineer
- **Story:** As a Device Engineer, I want to read the device shadow document to see the last reported state and the desired state set by operators, so that I can determine whether the device is in sync.
- **Acceptance Criteria:**
  - Shadow document returns three sections: `reported`, `desired`, and `delta`.
  - `delta` contains only keys where `desired` and `reported` differ.
  - Shadow reads are served from a low-latency cache with a maximum staleness of 5 seconds.

### US-012
- **ID:** US-012
- **Role:** Operations Engineer
- **Story:** As an Operations Engineer, I want to update the desired state of a device shadow, so that I can change configuration parameters like sampling rate or alert thresholds without re-flashing the device.
- **Acceptance Criteria:**
  - Desired state updates are published to the device's MQTT shadow delta topic within 2 seconds.
  - Shadow document version is incremented on every update; stale updates are rejected with a version conflict error.
  - Changes are logged with the operator's identity and a timestamp for auditability.

### US-013
- **ID:** US-013
- **Role:** Developer
- **Story:** As a Developer, I want to subscribe to shadow delta events via WebSocket, so that my application can react to configuration changes in real time without polling.
- **Acceptance Criteria:**
  - WebSocket connection receives a delta event within 3 seconds of a desired state change.
  - Events include the full delta object, the device ID, and the shadow version number.
  - Clients that reconnect receive any missed delta events from the last 24 hours.

---

## Telemetry Ingestion

### US-014
- **ID:** US-014
- **Role:** Device Engineer
- **Story:** As a Device Engineer, I want devices to publish telemetry payloads over MQTT using a defined topic schema, so that all sensor readings are ingested consistently into the time-series database.
- **Acceptance Criteria:**
  - Platform accepts JSON telemetry payloads up to 256 KB per message.
  - Telemetry is stored in the time-series database within 5 seconds of receipt under normal load.
  - Malformed JSON payloads are dropped and a parse-error counter is incremented for the device.

### US-015
- **ID:** US-015
- **Role:** Operations Engineer
- **Story:** As an Operations Engineer, I want to query historical telemetry for a specific device over a custom time range, so that I can investigate anomalies or produce compliance reports.
- **Acceptance Criteria:**
  - Query API supports `start`, `end`, `resolution`, and `fields` parameters.
  - Response is returned within 2 seconds for queries spanning up to 30 days at 1-minute resolution.
  - Data is downsampled server-side when `resolution` is coarser than the stored granularity.

### US-016
- **ID:** US-016
- **Role:** Developer
- **Story:** As a Developer, I want to stream live telemetry for a device group via Server-Sent Events, so that I can build real-time dashboards without implementing a WebSocket client.
- **Acceptance Criteria:**
  - SSE stream delivers events within 1 second of MQTT ingestion under normal load.
  - Stream supports filtering by field names so clients receive only the metrics they need.
  - Server sends a keep-alive comment every 15 seconds to prevent proxy timeouts.

### US-017
- **ID:** US-017
- **Role:** Fleet Manager
- **Story:** As a Fleet Manager, I want to configure per-device telemetry retention policies, so that high-value devices retain data for 2 years while low-cost sensors retain data for only 30 days.
- **Acceptance Criteria:**
  - Retention policy is configurable at the device level and inheritable from a group.
  - Data older than the retention period is purged automatically within a 24-hour window.
  - Retention policy changes are not retroactive to already-stored data unless explicitly triggered.

---

## OTA Firmware Updates

### US-018
- **ID:** US-018
- **Role:** Fleet Manager
- **Story:** As a Fleet Manager, I want to upload a new firmware binary and associate it with a hardware model, so that the artifact is available for OTA deployment campaigns.
- **Acceptance Criteria:**
  - Firmware uploads are validated for a SHA-256 checksum match before storage.
  - Platform rejects binaries larger than 500 MB.
  - Uploaded firmware versions are immutable; they cannot be overwritten once published.

### US-019
- **ID:** US-019
- **Role:** Fleet Manager
- **Story:** As a Fleet Manager, I want to create an OTA deployment campaign targeting a device group with a configurable rollout percentage, so that I can safely roll out firmware using a canary strategy.
- **Acceptance Criteria:**
  - Rollout percentage specifies what fraction of the target group receives the update in the first wave.
  - Campaign can be paused, resumed, or rolled back by an authorized user.
  - Dashboard shows per-device job status: `QUEUED`, `DOWNLOADING`, `APPLYING`, `SUCCEEDED`, `FAILED`.

### US-020
- **ID:** US-020
- **Role:** Operations Engineer
- **Story:** As an Operations Engineer, I want to monitor an active OTA campaign in real time and abort it if the failure rate exceeds a threshold, so that a bad firmware release does not brick the entire fleet.
- **Acceptance Criteria:**
  - Campaign dashboard shows failure rate as a live percentage.
  - Configurable auto-abort threshold (e.g., >5% failure rate) automatically pauses the campaign.
  - When a campaign is aborted, no additional devices receive the update.

### US-021
- **ID:** US-021
- **Role:** Device Engineer
- **Story:** As a Device Engineer, I want devices to verify the firmware checksum and digital signature before applying an update, so that corrupted or tampered binaries are never applied.
- **Acceptance Criteria:**
  - Device reports `CHECKSUM_MISMATCH` job status if the SHA-256 hash does not match.
  - Platform signs firmware binaries with a private key; devices verify using the embedded public key.
  - A failed verification does not overwrite the currently running firmware.

---

## Remote Commands

### US-022
- **ID:** US-022
- **Role:** Operations Engineer
- **Story:** As an Operations Engineer, I want to send a remote reboot command to a specific device, so that I can recover a device stuck in an error state without dispatching a field technician.
- **Acceptance Criteria:**
  - Command is delivered to the device via MQTT within 5 seconds when the device is online.
  - Device acknowledges command receipt; platform records the acknowledgement timestamp.
  - If device is offline, command is queued and delivered upon next connection (TTL: 24 hours).

### US-023
- **ID:** US-023
- **Role:** Developer
- **Story:** As a Developer, I want to send custom parameterized commands to devices and receive structured responses via the REST API, so that I can trigger device-side actions from my application without managing MQTT directly.
- **Acceptance Criteria:**
  - Command payload is a JSON object with a `name` field and an optional `params` object.
  - Platform returns a `commandId`; the caller can poll or subscribe for the device's response.
  - Command responses are retained for 7 days.

---

## Rules Engine and Alerts

### US-024
- **ID:** US-024
- **Role:** Operations Engineer
- **Story:** As an Operations Engineer, I want to define threshold-based alert rules on telemetry fields, so that I am notified automatically when a sensor reading exceeds a safe operating boundary.
- **Acceptance Criteria:**
  - Rules support conditions: `>`, `<`, `>=`, `<=`, `==`, `!=`.
  - Rules can be applied to a single device or an entire group.
  - Alert is triggered within 10 seconds of the offending telemetry message being ingested.

### US-025
- **ID:** US-025
- **Role:** Operations Engineer
- **Story:** As an Operations Engineer, I want alert rules to support a sustained-condition duration window, so that transient spikes do not generate false-positive alerts.
- **Acceptance Criteria:**
  - Duration window is configurable in seconds with a minimum of 30 seconds.
  - Alert fires only after the condition is continuously satisfied throughout the window.
  - If the condition clears before the window expires, no alert is generated and the timer resets.

### US-026
- **ID:** US-026
- **Role:** Fleet Manager
- **Story:** As a Fleet Manager, I want to configure alert notification channels (email, Slack webhook, PagerDuty) per alert rule, so that the right team is notified through the right channel.
- **Acceptance Criteria:**
  - At least three notification channels are supported: email, generic HTTP webhook, and PagerDuty.
  - Each rule can have multiple notification channels configured.
  - Platform retries failed webhook deliveries up to 3 times with exponential backoff.

### US-027
- **ID:** US-027
- **Role:** Operations Engineer
- **Story:** As an Operations Engineer, I want to view an alert history with filtering by device, rule, severity, and time range, so that I can investigate recurring issues and audit platform behaviour.
- **Acceptance Criteria:**
  - Alert history is retained for 90 days.
  - Filtering by device, rule name, severity (INFO, WARNING, CRITICAL), and time range is supported.
  - Alerts can be acknowledged or suppressed with an operator note.

---

## Security and Certificates

### US-028
- **ID:** US-028
- **Role:** Security Officer
- **Story:** As a Security Officer, I want to view the certificate lifecycle for all devices, so that I can maintain an up-to-date inventory and avoid certificate-related outages.
- **Acceptance Criteria:**
  - Certificate inventory table shows deviceId, commonName, issuedAt, expiresAt, and status (ACTIVE, REVOKED, EXPIRED).
  - Table supports filtering by expiry date range and status.
  - Certificates expiring within 30 days are highlighted and included in a weekly summary email.

### US-029
- **ID:** US-029
- **Role:** Security Officer
- **Story:** As a Security Officer, I want to revoke a compromised device certificate with a reason code and immediately publish an updated CRL, so that the compromised device cannot authenticate.
- **Acceptance Criteria:**
  - CRL is updated and distributed within 60 seconds of a revocation request.
  - Reason codes follow RFC 5280 (e.g., keyCompromise, cessationOfOperation).
  - Active MQTT sessions using the revoked certificate are terminated within 30 seconds.

---

## RBAC and Access Control

### US-030
- **ID:** US-030
- **Role:** Platform Admin
- **Story:** As a Platform Admin, I want to define custom roles with fine-grained permissions on platform resources, so that the principle of least privilege is enforced across all user accounts.
- **Acceptance Criteria:**
  - Permissions are defined at the resource-action level (e.g., devices:write, ota:deploy).
  - A role can be assigned to a user globally or scoped to a specific device group.
  - Removing a permission from a role takes effect on the next API request without requiring re-authentication.

### US-031
- **ID:** US-031
- **Role:** Platform Admin
- **Story:** As a Platform Admin, I want to enforce multi-factor authentication for all users with administrative roles, so that privileged accounts are protected against credential theft.
- **Acceptance Criteria:**
  - MFA enforcement is configurable at the tenant level.
  - TOTP (RFC 6238) and hardware security keys (FIDO2/WebAuthn) are supported.
  - Users who have not enrolled in MFA are redirected to the enrollment flow upon first login after the policy is enabled.

### US-032
- **ID:** US-032
- **Role:** Developer
- **Story:** As a Developer, I want to create service account API keys scoped to specific resources and actions, so that my application can access only the platform resources it needs.
- **Acceptance Criteria:**
  - API keys can be scoped to one or more device groups and specific permission sets.
  - API keys support an optional expiry date.
  - API key last-used timestamp is recorded to facilitate audit and key rotation policies.

---

## Diagnostics and Observability

### US-033
- **ID:** US-033
- **Role:** Operations Engineer
- **Story:** As an Operations Engineer, I want to retrieve the last 500 lines of device logs via the platform API, so that I can diagnose a misbehaving device without needing physical access.
- **Acceptance Criteria:**
  - Device log lines are uploaded by the device SDK over MQTT and stored server-side.
  - Log lines are tagged with device-local timestamp and severity level.
  - Logs are available for query within 10 seconds of being uploaded by the device.

### US-034
- **ID:** US-034
- **Role:** Platform Admin
- **Story:** As a Platform Admin, I want to view platform-level metrics (message ingestion rate, API latency percentiles, error rates) on an operations dashboard, so that I can detect degraded performance early.
- **Acceptance Criteria:**
  - Dashboard displays p50, p95, and p99 API latency updated every minute.
  - Message ingestion rate is shown as a time-series chart with 1-minute granularity.
  - An alert is raised automatically if the p99 API latency exceeds 2 seconds for 3 consecutive minutes.
