# Data Flow Diagrams

## Primary Flows
1. Read path: search request -> availability read model -> response.
2. Command path: reservation command -> transactional write -> outbox -> event bus.
3. Fulfillment path: operational event intake -> lifecycle store -> analytics sink.
4. Settlement path: usage events + policy inputs -> ledger posting -> reconciliation queue.

## Data Stores
- OLTP store for domain transactions
- Event store / audit log
- Read-model store for low-latency query
- Warehouse export for reporting
