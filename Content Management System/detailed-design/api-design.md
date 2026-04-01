# API Design — Content Management System

**Version:** 1.0  
**Status:** Approved  
**Last Updated:** 2025-01-01

---

## Table of Contents

1. [Overview](#1-overview)
2. [API Architecture](#2-api-architecture)
3. [Authentication and Authorization](#3-authentication-and-authorization)
4. [Content Management API](#4-content-management-api)
5. [Asset Management API](#5-asset-management-api)
6. [Content Delivery API](#6-content-delivery-api)
7. [Schema Management API](#7-schema-management-api)
8. [Workflow API](#8-workflow-api)
9. [Localization API](#9-localization-api)
10. [Webhook API](#10-webhook-api)
11. [Error Handling](#11-error-handling)
12. [Rate Limiting](#12-rate-limiting)
13. [Pagination](#13-pagination)
14. [Filtering and Sorting](#14-filtering-and-sorting)
15. [GraphQL API](#15-graphql-api)

---

## 1. Overview

The CMS provides dual API interfaces:
- **Management API**: Full CRUD operations for authenticated users (REST + GraphQL)
- **Delivery API**: Read-only content delivery for public/CDN consumption (REST + GraphQL)

**Base URLs:**
- Management API: `https://api.cms.example.com/v1`
- Delivery API: `https://cdn.cms.example.com/spaces/{space_id}`
- GraphQL Management: `https://api.cms.example.com/graphql`
- GraphQL Delivery: `https://cdn.cms.example.com/spaces/{space_id}/graphql`

**API Principles:**
- RESTful resource design with HATEOAS links
- JSON request/response payloads
- ISO 8601 timestamps (UTC)
- Idempotent operations where applicable
- Versioning via URL path (`/v1/`)

---

## 2. API Architecture

### 2.1 Request/Response Format

**Request Headers:**
```
POST /v1/spaces/sp_123/entries HTTP/1.1
Host: api.cms.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
X-Request-ID: uuid-v4
X-Idempotency-Key: uuid-v4
```

**Response Headers:**
```
HTTP/1.1 201 Created
Content-Type: application/json
X-Request-ID: uuid-v4
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4998
X-RateLimit-Reset: 1642345678
Location: /v1/spaces/sp_123/entries/ent_456
```

### 2.2 Resource Naming Conventions

| Resource | Collection Endpoint | Single Resource Endpoint |
|----------|-------------------|------------------------|
| Spaces | `GET /v1/spaces` | `GET /v1/spaces/{space_id}` |
| Entries | `GET /v1/spaces/{space_id}/entries` | `GET /v1/spaces/{space_id}/entries/{entry_id}` |
| Assets | `GET /v1/spaces/{space_id}/assets` | `GET /v1/spaces/{space_id}/assets/{asset_id}` |
| Content Types | `GET /v1/spaces/{space_id}/content-types` | `GET /v1/spaces/{space_id}/content-types/{type_id}` |

### 2.3 HTTP Method Semantics

| Method | Idempotent | Safe | Usage |
|--------|-----------|------|-------|
| GET | ✅ | ✅ | Retrieve resource(s) |
| POST | ❌ | ❌ | Create new resource |
| PUT | ✅ | ❌ | Replace entire resource |
| PATCH | ❌ | ❌ | Partial update |
| DELETE | ✅ | ❌ | Remove resource |

---

## 3. Authentication and Authorization

### 3.1 Authentication Methods

**Session Token (JWT):**
```bash
curl -X POST https://api.cms.example.com/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure_password"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4...",
  "expires_in": 86400,
  "token_type": "Bearer"
}
```

**API Key:**
```bash
curl -X GET https://api.cms.example.com/v1/spaces/sp_123/entries \
  -H "Authorization: Bearer cms_api_key_1234567890abcdef"
```

### 3.2 Token Refresh

**Endpoint:** `POST /v1/auth/refresh`

**Request:**
```json
{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "bmV3IHJlZnJlc2ggdG9rZW4...",
  "expires_in": 86400
}
```

---

## 4. Content Management API

### 4.1 Create Entry

**Endpoint:** `POST /v1/spaces/{space_id}/entries`

**Request:**
```json
{
  "content_type_id": "ct_blog_post",
  "locale": "en-US",
  "fields": {
    "title": "Introduction to Content Management Systems",
    "slug": "intro-to-cms",
    "body": {
      "html": "<p>Content management systems...</p>"
    },
    "author": {
      "entry_id": "ent_author_123"
    },
    "tags": ["cms", "tutorial", "guide"],
    "featured_image": {
      "asset_id": "ast_456"
    },
    "published_date": "2025-01-15T10:00:00Z",
    "seo_metadata": {
      "meta_title": "Intro to CMS | My Blog",
      "meta_description": "Learn about content management systems..."
    }
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "ent_789",
  "space_id": "sp_123",
  "content_type_id": "ct_blog_post",
  "locale": "en-US",
  "workflow_state": "draft",
  "fields": {
    "title": "Introduction to Content Management Systems",
    "slug": "intro-to-cms",
    "body": {
      "html": "<p>Content management systems...</p>"
    },
    "author": {
      "entry_id": "ent_author_123",
      "display_text": "Jane Doe"
    },
    "tags": ["cms", "tutorial", "guide"],
    "featured_image": {
      "asset_id": "ast_456",
      "url": "https://cdn.example.com/assets/ast_456.jpg"
    },
    "published_date": "2025-01-15T10:00:00Z",
    "seo_metadata": {
      "meta_title": "Intro to CMS | My Blog",
      "meta_description": "Learn about content management systems..."
    }
  },
  "created_at": "2025-01-10T14:30:00Z",
  "updated_at": "2025-01-10T14:30:00Z",
  "created_by": {
    "id": "usr_100",
    "name": "John Smith"
  },
  "_links": {
    "self": "/v1/spaces/sp_123/entries/ent_789",
    "content_type": "/v1/spaces/sp_123/content-types/ct_blog_post",
    "publish": "/v1/spaces/sp_123/entries/ent_789/publish"
  }
}
```

### 4.2 Get Entry

**Endpoint:** `GET /v1/spaces/{space_id}/entries/{entry_id}`

**Query Parameters:**
- `locale` (optional): Locale code (defaults to space default locale)
- `include` (optional): Depth of reference resolution (0-10, default: 0)

**Example:**
```bash
GET /v1/spaces/sp_123/entries/ent_789?locale=en-US&include=2
```

**Response:** `200 OK`
```json
{
  "id": "ent_789",
  "space_id": "sp_123",
  "content_type_id": "ct_blog_post",
  "locale": "en-US",
  "workflow_state": "published",
  "published_at": "2025-01-15T10:00:00Z",
  "version_number": 3,
  "fields": {
    "title": "Introduction to Content Management Systems",
    "author": {
      "id": "ent_author_123",
      "content_type_id": "ct_author",
      "fields": {
        "name": "Jane Doe",
        "bio": "Software engineer and technical writer"
      }
    }
  },
  "created_at": "2025-01-10T14:30:00Z",
  "updated_at": "2025-01-15T09:45:00Z",
  "_links": {
    "self": "/v1/spaces/sp_123/entries/ent_789",
    "versions": "/v1/spaces/sp_123/entries/ent_789/versions",
    "preview": "/v1/spaces/sp_123/entries/ent_789/preview"
  }
}
```

### 4.3 Update Entry

**Endpoint:** `PATCH /v1/spaces/{space_id}/entries/{entry_id}`

**Request:**
```json
{
  "fields": {
    "title": "Updated: Introduction to Content Management Systems",
    "body": {
      "html": "<p>Updated content...</p>"
    }
  }
}
```

**Response:** `200 OK` (same structure as Create Entry)

### 4.4 Delete Entry

**Endpoint:** `DELETE /v1/spaces/{space_id}/entries/{entry_id}`

**Response:** `204 No Content`

### 4.5 Publish Entry

**Endpoint:** `POST /v1/spaces/{space_id}/entries/{entry_id}/publish`

**Request:**
```json
{
  "scheduled_at": "2025-01-20T10:00:00Z"
}
```

**Response:** `200 OK`
```json
{
  "id": "ent_789",
  "workflow_state": "approved",
  "schedule": {
    "id": "sch_456",
    "action": "publish",
    "execute_at": "2025-01-20T10:00:00Z",
    "status": "pending"
  }
}
```

### 4.6 Unpublish Entry

**Endpoint:** `POST /v1/spaces/{space_id}/entries/{entry_id}/unpublish`

**Response:** `200 OK`
```json
{
  "id": "ent_789",
  "workflow_state": "archived",
  "unpublished_at": "2025-01-25T15:00:00Z"
}
```

### 4.7 List Entries

**Endpoint:** `GET /v1/spaces/{space_id}/entries`

**Query Parameters:**
- `content_type_id` (optional): Filter by content type
- `workflow_state` (optional): Filter by state (`draft`, `published`, etc.)
- `locale` (optional): Filter by locale
- `limit` (optional): Page size (1-100, default: 25)
- `skip` (optional): Pagination offset
- `order` (optional): Sort order (`-created_at`, `title`, etc.)

**Example:**
```bash
GET /v1/spaces/sp_123/entries?content_type_id=ct_blog_post&workflow_state=published&order=-published_at&limit=10
```

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "ent_789",
      "fields": {
        "title": "Introduction to CMS"
      },
      "published_at": "2025-01-15T10:00:00Z"
    }
  ],
  "total": 42,
  "limit": 10,
  "skip": 0,
  "_links": {
    "self": "/v1/spaces/sp_123/entries?limit=10&skip=0",
    "next": "/v1/spaces/sp_123/entries?limit=10&skip=10"
  }
}
```

### 4.8 Get Entry Versions

**Endpoint:** `GET /v1/spaces/{space_id}/entries/{entry_id}/versions`

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "ver_123",
      "version_number": 3,
      "created_by": {
        "id": "usr_100",
        "name": "John Smith"
      },
      "created_at": "2025-01-15T09:45:00Z",
      "change_summary": "Updated hero image"
    },
    {
      "id": "ver_122",
      "version_number": 2,
      "created_at": "2025-01-12T14:20:00Z"
    }
  ],
  "total": 3
}
```

### 4.9 Restore Entry Version

**Endpoint:** `POST /v1/spaces/{space_id}/entries/{entry_id}/versions/{version_id}/restore`

**Response:** `200 OK`
```json
{
  "id": "ent_789",
  "version_number": 4,
  "restored_from_version": 2,
  "workflow_state": "draft"
}
```

---

## 5. Asset Management API

### 5.1 Upload Asset

**Endpoint:** `POST /v1/spaces/{space_id}/assets`

**Request:** `multipart/form-data`
```bash
curl -X POST https://api.cms.example.com/v1/spaces/sp_123/assets \
  -H "Authorization: Bearer token" \
  -F "file=@hero-image.jpg" \
  -F "alt_text=A beautiful landscape" \
  -F "folder=/images/blog"
```

**Response:** `201 Created`
```json
{
  "id": "ast_456",
  "space_id": "sp_123",
  "filename": "hero-image.jpg",
  "mime_type": "image/jpeg",
  "size_bytes": 2048576,
  "width": 1920,
  "height": 1080,
  "alt_text": "A beautiful landscape",
  "folder": "/images/blog",
  "cdn_url": "https://cdn.example.com/assets/ast_456.jpg",
  "checksum_md5": "5d41402abc4b2a76b9719d911017c592",
  "uploaded_at": "2025-01-10T15:00:00Z",
  "_links": {
    "self": "/v1/spaces/sp_123/assets/ast_456",
    "transformations": "/v1/spaces/sp_123/assets/ast_456/transformations"
  }
}
```

### 5.2 Get Asset

**Endpoint:** `GET /v1/spaces/{space_id}/assets/{asset_id}`

**Response:** `200 OK` (same structure as Upload)

### 5.3 Update Asset Metadata

**Endpoint:** `PATCH /v1/spaces/{space_id}/assets/{asset_id}`

**Request:**
```json
{
  "alt_text": "Updated alt text",
  "folder": "/images/featured"
}
```

**Response:** `200 OK`

### 5.4 Delete Asset

**Endpoint:** `DELETE /v1/spaces/{space_id}/assets/{asset_id}`

**Response:** `204 No Content`

### 5.5 Get Asset Transformations

**Endpoint:** `GET /v1/spaces/{space_id}/assets/{asset_id}/transformations`

**Query Parameters:**
- `width` (optional): Target width
- `height` (optional): Target height
- `format` (optional): Output format (`jpeg`, `png`, `webp`, `avif`)
- `quality` (optional): Compression quality (1-100)
- `resize_mode` (optional): Resize behavior (`fit`, `fill`, `crop`, `thumb`)

**Example:**
```bash
GET /v1/spaces/sp_123/assets/ast_456/transformations?width=800&format=webp&quality=85
```

**Response:** `200 OK`
```json
{
  "id": "trn_789",
  "asset_id": "ast_456",
  "transformation_key": "w800_webp_q85",
  "width": 800,
  "height": 600,
  "format": "webp",
  "quality": 85,
  "resize_mode": "fit",
  "size_bytes": 102400,
  "cdn_url": "https://cdn.example.com/assets/ast_456/w800.webp",
  "created_at": "2025-01-10T15:05:00Z"
}
```

### 5.6 List Assets

**Endpoint:** `GET /v1/spaces/{space_id}/assets`

**Query Parameters:**
- `mime_type` (optional): Filter by MIME type
- `folder` (optional): Filter by folder path
- `limit`, `skip`, `order`: Pagination controls

**Response:** `200 OK` (collection format)

---

## 6. Content Delivery API

### 6.1 Get Published Entry

**Endpoint:** `GET /cdn/spaces/{space_id}/entries/{entry_id_or_slug}`

**Query Parameters:**
- `locale` (optional): Locale code
- `include` (optional): Reference depth

**Response:** `200 OK` (same structure as Management API but only published entries)

**Cache-Control:** `public, max-age=3600, s-maxage=86400`

### 6.2 List Published Entries

**Endpoint:** `GET /cdn/spaces/{space_id}/entries`

**Query Parameters:** Same as Management API

**Response:** `200 OK` (only includes published entries)

### 6.3 Search Entries

**Endpoint:** `GET /cdn/spaces/{space_id}/search`

**Query Parameters:**
- `q`: Search query
- `content_type_id` (optional): Filter by content type
- `locale` (optional): Filter by locale
- `fields` (optional): Fields to search (comma-separated)
- `limit`, `skip`: Pagination

**Example:**
```bash
GET /cdn/spaces/sp_123/search?q=content+management&content_type_id=ct_blog_post&limit=10
```

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "ent_789",
      "content_type_id": "ct_blog_post",
      "fields": {
        "title": "Introduction to Content Management Systems"
      },
      "published_at": "2025-01-15T10:00:00Z",
      "_score": 0.95
    }
  ],
  "total": 5,
  "query": "content management"
}
```

---

## 7. Schema Management API

### 7.1 Create Content Type

**Endpoint:** `POST /v1/spaces/{space_id}/content-types`

**Request:**
```json
{
  "name": "Blog Post",
  "api_id": "blog_post",
  "description": "Standard blog post content type",
  "display_field": "title",
  "fields": [
    {
      "name": "Title",
      "api_id": "title",
      "field_type": "short_text",
      "is_required": true,
      "is_unique": true,
      "validations": {
        "minLength": 1,
        "maxLength": 255
      }
    },
    {
      "name": "Body",
      "api_id": "body",
      "field_type": "rich_text",
      "is_required": true,
      "validations": {
        "allowedMarks": ["bold", "italic", "underline", "code"],
        "allowedNodes": ["paragraph", "heading", "blockquote", "list"]
      }
    },
    {
      "name": "Author",
      "api_id": "author",
      "field_type": "reference",
      "is_required": true,
      "validations": {
        "allowedContentTypes": ["author"]
      }
    }
  ]
}
```

**Response:** `201 Created`
```json
{
  "id": "ct_blog_post",
  "space_id": "sp_123",
  "name": "Blog Post",
  "api_id": "blog_post",
  "description": "Standard blog post content type",
  "display_field": "title",
  "version": 1,
  "fields": [...],
  "created_at": "2025-01-10T10:00:00Z"
}
```

### 7.2 Update Content Type

**Endpoint:** `PATCH /v1/spaces/{space_id}/content-types/{type_id}`

**Request:**
```json
{
  "fields": [
    {
      "action": "add",
      "field": {
        "name": "Tags",
        "api_id": "tags",
        "field_type": "array",
        "validations": {
          "maxItems": 10
        }
      }
    },
    {
      "action": "update",
      "api_id": "title",
      "changes": {
        "validations": {
          "maxLength": 300
        }
      }
    }
  ]
}
```

**Response:** `200 OK`

### 7.3 Delete Content Type

**Endpoint:** `DELETE /v1/spaces/{space_id}/content-types/{type_id}`

**Response:** `204 No Content` (only if no entries exist)

---

## 8. Workflow API

### 8.1 Request Approval

**Endpoint:** `POST /v1/spaces/{space_id}/entries/{entry_id}/approvals/request`

**Request:**
```json
{
  "approvers": ["usr_100", "usr_101"],
  "message": "Please review this blog post for publication"
}
```

**Response:** `200 OK`
```json
{
  "entry_id": "ent_789",
  "workflow_state": "in_review",
  "approval_requests": [
    {
      "id": "apr_req_123",
      "approver_id": "usr_100",
      "status": "pending"
    }
  ]
}
```

### 8.2 Grant Approval

**Endpoint:** `POST /v1/spaces/{space_id}/entries/{entry_id}/approvals`

**Request:**
```json
{
  "status": "approved",
  "comment": "Content looks great, approved for publish"
}
```

**Response:** `201 Created`
```json
{
  "id": "apr_123",
  "entry_id": "ent_789",
  "approver_id": "usr_100",
  "status": "approved",
  "comment": "Content looks great, approved for publish",
  "created_at": "2025-01-12T14:00:00Z"
}
```

### 8.3 Add Comment

**Endpoint:** `POST /v1/spaces/{space_id}/entries/{entry_id}/comments`

**Request:**
```json
{
  "field_id": "fld_body",
  "body": "Please add more details about the CMS features"
}
```

**Response:** `201 Created`
```json
{
  "id": "cmt_456",
  "entry_id": "ent_789",
  "field_id": "fld_body",
  "author_id": "usr_101",
  "body": "Please add more details about the CMS features",
  "is_resolved": false,
  "created_at": "2025-01-11T16:00:00Z"
}
```

### 8.4 Resolve Comment

**Endpoint:** `PATCH /v1/spaces/{space_id}/entries/{entry_id}/comments/{comment_id}`

**Request:**
```json
{
  "is_resolved": true
}
```

**Response:** `200 OK`

---

## 9. Localization API

### 9.1 Create Locale

**Endpoint:** `POST /v1/spaces/{space_id}/locales`

**Request:**
```json
{
  "code": "fr-CA",
  "name": "French (Canada)",
  "fallback_locale_code": "fr"
}
```

**Response:** `201 Created`

### 9.2 Get Entry Localization

**Endpoint:** `GET /v1/spaces/{space_id}/entries/{entry_id}/localizations`

**Response:** `200 OK`
```json
{
  "entry_id": "ent_789",
  "locales": [
    {
      "locale_code": "en-US",
      "is_default": true,
      "completion": 100
    },
    {
      "locale_code": "fr-CA",
      "is_default": false,
      "completion": 75,
      "missing_fields": ["seo_metadata"]
    }
  ]
}
```

### 9.3 Update Entry Localization

**Endpoint:** `PUT /v1/spaces/{space_id}/entries/{entry_id}/localizations/{locale_code}`

**Request:**
```json
{
  "fields": {
    "title": "Introduction aux systèmes de gestion de contenu",
    "body": {
      "html": "<p>Les systèmes de gestion de contenu...</p>"
    }
  }
}
```

**Response:** `200 OK`

---

## 10. Webhook API

### 10.1 Create Webhook

**Endpoint:** `POST /v1/spaces/{space_id}/webhooks`

**Request:**
```json
{
  "name": "Production Integration",
  "url": "https://example.com/webhooks/cms",
  "secret": "webhook_secret_key_1234567890abcdef",
  "events": [
    "entry.published",
    "entry.unpublished",
    "asset.uploaded"
  ]
}
```

**Response:** `201 Created`
```json
{
  "id": "wh_123",
  "space_id": "sp_123",
  "name": "Production Integration",
  "url": "https://example.com/webhooks/cms",
  "events": ["entry.published", "entry.unpublished", "asset.uploaded"],
  "status": "active",
  "created_at": "2025-01-10T10:00:00Z"
}
```

### 10.2 Get Webhook Deliveries

**Endpoint:** `GET /v1/spaces/{space_id}/webhooks/{webhook_id}/deliveries`

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "del_456",
      "webhook_id": "wh_123",
      "event_type": "entry.published",
      "status": "delivered",
      "http_status": 200,
      "attempt_count": 1,
      "delivered_at": "2025-01-15T10:00:01Z"
    },
    {
      "id": "del_457",
      "event_type": "entry.published",
      "status": "failed",
      "http_status": 500,
      "attempt_count": 5,
      "error_message": "Connection timeout",
      "created_at": "2025-01-14T14:00:00Z"
    }
  ]
}
```

### 10.3 Retry Webhook Delivery

**Endpoint:** `POST /v1/spaces/{space_id}/webhooks/{webhook_id}/deliveries/{delivery_id}/retry`

**Response:** `202 Accepted`

---

## 11. Error Handling

### 11.1 Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Entry validation failed",
    "details": [
      {
        "field": "title",
        "message": "Title is required",
        "code": "REQUIRED_FIELD_MISSING"
      },
      {
        "field": "body",
        "message": "Body must be at least 100 characters",
        "code": "MIN_LENGTH"
      }
    ],
    "request_id": "req_uuid_123"
  }
}
```

### 11.2 Error Codes

| HTTP Status | Error Code | Description |
|------------|------------|-------------|
| 400 | `BAD_REQUEST` | Malformed request |
| 400 | `VALIDATION_ERROR` | Field validation failed |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `NOT_FOUND` | Resource does not exist |
| 409 | `CONFLICT` | Resource conflict (e.g., duplicate slug) |
| 409 | `WORKFLOW_TRANSITION_INVALID` | Invalid state transition |
| 412 | `PRECONDITION_FAILED` | Approval requirement not met |
| 422 | `UNPROCESSABLE_ENTITY` | Semantic validation error |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server error |
| 503 | `SERVICE_UNAVAILABLE` | Temporary service disruption |

---

## 12. Rate Limiting

### 12.1 Rate Limit Headers

```
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4998
X-RateLimit-Reset: 1642345678
```

### 12.2 Rate Limit Tiers

| Credential Type | Requests/Hour | Burst Limit |
|----------------|--------------|-------------|
| Session Token (Free) | 1,000 | 2,000 |
| Session Token (Standard) | 10,000 | 20,000 |
| API Key (Standard) | 50,000 | 100,000 |
| API Key (Enterprise) | 500,000 | 1,000,000 |

### 12.3 Rate Limit Exceeded Response

**Response:** `429 Too Many Requests`
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit of 5000 requests per hour exceeded",
    "retry_after": 3600
  }
}
```

---

## 13. Pagination

### 13.1 Offset-Based Pagination

**Request:**
```bash
GET /v1/spaces/sp_123/entries?limit=25&skip=50
```

**Response:**
```json
{
  "items": [...],
  "total": 250,
  "limit": 25,
  "skip": 50,
  "_links": {
    "self": "/v1/spaces/sp_123/entries?limit=25&skip=50",
    "first": "/v1/spaces/sp_123/entries?limit=25&skip=0",
    "prev": "/v1/spaces/sp_123/entries?limit=25&skip=25",
    "next": "/v1/spaces/sp_123/entries?limit=25&skip=75",
    "last": "/v1/spaces/sp_123/entries?limit=25&skip=225"
  }
}
```

### 13.2 Cursor-Based Pagination

**Request:**
```bash
GET /v1/spaces/sp_123/entries?limit=25&cursor=eyJpZCI6ImVudF83ODkifQ==
```

**Response:**
```json
{
  "items": [...],
  "next_cursor": "eyJpZCI6ImVudF44MTQifQ==",
  "has_more": true
}
```

---

## 14. Filtering and Sorting

### 14.1 Filtering

**Query Parameters:**
- `fields.{field_name}`: Filter by field value
- `fields.{field_name}[match]`: Match operator

**Examples:**
```bash
# Exact match
GET /v1/spaces/sp_123/entries?fields.title=Introduction to CMS

# Pattern match
GET /v1/spaces/sp_123/entries?fields.title[match]=*CMS*

# Range query
GET /v1/spaces/sp_123/entries?fields.published_date[gte]=2025-01-01&fields.published_date[lte]=2025-01-31

# Array contains
GET /v1/spaces/sp_123/entries?fields.tags[in]=cms,tutorial
```

### 14.2 Sorting

**Order Parameter:**
- Ascending: `order=field_name`
- Descending: `order=-field_name`
- Multiple: `order=-published_at,title`

**Examples:**
```bash
GET /v1/spaces/sp_123/entries?order=-published_at
GET /v1/spaces/sp_123/entries?order=fields.title,-created_at
```

---

## 15. GraphQL API

### 15.1 Query Entries

```graphql
query {
  entries(
    spaceId: "sp_123"
    contentTypeId: "ct_blog_post"
    where: {
      workflowState: "published"
      fields: {
        publishedDate: { gte: "2025-01-01" }
      }
    }
    orderBy: publishedDate_DESC
    limit: 10
  ) {
    items {
      id
      fields {
        title
        slug
        author {
          ... on Author {
            fields {
              name
              bio
            }
          }
        }
        featuredImage {
          url(width: 800, format: webp)
          altText
        }
      }
      publishedAt
    }
    total
  }
}
```

### 15.2 Create Entry Mutation

```graphql
mutation {
  createEntry(
    spaceId: "sp_123"
    input: {
      contentTypeId: "ct_blog_post"
      locale: "en-US"
      fields: {
        title: "GraphQL and Content Management"
        body: { html: "<p>GraphQL provides...</p>" }
        author: { entryId: "ent_author_123" }
      }
    }
  ) {
    id
    workflowState
    fields {
      title
    }
  }
}
```

### 15.3 Publish Entry Mutation

```graphql
mutation {
  publishEntry(
    spaceId: "sp_123"
    entryId: "ent_789"
  ) {
    id
    workflowState
    publishedAt
  }
}
```

---

**Document Control:**  
- Approved by: API Architect, Engineering Lead  
- Review Cycle: Quarterly  
- Next Review: 2025-04-01
