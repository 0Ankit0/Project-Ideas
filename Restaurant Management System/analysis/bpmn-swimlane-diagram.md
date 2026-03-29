# BPMN Swimlane Diagram - Restaurant Management System

```mermaid
flowchart LR
    subgraph lane1[Guest]
        g1[Reserve / arrive]
        g2[Review status]
        g3[Receive food and pay]
    end

    subgraph lane2[Host / Reception]
        h1[Manage reservations and waitlist]
        h2[Assign table]
    end

    subgraph lane3[Waiter / Captain]
        w1[Capture order]
        w2[Manage service and guest changes]
    end

    subgraph lane4[Chef / Kitchen Staff]
        k1[Receive routed tickets]
        k2[Prepare and mark ready]
    end

    subgraph lane5[Cashier / Accountant]
        c1[Generate bill]
        c2[Settle payment and close session]
    end

    subgraph lane6[Inventory / Purchase Manager]
        i1[Track ingredient depletion and replenishment]
    end

    subgraph lane7[Branch Manager / Admin]
        m1[Approve exceptions and review branch ops]
    end

    g1 --> h1 --> h2 --> w1 --> k1 --> k2 --> w2 --> c1 --> c2 --> g3
    w1 --> i1
    k1 --> i1
    c2 --> m1
    w2 --> m1
```

## Swimlane Interpretation

- Front-of-house, kitchen, inventory, and cashiering are intentionally linked as one operational chain.
- Inventory visibility is not a back-office afterthought; it feeds ordering and kitchen decisions in real time.
- Manager approvals remain explicit for operational exceptions such as voids, stock overrides, and settlement issues.

## Detailed Swimlane with Exception and Cancellation Paths

```mermaid
flowchart LR
    subgraph G[Guest]
        gA[Request reservation/walk-in]
        gB[Confirm order preferences]
        gC[Approve bill split]
        gD[Receive refund/cancellation notice]
    end

    subgraph H[Host]
        hA[Evaluate slot/waitlist options]
        hB[Seat or reassign table]
        hC[Initiate reservation cancellation]
    end

    subgraph W[Waiter]
        wA[Capture draft order]
        wB[Submit/adjust order]
        wC[Serve and request settlement]
    end

    subgraph K[Kitchen]
        kA[Accept ticket]
        kB[Prepare/synchronize courses]
        kC[Delay/refire exception handling]
    end

    subgraph C[Cashier]
        cA[Settle multi-tender payment]
        cB[Handle reversal/refund]
    end

    subgraph M[Manager/Policy]
        mA[Approve protected actions]
        mB[Activate/deactivate surge controls]
    end

    gA --> hA --> hB --> wA --> wB --> kA --> kB --> wC --> cA --> gC
    kB -->|issue| kC --> wB
    hC --> mA --> cB --> gD
    wB -->|void/discount needed| mA
    cA -->|timeout/decline| cB
    hA -->|load high| mB
    mB --> hA
```
