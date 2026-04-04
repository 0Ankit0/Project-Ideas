# Code Guidelines

## Overview

Development standards, conventions, and best practices for the Order Management and Delivery System codebase.

## Language and Runtime

- **Runtime:** Node.js 20 LTS
- **Language:** TypeScript 5.x (strict mode enabled)
- **IaC:** AWS CDK with TypeScript
- **Package Manager:** npm (lockfile committed)

## Project Structure

```
oms/
├── packages/
│   ├── shared/                  # Shared types, utils, constants
│   │   ├── src/
│   │   │   ├── types/           # Domain types and interfaces
│   │   │   ├── events/          # Event schemas and contracts
│   │   │   ├── errors/          # Custom error classes
│   │   │   └── utils/           # Common utilities
│   │   └── package.json
│   ├── order-service/           # Lambda handlers
│   │   ├── src/
│   │   │   ├── handlers/        # Lambda entry points
│   │   │   ├── services/        # Business logic
│   │   │   ├── repositories/    # Data access layer
│   │   │   └── middleware/      # Auth, validation, idempotency
│   │   └── package.json
│   ├── payment-service/         # Lambda handlers
│   ├── inventory-service/       # Lambda handlers
│   ├── notification-service/    # Lambda handlers
│   ├── fulfillment-service/     # Fargate application
│   ├── delivery-service/        # Fargate application
│   ├── return-service/          # Fargate application
│   └── analytics-service/       # Fargate application
├── infra/                       # CDK infrastructure
│   ├── lib/
│   │   ├── stacks/              # CDK stacks per environment
│   │   └── constructs/          # Reusable CDK constructs
│   └── bin/                     # CDK app entry point
├── scripts/                     # Operational scripts
└── docs/                        # This documentation set
```

## Coding Standards

### Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Files | kebab-case | `order-service.ts`, `payment-handler.ts` |
| Classes | PascalCase | `OrderService`, `DeliveryAssignment` |
| Interfaces | PascalCase with `I` prefix | `IOrderRepository`, `IPaymentGateway` |
| Functions | camelCase | `createOrder()`, `capturePayment()` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_DELIVERY_ATTEMPTS`, `RESERVATION_TTL_MS` |
| Env vars | SCREAMING_SNAKE_CASE | `DATABASE_URL`, `PAYMENT_GATEWAY_API_KEY` |
| Event types | dot-separated, versioned | `oms.order.confirmed.v1` |
| API routes | kebab-case, plural nouns | `/orders`, `/delivery-zones` |

### Error Handling

```typescript
// Custom error hierarchy
class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number,
    public readonly details?: Record<string, unknown>,
  ) {
    super(message);
  }
}

class NotFoundError extends AppError {
  constructor(resource: string, id: string) {
    super(`${resource} not found`, 'NOT_FOUND', 404, { resource, id });
  }
}

class ConflictError extends AppError {
  constructor(reason: string) {
    super(reason, 'CONFLICT', 409);
  }
}

// All handlers must catch and transform errors
// No raw exceptions should reach the API response
```

### Dependency Injection

- Use constructor injection for all service dependencies
- Repository interfaces define data access contracts
- Gateway interfaces abstract external service calls
- This enables unit testing with mocks without infrastructure

### Logging

```typescript
// Structured JSON logging with correlation
const logger = createLogger({
  service: 'order-service',
  correlationId: event.headers['x-correlation-id'],
});

logger.info('Order created', {
  orderId: order.id,
  customerId: order.customerId,
  total: order.totalAmount,
});
```

- Log level: `DEBUG` in dev, `INFO` in production
- Sensitive fields (email, phone, payment tokens) must be redacted in logs
- Every log entry must include `correlationId` for distributed tracing

### Testing Standards

| Level | Coverage Target | Framework | Scope |
|---|---|---|---|
| Unit | > 80% | Jest | Service logic, validators, calculators |
| Integration | Key flows | Jest + testcontainers | Repository ↔ PostgreSQL, EventBridge publishing |
| E2E | Critical paths | Playwright | Checkout, delivery status update, return flow |
| Contract | All events | JSON Schema validation | Event producer ↔ consumer contract |

### Git Workflow

- **Trunk-based development** with short-lived feature branches
- Branch naming: `feat/order-cancellation`, `fix/pod-upload-retry`, `chore/upgrade-cdk`
- Commit messages: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)
- PRs require 1 approval + CI green (lint, test, build)
- Merge via squash merge to main

### CI/CD Pipeline

```
commit → lint → unit test → build → integration test → deploy staging → smoke test → manual approval → deploy production (canary)
```

## Performance Guidelines

- Lambda functions: target < 500 ms cold start; < 200 ms warm execution
- Database queries: use prepared statements; index all WHERE/JOIN columns
- ElastiCache: use for all hot-path reads (cart, session, idempotency)
- Batch DynamoDB writes where possible (BatchWriteItem)
- S3 uploads: use presigned URLs for direct client upload
- API responses: target < 500 ms P95 end-to-end

## Security Guidelines

- Never log or store raw PII outside of the primary database
- Use AWS Secrets Manager for all credentials and API keys
- Rotate secrets every 90 days (automated via Secrets Manager)
- All S3 buckets: block public access, SSE-S3 encryption, versioning enabled
- Cognito: enforce MFA for admin and staff roles
- API Gateway: enable WAF, enable request validation schemas
