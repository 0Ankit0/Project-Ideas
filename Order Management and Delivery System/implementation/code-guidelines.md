# Code Guidelines

## Overview

Development standards, conventions, and best practices for the Order Management and Delivery System (OMS) codebase. The OMS is an AWS-native monorepo using Lambda + Fargate hybrid compute, PostgreSQL 15 on RDS, DynamoDB, EventBridge, Cognito, ElastiCache Redis, OpenSearch, and S3.

---

## Technology Stack

### Backend Compute

| Component | Technology | Version | Notes |
|---|---|---|---|
| Runtime | Node.js | 20 LTS | All Lambda and Fargate services |
| Language | TypeScript | 5.x strict | `strict: true`, `noUncheckedIndexedAccess: true` |
| Lambda framework | Middy | 5.x | Middleware chain for handlers |
| Fargate framework | Fastify | 4.x | HTTP server for long-running services |
| IaC | AWS CDK | 2.x | TypeScript CDK app |
| Package manager | npm workspaces | 10.x | Lockfile committed, `npm ci` in CI |

### Data Stores

| Store | Technology | Version | Usage |
|---|---|---|---|
| OLTP | PostgreSQL | 15 (RDS) | Orders, payments, customers, inventory |
| Cart / sessions | DynamoDB | N/A | Low-latency cart reads, session tokens |
| Milestones | DynamoDB | N/A | Delivery milestones, order status timeline |
| Idempotency / cache | ElastiCache Redis | 7.x | Request deduplication, hot-path reads |
| Product search | OpenSearch | 2.x | Full-text product search |
| POD artifacts | S3 | N/A | Proof-of-delivery images |

### Messaging and Auth

| Component | Technology |
|---|---|
| Domain events | EventBridge (custom bus `oms-events`) |
| Auth | Cognito user pools + JWT |
| Email / SMS | SNS + SES |
| Async jobs | SQS FIFO queues per domain |

### Toolchain

| Tool | Purpose |
|---|---|
| ESLint + Prettier | Linting and formatting |
| Jest 29 | Unit and integration tests |
| testcontainers-node | Real database in integration tests |
| Playwright | E2E browser and API tests |
| node-pg-migrate | SQL migration runner |
| LocalStack | Local AWS service emulation |
| Docker Compose | Full local stack |

---

## Project Structure

```
oms/
├── package.json                          # npm workspaces root
├── tsconfig.base.json                    # shared TS config extended by all packages
├── .eslintrc.js                          # root ESLint config
├── jest.config.base.js                   # shared Jest config
├── docker-compose.yml                    # local dev: postgres, redis, localstack
│
├── packages/
│   ├── shared/                           # @oms/shared — published to internal registry
│   │   ├── src/
│   │   │   ├── types/
│   │   │   │   ├── order.types.ts        # Order, OrderItem, OrderStatus enum
│   │   │   │   ├── payment.types.ts      # PaymentIntent, CaptureResult
│   │   │   │   ├── delivery.types.ts     # DeliveryZone, Milestone
│   │   │   │   └── index.ts
│   │   │   ├── events/
│   │   │   │   ├── schemas/
│   │   │   │   │   ├── order-confirmed.schema.json
│   │   │   │   │   ├── payment-captured.schema.json
│   │   │   │   │   └── delivery-completed.schema.json
│   │   │   │   ├── event-bus.ts          # EventBridgePublisher
│   │   │   │   └── index.ts
│   │   │   ├── errors/
│   │   │   │   ├── app-error.ts          # AppError base class
│   │   │   │   ├── domain-errors.ts      # NotFoundError, ConflictError, …
│   │   │   │   └── index.ts
│   │   │   ├── middleware/
│   │   │   │   ├── auth.middleware.ts    # Cognito JWT verification (Middy / Fastify)
│   │   │   │   ├── idempotency.ts        # Redis idempotency guard
│   │   │   │   └── correlation.ts        # Correlation ID injection
│   │   │   ├── logger/
│   │   │   │   └── index.ts             # Structured logger (pino)
│   │   │   └── db/
│   │   │       ├── pool.ts              # node-postgres Pool factory
│   │   │       └── migrate.ts           # node-pg-migrate runner
│   │   └── package.json
│   │
│   ├── order-service/                    # Lambda — order CRUD + checkout
│   │   ├── src/
│   │   │   ├── handlers/
│   │   │   │   ├── create-order.handler.ts
│   │   │   │   ├── checkout.handler.ts   # idempotent, guarded by Redis
│   │   │   │   ├── get-order.handler.ts
│   │   │   │   └── cancel-order.handler.ts
│   │   │   ├── services/
│   │   │   │   ├── order.service.ts      # IOrderService + OrderService
│   │   │   │   └── checkout.service.ts   # ICheckoutService + CheckoutService
│   │   │   ├── repositories/
│   │   │   │   ├── order.repository.ts   # IOrderRepository + PostgresOrderRepository
│   │   │   │   └── cart.repository.ts    # DynamoDB cart adapter
│   │   │   ├── schemas/
│   │   │   │   └── create-order.schema.ts  # Zod schemas
│   │   │   └── db/
│   │   │       └── migrations/           # SQL migration files for this service
│   │   │           ├── 001_create_orders.sql
│   │   │           └── 002_add_order_indexes.sql
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   │   └── order.service.test.ts
│   │   │   ├── integration/
│   │   │   │   └── order.repository.test.ts
│   │   │   └── e2e/
│   │   │       └── checkout.test.ts
│   │   ├── jest.config.ts
│   │   └── package.json
│   │
│   ├── payment-service/                  # Lambda — Stripe / Razorpay integration
│   ├── inventory-service/                # Lambda — stock reservation / release
│   ├── notification-service/             # Lambda — SNS + SES dispatch
│   ├── fulfillment-service/              # Fargate — WMS integration, pick/pack
│   ├── delivery-service/                 # Fargate — carrier dispatch, tracking ingestion
│   ├── return-service/                   # Fargate — RMA workflow, refund orchestration
│   └── analytics-service/               # Fargate — OpenSearch aggregations, reports
│
├── infra/
│   ├── bin/
│   │   └── oms.ts                        # CDK app entry point
│   └── lib/
│       ├── stacks/
│       │   ├── network-stack.ts          # VPC, subnets, security groups
│       │   ├── data-stack.ts             # RDS, DynamoDB, ElastiCache, OpenSearch
│       │   ├── compute-stack.ts          # Lambda functions, Fargate services
│       │   ├── events-stack.ts           # EventBridge bus + rules
│       │   └── auth-stack.ts             # Cognito user pools
│       └── constructs/
│           ├── lambda-function.ts        # OMS-standard Lambda with layers + env
│           ├── fargate-service.ts        # OMS-standard Fargate with ALB
│           └── rds-postgres.ts           # RDS PostgreSQL with Parameter Groups
│
├── scripts/
│   ├── db-migrate.sh                     # Run migrations against target env
│   └── seed-dev.ts                       # Seed local DB with test data
│
└── docs/                                 # Architecture and design docs
```

---

## TypeScript Configuration

### tsconfig.base.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "exactOptionalPropertyTypes": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "dist"
  },
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
```

### ESLint (.eslintrc.js)

```js
module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint', 'import'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended-type-checked',
    'plugin:import/recommended',
    'plugin:import/typescript',
    'prettier',
  ],
  rules: {
    '@typescript-eslint/no-floating-promises': 'error',
    '@typescript-eslint/no-explicit-any': 'error',
    'import/order': ['error', { 'newlines-between': 'always' }],
    'no-console': 'error',
  },
};
```

---

## Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Files | kebab-case | `order-service.ts`, `checkout.handler.ts` |
| Classes | PascalCase | `OrderService`, `DeliveryAssignment` |
| Interfaces | PascalCase with `I` prefix | `IOrderRepository`, `IPaymentGateway` |
| Functions | camelCase | `createOrder()`, `capturePayment()` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_DELIVERY_ATTEMPTS`, `RESERVATION_TTL_MS` |
| Env vars | SCREAMING_SNAKE_CASE | `DATABASE_URL`, `PAYMENT_GATEWAY_API_KEY` |
| Event types | dot-separated, versioned | `oms.order.confirmed.v1` |
| API routes | kebab-case, plural nouns | `/orders`, `/delivery-zones` |
| DynamoDB keys | `PK` / `SK` with entity prefix | `ORDER#<id>`, `CUSTOMER#<id>` |
| Redis keys | colon-separated | `idempotency:<hash>`, `cart:<customerId>` |

---

## Lambda Handler Pattern

Every Lambda handler is a thin entry point that wires middleware and delegates to the service layer. Business logic never lives in the handler file.

### Handler Entry Point

```typescript
// packages/order-service/src/handlers/checkout.handler.ts
import middy from '@middy/core';
import httpJsonBodyParser from '@middy/http-json-body-parser';
import httpErrorHandler from '@middy/http-error-handler';
import { APIGatewayProxyEventV2, APIGatewayProxyResultV2 } from 'aws-lambda';

import { authenticate } from '@oms/shared/middleware/auth.middleware';
import { idempotencyGuard } from '@oms/shared/middleware/idempotency';
import { correlationMiddleware } from '@oms/shared/middleware/correlation';
import { createLogger } from '@oms/shared/logger';
import { CheckoutService } from '../services/checkout.service';
import { PostgresOrderRepository } from '../repositories/order.repository';
import { EventBridgePublisher } from '@oms/shared/events/event-bus';
import { getPool } from '@oms/shared/db/pool';
import { getRedis } from '@oms/shared/db/redis';
import { CheckoutCommandSchema } from '../schemas/create-order.schema';
import { lambdaErrorWrapper } from '@oms/shared/errors';

const logger = createLogger('checkout-handler');

const rawHandler = async (
  event: APIGatewayProxyEventV2,
): Promise<APIGatewayProxyResultV2> => {
  const body = CheckoutCommandSchema.parse(event.body);

  const pool = getPool();
  const redis = getRedis();
  const publisher = new EventBridgePublisher('oms-events');
  const orderRepo = new PostgresOrderRepository(pool);
  const service = new CheckoutService(orderRepo, publisher, redis);

  const order = await service.checkout(event.requestContext.authorizer!.jwt!.claims['sub'] as string, body);

  logger.info('Checkout complete', { orderId: order.id });

  return {
    statusCode: 201,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: { order } }),
  };
};

export const handler = middy(rawHandler)
  .use(httpJsonBodyParser())
  .use(correlationMiddleware())
  .use(authenticate())
  .use(idempotencyGuard({ redis: getRedis, ttlSeconds: 86400 }))
  .use(httpErrorHandler())
  .use(lambdaErrorWrapper());
```

---

## Service Layer

Interfaces define the contract; implementations contain business logic. Services receive all dependencies via constructor injection.

### Interface

```typescript
// packages/order-service/src/services/checkout.service.ts
import { Redis } from 'ioredis';

import { IOrderRepository } from '../repositories/order.repository';
import { IEventPublisher } from '@oms/shared/events/event-bus';
import { CheckoutCommand, Order } from '@oms/shared/types';
import { ConflictError } from '@oms/shared/errors';

export interface ICheckoutService {
  checkout(customerId: string, command: CheckoutCommand): Promise<Order>;
}

export class CheckoutService implements ICheckoutService {
  constructor(
    private readonly orderRepo: IOrderRepository,
    private readonly publisher: IEventPublisher,
    private readonly redis: Redis,
  ) {}

  async checkout(customerId: string, command: CheckoutCommand): Promise<Order> {
    // 1. Load cart items from DynamoDB via repository
    const cartItems = await this.orderRepo.getCartItems(customerId);
    if (cartItems.length === 0) {
      throw new ConflictError('Cart is empty');
    }

    // 2. Reserve inventory (calls inventory-service via EventBridge request-response)
    const reservationId = await this.reserveInventory(cartItems);

    // 3. Persist order in Postgres
    const order = await this.orderRepo.createOrder({
      customerId,
      items: cartItems,
      shippingAddressId: command.shippingAddressId,
      paymentMethodId: command.paymentMethodId,
      reservationId,
    });

    // 4. Publish domain event
    await this.publisher.publish({
      source: 'oms.order-service',
      detailType: 'oms.order.confirmed.v1',
      detail: {
        orderId: order.id,
        customerId,
        totalAmount: order.totalAmount,
        currency: order.currency,
        items: order.items.map((i) => ({ skuId: i.skuId, quantity: i.quantity })),
      },
    });

    // 5. Clear cart in Redis
    await this.redis.del(`cart:${customerId}`);

    return order;
  }

  private async reserveInventory(items: CartItem[]): Promise<string> {
    // Implementation calls inventory-service via SQS request-response or direct Lambda invoke
    throw new Error('Not implemented');
  }
}
```

---

## Repository Layer

Repositories encapsulate all SQL. No raw queries appear in service or handler code.

### Interface + PostgreSQL Implementation

```typescript
// packages/order-service/src/repositories/order.repository.ts
import { Pool, PoolClient } from 'pg';

import { Order, CreateOrderInput, CartItem } from '@oms/shared/types';
import { NotFoundError } from '@oms/shared/errors';

export interface IOrderRepository {
  createOrder(input: CreateOrderInput): Promise<Order>;
  findById(orderId: string): Promise<Order>;
  findByCustomer(customerId: string, limit: number, after?: string): Promise<Order[]>;
  updateStatus(orderId: string, status: string, updatedAt: Date): Promise<void>;
  getCartItems(customerId: string): Promise<CartItem[]>;
}

export class PostgresOrderRepository implements IOrderRepository {
  constructor(private readonly pool: Pool) {}

  async createOrder(input: CreateOrderInput): Promise<Order> {
    const client: PoolClient = await this.pool.connect();
    try {
      await client.query('BEGIN');

      const { rows } = await client.query<Order>(
        `INSERT INTO orders
           (customer_id, shipping_address_id, payment_method_id, reservation_id,
            status, subtotal, total_amount, currency, created_at, updated_at)
         VALUES ($1, $2, $3, $4, 'PENDING', $5, $6, $7, NOW(), NOW())
         RETURNING *`,
        [
          input.customerId,
          input.shippingAddressId,
          input.paymentMethodId,
          input.reservationId,
          input.subtotal,
          input.totalAmount,
          input.currency ?? 'INR',
        ],
      );

      const order = rows[0]!;

      // Batch-insert line items
      const itemValues = input.items.map(
        (item, i) =>
          `($${i * 5 + 1}, $${i * 5 + 2}, $${i * 5 + 3}, $${i * 5 + 4}, $${i * 5 + 5})`,
      );
      await client.query(
        `INSERT INTO order_items (order_id, sku_id, quantity, unit_price, line_total)
         VALUES ${itemValues.join(', ')}`,
        input.items.flatMap((item) => [order.id, item.skuId, item.quantity, item.unitPrice, item.lineTotal]),
      );

      await client.query('COMMIT');
      return order;
    } catch (err) {
      await client.query('ROLLBACK');
      throw err;
    } finally {
      client.release();
    }
  }

  async findById(orderId: string): Promise<Order> {
    const { rows } = await this.pool.query<Order>(
      `SELECT o.*, json_agg(oi.*) AS items
       FROM orders o
       LEFT JOIN order_items oi ON oi.order_id = o.id
       WHERE o.id = $1
       GROUP BY o.id`,
      [orderId],
    );
    if (!rows[0]) throw new NotFoundError('Order', orderId);
    return rows[0];
  }

  async findByCustomer(customerId: string, limit: number, after?: string): Promise<Order[]> {
    const { rows } = await this.pool.query<Order>(
      `SELECT * FROM orders
       WHERE customer_id = $1
         AND ($2::uuid IS NULL OR id < $2::uuid)
       ORDER BY created_at DESC
       LIMIT $3`,
      [customerId, after ?? null, limit],
    );
    return rows;
  }

  async updateStatus(orderId: string, status: string, updatedAt: Date): Promise<void> {
    const { rowCount } = await this.pool.query(
      `UPDATE orders SET status = $1, updated_at = $2 WHERE id = $3`,
      [status, updatedAt, orderId],
    );
    if (rowCount === 0) throw new NotFoundError('Order', orderId);
  }

  async getCartItems(customerId: string): Promise<CartItem[]> {
    // DynamoDB call via AWS SDK — kept here for interface symmetry
    // Real implementation delegates to a DynamoDBCartAdapter
    throw new Error('Delegated to DynamoDBCartAdapter');
  }
}
```

---

## EventBridge Publisher

```typescript
// packages/shared/src/events/event-bus.ts
import {
  EventBridgeClient,
  PutEventsCommand,
  PutEventsRequestEntry,
} from '@aws-sdk/client-eventbridge';

export interface DomainEvent {
  source: string;
  detailType: string;
  detail: Record<string, unknown>;
}

export interface IEventPublisher {
  publish(event: DomainEvent): Promise<void>;
  publishBatch(events: DomainEvent[]): Promise<void>;
}

export class EventBridgePublisher implements IEventPublisher {
  private readonly client = new EventBridgeClient({});

  constructor(private readonly busName: string) {}

  async publish(event: DomainEvent): Promise<void> {
    await this.publishBatch([event]);
  }

  async publishBatch(events: DomainEvent[]): Promise<void> {
    const entries: PutEventsRequestEntry[] = events.map((e) => ({
      EventBusName: this.busName,
      Source: e.source,
      DetailType: e.detailType,
      Detail: JSON.stringify(e.detail),
      Time: new Date(),
    }));

    const { FailedEntryCount, Entries } = await this.client.send(
      new PutEventsCommand({ Entries: entries }),
    );

    if (FailedEntryCount && FailedEntryCount > 0) {
      const failed = Entries?.filter((e) => e.ErrorCode).map((e) => e.ErrorMessage);
      throw new Error(`EventBridge publish failed: ${failed?.join(', ')}`);
    }
  }
}
```

---

## Idempotency Guard (ElastiCache Redis)

```typescript
// packages/shared/src/middleware/idempotency.ts
import { createHash } from 'crypto';
import middy from '@middy/core';
import { APIGatewayProxyEventV2, APIGatewayProxyResultV2 } from 'aws-lambda';
import { Redis } from 'ioredis';

interface IdempotencyOptions {
  redis: () => Redis;
  ttlSeconds?: number;
}

export const idempotencyGuard = (opts: IdempotencyOptions): middy.MiddlewareObj<APIGatewayProxyEventV2, APIGatewayProxyResultV2> => {
  const ttl = opts.ttlSeconds ?? 86400;

  return {
    before: async (request) => {
      const key = request.event.headers['idempotency-key'];
      if (!key) return;

      const cacheKey = `idempotency:${createHash('sha256').update(key).digest('hex')}`;
      const cached = await opts.redis().get(cacheKey);

      if (cached) {
        // Return cached response without re-executing handler
        request.response = JSON.parse(cached) as APIGatewayProxyResultV2;
      } else {
        // Store key in progress to detect concurrent duplicates
        await opts.redis().set(cacheKey, '__IN_PROGRESS__', 'EX', 30);
        // Attach cache key to event context for the after hook
        (request.event as Record<string, unknown>)['__idempotencyKey'] = cacheKey;
      }
    },
    after: async (request) => {
      const cacheKey = (request.event as Record<string, unknown>)['__idempotencyKey'] as string | undefined;
      if (!cacheKey || !request.response) return;
      const res = request.response as APIGatewayProxyResultV2;
      if (typeof res === 'object' && (res as { statusCode?: number }).statusCode && (res as { statusCode: number }).statusCode < 500) {
        await opts.redis().set(cacheKey, JSON.stringify(request.response), 'EX', ttl);
      }
    },
  };
};
```

---

## Error Handling

### Full Error Hierarchy

```typescript
// packages/shared/src/errors/app-error.ts
export class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number,
    public readonly details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace(this, this.constructor);
  }
}
```

```typescript
// packages/shared/src/errors/domain-errors.ts
import { AppError } from './app-error';

export class NotFoundError extends AppError {
  constructor(resource: string, id: string) {
    super(`${resource} not found`, 'NOT_FOUND', 404, { resource, id });
  }
}

export class ConflictError extends AppError {
  constructor(reason: string, details?: Record<string, unknown>) {
    super(reason, 'CONFLICT', 409, details);
  }
}

export class ValidationError extends AppError {
  constructor(message: string, fields?: Record<string, string>) {
    super(message, 'VALIDATION_ERROR', 422, { fields });
  }
}

export class UnauthorizedError extends AppError {
  constructor(message = 'Unauthorized') {
    super(message, 'UNAUTHORIZED', 401);
  }
}

export class ForbiddenError extends AppError {
  constructor(message = 'Forbidden') {
    super(message, 'FORBIDDEN', 403);
  }
}

export class PaymentError extends AppError {
  constructor(message: string, gatewayCode?: string) {
    super(message, 'PAYMENT_ERROR', 402, { gatewayCode });
  }
}

export class ServiceUnavailableError extends AppError {
  constructor(upstream: string) {
    super(`${upstream} is unavailable`, 'SERVICE_UNAVAILABLE', 503, { upstream });
  }
}
```

### Lambda Error Wrapper (Middy Middleware)

```typescript
// packages/shared/src/errors/lambda-error-wrapper.ts
import middy from '@middy/core';
import { ZodError } from 'zod';
import { createLogger } from '../logger';
import { AppError, ValidationError } from './domain-errors';

const logger = createLogger('error-handler');

export const lambdaErrorWrapper = (): middy.MiddlewareObj => ({
  onError: async (request) => {
    const { error } = request;

    if (error instanceof ZodError) {
      const fields = Object.fromEntries(
        error.errors.map((e) => [e.path.join('.'), e.message]),
      );
      const appErr = new ValidationError('Input validation failed', fields);
      request.response = toHttpResponse(appErr);
      return;
    }

    if (error instanceof AppError) {
      if (error.statusCode >= 500) {
        logger.error('Application error', { error: error.message, code: error.code, stack: error.stack });
      }
      request.response = toHttpResponse(error);
      return;
    }

    logger.error('Unhandled error', { error: String(error) });
    request.response = {
      statusCode: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        success: false,
        error: { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred' },
      }),
    };
  },
});

function toHttpResponse(err: AppError) {
  return {
    statusCode: err.statusCode,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      success: false,
      error: { code: err.code, message: err.message, details: err.details },
    }),
  };
}
```

---

## Database Patterns

### Connection Pool Configuration

```typescript
// packages/shared/src/db/pool.ts
import { Pool } from 'pg';

let pool: Pool | null = null;

export function getPool(): Pool {
  if (!pool) {
    pool = new Pool({
      connectionString: process.env['DATABASE_URL'],
      max: process.env['DB_POOL_MAX'] ? parseInt(process.env['DB_POOL_MAX'], 10) : 5,
      idleTimeoutMillis: 10_000,
      connectionTimeoutMillis: 3_000,
      ssl: process.env['NODE_ENV'] === 'production' ? { rejectUnauthorized: true } : false,
    });

    pool.on('error', (err) => {
      const logger = createLogger('pg-pool');
      logger.error('Idle client error', { message: err.message });
    });
  }
  return pool;
}

// Lambda: reuse pool across warm invocations; Fargate: single long-lived pool
// Max connections per Lambda = 5 (Aurora Serverless proxy handles multiplexing)
```

### SQL Migration Strategy

Migrations live in `packages/<service>/src/db/migrations/` and are numbered with zero-padded integers. They are plain SQL — no ORM DSL.

**File naming:** `NNN_<description>.sql` (e.g., `001_create_orders.sql`)

**Rules:**
- Migrations are **append-only**: never edit a committed file.
- Breaking changes use three-phase migrations: add column → backfill → add constraint / drop old.
- Each migration file must be idempotent when possible (`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX CONCURRENTLY IF NOT EXISTS`).

#### Migration Example

```sql
-- packages/order-service/src/db/migrations/001_create_orders.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS orders (
  id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  customer_id         UUID         NOT NULL,
  shipping_address_id UUID         NOT NULL,
  payment_method_id   VARCHAR(128) NOT NULL,
  reservation_id      UUID,
  status              VARCHAR(32)  NOT NULL DEFAULT 'PENDING',
  subtotal            NUMERIC(14,2) NOT NULL,
  total_amount        NUMERIC(14,2) NOT NULL,
  currency            CHAR(3)      NOT NULL DEFAULT 'INR',
  created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  order_id    UUID          NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  sku_id      UUID          NOT NULL,
  quantity    INT           NOT NULL CHECK (quantity > 0),
  unit_price  NUMERIC(12,2) NOT NULL,
  line_total  NUMERIC(14,2) NOT NULL
);
```

```sql
-- packages/order-service/src/db/migrations/002_add_order_indexes.sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_customer_id
  ON orders (customer_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_status_created
  ON orders (status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_order_items_order_id
  ON order_items (order_id);
```

#### Running Migrations

```typescript
// packages/shared/src/db/migrate.ts
import { createRequire } from 'module';
import path from 'path';
import pgMigrate from 'node-pg-migrate';

export async function runMigrations(migrationsDir: string): Promise<void> {
  await pgMigrate({
    databaseUrl: process.env['DATABASE_URL']!,
    migrationsTable: 'pgmigrations',
    dir: migrationsDir,
    direction: 'up',
    verbose: false,
  });
}
```

```bash
# Run from repo root — target a specific service's migrations
npx ts-node packages/order-service/scripts/migrate.ts

# Or via shell script
./scripts/db-migrate.sh order-service staging
```

---

## Testing Strategy

| Level | Coverage Target | Framework | Scope |
|---|---|---|---|
| Unit | > 80% branches | Jest 29 | Service logic, validators, calculators |
| Integration | All repository methods | Jest + testcontainers | Repository ↔ PostgreSQL, EventBridge publisher |
| E2E | Critical paths | supertest | Checkout, delivery status update, return flow |
| Contract | All domain events | JSON Schema (ajv) | Event producer ↔ consumer schema |

### Jest Base Config

```js
// jest.config.base.js
/** @type {import('jest').Config} */
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  coverageThreshold: { global: { branches: 80, lines: 80 } },
  setupFilesAfterFramework: ['<rootDir>/tests/setup.ts'],
  testMatch: ['<rootDir>/tests/**/*.test.ts'],
  moduleNameMapper: {
    '^@oms/shared/(.*)$': '<rootDir>/../../packages/shared/src/$1',
  },
};
```

### Test Setup File (conftest equivalent)

```typescript
// packages/order-service/tests/setup.ts
import { getPool } from '@oms/shared/db/pool';

beforeAll(async () => {
  // Ensure pool is lazily initialised before tests
  const pool = getPool();
  await pool.query('SELECT 1'); // warm up
});

afterAll(async () => {
  await getPool().end();
});
```

### Unit Test — OrderService.checkout()

```typescript
// packages/order-service/tests/unit/order.service.test.ts
import { CheckoutService } from '../../src/services/checkout.service';
import { IOrderRepository } from '../../src/repositories/order.repository';
import { IEventPublisher } from '@oms/shared/events/event-bus';
import { ConflictError } from '@oms/shared/errors';
import type { Redis } from 'ioredis';

const makeMockRepo = (): jest.Mocked<IOrderRepository> => ({
  createOrder: jest.fn(),
  findById: jest.fn(),
  findByCustomer: jest.fn(),
  updateStatus: jest.fn(),
  getCartItems: jest.fn(),
});

const makeMockPublisher = (): jest.Mocked<IEventPublisher> => ({
  publish: jest.fn().mockResolvedValue(undefined),
  publishBatch: jest.fn().mockResolvedValue(undefined),
});

const makeMockRedis = () =>
  ({
    get: jest.fn(),
    set: jest.fn(),
    del: jest.fn().mockResolvedValue(1),
  }) as unknown as Redis;

describe('CheckoutService', () => {
  let repo: jest.Mocked<IOrderRepository>;
  let publisher: jest.Mocked<IEventPublisher>;
  let redis: Redis;
  let service: CheckoutService;

  beforeEach(() => {
    repo = makeMockRepo();
    publisher = makeMockPublisher();
    redis = makeMockRedis();
    service = new CheckoutService(repo, publisher, redis);
  });

  describe('checkout()', () => {
    it('throws ConflictError when cart is empty', async () => {
      repo.getCartItems.mockResolvedValue([]);

      await expect(service.checkout('cust-1', { shippingAddressId: 'addr-1', paymentMethodId: 'pm-1' }))
        .rejects.toBeInstanceOf(ConflictError);
    });

    it('creates order and publishes event on success', async () => {
      const cartItems = [{ skuId: 'sku-1', quantity: 2, unitPrice: 500, lineTotal: 1000 }];
      const createdOrder = { id: 'order-1', customerId: 'cust-1', totalAmount: 1000, currency: 'INR', items: cartItems };

      repo.getCartItems.mockResolvedValue(cartItems);
      repo.createOrder.mockResolvedValue(createdOrder as never);

      const result = await service.checkout('cust-1', { shippingAddressId: 'addr-1', paymentMethodId: 'pm-1' });

      expect(result.id).toBe('order-1');
      expect(publisher.publish).toHaveBeenCalledWith(
        expect.objectContaining({
          detailType: 'oms.order.confirmed.v1',
          detail: expect.objectContaining({ orderId: 'order-1', customerId: 'cust-1' }),
        }),
      );
      expect((redis as jest.Mocked<Redis>).del).toHaveBeenCalledWith('cart:cust-1');
    });

    it('does not publish event if createOrder throws', async () => {
      repo.getCartItems.mockResolvedValue([{ skuId: 'sku-1', quantity: 1, unitPrice: 200, lineTotal: 200 }]);
      repo.createOrder.mockRejectedValue(new Error('DB error'));

      await expect(service.checkout('cust-1', { shippingAddressId: 'addr-1', paymentMethodId: 'pm-1' }))
        .rejects.toThrow('DB error');

      expect(publisher.publish).not.toHaveBeenCalled();
    });
  });
});
```

### Integration Test — PostgresOrderRepository

```typescript
// packages/order-service/tests/integration/order.repository.test.ts
import { PostgreSqlContainer, StartedPostgreSqlContainer } from '@testcontainers/postgresql';
import { Pool } from 'pg';
import { runMigrations } from '@oms/shared/db/migrate';
import { PostgresOrderRepository } from '../../src/repositories/order.repository';
import { NotFoundError } from '@oms/shared/errors';

let container: StartedPostgreSqlContainer;
let pool: Pool;
let repo: PostgresOrderRepository;

beforeAll(async () => {
  container = await new PostgreSqlContainer('postgres:15-alpine')
    .withDatabase('oms_test')
    .withUsername('oms')
    .withPassword('oms')
    .start();

  pool = new Pool({ connectionString: container.getConnectionUri() });
  await runMigrations(path.join(__dirname, '../../src/db/migrations'));
  repo = new PostgresOrderRepository(pool);
}, 60_000);

afterAll(async () => {
  await pool.end();
  await container.stop();
});

describe('PostgresOrderRepository', () => {
  it('creates an order and retrieves it by ID', async () => {
    const input = {
      customerId: 'cust-abc',
      shippingAddressId: 'addr-xyz',
      paymentMethodId: 'pm-stripe-123',
      reservationId: null,
      subtotal: 800,
      totalAmount: 900,
      currency: 'INR',
      items: [{ skuId: 'sku-a', quantity: 2, unitPrice: 400, lineTotal: 800 }],
    };

    const order = await repo.createOrder(input);
    expect(order.id).toBeDefined();

    const fetched = await repo.findById(order.id);
    expect(fetched.customerId).toBe('cust-abc');
    expect(fetched.items).toHaveLength(1);
  });

  it('throws NotFoundError for missing order', async () => {
    await expect(repo.findById('00000000-0000-0000-0000-000000000000'))
      .rejects.toBeInstanceOf(NotFoundError);
  });
});
```

### E2E Test — Checkout Flow (supertest)

```typescript
// packages/order-service/tests/e2e/checkout.test.ts
// Targets a locally running Fargate service on port 3000 (docker-compose up)
import request from 'supertest';

const BASE_URL = process.env['E2E_BASE_URL'] ?? 'http://localhost:3000';

describe('POST /v1/orders/checkout', () => {
  it('returns 201 and orderId for valid checkout', async () => {
    const token = await getTestJwt(); // utility that exchanges test credentials with Cognito

    const response = await request(BASE_URL)
      .post('/v1/orders/checkout')
      .set('Authorization', `Bearer ${token}`)
      .set('Idempotency-Key', `e2e-test-${Date.now()}`)
      .send({
        shippingAddressId: process.env['TEST_ADDRESS_ID'],
        paymentMethodId: process.env['TEST_PM_ID'],
      })
      .expect(201);

    expect(response.body.data.order.id).toMatch(/^[0-9a-f-]{36}$/);
  });

  it('returns 422 for missing shippingAddressId', async () => {
    const token = await getTestJwt();

    await request(BASE_URL)
      .post('/v1/orders/checkout')
      .set('Authorization', `Bearer ${token}`)
      .send({ paymentMethodId: 'pm-1' })
      .expect(422);
  });
});
```

### Contract Test — Event Schema (JSON Schema + ajv)

```typescript
// packages/order-service/tests/contract/order-confirmed.contract.test.ts
import Ajv from 'ajv';
import addFormats from 'ajv-formats';
import schema from '@oms/shared/events/schemas/order-confirmed.schema.json';

const ajv = new Ajv({ strict: true });
addFormats(ajv);
const validate = ajv.compile(schema);

describe('oms.order.confirmed.v1 event schema', () => {
  it('accepts a valid event payload', () => {
    const valid = {
      orderId: '550e8400-e29b-41d4-a716-446655440000',
      customerId: '6ba7b810-9dad-11d1-80b4-00c04fd430c8',
      totalAmount: 1500,
      currency: 'INR',
      items: [{ skuId: '6ba7b811-9dad-11d1-80b4-00c04fd430c8', quantity: 2 }],
    };
    expect(validate(valid)).toBe(true);
  });

  it('rejects a payload missing orderId', () => {
    const invalid = { customerId: 'x', totalAmount: 100, currency: 'INR', items: [] };
    expect(validate(invalid)).toBe(false);
  });
});
```

---

## CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: OMS CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'
  AWS_REGION: ap-south-1
  ECR_REGISTRY: ${{ secrets.ECR_REGISTRY }}

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck

  unit-test:
    name: Unit Tests
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npm run test:unit -- --coverage
      - uses: codecov/codecov-action@v4
        with:
          flags: unit

  build:
    name: Build
    runs-on: ubuntu-latest
    needs: unit-test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npm run build
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_CI_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}
      - name: Login to ECR
        uses: aws-actions/amazon-ecr-login@v2
      - name: Build and push Fargate images
        run: |
          for svc in fulfillment-service delivery-service return-service analytics-service; do
            IMAGE="$ECR_REGISTRY/oms-$svc:$GITHUB_SHA"
            docker build -t "$IMAGE" packages/$svc
            docker push "$IMAGE"
          done

  integration-test:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: build
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: oms
          POSTGRES_PASSWORD: oms
          POSTGRES_DB: oms_test
        ports: ['5432:5432']
        options: >-
          --health-cmd "pg_isready -U oms"
          --health-interval 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports: ['6379:6379']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - name: Run integration tests
        env:
          DATABASE_URL: postgres://oms:oms@localhost:5432/oms_test
          REDIS_URL: redis://localhost:6379
        run: npm run test:integration

  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: integration-test
    if: github.ref == 'refs/heads/main'
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_STAGING_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}
      - run: npm ci
      - name: CDK deploy staging
        run: |
          cd infra
          npx cdk deploy --all \
            --context imageTag=$GITHUB_SHA \
            --context env=staging \
            --require-approval never

  smoke-test:
    name: Smoke Test Staging
    runs-on: ubuntu-latest
    needs: deploy-staging
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - name: Run smoke tests
        env:
          E2E_BASE_URL: ${{ secrets.STAGING_API_URL }}
          TEST_ADDRESS_ID: ${{ secrets.STAGING_TEST_ADDRESS_ID }}
          TEST_PM_ID: ${{ secrets.STAGING_TEST_PM_ID }}
          COGNITO_TEST_CLIENT_ID: ${{ secrets.STAGING_COGNITO_TEST_CLIENT_ID }}
          COGNITO_TEST_USERNAME: ${{ secrets.STAGING_COGNITO_TEST_USERNAME }}
          COGNITO_TEST_PASSWORD: ${{ secrets.STAGING_COGNITO_TEST_PASSWORD }}
        run: npm run test:e2e

  deploy-production:
    name: Deploy to Production (Canary)
    runs-on: ubuntu-latest
    needs: smoke-test
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v4
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_PROD_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}
      - run: npm ci
      - name: CDK deploy production (10% canary)
        run: |
          cd infra
          npx cdk deploy --all \
            --context imageTag=$GITHUB_SHA \
            --context env=production \
            --context canaryWeight=10 \
            --require-approval never
```

---

## Structured Logging

```typescript
// packages/shared/src/logger/index.ts
import pino, { Logger } from 'pino';

const REDACTED_PATHS = [
  'password',
  'token',
  'authorization',
  'creditCard',
  'cardNumber',
  'cvv',
  'email',
  'phone',
  'phoneNumber',
];

let _baseLogger: Logger | null = null;

function getBaseLogger(): Logger {
  if (!_baseLogger) {
    _baseLogger = pino({
      level: process.env['LOG_LEVEL'] ?? 'info',
      formatters: {
        level: (label) => ({ level: label }),
      },
      timestamp: pino.stdTimeFunctions.isoTime,
      redact: {
        paths: REDACTED_PATHS,
        censor: '[REDACTED]',
      },
      base: {
        env: process.env['NODE_ENV'],
        region: process.env['AWS_REGION'],
        functionName: process.env['AWS_LAMBDA_FUNCTION_NAME'],
      },
    });
  }
  return _baseLogger;
}

export function createLogger(service: string, correlationId?: string): Logger {
  return getBaseLogger().child({ service, correlationId });
}

// Usage in a Lambda handler (correlation ID injected by middleware):
//
// const logger = createLogger('order-service', event.headers['x-correlation-id']);
// logger.info({ orderId: order.id, customerId: order.customerId }, 'Order created');
// logger.error({ err: error }, 'Checkout failed');
```

### Log Format (CloudWatch)

Every log line is a single JSON object. CloudWatch Logs Insights can query using:

```
fields @timestamp, level, service, correlationId, orderId, @message
| filter level = "error"
| sort @timestamp desc
```

---

## Health Check Endpoints (Fargate Services)

Fargate services expose `/health` (liveness) and `/ready` (readiness) on port `3000`. The ALB health check targets `/health`; Kubernetes-style readiness is `/ready`.

```typescript
// packages/fulfillment-service/src/routes/health.route.ts
import { FastifyInstance } from 'fastify';
import { Pool } from 'pg';
import { Redis } from 'ioredis';

export async function healthRoutes(app: FastifyInstance, { pool, redis }: { pool: Pool; redis: Redis }) {
  app.get('/health', async (_req, reply) => {
    reply.send({ status: 'ok', timestamp: new Date().toISOString() });
  });

  app.get('/ready', async (_req, reply) => {
    const checks: Record<string, boolean> = {
      database: false,
      redis: false,
    };

    try {
      await pool.query('SELECT 1');
      checks['database'] = true;
    } catch {
      /* intentionally empty */
    }

    try {
      await redis.ping();
      checks['redis'] = true;
    } catch {
      /* intentionally empty */
    }

    const ready = Object.values(checks).every(Boolean);
    reply.status(ready ? 200 : 503).send({ ready, checks });
  });
}
```

---

## Input Validation (Zod)

All Lambda and Fargate request inputs are validated with Zod before reaching the service layer. Parse, don't validate — always call `.parse()` so ZodError is thrown on invalid input.

```typescript
// packages/order-service/src/schemas/create-order.schema.ts
import { z } from 'zod';

export const CheckoutCommandSchema = z.object({
  shippingAddressId: z.string().uuid({ message: 'shippingAddressId must be a valid UUID' }),
  paymentMethodId: z.string().min(1).max(128),
  couponCode: z.string().regex(/^[A-Z0-9_-]{4,20}$/).optional(),
  notes: z.string().max(500).optional(),
});

export type CheckoutCommand = z.infer<typeof CheckoutCommandSchema>;

export const CreateOrderLineSchema = z.object({
  skuId: z.string().uuid(),
  quantity: z.number().int().min(1).max(999),
});

export const CreateOrderSchema = z.object({
  customerId: z.string().uuid(),
  shippingAddressId: z.string().uuid(),
  paymentMethodId: z.string().min(1).max(128),
  currency: z.enum(['INR', 'USD', 'EUR']).default('INR'),
  items: z.array(CreateOrderLineSchema).min(1).max(50),
  couponCode: z.string().regex(/^[A-Z0-9_-]{4,20}$/).optional(),
});

export type CreateOrderInput = z.infer<typeof CreateOrderSchema>;
```

---

## Authentication Middleware

### Cognito JWT Verification (Lambda / Middy)

```typescript
// packages/shared/src/middleware/auth.middleware.ts
import middy from '@middy/core';
import { CognitoJwtVerifier } from 'aws-jwt-verify';
import { APIGatewayProxyEventV2 } from 'aws-lambda';
import { UnauthorizedError } from '../errors/domain-errors';

const verifier = CognitoJwtVerifier.create({
  userPoolId: process.env['COGNITO_USER_POOL_ID']!,
  tokenUse: 'access',
  clientId: process.env['COGNITO_CLIENT_ID']!,
});

export const authenticate = (): middy.MiddlewareObj<APIGatewayProxyEventV2> => ({
  before: async (request) => {
    const authHeader = request.event.headers?.['authorization'] ?? request.event.headers?.['Authorization'];
    const token = authHeader?.replace(/^Bearer\s+/i, '');

    if (!token) throw new UnauthorizedError('Authorization header missing');

    try {
      const payload = await verifier.verify(token);
      // Attach claims to event so handlers can read sub, groups, etc.
      (request.event as Record<string, unknown>)['__cognitoClaims'] = payload;
    } catch {
      throw new UnauthorizedError('Invalid or expired token');
    }
  },
});
```

### Cognito JWT Verification (Fargate / Fastify)

```typescript
// packages/fulfillment-service/src/plugins/auth.plugin.ts
import fp from 'fastify-plugin';
import { FastifyPluginAsync, FastifyRequest, FastifyReply } from 'fastify';
import { CognitoJwtVerifier } from 'aws-jwt-verify';

const verifier = CognitoJwtVerifier.create({
  userPoolId: process.env['COGNITO_USER_POOL_ID']!,
  tokenUse: 'access',
  clientId: process.env['COGNITO_CLIENT_ID']!,
});

declare module 'fastify' {
  interface FastifyRequest {
    cognitoClaims: Record<string, unknown>;
  }
}

const authPlugin: FastifyPluginAsync = async (app) => {
  app.decorateRequest('cognitoClaims', null);

  app.addHook('onRequest', async (request: FastifyRequest, reply: FastifyReply) => {
    const token = request.headers.authorization?.replace(/^Bearer\s+/i, '');
    if (!token) {
      return reply.status(401).send({ error: 'UNAUTHORIZED', message: 'Authorization header missing' });
    }
    try {
      request.cognitoClaims = await verifier.verify(token) as Record<string, unknown>;
    } catch {
      return reply.status(401).send({ error: 'UNAUTHORIZED', message: 'Invalid or expired token' });
    }
  });
};

export default fp(authPlugin);
```

---

## Performance Guidelines

### Lambda Cold Start

- Target: < 500 ms cold start, < 200 ms warm execution.
- Keep `node_modules` lean — use `esbuild` to bundle each handler to a single file with tree-shaking.
- Initialise SDK clients and DB pools **outside** the handler function so they are reused across warm invocations.
- Provision Concurrency for checkout and payment handlers to eliminate cold starts on critical paths.

```typescript
// GOOD — pool created once at module load time
const pool = getPool();
const publisher = new EventBridgePublisher('oms-events');

export const handler = middy(async (event) => {
  const repo = new PostgresOrderRepository(pool);
  // ...
});

// BAD — pool recreated on every invocation
export const handler = middy(async (event) => {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL }); // ❌
});
```

### Connection Pool Sizing

| Service type | `max` connections | Rationale |
|---|---|---|
| Lambda (per instance) | 5 | RDS Proxy multiplexes; Lambda scales horizontally |
| Fargate task | 20 | Long-lived process; task count is bounded |
| RDS Proxy | — | Set `max_connections` per user pool in Parameter Group |

```typescript
// Lambda pool — conservative max, short idle timeout
const pool = new Pool({
  connectionString: process.env['DATABASE_URL'],
  max: 5,
  idleTimeoutMillis: 10_000,
  connectionTimeoutMillis: 3_000,
});
```

### ElastiCache Redis Patterns

```typescript
// Cache-aside pattern for read-heavy resources (product catalogue, delivery zones)
async function getDeliveryZone(zoneId: string): Promise<DeliveryZone> {
  const cacheKey = `zone:${zoneId}`;
  const cached = await redis.get(cacheKey);
  if (cached) return JSON.parse(cached) as DeliveryZone;

  const zone = await zoneRepo.findById(zoneId);
  await redis.set(cacheKey, JSON.stringify(zone), 'EX', 300); // 5-minute TTL
  return zone;
}

// Write-through pattern for cart (DynamoDB is source of truth; Redis is hot cache)
async function updateCart(customerId: string, cart: Cart): Promise<void> {
  await cartRepo.save(cart);                          // persist to DynamoDB
  await redis.set(`cart:${customerId}`, JSON.stringify(cart), 'EX', 86400);
}
```

### Batch DynamoDB Writes

Never write DynamoDB items one-by-one in a loop. Use `BatchWriteItem` (max 25 per call).

```typescript
import { DynamoDBClient, BatchWriteItemCommand } from '@aws-sdk/client-dynamodb';
import { marshall } from '@aws-sdk/util-dynamodb';
import { chunk } from 'lodash';

const dynamo = new DynamoDBClient({});

async function saveMilestones(milestones: DeliveryMilestone[]): Promise<void> {
  const batches = chunk(milestones, 25);
  await Promise.all(
    batches.map((batch) =>
      dynamo.send(
        new BatchWriteItemCommand({
          RequestItems: {
            'oms-milestones': batch.map((m) => ({
              PutRequest: { Item: marshall(m) },
            })),
          },
        }),
      ),
    ),
  );
}
```

---

## Local Development Setup

### Prerequisites

- Docker Desktop ≥ 4.x
- Node.js 20 LTS (`nvm use 20`)
- AWS CLI v2 (for LocalStack)

### docker-compose.yml

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:15-alpine
    ports: ["5432:5432"]
    environment:
      POSTGRES_USER: oms
      POSTGRES_PASSWORD: oms_dev
      POSTGRES_DB: oms_db
    volumes: ["pg_data:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U oms"]
      interval: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    command: redis-server --appendonly yes
    volumes: ["redis_data:/data"]

  localstack:
    image: localstack/localstack:3
    ports: ["4566:4566"]
    environment:
      SERVICES: s3,sqs,sns,events,secretsmanager
      DEFAULT_REGION: ap-south-1
      DEBUG: 0
    volumes:
      - "localstack_data:/var/lib/localstack"
      - "./scripts/localstack-init.sh:/etc/localstack/init/ready.d/init.sh"

  opensearch:
    image: opensearchproject/opensearch:2.12.0
    ports: ["9200:9200"]
    environment:
      discovery.type: single-node
      DISABLE_SECURITY_PLUGIN: "true"
    volumes: ["opensearch_data:/usr/share/opensearch/data"]

volumes:
  pg_data:
  redis_data:
  localstack_data:
  opensearch_data:
```

### Local Environment Variables (.env.local)

```bash
# Database
DATABASE_URL=postgres://oms:oms_dev@localhost:5432/oms_db

# Redis
REDIS_URL=redis://localhost:6379

# LocalStack AWS services
AWS_ENDPOINT_URL=http://localhost:4566
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
EVENTBRIDGE_BUS_NAME=oms-events
S3_POD_BUCKET=oms-pod-artifacts-local

# Cognito (use a local mock or a dev Cognito pool)
COGNITO_USER_POOL_ID=ap-south-1_XXXXXXXXX
COGNITO_CLIENT_ID=XXXXXXXXXXXXXXXXXXXXXXXXXX

# OpenSearch
OPENSEARCH_URL=http://localhost:9200

# App
NODE_ENV=development
LOG_LEVEL=debug
```

### Starting the Local Stack

```bash
# 1. Start all backing services
docker compose up -d

# 2. Install all workspace dependencies
npm ci

# 3. Run database migrations for all services
./scripts/db-migrate.sh all local

# 4. Seed development data
npx ts-node scripts/seed-dev.ts

# 5. Run the order-service Lambda locally via SAM (optional)
cd packages/order-service
sam local start-api --env-vars .env.local

# 6. Run a Fargate service locally (e.g., fulfillment-service)
cd packages/fulfillment-service
npm run dev
```

### Useful Local Commands

```bash
# Run all unit tests across workspaces
npm run test:unit --workspaces

# Run integration tests (requires docker compose up -d)
npm run test:integration --workspaces

# Type-check all packages
npm run typecheck --workspaces

# Lint and auto-fix
npm run lint:fix --workspaces

# Build all packages
npm run build --workspaces

# CDK synth (local validation, no deploy)
cd infra && npx cdk synth --context env=local
```

---

## Git Workflow

- **Trunk-based development** with short-lived feature branches (max 2 days)
- Branch naming: `feat/order-cancellation`, `fix/pod-upload-retry`, `chore/upgrade-cdk`
- Commit messages: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`)
- PRs require 1 approval + CI green (lint, type-check, unit test, build)
- Merge via **squash merge** to main; branch deleted after merge
- Hotfixes use `hotfix/` prefix and deploy directly from main after expedited review

---

## Security Guidelines

- Never log or store raw PII (email, phone, payment tokens) outside the primary database
- Use AWS Secrets Manager for all credentials and API keys; never hardcode in source
- Rotate secrets every 90 days via Secrets Manager automatic rotation
- All S3 buckets: block public access, SSE-S3 encryption, versioning enabled, lifecycle rules
- Cognito: enforce MFA for admin and staff user pools; short-lived access tokens (1 hour)
- API Gateway: enable WAF with AWS Managed Rules, enable request validation schemas, set throttle limits
- Lambda execution roles: least-privilege IAM — each function gets its own role with only the resources it needs
- RDS: deployed in private subnets, no public IP, SSL required (`ssl-mode=verify-full`)
- ElastiCache: deployed in private subnets, in-transit encryption enabled, AUTH token required
- Input validation with Zod on every API boundary before data reaches the service layer
- Use `crypto.timingSafeEqual` for any HMAC or token comparison to prevent timing attacks
