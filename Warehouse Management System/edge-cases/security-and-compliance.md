# Security and Compliance Edge Cases

## Sensitive Operation Controls

| Operation | Control |
|---|---|
| Manual inventory override | dual-approval + immutable evidence |
| Shipment cancellation post-handoff | supervisor + transport approval |
| Bulk adjustment upload | signed file + checksum + dry-run validation |

## Threat Scenarios
- Compromised scanner credential attempting fraudulent picks.
- Insider misuse of override permissions.
- Tampering with event replay payloads.

## Defensive Architecture
```mermaid
flowchart LR
    User --> IAM[Identity Provider]
    IAM --> API[WMS API]
    API --> Policy[Authorization Policy Engine]
    API --> Audit[Immutable Audit Store]
    API --> SIEM[Security Monitoring]
```

## Compliance Evidence
- Every high-impact command stores `who/what/why/when`.
- Quarterly access review and least-privilege recertification.
- Regional retention and legal-hold policy applied to audit evidence.
