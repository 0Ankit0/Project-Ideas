# Use-Case Descriptions — Social Networking Platform

---

## UC-001: Register & Onboard Account

**Actor:** Guest  
**Preconditions:** The guest has a valid email address or mobile phone number not previously registered on the platform.  
**Postconditions:** A new `User`, `UserProfile`, and `UserCredential` record are created. The user is authenticated and redirected to the interest-selection onboarding step. A welcome email is dispatched by the System.

### Primary Flow
1. Guest navigates to the registration page and selects sign-up method (email, phone, or OAuth via Google/Apple).
2. Guest enters their email address (or phone number) and a password meeting complexity requirements.
3. System validates the email is not already registered and that the password meets the minimum policy (min 8 characters, at least one number and one symbol).
4. System creates a pending `UserCredential` record and sends a one-time verification code to the provided email/phone.
5. Guest enters the verification code within the 10-minute window.
6. System marks the credential as verified, creates the `User` and `UserProfile` records with default privacy settings (posts: friends-only, profile: public).
7. System presents the onboarding wizard: upload avatar → set display name → select up to 5 interest categories → follow 3 suggested accounts.
8. Guest completes onboarding and is redirected to the personalised feed (empty state with suggestions).

### Alternate Flows

#### AF-001-01: OAuth Sign-Up (Google / Apple)
1a. Guest selects "Continue with Google" or "Continue with Apple."  
1b. System redirects to the OAuth provider's consent screen.  
1c. On successful OAuth token exchange, System extracts verified email and name from the token.  
1d. System creates `UserCredential` (OAuth type) and `UserProfile`, skipping step 5 (email already verified by provider).  
1e. Flow resumes at step 7.

#### AF-001-02: Guest Skips Onboarding
7a. Guest taps "Skip" on the onboarding wizard.  
7b. System records the onboarding as incomplete and redirects to an empty feed.  
7c. A nudge notification is scheduled for 24 hours later prompting the user to complete their profile.

### Exception Flows

#### EF-001-01: Email Already Registered
3a. System detects the email is already linked to an active account.  
3b. System displays "An account with this email already exists. Log in or reset your password." No new record is created.

#### EF-001-02: Verification Code Expired
5a. Guest enters the code after the 10-minute expiry.  
5b. System invalidates the code and offers to resend a fresh code. The pending `UserCredential` record is retained for 1 hour before cleanup.

#### EF-001-03: Underage Registration Blocked
3a. Guest enters a date of birth indicating age under 13 (or under 16 in GDPR jurisdictions).  
3b. System blocks registration and displays a localised age restriction message. No record is created.

---

## UC-002: Create & Publish Post

**Actor:** RegisteredUser, ContentCreator  
**Preconditions:** The user is authenticated and their account is in good standing (not suspended or restricted).  
**Postconditions:** A `Post` record is persisted. Associated `PostMedia`, `PostTag`, `Mention`, and `Hashtag` records are created. The post is enqueued for AI content screening. Upon passing screening, the post is distributed to followers' feeds via the `FeedItem` fan-out service.

### Primary Flow
1. User opens the post composer and selects post type: text, photo, video, poll, or reel.
2. User enters the post body text (max 2 000 characters for standard posts).
3. User optionally attaches media: selects up to 10 images or 1 video (max 500 MB, MP4/MOV/WebM).
4. System generates thumbnail previews for uploaded media and stores originals to object storage, recording `PostMedia` records.
5. User optionally tags up to 5 other users via the `@mention` autocomplete, adding `Mention` records.
6. User optionally inserts `#hashtags`; System resolves or creates `Hashtag` records and links via `PostTag`.
7. User selects audience visibility: Public, Followers, Friends, Close Friends, or Only Me.
8. User taps "Post." System creates the `Post` record in `PENDING_REVIEW` state and submits it to the AI Moderation Service.
9. AI Moderation Service evaluates the post for policy violations (NSFW, hate speech, spam, dangerous content). This completes within 2 seconds for text-only posts, up to 30 seconds for video.
10. Post passes screening; System transitions the post to `PUBLISHED` state and triggers the feed fan-out job for all followers.
11. Mentioned users receive in-app notifications. Hashtag trend counters are incremented.

### Alternate Flows

#### AF-002-01: Schedule Post (ContentCreator)
7a. ContentCreator selects "Schedule" instead of "Post Now."  
7b. ContentCreator selects a future date and time (up to 30 days ahead).  
7c. System saves the post in `SCHEDULED` state. No fan-out occurs until the scheduled time triggers the publishing job.

#### AF-002-02: Poll Post
2a. User selects "Poll" post type.  
2b. User enters the poll question and 2–4 answer options; sets duration (1 hour to 7 days).  
2c. System creates a `Poll` record linked to the `Post`. Voting is tracked in real-time against the `Poll` entity.

#### AF-002-03: Post to Community
7a. User selects a Community as the target instead of their own timeline.  
7b. If the community requires moderator approval, the post is placed in `COMMUNITY_PENDING` state until a community moderator approves it.

### Exception Flows

#### EF-002-01: AI Moderation Rejects Post
9a. AI Moderation flags the post with high-confidence policy violation.  
9b. System transitions the post to `REJECTED` state. User receives an in-app notification explaining the category of violation and a link to appeal.  
9c. Post is added to the `ModerationQueue` for human review within 24 hours.

#### EF-002-02: Media Upload Failure
4a. Object storage upload fails (network error or file corrupt).  
4b. System retries upload up to 3 times. On third failure, the user is shown an error and the draft is saved locally. Media records are not created.

#### EF-002-03: Video Exceeds Duration Limit
3a. User uploads a video exceeding the 10-minute limit for standard posts.  
3b. System rejects the file before upload and prompts the user to trim or use the Reel format.

---

## UC-003: Follow / Unfollow User

**Actor:** RegisteredUser  
**Preconditions:** The user is authenticated. The target account exists and has not blocked the user.  
**Postconditions:** A `Follow` record is created (or deleted). The follower's feed is updated to include (or remove) future posts from the target. Follow counts on both profiles are updated.

### Primary Flow
1. User navigates to the target's profile page.
2. User taps the "Follow" button.
3. System checks: (a) no existing `Block` record in either direction, (b) the target account is active.
4. If the target account is public, System immediately creates a `Follow` record. The "Follow" button changes to "Following."
5. Target user receives an in-app notification: "[User] started following you."
6. System updates `follower_count` on the target's `UserProfile` and `following_count` on the follower's `UserProfile`.
7. Feed fan-out service backfills up to 20 recent posts from the newly followed account into the follower's feed.

### Alternate Flows

#### AF-003-01: Follow Private Account
4a. The target account has `is_private = true`.  
4b. System creates a `FriendRequest` record in `PENDING` state rather than a `Follow` record.  
4c. "Follow" button changes to "Requested."  
4d. Target receives a follow request notification. Target can accept (creates `Follow`) or decline (deletes `FriendRequest`).

#### AF-003-02: Unfollow
2a. User taps "Following" (toggle) on a profile they already follow.  
2b. System deletes the `Follow` record and decrements follower/following counts.  
2c. No notification is sent to the unfollowed user.  
2d. Feed fan-out service marks the target's posts as lower priority in the user's feed; they will age out of `FeedItem` within 24 hours.

### Exception Flows

#### EF-003-01: Target Has Blocked the Actor
3a. System detects a `Block` record where `blocker_id = target` and `blocked_id = actor`.  
3b. From the actor's perspective, the target's profile appears as if it does not exist (404 profile view). No follow action is taken.

---

## UC-004: View Personalised Feed

**Actor:** RegisteredUser, System  
**Preconditions:** The user is authenticated.  
**Postconditions:** The user's feed is rendered with a ranked, paginated list of `FeedItem` records. Impression events are recorded.

### Primary Flow
1. User opens the app home screen.
2. System queries the `Feed` record for the user, retrieving the top 25 `FeedItem` entries ordered by `ranking_score DESC`.
3. `FeedItem` entries reference `Post` records. System fetches post content, author profiles, reaction counts, and comment counts in a single batched read.
4. System applies real-time filters: remove posts from blocked users, remove posts whose visibility does not include the current user, remove expired stories.
5. System renders the feed. Each visible post fires an impression event consumed by the `FeedRanking` service asynchronously.
6. As the user scrolls past the 20th item, System triggers pagination, fetching the next 25 `FeedItem` entries.
7. `FeedRanking` engine processes impression events and engagement signals (dwell time, reactions, comments, shares) to update `ranking_score` values for future sessions.

### Alternate Flows

#### AF-004-01: Chronological Feed Toggle
2a. User switches to "Latest" mode.  
2b. System bypasses `ranking_score` ordering and returns posts sorted by `created_at DESC` for all followed accounts.

#### AF-004-02: Empty Feed (New User)
2a. User has fewer than 3 follows; `FeedItem` table has no entries for the user.  
2b. System returns a curated "Discover" feed populated by trending posts and suggested accounts in the user's stated interest categories.

### Exception Flows

#### EF-004-01: Feed Service Unavailable
2a. Feed service returns a 503 or times out.  
2b. System serves a cached snapshot of the last-seen feed (up to 1 hour stale) from edge cache.  
2c. A "Feed is temporarily limited" banner is shown at the top of the screen.

---

## UC-005: Send Direct Message

**Actor:** RegisteredUser  
**Preconditions:** The sender is authenticated. The recipient exists, has not blocked the sender, and has not set their DM privacy to "No one."  
**Postconditions:** A `DirectMessage` record is persisted. The message is delivered to the recipient via WebSocket (if online) or push notification (if offline). Message content is stored encrypted at rest using E2E encryption keys.

### Primary Flow
1. User opens the Messaging inbox and selects an existing conversation or taps "New Message."
2. For a new conversation, user searches for and selects the recipient.
3. System validates that no `Block` record exists in either direction and that the recipient's DM privacy allows messages from the sender (e.g., "Everyone" or "Followers only").
4. User types the message body (max 5 000 characters) and/or attaches media (image, video, audio, GIF).
5. User taps "Send." System encrypts the message payload using the recipient's public key and the sender's private key (Signal Protocol / E2E).
6. System persists the `DirectMessage` record with the encrypted payload and metadata (sender, recipient, timestamp, message type).
7. System delivers the message to the recipient over WebSocket if the recipient is online; otherwise enqueues a push notification.
8. Sender UI shows a single grey tick (sent). When the server confirms delivery, it changes to a double grey tick. When the recipient opens the message, it changes to a double blue tick (read receipt).

### Alternate Flows

#### AF-005-01: Group Chat Message
2a. User selects an existing `GroupChat` or creates a new one (up to 256 members).  
2b. Message is encrypted for each group member's key individually and persisted.  
2c. Delivery and read receipts are aggregated per member.

#### AF-005-02: Disappearing Messages
3a. Either participant has enabled disappearing messages (1 hour, 24 hours, or 7 days).  
3b. System schedules a deletion job for each `DirectMessage` in the thread after the configured TTL, removing both the record and the encrypted payload from storage.

### Exception Flows

#### EF-005-01: Recipient Has Restricted DMs
3a. Recipient's DM privacy is "Followers only" and the sender does not follow the recipient.  
3b. System rejects the send action and shows "You can't send messages to this person."

#### EF-005-02: Message Delivery Failure
7a. Push notification delivery fails (invalid token, user has uninstalled the app).  
7b. System retries delivery using email fallback if the user's notification preferences include email for DMs.

---

## UC-006: React to Content

**Actor:** RegisteredUser  
**Preconditions:** The user is authenticated and the target post or comment is visible to them.  
**Postconditions:** A `Reaction` record is created (or updated/deleted). The post's reaction count is updated. The content author receives a notification.

### Primary Flow
1. User long-presses (or hovers over) the reaction button on a post or comment.
2. System displays the reaction picker with 6 options: Like 👍, Love ❤️, Haha 😂, Wow 😮, Sad 😢, Angry 😡.
3. User selects a reaction type.
4. System checks whether an existing `Reaction` record exists for this user on this target.
5. No existing reaction: System creates a new `Reaction` record with `reaction_type` and `target_type` (post/comment).
6. System increments the corresponding reaction count bucket on the `Post` or `Comment` record (denormalised counter for performance).
7. Author of the content receives an in-app notification: "[User] reacted to your post."

### Alternate Flows

#### AF-006-01: Change Reaction
4a. An existing `Reaction` record is found with a different `reaction_type`.  
4b. System updates the `reaction_type` in place and adjusts the counter buckets accordingly (decrement old type, increment new type).  
4c. Author receives no additional notification (de-duplicated).

#### AF-006-02: Remove Reaction (Un-react)
3a. User selects the same reaction type they already applied.  
3b. System deletes the `Reaction` record and decrements the counter bucket.  
3c. No notification is sent to the author.

### Exception Flows

#### EF-006-01: Target Post Deleted
1a. The post was deleted between the time the feed loaded and the reaction tap.  
1b. System returns a 404 response. The UI removes the post from the feed and shows a toast: "This post is no longer available."

---

## UC-007: Report & Moderate Content

**Actor:** RegisteredUser (reporter), Moderator, Admin  
**Preconditions:** The content or user being reported is visible to the reporter. The moderator is logged in with a moderator-level role.  
**Postconditions:** A `ContentReport` record is created. The content is queued for AI pre-screening and then human review in the `ModerationQueue`. If actioned, a `BanRecord` or content removal is logged.

### Primary Flow
1. User taps the "…" overflow menu on a post, comment, story, or profile and selects "Report."
2. System presents a categorised reason list: Spam, Nudity, Hate Speech, Violence, Harassment, Misinformation, Intellectual Property, Other.
3. User selects a reason and optionally adds a free-text description (max 500 characters).
4. System creates a `ContentReport` record linked to the target entity and reporter's `user_id`.
5. System submits the content to the AI Moderation Service for priority scoring. High-confidence violations (score ≥ 0.92) are auto-escalated to the front of the `ModerationQueue`.
6. Moderator opens the `ModerationQueue` dashboard, sorted by priority score and report count.
7. Moderator reviews the content in context, views the reporter's description, and the AI confidence breakdown.
8. Moderator selects an action: No Violation Found → Dismiss; Minor Violation → Warn User; Serious Violation → Remove Content; Severe / Repeat Violation → Temporary Ban (1 / 7 / 30 days); Escalate to Admin.
9. System executes the selected action: for removal, CDN purge is triggered; for bans, a `BanRecord` is created and the `User` record is transitioned to `SUSPENDED`.
10. Reporter receives a notification: "We reviewed your report and took action." (or "We reviewed your report and found no violation.") No specifics of the action are shared with the reporter.
11. Reported user receives a notification of the decision and, if applicable, the violation category and appeal link.

### Alternate Flows

#### AF-007-01: Auto-Removal by AI (High Confidence)
5a. AI Moderation returns a confidence score ≥ 0.98 for CSAM or terrorist content categories.  
5b. System immediately removes the content (transitions to `REMOVED_AUTO`) without waiting for human review, triggers law enforcement reporting workflow, and creates a `ModerationQueue` entry for human confirmation.

#### AF-007-02: User Appeals Decision
11a. User receives a ban or content removal notification and taps "Appeal."  
11b. System creates an appeal record and routes it to the Admin queue.  
11c. Admin reviews the appeal within 72 hours and either upholds or overturns the original decision.

### Exception Flows

#### EF-007-01: Duplicate Report
4a. System detects the same `reporter_id` has already submitted a `ContentReport` for the same target within 24 hours.  
4b. System ignores the duplicate submission and shows a confirmation: "You've already reported this content. We'll review it."

---

## UC-008: Create & View Story

**Actor:** RegisteredUser, ContentCreator  
**Preconditions:** The user is authenticated and their account is active.  
**Postconditions:** A `Story` record is created with a `expires_at` timestamp 24 hours from creation. Media is uploaded to CDN. Followers can view the story within the expiry window.

### Primary Flow
1. User taps the "+" story icon on their profile avatar or the story creation shortcut.
2. User selects media type: photo (JPEG/PNG/WebP, max 10 MB), video (max 60 seconds, MP4), or text card with background colour.
3. User optionally adds stickers (polls, questions, emoji sliders, music, countdowns, location tags).
4. User selects audience: Everyone, Friends, Close Friends.
5. User taps "Share to Story." System creates a `Story` record with `expires_at = NOW() + 24h` and uploads media to CDN.
6. Story appears in followers' story tray (sorted by recency and unread status) within 10 seconds.
7. Viewer taps the user's avatar in the story tray. System marks the story as viewed by recording the viewer's `user_id` in the story's view list. View count is incremented.
8. Creator can check story viewers by swiping up on their own story: list of viewers shown with timestamps.
9. At `expires_at`, the System runs the story expiry job: transitions the story to `EXPIRED` state, removes from the CDN, and archives the `Story` record (accessible only to the creator for 7 days in their archive).

### Alternate Flows

#### AF-008-01: Story Poll Interaction
3a. User adds a poll sticker with 2 options (max 25 characters each).  
3b. Viewers tap a poll option when viewing the story.  
3c. Creator sees live vote percentages in the viewer analytics panel.

#### AF-008-02: Highlight a Story
9a. Before expiry, creator taps "Add to Highlight" and selects or creates a Highlight reel on their profile.  
9b. System copies the story media to a permanent Highlight record, exempt from the 24-hour expiry.

#### AF-008-03: Story Reply
7a. Viewer taps the reply box while viewing a story and types a message.  
7b. System creates a `DirectMessage` record in the thread between viewer and creator, linking the message to the source story.

### Exception Flows

#### EF-008-01: Story Upload Failure
5a. CDN upload fails after 3 retries.  
5b. System discards the in-progress `Story` record and notifies the user: "Story failed to upload. Please try again." The draft is retained locally on mobile clients.

#### EF-008-02: Story Reported While Active
While a story is live, a viewer taps "Report."  
System creates a `ContentReport`. If AI Moderation confidence ≥ 0.95, System immediately sets `is_hidden = true` on the story (removing it from all trays) pending human review, without waiting for the 24-hour expiry.
