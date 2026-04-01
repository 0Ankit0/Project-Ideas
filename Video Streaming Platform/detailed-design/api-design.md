# Video Streaming Platform - REST API Specification

## Overview
This document defines the complete REST API for the Video Streaming Platform, covering content management, live streaming, subscriptions, DRM, and search functionality. All endpoints require Bearer JWT authentication except for health checks.

## Authentication & Authorization

### Headers
```
Authorization: Bearer <JWT_TOKEN>
X-User-ID: <UUID>
X-Client-ID: <CLIENT_UUID>
Content-Type: application/json
```

### JWT Claims
- `sub`: User ID (UUID)
- `email`: User email
- `roles`: Array of roles (subscriber, content-creator, admin, moderator)
- `subscription_tier`: free, basic, premium, enterprise
- `exp`: Expiration timestamp
- `iat`: Issued at timestamp

### Rate Limiting
- Free tier: 1000 requests/hour
- Premium tier: 10000 requests/hour
- Enterprise: Custom limits
- Live stream endpoints: 100 requests/minute per stream
- Rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## Content Management Endpoints

### POST /api/v1/contents/upload-url
Get presigned S3 URL for chunked video upload

**Request**
```json
{
  "filename": "summer_vacation.mp4",
  "file_size": 5368709120,
  "content_type": "video/mp4",
  "chunk_count": 512,
  "title": "My Summer Vacation 2024",
  "description": "Amazing travel footage",
  "genre_id": "b1a2c3d4-e5f6-47g8-h9i0-j1k2l3m4n5o6",
  "is_private": false,
  "metadata": {
    "source_camera": "DJI Air 3",
    "duration_seconds": 3600,
    "resolution": "4K"
  }
}
```

**Response (200 OK)**
```json
{
  "upload_session_id": "sess_abc123def456ghi789jkl012",
  "content_id": "content_xyz789uvw456rst123opq",
  "presigned_urls": [
    {
      "chunk_number": 1,
      "url": "https://s3.amazonaws.com/vsp-uploads/...",
      "expires_in_seconds": 3600,
      "http_method": "PUT",
      "required_headers": {
        "x-amz-algorithm": "AWS4-HMAC-SHA256",
        "x-amz-credential": "...",
        "x-amz-date": "20240415T143022Z",
        "x-amz-signature": "..."
      }
    }
  ],
  "completion_webhook_url": "https://api.vsp.com/internal/webhooks/upload-complete",
  "chunk_size_bytes": 10485760,
  "expires_at": "2024-04-15T15:30:22Z"
}
```

**Error Responses**
- 400 Bad Request: Invalid file size (>1TB) or unsupported content type
- 401 Unauthorized: Missing/invalid JWT
- 413 Payload Too Large: File exceeds maximum allowed size
- 429 Too Many Requests: Rate limit exceeded

---

### POST /api/v1/contents/upload-complete
Finalize upload after all chunks successfully transferred

**Request**
```json
{
  "upload_session_id": "sess_abc123def456ghi789jkl012",
  "content_id": "content_xyz789uvw456rst123opq",
  "chunk_hashes": [
    {
      "chunk_number": 1,
      "sha256_hash": "abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567"
    }
  ],
  "total_file_size": 5368709120
}
```

**Response (202 Accepted)**
```json
{
  "upload_session_id": "sess_abc123def456ghi789jkl012",
  "content_id": "content_xyz789uvw456rst123opq",
  "status": "queued_for_transcoding",
  "transcoding_job_id": "job_pqr123stu456vwx789yza012",
  "estimated_completion_time": "2024-04-15T18:30:22Z",
  "notification_url": "wss://api.vsp.com/notifications/content/content_xyz789uvw456rst123opq"
}
```

---

### POST /api/v1/contents/{id}/publish
Trigger transcoding pipeline and make content available

**Request**
```json
{
  "thumbnail_timestamp_seconds": 45,
  "generate_chapter_thumbnails": true,
  "chapter_interval_seconds": 300,
  "target_transcoding_profiles": ["360p", "480p", "720p", "1080p"],
  "enable_drm": true,
  "drm_schemes": ["widevine", "fairplay", "playready"],
  "enable_subtitle_generation": true,
  "subtitle_languages": ["en", "es", "fr", "de"],
  "enable_audio_descriptions": true,
  "enable_closed_captions": true,
  "custom_encoding_params": {
    "video_codec": "h264",
    "audio_codec": "aac",
    "target_bitrate_multiplier": 1.0
  }
}
```

**Response (202 Accepted)**
```json
{
  "content_id": "content_xyz789uvw456rst123opq",
  "publish_request_id": "pub_req_123abc456def789ghi012jkl",
  "status": "publishing",
  "transcoding_job_id": "job_pqr123stu456vwx789yza012",
  "pipeline_stages": [
    {
      "stage": "validation",
      "status": "completed",
      "started_at": "2024-04-15T14:32:22Z",
      "completed_at": "2024-04-15T14:33:22Z"
    },
    {
      "stage": "transcoding",
      "status": "in_progress",
      "started_at": "2024-04-15T14:33:22Z",
      "estimated_completion_at": "2024-04-15T17:33:22Z"
    },
    {
      "stage": "packaging",
      "status": "queued"
    },
    {
      "stage": "drm_encryption",
      "status": "queued"
    },
    {
      "stage": "cdn_distribution",
      "status": "queued"
    }
  ],
  "webhook_url": "https://api.vsp.com/internal/webhooks/publish-progress",
  "notification_topic": "arn:aws:sns:us-east-1:123456789012:content-publish-content_xyz789uvw456rst123opq"
}
```

**Error Responses**
- 404 Not Found: Content ID does not exist
- 409 Conflict: Content already published or publishing in progress
- 422 Unprocessable Entity: Invalid transcoding profile or DRM scheme

---

### GET /api/v1/contents/{id}/playback-token
Get DRM-protected CDN signed URL and playback token

**Query Parameters**
- `device_id` (required): Unique device identifier for DRM binding
- `bitrate_limit_mbps` (optional): Cap playback bitrate (default: unlimited)
- `offline_download` (optional): Enable offline download (premium only)
- `expiry_seconds` (optional): Token validity period (default: 3600, max: 86400)

**Request**
```
GET /api/v1/contents/content_xyz789uvw456rst123opq/playback-token?device_id=device_abc123&bitrate_limit_mbps=10&offline_download=false
```

**Response (200 OK)**
```json
{
  "playback_token": {
    "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in_seconds": 3600,
    "expires_at": "2024-04-15T16:32:22Z"
  },
  "playback_urls": {
    "hls_manifest": "https://cdn.vsp.com/hls/content_xyz789uvw456rst123opq/master.m3u8?token=...",
    "dash_manifest": "https://cdn.vsp.com/dash/content_xyz789uvw456rst123opq/manifest.mpd?token=...",
    "smooth_streaming": "https://cdn.vsp.com/ss/content_xyz789uvw456rst123opq/Manifest?token=..."
  },
  "drm_license_server": {
    "widevine_url": "https://drm.vsp.com/widevine/license",
    "fairplay_url": "https://drm.vsp.com/fairplay/license",
    "playready_url": "https://drm.vsp.com/playready/license"
  },
  "content_info": {
    "id": "content_xyz789uvw456rst123opq",
    "title": "My Summer Vacation 2024",
    "duration_seconds": 3600,
    "available_bitrates": [360, 480, 720, 1080],
    "available_audio_tracks": ["en-stereo", "en-5.1", "es-stereo", "fr-stereo"],
    "available_subtitles": ["en", "es", "fr", "de"],
    "available_audio_descriptions": ["en"],
    "closed_captions_available": true
  },
  "device_binding": {
    "device_id": "device_abc123",
    "device_model": "Samsung TV",
    "maximum_resolution": "1080p",
    "maximum_frame_rate": 60
  },
  "usage_rules": {
    "max_concurrent_streams": 1,
    "allow_offline_download": false,
    "allow_screen_mirroring": false,
    "bitrate_limit_mbps": 10,
    "geo_restrictions": ["US", "CA", "MX"]
  }
}
```

**Error Responses**
- 403 Forbidden: User lacks subscription tier for content or geo-restricted
- 404 Not Found: Content or playback not available
- 451 Unavailable For Legal Reasons: Content geo-blocked in user's region

---

### GET /api/v1/contents
Get paginated content catalog with search and filtering

**Query Parameters**
- `page` (optional): Page number (default: 1, min: 1)
- `limit` (optional): Results per page (default: 20, max: 100)
- `genre` (optional): Genre filter (action, drama, comedy, documentary, etc.)
- `year` (optional): Release year filter
- `language` (optional): Content language (en, es, fr, etc.)
- `sort` (optional): Sort field (trending, newest, rating, duration)
- `min_rating` (optional): Minimum user rating (0-10)
- `duration_min_seconds` (optional): Minimum duration
- `duration_max_seconds` (optional): Maximum duration
- `content_type` (optional): vod, live, series

**Request**
```
GET /api/v1/contents?genre=action&year=2024&page=1&limit=20&sort=trending&min_rating=7
```

**Response (200 OK)**
```json
{
  "data": [
    {
      "id": "content_abc123",
      "title": "Action Adventure 2024",
      "description": "Thrilling adventure story",
      "genre": ["action", "adventure"],
      "year": 2024,
      "language": "en",
      "duration_seconds": 7200,
      "poster_url": "https://cdn.vsp.com/posters/content_abc123.jpg",
      "thumbnail_url": "https://cdn.vsp.com/thumbnails/content_abc123.jpg",
      "rating": 8.5,
      "rating_count": 15234,
      "view_count": 125000,
      "creator_id": "creator_xyz789",
      "creator_name": "Action Films Studio",
      "subscription_required": "premium",
      "is_new": true,
      "is_trending": true,
      "content_rating": "PG-13",
      "available_in_hd": true,
      "has_subtitles": true,
      "has_audio_descriptions": true
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_count": 4523,
    "total_pages": 227,
    "has_next": true,
    "has_previous": false
  },
  "filters_applied": {
    "genre": "action",
    "year": 2024,
    "min_rating": 7
  }
}
```

---

### GET /api/v1/contents/{id}
Get detailed content information

**Response (200 OK)**
```json
{
  "id": "content_xyz789uvw456rst123opq",
  "title": "My Summer Vacation 2024",
  "description": "Amazing travel footage from summer 2024",
  "extended_synopsis": "A comprehensive documentary of our family's journey...",
  "genre": ["documentary", "travel", "family"],
  "tags": ["vacation", "family-friendly", "hd", "4k"],
  "year": 2024,
  "language": "en",
  "duration_seconds": 3600,
  "content_type": "vod",
  "content_rating": "G",
  "maturity_rating": "0+",
  "creator_id": "creator_abc123",
  "creator_name": "Travel Enthusiasts",
  "upload_date": "2024-04-01T14:32:22Z",
  "last_updated": "2024-04-14T10:15:30Z",
  "published_at": "2024-04-05T08:00:00Z",
  "availability": {
    "start_date": "2024-04-05T08:00:00Z",
    "end_date": "2025-04-05T08:00:00Z",
    "is_available": true,
    "status": "published"
  },
  "media_files": {
    "source": {
      "resolution": "4K",
      "bitrate_kbps": 50000,
      "frame_rate": 60,
      "codec": "h265",
      "size_bytes": 5368709120
    },
    "transcoded_variants": [
      {
        "profile": "360p",
        "bitrate_kbps": 1000,
        "frame_rate": 30,
        "codec": "h264",
        "hls_url": "https://cdn.vsp.com/hls/360p/...",
        "dash_url": "https://cdn.vsp.com/dash/360p/..."
      }
    ]
  },
  "drm_protection": {
    "enabled": true,
    "schemes": ["widevine", "fairplay", "playready"],
    "expiry_date": "2025-04-05T08:00:00Z"
  },
  "ratings": {
    "average_rating": 8.7,
    "rating_count": 2341,
    "distribution": {
      "5_star": 1500,
      "4_star": 600,
      "3_star": 200,
      "2_star": 30,
      "1_star": 11
    }
  },
  "engagement_metrics": {
    "view_count": 125000,
    "completion_rate": 0.85,
    "average_watch_duration_seconds": 2800,
    "like_count": 8500,
    "share_count": 1200,
    "comment_count": 450
  },
  "monetization": {
    "is_monetized": true,
    "revenue_share_percentage": 70,
    "total_earnings": 15000.50,
    "currency": "USD"
  },
  "metadata": {
    "source_camera": "DJI Air 3",
    "location": {
      "country": "Italy",
      "city": "Rome",
      "coordinates": {
        "latitude": 41.9028,
        "longitude": 12.4964
      }
    }
  }
}
```

---

## Live Streaming Endpoints

### POST /api/v1/live-streams
Start a new broadcast session

**Request**
```json
{
  "title": "Live Cooking Show - Episode 5",
  "description": "Join us for an exciting cooking demonstration",
  "is_public": true,
  "scheduled_start_time": "2024-04-15T19:00:00Z",
  "expected_duration_minutes": 90,
  "category": "cooking",
  "tags": ["cooking", "live", "educational"],
  "enable_dvr": true,
  "dvr_retention_days": 30,
  "enable_interactive_features": true,
  "features": {
    "allow_comments": true,
    "allow_live_polls": true,
    "allow_donations": true,
    "allow_moderator_only_chat": false
  },
  "monetization": {
    "enable_ads": true,
    "enable_tipping": true,
    "minimum_subscription_tier": "free"
  },
  "geo_restrictions": {
    "allowed_regions": ["US", "CA", "MX", "GB", "FR"],
    "blocked_regions": []
  }
}
```

**Response (201 Created)**
```json
{
  "stream_id": "stream_abc123def456ghi789jkl012",
  "status": "scheduled",
  "title": "Live Cooking Show - Episode 5",
  "broadcaster_id": "creator_xyz789",
  "scheduled_start_time": "2024-04-15T19:00:00Z",
  "created_at": "2024-04-15T14:32:22Z",
  "ingest": {
    "rtmp_url": "rtmp://ingest.vsp.com/live",
    "stream_key": "stream_abc123def456ghi789jkl012?auth_token=eyJ0eXAiOiJKV1QiLCJhbGc...",
    "backup_rtmp_url": "rtmp://ingest-backup.vsp.com/live",
    "backup_stream_key": "stream_abc123def456ghi789jkl012_backup?auth_token=...",
    "hls_ingest_url": "https://ingest.vsp.com/hls/live",
    "srt_ingest_url": "srt://ingest.vsp.com:2935",
    "connection_timeout_seconds": 10,
    "key_rotation_interval_minutes": 60
  },
  "playback": {
    "hls_playback_url": "https://cdn.vsp.com/live/stream_abc123def456ghi789jkl012/master.m3u8",
    "dash_playback_url": "https://cdn.vsp.com/live/stream_abc123def456ghi789jkl012/manifest.mpd",
    "ll_hls_playback_url": "https://cdn.vsp.com/live/stream_abc123def456ghi789jkl012/ll-master.m3u8",
    "thumbnail_url": "https://cdn.vsp.com/live/stream_abc123def456ghi789jkl012/thumbnail.jpg"
  },
  "encoding_recommendations": {
    "bitrate_kbps": 6000,
    "resolution": "1920x1080",
    "frame_rate": 60,
    "audio_bitrate_kbps": 192,
    "audio_sample_rate_hz": 48000,
    "gop_size_frames": 120
  },
  "dvr_metadata": {
    "dvr_enabled": true,
    "dvr_window_duration_hours": 24,
    "dvr_retention_days": 30,
    "dvr_storage_location": "us-east-1"
  }
}
```

---

### DELETE /api/v1/live-streams/{id}
End a broadcast session

**Request**
```
DELETE /api/v1/live-streams/stream_abc123def456ghi789jkl012
```

**Response (200 OK)**
```json
{
  "stream_id": "stream_abc123def456ghi789jkl012",
  "status": "ended",
  "ended_at": "2024-04-15T20:32:22Z",
  "duration_seconds": 5400,
  "viewer_statistics": {
    "peak_concurrent_viewers": 15000,
    "total_unique_viewers": 45000,
    "total_watch_minutes": 1125000,
    "average_watch_duration_minutes": 25
  },
  "ingestion_statistics": {
    "total_bytes_ingested": 67500000000,
    "average_bitrate_kbps": 6200,
    "quality_events": 23,
    "keyframe_intervals_ms": [2000, 2010, 1990]
  },
  "live_to_vod_conversion": {
    "status": "queued",
    "estimated_completion_time": "2024-04-15T21:32:22Z",
    "vod_content_id": "content_stream_abc123def456ghi789jkl012"
  }
}
```

---

### GET /api/v1/live-streams/{id}/playback-url
Get HLS manifest URL for active live stream

**Query Parameters**
- `quality` (optional): auto, high, medium, low (default: auto)
- `low_latency` (optional): true for LL-HLS, false for standard HLS (default: false)
- `dvr_mode` (optional): true to enable DVR controls (default: false)

**Response (200 OK)**
```json
{
  "stream_id": "stream_abc123def456ghi789jkl012",
  "status": "live",
  "playback_urls": {
    "hls_manifest_url": "https://cdn.vsp.com/live/stream_abc123def456ghi789jkl012/master.m3u8",
    "ll_hls_manifest_url": "https://cdn.vsp.com/live/stream_abc123def456ghi789jkl012/ll-master.m3u8",
    "dash_manifest_url": "https://cdn.vsp.com/live/stream_abc123def456ghi789jkl012/manifest.mpd",
    "thumbnail_url": "https://cdn.vsp.com/live/stream_abc123def456ghi789jkl012/thumbnail.jpg"
  },
  "stream_info": {
    "current_bitrate_kbps": 5800,
    "current_resolution": "1920x1080",
    "current_frame_rate": 60,
    "uptime_seconds": 2700,
    "ingestion_latency_ms": 3500
  },
  "dvr_info": {
    "enabled": true,
    "current_dvr_window_start": "2024-04-15T19:30:22Z",
    "current_dvr_window_end": "2024-04-15T20:32:22Z",
    "dvr_window_duration_seconds": 3600
  },
  "viewer_info": {
    "current_concurrent_viewers": 8500,
    "viewers_last_5_minutes": 12000
  }
}
```

---

## Subscription Endpoints

### POST /api/v1/subscriptions
Create subscription

**Request**
```json
{
  "tier": "premium",
  "billing_cycle": "monthly",
  "auto_renew": true,
  "payment_method_id": "pm_stripe_abc123",
  "promotional_code": "SUMMER2024",
  "start_date": "2024-04-15T00:00:00Z",
  "country_code": "US",
  "billing_address": {
    "street": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "zip": "94102",
    "country": "US"
  }
}
```

**Response (201 Created)**
```json
{
  "subscription_id": "sub_abc123def456ghi789jkl012",
  "user_id": "user_xyz789",
  "tier": "premium",
  "status": "active",
  "billing_cycle": "monthly",
  "auto_renew": true,
  "created_at": "2024-04-15T14:32:22Z",
  "start_date": "2024-04-15T00:00:00Z",
  "renewal_date": "2024-05-15T00:00:00Z",
  "current_period_end": "2024-05-15T00:00:00Z",
  "pricing": {
    "base_price_cents": 1299,
    "discount_cents": 200,
    "tax_cents": 118,
    "total_price_cents": 1217,
    "currency": "USD"
  },
  "features": {
    "max_concurrent_streams": 4,
    "max_profile_count": 6,
    "offline_download_enabled": true,
    "offline_download_max_titles": 50,
    "ad_tier": "ad_free",
    "video_quality": "4K",
    "audio_quality": "immersive_5.1",
    "early_access_content": true,
    "priority_support": true
  },
  "payment_method": {
    "id": "pm_stripe_abc123",
    "type": "credit_card",
    "brand": "visa",
    "last4": "4242",
    "exp_month": 12,
    "exp_year": 2026
  },
  "notifications": {
    "billing_email": "user@example.com",
    "renewal_reminder_enabled": true,
    "renewal_reminder_days_before": 7
  }
}
```

---

### DELETE /api/v1/subscriptions/{id}
Cancel subscription

**Request**
```json
{
  "cancellation_reason": "too_expensive",
  "feedback": "Will try again when prices drop",
  "cancel_immediately": false,
  "refund_current_billing_period": true
}
```

**Response (200 OK)**
```json
{
  "subscription_id": "sub_abc123def456ghi789jkl012",
  "status": "cancelled",
  "cancellation_date": "2024-04-15T14:32:22Z",
  "cancellation_effective_date": "2024-05-15T00:00:00Z",
  "refund": {
    "refund_issued": true,
    "refund_amount_cents": 609,
    "refund_date": "2024-04-15T14:32:22Z",
    "refund_method": "original_payment_method"
  },
  "access_until": "2024-05-15T00:00:00Z",
  "message": "Your subscription will end on 2024-05-15. You have until then to download your offline content."
}
```

---

### GET /api/v1/subscriptions/{id}
Get subscription details

**Response (200 OK)**
```json
{
  "subscription_id": "sub_abc123def456ghi789jkl012",
  "user_id": "user_xyz789",
  "tier": "premium",
  "status": "active",
  "billing_cycle": "monthly",
  "auto_renew": true,
  "created_at": "2024-04-15T14:32:22Z",
  "start_date": "2024-04-15T00:00:00Z",
  "current_period_start": "2024-04-15T00:00:00Z",
  "current_period_end": "2024-05-15T00:00:00Z",
  "renewal_date": "2024-05-15T00:00:00Z",
  "days_until_renewal": 30,
  "pricing": {
    "base_price_cents": 1299,
    "discount_cents": 0,
    "tax_cents": 104,
    "total_price_cents": 1403,
    "currency": "USD"
  },
  "features": {
    "max_concurrent_streams": 4,
    "max_profile_count": 6,
    "offline_download_enabled": true,
    "offline_download_max_titles": 50,
    "ad_tier": "ad_free"
  },
  "usage": {
    "current_concurrent_streams": 1,
    "downloaded_titles_count": 8,
    "next_reset_date": "2024-05-15T00:00:00Z"
  },
  "payment_method": {
    "id": "pm_stripe_abc123",
    "type": "credit_card",
    "brand": "visa",
    "last4": "4242",
    "exp_month": 12,
    "exp_year": 2026
  }
}
```

---

## Search Endpoints

### POST /api/v1/search
Full-text search with filters and facets

**Request**
```json
{
  "query": "action movies 2024",
  "filters": {
    "genre": ["action", "adventure"],
    "year": {
      "min": 2023,
      "max": 2024
    },
    "language": "en",
    "content_type": ["vod"],
    "rating": {
      "min": 7.0,
      "max": 10.0
    },
    "duration_seconds": {
      "min": 3600,
      "max": 7200
    },
    "subscription_required": ["free", "premium"],
    "has_subtitles": true,
    "has_audio_descriptions": true,
    "content_rating": ["PG-13", "R"]
  },
  "sort": {
    "field": "rating",
    "order": "desc"
  },
  "page": 1,
  "limit": 20,
  "highlight_fields": ["title", "description"],
  "return_facets": true
}
```

**Response (200 OK)**
```json
{
  "results": [
    {
      "id": "content_abc123",
      "title": "Action Adventure 2024",
      "description": "Thrilling adventure story",
      "genre": ["action", "adventure"],
      "year": 2024,
      "language": "en",
      "duration_seconds": 7200,
      "rating": 8.5,
      "rating_count": 15234,
      "view_count": 125000,
      "poster_url": "https://cdn.vsp.com/posters/content_abc123.jpg",
      "highlight": {
        "title": ["<em>Action</em> <em>Movies</em> <em>2024</em>"],
        "description": ["<em>action</em> packed adventure..."]
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_count": 4523,
    "total_pages": 227,
    "has_next": true
  },
  "facets": {
    "genre": [
      {"name": "action", "count": 2345},
      {"name": "adventure", "count": 1890}
    ],
    "year": [
      {"name": "2024", "count": 1200},
      {"name": "2023", "count": 987}
    ],
    "rating": [
      {"name": "8.5-9.0", "count": 456},
      {"name": "9.0-10.0", "count": 234}
    ]
  },
  "query_time_ms": 45,
  "did_you_mean": null
}
```

---

## Error Response Format

All error responses follow this format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "status_code": 400,
    "request_id": "req_abc123def456ghi789jkl012",
    "timestamp": "2024-04-15T14:32:22Z",
    "details": [
      {
        "field": "file_size",
        "issue": "exceeds_maximum",
        "constraint": "5368709120 bytes maximum",
        "provided_value": 10737418240
      }
    ],
    "documentation_url": "https://docs.vsp.com/api/errors/VALIDATION_ERROR"
  }
}
```

## HTTP Status Codes

- **200 OK**: Successful GET/HEAD
- **201 Created**: Successful POST creating resource
- **202 Accepted**: Asynchronous operation accepted
- **204 No Content**: Successful operation with no response body
- **400 Bad Request**: Malformed request
- **401 Unauthorized**: Missing/invalid authentication
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource state conflict
- **413 Payload Too Large**: Request body exceeds limits
- **429 Too Many Requests**: Rate limit exceeded
- **451 Unavailable For Legal Reasons**: Geo-blocked
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Service temporarily unavailable

---

## Rate Limiting

### Headers
- `X-RateLimit-Limit`: Total requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets
- `Retry-After`: Seconds to wait before retrying (on 429)

### Limits by Tier
- Free: 1,000 req/hour
- Premium: 10,000 req/hour
- Enterprise: Customized

---

## Webhooks

Endpoints publish events to configured webhooks:

- `content.uploaded`: File upload completed
- `content.published`: Content publishing started
- `content.ready`: Content available for playback
- `stream.started`: Live stream started
- `stream.ended`: Live stream ended
- `transcoding.progress`: Transcoding job update
- `transcoding.failed`: Transcoding job failed
- `subscription.renewed`: Subscription auto-renewed
- `subscription.expiring_soon`: Renewal coming up
