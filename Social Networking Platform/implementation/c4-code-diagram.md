# C4 Code Diagram — Social Networking Platform

## 1. Overview

This document presents code-level (C4 Level 4) class diagrams for four core services of the
Social Networking Platform: **Post Service**, **Feed Service**, **Notification Service**, and
**Messaging Service**. Each diagram shows the primary classes, their public interfaces, and
inter-class relationships, reflecting the layered architecture (Controller → Service →
Repository) used across all Go and Python services.

All Go services follow a hexagonal architecture pattern: inbound adapters (HTTP handlers),
domain core (service + domain models), and outbound adapters (repositories, Kafka producer,
external clients). Python services (Feed, Moderation, Analytics) follow a similar structure
with FastAPI routers acting as controllers.

---

## 2. Post Service — Code Structure

```mermaid
classDiagram
    class PostController {
        -postService PostService
        -validator Validator
        +createPost(ctx Context, req CreatePostRequest) Response
        +getPost(ctx Context, postId string) Response
        +deletePost(ctx Context, postId string) Response
        +listUserPosts(ctx Context, userId string, cursor string) Response
        +addReaction(ctx Context, postId string, req ReactionRequest) Response
        +removeReaction(ctx Context, postId string, reactionType string) Response
        +getPostReactions(ctx Context, postId string) Response
        +createComment(ctx Context, postId string, req CommentRequest) Response
        +listComments(ctx Context, postId string, cursor string) Response
    }

    class PostService {
        -postRepo PostRepository
        -mediaClient MediaClient
        -graphClient GraphClient
        -kafkaProducer KafkaProducer
        -redisClient RedisClient
        +CreatePost(ctx Context, userId string, req CreatePostInput) Post
        +GetPost(ctx Context, postId string, viewerId string) Post
        +DeletePost(ctx Context, postId string, requesterId string) void
        +AddReaction(ctx Context, postId string, userId string, reactionType string) void
        +RemoveReaction(ctx Context, postId string, userId string, reactionType string) void
        +FanOutToFeeds(ctx Context, postId string, authorId string) void
        +IncrementViewCount(ctx Context, postId string) void
        -validateVisibility(post Post, viewerId string) bool
        -enrichWithMediaURLs(post Post) Post
    }

    class PostRepository {
        -db *pgxpool.Pool
        -readDb *pgxpool.Pool
        +Save(ctx Context, post Post) Post
        +FindById(ctx Context, id string) Post
        +FindByUserId(ctx Context, userId string, cursor Cursor) []Post
        +SoftDelete(ctx Context, id string, deletedBy string) void
        +FindReactions(ctx Context, postId string) []Reaction
        +SaveReaction(ctx Context, reaction Reaction) void
        +DeleteReaction(ctx Context, postId string, userId string) void
        +SaveComment(ctx Context, comment Comment) Comment
        +FindComments(ctx Context, postId string, cursor Cursor) []Comment
        +IncrementCounter(ctx Context, postId string, field string) void
    }

    class Post {
        +ID string
        +AuthorID string
        +Content string
        +MediaIDs []string
        +Visibility string
        +ReactionCount map~string~int~
        +CommentCount int
        +ShareCount int
        +ViewCount int
        +CreatedAt time.Time
        +DeletedAt *time.Time
        +IsDeleted() bool
        +CanView(viewerId string, relationship string) bool
        +ToFeedItem() FeedItem
    }

    class KafkaProducer {
        -producer *kafka.Producer
        -schemaRegistry SchemaRegistryClient
        +PublishPostCreated(ctx Context, event PostCreatedEvent) void
        +PublishPostDeleted(ctx Context, event PostDeletedEvent) void
        +PublishReactionAdded(ctx Context, event ReactionEvent) void
    }

    class MediaClient {
        -httpClient *http.Client
        -baseURL string
        +GetMediaURLs(ctx Context, mediaIds []string) map~string~string~
        +ValidateMediaOwnership(ctx Context, mediaId string, userId string) bool
    }

    class GraphClient {
        -conn *grpc.ClientConn
        +GetFollowers(ctx Context, userId string, cursor string) []string
        +GetFollowerCount(ctx Context, userId string) int
        +IsBlocked(ctx Context, userId string, targetId string) bool
    }

    PostController --> PostService
    PostService --> PostRepository
    PostService --> KafkaProducer
    PostService --> MediaClient
    PostService --> GraphClient
    PostRepository --> Post
    PostService --> Post
```

---

## 3. Feed Service — Code Structure

```mermaid
classDiagram
    class FeedRouter {
        -feedService FeedService
        +get_user_feed(request Request) JSONResponse
        +get_explore_feed(request Request) JSONResponse
        +get_user_posts_feed(request Request) JSONResponse
        +invalidate_feed(request Request) JSONResponse
    }

    class FeedService {
        -feedRepo FeedRepository
        -ranker FeedRanker
        -postClient PostClient
        -graphClient GraphClient
        -cacheClient RedisCacheClient
        +get_feed(user_id str, cursor str, limit int) FeedPage
        +build_feed(user_id str) void
        +append_to_feed(user_id str, post_id str, score float) void
        +remove_from_feed(user_id str, post_id str) void
        +get_explore_feed(user_id str, cursor str) FeedPage
        -_is_feed_stale(user_id str) bool
        -_apply_diversity_filter(items list) list
    }

    class FeedRanker {
        -sagemaker_client SageMakerClient
        -feature_store FeatureStore
        -model_name str
        +rank_candidates(user_id str, candidates list) list
        +compute_features(user_id str, post_id str) FeatureVector
        +get_ranking_scores(feature_matrix ndarray) ndarray
        -_build_feature_vector(user_features dict, post_features dict, edge_features dict) ndarray
    }

    class FeedRepository {
        -redis RedisClient
        -dynamo DynamoClient
        +get_feed_items(user_id str, cursor str, limit int) list
        +add_feed_item(user_id str, item FeedItem, score float) void
        +remove_feed_item(user_id str, post_id str) void
        +get_feed_cursor(encoded_cursor str) FeedCursor
        +encode_cursor(last_score float, last_post_id str) str
        +get_feed_size(user_id str) int
        +trim_feed(user_id str, max_size int) void
    }

    class FeedItem {
        +post_id str
        +author_id str
        +score float
        +inserted_at datetime
        +source str
        +post_data dict
    }

    class FeatureStore {
        -redis RedisClient
        +get_user_features(user_id str) dict
        +get_post_features(post_id str) dict
        +get_edge_features(user_id str, author_id str) dict
        +set_user_features(user_id str, features dict, ttl int) void
        +set_post_features(post_id str, features dict, ttl int) void
    }

    class PostClient {
        -base_url str
        -session aiohttp.ClientSession
        +get_posts_batch(post_ids list) dict
        +get_post(post_id str) dict
    }

    FeedRouter --> FeedService
    FeedService --> FeedRanker
    FeedService --> FeedRepository
    FeedService --> PostClient
    FeedRanker --> FeatureStore
    FeedRepository --> FeedItem
```

---

## 4. Notification Service — Code Structure

```mermaid
classDiagram
    class NotificationController {
        -notifService NotificationService
        +listNotifications(ctx Context, userId string, cursor string) Response
        +markAsRead(ctx Context, userId string, notifId string) Response
        +markAllAsRead(ctx Context, userId string) Response
        +getUnreadCount(ctx Context, userId string) Response
        +updatePreferences(ctx Context, userId string, req PrefsRequest) Response
        +getPreferences(ctx Context, userId string) Response
    }

    class NotificationService {
        -notifRepo NotificationRepository
        -prefRepo PreferenceRepository
        -dispatcher NotificationDispatcher
        -kafkaConsumer KafkaConsumer
        +GetNotifications(ctx Context, userId string, cursor string) []Notification
        +MarkRead(ctx Context, userId string, notifId string) void
        +MarkAllRead(ctx Context, userId string) void
        +GetUnreadCount(ctx Context, userId string) int
        +ProcessEvent(ctx Context, event NotificationEvent) void
        +SendPush(ctx Context, userId string, notif Notification) void
        -buildNotificationPayload(event NotificationEvent) Notification
        -shouldSend(userId string, notifType string, prefs UserPreferences) bool
    }

    class NotificationRepository {
        -dynamoClient *dynamodb.Client
        -tableName string
        +Save(ctx Context, notif Notification) void
        +FindByUserId(ctx Context, userId string, cursor Cursor) []Notification
        +MarkAsRead(ctx Context, userId string, notifId string) void
        +MarkAllAsRead(ctx Context, userId string) void
        +GetUnreadCount(ctx Context, userId string) int
        +DeleteExpired(ctx Context, userId string) void
    }

    class NotificationDispatcher {
        -apnsClient APNsClient
        -fcmClient FCMClient
        -webPushClient WebPushClient
        -deviceRepo DeviceRepository
        +Dispatch(ctx Context, userId string, payload PushPayload) DispatchResult
        -dispatchAPNs(token string, payload PushPayload) error
        -dispatchFCM(token string, payload PushPayload) error
        -dispatchWebPush(endpoint string, payload PushPayload) error
    }

    class KafkaConsumer {
        -consumer *kafka.Consumer
        -handlers map~string~EventHandler~
        +Start(ctx Context) void
        +Stop() void
        +RegisterHandler(topic string, handler EventHandler) void
        -processMessage(msg *kafka.Message) void
        -handleDeadLetter(msg *kafka.Message, err error) void
    }

    class Notification {
        +ID string
        +UserID string
        +Type string
        +ActorID string
        +ActorName string
        +ActorAvatarURL string
        +EntityID string
        +EntityType string
        +Body string
        +IsRead bool
        +CreatedAt time.Time
        +ExpiresAt time.Time
        +ToPayload() PushPayload
    }

    class DeviceRepository {
        -db *pgxpool.Pool
        +FindByUserId(ctx Context, userId string) []Device
        +Register(ctx Context, device Device) void
        +Deregister(ctx Context, deviceToken string) void
        +UpdateLastSeen(ctx Context, deviceToken string) void
    }

    NotificationController --> NotificationService
    NotificationService --> NotificationRepository
    NotificationService --> NotificationDispatcher
    NotificationService --> KafkaConsumer
    NotificationDispatcher --> DeviceRepository
    NotificationRepository --> Notification
```

---

## 5. Messaging Service — Code Structure

```mermaid
classDiagram
    class MessagingController {
        -msgService MessagingService
        -wsHub WebSocketHub
        +createConversation(ctx Context, req ConversationRequest) Response
        +getConversations(ctx Context, userId string, cursor string) Response
        +getMessages(ctx Context, conversationId string, cursor string) Response
        +sendMessage(ctx Context, conversationId string, req SendMessageRequest) Response
        +deleteMessage(ctx Context, messageId string) Response
        +handleWebSocket(ctx Context, w http.ResponseWriter, r *http.Request) void
        +markConversationRead(ctx Context, conversationId string) Response
    }

    class MessagingService {
        -msgRepo MessageRepository
        -convRepo ConversationRepository
        -userClient UserClient
        -wsHub WebSocketHub
        -redisClient RedisClient
        +CreateConversation(ctx Context, creatorId string, participantIds []string) Conversation
        +SendMessage(ctx Context, senderId string, convId string, content MessageContent) Message
        +GetMessages(ctx Context, convId string, viewerId string, cursor string) []Message
        +DeleteMessage(ctx Context, messageId string, userId string) void
        +MarkRead(ctx Context, convId string, userId string) void
        +GetUnreadCounts(ctx Context, userId string) map~string~int~
        -validateParticipant(ctx Context, userId string, convId string) bool
        -publishToWebSocket(convId string, event MessageEvent) void
    }

    class WebSocketHub {
        -connections sync.Map
        -redisClient RedisClient
        -upgrader websocket.Upgrader
        +Register(conn *WebSocketConn) void
        +Unregister(userId string, connId string) void
        +BroadcastToConversation(convId string, event MessageEvent) void
        +BroadcastToUser(userId string, event MessageEvent) void
        +HandleConnection(userId string, w http.ResponseWriter, r *http.Request) void
        -subscribeRedis(pattern string) void
        -publishRedis(channel string, event MessageEvent) void
    }

    class MessageRepository {
        -db *pgxpool.Pool
        -dynamo *dynamodb.Client
        +Save(ctx Context, msg Message) Message
        +FindByConversationId(ctx Context, convId string, cursor Cursor) []Message
        +SoftDelete(ctx Context, msgId string, userId string) void
        +FindById(ctx Context, msgId string) Message
    }

    class ConversationRepository {
        -db *pgxpool.Pool
        +Create(ctx Context, conv Conversation) Conversation
        +FindByUserId(ctx Context, userId string, cursor Cursor) []Conversation
        +FindById(ctx Context, convId string) Conversation
        +UpdateLastMessage(ctx Context, convId string, msg Message) void
        +UpdateReadCursor(ctx Context, convId string, userId string, msgId string) void
        +GetParticipants(ctx Context, convId string) []string
    }

    class Message {
        +ID string
        +ConversationID string
        +SenderID string
        +Content MessageContent
        +Status string
        +ReplyToID *string
        +DeletedAt *time.Time
        +CreatedAt time.Time
        +IsDeleted() bool
        +ToEvent() MessageEvent
    }

    MessagingController --> MessagingService
    MessagingController --> WebSocketHub
    MessagingService --> MessageRepository
    MessagingService --> ConversationRepository
    MessagingService --> WebSocketHub
    MessageRepository --> Message
```
