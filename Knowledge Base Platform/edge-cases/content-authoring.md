# Edge Cases: Content Authoring — Knowledge Base Platform

## Overview

This document catalogs edge cases specific to the Content Authoring domain of the Knowledge Base Platform. Authors, editors, and the authoring infrastructure face a unique set of failure modes due to the richness of the TipTap editor, asynchronous operations (S3 uploads, auto-save), and multi-user collaboration scenarios. Each edge case follows the standard 5-section template.

---

## EC-AUTHOR-001: Concurrent Edit Conflict

**Failure Mode:** Two authors (or an author and an editor) simultaneously edit the same article in separate browser sessions. Both save changes at nearly the same time, creating conflicting versions that cannot be automatically merged by the server.

**Impact:**
- Severity: **High**
- One author's changes are silently overwritten, causing data loss
- The second save succeeds but discards the first author's work
- No user-visible error; the overwriting author may not realize the conflict occurred
- Trust in the platform's reliability is damaged

**Detection:**
- Version number mismatch detected in ArticleService.update(): incoming request carries stale `version_number`
- Optimistic locking check: `WHERE id = ? AND version_number = ?` returns 0 rows
- CloudWatch metric: `article.save.conflict` custom metric spike (> 5/min triggers alert)
- Application logs: `[WARN] ConcurrentEditConflict articleId={} userId={} staleVersion={}`

**Mitigation/Recovery:**
1. Return HTTP 409 Conflict with response body: `{ "error": "EDIT_CONFLICT", "currentVersion": 8, "yourVersion": 6 }`
2. Frontend presents a three-way merge dialog: left panel (current server version), right panel (user's changes), merged result panel
3. Author can choose: "Keep mine", "Use server version", or "Merge manually"
4. Accepted merge creates a new version with `change_summary: "Conflict resolved by {authorName}"`
5. Notify the other editor via WebSocket `article.conflict.resolved` event

**Prevention:**
- Implement CRDT-based collaborative editing using Yjs as the TipTap collaboration provider
- Use Yjs + y-websocket server to maintain a single authoritative document state
- Store Yjs document state in Redis (`article:{id}:yjs_state`) with 24-hour TTL
- On article publish, serialize Yjs state to TipTap JSON and persist as a new version
- For workspaces without real-time collab enabled, enforce optimistic locking with version numbers

---

## EC-AUTHOR-002: Large Article Upload

**Failure Mode:** An author pastes a large amount of content (50,000+ word document converted from DOCX) into TipTap, creating an article body exceeding 10 MB of JSON. The editor becomes sluggish, auto-save takes 8+ seconds, and the API request body exceeds NestJS's default body size limit, returning HTTP 413.

**Impact:**
- Severity: **Medium**
- Author loses work if the editor crashes before auto-save
- API request fails; author receives unhelpful "Request too large" error
- Editor performance degrades significantly for large documents (> 5,000 nodes in ProseMirror)
- Other API users not affected (isolated to single request)

**Detection:**
- HTTP 413 responses on `PATCH /api/v1/articles/:id`: alert if > 3/hour
- TipTap editor `transaction.docChanged` handler: measure JSON serialization time; log warning if > 200 ms
- ECS task CPU spike correlated with large save attempts
- Application log: `[WARN] LargeArticleBody articleId={} bodySizeBytes={} threshold=10485760`

**Mitigation/Recovery:**
1. Increase NestJS body size limit to 25 MB for article update endpoints only (via `@UseInterceptors(LargeBodyInterceptor)`)
2. Implement lazy loading in TipTap for documents > 2,000 nodes using virtual rendering
3. For articles exceeding 50,000 words, suggest splitting into multiple linked articles
4. Auto-save debounce increased to 5 seconds for documents > 5 MB to reduce frequency
5. Client-side validation: warn author when body JSON > 8 MB before attempting save

**Prevention:**
- Enforce a soft limit of 25 MB per article version in `ArticleVersionService`; return HTTP 422 with clear error above this
- Add DOCX import feature that splits large documents by heading level into separate articles
- Implement server-side streaming for large article reads to avoid full JSON load in memory
- TipTap editor performance monitoring: track and alert when renderTime > 500 ms

---

## EC-AUTHOR-003: Version History Corruption

**Failure Mode:** A database transaction that updates `articles.current_version_id` and inserts a new `article_versions` record partially fails. The `articles` record is updated but the `article_versions` insert rolls back, leaving the article pointing to a non-existent version ID.

**Impact:**
- Severity: **Critical**
- Article becomes unreadable: every request to `GET /articles/:id` returns 500 Internal Server Error
- Article is visible in search results but cannot be opened
- Author loses access to their content
- Requires manual database intervention to resolve

**Detection:**
- HTTP 500 rate spike on `GET /articles/:id` for affected article
- TypeORM `EntityNotFoundError` in application logs for `ArticleVersion` entity
- Scheduled integrity check job (runs every 6 hours): finds articles where `current_version_id` references non-existent version
- Database-level constraint: FOREIGN KEY `articles.current_version_id` → `article_versions.id` ON DELETE RESTRICT

**Mitigation/Recovery:**
1. Immediate: set `articles.current_version_id` to the highest available `article_versions.id` for that article
2. If no versions exist, set `current_version_id = NULL` and status = `DRAFT`; article shown as empty draft
3. Notify the article author of data loss and the recovery action taken
4. Run full version integrity audit across all articles in affected workspace
5. Open P1 incident; review transaction logs to determine root cause

**Prevention:**
- Wrap all version creation and article update operations in a single PostgreSQL transaction with proper rollback
- Add database-level NOT VALID foreign key constraint with periodic VALIDATE runs
- Integration test covering partial failure scenarios using deliberate transaction abort injection
- Consider Event Sourcing pattern for article state: rebuild current state from version chain, eliminating `current_version_id` as a point of failure

---

## EC-AUTHOR-004: Attachment Upload Failure

**Failure Mode:** An author initiates an image upload in the TipTap editor. The upload to AWS S3 via pre-signed URL begins, but the network connection drops mid-transfer. A partial object is written to S3 and the `attachments` record is created in PostgreSQL with status `UPLOADING`, but never transitions to `UPLOADED`.

**Impact:**
- Severity: **Medium**
- Broken image placeholder appears in the article body indefinitely
- Orphaned attachment record consumes S3 storage (partial multipart upload bytes)
- Author may not notice if the article is published with broken images
- Readers see `[image failed to load]` in the published article

**Detection:**
- `attachments.status = UPLOADING` and `created_at < NOW() - 30 minutes`: indicates stale upload (scheduled cleanup job)
- S3 ListMultipartUploads check: incomplete uploads older than 1 hour flagged
- Frontend attachment upload callback: network error → emit `upload.failed` event to analytics
- CloudWatch S3 metric: `NumberOfIncompleteMultipartUploads` alert if > 50

**Mitigation/Recovery:**
1. Frontend retry: on network failure, automatically retry upload up to 3 times with exponential backoff (2s, 4s, 8s)
2. If all retries fail, show author an inline error: "Upload failed. Click to retry." with a re-upload option
3. Backend cleanup job (BullMQ, every hour): find stale `UPLOADING` attachments → delete PostgreSQL record → abort S3 multipart upload
4. Publish-time validation: block article publish if any attachments in body have status ≠ `UPLOADED`; show author list of broken attachments

**Prevention:**
- Use S3 multipart upload with client-side checksum (CRC32) for files > 5 MB; verify checksum server-side after completion
- Implement S3 lifecycle rule to automatically abort incomplete multipart uploads after 24 hours
- TipTap extension: track upload state per attachment node; prevent editor save when any attachment is in `UPLOADING` state
- Add S3 bucket notification → SQS → Lambda to confirm upload completeness and update attachment status asynchronously

---

## EC-AUTHOR-005: Auto-Save Data Loss

**Failure Mode:** An author writes 30 minutes of content in TipTap. The browser crashes or the tab is accidentally closed 5 seconds before the 30-second auto-save timer fires. All unsaved content since the last auto-save checkpoint is lost.

**Impact:**
- Severity: **High**
- Author loses up to 30 seconds of work (max between auto-saves)
- If auto-save failed silently (network error) earlier, the loss could be much larger
- Significant frustration and productivity loss for authors writing long-form content
- No recovery possible once browser state is lost

**Detection:**
- Browser `beforeunload` event fires with unsaved changes: log `draft.unsaved_exit` analytics event
- Auto-save success/failure tracked per session: if failure rate > 20% in 5 minutes, surface error toast
- Network offline detection: `navigator.onLine` event → pause auto-save, show "Offline - changes not saved" banner

**Mitigation/Recovery:**
1. Implement browser-local draft backup using IndexedDB: backup TipTap JSON every 5 seconds to `localStorage['draft:{articleId}']`
2. On article editor load: check for IndexedDB draft newer than the server version; prompt author "We found unsaved changes from {time}. Restore them?"
3. On network recovery: auto-resume save queue with the most recent IndexedDB state
4. Configurable auto-save interval: default 30 seconds, author can reduce to 10 seconds in editor preferences
5. Persistent visual indicator in editor header: "Saved 2 minutes ago" or "Unsaved changes (saving...)"

**Prevention:**
- Reduce default auto-save interval to 15 seconds
- Implement beforeunload confirmation: "You have unsaved changes. Are you sure you want to leave?"
- Yjs CRDT integration (from EC-AUTHOR-001 fix) inherently solves this: Yjs state is synced to server in real-time, not in batch intervals

---

## EC-AUTHOR-006: Circular Cross-Link

**Failure Mode:** An author creates a cross-link from Article A → Article B. Another author adds a cross-link from Article B → Article A. Readers navigating "Related Articles" or clicking inline links may perceive a loop. A more severe scenario: Article A embeds Article B's content via a transclusion feature, which embeds Article A's content, causing infinite recursion in the renderer.

**Impact:**
- Severity: **Medium** (navigation loop) to **Critical** (recursive render crash)
- Navigation loop: poor reader experience, potentially confusing SEO crawlers
- Recursive render (if transclusion supported): API server stack overflow, 500 error for all readers of affected article
- Hard to detect without automated graph analysis

**Detection:**
- CrossLinkService.createLink(): perform DFS/BFS traversal of existing link graph before saving new link; detect cycles
- Article renderer: implement render depth counter (max depth = 1 for transclusion); return placeholder if exceeded
- Scheduled graph analysis job (weekly): find strongly connected components in article cross-link graph; report to workspace admin

**Mitigation/Recovery:**
1. On cycle detection in CrossLinkService: return HTTP 422 with message "Adding this link would create a circular reference: A → B → A"
2. For existing cycles (introduced before detection was implemented): article renderer checks depth counter; breaks cycle gracefully
3. Admin tool: list all circular cross-links in workspace; provide bulk-fix wizard to remove the loop-forming link

**Prevention:**
- Cross-link graph stored as adjacency list in Redis for fast DFS traversal at link creation time
- Maximum cross-link depth for related article suggestions: 2 hops
- Transclusion (if implemented): server-side render with hard depth limit of 1; document limitation in authoring guide

---

## EC-AUTHOR-007: Broken Media Embed

**Failure Mode:** An author embeds a YouTube video or external image URL in the article body. After the article is published, the external URL becomes inaccessible (video taken down, domain expired, CDN link rotated). Readers see a broken embed or missing image.

**Impact:**
- Severity: **Low** (single article affected) to **Medium** (widespread if template or popular article)
- Degraded reader experience; article appears incomplete
- No automated detection unless proactively monitored
- Author may be unaware; issue may persist for months

**Detection:**
- Link health check job (BullMQ, daily): for each published article, extract all external URLs from TipTap JSON; send HEAD requests; record failures
- Alert Workspace Admin when > 5 broken embeds detected in a single article
- Reader-facing tracking: JavaScript `onerror` event on `<img>` and `<iframe>` elements sends broken embed analytics event

**Mitigation/Recovery:**
1. Link health check results surface in author's article dashboard: "3 broken embeds detected" with link to fix
2. For images: provide "Re-upload to KB storage" option — downloads original URL, stores in S3, updates article body
3. For video embeds: show broken embed placeholder in reader view with "Video unavailable" message
4. Editor notification: weekly digest of all broken embeds across author's articles

**Prevention:**
- Encourage authors to upload media to S3 (via KB) rather than linking external URLs
- Link health check runs within 24 hours of first publish (near-time validation)
- TipTap embed extension: warn author when pasting external URL "External URLs can break. Consider uploading to Knowledge Base storage."

---

## EC-AUTHOR-008: Article Template Corruption

**Failure Mode:** A Workspace Admin saves an article template with malformed TipTap JSON (e.g., a node type that is no longer supported after a TipTap version upgrade). Authors who select this template for a new article encounter a JavaScript exception in TipTap, causing the editor to crash on load.

**Impact:**
- Severity: **High** (if popular template used by many authors)
- All new articles created from the corrupted template fail to open
- Existing articles created from the template may also be affected
- Authors blocked from starting new content until template is fixed

**Detection:**
- Template save endpoint: validate TipTap JSON against the current ProseMirror schema before persisting
- Template load in editor: JSON schema validation + try/catch around TipTap `setContent()`; log validation errors
- Error tracking (Sentry): `TipTapContentLoadError` events spike after template update
- Admin template list: automated linting badge shown for each template

**Mitigation/Recovery:**
1. Template load failure: TipTap falls back to an empty document with a warning banner "Template could not be loaded due to a compatibility issue. Starting with an empty document."
2. Workspace Admin notified immediately: "Template '{name}' contains invalid content. Please edit or delete it."
3. Admin can restore previous template version (template versions are retained for 30 days)
4. Affected articles: ArticleService detects articles with corrupt body on load; renders sanitized version stripping unknown node types

**Prevention:**
- Template validation middleware: all template save operations pass TipTap JSON through `@tiptap/core` schema validator before persistence
- Automated regression test: after each TipTap version upgrade, run all existing templates through the validator; fail the upgrade if validation errors detected
- Canary deployment for template changes: new template version shown to 10% of authors for 1 hour before full rollout

---

## Summary Table

| ID | Failure Mode | Severity | Primary Detection | Primary Prevention |
|----|-------------|----------|-------------------|--------------------|
| EC-AUTHOR-001 | Concurrent Edit Conflict | High | Version mismatch → HTTP 409 | CRDT/Yjs collaboration |
| EC-AUTHOR-002 | Large Article Upload | Medium | HTTP 413 spike; editor lag | 25 MB limit; lazy rendering |
| EC-AUTHOR-003 | Version History Corruption | Critical | FK violation; integrity check job | Atomic transactions; FK constraint |
| EC-AUTHOR-004 | Attachment Upload Failure | Medium | Stale UPLOADING records | S3 multipart + retry + cleanup job |
| EC-AUTHOR-005 | Auto-Save Data Loss | High | beforeunload analytics event | IndexedDB local backup + Yjs sync |
| EC-AUTHOR-006 | Circular Cross-Link | Medium–Critical | DFS cycle detection at save | Link graph cycle check |
| EC-AUTHOR-007 | Broken Media Embed | Low–Medium | Daily link health check job | Upload to S3; near-time validation |
| EC-AUTHOR-008 | Article Template Corruption | High | Schema validation on save | TipTap JSON schema validation; version regression tests |

---

## Operational Policy Addendum

### Content Governance Policies

All authoring edge cases with severity Critical or High require a documented post-incident review within 5 business days of occurrence. Recovered data (from IndexedDB restore or version rollback) must be validated by the original author before being published. Template changes by Workspace Admins are subject to a 1-hour canary period before full activation.

### Reader Data Privacy Policies

Local IndexedDB draft storage (EC-AUTHOR-005 prevention) stores TipTap JSON content in the author's browser. This is considered author-owned data. The platform does not transmit IndexedDB contents to analytics or logging systems. Clearing browser data removes local drafts; authors are warned of this in the editor preferences panel.

### AI Usage Policies

EC-AUTHOR-002 (large article) and EC-AUTHOR-003 (version corruption) can impact the embedding pipeline. When an article version cannot be embedded due to body corruption or size, the EmbeddingWorker logs the failure and moves the job to the DLQ without retrying automatically. A manual re-embed trigger is available in the admin tools. Large articles (> 10,000 words) are split into 512-token chunks for embedding, with up to 20 chunks per article.

### System Availability Policies

Auto-save failures (EC-AUTHOR-005) are surfaced to authors within 5 seconds via the editor status indicator. The platform's 99.9% SLA covers article read operations; write operations (save, publish) are covered at 99.5% due to dependency on RDS write availability. If the RDS primary is unavailable, article reads continue from read replicas, but saves are queued with a client-side retry for up to 2 minutes before showing an error.
