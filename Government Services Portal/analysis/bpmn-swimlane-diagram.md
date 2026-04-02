# BPMN Swimlane Diagram — Government Services Portal

## Overview

This document presents Business Process Model and Notation (BPMN) swimlane diagrams for the Government Services Portal's core processes. Each process is decomposed into lanes representing the actors (Citizen, System, Field Officer, Department Head, etc.) responsible for each activity. The diagrams use Mermaid flowchart notation to approximate BPMN swimlane semantics.

**Notation Guide:**
- Rectangles: Tasks / Activities
- Diamonds: Gateways (Decision points)
- Rounded rectangles: Start / End events
- Arrows: Sequence flows
- Subgraphs: Swimlanes (participant pools)

---

## Process 1: Service Application End-to-End

This is the primary citizen-facing process, spanning from service discovery through final certificate issuance.

```mermaid
flowchart TD
    subgraph CITIZEN["🧑 Citizen"]
        C1([Start]) --> C2[Browse Service Catalog]
        C2 --> C3{Eligible?}
        C3 -- No --> C4[View Eligibility Requirements]
        C4 --> C2
        C3 -- Yes --> C5[Fill Multi-Step Application Form]
        C5 --> C6[Upload Supporting Documents]
        C6 --> C7{All docs uploaded?}
        C7 -- No --> C6
        C7 -- Yes --> C8[Review Application Summary]
        C8 --> C9{Confirm Submission?}
        C9 -- No --> C5
        C9 -- Yes --> C10[Submit Application]
        C10 --> C11[Receive Acknowledgment SMS/Email]
        C11 --> C12[Receive Fee Payment Request]
        C12 --> C13[Pay Application Fee via ConnectIPS]
        C13 --> C14{Payment Successful?}
        C14 -- No --> C15[Retry Payment or Generate Challan]
        C15 --> C13
        C14 -- Yes --> C16[Receive Payment Receipt]
        C16 --> C17[Monitor Application Status]
        C17 --> C18{Clarification Requested?}
        C18 -- Yes --> C19[Respond to Clarification Request]
        C19 --> C17
        C18 -- No --> C20{Decision Received?}
        C20 -- Rejected --> C21[Review Rejection Reason]
        C21 --> C22{File Grievance?}
        C22 -- Yes --> C23[Submit Grievance]
        C22 -- No --> C24([End - Rejected])
        C20 -- Approved --> C25[Download Digital Certificate]
        C25 --> C26([End - Approved])
    end

    subgraph SYSTEM["⚙️ Portal System"]
        S1[Validate Form Data] --> S2[Check Document Completeness]
        S2 --> S3[Generate Application Reference ID]
        S3 --> S4[Trigger Acknowledgment Notification]
        S4 --> S5[Calculate Fee Amount]
        S5 --> S6[Initiate ConnectIPS Payment Session]
        S6 --> S7{ConnectIPS Callback Received?}
        S7 -- Timeout --> S8[Reconcile via Webhook Retry]
        S8 --> S7
        S7 -- Success --> S9[Update Application Status: PAYMENT_COMPLETED]
        S9 --> S10[Route to Department Queue]
        S10 --> S11[Assign to Available Field Officer]
        S11 --> S12[Monitor SLA Timer]
        S12 --> S13{SLA Breached?}
        S13 -- Yes --> S14[Escalate to Department Head]
        S13 -- No --> S15[Continue Monitoring]
        S15 --> S12
        S14 --> S16[Update Escalation Record]
    end

    subgraph OFFICER["👮 Field Officer"]
        O1[Receive Application in Queue] --> O2[Review Application Details]
        O2 --> O3[Verify Documents]
        O3 --> O4{Documents Valid?}
        O4 -- No --> O5[Request Clarification from Citizen]
        O5 --> O6[Await Citizen Response]
        O6 --> O3
        O4 -- Yes --> O7[Perform Field Verification if Required]
        O7 --> O8[Prepare Recommendation Report]
        O8 --> O9{Recommend?}
        O9 -- Reject --> O10[Document Rejection Reason]
        O10 --> O11[Submit Rejection to Dept Head]
        O9 -- Approve --> O12[Submit Approval Recommendation]
    end

    subgraph HOD["🏛️ Department Head"]
        H1[Review Officer Recommendation] --> H2{Decision?}
        H2 -- Approve --> H3[Digitally Approve Application]
        H3 --> H4[Trigger Certificate Generation]
        H4 --> H5[DSC Sign Certificate]
        H5 --> H6[Upload to S3 and Nepal Document Wallet (NDW)]
        H6 --> H7[Notify Citizen of Approval]
        H2 -- Reject --> H8[Record Final Rejection with Reason]
        H8 --> H9[Notify Citizen of Rejection]
        H2 -- Return --> H10[Return to Officer with Comments]
        H10 --> H1
    end

    C10 --> S1
    S11 --> O1
    O12 --> H1
    O11 --> H1
    H7 --> C25
    H9 --> C21
```

### Process Metrics

| Process | Average Duration | SLA Target | Automated Steps | Manual Steps |
|---------|-----------------|------------|-----------------|--------------|
| Form Fill & Submission | 15–45 minutes | N/A (citizen) | 5 | 3 |
| Fee Payment | 2–10 minutes | N/A (citizen) | 4 | 1 |
| Document Verification | 1–3 working days | 3 working days | 2 | 4 |
| Officer Review | 3–7 working days | 7 working days | 1 | 5 |
| HOD Approval | 1–2 working days | 2 working days | 3 | 2 |
| Certificate Issuance | 5–15 minutes | 30 minutes post-approval | 6 | 0 |
| **Full End-to-End** | **7–15 working days** | **15 working days** | **21** | **15** |

---

## Process 2: Grievance Redressal Process

```mermaid
flowchart TD
    subgraph CITIZEN2["🧑 Citizen"]
        G1([Grievance Start]) --> G2[File Grievance via Portal]
        G2 --> G3[Provide Grievance Category and Description]
        G3 --> G4[Attach Supporting Evidence]
        G4 --> G5[Submit Grievance]
        G5 --> G6[Receive Acknowledgment with Grievance ID]
        G6 --> G7[Monitor Grievance Status]
        G7 --> G8{Resolved Satisfactorily?}
        G8 -- Yes --> G9([End - Resolved])
        G8 -- No --> G10{Escalate?}
        G10 -- Yes --> G11[Request Ombudsman Escalation]
        G11 --> G12[Receive Ombudsman Case ID]
        G12 --> G13([End - Escalated to Ombudsman])
        G10 -- No --> G14[Accept Resolution]
        G14 --> G9
    end

    subgraph GSYSTEM["⚙️ System"]
        GS1[Auto-acknowledge Grievance] --> GS2[Generate Unique Grievance ID]
        GS2 --> GS3[Classify Grievance Category]
        GS3 --> GS4[Route to Appropriate Department]
        GS4 --> GS5[Set SLA Timer: 15 working days]
        GS5 --> GS6{SLA D-5 Warning?}
        GS6 -- Yes --> GS7[Send Warning Notification to Officer]
        GS6 -- No --> GS8[Continue Monitoring]
        GS8 --> GS6
        GS7 --> GS9{SLA Breached?}
        GS9 -- Yes --> GS10[Auto-escalate to Department Head]
        GS9 -- No --> GS8
        GS10 --> GS11{D-3 Still Unresolved?}
        GS11 -- Yes --> GS12[Escalate to Ombudsman Queue]
        GS11 -- No --> GS8
    end

    subgraph GOFF["👮 Dept Officer"]
        GO1[Receive Grievance Assignment] --> GO2[Investigate Complaint]
        GO2 --> GO3[Review Original Application Records]
        GO3 --> GO4{Valid Grievance?}
        GO4 -- Yes --> GO5[Prepare Resolution Report]
        GO5 --> GO6[Submit Resolution to Department Head]
        GO4 -- No --> GO7[Document Rejection with Evidence]
        GO7 --> GO8[Submit Rejection Decision]
    end

    subgraph GHOD["🏛️ Dept Head"]
        GH1[Review Officer Resolution] --> GH2{Decision?}
        GH2 -- Approve --> GH3[Finalize Resolution]
        GH3 --> GH4[Notify Citizen with Resolution Details]
        GH4 --> GH5[Close Grievance Record]
        GH2 -- Reject --> GH6[Reassign to Senior Officer]
        GH6 --> GO1
    end

    subgraph GOMB["⚖️ Ombudsman"]
        GM1[Review Escalated Grievance] --> GM2[Conduct Independent Investigation]
        GM2 --> GM3[Issue Binding Directive]
        GM3 --> GM4[Notify All Parties]
        GM4 --> GM5[Update Portal with Final Decision]
    end

    G5 --> GS1
    GS4 --> GO1
    GO6 --> GH1
    GO8 --> GH1
    GH4 --> G7
    GS12 --> GM1
    G11 --> GM1
    GM5 --> G7
```

---

## Process 3: Department Service Configuration

This process covers how a Super Admin or Department Head configures a new government service on the portal.

```mermaid
flowchart TD
    subgraph SADMIN["🔑 Super Admin"]
        SA1([Config Start]) --> SA2[Receive Service Onboarding Request]
        SA2 --> SA3[Verify Departmental Authorization Letter]
        SA3 --> SA4{Authorization Valid?}
        SA4 -- No --> SA5[Reject Request with Reason]
        SA5 --> SA6([End - Rejected])
        SA4 -- Yes --> SA7[Create Department in System if New]
        SA7 --> SA8[Assign Department Head User Account]
        SA8 --> SA9[Grant Department Admin Permissions]
        SA9 --> SA10[Notify Department Head]
    end

    subgraph DH2["🏛️ Department Head"]
        D1[Receive Access Notification] --> D2[Log into Admin Console]
        D2 --> D3[Create New Service Entry]
        D3 --> D4[Define Service Metadata]
        D4 --> D5[Configure Eligibility Criteria]
        D5 --> D6[Build Application Form Schema]
        D6 --> D7[Define Required Documents List]
        D7 --> D8[Set Fee Structure]
        D8 --> D9[Configure SLA Timelines]
        D9 --> D10[Define Workflow Steps and Approvers]
        D10 --> D11[Submit Service for Review]
        D11 --> D12{Review Passed?}
        D12 -- No --> D13[Revise Service Configuration]
        D13 --> D11
        D12 -- Yes --> D14[Publish Service to Catalog]
        D14 --> D15([Config End - Service Live])
    end

    subgraph CS["⚙️ Config System"]
        CS1[Validate Service Schema] --> CS2{Schema Valid?}
        CS2 -- No --> CS3[Return Validation Errors]
        CS3 --> D13
        CS2 -- Yes --> CS4[Preview Service in Staging]
        CS4 --> CS5[Run Automated Compliance Checks]
        CS5 --> CS6{Checks Pass?}
        CS6 -- No --> CS7[Flag Compliance Issues]
        CS7 --> D13
        CS6 -- Yes --> CS8[Approve for Publication]
        CS8 --> CS9[Index Service in Catalog Search]
        CS9 --> CS10[Enable Public Access]
        CS10 --> CS11[Send Launch Notification to Citizens]
    end

    SA10 --> D1
    D11 --> CS1
    CS8 --> D12
    CS11 --> D14
```

---

## Process 4: Offline Challan Payment Reconciliation

```mermaid
flowchart TD
    subgraph CP_CIT["🧑 Citizen"]
        CP1([Challan Start]) --> CP2[Request Offline Challan from Portal]
        CP2 --> CP3[Download PDF Challan]
        CP3 --> CP4[Visit Authorized Bank Branch]
        CP4 --> CP5[Pay Cash or DD Against Challan]
        CP5 --> CP6[Receive Bank Stamp and Receipt]
        CP6 --> CP7[Wait for Application Update]
        CP7 --> CP8{Application Updated?}
        CP8 -- Yes --> CP9([End - Payment Verified])
        CP8 -- No, after 3 days --> CP10[Contact Help Desk]
        CP10 --> CP8
    end

    subgraph CP_BANK["🏦 Authorized Bank"]
        B1[Receive Challan Payment] --> B2[Validate Challan Details]
        B2 --> B3{Challan Valid?}
        B3 -- No --> B4[Reject Payment]
        B4 --> B5[Inform Citizen]
        B3 -- Yes --> B6[Process Payment]
        B6 --> B7[Generate Bank UTR Number]
        B7 --> B8[Submit SFTP Payment File to Portal]
        B8 --> B9[End of Bank Process]
    end

    subgraph CP_SYS["⚙️ System"]
        CPS1[Receive SFTP Payment File] --> CPS2[Parse and Validate File Format]
        CPS2 --> CPS3{File Valid?}
        CPS3 -- No --> CPS4[Alert Finance Team]
        CPS4 --> CPS5[Request Corrected File from Bank]
        CPS5 --> CPS1
        CPS3 -- Yes --> CPS6[Match Challan Numbers to Applications]
        CPS6 --> CPS7{All Challans Matched?}
        CPS7 -- Unmatched --> CPS8[Flag Unmatched Payments]
        CPS8 --> CPS9[Manual Review Queue]
        CPS7 -- All Matched --> CPS10[Update Application Payment Status]
        CPS10 --> CPS11[Send Confirmation to Citizen]
        CPS11 --> CPS12[Generate Reconciliation Report]
    end

    CP2 --> CPS1
    B8 --> CPS1
    CPS11 --> CP7
```

---

## Exception Handling Procedures

| Exception | Trigger | Handling Procedure | Responsible Party |
|-----------|---------|-------------------|-------------------|
| Duplicate Application Submission | Citizen submits same application twice within 24 hours | System returns existing application reference; citizen redirected to status page | System (automated) |
| Payment Gateway Unavailable | ConnectIPS returns 503 or timeout | Show maintenance message; offer challan fallback; retry after 15 minutes | System + Field Officer notification |
| Document Upload Virus Detected | ClamAV flags uploaded file | Quarantine file; notify citizen; do not block application progress for 48 hours; request resubmission | System + Citizen Notification |
| Officer Unresponsive > 3 Days | Application not touched for 3 business days | Auto-reminder to officer; CC department head on day 4; auto-reassign on day 5 | System (Celery beat scheduler) |
| DSC Expiry During Certificate Generation | Signing service returns certificate expiry error | Queue certificate; notify Super Admin; fallback to manual stamp and scan; log incident | System + Super Admin alert |
| SLA Breach — Grievance | Grievance unresolved after 15 working days | Auto-escalate to Department Head; SMS alert to citizen; create escalation audit record | Celery Beat + Notification Service |
| Database Connection Pool Exhausted | All 100 PgBouncer connections busy | Queue wait with 30-second timeout; return 503 with Retry-After header; scale Fargate tasks | System + CloudWatch alarm |
| NID NASC (National Identity Management Centre) API Down | NASC (National Identity Management Centre) returns 5xx or times out | Switch to email OTP fallback; log NASC (National Identity Management Centre) outage; alert Super Admin; maintain 15-minute circuit breaker | Auth Service + Circuit Breaker |

---

## Operational Policy Addendum

### Citizen Data Privacy Policies

- **PP-01 — Minimal Data Collection**: Application forms collect only the data fields mandated by the relevant government act (e.g., Municipal Act, Motor Vehicles Act). No additional personal data is collected without explicit citizen consent.
- **PP-02 — Purpose Limitation**: Data collected during an application is used solely for processing that application. Reuse for unrelated services requires fresh consent.
- **PP-03 — NID Data Handling**: NID numbers are never stored in full; only a SHA-256 hash of the masked NID is persisted. Compliant with NID Act 2016 Section 29.
- **PP-04 — Citizen Data Access**: Citizens may request a full export of their personal data held by the portal via the Data Access Request feature. Response within 30 calendar days per PDPA draft guidelines.
- **PP-05 — Data Breach Notification**: In the event of a confirmed data breach, affected citizens will be notified within 72 hours via SMS and email. CERT-In will be notified per IT Amendment Rules 2022.
- **PP-06 — Retention and Deletion**: Application data retained for 7 years post-closure (RTI compliance). Citizens may request deletion of draft/incomplete applications at any time.

### Service Delivery SLA Policies

- **SLA-01 — Application Acknowledgment**: System sends acknowledgment (SMS + email) within 5 minutes of successful submission. Target: 99.5% within SLA.
- **SLA-02 — Fee Payment Confirmation**: Payment confirmation sent within 2 minutes of ConnectIPS webhook receipt. Target: 99.9% within SLA.
- **SLA-03 — Officer First Review**: Field officer must initiate review within 3 working days of payment confirmation. Breach triggers automated escalation.
- **SLA-04 — Certificate Delivery**: Approved certificates generated and delivered to Nepal Document Wallet (NDW) within 30 minutes of Department Head approval.
- **SLA-05 — Grievance Acknowledgment**: Grievances acknowledged (auto) within 1 hour of filing. First human response within 3 working days.
- **SLA-06 — Portal Availability**: Target 99.9% uptime (≤ 8.7 hours downtime/year). Measured via CloudWatch Synthetic Canaries.

### Fee and Payment Policies

- **FP-01 — Fee Immutability at Submission**: The fee amount displayed at form-start is locked for 48 hours. Price changes by admins take effect for new applications only.
- **FP-02 — Challan Validity**: Offline challans are valid for 7 calendar days from generation. Expired challans must be regenerated; no extensions without HOD approval.
- **FP-03 — Duplicate Payment Protection**: Idempotency keys (Redis, 24-hour TTL) prevent double-charging. All payment initiation endpoints are idempotent.
- **FP-04 — Refund Timeline**: Automatic refunds for rejected applications initiated within 24 hours. Bank processing: 5–7 working days. Citizen notified at each stage.
- **FP-05 — Reconciliation Cadence**: SFTP challan files processed daily at 06:00 IST. Unmatched payments escalated to Finance team by 09:00 IST same day.
- **FP-06 — Payment Records Retention**: All payment records retained for 10 years for audit and RTI compliance.

### System Availability Policies

- **AV-01 — Scheduled Maintenance Window**: Sundays 02:00–04:00 IST. Citizens notified 48 hours in advance via portal banner and SMS. Emergency maintenance may occur with 2-hour notice.
- **AV-02 — RTO/RPO Targets**: Recovery Time Objective: 4 hours for full system. Recovery Point Objective: 1 hour (RDS automated backup frequency).
- **AV-03 — Multi-AZ Deployment**: All production services run across two AWS Availability Zones (ap-south-1a, ap-south-1b). Single-AZ failure does not cause downtime.
- **AV-04 — Auto-Scaling Thresholds**: ECS services scale out when CPU > 70% for 2 consecutive minutes. Scale in when CPU < 30% for 10 minutes. Minimum 2 tasks always running.
- **AV-05 — Disaster Recovery Testing**: Full DR failover drill conducted quarterly. Results documented and remediation actions tracked in JIRA.
