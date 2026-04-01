# Code Guidelines — Real Estate Management System

## Tech Stack Overview

| Layer | Technology | Version |
|---|---|---|
| Runtime | Node.js LTS | 20.x |
| Language | TypeScript | 5.x |
| Primary DB | PostgreSQL + PostGIS | 15 + 3.4 |
| Search | Elasticsearch | 8.x |
| Cache / Streams | Redis | 7.x |
| Container | Docker | 24.x |
| Orchestration | Kubernetes | 1.29 |
| ORM / Query Builder | pg + node-pg-migrate | latest |
| HTTP Framework | Fastify | 4.x |
| Validation | Zod | 3.x |
| Logger | pino | 8.x |
| DI Container | tsyringe | 4.x |
| Test Runner | Jest + Supertest | 29.x |

All services follow a **hexagonal architecture** (ports and adapters). Domain logic is isolated from infrastructure, HTTP, and persistence concerns. Every boundary is expressed as a TypeScript interface.

---

## TypeScript Standards

### Strict Mode

Every package in the monorepo extends a shared base `tsconfig.json`:

```json
// tsconfig.base.json (workspace root)
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "lib": ["ES2022"],
    "strict": true,
    "noImplicitAny": true,
    "noImplicitReturns": true,
    "noImplicitOverride": true,
    "noUncheckedIndexedAccess": true,
    "noPropertyAccessFromIndexSignature": true,
    "exactOptionalPropertyTypes": true,
    "forceConsistentCasingInFileNames": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "skipLibCheck": false,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "dist",
    "rootDir": "src",
    "emitDecoratorMetadata": true,
    "experimentalDecorators": true
  }
}
```

Individual package `tsconfig.json` files extend the base and override only `paths` or `references`.

### Naming Conventions

| Construct | Convention | Example |
|---|---|---|
| Classes | PascalCase | `PropertyService`, `LeaseRepository` |
| Interfaces | PascalCase (no `I` prefix) | `LeaseRepository`, `EventPublisher` |
| Functions / methods | camelCase | `findPropertiesNearby()` |
| Constants (module-level) | SCREAMING_SNAKE_CASE | `MAX_SEARCH_RADIUS_KM` |
| Enum members | SCREAMING_SNAKE_CASE | `LeaseStatus.ACTIVE` |
| Files | kebab-case | `lease-service.ts`, `property.entity.ts` |
| Test files | `<subject>.spec.ts` or `<subject>.test.ts` | `lease-service.spec.ts` |
| Environment variables | SCREAMING_SNAKE_CASE | `DATABASE_URL`, `REDIS_HOST` |

### Branded Types for Domain IDs

Never use raw `string` for domain identifiers. Brand every ID type to prevent accidental cross-domain substitution.

```typescript
// packages/shared/src/types/branded.ts
declare const __brand: unique symbol;
type Brand<T, B> = T & { readonly [__brand]: B };

export type PropertyId = Brand<string, 'PropertyId'>;
export type UnitId     = Brand<string, 'UnitId'>;
export type LeaseId    = Brand<string, 'LeaseId'>;
export type TenantId   = Brand<string, 'TenantId'>;
export type OwnerId    = Brand<string, 'OwnerId'>;
export type VendorId   = Brand<string, 'VendorId'>;

// Factory functions perform UUID validation at runtime
import { randomUUID } from 'crypto';

export function newPropertyId(): PropertyId {
  return randomUUID() as PropertyId;
}
export function toPropertyId(raw: string): PropertyId {
  if (!/^[0-9a-f-]{36}$/.test(raw)) throw new ValidationError(`Invalid PropertyId: ${raw}`);
  return raw as PropertyId;
}
```

The TypeScript compiler will reject `findById(leaseId as PropertyId)` — a category of bugs eliminated at compile time.

### No `any` Policy

`noImplicitAny: true` is set globally. Explicit `any` casts require a `// eslint-disable-next-line @typescript-eslint/no-explicit-any` comment **plus** a JSDoc comment explaining why. An ESLint rule enforces this:

```json
// .eslintrc.json
{
  "rules": {
    "@typescript-eslint/no-explicit-any": ["error", { "ignoreRestArgs": false }],
    "@typescript-eslint/no-unsafe-assignment": "error",
    "@typescript-eslint/no-unsafe-call": "error",
    "@typescript-eslint/no-unsafe-member-access": "error",
    "@typescript-eslint/no-unsafe-return": "error"
  }
}
```

### Discriminated Unions for Domain States

Use discriminated unions rather than optional fields to model state machines:

```typescript
// packages/lease-service/src/domain/lease.ts
export type LeaseState =
  | { status: 'DRAFT';             draftedAt: Date }
  | { status: 'PENDING_SIGNATURE'; sentAt: Date; signingUrl: string }
  | { status: 'ACTIVE';            startDate: Date; endDate: Date }
  | { status: 'TERMINATED';        terminatedAt: Date; reason: string }
  | { status: 'EXPIRED';           expiredAt: Date };

// Exhaustive pattern matching is enforced at compile time
function describeState(state: LeaseState): string {
  switch (state.status) {
    case 'DRAFT':             return `Draft created at ${state.draftedAt.toISOString()}`;
    case 'PENDING_SIGNATURE': return `Awaiting signature, url: ${state.signingUrl}`;
    case 'ACTIVE':            return `Active until ${state.endDate.toISOString()}`;
    case 'TERMINATED':        return `Terminated: ${state.reason}`;
    case 'EXPIRED':           return `Expired at ${state.expiredAt.toISOString()}`;
  }
}
```

### Required Type Annotations

- All function parameters and return types must be explicitly annotated (inferred return types are banned on exported functions via ESLint `@typescript-eslint/explicit-module-boundary-types`).
- Object literals passed to external libraries that accept `unknown` must be explicitly typed.
- `Promise<void>` must be returned and `await`ed; floating promises are banned via `@typescript-eslint/no-floating-promises`.

---

## Architecture Patterns

### Repository Pattern

Every aggregate root has a **repository interface** defined in the domain layer. Infrastructure provides the implementation.

```typescript
// packages/property-service/src/domain/repositories/property.repository.ts
import type { PropertyId, UnitId } from '@rems/shared';
import type { PropertyEntity } from '../entities/property.entity';
import type { GeoPoint, RadiusSearchParams } from '../value-objects/geo.vo';

export interface PropertyRepository {
  findById(id: PropertyId): Promise<PropertyEntity | null>;
  save(property: PropertyEntity): Promise<void>;
  delete(id: PropertyId): Promise<void>;
  findByOwner(ownerId: string): Promise<PropertyEntity[]>;
  findWithinRadius(center: GeoPoint, params: RadiusSearchParams): Promise<PropertyEntity[]>;
}
```

```typescript
// packages/property-service/src/infrastructure/db/postgres-property.repository.ts
import { injectable, inject } from 'tsyringe';
import type { Pool } from 'pg';
import { TOKENS } from '../../container/tokens';
import type { PropertyRepository } from '../../domain/repositories/property.repository';
import type { PropertyEntity } from '../../domain/entities/property.entity';
import type { PropertyId } from '@rems/shared';
import { NotFoundError } from '@rems/shared';
import { mapRowToProperty } from './mappers/property.mapper';

@injectable()
export class PostgresPropertyRepository implements PropertyRepository {
  constructor(@inject(TOKENS.PgPool) private readonly pool: Pool) {}

  async findById(id: PropertyId): Promise<PropertyEntity | null> {
    const { rows } = await this.pool.query<PropertyRow>(
      `SELECT p.*, ST_AsGeoJSON(p.location)::json AS location_geojson
         FROM properties p
        WHERE p.id = $1 AND p.deleted_at IS NULL`,
      [id],
    );
    return rows[0] ? mapRowToProperty(rows[0]) : null;
  }

  async findWithinRadius(
    center: GeoPoint,
    params: RadiusSearchParams,
  ): Promise<PropertyEntity[]> {
    const { rows } = await this.pool.query<PropertyRow>(
      `SELECT p.*, ST_AsGeoJSON(p.location)::json AS location_geojson,
              ST_Distance(p.location::geography, ST_MakePoint($1,$2)::geography) AS distance_m
         FROM properties p
        WHERE ST_DWithin(
                p.location::geography,
                ST_MakePoint($1, $2)::geography,
                $3
              )
          AND p.status = 'LISTED'
          AND p.deleted_at IS NULL
        ORDER BY distance_m ASC
        LIMIT $4`,
      [center.lng, center.lat, params.radiusMeters, params.limit ?? 50],
    );
    return rows.map(mapRowToProperty);
  }

  async save(property: PropertyEntity): Promise<void> {
    await this.pool.query(
      `INSERT INTO properties (id, owner_id, address, location, property_type, status, created_at, updated_at)
       VALUES ($1, $2, $3, ST_SetSRID(ST_MakePoint($4, $5), 4326), $6, $7, NOW(), NOW())
       ON CONFLICT (id) DO UPDATE
         SET address = EXCLUDED.address,
             location = EXCLUDED.location,
             property_type = EXCLUDED.property_type,
             status = EXCLUDED.status,
             updated_at = NOW()`,
      [
        property.id,
        property.ownerId,
        property.address,
        property.location.lng,
        property.location.lat,
        property.propertyType,
        property.status,
      ],
    );
  }

  async delete(id: PropertyId): Promise<void> {
    await this.pool.query(
      `UPDATE properties SET deleted_at = NOW() WHERE id = $1`,
      [id],
    );
  }

  async findByOwner(ownerId: string): Promise<PropertyEntity[]> {
    const { rows } = await this.pool.query<PropertyRow>(
      `SELECT p.*, ST_AsGeoJSON(p.location)::json AS location_geojson
         FROM properties p
        WHERE p.owner_id = $1 AND p.deleted_at IS NULL
        ORDER BY p.created_at DESC`,
      [ownerId],
    );
    return rows.map(mapRowToProperty);
  }
}
```

### CQRS for Search

The **command side** writes to PostgreSQL (the source of truth). An async **sync worker** reindexes changed properties into Elasticsearch. The **query side** reads directly from Elasticsearch for full-text and geo search.

```
HTTP POST /properties   →  PropertyService.create()  →  PostgreSQL  →  Redis Stream (property.created)
                                                                          ↓
                                                                  ElasticsearchSyncWorker
                                                                          ↓
                                                                     Elasticsearch index
HTTP GET  /properties/search  →  PropertySearchService.search()  →  Elasticsearch
```

The sync worker listens on the `rems:property:events` Redis stream:

```typescript
// packages/search-service/src/workers/es-sync.worker.ts
async function processEvent(event: PropertyEvent): Promise<void> {
  switch (event.type) {
    case 'property.created':
    case 'property.updated':
      await esClient.index({
        index: PROPERTY_INDEX,
        id: event.payload.id,
        document: toPropertyDocument(event.payload),
      });
      break;
    case 'property.deleted':
      await esClient.delete({ index: PROPERTY_INDEX, id: event.payload.id });
      break;
  }
}
```

### Domain Events

Domain events are published via Redis Streams. Each event carries a `correlationId` for distributed tracing.

```typescript
// packages/shared/src/events/domain-event.ts
export interface DomainEvent<T = unknown> {
  readonly id: string;
  readonly type: string;
  readonly occurredAt: string;   // ISO 8601
  readonly correlationId: string;
  readonly payload: T;
}

// Publisher
export interface EventPublisher {
  publish<T>(streamKey: string, event: DomainEvent<T>): Promise<void>;
}
```

```typescript
// packages/shared/src/events/redis-event-publisher.ts
@injectable()
export class RedisEventPublisher implements EventPublisher {
  constructor(@inject(TOKENS.RedisClient) private readonly redis: Redis) {}

  async publish<T>(streamKey: string, event: DomainEvent<T>): Promise<void> {
    await this.redis.xadd(
      streamKey,
      '*',
      'event_id',    event.id,
      'type',        event.type,
      'occurred_at', event.occurredAt,
      'correlation', event.correlationId,
      'payload',     JSON.stringify(event.payload),
    );
  }
}
```

### Service Layer Responsibilities

- Orchestrate repository calls and domain logic.
- Validate command inputs (Zod schemas are invoked here, not in controllers).
- Publish domain events after state-changing operations.
- Never contain SQL — all persistence is delegated to repositories.
- Never contain HTTP-specific concerns (request/response objects).

---

## Project Structure

```
rems/                                   # monorepo root
├── packages/
│   ├── shared/                         # cross-cutting types, events, errors
│   │   └── src/
│   │       ├── types/branded.ts
│   │       ├── errors/app-error.ts
│   │       ├── events/domain-event.ts
│   │       └── validation/schemas.ts
│   ├── property-service/
│   │   └── src/
│   │       ├── domain/
│   │       │   ├── entities/property.entity.ts
│   │       │   ├── repositories/property.repository.ts
│   │       │   └── value-objects/geo.vo.ts
│   │       ├── application/
│   │       │   ├── commands/create-property.command.ts
│   │       │   └── services/property.service.ts
│   │       ├── infrastructure/
│   │       │   ├── db/postgres-property.repository.ts
│   │       │   └── storage/s3-image.storage.ts
│   │       ├── http/
│   │       │   ├── controllers/property.controller.ts
│   │       │   └── routes/property.routes.ts
│   │       └── container/
│   │           ├── tokens.ts
│   │           └── setup.ts
│   ├── lease-service/
│   │   └── src/
│   │       ├── domain/
│   │       ├── application/
│   │       ├── infrastructure/
│   │       ├── http/
│   │       └── container/
│   ├── tenant-service/
│   ├── maintenance-service/
│   ├── payment-service/
│   └── search-service/
├── infra/
│   ├── k8s/
│   │   ├── base/
│   │   └── overlays/
│   ├── docker/
│   └── terraform/
├── migrations/
│   ├── 001_create_properties.sql
│   ├── 002_create_units.sql
│   └── ...
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
├── package.json                        # workspaces config
└── tsconfig.base.json
```

---

## Database Guidelines

### Migration Strategy

Use `node-pg-migrate`. Migrations live in `migrations/` at the repo root and are applied in CI before tests and before deployment.

```typescript
// migrations/001_create_properties.ts
import type { MigrationBuilder } from 'node-pg-migrate';

export const up = (pgm: MigrationBuilder): void => {
  pgm.createExtension('postgis', { ifNotExists: true });
  pgm.createExtension('uuid-ossp', { ifNotExists: true });

  pgm.createTable('properties', {
    id:            { type: 'uuid', primaryKey: true, default: pgm.func('uuid_generate_v4()') },
    owner_id:      { type: 'uuid', notNull: true },
    address:       { type: 'jsonb', notNull: true },
    location:      { type: 'geometry(Point,4326)', notNull: true },
    property_type: { type: 'text', notNull: true },
    status:        { type: 'text', notNull: true, default: "'DRAFT'" },
    metadata:      { type: 'jsonb', default: "'{}'" },
    created_at:    { type: 'timestamptz', notNull: true, default: pgm.func('NOW()') },
    updated_at:    { type: 'timestamptz', notNull: true, default: pgm.func('NOW()') },
    deleted_at:    { type: 'timestamptz' },
  });

  pgm.createIndex('properties', 'owner_id');
  pgm.createIndex('properties', 'status');
  pgm.sql(`CREATE INDEX idx_properties_location ON properties USING GIST (location)`);
  pgm.sql(`CREATE INDEX idx_properties_status_deleted ON properties (status) WHERE deleted_at IS NULL`);
};

export const down = (pgm: MigrationBuilder): void => {
  pgm.dropTable('properties');
};
```

### Indexing Rules

- Every foreign key column must have a B-tree index.
- Columns used in `WHERE` clauses of high-frequency queries must have partial indexes where appropriate (`WHERE deleted_at IS NULL`).
- Geometry columns always use a **GiST** index.
- Full-text search columns use a **GIN** index with `tsvector`.
- Never index low-cardinality boolean columns alone; combine with a higher-cardinality column.
- Review `EXPLAIN (ANALYZE, BUFFERS)` output for all queries returning more than 100 rows before merging.

### PostGIS Query Patterns

```sql
-- Radius search: properties within 5 km of a point
-- ST_DWithin on geography uses metres; avoids manual haversine
SELECT
  p.id,
  p.address,
  ST_Distance(
    p.location::geography,
    ST_MakePoint(lng, lat)::geography
  ) AS distance_m
FROM properties p
WHERE ST_DWithin(
  p.location::geography,
  ST_MakePoint(:lng, :lat)::geography,
  5000              -- radius in metres
)
  AND p.status = 'LISTED'
  AND p.deleted_at IS NULL
ORDER BY distance_m
LIMIT 50;

-- Bounding box search (faster for viewport queries)
SELECT p.*
FROM properties p
WHERE p.location && ST_MakeEnvelope(:minLng, :minLat, :maxLng, :maxLat, 4326)
  AND p.status = 'LISTED';

-- Update a property location from geocoded coordinates
UPDATE properties
SET location = ST_SetSRID(ST_MakePoint(:lng, :lat), 4326),
    updated_at = NOW()
WHERE id = :id;
```

### Connection Pooling

```typescript
// packages/shared/src/db/pool.ts
import { Pool } from 'pg';

export function createPool(config: PoolConfig): Pool {
  return new Pool({
    connectionString: config.databaseUrl,
    max: 20,               // max connections per service instance
    idleTimeoutMillis: 30_000,
    connectionTimeoutMillis: 5_000,
    statement_timeout: 30_000,
    query_timeout: 30_000,
  });
}
```

In Kubernetes, each pod runs its own pool. The total connection count is `replicas × max`. Tune `max` so that `replicas × max ≤ PostgreSQL max_connections × 0.8`.

---

## Elasticsearch Guidelines

### Property Index Mapping

```json
{
  "mappings": {
    "properties": {
      "id":            { "type": "keyword" },
      "title":         { "type": "text", "analyzer": "english" },
      "description":   { "type": "text", "analyzer": "english" },
      "address": {
        "type": "object",
        "properties": {
          "street":  { "type": "text" },
          "city":    { "type": "keyword" },
          "state":   { "type": "keyword" },
          "zip":     { "type": "keyword" },
          "country": { "type": "keyword" }
        }
      },
      "location":      { "type": "geo_point" },
      "propertyType":  { "type": "keyword" },
      "status":        { "type": "keyword" },
      "bedrooms":      { "type": "integer" },
      "bathrooms":     { "type": "float" },
      "squareFeet":    { "type": "integer" },
      "rentAmount":    { "type": "scaled_float", "scaling_factor": 100 },
      "amenities":     { "type": "keyword" },
      "availableFrom": { "type": "date" },
      "ownerId":       { "type": "keyword" },
      "createdAt":     { "type": "date" },
      "updatedAt":     { "type": "date" }
    }
  },
  "settings": {
    "number_of_shards":   2,
    "number_of_replicas": 1,
    "refresh_interval":   "5s"
  }
}
```

### Search Query Patterns

```typescript
// packages/search-service/src/queries/property-search.query.ts
export function buildPropertySearchQuery(params: SearchParams): SearchRequest {
  return {
    index: PROPERTY_INDEX,
    body: {
      query: {
        bool: {
          must: params.q
            ? [{
                multi_match: {
                  query: params.q,
                  fields: ['title^3', 'description', 'address.city^2', 'amenities'],
                  type: 'best_fields',
                  fuzziness: 'AUTO',
                },
              }]
            : [{ match_all: {} }],
          filter: [
            { term: { status: 'LISTED' } },
            ...(params.propertyType ? [{ term: { propertyType: params.propertyType } }] : []),
            ...(params.minBeds ? [{ range: { bedrooms: { gte: params.minBeds } } }] : []),
            ...(params.maxRent ? [{ range: { rentAmount: { lte: params.maxRent } } }] : []),
            ...(params.center
              ? [{
                  geo_distance: {
                    distance: `${params.radiusKm ?? 10}km`,
                    location: { lat: params.center.lat, lon: params.center.lng },
                  },
                }]
              : []),
          ],
        },
      },
      sort: [
        ...(params.center
          ? [{
              _geo_distance: {
                location: { lat: params.center.lat, lon: params.center.lng },
                order: 'asc',
                unit: 'km',
              },
            }]
          : [{ createdAt: { order: 'desc' } }]),
      ],
      aggregations: {
        propertyTypes: { terms: { field: 'propertyType', size: 10 } },
        cities:        { terms: { field: 'address.city', size: 20 } },
        rentRanges:    {
          range: {
            field: 'rentAmount',
            ranges: [
              { to: 1500 },
              { from: 1500, to: 2500 },
              { from: 2500, to: 4000 },
              { from: 4000 },
            ],
          },
        },
      },
      from: (params.page - 1) * params.size,
      size: params.size,
    },
  };
}
```

### Index Lifecycle Management

Define an ILM policy that rolls the index over at 50 GB and deletes data older than 365 days via Kibana or the ILM API. Property data is mutable so use alias-based rollover pointing to a write alias `properties-write` and a read alias `properties`.

### PostgreSQL → Elasticsearch Sync Strategy

1. **Event-driven (primary)**: After every write, publish a domain event to the `rems:property:events` Redis stream. The sync worker consumes the stream and upserts the Elasticsearch document.
2. **Full reindex (recovery)**: A cron job at 02:00 UTC scans PostgreSQL for records with `updated_at > last_sync_checkpoint` and re-indexes them using the bulk API.

---

## Redis Guidelines

### Key Naming Convention

```
rems:{service}:{entity}:{id}:{field}

Examples:
  rems:property:unit:unit-uuid:availability     → unit availability bitmap
  rems:lease:lease:lease-uuid:status            → cached lease status
  rems:tenant:application:app-uuid:result       → background-check result
  rems:payment:invoice:invoice-uuid:pdf         → pre-signed S3 URL cache
  rems:search:query:sha256(params):results      → search result cache
```

### TTL Strategy

| Entity | TTL | Reason |
|---|---|---|
| Unit availability | 5 minutes | Changes with bookings; stale data is low-risk |
| Lease status | 10 minutes | Changes infrequently |
| Search query results | 2 minutes | Freshness matters for listings |
| Geocoding results | 7 days | Addresses do not change |
| Pre-signed S3 URLs | 1 hour | Matches S3 URL expiry |
| Background-check result | 24 hours | Regulatory compliance window |
| Session tokens | 15 minutes (sliding) | Security |

### Availability Cache Pattern

```typescript
// packages/property-service/src/infrastructure/cache/availability.cache.ts
@injectable()
export class AvailabilityCache {
  private static readonly TTL = 300; // seconds

  constructor(@inject(TOKENS.Redis) private readonly redis: Redis) {}

  async getUnitAvailability(unitId: UnitId): Promise<boolean | null> {
    const raw = await this.redis.get(`rems:property:unit:${unitId}:available`);
    if (raw === null) return null;
    return raw === '1';
  }

  async setUnitAvailability(unitId: UnitId, available: boolean): Promise<void> {
    await this.redis.set(
      `rems:property:unit:${unitId}:available`,
      available ? '1' : '0',
      'EX',
      AvailabilityCache.TTL,
    );
  }

  async invalidate(unitId: UnitId): Promise<void> {
    await this.redis.del(`rems:property:unit:${unitId}:available`);
  }
}
```

### Distributed Lock for Availability Updates

```typescript
// packages/shared/src/cache/distributed-lock.ts
export class DistributedLock {
  constructor(
    private readonly redis: Redis,
    private readonly lockKey: string,
    private readonly ttlMs: number,
  ) {}

  async acquire(): Promise<string | null> {
    const token = randomUUID();
    const result = await this.redis.set(
      `lock:${this.lockKey}`,
      token,
      'PX', this.ttlMs,
      'NX',
    );
    return result === 'OK' ? token : null;
  }

  async release(token: string): Promise<void> {
    // Lua script for atomic check-and-delete
    const script = `
      if redis.call("GET", KEYS[1]) == ARGV[1] then
        return redis.call("DEL", KEYS[1])
      else
        return 0
      end
    `;
    await this.redis.eval(script, 1, `lock:${this.lockKey}`, token);
  }
}

// Usage in UnitService
const lock = new DistributedLock(redis, `unit:${unitId}:availability`, 5_000);
const token = await lock.acquire();
if (!token) throw new ConflictError('Availability update in progress');
try {
  await updateAvailability(unitId);
} finally {
  await lock.release(token);
}
```

---

## Testing Strategy

### Unit Tests (Jest)

Every service has a co-located `__tests__/` directory. Repository dependencies are mocked using `jest.fn()` wrapped in factory functions.

```typescript
// packages/lease-service/src/__tests__/lease.service.spec.ts
import { LeaseService } from '../application/services/lease.service';
import type { LeaseRepository } from '../domain/repositories/lease.repository';
import type { EventPublisher } from '@rems/shared';
import { makeLeaseEntity } from './factories/lease.factory';

function makeLeaseRepository(): jest.Mocked<LeaseRepository> {
  return {
    findById:     jest.fn(),
    save:         jest.fn(),
    findByUnit:   jest.fn(),
    findByTenant: jest.fn(),
    findExpiring: jest.fn(),
  };
}

function makeEventPublisher(): jest.Mocked<EventPublisher> {
  return { publish: jest.fn() };
}

describe('LeaseService', () => {
  let svc: LeaseService;
  let repo: jest.Mocked<LeaseRepository>;
  let publisher: jest.Mocked<EventPublisher>;

  beforeEach(() => {
    repo      = makeLeaseRepository();
    publisher = makeEventPublisher();
    svc       = new LeaseService(repo, publisher);
  });

  describe('terminateLease', () => {
    it('publishes a lease.terminated event', async () => {
      const lease = makeLeaseEntity({ status: 'ACTIVE' });
      repo.findById.mockResolvedValue(lease);
      repo.save.mockResolvedValue();
      publisher.publish.mockResolvedValue();

      await svc.terminateLease({ leaseId: lease.id, reason: 'Tenant request' });

      expect(publisher.publish).toHaveBeenCalledWith(
        'rems:lease:events',
        expect.objectContaining({ type: 'lease.terminated' }),
      );
    });

    it('throws NotFoundError when lease does not exist', async () => {
      repo.findById.mockResolvedValue(null);
      await expect(
        svc.terminateLease({ leaseId: 'non-existent' as LeaseId, reason: '' }),
      ).rejects.toBeInstanceOf(NotFoundError);
    });
  });
});
```

### Integration Tests (Testcontainers)

Integration tests spin up real PostgreSQL and Redis containers using `testcontainers-node`.

```typescript
// packages/property-service/src/__tests__/integration/property.repository.integration.spec.ts
import { PostgreSqlContainer } from '@testcontainers/postgresql';
import { PostgresPropertyRepository } from '../../infrastructure/db/postgres-property.repository';
import { runMigrations } from '../../db/migrate';

let container: StartedPostgreSqlContainer;
let repo: PostgresPropertyRepository;

beforeAll(async () => {
  container = await new PostgreSqlContainer('postgis/postgis:15-3.4')
    .withDatabase('rems_test')
    .start();
  const pool = createPool({ databaseUrl: container.getConnectionUri() });
  await runMigrations(container.getConnectionUri());
  repo = new PostgresPropertyRepository(pool);
}, 60_000);

afterAll(async () => {
  await container.stop();
});

test('saves and retrieves a property', async () => {
  const property = makePropertyEntity();
  await repo.save(property);
  const found = await repo.findById(property.id);
  expect(found).toMatchObject({ id: property.id, status: 'DRAFT' });
});
```

### E2E Tests (Supertest)

```typescript
// packages/property-service/src/__tests__/e2e/property.api.e2e.spec.ts
import request from 'supertest';
import { buildApp } from '../../app';

describe('POST /v1/properties', () => {
  it('creates a property and returns 201', async () => {
    const app = await buildApp();
    const res = await request(app)
      .post('/v1/properties')
      .set('Authorization', `Bearer ${TEST_JWT}`)
      .send({
        address: { street: '123 Main St', city: 'Austin', state: 'TX', zip: '78701' },
        propertyType: 'APARTMENT',
        location: { lat: 30.2672, lng: -97.7431 },
      });

    expect(res.status).toBe(201);
    expect(res.body.data.id).toBeDefined();
  });
});
```

### Coverage Thresholds

```json
// jest.config.ts
coverageThreshold: {
  global: {
    branches:   80,
    functions:  80,
    lines:      80,
    statements: 80,
  },
  './packages/lease-service/src/application/': {
    branches:   90,
    functions:  90,
    lines:      90,
    statements: 90,
  },
},
```

---

## Property-Specific Considerations

### Geospatial Queries: PostGIS vs Elasticsearch Geo

| Use Case | Use |
|---|---|
| Authoritative storage of coordinates | PostGIS (`geometry(Point,4326)`) |
| Viewport/bounding box listing queries | PostGIS (`&&` operator with `ST_MakeEnvelope`) |
| Radius search with full-text filter | Elasticsearch `geo_distance` filter |
| Isochrone / drive-time polygons | PostGIS with `pgRouting` |
| Property cluster aggregation for map | Elasticsearch `geotile_grid` aggregation |

For radius search, prefer Elasticsearch when the result also requires text scoring. Use PostGIS for pure radius queries with no text component to avoid ES round-trip cost.

### Image Optimization Pipeline

```typescript
// packages/property-service/src/infrastructure/storage/image-pipeline.ts
import sharp from 'sharp';

const SIZES = [
  { suffix: 'thumb',  width: 300,  height: 200 },
  { suffix: 'medium', width: 800,  height: 533 },
  { suffix: 'large',  width: 1600, height: 1067 },
] as const;

export async function processPropertyImage(
  buffer: Buffer,
  propertyId: PropertyId,
  imageId: string,
): Promise<ProcessedImage[]> {
  const results: ProcessedImage[] = [];

  for (const size of SIZES) {
    const webp = await sharp(buffer)
      .resize(size.width, size.height, { fit: 'cover', position: 'attention' })
      .webp({ quality: 82, effort: 4 })
      .toBuffer();

    const key = `properties/${propertyId}/images/${imageId}/${size.suffix}.webp`;
    await s3Client.send(new PutObjectCommand({
      Bucket: process.env.ASSETS_BUCKET,
      Key: key,
      Body: webp,
      ContentType: 'image/webp',
      CacheControl: 'public, max-age=31536000, immutable',
    }));

    results.push({ size: size.suffix, key, bytes: webp.byteLength });
  }

  return results;
}
```

### Document Handling

Lease PDFs are generated via Handlebars + Puppeteer and stored in S3. Pre-signed URLs are issued with a 1-hour TTL and cached in Redis.

```typescript
// packages/lease-service/src/infrastructure/documents/lease-pdf.generator.ts
export async function generateLeasePdf(lease: LeaseEntity): Promise<Buffer> {
  const template = await fs.readFile('templates/lease.hbs', 'utf8');
  const html = Handlebars.compile(template)(mapLeaseToTemplateData(lease));

  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setContent(html, { waitUntil: 'networkidle0' });
  const pdf = await page.pdf({ format: 'Letter', printBackground: true });
  await browser.close();

  return Buffer.from(pdf);
}
```

---

## Security

### Input Validation (Zod)

Zod schemas are defined in `packages/shared/src/validation/` and reused by both HTTP controllers and service commands.

```typescript
export const CreatePropertySchema = z.object({
  address: z.object({
    street:  z.string().min(5).max(200),
    city:    z.string().min(2).max(100),
    state:   z.string().length(2).toUpperCase(),
    zip:     z.string().regex(/^\d{5}(-\d{4})?$/),
    country: z.string().length(2).default('US'),
  }),
  propertyType: z.enum(['APARTMENT', 'HOUSE', 'CONDO', 'TOWNHOUSE', 'COMMERCIAL']),
  location: z.object({
    lat: z.number().min(-90).max(90),
    lng: z.number().min(-180).max(180),
  }),
});
```

### SQL Injection Prevention

- **Always use parameterized queries** (`$1`, `$2`, ...). String interpolation into SQL is forbidden and enforced by the `no-sql-string-template` custom ESLint rule.
- Raw `pg.query(string)` without parameters is only allowed for DDL in migration files.

### PII Data Handling

Tenant SSN and DOB are encrypted at rest using AES-256-GCM with a DEK (data encryption key) stored in AWS KMS.

```typescript
// packages/shared/src/crypto/field-encryption.ts
export async function encryptField(plaintext: string): Promise<string> {
  const iv = randomBytes(16);
  const cipher = createCipheriv('aes-256-gcm', await getDek(), iv);
  const ciphertext = Buffer.concat([cipher.update(plaintext, 'utf8'), cipher.final()]);
  const tag = cipher.getAuthTag();
  return Buffer.concat([iv, tag, ciphertext]).toString('base64');
}
```

Database columns for SSN and DOB are typed `text` and stored as the base64-encoded ciphertext. Decryption only occurs in the service layer, never in the repository mapper.

### Rate Limiting

```typescript
// packages/shared/src/middleware/rate-limit.ts
const LIMITS: Record<string, { max: number; window: string }> = {
  '/v1/properties':           { max: 60,  window: '1m'  },
  '/v1/search':               { max: 120, window: '1m'  },
  '/v1/applications':         { max: 20,  window: '1m'  },
  '/v1/auth/login':           { max: 10,  window: '15m' },
  '/v1/auth/forgot-password': { max: 5,   window: '15m' },
};
```

Rate limit state is stored in Redis using a sliding window algorithm.

---

## Error Handling

### Custom Error Hierarchy

```typescript
// packages/shared/src/errors/app-error.ts
export abstract class AppError extends Error {
  abstract readonly statusCode: number;
  abstract readonly code: string;

  constructor(
    message: string,
    public readonly details?: unknown,
    public readonly cause?: Error,
  ) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace(this, this.constructor);
  }
}

export class ValidationError  extends AppError { statusCode = 400; code = 'VALIDATION_ERROR'; }
export class UnauthorizedError extends AppError { statusCode = 401; code = 'UNAUTHORIZED'; }
export class ForbiddenError    extends AppError { statusCode = 403; code = 'FORBIDDEN'; }
export class NotFoundError     extends AppError { statusCode = 404; code = 'NOT_FOUND'; }
export class ConflictError     extends AppError { statusCode = 409; code = 'CONFLICT'; }
export class UnprocessableError extends AppError { statusCode = 422; code = 'UNPROCESSABLE'; }
export class InternalError     extends AppError { statusCode = 500; code = 'INTERNAL_ERROR'; }
```

### Global Error Handler (Fastify)

```typescript
// packages/shared/src/http/error-handler.ts
export function registerErrorHandler(app: FastifyInstance): void {
  app.setErrorHandler((error, request, reply) => {
    const log = request.log;

    if (error instanceof AppError) {
      log.warn({ err: error, code: error.code }, error.message);
      return reply.status(error.statusCode).send({
        error: { code: error.code, message: error.message, details: error.details },
      });
    }

    if (error instanceof ZodError) {
      log.warn({ err: error }, 'Validation failed');
      return reply.status(400).send({
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Request validation failed',
          details: error.flatten(),
        },
      });
    }

    log.error({ err: error }, 'Unhandled error');
    return reply.status(500).send({
      error: { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred' },
    });
  });
}
```

### Structured Logging (pino)

```typescript
// packages/shared/src/logging/logger.ts
import pino from 'pino';

export const logger = pino({
  level: process.env.LOG_LEVEL ?? 'info',
  redact: ['req.headers.authorization', 'req.body.ssn', 'req.body.password'],
  serializers: pino.stdSerializers,
  formatters: {
    level: (label) => ({ level: label }),
  },
  base: {
    service: process.env.SERVICE_NAME,
    env:     process.env.NODE_ENV,
  },
});
```

Log every inbound HTTP request (method, path, status, latency) and every outbound database/Redis call duration at `debug` level. Log business-critical events (lease created, payment received) at `info` level with a `correlationId` field.
