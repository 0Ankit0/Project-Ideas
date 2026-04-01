# Sequence Diagrams

## Overview

Internal component interaction sequence diagrams for key workflows in the Finance Management System. All diagrams model the flow between services, repositories, and infrastructure components. Error paths and compensating actions are shown for each critical workflow.

---

## 1. Post Journal Entry

Posts a validated journal entry to the general ledger. Includes field validation, debit/credit balance check, period-open guard, optional approval routing, and event publication for downstream consumers.

```mermaid
sequenceDiagram
    autonumber
    participant API as JournalAPI
    participant VAL as ValidationEngine
    participant BRE as BusinessRulesEngine
    participant REPO as JournalRepository
    participant LEDGER as LedgerService
    participant PERIOD as PeriodManager
    participant EVT as EventBus

    API->>+VAL: validateJournalEntry(entry)
    VAL->>VAL: checkRequiredFields()
    VAL->>VAL: validateLineItems(lines[])
    VAL->>VAL: validateCurrencyCodes()

    alt Validation fails
        VAL-->>API: ValidationError(errors[])
    else Validation passes
        VAL-->>-API: ValidationResult(valid: true)
    end

    API->>+BRE: applyBusinessRules(entry)
    BRE->>BRE: checkDebitCreditBalance()

    alt Entry is not balanced
        BRE-->>API: BalanceError("Debits != Credits")
    end

    BRE->>+PERIOD: isPeriodOpen(entry.accountingPeriodId)
    PERIOD-->>-BRE: PeriodStatus

    alt Period is closed
        BRE-->>API: PeriodClosedError(periodId, status)
    end

    BRE->>BRE: validateAccountCodesExist(accountIds[])
    BRE->>BRE: validateExchangeRates(currency, exchangeRate)
    BRE->>BRE: checkApprovalRequired(amount, entryType, userId)
    BRE-->>-API: RulesResult(passed: true, requiresApproval: false)

    API->>+REPO: save(entry, status=DRAFT)
    REPO-->>-API: JournalEntry(id, entryNumber)

    API->>+REPO: findById(entryId)
    REPO-->>-API: JournalEntry

    API->>+LEDGER: postEntry(entry)
    activate LEDGER
    LEDGER->>LEDGER: beginTransaction()

    loop For each JournalLine
        LEDGER->>LEDGER: updateLedgerBalance(accountId, debitCredit, amount)
    end

    LEDGER->>+REPO: updateStatus(entryId, POSTED, postedBy, postedAt)
    REPO-->>-LEDGER: void

    LEDGER->>LEDGER: commitTransaction()
    deactivate LEDGER
    LEDGER-->>-API: PostingResult(success: true, entryNumber)

    API->>+EVT: publish(JournalEntryPostedEvent)
    Note over EVT: Subscribers: BudgetService, ReportingService, TaxService
    EVT-->>-API: EventId

    Note over API: HTTP 200 OK — JournalEntry response body
```

---

## 2. Accounting Period Close

Executes the accounting period-end close sequence. Validates sub-ledger reconciliation, runs checklist items, collects CFO approval, locks the period, and publishes the close event to trigger downstream reporting.

```mermaid
sequenceDiagram
    autonumber
    participant CLOSE as PeriodCloseService
    participant CHECK as ChecklistValidator
    participant SUB as SubLedgerReconciler
    participant LEDGER as LedgerService
    participant PERIOD as PeriodManager
    participant APPROVAL as ApprovalService
    participant EVT as EventBus

    CLOSE->>+CHECK: runPreCloseChecklist(periodId)
    activate CHECK
    CHECK->>CHECK: verifyAllJournalsPosted()
    CHECK->>CHECK: verifyBankReconciliationsComplete()
    CHECK->>CHECK: verifyFixedAssetDepreciationRun()
    CHECK->>CHECK: verifyARAgingReviewed()
    CHECK->>CHECK: verifyAPAgingReviewed()
    CHECK->>CHECK: verifyIntercompanyEliminations()

    alt Checklist items incomplete
        CHECK-->>CLOSE: ChecklistError(failedItems[])
        Note over CLOSE: Process halted; controller notified
    else All items complete
        CHECK-->>-CLOSE: ChecklistResult(allPassed: true)
    end

    CLOSE->>+SUB: reconcileSubLedgers(periodId)
    activate SUB
    SUB->>SUB: reconcileAccountsPayable()
    SUB->>SUB: reconcileAccountsReceivable()
    SUB->>SUB: reconcileFixedAssets()
    SUB->>SUB: reconcilePayroll()

    alt Reconciliation differences found
        SUB-->>CLOSE: ReconciliationError(differences[])
        Note over CLOSE: Out-of-balance items must be cleared before close
    else Clean reconciliation
        SUB-->>-CLOSE: ReconciliationResult(differences: 0)
    end

    CLOSE->>+LEDGER: generateTrialBalance(periodId)
    LEDGER->>LEDGER: aggregateAllAccountBalances()
    LEDGER->>LEDGER: verifyDebitCreditEquality()

    alt Trial balance out of balance
        LEDGER-->>CLOSE: TrialBalanceError(debitTotal, creditTotal, delta)
    else Balanced
        LEDGER-->>-CLOSE: TrialBalance(debitTotal, creditTotal)
    end

    CLOSE->>+APPROVAL: requestCloseApproval(periodId, trialBalance)
    APPROVAL->>APPROVAL: notifyController()
    APPROVAL->>APPROVAL: notifyCFO()
    APPROVAL->>APPROVAL: awaitApprovals(timeout: 48h)

    alt Approval rejected
        APPROVAL-->>CLOSE: ApprovalRejected(reason, rejectedBy)
        CLOSE->>CLOSE: logRejection(periodId, reason)
    else Approved
        APPROVAL-->>-CLOSE: ApprovalGranted(approvedBy, approvedAt)
    end

    CLOSE->>+PERIOD: softClose(periodId, approvedBy)
    PERIOD->>PERIOD: setStatus(SOFT_CLOSED)
    PERIOD->>PERIOD: recordCloseTimestamp()
    PERIOD-->>-CLOSE: PeriodClosed(status: SOFT_CLOSED)

    Note over CLOSE: Hard close follows after external audit sign-off

    CLOSE->>+LEDGER: finalizeBalances(periodId)
    LEDGER->>LEDGER: lockLedgerBalances(periodId)
    LEDGER->>LEDGER: propagateOpeningBalances(nextPeriodId)
    LEDGER-->>-CLOSE: BalancesFinalized

    CLOSE->>+EVT: publish(PeriodClosedEvent)
    Note over EVT: Triggers: ReportGeneration, TaxReturn, BudgetVarianceReport
    EVT-->>-CLOSE: EventId
```

---

## 3. Bank Statement Reconciliation

Imports a bank statement file, runs the matching engine against unreconciled ledger entries, and creates reconciliation records. Unmatched items are flagged for manual review.

```mermaid
sequenceDiagram
    autonumber
    participant API as ReconciliationAPI
    participant IMPORT as ImportService
    participant PARSE as ParseService
    participant MATCH as MatchingEngine
    participant REPO as ReconciliationRepository
    participant LEDGER as LedgerService
    participant NOTIFY as NotificationService

    API->>+IMPORT: importStatement(file, bankAccountId, format)
    IMPORT->>IMPORT: validateFileFormat(file)
    IMPORT->>IMPORT: checkDuplicateImport(bankAccountId, statementDate)

    alt Duplicate statement detected
        IMPORT-->>API: DuplicateImportError(existingStatementId)
    end

    IMPORT->>+PARSE: parseStatement(file, format)
    activate PARSE

    alt Format is OFX
        PARSE->>PARSE: parseOFX(file)
    else Format is CSV
        PARSE->>PARSE: parseCSV(file, mappingProfile)
    else Format is MT940
        PARSE->>PARSE: parseMT940(file)
    end

    PARSE->>PARSE: normalizeTransactions()
    PARSE->>PARSE: validateTransactionDates(startDate, endDate)
    PARSE->>PARSE: verifyOpeningClosingBalance()
    PARSE-->>-IMPORT: ParsedStatement(lines[], openingBalance, closingBalance)

    IMPORT->>+REPO: saveStatement(bankAccountId, parsedStatement)
    REPO-->>-IMPORT: BankStatement(id, linesCount)
    IMPORT-->>-API: ImportResult(statementId, linesImported)

    API->>+MATCH: runMatching(statementId, bankAccountId)
    MATCH->>+LEDGER: getUnreconciledEntries(bankAccountId, dateRange)
    LEDGER-->>-MATCH: JournalLine[]

    MATCH->>+REPO: getStatementLines(statementId)
    REPO-->>-MATCH: BankStatementLine[]

    loop For each statement line
        MATCH->>MATCH: findExactAmountMatch(line, ledgerEntries)

        alt Exact match found
            MATCH->>MATCH: markMatched(statementLine, journalLine, EXACT)
        else No exact match
            MATCH->>MATCH: findFuzzyMatch(line, tolerance: 0.01)
            alt Fuzzy match found
                MATCH->>MATCH: markMatchedPendingReview(statementLine, journalLine, FUZZY)
            else No match
                MATCH->>MATCH: markUnmatched(statementLine)
            end
        end
    end

    MATCH->>MATCH: calculateReconciliationSummary()
    MATCH->>+REPO: saveMatchResults(statementId, matches[])
    REPO-->>-MATCH: void
    MATCH-->>-API: MatchingResult(matched, unmatched, pendingReview)

    API->>+REPO: createReconciliation(statementId, summary)
    REPO-->>-API: Reconciliation(id, status)

    alt Unmatched items exist
        API->>+NOTIFY: notifyController(reconciliationId, unmatchedCount)
        NOTIFY->>NOTIFY: sendEmailAlert()
        NOTIFY->>NOTIFY: createInboxTask(assignedTo: controller)
        NOTIFY-->>-API: NotificationSent
    end
```

---

## 4. Budget Overrun Check

Validates whether a requested expense exceeds the available budget before allowing journal entry posting. Routes to an approval workflow when a soft-override policy is configured.

```mermaid
sequenceDiagram
    autonumber
    participant EXPENSE as ExpenseService
    participant BUDGET as BudgetService
    participant APPROVAL as ApprovalWorkflow
    participant JOURNAL as JournalService
    participant EVT as EventBus

    EXPENSE->>+BUDGET: checkBudgetAvailability(costCenterId, accountId, amount, periodId)
    activate BUDGET
    BUDGET->>BUDGET: findActiveBudgetLine(costCenterId, accountId, periodId)

    alt No active budget found
        BUDGET-->>EXPENSE: BudgetCheckResult(status: NO_BUDGET)
        Note over EXPENSE: Org policy determines: allow or block
    end

    BUDGET->>BUDGET: calculateCommittedAmount(costCenterId, accountId, periodId)
    BUDGET->>BUDGET: calculateActualAmount(costCenterId, accountId, periodId)
    BUDGET->>BUDGET: computeAvailableBalance(budgeted - actual - committed)
    BUDGET-->>-EXPENSE: BudgetCheckResult(available, budgeted, actual, committed, utilizationPct)

    alt Available balance >= requested amount
        EXPENSE->>EXPENSE: proceedWithExpense()
        EXPENSE->>+JOURNAL: createAndPostJournalEntry(expenseData)
        JOURNAL-->>-EXPENSE: JournalEntry(id)
        EXPENSE->>+BUDGET: updateCommitted(budgetLineId, amount)
        BUDGET-->>-EXPENSE: void

    else Budget overrun detected
        EXPENSE->>EXPENSE: evaluateOverrunPolicy(orgId, costCenterId)

        alt Policy is HARD_BLOCK
            EXPENSE-->>EXPENSE: BudgetOverrunError(shortfall, budgetLineId)
            Note over EXPENSE: Transaction rejected; user notified

        else Policy is SOFT_OVERRIDE
            EXPENSE->>+APPROVAL: initiateOverrunApproval(costCenterId, accountId, amount, shortfall)
            APPROVAL->>APPROVAL: identifyApprovers(costCenterId, overrunAmount)
            APPROVAL->>APPROVAL: createApprovalTask(approvers[], expenseDetails)
            APPROVAL->>APPROVAL: notifyApprovers()
            APPROVAL-->>-EXPENSE: ApprovalRequest(id, status: PENDING)

            Note over EXPENSE, APPROVAL: Async: approval decision delivered via webhook

            alt Approval granted
                APPROVAL->>+JOURNAL: createAndPostJournalEntry(expenseData, overrideApprovalId)
                JOURNAL-->>-APPROVAL: JournalEntry(id)
                APPROVAL->>+BUDGET: recordOverrun(budgetLineId, amount, approvalId)
                BUDGET-->>-APPROVAL: void
                APPROVAL->>+EVT: publish(BudgetOverrunApprovedEvent)
                EVT-->>-APPROVAL: EventId
            else Approval rejected
                APPROVAL->>+EVT: publish(BudgetOverrunRejectedEvent)
                EVT-->>-APPROVAL: EventId
            end
        end
    end
```

---

## 5. Fixed Asset Depreciation Run

Executes the monthly depreciation batch for all active assets in an accounting period. Calculates depreciation per method, generates journal entries, updates asset book values, and marks fully depreciated assets.

```mermaid
sequenceDiagram
    autonumber
    participant SCHED as DepreciationScheduler
    participant REPO as FixedAssetRepository
    participant ENGINE as DepreciationEngine
    participant JOURNAL as JournalService
    participant LEDGER as LedgerService
    participant EVT as EventBus

    SCHED->>+REPO: findAssetsForDepreciation(organizationId, periodId)
    REPO->>REPO: queryActiveAndPartiallyDepreciatedAssets()
    REPO->>REPO: excludeAlreadyDepreciatedThisPeriod()
    REPO->>REPO: excludeDisposedAssets()
    REPO-->>-SCHED: FixedAsset[]

    SCHED->>+REPO: createDepreciationRun(organizationId, periodId, assetCount)
    REPO-->>-SCHED: DepreciationRun(runId, status: STARTED)

    loop For each FixedAsset
        SCHED->>+ENGINE: calculateDepreciation(asset, period)
        ENGINE->>ENGINE: loadDepreciationMethod(asset.depreciationMethod)

        alt STRAIGHT_LINE
            ENGINE->>ENGINE: calcStraightLine(cost, residual, usefulLife)
        else DECLINING_BALANCE
            ENGINE->>ENGINE: calcDecliningBalance(bookValue, rate)
        else DOUBLE_DECLINING_BALANCE
            ENGINE->>ENGINE: calcDoubleDeclining(bookValue, usefulLife)
        else SUM_OF_YEARS_DIGITS
            ENGINE->>ENGINE: calcSYD(cost, residual, usefulLife, remaining)
        end

        ENGINE->>ENGINE: capAtResidualValue(amount, bookValue, residual)
        ENGINE-->>-SCHED: DepreciationResult(assetId, amount, newBookValue)

        alt Depreciation amount > 0
            SCHED->>+JOURNAL: createDepreciationEntry(asset, amount, periodId)
            JOURNAL->>JOURNAL: buildJournalLines(debitExpenseAccount, creditAccumDepreciation)
            JOURNAL->>+LEDGER: postEntry(journalEntry)
            LEDGER-->>-JOURNAL: PostingResult
            JOURNAL-->>-SCHED: JournalEntry(id)

            SCHED->>+REPO: saveDepreciation(assetId, runId, amount, journalEntryId)
            REPO-->>-SCHED: Depreciation(id)

            SCHED->>+REPO: updateAssetBookValue(assetId, newBookValue, accumulatedDepreciation)
            REPO-->>-SCHED: void

            alt Asset is now fully depreciated
                SCHED->>+REPO: updateAssetStatus(assetId, FULLY_DEPRECIATED)
                REPO-->>-SCHED: void
            end
        end
    end

    SCHED->>+REPO: completeDepreciationRun(runId, totalAmount, processed, failed)
    REPO-->>-SCHED: DepreciationRun(status: COMPLETED)

    SCHED->>+EVT: publish(DepreciationRunCompletedEvent)
    Note over EVT: Triggers: DepreciationReport generation, GL balance refresh, asset register update
    EVT-->>-SCHED: EventId
```
