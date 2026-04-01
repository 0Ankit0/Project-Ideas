# System Sequence Diagrams — Ticketing and Project Management System

## Overview

This document captures the key system-level interaction flows across microservices for the Ticketing and Project Management System. Each sequence diagram traces the path of a user action or internal system event through the service mesh, documenting synchronous REST calls, asynchronous Kafka events, and Redis-backed timer operations.

All sequences reflect production behavior: API Gateway authentication and rate limiting are always the first hop; service-to-service calls use mTLS within the Kubernetes cluster; async events are published to Kafka topics with at-least-once delivery guarantees.

---

## Sequence 1: Ticket Creation and Assignment

A developer or project manager submits a new ticket. The flow validates the target project, resolves the workflow's initial state, persists the ticket, starts the SLA clock, notifies the assignee, and indexes the ticket for full-text search — all before returning the created ticket to the client.

```mermaid
sequenceDiagram
    autonumber
    actor Client as Client (Browser/API)
    participant GW as API Gateway (Kong)
    participant TS as Ticket Service
    participant PS as Project Service
    participant WS as Workflow Service
    participant DB as PostgreSQL (Ticket DB)
    participant KF as Kafka
    participant SLA as SLA Service
    participant RD as Redis (SLA Timers)
    participant NS as Notification Service
    participant SS as Search Service
    participant ES as Elasticsearch

    Client->>GW: POST /api/v1/tickets
{projectId, title, type, priority, assigneeId, ...}
    GW->>GW: Validate JWT, check rate limit (Redis)
    GW->>TS: Forward request with user context headers

    TS->>PS: GET /internal/projects/{projectId}/validate
{requesterId}
    PS->>PS: Check project exists, requester is member,
create permission granted
    PS-->>TS: 200 {projectId, defaultWorkflowId, defaultSLAPolicyId,
customFieldSchema, boardId}

    TS->>WS: GET /internal/workflows/{workflowId}/initial-state
    WS-->>TS: 200 {stateId: "open", stateName: "Open",
category: "TODO", entryActions: []}

    TS->>TS: Generate ticket key (PROJECT-{seq})
Apply custom field defaults
Compute SLA target based on priority + policy

    TS->>DB: BEGIN TRANSACTION
INSERT INTO tickets (...)
INSERT INTO ticket_history (created event)
COMMIT
    DB-->>TS: 201 {ticketId, ticketKey, createdAt}

    TS->>KF: Publish ticket.created event
{ticketId, projectId, workflowId, assigneeId,
priority, slaPolicy, createdBy, timestamp}

    TS-->>GW: 201 {ticket object with all fields}
    GW-->>Client: 201 Created {ticket}

    Note over KF,SS: Async processing after client response

    KF->>SLA: Consume ticket.created
    SLA->>SLA: Calculate SLA due timestamps
(responseBy, resolutionBy) based on
priority + business hours calendar
    SLA->>DB: INSERT INTO sla_timers {ticketId, responseBy,
resolutionBy, status: ACTIVE}
    SLA->>RD: ZADD sla:active {score=resolutionBy.epochMs,
member=ticketId}
SET sla:ticket:{ticketId} {timerState}

    KF->>NS: Consume ticket.created
    NS->>NS: Resolve notification preferences for assigneeId
Render email + in-app templates
    NS->>NS: Send email via SendGrid
Publish in-app notification to WebSocket hub
Post Slack message if workspace Slack integration active

    KF->>SS: Consume ticket.created
    SS->>ES: POST /tickets/_doc/{ticketId}
{title, description, comments:[], labels,
projectId, assigneeId, status, priority, type}
    ES-->>SS: 201 {_id, result: "created"}
```

**Flow Notes:**
- Steps 1–12 are synchronous; the client receives the `201` response before SLA, notification, and search processing completes.
- The Kafka `ticket.created` event carries a full snapshot so downstream consumers are idempotent — they do not need to re-query the Ticket Service.
- SLA due timestamps are computed from the project's `SLAPolicy` (response time + resolution time) adjusted for business-hours calendars stored in the Project Service.
- The ticket key sequence (`PROJECT-{seq}`) uses a PostgreSQL sequence scoped per project, ensuring uniqueness without distributed coordination.

---

## Sequence 2: Ticket Status Transition

A user moves a ticket from one workflow state to another (e.g., "In Progress" → "In Review"). The Workflow Service validates the transition is permitted by the board's workflow graph, the database is updated atomically, SLA timers are adjusted, automation triggers are evaluated, and subscribers are notified.

```mermaid
sequenceDiagram
    autonumber
    actor Client as Client
    participant GW as API Gateway
    participant TS as Ticket Service
    participant WS as Workflow Service
    participant DB as PostgreSQL
    participant KF as Kafka
    participant SLA as SLA Service
    participant RD as Redis
    participant AE as Automation Engine
    participant NS as Notification Service
    participant SS as Search Service

    Client->>GW: PATCH /api/v1/tickets/{ticketId}/status
{toStateId, comment?, transitionId}
    GW->>GW: Validate JWT, rate limit check
    GW->>TS: Forward with user context

    TS->>DB: SELECT ticket WHERE id={ticketId}
FOR UPDATE SKIP LOCKED
    DB-->>TS: {ticketId, currentStateId, workflowId,
assigneeId, slaTimerId, projectId}

    TS->>WS: POST /internal/workflows/{workflowId}/validate-transition
{fromStateId, toStateId, actorId, ticketId}
    WS->>WS: Load transition graph for workflow
Check transition exists: from→to
Evaluate transition conditions (role, field guards)
Check required fields populated for target state
    WS-->>TS: 200 {valid: true, transition: {id, name,
postActions: ["notify_reporter", "clear_assignee?"]},
newStateCategory: "IN_PROGRESS"}

    TS->>DB: BEGIN TRANSACTION
UPDATE tickets SET stateId={toStateId}, updatedAt=NOW()
INSERT INTO ticket_history {actorId, fromState, toState, timestamp}
INSERT INTO ticket_comments IF comment provided
COMMIT
    DB-->>TS: OK

    TS->>KF: Publish ticket.status_changed
{ticketId, projectId, fromStateId, toStateId,
fromCategory, toCategory, actorId, timestamp,
slaTimerId, priority}

    TS-->>GW: 200 {updated ticket}
    GW-->>Client: 200 OK

    Note over KF,SS: Async consumers process in parallel

    KF->>SLA: Consume ticket.status_changed
    SLA->>SLA: Evaluate SLA impact of transition:
- toCategory==DONE → stop all timers
- toCategory==IN_PROGRESS + responseTimer running → mark response SLA met
- toCategory==ON_HOLD → pause resolution timer
    SLA->>RD: ZREM sla:active {ticketId} (if resolved)
or HSET sla:ticket:{ticketId} status PAUSED pausedAt NOW()
    SLA->>DB: UPDATE sla_timers SET status, responseMetAt?, resolvedAt?

    KF->>AE: Consume ticket.status_changed
    AE->>AE: Load automation rules for project
Match rules WHERE trigger.type=STATUS_CHANGED
AND trigger.toStateId={toStateId}
Evaluate conditions (assignee, labels, priority...)
    AE->>AE: Execute matched actions:
- Auto-assign to next team member
- Set field values
- Create linked sub-tasks
- Trigger webhooks
    AE->>KF: Publish automation.actions_executed {results}

    KF->>NS: Consume ticket.status_changed
    NS->>NS: Resolve watchers + reporter + assignee
Apply notification preference filters
Send targeted notifications (email, in-app, Slack)

    KF->>SS: Consume ticket.status_changed
    SS->>SS: Build partial update document
{status, stateCategory, updatedAt}
    SS->>ES: POST /tickets/_update/{ticketId}
{doc: {status, stateCategory, updatedAt}}
```

**Flow Notes:**
- `SELECT ... FOR UPDATE SKIP LOCKED` prevents concurrent transitions on the same ticket from causing state corruption.
- Transition conditions in the Workflow Service support: role-based guards (only QA can transition to "Verified"), field-required guards (resolution notes must be filled before closing), and time-based guards (cannot reopen after 30 days).
- SLA timer logic: response SLA is met when a ticket first enters an "IN_PROGRESS" category state; resolution SLA is met when the ticket enters a "DONE" category state.

---

## Sequence 3: Sprint Planning and Start

A Project Manager creates a sprint, adds backlog tickets to it via drag-and-drop, sets the capacity, and starts the sprint. Starting a sprint locks the backlog selection, sets board state, and notifies all team members.

```mermaid
sequenceDiagram
    autonumber
    actor PM as Project Manager
    participant GW as API Gateway
    participant SPS as Sprint Service
    participant PS as Project Service
    participant TS as Ticket Service
    participant DB as PostgreSQL
    participant KF as Kafka
    participant NS as Notification Service

    PM->>GW: POST /api/v1/projects/{projectId}/sprints
{name, goal, startDate, endDate, capacity}
    GW->>SPS: Create sprint
    SPS->>PS: Validate project, check no active sprint overlaps dates
    PS-->>SPS: 200 {valid: true, teamSize, defaultVelocity}
    SPS->>DB: INSERT INTO sprints {name, goal, startDate, endDate,
capacity, status: PLANNING, projectId}
    DB-->>SPS: {sprintId}
    SPS-->>GW: 201 {sprint}
    GW-->>PM: 201 {sprint}

    PM->>GW: POST /api/v1/sprints/{sprintId}/tickets
{ticketIds: ["PROJ-12","PROJ-14","PROJ-18",...]}
    GW->>SPS: Add tickets to sprint
    SPS->>TS: POST /internal/tickets/bulk-validate
{ticketIds, projectId, targetSprintId}
    TS->>TS: Verify tickets belong to project
Verify tickets are unassigned to another active sprint
Return storyPoints sum
    TS-->>SPS: {valid: true, totalStoryPoints: 34, tickets: [...]}
    SPS->>SPS: Check capacity: 34sp ≤ capacity (40sp) ✓
    SPS->>DB: UPDATE tickets SET sprintId={sprintId} WHERE id IN (...)
    SPS->>DB: UPDATE sprints SET plannedStoryPoints=34
    SPS-->>GW: 200 {addedCount: 3, totalPlanned: 34}
    GW-->>PM: 200

    PM->>GW: POST /api/v1/sprints/{sprintId}/start
    GW->>SPS: Start sprint
    SPS->>DB: SELECT sprint FOR UPDATE
    SPS->>SPS: Validate status=PLANNING, startDate≤TODAY
Validate at least 1 ticket assigned
    SPS->>DB: BEGIN TRANSACTION
UPDATE sprints SET status=ACTIVE, actualStartDate=NOW()
UPDATE project SET activeSprintId={sprintId}
INSERT INTO sprint_history {event: STARTED}
COMMIT
    SPS->>KF: Publish sprint.started {sprintId, projectId,
startDate, endDate, plannedStoryPoints,
teamId, ticketIds}
    SPS-->>GW: 200 {sprint with status: ACTIVE}
    GW-->>PM: 200

    KF->>NS: Consume sprint.started
    NS->>NS: Fetch team members for projectId
Render "Sprint {name} has started" notification
    NS->>NS: Send email digest + in-app notifications
to all team members
    KF->>TS: Consume sprint.started
    TS->>DB: UPDATE tickets SET boardColumnId=(first active column)
WHERE sprintId={sprintId} AND boardColumnId IS NULL
```

---

## Sequence 4: SLA Breach Detection

The SLA Service runs a Redis-backed timer scheduler. Every 60 seconds a Lua script scans the sorted set of active SLA timers for entries whose score (epoch ms) is ≤ now. Breached timers trigger escalation events consumed by the Notification Service and written back to the database.

```mermaid
sequenceDiagram
    autonumber
    participant SCHED as SLA Scheduler (cron/60s)
    participant RD as Redis
    participant SLA as SLA Service
    participant DB as PostgreSQL
    participant KF as Kafka
    participant NS as Notification Service
    participant AE as Automation Engine
    participant TS as Ticket Service

    loop Every 60 seconds
        SCHED->>RD: ZRANGEBYSCORE sla:active 0 {now_epoch_ms}
LIMIT 0 100
        RD-->>SCHED: [{ticketId1}, {ticketId2}, ...]

        alt No breaches
            SCHED->>SCHED: Sleep until next tick
        else Breaches detected
            SCHED->>SLA: processBreaches([ticketId1, ticketId2, ...])

            loop For each breached ticketId
                SLA->>RD: GET sla:ticket:{ticketId}
                RD-->>SLA: {timerType, policyId, responseBy,
resolutionBy, escalationLevel}

                SLA->>DB: SELECT t.*, sp.escalationChain, sp.breachActions
FROM tickets t
JOIN sla_policies sp ON t.slaPolicyId=sp.id
WHERE t.id={ticketId}
                DB-->>SLA: {ticket, policy, currentEscalationLevel}

                SLA->>DB: INSERT INTO sla_breaches
{ticketId, timerType, breachedAt: NOW(),
policyId, escalationLevel: current+1}
                SLA->>DB: UPDATE sla_timers SET status=BREACHED,
escalationLevel=current+1, breachedAt=NOW()

                SLA->>RD: ZREM sla:active {ticketId}
                SLA->>RD: ZADD sla:escalation {nextEscalation.epochMs} {ticketId}

                SLA->>KF: Publish sla.breached
{ticketId, ticketKey, projectId, assigneeId,
reporterId, timerType, breachedAt, policyId,
escalationLevel, escalationChain}
            end

            KF->>NS: Consume sla.breached
            NS->>NS: Resolve escalation chain contacts
(L1: assignee, L2: team lead, L3: PM, L4: VP Eng)
            NS->>NS: Send breach alert: email (high priority)
+ Slack DM + in-app banner
to current escalation level contacts
            NS->>NS: If escalationLevel > 1: also notify all previous levels

            KF->>AE: Consume sla.breached
            AE->>AE: Match automation rules for SLA_BREACHED trigger
Execute: raise priority to CRITICAL
Auto-reassign if assignee unresponsive
Post public comment "SLA breached - escalated"

            KF->>TS: Consume sla.breached
            TS->>DB: UPDATE tickets SET priority=CRITICAL
WHERE id={ticketId} AND priority != CRITICAL
INSERT INTO ticket_history {SLA_BREACH event}
        end
    end
```

**Flow Notes:**
- Redis sorted set `sla:active` uses resolution deadline epoch ms as the score, enabling O(log N) range queries for due timers.
- The Lua script approach ensures atomic read-and-remove to prevent double-processing under concurrent scheduler instances (only one scheduler pod is active via leader election using Redis `SET NX`).
- Escalation levels are defined per `SLAPolicy`: each level adds additional notification recipients and may trigger automated priority upgrades.
- Tickets in "ON_HOLD" status have their resolution timer paused; the sorted set score is set to `MAX_INT` while paused.

---

## Sequence Summary

| Sequence | Trigger | Sync Hops | Async Consumers | Key Invariants |
|---|---|---|---|---|
| Ticket Creation | `POST /tickets` | 4 (GW→TS→PS→WS→DB) | SLA, Notification, Search | Atomic ticket + history insert; SLA clock starts after commit |
| Status Transition | `PATCH /tickets/{id}/status` | 3 (GW→TS→WS→DB) | SLA, Automation, Notification, Search | Optimistic lock on ticket row; idempotent downstream consumers |
| Sprint Planning/Start | `POST /sprints/{id}/start` | 3 (GW→SPS→TS→DB) | Notification, Ticket Service | Exactly-one active sprint per board; capacity pre-validated |
| SLA Breach Detection | Redis timer expiry | 0 (internal) | Notification, Automation, Ticket | Leader-elected scheduler; idempotent breach records |
