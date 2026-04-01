# C4 Code Diagrams - Restaurant Management System

## Overview

This document presents Level 4 C4 diagrams — the code-level view of key services and modules in the Restaurant Management System. Where the C4 component diagrams (Level 3) show which components exist within each service container, these diagrams show the internal class and module structure, key design patterns applied, and how the modules relate to each other at the code level.

The system is built as a modular monolith with clear domain package boundaries. Each domain package (orders, kitchen, billing, inventory, seating, etc.) follows the same internal structure: entities, commands, queries, events, repositories, and policy hooks. The API application and worker application are thin shells that wire these domain packages together via NestJS dependency injection.

---

## Level 4: Code Structure — Order Service

The Order Service is the most critical domain package. It manages the full lifecycle of a restaurant order from draft creation through billing. It uses the Aggregate pattern, the Outbox pattern for reliable event publishing, and optimistic locking for concurrent write safety.

```mermaid
classDiagram
    class OrderAggregate {
        +id: OrderId
        +branchId: BranchId
        +tableId: TableId
        +waiterId: StaffId
        +status: OrderStatus
        +version: number
        +items: OrderLine[]
        +courseGroups: CourseGroup[]
        +events: DomainEvent[]
        +addLine(cmd: AddLineCommand): Result
        +removeLine(lineId: LineId): Result
        +updateLineQuantity(lineId: LineId, qty: number): Result
        +submit(cmd: SubmitCommand): Result
        +void(cmd: VoidCommand): Result
        +markServed(lineId: LineId): Result
        +raiseEvent(event: DomainEvent): void
        -validateAvailability(items: OrderLine[]): ValidationResult
        -validateModifiers(items: OrderLine[]): ValidationResult
        -applyTaxPolicy(context: TaxContext): TaxBreakdown
    }

    class OrderLine {
        +id: LineId
        +menuItemId: MenuItemId
        +menuItemName: string
        +quantity: number
        +unitPrice: Money
        +modifiers: AppliedModifier[]
        +courseNo: number
        +seatNo: number
        +notes: string
        +status: LineStatus
        +kitchenTicketId: TicketId
        +calculateSubtotal(): Money
        +applyModifierPrices(): Money
    }

    class OrderRepository {
        <<interface>>
        +findById(id: OrderId): Promise~Order~
        +findByBranchAndStatus(branchId: BranchId, status: OrderStatus[]): Promise~Order[]~
        +save(order: OrderAggregate): Promise~void~
        +saveWithOutbox(order: OrderAggregate, events: DomainEvent[]): Promise~void~
    }

    class SubmitOrderCommandHandler {
        -orderRepo: OrderRepository
        -availabilityService: MenuAvailabilityService
        -taxService: TaxCalculationService
        -outboxWriter: OutboxWriter
        +execute(cmd: SubmitOrderCommand): Promise~OrderId~
        -acquireLock(orderId: OrderId): Promise~OrderLock~
        -releaseLock(lock: OrderLock): Promise~void~
    }

    class OrderQueryService {
        -readDb: ReadConnection
        +getOrderDetail(id: OrderId): Promise~OrderDetailView~
        +listBranchOrders(branchId: BranchId, filter: OrderFilter): Promise~PagedResult~
        +getOrderTimeline(id: OrderId): Promise~TimelineEvent[]~
    }

    class OutboxWriter {
        -db: TransactionClient
        +writeEvents(orderId: OrderId, events: DomainEvent[]): Promise~void~
    }

    class OutboxRelay {
        -outboxRepo: OutboxRepository
        -eventBus: EventBus
        +pollAndPublish(): Promise~void~
        -markPublished(eventId: string): Promise~void~
    }

    class TaxCalculationService {
        -taxRuleRepo: TaxRuleRepository
        +calculate(items: OrderLine[], branchId: BranchId): TaxBreakdown
        +applyDiscounts(breakdown: TaxBreakdown, discounts: Discount[]): TaxBreakdown
    }

    class MenuAvailabilityService {
        -menuRepo: MenuRepository
        -cache: RedisClient
        +checkAvailability(items: OrderLine[], branchId: BranchId): AvailabilityResult
        +getAvailableItems(branchId: BranchId): Promise~MenuItem[]~
    }

    OrderAggregate "1" *-- "many" OrderLine
    SubmitOrderCommandHandler --> OrderRepository
    SubmitOrderCommandHandler --> MenuAvailabilityService
    SubmitOrderCommandHandler --> TaxCalculationService
    SubmitOrderCommandHandler --> OutboxWriter
    OutboxWriter --> OutboxRelay : triggers
    OrderQueryService --> OrderAggregate
```

### Order Status State Machine
```mermaid
stateDiagram-v2
    [*] --> draft : Create order
    draft --> submitted : submit() [items valid, availability confirmed]
    draft --> voided : void() [before submit]
    submitted --> in_preparation : Kitchen acknowledges ticket
    in_preparation --> ready : All lines bumped on KDS
    ready --> served : Waiter confirms serve
    served --> billed : Cashier generates bill
    billed --> settled : Payment captured
    billed --> voided : void() [manager approval required]
    settled --> [*]
    voided --> [*]
```

---

## Level 4: Code Structure — Billing Service

The Billing Service handles check generation, split strategies, multi-tender payment capture, and reconciliation. It enforces deterministic rounding and preserves an immutable financial ledger.

```mermaid
classDiagram
    class BillAggregate {
        +id: BillId
        +orderId: OrderId
        +branchId: BranchId
        +status: BillStatus
        +subChecks: SubCheck[]
        +tenders: TenderEntry[]
        +totalGross: Money
        +totalTax: Money
        +totalNet: Money
        +totalPaid: Money
        +splitBySeats(seats: SeatId[]): Result
        +splitByItems(groups: ItemGroup[]): Result
        +splitByPercentage(splits: PercentageSplit[]): Result
        +captureTender(entry: TenderEntry): Result
        +void(cmd: VoidBillCommand): Result
        +isFullyPaid(): boolean
        -allocateRounding(subChecks: SubCheck[]): void
    }

    class SubCheck {
        +id: SubCheckId
        +billId: BillId
        +seatNos: number[]
        +lines: BillLine[]
        +subtotal: Money
        +taxAmount: Money
        +discountAmount: Money
        +total: Money
        +tipAmount: Money
        +tenders: TenderEntry[]
        +status: SubCheckStatus
        +addTip(amount: Money): void
        +getBalance(): Money
    }

    class TenderEntry {
        +id: TenderId
        +type: TenderType
        +amount: Money
        +referenceId: string
        +capturedAt: Date
        +gatewayResponse: PaymentGatewayResponse
    }

    class PaymentCaptureService {
        -gateway: PaymentGateway
        -idempotencyStore: IdempotencyStore
        +capture(intent: PaymentIntent, key: IdempotencyKey): Promise~CaptureResult~
        +void(intentId: string, key: IdempotencyKey): Promise~VoidResult~
        +refund(intentId: string, amount: Money, key: IdempotencyKey): Promise~RefundResult~
    }

    class IdempotencyStore {
        -redis: RedisClient
        +check(key: string): Promise~IdempotencyRecord | null~
        +record(key: string, response: unknown, ttl: number): Promise~void~
    }

    class SettlementLedger {
        +id: LedgerEntryId
        +branchId: BranchId
        +billId: BillId
        +drawerSessionId: DrawerSessionId
        +tenderType: TenderType
        +amount: Money
        +direction: 'debit' | 'credit'
        +createdAt: Date
    }

    class DrawerSession {
        +id: DrawerSessionId
        +branchId: BranchId
        +staffId: StaffId
        +openedAt: Date
        +closedAt: Date
        +openingFloat: Money
        +expectedCash: Money
        +actualCash: Money
        +variance: Money
        +status: DrawerStatus
        +close(actualCash: Money): CloseResult
    }

    BillAggregate "1" *-- "many" SubCheck
    BillAggregate "1" *-- "many" TenderEntry
    SubCheck "1" *-- "many" TenderEntry
    PaymentCaptureService --> IdempotencyStore
    PaymentCaptureService --> SettlementLedger : writes
    DrawerSession "1" *-- "many" SettlementLedger
```

---

## Level 4: Code Structure — Kitchen Orchestrator

The Kitchen Orchestrator is responsible for receiving submitted orders, routing individual lines to the correct kitchen stations, managing ticket lifecycle on the KDS, and propagating delays back to front-of-house.

```mermaid
classDiagram
    class KitchenOrchestrator {
        -stationRouter: StationRouter
        -ticketRepo: KitchenTicketRepository
        -kdsPublisher: KdsPublisher
        -slaTimer: SlaTimerService
        +handleOrderSubmitted(event: OrderSubmittedEvent): Promise~void~
        +handleOrderLineVoided(event: OrderLineVoidedEvent): Promise~void~
        +handleRefireRequested(event: RefireRequestedEvent): Promise~void~
        -groupByCourseAndStation(lines: OrderLine[]): TicketGroup[]
        -createTickets(groups: TicketGroup[]): KitchenTicket[]
    }

    class KitchenTicket {
        +id: TicketId
        +orderId: OrderId
        +stationId: StationId
        +courseNo: number
        +lines: TicketLine[]
        +status: TicketStatus
        +priority: TicketPriority
        +firedAt: Date
        +slaDeadline: Date
        +bumpedAt: Date
        +refireOf: TicketId
        +bump(staffId: StaffId): Result
        +recall(): Result
        +refire(reason: RefireReason, staffId: StaffId): Result
        +isOverSla(): boolean
    }

    class StationRouter {
        -routingRules: RoutingRule[]
        -stationRepo: StationRepository
        +resolveStation(item: OrderLine, branchId: BranchId): StationId
        +getFallbackStation(stationId: StationId): StationId | null
        +isStationActive(stationId: StationId): boolean
    }

    class RoutingRule {
        +id: RuleId
        +branchId: BranchId
        +itemCategoryId: CategoryId
        +targetStationId: StationId
        +fallbackStationId: StationId
        +priority: number
        +isActive: boolean
        +matches(item: OrderLine): boolean
    }

    class KdsPublisher {
        -websocketHub: WebSocketHub
        -fallbackPoller: FallbackPoller
        +publishTicket(ticket: KitchenTicket): Promise~void~
        +publishTicketUpdate(ticket: KitchenTicket): Promise~void~
        +publishTicketVoid(ticketId: TicketId): Promise~void~
        -getStationSubscribers(stationId: StationId): WebSocketClient[]
    }

    class SlaTimerService {
        -redis: RedisClient
        -eventBus: EventBus
        +startTimer(ticketId: TicketId, deadline: Date): void
        +cancelTimer(ticketId: TicketId): void
        +onSlaBreached(ticketId: TicketId): void
    }

    class CourseFireController {
        -ticketRepo: KitchenTicketRepository
        -orchestrator: KitchenOrchestrator
        +holdCourse(orderId: OrderId, courseNo: number): Result
        +releaseCourse(orderId: OrderId, courseNo: number, staffId: StaffId): Result
        +autoFireCourse(orderId: OrderId, courseNo: number): void
    }

    KitchenOrchestrator --> StationRouter
    KitchenOrchestrator --> KdsPublisher
    KitchenOrchestrator --> SlaTimerService
    KitchenOrchestrator --> CourseFireController
    StationRouter "1" *-- "many" RoutingRule
    KitchenTicket --> SlaTimerService : triggers
```

---

## Module Dependency Graph

This diagram shows the allowed dependency directions between domain packages. Dependencies only flow downward or toward shared utilities. No circular dependencies are permitted.

```mermaid
flowchart TD
    api[apps/api] --> orders[domain/orders]
    api --> billing[domain/billing]
    api --> kitchen[domain/kitchen]
    api --> seating[domain/seating]
    api --> menu[domain/menu]
    api --> inventory[domain/inventory]
    api --> procurement[domain/procurement]
    api --> workforce[domain/workforce]
    api --> access[domain/access]
    api --> reporting[domain/reporting]

    worker[apps/worker] --> kitchen
    worker --> inventory
    worker --> billing
    worker --> reporting
    worker --> workforce

    kitchen --> orders
    billing --> orders
    inventory --> menu
    procurement --> inventory
    reporting --> orders
    reporting --> billing
    reporting --> inventory
    reporting --> kitchen

    orders --> menu
    orders --> access
    billing --> access
    kitchen --> access
    seating --> access

    orders --> shared[packages/shared]
    billing --> shared
    kitchen --> shared
    inventory --> shared
    seating --> shared
    menu --> shared
    access --> shared

    style shared fill:#f9f,stroke:#333
    style api fill:#bbf,stroke:#333
    style worker fill:#bbf,stroke:#333
```

---

## Key Design Patterns

### Repository Pattern

Each domain aggregate has a typed repository interface defined in the domain package. The implementation lives in the infrastructure layer (TypeORM adapters). This keeps domain logic free of ORM concerns.

```typescript
// Domain interface (packages/domain/orders/src/repositories/order.repository.ts)
export interface IOrderRepository {
  findById(id: OrderId, options?: FindOptions): Promise<Order | null>;
  findByBranchAndStatus(
    branchId: BranchId,
    statuses: OrderStatus[],
    pagination: Pagination,
  ): Promise<PagedResult<Order>>;
  save(order: Order, trx?: TransactionClient): Promise<void>;
}

// Infrastructure implementation (apps/api/src/infrastructure/typeorm/order.repository.ts)
@Injectable()
export class TypeOrmOrderRepository implements IOrderRepository {
  constructor(
    @InjectRepository(OrderEntity)
    private readonly repo: Repository<OrderEntity>,
  ) {}

  async findById(id: OrderId): Promise<Order | null> {
    const entity = await this.repo.findOne({
      where: { id },
      relations: ['lines', 'lines.modifiers'],
    });
    return entity ? OrderMapper.toDomain(entity) : null;
  }
}
```

### CQRS Pattern

Commands mutate state through aggregates; queries read from optimised read models.

```typescript
// Command side — goes through domain aggregate
@CommandHandler(SubmitOrderCommand)
export class SubmitOrderHandler implements ICommandHandler<SubmitOrderCommand> {
  async execute(cmd: SubmitOrderCommand): Promise<void> {
    const order = await this.orderRepo.findById(cmd.orderId);
    const result = order.submit(cmd);
    if (!result.ok) throw result.error;
    await this.orderRepo.saveWithOutbox(order, order.consumeEvents());
  }
}

// Query side — reads from denormalised projection table
@QueryHandler(OrderDetailQuery)
export class OrderDetailHandler implements IQueryHandler<OrderDetailQuery> {
  async execute(query: OrderDetailQuery): Promise<OrderDetailView> {
    return this.readDb.query(
      `SELECT * FROM v_order_detail WHERE id = $1 AND branch_id = $2`,
      [query.orderId, query.branchId],
    );
  }
}
```

### Outbox Pattern

Domain events are written atomically with the aggregate state change into an `outbox_events` table. A background relay polls and publishes them to RabbitMQ, guaranteeing at-least-once delivery without distributed transactions.

```mermaid
sequenceDiagram
    participant Handler as Command Handler
    participant DB as PostgreSQL
    participant Relay as Outbox Relay
    participant MQ as RabbitMQ

    Handler->>DB: BEGIN TRANSACTION
    Handler->>DB: UPDATE orders SET status = 'submitted'
    Handler->>DB: INSERT INTO outbox_events (payload, topic)
    Handler->>DB: COMMIT

    loop Every 100ms
        Relay->>DB: SELECT * FROM outbox_events WHERE published = false LIMIT 100
        Relay->>MQ: Publish events
        Relay->>DB: UPDATE outbox_events SET published = true
    end
```

### Saga Pattern (Order Fulfilment Saga)

Long-running processes that span multiple services are coordinated with sagas. The order fulfilment saga listens for domain events and issues compensating commands on failure.

```mermaid
flowchart TD
    A[OrderSubmitted] --> B[Route tickets to stations]
    B --> C{All tickets routed?}
    C -- Yes --> D[Start SLA timers]
    D --> E[Await ticket bumps]
    E --> F{All tickets bumped?}
    F -- Yes --> G[Notify front-of-house: Ready]
    F -- No --> H{SLA breached?}
    H -- Yes --> I[Emit SlaBreachEvent → alert FOH]
    H -- No --> E
    C -- No --> J[Emit TicketRoutingFailedEvent]
    J --> K[Cancel remaining tickets]
    K --> L[Emit OrderFulfilmentFailedEvent → alert manager]
```

---

## Database Access Layer

### Connection Pool Configuration
```typescript
// apps/api/src/config/database.config.ts
export const databaseConfig: TypeOrmModuleOptions = {
  type: 'postgres',
  url: process.env.DATABASE_URL,
  pool: {
    min: parseInt(process.env.DATABASE_POOL_MIN ?? '2'),
    max: parseInt(process.env.DATABASE_POOL_MAX ?? '20'),
  },
  extra: {
    statement_timeout: 30_000,     // 30 seconds max per statement
    idle_in_transaction_session_timeout: 60_000,
  },
  migrations: ['dist/migrations/*.js'],
  migrationsRun: false,            // Always run migrations explicitly, not on startup
  logging: process.env.NODE_ENV === 'development' ? 'all' : ['error', 'warn'],
};
```

### Transaction Management
```typescript
// Use explicit transactions for operations that span multiple writes
async function submitOrderWithOutbox(
  order: Order,
  events: DomainEvent[],
  dataSource: DataSource,
): Promise<void> {
  await dataSource.transaction(async (trx) => {
    await trx.save(OrderEntity, OrderMapper.toEntity(order));
    await trx.insert(OutboxEventEntity, events.map(OutboxMapper.toEntity));
  });
  // Transaction committed — outbox relay will pick up events asynchronously
}
```

### Read Model Projections
```sql
-- Materialised view for fast order dashboard queries
CREATE MATERIALIZED VIEW v_branch_order_summary AS
SELECT
  o.branch_id,
  o.status,
  COUNT(*)                         AS order_count,
  SUM(o.total_amount)              AS total_revenue,
  AVG(EXTRACT(EPOCH FROM (o.submitted_at - o.created_at))) AS avg_draft_seconds
FROM orders o
WHERE o.deleted_at IS NULL
GROUP BY o.branch_id, o.status;

-- Refresh every 5 minutes via cron job
REFRESH MATERIALIZED VIEW CONCURRENTLY v_branch_order_summary;
```
