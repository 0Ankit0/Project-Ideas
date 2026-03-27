# Requirements Document

## 1. Introduction

### 1.1 Purpose
This document defines the functional and non-functional requirements for a house rental management platform that enables property owners to manage their entire rental portfolio — including properties, tenants, leases, rent collection, utility bills, and maintenance — from a single system.

### 1.2 Scope
The system will support:
- Property listing, onboarding, and unit management
- Tenant application, screening, and onboarding
- Lease agreement creation and lifecycle management
- Rent invoicing, collection, and reconciliation
- Utility and bill management per unit
- Maintenance request tracking and resolution
- Financial reporting and analytics for owners
- Admin platform management and dispute resolution

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **Property** | A real-estate asset (house, apartment building, villa) owned by the landlord |
| **Unit** | An individual rentable space within a property (e.g., apartment 2B) |
| **Lease** | A formal rental agreement between an owner and a tenant for a unit |
| **Rent Cycle** | The recurring billing period (monthly, quarterly) defined in the lease |
| **Maintenance Request** | A tenant-submitted request for repair or upkeep of a unit or common area |
| **Bill** | A utility or service charge (electricity, water, gas, internet) applied to a unit |
| **Security Deposit** | A refundable amount collected from a tenant at lease start |
| **Inspection** | A formal check of a unit's condition at move-in, mid-term, or move-out |

---

## 2. Functional Requirements

### 2.1 User Management Module

#### FR-UM-001: Owner Registration
- System shall allow owners to register with email or phone
- System shall support document verification (ID proof, property ownership proof)
- System shall enforce email/phone OTP verification

#### FR-UM-002: Tenant Registration
- System shall allow tenants to create accounts via email or phone
- System shall collect basic profile information (name, ID, employment details)
- System shall support OTP-based phone verification

#### FR-UM-003: Maintenance Staff Management
- System shall allow owners to add maintenance staff to their portfolio
- System shall support role assignment (plumber, electrician, general)
- System shall maintain staff availability schedules

#### FR-UM-004: Admin Management
- System shall support role-based access control (RBAC) for admin users
- System shall maintain admin activity audit logs
- System shall support 2FA for admin accounts

#### FR-UM-005: Authentication
- System shall implement JWT-based authentication
- System shall support session management and token refresh
- System shall enforce password complexity policies

---

### 2.2 Property & Unit Management Module

#### FR-PM-001: Property Creation
- Owners shall create properties with address, type, photos, and amenities
- System shall support multiple property types (house, apartment, commercial)
- System shall support bulk unit creation for multi-unit properties

#### FR-PM-002: Unit Management
- Owners shall configure each unit with floor, size, bedrooms, bathrooms, and base rent
- System shall track unit availability status (vacant, occupied, under-maintenance)
- System shall support unit-level amenity tagging

#### FR-PM-003: Property Listing
- Owners shall publish or unpublish units for tenant browsing
- System shall support photo galleries, virtual tour links, and floor plans
- System shall allow owners to set pet policies, smoking policies, and lease terms

#### FR-PM-004: Property Documents
- Owners shall upload property-level documents (insurance, floor plans)
- System shall store and version documents securely
- System shall allow owners to share specific documents with tenants

---

### 2.3 Tenant Application & Screening Module

#### FR-TA-001: Tenant Application
- Tenants shall submit applications for available units
- Application shall collect employment info, references, and ID documents
- System shall support multiple concurrent applications per tenant

#### FR-TA-002: Application Review
- Owners shall review, approve, or reject tenant applications with reason
- System shall notify tenants of application status changes
- System shall maintain an application history per unit

#### FR-TA-003: Tenant Screening
- System shall support background check integration (credit, rental history)
- System shall flag applications that fail configurable screening criteria
- Owners shall be able to waive screening flags with a recorded reason

---

### 2.4 Lease Management Module

#### FR-LM-001: Lease Creation
- Owners shall generate lease agreements from templates
- Lease shall capture start date, end date, rent amount, deposit, and policies
- System shall support fixed-term and month-to-month lease types

#### FR-LM-002: Digital Signing
- System shall send lease documents to tenant for digital e-signature
- System shall record signature timestamp and IP address
- System shall generate a signed PDF copy for both parties

#### FR-LM-003: Lease Renewal
- System shall alert owners and tenants X days before lease expiry (configurable)
- Owners shall generate a renewal offer with updated terms
- Tenants shall accept or decline renewal offers

#### FR-LM-004: Lease Termination
- Owners and tenants shall initiate early termination with a notice period
- System shall calculate any early-termination fees per lease terms
- System shall trigger move-out inspection scheduling on termination

#### FR-LM-005: Security Deposit Management
- System shall track deposit collection, holds, deductions, and refunds
- Owners shall itemize deductions before releasing the deposit
- System shall enforce configurable deposit refund deadlines

---

### 2.5 Rent Management Module

#### FR-RM-001: Rent Invoice Generation
- System shall auto-generate rent invoices on each billing cycle date
- Invoice shall include base rent, applicable fees, and due date
- System shall support prorated rent for partial-month occupancy

#### FR-RM-002: Online Rent Payment
- Tenants shall pay rent through the platform (card, bank transfer, wallet)
- System shall integrate multiple payment gateways
- System shall send payment confirmation receipts

#### FR-RM-003: Late Fees & Reminders
- System shall send rent due reminders (X days before due date)
- System shall auto-apply late fees after configurable grace period
- System shall escalate overdue rent notifications to owners

#### FR-RM-004: Rent History & Receipts
- Tenants shall download payment receipts and rental ledger
- Owners shall view full payment history per unit and tenant
- System shall export rent history to CSV/PDF

#### FR-RM-005: Partial Payments
- System shall accept partial rent payments with owner approval
- System shall track outstanding balances across billing periods
- System shall flag units with chronic payment issues

---

### 2.6 Bill Management Module

#### FR-BM-001: Bill Creation
- Owners shall create utility bills (electricity, water, gas, internet) per unit
- System shall support recurring bills and one-time charges
- System shall allow attachment of utility bill scans

#### FR-BM-002: Bill Splitting
- Owners shall split common-area utility bills across occupied units
- System shall support equal or proportional (area/occupancy) split methods
- System shall generate individual tenant portions automatically

#### FR-BM-003: Bill Payment
- Tenants shall pay bills via the platform or mark as paid offline
- System shall reconcile payments and update outstanding balances
- System shall notify tenants of new bills and due dates

#### FR-BM-004: Bill History
- Tenants and owners shall view full bill history per unit
- System shall provide monthly expense summaries per property
- System shall support bill dispute initiation by tenants

---

### 2.7 Maintenance Request Module

#### FR-MR-001: Request Submission
- Tenants shall submit maintenance requests with description, photos, and priority
- System shall assign a unique request ID
- Owners shall be notified immediately of new requests

#### FR-MR-002: Request Assignment
- Owners shall assign requests to internal staff or external contractors
- System shall notify the assignee of the new task
- System shall track acceptance/rejection of assignments

#### FR-MR-003: Request Resolution
- Maintenance staff shall update status (in-progress, completed) with notes and photos
- Owners shall approve or reopen completed requests
- System shall close the request and notify the tenant upon approval

#### FR-MR-004: Maintenance Scheduling
- Owners shall schedule preventive maintenance tasks (HVAC, plumbing checks)
- System shall send reminders for upcoming scheduled maintenance
- System shall log all maintenance activity per unit

#### FR-MR-005: Maintenance Costs
- Owners shall log costs against maintenance requests
- System shall categorize costs (material, labour, contractor)
- System shall include maintenance costs in financial reports

---

### 2.8 Financial Reporting Module

#### FR-FR-001: Owner Dashboard
- Owners shall view total rental income, outstanding balances, and expenses
- Dashboard shall show occupancy rate and vacancy trends
- System shall provide month-over-month comparisons

#### FR-FR-002: Income & Expense Reports
- System shall generate income statements per property or portfolio
- System shall categorize expenses (maintenance, utilities, management fees)
- System shall export reports to PDF and CSV

#### FR-FR-003: Tax Reports
- System shall generate annual rental income summaries for tax purposes
- System shall list deductible expenses per property
- System shall support export to common accounting formats

#### FR-FR-004: Rent Roll
- System shall generate a rent roll showing all units, tenants, and rent status
- Rent roll shall be filterable by property, status, and date range
- System shall export rent roll to CSV/PDF

---

### 2.9 Notification Module

#### FR-NM-001: Email Notifications
- System shall send transactional emails (lease signed, rent due, request update)
- System shall support configurable email templates
- System shall track email delivery status

#### FR-NM-002: SMS Notifications
- System shall send SMS for rent reminders and urgent maintenance updates
- System shall manage SMS quotas per account

#### FR-NM-003: In-App Notifications
- System shall display in-app notifications for all key events
- System shall support notification preferences per user
- System shall support real-time push via WebSocket

---

## 3. Non-Functional Requirements

### 3.1 Performance

| Requirement | Target |
|-------------|--------|
| API response time | < 300ms (p95) |
| Dashboard load time | < 2 seconds |
| Concurrent users | 10,000+ |
| Document upload size | Up to 50 MB per file |

### 3.2 Scalability
- Horizontal scaling of all application services
- Database read replicas for reporting and analytics queries
- Auto-scaling based on traffic load
- CDN for property photos and document assets

### 3.3 Availability
- 99.9% uptime SLA
- Zero-downtime deployments
- Multi-AZ database deployment
- Graceful degradation of non-critical features

### 3.4 Security
- HTTPS/TLS 1.3 for all communications
- Encrypted storage of sensitive documents (leases, IDs)
- GDPR and regional data privacy compliance
- Rate limiting and brute-force protection
- Role-based access — tenants cannot view other tenants' data
- Audit log for all financial and lease actions

### 3.5 Reliability
- Automated daily database backups with point-in-time recovery
- Idempotent payment processing to prevent duplicate charges
- Transaction-safe rent and deposit operations
- Circuit breaker patterns for payment gateway calls

### 3.6 Maintainability
- Modular service-oriented architecture
- Comprehensive structured logging
- Distributed tracing for cross-service requests
- Health-check endpoints on all services
- Feature flags for gradual feature rollouts

### 3.7 Usability
- Mobile-responsive web interface
- Dedicated mobile app for tenants (iOS & Android)
- WCAG 2.1 AA accessibility compliance
- Multi-language support (i18n)

---

## 4. System Constraints

### 4.1 Technical Constraints
- Cloud-native deployment (AWS/GCP/Azure)
- Container-based deployment (Docker/Kubernetes)
- Event-driven architecture for async operations (notifications, reports)
- API-first design (REST)

### 4.2 Business Constraints
- Multi-currency support for international property portfolios
- Tax rule configuration per jurisdiction
- Support for both individual landlords and property management companies
- Integration with external e-signature providers (DocuSign, Adobe Sign)

### 4.3 Regulatory Constraints
- Compliance with local tenancy laws (notice periods, deposit limits)
- Secure storage and handling of government-issued ID documents
- Payment data security (PCI-DSS compliance)
- Data residency requirements for certain regions
