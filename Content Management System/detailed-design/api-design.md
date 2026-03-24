# API Design

## Overview
The CMS exposes a versioned REST API under `/api/v1`. All endpoints require JWT bearer authentication except for public read endpoints (published posts, feeds, search) and the OAuth2 callback. Identifiers use slug-based URLs for content and hashid-style tokens for users and media.

---

## API Architecture

```mermaid
graph TB
    subgraph "Clients"
        PublicFront[Public Frontend]
        AdminSPA[Admin & Editor SPA]
        AuthorSPA[Author Dashboard]
    end

    subgraph "CMS API — /api/v1"
        Router[Versioned Routers]
        IAM[IAM & Auth<br>/auth, /users]
        Content[Content<br>/posts, /pages, /revisions]
        Publishing[Publishing<br>/posts/{id}/submit|publish|schedule|return]
        Taxonomy[Taxonomy<br>/categories, /tags]
        Media[Media<br>/media]
        Layout[Layout<br>/themes, /widgets, /layouts, /menus]
        Comments[Comments<br>/posts/{id}/comments, /moderation/comments]
        SEO[SEO<br>/seo, /redirects, /sitemap, /feed]
        Analytics[Analytics<br>/analytics/events, /analytics/dashboard]
        Notify[Notifications<br>/notifications]
        Plugins[Plugins<br>/plugins]
        Sites[Sites<br>/sites — Super Admin only]
        Search[Search<br>/search]
    end

    subgraph "Persistence"
        DB[(PostgreSQL)]
        Redis[(Redis)]
        Storage[(Object Storage)]
        SearchIdx[(Search Index)]
    end

    PublicFront --> Router
    AdminSPA --> Router
    AuthorSPA --> Router

    Router --> IAM
    Router --> Content
    Router --> Publishing
    Router --> Taxonomy
    Router --> Media
    Router --> Layout
    Router --> Comments
    Router --> SEO
    Router --> Analytics
    Router --> Notify
    Router --> Plugins
    Router --> Sites
    Router --> Search

    Content --> DB
    Publishing --> DB
    Publishing --> Redis
    Taxonomy --> DB
    Media --> DB
    Media --> Storage
    Layout --> DB
    Comments --> DB
    SEO --> DB
    Analytics --> DB
    Notify --> DB
    Plugins --> DB
    Sites --> DB
    Search --> SearchIdx
    IAM --> DB
    IAM --> Redis
```

---

## API Conventions

| Convention | Behavior |
|-----------|----------|
| Versioning | All endpoints under `/api/v1` |
| Auth | JWT bearer; `Authorization: Bearer <token>` |
| Public endpoints | Published post reads, search, feed, sitemap — no auth required |
| Response envelope | `{data: ..., meta: {page, per_page, total}}` for lists |
| Errors | `{error: {code, message, details}}` with appropriate HTTP status |
| Identifiers | Slug for posts/pages; hashid for users, media, placements |
| Pagination | Cursor-based (`after`, `before`) for feeds; offset-based for admin lists |
| Rate limiting | 60 req/min for public; 300 req/min for authenticated; 10 req/min for comment submission |

---

## Authentication Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/auth/register` | Reader self-registration | None |
| POST | `/api/v1/auth/login` | Password login → JWT + refresh token | None |
| POST | `/api/v1/auth/refresh` | Rotate refresh token | Refresh token |
| POST | `/api/v1/auth/logout` | Invalidate session | Bearer |
| POST | `/api/v1/auth/password-reset/request` | Request password reset email | None |
| POST | `/api/v1/auth/password-reset/confirm` | Apply new password using token | None |
| GET | `/api/v1/auth/oauth/{provider}` | Initiate OAuth2 flow | None |
| GET | `/api/v1/auth/oauth/{provider}/callback` | OAuth2 callback | None |
| POST | `/api/v1/auth/2fa/setup` | Generate TOTP secret | Bearer |
| POST | `/api/v1/auth/2fa/verify` | Verify TOTP / OTP | Bearer |
| DELETE | `/api/v1/auth/2fa` | Disable 2FA | Bearer |

---

## Content Endpoints

| Method | Path | Description | Min Role |
|--------|------|-------------|----------|
| GET | `/api/v1/posts` | List published posts (public) | None |
| GET | `/api/v1/posts/{slug}` | Get published post (public) | None |
| GET | `/api/v1/posts/{id}` | Get post (any status) | Author |
| POST | `/api/v1/posts` | Create new post (draft) | Author |
| PATCH | `/api/v1/posts/{id}` | Update post fields | Author |
| DELETE | `/api/v1/posts/{id}` | Trash post | Author |
| GET | `/api/v1/posts/{id}/revisions` | List revisions | Author |
| GET | `/api/v1/posts/{id}/revisions/{rev_id}/diff` | Compare two revisions | Author |
| POST | `/api/v1/posts/{id}/revisions/{rev_id}/restore` | Restore revision as draft | Author |
| GET | `/api/v1/pages` | List published pages (public) | None |
| GET | `/api/v1/pages/{slug}` | Get published page (public) | None |
| POST | `/api/v1/pages` | Create page | Editor |
| PATCH | `/api/v1/pages/{id}` | Update page | Editor |
| DELETE | `/api/v1/pages/{id}` | Trash page | Editor |

---

## Publishing Workflow Endpoints

| Method | Path | Description | Min Role |
|--------|------|-------------|----------|
| PUT | `/api/v1/posts/{id}/submit` | Submit draft for review | Author |
| PUT | `/api/v1/posts/{id}/publish` | Publish post immediately | Editor |
| PUT | `/api/v1/posts/{id}/schedule` | Schedule post for future publish | Editor |
| PUT | `/api/v1/posts/{id}/return` | Return post to draft with feedback | Editor |
| PUT | `/api/v1/posts/{id}/archive` | Archive published post | Editor |
| GET | `/api/v1/posts?status=pending_review` | Editor submission queue | Editor |
| GET | `/api/v1/posts/{id}/preview` | Render preview in active theme | Author |

---

## Media Endpoints

| Method | Path | Description | Min Role |
|--------|------|-------------|----------|
| POST | `/api/v1/media` | Upload media file (multipart) | Author |
| GET | `/api/v1/media` | List media library items | Author |
| GET | `/api/v1/media/{id}` | Get media item metadata | Author |
| PATCH | `/api/v1/media/{id}` | Update alt text | Author |
| DELETE | `/api/v1/media/{id}` | Delete media item | Editor |

---

## Layout & Widget Endpoints

| Method | Path | Description | Min Role |
|--------|------|-------------|----------|
| GET | `/api/v1/themes` | List installed themes | Admin |
| POST | `/api/v1/themes` | Install theme (upload or marketplace slug) | Admin |
| PUT | `/api/v1/themes/{id}/activate` | Activate theme | Admin |
| GET | `/api/v1/themes/active/zones` | Get active theme zones with placements | Admin |
| GET | `/api/v1/themes/{id}/preview` | Generate preview URL | Admin |
| GET | `/api/v1/widgets` | List available widget types | Admin |
| POST | `/api/v1/layouts/zones/{zone}/widgets` | Place widget in zone | Admin |
| PATCH | `/api/v1/layouts/placements/{id}` | Update widget config | Admin |
| DELETE | `/api/v1/layouts/placements/{id}` | Remove widget from zone | Admin |
| PUT | `/api/v1/layouts/zones/{zone}/order` | Reorder widgets in zone | Admin |
| POST | `/api/v1/layouts/save` | Persist layout and invalidate cache | Admin |
| GET | `/api/v1/menus` | List navigation menus | Admin |
| POST | `/api/v1/menus` | Create navigation menu | Admin |
| PATCH | `/api/v1/menus/{id}` | Update menu name or zone | Admin |
| POST | `/api/v1/menus/{id}/items` | Add item to menu | Admin |
| PUT | `/api/v1/menus/{id}/items/order` | Reorder menu items | Admin |
| DELETE | `/api/v1/menus/{id}/items/{item_id}` | Remove menu item | Admin |

---

## Comment & Moderation Endpoints

| Method | Path | Description | Min Role |
|--------|------|-------------|----------|
| GET | `/api/v1/posts/{id}/comments` | List approved comments (public) | None |
| POST | `/api/v1/posts/{id}/comments` | Submit comment | None (rate limited) |
| GET | `/api/v1/moderation/comments` | Pending comment queue | Editor |
| PUT | `/api/v1/moderation/comments/{id}/approve` | Approve comment | Editor |
| DELETE | `/api/v1/moderation/comments/{id}` | Reject and delete comment | Editor |
| PUT | `/api/v1/moderation/comments/{id}/spam` | Mark as spam | Editor |

---

## SEO & Feed Endpoints

| Method | Path | Description | Min Role |
|--------|------|-------------|----------|
| GET | `/api/v1/seo/{content_type}/{content_id}` | Get SEO meta for content | Author |
| PUT | `/api/v1/seo/{content_type}/{content_id}` | Set SEO meta for content | Author |
| GET | `/api/v1/feed.xml` | RSS feed (public) | None |
| GET | `/api/v1/atom.xml` | Atom feed (public) | None |
| GET | `/api/v1/sitemap.xml` | Sitemap (public) | None |
| GET | `/api/v1/redirects` | List redirect rules | Admin |
| POST | `/api/v1/redirects` | Create redirect rule | Admin |
| PATCH | `/api/v1/redirects/{id}` | Update redirect rule | Admin |
| DELETE | `/api/v1/redirects/{id}` | Delete redirect rule | Admin |

---

## Analytics Endpoints

| Method | Path | Description | Min Role |
|--------|------|-------------|----------|
| POST | `/api/v1/analytics/events` | Ingest page-view event | None |
| GET | `/api/v1/analytics/dashboard` | Site dashboard summary | Admin |
| GET | `/api/v1/analytics/posts/{id}` | Per-post analytics | Author |
| GET | `/api/v1/analytics/authors` | Author performance table | Admin |
| GET | `/api/v1/analytics/export` | Export analytics CSV | Admin |

---

## Multi-Site Endpoints (Super Admin)

| Method | Path | Description | Min Role |
|--------|------|-------------|----------|
| GET | `/api/v1/sites` | List all sites | Super Admin |
| POST | `/api/v1/sites` | Provision new site | Super Admin |
| GET | `/api/v1/sites/{id}` | Get site details | Super Admin |
| PATCH | `/api/v1/sites/{id}` | Update site settings | Super Admin |
| DELETE | `/api/v1/sites/{id}` | Deactivate site | Super Admin |
| GET | `/api/v1/network/analytics` | Aggregate network analytics | Super Admin |
| POST | `/api/v1/network/plugins/update` | Push plugin update to all sites | Super Admin |
