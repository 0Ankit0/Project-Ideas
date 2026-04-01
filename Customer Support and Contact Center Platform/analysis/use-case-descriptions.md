# Use Case Descriptions — Customer Support and Contact Center Platform

**Version:** 1.1  
**Last Updated:** 2025-07  
**Status:** Approved

---

## Overview

This document provides fully detailed, structured use case descriptions for the twelve primary use cases of the Customer Support and Contact Center Platform. Each entry follows a standard template covering actors, pre/post-conditions, main success scenario, alternative flows, exception flows, and referenced business rules. These descriptions serve as the authoritative input for acceptance criteria, QA test case design, and API contract definition.

---

## Business Rules Reference

| Rule ID | Rule Description |
|---|---|
| BR-001 | A ticket must be associated with a valid Contact record before it enters any queue. |
| BR-002 | SLA policy is selected based on the matrix: [customer tier] × [channel] × [issue category]. |
| BR-003 | First-response SLA timer starts when a ticket is placed in an agent-visible queue. |
| BR-004 | A ticket may only be in one queue at a time; queue change is an auditable event. |
| BR-005 | An agent can hold a maximum of `agent.max_concurrent_tickets` open tickets simultaneously. |
| BR-006 | A CSAT survey is sent exactly once per resolved ticket via the customer's preferred channel. |
| BR-007 | Bot confidence must be ≥ 0.75 to auto-respond; below this threshold the bot must escalate or collect clarification. |
| BR-008 | Human handoff transfers the full bot conversation transcript and detected intent to the receiving agent. |
| BR-009 | SLA clock is paused only in `PENDING_CUSTOMER` status and resumes automatically on customer reply. |
| BR-010 | A GDPR deletion request must be completed or formally rejected within 30 calendar days. |
| BR-011 | Merged tickets retain the lower-ID ticket number as canonical; all communications thread under the canonical ID. |
| BR-012 | A knowledge article requires at least one approver review before publication. |

---

## UC-001: Submit Support Request via Email

| Field | Value |
|---|---|
| **Use Case ID** | UC-001 |
| **Name** | Submit Support Request via Email |
| **Version** | 1.0 |
| **Priority** | Critical |
| **Primary Actor** | Customer |
| **Secondary Actors** | Email Ingestion Adapter, Deduplication Service, Contact Service, SLA Engine, Notification Service |

### Preconditions
1. The customer has access to an email client and knows the support email address.
2. The email ingestion adapter is polling or has an active IMAP/SMTP webhook configured.
3. The platform has at least one active SLA policy matching the customer's tier (or a default policy exists).

### Postconditions (Success)
1. A new Ticket record is created in `OPEN` status with a system-generated ticket ID.
2. The ticket is associated with an existing or newly created Contact record.
3. An SLA policy is applied and the first-response timer has started.
4. The ticket is placed in the appropriate routing queue.
5. The customer receives an auto-acknowledgement email containing the ticket ID and expected response window.

### Main Success Scenario

| Step | Actor | Action |
|---|---|---|
| 1 | Customer | Sends email to `support@example.com` with subject and body describing the issue; optionally attaches files. |
| 2 | Email Adapter | Polls mailbox (or receives webhook push) and fetches the raw email message. |
| 3 | Email Adapter | Parses `From`, `Subject`, `Body`, and attachments; generates a normalized `InboundMessageEvent`. |
| 4 | Ingestion Service | Invokes Deduplication Service using `Message-ID` header and `From` address to check for an existing open ticket matching the same thread. |
| 5 | Deduplication Service | Returns `NO_MATCH`; proceeds as a new ticket. |
| 6 | Contact Service | Looks up the sender email address; finds an existing Contact record and returns `contact_id`. |
| 7 | Ticket Service | Creates a `Ticket` with fields: `channel=EMAIL`, `subject`, `body_html`, `contact_id`, `status=OPEN`, and attachment references. |
| 8 | SLA Engine | Reads contact tier and issue category; selects matching SLA policy; sets `first_response_due_at` and `resolution_due_at` on the ticket. |
| 9 | Routing Engine | Evaluates routing rules; assigns ticket to queue `GENERAL_SUPPORT_L1` with priority `NORMAL`. |
| 10 | Notification Service | Sends auto-acknowledgement email to customer with ticket ID and SLA-based response window. |
| 11 | Audit Service | Emits `ticket.created` event to the audit log with actor, timestamp, and ticket snapshot. |

### Alternative Flows

**AF-001A — Thread Continuation (Duplicate Detection Hits)**
- At step 5, Deduplication Service returns `MATCH` with an existing open `ticket_id`.
- Ingestion Service adds the new email as a reply `Message` on the existing ticket.
- SLA clock is not restarted; `updated_at` is refreshed.
- Agent notification is sent if the ticket is in `PENDING_CUSTOMER` status (auto-resumes SLA clock per BR-009).

**AF-001B — Unknown Customer (No Contact Record)**
- At step 6, Contact Service returns `NOT_FOUND`.
- Contact Service creates a new Contact record with `source=EMAIL` and `verified=false`.
- Ticket creation proceeds as normal with the new `contact_id`.
- A verification email is optionally sent based on tenant configuration.

**AF-001C — No Matching SLA Policy**
- At step 8, SLA Engine finds no matching policy.
- SLA Engine applies the tenant-level default SLA policy.
- An admin alert is raised: `"SLA policy gap detected for tier/category combination"`.

### Exception Flows

**EF-001A — Malformed Email / Parsing Failure**
- At step 3, the email body or headers cannot be parsed (e.g., unknown encoding).
- The raw email is placed in a `dead_letter_queue` with error code `PARSE_FAILURE`.
- An alert is sent to the platform operations team.
- No ticket is created; the customer receives no acknowledgement (manual intervention required).

**EF-001B — Attachment Size Exceeds Limit**
- At step 3, one or more attachments exceed the configured limit (default: 25 MB).
- Oversized attachments are discarded; a note is added to the ticket body.
- Ticket creation proceeds; the customer receives acknowledgement with a note that oversized attachments were dropped.

**EF-001C — Ingestion Service Unavailable**
- At step 3, the ingestion service is down.
- The email adapter retries with exponential back-off (3 attempts, max 5 minutes).
- If all retries fail, the raw email is stored in the durable `inbound_email_backlog` table for replay.

---

## UC-002: Handle Live Chat Session

| Field | Value |
|---|---|
| **Use Case ID** | UC-002 |
| **Name** | Handle Live Chat Session |
| **Primary Actor** | Customer |
| **Secondary Actors** | Chat Widget SDK, Bot Engine, Routing Engine, Support Agent, Notification Service |

### Preconditions
1. The chat widget is embedded and loaded on the customer-facing web or mobile surface.
2. At least one agent is online and accepting chat sessions, or the bot is configured to handle overflow.

### Postconditions (Success)
1. A Chat Session record and associated Ticket are created and linked.
2. The customer's issue is resolved or escalated within the session or via a follow-up ticket.
3. CSAT survey is queued for dispatch per BR-006.

### Main Success Scenario

| Step | Actor | Action |
|---|---|---|
| 1 | Customer | Opens the chat widget; optionally authenticates via SSO token or enters name/email. |
| 2 | Chat Widget | Establishes a WebSocket connection to the Chat Gateway; sends `session.start` event with device and locale metadata. |
| 3 | Bot Engine | Greets the customer with a welcome message and prompts for issue description. |
| 4 | Customer | Types the issue description. |
| 5 | Bot Engine | Runs NLP intent classification (per UC-005). If confidence ≥ 0.75, attempts automated resolution. If resolved, session ends early. |
| 6 | Bot Engine | Confidence < 0.75; initiates human handoff (UC-006). |
| 7 | Routing Engine | Finds available agent with matching skill tags; reserves the agent slot. |
| 8 | Agent | Receives `chat.assigned` notification; opens the conversation panel with bot transcript visible. |
| 9 | Customer & Agent | Exchange real-time messages over WebSocket; agent can insert KB article snippets or canned responses. |
| 10 | Agent | Resolves the issue; clicks "Resolve" on the ticket. |
| 11 | System | Marks ticket `RESOLVED`; triggers CSAT survey dispatch (per BR-006). |
| 12 | Customer | Receives survey inline in the chat widget or via email. |

### Alternative Flows

**AF-002A — No Agent Available (Queue Wait)**
- At step 7, no agent is available; customer is placed in a virtual queue.
- Bot sends estimated wait time and offers the option to receive an email callback instead.
- If wait exceeds configurable threshold, customer is offered to leave a message and receive an async reply.

**AF-002B — Customer Abandons Session**
- Customer closes the chat widget without resolution.
- Session marked `ABANDONED`; ticket remains open in `PENDING_CUSTOMER` status.
- System sends a re-engagement email after 30 minutes (configurable).

### Exception Flows

**EF-002A — WebSocket Disconnection**
- The WebSocket drops mid-conversation.
- Chat Gateway buffers outgoing messages for 2 minutes.
- On reconnect within the buffer window, session resumes transparently.
- If reconnect fails after buffer window, ticket is set to `PENDING_CUSTOMER` and agent is notified.

---

## UC-003: Route Ticket to Agent (Skill-Based)

| Field | Value |
|---|---|
| **Use Case ID** | UC-003 |
| **Name** | Route Ticket to Agent via Skill-Based Routing |
| **Primary Actor** | Routing Engine |
| **Secondary Actors** | Support Agent, Supervisor, Queue Manager |

### Preconditions
1. Ticket exists in `OPEN` status and has been classified with an `issue_category` and `required_skills` list.
2. Agent skill profiles are up to date in the workforce directory.
3. At least one active routing rule is configured for the ticket's queue.

### Postconditions (Success)
1. Ticket is assigned to an agent whose skill tags fully satisfy the ticket's `required_skills`.
2. Ticket status transitions to `ASSIGNED`.
3. Agent receives real-time `ticket.assigned` push notification.

### Main Success Scenario

| Step | Actor | Action |
|---|---|---|
| 1 | Routing Engine | Picks next ticket from the priority queue (highest priority + oldest first). |
| 2 | Routing Engine | Reads `required_skills` from ticket metadata (e.g., `["billing", "enterprise_tier"]`). |
| 3 | Routing Engine | Queries Workforce Service for agents in `AVAILABLE` status whose skill tags include all required skills. |
| 4 | Routing Engine | Filters by `current_ticket_count < max_concurrent_tickets` (BR-005). |
| 5 | Routing Engine | Applies the configured dispatch algorithm (least-loaded, round-robin, or longest-idle). |
| 6 | Routing Engine | Tentatively reserves the selected agent (optimistic lock with 10-second TTL). |
| 7 | Routing Engine | Commits assignment: sets `assigned_agent_id` on ticket, transitions status to `ASSIGNED`. |
| 8 | Notification Service | Pushes `ticket.assigned` event to agent's active session. |

### Alternative Flows

**AF-003A — No Qualifying Agent Available**
- At step 3, no agent meets skill requirements and availability criteria.
- Ticket remains in queue; re-evaluation occurs on a configurable polling interval (default: 30 seconds).
- If ticket waits > configured threshold, supervisor is notified and overflow rules are evaluated (UC-020).

**AF-003B — Agent Rejects Assignment**
- Agent is unavailable at time of push (e.g., status changed between lock and commit).
- Optimistic lock expires; Routing Engine retries from step 1 with the next eligible agent.

### Exception Flows

**EF-003A — Routing Engine Failure**
- Routing Engine becomes unavailable.
- Tickets are held in queue; a fallback cron job reassigns un-claimed tickets every 5 minutes using a simplified round-robin.
- Ops alert raised: `"Routing Engine degraded — fallback active"`.

---

## UC-004: Monitor and Escalate SLA Breach

| Field | Value |
|---|---|
| **Use Case ID** | UC-004 |
| **Name** | Monitor and Escalate SLA Breach |
| **Primary Actor** | SLA Monitor Service |
| **Secondary Actors** | Escalation Engine, Supervisor, Notification Service, Agent |

### Preconditions
1. Ticket has an active SLA policy with `first_response_due_at` and `resolution_due_at` timestamps.
2. SLA Monitor is running and evaluating tickets at the configured polling interval (≤ 60 seconds).

### Postconditions (Success)
1. Warning notification sent to agent at warning threshold (configurable, default: 75% of SLA elapsed).
2. Breach event published at the breach threshold.
3. Escalation actions applied: priority bumped, supervisor notified, optional reassignment.
4. `sla_breach_at` timestamp recorded on the ticket.

### Main Success Scenario

| Step | Actor | Action |
|---|---|---|
| 1 | SLA Monitor | Polls the database for tickets with `status NOT IN (RESOLVED, CLOSED)` and `sla_status = ACTIVE`. |
| 2 | SLA Monitor | For each ticket, calculates `elapsed_percentage = (now - created_at) / (resolution_due_at - created_at)`. |
| 3 | SLA Monitor | Detects ticket A has elapsed 75% without first response; emits `sla.warning` event. |
| 4 | Notification Service | Sends in-app and email warning to assigned agent and supervisor. |
| 5 | SLA Monitor | On next poll cycle, detects ticket A has breached `first_response_due_at`. |
| 6 | SLA Monitor | Emits `sla.breached` event with breach type `FIRST_RESPONSE`. |
| 7 | Escalation Engine | Evaluates escalation rules: bumps ticket priority to `CRITICAL`; reassigns to next available senior agent. |
| 8 | Notification Service | Sends breach alert to supervisor's dashboard, email, and (if configured) SMS. |
| 9 | Agent / Supervisor | Acknowledges the breach; supervisor adds breach reason code. |
| 10 | SLA Monitor | Records `sla_breach_at`, `breach_acknowledged_at`, and `breach_reason` on the ticket. |

### Alternative Flows

**AF-004A — SLA Paused (Waiting on Customer)**
- Ticket status is `PENDING_CUSTOMER`; SLA clock is paused per BR-009.
- Monitor skips elapsed calculation for paused tickets.
- Clock resumes when ticket transitions back to `IN_PROGRESS` on customer reply.

### Exception Flows

**EF-004A — SLA Monitor Lag**
- Monitor processing falls behind due to high ticket volume.
- If lag > 5 minutes, ops alert fires; a secondary monitor instance is spun up.

---

## UC-005: Bot Handles Customer Query with NLP

| Field | Value |
|---|---|
| **Use Case ID** | UC-005 |
| **Name** | Bot Handles Customer Query with NLP |
| **Primary Actor** | Bot Engine |
| **Secondary Actors** | Customer, NLP Service, Knowledge Base Service |

### Preconditions
1. Bot is active and deployed on the relevant channel (chat, WhatsApp, or IVR).
2. NLP service endpoint is reachable with latency < 500 ms.
3. Knowledge base is populated with published articles.

### Postconditions (Success)
1. Customer's intent is identified with confidence ≥ 0.75.
2. A relevant knowledge article or canned response is delivered.
3. Customer confirms resolution; session closes without human agent involvement.

### Main Success Scenario

| Step | Actor | Action |
|---|---|---|
| 1 | Customer | Sends a message: _"How do I reset my password?"_ |
| 2 | Bot Engine | Sends the message text to NLP Service for intent classification. |
| 3 | NLP Service | Returns: `intent=password_reset`, `confidence=0.92`, `entities={}`. |
| 4 | Bot Engine | Validates confidence ≥ 0.75 (BR-007). |
| 5 | Bot Engine | Queries Knowledge Base Service with `intent=password_reset`; retrieves top article. |
| 6 | Bot Engine | Renders the article summary with a "Learn More" deep link and sends to customer. |
| 7 | Customer | Replies: _"That worked, thanks!"_ |
| 8 | Bot Engine | Classifies reply intent as `positive_resolution_confirmation`. |
| 9 | Bot Engine | Marks bot session `RESOLVED_BY_BOT`; increments deflection counter; sends CSAT prompt. |

### Alternative Flows

**AF-005A — Low Confidence — Clarification Loop**
- At step 4, confidence is between 0.50 and 0.74.
- Bot asks a clarifying question: _"Are you looking to reset your login password or your PIN?"_
- Up to 2 clarification rounds attempted; if still below threshold, escalates to human (UC-006).

### Exception Flows

**EF-005A — NLP Service Timeout**
- NLP call exceeds 500 ms or times out.
- Bot falls back to keyword matching.
- If keyword match found, bot responds; otherwise triggers human handoff with message: _"Let me connect you to an agent."_

---

## UC-006: Bot Transfers to Human Agent

| Field | Value |
|---|---|
| **Use Case ID** | UC-006 |
| **Name** | Bot Transfers to Human Agent |
| **Primary Actor** | Bot Engine |
| **Secondary Actors** | Customer, Handoff Coordinator, Routing Engine, Support Agent |

### Preconditions
1. An active bot session exists with transcript history.
2. Human agents are online or a queuing mechanism is available.

### Postconditions (Success)
1. Full bot transcript and detected intent are transferred to the receiving agent (BR-008).
2. Agent acknowledges the handoff and begins responding to the customer.
3. A new Ticket is created (or existing ticket updated) with `source=BOT_HANDOFF`.

### Main Success Scenario

| Step | Actor | Action |
|---|---|---|
| 1 | Bot Engine | Determines handoff required (confidence < threshold, max clarifications reached, or customer typed _"agent"_). |
| 2 | Bot Engine | Notifies customer: _"Connecting you to a live agent. Average wait: 2 minutes."_ |
| 3 | Handoff Coordinator | Packages handoff payload: `{bot_transcript, detected_intent, confidence_history, contact_id}`. |
| 4 | Routing Engine | Selects available agent based on intent-derived skill requirements (UC-003). |
| 5 | Agent | Receives `chat.handoff` notification with embedded transcript panel. |
| 6 | Agent | Types a greeting that is delivered to customer; handoff is complete. |
| 7 | Handoff Coordinator | Updates ticket with `handoff_at` timestamp and `handoff_agent_id`. |
| 8 | Bot Engine | Ends bot session and transitions into observer mode for QA. |

### Exception Flows

**EF-006A — No Agent Available During Handoff**
- No agent is available at step 4.
- Customer is placed in queue; bot maintains the session and provides wait time updates every 60 seconds.
- If wait exceeds 10 minutes, bot offers async email callback.

---

## UC-007: Agent Resolves Ticket and Sends CSAT Survey

| Field | Value |
|---|---|
| **Use Case ID** | UC-007 |
| **Name** | Agent Resolves Ticket and Sends CSAT Survey |
| **Primary Actor** | Support Agent |
| **Secondary Actors** | Ticket Service, SLA Monitor, Notification Service, Analytics Service |

### Preconditions
1. Ticket is in `IN_PROGRESS` or `PENDING_CUSTOMER` status and is assigned to the agent.
2. The customer's preferred contact channel is recorded.

### Postconditions (Success)
1. Ticket status transitions to `RESOLVED`.
2. SLA resolution timer stops; `resolved_at` is recorded.
3. CSAT survey is dispatched exactly once to the customer (BR-006).
4. Ticket auto-closes after configured hold period (default: 48 hours) unless customer reopens.

### Main Success Scenario

| Step | Actor | Action |
|---|---|---|
| 1 | Agent | Reviews the issue and customer communication history. |
| 2 | Agent | Sends a resolution message to the customer via the active channel. |
| 3 | Agent | Selects a disposition code (e.g., `RESOLVED_FIRST_CONTACT`) and clicks "Mark Resolved". |
| 4 | Ticket Service | Validates agent is assigned to the ticket; transitions status to `RESOLVED`; records `resolved_at`. |
| 5 | SLA Monitor | Stops resolution SLA timer; calculates `resolution_time_minutes`. |
| 6 | Notification Service | Dispatches CSAT survey email (or in-app) with 5-star rating prompt and optional comment field. |
| 7 | Analytics Service | Publishes `ticket.resolved` metric event for AHT and SLA compliance dashboards. |
| 8 | Auto-Close Job | After 48-hour hold period, transitions ticket to `CLOSED` if no customer reply. |

### Alternative Flows

**AF-007A — Customer Replies Within Hold Period**
- Customer replies within 48 hours; ticket reopens automatically.
- CSAT survey is cancelled if not yet submitted.

### Exception Flows

**EF-007A — CSAT Dispatch Failure**
- Notification Service fails to send the survey email.
- Retry queue attempts delivery 3 times over 1 hour.
- On persistent failure, logs `csat_survey_failed` event; manual follow-up flagged in agent queue.

---

## UC-008: Supervisor Monitors Real-Time Dashboard

| Field | Value |
|---|---|
| **Use Case ID** | UC-008 |
| **Name** | Supervisor Monitors Real-Time Dashboard |
| **Primary Actor** | Team Lead / Supervisor |
| **Secondary Actors** | Analytics Service, Notification Service |

### Preconditions
1. Supervisor has `SUPERVISOR` role with access to queue and agent metrics.
2. Real-time analytics pipeline is streaming data with latency ≤ 5 seconds.

### Postconditions (Success)
1. Supervisor has an accurate, live view of all queue health metrics, agent statuses, and SLA risk tickets.
2. Any intervention actions taken (reassign, flag, escalate) are recorded in the audit log.

### Main Success Scenario

| Step | Actor | Action |
|---|---|---|
| 1 | Supervisor | Opens the Real-Time Dashboard from the supervisor portal. |
| 2 | Dashboard | Renders live widgets: queue depth, AHT, agents by status, SLA at-risk tickets, CSAT trend. |
| 3 | Supervisor | Reviews `SLA At-Risk` panel; sees Ticket #4821 is 80% through SLA with no response. |
| 4 | Supervisor | Clicks "Reassign" on Ticket #4821; selects Agent B who has capacity. |
| 5 | Ticket Service | Reassigns ticket; audit event `ticket.reassigned` with supervisor ID recorded. |
| 6 | Agent B | Receives `ticket.assigned` notification. |
| 7 | Supervisor | Sets a watch alert on Agent C (AHT > 20 minutes threshold) via the dashboard alert builder. |

### Alternative Flows

**AF-008A — Dashboard Data Stale**
- If the analytics stream lag exceeds 10 seconds, a "Data delayed" banner appears on the dashboard.
- Supervisor can manually trigger a data refresh.

---

## UC-009: Knowledge Manager Publishes Article

| Field | Value |
|---|---|
| **Use Case ID** | UC-009 |
| **Name** | Knowledge Manager Publishes Article |
| **Primary Actor** | Knowledge Manager |
| **Secondary Actors** | Author Agent, Review Team, Publication System, Search Engine |

### Preconditions
1. A draft article exists in `DRAFT` status, written by an agent or knowledge manager.
2. At least one reviewer is designated for the article category.

### Postconditions (Success)
1. Article transitions to `PUBLISHED` status and is indexed by the search engine.
2. A publication notification is sent to subscribed agents.
3. The article is visible in the customer-facing knowledge base (if marked `PUBLIC`).

### Main Success Scenario

| Step | Actor | Action |
|---|---|---|
| 1 | Knowledge Manager | Opens the article in the Knowledge Management console. |
| 2 | Knowledge Manager | Reviews content, metadata (tags, category, SEO slug), and audience (internal/public). |
| 3 | Knowledge Manager | Assigns the article to one or more reviewers. |
| 4 | Reviewer | Receives notification; reviews the article draft; adds inline comments if needed. |
| 5 | Reviewer | Approves the draft; status transitions to `APPROVED` (BR-012). |
| 6 | Knowledge Manager | Clicks "Publish"; optionally sets a scheduled publish date. |
| 7 | Publication System | Transitions article to `PUBLISHED`; assigns `published_at` timestamp and version number. |
| 8 | Search Engine | Re-indexes the new article within the configured indexing interval (≤ 5 minutes). |
| 9 | Notification Service | Sends "New article available" digest to subscribed internal agents. |

### Exception Flows

**EF-009A — Reviewer Rejects Article**
- Reviewer adds required changes and sets status to `NEEDS_REVISION`.
- Author is notified with inline comments; article returns to `DRAFT`.
- Article cannot be published until re-approved (BR-012).

---

## UC-010: Workforce Manager Creates Agent Schedule

| Field | Value |
|---|---|
| **Use Case ID** | UC-010 |
| **Name** | Workforce Manager Creates Agent Schedule |
| **Primary Actor** | Workforce Manager |
| **Secondary Actors** | Forecasting Service, Agent, Notification Service |

### Preconditions
1. Forecasted contact volume data is available for the target scheduling period.
2. Agent profiles, skills, and contracted hours are loaded in the WFM module.

### Postconditions (Success)
1. Published schedule covers all required shifts with sufficient staffing levels.
2. Agents receive shift notifications via email and in-app.
3. Schedule is locked for the period and visible to supervisors.

### Main Success Scenario

| Step | Actor | Action |
|---|---|---|
| 1 | Workforce Manager | Opens the Scheduling Workbench; selects the target week. |
| 2 | Forecasting Service | Loads predicted hourly contact volume per queue for the target week. |
| 3 | Workforce Manager | Reviews staffing recommendations generated by the Erlang-C staffing calculator. |
| 4 | Workforce Manager | Drags agents into time slots; reviews coverage heatmap for understaffed periods. |
| 5 | Workforce Manager | Assigns break windows and ensures compliance with labor rules (max consecutive hours). |
| 6 | Workforce Manager | Clicks "Publish Schedule". |
| 7 | Notification Service | Sends shift confirmation emails to all scheduled agents. |
| 8 | Adherence Monitor | Begins tracking clock-in/clock-out events against the published schedule. |

---

## UC-011: Agent Merges Duplicate Tickets

| Field | Value |
|---|---|
| **Use Case ID** | UC-011 |
| **Name** | Agent Merges Duplicate Tickets |
| **Primary Actor** | Support Agent |
| **Secondary Actors** | Ticket Service, Contact Service, SLA Monitor |

### Preconditions
1. Agent has access to at least two tickets believed to be duplicates from the same contact.
2. Both tickets are in `OPEN` or `ASSIGNED` status.

### Postconditions (Success)
1. One ticket is designated as canonical (BR-011); the other is marked `MERGED`.
2. All communications from the merged ticket are transferred to the canonical ticket.
3. Contacts and watchers from both tickets are unified.

### Main Success Scenario

| Step | Actor | Action |
|---|---|---|
| 1 | Agent | Identifies Ticket #1021 and Ticket #1034 as duplicates (same issue, same customer). |
| 2 | Agent | Opens the Merge dialog; selects the canonical ticket (#1021) and the duplicate (#1034). |
| 3 | Ticket Service | Validates both tickets belong to the same contact (BR-001). |
| 4 | Ticket Service | Copies all message threads and attachments from #1034 into #1021 with a merge timestamp. |
| 5 | Ticket Service | Marks #1034 as `MERGED` with `merged_into_ticket_id = 1021`. |
| 6 | SLA Monitor | Adopts the SLA policy with the earliest `first_response_due_at` between the two tickets. |
| 7 | System | Sends notifications to all watchers of both tickets pointing them to #1021. |

### Exception Flows

**EF-011A — Cross-Contact Merge Blocked**
- Tickets belong to different contacts.
- Merge is blocked; agent is prompted to confirm the contact association before proceeding.

---

## UC-012: Customer Submits GDPR Data Deletion Request

| Field | Value |
|---|---|
| **Use Case ID** | UC-012 |
| **Name** | Customer Submits GDPR Data Deletion Request |
| **Primary Actor** | Customer |
| **Secondary Actors** | Privacy Portal, Compliance Service, Administrator, Data Retention Service, Notification Service |

### Preconditions
1. Customer is authenticated (or has verified identity via the privacy portal).
2. The customer's data exists in the platform.

### Postconditions (Success)
1. A GDPR deletion request record is created with a 30-day completion deadline (BR-010).
2. All personal data (contact record, ticket content, call recordings, chat transcripts) is scheduled for deletion or anonymization.
3. Customer receives written confirmation of deletion or a formal rejection with legal basis.

### Main Success Scenario

| Step | Actor | Action |
|---|---|---|
| 1 | Customer | Navigates to the Privacy Portal; selects "Request Deletion of My Data"; authenticates. |
| 2 | Privacy Portal | Creates a `GDPRRequest` record: `type=DELETION`, `status=PENDING`, `deadline = now + 30 days`. |
| 3 | Notification Service | Acknowledges receipt to the customer with request reference ID and deadline. |
| 4 | Administrator | Reviews the request; checks for active legal hold or legitimate interest exceptions. |
| 5 | Administrator | No exceptions apply; approves the deletion request. |
| 6 | Compliance Service | Searches all data stores for records linked to the contact: tickets, transcripts, recordings, PII fields. |
| 7 | Data Retention Service | Anonymizes or hard-deletes PII per the tenant's retention policy; preserves anonymized aggregate analytics records. |
| 8 | Compliance Service | Updates `GDPRRequest` to `COMPLETED`; records a hash-signed deletion receipt. |
| 9 | Notification Service | Sends deletion confirmation to the customer with the signed receipt. |

### Alternative Flows

**AF-012A — Legal Hold Exception**
- At step 4, active litigation hold applies to the customer's records.
- Administrator rejects the deletion request with reason `LEGAL_HOLD`.
- Customer is notified of the rejection with legal basis cited.

### Exception Flows

**EF-012A — Deadline Approaching — Not Acted**
- With 7 days until the 30-day deadline, if request is still in `PENDING`, an automated reminder is sent to the Administrator.
- With 2 days remaining, a severity-1 escalation alert is sent to the DPO (Data Protection Officer).

**EF-012B — Data Store Inaccessible During Deletion**
- If a downstream data store is unavailable during deletion at step 7, the partial deletion is logged.
- A retry job is scheduled; the `GDPRRequest` remains `IN_PROGRESS` until all stores confirm deletion.
- An alert is sent to the platform ops team.
