# System Sequence Diagrams

## Overview
Black-box system sequence diagrams showing interactions between actors and the platform for primary use cases.

---

## Tenant Applies for a Unit

```mermaid
sequenceDiagram
    actor Tenant
    participant Platform as House Rental Platform
    actor Owner

    Tenant->>Platform: GET /units?available=true
    Platform-->>Tenant: List of available units

    Tenant->>Platform: GET /units/{unitId}
    Platform-->>Tenant: Unit details, photos, policies

    Tenant->>Platform: POST /applications { unitId, documents }
    Platform-->>Tenant: 201 Application created { applicationId, status: PENDING }
    Platform--)Owner: Notification: new application received

    Owner->>Platform: GET /applications/{applicationId}
    Platform-->>Owner: Application details and documents

    Owner->>Platform: PUT /applications/{applicationId} { status: APPROVED }
    Platform-->>Owner: 200 Application approved
    Platform--)Tenant: Notification: application approved
```

---

## Lease Creation and Signing

```mermaid
sequenceDiagram
    actor Owner
    participant Platform as House Rental Platform
    participant ESign as E-Signature Provider
    actor Tenant

    Owner->>Platform: POST /leases { applicationId, terms, startDate, endDate, rent }
    Platform-->>Owner: 201 Lease created { leaseId, status: DRAFT }

    Owner->>Platform: POST /leases/{leaseId}/send-for-signature
    Platform->>ESign: Send lease document to tenant
    ESign-->>Platform: Signature request ID
    Platform-->>Owner: 200 Lease sent { status: PENDING_TENANT_SIGNATURE }
    Platform--)Tenant: Email: Sign your lease

    Tenant->>ESign: Review and sign document
    ESign->>Platform: Webhook: tenant signed { leaseId, timestamp, ip }
    Platform-->>Platform: Update lease status
    Platform--)Owner: Notification: Tenant signed, please countersign

    Owner->>Platform: POST /leases/{leaseId}/countersign
    Platform->>ESign: Record owner signature
    ESign-->>Platform: Final signed document URL
    Platform-->>Owner: 200 Lease fully signed
    Platform-->>Platform: Generate rent schedule; set unit OCCUPIED
    Platform--)Tenant: Email: Signed lease PDF attached
```

---

## Rent Invoice and Payment

```mermaid
sequenceDiagram
    participant Scheduler as Billing Scheduler
    participant Platform as House Rental Platform
    actor Tenant
    participant PG as Payment Gateway
    actor Owner

    Scheduler->>Platform: Trigger billing cycle for lease
    Platform-->>Platform: Generate rent invoice
    Platform--)Tenant: Notification: Rent due - {amount} by {date}

    Tenant->>Platform: GET /invoices/current
    Platform-->>Tenant: Invoice details { amount, dueDate, breakdown }

    Tenant->>Platform: POST /invoices/{invoiceId}/pay { paymentMethod }
    Platform->>PG: Initiate payment { amount, method }
    PG-->>Platform: Payment URL / session

    Platform-->>Tenant: 200 { paymentUrl }
    Tenant->>PG: Complete payment

    PG->>Platform: Webhook: payment confirmed { gatewayRef, amount }
    Platform-->>Platform: Mark invoice PAID; update ledger
    Platform--)Tenant: Email: Payment receipt
    Platform--)Owner: Notification: Rent received
```

---

## Maintenance Request Lifecycle

```mermaid
sequenceDiagram
    actor Tenant
    participant Platform as House Rental Platform
    actor Owner
    actor MaintStaff as Maintenance Staff

    Tenant->>Platform: POST /maintenance-requests { unitId, title, description, priority, photos }
    Platform-->>Tenant: 201 { requestId, status: OPEN }
    Platform--)Owner: Notification: New maintenance request

    Owner->>Platform: GET /maintenance-requests/{requestId}
    Platform-->>Owner: Request details

    Owner->>Platform: PUT /maintenance-requests/{requestId}/assign { staffUserId }
    Platform-->>Owner: 200 Request assigned
    Platform--)MaintStaff: Notification: New task assigned

    MaintStaff->>Platform: PUT /maintenance-requests/{requestId}/status { status: IN_PROGRESS }
    Platform-->>MaintStaff: 200 Status updated
    Platform--)Tenant: Notification: Request in progress

    MaintStaff->>Platform: PUT /maintenance-requests/{requestId}/complete { notes, photos, materials }
    Platform-->>MaintStaff: 200 Marked completed
    Platform--)Owner: Notification: Work completed - review needed

    Owner->>Platform: PUT /maintenance-requests/{requestId}/approve
    Platform-->>Owner: 200 Request closed
    Platform--)Tenant: Notification: Request resolved - please rate

    Tenant->>Platform: POST /maintenance-requests/{requestId}/rating { rating, comment }
    Platform-->>Tenant: 200 Rating submitted
```

---

## Deposit Refund on Lease Termination

```mermaid
sequenceDiagram
    actor Tenant
    participant Platform as House Rental Platform
    actor Owner

    Tenant->>Platform: POST /leases/{leaseId}/termination { terminationDate, reason }
    Platform-->>Tenant: 202 Termination notice recorded
    Platform--)Owner: Notification: Termination notice received

    Platform-->>Platform: Schedule move-out inspection

    Owner->>Platform: POST /inspections { leaseId, type: MOVE_OUT, scheduledDate }
    Platform-->>Owner: 201 Inspection scheduled

    Owner->>Platform: PUT /inspections/{inspectionId}/conduct { findings, photos }
    Platform-->>Owner: 200 Inspection recorded

    Owner->>Platform: POST /leases/{leaseId}/deposit/deductions { deductions[] }
    Platform-->>Owner: 200 Deductions recorded
    Platform--)Tenant: Notification: Deposit deduction details

    Tenant->>Platform: POST /leases/{leaseId}/deposit/deductions/accept
    Platform-->>Tenant: 200 Accepted

    Owner->>Platform: POST /leases/{leaseId}/deposit/refund
    Platform-->>Owner: 200 Refund initiated
    Platform--)Tenant: Notification: Deposit refund processed
```
