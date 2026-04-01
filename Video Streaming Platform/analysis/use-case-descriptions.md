# Use Case Descriptions — Video Streaming Platform

## Overview

This document provides detailed, production-level use case specifications for the ten most critical use cases of the Video Streaming Platform. Each specification follows a structured template that captures preconditions, post-conditions, primary success scenarios, alternative flows, exception flows, referenced business rules, and non-functional requirements.

The use cases are ordered from content ingest through playback to rights enforcement and offline access — reflecting the full lifecycle of a piece of content on the platform.

---

## UC-001: Upload Video Content

**Use Case ID:** UC-001
**Use Case Name:** Upload Video Content
**Version:** 1.3
**Status:** Approved

### Actor(s)
- **Primary:** Content Creator
- **Secondary:** Content ID System (external), Upload Service (internal), Storage Service (S3-compatible)

### Description
A Content Creator uploads a raw video file to the platform. The system validates the file, performs a chunked multipart upload to durable object storage, triggers a Content ID fingerprint scan to detect copyright violations, and enqueues the file for transcoding. The Creator receives real-time progress feedback and a notification when the pipeline is complete.

### Preconditions
1. The Creator has an active, verified account with Creator privileges.
2. The Creator's account is not suspended or under a DMCA strike that blocks uploads.
3. The Creator has not exceeded their monthly storage quota.
4. The client device has a network connection with at least 1 Mbps upload bandwidth.

### Postconditions
**On Success:**
1. The raw video file is stored durably in S3 with versioning enabled.
2. A content record exists in the Content Database with status `PENDING_TRANSCODE`.
3. A transcoding job has been enqueued in the job queue.
4. The Content ID fingerprint scan has been initiated.
5. The Creator receives a push notification and email confirming the upload.

**On Failure:**
1. Any partially uploaded chunks are deleted from staging storage.
2. No content record is created (or any partial record is marked `FAILED` and cleaned up by a background job within 24 hours).
3. The Creator receives an error notification with a descriptive failure reason.

### Main Success Scenario
1. Creator navigates to the Creator Studio upload page and clicks "Upload Video".
2. Creator selects a local video file (MP4, MOV, MKV, AVI, or WebM) via the file picker or drag-and-drop interface.
3. Client-side JavaScript computes the file's SHA-256 hash and sends an **Upload Initiation** request to the Upload Service API: `POST /v1/uploads` with `{filename, size_bytes, sha256, content_type}`.
4. Upload Service checks the Creator's storage quota. If the upload would exceed the quota, it returns HTTP 422 with `QUOTA_EXCEEDED`.
5. Upload Service checks the Creator's account standing (no active ban or upload-blocking strike). If blocked, returns HTTP 403 with `ACCOUNT_RESTRICTED`.
6. Upload Service creates an upload session record in its database with status `INITIATED` and returns a presigned multipart upload URL set (one URL per 100 MB chunk) along with an `upload_id`.
7. Client splits the file into chunks of up to 100 MB and uploads each chunk in parallel (up to 4 concurrent requests) via HTTP PUT to the presigned S3 URLs.
8. For each chunk, the client records the returned `ETag` header.
9. After all chunks are uploaded, the client sends a **Complete Multipart Upload** request to the Upload Service: `POST /v1/uploads/{upload_id}/complete` with the ordered list of `{part_number, etag}` pairs.
10. Upload Service calls S3 `CompleteMultipartUpload` API. S3 assembles the chunks and verifies the total object integrity.
11. Upload Service updates the upload session status to `STORED` and creates a content record in the Content Database with status `PENDING_SCAN`.
12. Upload Service publishes a `ContentUploaded` event to the event bus (Kafka topic `content.uploaded`) containing `{content_id, creator_id, s3_key, file_size, sha256}`.
13. Content ID Service consumes the event and initiates an asynchronous fingerprint scan against the Content ID reference database.
14. Transcoding Orchestrator also consumes the `ContentUploaded` event and creates a transcoding job record with status `QUEUED`.
15. Upload Service returns HTTP 201 to the Creator's client with `{content_id, status: "PENDING_SCAN"}`.
16. Creator Studio UI polls `GET /v1/content/{content_id}/status` every 5 seconds to display progress.
17. Content ID Service completes the scan (typically within 60 seconds for files under 2 GB).
18. If no copyright match is found, Content ID Service publishes a `ContentIDCleared` event; the content record status advances to `PENDING_TRANSCODE`.
19. Transcoding Service picks up the job from the queue and begins processing (see UC-002).
20. On transcoding completion, a `TranscodingComplete` event is published.
21. Notification Service consumes the event and sends the Creator a push notification and email: "Your video '[title]' is ready to publish."

### Alternative Flows

**AF-01: Duplicate Upload Detection**
At step 3, if the SHA-256 hash matches an existing content record owned by the same Creator, the Upload Service returns HTTP 200 with the existing `content_id` and status, skipping the re-upload. The Creator is informed that the content already exists.

**AF-02: Upload Resumption**
If the network is interrupted during step 7, the client can resume by calling `GET /v1/uploads/{upload_id}` to retrieve the list of already-completed parts. The client re-uploads only the missing chunks.

**AF-03: Content ID Match Found**
At step 17, if a copyright match is identified at 80%+ confidence, the Content ID Service publishes a `ContentIDFlagged` event. The content record status changes to `BLOCKED_COPYRIGHT`. The Creator receives a notification explaining which reference asset matched. The video cannot be published until the Creator disputes the claim or the rights holder approves a monetisation split.

### Exception Flows

**EF-01: File Format Rejected**
At step 2, if the client selects an unsupported format (e.g., `.wmv`, `.flv` over 10 GB), the client-side validator rejects it immediately with a user-facing error. No request is sent to the server.

**EF-02: S3 Multipart Assembly Failure**
At step 10, if S3 returns an error (e.g., missing part, ETag mismatch), the Upload Service aborts the multipart upload, deletes staging chunks, marks the upload record `FAILED`, and returns HTTP 500 with `STORAGE_ASSEMBLY_ERROR`. The Creator is prompted to retry.

**EF-03: Upload Session Expiry**
Presigned upload URLs expire after 12 hours. If the Creator attempts to upload a chunk after expiry, the chunk PUT request returns HTTP 403 from S3. The client receives this error, calls the Upload Service to refresh the upload session, and receives new presigned URLs for the remaining parts.

**EF-04: Service Unavailable**
If the Upload Service is unreachable, the client retries with exponential back-off (1s, 2s, 4s, up to 60s), then displays a connectivity error after 5 failures.

### Business Rules
- **BR-UPL-01:** Maximum file size is 500 GB per upload.
- **BR-UPL-02:** Maximum video duration is 12 hours.
- **BR-UPL-03:** Accepted codecs: H.264, H.265/HEVC, VP9, AV1, ProRes. Audio: AAC, MP3, AC3, FLAC.
- **BR-UPL-04:** Free Creator tier: 10 GB/month upload quota. Pro tier: 1 TB/month. Enterprise: unlimited.
- **BR-UPL-05:** Content ID scan must complete before transcoding begins; however, if the scan exceeds 30 minutes (large files), transcoding may proceed with the content held in `PENDING_REVIEW` state.
- **BR-UPL-06:** All upload sessions that remain in `INITIATED` status for more than 24 hours are automatically purged.

### Non-Functional Requirements
- **Performance:** Upload throughput must support at least 500 MB/s aggregate ingress across the platform. Individual presigned URLs must be generated within 200 ms p99.
- **Reliability:** Multipart upload must tolerate individual part failure with retry. Data must not be lost once `CompleteMultipartUpload` returns success.
- **Security:** Presigned URLs must be scoped to the specific `upload_id` and expire in 12 hours. S3 objects are stored with server-side AES-256 encryption.
- **Scalability:** The upload service must scale horizontally to handle 10,000 concurrent upload sessions.

---

## UC-002: Transcode Content to Multi-Bitrate

**Use Case ID:** UC-002
**Use Case Name:** Transcode Content to Multi-Bitrate
**Version:** 1.1
**Status:** Approved

### Actor(s)
- **Primary:** Transcoding Orchestrator (system-initiated)
- **Secondary:** Content Creator (monitors progress), FFmpeg Workers, Storage Service

### Description
Following a successful upload and Content ID clearance, the Transcoding Orchestrator retrieves the raw video from S3, distributes encoding jobs across a pool of FFmpeg worker nodes to produce six adaptive bitrate (ABR) renditions, packages the output into HLS and MPEG-DASH formats, extracts representative thumbnails, processes embedded subtitle tracks, encrypts segments with DRM-compatible keys, and stores all artefacts back to S3 before pushing to CDN origin.

### Preconditions
1. A `ContentUploaded` or `ContentIDCleared` event exists on the `content.transcoding` Kafka topic for the content item.
2. The raw file is present in S3 at the expected key.
3. FFmpeg worker capacity is available (at least one worker has headroom).

### Postconditions
**On Success:**
1. Six video rendition directories exist in S3: `240p`, `360p`, `480p`, `720p`, `1080p`, `4K` (if source resolution permits).
2. A master HLS playlist (`master.m3u8`) and a DASH manifest (`manifest.mpd`) are stored in S3.
3. At least 10 thumbnails are stored as JPEG files in the `thumbnails/` prefix.
4. Subtitle `.vtt` files are stored per language track in the `subtitles/` prefix.
5. All `.ts` / `.m4s` segments are encrypted with CBCS (Common Encryption) keys.
6. Content keys are registered in the DRM key management system.
7. Content record status is updated to `TRANSCODED`.
8. CDN is instructed to pre-warm the master manifest at key edge nodes.

### Main Success Scenario
1. Transcoding Orchestrator dequeues the next available job from the `transcoding.jobs` queue (priority-ordered by Creator tier).
2. Orchestrator fetches the raw file metadata from the Content Database: codec, resolution, duration, frame rate, HDR flag.
3. Orchestrator generates a transcoding plan: which renditions apply (e.g., source is 1080p → produce 240p, 360p, 480p, 720p, 1080p; skip 4K).
4. Orchestrator creates one child job per rendition and pushes all six to the `transcoding.renditions` queue simultaneously.
5. Each FFmpeg worker picks up a rendition job, downloads the raw file from S3 (using S3 Select for segment pre-fetching where beneficial), and executes the FFmpeg transcoding command with the target profile parameters.
6. Rendition profiles:
   - **240p:** 426×240, H.264 Baseline, 400 kbps video, 64 kbps AAC
   - **360p:** 640×360, H.264 Main, 800 kbps video, 96 kbps AAC
   - **480p:** 854×480, H.264 Main, 1400 kbps video, 128 kbps AAC
   - **720p:** 1280×720, H.264 High, 2800 kbps video, 192 kbps AAC
   - **1080p:** 1920×1080, H.264 High, 5000 kbps video, 192 kbps AAC
   - **4K:** 3840×2160, H.265/HEVC Main10, 16000 kbps video, 384 kbps AAC-LC
7. Each worker segments the output into 6-second `.ts` segments (HLS) and 4-second `.m4s` fragments (DASH) and uploads each segment/fragment to S3 as it is produced (streaming upload).
8. As each rendition completes, the worker reports completion to the Orchestrator by publishing to `transcoding.rendition.complete`.
9. In parallel with step 5–8, the Orchestrator dispatches a **Thumbnail Extraction** job: FFmpeg extracts frames at 10%, 20%, …, 90% of the video duration plus the first non-black frame, saving as JPEG at 1280×720.
10. In parallel, a **Subtitle Processing** job extracts embedded subtitle tracks (SRT, SSA, EIA-608) and converts them to WebVTT format. If no embedded subtitles exist, the job is skipped.
11. Once all rendition jobs complete, the Orchestrator generates the HLS master playlist (`master.m3u8`) referencing each rendition's variant playlist, and the MPEG-DASH manifest (`manifest.mpd`) referencing each representation.
12. Orchestrator invokes the **DRM Packaging** step: generates a unique Content Encryption Key (CEK) and Key ID (KID) pair, registers them in the Key Management Service, encrypts all segments using the CBCS scheme, and embeds DRM signalling (`#EXT-X-KEY` in HLS; `<ContentProtection>` in DASH manifest) pointing to the platform's Widevine, FairPlay, and PlayReady licence acquisition URLs.
13. Orchestrator pushes the master manifest, DASH manifest, and all encrypted segments to the CDN origin bucket.
14. Orchestrator sends a CDN cache pre-warm request for the master manifests at the top 10 PoP locations.
15. Orchestrator updates the content record status to `TRANSCODED` and emits a `TranscodingComplete` event.
16. Notification Service sends the Creator a completion email with a preview link.

### Alternative Flows

**AF-01: Source is Already H.264 at 1080p**
The Orchestrator detects the source matches the 1080p profile bitrate within 20%. It uses a `copy` codec passthrough for that rendition instead of re-encoding, saving CPU time and preserving source quality.

**AF-02: Rendition Worker Failure Mid-Job**
If a worker fails (OOM, crash) mid-transcoding, the Orchestrator detects the heartbeat timeout after 2 minutes, marks the rendition job `FAILED`, and re-queues it. Up to 3 retries are attempted before the entire transcoding job is marked `FAILED`.

**AF-03: 4K Source with HDR**
If the source file has HDR10 or Dolby Vision metadata, the Orchestrator produces an additional HDR 4K rendition using HEVC Main10 with preserved HDR10 metadata alongside a standard SDR 4K rendition.

### Exception Flows

**EF-01: Corrupt Source File**
At step 5, if FFmpeg reports the source file is unreadable or corrupt, the worker marks the job `FAILED_CORRUPT_SOURCE`. The Orchestrator notifies the Creator to re-upload the file.

**EF-02: Transcoding Timeout**
If a single rendition job exceeds 6 hours, the Orchestrator terminates the worker, marks the job timed-out, and alerts the on-call team via PagerDuty.

### Business Rules
- **BR-TRN-01:** 4K rendition is only produced if the source resolution is at least 3840×2160.
- **BR-TRN-02:** All segments must be encrypted; unencrypted segments must never reach the CDN.
- **BR-TRN-03:** Transcoding priority: Enterprise Creator > Pro Creator > Free Creator.
- **BR-TRN-04:** Maximum transcoding queue wait time SLA: 15 minutes for Pro/Enterprise, 4 hours for Free.

### Non-Functional Requirements
- **Performance:** A 60-minute 1080p source must transcode to all six renditions within 30 minutes.
- **Scalability:** The worker pool must auto-scale from 10 to 500 workers based on queue depth.
- **Cost:** Spot instances are preferred for workers; the system gracefully handles spot interruption by checkpointing segment progress.

---

## UC-003: Stream Video (VOD Playback)

**Use Case ID:** UC-003
**Use Case Name:** Stream Video (VOD Playback)
**Version:** 2.0
**Status:** Approved

### Actor(s)
- **Primary:** Viewer
- **Secondary:** CDN, DRM Provider, Analytics Service, Recommendation Engine

### Description
A Viewer selects a video to watch. The platform authenticates the viewer, verifies their subscription entitlement, generates a signed personalised playback manifest (with DRM signalling), and delivers video segments via CDN to the video player. The player performs ABR quality selection. Playback events are streamed to the Analytics Service. On completion, the Recommendation Engine presents the next video.

### Preconditions
1. Viewer has an authenticated session (valid JWT, not expired).
2. The requested content item has status `PUBLISHED`.
3. The content item has at least the 480p rendition available in S3.
4. CDN has edge-cached or can reach the origin for segments.

### Postconditions
**On Success:**
1. The viewer successfully watches the video.
2. A `WatchSession` record is created containing the viewer ID, content ID, start/end timestamps, quality levels observed, rebuffering events, and completion percentage.
3. The viewer's resume position is updated.
4. Analytics events are delivered to the Analytics Service.

### Main Success Scenario
1. Viewer clicks a video thumbnail on the catalog or search results page.
2. Client sends `GET /v1/content/{content_id}/playback` with the Bearer JWT in the Authorization header.
3. Playback Service validates the JWT (signature, expiry, not revoked).
4. Playback Service queries the Entitlement Service: `CanView(viewer_id, content_id)`. Entitlement Service checks: active subscription tier, content rating vs. viewer's parental control settings, geo-restriction rules (viewer's IP-to-country vs. content's allowed territories).
5. If entitlement is denied, Playback Service returns HTTP 403 with a structured error: `{error: "SUBSCRIPTION_REQUIRED", upgrade_url: "..."}`.
6. If entitlement passes, Playback Service fetches the content's `{s3_key_prefix, drm_kid, available_renditions}` from the Content Database.
7. Playback Service generates a **signed playback token**: a short-lived JWT (15-minute TTL) encoding `{viewer_id, content_id, allowed_max_quality, geo_allowed, session_id}`.
8. Playback Service queries the Concurrent Stream Enforcer: increments the viewer's active stream count. If count exceeds the plan limit, returns HTTP 429 with `CONCURRENT_STREAM_LIMIT`.
9. Playback Service generates a personalised HLS master manifest: filters renditions based on the viewer's plan (e.g., Basic plan gets up to 720p), signs each segment URL with HMAC-SHA256 using the playback token, and injects the DRM `EXT-X-KEY` tags with the licence URL bearing the playback token.
10. Playback Service returns HTTP 200 with `{manifest_url: "https://cdn.platform.com/signed/v/{content_id}/master.m3u8?token=..."}`.
11. Video player fetches the manifest from the CDN edge. The CDN validates the URL signature before serving.
12. Player evaluates available bandwidth and device capability (codec support, resolution cap), selects an initial rendition (typically the 480p variant for the first segment).
13. Player sends a DRM licence challenge to the platform's DRM proxy: `POST /v1/drm/license/{widevine|fairplay|playready}` with the challenge payload and playback token.
14. DRM Proxy validates the playback token, fetches the CEK for the `KID` from the Key Management Service, and forwards the request to the upstream DRM licence server (Widevine/FairPlay/PlayReady).
15. DRM licence server returns an encrypted licence. The proxy passes it back to the player.
16. Player decrypts and loads the licence into the Content Decryption Module (CDM). Decrypted playback begins.
17. Player fetches video segments from CDN. CDN validates each signed segment URL before delivery.
18. Player ABR algorithm continuously measures download throughput and buffer health. It switches renditions (up or down) approximately every 3 segments to maintain smooth playback.
19. Player emits analytics heartbeat events every 10 seconds to `POST /v1/analytics/events` with: `{session_id, timestamp, position_seconds, bitrate, buffer_level, cdn_pop, rebuffer_count, dropped_frames}`.
20. On video completion (or explicit close), player sends a `SessionEnd` event. Concurrent Stream Enforcer decrements the viewer's active stream count.
21. Player displays the end screen. Recommendation Engine returns the next 6 recommendations based on the viewing history and content metadata.

### Alternative Flows

**AF-01: Resume Playback**
At step 11, before fetching the first segment, the player calls `GET /v1/viewers/{viewer_id}/resume/{content_id}`. If a resume position exists (and is less than 95% through the video), the player seeks to that position automatically and begins buffering from that segment.

**AF-02: Viewer Selects Quality Manually**
At step 18, if the viewer uses the quality picker to force a specific resolution, the player overrides the ABR algorithm and locks to the chosen rendition until the viewer changes it or explicitly switches back to Auto mode.

**AF-03: DRM Licence Cached**
At step 13, if the player already holds a valid, unexpired DRM licence for this `KID`, it skips the licence acquisition request and proceeds directly to decryption.

### Exception Flows

**EF-01: CDN Segment Fetch Failure**
If a segment request to the CDN times out after 3 retries, the player logs an error event, attempts to switch to a lower-quality rendition (which may be served from a different CDN PoP), and continues buffering. If all renditions fail for 5 consecutive segments, the player displays an error UI.

**EF-02: DRM Licence Acquisition Failure**
If the DRM proxy returns a non-200 response (e.g., Widevine is temporarily unavailable), the player retries up to 3 times with exponential back-off. If all retries fail, playback is blocked with error `DRM_LICENSE_UNAVAILABLE`.

**EF-03: Session Token Expiry During Playback**
The 15-minute playback token will expire during a normal viewing session. At step 17, when a signed segment URL is rejected (HTTP 403), the player silently refreshes the playback token by calling `POST /v1/content/{content_id}/playback/refresh` with the existing (expired) token. The server validates the viewer's entitlement again and issues a new token.

### Business Rules
- **BR-PLY-01:** Basic plan: max 720p, 1 concurrent stream, no offline download.
- **BR-PLY-02:** Standard plan: max 1080p, 2 concurrent streams, 2 offline downloads.
- **BR-PLY-03:** Premium plan: max 4K, 4 concurrent streams, unlimited offline downloads.
- **BR-PLY-04:** DRM licence duration: 48 hours for online playback, 30 days for offline.
- **BR-PLY-05:** Resume position is saved if the viewer has watched more than 30 seconds and less than 95% of the content.

### Non-Functional Requirements
- **Latency:** Time-to-first-frame (TTFF) must be under 2 seconds at p95 on a 10 Mbps connection.
- **Availability:** Playback Service must maintain 99.99% uptime; CDN provides the buffer against origin failures.
- **Throughput:** The platform must support 500,000 concurrent viewers.

---

## UC-004: Acquire DRM License

**Use Case ID:** UC-004
**Use Case Name:** Acquire DRM License
**Version:** 1.2
**Status:** Approved

### Actor(s)
- **Primary:** Viewer (indirectly via their video player / CDM)
- **Secondary:** DRM Proxy Service, Key Management Service, Widevine Licence Server, FairPlay Licence Server, PlayReady Licence Server

### Description
The video player's Content Decryption Module (CDM) sends a licence challenge to the platform's DRM proxy. The proxy authenticates the request, validates the viewer's current playback entitlement, fetches the Content Encryption Key from the Key Management Service, and relays the challenge to the appropriate upstream DRM licence server, returning the encrypted licence to the player.

### Preconditions
1. The viewer holds a valid, unexpired playback token for the content item.
2. The content item has an associated KID/CEK registered in the Key Management Service.
3. The CDM on the viewer's device supports the DRM system being requested (Widevine L1/L3, FairPlay, or PlayReady).

### Postconditions
**On Success:**
1. The player holds an encrypted DRM licence that permits decryption of the content's segments.
2. A licence issuance audit log entry is created.

### Main Success Scenario
1. Player encounters the `#EXT-X-KEY` or `<ContentProtection>` element in the manifest and generates a platform-specific licence challenge blob from the CDM.
2. Player sends `POST /v1/drm/license/{system}` where `{system}` is `widevine`, `fairplay`, or `playready`, with the `Authorization: Bearer {playback_token}` header and the raw binary challenge in the body.
3. DRM Proxy validates the playback token: signature, expiry, content ID match. Returns HTTP 401 if invalid.
4. DRM Proxy extracts the `viewer_id` and `content_id` from the token.
5. DRM Proxy checks the licence issuance rate limiter: max 10 licence requests per viewer per content per hour (prevents abuse).
6. DRM Proxy calls the Key Management Service: `GetContentKey(kid)` → returns `{cek, policy}`. The policy encodes: max resolution allowed (from the viewer's plan), rental expiry (if applicable), offline allowed flag.
7. DRM Proxy constructs the licence request to the upstream licence server, embedding the CEK and the policy.
8. DRM Proxy forwards the challenge + CEK + policy to the upstream DRM licence server over a mutually-authenticated TLS connection.
9. Upstream licence server generates the encrypted licence response.
10. DRM Proxy receives the licence response and passes it back to the player with HTTP 200.
11. DRM Proxy writes an audit log entry: `{viewer_id, content_id, kid, drm_system, timestamp, ip_address, device_fingerprint}`.
12. Player's CDM decrypts the licence using the device's hardware root of trust (for L1) or software CDM (for L3) and loads the content key into the decrypt pipeline.

### Alternative Flows

**AF-01: Offline Licence Request**
If the playback token carries the `offline: true` flag (set when the viewer initiated a download), the policy in step 6 sets `offline_expiry = now + 30 days` and `max_plays = -1`. The licence duration is extended accordingly.

### Exception Flows

**EF-01: KID Not Found**
At step 6, if the KID is not present in the Key Management Service (e.g., newly transcoded content whose keys have not yet been propagated), the DRM Proxy returns HTTP 404 with `KEYS_NOT_READY`. The player retries after 5 seconds up to 3 times.

**EF-02: Upstream DRM Server Unavailable**
At step 8, if the upstream licence server times out, the DRM Proxy retries on a standby licence server endpoint (all DRM providers expose primary + fallback endpoints). If both fail, HTTP 503 is returned to the player.

**EF-03: Policy Violation**
If the viewer's plan does not permit 4K but the content key policy is set for 4K, the proxy automatically downgrades the policy to 1080p before forwarding to the licence server.

### Business Rules
- **BR-DRM-01:** Licences for online streaming expire 48 hours after issuance.
- **BR-DRM-02:** Licences for offline downloads expire 30 days after issuance.
- **BR-DRM-03:** The platform must never log or expose the CEK in plain text; it is always wrapped by the upstream DRM server's public key.
- **BR-DRM-04:** Widevine L1 (hardware CDM) is required for 4K content. L3 software CDM is capped at 1080p.

### Non-Functional Requirements
- **Latency:** DRM proxy round-trip must complete in under 300 ms p95 (including the upstream licence server call).
- **Availability:** Key Management Service must be multi-region with 99.999% uptime.
- **Audit:** All licence issuance events must be retained for 7 years for rights-holder compliance.

---

## UC-005: Subscribe to Plan

**Use Case ID:** UC-005
**Use Case Name:** Subscribe to Plan
**Version:** 1.4
**Status:** Approved

### Actor(s)
- **Primary:** Viewer
- **Secondary:** Payment Gateway (Stripe), Entitlement Service, Notification Service

### Description
A Viewer selects a subscription plan (Basic, Standard, or Premium), provides payment details, and completes the transaction. The platform creates a Stripe Customer and Subscription, activates the viewer's entitlement, and sends a confirmation email. Subsequent renewals are handled automatically via Stripe webhooks.

### Preconditions
1. The Viewer has an authenticated account.
2. The Viewer does not already hold an active subscription at the chosen tier or higher.
3. The plan is currently available in the Viewer's country (geo-based pricing applies).

### Postconditions
**On Success:**
1. A Stripe Customer and Subscription record exist.
2. The Viewer's `subscription` record has status `ACTIVE` with the correct tier, current period start/end, and renewal date.
3. The Viewer can immediately access content permitted by the new tier.
4. A payment receipt email has been sent.

### Main Success Scenario
1. Viewer navigates to the subscription plans page.
2. Platform returns the available plans with localised pricing fetched from the Pricing Service.
3. Viewer selects a plan and clicks "Subscribe".
4. If no existing Stripe Customer exists for the Viewer, the platform calls Stripe `POST /v1/customers` to create one, storing the returned `customer_id`.
5. Client renders the Stripe Payment Element (hosted on Stripe's domain) for card input. The card number is tokenised client-side by Stripe.js — the raw PAN never touches platform servers.
6. Client submits the payment form. Stripe.js returns a `payment_method_id`.
7. Client sends `POST /v1/subscriptions` to the platform with `{plan_id, payment_method_id}`.
8. Platform Subscription Service calls Stripe `POST /v1/subscriptions` with `{customer_id, price_id, default_payment_method, trial_period_days (if applicable)}`.
9. Stripe charges the card for the first billing period.
10. Stripe returns subscription details including `{subscription_id, status: "active", current_period_end}`.
11. Platform creates a local subscription record: `{viewer_id, stripe_subscription_id, plan_tier, status: ACTIVE, renews_at}`.
12. Platform calls Entitlement Service `GrantEntitlement(viewer_id, plan_tier)` to update the viewer's access permissions.
13. Platform returns HTTP 201 to the client: `{subscription_id, plan_tier, renews_at}`.
14. Client redirects the Viewer to a success page.
15. Notification Service sends a payment receipt and welcome email.

### Alternative Flows

**AF-01: Trial Period**
If the chosen plan includes a 7-day free trial and the Viewer has never previously subscribed to any tier, step 9 does not charge the card. Stripe sets `trial_end = now + 7 days`. The Viewer has full access during the trial. At trial end, Stripe charges automatically and emits `invoice.paid`.

**AF-02: Upgrade from Existing Plan**
If the Viewer already has an active Basic subscription and selects Standard or Premium, the platform calls Stripe `POST /v1/subscriptions/{id}` with the new `price_id` and `proration_behavior: "create_prorations"`. The Viewer is charged the prorated difference immediately.

**AF-03: 3D Secure Challenge Required**
At step 9, if the card issuer requires 3D Secure authentication, Stripe returns a `payment_intent` with status `requires_action`. The client uses Stripe.js `handleCardAction()` to present the 3DS challenge to the Viewer. On success, the client reconfirms the payment intent.

### Exception Flows

**EF-01: Card Declined**
At step 9, Stripe returns a card decline code. The platform maps Stripe's decline codes to user-friendly messages and returns HTTP 402 to the client. The subscription record is not created. The Viewer is prompted to use a different payment method.

**EF-02: Stripe API Unavailable**
Platform retries the Stripe API call up to 3 times with 1-second delays. If all fail, the subscription attempt is marked `PENDING` and the Viewer is shown a message that the subscription is being processed.

### Business Rules
- **BR-SUB-01:** A Viewer may hold only one active subscription tier at any time.
- **BR-SUB-02:** Downgrades take effect at the end of the current billing period. Upgrades take effect immediately.
- **BR-SUB-03:** Refunds are only issued within 48 hours of initial subscription or renewal.
- **BR-SUB-04:** Subscription cancellation must be confirmed via a cancellation survey; immediate cancellation and retention offers apply.

### Non-Functional Requirements
- **PCI Compliance:** Platform must be PCI-DSS SAQ A compliant (no card data stored or processed on platform servers).
- **Performance:** Subscription creation must complete end-to-end within 5 seconds p95.

---

## UC-006: Start Live Stream

**Use Case ID:** UC-006
**Use Case Name:** Start Live Stream
**Version:** 1.0
**Status:** Approved

### Actor(s)
- **Primary:** Content Creator
- **Secondary:** Live Ingest Service, Transcoding Service, CDN, Chat Service

### Description
A Content Creator configures and initiates a live broadcast. The platform provisions a unique RTMP/SRT ingest endpoint, authenticates the incoming stream, runs live transcoding to produce LL-HLS and MPEG-DASH manifests, distributes via CDN, enables viewer access, and archives the stream for post-broadcast VOD availability.

### Preconditions
1. Creator has a verified account with Live Streaming capability enabled.
2. Creator has configured stream title, category, and thumbnail in Creator Studio.
3. Creator's streaming software (OBS, Streamlabs, hardware encoder) is configured with the ingest URL and stream key.

### Postconditions
**On Success:**
1. A live event record exists with status `LIVE`.
2. Viewers can access the live stream manifest URL.
3. DVR segments are being archived to S3 in near-real-time.
4. The stream appears in the Live section of the catalog.

### Main Success Scenario
1. Creator clicks "Go Live" in Creator Studio, triggering `POST /v1/live-events` with `{title, category, thumbnail_id, dvr_enabled, max_concurrent_viewers}`.
2. Live Event Service creates a live event record with a unique `stream_key` and `rtmp_ingest_url` (e.g., `rtmps://ingest.platform.com/live/{stream_key}`).
3. Creator's encoder connects to the RTMP ingest endpoint and begins sending the video stream.
4. Live Ingest Service authenticates the stream key against the live event record. If invalid, TCP connection is terminated.
5. Live Ingest Service inspects the incoming stream: codec (H.264 expected), resolution, frame rate, audio format. If codec is unsupported, connection is rejected.
6. Live Ingest Service forwards the raw RTMP stream to the Live Transcoding Service.
7. Live Transcoding Service spins up a transcoding pipeline (dedicated ffmpeg instance per stream) producing: 360p 800kbps, 720p 2500kbps, 1080p 5000kbps LL-HLS variants with 2-second segments.
8. Each LL-HLS part (0.5-second) is uploaded to the CDN origin as it is produced, achieving <3 second end-to-end latency.
9. Live Transcoding Service writes DVR segments to S3 in parallel.
10. Live Manifest Service generates the LL-HLS master manifest and publishes the CDN URL to the Live Event record.
11. Live Event record status updates to `LIVE`. The catalog immediately surfaces the event in the Live section.
12. Creator Studio UI displays stream health metrics: bitrate received, dropped frames, viewer count.

### Exception Flows

**EF-01: Stream Disconnection**
If the creator's encoder disconnects, Live Ingest Service waits 60 seconds for reconnection. If the stream resumes within 60 seconds, transcoding continues seamlessly. If not, the event is marked `INTERRUPTED` and viewers see a "Stream interrupted" message.

**EF-02: Codec Violation During Stream**
If the encoder dynamically changes to an unsupported codec mid-stream, Live Transcoding Service logs the violation and switches to displaying a "Technical difficulties" slate to viewers while maintaining the manifest.

### Business Rules
- **BR-LIVE-01:** Maximum stream duration: 12 hours. Beyond 12 hours the stream is automatically ended and archived.
- **BR-LIVE-02:** Live streams are encrypted in transit (RTMPS) but may optionally be DRM-protected for playback.
- **BR-LIVE-03:** DVR lookback window: 4 hours maximum.

### Non-Functional Requirements
- **Latency:** LL-HLS end-to-end latency target: <3 seconds.
- **Scale:** Platform must support 10,000 concurrent live streams.

---

## UC-007: Watch Live Stream

**Use Case ID:** UC-007
**Use Case Name:** Watch Live Stream
**Version:** 1.1
**Status:** Approved

### Actor(s)
- **Primary:** Viewer
- **Secondary:** CDN, Chat Service, Analytics Service

### Description
A Viewer joins and watches an active live stream. The platform checks entitlement, delivers the LL-HLS stream via CDN, enables live chat participation, tracks viewer analytics, and transitions to the VOD recording when the stream ends.

### Preconditions
1. The live event has status `LIVE`.
2. The Viewer has an authenticated session and an active subscription (if stream is subscriber-only).

### Main Success Scenario
1. Viewer clicks the live stream card on the catalog or receives a push notification.
2. Viewer's client fetches `GET /v1/live-events/{event_id}/playback`.
3. Platform checks entitlement and returns the signed LL-HLS manifest URL.
4. Player fetches the manifest and begins buffering from the live edge (latest available segment).
5. Player synchronises to the live edge using low-latency HLS part requests.
6. Chat Service WebSocket connection is established: `wss://chat.platform.com/live/{event_id}`.
7. Viewer can send chat messages (rate-limited to 2 messages per second per viewer).
8. Chat Service broadcasts messages to all connected viewers with sub-100 ms delivery.
9. Player emits live-stream analytics events: viewer count reported to the Live Dashboard Service every 10 seconds.
10. If the creator ends the stream, the manifest `#EXT-X-ENDLIST` tag is set. Player receives this and displays a "Stream ended" screen.
11. Platform enqueues a VOD archival job. When complete, the content item transitions to a normal VOD record.
12. Viewer is offered the option to watch the replay immediately.

### Exception Flows

**EF-01: Stream Falls Behind Live Edge**
If the viewer's buffer runs out and the player is >30 seconds behind the live edge, the player auto-seeks to the live edge on the next segment fetch.

### Business Rules
- **BR-LW-01:** Chat is disabled by default for streams with under 100 concurrent viewers (configurable by Creator).
- **BR-LW-02:** Viewers banned from a creator's channel cannot access the live chat or react.

---

## UC-008: Content Moderation Review

**Use Case ID:** UC-008
**Use Case Name:** Content Moderation Review
**Version:** 1.2
**Status:** Approved

### Actor(s)
- **Primary:** Platform Administrator (Human Reviewer)
- **Secondary:** Automated Moderation Service (ML pipeline), Content Creator, Viewer (reporter)

### Description
Content suspected of violating platform policies (hate speech, graphic violence, copyright violation, CSAM) is reviewed by an Administrator. The review process combines automated ML signals with human judgement to decide: approve, age-restrict, demonetise, remove, or escalate.

### Preconditions
1. A content item has been flagged: either by an automated scan (ML confidence > 70%), by a Viewer report, or by a Creator dispute.
2. The flagged item is queued in the Moderation Dashboard.

### Main Success Scenario
1. Automated Moderation Service analyses the video using ML models: nudity/explicit content detector (NSFW score), violence classifier, hate speech transcription analysis, and watermark/piracy detector.
2. Automation assigns a preliminary verdict with confidence scores per category.
3. Content with CSAM signals is immediately removed and the case is escalated to the Trust & Safety team and reported to NCMEC without human review steps.
4. For non-CSAM flags, an Administrator opens the moderation case in the dashboard.
5. Administrator reviews the automated signals, plays the flagged video segments (highlighted by the ML model), and reads the reporter's description.
6. Administrator selects a verdict: **Approve** (no violation), **Age-Restrict** (18+ gate), **Demonetise** (no ads/revenue), **Remove** (policy violation), **DMCA Takedown** (copyright — routes to UC-009).
7. Administrator adds a case note explaining the decision.
8. System applies the verdict: updates content status, updates Creator's policy strike count if applicable.
9. If verdict is Remove or DMCA, system also purges CDN edge cache for the content.
10. Notification Service sends the Creator a policy notice explaining the action and appeal rights.
11. If Creator submits an appeal, the case re-enters the moderation queue tagged `APPEAL` for senior review.

### Alternative Flows

**AF-01: Automated Removal (High-Confidence NSFW)**
If the NSFW classifier exceeds 95% confidence, the system automatically sets content status to `UNDER_REVIEW` and hides it from the catalog pending human confirmation. The human then confirms or reverses the automated removal within 24 hours.

### Exception Flows

**EF-01: Reviewer Conflict of Interest**
If the content was uploaded by a Creator whose account shares metadata with the reviewing Admin's account, the system flags a potential conflict and reassigns the case to a different reviewer.

### Business Rules
- **BR-MOD-01:** Three policy strikes within 90 days result in automatic account suspension.
- **BR-MOD-02:** CSAM content must be reported to NCMEC within 24 hours of detection.
- **BR-MOD-03:** Content removal must be actioned within 24 hours of a valid report for terrorist content (per DSA Article 46).
- **BR-MOD-04:** Creators have 14 days to appeal a removal decision.

### Non-Functional Requirements
- **SLA:** 95% of flagged content reviewed within 24 hours; CSAM within 1 hour.
- **Audit:** All moderation decisions and reviewer identities must be logged immutably for 5 years.

---

## UC-009: Process DMCA Takedown

**Use Case ID:** UC-009
**Use Case Name:** Process DMCA Takedown
**Version:** 1.0
**Status:** Approved

### Actor(s)
- **Primary:** Platform Administrator (DMCA Officer)
- **Secondary:** Content Creator (alleged infringer), Rights Holder (claimant), Legal Team

### Description
A rights holder submits a DMCA Section 512 takedown notice. The platform's DMCA Officer validates the notice, removes the infringing content, notifies the Creator, and manages any counter-notices filed by the Creator in accordance with the DMCA safe harbour provisions.

### Preconditions
1. A DMCA notice has been received via the designated agent (`dmca@platform.com`) or the web form.
2. The DMCA Officer role is held by a designated Administrator.

### Main Success Scenario
1. Rights holder submits a DMCA notice containing: identification of the copyrighted work, identification of the infringing material (URL), good faith statement, accuracy statement under penalty of perjury, and claimant signature.
2. DMCA Officer reviews the notice for legal sufficiency. Materially deficient notices (missing required elements) are rejected with an explanation to the claimant.
3. For a valid notice, the DMCA Officer creates a DMCA case record in the legal case management system.
4. DMCA Officer identifies the content item from the URL in the notice and confirms it is hosted by the platform.
5. Platform disables access to the content item: sets status `DMCA_DISABLED`, removes from catalog, purges CDN cache.
6. Platform sends the Creator a DMCA takedown notice: specifying the claimed work, the takedown URL, the claimant's contact information (required by 512(c)(3)), and instructions for filing a counter-notice.
7. Platform notifies the claimant that the content has been removed.
8. DMCA case status is updated to `CONTENT_REMOVED`.
9. Creator has 10–14 business days to file a counter-notice.
10. If no counter-notice is filed, the case is marked `RESOLVED`. The content remains disabled.
11. If a counter-notice is filed by the Creator (containing their contact info, consent to jurisdiction, and statement under penalty of perjury), the platform forwards it to the rights holder.
12. The rights holder has 10–14 business days to file a court action. If no court action is filed, the platform restores the content.
13. If a court action is filed, the platform does not restore the content and defers to the court.

### Exception Flows

**EF-01: Repeat Infringer**
If this is the Creator's third DMCA-substantiated strike within 12 months, the Creator's account is terminated per the platform's repeat infringer policy.

**EF-02: Fraudulent Notice**
If the DMCA Officer determines the notice is fraudulent or constitutes abuse (e.g., targeting a clearly licensed work), the case is rejected, the claimant is recorded as a potential abuser, and the platform may restrict future notices from the claimant.

### Business Rules
- **BR-DMCA-01:** Response to a valid DMCA notice must occur within 24 hours (business days).
- **BR-DMCA-02:** DMCA case records must be retained for 7 years.
- **BR-DMCA-03:** The platform's DMCA Designated Agent must be registered with the U.S. Copyright Office.

### Non-Functional Requirements
- **Compliance:** Full compliance with 17 U.S.C. § 512 safe harbour requirements.
- **Audit Trail:** Immutable, timestamped records of every action in the DMCA case.

---

## UC-010: Download Content for Offline

**Use Case ID:** UC-010
**Use Case Name:** Download Content for Offline
**Version:** 1.1
**Status:** Approved

### Actor(s)
- **Primary:** Viewer
- **Secondary:** Download Service, DRM Provider, CDN

### Description
A Viewer with a Standard or Premium subscription downloads an encrypted copy of a content item to their device for offline playback. The Download Service provides a download token; the DRM Provider issues an offline-enabled licence; the player downloads and stores the encrypted segments and licence. Offline playback proceeds without a network connection. Downloads expire per the DRM licence policy.

### Preconditions
1. Viewer has Standard or Premium subscription (Basic plan excludes offline downloads).
2. Content Creator has not disabled offline downloads for the content item.
3. The Viewer's device has sufficient storage space for the target quality level.
4. Viewer has not exceeded their simultaneous download limit (Standard: 2 titles, Premium: unlimited).

### Postconditions
**On Success:**
1. All video segments for the selected quality level are stored encrypted on the device.
2. An offline DRM licence (30-day expiry) is stored in the device's CDM licence store.
3. The download record is tracked in the Download Service.
4. The content can be played offline without any network request (except for licence renewal).

### Main Success Scenario
1. Viewer taps the download icon on a content detail page.
2. Client sends `POST /v1/downloads` with `{content_id, quality: "1080p"}`.
3. Download Service checks the Viewer's subscription plan for offline eligibility. Returns HTTP 403 with `OFFLINE_NOT_PERMITTED` for Basic plan.
4. Download Service checks the content item's `offline_available` flag. Returns HTTP 403 with `OFFLINE_DISABLED_BY_CREATOR` if not available.
5. Download Service checks the Viewer's concurrent download count. If at limit, returns HTTP 429 with `DOWNLOAD_LIMIT_REACHED`.
6. Download Service generates an offline playback token (`offline: true` flag) with a 30-day expiry.
7. Download Service returns the token plus the list of segment URLs (signed, long-lived 30-day presigned S3 URLs for the chosen quality rendition).
8. Client initiates an offline DRM licence request: `POST /v1/drm/license/{system}` with the offline token. DRM Proxy issues a licence with `offline_expiry = now + 30 days`.
9. Client downloads all `.ts` or `.m4s` segments sequentially (to avoid overwhelming mobile data plans) from the CDN, storing them in the device's encrypted local storage.
10. Client stores the variant playlist (`.m3u8`) and the DRM licence alongside the segments.
11. Download Service records the download: `{viewer_id, content_id, quality, downloaded_at, expires_at: now + 30_days}`.
12. Client displays download progress (percentage) and marks the content with an offline indicator when complete.
13. Viewer can now play the content offline. The player reads segments from local storage, decrypts with the cached licence.
14. After 30 days, the DRM licence expires. The player shows "Download expired. Renew to continue watching." If the Viewer is online and their subscription is still active, the player automatically requests a new licence.
15. If the Viewer's subscription lapses, licence renewal is denied and the downloaded content becomes unplayable. Segments remain on disk but cannot be decrypted.

### Alternative Flows

**AF-01: Background Download Resumption**
If the download is interrupted (app backgrounded, network lost), the client resumes from the last successfully saved segment on the next app foreground event.

**AF-02: Download Deletion**
Viewer can delete a downloaded title from the Downloads screen. The client deletes all local segment files and the licence, and calls `DELETE /v1/downloads/{download_id}` to decrement the download count.

### Exception Flows

**EF-01: Insufficient Device Storage**
Before beginning the download, the client estimates the required space based on segment count × average segment size. If insufficient, the user is shown a storage warning with an option to free space or select a lower quality.

**EF-02: DRM Licence Denied Mid-Download**
If the Viewer's subscription lapses while a download is in progress (e.g., payment failure processed between steps 8 and 12), the DRM licence request is denied. The partially downloaded segments are deleted. The Viewer is shown a subscription renewal prompt.

### Business Rules
- **BR-DL-01:** Maximum simultaneous downloads per device: 10 titles for Premium, 5 for Standard.
- **BR-DL-02:** Downloaded content expires 30 days after download regardless of licence renewal.
- **BR-DL-03:** Downloaded content is bound to the device; it cannot be transferred to another device or decrypted outside the platform's DRM ecosystem.
- **BR-DL-04:** Creators can disable offline downloads per content item for first-run exclusives or licensed content with territorial restrictions.

### Non-Functional Requirements
- **Performance:** Segment download speed should saturate available bandwidth up to the CDN's per-file transfer limit.
- **Storage:** Encrypted segments must use AES-128 with the platform's CBCS keys; no plaintext segment must ever be stored on-disk.
- **Privacy:** The Download Service must not retain segment URLs for longer than the download session; only segment count and completion status are stored server-side.
