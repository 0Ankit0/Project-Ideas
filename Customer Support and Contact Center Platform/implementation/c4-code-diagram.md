# C4 Code Diagram (Level 4) – Customer Support and Contact Center Platform

This document provides C4 Level 4 (Code) diagrams for the most critical code paths in the platform. Each diagram shows the key classes, their responsibilities, and relationships within the most important transaction boundaries.

---

## 1. Package Structure Reference

All Java services follow Domain-Driven Design (DDD) layered architecture:

### ticket-service Package Layout
```
ticket-service/
├── api/                              # Presentation layer
│   ├── TicketController.java         # REST endpoints; input validation; delegates to app service
│   ├── ThreadController.java         # Thread/message operations
│   ├── dto/
│   │   ├── CreateTicketRequest.java  # Validated input DTO (record + Bean Validation)
│   │   ├── UpdateTicketRequest.java
│   │   ├── TicketResponse.java       # Response projection; never exposes domain entity
│   │   └── TicketSummaryResponse.java
│   └── mapper/
│       └── TicketDtoMapper.java      # MapStruct mapper between domain and DTOs
├── application/                      # Use case orchestration
│   ├── TicketApplicationService.java # Orchestrates domain objects, emits domain events
│   ├── command/
│   │   ├── CreateTicketCommand.java
│   │   ├── AssignTicketCommand.java
│   │   └── CloseTicketCommand.java
│   └── handler/
│       └── TicketEventHandler.java   # Handles inbound domain events (e.g., BotHandoffRequested)
├── domain/                           # Pure domain model; no Spring/infra dependencies
│   ├── ticket/
│   │   ├── Ticket.java               # Aggregate root; guards all state transitions
│   │   ├── TicketId.java             # Value object (wraps UUID)
│   │   ├── TicketStatus.java         # Enum; transition() throws IllegalStateException on invalid
│   │   ├── TicketPriority.java
│   │   ├── TicketFactory.java        # Creates Ticket from CreateTicketCommand
│   │   ├── TicketRepository.java     # Repository interface (implemented in infrastructure/)
│   │   └── TicketDomainService.java  # Cross-aggregate domain logic
│   ├── thread/
│   │   ├── Thread.java               # Message thread entity
│   │   ├── ThreadMessage.java        # Individual message value object
│   │   └── ThreadRepository.java
│   ├── sla/
│   │   ├── SLAPolicy.java            # Immutable SLA policy value object
│   │   ├── SLAClock.java             # Clock state: start_time, breach_at, paused_at
│   │   └── SLAPolicyRepository.java
│   └── event/
│       ├── TicketCreatedEvent.java   # Domain event (immutable record)
│       ├── TicketAssignedEvent.java
│       ├── SLAStartedEvent.java
│       └── DomainEventPublisher.java # Interface for publishing events
├── infrastructure/                   # Adapters implementing domain interfaces
│   ├── persistence/
│   │   ├── TicketJpaRepository.java  # Spring Data JPA; returns JPA entities
│   │   ├── TicketJpaEntity.java      # @Entity; mapped to tickets table
│   │   └── TicketMapper.java        # Maps JPA entity ↔ domain Ticket
│   ├── messaging/
│   │   ├── KafkaEventPublisher.java  # Implements DomainEventPublisher
│   │   └── KafkaTopicConfig.java
│   └── client/
│       ├── RoutingEngineClient.java  # Feign/WebClient HTTP client for routing-engine
│       └── SLAServiceClient.java     # HTTP client for sla-svc
└── config/
    ├── SecurityConfig.java           # Keycloak + JWT filter chain
    ├── KafkaConfig.java
    └── FlywayConfig.java
```

### routing-engine Package Layout (Go)
```
routing-engine/
├── cmd/server/
│   └── main.go                       # Wire dependencies; start HTTP server
├── internal/
│   ├── handler/
│   │   └── routing_handler.go        # HTTP handler; parse request; delegate to service
│   ├── service/
│   │   ├── routing_orchestrator.go   # Top-level routing coordinator
│   │   ├── skill_matcher.go          # Filter agents by required skills
│   │   ├── availability_checker.go   # Check agent availability from Redis
│   │   ├── assignment_service.go     # Write assignment to DB and Redis
│   │   └── queue_manager.go          # Manage routing queues
│   ├── repository/
│   │   ├── agent_skill_repo.go       # pgx: query agent_skills table
│   │   └── queue_repo.go             # pgx: query routing_queues table
│   ├── store/
│   │   └── redis_availability.go     # Redis: HGETALL agent:availability:{id}
│   └── model/
│       ├── routing_request.go
│       ├── agent.go
│       └── assignment.go
└── pkg/
    ├── health/
    └── middleware/
```

---

## 2. Code Diagram 1: Ticket Creation Flow

This is the most critical write path. A new ticket is created from an inbound channel message, SLA clock is started, routing is initiated, and a domain event is published.

```mermaid
classDiagram
    class TicketController {
        +createTicket(CreateTicketRequest, JwtPrincipal) ResponseEntity
        -validateRequest(CreateTicketRequest) void
    }

    class TicketApplicationService {
        -ticketFactory: TicketFactory
        -ticketRepository: TicketRepository
        -slaServiceClient: SLAServiceClient
        -routingEngineClient: RoutingEngineClient
        -eventPublisher: DomainEventPublisher
        +createTicket(CreateTicketCommand) TicketResponse
    }

    class TicketFactory {
        +create(CreateTicketCommand) Ticket
        -applyDefaultPriority(Ticket, channel) void
        -buildInitialThread(CreateTicketCommand) Thread
    }

    class Ticket {
        -id: TicketId
        -status: TicketStatus
        -priority: TicketPriority
        -channel: Channel
        -contactId: UUID
        -assignedAgentId: UUID
        -slaClockId: UUID
        -createdAt: Instant
        +transitionTo(TicketStatus) void
        +assign(agentId: UUID) void
        +startSLA(slaClockId: UUID) void
        +recordEvents() List~DomainEvent~
    }

    class TicketRepository {
        <<interface>>
        +save(Ticket) Ticket
        +findById(TicketId) Optional~Ticket~
        +findByIdempotencyKey(String) Optional~Ticket~
    }

    class SLAServiceClient {
        +startClock(ticketId: UUID, policyId: UUID) SLAClockResponse
    }

    class RoutingEngineClient {
        +assignTicket(AssignRequest) AssignmentResponse
    }

    class DomainEventPublisher {
        <<interface>>
        +publish(DomainEvent) void
        +publishAll(List~DomainEvent~) void
    }

    class KafkaEventPublisher {
        -kafkaTemplate: KafkaTemplate
        +publish(DomainEvent) void
        +publishAll(List~DomainEvent~) void
    }

    class TicketCreatedEvent {
        +ticketId: UUID
        +contactId: UUID
        +channel: String
        +tenantId: UUID
        +correlationId: String
        +occurredAt: Instant
    }

    TicketController --> TicketApplicationService : delegates
    TicketApplicationService --> TicketFactory : creates ticket
    TicketApplicationService --> TicketRepository : persists
    TicketApplicationService --> SLAServiceClient : starts SLA clock
    TicketApplicationService --> RoutingEngineClient : requests assignment
    TicketApplicationService --> DomainEventPublisher : publishes events
    TicketFactory --> Ticket : builds
    KafkaEventPublisher ..|> DomainEventPublisher : implements
    DomainEventPublisher --> TicketCreatedEvent : publishes
```

### Sequence: Ticket Creation Transaction

```mermaid
sequenceDiagram
    participant C as TicketController
    participant A as TicketApplicationService
    participant F as TicketFactory
    participant R as TicketRepository
    participant SLA as SLAServiceClient
    participant RE as RoutingEngineClient
    participant EP as KafkaEventPublisher

    C->>A: createTicket(CreateTicketCommand)
    A->>R: findByIdempotencyKey(key) — dedup check
    R-->>A: Optional.empty()
    A->>F: create(command)
    F-->>A: Ticket (status=NEW)
    A->>R: save(ticket) — within @Transactional
    A->>SLA: startClock(ticketId, policyId)
    SLA-->>A: SLAClockResponse(clockId, breachAt)
    A->>A: ticket.startSLA(clockId)
    A->>R: save(ticket) — update with SLA ref
    A->>RE: assignTicket(AssignRequest)
    RE-->>A: AssignmentResponse(agentId) or QUEUED
    A->>A: ticket.assign(agentId) — status=OPEN
    A->>R: save(ticket) — final state
    A->>EP: publishAll(ticket.recordEvents())
    EP-->>A: published (async, fire-and-forget)
    A-->>C: TicketResponse
```

**Transaction boundary:** `TicketRepository.save()` calls are within a single `@Transactional` method. `SLAServiceClient` and `RoutingEngineClient` calls are outside the transaction (they are remote calls). If they fail, the ticket remains in `NEW` status and a compensating background job retries SLA start and routing assignment.

---

## 3. Code Diagram 2: Routing Decision Flow

The routing engine (Go) determines which agent receives a ticket based on skill matching and availability.

```mermaid
classDiagram
    class RoutingHandler {
        +handleAssign(w ResponseWriter, r *Request) void
    }

    class RoutingOrchestrator {
        -queueManager: QueueManager
        -skillMatcher: SkillMatcher
        -availabilityChecker: AvailabilityChecker
        -assignmentService: AssignmentService
        +Assign(ctx, RoutingRequest) AssignmentResult
    }

    class QueueManager {
        -queueRepo: QueueRepository
        +GetQueue(ctx, teamId string) Queue
        +Enqueue(ctx, ticketId string, queue Queue) error
        +Dequeue(ctx, queueId string) string
    }

    class SkillMatcher {
        -agentSkillRepo: AgentSkillRepository
        +Match(ctx, requiredSkills []string, teamId string) []AgentCandidate
        -scoreCandidate(agent AgentCandidate, skills []string) float64
    }

    class AvailabilityChecker {
        -redisStore: RedisAvailabilityStore
        +FilterAvailable(ctx, candidates []AgentCandidate) []AgentCandidate
        +GetStatus(ctx, agentId string) AvailabilityStatus
    }

    class AssignmentService {
        -assignRepo: AssignmentRepository
        -redisStore: RedisAvailabilityStore
        +Assign(ctx, ticketId string, agentId string) error
        +IncrementWorkload(ctx, agentId string) error
    }

    class AgentSkillRepository {
        -db: pgxPool
        +FindByTeam(ctx, teamId string) []AgentSkill
        +FindByAgent(ctx, agentId string) []string
    }

    class RedisAvailabilityStore {
        -client: redisClusterClient
        +GetAvailability(ctx, agentId string) AgentAvailability
        +SetBusy(ctx, agentId string) error
        +GetWorkload(ctx, agentId string) int
    }

    class QueueRepository {
        -db: pgxPool
        +GetQueueConfig(ctx, teamId string) QueueConfig
        +RecordQueueEntry(ctx, entry QueueEntry) error
    }

    RoutingHandler --> RoutingOrchestrator : calls
    RoutingOrchestrator --> QueueManager : manages queue
    RoutingOrchestrator --> SkillMatcher : finds candidates
    RoutingOrchestrator --> AvailabilityChecker : filters available
    RoutingOrchestrator --> AssignmentService : commits assignment
    SkillMatcher --> AgentSkillRepository : queries skills
    AvailabilityChecker --> RedisAvailabilityStore : checks presence
    AssignmentService --> RedisAvailabilityStore : updates state
    QueueManager --> QueueRepository : persists queue
```

### Routing Algorithm Detail

```mermaid
flowchart TD
    A[RoutingOrchestrator.Assign] --> B[QueueManager.GetQueue]
    B --> C[SkillMatcher.Match\nquery agent_skills WHERE team_id AND skill IN required]
    C --> D{Candidates found?}
    D -- no --> E[QueueManager.Enqueue ticket\nreturn QUEUED status]
    D -- yes --> F[AvailabilityChecker.FilterAvailable\ncheck Redis agent:availability:* HGETALL]
    F --> G{Available agents?}
    G -- no --> E
    G -- yes --> H[Score candidates\nweight = skill_proficiency × 1/current_workload]
    H --> I[Sort by score DESC\npick top candidate]
    I --> J[AssignmentService.Assign\nwrite to DB + Redis.SetBusy]
    J --> K[Return AssignmentResult\nagentId + queue position]
```

---

## 4. Code Diagram 3: SLA Clock Management

The SLA clock subsystem (Go) is the most latency-sensitive component. It manages thousands of concurrent SLA clocks.

```mermaid
classDiagram
    class SLAClockManager {
        -clockRepo: SLAClockRepository
        -scheduler: SLAScheduler
        +StartClock(ctx, StartClockRequest) SLAClock
        +PauseClock(ctx, clockId string) error
        +ResumeClock(ctx, clockId string) error
        +StopClock(ctx, clockId string) error
        -calculateBreachAt(policy SLAPolicy, businessHours BusinessHours) time.Time
    }

    class SLAClockRepository {
        -db: pgxPool
        -redis: redisClusterClient
        +Save(ctx, clock SLAClock) error
        +FindActive(ctx, tenantId string) []SLAClock
        +UpdateState(ctx, clockId string, state ClockState) error
        +RecordTransition(ctx, clockId string, transition ClockTransition) error
    }

    class SLAScheduler {
        -redis: redisClusterClient
        -breachDetector: SLABreachDetector
        +Schedule(ctx, clock SLAClock) error
        +Unschedule(ctx, clockId string) error
        +RunTick(ctx) error
        -fetchDueClocks(ctx, nowMs int64) []string
    }

    class SLABreachDetector {
        -clockRepo: SLAClockRepository
        -escalationEngine: EscalationEngine
        +DetectBreaches(ctx, clockIds []string) []BreachEvent
        +EmitWarnings(ctx, clockIds []string) []WarningEvent
    }

    class EscalationEngine {
        -ruleRepo: EscalationRuleRepository
        -actionExecutor: ActionExecutor
        +Escalate(ctx, event BreachEvent) error
        -selectRule(event BreachEvent, rules []EscalationRule) *EscalationRule
    }

    class EscalationRuleRepository {
        -db: pgxPool
        +FindByTenant(ctx, tenantId string) []EscalationRule
        +FindByPriority(ctx, tenantId string, priority string) []EscalationRule
    }

    class ActionExecutor {
        -kafkaProducer: kafkaSyncProducer
        +Execute(ctx, action EscalationAction) error
        -publishEscalationEvent(ctx, event EscalationEvent) error
        -publishNotificationRequest(ctx, req NotificationRequest) error
    }

    SLAClockManager --> SLAClockRepository : persists clocks
    SLAClockManager --> SLAScheduler : schedules ticks
    SLAScheduler --> SLAClockRepository : fetches due clocks
    SLAScheduler --> SLABreachDetector : detects breaches
    SLABreachDetector --> SLAClockRepository : reads clock details
    SLABreachDetector --> EscalationEngine : triggers escalation
    EscalationEngine --> EscalationRuleRepository : loads rules
    EscalationEngine --> ActionExecutor : executes actions
    ActionExecutor --> kafkaProducer : publishes events
```

### SLA Clock State Machine

```mermaid
stateDiagram-v2
    [*] --> PENDING : StartClock(ticketId, policyId)
    PENDING --> RUNNING : ClockActivated (ticket.status = OPEN)
    RUNNING --> WARNING : 80% of SLA window elapsed
    WARNING --> BREACHED : 100% of SLA window elapsed
    RUNNING --> PAUSED : ticket.status = PENDING (waiting customer)
    PAUSED --> RUNNING : ticket.status = OPEN (customer replied)
    RUNNING --> STOPPED : ticket.status = RESOLVED or CLOSED
    WARNING --> STOPPED : ticket.status = RESOLVED or CLOSED
    BREACHED --> STOPPED : ticket.status = RESOLVED or CLOSED
    PAUSED --> STOPPED : ticket.status = CLOSED
    STOPPED --> [*]
```

**Clock storage in Redis:**
```
Key:   sla:clock:{tenantId}          (Sorted Set)
Score: breach_at_unix_ms             (Unix timestamp in milliseconds)
Value: clockId                       (UUID string)

Key:   sla:clock:state:{clockId}     (Hash)
Fields:
  ticketId        -> UUID
  tenantId        -> UUID
  state           -> RUNNING|PAUSED|WARNING|BREACHED|STOPPED
  startedAt       -> ISO-8601
  breachAt        -> ISO-8601
  pausedAt        -> ISO-8601 (nullable)
  accruedMs       -> integer (total paused milliseconds)
  policyType      -> FIRST_RESPONSE|RESOLUTION
```

**SLA timer tick (runs every 1 second in `sla-timer-worker`):**
```go
func (s *SLAScheduler) RunTick(ctx context.Context) error {
    nowMs := time.Now().UnixMilli()
    // ZRANGEBYSCORE sla:clock:{tenantId} -inf nowMs LIMIT 0 100
    clockIds, err := s.redis.ZRangeByScore(ctx, clockKey, &redis.ZRangeBy{
        Min: "-inf", Max: strconv.FormatInt(nowMs, 10), Offset: 0, Count: 100,
    }).Result()
    if err != nil { return fmt.Errorf("fetch due clocks: %w", err) }
    if len(clockIds) == 0 { return nil }
    return s.breachDetector.DetectBreaches(ctx, clockIds)
}
```

---

## 5. Code Diagram 4: Channel Ingestion Pipeline

The channel ingestion pipeline normalizes messages from all external channels into a unified `ChannelMessage` DTO before publication to Kafka.

```mermaid
classDiagram
    class ChannelConnectorFactory {
        -connectors: Map~ChannelType, ChannelConnector~
        +getConnector(channelType: ChannelType) ChannelConnector
        +registerAll(connectors: ChannelConnector[]) void
    }

    class ChannelConnector {
        <<interface>>
        +receive() AsyncIterable~RawMessage~
        +send(outbound: OutboundMessage) Promise~void~
        +getChannelType() ChannelType
    }

    class EmailConnector {
        -imapClient: ImapClient
        -deduplicationService: DeduplicationService
        +receive() AsyncIterable~RawMessage~
        +send(outbound: OutboundMessage) Promise~void~
        -parseEmailHeaders(raw: Buffer) EmailHeaders
        -buildRawMessage(email: ParsedEmail) RawMessage
    }

    class ChatConnector {
        -wsServer: WebSocketServer
        -sessionStore: RedisSessionStore
        +receive() AsyncIterable~RawMessage~
        +send(outbound: OutboundMessage) Promise~void~
        -handleWebSocketMessage(ws: WebSocket, data: Buffer) void
    }

    class VoiceConnector {
        -twilioClient: TwilioRestClient
        -sipHandler: SIPHandler
        +receive() AsyncIterable~RawMessage~
        +send(outbound: OutboundMessage) Promise~void~
        -handleCallEvent(event: TwilioCallEvent) RawMessage
    }

    class MessageNormalizer {
        +normalize(raw: RawMessage) ChannelMessage
        -extractContactIdentity(raw: RawMessage) ContactIdentity
        -inferSubject(raw: RawMessage) string
        -mapChannelMetadata(raw: RawMessage) Metadata
    }

    class DeduplicationService {
        -redisClient: IORedis
        +isDuplicate(deduplicationKey: string) Promise~boolean~
        +markSeen(deduplicationKey: string, ttlSeconds: number) Promise~void~
        -buildKey(channelType: ChannelType, externalId: string) string
    }

    class IngestionPipeline {
        -connectorFactory: ChannelConnectorFactory
        -normalizer: MessageNormalizer
        -deduplicationService: DeduplicationService
        -ticketServiceClient: TicketServiceGrpcClient
        -kafkaProducer: KafkaProducer
        +run() Promise~void~
        -processMessage(raw: RawMessage) Promise~void~
    }

    class TicketServiceGrpcClient {
        +createOrUpdateTicket(msg: ChannelMessage) Promise~TicketRef~
        +appendMessage(ticketId: string, msg: ChannelMessage) Promise~void~
    }

    IngestionPipeline --> ChannelConnectorFactory : gets connectors
    IngestionPipeline --> MessageNormalizer : normalizes messages
    IngestionPipeline --> DeduplicationService : deduplicates
    IngestionPipeline --> TicketServiceGrpcClient : creates/updates tickets
    IngestionPipeline --> KafkaProducer : publishes to channel.inbound
    ChannelConnectorFactory --> EmailConnector : creates
    ChannelConnectorFactory --> ChatConnector : creates
    ChannelConnectorFactory --> VoiceConnector : creates
    EmailConnector ..|> ChannelConnector : implements
    ChatConnector ..|> ChannelConnector : implements
    VoiceConnector ..|> ChannelConnector : implements
    EmailConnector --> DeduplicationService : uses
```

### Ingestion Pipeline Flow

```mermaid
flowchart TD
    A[IngestionPipeline.run] --> B[ChannelConnectorFactory.getConnector for each channel]
    B --> C[connector.receive — async generator]
    C --> D[DeduplicationService.isDuplicate\nkey = channel_type:external_message_id]
    D -- duplicate --> E[Log + discard\nincrement cs_dedup_discarded_total counter]
    D -- new --> F[MessageNormalizer.normalize\nto ChannelMessage DTO]
    F --> G{Thread detection:\nIn-Reply-To or ticketId header?}
    G -- existing thread --> H[TicketServiceGrpcClient.appendMessage]
    G -- new conversation --> I[TicketServiceGrpcClient.createOrUpdateTicket]
    H --> J[DeduplicationService.markSeen TTL=7d]
    I --> J
    J --> K[KafkaProducer.send to channel.inbound\nfor downstream consumers]
```

**ChannelMessage DTO (TypeScript):**
```typescript
interface ChannelMessage {
  messageId:         string;          // Platform-generated UUID
  externalMessageId: string;          // Provider message ID (for dedup)
  channelType:       ChannelType;     // EMAIL | CHAT | SMS | WHATSAPP | VOICE | SOCIAL
  direction:         'INBOUND' | 'OUTBOUND';
  contactIdentity:   ContactIdentity; // { email?, phone?, socialHandle? }
  subject:           string | null;   // Email subject; null for chat/sms
  body:              string;          // Plain text body (HTML stripped)
  bodyHtml:          string | null;   // Original HTML (email only)
  attachments:       Attachment[];    // S3 references
  metadata:          Record<string, string>; // Channel-specific extras
  receivedAt:        Date;
  tenantId:          string;
  correlationId:     string;
}
```

---

## 6. Code Diagram 5: Bot-to-Human Handoff

The handoff is a critical atomic operation. The bot session must be cleanly transferred with all context to the agent.

```mermaid
classDiagram
    class BotSessionManager {
        -sessionStore: RedisSessionStore
        +getSession(sessionId: str) BotSession
        +freezeSession(sessionId: str) BotSession
        +expireSession(sessionId: str) None
        +resumeSession(sessionId: str) None
    }

    class HandoffOrchestrator {
        -botSessionManager: BotSessionManager
        -contextSerializer: ContextSerializer
        -ticketService: TicketServiceClient
        -routingEngine: RoutingEngineClient
        -notificationService: NotificationServiceClient
        +initiateHandoff(sessionId: str, reason: HandoffReason) HandoffResult
    }

    class ContextSerializer {
        +serialize(session: BotSession) HandoffContext
        -extractEntities(session: BotSession) dict
        -inferSentiment(session: BotSession) SentimentScore
        -buildTranscript(session: BotSession) list[TranscriptEntry]
    }

    class HandoffContext {
        +sessionId: str
        +transcript: list[TranscriptEntry]
        +extractedEntities: dict
        +predictedIntent: str
        +confidenceScore: float
        +customerSentiment: SentimentScore
        +suggestedArticles: list[str]
        +handoffReason: HandoffReason
        +contextVersion: int
    }

    class RedisSessionStore {
        +get(sessionId: str) dict
        +set(sessionId: str, data: dict, ttl: int) None
        +expire(sessionId: str) None
        +setFlag(sessionId: str, flag: str, value: str) None
    }

    HandoffOrchestrator --> BotSessionManager : freezes session
    HandoffOrchestrator --> ContextSerializer : serializes context
    HandoffOrchestrator --> TicketServiceClient : creates/updates ticket with context
    HandoffOrchestrator --> RoutingEngineClient : requests agent assignment
    HandoffOrchestrator --> NotificationServiceClient : notifies agent
    BotSessionManager --> RedisSessionStore : manages session state
    ContextSerializer --> HandoffContext : produces
```

---

## 7. Cross-Cutting Design Patterns

### Outbox Pattern (Reliable Event Publishing)
All Java services use the transactional outbox pattern to guarantee at-least-once event delivery:

```
1. Within @Transactional: save domain entity + save event to outbox_events table
2. OutboxPollingPublisher (background thread, 500ms poll): reads unpublished outbox_events
3. Publish to Kafka
4. Mark outbox_event as published
5. On Kafka timeout: retry up to 3× with exponential backoff; alert if all retries fail
```

### Idempotency Pattern
All mutating endpoints accept `X-Idempotency-Key` header:
```
1. Hash idempotency key + tenant_id → lookup in idempotency_keys table (Redis + DB)
2. If found and status=COMPLETED: return cached response
3. If found and status=IN_PROGRESS: return 202 Accepted (poll or wait)
4. If not found: process and store result with 24-hour TTL
```

### Row-Level Security (Multi-Tenancy)
All PostgreSQL queries are tenant-scoped using RLS policies:
```sql
-- Applied to all major tables
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON tickets
  USING (tenant_id = current_setting('app.tenant_id')::uuid);
-- Application sets: SET LOCAL app.tenant_id = '<tenant_uuid>'
```
