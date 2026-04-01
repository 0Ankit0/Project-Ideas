# Video Streaming Platform - API & UI Edge Cases

## Scenario 1: CDN Origin Returns 503 Service Unavailable

When origin S3/CloudFront experiences degraded performance or outage, all playback requests fail. CloudFront returns 503 to viewers. Problem: no fallback origin, no graceful degradation.

**Failure Mode**: Origin database connection pool exhausted, origin rejects new requests with 503. All viewers see immediate playback failure.

**Symptoms**: CloudFront logs show >50% 503 responses. Viewer app shows "Cannot connect to broadcast" within 1 second.

**Detection**: Monitor origin HTTP 503 rate, alert if >1% of requests fail with 503.

**Mitigation**: 
1. Configure CloudFront origin shield (intermediate cache layer)
2. Implement origin failover (primary + secondary region)
3. Return cached manifest/segments from edge when origin fails
4. Circuit breaker: if 503 rate >5%, pause new playback requests, queue them

**Recovery**: Auto-scale origin resources. Monitor recovers within 5 minutes.

---

## Scenario 2: Player SDK Null Pointer Exception on Corrupt Manifest

Player SDK receives invalid M3U8 file (missing EXT-X-ENDLIST), attempts to parse, gets null pointer when accessing array element. App crashes.

**Failure Mode**: Manifest generator produces invalid M3U8. Player crashes on parse (native code).

**Symptoms**: App crashes with "NullPointerException" in media parsing code. Crash reports flood error tracking system.

**Detection**: Crash analytics alert if crash rate >0.5% (usually <0.1%).

**Mitigation**:
1. Validate manifest before upload (schema validation)
2. Player SDK: add null checks on all array accesses
3. Graceful error handling: catch exception, show error message instead of crash

**Recovery**: Push SDK update with null check fix. Users get auto-update.

---

## Scenario 3: Search Results Stale Due to Elasticsearch Indexing Lag

New content published and indexed into Elasticsearch, but reindex takes 30 minutes. Search returns old results. Creator searches for their new content, doesn't find it (though it's available for playback).

**Failure Mode**: Content status changed to "published" in MySQL, but Elasticsearch index not updated yet. Search index lag.

**Symptoms**: Content playable in catalog, but search doesn't return it. Creator confused.

**Detection**: Monitor MySQL→Elasticsearch sync lag. Alert if >5 minutes.

**Mitigation**:
1. Write-through caching: update Elasticsearch immediately on publish
2. Dual-write: write to both MySQL and Elasticsearch simultaneously
3. Search fallback: if ES lag >5 min, query MySQL directly for recent content
4. TTL-based cache invalidation: search results cached client-side for 1 minute

**Recovery**: Reindex completes, search returns fresh results.

---

## Scenario 4: Playlist Race Condition During Rapid Track Switching

Viewer rapidly clicks between videos in playlist (next/prev button spam). App makes concurrent requests for new playback token for each video. Race condition: which token is used? Results in undefined behavior (sometimes plays wrong video).

**Failure Mode**: Race condition in player state management. Last request wins, but may not be the final user intent.

**Symptoms**: Playback video doesn't match what user clicked. Confusing UX.

**Detection**: Log playback requests and actual playback. Alert if mismatch rate >0.1%.

**Mitigation**:
1. Implement request cancellation: cancel in-flight requests when new request issued
2. Use request ID to track latest intent
3. Serialize requests: queue them, process one at a time
4. UI debounce: ignore clicks for 500ms after last click

---

## Scenario 5: Recommendation Engine Timeout Affecting UI Render

Homepage shows recommendations powered by ML model. Model takes >5 seconds to compute (high latency). Entire homepage blocks waiting for recommendations (synchronous blocking call).

**Failure Mode**: Recommendation request is synchronous. Timeout blocks entire page load. User sees blank screen for 5+ seconds.

**Symptoms**: Homepage load time >5 seconds. Users see white screen.

**Detection**: Monitor page load time. Alert if >3 seconds (target <1.5s).

**Mitigation**:
1. Make recommendations async: start request, render without waiting
2. Return "loading" skeleton UI while recommendations load
3. Cache recommendations: serve cached recs while fetching fresh
4. Timeout: after 3 seconds, show default recommendations (trending, new)

**Recovery**: Recommendations load after page is already visible.

---

(Continuing with remaining edge case files for the platforms...)
