# User Stories — Knowledge Base Platform

**Version:** 1.0  
**Date:** 2025-01-01  
**Status:** Approved  
**Owner:** Product Management

---

## 1. Introduction

This document contains the full set of user stories for the Knowledge Base Platform (KBP), organized by actor role and mapped to product epics. Stories follow the standard format:

> **US-[ROLE]-[NNN]** — As a [role], I want to [action] so that [benefit].

Each story includes acceptance criteria, a priority rating (Must-Have / High / Medium / Low), and a story-point estimate using the Fibonacci scale (1, 2, 3, 5, 8, 13).

---

## 2. Epic Summary

| Epic ID | Name | Description |
|---|---|---|
| EP-01 | Content Lifecycle | Everything related to creating, reviewing, publishing, versioning, and archiving articles |
| EP-02 | Discovery & Search | Full-text search, semantic search, navigation, and content organization |
| EP-03 | AI Assistance | AI Q&A, summarization, auto-tagging, gap detection, and draft generation |
| EP-04 | Access & Security | Authentication, authorization, SSO, audit, and rate limiting |
| EP-05 | Analytics & Integrations | Metrics, reporting, third-party integrations, and API access |

---

## 3. Author Stories

Authors create and maintain articles. They draft content, submit it for editorial review, upload media, and monitor the performance of their own articles.

---

**US-AU-001** — As an Author, I want to create a new article draft using a rich-text editor so that I can compose structured content without writing raw HTML.

- **Epic:** EP-01
- **Priority:** Must-Have
- **Story Points:** 5
- **Acceptance Criteria:**
  - Given I am logged in as an Author, when I click "New Article" within a Space, then an empty TipTap editor opens in a new draft with a generated UUID slug.
  - Given I am editing, when I type `/` then a slash-command palette appears with at least 12 block types (heading, image, callout, code block, table, divider, toggle, ordered list, unordered list, quote, embed, file).
  - Given I am editing, when I leave the tab idle for 30 seconds, then the draft is autosaved and a "Draft saved" toast appears.
  - Given an autosave fails due to network error, when the connection is restored, then the queued save is automatically retried and the draft is synchronized.
  - Given the draft is saved, when I reload the page, then all content, title, and metadata are restored exactly as left.

---

**US-AU-002** — As an Author, I want to upload images and files directly into the editor so that I can include visual assets without leaving the authoring interface.

- **Epic:** EP-01
- **Priority:** Must-Have
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given I am in the editor, when I drag a PNG/JPG/GIF/WebP image onto the editor canvas, then the image is uploaded to S3 and rendered inline within 3 seconds.
  - Given I am in the editor, when I upload a file via the slash command `/file`, then a file attachment block is inserted showing filename, size, and a download icon.
  - Given I attempt to upload a file larger than 50 MB, when the upload begins, then the upload is rejected and an error toast states "File exceeds 50 MB limit."
  - Given an uploaded image, when I click it, then I can set alt text, caption, and choose alignment (left, center, full-width).

---

**US-AU-003** — As an Author, I want to view the version history of my article and compare two versions side by side so that I can understand what changed between revisions.

- **Epic:** EP-01
- **Priority:** High
- **Story Points:** 5
- **Acceptance Criteria:**
  - Given a published article with multiple versions, when I open the version history panel, then all versions are listed with version number, publisher name, and UTC timestamp.
  - Given two versions selected, when I click "Compare", then a diff view renders additions in green and deletions in red at the block level.
  - Given a historical version, when I click "Restore this version", then the editor pre-fills with the historical content as a new draft, and I am prompted to confirm before overwriting the current draft.
  - Given I am an Author viewing another author's article history, then I can view versions but cannot restore them (read-only access to history).

---

**US-AU-004** — As an Author, I want to submit my draft for editorial review so that an Editor can approve it before it becomes visible to readers.

- **Epic:** EP-01
- **Priority:** Must-Have
- **Story Points:** 2
- **Acceptance Criteria:**
  - Given a saved draft, when I click "Submit for Review", then the article status changes to "In Review" and the Editor is notified via in-app notification and email.
  - Given my article is in "In Review" status, then the editor controls are locked and I see a read-only view with a "Withdraw from Review" option.
  - Given I withdraw from review, when confirmed, then the article status reverts to "Draft" and the Editor's notification is dismissed.
  - Given the Editor requests changes, when I receive the notification, then the article reverts to "Draft" status with the Editor's comment attached.

---

**US-AU-005** — As an Author, I want to use content templates so that I can start new articles with a consistent structure rather than from a blank page.

- **Epic:** EP-01
- **Priority:** High
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given I click "New Article", when I choose "From Template", then a template picker modal shows at least 10 built-in templates with a preview pane.
  - Given I select a template, when confirmed, then the editor opens with the template's TipTap JSON pre-loaded and all placeholder text highlighted for easy replacement.
  - Given a Workspace Admin has created custom templates, when I open the template picker, then custom templates appear in a "Workspace Templates" section above the built-in templates.
  - Given I am using a template, then all template content is treated as my own draft and I can freely edit, add, or delete any block.

---

**US-AU-006** — As an Author, I want to see real-time word count and reading time in the editor sidebar so that I can gauge article length while writing.

- **Epic:** EP-01
- **Priority:** Medium
- **Story Points:** 2
- **Acceptance Criteria:**
  - Given I am editing an article, then the editor sidebar shows a live word count updated as I type.
  - Given the article has content, then the sidebar shows an estimated reading time calculated at 238 words per minute, rounded to the nearest minute.
  - Given the article has headings, then the sidebar shows a structural SEO score rating the heading hierarchy, title length (target 50–60 chars), and meta description completeness.
  - Given the word count exceeds 2 000 words, then the reading time is shown in minutes and seconds (e.g., "8 min 22 sec").

---

**US-AU-007** — As an Author, I want to insert cross-links to other articles using wiki-link syntax so that readers can easily navigate between related content.

- **Epic:** EP-02
- **Priority:** High
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given I type `[[` in the editor, then an autocomplete dropdown appears showing article titles matching my typed query, filtered by the current workspace.
  - Given I select an article from the dropdown, then a wiki-link is inserted that renders as a styled hyperlink in reader view.
  - Given I hover over a wiki-link in reader view, then a popover card shows the linked article's title, description, tags, and a "Open article" button.
  - Given a linked article is deleted, then wiki-links pointing to it are highlighted with a broken-link indicator and the Author is notified via an in-app alert.

---

**US-AU-008** — As an Author, I want to view analytics for my own articles (views, helpfulness score, time-on-page) so that I can understand how well my content is performing.

- **Epic:** EP-05
- **Priority:** High
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given I am on the article detail page, when I click the "Analytics" tab, then I see pageviews, unique visitors, average time-on-page, and helpfulness score for the last 30 days.
  - Given the helpfulness score is below 60%, then the score is displayed in red with a "Needs attention" badge.
  - Given the analytics tab, when I switch the time range to 7, 30, or 90 days using a toggle, then the metrics update accordingly without a full page reload.
  - Given I have multiple articles, when I visit My Articles dashboard, then a sortable table shows all my articles with their top metrics in a single view.

---

**US-AU-009** — As an Author, I want to use AI-generated tag suggestions so that I can categorize my article accurately without manually brainstorming every tag.

- **Epic:** EP-03
- **Priority:** High
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given I have written at least 100 words of article content, when I open the Tags field, then an "AI Suggest Tags" button appears.
  - Given I click "AI Suggest Tags", then up to 5 tag suggestions appear as chips with an individual accept/reject control on each.
  - Given I accept a suggested tag, then it is added to the article's tag list; rejected tags are dismissed and not re-suggested for this session.
  - Given AI features are disabled for the workspace, then the "AI Suggest Tags" button is hidden and the feature is unavailable.

---

**US-AU-010** — As an Author, I want to duplicate an existing article as a starting point for a new one so that I can reuse structure without rewriting from scratch.

- **Epic:** EP-01
- **Priority:** Medium
- **Story Points:** 2
- **Acceptance Criteria:**
  - Given I am viewing any article I have at least Read access to, when I click "Duplicate", then a new draft is created with "(Copy)" appended to the title and all content, tags, and meta description copied.
  - Given the duplicate is created, then the version history and inline comments are NOT carried over to the new draft.
  - Given the duplicate is created, then I am immediately redirected to the editor for the new draft.
  - Given I duplicate an article in Space A, then the duplicate is created in the same Space and Collection by default, with an option to select a different location.

---

## 4. Editor Stories

Editors are the editorial gatekeepers. They review submitted articles, approve or request changes, publish, manage taxonomy, and monitor content quality across the workspace.

---

**US-ED-001** — As an Editor, I want to review submitted articles and provide inline feedback so that Authors know exactly what needs to be improved before publication.

- **Epic:** EP-01
- **Priority:** Must-Have
- **Story Points:** 5
- **Acceptance Criteria:**
  - Given an article is "In Review", when I open it, then I see the full article content and a toolbar with "Approve", "Request Changes", and "Reject" actions.
  - Given I select text and click "Comment", then I can type an inline comment anchored to the selected range, which is saved and visible to the Author.
  - Given I click "Request Changes", then I must enter a comment of at least 20 characters; the article reverts to "Draft" and the Author is notified.
  - Given I click "Approve", then the article moves to "Approved" status and the "Publish" button becomes available to me.
  - Given an article has been "In Review" for more than 10 business days, then I receive an escalation reminder notification.

---

**US-ED-002** — As an Editor, I want to publish approved articles with a scheduled publish date so that content goes live at the optimal time without requiring me to be online.

- **Epic:** EP-01
- **Priority:** High
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given an article in "Approved" status, when I click "Publish", then I can choose "Publish Now" or "Schedule" with a datetime picker.
  - Given I schedule a publish time, then a BullMQ job is created for that timestamp and the article status shows "Scheduled" with the time displayed.
  - Given a scheduled publish executes, then the article status changes to "Published", it becomes visible to permitted readers, and Slack/notification events fire.
  - Given I need to cancel a scheduled publish, when I click "Cancel Schedule", then the job is removed and the article reverts to "Approved".

---

**US-ED-003** — As an Editor, I want to manage the workspace tag taxonomy so that the content library remains consistently categorized and free of duplicate or misspelled tags.

- **Epic:** EP-02
- **Priority:** High
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given I am on the Tags management page, then I can see all workspace tags, their usage count (number of articles), and creation date.
  - Given I select two tags and click "Merge", then all articles tagged with either tag are re-tagged with my chosen canonical tag and the duplicate is deleted.
  - Given I rename a tag, then all articles using that tag are updated immediately and the old tag name is no longer accessible.
  - Given I delete a tag with zero associated articles, then it is permanently removed; deleting a tag with articles first requires confirmation showing the count of affected articles.

---

**US-ED-004** — As an Editor, I want to bulk-publish or bulk-archive multiple approved articles at once so that I can efficiently manage large content updates.

- **Epic:** EP-01
- **Priority:** High
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given the Articles list view, when I check multiple checkboxes, then a bulk actions toolbar appears with "Publish", "Archive", "Change Space", and "Add Tag" options.
  - Given I select "Bulk Publish", then only articles in "Approved" status are published; articles in other statuses are skipped with a warning message.
  - Given a bulk operation completes, then a summary notification states "X articles published, Y skipped" with a link to a detailed log.
  - Given I have selected more than 100 articles for bulk action, then the operation is queued as a BullMQ job and I am notified on completion.

---

**US-ED-005** — As an Editor, I want to view and resolve the feedback inbox so that low-quality content is identified and improved promptly.

- **Epic:** EP-05
- **Priority:** High
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given I open the Feedback Inbox, then I see a list of articles with pending reader comments or low helpfulness scores, sorted by urgency.
  - Given an article has a helpfulness score below the workspace threshold (default 60%), then it is flagged with a red indicator in the inbox.
  - Given I click "Reassign to Author", then a task notification is sent to the article's Author requesting an update.
  - Given I resolve a feedback thread, when I click "Mark Resolved", then the thread is collapsed and removed from the Inbox's unresolved count.

---

**US-ED-006** — As an Editor, I want to use AI-generated article summaries so that I can quickly assess content quality during review without reading every word.

- **Epic:** EP-03
- **Priority:** High
- **Story Points:** 2
- **Acceptance Criteria:**
  - Given I am reviewing an article, when I click "AI Summary" in the review sidebar, then a 3–5 sentence plain-language summary is generated and displayed within 5 seconds.
  - Given a summary was previously generated, then it is served from cache and displayed instantly without a new API call.
  - Given AI features are disabled for the workspace, then the "AI Summary" button is hidden.
  - Given the article is fewer than 100 words, then the summary feature is disabled with a tooltip "Article too short to summarize."

---

**US-ED-007** — As an Editor, I want to set article-level visibility overrides so that I can grant specific users access to private articles without changing their workspace role.

- **Epic:** EP-04
- **Priority:** High
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given an article with visibility set to "Private", when I open the Sharing panel, then I can search for workspace members by name/email and grant them "Can Read" access.
  - Given I add a user to the Private access list, then that user can view the article in search results and direct navigation.
  - Given I remove a user from the access list, then they immediately lose access and the article no longer appears in their search results.
  - Given I set visibility to "Internal", then all workspace members can read the article regardless of individual ACL entries.

---

**US-ED-008** — As an Editor, I want to view a content gap report based on failed searches so that I can commission new articles to fill knowledge holes.

- **Epic:** EP-03
- **Priority:** Medium
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given the AI Gap Detection report, then I see a table of search queries that returned zero results, ranked by frequency over the last 30 days.
  - Given a gap suggestion generated by the AI, then it shows a recommended article title, suggested space/collection, and a "Create Article" shortcut.
  - Given I click "Create Article" for a gap suggestion, then a new draft is opened pre-filled with the AI-suggested title and outline.
  - Given the report, when I export it as CSV, then a file is downloaded with columns: query text, frequency, suggested title, suggested collection.

---

**US-ED-009** — As an Editor, I want to archive outdated articles rather than deleting them so that historical content is preserved and can be restored if needed.

- **Epic:** EP-01
- **Priority:** High
- **Story Points:** 2
- **Acceptance Criteria:**
  - Given I click "Archive" on a Published article, then the article status changes to "Archived", it is hidden from all reader-facing views, and a confirmation toast appears.
  - Given an Archived article, when I search in the admin dashboard with "Include archived" toggled on, then it appears in results with an "Archived" badge.
  - Given I click "Restore" on an Archived article, then it returns to "Draft" status for further editing before re-publication.
  - Given an Archived article has not been modified for the workspace's configured retention period, then it appears in a "Pending Purge" list for Super Admin review.

---

## 5. Reader Stories

Readers are the end-users of the knowledge base — customers, employees, or public visitors who consume published content, search for answers, and provide feedback.

---

**US-RE-001** — As a Reader, I want to search across all published articles using a keyboard shortcut so that I can quickly find answers without navigating menus.

- **Epic:** EP-02
- **Priority:** Must-Have
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given I am on any page of the knowledge base, when I press `Cmd+K` (Mac) or `Ctrl+K` (Windows/Linux), then a search overlay opens with focus in the search input.
  - Given I type a query, then autocomplete suggestions appear within 150 ms showing matching article titles and tag names.
  - Given I press Enter or click a result, then I am navigated to the article page and the search overlay closes.
  - Given my query returns zero results, then a "No results found" message is shown with a "Try these related articles" section using semantic similarity.

---

**US-RE-002** — As a Reader, I want to rate articles as helpful or not helpful so that content teams know which articles to improve.

- **Epic:** EP-05
- **Priority:** Must-Have
- **Story Points:** 2
- **Acceptance Criteria:**
  - Given I have read to the end of a published article, then a "Was this article helpful?" prompt with 👍 and 👎 buttons is visible at the bottom.
  - Given I click 👎, then a free-text input appears asking "What could be improved?" with a 500-character limit and optional submission.
  - Given I submit a rating, then a thank-you message replaces the prompt and my rating is recorded for analytics.
  - Given I have already rated an article in this session, then the prompt is replaced with my previous rating with an option to change it.

---

**US-RE-003** — As a Reader, I want to use the AI assistant to ask questions in natural language so that I can get direct answers without reading multiple articles.

- **Epic:** EP-03
- **Priority:** Must-Have
- **Story Points:** 5
- **Acceptance Criteria:**
  - Given I open the AI chat panel (accessible from the sidebar and the help widget), when I type a question and press Enter, then a streaming response begins within 2 seconds.
  - Given the AI provides an answer, then source article titles are displayed as clickable citations below the response.
  - Given I click a citation, then I am taken to the relevant article with the cited passage highlighted.
  - Given the AI cannot find a relevant answer in the knowledge base, then it responds "I couldn't find an answer in this knowledge base. You may want to contact support." and does not hallucinate.
  - Given I continue the conversation with a follow-up question, then the AI maintains context from the prior 10 turns.

---

**US-RE-004** — As a Reader, I want to browse articles organized by Space and Collection so that I can explore the knowledge base structure when I do not have a specific query.

- **Epic:** EP-02
- **Priority:** Must-Have
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given the workspace home page, then I see all Spaces displayed as cards with their name, icon, description, and article count.
  - Given I click a Space, then I see its Collections as an expandable tree sidebar and the articles in the root collection in the main area.
  - Given I click a Collection, then articles in that collection are displayed as a list with title, author, last-updated date, and helpfulness score.
  - Given an article has a table of contents (2+ headings), then it is displayed as a sticky sidebar while I read, allowing click-to-scroll navigation.

---

**US-RE-005** — As a Reader, I want to filter search results by tags, space, author, and date so that I can narrow down large result sets quickly.

- **Epic:** EP-02
- **Priority:** High
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given a search results page, then a filter panel shows facets for: Space (multi-select), Tags (multi-select), Author (multi-select), Status (Published/Archived), and Date range (from/to pickers).
  - Given I select multiple filters, then results are filtered immediately without a page reload (client-side Elasticsearch query update).
  - Given I apply filters that produce zero results, then an empty state shows the applied filters with a "Clear all filters" button.
  - Given I apply a filter, then the URL is updated with filter params so the filtered view can be bookmarked and shared.

---

**US-RE-006** — As a Reader, I want to submit an inline comment on a specific section of an article so that I can ask a clarifying question or flag an error in context.

- **Epic:** EP-05
- **Priority:** High
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given I am authenticated and reading a published article, when I select any paragraph, then a comment icon appears in the margin.
  - Given I click the comment icon, then a comment input appears anchored to that paragraph.
  - Given I submit a comment, then it is saved, the paragraph is marked with a comment indicator, and the article's Editor is notified.
  - Given an Editor replies to my comment, then I receive an in-app notification and the thread is visible when I hover the paragraph indicator.
  - Given the comment thread is marked as resolved, then the indicator is dimmed and the thread is collapsed but still viewable.

---

**US-RE-007** — As a Reader, I want to use the embeddable help widget within a product I'm using so that I can access contextual help without navigating away from my current task.

- **Epic:** EP-01
- **Priority:** Must-Have
- **Story Points:** 5
- **Acceptance Criteria:**
  - Given the widget is embedded in a host application, when the widget launcher icon is clicked, then a slide-in panel opens within 500 ms.
  - Given the panel opens, then contextual article suggestions relevant to the current page URL are shown (up to 5).
  - Given I type in the widget search bar, then results appear within 300 ms.
  - Given I click an article title, then the full article content renders inside the widget panel without navigating away from the host page.
  - Given I click "Ask AI", then the AI chat interface opens within the widget and I can ask questions using the same RAG assistant.

---

**US-RE-008** — As a Reader, I want to see related articles at the bottom of each article so that I can continue exploring connected topics without backtracking.

- **Epic:** EP-02
- **Priority:** High
- **Story Points:** 2
- **Acceptance Criteria:**
  - Given I am at the bottom of a published article, then a "Related Articles" section shows up to 5 article cards with title, description excerpt, and Space/Collection breadcrumb.
  - Given the related articles are computed by AI similarity, then they are semantically relevant to the current article's content, not just sharing a common tag.
  - Given the current article has no published sibling articles with sufficient similarity, then the "Related Articles" section is hidden rather than showing low-relevance filler.
  - Given I click a related article, then I navigate to it and a new set of related articles is computed for the destination article.

---

## 6. Workspace Admin Stories

Workspace Admins configure and manage a single workspace — its membership, branding, integrations, settings, and analytics.

---

**US-WA-001** — As a Workspace Admin, I want to invite members to my workspace by email so that my team can access and contribute to our knowledge base.

- **Epic:** EP-04
- **Priority:** Must-Have
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given I am on the Members settings page, when I enter one or more email addresses and select a role, then invitation emails are sent and pending invitations appear in a list.
  - Given an invitee accepts the invitation, then their account is created (or linked if they already have one), they are added to the workspace with the assigned role, and I receive a notification.
  - Given an invitation has not been accepted within 7 days, then it is automatically marked as expired and removed from the pending list.
  - Given I resend an invitation, then a new invitation email is sent and the expiry is reset to 7 days.
  - Given I revoke a pending invitation, then the invitation link is invalidated immediately.

---

**US-WA-002** — As a Workspace Admin, I want to configure SSO for my workspace using SAML 2.0 so that my team can log in with their existing corporate credentials.

- **Epic:** EP-04
- **Priority:** Must-Have
- **Story Points:** 5
- **Acceptance Criteria:**
  - Given I navigate to Settings → SSO, then I can choose between SAML 2.0 and OIDC and enter IdP metadata (metadata URL or XML upload for SAML; client ID, secret, discovery URL for OIDC).
  - Given SSO is configured and a user logs in via SSO, then their profile is created or updated from the IdP assertions (name, email, groups).
  - Given SSO is enabled, when I toggle "Enforce SSO", then password-based login is disabled for all non-Super Admin members of this workspace.
  - Given an SSO login fails due to IdP error, then a friendly error page is shown with a support contact link and a fallback login option for Super Admins.

---

**US-WA-003** — As a Workspace Admin, I want to customize workspace branding (logo, colors, custom CSS) so that the knowledge base matches our company's visual identity.

- **Epic:** EP-04
- **Priority:** High
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given I am on the Branding settings page, then I can upload a logo (PNG/SVG, max 2 MB), set a primary color, and set a secondary color via a color picker.
  - Given I upload a logo, then it is stored in S3 and displayed on the workspace home, nav bar, and widget within 60 seconds.
  - Given I enter custom CSS (max 10 KB), then it is injected into the knowledge base page's `<head>` after the default Tailwind stylesheet.
  - Given I preview branding changes before saving, then a preview panel renders the workspace home with the proposed changes without affecting live readers.

---

**US-WA-004** — As a Workspace Admin, I want to set up the help widget so that my product team can embed contextual help in our application.

- **Epic:** EP-01
- **Priority:** Must-Have
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given I am on the Widget settings page, then I see an embed code snippet I can copy to my clipboard.
  - Given I configure widget appearance (color, icon, title, position), then the changes are reflected in the live preview within the settings page.
  - Given I configure URL-to-collection mappings (e.g., `/billing/*` → Billing Help collection), then the widget shows contextually relevant articles on matching host pages.
  - Given I click "Test Widget", then a new browser tab opens with a test harness page showing the widget as it will appear in a host application.

---

**US-WA-005** — As a Workspace Admin, I want to view workspace-level analytics so that I can measure content effectiveness and identify areas for improvement.

- **Epic:** EP-05
- **Priority:** High
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given the Analytics dashboard, then I see an overview with total pageviews, unique readers, average helpfulness score, search-no-result rate, and deflection rate over the last 30 days.
  - Given I click on a metric, then a drill-down view shows the metric over time as a line chart with daily granularity.
  - Given I navigate to "Search Analytics", then I see a table of top 50 search queries with result count and click-through rate.
  - Given I click "Export Report", then a CSV is generated asynchronously and a download link is emailed to me within 5 minutes.

---

**US-WA-006** — As a Workspace Admin, I want to configure IP allowlisting for my workspace so that only users on our corporate network can access internal content.

- **Epic:** EP-04
- **Priority:** High
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given I am on the Security settings page, then I can enter one or more CIDR ranges in the IP Allowlist and enable/disable the feature with a toggle.
  - Given IP allowlisting is enabled, when a request arrives from a non-allowed IP, then all authenticated API requests return 403 with message "Access restricted by IP policy."
  - Given IP allowlisting is enabled, then public articles remain accessible without restriction (allowlist only applies to authenticated/internal content).
  - Given I add my current IP automatically by clicking "Add my current IP", then my detected IP is pre-filled in the CIDR field.

---

**US-WA-007** — As a Workspace Admin, I want to export all workspace content as a ZIP archive so that I can migrate, backup, or hand off the knowledge base.

- **Epic:** EP-04
- **Priority:** High
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given I click "Export Workspace" in the Danger Zone settings, then a confirmation dialog warns about the operation and I must type the workspace slug to confirm.
  - Given confirmed, then a BullMQ job is created, a progress indicator is shown, and I receive an email with a download link when complete (expected within 15 minutes for workspaces up to 10 000 articles).
  - Given the export ZIP is downloaded, then it contains: `/articles/{id}.md` for each article, `/metadata.json` with workspace/space/collection/tag structure, and `/media/` with all attached files.
  - Given the export link, then it is a time-limited pre-signed S3 URL valid for 24 hours.

---

**US-WA-008** — As a Workspace Admin, I want to configure content retention policies so that outdated articles are automatically archived after a defined period.

- **Epic:** EP-01
- **Priority:** Medium
- **Story Points:** 2
- **Acceptance Criteria:**
  - Given the Content Policy settings, then I can enable an auto-archive policy with a configurable inactivity window (minimum 6 months, maximum 5 years).
  - Given the policy is enabled, then articles not updated within the configured window are automatically moved to "Archived" status on a nightly job.
  - Given an article is auto-archived, then its Author and assigned Editor receive a notification with a link to restore it.
  - Given I disable the policy, then no further auto-archiving occurs; previously archived articles remain archived.

---

## 7. Super Admin Stories

Super Admins have platform-wide authority. They manage all workspaces, billing, compliance, security, and system health.

---

**US-SA-001** — As a Super Admin, I want to create and configure new workspaces so that new teams or customers can be onboarded onto the platform.

- **Epic:** EP-04
- **Priority:** Must-Have
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given I am on the Super Admin → Workspaces page, when I click "New Workspace", then a form collects name, slug, owner email, plan tier, and member/storage quotas.
  - Given the workspace is created, then a default Space named "General" and a default Collection named "Getting Started" are automatically provisioned.
  - Given the owner email is provided, then an invitation email is sent to that address with Workspace Admin privileges.
  - Given I set a custom subdomain (`{slug}.kb.example.com`), then it is routed within 60 seconds and an SSL certificate is provisioned automatically.

---

**US-SA-002** — As a Super Admin, I want to view the global audit log across all workspaces so that I can investigate security incidents and compliance issues.

- **Epic:** EP-04
- **Priority:** Must-Have
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given I open the Audit Log page, then I see a searchable, filterable log of all sensitive actions across all workspaces, with actor, workspace, action type, timestamp, and IP address.
  - Given I filter by workspace, action type (e.g., "role_change"), actor, or date range, then results update in real time.
  - Given I click a log entry, then a detail panel shows the full before/after JSON of the changed entity.
  - Given I export the audit log, then a CSV is generated with all visible columns and delivered as a download within 2 minutes.
  - Given a log entry was generated by an impersonated action, then it is marked with `[Impersonated by: {super_admin_name}]` in the actor column.

---

**US-SA-003** — As a Super Admin, I want to impersonate any workspace member for debugging purposes so that I can reproduce reported issues in the exact context of the affected user.

- **Epic:** EP-04
- **Priority:** Medium
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given I navigate to any workspace member's profile in the Super Admin panel, when I click "Impersonate", then a confirmation dialog requires me to enter a reason (min 20 chars).
  - Given I confirm impersonation, then I am logged in as the target user and an impersonation banner is displayed at the top of every page during the session.
  - Given impersonation is active, then all actions I perform are recorded in the audit log as `{target_user} (impersonated by {super_admin})`.
  - Given I click "End Impersonation" in the banner, then I am returned to my Super Admin session immediately.

---

**US-SA-004** — As a Super Admin, I want to suspend a workspace so that I can temporarily disable access for a workspace that is in violation of terms of service.

- **Epic:** EP-04
- **Priority:** High
- **Story Points:** 2
- **Acceptance Criteria:**
  - Given I click "Suspend Workspace" on a workspace in the Super Admin panel, then I must enter a reason (min 50 chars) and confirm.
  - Given the workspace is suspended, then all members (except Super Admins) receive a 403 response with a "Workspace suspended" message on all API and UI requests.
  - Given the workspace is suspended, then public articles served via the custom domain display a maintenance page.
  - Given I click "Lift Suspension", then access is restored immediately and an email is sent to the Workspace Admin.

---

**US-SA-005** — As a Super Admin, I want to manage platform-wide AI feature settings and monitor OpenAI API usage so that I can control costs and ensure compliant AI usage.

- **Epic:** EP-03
- **Priority:** High
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given the AI Settings page in the Super Admin panel, then I can view total monthly OpenAI token consumption broken down by workspace and feature type (Q&A, summarization, auto-tagging, draft generation).
  - Given a workspace exceeds its monthly AI token quota, then AI features are automatically throttled and the Workspace Admin is notified.
  - Given I toggle "Disable AI Globally", then all AI features are immediately disabled across all workspaces with a platform-wide maintenance banner.
  - Given I click "Review Prompt Logs", then I can view the last 1 000 PII-stripped prompts sent to OpenAI, their token counts, and response latencies.

---

**US-SA-006** — As a Super Admin, I want to manage the global Elasticsearch index health and trigger re-indexing so that search quality is maintained after bulk content migrations.

- **Epic:** EP-02
- **Priority:** High
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given the Search Infrastructure page, then I see index stats: document count, index size, query latency (p50/p95/p99), and last full-indexing timestamp.
  - Given I click "Trigger Full Re-index", then a BullMQ job is queued that re-indexes all published articles across all workspaces in batches of 500.
  - Given re-indexing is in progress, then a progress bar shows completed/total documents and estimated time remaining.
  - Given re-indexing encounters errors for specific documents, then a log lists the failed article IDs with error messages for investigation.

---

**US-SA-007** — As a Super Admin, I want to configure and enforce platform-wide security policies (password complexity, MFA, session duration) so that the platform meets organizational security standards.

- **Epic:** EP-04
- **Priority:** High
- **Story Points:** 3
- **Acceptance Criteria:**
  - Given the Security Policies page, then I can set: minimum password length (8–64), required character classes, MFA requirement (optional/required for all/required for admins), and session timeout (1–168 hours).
  - Given MFA is set to "Required for all", then users without MFA enrolled are forced through the MFA setup flow on next login before accessing any workspace.
  - Given a session timeout is configured, then access tokens expire after the configured duration and refresh tokens are invalidated after the configured multiple.
  - Given I change a policy, then the change is recorded in the global audit log with the before/after values and takes effect within 5 minutes.

---

**US-SA-008** — As a Super Admin, I want to trigger a right-to-erasure (GDPR Article 17) deletion for a specific user so that we can fulfill data subject requests within the required 30-day window.

- **Epic:** EP-04
- **Priority:** Must-Have
- **Story Points:** 5
- **Acceptance Criteria:**
  - Given I search for a user by email in the GDPR Erasure panel, when found, I can click "Initiate Erasure" with a request reference number.
  - Given erasure is initiated, then a BullMQ job is queued that: anonymizes the user record (replaces name/email with hashed values), removes SSO identifiers, removes feedback submissions, and replaces article authorship attribution with "Deleted User".
  - Given erasure completes, then a confirmation record is stored (erasure request ID, timestamp, completion status) for compliance evidence — the confirmation record itself contains no PII.
  - Given the erasure job encounters an error, then the Super Admin is notified via email with the failed steps listed so that they can be retried or manually addressed.

---

## 8. Operational Policy Addendum

### 8.1 Content Governance Policies

All articles must pass through the full editorial lifecycle before public visibility. No Author may publish directly; all publications require Editor approval. Editors must review submitted articles within 5 business days. Articles idle in review for more than 10 business days trigger Workspace Admin escalation. Published articles are retained indefinitely unless a Workspace Admin configures a retention window (minimum 6 months). Audit logs of all content mutations are retained for 24 months and cannot be deleted by Workspace Admins.

### 8.2 Reader Data Privacy Policies

Reader PII is processed under GDPR and CCPA legal bases. IP addresses are truncated to /24 (IPv4) before analytics storage; full IPs are never persisted. Session IDs are daily-rotated salted hashes to prevent cross-day linkage. Cookie consent banners are displayed for EU/EEA/UK visitors before any non-essential cookies are set. Workspace Admins see only aggregate analytics; individual reader journeys are accessible only to Super Admins for fraud investigation.

### 8.3 AI Usage Policies

All content sent to OpenAI is governed by the OpenAI Enterprise Data Processing Agreement. PII is stripped from prompts before transmission via regex and NER pre-processing. AI features can be disabled per-workspace by Workspace Admins and per-article by Authors. AI responses are not persisted beyond the request lifecycle unless explicitly cached. Token usage is monitored and quotaed per workspace, with automatic throttling on overuse.

### 8.4 System Availability Policies

Platform API and frontend SLA: 99.9% monthly uptime. AI Assistant SLA: 99.5% (OpenAI dependency). Widget CDN SLA: 99.99% (CloudFront). RTO: ≤ 1 hour. RPO: ≤ 15 minutes (RDS Multi-AZ + WAL shipping). Severity 1 (full outage): on-call within 5 min, status page within 10 min, customer comms within 30 min. Mandatory post-incident review within 5 business days for Severity 1 and 2 events.
