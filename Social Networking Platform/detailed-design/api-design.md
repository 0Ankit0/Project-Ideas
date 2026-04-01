# API Design

All REST endpoints are versioned under the `/api/v1/` prefix, providing a stable contract that permits future breaking changes to be introduced under `/api/v2/` without disrupting existing clients. Authentication is enforced via JWT Bearer tokens in the `Authorization` header; access tokens have a 15-minute TTL and refresh tokens a 30-day TTL, with refresh tokens rotated on every use. All request and response bodies use `Content-Type: application/json`. Pagination follows a cursor-based pattern: each list response includes an opaque `next_cursor` string; clients supply `cursor` and `limit` on subsequent requests. An absent or `null` `next_cursor` indicates the end of the result set.

**Standard error envelope:**

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resource was not found.",
    "details": {},
    "request_id": "req_abc123"
  }
}
```

`code` is a machine-readable constant; `details` carries field-level validation errors; `request_id` correlates with server-side logs.

---

## Authentication APIs

### POST /api/v1/auth/register
Registers a new account and sends an email verification link.
**Auth:** No | **Rate limit:** 10 / hour / IP | **Errors:** `409 EMAIL_EXISTS`, `409 USERNAME_TAKEN`, `422 VALIDATION_ERROR`

```json
// Request
{ "username": "jane_doe", "email": "jane@example.com", "password": "S3cur3P@ss!", "display_name": "Jane Doe" }

// Response 201
{
  "user": { "id": "usr_01HXZ", "username": "jane_doe", "email": "jane@example.com", "created_at": "2024-06-01T12:00:00Z" },
  "access_token": "eyJhbGci...",
  "refresh_token": "dGhpcyBp..."
}
```

### POST /api/v1/auth/login
Authenticates with email and password, returning a fresh token pair.
**Auth:** No | **Rate limit:** 20 / hour / IP | **Errors:** `401 INVALID_CREDENTIALS`, `429 TOO_MANY_ATTEMPTS`

```json
// Request  { "email": "jane@example.com", "password": "S3cur3P@ss!" }
// Response 200
{ "user": { "id": "usr_01HXZ", "username": "jane_doe", "display_name": "Jane Doe" }, "access_token": "eyJhbGci...", "refresh_token": "dGhpcyBp..." }
```

### POST /api/v1/auth/refresh
Exchanges a refresh token for a rotated token pair. The submitted token is immediately invalidated.
**Auth:** No | **Body:** `{ "refresh_token": "..." }` | **Response:** `{ "access_token": "...", "refresh_token": "..." }` | **Errors:** `401 TOKEN_EXPIRED`

### POST /api/v1/auth/oauth/{provider}
Completes an OAuth 2.0 authorization-code exchange. Supported providers: `google`, `apple`, `facebook`.
**Auth:** No | **Body:** `{ authorization_code, redirect_uri }` | **Response:** `{ user, access_token, refresh_token, is_new_user }`

### DELETE /api/v1/auth/logout
Invalidates the current refresh token server-side, ending the session.
**Auth:** Yes (`Authorization: Bearer <token>`) | **Response:** `204 No Content`

---

## User APIs

### GET /api/v1/users/{id}
Returns a public profile. Authenticated callers also receive relationship fields (`is_following`, `is_blocked`).
**Auth:** Optional

```json
// Response 200
{
  "id": "usr_01HXZ", "username": "jane_doe", "display_name": "Jane Doe",
  "bio": "Engineer & open-source contributor.", "avatar_url": "https://cdn.example.com/avatars/jane.jpg",
  "website": "https://janedoe.dev", "follower_count": 1420, "following_count": 312,
  "post_count": 87, "is_private": false, "is_following": true, "is_blocked": false,
  "created_at": "2024-01-15T08:30:00Z"
}
```

### PUT /api/v1/users/{id}
Updates the caller's own profile. Returns `403 FORBIDDEN` for another user's record.
**Auth:** Yes (own account) | **Body:** `{ display_name, bio, avatar_url, website }` | **Response 200:** Updated user object.

### GET /api/v1/users/{id}/followers
Paginated follower list. **Auth:** Optional
**Response:** `{ "users": [...], "next_cursor": "...", "total_count": 1420 }`

### GET /api/v1/users/{id}/following
Paginated following list. Response mirrors `/followers`. **Auth:** Optional

### POST /api/v1/users/{id}/follow
Follows the target. Returns `"requested"` for private accounts pending approval.
**Auth:** Yes | **Response:** `{ "status": "following" | "requested" }`

### DELETE /api/v1/users/{id}/follow
Unfollows the target or cancels a pending request. **Auth:** Yes | **Response:** `204 No Content`

### POST /api/v1/users/{id}/block
Blocks the target, preventing profile visibility and messaging.
**Auth:** Yes | **Response:** `{ "status": "blocked" }`

### DELETE /api/v1/users/{id}/block
Removes an existing block. **Auth:** Yes | **Response:** `204 No Content`

### GET /api/v1/users/search?q=&limit=&cursor=
Full-text search across usernames and display names.
**Auth:** Optional | **Response:** `{ "users": [{ ...user, "relevance_score": 0.97 }], "next_cursor": "...", "total_count": 4 }`

---

## Post APIs

### POST /api/v1/posts
Creates a new post. `post_type` controls rendering: `text`, `photo`, `video`, or `repost`. Supply `original_post_id` when reposting.
**Auth:** Yes

```json
// Request
{
  "content": "Just shipped a new feature! #buildinpublic",
  "media_urls": ["https://cdn.example.com/media/img1.jpg"],
  "post_type": "photo", "visibility": "public",
  "hashtags": ["buildinpublic"], "original_post_id": null
}
// Response 201
{
  "id": "pst_09QWE", "author": { "id": "usr_01HXZ", "username": "jane_doe" },
  "content": "Just shipped a new feature! #buildinpublic",
  "media_urls": ["https://cdn.example.com/media/img1.jpg"],
  "like_count": 0, "comment_count": 0, "share_count": 0,
  "visibility": "public", "created_at": "2024-06-01T14:22:00Z"
}
```

### GET /api/v1/posts/{id}
Returns a single post with engagement counts. Visibility rules are server-enforced.
**Auth:** Optional | **Errors:** `403 FOLLOWERS_ONLY`, `404 NOT_FOUND`

### PUT /api/v1/posts/{id}
Edits content or visibility of the caller's own post.
**Auth:** Yes (own post) | **Body:** `{ content, visibility }` | **Response 200:** Updated post object.

### DELETE /api/v1/posts/{id}
Soft-deletes a post. Caller must own the post or hold the `moderator` role.
**Auth:** Yes | **Response:** `204 No Content`

### POST /api/v1/posts/{id}/like
Adds or updates a reaction. Valid `reaction_type` values: `like`, `love`, `haha`, `sad`, `angry`.
**Auth:** Yes | **Body:** `{ "reaction_type": "love" }` | **Response:** `{ "reaction_type": "love", "total_likes": 215 }`

### DELETE /api/v1/posts/{id}/like
Removes the caller's reaction. **Auth:** Yes | **Response:** `204 No Content`

### GET /api/v1/posts/{id}/comments?cursor=&limit=
Paginated threaded comment list. Top-level comments carry a `replies` array (one level deep).
**Auth:** Optional

```json
// Response 200
{
  "comments": [{
    "id": "cmt_01AAA", "author": { "id": "usr_03LRP", "username": "bob" },
    "content": "Congrats!", "like_count": 3, "reply_count": 1,
    "created_at": "2024-06-01T14:45:00Z",
    "replies": [{ "id": "cmt_01BBB", "author": { "id": "usr_01HXZ", "username": "jane_doe" },
      "content": "Thanks, Bob!", "like_count": 1, "created_at": "2024-06-01T14:50:00Z" }]
  }],
  "next_cursor": "Y3Vyc29y...", "total_count": 18
}
```

### POST /api/v1/posts/{id}/comments
Adds a top-level comment or a threaded reply. Omit `parent_comment_id` for top-level.
**Auth:** Yes | **Body:** `{ content, parent_comment_id? }` | **Response 201:** Created comment object.

### DELETE /api/v1/posts/{id}/comments/{comment_id}
Caller must own the comment, own the parent post, or hold the `moderator` role.
**Auth:** Yes | **Response:** `204 No Content`

### POST /api/v1/posts/{id}/share
Reposts or quote-reposts the target. Omit `content` for a plain repost.
**Auth:** Yes | **Body:** `{ content?, visibility }` | **Response 201:** New post with `post_type: "repost"`.

### POST /api/v1/posts/{id}/report
Submits a content report for moderator review.
**Auth:** Yes | **Body:** `{ reason: "HARASSMENT", description: "..." }` | **Response:** `{ "report_id": "rpt_07XYZ", "status": "received" }`

---

## Feed APIs

### GET /api/v1/feed?cursor=&limit=50
Personalized home feed combining followed-account posts with algorithmically ranked recommendations. The ranking model weighs recency, engagement velocity, and the caller's historical interaction signals.
**Auth:** Yes

```json
// Response 200
{
  "posts": [{
    "id": "pst_09QWE",
    "author": { "id": "usr_01HXZ", "username": "jane_doe", "display_name": "Jane Doe" },
    "content": "Just shipped a new feature! #buildinpublic",
    "media_urls": ["https://cdn.example.com/media/img1.jpg"],
    "like_count": 214, "comment_count": 18, "is_liked": false,
    "created_at": "2024-06-01T14:22:00Z",
    "ranking_score": 0.921,
    "feed_reason": "followed_user"
  }],
  "next_cursor": "Y3Vyc29y...",
  "request_id": "req_feed_001"
}
```

`feed_reason` describes item provenance: `followed_user`, `trending`, `recommended`, or `sponsored`.

### GET /api/v1/feed/explore?cursor=&limit=50&topic=
Trending or topic-filtered explore feed. Available to unauthenticated callers at a reduced rate limit. `topic` accepts a hashtag or category slug.
**Auth:** Optional | **Response:** Same envelope as `/feed`.

### GET /api/v1/feed/following?cursor=&limit=50
Strictly chronological feed from followed accounts — no algorithmic ranking applied.
**Auth:** Yes | **Response:** Same envelope as `/feed` with `ranking_score: null`.

---

## Messaging APIs

### GET /api/v1/conversations?cursor=&limit=
Lists all conversations the caller participates in, ordered by most recent activity.
**Auth:** Yes | **Response:** `{ "conversations": [{ id, type, participants, last_message, unread_count }], "next_cursor": "..." }`

### POST /api/v1/conversations
Creates a direct message thread (`participant_ids` must have exactly one entry) or a named group chat.
**Auth:** Yes | **Body:** `{ participant_ids, type: "direct"|"group", name? }` | **Response 201:** Conversation object.

### GET /api/v1/conversations/{id}/messages?cursor=&limit=
Paginated message history, ordered newest-first. Restricted to conversation participants.
**Auth:** Yes | **Response:** `{ "messages": [{ id, sender, content, media_url, message_type, status, created_at }], "next_cursor": "..." }`

### POST /api/v1/conversations/{id}/messages
Sends a message. Valid `message_type` values: `text`, `image`, `video`, `file`, `reaction`.
**Auth:** Yes | **Body:** `{ content, media_url?, message_type }` | **Response 201:** Created message object.

### PUT /api/v1/conversations/{id}/read
Marks all messages in the conversation as read for the authenticated caller.
**Auth:** Yes | **Response:** `{ "unread_count": 0 }`

### WebSocket: wss://api/v1/ws/messaging
Persistent connection for real-time message delivery. Authentication uses the JWT access token as a query parameter (`?token=<access_token>`) on the initial handshake. The server pushes typed frames: `message.new`, `message.updated`, `conversation.updated`, and `typing.indicator`.

---

## Group APIs

### POST /api/v1/groups
Creates a new group. **Auth:** Yes
**Body:** `{ name, description, privacy: "public"|"private", invite_only: bool }` | **Response 201:** Group object.

### GET /api/v1/groups/{id}
Returns group metadata. `role` reflects the caller's membership role (`admin`, `moderator`, `member`), or `null` if not a member.
**Auth:** Optional | **Response:** `{ id, name, description, privacy, member_count, is_member, role, created_at }`

### PUT /api/v1/groups/{id}
Updates group metadata. Restricted to group admins.
**Auth:** Yes (admin) | **Body:** Partial group object | **Response 200:** Updated group object.

### POST /api/v1/groups/{id}/join
Joins a public group immediately or submits a membership request for a private group.
**Auth:** Yes | **Response:** `{ "status": "member" | "pending" }`

### DELETE /api/v1/groups/{id}/leave
Removes the caller from the group. The sole admin must transfer ownership before leaving.
**Auth:** Yes | **Response:** `204 No Content`

### GET /api/v1/groups/{id}/posts?cursor=
Paginated post feed scoped to the group. Visibility follows group privacy settings.
**Auth:** Optional | **Response:** Same feed envelope as `/feed`.

### GET /api/v1/groups/{id}/members?cursor=
Paginated member list. **Auth:** Optional
**Response:** `{ "members": [{ user, role, joined_at }], "next_cursor": "..." }`

### POST /api/v1/groups/{id}/members/{user_id}/role
Updates a member's role. Caller must be a group admin and cannot demote themselves.
**Auth:** Yes (admin) | **Body:** `{ "role": "admin"|"moderator"|"member" }` | **Response:** `{ user_id, role }`

---

## Notification APIs

### GET /api/v1/notifications?cursor=&limit=&unread_only=
Paginated notification list. **Auth:** Yes
**Response:** `{ "notifications": [{ id, type, actor, resource_type, resource_id, is_read, created_at }], "unread_count": 7, "next_cursor": "..." }`

### PUT /api/v1/notifications/{id}/read
Marks a single notification as read.
**Auth:** Yes | **Response:** `{ "id": "ntf_11BBB", "is_read": true }`

### PUT /api/v1/notifications/read-all
Marks all unread notifications as read for the authenticated user.
**Auth:** Yes | **Response:** `{ "updated_count": 7 }`

### DELETE /api/v1/notifications/{id}
Permanently dismisses a notification. **Auth:** Yes | **Response:** `204 No Content`

### GET /api/v1/notifications/preferences
Retrieves per-channel delivery settings (`push`, `email`, `in_app`) for each notification category (`likes`, `comments`, `follows`, `messages`, `group_activity`).
**Auth:** Yes

### PUT /api/v1/notifications/preferences
Updates notification delivery preferences. A partial body is accepted; omitted keys are left unchanged.
**Auth:** Yes | **Body:** Partial preferences object | **Response 200:** Full updated preferences object.

---

## Moderation APIs

### POST /api/v1/reports
Submits a report against any platform resource. Valid `reason` codes: `SPAM`, `HARASSMENT`, `HATE_SPEECH`, `MISINFORMATION`, `NUDITY`, `VIOLENCE`, `OTHER`.
**Auth:** Yes | **Body:** `{ resource_type, resource_id, reason, description }` | **Response:** `{ "report_id": "rpt_07XYZ", "status": "received" }`

### GET /api/v1/admin/reports?status=&cursor=
Lists reports filtered by `status` (`pending`, `resolved`, `dismissed`). Requires the `moderator` role.
**Auth:** Yes (moderator) | **Response:** Paginated list of report objects.

### PUT /api/v1/admin/reports/{id}/action
Records a moderation action. Valid `action_type` values: `REMOVE_CONTENT`, `WARN_USER`, `SUSPEND_USER`, `BAN_USER`, `DISMISS_REPORT`.
**Auth:** Yes (moderator) | **Body:** `{ action_type, reason }` | **Response:** Updated report with `status: "resolved"`.

### GET /api/v1/admin/users/{id}/moderation-history
Retrieves the complete moderation action history for a user. Requires the `admin` role.
**Auth:** Yes (admin) | **Response:** `{ "user_id": "...", "actions": [{ id, action_type, reason, moderator_id, created_at }] }`

---

## GraphQL Schema Excerpt

The platform exposes a GraphQL endpoint at `/api/v1/graphql` as a complement to the REST surface, enabling clients to request exactly the fields they require and subscribe to real-time events.

```graphql
scalar DateTime
scalar Cursor
scalar URL

enum FeedType       { PERSONALIZED FOLLOWING EXPLORE }
enum MessageType    { TEXT IMAGE VIDEO FILE REACTION }
enum NotificationType { LIKE COMMENT FOLLOW FOLLOW_REQUEST MENTION GROUP_INVITE MESSAGE }

type User {
  id: ID!; username: String!; displayName: String!; bio: String; avatarUrl: URL
  followerCount: Int!; followingCount: Int!; isFollowing: Boolean; isBlocked: Boolean
  createdAt: DateTime!
}

type Post {
  id: ID!; author: User!; content: String; mediaUrls: [URL!]
  likeCount: Int!; commentCount: Int!; isLiked: Boolean; createdAt: DateTime!
}

type FeedItem {
  post: Post!
  rankingScore: Float
  feedReason: String!
}

type Conversation {
  id: ID!; type: String!; participants: [User!]!
  lastMessage: Message; unreadCount: Int!
}

type Message {
  id: ID!; sender: User!; content: String
  messageType: MessageType!; status: String!; createdAt: DateTime!
}

type Notification {
  id: ID!; type: NotificationType!; actor: User
  resourceType: String!; resourceId: ID!; isRead: Boolean!; createdAt: DateTime!
}

type Query {
  feed(cursor: Cursor, limit: Int = 50, feedType: FeedType = PERSONALIZED): [FeedItem!]!
  user(id: ID!): User
  post(id: ID!): Post
  searchUsers(query: String!, limit: Int = 20): [User!]!
  searchPosts(query: String, hashtag: String, limit: Int = 20, cursor: Cursor): [FeedItem!]!
}

type Mutation {
  createPost(content: String!, mediaUrls: [URL], visibility: String = "public", hashtags: [String]): Post!
  likePost(postId: ID!, reactionType: String = "like"): Post!
  followUser(userId: ID!): User!
  sendMessage(conversationId: ID!, content: String!, messageType: MessageType = TEXT): Message!
  reportContent(resourceType: String!, resourceId: ID!, reason: String!, description: String): Boolean!
}

type Subscription {
  onNewMessage(conversationId: ID!): Message!
  onNotification: Notification!
  onFeedUpdate: FeedItem!
}
```

---

## Rate Limiting Strategy

Rate limits are enforced at the API gateway using a sliding-window counter keyed by user ID for authenticated requests and by IP address for unauthenticated ones. Clients exceeding a limit receive `429 Too Many Requests` with a `Retry-After` header. A burst allowance of 10 requests per second is permitted before accumulation begins, accommodating legitimate spikes during app startup. Clients should implement exponential back-off with jitter when retrying after a `429` response.

| Endpoint Group       | Authenticated    | Unauthenticated  |
|----------------------|------------------|------------------|
| Auth                 | 20 / hour / IP   | 10 / hour / IP   |
| User reads           | 1 000 / hour     | 100 / hour       |
| Post creation        | 50 / hour        | N/A              |
| Like / Follow        | 500 / hour       | N/A              |
| Messaging            | 200 / hour       | N/A              |
| Feed reads           | 500 / hour       | 200 / hour       |
| Search               | 200 / hour       | 50 / hour        |
