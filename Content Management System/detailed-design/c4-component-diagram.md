# C4 Component Diagram

## Overview
This document provides the C4 Level 3 component diagrams for the major functional subsystems of the CMS backend.

---

## Component Diagram — IAM & Auth Subsystem

```mermaid
graph TB
    Client[Authenticated Client / Public Browser]

    subgraph "IAM & Auth Module"
        AuthRouter[Auth Router<br>POST /auth/login, /register, /refresh]
        UserRouter[User Router<br>GET/PATCH /users/{id}]
        JWTService[JWT Service<br>Issue, validate, refresh tokens]
        OAuthService[OAuth2 Service<br>Google / GitHub flow]
        TwoFAService[2FA Service<br>TOTP setup and verify]
        PermService[Permission Guard<br>Role enforcement per endpoint]
        InvitationService[Invitation Service<br>Send, validate, accept invites]
    end

    DB[(PostgreSQL)]
    Redis[(Redis — Token Store)]
    OAuthProvider[OAuth2 Provider]
    EmailSvc[Email Provider]

    Client --> AuthRouter
    Client --> UserRouter
    AuthRouter --> JWTService
    AuthRouter --> OAuthService
    AuthRouter --> TwoFAService
    OAuthService --> OAuthProvider
    AuthRouter --> InvitationService
    InvitationService --> EmailSvc
    JWTService --> Redis
    AuthRouter --> DB
    UserRouter --> DB
    PermService --> DB
```

---

## Component Diagram — Content & Publishing Subsystem

```mermaid
graph TB
    Author[Author / Editor Client]

    subgraph "Content & Publishing Module"
        PostRouter[Post Router]
        PageRouter[Page Router]
        PublishRouter[Publishing Router]

        DraftSvc[Draft & Auto-Save Service]
        RevisionSvc[Revision Service]
        WorkflowEngine[Workflow State Machine<br>draft→pending→published→archived]
        ScheduleSvc[Schedule Service<br>Job enqueue and cancel]
        FeedGen[RSS/Atom Feed Generator]
        SitemapGen[Sitemap Generator]
        PublishNotify[Publish Event Notifier]
        SearchIndexer[Search Indexer Client]
    end

    DB[(PostgreSQL)]
    Queue[(Redis Queue)]
    SearchIdx[(Search Index)]
    CDN[CDN Invalidator]

    Author --> PostRouter
    Author --> PageRouter
    Author --> PublishRouter

    PostRouter --> DraftSvc
    PostRouter --> RevisionSvc
    PublishRouter --> WorkflowEngine
    WorkflowEngine --> FeedGen
    WorkflowEngine --> SitemapGen
    WorkflowEngine --> PublishNotify
    WorkflowEngine --> ScheduleSvc
    WorkflowEngine --> SearchIndexer

    DraftSvc --> DB
    RevisionSvc --> DB
    WorkflowEngine --> DB
    ScheduleSvc --> Queue
    FeedGen --> DB
    FeedGen --> CDN
    SitemapGen --> DB
    SitemapGen --> CDN
    PublishNotify --> DB
    PublishNotify --> Queue
    SearchIndexer --> SearchIdx
```

---

## Component Diagram — Layout & Widget Subsystem

```mermaid
graph TB
    AdminClient[Admin Client]
    Visitor[Site Visitor]

    subgraph "Layout & Widget Module"
        ThemeRouter[Theme Router]
        WidgetRouter[Widget Router]
        MenuRouter[Menu Router]

        ThemeSvc[Theme Lifecycle Service<br>Install, activate, preview, migrate zones]
        WidgetRegistry[Widget Registry<br>Built-in + plugin-registered types]
        ZoneSvc[Zone Placement Service<br>Place, reorder, remove, override]
        MenuSvc[Navigation Menu Service]
        LayoutRenderer[Layout Renderer<br>Resolve zones + widget data at request time]
        CacheInvalidator[Cache Invalidation Service]
    end

    DB[(PostgreSQL)]
    Storage[(Object Storage — Theme Packages)]
    CDN[CDN]

    AdminClient --> ThemeRouter
    AdminClient --> WidgetRouter
    AdminClient --> MenuRouter

    ThemeRouter --> ThemeSvc
    WidgetRouter --> WidgetRegistry
    WidgetRouter --> ZoneSvc
    MenuRouter --> MenuSvc

    ThemeSvc --> DB
    ThemeSvc --> Storage
    ZoneSvc --> DB
    ZoneSvc --> CacheInvalidator
    WidgetRegistry --> DB
    MenuSvc --> DB
    CacheInvalidator --> CDN

    Visitor --> LayoutRenderer
    LayoutRenderer --> ZoneSvc
    LayoutRenderer --> WidgetRegistry
    LayoutRenderer --> DB
```

---

## Component Diagram — Comment & Moderation Subsystem

```mermaid
graph TB
    Reader[Reader / Guest]
    Moderator[Editor / Admin]

    subgraph "Comment Module"
        CommentRouter[Comment Router<br>POST /posts/{id}/comments]
        ModRouter[Moderation Router<br>GET /moderation/comments]

        CommentSvc[Comment Service<br>Submit, thread, approve, reject]
        SpamClient[Spam Filter Client]
        ModerationSvc[Moderation Service<br>Queue management, bulk actions]
        CommentNotify[Comment Notification Service]
    end

    DB[(PostgreSQL)]
    Queue[(Redis Queue)]
    SpamAPI[Spam Filter API]
    EmailSvc[Email Provider]

    Reader --> CommentRouter
    Moderator --> ModRouter

    CommentRouter --> CommentSvc
    CommentSvc --> SpamClient
    SpamClient --> SpamAPI
    CommentSvc --> ModerationSvc
    CommentSvc --> CommentNotify
    ModerationSvc --> DB
    CommentSvc --> DB
    CommentNotify --> Queue
    Queue --> EmailSvc
    ModRouter --> ModerationSvc
```

---

## Component Diagram — Analytics Subsystem

```mermaid
graph TB
    PublicVisitor[Public Visitor]
    AdminUser[Admin User]
    AuthorUser[Author User]
    Worker[Background Worker]

    subgraph "Analytics Module"
        EventRouter[Event Router<br>POST /analytics/events]
        DashboardRouter[Dashboard Router<br>GET /analytics/dashboard]

        IngestionSvc[Event Ingestion Service<br>Write page-view events]
        RollupSvc[Daily Rollup Service<br>Aggregate raw events]
        QuerySvc[Dashboard Query Service<br>Read rollup tables with filters]
        ExportSvc[Export Service<br>Generate CSV exports]
    end

    DB[(PostgreSQL)]
    Storage[(Object Storage — CSV Exports)]

    PublicVisitor --> EventRouter
    EventRouter --> IngestionSvc
    IngestionSvc --> DB

    AdminUser --> DashboardRouter
    AuthorUser --> DashboardRouter
    DashboardRouter --> QuerySvc
    QuerySvc --> DB

    Worker --> RollupSvc
    RollupSvc --> DB

    AdminUser --> ExportSvc
    ExportSvc --> DB
    ExportSvc --> Storage
```
