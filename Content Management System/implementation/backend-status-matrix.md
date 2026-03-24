# Backend Status Matrix

## Overview
This matrix tracks the implementation status of each CMS backend capability.

---

## Module Status

### IAM & Authentication

| Capability | Status | Notes |
|-----------|--------|-------|
| JWT login (email + password) | ✅ Implemented | Access + refresh token pair |
| JWT refresh rotation | ✅ Implemented | Refresh token invalidated on rotation |
| Reader self-registration | ✅ Implemented | Email verification link |
| OAuth2 social login (Google) | ✅ Implemented | Account linking on first login |
| OAuth2 social login (GitHub) | ✅ Implemented | |
| Password reset via email | ✅ Implemented | 24 h expiry token |
| TOTP-based 2FA | ✅ Implemented | pyotp; QR code provisioning |
| Email OTP 2FA | ✅ Implemented | Fallback for users without authenticator |
| Role-based permission guard | ✅ Implemented | Dependency injected per router |
| Multi-site role resolution | ✅ Implemented | Per-site membership; cross-site for Super Admin |
| Invitation accept flow | ✅ Implemented | Token + role assignment |
| Session invalidation on suspend | ✅ Implemented | Redis token blocklist |

### Content Authoring

| Capability | Status | Notes |
|-----------|--------|-------|
| Post CRUD (draft) | ✅ Implemented | |
| Page CRUD | ✅ Implemented | |
| Auto-save (server-side idempotent PATCH) | ✅ Implemented | Client sends at interval |
| Revision snapshot on save | ✅ Implemented | SQLAlchemy after_update listener |
| Revision diff endpoint | ✅ Implemented | Unified diff of content fields |
| Revision restore | ✅ Implemented | New revision created on restore |
| Slug auto-generation | ✅ Implemented | Deduplication with numeric suffix |
| Rich text content sanitisation | ✅ Implemented | bleach allowlist |
| SEO meta fields per post/page | ✅ Implemented | |

### Publishing Workflow

| Capability | Status | Notes |
|-----------|--------|-------|
| Submit for review (draft → pending) | ✅ Implemented | Editor notified |
| Publish immediately (pending → published) | ✅ Implemented | |
| Schedule future publish | ✅ Implemented | ARQ job enqueued |
| Scheduled auto-publish (worker) | ✅ Implemented | Runs every 60 s |
| Return to draft with feedback | ✅ Implemented | Author notified |
| Archive post | ✅ Implemented | |
| Trash and restore | ✅ Implemented | Soft delete; permanent purge after 30 days |
| RSS/Atom feed regeneration on publish | ✅ Implemented | |
| sitemap.xml rebuild on publish | ✅ Implemented | |
| CDN cache invalidation on publish | ✅ Implemented | |
| Search index update on publish/unpublish | ✅ Implemented | Async in worker |

### Taxonomy

| Capability | Status | Notes |
|-----------|--------|-------|
| Category CRUD with parent-child hierarchy | ✅ Implemented | Up to 5 levels |
| Tag CRUD | ✅ Implemented | |
| Tag merge (re-tag posts, old tag redirect) | ✅ Implemented | |
| Post-category and post-tag assignment | ✅ Implemented | |
| Per-taxonomy term feeds | ✅ Implemented | Category and tag RSS/Atom |

### Media

| Capability | Status | Notes |
|-----------|--------|-------|
| File upload (image, document) | ✅ Implemented | S3-compatible storage |
| Async image resize (thumbnail, medium, large) | ✅ Implemented | ARQ worker + Pillow |
| Media library list and search | ✅ Implemented | Filter by MIME type, date |
| Alt text management | ✅ Implemented | |
| Media deletion | ✅ Implemented | Removes all size variants from storage |
| CDN-backed media URLs | ✅ Implemented | |

### Layout & Widgets

| Capability | Status | Notes |
|-----------|--------|-------|
| Theme install from package upload | ✅ Implemented | |
| Theme activate with zone migration | ✅ Implemented | Unmapped zone helper |
| Theme live preview | ✅ Implemented | Isolated preview session cookie |
| Widget Registry (built-in types) | ✅ Implemented | See widget list below |
| Zone placement CRUD | ✅ Implemented | |
| Widget reorder within zone | ✅ Implemented | Position-based ordering |
| Per-page layout override | ✅ Implemented | `page_override_id` in placement |
| Layout save + CDN cache invalidation | ✅ Implemented | |
| Navigation menu builder | ✅ Implemented | Multi-level, multi-zone |
| Plugin-registered widgets | ✅ Implemented | Via `on_activate` hook |

### Built-in Widget Inventory

| Widget Type | Status |
|-------------|--------|
| Recent Posts | ✅ Implemented |
| Popular Posts (by views) | ✅ Implemented |
| Category List | ✅ Implemented |
| Tag Cloud | ✅ Implemented |
| Search Box | ✅ Implemented |
| Author Bio | ✅ Implemented |
| RSS Feed Link | ✅ Implemented |
| Social Links | ✅ Implemented |
| Custom HTML | ✅ Implemented |
| Image Banner | ✅ Implemented |
| Newsletter Signup | ✅ Implemented |
| Related Posts | ✅ Implemented |

### Comments & Moderation

| Capability | Status | Notes |
|-----------|--------|-------|
| Comment submission (guest + registered) | ✅ Implemented | |
| Threaded comments | ✅ Implemented | Configurable max depth |
| Spam filter integration | ✅ Implemented | Akismet-compatible adapter |
| Auto-approve for trusted readers | ✅ Implemented | |
| Moderation queue (pending comments) | ✅ Implemented | |
| Approve / Reject / Spam actions | ✅ Implemented | |
| Bulk moderation actions | ✅ Implemented | |
| Post author notification on new comment | ✅ Implemented | |
| Parent commenter reply notification | ✅ Implemented | |

### SEO & Feeds

| Capability | Status | Notes |
|-----------|--------|-------|
| Per-content SEO meta (title, description, OG image) | ✅ Implemented | |
| Auto-generated meta fallback | ✅ Implemented | |
| Global RSS and Atom feeds | ✅ Implemented | |
| Per-author / per-category / per-tag feeds | ✅ Implemented | |
| sitemap.xml (posts + pages) | ✅ Implemented | |
| Redirect rule management (301/302) | ✅ Implemented | |
| Canonical URL enforcement | ✅ Implemented | |

### Analytics

| Capability | Status | Notes |
|-----------|--------|-------|
| Page-view event ingestion | ✅ Implemented | Fire-and-forget beacon |
| Daily analytics rollup (worker) | ✅ Implemented | Runs nightly |
| Site dashboard (views, visitors, top posts) | ✅ Implemented | |
| Per-post analytics for authors | ✅ Implemented | |
| Author performance table | ✅ Implemented | |
| CSV export | ✅ Implemented | Async export to S3 |

### Notifications

| Capability | Status | Notes |
|-----------|--------|-------|
| In-app notification store | ✅ Implemented | |
| Real-time notification via WebSocket (admin/editor) | ✅ Implemented | |
| Email notifications (all transaction types) | ✅ Implemented | |
| Newsletter subscriber digest (worker) | ✅ Implemented | Immediate, daily, and weekly frequencies |
| Notification preference management | ✅ Implemented | |

### Plugins

| Capability | Status | Notes |
|-----------|--------|-------|
| Plugin install (upload) | ✅ Implemented | |
| Compatibility check | ✅ Implemented | API version match |
| Activate / Deactivate lifecycle | ✅ Implemented | `on_activate` / `on_deactivate` hooks |
| Hook engine (event-based) | ✅ Implemented | |
| Plugin settings page registration | ✅ Implemented | |
| Plugin update | ⬜ Planned | Auto-update from marketplace |

### Multi-Site

| Capability | Status | Notes |
|-----------|--------|-------|
| Site provisioning | ✅ Implemented | Schema-per-tenant |
| Per-site theme, plugin, and user isolation | ✅ Implemented | |
| Network analytics aggregation | ✅ Implemented | |
| Cross-site global user management | ✅ Implemented | |
| Push plugin update to all sites | ⬜ Planned | Bulk update flow |

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ Implemented | Feature is fully implemented and tested |
| 🔄 In Progress | Implementation started but not complete |
| ⬜ Planned | Designed but not yet implemented |
| ❌ Descoped | Removed from current scope |
