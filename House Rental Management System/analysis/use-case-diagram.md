# Use Case Diagram

## Overview
This document contains use case diagrams for all major actors in the house rental management system.

---

## Complete System Use Case Diagram

```mermaid
graph TB
    subgraph Actors
        Owner((Owner))
        Tenant((Tenant))
        MaintStaff((Maintenance Staff))
        Admin((Admin))
        PaymentGW((Payment Gateway))
        EmailSvc((Email Service))
        SMSSvc((SMS Service))
        ESign((E-Signature Provider))
    end

    subgraph "House Rental Management Platform"
        UC1[Manage Properties]
        UC2[Manage Units]
        UC3[Review Applications]
        UC4[Manage Leases]
        UC5[Manage Rent]
        UC6[Manage Bills]
        UC7[Manage Maintenance]
        UC8[View Reports]

        UC10[Browse Listings]
        UC11[Submit Application]
        UC12[Sign Lease]
        UC13[Pay Rent]
        UC14[Pay Bills]
        UC15[Submit Maintenance Request]

        UC20[Manage Tasks]
        UC21[Update Task Status]

        UC30[Manage Users]
        UC31[Verify Documents]
        UC32[Resolve Disputes]
        UC33[Configure Platform]
    end

    Owner --> UC1
    Owner --> UC2
    Owner --> UC3
    Owner --> UC4
    Owner --> UC5
    Owner --> UC6
    Owner --> UC7
    Owner --> UC8

    Tenant --> UC10
    Tenant --> UC11
    Tenant --> UC12
    Tenant --> UC13
    Tenant --> UC14
    Tenant --> UC15

    MaintStaff --> UC20
    MaintStaff --> UC21

    Admin --> UC30
    Admin --> UC31
    Admin --> UC32
    Admin --> UC33

    UC13 --> PaymentGW
    UC14 --> PaymentGW
    UC12 --> ESign
    UC5 --> EmailSvc
    UC7 --> SMSSvc
```

---

## Owner Use Cases

```mermaid
graph LR
    Owner((Owner))

    subgraph "Account & Portfolio"
        UC1[Register Account]
        UC2[Login / Logout]
        UC3[Manage Profile]
        UC4[Add Property]
        UC5[Manage Units]
        UC6[Publish Unit Listing]
    end

    subgraph "Tenant & Lease"
        UC7[Review Applications]
        UC8[Approve / Reject Applicant]
        UC9[Create Lease Agreement]
        UC10[Countersign Lease]
        UC11[Renew Lease]
        UC12[Terminate Lease]
    end

    subgraph "Rent Management"
        UC13[Configure Rent & Fees]
        UC14[View Rent Invoices]
        UC15[Record Offline Payment]
        UC16[View Overdue Payments]
    end

    subgraph "Bills & Utilities"
        UC17[Create Utility Bill]
        UC18[Split Bill Across Units]
        UC19[Attach Bill Scan]
    end

    subgraph "Maintenance"
        UC20[View Maintenance Requests]
        UC21[Assign Request to Staff]
        UC22[Approve Completed Request]
        UC23[Schedule Preventive Task]
        UC24[Log Maintenance Cost]
    end

    subgraph "Finance & Reports"
        UC25[View Financial Dashboard]
        UC26[Generate Rent Roll]
        UC27[Generate Tax Report]
        UC28[Export Reports]
    end

    Owner --> UC1
    Owner --> UC2
    Owner --> UC3
    Owner --> UC4
    Owner --> UC5
    Owner --> UC6
    Owner --> UC7
    Owner --> UC8
    Owner --> UC9
    Owner --> UC10
    Owner --> UC11
    Owner --> UC12
    Owner --> UC13
    Owner --> UC14
    Owner --> UC15
    Owner --> UC16
    Owner --> UC17
    Owner --> UC18
    Owner --> UC19
    Owner --> UC20
    Owner --> UC21
    Owner --> UC22
    Owner --> UC23
    Owner --> UC24
    Owner --> UC25
    Owner --> UC26
    Owner --> UC27
    Owner --> UC28
```

---

## Tenant Use Cases

```mermaid
graph LR
    Tenant((Tenant))

    subgraph "Account"
        UC1[Register Account]
        UC2[Login / Logout]
        UC3[Manage Profile]
        UC4[Upload Documents]
    end

    subgraph "Property Search"
        UC5[Browse Listings]
        UC6[Filter & Search Units]
        UC7[View Unit Details]
        UC8[Submit Application]
        UC9[Track Application Status]
    end

    subgraph "Lease"
        UC10[Review Lease Document]
        UC11[Sign Lease Digitally]
        UC12[View Active Lease]
        UC13[Accept / Decline Renewal]
    end

    subgraph "Rent & Bills"
        UC14[View Rent Invoice]
        UC15[Pay Rent Online]
        UC16[Download Rent Receipt]
        UC17[View Payment History]
        UC18[View Utility Bills]
        UC19[Pay Utility Bill]
        UC20[Dispute a Bill]
    end

    subgraph "Maintenance"
        UC21[Submit Maintenance Request]
        UC22[Track Request Status]
        UC23[Rate Resolved Request]
    end

    Tenant --> UC1
    Tenant --> UC2
    Tenant --> UC3
    Tenant --> UC4
    Tenant --> UC5
    Tenant --> UC6
    Tenant --> UC7
    Tenant --> UC8
    Tenant --> UC9
    Tenant --> UC10
    Tenant --> UC11
    Tenant --> UC12
    Tenant --> UC13
    Tenant --> UC14
    Tenant --> UC15
    Tenant --> UC16
    Tenant --> UC17
    Tenant --> UC18
    Tenant --> UC19
    Tenant --> UC20
    Tenant --> UC21
    Tenant --> UC22
    Tenant --> UC23
```

---

## Maintenance Staff Use Cases

```mermaid
graph LR
    MaintStaff((Maintenance Staff))

    subgraph "Task Management"
        UC1[View Assigned Tasks]
        UC2[Accept Task]
        UC3[Decline Task with Reason]
        UC4[Update Task Status]
        UC5[Add Work Notes and Photos]
        UC6[Log Materials Used]
        UC7[Mark Task Completed]
    end

    subgraph "Schedule"
        UC8[View Work Schedule]
        UC9[Set Availability]
    end

    subgraph "History"
        UC10[View Task History]
        UC11[View Property Details]
    end

    MaintStaff --> UC1
    MaintStaff --> UC2
    MaintStaff --> UC3
    MaintStaff --> UC4
    MaintStaff --> UC5
    MaintStaff --> UC6
    MaintStaff --> UC7
    MaintStaff --> UC8
    MaintStaff --> UC9
    MaintStaff --> UC10
    MaintStaff --> UC11
```

---

## Admin Use Cases

```mermaid
graph LR
    Admin((Admin))

    subgraph "Dashboard"
        UC1[View Platform Metrics]
        UC2[View Audit Logs]
        UC3[Generate Reports]
    end

    subgraph "User Management"
        UC4[Verify Owner Documents]
        UC5[Approve / Reject Owner]
        UC6[Suspend User Account]
        UC7[Manage Admin Roles]
    end

    subgraph "Dispute Resolution"
        UC8[View Disputes]
        UC9[Mediate Dispute]
        UC10[Override Payment Status]
        UC11[Close Dispute]
    end

    subgraph "Platform Config"
        UC12[Manage Lease Templates]
        UC13[Manage Notification Templates]
        UC14[Configure System Settings]
        UC15[Manage Integrations]
    end

    Admin --> UC1
    Admin --> UC2
    Admin --> UC3
    Admin --> UC4
    Admin --> UC5
    Admin --> UC6
    Admin --> UC7
    Admin --> UC8
    Admin --> UC9
    Admin --> UC10
    Admin --> UC11
    Admin --> UC12
    Admin --> UC13
    Admin --> UC14
    Admin --> UC15
```

---

## Use Case Relationships

```mermaid
graph TB
    subgraph "Include Relationships"
        SignLease[Sign Lease] -->|includes| VerifyIdentity[Verify Identity]
        SignLease -->|includes| GeneratePDF[Generate Signed PDF]
        SignLease -->|includes| NotifyOwner[Notify Owner]

        PayRent[Pay Rent] -->|includes| ValidateInvoice[Validate Invoice]
        PayRent -->|includes| ProcessPayment[Process via Gateway]
        PayRent -->|includes| GenerateReceipt[Generate Receipt]

        TerminateLease[Terminate Lease] -->|includes| CalcFees[Calculate Termination Fees]
        TerminateLease -->|includes| ScheduleInspection[Schedule Move-out Inspection]
        TerminateLease -->|includes| InitiateDeposit[Initiate Deposit Refund]
    end

    subgraph "Extend Relationships"
        BrowseListings[Browse Listings] -.->|extends| ApplyFilters[Apply Filters]
        BrowseListings -.->|extends| ViewOnMap[View on Map]

        ViewInvoice[View Invoice] -.->|extends| DownloadReceipt[Download Receipt]
        ViewInvoice -.->|extends| DisputeCharge[Dispute Charge]

        MaintenanceRequest[Maintenance Request] -.->|extends| AttachPhotos[Attach Photos]
        MaintenanceRequest -.->|extends| SetPriority[Set Priority Level]
    end
```
