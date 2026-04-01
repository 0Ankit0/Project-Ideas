# Use-Case Diagram — Social Networking Platform

## 1. Overview

This document presents the complete use-case model for the Social Networking Platform. It identifies all system actors, their goals, and the functional boundaries of the platform. The diagram captures both user-facing interactions and system-driven background processes spanning profile management, content creation, discovery, messaging, moderation, advertising, and safety features.

The platform supports a spectrum of users ranging from unauthenticated guests to platform administrators. Each actor category has a distinct set of permitted interactions governed by authentication state, role, and account standing.

---

## 2. Actors

| Actor | Type | Description |
|---|---|---|
| **Guest** | Primary | Unauthenticated visitor browsing public content or landing pages |
| **RegisteredUser** | Primary | Authenticated user with a standard account; can create content, follow others, and message |
| **ContentCreator** | Primary | Extends RegisteredUser; operates public/creator accounts with analytics and monetisation access |
| **Moderator** | Primary | Platform staff with access to the moderation queue; reviews flagged content and user reports |
| **Admin** | Primary | Platform operator with full configuration and override capabilities |
| **Advertiser** | Primary | Businesses or individuals who create and manage paid ad campaigns |
| **System** | Secondary | Internal automated services: feed ranking engine, notification dispatcher, AI moderation, story expiry, CDN purge |

---

## 3. Use-Case Diagram

```mermaid
graph TD
    %% Actors
    GUEST([Guest])
    USER([RegisteredUser])
    CREATOR([ContentCreator])
    MOD([Moderator])
    ADMIN([Admin])
    ADV([Advertiser])
    SYS([System])

    %% ── GUEST USE CASES ──────────────────────────────────────────
    GUEST --> UC_REGISTER["Register Account"]
    GUEST --> UC_LOGIN["Log In"]
    GUEST --> UC_VIEW_PUBLIC["View Public Profile"]
    GUEST --> UC_SEARCH_PUBLIC["Search Public Content"]
    GUEST --> UC_VIEW_POST_PUBLIC["View Public Post"]
    GUEST --> UC_FORGOT_PWD["Reset Password"]

    %% ── REGISTERED USER USE CASES ───────────────────────────────
    USER --> UC_REGISTER
    USER --> UC_EDIT_PROFILE["Edit Profile"]
    USER --> UC_PRIVACY_SETTINGS["Manage Privacy Settings"]
    USER --> UC_FOLLOW["Follow / Unfollow User"]
    USER --> UC_FRIEND_REQ["Send / Accept Friend Request"]
    USER --> UC_BLOCK["Block / Unblock User"]
    USER --> UC_MUTE["Mute User or Keyword"]

    USER --> UC_CREATE_POST["Create & Publish Post"]
    USER --> UC_EDIT_POST["Edit Post"]
    USER --> UC_DELETE_POST["Delete Post"]
    USER --> UC_CREATE_STORY["Create & View Story"]
    USER --> UC_CREATE_POLL["Create Poll & Vote"]
    USER --> UC_REPOST["Repost / Quote Post"]
    USER --> UC_SHARE["Share Post"]

    USER --> UC_REACT["React to Content"]
    USER --> UC_COMMENT["Comment on Post"]
    USER --> UC_NESTED_COMMENT["Reply to Comment"]
    USER --> UC_MENTION["Mention User in Post/Comment"]
    USER --> UC_TAG_HASHTAG["Tag Hashtag in Post"]
    USER --> UC_FOLLOW_HASHTAG["Follow Hashtag"]

    USER --> UC_VIEW_FEED["View Personalised Feed"]
    USER --> UC_EXPLORE["Explore / Discover Content"]
    USER --> UC_SEARCH["Search Users, Hashtags, Posts"]
    USER --> UC_VIEW_NOTIFICATIONS["View Notifications"]
    USER --> UC_MANAGE_NOTIF_PREFS["Manage Notification Preferences"]

    USER --> UC_DM["Send Direct Message"]
    USER --> UC_GROUP_CHAT["Create / Join Group Chat"]
    USER --> UC_DM_MEDIA["Share Media in DM"]

    USER --> UC_JOIN_COMMUNITY["Join / Leave Community"]
    USER --> UC_VIEW_COMMUNITY["View Community Feed"]
    USER --> UC_POST_COMMUNITY["Post in Community"]

    USER --> UC_REPORT["Report Content / User"]
    USER --> UC_GDPR_EXPORT["Export Personal Data (GDPR)"]
    USER --> UC_GDPR_DELETE["Request Account Deletion (GDPR)"]
    USER --> UC_VERIFY["Apply for Account Verification"]

    %% ── CONTENT CREATOR EXTENSIONS ──────────────────────────────
    CREATOR --> UC_CREATE_POST
    CREATOR --> UC_ANALYTICS["View Post & Audience Analytics"]
    CREATOR --> UC_REEL["Upload Reel / Short Video"]
    CREATOR --> UC_SCHEDULE_POST["Schedule Post"]
    CREATOR --> UC_CLOSE_FRIENDS["Manage Close Friends List"]
    CREATOR --> UC_COLLAB_POST["Create Collab Post"]
    CREATOR --> UC_MONETISE["Access Monetisation Dashboard"]

    %% ── MODERATOR USE CASES ─────────────────────────────────────
    MOD --> UC_REVIEW_QUEUE["Review Moderation Queue"]
    MOD --> UC_APPROVE_CONTENT["Approve Reported Content"]
    MOD --> UC_REMOVE_CONTENT["Remove Violating Content"]
    MOD --> UC_WARN_USER["Issue User Warning"]
    MOD --> UC_TEMP_BAN["Apply Temporary Ban"]
    MOD --> UC_ESCALATE["Escalate to Admin"]
    MOD --> UC_VIEW_MOD_HISTORY["View Moderation History"]

    %% ── ADMIN USE CASES ─────────────────────────────────────────
    ADMIN --> UC_REVIEW_QUEUE
    ADMIN --> UC_PERM_BAN["Apply Permanent Ban"]
    ADMIN --> UC_REINSTATE["Reinstate Account"]
    ADMIN --> UC_MANAGE_MODERATORS["Manage Moderator Accounts"]
    ADMIN --> UC_PLATFORM_CONFIG["Configure Platform Settings"]
    ADMIN --> UC_APPROVE_VERIFY["Approve Verification Badge"]
    ADMIN --> UC_AD_OVERSIGHT["Ad Campaign Oversight"]
    ADMIN --> UC_COMMUNITY_MGMT["Manage Communities"]
    ADMIN --> UC_GDPR_PROCESS["Process GDPR Requests"]

    %% ── ADVERTISER USE CASES ────────────────────────────────────
    ADV --> UC_CREATE_CAMPAIGN["Create Ad Campaign"]
    ADV --> UC_UPLOAD_CREATIVE["Upload Ad Creative"]
    ADV --> UC_TARGET_AUDIENCE["Define Target Audience"]
    ADV --> UC_SET_BUDGET["Set Campaign Budget & Schedule"]
    ADV --> UC_CAMPAIGN_ANALYTICS["View Campaign Analytics"]
    ADV --> UC_BILLING["Manage Billing & Invoices"]
    ADV --> UC_PAUSE_CAMPAIGN["Pause / Resume Campaign"]

    %% ── SYSTEM USE CASES ────────────────────────────────────────
    SYS --> UC_RANK_FEED["Rank Feed Items (ML)"]
    SYS --> UC_EXPIRE_STORIES["Expire Stories after 24h"]
    SYS --> UC_DISPATCH_NOTIF["Dispatch Notifications"]
    SYS --> UC_AI_MODERATION["AI Content Screening"]
    SYS --> UC_CDN_PURGE["Purge CDN on Content Removal"]
    SYS --> UC_AD_DELIVERY["Deliver Ad Impressions"]
    SYS --> UC_ENCRYPT_DM["Encrypt Direct Messages (E2E)"]
    SYS --> UC_SEND_DIGEST["Send Weekly Digest Email"]
```

---

## 4. Use-Case Summary Table

| # | Use Case | Actor(s) | Priority | Phase |
|---|---|---|---|---|
| UC-001 | Register & Onboard Account | Guest | P0 | MVP |
| UC-002 | Log In / Log Out | Guest, RegisteredUser | P0 | MVP |
| UC-003 | Reset Password | Guest | P0 | MVP |
| UC-004 | Edit Profile & Avatar | RegisteredUser | P0 | MVP |
| UC-005 | Manage Privacy Settings | RegisteredUser | P0 | MVP |
| UC-006 | Follow / Unfollow User | RegisteredUser | P0 | MVP |
| UC-007 | Send / Accept Friend Request | RegisteredUser | P0 | MVP |
| UC-008 | Block / Unblock User | RegisteredUser | P0 | MVP |
| UC-009 | Mute User or Keyword | RegisteredUser | P1 | MVP |
| UC-010 | Create & Publish Post | RegisteredUser, ContentCreator | P0 | MVP |
| UC-011 | Edit / Delete Post | RegisteredUser | P0 | MVP |
| UC-012 | Create & View Story | RegisteredUser, ContentCreator | P0 | MVP |
| UC-013 | Create Poll & Vote | RegisteredUser | P1 | MVP |
| UC-014 | Repost / Quote Post | RegisteredUser | P1 | MVP |
| UC-015 | Share Post | RegisteredUser | P1 | MVP |
| UC-016 | React to Content | RegisteredUser | P0 | MVP |
| UC-017 | Comment on Post | RegisteredUser | P0 | MVP |
| UC-018 | Reply to Comment (Nested) | RegisteredUser | P0 | MVP |
| UC-019 | Mention User | RegisteredUser | P1 | MVP |
| UC-020 | Tag Hashtag in Post | RegisteredUser | P1 | MVP |
| UC-021 | Follow Hashtag | RegisteredUser | P1 | MVP |
| UC-022 | View Personalised Feed | RegisteredUser, System | P0 | MVP |
| UC-023 | Explore / Discover Content | RegisteredUser | P0 | MVP |
| UC-024 | Search Users, Hashtags, Posts | RegisteredUser, Guest | P0 | MVP |
| UC-025 | View Notifications | RegisteredUser | P0 | MVP |
| UC-026 | Manage Notification Preferences | RegisteredUser | P1 | MVP |
| UC-027 | Send Direct Message (1:1) | RegisteredUser | P0 | MVP |
| UC-028 | Create / Join Group Chat | RegisteredUser | P1 | Phase 2 |
| UC-029 | Share Media in DM | RegisteredUser | P1 | Phase 2 |
| UC-030 | Join / Leave Community | RegisteredUser | P1 | Phase 2 |
| UC-031 | Post in Community | RegisteredUser | P1 | Phase 2 |
| UC-032 | Report Content / User | RegisteredUser | P0 | MVP |
| UC-033 | Export Personal Data (GDPR) | RegisteredUser | P0 | MVP |
| UC-034 | Request Account Deletion (GDPR) | RegisteredUser | P0 | MVP |
| UC-035 | Apply for Account Verification | RegisteredUser | P2 | Phase 2 |
| UC-036 | View Post & Audience Analytics | ContentCreator | P1 | Phase 2 |
| UC-037 | Upload Reel / Short Video | ContentCreator | P1 | Phase 2 |
| UC-038 | Schedule Post | ContentCreator | P2 | Phase 3 |
| UC-039 | Review Moderation Queue | Moderator, Admin | P0 | MVP |
| UC-040 | Approve / Remove Reported Content | Moderator, Admin | P0 | MVP |
| UC-041 | Issue Warning / Ban | Moderator, Admin | P0 | MVP |
| UC-042 | Escalate to Admin | Moderator | P0 | MVP |
| UC-043 | Approve Verification Badge | Admin | P2 | Phase 2 |
| UC-044 | Configure Platform Settings | Admin | P0 | MVP |
| UC-045 | Process GDPR Requests | Admin | P0 | MVP |
| UC-046 | Create Ad Campaign | Advertiser | P1 | Phase 2 |
| UC-047 | Upload Ad Creative | Advertiser | P1 | Phase 2 |
| UC-048 | Define Target Audience | Advertiser | P1 | Phase 2 |
| UC-049 | View Campaign Analytics | Advertiser | P1 | Phase 2 |
| UC-050 | Rank Feed Items (ML) | System | P0 | MVP |
| UC-051 | Expire Stories after 24h | System | P0 | MVP |
| UC-052 | Dispatch Notifications | System | P0 | MVP |
| UC-053 | AI Content Screening | System | P0 | MVP |
| UC-054 | Deliver Ad Impressions | System | P1 | Phase 2 |
| UC-055 | Encrypt Direct Messages (E2E) | System | P0 | MVP |

---

## 5. Actor Descriptions

### Guest
A Guest interacts with the platform before creating an account or while logged out. They can view content on public profiles, read public posts, and use the discovery/search surface. Their primary goal is to evaluate the platform before committing to registration. Guests cannot create content, react, comment, or access the messaging system.

### RegisteredUser
The core actor of the platform. A RegisteredUser has completed email/phone verification and set up at minimum a username and password. They have access to the full social graph (follows, friends, blocks), content creation (posts, stories, polls), reactions, comments, direct messaging, communities, and safety tools. Their experience is governed by their own privacy settings and those of users they interact with.

### ContentCreator
A ContentCreator is a RegisteredUser who has switched to or was granted a creator account. They have access to enhanced features: audience analytics, reel publishing, post scheduling, monetisation dashboards, and the close-friends story segmentation. Creator accounts are always public-facing and may carry a verification badge.

### Moderator
A Moderator is a platform employee or trusted community volunteer assigned to review flagged content submitted through the reporting pipeline. They can approve, remove, or warn but cannot issue permanent bans or alter platform-wide configuration. All moderation actions are logged with timestamps and moderator identity for audit purposes.

### Admin
The Admin has the highest privilege level in the platform. Admins manage moderator accounts, approve verification badges, configure feature flags, process GDPR deletion requests, override moderation decisions, and have full visibility into all audit logs. Admin actions are subject to a separate audit trail retained for legal compliance.

### Advertiser
An Advertiser is a business or individual with an approved ads account. They create campaigns, upload creatives (image/video/carousel), define targeting parameters (age, geography, interests, lookalike audiences), set daily/lifetime budgets, and access impression/click/conversion analytics. Campaigns are subject to content review before going live.

### System
The System actor represents automated, background services that operate without direct human trigger. Key system processes include the ML-based feed ranking engine, the 24-hour story expiry job, the push/email/in-app notification dispatcher, the AI content screening service (hate speech, NSFW, spam detection), the CDN purge service triggered on content removal, and the E2E encryption layer for direct messages.
