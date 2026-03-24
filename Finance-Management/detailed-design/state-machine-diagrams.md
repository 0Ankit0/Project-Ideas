# State Machine Diagrams

## Overview
Entity state transition diagrams for the key financial documents and workflows in the Finance Management System.

---

## Vendor Invoice State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Accountant creates invoice

    DRAFT --> SUBMITTED : Accountant submits for approval
    DRAFT --> VOID : Accountant voids before submission

    SUBMITTED --> MATCH_EXCEPTION : 3-way match variance exceeds tolerance
    SUBMITTED --> PENDING_FM_APPROVAL : Match passes, amount above threshold
    SUBMITTED --> APPROVED : Match passes, amount below threshold (auto-approved)

    MATCH_EXCEPTION --> PENDING_FM_APPROVAL : FM overrides exception
    MATCH_EXCEPTION --> VOID : FM rejects exception

    PENDING_FM_APPROVAL --> APPROVED : Finance Manager approves
    PENDING_FM_APPROVAL --> DRAFT : Finance Manager returns with comments

    APPROVED --> SCHEDULED : Added to payment run
    SCHEDULED --> PARTIALLY_PAID : Partial payment applied
    SCHEDULED --> PAID : Full payment received and cleared

    PARTIALLY_PAID --> PAID : Remaining balance paid

    APPROVED --> VOID : Finance Manager voids approved invoice
    PAID --> [*]
    VOID --> [*]
```

---

## Customer Invoice State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Accountant creates invoice

    DRAFT --> ISSUED : Accountant sends to customer
    DRAFT --> VOID : Cancelled before sending

    ISSUED --> PARTIALLY_PAID : Partial payment recorded
    ISSUED --> PAID : Full payment received
    ISSUED --> OVERDUE : Due date passes without payment

    PARTIALLY_PAID --> PAID : Remaining balance collected
    PARTIALLY_PAID --> OVERDUE : Due date passes

    OVERDUE --> PAID : Late payment received
    OVERDUE --> WRITTEN_OFF : CFO approves bad debt write-off

    PAID --> [*]
    WRITTEN_OFF --> [*]
    VOID --> [*]
```

---

## Budget State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Budget Manager creates budget

    DRAFT --> PENDING_FM_REVIEW : Submitted for Finance Manager review
    DRAFT --> [*] : Deleted as draft

    PENDING_FM_REVIEW --> DRAFT : Returned with comments
    PENDING_FM_REVIEW --> PENDING_CFO_APPROVAL : Finance Manager approves

    PENDING_CFO_APPROVAL --> PENDING_FM_REVIEW : CFO returns to Finance Manager
    PENDING_CFO_APPROVAL --> APPROVED : CFO approves

    APPROVED --> ACTIVE : Fiscal period starts
    ACTIVE --> REVISED : Budget revision submitted
    REVISED --> PENDING_FM_REVIEW : Revision routed for re-approval
    ACTIVE --> CLOSED : Fiscal period ends

    CLOSED --> [*]
```

---

## Expense Claim State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Employee creates claim

    DRAFT --> SUBMITTED : Employee submits claim
    DRAFT --> [*] : Employee deletes draft

    SUBMITTED --> PENDING_DEPT_APPROVAL : Routed to Department Head

    PENDING_DEPT_APPROVAL --> DRAFT : Rejected – returned to employee
    PENDING_DEPT_APPROVAL --> PENDING_FM_APPROVAL : Approved by Dept Head (high-value)
    PENDING_DEPT_APPROVAL --> APPROVED : Approved by Dept Head (below threshold)

    PENDING_FM_APPROVAL --> DRAFT : Rejected – returned to employee
    PENDING_FM_APPROVAL --> APPROVED : Finance Manager approves

    APPROVED --> QUEUED_FOR_PAYMENT : Added to reimbursement batch
    QUEUED_FOR_PAYMENT --> PAID : Reimbursement transferred to employee

    PAID --> [*]
```

---

## Payroll Run State Machine

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Accountant initiates payroll run

    DRAFT --> CALCULATED : Calculations completed
    DRAFT --> CANCELLED : Cancelled before calculation

    CALCULATED --> PENDING_APPROVAL : Submitted to Finance Manager

    PENDING_APPROVAL --> CALCULATED : Returned for corrections
    PENDING_APPROVAL --> APPROVED : Finance Manager approves

    APPROVED --> SUBMITTED_TO_BANK : Bank file submitted

    SUBMITTED_TO_BANK --> DISBURSED : Bank confirms clearance
    SUBMITTED_TO_BANK --> PARTIALLY_FAILED : Some disbursements failed

    PARTIALLY_FAILED --> DISBURSED : Failed entries reprocessed
    PARTIALLY_FAILED --> FAILED : All retries exhausted

    DISBURSED --> [*]
    FAILED --> [*]
    CANCELLED --> [*]
```

---

## Accounting Period State Machine

```mermaid
stateDiagram-v2
    [*] --> OPEN : Period created and activated

    OPEN --> SOFT_CLOSED : Finance Manager initiates soft-close
    note right of SOFT_CLOSED : Restricted posting\nAdjustments require approval

    SOFT_CLOSED --> OPEN : Reopened for corrections (rare)
    SOFT_CLOSED --> HARD_CLOSED : CFO approves final close

    note right of HARD_CLOSED : No postings allowed\nFully locked

    HARD_CLOSED --> [*]
```

---

## Fixed Asset State Machine

```mermaid
stateDiagram-v2
    [*] --> REGISTERED : Asset acquired and registered

    REGISTERED --> IN_SERVICE : Asset placed in service (depreciation begins)

    IN_SERVICE --> TRANSFERRED : Asset transferred to another dept/location
    TRANSFERRED --> IN_SERVICE : Transfer complete

    IN_SERVICE --> IMPAIRED : Write-down applied
    IMPAIRED --> IN_SERVICE : Impairment reversed

    IN_SERVICE --> FULLY_DEPRECIATED : Net book value reaches residual value
    FULLY_DEPRECIATED --> DISPOSED : Asset sold or scrapped
    IN_SERVICE --> DISPOSED : Early disposal

    DISPOSED --> [*]
```

---

## Payment Run State Machine

```mermaid
stateDiagram-v2
    [*] --> PENDING_APPROVAL : Finance Manager creates payment run

    PENDING_APPROVAL --> APPROVED : Finance Manager approves run
    PENDING_APPROVAL --> CANCELLED : Cancelled before approval

    APPROVED --> BANK_FILE_GENERATED : Bank transfer file generated

    BANK_FILE_GENERATED --> SUBMITTED_TO_BANK : File submitted to banking system
    BANK_FILE_GENERATED --> CANCELLED : Cancelled after file generation

    SUBMITTED_TO_BANK --> CLEARED : Bank confirms all payments cleared
    SUBMITTED_TO_BANK --> PARTIALLY_FAILED : Some payments failed
    SUBMITTED_TO_BANK --> FAILED : All payments failed

    PARTIALLY_FAILED --> CLEARED : Failed payments re-initiated and cleared

    CLEARED --> [*]
    FAILED --> [*]
    CANCELLED --> [*]
```
