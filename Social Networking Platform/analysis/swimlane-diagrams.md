# Swimlane Diagrams — Social Networking Platform

## 1. Overview

This document presents swimlane diagrams for two critical cross-functional platform processes: the Content Moderation Pipeline and the Ad Campaign Lifecycle. Swimlane diagrams extend standard activity diagrams by assigning each step to a specific actor (lane), making responsibility boundaries explicit and highlighting handoffs between systems or teams.

These diagrams are the primary reference for integration engineers, product managers, and compliance officers who need to understand accountability for each action in a multi-party process. Each lane represents a distinct actor: a user-facing role, an automated internal service, or a human team. Handoffs between lanes signal API calls, event publications, queue operations, or human task assignments.

---

## 2. Content Moderation Pipeline

This pipeline covers the full lifecycle of a content moderation event — from the moment a user submits a report (or new content is created) through AI pre-screening, human review, decision enforcement, and the appeals process. The four lanes reflect the actual operational boundaries: the end user (reporter and reported), the automated AI Moderation Service, the human Moderation team, and the Appeals team handling escalated disputes.

**Trigger conditions:**
- A `RegisteredUser` explicitly reports a post, comment, story, profile, or direct message.
- The platform's proactive scanning pipeline flags content at creation time (all new posts pass through AI screening).
- A scheduled re-scan job re-evaluates previously borderline content against an updated model.

```mermaid
flowchart TD
    subgraph User["👤 User (Reporter / Content Author)"]
        U1[User Reports Content\nor Content Is Created] --> U2[System Shows\nReport Confirmation]
        U_NOTIF[Receive Decision Notification\nAction Taken or No Violation Found]
        U_APPEAL[Tap Appeal Link\nEnter Appeal Reason\nmax 500 characters]
        U_APPEAL_RESULT[Receive Appeal Outcome\nUpheld or Overturned]
    end

    subgraph AIModerationService["🤖 AI Moderation Service"]
        AI1[Receive Content Submission\nwith content_id and content_type]
        AI2[Run Multimodal Classifiers\nText: NLP Hate Speech, Spam, Misinformation\nImage: NSFW, Violence, Symbols\nVideo: Scene-level Frame Sampling]
        AI3{Confidence Score\nEvaluation}
        AI_AUTO[Auto-Action:\nTransition to REMOVED_AUTO\nTrigger Law Enforcement Report if CSAM\nSkip Human Queue]
        AI_ESCALATE[Escalate to Front of ModerationQueue\nScore ≥ 0.92\nAttach Classifier Breakdown]
        AI_PASS[Mark as AI-Cleared\nSend to Standard Queue\nScore 0.70–0.91]
        AI_LOWSCORE[Dismiss — No Action\nScore < 0.70 and Single Report]
    end

    subgraph HumanModerator["🧑‍⚖️ Human Moderator"]
        MOD1[Open ModerationQueue Dashboard\nSorted by Priority Score and Report Count]
        MOD2[Review Content in Full Context\nView Reporter Description\nView AI Classifier Breakdown\nCheck Prior Violations on Account]
        MOD3{Moderator Decision}
        MOD_DISMISS[No Violation — Dismiss\nClose ContentReport\nUpdate Queue Item to RESOLVED]
        MOD_WARN[Minor Violation\nIssue In-App Warning\nCreate Warning Record]
        MOD_REMOVE[Remove Content\nTransition Post to REMOVED\nTrigger CDN Purge\nCreate ModerationQueue Entry]
        MOD_TEMPBAN[Temporary Ban\n1 day, 7 days, or 30 days\nCreate BanRecord\nSuspend User Account]
        MOD_ESCALATE_ADMIN[Escalate to Admin\nMark as NEEDS_ADMIN_REVIEW\nAttach Moderator Notes]
    end

    subgraph AppealsTeam["⚖️ Appeals Team (Admin-Level)"]
        APP1[Receive Appeal in Admin Queue]
        APP2[Review Original Decision\nReview AI Evidence\nReview Moderator Notes\nReview User Appeal Statement]
        APP3{Appeals Decision}
        APP_UPHOLD[Uphold Original Decision\nNotify User — Appeal Denied]
        APP_OVERTURN[Overturn Decision\nRestore Content or Lift Ban\nExpunge Warning Record\nNotify User — Appeal Successful]
        APP_PERMBAN[Escalate to Permanent Ban\nFor Severe or Repeat Offender\nCreate Permanent BanRecord]
    end

    %% ── Flow ──────────────────────────────────────────────────────
    U1 --> AI1
    AI1 --> AI2
    AI2 --> AI3

    AI3 --> |Score ≥ 0.98 — CSAM or Terrorism| AI_AUTO
    AI3 --> |Score 0.92–0.97 — High Risk| AI_ESCALATE
    AI3 --> |Score 0.70–0.91 — Moderate Risk| AI_PASS
    AI3 --> |Score < 0.70 and Single Report| AI_LOWSCORE

    AI_AUTO --> U_NOTIF
    AI_AUTO -.->|Human Confirmation Task| MOD1

    AI_ESCALATE --> MOD1
    AI_PASS --> MOD1
    AI_LOWSCORE --> U2

    U2 --> U_NOTIF

    MOD1 --> MOD2
    MOD2 --> MOD3

    MOD3 --> |No Violation| MOD_DISMISS
    MOD3 --> |Minor Violation| MOD_WARN
    MOD3 --> |Remove Content| MOD_REMOVE
    MOD3 --> |Temporary Ban| MOD_TEMPBAN
    MOD3 --> |Needs Admin Review| MOD_ESCALATE_ADMIN

    MOD_DISMISS --> U_NOTIF
    MOD_WARN --> U_NOTIF
    MOD_REMOVE --> U_NOTIF
    MOD_TEMPBAN --> U_NOTIF
    MOD_ESCALATE_ADMIN --> APP1

    U_NOTIF --> |User Disagrees and Taps Appeal| U_APPEAL
    U_APPEAL --> APP1

    APP1 --> APP2
    APP2 --> APP3

    APP3 --> |Uphold| APP_UPHOLD
    APP3 --> |Overturn| APP_OVERTURN
    APP3 --> |Escalate to Permanent Ban| APP_PERMBAN

    APP_UPHOLD --> U_APPEAL_RESULT
    APP_OVERTURN --> U_APPEAL_RESULT
    APP_PERMBAN --> U_APPEAL_RESULT
```

### 2.1 Pipeline Notes

**Priority Queue Ordering:** The `ModerationQueue` is a priority queue sorted by `(ai_confidence_score * report_count_weight * content_reach_factor)` where `content_reach_factor` is a multiplier based on how many users have viewed the flagged content. Content reaching > 10 000 impressions is boosted by 2×.

**SLA Targets:**

| Category | Target Review Time |
|---|---|
| CSAM / Child Safety (auto-removed, human confirmation) | 2 hours |
| Terrorism / Incitement to Violence (high confidence) | 4 hours |
| Hate Speech / Harassment (escalated) | 8 hours |
| Standard Spam / Nudity | 24 hours |
| Appeals | 72 hours |

**Repeat Offender Logic:** A user's third confirmed violation within 90 days automatically adds a `REPEAT_OFFENDER` flag to their `User` record. This flag causes all future posts by the account to undergo mandatory human review (bypassing the AI-pass-only path) for 180 days, regardless of AI confidence scores.

**Audit Trail:** Every action taken in the pipeline — AI verdict, moderator decision, admin override, appeal outcome — is logged with a timestamp, the acting agent's identifier, and a snapshot of the content at time of review. This log is retained for 7 years for legal compliance.

---

## 3. Ad Campaign Lifecycle

This swimlane covers the complete lifecycle of an advertising campaign: from the advertiser creating a campaign brief through creative submission, review, activation, live delivery with real-time budget tracking, and final billing reconciliation. The four lanes represent the Advertiser (external actor), the Ad Platform (internal service layer), the Billing Service, and the Content Delivery layer responsible for serving impressions.

**Key Entities:** `Advertiser`, `AdCampaign`, `AdCreative`, `AdImpression`

```mermaid
flowchart TD
    subgraph Advertiser["🏢 Advertiser"]
        ADV1[Log In to Ads Manager\nCreate New Campaign]
        ADV2[Define Campaign Details:\nObjective, Budget, Date Range\nTarget Audience: Age, Location, Interests\nLookalike Audience Source]
        ADV3[Upload Ad Creative:\nImage, Video, Carousel, or Story Ad\nAdd Headline, Body Copy, CTA, Landing URL]
        ADV4[Submit Campaign for Review]
        ADV_EDIT[Edit Creative or Targeting\nResubmit for Review]
        ADV_PAUSE[Pause Campaign Manually]
        ADV_VIEW[View Campaign Analytics Dashboard:\nImpressions, Clicks, CTR, Conversions\nCPM, CPC, ROAS]
        ADV_BILLING[View Invoices\nDownload Billing Statements\nDispute Charge if Needed]
    end

    subgraph AdPlatform["⚙️ Ad Platform (Internal)"]
        ADP1[Validate Campaign Parameters:\nBudget Minimum, Date Range Valid\nAudience Size Estimate ≥ 1000]
        ADP2[Submit Creative to Content Review\nAI Policy Check:\nNo Prohibited Categories\nNo Deceptive Claims\nNo Political Ads without Disclosure]
        ADP3{Creative Review Outcome}
        ADP_REJECT[Reject Creative\nReturn Violation Reason to Advertiser]
        ADP_APPROVE[Approve Creative\nCreate AdCreative Record in APPROVED State\nTransition AdCampaign to ACTIVE]
        ADP4[Real-Time Ad Auction:\nReceive Targeting Request from Feed Service\nScore Eligible Campaigns by Bid × Quality Score\nSelect Winning Creative]
        ADP5[Serve Winning Creative\nRecord AdImpression Event:\ncampaign_id, creative_id, user_id anon, timestamp, placement]
        ADP6{Daily Budget Reached?}
        ADP7[Pause Campaign for Remainder of Day\nResume at Midnight UTC]
        ADP8{Campaign End Date Reached?}
        ADP9[Transition AdCampaign to COMPLETED\nGenerate Final Impression Report]
        ADP_FRAUD[Fraud Detection Check\nFlag Suspicious Click Patterns\nInvalidate Fraudulent Impressions]
    end

    subgraph BillingService["💳 Billing Service"]
        BILL1[Capture Payment Method\nStripe Card Tokenisation]
        BILL2[Pre-Authorise Campaign Budget\non Card at Campaign Activation]
        BILL3[Meter Spend in Real-Time\nCharge per 1000 Impressions CPM\nor per Click CPC per Campaign Type]
        BILL4[Daily Reconciliation\nAggregate Valid Impressions\nDeduct Fraudulent Impressions]
        BILL5[Generate Monthly Invoice\nCharge Settled Amount to Card\nEmail Invoice PDF to Advertiser]
        BILL_DISPUTE[Process Dispute:\nPause Billing on Disputed Line Items\nRoute to Stripe Dispute Resolution]
    end

    subgraph ContentDelivery["📡 Content Delivery (CDN + Ad Serving)"]
        CDN1[Cache Approved Ad Creatives\nPre-warm CDN Edge Nodes for\nTargeted Geographies]
        CDN2[Serve Ad Creative from Nearest\nEdge Node — p95 < 100ms]
        CDN3[Return Impression Confirmation\nPixel Fire to Advertiser Tracking URL]
        CDN4[Purge Creative from CDN\non Campaign Pause, Completion, or Rejection]
    end

    %% ── Flow ──────────────────────────────────────────────────────
    ADV1 --> ADV2
    ADV2 --> ADV3
    ADV3 --> ADV4
    ADV4 --> ADP1

    ADP1 --> |Invalid Parameters| ADV_EDIT
    ADV_EDIT --> ADV4

    ADP1 --> |Valid| BILL1
    BILL1 --> BILL2
    BILL2 --> ADP2

    ADP2 --> ADP3
    ADP3 --> |Rejected| ADP_REJECT
    ADP_REJECT --> ADV_EDIT

    ADP3 --> |Approved| ADP_APPROVE
    ADP_APPROVE --> CDN1

    CDN1 --> ADP4

    ADP4 --> |Creative Wins Auction| ADP5
    ADP5 --> CDN2
    CDN2 --> CDN3
    CDN3 --> BILL3
    BILL3 --> ADP_FRAUD

    ADP_FRAUD --> |Clean Impression| BILL4
    ADP_FRAUD --> |Fraudulent — Invalidate| BILL4

    BILL4 --> ADP6
    ADP6 --> |Yes — Budget Exhausted for Today| ADP7
    ADP7 --> |Next Day| ADP4

    ADP6 --> |No — Continue Serving| ADP8
    ADP8 --> |End Date Not Reached| ADP4
    ADP8 --> |End Date Reached| ADP9

    ADP9 --> CDN4
    ADP9 --> BILL5
    BILL5 --> ADV_BILLING

    ADV_PAUSE --> ADP7
    ADP7 -.->|Pause Notification| ADV_VIEW

    ADV_VIEW --> |Ongoing Campaign| ADP4
    ADV_BILLING --> |Dispute Raised| BILL_DISPUTE
    BILL_DISPUTE --> BILL5
```

### 3.1 Campaign Lifecycle Notes

**Auction Mechanics:** The ad auction is a generalised second-price auction. Each eligible `AdCampaign` has an effective CPM bid and a Quality Score (0–10) calculated from the creative's historical CTR, landing page quality, and audience relevance. The effective rank is `bid × quality_score`. The winning campaign pays the second-highest effective bid plus $0.01, not its own maximum bid.

**Budget Controls:**

| Control | Behaviour |
|---|---|
| Daily Budget | Campaign paused when daily spend reaches the daily budget; resumes at midnight UTC |
| Lifetime Budget | Campaign paused permanently when cumulative spend reaches the lifetime cap |
| Pacing | Even pacing distributes budget evenly across the campaign window; accelerated pacing spends as fast as possible |

**Creative Review SLA:** Ad creatives submitted for review receive a decision within 24 hours for standard categories and within 1 hour for expedited review (available on premium ad accounts). Automated AI review covers prohibited content categories (weapons, adult content, hate speech, deceptive health claims) and returns a verdict within 60 seconds for image creatives and 5 minutes for video.

**Fraud Detection:** The platform operates a click-fraud detection model that analyses IP diversity, device fingerprint clustering, click-to-conversion lag, and post-click engagement depth. Impressions or clicks identified as fraudulent are invalidated within 24 hours and excluded from billing. Advertisers can view the fraud-adjusted metrics in their analytics dashboard.

**GDPR & Ad Targeting Compliance:** User interest vectors used in ad targeting are derived from anonymised, aggregated engagement signals. No raw personal data is shared with advertisers. Users can opt out of interest-based advertising via their Privacy Settings, which removes them from all lookalike and interest-targeted audiences and serves only contextual ads.
