# Hotel Property Management System

A full-stack, cloud-native Property Management System (PMS) built for independent hotels and chains of up to 500 rooms. The platform centralises reservations, front-desk operations, housekeeping, point-of-sale, billing, channel management, loyalty, revenue management, and night audit into a single unified system accessible from any device.

---

## Documentation Structure

Project root artifact: [`traceability-matrix.md`](./traceability-matrix.md) provides cross-phase requirement-to-implementation linkage.


```
Hotel Property Management System/
├── README.md                                  # Project overview, features, setup guide, and doc status
│
├── traceability-matrix.md
├── requirements/
│   └── requirements-document.md              # Full functional and non-functional requirements (FR-*, NFR-*)
│
├── high-level-design/
│   ├── architecture-overview.md              # System architecture, deployment topology, and service boundaries
│   ├── data-flow-diagrams.md                 # End-to-end data flows across all major modules
│   └── technology-stack.md                   # Rationale for each chosen technology and integration pattern
│
├── detailed-design/
│   ├── reservation-engine.md                 # Deep-dive: booking state machine, conflict resolution, rate logic
│   ├── channel-manager.md                    # ARI sync protocol, OTA adapter design, parity enforcement
│   ├── folio-billing-engine.md               # Folio lifecycle, routing rules, tax engine, invoice generation
│   ├── housekeeping-module.md                # Room-state FSM, task scheduler, mobile app interface
│   ├── night-audit-processor.md              # Audit sequence, rollover procedure, reconciliation logic
│   ├── revenue-management-engine.md          # Rate optimisation model, pick-up analytics, forecasting pipeline
│   ├── loyalty-engine.md                     # Points ledger, tier evaluation, redemption workflow
│   └── pos-integration.md                    # POS posting API, offline queue, fiscal compliance
│
├── implementation/
│   ├── api-reference.md                      # REST API catalogue: endpoints, request/response schemas, auth
│   ├── database-schema.md                    # Full ERD, table definitions, indexes, and partitioning strategy
│   ├── event-catalog.md                      # All domain events, Kafka topics, payload schemas
│   └── coding-standards.md                   # TypeScript style guide, naming conventions, review checklist
│
├── infrastructure/
│   ├── deployment-guide.md                   # Docker Compose local setup, Kubernetes production manifests
│   ├── ci-cd-pipeline.md                     # GitHub Actions workflows, environment promotion, rollback
│   ├── monitoring-alerting.md                # Prometheus metrics, Grafana dashboards, PagerDuty runbooks
│   └── disaster-recovery.md                  # RTO/RPO targets, backup schedule, failover playbook
│
├── analysis/
│   ├── competitive-analysis.md               # Comparison against Opera Cloud, Mews, Cloudbeds, Apaleo
│   └── market-requirements.md               # Hotel segment needs, pain-point research, feature prioritisation
│
└── edge-cases/
    └── edge-cases-document.md               # Exhaustive edge-case catalogue per module with resolution approach
```

---

## Key Features

### Reservations Engine
- **Online booking widget** with real-time availability calendar, room-type image galleries, and upsell modals that surface room upgrades and packages based on the guest's stay profile and length of stay.
- **OTA and GDS integration** via two-way XML/JSON adapters for Booking.com, Expedia, Airbnb, Amadeus GDS, and Sabre, with automatic allotment pooling and stop-sell propagation across all connected channels within 90 seconds.
- **Group and block reservations** with a dedicated block management interface allowing room-type allocation, pick-up tracking, rooming list import via CSV/Excel, and automatic release of unused rooms at a configurable cut-off date.
- **Waitlist and overbooking management** with a configurable oversell percentage per room type, automated waitlist promotion when cancellations occur, and guest notification via SMS and email at each status change.

### Front Desk Operations
- **Unified arrival and departure dashboard** presenting arrivals, in-house guests, and departures in a single colour-coded tapechart, with one-click check-in, room assignment, and keycard encoding via RFID/MIFARE interfaces.
- **Walk-in processing** with instant availability search, real-time rate display, ID/passport scan via OCR, payment pre-authorisation, and printed registration card generation in under 30 seconds.
- **Mobile and web check-in** allowing guests to complete registration forms, select rooms from an interactive floor plan, and receive a mobile key to their smartphone 24 hours before arrival.
- **Express check-out** via guest-facing kiosk or mobile app with automatic folio presentation, digital signature capture, and emailed final invoice within seconds of settlement.

### Housekeeping Management
- **Live room-status board** with colour-coded states (Vacant Clean, Vacant Dirty, Occupied Clean, Occupied Dirty, Inspected, Out of Order, Out of Service) updated in real time as housekeepers mark tasks complete on mobile devices.
- **Automated task assignment** distributing rooms across housekeeper sections based on configurable load rules, room priority (arrivals first), and staff shift schedules, with supervisor override capability.
- **Maintenance integration** allowing housekeepers to raise work orders from inside the room-status app, auto-routing them to the engineering queue with photo attachments and urgency classification.
- **Green program and minibar charging** supporting do-not-disturb opt-outs with configurable stayover service schedules, and minibar consumption entry that posts charges directly to the guest folio in real time.

### Point of Sale Integration
- **Multi-outlet posting** from restaurant, bar, spa, gym, room service, and retail outlets directly onto guest folios or city ledger accounts with outlet code tagging for revenue centre reporting.
- **Offline mode** with a local transaction queue that buffers up to 500 postings during network interruption and reconciles automatically with the PMS on reconnection, preventing revenue loss.
- **Split billing and comp posting** enabling cashiers to split a charge across multiple folios, apply manager-authorised complimentary discounts, or route charges to corporate accounts based on pre-configured routing instructions.
- **Fiscal compliance** generating locally signed electronic receipts in conformance with country-specific fiscal regulations (e.g., Italy SDI, Germany GoBD, Portugal SAF-T), with automatic transmission to tax authorities where required.

### Folio and Billing
- **Master and sub-folio architecture** allowing each reservation to carry multiple sub-folios segmented by charge type (room, F&B, spa, incidentals) with configurable routing rules that auto-post charges to the correct folio window.
- **City ledger and company billing** with direct-bill account management, credit limit enforcement, monthly statement generation, and AR ageing reports integrated with the finance module.
- **Multi-currency support** with ECB-sourced daily exchange rates, currency conversion at posting time, and the ability to settle in any accepted currency while reporting in the property's base currency.
- **Tax engine** supporting multiple concurrent tax rules (VAT, city tax, tourism levy, service charge) with rate-by-room-type and rate-by-date logic, proforma invoice generation, and credit note issuance.

### Channel Management and OTA Sync
- **Two-way ARI updates** (Availability, Rates, Inventory) pushed to all connected channels within 90 seconds of a change in the PMS, using a push-over-pull architecture with exponential-backoff retry on channel API failures.
- **Rate parity enforcement** with a parity monitor dashboard that alerts revenue managers when a channel displays a rate lower than the best available rate configured in the PMS, with one-click parity restoration.
- **Booking ingestion and modification sync** automatically importing new reservations, modifications, and cancellations from OTA channels via webhook callbacks and SFTP polling fallback, de-duplicating messages using channel booking reference IDs.
- **Commission tracking and reconciliation** recording the commission percentage per channel per booking, generating monthly commission statements, and reconciling against channel invoices to flag discrepancies.

### Night Audit
- **Automated room charge posting** running at a configurable time each night to post the correct nightly room rate, applicable packages, and taxes to every in-house guest folio, with exception reporting for rate discrepancies.
- **No-show processing** automatically applying the no-show fee from the rate plan policy, charging the guaranteed payment method, and updating the reservation status to No-Show with a timestamped audit log entry.
- **Date rollover and report generation** advancing the system business date, generating the daily Manager's Report, Occupancy Report, Revenue Report, and Cashier Report, and archiving them in PDF to the document store.
- **End-of-day reconciliation** comparing departmental totals against individual posting records, flagging any open cashier shifts, and triggering an encrypted backup of the day's transaction journal.

### Loyalty Program
- **Point accrual and redemption** earning points based on configurable earn rates per revenue category (room nights, F&B, spa) and allowing redemption against room charges, F&B bills, or spa treatments at check-out.
- **Tier management** with up to five configurable membership tiers (e.g., Silver, Gold, Platinum, Diamond, Ambassador), automatic tier evaluation at each anniversary date, and tier-based benefit entitlements such as welcome amenities, late check-out, and complimentary upgrades.
- **Stay history and member communications** maintaining a full lifetime stay history per member with automated pre-arrival, in-stay, and post-stay emails personalised with stay details, points balance, and targeted offers.
- **Third-party loyalty integration** supporting bidirectional sync with external loyalty platforms (e.g., Marriott Bonvoy-style schemes) via REST webhook, mapping external point currencies to internal earn/burn rates.

### Revenue Management
- **BAR pricing and rate plan management** with a complete rate plan hierarchy covering BAR, advance purchase, package, corporate, wholesale, and OTA-net rates, each with configurable stay restrictions, minimum advance booking, and blackout dates.
- **Dynamic length-of-stay restrictions** including minimum stay, maximum stay, closed-to-arrival (CTA), and closed-to-departure (CTD) controls configurable per room type, per channel, and per date range.
- **Pick-up and pace reporting** displaying on-the-books versus same-time-last-year occupancy and revenue by room type and market segment, with configurable alert thresholds that notify the revenue manager of unusual pace deviations.
- **Demand forecasting** using a weighted moving average model trained on 24 months of historical occupancy, segmented by day-of-week, season, and local events, providing a 90-day forward forecast refreshed nightly after audit.

---

## Getting Started

- Review [`traceability-matrix.md`](./traceability-matrix.md) first to navigate requirement-to-implementation coverage across phases.
### Prerequisites

| Dependency     | Minimum Version | Purpose                                      |
|----------------|-----------------|----------------------------------------------|
| Node.js        | 20.x LTS        | API server and background job workers        |
| PostgreSQL     | 15.x            | Primary relational datastore                 |
| Redis          | 7.x             | Session cache, rate-limit counters, job queue|
| Docker         | 24.x            | Local development containerisation           |
| Docker Compose | 2.x             | Multi-service local orchestration            |

### Setup Steps

**1. Clone the repository and install dependencies**
```bash
git clone https://github.com/your-org/hotel-pms.git
cd hotel-pms
npm install
```

**2. Copy and configure environment variables**
```bash
cp .env.example .env
# Edit .env with your local values (see Environment Variables section below)
```

**3. Start infrastructure services**
```bash
docker compose up -d postgres redis
# Postgres will be available on localhost:5432
# Redis will be available on localhost:6379
```

**4. Run database migrations**
```bash
npm run db:migrate
# Applies all Knex migrations in db/migrations/ in sequence
```

**5. Seed reference data**
```bash
npm run db:seed
# Loads room types, rate plans, tax codes, currencies, and a demo property
```

**6. Start the development server**
```bash
npm run dev
# API server on http://localhost:3000
# Background workers (audit processor, channel sync, notification dispatcher) start automatically
```

**7. (Optional) Start the frontend**
```bash
cd client
npm install
npm run dev
# Frontend on http://localhost:5173
```

**8. Verify the installation**
```bash
curl http://localhost:3000/health
# Expected: {"status":"ok","database":"connected","redis":"connected","version":"1.0.0"}
```

### Environment Variables

| Variable                        | Description                                                         | Example Value                          |
|---------------------------------|---------------------------------------------------------------------|----------------------------------------|
| `NODE_ENV`                      | Runtime environment                                                 | `development`                          |
| `PORT`                          | HTTP port the API server listens on                                 | `3000`                                 |
| `DATABASE_URL`                  | PostgreSQL connection string                                        | `postgresql://pms:secret@localhost:5432/hotel_pms` |
| `REDIS_URL`                     | Redis connection string                                             | `redis://localhost:6379`               |
| `JWT_SECRET`                    | HS256 signing secret for access tokens (min 64 chars)              | `<random-256-bit-hex>`                 |
| `JWT_REFRESH_SECRET`            | Separate secret for refresh token signing                           | `<random-256-bit-hex>`                 |
| `JWT_EXPIRY`                    | Access token TTL                                                    | `15m`                                  |
| `ENCRYPTION_KEY`                | AES-256 key for PII field encryption (32 bytes, base64)            | `<base64-encoded-key>`                 |
| `SMTP_HOST`                     | SMTP relay hostname for transactional email                        | `smtp.sendgrid.net`                    |
| `SMTP_PORT`                     | SMTP port                                                           | `587`                                  |
| `SMTP_USER`                     | SMTP authentication username                                        | `apikey`                               |
| `SMTP_PASS`                     | SMTP authentication password / API key                             | `SG.xxxx`                              |
| `TWILIO_ACCOUNT_SID`            | Twilio account identifier for SMS notifications                    | `ACxxxxxxxxxxxxxxxx`                   |
| `TWILIO_AUTH_TOKEN`             | Twilio authentication token                                         | `xxxxxxxxxxxxxxxx`                     |
| `TWILIO_FROM_NUMBER`            | Twilio sender phone number                                          | `+15550001234`                         |
| `STRIPE_SECRET_KEY`             | Stripe secret key for payment processing                            | `sk_live_xxxx`                         |
| `STRIPE_WEBHOOK_SECRET`         | Stripe webhook endpoint signing secret                             | `whsec_xxxx`                           |
| `BOOKING_COM_API_KEY`           | Booking.com Connectivity API key                                   | `xxxx`                                 |
| `EXPEDIA_API_KEY`               | Expedia QuickConnect API key                                        | `xxxx`                                 |
| `EXPEDIA_API_SECRET`            | Expedia QuickConnect API secret                                     | `xxxx`                                 |
| `GDS_AMADEUS_CLIENT_ID`         | Amadeus for Developers client ID                                    | `xxxx`                                 |
| `GDS_AMADEUS_CLIENT_SECRET`     | Amadeus for Developers client secret                               | `xxxx`                                 |
| `S3_BUCKET`                     | AWS S3 bucket for document and backup storage                      | `hotel-pms-documents`                  |
| `S3_REGION`                     | AWS region for S3 bucket                                            | `eu-west-1`                            |
| `AWS_ACCESS_KEY_ID`             | AWS IAM access key                                                  | `AKIAIOSFODNN7EXAMPLE`                 |
| `AWS_SECRET_ACCESS_KEY`         | AWS IAM secret access key                                           | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `KAFKA_BROKERS`                 | Comma-separated Kafka broker addresses                             | `localhost:9092`                       |
| `AUDIT_CRON`                    | Cron expression for nightly audit trigger                           | `0 3 * * *`                            |
| `CHANNEL_SYNC_INTERVAL_SECONDS` | ARI push interval to channels                                       | `90`                                   |
| `LOG_LEVEL`                     | Pino log level                                                      | `info`                                 |

---

## Documentation Status

- ✅ Traceability coverage is available via [`traceability-matrix.md`](./traceability-matrix.md).
| Document                               | Status   | Last Updated |
|----------------------------------------|----------|--------------|
| README.md                              | Complete | 2025-01-15   |
| requirements/requirements-document.md  | Complete | 2025-01-15   |
| high-level-design/architecture-overview.md | Complete | 2025-01-15 |
| high-level-design/data-flow-diagrams.md    | Complete | 2025-01-15 |
| high-level-design/technology-stack.md      | Complete | 2025-01-15 |
| detailed-design/reservation-engine.md      | Complete | 2025-01-15 |
| detailed-design/channel-manager.md         | Complete | 2025-01-15 |
| detailed-design/folio-billing-engine.md    | Complete | 2025-01-15 |
| detailed-design/housekeeping-module.md     | Complete | 2025-01-15 |
| detailed-design/night-audit-processor.md   | Complete | 2025-01-15 |
| detailed-design/revenue-management-engine.md | Complete | 2025-01-15 |
| detailed-design/loyalty-engine.md          | Complete | 2025-01-15 |
| detailed-design/pos-integration.md         | Complete | 2025-01-15 |
| implementation/api-reference.md            | Complete | 2025-01-15 |
| implementation/database-schema.md          | Complete | 2025-01-15 |
| implementation/event-catalog.md            | Complete | 2025-01-15 |
| implementation/coding-standards.md         | Complete | 2025-01-15 |
| infrastructure/deployment-guide.md         | Complete | 2025-01-15 |
| infrastructure/ci-cd-pipeline.md           | Complete | 2025-01-15 |
| infrastructure/monitoring-alerting.md      | Complete | 2025-01-15 |
| infrastructure/disaster-recovery.md        | Complete | 2025-01-15 |
| analysis/competitive-analysis.md           | Complete | 2025-01-15 |
| analysis/market-requirements.md            | Complete | 2025-01-15 |
| edge-cases/edge-cases-document.md          | Complete | 2025-01-15 |
