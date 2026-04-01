# Code Guidelines — Fleet Management System

## 1. Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Runtime | Node.js | 20 LTS | Backend services runtime |
| Language | TypeScript | 5.x strict | All backend + frontend code |
| Backend Framework | NestJS | 10 | Microservices, REST, MQTT consumers |
| Frontend Framework | React | 18 | Fleet dashboard web app |
| Mobile Framework | React Native | 0.74 (Expo SDK 51) | Driver mobile app |
| ORM | Prisma | 5 | PostgreSQL schema management and queries |
| Message Bus Client | kafkajs | 2.x | Kafka producers and consumers |
| MQTT Client | MQTT.js | 5.x | IoT device telemetry ingestion |
| Time-Series Toolkit | timescaledb-toolkit | latest | Hyperfunctions for GPS ping analytics |
| Unit Testing | Jest | 29 | Unit and integration tests |
| API Testing | Supertest | 7.x | HTTP endpoint integration tests |
| E2E Testing | Cypress | 13 | Frontend end-to-end tests |
| Load Testing | k6 | latest | Telemetry ingestion load tests |
| Monorepo Tooling | NX | 19 | Task orchestration, caching, affected builds |
| Containerisation | Docker multi-stage | 24.x | Service images, dev compose |
| Infrastructure as Code | Terraform | 1.8 | AWS resource provisioning |
| Relational Database | PostgreSQL + PostGIS | 16 | Primary database, geospatial queries |
| Time-Series Database | TimescaleDB | 2.x | GPS ping hypertable |
| Cache / Pub-Sub | Redis | 7 (ElastiCache) | Live positions, BreachStateTracker, rate limit |
| Streaming | Apache Kafka | 3.x (MSK) | Event bus between all services |
| IoT Broker | AWS IoT Core | — | MQTT device connections, routing rules |
| Container Orchestration | AWS ECS Fargate | — | Stateless service deployment |

---

## 2. Monorepo Structure

The repository follows an NX monorepo layout. All application and library code lives in a single Git repository.

```
/
├── apps/
│   ├── web/                     # React 18 fleet dashboard (Vite + TailwindCSS)
│   ├── mobile/                  # React Native driver app (Expo SDK 51)
│   ├── api-gateway/             # NestJS API gateway (single entry point for web/mobile)
│   └── eld-simulator/           # Dev-only ELD/GPS device simulator (MQTT publisher)
├── services/
│   ├── telemetry-service/       # MQTT ingestion, GPS processing, TimescaleDB writes
│   ├── vehicle-service/         # Vehicle CRUD, status management, odometer tracking
│   ├── driver-service/          # Driver profiles, HOS tracking, scoring engine
│   ├── trip-service/            # Trip lifecycle, distance calc, ignition event handling
│   ├── geofence-service/        # Geofence CRUD, breach detection (PostGIS)
│   ├── maintenance-service/     # Work orders, preventive schedules, predictive ML triggers
│   ├── fuel-service/            # Fuel records, WEX card integration, MPG calculations
│   ├── dvir-service/            # Digital inspection reports, e-signature, defect tracking
│   ├── compliance-service/      # HOS violation logs, IFTA reports, DOT document store
│   ├── route-service/           # Route planning, HERE Maps integration, dispatch
│   ├── alert-service/           # Rule engine, real-time alert evaluation
│   ├── analytics-service/       # KPIs, driver leaderboard, utilisation reports
│   ├── notification-service/    # Email (SendGrid), SMS (Twilio), push (FCM/APNs)
│   └── auth-service/            # JWT RS256, OAuth2 PKCE, RBAC, API key management
├── libs/
│   ├── shared/
│   │   ├── dto/                 # Shared DTOs validated with class-validator
│   │   ├── events/              # Kafka event contracts (Avro schema + TS types)
│   │   ├── geo/                 # PostGIS helper utilities (bbox, point, polygon)
│   │   ├── utils/               # Pagination, crypto, date/timezone helpers
│   │   └── errors/              # AppError hierarchy (DomainError, InfraError, etc.)
│   └── testing/
│       ├── fixtures/            # faker-js test data factories per domain entity
│       └── helpers/             # DB reset, MQTT mock broker, Kafka test consumer
├── infrastructure/
│   ├── terraform/               # All Terraform modules (vpc, ecs, rds, iot, msk, elasticache)
│   └── docker/                  # Per-service Dockerfiles (multi-stage)
├── .github/
│   ├── workflows/               # CI/CD GitHub Actions pipelines
│   └── PULL_REQUEST_TEMPLATE.md
├── nx.json
├── package.json                 # Root workspace package.json (pnpm workspaces)
└── tsconfig.base.json           # Base TS config with path aliases
```

### NX Conventions

- Every app and service has a `project.json` defining its `build`, `test`, `lint`, and `serve` targets.
- Use `nx affected --target=test` in CI to only test changed packages.
- Use `nx run-many --target=build --all` for full builds.
- Cache all deterministic targets (`build`, `lint`, `test`) via NX Cloud.

---

## 3. TypeScript Standards

### 3.1 Compiler Configuration

All services extend `tsconfig.base.json` at the repo root:

```jsonc
// tsconfig.base.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "exactOptionalPropertyTypes": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true,
    "esModuleInterop": true,
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true,
    "baseUrl": ".",
    "paths": {
      "@fms/shared/dto":      ["libs/shared/dto/src/index.ts"],
      "@fms/shared/events":   ["libs/shared/events/src/index.ts"],
      "@fms/shared/geo":      ["libs/shared/geo/src/index.ts"],
      "@fms/shared/utils":    ["libs/shared/utils/src/index.ts"],
      "@fms/shared/errors":   ["libs/shared/errors/src/index.ts"],
      "@fms/testing/*":       ["libs/testing/*/src/index.ts"]
    }
  }
}
```

### 3.2 Coding Rules

| Rule | Guidance |
|---|---|
| No `any` | Use `unknown` and narrow with type guards or Zod schemas |
| No type assertions (`as`) | Prefer type guards; if unavoidable, add a comment explaining why |
| Readonly arrays | Use `readonly T[]` or `ReadonlyArray<T>` for arrays not modified after creation |
| Barrel exports | Every `libs/` package exposes a single `src/index.ts` barrel |
| Zod for runtime validation | All external inputs (HTTP body, Kafka events, MQTT payloads) validated with Zod |
| Enums | Prefer `const enum` for compile-time erasure; use string literal unions for public APIs |
| Async/Await | No raw `.then()` chains — always use `async/await` |
| Error handling | Always wrap `await` calls in try/catch in controllers; propagate typed errors |

### 3.3 Zod Validation Example

```typescript
// libs/shared/dto/src/gps-ping.schema.ts
import { z } from 'zod';

export const GpsPingSchema = z.object({
  deviceId:   z.string().uuid(),
  vehicleId:  z.string().uuid(),
  lat:        z.number().min(-90).max(90),
  lng:        z.number().min(-180).max(180),
  speed:      z.number().min(0).max(300),   // km/h — physical max
  heading:    z.number().min(0).max(359),
  altitude:   z.number().optional(),
  accuracy:   z.number().min(0).optional(),
  timestamp:  z.string().datetime(),
  odometer:   z.number().min(0).optional(),
  ignition:   z.boolean(),
});

export type GpsPing = z.infer<typeof GpsPingSchema>;
```

---

## 4. NestJS Service Pattern

Every microservice follows the same four-layer architecture: **Module → Controller → Service → Repository**.

### 4.1 Module

```typescript
// services/vehicle-service/src/vehicle/vehicle.module.ts
import { Module } from '@nestjs/common';
import { VehicleController } from './vehicle.controller';
import { VehicleService }    from './vehicle.service';
import { VehicleRepository } from './vehicle.repository';
import { PrismaModule }      from '../prisma/prisma.module';
import { KafkaModule }       from '../kafka/kafka.module';

@Module({
  imports:   [PrismaModule, KafkaModule],
  controllers: [VehicleController],
  providers:   [VehicleService, VehicleRepository],
  exports:     [VehicleService],
})
export class VehicleModule {}
```

### 4.2 Controller

```typescript
// services/vehicle-service/src/vehicle/vehicle.controller.ts
import { Controller, Get, Post, Body, Param, ParseUUIDPipe, HttpCode, HttpStatus } from '@nestjs/common';
import { VehicleService }   from './vehicle.service';
import { CreateVehicleDto } from '@fms/shared/dto';
import { Roles }            from '../auth/roles.decorator';

@Controller('vehicles')
export class VehicleController {
  constructor(private readonly vehicleService: VehicleService) {}

  @Get(':id')
  @Roles('FLEET_MANAGER', 'DISPATCHER', 'ADMIN')
  async getById(@Param('id', ParseUUIDPipe) id: string) {
    return this.vehicleService.findById(id);
  }

  @Post()
  @Roles('FLEET_MANAGER', 'ADMIN')
  @HttpCode(HttpStatus.CREATED)
  async create(@Body() dto: CreateVehicleDto) {
    return this.vehicleService.create(dto);
  }
}
```

### 4.3 Service

```typescript
// services/vehicle-service/src/vehicle/vehicle.service.ts
import { Injectable, NotFoundException } from '@nestjs/common';
import { VehicleRepository }             from './vehicle.repository';
import { KafkaProducerService }          from '../kafka/kafka-producer.service';
import { CreateVehicleDto, VehicleDto }  from '@fms/shared/dto';
import { VehicleCreatedEvent }           from '@fms/shared/events';

@Injectable()
export class VehicleService {
  constructor(
    private readonly vehicleRepo: VehicleRepository,
    private readonly kafka: KafkaProducerService,
  ) {}

  async findById(id: string): Promise<VehicleDto> {
    const vehicle = await this.vehicleRepo.findById(id);
    if (!vehicle) throw new NotFoundException(`Vehicle ${id} not found`);
    return vehicle;
  }

  async create(dto: CreateVehicleDto): Promise<VehicleDto> {
    const vehicle = await this.vehicleRepo.create(dto);
    await this.kafka.emit<VehicleCreatedEvent>('vehicle.created', {
      vehicleId: vehicle.id,
      vin:       vehicle.vin,
      tenantId:  vehicle.tenantId,
    });
    return vehicle;
  }
}
```

### 4.4 Repository

```typescript
// services/vehicle-service/src/vehicle/vehicle.repository.ts
import { Injectable } from '@nestjs/common';
import { PrismaService }    from '../prisma/prisma.service';
import { CreateVehicleDto, VehicleDto } from '@fms/shared/dto';

@Injectable()
export class VehicleRepository {
  constructor(private readonly prisma: PrismaService) {}

  async findById(id: string): Promise<VehicleDto | null> {
    return this.prisma.vehicle.findUnique({
      where:  { id, deletedAt: null },
      select: vehicleSelectFields,
    });
  }

  async create(dto: CreateVehicleDto): Promise<VehicleDto> {
    return this.prisma.vehicle.create({ data: dto });
  }
}

const vehicleSelectFields = {
  id: true, vin: true, licensePlate: true, make: true, model: true,
  year: true, status: true, tenantId: true, createdAt: true,
} as const;
```

### 4.5 Kafka Consumer Pattern

```typescript
// services/geofence-service/src/consumers/telemetry.consumer.ts
import { Controller } from '@nestjs/common';
import { EventPattern, Payload, Ctx, KafkaContext } from '@nestjs/microservices';
import { GeofenceBreachEvaluator } from '../geofence/breach-evaluator.service';
import { GpsPingSchema }           from '@fms/shared/dto';

@Controller()
export class TelemetryConsumer {
  constructor(private readonly evaluator: GeofenceBreachEvaluator) {}

  @EventPattern('telemetry.position.updated')
  async handlePositionUpdate(
    @Payload() rawPayload: unknown,
    @Ctx()    ctx: KafkaContext,
  ): Promise<void> {
    const ping = GpsPingSchema.parse(rawPayload);
    await this.evaluator.evaluate(ping);
    ctx.getMessage().offset; // commit handled by NestJS Kafka consumer
  }
}
```

---

## 5. Telemetry Service Specifics

The `telemetry-service` is the highest-throughput component, targeting **10,000 GPS pings/second** at peak.

### 5.1 MQTT Subscription Pattern

Devices publish to AWS IoT Core using the topic pattern:
```
fleet/{tenantId}/vehicles/{vehicleId}/telemetry
```

The Telemetry Service subscribes via AWS IoT Core Rules, which forward to the `telemetry.raw` Kafka topic. Alternatively, for local dev, MQTT.js connects directly to the ELD Simulator broker:

```typescript
// services/telemetry-service/src/mqtt/mqtt-ingestion.service.ts
import * as mqtt from 'mqtt';
import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { TelemetryBatchBuffer } from './batch-buffer.service';

@Injectable()
export class MqttIngestionService implements OnModuleInit, OnModuleDestroy {
  private client!: mqtt.MqttClient;

  constructor(private readonly buffer: TelemetryBatchBuffer) {}

  onModuleInit(): void {
    this.client = mqtt.connect(process.env.MQTT_BROKER_URL!, {
      clientId: `telemetry-service-${process.pid}`,
      clean:    false, // persistent session for QoS 1
      qos:      1,
    });
    this.client.subscribe('fleet/+/vehicles/+/telemetry', { qos: 1 });
    this.client.on('message', (_topic, payload) => {
      this.buffer.add(payload.toString());
    });
  }

  onModuleDestroy(): void {
    this.client.end();
  }
}
```

### 5.2 Batch TimescaleDB Write Strategy

To avoid per-message INSERT overhead, the Telemetry Service batches pings and flushes every **5 seconds** or when the buffer reaches **100 items** (whichever comes first):

```typescript
// services/telemetry-service/src/mqtt/batch-buffer.service.ts
import { Injectable, OnModuleInit } from '@nestjs/common';
import { PrismaService }            from '../prisma/prisma.service';
import { GpsPingSchema, GpsPing }   from '@fms/shared/dto';

const BATCH_SIZE  = 100;
const FLUSH_MS    = 5_000;

@Injectable()
export class TelemetryBatchBuffer implements OnModuleInit {
  private buffer: GpsPing[] = [];
  private timer?: NodeJS.Timeout;

  constructor(private readonly prisma: PrismaService) {}

  onModuleInit(): void {
    this.timer = setInterval(() => this.flush(), FLUSH_MS);
  }

  add(raw: string): void {
    const ping = GpsPingSchema.parse(JSON.parse(raw));
    this.buffer.push(ping);
    if (this.buffer.length >= BATCH_SIZE) void this.flush();
  }

  private async flush(): Promise<void> {
    if (this.buffer.length === 0) return;
    const batch = this.buffer.splice(0, this.buffer.length);
    await this.prisma.$executeRaw`
      INSERT INTO gps_pings (vehicle_id, tenant_id, lat, lng, speed, heading,
                             altitude, accuracy, odometer, ignition, recorded_at)
      SELECT * FROM UNNEST(
        ${batch.map(p => p.vehicleId)}::uuid[],
        ${batch.map(p => p.tenantId)}::uuid[],
        ${batch.map(p => p.lat)}::double precision[],
        ${batch.map(p => p.lng)}::double precision[],
        ${batch.map(p => p.speed)}::real[],
        ${batch.map(p => p.heading)}::smallint[],
        ${batch.map(p => p.altitude)}::real[],
        ${batch.map(p => p.accuracy)}::real[],
        ${batch.map(p => p.odometer)}::bigint[],
        ${batch.map(p => p.ignition)}::boolean[],
        ${batch.map(p => p.timestamp)}::timestamptz[]
      )
      ON CONFLICT DO NOTHING
    `;
  }
}
```

### 5.3 Redis Live Position Update

After batching to TimescaleDB, each ping also updates the live position hash in Redis for instant map queries (no time-series scan needed):

```typescript
// services/telemetry-service/src/redis/live-position.service.ts
import { Injectable } from '@nestjs/common';
import { InjectRedis } from '@nestjs-modules/ioredis';
import Redis          from 'ioredis';
import { GpsPing }    from '@fms/shared/dto';

const LIVE_TTL_SECONDS = 300; // expire after 5 min of no updates

@Injectable()
export class LivePositionService {
  constructor(@InjectRedis() private readonly redis: Redis) {}

  async update(ping: GpsPing): Promise<void> {
    const key = `live:vehicle:${ping.vehicleId}`;
    await this.redis
      .pipeline()
      .hset(key, {
        lat:         ping.lat,
        lng:         ping.lng,
        speed:       ping.speed,
        heading:     ping.heading,
        ignition:    ping.ignition ? '1' : '0',
        recordedAt:  ping.timestamp,
      })
      .expire(key, LIVE_TTL_SECONDS)
      .exec();
  }

  async get(vehicleId: string): Promise<Record<string, string> | null> {
    const data = await this.redis.hgetall(`live:vehicle:${vehicleId}`);
    return Object.keys(data).length > 0 ? data : null;
  }
}
```

---

## 6. Database Conventions

### 6.1 Naming

| Convention | Rule |
|---|---|
| Table names | `snake_case`, plural (e.g., `vehicles`, `gps_pings`, `work_orders`) |
| Column names | `snake_case` (e.g., `vehicle_id`, `created_at`, `deleted_at`) |
| Primary keys | `UUID v4`, column named `id` |
| Foreign keys | `{referenced_table_singular}_id` (e.g., `vehicle_id`, `driver_id`) |
| Indexes | `idx_{table}_{column(s)}` (e.g., `idx_gps_pings_vehicle_id_recorded_at`) |
| Enum types | `UPPER_SNAKE_CASE` PostgreSQL enum (e.g., `VEHICLE_STATUS`) |

### 6.2 Required Columns on Every Table

```sql
id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
tenant_id   UUID        NOT NULL REFERENCES tenants(id),
created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
deleted_at  TIMESTAMPTZ NULL          -- soft-delete sentinel; NULL = active
```

A trigger maintains `updated_at` automatically:

```sql
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 6.3 PostGIS Geospatial Columns

Geofence polygons and vehicle positions use PostGIS geometry types:

```sql
-- Geofences table
CREATE TABLE geofences (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID NOT NULL,
  name        TEXT NOT NULL,
  type        TEXT NOT NULL CHECK (type IN ('CIRCLE','POLYGON','CORRIDOR')),
  boundary    GEOMETRY(Geometry, 4326) NOT NULL,  -- WGS84
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at  TIMESTAMPTZ
);

CREATE INDEX idx_geofences_boundary ON geofences USING GIST (boundary);
CREATE INDEX idx_geofences_tenant   ON geofences (tenant_id) WHERE deleted_at IS NULL;
```

### 6.4 TimescaleDB Hypertable for GPS Pings

```sql
CREATE TABLE gps_pings (
  vehicle_id   UUID        NOT NULL,
  tenant_id    UUID        NOT NULL,
  lat          DOUBLE PRECISION NOT NULL,
  lng          DOUBLE PRECISION NOT NULL,
  speed        REAL,
  heading      SMALLINT,
  altitude     REAL,
  accuracy     REAL,
  odometer     BIGINT,
  ignition     BOOLEAN NOT NULL DEFAULT FALSE,
  recorded_at  TIMESTAMPTZ NOT NULL
);

-- Convert to hypertable partitioned by time
SELECT create_hypertable('gps_pings', 'recorded_at',
  chunk_time_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

-- Add space partitioning on vehicle_id for parallel writes
SELECT add_dimension('gps_pings', 'vehicle_id', number_partitions => 8);

-- Compression policy: compress chunks older than 7 days
ALTER TABLE gps_pings SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'vehicle_id',
  timescaledb.compress_orderby   = 'recorded_at DESC'
);
SELECT add_compression_policy('gps_pings', INTERVAL '7 days');
```

---

## 7. Testing Standards

### 7.1 Coverage Requirements

| Test Type | Target | Tooling |
|---|---|---|
| Unit tests | ≥ 80% line coverage per service | Jest 29 |
| Integration tests | All public REST endpoints covered | Jest + Supertest |
| Contract tests | All Kafka event schemas validated | Jest + Avro schema registry |
| E2E tests | Critical user flows (login, trip view, DVIR) | Cypress 13 |
| Load tests | Telemetry ingestion: 10,000 pings/sec sustained for 5 min | k6 |

### 7.2 Unit Test Example

```typescript
// services/vehicle-service/src/vehicle/vehicle.service.spec.ts
import { Test, TestingModule }   from '@nestjs/testing';
import { NotFoundException }     from '@nestjs/common';
import { VehicleService }        from './vehicle.service';
import { VehicleRepository }     from './vehicle.repository';
import { KafkaProducerService }  from '../kafka/kafka-producer.service';
import { vehicleFactory }        from '@fms/testing/fixtures';

describe('VehicleService', () => {
  let service: VehicleService;
  let repo: jest.Mocked<VehicleRepository>;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        VehicleService,
        { provide: VehicleRepository,    useValue: { findById: jest.fn(), create: jest.fn() } },
        { provide: KafkaProducerService, useValue: { emit: jest.fn() } },
      ],
    }).compile();

    service = module.get(VehicleService);
    repo    = module.get(VehicleRepository);
  });

  describe('findById', () => {
    it('throws NotFoundException when vehicle does not exist', async () => {
      repo.findById.mockResolvedValue(null);
      await expect(service.findById('non-existent-id')).rejects.toBeInstanceOf(NotFoundException);
    });

    it('returns vehicle DTO when found', async () => {
      const vehicle = vehicleFactory.build();
      repo.findById.mockResolvedValue(vehicle);
      const result = await service.findById(vehicle.id);
      expect(result).toEqual(vehicle);
    });
  });
});
```

### 7.3 k6 Load Test for Telemetry Ingestion

```javascript
// infrastructure/load-tests/telemetry-ingestion.js
import mqtt from 'k6/x/mqtt';  // xk6-mqtt extension
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    telemetry_flood: {
      executor:    'constant-arrival-rate',
      rate:        10_000,      // 10,000 pings/sec
      timeUnit:    '1s',
      duration:    '5m',
      preAllocatedVUs: 500,
    },
  },
  thresholds: {
    mqtt_publish_duration: ['p(99)<500'],  // 99th percentile < 500ms
  },
};

export default function () {
  const payload = JSON.stringify({
    vehicleId: `vehicle-${Math.floor(Math.random() * 1000)}`,
    lat:       37.7749 + (Math.random() - 0.5) * 0.1,
    lng:      -122.4194 + (Math.random() - 0.5) * 0.1,
    speed:     Math.floor(Math.random() * 120),
    heading:   Math.floor(Math.random() * 360),
    ignition:  true,
    timestamp: new Date().toISOString(),
  });
  mqtt.publish(`fleet/tenant-1/vehicles/v-${__VU}/telemetry`, payload, 1);
}
```

---

## 8. Git Workflow

### 8.1 Branch Naming

| Type | Pattern | Example |
|---|---|---|
| Feature | `feat/{ticket-id}/{short-description}` | `feat/FMS-142/geofence-breach-detection` |
| Bug fix | `fix/{ticket-id}/{short-description}` | `fix/FMS-201/hos-clock-drift` |
| Hotfix | `hotfix/{ticket-id}/{short-description}` | `hotfix/FMS-305/telemetry-buffer-overflow` |
| Chore | `chore/{description}` | `chore/upgrade-prisma-5` |
| Release | `release/{version}` | `release/v2.4.0` |

### 8.2 Conventional Commits

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

**Scope examples:** `telemetry`, `geofence`, `hos`, `dvir`, `ifta`, `mobile`

```
feat(geofence): add PostGIS-backed breach detection pipeline

Implements GeofenceBreachEvaluator with Redis state tracking and
Kafka event publishing for ENTRY/EXIT transitions.

Closes FMS-142
```

### 8.3 PR Requirements

Before a PR is merged, all of the following must pass:
- [ ] NX affected lint: `nx affected --target=lint`
- [ ] NX affected test: `nx affected --target=test --coverage`
- [ ] NX affected build: `nx affected --target=build`
- [ ] Minimum 2 peer reviews
- [ ] No unresolved review comments
- [ ] Branch is up-to-date with `main`

### 8.4 Semantic Versioning

- **MAJOR** — breaking API contract changes, database schema migrations requiring manual intervention
- **MINOR** — new features, new Kafka event types
- **PATCH** — bug fixes, performance improvements, non-breaking dependency updates

Use `standard-version` or `semantic-release` for automated changelog generation.

---

## 9. Security Standards

### 9.1 Authentication and Authorisation

```typescript
// JWT RS256 — asymmetric key pair; public key distributed to all services
// Auth Service signs tokens; all other services verify with public key only

// services/auth-service/src/jwt/jwt.strategy.ts
import { Injectable }          from '@nestjs/common';
import { PassportStrategy }    from '@nestjs/passport';
import { ExtractJwt, Strategy } from 'passport-jwt';
import { SecretsService }      from '../secrets/secrets.service';

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  constructor(secrets: SecretsService) {
    super({
      jwtFromRequest:   ExtractJwt.fromAuthHeaderAsBearerToken(),
      algorithms:       ['RS256'],
      secretOrKey:      secrets.getJwtPublicKey(), // fetched from AWS Secrets Manager
      ignoreExpiration: false,
    });
  }
}
```

### 9.2 Secrets Management

- **Never** hardcode secrets in source code or `.env` files committed to Git.
- All secrets (DB passwords, API keys, JWT key pairs) are stored in **AWS Secrets Manager**.
- Services retrieve secrets at startup via the AWS SDK; secrets are cached in-process for 15 minutes.
- Environment variables in ECS task definitions reference `secretsManager` ARNs — not plaintext values.

### 9.3 PII Encryption at Rest

Driver PII fields (full name, SSN last-4, license number) are encrypted at the application layer using AES-256-GCM before storage in PostgreSQL:

```typescript
// libs/shared/utils/src/crypto.util.ts
import { createCipheriv, createDecipheriv, randomBytes } from 'crypto';

const ALGORITHM = 'aes-256-gcm';

export function encryptPii(plaintext: string, key: Buffer): string {
  const iv       = randomBytes(12);
  const cipher   = createCipheriv(ALGORITHM, key, iv);
  const encrypted = Buffer.concat([cipher.update(plaintext, 'utf8'), cipher.final()]);
  const authTag  = cipher.getAuthTag();
  return `${iv.toString('hex')}.${authTag.toString('hex')}.${encrypted.toString('hex')}`;
}

export function decryptPii(ciphertext: string, key: Buffer): string {
  const [ivHex, tagHex, encHex] = ciphertext.split('.');
  const decipher = createDecipheriv(ALGORITHM, key, Buffer.from(ivHex, 'hex'));
  decipher.setAuthTag(Buffer.from(tagHex, 'hex'));
  return decipher.update(Buffer.from(encHex, 'hex')) + decipher.final('utf8');
}
```

### 9.4 MQTT Device Authentication (x.509 Certificates)

Each GPS device is provisioned with a unique x.509 certificate issued by AWS IoT Core's Certificate Authority. The certificate's `CommonName` must equal the `deviceId` registered in the Vehicle Service. The IoT Core policy allows only:

```json
{
  "Effect": "Allow",
  "Action": ["iot:Connect", "iot:Publish"],
  "Resource": "arn:aws:iot:*:*:topic/fleet/*/vehicles/${iot:Certificate.Subject.CommonName}/telemetry"
}
```

This ensures a device can only publish to its own vehicle's telemetry topic.

### 9.5 Input Validation and Rate Limiting

- All HTTP endpoints protected by `ThrottlerGuard` (NestJS) — default 100 req/min per API key.
- All incoming Kafka payloads validated with Zod before processing.
- SQL injection prevented by exclusive use of Prisma parameterised queries (no raw SQL with user input).
- XSS prevention: React renders escape HTML by default; never use `dangerouslySetInnerHTML`.
- CORS: API Gateway allows only whitelisted origins (fleet dashboard domain, mobile app deep links).

---

## 10. Code Review Checklist

Reviewers must verify:

- [ ] No `any` types introduced
- [ ] All new Kafka events have Avro schema in `libs/shared/events/`
- [ ] All new database columns have migrations in the relevant service's `prisma/migrations/`
- [ ] New endpoints have at least one integration test
- [ ] Error paths tested (not just happy path)
- [ ] No secrets, credentials, or PII in log statements
- [ ] Multi-tenant isolation: all repository queries include `tenantId` filter
- [ ] TimescaleDB writes go through the batch buffer — no direct single-row inserts in hot paths
- [ ] Redis keys include `tenantId` prefix to prevent cross-tenant cache reads
