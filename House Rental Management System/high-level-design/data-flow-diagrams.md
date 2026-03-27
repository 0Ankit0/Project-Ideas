# Data Flow Diagrams

## Overview
Data flow diagrams (DFDs) showing how data moves through the house rental management system.

---

## Level 0 DFD – Context Diagram

```mermaid
graph LR
    Owner((Owner))
    Tenant((Tenant))
    MaintStaff((Maintenance Staff))
    Admin((Admin))
    PG((Payment Gateway))
    ESign((E-Signature Provider))

    HRMS[House Rental Management System]

    Owner -->|property data, lease terms, bill entries, assignments| HRMS
    HRMS -->|reports, notifications, signed leases, receipts| Owner

    Tenant -->|applications, payments, maintenance requests| HRMS
    HRMS -->|invoices, receipts, lease docs, request updates| Tenant

    MaintStaff -->|task updates, work notes, cost logs| HRMS
    HRMS -->|assigned tasks, property details| MaintStaff

    Admin -->|user actions, platform config| HRMS
    HRMS -->|audit logs, platform metrics, alerts| Admin

    PG -->|payment confirmations, webhooks| HRMS
    HRMS -->|payment initiation requests| PG

    ESign -->|signed documents| HRMS
    HRMS -->|lease documents for signing| ESign
```

---

## Level 1 DFD – Key Subsystems

```mermaid
graph TD
    subgraph Inputs
        OwnInput((Owner))
        TenInput((Tenant))
        MntInput((Staff))
        PGInput((Payment GW))
        ESignInput((E-Sign))
    end

    subgraph "Property & Unit Management"
        P1[Property Data Store]
        P2[Unit Data Store]
        ProcProp[Process: Manage Properties & Units]
    end

    subgraph "Application & Lease Management"
        P3[Application Data Store]
        P4[Lease Data Store]
        P5[Document Data Store]
        ProcApp[Process: Handle Applications]
        ProcLease[Process: Manage Leases]
    end

    subgraph "Rent & Payment Processing"
        P6[Invoice Data Store]
        P7[Payment Data Store]
        ProcRent[Process: Generate & Collect Rent]
    end

    subgraph "Bill Management"
        P8[Bill Data Store]
        ProcBill[Process: Manage Bills & Utilities]
    end

    subgraph "Maintenance Management"
        P9[Maintenance Data Store]
        ProcMaint[Process: Handle Maintenance]
    end

    subgraph "Notification Engine"
        ProcNotify[Process: Send Notifications]
    end

    OwnInput -->|property and unit data| ProcProp
    ProcProp --> P1
    ProcProp --> P2

    TenInput -->|application data| ProcApp
    ProcApp --> P3
    ProcApp --> P5
    ProcApp -->|approved application| ProcLease
    OwnInput -->|lease terms| ProcLease
    ProcLease --> P4
    ProcLease --> P5
    ProcLease -->|send for signature| ESignInput
    ESignInput -->|signed document| ProcLease

    P4 -->|active lease triggers| ProcRent
    TenInput -->|payment| ProcRent
    PGInput -->|webhook| ProcRent
    ProcRent --> P6
    ProcRent --> P7

    OwnInput -->|bill data| ProcBill
    TenInput -->|bill payment| ProcBill
    PGInput -->|webhook| ProcBill
    ProcBill --> P8

    TenInput -->|maintenance request| ProcMaint
    MntInput -->|task updates| ProcMaint
    OwnInput -->|assignments, approvals| ProcMaint
    ProcMaint --> P9

    ProcApp --> ProcNotify
    ProcLease --> ProcNotify
    ProcRent --> ProcNotify
    ProcBill --> ProcNotify
    ProcMaint --> ProcNotify
```

---

## Level 2 DFD – Rent Invoice Process

```mermaid
graph TD
    LeaseStore[(Lease Store)]
    InvoiceStore[(Invoice Store)]
    PaymentStore[(Payment Store)]
    TenantStore[(Tenant Store)]

    A[Billing Scheduler] -->|trigger billing cycle| B[Generate Invoice Process]
    LeaseStore -->|active lease details| B
    B -->|create invoice| InvoiceStore
    B -->|notify| C[Notification Process]
    C -->|send email/push| Tenant((Tenant))

    Tenant -->|pay invoice| D[Payment Process]
    InvoiceStore -->|invoice details| D
    D -->|initiate| E[Payment Gateway]
    E -->|webhook confirm| D
    D -->|update invoice PAID| InvoiceStore
    D -->|record payment| PaymentStore
    D -->|update ledger| TenantStore
    D -->|trigger| C
    C -->|send receipt| Tenant
    C -->|notify payment received| Owner((Owner))

    InvoiceStore -->|overdue check| F[Late Fee Process]
    F -->|apply late fee| InvoiceStore
    F -->|trigger| C
    C -->|overdue reminder| Tenant
    C -->|escalation alert| Owner
```

---

## Level 2 DFD – Maintenance Request Process

```mermaid
graph TD
    UnitStore[(Unit Store)]
    RequestStore[(Maintenance Store)]
    StaffStore[(Staff Store)]
    CostStore[(Cost Store)]

    Tenant((Tenant)) -->|submit request| A[Create Request Process]
    UnitStore -->|unit info| A
    A -->|create OPEN request| RequestStore
    A -->|notify| N[Notification Process]
    N -->|alert| Owner((Owner))

    Owner -->|assign staff| B[Assignment Process]
    StaffStore -->|available staff| B
    B -->|update request ASSIGNED| RequestStore
    B -->|notify| N
    N -->|task notification| MaintStaff((Maintenance Staff))

    MaintStaff -->|status updates, notes, photos| C[Update Request Process]
    C -->|update IN_PROGRESS / COMPLETED| RequestStore
    C -->|notify| N
    N -->|progress update| Tenant
    N -->|completion review request| Owner

    Owner -->|approve or reopen| D[Closure Process]
    D -->|set CLOSED| RequestStore
    D -->|notify| N
    N -->|request closed| Tenant

    Owner -->|log cost| E[Cost Logging Process]
    E -->|record cost entry| CostStore
    CostStore -->|link to request| RequestStore
```
