# Cloud Architecture

## Runtime Topology
- API tier (receiving/picking/packing/shipping command services).
- Worker tier (allocation, wave planner, reconciliation, outbox relay).
- Data tier (OLTP primary + read replicas + object archive).
- Integration tier (carrier adapters, OMS connectors, notification services).

## Availability and Scale Strategy
- Multi-AZ deployment for API and database.
- Autoscaling on queue depth, request rate, and p95 latency.
- Horizontal partitioning by warehouse region to contain blast radius.

## Resilience Patterns
- Outbox pattern for guaranteed event publication.
- Circuit breakers and fallback routing for carrier APIs.
- Dead-letter queues per integration with replay tooling.
- Backpressure gate on wave release when downstream dependency health degrades.

## Security and Compliance
- Private service networking; internet ingress only via WAF/API gateway.
- mTLS service-to-service authentication.
- KMS-managed encryption keys with periodic rotation.
- Immutable audit logs exported to long-retention storage.

## Disaster Recovery
- Cross-region backup replication every 5 minutes.
- Quarterly restore drills for inventory and shipment datasets.
- Defined RPO/RTO targets: 5 min / 30 min.

## Capacity Planning Inputs
- Peak orders/hour, scans/minute, waves/hour by warehouse.
- Average and p99 event payload size.
- Carrier API throughput limits and timeout profile.
