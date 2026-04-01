# BPMN Swimlane Diagrams — Legal Case Management System

This document models three core business processes using BPMN-inspired swimlane notation
rendered with Mermaid `flowchart` diagrams. Each lane represents a participant (human
actor, organizational role, or system component), and cross-lane arrows represent
handoffs, triggers, or data exchanges.

Notation conventions used throughout:

- `([text])` — Start or end event (rounded stadium shape)
- `[text]` — Task or activity (rectangle)
- `{text}` — Gateway / decision point (diamond)
- Arrows between lanes — message flows or sequence flows crossing organizational boundaries

The three processes documented are:

- **Case Opening Process** — Lanes: Client, Attorney, Platform, Court
- **Invoice Approval and Delivery Process** — Lanes: Attorney, Billing Admin, Partner, Client
- **Document E-Signature Workflow** — Lanes: Attorney, E-Signature Provider, Client, Platform

---

## Case Opening Process

### Process Narrative

The case opening process converts an unvetted prospect into a formally engaged client
with an active, billable matter record. It involves four participants:

- **Client** — Initiates interest, completes the intake form, attends consultation,
  signs the engagement letter, and funds the retainer.
- **Attorney** — Reviews the intake, conducts the ethical conflict screen, scopes the
  engagement, drafts the engagement letter, and opens the matter.
- **Platform** — Stores intake data, automates the conflict search, generates document
  templates, creates system records, and notifies relevant staff.
- **Court** — Issues docket numbers and scheduling orders that feed the matter calendar
  when a litigation matter is opened.

**Critical decision points:**

1. **Conflict-of-Interest Gateway** — The single most consequential gate. A conflict
   finding terminates the process immediately. The declination must be logged for ethics
   record-keeping (ABA Model Rule 1.10). If the conflict is waivable and all parties
   consent in writing, the attorney may proceed after obtaining written waivers; this
   sub-process is not shown here but is triggered from the conflict-found branch.

2. **Engagement Letter Execution** — A second hard gate. Until the client countersigns and
   the retainer is funded, the platform blocks timekeeper access to the matter. This
   prevents unauthorized pre-engagement billing.

**Integration touchpoints:**

| System | Action |
|---|---|
| Conflict-check database | Queried against all firm contacts, adverse parties, and former clients |
| DocuSign / E-signature | Sends engagement letter for electronic signature |
| IOLTA ledger | Records initial retainer deposit against client sub-ledger |
| Court e-filing system | Retrieves docket number and scheduling order when case is already filed |

### BPMN Swimlane Diagram

```mermaid
flowchart TD
    subgraph CLIENT["LANE — CLIENT"]
        CL_START([Contact Firm — Phone / Web Inquiry])
        CL_FORM[Complete Online Intake Form]
        CL_CONSULT[Attend Initial Consultation]
        CL_SIGN[Sign Engagement Letter via E-Signature]
        CL_FUND[Fund IOLTA Retainer via Client Portal]
        CL_CONFIRM([Receive Matter Open Confirmation and Portal Access])
    end

    subgraph ATTORNEY["LANE — ATTORNEY"]
        AT_REVIEW[Review Intake Submission]
        AT_CONFLICT[Run Conflict-of-Interest Check]
        AT_DECISION{Conflict Found?}
        AT_WAIVABLE{Conflict Waivable?}
        AT_DECLINE[Send Declination Letter and Log Result]
        AT_CONSULT[Conduct Initial Consultation]
        AT_SCOPE[Define Scope, Fee Arrangement, and Budget]
        AT_DRAFT[Draft Engagement Letter]
        AT_COUNTER[Countersign Engagement Letter]
        AT_OPEN[Open Matter and Assign Team Members]
    end

    subgraph PLATFORM["LANE — PLATFORM"]
        PL_INTAKE[Store Intake Record — Create Prospect]
        PL_CONFLICT[Execute Automated Conflict Search]
        PL_NOTIFY_RESULT[Notify Attorney of Conflict Result]
        PL_TEMPLATE[Generate Engagement Letter from Template]
        PL_ESIGN[Send E-Signature Request via Integration]
        PL_MATTER[Create Matter Record and Generate Matter Number]
        PL_CALENDAR[Import Court Dates and Deadlines to Calendar]
        PL_NOTIFY_TEAM[Notify Assigned Staff — Email and In-App]
        PL_RETAINER[Record Retainer in IOLTA Client Sub-Ledger]
        PL_PORTAL[Activate Client Portal Access]
    end

    subgraph COURT["LANE — COURT"]
        CT_REGISTER[Issue Docket or Case Number]
        CT_SCHEDULE[Issue Scheduling Order]
    end

    CL_START --> CL_FORM
    CL_FORM --> PL_INTAKE
    PL_INTAKE --> AT_REVIEW
    AT_REVIEW --> AT_CONFLICT
    AT_CONFLICT --> PL_CONFLICT
    PL_CONFLICT --> PL_NOTIFY_RESULT
    PL_NOTIFY_RESULT --> AT_DECISION
    AT_DECISION -->|No| AT_CONSULT
    AT_DECISION -->|Yes| AT_WAIVABLE
    AT_WAIVABLE -->|No| AT_DECLINE
    AT_DECLINE --> CL_CONFIRM
    AT_WAIVABLE -->|Yes — Obtain Written Waivers| AT_CONSULT
    AT_CONSULT --> CL_CONSULT
    CL_CONSULT --> AT_SCOPE
    AT_SCOPE --> AT_DRAFT
    AT_DRAFT --> PL_TEMPLATE
    PL_TEMPLATE --> PL_ESIGN
    PL_ESIGN --> CL_SIGN
    CL_SIGN --> AT_COUNTER
    AT_COUNTER --> CL_FUND
    CL_FUND --> PL_RETAINER
    PL_RETAINER --> AT_OPEN
    AT_OPEN --> PL_MATTER
    PL_MATTER --> CT_REGISTER
    CT_REGISTER --> CT_SCHEDULE
    CT_SCHEDULE --> PL_CALENDAR
    PL_CALENDAR --> PL_NOTIFY_TEAM
    PL_NOTIFY_TEAM --> PL_PORTAL
    PL_PORTAL --> CL_CONFIRM
```

---

## Invoice Approval and Delivery Process

### Process Narrative

The invoice lifecycle requires coordinated collaboration among the billing attorney,
billing administration, the supervising partner, and the client. The process enforces a
two-stage human approval (attorney → partner) before any invoice is released externally,
protecting the firm from billing errors, unsupported write-downs, and client dissatisfaction.

**Participants:**

- **Attorney** — Reviews pre-bill line items, approves or adjusts time and expense entries,
  and handles any client disputes post-delivery.
- **Billing Admin** — Runs the billing cycle, applies trust funds, drafts the pre-bill,
  routes for approvals, generates the LEDES invoice, delivers it, and monitors collections.
- **Partner** — Final approver before external delivery. May return the pre-bill with
  adjustment notes, which sends it back to the attorney review loop.
- **Client** — Receives and pays the invoice or raises disputes via the portal.

**Critical decision points:**

1. **Attorney Pre-Bill Review** — The attorney can edit narrative, write down hours, or
   flag no-charge entries. All write-downs are logged with the initiating user and reason.

2. **Partner Approval Gate** — Required for all invoices. Partners may lower rates,
   write off entire entries, or hold the invoice pending resolution of a client concern.

3. **Trust Fund Application** — Before drafting the pre-bill, billing admin checks the
   client's IOLTA sub-ledger. Available trust funds are applied to reduce the net invoice
   amount. The corresponding trust disbursement is recorded immediately.

4. **Client Dispute Loop** — A disputed invoice returns to the attorney, not directly to
   billing. This ensures that adjustments are attorney-supervised, as required by
   professional responsibility rules governing fee disputes.

**Process performance indicators:**

| Metric | Target |
|---|---|
| Billing cycle close to invoice delivery | ≤ 5 business days |
| Pre-bill write-down rate | Monitored by practice group |
| Days sales outstanding (DSO) | ≤ 45 days |
| Invoice dispute rate | < 3% of invoices |

### BPMN Swimlane Diagram

```mermaid
flowchart TD
    subgraph ATTORNEY["LANE — ATTORNEY"]
        AT_START([Billing Cycle Closes])
        AT_PREBILL[Receive Pre-Bill Report]
        AT_REVIEW{Entries Correct?}
        AT_ADJUST[Edit or Write-Down Entries with Reason Code]
        AT_APPROVE[Approve and Sign Off on Pre-Bill]
        AT_DISPUTE_IN[Receive Client Dispute Notification]
        AT_DISPUTE_DEC{Issue Credit or Adjustment?}
        AT_CREDIT[Draft Credit Note and Revised Invoice]
        AT_DENY[Send Dispute Resolution — No Adjustment]
    end

    subgraph BILLING_ADMIN["LANE — BILLING ADMIN"]
        BA_PULL[Pull All Unbilled Time and Expense Entries]
        BA_GROUP[Group Entries by Matter and Client]
        BA_TRUST[Check IOLTA Sub-Ledger Balance]
        BA_APPLY{Trust Funds Available?}
        BA_DISBURSE[Disburse from Trust and Record Transaction]
        BA_DRAFT[Draft Pre-Bill Report]
        BA_ROUTE_AT[Route Pre-Bill to Responsible Attorney]
        BA_RECV_AT[Receive Attorney-Approved Pre-Bill]
        BA_ROUTE_PT[Route Approved Pre-Bill to Partner]
        BA_RECV_PT[Receive Partner Approval]
        BA_GENERATE[Generate LEDES 1998B Invoice]
        BA_DELIVER[Deliver Invoice via Portal and Email]
        BA_AGING[Monitor Payment Aging Report Daily]
        BA_PAYMENT{Payment Received Within Terms?}
        BA_REMINDER[Send Overdue Reminder Notice]
        BA_COLLECT{Escalate to External Collections?}
        BA_WRITEOFF[Record Write-Off or Bad Debt in Ledger]
        BA_POST[Post Payment and Reconcile AR Ledger]
        BA_END([Invoice Cycle Complete — Revenue Recognized])
    end

    subgraph PARTNER["LANE — PARTNER"]
        PT_RECV[Receive Pre-Bill for Review]
        PT_DEC{Approve as Submitted?}
        PT_RETURN[Return Pre-Bill with Adjustment Notes]
        PT_APPROVE[Approve Invoice for Release]
    end

    subgraph CLIENT["LANE — CLIENT"]
        CL_RECV[Receive Invoice Notification via Portal]
        CL_VIEW[Review Invoice Line Items]
        CL_DEC{Dispute Any Charges?}
        CL_DISPUTE[Submit Dispute with Supporting Notes]
        CL_PAY[Submit Payment — ACH / Card / Check / Wire]
        CL_CONFIRM([Payment Confirmation and Receipt Issued])
    end

    AT_START --> BA_PULL
    BA_PULL --> BA_GROUP --> BA_TRUST
    BA_TRUST --> BA_APPLY
    BA_APPLY -->|Yes| BA_DISBURSE
    BA_DISBURSE --> BA_DRAFT
    BA_APPLY -->|No| BA_DRAFT
    BA_DRAFT --> BA_ROUTE_AT
    BA_ROUTE_AT --> AT_PREBILL
    AT_PREBILL --> AT_REVIEW
    AT_REVIEW -->|No| AT_ADJUST
    AT_ADJUST --> AT_PREBILL
    AT_REVIEW -->|Yes| AT_APPROVE
    AT_APPROVE --> BA_RECV_AT
    BA_RECV_AT --> BA_ROUTE_PT
    BA_ROUTE_PT --> PT_RECV
    PT_RECV --> PT_DEC
    PT_DEC -->|No| PT_RETURN
    PT_RETURN --> AT_PREBILL
    PT_DEC -->|Yes| PT_APPROVE
    PT_APPROVE --> BA_RECV_PT
    BA_RECV_PT --> BA_GENERATE
    BA_GENERATE --> BA_DELIVER
    BA_DELIVER --> CL_RECV
    CL_RECV --> CL_VIEW
    CL_VIEW --> CL_DEC
    CL_DEC -->|Yes| CL_DISPUTE
    CL_DISPUTE --> AT_DISPUTE_IN
    AT_DISPUTE_IN --> AT_DISPUTE_DEC
    AT_DISPUTE_DEC -->|Yes| AT_CREDIT
    AT_CREDIT --> BA_GENERATE
    AT_DISPUTE_DEC -->|No| AT_DENY
    AT_DENY --> CL_VIEW
    CL_DEC -->|No| CL_PAY
    CL_PAY --> BA_AGING
    CL_PAY --> CL_CONFIRM
    BA_AGING --> BA_PAYMENT
    BA_PAYMENT -->|Yes| BA_POST
    BA_POST --> BA_END
    BA_PAYMENT -->|No| BA_REMINDER
    BA_REMINDER --> BA_COLLECT
    BA_COLLECT -->|Yes| BA_WRITEOFF
    BA_WRITEOFF --> BA_END
    BA_COLLECT -->|No| BA_REMINDER
```

---

## Document E-Signature Workflow

### Process Narrative

Legal documents requiring client signatures — engagement letters, settlement agreements,
retainer amendments, and authorization forms — must be executed via a secure,
court-admissible e-signature process. The workflow integrates with a third-party
e-signature provider (modeled generically; the platform supports DocuSign, Adobe Sign,
and similar providers).

**Participants:**

- **Attorney** — Selects or uploads the document, configures signature fields and
  authentication requirements, dispatches the envelope, and certifies the final signed
  copy in the system.
- **E-Signature Provider** — Creates the envelope, delivers the signing link, verifies
  the signer's identity, collects the e-signature, generates the audit certificate, and
  returns the signed package to the platform.
- **Client** — Receives the signing request, completes identity verification, reviews the
  document, and either applies their electronic signature or declines with a stated reason.
- **Platform** — Stores the draft document, initiates the e-sign integration, tracks
  envelope status, versions the document on receipt of the signed copy, stores the final
  signed document with its audit certificate, and writes an audit trail entry.

**Critical decision points:**

1. **Authentication Level Selection** — The attorney configures authentication strength
   at dispatch time. Email verification is the minimum; SMS OTP and knowledge-based
   authentication (KBA) are available for high-value or high-risk documents.

2. **Sign or Decline Gateway** — If the client declines, the envelope is not re-sent
   automatically. The attorney receives a notification and must decide whether to revise
   the document and re-initiate, or withdraw it entirely. This prevents re-send loops that
   could obscure a genuine client objection.

3. **Version Control on Completion** — The platform creates a new, immutable document
   version for the signed copy. The unsigned draft is preserved in version history but
   flagged as superseded.

**Compliance and security requirements:**

| Requirement | Implementation |
|---|---|
| Tamper evidence | SHA-256 hash stored with signed document; provider audit certificate attached |
| Signer identity | Email verification minimum; KBA or SMS OTP for engagement letters and settlements |
| Audit trail | Immutable log entry written on every status transition of the envelope |
| Document storage | Signed copy stored in matter DMS with privilege and confidentiality flags |
| Access control | Only matter team members and the signing client can access the signed document |

### BPMN Swimlane Diagram

```mermaid
flowchart TD
    subgraph ATTORNEY["LANE — ATTORNEY"]
        AT_START([Identify Document Requiring Signature])
        AT_SELECT[Select Template or Upload Prepared Document]
        AT_TAG[Tag Signature, Initial, and Date Fields]
        AT_AUTH[Configure Authentication Level — Email / SMS / KBA]
        AT_DISPATCH[Dispatch Signing Envelope]
        AT_DECLINE_RECV[Receive Decline Notification and Reason]
        AT_REVISE{Revise and Resend?}
        AT_WITHDRAW[Withdraw Document — Log Reason]
        AT_REVIEW_SIGNED[Review Returned Signed Document]
        AT_CERTIFY[Confirm and Certify Execution in System]
        AT_END([Document Fully Executed and Filed to DMS])
    end

    subgraph ESIGN_PROVIDER["LANE — E-SIGNATURE PROVIDER"]
        DS_ENVELOPE[Create Signing Envelope with Fields]
        DS_NOTIFY[Send Signing Link via Email and Optional SMS]
        DS_VERIFY[Verify Signer Identity per Configured Method]
        DS_PRESENT[Present Document with Signature Fields]
        DS_COLLECT[Collect Signature and Initials]
        DS_CERT[Generate Tamper-Evident Audit Certificate]
        DS_RETURN[Return Signed Package and Certificate to Platform]
        DS_EXPIRE[Mark Envelope Declined or Expired]
    end

    subgraph CLIENT["LANE — CLIENT"]
        CL_EMAIL[Receive Signing Request Email]
        CL_VERIFY[Complete Identity Verification Step]
        CL_REVIEW[Read Document in Signing Interface]
        CL_DECISION{Sign or Decline?}
        CL_SIGN[Apply Electronic Signature and Initials]
        CL_DECLINE[Decline Envelope — Enter Reason]
        CL_COPY([Receive Signed Copy via Portal and Email])
    end

    subgraph PLATFORM["LANE — PLATFORM"]
        PL_STORE_DRAFT[Store Draft Document — Version 1 — in DMS]
        PL_INITIATE[Call E-Sign Provider API — Create Envelope]
        PL_TRACK[Track Envelope Status via Webhook]
        PL_RECV_SIGNED[Receive Signed Package from Provider]
        PL_VERSION[Create New Document Version — Signed]
        PL_STORE_FINAL[Store Signed Document with Audit Certificate]
        PL_AUDIT[Write Immutable Audit Trail Entry]
        PL_NOTIFY_AT[Notify Attorney — Signing Complete]
        PL_NOTIFY_CL[Deliver Signed Copy to Client Portal]
        PL_DECLINE_TRACK[Track Decline Event — Notify Attorney]
    end

    AT_START --> AT_SELECT
    AT_SELECT --> AT_TAG
    AT_TAG --> AT_AUTH
    AT_AUTH --> AT_DISPATCH
    AT_DISPATCH --> PL_STORE_DRAFT
    PL_STORE_DRAFT --> PL_INITIATE
    PL_INITIATE --> DS_ENVELOPE
    DS_ENVELOPE --> DS_NOTIFY
    DS_NOTIFY --> CL_EMAIL
    CL_EMAIL --> CL_VERIFY
    CL_VERIFY --> DS_VERIFY
    DS_VERIFY --> DS_PRESENT
    DS_PRESENT --> CL_REVIEW
    CL_REVIEW --> CL_DECISION
    CL_DECISION -->|Sign| CL_SIGN
    CL_SIGN --> DS_COLLECT
    DS_COLLECT --> DS_CERT
    DS_CERT --> DS_RETURN
    DS_RETURN --> PL_RECV_SIGNED
    PL_RECV_SIGNED --> PL_TRACK
    PL_TRACK --> PL_VERSION
    PL_VERSION --> PL_STORE_FINAL
    PL_STORE_FINAL --> PL_AUDIT
    PL_AUDIT --> PL_NOTIFY_AT
    PL_AUDIT --> PL_NOTIFY_CL
    PL_NOTIFY_AT --> AT_REVIEW_SIGNED
    AT_REVIEW_SIGNED --> AT_CERTIFY
    AT_CERTIFY --> AT_END
    PL_NOTIFY_CL --> CL_COPY
    CL_DECISION -->|Decline| CL_DECLINE
    CL_DECLINE --> DS_EXPIRE
    DS_EXPIRE --> PL_DECLINE_TRACK
    PL_DECLINE_TRACK --> AT_DECLINE_RECV
    AT_DECLINE_RECV --> AT_REVISE
    AT_REVISE -->|Yes| AT_SELECT
    AT_REVISE -->|No| AT_WITHDRAW
```

---

## Process Comparison Summary

| Process | Lanes | Key Human Gate | Primary Compliance Concern |
|---|---|---|---|
| Case Opening | Client, Attorney, Platform, Court | Conflict-of-interest check | ABA Model Rules 1.7, 1.10 |
| Invoice Approval and Delivery | Attorney, Billing Admin, Partner, Client | Partner pre-delivery approval | Fee reasonableness — ABA Model Rule 1.5 |
| Document E-Signature | Attorney, E-Sign Provider, Client, Platform | Decline review before re-send | ESIGN Act / UETA enforceability |

All three processes converge on the same platform audit trail, ensuring a complete and
immutable record of every cross-lane handoff for compliance reporting, malpractice defence,
and bar audit purposes.
