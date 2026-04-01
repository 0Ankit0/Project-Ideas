# Sequence Diagrams — Social Networking Platform

## 1. Overview

This document details the runtime interaction sequences for the five most architecturally significant flows in the Social Networking Platform. Each sequence diagram shows the precise message exchanges between clients, API gateway, microservices, external providers, and data stores. These diagrams drive API contract design, SLA budgeting, and integration testing.

---

## 2. Post Creation with Media Upload

A user composes a post that includes one or more media files. The flow covers pre-signed URL generation, direct-to-object-storage upload, async media processing, and fan-out to followers' feeds.

```mermaid
sequenceDiagram
    actor User
    participant App as Mobile / Web App
    participant GW as API Gateway
    participant Auth as Auth Service
    participant PS as Post Service
    participant MS as Media Service
    participant S3 as Object Storage (S3)
    participant MQ as Message Queue (Kafka)
    participant FO as Fan-Out Worker
    participant FC as Feed Cache (Redis)
    participant DB as Post DB (PostgreSQL)
    participant CDN as CDN (CloudFront)

    User->>App: Compose post with 2 images + caption
    App->>GW: POST /v1/posts/media/upload-intent\n(Authorization: Bearer <token>, fileCount: 2, mimeTypes)
    GW->>Auth: Validate JWT
    Auth-->>GW: 200 OK — userId, scopes
    GW->>MS: POST /internal/media/presigned-urls\n(userId, files[{name, mimeType, size}])
    MS->>S3: GeneratePresignedPutUrl × 2 (15-min TTL)
    S3-->>MS: presignedUrls[url1, url2]
    MS-->>GW: 200 OK — {uploadId, urls[{mediaId, presignedUrl}]}
    GW-->>App: 200 OK — uploadIntent

    par Upload image 1
        App->>S3: PUT presignedUrl1 (binary image data)
        S3-->>App: 200 OK (ETag)
    and Upload image 2
        App->>S3: PUT presignedUrl2 (binary image data)
        S3-->>App: 200 OK (ETag)
    end

    App->>GW: POST /v1/posts\n{body, visibility, mediaIds[mediaId1, mediaId2], tags[], mentions[]}
    GW->>Auth: Validate JWT (cached)
    Auth-->>GW: 200 OK
    GW->>PS: POST /internal/posts (authorId, payload)
    PS->>DB: INSERT posts (id, authorId, body, status=PROCESSING)
    DB-->>PS: post.id
    PS->>MS: POST /internal/media/attach\n(postId, mediaIds[mediaId1, mediaId2])
    MS->>DB: UPDATE post_media SET postId, status=PENDING_PROCESSING
    MS->>MQ: Publish media.process event\n{postId, mediaId, s3Key, operations:[resize, transcode, thumbnail]}
    MQ-->>MS: ack
    MS-->>PS: 202 Accepted — media processing enqueued
    PS->>MQ: Publish post.created event\n{postId, authorId, visibility, createdAt}
    MQ-->>PS: ack
    PS-->>GW: 201 Created — {postId, status: PROCESSING}
    GW-->>App: 201 Created — post draft

    Note over MS,CDN: Async: Media Processing Pipeline
    MQ->>MS: Consume media.process event
    MS->>S3: GetObject (original file)
    S3-->>MS: binary stream
    MS->>MS: Resize to [320w, 640w, 1080w]\nGenerate WEBP variants\nCreate thumbnail
    MS->>S3: PutObject × 4 variants + thumbnail
    S3-->>MS: ETags
    MS->>CDN: Invalidate origin cache for mediaId
    MS->>DB: UPDATE post_media SET processedUrls, thumbnailUrl, status=READY
    MS->>MQ: Publish media.ready event {postId, allMediaReady: true}

    Note over PS,FC: Async: Post Publishing & Fan-Out
    MQ->>PS: Consume media.ready event
    PS->>DB: UPDATE posts SET status=PUBLISHED, publishedAt=NOW()
    PS->>MQ: Publish post.published event {postId, authorId, followerCount}
    MQ->>FO: Consume post.published (fan-out consumer group)
    FO->>DB: SELECT follower_ids WHERE followee=authorId LIMIT 10000
    loop Per follower batch (1000 at a time)
        FO->>FC: ZADD feed:{followerId} score=timestamp postId
        FO->>FC: LTRIM feed:{followerId} 0 499
    end
    FO->>MQ: Publish notification.trigger\n{type: NEW_POST, actorId, recipientIds}
```

---

## 3. Feed Fetch with ML Ranking

A user opens the app and requests their personalised home feed. The feed service retrieves candidate posts, applies machine-learning ranking, hydrates entities, and returns a paginated response.

```mermaid
sequenceDiagram
    actor User
    participant App as Mobile App
    participant GW as API Gateway
    participant Auth as Auth Service
    participant FS as Feed Service
    participant FC as Feed Cache (Redis)
    participant RS as Ranking Service (ML)
    participant PS as Post Service
    participant US as User Service
    participant ES as Engagement Store (Redis)
    participant FS_DB as Feed DB (Cassandra)

    User->>App: Open home feed (pull-to-refresh)
    App->>GW: GET /v1/feed?type=home&limit=20&cursor=null\n(Authorization: Bearer <token>)
    GW->>Auth: Validate JWT (cache hit)
    Auth-->>GW: 200 OK — userId
    GW->>FS: GET /internal/feed/{userId}?limit=20&cursor=null

    FS->>FC: ZREVRANGE feed:{userId} 0 99 WITHSCORES
    alt Cache HIT (>= 20 candidates)
        FC-->>FS: candidatePostIds[100] with raw timestamps
    else Cache MISS
        FS->>FS_DB: SELECT post_id, score FROM feed_items\nWHERE user_id=userId ORDER BY inserted_at DESC LIMIT 200
        FS_DB-->>FS: candidateRows[200]
        FS->>FC: ZADD feed:{userId} score postId (pipeline, TTL 10 min)
        FC-->>FS: OK
    end

    FS->>RS: POST /internal/rank\n{userId, candidatePostIds[100], contextSignals:{deviceType, timeOfDay, sessionLength}}
    RS->>ES: HMGET engagement:{userId} [recentLikes, recentShares, dwellTimes]
    ES-->>RS: engagementVector
    RS->>RS: Load user affinity model (cached)\nScore each candidate:\n  base_score = freshness × 0.3\n  engagement_score = predicted_ctr × 0.5\n  diversity_score = topic_spread × 0.2\nSort descending, apply diversity re-rank
    RS-->>FS: rankedPostIds[100] with scores

    FS->>PS: POST /internal/posts/batch\n{postIds: rankedPostIds[0..24]}
    PS-->>FS: posts[25] (full post objects)

    FS->>US: POST /internal/users/batch\n{userIds: [distinct authorIds from posts]}
    US-->>FS: users[] (id, username, avatarUrl, isVerified)

    FS->>ES: HMGET post:engagement:{postId} [likes, comments, shares] (pipeline × 25)
    ES-->>FS: engagementCounts[]

    FS->>FS: Merge posts + authors + engagement\nAttach isSeen flags\nBuild nextCursor token (encryptedOffset)
    FS-->>GW: 200 OK — {items[20], nextCursor, hasMore: true}
    GW-->>App: 200 OK — FeedResponse

    App->>App: Render feed items
    App-->>User: Display personalised feed

    Note over App,ES: Async impression tracking (fire-and-forget)
    App->>GW: POST /v1/feed/impressions\n{postIds[], sessionId, viewport}
    GW->>ES: HINCRBY post:impressions:{postId} count 1 (pipeline)
    ES-->>GW: OK
    GW-->>App: 204 No Content
```

---

## 4. Story View with Expiry Check

A user taps on a story. The platform validates that the story has not expired, records the view deduplicated, and delivers the media URL via CDN with a signed token.

```mermaid
sequenceDiagram
    actor Viewer
    participant App as Mobile App
    participant GW as API Gateway
    participant Auth as Auth Service
    participant StS as Story Service
    participant RC as Story Cache (Redis)
    participant DB as Story DB (PostgreSQL)
    participant CDN as CDN (CloudFront)
    participant NS as Notification Service
    participant MQ as Message Queue (Kafka)

    Viewer->>App: Tap on story thumbnail (storyId)
    App->>GW: GET /v1/stories/{storyId}\n(Authorization: Bearer <token>)
    GW->>Auth: Validate JWT
    Auth-->>GW: 200 OK — viewerId

    GW->>StS: GET /internal/stories/{storyId} (viewerId)

    StS->>RC: GET story:{storyId}
    alt Cache HIT
        RC-->>StS: story JSON (id, authorId, expiresAt, mediaKey, status)
    else Cache MISS
        StS->>DB: SELECT * FROM stories WHERE id=storyId
        DB-->>StS: storyRow
        StS->>RC: SET story:{storyId} JSON EX 300
        RC-->>StS: OK
    end

    alt Story is EXPIRED or status=REMOVED
        StS-->>GW: 410 Gone — {code: STORY_EXPIRED}
        GW-->>App: 410 Gone
        App-->>Viewer: Show "Story no longer available"
    else Story is ACTIVE and not expired
        StS->>RC: SISMEMBER story:viewers:{storyId} viewerId
        alt Viewer has already seen this story
            RC-->>StS: 1 (already seen)
        else First view
            RC-->>StS: 0 (new view)
            StS->>RC: SADD story:viewers:{storyId} viewerId (EX 86400)
            StS->>RC: INCR story:viewcount:{storyId}
            StS->>MQ: Publish story.viewed\n{storyId, viewerId, authorId, viewedAt}
            MQ-->>StS: ack
        end

        StS->>CDN: GenerateSignedUrl(mediaKey, TTL=300s, viewerId)
        CDN-->>StS: signedMediaUrl

        StS-->>GW: 200 OK — {storyId, signedMediaUrl, expiresAt, viewCount, hasViewedBefore}
        GW-->>App: 200 OK — StoryViewResponse
        App->>CDN: GET signedMediaUrl (stream media)
        CDN-->>App: 200 OK — media stream
        App-->>Viewer: Play story

        Note over MQ,NS: Async: Notify author of new view
        MQ->>NS: Consume story.viewed event
        NS->>DB: SELECT notification_prefs WHERE userId=authorId AND type=STORY_VIEW
        DB-->>NS: prefs (inApp: true, push: false)
        NS->>DB: INSERT notifications (recipientId=authorId, type=STORY_VIEW, referenceId=storyId)
        NS-->>Viewer: (no push — pref disabled)
    end

    Note over StS,DB: Async: Story expiry flush (every 5 min cron)
    loop Expiry sweep
        StS->>DB: UPDATE stories SET status=EXPIRED\nWHERE expiresAt < NOW() AND status=ACTIVE
        DB-->>StS: rowsUpdated
        StS->>RC: DEL story:{storyId} (for each expired)
    end
```

---

## 5. Content Report & Moderation Queue

A user reports a post. The platform creates a report record, scores it for urgency using an AI screener, inserts it into the moderation queue at the appropriate priority, and dispatches a resolution notification once a moderator acts.

```mermaid
sequenceDiagram
    actor Reporter
    participant App as Mobile App
    participant GW as API Gateway
    participant Auth as Auth Service
    participant RptS as Report Service
    participant AI as AI Content Screener
    participant MQ as Message Queue (Kafka)
    participant ModW as Moderation Worker
    participant ModDB as Moderation DB (PostgreSQL)
    participant NS as Notification Service
    actor Moderator
    participant ModDash as Moderator Dashboard

    Reporter->>App: Tap "Report Post" → select reason: HATE_SPEECH\n+ optional additional context
    App->>GW: POST /v1/reports\n{targetId: postId, targetType: POST, reason: HATE_SPEECH, context: "..."}
    GW->>Auth: Validate JWT
    Auth-->>GW: 200 OK — reporterId

    GW->>RptS: POST /internal/reports (reporterId, payload)
    RptS->>ModDB: CHECK existing open report by same reporter on same target
    ModDB-->>RptS: no duplicate found
    RptS->>ModDB: INSERT content_reports\n(id, reporterId, targetId, targetType, reason, status=SUBMITTED)
    ModDB-->>RptS: reportId

    RptS->>AI: POST /internal/screen\n{targetId, targetType, reason, contentSnapshot}
    AI->>AI: Run BERT-based toxicity classifier\nExtract severity score (0.0–1.0)\nClassify subcategory (explicit, violence, harassment)
    AI-->>RptS: {severityScore: 0.87, subcategory: HARASSMENT, recommendedPriority: HIGH}

    RptS->>ModDB: INSERT moderation_queue\n(reportId, priority=HIGH, status=QUEUED, queuedAt=NOW())
    RptS->>ModDB: UPDATE content_reports SET status=UNDER_REVIEW, assignedPriority=HIGH
    RptS->>MQ: Publish report.queued {reportId, priority=HIGH, targetType}
    MQ-->>RptS: ack
    RptS-->>GW: 201 Created — {reportId, status: UNDER_REVIEW}
    GW-->>App: 201 Created
    App-->>Reporter: "Thank you — your report is under review"

    Note over MQ,ModDash: Async: Moderator reviews queue
    MQ->>ModW: Consume report.queued (moderation-consumer-group)
    ModW->>ModDB: UPDATE moderation_queue SET status=READY for priority routing
    Moderator->>ModDash: Open HIGH priority queue
    ModDash->>ModW: GET /internal/moderation/queue?priority=HIGH&limit=10
    ModW->>ModDB: SELECT * FROM moderation_queue\nWHERE priority=HIGH AND status=QUEUED\nORDER BY queuedAt ASC LIMIT 10
    ModDB-->>ModW: queueItems[]
    ModW-->>ModDash: queueItems with content snapshots

    Moderator->>ModDash: Claim item (queueItemId) + review content
    ModDash->>ModW: POST /internal/moderation/queue/{id}/claim
    ModW->>ModDB: UPDATE moderation_queue SET status=IN_REVIEW, claimedByModeratorId=moderatorId, claimedAt=NOW()

    Moderator->>ModDash: Decision: REMOVE_CONTENT + 7-day suspension for author
    ModDash->>ModW: POST /internal/moderation/decisions\n{queueItemId, decision: REMOVE_CONTENT, suspension: {days:7}, justification}
    ModW->>ModDB: INSERT moderation_decisions (queueItemId, moderatorId, decision, justification)
    ModW->>ModDB: UPDATE posts SET status=REMOVED, removedAt=NOW() WHERE id=targetId
    ModW->>ModDB: INSERT ban_records (userId=authorId, scope=PLATFORM, expiresAt=+7days, reason)
    ModW->>ModDB: UPDATE content_reports SET status=ACTION_TAKEN, resolvedAt=NOW()
    ModW->>ModDB: UPDATE moderation_queue SET status=COMPLETED, completedAt=NOW()
    ModW->>MQ: Publish moderation.actioned {reportId, targetId, decision, actorId=authorId}
    MQ->>NS: Consume moderation.actioned
    NS->>App: Push notification to Reporter: "We've taken action on your report"
    NS->>App: Push notification to Author: "Your post was removed — Community Standards violation"
```

---

## 6. Ad Serving & Impression Tracking

The feed service requests an ad to interleave into a user's feed. The ad server selects the best-matching creative using targeting and auction logic, logs the impression, and asynchronously records the billing event.

```mermaid
sequenceDiagram
    participant FS as Feed Service
    participant AdS as Ad Server
    participant AuctionE as Auction Engine
    participant TgtDB as Targeting DB (Elasticsearch)
    participant CacheAd as Ad Cache (Redis)
    participant AdDB as Ad DB (PostgreSQL)
    participant BillingW as Billing Worker
    participant BillDB as Billing DB (PostgreSQL)
    participant CDN as CDN (CloudFront)
    actor User
    participant App as Mobile App

    FS->>AdS: POST /internal/ads/request\n{userId, sessionId, placement: IN_FEED_POSITION_5,\n contextSignals:{deviceType, locale, feedTopics[]}}

    AdS->>CacheAd: GET user:targeting:{userId}
    alt Cache HIT
        CacheAd-->>AdS: targetingProfile (age, interests, location)
    else Cache MISS
        AdS->>TgtDB: GET /targeting/profile/{userId}
        TgtDB-->>AdS: targetingProfile
        AdS->>CacheAd: SET user:targeting:{userId} EX 3600
    end

    AdS->>TgtDB: POST /ads/eligible\n{targetingProfile, placement, locale, excludedAdIds[recentlyServed]}
    TgtDB-->>AdS: eligiblePlacements[] (campaignId, creativeId, bidAmount, frequencyOk)

    AdS->>AuctionE: POST /auction/run\n{eligiblePlacements[], contextSignals}
    AuctionE->>AuctionE: For each candidate:\n  qualityScore = predicted_ctr × relevance_score\n  effectiveCPM = bidAmount × qualityScore\nSelect winner (highest effectiveCPM)\nCalculate second-price clearing
    AuctionE-->>AdS: {winner:{placementId, creativeId, clearingPrice}, runnerUps[]}

    AdS->>CacheAd: INCR freq:{userId}:{campaignId}:{window} (frequency cap check, TTL=window)
    CacheAd-->>AdS: currentFreq = 3 (< cap of 5, proceed)

    AdS->>AdDB: SELECT creative WHERE id=creativeId
    AdDB-->>AdS: creative {headline, body, ctaText, mediaKey, destinationUrl}

    AdS->>CDN: GenerateSignedUrl(mediaKey, TTL=600)
    CDN-->>AdS: signedMediaUrl

    AdS-->>FS: 200 OK — {adUnit:{impressionId, creative, signedMediaUrl, beaconUrl}}

    FS->>FS: Interleave adUnit at position 5 in feed
    FS-->>App: FeedResponse with ad at position 5
    App-->>User: Render ad creative in feed

    Note over App,BillDB: Async: Impression & viewability tracking
    App->>AdS: POST /v1/ads/impression\n{impressionId, isViewable: true, viewDurationMs: 1200}
    AdS->>AdDB: INSERT ad_impressions\n(id, placementId, viewerUserId, sessionId, isViewable, impressedAt)
    AdDB-->>AdS: ok
    AdS->>BillingW: Publish billing.impression\n{impressionId, campaignId, advertiserId, clearingPrice}

    BillingW->>BillDB: INSERT ad_billing_events\n(campaignId, eventType=IMPRESSION, amount=clearingPrice)
    BillingW->>BillDB: UPDATE ad_campaigns SET spent_to_date = spent_to_date + clearingPrice
    BillDB-->>BillingW: ok

    Note over App,AdDB: Optional: Click tracking
    User->>App: Tap ad CTA
    App->>AdS: POST /v1/ads/click\n{impressionId}
    AdS->>AdDB: INSERT ad_clicks (impressionId, placementId, viewerUserId, clickedAt, costPerClick)
    AdS->>BillingW: Publish billing.click {impressionId, campaignId, costPerClick}
    AdS-->>App: 200 OK — {redirectUrl: destinationUrl}
    App-->>User: Open advertiser URL in browser
```
