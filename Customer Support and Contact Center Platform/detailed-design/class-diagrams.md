# Class Diagrams — Customer Support and Contact Center Platform

> **Document Purpose:** Defines the object-oriented domain model for the platform using UML class diagrams rendered in Mermaid. Each diagram covers one bounded context. Attributes include visibility modifiers (`+` public, `-` private, `#` protected) and types. Relationships are annotated with cardinality and role labels.

---

## Diagram 1 — Core Ticket Domain

This diagram models the central aggregate of the platform: **Ticket**. A Ticket is the unit of work that tracks a customer issue from creation to resolution. It owns a set of `TicketThread` objects (conversations), each composed of `Message` instances. Messages may carry `Attachment` objects. Every ticket is linked to a `Contact` (the customer), routed through a `Queue`, associated with one or more `Channel` definitions, and tagged with zero-or-more `Tag` labels.

```mermaid
classDiagram
    class Ticket {
        +UUID id
        +String ticketNumber
        +UUID organizationId
        +UUID contactId
        +UUID queueId
        +UUID assignedAgentId
        +UUID assignedTeamId
        +TicketStatus status
        +Priority priority
        +String subject
        +String description
        +ChannelType sourceChannel
        +DateTime createdAt
        +DateTime updatedAt
        +DateTime firstResponseAt
        +DateTime resolvedAt
        +DateTime closedAt
        +String externalRef
        +Map~String,String~ customFields
        +open() void
        +assign(agentId UUID) void
        +reassign(agentId UUID, reason String) void
        +pend() void
        +hold(reason String, duration Duration) void
        +resolve(wrapCodeId UUID) void
        +close() void
        +reopen(reason String) void
        +addTag(tag Tag) void
        +removeTag(tagId UUID) void
        +merge(sourceTicketId UUID) void
        +split(messageIds List~UUID~) Ticket
        +calculateSLAStatus() SLAStatus
    }

    class TicketThread {
        +UUID id
        +UUID ticketId
        +ThreadType type
        +String subject
        +Boolean isInternal
        +DateTime createdAt
        +DateTime lastMessageAt
        +Int messageCount
        +addMessage(message Message) void
        +getMessages(page Int, size Int) List~Message~
        +markRead(agentId UUID) void
    }

    class Message {
        +UUID id
        +UUID threadId
        +UUID senderId
        +SenderType senderType
        +String bodyText
        +String bodyHtml
        +MessageDirection direction
        +MessageStatus status
        +DateTime sentAt
        +DateTime deliveredAt
        +DateTime readAt
        +String externalMessageId
        +List~UUID~ attachmentIds
        +Boolean isPrivateNote
        +addAttachment(attachment Attachment) void
        +markDelivered() void
        +markRead() void
        +redact(reason String) void
    }

    class Attachment {
        +UUID id
        +UUID messageId
        +String filename
        +String mimeType
        +Long fileSizeBytes
        +String storageKey
        +String downloadUrl
        +DateTime uploadedAt
        +Boolean isInline
        +String virusScanStatus
        +generatePresignedUrl(ttlSeconds Int) String
        +flagInfected() void
        +delete() void
    }

    class Contact {
        +UUID id
        +UUID organizationId
        +String firstName
        +String lastName
        +String email
        +String phone
        +String externalId
        +String avatarUrl
        +String timezone
        +String language
        +ContactSegment segment
        +Map~String,String~ customAttributes
        +DateTime createdAt
        +DateTime lastSeenAt
        +getFullName() String
        +getTickets(limit Int) List~Ticket~
        +merge(duplicateContactId UUID) void
        +updateSegment(segment ContactSegment) void
    }

    class Channel {
        +UUID id
        +UUID organizationId
        +ChannelType type
        +String name
        +String externalAddress
        +Boolean isActive
        +Map~String,String~ config
        +DateTime createdAt
        +activate() void
        +deactivate() void
        +testConnectivity() Boolean
        +getConfig~T~(key String) T
    }

    class Queue {
        +UUID id
        +UUID organizationId
        +UUID teamId
        +String name
        +String description
        +Int maxConcurrentTickets
        +Int currentDepth
        +RoutingStrategy routingStrategy
        +Boolean isActive
        +DateTime createdAt
        +enqueue(ticketId UUID, priority Priority) void
        +dequeue() UUID
        +peek() UUID
        +getDepth() Int
        +pause() void
        +resume() void
        +transferTickets(targetQueueId UUID) void
    }

    class Tag {
        +UUID id
        +UUID organizationId
        +String name
        +String colorHex
        +String description
        +Int usageCount
        +DateTime createdAt
        +rename(newName String) void
        +merge(targetTagId UUID) void
        +getTickets(limit Int) List~Ticket~
    }

    Ticket "1" *-- "1..*" TicketThread : contains
    TicketThread "1" *-- "0..*" Message : composed of
    Message "1" o-- "0..*" Attachment : has
    Contact "1" --> "0..*" Ticket : raises
    Queue "1" --> "0..*" Ticket : holds
    Channel "1" --> "0..*" Ticket : source
    Ticket "0..*" --> "0..*" Tag : labelled with
```

---

## Diagram 2 — Agent and Team Domain

This diagram covers the **workforce model**. An `Organization` owns multiple `Team` objects. Each `Team` contains `Agent` members. An `Agent` holds a collection of `AgentSkill` proficiencies used by the routing engine. Agents follow `WorkforceSchedule` definitions that decompose into `Shift` windows. Post-interaction wrap-up is captured via `WrapCode` and `Disposition`.

```mermaid
classDiagram
    class Organization {
        +UUID id
        +String name
        +String subdomain
        +String timezone
        +String defaultLanguage
        +PlanTier plan
        +Boolean isActive
        +Int maxAgents
        +Int maxChannels
        +DateTime createdAt
        +Map~String,String~ settings
        +suspend() void
        +activate() void
        +upgradePlan(tier PlanTier) void
        +getAgentCount() Int
        +getActiveTicketCount() Int
    }

    class Team {
        +UUID id
        +UUID organizationId
        +String name
        +String description
        +UUID teamLeadAgentId
        +Boolean isActive
        +DateTime createdAt
        +addMember(agentId UUID, role TeamRole) void
        +removeMember(agentId UUID) void
        +getMembers() List~Agent~
        +getAvailableMembers() List~Agent~
        +assignQueue(queueId UUID) void
    }

    class Agent {
        +UUID id
        +UUID organizationId
        +UUID userId
        +String firstName
        +String lastName
        +String email
        +String avatarUrl
        +AgentStatus status
        +Int maxConcurrentTickets
        +Int currentTicketCount
        +String timezone
        +String language
        +DateTime lastActiveAt
        +DateTime createdAt
        +setStatus(status AgentStatus) void
        +assignTicket(ticketId UUID) void
        +unassignTicket(ticketId UUID) void
        +getActiveTickets() List~Ticket~
        +isAvailable() Boolean
        +isOverloaded() Boolean
        +addSkill(skill AgentSkill) void
        +removeSkill(skillId UUID) void
    }

    class AgentSkill {
        +UUID id
        +UUID agentId
        +String skillName
        +SkillLevel level
        +Boolean isCertified
        +DateTime certifiedAt
        +DateTime expiresAt
        +Boolean isActive
        +upgrade(newLevel SkillLevel) void
        +revoke(reason String) void
        +isExpired() Boolean
    }

    class WorkforceSchedule {
        +UUID id
        +UUID organizationId
        +String name
        +String timezone
        +List~UUID~ agentIds
        +DateTime effectiveFrom
        +DateTime effectiveTo
        +Boolean isActive
        +addShift(shift Shift) void
        +removeShift(shiftId UUID) void
        +getShiftsForDate(date LocalDate) List~Shift~
        +isAgentOnDuty(agentId UUID, at DateTime) Boolean
        +clone(newEffectiveFrom DateTime) WorkforceSchedule
    }

    class Shift {
        +UUID id
        +UUID scheduleId
        +UUID agentId
        +DayOfWeek dayOfWeek
        +LocalTime startTime
        +LocalTime endTime
        +String timezone
        +Boolean isOverride
        +LocalDate overrideDate
        +ShiftType type
        +getDurationMinutes() Int
        +overlaps(other Shift) Boolean
        +isCurrentlyActive(at DateTime) Boolean
    }

    class WrapCode {
        +UUID id
        +UUID organizationId
        +String code
        +String label
        +String description
        +Boolean requiresNote
        +Boolean isActive
        +WrapCategory category
        +Int usageCount
        +activate() void
        +deactivate() void
    }

    class Disposition {
        +UUID id
        +UUID ticketId
        +UUID agentId
        +UUID wrapCodeId
        +String notes
        +Int wrapTimeSeconds
        +DateTime recordedAt
        +Boolean requiresFollowUp
        +DateTime followUpDueAt
        +validate() Boolean
        +getWrapCode() WrapCode
    }

    Organization "1" *-- "1..*" Team : owns
    Organization "1" *-- "1..*" Agent : employs
    Team "0..*" o-- "1..*" Agent : has members
    Agent "1" *-- "0..*" AgentSkill : possesses
    Organization "1" *-- "0..*" WorkforceSchedule : defines
    WorkforceSchedule "1" *-- "1..*" Shift : composed of
    Agent "1" --> "0..*" Shift : works
    Ticket "1" --> "0..1" Disposition : wrapped with
    Disposition "1" --> "1" WrapCode : uses
    Organization "1" *-- "1..*" WrapCode : configures
```

---

## Diagram 3 — SLA and Escalation Domain

The SLA subsystem tracks time-based service level commitments. An `SLAPolicy` defines the rules (first-response time, resolution time, applicable conditions). An `SLAClock` is an instance created per ticket, per policy. `BusinessHoursSchedule` adjusts elapsed time calculations to exclude non-business hours. `SLABreach` records are created when a clock exceeds its deadline. `EscalationRule` defines automated reactions to breach events, executed via `EscalationAction`.

```mermaid
classDiagram
    class SLAPolicy {
        +UUID id
        +UUID organizationId
        +String name
        +String description
        +Int firstResponseMinutes
        +Int nextResponseMinutes
        +Int resolutionMinutes
        +Priority applicablePriority
        +Boolean useBusinessHours
        +UUID businessHoursScheduleId
        +Int warningThresholdPercent
        +Boolean isDefault
        +Boolean isActive
        +DateTime createdAt
        +getFirstResponseDeadline(from DateTime) DateTime
        +getResolutionDeadline(from DateTime) DateTime
        +calculateElapsed(start DateTime, end DateTime) Duration
        +applies(ticket Ticket) Boolean
    }

    class SLAClock {
        +UUID id
        +UUID ticketId
        +UUID slaPolicyId
        +SLAClockType type
        +SLAClockStatus status
        +DateTime startedAt
        +DateTime pausedAt
        +Duration accumulatedPauseTime
        +DateTime dueAt
        +DateTime warnAt
        +DateTime breachedAt
        +DateTime stoppedAt
        +start(at DateTime) void
        +pause(at DateTime) void
        +resume(at DateTime) void
        +stop(at DateTime) void
        +getRemainingTime(at DateTime) Duration
        +getElapsedTime(at DateTime) Duration
        +isBreached(at DateTime) Boolean
        +isWarning(at DateTime) Boolean
        +recalculate(policy SLAPolicy) void
    }

    class SLABreach {
        +UUID id
        +UUID ticketId
        +UUID slaClockId
        +UUID slaPolicyId
        +SLAClockType breachType
        +DateTime dueAt
        +DateTime actualAt
        +Duration overdueBy
        +Boolean acknowledged
        +UUID acknowledgedByAgentId
        +DateTime acknowledgedAt
        +String rootCause
        +acknowledge(agentId UUID, rootCause String) void
        +getOverdueMinutes() Int
    }

    class EscalationRule {
        +UUID id
        +UUID organizationId
        +String name
        +String description
        +EscalationTrigger trigger
        +Int triggerThresholdMinutes
        +Priority targetPriority
        +List~UUID~ notifyAgentIds
        +List~UUID~ notifyTeamIds
        +Boolean reassign
        +UUID reassignQueueId
        +Int executionOrder
        +Boolean isActive
        +DateTime createdAt
        +evaluate(ticket Ticket) Boolean
        +execute(ticket Ticket) List~EscalationAction~
    }

    class EscalationAction {
        +UUID id
        +UUID escalationRuleId
        +UUID ticketId
        +EscalationActionType actionType
        +Map~String,Object~ parameters
        +EscalationActionStatus status
        +DateTime executedAt
        +String errorMessage
        +Int retryCount
        +execute() void
        +retry() void
        +fail(reason String) void
        +getResult() Map~String,Object~
    }

    class BusinessHoursSchedule {
        +UUID id
        +UUID organizationId
        +String name
        +String timezone
        +Map~DayOfWeek,TimeWindow~ weeklySchedule
        +List~Holiday~ holidays
        +Boolean isActive
        +addHoliday(holiday Holiday) void
        +removeHoliday(date LocalDate) void
        +isBusinessHour(at DateTime) Boolean
        +getNextBusinessStart(from DateTime) DateTime
        +calculateBusinessMinutes(from DateTime, to DateTime) Int
        +clone() BusinessHoursSchedule
    }

    SLAPolicy "1" --> "0..*" SLAClock : instantiates
    SLAPolicy "1" --> "0..1" BusinessHoursSchedule : uses
    SLAClock "1" --> "0..1" SLABreach : produces
    SLAClock "1" --> "1" SLAPolicy : governs by
    EscalationRule "1" --> "0..*" EscalationAction : triggers
    SLABreach "1" --> "1..*" EscalationRule : activates
    Ticket "1" --> "1..*" SLAClock : tracked by
    Ticket "1" --> "0..*" SLABreach : may have
```

---

## Diagram 4 — Bot and Automation Domain

The bot layer provides self-service and triage capabilities. A `Bot` is configured with a `BotFlow` (conversation script) containing `BotIntent` nodes that the NLP classifier resolves. Each customer interaction spawns a `BotSession`. `AutomationRule` objects implement conditional business logic with `AutomationCondition` guards and `AutomationAction` executors. `CannedResponse` objects provide agent shortcuts.

```mermaid
classDiagram
    class Bot {
        +UUID id
        +UUID organizationId
        +String name
        +String description
        +BotType type
        +String nlpProvider
        +String nlpModelId
        +Float confidenceThreshold
        +UUID defaultHandoffQueueId
        +Boolean isActive
        +String welcomeMessage
        +String fallbackMessage
        +DateTime createdAt
        +activate() void
        +deactivate() void
        +test(message String) BotTestResult
        +getActiveSessionCount() Int
        +retrain() void
    }

    class BotFlow {
        +UUID id
        +UUID botId
        +String name
        +String description
        +Boolean isDefault
        +String entryIntentId
        +Map~String,Object~ flowJson
        +Int version
        +Boolean isActive
        +DateTime publishedAt
        +publish() void
        +rollback(version Int) void
        +addIntent(intent BotIntent) void
        +getEntryIntent() BotIntent
        +validate() List~String~
    }

    class BotIntent {
        +UUID id
        +UUID flowId
        +String intentName
        +String displayName
        +List~String~ trainingPhrases
        +List~String~ responseTemplates
        +String nextIntentId
        +String fallbackIntentId
        +Boolean triggersHandoff
        +Map~String,Object~ parameters
        +Float minConfidence
        +addTrainingPhrase(phrase String) void
        +removeTrainingPhrase(phrase String) void
        +addResponse(template String) void
        +getRandomResponse() String
    }

    class BotSession {
        +UUID id
        +UUID botId
        +UUID contactId
        +UUID channelId
        +BotSessionStatus status
        +UUID currentIntentId
        +List~BotTurn~ turns
        +Map~String,Object~ context
        +UUID handoffTicketId
        +DateTime startedAt
        +DateTime lastActivityAt
        +DateTime endedAt
        +Int turnCount
        +processMessage(text String) BotResponse
        +initiateHandoff(reason String) void
        +end(reason String) void
        +getTranscript() String
        +setContextVariable(key String, value Object) void
        +getContextVariable~T~(key String) T
    }

    class AutomationRule {
        +UUID id
        +UUID organizationId
        +String name
        +String description
        +AutomationTrigger trigger
        +ConditionOperator conditionOperator
        +List~AutomationCondition~ conditions
        +List~AutomationAction~ actions
        +Int executionOrder
        +Boolean stopOnMatch
        +Boolean isActive
        +Int executionCount
        +DateTime lastExecutedAt
        +DateTime createdAt
        +evaluate(context Map~String,Object~) Boolean
        +execute(context Map~String,Object~) List~AutomationResult~
        +activate() void
        +deactivate() void
    }

    class AutomationCondition {
        +UUID id
        +UUID ruleId
        +String field
        +ConditionOperator operator
        +String value
        +ConditionType conditionType
        +Int groupId
        +evaluate(context Map~String,Object~) Boolean
        +validate() Boolean
    }

    class AutomationAction {
        +UUID id
        +UUID ruleId
        +AutomationActionType actionType
        +Map~String,Object~ parameters
        +Int executionOrder
        +execute(context Map~String,Object~) AutomationResult
        +validate() Boolean
        +getDescription() String
    }

    class CannedResponse {
        +UUID id
        +UUID organizationId
        +UUID teamId
        +UUID createdByAgentId
        +String shortCode
        +String title
        +String bodyText
        +String bodyHtml
        +List~String~ tags
        +Boolean isShared
        +Int usageCount
        +DateTime createdAt
        +DateTime updatedAt
        +render(variables Map~String,String~) String
        +incrementUsage() void
        +clone() CannedResponse
    }

    Bot "1" *-- "1..*" BotFlow : has
    BotFlow "1" *-- "1..*" BotIntent : contains
    Bot "1" --> "0..*" BotSession : runs
    BotSession "1" --> "0..*" BotIntent : navigates
    AutomationRule "1" *-- "1..*" AutomationCondition : guarded by
    AutomationRule "1" *-- "1..*" AutomationAction : executes
    BotSession "0..1" --> "0..1" Ticket : escalates to
```

---

## Diagram 5 — Knowledge Base Domain

The Knowledge Base (KB) subsystem supports agent and bot-assisted self-service. A `KnowledgeBase` scopes articles per organisation and language. `KBArticle` is the content entity, versioned via `KBArticleVersion` snapshots. `KBArticleFeedback` captures per-article reader sentiment. `KBSearchQuery` records search telemetry. `KBSuggestion` models AI-powered article recommendations that the bot and ticket form surface.

```mermaid
classDiagram
    class KnowledgeBase {
        +UUID id
        +UUID organizationId
        +String name
        +String slug
        +String description
        +String language
        +Boolean isPublic
        +String customDomain
        +String theme
        +Boolean isActive
        +DateTime createdAt
        +publish() void
        +unpublish() void
        +getArticleCount() Int
        +getPublishedArticleCount() Int
        +search(query String, filters Map) List~KBSearchResult~
        +getCategories() List~KBCategory~
    }

    class KBArticle {
        +UUID id
        +UUID knowledgeBaseId
        +UUID categoryId
        +UUID authorAgentId
        +UUID lastEditedByAgentId
        +String title
        +String slug
        +String summary
        +String bodyMarkdown
        +String bodyHtml
        +ArticleStatus status
        +Int currentVersion
        +List~String~ tags
        +List~String~ keywords
        +Boolean isFeatured
        +Int viewCount
        +Float avgRating
        +Int ratingCount
        +DateTime publishedAt
        +DateTime lastUpdatedAt
        +DateTime createdAt
        +publish() void
        +archive() void
        +createDraft() KBArticle
        +saveVersion(note String) KBArticleVersion
        +getVersionHistory() List~KBArticleVersion~
        +addFeedback(feedback KBArticleFeedback) void
        +getRelatedArticles(limit Int) List~KBArticle~
        +generateVectorEmbedding() Float[]
    }

    class KBArticleVersion {
        +UUID id
        +UUID articleId
        +Int versionNumber
        +UUID savedByAgentId
        +String title
        +String bodyMarkdown
        +String changeNote
        +DateTime savedAt
        +restore() void
        +diff(other KBArticleVersion) String
    }

    class KBArticleFeedback {
        +UUID id
        +UUID articleId
        +UUID contactId
        +FeedbackType type
        +Int rating
        +String comment
        +DateTime submittedAt
        +String sessionId
        +isPositive() Boolean
    }

    class KBSearchQuery {
        +UUID id
        +UUID organizationId
        +UUID knowledgeBaseId
        +String queryText
        +UUID contactId
        +UUID agentId
        +Int resultsReturned
        +Boolean resultClicked
        +UUID clickedArticleId
        +DateTime queriedAt
        +String sessionId
        +SearchChannel channel
        +Boolean handoffTriggered
        +getClickThroughRate() Float
    }

    class KBSuggestion {
        +UUID id
        +UUID ticketId
        +UUID articleId
        +Float confidenceScore
        +SuggestionSource source
        +SuggestionStatus status
        +UUID dismissedByAgentId
        +DateTime createdAt
        +DateTime actedAt
        +accept() void
        +dismiss(reason String) void
        +getArticle() KBArticle
        +wasHelpful() Boolean
    }

    KnowledgeBase "1" *-- "0..*" KBArticle : contains
    KBArticle "1" *-- "0..*" KBArticleVersion : versioned as
    KBArticle "1" o-- "0..*" KBArticleFeedback : receives
    KBArticle "1" --> "0..*" KBSuggestion : surfaced as
    KnowledgeBase "1" --> "0..*" KBSearchQuery : records
    Ticket "1" --> "0..*" KBSuggestion : presented with
```

---

## Diagram 6 — Service Layer Classes

This diagram documents the service-layer interfaces and their primary concrete implementations. It captures the dependency inversion principle applied across all domain services: controllers depend on interfaces; concrete classes are injected at runtime.

```mermaid
classDiagram
    class ITicketService {
        <<interface>>
        +createTicket(cmd CreateTicketCommand) Ticket
        +getTicket(ticketId UUID) Ticket
        +updateTicket(cmd UpdateTicketCommand) Ticket
        +assignTicket(ticketId UUID, agentId UUID) void
        +resolveTicket(ticketId UUID, wrapCodeId UUID) void
        +closeTicket(ticketId UUID) void
        +reopenTicket(ticketId UUID, reason String) void
        +mergeTickets(primaryId UUID, duplicateId UUID) void
        +addMessage(cmd AddMessageCommand) Message
        +searchTickets(query TicketSearchQuery) Page~Ticket~
    }

    class TicketServiceImpl {
        -TicketRepository ticketRepo
        -ThreadRepository threadRepo
        -ContactService contactService
        -SLAService slaService
        -RoutingEngine routingEngine
        -EventPublisher eventPublisher
        -AuditService auditService
        +createTicket(cmd CreateTicketCommand) Ticket
        +getTicket(ticketId UUID) Ticket
        +updateTicket(cmd UpdateTicketCommand) Ticket
        +assignTicket(ticketId UUID, agentId UUID) void
        +resolveTicket(ticketId UUID, wrapCodeId UUID) void
        -validateStatusTransition(from TicketStatus, to TicketStatus) void
        -publishEvent(event DomainEvent) void
        -enforceBusinessRules(ticket Ticket) void
    }

    class IRoutingEngine {
        <<interface>>
        +route(ticket Ticket) RoutingDecision
        +getEligibleAgents(queueId UUID, skills List~String~) List~Agent~
        +selectAgent(agents List~Agent~, strategy RoutingStrategy) Agent
        +rebalance(queueId UUID) void
    }

    class SkillBasedRoutingEngine {
        -AgentSkillRepository skillRepo
        -AgentAvailabilityService availabilityService
        -QueueService queueService
        -LoadBalancer loadBalancer
        +route(ticket Ticket) RoutingDecision
        +getEligibleAgents(queueId UUID, skills List~String~) List~Agent~
        +selectAgent(agents List~Agent~, strategy RoutingStrategy) Agent
        -matchSkills(required List~String~, agentSkills List~AgentSkill~) Float
        -checkAvailability(agent Agent) Boolean
        -calculateLoad(agent Agent) Float
    }

    class RoundRobinRoutingEngine {
        -AgentRepository agentRepo
        -AssignmentRepository assignmentRepo
        -RoundRobinStateStore stateStore
        +route(ticket Ticket) RoutingDecision
        +getEligibleAgents(queueId UUID, skills List~String~) List~Agent~
        +selectAgent(agents List~Agent~, strategy RoutingStrategy) Agent
        -getNextAgent(agents List~Agent~) Agent
        -updatePointer(queueId UUID, agentIndex Int) void
    }

    class ISLAService {
        <<interface>>
        +startClock(ticket Ticket, policy SLAPolicy) SLAClock
        +pauseClock(ticketId UUID, clockType SLAClockType) void
        +resumeClock(ticketId UUID, clockType SLAClockType) void
        +stopClock(ticketId UUID, clockType SLAClockType) void
        +checkBreaches(at DateTime) List~SLABreach~
        +getActiveClocksNearBreach(warningMinutes Int) List~SLAClock~
        +recalculate(ticketId UUID) void
    }

    class SLAServiceImpl {
        -SLAClockRepository clockRepo
        -SLAPolicyRepository policyRepo
        -BusinessHoursService businessHoursService
        -EventPublisher eventPublisher
        -MetricsRegistry metricsRegistry
        +startClock(ticket Ticket, policy SLAPolicy) SLAClock
        +pauseClock(ticketId UUID, clockType SLAClockType) void
        +resumeClock(ticketId UUID, clockType SLAClockType) void
        +checkBreaches(at DateTime) List~SLABreach~
        -calculateDeadline(policy SLAPolicy, from DateTime) DateTime
        -applyBusinessHours(deadline DateTime, schedule BusinessHoursSchedule) DateTime
    }

    class IBotEngine {
        <<interface>>
        +startSession(contactId UUID, channelId UUID, botId UUID) BotSession
        +processMessage(sessionId UUID, message String) BotResponse
        +initiateHandoff(sessionId UUID, reason String) HandoffResult
        +endSession(sessionId UUID, reason String) void
        +getSession(sessionId UUID) BotSession
    }

    class NLPBotEngine {
        -BotSessionRepository sessionRepo
        -NLPClassifier nlpClassifier
        -IntentRouter intentRouter
        -KBSearchService kbSearch
        -HandoffCoordinator handoffCoordinator
        -BotAuditLogger auditLogger
        +startSession(contactId UUID, channelId UUID, botId UUID) BotSession
        +processMessage(sessionId UUID, message String) BotResponse
        +initiateHandoff(sessionId UUID, reason String) HandoffResult
        -classifyIntent(text String, botId UUID) IntentClassification
        -generateResponse(intent BotIntent, context Map) String
        -evaluateHandoffConditions(session BotSession) Boolean
    }

    ITicketService <|.. TicketServiceImpl : implements
    IRoutingEngine <|.. SkillBasedRoutingEngine : implements
    IRoutingEngine <|.. RoundRobinRoutingEngine : implements
    ISLAService <|.. SLAServiceImpl : implements
    IBotEngine <|.. NLPBotEngine : implements
    TicketServiceImpl --> IRoutingEngine : uses
    TicketServiceImpl --> ISLAService : uses
    NLPBotEngine --> ITicketService : creates tickets via
```

---

*Last updated: 2025 | Version: 1.0 | Owner: Platform Engineering*
