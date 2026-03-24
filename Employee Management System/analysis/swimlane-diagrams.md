# Swimlane Diagrams

## Overview
Swimlane / BPMN diagrams showing cross-department workflows in the Employee Management System.

---

## 1. Leave Approval Swimlane

```mermaid
sequenceDiagram
    participant E as Employee
    participant S as EMS System
    participant M as Manager
    participant HR as HR Staff

    E->>S: Submit Leave Request
    S->>S: Validate policy & balance
    S->>M: Notify - Pending Approval
    M->>S: Review request & team calendar
    alt Approve
        M->>S: Approve with optional comment
        S->>S: Deduct leave balance
        S->>E: Notify - Leave Approved
    else Reject
        M->>S: Reject with reason
        S->>E: Notify - Leave Rejected
    else Delegate
        M->>S: Delegate to HR
        S->>HR: Notify - Approval Delegated
        HR->>S: Approve or Reject
        S->>E: Notify - Decision
    end
```

---

## 2. Payroll Processing Swimlane

```mermaid
sequenceDiagram
    participant PO as Payroll Officer
    participant S as EMS System
    participant HR as HR Staff
    participant E as Employee
    participant Bank as Banking System

    PO->>S: Initiate Payroll Run
    S->>S: Lock attendance & leave data
    S->>S: Calculate gross pay, deductions, net pay
    S->>PO: Display payroll summary & exceptions
    PO->>S: Resolve exceptions & approve payroll
    S->>S: Generate payslips
    S->>E: Deliver payslips via email & ESS
    S->>Bank: Submit bank transfer file
    S->>PO: Generate compliance reports
    S->>HR: Notify payroll finalized
```

---

## 3. Performance Appraisal Swimlane

```mermaid
sequenceDiagram
    participant HR as HR Staff
    participant S as EMS System
    participant E as Employee
    participant M as Manager

    HR->>S: Configure & launch review cycle
    S->>E: Notify - Complete self-assessment
    E->>S: Submit self-assessment with KRA ratings
    S->>M: Notify - Self-assessment ready for review
    M->>S: Rate KRAs, add comments, recommend action
    S->>HR: Notify - Manager review submitted
    HR->>S: Conduct calibration & finalize ratings
    S->>S: Lock ratings & generate appraisal letters
    S->>E: Notify - Appraisal available
    E->>S: View final rating & feedback
```

---

## 4. Employee Onboarding Swimlane

```mermaid
sequenceDiagram
    participant HR as HR Staff
    participant S as EMS System
    participant IT as IT Team
    participant E as New Employee
    participant M as Manager

    HR->>S: Create employee profile
    S->>S: Generate Employee ID & assign policies
    S->>E: Send welcome email with ESS credentials
    S->>IT: Assign IT provisioning tasks
    S->>HR: Assign document collection tasks
    S->>E: Assign profile completion tasks
    S->>M: Assign team introduction tasks
    IT->>S: Complete equipment & access setup
    E->>S: Complete profile & upload documents
    HR->>S: Verify documents & mark complete
    M->>S: Complete team introduction
    S->>HR: All tasks complete - onboarding done
```

---

## 5. Expense Claim Reimbursement Swimlane

```mermaid
sequenceDiagram
    participant E as Employee
    participant S as EMS System
    participant M as Manager
    participant PO as Payroll Officer

    E->>S: Submit expense claim with receipts
    S->>M: Notify - Pending claim approval
    M->>S: Review claim & receipts
    alt Approve
        M->>S: Approve claim
        S->>PO: Add to next payroll run
        PO->>S: Finalize payroll with reimbursement
        S->>E: Notify - Reimbursement processed in payslip
    else Reject
        M->>S: Reject with reason
        S->>E: Notify - Claim rejected with reason
    end
```

---

## 6. PIP (Performance Improvement Plan) Swimlane

```mermaid
sequenceDiagram
    participant M as Manager
    participant S as EMS System
    participant E as Employee
    participant HR as HR Staff

    M->>S: Initiate PIP for employee
    S->>HR: Notify - PIP initiated, review required
    HR->>S: Review & approve PIP objectives
    S->>E: Notify - PIP initiated with objectives
    loop Monthly Check-ins
        M->>S: Record check-in with progress notes
        S->>E: Notify - Check-in recorded
        E->>S: Acknowledge or add comments
    end
    M->>S: Record PIP outcome (completed / extended / terminated)
    S->>HR: Notify - PIP outcome recorded
    HR->>S: Finalize PIP outcome & update employee record
    S->>E: Notify - PIP closed with outcome
```
