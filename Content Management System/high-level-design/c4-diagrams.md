# C4 Diagrams

## Overview
C4 diagrams describe the CMS architecture at four levels of zoom: System Context, Container, Component, and Code.

---

## Level 1: System Context Diagram

```mermaid
graph TB
    Reader((Reader))
    Author((Author))
    Editor((Editor))
    Admin((Admin))
    SuperAdmin((Super Admin))

    subgraph "CMS Platform"
        System[Content Management System<br>Widget-based page builder, multi-author publishing workflow,<br>multi-site management, plugin architecture]
    end

    EmailSvc[Email Provider<br>SES / SendGrid / Mailgun]
    SpamSvc[Spam Filter Service<br>Akismet-compatible API]
    MediaStorage[Object Storage<br>S3-compatible]
    SearchSvc[Search Service<br>Meilisearch]
    CDN[CDN<br>CloudFront / Fastly]
    OAuth[OAuth2 Provider<br>Google / GitHub]

    Reader -->|"read, comment, subscribe, search"| System
    Author -->|"create posts, upload media, manage drafts"| System
    Editor -->|"review, publish, manage taxonomy"| System
    Admin -->|"configure themes, widgets, users, plugins"| System
    SuperAdmin -->|"manage sites, global users, push updates"| System

    System -->|"transactional and digest emails"| EmailSvc
    System -->|"score comments for spam"| SpamSvc
    System -->|"store and retrieve media"| MediaStorage
    System -->|"index and query content"| SearchSvc
    System -->|"serve cached assets and pages"| CDN
    System -->|"delegate social login"| OAuth
```

---

## Level 2: Container Diagram

```mermaid
graph TB
    Reader((Reader))
    Author((Author))
    Editor((Editor))
    Admin((Admin))

    subgraph "CMS Platform"
        PublicFront[Public Frontend<br>SSR web application<br>Next.js / Astro]
        AdminSPA[Admin & Editor SPA<br>React SPA]
        AuthorSPA[Author Dashboard<br>React SPA]

        API[CMS API Server<br>FastAPI — versioned REST endpoints<br>and domain modules]
        Worker[Background Worker<br>Scheduled jobs: publish, email dispatch,<br>media processing, index sync, cache invalidation]
        WS[WebSocket Server<br>Real-time notifications for editors and admins]

        DB[(PostgreSQL<br>Primary content, users, layout, analytics)]
        Redis[(Redis<br>Sessions, rate limiting, job queue, short-term cache)]
        Storage[(Object Storage<br>Media assets, theme & plugin packages)]
        SearchIdx[(Search Index<br>Meilisearch)]
    end

    EmailSvc[Email Provider]
    SpamSvc[Spam Filter]
    CDN[CDN]
    OAuth[OAuth2 Provider]

    Reader --> PublicFront
    Author --> AuthorSPA
    Editor --> AdminSPA
    Admin --> AdminSPA

    PublicFront --> API
    AuthorSPA --> API
    AdminSPA --> API
    AdminSPA --> WS

    API --> DB
    API --> Redis
    API --> Storage
    API --> SearchIdx
    API --> Worker
    API --> SpamSvc
    API --> OAuth

    Worker --> DB
    Worker --> Storage
    Worker --> EmailSvc
    Worker --> SearchIdx
    Worker --> CDN

    PublicFront --> CDN
```

---

## Level 3: Component Diagram — Content & Publishing Core

```mermaid
graph TB
    AuthorClient[Author / Editor Client]

    subgraph "Content & Publishing Core"
        ContentAPI[Content Routers<br>POST /posts, /pages, /revisions]
        TaxonomyAPI[Taxonomy Routers<br>/categories, /tags]
        MediaAPI[Media Routers<br>/media]
        PublishingAPI[Publishing Routers<br>/posts/{id}/submit|publish|schedule|return]

        DraftService[Draft & Auto-Save Service]
        RevisionService[Revision Snapshot Service]
        PublishService[Publish / Schedule Service]
        FeedService[RSS/Atom Feed Generator]
        SitemapService[Sitemap Builder]
        NotifyService[Publishing Event Notifier]
    end

    DB[(PostgreSQL)]
    Redis[(Redis Queue)]
    SearchIdx[(Search Index)]
    Worker[Background Worker]

    AuthorClient --> ContentAPI
    AuthorClient --> TaxonomyAPI
    AuthorClient --> MediaAPI
    AuthorClient --> PublishingAPI

    ContentAPI --> DraftService
    ContentAPI --> RevisionService
    PublishingAPI --> PublishService
    PublishService --> FeedService
    PublishService --> SitemapService
    PublishService --> NotifyService

    DraftService --> DB
    RevisionService --> DB
    PublishService --> DB
    PublishService --> Worker
    FeedService --> DB
    SitemapService --> DB
    NotifyService --> DB
    NotifyService --> Redis
    ContentAPI --> SearchIdx
```

---

## Level 3: Component Diagram — Layout & Widget Core

```mermaid
graph TB
    AdminClient[Admin Client]

    subgraph "Layout & Widget Core"
        ThemeAPI[Theme Routers<br>/themes]
        WidgetAPI[Widget Routers<br>/widgets, /layouts]
        MenuAPI[Menu Routers<br>/menus]

        ThemeService[Theme Lifecycle Service]
        WidgetRegistry[Widget Registry]
        ZoneService[Zone Placement Service]
        MenuService[Navigation Menu Service]
        LayoutRenderer[Layout Renderer<br>Resolves zones and widget data at request time]
        CacheInvalidator[Cache Invalidation Service]
    end

    DB[(PostgreSQL)]
    CDN[CDN]
    Storage[(Object Storage)]

    AdminClient --> ThemeAPI
    AdminClient --> WidgetAPI
    AdminClient --> MenuAPI

    ThemeAPI --> ThemeService
    WidgetAPI --> WidgetRegistry
    WidgetAPI --> ZoneService
    MenuAPI --> MenuService

    ThemeService --> DB
    ThemeService --> Storage
    ZoneService --> DB
    ZoneService --> CacheInvalidator
    MenuService --> DB
    WidgetRegistry --> DB
    LayoutRenderer --> ZoneService
    LayoutRenderer --> WidgetRegistry
    CacheInvalidator --> CDN
```

---

## Current-Future Boundary

| Area | Current Design |
|------|---------------|
| Architecture | Modular monolith (FastAPI) |
| Search | Meilisearch for full-text; filtered DB queries as fallback |
| Real-time notifications | WebSocket for admin/editor panel; email for authors and readers |
| Plugin hooks | In-process hook invocation; external webhook plugins are a future option |
| Multi-site | Schema-per-tenant PostgreSQL; shared application layer |
| Recommendation | Tag/category affinity for related-posts widget; ML-based ranking is a future option |
