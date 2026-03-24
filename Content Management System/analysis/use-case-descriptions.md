# Use Case Descriptions

## Overview
Detailed descriptions of the primary use cases for the CMS platform.

---

## UC-001: Create and Publish a Post

| Field | Detail |
|-------|--------|
| **Use Case ID** | UC-001 |
| **Name** | Create and Publish a Post |
| **Actor(s)** | Author, Editor |
| **Preconditions** | User is authenticated with Author or Editor role |
| **Post-conditions** | Post is published and visible to readers; RSS feed and sitemap are updated |
| **Trigger** | Author clicks "New Post" |

### Main Flow
1. Author opens the post editor.
2. Author writes content using the rich text or Markdown editor.
3. Author uploads or selects a featured image from the media library.
4. Author assigns one or more categories and tags.
5. Author sets SEO title, meta description, and OG image (optional).
6. Author clicks **Save Draft** – system auto-saves and stores a revision.
7. Author clicks **Preview** – system renders the post in the active theme in a new tab.
8. Author clicks **Submit for Review** – post state transitions to **Pending Review**; assigned editor is notified.
9. Editor opens the review queue, opens the submission, and previews it.
10. Editor clicks **Publish** – post state transitions to **Published**.
11. System triggers: feed update, sitemap rebuild, subscriber notification dispatch.

### Alternative Flows
- **A1 – Editor publishes directly**: Editor skips submission queue and publishes own post.
- **A2 – Scheduled publish**: At step 10, editor sets a future datetime; post transitions to **Scheduled**; system publishes at the specified time.
- **A3 – Return to draft**: At step 10, editor clicks **Return to Draft** with feedback; post returns to **Draft**; author is notified with feedback.

### Exception Flows
- **E1 – Auto-save fails**: System shows unsaved-changes warning; author can manually save.
- **E2 – Media upload fails**: System shows error; draft is preserved without the image.

---

## UC-002: Customize Widget Layout

| Field | Detail |
|-------|--------|
| **Use Case ID** | UC-002 |
| **Name** | Customize Widget Layout |
| **Actor(s)** | Administrator |
| **Preconditions** | Admin is authenticated; at least one theme is active |
| **Post-conditions** | Widget layout is saved; all visitors see the updated layout |
| **Trigger** | Admin navigates to Appearance → Widgets |

### Main Flow
1. Admin opens the Widget Manager.
2. System displays layout zones defined by the active theme (e.g., Header, Primary Sidebar, Footer Left, Footer Right).
3. System displays the Widget Library panel with available widgets.
4. Admin drags a widget (e.g., **Recent Posts**) from the library into a zone.
5. System opens the widget configuration form.
6. Admin sets configuration (e.g., number of posts = 5, show thumbnail = true).
7. Admin clicks **Save Widget**.
8. Admin reorders widgets within a zone by dragging.
9. Admin clicks **Save Layout**.
10. System persists the layout; all pages render the updated zones.

### Alternative Flows
- **A1 – Remove widget**: Admin clicks the ✕ on a placed widget; widget is removed from the zone.
- **A2 – Per-page override**: Admin navigates to a specific page and enables a layout override; widget zones for that page are configured independently.
- **A3 – Preview changes**: Admin clicks **Preview** before saving; changes are visible only in the preview session.

### Exception Flows
- **E1 – Zone incompatible with widget**: System warns the admin that the widget has a minimum width requirement; admin can proceed or cancel.

---

## UC-003: Moderate Comments

| Field | Detail |
|-------|--------|
| **Use Case ID** | UC-003 |
| **Name** | Moderate Comments |
| **Actor(s)** | Editor, Administrator |
| **Preconditions** | Comment moderation is enabled in site settings |
| **Post-conditions** | Comment is approved (visible to all), rejected (deleted), or marked as spam (filtered) |
| **Trigger** | New comment is submitted; moderator opens the comment queue |

### Main Flow
1. Reader submits a comment on a published post.
2. System passes comment to spam filter; spam score is stored.
3. If spam score is below threshold, comment is placed in **Pending** queue; post author is notified.
4. Moderator opens the Comment Queue.
5. Moderator reads the comment and its context.
6. Moderator clicks **Approve** – comment state changes to **Approved**; comment is visible on the post; commenter is not notified.
7. Commenter whose parent comment was replied to receives a reply notification.

### Alternative Flows
- **A1 – Reject**: Moderator clicks **Reject** – comment is deleted; commenter is not notified.
- **A2 – Spam**: Moderator clicks **Spam** – comment is moved to spam folder; commenter IP/email added to spam list.
- **A3 – Auto-approved**: If spam score is very low and trust level is high (registered reader with approved history), comment bypasses queue and is published immediately.
- **A4 – Bulk moderation**: Moderator selects multiple comments and applies a bulk action (Approve All / Spam All / Delete All).

### Exception Flows
- **E1 – Spam filter unavailable**: System logs the error and places all comments in the pending queue automatically.

---

## UC-004: Install and Configure a Plugin

| Field | Detail |
|-------|--------|
| **Use Case ID** | UC-004 |
| **Name** | Install and Configure a Plugin |
| **Actor(s)** | Administrator |
| **Preconditions** | Admin is authenticated; internet access available for marketplace install |
| **Post-conditions** | Plugin is active and its features are available |
| **Trigger** | Admin navigates to Plugins → Add New |

### Main Flow
1. Admin searches the plugin marketplace or uploads a plugin package.
2. System displays plugin details: description, author, version, compatibility, and ratings.
3. Admin clicks **Install**.
4. System downloads and extracts the plugin; verifies API and hook compatibility.
5. System shows the **Activate** button.
6. Admin clicks **Activate** – plugin hooks are registered; plugin menu item appears in admin sidebar.
7. Admin navigates to the plugin's settings page.
8. Admin configures plugin-specific settings and saves.

### Alternative Flows
- **A1 – Incompatible plugin**: At step 4, if compatibility check fails, system shows a warning with details; admin may proceed at own risk or cancel.
- **A2 – Deactivate**: Admin clicks **Deactivate** – hooks are unregistered; plugin data is preserved; settings page is removed from sidebar.
- **A3 – Uninstall**: Admin clicks **Uninstall** after deactivation – plugin files and optionally its data are removed.

### Exception Flows
- **E1 – Upload fails**: System displays the error message; admin retries or chooses marketplace install.

---

## UC-005: Subscribe to Newsletter

| Field | Detail |
|-------|--------|
| **Use Case ID** | UC-005 |
| **Name** | Subscribe to Newsletter |
| **Actor(s)** | Reader |
| **Preconditions** | Newsletter subscription widget is placed on the site |
| **Post-conditions** | Reader is subscribed and will receive new-post digest emails |
| **Trigger** | Reader submits the subscription form |

### Main Flow
1. Reader enters their email in the Newsletter Signup widget.
2. Reader clicks **Subscribe**.
3. System validates the email format.
4. System sends a double opt-in confirmation email.
5. Reader clicks the confirmation link in the email.
6. System marks the subscription as confirmed and associates it with the site.
7. System sends a welcome email to the reader.

### Alternative Flows
- **A1 – Already subscribed**: System informs the reader they are already subscribed; no duplicate entry created.
- **A2 – Unsubscribe**: Reader clicks the one-click unsubscribe link in any digest email; subscription is deleted; confirmation page shown.

### Exception Flows
- **E1 – Email provider unavailable**: System queues the confirmation email and retries; reader sees a "check your inbox shortly" message.

---

## UC-006: Manage Revision History

| Field | Detail |
|-------|--------|
| **Use Case ID** | UC-006 |
| **Name** | Manage Revision History |
| **Actor(s)** | Author, Editor |
| **Preconditions** | Post exists with at least two saved revisions |
| **Post-conditions** | Selected revision is restored as the current draft |
| **Trigger** | Author or editor clicks "Revision History" in the post editor |

### Main Flow
1. User opens the Revision History panel for a post.
2. System lists all revisions with timestamp, actor, and change summary.
3. User selects two revisions to compare.
4. System renders a side-by-side diff highlighting added and removed content.
5. User selects the revision to restore.
6. User clicks **Restore This Revision**.
7. System saves the restored content as a new revision (so the restore action is itself reversible).
8. Post editor refreshes with the restored content.

### Alternative Flows
- **A1 – Single revision view**: User clicks a single revision to preview its full content without a diff.

### Exception Flows
- **E1 – Revision data corrupted**: System shows an error and excludes the corrupted revision from the list.
