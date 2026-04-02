# C4 Component Diagrams — Knowledge Base Platform

## 1. Level 3 C4 Component — API Server (NestJS)

> **Container**: API Server running on ECS Fargate  
> **Technology**: Node.js 20 + NestJS  
> **Purpose**: Serves all REST API requests from the Next.js frontend, Widget SDK, and third-party integrations.

```mermaid
flowchart TD
    %% External actors
    FE(["Next.js Frontend\n[Web Application]"])
    WSDK(["Widget SDK\n[Browser JavaScript]"])
    EXT(["External Systems\n[Zapier, Zendesk, Slack]"])

    %% Security boundary
    subgraph APIGW["AWS WAF + API Gateway Layer"]
        WAF["WAF Rules\n(rate limit, SQL inject,\nXSS, geo-block)"]
        ALB["Application Load Balancer\n(HTTPS termination, sticky sessions)"]
    end

    %% NestJS API Server boundary
    subgraph API["API Server Container — NestJS on ECS Fargate"]
        direction TB

        subgraph AuthBoundary["Auth & Security Boundary"]
            AUTHC["Auth Component\n[NestJS Module]\nJWT issuance, refresh,\nSAML SSO, email verify\nDeps: UserComponent, Redis"]
            PERMC["Permission Component\n[NestJS Module — Global]\nRBAC evaluation per request,\ncollection-level ACL checks\nDeps: DB (roles, members)"]
        end

        subgraph CoreBoundary["Core Knowledge Base Boundary"]
            ARTC["Article Component\n[NestJS Module]\nCRUD, versioning,\nlifecycle management,\nattachment handling\nDeps: DB, S3, BullMQ"]
            COLC["Collection Component\n[NestJS Module]\nHierarchical taxonomy,\npermission scoping,\nreordering\nDeps: DB"]
            USERC["User Component\n[NestJS Module]\nProfile CRUD, workspace\nmemberships, data export\nDeps: DB, Email"]
            WSC["Workspace Component\n[NestJS Module]\nWorkspace CRUD, member\nmanagement, plan settings\nDeps: DB, Email"]
        end

        subgraph SearchBoundary["Search & Intelligence Boundary"]
            SRCHC["Search Component\n[NestJS Module]\nFull-text + semantic search,\nhybrid ranking, caching\nDeps: Elasticsearch, pgvector, Redis"]
            AIC["AI Component\n[NestJS Module]\nRAG pipeline, conversation\nmanagement, citation extraction\nDeps: OpenAI, pgvector, Redis"]
            EMBC["Embedding Component\n[Shared Service]\nText→vector via OpenAI\ntext-embedding-3-small\nDeps: OpenAI, Redis cache"]
        end

        subgraph DistributionBoundary["Distribution & Integration Boundary"]
            WGTC["Widget Component\n[NestJS Module]\nWidget config, domain auth,\nsuggestion routing, chat proxy\nDeps: SearchComponent, AIComponent"]
            INTC["Integration Component\n[NestJS Module]\nOAuth flows, sync jobs,\nwebhook handling (Zapier, Zendesk)\nDeps: BullMQ, DB, ExternalAdapters"]
            NOTC["Notification Component\n[NestJS Module]\nEmail + Slack transactional\nmessages via BullMQ workers\nDeps: SES, Slack API, BullMQ"]
        end

        subgraph ObservabilityBoundary["Observability & Analytics Boundary"]
            ANAC["Analytics Component\n[NestJS Module]\nEvent tracking, aggregation,\ndeflection reports, top articles\nDeps: DB, BullMQ, Redis counters"]
            QUEC["Queue Component\n[BullMQ Worker Processes]\nEmbedding, publish pipeline,\nnification, analytics batch,\nintegration sync workers\nDeps: Redis, DB"]
        end
    end

    %% Data stores
    subgraph DS["Data Stores"]
        PG[("PostgreSQL 15\nRDS Multi-AZ")]
        RDS[("Redis 7\nElastiCache Cluster")]
        ES[("Amazon OpenSearch\nService")]
        S3B[("AWS S3\n+ CloudFront")]
    end

    subgraph ExtServices["External Services"]
        OPENAI["OpenAI API\n(GPT-4o + embeddings)"]
        SLACK["Slack API"]
        SES["AWS SES\n(email)"]
        ZD["Zendesk API"]
        ZAP["Zapier Webhooks"]
    end

    %% Ingress
    FE --> WAF
    WSDK --> WAF
    EXT --> WAF
    WAF --> ALB
    ALB --> AUTHC

    %% Internal routing (via NestJS guards/interceptors)
    AUTHC --> ARTC
    AUTHC --> COLC
    AUTHC --> USERC
    AUTHC --> WSC
    AUTHC --> SRCHC
    AUTHC --> AIC
    AUTHC --> WGTC
    AUTHC --> INTC
    AUTHC --> ANAC
    PERMC -.->|guards| ARTC
    PERMC -.->|guards| COLC
    PERMC -.->|guards| WGTC

    %% Cross-component dependencies
    ARTC --> EMBC
    ARTC --> QUEC
    ARTC --> NOTC
    ARTC --> ANAC
    SRCHC --> EMBC
    SRCHC --> ES
    AIC --> EMBC
    AIC --> SRCHC
    WGTC --> SRCHC
    WGTC --> AIC
    INTC --> NOTC
    INTC --> QUEC
    QUEC --> EMBC

    %% Data store connections
    ARTC --> PG
    COLC --> PG
    USERC --> PG
    WSC --> PG
    SRCHC --> PG
    SRCHC --> RDS
    AIC --> PG
    AIC --> RDS
    ANAC --> PG
    ANAC --> RDS
    AUTHC --> RDS
    ARTC --> S3B
    QUEC --> RDS

    %% External service connections
    EMBC --> OPENAI
    AIC --> OPENAI
    NOTC --> SES
    NOTC --> SLACK
    INTC --> ZD
    INTC --> ZAP
```

---

## 2. Level 3 C4 Component — Search Service (Internal Decomposition)

> **Component**: Search Component (within API Server container)  
> **Technology**: NestJS SearchModule  
> **Purpose**: Receives search requests and returns ranked results using full-text (Elasticsearch) and semantic (pgvector) search, with Redis caching.

```mermaid
flowchart TD
    subgraph SearchComponent["Search Component — Internal Architecture"]
        direction TB

        QP["Query Parser\nNormalises query string:\n- Strip HTML\n- Detect language (langdetect)\n- Extract quoted phrases\n- Detect filter tokens (tag:, in:)\n- Tokenise for FTS boost"]

        CL["Cache Layer\n(Redis)\n- Key: sha256(wsId+q+filters)\n- TTL: 300 s (full-text)\n- TTL: 600 s (semantic)\n- Invalidation: article publish/update events\n- Stats: hit_rate tracked in Analytics"]

        ESA["Elasticsearch Adapter\n(Amazon OpenSearch)\n- multi_match query (title^3, excerpt^2, body)\n- Highlight extraction\n- Filter: workspace_id, status='published'\n- Pagination: search_after cursor\n- Fuzzy matching on typos"]

        PGVA["pgvector Adapter\n(PostgreSQL 15 + pgvector)\n- ANN cosine similarity search\n- HNSW index (m=16, ef=64)\n- Filter: workspace_id, language, min_score\n- Joins: articles table for metadata\n- Returns top-K nearest neighbours"]

        RR["Result Ranker\nMerges FTS + semantic hits:\n- Reciprocal Rank Fusion (k=60)\n- Score = Σ 1/(k + rank_i)\n- De-duplicate by article_id\n- Apply collection-level access filter\n- Sort by RRF score DESC"]

        AR["Analytics Recorder\n(fire-and-forget)\n- Emit search_query event to BullMQ\n- Track: query_hash, resultCount,\n  searchType, latencyMs, cacheHit\n- Non-blocking: wrapped in setImmediate"]

        EMBC_REF["EmbeddingService\n(reference to shared service)\n- Provides queryEmbedding for\n  semantic search path only"]
    end

    %% Caller
    CALLER(["SearchController\nor WidgetService"])

    %% External
    REDIS_EXT[("Redis\nElastiCache")]
    ES_EXT[("Amazon OpenSearch")]
    PG_EXT[("PostgreSQL\npgvector extension")]
    OPENAI_EXT["OpenAI API\ntext-embedding-3-small"]

    CALLER -->|"SearchQueryDto"| QP
    QP --> CL

    CL -->|"Cache HIT"| CALLER
    CL -->|"Cache MISS"| ESA
    CL -->|"Cache MISS (semantic)"| EMBC_REF

    EMBC_REF -->|"queryEmbedding: Float32[1536]"| PGVA
    EMBC_REF --> OPENAI_EXT

    ESA --> RR
    PGVA --> RR

    RR --> AR
    RR -->|"merged, ranked results"| CL
    CL -->|"cache store + return"| CALLER

    AR -.->|"async"| REDIS_EXT

    ESA --> ES_EXT
    PGVA --> PG_EXT
    CL --> REDIS_EXT
```

### Search Component Security Boundaries

| Boundary | Control | Details |
|----------|---------|---------|
| **Workspace Isolation** | Query-level filter | Every Elasticsearch query and pgvector query includes `workspace_id = $requester.workspaceId`; no cross-workspace data leakage possible |
| **Collection Access Filter** | Post-rank ACL | `ResultRanker` applies collection-level ACL after merging to remove articles from collections the requester lacks `view` permission for |
| **Rate Limiting** | Redis sliding window | 100 req/min per authenticated user; 20 req/min per widget API key (separately tracked) |
| **Query Sanitisation** | QueryParser | HTML stripped, length capped at 512 characters, regex injection patterns rejected with 400 |

---

## 3. Level 3 C4 Component — AI Service (Internal Decomposition)

> **Component**: AI Component (within API Server container)  
> **Technology**: NestJS AIModule + LangChain.js  
> **Purpose**: Implements the full RAG (Retrieval-Augmented Generation) pipeline: embed query → retrieve context → build prompt → call GPT-4o → extract citations → manage conversation.

```mermaid
flowchart TD
    subgraph AIComponent["AI Component — Internal Architecture"]
        direction TB

        QE["Query Embedder\n- Calls EmbeddingService.embed(userQuery)\n- Redis-cached by sha256(query)\n- Embedding TTL: 1 hour\n- Returns Float32[1536]"]

        VR["Vector Retriever\n(pgvector)\n- Cosine similarity: 1-(emb <=> query_emb)\n- Filter: workspace_id, status='published'\n- HNSW index traversal\n- Threshold: min_similarity=0.70\n- Top-K: configurable (default 5)\n- Returns: chunks with title, excerpt,\n  contentText, articleId, similarity"]

        CB["Context Builder\n- Formats system prompt\n- Injects retrieved chunks as\n  numbered context blocks\n- Appends conversation history\n  (sliding window: last 10 turns)\n- Token budget enforcement:\n  ctx≤4096, completion≤1024\n- Truncates history if over budget\n- Detects and rejects prompt injection"]

        LLMC["LLM Client\n(LangChain.js)\n- Model: gpt-4o-2024-08-06\n- Temperature: 0.2 (factual)\n- Max tokens: 1024\n- Streaming: SSE when enabled\n- Retries: 3x with exp back-off\n- Timeout: 30 s\n- Falls back to gpt-4o-mini on error"]

        CE["Citation Extractor\n- Parses LLM response for\n  reference markers [1], [2]…\n- Maps markers to retrieved chunks\n- Validates: each citation must map\n  to a real article in workspace\n- Removes hallucinated citations\n- Builds Citation[] array\n  { articleId, title, slug, snippet }"]

        CONVM["Conversation Manager\n- Persists user + assistant messages\n- Updates conversation status\n  (idle → querying → responding → awaiting_followup)\n- Manages session TTL (Redis)\n- Tracks cumulative token usage\n- Enforces token budget per workspace\n- Returns full message with citations"]

        FBH["Fallback Handler\n- Triggered when:\n  • No chunks above threshold\n  • OpenAI API unavailable\n  • Token budget exceeded\n  • Content policy violation\n- Returns configured fallback message\n- Includes top-3 FTS results as alternatives\n- Logs fallback_reason to analytics"]
    end

    %% Caller
    AICTRL(["AIController\nPOST /ai/conversations/:id/messages"])

    %% External deps
    EMBC_SVC["EmbeddingService\n(shared)"]
    PG_VEC[("PostgreSQL + pgvector")]
    REDIS_C[("Redis\nElastiCache")]
    OPENAI_GPT["OpenAI API\nGPT-4o"]
    CONVREPO[("ConversationRepository\nPostgreSQL")]
    ANA_SVC["AnalyticsService\n(fire-and-forget)"]

    AICTRL -->|"SendMessageDto"| CONVM
    CONVM --> QE
    QE --> EMBC_SVC
    EMBC_SVC --> REDIS_C
    EMBC_SVC -->|"if not cached"| OPENAI_GPT

    QE -->|"queryEmbedding"| VR
    VR --> PG_VEC

    VR -->|"chunks[]"| CB
    VR -->|"no chunks"| FBH
    CB -->|"PromptMessages[]"| LLMC
    LLMC --> OPENAI_GPT
    LLMC -->|"on error"| FBH

    LLMC -->|"LLMResult"| CE
    CE -->|"AiMessage + citations"| CONVM
    FBH -->|"FallbackMessage"| CONVM

    CONVM --> CONVREPO
    CONVM --> REDIS_C
    CONVM -->|"response"| AICTRL
    CONVM --> ANA_SVC
```

### AI Service Security Boundaries

| Boundary | Control | Details |
|----------|---------|---------|
| **Workspace Data Isolation** | VectorRetriever filter | `workspace_id` filter prevents any cross-workspace context retrieval |
| **Prompt Injection Shield** | ContextBuilder | Pattern-based deny-list; malicious instructions replaced with `[filtered]` before sending to OpenAI |
| **Token Budget Enforcement** | ConversationManager | Per-workspace hourly token limit checked from Redis counter before calling LLM; exceeding returns 429 |
| **PII in Responses** | CitationExtractor | Article slugs and titles included in citations; no raw user PII from database is injected into prompts |
| **API Key Rotation** | OpenAI SDK | API key stored in AWS Secrets Manager; rotated quarterly; ECS task definition references secret ARN |
| **Content Policy** | LLM Client | OpenAI moderation endpoint pre-screens user messages; policy violations skip LLM call and return moderation failure message |

---

## 4. Component Technology & Responsibility Summary

| Component | Technology | Responsibility |
|-----------|-----------|----------------|
| Auth Component | NestJS + Passport.js + `jsonwebtoken` + `passport-saml` | JWT lifecycle, SSO, email verification, token blacklisting via Redis |
| Permission Component | NestJS Global Module + TypeORM | RBAC evaluation on every request via `CanActivate` guards; caches role data in Redis for 5 min |
| Article Component | NestJS + TypeORM + BullMQ | Full article CRUD, versioning, lifecycle state machine, S3 attachment management |
| Collection Component | NestJS + TypeORM | Hierarchical collection tree with adjacency-list model; permission scoping |
| Search Component | NestJS + Elasticsearch client + TypeORM (pgvector) + ioredis | Hybrid search orchestration, query parsing, caching, result ranking |
| AI Component | NestJS + LangChain.js + TypeORM + ioredis | Full RAG pipeline, conversation management, citation extraction |
| Embedding Component | NestJS Shared Service + OpenAI SDK | Embedding generation and caching; used by Search and AI components |
| Widget Component | NestJS + ioredis | Widget configuration management, domain validation, suggestion proxy |
| Analytics Component | NestJS + TypeORM + BullMQ | Event tracking ingestion via queue, query-time aggregation for dashboards |
| Integration Component | NestJS + BullMQ + external SDKs | Integration lifecycle, credential encryption (AWS KMS), webhook handling |
| Notification Component | NestJS + BullMQ + `@aws-sdk/client-ses` + `@slack/web-api` | Async email and Slack delivery via dedicated BullMQ worker |
| Queue Component | BullMQ workers on Redis | Embedding, publish pipeline, notifications, analytics batch, integration sync |

---

## 5. Operational Policy Addendum

### 5.1 Content Governance Policies

- **Component Ownership**: Each NestJS module exclusively owns its repositories; no module may directly instantiate or inject a repository owned by another module. Cross-module data needs are served through the owning module's exported service.
- **Attachment Virus Scanning**: `AttachmentService` triggers an async BullMQ job (`scan-attachment`) after S3 upload; the job calls AWS Macie or a ClamAV Lambda to scan the file. Articles cannot be published until all attachments are cleared; infected files are deleted and the author notified.
- **Version Comparison API**: `ArticleVersionService` exposes a diff endpoint (`GET /articles/:id/versions/:v1/diff/:v2`) that returns a JSON Patch diff of TipTap content, enabling authors to review changes before restoring a version.
- **Content Export**: Workspace admins may export all articles as a ZIP of Markdown files (converted from TipTap JSON) via `POST /workspaces/:id/export`; the export job runs asynchronously and delivers a pre-signed S3 URL valid for 1 hour.

### 5.2 Reader Data Privacy Policies

- **Personalised Search**: If a Reader is authenticated, `SearchService` may boost articles from collections the user has previously viewed (stored as `recent_views` in Redis with 30-day TTL). This personalisation is disclosed in the privacy policy and can be opted out via `preferences.personaliseSearch=false`.
- **Widget Analytics Consent**: Before `AnalyticsRecorder` in the Search Component emits events originating from a Widget, it checks the widget's `config.analyticsConsent` flag set by the workspace admin; if `false`, no user-identifying properties are included in the event.
- **Search History Deletion**: Users may delete their search history via `DELETE /users/me/search-history`; this clears hashed query entries from `analytics_events` linked to their `user_id` (anonymised, not physically deleted) and clears `recent_searches` from Redis.
- **Data Residency**: The `ConfigModule` exposes a `DATA_REGION` environment variable; all RDS, ElastiCache, and OpenSearch resources are deployed to the configured region; cross-region data transfer for embeddings (OpenAI API) is governed by the OpenAI DPA.

### 5.3 AI Usage Policies

- **Component-Level Audit**: Every call from `LLMClient` to OpenAI logs `{ model, prompt_tokens, completion_tokens, latency_ms, workspace_id, conversation_id }` to the `ai_messages` table; this enables per-workspace cost attribution and anomaly detection.
- **Embedding Model Versioning**: `EmbeddingService` pins to `text-embedding-3-small` with dimension 1536; changing the model requires a full re-embedding of all `search_indices` rows and a re-index in Elasticsearch. Model upgrades require a maintenance window announcement.
- **Semantic Search Threshold Tuning**: The `min_similarity` threshold (default 0.70) in `VectorRetriever` is configurable per workspace via `settings.ai.minSimilarity`; workspaces with narrow knowledge bases (high-precision domains) are advised to increase to 0.80.
- **LangChain Callback Handlers**: A custom `AuditCallbackHandler` is registered in `LangChainClient`; it logs chain start/end events and tool calls to the structured logger (Winston) with `level=debug` in non-production environments.

### 5.4 System Availability Policies

- **ECS Task Scaling**: The `API Server` ECS service scales horizontally from 2 to 10 tasks based on CPU utilisation (target: 60%) and request count (target: 1,000 req/min per task); scale-in is protected by a 5-minute cooldown to prevent thrashing.
- **Queue Worker Scaling**: BullMQ `embedding-jobs` workers scale independently from 1 to 5 tasks based on queue depth (scale up at depth > 50); workers are deployed in a separate ECS service with a tighter memory profile (512 MB vs. 1 GB for API).
- **Database Connection Management**: TypeORM is configured with `extra.max: 20` per ECS task; at 10 tasks, maximum connections = 200, matching the RDS `max_connections` parameter; RDS Proxy is deployed in front of the primary to multiplex and pool connections.
- **Dependency Health Gate**: On ECS task startup, the NestJS `AppModule` runs a `StartupHealthService` that verifies connectivity to PostgreSQL, Redis, and Elasticsearch before accepting traffic; tasks that fail the health gate are terminated immediately without joining the ALB target group.
