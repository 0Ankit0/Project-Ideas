# Swimlane Diagrams

These swimlane views show who owns each cross-system handoff. The emphasis is on
identity-domain race conditions, human approvals, and evidence-producing transitions.

## Federated Login with Adaptive MFA

```mermaid
flowchart LR
    subgraph User["User and Browser"]
        U1["Start login"]
        U2["Complete factor challenge"]
        U3["Receive tokens and session state"]
    end
    subgraph IdP["External IdP"]
        I1["Authenticate subject"]
        I2["Return assertion or code"]
    end
    subgraph IAM["IAM Auth Core"]
        A1["Validate assertion and connection policy"]
        A2["Build session candidate"]
        A3["Issue tokens"]
    end
    subgraph Risk["Risk and MFA"]
        R1["Score device posture and login risk"]
        R2["Select challenge method"]
        R3["Promote assurance level"]
    end
    subgraph Audit["Audit and SIEM"]
        S1["Record login attempt"]
        S2["Record session creation"]
    end

    U1 --> I1 --> I2 --> A1 --> S1 --> A2 --> R1
    R1 --> R2 --> U2 --> R3 --> A3 --> S2 --> U3
```

**Lane ownership**
- The IdP proves primary authentication but does not decide local session state, adaptive MFA, or authorization scope.
- IAM Auth Core owns nonce validation, issuer or audience pinning, JIT provisioning limits, and refresh-family creation.
- Risk and MFA owns challenge method selection, device posture evaluation, and factor replay protection.

## SCIM Drift Reconciliation and Entitlement Repair

```mermaid
flowchart LR
    subgraph Directory["Source Directory or HRIS"]
        D1["Publish user or group delta"]
    end
    subgraph Connector["SCIM and Federation Adapters"]
        C1["Validate schema and source ownership"]
        C2["Store provisioning delta"]
    end
    subgraph Reconciler["Drift and Entitlement Reconciler"]
        R1["Compare current state with authoritative attributes"]
        R2["Detect entitlement conflicts"]
        R3["Prepare auto fix or review item"]
    end
    subgraph Admin["Identity Admin and SecOps"]
        A1["Approve high risk correction"]
        A2["Review residual conflicts"]
    end
    subgraph Runtime["IAM Runtime"]
        I1["Apply corrections and revoke stale grants"]
        I2["Terminate sessions when required"]
        I3["Emit reconciliation proof"]
    end

    D1 --> C1 --> C2 --> R1 --> R2 --> R3
    R3 -->|Low risk| I1 --> I2 --> I3
    R3 -->|High risk| A1 --> A2 --> I1
```

**Lane ownership**
- Connector validation owns schema correctness, idempotency, and source-of-truth tagging before any local mutation occurs.
- The reconciler owns deterministic conflict resolution and escalation routing, not the external directory.
- Admin review is required for manager-chain changes, privileged group removals, or claim mapping changes that would broaden access.

## Break-Glass Approval, Use, and Closure

```mermaid
flowchart LR
    subgraph Requestor["Operator Requestor"]
        Q1["Submit emergency request plus reason"]
        Q2["Complete fresh step up"]
        Q3["Use scoped emergency session"]
    end
    subgraph Approvers["Security and Service Owners"]
        A1["Review scope, ticket, and blast radius"]
        A2["Grant dual approval"]
    end
    subgraph ControlPlane["IAM Admin Control Plane"]
        C1["Create pending break glass record"]
        C2["Mint scoped session after approvals"]
        C3["Track expiry and revoke on timeout"]
    end
    subgraph Enforcement["PEP, PDP, and Session Services"]
        E1["Enforce scope and obligations"]
        E2["Revoke session and grants"]
    end
    subgraph Compliance["Audit and Compliance"]
        P1["Capture full approval chain"]
        P2["Archive closure evidence"]
    end

    Q1 --> C1 --> A1 --> A2 --> P1 --> Q2 --> C2 --> E1 --> Q3 --> C3 --> E2 --> P2
```

## RACI Highlights

| Workflow | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Federated login assurance | Auth service plus risk engine | IAM product owner | Tenant security admin | End-user support |
| Drift reconciliation | SCIM reconciler | Identity operations lead | Source directory owner | Affected application owners |
| Break-glass activation | Admin control plane plus approvers | Incident commander | Service owner and SecOps | Compliance team |

## Handoff Rules
- Every lane transition carries `tenant_id`, `correlation_id`, subject reference, and actor reference where applicable.
- Human review lanes must record start time, reviewer identity, approval outcome, and timeout path.
- Security-sensitive transitions are incomplete until an immutable audit envelope is written and linked back to the workflow record.
