# Domain Model

## Overview
The domain model shows the key business entities in the CMS, their attributes, and the relationships between them.

---

## Core Domain Model

```mermaid
classDiagram
    class Site {
        +id: int
        +name: string
        +slug: string
        +domain: string
        +timezone: string
        +active_theme_id: int
        +is_active: bool
    }

    class User {
        +id: int
        +email: string
        +display_name: string
        +bio: text
        +avatar_url: string
        +role: Role
        +is_active: bool
        +twofa_enabled: bool
    }

    class Post {
        +id: int
        +title: string
        +slug: string
        +content: text
        +excerpt: text
        +status: PostStatus
        +featured_image_id: int
        +scheduled_at: datetime
        +published_at: datetime
        +author_id: int
        +site_id: int
    }

    class Page {
        +id: int
        +title: string
        +slug: string
        +content: text
        +status: PageStatus
        +template: string
        +in_navigation: bool
        +site_id: int
    }

    class Revision {
        +id: int
        +content_type: string
        +content_id: int
        +title: string
        +content: text
        +actor_id: int
        +created_at: datetime
    }

    class Category {
        +id: int
        +name: string
        +slug: string
        +parent_id: int
        +description: text
        +site_id: int
    }

    class Tag {
        +id: int
        +name: string
        +slug: string
        +site_id: int
    }

    class MediaItem {
        +id: int
        +filename: string
        +mime_type: string
        +file_size: int
        +original_url: string
        +thumbnail_url: string
        +medium_url: string
        +large_url: string
        +alt_text: string
        +uploader_id: int
        +site_id: int
    }

    class Comment {
        +id: int
        +post_id: int
        +parent_id: int
        +author_user_id: int
        +author_name: string
        +author_email: string
        +body: text
        +status: CommentStatus
        +spam_score: float
    }

    class Widget {
        +id: int
        +type: string
        +name: string
        +description: string
        +config_schema: json
        +registered_by: string
    }

    class WidgetPlacement {
        +id: int
        +site_id: int
        +theme_id: int
        +zone_name: string
        +widget_id: int
        +position: int
        +config: json
        +page_override_id: int
    }

    class Theme {
        +id: int
        +name: string
        +version: string
        +zones: json
        +package_url: string
        +is_active: bool
        +site_id: int
    }

    class NavigationMenu {
        +id: int
        +name: string
        +zone: string
        +site_id: int
    }

    class NavigationItem {
        +id: int
        +menu_id: int
        +label: string
        +url: string
        +parent_id: int
        +position: int
    }

    class SEOMeta {
        +id: int
        +content_type: string
        +content_id: int
        +meta_title: string
        +meta_description: text
        +og_image_id: int
        +canonical_url: string
    }

    class Subscription {
        +id: int
        +email: string
        +site_id: int
        +is_confirmed: bool
        +frequency: string
        +created_at: datetime
    }

    class Plugin {
        +id: int
        +name: string
        +version: string
        +is_active: bool
        +site_id: int
        +config: json
    }

    Site "1" --> "many" User : has members
    Site "1" --> "many" Post : contains
    Site "1" --> "many" Page : contains
    Site "1" --> "many" Category : owns
    Site "1" --> "many" Tag : owns
    Site "1" --> "many" Theme : installs
    Site "1" --> "many" NavigationMenu : defines
    Site "1" --> "many" Subscription : gathers
    Site "1" --> "many" Plugin : installs

    User "1" --> "many" Post : authors
    User "1" --> "many" Comment : writes

    Post "1" --> "many" Revision : has
    Post "many" --> "many" Category : classified_by
    Post "many" --> "many" Tag : tagged_with
    Post "1" --> "many" Comment : receives
    Post "1" --> "1" SEOMeta : has

    Page "1" --> "many" Revision : has
    Page "1" --> "1" SEOMeta : has

    Theme "1" --> "many" WidgetPlacement : defines
    Widget "1" --> "many" WidgetPlacement : placed_as

    NavigationMenu "1" --> "many" NavigationItem : contains
```

---

## Domain Enumerations

### PostStatus
```
Draft → PendingReview → Scheduled → Published → Archived → Trashed
```

### CommentStatus
```
Pending → Approved
Pending → Rejected
Pending → Spam
```

### Role
```
Reader < Author < Editor < Administrator < SuperAdmin
```
