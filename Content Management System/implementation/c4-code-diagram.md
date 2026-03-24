# C4 Code Diagram

## Overview
C4 Level 4 code diagrams illustrate the internal class-level structure of the most complex CMS subsystems.

---

## Publishing Workflow — Code Level

```mermaid
classDiagram
    class PublishingRouter {
        +submit(post_id: int, user: User) PostResponse
        +publish(post_id: int, user: User) PostResponse
        +schedule(post_id: int, dt: datetime, user: User) PostResponse
        +return_to_draft(post_id: int, feedback: str, user: User) PostResponse
    }

    class WorkflowEngine {
        -post_repo: PostRepository
        -event_log: WorkflowEventLog
        -notifier: PublishEventNotifier
        +transition(post: Post, to: PostStatus, actor: User, ctx: dict) Post
        -validate_transition(from: PostStatus, to: PostStatus, role: Role) void
        -record_event(post_id: int, event: WorkflowEvent) void
    }

    class PostRepository {
        +get(post_id: int, site_id: int) Post
        +save(post: Post) Post
        +list(site_id: int, status: PostStatus, page: int) List~Post~
        +list_due_scheduled(now: datetime) List~Post~
    }

    class WorkflowEventLog {
        +record(post_id: int, from_status: PostStatus, to_status: PostStatus, actor_id: int) void
        +get_history(post_id: int) List~WorkflowEvent~
    }

    class PublishEventNotifier {
        -notification_store: NotificationStore
        -email_queue: EmailQueue
        +notify_editors(post: Post) void
        +notify_author_published(post: Post) void
        +notify_author_returned(post: Post, feedback: str) void
        +dispatch_subscriber_digest(post: Post) void
    }

    class FeedGenerator {
        -post_repo: PostRepository
        -cdn_invalidator: CDNInvalidator
        +regenerate(site_id: int) void
        -build_rss_xml(posts: List~Post~) str
        -build_atom_xml(posts: List~Post~) str
    }

    class SitemapBuilder {
        -post_repo: PostRepository
        -page_repo: PageRepository
        -cdn_invalidator: CDNInvalidator
        +rebuild(site_id: int) void
        -render_sitemap_xml(urls: List~SitemapEntry~) str
    }

    class ScheduleService {
        -queue: RedisQueue
        +enqueue_publish_job(post: Post) void
        +cancel_publish_job(post: Post) void
    }

    PublishingRouter --> WorkflowEngine : calls
    WorkflowEngine --> PostRepository : reads/writes
    WorkflowEngine --> WorkflowEventLog : records
    WorkflowEngine --> PublishEventNotifier : notifies
    WorkflowEngine --> FeedGenerator : triggers
    WorkflowEngine --> SitemapBuilder : triggers
    WorkflowEngine --> ScheduleService : schedules
```

---

## Widget Layout — Code Level

```mermaid
classDiagram
    class WidgetRouter {
        +place(zone: str, widget_type: str, config: dict, position: int) PlacementResponse
        +update_config(placement_id: int, config: dict) PlacementResponse
        +remove(placement_id: int) void
        +reorder(zone: str, placement_ids: List~int~) void
        +save_layout() void
    }

    class ZonePlacementService {
        -placement_repo: PlacementRepository
        -widget_registry: WidgetRegistry
        -theme_service: ThemeService
        -cache_invalidator: CacheInvalidator
        +place_widget(site_id: int, zone: str, widget_type: str, config: dict, pos: int) Placement
        +update_config(placement_id: int, config: dict) Placement
        +remove(placement_id: int) void
        +reorder(zone: str, ids: List~int~) void
        +save_and_invalidate(site_id: int) void
    }

    class WidgetRegistry {
        -widgets: Dict~str, Type~BaseWidget~~
        +register(type: str) Decorator
        +get(type: str) BaseWidget
        +list_all() List~WidgetMeta~
        +validate_config(type: str, config: dict) bool
    }

    class BaseWidget {
        <<abstract>>
        +type: str
        +name: str
        +config_schema: Type~BaseModel~
        +render(config: dict, context: RenderContext) str*
        +validate_config(config: dict) bool
    }

    class RecentPostsWidget {
        +type: str = "recent_posts"
        +render(config: RecentPostsConfig, context: RenderContext) str
    }

    class TagCloudWidget {
        +type: str = "tag_cloud"
        +render(config: TagCloudConfig, context: RenderContext) str
    }

    class SearchBoxWidget {
        +type: str = "search_box"
        +render(config: SearchBoxConfig, context: RenderContext) str
    }

    class CustomHTMLWidget {
        +type: str = "custom_html"
        +render(config: CustomHTMLConfig, context: RenderContext) str
    }

    class LayoutRenderer {
        -zone_svc: ZonePlacementService
        -widget_registry: WidgetRegistry
        -cache: RedisCache
        +render_zone(site_id: int, zone_name: str, context: RenderContext) str
        -cache_key(site_id: int, zone: str, theme_id: int) str
    }

    class CacheInvalidator {
        -cdn: CDNClient
        -cache: RedisCache
        +invalidate_zone(site_id: int, zone_name: str) void
        +invalidate_site(site_id: int) void
    }

    WidgetRouter --> ZonePlacementService : calls
    ZonePlacementService --> WidgetRegistry : validates
    ZonePlacementService --> CacheInvalidator : triggers
    WidgetRegistry --> BaseWidget : manages
    BaseWidget <|-- RecentPostsWidget
    BaseWidget <|-- TagCloudWidget
    BaseWidget <|-- SearchBoxWidget
    BaseWidget <|-- CustomHTMLWidget
    LayoutRenderer --> ZonePlacementService : resolves
    LayoutRenderer --> WidgetRegistry : renders
```

---

## Comment Moderation — Code Level

```mermaid
classDiagram
    class CommentRouter {
        +submit(post_id: int, body: CommentCreate) CommentResponse
        +list_approved(post_id: int, page: int) List~CommentResponse~
        +approve(comment_id: int, moderator: User) CommentResponse
        +reject(comment_id: int, moderator: User) void
        +mark_spam(comment_id: int, moderator: User) void
    }

    class CommentService {
        -comment_repo: CommentRepository
        -spam_client: SpamFilterClient
        -moderation_svc: ModerationService
        -notifier: CommentNotifier
        +submit(post: Post, author_info: AuthorInfo, body: str) Comment
        -classify(comment: Comment, score: float) CommentStatus
    }

    class SpamFilterClient {
        -api_url: str
        -api_key: str
        +check(body: str, author: AuthorInfo, ip: str) SpamCheckResult
    }

    class ModerationService {
        -comment_repo: CommentRepository
        +approve(comment: Comment, moderator: User) Comment
        +reject(comment: Comment, moderator: User) void
        +mark_spam(comment: Comment, moderator: User) void
        +list_pending(site_id: int, page: int) List~Comment~
        +bulk_approve(ids: List~int~, moderator: User) void
    }

    class CommentNotifier {
        -notification_store: NotificationStore
        -email_queue: EmailQueue
        +notify_post_author(comment: Comment) void
        +notify_parent_commenter(reply: Comment) void
        +notify_moderators(comment: Comment) void
    }

    CommentRouter --> CommentService : calls
    CommentService --> SpamFilterClient : checks
    CommentService --> ModerationService : delegates
    CommentService --> CommentNotifier : notifies
    CommentRouter --> ModerationService : moderate actions
```
