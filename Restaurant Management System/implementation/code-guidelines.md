# Code Guidelines - Restaurant Management System

## Overview and Philosophy

These guidelines define the coding standards, architectural conventions, and development practices for the Restaurant Management System (RMS). All contributors — backend engineers, frontend engineers, and DevOps — are expected to follow these standards consistently.

**Core Principles:**
1. **Correctness first** — Financial and inventory calculations must be deterministic and auditable. Prefer explicit over clever.
2. **Branch scoping everywhere** — Every data read and write must be scoped to the correct branch. Missing branch scope is a security defect, not a style issue.
3. **Immutability for financial data** — Billing records, stock ledger entries, and audit logs are append-only. Never update or delete them; issue compensating entries instead.
4. **Fail fast, recover gracefully** — Validate inputs at the boundary, use domain errors for expected failures, and never silently swallow exceptions.
5. **Observable by default** — Structured logs, distributed traces, and metrics are not optional add-ons. Every service must emit them from day one.

---

## Project Structure

```text
restaurant-platform/
├── apps/
│   ├── api/                      # Main NestJS HTTP + WebSocket API
│   │   ├── src/
│   │   │   ├── main.ts           # Bootstrap and app factory
│   │   │   ├── app.module.ts     # Root module
│   │   │   ├── config/           # Config service, validation schema
│   │   │   ├── health/           # Health check endpoints
│   │   │   └── modules/          # Feature modules (thin: controllers + wiring)
│   │   └── test/                 # API-level integration tests
│   ├── worker/                   # Background job processors (queues, crons)
│   │   ├── src/
│   │   │   ├── main.ts
│   │   │   ├── processors/       # One file per queue consumer
│   │   │   └── schedulers/       # Cron-based scheduled jobs
│   │   └── test/
│   ├── staff-pos/                # React 18 staff POS application
│   │   ├── src/
│   │   │   ├── features/         # Feature-sliced: orders/, tables/, billing/
│   │   │   ├── components/       # Shared UI components
│   │   │   ├── hooks/            # Custom React hooks
│   │   │   ├── stores/           # Zustand or Redux Toolkit state
│   │   │   └── api/              # API client (React Query)
│   ├── kitchen-display/          # KDS React application
│   ├── back-office/              # Management + reporting React application
│   └── guest-touchpoints/        # QR menu, reservation widget
├── packages/
│   ├── domain/
│   │   ├── access/               # Auth, RBAC, session management
│   │   │   ├── src/
│   │   │   │   ├── entities/
│   │   │   │   ├── commands/
│   │   │   │   ├── queries/
│   │   │   │   ├── events/
│   │   │   │   ├── policies/     # Permission evaluation logic
│   │   │   │   └── index.ts
│   │   │   └── test/
│   │   ├── seating/              # Tables, reservations, waitlist
│   │   ├── menu/                 # Menu items, modifiers, pricing, availability
│   │   ├── orders/               # Order aggregate, line items, state machine
│   │   ├── kitchen/              # Ticket routing, station management, KDS
│   │   ├── inventory/            # Stock ledger, recipes, depletion, counts
│   │   ├── procurement/          # Suppliers, POs, GRNs
│   │   ├── billing/              # Checks, split, tender, settlement
│   │   ├── workforce/            # Shifts, attendance, scheduling
│   │   └── reporting/            # Projection models, read models, exports
│   ├── shared/
│   │   ├── types/                # Shared enums, interfaces, value objects
│   │   ├── errors/               # Domain error hierarchy
│   │   ├── events/               # Shared event contracts
│   │   ├── utils/                # Date, money, rounding, string utilities
│   │   └── testing/              # Test helpers, fixtures, factory builders
│   └── ui/
│       ├── components/           # Design system components
│       ├── icons/
│       └── tokens/               # Design tokens (colours, spacing, typography)
├── infra/
│   ├── terraform/                # Cloud infrastructure as code
│   ├── kubernetes/               # K8s manifests and Helm charts
│   ├── docker/                   # Dockerfiles per service
│   └── scripts/                  # Deployment and maintenance scripts
└── tests/
    ├── e2e/                      # Playwright E2E test suites
    ├── load/                     # k6 load test scripts
    └── contract/                 # Pact consumer/provider tests
```

---

## Naming Conventions

### Files and Directories
| Artifact | Convention | Example |
|----------|-----------|---------|
| Source files | `kebab-case.ts` | `order-aggregate.ts` |
| Test files | `*.spec.ts` (unit), `*.test.ts` (integration) | `order-aggregate.spec.ts` |
| Entity files | `<entity-name>.entity.ts` | `order.entity.ts` |
| Command files | `<action>-<noun>.command.ts` | `submit-order.command.ts` |
| Query files | `<noun>-<scope>.query.ts` | `order-detail.query.ts` |
| Event files | `<noun>-<past-tense>.event.ts` | `order-submitted.event.ts` |
| DTO files | `<action>-<noun>.dto.ts` | `create-order.dto.ts` |
| Repository files | `<noun>.repository.ts` | `order.repository.ts` |
| Service files | `<noun>.service.ts` | `tax-calculation.service.ts` |
| Controller files | `<noun>.controller.ts` | `orders.controller.ts` |
| Migration files | `<timestamp>_<description>.ts` | `1700000001_add_order_version_column.ts` |

### Classes and Interfaces
```typescript
// Entities: PascalCase noun
class Order { }
class KitchenTicket { }

// Commands: PascalCase imperative phrase + Command suffix
class SubmitOrderCommand { }
class VoidBillCommand { }

// Events: PascalCase past tense + Event suffix
class OrderSubmittedEvent { }
class KitchenTicketBumpedEvent { }

// Queries: PascalCase + Query suffix
class OrderDetailQuery { }
class BranchActiveTablesQuery { }

// DTOs: PascalCase + Dto suffix
class CreateOrderDto { }
class UpdateModifierDto { }

// Interfaces: PascalCase with I prefix for contracts
interface IOrderRepository { }
interface ITaxCalculator { }

// Value objects: PascalCase noun
class Money { }
class TableReference { }
```

### Functions and Variables
```typescript
// Functions: camelCase verbs
function calculateOrderTax(order: Order): Money { }
function routeTicketToStation(ticket: KitchenTicket): Station { }

// Variables: camelCase nouns (descriptive, not abbreviated)
const branchId = 'b_123';               // ✅
const bid = 'b_123';                    // ❌ Too abbreviated
const activeOrderCount = orders.length; // ✅
const n = orders.length;                // ❌ Meaningless

// Booleans: use is/has/can/should prefix
const isOrderVoidable = checkVoidEligibility(order);
const hasUnsettledItems = check.items.some(i => !i.settled);
const canWaiterApply = rolePolicy.allows('discount:apply', staff.role);

// Constants: SCREAMING_SNAKE_CASE for module-level constants
const MAX_ORDER_LINE_COUNT = 100;
const IDEMPOTENCY_KEY_TTL_SECONDS = 86400;
const KITCHEN_SLA_DEFAULT_MINUTES = 20;
```

### Database Tables and Columns
```sql
-- Tables: snake_case plural nouns
orders, kitchen_tickets, stock_ledger_entries, staff_sessions

-- Columns: snake_case
branch_id, created_at, updated_at, deleted_at

-- Primary keys: always named 'id', UUID type
id UUID PRIMARY KEY DEFAULT gen_random_uuid()

-- Foreign keys: <referenced_table_singular>_id
order_id, branch_id, menu_item_id, station_id

-- Boolean columns: is_ or has_ prefix
is_voided, has_modifiers, is_active

-- Timestamp columns: _at suffix
created_at, updated_at, submitted_at, settled_at, fired_at

-- Status/type columns: snake_case, stored as varchar or enum
status, order_source, tender_type, movement_type

-- Soft delete: use deleted_at nullable timestamp (not is_deleted boolean)
deleted_at TIMESTAMPTZ NULL
```

---

## TypeScript Standards

### Strict Mode
All TypeScript projects must use strict mode with these `tsconfig.json` settings:
```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "exactOptionalPropertyTypes": true,
    "noPropertyAccessFromIndexSignature": true
  }
}
```

### Type Safety Rules
```typescript
// ✅ Use branded types for IDs to prevent accidental mixing
type BranchId = string & { readonly __brand: 'BranchId' };
type OrderId = string & { readonly __brand: 'OrderId' };
function getOrder(branchId: BranchId, orderId: OrderId): Promise<Order> { }

// ✅ Use discriminated unions for state
type OrderState =
  | { status: 'draft'; items: DraftItem[] }
  | { status: 'submitted'; submittedAt: Date; kitchenTicketId: string }
  | { status: 'voided'; voidedAt: Date; voidedBy: string; reason: string };

// ✅ Use Result type for operations that can fail predictably
type Result<T, E = DomainError> = { ok: true; value: T } | { ok: false; error: E };

// ❌ Never use any — use unknown and narrow with type guards
function processPayload(data: any) { }   // ❌
function processPayload(data: unknown) { // ✅
  if (isOrderPayload(data)) { }
}

// ✅ Use readonly for value objects and immutable data
interface MoneyValue {
  readonly amount: number;
  readonly currency: string;
}

// ❌ Do not use non-null assertions unless provably safe
const item = order.items[0]!;           // ❌ Can panic at runtime
const item = order.items.at(0);         // ✅ Returns undefined safely
if (!item) throw new DomainError(...);  // ✅ Explicit guard
```

### Async Patterns
```typescript
// ✅ Always handle async errors explicitly
const result = await orderRepo.findById(orderId);
if (!result) throw new OrderNotFoundError(orderId);

// ✅ Use Promise.all for independent async operations
const [order, table, staff] = await Promise.all([
  orderRepo.findById(orderId),
  tableRepo.findById(tableId),
  staffRepo.findById(staffId),
]);

// ❌ Avoid fire-and-forget async calls without error handling
doSomethingAsync(); // ❌ Errors are silently swallowed
void doSomethingAsync().catch(logger.error); // ✅ Explicit void + error capture
```

---

## API Design Standards

### Route Conventions
```
POST   /v1/branches/:branchId/orders                    # Create
GET    /v1/branches/:branchId/orders                    # List
GET    /v1/branches/:branchId/orders/:orderId           # Get one
PATCH  /v1/branches/:branchId/orders/:orderId           # Partial update
POST   /v1/branches/:branchId/orders/:orderId/submit    # State transition
POST   /v1/branches/:branchId/orders/:orderId/void      # State transition
DELETE /v1/branches/:branchId/orders/:orderId/lines/:lineId  # Remove line
```

### Response Envelope
```typescript
// Success — single resource
{
  "data": { "id": "ord_123", "status": "submitted", ... },
  "meta": { "requestId": "req_abc", "timestamp": "2024-01-15T12:00:00Z" }
}

// Success — collection
{
  "data": [...],
  "meta": {
    "requestId": "req_abc",
    "timestamp": "2024-01-15T12:00:00Z",
    "pagination": { "page": 1, "pageSize": 20, "total": 150 }
  }
}

// Error response
{
  "error": {
    "code": "ORDER_VERSION_CONFLICT",
    "message": "Order has been modified by another session. Refresh and retry.",
    "details": { "currentVersion": 5, "submittedVersion": 3 },
    "requestId": "req_abc"
  }
}
```

### Idempotency
- All `POST` state-transition endpoints must accept `Idempotency-Key` header.
- Idempotency keys are stored in Redis with a 24-hour TTL.
- Duplicate requests with the same key return the cached response without re-executing.

### Versioning
- URL versioning: `/v1/`, `/v2/` — never remove a version without deprecation period.
- Deprecation header: `Deprecation: true` + `Sunset: <date>` on deprecated endpoints.

---

## Error Handling Standards

### Domain Error Hierarchy
```typescript
// packages/shared/errors/domain-error.ts
export class DomainError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly context?: Record<string, unknown>,
  ) {
    super(message);
    this.name = this.constructor.name;
  }
}

export class OrderNotFoundError extends DomainError {
  constructor(orderId: string) {
    super('ORDER_NOT_FOUND', `Order ${orderId} not found`, { orderId });
  }
}

export class OrderVersionConflictError extends DomainError {
  constructor(current: number, submitted: number) {
    super('ORDER_VERSION_CONFLICT', 'Order was modified concurrently', {
      currentVersion: current, submittedVersion: submitted,
    });
  }
}

export class InsufficientStockError extends DomainError {
  constructor(ingredientId: string, required: number, available: number) {
    super('INSUFFICIENT_STOCK', 'Not enough stock to fulfil order', {
      ingredientId, required, available,
    });
  }
}

export class PolicyViolationError extends DomainError {
  constructor(action: string, role: string, reason: string) {
    super('POLICY_VIOLATION', `Action ${action} denied for role ${role}: ${reason}`, {
      action, role, reason,
    });
  }
}
```

### Error Mapping in Controllers
```typescript
@Catch(DomainError)
export class DomainErrorFilter implements ExceptionFilter {
  catch(error: DomainError, host: ArgumentsHost) {
    const response = host.switchToHttp().getResponse<Response>();
    const statusMap: Record<string, number> = {
      ORDER_NOT_FOUND: 404,
      ORDER_VERSION_CONFLICT: 409,
      POLICY_VIOLATION: 403,
      INSUFFICIENT_STOCK: 422,
    };
    const status = statusMap[error.code] ?? 400;
    response.status(status).json({
      error: { code: error.code, message: error.message, details: error.context },
    });
  }
}
```

---

## Logging Standards

### Log Levels and Usage
| Level | When to Use |
|-------|------------|
| `error` | Unhandled exceptions, payment failures, data integrity violations |
| `warn` | Recoverable errors, policy soft-failures, deprecated API usage |
| `info` | Request lifecycle, state transitions, significant business events |
| `debug` | Detailed flow tracing (disabled in production by default) |

### Structured Log Format
```typescript
// ✅ Always log structured JSON with required context fields
logger.info('Order submitted', {
  orderId: order.id,
  branchId: order.branchId,
  waiterId: order.waiterId,
  lineCount: order.items.length,
  totalAmount: order.total.amount,
  durationMs: Date.now() - startTime,
  traceId: context.traceId,
});

// ❌ Never log raw objects or card data
logger.info('Payment processed', { payment });          // ❌ May log card numbers
logger.info('Payment processed', {                      // ✅
  paymentIntentId: payment.intentId,
  amount: payment.amount,
  status: payment.status,
});
```

### Sensitive Data Rules
- **Never log**: card numbers, CVVs, PINs, passwords, JWT tokens, full SSNs.
- **Always tokenise**: payment references — log `intentId`, never raw card data.
- **Mask in logs**: staff PINs must be replaced with `****` before any logging.

---

## Testing Standards

### Test File Naming
```
packages/domain/orders/test/
├── order-aggregate.spec.ts          # Unit: order domain logic
├── tax-calculation.spec.ts          # Unit: tax engine
├── submit-order.command.spec.ts     # Unit: command handler
├── order-repository.test.ts         # Integration: DB queries
└── order-submission-flow.test.ts    # Integration: full flow
```

### Test Structure (AAA Pattern)
```typescript
describe('OrderAggregate', () => {
  describe('submit()', () => {
    it('should transition status from draft to submitted', () => {
      // Arrange
      const order = OrderFactory.createDraft({ branchId: 'b_123' });

      // Act
      const result = order.submit({ submittedBy: 'staff_1' });

      // Assert
      expect(result.ok).toBe(true);
      expect(order.status).toBe('submitted');
      expect(order.events).toContainEqual(
        expect.objectContaining({ type: 'OrderSubmitted' }),
      );
    });

    it('should return an error when order has no items', () => {
      // Arrange
      const order = OrderFactory.createDraft({ items: [] });

      // Act
      const result = order.submit({ submittedBy: 'staff_1' });

      // Assert
      expect(result.ok).toBe(false);
      expect(result.error.code).toBe('ORDER_EMPTY');
    });
  });
});
```

### Coverage Targets
| Package | Statements | Branches | Functions |
|---------|-----------|---------|----------|
| `domain/billing` | 90% | 85% | 95% |
| `domain/orders` | 88% | 83% | 92% |
| `domain/kitchen` | 85% | 80% | 90% |
| `domain/inventory` | 88% | 83% | 90% |
| All others | 80% | 75% | 85% |

---

## Security Guidelines

### Input Validation
```typescript
// ✅ Always validate at the DTO boundary using class-validator
export class CreateOrderDto {
  @IsUUID()
  branchId: string;

  @IsEnum(OrderSource)
  orderSource: OrderSource;

  @IsOptional()
  @IsUUID()
  tableId?: string;

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => OrderLineDto)
  @ArrayMaxSize(100)            // Protect against oversized payloads
  items: OrderLineDto[];

  @IsOptional()
  @IsString()
  @MaxLength(500)               // Prevent injection via long strings
  @Transform(({ value }) => sanitizeHtml(value))
  notes?: string;
}
```

### Authorisation Checks
```typescript
// ✅ Check permissions at command handler level, not just controller
@CommandHandler(VoidBillCommand)
export class VoidBillHandler {
  async execute(command: VoidBillCommand) {
    // Verify actor has permission in THIS branch
    const allowed = await this.policy.evaluate({
      actor: command.actorId,
      action: 'bill:void',
      resource: { branchId: command.branchId },
    });
    if (!allowed) throw new PolicyViolationError('bill:void', command.actorRole, 'Insufficient permission');

    // ... proceed with void logic
  }
}
```

### SQL Injection Prevention
- Use parameterised queries exclusively. Never concatenate user input into SQL strings.
- ORM query builder must be used for dynamic filters; raw SQL queries require security review.

---

## Performance Guidelines

### Database
- Use `SELECT` with explicit column lists; avoid `SELECT *` on large tables.
- Add `LIMIT` to all list queries; maximum page size is 200 records.
- Use `EXPLAIN ANALYZE` before merging any new query that touches tables > 10k rows.
- Use database-level `CHECK` constraints rather than application-only validation for critical invariants.

### Caching Strategy
```typescript
// Cache slot availability (30-second TTL — stale is acceptable for reads, not confirms)
const cacheKey = `rms:slots:${branchId}:${date}`;
const cached = await redis.get(cacheKey);
if (cached) return JSON.parse(cached);
const slots = await slotRepository.findAvailable(branchId, date);
await redis.setex(cacheKey, 30, JSON.stringify(slots));
return slots;

// Cache menu (5-minute TTL — changes are rare)
const menuCacheKey = `rms:menu:${branchId}:${menuVersion}`;

// Never cache: payment states, order version counters, active kitchen tickets
```

### Frontend Performance
- POS app must achieve First Contentful Paint < 2s on a 4G connection.
- Use React Query for server state; avoid duplicating server state in local Redux.
- Virtualise long lists (100+ items) using `react-virtual` or `@tanstack/virtual`.
- Lazy load back-office reporting charts; they must not block POS bundle.

---

## Code Review Checklist

Before approving any pull request, verify the following:

### Correctness
- [ ] Financial calculations (tax, discount, split, rounding) have unit tests with edge cases
- [ ] State machine transitions are guarded; invalid transitions throw explicit errors
- [ ] Concurrent write paths use optimistic locking or database-level serialisation
- [ ] All async operations have proper error handling; no fire-and-forget without error capture

### Security
- [ ] Branch scoping is enforced on every new data access — no cross-branch data leak
- [ ] Input validation applied at DTO level for all new endpoints
- [ ] No sensitive data (PINs, card data) is logged or included in error responses
- [ ] New endpoints are protected by appropriate auth guard and RBAC policy

### Data Integrity
- [ ] Financial records use compensating entries, not updates or deletes
- [ ] Idempotency key is required for all state-transition POST endpoints
- [ ] Database migrations are backward-compatible (additive only in non-breaking releases)
- [ ] New indexes are created `CONCURRENTLY` to avoid table locks in production

### Code Quality
- [ ] No `any` types; `unknown` with type guards used where needed
- [ ] All public domain functions have JSDoc comments explaining business intent
- [ ] No magic numbers; constants are named and placed in a constants file
- [ ] No dead code or commented-out blocks

### Testing
- [ ] New business logic has unit tests covering happy path and at least 2 error paths
- [ ] Integration test added if the change touches database queries or queue interactions
- [ ] Coverage targets met (CI will fail if they drop below configured thresholds)

### Observability
- [ ] Significant state transitions emit structured log entries with required context fields
- [ ] New queue consumers emit processing duration and error count metrics
- [ ] Any new external API call has a timeout configured and is traced with OpenTelemetry

### Documentation
- [ ] README or inline docs updated if the change introduces a new pattern or convention
- [ ] API changes reflected in OpenAPI spec (auto-generated from decorators — verify Swagger UI)
- [ ] Breaking changes documented in `CHANGELOG.md` with migration notes

---

## Git Conventions

### Branch Naming
```
feature/<ticket-id>-short-description      # e.g. feature/RMS-123-split-bill-by-seat
fix/<ticket-id>-short-description          # e.g. fix/RMS-456-order-version-conflict
chore/<description>                        # e.g. chore/upgrade-nestjs-10
hotfix/<ticket-id>-short-description       # e.g. hotfix/RMS-789-payment-timeout-crash
release/<version>                          # e.g. release/1.4.0
```

### Commit Message Format (Conventional Commits)
```
<type>(<scope>): <short summary>

[optional body — explain the why, not just the what]

[optional footer: BREAKING CHANGE: <description> | Closes #<issue>]
```

**Types:** `feat`, `fix`, `perf`, `refactor`, `test`, `docs`, `chore`, `ci`

**Scopes:** `orders`, `kitchen`, `billing`, `inventory`, `seating`, `api`, `worker`, `infra`, `pos`

**Examples:**
```
feat(billing): add split-by-seat with rounding allocation

Implements deterministic split billing where remaining rounding residue
is allocated to the last sub-check. Supports up to 20 sub-checks per bill.

Closes #RMS-234
```
```
fix(orders): resolve version conflict when two waiters add lines concurrently

The previous implementation used application-level version checks which
had a TOCTOU race. Now uses SELECT ... FOR UPDATE to serialise the version
increment at the database level.

BREAKING CHANGE: OrderVersionConflictError code changed from
VERSION_MISMATCH to ORDER_VERSION_CONFLICT to match error catalogue.
```

### Pull Request Requirements
- PR title must follow Conventional Commits format.
- PR description must include: what changed, why it changed, how to test it, and screenshot/video for UI changes.
- Minimum 1 approving review required; 2 required for billing, payment, or RBAC changes.
- All CI checks must pass before merge.
- Squash merge into `main`/`develop`; no merge commits.

---

## Documentation Requirements

### Code Documentation
- **Domain services**: every public method must have a JSDoc comment explaining the business rule it implements.
- **Domain events**: document the trigger conditions and the expected downstream consumers.
- **Configuration values**: every environment variable must be documented in `.env.example` with type, default, and description.

### Architecture Decision Records (ADRs)
Store ADRs in `docs/adr/` using the format `<number>-<title>.md`. Required for decisions about:
- Technology stack choices
- Database schema design decisions
- Concurrency and locking strategies
- Payment provider integration approach
- Breaking API changes

### API Documentation
- OpenAPI spec auto-generated from NestJS decorators; always buildable and valid.
- Breaking changes require major version bump and are documented in `CHANGELOG.md`.
- Sample request/response payloads required for all endpoints in Swagger UI.
