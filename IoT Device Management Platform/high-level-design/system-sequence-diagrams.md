# System Sequence Diagrams

This document captures the key interaction sequences in the IoT Device Management Platform. Each
diagram traces the message flow between system participants for a critical use case, making the
runtime behaviour explicit for developers, architects, and security reviewers.

---

## 1. Device Registration and First Connection

Before an IoT device can publish telemetry or receive commands it must be registered with the
platform and provisioned with a unique X.509 certificate. This sequence covers the full lifecycle
from the initial HTTP registration request through mutual-TLS MQTT connection establishment.

The device presents its factory-burned serial number and model identifier. The API Gateway
validates the bootstrap token that ships with every device. The Device Service creates a persistent
record, then delegates certificate issuance to the Certificate Service which interfaces with the
internal CA. Once the MQTT broker ACL entry is written the device may open a persistent MQTT
session authenticated by the issued certificate. All steps are transactional: a failure at any
point rolls back already-completed sub-steps and returns an error to the device.

```mermaid
sequenceDiagram
    autonumber
    participant IoTDevice as IoT Device
    participant APIGateway as API Gateway
    participant DeviceService as Device Service
    participant CertificateService as Certificate Service
    participant MQTTBroker as MQTT Broker
    participant Database as PostgreSQL

    IoTDevice->>APIGateway: POST /devices/register\n{serialNumber, modelId, bootstrapToken}
    APIGateway->>APIGateway: Validate bootstrap token signature
    APIGateway->>DeviceService: CreateDevice(serialNumber, modelId)
    DeviceService->>Database: INSERT device record\n(status=PENDING, deviceId=UUID)
    Database-->>DeviceService: device row created
    DeviceService->>CertificateService: IssueDeviceCertificate(deviceId, serialNumber)
    CertificateService->>CertificateService: Generate RSA-2048 key pair
    CertificateService->>CertificateService: Build CSR with CN=deviceId
    CertificateService->>CertificateService: Sign CSR with intermediate CA
    CertificateService->>Database: INSERT certificate record\n(deviceId, fingerprint, expiresAt)
    Database-->>CertificateService: certificate row created
    CertificateService-->>DeviceService: {certificate, privateKey, caCertificate}
    DeviceService->>MQTTBroker: AddACL(clientId=deviceId,\ntopic=devices/{deviceId}/#, allow)
    MQTTBroker-->>DeviceService: ACL written
    DeviceService->>Database: UPDATE device SET status=ACTIVE
    Database-->>DeviceService: row updated
    DeviceService-->>APIGateway: {deviceId, certificate, privateKey, caCertificate, mqttEndpoint}
    APIGateway-->>IoTDevice: 201 Created\n{deviceId, certificate, privateKey, caCertificate, mqttEndpoint}

    Note over IoTDevice: Device stores credentials\nin secure element / flash

    IoTDevice->>MQTTBroker: CONNECT (clientId=deviceId,\nmTLS with issued certificate)
    MQTTBroker->>MQTTBroker: Verify client certificate against CA chain
    MQTTBroker->>MQTTBroker: Enforce ACL — clientId matches CN
    MQTTBroker-->>IoTDevice: CONNACK (returnCode=0, sessionPresent=false)
    IoTDevice->>MQTTBroker: SUBSCRIBE devices/{deviceId}/commands/#\n(QoS 1)
    MQTTBroker-->>IoTDevice: SUBACK
    IoTDevice->>MQTTBroker: PUBLISH devices/{deviceId}/status\n{online: true, firmwareVersion, ipAddress}
    MQTTBroker->>DeviceService: Event: device/connected (deviceId)
    DeviceService->>Database: UPDATE device SET lastSeenAt=NOW(), connectionStatus=ONLINE
    Database-->>DeviceService: row updated
```

---

## 2. Telemetry Ingestion to Alert

This sequence covers the hot path: a device publishes a sensor reading, the platform ingests it
into the time-series store, the rules engine evaluates configured thresholds, and—if a rule fires—
an alert is created and a notification is dispatched to the on-call team.

The MQTT Broker acts as the entry point and fans the raw payload into Kafka so that multiple
downstream consumers (the Telemetry Service, the Rules Engine, and any third-party integrations)
can process the same message independently and at their own pace. The Telemetry Service normalises
the JSON payload, tags it with device metadata, and writes it to InfluxDB. The Rules Engine reads
from the same Kafka topic, applies the pre-compiled rule predicates for the device's fleet, and
calls the Alert Service if any threshold is breached. The Alert Service deduplicates in Redis
(preventing alert storms) before persisting the alert and asking the Notification Service to
dispatch an email or SMS.

```mermaid
sequenceDiagram
    autonumber
    participant IoTDevice as IoT Device
    participant MQTTBroker as MQTT Broker
    participant KafkaProducer as Kafka Producer
    participant TelemetryService as Telemetry Service
    participant InfluxDB as InfluxDB
    participant RulesEngine as Rules Engine
    participant AlertService as Alert Service
    participant NotificationService as Notification Service

    IoTDevice->>MQTTBroker: PUBLISH devices/{deviceId}/telemetry\n{temperature:72.4, humidity:55, ts:1700000000}
    MQTTBroker->>KafkaProducer: Forward payload\n(key=deviceId, topic=telemetry-raw)
    MQTTBroker-->>IoTDevice: PUBACK (QoS 1)

    KafkaProducer->>KafkaProducer: Produce record to Kafka\ntopic: telemetry-raw, partition by deviceId

    TelemetryService->>KafkaProducer: Consume from telemetry-raw\n(consumer group: telemetry-service)
    TelemetryService->>TelemetryService: Validate schema (JSON Schema v7)
    TelemetryService->>TelemetryService: Enrich with device metadata\n(fleetId, modelId, timezone)
    TelemetryService->>TelemetryService: Convert units if required by\nstream configuration
    TelemetryService->>InfluxDB: Write point\nmeasurement=telemetry, tags={deviceId,fleetId},\nfields={temperature,humidity}, time=ts
    InfluxDB-->>TelemetryService: 204 No Content
    TelemetryService->>KafkaProducer: Produce to telemetry-enriched\n(for Rules Engine and integrations)

    RulesEngine->>KafkaProducer: Consume from telemetry-enriched\n(consumer group: rules-engine)
    RulesEngine->>RulesEngine: Load active rules for fleetId\n(cached in memory, TTL 60 s)
    RulesEngine->>RulesEngine: Evaluate conditions:\ntemperature > 70 AND fleetId = "warehouse-A"
    RulesEngine->>RulesEngine: Condition matched — Rule ID r-0042

    RulesEngine->>AlertService: CreateAlert(ruleId, deviceId, metric=temperature,\nvalue=72.4, threshold=70)
    AlertService->>AlertService: Check dedup key in Redis\n(ruleId:deviceId TTL 5 min)
    AlertService->>AlertService: Key absent — not a duplicate
    AlertService->>AlertService: Persist alert to PostgreSQL\n(severity=WARNING, status=OPEN)
    AlertService->>AlertService: Set dedup key in Redis (TTL 300 s)
    AlertService->>NotificationService: DispatchNotification(alertId, channels=[email, sms],\nrecipients=["ops@acme.com", "+1-555-0100"])
    NotificationService->>NotificationService: Render template with alert details
    NotificationService->>NotificationService: Send email via SMTP
    NotificationService->>NotificationService: Send SMS via Twilio
    NotificationService-->>AlertService: {emailStatus: SENT, smsStatus: SENT}
    AlertService-->>RulesEngine: alertId created
```

---

## 3. OTA Firmware Deployment

Over-the-Air (OTA) firmware updates are the mechanism by which the platform pushes new firmware
versions to one or many devices without physical access. This sequence begins when an admin uploads
a signed firmware binary and creates an OTA Job targeting a fleet (or a specific device). The OTA
Service orchestrates a controlled rollout: it publishes a notification to affected devices via
Kafka, each device acknowledges the notification, downloads the binary from the Firmware Registry
over HTTPS, applies the update, and reports success or failure. The OTA Service tracks aggregate
progress and marks the job complete only when all targeted devices have responded.

A rollout policy (e.g., canary 10% → 50% → 100% with a 24-hour bake time between waves) is
evaluated by the OTA Service before each wave is released, guarding against fleet-wide outages
caused by a defective firmware build.

```mermaid
sequenceDiagram
    autonumber
    participant Admin as Admin User
    participant APIGateway as API Gateway
    participant OTAService as OTA Service
    participant FirmwareRegistry as Firmware Registry\n(MinIO/S3)
    participant KafkaBroker as Kafka Broker
    participant IoTDevice as IoT Device
    participant Database as PostgreSQL

    Admin->>APIGateway: POST /firmware\n{binary, version:"2.4.1", modelId, releaseNotes}
    APIGateway->>OTAService: UploadFirmware(binary, version, modelId)
    OTAService->>OTAService: Compute SHA-256 checksum
    OTAService->>OTAService: Verify firmware signature\nagainst vendor public key
    OTAService->>FirmwareRegistry: PUT firmware-binaries/{modelId}/{version}.bin
    FirmwareRegistry-->>OTAService: {eTag, presignedDownloadUrl}
    OTAService->>Database: INSERT firmware_version\n(modelId, version, checksum, downloadUrl, status=AVAILABLE)
    Database-->>OTAService: firmware_version row created
    OTAService-->>APIGateway: 201 Created {firmwareVersionId}
    APIGateway-->>Admin: 201 Created {firmwareVersionId}

    Admin->>APIGateway: POST /ota-jobs\n{firmwareVersionId, targetFleetId:"fleet-001",\nrolloutPolicy:{waves:[10,50,100], bakePeriodHours:24}}
    APIGateway->>OTAService: CreateOTAJob(firmwareVersionId, targetFleetId, rolloutPolicy)
    OTAService->>Database: SELECT devices WHERE fleetId=fleet-001\nAND modelId matches AND status=ACTIVE
    Database-->>OTAService: 240 device records
    OTAService->>Database: INSERT ota_job (jobId, firmwareVersionId,\ntotalDevices=240, status=IN_PROGRESS)
    OTAService->>Database: INSERT ota_job_device for wave-1\n(first 24 devices, status=PENDING)
    Database-->>OTAService: rows created

    OTAService->>KafkaBroker: Produce to ota-jobs topic\n(key=deviceId) × 24 messages\n{jobId, firmwareVersionId, downloadUrl, checksum}

    IoTDevice->>KafkaBroker: Consume from ota-jobs\n(subscribed topic: devices/{deviceId}/ota)
    Note over IoTDevice: Device validates job signature\nand checks current firmware version
    IoTDevice->>FirmwareRegistry: GET {downloadUrl} (HTTPS, mTLS)
    FirmwareRegistry-->>IoTDevice: firmware binary stream
    IoTDevice->>IoTDevice: Verify SHA-256 checksum
    IoTDevice->>IoTDevice: Write to inactive partition\n(A/B partition scheme)
    IoTDevice->>KafkaBroker: PUBLISH devices/{deviceId}/ota/progress\n{jobId, status:DOWNLOADED, progress:100}
    KafkaBroker->>OTAService: Consume ota-progress event
    OTAService->>Database: UPDATE ota_job_device SET status=DOWNLOADED

    IoTDevice->>IoTDevice: Reboot into new partition
    IoTDevice->>KafkaBroker: PUBLISH devices/{deviceId}/ota/progress\n{jobId, status:APPLIED, newVersion:"2.4.1"}
    KafkaBroker->>OTAService: Consume ota-progress event
    OTAService->>Database: UPDATE ota_job_device SET status=SUCCESS,\ncompletedAt=NOW()
    OTAService->>OTAService: Check wave-1 success rate\n(24/24 = 100% — proceed to wave-2 after bake)
    OTAService->>Database: UPDATE ota_job SET completedWaves=1,\nsuccessCount+=24
    OTAService-->>APIGateway: Job progress event (wave 1 complete)
    APIGateway-->>Admin: WebSocket push: OTA job wave-1 complete\n(24/240 devices updated)
```

---

## Summary

| Sequence | Primary Trigger | Key Data Stores | Avg Latency Target |
|---|---|---|---|
| Device Registration & First Connection | New device boot | PostgreSQL, CA store | < 3 s end-to-end |
| Telemetry Ingestion to Alert | Sensor publish (MQTT) | Kafka, InfluxDB, PostgreSQL | < 500 ms ingest; < 2 s alert |
| OTA Firmware Deployment | Admin job creation | PostgreSQL, MinIO/S3, Kafka | Asynchronous; wave-scoped |

These three sequences collectively cover the three highest-traffic and highest-risk paths in the
platform. All other interactions (shadow reads/writes, command dispatch, audit log queries) follow
the same layered pattern of API Gateway → microservice → data store, and can be derived from the
principles illustrated here.
