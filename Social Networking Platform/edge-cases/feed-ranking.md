# Feed Ranking — Edge Cases

## Overview

The feed ranking system is a real-time ML inference pipeline that personalizes content ordering
for every user on every session. Failures range from total model outages (serving a degraded
chronological fallback) to subtle algorithmic biases that silently degrade engagement quality.
This file covers the failure modes, feedback loops, and cold-start problems that most commonly
cause production incidents or long-term product health degradation.

---

## Failure Modes

| Failure Mode | Impact | Detection | Mitigation | Recovery | Prevention |
|---|---|---|---|---|---|
| Ranking model serving timeout | Feed falls back to chronological order; engagement metrics drop | p99 latency SLO breach on ranking service | Circuit breaker triggers fallback to reverse-chronological feed | Restart ranking pods; drain and reload model shards | Horizontal auto-scaling with pre-warmed replicas; readiness probes |
| Feature store staleness | Ranking uses outdated user-interest signals; reduced personalization quality | Feature freshness metric; age-of-features histogram alert | Serve degraded rank using features within acceptable staleness window | Trigger feature backfill job; monitor freshness recovery | Feature freshness SLOs enforced at serving layer; write-ahead pipeline monitoring |
| A/B experiment conflict | Two overlapping experiments produce contradictory signals; metrics are uninterpretable | Divergent metric trends across experiment buckets; mutual exclusion violations in experiment config | Mutual-exclusion experiment groups; experiment overlap detection in config validation | Roll back conflicting experiment; re-analyze affected metrics window | Experiment platform enforces disjoint user bucketing; pre-launch conflict checks |
| Echo-chamber feedback loop | Users trapped in homogeneous content bubble; reduced discovery; long-term churn risk | Diversity score decline; rising content-type concentration per user cohort | Inject diversity slots (10–15% of feed positions reserved for out-of-cluster content) | Gradual diversification via exploration policy increase; user-visible "broaden my feed" control | Diversity metric as a first-class ranking objective alongside engagement |
| New user cold start | New accounts see generic/low-quality feed; poor first-session experience drives churn | Session duration and return rate for <7-day-old accounts | Onboarding interest survey; topic-following prompts; bootstrapped interest profile from signup signals | Rapid-feedback loop: surface highly-rated content from selected seed interests | Lightweight onboarding flow captures 3–5 interest signals before first feed render |
| Popularity bias collapse | Ranking weights popularity signals too heavily; viral content monopolizes feeds; niche creators lose visibility | Creator diversity metric; content-source Gini coefficient | Cap popularity boost at configurable ceiling; recency and freshness weighting | Re-tune popularity weight; increase fresh-content slot allocation | Regularize popularity features in training; creator health metrics in ranking objectives |
| Model rollback storm | Rapid successive rollbacks destabilize ranking config; every rollback triggers a cache flush | Rollback rate alert; cache hit rate collapse | Staged rollback with traffic ramp; blue/green model serving | Stabilize at known-good model checkpoint; gradual ramp back | Shadow mode validation before any production model promotion; automated rollback gates |
| Training-serving skew | Training data distribution diverges from live serving inputs; model performance degrades silently | KL-divergence alert on feature distributions between training and serving | Log serving features; train on logged features (online learning pipeline) | Retrain on recent serving logs; promote new model | Continuous training pipeline; feature schema versioning; automated distribution tests |

---

## Detailed Scenarios

### Scenario 1: Ranking Model Serving Timeout at Peak Traffic

**Trigger**: A memory leak in the ranking model server accumulates over 8 hours. At peak
evening traffic (3× normal QPS), pod memory limits are breached, triggering OOM kills. The
Kubernetes deployment enters a restart loop, causing p99 latency to exceed 2,000 ms.

**Symptoms**:
- Feed load times spike; user-visible spinner on app home screen.
- Ranking service error rate rises above 5%; circuit breaker opens.
- Feed falls back to reverse-chronological order for affected users.
- Engagement metrics (clicks, watch time) decline by ~30%.

**Detection**:
- p99 ranking latency alert fires at 500 ms threshold (P2) then 1,000 ms (P1).
- Pod restart count alert fires after 3 restarts in 5 minutes.
- Circuit breaker state change emits a P1 PagerDuty alert.

**Mitigation**:
1. Circuit breaker serves chronological fallback feed; user experience is degraded but functional.
2. On-call restarts affected pods; memory profiler attached to next deployment.
3. Horizontal Pod Autoscaler spins up additional replicas from pre-warmed pool.
4. Memory leak root-caused to embedding cache that lacks an eviction policy; patch deployed.

**Prevention**: Memory eviction policies on all caches; resource limits tuned with headroom for
3× traffic spikes; canary deployment with memory growth profiling over 24 hours before full rollout.

---

### Scenario 2: Echo-Chamber Feedback Loop Amplification

**Trigger**: A cohort of users who engage heavily with politically partisan content receive
feeds increasingly dominated by that content type. As engagement signals reinforce the pattern,
ranking weights compound. After 3 months, 40% of the cohort's feeds are a single content
cluster. Cross-cluster engagement drops to near zero.

**Symptoms**:
- Per-user content-type entropy metric declining monotonically for affected cohort.
- Support requests from users feeling "trapped" in specific content types.
- Long-term: session-start rate declining for cohort; 30-day retention drop.

**Detection**:
- Weekly content-diversity score report flags cohort with Gini coefficient >0.75.
- Automated canary in ranking pipeline measures average inter-cluster content variety per feed page.

**Mitigation**:
1. Introduce mandatory diversity slots: positions 4, 8, 12, 20 in each feed page reserved for
   out-of-primary-cluster content.
2. Add a diversity regularization term to the ranking objective function.
3. Surface "Explore new topics" prompt to users whose diversity score falls below threshold.
4. A/B test diversification strategy against control before full rollout.

**Prevention**: Diversity as a first-class offline metric evaluated in every model release;
diversity regression tests block model promotion if score drops >5%.

---

### Scenario 3: New User Cold Start and Churn

**Trigger**: A new user signs up without completing the interest-selection onboarding flow
(closed the modal). The ranking system has zero personalization signal, so the feed defaults
to globally trending content. The user's first 20 posts are celebrity news and viral videos
irrelevant to their actual interests (niche sports). They close the app after 2 minutes and
do not return the next day.

**Symptoms**: Day-1 return rate for users who skipped onboarding is 18% versus 47% for users
who completed it. Session duration for skip-onboarding cohort averages 90 seconds vs. 7 minutes.

**Detection**: Onboarding completion funnel tracking; cohort analysis on D1 retention split by
onboarding completion status.

**Mitigation**:
1. Passive interest inference from signup metadata (device locale, referral source, declared
   age bracket) bootstraps a minimal interest profile without requiring explicit input.
2. First-feed "interest calibration" cards interspersed at positions 3, 7, 15: single-tap
   like/dislike to rapidly capture signal.
3. Trending content filtered by region and age demographic as safe default for zero-signal state.

**Prevention**: Frictionless one-tap interest selection during signup; personalization quality
gates in new-user funnel analytics; D1 retention as a primary metric for ranking team OKRs.
