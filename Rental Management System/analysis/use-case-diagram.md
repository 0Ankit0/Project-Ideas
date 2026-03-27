# Use Case Diagram

## Overview
Use case diagrams for all major actors in the rental management system, applicable to any asset type (cars, gear, flats, equipment, etc.).

---

## Complete System Use Case Diagram

```mermaid
graph TB
    subgraph Actors
        Owner((Owner / Operator))
        Customer((Customer / Renter))
        Staff((Staff))
        Admin((Admin))
        PaymentGW((Payment Gateway))
        ESign((E-Signature Provider))
        SMSSvc((SMS Provider))
    end

    subgraph "Rental Management Platform"
        UC1[Manage Assets & Listings]
        UC2[Manage Availability]
        UC3[Review Bookings]
        UC4[Manage Agreements]
        UC5[Manage Payments & Invoices]
        UC6[Manage Condition Assessments]
        UC7[Manage Maintenance]
        UC8[View Reports & Analytics]

        UC10[Search & Browse Listings]
        UC11[Make Booking]
        UC12[Sign Rental Agreement]
        UC13[Pay Invoice]
        UC14[Countersign Assessment]
        UC15[Return Asset]
        UC16[Rate & Review]

        UC20[Perform Assessments]
        UC21[Update Maintenance Tasks]

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

    Customer --> UC10
    Customer --> UC11
    Customer --> UC12
    Customer --> UC13
    Customer --> UC14
    Customer --> UC15
    Customer --> UC16

    Staff --> UC20
    Staff --> UC21

    Admin --> UC30
    Admin --> UC31
    Admin --> UC32
    Admin --> UC33

    UC13 --> PaymentGW
    UC12 --> ESign
    UC5 --> SMSSvc
```

---

## Owner Use Cases

```mermaid
graph LR
    Owner((Owner / Operator))

    subgraph "Account & Portfolio"
        UC1[Register Account]
        UC2[Login / Logout]
        UC3[Manage Profile]
        UC4[Create Asset Category]
        UC5[Add Asset]
        UC6[Configure Pricing Rules]
        UC7[Manage Availability Calendar]
        UC8[Publish / Unpublish Listing]
    end

    subgraph "Booking Management"
        UC9[View Booking Requests]
        UC10[Approve / Decline Booking]
        UC11[View Active Bookings]
        UC12[Cancel Booking]
    end

    subgraph "Agreements & Deposits"
        UC13[Generate Rental Agreement]
        UC14[Countersign Agreement]
        UC15[Configure Security Deposit]
        UC16[Process Deposit Refund or Deduction]
    end

    subgraph "Payments"
        UC17[View Invoices]
        UC18[Add Additional Charges]
        UC19[View Payout History]
        UC20[Request Payout]
    end

    subgraph "Assessments & Maintenance"
        UC21[Review Pre-Rental Assessment]
        UC22[Review Post-Rental Assessment]
        UC23[Log Maintenance Request]
        UC24[Assign Maintenance to Staff]
        UC25[Approve Completed Maintenance]
        UC26[Schedule Preventive Servicing]
    end

    subgraph "Reports"
        UC27[View Financial Dashboard]
        UC28[Generate Revenue Report]
        UC29[Generate Utilisation Report]
        UC30[Generate Tax Report]
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
    Owner --> UC29
    Owner --> UC30
```

---

## Customer Use Cases

```mermaid
graph LR
    Customer((Customer / Renter))

    subgraph "Account"
        UC1[Register Account]
        UC2[Login / Logout]
        UC3[Manage Profile]
        UC4[Upload ID Documents]
        UC5[Manage Payment Methods]
    end

    subgraph "Search & Booking"
        UC6[Search Listings]
        UC7[Filter & Sort Results]
        UC8[View Asset Listing]
        UC9[Check Availability]
        UC10[Submit Booking Request]
        UC11[Track Booking Status]
        UC12[Modify Booking]
        UC13[Cancel Booking]
    end

    subgraph "Agreements & Payments"
        UC14[Review Rental Agreement]
        UC15[Sign Agreement Digitally]
        UC16[Pay Invoice]
        UC17[Download Receipt]
        UC18[View Payment History]
        UC19[Dispute Additional Charge]
    end

    subgraph "Assessments & Returns"
        UC20[Countersign Pre-Rental Assessment]
        UC21[Initiate Return]
        UC22[View Post-Rental Assessment]
    end

    subgraph "Reviews"
        UC23[Rate & Review Asset]
        UC24[View Asset Reviews]
    end

    Customer --> UC1
    Customer --> UC2
    Customer --> UC3
    Customer --> UC4
    Customer --> UC5
    Customer --> UC6
    Customer --> UC7
    Customer --> UC8
    Customer --> UC9
    Customer --> UC10
    Customer --> UC11
    Customer --> UC12
    Customer --> UC13
    Customer --> UC14
    Customer --> UC15
    Customer --> UC16
    Customer --> UC17
    Customer --> UC18
    Customer --> UC19
    Customer --> UC20
    Customer --> UC21
    Customer --> UC22
    Customer --> UC23
    Customer --> UC24
```

---

## Staff Use Cases

```mermaid
graph LR
    Staff((Staff))

    subgraph "Assessment Tasks"
        UC1[View Assigned Tasks]
        UC2[Complete Pre-Rental Assessment]
        UC3[Complete Post-Rental Assessment]
        UC4[Upload Assessment Photos]
        UC5[Submit Assessment for Review]
    end

    subgraph "Maintenance Tasks"
        UC6[Accept Maintenance Task]
        UC7[Decline Task with Reason]
        UC8[Update Task Status]
        UC9[Add Work Notes and Photos]
        UC10[Log Materials and Costs]
        UC11[Mark Task Completed]
    end

    subgraph "Schedule & History"
        UC12[View Work Schedule]
        UC13[Set Availability]
        UC14[View Completed Task History]
    end

    Staff --> UC1
    Staff --> UC2
    Staff --> UC3
    Staff --> UC4
    Staff --> UC5
    Staff --> UC6
    Staff --> UC7
    Staff --> UC8
    Staff --> UC9
    Staff --> UC10
    Staff --> UC11
    Staff --> UC12
    Staff --> UC13
    Staff --> UC14
```

---

## Admin Use Cases

```mermaid
graph LR
    Admin((Admin))

    subgraph "Dashboard & Monitoring"
        UC1[View Platform Metrics]
        UC2[View Audit Logs]
        UC3[Generate Reports]
    end

    subgraph "User Management"
        UC4[Verify Owner Documents]
        UC5[Approve / Reject Owner]
        UC6[Suspend / Deactivate User]
        UC7[Manage Admin Roles]
    end

    subgraph "Content & Config"
        UC8[Manage Asset Categories]
        UC9[Manage Agreement Templates]
        UC10[Manage Notification Templates]
        UC11[Configure Commission Rates]
        UC12[Configure System Settings]
    end

    subgraph "Dispute Resolution"
        UC13[View Disputes]
        UC14[Mediate Dispute]
        UC15[Override Payment / Charge]
        UC16[Close Dispute]
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
    Admin --> UC16
```

---

## Use Case Relationships

```mermaid
graph TB
    subgraph "Include Relationships"
        MakeBooking[Make Booking] -->|includes| CheckAvailability[Check Asset Availability]
        MakeBooking -->|includes| CalculatePrice[Calculate Rental Price]
        MakeBooking -->|includes| HoldDeposit[Collect Security Deposit]

        SignAgreement[Sign Agreement] -->|includes| VerifyIdentity[Verify Customer Identity]
        SignAgreement -->|includes| SendToESign[Send to E-Sign Provider]
        SignAgreement -->|includes| StorePDF[Store Signed PDF]

        CloseRental[Close Rental] -->|includes| PostAssessment[Complete Post-Rental Assessment]
        CloseRental -->|includes| ReleaseDeposit[Process Deposit Refund]
        CloseRental -->|includes| GenerateFinalInvoice[Generate Final Invoice]
    end

    subgraph "Extend Relationships"
        SearchListings[Search Listings] -.->|extends| ApplyFilters[Apply Category / Date / Price Filters]
        SearchListings -.->|extends| ViewOnMap[View on Map]

        ViewInvoice[View Invoice] -.->|extends| DownloadReceipt[Download Receipt]
        ViewInvoice -.->|extends| DisputeCharge[Dispute Charge]

        PostAssessment[Post-Rental Assessment] -.->|extends| RaiseDamageCharge[Raise Damage Charge]
        PostAssessment -.->|extends| DetectLateReturn[Detect Late Return Fee]
    end
```
