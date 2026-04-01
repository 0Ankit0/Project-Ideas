# User Stories — Smart Recommendation Engine

**Version**: 2.0.0  
**Status**: Approved  
**Last Updated**: 2025-07-10  
**Owner**: Product Management / ML Platform Team

---

## User Personas

| Persona | Role Description | Primary Goals |
|---------|-----------------|---------------|
| **End User** | Shopper, consumer, or reader interacting with the platform | Discover relevant items quickly; trust the recommendations |
| **Product Manager** | Owns recommendation features and engagement KPIs | Launch experiments, measure lift, configure placement slots |
| **Data Scientist** | Builds and evaluates ML recommendation models | Improve NDCG/MAP@K, run fairness audits, ship better models |
| **ML Engineer** | Operates the ML pipeline and feature infrastructure | Reliable training pipelines, feature store health, model drift monitoring |
| **Platform Admin** | Manages tenants, rate limits, and platform health | System stability, compliance, tenant onboarding |
| **Business Analyst** | Measures business impact of recommendations | CTR, conversion funnels, A/B experiment ROI reporting |
| **Integration Engineer** | Connects client applications to the SRE platform | Clean SDK integration, webhook events, catalog sync |

---

## Epic 1: End-User Personalization

### US-001 — Personalized Homepage Feed

> **As an** end user,  
> **I want** to see a personalized recommendation feed on my homepage,  
> **so that** I can discover items relevant to my tastes without manually searching.

**Priority**: Must Have  
**Role**: End User

**Acceptance Criteria**:
- [ ] The homepage slot (`homepage_hero`) returns ≥ 10 personalized items ranked by predicted relevance score.
- [ ] Recommendations reflect interactions from the user's last 30 days, with recency-weighted scoring.
- [ ] Cold-start users (< 5 interactions) receive a popularity-ranked feed within the same response time SLA.
- [ ] The API response includes a `recommendation_source` field indicating `collaborative`, `content_based`, or `popularity_fallback`.
- [ ] p95 API latency for homepage recommendations is < 100ms under normal load.

---

### US-002 — Similar Items on Product Detail Page

> **As an** end user,  
> **I want** to see a "You might also like" section on item detail pages,  
> **so that** I can explore closely related items without leaving my browsing flow.

**Priority**: Must Have  
**Role**: End User

**Acceptance Criteria**:
- [ ] The PDP slot (`pdp_similar`) returns ≥ 6 items with cosine similarity to the current item's embedding vector.
- [ ] Already-purchased or viewed items (within 7 days) are excluded from the similar-items list by default.
- [ ] Filter expressions (e.g., same category, price ≤ 120% of current item price) are applied before ranking.
- [ ] Response includes an `explanation` field: `"Similar to [item name] that you viewed"`.
- [ ] Recommendations load within 100ms of the page request.

---

### US-003 — Cart Page Cross-Sell Suggestions

> **As an** end user,  
> **I want** to see complementary product suggestions on my cart page,  
> **so that** I can add relevant companion items to my order in a single session.

**Priority**: Must Have  
**Role**: End User

**Acceptance Criteria**:
- [ ] The cart slot (`cart_upsell`) uses current cart item IDs as context to retrieve frequently co-purchased items.
- [ ] Cart items themselves are excluded from the suggestion list.
- [ ] At most 1 item per category of existing cart items is shown (diversity constraint).
- [ ] Suggestions update dynamically when items are added to or removed from the cart.
- [ ] The slot respects server-side filters for in-stock items only.

---

### US-004 — Personalized Email Recommendation Digest

> **As an** end user,  
> **I want** to receive a weekly email with personalized item recommendations,  
> **so that** I can re-engage with the platform and discover items I missed.

**Priority**: Should Have  
**Role**: End User

**Acceptance Criteria**:
- [ ] The batch recommendation job pre-computes a top-10 list for each opted-in user within a 4-hour window.
- [ ] Email lists are available via the batch recommendation list API, keyed by user ID, within 30 minutes of job completion.
- [ ] Users who have opted out of email marketing are excluded from the batch job output.
- [ ] Recommendations in the digest differ from what the user last saw on the homepage (novelty constraint: < 30% overlap with last homepage serving).
- [ ] Job status is accessible via the batch status API with start time, records processed, and terminal state.

---

### US-005 — Opt Out of Personalization

> **As an** end user,  
> **I want** to opt out of behavioral tracking and personalized recommendations,  
> **so that** I can use the platform without my activity being used for profiling.

**Priority**: Must Have  
**Role**: End User

**Acceptance Criteria**:
- [ ] A preference flag `personalization_enabled = false` can be set on the user profile via API.
- [ ] When opted out, all recommendation slots return the popularity-based fallback without any personalized model scoring.
- [ ] Interaction events are still accepted but are flagged as `opted_out = true` and excluded from training datasets.
- [ ] The opt-out takes effect on the next API call (no caching delay for this flag).
- [ ] The opt-out preference is persisted across sessions and devices.

---

### US-006 — View Recommendation Explanation

> **As an** end user,  
> **I want** to see a brief explanation of why an item was recommended to me,  
> **so that** I can understand and trust the recommendation system.

**Priority**: Should Have  
**Role**: End User

**Acceptance Criteria**:
- [ ] Each recommended item in the API response includes an `explanation` object with a `type` (`item_based`, `collaborative`, `popularity`) and a `text` field (e.g., "Because you viewed Wireless Headphones").
- [ ] Item-based explanations reference the most similar item the user has interacted with (highest cosine similarity in embedding space).
- [ ] Collaborative explanations reference user similarity: "Customers with similar taste also liked this."
- [ ] Explanations are human-readable and < 80 characters in length.
- [ ] A `confidence_score` (0.0–1.0) is included alongside each explanation.

---

### US-007 — First Visit Cold-Start Experience

> **As an** end user visiting for the first time,  
> **I want** to see relevant items even before I have any interaction history,  
> **so that** my first experience feels personalized rather than generic.

**Priority**: Must Have  
**Role**: End User

**Acceptance Criteria**:
- [ ] An onboarding preference questionnaire result (selected categories, price range) is accepted by the user profile API and immediately influences the first recommendation response.
- [ ] Without onboarding data, the system returns trending items (top 7-day popularity) in the user's geographic region if available.
- [ ] Cold-start fallback responds within the standard p95 100ms SLA.
- [ ] As the user accumulates interactions (5 → 20 → 50+), the `recommendation_source` field transitions from `popularity_fallback` → `content_based` → `collaborative`.
- [ ] No error or degraded response occurs for brand-new users with zero history.

---

## Epic 2: Product Manager Features

### US-008 — Launch an A/B Experiment

> **As a** product manager,  
> **I want** to create and launch an A/B experiment comparing two recommendation models,  
> **so that** I can measure the causal impact on CTR and conversion before full rollout.

**Priority**: Must Have  
**Role**: Product Manager

**Acceptance Criteria**:
- [ ] An experiment can be created via the experiments API with: name, description, slot, start/end date, traffic split (%), and up to 5 variant model IDs.
- [ ] Traffic split percentages across control + variants must sum to 100%; API returns a validation error otherwise.
- [ ] User assignment to variants is deterministic (hash of experiment_id + user_id) and stable for the experiment's lifetime.
- [ ] Experiment status transitions: `draft` → `running` → `completed` / `paused`.
- [ ] The experiment cannot be launched if it conflicts (same slot, overlapping user population) with an existing running experiment (mutual exclusion enforced).

---

### US-009 — View Experiment Results & Statistical Significance

> **As a** product manager,  
> **I want** to view real-time experiment results including CTR, conversion delta, and statistical significance,  
> **so that** I can make an informed decision on which variant to promote to production.

**Priority**: Must Have  
**Role**: Product Manager

**Acceptance Criteria**:
- [ ] The experiment results API returns per-variant CTR, CVR, revenue-per-user, and NDCG@10 with confidence intervals.
- [ ] Statistical significance is computed via a two-sided t-test; p-value and 95% CI are surfaced for each metric.
- [ ] A "minimum sample size reached" flag is displayed to prevent premature decisions before statistical power is achieved.
- [ ] Results refresh at ≤ 5-minute granularity.
- [ ] An audit log records who viewed and who acted on the experiment results.

---

### US-010 — Configure Diversity Controls per Slot

> **As a** product manager,  
> **I want** to configure the maximum fraction of recommendations from the same category per slot,  
> **so that** users see a varied set of items rather than a single over-represented category.

**Priority**: Should Have  
**Role**: Product Manager

**Acceptance Criteria**:
- [ ] A per-slot configuration API accepts `max_category_fraction` (0.0–1.0, default 0.3).
- [ ] The serving layer enforces MMR (Maximal Marginal Relevance) or a greedy diversity algorithm post-retrieval.
- [ ] Changes to diversity config take effect on the next recommendation request without a service restart.
- [ ] Diversity metrics (ILD — intra-list distance) are logged per slot per hour for monitoring.
- [ ] The configuration is versioned and tied to a tenant ID for multi-tenant isolation.

---

### US-011 — Configure Recommendation Slot Parameters

> **As a** product manager,  
> **I want** to define and configure named recommendation slots with their own algorithm, count, filters, and diversity rules,  
> **so that** each placement on the product (homepage, PDP, cart, email) serves the right kind of recommendations.

**Priority**: Must Have  
**Role**: Product Manager

**Acceptance Criteria**:
- [ ] A slot configuration CRUD API accepts: slot name, algorithm preference, default item count, filter expressions, diversity settings, and fallback strategy.
- [ ] Up to 20 slots can be configured per tenant.
- [ ] Slot configurations are validated on creation (unknown algorithm names are rejected with a descriptive error).
- [ ] Slot-level CTR and conversion metrics are tracked independently in the analytics pipeline.
- [ ] Deleting a slot does not remove historical metric data for that slot.

---

## Epic 3: Data Scientist Features

### US-012 — Train a New Recommendation Model

> **As a** data scientist,  
> **I want** to trigger a model training job with a custom algorithm and hyperparameter configuration,  
> **so that** I can experiment with new approaches and measure offline quality before deployment.

**Priority**: Must Have  
**Role**: Data Scientist

**Acceptance Criteria**:
- [ ] The training API accepts a JSON config with: algorithm (`als`, `ncf`, `bert4rec`, `two_tower`), hyperparameters, dataset date range, validation split ratio, and target tenant.
- [ ] Training progress is streamed via a job status endpoint (step, loss, elapsed time).
- [ ] On completion, evaluation metrics (NDCG@10, MAP@10, precision@10, recall@10, AUC-ROC) are logged to MLflow and returned in the job result.
- [ ] The trained model artifact is saved to the model registry in `Staging` stage with full metadata.
- [ ] Training job failures produce a structured error message with stack trace accessible via the job API.

---

### US-013 — Evaluate Model with NDCG and MAP@K

> **As a** data scientist,  
> **I want** to evaluate any registered model version using NDCG@K and MAP@K on a held-out test set,  
> **so that** I can objectively compare model quality before promoting to production.

**Priority**: Must Have  
**Role**: Data Scientist

**Acceptance Criteria**:
- [ ] An evaluation job can be triggered for any model version in `Staging` or `Production` stage.
- [ ] The evaluation report includes NDCG@5, NDCG@10, MAP@5, MAP@10, MRR, precision@K, and recall@K for configurable K values.
- [ ] Evaluation results are stored in MLflow as a child run linked to the parent training run.
- [ ] A side-by-side comparison view is available for any two model versions within the same tenant.
- [ ] The evaluation dataset is isolated from the training dataset (temporal or random split, configurable).

---

### US-014 — Deploy a Model to Production

> **As a** data scientist,  
> **I want** to promote a staged model to production after it passes promotion gates,  
> **so that** users start receiving recommendations from the improved model.

**Priority**: Must Have  
**Role**: Data Scientist

**Acceptance Criteria**:
- [ ] Promotion is blocked if the model's NDCG@10 does not show ≥ 2% improvement over the current production champion.
- [ ] Promotion is blocked if the fairness scorecard has any metric flagged above the configured threshold.
- [ ] A promotion request creates an audit log entry with: requester, timestamp, model version, metrics delta, and approval status.
- [ ] Traffic to the new model can be ramped incrementally (canary: 5% → 25% → 100%) with automatic rollback if error rate exceeds 5%.
- [ ] The old production model is moved to `Archived` stage but retained for rollback.

---

### US-015 — Configure Hyperparameters for ALS and NCF

> **As a** data scientist,  
> **I want** to configure algorithm-specific hyperparameters when launching a training job,  
> **so that** I can run systematic hyperparameter sweeps and tune model quality.

**Priority**: Must Have  
**Role**: Data Scientist

**Acceptance Criteria**:
- [ ] ALS accepts: `rank` (int, default 128), `reg_param` (float, default 0.01), `max_iter` (int, default 20), `implicit_prefs` (bool).
- [ ] NCF accepts: `embedding_dim` (int, default 64), `hidden_layers` (list[int], default [256, 128, 64]), `dropout` (float, default 0.2), `learning_rate` (float).
- [ ] BERT4Rec accepts: `max_seq_len` (int, default 50), `num_heads` (int, default 4), `num_blocks` (int, default 2), `hidden_size` (int, default 256).
- [ ] Invalid hyperparameter values (e.g., negative rank) are rejected at API validation before the training job is submitted.
- [ ] All hyperparameter configurations are stored alongside model artifacts for reproducibility.

---

### US-016 — Run a Fairness Audit Report

> **As a** data scientist,  
> **I want** to generate a fairness audit report for a trained model,  
> **so that** I can identify demographic disparities in recommendation exposure before deployment.

**Priority**: Should Have  
**Role**: Data Scientist

**Acceptance Criteria**:
- [ ] The fairness audit job accepts a model version ID and a protected attribute name (e.g., `age_bucket`, `gender`).
- [ ] The report computes per-group recommendation exposure rates and NDCG@10 splits across all demographic groups.
- [ ] Demographic parity difference (max exposure gap between any two groups) is computed and flagged if it exceeds the configured threshold (default: 10%).
- [ ] The report is exported in both JSON (for programmatic use) and PDF (for compliance review) formats.
- [ ] If the fairness audit is not run or fails, the model cannot be promoted to production.

---

## Epic 4: ML Engineer Features

### US-017 — Configure Feature Store Feature Groups

> **As an** ML engineer,  
> **I want** to define and configure feature groups in the feature store (user features, item features),  
> **so that** both training jobs and online serving use consistent, versioned feature definitions.

**Priority**: Must Have  
**Role**: ML Engineer

**Acceptance Criteria**:
- [ ] Feature group definitions are stored as YAML/JSON schemas with: feature name, type, source (event stream / catalog API), freshness SLA, and owner.
- [ ] The feature store validates feature group schemas on registration and rejects duplicates or conflicting definitions.
- [ ] User feature groups include: `interaction_count_7d`, `interaction_count_30d`, `category_affinity_vector`, `avg_rating_given`, `last_active_ts`.
- [ ] Item feature groups include: `embedding_vector_512d`, `popularity_score_7d`, `avg_rating_received`, `category_onehot`, `price_bucket`.
- [ ] Feature lineage (source event type → transformation → feature) is tracked and queryable.

---

### US-018 — Set Up Automated Training Pipeline

> **As an** ML engineer,  
> **I want** to configure a scheduled training pipeline that automatically retrains the collaborative filtering model nightly,  
> **so that** the production model stays fresh without manual intervention.

**Priority**: Must Have  
**Role**: ML Engineer

**Acceptance Criteria**:
- [ ] A pipeline configuration accepts: schedule (cron expression), algorithm, hyperparameter config, dataset window, evaluation thresholds, and auto-promote flag.
- [ ] The pipeline automatically triggers feature materialization, model training, evaluation, fairness check, and conditional promotion.
- [ ] Pipeline execution is logged as a DAG run with per-step status, duration, and output artifacts.
- [ ] If any pipeline step fails, the pipeline halts and sends an alert via configured channels (PagerDuty, Slack).
- [ ] The auto-promote flag is disabled by default; manual review is required unless explicitly enabled.

---

### US-019 — Monitor Model Drift and Trigger Retraining

> **As an** ML engineer,  
> **I want** to receive alerts when the serving model's online NDCG drops significantly or feature distributions shift,  
> **so that** I can proactively retrain before recommendation quality degrades for users.

**Priority**: Must Have  
**Role**: ML Engineer

**Acceptance Criteria**:
- [ ] The drift monitoring service computes a 24-hour rolling online NDCG estimate using click-through signals as implicit relevance labels.
- [ ] An alert fires when online NDCG drops > 5% relative to the 7-day baseline.
- [ ] Population Stability Index (PSI) is computed for key features; alert fires when PSI > 0.2 for any feature group.
- [ ] Alerts are routed to PagerDuty (severity: P2) and include: metric name, current value, baseline, delta, and a link to the Grafana dashboard.
- [ ] A retraining job can be triggered directly from the alert, pre-filled with the current production hyperparameter config.

---

### US-020 — Trigger Model Rollback

> **As an** ML engineer,  
> **I want** to roll back the production model to the previous version within 60 seconds,  
> **so that** I can immediately mitigate a quality regression or serving error introduced by a new model deployment.

**Priority**: Must Have  
**Role**: ML Engineer

**Acceptance Criteria**:
- [ ] A rollback API endpoint accepts a tenant ID and optional target model version (defaults to previous production version).
- [ ] Rollback completes and 100% of traffic is on the previous model within 60 seconds.
- [ ] Rollback creates an audit log entry with: initiator, timestamp, rolled-back model version, restored model version, and reason (free text).
- [ ] An automated rollback is triggered if the error rate on recommendation API calls exceeds 5% over a 60-second window post-deployment.
- [ ] Rollback does not affect experiment assignments; users in active A/B tests continue to receive their assigned variant.

---

### US-021 — Configure Online Learning (Micro-Batch Updates)

> **As an** ML engineer,  
> **I want** to configure an online learning pipeline that updates user and item embeddings every 5 minutes using recent interaction events,  
> **so that** the system reacts to within-session behavioral signals faster than the nightly full retrain.

**Priority**: Should Have  
**Role**: ML Engineer

**Acceptance Criteria**:
- [ ] The online learning pipeline consumes events from Kafka in micro-batches with a configurable interval (default: 5 minutes).
- [ ] User embedding vectors in the feature store are updated within the configured interval after a new interaction event.
- [ ] Online learning updates are applied incrementally without requiring a full model retrain.
- [ ] The pipeline supports a "shadow mode" where updates are computed but not applied to serving, for validation before enabling.
- [ ] Lag between event ingestion and feature store update is monitored and alerted if it exceeds 2× the configured interval.

---

## Epic 5: Platform Admin Features

### US-022 — Create and Onboard a New Tenant

> **As a** platform admin,  
> **I want** to create a new tenant with isolated data and configuration namespaces,  
> **so that** a new customer can start using the recommendation platform without any risk of cross-tenant data leakage.

**Priority**: Must Have  
**Role**: Platform Admin

**Acceptance Criteria**:
- [ ] Tenant creation API accepts: tenant ID (globally unique), display name, plan tier, and initial admin user.
- [ ] All data entities (catalog, user profiles, interactions, models, experiments) are namespaced by tenant ID at the storage layer.
- [ ] A default slot configuration (homepage, PDP, cart) is provisioned automatically on tenant creation.
- [ ] An API key scoped to the new tenant is generated and returned only once on creation.
- [ ] Tenant onboarding is idempotent: re-submitting the same tenant ID returns the existing tenant record without creating a duplicate.

---

### US-023 — Configure Per-Tenant Rate Limits

> **As a** platform admin,  
> **I want** to configure per-tenant API rate limits (requests per second),  
> **so that** a single high-traffic tenant cannot degrade service quality for other tenants.

**Priority**: Should Have  
**Role**: Platform Admin

**Acceptance Criteria**:
- [ ] Rate limits can be set per tenant for each API group: recommendation API, event ingestion API, and management APIs.
- [ ] Requests exceeding the rate limit receive an HTTP 429 response with a `Retry-After` header.
- [ ] Rate limit configurations take effect within 30 seconds of update.
- [ ] Rate limit hit counts are emitted as a metric per tenant for monitoring.
- [ ] Admin-tier API calls are exempt from per-tenant rate limits.

---

### US-024 — Process a GDPR Erasure Request

> **As a** platform admin,  
> **I want** to initiate and track a GDPR right-to-erasure request for a specific user,  
> **so that** I can fulfill the legal obligation to delete all personal data within 30 days.

**Priority**: Must Have  
**Role**: Platform Admin

**Acceptance Criteria**:
- [ ] The GDPR erasure API accepts a tenant ID and user ID, and returns an erasure request ID with a submitted timestamp.
- [ ] Within 30 days: all interaction events, user profile data, and pre-computed recommendations for the user are permanently deleted.
- [ ] The user ID is added to a suppression list to prevent re-insertion of data from delayed event streams.
- [ ] The user's interaction data is excluded from any future training dataset materialization.
- [ ] An immutable audit log entry is created and retained for 7 years, recording: request timestamp, requestor, completion timestamp, and data scopes erased.

---

### US-025 — View System Health Dashboard

> **As a** platform admin,  
> **I want** to view a real-time system health dashboard showing API latency, error rates, feature freshness, and model status,  
> **so that** I can proactively identify and resolve incidents before they impact users.

**Priority**: Must Have  
**Role**: Platform Admin

**Acceptance Criteria**:
- [ ] The health API returns: current p95/p99 recommendation API latency, error rate (5xx/4xx), feature store lag, cache hit rate, and current production model version per tenant.
- [ ] Metrics are available at 1-minute granularity with a 7-day retention window via the metrics API.
- [ ] A system status endpoint (`/health`) returns a structured response indicating `healthy`, `degraded`, or `down` for each subsystem.
- [ ] Alerts for SLA breaches (latency > 200ms p99, error rate > 1%) are configured out of the box.
- [ ] The dashboard is accessible to admin-role users only.

---

### US-026 — Manage Banned and Restricted Items

> **As a** platform admin,  
> **I want** to add items to a banned list that prevents them from ever appearing in recommendation results,  
> **so that** I can immediately suppress inappropriate, recalled, or legally restricted items.

**Priority**: Must Have  
**Role**: Platform Admin

**Acceptance Criteria**:
- [ ] A banned items API accepts item IDs with a reason and expiration date (optional).
- [ ] Banned items are excluded from all recommendation slots across all serving strategies (real-time and batch).
- [ ] The ban takes effect within 60 seconds of the API call (no cache delay for safety).
- [ ] Banned item IDs are propagated to all serving replicas via a distributed configuration update.
- [ ] The ban list is auditable with a log of who banned each item and when.

---

## Epic 6: Business Analyst Features

### US-027 — View CTR Report by Slot and Model

> **As a** business analyst,  
> **I want** to view a CTR report broken down by recommendation slot and model version,  
> **so that** I can identify which placements and models drive the most user engagement.

**Priority**: Must Have  
**Role**: Business Analyst

**Acceptance Criteria**:
- [ ] The analytics API returns CTR per slot, per model version, and per date range (configurable start/end).
- [ ] Data is aggregated at daily and hourly granularity.
- [ ] The report includes: impressions, clicks, CTR, and 95% CI for CTR.
- [ ] Filters are supported for: tenant, slot, model version, user segment, device type.
- [ ] Report data can be exported in CSV and JSON formats.

---

### US-028 — View Conversion Funnel from Recommendation to Purchase

> **As a** business analyst,  
> **I want** to view a conversion funnel showing the rate at which recommendation impressions lead to clicks, add-to-cart, and purchases,  
> **so that** I can measure the full business impact of the recommendation engine.

**Priority**: Must Have  
**Role**: Business Analyst

**Acceptance Criteria**:
- [ ] The funnel report shows: impressions → clicks → add_to_cart → purchase, with conversion rates between each step.
- [ ] Attribution window is configurable (default: 30 minutes for add_to_cart and purchase after a recommendation click).
- [ ] Revenue attributed to recommendations is reported alongside unit conversion rates.
- [ ] Funnel data is segmented by slot, model version, and user cohort (new vs returning).
- [ ] A comparison view allows side-by-side funnel analysis for two time periods or two model versions.

---

### US-029 — Export Interaction Data for Analysis

> **As a** business analyst,  
> **I want** to export raw interaction event data for a specified date range,  
> **so that** I can perform ad-hoc analysis in external BI tools.

**Priority**: Should Have  
**Role**: Business Analyst

**Acceptance Criteria**:
- [ ] The export API accepts: tenant ID, event types, date range, and output format (CSV/JSON/Parquet).
- [ ] Exports are processed asynchronously and available for download via a signed URL within 30 minutes.
- [ ] Exported data is pseudonymized (user IDs are HMAC-hashed; no raw PII included).
- [ ] Export jobs are subject to the requester's role-based access control; analysts can only export their tenant's data.
- [ ] A download link expires after 24 hours for security.

---

### US-030 — Compare A/B Experiment Results Side-by-Side

> **As a** business analyst,  
> **I want** to compare all variants in a completed A/B experiment side-by-side with statistical annotations,  
> **so that** I can present a data-driven recommendation to leadership on which model to roll out.

**Priority**: Must Have  
**Role**: Business Analyst

**Acceptance Criteria**:
- [ ] The experiment comparison API returns a table of all variants with: CTR, CVR, revenue-per-user, NDCG@10, p-value vs control, and CI width.
- [ ] Variants that have reached statistical significance (p < 0.05) are highlighted.
- [ ] A "winner" is flagged if one variant is statistically significantly better on the primary metric.
- [ ] The comparison report is exportable as PDF and CSV.
- [ ] Historical experiment comparisons are stored indefinitely for audit and retrospective analysis.

---

## Epic 7: Integration Engineer Features

### US-031 — Subscribe to Webhook Events

> **As an** integration engineer,  
> **I want** to subscribe to webhook events for model deployments and experiment completions,  
> **so that** my downstream application can react automatically to platform events without polling.

**Priority**: Should Have  
**Role**: Integration Engineer

**Acceptance Criteria**:
- [ ] A webhook subscription API accepts: event type (`model.deployed`, `experiment.completed`, `gdpr.erasure_complete`), target URL, and a secret for HMAC request signing.
- [ ] Webhook payloads are signed with HMAC-SHA256 using the subscriber's secret; the signature is included in the `X-SRE-Signature` header.
- [ ] Webhook delivery is retried up to 3 times with exponential backoff (1s, 5s, 30s) if the target URL returns a non-2xx response.
- [ ] A webhook delivery log is available via API, showing: event, target URL, delivery status, HTTP response code, and timestamp.
- [ ] Subscriptions can be paused and resumed without deletion.

---

### US-032 — Integrate Using the Python SDK

> **As an** integration engineer,  
> **I want** to use an official Python SDK to call the recommendation API, track events, and manage experiments,  
> **so that** I can integrate the SRE into our Python application with minimal boilerplate and robust error handling.

**Priority**: Should Have  
**Role**: Integration Engineer

**Acceptance Criteria**:
- [ ] The `sre-client` Python package is installable via `pip install sre-client` and supports Python 3.11+.
- [ ] The SDK exposes typed client classes: `RecommendationClient`, `EventClient`, `ExperimentClient`.
- [ ] The SDK implements automatic retry with exponential backoff for transient errors (5xx, network timeout).
- [ ] The SDK implements a circuit breaker that short-circuits after 5 consecutive failures and re-tests after a 30-second half-open period.
- [ ] The SDK is fully type-annotated and includes a complete docstring for every public method.

---

### US-033 — Call the Batch Recommendation API for Campaign Use

> **As an** integration engineer,  
> **I want** to retrieve pre-computed recommendation lists for a batch of up to 10,000 users in a single API call,  
> **so that** I can populate personalized email campaigns efficiently without making one API call per user.

**Priority**: Must Have  
**Role**: Integration Engineer

**Acceptance Criteria**:
- [ ] The batch recommendation API (`POST /v1/recommend/batch`) accepts a JSON body with: `user_ids` (array, max 10,000), `slot`, and optional `filters`.
- [ ] Response returns a map of user_id → ranked item list, with items missing their history receiving the fallback list.
- [ ] The batch API response time is ≤ 5 seconds for 10,000 user IDs (using pre-computed cache).
- [ ] A `cache_age_seconds` field in the response indicates how old the pre-computed recommendations are.
- [ ] Rate limits for the batch API are configured separately from the real-time API.

---

### US-034 — Upload Catalog via Bulk API

> **As an** integration engineer,  
> **I want** to upload or update the item catalog in bulk via a single API call,  
> **so that** the recommendation engine stays synchronized with our product catalog without item-by-item API calls.

**Priority**: Must Have  
**Role**: Integration Engineer

**Acceptance Criteria**:
- [ ] The catalog bulk upload API (`POST /v1/catalog/bulk`) accepts a JSON Lines or CSV file with up to 1,000,000 items.
- [ ] The API returns a job ID immediately; the upload is processed asynchronously with status available via `/v1/catalog/jobs/{job_id}`.
- [ ] Invalid rows (missing required fields, invalid types) are collected in an error report available on job completion; valid rows are still processed.
- [ ] Embeddings are regenerated for all new or updated items within 5 minutes of job completion.
- [ ] A checksum of the uploaded file is accepted and validated server-side to detect upload corruption.

---

## Epic 8: Multi-Tenant & Governance

### US-035 — Per-Tenant Model Version Pinning

> **As a** platform admin,  
> **I want** to pin a tenant to a specific model version,  
> **so that** that tenant's serving remains stable even when other tenants receive model upgrades.

**Priority**: Should Have  
**Role**: Platform Admin

**Acceptance Criteria**:
- [ ] A tenant configuration API supports `model_version_pin: <version_id>` that overrides automatic model promotion for that tenant.
- [ ] Pinned tenants are excluded from automated nightly model promotion.
- [ ] The pinned version and the current global production version are both visible in the tenant's status API response.
- [ ] An admin can clear the pin to resume normal auto-promotion.
- [ ] Version pins are audited: creation, modification, and removal are logged with actor and timestamp.

---

### US-036 — Manage Per-Tenant Feature Freshness SLAs

> **As an** ML engineer,  
> **I want** to configure per-tenant feature freshness SLAs for each feature group,  
> **so that** high-value tenants can have stricter freshness guarantees than lower-tier tenants.

**Priority**: Should Have  
**Role**: ML Engineer

**Acceptance Criteria**:
- [ ] Feature freshness SLAs are configurable per tenant per feature group (e.g., `user_interaction_features: 5min`, `item_popularity: 15min`).
- [ ] An alert fires when a feature group's actual lag exceeds the configured SLA for a given tenant.
- [ ] Feature freshness lag is reported per tenant per feature group in the health dashboard.
- [ ] SLA configuration changes take effect without service restart.
- [ ] Tenants with stricter SLAs are prioritized in feature materialization job scheduling.

---

## Story Summary & Priority Matrix

| US ID | Title | Role | Priority |
|-------|-------|------|----------|
| US-001 | Personalized Homepage Feed | End User | Must Have |
| US-002 | Similar Items on PDP | End User | Must Have |
| US-003 | Cart Page Cross-Sell | End User | Must Have |
| US-004 | Personalized Email Digest | End User | Should Have |
| US-005 | Opt Out of Personalization | End User | Must Have |
| US-006 | View Recommendation Explanation | End User | Should Have |
| US-007 | First Visit Cold-Start Experience | End User | Must Have |
| US-008 | Launch an A/B Experiment | Product Manager | Must Have |
| US-009 | View Experiment Results | Product Manager | Must Have |
| US-010 | Configure Diversity Controls | Product Manager | Should Have |
| US-011 | Configure Recommendation Slot | Product Manager | Must Have |
| US-012 | Train a New Model | Data Scientist | Must Have |
| US-013 | Evaluate with NDCG / MAP@K | Data Scientist | Must Have |
| US-014 | Deploy Model to Production | Data Scientist | Must Have |
| US-015 | Configure Hyperparameters | Data Scientist | Must Have |
| US-016 | Run Fairness Audit Report | Data Scientist | Should Have |
| US-017 | Configure Feature Store Groups | ML Engineer | Must Have |
| US-018 | Set Up Training Pipeline | ML Engineer | Must Have |
| US-019 | Monitor Model Drift | ML Engineer | Must Have |
| US-020 | Trigger Model Rollback | ML Engineer | Must Have |
| US-021 | Configure Online Learning | ML Engineer | Should Have |
| US-022 | Onboard New Tenant | Platform Admin | Must Have |
| US-023 | Configure Rate Limits | Platform Admin | Should Have |
| US-024 | Process GDPR Erasure | Platform Admin | Must Have |
| US-025 | View System Health Dashboard | Platform Admin | Must Have |
| US-026 | Manage Banned Items | Platform Admin | Must Have |
| US-027 | View CTR Report | Business Analyst | Must Have |
| US-028 | View Conversion Funnel | Business Analyst | Must Have |
| US-029 | Export Interaction Data | Business Analyst | Should Have |
| US-030 | Compare A/B Results | Business Analyst | Must Have |
| US-031 | Subscribe to Webhooks | Integration Engineer | Should Have |
| US-032 | Integrate Python SDK | Integration Engineer | Should Have |
| US-033 | Batch Recommendation API | Integration Engineer | Must Have |
| US-034 | Bulk Catalog Upload | Integration Engineer | Must Have |
| US-035 | Per-Tenant Model Pinning | Platform Admin | Should Have |
| US-036 | Manage Feature Freshness SLAs | ML Engineer | Should Have |

---

## MoSCoW Summary

| Must Have | Should Have | Nice to Have |
|-----------|-------------|--------------|
| US-001, US-002, US-003 | US-004, US-006 | US-021 (online learning) |
| US-005, US-007 | US-010, US-016 | US-035 (model pinning) |
| US-008, US-009, US-011 | US-023, US-029 | US-036 (SLA config) |
| US-012, US-013, US-014, US-015 | US-031, US-032 | |
| US-017, US-018, US-019, US-020 | US-019 (drift alerts) | |
| US-022, US-024, US-025, US-026 | | |
| US-027, US-028, US-030 | | |
| US-033, US-034 | | |
