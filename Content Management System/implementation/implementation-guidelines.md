# Implementation Guidelines

## Overview
This document provides implementation guidelines for the CMS backend, covering technology choices, coding standards, module boundaries, and development patterns.

---

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| API Framework | FastAPI (Python 3.11+) | Async-native, automatic OpenAPI docs, type-safe via Pydantic |
| ORM | SQLAlchemy 2.x (async) | Mature, supports PostgreSQL-specific features |
| Database | PostgreSQL 15+ | JSONB for widget configs, full-text search fallback, strong ACID guarantees |
| Cache / Queue | Redis 7 (via ARQ or Celery) | Session store, rate limiting, background job queue |
| Search | Meilisearch | Typo-tolerant, fast, easy to self-host |
| Media Processing | Pillow (Python) via worker | Resize and optimise images asynchronously |
| Auth | python-jose (JWT) + pyotp (TOTP) | Standard libraries with well-understood security properties |
| Email | SMTP abstraction (SES/SendGrid adapter) | Provider-agnostic via adapter pattern |
| Frontend (Public) | Next.js 14+ (App Router, SSR) | SEO-optimised server-side rendering, ISR for post pages |
| Frontend (Admin/Author) | React + Vite + TanStack Query | SPA for complex interactive editors |
| Containerisation | Docker + Kubernetes (Helm charts) | Standard cloud-native deployment |

---

## Project Structure

```
cms-backend/
├── app/
│   ├── main.py                  # FastAPI app factory, lifespan events
│   ├── config.py                # Settings (pydantic-settings)
│   ├── database.py              # Async SQLAlchemy engine and session
│   ├── dependencies.py          # Shared FastAPI dependencies (auth, pagination)
│   │
│   ├── iam/                     # Auth, users, roles, 2FA, OAuth2
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── permissions.py
│   │
│   ├── content/                 # Posts, pages, revisions
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── models.py
│   │   └── schemas.py
│   │
│   ├── publishing/              # Workflow state machine, scheduling
│   │   ├── router.py
│   │   ├── workflow.py          # State machine transitions
│   │   ├── scheduler.py         # ARQ job registration
│   │   ├── feed.py              # RSS/Atom feed generation
│   │   └── sitemap.py           # sitemap.xml generation
│   │
│   ├── taxonomy/                # Categories, tags, custom taxonomies
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── models.py
│   │   └── schemas.py
│   │
│   ├── media/                   # Upload, library, resize
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── processor.py         # Image resize using Pillow
│   │   ├── storage.py           # S3-compatible storage abstraction
│   │   └── models.py
│   │
│   ├── layout/                  # Themes, widgets, zones, menus
│   │   ├── router.py
│   │   ├── theme_service.py
│   │   ├── widget_registry.py   # Built-in + plugin-registered widgets
│   │   ├── zone_service.py
│   │   ├── renderer.py          # Zone resolution at request time
│   │   ├── menu_service.py
│   │   └── models.py
│   │
│   ├── comments/                # Comment submission, threading, moderation
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── moderation.py
│   │   ├── spam_client.py       # Spam filter API adapter
│   │   └── models.py
│   │
│   ├── seo/                     # Meta fields, redirects
│   │   ├── router.py
│   │   ├── service.py
│   │   └── models.py
│   │
│   ├── analytics/               # Event ingestion, rollups, dashboard
│   │   ├── router.py
│   │   ├── ingestion.py
│   │   ├── rollup.py
│   │   ├── query.py
│   │   └── models.py
│   │
│   ├── notifications/           # In-app store, email dispatch
│   │   ├── service.py
│   │   ├── email_dispatcher.py
│   │   └── models.py
│   │
│   ├── plugins/                 # Plugin registry and hook engine
│   │   ├── router.py
│   │   ├── registry.py
│   │   ├── hooks.py             # Hook system: on_post_publish, on_widget_render, etc.
│   │   └── models.py
│   │
│   ├── sites/                   # Multi-site and tenant management
│   │   ├── router.py
│   │   ├── service.py
│   │   └── models.py
│   │
│   └── worker/                  # Background job definitions
│       ├── jobs.py              # ARQ job functions
│       └── scheduler_config.py
│
├── alembic/                     # Database migrations
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── test_publishing_workflow.py
│   ├── test_widget_placement.py
│   ├── test_comment_moderation.py
│   └── ...
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

## Module Design Principles

### 1. Workflow State Machine
All post and comment state transitions must go through the `WorkflowEngine`. Direct model `status` mutations outside the engine are prohibited. Each transition validates the current state, the actor's role, and records an event log entry.

```python
# Example: Transition a post to published
await workflow_engine.transition(
    post=post,
    to_state=PostStatus.PUBLISHED,
    actor=current_user,
    context={"published_at": datetime.utcnow()},
)
```

### 2. Widget Registry Pattern
Widgets are registered via a decorator in the `WidgetRegistry`. Built-in widgets are registered on application startup. Plugins register their widgets during their `on_activate` hook.

```python
@widget_registry.register("recent_posts")
class RecentPostsWidget(BaseWidget):
    config_schema = RecentPostsConfig  # Pydantic model
    
    async def render(self, config: RecentPostsConfig, context: RenderContext) -> str:
        posts = await post_repo.list_recent(site_id=context.site_id, limit=config.count)
        return templates.render("widgets/recent_posts.html", posts=posts)
```

### 3. Zone Placement and Rendering
The `LayoutRenderer` resolves widget placements at request time by querying the zone placement table. Results are cached in Redis for a configurable TTL. The cache is invalidated on every layout save or theme activation.

### 4. Plugin Hook System
Hooks allow plugins to extend CMS behaviour without modifying core code. Key hooks:

| Hook Name | Trigger | Use Case |
|-----------|---------|----------|
| `on_post_publish` | Post transitions to published | Crosspost to social media |
| `on_comment_approve` | Comment approved | Send mention notification |
| `on_widget_render` | Widget renders | Inject custom analytics code |
| `on_admin_menu_build` | Admin sidebar built | Add plugin settings link |
| `on_page_request` | Public page requested | Add custom HTTP headers |

### 5. Multi-Site Isolation
All repository methods accept `site_id` as the first argument and apply it as a mandatory filter. The `get_current_site` FastAPI dependency resolves site context from the request host or an `X-Site-ID` header for API clients.

### 6. Revision Strategy
Revisions are captured automatically via a SQLAlchemy event listener on Post and Page `after_update` events. The full content snapshot is stored; no delta compression is applied at this stage to keep the implementation simple and restore operations fast.

---

## Security Checklist

- [ ] All state-mutating endpoints require authenticated JWT with appropriate role
- [ ] All rich text content is sanitised server-side using `bleach` or equivalent before storage
- [ ] File uploads are validated for MIME type and max size before processing
- [ ] Rate limiting applied to comment submission (10/min per IP) and login (5/min per IP)
- [ ] CSRF protection enabled for non-API browser sessions (SameSite=Strict cookies)
- [ ] `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY` headers on all responses
- [ ] SQL queries exclusively via SQLAlchemy ORM (no raw string interpolation)
- [ ] Spam filter called on every comment before storage
- [ ] Plugin packages validated against a checksum and scanned before activation

---

## Performance Guidelines

| Area | Guideline |
|------|-----------|
| Database | Use indexed columns for `site_id`, `status`, `slug`, `published_at` on all content tables |
| Redis caching | Cache rendered zone HTML with key `zone:{site_id}:{zone_name}:{theme_id}` TTL 5 min |
| Image resizing | Perform async in worker; do not resize in the API request path |
| Feed generation | Cache RSS/Atom at CDN; regenerate only on publish/unpublish events |
| Search indexing | Async in worker; API returns 200 immediately after DB write |
| Analytics ingestion | Fire-and-forget POST to `/analytics/events`; no synchronous response payload needed |
| Pagination | Default 20, max 100 items per page for all list endpoints |

---

## Testing Strategy

| Level | Tool | Coverage Target |
|-------|------|----------------|
| Unit | pytest + pytest-asyncio | Business logic in services and state machine |
| Integration | pytest + test database | Router → service → DB round-trips |
| API contract | httpx TestClient | All published API endpoints |
| Widget rendering | HTML snapshot tests | Each built-in widget type |
| End-to-end | Playwright | Critical reader and author journeys |
