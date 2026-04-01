# User Stories — Customer Support and Contact Center Platform

> All user stories follow the format: **As a [role], I want [capability], so that [benefit].**  
> Each story includes priority, epic, estimated story points (Fibonacci), and 3–5 acceptance criteria.

---

## Table of Contents

- [Epic 1: Ticket Management](#epic-1-ticket-management)
- [Epic 2: Omni-Channel Communication](#epic-2-omni-channel-communication)
- [Epic 3: Routing & Assignment](#epic-3-routing--assignment)
- [Epic 4: SLA & Escalation](#epic-4-sla--escalation)
- [Epic 5: Agent Productivity](#epic-5-agent-productivity)
- [Epic 6: Knowledge Base](#epic-6-knowledge-base)
- [Epic 7: Bot & Automation](#epic-7-bot--automation)
- [Epic 8: Customer 360°](#epic-8-customer-360)
- [Epic 9: Supervisor & Workforce](#epic-9-supervisor--workforce)
- [Epic 10: Reporting & Analytics](#epic-10-reporting--analytics)
- [Epic 11: Administration & Compliance](#epic-11-administration--compliance)

---

## Epic 1: Ticket Management

**US-001: Create Ticket from Email**
**Priority:** High | **Epic:** Ticket Management | **Points:** 5
> As a **support agent**, I want inbound emails to automatically create tickets in the system, so that I never miss a customer request and all contacts are tracked in one place.

**Acceptance Criteria:**
1. An email sent to the configured support mailbox creates a new ticket within 10 seconds of receipt.
2. The ticket captures the sender's email address, subject line, body, and any attachments.
3. If the sender's email matches an existing customer record, the ticket is linked to that customer automatically.
4. A duplicate email with the same `Message-ID` does not create a second ticket; it is idempotently ignored.
5. The agent receives an in-app notification for the new ticket if it falls within their assigned queue.

---

**US-002: Manually Create Ticket on Behalf of Customer**
**Priority:** High | **Epic:** Ticket Management | **Points:** 3
> As a **support agent**, I want to manually create a ticket on behalf of a customer who contacts me by phone or in person, so that the interaction is tracked and subject to the same SLA and routing rules as any other channel.

**Acceptance Criteria:**
1. The agent can create a ticket from the "New Ticket" button, selecting or searching for the customer by name, email, or phone.
2. The agent can set the channel to `Phone` or `Walk-In` for tracking purposes.
3. All mandatory fields (subject, queue, priority) must be completed before the ticket can be saved.
4. The ticket appears in the assigned queue immediately upon creation.
5. The SLA clock starts at the time the ticket is saved, not when the customer first called.

---

**US-003: Merge Duplicate Tickets**
**Priority:** Medium | **Epic:** Ticket Management | **Points:** 5
> As a **support agent**, I want to merge duplicate tickets from the same customer about the same issue, so that I handle the problem once and avoid sending the customer conflicting replies.

**Acceptance Criteria:**
1. The agent can select a "Merge" action on any open ticket and search for a second ticket to merge with.
2. The system warns the agent if the two tickets belong to different customers.
3. Upon confirmation, all conversation threads from the secondary ticket are appended to the primary ticket's timeline in chronological order.
4. The secondary ticket status changes to `Merged` and is no longer actionable; a link to the primary ticket is displayed.
5. Attachments from the secondary ticket are accessible from the primary ticket's attachment panel.

---

**US-004: Split a Multi-Issue Ticket**
**Priority:** Medium | **Epic:** Ticket Management | **Points:** 5
> As a **support agent**, I want to split a ticket that covers multiple unrelated issues into separate tickets, so that each issue can be routed, prioritized, and resolved independently.

**Acceptance Criteria:**
1. The agent can invoke a "Split Ticket" action and specify a new subject and selected messages to move to the child ticket.
2. The original ticket retains messages not moved to the child; both tickets preserve the full customer reference.
3. The child ticket is assigned a new unique ticket ID and appears as a new open ticket in the appropriate queue.
4. A link between parent and child tickets is visible on both ticket detail pages.
5. Both tickets start with independent SLA clocks from the split timestamp.

---

**US-005: Bulk Close Resolved Tickets**
**Priority:** Medium | **Epic:** Ticket Management | **Points:** 3
> As a **team lead**, I want to bulk-close tickets that have been in `Pending Customer` status for more than 7 days with no customer response, so that my queue stays clean and accurate.

**Acceptance Criteria:**
1. The team lead can filter tickets by status `Pending Customer` and last-updated date using the queue filter panel.
2. Multi-select is available on the filtered results, allowing selection of all matching tickets.
3. A "Bulk Close" action requires a confirmation dialog showing the count of tickets to be closed.
4. Each closed ticket receives an automatic system note: "Closed after 7 days with no customer response."
5. The customer receives an automated closure notification email for each closed ticket.

---

**US-006: Add Internal Notes to Tickets**
**Priority:** High | **Epic:** Ticket Management | **Points:** 2
> As a **support agent**, I want to add internal notes to a ticket that are visible only to agents and supervisors, so that I can share context and investigation findings with my team without exposing internal details to the customer.

**Acceptance Criteria:**
1. The reply composer has a toggle to switch between `Reply to Customer` and `Internal Note` modes.
2. Internal notes are displayed with a visually distinct background color (e.g., yellow) in the ticket thread.
3. Internal notes are never included in email reply threads sent to the customer.
4. Internal notes are searchable within the ticket and across the agent workspace search.
5. All internal notes are included in the ticket's audit history with the authoring agent's name and timestamp.

---

## Epic 2: Omni-Channel Communication

**US-007: Handle Live Chat in Unified Inbox**
**Priority:** High | **Epic:** Omni-Channel Communication | **Points:** 8
> As a **support agent**, I want incoming live chat sessions from the website widget to appear in my unified inbox alongside email tickets, so that I can manage all customer interactions from a single interface without switching tools.

**Acceptance Criteria:**
1. A new live chat session creates a ticket in the agent's queue within 2 seconds of the customer sending their first message.
2. The chat interface within the ticket allows the agent to type and send real-time messages with typing indicators visible to both parties.
3. The chat widget displays an estimated wait time to the customer while the session is queued.
4. If the agent does not respond within the configured timeout, the system sends a configurable hold message to the customer automatically.
5. The full chat transcript is preserved on the ticket timeline after the session ends, searchable by keyword.

---

**US-008: Respond to Customer via SMS**
**Priority:** High | **Epic:** Omni-Channel Communication | **Points:** 5
> As a **support agent**, I want to send and receive SMS messages within a ticket, so that I can serve customers who prefer SMS without needing a separate mobile tool.

**Acceptance Criteria:**
1. Inbound SMS messages to the configured support number create a new ticket or append to an existing open ticket correlated by the sender's phone number.
2. The agent can type a reply in the ticket interface and send it as an SMS; the message appears in the customer's SMS thread.
3. SMS character count and segment count are displayed in the reply composer to help agents stay within limits.
4. Media messages (MMS) received from the customer are stored as attachments on the ticket.
5. The agent sees a channel badge indicating `SMS` on the ticket so they know the medium before replying.

---

**US-009: Manage WhatsApp Conversations**
**Priority:** Medium | **Epic:** Omni-Channel Communication | **Points:** 5
> As a **support agent**, I want WhatsApp messages from customers to appear as tickets in my inbox, so that I can serve customers on their preferred channel with the same toolset I use for other channels.

**Acceptance Criteria:**
1. Inbound WhatsApp messages route to the configured WhatsApp queue and appear as chat-type tickets in the agent workspace.
2. Agents can send text replies, template messages (per WhatsApp Business API requirements), and media files via the ticket interface.
3. WhatsApp's 24-hour customer service window rule is enforced: a warning appears if the agent attempts to send a non-template message after 24 hours of customer inactivity.
4. Read receipts from WhatsApp are reflected in the ticket thread (sent / delivered / read status icons).
5. The ticket retains the WhatsApp message thread ID for correlation on subsequent customer replies.

---

**US-010: Monitor Social Media Mentions**
**Priority:** Medium | **Epic:** Omni-Channel Communication | **Points:** 8
> As a **support agent**, I want Twitter/X mentions and Facebook Page messages to automatically create tickets, so that I can respond to customers on social media through the same platform without monitoring multiple social media dashboards.

**Acceptance Criteria:**
1. Twitter/X mentions of the configured handle and Facebook Page direct messages are ingested within 5 minutes of posting.
2. Each social message creates a ticket with the social network's post/message ID stored as metadata.
3. The agent can compose and post a reply directly from the ticket; the reply appears as a response to the original post or message on the social platform.
4. Duplicate ingestion of the same post ID is idempotently prevented.
5. A social media channel badge is visible on the ticket for context.

---

**US-011: Receive and Respond on Voice Channel**
**Priority:** High | **Epic:** Omni-Channel Communication | **Points:** 8
> As a **support agent**, I want inbound calls to be connected to me through the platform and automatically associated with a ticket, so that I have full context during the call and a complete record of the interaction after it ends.

**Acceptance Criteria:**
1. Inbound calls ring in the agent's browser-based softphone; accepting creates a new ticket pre-filled with the caller's phone number and a `Voice` channel tag.
2. If the caller's phone number matches an existing customer, their 360° profile panel opens automatically alongside the call.
3. The call duration, hold times, and disposition (resolved / transferred / callback requested) are written to the ticket upon call end.
4. The call recording is attached to the ticket timeline within 2 minutes of call completion.
5. The agent can add notes and update ticket fields during the call using the ticket editor running alongside the softphone.

---

## Epic 3: Routing & Assignment

**US-012: Auto-Assign via Skill-Based Routing**
**Priority:** High | **Epic:** Routing & Assignment | **Points:** 8
> As a **support agent**, I want tickets to be automatically assigned to me only when they match my configured skills, so that I am handling requests I am qualified to resolve rather than wasting time reassigning tickets I cannot help with.

**Acceptance Criteria:**
1. A ticket created with `required_skills: [language:Spanish, tier:2]` is only assigned to an agent whose skill profile includes both skills.
2. If I am Online and available and have matching skills, the ticket is assigned to me within 500 ms of the ticket creation event.
3. If no eligible agent is available, the ticket waits in the queue and is assigned within 30 seconds of an eligible agent coming Online.
4. The routing engine logs the assignment rationale (agent selected, skills matched, agents considered and rejected) for each assignment.
5. I can view my current skill assignments in my profile and request changes through the system.

---

**US-013: Configure Round-Robin Queue**
**Priority:** Medium | **Epic:** Routing & Assignment | **Points:** 5
> As a **supervisor**, I want to configure a queue to use round-robin assignment, so that ticket volume is distributed evenly across my team during high-traffic periods and no single agent becomes overwhelmed.

**Acceptance Criteria:**
1. I can navigate to Queue Settings and change the routing mode to `Round-Robin` without downtime.
2. After the change, the next 10 tickets assigned in that queue go to a different agent each time, cycling through all Online available agents.
3. An agent at their concurrency limit is skipped in the rotation and the next eligible agent receives the ticket.
4. The rotation pointer persists across a routing service restart; the cycle does not reset to the first agent.
5. The supervisor dashboard shows which agent is "next in rotation" for the queue.

---

**US-014: Set Up Overflow Routing**
**Priority:** Medium | **Epic:** Routing & Assignment | **Points:** 5
> As a **supervisor**, I want to configure overflow routing so that when a queue's wait time exceeds a threshold, tickets automatically spill to a secondary queue, so that customers are not left waiting indefinitely during volume spikes.

**Acceptance Criteria:**
1. I can set an overflow threshold on a queue: either max queue depth (e.g., 50 tickets) or max wait time (e.g., 10 minutes).
2. When the threshold is breached, new incoming tickets route to the designated overflow queue automatically.
3. An overflow event is logged with the timestamp, queue name, queue depth at overflow, and overflow target.
4. The supervisor dashboard displays a visual indicator when a queue is in overflow state.
5. When the queue depth falls below a configurable recovery threshold, overflow mode deactivates and routing returns to the primary queue.

---

**US-015: Create Auto-Assignment Rules**
**Priority:** Medium | **Epic:** Routing & Assignment | **Points:** 5
> As a **system administrator**, I want to define automatic routing rules that set ticket attributes based on content, so that tickets are pre-tagged and routed to the correct queue without requiring manual triage.

**Acceptance Criteria:**
1. I can create a rule with conditions (e.g., `channel = Email AND subject contains "invoice"`) and actions (set tag `billing`, set priority `High`, assign to queue `Billing`).
2. Rules can use AND/OR logic with up to 5 conditions and up to 5 actions.
3. Rules are evaluated in descending priority order; the first matching rule's actions are applied.
4. I can test a rule against a sample ticket payload from the rule editor without creating a real ticket.
5. Rule evaluation results (which rule matched, actions applied) are visible in each ticket's audit timeline.

---

## Epic 4: SLA & Escalation

**US-016: Track SLA Countdown in Real Time**
**Priority:** High | **Epic:** SLA & Escalation | **Points:** 5
> As a **support agent**, I want to see a real-time SLA countdown on each ticket in my queue, so that I can prioritize my work by urgency and respond before any SLA is breached.

**Acceptance Criteria:**
1. Every ticket in my queue shows the remaining SLA time as a countdown timer (e.g., "2h 14m until first response SLA").
2. Tickets within 25% of their SLA window display an amber warning indicator.
3. Tickets that have breached SLA display a red indicator with the amount of time overdue.
4. The countdown updates in the UI every 30 seconds without requiring a page refresh.
5. Sorting the queue by "SLA urgency" places the most at-risk tickets at the top.

---

**US-017: Receive SLA Warning Notification**
**Priority:** High | **Epic:** SLA & Escalation | **Points:** 3
> As a **support agent**, I want to receive a proactive warning notification before an SLA is breached, so that I have time to act before the ticket is escalated or marked as a breach.

**Acceptance Criteria:**
1. I receive an in-app notification and an optional email alert when a ticket I am assigned to reaches 75% of its first-response SLA window (threshold configurable by admin).
2. The notification includes the ticket ID, subject, customer name, and exact time remaining.
3. Clicking the notification opens the ticket directly.
4. If I have already responded (clock stopped), no warning is sent.
5. I can configure my personal notification preferences (in-app only, email only, both) for SLA warnings.

---

**US-018: Auto-Escalate Breached Tickets**
**Priority:** High | **Epic:** SLA & Escalation | **Points:** 5
> As a **supervisor**, I want tickets to be automatically escalated to me when an SLA is breached, so that I can intervene immediately and prevent a poor customer experience from going unaddressed.

**Acceptance Criteria:**
1. When a first-response SLA is breached, the system automatically sends me an escalation notification with the ticket ID, agent assigned, customer, and breach duration.
2. A system note is appended to the ticket: "SLA breached – escalated to supervisor [name] at [timestamp]."
3. If configured, the ticket is automatically reassigned to the escalation queue.
4. I can acknowledge the escalation from the notification, which records my name and timestamp on the ticket.
5. Repeat breaches on the same ticket trigger additional escalations with increasing notification urgency.

---

**US-019: Pause SLA Clock While Awaiting Customer**
**Priority:** Medium | **Epic:** SLA & Escalation | **Points:** 3
> As a **support agent**, I want to pause the SLA clock when I am waiting for the customer to provide more information, so that my SLA metrics are not penalized for time the customer is unresponsive.

**Acceptance Criteria:**
1. I can change the ticket status to `Pending Customer`, which pauses the resolution SLA clock immediately.
2. The ticket thread shows a system note: "SLA paused — awaiting customer response at [timestamp]."
3. When the customer replies or I manually resume the ticket, the SLA clock resumes from where it paused.
4. The paused duration is excluded from SLA reports; the SLA report shows both total elapsed time and active SLA time.
5. I cannot pause the first-response SLA clock; it only pauses once I have sent my first response.

---

## Epic 5: Agent Productivity

**US-020: Use Canned Responses**
**Priority:** High | **Epic:** Agent Productivity | **Points:** 3
> As a **support agent**, I want to insert canned responses into my replies with a shortcut, so that I can respond to common questions quickly without retyping the same content repeatedly.

**Acceptance Criteria:**
1. Typing `/` in the reply composer opens a canned response search panel.
2. I can search by keyword or browse by category; results show the response title and a preview of the first 100 characters.
3. Selecting a canned response inserts it at the cursor position with dynamic variables (e.g., `{{customer.firstName}}`) resolved to their actual values.
4. I can create personal canned responses visible only to me, or submit responses to the shared library for supervisor approval.
5. Canned response usage is tracked per response so managers can identify the most-used and most-useful templates.

---

**US-021: View KB Article Suggestions While Replying**
**Priority:** High | **Epic:** Agent Productivity | **Points:** 5
> As a **support agent**, I want the system to automatically suggest relevant knowledge base articles while I am composing a reply, so that I can provide accurate answers faster without leaving the ticket.

**Acceptance Criteria:**
1. As I type in the reply composer, a suggestion panel updates in real time (debounced at 1 second) showing the top-3 KB articles most relevant to the ticket subject and my current text.
2. Each suggestion shows the article title, category, and a two-sentence excerpt.
3. Clicking "Insert Link" adds a formatted article link to my reply; clicking "Copy Passage" copies the excerpt to my clipboard.
4. I can dismiss the suggestion panel and it will not reappear until I start a new reply.
5. If no relevant articles are found, the panel shows a "No suggestions found" message with a link to search the full KB.

---

**US-022: Manage My Ticket Queue View**
**Priority:** Medium | **Epic:** Agent Productivity | **Points:** 3
> As a **support agent**, I want to customize how my queue is displayed — sorting, filtering, and column visibility — so that I can work most efficiently given my personal workflow and current priorities.

**Acceptance Criteria:**
1. I can sort my queue by any column: SLA urgency, created date, updated date, priority, and customer name.
2. I can filter by status, channel, tag, priority, and any custom field.
3. I can show/hide columns from a configurable column picker; my preferences are saved per browser session and persist on next login.
4. I can save named filter combinations as "saved views" (e.g., "My Open Critical Email Tickets") and switch between them with one click.
5. The ticket count for each saved view is shown as a badge on the view tab.

---

**US-023: Switch Status and Track Availability**
**Priority:** High | **Epic:** Agent Productivity | **Points:** 2
> As a **support agent**, I want to set my availability status with a reason, so that the routing engine does not assign me tickets when I am unavailable and my supervisor can see my current activity at a glance.

**Acceptance Criteria:**
1. I can set my status to Online, Busy, Away (with a reason from a predefined list: Break, Lunch, Training, Meeting, Admin), or Offline.
2. My status change takes effect immediately and is reflected on the supervisor dashboard within 5 seconds.
3. When my status is Away or Offline, the routing engine does not assign me new tickets automatically.
4. If I am idle (no ticket activity and no status change) for longer than the configured idle timeout, my status automatically changes to `Away – Idle`.
5. My status history for the current shift is visible to supervisors in the agent monitoring panel.

---

**US-024: View My Performance Scorecard**
**Priority:** Medium | **Epic:** Agent Productivity | **Points:** 3
> As a **support agent**, I want to view my personal performance scorecard, so that I can track my own progress, identify areas for improvement, and prepare for coaching conversations with my team lead.

**Acceptance Criteria:**
1. My scorecard shows: tickets handled (today / this week / this month), average first-response time, average handle time, SLA compliance rate, and CSAT score for the selected period.
2. I can compare my metrics to my team's anonymized average.
3. Each metric has a trend indicator (up / down / neutral) compared to the previous equivalent period.
4. I can filter the scorecard by date range (last 7 days, last 30 days, last quarter, custom range).
5. I can export my scorecard as a PDF.

---

## Epic 6: Knowledge Base

**US-025: Author and Publish a KB Article**
**Priority:** High | **Epic:** Knowledge Base | **Points:** 5
> As a **knowledge manager**, I want to create and publish knowledge base articles with rich content, so that agents and customers can find accurate, well-formatted answers to common questions.

**Acceptance Criteria:**
1. The article editor supports: headings (H1–H3), ordered and unordered lists, bold/italic text, inline code, code blocks with syntax highlighting, images (drag-and-drop or URL), and embedded video URLs.
2. I can save an article as a draft without publishing it; drafts are only visible to authors and reviewers.
3. I can submit a draft for review; a designated reviewer receives a notification and can approve or reject with comments.
4. Approved articles are published immediately or at a scheduled future date/time.
5. Published articles are immediately indexed and available in the KB search within 30 seconds of publication.

---

**US-026: Search the Knowledge Base**
**Priority:** High | **Epic:** Knowledge Base | **Points:** 5
> As a **support agent**, I want to search the knowledge base using natural language queries, so that I can find relevant articles even when I do not know the exact title or keywords.

**Acceptance Criteria:**
1. The KB search bar accepts queries of up to 500 characters and returns results within 500 ms.
2. Results are ranked by relevance (combining keyword and semantic similarity); the most relevant article appears first.
3. Each result shows: article title, category breadcrumb, a snippet highlighting the matching passage, and the date last updated.
4. Searching for a phrase that exists verbatim in an article surfaces that article in the top 3 results.
5. Searching with a conceptually related query (e.g., "refund my purchase" matching an article titled "How to Request a Return") also returns relevant results.

---

**US-027: Rate an Article and Submit Feedback**
**Priority:** Low | **Epic:** Knowledge Base | **Points:** 2
> As a **customer**, I want to rate a knowledge base article and optionally leave a comment, so that the support team knows whether the article helped me and can improve content that is unclear or outdated.

**Acceptance Criteria:**
1. At the bottom of every published customer-facing article, there are two buttons: "👍 Helpful" and "👎 Not Helpful."
2. I can optionally type a comment (up to 500 characters) explaining my rating before submitting.
3. Submitting a rating does not require me to be logged in; my rating is anonymous unless I am already authenticated.
4. I can only rate each article once per session; the rating buttons are replaced with a "Thank you for your feedback" message after submission.
5. Articles with a helpful rate below 60% over the last 30 days appear in the knowledge manager's review queue automatically.

---

**US-028: Manage Article Versions**
**Priority:** Medium | **Epic:** Knowledge Base | **Points:** 3
> As a **knowledge manager**, I want to view the version history of an article and restore a previous version, so that I can safely iterate on content and roll back if a change introduces errors.

**Acceptance Criteria:**
1. The article editor shows a "Version History" tab listing all published versions with author name, publish date, and a short edit summary.
2. I can preview any historical version in a read-only view.
3. I can diff any two versions side-by-side with additions highlighted in green and deletions in red.
4. I can restore any historical version as the new draft; this creates a new draft version rather than overwriting the published version immediately.
5. Restoring a version creates an audit event: "Version X restored as draft by [user] at [timestamp]."

---

## Epic 7: Bot & Automation

**US-029: Define a Bot Conversation Flow**
**Priority:** High | **Epic:** Bot & Automation | **Points:** 8
> As an **administrator**, I want to build and deploy a chatbot flow using a visual editor, so that routine customer inquiries are handled automatically 24/7 without agent involvement.

**Acceptance Criteria:**
1. The bot flow editor provides drag-and-drop nodes for: greeting message, intent classification, condition branch, collect slot (text/number/date/option), API call action, KB lookup action, send message, and handoff to agent.
2. I can save a flow as a draft and test it using a simulated chat interface within the editor before publishing.
3. Publishing a flow takes effect within 60 seconds; the previous flow remains active until the new one is live.
4. Flows support multiple entry intents; the engine selects the matching flow based on the first message's classified intent.
5. Invalid or incomplete flows (e.g., a branch with no terminal node) are highlighted as errors and cannot be published until resolved.

---

**US-030: Graceful Handoff from Bot to Agent**
**Priority:** High | **Epic:** Bot & Automation | **Points:** 8
> As a **customer**, I want to be seamlessly connected to a human agent when the bot cannot resolve my issue, so that I do not have to repeat myself and the agent has all the context from my bot interaction.

**Acceptance Criteria:**
1. When the bot's intent confidence drops below the configured threshold (default: 70%) for two consecutive turns, the bot informs me: "Let me connect you with an agent who can help."
2. The agent receives the complete bot conversation transcript and a summary of extracted slots (e.g., account number, issue type) in the ticket before sending their first message.
3. I remain in the same chat session throughout the handoff; there is no page refresh or reconnect required.
4. If no agent is available, the bot provides me an estimated wait time and offers to send me a notification when an agent is ready.
5. The handoff is completed and I receive an agent response within the queue's SLA first-response window; a breach is counted if the agent does not respond in time even if the bot context was handed over within SLA.

---

**US-031: Create an Automation Rule**
**Priority:** High | **Epic:** Bot & Automation | **Points:** 5
> As an **administrator**, I want to create event-driven automation rules that execute actions on tickets when certain conditions are met, so that repetitive triage tasks are handled automatically and consistently.

**Acceptance Criteria:**
1. I can create a rule triggered by events: `ticket.created`, `ticket.updated`, `ticket.replied`, `ticket.idle` (no activity for N hours).
2. Conditions support: channel equals, priority equals/greater than, subject contains, tag contains, customer tier equals, assigned agent equals, and custom field comparisons.
3. Actions available: set priority, add tag, remove tag, assign to queue, assign to agent, send canned response, add internal note, close ticket, and call webhook.
4. Rules are active by default on creation and can be toggled on/off without deletion.
5. Each rule has a "Last Triggered" timestamp and a 30-day trigger count visible in the rule list, so I can audit automation activity.

---

**US-032: Use Auto-Suggested Tags**
**Priority:** Low | **Epic:** Bot & Automation | **Points:** 3
> As a **support agent**, I want the system to automatically suggest relevant tags on new tickets based on their content, so that I spend less time manually categorizing tickets and my tagging is more consistent.

**Acceptance Criteria:**
1. When a ticket is created or first opened in my workspace, the system shows up to 5 suggested tags derived from the ticket's subject and body using the ML classifier.
2. Each suggested tag is displayed with a confidence percentage and a one-click "Accept" button.
3. I can accept individual tags or accept all suggested tags with one click.
4. Rejected tags are not re-suggested on the same ticket.
5. Accepted and rejected tag decisions are sent as feedback to the classifier training pipeline for continuous improvement.

---

## Epic 8: Customer 360°

**US-033: View Full Customer History on a Ticket**
**Priority:** High | **Epic:** Customer 360° | **Points:** 5
> As a **support agent**, I want to see a complete history of all past interactions with a customer while handling their ticket, so that I have full context and do not ask them to repeat information they have already provided.

**Acceptance Criteria:**
1. The ticket workspace displays a customer panel showing: contact details, company, account tier, and a chronological list of all past tickets (open and closed) across all channels.
2. Each past ticket entry shows: ticket ID, subject, channel, date, handling agent, and resolution status.
3. I can click on any past ticket from the panel to open it in a side-drawer without leaving the current ticket.
4. The panel also shows the customer's CSAT rating history (last 5 surveys) and their current NPS score category (Promoter / Passive / Detractor).
5. The customer panel loads within 1 second of opening the ticket.

---

**US-034: Merge Duplicate Customer Records**
**Priority:** Medium | **Epic:** Customer 360° | **Points:** 5
> As a **supervisor**, I want to merge duplicate customer records, so that the agent sees a unified history and the customer is not treated as multiple different people.

**Acceptance Criteria:**
1. The customer profile page shows a "Possible Duplicates" alert when other records share the same email or phone number.
2. I can review the duplicate records side-by-side and select which record is the primary (surviving) record.
3. Upon confirming the merge, all tickets, surveys, and contact history from the secondary record are moved to the primary record.
4. The secondary record is marked `inactive – merged` and a link to the primary is displayed; it is not deleted (for audit purposes).
5. A merge event is logged in the audit trail with: actor, timestamp, primary record ID, and secondary record ID.

---

**US-035: Send Automatic CSAT Survey After Ticket Close**
**Priority:** High | **Epic:** Customer 360° | **Points:** 5
> As a **supervisor**, I want CSAT surveys sent automatically when a ticket is closed, so that I get consistent customer satisfaction feedback without relying on agents to remember to send surveys manually.

**Acceptance Criteria:**
1. When a ticket transitions to `Closed`, a CSAT survey is queued for delivery after the configured delay (default: 1 hour).
2. The survey is delivered via the same channel as the ticket (email for email tickets, in-chat prompt for chat tickets).
3. The survey asks: "How satisfied were you with the support you received? (1–5 stars)" with an optional comment field.
4. Survey responses are linked to the ticket, the handling agent, and the queue for attribution.
5. If the customer has already received a survey for another ticket within the last 7 days, the survey is suppressed to avoid survey fatigue.

---

**US-036: Track NPS Trends**
**Priority:** Medium | **Epic:** Customer 360° | **Points:** 3
> As a **supervisor**, I want to see NPS trends over time, so that I can track whether our overall service quality is improving or declining and take action on detractor feedback.

**Acceptance Criteria:**
1. The NPS dashboard shows the current NPS score, the percentage of Promoters/Passives/Detractors, and a trend line for the last 12 months.
2. I can filter NPS data by customer segment, product, and date range.
3. Detractor responses (score 0–6) are listed with the customer name, score, comment, and a "Create Follow-Up Ticket" button.
4. Clicking "Create Follow-Up Ticket" opens a pre-filled ticket with the customer linked and a note containing their NPS comment.
5. NPS data is exportable as CSV with all response details.

---

## Epic 9: Supervisor & Workforce

**US-037: Monitor Real-Time Queue on Supervisor Dashboard**
**Priority:** High | **Epic:** Supervisor & Workforce | **Points:** 8
> As a **supervisor**, I want a real-time dashboard showing the health of all queues and agent statuses, so that I can intervene proactively when queues are backing up or agents are struggling.

**Acceptance Criteria:**
1. The dashboard refreshes every 5 seconds and shows for each queue: ticket count, average wait time, SLA at-risk count, and agents currently serving that queue.
2. Queues with a wait time exceeding their SLA first-response target are highlighted in red.
3. The agent panel shows each agent's name, current status, current ticket (linked), tickets handled today, and today's CSAT score.
4. I can click on any queue or agent to drill into a detail view without navigating away from the dashboard.
5. The dashboard is configurable: I can choose which queues and metrics are displayed in my personal dashboard layout.

---

**US-038: Force Reassign a Ticket**
**Priority:** High | **Epic:** Supervisor & Workforce | **Points:** 3
> As a **supervisor**, I want to force-reassign any ticket to a different agent or queue from the dashboard, so that I can intervene immediately when an agent is overloaded or a ticket needs specialized handling.

**Acceptance Criteria:**
1. From the supervisor dashboard or any ticket detail, I can use a "Reassign" action and select any active agent or queue as the target.
2. The reassignment takes effect within 5 seconds; the original agent receives a notification that the ticket has been reassigned.
3. The new agent receives an assignment notification immediately.
4. A system note is added to the ticket: "Reassigned from [Agent A] to [Agent B] by Supervisor [Name] at [timestamp] — [optional reason]."
5. Forced reassignment does not reset the SLA clock; the original ticket creation time remains the SLA baseline.

---

**US-039: Build Agent Schedules**
**Priority:** Medium | **Epic:** Supervisor & Workforce | **Points:** 8
> As a **workforce manager**, I want to create and publish weekly shift schedules for my team, so that agents know their working hours and the system accurately reflects staffing availability for routing and forecasting.

**Acceptance Criteria:**
1. The schedule builder shows a weekly calendar grid per agent; I can drag time blocks to set shift start/end times and break windows.
2. I can create reusable schedule templates (e.g., "Standard 9–5 Mon–Fri") and apply them to multiple agents at once.
3. Published schedules are visible to agents in their personal schedule view.
4. The routing engine uses published schedule data to determine expected agent availability when calculating queue staffing levels.
5. Schedule changes published with less than 24 hours notice trigger a notification to the affected agents.

---

**US-040: Review Agent Adherence**
**Priority:** Medium | **Epic:** Supervisor & Workforce | **Points:** 5
> As a **workforce manager**, I want to see how closely agents adhere to their scheduled shifts, so that I can identify patterns of late starts, early departures, or extended breaks and address them in coaching sessions.

**Acceptance Criteria:**
1. The adherence report shows, per agent per day: scheduled start time, actual first Online status time, scheduled end time, actual last Online status time, and total scheduled vs. actual Online minutes.
2. Each agent's daily adherence score is shown as a percentage: (actual Online minutes ÷ scheduled Online minutes) × 100.
3. Agents with adherence below a configurable threshold (default: 90%) are highlighted in the report.
4. I can drill into any day to see a minute-by-minute timeline of the agent's status changes.
5. The report is available for any date range up to 90 days and is exportable as CSV.

---

## Epic 10: Reporting & Analytics

**US-041: Generate SLA Compliance Report**
**Priority:** High | **Epic:** Reporting & Analytics | **Points:** 5
> As a **supervisor**, I want to generate an SLA compliance report for any time period, so that I can understand where SLA breaches are occurring and take corrective action with specific queues, agents, or policy definitions.

**Acceptance Criteria:**
1. I can navigate to Reports → SLA Compliance and select a date range, queue filter, and agent filter.
2. The report shows: total tickets, tickets within SLA, tickets breached, breach rate (%), and average time-to-breach for breached tickets.
3. I can group the report by queue, agent, channel, or customer tier to identify patterns.
4. The report renders within 30 seconds for date ranges up to 90 days.
5. I can export the report as CSV (raw data) or PDF (formatted report with chart).

---

**US-042: Build a Custom Report**
**Priority:** Medium | **Epic:** Reporting & Analytics | **Points:** 8
> As a **supervisor**, I want to build a custom report combining metrics and dimensions of my choice, so that I can answer specific operational questions that are not covered by the pre-built reports.

**Acceptance Criteria:**
1. The custom report builder provides a metric catalog with at minimum: ticket volume, first-response time (avg/p50/p95), handle time, resolution time, SLA breach count, CSAT score, NPS score, and bot containment rate.
2. I can add up to 4 dimensions (group-by fields) such as channel, queue, agent, team, topic, and customer tier.
3. I can preview the report with a sample of 100 rows before saving.
4. I can save the report with a name and description; saved reports appear in a "My Reports" list.
5. I can schedule the report to be emailed to a list of recipients daily, weekly, or monthly as a PDF or CSV attachment.

---

**US-043: View Real-Time Operational Dashboard**
**Priority:** High | **Epic:** Reporting & Analytics | **Points:** 5
> As a **team lead**, I want a real-time operational dashboard I can display on a wall monitor in the contact center, so that the entire team can see live queue health and stay motivated to hit SLA targets.

**Acceptance Criteria:**
1. The dashboard has a "TV Mode" that removes navigation chrome and displays a full-screen, auto-refreshing wallboard.
2. The wallboard shows: queue depth and SLA status for each active queue, current CSAT (rolling 24h), and the top 3 agents by tickets resolved today.
3. The wallboard refreshes automatically every 5 seconds without requiring user interaction.
4. TV Mode is accessible via a direct URL with an auth token so it can be opened on a shared display without an agent login.
5. The layout is responsive and readable at 1920×1080 resolution from a distance of 3 meters.

---

## Epic 11: Administration & Compliance

**US-044: Configure SLA Policies**
**Priority:** High | **Epic:** Administration & Compliance | **Points:** 5
> As a **system administrator**, I want to define and manage SLA policies for different customer tiers and channels, so that the system automatically enforces the correct response and resolution targets for every ticket.

**Acceptance Criteria:**
1. I can create a named SLA policy with configurable targets for first-response time and resolution time, in minutes, hours, or business hours.
2. I can associate an SLA policy with specific queues, customer tiers (Gold/Silver/Bronze), channels, or ticket priorities.
3. Editing a policy applies the new targets only to tickets created after the change; in-flight tickets continue with the policy version active at their creation time.
4. I can deactivate an SLA policy; deactivated policies are not applied to new tickets but remain accessible for historical reporting.
5. A policy change is recorded in the audit log with the before/after values and the administrator who made the change.

---

**US-045: Manage RBAC Roles and Permissions**
**Priority:** High | **Epic:** Administration & Compliance | **Points:** 5
> As a **system administrator**, I want to assign roles to users and create custom roles with specific permissions, so that each person in the organization has exactly the access they need and no more.

**Acceptance Criteria:**
1. I can assign one or more roles to any user from the user management screen; changes take effect within 60 seconds.
2. I can create custom roles by selecting a subset of permissions from the permission catalog organized by resource (Ticket, Agent, Queue, KB, Report, Admin, Audit).
3. Built-in roles (Agent, Supervisor, Admin, Auditor) cannot be deleted, but their permissions can be viewed for reference.
4. Attempting to access a resource without the required permission returns HTTP 403 and is logged in the audit log.
5. I can export the current permission matrix as a CSV showing all roles and their granted permissions for compliance documentation.

---

**US-046: Export Audit Logs for Compliance Review**
**Priority:** High | **Epic:** Administration & Compliance | **Points:** 3
> As a **compliance officer**, I want to export audit logs covering all data access and modification events for a specific date range, so that I can satisfy regulatory inspection requests and internal security reviews.

**Acceptance Criteria:**
1. I can access the Audit Log screen (Read-Only Auditor role or above) and filter by: date range, actor, resource type, action type, and IP address.
2. The filtered log is exportable as CSV and JSON; exports up to 100,000 records complete within 2 minutes.
3. Each audit log entry contains: event ID, timestamp (UTC), actor ID, actor role, action type, resource type, resource ID, IP address, user agent, and change delta.
4. Audit logs are append-only; no user (including System Administrator) can delete or modify individual audit log entries through the UI or API.
5. Export actions are themselves recorded in the audit log: "Audit log exported by [user] covering [date range] at [timestamp]."

---

**US-047: Execute GDPR Right-to-Erasure Request**
**Priority:** High | **Epic:** Administration & Compliance | **Points:** 8
> As a **system administrator**, I want to process a verified GDPR right-to-erasure request for a specific customer, so that the organization meets its Article 17 obligation within the required 30-day window.

**Acceptance Criteria:**
1. I can search for a customer by email or ID in the Privacy Controls panel and initiate an erasure request with a case reference number.
2. The system performs the following within 48 hours of initiation: replaces all PII fields (name, email, phone, IP address) in the customer record and all linked ticket threads with `[REDACTED]`, removes the customer's data from Elasticsearch indexes, and purges their data from the KB article feedback store.
3. Call recording transcripts linked to the customer are redacted of PII but the audio recording metadata (not the audio itself) is retained for regulatory audit if a litigation hold applies.
4. A completion report is generated listing every record type modified, the count of records affected, and the timestamp of each redaction operation.
5. Aggregate analytics data (e.g., CSAT aggregate scores, queue volume counts) that cannot be re-identified are not deleted; only individually identifiable records are redacted.
