# Code Guidelines — API Gateway and Developer Portal

---

## Table of Contents

1. [Overview](#1-overview)
2. [Repository Structure](#2-repository-structure)
3. [TypeScript Configuration](#3-typescript-configuration)
4. [Code Style](#4-code-style)
5. [Fastify Gateway Guidelines](#5-fastify-gateway-guidelines)
6. [Next.js Portal Guidelines](#6-nextjs-portal-guidelines)
7. [Database Guidelines](#7-database-guidelines)
8. [Redis Guidelines](#8-redis-guidelines)
9. [Testing Guidelines](#9-testing-guidelines)
10. [Security Guidelines](#10-security-guidelines)
11. [Observability Guidelines](#11-observability-guidelines)
12. [API Design Guidelines](#12-api-design-guidelines)
13. [Git and PR Guidelines](#13-git-and-pr-guidelines)

---

## 1. Overview

### Philosophy

This project is **TypeScript-first** throughout. Every package and application is written in strict TypeScript with no implicit `any`. The architectural philosophy is:

- **Functional core, OO shell**: Pure functions for business logic (easy to test, no side effects). Classes and interfaces for dependency injection boundaries, plugin contracts, and repository abstractions.
- **Explicit over implicit**: No magic. Every plugin registration, every middleware, every DB query is explicit and traceable.
- **Fail fast, fail loudly**: Validation happens at the edge. Errors carry structured context. Nothing silently swallows exceptions.
- **Security by default**: Rate limiting, auth, and input validation are on by default. Opt-out requires explicit configuration.

### Language Targets

| Package / App       | Target                            |
|---------------------|-----------------------------------|
| `apps/gateway`      | Node.js 20, ES2022 modules        |
| `apps/portal`       | Next.js 14 (React 18), ES2022     |
| `apps/admin`        | Next.js 14 (React 18), ES2022     |
| `packages/*`        | ES2022, CJS + ESM dual output     |

---

## 2. Repository Structure

```
api-gateway-portal/
├── apps/
│   ├── gateway/
│   │   ├── src/
│   │   │   ├── plugins/         # Fastify plugins (auth, rate-limit, cors, etc.)
│   │   │   ├── routes/          # Route handlers (admin, health)
│   │   │   ├── hooks/           # Fastify lifecycle hooks
│   │   │   └── server.ts        # Fastify instance factory
│   │   ├── test/
│   │   │   └── integration/     # Supertest integration tests
│   │   └── Dockerfile
│   ├── portal/
│   │   ├── src/
│   │   │   ├── app/             # App Router pages and layouts
│   │   │   ├── components/      # React components
│   │   │   ├── lib/             # Server-side utilities
│   │   │   └── actions/         # Next.js Server Actions
│   │   ├── e2e/                 # Playwright E2E tests
│   │   └── Dockerfile
│   └── admin/
│       └── src/
├── packages/
│   ├── shared/                  # Shared types, utilities, constants
│   │   └── src/
│   │       ├── types/
│   │       ├── utils/
│   │       └── errors/
│   ├── db/                      # PostgreSQL repository layer
│   │   └── src/
│   │       ├── client.ts
│   │       ├── migrations/
│   │       └── repositories/
│   ├── auth/                    # Auth plugin package
│   │   └── src/
│   │       ├── plugins/
│   │       ├── validators/
│   │       ├── services/
│   │       └── utils/
│   └── rate-limit/
│       └── src/
│           ├── limiters/
│           └── store/
├── infrastructure/
│   ├── terraform/
│   │   ├── modules/
│   │   ├── environments/
│   │   └── main.tf
│   └── k8s/
├── tests/
│   └── load/                    # k6 load test scripts
├── turbo.json
├── pnpm-workspace.yaml
└── package.json
```

### Package Ownership Rules

- `packages/shared` — no dependencies on other internal packages
- `packages/db` — depends on `packages/shared` only
- `packages/auth` — depends on `packages/shared`, `packages/db`
- `packages/rate-limit` — depends on `packages/shared`
- `apps/gateway` — depends on all packages
- `apps/portal` — depends on `packages/shared`, `packages/auth`

---

## 3. TypeScript Configuration

### Base tsconfig (`tsconfig.base.json` at root)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "exactOptionalPropertyTypes": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": false,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "paths": {
      "@gateway/shared": ["packages/shared/src/index.ts"],
      "@gateway/db": ["packages/db/src/index.ts"],
      "@gateway/auth": ["packages/auth/src/index.ts"],
      "@gateway/rate-limit": ["packages/rate-limit/src/index.ts"]
    }
  }
}
```

### Strict Rules Enforced

- `strict: true` — enables `strictNullChecks`, `strictFunctionTypes`, `strictBindCallApply`, `strictPropertyInitialization`, `noImplicitAny`, `noImplicitThis`, `alwaysStrict`
- `noUncheckedIndexedAccess: true` — array indexing returns `T | undefined`
- `exactOptionalPropertyTypes: true` — optional properties cannot be set to `undefined` explicitly

### Disallowed Patterns

```typescript
// Never use 'any'
const data: any = response.body; // ERROR

// Use unknown and narrow instead
const data: unknown = response.body;
if (typeof data === 'object' && data !== null && 'id' in data) {
  const typed = data as { id: string };
}

// Never use non-null assertion without an explanatory comment
const user = users[0]!; // ERROR

// Narrow explicitly instead
const user = users[0];
if (user === undefined) throw new NotFoundError('User not found');
```

---

## 4. Code Style

### ESLint Configuration (`.eslintrc.cjs`)

```js
module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  parserOptions: { project: './tsconfig.json', ecmaVersion: 2022 },
  extends: [
    'airbnb-typescript/base',
    'plugin:@typescript-eslint/recommended-type-checked',
    'plugin:unicorn/recommended',
    'prettier',
  ],
  rules: {
    'no-console': 'error',
    'import/prefer-default-export': 'off',
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/consistent-type-imports': ['error', { prefer: 'type-imports' }],
    'unicorn/prevent-abbreviations': 'off',
    'unicorn/no-null': 'off',
  },
};
```

### Prettier Configuration (`.prettierrc`)

```json
{
  "singleQuote": true,
  "trailingComma": "all",
  "semi": true,
  "printWidth": 100,
  "tabWidth": 2,
  "arrowParens": "always"
}
```

### Naming Conventions

| Entity                      | Convention              | Example                                   |
|-----------------------------|-------------------------|-------------------------------------------|
| Variables and functions     | `camelCase`             | `apiKeyHash`, `validateToken()`           |
| Classes and interfaces      | `PascalCase`            | `ApiKeyRepository`, `IAuthPlugin`         |
| Plugin contract interfaces  | `I` prefix + PascalCase | `IAuthPlugin`, `IRateLimiter`             |
| Constants                   | `SCREAMING_SNAKE_CASE`  | `MAX_RETRY_ATTEMPTS`, `DEFAULT_TTL_SECONDS` |
| Source files                | `kebab-case`            | `api-key-validator.ts`                    |
| React component files       | `PascalCase`            | `ApiKeyCard.tsx`                          |
| Directories                 | `kebab-case`            | `rate-limit/`, `token-cache/`             |
| Environment variables       | `SCREAMING_SNAKE_CASE`  | `DATABASE_URL`, `REDIS_HOST`              |
| Database columns            | `snake_case`            | `created_at`, `api_key_hash`              |
| JSON and API fields         | `camelCase`             | `createdAt`, `apiKeyHash`                 |

---

## 5. Fastify Gateway Guidelines

### Plugin Authoring Pattern

Every gateway feature is a Fastify plugin wrapped with `fastify-plugin`. The `fp()` wrapper breaks Fastify's encapsulation so decorators and dependencies are available across the entire instance.

```typescript
// packages/auth/src/plugins/api-key-auth.plugin.ts
import fp from 'fastify-plugin';
import type { FastifyPluginAsync, FastifyRequest } from 'fastify';
import { ApiKeyValidator } from '../validators/api-key-validator.js';
import { AuthError } from '../errors/auth-error.js';

export interface ApiKeyAuthPluginOptions {
  headerName?: string;
}

const apiKeyAuthPlugin: FastifyPluginAsync<ApiKeyAuthPluginOptions> = async (
  fastify,
  options,
) => {
  const headerName = options.headerName ?? 'x-api-key';

  fastify.decorate('apiKeyAuth', async (request: FastifyRequest) => {
    const rawKey = request.headers[headerName];
    if (typeof rawKey !== 'string' || rawKey.length === 0) {
      throw new AuthError('API key missing', 'MISSING_API_KEY', 401);
    }
    const result = await ApiKeyValidator.validate(rawKey);
    if (!result.valid) {
      throw new AuthError('Invalid API key', 'INVALID_API_KEY', 401);
    }
    request.consumerId = result.consumerId;
    request.apiKeyId = result.keyId;
  });
};

export default fp(apiKeyAuthPlugin, {
  name: 'api-key-auth',
  dependencies: ['@fastify/redis'],
});
```

### Route Schema Validation with AJV

All routes must declare a JSON Schema. Routes without a schema will fail the CI lint check.

```typescript
// apps/gateway/src/routes/admin/routes.ts
import type { FastifyPluginAsync } from 'fastify';

const createRouteBodySchema = {
  type: 'object',
  required: ['path', 'upstreamUrl', 'methods'],
  additionalProperties: false,
  properties: {
    path: { type: 'string', pattern: '^/[a-z0-9/_-]+$' },
    upstreamUrl: { type: 'string', format: 'uri' },
    methods: {
      type: 'array',
      items: { type: 'string', enum: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'] },
      minItems: 1,
    },
    authRequired: { type: 'boolean', default: true },
  },
} as const;

const adminRoutesPlugin: FastifyPluginAsync = async (fastify) => {
  fastify.post(
    '/admin/v1/routes',
    {
      schema: { body: createRouteBodySchema },
      onRequest: [fastify.adminAuth],
    },
    async (request, reply) => {
      const route = await fastify.routeRepository.create(request.body);
      return reply.status(201).send(route);
    },
  );
};

export default adminRoutesPlugin;
```

### Error Handling Pattern

Register a single `setErrorHandler` at the root instance. Every module throws typed errors from `packages/shared/errors/`. Never throw plain `new Error()` from route handlers.

```typescript
// apps/gateway/src/plugins/error-handler.plugin.ts
import fp from 'fastify-plugin';
import type { FastifyPluginAsync } from 'fastify';
import { AppError } from '@gateway/shared';

const errorHandlerPlugin: FastifyPluginAsync = async (fastify) => {
  fastify.setErrorHandler((error, request, reply) => {
    const traceId = request.id;

    if (error instanceof AppError) {
      request.log.warn({ err: error, traceId }, error.message);
      return reply.status(error.statusCode).send({
        error: {
          code: error.code,
          message: error.message,
          details: error.details ?? null,
          traceId,
        },
      });
    }

    if (error.validation !== undefined) {
      request.log.warn({ validation: error.validation, traceId }, 'Validation error');
      return reply.status(400).send({
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Request validation failed',
          details: error.validation,
          traceId,
        },
      });
    }

    request.log.error({ err: error, traceId }, 'Unhandled error');
    return reply.status(500).send({
      error: { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred', traceId },
    });
  });
};

export default fp(errorHandlerPlugin, { name: 'error-handler' });
```

### Decorators and Type Augmentation

Extend Fastify's type system when adding decorators. Never cast `request` to `any` to access custom properties.

```typescript
// apps/gateway/src/types/fastify.d.ts
import 'fastify';

declare module 'fastify' {
  interface FastifyRequest {
    consumerId: string;
    apiKeyId: string;
    scopes: string[];
  }
  interface FastifyInstance {
    apiKeyAuth: (request: FastifyRequest) => Promise<void>;
    jwtAuth: (request: FastifyRequest) => Promise<void>;
    adminAuth: (request: FastifyRequest) => Promise<void>;
    routeRepository: import('@gateway/db').RouteRepository;
    consumerRepository: import('@gateway/db').ConsumerRepository;
  }
}
```

---

## 6. Next.js Portal Guidelines

### App Router Conventions

- **Server Components by default.** Only add `'use client'` when the component needs browser APIs, `useState`, or `useEffect`.
- **Route groups** (parentheses folders) share layouts without affecting the URL path.
- Every segment that fetches data should have a `loading.tsx` (streaming skeleton) and `error.tsx` (error boundary).

### Server Actions Pattern

Use Server Actions for all mutations. Do not create internal API routes for form submissions that could be Server Actions instead.

```typescript
// app/actions/api-key-actions.ts
'use server';

import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { getSession } from '@/lib/auth/session';
import { createApiKey, revokeApiKey } from '@/lib/api/keys';

export async function createKeyAction(formData: FormData) {
  const session = await getSession();
  if (!session) redirect('/login');

  const name = formData.get('name');
  if (typeof name !== 'string' || name.trim().length === 0) {
    return { error: 'Name is required' };
  }

  const key = await createApiKey({ consumerId: session.consumerId, name: name.trim() });
  revalidatePath('/dashboard/keys');
  return { success: true, key };
}

export async function revokeKeyAction(keyId: string) {
  const session = await getSession();
  if (!session) redirect('/login');

  await revokeApiKey({ keyId, consumerId: session.consumerId });
  revalidatePath('/dashboard/keys');
}
```

### Data Fetching with Cache Directives

```typescript
// app/dashboard/page.tsx (Server Component)
import { getConsumerUsage } from '@/lib/api/usage';

// This page is dynamically rendered per request (no caching)
export const dynamic = 'force-dynamic';

export default async function DashboardPage() {
  const usage = await getConsumerUsage({ days: 30 });
  return <UsageDashboard data={usage} />;
}

// lib/api/usage.ts
export async function getConsumerUsage(params: { days: number }) {
  const res = await fetch(
    `${process.env.GATEWAY_INTERNAL_URL}/v1/usage?days=${params.days}`,
    {
      next: { revalidate: 60 }, // Cache for 60 seconds
      headers: { Authorization: `Bearer ${process.env.GATEWAY_SERVICE_TOKEN}` },
    },
  );
  if (!res.ok) throw new Error('Failed to fetch usage data');
  return res.json();
}
```

### Error Boundaries and Loading States

```typescript
// app/dashboard/error.tsx
'use client';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div role="alert">
      <h2>Something went wrong loading your dashboard.</h2>
      <button onClick={reset}>Try again</button>
    </div>
  );
}
```

---

## 7. Database Guidelines

### Connection Pooling with node-postgres

Use a single `pg.Pool` singleton per process. Never create a new pool per request.

```typescript
// packages/db/src/client.ts
import { Pool } from 'pg';

let pool: Pool | undefined;

export function getPool(): Pool {
  if (pool === undefined) {
    pool = new Pool({
      connectionString: process.env['DATABASE_URL'],
      max: 20,
      idleTimeoutMillis: 30_000,
      connectionTimeoutMillis: 2_000,
    });
    pool.on('error', (err) => {
      // Pino logger is not available here; use process.stderr
      process.stderr.write(`[db] Idle client error: ${err.message}\n`);
    });
  }
  return pool;
}
```

### Repository Pattern with Typed Queries

Each entity has a dedicated repository class. Repositories accept a `Pool` or `PoolClient` (for transactions) via the constructor.

```typescript
// packages/db/src/repositories/api-key.repository.ts
import type { Pool, PoolClient } from 'pg';
import type { ApiKey, CreateApiKeyInput } from '@gateway/shared';

export class ApiKeyRepository {
  constructor(private readonly db: Pool | PoolClient) {}

  async findByPrefix(prefix: string): Promise<ApiKey | null> {
    const result = await this.db.query<ApiKey>(
      'SELECT id, prefix, key_hash, consumer_id, name, scopes, created_at, revoked_at ' +
        'FROM api_keys WHERE prefix = $1 AND revoked_at IS NULL LIMIT 1',
      [prefix],
    );
    return result.rows[0] ?? null;
  }

  async create(input: CreateApiKeyInput): Promise<ApiKey> {
    const result = await this.db.query<ApiKey>(
      `INSERT INTO api_keys (id, prefix, key_hash, consumer_id, name, scopes)
       VALUES (gen_random_uuid(), $1, $2, $3, $4, $5)
       RETURNING *`,
      [input.prefix, input.keyHash, input.consumerId, input.name, input.scopes],
    );
    const row = result.rows[0];
    if (row === undefined) throw new Error('Insert did not return a row');
    return row;
  }

  async revoke(id: string): Promise<void> {
    await this.db.query(
      'UPDATE api_keys SET revoked_at = NOW() WHERE id = $1',
      [id],
    );
  }
}
```

### SQL Safety Rules

- **Never use string interpolation or concatenation** to build SQL. Always use parameterized queries (`$1`, `$2`, ...).
- **Never** use raw `query(sql + userInput)`. This is an immediate security rejection in code review.

```typescript
// FORBIDDEN — SQL injection risk
const rows = await db.query(`SELECT * FROM users WHERE email = '${email}'`);

// REQUIRED — parameterized query
const rows = await db.query('SELECT * FROM users WHERE email = $1', [email]);
```

### Transaction Pattern

```typescript
// packages/db/src/utils/transaction.ts
import type { Pool } from 'pg';

export async function withTransaction<T>(
  pool: Pool,
  fn: (client: import('pg').PoolClient) => Promise<T>,
): Promise<T> {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const result = await fn(client);
    await client.query('COMMIT');
    return result;
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}

// Usage:
const result = await withTransaction(pool, async (client) => {
  const repo = new ApiKeyRepository(client);
  await repo.revoke(oldKeyId);
  return repo.create(newKeyInput);
});
```

---

## 8. Redis Guidelines

### ioredis Client Configuration

```typescript
// packages/rate-limit/src/store/redis-client.ts
import Redis from 'ioredis';

export function createRedisClient(): Redis {
  return new Redis({
    host: process.env['REDIS_HOST'],
    port: Number(process.env['REDIS_PORT'] ?? 6379),
    password: process.env['REDIS_PASSWORD'],
    tls: process.env['REDIS_TLS'] === 'true' ? {} : undefined,
    maxRetriesPerRequest: 3,
    retryStrategy: (times) => Math.min(times * 100, 3000),
    lazyConnect: false,
  });
}
```

### Key Naming Convention

All Redis keys must follow the pattern: `{service}:{entity}:{id}:{field}`

| Key Type              | Pattern                                    | Example                                     |
|-----------------------|--------------------------------------------|---------------------------------------------|
| Rate limit counter    | `ratelimit:key:{apiKeyId}:counter`         | `ratelimit:key:abc123:counter`              |
| Token cache           | `auth:token:{tokenHash}:payload`           | `auth:token:sha256hex:payload`              |
| Consumer plan         | `consumer:{consumerId}:plan`               | `consumer:uuid-v4:plan`                     |
| Quota counter         | `quota:{consumerId}:{yearMonth}`           | `quota:uuid-v4:2024-01`                     |
| OAuth state           | `oauth:state:{stateValue}`                 | `oauth:state:random-string`                 |
| Refresh token         | `auth:refresh:{tokenHash}`                 | `auth:refresh:sha256hex`                    |

### TTL Policies

| Key Type            | TTL        | Reason                                          |
|---------------------|------------|-------------------------------------------------|
| Rate limit counter  | 60 seconds | Sliding window resets each minute               |
| Access token cache  | 300 seconds| Matches JWT expiry (5 minutes)                  |
| Refresh token       | 2592000 s  | 30-day rotation window                          |
| Consumer plan cache | 3600 seconds| Re-read from DB hourly to catch plan changes   |
| OAuth state         | 600 seconds| PKCE state expires after 10 minutes             |
| Quota counter       | 2678400 s  | 31-day TTL — covers longest month               |

### Lua Scripting for Atomic Rate Limit Operations

```typescript
// packages/rate-limit/src/store/redis-store.ts
import type Redis from 'ioredis';

const SLIDING_WINDOW_SCRIPT = `
local key = KEYS[1]
local window = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local clearBefore = now - window

redis.call('ZREMRANGEBYSCORE', key, '-inf', clearBefore)
local count = redis.call('ZCARD', key)

if count < limit then
  redis.call('ZADD', key, now, now .. math.random())
  redis.call('EXPIRE', key, window)
  return {1, limit - count - 1, 0}
else
  local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
  local resetAt = tonumber(oldest[2]) + window
  return {0, 0, resetAt}
end
`;

export class RedisStore {
  private readonly script: string;

  constructor(private readonly redis: Redis) {
    this.script = SLIDING_WINDOW_SCRIPT;
  }

  async slidingWindowCheck(
    key: string,
    windowSeconds: number,
    limit: number,
  ): Promise<{ allowed: boolean; remaining: number; resetAt: number }> {
    const now = Date.now();
    const result = await this.redis.eval(
      this.script,
      1,
      key,
      String(windowSeconds * 1000),
      String(limit),
      String(now),
    ) as [number, number, number];

    return {
      allowed: result[0] === 1,
      remaining: result[1],
      resetAt: result[2],
    };
  }
}
```

---

## 9. Testing Guidelines

### Vitest for Unit Tests

- Unit test files are **colocated** with source files: `api-key-validator.test.ts` alongside `api-key-validator.ts`
- Tests use the `describe` / `it` pattern
- Test naming: `it('should [expected behavior] when [condition or input]')`

```typescript
// packages/auth/src/validators/api-key-validator.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiKeyValidator } from './api-key-validator.js';
import { ApiKeyRepository } from '@gateway/db';

vi.mock('@gateway/db');

describe('ApiKeyValidator', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should return valid result when key matches stored hash', async () => {
    vi.mocked(ApiKeyRepository.prototype.findByPrefix).mockResolvedValue({
      id: 'key-id',
      keyHash: 'hashed-value',
      consumerId: 'consumer-123',
      revokedAt: null,
    });

    const result = await ApiKeyValidator.validate('prefix.rawsecret');
    expect(result.valid).toBe(true);
    expect(result.consumerId).toBe('consumer-123');
  });

  it('should return invalid result when key hash does not match', async () => {
    vi.mocked(ApiKeyRepository.prototype.findByPrefix).mockResolvedValue({
      id: 'key-id',
      keyHash: 'different-hash',
      consumerId: 'consumer-123',
      revokedAt: null,
    });

    const result = await ApiKeyValidator.validate('prefix.wrongsecret');
    expect(result.valid).toBe(false);
  });

  it('should return invalid result when key prefix does not exist', async () => {
    vi.mocked(ApiKeyRepository.prototype.findByPrefix).mockResolvedValue(null);

    const result = await ApiKeyValidator.validate('unknown.rawsecret');
    expect(result.valid).toBe(false);
  });
});
```

### Supertest for Integration Tests

Integration tests start a real Fastify instance and use Testcontainers for real PostgreSQL and Redis instances.

```typescript
// apps/gateway/test/integration/rate-limit.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import supertest from 'supertest';
import { PostgreSqlContainer } from '@testcontainers/postgresql';
import { RedisContainer } from '@testcontainers/redis';
import { buildApp } from '../../src/server.js';

describe('Rate Limiting Integration', () => {
  let app: Awaited<ReturnType<typeof buildApp>>;
  let request: ReturnType<typeof supertest>;

  beforeAll(async () => {
    const postgres = await new PostgreSqlContainer().start();
    const redis = await new RedisContainer().start();

    app = await buildApp({
      databaseUrl: postgres.getConnectionUri(),
      redisUrl: redis.getConnectionUrl(),
    });
    await app.ready();
    request = supertest(app.server);
  });

  afterAll(() => app.close());

  it('should return 429 when rate limit is exceeded', async () => {
    const key = 'test.validkey';
    for (let i = 0; i < 10; i++) {
      await request.get('/v1/test').set('x-api-key', key);
    }
    const response = await request.get('/v1/test').set('x-api-key', key);

    expect(response.status).toBe(429);
    expect(response.headers['retry-after']).toBeDefined();
    expect(response.body.error.code).toBe('RATE_LIMIT_EXCEEDED');
  });
});
```

### Mock Strategy

- `vi.mock()` for module-level mocks (repositories, external services)
- **Testcontainers** for integration tests that require real DB or Redis behavior
- Never mock `crypto` — use real HMAC operations in tests to catch algorithm bugs
- Mock `Date.now()` explicitly in rate-limiting tests: `vi.setSystemTime(new Date(...))`

### Coverage Requirements

| Module                    | Minimum Coverage |
|---------------------------|-----------------|
| `packages/auth/`          | 100%            |
| `packages/rate-limit/`    | 100%            |
| `packages/db/`            | 90%             |
| `apps/gateway/src/`       | 80%             |
| `apps/portal/src/`        | 70%             |
| Overall                   | 80%             |

Configure in `vitest.config.ts`:

```typescript
export default {
  test: {
    coverage: {
      provider: 'v8',
      thresholds: { global: { lines: 80, functions: 80, branches: 75 } },
      include: ['packages/*/src/**', 'apps/*/src/**'],
    },
  },
};
```

---

## 10. Security Guidelines

### Sensitive Data in Logs

**Never log the following**: API keys (raw or prefixed), JWT tokens, OAuth client secrets, passwords, credit card numbers, Social Security numbers, or any PII (email in debug logs only, never in error logs).

```typescript
// FORBIDDEN — leaks API key
fastify.log.info({ apiKey: request.headers['x-api-key'] }, 'Request received');

// CORRECT — log only the non-sensitive identifier
fastify.log.info({ apiKeyPrefix: rawKey.split('.')[0], consumerId }, 'Request authenticated');
```

### Input Validation

All user-supplied input must pass through AJV JSON Schema validation before being used in any business logic or database query. The schema is the contract — anything not in the schema is rejected by `additionalProperties: false`.

### Timing-Safe Key Comparison

API key validation must use `crypto.timingSafeEqual` to prevent timing attacks. Never use `===` or `String.compare` for secrets.

```typescript
// packages/auth/src/utils/hmac-sha256.ts
import { createHmac, timingSafeEqual } from 'node:crypto';

export class HmacSha256 {
  static sign(secret: string, data: string): string {
    return createHmac('sha256', secret).update(data).digest('hex');
  }

  static timingSafeCompare(a: string, b: string): boolean {
    if (a.length !== b.length) return false;
    return timingSafeEqual(Buffer.from(a, 'hex'), Buffer.from(b, 'hex'));
  }
}
```

### Secrets Management Rules

- Secrets come from environment variables injected by AWS Secrets Manager at ECS task startup
- Zero secrets in source code, `.env` files checked into git, or Docker images
- `dotenv` is only used in local development via `.env.local` which is in `.gitignore`
- The CI security scan step runs `git-secrets --scan` and fails the build on any detected secret

### Dependency Auditing

- `npm audit --audit-level=high` runs in the CI security scan stage
- Dependabot is configured to create PRs for dependency updates weekly
- Trivy scans Docker images and fails the build on any `CRITICAL` CVE

---

## 11. Observability Guidelines

### OpenTelemetry Spans for Every Route

Every Fastify route must produce an OpenTelemetry span. The `@opentelemetry/instrumentation-fastify` package handles this automatically when the SDK is initialized before the Fastify instance.

```typescript
// apps/gateway/src/telemetry.ts  (must be imported FIRST in server.ts)
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { FastifyInstrumentation } from '@opentelemetry/instrumentation-fastify';
import { PgInstrumentation } from '@opentelemetry/instrumentation-pg';
import { IORedisInstrumentation } from '@opentelemetry/instrumentation-ioredis';

const sdk = new NodeSDK({
  serviceName: 'api-gateway',
  traceExporter: new OTLPTraceExporter({
    url: process.env['OTEL_EXPORTER_OTLP_ENDPOINT'],
  }),
  instrumentations: [
    new FastifyInstrumentation(),
    new PgInstrumentation(),
    new IORedisInstrumentation(),
  ],
});

sdk.start();
```

### Structured Logging with Pino

The Fastify logger uses Pino in JSON format. Every log line must include a `correlationId`.

```typescript
// apps/gateway/src/plugins/correlation-id.plugin.ts
import fp from 'fastify-plugin';
import { randomUUID } from 'node:crypto';

export default fp(async (fastify) => {
  fastify.addHook('onRequest', async (request) => {
    request.id = request.headers['x-correlation-id'] as string ?? randomUUID();
  });

  fastify.addHook('onSend', async (request, reply) => {
    void reply.header('x-correlation-id', request.id);
  });
});
```

### Log Level Policy

| Level   | When to Use                                                              |
|---------|--------------------------------------------------------------------------|
| `error` | Unhandled exceptions, system failures, data integrity issues             |
| `warn`  | Business rule violations (auth failure, rate limit, quota exceeded)      |
| `info`  | Lifecycle events (server start, plugin loaded, migration run)            |
| `debug` | Detailed flow tracing (cache hit/miss, DB query, token validation step)  |

Never use `info` for per-request logging in production — use `debug` for request-level detail. The production log level is `warn` by default; `info` for ops windows; `debug` never in production.

### Correlation ID Propagation

```typescript
// Correlation ID must be passed to every downstream call
const upstream = await fetch(upstreamUrl, {
  headers: {
    'x-correlation-id': request.id,
    'x-forwarded-for': request.ip,
  },
});

// And must appear in every log line
request.log.info({ correlationId: request.id, upstreamStatus: upstream.status }, 'Proxied request');
```

---

## 12. API Design Guidelines

### RESTful Conventions

- Use nouns for resource paths: `/v1/consumers`, `/v1/api-keys`, `/v1/routes`
- Use HTTP verbs correctly: `GET` read, `POST` create, `PUT` full replace, `PATCH` partial update, `DELETE` remove
- Nested resources only one level deep: `/v1/consumers/{consumerId}/keys` (not `/v1/consumers/{id}/keys/{id}/scopes/{id}`)
- Use plural nouns for collections

### Error Response Format

All error responses follow this exact shape:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "You have exceeded the rate limit for this API key.",
    "details": {
      "limit": 1000,
      "windowSeconds": 60,
      "retryAfter": 45
    },
    "traceId": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

- `code`: Machine-readable `SCREAMING_SNAKE_CASE` string constant
- `message`: Human-readable sentence, suitable for display
- `details`: Structured additional context (nullable)
- `traceId`: Correlation ID from the request

### Pagination: Cursor-Based

```
GET /v1/consumers?limit=20&cursor=eyJpZCI6IjEyMyJ9

Response:
{
  "data": [...],
  "pagination": {
    "hasNextPage": true,
    "nextCursor": "eyJpZCI6IjE0MyJ9",
    "limit": 20
  }
}
```

Never use offset-based pagination for large datasets — cursor-based is required for all collection endpoints.

### Versioning

All routes carry a `/v1/` prefix. When breaking changes are needed, a `/v2/` prefix is added. The `v1` route is kept alive for a minimum of 12 months with a deprecation notice (`Deprecation` and `Sunset` headers).

---

## 13. Git and PR Guidelines

### Conventional Commits

All commit messages must follow the Conventional Commits specification:

```
<type>(<scope>): <short description>

[optional body]

[optional footer(s)]
```

| Type       | When to Use                                         |
|------------|-----------------------------------------------------|
| `feat`     | New feature                                         |
| `fix`      | Bug fix                                             |
| `chore`    | Build process, dependency updates, no logic change  |
| `refactor` | Code restructure with no behavior change            |
| `test`     | Adding or updating tests                            |
| `docs`     | Documentation changes only                         |
| `perf`     | Performance improvement                             |
| `ci`       | Changes to CI/CD configuration                      |

Examples:
```
feat(auth): add PKCE support to OAuth 2.0 authorization endpoint
fix(rate-limit): correct sliding window reset timestamp in Redis Lua script
test(gateway): add integration tests for admin route CRUD API
```

### Branch Naming

```
feature/PROJ-123-add-pkce-support
fix/PROJ-456-rate-limit-reset-bug
chore/PROJ-789-upgrade-fastify-5
refactor/PROJ-101-extract-token-cache
```

### PR Checklist (PR Template)

```markdown
## Summary
Brief description of what this PR does.

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Refactor
- [ ] Documentation

## Checklist
- [ ] TypeScript strict — zero `any` without justification comment
- [ ] ESLint and Prettier pass (`pnpm lint`)
- [ ] Unit tests added / updated
- [ ] Integration tests pass
- [ ] Coverage does not regress from baseline
- [ ] No sensitive data in logs
- [ ] OpenAPI spec updated (if endpoint changed)
- [ ] `npm audit` shows no new critical/high vulnerabilities
- [ ] Tested on staging (for significant changes)

## Related Issues
Closes #<issue_number>
```

### Merge Strategy

- **Squash merge** to `main` — one commit per PR, preserving the Conventional Commit type in the squash message
- **No direct pushes** to `main` — all changes via PR with at least one approval
- **Linear history** enforced — rebase instead of merge commits on feature branches
- Delete branches after merge (automated in GitHub repository settings)
