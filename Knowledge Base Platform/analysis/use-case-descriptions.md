# Use-Case Descriptions — Knowledge Base Platform

## Overview

This document provides detailed structured descriptions for the ten most critical use cases
identified in the Knowledge Base Platform. Each description follows a standardised template
aligned with UML 2.5 use-case specification guidelines and references business rules (BR-*)
defined in `business-rules.md` and non-functional requirements (NFR-*).

---

## UC-001 — Create Article

| Field | Value |
|---|---|
| **UC-ID** | UC-001 |
| **Name** | Create Article |
| **Actor(s)** | Author (primary), Editor (secondary – can also create) |
| **Priority** | Critical |

### Preconditions
- The actor is authenticated with at minimum the Author role in the target workspace.
- The workspace is in `active` billing status.
- The actor has write permission on at least one collection.

### Postconditions
- A new `Article` record exists in state `draft` with a UUID, creation timestamp, and the
  actor's user ID set as `createdBy`.
- An `ArticleVersion` record (version 1) is persisted, capturing the initial content snapshot.
- An `article.drafted` domain event is published to the event bus.
- The article appears in the author's private drafts list but is not indexed in Elasticsearch.

### Main Flow
1. Actor navigates to **New Article** in the workspace dashboard.
2. System presents the TipTap rich-text editor with an empty canvas and a title input field.
3. Actor enters a title (minimum 5 characters).
4. Actor authors the body content using the editor toolbar (headings, lists, code blocks,
   callouts, embeds).
5. System autosaves the draft every 30 seconds (include UC-002).
6. Actor optionally attaches media files (extend UC-004).
7. Actor fills in tags and metadata fields (include UC-005).
8. Actor clicks **Save Draft**.
9. System validates title length and at least one collection assignment (BR-CA-001).
10. System persists the Article and ArticleVersion records and emits `article.drafted`.
11. System displays a confirmation toast: *"Draft saved"* with a link to the article.

### Alternative Flows
- **AF-001A — Import from Markdown:** At step 2, actor selects *Import from Markdown*. System
  parses the uploaded `.md` file and populates the editor. Flow continues from step 3.
- **AF-001B — Duplicate Existing Article:** Actor selects *Duplicate* on an existing article.
  System creates a new draft with identical content and a title suffix *(Copy)*. Flow continues
  from step 7.
- **AF-001C — AI Draft Assist:** At step 4, actor clicks *Generate with AI*. System invokes
  the AI assistant to produce a structured draft from the title. Flow continues from step 5.

### Exception Flows
- **EF-001A — Autosave Failure:** If the autosave POST call fails (network error or 5xx),
  the system retries up to 3 times with exponential backoff. If all retries fail, a banner
  warns the actor: *"Autosave failed. Your content is preserved locally."* The editor falls
  back to localStorage buffering.
- **EF-001B — Collection Permission Denied:** If the actor attempts to assign the article to
  a collection for which they lack write access, the system returns HTTP 403 and displays
  an inline error beside the collection picker.
- **EF-001C — Media Upload Failure:** Covered in UC-004 exception flows.

### Business Rules Referenced
- BR-CA-001: Article must have title ≥ 5 characters before save.
- BR-CA-002: Article must be assigned to exactly one primary collection.
- BR-CA-003: Draft articles are invisible to Readers and not indexed.

### Related NFRs
- NFR-PERF-01: Autosave must complete within 500 ms p95.
- NFR-AVAIL-01: Editor must remain functional during Elasticsearch outages.

---

## UC-002 — Publish Article

| Field | Value |
|---|---|
| **UC-ID** | UC-002 |
| **Name** | Publish Article |
| **Actor(s)** | Editor (primary) |
| **Priority** | Critical |

### Preconditions
- The article exists in state `approved`.
- The actor holds the Editor role or higher in the workspace.
- The article has: non-empty title, body ≥ 50 characters, at least one tag, and an SEO
  description ≤ 160 characters (BR-CA-003).

### Postconditions
- Article state transitions to `published`.
- `publishedAt` timestamp is set to UTC now.
- An `ArticleVersion` snapshot is created and marked as the canonical published version.
- Elasticsearch index is updated within 10 seconds (async via BullMQ job).
- pgvector embedding is generated and stored (async).
- `article.published` event is emitted.
- Author receives an in-app and email notification.

### Main Flow
1. Editor opens the article from the review queue in state `approved`.
2. System displays a **Publish** button and a preview of the final rendered article.
3. Editor optionally schedules a future publish date/time.
4. Editor clicks **Publish Now** (or confirms scheduled publish).
5. System runs a pre-publish validation checklist (BR-CA-003, BR-CA-004).
6. System transitions article state to `published` and persists.
7. System enqueues BullMQ jobs: `index-article` (Elasticsearch) and `embed-article` (pgvector).
8. System emits `article.published` event.
9. Notification service sends in-app + email notification to the article author.
10. System displays confirmation with a public article link.

### Alternative Flows
- **AF-002A — Scheduled Publish:** At step 3, editor sets a future timestamp. System creates
  a BullMQ delayed job. Article remains in `approved` state until job executes.
- **AF-002B — Publish with Redirect:** Editor sets a canonical URL redirect from an old slug.
  System creates a `301` redirect record before completing the publish.

### Exception Flows
- **EF-002A — Indexing Failure:** If the BullMQ `index-article` job fails after 3 retries,
  the article remains published but a system alert is raised and the article is placed in a
  `pending_index` sub-state. A manual re-index can be triggered by a Workspace Admin.
- **EF-002B — Validation Failure:** If pre-publish validation fails, the system highlights
  the missing fields and blocks the publish action with an HTTP 422 response body listing
  each violated rule.

### Business Rules Referenced
- BR-CA-003: Mandatory metadata before publish.
- BR-CA-004: Published article must not duplicate the slug of another active article.
- BR-CA-005: Publish action creates an immutable version snapshot.

### Related NFRs
- NFR-PERF-02: Search index update must complete within 10 seconds of publish.
- NFR-AUDIT-01: All state transitions must be logged with actor, timestamp, and previous state.

---

## UC-003 — Search Knowledge Base

| Field | Value |
|---|---|
| **UC-ID** | UC-003 |
| **Name** | Search Knowledge Base |
| **Actor(s)** | Reader, Author, Editor, Widget User, Slack Bot, Zendesk Integration |
| **Priority** | Critical |

### Preconditions
- At least one article is in `published` state in the workspace.
- Elasticsearch index is available (degraded fallback: PostgreSQL FTS).

### Postconditions
- A ranked list of articles matching the query is returned.
- A `search.query_executed` event is emitted with query hash, result count, and source.
- If no results are found, a `search.no_results_found` event is emitted.

### Main Flow
1. User enters a search query in the search bar (minimum 2 characters).
2. System tokenises the query and issues a multi-match query to Elasticsearch across
   `title`, `body`, `tags`, and `excerpt` fields with BM25 scoring.
3. System concurrently generates a text embedding (OpenAI text-embedding-3-small) and
   performs a pgvector cosine-similarity query (top-K = 5, threshold = 0.7).
4. System merges and re-ranks results using a reciprocal rank fusion algorithm.
5. System applies collection-level access control filtering (BR-AC-001).
6. System returns the top 10 results with title, excerpt, breadcrumb, last updated date,
   and relevance score.
7. System emits `search.query_executed`.
8. Results are rendered in the search results page within 500 ms (p95 NFR-PERF-03).

### Alternative Flows
- **AF-003A — Filtered Search:** User applies filters (collection, tag, date range, author).
  System appends filter clauses to the Elasticsearch query.
- **AF-003B — Degraded Mode:** If Elasticsearch is unavailable, system falls back to
  PostgreSQL `to_tsvector` / `plainto_tsquery` full-text search. Semantic re-ranking is
  skipped. A banner informs the user of degraded search quality.
- **AF-003C — Federated Search via Slack:** Slack bot issues search via internal API. The
  same search logic is invoked; results are formatted as Slack Block Kit message payloads.

### Exception Flows
- **EF-003A — Query Timeout:** If Elasticsearch does not respond within 3 seconds, system
  switches to PostgreSQL FTS and logs a latency alert.
- **EF-003B — No Results:** System emits `search.no_results_found`, surfaces the AI Q&A
  widget (if enabled), and suggests related tags.

### Business Rules Referenced
- BR-SR-001: Search results must only include articles visible to the requesting user's role.
- BR-SR-002: Deleted and archived articles must be excluded from search results.
- BR-AC-001: Collection-level access filtering must be applied server-side.

### Related NFRs
- NFR-PERF-03: Search must return results in ≤ 500 ms p95.
- NFR-SEC-02: Search queries must not leak cross-workspace article data.

---

## UC-004 — AI Q&A Query

| Field | Value |
|---|---|
| **UC-ID** | UC-004 |
| **Name** | AI Q&A Query |
| **Actor(s)** | Reader (primary), Widget User (primary), Author |
| **Priority** | Critical |

### Preconditions
- AI Q&A feature is enabled for the workspace (Workspace Admin toggle).
- At least one article is published and embedded in the vector index.
- OpenAI API key is configured and credits are available.

### Postconditions
- An `AIConversation` and one or more `AIMessage` records are created or updated.
- An `ai.query_asked` event and `ai.answer_generated` (or `ai.fallback_triggered`) event
  are emitted.
- The answer is displayed with inline source-article citations.

### Main Flow
1. User types a natural-language question and submits.
2. System checks conversation context (include UC-007 – Maintain Conversation Context).
3. System generates an embedding for the question using text-embedding-3-small.
4. LangChain.js retrieves top-5 semantically similar article chunks from pgvector store
   (cosine similarity ≥ 0.45).
5. System constructs a RAG prompt: system instructions + retrieved chunks + conversation
   history (last 6 turns) + user question.
6. System calls OpenAI GPT-4o API with token budget enforcement (BR-AI-002).
7. System streams the response back to the client using Server-Sent Events.
8. System appends source article links below the streamed answer.
9. System persists AIConversation and AIMessage records.
10. System emits `ai.query_asked` and `ai.answer_generated`.
11. User is presented with thumbs-up / thumbs-down rating controls (extend UC-AIUC-05).

### Alternative Flows
- **AF-004A — Low Confidence Fallback:** If maximum cosine similarity of retrieved chunks
  < 0.45, system appends a disclaimer (BR-AI-003) and emits `ai.fallback_triggered`.
- **AF-004B — Follow-Up Question:** User asks a follow-up. System appends to the existing
  conversation context and repeats from step 3 with updated history.
- **AF-004C — Conversation Reset:** User clicks *New conversation*. System creates a new
  AIConversation record; prior context is not passed to GPT.

### Exception Flows
- **EF-004A — OpenAI API Unavailable:** System displays a user-facing message: *"AI Q&A is
  temporarily unavailable. Please use search or contact support."* Emits
  `ai.fallback_triggered` with reason `api_unavailable`.
- **EF-004B — Token Budget Exceeded:** If constructed prompt exceeds budget, system truncates
  the oldest conversation turns and retries once. If still over budget, oldest chunks are
  removed until within limits.
- **EF-004C — Content Policy Violation:** If OpenAI returns a content policy refusal, system
  surfaces the refusal message without modification and logs the event.

### Business Rules Referenced
- BR-AI-001: AI answers must be grounded in retrieved KB content only.
- BR-AI-002: Token budget limits must be enforced per user tier.
- BR-AI-003: Low-confidence answers must include disclaimers.
- BR-AI-004: AI conversation history must not cross workspace boundaries.

### Related NFRs
- NFR-PERF-04: First token of streamed answer must appear within 2 seconds p95.
- NFR-PRIV-02: Conversation history must be purged per data retention policy.

---

## UC-005 — Embed Help Widget

| Field | Value |
|---|---|
| **UC-ID** | UC-005 |
| **Name** | Embed Help Widget |
| **Actor(s)** | Workspace Admin (setup), External Widget User (runtime) |
| **Priority** | Critical |

### Preconditions
- Workspace is active and at least one article is published.
- Host product domain is whitelisted in workspace CORS settings.
- Widget JavaScript snippet has been added to the host product's HTML.

### Postconditions
- Widget renders in the host product UI without errors.
- `widget.initialized` event is emitted with workspace ID, page URL, and user context.
- Contextual article suggestions are displayed based on current page URL/metadata.

### Main Flow
1. Host product page loads; browser executes the embedded `<script>` snippet.
2. Snippet bootstraps the widget by loading the widget bundle from CloudFront CDN.
3. Widget sends an initialisation request to the `/api/widget/init` endpoint with
   workspace ID, current page URL, and optional authenticated user token.
4. System validates the workspace ID and CORS origin (BR-WS-003).
5. System runs page-context detection: matches page URL patterns against article metadata
   and collection labels to produce a ranked list of relevant articles.
6. Widget renders a collapsed launcher button.
7. User clicks the launcher; widget expands to show contextual article cards.
8. `widget.initialized` event is emitted.

### Alternative Flows
- **AF-005A — Authenticated User Context:** If a signed JWT is passed in step 3, system
  personalises suggestions based on user role and previous interaction history.
- **AF-005B — Custom Branding:** Workspace Admin has configured custom colours and logo;
  widget renders with custom theme from workspace settings.

### Exception Flows
- **EF-005A — CORS Rejection:** If the host origin is not whitelisted, the `/widget/init`
  request is rejected with HTTP 403. Widget displays no-op silently; no error is surfaced
  to end users.
- **EF-005B — CDN Unavailable:** If CloudFront is unreachable, the widget fails to load.
  The snippet must be wrapped in a try-catch so the host product continues to function
  without the widget.

### Business Rules Referenced
- BR-WS-003: Widget origins must be validated against the allowlist.
- BR-AC-004: Unauthenticated widget users only see articles marked as `public`.

### Related NFRs
- NFR-PERF-05: Widget bundle must be ≤ 150 KB gzipped.
- NFR-PERF-06: Widget initialisation must complete within 1 second on a 4G connection.

---

## UC-006 — Manage Collection Permissions

| Field | Value |
|---|---|
| **UC-ID** | UC-006 |
| **Name** | Manage Collection Permissions |
| **Actor(s)** | Workspace Admin (primary) |
| **Priority** | Critical |

### Preconditions
- Actor is authenticated as Workspace Admin.
- Target collection exists in the workspace.

### Postconditions
- Permission records updated in the database.
- Affected users' effective permissions are recalculated and cached in Redis.
- A `collection.updated` event is emitted.
- Audit log entry is created.

### Main Flow
1. Admin navigates to **Settings → Collections → [Collection Name] → Permissions**.
2. System displays current permission assignments: role-based and user-specific entries.
3. Admin selects a role (Reader / Author / Editor) or a specific user.
4. Admin assigns a permission level: `viewer`, `contributor`, `manager`, or `no_access`.
5. Admin clicks **Save Permissions**.
6. System validates no circular permission conflicts (BR-AC-002).
7. System persists the `Permission` records and invalidates the Redis permissions cache
   for all affected user IDs.
8. System emits `collection.updated` event.
9. System logs the change to the audit trail with before/after state.

### Alternative Flows
- **AF-006A — Inherit from Parent Collection:** Admin selects *Inherit from parent*.
  System marks the collection as inheriting, removing any explicit overrides.
- **AF-006B — Bulk Role Assignment:** Admin selects multiple collections and applies the
  same permission change in bulk. System iterates and applies to each.

### Exception Flows
- **EF-006A — Last Admin Lock-out Prevention:** System prevents removal of the last user
  with `manager` permission from a collection, returning HTTP 409.

### Business Rules Referenced
- BR-AC-001: Permissions are enforced server-side on every data-access call.
- BR-AC-002: A collection must always have at least one manager.
- BR-AC-003: Permission inheritance follows the collection hierarchy.

### Related NFRs
- NFR-SEC-01: Permission changes must propagate within 5 seconds.
- NFR-AUDIT-01: All permission mutations must be audit-logged.

---

## UC-007 — Review Article Draft

| Field | Value |
|---|---|
| **UC-ID** | UC-007 |
| **Name** | Review Article Draft |
| **Actor(s)** | Editor (primary) |
| **Priority** | Critical |

### Preconditions
- Article is in `in_review` state.
- Actor holds the Editor role.
- Actor is assigned as reviewer, or the article is in a collection where they have
  `manager` or `contributor` editor permission.

### Postconditions
- Inline comments are saved and visible to the Author.
- Article state transitions to `approved` (UC-002) or `changes_requested`.
- `article.submitted_for_review` or status-change event is emitted.

### Main Flow
1. Editor opens the review queue and selects the article.
2. System displays the article in review mode with the diff view against the last
   published version (if any).
3. Editor reads the content and adds inline comments by highlighting text.
4. Editor may accept or suggest changes using the suggestion mode.
5. Editor chooses **Approve** or **Request Changes**.
6. If **Approve**: system transitions article to `approved` (continue in UC-002 main flow).
7. If **Request Changes**: editor enters a summary message; system transitions article to
   `changes_requested` and notifies the Author.

### Alternative Flows
- **AF-007A — Co-review:** Multiple editors may simultaneously review. Comments are
  threaded; final approval requires only one editor with merge authority.

### Exception Flows
- **EF-007A — Author Edits During Review:** If Author edits the article while it is in
  review, system locks the review and notifies the editor: *"Article has been updated.
  Please re-review."* The article is transitioned back to `draft`.

### Business Rules Referenced
- BR-CA-006: Only one review cycle may be active per article at a time.
- BR-CA-007: An editor cannot approve their own article.

### Related NFRs
- NFR-COLLAB-01: Simultaneous editor sessions must be resolved via operational
  transformation to prevent data conflicts.

---

## UC-008 — Export Analytics Report

| Field | Value |
|---|---|
| **UC-ID** | UC-008 |
| **Name** | Export Analytics Report |
| **Actor(s)** | Workspace Admin (primary), Super Admin |
| **Priority** | Medium |

### Preconditions
- Actor is authenticated as Workspace Admin or Super Admin.
- Analytics data exists for the selected date range.

### Postconditions
- A downloadable CSV or PDF report is generated and made available via a pre-signed S3 URL.
- An `analytics.report_exported` event is emitted.

### Main Flow
1. Actor navigates to **Analytics Dashboard**.
2. Actor selects report type: *Article Performance*, *Search Trends*, *AI Q&A Usage*,
   *Deflection Rate*, or *User Activity*.
3. Actor sets date range and optional filters (collections, roles).
4. Actor selects output format: CSV or PDF.
5. Actor clicks **Export**.
6. System enqueues a BullMQ `generate-report` job.
7. System returns HTTP 202 Accepted; UI shows a progress indicator.
8. Worker generates the report, uploads to S3, and stores the pre-signed URL (valid 24 h).
9. System notifies the actor via in-app notification with a download link.
10. Actor downloads the report.

### Exception Flows
- **EF-008A — Large Dataset Timeout:** If report generation exceeds 5 minutes, the job
  is split into chunks processed in parallel. Actor is notified when all chunks are ready.
- **EF-008B — No Data for Range:** System returns an empty CSV with headers and displays
  an informational message.

### Business Rules Referenced
- BR-AN-001: Analytics data must not contain PII unless the actor has explicit data-export
  permissions.
- BR-AN-002: Report pre-signed URLs expire after 24 hours.

### Related NFRs
- NFR-PERF-07: Reports for ≤ 90-day ranges must generate within 60 seconds.

---

## UC-009 — Configure SSO Integration

| Field | Value |
|---|---|
| **UC-ID** | UC-009 |
| **Name** | Configure SSO Integration |
| **Actor(s)** | Workspace Admin (primary) |
| **Priority** | High |

### Preconditions
- Workspace is on a plan that includes SSO (Business tier or above).
- Actor holds the Workspace Admin role.
- Identity provider metadata XML or OIDC discovery URL is available.

### Postconditions
- SSO configuration is active; users can authenticate via the identity provider.
- A test login succeeds.
- `integration.connected` event is emitted with integration type `sso`.

### Main Flow
1. Admin navigates to **Settings → Authentication → SSO**.
2. System displays the SSO configuration form with SP metadata (EntityID, ACS URL).
3. Admin selects protocol: SAML 2.0 or OIDC.
4. Admin uploads IdP metadata XML (SAML) or enters discovery URL + client credentials (OIDC).
5. Admin maps IdP attributes to platform fields: email, name, role.
6. Admin clicks **Save & Test**.
7. System performs a metadata validation and test assertion (SP-initiated SSO flow in a
   popup window).
8. If test passes, system marks configuration as `active` and emits `integration.connected`.
9. System displays instructions for enforcing SSO-only login (optional step).

### Exception Flows
- **EF-009A — Certificate Expiry:** If IdP certificate is expired, system rejects the
  metadata with a descriptive error listing the certificate's expiry date.
- **EF-009B — Attribute Mapping Failure:** If the required `email` attribute is missing
  from the test assertion, system shows which attributes were received and prompts Admin
  to update the mapping.

### Business Rules Referenced
- BR-WS-004: SSO configuration requires plan-level feature flag validation.
- BR-AC-005: At least one local Admin account must remain active after SSO enforcement.

### Related NFRs
- NFR-SEC-03: SAML assertions must be validated against the stored certificate fingerprint.
- NFR-SEC-04: OIDC tokens must be validated for audience, issuer, and expiry.

---

## UC-010 — Deflect Support Ticket via Widget

| Field | Value |
|---|---|
| **UC-ID** | UC-010 |
| **Name** | Deflect Support Ticket via Widget |
| **Actor(s)** | External Widget User (primary), AI Assistant (system), Support Agent (secondary) |
| **Priority** | Critical |

### Preconditions
- Widget is initialised successfully (UC-005 postconditions met).
- At least one article is published and contextually relevant to the current page.
- The workspace has ticket deflection enabled in widget settings.

### Postconditions
- If the issue is resolved: `feedback.submitted` event with `deflected = true` is emitted.
  No ticket is created.
- If escalated: a ticket is created in the connected support system (Zendesk / Jira) and
  a `widget.escalation_triggered` event is emitted.
- Deflection rate metric is updated in the Analytics store.

### Main Flow
1. Widget User encounters a problem and opens the help widget.
2. Widget displays contextual article suggestions ranked by page-URL relevance.
3. User scans article cards; if an article resolves the issue, user marks *"This helped"*
   and closes the widget. Flow ends with ticket deflected.
4. If no article resolves the issue, user clicks **Ask AI**.
5. User submits a natural-language question (include UC-004 – AI Q&A Query).
6. System streams AI answer with source citations.
7. User rates the answer: **Resolved** or **Still need help**.
8. If **Resolved**: `feedback.submitted` (deflected = true) is emitted. Flow ends.
9. If **Still need help**: system presents a contact form pre-populated with the conversation
   summary and page context.
10. User submits the form; system creates a ticket via the integration API and emits
    `widget.escalation_triggered`.
11. System confirms ticket creation with a reference number.

### Alternative Flows
- **AF-010A — Live Chat Handoff:** If live chat integration is active, user is offered
  a live chat option instead of async ticket creation at step 9.

### Exception Flows
- **EF-010A — Integration API Unavailable:** If the ticket creation call fails, system
  stores the form data locally and retries asynchronously. User sees: *"Your request was
  submitted. We'll get back to you shortly."*

### Business Rules Referenced
- BR-WS-005: Widget must not collect personal data beyond email and the message unless
  user explicitly provides it.
- BR-AI-005: AI conversation summary included in ticket must be marked as AI-generated.

### Related NFRs
- NFR-PERF-06: Widget escalation form must submit within 2 seconds.
- NFR-AVAIL-02: Ticket creation fallback must prevent data loss on integration outage.

---

## Operational Policy Addendum

### Section 1 — Content Governance Policies
All use cases that mutate article state (UC-001, UC-002, UC-007, UC-008) must enforce the
state-machine transitions defined in `business-rules.md` (BR-CA-001 through BR-CA-010).
No direct database writes that bypass the application state machine are permitted.
Content created by AI Assist (AF-001C) must be labelled `ai_assisted = true` and require
human review before publishing. Editors must not approve articles they co-authored.

### Section 2 — Reader Data Privacy Policies
Search queries (UC-003), AI conversation data (UC-004), and widget interaction events
(UC-005, UC-010) must be collected and stored in compliance with the platform's data
retention schedule. Reader bookmarks and feedback are treated as personal data. Readers
may request their data via the *Privacy Settings* page, which triggers the GDPR erasure
workflow within 72 hours.

### Section 3 — AI Usage Policies
UC-004 and UC-010 both rely on the AI Q&A sub-system. All AI-generated answers must carry
source citations linking to specific articles (BR-AI-001). Answers that trigger the
low-confidence fallback (AF-004A) must display a standardised disclaimer. AI usage metrics
(tokens consumed, query volume, fallback rate) are tracked per workspace and surfaced in
the Analytics Dashboard (UC-008). Workspaces exceeding their AI token budget receive
throttled responses with a nudge to upgrade their plan.

### Section 4 — System Availability Policies
UC-003 (Search) and UC-010 (Widget Deflection) must remain functional during Elasticsearch
outages via PostgreSQL FTS fallback. UC-004 (AI Q&A) gracefully degrades when the OpenAI
API is unavailable. All use cases that enqueue BullMQ jobs (UC-002, UC-008) must implement
dead-letter queue handling so failed jobs do not silently lose data. The widget
initialisation (UC-005) must not block the host product's JavaScript execution.
