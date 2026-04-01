# System Sequence Diagrams

This document captures the most critical runtime interactions in the Video Streaming Platform using
UML-style sequence diagrams rendered in Mermaid. Three scenarios are covered: authenticated video
playback protected by DRM, the creator upload-and-transcoding pipeline, and live stream setup with
real-time broadcast delivery.

---

## Video Playback with DRM

The following diagram traces every interaction from the moment a viewer presses **Play** through
license acquisition, manifest resolution, and adaptive bitrate segment delivery via CDN.

```mermaid
sequenceDiagram
    autonumber
    actor Viewer
    participant PlayerSDK   as Player SDK
    participant APIGW       as API Gateway
    participant PlaybackSvc as Playback Service
    participant AuthSvc     as Auth Service
    participant DRMServer   as DRM License Server
    participant CDN         as CDN (Cloudflare/Akamai)

    Viewer->>PlayerSDK: press Play (contentId, quality=auto)
    PlayerSDK->>APIGW: GET /playback/token {contentId, deviceFingerprint}
    APIGW->>AuthSvc: validateSession(sessionJWT)
    AuthSvc-->>APIGW: sessionValid=true, userId, subscriptionTier
    APIGW->>PlaybackSvc: issuePlaybackToken(userId, contentId, tier)
    PlaybackSvc->>AuthSvc: checkEntitlement(userId, contentId)
    AuthSvc-->>PlaybackSvc: entitled=true, licenseTemplate
    PlaybackSvc-->>APIGW: playbackToken (JWT, 15min TTL), manifestURL
    APIGW-->>PlayerSDK: 200 {playbackToken, manifestURL, drmType}
    PlayerSDK->>CDN: GET manifestURL (HLS master.m3u8 or DASH .mpd)
    CDN->>PlaybackSvc: origin pull — manifest not cached
    PlaybackSvc-->>CDN: manifest bytes (Cache-Control: max-age=10)
    CDN-->>PlayerSDK: master manifest (variant streams + DRM init data)
    PlayerSDK->>PlayerSDK: parse manifest, select 1080p rendition
    PlayerSDK->>CDN: GET rendition playlist (1080p/playlist.m3u8)
    CDN-->>PlayerSDK: rendition playlist (segment URLs + EXT-X-KEY)
    Note over PlayerSDK: DRM initialization data parsed from manifest
    PlayerSDK->>DRMServer: POST /license {drmChallenge, playbackToken, deviceId}
    DRMServer->>AuthSvc: verifyPlaybackToken(playbackToken)
    AuthSvc-->>DRMServer: valid=true, userId, contentId, policy
    DRMServer->>DRMServer: generate Widevine/FairPlay license (policy enforcement)
    DRMServer-->>PlayerSDK: 200 DRM license (encrypted content key)
    PlayerSDK->>PlayerSDK: install license in CDM (Content Decryption Module)
    PlayerSDK->>CDN: GET segment_001.ts (or .m4s for CMAF)
    CDN-->>PlayerSDK: encrypted segment bytes (from edge cache)
    PlayerSDK->>PlayerSDK: decrypt segment, decode H.264/H.265, render frame
    PlayerSDK->>CDN: GET segment_002.ts
    CDN-->>PlayerSDK: encrypted segment bytes
    PlayerSDK->>CDN: GET segment_003.ts
    CDN-->>PlayerSDK: encrypted segment bytes
    Note over PlayerSDK: ABR algorithm monitors bandwidth every 3 segments
    PlayerSDK->>CDN: GET rendition playlist (720p/playlist.m3u8) [ABR downgrade]
    CDN-->>PlayerSDK: 720p rendition playlist
    PlayerSDK->>CDN: GET segment_004_720p.ts
    CDN-->>PlayerSDK: encrypted segment bytes
    PlayerSDK->>APIGW: POST /playback/heartbeat {contentId, position, bitrate, buffering}
    APIGW->>PlaybackSvc: recordHeartbeat(userId, contentId, position, bitrateKbps)
    PlaybackSvc-->>APIGW: 204 No Content
    APIGW-->>PlayerSDK: 204 No Content
    PlayerSDK->>APIGW: POST /playback/heartbeat {position=300s}
    APIGW->>PlaybackSvc: recordHeartbeat(userId, contentId, position=300)
    PlaybackSvc-->>APIGW: 204 No Content
    Note over DRMServer: License TTL expires — renewal triggered
    PlayerSDK->>DRMServer: POST /license/renew {renewalToken, playbackToken}
    DRMServer->>AuthSvc: verifyPlaybackToken(playbackToken)
    AuthSvc-->>DRMServer: valid=true
    DRMServer-->>PlayerSDK: 200 renewed DRM license
    PlayerSDK->>APIGW: POST /playback/complete {contentId, watchDuration, completionPct}
    APIGW->>PlaybackSvc: markWatchComplete(userId, contentId, watchDuration)
    PlaybackSvc-->>APIGW: 204 No Content
    APIGW-->>PlayerSDK: 204 No Content
    PlayerSDK-->>Viewer: playback complete
```

### Playback Flow — Design Rationale

The playback token architecture decouples authentication from DRM licensing. The API Gateway
validates the user's long-lived session JWT and then delegates to the Playback Service to mint a
short-lived (15-minute) playback token scoped to a specific content item and device. This limits
the blast radius of a stolen session: even if a playback token is intercepted, it cannot be used
to access other content or generate new tokens.

DRM license acquisition occurs after the manifest is fetched so that the Player SDK has the precise
DRM system identifier (Widevine, FairPlay, or PlayReady) and initialization data embedded in the
manifest. The DRM License Server re-validates the playback token on every license request — it
does not cache the entitlement check — ensuring that a subscriber who cancels mid-stream loses
license renewal on the next TTL expiry, typically within 10–15 minutes, without requiring active
session revocation.

Heartbeat events serve dual purposes: they feed the resume-position feature (so viewers can pick
up where they left off on any device) and provide real-time engagement telemetry to the Analytics
pipeline. The 30-second heartbeat interval is a deliberate balance between data granularity and
API Gateway load; the interval is configurable per subscription tier, with premium subscribers
receiving 10-second granularity for richer analytics.

### Playback — Failure Modes and Fallbacks

Several failure paths are handled gracefully in this flow:

- **DRM License Server unavailable:** The Player SDK retries license acquisition three times
  with 1-second exponential backoff before surfacing an error to the viewer. The Playback
  Service returns a distinct `503 DRM_UNAVAILABLE` error code that the player renders as a
  specific user message rather than a generic error, preserving user trust.
- **CDN segment unavailability:** When a segment request to the CDN returns a 404 or 5xx, the
  Player SDK falls back to the origin URL embedded in the manifest as an `EXT-X-MAP` alternative.
  This origin fallback URL routes through the API Gateway to the Streaming Service, which proxies
  the segment directly from S3. This path is significantly slower but prevents complete playback
  failure during CDN incidents.
- **Heartbeat loss:** Heartbeat failures are silently swallowed by the Player SDK — the viewer
  is never informed of a failed heartbeat. The last successfully acknowledged position is used
  for resume. If all heartbeats in a session fail (e.g., complete backend outage), the player
  stores the position in localStorage and syncs it on next app launch.
- **Concurrent stream limit exceeded:** When the Playback Service detects that the subscriber's
  concurrent stream limit is reached (checked via the Redis counter), it returns `403
  CONCURRENT_LIMIT_EXCEEDED`. The Player SDK displays a stream management prompt allowing the
  viewer to terminate another active session before retrying. This UX avoids frustrating the
  viewer with an opaque error and preserves the subscription service's session count accuracy.

---

## Video Upload and Transcoding Pipeline

This diagram covers the creator's journey from selecting a file in Creator Studio to a fully
transcoded, CDN-distributed video asset with viewer notification.

```mermaid
sequenceDiagram
    autonumber
    actor Creator
    participant Studio      as Creator Studio
    participant APIGW       as API Gateway
    participant UploadSvc   as Upload Service
    participant S3          as Object Storage (S3)
    participant Transcoder  as Transcoding Service
    participant CDN         as CDN (Cloudflare/Akamai)
    participant NotifSvc    as Notification Service

    Creator->>Studio: select file (video.mp4, 4 GB), add metadata
    Studio->>APIGW: POST /uploads/initiate {filename, size, mimeType, metadata}
    APIGW->>UploadSvc: initiateMultipartUpload(creatorId, filename, size)
    UploadSvc->>S3: CreateMultipartUpload(bucket=raw-ingestion, key=uploads/{uploadId}/video.mp4)
    S3-->>UploadSvc: uploadId, presignedUrlSet (part 1..N, 100 MB each)
    UploadSvc-->>APIGW: 201 {uploadId, presignedUrls[], totalParts=40}
    APIGW-->>Studio: 201 {uploadId, presignedUrls[], totalParts}
    loop Upload each 100 MB chunk (parts 1..40)
        Studio->>S3: PUT presignedUrl_N (chunk bytes, Content-MD5)
        S3-->>Studio: 200 {ETag: "abc123"}
        Studio->>Studio: store ETag for part N
        Studio->>APIGW: POST /uploads/{uploadId}/progress {partNumber, etag}
        APIGW->>UploadSvc: recordPartProgress(uploadId, partNumber, etag)
        UploadSvc-->>APIGW: 204 No Content
        APIGW-->>Studio: 204 No Content
    end
    Studio->>APIGW: POST /uploads/{uploadId}/complete {parts:[{partNumber,etag}]}
    APIGW->>UploadSvc: completeMultipartUpload(uploadId, parts)
    UploadSvc->>S3: CompleteMultipartUpload(uploadId, parts)
    S3-->>UploadSvc: 200 {location, versionId, eTag}
    UploadSvc->>UploadSvc: validate checksum, virus scan trigger
    UploadSvc->>Transcoder: enqueueTranscodingJob(contentId, s3Key, profiles=[360p,480p,720p,1080p,4K])
    Transcoder-->>UploadSvc: 202 {jobId, estimatedDuration=18min}
    UploadSvc-->>APIGW: 202 {jobId, status=PROCESSING, estimatedDuration}
    APIGW-->>Studio: 202 {jobId, status=PROCESSING}
    Studio->>Studio: display progress indicator
    loop Poll job status every 30 seconds
        Studio->>APIGW: GET /transcoding/jobs/{jobId}
        APIGW->>Transcoder: getJobStatus(jobId)
        Transcoder-->>APIGW: {jobId, status=ENCODING, progress=45%, currentProfile=1080p}
        APIGW-->>Studio: {jobId, status=ENCODING, progress=45%}
    end
    Transcoder->>Transcoder: encode all renditions + package HLS/DASH
    Transcoder->>S3: PUT encoded segments + manifests (bucket=cdn-origin)
    S3-->>Transcoder: 200 stored
    Transcoder->>CDN: purgeCache(contentId) + preWarm([manifest, init segments])
    CDN-->>Transcoder: 200 purge accepted, warming queued
    Transcoder->>NotifSvc: publishEvent(TRANSCODING_COMPLETE, {contentId, jobId, creatorId})
    NotifSvc->>NotifSvc: resolve creator notification preferences
    NotifSvc-->>Creator: email + push notification "Your video is ready"
    Transcoder-->>APIGW: jobStatus=COMPLETE (via webhook callback)
    APIGW->>UploadSvc: updateContentStatus(contentId, PUBLISHED)
    UploadSvc-->>APIGW: 200 OK
    Studio->>APIGW: GET /transcoding/jobs/{jobId}
    APIGW->>Transcoder: getJobStatus(jobId)
    Transcoder-->>APIGW: {status=COMPLETE, renditions:[360p,480p,720p,1080p,4K], manifestUrl}
    APIGW-->>Studio: {status=COMPLETE, manifestUrl, renditions}
    Studio-->>Creator: "Video published — share link ready"
```

### Upload and Transcoding Flow — Design Rationale

Multipart upload to S3 pre-signed URLs bypasses the API Gateway for the raw video bytes,
eliminating a bottleneck that would otherwise require the gateway to proxy gigabytes of binary
data. Each 100 MB chunk is uploaded directly from the browser or mobile SDK to S3, keeping API
Gateway payloads small and avoiding timeout pressure on large files. The Upload Service tracks
part ETags, which are then used to complete the S3 multipart upload atomically; if any part fails,
only that chunk is re-uploaded.

The Transcoding Service operates an asynchronous job queue backed by AWS Batch or a Kubernetes Job
controller. Rendition profiles (360p through 4K) are encoded in parallel across separate worker
pods to minimize time-to-publish. Each rendition is packaged into both HLS (TS segments or CMAF)
and MPEG-DASH manifests, enabling broad device compatibility. Thumbnail extraction, HDR tone-mapping,
and audio normalization (EBU R128) are performed as subordinate steps within the same job graph.

CDN cache pre-warming is triggered immediately after transcoding completes. The Transcoding Service
pushes the master manifest, initial segment of each rendition, and DRM initialization segments to
CDN edge nodes in the top-5 viewer geographies. This dramatically reduces the cache-miss rate for
popular content in the first minutes after publication, which is typically when traffic is highest.
The Notification Service delivers creator alerts through email (SendGrid) and push notifications
(Firebase Cloud Messaging) using a templated message that includes the video thumbnail and
direct share URL.

---

## Live Stream Setup and Broadcast

This diagram covers the full lifecycle of a live stream: key generation, RTMP ingest, adaptive
packaging, viewer delivery, DVR storage, and graceful termination.

```mermaid
sequenceDiagram
    autonumber
    actor Creator
    participant Encoder     as Encoder (OBS/FFMPEG)
    participant APIGW       as API Gateway
    participant RTMPIngest  as RTMP Ingest Service
    participant LivePkg     as Live Packaging Service
    participant CDN         as CDN (Cloudflare/Akamai)
    actor Viewer
    participant DVRStorage  as DVR Storage (S3)

    Creator->>APIGW: POST /livestreams {title, scheduledAt, category, drmEnabled}
    APIGW->>RTMPIngest: createStream(creatorId, metadata)
    RTMPIngest->>RTMPIngest: generate streamKey (256-bit random, HMAC-signed)
    RTMPIngest-->>APIGW: {streamId, streamKey, rtmpUrl: rtmp://ingest.stream.io/live}
    APIGW-->>Creator: {streamId, streamKey, rtmpUrl, previewUrl}
    Creator->>Encoder: configure RTMP output (rtmpUrl + streamKey, 1080p60, 6 Mbps)
    Creator->>Encoder: start streaming
    Encoder->>RTMPIngest: RTMP CONNECT (rtmpUrl, streamKey)
    RTMPIngest->>RTMPIngest: authenticate streamKey, resolve creatorId
    RTMPIngest-->>Encoder: RTMP connect acknowledged
    Encoder->>RTMPIngest: RTMP publish (stream name)
    RTMPIngest-->>Encoder: publish acknowledged — stream LIVE
    RTMPIngest->>APIGW: streamStatusUpdate(streamId, LIVE)
    APIGW->>APIGW: broadcast SSE event to Creator Studio dashboard
    loop Every keyframe (~2s GOP)
        Encoder->>RTMPIngest: RTMP data (video keyframe + audio chunk)
        RTMPIngest->>LivePkg: forwardMediaChunk(streamId, chunk, pts)
        LivePkg->>LivePkg: package chunk into HLS segment (2s) + DASH segment
        LivePkg->>CDN: push HLS segment (streamId/seg_NNNN.ts)
        CDN-->>LivePkg: 200 stored at edge
        LivePkg->>CDN: update live playlist (m3u8, sliding 3-segment window)
        CDN-->>LivePkg: 200 playlist updated
        LivePkg->>DVRStorage: archive segment to S3 (streamId/dvr/seg_NNNN.ts)
        DVRStorage-->>LivePkg: 200 archived
    end
    Viewer->>CDN: GET /live/{streamId}/master.m3u8
    CDN-->>Viewer: master manifest (live renditions: 360p, 720p, 1080p)
    Viewer->>CDN: GET /live/{streamId}/1080p/playlist.m3u8
    CDN-->>Viewer: live rendition playlist (3 segments, ~6s latency)
    Viewer->>CDN: GET /live/{streamId}/1080p/seg_0001.ts
    CDN-->>Viewer: segment bytes (from edge)
    Viewer->>CDN: GET /live/{streamId}/1080p/seg_0002.ts
    CDN-->>Viewer: segment bytes
    Viewer->>CDN: GET /live/{streamId}/1080p/playlist.m3u8 [refresh]
    CDN-->>Viewer: updated playlist (new segments appended)
    Viewer->>APIGW: POST /livestreams/{streamId}/heartbeat {viewerToken, quality}
    APIGW->>RTMPIngest: recordViewerHeartbeat(streamId, viewerId)
    RTMPIngest-->>APIGW: 204 No Content
    APIGW-->>Viewer: 204 No Content
    Note over Creator, Encoder: Creator ends the stream
    Creator->>Encoder: stop streaming
    Encoder->>RTMPIngest: RTMP FCUnpublish + DeleteStream
    RTMPIngest->>LivePkg: streamEnded(streamId)
    LivePkg->>CDN: finalize live playlist (EXT-X-ENDLIST)
    CDN-->>LivePkg: 200 playlist finalized
    LivePkg->>DVRStorage: writeVODManifest(streamId, totalSegments)
    DVRStorage-->>LivePkg: 200 VOD manifest stored
    RTMPIngest->>APIGW: streamStatusUpdate(streamId, ENDED)
    APIGW->>APIGW: broadcast SSE event — stream ended
    APIGW-->>Creator: stream summary {duration, peakViewers, totalViews}
```

### Live Stream Flow — Design Rationale

Stream key authentication at the RTMP layer is the first security gate. The RTMP Ingest Service
validates the HMAC-signed stream key before accepting any media data, preventing unauthorized
broadcasts on a creator's channel. Stream keys are single-use per session by default; a creator
who disconnects must generate a new key or explicitly reuse the existing one within a 30-minute
window. This guards against key replay attacks.

The Live Packaging Service operates with a 2-second segment duration to achieve approximately 6–8
seconds of end-to-end latency in standard HLS delivery. For use cases requiring lower latency
(e.g., live auctions, interactive events), Low-Latency HLS (LL-HLS) with partial segments and
blocking playlist reload is available as an opt-in configuration, reducing latency to under 3
seconds. MPEG-DASH CMAF chunked transfer is simultaneously produced for Android and Smart TV
clients that prefer it.

DVR storage is a byproduct of the live packaging loop: every segment written to the CDN edge is
also archived to S3 with a sequential index. When the stream ends, the Live Packaging Service
emits a VOD manifest (a static HLS playlist pointing to all archived segments) that is immediately
available for on-demand playback, creating a seamless "watch from the beginning" experience for
viewers who join late. The DVR window is configurable per subscription tier — free creators receive
a 2-hour DVR window while premium creators retain a full 30-day archive.
