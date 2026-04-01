# User Stories — Social Networking Platform

## Epic 1: User Registration & Authentication

### US-001: Register with Email
**As a** new visitor  
**I want to** create an account using my email address and a password  
**So that** I can access the social platform and connect with others

**Acceptance Criteria:**
- **Given** I am on the registration page, **When** I enter a valid email, a strong password, and a unique username and submit the form, **Then** my account is created and a verification email is sent to the provided address
- **Given** I enter an email already associated with an existing account, **When** I submit the form, **Then** an error message states "An account with this email already exists" without exposing account details
- **Given** I submit a password shorter than 8 characters or lacking required character types, **When** the form is submitted, **Then** inline validation messages specify exactly which requirements are unmet before the form is processed

---

### US-002: Register via OAuth
**As a** new visitor  
**I want to** sign up using my Google or Apple account  
**So that** I can register quickly without creating a new password

**Acceptance Criteria:**
- **Given** I click "Continue with Google," **When** I complete the Google OAuth consent screen, **Then** an account is created using my Google profile name and email, and I am redirected to a username selection step
- **Given** I sign up with Apple using "Hide My Email," **When** the flow completes, **Then** my account is linked to the Apple-generated relay email and I can receive platform emails at that relay
- **Given** an account already exists with the same email via a different method, **When** I attempt to OAuth register, **Then** I am prompted to link the new login method to the existing account instead of creating a duplicate

---

### US-003: Verify Email Address
**As a** newly registered user  
**I want to** verify my email address  
**So that** I can unlock full account features and secure my account

**Acceptance Criteria:**
- **Given** I registered with an email, **When** I click the verification link in the email, **Then** my account is marked as verified, the banner prompting verification is dismissed, and I gain access to all features
- **Given** the verification link has expired (older than 24 hours), **When** I click it, **Then** I am shown an expiry message and offered a "Resend Verification Email" button
- **Given** I have not verified my email, **When** I attempt to follow accounts beyond 5 or create more than 3 posts, **Then** a prompt blocks the action and asks me to verify my email first

---

### US-004: Log In to Account
**As a** registered user  
**I want to** log in to my account  
**So that** I can access my personalized feed and continue using the platform

**Acceptance Criteria:**
- **Given** I enter my correct email and password, **When** I submit the login form, **Then** I receive a valid session token and am redirected to my home feed
- **Given** I enter an incorrect password fewer than 10 times, **When** I submit, **Then** I receive "Incorrect password" feedback and the attempt is logged
- **Given** I have entered the wrong password 10 consecutive times, **When** the 10th attempt fails, **Then** my account is temporarily locked and an unlock email is sent to my registered address

---

### US-005: Reset Password
**As a** registered user who has forgotten my password  
**I want to** reset my password via email  
**So that** I can regain access to my account

**Acceptance Criteria:**
- **Given** I enter a registered email on the "Forgot Password" page, **When** I submit, **Then** a password reset link is sent (if the email exists) and I see a confirmation message regardless of whether the email was found
- **Given** I click the reset link within 1 hour, **When** I enter and confirm a new password meeting strength requirements, **Then** my password is updated, all existing sessions are invalidated, and I am redirected to the login page
- **Given** I click a reset link older than 1 hour, **When** the page loads, **Then** I see "This link has expired" and am offered the option to request a new reset link

---

### US-006: Enable Two-Factor Authentication
**As a** security-conscious user  
**I want to** enable two-factor authentication on my account  
**So that** my account is protected even if my password is compromised

**Acceptance Criteria:**
- **Given** I navigate to Security Settings and choose "Enable 2FA," **When** I scan the QR code with my authenticator app and enter the first valid TOTP code, **Then** 2FA is enabled and I am shown 8 recovery codes to store safely
- **Given** 2FA is enabled on my account, **When** I log in with correct credentials, **Then** I am prompted for a 6-digit TOTP code before access is granted
- **Given** I enter an incorrect TOTP code 5 consecutive times, **When** the 5th attempt fails, **Then** my session attempt is blocked for 15 minutes with a clear message

---

## Epic 2: Profile Management

### US-007: Set Up Profile
**As a** new user  
**I want to** set up my profile with a photo, bio, and personal details  
**So that** others can learn about me and I can make a good first impression

**Acceptance Criteria:**
- **Given** I upload a profile photo, **When** the upload completes, **Then** the image is cropped to a square, resized to 400×400 px, and displayed on my profile within 5 seconds
- **Given** I enter a bio longer than 160 characters, **When** I attempt to save, **Then** the field shows a character count warning at 140 and blocks saving above 160 with an inline error
- **Given** I set a website URL that lacks a valid scheme, **When** I save, **Then** the system auto-prepends "https://" or rejects clearly non-URL input with a validation message

---

### US-008: Change Username
**As a** registered user  
**I want to** change my username  
**So that** my handle better reflects my current identity or brand

**Acceptance Criteria:**
- **Given** I enter a new username that is not taken and conforms to the format (3–30 alphanumeric characters, underscores, hyphens), **When** I confirm the change, **Then** my username is updated immediately and all @mentions of the old username in the UI redirect to my new handle
- **Given** I attempt to change my username a third time within 30 days, **When** I submit the change, **Then** I receive a message: "Username can only be changed twice every 30 days. Your next change is available on [date]"
- **Given** I change my username, **When** another user tries to use the old username within 14 days, **Then** the old username is reserved and unavailable; after 14 days it becomes publicly available

---

### US-009: Control Profile Visibility
**As a** user concerned about privacy  
**I want to** make my profile private  
**So that** only approved followers can see my posts and activity

**Acceptance Criteria:**
- **Given** I set my profile to Private, **When** a non-follower visits my profile, **Then** they see only my avatar, display name, and follower/following counts; posts and stories are hidden with a "Follow to see posts" message
- **Given** my profile is Private and a user follows me, **When** I receive the follow request, **Then** I can accept or decline; until accepted, the requester cannot see my content
- **Given** I switch my profile from Private to Public, **When** the change is saved, **Then** all pending follow requests are automatically accepted and existing followers retain access

---

## Epic 3: Social Graph

### US-010: Follow a Public Account
**As a** user  
**I want to** follow a public account  
**So that** their posts appear in my feed

**Acceptance Criteria:**
- **Given** I visit a public profile and click "Follow," **When** the request processes, **Then** the button changes to "Following," the account's follower count increments by 1, and their posts begin appearing in my Following feed
- **Given** I follow an account, **When** I visit their profile, **Then** I see posts, stories, and any other content visible to followers
- **Given** I click "Unfollow," **When** confirmed, **Then** the account is removed from my following list and their posts no longer appear in my Following feed within the next refresh

---

### US-011: Send a Friend Request
**As a** user  
**I want to** send a friend request to another user  
**So that** we can have a mutual connection with enhanced privacy sharing

**Acceptance Criteria:**
- **Given** I send a friend request to User B, **When** User B accepts, **Then** we are mutual friends, both appear in each other's friends list, and we each receive a confirmation notification
- **Given** User B declines my request, **When** the decline action is taken, **Then** my request is removed, I am not notified of the decline, and I can send another request after 30 days
- **Given** I cancel a sent friend request before it is accepted, **When** I confirm cancellation, **Then** the request is withdrawn and User B's pending requests list no longer shows my request

---

### US-012: Block a User
**As a** user experiencing harassment  
**I want to** block another user  
**So that** they cannot interact with me or view my content

**Acceptance Criteria:**
- **Given** I block User B, **When** the block is applied, **Then** User B's follow/friend connection to me is removed, they cannot view my profile or posts, and any messages from them are hidden from my inbox
- **Given** I have blocked User B, **When** User B searches for my profile, **Then** my account does not appear in their search results
- **Given** I unblock User B, **When** the unblock is confirmed, **Then** User B can view my public profile again, but any previous follow relationship is not automatically restored

---

### US-013: Mute an Account
**As a** user  
**I want to** mute someone's posts without unfollowing them  
**So that** I maintain the connection while reducing noise in my feed

**Acceptance Criteria:**
- **Given** I mute User B's posts, **When** my feed refreshes, **Then** posts from User B no longer appear in either the Following or For You feed, and User B is not notified of the mute
- **Given** I mute User B's stories, **When** I open the stories tray, **Then** User B's story bubble is removed from the tray without appearing at the end of the list
- **Given** I navigate to my muted accounts list and unmute User B, **When** the unmute is confirmed, **Then** their content resumes appearing in my feed from the next refresh

---

## Epic 4: Post Creation & Management

### US-014: Create a Text Post
**As a** user  
**I want to** create a text post  
**So that** I can share thoughts with my followers

**Acceptance Criteria:**
- **Given** I type a post up to 2,000 characters, **When** I tap "Post," **Then** the post is published, appears at the top of my profile feed, and is distributed to my followers' feeds within 30 seconds
- **Given** I type a post containing a URL, **When** I pause typing or submit, **Then** a link preview card is auto-generated showing the page title, description, and thumbnail image
- **Given** I type a post exceeding 2,000 characters, **When** I reach the limit, **Then** the character counter turns red and the Post button is disabled until the content is within the limit

---

### US-015: Create a Photo Post
**As a** user  
**I want to** share photos in a post  
**So that** I can visually express moments with my followers

**Acceptance Criteria:**
- **Given** I select up to 10 images from my device, **When** I publish the post, **Then** all images are uploaded, optimized (WebP conversion), and displayed as a gallery with swipe navigation
- **Given** I upload an image larger than 10 MB, **When** the file is selected, **Then** the system automatically compresses it to under 2 MB while maintaining visible quality, or shows an error if compression is not feasible
- **Given** I post photos with faces in them, **When** the post is published, **Then** the system prompts me (but does not require me) to tag the people shown, using face-recognition suggestions

---

### US-016: Create a Poll
**As a** user  
**I want to** post a poll with multiple choice options  
**So that** I can gather opinions from my followers

**Acceptance Criteria:**
- **Given** I create a poll with a question, 2–4 non-empty options, and a voting window, **When** I publish it, **Then** the poll post is live and followers can vote immediately
- **Given** a follower selects an option on my poll, **When** their vote is registered, **Then** they see the current percentage breakdown and their selected option is highlighted; they cannot change their vote
- **Given** the poll voting window expires, **When** the deadline passes, **Then** no new votes are accepted, the final results are displayed on the post, and I receive a notification with the outcome

---

### US-017: Schedule a Post
**As a** content creator  
**I want to** schedule posts in advance  
**So that** I can maintain a consistent publishing cadence without being online 24/7

**Acceptance Criteria:**
- **Given** I compose a post and select "Schedule," **When** I choose a future date and time (up to 6 months out) and confirm, **Then** the post is saved as Scheduled and visible in my Scheduled Posts queue
- **Given** a scheduled post's time arrives, **When** the system processes the queue, **Then** the post is published within 2 minutes of the scheduled time
- **Given** I edit a scheduled post before its publish time, **When** I save changes, **Then** the updated content is what gets published; I can also cancel the scheduled post and it is moved to Drafts

---

### US-018: Quote Post
**As a** user  
**I want to** quote another user's post with my own commentary  
**So that** I can contribute to a conversation while giving credit to the original

**Acceptance Criteria:**
- **Given** I tap "Quote Post" on a public post, **When** I add my commentary (up to 2,000 characters) and publish, **Then** my post contains an embedded card of the original post with the original author's handle and content
- **Given** the original post is deleted after I quote it, **When** someone views my quote post, **Then** the embedded card shows "This post is no longer available" instead of the original content
- **Given** the original author has blocked me, **When** I attempt to quote their post, **Then** the option to quote is unavailable, and if a pre-written quote exists from before the block, it is removed from my drafts

---

## Epic 5: Feed & Content Discovery

### US-019: View Personalized Feed
**As a** returning user  
**I want to** see a personalized "For You" feed  
**So that** I discover interesting content beyond just the accounts I follow

**Acceptance Criteria:**
- **Given** I open the app after being away for 8+ hours, **When** the feed loads, **Then** I see fresh content with a mix of posts from followed accounts, trending content, and suggested creators, ranked by relevance
- **Given** I tap "Not Interested" on a post, **When** the feedback is recorded, **Then** the post is immediately removed from my feed and content from that account is deprioritized in future feed sessions
- **Given** I switch to the "Following" tab, **When** the tab content loads, **Then** I see only posts from accounts I follow, ordered chronologically with the most recent at the top

---

### US-020: Discover via Explore
**As a** user looking to find new content  
**I want to** browse an Explore/Discover section  
**So that** I can find trending posts, hashtags, and communities relevant to my interests

**Acceptance Criteria:**
- **Given** I open the Explore page, **When** it loads, **Then** I see a curated grid of trending media posts, a list of trending hashtags (top 10), and suggested communities, all personalized to my declared interests and behavior
- **Given** I tap a trending hashtag on the Explore page, **When** the hashtag page opens, **Then** I see total post count, the number of followers the hashtag has, and a feed combining "Top" and "Recent" posts using that tag
- **Given** I have no account interests set and am a new user, **When** I open Explore, **Then** I see globally trending content and a prompt to follow topics to personalize the page

---

### US-021: Search for Users and Content
**As a** user  
**I want to** search for people, posts, and hashtags  
**So that** I can quickly find specific content or accounts

**Acceptance Criteria:**
- **Given** I type a search query of 2 or more characters, **When** I pause for 300 ms, **Then** type-ahead suggestions appear showing matched usernames, hashtags, and community names in a dropdown
- **Given** I submit a search, **When** results load, **Then** I see results grouped into tabs: People, Posts, Hashtags, and Communities, defaulting to the most relevant tab based on query format
- **Given** I search for a query that returns no results, **When** the results page renders, **Then** I see "No results for '[query]'" along with suggestions to check spelling or try related terms

---

## Epic 6: Stories

### US-022: Create and Post a Story
**As a** user  
**I want to** post a Story that disappears after 24 hours  
**So that** I can share ephemeral moments without cluttering my permanent profile

**Acceptance Criteria:**
- **Given** I capture or select a photo or short video (up to 30 s) and add optional text/stickers, **When** I tap "Share to Story," **Then** my Story is live within 5 seconds and visible to the configured audience
- **Given** 24 hours have passed since I posted a Story segment, **When** my followers open the stories tray, **Then** my story bubble no longer appears; the content is still accessible to me in Story Archive
- **Given** I add a poll sticker to my Story, **When** viewers tap the poll options, **Then** their vote is recorded in real-time and I can see the vote breakdown and individual responses in the story viewer

---

### US-023: View Stories
**As a** user  
**I want to** view Stories from accounts I follow  
**So that** I can see their ephemeral updates

**Acceptance Criteria:**
- **Given** I tap a story bubble in the tray, **When** the story opens, **Then** each segment plays sequentially (photos for 5 seconds, videos for their full duration) and I can tap right to advance or left to go back
- **Given** I am viewing someone's story, **When** I swipe up or tap "Reply," **Then** a direct message compose box opens pre-addressed to the story author
- **Given** I view a story from an account, **When** I close it, **Then** that story bubble appears as "viewed" (greyed out ring) in the tray for the duration of that story's life

---

### US-024: Save Story to Highlights
**As a** user  
**I want to** save my Stories to a permanent Highlight on my profile  
**So that** visitors can view key moments even after the 24-hour window

**Acceptance Criteria:**
- **Given** I open a past story in my Story Archive and tap "Add to Highlight," **When** I select an existing Highlight or create a new one with a name and cover image, **Then** the story segment appears in that Highlight on my profile
- **Given** I have a Highlight on my profile, **When** a visitor taps it, **Then** the segments play in the same sequential story format as live stories
- **Given** I delete a Highlight, **When** confirmed, **Then** the Highlight is removed from my profile; the underlying story segments remain in my archive

---

## Epic 7: Reactions & Comments

### US-025: React to a Post
**As a** user  
**I want to** react to posts with an emoji  
**So that** I can express my feelings beyond a simple like

**Acceptance Criteria:**
- **Given** I tap the reaction button on a post, **When** the reaction picker appears, **Then** I see 6 options: Like, Love, Haha, Wow, Sad, Angry, and can tap any one to apply it
- **Given** I have already reacted to a post with "Like," **When** I open the reaction picker and select "Love," **Then** my reaction changes from Like to Love, the Like count decrements, and the Love count increments
- **Given** I tap my existing reaction, **When** confirmed, **Then** the reaction is removed and the count decrements

---

### US-026: Comment on a Post
**As a** user  
**I want to** leave a comment on a post  
**So that** I can engage in conversation with the author and other users

**Acceptance Criteria:**
- **Given** I type a comment (up to 500 characters) and submit, **When** the comment posts, **Then** it appears in the thread immediately below the post with my avatar, name, and timestamp
- **Given** I reply to an existing comment, **When** my reply posts, **Then** it is nested below the parent comment and the parent commenter receives a mention notification
- **Given** the post author has disabled comments, **When** I open the post, **Then** the comment input is hidden and replaced with "Comments are disabled for this post"

---

### US-027: Pin a Comment
**As a** post author  
**I want to** pin a comment to the top of my post's comment thread  
**So that** I can highlight the most relevant or appreciated response

**Acceptance Criteria:**
- **Given** I tap the overflow menu on a comment on my own post and select "Pin," **When** confirmed, **Then** the comment is moved to the top of the thread with a "Pinned" badge
- **Given** I already have 3 pinned comments on a post, **When** I try to pin a 4th, **Then** I am prompted to unpin one of the existing pinned comments before the new one can be pinned
- **Given** a commenter deletes their comment that I had pinned, **When** the deletion is processed, **Then** the pinned spot is vacated and the next chronological comment takes its place (unpinned)

---

## Epic 8: Messaging

### US-028: Send a Direct Message
**As a** user  
**I want to** send a private message to another user  
**So that** we can communicate one-on-one outside of the public feed

**Acceptance Criteria:**
- **Given** User B and I mutually follow each other, **When** I compose and send a message, **Then** it is delivered to User B's inbox in real-time (under 100 ms) and displayed in our conversation thread
- **Given** I send a message to a user I do not mutually follow, **When** the message is sent, **Then** it arrives in their "Message Requests" folder and they are notified; the message is not visible in their main inbox until they accept
- **Given** I send a message and then delete it within 5 minutes, **When** I tap "Delete for Everyone," **Then** the message is replaced with "This message was deleted" in both our views and no content is recoverable

---

### US-029: Create a Group Chat
**As a** user  
**I want to** create a group chat with multiple friends  
**So that** we can communicate together in a shared thread

**Acceptance Criteria:**
- **Given** I create a group with up to 250 members, a group name, and a group photo, **When** I confirm creation, **Then** all added members receive a notification and the group thread opens for everyone simultaneously
- **Given** I am a group admin, **When** I add a new member, **Then** the member sees the last 30 days of message history (configurable by admin) and is listed in the members panel
- **Given** I leave a group chat, **When** confirmed, **Then** I am removed from the member list, I no longer receive notifications from the group, and remaining members see "[My name] left the group"

---

### US-030: Send Voice Message
**As a** user in a conversation  
**I want to** send a voice message  
**So that** I can communicate quickly without typing

**Acceptance Criteria:**
- **Given** I hold the voice message button and speak, **When** I release the button, **Then** the audio (up to 5 minutes) is uploaded and sent as a waveform-display message in the conversation
- **Given** the recipient receives a voice message, **When** they tap the play button, **Then** it plays through their device speaker with a visual waveform and elapsed time indicator
- **Given** I want to cancel a voice recording in progress, **When** I slide left (cancel gesture) while holding the button, **Then** the recording is discarded without sending and the UI returns to the compose state

---

## Epic 9: Notifications

### US-031: Manage Notification Preferences
**As a** user  
**I want to** control which notifications I receive and how  
**So that** I only get interruptions that matter to me

**Acceptance Criteria:**
- **Given** I open Notification Settings, **When** I toggle off push notifications for "New Followers," **Then** I stop receiving push alerts for follows while still seeing them in the in-app notification center
- **Given** I enable "Do Not Disturb" from 11 PM to 8 AM, **When** a post reaction arrives at midnight, **Then** no push notification is sent; the notification queues and delivers at 8 AM
- **Given** I disable email notifications entirely, **When** any platform event occurs, **Then** no emails are sent to my address except critical account security alerts (password changes, new device logins)

---

### US-032: View Notification Center
**As a** user  
**I want to** view all my recent notifications in one place  
**So that** I can catch up on activity related to my account

**Acceptance Criteria:**
- **Given** I open the notification center, **When** it loads, **Then** unread notifications are shown with a highlighted background, grouped by Today, This Week, and Earlier
- **Given** I tap a notification for a comment on my post, **When** the navigation completes, **Then** the post opens scrolled to the specific comment that triggered the notification, and the notification is marked as read
- **Given** I tap "Mark all as read," **When** confirmed, **Then** all notifications in the center lose their unread styling and the notification badge on the app icon clears

---

## Epic 10: Communities

### US-033: Create a Community
**As a** user with a specific interest  
**I want to** create a community around that interest  
**So that** people can find each other and share related content in a dedicated space

**Acceptance Criteria:**
- **Given** I fill in a community name (3–100 characters), description, category, cover image, and choose Public visibility, **When** I create the community, **Then** it is immediately discoverable in search and on the Explore page
- **Given** I set the community to Private, **When** it is created, **Then** it does not appear in public search results; only users with a direct link or invitation can request to join
- **Given** I am the community creator, **When** I visit my community admin panel, **Then** I see controls for member management, post approval settings, community rules, and analytics

---

### US-034: Join and Participate in a Community
**As a** user  
**I want to** join a community and post in it  
**So that** I can engage with others who share my interests

**Acceptance Criteria:**
- **Given** I join a public community, **When** my membership is confirmed, **Then** community posts begin appearing in my Following feed and I gain access to the community feed and posting features
- **Given** I post in a community that requires admin approval, **When** I submit the post, **Then** it enters a "Pending Review" state visible only to me and admins; I receive a notification when it is approved or rejected
- **Given** a community admin removes me, **When** the action is taken, **Then** I am immediately removed from the member list, my community posts are hidden, and I receive a notification explaining the removal

---

## Epic 11: Content Moderation

### US-035: Report Content
**As a** user who encounters harmful content  
**I want to** report it to the platform  
**So that** it can be reviewed and removed if it violates community standards

**Acceptance Criteria:**
- **Given** I tap "Report" on a post, **When** the report flow opens, **Then** I am presented with clearly worded violation categories (spam, harassment, hate speech, nudity, violence, misinformation, IP infringement) and an optional text field for additional context
- **Given** I submit a report, **When** the flow completes, **Then** I see a confirmation that my report was received with a reference number and an indication of typical resolution time
- **Given** I report a message in a non-E2EE context, **When** the report is submitted, **Then** a snapshot of the message and surrounding context is attached to the moderation queue item for reviewer reference

---

### US-036: Appeal a Moderation Decision
**As a** user whose content was removed  
**I want to** appeal the moderation decision  
**So that** I can have the decision reviewed if I believe it was made in error

**Acceptance Criteria:**
- **Given** I receive a content removal notification, **When** I tap "Appeal This Decision," **Then** I am shown the specific policy cited and a text field to explain why I believe my content does not violate it, with a 30-day submission window
- **Given** I submit an appeal, **When** it is received, **Then** I get an acknowledgement notification with an estimated review time (72 hours SLA)
- **Given** the appeal reviewer overturns the decision, **When** the appeal is resolved, **Then** my content is restored, my account penalty (if any) is reversed, and I receive a notification confirming the overturn

---

## Epic 12: Advertising

### US-037: Create an Ad Campaign
**As an** advertiser  
**I want to** create a targeted ad campaign  
**So that** I can reach the right audience for my product or service

**Acceptance Criteria:**
- **Given** I complete advertiser verification and payment method setup, **When** I create a campaign with objective "Traffic," a daily budget of $20, and a target audience by age, location, and interest, **Then** the campaign enters a review queue; upon approval (within 24 hours) ads begin serving
- **Given** my campaign's daily budget is depleted, **When** the budget cap is hit, **Then** ad serving pauses automatically until the next calendar day (UTC midnight reset) and I receive a budget depletion notification
- **Given** I upload an ad creative that violates advertising policies (e.g., misleading claims), **When** the creative is reviewed, **Then** it is rejected with a specific policy violation reason and guidance on how to resubmit a compliant version

---

### US-038: View Ad Performance
**As an** active advertiser  
**I want to** view real-time campaign performance metrics  
**So that** I can optimize my spend and creative strategy

**Acceptance Criteria:**
- **Given** my campaign has been running for 24 hours, **When** I open the campaign dashboard, **Then** I see impressions, clicks, CTR, total spend, average CPM, and CPC, updated with at most a 2-hour data lag
- **Given** I view individual creative performance, **When** I select an ad creative, **Then** I see a breakdown by placement (feed, stories, explore), device type, and age/gender demographic cohort
- **Given** I export campaign data, **When** I click "Export CSV," **Then** a download is prepared with day-by-day metrics for the selected date range and I receive an email link within 5 minutes

---

## Epic 13: Analytics & Insights

### US-039: View Personal Post Analytics
**As a** creator  
**I want to** see how my posts are performing  
**So that** I can understand what resonates with my audience and improve my content

**Acceptance Criteria:**
- **Given** I open a post and tap "View Insights," **When** the analytics panel loads, **Then** I see: reach (unique accounts), impressions (total views), engagement rate, reactions breakdown by type, comment count, shares, saves, and profile visits attributed to that post
- **Given** I view my overall profile analytics for the last 28 days, **When** the dashboard renders, **Then** I see follower growth with a net change figure, total post reach, profile visits, and a ranked list of my top 5 posts by engagement
- **Given** my follower count crosses 1,000, **When** I open audience insights, **Then** I see demographic charts: age distribution (bins: 13–17, 18–24, 25–34, 35–44, 45+), gender split, and top 5 countries and cities

---

### US-040: Export Personal Data
**As a** user exercising my data rights  
**I want to** download all my personal data from the platform  
**So that** I have a complete copy of my information and can hold the platform accountable

**Acceptance Criteria:**
- **Given** I request a data export from Privacy Settings, **When** the request is submitted, **Then** I receive a confirmation that the export will be ready within 30 days and a notification when it is ready for download
- **Given** my export is ready, **When** I download it, **Then** I receive a structured ZIP archive containing: profile data, all posts and media, comments, direct message history (non-E2EE), notification log, activity log, and ad preference data in human-readable JSON or CSV format
- **Given** I make a second export request within 30 days of the previous one, **When** I submit it, **Then** I am informed that a recent export already exists and prompted to download it, with the option to request a fresh export after the 30-day window

---

## Epic 14: Privacy & GDPR

### US-041: Manage Privacy Settings
**As a** user  
**I want to** have granular control over my privacy settings  
**So that** I can decide exactly what information is visible and to whom

**Acceptance Criteria:**
- **Given** I navigate to Privacy Settings, **When** the page loads, **Then** I see clearly organized sections: Profile Visibility, Post Audience Defaults, Activity Visibility (liked posts, followed hashtags, communities joined), Data & Advertising, and Contact Discovery
- **Given** I disable "Allow email contact lookup," **When** another user imports their phone contacts, **Then** my account is not surfaced as a suggestion even if my email matches a contact in their list
- **Given** I turn off personalized advertising, **When** the setting is saved, **Then** I still see ads but they are contextually targeted only (no interest/behavior-based targeting), and the change is reflected in my ad preference log within 24 hours

---

### US-042: Withdraw Consent
**As a** user  
**I want to** withdraw my consent to specific data processing activities  
**So that** the platform stops using my data for purposes I no longer agree to

**Acceptance Criteria:**
- **Given** I open the Privacy Center and withdraw consent for "Third-Party Data Sharing," **When** the change is saved, **Then** my data is no longer shared with third-party ad partners from that point forward, and I see a confirmation with the timestamp of the consent withdrawal
- **Given** I withdraw consent for "Analytics and Performance Measurement," **When** saved, **Then** my interactions are excluded from platform analytics datasets and the change cannot retroactively alter already-processed analytics
- **Given** I withdraw all optional consents, **When** all changes are confirmed, **Then** my account remains functional for core social features; only features that depend on declined data processing are disabled with a clear explanation of why

---

### US-043: Request Account Deletion
**As a** user who wants to leave the platform  
**I want to** permanently delete my account  
**So that** all my personal data is removed from the platform

**Acceptance Criteria:**
- **Given** I submit a permanent deletion request, **When** confirmed with my password, **Then** my account enters a 14-day grace period during which I can log back in to cancel the deletion; no new content can be posted during this period
- **Given** the 14-day grace period passes without cancellation, **When** the deletion job runs, **Then** my profile becomes inaccessible, my PII is purged from primary databases within 30 days, and a deletion confirmation email is sent
- **Given** my account is deleted, **When** someone tries to visit my old profile URL or @mention my old username, **Then** they see "This account no longer exists" and my username is made available to new registrations after 90 days
