# Search and Retrieval — Edge Cases

## Introduction

The search and retrieval subsystem is the primary discovery mechanism for the Knowledge Base Platform. It orchestrates three complementary layers: Amazon OpenSearch Service (Elasticsearch 8-compatible) for full-text search, pgvector (PostgreSQL 15 extension) for semantic similarity search using OpenAI `text-embedding-3-small` embeddings, and Redis 7 (ElastiCache) for caching popular query results. The subsystem is also the highest-traffic component of the platform, processing tens of thousands of queries per day.

Failures in search are immediately visible to users — a missing article, a stale result, or an irrelevant AI-ranked document erodes confidence faster than almost any other failure type. The eight edge cases below cover the most significant failure modes: index consistency, vector dimension compatibility, cache contention, denial-of-service vectors, semantic ranking errors, tenant data isolation, shard-level partial failures, and query injection.

---

## EC-SEARCH-001: Elasticsearch Index Out of Sync

### Failure Mode
An author publishes an article. The NestJS `ArticleService.publish()` method writes the article to PostgreSQL, then enqueues an `IndexArticleJob` in BullMQ. If the BullMQ worker is down, overwhelmed, or the OpenSearch write fails silently, the article is persisted in the database but is never indexed in OpenSearch. Users searching for the article's title or content receive zero results. The article is accessible only via its direct URL. The inconsistency may persist for hours or days without automatic detection.

### Impact
**Severity: High**
- Newly published articles are invisible to all users relying on search.
- Support teams directing users to search for documentation find it unreachable.
- For time-sensitive content (incident runbooks, product announcements), the delay in discovery is operationally damaging.
- Authors believe their publish action succeeded but the content is effectively inaccessible.

### Detection
- **Publish-to-Index Lag Metric**: After every `IndexArticleJob` completes, record the delta between `articles.published_at` and the OpenSearch index timestamp. Alert if P99 lag exceeds 60 seconds.
- **Index Count Reconciliation**: Run a cron job every 5 minutes: `SELECT COUNT(*) FROM articles WHERE status = 'published'` vs OpenSearch document count. Alert if delta exceeds 10.
- **BullMQ Queue Depth**: CloudWatch alarm on `bullmq.index_article.waiting` depth > 100.
- **Dead Letter Queue**: Failed `IndexArticleJob` messages moved to the DLQ trigger a PagerDuty alert.
- **Health Endpoint**: `GET /api/health/search-sync` returns the current replication lag.

### Mitigation/Recovery
1. Identify all published articles missing from OpenSearch using the reconciliation query.
2. For each missing article, enqueue a new `IndexArticleJob` directly via the BullMQ admin UI or a CLI script: `npm run jobs:reindex -- --articleId=<id>`.
3. If the BullMQ worker is down, restart the ECS task running the worker service and monitor for job consumption.
4. If OpenSearch is rejecting writes (e.g., due to mapping conflict — see EC-OPS-004), resolve the mapping issue before re-enqueueing.
5. Communicate to users via the platform status page that search results for recently published articles may be temporarily delayed.

### Prevention
- Implement a dual-write consistency check: after the `IndexArticleJob` completes, query OpenSearch to confirm the document is retrievable. If not, retry up to 3 times with exponential backoff before alerting.
- Add a nightly full reconciliation job (`ReconcileSearchIndexJob`) that compares all published article IDs in PostgreSQL against the OpenSearch index and re-indexes any missing documents.
- Use BullMQ's built-in retry with backoff for `IndexArticleJob`: 3 retries with 30-second delays before sending to DLQ.
- Tag OpenSearch write failures with the article ID in Sentry for easy backfill targeting.

---

## EC-SEARCH-002: Vector Embedding Dimension Mismatch

### Failure Mode
The platform uses OpenAI `text-embedding-3-small` which produces 1536-dimensional vectors stored in PostgreSQL's `pgvector` extension as `VECTOR(1536)` columns. OpenAI announces a successor embedding model (e.g., `text-embedding-4-small`) that produces 3072-dimensional vectors. An engineer updates the embedding model configuration without migrating the existing vectors. New articles are embedded with 3072 dimensions while old articles retain 1536-dimensional vectors. The pgvector cosine similarity search fails with a `dimension mismatch` PostgreSQL error for any query that encounters old and new vectors in the same scan.

### Impact
**Severity: Critical**
- Semantic search and AI Q&A are completely non-functional for any workspace with mixed-dimension vectors.
- The failure is widespread, affecting all users simultaneously.
- Reverting the model change requires re-embedding all new articles with the old model or re-embedding all old articles with the new model — both are expensive and time-consuming.
- OpenAI API costs spike during the re-embedding operation.

### Detection
- **PostgreSQL Error Logs**: `ERROR: different vector dimensions X and Y` in RDS logs. CloudWatch Logs Insights alert on this pattern.
- **pgvector Query Error Rate**: Track `search.vector_query_errors` metric. Alert if rate exceeds 1% of semantic search queries.
- **Embedding Model Config Drift**: The deployment pipeline must compare the configured `EMBEDDING_MODEL` environment variable against the model recorded in the `article_embeddings` table's `model_version` column. Alert if they diverge.
- **Sentry Error**: `VectorDimensionMismatchError` captured on every failed semantic search request.

### Mitigation/Recovery
1. Immediately revert the `EMBEDDING_MODEL` configuration to the previous model and redeploy. This prevents new mismatched vectors from being created.
2. Identify all articles with the new-dimension vectors using: `SELECT article_id FROM article_embeddings WHERE model_version = '<new-model>' `.
3. Re-embed those articles using the old model via a rate-limited BullMQ job `ReembedJob` to restore consistency.
4. Once the re-embedding is complete and verified, plan a proper migration window for upgrading all vectors to the new model.
5. During the re-embedding period, fall back to full-text OpenSearch search for semantic queries and display a banner: "Semantic search is temporarily using keyword mode."

### Prevention
- Store the embedding model name and dimension in every `article_embeddings` record: `model_version VARCHAR, vector_dimensions INT`.
- Before any embedding model change, run a migration that adds a new `embedding_v2 VECTOR(<new_dim>)` column rather than replacing the existing column. Use dual-column search during the transition period.
- Gate model changes behind a feature flag that requires a complete migration job to finish before activating the new model for search queries.
- Add a pre-deployment check in the CI/CD pipeline that verifies the configured embedding model's output dimension matches the pgvector column definition.

---

## EC-SEARCH-003: Search Cache Stampede

### Failure Mode
A popular search query (e.g., "getting started guide") is cached in Redis with a 5-minute TTL. When the TTL expires, 200 simultaneous users have that query in flight. All 200 requests find the cache empty and simultaneously query OpenSearch. OpenSearch receives 200 identical queries within 100ms, overwhelming the cluster's query threads, causing latency to spike from 50ms to 5+ seconds for all search traffic — not just this query.

### Impact
**Severity: High**
- All search traffic experiences high latency during the stampede window (typically 2–10 seconds).
- OpenSearch circuit breakers may trip, causing all searches to fail with `503 Service Unavailable` until pressure subsides.
- A single popular query effectively creates a self-induced DDoS on the search cluster.
- User experience degrades noticeably; page timeout errors appear in the frontend.

### Detection
- **OpenSearch Query Latency**: CloudWatch `SearchLatency` P99 > 2 seconds triggers a High alert.
- **Simultaneous Query Count**: Track `search.concurrent_queries_for_same_term` metric. Alert if more than 10 concurrent queries for the same normalized term.
- **Cache Hit Rate Drop**: Redis `cache_hit_rate` dropping below 70% for `search:*` keys is a leading indicator.
- **OpenSearch Thread Pool Rejection**: `opensearch.thread_pool.search.rejected` counter spike.

### Mitigation/Recovery
1. Enable Redis probabilistic early expiration (PER): refresh the cache entry when a query finds the TTL below a threshold (e.g., 30 seconds remaining) with a configurable probability, rather than waiting for TTL=0.
2. Implement a single-flight / request coalescing pattern in the NestJS `SearchService`: use a Redis-based distributed lock (`SET nx px`) so that only one of the 200 concurrent requests actually queries OpenSearch. The other 199 wait on the lock, then read the freshly populated cache entry.
3. During active stampede: temporarily raise the search cache TTL to 15 minutes to allow the cluster to recover.
4. If OpenSearch thread pool rejection has occurred, reduce incoming search traffic by rate-limiting the search API endpoint to 10 requests/second per workspace.

### Prevention
- Implement cache warming: when an article is published or the top-10 most popular queries are identified, proactively re-cache their results before TTL expiry.
- Use staggered TTLs: add random jitter (±60 seconds) to cache TTLs to prevent multiple popular queries from expiring simultaneously.
- Implement the single-flight pattern as the default in `SearchService`, not as a recovery measure.
- Set OpenSearch circuit breaker thresholds and test them in staging to understand the cluster's actual query capacity.

---

## EC-SEARCH-004: Zero-Result Query Flood

### Failure Mode
A bot, a misconfigured integration, or a malicious actor sends thousands of nonsense or highly specific queries (e.g., random UUIDs, gibberish strings) to the search API in a short time window. Each query returns zero results and is recorded in the `search_analytics` PostgreSQL table. Within minutes, the `search_analytics` table grows by hundreds of thousands of rows, consuming PostgreSQL write capacity (IOPS), bloating the table, and slowing down legitimate analytics aggregation queries. If the analytics table has no size cap, it can fill available storage.

### Impact
**Severity: Medium**
- RDS write IOPS spike, degrading write performance for the articles and users tables.
- `search_analytics` table bloat increases vacuum time and autovacuum locking.
- Analytics dashboards become slow or unresponsive as queries against the bloated table time out.
- If storage fills, RDS enters read-only mode, causing a Critical outage.

### Detection
- **Rate Limit Alert**: CloudWatch metric `api.search.requests_per_minute` > 1000 for a single IP/workspace triggers a High alert.
- **Zero-Result Rate**: Track `search.zero_result_rate` over a rolling 5-minute window. Alert if it exceeds 30% (indicates query flood or index problem).
- **RDS Storage Growth**: CloudWatch `FreeStorageSpace` declining faster than 1GB/hour.
- **Write IOPS Saturation**: `WriteIOPS` approaching the provisioned IOPS limit.

### Mitigation/Recovery
1. Apply IP-level and workspace-level rate limiting at the AWS WAF layer: block IPs exceeding 200 search requests per minute.
2. Add application-level rate limiting in NestJS: 60 search requests per minute per authenticated user, 10 per minute for unauthenticated (public KB search).
3. Stop writing analytics records for zero-result queries from IP addresses flagged as bots (based on WAF bot detection).
4. If the `search_analytics` table is bloated: partition it by day and drop old partitions. Run `VACUUM ANALYZE search_analytics` immediately.
5. Purge search_analytics records older than 90 days to reclaim storage.

### Prevention
- Implement table partitioning for `search_analytics` from the start, partitioned by day with automatic old-partition dropping after 90 days.
- Write zero-result queries to a separate `search_zero_results` table with a lower retention period (7 days) and separate storage quota monitoring.
- Deploy AWS WAF managed rule set for bot detection on the API Gateway.
- Implement a query normalizer that collapses clearly nonsensical queries (pure UUID, >200 character queries, non-UTF-8) before they reach the analytics write path.

---

## EC-SEARCH-005: Semantic Search Hallucination Risk

### Failure Mode
The platform's AI-powered search uses pgvector to find articles whose embeddings are semantically similar to the user's query embedding. When a user searches for "how to configure SSO with Okta," pgvector returns the top-5 articles ranked by cosine similarity. However, if the knowledge base contains no article directly about Okta SSO configuration, pgvector returns loosely related articles (e.g., "General Authentication Overview," "Password Reset Guide") with similarity scores of 0.65–0.75 — which the platform's UI presents as "Top Results" with a high-confidence ranking. The user believes these are authoritative answers, makes configuration decisions based on them, and encounters problems.

### Impact
**Severity: High**
- Users act on misleading search results, especially for technical or procedural queries.
- For customer-facing knowledge bases, this can lead to incorrect product usage, support escalations, and trust damage.
- The AI Q&A feature (if built on top of these results) may compound the issue by generating a confident answer based on irrelevant source material.

### Detection
- **Low Similarity Score Distribution**: Track the distribution of cosine similarity scores for returned results. Alert if P50 similarity score for returned results falls below 0.70.
- **User Engagement Signal**: Track "click-through rate" on search results. A very low CTR (< 20%) for top results indicates poor relevance.
- **User Feedback**: Surface a "Was this helpful?" prompt on search results. Track negative feedback rate.
- **A/B Test**: Compare semantic search precision against full-text OpenSearch results for the same queries.

### Mitigation/Recovery
1. Implement a similarity score threshold: do not return any pgvector result with cosine similarity < 0.75. If all results fall below the threshold, display a "No closely matching articles found" message rather than displaying low-confidence results.
2. Add a "confidence indicator" to search results: articles above 0.90 similarity show "Best Match," 0.75–0.90 show "Related," and < 0.75 are suppressed.
3. Fall back to OpenSearch full-text results when pgvector returns fewer than 3 results above the threshold.
4. Display a clear disclaimer on AI Q&A answers when the source article similarity is below 0.80: "This answer is based on loosely related content and may not be fully accurate."

### Prevention
- Regularly evaluate retrieval precision using a golden test set of query-article pairs. Run this evaluation in the CI pipeline after any change to the embedding model or retrieval parameters.
- Use Reciprocal Rank Fusion (RRF) to combine pgvector semantic results with OpenSearch full-text results, improving overall relevance by cross-validating both systems.
- Implement query expansion: before embedding the user's query, use GPT-4o to generate 2–3 alternative phrasings, embed all of them, and take the union of top results to improve recall.
- Monitor the article coverage gap: if a query returns low-similarity results and is searched frequently, surface it to the knowledge base admins as a content gap to fill.

---

## EC-SEARCH-006: Cross-Workspace Data Leak in Search

### Failure Mode
The NestJS `SearchService` constructs an OpenSearch query with a `workspace_id` filter to ensure results are scoped to the requesting user's workspace. A developer adds a new search feature (e.g., federated search across shared public articles) and accidentally introduces a code path where the `workspace_id` filter is omitted for certain query types. When a user in Workspace A searches for a term that matches an article in Workspace B, they receive Workspace B's article in their results — including the article title, excerpt, and metadata — even though they have no access to Workspace B.

### Impact
**Severity: Critical**
- This is a data breach: confidential proprietary information from one tenant is exposed to another.
- Even article titles and excerpts can contain sensitive competitive or operational information.
- Under GDPR and enterprise SLAs, this triggers mandatory breach notification obligations.
- Regulatory fines, enterprise contract violations, and severe reputational damage follow.

### Detection
- **Automated Cross-Workspace Query Test**: A synthetic monitoring test runs every 5 minutes, executing a search from Workspace A for a known-unique term from a canary article in Workspace B. Any result returned from Workspace B triggers a Critical alert.
- **Search Result Workspace Audit**: Log the `workspace_id` of every search result returned. If a result's `workspace_id` differs from the requesting user's `workspace_id`, emit a `CROSS_WORKSPACE_RESULT_DETECTED` critical alert immediately.
- **Code Review Gate**: Any change to `SearchService` or the OpenSearch query builder requires a second reviewer who specifically checks workspace filter completeness.

### Mitigation/Recovery
1. **Immediate**: Disable the affected search feature or code path and deploy a hotfix. If the scope is unclear, temporarily disable all search and display a maintenance message while investigating.
2. Identify all users who received cross-workspace results using the search result audit logs (retain for 90 days).
3. Notify all affected workspaces of the incident within 72 hours as required by GDPR Article 33.
4. Rotate all API tokens and JWT secrets as a precaution if there is any indication the leak was exploited intentionally.
5. File a legal/compliance report and engage the Data Protection Officer.

### Prevention
- Implement workspace isolation at the OpenSearch index level: each workspace has its own OpenSearch index. Cross-index queries are architecturally impossible.
- As a secondary safeguard, add a mandatory `workspace_id` parameter to the `SearchService.search()` method signature (not optional). Any call without it fails at compile time.
- Write an automated test for every search code path that asserts: given a query from Workspace A, no results with `workspace_id = B` are returned, for all known search modes.
- Enforce a database-level row security policy (PostgreSQL RLS) on the `articles` table as a defense-in-depth measure.

---

## EC-SEARCH-007: Elasticsearch Shard Failure

### Failure Mode
The OpenSearch cluster is configured with 3 primary shards and 1 replica per shard. A network partition or disk failure causes one primary shard (shard 1 of 3) to become unavailable. OpenSearch marks the shard as `UNASSIGNED` and promotes the replica. During the replica promotion window (typically 30–60 seconds), queries that would be routed to shard 1 receive partial results or time out. After promotion, documents stored in the unavailable primary that were written after the last replica sync may be missing from results.

### Impact
**Severity: High**
- Approximately 33% of articles are temporarily missing from search results (those stored in shard 1).
- The OpenSearch cluster status turns `YELLOW`, but the API continues to return HTTP 200 with partial results and no error indicator in the response body.
- Users see inconsistent results: the same query returns different result sets on successive calls.
- Data written to the failed shard between the last replica sync and the failure is permanently lost.

### Detection
- **Cluster Health API**: Poll `GET /_cluster/health` every 60 seconds. Alert on `status: yellow` or `status: red`.
- **Unassigned Shards Metric**: CloudWatch `KibanaHealthyNodes` metric drop; `ShardsUnassigned` > 0 triggers High alert.
- **Result Count Anomaly**: Track the rolling average result count for the top-10 queries. A sudden drop of > 25% in result count for a stable query is a shard failure signal.
- **Amazon OpenSearch Service Events**: Subscribe to `OpenSearch-OperationalAlerts` SNS topic for shard failure events.

### Mitigation/Recovery
1. Immediately navigate to the OpenSearch Service console and confirm the shard assignment status.
2. If the replica is healthy, OpenSearch will auto-promote it. Monitor until cluster status returns to `GREEN`.
3. If the replica is also unavailable (double failure), initiate a cluster snapshot restore from the most recent daily S3 snapshot.
4. Once the cluster is `GREEN`, run the reconciliation job to identify and re-index any documents missing due to the shard gap.
5. Communicate the partial search degradation to users via the status page.

### Prevention
- Configure 2 replicas per shard (not 1) for the production OpenSearch cluster. This tolerates 2 simultaneous node failures.
- Enable OpenSearch's `index.unassigned.node_left.delayed_timeout` to 5 minutes to prevent unnecessary shard rebalancing on transient node failures.
- Take daily OpenSearch index snapshots to S3 using the OpenSearch snapshot API.
- Enable Enhanced VPC Routing to reduce the risk of network partitions causing shard failures.
- Test shard failure recovery quarterly in a staging environment.

---

## EC-SEARCH-008: Query Injection Attack

### Failure Mode
The public-facing search API accepts a `query` string parameter from unauthenticated users. A malicious actor submits an Elasticsearch DSL payload as the query string: `{"query": {"match_all": {}}, "size": 10000}`. If the NestJS `SearchService` constructs the OpenSearch query by interpolating the user's input directly into a query template (using string concatenation rather than parameterized queries), the injected DSL overrides the workspace filter and returns all articles across all workspaces, up to 10,000 results.

### Impact
**Severity: Critical**
- Bulk extraction of all article content from the OpenSearch index, bypassing all access controls.
- Confidential content from all workspaces is exposed to the attacker.
- The attack is stealthy: it looks like a normal search request in access logs.
- Constitutes a data breach affecting all tenants on the platform.

### Detection
- **Query Structure Anomaly**: Detect search query strings containing `{`, `}`, `query`, `match_all`, or other OpenSearch DSL keywords. Log as `QUERY_INJECTION_ATTEMPT` and alert.
- **Response Size Anomaly**: If a search response contains more than 50 results (normal max is 20), emit a `LARGE_SEARCH_RESPONSE` alert.
- **WAF Managed Rules**: AWS WAF should inspect the `query` parameter for JSON structure patterns and block requests where the query value is valid JSON rather than a plain text string.
- **Sentry Error Tracking**: Monitor for `OpenSearchQueryError` exceptions that reference user-supplied DSL fragments.

### Mitigation/Recovery
1. Immediately deploy a WAF rule blocking search requests where the `q` parameter contains JSON syntax characters (`{`, `}`, `[`, `]`).
2. In the NestJS `SearchService`, wrap the user input in an OpenSearch `match` query object server-side — never interpolate it directly. The user input must always be treated as a plain string, never as a DSL structure.
3. Review access logs for the past 30 days for anomalous search result volumes per IP/user to determine if the attack was exploited.
4. If exploitation is confirmed, initiate breach response procedures.

### Prevention
- Use the OpenSearch client's query builder API exclusively. Never construct query JSON by string concatenation or template interpolation.
- Validate and sanitize the `query` parameter: strip all characters that are not alphanumeric, spaces, hyphens, or common punctuation. Reject queries longer than 500 characters.
- Apply the principle of least privilege to the OpenSearch service account: the API's IAM role must have read-only access limited to the workspace-specific index only.
- Write security tests that submit known DSL injection payloads to the search endpoint and assert they are rejected or safely handled.
- Enable AWS WAF Core Rule Set and specifically the `AWSManagedRulesKnownBadInputsRuleSet` on the API Gateway.

---

## Summary Table

| ID            | Edge Case                          | Severity | Primary Owner           | Status   |
|---------------|------------------------------------|----------|-------------------------|----------|
| EC-SEARCH-001 | Index Out of Sync                  | High     | Backend / Search        | Open     |
| EC-SEARCH-002 | Vector Dimension Mismatch          | Critical | Backend / AI            | Open     |
| EC-SEARCH-003 | Search Cache Stampede              | High     | Backend / Infrastructure| Open     |
| EC-SEARCH-004 | Zero-Result Query Flood            | Medium   | Backend / Security      | Open     |
| EC-SEARCH-005 | Semantic Search Hallucination Risk | High     | AI / Product            | Open     |
| EC-SEARCH-006 | Cross-Workspace Data Leak          | Critical | Backend / Security      | Open     |
| EC-SEARCH-007 | Elasticsearch Shard Failure        | High     | Infrastructure / SRE    | Open     |
| EC-SEARCH-008 | Query Injection Attack             | Critical | Security / Backend      | Open     |

---

## Operational Policy Addendum

### 1. Search Index Consistency Policy

The PostgreSQL database is the system of record for all article content. The OpenSearch index is a derived projection. Any discrepancy between the two is a data integrity violation. The reconciliation job must run nightly and report results to the #search-ops Slack channel. Any gap of more than 50 unindexed articles is a High incident. Any gap of more than 200 is a Critical incident and requires immediate on-call engineer response.

### 2. Vector Embedding Model Change Policy

Changes to the embedding model are classified as breaking changes and must follow the full change management process. A model change requires: (1) written approval from the Engineering Lead, (2) a complete re-embedding plan with cost estimate, (3) a tested rollback plan, (4) a maintenance window. No embedding model changes may be deployed on Fridays or before public holidays.

### 3. Search Query Data Retention Policy

Search queries are retained in the `search_analytics` table for 90 days. Queries containing apparent PII (detected via regex) must be redacted before insertion. Zero-result queries are retained for 7 days only. Query data may not be shared with third parties or used for purposes other than internal relevance improvement and capacity planning.

### 4. Cross-Workspace Isolation Assurance

Search isolation between workspaces is a contractual and legal obligation. Automated synthetic tests asserting cross-workspace isolation must run every 5 minutes in production. If these tests fail, the on-call engineer must treat it as a Critical security incident with a 15-minute response SLA. Disabling or skipping these synthetic tests requires Engineering Lead approval and must be accompanied by a documented risk acceptance.
