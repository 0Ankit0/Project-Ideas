# Social Networking Platform

A production-grade social networking platform enabling users to connect, share content, discover communities, and communicate in real time. The platform supports multi-format content creation, ML-powered feed ranking, content moderation, advertising, and robust privacy controls.

## Overview

The Social Networking Platform is a full-stack distributed system designed for scale, supporting millions of concurrent users. It provides the core pillars of modern social media: social graph management, content publishing, real-time feeds, direct messaging, stories, live streaming, community management, and an advertising engine.

## Key Features

- **User Profiles & Social Graph** — Follow/friend connections, blocking, muting, account verification
- **Multi-Format Content** — Text posts, photos, videos, polls, stories (24h expiry), reels, live streams
- **ML-Powered News Feed** — Fan-out architecture, engagement-based ranking, content diversity
- **Hashtags & Discovery** — Trending topics, hashtag following, search, recommendations
- **Direct Messaging** — 1:1 and group chats with media support and read receipts
- **Reactions & Comments** — Nested comments, emoji reactions (like/love/laugh/sad/angry)
- **Notifications** — Push (FCM/APNs), in-app, and email with per-user preferences
- **Stories with 24h Expiry** — Ephemeral content with viewer tracking and highlights
- **Community Management** — Public/private groups, member roles, community posts
- **Content Moderation** — AI-assisted detection + human review queue + appeal flow
- **Advertising Platform** — Campaign management, ad creatives, impression tracking, targeting
- **User Safety** — Block/mute/report, GDPR data export/deletion, privacy settings
- **Analytics** — Creator insights, business account analytics, engagement metrics
- **Account Verification** — Blue checkmark for public figures and businesses

## Getting Started

- Review [`traceability-matrix.md`](./traceability-matrix.md) first to navigate requirement-to-implementation coverage across phases.
### Prerequisites
- Node.js 20+ / Python 3.11+ (backend services)
- PostgreSQL 15+, Redis 7+, Apache Kafka 3+
- Docker & Kubernetes (deployment)
- AWS S3 or compatible object storage (media)

### Quick Start
1. Clone the repository
2. Review `requirements/requirements.md` for functional and non-functional requirements
3. Review `analysis/` for use cases, data dictionary, and business rules
4. Review `high-level-design/` for architecture and domain model
5. Review `detailed-design/` for API specs, database schema, and class diagrams
6. Review `infrastructure/` for deployment topology

### Documentation Navigation
| Audience | Start Here |
|---|---|
| Product Manager | `requirements/requirements.md`, `requirements/user-stories.md` |
| Architect | `high-level-design/architecture-diagram.md`, `high-level-design/c4-diagrams.md` |
| Backend Engineer | `detailed-design/api-design.md`, `detailed-design/erd-database-schema.md` |
| DevOps Engineer | `infrastructure/deployment-diagram.md`, `infrastructure/cloud-architecture.md` |
| ML Engineer | `detailed-design/feed-ranking-and-recommendation.md` |
| QA Engineer | `edge-cases/` directory |

## Documentation Structure

Project root artifact: [`traceability-matrix.md`](./traceability-matrix.md) provides cross-phase requirement-to-implementation linkage.


```
Social Networking Platform/
├── README.md                          ← This file
├── traceability-matrix.md
├── requirements/
│   ├── requirements.md                ← Functional & non-functional requirements (REQ-XXX)
│   └── user-stories.md                ← User stories with acceptance criteria (US-XXX)
├── analysis/
│   ├── use-case-diagram.md            ← Mermaid use-case flowcharts
│   ├── use-case-descriptions.md       ← Detailed use case narratives
│   ├── system-context-diagram.md      ← C4 context diagram
│   ├── activity-diagrams.md           ← Activity flow diagrams
│   ├── swimlane-diagrams.md           ← Cross-actor swimlane diagrams
│   ├── data-dictionary.md             ← Entity definitions and attribute tables
│   ├── business-rules.md              ← Enforceable business rules
│   └── event-catalog.md               ← Domain events and SLOs
├── high-level-design/
│   ├── system-sequence-diagrams.md    ← System-level sequence diagrams
│   ├── domain-model.md                ← Domain class diagram
│   ├── data-flow-diagrams.md          ← DFDs level 0 and level 1
│   ├── architecture-diagram.md        ← High-level system architecture
│   └── c4-diagrams.md                 ← C4 Context + Container diagrams
├── detailed-design/
│   ├── class-diagrams.md              ← OOP class diagrams per domain
│   ├── sequence-diagrams.md           ← Detailed interaction sequences
│   ├── state-machine-diagrams.md      ← Lifecycle state machines
│   ├── erd-database-schema.md         ← Full ERD + SQL DDL
│   ├── component-diagrams.md          ← Service component breakdowns
│   ├── api-design.md                  ← REST API reference
│   ├── c4-component-diagram.md        ← C4 Component diagrams
│   └── feed-ranking-and-recommendation.md ← ML feed ranking deep dive
├── infrastructure/
│   ├── deployment-diagram.md          ← Kubernetes + cloud deployment
│   ├── network-infrastructure.md      ← VPC, CDN, security groups
│   └── cloud-architecture.md          ← Multi-region cloud design
├── implementation/
│   ├── implementation-guidelines.md   ← Coding patterns and guidelines
│   ├── c4-code-diagram.md             ← C4 Code-level diagram
│   └── backend-status-matrix.md       ← Service/endpoint status tracker
└── edge-cases/
    ├── README.md                      ← Edge case overview
    ├── content-moderation.md          ← Moderation edge cases
    ├── feed-ranking.md                ← Feed/ranking edge cases
    ├── notification-storms.md         ← Notification edge cases
    ├── account-compromise.md          ← Security edge cases
    ├── api-and-ui.md                  ← API/UI edge cases
    ├── security-and-compliance.md     ← GDPR/legal edge cases
    └── operations.md                  ← Operational edge cases
```

## Documentation Status

- ✅ Traceability coverage is available via [`traceability-matrix.md`](./traceability-matrix.md).
| Document | Status | Last Updated |
|---|---|---|
| requirements/requirements.md | Complete | 2024-01 |
| requirements/user-stories.md | Complete | 2024-01 |
| analysis/use-case-diagram.md | Complete | 2024-01 |
| analysis/use-case-descriptions.md | Complete | 2024-01 |
| analysis/system-context-diagram.md | Complete | 2024-01 |
| analysis/activity-diagrams.md | Complete | 2024-01 |
| analysis/swimlane-diagrams.md | Complete | 2024-01 |
| analysis/data-dictionary.md | Complete | 2024-01 |
| analysis/business-rules.md | Complete | 2024-01 |
| analysis/event-catalog.md | Complete | 2024-01 |
| high-level-design/system-sequence-diagrams.md | Complete | 2024-01 |
| high-level-design/domain-model.md | Complete | 2024-01 |
| high-level-design/data-flow-diagrams.md | Complete | 2024-01 |
| high-level-design/architecture-diagram.md | Complete | 2024-01 |
| high-level-design/c4-diagrams.md | Complete | 2024-01 |
| detailed-design/class-diagrams.md | Complete | 2024-01 |
| detailed-design/sequence-diagrams.md | Complete | 2024-01 |
| detailed-design/state-machine-diagrams.md | Complete | 2024-01 |
| detailed-design/erd-database-schema.md | Complete | 2024-01 |
| detailed-design/component-diagrams.md | Complete | 2024-01 |
| detailed-design/api-design.md | Complete | 2024-01 |
| detailed-design/c4-component-diagram.md | Complete | 2024-01 |
| detailed-design/feed-ranking-and-recommendation.md | Complete | 2024-01 |
| infrastructure/deployment-diagram.md | Complete | 2024-01 |
| infrastructure/network-infrastructure.md | Complete | 2024-01 |
| infrastructure/cloud-architecture.md | Complete | 2024-01 |
| implementation/implementation-guidelines.md | Complete | 2024-01 |
| implementation/c4-code-diagram.md | Complete | 2024-01 |
| implementation/backend-status-matrix.md | Complete | 2024-01 |
| edge-cases/README.md | Complete | 2024-01 |
| edge-cases/content-moderation.md | Complete | 2024-01 |
| edge-cases/feed-ranking.md | Complete | 2024-01 |
| edge-cases/notification-storms.md | Complete | 2024-01 |
| edge-cases/account-compromise.md | Complete | 2024-01 |
| edge-cases/api-and-ui.md | Complete | 2024-01 |
| edge-cases/security-and-compliance.md | Complete | 2024-01 |
| edge-cases/operations.md | Complete | 2024-01 |

## Domain Entities

**Core:** User, UserProfile, UserCredential, Follow, Block, FriendRequest  
**Content:** Post, PostMedia, PostTag, Mention, Poll, Story, Reel, Comment, Reaction, Share, Repost  
**Discovery:** Hashtag, HashtagFollow, Feed, FeedItem, FeedRanking  
**Messaging:** DirectMessage, GroupChat, GroupChatMember  
**Notifications:** Notification, NotificationPreference  
**Moderation:** ContentReport, ModerationQueue, BanRecord  
**Community:** Community, CommunityMember, CommunityPost  
**Ads:** Advertiser, AdCampaign, AdCreative, AdImpression  

## Technology Stack

| Layer | Technology |
|---|---|
| API Gateway | Kong / AWS API Gateway |
| Backend Services | Node.js (TypeScript) / Python |
| Primary Database | PostgreSQL 15 |
| Cache | Redis 7 Cluster |
| Feed Store | Apache Cassandra / DynamoDB |
| Message Queue | Apache Kafka |
| Search | Elasticsearch |
| Media Storage | AWS S3 + CloudFront CDN |
| Container Orchestration | Kubernetes (EKS) |
| Service Mesh | Istio |
| Observability | Prometheus + Grafana + Jaeger |
