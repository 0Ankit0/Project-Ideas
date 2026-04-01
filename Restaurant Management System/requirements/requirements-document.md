# Restaurant Management System - Requirements Document

## Executive Summary

The Restaurant Management System (RMS) is a comprehensive, cloud-native platform designed to modernize and unify every operational aspect of multi-branch restaurant businesses. From the moment a guest makes a reservation to the point where a cashier closes the drawer at the end of service, the RMS orchestrates every workflow — seating management, waiter-assisted ordering, kitchen production, inventory tracking, payment settlement, shift scheduling, and financial reconciliation — within a single, cohesive platform accessible across tablets, POS terminals, kitchen display screens, and management dashboards.

Unlike fragmented point solutions that force restaurants to manage separate systems for reservations, POS, kitchen displays, and accounting, the RMS treats the restaurant as a connected graph of operational entities. A reservation naturally flows into a table assignment, which flows into waiter order capture, which routes kitchen tickets to the right stations, which triggers inventory deductions, which ultimately resolves into a guest bill that feeds the cashier session and accounting export. Every event in this chain is traceable, auditable, and recoverable — even under degraded network conditions or peak-load stress.

The platform is built to scale from a single-location café to a chain of 500+ branches, supporting thousands of concurrent staff devices without sacrificing the sub-second responsiveness that high-volume table service demands. Security, compliance, and operational resilience are first-class design constraints, not afterthoughts. The RMS enables branch managers, inventory teams, and executives to make data-driven decisions through real-time dashboards and exportable reports, while keeping day-to-day staff workflows lean, fast, and intuitive.

---

## Project Scope

### In Scope

| Area | Description |
|------|-------------|
| Multi-branch dine-in and takeaway operations | Full table, order, kitchen, inventory, billing, and shift lifecycle management per branch |
| Reservation and waitlist management | Guest-facing and staff-facing reservation flows, walk-in queuing, ETA quoting |
| Table and floor management | Table maps, zone assignments, merge/split, cleaning workflows |
| Menu and pricing management | Branch-aware menus, categories, modifiers, tax rules, happy-hour pricing |
| Order management and POS | Waiter-driven order capture, course firing, split orders, voids |
| Kitchen operations (KDS) | Station-based ticket routing, preparation state machine, pass coordination |
| Inventory and procurement | Ingredient management, recipe BOM, purchase orders, receiving, wastage |
| Billing and payment processing | Bill generation, split payments, multi-tender, refunds, settlement |
| Staff and shift management | Shift scheduling, attendance tracking, branch day open/close |
| Delivery channel integration | Integration with Uber Eats, DoorDash, Zomato and other aggregators |
| Loyalty program hooks | Basic loyalty points accrual and redemption tied to guest profiles |
| Reporting and analytics | Sales dashboards, kitchen SLA reports, inventory variance, shift summaries |
| System administration | Role-based access, branch configuration, audit trails, policy management |

### Out of Scope

| Area | Reason |
|------|--------|
| Full payroll and HR suite | Handled by dedicated HRMS platforms |
| General ledger ERP accounting | Export adapters provided; full accounting out of scope |
| Custom payment gateway implementation | Integration with Stripe, Square, Razorpay via standard APIs |
| Manufacturing-grade supply-chain optimization | Advanced logistics is outside restaurant operations scope |
| Customer-facing mobile app (standalone) | Guest touchpoints are web-based; native app is Phase 3 |

---

## Stakeholders

| Role | Responsibility | Key Concerns |
|------|----------------|--------------|
| Restaurant Owner / Executive | Strategic oversight and investment decisions | ROI, multi-branch visibility, compliance |
| Branch Manager | Day-to-day operations management | Staff productivity, service quality, daily close accuracy |
| Restaurant Manager | Floor and kitchen coordination | Table turnover, kitchen SLA, guest satisfaction |
| Host / Reception Staff | Reservations, seating, and waitlist | Accurate ETA, fast seating, no overbooking |
| Waiter / Server | Order capture and table service | Fast POS, accurate kitchen routing, easy bill split |
| Chef / Kitchen Staff | Food preparation and station management | Clear ticket queues, accurate prep times, stock visibility |
| Cashier / Accountant | Payment settlement and reconciliation | Tax accuracy, split bill support, day-end close |
| Inventory Manager | Stock control and procurement | Recipe deductions, low-stock alerts, vendor management |
| Delivery Staff | Delivery order fulfillment | Clear order details, accurate packing lists |
| IT / System Administrator | Platform configuration and maintenance | Security, uptime, audit trails, integration stability |
| End Customer / Guest | Dining experience | Accurate reservations, fast service, correct billing |
| Payment Processor (Stripe/Square) | Transaction processing | API stability, PCI compliance |
| Third-party Delivery Aggregators | Order intake and dispatch | API reliability, order sync accuracy |
| Accounting System (QuickBooks) | Financial reporting | Clean export data, tax summaries |

---

## Functional Requirements

### Module 1: Restaurant and Branch Management

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | The system shall support creation and management of multiple restaurant branches, each with its own configuration for tables, service zones, menus, taxes, payment methods, and printers. | Must Have |
| FR-02 | Each branch shall have independently configurable operating hours, service types (dine-in, takeaway, delivery), and peak-load policies. | Must Have |
| FR-03 | The system shall support a branch day-open workflow that validates staffing coverage, cash drawer initialization, and kitchen station readiness before allowing service transactions. | Must Have |
| FR-04 | The system shall support a branch day-close workflow that validates all checks are settled or transferred, all drawers are reconciled, and all kitchen tickets are resolved before allowing end-of-day sign-off. | Must Have |
| FR-05 | Administrators shall be able to clone branch configurations, propagate menu updates across selected branches, and manage branch-level feature flags from a central console. | Should Have |

### Module 2: Table and Floor Management

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-06 | The system shall maintain a real-time interactive floor map per branch showing table status (available, reserved, occupied, cleaning, blocked) with party size, elapsed time, and assigned server. | Must Have |
| FR-07 | Hosts shall be able to assign, reassign, merge, and split tables, with the system maintaining full order and check lineage across these operations. | Must Have |
| FR-08 | The system shall support configurable table turn timers that alert hosts when a table exceeds its expected service duration, supporting both manual and automatic table release workflows. | Must Have |
| FR-09 | The system shall track table cleaning status and prevent new seatings until a table is marked clean by authorized staff. | Must Have |
| FR-10 | The system shall support blocking tables for maintenance, events, or VIP reservations with required reason codes and automatic unblock scheduling. | Should Have |

### Module 3: Reservation and Waitlist Management

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-11 | The system shall support guest reservations with fields for guest name, contact, party size, seating preference (indoor, outdoor, bar), dietary notes, and requested date/time. | Must Have |
| FR-12 | The reservation engine shall perform real-time availability checks against table capacity, existing reservations, and estimated turn times before confirming a booking. | Must Have |
| FR-13 | The system shall maintain a digital waitlist for walk-in guests with live queue position, estimated wait time, and SMS/in-app notifications when their table is ready. | Must Have |
| FR-14 | The system shall enforce configurable no-show policies, including automatic cancellation after a grace period and optional deposit or credit card hold requirements. | Should Have |
| FR-15 | Hosts shall be able to view a consolidated reservation timeline showing confirmed bookings, walk-in queue, and table availability projections for the next 4 hours. | Must Have |

### Module 4: Menu and Item Management

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-16 | The system shall support a hierarchical menu structure with categories, sub-categories, items, variants, and modifier groups configurable per branch. | Must Have |
| FR-17 | Each menu item shall support multiple pricing rules including base price, variant pricing, happy-hour pricing, and time/day-based pricing tiers. | Must Have |
| FR-18 | The system shall support item-level tax configurations including GST, VAT, and service charge with per-item and category-level overrides. | Must Have |
| FR-19 | Menu items shall be linkable to recipe Bill of Materials (BOM), enabling automatic inventory deduction upon order or production milestones. | Must Have |
| FR-20 | The system shall support item availability toggling (available, 86'd, scheduled unavailable) that propagates instantly to POS terminals and guest-facing displays without removing historical sales context. | Must Have |

### Module 5: Order Management and POS

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-21 | Waiters shall be able to create, edit, add items to, apply modifiers to, and submit orders from tablet or POS terminal with an optimistic UI that handles intermittent connectivity. | Must Have |
| FR-22 | The system shall support seat-level ordering, allowing items to be assigned to specific seats within a table for accurate split billing. | Must Have |
| FR-23 | The system shall support course-based ordering with manual and automatic course firing, enabling kitchen execution to match the guest's dining pace. | Must Have |
| FR-24 | The system shall support item voids, order cancellations, and quantity changes with mandatory reason codes and manager approval for post-submission modifications. | Must Have |
| FR-25 | The system shall maintain order version history with optimistic locking to prevent concurrent editing conflicts between multiple staff members working the same table. | Must Have |

### Module 6: Kitchen Operations and KDS

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-26 | The system shall route kitchen tickets to the correct station (grill, fryer, salad, pastry, beverages) based on item-station assignments in the menu configuration. | Must Have |
| FR-27 | Kitchen staff shall be able to update ticket states (queued, accepted, in preparation, ready at pass, served, voided) from a touch-optimized Kitchen Display System (KDS) interface. | Must Have |
| FR-28 | The system shall support course synchronization rules that hold back main course tickets until appetizers for the same table reach a configurable "ready" threshold. | Must Have |
| FR-29 | The system shall surface real-time station load indicators, overdue ticket alerts, and estimated completion times to both kitchen staff and front-of-house coordinators. | Must Have |
| FR-30 | The system shall support ticket refire workflows with mandatory reason tagging (quality issue, order change, reorder) feeding into waste tracking and QoS analytics. | Should Have |

### Module 7: Billing and Payment Processing

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-31 | The system shall generate accurate bills incorporating item prices, modifiers, applicable taxes, service charges, discounts, and loyalty redemptions in a line-item format. | Must Have |
| FR-32 | The system shall support bill splitting by seat, by item, or by equal share, with partial payment tracking ensuring the check remains open until fully settled. | Must Have |
| FR-33 | The system shall support multiple payment methods per transaction including cash, credit/debit card, digital wallets, QR code payments, and house accounts. | Must Have |
| FR-34 | Cashiers shall be able to process voids and refunds with manager authorization, maintaining a complete audit trail linking refunds to original transactions. | Must Have |
| FR-35 | The system shall support cashier drawer sessions with opening balance entry, transaction logging per payment method, and closing balance reconciliation with variance reporting. | Must Have |

### Module 8: Inventory and Procurement

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-36 | The system shall maintain ingredient masters with unit of measure, storage category, reorder threshold, and preferred vendor linkage per branch. | Must Have |
| FR-37 | The system shall automatically deduct ingredient stock based on recipe BOM mappings at configurable booking points (order submission, kitchen fire, or settlement). | Must Have |
| FR-38 | The system shall support purchase request creation, purchase order approval, goods receiving with discrepancy logging, and vendor performance tracking. | Must Have |
| FR-39 | The system shall support periodic stock counts with variance comparison against expected theoretical stock, waste logging, ingredient transfers between branches, and manual adjustment approvals. | Must Have |
| FR-40 | The system shall generate low-stock and stockout alerts visible on POS terminals, KDS, and manager dashboards, and shall suppress or flag impacted menu items automatically. | Must Have |

### Module 9: Staff and Shift Management

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-41 | Branch managers shall be able to create and publish shift schedules for all operational roles (host, waiter, chef, cashier, inventory) with configurable shift templates. | Must Have |
| FR-42 | The system shall record staff clock-in and clock-out times linked to their assigned shift, providing real-time staffing coverage visibility on the manager dashboard. | Must Have |
| FR-43 | The system shall support role-based access scoping so that staff members can only access features and data relevant to their current shift assignment. | Must Have |

### Module 10: Delivery and Channel Integration

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-44 | The system shall integrate with Uber Eats, DoorDash, and Zomato APIs to ingest delivery orders directly into the POS and kitchen workflow without manual re-entry. | Should Have |
| FR-45 | Delivery orders from aggregators shall be routed to kitchen stations identically to dine-in orders, with delivery-specific packing and dispatch status tracking. | Should Have |
| FR-46 | The system shall display aggregator order statuses (driver assigned, picked up, delivered) on manager and dispatch dashboards with estimated delivery time projections. | Should Have |
| FR-47 | The system shall maintain separate sales reporting streams for dine-in, takeaway, and delivery channels to support channel-level profitability analysis. | Should Have |
| FR-48 | The system shall handle aggregator order cancellations and modifications with automated kitchen ticket updates and inventory rollback where applicable. | Should Have |

### Module 11: Loyalty Program

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-49 | The system shall maintain guest loyalty profiles with point balances, tier status, and redemption history linked to guest reservations and billing records. | Should Have |
| FR-50 | Loyalty points shall be automatically awarded at bill settlement based on configurable earn rates per menu category and branch. | Should Have |
| FR-51 | Guests and cashiers shall be able to apply loyalty redemptions at checkout, with the system validating point balance and applying the correct discount calculation. | Should Have |

### Module 12: Reporting and Analytics

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-52 | The system shall provide real-time dashboards for sales by category, table turnover rate, kitchen ticket SLA performance, stock depletion rate, and cashier settlement health. | Must Have |
| FR-53 | The system shall generate end-of-day, weekly, and monthly reports covering gross sales, refunds, discounts, tax collected, and net revenue exportable as PDF and CSV. | Must Have |
| FR-54 | The system shall provide inventory variance reports comparing theoretical vs. physical stock, with drill-down by ingredient, date range, and branch. | Must Have |

### Module 13: System Administration

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-55 | Administrators shall be able to define and assign role templates with granular feature permissions scoped to specific branches or the entire organization. | Must Have |
| FR-56 | The system shall maintain immutable audit logs for all privileged actions including voids, refunds, manual discounts, stock adjustments, role changes, and reconciliation overrides. | Must Have |
| FR-57 | The system shall support configuration management for tax codes, payment gateways, printer endpoints, KDS station mappings, and notification templates from a central admin console. | Must Have |

---

## Non-Functional Requirements

### Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-PERF-01 | POS action response time (add item, apply modifier) | < 300 ms p95 |
| NFR-PERF-02 | Order submission to kitchen routing acknowledgment | < 2 seconds p95 |
| NFR-PERF-03 | Bill generation including tax computation | < 2 seconds p95 |
| NFR-PERF-04 | Table map refresh latency for host display | < 1 second p95 |
| NFR-PERF-05 | Kitchen ticket state update propagation to POS | < 2 seconds p95 |

### Scalability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-SCALE-01 | Concurrent branches supported | 500+ |
| NFR-SCALE-02 | Concurrent staff devices per deployment | 20,000+ |
| NFR-SCALE-03 | Orders processed per minute at peak | 10,000+ system-wide |
| NFR-SCALE-04 | Horizontal scaling approach | Stateless services behind load balancers |

### Availability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-AVAIL-01 | Core service availability (monthly) | 99.9% (< 44 min downtime/month) |
| NFR-AVAIL-02 | Branch offline resilience | Critical POS workflows operate in degraded mode for up to 15 minutes |
| NFR-AVAIL-03 | Planned maintenance windows | Off-peak hours with zero-downtime deployment target |
| NFR-AVAIL-04 | Recovery Time Objective (RTO) | < 30 minutes for any single service failure |
| NFR-AVAIL-05 | Recovery Point Objective (RPO) | < 5 minutes for transactional data |

### Security

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-SEC-01 | Data in transit encryption | TLS 1.3 minimum |
| NFR-SEC-02 | Data at rest encryption | AES-256 |
| NFR-SEC-03 | Authentication mechanism | JWT with short-lived tokens + refresh token rotation |
| NFR-SEC-04 | Payment data handling | PCI-DSS SAQ-A compliant (no raw card data stored) |
| NFR-SEC-05 | Privileged action audit coverage | 100% of voids, refunds, discounts, adjustments, role changes |

### Compliance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-COMP-01 | Tax reporting | Configurable GST/VAT compliance per jurisdiction |
| NFR-COMP-02 | Data retention | Transaction records retained for minimum 7 years |
| NFR-COMP-03 | GDPR / Privacy | Guest personal data exportable and deletable on request |
| NFR-COMP-04 | Audit trail immutability | Append-only event store with no update/delete operations |

### Usability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-USE-01 | POS task completion time (new order, 3 items) | < 45 seconds for trained staff |
| NFR-USE-02 | KDS interface legibility | Readable from 1.5 meters in kitchen lighting |
| NFR-USE-03 | Accessibility | WCAG 2.1 AA for management and guest-facing web UIs |
| NFR-USE-04 | Mobile responsiveness | Full function on 7-inch tablets and above |

### Maintainability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-MAINT-01 | Deployment model | Containerized microservices with CI/CD pipeline |
| NFR-MAINT-02 | Logging | Structured JSON logs with correlation IDs on all services |
| NFR-MAINT-03 | Monitoring | Distributed tracing (OpenTelemetry) and real-time alerting |
| NFR-MAINT-04 | Configuration management | Environment-variable driven; no hardcoded configs |
| NFR-MAINT-05 | API versioning | Semantic versioning with minimum 2-version backward compatibility |

---

## MVP vs Phase 2 vs Phase 3 Scope

| Feature | Priority | Phase |
|---------|----------|-------|
| Branch and table management | Critical | MVP |
| Staff authentication and RBAC | Critical | MVP |
| Reservation and waitlist management | Critical | MVP |
| Menu and modifier management | Critical | MVP |
| Dine-in order capture (POS) | Critical | MVP |
| Kitchen ticket routing (KDS) | Critical | MVP |
| Basic inventory deduction | Critical | MVP |
| Bill generation and tax calculation | Critical | MVP |
| Cash and card payment settlement | Critical | MVP |
| Cashier drawer open/close | Critical | MVP |
| Basic sales and shift reports | Critical | MVP |
| Audit logs and admin console | Critical | MVP |
| Takeaway order support | High | MVP |
| Shift scheduling and attendance | High | MVP |
| Purchase order and goods receiving | High | Phase 2 |
| Full stock count and variance | High | Phase 2 |
| Delivery channel integration (Uber Eats, DoorDash) | High | Phase 2 |
| Split bill by seat and item | High | Phase 2 |
| Loyalty points earn and redeem | Medium | Phase 2 |
| Happy-hour and time-based pricing | Medium | Phase 2 |
| Advanced KDS course synchronization | Medium | Phase 2 |
| Manager analytics dashboard | Medium | Phase 2 |
| Multi-tender payments (wallets, QR) | Medium | Phase 2 |
| SMS/Email reservation notifications | Medium | Phase 2 |
| Zomato and additional aggregator integration | Low | Phase 3 |
| Guest-facing mobile app (React Native) | Low | Phase 3 |
| Franchise-level consolidated reporting | Low | Phase 3 |
| AI-driven demand forecasting for inventory | Low | Phase 3 |
| Customer-facing digital menu (QR code) | Low | Phase 3 |
| Payroll export integration | Low | Phase 3 |

---

## Constraints and Assumptions

### Technical Constraints
- The platform must support deployment on AWS, GCP, or Azure using containerized workloads (Docker/Kubernetes).
- Receipt printing, KDS hardware, and payment terminals are branch-specific peripheral integrations; the platform provides standard integration interfaces rather than hardware drivers.
- Offline-capable POS clients must queue transactions locally and sync upon reconnection without data loss.
- All payment processing must route through certified third-party gateways; no raw card data may be stored on platform servers.

### Business Constraints
- The platform must support configurable currency, tax jurisdiction, and language settings to support international deployment.
- Branch data isolation must be enforced at the data layer; a breach of one branch's data must not expose another branch's operational data.
- Inventory depletion policy (at order, at fire, or at settlement) must be configurable per branch without requiring code changes.

### Assumptions
- Restaurant staff have access to compatible tablet or POS terminal hardware provided by the restaurant operator.
- External delivery aggregator APIs (Uber Eats, DoorDash, Zomato) are accessible and have stable webhook/polling interfaces.
- Guest contact information for reservations is voluntarily provided and consent-managed by the restaurant operator.
- Accounting export format requirements will be defined per deployment in a post-MVP integration specification.
- Kitchen display screens operate on a stable local network with fallback to offline queue mode.

---

## Acceptance Criteria

### System-Level Acceptance Criteria

1. **Order Routing Accuracy**: 99%+ of submitted orders must route to the correct kitchen station without manual staff intervention in a 30-day production trial.
2. **Billing Accuracy**: 100% of settled checks must be traceable to their originating orders, applied taxes, discount rules, payment methods, and cashier sessions with zero unexplained variances.
3. **Audit Completeness**: 100% of privileged actions (voids, refunds, manual discounts, stock adjustments, role changes) must appear in the immutable audit log within 5 seconds of occurrence.
4. **Reservation Accuracy**: No confirmed reservation may be double-booked against the same table slot; the system must surface a slot conflict error before confirmation.
5. **Payment Idempotency**: No payment intent may result in a duplicate charge; the system must detect and reject duplicate capture attempts using idempotency keys.
6. **Offline Resilience**: Core POS and KDS workflows must remain functional for a minimum of 15 minutes during API gateway unavailability, with automatic sync upon reconnection.
7. **Performance Benchmarks**: The system must pass load tests simulating 500 concurrent branches with 40 active staff devices each, maintaining p95 response times within defined NFR targets.
8. **Inventory Variance Explainability**: At any point in time, the difference between theoretical stock (opening balance + received - recipe deductions - recorded wastage) and physical count must be explainable by auditable ledger events with no unexplained residuals greater than 2% of total throughput.
9. **Day-Close Integrity**: The day-close process must reject sign-off if any open check, unresolved payment intent, or drawer variance above threshold exists, ensuring financial accuracy before next-day operations begin.
10. **Role Access Isolation**: No staff member may access features or data outside their assigned role and branch scope; access control violations must be logged as security events.

### Feature-Level Acceptance Criteria

#### Table Management
- Table map must reflect status changes within 1 second across all concurrently logged-in host terminals.
- Table merge must consolidate all associated order lines into a single check view without losing individual seat assignments.
- Table split must create independent checks with correct item assignments and allow independent payment settlement.

#### Reservation System
- System must reject reservations for time slots where all tables of sufficient capacity are already booked.
- Waitlist position updates must be broadcast to queued guests within 30 seconds of each seating action.
- Cancellation of a reservation must release the table slot back to available inventory within 5 seconds.

#### Kitchen Operations
- All submitted order items must appear on the correct station KDS within 3 seconds of order submission.
- Course fire must not release subsequent course tickets until the preceding course for the same table is in "ready" state on all stations.
- A manually voided kitchen ticket must disappear from the KDS screen within 2 seconds and generate a waste log entry.

#### Inventory Management
- Stock deductions from recipe BOMs must post within 10 seconds of the configured deduction trigger event.
- A low-stock alert for any ingredient below its reorder threshold must appear on manager dashboard and affected POS terminals within 60 seconds of the threshold being crossed.
- A stock count submission must produce a variance report comparing physical counts to theoretical quantities within 30 seconds of submission.

#### Payment Processing
- Bill total must match the sum of all line items, taxes, service charges, and discounts to within the smallest currency unit (zero rounding error).
- A partial payment must leave the check in "partially paid" status and must not allow table release until fully settled.
- A refund initiated against a settled check must create a negative ledger entry and update the cashier session totals within the same business session.

---

## Glossary

| Term | Definition |
|------|------------|
| Branch | A single physical restaurant location managed independently within the platform |
| BOM / Recipe | Bill of Materials mapping a menu item to its constituent ingredients and quantities |
| KDS | Kitchen Display System — screen-based interface replacing printed kitchen tickets |
| Check | The billing record for a table or order, accumulating items, taxes, and payments |
| Drawer Session | A cashier's shift-level cash and payment tracking session opened at shift start and closed at shift end |
| Course Firing | The act of releasing a batch of kitchen tickets for a specific course at a controlled time |
| Aggregator | Third-party food delivery platform (Uber Eats, DoorDash, Zomato) that sends orders to the RMS |
| Theoretical Stock | Expected stock level calculated from opening balance, receipts, transfers, and BOM deductions |
| Physical Count | Actual stock quantity measured during a periodic stock count |
| Variance | Difference between theoretical stock and physical count, expressed as quantity and percentage |
| Idempotency Key | A unique identifier per payment request that prevents duplicate charges on retry |
| No-Show | A guest with a confirmed reservation who fails to arrive within the grace period |
| 86'd | Industry term for a menu item that is temporarily unavailable due to stock depletion |
| Refire | Re-sending a kitchen ticket for an item that needs to be re-prepared due to quality or order error |
| Day-Close | End-of-day operational process that reconciles all transactions, closes drawers, and prepares accounting exports |

