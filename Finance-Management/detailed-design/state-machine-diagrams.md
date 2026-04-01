# State Machine Diagrams

## Overview

State transition diagrams for key financial domain objects in the Finance Management System. Each diagram shows valid states, transitions with trigger conditions and guards, entry/exit actions, and terminal states. Diagrams use `stateDiagram-v2` notation.

---

## 1. JournalEntry State Machine

A journal entry moves from composition through approval and posting. Once posted it is immutable; reversal creates a new offsetting entry rather than modifying the original.

```mermaid
stateDiagram-v2
    [*] --> DRAFT : create()

    DRAFT --> PENDING_APPROVAL : submit()
[hasLines && isBalanced && periodIsOpen]
    DRAFT --> DRAFT : saveDraft()
    DRAFT --> [*] : discard()
[no approvals started]

    PENDING_APPROVAL --> APPROVED : approve(userId)
[approver != creator && hasAuthority]
    PENDING_APPROVAL --> REJECTED : reject(userId, reason)
    PENDING_APPROVAL --> DRAFT : recall()
[creator only && within 15 min]

    APPROVED --> POSTED : post(userId)
[period.isPostable()]
    APPROVED --> DRAFT : revise(userId)
[within 1 hour of approval]

    POSTED --> REVERSED : reverse(userId, date, reason)
[period.isOpen() || periodIsReopened]

    REJECTED --> DRAFT : reviseAndResubmit()

    REVERSED --> [*]

    note right of DRAFT
        entry: generateDraftNumber()
        exit: validateBalance()
    end note

    note right of PENDING_APPROVAL
        entry: notifyApprovers()
        entry: setSubmittedAt()
    end note

    note right of POSTED
        entry: updateLedgerBalances()
        entry: publishJournalPostedEvent()
        entry: setPostedAt()
    end note

    note right of REVERSED
        entry: createReversalEntry()
        entry: updateLedgerBalances()
        entry: publishJournalReversedEvent()
    end note
```

**State Reference**

| State | Description |
|---|---|
| DRAFT | Entry is being composed; lines can be added or removed freely |
| PENDING_APPROVAL | Submitted for workflow approval; entry is read-only |
| APPROVED | Approved by an authorised reviewer; awaiting the posting window |
| POSTED | Permanently posted to the general ledger; fully immutable |
| REVERSED | A reversal entry has been created; this entry is effectively voided |
| REJECTED | Rejected by approver; returned to DRAFT with a mandatory reason |

---

## 2. AccountingPeriod State Machine

An accounting period progresses through a controlled close sequence. Re-opening a hard-closed period requires board-level approval and creates an immutable audit trail entry.

```mermaid
stateDiagram-v2
    [*] --> FUTURE : createPeriod()

    FUTURE --> OPEN : open()
[currentDate >= period.startDate]

    OPEN --> SOFT_CLOSED : softClose(userId)
[checklistComplete && approvalGranted]
    OPEN --> OPEN : postJournalEntry()

    SOFT_CLOSED --> HARD_CLOSED : hardClose(userId)
[auditSignOff && allAdjustmentsPosted]
    SOFT_CLOSED --> REOPENED : reopen(userId, reason)
[requires CFO approval]

    HARD_CLOSED --> REOPENED : reopen(userId, reason)
[requires board approval + audit entry]

    REOPENED --> SOFT_CLOSED : softClose(userId)
[adjustments posted && re-approved]
    REOPENED --> HARD_CLOSED : hardClose(userId)

    note right of OPEN
        entry: setOpenedAt()
        entry: propagateOpeningBalances()
        exit: runPreCloseChecklist()
    end note

    note right of SOFT_CLOSED
        entry: lockNonAdjustingEntries()
        entry: notifyControllers()
        entry: publishPeriodSoftClosedEvent()
    end note

    note right of HARD_CLOSED
        entry: lockAllEntries()
        entry: archiveLedgerBalances()
        entry: publishPeriodHardClosedEvent()
    end note

    note right of REOPENED
        entry: createAuditLogEntry(reason, approvedBy)
        entry: notifyAuditTeam()
        entry: publishPeriodReopenedEvent()
    end note
```

---

## 3. Invoice State Machine

Invoices flow from creation through approval to payment settlement. Disputes can interrupt the payment flow and require explicit resolution before the invoice proceeds.

```mermaid
stateDiagram-v2
    [*] --> DRAFT : createInvoice()

    DRAFT --> SUBMITTED : submit()
[hasLines && totalAmount > 0]
    DRAFT --> [*] : delete()
[no payments applied]

    SUBMITTED --> APPROVED : approve(userId)
[approver is authorised]
    SUBMITTED --> DRAFT : reject(userId, reason)
    SUBMITTED --> CANCELLED : cancel(userId, reason)

    APPROVED --> PARTIALLY_PAID : applyPayment(amount)
[0 < amount < totalAmount]
    APPROVED --> PAID : applyPayment(amount)
[amount == amountDue]
    APPROVED --> DISPUTED : dispute(reason)
    APPROVED --> CANCELLED : cancel(userId, reason)
[no payments applied]

    PARTIALLY_PAID --> PAID : applyPayment(amount)
[amountDue == 0]
    PARTIALLY_PAID --> DISPUTED : dispute(reason)

    DISPUTED --> APPROVED : resolveDispute(resolution)
[resolution = VALID]
    DISPUTED --> CANCELLED : resolveDispute(resolution)
[resolution = INVALID]

    PAID --> [*]
    CANCELLED --> [*]

    note right of APPROVED
        entry: createJournalEntry()
        entry: updateVendorOrCustomerBalance()
        entry: publishInvoiceApprovedEvent()
    end note

    note right of PAID
        entry: publishInvoicePaidEvent()
        entry: closeJournalEntry()
        entry: updatePaymentTerm()
    end note

    note right of DISPUTED
        entry: notifyCounterparty()
        entry: freezePaymentSchedule()
        entry: createDisputeCase()
    end note
```

---

## 4. Budget State Machine

A budget is drafted, reviewed, approved, and activated for spend control. Mid-year revisions create a new version while the current version remains active until the revision is approved.

```mermaid
stateDiagram-v2
    [*] --> DRAFT : createBudget()

    DRAFT --> SUBMITTED : submit(userId)
[hasLines && totalAmount > 0]
    DRAFT --> DRAFT : saveDraft()
    DRAFT --> [*] : discard()

    SUBMITTED --> UNDER_REVIEW : startReview(reviewerId)
    SUBMITTED --> DRAFT : returnToDraft(userId, reason)

    UNDER_REVIEW --> APPROVED : approve(userId)
[quorum of approvers reached]
    UNDER_REVIEW --> REVISION_REQUESTED : requestRevision(userId, changes[])
    UNDER_REVIEW --> SUBMITTED : returnForRevision()

    APPROVED --> ACTIVE : activate()
[fiscalYear.isOpen()]
    APPROVED --> REVISION_REQUESTED : requestRevision(userId)

    ACTIVE --> REVISION_REQUESTED : requestRevision(userId, reason)
    ACTIVE --> CLOSED : close()
[fiscalYear.isClosed()]

    REVISION_REQUESTED --> DRAFT : createRevision()
[new version; current frozen]

    CLOSED --> [*]

    note right of ACTIVE
        entry: enableBudgetChecks()
        entry: notifyBudgetOwner()
        entry: publishBudgetActivatedEvent()
    end note

    note right of REVISION_REQUESTED
        entry: freezeCurrentVersion()
        entry: notifyBudgetOwner()
        entry: createRevisionRecord()
    end note

    note right of CLOSED
        entry: archiveBudgetLines()
        entry: publishBudgetClosedEvent()
    end note
```

---

## 5. BankReconciliation State Machine

A bank reconciliation progresses from statement import through automated matching to human review and final completion. Disputes freeze the reconciliation until the bank resolves the discrepancy.

```mermaid
stateDiagram-v2
    [*] --> INITIATED : initiateReconciliation(bankAccountId, statementId)

    INITIATED --> IN_PROGRESS : startMatching()

    IN_PROGRESS --> PARTIALLY_MATCHED : matchingComplete()
[unmatchedItems > 0]
    IN_PROGRESS --> PENDING_REVIEW : matchingComplete()
[fuzzyMatchCount > 0]
    IN_PROGRESS --> COMPLETED : matchingComplete()
[allMatched && balanced]

    PARTIALLY_MATCHED --> PENDING_REVIEW : submitForReview(userId)
    PARTIALLY_MATCHED --> IN_PROGRESS : addManualMatch(userId, lineId, entryId)

    PENDING_REVIEW --> IN_PROGRESS : applyReviewDecisions(userId)
    PENDING_REVIEW --> COMPLETED : approveReconciliation(userId)
[allItemsResolved && balanced]
    PENDING_REVIEW --> DISPUTED : raiseDispute(userId, items[])

    DISPUTED --> PENDING_REVIEW : resolveDispute(userId, resolution)

    COMPLETED --> [*]

    note right of COMPLETED
        entry: lockStatementLines()
        entry: updateLastReconciledDate()
        entry: publishReconciliationCompletedEvent()
    end note

    note right of DISPUTED
        entry: notifyBankOperationsTeam()
        entry: createDisputeTicket()
        entry: suspendAutomatedMatching()
    end note

    note right of PENDING_REVIEW
        entry: notifyController()
        entry: generateExceptionReport()
    end note
```

---

## 6. FixedAsset State Machine

A fixed asset moves from capital proposal through active depreciation to eventual disposal. Each state transition generates a corresponding journal entry to maintain ledger accuracy.

```mermaid
stateDiagram-v2
    [*] --> PROPOSED : proposeAsset(assetData)

    PROPOSED --> ACTIVE : approve(userId)
[capitalised in acquisition journal]
    PROPOSED --> [*] : reject(userId, reason)

    ACTIVE --> PARTIALLY_DEPRECIATED : runDepreciation()
[0 < accumulatedDepr < cost - residual]
    ACTIVE --> DISPOSED : dispose(date, proceeds, method)
[prior to depreciation start]

    PARTIALLY_DEPRECIATED --> FULLY_DEPRECIATED : runDepreciation()
[bookValue == residualValue]
    PARTIALLY_DEPRECIATED --> DISPOSED : dispose(date, proceeds, method)

    FULLY_DEPRECIATED --> DISPOSED : dispose(date, proceeds, method)

    DISPOSED --> [*]

    note right of ACTIVE
        entry: generateAssetCode()
        entry: createAcquisitionJournalEntry()
        entry: buildDepreciationSchedule()
        entry: publishAssetActivatedEvent()
    end note

    note right of PARTIALLY_DEPRECIATED
        entry: updateBookValue()
        entry: postDepreciationJournalEntry()
        entry: updateRemainingLifeMonths()
    end note

    note right of FULLY_DEPRECIATED
        entry: setBookValueToResidualValue()
        entry: stopDepreciationSchedule()
        entry: notifyAssetManager()
    end note

    note right of DISPOSED
        entry: calculateGainLoss()
        entry: createDisposalJournalEntry()
        entry: derecogniseFromAssetRegister()
        entry: publishAssetDisposedEvent()
    end note
```
