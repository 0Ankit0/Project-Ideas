# High-Level Architecture Diagram

## Overview
The CMS is designed as a modular monolith with clear domain boundaries. The backend provides a REST API consumed by the Admin SPA, Author/Editor dashboard, and public-facing frontend. A background worker handles scheduled publishing, newsletter dispatch, media processing, and cache invalidation.

---

## System Architecture Overview

```mermaid
graph TB
    subgraph "Clients"
        PublicFront[Public Frontend<br>SSR / Static Site]
        AdminSPA[Admin & Editor SPA]
        AuthorSPA[Author Dashboard SPA]
    end

    subgraph "Edge"
        CDN[CDN<br>Static assets & cached pages]
        WAF[WAF / Rate Limiter]
        LB[Load Balancer]
    end

    subgraph "Application"
        API[CMS API Server<br>REST / FastAPI]

        subgraph "Core Modules"
            IAM[IAM & Auth]
            Content[Content<br>Posts, Pages, Revisions]
            Media[Media Management]
            Taxonomy[Taxonomy]
            Layout[Layout & Widgets]
            Publishing[Publishing Workflow]
            Comments[Comments & Moderation]
            SEO[SEO & Feeds]
            Plugins[Plugin Registry]
            Analytics[Analytics Ingestion]
            Notify[Notifications]
            MultiSite[Multi-Site Manager]
        end

        Worker[Background Worker<br>Scheduled publish, email dispatch,<br>media processing, cache invalidation]
    end

    subgraph "Data"
        DB[(PostgreSQL<br>Primary content store)]
        Redis[(Redis<br>Sessions, cache, job queue)]
        Storage[(Object Storage<br>Media assets, theme packages)]
        SearchIdx[(Search Index<br>Meilisearch)]
    end

    subgraph "External Services"
        EmailSvc[Email Provider<br>SES / SendGrid]
        SpamSvc[Spam Filter API]
        OAuth[OAuth2 Provider<br>Google / GitHub]
        AnalyticsSvc[Analytics Service<br>Internal or third-party]
    end

    PublicFront --> CDN
    AdminSPA --> CDN
    AuthorSPA --> CDN
    CDN --> WAF
    WAF --> LB
    LB --> API

    API --> IAM
    API --> Content
    API --> Media
    API --> Taxonomy
    API --> Layout
    API --> Publishing
    API --> Comments
    API --> SEO
    API --> Plugins
    API --> Analytics
    API --> Notify
    API --> MultiSite

    Content --> DB
    Media --> DB
    Media --> Storage
    Taxonomy --> DB
    Layout --> DB
    Publishing --> DB
    Comments --> DB
    SEO --> DB
    Analytics --> DB
    Notify --> DB
    MultiSite --> DB
    IAM --> DB
    IAM --> Redis

    Content --> SearchIdx
    Taxonomy --> SearchIdx

    Publishing --> Worker
    Notify --> Worker
    Media --> Worker

    Worker --> EmailSvc
    Worker --> Storage
    Worker --> CDN

    Comments --> SpamSvc
    IAM --> OAuth
    Analytics --> AnalyticsSvc
```

---

## Runtime Interaction Model

```mermaid
graph LR
    Client[Client Request] --> API[CMS API Router]
    API --> Domain[Domain Service / Repository]
    Domain --> DB[(PostgreSQL)]
    Domain --> Cache[(Redis)]

    Domain --> Event[Domain Event / Notification]
    Event --> Worker[Background Worker]
    Worker --> Email[Email Provider]
    Worker --> Media[Media Processor]
    Worker --> CDN[CDN Invalidation]

    Domain --> Search[Search Indexer]
    Search --> SearchIdx[(Search Index)]
```

---

## Key Backend Module Responsibilities

| Module | Main Responsibilities |
|--------|----------------------|
| IAM | JWT auth, refresh tokens, OAuth2, 2FA (TOTP/OTP), role/permission enforcement |
| Content | Post/page CRUD, auto-save, revision snapshots, diff computation, draft/publish states |
| Media | File upload, image resizing, media library, storage abstraction, CDN URL generation |
| Taxonomy | Category and tag CRUD, custom taxonomy definitions, term merging |
| Layout | Theme registry, widget library, zone-based placement, per-page overrides, menu builder |
| Publishing | Workflow state machine, scheduled-publish job scheduling, notification dispatch |
| Comments | Comment submission, threading, moderation queue, spam filter integration |
| SEO | Meta field management, sitemap generation, canonical URL enforcement, redirect rules |
| Plugins | Plugin registry, lifecycle management, hook and extension point invocation |
| Analytics | Page-view event ingestion, aggregation, dashboard query API |
| Notifications | In-app notification store, email notification dispatch, preference management |
| Multi-Site | Tenant provisioning, cross-site user management, network analytics aggregation |
