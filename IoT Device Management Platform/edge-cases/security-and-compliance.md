# Edge Cases: Security and Compliance

This document catalogs security-sensitive edge cases and compliance-related scenarios for the IoT Device Management Platform. Each case identifies the risk level, describes how the threat is detected, defines the platform's response actions, and specifies the long-term mitigation controls.

---

## Compromised Device Certificate Used to Impersonate Device and Inject False Telemetry

**Risk Level: Critical**

**Scenario**

An attacker extracts the private key from a compromised physical device (via hardware attack, firmware extraction, or supply chain compromise) and uses it to establish a separate MQTT connection impersonating the legitimate device. The attacker injects crafted telemetry readings—falsely reporting normal operating conditions on a device that is actually malfunctioning—to suppress legitimate alerts.

**Detection**

1. The platform detects concurrent MQTT sessions sharing the same `clientId` (device ID). MQTT protocol enforces exclusive session ownership, so the legitimate device's session is disconnected when the attacker connects. The legitimate device then attempts to reconnect, causing rapid session churn that triggers a `SessionConflict` security alert.
2. Telemetry anomaly detection identifies statistically improbable readings—telemetry that is too perfect (zero variance, exact round numbers, or values precisely at the "normal" threshold boundary) compared to the device's historical telemetry profile.
3. Geographic IP anomaly detection flags connections from the attacker's IP address if it resolves to a location geographically inconsistent with the device's registered deployment location.

**Response**

1. The compromised certificate is immediately revoked via the CA's revocation API, and the CRL is updated and pushed to the MQTT broker's revocation cache.
2. Both the attacker's session and the legitimate device's session are terminated.
3. A security incident is created with CRITICAL severity, including the compromised certificate fingerprint, the attacker's connection metadata (IP, connection timestamps), and the time window during which false telemetry may have been injected.
4. The telemetry data written during the potential compromise window is flagged as `Unverified` in the time-series database, and all dependent alert evaluations and historical reports based on that data are marked as potentially unreliable.
5. A new certificate is provisioned for the legitimate device through the certificate replacement workflow.

**Mitigation**

Device private keys should be generated and stored in a hardware security element (TPM, secure enclave, or dedicated crypto-chip) from which the key cannot be extracted. The platform requires hardware attestation tokens for devices in high-security classifications, making it impossible to impersonate the device without physical access to the secure element. Certificate pinning in the platform prevents certificates issued by external CAs from being accepted.

---

## Certificate Rotation During Active Device Session (Zero-Downtime Cert Renewal)

**Risk Level: Medium**

**Scenario**

A device's certificate is approaching its expiry date (30 days remaining) while the device is actively connected and publishing telemetry. Revoking the current certificate and issuing a new one would disconnect the device. The platform must renew the certificate without interrupting the device's MQTT session or causing a gap in telemetry.

**Detection**

The platform's certificate expiry monitoring job identifies certificates expiring within the renewal lead time (configurable, default: 30 days) on a daily scan. For actively connected devices, the system flags the need for a zero-downtime rotation.

**Response**

The platform implements a dual-certificate acceptance window for certificate rotation:
1. The new certificate is issued by the CA before the old certificate expires.
2. The new certificate's fingerprint is added to the device's trusted fingerprint list in the Device Registry while the old certificate remains active.
3. The device is notified of the pending rotation via its configuration topic. The notification includes the new certificate and private key, encrypted to the device's current session key.
4. The device installs the new certificate in its credential store and initiates a new MQTT connection using the new certificate while the old connection is still active.
5. The old connection is gracefully closed after the new connection is confirmed active.
6. The old certificate is revoked after the rotation confirmation is received.

**Mitigation**

Certificate renewal should be automated and triggered well before expiry to avoid the operational complexity of emergency rotation. The platform maintains a renewal queue and processes renewals in the background. For devices that cannot perform dual-connection rotation (resource-constrained devices), a maintenance window rotation approach is used: the device completes its current operation cycle, disconnects, renews the certificate, and reconnects.

---

## Attacker Replaying Old Telemetry Messages (Replay Attack Mitigation)

**Risk Level: High**

**Scenario**

An attacker captures authentic MQTT telemetry messages from a device's network traffic. Although the messages are encrypted with TLS, the attacker operates a man-in-the-middle on a compromised network segment and records the encrypted messages. The attacker later replays the captured messages to inject stale telemetry data, either to suppress current anomaly alerts (by replacing current abnormal readings with previously captured normal readings) or to trigger false alerts.

**Detection**

1. MQTT over TLS prevents message capture and replay at the transport layer—TLS session keys are ephemeral (using ECDHE), so captured ciphertext cannot be decrypted or replayed within a different TLS session.
2. At the application layer, each telemetry message includes a `messageId` (UUID v4) and a `timestamp`. The ingestion pipeline checks incoming message IDs against a short-lived deduplication cache (5-minute window using a Bloom filter) to detect replayed messages with the same message ID.
3. Telemetry timestamps outside the acceptable ingestion window (default: ±5 minutes from server time) are rejected as potentially replayed or clock-skewed messages.

**Response**

1. Detected replay attempts are logged to the security event stream with the source connection details.
2. Replayed messages are rejected and not written to the time-series database.
3. Excessive replay attempts from a single connection trigger automatic session termination and a security alert.

**Mitigation**

Mutual TLS with ephemeral key exchange (ECDHE) at the transport layer provides the primary replay defense. Application-layer defenses (message ID deduplication, timestamp validation) provide defense in depth for scenarios where the transport layer is compromised. Devices should use monotonically increasing sequence numbers in telemetry messages as an additional replay indicator—the ingestion pipeline can detect when a received sequence number is lower than the last observed sequence number from the same device.

---

## Device Attempting to Access Another Device's Shadow State (Authorization Bypass)

**Risk Level: High**

**Scenario**

A malicious device firmware (either intentionally crafted or compromised by an attacker) attempts to read or write the shadow state of a different device by constructing MQTT topic strings targeting the other device's shadow topics (e.g., `iot/devices/victim-device-id/shadow/desired`).

**Detection**

The MQTT broker enforces per-device topic authorization via a dynamic ACL policy. Each device's certificate CN field contains its device ID, and the broker evaluates topic ACLs by matching the device ID extracted from the TLS certificate against the device ID in the requested topic.

**Response**

1. The broker evaluates the topic authorization: device `attacker-device-id` is only authorized to publish/subscribe to topics containing its own device ID. Attempts to access `victim-device-id` topics result in an immediate `SUBACK` or `PUBACK` with the `Not Authorized` reason code.
2. The authorization failure is logged to the security event stream with the source device ID, the unauthorized topic, and the connection metadata.
3. If a device generates more than a configurable number of authorization failures within a time window (default: 5 failures per minute), the device is automatically suspended and an operator security alert is generated.
4. The incident is treated as a possible firmware compromise and the device is quarantined pending investigation.

**Mitigation**

Topic authorization policies are enforced at the broker level and cannot be circumvented by application-layer manipulation. The ACL policy evaluation is performed using the certificate CN rather than any client-provided claim, preventing an attacker from claiming a different device identity through the MQTT CONNECT packet.

---

## Firmware Signed With Expired Code-Signing Certificate

**Risk Level: High**

**Scenario**

The platform's firmware code-signing certificate expires. The firmware security team, unaware of the expiry, continues to sign new firmware binaries with the expired certificate. A firmware deployment is initiated and devices receive the firmware notification with the expired signature.

**Detection**

1. The platform's firmware upload endpoint validates the firmware signature as part of the upload acceptance process. Signatures from expired certificates are rejected at upload time with a structured error response identifying the certificate expiry date.
2. The certificate expiry monitoring job includes code-signing certificates in its monitoring scope and generates an operator alert when the signing certificate is within 60 days of expiry.

**Response**

1. The firmware binary with the expired signature is rejected at upload and not stored in the firmware repository.
2. Any firmware binaries that were signed with the expired certificate before the expiry was noticed are identified via a registry query and quarantined (marked as `IneligibleForDeployment`).
3. Active deployments referencing quarantined firmware are paused, and devices that have already downloaded but not installed the firmware are instructed to discard it.
4. A new code-signing certificate is issued and the firmware binaries must be re-signed with the new certificate before deployment can resume.

**Mitigation**

Code-signing certificates should have a validity period aligned to the platform's key rotation schedule (minimum 2 years). The signing process should be automated within the CI/CD pipeline with built-in certificate validity checks. Certificate expiry monitoring with a 60-day lead time provides sufficient runway for renewal without emergency procedures.

---

## GDPR Data Subject Request for Telemetry Data Tied to a Person's Device

**Risk Level: High (Regulatory)**

**Scenario**

A consumer IoT platform tenant receives a GDPR Subject Access Request (SAR) from a data subject who owns a personal health monitoring device. The data subject requests access to all telemetry data collected from their device. The tenant must fulfill the request within 30 days. The telemetry data is stored across a time-series database, object storage archives, analytics system exports, and SIEM event logs.

**Detection**

The tenant's platform administrator initiates a data subject request workflow in the platform's compliance management module, providing the data subject's identifier and the device ID(s) associated with their account.

**Response**

1. The compliance module generates a data inventory report: all platform subsystems where data associated with the specified device ID is stored (time-series DB, device shadow history, audit logs, firmware update history, alert history, command history).
2. An automated export job collects data from each subsystem, applying the following transformations:
   - Telemetry data: exported as CSV with device-reported timestamps, stream names, and field values.
   - Alert history: exported with alert details, timestamps, and notification delivery records.
   - Audit log entries: exported with operation type, timestamp, and operator identity (pseudonymized to protect platform operator privacy).
3. The export is packaged in a machine-readable format (JSON or CSV) and delivered to the tenant administrator via a secure download link with a 7-day expiry.
4. The compliance module records the SAR event in an immutable audit trail.
5. For the right to erasure (right to be forgotten), a data purge workflow is available that deletes or anonymizes data from all subsystems, subject to legal hold checks.

**Mitigation**

The platform's data model tags all records with a `deviceOwnerId` foreign key, enabling efficient cross-subsystem data subject queries without full table scans. Telemetry data that does not contain personally identifiable information (e.g., environmental sensor data from a non-personal device) may be classified as outside the GDPR scope, reducing compliance burden.

---

## Regulatory Audit Requiring Complete Audit Trail of All Device Commands

**Risk Level: High (Regulatory)**

**Scenario**

A regulated industry customer (pharmaceutical cold-chain monitoring) is subject to FDA 21 CFR Part 11 regulations requiring a complete, tamper-evident audit trail of all commands issued to devices that control regulated processes. The customer is audited by the FDA and must produce a complete command audit log for a 3-year retention period.

**Detection**

All device command operations are recorded in the Command Service's audit log at execution time, including: command type, target device ID, initiating operator identity, timestamp (UTC), command parameters, delivery status, and device acknowledgment with execution result. This logging is not optional and cannot be disabled.

**Response**

1. The platform's compliance module provides an audit log export API that supports time-range queries with cryptographic integrity verification: each log entry includes a hash chain linking it to the previous entry, enabling detection of log tampering or deletion.
2. Audit logs are stored in an append-only database partition with write-once characteristics; even platform administrators cannot modify or delete audit log entries.
3. The export includes a manifest file signed with the platform's audit integrity key, which auditors can verify independently.
4. The export format is compatible with common audit review tools and is documented in the platform's compliance documentation.

**Mitigation**

Audit log storage uses a write-once S3 bucket with Object Lock (WORM) to provide storage-level immutability. Audit log entries are replicated to a secondary region to ensure availability even in the event of a regional disaster affecting the primary region's storage. The platform's SOC 2 Type II certification covers audit log controls.

---

## Device in a Country With Data Sovereignty Requirements (Data Residency)

**Risk Level: High (Regulatory)**

**Scenario**

A healthcare IoT platform deploys patient monitoring devices in Germany. German data protection law (and the EU GDPR) requires that personal health data collected from these devices must be stored and processed within the European Economic Area (EEA). The platform's default configuration routes all telemetry to a US-East-1 region for processing.

**Detection**

Data residency violations are a configuration-level issue detected at provisioning time. When a device is provisioned, the Device Registry checks the device's `deploymentRegion` attribute against the platform's data residency policy map for the tenant.

**Response**

1. Devices provisioned with a `deploymentRegion` in a data-residency-constrained region are automatically assigned to a regional processing cluster in the appropriate jurisdiction (e.g., EU-West for EEA-constrained devices).
2. The MQTT connection endpoint advertised to the device during provisioning points to the regional broker cluster, ensuring that telemetry never transits a non-compliant region.
3. The time-series database, device shadow store, and audit log for constrained devices are provisioned in the regional cluster exclusively.
4. Cross-region replication is disabled for constrained tenants, or restricted to replication only within the approved region group.
5. The tenant's compliance dashboard shows a data residency compliance status for all device groups.

**Mitigation**

The platform's multi-region architecture provisions independent processing stacks per approved jurisdiction. Tenant onboarding includes a data residency configuration step where the tenant specifies their applicable regulatory regions. The platform enforces region constraints through infrastructure-level network policies (not just application-level routing), preventing accidental data egress.

---

## Side-Channel Attack via Timing of Command Responses

**Risk Level: Medium**

**Scenario**

An attacker with access to the platform's command response API observes that the time taken for a device to respond to a `queryDeviceConfig` command varies based on the presence or absence of specific configuration keys. By issuing many commands and measuring response times statistically, the attacker infers information about the device's configuration without having direct access to the configuration values.

**Detection**

This is a passive attack and does not generate obvious anomaly signals. Detection relies on auditing the rate and pattern of command submissions from specific API callers: unusually high volumes of identical command types from the same operator or API key may indicate a timing oracle attack.

**Response**

1. The Command Service applies a constant-time response policy: command responses are padded to a fixed latency window (e.g., the response is not returned until a minimum of 200ms has elapsed since the command was dispatched, regardless of actual processing time). This eliminates the timing signal.
2. Rate limiting on the command API prevents the statistical sampling volume required for a successful timing attack.
3. Unusual command patterns (same command type issued more than N times per minute to the same device) trigger an audit alert.

**Mitigation**

Command handlers on the device should be implemented to execute in constant time where possible, avoiding timing oracles at the device level. Access to sensitive device configuration commands should require elevated permissions and produce detailed audit log entries that enable post-hoc forensic analysis.

---

## Insider Threat: Platform Admin Exfiltrating Device Telemetry at Scale

**Risk Level: Critical**

**Scenario**

A malicious platform administrator uses their elevated access privileges to export bulk telemetry data for all devices across all tenants. The administrator uses the platform's data export API, making the export appear to be a legitimate routine operation. Over several days, they transfer multiple terabytes of sensitive device telemetry to an external storage endpoint.

**Detection**

1. The SIEM system correlates platform audit log events with data transfer volume metrics. A single administrator account generating export jobs that collectively transfer significantly more data than their normal pattern triggers a behavioral anomaly alert.
2. The platform's data loss prevention (DLP) policy enforces maximum export volume limits per operator per time period. Bulk export requests exceeding the limit require a secondary authorization from a different administrator (four-eyes principle).
3. All data export operations are logged with the destination endpoint, transferred data volume, and the initiating operator's identity. Exports to external (non-platform) endpoints are flagged for review.

**Response**

1. The anomaly alert triggers immediate account suspension (automated, pending investigation).
2. The security incident response team conducts a forensic review of the audit logs to determine the scope of the exfiltration: which tenants, which devices, what time range, and what volume of data was transferred.
3. Affected tenants are notified of the potential data breach according to breach notification obligations (GDPR 72-hour notification, etc.).
4. The export destination endpoint is recorded and shared with law enforcement if criminal action is warranted.

**Mitigation**

Platform administrators should operate under the principle of least privilege: break-glass access to bulk telemetry data requires a separate elevated access role that is granted time-limited and must be justified in a ticket. All break-glass accesses are reviewed by the security team in real time. Telemetry data in the database should be encrypted at rest using tenant-specific encryption keys managed by the tenant (BYOK), ensuring that even a database-level access by a rogue admin does not yield decryptable data.

---

## Summary Table

| Edge Case | Risk Level | Primary Detection | Key Mitigation |
|---|---|---|---|
| Compromised certificate impersonation | Critical | Session conflict, telemetry anomaly, IP geo-anomaly | HSM key storage, hardware attestation |
| Certificate rotation zero-downtime | Medium | Expiry monitoring job | Dual-cert acceptance window, proactive renewal |
| Telemetry replay attack | High | TLS ephemeral keys, message ID dedup, timestamp window | mTLS + ECDHE, sequence numbers |
| Cross-device shadow access attempt | High | MQTT broker ACL enforcement | Dynamic ACL by certificate CN |
| Expired code-signing certificate | High | Upload-time signature validation | Automated signing, 60-day expiry monitoring |
| GDPR subject access request | High (Regulatory) | Compliance module workflow | Cross-subsystem data tagging, export automation |
| Regulatory command audit trail | High (Regulatory) | Append-only audit log | Write-once storage, hash chain integrity |
| Data sovereignty violation | High (Regulatory) | Provisioning-time region policy check | Regional cluster routing, infrastructure-level enforcement |
| Timing side-channel attack | Medium | Command pattern rate anomaly | Constant-time response padding, rate limiting |
| Insider data exfiltration | Critical | SIEM behavioral anomaly, DLP limits | Four-eyes export authorization, BYOK encryption |
