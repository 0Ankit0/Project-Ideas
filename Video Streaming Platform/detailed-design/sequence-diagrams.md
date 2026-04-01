# Sequence Diagrams — Video Streaming Platform

This document captures three critical runtime flows of the Video Streaming Platform using Mermaid
`sequenceDiagram` notation. The first traces the full DRM license acquisition and playback
lifecycle. The second covers the resumable chunked upload pipeline used by creators. The third
maps the path from a live RTMP broadcast to viewer HLS delivery.

---

## DRM License Acquisition and Playback

The DRM flow begins when the player fetches a manifest and discovers which protection systems are
required. Each DRM scheme (Widevine, FairPlay, PlayReady) embeds a Protection System Specific
Header (PSSH) box in the manifest or the media init segment. The player's Content Decryption
Module (CDM) generates an opaque challenge blob that the player submits to the platform license
endpoint alongside a valid JWT. The license endpoint validates the user's entitlement before
forwarding the challenge to the appropriate DRM vendor server.

The license response flows back through the platform — never directly from the vendor to the
player — giving the platform audit control, geo-restriction enforcement, and the ability to embed
custom policy fields such as rental window duration, output protection level, and offline download
rights. The Key Management Service (KMS) stores content encryption keys encrypted at rest; the
DRM server requests keys by `keyId` and assembles the license without ever persisting plaintext
keys to disk. License renewal runs proactively five minutes before expiry so that legitimate
subscribers experience zero-interruption playback.

```mermaid
sequenceDiagram
    autonumber
    participant SDK as Player SDK
    participant CDN as CDN Edge
    participant API as Streaming API
    participant Auth as Auth Service
    participant DRM as DRM License Server
    participant KMS as Key Management Service

    SDK->>CDN: GET /vod/{contentId}/master.m3u8
    CDN->>CDN: check edge cache (TTL 60 s)
    CDN->>API: cache miss — forward manifest request
    API->>Auth: POST /token/validate { jwt }
    Auth-->>API: { valid: true, userId, subscriptionTier }
    API->>API: resolve geo-restriction for client IP
    API->>API: generate signed manifest URL with PSSH signal
    API-->>CDN: manifest (Cache-Control: max-age=60)
    CDN-->>SDK: master.m3u8 with DRM signalling

    SDK->>SDK: parse master.m3u8, select quality rendition
    SDK->>CDN: GET /vod/{contentId}/720p/playlist.m3u8
    CDN-->>SDK: variant playlist with EXT-X-KEY tags
    SDK->>CDN: GET /vod/{contentId}/720p/init.mp4
    CDN-->>SDK: init segment containing PSSH box
    SDK->>SDK: detect DRM system from PSSH system UUID
    SDK->>SDK: CDM generates opaque license challenge bytes

    SDK->>API: POST /drm/license { challenge, keyId, drmSystem, jwt }
    activate API
    API->>Auth: POST /token/validate { jwt }
    Auth-->>API: { valid: true, userId, planId }
    API->>Auth: GET /entitlements/{userId}/content/{contentId}
    Auth-->>API: { entitled: true, rights: [stream, download] }
    API->>API: enforce concurrent stream limit via Redis INCR
    API->>DRM: POST /license { challenge, keyId, drmSystem, customPolicy }
    activate DRM
    DRM->>DRM: validate challenge structure and signature
    DRM->>DRM: parse keyId from challenge payload
    DRM->>KMS: GET /keys/{keyId}
    activate KMS
    KMS->>KMS: decrypt key envelope with AWS KMS master key
    KMS-->>DRM: { contentKey, iv }
    deactivate KMS
    DRM->>DRM: assemble license with content key
    DRM->>DRM: apply custom policy (duration, output protection level)
    DRM->>DRM: sign license with provider root certificate
    DRM-->>API: license response blob
    deactivate DRM
    API->>API: write license issuance record to audit_logs
    API-->>SDK: HTTP 200 license response
    deactivate API

    SDK->>SDK: install license in platform CDM
    SDK->>SDK: extract content decryption key from license
    SDK->>CDN: GET /vod/{contentId}/720p/seg-001.ts
    CDN-->>SDK: encrypted segment (AES-128-CTR)
    SDK->>SDK: decrypt segment using extracted key
    SDK->>SDK: decode H.264/HEVC frames
    SDK->>SDK: begin rendering — playback starts

    loop Segment playback (every ~6 s)
        SDK->>CDN: GET next segment seq-N
        CDN-->>SDK: encrypted segment
        SDK->>SDK: decrypt and render segment
        SDK->>API: POST /sessions/{sessionId}/heartbeat { positionSeconds }
        API-->>SDK: { ok: true }
    end

    Note over SDK,API: License renewal — triggered 5 min before expiry

    SDK->>SDK: timer fires: license expires in < 5 min
    SDK->>API: POST /drm/license/renew { sessionToken, keyId, drmSystem }
    activate API
    API->>Auth: POST /token/validate { sessionToken }
    Auth-->>API: { valid: true, userId }
    API->>Auth: GET /entitlements/{userId}/content/{contentId}
    Auth-->>API: { entitled: true }
    API->>DRM: POST /license/renew { keyId, userId, existingPolicy }
    DRM->>KMS: GET /keys/{keyId}
    KMS-->>DRM: { contentKey, iv }
    DRM-->>API: renewed license
    API->>API: log renewal to audit_logs
    API-->>SDK: HTTP 200 renewed license
    deactivate API
    SDK->>SDK: replace license in CDM, no playback interruption

    alt Subscription lapsed during playback
        Auth-->>API: { entitled: false, reason: subscription_expired }
        API-->>SDK: HTTP 402 Payment Required
        SDK->>SDK: pause playback immediately
        SDK->>SDK: display subscription renewal prompt
    end
```

The platform enforces that license responses always pass through the Streaming API rather than
being returned directly by the DRM vendor. This ensures every license issuance is logged in
`audit_logs` with the userId, contentId, deviceId, IP address, and country code — a requirement
for GDPR compliance and content-rights auditing. Default streaming license duration is 24 hours;
offline download licenses carry a 48-hour validity window and an explicit
`offline_lease_duration` field in the Widevine/PlayReady policy JSON.

---

## Video Upload Chunking (Resumable Upload)

Large source files — up to 200 GB for 4K HDR raw footage — cannot be transferred reliably in a
single HTTP request. The platform implements a resumable upload protocol inspired by the TUS
open standard. The creator client splits the file into 10 MB chunks client-side and uploads each
independently. The server tracks chunk acknowledgements in Redis so that any network interruption
can be recovered from without re-uploading already-transferred data.

AWS S3's native multipart upload API is used as the storage backend, mapping each chunk directly
to an S3 part. When all parts are acknowledged, the client posts a completion request, triggering
S3 to assemble the object server-side. The Upload API then verifies the checksum, copies the
object to the permanent content bucket, and enqueues a `TranscodingJobRequested` event on Kafka.
The creator receives a job ID immediately and polls for progress or awaits a webhook notification
when transcoding completes.

```mermaid
sequenceDiagram
    autonumber
    participant Creator as Creator Studio
    participant UploadAPI as Upload API
    participant Redis as Redis Session Store
    participant S3 as S3 Object Store
    participant Queue as Transcoding Queue

    Creator->>UploadAPI: POST /uploads/initiate { fileName, fileSize, mimeType, clientChecksum }
    activate UploadAPI
    UploadAPI->>UploadAPI: validate JWT, extract creatorId
    UploadAPI->>UploadAPI: assert mimeType in [video/mp4, video/quicktime, video/x-matroska]
    UploadAPI->>UploadAPI: assert fileSize <= 200 GB quota
    UploadAPI->>S3: CreateMultipartUpload { bucket, key, contentType, serverSideEncryption: AES256 }
    S3-->>UploadAPI: { uploadId }
    UploadAPI->>UploadAPI: chunkCount = ceil(fileSize / 10 485 760)
    UploadAPI->>Redis: SET upload:session:{sessionId} { uploadId, totalChunks, status:pending, clientChecksum }
    UploadAPI->>Redis: EXPIRE upload:session:{sessionId} 86400
    UploadAPI-->>Creator: { sessionId, uploadId, chunkSizeBytes: 10485760, totalChunks }
    deactivate UploadAPI

    loop Upload each chunk (up to 4 in parallel)
        Creator->>UploadAPI: GET /uploads/{sessionId}/chunk/{n}/presigned-url
        UploadAPI->>Redis: GET upload:session:{sessionId}
        Redis-->>UploadAPI: session record
        UploadAPI->>UploadAPI: validate chunk index in [0, totalChunks-1]
        UploadAPI->>S3: GeneratePresignedUrl { uploadId, partNumber: n+1, expires: 3600 }
        S3-->>UploadAPI: presigned PUT URL
        UploadAPI-->>Creator: { presignedUrl, expiresAt }
        Creator->>S3: PUT chunk bytes directly to presigned URL
        S3-->>Creator: ETag response header
        Creator->>UploadAPI: POST /uploads/{sessionId}/chunk/{n}/ack { etag, bytesReceived }
        UploadAPI->>Redis: HSET upload:session:{sessionId}:parts n etag
        UploadAPI->>Redis: SADD upload:session:{sessionId}:done n
        UploadAPI-->>Creator: { acknowledged: true, completedCount, remainingCount }
    end

    opt Network failure — resume flow
        Creator->>UploadAPI: GET /uploads/{sessionId}/resume
        UploadAPI->>Redis: SMEMBERS upload:session:{sessionId}:done
        Redis-->>UploadAPI: set of completed chunk indices
        UploadAPI-->>Creator: { completedChunks, missingChunks, resumeFromChunk }
        Creator->>Creator: skip completed chunks, re-upload only missing
    end

    Creator->>UploadAPI: POST /uploads/{sessionId}/complete
    activate UploadAPI
    UploadAPI->>Redis: HGETALL upload:session:{sessionId}:parts
    Redis-->>UploadAPI: ordered map of partNumber → ETag
    UploadAPI->>UploadAPI: assert all expected parts present
    UploadAPI->>S3: CompleteMultipartUpload { uploadId, parts: [{partNumber, etag}] }
    S3->>S3: assemble object from parts, compute ETag
    S3-->>UploadAPI: { location, versionId, serverETag }
    UploadAPI->>UploadAPI: compare serverETag to clientChecksum
    UploadAPI->>S3: CopyObject to s3://content-source/{contentId}/source.mp4
    S3-->>UploadAPI: { newKey, etag }
    UploadAPI->>Queue: publish TranscodingJobRequested { contentId, s3Key, priority: NORMAL }
    Queue-->>UploadAPI: { messageId, jobId }
    UploadAPI->>Redis: HSET upload:session:{sessionId} status queued jobId {jobId}
    UploadAPI-->>Creator: { jobId, status: queued, estimatedMinutes: 45 }
    deactivate UploadAPI

    loop Poll every 10 s (or use webhook)
        Creator->>UploadAPI: GET /transcoding/{jobId}/status
        UploadAPI->>Queue: query transcoding_jobs record
        Queue-->>UploadAPI: { status, progressPercent, completedTasks, totalTasks }
        UploadAPI-->>Creator: { status, progress, eta }
    end

    Queue->>UploadAPI: POST /webhooks/transcoding-complete { jobId, contentId, variants }
    UploadAPI-->>Creator: webhook delivery: transcoding complete, variants available
    Creator->>UploadAPI: PATCH /contents/{contentId} { status: published, title, description }
    UploadAPI-->>Creator: { contentId, status: published, playbackUrl }
```

The presigned URL model removes the Upload API from the data path for chunk bytes — all data
flows directly from the creator's browser or native app to S3, eliminating the Upload API as a
bandwidth bottleneck and reducing per-upload egress costs to near zero. The 24-hour Redis TTL on
the session gives creators a generous window to resume uploads on slow or intermittent
connections. Orphaned S3 multipart uploads (sessions abandoned before completion) are cleaned up
by an S3 lifecycle rule set to abort incomplete uploads after 48 hours.

---

## Live RTMP Ingest to HLS Delivery

The live streaming pipeline begins with a broadcaster connecting from OBS, Streamlabs, or any
RTMP-capable encoder. The RTMP Ingest Service performs the standard RTMP handshake, authenticates
the stream key (which embeds a signed JWT with the creator's identity), and proxies the AV data
into a spawned FFmpeg process. FFmpeg simultaneously transcodes the input into multiple bitrate
renditions in real time, writing fixed-duration MPEG-TS segments to the HLS Packager.

The HLS Packager assembles variant playlists with a rolling three-segment window, pushes each new
segment to S3 for DVR storage, and cache-busts updated manifests on the Akamai CDN by setting a
short `Cache-Control: max-age=2` header. Viewers poll the variant playlist every two seconds to
discover new segments. If the RTMP connection drops, the ingest service holds the stream slot
open for 30 seconds before marking the stream interrupted — giving the encoder time to reconnect
without losing the DVR archive or the viewer session.

```mermaid
sequenceDiagram
    autonumber
    participant OBS as OBS Encoder
    participant RTMP as RTMP Ingest Service
    participant FFmpeg as Transcoder FFmpeg
    participant HLS as HLS Packager
    participant S3 as S3 DVR Store
    participant CDN as CDN Akamai
    participant Viewer as Viewer Player

    OBS->>RTMP: TCP SYN (port 1935)
    RTMP-->>OBS: TCP SYN-ACK
    OBS->>RTMP: C0 RTMP version byte 0x03
    OBS->>RTMP: C1 timestamp + 1528 random bytes
    RTMP-->>OBS: S0 version byte 0x03
    RTMP-->>OBS: S1 timestamp + 1528 random bytes
    RTMP-->>OBS: S2 echo of C1
    OBS->>RTMP: C2 echo of S1
    OBS->>RTMP: connect command { app: live, flashVer, tcUrl }
    RTMP->>RTMP: extract stream key from tcUrl path segment
    RTMP->>RTMP: validate JWT embedded in stream key
    Note over RTMP: stream key = base64(creatorId:streamId:sig)
    RTMP-->>OBS: _result NetConnection.Connect.Success
    OBS->>RTMP: Window Acknowledgement Size 2500000
    OBS->>RTMP: Set Peer Bandwidth 2500000
    OBS->>RTMP: createStream command
    RTMP-->>OBS: _result { streamId: 1 }
    OBS->>RTMP: publish { streamName, type: live }
    RTMP-->>OBS: onStatus NetStream.Publish.Start
    OBS->>RTMP: @setDataFrame onMetaData { width, height, framerate, videocodecid }
    OBS->>RTMP: video sequence header (SPS + PPS NAL units)
    OBS->>RTMP: audio sequence header (AAC AudioSpecificConfig)
    RTMP->>FFmpeg: spawn process with stdin RTMP pipe
    RTMP->>FFmpeg: write video sequence header to pipe
    RTMP->>FFmpeg: write audio sequence header to pipe
    FFmpeg->>FFmpeg: initialise H.264 decoder
    FFmpeg->>FFmpeg: init outputs: 1080p@6Mbps, 720p@3Mbps, 480p@1.5Mbps, 360p@800kbps
    FFmpeg->>HLS: open segment write pipe per rendition

    loop Real-time ingest — continuous
        OBS->>RTMP: video chunk (P-frame or I-frame)
        OBS->>RTMP: audio chunk AAC frame
        RTMP->>FFmpeg: pipe raw RTMP message bytes
        FFmpeg->>FFmpeg: decode input frame
        FFmpeg->>FFmpeg: encode to all output renditions
        FFmpeg->>HLS: push encoded frames into segment buffer
        HLS->>HLS: check accumulated duration >= 2 s target
        HLS->>HLS: seal segment, assign sequence number seq-N
        HLS->>S3: PUT /dvr/{streamId}/{rendition}/seq-{N}.ts
        S3-->>HLS: ETag
        HLS->>HLS: append segment to variant playlist
        HLS->>HLS: evict oldest segment if live window > 3 segments
        HLS->>S3: PUT /dvr/{streamId}/{rendition}/playlist.m3u8
        HLS->>CDN: PURGE /live/{streamId}/{rendition}/playlist.m3u8
        CDN-->>HLS: purge acknowledged
    end

    Note over Viewer,CDN: Viewer joins mid-stream

    Viewer->>CDN: GET /live/{streamId}/master.m3u8
    CDN->>HLS: cache miss — fetch master playlist
    HLS-->>CDN: master.m3u8 (Cache-Control: max-age=5)
    CDN-->>Viewer: master.m3u8
    Viewer->>Viewer: ABR selects 720p rendition based on bandwidth probe
    Viewer->>CDN: GET /live/{streamId}/720p/playlist.m3u8
    CDN->>S3: fetch latest variant playlist
    S3-->>CDN: playlist (3 segments, EXT-X-TARGETDURATION: 2)
    CDN-->>Viewer: variant playlist (Cache-Control: max-age=2)
    Viewer->>CDN: GET /live/{streamId}/720p/seq-{N}.ts
    CDN-->>Viewer: segment bytes
    Viewer->>Viewer: buffer and decode first segment, start playback

    loop Live edge polling every 2 s
        Viewer->>CDN: GET /live/{streamId}/720p/playlist.m3u8
        CDN-->>Viewer: updated playlist with seq-{N+1}
        Viewer->>CDN: GET /live/{streamId}/720p/seq-{N+1}.ts
        CDN-->>Viewer: new segment bytes
        Viewer->>Viewer: append to decode buffer
    end

    alt RTMP connection interrupted
        OBS->>RTMP: TCP RST (network failure)
        RTMP->>RTMP: detect EOF on RTMP socket
        RTMP->>FFmpeg: SIGTERM — flush in-progress segment
        FFmpeg->>HLS: write final partial segment
        HLS->>S3: PUT final partial segment
        HLS->>HLS: inject EXT-X-GAP tag into playlist
        RTMP->>RTMP: start 30 s reconnect grace timer
        OBS->>RTMP: TCP reconnect after network restore
        RTMP->>RTMP: cancel grace timer, resume same stream session
        RTMP->>FFmpeg: spawn new transcoder process
        RTMP-->>OBS: onStatus NetStream.Publish.Start
        Note over S3,HLS: DVR archive intact — no gap in recorded segments
    end
```

The two-second segment duration balances end-to-end latency (approximately six seconds at the
live edge: three segments in the playlist window) against the HTTP request overhead of frequent
segment fetches. For latency-critical events such as sports or auctions, the platform can switch
to Low-Latency HLS by reducing the chunk boundary to 200 ms partial segments and enabling HTTP/2
server push on the Akamai tier, driving live latency below two seconds. DVR archival reuses the
same segment files written for live delivery with no second encode pass, so catch-up viewers
experience identical quality to those watching live.
