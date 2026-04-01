# Sequence Diagrams — IoT Device Management Platform

## Overview

This document captures the key runtime flows in the IoT Device Management Platform as UML sequence diagrams rendered in Mermaid. Each diagram covers one primary use-case path along with the most critical failure paths. Prose sections before and after each diagram explain the design rationale, failure modes, SLA targets, and operational considerations.

The platform has three primary runtime planes:

- **Device Plane**: MQTT over TLS 1.3, device → EMQX → Kafka
- **Control Plane**: REST/gRPC, operator tools → API Gateway → microservices
- **Data Plane**: Kafka consumers → InfluxDB / PostgreSQL / Redis

All inter-service calls within the cluster use mTLS (SPIFFE/SPIRE-issued SVIDs). Kafka produces and consumes use SASL/SCRAM-512 with per-topic ACLs.

---

## Device Authentication with X.509 Certificates

### Context and Design Rationale

X.509 mutual TLS is the primary authentication mechanism for production devices. Each device holds a unique client certificate issued by the platform CA (or a subordinate CA for enterprise customers with their own PKI). The thumbprint of the certificate (SHA-256 of the DER-encoded cert) is the lookup key throughout the system — it appears in Redis cache entries, PostgreSQL `device_certificates` rows, and EMQX's authentication hook call.

The authentication path is on the critical latency path for every device connection and reconnection. The target SLAs are:

- TLS handshake complete (including client cert validation): **< 200 ms** at the 99th percentile
- Certificate lookup with Redis cache hit: **< 5 ms**
- Certificate lookup with PostgreSQL (cache miss): **< 50 ms**
- Total CONNACK latency (including ACL policy load): **< 300 ms**

Redis caches authentication results with a 300-second TTL, keyed as `cert:auth:{thumbprint}`. This means a certificate revocation takes up to 300 seconds to propagate to all EMQX nodes. For immediate revocation (e.g., compromised device), a Kafka `certificate-revoked` event triggers a Redis `DEL` on the cache key across all nodes via a fan-out consumer on each EMQX node's embedded Erlang process.

### Happy Path and Failure Flows

```mermaid
sequenceDiagram
    autonumber
    participant Device
    participant EMQX_Broker as EMQX Broker
    participant CertService as Cert Service
    participant Redis
    participant PostgreSQL
    participant Kafka
    participant DeviceService as Device Service

    Note over Device,EMQX_Broker: TLS 1.3 ClientHello — cipher suite TLS_AES_256_GCM_SHA384<br/>Device sends client certificate in CertificateVerify message

    Device->>EMQX_Broker: TCP SYN → TLS 1.3 handshake (client cert attached)
    EMQX_Broker->>EMQX_Broker: Verify cert chain against trusted CA pool<br/>(CA certs loaded in-memory at broker startup)

    alt Certificate chain invalid or CA untrusted
        EMQX_Broker-->>Device: TLS Alert: certificate_unknown (42)<br/>Connection closed — no MQTT CONNECT sent
        Note over EMQX_Broker: Metric: emqx_auth_failure_total{reason="invalid_chain"}++
    else Certificate chain valid
        Note over EMQX_Broker: Extract thumbprint = SHA-256(DER(client_cert))<br/>Extract MQTT ClientId from certificate CN field
        EMQX_Broker->>CertService: POST /internal/certs/authenticate<br/>Body: {thumbprint, clientId, remoteIp}

        CertService->>Redis: GET cert:auth:{thumbprint}
        
        alt Cache HIT (TTL remaining > 0)
            Redis-->>CertService: {deviceId, orgId, status, expiresAt} — latency < 5ms
            CertService->>CertService: Check status == ACTIVE && expiresAt > now()
        else Cache MISS
            Redis-->>CertService: nil
            CertService->>PostgreSQL: SELECT dc.*, d.status, d.organization_id<br/>FROM device_certificates dc<br/>JOIN devices d ON d.id = dc.device_id<br/>WHERE dc.thumbprint = $1<br/>AND dc.is_revoked = false<br/>AND dc.not_after > NOW()
            
            alt Certificate not found
                PostgreSQL-->>CertService: 0 rows
                CertService-->>EMQX_Broker: 401 {reason: "certificate_not_found"}
                EMQX_Broker-->>Device: CONNACK rc=135 (Not Authorized)<br/>MQTT 5.0 reason code 0x87
                Note over EMQX_Broker: AuditLog: action=CONNECT_REJECTED, reason=CERT_NOT_FOUND
            else Certificate found
                PostgreSQL-->>CertService: {deviceId, orgId, deviceStatus, notAfter, ...}
                CertService->>Redis: SETEX cert:auth:{thumbprint} 300 {payload}
                Note over CertService: Also check CRL: GET {crlUrl} (cached 3600s in Redis)
            end
        end

        alt Device status == SUSPENDED or DECOMMISSIONED
            CertService-->>EMQX_Broker: 403 {reason: "device_suspended"}
            EMQX_Broker-->>Device: CONNACK rc=135 (Not Authorized)
            EMQX_Broker->>Kafka: Produce → audit-events<br/>{action: CONNECT_BLOCKED, deviceId, reason: SUSPENDED}
        else Certificate revoked (discovered via CRL check)
            CertService->>PostgreSQL: UPDATE device_certificates SET is_revoked=true,<br/>revoked_at=NOW(), revocation_reason='CRL_MATCH'<br/>WHERE thumbprint=$1
            CertService->>Redis: DEL cert:auth:{thumbprint}
            CertService-->>EMQX_Broker: 403 {reason: "certificate_revoked"}
            EMQX_Broker-->>Device: CONNACK rc=135 + DISCONNECT packet (MQTT 5.0)
            EMQX_Broker->>Kafka: Produce → audit-events<br/>{action: CONNECT_BLOCKED, reason: CERT_REVOKED}
        else Authentication successful
            CertService-->>EMQX_Broker: 200 {deviceId, orgId, aclScope}
            Note over EMQX_Broker: Apply ACL: device may PUBLISH to<br/>devices/{deviceId}/telemetry<br/>devices/{deviceId}/shadow/reported<br/>devices/{deviceId}/events<br/>SUBSCRIBE to<br/>devices/{deviceId}/commands<br/>devices/{deviceId}/shadow/desired<br/>devices/{deviceId}/ota
            EMQX_Broker-->>Device: CONNACK rc=0 (Success)<br/>Session Present flag based on persistent session state
            Note over Device: MQTT session established — keepalive 60s<br/>Will message: devices/{deviceId}/status topic, payload={status:offline}

            EMQX_Broker->>Kafka: Produce → device-events<br/>{type: DEVICE_CONNECTED, deviceId, orgId, remoteIp, timestamp}
            Kafka->>DeviceService: Consume device-events (consumer group: device-service)
            DeviceService->>PostgreSQL: UPDATE devices SET last_seen_at=NOW(),<br/>ip_address=$1 WHERE id=$2
            DeviceService->>Redis: HSET device:status:{deviceId} connected true last_seen {ts}
        end
    end
```

### Post-Connection Considerations

After `CONNACK`, EMQX delivers any queued QoS 1/2 messages if the device reconnected with `cleanSession=false` (MQTT 3.1.1) or `cleanStart=false` (MQTT 5.0). Queued commands stored in Redis are drained to the device's command topic by `CommandService`, which subscribes to the `device-events` Kafka topic and reacts to `DEVICE_CONNECTED` events.

**TLS Session Resumption**: EMQX is configured with a TLS session ticket lifetime of 86,400 seconds (24 hours). Devices that reconnect within this window perform an abbreviated TLS 1.3 handshake (0-RTT or 1-RTT), reducing handshake latency from ~150 ms to ~30 ms. The full certificate authentication hook is still called on resumed sessions to enforce revocation checks.

**Cipher Suites**: Only TLS 1.3 cipher suites are accepted: `TLS_AES_256_GCM_SHA384`, `TLS_CHACHA20_POLY1305_SHA256`. TLS 1.2 is disabled at the EMQX listener level except for a legacy compatibility listener on port 8884 that supports `TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384` for constrained devices (e.g., ESP32 with mbedTLS < 3.0).

**MQTT 5.0 Enhanced Authentication**: For devices supporting MQTT 5.0, the `AUTH` packet exchange with `reason_code=0x18` (Continue Authentication) is used for challenge-response PSK flows. This is handled by a separate EMQX plugin and does not go through the `CertService` path described above.

---

## OTA Firmware Update with Canary Rollout and Auto-Rollback

### Context and Design Rationale

OTA deployments are the most operationally complex flow in the platform. The key design goals are:

1. **Integrity**: A device never installs firmware that hasn't been verified against a SHA-256 hash and RSA-PSS signature checked by the platform before the deployment is approved.
2. **Safety**: The canary strategy limits blast radius. A configurable `failureThresholdPct` (default 5%) triggers automatic rollback before the failure propagates to the full fleet.
3. **Resilience**: Devices may be offline. The OTA command is re-queued and retried up to `maxAttempts` (default 3) times with exponential backoff. After exhausting retries, the job is marked `ABANDONED` and excluded from health calculations.
4. **Auditability**: Every state transition for every device job is recorded in PostgreSQL with a timestamp, enabling post-incident analysis.

The presigned S3/MinIO URL given to the device has a TTL of 3,600 seconds. If the device has not started the download within that window (e.g., due to intermittent connectivity), `OTAService` generates a new presigned URL and re-publishes the MQTT command with the updated URL on the next retry cycle.

```mermaid
sequenceDiagram
    autonumber
    participant FleetMgr as Fleet Manager (UI/API)
    participant APIGateway as API Gateway
    participant OTAService as OTA Service
    participant FirmwareStore as MinIO / S3
    participant Kafka
    participant DeviceService as Device Service
    participant MQTTBroker as EMQX Broker
    participant Device
    participant ProgressTracker as Progress Tracker

    Note over FleetMgr,OTAService: Phase 1 — Deployment Creation and Validation

    FleetMgr->>APIGateway: POST /api/v1/ota/deployments<br/>{firmwareVersionId, targetGroupId, strategy:"CANARY",<br/>canaryPct:5, failureThresholdPct:5.0, autoRollback:true}
    APIGateway->>OTAService: Forward request (JWT validated at gateway)
    OTAService->>FirmwareStore: HEAD {fileUrl} — verify object exists, get ETag
    FirmwareStore-->>OTAService: 200 {contentLength, ETag}
    OTAService->>OTAService: Verify RSA-PSS signature over SHA-256(file)<br/>using org's public signing key (fetched from Vault)
    
    alt Signature invalid
        OTAService-->>APIGateway: 422 {error: "firmware_signature_invalid"}
        APIGateway-->>FleetMgr: 422
    else Signature valid
        OTAService->>OTAService: Create OTADeployment record (status=ACTIVE)<br/>Select canary cohort: 5% of devices in targetGroupId<br/>by stable hash(deviceId) % 100 < canaryPct
        OTAService-->>APIGateway: 201 {deploymentId, cohortSize, estimatedDuration}
        APIGateway-->>FleetMgr: 201

        Note over OTAService,Kafka: Phase 2 — Canary Wave Dispatch (5% of fleet)

        loop For each device in canary cohort
            OTAService->>FirmwareStore: GeneratePresignedURL(fileUrl, ttl=3600s)
            FirmwareStore-->>OTAService: presignedUrl
            OTAService->>Kafka: Produce → ota-jobs<br/>{jobId, deviceId, deploymentId, firmwareVersion,<br/>downloadUrl: presignedUrl, sha256, signatureB64,<br/>maxAttempts:3}
        end

        Kafka->>DeviceService: Consume ota-jobs (consumer group: device-svc)
        DeviceService->>MQTTBroker: PUBLISH devices/{deviceId}/ota QoS=1<br/>{command:"OTA_UPDATE", jobId, downloadUrl, sha256,<br/>targetVersion, fileSize}
        MQTTBroker-->>Device: PUBLISH delivered (QoS 1 PUBACK received)
        DeviceService->>OTAService: PATCH /internal/jobs/{jobId} status=NOTIFIED
        OTAService->>Kafka: Produce → ota-progress {jobId, deviceId, status:NOTIFIED}

        Note over Device,ProgressTracker: Phase 3 — Device Download and Install

        Device->>MQTTBroker: PUBLISH devices/{deviceId}/ota/progress<br/>{jobId, event:"DOWNLOAD_STARTED", timestamp}
        MQTTBroker->>Kafka: Bridge → ota-progress topic
        Kafka->>ProgressTracker: Consume ota-progress
        ProgressTracker->>OTAService: Update job status → DOWNLOADING

        Device->>FirmwareStore: GET presignedUrl (HTTPS, chunked, resume-capable)
        FirmwareStore-->>Device: 200 firmware binary (streaming)
        
        Note over Device: Device computes SHA-256 of received bytes<br/>Verifies against provided hash

        alt SHA-256 mismatch
            Device->>MQTTBroker: PUBLISH devices/{deviceId}/ota/progress<br/>{event:"DOWNLOAD_FAILED", reason:"checksum_mismatch"}
            MQTTBroker->>Kafka: Bridge → ota-progress
            Kafka->>ProgressTracker: Consume → mark job DOWNLOAD_FAILED
            ProgressTracker->>OTAService: Evaluate retry: attempt < maxAttempts?

            alt Retry available
                OTAService->>FirmwareStore: GeneratePresignedURL (fresh URL)
                OTAService->>Kafka: Produce → ota-jobs (retry payload, attempt++)
            else Max attempts reached
                OTAService->>Kafka: Produce → ota-progress {status:ABANDONED}
            end
        else Download verified
            Device->>MQTTBroker: PUBLISH devices/{deviceId}/ota/progress<br/>{event:"INSTALL_STARTED"}
            Device->>Device: Write firmware to secondary partition (A/B scheme)<br/>Verify CRC32 of written partition
            Device->>MQTTBroker: PUBLISH devices/{deviceId}/ota/progress<br/>{event:"INSTALL_COMPLETE"}
            Device->>Device: Set boot flag → secondary partition, reboot

            Note over Device,MQTTBroker: ~30–90 second gap during reboot

            Device->>MQTTBroker: MQTT CONNECT (reconnect after reboot)
            Device->>MQTTBroker: PUBLISH devices/{deviceId}/shadow/reported<br/>{firmwareVersion: "2.4.1", bootPartition: "B"}
            MQTTBroker->>Kafka: Bridge → telemetry-enriched (shadow update)
            Kafka->>ProgressTracker: Detect version match for job → REPORTING → COMPLETED
        end

        Note over ProgressTracker,OTAService: Phase 4 — Canary Health Evaluation

        ProgressTracker->>OTAService: Emit canary health metrics every 60s<br/>{completed, failed, abandoned, successRate}
        OTAService->>OTAService: successRate = completed / (completed + failed + abandoned)

        alt successRate >= (1 - failureThresholdPct) AND all canary jobs terminal
            OTAService->>OTAService: Advance to wave 2 (25%), then 75%, then 100%
            Note over OTAService: Each wave repeats Phase 2–4
            OTAService->>Kafka: Produce → audit-events<br/>{action:OTA_WAVE_ADVANCED, deploymentId, wave:2}
        else failureRate > failureThresholdPct AND autoRollback=true
            Note over OTAService: Rollback triggered — failureThresholdPct exceeded

            OTAService->>OTAService: Fetch rollbackFirmwareId (previous stable version)
            OTAService->>Kafka: Produce → ota-jobs for each COMPLETED device<br/>{rollback:true, targetVersion: prevVersion}
            OTAService->>Kafka: Produce → audit-events<br/>{action:OTA_ROLLBACK_TRIGGERED, deploymentId,<br/>failureRate, threshold: failureThresholdPct}
            OTAService->>OTAService: Set deployment status = ROLLING_BACK
        end
    end

    Note over FleetMgr,ProgressTracker: Status Polling

    loop Every 30 seconds (or SSE push)
        FleetMgr->>APIGateway: GET /api/v1/ota/deployments/{id}/progress
        APIGateway->>OTAService: Forward
        OTAService-->>APIGateway: {total, pending, downloading, completed,<br/>failed, abandoned, successRate, currentWave}
        APIGateway-->>FleetMgr: 200 progress payload
    end
```

### Failure Modes and Mitigations

**Device offline at dispatch time**: If a device is offline when `DeviceService` attempts to publish the MQTT command, EMQX returns a no-subscriber indicator. `DeviceService` stores the OTA command in Redis as `ZSET ota:queued:{deviceId}` scored by `expires_at`. On device reconnect (detected via Kafka `DEVICE_CONNECTED` event), the command is drained from the queue and published. If the presigned URL has expired by then, `OTAService` regenerates it before re-queuing.

**Power loss mid-flash**: Devices must implement an A/B partition scheme. If the device fails to boot from the new partition (boot attempts counter > 3), the bootloader reverts to the previous partition and reconnects to MQTT. The `firmwareVersion` in the shadow `reported` state will not match the `targetVersion`, and `ProgressTracker` marks the job `INSTALL_FAILED`. The same retry logic applies.

**Kafka consumer lag**: If `ota-progress` consumer lag exceeds 10,000 messages (monitored via Prometheus `kafka_consumer_lag` metric), the `ProgressTracker` pod is scaled horizontally via HPA. All partition assignments are rebalanced with `CooperativeStickyAssignor` to minimize rebalance overhead.

---

## Alert Rule Evaluation and Notification

### Context and Design Rationale

Alert rule evaluation is a streaming computation: telemetry records flow from devices through Kafka, are enriched by `TelemetryService`, and evaluated against rules in `RulesEngine`. The key design goals are:

1. **Low latency**: Time from telemetry publication to alert notification < 5 seconds for threshold rules, < 30 seconds for window aggregation rules.
2. **Idempotency**: Duplicate Kafka messages (at-least-once delivery) must not create duplicate `AlertEvent` rows. A unique constraint on `(alert_rule_id, device_id, triggered_at::date)` combined with a Redis SETNX cooldown check prevents duplicate firing within the cooldown window.
3. **Cooldown enforcement**: Redis `SETNX alert:cooldown:{ruleId}:{deviceId}` with TTL = `cooldown_seconds` gates evaluation. A SETNX call returning 0 means the alert is suppressed without creating any database record.
4. **Escalation**: If an operator does not acknowledge an alert within `escalation_timeout_seconds`, `AlertService` escalates by publishing to additional notification channels (e.g., PagerDuty, on-call SMS).

```mermaid
sequenceDiagram
    autonumber
    participant Device
    participant MQTTBroker as EMQX Broker
    participant Kafka
    participant TelemetrySvc as Telemetry Service
    participant InfluxDB
    participant RulesEngine as Rules Engine
    participant Redis
    participant PostgreSQL
    participant AlertSvc as Alert Service
    participant NotifSvc as Notification Service
    participant OpsEngineer as Operations Engineer

    Note over Device,MQTTBroker: Telemetry publication — QoS 1

    Device->>MQTTBroker: PUBLISH devices/{deviceId}/telemetry QoS=1<br/>{metric:"temperature", value:87.3, unit:"celsius",<br/>quality:"GOOD", ts:"2024-11-15T14:22:05Z"}
    MQTTBroker-->>Device: PUBACK
    MQTTBroker->>Kafka: EMQX Kafka bridge → telemetry-raw<br/>Key: {orgId}/{deviceId}, Partition by hash(deviceId)

    Note over TelemetrySvc: Consumer group: telemetry-svc<br/>Processes ~50,000 msg/s per partition

    Kafka->>TelemetrySvc: Consume telemetry-raw record
    TelemetrySvc->>Redis: HGETALL device:meta:{deviceId}<br/>(orgId, modelId, groupId, tags)

    alt Cache MISS (device not recently active)
        Redis-->>TelemetrySvc: nil
        TelemetrySvc->>PostgreSQL: SELECT d.organization_id, d.device_model_id,<br/>d.group_id, d.tags, d.status<br/>FROM devices d WHERE d.id=$1 AND d.status='ACTIVE'
        PostgreSQL-->>TelemetrySvc: device metadata
        TelemetrySvc->>Redis: HSET device:meta:{deviceId} ... EX 300
    else Cache HIT
        Redis-->>TelemetrySvc: device metadata
    end

    TelemetrySvc->>TelemetrySvc: Validate against TelemetrySchema for device model<br/>Normalize unit if needed (e.g., °F → °C)<br/>Stamp serverTimestamp, set quality=GOOD/BAD

    TelemetrySvc->>InfluxDB: Write point:<br/>measurement=device_telemetry<br/>tags: org_id, device_id, model_id, group_id, metric<br/>fields: value (Float), quality (Int 0/1/2)<br/>timestamp: deviceTimestamp (nanosecond precision)

    TelemetrySvc->>Kafka: Produce → telemetry-enriched<br/>{orgId, deviceId, groupId, modelId,<br/>metric, value, unit, quality,<br/>deviceTimestamp, serverTimestamp, tags}

    Note over RulesEngine: Consumer group: rules-engine<br/>Stateless — each record evaluated independently

    Kafka->>RulesEngine: Consume telemetry-enriched record
    RulesEngine->>Redis: SMEMBERS rules:active:{orgId}:{groupId}

    alt Rules cache MISS
        Redis-->>RulesEngine: nil
        RulesEngine->>PostgreSQL: SELECT * FROM alert_rules<br/>WHERE organization_id=$1<br/>AND device_group_id IN (SELECT ancestor_id FROM group_ancestors WHERE descendant_id=$2)<br/>AND metric_name=$3 AND is_active=true
        PostgreSQL-->>RulesEngine: matching rules
        RulesEngine->>Redis: SADD rules:active:{orgId}:{groupId} {ruleJson...} EX 60
    else Rules cache HIT
        Redis-->>RulesEngine: rule set (JSON blobs)
    end

    loop For each matching AlertRule
        alt condition_type == THRESHOLD
            RulesEngine->>RulesEngine: Compare value against threshold<br/>e.g., 87.3 > 85.0 (GT operator) → TRUE
        else condition_type == WINDOW_AVERAGE
            RulesEngine->>InfluxDB: Flux query:<br/>from(bucket:"telemetry")<br/>|> range(start:-{windowSeconds}s)<br/>|> filter(fn:(r) => r.device_id=="{deviceId}"<br/>and r.metric=="{metricName}")<br/>|> mean()<br/>→ windowAvg = 84.1
            InfluxDB-->>RulesEngine: {windowAvg: 84.1}
            RulesEngine->>RulesEngine: Compare windowAvg against threshold
        else condition_type == ABSENCE
            RulesEngine->>InfluxDB: Query last point for device/metric within windowSeconds
            InfluxDB-->>RulesEngine: {lastTimestamp}
            RulesEngine->>RulesEngine: Check if lastTimestamp older than windowSeconds
        end

        alt Condition FALSE
            Note over RulesEngine: No action — auto-resolve check if rule.autoResolve=true
        else Condition TRUE
            RulesEngine->>Redis: SET NX EX {cooldownSeconds}<br/>alert:cooldown:{ruleId}:{deviceId}

            alt SETNX returns 0 (cooldown active)
                Note over RulesEngine: Alert suppressed — within cooldown window<br/>No AlertEvent created
            else SETNX returns 1 (cooldown gate opened)
                RulesEngine->>PostgreSQL: INSERT INTO alert_events<br/>(id, alert_rule_id, device_id, organization_id,<br/>triggered_value, status, triggered_at)<br/>VALUES (..., 87.3, 'TRIGGERED', NOW())<br/>ON CONFLICT DO NOTHING
                PostgreSQL-->>RulesEngine: inserted rowId
                RulesEngine->>Kafka: Produce → alert-events<br/>{alertEventId, ruleId, deviceId, orgId,<br/>severity:"CRITICAL", triggeredValue:87.3,<br/>threshold:85.0, metric:"temperature"}
            end
        end
    end

    Note over AlertSvc: Consumer group: alert-svc

    Kafka->>AlertSvc: Consume alert-events record
    AlertSvc->>PostgreSQL: SELECT ar.notification_channels,<br/>ar.escalation_timeout_seconds, ar.severity<br/>FROM alert_rules ar WHERE ar.id=$1
    PostgreSQL-->>AlertSvc: rule config

    AlertSvc->>NotifSvc: POST /internal/notify<br/>{channels:[{type:"EMAIL",recipients:[...]},<br/>{type:"WEBHOOK",url:"..."}],<br/>template:"alert_triggered",<br/>context:{device, metric, value, threshold, severity}}

    NotifSvc->>NotifSvc: Render Jinja2 template with context
    NotifSvc->>OpsEngineer: Send email (SES) + webhook POST (signed HMAC-SHA256)
    NotifSvc-->>AlertSvc: {delivered: ["email", "webhook"], failed: []}

    Note over AlertSvc: Schedule escalation timer<br/>escalation_timeout_seconds = 900 (15 min)

    AlertSvc->>Redis: SET alert:escalation:{alertEventId}<br/>EX {escalationTimeoutSeconds} "pending"

    Note over OpsEngineer: Option A — Operator acknowledges within timeout

    OpsEngineer->>APIGateway: PATCH /api/v1/alerts/{alertEventId}<br/>{action:"acknowledge", notes:"Investigating sensor drift"}
    APIGateway->>AlertSvc: Forward
    AlertSvc->>PostgreSQL: UPDATE alert_events<br/>SET status='ACKNOWLEDGED', acknowledged_at=NOW(),<br/>acknowledged_by={userId}<br/>WHERE id=$1
    AlertSvc->>Redis: DEL alert:escalation:{alertEventId}
    AlertSvc-->>APIGateway: 200
    APIGateway-->>OpsEngineer: 200

    Note over AlertSvc: Option B — Escalation timer fires (operator did not ack)

    AlertSvc->>Redis: GET alert:escalation:{alertEventId}

    alt Key expired (escalation triggered)
        AlertSvc->>PostgreSQL: UPDATE alert_events SET status='ESCALATED',<br/>escalated_at=NOW() WHERE id=$1
        AlertSvc->>NotifSvc: POST /internal/notify<br/>{channels:[{type:"SMS",numbers:["+1..."]},<br/>{type:"PAGERDUTY",integrationKey:"..."}],<br/>template:"alert_escalated"}
        NotifSvc->>OpsEngineer: SMS + PagerDuty incident created
    end

    Note over RulesEngine: Auto-resolution check (if autoResolve=true)<br/>Runs every 30s for TRIGGERED/ACKNOWLEDGED events

    RulesEngine->>InfluxDB: Re-evaluate condition for active alert devices
    alt Condition no longer met (temperature now 79.2 < 85.0)
        RulesEngine->>Kafka: Produce → alert-events {type:AUTO_RESOLVE, alertEventId}
        Kafka->>AlertSvc: Consume AUTO_RESOLVE
        AlertSvc->>PostgreSQL: UPDATE alert_events<br/>SET status='AUTO_CLOSED', resolved_at=NOW(),<br/>auto_resolved=true WHERE id=$1
        AlertSvc->>NotifSvc: POST /internal/notify {template:"alert_resolved"}
        NotifSvc->>OpsEngineer: Alert resolved notification
    end
```

### At-Least-Once Delivery and Idempotency

Kafka provides at-least-once delivery semantics. The `RulesEngine` may re-process the same telemetry record if a consumer crashes after writing to InfluxDB but before committing the Kafka offset. Two safeguards prevent duplicate alerts:

1. **Redis SETNX cooldown key**: The cooldown key acts as an idempotency gate. Even if the same telemetry record triggers the same rule twice within the cooldown window, the second SETNX returns 0 and no `AlertEvent` is created.

2. **PostgreSQL INSERT ON CONFLICT DO NOTHING**: The unique constraint on `alert_events(alert_rule_id, device_id, triggered_at)` (with `triggered_at` truncated to minute granularity for the index) provides a second layer of protection. The `INSERT ... ON CONFLICT DO NOTHING` ensures no duplicate row is created even if the Redis key expired between the two SETNX calls.

### Performance Considerations

- **InfluxDB window queries** are the most expensive operation in the rules evaluation path. Window queries are only executed for `WINDOW_AVERAGE` and `WINDOW_SUM` condition types (~15% of rules). The Flux query uses a `range()` predicate that is pushed down to the TSM storage engine for efficient time-range scanning. With the `device_id` and `metric` tag indexes in InfluxDB, a 5-minute window query returns in < 20 ms at the 95th percentile.
- **Rules cache TTL**: The 60-second Redis TTL on `rules:active:{orgId}:{groupId}` means rule configuration changes (e.g., threshold updates) take up to 60 seconds to propagate. A `CacheInvalidation` Kafka event published by the admin API triggers an immediate `DEL` on the affected cache keys to reduce this lag to < 1 second.
- **Consumer group scaling**: The `rules-engine` consumer group is sized at `numPartitions / 2` pods (default: 12 partitions → 6 pods). Each pod processes ~8,000 records/second. Peak load of 96,000 records/second requires 12 pods; HPA triggers scale-out at 70% CPU utilization.
