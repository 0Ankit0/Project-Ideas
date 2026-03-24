# System Sequence Diagrams

## Overview
System sequence diagrams model the interactions between external actors and the CMS as a black box, focusing on the messages exchanged at the system boundary.

---

## 1. Author Creates and Submits a Post

```mermaid
sequenceDiagram
    actor Author
    participant CMS as CMS System

    Author->>CMS: POST /api/v1/posts (title, content, status=draft)
    CMS-->>Author: 201 Created {post_id, slug, status: draft}

    Author->>CMS: PATCH /api/v1/posts/{post_id} (content update)
    CMS-->>Author: 200 OK {revision_id, updated_at}

    Author->>CMS: POST /api/v1/media (image file)
    CMS-->>Author: 201 Created {media_id, thumbnail_url, medium_url, large_url}

    Author->>CMS: PATCH /api/v1/posts/{post_id} (featured_image_id)
    CMS-->>Author: 200 OK

    Author->>CMS: PUT /api/v1/posts/{post_id}/submit
    CMS-->>Author: 200 OK {status: pending_review, notified_editor: true}
```

---

## 2. Editor Reviews and Publishes

```mermaid
sequenceDiagram
    actor Editor
    participant CMS as CMS System

    Editor->>CMS: GET /api/v1/posts?status=pending_review
    CMS-->>Editor: 200 OK [{post_id, title, author, submitted_at}, ...]

    Editor->>CMS: GET /api/v1/posts/{post_id}
    CMS-->>Editor: 200 OK {full post content, metadata}

    Editor->>CMS: GET /api/v1/posts/{post_id}/preview
    CMS-->>Editor: 200 OK (rendered HTML preview)

    alt Publish now
        Editor->>CMS: PUT /api/v1/posts/{post_id}/publish
        CMS-->>Editor: 200 OK {status: published, published_at}
    else Schedule
        Editor->>CMS: PUT /api/v1/posts/{post_id}/schedule (scheduled_at)
        CMS-->>Editor: 200 OK {status: scheduled, scheduled_at}
    else Return to draft
        Editor->>CMS: PUT /api/v1/posts/{post_id}/return (feedback)
        CMS-->>Editor: 200 OK {status: draft}
    end
```

---

## 3. Admin Configures Widget Layout

```mermaid
sequenceDiagram
    actor Admin
    participant CMS as CMS System

    Admin->>CMS: GET /api/v1/themes/active/zones
    CMS-->>Admin: 200 OK [{zone_name, current_widgets}, ...]

    Admin->>CMS: GET /api/v1/widgets
    CMS-->>Admin: 200 OK [{widget_type, name, config_schema}, ...]

    Admin->>CMS: POST /api/v1/layouts/zones/{zone_name}/widgets
    Note right of Admin: body: {widget_type, config, position}
    CMS-->>Admin: 201 Created {placement_id}

    Admin->>CMS: PATCH /api/v1/layouts/placements/{placement_id}
    Note right of Admin: body: {config updates}
    CMS-->>Admin: 200 OK

    Admin->>CMS: PUT /api/v1/layouts/zones/{zone_name}/order
    Note right of Admin: body: {placement_ids in order}
    CMS-->>Admin: 200 OK

    Admin->>CMS: DELETE /api/v1/layouts/placements/{placement_id}
    CMS-->>Admin: 204 No Content

    Admin->>CMS: POST /api/v1/layouts/save
    CMS-->>Admin: 200 OK {cache_invalidated: true}
```

---

## 4. Reader Subscribes to Newsletter

```mermaid
sequenceDiagram
    actor Reader
    participant CMS as CMS System
    participant Email as Email Provider

    Reader->>CMS: POST /api/v1/subscriptions (email)
    CMS-->>Reader: 202 Accepted {message: "check your inbox"}

    CMS->>Email: Send confirmation email with token
    Email-->>Reader: Confirmation email delivered

    Reader->>CMS: GET /api/v1/subscriptions/confirm?token={token}
    CMS-->>Reader: 200 OK {subscribed: true}

    CMS->>Email: Send welcome email
    Email-->>Reader: Welcome email delivered
```

---

## 5. Reader Searches and Reads a Post

```mermaid
sequenceDiagram
    actor Reader
    participant CMS as CMS System
    participant Search as Search Index

    Reader->>CMS: GET /api/v1/search?q=keyword&category=tech
    CMS->>Search: query(keyword, filters)
    Search-->>CMS: [{post_id, title, excerpt, score}, ...]
    CMS-->>Reader: 200 OK {results, total, page}

    Reader->>CMS: GET /api/v1/posts/{slug}
    CMS-->>Reader: 200 OK {post content, author, categories, tags, comments_enabled}

    Reader->>CMS: POST /api/v1/analytics/pageview
    Note right of Reader: body: {post_id, referrer, device}
    CMS-->>Reader: 204 No Content
```

---

## 6. Super Admin Creates a New Site

```mermaid
sequenceDiagram
    actor SuperAdmin
    participant CMS as CMS System
    participant Email as Email Provider

    SuperAdmin->>CMS: POST /api/v1/sites
    Note right of SuperAdmin: body: {name, domain, slug, owner_email, theme_id}
    CMS-->>SuperAdmin: 201 Created {site_id, status: provisioning}

    CMS->>CMS: Provision tenant database schema
    CMS->>CMS: Apply default theme and plugins
    CMS->>Email: Send owner invitation email
    Email-->>SuperAdmin: Invitation sent confirmation

    SuperAdmin->>CMS: GET /api/v1/sites/{site_id}
    CMS-->>SuperAdmin: 200 OK {site_id, status: active, domain}
```
