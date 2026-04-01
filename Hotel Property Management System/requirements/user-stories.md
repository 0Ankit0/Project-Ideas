# Hotel Property Management System — User Stories

## Story Format and Definition of Done

### Story Format

Each user story in this document follows the standard format below:

```
**US-XXX — [Title]**
*As a [role], I want to [action] so that [benefit].*

**Acceptance Criteria:**
- [Specific, testable criterion]
- [Specific, testable criterion]
- ...

**Priority:** High / Medium / Low
**Estimate:** S (≤ 1 day) / M (2–4 days) / L (5–10 days)
```

### Definition of Done

A user story is considered **Done** when all of the following conditions are met:

1. All acceptance criteria are verified by a QA engineer in the staging environment.
2. Unit and integration tests covering the new behaviour are written and passing (≥ 80% branch coverage on changed code).
3. The feature is reviewed and approved in a pull request by at least one senior engineer.
4. API changes are reflected in the OpenAPI 3.0 specification and documentation site.
5. Relevant audit log events are emitted and verifiable in the observability platform.
6. UI changes have passed accessibility review (WCAG 2.1 AA compliance).
7. The product owner has accepted the story in a demo session.
8. No open Critical or High severity defects are related to the story.

### Roles

| Role | Description |
|---|---|
| **Front Desk Staff** | Hotel employees at the reception desk responsible for guest arrivals, departures, and folio management. |
| **Housekeeper** | On-property cleaning and room preparation staff, including supervisors. |
| **Revenue Manager** | Staff responsible for pricing strategy, channel management, and demand forecasting. |
| **Guest** | A hotel customer interacting with self-service digital touchpoints (web portal, mobile app). |
| **Property Owner** | General managers, owners, or group-level executives monitoring property or portfolio performance. |

---

## Front Desk Staff Stories

**US-001 — Standard Guest Check-In**
*As a Front Desk Staff member, I want to check a guest in against their confirmed reservation so that they receive their room key and their stay is activated in the system.*

**Acceptance Criteria:**
- Staff can search for the reservation by confirmation number, guest name, or arrival date from the arrivals dashboard.
- The system displays reservation details: room type, rate plan, number of nights, special requests, and loyalty tier.
- Staff can assign an available, inspected room from a filtered list of matching room types.
- The system captures ID type and ID number as mandatory fields before completing check-in.
- Upon confirmation, room status changes to `Occupied`, a folio is opened, and a keycard issuance prompt is displayed.
- The guest receives an automated check-in confirmation SMS or email within 60 seconds.
- The entire check-in workflow completes in under 3 minutes on a standard workstation.

**Priority:** High
**Estimate:** M

---

**US-002 — Walk-In Guest Check-In**
*As a Front Desk Staff member, I want to create a reservation and check in a walk-in guest in a single workflow so that I do not need to navigate between separate screens.*

**Acceptance Criteria:**
- A "Walk-In" action on the arrivals dashboard opens a combined reservation-creation and check-in form.
- The system displays only rooms that are currently available and in `Inspected` status.
- Staff can select a room type and specific room, and the system calculates the applicable walk-in BAR rate.
- Payment method (card pre-authorisation or cash deposit) is captured before check-in is finalised.
- The completed check-in assigns a room, opens a folio, and displays the keycard issuance prompt.
- The workflow does not require the staff member to exit and re-enter any module.

**Priority:** High
**Estimate:** M

---

**US-003 — Early Arrival Queue Management**
*As a Front Desk Staff member, I want to add an arriving guest to an early arrival queue so that I can notify them automatically when their room is ready without making them wait at the desk.*

**Acceptance Criteria:**
- A "Queue for Early Arrival" action is available on any reservation with a same-day arrival date and no available room of the requested type.
- Queuing a guest records an estimated arrival time, contact number, and preferred notification channel (SMS/email/both).
- When a room of the matching type transitions to `Inspected` status, the system automatically sends the guest a notification and creates a front-desk alert.
- Front desk staff can view all currently queued guests on a panel, showing queue position and room readiness status.
- Staff can manually trigger the notification or re-queue a guest if the initially offered room is declined.

**Priority:** High
**Estimate:** M

---

**US-004 — Room Assignment with Preference Matching**
*As a Front Desk Staff member, I want the system to suggest the best available room based on guest preferences so that I can assign rooms quickly without manually reviewing each option.*

**Acceptance Criteria:**
- The room assignment panel displays guest preferences pulled from their profile (floor preference, view type, bed configuration, accessibility requirements).
- The system ranks available, inspected rooms against the preferences and highlights the best match.
- Staff can accept the suggested room or override it with any other available room.
- Overrides are logged in the audit trail with the staff member's name and the timestamp.
- Assigning a room updates room status to `Reserved` and prevents double-assignment.
- Connecting-room requests show both rooms as a paired option when both are available.

**Priority:** High
**Estimate:** M

---

**US-005 — Group Check-In**
*As a Front Desk Staff member, I want to check in all or a subset of a group's rooms in a single operation so that large group arrivals are processed efficiently.*

**Acceptance Criteria:**
- A group block view lists all reservations under the group with their status, assigned room, and guest name.
- Staff can pre-assign rooms to all group reservations before the group arrives using a bulk assignment tool.
- A "Check In Selected" action allows staff to check in multiple group members simultaneously after verifying IDs.
- Each individual guest receives their own check-in confirmation message; the group master account is updated to reflect checked-in room count.
- Any group reservation that cannot be checked in (e.g., room not ready, ID not presented) is flagged and excluded from the batch, without blocking the rest.
- The group master folio and individual folios are both visible and correctly linked.

**Priority:** High
**Estimate:** L

---

**US-006 — Folio Adjustment at Check-Out**
*As a Front Desk Staff member, I want to add, void, or discount charges on a guest folio before finalising check-out so that the invoice accurately reflects what the guest owes.*

**Acceptance Criteria:**
- The folio review screen at check-out presents all charges in chronological order with category labels.
- Staff can add a new charge by selecting a charge category, entering an amount, and providing a description.
- Staff can void a same-day charge or apply a credit adjustment to a prior-day charge, both requiring a mandatory reason code.
- Discount application (percentage or fixed amount) requires the staff member's role to have `Discount` permission; discounts above a configurable threshold require supervisor approval.
- All adjustments are reflected in the updated folio total in real time before the payment step.
- Every adjustment creates an immutable audit log entry with staff identity, reason code, amount, and timestamp.

**Priority:** High
**Estimate:** M

---

**US-007 — Split Folio at Check-Out**
*As a Front Desk Staff member, I want to split a guest's folio into two or more separate invoices so that the room charge is billed to a company account and personal charges are billed to the guest.*

**Acceptance Criteria:**
- A "Split Folio" action is available on any open folio before check-out is finalised.
- Staff can split by charge category (e.g., all `Room Rate` and `Tax` items to Folio A; all `F&B` and `Misc` to Folio B).
- Staff can also manually drag individual line items between folio splits.
- Each split folio displays its own sub-total, tax summary, and payment section.
- A different payment method can be assigned to each split (e.g., Folio A → City Ledger; Folio B → Visa ending 4242).
- Two separate invoices are generated at check-out, each with a unique invoice number.
- The original folio reference links to both split invoices for audit purposes.

**Priority:** High
**Estimate:** M

---

**US-008 — Express Check-Out Processing**
*As a Front Desk Staff member, I want to process an express check-out for a guest who has already settled their folio via the guest portal so that I can complete their departure without requiring them to queue at the desk.*

**Acceptance Criteria:**
- The departures dashboard flags reservations where the guest has completed express check-out via the portal.
- Staff can review the auto-settled folio and confirm the check-out with a single click.
- Upon confirmation, room status changes to `Dirty`, keycards are remotely deactivated, and a final invoice email is sent to the guest.
- If the guest's express payment failed (e.g., card declined), the reservation is returned to a `Pending Check-Out` status and the guest is notified to visit the desk.
- Express check-outs completed before 10:00 AM waive any late check-out fee automatically.

**Priority:** Medium
**Estimate:** M

---

## Housekeeper Stories

**US-009 — View Daily Task List**
*As a Housekeeper, I want to view my assigned task list for the day on my mobile device so that I know which rooms to service and in what order.*

**Acceptance Criteria:**
- The mobile app displays the housekeeper's assigned tasks sorted by priority (RUSH → VIP → Priority → Standard) and then by floor/zone.
- Each task card shows: room number, task type (Checkout Clean, Stayover Service, Inspection), current room status, and any guest notes or special requests.
- The list refreshes automatically when a new task is assigned or reprioritised by the supervisor.
- Tapping a task card shows the full room details, including bed type, occupancy count, and any maintenance flags.
- The app works on both Android 10+ and iOS 15+ devices and remains usable with a 2G-equivalent connection (offline queue sync when connectivity is restored).

**Priority:** High
**Estimate:** M

---

**US-010 — Update Room Status in Real Time**
*As a Housekeeper, I want to update the status of a room directly from my mobile device so that front desk staff can assign it to arriving guests without delay.*

**Acceptance Criteria:**
- The housekeeper can transition a room through the status sequence: `Dirty` → `In Progress` → `Clean` from the task card.
- Changing status to `In Progress` timestamps the start of the service; changing to `Clean` timestamps completion and calculates service duration.
- Status updates are reflected on the front desk room status dashboard within 5 seconds.
- A `Clean` status notification is sent to the front desk supervisor for rooms flagged as Priority or VIP.
- The housekeeper cannot skip the `In Progress` state; they must tap "Start" before they can tap "Finish".
- Status changes are logged with housekeeper identity and GPS confirmation that the device is on-property (configurable toggle per property).

**Priority:** High
**Estimate:** M

---

**US-011 — Flag a Maintenance Issue**
*As a Housekeeper, I want to flag a maintenance issue from within the room I am servicing so that the engineering team can address it promptly without requiring me to find a phone or supervisor.*

**Acceptance Criteria:**
- A "Report Issue" button is accessible from any task card in the mobile app.
- The housekeeper selects an issue category (Plumbing, Electrical, HVAC, Furniture, IT/TV, Other) and enters a description.
- Photo attachments (up to 5 images) can be added via the device camera.
- Severity is set by the housekeeper (Low, Medium, High, Urgent); Urgent issues immediately alert the on-duty engineering supervisor via push notification.
- The submitted maintenance request appears in the engineering team's work queue and is linked to the room record.
- If the issue prevents the room from being cleaned, the housekeeper can change room status to `Out of Service` pending resolution.

**Priority:** High
**Estimate:** M

---

**US-012 — Prioritise VIP and Loyalty Tier Rooms**
*As a Housekeeping Supervisor, I want VIP and high-tier loyalty guest rooms to be automatically elevated to Priority status so that these guests receive their rooms before other arriving guests.*

**Acceptance Criteria:**
- When a reservation is linked to a guest with a loyalty tier of Gold or above, or is flagged as VIP by front desk, the associated housekeeping task is automatically set to VIP or Priority level.
- VIP tasks are sorted to the top of the relevant housekeeper's task list.
- The supervisor's dashboard displays a VIP room count and its current status alongside a countdown to the VIP guest's expected arrival time.
- If a VIP room has not reached `Clean` status 2 hours before the expected arrival time, an escalation alert is sent to the housekeeping supervisor.
- Priority re-assignment of a VIP room to a different housekeeper (for speed) is available as a one-click supervisor action with a push notification sent to the newly assigned housekeeper.

**Priority:** Medium
**Estimate:** M

---

**US-013 — Shift Handoff Report**
*As a Housekeeping Supervisor, I want to generate and share a shift handoff report so that the incoming supervisor is fully briefed on outstanding tasks, room discrepancies, and open maintenance items.*

**Acceptance Criteria:**
- A "Generate Handoff Report" action in the supervisor dashboard produces a report showing: number of rooms cleaned, number still dirty or in-progress, open maintenance requests, room discrepancies awaiting resolution, and tasks reassigned during the shift.
- The report is generated within 10 seconds and is viewable in-app and downloadable as PDF.
- The supervisor can annotate the report with freeform notes before sharing.
- The report can be shared with specific users (by name or role) via in-app notification.
- The incoming supervisor receives a notification and must acknowledge the report receipt within the app.

**Priority:** Medium
**Estimate:** S

---

## Revenue Manager Stories

**US-014 — Set and Publish a Rate Plan**
*As a Revenue Manager, I want to create and publish a new rate plan so that bookings made on or after the publication date use the correct pricing for the intended market segment.*

**Acceptance Criteria:**
- The rate plan form requires: name, applicable room types, date range, base rate per night, day-of-week modifiers, cancellation policy, inclusions (meals, transfers), minimum stay, and distribution channels.
- A preview panel shows the effective rate calendar for the next 90 days before publishing.
- Publishing a rate plan pushes the rates to all connected channels within 60 seconds (confirmed by a green status indicator per channel).
- If a channel push fails, the rate plan is marked `Partially Published` with a per-channel error log available for review.
- Rate plans can be saved as draft, published immediately, or scheduled for future publication with a date/time selector.

**Priority:** High
**Estimate:** M

---

**US-015 — View and Analyse Pickup Report**
*As a Revenue Manager, I want to view a pickup report for the next 30 days so that I can identify which arrival dates are filling slowly and need a pricing intervention.*

**Acceptance Criteria:**
- The pickup report displays one row per future arrival date with columns: total room capacity, rooms sold, occupancy %, rooms picked up in last 1/7/30 days, current BAR, and pace vs. STLY (same time last year).
- Dates where occupancy is below a configurable threshold (e.g., < 50%) are highlighted in amber; dates where pace is more than 10% below STLY are highlighted in red.
- Revenue managers can click any date to drill into a channel and room-type breakdown.
- The report can be exported to CSV with all columns and date range preserved.
- Report data is current as of the last 15-minute refresh cycle; a manual refresh button is available.

**Priority:** High
**Estimate:** M

---

**US-016 — Apply Yield Restrictions**
*As a Revenue Manager, I want to apply a minimum length of stay restriction on high-demand dates so that short stays do not erode average revenue during peak periods.*

**Acceptance Criteria:**
- The yield restrictions panel allows the revenue manager to select a date range, room type(s), and restriction type: MLOS, CTA, CTD, or Stop-Sell.
- MLOS requires a minimum nights value (1–30). CTA and CTD are boolean toggles per date. Stop-Sell closes all booking acceptance for the selected scope.
- Restrictions can be applied per channel or across all channels simultaneously.
- Applied restrictions are displayed on the rate calendar as colour-coded overlays.
- All restrictions push to connected channels within 60 seconds; push status is confirmed per channel.
- Removing a restriction (opening back up) follows the same workflow and also propagates within 60 seconds.

**Priority:** High
**Estimate:** M

---

**US-017 — Forecast Occupancy and Revenue**
*As a Revenue Manager, I want to view a 90-day occupancy and revenue forecast so that I can plan pricing strategy and staffing recommendations proactively.*

**Acceptance Criteria:**
- The forecast view displays projected occupancy %, ADR, and RevPAR for each of the next 90 days.
- Forecast methodology is documented in a tooltip: based on historical pace curves, current on-books data, and seasonality index.
- Revenue managers can overlay market events (concerts, conferences, holidays) from a built-in calendar to contextualise demand spikes.
- An "Apply Suggested Pricing" feature generates recommended BAR adjustments for dates where the forecast diverges significantly from the STLY baseline; changes require manual confirmation before applying.
- The forecast report is exportable to Excel with a data dictionary sheet included.

**Priority:** High
**Estimate:** L

---

**US-018 — Competitor Rate Monitoring**
*As a Revenue Manager, I want to view competitor rates from OTAs alongside my own rates so that I can assess my price positioning and maintain appropriate rate parity.*

**Acceptance Criteria:**
- A competitor rate panel shows rates for up to 10 comp-set properties (configurable) for a selected date range, sourced from an integrated rate-shopping API or OTA scraper.
- The panel displays the lowest publicly available rate per comp-set property per night, alongside the property's own BAR for the same date.
- Dates where the property's BAR is more than 10% above the median comp-set rate are flagged with a suggested decrease action.
- Dates where the property's BAR is more than 10% below the median comp-set rate are flagged with a suggested increase action.
- Revenue managers can act on a suggested change directly from the panel, pre-populating the rate adjustment form with the recommended value.
- Data is refreshed at minimum twice daily; last refresh timestamp is visible on the panel.

**Priority:** Medium
**Estimate:** L

---

## Guest Stories

**US-019 — Online Pre-Arrival Check-In**
*As a Guest, I want to complete my check-in online before I arrive so that I can go directly to my room without waiting at the front desk.*

**Acceptance Criteria:**
- The guest receives a pre-arrival check-in invitation email or SMS 24–48 hours before arrival (timing configurable by property).
- The check-in flow collects: government ID details (type, number, expiry), estimated arrival time, and credit card for incidentals.
- The guest can review their reservation details and submit any last-minute special requests during the flow.
- Upon completion, the guest receives a digital confirmation with a mobile key (if the property supports mobile keys) or a notification that their physical key will be ready on arrival.
- Online check-in data pre-populates the front desk check-in screen, reducing staff data entry to ID verification only.
- If the guest's room is not yet available at the time of online check-in, the system queues them and sends an automatic notification when the room is ready.

**Priority:** High
**Estimate:** L

---

**US-020 — Room Upgrade Request**
*As a Guest, I want to request a room upgrade after making my booking so that I can secure a better room if one becomes available.*

**Acceptance Criteria:**
- The guest portal shows available upgrade options (room types above the booked type) with their respective upgrade rates or complimentary eligibility (based on loyalty tier).
- The guest can request a specific upgrade type; the request is queued in the front desk module for manual approval or auto-approval based on property policy.
- The guest receives an email/SMS notification within 24 hours confirming whether the upgrade was granted or declined.
- If granted, the reservation is updated with the new room type and any rate differential is added to the folio.
- Complimentary upgrades for eligible loyalty members do not generate a rate differential charge.
- The guest can withdraw an upgrade request at any time before confirmation.

**Priority:** Medium
**Estimate:** M

---

**US-021 — View Current Folio**
*As a Guest, I want to view my current folio charges via the guest portal so that I can review my spending before check-out and avoid billing surprises.*

**Acceptance Criteria:**
- The guest portal shows a live folio view with all posted charges, including room rate, taxes, F&B charges, and ancillary fees.
- Charges are grouped by date and category for readability.
- Each charge displays: date, description, outlet/source, amount, and currency.
- The total amount due is displayed prominently and updates in real time as new charges are posted.
- The folio is accessible via a secure, tokenised URL that expires at midnight following check-out.
- The guest can download a preliminary invoice PDF at any time during their stay.

**Priority:** High
**Estimate:** M

---

**US-022 — Loyalty Points Balance and History**
*As a Guest, I want to view my loyalty points balance and transaction history in the guest portal so that I know how many points I have and can plan redemptions.*

**Acceptance Criteria:**
- The guest portal displays current points balance, loyalty tier, and tier progression (e.g., "2,500 more points to Gold").
- A transaction history table shows each earn and redemption event: date, property, reservation reference, points amount (positive for earn, negative for redeem), and running balance.
- The guest can filter history by date range and event type (earn / redeem / expiry).
- A "Points Expiry" notice is shown prominently if any points are due to expire within 90 days.
- The points balance is updated within 24 hours of check-out.

**Priority:** Medium
**Estimate:** M

---

**US-023 — Submit Special Requests**
*As a Guest, I want to submit special requests for my stay (e.g., high floor, extra pillows, anniversary decoration) so that the hotel can prepare for my preferences before I arrive.*

**Acceptance Criteria:**
- The guest can submit special requests at the time of booking, via the pre-arrival check-in flow, or via the portal at any time before check-out.
- Request types include: room preference (floor, view, location), bed configuration, accessibility needs, dietary requirements, celebration decorations, and freeform notes.
- Submitted requests appear on the reservation record in the PMS, flagged for the relevant department (front desk, housekeeping, F&B).
- The guest receives a confirmation that their request has been received and a note that it is subject to availability.
- Requests are visible to all relevant staff departments on the arrivals dashboard.

**Priority:** Medium
**Estimate:** S

---

**US-024 — Request Late Check-Out**
*As a Guest, I want to request a late check-out via the guest portal so that I can sleep in without having to call the front desk.*

**Acceptance Criteria:**
- The late check-out request option appears in the guest portal from 6:00 PM the day before departure.
- Available late check-out time slots (e.g., 12:00, 13:00, 14:00) are presented based on real-time availability for the room type.
- Selecting a time slot shows the applicable late checkout fee (if any), with complimentary slots highlighted for eligible loyalty members.
- The guest confirms the request; the system notifies the front desk and automatically updates the expected departure time on the reservation.
- If the selected slot becomes unavailable (e.g., next arrival assigned to the same room), the request is escalated to front desk to offer an alternative.
- A confirmation message with the approved time is sent to the guest by email/SMS.

**Priority:** Medium
**Estimate:** M

---

**US-025 — Split Payment at Check-Out**
*As a Guest completing express check-out, I want to split my folio payment across two cards so that I can allocate business expenses to my corporate card and personal charges to my own card.*

**Acceptance Criteria:**
- The express check-out payment screen allows the guest to add a second payment method.
- The guest can specify a fixed amount or percentage to charge to each card.
- Both cards are charged in sequence; if either charge fails, the guest is prompted to provide an alternative method before the check-out is finalised.
- The final invoice reflects both payment legs with the card type and last four digits for each.
- Split payment is also available for loyalty point redemption as one of the payment legs.

**Priority:** Medium
**Estimate:** M

---

## Property Owner Stories

**US-026 — Multi-Property Operational Dashboard**
*As a Property Owner, I want a consolidated dashboard showing key operational metrics across all my properties so that I can quickly identify which properties need attention today.*

**Acceptance Criteria:**
- The dashboard displays one card per property with: today's occupancy %, arrivals due, departures due, rooms out of order, and open maintenance items.
- Cards are sortable by occupancy, property name, and alert count.
- Clicking a property card navigates to that property's detailed operational view.
- Metrics on the dashboard are refreshed every 5 minutes; a last-refreshed timestamp is shown.
- Properties with occupancy below a configurable threshold or with more than a configurable number of open maintenance items are highlighted with a warning badge.
- The dashboard is accessible on desktop and mobile browsers without loss of functionality.

**Priority:** High
**Estimate:** M

---

**US-027 — Revenue Performance Report**
*As a Property Owner, I want to view a revenue performance report comparing ADR, RevPAR, and total revenue across properties and time periods so that I can evaluate portfolio-wide financial health.*

**Acceptance Criteria:**
- The report supports date range selection (day, week, month, custom range) and property grouping (individual property, region, all properties).
- Metrics displayed: total room revenue, ADR, occupancy %, RevPAR, total F&B revenue, total ancillary revenue, and gross total revenue.
- Each metric shows the current period value, prior period value, and period-over-period change (absolute and percentage).
- A bar chart visualises RevPAR across all selected properties side by side for the chosen period.
- The report is exportable to PDF (formatted for boardroom presentation) and Excel (raw data for further analysis).
- Data is calculated from the night audit records and is accurate as of the last completed business date.

**Priority:** High
**Estimate:** M

---

**US-028 — Occupancy KPI Monitoring**
*As a Property Owner, I want to track occupancy KPIs with trend lines over time so that I can assess whether my properties are trending towards or away from their targets.*

**Acceptance Criteria:**
- A KPI panel shows 30-day and 90-day rolling occupancy % trend lines per property on a line chart.
- Configurable occupancy targets can be set per property per month; the chart shows the target as a dashed reference line.
- The panel highlights the number of days in the selected period where occupancy was above or below target.
- A heatmap view (calendar-style) shows occupancy % per day for the trailing 6 months, colour-coded by performance band.
- KPI data is refreshed nightly after night audit completion.

**Priority:** Medium
**Estimate:** M

---

**US-029 — Channel Performance Analysis**
*As a Property Owner, I want to see which booking channels are delivering the most revenue and the best margins so that I can direct distribution investments appropriately.*

**Acceptance Criteria:**
- The channel performance report lists all active channels (Direct, Booking.com, Expedia, Airbnb, GDS, Corporate, Other) per property.
- For each channel and time period: total room nights booked, revenue generated, ADR, cancellation rate, and average lead time are displayed.
- A cost-per-booking column shows the estimated commission cost per channel (configurable commission rates per channel).
- Net contribution (revenue minus estimated commission) is calculated and displayed per channel.
- A pie chart shows the revenue mix by channel for the selected property and period.
- The report is exportable to CSV for use in third-party BI tools.

**Priority:** Medium
**Estimate:** M

---

**US-030 — Audit Trail Review**
*As a Property Owner, I want to query the system audit trail for a specific property, date range, and record type so that I can investigate any discrepancy or suspicious activity.*

**Acceptance Criteria:**
- The audit trail search accepts filters: property, date/time range (UTC), user, record type (Reservation, Folio, Guest Profile, Rate Plan, User Account), action type (Create, Update, Delete, Login, Failed Login), and entity ID.
- Results show: timestamp, user, IP address, action, entity type, entity ID, and a field-level diff (before/after values).
- Searches return results within 10 seconds for date ranges up to 90 days. Larger ranges display an asynchronous job with email notification on completion.
- The audit trail is read-only; no record can be modified or deleted via the UI or any API.
- Audit data is retained for a minimum of 7 years in accordance with compliance requirements.
- Audit trail access is restricted to Property Manager, Group Admin, and System Admin roles.

**Priority:** High
**Estimate:** M

---

## Cross-Cutting Stories

**US-031 — Real-Time Notifications and Alerts**
*As any staff member, I want to receive real-time in-app and push notifications for events relevant to my role so that I can respond to operational needs without constantly monitoring dashboards.*

**Acceptance Criteria:**
- Notification types are configurable per role: room ready alerts (front desk), VIP arrival escalations (housekeeping supervisor), pickup anomaly alerts (revenue manager), maintenance urgency alerts (engineering), and failed night audit alerts (property manager).
- Notifications are delivered via in-app bell icon, browser push notification, and optionally via SMS or email (user preference).
- Each notification links directly to the relevant record (room, reservation, maintenance ticket, rate plan).
- Notifications are marked as read when the linked record is opened; unread count is shown on the navigation badge.
- Notification delivery is guaranteed at-least-once; duplicate suppression prevents the same event generating more than one notification per user within a 60-second window.
- Staff can manage notification preferences (enable/disable per event type) from their profile settings.

**Priority:** High
**Estimate:** M

---

**US-032 — Immutable Audit Log for All Data Mutations**
*As a Compliance Officer or System Admin, I want every data mutation in the system to generate an immutable audit log entry so that I can demonstrate regulatory compliance and investigate any data integrity issues.*

**Acceptance Criteria:**
- Every create, update, and delete operation on a reservation, folio line, guest profile, rate plan, user account, and system configuration record produces an audit log entry automatically, without requiring explicit developer action at each call site (implemented via a cross-cutting infrastructure concern).
- Each audit entry captures: entity type, entity ID, field-level diff (JSON patch format), user ID, user role, client IP, user agent, and UTC timestamp.
- Audit entries are written to an append-only store; no delete or update operation exists on the audit log table, even for system administrators.
- The audit log is searchable via the admin UI (US-030) and via a dedicated audit API endpoint for integration with external SIEM tools.
- Bulk or automated system operations (e.g., night audit, channel ARI push) are attributed to a named system service identity, not a human user.

**Priority:** High
**Estimate:** L

---

**US-033 — External API Integration for Third-Party Systems**
*As an IT Administrator, I want to connect approved third-party systems (accounting software, BI tools, CRM) to the HPMS via a documented REST API so that data flows automatically without manual exports.*

**Acceptance Criteria:**
- The HPMS exposes a versioned REST API (v1, v2 etc.) documented in OpenAPI 3.0, accessible from the developer portal.
- API authentication uses OAuth 2.0 client credentials flow; API keys are also supported for server-to-server integrations.
- Rate limits are enforced per API key (configurable per integration; default: 1,000 requests/minute).
- Available endpoints cover all primary entities: reservations, guest profiles, folios, room inventory, rate plans, channel log, audit log (read-only), and reporting (async export).
- Webhook subscriptions allow third-party systems to receive push events (reservation created/modified/cancelled, folio closed, room status changed) without polling.
- API versioning policy guarantees backward compatibility for 12 months after a new version is published, with deprecation notices sent via the developer portal and email.

**Priority:** High
**Estimate:** L

---

**US-034 — Role-Based Access Control and User Provisioning**
*As a System Admin, I want to create user accounts, assign roles, and manage permissions so that staff access is aligned with their responsibilities and the principle of least privilege is maintained.*

**Acceptance Criteria:**
- The admin panel allows creation of user accounts with: name, email, property assignment(s), role assignment, and MFA enforcement toggle.
- Pre-defined roles are available (Front Desk Agent, Housekeeping, Revenue Manager, F&B Cashier, Property Manager, Group Admin, System Admin) and cannot be deleted but can be cloned as custom roles.
- Custom roles allow granular permission toggles at the module and action (read/write/delete/approve) level.
- Property assignment restricts the user's access to data for only their assigned properties; Group Admin role grants cross-property read access.
- A user list view shows all accounts with last login date, role, and active/inactive status, filterable by property and role.
- Deactivated accounts cannot log in but are retained for audit trail attribution; hard deletion is not permitted.
- Admin actions on user accounts (create, role change, deactivate) are themselves captured in the audit log.

**Priority:** High
**Estimate:** M

---

**US-035 — Multi-Language Guest Communications**
*As a Property Owner, I want all automated guest communications (confirmation emails, check-in invitations, folio receipts) to be delivered in the guest's preferred language so that the guest experience is personalised regardless of their country of origin.*

**Acceptance Criteria:**
- Guest profiles store a preferred communication language (default to browser locale if not specified; overridable by staff or the guest).
- Email and SMS templates are maintained in at least seven languages: English, Spanish, French, German, Arabic, Japanese, and Simplified Chinese.
- The correct template variant is selected automatically based on the guest's preferred language at the time of each communication trigger.
- Property admins can customise the wording of each template per language per property, with fallback to the default global template if no property-specific customisation exists.
- Template preview in the admin panel shows the rendered output for a selected language before saving.
- Right-to-left layout is applied automatically for Arabic; CJK character encoding is handled correctly for Japanese and Chinese.

**Priority:** Medium
**Estimate:** L
