# Hotel Property Management System — Requirements Document

## Purpose and Scope

This document defines the functional and non-functional requirements for the Hotel Property Management System (HPMS). The system is intended to serve as the operational backbone of hotel and resort properties, supporting all front-of-house and back-of-house workflows from reservation intake through guest departure and post-stay billing. The HPMS replaces fragmented legacy tooling with a unified, cloud-native platform accessible by property staff, management, and integrated third-party services.

**In scope:**
- Reservation lifecycle management (creation, modification, cancellation)
- Front desk operations including check-in, check-out, and room assignment
- Housekeeping task management and room status tracking
- Point of Sale (POS) integration for F&B and ancillary services
- Guest folio creation, maintenance, and invoicing
- Two-way OTA and channel manager synchronisation
- Revenue management, dynamic pricing, and yield controls
- Guest loyalty programme (points, tiers, and benefits)
- Multi-property support and consolidated reporting
- Audit logging, compliance, and data governance

**Out of scope:**
- On-property construction or physical infrastructure management
- Third-party payroll or HR systems
- External accounting system internals (integration only, not replication)

## Stakeholders

| Stakeholder | Role | Primary Concerns |
|---|---|---|
| Front Desk Staff | Primary day-to-day operators | Speed, reliability, intuitive UI |
| Housekeeping Supervisors | Room readiness and task dispatch | Real-time room status, task queues |
| Revenue Managers | Pricing and inventory strategy | Rate plan management, forecasting |
| Food & Beverage Staff | POS terminals and folio posting | Accurate charge routing |
| Property General Manager | Overall operations and KPIs | Dashboards, compliance, audit |
| Property Owner / Group CXO | Portfolio-level performance | Multi-property reporting, P&L visibility |
| Guests | End consumers of hotel services | Smooth check-in/out, digital touchpoints |
| OTA Partners (Booking.com, Expedia, Airbnb, etc.) | Distribution channels | Timely ARI updates, booking confirmations |
| Channel Manager Vendors (SiteMinder, STAAH, etc.) | Middleware integration layer | Stable API contracts, low error rates |
| Payment Service Providers | Card processing and settlements | PCI-DSS compliance, tokenisation |
| IT / DevOps Team | Platform maintenance | Deployability, observability, scalability |
| Compliance Officers | Regulatory adherence | GDPR, PCI-DSS, local fiscal laws |

## System Overview

The HPMS is a multi-tenant, cloud-hosted SaaS platform. Each property is provisioned as a tenant within the platform, and a group umbrella account can span multiple properties. The system exposes a browser-based staff portal, a guest-facing web portal, mobile applications for housekeeping staff, and a RESTful JSON API for all integrations.

**Core modules:**

1. **Reservation Engine** — stores and manages all reservation records across channels.
2. **Front Desk Module** — room assignment, check-in/check-out workflows, key issuance.
3. **Housekeeping Module** — task generation, room status machine, maintenance ticketing.
4. **POS Interface** — charge capture at F&B and ancillary outlets, routed to guest folios.
5. **Folio & Billing Engine** — charge aggregation, tax computation, invoice generation.
6. **Channel Manager Bridge** — two-way ARI sync with OTA and GDS channels.
7. **Revenue Management Module** — dynamic pricing, BAR, yield rules, forecast tools.
8. **Loyalty Engine** — point ledger, tier evaluation, benefit application.
9. **Reporting & Analytics** — occupancy, RevPAR, ADR, channel performance, audit reports.
10. **Admin & Configuration** — user roles, rate plans, room types, property settings.

All modules communicate via internal event buses and share a common guest profile and reservation data model, ensuring a single source of truth across the platform.

## Functional Requirements

### Reservation Management

**RM-001** The system shall allow staff and integrated booking engines to create reservations specifying: property, room type, arrival date, departure date, number of guests, rate plan, and special requests.

**RM-002** Reservations shall support the following statuses: `Enquiry`, `Tentative`, `Confirmed`, `Checked-In`, `Checked-Out`, `Cancelled`, `No-Show`, `Waitlisted`.

**RM-003** Staff shall be able to modify any confirmed reservation field (dates, room type, rate plan, guest count, special requests) with a full audit trail capturing the before/after state, operator identity, and timestamp.

**RM-004** Cancellation workflows shall enforce configurable cancellation policies per rate plan. The system shall calculate and post applicable cancellation fees to the folio automatically when a reservation is cancelled within a restricted window.

**RM-005** The system shall support group reservations: a single group block can encompass multiple rooms, with shared and individual billing options. Group blocks shall support rooming list upload (CSV or API), partial release of rooms back to inventory, and a group master folio.

**RM-006** A waitlist feature shall allow reservations to be queued when the desired room type or property is sold out. When inventory becomes available (due to cancellations or room type changes), the system shall notify the next waitlist entry in priority order and allow staff to confirm or release the slot within a configurable window.

**RM-007** OTA and GDS bookings shall be imported automatically via the Channel Manager Bridge. Imported reservations shall be validated against current inventory before acceptance; duplicate prevention logic shall reject bookings already matched by channel confirmation number.

**RM-008** Each reservation shall support multiple rate plan options: BAR (Best Available Rate), contracted corporate rates, package rates, promotional codes, loyalty member rates, and negotiated group rates. Rate plan visibility shall be role-gated (e.g., staff may view net rates; guests see only retail rates).

**RM-009** The system shall generate a unique confirmation number for every reservation and deliver an automated email or SMS confirmation to the guest upon booking, modification, and cancellation.

**RM-010** Staff shall be able to attach notes, preferences, and file attachments (e.g., signed contracts for groups) to any reservation record.

**RM-011** The system shall maintain a complete guest profile linked across reservations, capturing stay history, preferences, loyalty membership, communication language, and consent flags.

**RM-012** Reservation search shall support lookup by: confirmation number, guest name (fuzzy), company name, arrival/departure date range, room number, and channel reference ID.

### Front Desk Operations (Check-In / Check-Out)

**FD-001** The system shall present an arrivals dashboard showing all reservations due to arrive on the current date, sortable by arrival time estimate, VIP status, loyalty tier, group affiliation, and room readiness.

**FD-002** Walk-in reservations shall be created at the front desk without a prior booking. The system shall search availability in real time and create a confirmed reservation and check-in in a single workflow.

**FD-003** An early arrival queue shall capture guests who arrive before their room is ready. The system shall notify front desk staff automatically when a queued guest's assigned room reaches `Inspected` status.

**FD-004** Check-in shall require identity verification. The system shall record the ID type, ID number, and expiry date collected from the guest, with optional image attachment. Properties operating in jurisdictions requiring police reporting shall trigger an automated submission upon check-in.

**FD-005** Room assignment shall be performed manually by staff or via automatic assignment rules. Auto-assignment rules shall consider: room type match, floor preferences, VIP/loyalty tier adjacency, connecting-room requirements, and housekeeping readiness status.

**FD-006** The system shall interface with property keycard systems (e.g., ASSA ABLOY, dormakaba, Salto) via standard APIs to issue, re-encode, and deactivate electronic keycards at check-in and check-out. Mobile key issuance via the guest app shall also be supported.

**FD-007** At check-out, the system shall present a folio review screen displaying all charges, credits, and adjustments. Staff shall be able to add last-minute charges, apply discounts, and split the folio before finalising payment.

**FD-008** Split folio workflows shall allow division of charges by: category (room vs. F&B vs. extras), guest (for multi-occupancy), or company (e.g., room to company, incidentals to personal card). Each split folio shall produce an independent invoice.

**FD-009** Late checkout fees shall be calculated automatically based on the property's late checkout fee schedule (configurable per room type and time bracket). Staff shall have an override capability with mandatory reason capture for audit.

**FD-010** Express checkout shall allow guests to settle their folio via the guest portal or mobile app without visiting the front desk. The system shall send the final invoice by email and deactivate keycards at the confirmed checkout time.

**FD-011** The system shall support pre-authorisation of a credit card at check-in for an estimated incidental hold amount (configurable per property). The authorisation shall be released automatically at check-out if no incidentals remain, or captured for the actual incidental amount.

**FD-012** No-show processing shall be available as a bulk operation on the departures-plus-one-day report. The system shall post no-show fees per rate plan policy and set reservation status to `No-Show`.

### Room and Housekeeping Management

**HK-001** The system shall maintain a room inventory with attributes including: room number, room type, floor, building, bed configuration, occupancy capacity, accessibility features, smoking status, view type, and current status.

**HK-002** Room status shall follow a defined state machine: `Occupied` → `Dirty` (on checkout) → `In Progress` (housekeeping starts) → `Clean` → `Inspected` → `Available`. Additional states: `Out of Order` (OOO), `Out of Service` (OOS), `Do Not Disturb` (DND), `Refused Service`.

**HK-003** The system shall auto-generate housekeeping tasks for every checkout, assigning them to the housekeeping queue for the departure date. Task assignments shall account for floor zones and staff workload balancing.

**HK-004** Housekeeping supervisors shall be able to set priorities on tasks (Standard, Priority, VIP, RUSH). VIP and loyalty-tier guests' rooms shall be auto-elevated to Priority or VIP priority.

**HK-005** The mobile housekeeping application shall present each housekeeper with their assigned task queue. Housekeepers shall be able to update room status in real time, add notes, and flag issues directly from the app.

**HK-006** Maintenance requests shall be raised by housekeeping, front desk, or engineering staff. Each request shall capture: room number, issue category, description, severity, and photos. Requests shall be assigned to the engineering team queue and tracked to resolution.

**HK-007** Room discrepancies (e.g., system shows `Vacant Clean` but housekeeper finds the room occupied) shall be flaggable by housekeepers. Discrepancies shall trigger an alert to the front desk supervisor for resolution.

**HK-008** Stay-over rooms shall generate a `Service` task each day according to the property's service schedule policy. Guests who opt out of daily service (eco or DND preference) shall suppress the task automatically.

**HK-009** A room status dashboard shall display the floor-plan view with colour-coded room status indicators. Supervisors shall be able to filter by status, floor, housekeeper assignment, and priority.

**HK-010** Shift handoff reports shall be generated automatically at configurable times (e.g., morning/evening shift change), summarising outstanding tasks, rooms still dirty, maintenance open items, and discrepancies.

### Point of Sale

**POS-001** The system shall integrate with property POS terminals (restaurant, bar, spa, room service, gift shop) to receive charges in real time and route them to the correct guest folio.

**POS-002** POS charges shall include: outlet name, server/staff ID, item descriptions, quantities, unit prices, VAT/GST breakdown, and timestamp. Each POS transaction shall be a discrete, immutable folio line item.

**POS-003** Payment methods accepted at POS outlets shall include: cash, debit/credit card (via integrated terminal), room charge (post to guest folio), city ledger (post to corporate account), and loyalty points redemption.

**POS-004** Room charge postings shall validate that the guest is currently checked in and that the guest's folio is open before accepting the charge. Failed validations shall be surfaced to POS staff with a specific error message.

**POS-005** Authorised staff shall be able to post manual charges or adjustments to a guest folio from the front desk module (e.g., amenity fees, parking, tour bookings), with mandatory category tagging and reason entry.

**POS-006** The system shall support package inclusions (e.g., breakfast included, spa credit). When a guest redeems an included item at a POS outlet, the system shall offset the charge against the package allowance and only post the overage amount to the folio.

**POS-007** Voids and refunds on POS charges shall be permitted only by authorised roles. A void reverses a charge on the same business day; a refund creates a credit line item for prior-day charges. Both actions require a mandatory reason and are logged in the audit trail.

### Folio and Billing

**FB-001** Every checked-in guest shall have at least one open folio. A folio shall record all charges (room rate, taxes, POS postings, ancillary fees) and credits (payments, discounts, adjustments, package offsets) in chronological order.

**FB-002** The billing engine shall calculate applicable taxes automatically based on the property's tax configuration (tax rate, tax type, rounding rules, inclusive vs. exclusive, exemption rules for loyalty or corporate accounts).

**FB-003** The system shall support city ledger billing: charges and the final invoice are deferred to a corporate account (AR). City ledger transactions shall feed the property's accounts receivable module or export to the integrated accounting system.

**FB-004** Night audit processing shall run automatically at the configurable end-of-day time. Night audit shall post nightly room charges, apply package components, roll the business date, generate daily financial summaries, and archive the audit report.

**FB-005** Invoice PDFs shall be generated on demand or at checkout. Invoices shall be branded with the property logo, full itemised charges, tax summary, payment summary, and legal compliance fields (VAT number, fiscal receipt number where required by jurisdiction).

**FB-006** Staff shall be able to apply adjustments (discounts, complimentary credits, error corrections) to any open folio line. All adjustments require a mandatory reason code and are captured in the audit trail with staff identity.

**FB-007** The system shall support advance deposits: a deposit folio line is created at booking, the payment is captured or pre-authorised, and the deposit is applied against the final bill at checkout.

**FB-008** Multiple payment methods shall be accepted at checkout, including split payment across two or more cards, cash plus card, loyalty points plus card, and city ledger plus card. Each payment leg shall be recorded individually on the folio.

**FB-009** The folio shall be shareable with the guest via a secure, tokenised web link that renders a live read-only view of their current charges, refreshed on each page load.

**FB-010** Folios and invoices shall be retained for a minimum of seven years in immutable storage for audit and tax purposes.

### OTA Channel Synchronisation

**OTA-001** The system shall maintain a channel manager integration layer capable of connecting to major channel managers (SiteMinder, STAAH, Cloudbeds, RateGain, etc.) and directly to OTAs via their native APIs where available.

**OTA-002** Availability, rates, and inventory (ARI) updates shall be pushed to all connected channels within 60 seconds of a change event in the HPMS inventory engine. Bulk updates (e.g., closing a room type for renovations) shall propagate to all channels atomically.

**OTA-003** The system shall receive booking notifications from channels in real time. Each incoming booking shall be validated, de-duplicated, mapped to internal room type and rate plan, and confirmed or rejected with an appropriate response message.

**OTA-004** Booking modifications received from channels (date changes, guest count, room type upgrades initiated by the OTA) shall be applied to the existing reservation and trigger re-evaluation of the applicable rate plan. Staff shall be notified of externally originated modifications.

**OTA-005** Cancellations received from channels shall update reservation status to `Cancelled`, post applicable cancellation fees per rate plan policy, and release the inventory back to all channels within 60 seconds.

**OTA-006** The system shall maintain a per-channel log of all outbound ARI messages and inbound booking events, including payload, response code, latency, and error descriptions. This log shall be queryable by channel, date range, and error type.

**OTA-007** Channel-specific stop-sell, min/max length of stay, closed to arrival, and closed to departure restrictions shall be configurable per room type, rate plan, and date range. Changes shall propagate to channels in the standard ARI push cycle.

**OTA-008** The system shall support parity monitoring: alerting revenue managers when rate parity between channels deviates beyond a configurable threshold.

### Revenue Management

**RV-001** The system shall maintain rate plans with attributes: name, description, currency, base rate, day-of-week modifiers, minimum stay, maximum stay, cancellation policy, inclusions (meals, transfers), and commission model.

**RV-002** Best Available Rate (BAR) shall be the dynamic baseline rate, adjustable by revenue managers per room type per day. All derived rates (e.g., corporate at −10% of BAR, OTA at +15% of net) shall update automatically when BAR changes.

**RV-003** Dynamic pricing rules shall allow automatic BAR adjustments based on: occupancy thresholds, days-to-arrival windows, pickup velocity, competitor rate index (if integrated), and season/event calendars.

**RV-004** Yield restriction controls shall include: stop-sell (close room type to further bookings), minimum length of stay (MLOS), maximum length of stay, closed-to-arrival (CTA), and closed-to-departure (CTD). Each restriction shall be configurable per room type, channel, and date range.

**RV-005** A pickup report shall display, for each future arrival date: the number of rooms picked up in the last 1/7/30 days, occupancy percentage, current BAR, and pace versus same-time-last-year.

**RV-006** Forecast tools shall project occupancy, ADR, and RevPAR for a rolling 90-day horizon using historical pace data, current bookings, and configurable market assumptions. Forecasts shall be exportable to CSV.

**RV-007** The system shall integrate with or provide a rate-shopping interface to display competitor rates from OTAs for configurable comp-set properties on a given date.

**RV-008** An overbooking management tool shall allow revenue managers to set an overbooking buffer (e.g., accept up to 103% of room count) per room type per date, with automatic stop-sell triggers when the buffer is exhausted.

**RV-009** Revenue managers shall be able to create promotional codes that override the BAR with a fixed discount amount or percentage. Codes shall be single-use or multi-use, with expiry dates and optional minimum stay requirements.

### Loyalty Programme

**LY-001** Guest profiles shall include a loyalty membership record with: membership number, tier (e.g., Member, Silver, Gold, Platinum), points balance, lifetime points earned, tier qualification window, and benefit entitlements.

**LY-002** Points shall be earned on eligible charges at configurable earn rates per currency unit (e.g., 10 points per $1 spent on room rate, 5 points per $1 on F&B). Ineligible charge categories (taxes, government fees) shall be excluded from earn calculations.

**LY-003** Points shall be redeemable at checkout or at POS outlets at a configurable redemption rate (e.g., 100 points = $1 credit). Partial redemption shall be allowed; the remaining balance shall be settled by another payment method.

**LY-004** Tier evaluations shall run nightly. Tier upgrades shall be applied immediately; downgrades shall be deferred to the end of the tier qualification window. Guests shall receive automated notifications on tier changes.

**LY-005** Benefits by tier shall be configurable per property: complimentary room upgrades (subject to availability), late checkout eligibility, welcome amenity, guaranteed room type, lounge access flags, and bonus point multipliers.

**LY-006** A loyalty points history ledger shall record every earn and redemption event with: reservation or folio reference, points amount, transaction type, and timestamp. Guests shall be able to view this ledger via the guest portal.

**LY-007** Points expiry rules shall be configurable: points expire after a period of inactivity (e.g., 12 months without a qualifying stay) or after an absolute calendar date. The system shall send expiry warning notifications at configurable lead times (e.g., 60 and 30 days before expiry).

## Non-Functional Requirements

### Availability and Reliability

**NFR-AV-001** The production environment shall achieve a minimum uptime SLA of **99.9%** (≤ 8.7 hours downtime per year), measured on a rolling 30-day basis, excluding pre-approved maintenance windows.

**NFR-AV-002** Planned maintenance windows shall be scheduled during off-peak hours (02:00–04:00 local property time), notified at least 72 hours in advance, and shall not exceed 60 minutes per window.

**NFR-AV-003** The system shall implement automated health checks and circuit breakers for all external integrations (channel managers, payment gateways, keycard systems). Degraded mode operation shall allow front desk check-in/out to continue without external dependency when integrations are unavailable.

**NFR-AV-004** Data shall be replicated across at least two geographically separated availability zones. Recovery Point Objective (RPO) shall not exceed 5 minutes; Recovery Time Objective (RTO) shall not exceed 30 minutes.

**NFR-AV-005** All critical workflows (check-in, check-out, folio posting) shall be covered by end-to-end synthetic monitoring with alerting to on-call engineering staff when a scenario fails.

### Performance

**NFR-PE-001** API responses for all read operations shall complete at the **p95 latency of ≤ 200 ms** under normal load conditions (defined as ≤ 10,000 concurrent users).

**NFR-PE-002** Page load time for the staff portal (Time to Interactive) shall not exceed 2 seconds on a standard wired connection.

**NFR-PE-003** The system shall sustain **10,000 concurrent authenticated users** across all properties without performance degradation beyond the stated p95 latency thresholds.

**NFR-PE-004** Night audit processing shall complete within 15 minutes for a single property with up to 500 rooms and 1,000 active folios.

**NFR-PE-005** ARI push to all connected channels shall complete within **60 seconds** of an inventory change event for 95% of update events.

**NFR-PE-006** Report generation for standard reports (daily manager's report, pickup report, occupancy forecast) shall complete within 10 seconds for a single property and within 60 seconds for a portfolio of 100 properties.

### Security and Compliance

**NFR-SC-001** Payment card data shall be handled in compliance with **PCI-DSS Level 1**. The HPMS shall not store full card numbers (PAN) in any persistent store; all card data shall be tokenised via the payment service provider before storage.

**NFR-SC-002** The system shall comply with **GDPR** (EU) and equivalent data protection regulations. Guest personal data shall be stored with explicit consent records, subject to right-to-erasure requests within 30 days, and exportable via a structured data download on request.

**NFR-SC-003** All data in transit shall be encrypted using **TLS 1.2 or higher**. All data at rest shall be encrypted using AES-256 or equivalent.

**NFR-SC-004** Authentication shall support **multi-factor authentication (MFA)** for all staff roles. Session tokens shall expire after 8 hours of inactivity. Failed login attempts shall trigger progressive lockout (3 attempts → 5-minute lockout, 10 attempts → account lock requiring admin reset).

**NFR-SC-005** Role-based access control (RBAC) shall enforce the principle of least privilege. Pre-defined roles shall include: Front Desk Agent, Front Desk Supervisor, Housekeeper, Housekeeping Supervisor, Revenue Manager, F&B Cashier, Property Manager, Group Admin, and System Admin. Custom role creation shall be supported.

**NFR-SC-006** A tamper-evident audit log shall record every data mutation (create, update, delete) on reservation, folio, guest profile, rate plan, and user account records. Audit log entries shall include: entity type, entity ID, field-level diff, user ID, IP address, and UTC timestamp. Audit logs shall be immutable and retained for 7 years.

**NFR-SC-007** All API endpoints shall enforce authentication (OAuth 2.0 / API key) and rate limiting. Public-facing endpoints shall be protected by a WAF (Web Application Firewall).

**NFR-SC-008** Penetration testing shall be performed at least annually by a qualified third-party assessor. Critical and high findings shall be remediated within 30 days of report delivery.

### Scalability and Multi-Property

**NFR-SM-001** The platform shall support a minimum of **100 active properties** per group account without architectural changes, scaling to 500+ properties with horizontal infrastructure scaling.

**NFR-SM-002** Property data shall be logically isolated. Cross-property data access shall only be permitted to group-level roles and shall be enforced at the data access layer, not merely the UI layer.

**NFR-SM-003** Each module shall be independently deployable and scalable. Increased load on the POS posting service shall not require scaling of the reservation engine.

**NFR-SM-004** The platform shall support multi-currency operations. Each property shall be configurable with a base currency; folio charges shall be recorded in the transaction currency and converted to base currency using configurable exchange rate sources updated daily.

**NFR-SM-005** Multi-language support (UI and guest communications) shall include at minimum: English, Spanish, French, German, Arabic, Japanese, and Simplified Chinese.

### Maintainability

**NFR-MN-001** The codebase shall maintain a minimum test coverage of 80% for unit and integration tests across all core modules.

**NFR-MN-002** All public APIs shall be documented using OpenAPI 3.0 specification, kept in sync with the implementation via CI/CD pipeline validation.

**NFR-MN-003** Application logs shall be structured (JSON), correlated by trace ID, and shipped to a centralised observability platform (e.g., Datadog, Elastic Stack). Log retention shall be 90 days hot, 1 year cold.

**NFR-MN-004** Deployments shall use zero-downtime blue/green or canary strategies. Rollback to the prior version shall be achievable within 5 minutes.

**NFR-MN-005** Database schema migrations shall be backward-compatible for at least one prior API version to allow staged rollouts.

## Constraints

**C-001** The system must operate on a cloud infrastructure (AWS, Azure, or GCP) without dependency on on-premise servers at the property level, except for network hardware and POS terminals.

**C-002** The guest-facing portal and staff portal must be fully functional on evergreen browsers (Chrome, Safari, Firefox, Edge — current and prior major version) without requiring browser plugins.

**C-003** The mobile housekeeping application must function on Android 10+ and iOS 15+ devices.

**C-004** All external OTA integrations must use the channel manager's certified API. Direct OTA integration shall only be permitted where the OTA provides a certified connectivity partner programme.

**C-005** Night audit must be atomic: if any step fails, the entire audit rolls back, an alert is raised, and the prior business date is preserved until the issue is resolved and the audit is re-run.

**C-006** The platform must be deployable within a single regulatory jurisdiction's cloud region for properties subject to data residency requirements (e.g., EU data residency under GDPR).

**C-007** Integration contracts (API versions) shall be maintained for a minimum of 12 months before deprecation, with advance notice of at least 6 months.

## Assumptions

**A-001** Properties will have reliable broadband internet with a minimum uptime of 99% at the property. The system does not provide offline-first operation for the staff portal beyond a read-only cached mode.

**A-002** Each property will designate at least one system administrator responsible for user provisioning, room configuration, and rate plan setup during onboarding.

**A-003** Channel manager vendors are responsible for maintaining their own API connectivity to OTAs. The HPMS is responsible only for delivering accurate ARI data to the channel manager.

**A-004** Guest-facing mobile key issuance requires compatible smart-lock hardware already installed at the property. Hardware procurement is outside the scope of this system.

**A-005** Loyalty programme rules (earn rates, tier thresholds, benefit definitions) are configured per property group by the Group Admin. The system enforces these rules but does not determine the commercial policy.

**A-006** Tax rules and fiscal compliance requirements (e.g., fiscal receipt numbering, electronic tax reporting) will be configured per property based on local legal requirements. The vendor will provide configuration templates for major jurisdictions but not legal advice.

**A-007** Historical reservation and guest data migration from legacy PMS platforms is a one-time onboarding activity and is out of scope for this document; a separate data migration plan will be produced for each property onboarding.

## Glossary

| Term | Definition |
|---|---|
| **ADR** | Average Daily Rate. Total room revenue divided by the number of rooms sold in a given period. A key hotel performance metric. |
| **ARI** | Availability, Rates, and Inventory. The three core data elements synchronised between the PMS and distribution channels. |
| **BAR** | Best Available Rate. The lowest publicly available rate for a room type on a given date, used as the baseline for all rate derivation. |
| **Channel Manager** | A middleware platform that aggregates and synchronises ARI data between the PMS and multiple OTAs and GDS channels. |
| **City Ledger** | An accounts receivable account used to defer payment from a guest's folio to a corporate or travel agent billing account settled periodically. |
| **CTA / CTD** | Closed to Arrival / Closed to Departure. Yield restrictions that prevent new bookings with an arrival or departure on a specified date. |
| **Folio** | The running account of all charges, credits, and payments associated with a guest's stay at the property. |
| **GDS** | Global Distribution System. A network (e.g., Sabre, Amadeus, Travelport) used by travel agents to search and book hotel rates. |
| **MLOS** | Minimum Length of Stay. A yield restriction requiring bookings to include at least N consecutive nights to be valid. |
| **Night Audit** | The end-of-day accounting process that posts nightly room charges, closes the business date, and generates financial summary reports. |
| **No-Show** | A confirmed reservation where the guest did not arrive and did not cancel within the cancellation policy window. |
| **OTA** | Online Travel Agency. A web-based platform (e.g., Booking.com, Expedia) through which guests can search and book hotel rooms. |
| **PAN** | Primary Account Number. The 14–16 digit number embossed on a payment card. PCI-DSS prohibits storage of unencrypted PANs. |
| **PCI-DSS** | Payment Card Industry Data Security Standard. A set of security standards governing organisations that process, store, or transmit payment card data. |
| **RevPAR** | Revenue Per Available Room. Total room revenue divided by total available rooms in a period. Combines occupancy and ADR into a single KPI. |
| **Room Type** | A category of rooms sharing the same bed configuration, capacity, and feature set (e.g., Standard King, Deluxe Twin, Junior Suite). |
| **Yield Management** | The practice of adjusting pricing and availability restrictions in real time to maximise revenue based on demand forecasts and booking pace. |
