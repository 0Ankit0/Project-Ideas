# Security And Compliance

## Purpose
Describe the operational security and compliance controls for the **Hospital Information System**, especially those tied to PHI protection, auditability, zero-trust access, and regulated healthcare workloads.

## Control Domains

| Domain | Key Controls |
|---|---|
| Identity and access | SSO, MFA, least privilege, department-scoped roles, break-glass |
| Data protection | encryption, tokenization where needed, PHI redaction, WORM archives |
| Auditability | immutable logs, policy decision capture, evidence export, access review |
| Platform security | mTLS, network policy, image signing, secret rotation, vulnerability management |
| Privacy governance | consent enforcement, minimum necessary, segmentation, legal hold |

## Security Monitoring Flow
```mermaid
flowchart LR
    Services[Domain services] --> Audit[Audit and security logs]
    Audit --> SIEM[SIEM correlation]
    SIEM --> Alert[Security alert and case]
    Alert --> IR[Incident response]
    IR --> Evidence[Evidence repository]
    Evidence --> Review[Compliance review]
```

## PHI Control Requirements
- Every PHI read and write must produce immutable audit evidence.
- Sensitive identifiers in logs are masked or tokenized before leaving the source service.
- Service accounts have purpose-bound scopes and cannot browse patient charts.
- Bulk export requires explicit approval, reason, recipient, time window, and retention plan.
- Support staff access to production uses privileged sessions with recording and automatic expiration.

## Access Governance
- Role catalog must separate registrar, clinician, nurse, pharmacist, lab tech, radiology tech, billing staff, coder, auditor, admin, and support engineer privileges.
- Department and facility attributes constrain access beyond broad role membership.
- Break-glass access is time bound and triggers retrospective privacy review.
- Quarterly access certification is required for privileged roles and service accounts.

## Compliance Evidence Pack

| Evidence Type | Frequency | Source |
|---|---|---|
| PHI access audit export | on demand and monthly sample | Audit Service |
| Break-glass review report | daily | Audit Service and policy engine |
| Encryption and key rotation status | monthly | KMS, Vault, platform inventory |
| Vulnerability remediation status | weekly | container and host scanning |
| Backup and restore proof | monthly | backup platform and DR drills |
| Interface replay log | per incident | integration engine and audit service |

## Incident Handling Expectations
- Security incidents affecting PHI are triaged with compliance and legal involvement from the start.
- Audit subsystem degradation is treated as Sev 1 because fail-secure behavior can impact care operations.
- Breach investigation needs exact list of records accessed, actor sessions, affected patients, and policy decisions.
- Post-incident actions must include control gap remediation, not only service recovery.

## Technical Guardrails
1. Signed container images and admission policy for every workload.
2. Secrets injected at runtime from Vault with lease rotation.
3. No production PHI in developer environments.
4. Object storage for records and images uses immutable retention where policy requires.
5. All admin and data export endpoints are behind explicit allowlists and step-up authentication.

