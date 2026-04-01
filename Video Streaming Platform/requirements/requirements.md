# Requirements — Video Streaming Platform

> Version 1.0 | Status: Approved | Audience: Engineering, Product, QA, Legal

---

## Table of Contents

1. [Overview](#1-overview)
2. [Stakeholders](#2-stakeholders)
3. [Scope](#3-scope)
4. [Functional Requirements](#4-functional-requirements)
   - 4.1 [Content Management](#41-content-management)
   - 4.2 [Streaming & Playback](#42-streaming--playback)
   - 4.3 [Live Streaming](#43-live-streaming)
   - 4.4 [Subscriptions & Monetisation](#44-subscriptions--monetisation)
   - 4.5 [Content Discovery & Recommendations](#45-content-discovery--recommendations)
   - 4.6 [Creator Tools](#46-creator-tools)
   - 4.7 [Administration & Trust and Safety](#47-administration--trust-and-safety)
5. [Non-Functional Requirements](#5-non-functional-requirements)
   - 5.1 [Performance](#51-performance)
   - 5.2 [Scalability](#52-scalability)
   - 5.3 [Availability & Reliability](#53-availability--reliability)
   - 5.4 [Security](#54-security)
   - 5.5 [Compliance & Accessibility](#55-compliance--accessibility)
   - 5.6 [Maintainability & Operability](#56-maintainability--operability)
6. [Constraints](#6-constraints)
7. [Assumptions](#7-assumptions)
8. [Glossary](#8-glossary)

---

## 1. Overview

The **Video Streaming Platform** is a cloud-native, globally distributed service for publishing, delivering, and monetising video content at Internet scale. It supports both **Video on Demand (VOD)** — pre-recorded content uploaded and stored — and **Live Streaming** — real-time broadcast content ingested and distributed with sub-second to sub-4-second end-to-end latency.

The platform targets two primary audiences:
- **Consumers (Viewers):** Subscribers who watch content on web browsers, iOS/Android apps, Smart TVs, and streaming sticks (Roku, Fire TV, Chromecast).
- **Producers (Creators):** Independent creators, media companies, or enterprise customers who upload content, go live, and analyse performance.

The platform must be capable of competing operationally with Netflix (200M+ subscribers), YouTube (2.7B monthly active users), and Twitch (8M concurrent live viewers at peak). All design decisions must account for this scale from day one.

---

## 2. Stakeholders

| Stakeholder | Role | Key Interests |
|---|---|---|
| **Viewers** | Primary consumer | Reliable, high-quality playback; seamless cross-device experience; fair pricing |
| **Content Creators** | Primary producer | Easy upload; rich analytics; monetisation options; fast content publishing |
| **Platform Administrators** | Operations | Efficient moderation workflows; user management; system health visibility |
| **Product Management** | Strategy | Feature completeness; conversion metrics; churn reduction |
| **Engineering** | Build & operate | Clean APIs; well-defined service contracts; observability |
| **Finance** | Revenue | Billing accuracy; subscription growth; payment reliability |
| **Legal / Compliance** | Risk | GDPR/CCPA compliance; DMCA safe harbor; COPPA enforcement |
| **Security** | Risk | DRM robustness; API security; fraud prevention |
| **Content Partners** | Licensing | Rights management; geo-restriction controls; revenue reporting |
| **Advertisers** | Revenue | Targeted ad delivery; viewability metrics; brand safety |

---

## 3. Scope

### In Scope

- VOD ingestion, transcoding, packaging, and delivery
- Live streaming ingest, transcoding, packaging, and delivery
- Multi-DRM content protection (Widevine, FairPlay, PlayReady)
- Subscription management and payment processing
- Content discovery, search, and personalised recommendations
- Creator dashboard with analytics and monetisation
- Content moderation (AI-assisted + human review)
- Multi-CDN delivery with automatic failover
- Native mobile apps (iOS, Android) and web player
- Smart TV apps (Apple TV, Android TV, Samsung Tizen, LG webOS, Roku, Fire TV)
- Administrative console for operations and trust-and-safety teams
- Platform analytics and business intelligence

### Out of Scope (Phase 1)

- Social network features (following/followers feeds beyond subscriptions)
- User-generated short-form clips (TikTok-style vertical feed) — Phase 2
- Podcast hosting — Phase 3
- Live commerce / interactive shopping — Phase 3
- VR/360° video streaming — Phase 4

---

## 4. Functional Requirements

### 4.1 Content Management

#### 4.1.1 Video Upload

| ID | Requirement |
|---|---|
| CM-001 | The system shall accept single-file uploads up to **100 GB** via standard multipart HTTP POST. |
| CM-002 | Files larger than **5 GB** shall be uploaded using the **TUS resumable upload protocol** (tus.io v1.0) or AWS S3 multipart upload API, with automatic resume on connection failure. |
| CM-003 | Upload progress must be queryable via a `/uploads/{uploadId}/status` endpoint returning percentage complete, bytes transferred, and ETA. |
| CM-004 | Supported input container formats: **MP4, MOV (QuickTime), MKV (Matroska), AVI, WebM, ProRes (.mov), DNxHD/DNxHR (.mxf, .mov)**. |
| CM-005 | Supported input video codecs: **H.264 (AVC), H.265 (HEVC), VP8, VP9, AV1, Apple ProRes 422/4444, Avid DNxHD/DNxHR**. |
| CM-006 | Supported input audio codecs: **AAC, MP3, AC-3, E-AC-3, PCM (WAV/AIFF), FLAC, Opus**. |
| CM-007 | The system shall validate file integrity using **SHA-256 checksums** provided at upload initiation; uploads failing checksum verification shall be rejected with `HTTP 422`. |
| CM-008 | Uploaded files shall be quarantined in a staging S3 bucket; they are promoted to the processing bucket only after passing virus/malware scanning (ClamAV integration). |
| CM-009 | Bulk upload shall be supported via a **CSV manifest** (columns: `source_url`, `title`, `description`, `category`, `tags`, `visibility`) and a corresponding bulk ingestion API endpoint. |
| CM-010 | Creators shall be able to replace existing video content (re-upload) without changing the video's public URL or metadata; the old renditions shall be preserved for 72 hours before deletion to support rollback. |

#### 4.1.2 Transcoding

| ID | Requirement |
|---|---|
| CM-011 | Upon upload completion, the system shall automatically enqueue a transcoding job within **30 seconds**. |
| CM-012 | The system shall transcode source video to **HLS** (RFC 8216) and **MPEG-DASH** (ISO 23009-1) adaptive bitrate formats. |
| CM-013 | The standard bitrate ladder shall include the following renditions: |

**Standard ABR Ladder:**

| Resolution | Codec | Video Bitrate | Audio Bitrate | Frame Rate |
|---|---|---|---|---|
| 240p (426×240) | H.264 Baseline | 400 kbps | 64 kbps AAC | 24 fps |
| 360p (640×360) | H.264 Main | 800 kbps | 96 kbps AAC | 24 fps |
| 480p (854×480) | H.264 Main | 1,500 kbps | 128 kbps AAC | 30 fps |
| 720p (1280×720) | H.264 High | 3,000 kbps | 128 kbps AAC | 30/60 fps |
| 1080p (1920×1080) | H.264 High | 6,000 kbps | 192 kbps AAC | 30/60 fps |
| 1080p HDR | H.265 Main10 | 8,000 kbps | 192 kbps AAC | 30/60 fps |
| 2160p / 4K (3840×2160) | H.265 Main10 | 20,000 kbps | 384 kbps AAC | 24/30 fps |
| 2160p / 4K HDR | H.265 Main10 | 25,000 kbps | 384 kbps AAC | 24/30 fps |

| ID | Requirement |
|---|---|
| CM-014 | **Per-title encoding** shall be applied: the platform analyses each video's complexity using a single-pass preview encode and computes the optimal bitrate for each resolution using convex hull optimisation, reducing file size by 20–40% versus fixed ladders. |
| CM-015 | Segment duration for HLS and DASH shall be **6 seconds** for VOD and **2 seconds** (with 200ms parts) for LL-HLS live outputs. |
| CM-016 | The system shall generate a **sprite sheet** (one thumbnail per 10 seconds) for video timeline hover previews. |
| CM-017 | Transcoding jobs shall expose real-time progress events via Kafka topic `transcode.progress.{jobId}`, consumed by the creator dashboard. |
| CM-018 | Failed transcoding jobs shall be retried up to **3 times** with exponential backoff (15s, 60s, 300s); after all retries fail, the creator shall be notified via email with a failure reason. |
| CM-019 | Transcoding infrastructure shall support **GPU-accelerated** encoding using NVIDIA NVENC for H.264/H.265 on `g4dn.xlarge` or larger EC2 instances. |

#### 4.1.3 Thumbnail & Metadata

| ID | Requirement |
|---|---|
| CM-020 | The system shall automatically extract **5 candidate thumbnails** at even intervals; the creator may select one or upload a custom JPEG/PNG (max 2 MB, aspect ratio 16:9). |
| CM-021 | Thumbnails shall be served from CDN edge with **WebP** conversion for supporting browsers, reducing thumbnail payload by ~30%. |
| CM-022 | Metadata fields per video: `title` (max 200 chars), `description` (max 5,000 chars), `tags` (max 50, each ≤ 50 chars), `category` (single, from taxonomy), `cast` (list of names), `release_year`, `rating` (MPAA-style), `language`, `country_of_origin`. |
| CM-023 | Subtitles/captions shall be accepted in **SRT, WebVTT, SCC, and TTML** formats; the system converts all formats to WebVTT for delivery. |
| CM-024 | The creator may optionally **burn subtitles** into the video at a chosen rendition; burned-in renditions are stored separately and are not encrypted with DRM. |
| CM-025 | Auto-generated captions shall be produced via an ASR pipeline (Whisper large-v3 model) within **10 minutes** of transcoding completion; creator may edit captions in a web-based caption editor. |

---

### 4.2 Streaming & Playback

| ID | Requirement |
|---|---|
| PB-001 | The web player shall support **HLS** playback using `hls.js` and **DASH** playback using `Shaka Player`; format selection shall be automatic based on browser DRM capabilities. |
| PB-002 | iOS and macOS Safari shall use **HLS with FairPlay DRM** via native `AVPlayer`. |
| PB-003 | Android and Chrome shall use **DASH or HLS with Widevine DRM** via ExoPlayer (Android) or EME (Web). |
| PB-004 | Windows Edge and Xbox shall use **DASH with PlayReady DRM**. |
| PB-005 | The player shall implement **ABR switching** with hysteresis: upgrade quality when buffer > 20s and available bandwidth exceeds next tier by 20%; downgrade when buffer < 8s. |
| PB-006 | The player shall support **playback speed control** from **0.25×** to **3.0×** in 0.25× increments, applied to both audio (pitch-corrected) and video. |
| PB-007 | The player shall support **chapter navigation** if the creator has defined timestamps; chapters shall be visually indicated on the progress bar. |
| PB-008 | **Picture-in-Picture (PiP)** shall be supported on iOS 14+, Android 8+, Chrome 70+, Safari 13+, and Firefox 86+. |
| PB-009 | **Chromecast** (Google Cast SDK v3) and **AirPlay** (AVFoundation) shall be supported for casting to TVs. |
| PB-010 | **Resume playback** — the player shall save the last watch position server-side (to `watch_progress` table) at 10-second intervals and on pause/unload events; position shall be restored on any device when the viewer re-opens the video. |
| PB-011 | **Offline download** (mobile only): DRM-protected content may be downloaded at up to 1080p for offline viewing; downloaded files are bound to the device's DRM hardware; licence offline lease period is **30 days** (renewed on next online session). |
| PB-012 | The player shall display a **"Skip Intro"** button when the creator has defined an intro segment (detected automatically via audio fingerprinting or manual timestamp). |
| PB-013 | The player shall support **multi-audio track selection** (e.g., original language + dub) and **multi-subtitle track selection** (all ingested caption tracks). |
| PB-014 | The player shall collect playback telemetry: `startup_time_ms`, `initial_bitrate_kbps`, `bitrate_switches`, `buffering_events`, `buffering_duration_ms`, `errors`, `exit_before_end`, emitting events to the analytics pipeline via beacon API. |
| PB-015 | Playback of DRM-protected content shall require a valid **DRM licence token** with expiry ≤ 30 minutes; the player shall proactively renew tokens 5 minutes before expiry without interrupting playback. |

---

### 4.3 Live Streaming

| ID | Requirement |
|---|---|
| LS-001 | The platform shall accept live stream ingest via **RTMP** (port 1935) and **RTMPS** (port 443, TLS) using a per-creator stream key. |
| LS-002 | The platform shall accept ingest via **SRT** (Secure Reliable Transport, port 4200) for contribution links over unreliable public internet; SRT shall provide FEC and ARQ retransmission. |
| LS-003 | The platform shall support **WebRTC** ingest for ultra-low-latency (< 1 second) use cases (e.g., interactive events, gaming); WebRTC ingest shall transcode to HLS/DASH for broad delivery. |
| LS-004 | The live transcoder shall produce the following ABR ladder for standard streams: **360p (800 kbps), 720p (3 Mbps), 1080p (6 Mbps)**; 1080p60 at 8 Mbps shall be available for Premium plan creators. |
| LS-005 | **LL-HLS** (Low-Latency HLS per Apple's draft spec) output shall be generated with 2-second segment duration and 200ms partial segment (part) duration, achieving **end-to-end latency < 4 seconds**. |
| LS-006 | **CMAF-CTE** (Common Media Application Format with Chunked Transfer Encoding) shall be generated for DASH-compatible players targeting < 3-second latency. |
| LS-007 | A **DVR sliding window** of **30 minutes** (configurable up to **4 hours** for enterprise plans) shall be maintained, allowing viewers to seek back in the live stream. |
| LS-008 | At stream end, the platform shall automatically trigger a **live-to-VOD archival** job: the full stream recording shall be processed into a standard VOD asset and made available within **30 minutes** of stream conclusion. |
| LS-009 | The platform shall support **multi-source co-streaming**: up to **4 simultaneous RTMP ingest sources** can be combined (picture-in-picture or side-by-side layout) into a single output stream. |
| LS-010 | Scheduled live events shall support a **countdown page** with configurable pre-show content (static image or looping video) displayed until stream start. |
| LS-011 | **Live chat** shall be implemented as a WebSocket-based service supporting up to **100,000 concurrent chat participants** per stream; messages shall be rate-limited to 1 per 2 seconds per viewer to prevent flooding. |
| LS-012 | Creators shall be able to configure **slow mode** (1 message per N seconds), **subscriber-only mode**, and **emoji-only mode** for chat. |
| LS-013 | The live ingest pipeline shall detect stream health and alert the creator via dashboard notification if: input bitrate drops below 80% of configured target, audio levels are silent for > 10 seconds, or video freeze is detected. |
| LS-014 | **Stream key rotation** shall be supported: creators can regenerate stream keys without interrupting a currently-active stream; the new key takes effect on the next connection. |

---

### 4.4 Subscriptions & Monetisation

| ID | Requirement |
|---|---|
| MN-001 | The platform shall offer the following **subscription tiers**: |

**Subscription Plan Matrix:**

| Plan | Price/mo | Resolution | Screens | Downloads | Ads | Extras |
|---|---|---|---|---|---|---|
| Free | $0 | 480p | 1 | No | Yes (pre-roll + mid-roll) | — |
| Basic | $6.99 | 1080p | 1 | No | No | — |
| Standard | $13.99 | 1080p | 2 | Yes (2 devices) | No | — |
| Premium | $19.99 | 4K HDR | 4 | Yes (4 devices) | No | Spatial Audio |
| 4K Ultra | $24.99 | 4K Dolby Vision | 6 | Yes (6 devices) | No | Dolby Atmos, HDR10+ |

| ID | Requirement |
|---|---|
| MN-002 | **Pay-Per-View (PPV):** Individual content items (films, sporting events, concerts) may be priced for one-time purchase or 48-hour rental. |
| MN-003 | **Creator channel memberships:** Creators may offer up to **5 membership tiers** with configurable monthly prices ($1–$500); membership perks include ad-free viewing, exclusive content, early access, and custom badges. |
| MN-004 | **Ad-supported tier (SSAI):** Pre-roll (max 30s) and mid-roll (max 15s, triggered at content-defined ad markers) ads shall be inserted server-side via AWS MediaTailor integration with VAST 2.0/3.0 ad tags. |
| MN-005 | **Creator revenue sharing:** Platform takes **30%** of ad revenue and **20%** of membership revenue; creators receive a monthly payout to a connected bank account (Stripe Connect) or PayPal. |
| MN-006 | The platform shall support **coupon codes** with fixed-amount, percentage, or free-trial configurations; coupons shall be single-use or multi-use with configurable expiry dates. |
| MN-007 | **Family/group plans:** A plan holder may add up to **5 member accounts** at a discounted incremental rate ($2.99/member/month); member accounts inherit the plan holder's content entitlements. |
| MN-008 | **Annual billing:** All plans shall offer an annual payment option at a **2-month discount** (equivalent to 10 months' price for 12 months). |
| MN-009 | Billing shall use **Stripe** as the primary payment processor and **Braintree** as the fallback; Stripe webhooks shall trigger entitlement updates within **5 seconds** of payment event. |
| MN-010 | **Dunning management:** Failed payments shall trigger a retry schedule: Day 1, Day 3, Day 7, Day 14; after all retries fail, subscription shall be downgraded to Free with 7-day grace period; subscriber is notified at each stage. |
| MN-011 | Subscription **upgrades** shall be prorated (charge for remaining days on new plan); **downgrades** shall take effect at the end of the current billing period. |
| MN-012 | Viewers shall be able to **cancel subscriptions** self-service; cancellation is effective at period end; data shall be retained for 90 days post-cancellation per GDPR; deleted on explicit erasure request. |

---

### 4.5 Content Discovery & Recommendations

| ID | Requirement |
|---|---|
| DS-001 | **Full-text search** shall be powered by Elasticsearch 8.x, indexing: `title`, `description`, `tags`, `cast`, `auto-generated transcript`, `category`. |
| DS-002 | Search shall support **fuzzy matching** (edit distance ≤ 2 for queries > 4 characters), **synonym expansion** (configurable synonym dictionary), and **language-specific analysers** for at least English, Spanish, French, German, Portuguese, Japanese, Korean. |
| DS-003 | **Search autocomplete** shall return up to **10 suggestions** within **50ms** (P99) using a prefix-indexed completion suggester. |
| DS-004 | **Faceted filtering** shall be available: filter by `category`, `duration`, `language`, `release_year`, `rating`, `resolution` (4K, HDR), `upload_date`. |
| DS-005 | The **recommendation engine** shall generate personalised homepage rows: "Continue Watching", "Recommended for You", "Because You Watched [X]", "Trending Now", "New Releases", "Top in [Category]". |
| DS-006 | Recommendations shall use a **two-stage retrieval-ranking** architecture: (1) ALS collaborative filtering model retrieves top-500 candidate videos; (2) a neural ranker (LightGBM or two-tower DNN) re-ranks candidates using contextual features (time of day, device, session length). |
| DS-007 | The recommendation model shall be retrained **daily** on the previous 90-day interaction window using SageMaker Processing jobs; predictions shall be pre-computed and cached in Redis with a 15-minute TTL. |
| DS-008 | **Cold-start strategy for new users:** Content-based filtering using onboarding genre preferences; fallback to global popularity ranking until 10 interactions are recorded. |
| DS-009 | **Cold-start strategy for new content:** Metadata-based similarity to existing catalogue; boosted exposure for 72 hours after publish to gather interaction signal. |
| DS-010 | The **"Trending Now"** row shall be computed using a real-time view velocity algorithm: `score = view_count_last_24h / (hours_since_upload + 2)^gravity` where `gravity = 1.8`; computed every 5 minutes via Flink. |

---

### 4.6 Creator Tools

| ID | Requirement |
|---|---|
| CT-001 | The **Creator Studio** dashboard shall display: total views (lifetime + 28-day), watch time (hours), average view duration, revenue (ad + membership), subscriber count, top-performing videos. |
| CT-002 | **Audience retention graph** shall be available per video: shows the percentage of viewers still watching at each second of the video, highlighting drop-off points and re-watch peaks. |
| CT-003 | **Traffic source breakdown** shall show: direct (homepage/notification), search, recommended, external links, social media — with click-through rate (CTR) per source. |
| CT-004 | **Realtime analytics** (for live streams and first 48 hours post-publish): concurrent viewers, chat message rate, bitrate quality distribution, geographic distribution — refreshed every 60 seconds. |
| CT-005 | The **Video Manager** shall allow creators to: edit metadata, change visibility (`public`, `unlisted`, `private`, `scheduled`), update thumbnails, manage captions, set geo-restrictions, duplicate videos. |
| CT-006 | Creators shall be able to **schedule content** for future publish, specifying a UTC timestamp up to 6 months in advance. |
| CT-007 | **Comment management:** AI pre-filter flags comments with toxicity score > 0.7 for review; creator can approve, delete, pin, or respond to comments; bulk moderation actions available. |
| CT-008 | **Community posts:** Creators can publish text, image, video preview, or poll posts to their channel; posts are visible to subscribers and on the channel page. |
| CT-009 | Creators shall receive an **email digest** (daily or weekly, configurable) summarising analytics: top video, total views, new subscribers, revenue. |
| CT-010 | **Channel page customisation:** Banner image (2560×1440 px), profile avatar, channel description (max 1,000 chars), featured video/playlist, custom URL slug (verified channels only). |

---

### 4.7 Administration & Trust and Safety

| ID | Requirement |
|---|---|
| AD-001 | **AI content classifier** shall scan every uploaded video for: nudity/sexual content, graphic violence, hate symbols, and drug/weapon depictions; flagged content is held in a review queue and not published until cleared. |
| AD-002 | The classifier shall target a **false positive rate < 5%** and **recall > 95%** for Category 1 (CSAM, terrorism); all Category 1 detections trigger immediate removal and law enforcement reporting workflow. |
| AD-003 | **Audio transcript moderation**: ASR-generated transcripts shall be scanned for hate speech, harassment, and prohibited content keywords using an NLP classifier. |
| AD-004 | **Content ID fingerprinting:** Audio and video fingerprints shall be computed for every upload and matched against a rights-holder fingerprint database (Audible Magic / internal); matches trigger automatic claim notification to the rights-holder. |
| AD-005 | **DMCA takedown workflow:** DMCA notices received via email or web form shall be parsed, matched to content, automatically removed within **24 hours** of receipt, and creator notified; counter-notice workflow (10-business-day window) shall be supported. |
| AD-006 | **Geo-restriction management:** Administrators and creators shall be able to restrict video availability to a whitelist or blacklist of **ISO 3166-1 alpha-2** country codes; enforcement is at the CDN edge via signed token claims. |
| AD-007 | **User management:** Admins can search users by email/username/ID, view account details, suspend/ban accounts (temporary or permanent), reset passwords, and impersonate users for support (all impersonation events logged to immutable audit log). |
| AD-008 | **Platform-wide reporting:** Admin dashboard shall provide: DAU/MAU, content hours uploaded per day, streaming hours delivered, revenue (MRR, ARR, churn rate), moderation queue SLA metrics, CDN cost breakdown — exportable to CSV. |
| AD-009 | **Age verification (COPPA):** Users indicating age under 13 during registration shall be directed to a parental consent flow; COPPA-protected accounts shall have restricted data collection (no personalised ads, no watch history sharing). |
| AD-010 | **Parental controls:** A verified parent/guardian may link child accounts and configure: maximum content rating allowed, daily watch time limit, restricted search. |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| ID | Metric | Target | Measurement |
|---|---|---|---|
| NFR-P01 | VOD playback startup time | < 2 seconds (P99), < 1 second (P50) | Player telemetry: `time_to_first_frame` |
| NFR-P02 | Live stream end-to-end latency (LL-HLS) | < 4 seconds (P99), < 2 seconds (P50) | Clock-sync measurement from OBS → player |
| NFR-P03 | Metadata API response time | < 100ms (P95), < 50ms (P50) | APM traces on `/api/v1/videos/{id}` |
| NFR-P04 | Search query response time | < 200ms (P99) | Elasticsearch query latency metrics |
| NFR-P05 | CDN thumbnail delivery | < 50ms | CloudFront access logs, edge cache hit |
| NFR-P06 | 4K HDR streaming bitrate | 15–25 Mbps sustained | ABR telemetry: average bitrate |
| NFR-P07 | ABR segment availability (live) | ≤ 6 seconds after capture | Origin ingest timestamp vs. playlist update |
| NFR-P08 | DRM licence acquisition time | < 500ms (P99) | Player: time from key request to first decrypted frame |
| NFR-P09 | Upload API throughput | ≥ 10 Gbps aggregate | Load test: 1,000 concurrent 1 GB/s upload connections |
| NFR-P10 | Rebuffering ratio | < 0.5% of total watch time | Player telemetry aggregate |

### 5.2 Scalability

| ID | Dimension | Target |
|---|---|---|
| NFR-S01 | Concurrent VOD viewers | 50M+ (horizontal CDN scaling, no single origin bottleneck) |
| NFR-S02 | Concurrent live streams | 500K+ (auto-scaled ingest pods, 1 pod per stream) |
| NFR-S03 | Content uploads per day | 1M+ (async job queue, unlimited transcode farm auto-scaling) |
| NFR-S04 | Total content library | 10PB+ (S3 Intelligent-Tiering; cold content to Glacier after 180 days) |
| NFR-S05 | API request throughput | 100K req/s (horizontally scaled behind API Gateway + Kong) |
| NFR-S06 | Search index size | 500M+ documents (Elasticsearch cluster with dedicated master/data nodes) |
| NFR-S07 | CDN egress bandwidth | 100 Tbps peak (multi-CDN distribution; each CDN capped at 50 Tbps per contract) |
| NFR-S08 | Transcode throughput | 10,000 concurrent jobs (GPU auto-scaling group, target max queue depth: 100 jobs) |
| NFR-S09 | Database connections | 50,000+ (Aurora Serverless v2 connection pooling via PgBouncer) |
| NFR-S10 | Recommendation serving | < 10ms for pre-computed results (Redis cluster, 100K req/s capacity) |

### 5.3 Availability & Reliability

| ID | Requirement | Target |
|---|---|---|
| NFR-A01 | Streaming service uptime SLA | 99.9% (≤ 8.76 hours downtime/year) |
| NFR-A02 | Subscription/payment API uptime SLA | 99.99% (≤ 52 minutes downtime/year) |
| NFR-A03 | Recovery Time Objective (RTO) | < 30 minutes for full regional failover |
| NFR-A04 | Recovery Point Objective (RPO) | < 5 minutes (Aurora Global continuous replication; S3 cross-region replication) |
| NFR-A05 | CDN failover time | < 60 seconds automatic failover from primary to secondary CDN |
| NFR-A06 | Transcode job durability | Zero job loss: all jobs persisted to Aurora; workers are stateless and re-assignable |
| NFR-A07 | Multi-region deployment | Active-active across 3 AWS regions (us-east-1, eu-west-1, ap-northeast-1) |
| NFR-A08 | Database read replicas | ≥ 3 read replicas per region for read-heavy workloads (metadata, catalogue) |
| NFR-A09 | Circuit breakers | All inter-service calls protected by Hystrix/Resilience4j circuit breakers; open after 5 failures in 10 seconds |
| NFR-A10 | Graceful degradation | If recommendation service fails, homepage falls back to curated editorial list from Redis cache |

### 5.4 Security

| ID | Requirement |
|---|---|
| NFR-SEC01 | All content at rest shall be encrypted using **AES-256** (S3 SSE-KMS with CMK) |
| NFR-SEC02 | All data in transit shall use **TLS 1.3**; TLS 1.0 and 1.1 shall be disabled at all load balancers |
| NFR-SEC03 | DRM licence tokens shall expire in ≤ **30 minutes**; playback tokens (signed CDN URLs) shall expire in ≤ **4 hours** |
| NFR-SEC04 | Stream keys shall be stored as HMAC-SHA256 hashes; raw stream keys never stored in database |
| NFR-SEC05 | **Geo-blocking** enforcement via CloudFront geographic restriction + JWT claim `allowed_countries`; enforced at edge, not just origin |
| NFR-SEC06 | **Rate limiting:** API endpoints limited to 100 req/min per authenticated user, 10 req/min per unauthenticated IP; exceeded limits return `HTTP 429` with `Retry-After` header |
| NFR-SEC07 | **DDoS protection:** AWS Shield Advanced on all public-facing ALBs and CloudFront distributions |
| NFR-SEC08 | **OWASP Top 10** compliance; annual penetration test by third-party firm; critical findings remediated within 7 days |
| NFR-SEC09 | **Secrets rotation:** All API keys, database passwords, and DRM keys rotated at least every **90 days** via HashiCorp Vault dynamic secrets |
| NFR-SEC10 | All administrative actions logged to an **immutable audit log** (CloudTrail + S3 with Object Lock WORM) retained for 7 years |

### 5.5 Compliance & Accessibility

| ID | Requirement |
|---|---|
| NFR-C01 | **GDPR (EU 2016/679):** Data subject rights (access, rectification, erasure, portability) fulfilled within 30 days; data processing records maintained; DPA agreements with all sub-processors |
| NFR-C02 | **CCPA (California Consumer Privacy Act):** "Do Not Sell My Personal Information" opt-out; data deletion within 45 days of request |
| NFR-C03 | **COPPA:** Users under 13 require verified parental consent; no behavioural advertising for COPPA-protected accounts |
| NFR-C04 | **DMCA Safe Harbor:** Platform qualifies as a service provider; designated DMCA agent registered with Copyright Office; 24-hour takedown response |
| NFR-C05 | **Accessibility (WCAG 2.1 Level AA):** All web and mobile interfaces meet WCAG 2.1 AA; all video content must have closed captions (auto-generated or creator-uploaded); keyboard-navigable player |
| NFR-C06 | **PCI-DSS:** No raw card data stored on platform infrastructure; Stripe/Braintree handle PCI scope; SAQ A attestation maintained annually |
| NFR-C07 | **SOC 2 Type II:** Annual audit covering Security, Availability, and Confidentiality trust criteria |

### 5.6 Maintainability & Operability

| ID | Requirement |
|---|---|
| NFR-M01 | All services shall expose **Prometheus-compatible `/metrics` endpoints**; scraped by a central Prometheus cluster |
| NFR-M02 | All services shall emit **structured JSON logs** to stdout; collected by Fluentd and shipped to CloudWatch Logs + Datadog |
| NFR-M03 | All HTTP requests shall propagate **W3C Trace Context** headers (`traceparent`, `tracestate`); traces collected in Jaeger |
| NFR-M04 | **Deployment:** All services deployed via ArgoCD GitOps; rollback to previous version achievable in < 2 minutes |
| NFR-M05 | **Canary deployments:** Traffic shifting (1% → 10% → 50% → 100%) with automatic rollback on error rate > 1% or P99 latency increase > 20% |
| NFR-M06 | **Configuration management:** All service configuration stored in Kubernetes ConfigMaps and Secrets; no hardcoded configuration in container images |
| NFR-M07 | **Health checks:** All services expose `/healthz` (liveness) and `/readyz` (readiness) probes; readiness probe fails during schema migration |
| NFR-M08 | **Chaos engineering:** Monthly GameDays simulating: random pod termination (Chaos Monkey), network partition, CDN origin failure, database failover |

---

## 6. Constraints

| Constraint | Description |
|---|---|
| **Cloud Provider** | Primary deployment on AWS; secondary region on AWS; GCP or Azure only for specific vendor services (e.g., Widevine license server on GCP) |
| **DRM Licensing** | Widevine requires Google-approved licence server; FairPlay requires Apple KSM provisioning; both have vendor-specific SLAs and key management requirements |
| **Content Budget** | Transcoding costs estimated at $0.015 per minute of source video per output rendition; cost model must account for 8 renditions per video average |
| **Codec Licensing** | H.264 and H.265 require per-unit MPEG-LA licence fees; AV1 is royalty-free; VP9 is royalty-free; codec mix must balance quality, compatibility, and licensing cost |
| **CDN Egress** | AWS CloudFront pricing: $0.0085–$0.02 per GB depending on region; budget constraint requires CDN caching ratio > 95% for cost viability |
| **Regulatory Jurisdictions** | EU content must be served from EU regions (EU data residency requirement for user PII under GDPR Article 44); US content may be served globally |
| **Mobile App Stores** | iOS App Store and Google Play Store policies govern in-app purchases; subscription management for mobile users must route through native IAP APIs, not direct Stripe integration |
| **Transcode Latency SLA** | Content must be available for streaming within **30 minutes** of upload completion for standard content; up to **4 hours** for ultra-high-bitrate source files > 50 GB |

---

## 7. Assumptions

1. **Infrastructure:** AWS is the primary cloud provider; IaC (Terraform) and Kubernetes (EKS) are the deployment standard.
2. **Encoding farm:** GPU instances (NVIDIA T4 via `g4dn.xlarge`) are available on-demand and via Spot instances for non-time-sensitive batch jobs.
3. **DRM keys:** A CPIX-compatible key management service is available (AWS Elemental MediaConvert or a self-managed CPIX server); Widevine and FairPlay credentials are pre-provisioned.
4. **Content rights:** The platform has a legal framework for creator-uploaded content (ToS, DMCA agent registration, Content ID integration) before launch.
5. **Email volume:** SES sending limits will be raised to 1M emails/day before launch; the platform will not use SES for bulk marketing (separate ESP for that).
6. **Payment volumes:** Stripe has confirmed processing capacity for projected launch volumes; PCI SAQ A-EP is in scope.
7. **CDN contracts:** CloudFront and Akamai contracts with committed usage tiers are in place; pricing per GB is locked for 12 months.
8. **ASR accuracy:** Whisper large-v3 achieves < 5% WER on English content; non-English accuracy varies; creators are expected to review auto-generated captions.
9. **Mobile platforms:** iOS 14+ and Android 8+ are the minimum supported versions.
10. **Browser support:** Chrome 80+, Firefox 80+, Safari 14+, Edge 80+; Internet Explorer is not supported.

---

## 8. Glossary

| Term | Definition |
|---|---|
| **ABR** | Adaptive Bitrate Streaming: technique of encoding content at multiple quality levels and switching between them based on available bandwidth |
| **ALS** | Alternating Least Squares: matrix factorisation algorithm used for collaborative filtering recommendations |
| **ASR** | Automatic Speech Recognition: transcription of audio to text; Whisper used here |
| **CMAF** | Common Media Application Format (ISO 23000-19): a packaging standard that unifies HLS and DASH into a single set of media files |
| **CPIX** | Content Protection Information Exchange Format (DASH-IF): XML schema for exchanging DRM keys between key server and packager |
| **CTE** | Chunked Transfer Encoding: HTTP mechanism for streaming data in chunks; used in CMAF-CTE for low-latency DASH |
| **DVR** | Digital Video Recording: ability to pause and rewind a live stream within a time window |
| **DASH** | Dynamic Adaptive Streaming over HTTP (ISO 23009-1): open streaming standard using MPD manifests |
| **DRM** | Digital Rights Management: technology to control usage of copyrighted digital content |
| **FPS** | FairPlay Streaming: Apple's DRM system for HLS content |
| **HLS** | HTTP Live Streaming (RFC 8216): Apple's adaptive streaming protocol using `.m3u8` playlists |
| **LL-HLS** | Low-Latency HLS: extension to HLS spec using partial segments (parts) to reduce live latency |
| **MPAA** | Motion Picture Association of America: issues content ratings (G, PG, PG-13, R, NC-17) |
| **MPD** | Media Presentation Description: XML manifest file used by MPEG-DASH |
| **NVENC** | NVIDIA Video Encoder: hardware-accelerated video encoding on NVIDIA GPUs |
| **PPV** | Pay-Per-View: content purchase model for one-time access (rental or buy) |
| **QoE** | Quality of Experience: composite metric of playback quality from the viewer's perspective |
| **RTMP** | Real-Time Messaging Protocol: TCP-based protocol used for live stream ingest |
| **SSAI** | Server-Side Ad Insertion: ads are stitched into the media stream server-side, bypassing client-side ad blockers |
| **SRT** | Secure Reliable Transport: UDP-based protocol with ARQ/FEC for reliable video delivery over unreliable networks |
| **TUS** | Tus Resumable Upload Protocol (tus.io): open protocol for resumable HTTP file uploads |
| **VAST** | Video Ad Serving Template: XML-based standard for serving video ads |
| **VMAP** | Video Multiple Ad Playlist: XML standard for defining multiple ad breaks in a video |
| **VOD** | Video on Demand: pre-recorded content available for streaming at any time |
| **WebRTC** | Web Real-Time Communication: browser standard for real-time audio/video communication |
| **WER** | Word Error Rate: measure of ASR accuracy; percentage of words incorrectly transcribed |

---

*Document maintained by Platform Engineering. Changes require review from Product, Engineering, and Legal leads.*
