# Activity Diagrams — Social Networking Platform

## 1. Overview

This document presents detailed activity diagrams for three core platform processes: User Registration & Onboarding, Post Creation & Publishing Pipeline, and Feed Generation. Each diagram captures every decision point, parallel activity, and exception path using Mermaid flowchart notation.

Activity diagrams complement the use-case descriptions by focusing on *how* a process executes step-by-step, including system-side automation, background jobs, and branching logic. They are the primary reference for backend engineers implementing the respective workflows and for QA engineers designing test scenarios.

---

## 2. Activity Diagram: User Registration & Onboarding

This activity covers the full lifecycle from a guest's first interaction with the sign-up surface through to their personalised feed being populated. It includes both the standard email/phone registration path and the OAuth fast path, as well as the age-gate check, verification, and the multi-step onboarding wizard.

```mermaid
flowchart TD
    A([Guest Opens Registration Page]) --> B{Choose Sign-Up Method}

    B --> |Email / Phone| C[Enter Email or Phone + Password]
    B --> |OAuth: Google or Apple| OA[Redirect to OAuth Provider Consent Screen]

    OA --> OB{OAuth Consent Granted?}
    OB --> |No| OC([Guest Cancels — End])
    OB --> |Yes| OD[Exchange Auth Code for ID Token]
    OD --> OE[Extract Verified Email & Name from Token]
    OE --> F

    C --> D[Client-Side Validation\nPassword strength, email format]
    D --> |Validation Fails| C
    D --> |Validation Passes| E[Submit Registration Request]

    E --> F{Email Already Registered?}
    F --> |Yes| G[Show Error: Account Exists\nOffer Login or Password Reset]
    G --> A
    F --> |No| H[Age Gate Check\nDate of Birth Entry]

    H --> I{Age ≥ 13 and ≥ 16 in GDPR Region?}
    I --> |No| J[Block Registration\nDisplay Age Restriction Message]
    J --> ([End])
    I --> |Yes| K[Create Pending UserCredential Record]

    K --> L[Send Verification Code\nEmail OTP or SMS OTP]
    L --> M[User Enters Verification Code]
    M --> N{Code Valid and Not Expired?}
    N --> |Expired| O[Offer Resend Code — max 3 attempts]
    O --> L
    N --> |Invalid Code| P[Show Error — Attempts Remaining Counter]
    P --> M
    N --> |Valid| Q

    %% OAuth path skips verification — jumps directly here
    Q[Mark Credential as Verified\nCreate User + UserProfile Records\nApply Default Privacy Settings]

    Q --> R[Log In User — Issue JWT + Refresh Token]
    R --> S[Show Onboarding Wizard Step 1:\nUpload Profile Avatar]

    S --> T{Avatar Uploaded?}
    T --> |Skip| U
    T --> |Yes| U[Onboarding Step 2:\nEnter Display Name and Bio]

    U --> V[Onboarding Step 3:\nSelect Up to 5 Interest Categories]
    V --> W[Onboarding Step 4:\nFollow 3 Suggested Accounts]

    W --> X{Onboarding Completed?}
    X --> |User Skipped Steps| Y[Mark Onboarding Incomplete\nSchedule 24h Nudge Notification]
    X --> |Completed| Z[Mark Onboarding Complete]

    Y --> AA
    Z --> AA[Trigger Feed Bootstrap\nBackfill 20 Recent Posts from Followed Accounts]

    AA --> AB[Send Welcome Email via Email Delivery Service]
    AB --> AC([Redirect to Personalised Feed — End])

    style A fill:#4CAF50,color:#fff
    style AC fill:#4CAF50,color:#fff
    style J fill:#f44336,color:#fff
    style OC fill:#f44336,color:#fff
```

---

## 3. Activity Diagram: Post Creation & Publishing Pipeline

This activity covers the end-to-end journey of a post from the moment the user opens the composer to the point where the content is live in followers' feeds. It includes media upload, AI content screening with human escalation, fan-out distribution, and notification dispatch. Scheduled posts and community-targeted posts are handled as alternate branches.

```mermaid
flowchart TD
    START([User Opens Post Composer]) --> PT{Select Post Type}

    PT --> |Text Only| TXT[Enter Post Body\nmax 2000 characters]
    PT --> |Photo / Video| MEDIA[Attach Media Files]
    PT --> |Poll| POLL[Enter Poll Question + 2–4 Options\nSet Poll Duration]
    PT --> |Reel| REEL[Upload Short Video\nmax 60 seconds]

    MEDIA --> MV{Media Validation}
    MV --> |File Too Large or Wrong Format| MVF[Show Validation Error\nPrompt User to Retry]
    MVF --> MEDIA
    MV --> |Valid| MU[Upload Media to Pre-signed S3 URL]
    MU --> MR{Upload Successful?}
    MR --> |Fails after 3 Retries| MFail[Save Draft Locally\nShow Upload Error Toast]
    MFail --> ([End — Draft Saved])
    MR --> |Success| MT[Generate Thumbnails\nTranscode Video via Media Service]
    MT --> TXT

    REEL --> REELV{Video ≤ 60s and Supported Format?}
    REELV --> |No| REELF[Show Format or Duration Error]
    REELF --> REEL
    REELV --> |Yes| MU

    POLL --> TXT
    TXT --> TAG[Optionally Add @Mentions and Hashtags]

    TAG --> AUD[Select Audience:\nPublic, Followers, Friends, Close Friends, Only Me]
    AUD --> SCHED{Post Now or Schedule?}

    SCHED --> |Schedule — ContentCreator only| SCHEDTIME[Select Future Date and Time\nmax 30 days ahead]
    SCHEDTIME --> SCHEDSAVE[Save Post in SCHEDULED State]
    SCHEDSAVE --> ([End — Post Scheduled])

    SCHED --> |Post Now| TARGET{Target: Profile or Community?}

    TARGET --> |Community| COMMCHECK{Community Requires Approval?}
    COMMCHECK --> |Yes| COMMPEND[Save Post in COMMUNITY_PENDING State\nNotify Community Moderator]
    COMMPEND --> COMMMOD{Moderator Decision}
    COMMMOD --> |Reject| COMMREJ[Notify Author — Post Rejected\nPost Deleted]
    COMMREJ --> ([End])
    COMMMOD --> |Approve| POSTPEND
    COMMCHECK --> |No| POSTPEND

    TARGET --> |Own Profile| POSTPEND

    POSTPEND[Create Post Record in PENDING_REVIEW State\nPersist Mentions, Hashtags, PostMedia]

    POSTPEND --> AISUB[Submit to AI Moderation Service]
    AISUB --> AIEVAL{AI Verdict}

    AIEVAL --> |Confidence ≥ 0.98 — CSAM or Terrorism| AUTOREMOVE[Auto-Remove Post\nTrigger Law Enforcement Reporting\nCreate ModerationQueue Entry for Confirmation]
    AUTOREMOVE --> NOTIFYREJECT[Notify Author — Policy Violation\nOffer Appeal Link]
    NOTIFYREJECT --> ([End — Auto-Removed])

    AIEVAL --> |Confidence ≥ 0.92 — High Risk| ESCALATE[Transition Post to PENDING_REVIEW\nEscalate to Front of ModerationQueue]
    ESCALATE --> HUMANREVIEW{Human Moderator Decision}
    HUMANREVIEW --> |Remove| REMOVED[Transition to REJECTED\nNotify Author\nPurge CDN if Media Exists]
    REMOVED --> ([End — Rejected])
    HUMANREVIEW --> |Approve| PUBLISH

    AIEVAL --> |Low Confidence — Auto-Pass| PUBLISH

    PUBLISH[Transition Post to PUBLISHED State\nUpdate Hashtag Trend Counters\nUpdate Author Post Count]

    PUBLISH --> FANOUT[Trigger Feed Fan-Out Job\nInsert FeedItem for Each Follower\nApply Privacy Audience Filter]

    FANOUT --> PARALLEL_NOTIF
    FANOUT --> SEARCH_INDEX

    PARALLEL_NOTIF[Dispatch Mention Notifications\nto All Tagged Users]
    SEARCH_INDEX[Index Post in Search and Discovery Service]

    PARALLEL_NOTIF --> DONE
    SEARCH_INDEX --> DONE

    DONE([Post Live in Followers' Feeds — End])

    style START fill:#4CAF50,color:#fff
    style DONE fill:#4CAF50,color:#fff
    style AUTOREMOVE fill:#f44336,color:#fff
    style REMOVED fill:#f44336,color:#fff
    style MFail fill:#FF9800,color:#fff
```

---

## 4. Activity Diagram: Feed Generation

This activity describes how the personalised feed is constructed and delivered to a user on app open and on scroll-based pagination. It covers cache consultation, feed assembly from the database, real-time filtering (blocks, privacy, expiry), ML ranking, ad injection, and continuous re-ranking based on engagement feedback. The chronological "Latest" mode bypass and the empty-state discovery feed are included as alternate branches.

```mermaid
flowchart TD
    START([User Opens App Home Screen]) --> MODE{Feed Mode Selected?}

    MODE --> |Default — Ranked| CACHECHECK
    MODE --> |Latest — Chronological| CHRON[Query Posts from Followed Accounts\nOrder by created_at DESC\nSkip Ranking]
    CHRON --> FILTER

    CACHECHECK{Ranked Feed Cache Hit\nEdge Cache TTL = 2 minutes?}
    CACHECHECK --> |Cache Hit| CACHEDRESULT[Return Cached Feed Slice\nSkip DB Query]
    CACHEDRESULT --> RENDER
    CACHECHECK --> |Cache Miss| FOLLOWCHECK

    FOLLOWCHECK{User Has ≥ 3 Follows?}
    FOLLOWCHECK --> |No — New User| DISCOVER[Build Discovery Feed\nTrending Posts in User Interest Categories\nSuggested Accounts to Follow]
    DISCOVER --> ADSLOT
    FOLLOWCHECK --> |Yes| FEEDQUERY

    FEEDQUERY[Query FeedItem Table\nWHERE user_id = current user\nORDER BY ranking_score DESC\nLIMIT 50 candidates]

    FEEDQUERY --> FILTER

    FILTER[Apply Real-Time Filters\nRemove Posts from Blocked Users\nRemove Posts Violating Viewer Privacy\nRemove Expired Stories\nRemove Deleted or Removed Posts]

    FILTER --> DIVERSITY{Diversity Check\nSame Author > 3 consecutive posts?}
    DIVERSITY --> |Yes| REORDER[Interleave Posts from Other Authors\nPreserve Top Score but Break Clusters]
    DIVERSITY --> |No| ADSLOT
    REORDER --> ADSLOT

    ADSLOT[Ad Injection\nCall Ad Delivery Service with User Interest Vector\nInsert 1 Sponsored Post per 8 Organic Posts]

    ADSLOT --> ADAUCTION{Eligible Campaigns with Budget?}
    ADAUCTION --> |No Eligible Campaigns| NOAD[Skip Ad Slot — Return Organic Only]
    ADAUCTION --> |Winning Creative Selected| ADINJECT[Inject AdCreative as Sponsored FeedItem\nRecord AdImpression Event]

    NOAD --> PAGINATE
    ADINJECT --> PAGINATE

    PAGINATE{Pagination Cursor Provided?}
    PAGINATE --> |First Load — No Cursor| TOP25[Return Top 25 FeedItems to Client]
    PAGINATE --> |Scroll — Has Cursor| NEXTPAGE[Return Next 25 FeedItems\nStarting After Cursor Position]

    TOP25 --> RENDER
    NEXTPAGE --> RENDER

    RENDER[Client Renders Feed\nUser Begins Scrolling]

    RENDER --> IMPRESSIONS[Client Emits Impression Events\nfor Each Visible Post\nDwell Time, Scroll Depth]

    IMPRESSIONS --> KAFKA[Publish Engagement Events\nto Kafka Topic: feed.impressions]

    KAFKA --> RANKENGINE[Feed Ranking Engine Consumes Events\nUpdate Engagement Signals in Feature Store]

    RANKENGINE --> RESCORE[Re-score FeedItems for User\nUpdate ranking_score in DB\nInvalidate Edge Cache]

    RESCORE --> PRECOMPUTE[Pre-compute Next Feed Slice\nCache for Next Session Open]

    PRECOMPUTE --> ([Background Re-ranking Complete — End])

    RENDER --> SCROLL{User Scrolls to 20th Item?}
    SCROLL --> |Yes — Load More| PAGINATE
    SCROLL --> |No — User Leaves Feed| ([Session Ends — End])

    style START fill:#4CAF50,color:#fff
    style RENDER fill:#2196F3,color:#fff
```

---

## 5. Key Design Notes

### Fan-Out Strategy
The platform uses a **fan-out-on-write** strategy for users with fewer than 10 000 followers. Posts are proactively pushed into each follower's `FeedItem` table at publish time, minimising read latency. For accounts with > 10 000 followers (celebrities, verified creators), a **fan-out-on-read** strategy is used: the feed query merges a pre-computed popular-posts list with the user's personal follow graph at read time to avoid write amplification.

### Feed Ranking Signals
The ML ranking model incorporates the following features per `FeedItem`: author relationship strength (close friend vs. casual follow), content type preference (user historically engages more with video vs. text), recency decay (exponential decay on posts older than 48 hours), engagement velocity (reactions and comments in the first 30 minutes post-publish), and topic affinity (cosine similarity between post embedding and user interest vector).

### Moderation Latency Targets
- **Text-only posts:** AI screening completes in < 2 seconds; feed fan-out begins immediately on pass.
- **Image posts:** AI screening completes in < 5 seconds.
- **Video posts:** AI screening completes in < 30 seconds (async; post may appear in feed before video is fully screened, with video replaced by a placeholder until cleared).
- **Human review SLA:** Escalated items are reviewed within 4 hours for high-severity categories (violence, CSAM escalation confirmation) and within 24 hours for standard categories.

### Story Expiry Job
A scheduled cron job runs every 5 minutes to identify `Story` records where `expires_at <= NOW()` and `status = ACTIVE`. Expired stories are transitioned to `EXPIRED`, their CDN paths are purged, and the media is moved to the creator's private archive (retained for 7 days). The job processes up to 10 000 stories per run with an idempotency key to prevent double-processing.
