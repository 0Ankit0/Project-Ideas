# User Stories — Real Estate Management System

**Version:** 1.0  
**Date:** 2025-01  
**Roles:** Property Manager, Tenant, Owner, Contractor, Admin  

---

## Epic 1: Property & Unit Management

### US-001 — Add New Property
**As a** Property Manager,  
**I want** to create a new property record with full address, type, and configuration details,  
**So that** I can begin managing units and listings under the property.

**Acceptance Criteria:**
- AC-001-1: Property form requires address (street, city, state, zip), property type, year built, and total unit count
- AC-001-2: System validates address against USPS address verification API
- AC-001-3: Duplicate property detection warns if another property with same address exists in the company portfolio
- AC-001-4: Property is saved with status "Active" and creation audit log entry
- AC-001-5: System auto-generates a unique property code (e.g., PROP-20250001)

---

### US-002 — Add Property Units
**As a** Property Manager,  
**I want** to add individual units to a property with floor, type, and size details,  
**So that** I can manage each rentable space independently.

**Acceptance Criteria:**
- AC-002-1: Unit requires unit number, floor number, unit type (studio, 1BR, 2BR, commercial), sq footage, and bedroom/bathroom count
- AC-002-2: Unit number must be unique within the property
- AC-002-3: System allows bulk unit creation for multi-family buildings (e.g., floors 1–10, units 01–08)
- AC-002-4: Created units default to status "Vacant"

---

### US-003 — Upload Property Listing Photos
**As a** Property Manager,  
**I want** to upload and organize photos for a unit listing,  
**So that** prospective tenants can view the property visually before scheduling a showing.

**Acceptance Criteria:**
- AC-003-1: System accepts JPEG, PNG, and HEIC formats up to 20MB per photo
- AC-003-2: Photos are automatically resized to three variants: thumbnail (200×150), web (1200×800), full (2400×1600)
- AC-003-3: Manager can tag each photo with a room category (Living Room, Kitchen, Bedroom, Bathroom, Exterior, Amenity)
- AC-003-4: Drag-and-drop reordering of photos is supported
- AC-003-5: Maximum 50 photos per listing; uploading beyond this limit returns a validation error

---

### US-004 — Publish Listing to External Portals
**As a** Property Manager,  
**I want** to activate a listing so it is syndicated to Zillow and Apartments.com automatically,  
**So that** I reach the maximum prospective tenant audience without manual re-entry.

**Acceptance Criteria:**
- AC-004-1: Listing activation triggers syndication job within 15 minutes
- AC-004-2: Syndication success/failure status is displayed per portal in the listing detail view
- AC-004-3: Failed syndication generates a manager notification with error details
- AC-004-4: Deactivating a listing propagates removal from portals within 30 minutes

---

## Epic 2: Tenant Application & Screening

### US-005 — Submit Rental Application Online
**As a** Prospective Tenant,  
**I want** to submit a rental application online for a specific unit,  
**So that** I can express interest in renting without visiting the office.

**Acceptance Criteria:**
- AC-005-1: Application form collects: full name, date of birth, SSN (encrypted), employment info, income, references, and rental history
- AC-005-2: Applicant must upload at least one government-issued ID and two months of pay stubs or bank statements
- AC-005-3: Application requires explicit consent checkbox for background and credit check
- AC-005-4: Submitted application generates an acknowledgment email within 2 minutes
- AC-005-5: Application is rejected at form level if applicant is under 18

---

### US-006 — Automated Background Check Initiation
**As a** Property Manager,  
**I want** the system to automatically initiate a background check when an application is submitted,  
**So that** I do not have to manually trigger screening and can review results in one place.

**Acceptance Criteria:**
- AC-006-1: Background check is initiated via Checkr API within 60 seconds of application submission
- AC-006-2: Check covers: criminal history (7-year lookback), eviction records, sex offender registry
- AC-006-3: Results are displayed within the application review screen with clear pass/flag indicators
- AC-006-4: If Checkr is unavailable, application is flagged "Screening Pending - Manual" and manager is notified

---

### US-007 — Review and Approve Tenant Application
**As a** Property Manager,  
**I want** to review screening results, income ratio, and references in a unified interface,  
**So that** I can make an informed and compliant approval decision efficiently.

**Acceptance Criteria:**
- AC-007-1: Application review screen shows: personal info, credit score, background check results, income-to-rent ratio, references, uploaded documents
- AC-007-2: Income-to-rent ratio calculated as gross monthly income / monthly rent; flagged if below 2.5x
- AC-007-3: Approve and Reject buttons are available; Reject requires selecting a reason from a Fair Housing-compliant dropdown
- AC-007-4: Approval triggers automated lease creation offer; rejection triggers applicant notification within 5 minutes

---

### US-008 — Receive Application Status Notification
**As a** Prospective Tenant,  
**I want** to receive real-time email and SMS updates about my application status,  
**So that** I am kept informed without having to log in repeatedly.

**Acceptance Criteria:**
- AC-008-1: Notifications are sent for: application received, under review, approved, rejected, additional info requested
- AC-008-2: Email notifications include application reference number and portal link
- AC-008-3: SMS is sent to the mobile number provided on the application
- AC-008-4: Notification delivery is logged with timestamp and channel

---

## Epic 3: Lease Management

### US-009 — Generate Lease from Template
**As a** Property Manager,  
**I want** to generate a lease agreement automatically from an approved template after approving a tenant application,  
**So that** I reduce manual document preparation time and ensure consistency.

**Acceptance Criteria:**
- AC-009-1: System auto-populates: tenant name(s), property address, unit details, rent amount, security deposit, lease start/end dates, pet policy, and parking allocation
- AC-009-2: Manager can select from a library of approved addenda (pet addendum, parking addendum, utilities addendum)
- AC-009-3: Lease preview is available before sending for signature
- AC-009-4: Lease is created with status "Draft" until sent for signature

---

### US-010 — Sign Lease Digitally via DocuSign
**As a** Tenant,  
**I want** to sign my lease electronically via DocuSign,  
**So that** I can complete the move-in process without printing or visiting the office.

**Acceptance Criteria:**
- AC-010-1: Tenant receives a DocuSign email invitation within 5 minutes of lease being sent
- AC-010-2: All required signature fields are pre-placed on the lease document
- AC-010-3: Tenant can review the full lease before signing
- AC-010-4: Upon all parties signing, the completed lease PDF is stored in REMS and emailed to all parties
- AC-010-5: Lease status changes to "Active" automatically upon all signatures

---

### US-011 — Configure Rent Schedule
**As a** Property Manager,  
**I want** to configure the rent schedule for a new lease,  
**So that** the system can automate invoice generation and late fee calculation.

**Acceptance Criteria:**
- AC-011-1: Schedule includes: monthly rent amount, due date (day of month), grace period (days), start date, end date
- AC-011-2: First month proration is calculated automatically if lease starts mid-month
- AC-011-3: Manager can configure annual escalation: fixed dollar amount or percentage
- AC-011-4: Schedule changes require a reason note and generate a lease amendment record

---

### US-012 — Receive Lease Renewal Offer
**As a** Tenant,  
**I want** to receive a lease renewal offer with updated terms before my lease expires,  
**So that** I can decide whether to continue renting without service interruption.

**Acceptance Criteria:**
- AC-012-1: Renewal offer sent automatically 90 days before lease expiration
- AC-012-2: Offer includes: new monthly rent, new lease term options (6 months, 12 months, 24 months), any change in terms
- AC-012-3: Tenant can accept or decline online; acceptance triggers new lease creation workflow
- AC-012-4: If tenant does not respond by 30 days before expiration, manager is alerted

---

### US-013 — Process Early Lease Termination
**As a** Property Manager,  
**I want** to process an early lease termination with correct fee calculation,  
**So that** financial obligations are properly settled and the unit is made available promptly.

**Acceptance Criteria:**
- AC-013-1: System calculates early termination fee per lease clause (e.g., 2 months rent)
- AC-013-2: Prorated rent for partial month is calculated if termination is mid-month
- AC-013-3: Security deposit disposition workflow is automatically initiated
- AC-013-4: Unit status is set to "Vacant" upon confirmed termination date

---

## Epic 4: Rent & Payment Management

### US-014 — Automated Monthly Rent Invoice
**As a** Property Manager,  
**I want** the system to automatically generate and send rent invoices monthly,  
**So that** I do not have to manually invoice tenants and can focus on higher-value tasks.

**Acceptance Criteria:**
- AC-014-1: Invoices generated 5 days before the due date per rent schedule
- AC-014-2: Invoice includes: base rent, recurring charges (parking, pet, storage), prior balance, total due
- AC-014-3: Invoice is emailed to tenant(s) and available in tenant portal within 1 minute of generation
- AC-014-4: Invoice generation failures are logged and trigger a retry within 30 minutes

---

### US-015 — Pay Rent Online
**As a** Tenant,  
**I want** to pay my rent online via bank transfer or credit card,  
**So that** I can pay conveniently without mailing checks.

**Acceptance Criteria:**
- AC-015-1: Tenant can pay via ACH (bank account) or Stripe card (Visa, Mastercard, Amex)
- AC-015-2: Payment confirmation screen shows: amount charged, method, confirmation number, date
- AC-015-3: Email receipt sent within 60 seconds of payment processing
- AC-015-4: Partial payments are accepted with remaining balance reflected on the tenant ledger
- AC-015-5: Autopay setup available for ACH with configurable day-of-month trigger

---

### US-016 — Automatic Late Fee Assessment
**As a** Property Manager,  
**I want** the system to automatically apply late fees after the grace period,  
**So that** I don't have to manually track and bill overdue accounts.

**Acceptance Criteria:**
- AC-016-1: Late fee calculated at 11:59 PM on the last day of the grace period for all unpaid invoices
- AC-016-2: Late fee structure applied per lease configuration (flat fee default: $75 or 5% of monthly rent, whichever is greater, subject to state maximums)
- AC-016-3: Late fee invoice generated separately with clear description and original invoice reference
- AC-016-4: Tenant notified of late fee assessment via email and SMS

---

### US-017 — Security Deposit Collection
**As a** Property Manager,  
**I want** to collect and track security deposits separately from rent,  
**So that** I maintain compliant escrow accounting and have a clear record for refund processing.

**Acceptance Criteria:**
- AC-017-1: Security deposit invoice generated separately at lease signing with separate Stripe payment link
- AC-017-2: Payment recorded against security deposit ledger, not rent ledger
- AC-017-3: Deposit amount displayed in owner portal with escrow account reference
- AC-017-4: System enforces state-specific maximum deposit limits (e.g., 2 months rent in California)

---

### US-018 — Security Deposit Refund Processing
**As a** Property Manager,  
**I want** to process security deposit refunds with itemized deductions,  
**So that** I comply with legal timelines and provide transparent accounting to tenants.

**Acceptance Criteria:**
- AC-018-1: Refund workflow initiated from move-out inspection
- AC-018-2: Manager can add deduction line items with description, amount, and supporting photo
- AC-018-3: System calculates net refund = deposit paid - total deductions
- AC-018-4: Refund processed via ACH to tenant bank account on file; if no ACH, check generated
- AC-018-5: Itemized deduction statement and refund confirmation emailed to tenant

---

## Epic 5: Maintenance Management

### US-019 — Submit Maintenance Request
**As a** Tenant,  
**I want** to submit a maintenance request through the portal with photos,  
**So that** I can report issues quickly and track their resolution.

**Acceptance Criteria:**
- AC-019-1: Request form collects: category, title, description, urgency indicator (non-emergency / emergency), and up to 10 photo/video attachments
- AC-019-2: Submitted request generates a unique work order ID and acknowledgment notification
- AC-019-3: Emergency requests trigger immediate SMS alert to the on-call property manager
- AC-019-4: Tenant can track request status in real time through the portal

---

### US-020 — Assign Maintenance Request to Contractor
**As a** Property Manager,  
**I want** to assign a maintenance request to a contractor with access instructions,  
**So that** the work is completed promptly by a qualified service provider.

**Acceptance Criteria:**
- AC-020-1: Manager selects contractor from the managed contractor database filtered by trade and service area
- AC-020-2: Assignment sends contractor a work order notification with unit address, access code, and scope of work
- AC-020-3: Proposed appointment time is communicated to tenant with 24-hour advance notice
- AC-020-4: Contractor receives a mobile-friendly work order page to update status and upload completion photos

---

### US-021 — Complete Work Order with Photos
**As a** Contractor,  
**I want** to mark a work order complete and upload before/after photos,  
**So that** the property manager and tenant have visual confirmation of the completed work.

**Acceptance Criteria:**
- AC-021-1: Contractor can update status to "In Progress" on arrival and "Completed" upon finishing
- AC-021-2: At least one "after" photo is required to mark a request complete
- AC-021-3: Contractor can add materials used and labor time for invoice generation
- AC-021-4: Completion notification sent to tenant and property manager

---

### US-022 — Track Maintenance SLA Compliance
**As a** Property Manager,  
**I want** to see overdue maintenance requests flagged on my dashboard,  
**So that** I can prioritize resolution and avoid habitability violations.

**Acceptance Criteria:**
- AC-022-1: Maintenance dashboard shows open requests sorted by SLA status: On Track, At Risk (>50% time elapsed), Overdue
- AC-022-2: Overdue emergency requests trigger escalation email to supervisor
- AC-022-3: SLA metrics (average response time, resolution time) displayed per priority category
- AC-022-4: SLA report exportable by date range

---

## Epic 6: Property Inspections

### US-023 — Schedule Move-In Inspection
**As a** Property Manager,  
**I want** to schedule a move-in inspection before a tenant takes possession,  
**So that** the pre-tenancy condition of the unit is documented for deposit purposes.

**Acceptance Criteria:**
- AC-023-1: Inspection scheduled within the lease creation workflow with configurable lead time
- AC-023-2: Tenant notified of inspection date/time at least 24 hours in advance
- AC-023-3: Digital checklist auto-assigned based on property type (residential/commercial)
- AC-023-4: Inspection report saved as a versioned document linked to the lease

---

### US-024 — Complete Digital Inspection Checklist
**As a** Property Manager,  
**I want** to complete a digital inspection checklist on a tablet or phone during the walkthrough,  
**So that** I can capture detailed condition data and photos for each room without paper forms.

**Acceptance Criteria:**
- AC-024-1: Each checklist item has condition selector (Excellent/Good/Fair/Poor/Damaged) and notes field
- AC-024-2: Photos can be taken in-app per checklist item via camera API
- AC-024-3: Checklist auto-saves progress; incomplete inspections are resumable
- AC-024-4: Inspection can be completed offline with sync on reconnection

---

## Epic 7: Owner Management

### US-025 — View Owner Dashboard
**As an** Owner,  
**I want** to view a real-time dashboard of my portfolio performance,  
**So that** I can monitor occupancy, revenue, and expenses without contacting my property manager.

**Acceptance Criteria:**
- AC-025-1: Dashboard shows total units, occupancy rate, gross rent collected (current month/YTD), outstanding rent, maintenance spend
- AC-025-2: Property-level drill-down available for portfolios with multiple properties
- AC-025-3: Dashboard data refreshes every 15 minutes
- AC-025-4: Mobile-responsive layout for smartphone access

---

### US-026 — Download Monthly Owner Statement
**As an** Owner,  
**I want** to download my monthly owner financial statement in PDF format,  
**So that** I have a clear record of property income and expenses for accounting purposes.

**Acceptance Criteria:**
- AC-026-1: Statement generated automatically on the 5th of each month for the prior month
- AC-026-2: Statement includes: gross rent collected, vacancy loss, management fees, maintenance expenses, other deductions, net distribution
- AC-026-3: PDF-formatted statement emailed automatically and available for download in owner portal
- AC-026-4: Statements available for download for a rolling 5 years

---

## Epic 8: Document Management

### US-027 — Upload and Organize Property Documents
**As a** Property Manager,  
**I want** to upload and categorize documents associated with properties and leases,  
**So that** I can retrieve important documents quickly and share them with relevant parties.

**Acceptance Criteria:**
- AC-027-1: Documents can be uploaded and tagged with category (lease, insurance, inspection, deed, permit, other)
- AC-027-2: Document versioning allows uploading a new version while retaining previous versions
- AC-027-3: Role-based access controls determine which documents tenants and owners can view
- AC-027-4: Document expiry date field with automated alert notifications

---

### US-028 — Receive Document Expiry Alert
**As a** Property Manager,  
**I want** to receive alerts when key documents (insurance, contractor licenses) are approaching expiry,  
**So that** I can renew them before lapsing and avoid compliance gaps.

**Acceptance Criteria:**
- AC-028-1: Alerts sent 90, 30, and 7 days before document expiry
- AC-028-2: Alert includes: document name, property/entity link, expiry date, and renewal action link
- AC-028-3: Expired documents are flagged in the document list with a red indicator
- AC-028-4: Manager can dismiss alerts with a reason note for compliance auditing

---

## Epic 9: Reporting & Analytics

### US-029 — View Occupancy Analytics
**As a** Property Manager,  
**I want** to view occupancy rate trends across my portfolio,  
**So that** I can identify underperforming properties and optimize vacancy marketing.

**Acceptance Criteria:**
- AC-029-1: Occupancy chart shows monthly trend for last 12 months by property and portfolio aggregate
- AC-029-2: Average days vacant per unit displayed with benchmark comparison
- AC-029-3: Upcoming lease expirations shown in a 90-day forward calendar view
- AC-029-4: Report exportable to CSV and PDF

---

### US-030 — Generate Delinquency Report
**As a** Property Manager,  
**I want** to generate a delinquency report showing all overdue invoices,  
**So that** I can prioritize collection follow-up and escalate persistent delinquents.

**Acceptance Criteria:**
- AC-030-1: Report shows: tenant name, unit, days overdue, amount overdue, last payment date
- AC-030-2: Filter options: property, days overdue (30+, 60+, 90+), amount range
- AC-030-3: Bulk email action to send payment reminder to selected delinquent tenants
- AC-030-4: Report exportable to CSV

---

## Epic 10: Administration

### US-031 — Manage User Accounts and Roles
**As a** System Administrator,  
**I want** to create and manage user accounts with role-based permissions,  
**So that** staff members have appropriate access and sensitive data is protected.

**Acceptance Criteria:**
- AC-031-1: Admin can create user accounts with roles: Admin, Property Manager, Leasing Agent, Accounting, Owner, Contractor, Tenant
- AC-031-2: Role permissions are predefined but customizable per company
- AC-031-3: User accounts can be deactivated (not deleted) with immediate session invalidation
- AC-031-4: MFA enrollment enforced for Admin and Property Manager roles

---

### US-032 — Configure Notification Templates
**As a** System Administrator,  
**I want** to customize email and SMS notification templates per company branding,  
**So that** all tenant communications reflect the property management company's brand.

**Acceptance Criteria:**
- AC-032-1: Email templates support variable substitution for tenant name, property address, amounts, dates
- AC-032-2: Templates support HTML formatting with inline logo upload
- AC-032-3: Template changes are versioned with preview functionality before activation
- AC-032-4: Default fallback templates are used if a custom template fails rendering

---

### US-033 — Manage Contractor Database
**As a** Property Manager,  
**I want** to maintain a database of approved contractors with trade categories and coverage areas,  
**So that** I can quickly find and assign qualified contractors for maintenance work orders.

**Acceptance Criteria:**
- AC-033-1: Contractor profile includes: company name, trade categories, service area (zip codes), license number, insurance expiry, and contact details
- AC-033-2: System blocks assignment of contractors with expired licenses or insurance
- AC-033-3: Contractor performance rating calculated from completed work order reviews
- AC-033-4: Contractor database searchable by trade, zip code, and availability

---

### US-034 — View System Audit Logs
**As a** System Administrator,  
**I want** to view and export audit logs for all user actions,  
**So that** I can investigate security incidents and satisfy regulatory audit requirements.

**Acceptance Criteria:**
- AC-034-1: Audit log shows: timestamp, user, action, affected resource, source IP
- AC-034-2: Filter by date range, user, action type, and resource type
- AC-034-3: Log entries are immutable and cannot be deleted via UI
- AC-034-4: Export in CSV and JSON formats; retention 7 years

---

### US-035 — Configure Late Fee Rules
**As a** Property Manager,  
**I want** to configure late fee rules per property or company with jurisdictional limits applied automatically,  
**So that** late fees are assessed correctly without manual calculation.

**Acceptance Criteria:**
- AC-035-1: Fee structure options: flat amount, percentage of monthly rent, daily accrual after grace period
- AC-035-2: System enforces maximum late fee limits per state regulatory rules
- AC-035-3: Grace period configurable from 1–10 days with default set per jurisdiction
- AC-035-4: Late fee rules versioned; prior rules retained for historical invoice accuracy

---

### US-036 — Manage Utility Accounts
**As a** Property Manager,  
**I want** to track utility accounts per unit and enter sub-meter readings for billing,  
**So that** utility costs are accurately distributed to responsible parties.

**Acceptance Criteria:**
- AC-036-1: Utility accounts linked to unit with provider, account number, and billing cycle
- AC-036-2: Sub-meter readings can be entered manually or imported via CSV
- AC-036-3: System calculates consumption (current reading - previous reading) and applies rate
- AC-036-4: Utility invoices generated as line items on next rent invoice

---

### US-037 — Export to QuickBooks
**As a** Property Manager / Accountant,  
**I want** to export financial transactions to QuickBooks Online automatically,  
**So that** my accounting records are synchronized without manual data entry.

**Acceptance Criteria:**
- AC-037-1: QuickBooks sync runs daily at 02:00 AM UTC; manual sync also available
- AC-037-2: Sync includes: rent payments, security deposit movements, maintenance expenses, owner distributions
- AC-037-3: Sync errors are logged and emailed to the configured accounting contact
- AC-037-4: QuickBooks chart of accounts mapping configurable per company

---

### US-038 — Set Up Autopay
**As a** Tenant,  
**I want** to enroll my bank account in autopay for monthly rent,  
**So that** I never miss a payment due to forgetting.

**Acceptance Criteria:**
- AC-038-1: Tenant links bank account via Plaid or manual routing/account entry (micro-deposit verification)
- AC-038-2: Autopay configured for specific day of month (default: due date - 2 days)
- AC-038-3: Confirmation email sent at enrollment and 3 days before each autopay deduction
- AC-038-4: Autopay can be paused or cancelled by tenant at any time; cancellation effective from next billing cycle

---

### US-039 — View Tenant Ledger
**As a** Tenant,  
**I want** to view my complete payment history and current balance on the portal,  
**So that** I can verify all charges and confirm my account is current.

**Acceptance Criteria:**
- AC-039-1: Ledger shows: date, description, charge/credit amount, balance after each transaction
- AC-039-2: Rent invoices, payments, late fees, security deposit, and adjustments all visible
- AC-039-3: Downloadable PDF ledger statement available for last 12 months
- AC-039-4: Disputed charges can be flagged from the ledger with a note to manager

---

### US-040 — Manage Multi-Language Notices
**As a** Property Manager,  
**I want** to send lease notices and communications in the tenant's preferred language,  
**So that** I ensure comprehension and demonstrate fair housing commitment.

**Acceptance Criteria:**
- AC-040-1: Tenant profile includes preferred language selection (English, Spanish, Mandarin, French for v1)
- AC-040-2: System sends notifications in tenant's preferred language when template translations are available
- AC-040-3: Language preference logged in tenant profile audit trail
- AC-040-4: Manager can override and send in English for legal documents when required

---

### US-041 — Process NSF / Returned Payment
**As a** Property Manager,  
**I want** to be notified automatically when a tenant payment is returned and have the invoice re-opened,  
**So that** I can pursue collection and assess the applicable NSF fee without manual tracking.

**Acceptance Criteria:**
- AC-041-1: Stripe webhook triggers NSF processing within 30 minutes of return notification
- AC-041-2: Payment reversed in ledger; invoice status reset to "Unpaid"
- AC-041-3: NSF fee invoice generated and added to tenant balance
- AC-041-4: Tenant notified of returned payment via email and SMS
- AC-041-5: Payment method flagged as "NSF - manager review required" in tenant profile

---

### US-042 — View Portfolio-Level Revenue Report
**As an** Owner,  
**I want** to view a consolidated revenue report across all my properties,  
**So that** I can assess the performance of my real estate portfolio holistically.

**Acceptance Criteria:**
- AC-042-1: Report shows gross potential rent, collected rent, vacancy loss, delinquency amount, NOI per property and aggregated
- AC-042-2: Date range filter: current month, YTD, last 12 months, custom range
- AC-042-3: Charts show revenue trend and occupancy trend on the same timeline
- AC-042-4: PDF export with company branding applied

---

### US-043 — Manage Lease Addenda
**As a** Property Manager,  
**I want** to add property-specific addenda to leases from a pre-approved library,  
**So that** lease customization is fast and legally reviewed clauses are used consistently.

**Acceptance Criteria:**
- AC-043-1: Addenda library includes: pet addendum, parking addendum, storage addendum, pool/gym rules, move-in/move-out procedures
- AC-043-2: Addenda content versioned; selecting an addendum always uses the current approved version
- AC-043-3: Custom addenda can be created by Admins only after legal review flag
- AC-043-4: All selected addenda included in DocuSign envelope with signature fields

---

### US-044 — Submit Contractor Invoice
**As a** Contractor,  
**I want** to submit an invoice for completed maintenance work through the portal,  
**So that** I am paid promptly without submitting paper invoices.

**Acceptance Criteria:**
- AC-044-1: Invoice linked to work order; includes labor hours, materials breakdown, and total amount
- AC-044-2: PDF invoice upload supported in addition to manual line item entry
- AC-044-3: Property manager receives notification of invoice submission
- AC-044-4: Approved invoices queued for payment within 30 days
- AC-044-5: Disputed invoices trigger a communication thread between manager and contractor

---

### US-045 — Configure Property-Specific Late Fee Rules
**As a** System Administrator,  
**I want** to configure different late fee rules for different states/jurisdictions,  
**So that** the platform remains compliant across all markets where the company operates.

**Acceptance Criteria:**
- AC-045-1: Admin can define late fee rules per state with: max flat fee, max percentage, grace period minimum
- AC-045-2: Jurisdiction rules take precedence over company-level defaults
- AC-045-3: Rule changes are effective from specified date, not retroactively applied to existing invoices
- AC-045-4: Compliance report shows current rules vs. state statutory limits for audit purposes
