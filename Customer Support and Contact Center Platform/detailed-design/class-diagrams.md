# Class Diagrams

```mermaid
classDiagram
    class CustomerProfile {
      +UUID id
      +String email
      +String phone
      +String segment
      +updateContactInfo()
    }

    class Ticket {
      +UUID id
      +UUID customerId
      +TicketStatus status
      +Priority priority
      +String category
      +DateTime createdAt
      +assign(queueId)
      +escalate(reason)
      +resolve(code)
      +close()
    }

    class InteractionSession {
      +UUID id
      +UUID ticketId
      +ChannelType channel
      +SessionStatus status
      +start()
      +hold()
      +transfer(queueId)
      +end()
    }

    class SLAClock {
      +UUID id
      +UUID ticketId
      +Duration target
      +DateTime dueAt
      +start()
      +pause()
      +breach()
    }

    class Queue {
      +UUID id
      +String name
      +String skillRule
      +enqueue(ticketId)
      +dequeue()
    }

    class Escalation {
      +UUID id
      +UUID ticketId
      +EscalationLevel level
      +String reason
      +open()
      +close()
    }

    class KnowledgeArticle {
      +UUID id
      +String title
      +String topic
      +ArticleStatus status
      +publish()
      +archive()
    }

    CustomerProfile "1" --> "many" Ticket
    Ticket "1" --> "many" InteractionSession
    Ticket "1" --> "1" SLAClock
    Queue "1" --> "many" Ticket
    Ticket "0..many" --> "0..many" Escalation
    Ticket "0..many" --> "0..many" KnowledgeArticle : references
```

## Class Model Narrative for Operations
Representative classes and invariants:
- `Conversation`: aggregate root; owns interaction timeline.
- `QueueAssignment`: value object linking skill profile and priority score.
- `SlaPolicy` and `SlaClock`: policy/instance split for versioned rule execution.
- `EscalationRecord`: immutable escalation decision snapshot.
- `AuditEvent`: cryptographically signed event envelope.

```mermaid
classDiagram
    Conversation "1" --> "many" QueueAssignment
    Conversation "1" --> "many" AuditEvent
    Conversation "1" --> "many" SlaClock
    SlaClock --> SlaPolicy
    Conversation "1" --> "many" EscalationRecord
```

Class methods that mutate state must emit both domain events and audit events, ensuring replay + compliance parity.

Operational coverage note: this artifact also specifies omnichannel and incident controls for this design view.
