# System Sequence Diagrams

## Overview

This document presents system-level sequence diagrams for the six most critical interactions in the WMS. Each diagram shows the full end-to-end flow including database writes, outbox event publications, and external system callbacks. All sequences use `autonumber` for step traceability and include both happy-path and failure branches.

---

## Sequence 1: Receive Pallet with ASN Validation

```mermaid
sequenceDiagram
    autonumber
    actor Receiver as Receiver (Operator)
    participant Scanner as RF Scanner
    participant APIGW as API Gateway
    participant RecvSvc as Receiving Service
    participant InvSvc as Inventory Service
    participant PG as PostgreSQL
    participant Outbox as Outbox Table
    participant OpsSvc as Operations Service

    Receiver->>Scanner: Scan pallet barcode + ASN label
    Scanner->>APIGW: POST /api/v1/receipts\n{asn_id, pallet_id, lines[]}
    APIGW->>APIGW: JWT validation + RBAC check (role: RECEIVER)
    APIGW->>RecvSvc: Forward validated request

    RecvSvc->>PG: SELECT asn_lines WHERE asn_id = ? AND status = OPEN
    PG-->>RecvSvc: ASN lines with expected quantities

    RecvSvc->>InvSvc: POST /internal/validate-lot\n{sku_code, lot_number, expiry_date}
    InvSvc->>PG: SELECT sku_master, lot_rules WHERE sku_code = ?
    PG-->>InvSvc: SKU rules (min shelf life, temp requirements)

    alt Lot expired or shelf life violation
        InvSvc-->>RecvSvc: 422 LOT_EXPIRED {lot_number, expiry_date}
        RecvSvc->>PG: INSERT INTO discrepancy_cases\n{receipt_id, reason: LOT_EXPIRED}
        RecvSvc->>PG: INSERT INTO outbox\n{event: discrepancy-raised, payload: ...}
        RecvSvc-->>APIGW: 422 {discrepancy_case_id}
        APIGW-->>Scanner: Show discrepancy screen
    else Quantity mismatch beyond tolerance
        InvSvc-->>RecvSvc: 200 valid lot
        RecvSvc->>RecvSvc: Compare received_qty vs expected_qty (±tolerance)
        RecvSvc->>PG: INSERT INTO discrepancy_cases\n{type: QTY_MISMATCH, delta: -5}
        RecvSvc->>PG: INSERT INTO outbox\n{event: discrepancy-raised}
        RecvSvc-->>APIGW: 207 PARTIAL_ACCEPT {discrepancy_case_id}
    else All validations pass
        InvSvc-->>RecvSvc: 200 valid lot + SKU confirmed
        RecvSvc->>PG: BEGIN TRANSACTION
        RecvSvc->>PG: INSERT INTO receipts {receipt_id, asn_id, ...}
        RecvSvc->>PG: INSERT INTO receipt_lines {lines[]}
        RecvSvc->>PG: INSERT INTO inventory_ledger\n{type: RECEIPT, qty_delta: +qty}
        RecvSvc->>Outbox: INSERT INTO outbox\n{event: receipt-created, receipt_id, sku_code, qty}
        RecvSvc->>PG: COMMIT
        RecvSvc->>OpsSvc: POST /internal/putaway-plan\n{receipt_id, lines[]}
        OpsSvc->>PG: SELECT bin_capacity_rules, zone_affinity WHERE sku_code = ?
        OpsSvc->>PG: INSERT INTO putaway_tasks {task_id, bin_code, qty}
        OpsSvc-->>RecvSvc: 201 {putaway_task_ids[]}
        RecvSvc-->>APIGW: 201 {receipt_id, putaway_task_ids[]}
        APIGW-->>Scanner: Show putaway instructions
    end
```

---

## Sequence 2: Confirm Shipment with Carrier Integration

```mermaid
sequenceDiagram
    autonumber
    actor Coord as Shipping Coordinator
    participant APIGW as API Gateway
    participant ShipSvc as Shipping Service
    participant PG as PostgreSQL
    participant PackSvc as Fulfillment Service
    participant CarrierRouter as Carrier Router
    participant FedEx as FedEx API
    participant S3 as AWS S3
    participant Outbox as Outbox Table
    participant OMS as OMS Callback

    Coord->>APIGW: POST /api/v1/shipments/{id}/confirm
    APIGW->>APIGW: JWT validation + RBAC check (role: SHIPPING_COORD)
    APIGW->>ShipSvc: Forward request

    ShipSvc->>PG: SELECT shipment WHERE id = ? AND status = READY_TO_SHIP
    PG-->>ShipSvc: Shipment record with pack_session_id

    ShipSvc->>PackSvc: GET /internal/pack-sessions/{id}/status
    PackSvc->>PG: SELECT pack_session WHERE id = ? AND status = CLOSED
    PG-->>PackSvc: Pack session with all lines reconciled
    PackSvc-->>ShipSvc: 200 {status: CLOSED, containers: [], total_weight_kg: 12.5}

    ShipSvc->>CarrierRouter: requestLabel({carrier_code, address, weight, dims})
    CarrierRouter->>FedEx: POST /ship/v1/shipments\n{shipper, recipient, packages[]}

    alt FedEx API timeout (>5s)
        FedEx-->>CarrierRouter: timeout
        CarrierRouter->>CarrierRouter: Circuit breaker trips to OPEN
        CarrierRouter->>PG: INSERT INTO label_retry_queue\n{shipment_id, carrier: FEDEX}
        CarrierRouter-->>ShipSvc: 503 CARRIER_UNAVAILABLE
        ShipSvc-->>APIGW: 503 {retry_after: 30, queue_ref: ...}
        APIGW-->>Coord: Show retry notification
    else FedEx returns label
        FedEx-->>CarrierRouter: 200 {tracking_number, label_pdf_base64}
        CarrierRouter->>S3: PUT labels/{shipment_id}/{tracking_number}.pdf
        S3-->>CarrierRouter: 200 ETag confirmed
        CarrierRouter-->>ShipSvc: 200 {tracking_number, label_url}
        ShipSvc->>PG: BEGIN TRANSACTION
        ShipSvc->>PG: UPDATE shipments SET status=CONFIRMED,\ntracking_number=?, label_url=?
        ShipSvc->>Outbox: INSERT INTO outbox\n{event: shipment-confirmed, tracking_number, carrier}
        ShipSvc->>PG: COMMIT
        ShipSvc->>OMS: POST /callbacks/shipment-confirmed\n{order_id, tracking_number, carrier}
        OMS-->>ShipSvc: 200 acknowledged
        ShipSvc-->>APIGW: 200 {shipment_id, tracking_number, label_url}
        APIGW-->>Coord: Show tracking number + print label prompt
    end
```

---

## Sequence 3: Wave Planning with OMS Integration

```mermaid
sequenceDiagram
    autonumber
    participant OMS as OMS System
    participant Kafka as Kafka Event Bus
    participant WaveWorker as Wave Planning Worker
    participant AllocSvc as Allocation Service
    participant PG as PostgreSQL
    participant Redis as Redis Cache
    participant Outbox as Outbox Table
    participant FulfillSvc as Fulfillment Service

    OMS->>Kafka: Publish order-released event\n{order_id, lines[], priority: HIGH}
    Kafka->>WaveWorker: Consume order-released

    WaveWorker->>AllocSvc: POST /internal/reserve\n{order_id, lines[]}
    AllocSvc->>Redis: GET inventory_balance:{sku_code}:{bin_code}
    Redis-->>AllocSvc: {on_hand: 100, reserved: 20, available: 80}

    AllocSvc->>AllocSvc: Apply FEFO policy — score bins by expiry date
    AllocSvc->>PG: SELECT FOR UPDATE inventory_balances\nWHERE sku_code=? AND available>=?
    PG-->>AllocSvc: Row lock acquired on optimal bin

    AllocSvc->>PG: BEGIN TRANSACTION
    AllocSvc->>PG: INSERT INTO reservations\n{reservation_id, order_id, sku_code, bin_code, qty}
    AllocSvc->>PG: UPDATE inventory_balances SET reserved = reserved + qty
    AllocSvc->>Outbox: INSERT INTO outbox\n{event: reservation-created, reservation_id}
    AllocSvc->>PG: COMMIT

    AllocSvc-->>WaveWorker: 201 {reservation_ids[]}

    WaveWorker->>PG: SELECT reservations WHERE wave_id IS NULL\nGROUP BY zone_id ORDER BY priority
    PG-->>WaveWorker: Unassigned reservations grouped by zone

    WaveWorker->>WaveWorker: Apply zone balancing algorithm\nMax 200 lines per wave
    WaveWorker->>PG: BEGIN TRANSACTION
    WaveWorker->>PG: INSERT INTO waves {wave_id, zone_ids[], status: PLANNED}
    WaveWorker->>PG: INSERT INTO wave_lines {wave_id, reservation_id, zone_id}[]
    WaveWorker->>PG: INSERT INTO pick_lists {pick_list_id, wave_id, zone_id}[]
    WaveWorker->>Outbox: INSERT INTO outbox\n{event: wave-planned, wave_id, pick_list_ids[]}
    WaveWorker->>PG: COMMIT

    Outbox->>Kafka: Relay wave-planned event
    Kafka->>FulfillSvc: Consume wave-planned
    FulfillSvc->>PG: UPDATE pick_lists SET status = RELEASED
    FulfillSvc->>PG: INSERT INTO pick_tasks {task_id, pick_list_id, scanner_id=NULL}[]
    FulfillSvc-->>Kafka: Publish pick-list-generated event
```

---

## Sequence 4: Real-Time Inventory Query from ERP

```mermaid
sequenceDiagram
    autonumber
    participant ERP as ERP System
    participant APIGW as API Gateway
    participant InvSvc as Inventory Service
    participant Redis as Redis Cache
    participant PG as PostgreSQL (Read Replica)
    participant PGWrite as PostgreSQL (Primary)

    ERP->>APIGW: GET /api/v1/inventory/balance\n?sku_code=SKU-001&warehouse_id=WH-01
    APIGW->>APIGW: JWT validation + RBAC (role: ERP_INTEGRATION)
    APIGW->>InvSvc: Forward request

    InvSvc->>Redis: GET inv_balance:WH-01:SKU-001
    alt Cache hit (TTL valid)
        Redis-->>InvSvc: {on_hand: 450, reserved: 80, available: 370}
        InvSvc-->>APIGW: 200 {on_hand, reserved, available, as_of: timestamp}
        APIGW-->>ERP: 200 balance response (p99 < 5ms)
    else Cache miss
        Redis-->>InvSvc: nil (cache miss)
        InvSvc->>PG: SELECT on_hand, reserved, (on_hand-reserved) AS available\nFROM inventory_balances\nWHERE sku_code=? AND warehouse_id=?
        PG-->>InvSvc: Row with current balance
        InvSvc->>Redis: SET inv_balance:WH-01:SKU-001 EX 300\n(5 minute TTL)
        InvSvc-->>APIGW: 200 {on_hand, reserved, available, as_of: timestamp}
        APIGW-->>ERP: 200 balance response (p99 < 30ms)
    end

    note over ERP,APIGW: ERP also polls /inventory/ledger for delta sync
    ERP->>APIGW: GET /api/v1/inventory/ledger\n?since=2024-01-15T08:00:00Z&warehouse_id=WH-01
    APIGW->>InvSvc: Forward request
    InvSvc->>PG: SELECT * FROM inventory_ledger\nWHERE warehouse_id=? AND created_at > ?\nORDER BY created_at LIMIT 1000
    PG-->>InvSvc: Ledger entries (paginated)
    InvSvc-->>APIGW: 200 {entries[], next_cursor}
    APIGW-->>ERP: 200 delta ledger (for ERP financial reconciliation)
```

---

## Sequence 5: Carrier Label Generation Flow

```mermaid
sequenceDiagram
    autonumber
    participant Kafka as Kafka Event Bus
    participant LabelWorker as Label Gen Worker
    participant ShipSvc as Shipping Service
    participant CarrierRouter as Carrier Router
    participant FedEx as FedEx API
    participant UPS as UPS API
    participant S3 as AWS S3
    participant PG as PostgreSQL
    participant Outbox as Outbox Table

    Kafka->>LabelWorker: Consume pack-closed event\n{pack_session_id, shipment_id, containers[]}
    LabelWorker->>ShipSvc: POST /internal/label/generate\n{shipment_id}

    ShipSvc->>PG: SELECT shipment JOIN pack_session\nWHERE shipment_id=? AND status=READY
    PG-->>ShipSvc: Shipment details (address, carrier_code, weight)

    ShipSvc->>CarrierRouter: selectCarrier({weight, dims, service_level, destination})
    CarrierRouter->>CarrierRouter: Apply carrier selection rules\n(rate + SLA + circuit breaker state)

    alt FedEx circuit breaker OPEN
        CarrierRouter->>CarrierRouter: FedEx CB is OPEN — skip
        CarrierRouter->>UPS: POST /ship/labels\n{packages, addresses}
        UPS-->>CarrierRouter: 200 {tracking_number, label_zpl}
    else FedEx available
        CarrierRouter->>FedEx: POST /ship/v1/shipments
        FedEx-->>CarrierRouter: 200 {tracking_number, label_pdf_base64}
    end

    CarrierRouter-->>ShipSvc: 200 {carrier, tracking_number, label_content}

    ShipSvc->>S3: PUT /labels/{shipment_id}/{tracking_number}.pdf\n(label_pdf_base64 decoded)
    S3-->>ShipSvc: 200 {etag, version_id}

    ShipSvc->>PG: BEGIN TRANSACTION
    ShipSvc->>PG: INSERT INTO tracking_labels\n{shipment_id, tracking_number, carrier_code, s3_key}
    ShipSvc->>PG: UPDATE shipments SET tracking_number=?, label_s3_key=?, status=LABEL_PRINTED
    ShipSvc->>Outbox: INSERT INTO outbox\n{event: label-generated, shipment_id, tracking_number}
    ShipSvc->>PG: COMMIT

    ShipSvc-->>LabelWorker: 201 {tracking_number, label_url (presigned)}
    LabelWorker->>Kafka: Acknowledge offset (commit)
```

---

## Sequence 6: Cycle Count Approval and Adjustment

```mermaid
sequenceDiagram
    autonumber
    actor Operator as Warehouse Operator
    actor Supervisor as Supervisor
    participant Scanner as RF Scanner
    participant APIGW as API Gateway
    participant OpsSvc as Operations Service
    participant InvSvc as Inventory Service
    participant PG as PostgreSQL
    participant Outbox as Outbox Table
    participant Kafka as Kafka Event Bus

    Supervisor->>APIGW: POST /api/v1/cycle-counts\n{zone_id, bin_range: A01-A20, scheduled_for}
    APIGW->>OpsSvc: Create cycle count
    OpsSvc->>PG: INSERT INTO cycle_counts\n{count_id, zone_id, bin_range, status: SCHEDULED}
    OpsSvc->>PG: INSERT INTO cycle_count_lines {count_id, bin_code, sku_code, system_qty}[]
    OpsSvc-->>APIGW: 201 {count_id, line_count: 20}
    APIGW-->>Supervisor: Cycle count created

    Operator->>Scanner: Start cycle count scan
    Scanner->>APIGW: POST /api/v1/cycle-counts/{id}/lines/{bin}/record\n{counted_qty, scan_timestamp}
    APIGW->>OpsSvc: Record count for bin
    OpsSvc->>PG: UPDATE cycle_count_lines\nSET counted_qty=?, status=COUNTED WHERE bin_code=?
    OpsSvc->>OpsSvc: Calculate variance = counted_qty - system_qty
    OpsSvc-->>APIGW: 200 {variance: -3, threshold_exceeded: true}
    APIGW-->>Scanner: Show variance flag (supervisor approval required)

    Operator->>APIGW: POST /api/v1/cycle-counts/{id}/submit
    APIGW->>OpsSvc: Submit count for review
    OpsSvc->>PG: UPDATE cycle_counts SET status=PENDING_APPROVAL
    OpsSvc-->>APIGW: 200 submitted

    Supervisor->>APIGW: GET /api/v1/cycle-counts/{id}/variance-report
    APIGW->>OpsSvc: Get variance summary
    OpsSvc->>PG: SELECT SUM(ABS(variance)) as total_variance,\nCOUNT(*) FILTER (WHERE ABS(variance)>0) as lines_with_variance
    PG-->>OpsSvc: {total_variance: 7, lines_with_variance: 2, total_value: $340}
    OpsSvc-->>APIGW: 200 variance report
    APIGW-->>Supervisor: Show variance report

    Supervisor->>APIGW: POST /api/v1/cycle-counts/{id}/approve\n{approval_note: "Recount confirmed, adjust"}
    APIGW->>OpsSvc: Approve and post adjustment

    OpsSvc->>PG: BEGIN TRANSACTION
    OpsSvc->>PG: UPDATE cycle_counts SET status=APPROVED, approved_by=?, approved_at=NOW()
    OpsSvc->>InvSvc: POST /internal/adjustments\n{lines: [{sku_code, bin_code, delta_qty, reason: CYCLE_COUNT}]}
    InvSvc->>PG: INSERT INTO inventory_ledger\n{type: CYCLE_COUNT_ADJ, qty_delta: -3}
    InvSvc->>PG: UPDATE inventory_balances SET on_hand = on_hand + delta_qty
    InvSvc->>Outbox: INSERT INTO outbox\n{event: adjustment-posted, count_id, adjustments[]}
    InvSvc->>PG: COMMIT
    InvSvc-->>OpsSvc: 200 adjustments posted
    OpsSvc->>Outbox: INSERT INTO outbox\n{event: cycle-count-adjusted, count_id}
    OpsSvc->>PG: COMMIT outer transaction
    OpsSvc-->>APIGW: 200 {count_id, adjusted_lines: 2, total_delta: -3}
    APIGW-->>Supervisor: Adjustment confirmed

    Outbox->>Kafka: Relay cycle-count-adjusted + adjustment-posted events
    note over Kafka: Reporting service consumes for KPI updates\nInventory cache invalidated by adjustment-posted event
