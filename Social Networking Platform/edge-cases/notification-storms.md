# Notification Storms — Edge Cases

## Overview

Notification delivery is a high-volume, fan-out-heavy system. A celebrity with 50 million
followers posting a single item can trigger 50 million push notification write operations
within seconds. The gap between "notification sent" and "notification delivered" hides a rich
failure space: APNs/FCM rejections, device token staleness, user-level throttle violations,
and thundering-herd effects on the backend when users tap notifications simultaneously.
This file documents the most critical failure modes in the notification pipeline.

---

## Failure Modes

| Failure Mode | Impact | Detection | Mitigation | Recovery | Prevention |
|---|---|---|---|---|---|
| Celebrity post fan-out storm | Notification workers saturated; queue depth explodes; delivery delayed for all users | Notification queue depth alert; worker CPU/memory saturation | Tiered fan-out: pre-computed follower shards; rate-limited worker pools; priority lanes | Drain backlog using burst-capacity worker pool; deprioritize low-priority notification types | Fan-out budget per post based on follower count; async multi-stage fan-out for mega-accounts |
| Push token staleness causing delivery failure | Notifications silently dropped; users miss important alerts | APNs/FCM "invalid token" error rate spike; delivery success rate drop | Lazy token invalidation on 410 responses; periodic token health sweep | Remove stale tokens; prompt user to re-register device | Token rotation on app open; proactive health-check pings for inactive tokens |
| Notification flood to single user | User receives hundreds of notifications within minutes (mention storm, reply chain explosion) | Per-user notification rate counter; user complaints/uninstalls | Per-user rate limiter with configurable daily/hourly caps; notification digest batching | Flush pending individual notifications into a single digest; apply temporary hold | Default notification preferences with aggressive deduplication; notification preference center |
| Push provider outage (APNs/FCM) | Push notifications undeliverable to iOS/Android respectively | HTTP 5xx rate from push provider; delivery success rate drop | Retry queue with exponential backoff and jitter; fallback to in-app badge/counter | Process retry backlog when provider recovers; send catch-up in-app notification summary | Multi-provider architecture for critical notification types; in-app inbox as persistent fallback |
| Notification deduplication failure | User receives duplicate notifications for the same event | User reports; client-side dedup log divergence | Server-side idempotency key per notification event; client-side dedup window | Suppress duplicates at client based on event ID; apologize proactively for flood events | Idempotency enforcement at notification creation layer; event dedup at Kafka consumer |
| Thundering herd on notification tap | Millions of users tap a notification simultaneously; origin servers overwhelmed | Traffic spike correlated with celebrity notification delivery; cache miss rate spike | Pre-warm cache for destination content before fan-out completes; stagger delivery | Activate read-path caching; shed non-critical writes; serve stale cache | Delivery time randomization (jitter) for mass notifications; predictive cache warming |
| Silent notification causing background wake abuse | App uses silent push to over-trigger background refresh; OS throttles app; critical notifications delayed | Increased OS-level background task kills; user reports of missing notifications | Limit silent notification rate; use standard push for time-sensitive events | Re-send affected notifications via standard channel | Audit silent push usage; document background push budget in API contracts |
| Kafka consumer lag on notification pipeline | Notification delivery delayed by minutes to hours during traffic surges | Consumer lag metric alert on notification topic | Scale consumer group; prioritize high-urgency notification topics | Catch-up processing with burst consumer capacity; stale low-priority notifications discarded | Auto-scaling consumer group; topic partitioning sized for peak load plus 3× headroom |

---

## Detailed Scenarios

### Scenario 1: Celebrity Post Fan-Out Storm

**Trigger**: A verified account with 48 million followers posts a video at 8:00 PM on a
Friday. The notification pipeline attempts to enqueue 48 million push tasks within 60 seconds.
Worker pods are provisioned for a sustained load of 500,000 tasks/minute; the instantaneous
spike is 48× their capacity.

**Symptoms**:
- Notification task queue depth climbs from nominal 200K to 28 million within 90 seconds.
- Worker pod CPU pegs at 100%; memory pressure triggers OOM kills.
- Notification latency for all users (not just the celebrity's followers) rises from ~2 seconds
  to 18 minutes as the pipeline is fully saturated.
- Direct-message notifications — higher priority, smaller volume — are delayed by the backlog.

**Detection**:
- Queue depth alert fires at 1 million tasks (P2) and 5 million tasks (P1).
- Worker CPU saturation alert fires after 60 seconds at >90%.
- Notification delivery latency p95 alert fires at 30-second threshold.

**Mitigation**:
1. **Tiered fan-out**: For accounts with >1 million followers, fan-out is split into 10-minute
   delivery windows. Followers are bucketed by timezone and engagement history; high-engagement
   followers receive delivery in the first window.
2. **Priority lanes**: Direct messages and security alerts occupy a dedicated high-priority
   queue that is not affected by general-content fan-out congestion.
3. **Burst capacity**: Pre-configured auto-scaling policy spins up 5× additional consumer pods
   within 3 minutes of a queue-depth breach.
4. **Delivery budget**: Accounts with >500K followers have a configurable notification delivery
   rate (e.g., 200K/minute max) to prevent single-account storms.

**Recovery**: Backlog is drained over 45 minutes using burst capacity. Low-priority
notifications older than 2 hours are discarded rather than delivered stale.

**Prevention**: Fan-out load test with synthetic mega-account as part of capacity planning;
delivery budget enforced in notification creation service.

---

### Scenario 2: Notification Flood — Reply Chain Explosion

**Trigger**: A user is mentioned in a post that goes viral. 12,000 replies are added over
4 hours, each triggering a "someone replied to a post you're mentioned in" notification. The
user receives 12,000 push notifications. Their device notification tray is unusable; they
uninstall the app.

**Symptoms**:
- Per-user notification count exceeds 500 in one hour (alert threshold).
- User uninstall event fires shortly after.
- App store review submitted: "notification spam."

**Detection**:
- Per-user hourly notification rate counter in Redis; alert at 200 notifications/hour.
- Uninstall event correlated with notification volume in funnel analysis.

**Mitigation**:
1. **Digest batching**: When a user exceeds 10 notifications of the same type within 5 minutes,
   subsequent notifications are suppressed and a single digest ("47 new replies to a post you're
   in") is sent every 15 minutes.
2. **Thread-level opt-out**: After 5 notifications from a single thread, surface an in-notification
   "mute this thread" action.
3. **Per-user daily cap**: Hard limit of 500 push notifications per user per day across all
   non-security types, with overflow held in the in-app inbox.

**Recovery**: Retroactively silence the notification flood for the affected user; send a single
catch-up summary; issue an in-app apology card.

**Prevention**: Notification preference center prominently surfaced during onboarding; default
notification settings use digest mode for mention replies.

---

### Scenario 3: Push Provider Partial Outage

**Trigger**: APNs (Apple Push Notification service) experiences elevated error rates for a
subset of device tokens in the US-East region. 18% of iOS push notifications receive a 5xx
response. The notification pipeline's immediate retry logic sends the same notifications up to
3 times within 60 seconds, amplifying the load on APNs and compounding the outage.

**Symptoms**:
- iOS delivery success rate drops from 98.5% to 82% in the affected region.
- Retry amplification causes APNs to begin rate-limiting the platform's sending certificate.
- Android (FCM) notifications are unaffected; parity gap triggers user confusion.

**Detection**:
- APNs HTTP 5xx error rate alert fires at 2% threshold.
- Delivery success rate SLO breach alert (iOS p95 delivery < 95%) fires within 5 minutes.

**Mitigation**:
1. **Exponential backoff with jitter**: Retry queue applies 30s → 2m → 8m → 32m backoff with
   ±20% jitter to prevent retry storms.
2. **Dead-letter queue**: After 4 failed attempts, notification moves to DLQ for manual
   review and catch-up delivery once provider recovers.
3. **In-app inbox fallback**: For notification types classified as "important" (DMs, security
   alerts), the in-app inbox badge is updated immediately as a delivery fallback.
4. **Provider health circuit breaker**: If APNs error rate exceeds 10% for 2 minutes, halt
   new enqueues and accumulate in a local buffer to avoid further amplification.

**Recovery**: When APNs recovers, drain the DLQ with a controlled send rate of 50K/minute.
Notifications older than 6 hours are converted to in-app inbox items rather than push.

**Prevention**: Load testing with simulated provider failure scenarios quarterly; multi-provider
fallback for critical notification types.
