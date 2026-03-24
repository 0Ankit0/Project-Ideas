# Swimlane Diagrams

## Overview
Cross-departmental BPMN-style workflows showing how Finance Management processes span multiple roles and systems.

---

## Invoice-to-Payment Workflow

```mermaid
graph LR
    subgraph Vendor
        V1[Send Invoice]
        V2[Receive Remittance]
    end

    subgraph Accountant
        A1[Record Invoice]
        A2[Perform 3-Way Match]
        A3[Upload Invoice Document]
        A4[Submit for Approval]
        A5[Post AP GL Entry]
    end

    subgraph Finance_Manager
        FM1[Review High-Value Invoices]
        FM2[Approve Payment Batch]
        FM3[Submit Bank File]
    end

    subgraph Banking_System
        B1[Process ACH Transfer]
        B2[Confirm Clearance]
    end

    subgraph System
        S1[Duplicate Check]
        S2[Route for Approval]
        S3[Generate Bank File]
        S4[Update Invoice Status]
        S5[Send Remittance Email]
    end

    V1 --> A1
    A1 --> S1
    S1 --> A2
    A2 --> A3
    A3 --> A4
    A4 --> S2
    S2 -->|Above Threshold| FM1
    FM1 --> FM2
    S2 -->|Below Threshold| FM2
    FM2 --> S3
    S3 --> FM3
    FM3 --> B1
    B1 --> B2
    B2 --> S4
    S4 --> A5
    S4 --> S5
    S5 --> V2
```

---

## Budget Planning and Approval Workflow

```mermaid
graph LR
    subgraph Budget_Manager
        BM1[Create Draft Budget]
        BM2[Enter Monthly Amounts]
        BM3[Submit for Review]
        BM4[Revise Based on Comments]
    end

    subgraph Finance_Manager
        FM1[Review Budget Lines]
        FM2[Approve or Return with Comments]
        FM3[Consolidate All Department Budgets]
    end

    subgraph CFO
        CFO1[Review Consolidated Budget]
        CFO2[Approve or Reject]
        CFO3[Set Executive Constraints]
    end

    subgraph System
        S1[Route to Finance Manager]
        S2[Route to CFO]
        S3[Activate Budget]
        S4[Notify All Stakeholders]
        S5[Begin Actuals Tracking]
    end

    BM1 --> BM2
    BM2 --> BM3
    BM3 --> S1
    S1 --> FM1
    FM1 --> FM2
    FM2 -->|Approved| FM3
    FM2 -->|Returned| BM4
    BM4 --> BM3
    FM3 --> S2
    S2 --> CFO1
    CFO1 --> CFO2
    CFO2 -->|Rejected| FM1
    CFO2 -->|Approved| S3
    S3 --> S4
    S4 --> S5
```

---

## Expense Claim and Reimbursement Workflow

```mermaid
graph LR
    subgraph Employee
        E1[Create Expense Report]
        E2[Upload Receipts]
        E3[Submit Claim]
        E4[Receive Reimbursement]
    end

    subgraph Dept_Head
        DH1[Receive Approval Request]
        DH2[Review Items and Receipts]
        DH3[Approve or Reject]
    end

    subgraph Finance_Manager
        FM1[Review High-Value Claims]
        FM2[Approve or Reject]
        FM3[Queue for Reimbursement]
    end

    subgraph Accountant
        AC1[Process Reimbursement Batch]
        AC2[Post GL Entry]
    end

    subgraph System
        S1[Policy Check]
        S2[Route to Dept Head]
        S3[Route to Finance Manager]
        S4[Initiate Bank Transfer]
        S5[Notify Employee]
    end

    E1 --> E2
    E2 --> E3
    E3 --> S1
    S1 --> S2
    S2 --> DH1
    DH1 --> DH2
    DH2 --> DH3
    DH3 -->|Rejected| E1
    DH3 -->|Approved| S3
    S3 -->|Threshold Exceeded| FM1
    FM1 --> FM2
    FM2 -->|Rejected| E1
    FM2 -->|Approved| FM3
    S3 -->|Below Threshold| FM3
    FM3 --> AC1
    AC1 --> S4
    S4 --> AC2
    AC2 --> S5
    S5 --> E4
```

---

## Payroll Processing Workflow

```mermaid
graph LR
    subgraph HR_System
        HR1[Provide Employee Master]
        HR2[Submit Timesheets]
    end

    subgraph Accountant
        AC1[Initiate Payroll Run]
        AC2[Review Pre-Run Validation]
        AC3[Review Payroll Register]
        AC4[Submit for Approval]
        AC5[Post GL Entries]
    end

    subgraph Finance_Manager
        FM1[Review Payroll Register]
        FM2[Approve Payroll Run]
    end

    subgraph Banking_System
        B1[Process Direct Deposits]
        B2[Confirm Disbursements]
    end

    subgraph System
        S1[Calculate Gross Pay]
        S2[Apply Deductions and Tax]
        S3[Generate Register]
        S4[Generate ACH File]
        S5[Send Pay Stubs]
        S6[Generate Tax Filings]
    end

    HR1 --> AC1
    HR2 --> AC1
    AC1 --> S1
    S1 --> S2
    S2 --> S3
    S3 --> AC2
    AC2 --> AC3
    AC3 --> AC4
    AC4 --> FM1
    FM1 --> FM2
    FM2 --> S4
    S4 --> B1
    B1 --> B2
    B2 --> AC5
    B2 --> S5
    B2 --> S6
```

---

## Period Close Workflow

```mermaid
graph LR
    subgraph Accountant
        AC1[Reconcile Subledgers]
        AC2[Post Accruals]
        AC3[Post Depreciation]
        AC4[Review Trial Balance]
        AC5[Post Adjustments]
    end

    subgraph Finance_Manager
        FM1[Initiate Close Checklist]
        FM2[Review Draft Financials]
        FM3[Sign Off on Statements]
        FM4[Hard-Close Period]
    end

    subgraph CFO
        CFO1[Review Final Statements]
        CFO2[Approve Period Close]
    end

    subgraph System
        S1[Generate Checklist]
        S2[Run Trial Balance]
        S3[Generate Financial Statements]
        S4[Lock Period]
        S5[Archive Records]
    end

    FM1 --> S1
    S1 --> AC1
    AC1 --> AC2
    AC2 --> AC3
    AC3 --> S2
    S2 --> AC4
    AC4 --> FM2
    FM2 -->|Adjustments Needed| AC5
    AC5 --> S2
    FM2 -->|Satisfied| S3
    S3 --> FM3
    FM3 --> CFO1
    CFO1 -->|Requires Changes| FM2
    CFO1 -->|Approves| CFO2
    CFO2 --> FM4
    FM4 --> S4
    S4 --> S5
```

---

## Tax Filing Workflow

```mermaid
graph LR
    subgraph Accountant
        AC1[Review Tax Liability Report]
        AC2[Reconcile Input vs Output Tax]
        AC3[Prepare Filing Data]
        AC4[Submit to Finance Manager]
    end

    subgraph Finance_Manager
        FM1[Review Tax Return]
        FM2[Approve Filing]
    end

    subgraph Tax_Authority
        TA1[Receive Filing]
        TA2[Issue Acknowledgment]
        TA3[Process Tax Payment]
    end

    subgraph System
        S1[Calculate Tax Liability]
        S2[Generate Filing Report]
        S3[Submit E-Filing]
        S4[Record Acknowledgment]
        S5[Post Tax Payment Entry]
    end

    S1 --> AC1
    AC1 --> AC2
    AC2 --> AC3
    AC3 --> S2
    S2 --> AC4
    AC4 --> FM1
    FM1 --> FM2
    FM2 --> S3
    S3 --> TA1
    TA1 --> TA2
    TA2 --> S4
    FM2 --> TA3
    TA3 --> S5
```

---

## Bank Reconciliation Workflow

```mermaid
graph LR
    subgraph Bank
        BK1[Provide Bank Statement]
    end

    subgraph Accountant
        AC1[Import Bank Statement]
        AC2[Review Auto-Matches]
        AC3[Manually Match Unmatched]
        AC4[Post Adjusting Entries]
        AC5[Sign Off on Reconciliation]
    end

    subgraph Finance_Manager
        FM1[Review Reconciliation Report]
        FM2[Approve Reconciliation]
    end

    subgraph System
        S1[Parse Bank Statement]
        S2[Auto-Match Transactions]
        S3[Flag Unmatched Items]
        S4[Calculate Reconciled Balance]
        S5[Generate Reconciliation Report]
    end

    BK1 --> AC1
    AC1 --> S1
    S1 --> S2
    S2 --> AC2
    S2 --> S3
    S3 --> AC3
    AC2 --> AC3
    AC3 --> AC4
    AC4 --> S4
    S4 --> S5
    S5 --> AC5
    AC5 --> FM1
    FM1 --> FM2
```
