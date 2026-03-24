# Class Diagrams

## Overview
Class diagrams model the detailed internal structure of the CMS domain objects, their attributes, methods, and relationships.

---

## Content Domain Classes

```mermaid
classDiagram
    class Post {
        +id: int
        +site_id: int
        +author_id: int
        +title: str
        +slug: str
        +content: str
        +excerpt: str
        +status: PostStatus
        +featured_image_id: int
        +scheduled_at: datetime
        +published_at: datetime
        +created_at: datetime
        +updated_at: datetime
        +submit_for_review() void
        +publish() void
        +schedule(dt: datetime) void
        +return_to_draft(feedback: str) void
        +archive() void
        +trash() void
        +generate_slug() str
        +latest_revision() Revision
    }

    class Page {
        +id: int
        +site_id: int
        +author_id: int
        +title: str
        +slug: str
        +content: str
        +status: PageStatus
        +template: str
        +in_navigation: bool
        +created_at: datetime
        +updated_at: datetime
        +publish() void
        +unpublish() void
    }

    class Revision {
        +id: int
        +content_type: str
        +content_id: int
        +title: str
        +content: str
        +actor_id: int
        +created_at: datetime
        +diff_from(other: Revision) RevisionDiff
        +restore() void
    }

    class MediaItem {
        +id: int
        +site_id: int
        +uploader_id: int
        +filename: str
        +mime_type: str
        +file_size: int
        +original_url: str
        +thumbnail_url: str
        +medium_url: str
        +large_url: str
        +alt_text: str
        +created_at: datetime
        +generate_sizes() void
        +cdn_url(size: str) str
    }

    class SEOMeta {
        +id: int
        +content_type: str
        +content_id: int
        +meta_title: str
        +meta_description: str
        +og_image_id: int
        +canonical_url: str
        +updated_at: datetime
        +effective_title(post: Post) str
        +effective_description(post: Post) str
    }

    Post "1" --> "many" Revision : captured_as
    Page "1" --> "many" Revision : captured_as
    Post "1" --> "1" SEOMeta : described_by
    Page "1" --> "1" SEOMeta : described_by
    Post "1" --> "1" MediaItem : featured
```

---

## Taxonomy Domain Classes

```mermaid
classDiagram
    class Category {
        +id: int
        +site_id: int
        +name: str
        +slug: str
        +description: str
        +parent_id: int
        +created_at: datetime
        +children() List~Category~
        +ancestors() List~Category~
        +post_count() int
    }

    class Tag {
        +id: int
        +site_id: int
        +name: str
        +slug: str
        +created_at: datetime
        +merge_into(target: Tag) void
        +post_count() int
    }

    class PostCategory {
        +post_id: int
        +category_id: int
    }

    class PostTag {
        +post_id: int
        +tag_id: int
    }

    Category "1" --> "many" PostCategory : classifies
    Tag "1" --> "many" PostTag : tags
```

---

## Layout & Widget Domain Classes

```mermaid
classDiagram
    class Theme {
        +id: int
        +site_id: int
        +name: str
        +version: str
        +zones: Dict~str, ZoneDefinition~
        +package_url: str
        +is_active: bool
        +installed_at: datetime
        +activate() void
        +deactivate() void
        +preview_url() str
        +defined_zones() List~str~
    }

    class Widget {
        +id: int
        +type: str
        +name: str
        +description: str
        +config_schema: dict
        +registered_by: str
        +render(config: dict, context: RenderContext) str
        +validate_config(config: dict) bool
    }

    class WidgetPlacement {
        +id: int
        +site_id: int
        +theme_id: int
        +zone_name: str
        +widget_id: int
        +position: int
        +config: dict
        +page_override_id: int
        +update_config(config: dict) void
        +move_to_zone(zone: str, position: int) void
        +remove() void
    }

    class NavigationMenu {
        +id: int
        +site_id: int
        +name: str
        +zone: str
        +created_at: datetime
        +items() List~NavigationItem~
        +add_item(item: NavigationItem) void
        +reorder(item_ids: List~int~) void
    }

    class NavigationItem {
        +id: int
        +menu_id: int
        +label: str
        +url: str
        +parent_id: int
        +position: int
        +children() List~NavigationItem~
    }

    Theme "1" --> "many" WidgetPlacement : hosts
    Widget "1" --> "many" WidgetPlacement : instantiated_as
    NavigationMenu "1" --> "many" NavigationItem : contains
```

---

## User & Auth Domain Classes

```mermaid
classDiagram
    class User {
        +id: int
        +email: str
        +display_name: str
        +bio: str
        +avatar_url: str
        +hashed_password: str
        +is_active: bool
        +twofa_enabled: bool
        +twofa_secret: str
        +created_at: datetime
        +set_password(raw: str) void
        +verify_password(raw: str) bool
        +enable_2fa() str
        +verify_2fa(token: str) bool
    }

    class SiteMembership {
        +user_id: int
        +site_id: int
        +role: Role
        +invited_at: datetime
        +joined_at: datetime
    }

    class Invitation {
        +id: int
        +email: str
        +site_id: int
        +role: Role
        +token: str
        +expires_at: datetime
        +accepted_at: datetime
        +is_valid() bool
        +accept(user: User) void
    }

    class Session {
        +id: str
        +user_id: int
        +site_id: int
        +refresh_token: str
        +expires_at: datetime
        +invalidate() void
    }

    User "1" --> "many" SiteMembership : has
    User "1" --> "many" Session : owns
    Invitation "many" --> "1" User : accepted_by
```

---

## Comment Domain Classes

```mermaid
classDiagram
    class Comment {
        +id: int
        +post_id: int
        +parent_id: int
        +author_user_id: int
        +author_name: str
        +author_email: str
        +body: str
        +status: CommentStatus
        +spam_score: float
        +created_at: datetime
        +approve() void
        +reject() void
        +mark_spam() void
        +children() List~Comment~
    }

    class SpamCheckResult {
        +comment_id: int
        +score: float
        +classification: str
        +checked_at: datetime
    }

    Comment "1" --> "1" SpamCheckResult : checked_by
    Comment "1" --> "many" Comment : replies
```
