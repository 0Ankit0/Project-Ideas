# API and UI Edge Cases — Real Estate Management System

## Overview

Real estate platforms face a distinctive combination of high-stakes transactional workflows — lease signing, rent payment, tenant screening — and periods of intense, spiky traffic driven by market seasonality. The spring buying season (March through June in North American markets) routinely drives 3–5× baseline traffic to property search APIs as buyers accelerate their searches. At the same time, the platform must handle the precision requirements of legal document workflows, the latency constraints of map-dependent search UX, and the reliability requirements of payment confirmations that tenants and landlords depend on.

The edge cases documented here address scenarios where the API or UI layer fails in ways that are disproportionately damaging: not just degraded performance, but broken lease workflows, lost payment confirmations, or tenant screening processes that leave rental applications in limbo. Each scenario includes detection signals that allow the engineering team to distinguish between planned load and unexpected failure, and mitigation strategies that preserve the most critical user journeys even when non-critical services are degraded.

---

### Property Search API Latency Spike During Peak Season

**Failure Mode**

The property search API, which queries an Elasticsearch cluster to power the primary property browsing experience, experiences sustained response time degradation during peak spring market traffic. The failure manifests as P95 response times rising from a baseline of 120ms to 4,000ms or higher, with intermittent 503 responses as connection pools saturate. The root causes are compounding: Elasticsearch query complexity increases as users apply more filters (price range + bedroom count + school district + walk score), JVM heap pressure builds on Elasticsearch nodes under sustained concurrent query load, and the API gateway's upstream timeout is shorter than the degraded query time — causing the gateway to return 504s before Elasticsearch can respond. Simultaneously, the backend connection pool to Elasticsearch may be misconfigured for peak concurrency, with a pool size optimized for average load rather than peak.

**Impact**

Property search is the entry point for every user journey on the platform. A degraded search API directly impacts: new user acquisition (users who experience slow search abandon and use competing platforms), time-on-site metrics that affect SEO ranking, and the platform's reputation among agents who are showing properties in real time. For a platform monetizing through lead generation or subscription listings, a 4-second search response time drives measurable revenue loss — A/B test data from e-commerce consistently shows >40% abandonment at 3-second load times. For the spring selling season that drives 40% of annual transaction volume, a multi-day search performance incident can cause irreversible business harm.

**Detection**

Instrument the search API with latency percentile tracking (P50, P95, P99) using a time-series metrics system (Prometheus/Grafana or Datadog). Alert when P95 exceeds 500ms for more than 2 consecutive minutes — this is early-warning before user-visible degradation becomes severe. Monitor Elasticsearch cluster health: heap utilization, JVM garbage collection frequency and pause duration, query queue depth, and thread pool rejection count. Set an Elasticsearch-specific alert when the search thread pool rejection count is non-zero — this directly precedes 503 errors at the API layer. Track the ratio of search requests served from cache versus Elasticsearch; a cache hit ratio drop below 40% indicates cache warming has not kept up with query variety, increasing Elasticsearch load.

**Mitigation**

Implement query result caching at the API layer using Redis with a 60-second TTL for popular search combinations (e.g., "3-bedroom, San Francisco, under $2M" returning the same top-20 results for 60 seconds across all users submitting that query). Pre-warm the cache with the top-100 most-common query parameter combinations during off-peak hours before the business day begins. Implement circuit breakers in the search API: if Elasticsearch P95 exceeds 3 seconds, return cached stale results (up to 5 minutes old) rather than waiting for fresh queries, with a UI indicator that results may be slightly out of date. Autoscale Elasticsearch data nodes based on CPU and heap metrics, with a scale-out warm-up buffer — add nodes proactively at 60% heap, not reactively at 90%.

**Recovery**

During an active latency spike: (1) Enable the stale cache fallback immediately to stop user-visible degradation while Elasticsearch recovers. (2) Reduce Elasticsearch query complexity by temporarily disabling expensive aggregations (facet counts for filter options) that are not critical to core search results. (3) If heap pressure is the root cause, trigger a rolling restart of Elasticsearch nodes to clear heap fragmentation — in an active incident this is a last resort but prevents OOM crashes. (4) After the incident: conduct a query profiling session on the slowest queries identified during the incident, using Elasticsearch's Profile API, to identify specific query structures that can be rewritten or offloaded to pre-aggregated indexes. (5) Increase the connection pool size and autoscale thresholds based on the peak concurrency observed during the incident. (6) Build a load test that simulates spring market traffic patterns and run it quarterly to catch regressions before the peak season arrives.

---

### Map Tile Loading Failures Breaking Property Search UX

**Failure Mode**

The property search map view depends on a third-party map tile provider (Mapbox, Google Maps, or similar) to render the base map over which property pins are overlaid. Map tile loading failure occurs when: the tile provider's CDN experiences an outage or regional edge node failure, the API key embedded in the frontend application exceeds its daily tile request quota, the tile provider changes their tile URL schema in a breaking way, or CORS policy changes at the provider level cause tile requests to be blocked by the browser. The UI failure mode is the map rendering as a gray or blank canvas with property pins floating on an empty background — making it impossible for users to understand the geographic context of listings. In some cases, the map container crashes entirely, removing property pins from view as well.

**Impact**

For users browsing properties geographically — which represents the primary search mode for buyers evaluating neighborhoods — a blank map is equivalent to a broken search experience. Users cannot assess proximity to schools, transit, or amenities; cannot draw custom search area polygons; and cannot compare the relative locations of multiple listings. Bounce rates increase significantly when the map fails. For listings agents who pay for featured placement that includes map highlighting, a map outage means their paid placement is not rendering correctly — creating both user experience and contractual issues. The mobile experience, which typically defaults to map view rather than list view, is disproportionately affected.

**Detection**

Implement synthetic monitoring that loads the property search map view in a headless browser every 60 seconds and measures: (1) time to first tile render, (2) percentage of tile requests that return 200 vs. error responses, and (3) whether property pins are visible on the rendered map. Alert if tile error rate exceeds 5% or if the synthetic check fails to render property pins. Monitor the map tile provider's status page via RSS feed or status page API and alert when the provider posts an incident. Track tile quota consumption daily against the account limit; alert at 70% consumption so that the quota can be increased before exhaustion. Monitor browser console error rates in production via a real user monitoring (RUM) tool — a spike in tile-related JavaScript errors indicates a client-side map failure.

**Mitigation**

Configure the map component to support multiple tile provider backends with automatic failover: primary Mapbox, secondary OpenStreetMap tiles (via a self-hosted or commercial OSM tile server), tertiary a simplified vector tile renderer that can operate from cached tiles. Implement tile-level caching in the service worker (for PWA deployments) or in a tile proxy server, so that tiles for commonly viewed geographic areas (major metropolitan markets) are served from cache during provider outages. Design the map component with a graceful degradation mode: if tile loading fails, display a placeholder map with geographic labels and coastline/boundary outlines from a lightweight static dataset, ensuring property pins remain visible even without a full tile background. Monitor and proactively increase API key quota limits before peak season.

**Recovery**

During a tile provider outage: (1) Activate the OSM tile fallback in the feature flag system, which switches the tile URL base in the frontend configuration without requiring a code deployment. (2) Communicate to listing agents via in-app notification that the map is operating in reduced-quality mode using OpenStreetMap tiles. (3) Monitor the provider's status page for recovery and switch back to the primary provider once they confirm the incident is resolved, after validating with the synthetic monitor. (4) For quota exhaustion outages: immediately contact the provider to arrange an emergency quota increase (most providers accommodate this with a payment authorization); implement request deduplication to reduce tile requests for users panning the same area repeatedly. (5) Conduct a quarterly map tile quota forecast based on traffic growth projections and adjust the account tier proactively.

---

### Document Upload Exceeding Size Limits During Lease Signing

**Failure Mode**

The lease signing workflow requires tenants and landlords to upload supporting documents: government-issued ID, proof of income (bank statements, pay stubs), the executed lease PDF, and supplemental addenda. Document upload failure occurs when: a user attempts to upload a file that exceeds the configured maximum size limit (e.g., a multi-month bank statement PDF exported with embedded images that exceeds a 10MB limit), the upload endpoint returns an error after receiving the full file (wasting bandwidth), the frontend does not validate file size client-side before upload begins (causing a frustrating 100% → error UX), or the file storage backend (S3 or equivalent) has a presigned URL that has expired by the time the user completes the upload workflow and submits. For lease documents specifically, the signed PDF may be generated by an e-signature provider (DocuSign, HelloSign) and may be larger than anticipated due to digital signature metadata and certificate chains embedded in the PDF.

**Impact**

A document upload failure at a critical point in the lease signing workflow — after the tenant has completed all other steps — creates immediate friction that may cause lease abandonment. For competitive rental markets where a prospective tenant is applying to multiple units simultaneously, a failed upload experience may cause them to complete the application on a competing platform. For the landlord, a stalled lease workflow delays the rental income start date. For the platform, an incomplete lease record without uploaded documents may be legally invalid in jurisdictions that require specific disclosures to be in the lease file. If the e-signature provider's signed PDF is rejected by the upload system, the entire e-signature ceremony may need to be repeated — a significant inconvenience to both parties.

**Detection**

Monitor document upload error rates by error type (size exceeded, timeout, format rejected, storage error) using the application metrics pipeline. Set a baseline of acceptable upload error rates based on historical data and alert when the error rate for size-exceeded errors spikes — this may indicate that a document type being uploaded has become larger than anticipated (e.g., new e-signature provider generating larger PDFs). Track upload completion rates by document type and workflow step; a significant drop in completion rate for a specific document type (e.g., lease PDF uploads) indicates a systemic issue with that document category. Instrument the frontend to report client-side validation events separately from server-side rejections to understand where in the user journey failures are occurring.

**Mitigation**

Implement client-side file size validation before the upload begins — display a clear error message specifying the maximum allowed size before any data is transmitted. Set the server-side limit generously relative to typical document sizes (50MB for documents, not 10MB) while applying the stricter limit only to types where large files indicate user error (profile photos). For lease PDFs from e-signature providers, implement server-side PDF optimization (using a PDF compression library) as a post-processing step that reduces file size before storage without affecting the legal validity of the signed document. Use multi-part upload with progress tracking so that large files do not time out. Generate presigned upload URLs with a TTL of at least 30 minutes and implement URL refresh logic in the frontend that requests a new presigned URL if the existing one is within 5 minutes of expiry.

**Recovery**

When a user reports or the system detects a document upload failure during lease signing: (1) Preserve the workflow state — do not require the user to restart the entire lease signing process; resume from the document upload step. (2) If the failure was due to a size limit, provide the user with clear instructions for reducing file size (e.g., "Export your bank statement as a smaller PDF" or "Use the scanner's PDF mode instead of image mode"). (3) For e-signature provider PDFs that exceed size limits, trigger the server-side PDF optimization pipeline and retry the storage upload automatically. (4) If the presigned URL expired, generate a new one automatically and present the user with a "Resume Upload" button rather than asking them to restart. (5) For persistent upload failures that cannot be resolved automatically, route the user to a document submission assistance flow where a platform support agent can accept the document via an alternative channel and attach it to the lease record manually.

---

### Payment Gateway Webhook Delivery Failure Causing Rent Confirmation Loss

**Failure Mode**

Rent payment confirmation in the property management workflow depends on webhooks delivered by the payment gateway (Stripe, Dwolla, or similar ACH processor) to notify the platform of payment success, failure, or pending ACH settlement. Webhook delivery failure occurs when: the platform's webhook endpoint is unavailable at the time of delivery (deployment in progress, server restart), the webhook fails signature verification due to key rotation timing, the platform returns a non-2xx response causing the gateway to retry with exponential backoff (creating a delivery delay of hours), or the webhook processing job crashes after recording receipt but before committing the database transaction, leaving the gateway in a state where it believes the webhook was delivered but the platform has no record. The last scenario — silent loss — is the most dangerous: no retry is triggered because the gateway received a 200 OK, but the tenant's payment is not reflected in the platform.

**Impact**

A missing payment confirmation causes: the tenant's ledger to show rent as unpaid after they have successfully paid, late fee logic to potentially trigger incorrectly if the confirmation is not received before the grace period expires, automated late payment notices to be sent to tenants who have paid (damaging the landlord-tenant relationship), and the property manager's reconciliation report to show an outstanding balance. For automated lease renewal workflows that check for payment compliance, a lost webhook confirmation may incorrectly flag the tenant as non-compliant. If the confirmed payment is for a security deposit, missing confirmation may block move-in workflows.

**Detection**

Implement idempotent webhook processing with receipt logging: when a webhook arrives, log its ID, timestamp, and payload hash to a webhook receipt table before any processing begins, using a database insert that returns on duplicate key (webhook IDs are unique in all major gateway SDKs). After processing, mark the receipt as processed. A monitoring job should identify webhook receipts that have been in an unprocessed state for more than 5 minutes, which indicates the processing step failed after receipt. Additionally, implement a reconciliation job that compares the payment gateway's payment list (fetched via the gateway's list payments API) against the platform's payment ledger for the current and previous billing cycles, identifying any payment records in the gateway that have no corresponding confirmation in the platform.

**Mitigation**

Implement the transactional outbox pattern for webhook processing: upon receiving a webhook, write its payload to an outbox table within the same database transaction as the payment confirmation update. A separate outbox processor reads from the outbox table and applies the payment update to the main ledger; if the processor fails, the outbox entry remains and the processor retries on restart. This guarantees that a 200 OK is only returned to the gateway after the webhook payload is durably stored — even if the processing step has not yet completed, the data is not lost. Configure the platform's webhook endpoint with a strict 30-second response SLA and process webhooks asynchronously: receive, durably store, return 200 immediately, process in background. Configure a retry budget in the webhook processor for transient failures.

**Recovery**

When payment confirmation loss is detected (via reconciliation job or tenant complaint): (1) Query the gateway's payment list API to retrieve the full payment record for the affected transaction, including payment method, amount, timestamp, and settlement status. (2) Apply the payment confirmation to the tenant ledger manually via an administrative correction, logging the correction with the gateway payment ID as the reference. (3) If a late fee was assessed as a result of the missing confirmation, reverse the fee and notify the tenant with an apology. (4) If a late payment notice was sent, send a corrective notice confirming that payment was received and the account is current. (5) For the webhook delivery failure root cause: review the webhook endpoint availability logs for the delivery window and identify whether the failure was due to a deployment, crash, or network issue. (6) Run the reconciliation job in retrospective mode for the previous 30 days to identify any additional undetected mismatches.

---

### Background Check API Timeout During Tenant Screening

**Failure Mode**

Tenant screening workflows call a background check provider (TransUnion SmartMove, Checkr, or similar FCRA-compliant service) to retrieve credit reports, criminal history, and eviction records. API timeout failure occurs when the background check provider's API response time exceeds the platform's configured timeout (typically 30 seconds for synchronous calls), the provider returns a partial result that is missing one of the three components (credit, criminal, eviction), the provider's async callback webhook is delayed beyond the expected turnaround window (typically 15 minutes for instant checks), or a rate limit is hit when multiple tenant applications are processed simultaneously for a popular listing. The failure mode is compounded when the platform does not distinguish between a permanent failure (provider error) and a transient failure (timeout that should be retried), and surfaces the same "screening failed" message to the landlord regardless of cause.

**Impact**

A background check timeout leaves the tenant application in limbo: the landlord cannot approve or reject the tenant without the screening result, creating a frustrating experience for both parties. In a competitive rental market, a 24-hour delay in screening results may cause a well-qualified tenant to accept a competing unit. For the platform, the inability to complete screening represents a lost transaction fee if screening is a paid service. From an FCRA compliance perspective, the platform must handle screening results with care — a timeout must not result in an adverse action being taken against the applicant based on a missing result that may simply be delayed.

**Detection**

Instrument the background check API client with latency tracking and error categorization. Monitor the distribution of response times for background check requests; alert when P95 response time exceeds 20 seconds (pre-timeout warning). Track the rate of timeout errors, partial result returns, and provider error responses separately in the metrics pipeline — a spike in timeouts from a specific provider indicates provider-side instability. Monitor the webhook delivery rate for async background check callbacks; if the callback rate drops significantly below the request rate, callbacks are being lost or the provider's async pipeline is backed up.

**Mitigation**

Implement a fully asynchronous screening workflow: submit the background check request to the provider, return a "screening in progress" status to the landlord, and await the provider's async callback webhook rather than polling. This eliminates synchronous timeout failures entirely. Implement retry logic with exponential backoff for transient API errors (5xx responses, connection timeouts), with a maximum of 3 retries over 15 minutes before escalating to a manual review queue. If the primary provider times out, fall back to a secondary FCRA-compliant provider for the credit component while the primary recovers. Cache provider status (known outage / degraded) using the provider's status page API and surface this to landlords in the UI: "Background check provider is experiencing delays; results may take up to 2 hours."

**Recovery**

When a background check API timeout or failure is detected: (1) Do not surface a "screening failed" error to the landlord — instead, show a "screening in progress, estimated completion: X" status with a specific timeframe. (2) Trigger the retry pipeline automatically for recoverable failures. (3) If the provider confirms a full outage, notify affected landlords that results are delayed with an estimated recovery time. (4) Once results are received (via retry or delayed callback), notify the landlord immediately via email and in-app notification. (5) For applications that were waiting beyond the provider's stated SLA, review whether any FCRA adverse action timing obligations have been triggered and consult legal counsel if a landlord has made a tentative decision based on incomplete data. (6) Ensure the platform's audit log records the full timeline of the background check request and result receipt for FCRA compliance documentation.

---

### Elasticsearch Reindex Blocking Property Search

**Failure Mode**

Elasticsearch reindexing — required when adding new property fields, changing analyzer configurations, or migrating to a new index structure — is a resource-intensive operation that, if performed against the live index without proper management, can degrade or block property search queries. The failure mode occurs when: a reindex operation is initiated during business hours without a maintenance window, the reindex consumes all available Elasticsearch node resources (CPU, I/O, network), queries competing with the reindex fail with search thread pool rejections, or a reindex that was expected to complete in 2 hours takes 12 hours due to a larger-than-expected document count or slow source indexing rate. Additionally, if the reindex target alias cutover is performed before the new index is fully built, users briefly receive an empty search result set.

**Impact**

Property search unavailability or severe degradation during a reindex event directly impacts all user-facing search functionality. For a platform with active listings agents running open house campaigns that drive peak traffic to search, a reindex-induced outage timed to a busy weekend causes immediate revenue impact. The empty result set scenario — where the alias cutover occurs before the new index is ready — is particularly damaging because users see a blank search result page that looks like a bug, not a planned maintenance event. From an operational standpoint, a 12-hour reindex blocks any subsequent index structure changes, creating a queue of delayed improvements.

**Detection**

Monitor Elasticsearch reindex task progress via the Tasks API, tracking documents per second throughput, estimated completion time, and resource utilization. Alert when reindex throughput drops significantly below baseline (indicating resource contention), when estimated completion time exceeds the planned maintenance window, or when the reindex is running during business hours without a scheduled maintenance window in the change management calendar. Track the index alias state in the monitoring dashboard to ensure it always points to a valid, fully-built index.

**Mitigation**

Use the Elasticsearch blue-green index strategy: maintain a blue (live) index and build the new structure as a green (shadow) index. Write operations are mirrored to both indexes during the transition; read operations remain on the blue index until the green index is fully built and validated. The alias cutover is performed atomically using the Elasticsearch aliases API, which provides a zero-downtime switch with no intermediate state where the alias points to an empty or partial index. Throttle reindex operations using the `max_docs_per_second` parameter to limit the resource impact on query performance. Schedule reindexes during off-peak hours (2–6 AM local time) and implement an automatic abort if the estimated completion time will extend into business hours.

**Recovery**

If a reindex causes search degradation: (1) Immediately throttle the reindex operation to its minimum rate to free resources for search queries. (2) If search thread pool rejections are occurring, pause the reindex entirely and allow the queue to drain before resuming at a lower throttle rate. (3) If the alias was prematurely cut over to an incomplete index, immediately switch the alias back to the previous (blue) index — this is the primary reason blue-green reindex strategy maintains both indexes until cutover validation is complete. (4) After the incident, schedule the reindex completion for the next available off-peak window. (5) Implement reindex progress notifications to the engineering team at 25%, 50%, and 75% completion, with automatic abort and alert if the 75% mark is not reached within the planned window. (6) Document the performance impact observed at each throttle level so that future reindexes can be throttled appropriately from the start.

---

### Mobile App Offline Mode for Property Viewing

**Failure Mode**

Real estate platform mobile apps are frequently used in environments with intermittent or absent connectivity: walking through properties in buildings with poor cellular reception, traveling between showings, or in rural markets where data coverage is sparse. Offline mode failure occurs when: the app has not pre-cached any property data and encounters offline state unexpectedly, showing a generic network error rather than previously viewed listings; cached data is present but the UI does not correctly identify which properties are available offline versus which require connectivity; a user attempts to complete a contact-agent form or save a favorite property while offline, and the form submission is silently dropped rather than queued for submission when connectivity is restored; or the offline cache becomes stale (properties that are under contract or sold still show as available in the cached view).

**Impact**

An agent showing a property to a buyer who then opens the platform app in the building and sees a blank screen or a generic error — rather than the property details, photos, and disclosure documents — creates a poor impression at a critical moment in the purchase decision. If a buyer attempts to submit an offer inquiry while offline and the submission is silently dropped, a motivated buyer may lose a time-sensitive opportunity. Stale cached data showing a sold or contracted property as available can create confusion during showings and damage the platform's credibility with agents and buyers.

**Detection**

Monitor offline interaction events from mobile clients via the analytics pipeline: track what actions users attempt while offline (form submissions, saves, map interactions) and what the app does with those actions (queued, dropped, error). A high rate of dropped offline actions indicates that the queuing mechanism is not working. Track the staleness of cached property data: record the last-sync timestamp for each property in the local cache and surface a staleness warning in the UI when cached data is older than 24 hours. Monitor crash rates and error rates on the network layer of the mobile app, segmented by device connectivity type (offline, 3G, LTE) to identify connectivity-related failure patterns.

**Mitigation**

Implement a service worker (for PWA) or offline-first data layer (for native app using SQLite or Realm) that: (1) caches property detail pages, photos (at reduced resolution), and disclosure documents for all properties the user has recently viewed or favorited; (2) queues form submissions (contact agent, schedule showing, save favorite) in a local action queue that is flushed when connectivity is restored; (3) clearly marks cached content with its age and whether it reflects the current live status; (4) performs background sync of listing status (available, pending, sold) for cached properties every 30 minutes when connectivity is available, so stale availability data is promptly corrected. Design the UI to proactively inform the user of offline mode with a visible banner and to clearly distinguish interactive features that require connectivity from those available offline.

**Recovery**

When the app transitions from offline to online: (1) Flush the queued action queue in order, submitting all pending form actions to the server and displaying confirmation for each successful submission. (2) For queued actions that fail on submission (e.g., a property contact form for a listing that was removed while offline), notify the user specifically about the failure with context ("This property is no longer available; your message was not delivered"). (3) Refresh the listing status for all cached properties to clear any stale availability indicators. (4) If the user's session expired during the offline period, prompt for re-authentication before flushing the action queue, preserving the queued actions through the re-auth flow. (5) For users who rely heavily on offline mode (agents showing multiple properties per day), provide an explicit "Download for offline" feature that pre-caches all photos and documents for a showing list at full resolution while on Wi-Fi.
