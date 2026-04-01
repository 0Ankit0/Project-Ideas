# Database Schema — Entity Relationship Diagram

The Social Networking Platform database uses PostgreSQL as its primary relational store, responsible for all transactional data, the social graph, user-generated content, moderation records, and notification state. High-throughput time-series workloads — particularly direct messaging at scale and real-time activity feeds — are offloaded to Apache Cassandra, which provides wide-row storage optimised for append-heavy, partition-key-based access patterns. Full-text search is served by Elasticsearch, kept in sync with the PostgreSQL primary through change-data-capture driven by the write-ahead log. This document defines the canonical PostgreSQL schema, covering every entity, its attributes and data types, referential integrity constraints, and the relationships that govern data consistency across the platform.

## Entity Relationship Diagram

```mermaid
erDiagram
    %% ── User core ─────────────────────────────────────────────────────────
    USERS ||--|| USER_SETTINGS : "configures"
    USERS ||--o{ USER_INTERESTS : "has"
    USERS ||--o{ POSTS : "authors"
    USERS ||--o{ COMMENTS : "writes"
    USERS ||--o{ LIKES : "gives"
    USERS ||--o{ GROUPS : "owns"
    USERS ||--o{ GROUP_MEMBERS : "joins"
    USERS ||--o{ MESSAGES : "sends"
    USERS ||--o{ CONVERSATION_PARTICIPANTS : "participates in"
    USERS ||--o{ NOTIFICATIONS : "receives"
    USERS ||--o{ NOTIFICATIONS : "triggers"
    USERS ||--o{ REPORTS : "files"
    USERS |o--o{ REPORTS : "reviews"
    USERS ||--o{ MODERATION_ACTIONS : "performs"

    %% ── Social graph ───────────────────────────────────────────────────────
    USERS ||--o{ FOLLOWS : "follows"
    USERS ||--o{ FOLLOWS : "is followed by"
    USERS ||--o{ USER_BLOCKS : "blocks"
    USERS ||--o{ USER_BLOCKS : "is blocked by"

    %% ── Post content ───────────────────────────────────────────────────────
    POSTS ||--o{ POST_HASHTAGS : "tagged with"
    POSTS ||--o{ COMMENTS : "receives"
    POSTS ||--o{ LIKES : "receives"
    POSTS ||--o{ GROUP_POSTS : "included in"
    POSTS |o--o{ POSTS : "repost of"

    %% ── Comment hierarchy ──────────────────────────────────────────────────
    COMMENTS |o--o{ COMMENTS : "replies to"

    %% ── Groups ─────────────────────────────────────────────────────────────
    GROUPS ||--o{ GROUP_MEMBERS : "has"
    GROUPS ||--o{ GROUP_POSTS : "contains"

    %% ── Messaging ──────────────────────────────────────────────────────────
    CONVERSATIONS ||--o{ MESSAGES : "contains"
    CONVERSATIONS ||--o{ CONVERSATION_PARTICIPANTS : "includes"
    CONVERSATIONS |o--o| MESSAGES : "last message"

    %% ── Moderation ─────────────────────────────────────────────────────────
    REPORTS ||--o{ MODERATION_ACTIONS : "triggers"

    %% ── Entity definitions ─────────────────────────────────────────────────

    USERS {
        uuid id PK
        string username UK
        string email UK
        string display_name
        text bio
        string avatar_url
        string status
        string role
        timestamp created_at
        timestamp last_active_at
    }

    USER_SETTINGS {
        uuid user_id PK FK
        string privacy_level
        jsonb notification_prefs
        string content_language
        bool show_online_status
        bool allow_dm_from_strangers
    }

    POSTS {
        uuid id PK
        uuid author_id FK
        text content
        jsonb media_urls
        string post_type
        string visibility
        string status
        int like_count
        int comment_count
        int share_count
        uuid original_post_id FK
        timestamp created_at
        timestamp updated_at
    }

    POST_HASHTAGS {
        uuid post_id PK FK
        string hashtag PK
    }

    COMMENTS {
        uuid id PK
        uuid post_id FK
        uuid author_id FK
        uuid parent_comment_id FK
        text content
        string status
        int like_count
        timestamp created_at
    }

    LIKES {
        uuid user_id PK FK
        uuid post_id PK FK
        string reaction_type
        timestamp created_at
    }

    FOLLOWS {
        uuid follower_id PK FK
        uuid following_id PK FK
        string status
        timestamp created_at
        timestamp accepted_at
    }

    GROUPS {
        uuid id PK
        string name
        text description
        uuid owner_id FK
        string privacy
        int member_count
        string status
        timestamp created_at
    }

    GROUP_MEMBERS {
        uuid group_id PK FK
        uuid user_id PK FK
        string role
        timestamp joined_at
    }

    GROUP_POSTS {
        uuid group_id PK FK
        uuid post_id PK FK
        timestamp added_at
    }

    CONVERSATIONS {
        uuid id PK
        string type
        uuid last_message_id FK
        timestamp created_at
        timestamp updated_at
    }

    CONVERSATION_PARTICIPANTS {
        uuid conversation_id PK FK
        uuid user_id PK FK
        timestamp joined_at
        timestamp last_read_at
        bool is_muted
    }

    MESSAGES {
        uuid id PK
        uuid conversation_id FK
        uuid sender_id FK
        text content
        string media_url
        string message_type
        string status
        bool is_deleted
        timestamp created_at
    }

    NOTIFICATIONS {
        uuid id PK
        uuid recipient_id FK
        uuid actor_id FK
        string type
        string resource_type
        uuid resource_id
        bool is_read
        jsonb metadata
        timestamp created_at
    }

    REPORTS {
        uuid id PK
        uuid reporter_id FK
        string resource_type
        uuid resource_id
        string reason
        text description
        string status
        uuid reviewer_id FK
        timestamp created_at
        timestamp resolved_at
    }

    MODERATION_ACTIONS {
        uuid id PK
        uuid report_id FK
        string action_type
        uuid moderator_id FK
        text reason
        jsonb metadata
        timestamp created_at
    }

    USER_BLOCKS {
        uuid blocker_id PK FK
        uuid blocked_id PK FK
        timestamp created_at
    }

    HASHTAG_TRENDS {
        uuid id PK
        string hashtag UK
        int post_count
        int hour_count
        timestamp window_start
        timestamp computed_at
    }

    USER_INTERESTS {
        uuid user_id PK FK
        string topic PK
        float score
        timestamp updated_at
    }
```

## Table Descriptions

### Users and Profiles

The `USERS` table is the root entity of the entire schema. Its primary key is a UUID generated at the application layer (using UUIDv7 for time-ordered indexing), ensuring global uniqueness without exposing sequential identifiers. Both `username` and `email` carry unique constraints backed by B-tree indexes, supporting O(1) lookup during authentication and mention resolution. The `status` field implements a soft-delete pattern with enumerated values `active`, `suspended`, `deactivated`, and `deleted`; hard deletes are never issued, preserving referential integrity for moderation audit trails and shared content history. The `role` field distinguishes `user`, `moderator`, and `admin` tiers, driving access control checks in the API layer. `last_active_at` is updated on each authenticated request and drives online-presence indicators without requiring a separate presence service for non-realtime contexts.

`USER_SETTINGS` maintains a strict one-to-one relationship with `USERS` via a shared primary/foreign key (`user_id`), guaranteeing that every user record has exactly one settings row created transactionally at registration. The `privacy_level` enum (`public`, `friends_only`, `private`) governs who can view the user's profile and post feed. Notification delivery channels and per-event toggles are stored as a `jsonb` document in `notification_prefs`, enabling flexible schema evolution without DDL migrations for each new notification type. The `allow_dm_from_strangers` boolean gates the messaging flow for users outside the follower graph.

`USER_INTERESTS` forms a composite primary key on `(user_id, topic)` and stores a normalised affinity `score` in the range 0.0–1.0, computed by the recommendation engine from engagement signals. This table feeds the Smart Recommendation Engine's collaborative-filtering pipeline and is refreshed incrementally via a background worker rather than synchronous writes.

### Posts and Content

`POSTS` is the central content entity. The `author_id` foreign key references `USERS`, and the nullable `original_post_id` is a self-referential FK that links a repost or quote-post back to the originating record, enabling unbounded share chains while preserving attribution. The `post_type` enum distinguishes `original`, `repost`, `quote`, and `story` variants, while `visibility` controls audience with values `public`, `friends`, `private`, and `group`. The `status` field (`active`, `removed`, `archived`) supports soft content removal without cascading deletes.

The `like_count`, `comment_count`, and `share_count` integer columns are intentional denormalisation. Maintaining accurate real-time counts via `COUNT(*)` queries against `LIKES` and `COMMENTS` at every feed render is prohibitively expensive at scale; these counters are instead incremented and decremented atomically using `UPDATE … SET like_count = like_count + 1` inside the same transaction that inserts or deletes the corresponding child row. Periodic reconciliation jobs correct any drift caused by partial failures.

`POST_HASHTAGS` uses a composite primary key on `(post_id, hashtag)`, avoiding a surrogate key. The `hashtag` column is stored in normalised lowercase form. A GIN index on the `hashtag` column enables efficient tag-based feed queries without a separate tag registry table.

`COMMENTS` supports arbitrary-depth threading through the nullable `parent_comment_id` self-referential FK. Depth is not stored; the API layer enforces a maximum nesting limit of three levels by walking the parent chain at write time. `LIKES` uses a composite PK on `(user_id, post_id)`, preventing duplicate reactions and making existence checks a primary-key lookup. The `reaction_type` enum (`like`, `love`, `haha`, `wow`, `sad`, `angry`) extends the simple binary like into an emoji-reaction model compatible with Facebook's reaction vocabulary.

### Social Graph

`FOLLOWS` models the directed follower graph with a composite primary key on `(follower_id, following_id)`. The `status` enum supports `pending` (for private accounts that require approval), `active`, and `blocked` states. The `accepted_at` timestamp is populated when a pending follow request is approved, enabling latency analysis of follow-request workflows. Mutual follow detection is resolved in a single self-join:

```sql
SELECT a.follower_id, a.following_id
FROM follows a
JOIN follows b
  ON a.follower_id = b.following_id
 AND a.following_id = b.follower_id
WHERE a.status = 'active'
  AND b.status = 'active'
  AND a.follower_id = :user_id;
```

`USER_BLOCKS` maintains a composite primary key on `(blocker_id, blocked_id)`. When a block is created, the application layer also removes any active follow relationships in both directions within the same transaction, and inserts a `blocked` status record into `FOLLOWS` to prevent re-follows. Block records are excluded from all feed, search, and notification queries via a `NOT EXISTS` lateral filter on the `USER_BLOCKS` table.

### Groups

`GROUPS` captures community spaces with a `privacy` enum of `public` (discoverable, joinable by anyone), `private` (discoverable, join-by-request), and `secret` (non-discoverable, invite-only). The `owner_id` FK establishes the creating user as the initial owner. The `member_count` integer column is denormalised for the same reasons as post counters — group membership lists can reach tens of thousands of rows, making `COUNT(*)` scans impractical at feed-render latency.

`GROUP_MEMBERS` uses a composite primary key on `(group_id, user_id)` and assigns each member a `role` of `owner`, `admin`, `moderator`, or `member`. Role-based permission checks in the API layer read this field directly, avoiding a separate RBAC table for group-scoped permissions. `GROUP_POSTS` bridges `GROUPS` and `POSTS` with a composite PK on `(group_id, post_id)`, recording when a post was added to the group feed. A post may belong to at most one group; this constraint is enforced at the application layer.

### Messaging

`CONVERSATIONS` represents both one-to-one direct messages (`type = 'direct'`) and multi-party group chats (`type = 'group'`). The nullable `last_message_id` FK enables O(1) conversation-list rendering without a subquery to find the most recent message. This introduces a circular reference — `CONVERSATIONS.last_message_id → MESSAGES.conversation_id` — which is resolved by inserting the message first, then updating the conversation in the same transaction using a deferred foreign key constraint.

`CONVERSATION_PARTICIPANTS` uses a composite PK on `(conversation_id, user_id)`. The `last_read_at` timestamp drives unread message count computation: `SELECT COUNT(*) FROM messages WHERE conversation_id = :cid AND created_at > :last_read_at AND is_deleted = false`. The `is_muted` boolean suppresses push notifications for the participant without removing them from the conversation.

`MESSAGES` stores the content of each message, with `is_deleted` implementing a soft-delete that replaces the rendered content with a tombstone label rather than removing the row. The `message_type` enum (`text`, `image`, `video`, `audio`, `file`, `system`) determines client-side rendering. For deployments exceeding 10,000 messages per second, the `messages` table is migrated entirely to Cassandra, partitioned by `(conversation_id, time_bucket)`, while PostgreSQL retains only the `conversations` and `conversation_participants` metadata tables.

### Notifications and Moderation

`NOTIFICATIONS` records in-app alerts for events such as follows, likes, comments, mentions, and group invites. The `type` field is a string enum with values including `follow`, `like`, `comment`, `mention`, `group_invite`, `follow_request`, and `system_alert`. The polymorphic `(resource_type, resource_id)` pair identifies the entity the notification pertains to (e.g., `resource_type = 'post'`, `resource_id = <uuid>`). The `metadata` jsonb column carries additional context for rendering (e.g., a truncated post excerpt) without requiring a join. Notifications older than 90 days are pruned by a scheduled job.

`REPORTS` tracks user-submitted abuse reports against any content type. The `resource_type` and `resource_id` columns implement a polymorphic reference to the reported entity (post, comment, user, group). The `status` field follows the workflow `pending → under_review → resolved | dismissed`. The nullable `reviewer_id` FK is populated when a moderator claims the report. `MODERATION_ACTIONS` records the outcome of each reviewed report; the `action_type` enum includes `remove_content`, `warn_user`, `suspend_user`, `ban_user`, and `shadowban_user`. The `metadata` jsonb field stores action-specific context such as suspension duration or appeal eligibility.

`HASHTAG_TRENDS` is a pre-computed materialised table populated by a scheduled aggregation job that runs every 15 minutes. It does not carry foreign keys to other tables; it is a denormalised projection consumed directly by the Trending Topics API endpoint. The `window_start` timestamp anchors the trend computation window, and `hour_count` tracks the rate of growth within the most recent hour for velocity-based ranking.

## Indexes and Performance

The following indexes are created in addition to those implied by primary key and unique constraints:

```sql
-- Chronological post feed per author (most common query pattern)
CREATE INDEX idx_posts_author_created
    ON posts (author_id, created_at DESC)
    WHERE status = 'active';

-- Follower lookups (reverse graph traversal for fan-out reads)
CREATE INDEX idx_follows_following_id
    ON follows (following_id)
    WHERE status = 'active';

-- Notification inbox rendering
CREATE INDEX idx_notifications_recipient_unread
    ON notifications (recipient_id, created_at DESC)
    WHERE is_read = false;

-- Full notification history
CREATE INDEX idx_notifications_recipient_all
    ON notifications (recipient_id, created_at DESC);

-- Message history within a conversation
CREATE INDEX idx_messages_conversation_created
    ON messages (conversation_id, created_at DESC)
    WHERE is_deleted = false;

-- Full-text search on post content (GIN index on tsvector)
CREATE INDEX idx_posts_content_fts
    ON posts USING GIN (to_tsvector('english', content))
    WHERE status = 'active';

-- Hashtag-based feed queries
CREATE INDEX idx_post_hashtags_hashtag
    ON post_hashtags (hashtag, post_id);

-- Group member role lookups
CREATE INDEX idx_group_members_user
    ON group_members (user_id, group_id);

-- Report queue for moderator dashboards
CREATE INDEX idx_reports_status_created
    ON reports (status, created_at ASC)
    WHERE status IN ('pending', 'under_review');

-- Block graph — inverted lookup (was I blocked by this user?)
CREATE INDEX idx_user_blocks_blocked_id
    ON user_blocks (blocked_id);
```

Partial indexes filtering on `status = 'active'` or `is_deleted = false` dramatically reduce index size and improve cache efficiency for the hot read path, which exclusively queries non-deleted, active records. All foreign key columns that are not part of a composite primary key receive individual B-tree indexes to prevent sequential scans on cascade operations.

## Data Partitioning Strategy

### Posts Table — Range Partitioning

The `posts` table is range-partitioned by `created_at` using PostgreSQL declarative partitioning with monthly boundaries:

```sql
CREATE TABLE posts (...)
    PARTITION BY RANGE (created_at);

CREATE TABLE posts_2024_01
    PARTITION OF posts
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

Partitioning constrains query planning to scan only the relevant monthly child tables when a `created_at` range predicate is present, which is the case for all feed and archive queries. Partitions older than 12 months are candidates for archival to cold object storage; the parent table continues to serve recent data from hot NVMe storage.

### Messages — Cassandra Partitioning

When message volume warrants migration to Cassandra, the partition key is `(conversation_id, time_bucket)` where `time_bucket` is a truncated timestamp at one-hour granularity. This prevents unbounded partition growth for long-running conversations while keeping all messages for a given conversation-hour co-located on the same Cassandra node for efficient sequential reads. The clustering column is `created_at DESC`, matching the default rendering order.

### Notifications — TTL Pruning

Notification rows are automatically pruned after 90 days via a scheduled `DELETE` job executed during off-peak hours:

```sql
DELETE FROM notifications
WHERE created_at < NOW() - INTERVAL '90 days';
```

In high-scale deployments, this can alternatively be implemented as a Cassandra TTL on notification records migrated out of PostgreSQL, avoiding lock contention on large DELETE operations against the primary store.
