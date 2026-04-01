# Class Diagrams — Social Networking Platform

## 1. Overview

This document captures the detailed object-oriented class model for the Social Networking Platform. Each domain section contains a Mermaid `classDiagram` that shows attributes, methods, and inter-class relationships. Together these diagrams form the authoritative blueprint for entity modelling, ORM schema generation, and API contract design.

Relationship notation used throughout:
- `<|--` inheritance / extends
- `*--` composition (strong ownership)
- `o--` aggregation (loose ownership)
- `-->` directed association
- `..>` dependency

---

## 2. User Domain

Covers identity, authentication credentials, social graph edges (follow / block / friend request), and profile metadata.

```mermaid
classDiagram
    class User {
        +UUID id
        +String username
        +String email
        +String phoneNumber
        +UserStatus status
        +Boolean isVerified
        +Boolean isMfaEnabled
        +DateTime createdAt
        +DateTime updatedAt
        +DateTime deletedAt
        +register(email, password) User
        +deactivate() void
        +reactivate() void
        +verifyEmail(token) Boolean
        +requestPasswordReset() void
        +updateEmail(newEmail) void
        +enableMfa(method) void
    }

    class UserProfile {
        +UUID id
        +UUID userId
        +String displayName
        +String bio
        +String avatarUrl
        +String coverImageUrl
        +String website
        +String location
        +Date birthDate
        +GenderType gender
        +PrivacySetting profileVisibility
        +DateTime updatedAt
        +updateAvatar(imageUrl) void
        +updateBio(text) void
        +setVisibility(setting) void
    }

    class UserCredential {
        +UUID id
        +UUID userId
        +CredentialType type
        +String hashedSecret
        +String salt
        +DateTime lastUsedAt
        +DateTime expiresAt
        +Boolean isRevoked
        +validate(secret) Boolean
        +revoke() void
        +rotate(newSecret) void
    }

    class Follow {
        +UUID id
        +UUID followerId
        +UUID followeeId
        +FollowStatus status
        +DateTime createdAt
        +DateTime approvedAt
        +approve() void
        +reject() void
        +unfollow() void
    }

    class Block {
        +UUID id
        +UUID blockerId
        +UUID blockedId
        +String reason
        +DateTime createdAt
        +unblock() void
    }

    class FriendRequest {
        +UUID id
        +UUID senderId
        +UUID receiverId
        +FriendRequestStatus status
        +String message
        +DateTime sentAt
        +DateTime respondedAt
        +accept() void
        +decline() void
        +cancel() void
    }

    class UserSession {
        +UUID id
        +UUID userId
        +String deviceFingerprint
        +String ipAddress
        +String userAgent
        +String refreshToken
        +DateTime issuedAt
        +DateTime expiresAt
        +Boolean isActive
        +revoke() void
        +extend() void
    }

    User "1" *-- "1" UserProfile : has
    User "1" *-- "1..n" UserCredential : authenticates via
    User "1" *-- "0..n" UserSession : maintains
    User "1" o-- "0..n" Follow : followee
    User "1" o-- "0..n" Follow : follower
    User "1" o-- "0..n" Block : blocker
    User "1" o-- "0..n" FriendRequest : sender
    User "1" o-- "0..n" FriendRequest : receiver
```

---

## 3. Content Domain

Models all user-generated content: posts, media attachments, stories, polls, comments, reactions, shares, and reposts.

```mermaid
classDiagram
    class Post {
        +UUID id
        +UUID authorId
        +String body
        +PostType type
        +PostVisibility visibility
        +Boolean isEdited
        +Boolean isPinned
        +Boolean isSensitive
        +UUID communityId
        +UUID replyToPostId
        +Integer reactionCount
        +Integer commentCount
        +Integer shareCount
        +Integer repostCount
        +Integer viewCount
        +DateTime publishedAt
        +DateTime scheduledAt
        +DateTime createdAt
        +DateTime updatedAt
        +DateTime deletedAt
        +publish() void
        +schedule(at) void
        +softDelete() void
        +pin() void
        +unpin() void
        +markSensitive() void
        +incrementView() void
    }

    class PostMedia {
        +UUID id
        +UUID postId
        +MediaType mediaType
        +String originalUrl
        +String processedUrl
        +String thumbnailUrl
        +String altText
        +Integer width
        +Integer height
        +Integer durationSeconds
        +Long fileSizeBytes
        +String mimeType
        +Integer displayOrder
        +MediaStatus processingStatus
        +DateTime uploadedAt
        +process() void
        +generateThumbnail() void
    }

    class PostTag {
        +UUID id
        +UUID postId
        +String tag
        +DateTime createdAt
    }

    class Mention {
        +UUID id
        +UUID postId
        +UUID mentionedUserId
        +Integer startIndex
        +Integer endIndex
        +DateTime createdAt
        +notify() void
    }

    class Poll {
        +UUID id
        +UUID postId
        +String question
        +Integer durationHours
        +Boolean allowMultipleVotes
        +Boolean isAnonymous
        +DateTime expiresAt
        +DateTime createdAt
        +close() void
        +getResults() PollResults
    }

    class PollOption {
        +UUID id
        +UUID pollId
        +String optionText
        +Integer voteCount
        +Integer displayOrder
        +addVote(userId) void
        +removeVote(userId) void
    }

    class PollVote {
        +UUID id
        +UUID pollId
        +UUID pollOptionId
        +UUID userId
        +DateTime votedAt
    }

    class Story {
        +UUID id
        +UUID authorId
        +String mediaUrl
        +MediaType mediaType
        +String textOverlay
        +String backgroundColour
        +StoryStatus status
        +Integer viewCount
        +DateTime expiresAt
        +DateTime createdAt
        +expire() void
        +recordView(userId) void
    }

    class StoryView {
        +UUID id
        +UUID storyId
        +UUID viewerId
        +DateTime viewedAt
    }

    class Comment {
        +UUID id
        +UUID postId
        +UUID authorId
        +UUID parentCommentId
        +String body
        +Boolean isEdited
        +Integer reactionCount
        +Integer replyCount
        +DateTime createdAt
        +DateTime updatedAt
        +DateTime deletedAt
        +edit(newBody) void
        +softDelete() void
    }

    class Reaction {
        +UUID id
        +UUID targetId
        +ReactionTargetType targetType
        +UUID userId
        +ReactionType reactionType
        +DateTime createdAt
        +change(newType) void
        +remove() void
    }

    class Share {
        +UUID id
        +UUID originalPostId
        +UUID sharedByUserId
        +String commentary
        +PostVisibility visibility
        +DateTime createdAt
    }

    class Repost {
        +UUID id
        +UUID originalPostId
        +UUID repostedByUserId
        +DateTime createdAt
        +undo() void
    }

    Post "1" *-- "0..n" PostMedia : contains
    Post "1" *-- "0..n" PostTag : tagged with
    Post "1" *-- "0..n" Mention : mentions
    Post "1" o-- "0..1" Poll : may have
    Poll "1" *-- "2..n" PollOption : options
    Poll "1" *-- "0..n" PollVote : votes
    Post "1" o-- "0..n" Comment : has
    Comment "1" o-- "0..n" Comment : replies
    Post "1" o-- "0..n" Reaction : receives
    Comment "1" o-- "0..n" Reaction : receives
    Post "1" o-- "0..n" Share : shared as
    Post "1" o-- "0..n" Repost : reposted as
    Story "1" *-- "0..n" StoryView : viewed by
```

---

## 4. Feed & Notification Domain

Captures the structures that power personalised feed delivery and in-app/push notification dispatch.

```mermaid
classDiagram
    class Feed {
        +UUID id
        +UUID userId
        +FeedType feedType
        +DateTime lastRefreshedAt
        +String cursorToken
        +refresh() void
        +paginate(cursor, limit) FeedPage
        +invalidate() void
    }

    class FeedItem {
        +UUID id
        +UUID feedId
        +UUID sourceEntityId
        +FeedItemType itemType
        +Float rankingScore
        +Integer position
        +Boolean isSeen
        +Boolean isClicked
        +DateTime insertedAt
        +DateTime expiresAt
        +markSeen() void
        +markClicked() void
    }

    class FeedRanking {
        +UUID id
        +UUID userId
        +String modelVersion
        +Map~String,Float~ featureWeights
        +DateTime trainedAt
        +DateTime appliedAt
        +score(item) Float
        +rerank(items) List~FeedItem~
        +refreshModel() void
    }

    class Notification {
        +UUID id
        +UUID recipientId
        +UUID actorId
        +NotificationType type
        +UUID referenceId
        +ReferenceType referenceType
        +String title
        +String body
        +String deepLinkUrl
        +Boolean isRead
        +Boolean isSent
        +NotificationChannel channel
        +DateTime createdAt
        +DateTime readAt
        +DateTime sentAt
        +markRead() void
        +send() void
        +dismiss() void
    }

    class NotificationPreference {
        +UUID id
        +UUID userId
        +NotificationType notificationType
        +Boolean inApp
        +Boolean push
        +Boolean email
        +Boolean sms
        +QuietHours quietHours
        +DateTime updatedAt
        +update(channel, enabled) void
        +setQuietHours(start, end) void
    }

    class NotificationBatch {
        +UUID id
        +UUID userId
        +Integer count
        +NotificationType aggregatedType
        +String summary
        +DateTime windowStart
        +DateTime windowEnd
        +List~UUID~ notificationIds
        +collapse() void
        +dispatch() void
    }

    Feed "1" *-- "0..n" FeedItem : contains
    Feed "1" --> "1" FeedRanking : scored by
    Notification "n" --> "1" NotificationPreference : filtered by
    NotificationBatch "1" *-- "1..n" Notification : groups
```

---

## 5. Messaging Domain

Models direct messages and group chats with end-to-end encryption metadata.

```mermaid
classDiagram
    class Conversation {
        +UUID id
        +ConversationType type
        +String title
        +String avatarUrl
        +UUID createdById
        +DateTime createdAt
        +DateTime updatedAt
        +DateTime lastMessageAt
        +addParticipant(userId) void
        +removeParticipant(userId) void
        +archive() void
        +mute(userId, until) void
    }

    class ConversationParticipant {
        +UUID id
        +UUID conversationId
        +UUID userId
        +ParticipantRole role
        +Boolean isMuted
        +DateTime mutedUntil
        +Boolean isArchived
        +DateTime joinedAt
        +DateTime leftAt
        +DateTime lastReadAt
        +Integer unreadCount
        +markRead(messageId) void
        +leave() void
        +promote() void
    }

    class DirectMessage {
        +UUID id
        +UUID conversationId
        +UUID senderId
        +MessageContentType contentType
        +String encryptedBody
        +String encryptionKeyId
        +Boolean isEdited
        +Boolean isDeleted
        +UUID replyToMessageId
        +DateTime sentAt
        +DateTime deliveredAt
        +DateTime readAt
        +List~Reaction~ reactions
        +edit(newContent) void
        +softDelete() void
        +addReaction(type) void
    }

    class MessageMedia {
        +UUID id
        +UUID messageId
        +MediaType mediaType
        +String encryptedUrl
        +String decryptionKey
        +Long fileSizeBytes
        +String mimeType
        +DateTime uploadedAt
        +decrypt() Blob
    }

    class GroupChat {
        +UUID id
        +UUID conversationId
        +String name
        +String description
        +String avatarUrl
        +Integer maxMembers
        +Boolean isPublic
        +UUID inviteLinkToken
        +DateTime createdAt
        +DateTime updatedAt
        +updateSettings(settings) void
        +generateInviteLink() String
        +revokeInviteLink() void
    }

    class GroupChatMember {
        +UUID id
        +UUID groupChatId
        +UUID userId
        +GroupRole role
        +DateTime joinedAt
        +DateTime bannedAt
        +String banReason
        +kick() void
        +ban(reason) void
        +promoteToAdmin() void
        +demote() void
    }

    Conversation "1" *-- "2..n" ConversationParticipant : has
    Conversation "1" *-- "0..n" DirectMessage : contains
    DirectMessage "1" o-- "0..n" MessageMedia : attaches
    Conversation "1" o-- "0..1" GroupChat : extended by
    GroupChat "1" *-- "2..n" GroupChatMember : members
```

---

## 6. Moderation & Community Domain

Captures content moderation workflows, community spaces, and membership governance.

```mermaid
classDiagram
    class ContentReport {
        +UUID id
        +UUID reporterId
        +UUID targetId
        +ReportTargetType targetType
        +ReportReason reason
        +String additionalContext
        +ReportStatus status
        +UUID assignedModeratorId
        +DateTime createdAt
        +DateTime reviewedAt
        +DateTime resolvedAt
        +assign(moderatorId) void
        +resolve(action) void
        +escalate() void
    }

    class ModerationQueue {
        +UUID id
        +UUID reportId
        +ModerationPriority priority
        +QueueStatus status
        +UUID claimedByModeratorId
        +DateTime queuedAt
        +DateTime claimedAt
        +DateTime completedAt
        +claim(moderatorId) void
        +release() void
        +complete(decision) void
        +escalatePriority() void
    }

    class ModerationDecision {
        +UUID id
        +UUID queueItemId
        +UUID moderatorId
        +DecisionType decision
        +String justification
        +Boolean notifyReporter
        +Boolean notifyTarget
        +DateTime decidedAt
        +apply() void
        +reverse() void
    }

    class BanRecord {
        +UUID id
        +UUID userId
        +BanScope scope
        +UUID scopeId
        +String reason
        +UUID issuedByModeratorId
        +DateTime issuedAt
        +DateTime expiresAt
        +Boolean isPermanent
        +Boolean isAppealed
        +lift() void
        +extend(newExpiry) void
        +markAppealed() void
    }

    class Community {
        +UUID id
        +String name
        +String slug
        +String description
        +String avatarUrl
        +String bannerUrl
        +CommunityVisibility visibility
        +JoinPolicy joinPolicy
        +Integer memberCount
        +Integer postCount
        +UUID createdById
        +DateTime createdAt
        +DateTime updatedAt
        +updateSettings(settings) void
        +ban(userId, reason) BanRecord
        +addModerator(userId) void
    }

    class CommunityMember {
        +UUID id
        +UUID communityId
        +UUID userId
        +CommunityRole role
        +MembershipStatus status
        +DateTime joinedAt
        +DateTime bannedAt
        +promote(role) void
        +demote() void
        +remove() void
    }

    class CommunityRule {
        +UUID id
        +UUID communityId
        +Integer ruleNumber
        +String title
        +String description
        +DateTime createdAt
        +update(title, description) void
        +delete() void
    }

    class CommunityPost {
        +UUID id
        +UUID communityId
        +UUID postId
        +UUID submittedById
        +CommunityPostStatus status
        +Boolean isPinned
        +UUID approvedByModeratorId
        +DateTime submittedAt
        +DateTime approvedAt
        +pin() void
        +approve() void
        +reject(reason) void
    }

    ContentReport "1" *-- "1" ModerationQueue : queued as
    ModerationQueue "1" *-- "0..1" ModerationDecision : results in
    Community "1" *-- "0..n" CommunityMember : has
    Community "1" *-- "1..n" CommunityRule : governed by
    Community "1" *-- "0..n" CommunityPost : contains
    Community "1" o-- "0..n" BanRecord : issues
```

---

## 7. Advertising Domain

Models the full ad lifecycle from campaign creation through impression and click tracking.

```mermaid
classDiagram
    class Advertiser {
        +UUID id
        +UUID userId
        +String businessName
        +String businessUrl
        +AdvertiserStatus status
        +String billingEmail
        +String taxId
        +Decimal creditBalance
        +DateTime createdAt
        +DateTime verifiedAt
        +verify() void
        +suspend() void
        +topUpCredit(amount) void
    }

    class AdCampaign {
        +UUID id
        +UUID advertiserId
        +String name
        +CampaignObjective objective
        +CampaignStatus status
        +Decimal totalBudget
        +Decimal dailyBudget
        +Decimal spentToDate
        +BiddingStrategy biddingStrategy
        +Decimal bidAmount
        +TargetingSpec targetingSpec
        +DateTime startDate
        +DateTime endDate
        +DateTime createdAt
        +DateTime updatedAt
        +submit() void
        +pause() void
        +resume() void
        +complete() void
        +getRemainingBudget() Decimal
    }

    class AdCreative {
        +UUID id
        +UUID campaignId
        +CreativeFormat format
        +String headline
        +String body
        +String ctaText
        +String destinationUrl
        +String mediaUrl
        +String thumbnailUrl
        +CreativeStatus approvalStatus
        +String rejectionReason
        +DateTime submittedAt
        +DateTime reviewedAt
        +submit() void
        +approve() void
        +reject(reason) void
    }

    class AdPlacement {
        +UUID id
        +UUID campaignId
        +UUID creativeId
        +PlacementType placementType
        +Integer frequencyCap
        +Integer frequencyWindowHours
        +Boolean isActive
        +DateTime createdAt
        +activate() void
        +deactivate() void
    }

    class AdImpression {
        +UUID id
        +UUID placementId
        +UUID viewerUserId
        +String sessionId
        +String ipAddress
        +String userAgent
        +PlacementContext context
        +Boolean isViewable
        +DateTime impressedAt
        +recordViewability(viewable) void
    }

    class AdClick {
        +UUID id
        +UUID impressionId
        +UUID placementId
        +UUID viewerUserId
        +String destinationUrl
        +Decimal costPerClick
        +DateTime clickedAt
        +isConversion() Boolean
    }

    class AdBillingEvent {
        +UUID id
        +UUID campaignId
        +BillingEventType eventType
        +Decimal amount
        +Decimal runningBalance
        +UUID relatedEntityId
        +DateTime occurredAt
    }

    Advertiser "1" *-- "0..n" AdCampaign : runs
    AdCampaign "1" *-- "1..n" AdCreative : uses
    AdCampaign "1" *-- "1..n" AdPlacement : placed via
    AdPlacement "1" o-- "0..n" AdImpression : generates
    AdImpression "1" o-- "0..1" AdClick : may produce
    AdCampaign "1" o-- "0..n" AdBillingEvent : billed by
```
