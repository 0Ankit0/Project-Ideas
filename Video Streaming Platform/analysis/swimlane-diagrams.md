# Swimlane Diagrams

Swimlane diagrams partition complex workflows by the actor or service responsible for each step. For the Video Streaming Platform two critical end-to-end flows are documented here: the content upload and transcoding pipeline, and the subscription-gated playback flow. Each swim lane represents a discrete system boundary; handoffs between lanes correspond to asynchronous events or synchronous API calls.

---

## Content Upload and Transcoding

This flow covers every step from a creator initiating an upload through to CDN-distributed, DRM-packaged content being available for playback.

```mermaid
flowchart TD
    subgraph Creator
        A1([Creator opens Upload UI]) --> A2[Selects video file\nup to 50 GB]
        A2 --> A3[POST /contents/upload-url]
        A6[Receives upload-complete\nconfirmation] --> A7[POST /contents/id/publish]
        A7 --> A8([Creator sees\nProcessing status])
        A17([Creator receives\nContentPublished notification])
    end

    subgraph UploadService
        B1[Validates request\nfile size, auth, quota] --> B2[Generates presigned\nS3 multipart URL]
        B2 --> B3[Returns upload-url\nwith uploadId]
        B8[Receives publish trigger] --> B9[Emits VideoUploaded\nevent to Kafka]
        B9 --> B10[Sets content status\nto TRANSCODING_QUEUED]
    end

    subgraph TranscodingService
        C1[JobDispatcher polls\nKafka VideoUploaded] --> C2[Creates TranscodingJob\nin DynamoDB]
        C2 --> C3[Assigns job to\nFFmpegWorker pool]
        C3 --> C4[FFmpegWorker pulls\nraw file from S3]
        C4 --> C5[Transcodes to\n2160p 1080p 720p 480p 360p]
        C5 --> C6[HLSPackager generates\nmaster manifest + segments]
        C6 --> C7[ThumbnailExtractor\ngenerates preview images]
        C7 --> C8[QualityValidator runs\nVMAF scoring]
        C8 --> C9{VMAF pass?}
        C9 -->|Yes| C10[DRMPackager encrypts\nwith Widevine FairPlay]
        C9 -->|No| C11[Emits TranscodingFailed\nto Kafka]
        C10 --> C12[Emits TranscodingCompleted\nto Kafka]
    end

    subgraph StorageService
        D1[Stores raw upload\nin S3 raw-uploads bucket]
        D2[Stores HLS segments\nin S3 processed bucket]
        D3[Stores thumbnails\nin S3 thumbnails bucket]
    end

    subgraph CDN
        E1[CDNPusher replicates\nsegments to CloudFront\norigin S3]
        E2[CloudFront invalidation\npropagates manifest]
        E3([Content available\nat CDN edge nodes])
    end

    A3 --> B1
    B3 --> A4[Creator uploads chunks\ndirectly to S3\nusing presigned URL]
    A4 --> D1
    A4 --> A5[Last chunk uploaded\nS3 CompleteMultipartUpload]
    A5 --> A6
    A7 --> B8
    B10 --> C1
    C5 --> D2
    C7 --> D3
    C10 --> E1
    E1 --> E2
    E2 --> E3
    C12 --> F1[ContentService updates\nstatus to PUBLISHED]
    F1 --> A17
    C11 --> F2[ContentService updates\nstatus to FAILED\nnotifies creator]
```

### Lane Responsibilities

| Lane | Responsibility | Key SLOs |
|---|---|---|
| Creator | Initiates upload, triggers publish | N/A (user-facing) |
| UploadService | Presigned URL generation, event emission | URL generation < 200 ms |
| TranscodingService | FFmpeg processing, HLS packaging, DRM encryption | 1080p ready < 30 min |
| StorageService | Raw and processed object persistence | 99.99% durability |
| CDN | Edge distribution, cache invalidation | Propagation < 60 s |

### Key Events in This Flow

- **VideoUploaded** — emitted by UploadService after creator triggers publish; payload includes `contentId`, `s3RawKey`, `fileSizeBytes`, `creatorId`.
- **TranscodingJobStarted** — emitted by JobDispatcher when a worker picks up the job.
- **TranscodingCompleted** — emitted after DRM packaging and CDN push succeed; includes variant manifest URLs.
- **TranscodingFailed** — emitted when VMAF score is below threshold or FFmpeg exits non-zero; triggers creator notification.
- **ContentPublished** — emitted by ContentService after status flip; consumed by search indexer, recommendation engine, and notification service.

### Error Paths

If the FFmpegWorker crashes mid-job the JobDispatcher detects a heartbeat timeout after 5 minutes and re-enqueues the job on a different worker. If S3 upload of processed segments fails, the CDNPusher retries with exponential backoff (3 attempts, max 2 min). If DRM packaging fails the content is held in `TRANSCODING_COMPLETE_DRM_PENDING` status and an alert fires to the on-call engineer.

---

## Subscription and Playback

This flow covers a viewer requesting to watch premium content from the moment they click play through to the CDN delivering encrypted media segments to their player.

```mermaid
flowchart TD
    subgraph Viewer
        V1([Viewer clicks Play\non content page]) --> V2[GET /contents/id/playback-token]
        V7[Player initialises\nwith manifest URL] --> V8[Player requests DRM\nlicense from proxy]
        V11[Player fetches\nHLS master manifest] --> V12[Player selects\ninitial quality variant]
        V12 --> V13[Player requests\nfirst segments from CDN]
        V16([Playback begins\non device])
    end

    subgraph AuthService
        AU1[Validates Bearer JWT\nchecks expiry, signature] --> AU2{Token valid?}
        AU2 -->|No| AU3[Returns 401\nUnauthorized]
        AU2 -->|Yes| AU4[Passes userId\nto ContentService]
    end

    subgraph ContentService
        CS1[Receives playback-token\nrequest with contentId] --> CS2[Checks content exists\nand is PUBLISHED]
        CS2 --> CS3[Checks geo-restriction\nvs viewer IP/region]
        CS3 --> CS4{Geo allowed?}
        CS4 -->|No| CS5[Returns 451\nUnavailable For Legal Reasons]
        CS4 -->|Yes| CS6[Calls SubscriptionService\nto validate entitlement]
        CS6 --> CS7{Entitled?}
        CS7 -->|No| CS8[Returns 402\nSubscription Required]
        CS7 -->|Yes| CS9[Calls DRMService\nfor license token]
    end

    subgraph DRMService
        DR1[Receives license request\nwith contentId userId deviceId] --> DR2[Checks concurrent\nstream count for household]
        DR2 --> DR3{Streams ≤ 3?}
        DR3 -->|No| DR4[Returns 429\nMax Streams Exceeded]
        DR3 -->|Yes| DR5[Generates Widevine\nor FairPlay token]
        DR5 --> DR6[Records active session\nin Redis with TTL]
        DR6 --> DR7[Returns DRM token\n+ license server URL]
    end

    subgraph StreamingService
        SS1[Receives contentId\nand userId] --> SS2[Generates CloudFront\nsigned URL for manifest]
        SS2 --> SS3[Sets signed cookie\nwith 4h TTL]
        SS3 --> SS4[Returns manifest URL\n+ DRM token to viewer]
    end

    subgraph CDN
        CDN1[Viewer player fetches\nmanifest via signed URL] --> CDN2{Signature valid?}
        CDN2 -->|No| CDN3[Returns 403 Forbidden]
        CDN2 -->|Yes| CDN4[Returns HLS master\nmanifest from edge cache]
        CDN4 --> CDN5[Serves encrypted\nHLS segments on demand]
        CDN5 --> CDN6[Logs playback telemetry\nto access logs]
    end

    V2 --> AU1
    AU4 --> CS1
    CS9 --> DR1
    DR7 --> SS1
    SS4 --> V7
    V8 --> DR5
    V11 --> CDN1
    CDN4 --> V11
    CDN5 --> V13
    V13 --> V16
    V16 --> PE1[PlaybackStarted event\nemitted to Kafka]
    PE1 --> PE2[QoEMonitor tracks\nrebuffering, bitrate, errors]
```

### Lane Responsibilities

| Lane | Responsibility | Key SLOs |
|---|---|---|
| Viewer | Initiates playback, receives media | Startup time < 3 s |
| AuthService | JWT validation, identity assertion | p99 < 10 ms |
| ContentService | Entitlement, geo-restriction, routing | p99 < 50 ms |
| DRMService | License issuance, concurrent stream enforcement | p99 < 100 ms |
| StreamingService | Signed URL / cookie generation | p99 < 50 ms |
| CDN | Segment delivery, manifest caching | Hit ratio > 95% |

### Concurrency Enforcement

DRMService maintains a Redis sorted set keyed by `householdId`. Each active session is a member with the session start time as score. When a new stream is requested the service counts members where `now - score < sessionTTL`. If count ≥ 3 the request is rejected with `MAX_STREAMS_EXCEEDED`. Sessions expire automatically via Redis TTL aligned to the last heartbeat timestamp; the player sends a keepalive every 30 seconds.

### Playback Token Structure

```json
{
  "manifestUrl": "https://cdn.example.com/content/{id}/master.m3u8",
  "drmToken": "<base64-encoded-widevine-or-fairplay-token>",
  "licenseServerUrl": "https://widevine.example.com/license",
  "signedCookies": {
    "CloudFront-Policy": "...",
    "CloudFront-Signature": "...",
    "CloudFront-Key-Pair-Id": "..."
  },
  "expiresAt": "2025-01-15T22:00:00Z",
  "sessionId": "sess_01HXYZ...",
  "maxBitrate": 8000000
}
```
