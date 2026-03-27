# Architecture Diagram

## Logical Components
- API Gateway / BFF
- Catalog & Availability Service
- Reservation Service
- Fulfillment Service
- Settlement Service
- Incident & Dispute Service
- Policy Engine
- Event Bus + Outbox Relay
- Read Models / Analytics Sink

## Architectural Style
- Command side uses transactional services with outbox events.
- Query side uses denormalized read models for low-latency lookups.
- Cross-service workflows use saga orchestration with compensating actions.

## Sector Adaptation
Domain adapters provide sector-specific policy modules without changing core lifecycle contracts.
