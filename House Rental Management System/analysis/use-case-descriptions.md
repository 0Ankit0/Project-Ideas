# Use Case Descriptions

## Overview
Detailed descriptions of primary use cases in the house rental management system.

---

## UC-001: Submit Tenant Application

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-001 |
| **Name** | Submit Tenant Application |
| **Actor** | Tenant |
| **Description** | A prospective tenant submits a rental application for a specific unit |
| **Preconditions** | Tenant is registered and logged in; unit is published and available |
| **Postconditions** | Application is created with status PENDING; owner is notified |

**Main Flow:**
1. Tenant browses available listings and selects a unit
2. Tenant clicks "Apply Now"
3. System displays the application form
4. Tenant fills in personal details, employment information, and references
5. Tenant uploads required documents (ID, pay slips)
6. Tenant submits the application
7. System validates the uploaded documents and form data
8. System creates the application record with status PENDING
9. System notifies the owner via email and in-app notification
10. System displays a confirmation screen with the application ID

**Alternative Flows:**
- *A1 – Missing documents*: System displays validation errors; tenant must re-upload
- *A2 – Unit becomes unavailable*: System informs tenant the unit is no longer available

**Exception Flows:**
- *E1 – Payment gateway timeout*: System retries once; if still failing, shows error

---

## UC-002: Create and Sign Lease Agreement

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-002 |
| **Name** | Create and Sign Lease Agreement |
| **Actor** | Owner (initiates), Tenant (signs) |
| **Description** | Owner generates a lease from a template and sends it to the tenant for digital signing |
| **Preconditions** | Application is APPROVED; tenant and owner accounts verified |
| **Postconditions** | Lease is in ACTIVE status; signed PDF stored; rent schedule generated |

**Main Flow:**
1. Owner navigates to the approved application and selects "Create Lease"
2. Owner selects a lease template
3. Owner fills in lease parameters (start/end date, rent, deposit, policies)
4. System generates a lease document preview
5. Owner reviews and sends the lease to the tenant
6. System sends the tenant an e-signature request via email
7. Tenant opens the lease, reviews terms, and signs digitally
8. System records the signature with timestamp and IP
9. System notifies the owner to countersign
10. Owner countersigns
11. System generates the final signed PDF
12. System stores the PDF and emails copies to both parties
13. System creates the rent schedule based on the lease billing cycle
14. Unit status is updated to OCCUPIED

**Alternative Flows:**
- *A1 – Tenant requests changes*: Tenant adds a comment; owner revises and resends
- *A2 – Tenant declines*: Lease status set to DECLINED; unit remains available

---

## UC-003: Collect Rent Payment

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-003 |
| **Name** | Collect Rent Payment |
| **Actor** | Tenant |
| **Description** | Tenant views a rent invoice and completes payment through the platform |
| **Preconditions** | Active lease exists; rent invoice has been generated for the billing period |
| **Postconditions** | Invoice status PAID; ledger updated; receipt emailed to tenant |

**Main Flow:**
1. Tenant receives a rent due notification (email/SMS/in-app)
2. Tenant logs in and navigates to "My Payments"
3. System displays the current invoice with amount and due date
4. Tenant clicks "Pay Now"
5. Tenant selects a payment method (card, bank transfer, wallet)
6. System redirects to payment gateway
7. Tenant completes payment on the gateway
8. Gateway sends a webhook confirming payment
9. System marks the invoice as PAID
10. System credits the owner's ledger
11. System generates and emails a receipt to the tenant
12. System sends an in-app notification to both tenant and owner

**Alternative Flows:**
- *A1 – Partial payment*: Owner approval required; outstanding balance tracked
- *A2 – Payment declined*: System retains invoice as UNPAID; tenant notified

**Exception Flows:**
- *E1 – Webhook not received*: System polls gateway after 5 minutes; auto-reconciles

---

## UC-004: Submit and Resolve Maintenance Request

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-004 |
| **Name** | Submit and Resolve Maintenance Request |
| **Actor** | Tenant (submits), Owner (assigns), Maintenance Staff (resolves) |
| **Description** | Full lifecycle of a maintenance request from submission to resolution |
| **Preconditions** | Tenant has an active lease; unit is identified |
| **Postconditions** | Request is CLOSED; cost logged; tenant rates the resolution |

**Main Flow:**
1. Tenant navigates to "Maintenance" and submits a new request
2. Tenant enters description, selects priority (low/medium/high/emergency), and uploads photos
3. System creates the request with status OPEN and notifies the owner
4. Owner reviews the request and assigns it to a maintenance staff member
5. System notifies the staff member via email and push notification
6. Staff member accepts the assignment; status changes to ASSIGNED
7. Staff member visits the property, updates status to IN_PROGRESS
8. Staff member adds work notes, photos, and materials used
9. Staff member marks the request as COMPLETED
10. Owner receives completion notification and reviews the work
11. Owner approves the completion; status changes to CLOSED
12. Tenant receives a closure notification and is prompted to rate the work
13. Owner logs the maintenance cost against the request

**Alternative Flows:**
- *A1 – Staff declines*: Owner reassigns to another staff member
- *A2 – Owner reopens*: Status reverts to IN_PROGRESS with reopen reason noted
- *A3 – Emergency request*: Owner notified immediately via SMS

---

## UC-005: Lease Renewal

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-005 |
| **Name** | Lease Renewal |
| **Actor** | Owner (initiates), Tenant (accepts/declines) |
| **Description** | Owner offers a renewed lease to the current tenant before the existing lease expires |
| **Preconditions** | Active lease within the renewal notice window (e.g., 60 days before expiry) |
| **Postconditions** | New lease created and both parties signed; or unit marked for re-listing |

**Main Flow:**
1. System sends renewal alert to both owner and tenant X days before lease end
2. Owner navigates to the expiring lease and clicks "Create Renewal"
3. Owner configures updated terms (new rent, duration, updated policies)
4. System generates a renewal lease document
5. Owner sends renewal offer to tenant
6. Tenant reviews updated terms
7. Tenant accepts the renewal; digital signing flow begins (same as UC-002 steps 7–14)
8. New lease becomes ACTIVE; old lease is archived as EXPIRED

**Alternative Flows:**
- *A1 – Tenant declines renewal*: Owner is notified; unit is scheduled for re-listing
- *A2 – Owner decides not to renew*: Owner sends non-renewal notice; system schedules move-out

---

## UC-006: Manage Utility Bills

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-006 |
| **Name** | Manage Utility Bills |
| **Actor** | Owner (creates/splits), Tenant (views/pays/disputes) |
| **Description** | Owner uploads utility bills and assigns charges to tenant units |
| **Preconditions** | Active leases exist for the relevant units |
| **Postconditions** | Bill charges assigned to tenants; payments recorded; disputes handled |

**Main Flow:**
1. Owner receives a utility bill from the service provider
2. Owner logs into the platform and navigates to "Bills"
3. Owner creates a new bill entry (type: electricity, water, etc.) with amount, billing period, and due date
4. Owner optionally uploads the scanned bill document
5. For a common-area bill, Owner selects a split method (equal / proportional)
6. System calculates each tenant's share and creates individual bill records
7. System notifies each tenant of the new bill via email and in-app
8. Tenant views the bill and the attached scan
9. Tenant pays through the platform or marks as paid offline
10. System records the payment and updates the outstanding balance
11. Owner views the reconciled bill status

**Alternative Flows:**
- *A1 – Tenant disputes the bill*: Tenant submits a dispute; owner is notified; admin can mediate
- *A2 – Tenant pays offline*: Owner records an offline payment with reference number

---

## UC-007: Generate Financial Report

| Attribute | Detail |
|-----------|--------|
| **Use Case ID** | UC-007 |
| **Name** | Generate Financial Report |
| **Actor** | Owner |
| **Description** | Owner generates a financial report for a selected property and date range |
| **Preconditions** | Owner is authenticated; at least one property with transactions exists |
| **Postconditions** | Report generated and available for download |

**Main Flow:**
1. Owner navigates to "Reports"
2. Owner selects report type (income statement, rent roll, tax summary)
3. Owner selects the property (or all properties) and date range
4. System aggregates income, expense, and payment data
5. System renders the report in the UI
6. Owner reviews the report
7. Owner exports to PDF or CSV
8. System generates the export file and triggers a download
