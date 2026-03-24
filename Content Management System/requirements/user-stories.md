# User Stories

## Reader User Stories

### Account & Subscription

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| RDR-001 | As a reader, I want to register with my email so that I can comment and subscribe | - Email validation<br>- Verification link sent<br>- Profile created on confirmation |
| RDR-002 | As a reader, I want to log in with Google so that I can access quickly | - OAuth2 redirect works<br>- Account created on first login<br>- Existing email linked |
| RDR-003 | As a reader, I want to reset my password so that I can recover my account | - Reset link sent<br>- Link expires in 24 h<br>- Password updated and session invalidated |
| RDR-004 | As a reader, I want to subscribe to the site newsletter so that I receive new posts | - Subscribe form visible<br>- Confirmation email sent<br>- Double opt-in compliant |
| RDR-005 | As a reader, I want to manage my notification preferences so that I only receive relevant emails | - Preference centre reachable<br>- Unsubscribe from any category<br>- One-click global unsubscribe |

### Content Discovery

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| RDR-006 | As a reader, I want to browse posts by category so that I can find relevant content | - Category pages load<br>- Post count shown<br>- Pagination works |
| RDR-007 | As a reader, I want to search posts by keyword so that I can find specific content | - Results appear within 400 ms<br>- Typo tolerance applied<br>- Excerpt highlights match |
| RDR-008 | As a reader, I want to view an author profile so that I can discover their work | - Bio and avatar shown<br>- Post list paginated<br>- Social links visible |
| RDR-009 | As a reader, I want to subscribe to an RSS feed so that I can read content in my reader app | - Feed URL discoverable<br>- Valid Atom/RSS format<br>- Per-author and per-category feeds available |

### Commenting

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| RDR-010 | As a reader, I want to leave a comment on a post so that I can share my thoughts | - Comment form accessible<br>- Submission queued or published per moderation setting<br>- Spam check applied |
| RDR-011 | As a reader, I want to reply to existing comments so that I can join a thread | - Reply button visible<br>- Thread indented correctly<br>- Parent notified of reply |
| RDR-012 | As a reader, I want to be notified of replies to my comment so that I can continue the discussion | - Email notification sent<br>- In-thread reply count updated<br>- Unsubscribe from thread available |

---

## Author User Stories

### Account & Profile

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| AUT-001 | As an author, I want to accept an invitation so that I can join the site | - Invitation email received<br>- Accept link sets password<br>- Author role assigned |
| AUT-002 | As an author, I want to update my bio and avatar so that readers know me | - Bio editor available<br>- Avatar upload works<br>- Changes reflected on author page |
| AUT-003 | As an author, I want to set up 2FA so that my account is secure | - TOTP or email OTP configurable<br>- Backup codes provided<br>- Login challenged when enabled |

### Content Creation

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| AUT-004 | As an author, I want to create a new post so that I can publish my writing | - Rich text and Markdown modes available<br>- Auto-save every 60 s<br>- Post saved as Draft on creation |
| AUT-005 | As an author, I want to embed images in my post so that content is visually rich | - Upload from device or media library<br>- Alt text field present<br>- Responsive image sizes generated |
| AUT-006 | As an author, I want to assign categories and tags to my post so that it is discoverable | - Category tree selector shown<br>- Tag autocomplete works<br>- At least one category required for submission |
| AUT-007 | As an author, I want to preview my post before submitting so that I can check formatting | - Preview renders in active theme<br>- Opens in new tab or overlay<br>- Draft changes reflected |
| AUT-008 | As an author, I want to submit my post for editorial review so that it can be published | - Submit button transitions post to Pending Review<br>- Assigned editor notified<br>- Post locked from further edit until returned |
| AUT-009 | As an author, I want to see revision history so that I can track changes | - All saves listed with timestamp<br>- Diff between two revisions shown<br>- Restore to any revision available |
| AUT-010 | As an author, I want to set an SEO title and meta description so that search engines index my post correctly | - SEO fields in sidebar<br>- Character counters shown<br>- Preview of search snippet visible |

### Analytics

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| AUT-011 | As an author, I want to view the performance of my posts so that I can improve my writing | - View count per post<br>- Comment count per post<br>- Top posts by views shown |
| AUT-012 | As an author, I want to see comment notifications so that I can engage with readers | - Bell icon shows unread count<br>- Click navigates to comment<br>- Mark-all-read available |

---

## Editor User Stories

### Review & Publishing

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| EDT-001 | As an editor, I want to see all pending submissions so that I can process them | - Submission queue filterable by author and date<br>- Post age indicator shown<br>- Bulk actions available |
| EDT-002 | As an editor, I want to review a submitted post so that I can assess quality | - Full post preview in editor<br>- Inline comment tool available<br>- Submission metadata shown |
| EDT-003 | As an editor, I want to approve and publish a post so that readers can see it | - Publish button transitions post to Published<br>- Author notified<br>- Post appears in feeds immediately |
| EDT-004 | As an editor, I want to return a post to draft with feedback so that the author can revise | - Reject/return action available<br>- Feedback field required<br>- Author notified with feedback |
| EDT-005 | As an editor, I want to schedule a post for future publication so that it goes live at the right time | - Datetime picker available<br>- Post transitions to Scheduled state<br>- Reminder notification sent to author |
| EDT-006 | As an editor, I want to edit a submitted post directly so that minor corrections are fast | - Edit mode unlocked for editors<br>- Original author attribution preserved<br>- Revision logged with editor as actor |

### Taxonomy & Category Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| EDT-007 | As an editor, I want to create and edit categories so that content is well-organized | - Category CRUD available<br>- Parent-child hierarchy supported<br>- Slug auto-generated |
| EDT-008 | As an editor, I want to merge duplicate tags so that taxonomy is clean | - Tag merge tool available<br>- Posts re-tagged automatically<br>- Old tag redirects to new |

---

## Administrator User Stories

### Site Configuration

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ADM-001 | As an admin, I want to configure site settings so that the platform behaves correctly | - Site name, tagline, URL, and timezone settable<br>- Settings saved and applied immediately<br>- Audit log entry created |
| ADM-002 | As an admin, I want to install and activate a theme so that the site looks as intended | - Theme upload and marketplace install work<br>- Live preview before activation<br>- Rollback to previous theme available |
| ADM-003 | As an admin, I want to manage widget zones so that each page area has the right content | - All zones listed per active theme<br>- Drag-and-drop widget placement works<br>- Per-instance configuration saved independently |
| ADM-004 | As an admin, I want to configure navigation menus so that visitors can find content | - Menu builder with pages, posts, and custom links<br>- Multiple menus assignable to theme zones<br>- Reorder by drag-and-drop |
| ADM-005 | As an admin, I want to manage plugins so that additional features are available | - Plugin install, activate, deactivate, and uninstall work<br>- Compatibility check before activation<br>- Plugin settings page registered |

### User & Role Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ADM-006 | As an admin, I want to invite authors so that new contributors can join | - Invitation email sent with time-limited link<br>- Role selectable at invite time<br>- Invitation revocable before acceptance |
| ADM-007 | As an admin, I want to change a user's role so that permissions are accurate | - Role selector on user profile<br>- Change logged in audit trail<br>- User notified of role change |
| ADM-008 | As an admin, I want to suspend a user so that access is revoked immediately | - Suspend action available<br>- All active sessions invalidated<br>- User status shown as Suspended |

### Content Moderation

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ADM-009 | As an admin, I want to moderate comments so that quality is maintained | - Comment queue available<br>- Approve, reject, and spam actions present<br>- Bulk moderation supported |
| ADM-010 | As an admin, I want to configure spam filter settings so that automated filtering is appropriate | - Spam filter threshold configurable<br>- Allowlist and blocklist terms manageable<br>- Manual override available |
| ADM-011 | As an admin, I want to manage redirect rules so that changed URLs don't break | - Redirect CRUD available<br>- Source and destination URL fields present<br>- 301 vs 302 selectable |

### Analytics & Reporting

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ADM-012 | As an admin, I want to view site-wide analytics so that I can understand audience trends | - Dashboard shows daily views, visitors, and top posts<br>- Date range filter available<br>- Export to CSV available |
| ADM-013 | As an admin, I want to view author performance metrics so that I can identify contributors | - Per-author post count, total views, and comments shown<br>- Sortable table<br>- Data refreshed daily |
| ADM-014 | As an admin, I want to export subscriber lists so that I can use them in email tools | - CSV export with email, name, and subscription date<br>- GDPR consent flag included<br>- Download secured to admin only |

---

## Super Admin User Stories

### Multi-Site Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| SUP-001 | As a super admin, I want to create a new site so that a new blog is onboarded | - Site creation form available<br>- Domain, slug, and owner configurable<br>- Default theme applied |
| SUP-002 | As a super admin, I want to view aggregate analytics across all sites so that I can monitor the network | - Network dashboard shows total views and posts<br>- Per-site breakdown available<br>- Exportable |
| SUP-003 | As a super admin, I want to push plugin updates to all sites so that security patches are applied quickly | - Bulk update action available<br>- Progress shown per site<br>- Rollback available if update fails |
| SUP-004 | As a super admin, I want to manage global user accounts so that cross-site contributors are centrally controlled | - Global user list with site membership shown<br>- Disable account globally available<br>- Audit log for all cross-site actions |
