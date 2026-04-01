# System Context Diagram — Resource Lifecycle Management Platform

## Purpose

This document describes the Resource Lifecycle Management Platform (RLMP) in the context of its
external environment. It defines the system boundary, identifies all external actors and systems,
and describes the nature of each integration.

---

## C4 Level 1 — System Context Diagram

```mermaid
C4Context
    title System Context — Resource Lifecycle Management Platform

    Person(requestor, "Requestor", "Customer who reserves and uses physical or logical resources")
    Person(custodian, "Custodian", "Field staff handling physical checkout and check-in with barcode scanning")
    Person(resMgr, "Resource Manager", "Operator managing catalog, scheduling, and incident response")
    Person(finMgr, "Finance Manager", "Approves settlements and manages deposit reconciliation")
    Person(opsAdmin, "Operations Admin", "Configures policies, SLA profiles, resource types")
    Person(compliance, "Compliance Officer", "Audits lifecycle events and incident reports")

    System(rlmp, "Resource Lifecycle Management Platform", "Manages resource catalog, reservations, checkout/check-in, maintenance, incidents, settlements, and SLA tracking")

    System_Ext(iam, "IAM / SSO", "Issues and validates JWTs. Provides RBAC roles and tenant context for all authenticated requests.")
    System_Ext(pay, "Payment Gateway", "Processes deposit holds, charge captures, and refund disbursements. Supports idempotent requests via idempotency keys.")
    System_Ext(notify, "Notification Service (SMS/Email)", "Delivers reservation confirmations, overdue reminders, incident alerts, and settlement notifications to customers and operators.")
    System_Ext(erp, "ERP / SAP", "Receives asset register updates (resource catalog events) and financial postings (settlement charges and refunds) for accounting.")
    System_Ext(siem, "SIEM", "Receives structured audit-log events for security monitoring, anomaly detection, and compliance reporting.")
    System_Ext(scanner, "Barcode / QR Scanner", "Physical device or mobile SDK used to identify ResourceUnits at checkout and check-in. Communicates via REST API or BLE bridge.")

    Rel(requestor, rlmp, "Creates reservations, views availability, checks settlement status", "HTTPS/REST")
    Rel(custodian, rlmp, "Scans barcodes, completes checkouts and check-ins, files condition reports", "HTTPS/REST + mobile app")
    Rel(resMgr, rlmp, "Manages catalog, schedules maintenance, handles incidents", "HTTPS/REST + operator portal")
    Rel(finMgr, rlmp, "Reviews and approves settlements", "HTTPS/REST + finance portal")
    Rel(opsAdmin, rlmp, "Configures policies, SLA profiles, resource types", "HTTPS/REST + admin portal")
    Rel(compliance, rlmp, "Queries audit logs and incident reports", "HTTPS/REST + compliance portal")

    Rel(rlmp, iam, "Validates JWT on every request; fetches user roles and tenant context", "HTTPS/REST")
    Rel(rlmp, pay, "Initiates deposit holds at checkout; captures or releases on settlement approval", "HTTPS/REST + idempotency keys")
    Rel(rlmp, notify, "Publishes notification events via Kafka; Notification Service delivers to end users", "Kafka events")
    Rel(rlmp, erp, "Publishes ResourceCataloged / ChargeSettled events; ERP consumes for asset register and GL posting", "Kafka events")
    Rel(rlmp, siem, "Streams structured audit events: state transitions, policy decisions, security-sensitive operations", "Kafka → SIEM connector")
    Rel(scanner, rlmp, "Submits barcode scan results during checkout and check-in workflows", "HTTPS/REST")
```

---

## External System Profiles

### IAM / SSO

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Central identity provider for all RLMP actors |
| **Protocol** | OAuth 2.0 / OpenID Connect; JWT tokens (RS256) |
| **Integration Point** | API Gateway validates Bearer token on every inbound request |
| **Data Exchanged** | Access token, user_id, tenant_id, roles[] |
| **Failure Mode** | Hard dependency — all requests rejected if IAM is unreachable |
| **SLA Requirement** | ≥ 99.99% availability; token validation must complete < 20 ms (local JWKS cache) |

### Payment Gateway

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Authorise and capture deposits; disburse refunds on settlement |
| **Protocol** | HTTPS REST with HMAC-signed requests; idempotency key header |
| **Integration Point** | Checkout Service calls `/holds`, `/captures`, `/refunds` |
| **Data Exchanged** | payment_method_id, amount, currency, idempotency_key, hold_reference |
| **Failure Mode** | Soft dependency — deposit hold failure blocks checkout; retry with exponential backoff up to 3 attempts |
| **SLA Requirement** | p95 hold initiation ≤ 2 s; settlement disbursement ≤ 30 s |

### Notification Service (SMS/Email)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Deliver transactional notifications to customers and operators |
| **Protocol** | Kafka consumer on `notifications.outbound` topic |
| **Notification Types** | Reservation confirmed, Reservation cancelled, Checkout completed, Overdue reminder (1 h/4 h/24 h), Incident created, Settlement approved |
| **Failure Mode** | Async — RLMP fires-and-forgets via Kafka; retry handled by Notification Service |
| **Data Exchanged** | notification_type, recipient, template_id, template_vars, idempotency_key |

### ERP / SAP

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Asset register (resource catalog) and financial accounting (settlements) |
| **Protocol** | Kafka consumer on `erp.sync` topic; SAP IDoc adapter on receiving end |
| **Data Exchanged** | ResourceCataloged (asset creation), ChargeSettled (GL posting), DepositReleased (refund posting) |
| **Failure Mode** | Async — RLMP publishes events; ERP lag is acceptable up to 15 min |
| **Reconciliation** | Nightly reconciliation job cross-checks RLMP settlement totals vs. SAP posting totals |

### SIEM

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Security event monitoring, anomaly detection, compliance audit trail |
| **Protocol** | Kafka connector → SIEM ingest pipeline (Splunk / Elastic SIEM) |
| **Events Forwarded** | All state-transition events, policy-evaluation decisions, failed auth attempts, override actions |
| **Data Classification** | Audit-grade; records must be tamper-evident, retained for ≥ 7 years |
| **Latency SLO** | Audit events delivered to SIEM within 10 s of origination |

### Barcode / QR Scanner

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Identify physical ResourceUnits by their barcode or QR code during checkout and check-in |
| **Protocol** | REST POST to `/checkouts` or `/check-ins` with scanned_barcode field; mobile SDK for BLE scanners |
| **Offline Mode** | Custodian mobile app queues scans locally; syncs on reconnection |
| **Validation** | Barcode validated against resource_units.barcode_id with exact match; returns resource_unit_id |

---

## Data Flow Summary

```mermaid
flowchart LR
    Requestor -->|HTTPS| RLMP
    Custodian -->|HTTPS + BLE| RLMP
    Scanner -->|REST| RLMP
    RLMP -->|JWT validate| IAM
    RLMP -->|Deposit hold / release| PayGW[Payment Gateway]
    RLMP -->|Kafka events| NotifySvc[Notification Service]
    RLMP -->|Kafka events| ERP
    RLMP -->|Kafka events| SIEM
```

---

## Security Boundary

All inbound traffic passes through the API Gateway, which enforces:
1. **TLS 1.3** termination
2. **JWT validation** (RS256 signature + expiry check via local JWKS cache)
3. **Tenant isolation** — `tenant_id` extracted from JWT claims and injected into all downstream service calls
4. **Rate limiting** — 1,000 rps per tenant; 100 rps per individual user
5. **WAF rules** — OWASP Top 10 rule set applied at edge
