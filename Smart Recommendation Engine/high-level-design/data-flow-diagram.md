# Data Flow Diagram — Smart Recommendation Engine

## Overview

This document presents the data flows of the Smart Recommendation Engine using a three-level DFD hierarchy. Level 0 gives the system-in-context view; Level 1 decomposes the engine into its six major processes and their data stores; subsequent sections drill into specific high-value flows: real-time recommendation serving, model training, and interaction ingestion.

---

## Level 0 — Context Diagram (System Boundary)

The Level 0 diagram shows the Smart Recommendation Engine as a single process surrounded by the external entities that produce or consume data. It establishes the system boundary and names every external data flow.

```mermaid
flowchart LR
    USER(("👤 End User\n(Shopper)"))
    ECOM["🛒 E-Commerce\nPlatform"]
    MLPLAT["🔬 ML Platform\n(MLflow)"]
    FEAT["📦 Feature Store\n(Feast/Tecton)"]
    ANALYTICS["📊 Analytics\nPlatform"]
    EMAIL["📧 Email Marketing\nPlatform"]

    SRE["🤖 Smart\nRecommendation\nEngine"]

    USER -- "Recommendation\nRequests (HTTPS/JSON)" --> SRE
    SRE -- "Ranked Item Lists\n(JSON)" --> USER

    USER -- "Interaction Events\n(click/view/purchase)" --> SRE

    ECOM -- "Catalog Updates\n(item upsert/delete)" --> SRE
    ECOM -- "User Profiles\n(demographics, signup)" --> SRE
    SRE -- "Recommendation\nAPI Responses" --> ECOM

    MLPLAT -- "Model Artefacts\n(weights, ONNX)" --> SRE
    SRE -- "Training Metrics\n(NDCG, MAP@K)" --> MLPLAT
    SRE -- "Experiment Results\n(CTR lift, p-value)" --> MLPLAT

    FEAT -- "Feature Vectors\n(user + item embeddings)" --> SRE
    SRE -- "Feature Materialisation\nRequests" --> FEAT

    SRE -- "Impression &\nInteraction Events" --> ANALYTICS
    ANALYTICS -- "Aggregated Reports\n(CTR, CVR, Diversity)" --> SRE

    SRE -- "Pre-computed\nRecommendations\n(top-N per user)" --> EMAIL
```

---

## Level 1 — System Decomposition

Level 1 breaks the engine into six major processes and identifies the data stores each process reads from or writes to.

```mermaid
flowchart TB
    %% ── External Entities ──────────────────────────────────
    USER(("👤 User"))
    DS(("👨‍🔬 Data\nScientist"))
    ECOM["🛒 E-Commerce\nPlatform"]
    EMAIL["📧 Email\nMarketing"]

    %% ── Process Nodes ──────────────────────────────────────
    P1["1.0\nInteraction\nIngestion"]
    P2["2.0\nFeature\nComputation"]
    P3["3.0\nModel\nTraining"]
    P4["4.0\nReal-time\nServing"]
    P5["5.0\nA/B Testing\n& Analytics"]
    P6["6.0\nBatch\nRecommendation"]

    %% ── Data Stores ────────────────────────────────────────
    D1[("D1\nItem Store\n(PostgreSQL +\nQdrant)")]
    D2[("D2\nInteraction\nStore\n(Kafka + S3\nParquet)")]
    D3[("D3\nFeature Store\n(Redis online +\nS3 offline)")]
    D4[("D4\nModel Registry\n(MLflow)")]
    D5[("D5\nRecommendation\nCache\n(Redis)")]
    D6[("D6\nAnalytics Store\n(ClickHouse)")]
    D7[("D7\nExperiment\nConfig Store\n(PostgreSQL)")]

    %% ── External → Process ─────────────────────────────────
    USER -- "Interaction Events\n{userId, itemId, action}" --> P1
    ECOM -- "Catalog Payloads\n(item attributes)" --> P1
    DS -- "Training Config\n(algorithm, hyperparams)" --> P3
    DS -- "Recommendation Request\n(test/preview)" --> P4
    USER -- "Recommendation\nRequest" --> P4

    %% ── P1: Interaction Ingestion ──────────────────────────
    P1 -- "Validated Events\n(Avro)" --> D2
    P1 -- "Item Records\n(JSON)" --> D1

    %% ── P2: Feature Computation ────────────────────────────
    D2 -- "Raw Events\n(Parquet)" --> P2
    D1 -- "Item Attributes" --> P2
    P2 -- "User Feature Vectors\n(Float[128])" --> D3
    P2 -- "Item Embeddings\n(Float[128])" --> D3

    %% ── P3: Model Training ─────────────────────────────────
    D3 -- "Training Snapshots\n(S3 Parquet)" --> P3
    D2 -- "Interaction Labels\n(implicit feedback)" --> P3
    P3 -- "Trained Model\nArtefact + Metrics" --> D4

    %% ── P4: Real-time Serving ──────────────────────────────
    D3 -- "User Feature Vector\n(Float[128])" --> P4
    D3 -- "Item Feature Vectors" --> P4
    D4 -- "Model Weights\n(loaded on startup)" --> P4
    D1 -- "Item Eligibility\n(price, stock)" --> P4
    D7 -- "Variant Config\n(model version,\nparams)" --> P4
    D5 -- "Cached Response\n(30s TTL)" --> P4
    P4 -- "Recommendation\nResult (JSON)" --> USER
    P4 -- "Impression Events" --> D6
    P4 -- "Cache Write\n(key: userId+context)" --> D5

    %% ── P5: A/B Testing & Analytics ────────────────────────
    D6 -- "Impression + Click\nEvents" --> P5
    D2 -- "Conversion Events\n(purchase)" --> P5
    P5 -- "Experiment Results\n(CTR, CVR, NDCG)" --> D7
    P5 -- "Aggregated Metrics\n(per-variant KPIs)" --> D6
    P5 -- "Statistical Report" --> DS

    %% ── P6: Batch Recommendation ───────────────────────────
    D4 -- "Champion Model" --> P6
    D3 -- "All User Vectors\n(S3 offline)" --> P6
    D1 -- "Active Item Pool" --> P6
    P6 -- "Pre-computed Recs\n(top-50 per user)" --> D5
    P6 -- "Personalised\nDigest Payload" --> EMAIL
```

---

## Level 2 — Real-Time Recommendation Serving (Process 4.0)

This diagram zooms into the real-time serving process, showing every sub-step and the exact data format moving between them.

```mermaid
flowchart TB
    REQ["📥 Recommendation\nRequest\n{userId, context, limit}"]

    P4_1["4.1\nAuthenticate &\nRoute Request\n(JWT verify,\nrate-limit check)"]
    P4_2["4.2\nA/B Variant\nResolution\n(deterministic hash\nbucketing)"]
    P4_3["4.3\nFeature Lookup\n(Redis online store\np99 <5ms)"]
    P4_4["4.4\nCandidate\nGeneration\n(ANN search\nQdrant top-200)"]
    P4_5["4.5\nML Scoring\n(TorchServe / ONNX\nbatch inference)"]
    P4_6["4.6\nBusiness Rule\nFiltering\n(stock, price,\nexclusions)"]
    P4_7["4.7\nDiversity\nRe-ranking\n(MMR lambda=0.5)"]
    P4_8["4.8\nSponsored\nSlot Injection\n(at configured\npositions)"]
    P4_9["4.9\nResponse\nAssembly &\nCache Write"]

    D3[("Feature Store\n(Redis)")]
    D1[("Item Store\n(PostgreSQL)")]
    D4[("Model Registry\n(MLflow / TorchServe)")]
    D5[("Rec Cache\n(Redis 30s TTL)")]
    D7[("Experiment Config\n(PostgreSQL)")]
    KAFKA["📨 Kafka\nImpressions Topic"]

    REQ --> P4_1
    P4_1 -->|"userId + context"| P4_2
    P4_2 -->|"variant: {modelId,\noverrideParams}"| D7
    D7 -->|"ExperimentVariant"| P4_3
    P4_3 -->|"read user vector\nFloat[128]"| D3
    D3 -->|"userFeatureVector"| P4_4
    P4_4 -->|"ANN query:\nuserEmbedding"| D4
    D4 -->|"top-200 candidates\n[(itemId, score)]"| P4_5
    P4_5 -->|"batch score request\n(user + item features)"| D3
    D3 -->|"itemFeatureVectors"| P4_5
    P4_5 -->|"scored candidates\n[(itemId, predictedCTR)]"| P4_6
    P4_6 -->|"eligibility check\n(inStock, price)"| D1
    D1 -->|"eligible items"| P4_7
    P4_7 -->|"re-ranked list\n(relevance + diversity)"| P4_8
    P4_8 -->|"final ranked list\n(limit N)"| P4_9
    P4_9 -->|"write {key,recs,TTL}"| D5
    P4_9 -->|"async publish\nImpressionEvent"| KAFKA
    P4_9 -->|"RecommendationResult\n(JSON)"| RESP["📤 HTTP Response"]
```

---

## Level 2 — Model Training Data Flow (Process 3.0)

```mermaid
flowchart LR
    subgraph INGEST["Interaction Data Pipeline"]
        EV["Raw Events\n(interactions.raw\nKafka topic)"]
        SP["Spark Streaming\nConsumer"]
        S3RAW[("S3 Raw\nParquet\n(partitioned by date)")]
        S3FEAT[("S3 Feature\nSnapshots\n(materialised)")]
    end

    subgraph TRAIN["Training Pipeline (Spark + PyTorch)"]
        READER["Training Data\nReader\n(Feast offline SDK)"]
        SPLIT["Train / Val / Test\nSplit\n(temporal holdout)"]
        ALS["Spark ALS\nCollaborative Filtering"]
        NCF["PyTorch NCF\n(Neural CF, GPU)"]
        B4R["BERT4Rec\n(Transformer,\nHuggingFace)"]
    end

    subgraph EVAL["Evaluation & Gate"]
        OFFEVAL["Offline Metrics\n(NDCG@10, MAP@K\nCoverage, ILD)"]
        FAIR["Fairness Audit\n(AIF360\nDisparate Impact)"]
        GATE{"Passes\nProduction\nGate?"}
    end

    subgraph REGISTRY["MLflow Model Registry"]
        MLFLOW[("MLflow\nExperiment Run\n+ Artefact Store")]
        STAGE_S["Stage: Staging"]
        STAGE_P["Stage: Production"]
    end

    subgraph SERVING["Model Serving Hot-Reload"]
        TORCHSERVE["TorchServe\nModel Handler"]
        QDRANT[("Qdrant\nEmbedding Index\n(refreshed)")]
    end

    EV --> SP
    SP --> S3RAW
    S3RAW --> READER
    S3FEAT --> READER
    READER --> SPLIT
    SPLIT --> ALS
    SPLIT --> NCF
    SPLIT --> B4R
    ALS -->|"model artefact\n+ metrics"| MLFLOW
    NCF -->|"model artefact\n+ metrics"| MLFLOW
    B4R -->|"model artefact\n+ metrics"| MLFLOW
    MLFLOW --> OFFEVAL
    OFFEVAL --> FAIR
    FAIR --> GATE
    GATE -- "Yes" --> STAGE_S
    GATE -- "No" --> BLOCKED["🚫 Blocked\n(alert ML team)"]
    STAGE_S -->|"Data Scientist\napproves"| STAGE_P
    STAGE_P -->|"model.deployed\nKafka event"| TORCHSERVE
    STAGE_P -->|"item embeddings\nrefresh"| QDRANT
```

---

## Level 2 — Interaction Ingestion Data Flow (Process 1.0)

```mermaid
flowchart TB
    subgraph CAPTURE["Event Capture"]
        BROWSER["🌐 Browser / App\nSDK"]
        COLL_API["Interaction Collector\nAPI\n(FastAPI, 10K+ ev/s)"]
        DEDUP[("Redis Dedup\nCache\n(event_id TTL=60s)")]
    end

    subgraph STREAM["Kafka Event Bus"]
        KAFKA_RAW["Topic:\ninteractions.raw\n(keyed by userId)"]
    end

    subgraph CONSUMERS["Downstream Consumers"]
        FEAT_CONS["Feature Store\nConsumer\n(update user vector\nin Redis)"]
        ANALYTICS_CONS["Analytics\nConsumer\n(ClickHouse insert:\nCTR, CVR counters)"]
        TRAINING_CONS["Training Pipeline\nConsumer\n(accumulate S3\nParquet daily)"]
        COLD_CONS["Cold Start\nConsumer\n(detect first\nN interactions)"]
    end

    subgraph STORES["Data Stores Updated"]
        REDIS_USER[("Redis\nUser Feature\nVectors")]
        CLICKHOUSE[("ClickHouse\nAnalytics\nEvents")]
        S3_PARQUET[("S3 Parquet\nTraining\nDataset")]
        PG_PROFILE[("PostgreSQL\nUser Profile\nCold Start Flag")]
    end

    BROWSER -->|"POST /v1/events\n{userId, itemId, action\ntimestamp, sessionId}"| COLL_API
    COLL_API -->|"check event_id\nexists?"| DEDUP
    DEDUP -- "duplicate\n→ discard" --> COLL_API
    DEDUP -- "new event\n→ set key" --> COLL_API
    COLL_API -->|"publish Avro\nInteractionEvent"| KAFKA_RAW
    COLL_API -->|"202 Accepted\n(immediate return)"| BROWSER

    KAFKA_RAW --> FEAT_CONS
    KAFKA_RAW --> ANALYTICS_CONS
    KAFKA_RAW --> TRAINING_CONS
    KAFKA_RAW --> COLD_CONS

    FEAT_CONS -->|"HSET user:{id}:vector\n(sliding window update)"| REDIS_USER
    ANALYTICS_CONS -->|"INSERT INTO\ninteractions_mv"| CLICKHOUSE
    TRAINING_CONS -->|"s3.put_object\n(daily compaction)"| S3_PARQUET
    COLD_CONS -->|"UPDATE users SET\ncold_start_phase"| PG_PROFILE
```

---

## Data Schemas at Key Boundaries

### Interaction Event (Avro — Kafka)
```json
{
  "interactionId": "uuid-v4",
  "userId": "string",
  "itemId": "string",
  "actionType": "enum[view|click|add_to_cart|purchase|rating|skip]",
  "explicitRating": "float|null",
  "timestamp": "long (epoch ms)",
  "sessionId": "string",
  "pageContext": "string",
  "deviceType": "enum[web|ios|android]",
  "contextData": "map<string, string>"
}
```

### Feature Vector (Redis HSET)
```
Key:   feat:user:{userId}
Field: embedding      → Float[128] (MessagePack encoded)
Field: last_10_items  → JSON array of itemIds
Field: category_affinity → JSON map {category: score}
Field: computed_at    → ISO-8601 timestamp
Field: feature_set_v  → "v2.3"
```

### Recommendation Response (JSON)
```json
{
  "requestId": "uuid-v4",
  "userId": "string",
  "items": [
    {
      "position": 1,
      "itemId": "string",
      "title": "string",
      "imageUrl": "string",
      "price": 29.99,
      "score": 0.94,
      "explanation": "Based on your recent purchases",
      "isSponsored": false
    }
  ],
  "modelVersion": "als-v3.2.1",
  "experimentVariant": "treatment_neural_v2",
  "inferenceLatencyMs": 42,
  "generatedAt": "ISO-8601"
}
```

---

## Release Gate Checklist

- [ ] All Kafka topics provisioned with correct partition counts and replication factors.
- [ ] Avro schemas registered and backward-compatible in schema registry.
- [ ] Deduplication TTL validated against expected event burst window.
- [ ] S3 Parquet compaction job tested for correctness and idempotence.
- [ ] Feature freshness SLA (≤5 min lag from event to online store) validated under load.
- [ ] Offline → online feature parity test passes (no training-serving skew detected).
