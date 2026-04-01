# User Stories — Video Streaming Platform

## Summary Table

| Story ID | Title                              | Role            | Priority |
|----------|------------------------------------|-----------------|----------|
| US-001   | Viewer Registration & Profile Setup | Viewer         | High     |
| US-002   | Content Search and Discovery       | Viewer          | High     |
| US-003   | VOD Playback with Adaptive Bitrate | Viewer          | High     |
| US-004   | DRM-Protected Content Playback     | Viewer          | High     |
| US-005   | Subscription Plan Purchase         | Viewer          | High     |
| US-006   | Concurrent Stream Enforcement      | Viewer          | High     |
| US-007   | Offline Content Download           | Viewer          | Medium   |
| US-008   | Parental Controls and Ratings      | Viewer          | Medium   |
| US-009   | Subtitles and Closed Captions      | Viewer          | Medium   |
| US-010   | Notification Preferences           | Viewer          | Low      |
| US-011   | Personalised Recommendations       | Viewer          | High     |
| US-012   | Resume Playback Across Devices     | Viewer          | Medium   |
| US-013   | Watchlist Management               | Viewer          | Medium   |
| US-014   | Live Stream Viewing                | Viewer          | High     |
| US-015   | Geo-Restriction Notification       | Viewer          | Medium   |
| US-016   | Content Upload                     | Content Creator | High     |
| US-017   | Transcoding Status Monitoring      | Content Creator | High     |
| US-018   | Live Stream Setup and Broadcast    | Content Creator | High     |
| US-019   | Creator Analytics Dashboard        | Content Creator | High     |
| US-020   | DMCA Counter-Notice Submission     | Content Creator | Medium   |
| US-021   | Geo-Restriction Configuration      | Content Creator | Medium   |
| US-022   | Subtitle and Caption Management    | Content Creator | Medium   |
| US-023   | DRM Licensing Configuration        | Content Creator | Medium   |
| US-024   | Content Moderation Review          | Admin           | High     |
| US-025   | DMCA Takedown Processing           | Admin           | High     |
| US-026   | User Account Management            | Admin           | High     |
| US-027   | Platform-Wide Analytics            | Admin           | High     |
| US-028   | DRM Key and Policy Management      | Admin           | High     |
| US-029   | Ad Campaign Creation               | Advertiser      | High     |
| US-030   | Audience Targeting Configuration   | Advertiser      | High     |
| US-031   | Ad Performance Analytics           | Advertiser      | Medium   |
| US-032   | Ad Frequency Cap Management        | Advertiser      | Medium   |
| US-033   | Mid-Roll Ad Placement Rules        | Advertiser      | Medium   |

---

### US-001 — Viewer Registration and Profile Setup

**As a** Viewer **I want to** register an account and create named profiles **so that** my viewing history, preferences, and subscription are persisted across all my devices.

**Acceptance Criteria:**
- Registration completes via email/password, Google OAuth 2.0, Apple Sign-In, or SMS OTP within 30 seconds.
- The platform sends an email or SMS verification within 60 seconds of account creation.
- Up to five named profiles can be created under one account, each with an independent watch history and recommendation model.
- A profile can be marked as "Kids" to enforce age-appropriate content filtering automatically across search, browse, and recommendations.
- Duplicate email or username submissions are rejected before account creation with a user-readable conflict message.

**Priority:** High
**Effort:** M

---

### US-002 — Content Search and Discovery

**As a** Viewer **I want to** search for videos by title, genre, cast, or keyword **so that** I can quickly locate content without browsing multiple category pages.

**Acceptance Criteria:**
- Full-text search returns results within 300 ms at p95 for a catalogue of one million titles.
- Results display thumbnail, duration, content rating, and subscription-tier availability badge.
- Autocomplete suggestions appear after the third keystroke with a maximum latency of 150 ms.
- Filters for genre, language, release year, and content rating apply without a full page reload.
- Geo-restricted content is suppressed from results for the requesting viewer's region.

**Priority:** High
**Effort:** M

---

### US-003 — VOD Playback with Adaptive Bitrate

**As a** Viewer **I want to** start a video-on-demand title and have the player automatically select the best quality for my current network **so that** I experience smooth, uninterrupted playback regardless of fluctuating bandwidth.

**Acceptance Criteria:**
- The player begins buffering within 2 seconds of the user pressing play on a standard broadband connection.
- DASH and HLS manifests are served with at least five bitrate variants ranging from 240p to 4K where the asset is available.
- The ABR algorithm switches quality levels without visible stutter under a simulated 50 % bandwidth reduction.
- A manual quality selector allows the viewer to override automatic selection at any time during playback.
- Buffering events lasting more than 5 seconds are captured as a `PlaybackBufferingEvent` and forwarded to the analytics pipeline.

**Priority:** High
**Effort:** L

---

### US-004 — DRM-Protected Content Playback

**As a** Viewer **I want to** play DRM-protected premium content on my device **so that** I can access the content I have paid for while the platform ensures copyright compliance.

**Acceptance Criteria:**
- Widevine, FairPlay, and PlayReady licence acquisition completes within 1 second on a 4G connection.
- A licence is issued only to viewers whose active subscription tier grants access to the requested content.
- Expired or revoked licences trigger an in-player error overlay with a "Renew Subscription" call to action.
- Offline licences are bound to the device and expire after 7 days for Basic subscribers or 30 days for Premium.
- Every licence request is logged with user ID, content ID, device fingerprint, DRM system, and timestamp for compliance auditing.

**Priority:** High
**Effort:** L

---

### US-005 — Subscription Plan Purchase

**As a** Viewer **I want to** choose and purchase a subscription plan using a credit card, PayPal, or App Store billing **so that** I can unlock ad-free or higher-quality content immediately after payment.

**Acceptance Criteria:**
- Three plans are available: Free (ad-supported, SD only), Basic ($7.99/mo, HD, 2 concurrent streams), Premium ($14.99/mo, 4K HDR, 4 streams, offline downloads).
- Payment is processed via Stripe or PayPal; raw card data is never exposed in the platform UI.
- The subscription tier is updated in the entitlement service within 5 seconds of a successful payment event.
- Failed payments trigger an automated retry schedule at 1 day, 3 days, and 7 days before the subscription is downgraded.
- A pro-rated credit is calculated and applied when a viewer upgrades from Basic to Premium mid-billing cycle.

**Priority:** High
**Effort:** L

---

### US-006 — Concurrent Stream Enforcement

**As a** Viewer **I want to** stream on multiple devices simultaneously up to my plan limit **so that** household members can watch independently on their own devices.

**Acceptance Criteria:**
- Free tier permits 1 concurrent stream; Basic permits 2; Premium permits 4.
- Exceeding the limit displays an error that lists all active sessions with a "Stop Other Stream" action per session.
- Concurrency enforcement completes within 500 ms of a new playback session being registered.
- Session concurrency state is stored in a distributed cache with a TTL equal to the HLS segment duration plus a 60-second grace window.
- A session terminated remotely via the active-sessions UI surfaces a graceful session-ended overlay on the affected device.

**Priority:** High
**Effort:** M

---

### US-007 — Offline Content Download

**As a** Viewer **I want to** download episodes and films to my mobile device over Wi-Fi **so that** I can watch them later without an internet connection while travelling.

**Acceptance Criteria:**
- Offline downloads are available exclusively to Premium subscribers.
- A maximum of 25 titles can be stored offline per profile at any one time.
- Downloaded content is DRM-bound to the device and cannot be transferred or played on another device.
- The offline licence expires after 30 days or 48 hours after first play, whichever occurs first.
- When a title is removed from the platform, the downloaded copy is invalidated and deleted on the next app launch.

**Priority:** Medium
**Effort:** L

---

### US-008 — Parental Controls and Content Ratings

**As a** Viewer **I want to** set a PIN-protected content rating ceiling on a Kids profile **so that** my children cannot access content rated above the configured threshold.

**Acceptance Criteria:**
- Supported rating systems: MPAA (G, PG, PG-13, R, NC-17), BBFC, FSK, and regional equivalents configurable per account.
- A parental PIN must be set by the account owner before restrictions can be activated on any profile.
- Content above the rating ceiling is hidden from search results, browse grids, autoplay queues, and recommendations.
- Accessing a restricted title via a direct link prompts for the parental PIN rather than silently failing or returning a blank page.
- A PIN-granted override for a specific session expires when the current playback session ends.

**Priority:** Medium
**Effort:** M

---

### US-009 — Subtitles and Closed Captions

**As a** Viewer **I want to** enable subtitles in my preferred language and customise caption appearance **so that** I can follow content in foreign languages or when audio output is unavailable.

**Acceptance Criteria:**
- Caption tracks are available in at least the original content language and English for all premium titles.
- Subtitle preferences (font family, size, colour, text edge style, background opacity) persist per profile across sessions and devices.
- Captions are delivered as WebVTT sidecar files or as TTML tracks embedded in DASH manifests.
- When a sidecar track is unavailable, the player falls back to burnt-in subtitles without interrupting playback.
- Auto-generated captions produced by the speech-recognition pipeline are clearly labelled "Auto-generated" in the subtitle selector.

**Priority:** Medium
**Effort:** M

---

### US-010 — Notification Preferences

**As a** Viewer **I want to** configure which notifications I receive from the platform **so that** I am kept informed about relevant events without being overwhelmed by alerts.

**Acceptance Criteria:**
- Notification channels: email, in-app banner, iOS/Android push notification, and SMS.
- Notification categories: new episode released, live stream starting soon, subscription renewal reminder, and promotional offers.
- Disabling a category stops new deliveries within 1 hour of the preference being saved.
- Scheduled event notifications respect the viewer's configured time zone.
- Notification history is accessible in account settings with a 90-day retention window and individual mark-as-read controls.

**Priority:** Low
**Effort:** S

---

### US-011 — Personalised Recommendations

**As a** Viewer **I want to** receive content recommendations tailored to my watch history and explicit ratings **so that** I can discover new titles aligned with my tastes without extensive manual browsing.

**Acceptance Criteria:**
- The recommendation engine refreshes each profile's suggestion list at least once every 24 hours.
- Explicit "thumbs up / thumbs down" signals are incorporated into the model within 30 minutes of submission.
- The home screen displays at minimum three recommendation rows: "Because you watched X", "Top picks for you", and "Continue watching".
- Recommendations exclude titles the profile has already completed within the past 30 days.
- The model must never surface content above the profile's active parental rating ceiling.

**Priority:** High
**Effort:** L

---

### US-012 — Resume Playback Across Devices

**As a** Viewer **I want to** continue watching a video from where I left off on any of my registered devices **so that** I do not lose my position when switching between phone, tablet, and TV.

**Acceptance Criteria:**
- Playback position is stored server-side within 10 seconds of the viewer pausing or stopping.
- A "Continue Watching" row on the home screen shows all titles with in-progress playback for the active profile.
- The position synchronises across all devices on the profile within 15 seconds of being saved.
- Titles where playback progress exceeds 90 % are considered complete and removed from "Continue Watching".
- The position is stored per profile rather than per device, enabling seamless cross-device handoff.

**Priority:** Medium
**Effort:** S

---

### US-013 — Watchlist Management

**As a** Viewer **I want to** save titles to a personal watchlist **so that** I can find content I intend to watch later without repeating a search.

**Acceptance Criteria:**
- A viewer can add or remove a title from their watchlist with a single tap or click from any browse or detail page.
- Watchlists are profile-scoped and support up to 500 entries.
- The watchlist page shows thumbnail, title, runtime, content rating, and subscription-tier badge for each entry.
- Entries are ordered by date added (newest first) by default, with optional drag-to-reorder capability.
- When a watchlisted title becomes unavailable in the viewer's region, an in-app notification is sent within 24 hours.

**Priority:** Medium
**Effort:** S

---

### US-014 — Live Stream Viewing

**As a** Viewer **I want to** watch a live broadcast with a real-time chat panel **so that** I can engage with events and creator content as they happen.

**Acceptance Criteria:**
- A viewer can join a live stream within 5 seconds of selecting it from the live events discovery page.
- The active latency mode is shown in the player HUD: Standard (≤ 30 s), Low-latency (≤ 8 s), or Ultra-low (≤ 2 s).
- The chat panel renders new messages with a maximum 1-second display delay.
- When the broadcast concludes, the archived VOD recording is available for playback within 30 minutes.
- The player displays a pulsing "LIVE" indicator and a viewer count refreshed every 30 seconds.

**Priority:** High
**Effort:** L

---

### US-015 — Geo-Restriction Notification

**As a** Viewer **I want to** receive a clear, localised explanation when a title is unavailable in my region **so that** I understand why access is blocked and what options are available to me.

**Acceptance Criteria:**
- When a geo-blocked title is requested, the player shows a message specifying that the content is not available in the viewer's country.
- Geo-blocked content does not appear in search results or browse carousels for restricted regions.
- If a VPN or proxy is detected via IP reputation scoring, the platform enforces the content's licensing jurisdiction and logs the event.
- The viewer is offered a link to a regional availability FAQ page from the error screen.
- Geo-restriction rule evaluation completes within 100 ms of the playback request using IP-based geolocation.

**Priority:** Medium
**Effort:** M

---

### US-016 — Content Upload

**As a** Content Creator **I want to** upload video files up to 50 GB in size along with metadata **so that** my content is ingested, processed, and distributed to viewers efficiently.

**Acceptance Criteria:**
- Supported source formats: MP4 (H.264 / H.265), MOV, MKV, AVI, and Apple ProRes 422/4444.
- Multi-part resumable upload allows resuming after a network interruption without restarting from byte zero.
- Upload progress is shown as a percentage with an estimated time to completion updated every 30 seconds.
- Files exceeding 50 GB or a source resolution above 4K (3840 × 2160) are rejected immediately with a descriptive error.
- Metadata fields (title, description, genre, language, content rating, tags) can be filled concurrently with the upload.

**Priority:** High
**Effort:** L

---

### US-017 — Transcoding Status Monitoring

**As a** Content Creator **I want to** track the transcoding status of my uploaded video in real time **so that** I know when my content will be published and can diagnose failures promptly.

**Acceptance Criteria:**
- The upload dashboard displays a pipeline stage indicator: Queued → Downloading Source → Transcoding → Packaging → Publishing → Complete.
- A progress bar shows the percentage completion of the active transcoding stage, updated every 15 seconds.
- Estimated completion time is recalculated every 60 seconds using observed worker throughput.
- Transcoding failures present an error code and human-readable description, and trigger an email notification to the creator.
- Ninety percent of uploads complete the full transcoding pipeline within 10 minutes of the source file being available in object storage.

**Priority:** High
**Effort:** M

---

### US-018 — Live Stream Setup and Broadcast

**As a** Content Creator **I want to** configure and start a live stream using standard RTMP or SRT ingest **so that** I can broadcast to my audience using any standard encoding software without proprietary plugins.

**Acceptance Criteria:**
- The platform generates a unique, per-event stream key and ingest endpoint supporting both RTMP and SRT protocols.
- Stream keys can be rotated by the creator at any time; the previous key expires within 60 seconds of rotation.
- The creator dashboard displays a real-time ingest preview with audio level meters and ingest bitrate metrics.
- Live transcoding to ABR renditions begins within 5 seconds of the ingest connection being established and authenticated.
- A test broadcast mode allows verifying encoding settings and preview quality without publishing the stream to any viewer.

**Priority:** High
**Effort:** L

---

### US-019 — Creator Analytics Dashboard

**As a** Content Creator **I want to** view detailed analytics for my content including views, watch time, audience retention, and revenue **so that** I can make informed decisions about my content strategy.

**Acceptance Criteria:**
- Analytics data is updated with a maximum 5-minute delay from the underlying event stream.
- Displayed metrics include total views, unique viewers, average watch duration, audience retention curve, geographic distribution, device breakdown, and revenue per mille (RPM).
- All data can be exported as CSV for any rolling 90-day window with a single click.
- Audience retention charts show viewer drop-off at 30-second granularity across the video timeline.
- Revenue figures are broken down by ad revenue, subscription-share allocation, and paid-content direct sales.

**Priority:** High
**Effort:** L

---

### US-020 — DMCA Counter-Notice Submission

**As a** Content Creator **I want to** submit a formal DMCA counter-notice when I believe a takedown was issued in error **so that** my content is restored if my counter-notice is legally valid.

**Acceptance Criteria:**
- A counter-notice submission form is accessible from the takedown notification within the creator dashboard.
- Required fields include a good-faith belief statement, the creator's personal information, and consent to jurisdiction.
- An automated submission confirmation is sent to the creator's registered email within 5 minutes.
- The platform notifies the original claimant within 24 hours of a valid counter-notice being filed.
- If the claimant initiates no legal action within 10 business days, the content is automatically restored and the creator is notified.

**Priority:** Medium
**Effort:** M

---

### US-021 — Geo-Restriction Configuration

**As a** Content Creator **I want to** restrict or allow my content in specific countries **so that** I can comply with the territorial licensing agreements associated with my content.

**Acceptance Criteria:**
- The creator can configure an allowlist or blocklist of ISO 3166-1 alpha-2 country codes per content item.
- Restriction rules take effect within 5 minutes of being saved via the content management interface.
- The default behaviour when no restriction is configured is global availability.
- Regional availability status is visible to platform admins in the content management console.
- All restriction changes are written to an audit trail recording the creator's user ID, IP address, and timestamp.

**Priority:** Medium
**Effort:** S

---

### US-022 — Subtitle and Caption Management

**As a** Content Creator **I want to** upload caption files and associate them with specific language tracks on my video **so that** my content is accessible to audiences in multiple languages.

**Acceptance Criteria:**
- Supported caption upload formats: WebVTT (.vtt), SubRip (.srt), and TTML (.ttml).
- Multiple caption tracks can be attached per content item; each track carries a BCP-47 language tag.
- The creator can designate a track as the default for a given language; the player selects this track automatically.
- Uploaded files are validated for timing overlaps and malformed tags; validation errors identify the offending line number.
- Auto-generated captions produced by the platform can be reviewed and edited in an inline web editor before being published.

**Priority:** Medium
**Effort:** M

---

### US-023 — DRM Licensing Configuration

**As a** Content Creator **I want to** configure DRM policies for my premium content **so that** my intellectual property is protected in accordance with my distribution requirements.

**Acceptance Criteria:**
- Available DRM systems: Widevine (Security Levels L1–L3), FairPlay, and PlayReady.
- Licence duration options: 24 hours, 7 days, 30 days, or perpetual (subscription-gated renewal).
- Maximum simultaneous device playbacks per licence: 1, 2, or 4, configurable per content item.
- Content flagged as DRM-required cannot be published unless a valid encryption configuration has been applied.
- DRM configuration changes apply to all new licence requests immediately; existing valid licences are not revoked retroactively.

**Priority:** Medium
**Effort:** M

---

### US-024 — Content Moderation Review

**As an** Admin **I want to** review content flagged by the automated moderation system **so that** policy-violating material is actioned before it reaches a wide audience.

**Acceptance Criteria:**
- The moderation queue displays flagged items sorted by confidence score descending, with highest-severity items first.
- Each queue item shows the automated flag reason, a thumbnail and 30-second preview clip, full metadata, and creator details.
- Available actions are: Approve, Remove with mandatory reason code, or Escalate to the legal team.
- All moderation decisions are logged with moderator ID, timestamp, action taken, and reason code in an immutable audit record.
- An SLA dashboard displays the percentage of flagged items reviewed within 24 hours, with a target of 95 %.

**Priority:** High
**Effort:** M

---

### US-025 — DMCA Takedown Processing

**As an** Admin **I want to** process incoming DMCA takedown notices and track their resolution status **so that** the platform meets its safe-harbour obligations under the DMCA.

**Acceptance Criteria:**
- The DMCA intake form captures: claimant identity, contact details, description of the infringed work, URL of the infringing content, and required sworn statements.
- An acknowledgement is sent to the claimant within 24 hours of a notice being received.
- Infringing content is removed or access-restricted within 48 hours of the notice being validated by the legal team.
- The content creator is notified of the takedown with the stated reason and step-by-step counter-notice instructions.
- All DMCA case records, correspondence, and decisions are retained for a minimum of 3 years.

**Priority:** High
**Effort:** M

---

### US-026 — User Account Management

**As an** Admin **I want to** view, suspend, and permanently delete user accounts **so that** I can enforce platform terms of service and respond to verified abuse reports.

**Acceptance Criteria:**
- Admin search retrieves an account by email address, username, or user ID within 500 ms.
- Suspension immediately revokes all active session tokens and outstanding DRM playback licences for the account.
- Permanent deletion anonymises all personally identifiable information within 30 days in compliance with GDPR Article 17 and CCPA.
- Every admin action on an account is written to an immutable audit log recording the admin's user ID, action, reason, and IP address.
- Bulk suspension of up to 100 accounts is supported via a structured CSV import with per-row result reporting.

**Priority:** High
**Effort:** M

---

### US-027 — Platform-Wide Analytics

**As an** Admin **I want to** view real-time and historical dashboards covering streaming volume, error rates, CDN performance, and revenue **so that** I can monitor platform health and business performance from a single pane of glass.

**Acceptance Criteria:**
- The admin analytics dashboard refreshes every 60 seconds using a streaming aggregation pipeline.
- KPIs displayed: peak concurrent viewers, total streams initiated, playback error rate, CDN cache-hit ratio, and monthly recurring revenue.
- Historical data ranges available: rolling 7-day, 30-day, 90-day, 1-year, and all-time.
- Configurable threshold alerts trigger when any KPI breaches a set value (example: playback error rate > 2 %).
- Dashboard data is exportable as CSV and accessible via a read-only REST analytics API with OAuth 2.0 authentication.

**Priority:** High
**Effort:** L

---

### US-028 — DRM Key and Policy Management

**As an** Admin **I want to** manage DRM encryption keys, rotate them on a schedule, and audit all licence grants **so that** the platform's content protection infrastructure remains secure and audit-ready.

**Acceptance Criteria:**
- Content encryption keys (CEK) are stored exclusively in an HSM-backed key management service; no key material is persisted on application servers.
- Key rotation can be triggered manually or configured on a schedule with a minimum rotation interval of 30 days.
- The admin console lists all active DRM policies with licence issuance counts, creation dates, and expiry timestamps.
- Revoking an encryption key renders all associated licences invalid and initiates re-encryption of the affected content within 4 hours.
- All key access and rotation events are logged in an immutable audit trail exportable in SIEM-compatible JSON format.

**Priority:** High
**Effort:** L

---

### US-029 — Ad Campaign Creation

**As an** Advertiser **I want to** create a video ad campaign with targeting parameters and budget constraints **so that** my ads are displayed to the most relevant audience within a controlled spend.

**Acceptance Criteria:**
- Campaign creation supports pre-roll, mid-roll, and post-roll placement types.
- Targeting parameters include: genre, content rating, geography (country and region), device type, viewer age bracket, and time of day.
- Daily budget and total campaign budget caps are enforced within a 5 % tolerance by the ad-serving engine.
- Creative assets must be MP4 format, 16:9 aspect ratio, ≤ 100 MB, and between 15 and 60 seconds in duration.
- A pre-launch preview shows estimated daily impressions, projected reach, and CPM forecast before the campaign goes live.

**Priority:** High
**Effort:** L

---

### US-030 — Audience Targeting Configuration

**As an** Advertiser **I want to** define custom audience segments based on aggregated viewing behaviour **so that** I can target viewers most likely to engage with my brand message.

**Acceptance Criteria:**
- Segments are built using combinations of: genres watched in the past 30 days, subscription tier, device type, and geographic region.
- Segment size estimates update in real time as targeting criteria are added or removed.
- A minimum segment size of 10,000 anonymised viewers is required before a campaign can be activated against the segment.
- Audience data shared with advertisers is always anonymised and aggregated; no PII is accessible to any advertiser account.
- Segments are recalculated nightly; active campaign targeting updates automatically to reflect the latest composition.

**Priority:** High
**Effort:** M

---

### US-031 — Ad Performance Analytics

**As an** Advertiser **I want to** view detailed performance metrics for my running and completed campaigns **so that** I can optimise creative selection and targeting decisions to maximise return on ad spend.

**Acceptance Criteria:**
- Metrics reported: impressions served, video completion rate, skip rate, click-through rate (CTR), cost per mille (CPM), and VAST-standard viewability score.
- Data refreshes every 15 minutes during an active campaign and within 1 hour of campaign completion.
- All metrics are breakable by date, placement type (pre/mid/post-roll), device category, and geographic region.
- An A/B creative comparison view is available when two or more creative assets are active within the same campaign.
- Performance reports are exportable as CSV and accessible via the platform Reporting API with advertiser-scoped OAuth tokens.

**Priority:** Medium
**Effort:** M

---

### US-032 — Ad Frequency Cap Management

**As an** Advertiser **I want to** set a frequency cap so that a viewer does not see my ad more than a specified number of times within a rolling time window **so that** I minimise ad fatigue and optimise budget distribution.

**Acceptance Criteria:**
- Frequency caps are configurable per campaign as X impressions per Y hours, with a minimum cap of 1 impression per 1 hour.
- The cap state is tracked per anonymised viewer identifier and enforced within a single ad-decision cycle of ≤ 200 ms.
- When a viewer has reached the cap, the ad server selects the next eligible campaign for the same slot without increasing the viewer's wait time.
- Frequency cap values can be updated on a live campaign; the revised cap applies from the next ad-decision cycle onwards.
- Cap telemetry is retained for 90 days to support billing reconciliation and impression audit requests.

**Priority:** Medium
**Effort:** M

---

### US-033 — Mid-Roll Ad Placement Rules

**As an** Advertiser **I want to** have mid-roll ads inserted at creator-approved break points in longer content for Basic subscribers **so that** my ads appear at natural, non-disruptive moments in the viewing experience.

**Acceptance Criteria:**
- Mid-roll ads are only inserted into content with a published runtime of 8 minutes or longer.
- Ad break markers are set by the content creator during upload or detected automatically by a scene-change analysis pass.
- A minimum gap of 8 minutes must separate any two consecutive mid-roll ad breaks in the same piece of content.
- Mid-roll ad breaks are not placed within 60 seconds of the content start or within 120 seconds of the content end.
- Premium subscribers are never served mid-roll ads; tier enforcement is applied at the ad-decision layer before any creative is selected.

**Priority:** Medium
**Effort:** M
