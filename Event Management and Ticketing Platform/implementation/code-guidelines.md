# Code Guidelines — Event Management and Ticketing Platform

## 1. Framework and Language Choices

### Backend Services

| Service | Language / Runtime | Framework |
|---|---|---|
| Event Service | Node.js 20 LTS, TypeScript 5.x | Fastify 4.x |
| Order Service | Node.js 20 LTS, TypeScript 5.x | Fastify 4.x |
| Notification Service | Node.js 20 LTS, TypeScript 5.x | Express.js 4.x |
| Inventory Service | Go 1.22 | net/http + chi router |
| Check-In Service | Go 1.22 | net/http + chi router |
| Analytics Service | Python 3.12 | FastAPI 0.111 |
| PDF / QR Service | Node.js 20 LTS, TypeScript 5.x | Fastify 4.x |

**Rationale for Go in Inventory and Check-In Services:** Ticket inventory mutations require sub-millisecond Redis and PostgreSQL operations under high concurrency (flash sales). Go's goroutine model and zero-overhead channel primitives handle 200+ inventory mutations per second without thread-pool saturation.

### Frontend and Mobile

- **Web:** Next.js 14 (App Router), Tailwind CSS 3.x, Shadcn/ui component library
- **Mobile:** React Native 0.73 with Expo SDK 50; shared business logic with web via a `packages/core` workspace
- **State management:** Zustand for global state; React Query (TanStack Query v5) for server state and cache invalidation

### Infrastructure

- **IaC:** Terraform 1.8 for cloud resources; Helm 3.x charts for Kubernetes workloads
- **Container orchestration:** AWS EKS 1.30; Karpenter for node autoscaling
- **Service mesh:** Istio 1.21 for mTLS between services and traffic management

---

## 2. TypeScript Coding Standards

### Compiler Configuration

```jsonc
// tsconfig.json — all services must extend this base
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "noImplicitAny": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "esModuleInterop": true,
    "skipLibCheck": false
  }
}
```

- **Zero `any` types.** Use `unknown` when the shape is genuinely unknown; narrow with type guards.
- **Zod** for all external input validation (HTTP request bodies, Kafka message payloads). Schema defines the source of truth; derive TypeScript types with `z.infer<>`.
- **ESLint** config: `@typescript-eslint/recommended-requiring-type-checking` + `eslint-plugin-unicorn` + `eslint-plugin-import`.
- **Prettier** for formatting; enforced in CI via `prettier --check`.
- **No default exports** in service modules; named exports only for testability and refactoring safety.
- All async functions must explicitly type their return as `Promise<T>`, never infer it as `Promise<any>`.

### Naming Conventions

- Types and interfaces: `PascalCase`
- Functions and variables: `camelCase`
- Constants (module-level): `SCREAMING_SNAKE_CASE`
- File names: `kebab-case.ts`
- API response JSON keys: `camelCase`
- Database column names: `snake_case` (mapped in repository layer)

---

## 3. Go Coding Standards

- **golangci-lint 1.58** with the following linters enabled: `errcheck`, `govet`, `staticcheck`, `revive`, `gocyclo`, `godot`, `misspell`, `gocritic`, `exhaustive`.
- Follow the **Uber Go Style Guide** (https://github.com/uber-go/guide).
- All exported functions and types must have GoDoc comments.
- Errors must be wrapped with `fmt.Errorf("context: %w", err)` — never swallowed or logged-and-continued.
- Use `context.Context` as the first parameter of every function that performs I/O.
- Avoid global state; inject dependencies via constructor functions returning an interface.
- Channel ownership: the goroutine that creates a channel is responsible for closing it.
- Use `sync.WaitGroup` + `errgroup.Group` (golang.org/x/sync) for concurrent operations with shared error propagation.

---

## 4. Python Coding Standards

- **Ruff** 0.4 for linting (replaces flake8/isort/pyupgrade in one tool); run with `ruff check --fix`.
- **Black** 24.x for formatting; enforced in CI.
- **Type hints required** on every function signature; use `from __future__ import annotations` for forward references.
- Pydantic v2 for request/response models; `model_config = ConfigDict(populate_by_name=True)` to handle snake_case DB ↔ camelCase API mapping.
- Async I/O with `asyncio`; use `asyncpg` for PostgreSQL, `aioredis` for Redis, `aiokafka` for Kafka.
- ClickHouse queries via `clickhouse-driver` (sync) or `asynch` (async); always parameterize queries.

---

## 5. Error Code Convention

Error codes follow the pattern: `DOMAIN_RESOURCE_REASON`

| Code | HTTP Status | Meaning |
|---|---|---|
| `INVENTORY_TICKET_INSUFFICIENT` | 409 | No available tickets of the requested type |
| `INVENTORY_SEAT_ALREADY_HELD` | 409 | Seat is held by another session |
| `INVENTORY_HOLD_EXPIRED` | 410 | Seat hold TTL elapsed before order completion |
| `ORDER_PAYMENT_DECLINED` | 402 | Stripe charge declined |
| `ORDER_PROMO_INVALID` | 422 | Promo code does not exist or has expired |
| `ORDER_PROMO_EXHAUSTED` | 409 | Promo code has reached its redemption limit |
| `CHECKIN_TICKET_ALREADY_SCANNED` | 409 | QR code has been used; possible duplicate entry |
| `CHECKIN_TICKET_INVALID_HMAC` | 401 | HMAC verification failed; suspected counterfeit |
| `CHECKIN_TICKET_EXPIRED` | 410 | Ticket scanned after event_end_time + 2 hours |
| `EVENT_NOT_FOUND` | 404 | Event ID does not exist |
| `AUTH_TOKEN_EXPIRED` | 401 | JWT past its `exp` claim |

All error responses conform to:
```json
{
  "error": {
    "code": "INVENTORY_TICKET_INSUFFICIENT",
    "message": "No tickets of type 'General Admission' are available.",
    "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
    "requestId": "01J0ZK8Y2F3NV9TBKSPXQ6MHPR"
  }
}
```

---

## 6. Concurrency Patterns for Ticket Inventory

### Redis Seat Holds

Holds are created atomically using `SETNX` with a TTL:

```
SETNX seat:hold:{seat_id}:{session_id} {order_id}
EXPIRE seat:hold:{seat_id}:{session_id} 600
```

Use a Lua script to combine SETNX + EXPIRE atomically (avoids hold leak on crash between two commands):

```lua
-- hold_seat.lua
local key = KEYS[1]
local value = ARGV[1]
local ttl = tonumber(ARGV[2])
if redis.call('SET', key, value, 'NX', 'EX', ttl) then
  return 1
else
  return 0
end
```

### PostgreSQL Optimistic Locking

Every inventory row carries a `version` integer. Decrement atomically:

```sql
UPDATE ticket_inventory
SET    available_count = available_count - 1,
       version         = version + 1
WHERE  inventory_id   = $1
  AND  version        = $2
  AND  available_count > 0;
```

If `rows_affected = 0`: retry up to **3 times** with exponential backoff (50 ms, 100 ms, 200 ms), then return `HTTP 409 INVENTORY_TICKET_INSUFFICIENT`.

### Batch Processing with SKIP LOCKED

Payout batch jobs use `SELECT FOR UPDATE SKIP LOCKED` so multiple worker replicas can process disjoint rows without blocking:

```sql
SELECT payout_id, organizer_id, amount_cents, currency
FROM   payouts
WHERE  status = 'pending'
LIMIT  50
FOR UPDATE SKIP LOCKED;
```

---

## 7. Payment Idempotency

- Every `POST /orders` and `POST /refunds` request **must** include an `Idempotency-Key` header (UUID v4 generated by the client).
- The middleware hashes `SHA-256(idempotency_key + request_body)` and checks Redis:
  - **Miss:** process the request, store `{status_code, response_body}` in Redis with 24-hour TTL.
  - **Hit:** return the cached response with header `Idempotency-Replay: true`.
- Payment intents are created **server-side**; only the `client_secret` is returned to the frontend for Stripe.js `confirmPayment()`. The raw secret key never reaches the browser.
- **Webhook deduplication:** store Stripe event IDs in a Redis SET (`SADD stripe:processed_events {event_id}`, TTL 7 days). If `SADD` returns 0, the event was already processed — acknowledge and discard.

---

## 8. QR Code Generation and Validation

### Generation Algorithm

```
payload_data = ticket_id + "|" + event_id + "|" + issued_at_unix
hmac_signature = HMAC-SHA256(SECRET_KEY, payload_data)
encoded = base64url(payload_data + "." + hmac_signature)
qr_uri = "evtplt://checkin/v1/" + encoded
```

`SECRET_KEY` is a 32-byte random key stored in AWS Secrets Manager, rotated per-event to limit blast radius if compromised.

### Offline Validation (Check-In Service)

1. Check-In app fetches the event secret key once before the event (requires network).
2. Parses URI scheme `evtplt://checkin/v1/{payload}`.
3. Splits `payload` into `payload_data` and `hmac_signature`.
4. Recomputes HMAC-SHA256 locally; compares with constant-time `hmac.Equal`.
5. Extracts `issued_at_unix`; rejects if `now > event_end_time + 7200` (2-hour grace window).
6. Checks local SQLite `scanned_tickets` table; rejects if `ticket_id` already present (duplicate scan).

---

## 9. PDF Ticket Generation

- HTML ticket templates are maintained in `services/pdf-service/templates/`.
- **Puppeteer** (Node.js, Chromium) renders the HTML template to PDF. Use `--no-sandbox` only in containers with proper Linux namespaces; use `--disable-dev-shm-usage` in Kubernetes pods with limited `/dev/shm`.
- Template data: event name, date/time (formatted in event timezone), venue name and address, attendee name, ticket type, seat section/row/number, QR code as inline PNG (base64), order reference.
- Completed PDFs are uploaded to S3 bucket `evtplt-tickets-{env}` with key `tickets/{year}/{event_id}/{ticket_id}.pdf`.
- A presigned URL (1-hour expiry) is generated and returned to the attendee via the order confirmation email.
- **Kafka pipeline:** `ticket.issued` event → PDF Service consumer → render → S3 upload → publish `ticket.pdf_ready` event → Notification Service → SendGrid email delivery.
- Retry policy: 3 attempts with 30-second delay; after 3 failures, dead-letter to `ticket.pdf_failed` topic and trigger PagerDuty alert.

---

## 10. Real-Time Capacity Updates

- After each successful check-in: `INCR event:checkin_count:{event_id}` in Redis.
- **SSE endpoint:** `GET /analytics/events/{eventId}/capacity/stream` — streams `text/event-stream` with capacity data every 5 seconds or on each check-in event.
- Capacity thresholds trigger Kafka events on topic `event.capacity_threshold`:

| Threshold | Event Type |
|---|---|
| 50% checked in | `CAPACITY_HALF` |
| 75% checked in | `CAPACITY_HIGH` |
| 90% checked in | `CAPACITY_CRITICAL` |
| 100% checked in | `CAPACITY_FULL` |

- Organizer dashboard receives threshold notifications via WebSocket (`ws://api.evtplt.com/ws/events/{eventId}`), displayed as toast alerts.

---

## 11. Observability Standards

### Tracing

Every service must instrument with **OpenTelemetry SDK**. All public service methods create a child span:

```typescript
// Node.js example
const span = tracer.startSpan('InventoryService.reserveTickets', {
  attributes: {
    'inventory.event_id': eventId,
    'inventory.ticket_type_id': ticketTypeId,
    'inventory.quantity': quantity,
  },
});
```

Spans are exported to **Jaeger** (dev/staging) and **AWS X-Ray** (production).

### Structured Logging

All logs must be JSON with these mandatory fields:

```json
{
  "timestamp": "2024-06-15T14:32:01.123Z",
  "level": "info",
  "service": "order-service",
  "correlation_id": "01J0ZK8Y2F3NV9TBKSPXQ6MHPR",
  "span_id": "a3ce929d0e0e4736",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "user_id": "usr_01J0ABC123",
  "message": "Order created successfully",
  "order_id": "ord_01J0XYZ456"
}
```

Use `pino` (Node.js), `slog` (Go), or `structlog` (Python).

---

## 12. Testing Standards

| Layer | Tooling | Coverage Target |
|---|---|---|
| Unit | Jest (TS), `go test` (Go), pytest (Python) | ≥ 80% line coverage |
| Integration | Testcontainers (PostgreSQL, Redis, Kafka) | All repository and service layers |
| E2E (Web) | Playwright 1.44 | Critical purchase and check-in flows |
| E2E (Mobile) | Detox 20 | Purchase, ticket wallet, QR scan |
| Load | k6 | 50k concurrent users; 200 tickets/sec; P99 < 2s |
| Contract | Pact 12 (consumer-driven) | All inter-service API boundaries |

- Integration tests must not call live external APIs. Use WireMock for Stripe and TaxJar.
- Each service has a `docker-compose.test.yml` that spins up its dependencies for local integration test runs.
- Load test scripts live in `load-tests/k6/` and are run in CI on the `perf` branch merges.
- Pact broker is hosted internally; contracts are published on every merge to `main`.

---

## 13. Security Requirements

- All inter-service communication uses mTLS enforced by Istio `PeerAuthentication` in `STRICT` mode.
- Secrets (DB passwords, Stripe keys, HMAC secrets) are stored in **AWS Secrets Manager**; injected into pods via the AWS Secrets Store CSI Driver — never as plain environment variables in manifests.
- JWT tokens: RS256 algorithm, 15-minute access token expiry, 7-day refresh token with rotation.
- Rate limiting: `100 req/min` per IP for unauthenticated endpoints; `1000 req/min` per authenticated user. Enforced at the API gateway (Kong).
- Input sanitization: all HTML inputs (event descriptions) are sanitized with DOMPurify (frontend) and `bluemonday` (Go backend) before persistence.
- PCI DSS: cardholder data never touches application servers. Stripe.js tokenizes card data in the browser; only `PaymentMethod` tokens reach the backend.
