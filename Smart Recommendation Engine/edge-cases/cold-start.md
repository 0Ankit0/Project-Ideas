# Edge Cases — Cold Start

Cold start problems arise whenever a user, item, or the entire system lacks sufficient interaction history to produce high-quality personalized recommendations. These are among the most common failure modes and must be handled gracefully since every new user and every new catalog item will pass through this state.

---

### 1. New User with Zero Interactions

**Failure Mode**: A user registers and immediately requests recommendations. The collaborative filtering model has no user history to operate on; the content-based model has no preference signal. The system has no embeddings, no implicit feedback, and no explicit ratings to anchor a personalized response.

**Impact**: High — poor first impression leads to a 30–50% higher bounce rate for new users compared to warm users. Revenue loss on first visit is disproportionately significant since first-session conversion is a strong predictor of long-term retention. The system silently serves a degraded experience with no error surfaced to the client.

**Detection**: Check for `cold_start=true` flag in the recommendation response envelope; confirm `user_profile.cold_start_phase='cold'`; monitor `interaction_count < 5` for the requesting user. Alert if `cold_start_rate > 15%` of total recommendation requests — a spike typically indicates a new marketing acquisition campaign or a data pipeline failure resetting interaction counts.

**Mitigation**: Serve popularity-based fallback recommendations (global trending, regionally trending) immediately. Trigger onboarding preference survey during the session — prompt the user to select 3–5 interest categories before serving recommendations. Use device type, referrer URL, and UTM parameters as weak signals for initial personalization. Serve trending items scoped to the user's detected locale. Ensure the popularity model is always pre-warmed and available independently of the personalization stack.

**Recovery**: Not a failure state requiring recovery — cold start is expected behavior. Ensure that the fallback popularity model is always available and pre-computed. If a user is incorrectly stuck in `cold_start_phase='cold'` despite having interactions (pipeline failure), trigger a manual feature vector recomputation job for the affected user cohort.

**Prevention**: Pre-populate a lightweight user preference profile from registration data — age bracket, location, and signup source (e.g., referral campaign category) can anchor a weak content-based signal before any interactions occur. Design the UX to encourage first interactions within the session (e.g., swipeable item cards with implicit feedback). Progressively collect implicit preferences and graduate users to `warm` phase upon reaching 5 interactions.

---

### 2. New Item Added to Catalog with No Ratings

**Failure Mode**: A newly ingested item has no interaction history. Collaborative filtering cannot include it in the factored user-item matrix because it has no co-occurrence signal. The approximate nearest-neighbor (ANN) index may not yet contain its embedding vector if the index has not been rebuilt since item creation. The item is effectively invisible to the recommendation engine.

**Impact**: Medium — new items are never discovered by users, reducing catalog coverage and novelty scores system-wide. The problem is especially acute for time-sensitive items (breaking news, seasonal products, limited-run inventory) where a 24-hour discovery delay destroys most of the item's commercial value. Catalog expansion efforts are undermined if new items consistently receive zero recommendation exposure.

**Detection**: Monitor the `catalog_coverage` metric — a drop immediately following a bulk item ingestion event indicates new items are not being picked up. Track `item_age_hours` versus `first_recommendation_at` for new items. Alert if any item older than 24 hours has `recommendation_count = 0`. Check for items in the catalog table that have no entry in the `item_embeddings` table.

**Mitigation**: Trigger content-based embedding generation on the `ItemCreated` event — target completion within 60 seconds of item creation. Apply a new item injection policy: force 5% of each recommendation slate to include items with `created_at < 7 days`. Score new items using `content_similarity_score × recency_boost_factor` where `recency_boost_factor` decays from 2.0 at creation to 1.0 at 7 days. Allow manual boost via `slot_config.boost_rules` for high-priority new items.

**Recovery**: Query for items in the catalog that are missing embedding vectors; trigger `ItemEmbeddingGeneration` job for the missing cohort. Force ANN index rebuild after resolving embedding gaps. Validate index completeness with item count comparison between `catalog_items` and `item_embeddings` tables. Re-run affected recommendation slots after index is rebuilt.

**Prevention**: Subscribe to `ItemCreated` events in the embedding service and automate vector generation as part of the item onboarding pipeline. Set up `ItemEmbeddingMissing` alert with a 2-hour grace period for processing. Include item freshness as an explicit ranking feature in the hybrid scoring model so the model learns to surface new items even before accumulating interaction history.

---

### 3. System-wide Cold Start (After Data Wipe or Disaster Recovery)

**Failure Mode**: A catastrophic data loss event (accidental database drop, ransomware, failed migration, region-level outage) destroys all interaction data, user profiles, and feature vectors. All models need to be retrained from scratch. No historical personalization signal is available. Every user is treated as if they registered today.

**Impact**: Critical — the entire platform reverts to popularity-based recommendations for 100% of users. Personalization quality drops to near-zero. Depending on data retention and recovery capabilities, degraded operation may last hours to days. Business impact includes revenue loss, user trust erosion, and potential SLA breach with enterprise tenants. Retraining may take 4–12 hours for large datasets.

**Detection**: `interaction_count = 0` for all users system-wide (not just a subset); all users simultaneously transition to `cold_start_phase='cold'`; feature store returns empty vectors for all queries; model serving logs show 100% fallback to popularity model. These signals in combination distinguish a true system-wide cold start from a localized pipeline failure.

**Mitigation**: Serve popularity-based recommendations immediately during the recovery window. Communicate estimated recovery timeline to internal stakeholders and, if SLA-bound, to enterprise tenants. Prioritize restoration of the most recent interaction data first (last 30 days) to restore partial personalization for active users before full historical recovery. Activate read-replica or standby database to prevent write load from slowing recovery.

**Recovery**: Restore PostgreSQL from the latest point-in-time snapshot (target RTO < 4 hours for 30-day retention policy). Replay Kafka messages from the interaction topic (7-day retention window) to reconstruct the feature store for the most recent interactions. Trigger emergency model retraining once sufficient data is restored. Serve popularity-based recommendations during the full recovery window. Validate feature store completeness before switching traffic back to personalized model.

**Prevention**: Implement cross-region database replication with automatic failover. Maintain daily PostgreSQL snapshots with 30-day retention, stored in a separate cloud region. Run weekly automated backup verification: restore to a test instance and run a validation query suite. Maintain the popularity model on a completely independent infrastructure stack that is not dependent on the personalization data pipeline, so at minimum a quality fallback is always available.

---

### 4. Popularity Bias During Cold Start

**Failure Mode**: The cold start fallback algorithm recommends only the most globally popular items (head items in the long-tail distribution). The top 1% of items by interaction volume receive 100% of cold-start recommendation exposure. The 99% of the catalog — including niche, regional, and newly launched items — receives zero exposure. New users receive a distorted first impression of the platform's breadth.

**Impact**: Medium — reduces catalog coverage for cold-start requests; creates a self-reinforcing popularity loop where head items accumulate even more interactions; systematically disadvantages new, niche, and regional items from ever accumulating the interaction signal needed to enter collaborative filtering. New user preferences may be artificially homogenized toward head items, reducing long-term engagement diversity.

**Detection**: Monitor the Gini coefficient of the item recommendation distribution for cold-start requests — a value above 0.9 indicates extreme concentration. Track `catalog_coverage` for cold-start requests (alert if < 10% of catalog items appear in cold-start slates over a rolling 24-hour window). Monitor `diversity_score` in recommendation responses — alert if the average falls below 0.2 for cold-start cohort.

**Mitigation**: Replace the single popularity score with a diversified cold-start slate composition policy: 40% globally trending (last 7 days), 30% new arrivals (last 7 days), 20% category-sampled proportionally to catalog distribution, 10% serendipitous (random draw with quality floor). Maintain separate popularity tiers — global trending and per-category trending — so category-level recommendations aren't dominated by cross-category blockbusters. Enforce a minimum diversity floor per business rule BR-07.

**Recovery**: Update cold-start algorithm parameters in the serving configuration without requiring model retraining. Reduce the `popularity_weight` parameter and introduce an `exploration_bonus` in the cold-start scoring function. Validate the change on a held-out cold-start user cohort before rolling out fully.

**Prevention**: Run periodic A/B tests on cold-start strategies to measure new user conversion rates segmented by recommendation diversity. Measure whether diverse cold-start slates improve 7-day retention compared to popularity-only baselines. Conduct fairness audits on cold-start recommendations (BR-09) to ensure niche and regional items receive equitable exposure opportunities.

---

### 5. A/B Test Cold Start Distortion

**Failure Mode**: A new user is assigned to a treatment variant in an active A/B experiment simultaneously with being in the cold start phase. The user's experience is doubly degraded — cold start provides low-quality signals, and the treatment variant may further alter recommendation quality in ways that are confounded with the cold start effect. Experiment results are contaminated by this overlap.

**Impact**: Medium — the cold-start effect inflates or deflates the apparent performance gap between control and treatment variants, depending on how cold-start users are distributed across experiment groups. This can cause false positives (shipping a treatment that only appeared better because cold-start users were unevenly distributed) or false negatives (rejecting a genuinely better treatment). Repeated contamination erodes confidence in the A/B testing framework.

**Detection**: Monitor `new_user_rate` per experiment variant — a statistically significant imbalance indicates randomization failure or assignment timing issues. Run a chi-square test on the `interaction_count` distribution across variants at the time of assignment. Compare `cold_start_rate` between control and treatment groups; a difference > 5 percentage points warrants investigation. Log `user_cold_start_phase` in experiment exposure events.

**Mitigation**: By default, exclude users in `cold_start_phase='cold'` from A/B experiment assignment using experiment eligibility criteria. Only assign users to experiments after they have reached `cold_start_phase='warm'` (minimum interaction threshold, e.g., 5 interactions). Alternatively, run a dedicated cold-start experiment group separate from the main experiment cohort so cold-start optimization is studied independently.

**Recovery**: Re-analyze concluded experiment data after filtering out cold-start users. If the experiment was declared significant based on contaminated data, mark the result as inconclusive in the experiment tracking system and schedule a re-run with proper eligibility filtering. Document the contamination event in the experiment log for future reference.

**Prevention**: Add an `eligibility_criteria` field to `ExperimentConfig` that enforces minimum interaction count requirements before user assignment. Implement an automated pre-experiment balance check that validates `interaction_count` distribution is statistically similar across variants at the point of analysis. Include minimum interaction count as a hard filter in the user assignment service, not just in post-hoc analysis.
