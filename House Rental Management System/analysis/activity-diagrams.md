# Activity Diagrams

## Overview
Activity diagrams showing the business process flows for key operations in the house rental management system.

---

## Tenant Application & Onboarding Flow

```mermaid
flowchart TD
    A([Start]) --> B[Tenant Browses Listings]
    B --> C[Tenant Selects a Unit]
    C --> D{Unit Available?}
    D -- No --> B
    D -- Yes --> E[Tenant Fills Application Form]
    E --> F[Tenant Uploads Documents]
    F --> G[Tenant Submits Application]
    G --> H[System Validates Submission]
    H --> I{Documents Valid?}
    I -- No --> F
    I -- Yes --> J[System Creates Application - PENDING]
    J --> K[Owner Notified]
    K --> L{Owner Reviews}
    L -- Rejected --> M[Tenant Notified of Rejection]
    M --> N([End])
    L -- Approved --> O[Owner Creates Lease]
    O --> P[Lease Sent for Tenant Signature]
    P --> Q{Tenant Signs?}
    Q -- Declined --> R[Lease Status = DECLINED]
    R --> N
    Q -- Signed --> S[Owner Countersigns]
    S --> T[Signed PDF Generated & Stored]
    T --> U[Rent Schedule Created]
    U --> V[Unit Status = OCCUPIED]
    V --> W([End - Tenant Onboarded])
```

---

## Rent Payment Flow

```mermaid
flowchart TD
    A([Billing Cycle Date]) --> B[System Generates Rent Invoice]
    B --> C[Tenant Notified - Due Date]
    C --> D{Tenant Pays Before Due?}
    D -- Yes --> E[Tenant Selects Payment Method]
    E --> F[Payment Gateway Processes]
    F --> G{Payment Successful?}
    G -- No --> H[Tenant Notified - Retry]
    H --> E
    G -- Yes --> I[Invoice Marked PAID]
    I --> J[Receipt Generated & Emailed]
    J --> K[Owner Ledger Updated]
    K --> L([End])
    D -- No --> M{Grace Period Passed?}
    M -- No --> D
    M -- Yes --> N[Late Fee Applied]
    N --> O[Overdue Notification to Tenant]
    O --> P[Escalation Alert to Owner]
    P --> Q{Tenant Pays Now?}
    Q -- Yes --> E
    Q -- No --> R[Owner Takes Manual Action]
    R --> L
```

---

## Maintenance Request Flow

```mermaid
flowchart TD
    A([Tenant Submits Request]) --> B[System Creates Request - OPEN]
    B --> C[Owner Notified]
    C --> D{Emergency Priority?}
    D -- Yes --> E[SMS Alert Sent to Owner]
    D -- No --> F[In-App Notification Only]
    E --> G[Owner Reviews Request]
    F --> G
    G --> H[Owner Assigns to Maintenance Staff]
    H --> I[Staff Notified]
    I --> J{Staff Accepts?}
    J -- No --> K[Staff Declines with Reason]
    K --> G
    J -- Yes --> L[Status = ASSIGNED]
    L --> M[Staff Visits Property]
    M --> N[Status = IN_PROGRESS]
    N --> O[Staff Adds Notes, Photos, Materials]
    O --> P[Staff Marks COMPLETED]
    P --> Q[Owner Reviews Completion]
    Q --> R{Owner Approves?}
    R -- No --> S[Owner Reopens with Reason]
    S --> N
    R -- Yes --> T[Status = CLOSED]
    T --> U[Tenant Notified - Rate Request]
    U --> V[Owner Logs Maintenance Cost]
    V --> W([End])
```

---

## Lease Termination & Deposit Refund Flow

```mermaid
flowchart TD
    A([Termination Initiated]) --> B{Who Initiates?}
    B -- Owner --> C[Owner Issues Notice]
    B -- Tenant --> D[Tenant Issues Notice]
    C --> E[System Logs Termination Date]
    D --> E
    E --> F[Notice Period Enforced]
    F --> G{Early Termination?}
    G -- Yes --> H[Calculate Early Termination Fee]
    H --> I[Fee Added to Final Account]
    G -- No --> I
    I --> J[Schedule Move-out Inspection]
    J --> K[Inspection Conducted]
    K --> L[Owner Records Inspection Findings]
    L --> M{Damages Found?}
    M -- Yes --> N[Owner Itemises Deductions]
    N --> O[Tenant Notified of Deductions]
    O --> P{Tenant Disputes?}
    P -- Yes --> Q[Admin Mediates]
    Q --> R[Resolution Recorded]
    R --> S[Adjusted Deduction Finalised]
    P -- No --> S
    M -- No --> S
    S --> T[Deposit Refund Calculated]
    T --> U[Refund Processed to Tenant]
    U --> V[Lease Status = EXPIRED]
    V --> W[Unit Status = VACANT]
    W --> X([End])
```

---

## Bill Management Flow

```mermaid
flowchart TD
    A([Owner Receives Utility Bill]) --> B[Owner Creates Bill in Platform]
    B --> C[Owner Uploads Bill Scan]
    C --> D{Common Area Bill?}
    D -- Yes --> E[Owner Selects Split Method]
    E --> F[System Calculates Each Tenant Share]
    F --> G[Individual Bill Records Created]
    D -- No --> H[Bill Assigned to Single Unit]
    G --> I[Tenants Notified of New Bills]
    H --> I
    I --> J{Tenant Reviews Bill}
    J --> K{Dispute?}
    K -- Yes --> L[Tenant Submits Dispute]
    L --> M[Owner Notified]
    M --> N[Owner Reviews Dispute]
    N --> O{Valid Dispute?}
    O -- Yes --> P[Bill Adjusted]
    P --> Q[Tenant Notified of Adjustment]
    O -- No --> R[Dispute Rejected with Reason]
    R --> Q
    K -- No --> S[Tenant Pays Bill]
    Q --> S
    S --> T{Online or Offline?}
    T -- Online --> U[Payment Gateway Processes]
    U --> V[Payment Confirmed]
    T -- Offline --> W[Owner Records Offline Payment]
    W --> V
    V --> X[Bill Status = PAID]
    X --> Y([End])
```
