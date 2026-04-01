# System Sequence Diagrams — Smart Recommendation Engine

## Overview

This document contains system-level sequence diagrams (SSDs) for the four most important interaction scenarios in the Smart Recommendation Engine. Each SSD shows the messages exchanged between actors and system components, including synchronous calls, asynchronous events, error/fallback paths, and timing annotations.

---

## SSD-01: Real-Time Recommendation Request (Happy Path)

**Trigger**: A logged-in user loads a product discovery page.  
**Goal**: Return a ranked, diversified, experiment-aware list of up to N recommendations within 100 ms (p99).  
**Preconditions**: JWT is valid; user has at least one prior interaction (warm user).

```mermaid
sequenceDiagram
    autonumber
    actor Browser as 🌐 User Browser
    participant NGINX as Nginx\nReverse Proxy
    participant REDIS_CACHE as Redis\nAPI Cache
    participant REC_API as Recommendation API\n(FastAPI)
    participant AB_SVC as A/B Testing\nService
    participant FEAT_SVC as Feature Store\nService (Redis)
    participant MODEL_SVC as Model Serving\n(TorchServe)
    participant QDRANT as Qdrant\nVector Index
    participant RANK_SVC as Ranking\nLogic (in-process)
    participant PG as PostgreSQL\n(Item Eligibility)
    participant KAFKA as Kafka\n(impressions topic)

    Browser->>+NGINX: GET /v1/recommendations?userId=U123&limit=10\nAuthorization: Bearer <JWT>

    NGINX->>+REDIS_CACHE: GET rec:U123:home:10
    REDIS_CACHE-->>-NGINX: MISS (TTL expired)

    NGINX->>+REC_API: forward request + decoded JWT claims

    REC_API->>+AB_SVC: GET /ab/variant\n{userId: U123, experiment: rec_model_v4}
    AB_SVC-->>-REC_API: {variantId: "treatment_neural", modelVersionId: "ncf-v2.1.0"}

    REC_API->>+FEAT_SVC: GET /features/user/U123
    FEAT_SVC-->>-REC_API: {embedding: Float[128], last10Items: [...], categoryAffinities: {...}}

    Note over REC_API,MODEL_SVC: Model Serving performs two-stage retrieval: ANN + scoring

    REC_API->>+MODEL_SVC: gRPC InferRequest\n{userEmbedding: Float[128], modelVersion: "ncf-v2.1.0"}
    MODEL_SVC->>+QDRANT: POST /collections/items/points/search\n{vector: Float[128], top: 200, filter: {inStock: true}}
    QDRANT-->>-MODEL_SVC: [{itemId, score}×200]
    MODEL_SVC->>MODEL_SVC: batch score candidates\n(NCF forward pass, GPU)
    MODEL_SVC-->>-REC_API: [{itemId, predictedCTR}×200]

    REC_API->>+PG: SELECT itemId, price, inStock\nWHERE itemId IN (top-200)
    PG-->>-REC_API: eligibility map {itemId → eligible: bool}

    REC_API->>+RANK_SVC: applyBusinessRules(candidates, eligibilityMap)
    RANK_SVC-->>-REC_API: filteredCandidates (remove OOS, exclude purchased)

    REC_API->>+RANK_SVC: mmrRerank(filteredCandidates, lambda=0.5, limit=10)
    RANK_SVC-->>-REC_API: top10DiversifiedItems

    REC_API->>+REDIS_CACHE: SET rec:U123:home:10 (TTL=30s)\n= serialised response
    REDIS_CACHE-->>-REC_API: OK

    REC_API-->>-NGINX: 200 OK\n{requestId, items[10], modelVersion, variantId, latencyMs}
    NGINX-->>-Browser: 200 OK (gzip compressed)

    REC_API-)KAFKA: async publish ImpressionEvent\n{requestId, userId, itemIds, modelVersion, variantId, ts}

    Note over Browser,KAFKA: Total wall-clock time target: p50 ≤ 40ms, p99 ≤ 100ms
```

### Key Design Decisions in SSD-01
- Steps 3–4: The API cache check happens at Nginx before the Recommendation API is ever invoked, saving the full orchestration cost on cache hits (>60 % of requests in steady state).
- Steps 6–8: Feature lookup and A/B assignment can be parallelised with `asyncio.gather` because they are independent.
- Steps 9–11: Two-tower retrieval (ANN) narrows 2 M items to 200 candidates; NCF scoring then ranks those 200 precisely. This two-stage design keeps latency within budget.
- Step 18: The Kafka publish is fire-and-forget (non-blocking). If Kafka is slow, it does not affect response latency.

---

## SSD-02: Interaction Event Recording

**Trigger**: A user clicks on a recommended item.  
**Goal**: Record the interaction durably, update real-time features, and feed analytics — all without blocking the UI click response beyond 50 ms.

```mermaid
sequenceDiagram
    autonumber
    actor Browser as 🌐 User Browser
    participant COLL_API as Interaction Collector\nAPI (FastAPI)
    participant DEDUP as Redis Dedup\nCache (TTL=60s)
    participant KAFKA as Kafka\n(interactions.raw)
    participant FEAT_CONS as Feature Store\nConsumer
    participant REDIS_FEAT as Redis\nUser Feature Store
    participant ANALYTICS as Analytics Service\nConsumer
    participant CLICKHOUSE as ClickHouse\nAnalytics DB
    participant TRAIN_CONS as Training Pipeline\nConsumer
    participant S3 as S3\nParquet Store

    Browser->>+COLL_API: POST /v1/events\n{interactionId, userId, itemId, action: "click"\ntimestamp, sessionId, pageContext}

    COLL_API->>+DEDUP: EXISTS event:{interactionId}
    DEDUP-->>-COLL_API: 0 (not found — new event)
    COLL_API->>DEDUP: SET event:{interactionId} EX 60
    Note over DEDUP: Duplicate protection\nwindow = 60 seconds

    COLL_API->>COLL_API: validate schema\n(Pydantic InteractionEvent)
    COLL_API->>COLL_API: enrich with serverTimestamp\nand geoIP approximation

    COLL_API->>+KAFKA: produce(topic="interactions.raw"\nkey=userId, value=Avro{...})
    KAFKA-->>-COLL_API: partition=3, offset=10048291

    COLL_API-->>-Browser: 202 Accepted\n{eventId, receivedAt}

    Note over KAFKA,S3: All downstream processing is async — decoupled from API response

    KAFKA->>+FEAT_CONS: consume InteractionEvent (consumer group: feature-store)
    FEAT_CONS->>+REDIS_FEAT: HSET feat:user:U123\n  last_10_items = sliding push(itemId)\n  category_affinity[cat] += decay_weight
    REDIS_FEAT-->>-FEAT_CONS: OK
    FEAT_CONS-->>-KAFKA: commit offset

    KAFKA->>+ANALYTICS: consume InteractionEvent (consumer group: analytics)
    ANALYTICS->>+CLICKHOUSE: INSERT INTO interactions_mv\n(userId, itemId, action, ts, sessionId)
    CLICKHOUSE-->>-ANALYTICS: written
    ANALYTICS->>CLICKHOUSE: UPDATE ctr_hourly SET clicks += 1\nWHERE itemId = X AND hour = H
    ANALYTICS-->>-KAFKA: commit offset

    KAFKA->>+TRAIN_CONS: consume InteractionEvent (consumer group: training)
    TRAIN_CONS->>+S3: append to s3://data/interactions\n/year=YYYY/month=MM/day=DD/part-N.parquet
    S3-->>-TRAIN_CONS: OK
    TRAIN_CONS-->>-KAFKA: commit offset
```

### Key Design Decisions in SSD-02
- The Collector API returns `202 Accepted` after Kafka `produce()` succeeds — not after downstream consumers finish. This keeps UI response time <20 ms.
- Redis deduplication prevents double-counting if the browser retries a failed click event (at-least-once Kafka delivery).
- All three consumer groups (feature-store, analytics, training) read independently from the same Kafka partition, applying exactly-once semantics via committed offsets.

---

## SSD-03: Model Training and Deployment

**Trigger**: A data scientist submits a new training job via the ML API, or a nightly scheduled CronJob fires.  
**Goal**: Train a new model version, evaluate it, gate it through fairness checks, and deploy it to production — with the running recommendation service experiencing zero downtime.

```mermaid
sequenceDiagram
    autonumber
    actor DS as 👨‍🔬 Data Scientist
    participant TRAIN_API as Training API\n(FastAPI)
    participant K8S as Kubernetes\nJob Controller
    participant SPARK as Spark Cluster\n(ALS) or GPU Pod\n(PyTorch NCF)
    participant S3 as S3\nOffline Feature Store
    participant MLFLOW as MLflow\nTracking + Registry
    participant EVAL_SVC as Evaluation\nService
    participant FAIR_SVC as Fairness Audit\nService
    participant KAFKA as Kafka\n(model events)
    participant MODEL_SVC as Model Serving\n(TorchServe)

    DS->>+TRAIN_API: POST /v1/models/train\n{algorithm: "ncf", hyperparams: {...}\ndataDateRange: "2024-01-01/2024-06-30"}
    TRAIN_API->>+MLFLOW: create_run(experiment="ncf-training")\n→ runId
    MLFLOW-->>-TRAIN_API: runId = "abc123"
    TRAIN_API->>+K8S: create Job spec\n(image: rec-trainer:v3, runId: abc123)
    TRAIN_API-->>-DS: 202 Accepted\n{jobId, mlflowRunId: "abc123", status: "queued"}

    K8S->>+SPARK: schedule training Pod(s)\n(or GPU PyTorch Pod)
    SPARK->>+S3: read training data\n(Parquet: users × items × labels)
    S3-->>-SPARK: 2.4 GB training dataset

    SPARK->>SPARK: split train/val/test (80/10/10 temporal)
    SPARK->>SPARK: train epochs (NCF: 20 epochs, GPU)
    SPARK->>+MLFLOW: log_metric(epoch_loss) ×20
    MLFLOW-->>-SPARK: OK

    SPARK->>+MLFLOW: log_artifact(model_weights.pt)\nlog_param(hyperparams)
    MLFLOW-->>-SPARK: artefact stored at s3://mlflow/abc123/

    SPARK-->>-K8S: Pod completed (exit 0)
    K8S->>+EVAL_SVC: trigger evaluation\n{runId: abc123, modelUri: s3://...}
    EVAL_SVC->>+S3: read holdout test set
    S3-->>-EVAL_SVC: test interactions (10%)
    EVAL_SVC->>EVAL_SVC: compute NDCG@10, MAP@10\nCoverage, ILD, Novelty
    EVAL_SVC->>+MLFLOW: log_metric(ndcg@10=0.312\nmap@10=0.218, coverage=0.67)
    MLFLOW-->>-EVAL_SVC: OK
    EVAL_SVC-->>-K8S: evaluation complete

    K8S->>+FAIR_SVC: trigger fairness audit\n{runId: abc123, protectedAttrs: [gender, age_group]}
    FAIR_SVC->>+S3: read predictions + demographics
    S3-->>-FAIR_SVC: prediction × user demographics
    FAIR_SVC->>FAIR_SVC: compute disparate impact (gender)\ncompute equal opportunity (age_group)
    FAIR_SVC->>+MLFLOW: log_metric(disparate_impact=0.91\nequal_opportunity_diff=0.02)
    MLFLOW-->>-FAIR_SVC: OK

    alt Fairness passes (DI ≥ 0.8)
        FAIR_SVC->>+MLFLOW: set_tag(fairness_status="approved")
        MLFLOW-->>-FAIR_SVC: OK
        FAIR_SVC-->>-K8S: approved
    else Fairness fails (DI < 0.8)
        FAIR_SVC->>MLFLOW: set_tag(fairness_status="blocked")
        FAIR_SVC->>KAFKA: publish BiasThresholdExceeded\n{runId, metric, value, threshold}
        Note over FAIR_SVC,KAFKA: PagerDuty alert triggered via Kafka consumer
        FAIR_SVC-->>K8S: blocked — model cannot be promoted
    end

    DS->>+MLFLOW: transition_model_version_stage\n(version: abc123, stage: "Production")
    MLFLOW->>+KAFKA: publish model.deployed\n{modelId, version, artefactUri, algorithm}
    KAFKA-->>-MLFLOW: ack
    MLFLOW-->>-DS: version promoted

    KAFKA->>+MODEL_SVC: consume model.deployed event
    MODEL_SVC->>+MLFLOW: download artefact\n(model_weights.pt)
    MLFLOW-->>-MODEL_SVC: artefact bytes
    MODEL_SVC->>MODEL_SVC: load model into shadow slot\nwarm-up inference pass (10 requests)
    MODEL_SVC->>MODEL_SVC: atomic swap: shadow → active\n(zero-downtime hot reload)
    MODEL_SVC-->>-KAFKA: commit offset
    Note over MODEL_SVC: New model now serving\n100% of live traffic
```

---

## SSD-04: Cold Start — New User First Visit

**Trigger**: A brand-new user visits the platform for the first time (no prior interactions, no feature vector).  
**Goal**: Serve a useful, non-personalised recommendation fallback immediately, then progressively personalise as the user interacts.

```mermaid
sequenceDiagram
    autonumber
    actor NewUser as 🆕 New User\n(first visit)
    participant REC_API as Recommendation API\n(FastAPI)
    participant USER_SVC as User Profile\nService
    participant PG as PostgreSQL\n(User Profiles)
    participant FEAT_SVC as Feature Store\nService (Redis)
    participant POP_SVC as Popularity\nService (Redis)
    participant CATALOG as Catalog Service\n(PostgreSQL)
    participant KAFKA as Kafka\n(cold-start events)

    NewUser->>+REC_API: GET /v1/recommendations\nAuthorization: Bearer <new-user-JWT>

    REC_API->>+USER_SVC: GET /users/U999/profile
    USER_SVC->>+PG: SELECT * FROM users WHERE userId = 'U999'
    PG-->>-USER_SVC: {userId: U999, createdAt: now, interactionCount: 0}
    USER_SVC-->>-REC_API: UserProfile {coldStartPhase: "cold"\ninteractionCount: 0, featureVector: null}

    REC_API->>+FEAT_SVC: GET /features/user/U999
    FEAT_SVC-->>-REC_API: 404 Not Found\n(no feature vector exists)

    Note over REC_API: Cold-start detected — fallback\nto popularity-based recommendations

    REC_API->>+POP_SVC: GET /popularity/trending\n{context: "homepage", limit: 10, window: "24h"}
    POP_SVC-->>-REC_API: [{itemId, trendingScore, category}×10]\n(pre-aggregated from ClickHouse hourly job)

    REC_API->>+CATALOG: GET /catalog/items?ids=I1,I2,...,I10
    CATALOG-->>-REC_API: [{itemId, title, price, imageUrl, inStock}×10]

    REC_API->>REC_API: assemble response\n(no personalisation, explain="Trending now")
    REC_API-->>-NewUser: 200 OK\n{items[10], modelVersion: "popularity-v1"\nrecommendationType: "cold_start"}

    REC_API-)KAFKA: async publish ColdStartServedEvent\n{userId: U999, strategy: "popularity"\ntimestamp, pageContext}

    Note over KAFKA,PG: After the user makes 3+ interactions, the system\nautomatically transitions to warm-start then\nto fully personalised recommendations

    loop Each subsequent interaction (3 needed)
        NewUser->>REC_API: POST /v1/events {action: "click"/"purchase"...}
        Note over REC_API: Interaction Collector updates\nfeature vector in Redis
        REC_API->>USER_SVC: PATCH /users/U999/profile\n{increment: interactionCount}
        USER_SVC->>PG: UPDATE users SET interactionCount += 1\nSET coldStartPhase = "warm" WHERE count ≥ 3
    end

    Note over NewUser,REC_API: Next recommendation request:\ncoldStartPhase="warm" — hybrid popularity + embedding
```

### Cold Start Phases

| Phase | Condition | Strategy |
|---|---|---|
| `cold` | < 3 interactions | Popularity-based (trending, new arrivals, editorial picks) |
| `warm` | 3–20 interactions | Hybrid: 70 % popularity + 30 % embedding similarity |
| `active` | > 20 interactions | Fully personalised (NCF / two-tower model) |
| `returning` | > 20 interactions + >7 days inactive | Re-entry hybrid: decayed embedding + recent trends |

---

## SSD-05: Graceful Degradation — Feature Store Unavailable

**Trigger**: The Redis Feature Store cluster experiences a failover during peak traffic.  
**Goal**: Continue serving recommendations (with reduced personalisation quality) rather than returning errors.

```mermaid
sequenceDiagram
    autonumber
    actor Browser as 🌐 User Browser
    participant REC_API as Recommendation API
    participant FEAT_SVC as Feature Store\nService
    participant REDIS as Redis Cluster\n(DEGRADED)
    participant POP_SVC as Popularity Service\n(fallback)
    participant KAFKA as Kafka\n(degradation events)

    Browser->>+REC_API: GET /v1/recommendations?userId=U123

    REC_API->>+FEAT_SVC: GET /features/user/U123 (timeout=10ms)
    FEAT_SVC->>+REDIS: GET feat:user:U123
    REDIS-->>-FEAT_SVC: TIMEOUT (Redis failover in progress)
    FEAT_SVC-->>-REC_API: 503 Feature Store Unavailable

    Note over REC_API: Circuit breaker OPEN\n(>5 failures in 10s window)

    REC_API->>+POP_SVC: GET /popularity/trending?limit=10\n(fallback path — always available)
    POP_SVC-->>-REC_API: [{itemId, trendingScore}×10]\n(served from local in-memory cache)

    REC_API-->>-Browser: 200 OK\n{items[10], recommendationType: "degraded_popularity"\nX-Degraded: true}

    REC_API-)KAFKA: publish DegradedServingEvent\n{userId, reason: "feature_store_timeout"\ntimestamp, fallbackStrategy: "popularity"}

    Note over REC_API,KAFKA: SRE alert fires; circuit breaker\nauto-recovers when Redis is healthy
```

---

## Timing Budget Summary

| Step | Component | Target Latency |
|---|---|---|
| API cache check (Nginx) | Redis | ≤ 2 ms |
| JWT validation | A/B Service | ≤ 5 ms |
| Feature lookup | Redis Feature Store | ≤ 5 ms |
| ANN retrieval | Qdrant | ≤ 15 ms |
| NCF batch scoring | TorchServe GPU | ≤ 20 ms |
| Business rule filtering | In-process | ≤ 3 ms |
| MMR re-ranking (200 items) | In-process | ≤ 5 ms |
| Response serialisation | FastAPI | ≤ 3 ms |
| **Total (cache miss path)** | **End-to-end** | **≤ 58 ms (p50), ≤ 100 ms (p99)** |

---

## Release Gate Checklist

- [ ] All SSD-01 steps load-tested at 1000 req/s sustained with p99 ≤ 100 ms.
- [ ] SSD-02 deduplication tested with burst of 500 duplicate events per second.
- [ ] SSD-03 fairness gate integration-tested with synthetic biased model (DI < 0.8 must block promotion).
- [ ] SSD-04 cold start fallback tested for zero-interaction and partial-interaction users.
- [ ] SSD-05 circuit breaker opens within 10 s of Redis failure and recovers within 30 s of Redis recovery.
- [ ] All Kafka publishes validated as non-blocking (async fire-and-forget pattern).
