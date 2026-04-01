# System Sequence Diagrams — Social Networking Platform

## 1. Overview

These sequence diagrams capture the end-to-end message flow across microservices for the four most
critical runtime paths in the Social Networking Platform:

| # | Scenario | Primary Services Involved |
|---|----------|--------------------------|
| 1 | User Registration & Login | User Service, Profile Service, Auth/Token Service, Notification Service |
| 2 | Create Post & Feed Fan-Out | Post Service, Media Service, Feed Service, Social Graph Service, Cache, Message Broker |
| 3 | Real-time Notification Delivery | Any trigger service, Notification Service, WebSocket Gateway, Push Gateway |
| 4 | Direct Message (E2E Encrypted) | Messaging Service, WebSocket Gateway, Notification Service, Media Service |

All inter-service calls go through an internal service mesh (mTLS). Client-facing calls pass through
the API Gateway, which handles JWT validation, rate limiting, and request routing.

---

## 2. User Registration & Login

### 2.1 Registration Flow

A new user submits their email and password. The User Service creates the account, hashes the
credential, fires a domain event, and delegates welcome-email dispatch to the Notification Service.
The Profile Service initialises an empty profile record on the same event.

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant GW as API Gateway
    participant US as User Service
    participant PS as Profile Service
    participant NS as Notification Service
    participant MB as Message Broker (Kafka)
    participant Cache as Redis Cache
    participant DB as Users DB (Postgres)

    Client->>GW: POST /users { email, username, password }
    GW->>GW: Rate-limit check (IP bucket)
    GW->>US: Forward request (no JWT required)

    US->>DB: SELECT * FROM users WHERE email = ?
    DB-->>US: 0 rows (email available)

    US->>US: bcrypt hash password (cost=12)
    US->>DB: INSERT INTO users (id, email, username, status=PENDING_VERIFY)
    DB-->>US: OK

    US->>MB: Publish user.registered { userId, email, username }
    MB-->>US: ACK

    US-->>GW: 201 Created { userId, username }
    GW-->>Client: 201 Created { userId, username }

    par Profile Initialisation
        MB->>PS: Consume user.registered
        PS->>PS: Create empty UserProfile record
        PS-->>MB: ACK
    and Welcome Email
        MB->>NS: Consume user.registered
        NS->>NS: Render welcome-email template
        NS->>NS: Enqueue to SMTP worker (SendGrid)
        NS-->>MB: ACK
    end
```

### 2.2 Email Verification Flow

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant GW as API Gateway
    participant US as User Service
    participant Cache as Redis Cache
    participant DB as Users DB (Postgres)

    Note over Client,DB: User clicks verification link in email
    Client->>GW: GET /users/verify?token=<jwt-otp>
    GW->>US: Forward request

    US->>Cache: GET verify:<token>
    Cache-->>US: { userId }

    US->>DB: UPDATE users SET status=ACTIVE WHERE id=?
    DB-->>US: OK

    US->>Cache: DEL verify:<token>
    US-->>GW: 200 OK { message: "Account activated" }
    GW-->>Client: 200 OK
```

### 2.3 Login & Token Issuance Flow

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant GW as API Gateway
    participant US as User Service
    participant Cache as Redis Cache
    participant DB as Users DB (Postgres)

    Client->>GW: POST /auth/login { email, password }
    GW->>US: Forward request

    US->>DB: SELECT id, password_hash, status FROM users WHERE email=?
    DB-->>US: { id, password_hash, status=ACTIVE }

    US->>US: bcrypt.compare(password, hash)
    Note right of US: Constant-time comparison

    US->>US: Sign JWT access token (15 min TTL)
    US->>US: Sign JWT refresh token (30 day TTL)
    US->>Cache: SET refresh:<userId>:<tokenId> TTL=30d

    US-->>GW: 200 OK { accessToken, refreshToken, expiresIn }
    GW-->>Client: 200 OK { accessToken, refreshToken, expiresIn }

    Note over Client: Client stores accessToken in memory,<br/>refreshToken in httpOnly cookie
```

---

## 3. Create Post & Feed Fan-Out

### 3.1 Post Creation with Media Upload

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant GW as API Gateway
    participant PostSvc as Post Service
    participant MediaSvc as Media Service
    participant CDN as CDN (CloudFront)
    participant S3 as Object Store (S3)
    participant DB as Posts DB (Postgres)
    participant MB as Message Broker (Kafka)

    Client->>GW: POST /posts (multipart: text + images)
    GW->>GW: Validate JWT, extract userId
    GW->>PostSvc: Forward metadata + presign request

    PostSvc->>MediaSvc: POST /media/presign { files: [{name, type, size}] }
    MediaSvc->>S3: GeneratePresignedPutURL (TTL=5min, max 20 MB)
    S3-->>MediaSvc: presignedUrls[]
    MediaSvc-->>PostSvc: { uploadUrls[] }
    PostSvc-->>GW: 200 { uploadUrls[], draftPostId }
    GW-->>Client: 200 { uploadUrls[], draftPostId }

    loop For each media file
        Client->>S3: PUT <presignedUrl> (binary)
        S3-->>Client: 200 OK
    end

    Client->>GW: POST /posts/:draftPostId/publish { mediaKeys[] }
    GW->>PostSvc: Forward publish

    PostSvc->>MediaSvc: POST /media/confirm { keys[] }
    MediaSvc->>MediaSvc: Trigger async transcoding job
    MediaSvc-->>PostSvc: { mediaIds[], thumbnailUrls[] }

    PostSvc->>DB: INSERT INTO posts (id, authorId, content, mediaIds, status=PUBLISHED)
    DB-->>PostSvc: OK
    PostSvc->>MB: Publish post.created { postId, authorId, visibility, tags, mentionedUsers }
    MB-->>PostSvc: ACK
    PostSvc-->>GW: 201 Created { postId, url }
    GW-->>Client: 201 Created { postId, url }
```

### 3.2 Feed Fan-Out (Hybrid Push/Pull)

```mermaid
sequenceDiagram
    autonumber
    participant MB as Message Broker (Kafka)
    participant FeedSvc as Feed Service
    participant SGSvc as Social Graph Service
    participant RankSvc as Feed Ranking (ML)
    participant Cache as Feed Cache (Redis)
    participant DB as Feed DB (Cassandra)

    MB->>FeedSvc: Consume post.created { postId, authorId }

    FeedSvc->>SGSvc: GET /graph/followers { userId: authorId, limit: 10000 }
    SGSvc-->>FeedSvc: { followerIds[] }

    Note over FeedSvc: Celebrity check: if followers > 1M,<br/>switch to pull-on-read for large accounts

    FeedSvc->>RankSvc: POST /rank/score { postId, authorId }
    RankSvc->>RankSvc: Compute engagement-prediction score (BERT embeddings + XGBoost)
    RankSvc-->>FeedSvc: { score: 0.87, boostFactors: [...] }

    loop Fan-out (batched, async workers)
        FeedSvc->>Cache: ZADD feed:<followerId> score postId (TTL=7d)
        FeedSvc->>DB: INSERT INTO feed_items (userId, postId, score, ts)
    end

    Note over FeedSvc,DB: Active users (online in last 5 min) get<br/>Cache-only fan-out; others get DB write.
```

### 3.3 Feed Read (Client Fetching Timeline)

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant GW as API Gateway
    participant FeedSvc as Feed Service
    participant Cache as Feed Cache (Redis)
    participant DB as Feed DB (Cassandra)
    participant PostSvc as Post Service
    participant RankSvc as Feed Ranking (ML)

    Client->>GW: GET /feed?cursor=<ts>&limit=20
    GW->>GW: Validate JWT
    GW->>FeedSvc: Forward { userId, cursor, limit }

    FeedSvc->>Cache: ZREVRANGEBYSCORE feed:<userId> (paginate by cursor)
    Cache-->>FeedSvc: postIds[] (cache hit)

    alt Cache miss / stale feed
        FeedSvc->>DB: SELECT postId, score FROM feed_items WHERE userId=? ORDER BY score DESC
        DB-->>FeedSvc: postIds[]
        FeedSvc->>RankSvc: POST /rank/personalise { userId, postIds[] }
        RankSvc-->>FeedSvc: ranked postIds[]
    end

    FeedSvc->>PostSvc: POST /posts/batch { ids: postIds[] }
    PostSvc-->>FeedSvc: posts[] (hydrated with author, media, reactions)

    FeedSvc-->>GW: 200 OK { posts[], nextCursor }
    GW-->>Client: 200 OK { posts[], nextCursor }
```

---

## 4. Real-time Notification Delivery

```mermaid
sequenceDiagram
    autonumber
    participant TriggerSvc as Trigger Service (e.g. Post Service)
    participant MB as Message Broker (Kafka)
    participant NotifSvc as Notification Service
    participant PrefDB as Prefs DB (Postgres)
    participant WS as WebSocket Gateway
    participant Push as Push Gateway (FCM/APNs)
    participant Email as Email Worker (SendGrid)
    participant Cache as Notification Cache (Redis)
    actor Recipient

    TriggerSvc->>MB: Publish notification.trigger { type: REACTION, actorId, targetUserId, entityId }

    MB->>NotifSvc: Consume notification.trigger

    NotifSvc->>PrefDB: SELECT preferences WHERE userId=targetUserId AND type=REACTION
    PrefDB-->>NotifSvc: { inApp: true, push: true, email: false }

    NotifSvc->>NotifSvc: Render notification payload { title, body, deeplink }
    NotifSvc->>Cache: LPUSH notif:<targetUserId> payload (TTL=30d, max 500 items)

    par In-App (WebSocket)
        NotifSvc->>WS: POST /ws/send { userId: targetUserId, event: "notification", payload }
        WS->>WS: Lookup active socket(s) for userId
        alt User online
            WS-->>Recipient: Push frame over WebSocket
        else User offline
            WS->>NotifSvc: 404 user-offline
            Note over NotifSvc: Notification already in cache;<br/>client fetches on reconnect
        end
    and Mobile Push
        NotifSvc->>Push: POST /push { deviceTokens[], title, body, data }
        Push->>Push: Route to FCM (Android) or APNs (iOS)
        Push-->>NotifSvc: { sent: 2, failed: 0 }
    end

    Recipient->>WS: WebSocket CONNECT (on app open)
    WS->>NotifSvc: GET /notifications/unread?userId=targetUserId
    NotifSvc->>Cache: LRANGE notif:<targetUserId> 0 49
    Cache-->>NotifSvc: pending notifications[]
    NotifSvc-->>WS: notifications[]
    WS-->>Recipient: Batch push unread notifications
```

---

## 5. Direct Message (E2E Encrypted)

```mermaid
sequenceDiagram
    autonumber
    actor Sender
    actor Recipient
    participant GW as API Gateway
    participant MsgSvc as Messaging Service
    participant KeySvc as Key Service (KMS)
    participant WS as WebSocket Gateway
    participant S3 as Object Store (media)
    participant DB as Messages DB (Cassandra)
    participant MB as Message Broker (Kafka)
    participant NotifSvc as Notification Service

    Note over Sender,Recipient: Signal Protocol key exchange already completed<br/>on first conversation open (X3DH handshake)

    Sender->>GW: POST /messages { conversationId, ciphertext, mediaKey? }
    GW->>GW: Validate JWT (senderId)
    GW->>MsgSvc: Forward message

    MsgSvc->>DB: SELECT conversation WHERE id=conversationId
    DB-->>MsgSvc: { participantIds: [senderId, recipientId], status: ACTIVE }

    MsgSvc->>MsgSvc: Verify sender is participant
    MsgSvc->>DB: INSERT INTO messages (id, conversationId, senderId, ciphertext, sentAt, status=SENT)
    DB-->>MsgSvc: OK

    MsgSvc->>MB: Publish message.sent { msgId, conversationId, recipientId }
    MB-->>MsgSvc: ACK
    MsgSvc-->>GW: 201 Created { messageId, sentAt }
    GW-->>Sender: 201 Created { messageId, sentAt }

    MB->>WS: Consume message.sent
    WS->>WS: Lookup WebSocket for recipientId

    alt Recipient online
        WS-->>Recipient: Push encrypted frame { msgId, ciphertext, senderId, sentAt }
        Recipient->>WS: ACK { msgId }
        WS->>MsgSvc: PATCH /messages/:msgId/status { status: DELIVERED }
        MsgSvc->>DB: UPDATE messages SET status=DELIVERED
        WS-->>Sender: Push delivery-receipt { msgId, status: DELIVERED }
    else Recipient offline
        MB->>NotifSvc: Consume message.sent
        NotifSvc->>NotifSvc: Build push payload (no plaintext — only "New message")
        NotifSvc->>NotifSvc: Dispatch FCM/APNs silent push
    end

    Note over Recipient: Recipient opens app, establishes WebSocket
    Recipient->>GW: GET /conversations/:id/messages?after=<lastMsgId>
    GW->>MsgSvc: Forward
    MsgSvc->>DB: SELECT * FROM messages WHERE conversationId=? AND id > lastMsgId
    DB-->>MsgSvc: messages[]
    MsgSvc-->>GW: 200 OK { messages[] }
    GW-->>Recipient: 200 OK { messages[] }
    Recipient->>Recipient: Decrypt each message using local session key
    Recipient->>GW: PATCH /messages/batch-status { ids[], status: READ }
    GW->>MsgSvc: Forward
    MsgSvc->>DB: UPDATE messages SET status=READ
    MsgSvc->>MB: Publish message.read { ids[], senderId }
    MB->>WS: Consume message.read
    WS-->>Sender: Push read-receipts { ids[], status: READ }
```
