# IoT Device Management Platform – Requirements

## Revision History

| Version | Date       | Author            | Description                              |
|---------|------------|-------------------|------------------------------------------|
| 1.0     | 2024-01-10 | Platform Architect | Initial requirements baseline            |
| 1.1     | 2024-01-18 | IoT Lead Engineer  | Added OTA and Certificate requirements   |
| 1.2     | 2024-01-25 | Security Architect | Expanded security and compliance section |
| 1.3     | 2024-02-01 | Platform Architect | Added Device Shadow and Fleet Management |

---

## 1. Introduction

### 1.1 Purpose
This document specifies the functional and non-functional requirements for the IoT Device Management Platform. It serves as the authoritative source of truth for all engineering, QA, and product decisions.

### 1.2 Scope
The platform encompasses device lifecycle management from initial provisioning through decommissioning, real-time telemetry ingestion, rules-based alerting, OTA firmware management, remote command execution, and multi-tenant security. The platform is designed to support industrial, commercial, and consumer IoT deployments.

### 1.3 Definitions
| Term | Definition |
|------|------------|
| Device | An IoT endpoint that connects to the platform via MQTT, CoAP, or HTTPS |
| Fleet | A logical grouping of devices managed under shared policies |
| Tenant | An isolated organizational unit with its own data, users, and configuration |
| Device Shadow | A persistent JSON document representing a device's last-known and desired state |
| Telemetry | Time-series sensor readings published by devices |
| OTA | Over-the-Air firmware update delivered remotely to devices |
| Rules Engine | The subsystem that evaluates telemetry against conditions and triggers actions |
| Certificate | An X.509 digital certificate used for device authentication |
| Edge Gateway | An intermediate node that bridges local device networks to the cloud platform |

### 1.4 Assumptions
- Devices may be intermittently connected and must support offline buffering
- The platform must handle burst traffic of 10× normal ingest volume
- All device communications must be encrypted with TLS 1.2 or higher
- The platform will be deployed on Kubernetes in a multi-availability-zone configuration
- Tenants are fully isolated at the data layer; no cross-tenant data leakage is permitted

---

## 2. Functional Requirements

### FR-01: Device Provisioning

Device provisioning is the process by which a new device establishes a trusted identity with the platform, receives credentials, and is registered in the device registry. The platform must support multiple provisioning flows to accommodate different device manufacturing capabilities and security postures.

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| REQ-DP-001 | The system shall support X.509 certificate-based device provisioning using a device-unique client certificate signed by a tenant CA or the platform CA | High | Defined |
| REQ-DP-002 | The system shall support pre-shared key (PSK) provisioning for constrained devices that cannot perform asymmetric cryptography at acceptable performance | High | Defined |
| REQ-DP-003 | The system shall support JWT-based provisioning tokens with configurable expiry (1 hour to 7 days) for fleet enrollment workflows | High | Defined |
| REQ-DP-004 | The system shall implement a Just-in-Time Registration (JITR) flow that automatically creates a device registry entry when a device presents a valid certificate from a registered CA | High | Defined |
| REQ-DP-005 | The system shall support bulk provisioning via CSV manifest upload containing device IDs, certificate thumbprints, and initial metadata for batches of up to 100,000 devices | High | Defined |
| REQ-DP-006 | The system shall provide a manufacturing provisioning API that can issue device credentials at a rate of at least 500 devices per second during production line operations | High | Defined |
| REQ-DP-007 | The system shall assign each provisioned device a globally unique device identifier (UUID v4) that is immutable for the device's lifetime | High | Defined |
| REQ-DP-008 | The system shall allow operators to define provisioning templates that pre-populate device metadata, initial desired state, and fleet assignment during the provisioning flow | Medium | Defined |
| REQ-DP-009 | The system shall emit a `device.provisioned` event to the event bus immediately upon successful provisioning, including device ID, tenant ID, provisioning method, and timestamp | Medium | Defined |
| REQ-DP-010 | The system shall reject provisioning requests from devices presenting revoked certificates, and the rejection reason must be logged to the audit trail with the certificate serial number | High | Defined |

### FR-02: Device Registry

The device registry is the authoritative source of truth for all device metadata, status, and configuration. It must support efficient lookups, filtering, and bulk operations across millions of devices per tenant.

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| REQ-DR-001 | The system shall maintain a registry entry for every provisioned device containing: device ID, name, model, firmware version, status, last-seen timestamp, IP address, tenant ID, fleet assignments, and custom metadata tags | High | Defined |
| REQ-DR-002 | The system shall support querying the device registry by any combination of: status, fleet, firmware version, tag key/value pairs, last-seen time range, and geographic region with paginated results | High | Defined |
| REQ-DR-003 | The system shall support bulk metadata updates to up to 10,000 devices in a single API call via a device filter or explicit device ID list | Medium | Defined |
| REQ-DR-004 | The system shall track device connectivity status in near-real-time, transitioning devices to OFFLINE status within 60 seconds of the last heartbeat expiry | High | Defined |
| REQ-DR-005 | The system shall maintain a complete audit history of all registry changes including the user/service that made the change, previous value, new value, and timestamp, retained for a minimum of 1 year | High | Defined |
| REQ-DR-006 | The system shall support custom metadata fields as key-value pairs (string, number, boolean, JSON object) with per-tenant schema validation | Medium | Defined |
| REQ-DR-007 | The system shall support soft deletion of device registry entries with a 30-day grace period before permanent deletion, during which the device can be restored | Medium | Defined |
| REQ-DR-008 | The system shall provide a device search API capable of returning results for queries against 10 million devices in under 500 milliseconds at the 95th percentile | High | Defined |
| REQ-DR-009 | The system shall track and expose the following computed fields per device: days since provisioning, total telemetry messages received, total commands sent, and OTA update history summary | Low | Defined |
| REQ-DR-010 | The system shall generate a device summary report per fleet exportable in CSV and JSON formats, including all registry fields and computed statistics | Low | Defined |

### FR-03: Telemetry Ingestion

Real-time telemetry ingestion is a core capability. Devices publish sensor readings and operational metrics which the platform ingests, validates, routes, and stores for analysis and rule evaluation.

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| REQ-TI-001 | The system shall accept telemetry published via MQTT (v3.1.1 and v5.0) on topic pattern `v1/{tenantId}/devices/{deviceId}/telemetry` with QoS 0 and QoS 1 support | High | Defined |
| REQ-TI-002 | The system shall accept telemetry via CoAP (RFC 7252) for constrained devices operating on low-power networks, supporting confirmable and non-confirmable messages | High | Defined |
| REQ-TI-003 | The system shall accept telemetry via HTTPS POST to `/v1/telemetry` for devices in environments where MQTT is not permitted, with batch payloads of up to 1,000 readings per request | High | Defined |
| REQ-TI-004 | The system shall validate all incoming telemetry against the device's registered schema (if defined) and route invalid payloads to a dead-letter topic for inspection | High | Defined |
| REQ-TI-005 | The system shall ingest telemetry at a sustained rate of at least 1 million messages per minute per cluster deployment and handle burst loads of 5 million messages per minute | High | Defined |
| REQ-TI-006 | The system shall store validated telemetry in a time-series database within 2 seconds of receipt at the 99th percentile under normal operating conditions | High | Defined |
| REQ-TI-007 | The system shall deduplicate telemetry messages with identical device ID, timestamp, and payload hash within a 5-minute deduplication window | Medium | Defined |
| REQ-TI-008 | The system shall forward all valid telemetry messages to the Rules Engine for condition evaluation within 500 milliseconds of receipt | High | Defined |
| REQ-TI-009 | The system shall apply per-tenant configurable data retention policies to time-series data, supporting retention periods from 7 days to 10 years with automated tiered archival to object storage | Medium | Defined |
| REQ-TI-010 | The system shall provide a telemetry query API supporting time-range queries, aggregations (mean, min, max, sum, count, percentile), downsampling, and interpolation for up to 1,000 data points per series per response page | High | Defined |

### FR-04: Rules Engine

The rules engine evaluates telemetry data and device state changes against operator-defined conditions and executes configured actions in response. It enables automated alerting, command dispatch, and webhook integrations.

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| REQ-RE-001 | The system shall allow operators to define rules consisting of: a trigger (telemetry field threshold, device state change, schedule), one or more conditions (comparison operators, logical AND/OR, time-window aggregations), and one or more actions | High | Defined |
| REQ-RE-002 | The system shall support the following action types: send alert notification (email, SMS, push), invoke webhook (HTTP POST with configurable payload template), publish MQTT command to device, write to audit log, and trigger OTA deployment | High | Defined |
| REQ-RE-003 | The system shall evaluate telemetry-triggered rules within 1 second of telemetry ingestion at the 95th percentile | High | Defined |
| REQ-RE-004 | The system shall support rule suppression windows to prevent alert storms, with configurable cool-down periods (minimum 1 minute, maximum 24 hours) per rule | High | Defined |
| REQ-RE-005 | The system shall maintain a rule execution history log for each rule including: evaluation timestamp, input telemetry values, condition result, and action outcomes with success/failure status | Medium | Defined |
| REQ-RE-006 | The system shall support rule scoping: rules can be applied globally to all devices in a tenant, to a specific fleet, or to individual devices | Medium | Defined |
| REQ-RE-007 | The system shall support complex condition expressions including: sliding window aggregations over configurable time periods (1 minute to 24 hours), rate-of-change calculations, and cross-field comparisons | Medium | Defined |
| REQ-RE-008 | The system shall provide a rule simulation mode allowing operators to test a rule definition against historical telemetry data before activating it in production | Low | Defined |

### FR-05: OTA Firmware Updates

The OTA subsystem manages the full lifecycle of firmware artifacts and their deployment to devices, including targeting, scheduling, progress tracking, and automatic rollback.

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| REQ-OTA-001 | The system shall allow authorized users to upload firmware binary artifacts (up to 512 MB per artifact) with associated metadata: version string, target device model, release notes, minimum required current version, and cryptographic signature | High | Defined |
| REQ-OTA-002 | The system shall verify the cryptographic signature of every firmware artifact at upload time and reject artifacts with invalid or missing signatures | High | Defined |
| REQ-OTA-003 | The system shall support deployment campaigns targeting: all devices in a tenant, devices in a specific fleet, devices matching a metadata filter, or an explicit list of device IDs | High | Defined |
| REQ-OTA-004 | The system shall support staged rollout strategies: percentage-based rollout (deploy to N% of target devices first), canary group (deploy to a named test fleet first), and time-based phased rollout | High | Defined |
| REQ-OTA-005 | The system shall track per-device OTA update status through the following states: PENDING, NOTIFIED, DOWNLOADING, DOWNLOADED, INSTALLING, SUCCESS, FAILED, ROLLED_BACK | High | Defined |
| REQ-OTA-006 | The system shall automatically pause a deployment campaign and trigger rollback when the failure rate across updated devices exceeds a configurable threshold (default 10%) | High | Defined |
| REQ-OTA-007 | The system shall queue OTA notifications for offline devices and deliver them within 60 seconds of the device reconnecting to the platform | High | Defined |
| REQ-OTA-008 | The system shall provide firmware download via CDN with TLS, and devices shall verify the firmware SHA-256 checksum before applying the update | High | Defined |
| REQ-OTA-009 | The system shall provide a campaign dashboard showing: total devices targeted, percentage complete, per-state device counts, estimated completion time, and error summary | Medium | Defined |
| REQ-OTA-010 | The system shall retain full deployment history per device including all firmware versions applied, timestamps, and outcomes, for the lifetime of the device record | Medium | Defined |

### FR-06: Remote Command Execution

The remote command subsystem enables operators and automated processes to send commands to individual devices or fleets, with delivery guarantees and acknowledgment tracking.

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| REQ-CMD-001 | The system shall allow authorized users to dispatch commands to individual devices or all devices in a fleet, with a configurable payload (JSON, up to 64 KB) | High | Defined |
| REQ-CMD-002 | The system shall queue commands for offline devices and deliver them in order within 60 seconds of device reconnection, maintaining delivery order per device | High | Defined |
| REQ-CMD-003 | The system shall support the following command states: QUEUED, DELIVERED, ACKNOWLEDGED, EXECUTING, SUCCEEDED, FAILED, TIMED_OUT | High | Defined |
| REQ-CMD-004 | The system shall enforce a configurable command TTL (time-to-live) after which undelivered commands expire, with a default of 24 hours and maximum of 7 days | High | Defined |
| REQ-CMD-005 | The system shall require devices to send an acknowledgment message upon receiving a command, and a completion message upon finishing execution, with optional result payload | High | Defined |
| REQ-CMD-006 | The system shall restrict command dispatch to users with the `device:command` permission and log every command dispatch with user ID, timestamp, command type, and target | High | Defined |
| REQ-CMD-007 | The system shall support command templates that allow operators to define reusable command schemas with parameter validation before dispatch | Medium | Defined |
| REQ-CMD-008 | The system shall provide a command history API returning the full execution history for a device, paginated by time, with filtering by command type and status | Medium | Defined |

### FR-07: Certificate Management

The certificate management subsystem handles the full lifecycle of X.509 certificates used for device authentication, including issuance, renewal, revocation, and monitoring.

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| REQ-CERT-001 | The system shall operate an internal Certificate Authority (CA) per tenant, allowing tenant admins to upload their own CA or use the platform-managed CA | High | Defined |
| REQ-CERT-002 | The system shall issue device certificates with a configurable validity period (minimum 1 day, maximum 10 years, default 1 year) and enforce key length minimums (RSA 2048+, ECC P-256+) | High | Defined |
| REQ-CERT-003 | The system shall maintain a Certificate Revocation List (CRL) and support Online Certificate Status Protocol (OCSP) for real-time certificate validity checks during device authentication | High | Defined |
| REQ-CERT-004 | The system shall automatically alert operators 30 days and 7 days before certificate expiry for certificates approaching their validity end date | High | Defined |
| REQ-CERT-005 | The system shall support automated certificate rotation by issuing a new certificate to an online device before the current certificate expires, without requiring device downtime | High | Defined |
| REQ-CERT-006 | The system shall immediately revoke all certificates associated with a device when the device is decommissioned or when an operator triggers emergency revocation | High | Defined |
| REQ-CERT-007 | The system shall maintain a certificate audit log recording: issuance, renewal, revocation events, the triggering actor (user or automation), and timestamp | High | Defined |
| REQ-CERT-008 | The system shall support certificate pinning for high-security tenants, allowing a tenant to bind device authentication exclusively to a specific certificate thumbprint | Medium | Defined |

### FR-08: Multi-Tenant Architecture

The platform must provide strong tenant isolation while sharing underlying infrastructure to achieve economies of scale. Each tenant operates as an independent organizational unit.

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| REQ-MT-001 | The system shall isolate all tenant data at the data layer using tenant-scoped database schemas or row-level security, ensuring no cross-tenant data access is possible through the API | High | Defined |
| REQ-MT-002 | The system shall enforce per-tenant resource quotas including: maximum devices, maximum telemetry messages per hour, maximum active rules, maximum concurrent OTA campaigns, and API rate limits | High | Defined |
| REQ-MT-003 | The system shall support a hierarchical RBAC model within each tenant with the following built-in roles: Tenant Admin, Fleet Manager, Device Operator, Security Admin, and Read-Only Viewer | High | Defined |
| REQ-MT-004 | The system shall allow Tenant Admins to create custom roles with granular permission sets from the platform permission catalog | Medium | Defined |
| REQ-MT-005 | The system shall provide tenant-level configuration for: MQTT broker endpoint hostname, certificate authority, data retention policy, alert notification channels, and webhook endpoints | Medium | Defined |
| REQ-MT-006 | The system shall support tenant onboarding via an automated workflow that provisions the tenant's namespace, default CA, MQTT credentials, and initial admin user within 30 seconds | High | Defined |
| REQ-MT-007 | The system shall provide per-tenant usage dashboards showing: active device count, telemetry message volume, storage consumed, API call volume, and current quota utilization | Medium | Defined |
| REQ-MT-008 | The system shall support tenant offboarding with a 30-day data export window before permanent data deletion, with export in JSON and CSV formats | Medium | Defined |

### FR-09: Security

Security requirements apply platform-wide and encompass authentication, authorization, encryption, and compliance with the IEC 62443 industrial IoT security standard.

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| REQ-SEC-001 | All device-to-platform and user-to-platform communications must be encrypted using TLS 1.2 or TLS 1.3; TLS 1.0 and 1.1 must be disabled on all endpoints | High | Defined |
| REQ-SEC-002 | The system shall enforce mutual TLS (mTLS) for all MQTT device connections, requiring devices to present a valid client certificate | High | Defined |
| REQ-SEC-003 | The system shall implement OAuth 2.0 with PKCE for user authentication via the management API and dashboard, supporting integration with external identity providers via OIDC | High | Defined |
| REQ-SEC-004 | The system shall log all authentication events (success and failure) with source IP, timestamp, credential type, and outcome to a tamper-evident audit log | High | Defined |
| REQ-SEC-005 | The system shall detect and block brute-force authentication attempts by rate-limiting failed authentication attempts per source IP and per credential, with automatic lockout after 10 failures in 5 minutes | High | Defined |
| REQ-SEC-006 | The system shall implement row-level tenant isolation verified by automated integration tests that confirm no API endpoint returns data from a different tenant regardless of authentication token | High | Defined |
| REQ-SEC-007 | The system shall support field-level encryption for sensitive telemetry fields, allowing tenants to designate specific telemetry keys as encrypted-at-rest using tenant-managed KMS keys | Medium | Defined |
| REQ-SEC-008 | The system shall comply with IEC 62443-3-3 security level SL2 requirements, including zone-and-conduit network segmentation, integrity protection, and non-repudiation of control commands | High | Defined |
| REQ-SEC-009 | The system shall perform automated vulnerability scanning of all firmware artifacts uploaded to the OTA subsystem using a static analysis tool before making the artifact available for deployment | Medium | Defined |
| REQ-SEC-010 | The system shall enforce network policies that restrict inter-service communication to explicitly defined service-to-service routes, denying all unlisted communication by default | High | Defined |

### FR-10: Device Shadow / Digital Twin

The device shadow provides a persistent, bidirectional state synchronization mechanism between the platform and devices, enabling offline state management and desired state delivery.

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| REQ-DS-001 | The system shall maintain a device shadow document for every registered device, consisting of a `desired` section (operator-set target state), a `reported` section (device-reported current state), and a `delta` section (computed difference) | High | Defined |
| REQ-DS-002 | The system shall allow operators to update the `desired` state of a device shadow via the REST API, with the delta automatically delivered to the device over MQTT on reconnection | High | Defined |
| REQ-DS-003 | The system shall persist the device shadow in a durable store with optimistic locking using a version counter, rejecting stale updates with an HTTP 409 Conflict response | High | Defined |
| REQ-DS-004 | The system shall deliver shadow delta updates to online devices within 2 seconds of a desired state change at the 95th percentile | High | Defined |
| REQ-DS-005 | The system shall support shadow versioning, retaining the last 50 versions of each shadow document for audit and rollback purposes | Medium | Defined |
| REQ-DS-006 | The system shall support nested JSON objects in shadow documents with a maximum depth of 10 levels and a maximum document size of 64 KB | Medium | Defined |
| REQ-DS-007 | The system shall emit a `shadow.delta.updated` event whenever the delta section changes, enabling downstream systems to react to state divergence | Medium | Defined |
| REQ-DS-008 | The system shall allow operators to define shadow schema templates per device model, enforcing type and value constraints on reported state fields | Low | Defined |

### FR-11: Fleet Management

Fleet management enables logical grouping of devices for policy application, bulk operations, and organizational reporting.

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| REQ-FM-001 | The system shall support hierarchical fleet organization with up to 5 levels of nesting (e.g., Region > Country > City > Building > Floor) | High | Defined |
| REQ-FM-002 | The system shall allow a device to belong to multiple fleets simultaneously, with fleet membership tracked with effective dates | Medium | Defined |
| REQ-FM-003 | The system shall support fleet-level policies that are inherited by all member devices, including: telemetry schema, alert rules, default desired state, and OTA approval workflow | High | Defined |
| REQ-FM-004 | The system shall provide fleet-level aggregate dashboards showing: total devices, online percentage, firmware version distribution, recent alert counts, and average telemetry rate | Medium | Defined |
| REQ-FM-005 | The system shall support bulk device operations scoped to a fleet: send command to all, initiate OTA campaign, update metadata tag, export device list | High | Defined |
| REQ-FM-006 | The system shall support dynamic fleet membership rules based on device metadata filters, automatically adding or removing devices as their metadata changes | Medium | Defined |
| REQ-FM-007 | The system shall allow fleet managers to define maintenance windows for a fleet during which OTA updates are permitted or prohibited | Medium | Defined |
| REQ-FM-008 | The system shall provide fleet comparison reports allowing managers to compare firmware version distribution, connectivity rates, and telemetry volumes across two or more fleets | Low | Defined |

---

## 3. Non-Functional Requirements

### NFR-01: Performance

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-PERF-001 | MQTT message ingestion end-to-end latency (device publish to time-series storage) | p99 < 2 seconds | High |
| NFR-PERF-002 | REST API response time for single-resource GET operations | p95 < 200 ms | High |
| NFR-PERF-003 | REST API response time for list/search operations with up to 10M devices | p95 < 500 ms | High |
| NFR-PERF-004 | Device shadow update delivery latency (API write to device MQTT delivery) | p95 < 2 seconds | High |
| NFR-PERF-005 | Rules engine evaluation latency (telemetry receipt to action trigger) | p95 < 1 second | High |
| NFR-PERF-006 | Device provisioning throughput during manufacturing bulk operations | >= 500 devices/sec | High |
| NFR-PERF-007 | Telemetry time-series query response (30-day range, hourly aggregation, 1M points) | p95 < 3 seconds | Medium |
| NFR-PERF-008 | OTA firmware download throughput per device | >= 1 MB/s per device | Medium |

### NFR-02: Reliability

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-REL-001 | Platform overall availability SLA | >= 99.95% per month (< 22 min downtime/month) | High |
| NFR-REL-002 | Telemetry ingestion pipeline availability (MQTT broker and ingest workers) | >= 99.99% per month | High |
| NFR-REL-003 | Recovery Time Objective (RTO) for full platform failure | < 15 minutes | High |
| NFR-REL-004 | Recovery Point Objective (RPO) for telemetry data | < 30 seconds | High |
| NFR-REL-005 | Message durability for telemetry in the Kafka pipeline | No loss for messages acknowledged by broker | High |
| NFR-REL-006 | Command delivery guarantee for offline devices | At-least-once delivery within 60s of reconnection | High |
| NFR-REL-007 | Database replication lag for read replicas | < 1 second under normal load | Medium |

### NFR-03: Security

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-SEC-001 | All secrets (API keys, certificates, passwords) stored in a dedicated secrets manager | 100% compliance | High |
| NFR-SEC-002 | Penetration testing frequency | Quarterly external pen-test | High |
| NFR-SEC-003 | Vulnerability patch SLA for critical CVEs | Patched within 24 hours | High |
| NFR-SEC-004 | Dependency vulnerability scanning | Every CI build | High |
| NFR-SEC-005 | Audit log retention | Minimum 2 years, immutable storage | High |
| NFR-SEC-006 | Data encryption at rest | AES-256 for all persistent data stores | High |
| NFR-SEC-007 | Secrets rotation policy | All platform secrets rotated every 90 days | Medium |

### NFR-04: Scalability

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-SCAL-001 | Maximum connected devices per cluster | 100 million devices | High |
| NFR-SCAL-002 | Maximum telemetry ingestion rate per cluster | 10 million messages/minute | High |
| NFR-SCAL-003 | Maximum concurrent MQTT connections | 5 million persistent connections | High |
| NFR-SCAL-004 | Horizontal scaling: MQTT broker and ingest workers must auto-scale | Scale to 3× baseline within 5 minutes | High |
| NFR-SCAL-005 | Maximum tenants per platform deployment | 10,000 tenants | Medium |
| NFR-SCAL-006 | Maximum devices per tenant | 10 million devices | Medium |
| NFR-SCAL-007 | Storage scalability for telemetry data | Support petabyte-scale with hot/warm/cold tiering | High |

### NFR-05: Observability

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR-OBS-001 | All services must emit structured logs in JSON format with trace ID, span ID, service name, and log level | 100% compliance | High |
| NFR-OBS-002 | All services must expose Prometheus-compatible metrics on /metrics endpoint | 100% compliance | High |
| NFR-OBS-003 | Distributed tracing must be implemented across all synchronous service calls using OpenTelemetry | 100% of critical paths | High |
| NFR-OBS-004 | Platform health dashboard with real-time SLI/SLO tracking must be available in Grafana | Available 99.9% of time | Medium |
| NFR-OBS-005 | Alerting on SLO breach must trigger within 2 minutes of threshold violation | p95 < 2 minutes | High |
| NFR-OBS-006 | All telemetry ingest pipeline stages must expose per-stage throughput, latency, and error rate metrics | 100% of pipeline stages | High |

---

## 4. Constraints

- The platform must run on Kubernetes 1.28+ with Helm-based deployment
- MQTT broker implementation must be based on EMQX or Mosquitto for compliance with MQTT specification
- Time-series storage must use InfluxDB 2.x or TimescaleDB 15+ for telemetry persistence
- The primary relational database must be PostgreSQL 15+
- Message streaming infrastructure must be Apache Kafka 3.x
- All APIs must be versioned with the version prefix in the URL path (e.g., `/v1/`)
- The platform must be cloud-provider agnostic and deployable on AWS, Azure, and GCP
- Client SDKs must be provided for Python, JavaScript/Node.js, Go, and Java

---

## 5. Out of Scope

- Consumer mobile application for end-users (handled by a separate mobile product team)
- Device hardware design or firmware development (platform provides SDK and protocol specs only)
- Data analytics and machine learning pipelines (platform provides raw telemetry export APIs)
- Billing and invoicing systems (integrates with an external billing platform via webhook)
