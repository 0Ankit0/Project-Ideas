# Requirements — Social Networking Platform

## 1. Introduction

### 1.1 Purpose
This document defines the functional and non-functional requirements for the Social Networking Platform — a full-featured social media product enabling users to connect, share content, communicate, and discover communities. It serves as the authoritative specification for engineering, product, and QA teams.

### 1.2 Product Vision
Build a scalable, privacy-first social networking platform that empowers authentic self-expression, meaningful connections, and safe digital communities. The platform supports individual creators, casual users, and advertisers through a unified content ecosystem.

### 1.3 Intended Audience
- Product Managers
- Software Engineers (Backend, Frontend, Mobile)
- QA and Test Engineers
- Security and Compliance Teams
- Data and ML Engineers

### 1.4 Definitions & Abbreviations
| Term | Definition |
|---|---|
| FR | Functional Requirement |
| NFR | Non-Functional Requirement |
| E2EE | End-to-End Encryption |
| DAU | Daily Active Users |
| MAU | Monthly Active Users |
| GDPR | General Data Protection Regulation |
| CCPA | California Consumer Privacy Act |
| CDN | Content Delivery Network |
| ML | Machine Learning |
| SLA | Service Level Agreement |

---

## 2. Functional Requirements

### 2.1 User Management & Authentication

**FR-USR-001:** The system shall allow new users to register using an email address and password, or via OAuth 2.0 providers (Google, Apple, Facebook).

**FR-USR-002:** The system shall verify email addresses by sending a time-limited (24-hour) confirmation link before granting full account access.

**FR-USR-003:** The system shall enforce strong password requirements: minimum 8 characters, at least one uppercase letter, one digit, and one special character.

**FR-USR-004:** The system shall support Multi-Factor Authentication (MFA) via TOTP authenticator apps and SMS OTP as a secondary factor.

**FR-USR-005:** The system shall allow users to reset their password via a verified email link that expires after 1 hour.

**FR-USR-006:** The system shall detect and throttle brute-force login attempts, locking an account after 10 consecutive failures and requiring email verification to unlock.

**FR-USR-007:** The system shall maintain session tokens with a configurable expiry (default 30 days) and allow users to view and revoke active sessions from any device.

**FR-USR-008:** The system shall support phone-number-based registration as an alternative to email, with OTP verification.

**FR-USR-009:** The system shall allow users to link multiple login methods (email, Google, Apple) to a single account.

**FR-USR-010:** The system shall allow users to deactivate their account (temporary, reversible within 30 days) or permanently delete their account with a 14-day grace period.

---

### 2.2 Profile Management

**FR-PRF-001:** Each user shall have a profile containing: display name, unique username (handle), profile photo, cover photo, bio (up to 160 characters), website URL, location, date of birth (private by default), and pronouns.

**FR-PRF-002:** The system shall enforce globally unique usernames (case-insensitive) and allow users to change their username up to twice per 30-day period.

**FR-PRF-003:** The system shall support profile verification badges for public figures, brands, and creators, managed by platform admins.

**FR-PRF-004:** Users shall be able to set their profile visibility to Public, Followers Only, or Private (connection requests required).

**FR-PRF-005:** The system shall display profile statistics including: follower count, following count, post count, and (for public profiles) total post impressions.

**FR-PRF-006:** Users shall be able to pin up to 3 posts to the top of their profile page.

**FR-PRF-007:** The system shall support a "Featured" section on profiles where users can highlight up to 6 posts, stories, or communities.

**FR-PRF-008:** Users shall be able to configure which activity is visible on their profile (e.g., liked posts, communities joined, followed hashtags).

---

### 2.3 Social Graph (Follow / Friends / Blocks)

**FR-SOC-001:** The system shall support a directed follow model where User A can follow User B without reciprocity, and a mutual friend model where both parties must accept.

**FR-SOC-002:** Users with private profiles shall receive follow requests that they can accept or decline; public profiles shall allow instant following.

**FR-SOC-003:** The system shall allow users to remove followers without notifying the removed party.

**FR-SOC-004:** The system shall enforce a following limit of 10,000 accounts per user to prevent spam networks.

**FR-SOC-005:** Users shall be able to block another user, which prevents the blocked user from viewing their profile, posts, or sending messages.

**FR-SOC-006:** Users shall be able to mute another user's posts and/or stories without unfollowing them; muting is private and not communicated to the muted user.

**FR-SOC-007:** The system shall provide a "Close Friends" list feature, allowing users to share stories or posts with a selected subset of followers.

**FR-SOC-008:** The system shall suggest accounts to follow based on mutual connections, shared interests, and location (opt-in).

**FR-SOC-009:** Users shall be able to view their full list of followers and following accounts, with the ability to search and filter.

**FR-SOC-010:** The system shall allow users to send, accept, decline, and cancel friend requests; a pending friend request shall not grant any additional visibility.

---

### 2.4 Post Creation & Management

**FR-POST-001:** Users shall be able to create posts with the following content types: plain text (up to 2,000 characters), photo(s) (up to 10 images per post), video (up to 10 minutes, 500 MB), polls, and link previews with auto-generated metadata.

**FR-POST-002:** The system shall support rich text formatting in post captions: bold, italic, and inline code via Markdown-lite syntax.

**FR-POST-003:** Users shall be able to tag up to 20 other users in a post; tagged users receive a notification and may remove their tag.

**FR-POST-004:** Users shall be able to set post-level audience: Public, Followers Only, Close Friends, or Specific People.

**FR-POST-005:** The system shall support scheduled posts, allowing users to set a future publish date/time up to 6 months in advance.

**FR-POST-006:** Users shall be able to edit post captions and audience settings after publishing; an edit history shall be retained and visible to readers.

**FR-POST-007:** Users shall be able to delete their own posts; deleted posts shall be permanently removed within 30 days of deletion.

**FR-POST-008:** The system shall support creating poll posts with 2–4 options, a configurable voting window (1 hour to 7 days), and anonymous or attributed voting.

**FR-POST-009:** Users shall be able to create quote posts that embed an existing post with additional commentary.

**FR-POST-010:** The system shall support repost (without commentary), where the original post appears on the reposter's profile with attribution.

**FR-POST-011:** Users shall be able to enable or disable comments and reactions on their individual posts.

**FR-POST-012:** The system shall auto-detect and hyperlink hashtags and mentions within post text at creation time.

---

### 2.5 Feed & Content Discovery

**FR-FEED-001:** The system shall generate a personalized "For You" feed for each authenticated user, ranking content based on a configurable ML ranking model.

**FR-FEED-002:** The system shall provide a chronological "Following" feed showing only posts from accounts and communities the user follows.

**FR-FEED-003:** Feed items shall include posts, reposts, quote posts, sponsored ads (clearly labeled), and suggested accounts.

**FR-FEED-004:** The system shall apply a deduplication rule so the same post does not appear more than once per feed refresh cycle.

**FR-FEED-005:** Users shall be able to tune their feed by marking posts as "Not Interested," snoozing accounts for 30 days, or reporting low-quality content.

**FR-FEED-006:** The system shall support an Explore/Discover section showing trending posts, hashtags, and communities, personalized by location and interests.

**FR-FEED-007:** Feed ranking signals shall include: recency, engagement rate (likes, comments, shares), relationship strength (close friends, frequent interactions), content-type preference, and advertiser bid.

**FR-FEED-008:** The system shall support infinite scroll with cursor-based pagination, loading batches of 20 feed items per request.

---

### 2.6 Reactions & Comments

**FR-RCT-001:** The system shall support six reaction types on posts, comments, and stories: Like, Love, Haha, Wow, Sad, and Angry.

**FR-RCT-002:** Users shall be able to view the full list of reactors on a post, filterable by reaction type, for posts on public profiles.

**FR-RCT-003:** Post authors shall be able to restrict or disable reactions on individual posts.

**FR-RCT-004:** The system shall support threaded comments up to 3 levels deep (comment → reply → nested reply).

**FR-RCT-005:** Comments shall support text (up to 500 characters), a single image attachment, GIF selection from an integrated GIF library, and @mentions.

**FR-RCT-006:** Post authors shall be able to pin up to 3 comments to the top of their comment thread.

**FR-RCT-007:** Users shall be able to edit or delete their own comments; edited comments show an "Edited" label.

**FR-RCT-008:** Post authors shall be able to hide individual comments from their post without deleting them; hidden comments are visible only to the commenter.

**FR-RCT-009:** The system shall display comment counts and reaction summary (top 3 reaction types + total count) on feed cards.

---

### 2.7 Stories

**FR-STR-001:** Users shall be able to create Stories composed of photos, videos (up to 30 seconds each), or text cards with background colors and fonts.

**FR-STR-002:** Stories shall automatically expire and become inaccessible to viewers after 24 hours from the time of posting; the author retains access via Story Archive.

**FR-STR-003:** Users shall be able to add interactive stickers to Stories: polls (binary choice), questions (open text), sliders (emoji scale), countdown timers, and location tags.

**FR-STR-004:** Users shall be able to view a list of accounts that viewed their Story within the 24-hour active window; after expiry, only the view count is retained.

**FR-STR-005:** The system shall apply configurable audience settings per Story: Public, Followers, Close Friends, or hide from specific users.

**FR-STR-006:** Users shall be able to reply to a Story via a private direct message to the author.

**FR-STR-007:** Users shall be able to save Stories to a permanent "Highlight" collection displayed on their profile.

**FR-STR-008:** The system shall display active Stories from followed accounts in a horizontally scrolling tray at the top of the home feed, ordered by recency and relationship closeness.

---

### 2.8 Messaging (Direct & Group)

**FR-MSG-001:** The system shall support 1:1 direct messaging between any two users who are mutually following or have accepted a message request.

**FR-MSG-002:** Messages from unknown users shall be delivered to a "Message Requests" inbox that the recipient must accept before a full conversation thread is opened.

**FR-MSG-003:** The system shall support group chats with up to 250 members, a group name, group photo, and role-based permissions (owner, admin, member).

**FR-MSG-004:** Group chat admins shall be able to add or remove members, change group settings, and promote/demote other members.

**FR-MSG-005:** Messages shall support: text (up to 2,000 characters), photos, videos (up to 100 MB), voice messages (up to 5 minutes), GIFs, stickers, and shared posts/stories.

**FR-MSG-006:** The system shall provide end-to-end encryption (E2EE) for all direct messages and group chats using the Signal Protocol; encrypted messages cannot be read by the platform.

**FR-MSG-007:** Users shall be able to react to individual messages with emoji reactions.

**FR-MSG-008:** Users shall be able to reply to a specific message (threaded reply within a chat), forward messages to other chats, and delete messages for themselves or for everyone (within 5 minutes).

**FR-MSG-009:** The system shall show real-time typing indicators and read receipts (individually togglable by each user).

**FR-MSG-010:** Users shall be able to mute conversation notifications for a duration (1 hour, 8 hours, 1 week, always) or archive conversations.

---

### 2.9 Notifications

**FR-NTF-001:** The system shall deliver in-app, push (mobile), and email notifications for: new followers, post reactions, comments, mentions, shares, message requests, story interactions, community activity, and moderation decisions.

**FR-NTF-002:** Users shall have granular notification preferences per notification type and per delivery channel (in-app, push, email).

**FR-NTF-003:** The system shall batch non-urgent notifications (e.g., "5 people reacted to your post") to reduce notification fatigue, using a 15-minute aggregation window.

**FR-NTF-004:** The system shall support a "Do Not Disturb" schedule (configurable hours) during which only direct message notifications from close friends are delivered.

**FR-NTF-005:** The notification center shall display a paginated list of all notifications with read/unread state, allowing bulk mark-as-read.

**FR-NTF-006:** The system shall deliver time-sensitive notifications (e.g., story reply, direct message) in real-time via WebSocket push, falling back to polling every 30 seconds.

---

### 2.10 Hashtags & Discovery

**FR-HASH-001:** The system shall parse and index hashtags (case-insensitive, up to 50 characters) from post captions and comments at ingestion time.

**FR-HASH-002:** Clicking a hashtag shall open a dedicated hashtag page showing post count, follower count, and a feed of recent and top posts using that hashtag.

**FR-HASH-003:** Users shall be able to follow hashtags; followed hashtag content will appear in their Following feed interspersed with account posts.

**FR-HASH-004:** The system shall surface trending hashtags on the Explore page, calculated using a rolling 24-hour velocity metric normalized by historical baseline.

**FR-HASH-005:** The system shall support a global search function that queries across users, posts, hashtags, and communities, returning ranked results by relevance and recency.

**FR-HASH-006:** Search results shall be filterable by type (People, Posts, Hashtags, Communities) and sortable by Top, Latest, and Media.

---

### 2.11 Communities

**FR-COM-001:** Users shall be able to create a Community with a name, description, cover image, category tag, and visibility setting (Public or Private).

**FR-COM-002:** Community creators automatically become admins and can appoint additional admins and moderators with defined role-based permissions.

**FR-COM-003:** Public communities can be discovered and joined by any user; Private communities require an invitation or a join request approved by an admin.

**FR-COM-004:** Communities shall have their own dedicated feed of posts, with content types restricted by community rules (configurable by admins).

**FR-COM-005:** Community admins shall be able to create and enforce community-specific rules, pin announcements, and create membership questions for join requests.

**FR-COM-006:** Community members shall be able to create posts within the community subject to admin-configured content review (auto-approved or pending approval).

**FR-COM-007:** Community admins shall be able to ban, mute (temporary), or remove members, and review and action reported content within their community.

**FR-COM-008:** The system shall display community statistics: member count, active members (last 30 days), total posts, and top contributors.

---

### 2.12 Content Moderation

**FR-MOD-001:** Any user shall be able to report a post, comment, story, profile, message (in non-E2EE contexts), or community for: spam, harassment, hate speech, misinformation, nudity/sexual content, violence, or intellectual property infringement.

**FR-MOD-002:** Reported content shall be queued in a ModerationQueue with priority scoring based on report volume and severity category.

**FR-MOD-003:** The system shall apply automated pre-screening using ML classifiers to detect: nudity, graphic violence, spam patterns, and known CSAM hashes (PhotoDNA integration); content exceeding confidence thresholds shall be auto-actioned or escalated.

**FR-MOD-004:** Human moderators shall be able to review queued items and take actions: approve (no action), remove content, issue a warning, restrict account features (temporary), suspend account (30/60/90 days), or permanently ban.

**FR-MOD-005:** The system shall maintain an immutable BanRecord for each moderation action, including moderator ID, timestamp, reason code, and evidence snapshot.

**FR-MOD-006:** Users subject to moderation actions shall receive a notification explaining the action, the policy violated, and their right to appeal.

**FR-MOD-007:** Users shall be able to submit a single appeal per moderation action within 30 days; appeals shall be routed to a senior moderation queue with a 72-hour SLA.

**FR-MOD-008:** The system shall generate daily moderation dashboards showing queue volume, average resolution time, action distribution, and appeal outcomes.

---

### 2.13 Advertising

**FR-ADV-001:** Advertisers shall be able to register an Advertiser account, submit business verification documents, and agree to advertising policies before creating campaigns.

**FR-ADV-002:** Advertisers shall be able to create AdCampaigns with campaign objectives: Awareness, Traffic, Engagement, Lead Generation, or Conversions.

**FR-ADV-003:** Each campaign shall support multiple AdCreatives (image, video, carousel) with associated headlines, body text, CTAs, and destination URLs.

**FR-ADV-004:** Advertisers shall configure audience targeting per campaign: age range, gender, location, interests (inferred from platform behavior), device type, and custom/lookalike audiences.

**FR-ADV-005:** The system shall use a second-price auction model (Vickrey auction) for ad placement, where the winning bidder pays one cent above the second-highest bid.

**FR-ADV-006:** Ads shall be clearly labeled with a "Sponsored" tag and provide a "Why am I seeing this?" disclosure page linking to audience targeting criteria.

**FR-ADV-007:** The system shall track AdImpressions, clicks, click-through rate (CTR), cost-per-click (CPC), cost-per-mille (CPM), and conversion events for each creative.

**FR-ADV-008:** Advertisers shall have access to a self-serve dashboard with real-time campaign performance metrics, budget pacing, and spend breakdown.

---

### 2.14 Analytics & Insights

**FR-ANL-001:** Every user shall have access to a personal analytics dashboard showing: post reach, impressions, profile visits, follower growth, and top-performing content over selectable time windows (7, 28, 90 days).

**FR-ANL-002:** Creators with more than 1,000 followers shall unlock an advanced insights tier with demographic breakdowns of their audience (age range, gender, top countries/cities).

**FR-ANL-003:** The system shall provide per-post analytics: impressions, reach, engagement rate, reactions breakdown, comments count, shares, saves, and link clicks.

**FR-ANL-004:** Community admins shall see community-specific analytics: new members, post volume, top contributors, engagement rate, and retention (members active after 30 days).

**FR-ANL-005:** Analytics data shall be exportable in CSV format for users and advertisers, covering up to 2 years of historical data.

---

### 2.15 GDPR & Privacy

**FR-GDPR-001:** Users shall be able to download a complete export of all their personal data (posts, messages, profile data, activity logs) within 30 days of request, delivered as a structured ZIP archive.

**FR-GDPR-002:** Upon permanent account deletion, all PII shall be purged from primary databases within 30 days and from backup systems within 90 days, except where legal retention obligations apply.

**FR-GDPR-003:** The system shall present a clear, plain-language consent flow at registration covering data processing purposes; users must affirmatively opt in to optional processing (ads personalization, analytics sharing).

**FR-GDPR-004:** Users shall be able to access a Privacy Center showing: what data is collected, how it is used, third-party data sharing partners, and controls to opt out of each data use category.

**FR-GDPR-005:** The system shall support the Right to Rectification — users can correct inaccurate personal data from their profile settings.

**FR-GDPR-006:** The system shall support suppression lists — users who have requested deletion shall not be re-enrolled via imported contact lists or third-party sources.

**FR-GDPR-007:** The system shall log all consent events (grant, withdraw, modification) with timestamp, IP address, and user agent, retaining these logs for 5 years for compliance audits.

---

## 3. Non-Functional Requirements

### 3.1 Performance

**NFR-PERF-001:** The feed API endpoint shall return the first 20 feed items within 200 ms (p95) under normal load.

**NFR-PERF-002:** Post creation (text + up to 3 images) shall complete end-to-end (upload, processing, publish) within 3 seconds (p95) on a 10 Mbps connection.

**NFR-PERF-003:** Search queries shall return results within 300 ms (p95) for queries up to 50 characters.

**NFR-PERF-004:** Direct message delivery latency shall be under 100 ms (p95) for messages sent between users in the same geographic region.

**NFR-PERF-005:** Story expiry jobs shall run every 5 minutes and process all expired stories within 10 minutes of their expiry timestamp.

**NFR-PERF-006:** All API endpoints shall support a sustained throughput of at least 10,000 requests per second globally during peak traffic hours.

---

### 3.2 Scalability

**NFR-SCAL-001:** The platform architecture shall support horizontal scaling of all stateless services (API, feed ranking, notification) without code changes.

**NFR-SCAL-002:** The media storage layer shall scale to accommodate 10 petabytes of user-generated media without architectural redesign.

**NFR-SCAL-003:** The feed ranking system shall support re-ranking a user's feed for 500 million DAU within a 5-minute freshness window using a distributed stream processing pipeline.

**NFR-SCAL-004:** The database layer shall shard user, post, and message data by user ID using consistent hashing, supporting addition of shards with zero downtime.

**NFR-SCAL-005:** The WebSocket notification layer shall support 50 million concurrent connections distributed across a geographically distributed cluster.

---

### 3.3 Availability & Reliability

**NFR-AVAIL-001:** Core services (feed, messaging, post creation) shall maintain 99.95% monthly uptime, allowing no more than 21.9 minutes of unplanned downtime per month.

**NFR-AVAIL-002:** The platform shall deploy across a minimum of 3 geographic regions in active-active configuration, with automatic failover completing within 60 seconds.

**NFR-AVAIL-003:** All write operations (post creation, message send) shall be persisted durably via synchronous replication to at least 2 replicas before acknowledging success to the client.

**NFR-AVAIL-004:** The system shall implement circuit breakers on all external service dependencies (payment processor, CDN, ML inference) with graceful degradation modes.

**NFR-AVAIL-005:** Recovery Point Objective (RPO) for user data shall be ≤ 5 minutes; Recovery Time Objective (RTO) for full service restoration shall be ≤ 30 minutes.

---

### 3.4 Security

**NFR-SEC-001:** All data in transit shall be encrypted using TLS 1.3 or higher; TLS 1.0 and 1.1 shall be disabled.

**NFR-SEC-002:** All data at rest (databases, object storage, backups) shall be encrypted using AES-256.

**NFR-SEC-003:** Direct messages shall be protected with end-to-end encryption (Signal Protocol); the platform server shall not hold plaintext message keys.

**NFR-SEC-004:** All API endpoints shall enforce authentication via short-lived JWT access tokens (15-minute TTL) and long-lived refresh tokens (30-day TTL) stored in HttpOnly cookies.

**NFR-SEC-005:** The platform shall undergo a third-party penetration test at least annually and remediate Critical/High findings within 14 days of the test report.

**NFR-SEC-006:** PII fields (email, phone, date of birth) shall be stored hashed or tokenized in analytics and logging systems; raw PII shall never appear in application logs.

**NFR-SEC-007:** All administrative actions (bans, content removal, data exports) shall be recorded in an immutable, append-only audit log retained for 7 years.

---

### 3.5 Compliance

**NFR-COMP-001:** The platform shall comply with GDPR (EU), CCPA (California), LGPD (Brazil), and PIPEDA (Canada) data protection regulations.

**NFR-COMP-002:** The platform shall comply with COPPA by blocking registration for users who declare an age under 13; users under 18 shall be subject to restricted advertising targeting.

**NFR-COMP-003:** All payment and billing flows for the advertising platform shall comply with PCI DSS Level 1 standards.

**NFR-COMP-004:** CSAM detection shall integrate with NCMEC's CyberTipline and comply with 18 U.S.C. § 2258A reporting obligations within 24 hours of detection.

**NFR-COMP-005:** The platform shall publish a Transparency Report semi-annually disclosing: government data requests, content removal volumes by category, and account actions.

---

## 4. Scope Definition

### 4.1 MVP (Phase 1)

The MVP delivers the core social networking loop sufficient for user acquisition and retention validation.

| Feature Area | Included in MVP |
|---|---|
| User registration & login (email + Google OAuth) | ✅ |
| Basic profile (avatar, bio, username) | ✅ |
| Follow/unfollow (public profiles only) | ✅ |
| Text + photo posts | ✅ |
| Chronological following feed | ✅ |
| Likes and flat (non-threaded) comments | ✅ |
| Push and in-app notifications (follows, likes, comments) | ✅ |
| Basic hashtag parsing and hashtag pages | ✅ |
| 1:1 Direct messaging (unencrypted at MVP) | ✅ |
| Content reporting (spam, harassment) | ✅ |
| Manual moderation queue (basic) | ✅ |
| Mobile-responsive web application | ✅ |
| Stories (photo only, 24h expiry) | ✅ |

**MVP Exclusions:** ML feed ranking, polls, E2EE messaging, group chats, communities, advertising platform, advanced analytics, GDPR data export automation.

---

### 4.2 Phase 2

Phase 2 expands engagement depth, monetization infrastructure, and safety tooling.

| Feature Area | Phase 2 |
|---|---|
| ML-based "For You" feed ranking | ✅ |
| Threaded comments (3 levels) | ✅ |
| 6-reaction system | ✅ |
| Polls and quote posts | ✅ |
| Story interactive stickers (polls, questions) | ✅ |
| Story Highlights on profiles | ✅ |
| Group messaging (up to 50 members) | ✅ |
| E2EE for direct messages | ✅ |
| Communities (public, up to 50k members) | ✅ |
| Hashtag following | ✅ |
| Advanced search (users, posts, hashtags) | ✅ |
| Creator analytics dashboard | ✅ |
| Advertising platform (self-serve, basic targeting) | ✅ |
| Automated ML content moderation (nudity, spam) | ✅ |
| GDPR data export | ✅ |
| Native iOS and Android apps | ✅ |

---

### 4.3 Phase 3 (Future)

Phase 3 targets advanced creator tools, platform openness, and ecosystem expansion.

| Feature Area | Phase 3 |
|---|---|
| Short-form video (Reels, up to 90 seconds) | ✅ |
| Live streaming with real-time chat | ✅ |
| Creator monetization (tips, subscriptions, branded content) | ✅ |
| Group chats scaled to 250 members | ✅ |
| Community marketplace and events | ✅ |
| Advanced ad targeting (lookalike audiences, retargeting) | ✅ |
| Open API / Developer Platform | ✅ |
| Federated identity (ActivityPub support) | ✅ |
| AI-powered content creation tools | ✅ |
| Augmented reality filters for photos and stories | ✅ |
| Third-party app integrations and embeds | ✅ |
| Advanced misinformation detection pipeline | ✅ |

---

## 5. Constraints & Assumptions

### 5.1 Constraints

1. **Media Storage:** All user-uploaded media must be stored in a geo-redundant object storage service (e.g., AWS S3 multi-region) and served through a CDN for global performance.
2. **E2EE Messaging:** End-to-end encryption on messages means the platform cannot access message content for moderation. User-initiated reporting (client-side) is the only available signal.
3. **GDPR Residency:** EU user data must remain within EU-based data centers; cross-border data transfers require Standard Contractual Clauses (SCCs) or adequacy decisions.
4. **Third-Party ML:** CSAM detection must use NCMEC-approved hash-matching databases; the platform may not build independent CSAM detection models.
5. **App Store Policies:** Mobile app features, in-app purchases, and subscription billing must comply with Apple App Store and Google Play policies.
6. **Ad Targeting (Minors):** Behavioral and interest-based ad targeting is prohibited for users under 18 years old; only contextual targeting is permitted.

### 5.2 Assumptions

1. Users are expected to have a stable internet connection of at least 3 Mbps for standard features; video features require 5 Mbps or higher.
2. The platform will launch first in English with i18n architecture in place for future locale expansion.
3. Third-party OAuth providers (Google, Apple) will maintain their OAuth 2.0 APIs without breaking changes during the MVP launch window.
4. The advertising platform assumes a minimum 6-month ramp period before ad revenue is expected to offset infrastructure costs.
5. The engineering team will deploy on a major cloud provider (AWS, GCP, or Azure) with managed Kubernetes for container orchestration.
6. Legal and compliance review will be completed prior to launch in each jurisdiction; the requirements team will update this document if regulatory review mandates feature changes.
