# Sequence Diagrams

## Overview
Internal sequence diagrams show the interactions between objects and services inside the CMS for key scenarios.

---

## 1. Author Submits Post for Review

```mermaid
sequenceDiagram
    participant API as Publishing Router
    participant PostSvc as Post Service
    participant RevisionSvc as Revision Service
    participant NotifySvc as Notification Service
    participant DB as PostgreSQL
    participant Queue as Redis Queue

    API->>PostSvc: submit_for_review(post_id, user)
    PostSvc->>DB: SELECT post WHERE id=post_id AND author_id=user.id
    DB-->>PostSvc: Post (status=draft)
    PostSvc->>PostSvc: validate state transition (draft → pending_review)
    PostSvc->>RevisionSvc: capture_revision(post)
    RevisionSvc->>DB: INSERT revision
    DB-->>RevisionSvc: revision_id
    PostSvc->>DB: UPDATE post SET status=pending_review
    PostSvc->>NotifySvc: notify_editors(post, event=submitted)
    NotifySvc->>DB: INSERT notification records for editors
    NotifySvc->>Queue: enqueue email job (editor notification)
    PostSvc-->>API: PostResponse(status=pending_review)
```

---

## 2. Editor Publishes a Post

```mermaid
sequenceDiagram
    participant API as Publishing Router
    participant PostSvc as Post Service
    participant FeedSvc as Feed Service
    participant SitemapSvc as Sitemap Service
    participant SearchSvc as Search Indexer
    participant NotifySvc as Notification Service
    participant DB as PostgreSQL
    participant Queue as Redis Queue
    participant CDN as CDN Invalidator

    API->>PostSvc: publish(post_id, editor)
    PostSvc->>DB: SELECT post WHERE id=post_id
    DB-->>PostSvc: Post (status=pending_review or scheduled)
    PostSvc->>PostSvc: validate editor permission
    PostSvc->>DB: UPDATE post SET status=published, published_at=now()
    PostSvc->>FeedSvc: regenerate_feed(site_id)
    FeedSvc->>DB: SELECT recent published posts
    FeedSvc->>FeedSvc: build RSS/Atom XML
    FeedSvc->>CDN: invalidate /feed.xml and /atom.xml
    PostSvc->>SitemapSvc: rebuild_sitemap(site_id)
    SitemapSvc->>DB: SELECT all published posts and pages
    SitemapSvc->>CDN: invalidate /sitemap.xml
    PostSvc->>SearchSvc: index_post(post)
    SearchSvc->>SearchSvc: upsert document in search index
    PostSvc->>NotifySvc: dispatch_publish_notifications(post)
    NotifySvc->>DB: SELECT confirmed subscribers
    NotifySvc->>Queue: enqueue newsletter digest jobs (batched)
    NotifySvc->>DB: INSERT notification for post author
    PostSvc-->>API: PostResponse(status=published, published_at)
```

---

## 3. Admin Places Widget in Zone

```mermaid
sequenceDiagram
    participant API as Layout Router
    participant ZoneSvc as Zone Placement Service
    participant WidgetReg as Widget Registry
    participant ThemeSvc as Theme Service
    participant CacheInv as Cache Invalidator
    participant DB as PostgreSQL
    participant CDN as CDN

    API->>ZoneSvc: place_widget(site_id, zone_name, widget_type, config, position)
    ZoneSvc->>ThemeSvc: get_active_theme(site_id)
    ThemeSvc->>DB: SELECT active theme
    DB-->>ThemeSvc: Theme {zones: [...]}
    ThemeSvc-->>ZoneSvc: Theme
    ZoneSvc->>ZoneSvc: validate zone_name exists in theme
    ZoneSvc->>WidgetReg: get_widget(widget_type)
    WidgetReg->>DB: SELECT widget WHERE type=widget_type
    DB-->>WidgetReg: Widget
    WidgetReg->>WidgetReg: validate_config(config, widget.config_schema)
    ZoneSvc->>DB: INSERT widget_placement (zone, widget_id, config, position)
    DB-->>ZoneSvc: placement_id
    ZoneSvc->>CacheInv: invalidate_zone_pages(site_id, zone_name)
    CacheInv->>CDN: purge affected page cache entries
    CDN-->>CacheInv: purge confirmed
    ZoneSvc-->>API: WidgetPlacementResponse(placement_id)
```

---

## 4. Comment Submitted and Moderated

```mermaid
sequenceDiagram
    participant API as Comment Router
    participant CommentSvc as Comment Service
    participant SpamSvc as Spam Filter Client
    participant NotifySvc as Notification Service
    participant DB as PostgreSQL
    participant Queue as Redis Queue

    API->>CommentSvc: submit_comment(post_id, author_info, body)
    CommentSvc->>DB: SELECT post WHERE id=post_id AND status=published
    DB-->>CommentSvc: Post
    CommentSvc->>SpamSvc: check_spam(body, author_info)
    SpamSvc-->>CommentSvc: SpamCheckResult {score, classification}
    CommentSvc->>DB: INSERT comment (status=pending, spam_score)

    alt High spam score
        CommentSvc->>DB: UPDATE comment SET status=spam
        CommentSvc-->>API: 202 Accepted (silent discard)
    else Low score + trusted reader
        CommentSvc->>DB: UPDATE comment SET status=approved
        CommentSvc->>NotifySvc: notify_author(post.author_id, comment)
        NotifySvc->>Queue: enqueue email notification
        CommentSvc-->>API: 201 Created (comment published)
    else Medium score
        CommentSvc->>NotifySvc: notify_moderators(site_id, comment)
        NotifySvc->>DB: INSERT moderator notification records
        NotifySvc->>Queue: enqueue email to moderators
        CommentSvc-->>API: 202 Accepted (pending moderation)
    end
```

---

## 5. Media Upload and Processing

```mermaid
sequenceDiagram
    participant API as Media Router
    participant MediaSvc as Media Service
    participant Processor as Image Processor
    participant Storage as Object Storage
    participant DB as PostgreSQL

    API->>MediaSvc: upload_media(site_id, uploader_id, file)
    MediaSvc->>MediaSvc: validate mime_type and file_size
    MediaSvc->>Storage: put_object(original, path=media/{site_id}/{uuid}/original)
    Storage-->>MediaSvc: original_url
    MediaSvc->>Processor: generate_sizes(original_url)
    Processor->>Processor: resize to thumbnail (150x150)
    Processor->>Storage: put_object(thumbnail)
    Storage-->>Processor: thumbnail_url
    Processor->>Processor: resize to medium (640x480)
    Processor->>Storage: put_object(medium)
    Storage-->>Processor: medium_url
    Processor->>Processor: resize to large (1280x960)
    Processor->>Storage: put_object(large)
    Storage-->>Processor: large_url
    Processor-->>MediaSvc: {thumbnail_url, medium_url, large_url}
    MediaSvc->>DB: INSERT media_items record
    DB-->>MediaSvc: media_id
    MediaSvc-->>API: MediaItemResponse(media_id, all variant URLs)
```

---

## 6. Scheduled Post Auto-Published by Worker

```mermaid
sequenceDiagram
    participant Scheduler as Job Scheduler
    participant Worker as Background Worker
    participant PostSvc as Post Service
    participant FeedSvc as Feed Service
    participant NotifySvc as Notification Service
    participant DB as PostgreSQL
    participant Queue as Redis Queue

    Scheduler->>Worker: trigger_scheduled_publish_check (every minute)
    Worker->>DB: SELECT posts WHERE status=scheduled AND scheduled_at <= now()
    DB-->>Worker: [Post, ...]

    loop For each due post
        Worker->>PostSvc: publish(post, actor=system)
        PostSvc->>DB: UPDATE post SET status=published, published_at=now()
        PostSvc->>FeedSvc: regenerate_feed(site_id)
        PostSvc->>NotifySvc: dispatch_publish_notifications(post)
        NotifySvc->>Queue: enqueue subscriber digest batch
        NotifySvc->>DB: INSERT author notification
    end
```
