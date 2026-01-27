# Data Flow Diagram - Slot Booking System

> **Platform Independence**: Shows how data moves through the system regardless of technology choices.

---

## Overview

Data Flow Diagrams (DFDs) show the flow of data through the system, from external entities through processes to data stores.

---

## Level 0: Context Diagram

```mermaid
flowchart LR
    U((User)) -->|Registration Data,<br/>Booking Requests| SBS[Slot Booking<br/>System]
    SBS -->|Confirmations,<br/>Notifications| U
    
    P((Provider)) -->|Resource Data,<br/>Availability| SBS
    SBS -->|Booking Alerts,<br/>Earnings Reports| P
    
    A((Admin)) -->|Configuration,<br/>Approvals| SBS
    SBS -->|Analytics,<br/>Alerts| A
    
    PG[Payment<br/>Gateway] <-->|Payment Data,<br/>Refunds| SBS
    
    NS[Notification<br/>Services] <--|Email, SMS,<br/>Push Data| SBS
```

---

## Level 1: Main Processes

```mermaid
flowchart TB
    subgraph External Entities
        USER((User))
        PROV((Provider))
        ADMIN((Admin))
    end
    
    subgraph "External Systems"
        PAY_EXT[Payment Gateway]
        NOTIF_EXT[Notification Services]
        MAP_EXT[Maps Service]
        STORE_EXT[File Storage]
    end
    
    subgraph "Processes"
        P1[1.0<br/>User<br/>Management]
        P2[2.0<br/>Resource<br/>Management]
        P3[3.0<br/>Slot<br/>Management]
        P4[4.0<br/>Booking<br/>Management]
        P5[5.0<br/>Payment<br/>Processing]
        P6[6.0<br/>Notification<br/>Dispatch]
        P7[7.0<br/>Review<br/>Management]
        P8[8.0<br/>Reporting &<br/>Analytics]
        P9[9.0<br/>Audit &<br/>Compliance]
    end
    
    subgraph "Data Stores"
        D1[(Users)]
        D2[(Resources)]
        D3[(Slots)]
        D4[(Bookings)]
        D5[(Payments)]
        D6[(Reviews)]
        D7[(Notifications)]
        D8[(Audit Logs)]
        D9[(Idempotency Keys)]
        D10[(Notification Preferences)]
    end
    
    %% User Management
    USER -->|Registration Data| P1
    P1 -->|User Record| D1
    P1 -->|Auth Response| USER
    
    %% Resource Management
    PROV -->|Resource Info| P2
    P2 -->|Resource Record| D2
    P2 <-->|Images| STORE_EXT
    P2 <-->|Location Data| MAP_EXT
    
    %% Slot Management
    P2 -->|Availability Rules| P3
    P3 -->|Slot Records| D3
    D3 -->|Available Slots| P4
    
    %% Booking Management
    USER -->|Booking Request| P4
    D1 -->|User Data| P4
    D2 -->|Resource Data| P4
    P4 -->|Booking Record| D4
    P4 -->|Idempotency Key| D9
    P4 -->|Payment Request| P5
    
    %% Payment Processing
    P5 <-->|Transaction| PAY_EXT
    P5 -->|Payment Record| D5
    P5 -->|Idempotency Key| D9
    P5 -->|Confirmation| P4
    
    %% Notifications
    P4 -->|Booking Event| P6
    P6 -->|Notification Record| D7
    D10 -->|User Preferences| P6
    P6 -->|Notification| NOTIF_EXT
    
    %% Reviews
    USER -->|Review Data| P7
    P7 -->|Review Record| D6
    D6 -->|Stats| P2
    
    %% Reporting
    D4 -->|Booking Data| P8
    D5 -->|Payment Data| P8
    P8 -->|Reports| ADMIN
    P8 -->|Reports| PROV

    %% Audit & Compliance
    P1 -->|Audit Events| P9
    P2 -->|Audit Events| P9
    P3 -->|Audit Events| P9
    P4 -->|Audit Events| P9
    P5 -->|Audit Events| P9
    P9 -->|Audit Record| D8
```

---

## Level 2: Booking Management Process (4.0)

```mermaid
flowchart TB
    subgraph "External"
        USER((User))
    end
    
    subgraph "From Other Processes"
        FROM_3[From 3.0: Slot Data]
        FROM_1[From 1.0: User Data]
        FROM_2[From 2.0: Resource Data]
    end
    
    subgraph "Process 4.0: Booking Management"
        P4_1[4.1<br/>Search<br/>Slots]
        P4_2[4.2<br/>Reserve<br/>Slot]
        P4_3[4.3<br/>Confirm<br/>Booking]
        P4_4[4.4<br/>Cancel<br/>Booking]
        P4_5[4.5<br/>Reschedule<br/>Booking]
        P4_6[4.6<br/>Manage<br/>Waitlist]
    end
    
    subgraph "Data Stores"
        D4[(Bookings)]
        D3[(Slots)]
        D_WAIT[(Waitlist)]
    end
    
    subgraph "To Other Processes"
        TO_5[To 5.0: Payment]
        TO_6[To 6.0: Notifications]
    end
    
    USER -->|Search Criteria| P4_1
    FROM_3 -->|Available Slots| P4_1
    FROM_2 -->|Resource Info| P4_1
    P4_1 -->|Search Results| USER
    
    USER -->|Slot Selection| P4_2
    FROM_1 -->|User Info| P4_2
    P4_2 -->|Temp Reservation| D3
    P4_2 -->|Summary| USER
    
    USER -->|Confirmation| P4_3
    D3 -->|Reservation Data| P4_3
    P4_3 -->|Payment Request| TO_5
    TO_5 -->|Payment Result| P4_3
    P4_3 -->|Booking Record| D4
    P4_3 -->|Booking Event| TO_6
    P4_3 -->|Confirmation| USER
    
    USER -->|Cancel Request| P4_4
    D4 -->|Booking Data| P4_4
    P4_4 -->|Updated Status| D4
    P4_4 -->|Release Slot| D3
    P4_4 -->|Refund Request| TO_5
    P4_4 -->|Cancel Event| TO_6
    P4_4 -->|Slot Available| P4_6
    
    USER -->|Reschedule Request| P4_5
    D4 -->|Current Booking| P4_5
    FROM_3 -->|Alternative Slots| P4_5
    P4_5 -->|Updated Booking| D4
    P4_5 -->|Reschedule Event| TO_6
    
    USER -->|Join Waitlist| P4_6
    P4_6 -->|Waitlist Entry| D_WAIT
    D_WAIT -->|Waitlist User| P4_6
    P4_6 -->|Availability Alert| TO_6
```

---

## Level 2: Payment Processing (5.0)

```mermaid
flowchart TB
    subgraph "From Other Processes"
        FROM_4[From 4.0: Payment Request]
    end
    
    subgraph "Process 5.0: Payment Processing"
        P5_1[5.1<br/>Calculate<br/>Amount]
        P5_2[5.2<br/>Apply<br/>Promo]
        P5_3[5.3<br/>Process<br/>Payment]
        P5_4[5.4<br/>Process<br/>Refund]
        P5_5[5.5<br/>Generate<br/>Invoice]
        P5_6[5.6<br/>Calculate<br/>Payout]
    end
    
    subgraph "Data Stores"
        D5[(Payments)]
        D_PROMO[(Promo Codes)]
        D_INVOICE[(Invoices)]
        D_PAYOUT[(Payouts)]
    end
    
    subgraph "External"
        PAY_GW[Payment Gateway]
        PROV((Provider))
    end
    
    subgraph "To Other Processes"
        TO_4[To 4.0: Result]
        TO_6[To 6.0: Notifications]
    end
    
    FROM_4 -->|Booking Details| P5_1
    P5_1 -->|Base Amount| P5_2
    D_PROMO -->|Promo Rules| P5_2
    P5_2 -->|Final Amount| P5_3
    
    P5_3 <-->|Transaction| PAY_GW
    P5_3 -->|Payment Record| D5
    P5_3 -->|Result| TO_4
    P5_3 -->|Success| P5_5
    
    FROM_4 -->|Refund Request| P5_4
    D5 -->|Original Payment| P5_4
    P5_4 <-->|Refund| PAY_GW
    P5_4 -->|Refund Record| D5
    P5_4 -->|Refund Event| TO_6
    
    P5_5 -->|Invoice| D_INVOICE
    P5_5 -->|Invoice Copy| TO_6
    
    D5 -->|Settlement Data| P5_6
    P5_6 -->|Payout Record| D_PAYOUT
    P5_6 -->|Payout Info| PROV
```

---

## Data Dictionary

### Data Flows

| Data Flow | Description | Contents |
|-----------|-------------|----------|
| Registration Data | User signup info | email, password, name, phone |
| Booking Request | Slot reservation request | userId, slotIds, notes |
| Resource Info | Resource details | name, description, location, pricing |
| Payment Request | Payment initiation | amount, method, bookingId |
| Booking Event | Booking lifecycle event | type, bookingId, timestamp |

### Data Stores

| Store | Description | Key Fields |
|-------|-------------|------------|
| D1: Users | User accounts | userId, email, role, profile |
| D2: Resources | Bookable resources | resourceId, providerId, details |
| D3: Slots | Time slots | slotId, resourceId, startTime, status |
| D4: Bookings | Reservations | bookingId, userId, slotId, status |
| D5: Payments | Transactions | paymentId, amount, status |
| D6: Reviews | User feedback | reviewId, rating, comment |
| D7: Notifications | Sent notifications | notifId, userId, channel |
| D8: Audit Logs | Compliance records | actorId, action, timestamp |
| D9: Idempotency Keys | Request deduplication | key, status, response |
| D10: Notification Preferences | User settings | userId, channels, quiet_hours |

---

## Data Flow Summary

```mermaid
graph LR
    subgraph "Input"
        I1[User Actions]
        I2[Provider Actions]
        I3[Admin Actions]
        I4[External Webhooks]
    end
    
    subgraph "Processing"
        P1[Validate]
        P2[Transform]
        P3[Business Logic]
        P4[Persist]
    end
    
    subgraph "Output"
        O1[UI Responses]
        O2[Notifications]
        O3[Reports]
        O4[External Calls]
    end
    
    I1 --> P1
    I2 --> P1
    I3 --> P1
    I4 --> P1
    
    P1 --> P2
    P2 --> P3
    P3 --> P4
    
    P4 --> O1
    P3 --> O2
    P4 --> O3
    P3 --> O4
```
