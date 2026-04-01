# Edge Cases: Device Provisioning — IoT Device Management Platform

## Introduction

Device provisioning in an IoT platform differs fundamentally from user registration in a web application. A user who fails to register can retry from a browser; a device that fails to provision may be in a sealed enclosure on a factory floor, a remote oil rig, or embedded in medical equipment — with no human operator nearby and no UI to retry from. The provisioning flow must be designed to succeed in the presence of network partitions, power failures, firmware crashes, and factory-line race conditions, and it must do so with absolute data integrity.

The provisioning flow on this platform involves multiple systems executing in sequence: the API Gateway validates the request, the CertificateService generates the X.509 certificate and signs it with the intermediate CA, PostgreSQL stores the device record with the certificate thumbprint, and EMQX receives the device's first authenticated connection. Any failure between these steps leaves the platform in a partially-consistent state that must be detected and remediated automatically.

At scale, provisioning edge cases are not hypothetical. A factory line bringing up 10,000 devices at shift start is an expected operating condition, not an anomaly. The platform must handle this without degrading provisioning reliability below its 99.95% SLA, without allowing rogue registrations to impersonate legitimate devices, and without creating a data model that becomes inconsistent under concurrent writes.

---

## Certificate Rotation Failure During Provisioning

### Scenario Description

Device provisioning using the X.509 flow involves a multi-step transaction: (1) the device submits a Certificate Signing Request (CSR) via `POST /provisioning/csr`; (2) the CertificateService validates the CSR, signs it with the intermediate CA key, and returns the signed certificate; (3) the ProvisioningService writes the device record to PostgreSQL including the certificate thumbprint, device metadata, and organization assignment; (4) the device stores the certificate and private key in secure storage and connects to EMQX on port 8883.

If step 3 fails — PostgreSQL write error, connection timeout, transaction conflict — the device holds a valid, CA-signed certificate in memory, but the platform has no device record. The device is now in a ghost state: it can authenticate to EMQX (the MQTT auth plugin queries the CertificateService, which has the cert in its cache) but cannot be looked up by device_id, and its telemetry will be rejected by the TelemetryService because no device record exists to validate against.

The ghost device will appear in the certificate authority's issued-certs log but not in the devices table. Nightly reconciliation will detect the divergence. However, until remediation, the device is silently dropping all telemetry to the DLQ with `DEVICE_NOT_FOUND` errors, and the organization has no visibility into the device's status.

### Trigger Conditions

- PostgreSQL primary failover occurring mid-transaction during a write to the `devices` table
- Deadlock on the `devices` table caused by concurrent provisioning writes to the same organization's shard (particularly during mass provisioning)
- CertificateService pod OOM-killed after signing the certificate but before the callback to ProvisioningService completes
- Network partition between CertificateService and ProvisioningService lasting longer than the saga timeout (15 seconds)
- PostgreSQL connection pool exhaustion causing the write to be queued past the 10-second transaction timeout

### Impact

- **Device impact:** Device has a valid certificate and can authenticate to EMQX, but all telemetry messages are routed to `telemetry-raw-dlq` with `DEVICE_NOT_FOUND`. The device appears online to EMQX metrics but invisible to the platform's device registry.
- **Organization impact:** Operator sees a device count discrepancy — fewer devices in the registry than were provisioned at the factory. No alert is generated in real time; detection depends on reconciliation jobs.
- **Data at risk:** Up to 1 hour of telemetry from the ghost device (from provisioning attempt to reconciliation job) goes to DLQ and is not written to InfluxDB. Telemetry can be replayed from DLQ after remediation.
- **CA impact:** Orphaned certificate contributes to CA audit log noise and, if not revoked, remains a permanent credential that could be abused.

### Detection

- **Metric:** `device_provisioning_success_total` vs. `certificate_issued_total` per organization. A persistent divergence > 0 triggers alert `PROV-CERT-ORPHAN-001` after 5 minutes.
- **Log pattern:** TelemetryService emits `WARN device_not_found device_id=<id>` for each rejected telemetry message. Log aggregator (Loki) alert rule fires when this pattern appears > 5 times for the same device_id within 5 minutes.
- **Reconciliation job:** `cert-device-reconcile` cron job runs every hour. Queries CertificateService for issued certs in the last 2 hours, cross-references with PostgreSQL devices table. Publishes `reconciliation.orphaned_cert` events to Kafka for any cert with no corresponding device record.

### Mitigation

The provisioning flow uses a distributed saga pattern to ensure consistency. The saga steps are:

1. **CertificateService:** Sign certificate, record in `certificates` table with `status = ISSUED_PENDING_DEVICE`.
2. **ProvisioningService:** Write device record to PostgreSQL with `status = PROVISIONING`. On success, call CertificateService to update cert status to `status = ACTIVE`.
3. **On saga compensation (step 2 failure):** CertificateService revokes the certificate (marks `status = REVOKED`), notifies device to re-provision.

The idempotency key for the provisioning request is derived from `SHA-256(serial_number + ":" + csr_public_key_fingerprint)`. A retry with the same serial number and CSR returns the same certificate without re-executing the saga, even if the original request partially completed.

EMQX authentication plugin checks both `certificates.status = ACTIVE` and `devices.status IN ('ACTIVE', 'PROVISIONING')`. Ghost devices (cert ISSUED_PENDING_DEVICE, no device record) are rejected at MQTT auth even though the cert is technically valid.

### Recovery Procedure

1. Run the reconciliation query to identify all orphaned certificates:
   ```sql
   SELECT c.thumbprint, c.device_serial, c.issued_at, c.organization_id
   FROM certificates c
   LEFT JOIN devices d ON d.certificate_thumbprint = c.thumbprint
   WHERE c.status = 'ISSUED_PENDING_DEVICE'
     AND c.issued_at < NOW() - INTERVAL '30 minutes'
     AND d.id IS NULL;
   ```
2. For each orphaned certificate, check whether a device record was partially written:
   ```sql
   SELECT * FROM devices WHERE serial_number = '<serial>' AND organization_id = '<org_id>';
   ```
3. If no device record exists: trigger re-provisioning by calling `POST /internal/provisioning/retry` with the `{certificate_thumbprint}`. This re-executes the saga from step 2 using the existing certificate.
4. If a partial device record exists (status = 'PROVISIONING'): update the certificate status to ACTIVE and device status to ACTIVE:
   ```sql
   BEGIN;
   UPDATE devices SET status = 'ACTIVE', updated_at = NOW() WHERE serial_number = '<serial>';
   UPDATE certificates SET status = 'ACTIVE' WHERE thumbprint = '<thumbprint>';
   COMMIT;
   ```
5. Replay DLQ messages for the recovered device: `POST /internal/dlq/replay?device_id=<id>&topic=telemetry-raw-dlq&from=<provisioning_timestamp>`.
6. Verify device appears in registry and telemetry is flowing: `GET /devices/{id}/telemetry/latest`.

### Preventive Measures

- Configure PostgreSQL connection pool size per service with headroom: `max_connections = 200`, `pool_size = 40 per CertificateService replica`. Monitor `pg_stat_activity` for connection saturation.
- Enable PostgreSQL `statement_timeout = 8000ms` for provisioning transactions to fail fast rather than queue indefinitely.
- Scale ProvisioningService horizontally before mass provisioning windows (scheduled factory startups) using `kubectl scale deployment provisioning-service --replicas=10`.
- Enable CertificateService write-ahead log replication to a read replica; primary failover completes within 15 seconds with no orphaned certs (automatic saga compensation fires before timeout).

---

## Mass Provisioning Storm

### Scenario Description

A factory production line that manufactures industrial IoT sensors operates in shifts. At shift start, the manufacturing execution system (MES) boots all devices assembled in the previous shift simultaneously and triggers the provisioning flow for each. A typical shift produces 2,000–15,000 devices, all of which come online within a 60-second window.

Each provisioning request requires: RSA key generation and CSR signing (CPU-intensive, ~50ms per device in CertificateService), a PostgreSQL write with a uniqueness check on `serial_number`, and an EMQX connection attempt. At 10,000 concurrent provisioning requests, the CertificateService CPU utilization spikes to 100%, the PostgreSQL `devices` table experiences severe lock contention on the unique index scan, and EMQX receives 10,000 TCP SYN packets within seconds — resembling a SYN flood from the kernel's perspective.

Downstream, the provisioning storm immediately transitions to a telemetry storm: all 10,000 freshly-provisioned devices begin publishing their first telemetry within 30 seconds, creating compounding load on EMQX and Kafka simultaneously. The factory's network switch may also become a bottleneck if the devices are on the same Layer 2 segment and all attempt to establish TLS connections simultaneously.

### Trigger Conditions

- Shift start on a large factory line without staggered device boot sequence
- Recovery from factory network outage (all devices reconnect simultaneously)
- Scheduled manufacturing batch run where MES provisions all devices in a single API call without client-side rate limiting
- Factory firmware update that clears device certificates, forcing re-provisioning for all devices in the batch

### Impact

- **CertificateService:** CSR queue depth exceeds 5,000; p99 latency for provisioning requests spikes from 200ms to 30+ seconds. The factory MES starts receiving HTTP 503 responses and 429 (rate-limited) responses.
- **PostgreSQL:** Write contention on `devices` table unique index for `serial_number`. `pg_locks` shows 500+ waiting lock acquisitions. Other services (DeviceService, OTAService) experience elevated query latency as connection pool fills.
- **EMQX:** Connection rate reaches 200/s. Platform limit is 1,000/s; factory-level limit (per organization) is 100/s. Organization-level throttle fires; factory sees MQTT CONNACK with `0x97` (Quota Exceeded) for devices beyond the burst limit.
- **Factory line:** MES receives rate limit errors, may halt production line if it lacks retry logic. Production throughput drops to the provisioning rate limit.

### Detection

- **Alert `PROV-STORM-001`:** CertificateService CSR queue depth > 2,000 for > 60 seconds.
- **Alert `PROV-STORM-002`:** PostgreSQL `pg_locks` waiting count > 200 on `devices` table.
- **Alert `PROV-STORM-003`:** EMQX `connection.accept.rate` > 500/s sustained for > 30 seconds.
- **Metric:** `provisioning_request_rate_per_org` dashboard. Normal: 10–50/min. Storm indicator: > 500/min.
- **Log pattern:** `WARN rate_limit_exceeded org_id=<id> current_rate=<n> limit=<m>` in APIGateway logs (Kong rate-limit plugin).

### Mitigation

**Bulk provisioning API:** `POST /provisioning/bulk` accepts an array of up to 1,000 CSR objects in a single HTTP request. The CertificateService processes the batch using a worker pool (parallelism = CPU cores × 2), amortizing the HTTP overhead and allowing vectorized PostgreSQL writes with `INSERT ... VALUES (...), (...), ... ON CONFLICT DO NOTHING`. A bulk request for 1,000 devices completes in ~3 seconds vs. 1,000 × 200ms = 200 seconds for individual requests.

**Organization-level rate limits (Kong):** Default: 100 provisioning requests/minute. Pre-approved burst: up to 10,000/minute for organizations with scheduled mass provisioning windows (configured via `POST /admin/organizations/{id}/rate-limits` with a `burst_window` time range). The rate limit operates on a sliding window counter in Redis.

**Certificate pre-loading:** For factory scenarios, the platform supports pre-provisioning certificates at manufacturing time. The manufacturer generates device key pairs offline, submits CSRs in bulk via the manufacturing portal, and receives signed certificates to flash into firmware. The device's first EMQX connection is authenticated immediately without a live provisioning API call. Device records are created in `status = PRE_PROVISIONED` and transition to `ACTIVE` on first MQTT connection.

**EMQX connection rate limiting:** Platform-wide limit: 1,000 TCP connections/second. Per-organization limit: 100/second (default), configurable up to 500/second. Devices that exceed the rate limit receive `CONNACK 0x97` and are expected to use exponential backoff with jitter (base: 5s, cap: 300s) before retrying.

### Recovery Procedure

1. Identify the storm source: `GET /admin/metrics/provisioning?group_by=organization_id&interval=1m` — identify which organization's provisioning rate is anomalous.
2. If MES does not have proper backpressure: contact the factory operations team to enable batch API usage and rate-limit compliance in the MES provisioning client.
3. Temporarily increase the organization's provisioning burst limit to absorb the backlog: `PATCH /admin/organizations/{org_id}/rate-limits {"burst_per_minute": 5000, "burst_window_until": "2024-11-15T18:00:00Z"}`.
4. Monitor CertificateService queue depth: `GET /internal/certservice/metrics?metric=csr_queue_depth`. Confirm it drains within 10 minutes.
5. Scale CertificateService horizontally if queue depth remains > 1,000 after 5 minutes: `kubectl scale deployment cert-service --replicas=8`.
6. After storm resolves, review PostgreSQL lock contention: `SELECT pid, query, wait_event FROM pg_stat_activity WHERE wait_event_type = 'Lock'` to confirm no long-running blocked transactions remain.
7. Update organization's rate-limit back to standard value after burst window expires.

### Preventive Measures

- Require all manufacturing partners to use the bulk provisioning API. Enforce via API Gateway: `POST /provisioning/csr` (individual) is rate-limited to 10/min per IP for non-whitelisted sources.
- Use certificate pre-loading for factory environments to eliminate live provisioning API dependency from the production line critical path.
- Conduct capacity planning for scheduled mass provisioning events: `POST /admin/capacity/reserve {"event_type": "mass_provisioning", "estimated_devices": 10000, "window_start": "...", "window_end": "..."}` — this pre-scales CertificateService replicas and raises PostgreSQL connection limits for the window.
- Configure MES provisioning clients with full-jitter exponential backoff and compliance with `Retry-After` headers from 429 responses.

---

## Device Claims Conflict

### Scenario Description

Hardware serial numbers are the foundational identity anchor for IoT devices before they are assigned platform credentials. A device's serial number is burned into firmware at manufacturing time and is used as the lookup key during provisioning to correlate the physical device with its digital twin. When serial number uniqueness is not enforced across the entire supply chain, two categories of conflict arise.

In the first category, a legitimate ownership dispute occurs: a hardware reseller purchases a batch of 5,000 devices from a manufacturer and distributes them to three customers. The manufacturer assigned serial numbers `SN-10000` through `SN-14999` to the batch, but two customers (Organization A and Organization B) each receive overlapping subsets because the reseller's inventory system did not sub-partition the serial space. Both organizations attempt to provision `SN-10200` — the platform's uniqueness constraint fires, and one organization's provisioning fails.

In the second category, a deliberate claim race occurs: an attacker who knows a device's serial number (readable from a device label, intercepted from a shipping manifest, or scraped from a public API) attempts to register the device before the legitimate owner. If the attacker succeeds, they receive a valid certificate for the device and can receive its telemetry or send it commands.

### Trigger Conditions

- Reseller or distributor distributing a single serial number range to multiple customers
- Manufacturer failing to enforce globally-unique serial number assignment across production runs
- Serial numbers that are predictable or enumerable (e.g., sequential integers starting from 1 per model)
- Compromised shipping manifest or supply chain document revealing serial numbers before delivery

### Impact

- **Legitimate owner:** `POST /provisioning/csr` returns `409 Conflict` with `error_code: DUPLICATE_SERIAL`. Device cannot be provisioned. Factory line halts if this affects multiple devices.
- **Security impact (rogue claim scenario):** Attacker receives telemetry from victim's device. If device is a sensor controlling a physical process, attacker may also be able to send commands. Certificate issued to attacker is valid until revoked.
- **Platform integrity:** Duplicate serial number analysis in post-incident review may surface systematic supply chain weaknesses.

### Detection

- **Alert `PROV-CONFLICT-001`:** `provisioning_conflict_rate` > 5 conflicts/minute for any single organization — indicates systematic supply chain issue, not one-off error.
- **Security alert `SEC-CLAIM-001`:** Serial number provisioned by Organization A; provisioning attempt from Organization B for same serial within 30 days. Triggers security review.
- **Log pattern:** `ERROR duplicate_serial_claim serial=<sn> claiming_org=<id> existing_org=<id>` in ProvisioningService. Aggregated into security event stream.
- **Anomaly detection:** Provisioning attempts for serial numbers that follow predictable patterns (sequential, low-entropy) from different source IPs flagged as potential enumeration attacks.

### Mitigation

**Manufacturing claim tokens:** Manufacturers enrolled in the platform receive a batch of cryptographically-signed claim tokens at device production time. Each token binds `serial_number + manufacturer_id + creation_timestamp` and is signed with the manufacturer's registered private key. Provisioning requires presenting the claim token alongside the CSR. The platform verifies the token signature using the manufacturer's registered public key. An attacker without the claim token cannot provision a device even if they know its serial number.

**Organization-scoped serial isolation:** Serial numbers are unique within an organization, not globally. This allows legitimate duplicate use of the same serial space across organizations (e.g., both organizations can have a device with serial `SN-001`) while preventing cross-organization confusion. The globally unique identifier is the platform-assigned `device_id` (UUID). This is the default mode.

**Ownership transfer API:** `POST /devices/{device_id}/transfer` initiates a two-party ownership transfer with cryptographic proof. The initiating organization signs the transfer request with their API key; the receiving organization accepts with theirs. The previous owner's certificate is revoked and a new certificate is issued to the receiving organization's device record.

**Serial number pre-registration:** Manufacturers can pre-register serial number ranges via `POST /admin/manufacturers/{id}/serial-ranges`. Pre-registered serials can only be claimed by organizations explicitly authorized by the manufacturer (allowlist), preventing rogue claims entirely.

### Recovery Procedure

1. Identify the conflicting provisioning attempt: query ProvisioningService logs for `duplicate_serial_claim` events with the serial number in question.
2. Determine the legitimate claimant by requesting proof of purchase or manufacturing claim token from both parties.
3. If Organization A is the legitimate owner and Organization B has an existing device record: `DELETE /devices/{device_b_id}?reason=ownership_dispute&audit_note=<ticket_id>`. This revokes Organization B's certificate and removes the device record.
4. Provision the device under Organization A using the standard flow. The serial number is now available within Organization A's namespace.
5. If Organization B provisioned first and already has a valid certificate, revoke it immediately: `POST /certificates/{thumbprint}/revoke?reason=ownership_dispute`.
6. Publish the revoked certificate's serial to the CRL. EMQX auth plugin checks CRL on each connection; revoked device will be disconnected within the CRL refresh interval (default: 5 minutes).
7. Preserve the full audit trail: both provisioning attempts, the conflict detection event, the resolution decision, and the certificate revocation must be present in the security audit log.

### Preventive Measures

- Enforce claim token requirement for all new manufacturer partnerships. Existing partnerships without claim token support should be migrated within 6 months.
- Provide manufacturers with a serial number validation API (`GET /admin/manufacturers/{id}/validate-serial?sn=<sn>`) to check for conflicts before production runs.
- Monitor serial number entropy for each organization's provisioned devices. Low-entropy serials (sequential, predictable) trigger a recommendation to implement claim tokens.

---

## Factory Reset During Provisioning

### Scenario Description

Provisioning is not always a clean, atomic operation from the device's perspective. Between the moment the device generates a key pair and submits a CSR, and the moment it receives and persists the signed certificate to secure storage, several failure conditions can trigger a factory reset — wiping the device's volatile and non-volatile memory and returning it to a clean state.

The most common trigger is a firmware watchdog timeout: if the provisioning process takes longer than the watchdog interval (typically 30–120 seconds in embedded systems), the watchdog fires a hardware reset. The device reboots, generates a new key pair (different from the original CSR), and restarts the provisioning flow. The original CSR's certificate has already been signed and stored in the CertificateService — this certificate is now orphaned, as the device no longer holds the corresponding private key and cannot use it.

A second scenario involves deliberate factory reset: a quality assurance technician resets a device during the provisioning process to restart a failed test cycle. The technician may not know that the provisioning flow was in progress. The result is identical to the watchdog scenario: orphaned certificate plus a new provisioning attempt with a different key pair for the same serial number.

The platform must distinguish between these two cases — a duplicate provisioning attempt caused by a firmware reset (legitimate, should be allowed) and a duplicate attempt that may indicate an attack (e.g., an attacker intercepting the serial number and submitting a second CSR to replace the legitimate device's certificate). The distinguishing signal is the presence of a signed factory-reset acknowledgment event.

### Trigger Conditions

- Watchdog timeout fires during the TLS handshake with the provisioning API (common on devices with slow TLS stacks or network congestion)
- Hardware power interruption between CSR submission and certificate storage (especially during in-circuit testing)
- Deliberate quality assurance reset during provisioning test cycle
- Firmware panic (null pointer dereference, stack overflow) in the provisioning code path before certificate persistence
- Flash write failure when persisting the private key to secure storage (NVRAM corruption)

### Impact

- **Orphaned certificate:** The original certificate exists in the CertificateService with `status = ACTIVE` but no device holds its private key. It cannot be used for authentication, but it occupies a slot in the CA's issued-certs list and contributes to CRL size if not revoked.
- **Duplicate device record risk:** Second provisioning attempt for the same serial number with a different CSR. Without proper handling, this creates a second device record for the same physical device, splitting the device's history across two platform identities.
- **Telemetry continuity:** If the device previously had telemetry data associated with the old `device_id`, a new provisioning creates a new `device_id` and the telemetry history is fragmented.
- **Security risk (undetected):** If the factory-reset event is not published (firmware bug, no connectivity at reset time), the platform cannot distinguish this from a potential certificate replacement attack.

### Detection

- **Alert `PROV-RESET-001`:** Second CSR submission for the same serial number with a different public key fingerprint within a 1-hour window. Severity: Warning (triggers investigation, does not block provisioning if factory-reset token present).
- **Reconciliation metric:** `orphaned_cert_count` published hourly by the `cert-device-reconcile` job. Alert if > 10 orphaned certs per organization per hour (indicates systematic issue).
- **Device event log:** `devices/{id}/events` topic consumed by DeviceEventService. Factory reset events logged with device_id, serial_number, timestamp, and firmware_version. Absence of factory-reset event before a re-provisioning attempt for the same serial triggers a security escalation.
- **Log pattern:** `WARN duplicate_provisioning_attempt serial=<sn> previous_thumbprint=<t1> new_thumbprint=<t2>` in ProvisioningService.

### Mitigation

**Idempotent provisioning with fingerprint matching:** When a provisioning request arrives for a serial number that already has an active device record:
- If the CSR public key fingerprint matches the existing certificate's public key fingerprint: return the existing certificate (idempotent retry).
- If the CSR public key fingerprint is different AND a valid factory-reset token is present in the request: revoke the existing certificate, create a new device record with a new device_id (old device_id is tombstoned and linked to the new one for audit), issue the new certificate.
- If the CSR public key fingerprint is different AND no factory-reset token is present: return `409 Conflict` with `error_code: CONFLICTING_CERTIFICATE_FINGERPRINT` and require explicit operator confirmation via `POST /provisioning/override` (admin only, rate-limited, audited).

**Factory reset acknowledgment protocol:** Device firmware is required (per Platform Device SDK specification v2.1+) to publish a factory-reset event before executing the reset:
```json
{
  "topic": "devices/{serial_number}/events",
  "payload": {
    "event": "factory_reset",
    "firmware_version": "1.4.2",
    "reason": "watchdog_timeout",
    "previous_cert_thumbprint": "sha256:abc123...",
    "timestamp": "2024-11-15T09:14:32Z"
  }
}
```
This event is published using the device's current (pre-reset) certificate over MQTT before the reset is executed. The platform stores this event and uses it to authorize the re-provisioning with a different key pair.

**Factory reset tokens:** For scenarios where the device cannot publish the event (power failure mid-provisioning, before any certificate is available), the platform accepts a factory-reset token generated by the manufacturing system. This token is `HMAC-SHA256(serial_number + ":" + reset_timestamp, manufacturer_secret_key)` and is presented alongside the new CSR. The platform verifies the HMAC, allows the re-provisioning, and links the new device record to the old one.

### Recovery Procedure

1. Identify orphaned certificates via the reconciliation report or alert: `GET /internal/reconciliation/orphaned-certs?organization_id=<org_id>&issued_after=<timestamp>`.
2. For each orphaned certificate, determine whether a re-provisioning has already succeeded: `SELECT * FROM devices WHERE serial_number = '<sn>' ORDER BY created_at DESC`.
3. If re-provisioning succeeded: revoke the orphaned certificate via `POST /certificates/{thumbprint}/revoke?reason=factory_reset_orphan`. The certificate was never used and its revocation is administrative cleanup.
4. If re-provisioning has not been attempted (device is still offline after reset): the device will re-provision on next boot. Pre-stage a factory-reset token in the provisional device record so re-provisioning is not blocked: `POST /internal/provisioning/prestage-reset-token {"serial_number": "<sn>", "token": "<hmac>", "valid_until": "..."}`.
5. After re-provisioning completes, link the old and new device records for telemetry continuity: `POST /internal/devices/{new_id}/link-predecessor {"predecessor_device_id": "<old_id>"}`. Telemetry queries that include `include_predecessor: true` will span both device IDs.
6. Verify the telemetry history is queryable across both device IDs: `GET /devices/{new_id}/telemetry?include_predecessor=true&from=<before_reset>`.

### Preventive Measures

- Require device firmware to implement the factory-reset acknowledgment event protocol (enforced as a certification requirement in the Device Compatibility Program v2.1+).
- Set watchdog interval to at least 3× the p99 provisioning latency (currently p99 = 800ms; watchdog should be set to ≥ 10 seconds for provisioning context). Document this in the Platform Device SDK integration guide.
- Manufacture devices with dual-stage provisioning: stage 1 (key generation and CSR signing) persists to NVRAM before stage 2 (CSR submission) begins. If stage 2 is interrupted, stage 1 is already durable — the same CSR is resubmitted on the next boot without generating a new key pair.
- Run the `cert-device-reconcile` job every 30 minutes during active manufacturing shifts (instead of hourly default). Configure via `POST /admin/jobs/cert-device-reconcile/schedule {"cron": "*/30 * * * *"}`.
