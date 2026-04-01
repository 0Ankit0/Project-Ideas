# Data Flow Diagrams — Social Networking Platform

## 1. Overview

These diagrams trace how data moves through the platform's microservices, message broker,
caches, and storage layers for three high-impact scenarios:

| # | Scenario | Key Concern |
|---|----------|-------------|
| 1 | Feed Data Flow | Latency < 200 ms for feed reads; eventual consistency for fan-out |
| 2 | Content Moderation | Safety SLA: actionable reports triaged within 24 h |
| 3 | Advertising | Impression attribution < 1 s; billing reconciled nightly |

All flows traverse the API Gateway for inbound requests. Internal service-to-service calls use
gRPC over a service mesh (Istio). Asynchronous data movement uses Kafka topics with at-least-once
delivery and idempotent consumers.

---

## 2. Feed Data Flow

### 2.1 Write Path — Post Creation to Feed Delivery

```mermaid
flowchart LR
    subgraph Client["Client Layer"]
        APP["Mobile / Web App"]
    end

    subgraph Gateway["API Gateway"]
        GW["Kong Gateway\n(Auth · Rate Limit · Route)"]
    end

    subgraph PostLayer["Post Pipeline"]
        PostSvc["Post Service\n(Postgres)"]
        MediaSvc["Media Service\n(S3 + Transcoder)"]
        SearchIdx["Search Indexer\n(Elasticsearch)"]
    end

    subgraph Broker["Message Broker"]
        KafkaPost["Kafka\ntopic: post.created"]
    end

    subgraph FeedPipeline["Feed Pipeline"]
        FeedSvc["Feed Service"]
        SGSvc["Social Graph Service\n(Neo4j)"]
        RankML["Ranking ML Worker\n(XGBoost + Embeddings)"]
        FeedCache["Feed Cache\n(Redis Sorted Sets)"]
        FeedDB["Feed DB\n(Cassandra)"]
    end

    subgraph NotifPipeline["Notification Pipeline"]
        NotifSvc["Notification Service"]
        WS["WebSocket Gateway"]
        Push["Push Gateway\n(FCM / APNs)"]
    end

    APP -->|"POST /posts (JWT)"| GW
    GW -->|"Forward"| PostSvc
    PostSvc -->|"Presign upload URL"| MediaSvc
    MediaSvc -->|"Return presignedUrl"| PostSvc
    PostSvc -.->|"201 + uploadUrls"| APP
    APP -->|"PUT binary to S3"| MediaSvc
    PostSvc -->|"Publish post.created"| KafkaPost

    KafkaPost -->|"Consume"| FeedSvc
    KafkaPost -->|"Consume"| SearchIdx
    KafkaPost -->|"Consume"| NotifSvc

    FeedSvc -->|"GET followers list"| SGSvc
    SGSvc -->|"followerIds[ ]"| FeedSvc
    FeedSvc -->|"Score post"| RankML
    RankML -->|"rankScore"| FeedSvc

    FeedSvc -->|"ZADD feed:userId score postId"| FeedCache
    FeedSvc -->|"INSERT feed_items"| FeedDB

    NotifSvc -->|"WS push (mentions)"| WS
    NotifSvc -->|"Silent push"| Push
```

### 2.2 Read Path — Timeline Fetch

```mermaid
flowchart LR
    subgraph Client["Client Layer"]
        APP["Mobile / Web App"]
    end

    subgraph Gateway["API Gateway"]
        GW["Kong Gateway"]
    end

    subgraph FeedRead["Feed Read Path"]
        FeedSvc["Feed Service"]
        FeedCache["Feed Cache\n(Redis — L1)"]
        FeedDB["Feed DB\n(Cassandra — L2)"]
        RankML["Re-rank Worker\n(on cache miss)"]
    end

    subgraph PostHydration["Post Hydration"]
        PostSvc["Post Service"]
        PostCache["Post Cache\n(Redis — metadata)"]
        CDN["CDN\n(CloudFront)"]
    end

    APP -->|"GET /feed?cursor=&limit=20"| GW
    GW -->|"userId + cursor"| FeedSvc

    FeedSvc -->|"ZREVRANGEBYSCORE"| FeedCache
    FeedCache -.->|"Cache HIT: postIds[ ]"| FeedSvc
    FeedCache -.->|"Cache MISS"| FeedSvc
    FeedSvc -->|"On miss: SELECT feed_items"| FeedDB
    FeedDB -->|"postIds[ ]"| FeedSvc
    FeedSvc -->|"On miss: personalise"| RankML
    RankML -->|"ranked postIds[ ]"| FeedSvc

    FeedSvc -->|"POST /posts/batch"| PostSvc
    PostSvc -->|"GET post metadata"| PostCache
    PostCache -.->|"Hit"| PostSvc
    PostSvc -.->|"posts[ ] (hydrated)"| FeedSvc

    FeedSvc -.->|"200 { posts, nextCursor }"| GW
    GW -.->|"Response"| APP
    APP -->|"Lazy-load media"| CDN
```

### 2.3 Explore / Trending Feed

```mermaid
flowchart TD
    subgraph Inputs["Signal Inputs"]
        ReactionEvents["Reaction Events\n(Kafka: reaction.added)"]
        ShareEvents["Share Events\n(Kafka: post.shared)"]
        SearchEvents["Search Events\n(Kafka: search.query)"]
    end

    subgraph TrendEngine["Trending Engine"]
        TrendWorker["Trend Aggregator\n(Flink streaming job)"]
        TrendStore["Trending Store\n(Redis Sorted Set\nwindow: 1h / 24h / 7d)"]
        TrendDB["Trend History\n(ClickHouse — analytics)"]
    end

    subgraph ExploreService["Explore Feed Builder"]
        ExploreSvc["Explore Service"]
        PersonalisationML["Personalisation ML\n(collaborative filtering)"]
        SafetyFilter["Safety Filter\n(content policy rules)"]
    end

    subgraph Delivery["Delivery"]
        FeedSvc["Feed Service"]
        APP["Client App"]
    end

    ReactionEvents -->|"Stream"| TrendWorker
    ShareEvents -->|"Stream"| TrendWorker
    SearchEvents -->|"Stream"| TrendWorker

    TrendWorker -->|"Increment score"| TrendStore
    TrendWorker -->|"Persist"| TrendDB

    APP -->|"GET /feed/explore"| FeedSvc
    FeedSvc -->|"GET /trending?window=1h"| ExploreSvc
    ExploreSvc -->|"ZREVRANGE trending:global 0 199"| TrendStore
    TrendStore -->|"Top 200 postIds"| ExploreSvc
    ExploreSvc -->|"Personalise for userId"| PersonalisationML
    PersonalisationML -->|"Ranked subset"| ExploreSvc
    ExploreSvc -->|"Apply content policy"| SafetyFilter
    SafetyFilter -->|"Filtered postIds"| ExploreSvc
    ExploreSvc -->|"Ranked, safe list"| FeedSvc
    FeedSvc -->|"Hydrate + return"| APP
```

---

## 3. Content Moderation Data Flow

### 3.1 User-Submitted Report Flow

```mermaid
flowchart TD
    subgraph Submission["Report Submission"]
        USER["Reporting User"]
        GW["API Gateway"]
        ModSvc["Moderation Service\n(Postgres: reports)"]
    end

    subgraph AutoScreen["Automated Screening"]
        MLClassifier["ML Classifier\n(toxicity / CSAM / spam)"]
        HashMatch["Hash Matching\n(PhotoDNA / MD5 blocklist)"]
        KafkaMod["Kafka\ntopic: report.submitted"]
    end

    subgraph Queue["Moderation Queue"]
        ModQueue["Moderation Queue Service\n(priority queue — Redis)"]
        ModDB["Queue DB\n(Postgres: moderation_queue)"]
    end

    subgraph HumanReview["Human Review"]
        ModDashboard["Moderator Dashboard\n(Internal Tool)"]
        ModAction["Action Worker\n(take-down / warn / ban)"]
    end

    subgraph Outcomes["Outcome Propagation"]
        KafkaAction["Kafka\ntopic: moderation.actioned"]
        PostSvc["Post Service\n(soft-delete content)"]
        UserSvc["User Service\n(issue warning / ban)"]
        FeedSvc["Feed Service\n(remove from feeds)"]
        SearchSvc["Search Service\n(de-index content)"]
        NotifSvc["Notification Service\n(notify reporter + target)"]
    end

    USER -->|"POST /reports"| GW
    GW -->|"Validate + forward"| ModSvc
    ModSvc -->|"INSERT report (status=PENDING)"| ModSvc
    ModSvc -->|"Publish report.submitted"| KafkaMod

    KafkaMod -->|"Consume"| MLClassifier
    KafkaMod -->|"Consume"| HashMatch

    MLClassifier -->|"HIGH severity → auto-escalate"| ModQueue
    HashMatch -->|"CSAM match → immediate take-down"| ModAction
    MLClassifier -->|"LOW severity → queue"| ModQueue

    ModQueue -->|"INSERT into moderation_queue\n(priority: HIGH/MED/LOW)"| ModDB
    ModQueue -->|"Route to reviewer pool"| ModDashboard

    ModDashboard -->|"Moderator selects & reviews"| ModAction
    ModAction -->|"Record action + notes"| ModDB
    ModAction -->|"Publish moderation.actioned"| KafkaAction

    KafkaAction -->|"Consume"| PostSvc
    KafkaAction -->|"Consume"| UserSvc
    KafkaAction -->|"Consume"| FeedSvc
    KafkaAction -->|"Consume"| SearchSvc
    KafkaAction -->|"Consume"| NotifSvc
```

### 3.2 Proactive Automated Scanning

```mermaid
flowchart LR
    subgraph Upload["Upload Events"]
        MediaUploaded["Media Uploaded\n(Kafka: media.uploaded)"]
        PostCreated["Post Created\n(Kafka: post.created)"]
    end

    subgraph Scanner["Content Scanner"]
        TextScanner["Text Scanner\n(Perspective API + custom model)"]
        ImageScanner["Image Scanner\n(Vision API — nudity/violence)"]
        VideoScanner["Video Scanner\n(frame-sampled, async)"]
    end

    subgraph Decision["Decision Engine"]
        AutoAction["Auto-Action Engine"]
        ConfigStore["Policy Config Store\n(Redis — thresholds)"]
    end

    subgraph Outcomes["Outcomes"]
        AutoRemove["Auto Remove\n(score > 0.95)"]
        FlagForReview["Flag for Human Review\n(score 0.7–0.95)"]
        Allow["Allow\n(score < 0.7)"]
    end

    PostCreated -->|"text content"| TextScanner
    MediaUploaded -->|"image"| ImageScanner
    MediaUploaded -->|"video"| VideoScanner

    TextScanner -->|"toxicity score"| AutoAction
    ImageScanner -->|"policy score"| AutoAction
    VideoScanner -->|"policy score"| AutoAction
    ConfigStore -->|"thresholds"| AutoAction

    AutoAction -->|"score > 0.95"| AutoRemove
    AutoAction -->|"0.7 ≤ score ≤ 0.95"| FlagForReview
    AutoAction -->|"score < 0.7"| Allow
```

---

## 4. Advertising Data Flow

### 4.1 Ad Serving — Request-Time Flow

```mermaid
flowchart LR
    subgraph Client["Client Layer"]
        APP["Mobile / Web App"]
    end

    subgraph Gateway["API Gateway"]
        GW["Kong Gateway"]
    end

    subgraph AdDecision["Ad Decision Engine"]
        AdSvc["Ad Service"]
        AuctionEngine["Auction Engine\n(eCPM second-price)"]
        TargetingEngine["Targeting Engine\n(segments + context)"]
        FreqCap["Frequency Cap\n(Redis: impressions per user)"]
        AdCache["Ad Creative Cache\n(Redis — 5 min TTL)"]
    end

    subgraph CampaignData["Campaign Data"]
        AdDB["Ad DB\n(Postgres: campaigns/creatives)"]
        SegmentStore["User Segment Store\n(Redis Bitmaps)"]
    end

    subgraph Tracking["Impression Tracking"]
        ImpressionKafka["Kafka\ntopic: ad.impression"]
        AnalyticsSvc["Analytics Service\n(ClickHouse)"]
        BillingSvc["Billing Service\n(Postgres: spend ledger)"]
    end

    subgraph CDN["Media Delivery"]
        CDN["CDN (CloudFront)\nAd Creative Assets"]
    end

    APP -->|"GET /feed (slot: in-feed-ad)"| GW
    GW -->|"Forward + userId"| AdSvc

    AdSvc -->|"Check daily cap"| FreqCap
    FreqCap -->|"Cap not reached"| AdSvc

    AdSvc -->|"GET eligible segments"| SegmentStore
    SegmentStore -->|"segmentIds[ ]"| AdSvc

    AdSvc -->|"GET creatives by segments"| AdCache
    AdCache -.->|"Cache miss"| AdDB
    AdDB -->|"eligible campaigns + bids"| AdSvc
    AdSvc -->|"Run auction"| AuctionEngine
    AuctionEngine -->|"Winning creative + clearing price"| AdSvc

    AdSvc -->|"Render ad slot"| GW
    GW -->|"Include ad in feed response"| APP
    APP -->|"Fetch media asset"| CDN

    APP -->|"Impression beacon (async)"| AdSvc
    AdSvc -->|"Increment freq cap"| FreqCap
    AdSvc -->|"Publish ad.impression"| ImpressionKafka

    ImpressionKafka -->|"Consume"| AnalyticsSvc
    ImpressionKafka -->|"Consume"| BillingSvc
```

### 4.2 Ad Performance Reporting Data Flow

```mermaid
flowchart TD
    subgraph RawEvents["Raw Event Streams"]
        ImpressionTopic["Kafka: ad.impression"]
        ClickTopic["Kafka: ad.click"]
        ConversionTopic["Kafka: ad.conversion"]
    end

    subgraph StreamProcessing["Stream Processing"]
        FlinkJob["Flink Aggregation Job\n(window: 5 min)"]
    end

    subgraph Storage["Analytics Storage"]
        ClickHouse["ClickHouse\n(ad_impressions, ad_clicks tables)"]
        ReportCache["Report Cache\n(Redis — hourly rollups)"]
    end

    subgraph Reporting["Reporting Layer"]
        AnalyticsSvc["Analytics Service"]
        AdvertiserPortal["Advertiser Portal\n(Dashboard UI)"]
        BillingJob["Nightly Billing Job\n(reconcile spend vs ledger)"]
    end

    ImpressionTopic -->|"Stream"| FlinkJob
    ClickTopic -->|"Stream"| FlinkJob
    ConversionTopic -->|"Stream"| FlinkJob

    FlinkJob -->|"INSERT aggregated rows"| ClickHouse
    FlinkJob -->|"UPDATE rolling counters"| ReportCache

    AdvertiserPortal -->|"GET /analytics/campaigns/:id"| AnalyticsSvc
    AnalyticsSvc -->|"Query impressions, clicks, CTR, CPC"| ClickHouse
    ClickHouse -->|"Aggregated metrics"| AnalyticsSvc
    AnalyticsSvc -->|"Cache result"| ReportCache
    AnalyticsSvc -->|"Return metrics"| AdvertiserPortal

    BillingJob -->|"Nightly: SELECT spend by campaign"| ClickHouse
    BillingJob -->|"Reconcile with ledger"| BillingJob
    BillingJob -->|"Charge advertiser / send invoice"| BillingJob
```
