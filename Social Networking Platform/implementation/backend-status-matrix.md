# Backend Implementation Status Matrix

This document tracks the implementation progress across all backend services of the Social Networking Platform. Each service is broken down by feature or endpoint, with current status, priority tier, and relevant technical notes. This matrix serves as the authoritative reference for sprint planning, code review prioritization, and stakeholder reporting.

**Status Legend:**

| Symbol | Meaning |
|--------|---------|
| 🔴 Planned | Work not yet started |
| 🟡 In Progress | Actively under development |
| 🟢 Implemented | Code complete, pending tests |
| ✅ Tested | Implementation verified by automated tests |

**Priority Tiers:** P0 = launch blocker, P1 = required pre-GA, P2 = post-launch iteration

---

## User Service

Responsible for identity, authentication, profile management, and social graph operations. Depends on PostgreSQL (primary store), Redis (session/token cache), and Elasticsearch (search index).

| Feature / Endpoint | Status | Priority | Notes |
|--------------------|--------|----------|-------|
| User Registration (`POST /auth/register`) | 🔴 Planned | P0 | Requires email verification flow before account activation |
| User Login (`POST /auth/login`) | 🔴 Planned | P0 | JWT access token + opaque refresh token issuance |
| OAuth Login (Google, Apple, Facebook) | 🔴 Planned | P0 | OAuth2 PKCE flow required; state param CSRF protection |
| Token Refresh (`POST /auth/refresh`) | 🔴 Planned | P0 | Sliding window refresh tokens; rotation on each use |
| Get User Profile (`GET /users/{id}`) | 🔴 Planned | P0 | Public/private visibility rules; blocked user check |
| Update Profile (`PUT /users/{id}`) | 🔴 Planned | P1 | Field validation, avatar upload to S3 pre-signed URL |
| Follow User (`POST /users/{id}/follow`) | 🔴 Planned | P0 | Enters pending state for private accounts awaiting approval |
| Unfollow User (`DELETE /users/{id}/follow`) | 🔴 Planned | P0 | Fan-out deletion from Redis feed cache via Kafka event |
| Block User (`POST /users/{id}/block`) | 🔴 Planned | P1 | Cascades to mutual unfollow and feed entry removal |
| Get Followers / Following Lists | 🔴 Planned | P1 | Cursor-based pagination; keyset pagination on `user_id` |
| User Search (`GET /users/search`) | 🔴 Planned | P1 | Elasticsearch integration; fuzzy + prefix matching |
| Account Deletion (soft delete) | 🔴 Planned | P2 | GDPR right to erasure; 30-day grace period before hard delete |
| Account Suspension / Ban | 🔴 Planned | P1 | Triggered by moderator action; status propagated via Kafka |
| Password Reset Flow | 🔴 Planned | P1 | Short-lived email token; rate limited per email address |
| Email Verification | 🔴 Planned | P0 | Token required before first post; resend endpoint needed |

---

## Post Service

Handles content creation, media processing, reactions, comments, and content moderation pre-publish hooks. Primary store: PostgreSQL. Media store: S3 + CloudFront CDN.

| Feature / Endpoint | Status | Priority | Notes |
|--------------------|--------|----------|-------|
| Create Post (`POST /posts`) | 🔴 Planned | P0 | Visibility rules enforced; content validation pipeline |
| Media Upload (images / video) | 🔴 Planned | P0 | S3 multipart upload; CDN invalidation on publish |
| Video Transcoding | 🔴 Planned | P1 | HLS transcoding via AWS Elemental MediaConvert for adaptive streaming |
| Image Compression / Thumbnails | 🔴 Planned | P1 | WebP conversion; multiple resolutions (thumbnail, medium, full) |
| Get Post (`GET /posts/{id}`) | 🔴 Planned | P0 | Visibility check against requester; block relationship check |
| Edit Post (`PUT /posts/{id}`) | 🔴 Planned | P1 | Content change audit log retained for moderation review |
| Delete Post (`DELETE /posts/{id}`) | 🔴 Planned | P0 | Soft delete; Kafka event triggers feed cache invalidation |
| Like / React to Post | 🔴 Planned | P0 | Atomic counter increment via Redis; Kafka event for fan-out |
| Unlike Post | 🔴 Planned | P0 | Atomic counter decrement; idempotent on double-unlike |
| Add Comment (`POST /posts/{id}/comments`) | 🔴 Planned | P0 | Threaded comments; maximum nesting depth of 3 levels |
| Delete Comment | 🔴 Planned | P1 | Owner or moderator permitted; soft delete with tombstone |
| Share / Repost | 🔴 Planned | P1 | Original post reference preserved; chain repost supported |
| Hashtag Extraction | 🔴 Planned | P1 | Regex parsing on post content; triggers trend computation job |
| Post Visibility Enforcement | 🔴 Planned | P0 | Scopes: public / followers-only / private / group-restricted |
| Content Text Moderation | 🔴 Planned | P1 | Pre-publish ML classifier hook; async re-check post-publish |
| NSFW Image Detection | 🔴 Planned | P1 | Pre-publish image classifier; confidence threshold configurable |

---

## Feed Service

Constructs and serves personalized and chronological feeds. Architecture uses Redis sorted sets for feed storage, Kafka for fan-out events, and a gRPC ML Ranking Service for personalization scoring.

| Feature / Endpoint | Status | Priority | Notes |
|--------------------|--------|----------|-------|
| Personalized Feed (`GET /feed`) | 🔴 Planned | P0 | Redis sorted sets; ML-ranked candidate set via gRPC call |
| Following Feed (`GET /feed/following`) | 🔴 Planned | P0 | Strict chronological order; no ML re-ranking applied |
| Explore / Trending Feed (`GET /feed/explore`) | 🔴 Planned | P1 | Hashtag + engagement velocity score; refreshed every 5 minutes |
| Fan-Out on Write Worker | 🔴 Planned | P0 | Kafka consumer; ZADD post to all follower feed sets |
| Celebrity Fan-Out on Read | 🔴 Planned | P1 | Merge at read time for accounts with >10K followers |
| Feed Cache Management (Redis) | 🔴 Planned | P0 | TTL of 7 days; trim feed sets to 1,000 posts per user |
| Feed Ranking Integration (ML) | 🔴 Planned | P1 | gRPC call to ML Ranking Service; batch score 500 candidates |
| Real-time Feed Updates (WebSocket / SSE) | 🔴 Planned | P2 | Push new post events to connected clients without poll |
| Cold Start Feed (new users) | 🔴 Planned | P1 | Seeded from trending content and onboarding interest selection |
| Feed Invalidation on Block / Unfollow | 🔴 Planned | P1 | Async Kafka consumer removes blocked-user posts from Redis sets |

---

## Messaging Service

Provides direct messaging and group chat. Built on Apache Cassandra for message history and WebSocket connections for real-time delivery. Offline delivery handled via FCM/APNs push.

| Feature / Endpoint | Status | Priority | Notes |
|--------------------|--------|----------|-------|
| Create Conversation (`POST /conversations`) | 🔴 Planned | P0 | Supports DM (2-party) and group chat types |
| List Conversations (`GET /conversations`) | 🔴 Planned | P0 | Returns conversations sorted by last message; includes unread counts |
| Send Message (`POST /conversations/{id}/messages`) | 🔴 Planned | P0 | Supports text, images, and media attachments |
| Get Message History | 🔴 Planned | P0 | Cursor-based pagination; Cassandra partition by `conversation_id` |
| WebSocket Real-time Delivery | 🔴 Planned | P0 | Persistent connection management; heartbeat and reconnect logic |
| Read Receipts | 🔴 Planned | P1 | `last_read_at` update on open; unread count decrement |
| Typing Indicators | 🔴 Planned | P2 | Ephemeral WebSocket events; no persistence required |
| Push Notification on New Message | 🔴 Planned | P0 | Delivered via FCM / APNs when recipient is offline |
| Message Encryption (E2E) | 🔴 Planned | P2 | Signal Protocol implementation; key exchange on conversation init |
| Message Deletion | 🔴 Planned | P1 | Soft delete; replaced with tombstone "This message was deleted" |
| Group Chat Management | 🔴 Planned | P1 | Add / remove participants; admin controls and participant cap |
| Message Search | 🔴 Planned | P2 | Full-text search scoped within a single conversation |

---

## Group Service

Manages community groups with configurable privacy levels, role-based membership, and group-scoped content feeds. Backed by PostgreSQL with Elasticsearch for discovery.

| Feature / Endpoint | Status | Priority | Notes |
|--------------------|--------|----------|-------|
| Create Group (`POST /groups`) | 🔴 Planned | P1 | Privacy levels: public / private / secret |
| Get Group Info (`GET /groups/{id}`) | 🔴 Planned | P1 | Returns member count, description, and `is_member` status |
| Update Group Settings | 🔴 Planned | P1 | Restricted to owner and admin roles only |
| Join Group (`POST /groups/{id}/join`) | 🔴 Planned | P1 | Approval queue flow for private groups; instant join for public |
| Leave Group | 🔴 Planned | P1 | Owner must transfer ownership before leaving |
| Group Feed (`GET /groups/{id}/posts`) | 🔴 Planned | P1 | Posts scoped to group; chronological with optional pinned posts |
| Post to Group | 🔴 Planned | P1 | Group visibility enforcement; moderation pre-publish hook |
| Group Member Management | 🔴 Planned | P1 | Roles: owner / admin / moderator / member; role assignment API |
| Group Discovery (search) | 🔴 Planned | P2 | Elasticsearch index; topic-based and keyword matching |
| Group Invitations | 🔴 Planned | P2 | Invite link generation with configurable expiry and usage cap |

---

## Notification Service

Delivers in-app, push, email, and SMS notifications. Consumes events from Kafka and routes to appropriate delivery channels based on user preferences and online presence.

| Feature / Endpoint | Status | Priority | Notes |
|--------------------|--------|----------|-------|
| In-App Notification Delivery | 🔴 Planned | P0 | Kafka consumer; persists notifications to PostgreSQL |
| Push Notification (FCM / APNs) | 🔴 Planned | P0 | Firebase Cloud Messaging and Apple APNS; device token registry |
| Email Notifications (SendGrid) | 🔴 Planned | P1 | Important events and weekly digest; respects quiet hours |
| SMS Notifications (Twilio) | 🔴 Planned | P2 | Security alerts only (login from new device, password change) |
| Notification Preferences | 🔴 Planned | P1 | Per-notification-type toggle; configurable quiet hours window |
| Notification Aggregation | 🔴 Planned | P1 | Batch similar events: "5 people liked your post" within 1-hour window |
| Unread Count Badge | 🔴 Planned | P0 | Incremented atomically in Redis; pushed via WebSocket event |
| Mark as Read (single / all) | 🔴 Planned | P0 | Updates `read_at` timestamp; decrements Redis unread counter |
| Notification Digest (email) | 🔴 Planned | P2 | Daily and weekly digest; configurable per user preference |

---

## Moderation Service

Enforces platform safety policies through automated ML classifiers and human review workflows. CSAM detection is the highest-criticality feature and must pass third-party audit before launch.

| Feature / Endpoint | Status | Priority | Notes |
|--------------------|--------|----------|-------|
| Submit Report (`POST /reports`) | 🔴 Planned | P0 | Any resource type: post, comment, user, group, message |
| Automated Text Classification | 🔴 Planned | P0 | ML classifier for hate speech, harassment, and spam categories |
| Automated Image Classification (NSFW) | 🔴 Planned | P0 | Vision ML model with confidence threshold gating |
| CSAM Detection (PhotoDNA) | 🔴 Planned | P0 | PhotoDNA API integration — **CRITICAL**: legal and compliance blocker |
| Human Review Queue | 🔴 Planned | P0 | Priority-sorted moderator dashboard feed; SLA tracking per item |
| Take Moderation Action | 🔴 Planned | P0 | Actions: remove content / warn / suspend / ban / shadowban |
| Appeals Process | 🔴 Planned | P1 | User submits appeal within 30 days; senior reviewer assignment |
| Moderation Action Audit Log | 🔴 Planned | P0 | Immutable append-only audit trail; required for regulatory reporting |
| Automated Spam Detection | 🔴 Planned | P1 | Rate-based heuristics combined with ML classifier scoring |
| Shadowban Implementation | 🔴 Planned | P1 | Posts visible only to author and followers; invisible in explore/search |

---

## Search Service

Powered by Elasticsearch. Indexes users, posts, hashtags, and groups. Real-time indexing pipeline consumes create/update/delete events from Kafka.

| Feature / Endpoint | Status | Priority | Notes |
|--------------------|--------|----------|-------|
| User Search (full-text) | 🔴 Planned | P1 | Elasticsearch multi-match; fuzzy matching with edit distance 1 |
| Post Search by Keyword | 🔴 Planned | P1 | Relevance-ranked; applies visibility filters at query time |
| Hashtag Search | 🔴 Planned | P1 | Exact and prefix matching; case-insensitive normalization |
| Trending Hashtags API | 🔴 Planned | P1 | Sliding window count over 1-hour and 24-hour intervals; top 10 |
| Autocomplete Suggestions | 🔴 Planned | P2 | Users, hashtags, and topics; prefix index with edge n-gram tokenizer |
| Search Indexing Pipeline | 🔴 Planned | P1 | Kafka consumer writes to Elasticsearch; at-least-once delivery |
| Search Analytics | 🔴 Planned | P2 | Track zero-result queries and top search terms for product insights |

---

## Analytics Service

Aggregates platform usage and content performance metrics. Powered by a Lambda architecture: real-time stream processing via Kafka Streams and batch aggregation via Apache Spark.

| Feature / Endpoint | Status | Priority | Notes |
|--------------------|--------|----------|-------|
| User Engagement Metrics | 🔴 Planned | P1 | DAU, MAU, session length, retention cohorts |
| Post Performance Metrics | 🔴 Planned | P1 | Impressions, reach, engagement rate, share velocity |
| Feed Quality Metrics | 🔴 Planned | P1 | CTR, dwell time, scroll depth per feed position |
| Platform Health Dashboard | 🔴 Planned | P1 | Error rates, p99 latency per service, throughput |
| Content Moderation Metrics | 🔴 Planned | P1 | Reports per day, classifier accuracy, resolution time SLA |
| Revenue / Ads Metrics | 🔴 Planned | P2 | Ad impressions, click-through rate, CPM by placement |

---

## Story Points and Effort Estimates

Estimates are in story points using a Fibonacci scale (1, 2, 3, 5, 8, 13, 21). One story point ≈ one ideal engineering day for a mid-level backend engineer. Estimates cover implementation only; test authoring is tracked separately.

| Service | Estimated Points (P0) | Estimated Points (P1) | Estimated Points (P2) | Total |
|---------|-----------------------|-----------------------|-----------------------|-------|
| User Service | 34 | 21 | 8 | 63 |
| Post Service | 42 | 34 | 0 | 76 |
| Feed Service | 38 | 29 | 13 | 80 |
| Messaging Service | 55 | 21 | 21 | 97 |
| Group Service | 0 | 42 | 13 | 55 |
| Notification Service | 29 | 21 | 13 | 63 |
| Moderation Service | 55 | 21 | 0 | 76 |
| Search Service | 0 | 42 | 13 | 55 |
| Analytics Service | 0 | 34 | 8 | 42 |
| Infrastructure | 55 | 29 | 0 | 84 |
| **Total** | **308** | **294** | **89** | **691** |

> These estimates assume a team of 8 backend engineers. At average 8 story points per engineer per sprint (2-week sprint), the P0 backlog alone represents approximately 5 sprints at full team capacity.

---

## Service Dependency Map

The following table documents the upstream dependencies each service relies on at runtime. All dependencies must be available and healthy before a service can serve production traffic.

| Service | PostgreSQL | Redis | Kafka | Cassandra | Elasticsearch | S3 | ML Ranking (gRPC) |
|---------|:----------:|:-----:|:-----:|:---------:|:-------------:|:--:|:-----------------:|
| User Service | ✅ Primary | ✅ Session cache | ✅ Events out | — | ✅ User index | ✅ Avatar storage | — |
| Post Service | ✅ Primary | ✅ Counter cache | ✅ Events out | — | ✅ Post index | ✅ Media storage | — |
| Feed Service | — | ✅ Feed sets | ✅ Events in | — | — | — | ✅ Ranking |
| Messaging Service | ✅ Conversation meta | ✅ Presence cache | ✅ Events out | ✅ Message history | — | ✅ Media storage | — |
| Group Service | ✅ Primary | — | ✅ Events out | — | ✅ Group index | — | — |
| Notification Service | ✅ Notification log | ✅ Unread counts | ✅ Events in | — | — | — | — |
| Moderation Service | ✅ Reports / actions | — | ✅ Events in/out | — | — | — | — |
| Search Service | — (read from Kafka) | — | ✅ Events in | — | ✅ All indexes | — | — |
| Analytics Service | — | — | ✅ Events in | — | — | — | — |

---

## Infrastructure and Cross-Cutting Concerns

Platform-wide infrastructure components that span all microservices. All P0 items are prerequisites before any service can be deployed to staging.

| Component | Status | Priority | Notes |
|-----------|--------|----------|-------|
| API Gateway Setup (Kong) | 🔴 Planned | P0 | Rate limiting, auth middleware, request logging plugins |
| JWT Authentication Middleware | 🔴 Planned | P0 | Validates access token on all protected routes; propagates claims |
| Rate Limiter (Redis-based) | 🔴 Planned | P0 | Sliding window algorithm per user ID and per IP address |
| CDN Integration (CloudFront) | 🔴 Planned | P0 | Static assets and media delivery; signed URLs for private content |
| Kafka Topic Configuration | 🔴 Planned | P0 | All event topics defined; replication factor 3; retention 7 days |
| Service Mesh (Istio) | 🔴 Planned | P1 | mTLS between services; observability sidecars; traffic policies |
| Distributed Tracing (Jaeger) | 🔴 Planned | P1 | Trace propagation across all cross-service HTTP and gRPC calls |
| Metrics and Alerting (Prometheus / Grafana) | 🔴 Planned | P1 | Service-level dashboards; PagerDuty alerting on SLO breach |
| Database Migration Framework (Flyway) | 🔴 Planned | P0 | Schema versioning for all PostgreSQL databases |
| CI/CD Pipeline (GitHub Actions) | 🔴 Planned | P0 | Build, test, Docker image push, and Kubernetes rolling deploy |

---

## Test Coverage Status

Target coverage thresholds: **80%** line coverage for unit tests, **60%** scenario coverage for integration tests. E2E tests cover critical user journeys end-to-end across deployed services.

| Service | Unit Tests | Integration Tests | E2E Tests | Coverage Target | Notes |
|---------|------------|-------------------|-----------|-----------------|-------|
| User Service | 🔴 Not Written | 🔴 Not Written | 🔴 Not Written | 80% / 60% | Contract tests with Pact for OAuth provider |
| Post Service | 🔴 Not Written | 🔴 Not Written | 🔴 Not Written | 80% / 60% | Media upload mocked with S3 localstack |
| Feed Service | 🔴 Not Written | 🔴 Not Written | 🔴 Not Written | 80% / 60% | Load tests with k6; fan-out latency assertions |
| Messaging Service | 🔴 Not Written | 🔴 Not Written | 🔴 Not Written | 80% / 60% | WebSocket tests via ws-jest; Cassandra test container |
| Group Service | 🔴 Not Written | 🔴 Not Written | 🔴 Not Written | 80% / 60% | Role permission matrix fully covered in unit tests |
| Notification Service | 🔴 Not Written | 🔴 Not Written | 🔴 Not Written | 80% / 60% | FCM / APNs mocked; Kafka test consumer in integration tests |
| Moderation Service | 🔴 Not Written | 🔴 Not Written | 🔴 Not Written | 80% / 60% | CSAM detection tested with synthetic hash data only — never real content |
| Search Service | 🔴 Not Written | 🔴 Not Written | 🔴 Not Written | 80% / 60% | Elasticsearch test container; index mapping validation tests |
| Analytics Service | 🔴 Not Written | 🔴 Not Written | 🔴 Not Written | 80% / 60% | Kafka Streams topology unit tests with TopologyTestDriver |
| API Gateway | 🔴 Not Written | 🔴 Not Written | 🔴 Not Written | 80% / 60% | Rate limiter behavior tested under simulated burst traffic |

---

## Known Technical Debt

The following items represent known architectural gaps and design shortcuts accepted for the initial development phase. Each item must be resolved before the platform reaches production scale.

- **Counter drift under concurrency:** Like, comment, and share count columns in PostgreSQL can drift under high write concurrency. A periodic reconciliation job reading from the events table is required to correct accumulated skew.
- **User interest vector batch latency:** The ML user interest vector is updated once daily via batch job. This must be migrated to a near-real-time streaming update to improve feed relevance within hours of a new user action.
- **Missing circuit breaker between Feed Service and ML Ranking Service:** No circuit breaker is implemented on the gRPC call to the ML Ranking Service. A cascading failure in the ranking service will degrade feed availability. Resilience4j or Istio retry/circuit-break policies must be applied.
- **WebSocket connection state is in-process:** Current design stores WebSocket session state in-process on the Messaging Service instance. This prevents horizontal scaling. Connection state must be migrated to Redis pub/sub with a shared channel registry.
- **Synchronous image compression in Post Service:** Image compression and thumbnail generation is handled synchronously within the Post Service request handler, adding significant latency to the post creation path. This must be moved to an asynchronous job queue (e.g., SQS + Lambda or a dedicated worker pool).
- **OAuth refresh tokens not revocable:** The current OAuth token design lacks a revocation list. Compromised refresh tokens cannot be invalidated server-side without a full token revocation index backed by Redis or a dedicated token store.
- **Cassandra schema migration tooling undefined:** No migration framework has been selected or configured for Cassandra schema changes in the Messaging Service. Cassandra Reaper or a custom migration runner must be evaluated before the first schema change post-launch.
- **Search index and primary database divergence risk:** The Elasticsearch index is populated asynchronously via Kafka. Extended consumer lag or consumer failure can cause the search index to diverge from the primary PostgreSQL state. A reconciliation backfill job triggered on lag threshold breach is required.
- **Hardcoded celebrity fan-out threshold:** The 10,000-follower threshold that switches fan-out strategy from write-time to read-time is hardcoded in the Fan-Out Worker. This value should be externalized to a configuration service to allow per-deployment tuning without redeployment.
- **Notification digest grouping logic unspecified:** The aggregation window and grouping rules for the notification digest (e.g., "5 people liked your post") have not been formally specified. The current placeholder implementation risks N+1 queries when constructing digest payloads for users with high notification volumes.
- **E2E encryption key management undefined:** The Signal Protocol implementation plan for end-to-end encrypted messages does not yet include a key management strategy — specifically key rotation cadence, key backup, and recovery flows for device loss scenarios.
- **GDPR data portability not scoped:** While account deletion (right to erasure) is scoped, the GDPR right of data portability — allowing users to export all their data as a machine-readable archive — has not been designed or estimated for the current roadmap.

---

## Performance Benchmarks

All targets represent steady-state p99 latency and sustained throughput under expected peak load. Benchmarks are aspirational until baseline measurements are established through load testing with k6 and Locust against a staging environment.

| Service / Endpoint | Target Latency (p99) | Target Throughput | Current Status | Notes |
|--------------------|----------------------|-------------------|----------------|-------|
| Feed API (`GET /feed`) | < 200 ms | 10,000 req/s | 🔴 Baseline not established | Cache-hit path target < 50 ms; cache-miss path < 500 ms |
| Post Creation | < 300 ms | 2,000 req/s | 🔴 Not measured | Excludes async media processing; includes URL validation |
| Fan-Out Worker | < 5 s end-to-end | 50,000 posts/min | 🔴 Not measured | Measured from post create event to last follower feed write |
| Message Delivery (WebSocket) | < 100 ms | 100,000 msg/s | 🔴 Not measured | P99 measured from client send to delivery acknowledgment |
| Search API | < 150 ms | 5,000 req/s | 🔴 Not measured | Elasticsearch query latency; excludes network overhead |
| Notification Delivery | < 1 s push | 500,000 notif/s peak | 🔴 Not measured | APNs / FCM batch delivery; subject to third-party SLA |
| ML Ranking (gRPC) | < 50 ms | 5,000 req/s | 🔴 Not measured | Batch scoring of 500 candidate posts per call |
| Auth / Login API | < 100 ms | 3,000 req/s | 🔴 Not measured | Bcrypt cost factor must be tuned against latency budget |
| Database Read (PostgreSQL) | < 10 ms | 50,000 QPS | 🔴 Not measured | Assumes read replica routing; index coverage required |
| Redis Feed Read | < 5 ms | 100,000 QPS | 🔴 Not measured | Single `ZRANGE` on sorted set; pipeline for multi-key reads |

---

*Last updated: see git log for revision history. All status values must be updated in-place as implementation progresses. Do not create separate status documents — this matrix is the single source of truth.*
