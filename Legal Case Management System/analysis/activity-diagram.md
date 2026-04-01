# Activity Diagrams — Legal Case Management System

This document contains three activity diagrams modelling the primary operational workflows
of a law firm SaaS platform. Each diagram uses swim-lane–style notation via `subgraph`
blocks to assign activities to their responsible actor or system component. Arrows between
lanes represent handoffs, triggers, or data flows.

The three workflows covered are:

- **Case Lifecycle** — from first client contact to matter archival
- **Billing Workflow** — from time entry to payment reconciliation
- **Court Deadline Management** — from deadline identification to timely completion

---

## Case Lifecycle Activity Diagram

The case lifecycle spans from a prospective client's first contact with the firm through
final matter archival. It crosses four swim lanes:

- **Client** — initiates contact, signs documents, funds the retainer, reviews invoices,
  and receives the closure summary.
- **Attorney** — evaluates the intake, runs the conflict-of-interest check, drafts the
  engagement letter, performs legal work, approves billing, and closes the matter.
- **Platform** — automates conflict searches, generates document templates, manages matter
  records, syncs court calendars, and maintains the audit trail.
- **Court** — issues scheduling orders and docket numbers that feed the calendar.

Two hard gates govern the entire lifecycle. First, the **conflict-of-interest check**
(required under ABA Model Rule 1.7) must pass before any attorney-client relationship is
formed. Second, the **engagement letter** must be fully executed before any billable work
commences. Until both gates are cleared, no time entries are permitted against the matter.

Key compliance notes:

- Conflict check results must be logged regardless of outcome.
- Retainer funds are deposited to the IOLTA trust account, not the operating account.
- The matter may only transition to `Closed` after all open invoices are resolved.
- Archival preserves all records immutably for the firm's document-retention period.

```mermaid
flowchart TD
    subgraph CLIENT["LANE — CLIENT"]
        c1([Inquiry / Contact Firm])
        c2[Submit Online Intake Form]
        c3[Sign Engagement Letter via Portal]
        c4[Fund Retainer to IOLTA Trust]
        c5[Review Bills on Client Portal]
        c6{Dispute Invoice?}
        c7[Submit Payment]
        c8([Receive Matter Closure Summary])
    end

    subgraph ATTORNEY["LANE — ATTORNEY"]
        a1[Review Intake Submission]
        a2[Initiate Conflict-of-Interest Check]
        a3{Conflict Found?}
        a4[Send Declination Letter / Refer Out]
        a5[Draft Engagement Letter]
        a6[Open Matter in System]
        a7[Assign Staff and Court Deadlines]
        a8[Perform Legal Work]
        a9[Record Time and Disbursements]
        a10[Review Pre-Bill Report]
        a11{Entries Correct?}
        a12[Adjust or Write-Down Entries]
        a13[Approve Final Invoice]
        a14[Close Matter]
    end

    subgraph PLATFORM["LANE — PLATFORM"]
        p1[Capture and Store Intake Data]
        p2[Run Automated Conflict Search]
        p3[Generate Engagement Letter Template]
        p4[Create Matter Record and Number]
        p5[Sync Court Dates to Calendar]
        p6[Log Time and Expense Entries]
        p7[Compile Pre-Bill Report]
        p8[Generate LEDES 1998B Invoice]
        p9[Deliver Invoice via Secure Portal]
        p10[Post Payment and Update IOLTA Ledger]
        p11[Archive Matter with Audit Trail]
    end

    subgraph COURT["LANE — COURT"]
        ct1[Issue Docket Number and Scheduling Order]
        ct2[Accept Filed Documents]
        ct3[Update Case Status on Docket]
    end

    c1 --> a1
    a1 --> p1
    p1 --> a2
    a2 --> p2
    p2 --> a3
    a3 -->|Yes| a4
    a4 --> c8
    a3 -->|No| a5
    a5 --> p3
    p3 --> c3
    c3 --> a6
    c4 --> a6
    a6 --> p4
    ct1 --> p5
    p5 --> a7
    a7 --> a8
    a8 --> a9
    a9 --> p6
    p6 --> p7
    p7 --> a10
    a10 --> a11
    a11 -->|No| a12
    a12 --> a10
    a11 -->|Yes| a13
    a13 --> p8
    p8 --> p9
    p9 --> c5
    c5 --> c6
    c6 -->|Yes| a10
    c6 -->|No| c7
    c7 --> p10
    p10 --> a14
    a14 --> ct2
    ct2 --> ct3
    ct3 --> p11
    p11 --> c8
```

---

## Billing Workflow Activity Diagram

The billing workflow translates attorney time and expense records into legally compliant,
client-ready invoices and reconciled payments. Key design principles:

- **UTBMS codes** are applied at time entry, not at invoicing, ensuring clean LEDES output.
- **Pre-bill review** by the responsible attorney occurs before any figure is shown to the
  partner or client. This is the primary write-down gate.
- **Partner approval** acts as a second quality gate, required for all invoices before
  external delivery.
- **IOLTA deduction** happens at invoice generation time, not at payment receipt, to keep
  trust ledger balances accurate.
- **Disputed invoices** re-enter the attorney review loop — revenue is not recognized until
  the dispute is resolved.

The four lanes are **Attorney**, **Billing Admin**, **Partner**, and **Client**.

Performance benchmarks typically tracked in this workflow:

- Days from billing-cycle close to invoice delivery (target: ≤ 5 business days)
- Pre-bill write-down rate by attorney and practice group
- Days sales outstanding (DSO) by client segment
- Write-off rate as a percentage of billed fees

```mermaid
flowchart TD
    subgraph ATTORNEY["LANE — ATTORNEY"]
        t1([Record Time or Expense])
        t2[Assign UTBMS Task and Activity Code]
        t3[Tag Matter and Billing Rate]
        t4[Submit Entry to Billing System]
        t5[Receive Pre-Bill for Review]
        t6{Entries Accurate?}
        t7[Edit or Write-Down Entries]
        t8[Sign Off on Pre-Bill]
        t9[Review Client Dispute]
        t10{Credit or Adjust?}
        t11[Issue Credit Note]
    end

    subgraph BILLING_ADMIN["LANE — BILLING ADMIN"]
        b1[Pull Unbilled Entries at Cycle Close]
        b2[Group by Matter and Client]
        b3[Check IOLTA Trust Account Balance]
        b4{Apply Trust Funds?}
        b5[Disburse from Trust and Record Transaction]
        b6[Draft Pre-Bill Report]
        b7[Route Pre-Bill to Responsible Attorney]
        b8[Receive Attorney-Approved Pre-Bill]
        b9[Route to Partner for Approval]
        b10[Receive Partner Approval]
        b11[Generate LEDES 1998B Invoice]
        b12[Deliver Invoice via Portal and Email]
        b13[Monitor Payment Aging Report]
        b14{Payment in 30 Days?}
        b15[Send Reminder Notice]
        b16{Escalate to Collections?}
        b17[Record Write-Off or Bad Debt]
        b18[Post Payment and Reconcile AR]
        b19([Invoice Cycle Complete])
    end

    subgraph PARTNER["LANE — PARTNER"]
        pa1[Receive Pre-Bill for Approval]
        pa2{Approve as Submitted?}
        pa3[Return with Adjustment Notes]
        pa4[Approve Invoice Release]
    end

    subgraph CLIENT["LANE — CLIENT"]
        cl1[Receive Invoice via Portal]
        cl2{Dispute Any Charges?}
        cl3[Submit Dispute via Portal]
        cl4[Submit Payment — ACH / Card / Check]
        cl5([Payment Confirmed])
    end

    t1 --> t2 --> t3 --> t4
    t4 --> b1
    b1 --> b2 --> b3
    b3 --> b4
    b4 -->|Yes| b5
    b5 --> b6
    b4 -->|No| b6
    b6 --> b7
    b7 --> t5
    t5 --> t6
    t6 -->|No| t7
    t7 --> t5
    t6 -->|Yes| t8
    t8 --> b8
    b8 --> b9
    b9 --> pa1
    pa1 --> pa2
    pa2 -->|No| pa3
    pa3 --> t5
    pa2 -->|Yes| pa4
    pa4 --> b10
    b10 --> b11 --> b12
    b12 --> cl1
    cl1 --> cl2
    cl2 -->|Yes| cl3
    cl3 --> t9
    t9 --> t10
    t10 -->|Yes| t11
    t11 --> b12
    t10 -->|No| cl1
    cl2 -->|No| cl4
    cl4 --> b13
    cl4 --> cl5
    b13 --> b14
    b14 -->|Yes| b18
    b18 --> b19
    b14 -->|No| b15
    b15 --> b16
    b16 -->|Yes| b17
    b17 --> b19
    b16 -->|No| b15
```

---

## Court Deadline Management Activity Diagram

Missed court deadlines are among the leading causes of legal malpractice claims. This
workflow models how the platform captures deadline triggers, calculates due dates,
delivers escalating notifications, and confirms timely completion.

Deadline types covered include:

- **Statute of limitations** — computed from the date of injury or accrual
- **Discovery cutoffs** — calculated from scheduling order issue date
- **Motion practice deadlines** — computed from filing or service date
- **Trial dates** — fixed calendar entries
- **Appeal windows** — computed from judgment entry date

The escalation ladder is intentional: unacknowledged reminders at the 7-day and
1-day marks surface automatically to the supervising partner, who can authorize an
extension motion or activate the firm's missed-deadline protocol. The system never
silently drops a critical deadline.

The four lanes are **Trigger Source**, **Platform**, **Attorney/Paralegal**, and
**Supervising Partner**.

Compliance notes:

- All deadline entries include the rule or statute that generated them.
- Completion must be confirmed by the responsible attorney, not auto-cleared by the system.
- Missed deadlines trigger a mandatory risk management log entry.
- Reminder intervals are configurable per deadline type and jurisdiction.

```mermaid
flowchart TD
    subgraph TRIGGER_SOURCE["LANE — TRIGGER SOURCE"]
        tr1([Court Order / Rule / Statute Event])
        tr2[Identify Deadline Type and Governing Rule]
        tr3[Calculate Due Date from Rule and Event Date]
        tr4[Assign Responsible Attorney and Paralegal]
    end

    subgraph PLATFORM["LANE — PLATFORM"]
        pl1[Create Calendar Event on Matter Docket]
        pl2[Link Deadline to Docket Entry and Document]
        pl3[Set Reminder Intervals: 30 / 14 / 7 / 1 Day]
        pl4{30-Day Reminder Due?}
        pl5[Send 30-Day Notification]
        pl6{14-Day Reminder Due?}
        pl7[Send 14-Day Notification]
        pl8{7-Day Reminder Due?}
        pl9[Send 7-Day Notification]
        pl10{1-Day Reminder Due?}
        pl11[Send Critical Alert and Escalate to Partner]
        pl12[Mark Deadline Cleared in Docket]
        pl13[Flag Overdue and Open Risk Alert]
    end

    subgraph ATTORNEY["LANE — ATTORNEY / PARALEGAL"]
        at1[Receive Notification via Email and In-App]
        at2[Acknowledge Reminder]
        at3[Prepare Filing or Required Action]
        at4[File with Court or Complete Action]
        at5[Log Completion Reference in System]
        at6{Filed On Time?}
        at7[Mark Deadline Met]
        at8[Escalate — Missed Deadline Protocol]
    end

    subgraph PARTNER["LANE — SUPERVISING PARTNER"]
        pt1[Receive Escalation Alert]
        pt2[Assess Situation and Available Options]
        pt3{Extension Possible?}
        pt4[File Motion for Extension with Court]
        pt5[Initiate Remediation and Risk Reporting]
    end

    tr1 --> tr2 --> tr3 --> tr4
    tr4 --> pl1
    pl1 --> pl2 --> pl3
    pl3 --> pl4
    pl4 -->|Yes| pl5
    pl5 --> pl6
    pl6 -->|Yes| pl7
    pl7 --> pl8
    pl8 -->|Yes| pl9
    pl9 --> pl10
    pl10 -->|Yes| pl11
    pl5 --> at1
    pl7 --> at1
    pl9 --> at1
    pl11 --> pt1
    at1 --> at2
    at2 --> at3
    at3 --> at4
    at4 --> at5
    at5 --> at6
    at6 -->|Yes| at7
    at7 --> pl12
    at6 -->|No| at8
    at8 --> pl13
    pl13 --> pt1
    pt1 --> pt2
    pt2 --> pt3
    pt3 -->|Yes| pt4
    pt4 --> at3
    pt3 -->|No| pt5
    pt5 --> pl13
```

---

## Summary

| Diagram | Primary Actor | Critical Gate | Compliance Anchor |
|---|---|---|---|
| Case Lifecycle | Attorney | Conflict check + engagement letter | ABA Model Rules 1.7, 1.15 |
| Billing Workflow | Billing Admin | Partner invoice approval | LEDES/UTBMS billing standards |
| Court Deadline Management | Platform | 1-day escalation to partner | ABA Model Rule 1.3 (Diligence) |

The three diagrams together cover the entire revenue cycle of a litigation or transactional
matter: intake and onboarding, active-phase time capture and billing, and the parallel
docket management track that governs court-facing obligations. All platform automation is
designed to augment attorney judgment, not replace the human approval gates required by
professional responsibility rules.
