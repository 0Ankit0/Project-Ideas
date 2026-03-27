# Requirements Document

## 1. Introduction

### 1.1 Purpose
This document defines the functional and non-functional requirements for a generalized rental management platform that supports any class of rentable asset — real estate, vehicles, equipment, gear, and more — enabling owners and rental operators to manage their entire rental business from a single system.

### 1.2 Scope
The system will support:
- Multi-category asset listing and availability management
- Customer booking and reservation workflows
- Digital rental agreement creation and signing
- Flexible pricing (hourly, daily, weekly, monthly; peak pricing; bulk discounts)
- Security deposit collection, hold, deduction, and refund
- Pre- and post-rental condition assessments
- Invoice generation, online payment collection, and overdue fee handling
- Asset maintenance and servicing lifecycle
- Financial reporting and analytics for owners and operators
- Admin platform management and dispute resolution

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **Asset** | Any rentable item managed on the platform (car, flat, camera, generator, etc.) |
| **Asset Category** | A classification grouping similar assets (Vehicles, Real Estate, Equipment, etc.) |
| **Listing** | A published asset made available for customer booking |
| **Booking / Reservation** | A customer's request to rent an asset for a specified period |
| **Rental Period** | The confirmed start and end date/time of a rental |
| **Rental Agreement** | A formal contract between the owner and customer for a booking |
| **Pricing Rule** | A rate definition for an asset (hourly, daily, weekly, monthly; peak/off-peak) |
| **Security Deposit** | A refundable amount collected at booking confirmation |
| **Condition Assessment** | A pre- or post-rental inspection of an asset's condition with photo evidence |
| **Additional Charge** | Any fee beyond the base rental rate (damage, late return, fuel, cleaning, etc.) |
| **Return** | The process of a customer handing back the asset at the end of the rental period |

---

## 2. Functional Requirements

### 2.1 User Management Module

#### FR-UM-001: Owner / Operator Registration
- System shall allow owners and rental operators to register with email or phone
- System shall support business profile creation with trading name and contact details
- System shall require identity and (optionally) business document verification
- System shall enforce OTP-based email/phone verification

#### FR-UM-002: Customer Registration
- System shall allow customers to create accounts via email or phone
- System shall collect basic profile information (name, ID, payment method)
- System shall support social login (Google, Apple)
- System shall support OTP-based phone verification

#### FR-UM-003: Staff Management
- Owners shall add staff members to their account (e.g., fleet managers, depot staff)
- System shall support role assignment per staff member (assessment, maintenance, customer service)
- System shall maintain staff availability schedules

#### FR-UM-004: Admin Management
- System shall support role-based access control (RBAC) for admin users
- System shall maintain admin activity audit logs
- System shall support 2FA for all admin accounts

#### FR-UM-005: Authentication
- System shall implement JWT-based authentication with refresh tokens
- System shall support session management and concurrent device limits
- System shall enforce password complexity policies and account lockout

---

### 2.2 Asset & Listing Management Module

#### FR-AL-001: Asset Category Management
- Owners shall define or select asset categories (Vehicles, Real Estate, Equipment, etc.)
- Each category shall support configurable custom attribute fields (e.g., make/model for vehicles, sqft for flats, wattage for generators)
- Admins shall manage the global category taxonomy

#### FR-AL-002: Asset Creation
- Owners shall create assets with a name, description, category, photos, and custom attributes
- System shall support multiple photos and a cover image per asset
- System shall track asset serial numbers or registration identifiers where applicable

#### FR-AL-003: Pricing Configuration
- Owners shall define flexible pricing rules per asset: hourly, daily, weekly, monthly rates
- System shall support peak pricing windows and seasonal rate adjustments
- System shall support minimum and maximum rental duration constraints
- Owners shall configure security deposit amounts per asset

#### FR-AL-004: Availability Management
- Owners shall set asset availability windows on a calendar
- System shall block out dates when an asset is booked, under maintenance, or manually unavailable
- System shall support recurring unavailability (e.g., every Sunday)

#### FR-AL-005: Listing Publication
- Owners shall publish or unpublish assets for customer browsing
- System shall support drafts before publication
- Owners shall configure booking lead time (e.g., must book at least 2 hours in advance)

#### FR-AL-006: Asset Documents
- Owners shall upload asset-level documents (insurance certificates, inspection certificates, manuals)
- System shall store documents securely and link them to the asset
- Owners shall share specific documents with customers at booking confirmation

---

### 2.3 Booking & Reservation Module

#### FR-BR-001: Asset Search & Discovery
- Customers shall search available assets by category, location, date range, and price
- System shall display a real-time availability calendar per asset
- System shall show pricing breakdown for the selected period

#### FR-BR-002: Booking Request
- Customers shall submit a booking request for an available asset and period
- System shall capture selected rental period, delivery/pickup preference, and special requests
- System shall place a temporary hold on the asset's availability upon booking request

#### FR-BR-003: Booking Confirmation
- Owners shall approve or decline booking requests (for manual confirmation mode)
- System shall support instant booking mode where requests are auto-confirmed if available
- System shall collect the security deposit upon booking confirmation
- System shall notify both parties of the confirmed booking

#### FR-BR-004: Booking Modification
- Customers shall request changes to booking dates before the rental starts
- Owners shall approve or decline modification requests
- System shall recalculate the price difference and process additional charges or refunds

#### FR-BR-005: Booking Cancellation
- Customers and owners shall cancel bookings subject to the configured cancellation policy
- System shall calculate and apply cancellation fees per policy
- System shall process refunds (full, partial, or none) based on the policy tier
- System shall release the asset's availability upon cancellation

---

### 2.4 Rental Agreement Module

#### FR-RA-001: Agreement Generation
- System shall generate a rental agreement from a configurable template upon booking confirmation
- Agreement shall capture asset details, rental period, pricing, deposit, policies, and liability terms
- System shall support owner-defined custom clauses per asset category

#### FR-RA-002: Digital Signing
- System shall send the agreement to the customer for digital e-signature
- System shall record the signature timestamp and IP address
- System shall generate a signed PDF copy for both parties and store it securely
- Owners shall countersign before the rental begins

#### FR-RA-003: Agreement Amendments
- Owners shall issue an amendment agreement for booking modifications
- Amendment shall be re-signed by both parties
- System shall version-control all agreement revisions

---

### 2.5 Payment & Invoice Module

#### FR-PI-001: Invoice Generation
- System shall generate invoices automatically on booking confirmation and at rental completion
- Invoices shall include base rental fee, applicable taxes, and any additional charges
- System shall support prorated billing for partial periods

#### FR-PI-002: Payment Collection
- Customers shall pay via the platform (card, bank transfer, wallet, buy-now-pay-later)
- System shall integrate multiple payment gateways
- System shall collect security deposits as a separate hold or charge
- System shall send payment confirmation receipts

#### FR-PI-003: Additional Charges
- Owners shall add post-rental charges (damage, excess mileage, late return, cleaning, fuel)
- System shall notify customers of additional charges before processing
- System shall allow customers to dispute additional charges

#### FR-PI-004: Refunds
- System shall process security deposit refunds within a configurable window after return
- System shall process booking cancellation refunds per the cancellation policy
- System shall track all refund transactions

#### FR-PI-005: Overdue & Late Return Fees
- System shall detect late returns and auto-calculate overdue fees per the asset's daily/hourly rate
- System shall notify both customer and owner of a detected overdue return
- System shall apply the overdue fee to the customer's outstanding balance

#### FR-PI-006: Payout to Owners
- System shall calculate net payouts after platform commission deduction
- System shall process scheduled payouts to owner bank accounts
- System shall provide owners with a payout history and settlement export

---

### 2.6 Condition Assessment Module

#### FR-CA-001: Pre-Rental Assessment
- Staff or owners shall complete a condition assessment before handing over the asset
- Assessment shall capture asset condition per category-specific checklist items
- Assessment shall include timestamped photos
- Customer shall countersign the pre-rental assessment report

#### FR-CA-002: Post-Rental Assessment
- Staff or owners shall complete a condition assessment upon asset return
- System shall compare post-rental against pre-rental condition to highlight discrepancies
- Assessment shall include timestamped photos as evidence
- System shall prompt owner to raise damage charges based on assessment findings

#### FR-CA-003: Assessment Reports
- System shall generate a PDF assessment report for each assessment
- Both parties shall receive a copy of the completed assessment
- Assessment reports shall be stored and linked to the booking

---

### 2.7 Maintenance & Servicing Module

#### FR-MS-001: Maintenance Request Logging
- Owners and staff shall log maintenance requests for assets (damage, servicing, repairs)
- System shall assign a unique request ID and notify relevant staff
- System shall block the asset's availability during active maintenance

#### FR-MS-002: Maintenance Assignment
- Owners shall assign requests to internal staff or external service providers
- System shall track assignment acceptance and task status updates
- Owners shall approve completed maintenance before the asset is released back to available

#### FR-MS-003: Maintenance Scheduling
- Owners shall schedule preventive servicing (oil changes, calibration, safety checks)
- System shall send reminders before scheduled service dates
- System shall log all service history per asset

#### FR-MS-004: Maintenance Costs
- Owners shall log costs (labour, parts, contractor fees) against maintenance requests
- Costs shall be included in asset expense reports and financial summaries

---

### 2.8 Reporting & Analytics Module

#### FR-RP-001: Owner Dashboard
- Owners shall view total revenue, outstanding balances, active bookings, and asset utilisation
- Dashboard shall show asset-level and portfolio-level performance metrics
- System shall provide month-over-month and year-over-year comparisons

#### FR-RP-002: Revenue & Expense Reports
- System shall generate revenue reports per asset, category, or full portfolio
- System shall categorise expenses (maintenance, commissions, insurance)
- System shall export reports to PDF and CSV

#### FR-RP-003: Booking & Utilisation Reports
- System shall report booking counts, utilisation rates, and vacancy periods per asset
- System shall show peak demand periods and average booking durations

#### FR-RP-004: Tax Reports
- System shall generate annual rental income summaries for tax filing purposes
- System shall list deductible expenses per asset
- System shall export to common accounting formats (CSV, PDF)

---

### 2.9 Notification Module

#### FR-NM-001: Email Notifications
- System shall send transactional emails for all key events (booking, agreement, payment, return)
- System shall support configurable email templates per event type

#### FR-NM-002: SMS Notifications
- System shall send SMS for booking confirmations, reminders, and urgent alerts (overdue return)
- System shall manage SMS quotas per account tier

#### FR-NM-003: In-App / Push Notifications
- System shall display real-time in-app notifications for all key events
- System shall support notification preference management per user
- System shall deliver real-time push via WebSocket for dashboard updates

---

## 3. Non-Functional Requirements

### 3.1 Performance

| Requirement | Target |
|-------------|--------|
| API response time | < 300ms (p95) |
| Availability calendar load | < 500ms |
| Dashboard load time | < 2 seconds |
| Concurrent users | 50,000+ |
| File upload size | Up to 50 MB per file |

### 3.2 Scalability
- Horizontal scaling of all application services
- Database read replicas for analytics and reporting queries
- Auto-scaling based on traffic patterns
- CDN for asset photos, documents, and report exports

### 3.3 Availability
- 99.9% uptime SLA
- Zero-downtime deployments
- Multi-AZ database deployment
- Graceful degradation of non-critical features

### 3.4 Security
- HTTPS/TLS 1.3 for all communications
- Encrypted storage of sensitive documents (agreements, IDs, assessment reports)
- PCI-DSS compliance for payment data
- GDPR and regional data privacy compliance
- Role-based access — customers cannot view other customers' data
- Audit logs for all financial, booking, and agreement actions
- Rate limiting and brute-force protection

### 3.5 Reliability
- Idempotent payment processing to prevent duplicate charges
- Transaction-safe booking and deposit operations
- Automated daily database backups with point-in-time recovery
- Circuit breaker patterns for payment gateway and e-signature calls

### 3.6 Maintainability
- Modular service-oriented architecture with pluggable asset category adapters
- Comprehensive structured logging
- Distributed tracing for cross-service requests
- Health-check endpoints on all services
- Feature flags for gradual feature rollouts

### 3.7 Usability
- Mobile-responsive web interface for owners and customers
- Dedicated mobile app for customers and staff
- WCAG 2.1 AA accessibility compliance
- Multi-language and multi-currency support

---

## 4. System Constraints

### 4.1 Technical Constraints
- Cloud-native deployment (AWS / GCP / Azure)
- Container-based deployment (Docker / Kubernetes)
- Event-driven architecture for async operations (notifications, reports, billing)
- API-first design (REST / OpenAPI 3.0)
- Pluggable asset category schema — custom attributes defined per category without schema migrations

### 4.2 Business Constraints
- Multi-currency support for international operations
- Tax rule configuration per jurisdiction
- Support for individual asset owners and multi-asset rental fleet operators
- Integration with external e-signature providers (DocuSign, Adobe Sign)
- White-label support for enterprise operators running branded platforms

### 4.3 Regulatory Constraints
- Compliance with consumer protection and rental regulations per jurisdiction
- Secure storage and handling of government-issued ID documents
- Payment data security (PCI-DSS)
- Data residency requirements for certain regions
