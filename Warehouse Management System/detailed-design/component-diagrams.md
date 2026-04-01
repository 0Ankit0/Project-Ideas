# Component Diagrams

## Overview

The Warehouse Management System (WMS) is built on a service-oriented architecture (SOA) in which each bounded domain is encapsulated as an independently deployable service. Services communicate synchronously over REST/gRPC for request-reply interactions and asynchronously over an event bus (Kafka) for domain-event propagation. All services share a common infrastructure layer consisting of PostgreSQL (persistence), Redis (caching and locking), Kafka (event streaming), and S3-compatible object storage (labels, manifests, reports).

| Service | Responsibility |
|---|---|
| **API Gateway** | TLS termination, JWT validation, rate limiting, request routing |
| **Receiving Service** | ASN ingestion, receipt recording, discrepancy detection, putaway task creation |
| **Putaway Service** | Directed putaway execution, slot assignment, inventory balance update |
| **Allocation Service** | ATP calculation, stock reservation, rotation policy enforcement |
| **Wave Service** | Wave planning, order batching, release scheduling |
| **Pick Service** | Pick task dispatch, scan confirmation, short-pick handling |
| **Pack Service** | Pack session management, carton building, label requests |
| **Shipping Service** | Carrier rate shopping, label generation, manifest building, dispatch |
| **Cycle Count Service** | Count task scheduling, variance detection, adjustment posting |
| **Replenishment Service** | Min/max triggers, replenishment task creation and execution |
| **Returns Service** | RMA ingestion, disposition routing, credit/restock posting |
| **Notification Service** | Fan-out of domain events to email, SMS, and push channels |
| **Reporting Service** | Operational dashboards, KPI aggregation, scheduled report generation |

---

## Service Architecture Overview

```mermaid
flowchart TB
    subgraph External[External Systems]
        OMS[OMS\nOrder Management]
        ERP[ERP\nEnterprise Resource]
        CarrierAPIs[Carrier APIs\nFedEx · UPS · DHL]
        MobileApp[WMS Mobile App\niOS / Android]
        AdminPortal[Admin Portal\nWeb SPA]
    end

    subgraph Gateway[API Layer]
        APIGW[API Gateway\nJWT · Rate Limit · Routing]
    end

    subgraph CoreServices[Core WMS Services]
        RCV[Receiving Service]
        PUT[Putaway Service]
        ALLOC[Allocation Service]
        WAVE[Wave Service]
        PICK[Pick Service]
        PACK[Pack Service]
        SHIP[Shipping Service]
        CC[Cycle Count Service]
        REPL[Replenishment Service]
        RET[Returns Service]
        NOTIF[Notification Service]
        RPT[Reporting Service]
    end

    subgraph Infra[Infrastructure]
        PG[(PostgreSQL\nTransactional DB)]
        REDIS[(Redis Cache\n+ Distributed Lock)]
        KAFKA[(Event Bus\nKafka)]
        S3[(Object Storage\nS3)]
    end

    OMS -->|ASNs, Orders| APIGW
    ERP -->|PO data, SKU master| APIGW
    MobileApp -->|Scan events| APIGW
    AdminPortal -->|Config, reports| APIGW
    APIGW --> RCV
    APIGW --> ALLOC
    APIGW --> WAVE
    APIGW --> PICK
    APIGW --> PACK
    APIGW --> SHIP
    APIGW --> CC
    APIGW --> REPL
    APIGW --> RET
    APIGW --> RPT

    RCV -->|putaway.task.created| KAFKA
    PUT -->|inventory.balance.updated| KAFKA
    ALLOC -->|stock.reserved| KAFKA
    WAVE -->|wave.released| KAFKA
    PICK -->|pick.confirmed| KAFKA
    PACK -->|pack.completed| KAFKA
    SHIP -->|shipment.dispatched| KAFKA
    CC -->|variance.posted| KAFKA
    REPL -->|replenishment.completed| KAFKA
    RET -->|return.processed| KAFKA

    KAFKA --> NOTIF
    KAFKA --> RPT
    KAFKA --> REPL
    KAFKA --> CC

    SHIP -->|Rate & Label API| CarrierAPIs
    CarrierAPIs -->|Tracking events| SHIP

    RCV --> PG
    PUT --> PG
    ALLOC --> PG
    WAVE --> PG
    PICK --> PG
    PACK --> PG
    SHIP --> PG
    CC --> PG
    REPL --> PG
    RET --> PG

    ALLOC --> REDIS
    WAVE --> REDIS
    PICK --> REDIS

    SHIP --> S3
    RPT --> S3
    PACK --> S3
```

---

## Receiving Service Components

```mermaid
flowchart LR
    subgraph API[API Layer]
        ASNCTL[ASN Controller\nREST /api/v1/asns]
    end

    subgraph Domain[Domain Components]
        ASNVAL[ASN Validator\nvalidates against PO]
        RCVPROC[Receipt Processor\nrecords quantities]
        DISDET[Discrepancy Detector\nover · under · damage]
        PUTGEN[Putaway Task Generator\ncreates directed tasks]
        EVTPUB[Receiving Event Publisher\nOutbox pattern]
    end

    subgraph Data[Data Layer]
        ASNREPO[ASN Repository\nCRUD + status transitions]
        INVREPO[Inventory Balance Repository\nupdates on-hand qty]
    end

    subgraph External[External]
        OMS_IN[OMS\nASN source]
        SCANNER[Scanner App\nscan events]
        KAFKA_OUT[Event Bus\nKafka]
        PG_DB[(PostgreSQL)]
    end

    OMS_IN -->|POST /asns| ASNCTL
    SCANNER -->|POST /receipts| ASNCTL
    ASNCTL --> ASNVAL
    ASNVAL -->|valid ASN| RCVPROC
    ASNVAL -->|invalid| ASNCTL
    RCVPROC --> DISDET
    DISDET -->|discrepancy record| ASNREPO
    RCVPROC --> PUTGEN
    PUTGEN -->|putaway task| KAFKA_OUT
    RCVPROC --> EVTPUB
    EVTPUB -->|receipt.completed| KAFKA_OUT
    ASNREPO --> PG_DB
    INVREPO --> PG_DB
    RCVPROC --> INVREPO
```

**Component Responsibilities:**

| Component | Responsibility |
|---|---|
| ASN Controller | Accepts inbound ASN payloads from OMS and scan confirmations from scanners; validates HTTP contract |
| ASN Validator | Cross-checks ASN line items against open purchase orders; enforces quantity and SKU constraints |
| Receipt Processor | Persists received quantities, drives state transitions on the ASN document |
| Discrepancy Detector | Compares expected vs. received quantities; raises over/under/damage events |
| Putaway Task Generator | Creates directed putaway tasks based on SKU putaway rules and available slot assignments |
| Receiving Event Publisher | Writes domain events to the transactional outbox; relay process forwards to Kafka |
| ASN Repository | Owns all persistence for ASN documents and their line-item status |
| Inventory Balance Repository | Applies delta updates to on-hand inventory balances on receipt confirmation |

---

## Allocation and Wave Service Components

```mermaid
flowchart TB
    subgraph API[API Layer]
        ORDCTL[Order Intake Controller\nREST /api/v1/allocations]
    end

    subgraph Allocation[Allocation Domain]
        ATP[ATP Calculator\navailable-to-promise]
        ROTP[Rotation Policy Engine\nFEFO · FEFO · FIFO · LIFO]
        STOCK[Stock Allocator\nreserves inventory]
        ALLOCREPO[Allocation Repository\nreservations + locks]
    end

    subgraph Wave[Wave Domain]
        WPLAN[Wave Planner\nbatch + schedule waves]
        PPOPT[Pick Path Optimizer\nzone / aisle sequencing]
        PLGEN[Pick List Generator\nper-picker task lists]
        WAVEREPO[Wave Repository\nwave + pick-list state]
    end

    subgraph Events[Event Layer]
        WEVT[Wave Event Publisher\nOutbox pattern]
        KAFKA_OUT[Event Bus\nKafka]
    end

    subgraph External[External]
        OMS_ORD[OMS\norder feed]
        REDIS_LK[(Redis\ndistributed lock)]
        PG_DB[(PostgreSQL)]
    end

    OMS_ORD -->|POST /allocations| ORDCTL
    ORDCTL --> ATP
    ATP -->|available qty| STOCK
    STOCK --> ROTP
    ROTP -->|rotation-aware lots| STOCK
    STOCK -->|reservation| ALLOCREPO
    ALLOCREPO --> REDIS_LK
    ALLOCREPO --> PG_DB
    STOCK --> WPLAN
    WPLAN --> PPOPT
    PPOPT --> PLGEN
    PLGEN --> WAVEREPO
    WAVEREPO --> PG_DB
    WPLAN --> WEVT
    WEVT -->|wave.released| KAFKA_OUT
```

**Component Responsibilities:**

| Component | Responsibility |
|---|---|
| Order Intake Controller | Accepts allocation requests from OMS; validates order lines and priority flags |
| ATP Calculator | Queries on-hand minus reserved quantities to determine what can be promised |
| Rotation Policy Engine | Enforces FEFO/FIFO/LIFO rotation per SKU class when selecting lots |
| Stock Allocator | Creates soft reservations using optimistic locking via Redis; commits to PostgreSQL |
| Wave Planner | Groups allocated orders into waves by zone, carrier cutoff, and priority |
| Pick Path Optimizer | Sequences pick locations to minimize travel distance using zone-aisle ordering |
| Pick List Generator | Produces per-picker task lists with optimized slot sequences |
| Wave Event Publisher | Emits `wave.released` events via outbox pattern for downstream services |
| Allocation Repository | Persists reservation records with concurrency-safe update patterns |
| Wave Repository | Stores wave headers, pick lists, and status lifecycle |

---

## Fulfillment Service Components

```mermaid
flowchart LR
    subgraph PickDomain[Pick Domain]
        PICKCTL[Pick Controller\nREST /api/v1/picks]
        PCKHNDL[Pick Confirmation Handler\nscanner confirmations]
        SHRTPCK[Short Pick Handler\nbackorder · substitute]
        PICKREPO[Pick Repository\npick task state]
    end

    subgraph PackDomain[Pack Domain]
        PACKCTL[Pack Controller\nREST /api/v1/packs]
        PSESSMGR[Pack Session Manager\nstation lifecycle]
        CTRBLD[Container Builder\ncarton selection + packing]
        LBLREQ[Label Request Handler\nZPL · PDF labels]
        PACKREPO[Pack Repository\npack session + carton state]
    end

    subgraph Events[Event Layer]
        FEVT[Fulfillment Event Publisher\nOutbox pattern]
        KAFKA_OUT[Event Bus\nKafka]
    end

    subgraph External[External]
        SCANNER[Mobile Scanner\nscan events]
        SHIP_SVC[Shipping Service\nlabel API]
        PG_DB[(PostgreSQL)]
    end

    SCANNER -->|PUT /picks/:id/confirm| PICKCTL
    PICKCTL --> PCKHNDL
    PCKHNDL -->|short qty| SHRTPCK
    SHRTPCK -->|backorder event| KAFKA_OUT
    PCKHNDL --> PICKREPO
    PICKREPO --> PG_DB

    SCANNER -->|POST /packs| PACKCTL
    PACKCTL --> PSESSMGR
    PSESSMGR --> CTRBLD
    CTRBLD --> LBLREQ
    LBLREQ -->|label request| SHIP_SVC
    SHIP_SVC -->|ZPL label| LBLREQ
    PSESSMGR --> PACKREPO
    PACKREPO --> PG_DB

    PCKHNDL --> FEVT
    PSESSMGR --> FEVT
    FEVT -->|pick.confirmed, pack.completed| KAFKA_OUT
```

**Component Responsibilities:**

| Component | Responsibility |
|---|---|
| Pick Controller | Exposes pick task assignment and confirmation endpoints; routes scanner payloads |
| Pick Confirmation Handler | Validates scanned barcode against expected task; updates pick quantity |
| Short Pick Handler | Records shortage, triggers backorder or substitution workflow via event |
| Pack Controller | Manages pack station sessions; accepts scan-to-pack and close-carton commands |
| Pack Session Manager | Maintains the lifecycle of a pack station session from open to closed |
| Container Builder | Selects optimal carton size and records item-to-carton assignments |
| Label Request Handler | Requests shipping labels from Shipping Service; stores label reference |
| Fulfillment Event Publisher | Writes `pick.confirmed` and `pack.completed` events to outbox |
| Pick Repository | Persists pick task state including confirmations and shortage records |
| Pack Repository | Persists pack sessions, carton contents, and label associations |

---

## Shipping Service Components

```mermaid
flowchart TB
    subgraph API[API Layer]
        SHIPCTL[Shipment Controller\nREST /api/v1/shipments]
    end

    subgraph Core[Core Domain]
        CARRADP[Carrier Adapter\npluggable per carrier]
        RATESHOP[Rate Shopping Engine\nmulti-carrier comparison]
        LBLGEN[Label Generation Service\nZPL · PDF · PNG]
        MFSTBLD[Manifest Builder\nend-of-day manifest]
        DISPCONF[Dispatch Confirmer\nseals shipment]
        TRKPOLL[Tracking Poller\nstatus sync job]
    end

    subgraph Data[Data Layer]
        SHIPREPO[Shipment Repository\nshipment + package state]
        CARRCONF[Carrier Configuration Repository\naccounts · service levels]
    end

    subgraph Events[Event Layer]
        SHPEVT[Shipping Event Publisher\nOutbox pattern]
        KAFKA_OUT[Event Bus\nKafka]
    end

    subgraph External[External]
        FEDEX[FedEx API]
        UPS[UPS API]
        DHL[DHL API]
        S3_STORE[(S3\nlabel + manifest storage)]
        PG_DB[(PostgreSQL)]
    end

    SHIPCTL --> RATESHOP
    RATESHOP --> CARRADP
    CARRADP --> FEDEX
    CARRADP --> UPS
    CARRADP --> DHL
    CARRADP -->|rates| RATESHOP
    RATESHOP -->|selected rate| LBLGEN
    LBLGEN --> CARRADP
    CARRADP -->|label bytes| LBLGEN
    LBLGEN --> S3_STORE
    SHIPCTL --> MFSTBLD
    MFSTBLD --> DISPCONF
    DISPCONF --> SHIPREPO
    TRKPOLL --> CARRADP
    TRKPOLL -->|tracking update| SHIPREPO
    SHIPREPO --> PG_DB
    CARRCONF --> PG_DB
    DISPCONF --> SHPEVT
    SHPEVT -->|shipment.dispatched| KAFKA_OUT
```

**Component Responsibilities:**

| Component | Responsibility |
|---|---|
| Shipment Controller | Accepts shipment creation requests from Pack Service; exposes status endpoints |
| Carrier Adapter | Pluggable abstraction over carrier-specific APIs; normalises request/response models |
| Rate Shopping Engine | Queries multiple carriers in parallel; selects lowest cost or fastest service |
| Label Generation Service | Requests labels from chosen carrier; stores label to S3; returns label reference |
| Manifest Builder | Aggregates shipments into an end-of-day manifest per carrier account |
| Dispatch Confirmer | Marks shipment as dispatched; triggers manifest submission to carrier |
| Tracking Poller | Scheduled job that fetches tracking milestones and persists status updates |
| Shipping Event Publisher | Emits `shipment.dispatched` and `tracking.updated` events via outbox |
| Shipment Repository | Persists shipment headers, package details, label refs, and tracking history |
| Carrier Configuration Repository | Stores carrier account credentials, service levels, and rate card rules |

---

## Component Interface Contracts

| Component | Interface | Protocol | Input | Output | Error Contract |
|---|---|---|---|---|---|
| ASN Controller | `POST /api/v1/asns` | REST/JSON | `AsnPayload` (header + lines) | `201 AsnResponse` | `400` validation; `409` duplicate ASN |
| ASN Validator | Internal function | In-process | `AsnPayload`, PO data | `ValidationResult` | Throws `AsnValidationException` |
| Receipt Processor | Internal function | In-process | `ReceiptCommand` | `ReceiptRecord` | Throws `InventoryException` on balance conflict |
| Discrepancy Detector | Internal function | In-process | expected vs. actual qty | `DiscrepancyReport` | Returns empty list if no discrepancy |
| Putaway Task Generator | Internal function | In-process | `ReceiptRecord` | `List<PutawayTask>` | Throws `NoSlotAvailableException` |
| Order Intake Controller | `POST /api/v1/allocations` | REST/JSON | `AllocationRequest` | `202 AllocationRef` | `422` insufficient stock; `429` rate limit |
| ATP Calculator | Internal function | In-process | `SkuId`, `WarehouseId` | `AvailableQty` | Returns 0; never throws |
| Stock Allocator | Internal function | In-process | `AllocationRequest`, `AvailableQty` | `Reservation` | Throws `OptimisticLockException` on conflict |
| Wave Planner | Internal function | In-process | `List<Reservation>` | `Wave` | Throws `WaveConstraintException` |
| Pick Confirmation Handler | `PUT /api/v1/picks/:id/confirm` | REST/JSON | `ConfirmPayload` (scan + qty) | `200 PickTask` | `404` task not found; `409` already confirmed |
| Short Pick Handler | Internal function | In-process | `PickTask`, actualQty | `ShortageRecord` | Emits `pick.shorted` event; never throws |
| Pack Session Manager | `POST /api/v1/packs` | REST/JSON | `PackStartCommand` | `201 PackSession` | `400` invalid station; `409` session active |
| Container Builder | Internal function | In-process | `PackSession`, `ItemList` | `Carton` | Throws `CartonOverflowException` |
| Shipment Controller | `POST /api/v1/shipments` | REST/JSON | `ShipmentRequest` | `201 ShipmentResponse` | `400` invalid address; `503` carrier unavailable |
| Rate Shopping Engine | Internal function | In-process | `ShipmentRequest` | `List<RateQuote>` | Returns empty if all carriers fail |
| Carrier Adapter | Internal interface | In-process | `CarrierRequest` | `CarrierResponse` | Throws `CarrierApiException`; retried with backoff |
| Label Generation Service | Internal function | In-process | `RateQuote` | `LabelReference` (S3 key) | Throws `LabelGenerationException` |
| Manifest Builder | `POST /api/v1/manifests` | REST/JSON | `ManifestRequest` | `201 ManifestResponse` | `409` manifest already closed |
| Tracking Poller | Scheduled job | Cron/internal | Carrier tracking IDs | `TrackingUpdate` | Logs failures; skips on transient error |

---

## Component Dependencies Matrix

| Component | PostgreSQL | Redis | Kafka (publish) | Kafka (consume) | OMS | Carrier APIs | S3 |
|---|---|---|---|---|---|---|---|
| ASN Controller | ✓ read | — | — | — | — | — | — |
| ASN Validator | ✓ read (PO data) | — | — | — | — | — | — |
| Receipt Processor | ✓ write | — | — | — | — | — | — |
| Discrepancy Detector | ✓ write | — | — | — | — | — | — |
| Putaway Task Generator | ✓ write | — | ✓ | — | — | — | — |
| Receiving Event Publisher | ✓ outbox | — | ✓ | — | — | — | — |
| ATP Calculator | ✓ read | ✓ cache | — | — | — | — | — |
| Stock Allocator | ✓ write | ✓ lock | — | — | — | — | — |
| Rotation Policy Engine | ✓ read | — | — | — | — | — | — |
| Wave Planner | ✓ write | ✓ cache | ✓ | — | — | — | — |
| Pick Path Optimizer | ✓ read | — | — | — | — | — | — |
| Pick List Generator | ✓ write | — | — | — | — | — | — |
| Wave Event Publisher | ✓ outbox | — | ✓ | — | — | — | — |
| Pick Confirmation Handler | ✓ write | — | — | — | — | — | — |
| Short Pick Handler | ✓ write | — | ✓ | — | — | — | — |
| Pack Session Manager | ✓ write | — | — | — | — | — | — |
| Container Builder | ✓ write | — | — | — | — | — | — |
| Label Request Handler | ✓ write | — | — | — | — | — | ✓ |
| Fulfillment Event Publisher | ✓ outbox | — | ✓ | — | — | — | — |
| Rate Shopping Engine | ✓ read | ✓ cache | — | — | — | ✓ | — |
| Carrier Adapter | — | — | — | — | — | ✓ | — |
| Label Generation Service | ✓ write | — | — | — | — | ✓ | ✓ |
| Manifest Builder | ✓ write | — | — | — | — | — | ✓ |
| Dispatch Confirmer | ✓ write | — | ✓ | — | — | — | — |
| Tracking Poller | ✓ write | — | ✓ | — | — | ✓ | — |
| Shipping Event Publisher | ✓ outbox | — | ✓ | — | — | — | — |
| Cycle Count Engine | ✓ write | — | ✓ | — | — | — | — |
| Replenishment Engine | ✓ write | — | ✓ | ✓ | — | — | — |
| Returns Service | ✓ write | — | ✓ | — | ✓ | — | — |
| Notification Service | — | — | — | ✓ | — | — | — |
| Reporting Service | ✓ read | ✓ cache | — | ✓ | — | — | ✓ |

