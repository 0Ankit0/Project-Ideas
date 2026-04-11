# System Sequence Diagrams

> **Scope**: System-level sequence diagrams (SSDs) treat the Customer Support and Contact Center Platform as a single black box. They capture the messages exchanged between external actors and the system boundary, and between the system and other external systems. Internal service choreography is intentionally hidden here; see `detailed-design/sequence-diagrams.md` for service-level detail.
>
> These diagrams follow the *system sequence diagram* convention from Larman's *Applying UML and Patterns*: only the system boundary participates as a lifeline, not individual internal services.

---

## Summary of System Interactions

| SSD ID | Title | Primary Actor | External Systems | Trigger |
|--------|-------|---------------|------------------|---------|
| SSD-001 | New Ticket via Email | Customer | Email Provider | Inbound email to support address |
| SSD-002 | Live Chat with Bot Escalation | Customer | Chat Widget | Widget opened on web/mobile |
| SSD-003 | Voice Call via IVR | Customer | Telephony / IVR | Inbound PSTN call |
| SSD-004 | SLA Breach Notification | Support Platform | Notification Gateway, Supervisor | SLA deadline crossed |
| SSD-005 | Real-Time Dashboard Update | Support Platform | Supervisor Dashboard | Continuous metric emission |
| SSD-006 | CSAT Survey via Email | Support Platform | Customer, Email Provider | Ticket resolved |
| SSD-007 | CRM Integration Sync | Support Platform | CRM System | Ticket creation, resolution, nightly sync |

---

## SSD-001: New Ticket via Email

### Description

A customer sends an email to the monitored support inbox (e.g., `support@company.com`). The Email Provider (SendGrid Inbound Parse, Gmail API, or Microsoft 365 webhook) parses the MIME message and forwards it to the platform via an inbound webhook. The platform deduplicates the thread using `Message-ID` and `References` headers, creates or updates a ticket, routes it to an agent, and sends a confirmation to the customer and a notification to the assigned agent.

### Participants

| Lifeline | Type | Description |
|----------|------|-------------|
| Customer | External Actor | End user sending the email |
| Email Provider | External System | Inbound mail relay (SendGrid, Gmail, Microsoft 365) |
| Support Platform | System Under Design | Black-box boundary |
| Agent | External Actor | Support agent assigned to the ticket |

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    participant EmailProvider as Email Provider
    participant Platform as Support Platform
    actor Agent

    Customer->>EmailProvider: Sends email to support@company.com
    EmailProvider->>Platform: POST /webhooks/email/inbound (MIME payload, Message-ID, References, attachments)
    Platform-->>EmailProvider: HTTP 200 OK (ingestion acknowledged)
    Note over Platform: Parses MIME body and attachments.<br/>Deduplicates thread via Message-ID + References.<br/>Creates TKT-00123, classifies category and priority.<br/>Runs routing engine, assigns to agent AGT-07.<br/>SLA clock started.
    Platform->>Customer: Outbound email: "Your request has been received (Ticket #TKT-00123). We will respond within 4 hours."
    Platform->>Agent: Push notification + email: "New ticket TKT-00123 assigned — Subject: VPN issue, Priority: HIGH"
    Agent->>Platform: GET /v1/tickets/TKT-00123 (opens ticket in agent desktop)
    Platform-->>Agent: Ticket payload (subject, body, attachments, customer 360 profile, suggested KB articles, SLA deadline)
    Agent->>Platform: POST /v1/tickets/TKT-00123/messages (sends reply to customer)
    Platform-->>Agent: Message created (first-response SLA clock stopped)
    Platform->>Customer: Reply email forwarded via Email Provider (Thread maintained via Re: subject + References header)
```

### Key System Messages

| # | From | To | Message | Data Carried |
|---|------|----|---------|--------------|
| 1 | Customer | Email Provider | Email send | MIME message |
| 2 | Email Provider | Platform | Inbound webhook | MIME payload, headers, attachment URLs |
| 3 | Platform | Email Provider | Acknowledgement | HTTP 200 |
| 4 | Platform | Customer | Auto-acknowledgement email | Ticket number, estimated response time |
| 5 | Platform | Agent | Assignment notification | Ticket ID, customer name, subject, priority |
| 6 | Agent | Platform | Ticket fetch (GET) | ticket_id |
| 7 | Agent | Platform | Send reply (POST) | Message body |
| 8 | Platform | Customer | Agent reply email | Reply content (threaded) |

---

## SSD-002: Live Chat to Ticket with Bot Escalation

### Description

A customer initiates a live chat session via the embedded JavaScript widget on the company website or portal. The platform's Bot Engine handles the conversation first, performing NLP intent classification and Knowledge Base lookups to attempt self-service resolution. If the bot cannot resolve after a configured number of turns, or the customer explicitly requests a human agent, the system escalates: a ticket is created with the full bot transcript attached, and the conversation is routed to an available agent via the skill-based routing engine. A CSAT rating prompt is shown at session end.

### Participants

| Lifeline | Type | Description |
|----------|------|-------------|
| Customer | External Actor | Website or portal visitor |
| Chat Widget | External Component | Embedded JS SDK on customer's web property |
| Support Platform | System Under Design | Black-box boundary |
| Agent | External Actor | Human agent accepting the escalated chat |

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    participant Widget as Chat Widget
    participant Platform as Support Platform
    actor Agent

    Customer->>Widget: Opens chat widget, clicks "Start Chat"
    Widget->>Platform: WebSocket CONNECT /ws/chat + session_init {visitor_id, page_url, locale, user_agent}
    Platform-->>Widget: session_created {session_id, bot_greeting: "Hi! How can I help you today?"}
    Widget-->>Customer: Bot greeting displayed

    Customer->>Widget: Types "I was charged twice for my order"
    Widget->>Platform: message {session_id, text: "I was charged twice for my order"}
    Note over Platform: NLP: intent=billing_duplicate_charge,<br/>entity={order: null}, confidence=0.87.<br/>Bot selects clarification flow.
    Platform-->>Widget: Bot: "I'm sorry to hear that. Can you share your order number?"
    Widget-->>Customer: Bot message displayed

    Customer->>Widget: "My order is #ORD-45678"
    Widget->>Platform: message {session_id, text: "#ORD-45678"}
    Note over Platform: Entity extracted: order_id=ORD-45678.<br/>KB article found: "Duplicate charge resolution steps".<br/>Self-service resolution offered.
    Platform-->>Widget: Bot: "Here are the steps to resolve a duplicate charge: [KB article]. Would this solve your issue?"
    Widget-->>Customer: KB article and resolution steps displayed

    Customer->>Widget: "This didn't help. I want to speak with a person."
    Widget->>Platform: message {session_id, text: "...", escalation_signal: true}
    Note over Platform: Escalation triggered. Bot session paused.<br/>Ticket TKT-00456 created (bot transcript attached).<br/>Routing engine: channel=CHAT, queue=billing, skill=billing_refunds.<br/>Agent AGT-03 selected (available, skill match: 100%).
    Platform-->>Widget: status_update {type: "ESCALATING", message: "Connecting you to a billing specialist. Estimated wait: ~3 minutes."}
    Widget-->>Customer: "Connecting you to an agent..." (animated waiting indicator)

    Platform->>Agent: chat_assignment_alert {ticket_id: "TKT-00456", transcript_preview, customer_name: "Jane", intent: "billing_duplicate_charge"}
    Agent->>Platform: POST /v1/tickets/TKT-00456/accept
    Platform-->>Widget: agent_joined {agent_name: "Sarah", agent_avatar_url, intro_message: "Hi Jane, I'm Sarah. I can see you were charged twice for order ORD-45678."}
    Widget-->>Customer: "Sarah has joined the conversation"

    Customer->>Widget: "Yes, my bank shows two charges of $49.99"
    Widget->>Platform: message (forwarded in real-time to agent)
    Agent->>Platform: POST /v1/tickets/TKT-00456/messages {text: "I've confirmed the duplicate charge and have initiated a refund. It will appear in 3–5 business days."}
    Platform-->>Widget: Agent message delivered to customer

    Agent->>Platform: POST /v1/tickets/TKT-00456/resolve {resolution_code: "REFUND_INITIATED", notes: "Duplicate charge confirmed, refund processed"}
    Platform-->>Widget: session_ended {csat_prompt: true, agent_name: "Sarah"}
    Widget-->>Customer: "Sarah has ended the chat. How did we do?" (1–5 star CSAT prompt)
    Customer->>Widget: Selects 5 stars
    Widget->>Platform: POST /v1/surveys/csat {session_id, ticket_id: "TKT-00456", rating: 5}
    Platform-->>Widget: survey_received {message: "Thank you for your feedback!"}
```

### Key System Messages

| # | From | To | Message | Data Carried |
|---|------|----|---------|--------------|
| 1–2 | Customer / Widget | Platform | WebSocket connect + session init | visitor_id, page context, locale |
| 3–8 | Platform ↔ Widget ↔ Customer | — | Bot conversation turns | Intents, entities, KB articles, bot replies |
| 9 | Widget | Platform | Escalation signal | Session ID, escalation flag |
| 10 | Platform | Widget | Escalating status + wait time | Estimated wait |
| 11 | Platform | Agent | Chat assignment alert | Ticket ID, transcript preview, intent |
| 12 | Agent | Platform | Accept assignment | ticket_id |
| 13 | Platform | Widget | Agent joined event | Agent name, intro message |
| 14 | Agent | Platform | Resolve ticket | Resolution code, notes |
| 15 | Platform | Widget | Session ended + CSAT | CSAT prompt flag |
| 16 | Widget | Platform | CSAT submission | Rating (1–5), ticket_id |

---

## SSD-003: Voice Call to Ticket via IVR

### Description

A customer calls the support hotline. The Telephony/IVR system (Twilio, Genesys, or Avaya) plays a menu tree and collects DTMF input. On menu selection, the IVR fires a webhook to the platform. The platform looks up the caller by ANI (Automatic Number Identification / caller ID), determines routing priority, creates a pre-ticket, and instructs the IVR to connect to the appropriate agent queue. A screen-pop delivers customer context to the agent at answer time. The call is recorded throughout; after it ends, a transcript is generated via ASR and attached to the ticket, and a post-call SMS survey is dispatched.

### Participants

| Lifeline | Type | Description |
|----------|------|-------------|
| Customer | External Actor | Caller on a phone (PSTN or VoIP) |
| Telephony / IVR | External System | PSTN gateway + IVR menu (Twilio, Genesys, Avaya) |
| Support Platform | System Under Design | Black-box boundary |
| Agent | External Actor | Support agent answering the call |

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    participant IVR as Telephony / IVR
    participant Platform as Support Platform
    actor Agent

    Customer->>IVR: Dials +1-800-XXX-XXXX
    IVR-->>Customer: "Welcome to Acme Support. Press 1 for Billing, 2 for Technical Support, 3 for Account Management, or stay on the line for more options."
    Customer->>IVR: DTMF input: presses 2 (Technical Support)
    IVR->>Platform: Webhook POST /webhooks/telephony/ivr-selection {call_sid, ani: "+15551234567", dnis: "+18001234567", menu_selection: "2", ivr_path: "main>tech_support", timestamp}
    Note over Platform: ANI lookup: contact found — Jane Doe, Account: Acme Corp (Enterprise).<br/>Open tickets: 0. Account tier: Enterprise → priority HIGH.<br/>Routing: queue=tech_support_en, skill=networking, language=en.<br/>Pre-ticket TKT-00789 created (status: ACTIVE_CALL).
    Platform-->>IVR: Routing instruction {action: "ENQUEUE", queue: "tech_support_en", skill: "networking", estimated_wait_sec: 120, screen_pop_url: "/screenpop/TKT-00789"}
    IVR-->>Customer: "Please hold. Your estimated wait time is 2 minutes. Your call is important to us."
    IVR->>Agent: Incoming call ring + screen-pop notification (customer name, account, open tickets, last interaction)
    Agent->>IVR: Answers call (picks up headset)
    IVR->>Platform: Webhook POST /webhooks/telephony/call-answered {call_sid, agent_extension: "ext-302", answered_at, queue_wait_sec: 94}
    Platform-->>IVR: HTTP 200 (acknowledged and call recording instruction: start)
    IVR-->>Customer: Connected to agent
    Note over Platform: Call recording active (dual-channel: customer + agent).<br/>Real-time ASR transcript stream begins.<br/>TKT-00789 status: IN_PROGRESS.

    Customer->>Agent: Describes networking issue over voice
    Agent->>Platform: POST /v1/tickets/TKT-00789/notes {content: "Customer reports dropped VPN connections after firmware update v3.1.2. Last occurrence: this morning 09:15 EST."} (live note-taking during call)
    Platform-->>Agent: Note saved (HTTP 201)

    Agent->>IVR: Ends call (hangs up headset)
    IVR->>Platform: Webhook POST /webhooks/telephony/call-ended {call_sid, duration_sec: 487, recording_url: "https://recordings.provider.com/abc123.mp3", end_reason: "agent_hangup", talk_time_sec: 412, hold_time_sec: 75}
    Note over Platform: Recording downloaded and stored in Object Storage (S3).<br/>ASR transcript job queued (async, ~60–90s processing).<br/>TKT-00789 updated: status=PENDING_FOLLOWUP, duration=487s, recording_url stored.
    Platform->>Customer: SMS to +15551234567: "Thanks for calling Acme Support! Rate your experience: https://survey.acme.com/s/TKT-00789"

    Note over Agent: Wrap-up screen displayed (120-second countdown timer)
    Agent->>Platform: POST /v1/tickets/TKT-00789/wrap-up {disposition_code: "TECHNICAL_ESCALATED", wrap_notes: "Escalating to network engineering team for firmware investigation", after_call_work_sec: 95}
    Platform-->>Agent: Wrap-up accepted. Agent status reset to AVAILABLE. Concurrent ticket count decremented.
```

### Key System Messages

| # | From | To | Message | Data Carried |
|---|------|----|---------|--------------|
| 1 | Customer | Telephony/IVR | PSTN call | ANI, DNIS |
| 2–3 | IVR ↔ Customer | — | IVR menu interaction | DTMF input |
| 4 | Telephony/IVR | Platform | IVR selection webhook | Call SID, ANI, menu selection |
| 5 | Platform | Telephony/IVR | Routing instruction | Queue name, skill, estimated wait |
| 6 | Telephony/IVR | Agent | Incoming call + screen-pop | Customer name, ticket pre-data |
| 7 | Telephony/IVR | Platform | Call answered webhook | Agent extension, queue wait time |
| 8 | Telephony/IVR | Platform | Call ended webhook | Duration, recording URL, end reason |
| 9 | Platform | Customer | Post-call SMS survey | Survey URL |
| 10 | Agent | Platform | Wrap-up submission | Disposition code, notes, ACW duration |

---

## SSD-004: SLA Breach Notification

### Description

The platform's SLA monitor runs on a scheduled evaluation cycle (every 60 seconds). When a ticket's first-response or resolution deadline crosses a configurable warning threshold (default: 25% of total SLA window remaining), the platform dispatches proactive alerts to the responsible supervisor. When the actual deadline is missed (breach), it emits a breach event, dispatches urgent notifications, and auto-escalates the ticket to a higher-tier queue. All breach events are written to the SLA audit log for reporting.

### Participants

| Lifeline | Type | Description |
|----------|------|-------------|
| Support Platform | System Under Design | Detects and emits SLA events |
| Notification Gateway | External System | Email / SMS / push delivery service |
| Supervisor | External Actor | Receives alerts and takes remedial action |

```mermaid
sequenceDiagram
    autonumber
    participant Platform as Support Platform
    participant NotifGateway as Notification Gateway
    actor Supervisor

    Note over Platform: SLA monitor cycle (every 60 seconds).<br/>TKT-00321 (Enterprise SLA: 4h resolution):<br/>resolution_deadline = now + 18 min.<br/>Warning threshold = 20 min → threshold crossed.
    Platform->>NotifGateway: Dispatch SLA warning alert {channel: [push, email], recipient: supervisor_id, ticket_id: "TKT-00321", agent: "Alex B.", queue: "enterprise_support", time_remaining_min: 18, action_url: "/supervisor/tickets/TKT-00321"}
    NotifGateway->>Supervisor: 🟡 Push notification: "⚠ SLA Warning: TKT-00321 — Resolution deadline in 18 min (Agent: Alex B.)"
    NotifGateway->>Supervisor: Email: SLA warning with full ticket context, one-click escalate button

    Supervisor->>Platform: GET /v1/supervisor/sla/at-risk?queue=enterprise_support (views at-risk panel)
    Platform-->>Supervisor: [{ticket_id, subject, agent, queue, time_remaining_min, customer_name, customer_tier}] (sorted ascending by time_remaining)

    Supervisor->>Platform: POST /v1/tickets/TKT-00321/escalate {reason: "SLA risk, agent approaching deadline", target_tier: 2, notify_agent: true}
    Platform-->>Supervisor: {escalation_id: "ESC-0044", new_queue: "enterprise_support_tier2", status: "ESCALATED", agent_notified: true}

    Note over Platform: 18 minutes pass — ticket remains open. Deadline reached (14:47 UTC).<br/>SLA breach event emitted to Kafka topic: sla.breach.<br/>Breach: {ticket_id=TKT-00321, type=RESOLUTION, policy=enterprise_4h, overdue_min=0}.
    Platform->>NotifGateway: Dispatch SLA breach alert {severity: CRITICAL, channel: [sms, push, email], recipient: supervisor_id, ticket_id: "TKT-00321", breach_type: "RESOLUTION_DEADLINE", sla_policy: "enterprise_4h", customer: "Acme Corp", customer_tier: "Enterprise"}
    NotifGateway->>Supervisor: 🔴 SMS: "SLA BREACH: TKT-00321 — Resolution deadline missed. Acme Corp (Enterprise). Escalated to Tier-2."
    NotifGateway->>Supervisor: Push: urgent banner notification (red)

    Platform->>NotifGateway: Notify team lead for agent Alex B. (separate alert)
    NotifGateway->>Supervisor: Email to team lead: "Auto-escalated TKT-00321 to Tier-2. Breach logged. Please review agent workload."

    Note over Platform: Auto-escalation completed: TKT-00321 moved to enterprise_support_tier2 queue.<br/>Breach event written to SLA audit log.<br/>Breach counter incremented in real-time analytics (breach_count_today += 1).
```

---

## SSD-005: Real-Time Dashboard Update

### Description

The Supervisor Dashboard establishes a persistent WebSocket connection on load, receiving a full state snapshot immediately and then receiving incremental delta events for every ticket state change, agent status change, and metric update thereafter. This eliminates the need for polling and enables sub-second latency dashboard updates. Data is scoped to the supervisor's authorized queues and tenant.

### Participants

| Lifeline | Type | Description |
|----------|------|-------------|
| Support Platform | System Under Design | Emits real-time metric and event streams |
| Supervisor Dashboard | External System (SPA) | React SPA consuming WebSocket stream |
| Supervisor | External Actor | Views and acts on live dashboard data |

```mermaid
sequenceDiagram
    autonumber
    actor Supervisor
    participant Dashboard as Supervisor Dashboard
    participant Platform as Support Platform

    Supervisor->>Dashboard: Opens browser — navigates to /supervisor/dashboard
    Dashboard->>Platform: WebSocket CONNECT wss://api.company.com/ws/v1/supervisor/stream?tenant=acme&scope=all_queues (JWT in Authorization header)
    Platform-->>Dashboard: connection_ack + full_snapshot {queue_metrics: {depth: 12, avg_wait_sec: 142}, agent_states: [...], sla_health: {at_risk: 2, breached_today: 0}, open_ticket_count: 47, ticket_velocity_per_hour: 18}
    Dashboard-->>Supervisor: Dashboard fully rendered with initial data

    loop Metric heartbeat every 5 seconds
        Platform->>Dashboard: metrics_delta {queue_depth: 14, agents_available: 8, agents_busy: 7, agents_on_break: 2, breach_risk_count: 2, avg_wait_time_sec: 156, oldest_ticket_age_min: 87}
        Dashboard-->>Supervisor: Live counters updated (queue depth, availability gauge, SLA risk badge)
    end

    Note over Platform: New ticket TKT-00991 ingested via email channel (14:52 UTC)
    Platform->>Dashboard: ticket_event {type: "CREATED", ticket_id: "TKT-00991", channel: "EMAIL", priority: "HIGH", queue: "billing", subject: "Duplicate invoice", created_at}
    Dashboard-->>Supervisor: Queue panel: queue depth +1. New row appears in live ticket feed with HIGH priority badge.

    Note over Platform: TKT-00991 assigned to agent AGT-04 (14:52:03 UTC)
    Platform->>Dashboard: ticket_event {type: "ASSIGNED", ticket_id: "TKT-00991", agent_id: "AGT-04", agent_name: "Maria K.", assigned_at, time_to_assign_sec: 3}
    Dashboard-->>Supervisor: Agent AGT-04 card: active ticket counter increments. Queue depth decrements.

    Note over Platform: Agent AGT-11 manually changes status from ONLINE → BREAK
    Platform->>Dashboard: agent_event {type: "STATUS_CHANGE", agent_id: "AGT-11", agent_name: "Tom R.", old_status: "ONLINE", new_status: "BREAK", timestamp, scheduled_break: true}
    Dashboard-->>Supervisor: Agent grid: AGT-11 indicator turns yellow. Available agent count decrements.

    Note over Platform: SLA breach detected on TKT-00321 (from SSD-004)
    Platform->>Dashboard: sla_event {type: "BREACH", ticket_id: "TKT-00321", severity: "CRITICAL", breach_type: "RESOLUTION", customer: "Acme Corp", agent: "Alex B.", overdue_min: 0}
    Dashboard-->>Supervisor: Red alert banner at top of dashboard. SLA health widget: breach count +1. TKT-00321 row highlighted in red in at-risk table.
```

---

## SSD-006: CSAT Survey via Email

### Description

After a ticket is resolved, the platform schedules a CSAT (Customer Satisfaction) survey with a configurable post-resolution delay (default: 60 minutes, ensuring customer has time to verify resolution). The survey email contains signed JWT tokens embedded in one-click star-rating hyperlinks (1–5), enabling frictionless single-click response capture. Optional free-text follow-up is available on the thank-you page. Separately, the platform evaluates NPS (Net Promoter Score) eligibility (last NPS > 30 days ago) and dispatches an NPS survey as appropriate.

### Participants

| Lifeline | Type | Description |
|----------|------|-------------|
| Support Platform | System Under Design | Schedules, dispatches, and captures surveys |
| Email Provider | External System | Email delivery (SendGrid, Postmark) |
| Customer | External Actor | Receives survey email and submits rating |

```mermaid
sequenceDiagram
    autonumber
    participant Platform as Support Platform
    participant EmailProvider as Email Provider
    actor Customer

    Note over Platform: TKT-00789 resolved at 14:00 UTC.<br/>CSAT survey scheduled: dispatch_at = 15:00 UTC (1-hour delay).<br/>Survey suppression check: no previous open survey for this customer.

    Note over Platform: 15:00 UTC — Survey dispatch job fires.<br/>JWT token generated: {sub: survey_id, ticket_id, agent_id, customer_email, exp: +48h, iat}.<br/>Signed with HS256 + survey secret.
    Platform->>EmailProvider: POST /send {to: "jane@acme.com", from: "support@company.com", reply_to: "noreply@company.com", template_id: "csat_one_click", vars: {agent_name: "James", ticket_subject: "VPN connectivity issue", ticket_id: "TKT-00789", rating_links: {1: "/csat/respond?t=<JWT>&r=1", ..., 5: "/csat/respond?t=<JWT>&r=5"}}}
    EmailProvider->>Customer: Email delivered: "How did James do? Rate your recent support experience." (1–5 star buttons, each a hyperlink)

    Customer->>Platform: GET /v1/surveys/csat/respond?token=<JWT>&rating=4 (customer clicks 4-star link)
    Note over Platform: JWT validated: not expired, not already used (idempotency key checked).<br/>Response recorded: {survey_id, ticket_id=TKT-00789, agent_id=AGT-07,<br/>channel=EMAIL, rating=4, responded_at=15:42 UTC, response_latency_h=0.7}.
    Platform-->>Customer: HTTP 302 → /surveys/thank-you?message=Thank+you+for+your+feedback%21+Your+rating+helps+us+improve.

    alt Customer clicks "Add a comment" on the thank-you page
        Customer->>Platform: POST /v1/surveys/csat/comment {token: <JWT>, comment: "James was very helpful but it took a while to get connected."}
        Platform-->>Customer: HTTP 200 {message: "Your comment has been recorded. Thank you!"}
        Note over Platform: Comment stored on survey record. Async sentiment analysis job queued.
    end

    Note over Platform: Agent AGT-07 rolling CSAT recalculated (last 90 days, min 5 responses).<br/>Ticket TKT-00789: csat_score=4 persisted.<br/>Team CSAT metric updated in analytics read model.

    Note over Platform: NPS eligibility check for jane@acme.com:<br/>last_nps_survey = 52 days ago > 30-day threshold → eligible.
    Platform->>EmailProvider: POST /send {to: "jane@acme.com", template_id: "nps_relationship", vars: {nps_token: <NPS_JWT>, company_name: "Acme Corp", scale: "0-10", expires_in: "7 days"}}
    EmailProvider->>Customer: NPS email: "How likely are you to recommend Company X to a colleague? (0–10)"
    Customer->>Platform: GET /v1/surveys/nps/respond?token=<NPS_JWT>&score=8
    Platform-->>Customer: HTTP 302 → NPS thank-you page
    Note over Platform: NPS response recorded. Score=8 → category=PASSIVE (Promoter≥9, Passive=7–8, Detractor≤6).<br/>NPS score recalculated: ((promoters - detractors) / total_respondents) × 100.
```

---

## SSD-007: CRM Integration Sync

### Description

The platform integrates bidirectionally with a CRM system (Salesforce, HubSpot, or Microsoft Dynamics). Contacts are enriched in real time at ticket creation via CRM REST API lookup. Resolved tickets are pushed back as CRM case records for account managers' visibility. When contact or account data changes in the CRM (tier upgrades, ownership changes), a CRM-fired webhook triggers contact updates and may re-prioritize open tickets. A nightly batch sync provides consistency recovery for any missed real-time updates.

### Participants

| Lifeline | Type | Description |
|----------|------|-------------|
| Support Platform | System Under Design | Initiates lookups, processes webhooks, pushes case data |
| CRM System | External System | Salesforce / HubSpot / Dynamics — source of truth for contacts and accounts |

```mermaid
sequenceDiagram
    autonumber
    participant Platform as Support Platform
    participant CRM as CRM System

    Note over Platform: Ticket TKT-01100 created (email channel, contact: jane@acme.com).<br/>Real-time CRM enrichment initiated.
    Platform->>CRM: GET /api/v1/contacts?email=jane@acme.com&fields=crm_id,account_id,account_tier,account_owner,open_cases,last_interaction (REST, API key auth)
    CRM-->>Platform: {crm_contact_id: "CRM-C-9988", account_id: "ACC-1122", account_tier: "Enterprise", account_owner: "Mike Sales", open_cases: 2, last_interaction: "2024-01-10", custom_fields: {priority_support: true}}
    Note over Platform: TKT-01100 enriched: priority→HIGH (Enterprise tier, priority_support=true).<br/>crm_contact_id and account_id stored on ticket.<br/>Routing queue overridden: enterprise_priority queue.

    Note over Platform: TKT-01100 resolved at 16:30 UTC. CRM case sync triggered.
    Platform->>CRM: POST /api/v1/cases {external_ticket_id: "TKT-01100", crm_contact_id: "CRM-C-9988", subject: "VPN connectivity issue", channel: "PHONE", category: "TECHNICAL", resolution_summary: "Escalated to network engineering", resolved_at: "2024-01-16T16:30:00Z", handle_time_min: 8, csat_score: 4, agent_name: "James", escalated: true}
    CRM-->>Platform: {crm_case_id: "CS-112233", status: "closed", synced_at}
    Note over Platform: crm_case_id=CS-112233 stored on TKT-01100 for bidirectional traceability.

    Note over CRM: Account manager upgrades Acme Corp from "Enterprise" → "VIP" in CRM
    CRM->>Platform: Webhook POST /v1/webhooks/crm/contact-updated {hmac_signature, crm_contact_id: "CRM-C-9988", changed_fields: {account_tier: {old: "Enterprise", new: "VIP"}}, updated_by: "mike.sales@company.com", updated_at}
    Platform-->>CRM: HTTP 200 OK (webhook acknowledged within 200ms)
    Note over Platform: Contact record updated: account_tier=VIP.<br/>Open tickets for crm_contact_id=CRM-C-9988 re-evaluated.<br/>TKT-01200 (open, current priority=HIGH) → priority escalated to CRITICAL.<br/>Routing engine: TKT-01200 moved to vip_priority queue.

    Note over Platform: Nightly batch sync — 02:00 UTC
    Platform->>CRM: GET /api/v1/contacts?updated_since=2024-01-16T00:00:00Z&limit=500&cursor=null (paginated full sync)
    CRM-->>Platform: Page 1: 500 contact records + next_cursor: "eyJpZCI6IjUwMCJ9"
    Platform->>CRM: GET /api/v1/contacts?updated_since=2024-01-16T00:00:00Z&limit=500&cursor=eyJpZCI6IjUwMCJ9
    CRM-->>Platform: Page 2: 312 contact records + next_cursor: null (last page)
    Note over Platform: 812 contacts upserted into Contact DB (ON CONFLICT DO UPDATE).<br/>Elasticsearch index refreshed for updated contacts.<br/>Sync audit log: {sync_id, type=NIGHTLY_BATCH, started_at, completed_at, records_processed: 812, errors: 0, duration_sec: 47}.
```

---

## System Interaction Summary Table

The following table provides a consolidated reference for all external system interactions defined in the SSDs above.

| Interaction | SSD | Direction | Protocol / Transport | Trigger | Primary Data |
|-------------|-----|-----------|---------------------|---------|--------------|
| Inbound email webhook | SSD-001 | Email Provider → Platform | HTTP POST (Webhook) | New email received | MIME payload, headers, attachments |
| Outbound acknowledgement email | SSD-001 | Platform → Customer | SMTP via Email Provider | Ticket created | Ticket number, ERT |
| Agent assignment notification | SSD-001 | Platform → Agent | Push + Email | Ticket assigned | Ticket ID, subject, priority |
| Chat WebSocket session init | SSD-002 | Customer ↔ Platform | WebSocket (WSS) | Widget opened | visitor_id, page context, locale |
| Bot conversation turns | SSD-002 | Platform ↔ Widget | WebSocket messages | Each customer message | Intent, KB results, bot replies |
| Escalation signal | SSD-002 | Widget → Platform | WebSocket message | Customer requests human | Session ID, escalation flag |
| Chat assignment notification | SSD-002 | Platform → Agent | Push | Ticket routed to agent | Ticket ID, transcript preview |
| Post-chat CSAT prompt | SSD-002 | Platform → Widget | WebSocket message | Session ended | CSAT flag, agent name |
| IVR call selection webhook | SSD-003 | Telephony → Platform | HTTP POST (Webhook) | Menu DTMF selection | Call SID, ANI, menu choice, IVR path |
| IVR routing instruction | SSD-003 | Platform → Telephony | HTTP response | IVR webhook received | Queue name, estimated wait, screen-pop URL |
| Call answered webhook | SSD-003 | Telephony → Platform | HTTP POST (Webhook) | Agent answers | Call SID, agent extension, queue wait |
| Call ended webhook | SSD-003 | Telephony → Platform | HTTP POST (Webhook) | Call disconnected | Duration, recording URL, end reason |
| Post-call SMS survey | SSD-003 | Platform → Customer | SMS via SMS Gateway | Call ended + wrap-up | Survey URL with signed token |
| SLA warning alert | SSD-004 | Platform → Supervisor | Push + Email | Warning threshold crossed | Ticket ID, time remaining |
| SLA breach alert | SSD-004 | Platform → Supervisor | SMS + Push + Email | Deadline missed | Ticket ID, breach type, severity, customer |
| Dashboard WebSocket stream | SSD-005 | Platform → Dashboard | WebSocket (WSS) | Connection established + continuous | Full snapshot, then metric/event deltas |
| CSAT survey email | SSD-006 | Platform → Customer | SMTP via Email Provider | 60 min post-resolution | Signed JWT token embedded in star links |
| CSAT rating response | SSD-006 | Customer → Platform | HTTP GET | Star link clicked in email | JWT token, rating (1–5) |
| CSAT comment submission | SSD-006 | Customer → Platform | HTTP POST | Optional on thank-you page | Comment text |
| NPS survey email | SSD-006 | Platform → Customer | SMTP via Email Provider | 30-day NPS recency check | Signed NPS token, 0–10 scale |
| CRM contact lookup | SSD-007 | Platform → CRM | REST GET | Ticket created | Contact email address |
| CRM case push | SSD-007 | Platform → CRM | REST POST | Ticket resolved | Case summary, CSAT score, handle time |
| CRM contact updated webhook | SSD-007 | CRM → Platform | HTTP POST (Webhook) | Contact/account changed in CRM | Changed fields, crm_contact_id |
| CRM nightly batch sync | SSD-007 | Platform ↔ CRM | REST GET (paginated cursor) | Scheduled 02:00 UTC | All contacts updated since last sync |
