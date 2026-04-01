# Cloud Architecture

This document describes the AWS cloud architecture underpinning the Manufacturing Execution System (MES), covering edge computing, real-time telemetry ingestion, analytics, ERP integration, machine learning, and operational observability. Every component is designed for high availability, least-privilege security, and cost-conscious scalability.

---

## Architecture Diagram

```mermaid
flowchart TD
    subgraph PLANT["Plant Floor (On-Premises)"]
        PLC["PLCs / CNCs\n(OPC-UA / Modbus)"]
        IPC["Industrial PC\n(Greengrass v2 Host)"]
        MOQUETTE["Local MQTT Broker\n(Moquette)"]
        MM2["Kafka MirrorMaker 2\n(on-prem → MSK)"]
        DMS_SRC["On-Prem PostgreSQL\n(legacy MES DB)"]
        SAP_ON["SAP S/4HANA\n(on-prem)"]
        PLC -->|OPC-UA / Modbus| IPC
        IPC -->|MQTT pub/sub| MOQUETTE
        MOQUETTE -->|StreamManager\nbuffered upload| IPC
    end

    subgraph EDGE["AWS Greengrass v2 (Edge Runtime on IPC)"]
        GG_LAMBDA["Lambda Edge Components\n(protocol normalisation)"]
        GG_SM["StreamManager\n(store-and-forward)"]
        GG_SHADOW["Shadow Sync Component"]
        GG_NEO["Neo-Compiled LSTM\n(bearing anomaly detector)"]
        IPC --> GG_LAMBDA
        GG_LAMBDA --> GG_SM
        GG_LAMBDA --> GG_NEO
        GG_NEO -->|anomaly score| GG_SM
        GG_SHADOW <-->|device state| IPC
    end

    subgraph IOTCORE["AWS IoT Core"]
        IOT_EP["Custom Domain Endpoint\n(Regional Failover)"]
        IOT_REG["Device Registry\n(Thing Types + Groups)"]
        IOT_RULES["Rules Engine\n(SQL routing)"]
        GG_SM -->|TLS 1.2 + X.509| IOT_EP
        IOT_EP --> IOT_REG
        IOT_EP --> IOT_RULES
    end

    subgraph MSK["Amazon MSK (Kafka)"]
        T_RAW["telemetry-raw\n96 partitions / 24h"]
        T_AGG["telemetry-aggregated\n24 partitions / 7d"]
        T_WO["work-order-events\n12 partitions / 7d"]
        T_QE["quality-events\n12 partitions / 7d"]
        T_OEE["oee-calculated\n12 partitions / 7d"]
        IOT_RULES -->|Kinesis Firehose rule| T_RAW
        IOT_RULES -->|direct MSK rule| T_RAW
        MM2 -->|mTLS| T_RAW
        MM2 -->|mTLS| T_WO
    end

    subgraph EKS["Amazon EKS (Kubernetes)"]
        OEE_SVC["OEECalculatorService\n(on-demand node group)"]
        PM_API["PredictiveMaintenanceAPI\n(on-demand node group)"]
        QA_SVC["QualityAnalyticsService\n(on-demand node group)"]
        BATCH["Batch Analytics Jobs\n(spot node group)"]
        APPMESH["AWS App Mesh\n(mTLS sidecar)"]
        ARGOCD["ArgoCD\n(GitOps)"]
        KEDA["KEDA\n(MSK lag autoscaler)"]
        T_RAW -->|Kafka consumer| OEE_SVC
        T_WO -->|Kafka consumer| OEE_SVC
        T_QE -->|Kafka consumer| QA_SVC
        OEE_SVC -->|produce| T_OEE
        OEE_SVC --- APPMESH
        PM_API --- APPMESH
        QA_SVC --- APPMESH
        KEDA -->|scale| OEE_SVC
        KEDA -->|scale| QA_SVC
        ARGOCD -->|deploy| EKS
    end

    subgraph RDS["Amazon RDS PostgreSQL Multi-AZ"]
        RDS_PRIMARY["Primary Instance\n(us-east-1a)"]
        RDS_STANDBY["Standby Instance\n(us-east-1b)"]
        RDS_REPLICA["Read Replica\n(reporting)"]
        RDS_PRIMARY <-->|sync replication| RDS_STANDBY
        RDS_PRIMARY --> RDS_REPLICA
    end

    subgraph TIMESTREAM["Amazon Timestream"]
        TS_TABLE["machine_metrics table\n(magneticTemperature,\nvibrationRMS, currentDraw)"]
        TS_SQ["Scheduled Queries\n(OEE aggregation)"]
        TS_TABLE --> TS_SQ
    end

    subgraph SAGEMAKER["AWS SageMaker"]
        SM_PROC["SageMaker Processing\n(Pandas / Spark\nfeature engineering)"]
        SM_TRAIN["Training Job\n(LSTM on P3 instances)"]
        SM_REG["Model Registry\n(approval workflow)"]
        SM_EP["Real-Time Endpoint\n(multi-variant A/B)"]
        SM_BATCH["Batch Transform\n(scheduled scoring)"]
        SM_NEO["Neo Compilation\n(edge deployment)"]
        SM_PROC --> SM_TRAIN
        SM_TRAIN --> SM_REG
        SM_REG --> SM_EP
        SM_REG --> SM_BATCH
        SM_REG --> SM_NEO
        SM_NEO -->|IoT Jobs OTA| GG_NEO
    end

    subgraph DATALAKE["S3 Data Lake + Glue + Athena"]
        S3_RAW["s3://mes-data/raw-telemetry/\nyear=/month=/day=/plant=/"]
        S3_PARQUET["s3://mes-data/processed/\n(Parquet, partitioned)"]
        GLUE_CRAWL["Glue Crawlers\n(schema discovery)"]
        GLUE_ETL["Glue ETL Jobs\n(JSON → Parquet)"]
        ATHENA["Athena Workgroups\n(per-team cost control)"]
        LF["Lake Formation\n(column-level security)"]
        IOT_RULES -->|Firehose delivery| S3_RAW
        S3_RAW --> GLUE_CRAWL
        GLUE_CRAWL --> GLUE_ETL
        GLUE_ETL --> S3_PARQUET
        S3_PARQUET --> ATHENA
        LF --> ATHENA
    end

    subgraph QS["Amazon QuickSight"]
        QS_OEE["OEE Dashboard\n(SPICE cached)"]
        QS_PM["Predictive Maintenance\nStatus Dashboard"]
        QS_QT["Quality Trends\n(RLS by plant code)"]
        TS_SQ -->|JDBC| QS_OEE
        ATHENA --> QS_OEE
        ATHENA --> QS_QT
        RDS_REPLICA --> QS_PM
    end

    subgraph SAP_INT["SAP Integration Layer"]
        APIGW["API Gateway\n(REST + VPC Link)"]
        SAP_LAMBDA["Lambda\n(SAP JCo Layer\nRFC/BAPI calls)"]
        IDEM_DB["DynamoDB\n(idempotency table\nSAP doc# dedupe)"]
        APIGW --> SAP_LAMBDA
        SAP_LAMBDA <-->|RFC over Direct Connect| SAP_ON
        SAP_LAMBDA --> IDEM_DB
        SAP_LAMBDA -->|produce| T_WO
    end

    subgraph DEBEZIUM["Change Data Capture"]
        DBZ["Debezium Connector\n(SAP DB → MSK)"]
        DMS["AWS DMS\n(on-prem PG → RDS)"]
        SAP_ON -->|DB log streaming| DBZ
        DBZ -->|CDC events| T_WO
        DMS_SRC -->|DMS replication| RDS_PRIMARY
    end

    subgraph MSK_CONNECT["MSK Connect"]
        JDBC_SINK["JDBC Sink Connector\n(MSK → RDS ERP tables)"]
        T_WO --> JDBC_SINK
        JDBC_SINK --> RDS_PRIMARY
    end

    subgraph NETWORK["Networking"]
        DX["AWS Direct Connect\n(10 Gbps)"]
        VPN["Site-to-Site VPN\n(failover)"]
        SAP_ON -->|primary| DX
        SAP_ON -->|failover| VPN
        DMS_SRC -->|primary| DX
        MM2 -->|primary| DX
    end

    IOT_RULES -->|rule action| TS_TABLE
    T_RAW --> SM_PROC
    OEE_SVC --> RDS_PRIMARY
    QA_SVC --> RDS_PRIMARY
    PM_API --> SM_EP
    T_OEE -->|Kafka consumer| TS_TABLE
```

---

## AWS Greengrass v2 — Edge Computing Layer

Each factory floor hosts one or more industrial PCs running the AWS Greengrass v2 core device runtime. These machines act as the intelligent edge between OT hardware (PLCs, CNC controllers, sensors) and the AWS cloud, enabling local processing, store-and-forward buffering, and on-device ML inference.

### Component Model

Greengrass v2 uses a component-based architecture. The MES deployment ships three categories of components:

**Lambda function components** handle protocol normalisation. A dedicated Lambda component reads OPC-UA and Modbus frames from the local network and transforms them into a canonical JSON telemetry schema before publishing to the Moquette broker. Because this runs in-process on the Greengrass runtime, the round-trip latency from sensor read to normalised message is under 50 milliseconds.

**StreamManager** is the Greengrass-managed store-and-forward subsystem. It persists telemetry streams to local NVMe storage in configurable-size segments and uploads them to AWS IoT Core (and directly to S3 via Kinesis Firehose) as soon as connectivity is available. The MES configures StreamManager with a 48-hour local retention window, ensuring no data is lost during network partitions that commonly occur on plant floors during maintenance windows.

**Shadow sync components** maintain device shadow documents for each machine's configuration state (target spindle speed, quality tolerance thresholds, maintenance mode flags). Shadow desired/reported reconciliation is handled automatically by Greengrass, and EKS services read the shadow over IoT Core's REST API when making scheduling decisions.

### Edge ML Inference

SageMaker Neo-compiled LSTM models run inside a dedicated Greengrass ML inference component. The models are trained in the cloud on bearing vibration time-series data (vibrationRMS, bearing envelope spectrum features) and compiled by SageMaker Neo to target the ARM Cortex-A72 or x86-64 ISA of the edge host, producing quantised TensorFlow Lite or ONNX Runtime artifacts that deliver sub-10 ms inference per sample.

The inference component consumes 4 kHz vibration accelerometer streams from StreamManager, runs a sliding 256-sample window, and emits an anomaly score alongside the raw telemetry. Anomaly scores above the configured threshold trigger a local Greengrass event that illuminates the andon light GPIO and publishes a high-priority alert to a dedicated MQTT topic that bypasses normal batch buffering.

### OTA Deployment via IoT Jobs

All Greengrass component updates — including new ML model artifacts — are delivered through AWS IoT Jobs. A deployment job targets a thing group (e.g., `plant/P1/line/L3`) and Greengrass orchestrates the rollout with configurable rollout rates and abort criteria. A canary deployment to 5% of devices with a 30-minute observation window precedes full fleet rollout, automatically aborting if the reported job failure rate exceeds 2%.

---

## AWS IoT Core — Device Connectivity and Routing

### Device Registry

Every physical machine is registered as an AWS IoT Thing with a structured naming convention: `{plant}-{line}-{machine_type}-{serial}`. Things are assigned to thing types (`CNCMachine`, `WeldingRobot`, `ConveyorBelt`, `QualitySensor`) that carry searchable attributes and define which MQTT topic namespace the device is permitted to use.

Thing groups are hierarchical: a plant-level group (`plant/P1`) contains line-level subgroups (`plant/P1/line/L1`) which contain machine-type subgroups. This hierarchy drives bulk operations: IoT Jobs target groups, and Greengrass deployments push to groups. Fleet indexing is enabled on all thing groups for real-time fleet health queries.

### X.509 Certificate Authentication and IoT Policies

Each device is provisioned with a unique X.509 certificate signed by a private CA registered with AWS IoT Core. Fleet provisioning templates automate certificate issuance at manufacturing time using a claim certificate that exchanges for a production certificate on first boot. The claim certificate is locked to a single provisioning claim action and is revoked after use.

IoT Policies enforce least-privilege MQTT topic ACLs. A CNC machine policy permits publish only to `dt/mes/P1/L1/CNC-${iot:Certificate.Subject.CN}/telemetry` and subscribe only to `cmd/mes/P1/L1/CNC-${iot:Certificate.Subject.CN}/#`. Wildcard publish is explicitly denied. Policy variables (`${iot:ThingName}`, `${iot:Certificate.Subject.CN}`) ensure that a compromised device certificate cannot publish under another device's topic.

### IoT Rules Engine

SQL-based Rules Engine rules route inbound telemetry to multiple downstream systems simultaneously, without any application code:

- **S3 Firehose rule**: all telemetry matching `SELECT * FROM 'dt/mes/+/+/+/telemetry'` is delivered to Kinesis Firehose with a dynamic partitioning prefix (`year/month/day/plant`) and written to the raw S3 prefix with Parquet buffering.
- **MSK rule**: high-frequency telemetry (vibration, current) is routed directly to the `telemetry-raw` MSK topic via the MSK rule action using IAM role-based authentication to the cluster.
- **Timestream rule**: aggregated metric payloads (1-second averages) matching a specific `messageType` field are written directly to Timestream's `machine_metrics` table.
- **DynamoDB rule**: device connection/disconnection lifecycle events update a DynamoDB `device_status` table for real-time fleet dashboard queries.

The custom domain endpoint (`iot.mes.example.com`) is backed by AWS-managed regional failover. During a regional impairment, DNS health checks route devices to a secondary regional endpoint within the regional failover SLA.

---

## Amazon MSK — Managed Kafka Streaming Backbone

### Topic Design

| Topic | Partitions | Retention | Key |
|---|---|---|---|
| `telemetry-raw` | 96 | 24 hours (+ tiered storage) | `{plant}-{line}-{machineId}` |
| `telemetry-aggregated` | 24 | 7 days | `{plant}-{line}-{machineId}` |
| `work-order-events` | 12 | 7 days | SAP work order number |
| `quality-events` | 12 | 7 days | `{plant}-{batchId}` |
| `oee-calculated` | 12 | 7 days | `{plant}-{shift}-{machineId}` |

The `telemetry-raw` partition count of 96 is sized to support 96 concurrent EKS pod consumers at peak, one per partition, with each partition receiving data from a contiguous block of machine IDs per line to maintain locality.

### MSK Tiered Storage

Tiered storage is enabled on `telemetry-raw` and `telemetry-aggregated`. Local broker storage retains 24 hours of high-rate data; older segments are transparently offloaded to S3-backed tiered storage and remain consumable via the standard Kafka consumer API. This eliminates the need to over-provision broker EBS volumes for historical reprocessing and reduces MSK broker storage costs by roughly 70% for long-retention topics.

### Cross-Environment Replication

An on-premises Kafka MirrorMaker 2 cluster replicates events from the legacy factory Kafka deployment into MSK over AWS Direct Connect. MirrorMaker 2 uses mTLS mutual authentication to the MSK cluster and checkpoints consumer group offsets so that failover from on-prem to cloud-native consumers is seamless. The MSK cluster's security group only accepts TLS connections from the Direct Connect VIF attachment.

### MSK Connect — ERP Write-Back

An MSK Connect worker pool running a Kafka JDBC sink connector synchronises `work-order-events` topic records into the RDS `production_orders` and `bom_items` tables. The connector uses exactly-once semantics (EOS) with idempotent producer mode enabled. Schema Registry (AWS Glue Schema Registry) enforces Avro schemas on all topics, preventing malformed messages from reaching downstream consumers.

---

## Amazon EKS — Microservices Runtime

### Node Groups

Two managed node groups run in separate AZs:

**On-demand node group** uses `m6i.2xlarge` instances (8 vCPU / 32 GB) for latency-sensitive services (OEECalculatorService, PredictiveMaintenanceAPI, QualityAnalyticsService). Cluster Autoscaler scales this group between 3 and 30 nodes. Nodes carry a `workload=analytics` taint so only analytics workloads are scheduled here.

**Spot node group** uses a mixed fleet of `m6i.4xlarge`, `m5.4xlarge`, and `c6i.4xlarge` (Spot diversification to reduce interruption probability) for batch jobs such as Glue ETL orchestration sidecars and SageMaker training launchers. Spot interruption handlers drain pods gracefully using the AWS Node Termination Handler daemonset.

### Core Services

**OEECalculatorService** consumes `telemetry-raw` and `work-order-events`, calculates Availability × Performance × Quality per shift per machine using a sliding tumbling window, and produces results to `oee-calculated`. It also writes OEE snapshots to Timestream every 60 seconds.

**PredictiveMaintenanceAPI** exposes a REST API consumed by the MES web portal. It queries SageMaker real-time endpoints for anomaly probability given the latest bearing telemetry, reads maintenance history from RDS, and returns a recommended maintenance action with confidence interval.

**QualityAnalyticsService** consumes `quality-events`, applies statistical process control (SPC) rules (Western Electric rules for Xbar-R charts), and writes out-of-control signals to the `quality-events` downstream topic and to RDS `quality_records`.

### Autoscaling with KEDA

KEDA (Kubernetes Event-Driven Autoscaling) is deployed as a CRD-based operator. It monitors MSK consumer group lag for the `telemetry-raw` consumer group bound to OEECalculatorService. When per-partition lag exceeds 50,000 messages, KEDA triggers a scale-out event, adding a pod per lagging partition until consumer throughput matches producer rate. Scale-in waits for lag to drop below 5,000 messages for 5 consecutive minutes before removing pods, preventing oscillation during bursty production events (shift changeover, batch start).

### Service Mesh and Security

AWS App Mesh provides mTLS between all EKS services using Envoy sidecar proxies. Service-to-service traffic never leaves the VPC unencrypted. App Mesh Virtual Services enforce retry policies (3 retries, exponential backoff) and circuit breakers (5% error rate over 30s trips the breaker for 30s).

ArgoCD watches the `main` branch of the `mes-gitops` repository. Every merged PR that changes a Kubernetes manifest triggers an automatic sync. Deployments use a blue-green strategy: ArgoCD Rollouts shift traffic from blue to green 20% at a time, with automated analysis of Prometheus error rate and p99 latency before each increment.

---

## Amazon RDS PostgreSQL Multi-AZ — Operational Database

### Schema Overview

The MES operational schema is organised around manufacturing entities:

- `production_orders` — header record per SAP production order, including planned vs. actual quantities, target work center, scheduled start/end
- `bom_items` — bill of materials lines linked to production orders, with material numbers and planned consumption quantities
- `work_centers` — physical work centers with capacity calendars and efficiency factors
- `quality_records` — inspection lot results linked to production order and operation, storing measured values, tolerances, and conformance flags

All tables use UUID primary keys, created_at/updated_at timestamps, and soft-delete patterns (deleted_at nullable column) to support CDC event reconstruction.

### Read Replicas and Reporting

A synchronous Multi-AZ standby ensures automatic failover within 60 seconds. An asynchronous read replica in a third AZ serves all reporting and QuickSight queries, isolating analytics workloads from OLTP write traffic. The read replica has `max_connections` tuned to accept RDS Proxy connections from QuickSight's JDBC connector, capped at 200 connections.

### SAP Integration via Debezium

Debezium running on EKS streams PostgreSQL WAL change events from the RDS primary into the `work-order-events` MSK topic. This feeds the MSK Connect JDBC sink connector in the reverse direction for ERP write-back: when the MES updates a `production_orders` record (e.g., records actual yield), Debezium captures the change, the event flows through MSK, and a Lambda function reconciles it into SAP via RFC.

### AWS DMS for Legacy Migration

AWS Database Migration Service runs a continuous replication task from the on-premises legacy PostgreSQL MES database to the RDS primary. Full-load migration seeds initial data; ongoing CDC replication keeps the tables synchronised during the parallel-run cutover period. DMS validation tasks compare row counts and checksums between source and target every 4 hours.

---

## Amazon Timestream — Time-Series Telemetry Store

### Table Design

The `machine_metrics` table stores all sensor measurements with the following dimensions:

- `plant_id`, `line_id`, `machine_id`, `machine_type` (high-cardinality routing dimensions)
- `sensor_type` (magneticTemperature, vibrationRMS, currentDraw, spindleSpeed, feedRate)

Measures are stored as DOUBLE or BIGINT depending on precision requirements. Timestream's columnar storage automatically colocates time-adjacent records from the same machine, making range scans over a single machine's sensor history extremely efficient.

### Scheduled Queries for OEE

Timestream Scheduled Queries compute OEE sub-metrics at 15-minute granularity and materialise results into a `oee_aggregates` table:

- **Availability** = (Scheduled time − unplanned downtime) / Scheduled time, derived from `machine_state` change events
- **Performance** = (Actual cycle count × Ideal cycle time) / Runtime, derived from `spindleSpeed` and `feedRate` against BOM ideal cycle time from RDS
- **Quality** = Conforming parts / Total parts, derived from `quality_events` joined to `production_orders`

The OEE scheduled query runs every 15 minutes with a 5-minute lookback to account for late-arriving telemetry from plant-floor network latency.

### Retention Policy

The memory store retains 1 day of data for sub-second query access. The magnetic store retains 1 year of data for trend analysis and ML feature backfilling. Data older than 1 year is exported via a Timestream scheduled export to S3 Glacier Instant Retrieval for regulatory retention (7 years per ISO 9001 quality record requirements) at a fraction of magnetic store cost.

---

## AWS SageMaker — ML Platform

### Training Pipeline

**Feature engineering** runs on SageMaker Processing Jobs using a PySpark container. The job reads raw vibration telemetry from S3 (`s3://mes-data/raw-telemetry/`), computes bearing envelope spectrum features (RMS, kurtosis, crest factor, band-pass energy in 1–5 kHz), and writes training-ready Parquet datasets to `s3://mes-data/features/`.

**Model training** uses a custom LSTM container (PyTorch Lightning) submitted as a SageMaker Training Job on `ml.p3.2xlarge` instances. The model architecture is a stacked 3-layer LSTM with dropout, trained on 90-day rolling windows of per-bearing vibration sequences. Training pipelines are orchestrated by SageMaker Pipelines with conditional steps: if validation RMSE exceeds a threshold, the pipeline halts and sends a CloudWatch alarm rather than registering a flawed model.

### Model Registry and Approval Workflow

All trained model versions are registered in the SageMaker Model Registry under the `BearingAnomalyDetector` model package group. A registered model starts in `PendingManualApproval` status. A data scientist reviews model card metrics (validation RMSE, precision-recall curve, drift report from SageMaker Clarify) in the SageMaker Studio UI and moves the model to `Approved` status. An EventBridge rule fires on approval, triggering a Lambda that deploys the model to the real-time endpoint and kicks off Neo compilation for edge delivery.

### Inference Paths

**Real-time endpoints** host two production variants for A/B testing: `current-prod` (90% traffic weight) and `challenger` (10% traffic weight). Endpoint invocation metrics (latency, invocations per variant) are captured in CloudWatch. A SageMaker Experiments trial tracks the A/B outcome metrics so the data science team can make a statistically grounded promotion decision.

**Batch Transform** jobs run nightly, scoring the entire fleet's 24-hour vibration history against the approved model and writing anomaly scores to `s3://mes-data/batch-scores/`. These scores are loaded into Timestream and surfaced on the predictive maintenance QuickSight dashboard.

**Edge deployment** via SageMaker Neo compiles the approved PyTorch model to a target-architecture-specific artifact (TFLite for ARM, ONNX for x86-64) and uploads it to the Greengrass component store. An IoT Jobs OTA deployment pushes the artifact to the edge fleet with canary rollout as described in the Greengrass section.

---

## S3 Data Lake, Glue, and Athena

### S3 Prefix Layout

```
s3://mes-data/
  raw-telemetry/
    year=YYYY/month=MM/day=DD/plant=P1/line=L1/
      *.json.gz          (Firehose delivery, ~5 MB files)
  processed/
    telemetry/
      year=YYYY/month=MM/day=DD/plant=P1/
        *.parquet         (Glue ETL output, Snappy compressed)
    quality/
      year=YYYY/month=MM/day=DD/plant=P1/
        *.parquet
  features/              (SageMaker Processing output)
  batch-scores/          (SageMaker Batch Transform output)
  athena-results/        (per-workgroup query result prefixes)
```

Hive-style partitioning in the `processed/` prefix enables Athena partition pruning. A query filtering on `year=2025 AND month=01 AND plant=P1` reads only the matching S3 objects rather than scanning the full dataset.

### Glue Crawlers and ETL

**Glue Crawlers** run hourly against `raw-telemetry/` prefixes, discovering new partitions and updating the Data Catalog. Schema evolution is handled by crawler classification rules that treat additive new fields as non-breaking and emit a CloudWatch alarm for breaking changes (field type change, field removal).

**Glue ETL jobs** run on a 30-minute trigger, reading newly landed JSON files from `raw-telemetry/`, applying the Glue DynamicFrame schema mapping (type coercion, field renaming for consistency), converting to Parquet with Snappy compression, and writing partitioned output to `processed/telemetry/`. The Glue job uses bookmark state to avoid reprocessing files, and job metrics (records processed, bytes read/written) are published to CloudWatch.

### Athena Workgroups and Cost Control

Three Athena workgroups isolate teams:

- `analytics-team`: 10 GB per-query data scan limit, results in `s3://mes-data/athena-results/analytics/`
- `data-engineering`: 100 GB per-query limit for ETL validation queries
- `ml-team`: 50 GB per-query limit for feature exploration

Per-workgroup CloudWatch alarms alert when monthly data scanned exceeds budget thresholds.

### Lake Formation Column-Level Security

AWS Lake Formation governs access to the `processed/quality/` tables. Quality inspectors have column-level permissions excluding the `inspector_id` and `batch_formula` columns (trade-secret protection). Plant managers have full column access scoped by a row-filter on their `plant_id`. Cross-account access for the corporate data warehouse is granted via Lake Formation cross-account grants without requiring S3 bucket policy changes.

---

## Amazon QuickSight — Business Intelligence

### Datasets and SPICE

Three primary datasets feed the MES analytics portal:

**OEE Dashboard dataset** joins the Timestream `oee_aggregates` scheduled query output (via JDBC connector) with the RDS `work_centers` table for plant/line metadata. SPICE caching refreshes every 15 minutes, delivering sub-second filter interactions on the dashboard.

**Predictive Maintenance Status dataset** queries the SageMaker batch score S3 output via Athena and joins it with the RDS `work_centers` and maintenance history tables. A calculated field maps anomaly score ranges to traffic-light status indicators (green/amber/red) for operator-friendly display.

**Quality Trends dataset** reads from the Lake Formation-governed Athena table. Row-level security is enforced via a QuickSight RLS dataset rule that maps the `${user:username}` QuickSight attribute to a `plant_id` allow-list stored in a DynamoDB-backed Lambda custom data source.

### Embedded Analytics

QuickSight dashboards are embedded in the MES web portal using the QuickSight Embedding SDK. The portal backend exchanges a Cognito JWT for a QuickSight session URL via the `GenerateEmbedUrlForRegisteredUser` API. The embedding preserves row-level security: the embedded session inherits the QuickSight user's RLS context, so operators only see data for their assigned plant.

---

## SAP S/4HANA Integration

### API Gateway and Lambda Middleware

An Amazon API Gateway REST API with VPC Link integration proxies requests to a Lambda function running inside the VPC. This Lambda function acts as the SAP middleware, carrying the SAP Java Connector (JCo) as a Lambda layer (JCo native libraries bundled for the `provided.al2` runtime).

Lambda invokes SAP RFC/BAPI functions over a TCP connection that traverses AWS Direct Connect to the on-premises SAP system. The Lambda function is configured with a 29-second timeout (aligned to API Gateway's maximum) and a reserved concurrency of 50 to prevent overwhelming the SAP application server's RFC connection pool.

### Event Flows

**Production order creation**: When SAP creates a production order, the Debezium connector captures the database change and publishes a `ProductionOrderCreated` Avro event to `work-order-events`. The OEECalculatorService and QualityAnalyticsService both consume this event to initialise per-order tracking state in RDS.

**Goods receipt**: When a goods receipt is posted in SAP, a BAPI_GOODSMVT_CREATE RFC is mirrored to a `GoodsReceiptPosted` event via the Debezium → MSK pipeline. The inventory management module in MES consumes this event to update material stock levels in the MES operational database.

**Production confirmation write-back**: When MES records an actual production quantity (operation confirmed), an `OperationConfirmed` event flows from `work-order-events` → Lambda → SAP BAPI_PRODORD_CREATE_HDR_CONF to post the confirmation in SAP PP. This keeps SAP and MES in sync without a nightly batch reconciliation job.

### Idempotency

Every SAP document number (production order number, goods movement document number) is used as a deduplication key in a DynamoDB `sap_integration_idempotency` table with a 24-hour TTL. Before invoking any write-side BAPI, the Lambda function checks whether this SAP document number has already been processed. If the key exists, the function returns the cached result without re-invoking SAP, preventing duplicate postings in the event of Lambda retry or Kafka consumer redelivery.

---

## High Availability Strategy

### Multi-AZ Deployment

Every stateful service runs across at least two Availability Zones:

- **RDS PostgreSQL**: synchronous Multi-AZ standby with automatic failover
- **MSK**: broker replicas spread across three AZs; replication factor 3, minimum in-sync replicas 2
- **EKS node groups**: pod anti-affinity rules enforce distribution of OEECalculatorService and QualityAnalyticsService replicas across AZs
- **ElastiCache (session store)**: Multi-AZ Redis cluster mode for the MES web portal session layer
- **DynamoDB**: globally replicated by default; used for the idempotency table and device status table

### Recovery Objectives

| Service Tier | RTO | RPO | Mechanism |
|---|---|---|---|
| Telemetry ingestion (IoT Core + MSK) | 2 minutes | 30 seconds | Regional failover endpoint, MSK replication |
| Analytics services (EKS) | 15 minutes | 5 minutes | Multi-AZ pods, Kafka consumer replay |
| Operational DB (RDS) | 60 seconds | Near-zero | Synchronous Multi-AZ standby |
| SAP integration (Lambda) | 5 minutes | Transaction-level | DynamoDB idempotency + SAP retry |
| Edge telemetry (Greengrass) | N/A (local) | 48 hours | StreamManager local persistence |

### Network Redundancy

AWS Direct Connect provides 10 Gbps dedicated connectivity between the on-premises plants and the AWS VPC. A Site-to-Site VPN runs in active-passive standby over the public internet as a failover path. BGP route health injection automatically withdraws the Direct Connect prefix during a link impairment, causing traffic to fail over to the VPN path within 30 seconds.

---

## Cost Optimisation

### MSK Tiered Storage

Enabling MSK Tiered Storage on `telemetry-raw` shifts data older than 24 hours to S3-backed cold storage billed at $0.023/GB-month versus $0.10/GB-month for local broker EBS storage. At a telemetry ingest rate of 50 GB/day per plant, tiered storage reduces the weekly `telemetry-raw` storage cost by approximately 77%.

### EKS Spot Instances for Batch Workloads

SageMaker training job launchers, Glue ETL orchestration sidecars, and Athena-result post-processing jobs run on the Spot node group. Spot pricing for the mixed `m6i.4xlarge`/`m5.4xlarge`/`c6i.4xlarge` fleet delivers 60–70% savings versus on-demand. The AWS Node Termination Handler ensures jobs checkpoint their state to S3 before Spot reclamation, allowing seamless restart on a replacement node.

### Timestream vs. S3 Glacier Tiering

Timestream magnetic store at $0.03/GB-month is cost-effective for the 1-year active analytical window. For regulatory 7-year retention, Timestream's scheduled export to S3 Glacier Instant Retrieval at $0.004/GB-month provides a 7.5× cost reduction for cold data that is queried at most a few times per year during audits.

### Reserved Capacity for Stable Workloads

RDS PostgreSQL on `db.r6g.2xlarge` instances is purchased on 1-year Reserved Instance terms (All Upfront), saving 38% versus on-demand. EKS on-demand node group `m6i.2xlarge` instances are covered by Compute Savings Plans at the EC2 Instance Savings Plan level for 30% savings with flexibility across instance sizes within the `m6i` family. SageMaker real-time endpoint instances (`ml.m5.xlarge`) are reserved via SageMaker Savings Plans.

### Right-Sizing and Observability

AWS Cost Explorer anomaly detection monitors daily spend per service. Container Insights metrics (CPU/memory utilisation per pod) feed a weekly right-sizing review that adjusts EKS pod resource requests, preventing over-provisioning. Athena cost per workgroup is tracked via CloudWatch dashboards, and workgroups exceeding monthly data scan budgets receive automated notifications to the owning team.
