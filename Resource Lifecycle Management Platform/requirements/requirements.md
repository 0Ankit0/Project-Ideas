# Requirements — Resource Lifecycle Management Platform

## 1. Introduction

This document captures all functional and non-functional requirements for the Resource Lifecycle
Management Platform (RLMP). Requirements are traced to business rules (BR-xx) and user stories
(US-xx) where applicable.

---

## 2. Functional Requirements

### 2.1 Resource Catalog Management

| ID | Requirement | Priority | Trace |
|----|-------------|----------|-------|
| FR-01 | The system shall allow operators to define ResourceTypes with a configurable JSON attribute schema, unit of measure, and maintenance interval. | Must | — |
| FR-02 | The system shall allow operators to catalog individual ResourceUnits under a ResourceType, capturing serial number, barcode/QR identifier, acquisition date, and location. | Must | — |
| FR-03 | The system shall support bulk import of resource units via CSV upload with field-validation error reporting per row. | Should | — |
| FR-04 | The system shall maintain a full audit trail of catalog changes (create, update, retire) with operator identity and timestamp. | Must | — |
| FR-05 | The system shall expose a real-time availability calendar per resource, showing AVAILABLE / RESERVED / ALLOCATED / MAINTENANCE / RETIRED windows. | Must | — |

### 2.2 Reservation Management

| ID | Requirement | Priority | Trace |
|----|-------------|----------|-------|
| FR-06 | The system shall allow authenticated customers to create reservations specifying resource type, quantity, start time, and end time. | Must | US-01 |
| FR-07 | The system shall prevent double-reservation via optimistic locking with a row-version check on Resource.availability before committing. | Must | BR-01 |
| FR-08 | The system shall enforce a minimum lead time: 30 minutes for standard resources, 24 hours for premium resources. | Must | BR-02 |
| FR-09 | The system shall notify the customer via email and SMS within 60 seconds of reservation confirmation. | Must | US-01 |
| FR-10 | The system shall allow operators to cancel any reservation, automatically notifying affected customers and releasing availability windows. | Must | US-05 |
| FR-11 | The system shall allow customers to cancel their own reservation up to the lead-time cutoff with no penalty; cancellations within the lead-time window incur a configurable fee. | Should | US-02 |
| FR-12 | The system shall support reservation hold periods: unconfirmed reservations expire after a configurable TTL (default 15 min) and revert to AVAILABLE. | Must | — |

### 2.3 Allocation and Assignment

| ID | Requirement | Priority | Trace |
|----|-------------|----------|-------|
| FR-13 | The system shall create an Allocation record linking a confirmed Reservation to a specific ResourceUnit upon operator assignment. | Must | US-03 |
| FR-14 | The system shall validate that the selected ResourceUnit is in AVAILABLE or RESERVED state before completing allocation. | Must | BR-01 |
| FR-15 | The system shall support multi-resource allocations where a single reservation maps to multiple physical units across locations. | Should | — |

### 2.4 Checkout and Check-In

| ID | Requirement | Priority | Trace |
|----|-------------|----------|-------|
| FR-16 | The system shall initiate a deposit hold against the customer's payment method before completing checkout; checkout is blocked if the hold fails. | Must | BR-03, US-03 |
| FR-17 | The system shall record a CheckoutRecord with custodian identity, checkout timestamp, pre-condition notes, and photo references. | Must | US-06 |
| FR-18 | The system shall allow barcode/QR scanning to identify the ResourceUnit during checkout and check-in. | Must | US-06 |
| FR-19 | The system shall enforce a mandatory ConditionReport on check-in; if not filed within 2 hours, the system auto-creates a P2 Incident. | Must | BR-04 |
| FR-20 | The system shall record a CheckInRecord with custodian identity, return timestamp, post-condition notes, and photo references. | Must | US-07 |

### 2.5 Condition Assessment and Reporting

| ID | Requirement | Priority | Trace |
|----|-------------|----------|-------|
| FR-21 | The system shall allow custodians to file ConditionReports with damage severity (NONE / MINOR / MODERATE / SEVERE), free-text description, and up to 10 photo attachments. | Must | US-07 |
| FR-22 | The system shall automatically create an Incident when a ConditionReport records damage severity of MODERATE or higher. | Must | BR-06 |
| FR-23 | The system shall place a hold on deposit release when a damage Incident is created; release is blocked until settlement approval. | Must | BR-06 |

### 2.6 Maintenance Management

| ID | Requirement | Priority | Trace |
|----|-------------|----------|-------|
| FR-24 | The system shall allow operators to schedule MaintenanceJobs with type (PREVENTIVE / CORRECTIVE / EMERGENCY), assigned technician, and estimated duration. | Must | US-04 |
| FR-25 | The system shall block all new reservations for a resource when an active MaintenanceJob exists for that resource. | Must | BR-05 |
| FR-26 | The system shall auto-cancel all future reservations conflicting with a newly created maintenance window and notify affected customers. | Must | BR-05 |
| FR-27 | The system shall track a MaintenanceSchedule (calendar triggers) per ResourceType with configurable intervals. | Should | — |

### 2.7 Incident Management

| ID | Requirement | Priority | Trace |
|----|-------------|----------|-------|
| FR-28 | The system shall allow custodians and operators to report Incidents with type (DAMAGE / LOSS / THEFT / OVERDUE), severity, description, and supporting evidence. | Must | US-08 |
| FR-29 | The system shall implement the overdue escalation ladder: 1 h → automated reminder; 4 h → manager escalation; 24 h → Incident report + legal hold. | Must | BR-08 |
| FR-30 | The system shall link Incidents to the originating CheckoutRecord, ConditionReport, and ResourceUnit. | Must | — |

### 2.8 Settlement and Finance

| ID | Requirement | Priority | Trace |
|----|-------------|----------|-------|
| FR-31 | The system shall calculate settlement amounts as: refund = deposit − (assessed_damage_charge + late_fees). | Must | BR-07 |
| FR-32 | The system shall require Finance Manager approval before executing deposit disbursements or charge captures. | Must | US-09 |
| FR-33 | The system shall post settlement outcomes to the ERP/SAP ledger via integration within 5 minutes of approval. | Must | — |
| FR-34 | The system shall provide a customer-facing settlement breakdown report with itemised charges. | Must | US-09 |

### 2.9 SLA Management

| ID | Requirement | Priority | Trace |
|----|-------------|----------|-------|
| FR-35 | The system shall allow operators to define SLAProfiles with availability windows (e.g., 99.5% monthly), breach thresholds, and credit values. | Must | US-10 |
| FR-36 | The system shall detect SLA breaches in real-time when a resource is unavailable beyond the SLA window. | Must | BR-09 |
| FR-37 | The system shall automatically issue SLA credits to the customer account upon breach detection without manual intervention. | Must | BR-09 |

### 2.10 Policy and Configuration

| ID | Requirement | Priority | Trace |
|----|-------------|----------|-------|
| FR-38 | The system shall support configurable Policies per ResourceType covering: lead time, deposit amount, late-fee rate, damage rate card, and cancellation penalties. | Must | — |
| FR-39 | The system shall evaluate all applicable policies via the OPA (Open Policy Agent) engine at reservation and checkout time. | Must | — |

### 2.11 Multi-Location and Portals

| ID | Requirement | Priority | Trace |
|----|-------------|----------|-------|
| FR-40 | The system shall support multi-location inventory with location-scoped availability calendars and cross-location transfer workflows. | Should | — |
| FR-41 | The system shall provide an operator portal for resource management, reservation oversight, and incident handling. | Must | US-05 |
| FR-42 | The system shall provide a customer portal for self-service reservation, checkout status, and settlement history. | Must | US-01 |

---

## 3. Non-Functional Requirements

### 3.1 Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-01 | Reservation creation API (conflict check + write) | p95 ≤ 300 ms under 500 rps |
| NFR-02 | Availability calendar query | p95 ≤ 100 ms via Elasticsearch read path |
| NFR-03 | Checkout deposit hold initiation | p95 ≤ 2 s including payment gateway round-trip |
| NFR-04 | Event delivery from outbox to consumers | p99 ≤ 5 s end-to-end |
| NFR-05 | SLA breach detection latency | ≤ 60 s from breach event to credit issuance |

### 3.2 Availability and Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-06 | Platform API uptime SLA | ≥ 99.9% monthly |
| NFR-07 | Data durability (PostgreSQL + WAL shipping) | RPO ≤ 5 min, RTO ≤ 30 min |
| NFR-08 | Reservation service must be available during primary DB failover | Standby promotion ≤ 60 s |
| NFR-09 | Kafka consumer group must process the DLQ within 4 hours of incident | ≤ 4 h DLQ drain SLA |

### 3.3 Consistency and Correctness

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-10 | Reservation conflict detection must be linearisable | Optimistic locking + retry; zero double-bookings |
| NFR-11 | Financial transactions (deposit, charge, refund) must be idempotent | Idempotency keys enforced at gateway and service layers |
| NFR-12 | All domain events must be delivered at-least-once with deduplication at consumer | Outbox pattern + Kafka consumer idempotency |
| NFR-13 | Lifecycle state transitions must be atomic | DB transaction wrapping state write + outbox insert |

### 3.4 Security

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-14 | All API endpoints must require a valid JWT issued by the IAM/SSO service | 401 on missing/expired token |
| NFR-15 | Tenant isolation: every query must be scoped to the authenticated tenant_id | Row-level security on all tenant-owned tables |
| NFR-16 | PII fields (customer_name, contact_email) must be encrypted at rest (AES-256) | AWS KMS managed keys |
| NFR-17 | All state-changing operations must be logged to the SIEM within 10 s | Audit events forwarded via Kafka → SIEM topic |
| NFR-18 | Deposit amounts and settlement figures are financial data and must be stored with DECIMAL(18,4) precision | No floating-point arithmetic on monetary values |

### 3.5 Scalability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-19 | Core API pods must auto-scale from 3 to 20 replicas based on CPU utilisation | HPA: target 70% CPU |
| NFR-20 | Kafka partitioning must support horizontal consumer scaling to 20 workers per topic | Min 20 partitions per high-throughput topic |
| NFR-21 | Elasticsearch indices must support sharding for ≥ 10 M resource-availability records | Index lifecycle management with rollover at 50 GB |

### 3.6 Observability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-22 | All services must emit structured JSON logs with trace_id, span_id, and tenant_id | OpenTelemetry SDK integration |
| NFR-23 | Metrics must be scraped by Prometheus and visualised in Grafana | Dashboards per service with SLI/SLO indicators |
| NFR-24 | Distributed tracing must cover the end-to-end reservation → checkout flow | Jaeger with sampling rate ≥ 1% |
