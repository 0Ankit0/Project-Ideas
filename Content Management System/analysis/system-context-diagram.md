# System Context Diagram

## Overview
The system context diagram shows the CMS and its interactions with external actors and systems at the highest level of abstraction.

---

## System Context

```mermaid
graph TB
    Reader((Reader))
    Author((Author))
    Editor((Editor))
    Admin((Admin))
    SuperAdmin((Super Admin))

    subgraph "Content Management System"
        CMS[CMS Platform<br>Widget-based page builder, publishing workflow,<br>multi-author support, multi-site management]
    end

    EmailProvider[Email Provider<br>SendGrid / SES / Mailgun]
    SpamFilter[Spam Filter Service<br>Akismet-compatible API]
    MediaStorage[Object / Media Storage<br>S3-compatible]
    SearchService[Search Service<br>Meilisearch / Elasticsearch]
    Analytics[Analytics Service<br>Internal or GA4 / Plausible]
    CDN[CDN<br>CloudFront / Fastly]
    OAuth[OAuth2 Provider<br>Google / GitHub]

    Reader -->|read posts, comment, subscribe| CMS
    Author -->|create posts, upload media| CMS
    Editor -->|review, publish, manage taxonomy| CMS
    Admin -->|configure themes, widgets, plugins, users| CMS
    SuperAdmin -->|manage sites, global users, network updates| CMS

    CMS -->|transactional & digest emails| EmailProvider
    CMS -->|comment spam scoring| SpamFilter
    CMS -->|store & retrieve media assets| MediaStorage
    CMS -->|index and query content| SearchService
    CMS -->|ingest and query page-view events| Analytics
    CMS -->|serve static assets and cached pages| CDN
    CMS -->|delegate social login| OAuth
```

---

## External System Descriptions

| External System | Purpose | Interaction |
|-----------------|---------|-------------|
| **Email Provider** | Delivers transactional emails (invitations, comment notifications, newsletter digests, password resets) | CMS calls provider API to send; provider webhooks report delivery/bounce status |
| **Spam Filter Service** | Scores incoming comments for spam probability | CMS submits comment text, author, and IP; service returns spam score and classification |
| **Object / Media Storage** | Stores uploaded images, documents, theme assets, and plugin packages | CMS uploads files on ingest; serves via CDN-backed presigned URLs |
| **Search Service** | Provides fast full-text search over published posts and pages | CMS indexes documents on publish/update/delete events; frontend queries via CMS API proxy |
| **Analytics Service** | Collects and aggregates page-view events for the analytics dashboard | CMS frontend sends beacon events; admin dashboard reads aggregated data via API |
| **CDN** | Caches and serves static assets and optionally full HTML pages at edge nodes | CMS invalidates CDN cache on publish/unpublish events |
| **OAuth2 Provider** | Enables social login for readers and authors | CMS acts as OAuth2 client; redirects users to provider; receives identity tokens |
