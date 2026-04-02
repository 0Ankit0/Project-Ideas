# Requirements Document — Knowledge Base Platform

**Version:** 1.0  
**Date:** 2025-01-01  
**Status:** Approved  
**Owner:** Product Management

---

## 1. Project Overview

The Knowledge Base Platform (KBP) is a SaaS product that provides organizations with a unified system for creating, managing, and publishing structured knowledge — covering internal team wikis, external customer help centers, AI-powered semantic search, article versioning, and embeddable in-app help widgets. The platform serves both technical and non-technical teams, enabling collaborative content authoring with an editorial approval workflow, rich-text editing, contextual AI assistance, and deep analytics to measure content effectiveness.

### 1.1 Scope

**In Scope:**
- Multi-workspace knowledge base with hierarchical space/collection/article structure
- Rich-text article authoring with TipTap editor, versioning, and diff views
- Editorial workflow (Draft → In Review → Approved → Published → Archived)
- Full-text and semantic hybrid search powered by Elasticsearch and pgvector
- AI Q&A assistant, article summarization, auto-tagging, and gap detection
- Five-role RBAC with SSO (SAML 2.0 / OIDC) support
- Embeddable JavaScript help widget with contextual suggestions and AI chat
- Per-article helpfulness ratings and comment-thread feedback
- Multi-workspace management with custom domains and branding
- Analytics dashboard with deflection, engagement, and authorship metrics
- Integrations with Slack, Zendesk, GitHub, Jira, Zapier, REST/GraphQL APIs

**Out of Scope:**
- Video hosting (video embeds via YouTube/Vimeo URL are supported; direct video upload is not)
- Live chat / ticketing system (integration only, not native)
- Mobile native applications (responsive web only)
- On-premise self-hosted deployment in v1

---

## 2. Stakeholders

| Stakeholder | Role | Interests |
|---|---|---|
| Engineering Lead | Technical Decision Maker | Scalable architecture, clean APIs, testability |
| Product Manager | Scope & Prioritization Owner | Feature completeness, delivery timelines |
| UX Designer | Interface & Usability Owner | Intuitive authoring experience, accessibility |
| Content Operations Lead | Primary Author/Editor User | Workflow efficiency, bulk management tools |
| Customer Success | Voice of External Reader | Fast search, accurate AI answers, easy navigation |
| Security / Compliance | Risk Owner | GDPR, SOC 2, SSO, audit logs |
| DevOps / SRE | Infrastructure Owner | Deployment, uptime, observability |
| CTO / Executive Sponsor | Business Owner | ROI, scalability, competitive differentiation |

---

## 3. Functional Requirements

### 3.1 Content Authoring (FR-CA)

| ID | Requirement | Priority | Notes |
|---|---|---|---|
| FR-CA-001 | The system shall provide a TipTap-based rich-text editor supporting headings (H1–H4), bold, italic, underline, strikethrough, inline code, blockquotes, ordered/unordered lists, and tables. | MH | TipTap StarterKit + custom extensions |
| FR-CA-002 | The system shall support slash-command palette (`/`) to insert block types: image, callout, code block, divider, toggle list, and embed (YouTube/Vimeo/Figma). | H | Custom TipTap extension |
| FR-CA-003 | The system shall autosave article drafts every 30 seconds and on tab-blur, preserving unsaved changes in localStorage as a fallback. | MH | Debounced save + offline queue |
| FR-CA-004 | The system shall maintain a complete version history for every article, storing a snapshot of the TipTap JSON document on each publish event. | MH | Version table with diff computed on read |
| FR-CA-005 | Authors shall be able to view a visual diff between any two article versions, with additions highlighted green and deletions highlighted red at the block level. | H | Server-side diff using `diff` library |
| FR-CA-006 | The system shall support inline comments on any selected text range within an article, with threaded replies, resolution, and re-open capabilities. | H | Comment anchors stored as document ranges |
| FR-CA-007 | Authors shall be able to upload images, PDFs, and files up to 50 MB directly within the editor; files are stored in AWS S3 and served via CloudFront. | MH | Pre-signed S3 upload URL flow |
| FR-CA-008 | The system shall provide a content template library (minimum 10 built-in templates: FAQ, How-To, Release Note, Troubleshooting, API Reference, Policy, Meeting Note, Runbook, Onboarding, Changelog). | H | Templates stored as TipTap JSON presets |
| FR-CA-009 | Authors shall be able to duplicate any existing article as a new draft, retaining all content, tags, and metadata (excluding version history and comments). | M | Copy-on-write in database |
| FR-CA-010 | The system shall display a real-time word count, estimated reading time (at 238 WPM), and SEO meta score (title length, meta description, heading structure) in the editor sidebar. | M | Client-side computation |

### 3.2 Knowledge Organization (FR-KO)

| ID | Requirement | Priority | Notes |
|---|---|---|---|
| FR-KO-001 | The system shall support a three-level hierarchy: Workspace → Space → Collection → Article. Each level must support an icon, description, and visibility setting. | MH | Adjacency list model in Postgres |
| FR-KO-002 | Articles and collections shall be reorderable via drag-and-drop within their parent, with positions persisted as fractional indices to avoid bulk re-numbering. | H | `position` column, LexoRank or similar |
| FR-KO-003 | The system shall support user-defined tags with autocomplete; each article can have up to 20 tags; tags are workspace-scoped. | H | Tag table with workspace_id FK |
| FR-KO-004 | Authors shall be able to create bidirectional cross-links between articles using `[[article title]]` wiki-link syntax, resolved at render time with hover preview. | H | Reference table tracking link pairs |
| FR-KO-005 | The system shall auto-generate a table of contents for any article containing 2 or more heading blocks, displayed as a sticky sidebar on the reader view. | M | Derived from TipTap heading nodes |
| FR-KO-006 | Editors shall be able to set an article's visibility to one of: Public (unauthenticated access), Internal (authenticated workspace members only), or Private (specific roles/users only). | MH | Visibility enum + ACL entries |
| FR-KO-007 | The system shall surface "Related Articles" (up to 5) at the bottom of each article page, computed using cosine similarity of stored pgvector embeddings. | H | Computed async after publish |
| FR-KO-008 | Workspace Admins shall be able to configure a "Featured Articles" section on the workspace home, pinning up to 12 articles or collections. | M | Featured table with ordering |

### 3.3 Search (FR-SR)

| ID | Requirement | Priority | Notes |
|---|---|---|---|
| FR-SR-001 | The system shall provide a global search bar accessible from any page via keyboard shortcut `Cmd/Ctrl+K`, returning results within 300 ms for the p95 case. | MH | Elasticsearch instant search |
| FR-SR-002 | Search shall cover article titles, body content, tags, and author names, with configurable field boosting (title × 3, tags × 2, body × 1). | MH | Elasticsearch multi_match query |
| FR-SR-003 | The system shall support typo-tolerant full-text search with fuzziness auto-correction (edit distance 1 for terms ≤ 8 chars, distance 2 for longer terms). | H | Elasticsearch fuzziness parameter |
| FR-SR-004 | Search results shall support faceted filtering by: Space, Collection, Tags, Author, Status (Published/Archived), and Date range. | H | Elasticsearch aggregations |
| FR-SR-005 | The system shall implement hybrid search combining BM25 full-text (weight 0.6) and pgvector cosine similarity (weight 0.4), re-ranked using Reciprocal Rank Fusion. | H | Dual query, RRF merge in application layer |
| FR-SR-006 | The system shall log all search queries, result counts, and click-through positions to support "search-no-result" analytics and ongoing relevance tuning. | H | Async event to analytics pipeline |
| FR-SR-007 | The system shall display autocomplete suggestions (up to 8) in a dropdown as the user types, populated from Elasticsearch completion suggester on indexed titles and tags. | H | Completion suggester with edge n-grams |
| FR-SR-008 | Search shall respect article visibility and workspace membership — authenticated users see internal articles; unauthenticated users see only public articles. | MH | Elasticsearch query-time filter by visibility + workspace |

### 3.4 AI Assistant (FR-AI)

| ID | Requirement | Priority | Notes |
|---|---|---|---|
| FR-AI-001 | The system shall provide an AI Q&A chat interface that answers user questions using retrieval-augmented generation (RAG) over the workspace's published articles. | MH | LangChain.js + GPT-4o + pgvector retrieval |
| FR-AI-002 | The AI assistant shall cite the source articles used to generate each answer, displaying article titles as clickable links with the relevant passage highlighted. | MH | Source documents returned from LangChain retrieval chain |
| FR-AI-003 | The system shall offer a one-click "Summarize" action on any article, producing a 3–5 sentence plain-language summary stored in the article metadata. | H | GPT-4o summarization prompt, cached in DB |
| FR-AI-004 | The system shall auto-suggest up to 5 tags for a newly created article based on its content, using GPT-4o with a structured JSON output schema. | H | Author can accept/reject individual suggestions |
| FR-AI-005 | The system shall detect "content gaps" — search queries with zero results — and weekly generate a list of suggested article titles for Editors to commission. | M | Cron job, stored in gap_suggestions table |
| FR-AI-006 | Authors shall be able to invoke "AI Draft" by providing a topic prompt (≤ 500 chars); the system generates a structured article outline and body as a new draft. | H | GPT-4o with article-structure system prompt |
| FR-AI-007 | The AI assistant shall support multi-turn conversation, maintaining context for up to 10 prior turns within a single session using LangChain ConversationBufferWindowMemory. | H | Session stored in Redis with 1-hour TTL |
| FR-AI-008 | Workspace Admins shall be able to enable or disable individual AI features (Q&A, summarization, auto-tagging, gap detection, draft generation) independently per workspace. | M | Feature flags per workspace in DB |

### 3.5 Access Control (FR-AC)

| ID | Requirement | Priority | Notes |
|---|---|---|---|
| FR-AC-001 | The system shall implement five roles: Reader, Author, Editor, Workspace Admin, Super Admin, applied at the workspace level with additive permissions. | MH | RBAC with role enum in member table |
| FR-AC-002 | The system shall support SSO via SAML 2.0 and OIDC, with configurable identity provider (IdP) metadata per workspace. | MH | Passport.js SAML + OIDC strategies |
| FR-AC-003 | The system shall enforce JWT-based authentication with access tokens (15-minute expiry) and rotating refresh tokens (30-day expiry, stored in HttpOnly cookies). | MH | NestJS Guards + Passport JWT strategy |
| FR-AC-004 | Article-level visibility overrides shall allow Editors to grant specific users or roles access to Private articles beyond their workspace-level role. | H | ACL entries in article_permissions table |
| FR-AC-005 | The system shall support IP allowlisting per workspace, blocking API and UI access from non-allowed IP ranges with a 403 response. | H | NestJS middleware + Redis IP cache |
| FR-AC-006 | All sensitive actions (role changes, workspace deletion, article publication, SSO configuration) shall be recorded in an immutable audit log with actor, timestamp, and before/after values. | MH | audit_log table, append-only, no UPDATE/DELETE |
| FR-AC-007 | The system shall enforce rate limiting: 100 req/min per authenticated user, 20 req/min per unauthenticated IP, 10 AI requests/min per user, with 429 responses and Retry-After headers. | MH | NestJS ThrottlerModule backed by Redis |
| FR-AC-008 | Super Admins shall be able to impersonate any workspace member for debugging, with all impersonated actions clearly attributed in the audit log as `actor_id (impersonated by super_admin_id)`. | M | Impersonation token with embedded impersonator ID |

### 3.6 In-App Help Widget (FR-WG)

| ID | Requirement | Priority | Notes |
|---|---|---|---|
| FR-WG-001 | The system shall provide a self-contained JavaScript widget bundle (≤ 50 KB gzipped) embeddable via a single `<script>` tag with a `data-workspace-token` attribute. | MH | Vite-bundled vanilla JS, served from CloudFront |
| FR-WG-002 | The widget shall display context-aware article suggestions based on the host page's URL path and page title, matching against indexed article metadata using Elasticsearch. | MH | URL pattern → collection mapping configured in workspace settings |
| FR-WG-003 | The widget shall include a full search overlay with instant results powered by the workspace's Elasticsearch index, respecting public/internal visibility. | H | Widget uses a scoped read-only API key |
| FR-WG-004 | The widget shall embed the AI chat interface, allowing Readers to ask questions and receive RAG-generated answers without leaving the host application. | H | Proxied through widget API endpoint, rate limited |
| FR-WG-005 | Workspace Admins shall be able to customize widget appearance: primary color, launcher icon (from preset library or custom SVG upload), widget title, and position (bottom-left / bottom-right). | M | Customization stored in workspace_widget_config table |
| FR-WG-006 | The widget shall send helpfulness feedback (👍/👎) per article viewed, recorded against the anonymous session ID (no PII stored for unauthenticated users). | M | POST to /api/feedback/widget endpoint |

### 3.7 Customer Feedback (FR-FB)

| ID | Requirement | Priority | Notes |
|---|---|---|---|
| FR-FB-001 | Each published article shall display a "Was this helpful?" prompt (thumbs up / thumbs down) and record the response against the article and optional session/user ID. | MH | article_feedback table |
| FR-FB-002 | Authenticated readers shall be able to submit inline comment threads on any paragraph of a published article, with threaded replies up to 3 levels deep. | H | Separate from authoring inline comments |
| FR-FB-003 | The system shall automatically alert Editors (via in-app notification and optional email) when an article's rolling 30-day helpfulness score drops below a configurable threshold (default: 60%). | H | BullMQ scheduled job, threshold in workspace settings |
| FR-FB-004 | Workspace Admins shall be able to configure integration with Zendesk or Intercom so that submitted feedback comments can be escalated as support tickets with a single click. | M | OAuth 2.0 integration with Zendesk/Intercom APIs |
| FR-FB-005 | The system shall collect optional free-text feedback ("What could be improved?") after a thumbs-down response, with a 500-character limit. | H | free_text column in article_feedback |
| FR-FB-006 | Editors shall be able to view a consolidated Feedback inbox showing unresolved comments and low-rated articles, filterable by space, date, and rating score. | H | Dedicated /feedback route in dashboard |

### 3.8 Multi-workspace (FR-WS)

| ID | Requirement | Priority | Notes |
|---|---|---|---|
| FR-WS-001 | The system shall support creation of multiple isolated workspaces, each with its own members, content, settings, and analytics data. | MH | workspace_id FK on all tenant-scoped tables |
| FR-WS-002 | Each workspace shall support a custom subdomain (`{slug}.kb.example.com`) and optionally a fully custom domain via CNAME configuration. | MH | Route 53 + CloudFront per-distribution or SNI-based routing |
| FR-WS-003 | Workspace Admins shall be able to configure custom branding: logo (PNG/SVG, max 2 MB), primary/secondary color palette, and custom CSS injection (max 10 KB). | H | Stored in workspace_branding table, served via CloudFront |
| FR-WS-004 | Super Admins shall be able to create, suspend, and permanently delete workspaces; deletion requires a 30-day grace period with data export option. | MH | Soft-delete with scheduled purge job |
| FR-WS-005 | The system shall support cross-workspace article sharing, allowing specific articles to be read-only mirrored to another workspace, with original workspace retaining edit ownership. | M | article_shares table with source/target workspace_id |
| FR-WS-006 | Each workspace shall have configurable member limits and storage quotas enforced at the API layer, with overage warnings at 80% and hard blocks at 100%. | H | Quota table with counters updated via triggers |
| FR-WS-007 | Workspace Admins shall be able to export all workspace content as a structured ZIP archive containing Markdown files, metadata JSON, and media assets. | H | BullMQ export job, result stored in S3, emailed to requester |
| FR-WS-008 | The system shall provide a workspace activity feed showing recent publishes, member joins, role changes, and integration events, paginated and filterable. | M | Derived from audit_log with workspace_id filter |

### 3.9 Analytics (FR-AN)

| ID | Requirement | Priority | Notes |
|---|---|---|---|
| FR-AN-001 | The system shall track article page views, unique visitors (by session hash), time-on-page, and scroll depth for all published articles. | MH | Client-side beacon API, server-side aggregation |
| FR-AN-002 | The system shall compute and display article-level helpfulness scores (% positive ratings over configurable rolling windows: 7 / 30 / 90 days). | MH | Aggregated in analytics pipeline |
| FR-AN-003 | The system shall track and report "search-no-result" queries — searches returning zero results — grouped by query term, ranked by frequency. | MH | Logged from FR-SR-006 events |
| FR-AN-004 | The system shall track widget deflection: the ratio of users who viewed a help article via the widget and did not submit a support ticket (requires Zendesk integration). | H | Linked via session ID across widget and Zendesk |
| FR-AN-005 | The system shall display an Author Contribution report showing articles created, edited, published per author over time, with comparison to workspace averages. | H | Per-author aggregation |
| FR-AN-006 | The system shall provide a Search Analytics view showing top queries, click-through rates, and mean result position for clicked articles. | H | Click events from search results |
| FR-AN-007 | Workspace Admins shall be able to export any analytics report as CSV or PDF, generated asynchronously via a BullMQ job and delivered via download link. | M | BullMQ job, S3 storage, email notification |
| FR-AN-008 | The system shall display real-time active readers (last 5 minutes) per article using Redis sorted sets, shown as a live badge on article cards in the dashboard. | M | Redis ZADD with 5-min expiry, SSE to dashboard |

### 3.10 Integrations (FR-IN)

| ID | Requirement | Priority | Notes |
|---|---|---|---|
| FR-IN-001 | The system shall send a Slack notification to a configured channel when an article is Published or Archived, including title, author, space, and direct link. | H | Slack Incoming Webhooks |
| FR-IN-002 | The system shall integrate with Zendesk to sync article deflection data and allow feedback escalation to tickets (FR-FB-004). | H | Zendesk REST API v2, OAuth 2.0 |
| FR-IN-003 | The system shall support embedding GitHub code snippets within articles by URL, with syntax highlighting and auto-refresh on file change via webhook. | M | GitHub REST API + article webhook handler |
| FR-IN-004 | The system shall allow articles to be linked to Jira issues, displaying issue status, assignee, and last-updated in an article sidebar card. | M | Jira Cloud REST API, OAuth 2.0 |
| FR-IN-005 | The system shall expose outbound Zapier webhooks triggered by events: article published, article archived, feedback submitted, member invited. | H | Webhook table, BullMQ delivery with retry |
| FR-IN-006 | The system shall provide a versioned REST API (v1) covering all content, search, analytics, and workspace management operations, documented with OpenAPI 3.1. | MH | NestJS Swagger module |
| FR-IN-007 | The system shall provide a GraphQL API endpoint supporting queries for articles, spaces, collections, and analytics aggregates, with cursor-based pagination. | H | NestJS GraphQL module, DataLoader for N+1 prevention |
| FR-IN-008 | The system shall support inbound webhook handlers for Zendesk (ticket resolved → trigger article suggestion), GitHub (push event → refresh embedded snippet), and Jira (issue closed → notify linked article authors). | M | Signed webhook verification for each platform |

---

## 4. Non-Functional Requirements

| ID | Category | Requirement | Target |
|---|---|---|---|
| NFR-001 | Performance | API p95 response time for read endpoints (article fetch, search) | ≤ 300 ms |
| NFR-002 | Performance | API p95 response time for write endpoints (save draft, publish) | ≤ 600 ms |
| NFR-003 | Performance | AI Q&A first-token latency (streaming) | ≤ 2 000 ms |
| NFR-004 | Scalability | System shall support 500 concurrent active users per workspace without degradation | Horizontal ECS Fargate scaling |
| NFR-005 | Scalability | Elasticsearch index shall support 10 million article documents per deployment | Sharding strategy defined in elasticsearch-mappings.md |
| NFR-006 | Availability | Platform uptime SLA | 99.9% monthly (API + frontend) |
| NFR-007 | Availability | Help widget CDN uptime | 99.99% (CloudFront) |
| NFR-008 | Security | All API traffic encrypted in transit | TLS 1.3 minimum |
| NFR-009 | Security | Secrets stored in AWS Secrets Manager; no secrets in environment variables or code | Enforced by CI/CD scan |
| NFR-010 | Accessibility | Public knowledge base and widget shall conform to WCAG 2.1 Level AA | Automated axe-core checks in CI |
| NFR-011 | Privacy | GDPR Article 17 right-to-erasure requests processed within 30 days | Erasure job in admin panel |
| NFR-012 | Observability | All services emit structured JSON logs, traces (OpenTelemetry), and metrics (Prometheus) | Sent to AWS CloudWatch + X-Ray |

---

## 5. Constraints

- **Budget:** Infrastructure costs must not exceed $4 000/month at initial launch scale (< 10 000 MAU).
- **Timeline:** MVP (phases 1–3) must ship within 16 weeks of project kick-off.
- **Compliance:** Must comply with GDPR (EU), CCPA (California), and be on a SOC 2 Type II roadmap.
- **Browser Support:** Chrome 110+, Firefox 115+, Safari 16+, Edge 110+. IE11 not supported.
- **Accessibility:** WCAG 2.1 Level AA for all public-facing surfaces.
- **LLM Vendor Lock-in:** The AI layer must be abstracted via LangChain.js so the underlying model can be swapped with < 1 week of engineering effort.

---

## 6. Assumptions

- The platform is deployed exclusively on AWS; multi-cloud is not a v1 requirement.
- Article content is authored in English for v1; i18n infrastructure (i18next) will be scaffolded but translations are out of scope.
- Real-time collaborative editing (Conflict-free Replicated Data Types / OT) is out of scope for v1; autosave with optimistic locking is sufficient.
- OpenAI API keys are managed at the platform level; per-workspace BYOK (Bring Your Own Key) is a v2 feature.
- Elasticsearch indices are managed via Amazon OpenSearch Service; self-managed Elasticsearch is not supported.

---

## 7. Acceptance Criteria Examples

**FR-CA-004 (Version History):**
- GIVEN a published article, WHEN an Editor publishes a new version, THEN a version record is created containing the full TipTap JSON snapshot, the actor ID, and a UTC timestamp.
- GIVEN two version IDs, WHEN a user requests a diff, THEN the response returns an array of block-level change objects with type `added`, `removed`, or `unchanged`.

**FR-SR-005 (Hybrid Search):**
- GIVEN a query "how to reset password", WHEN the hybrid search is executed, THEN results are ranked by RRF score combining BM25 (0.6) and cosine similarity (0.4), with the top result being the most relevant article in the workspace.
- GIVEN an authenticated user in workspace A, WHEN searching, THEN results from workspace B are never returned.

**FR-AI-001 (AI Q&A):**
- GIVEN a published article corpus, WHEN a user asks a question directly answered in one article, THEN the AI response contains the correct answer and cites the source article title.
- GIVEN AI features are disabled for a workspace, WHEN a user attempts to access the AI chat, THEN a 403 response is returned with message "AI features are disabled for this workspace."

---

## 8. Operational Policy Addendum

### 8.1 Content Governance Policies

All articles must pass through the full editorial lifecycle (Draft → In Review → Approved → Published) before public visibility. Editors must respond to review requests within 5 business days. Articles idle in review for more than 10 business days trigger an escalation notification to the Workspace Admin. Published articles are retained indefinitely; Workspace Admins may configure archive retention policies with a minimum window of 6 months. Audit logs of all content mutations are retained for 24 months and are non-deletable by Workspace Admins.

### 8.2 Reader Data Privacy Policies

Reader PII is processed under GDPR and CCPA. IP addresses are truncated before analytics storage. User-agent strings are parsed for OS/browser family only. Session IDs are daily-rotated salted hashes. Cookie consent banners are displayed for EU/EEA/UK visitors before any non-essential cookies are set. Individual reader journeys are accessible only to Super Admins for fraud investigation; Workspace Admins see aggregate metrics only.

### 8.3 AI Usage Policies

Article content sent to OpenAI is governed by the OpenAI Enterprise DPA; content is not used for model training. PII is stripped from prompts via regex + NER pre-processing. AI feature toggles are available at workspace level and per-article level. AI API responses are not persisted beyond the request lifecycle unless explicitly cached. Prompt construction logic must never reintroduce PII fields from user profiles.

### 8.4 System Availability Policies

API/frontend SLA: 99.9% monthly uptime. AI Assistant SLA: 99.5% (dependent on OpenAI API). Widget CDN SLA: 99.99%. RTO: ≤ 1 hour. RPO: ≤ 15 minutes (RDS Multi-AZ + WAL shipping). Severity 1 incidents require on-call engineer within 5 minutes, status page update within 10 minutes, and customer communication within 30 minutes. Post-incident reviews mandatory for Severity 1 and 2 events, published within 5 business days.
