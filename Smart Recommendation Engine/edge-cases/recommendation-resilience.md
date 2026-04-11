# Edge Cases — Recommendation Resilience

This runbook consolidates high-risk recommendation edge cases across serving, ranking, and feature systems.

## 1) Cold Start (User/Item/System)
- **Failure mode**: insufficient historical interactions or full personalization reset.
- **Detection**: elevated `cold_start_rate`, empty user embeddings, high fallback usage.
- **Mitigation**: blend trending + contextual + exploratory items; force onboarding preference capture.
- **Recovery**: replay events, regenerate profiles, retrain and rehydrate embeddings.

## 2) Popularity Bias
- **Failure mode**: head items monopolize exposure and long-tail discovery collapses.
- **Detection**: high exposure Gini coefficient, low catalog coverage, low entropy in top-K.
- **Mitigation**: diversity-constrained re-rank, category quotas, novelty injection.
- **Recovery**: reduce popularity weight, retune exploration factor, validate cohort-level KPIs.

## 3) Stale Embeddings
- **Failure mode**: user/item embeddings exceed freshness SLO and no longer represent current behavior.
- **Detection**: `embedding_staleness_seconds` threshold breaches; CTR drop concentrated in stale cohort.
- **Mitigation**: lower ANN influence and increase session/context ranker weights.
- **Recovery**: trigger embedding backfill + index refresh; verify index/model compatibility.

## 4) Missing Features
- **Failure mode**: critical online features unavailable due to upstream timeout/schema break.
- **Detection**: feature null-rate spike, contract validation errors, dependency timeout alarms.
- **Mitigation**: deterministic defaulting for non-critical features; switch to fallback strategy for critical gaps.
- **Recovery**: restore upstream services, replay delayed updates, verify feature parity tests.

## 5) Degraded Mode Recommendations
- **Failure mode**: ANN/feature store/ranker failures force simplified recommendation path.
- **Detection**: `degraded_mode=true` ratio breach, fallback-path alarms, p95 latency anomalies.
- **Mitigation**: serve cached or precomputed slates plus policy filtering; preserve non-empty results.
- **Recovery**: dependency-level health restore, circuit breaker close, staged return to full ranking.

## Degraded Mode Priority Order
1. Full personalized pipeline.
2. Personalized candidates + lightweight ranker.
3. Context + popularity hybrid.
4. Cached fallback slate (tenant + locale aware).

## Validation Checklist
- [ ] Every edge case has an alert with owner and severity.
- [ ] Fallback paths are contract-tested pre-release.
- [ ] Degraded responses include machine-readable reason codes.
- [ ] Rollback path to last-known-good model/index is one command or one click.
