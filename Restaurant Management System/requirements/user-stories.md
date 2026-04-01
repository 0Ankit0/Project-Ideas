# User Stories - Restaurant Management System

## Overview and Persona Summary

This document contains user stories for the Restaurant Management System (RMS), organized by epic and persona. Each story follows the standard format with acceptance criteria, priority, and story point estimates. Stories are implementation-ready and intended for use in agile sprint planning.

### Persona Descriptions

| Persona | Description | Primary Goals |
|---------|-------------|---------------|
| **Guest / Customer** | A person dining at the restaurant, either walk-in or with a reservation. May be tech-savvy or not. Wants a smooth, enjoyable dining experience without friction. | Easy reservations, accurate orders, transparent billing, fast service |
| **Host / Reception Staff** | Staff member stationed at the entrance responsible for managing arrivals, reservations, seating, and the waitlist. Works from a tablet or desktop terminal. | Minimize wait times, seat guests quickly, zero overbooking, clear floor visibility |
| **Waiter / Server** | Front-of-house staff member responsible for taking orders, coordinating service, managing table communication, and facilitating bill settlement. Works from a tablet POS. | Fast order capture, accurate kitchen routing, easy modifications, quick bill split |
| **Chef / Kitchen Staff** | Back-of-house staff member responsible for food preparation. Reads kitchen tickets from a KDS screen. Works in a physically demanding, time-sensitive environment. | Clear ticket queue, station-specific orders, real-time status visibility, stock awareness |
| **Cashier** | Staff member responsible for processing payments, managing the cash drawer, handling refunds, and closing the drawer session at end of shift. | Accurate bill totals, fast settlement, multi-tender support, clean drawer close |
| **Restaurant Manager** | Operations manager responsible for overall floor and kitchen performance, staff coordination, and exception handling. Has approval authority for voids, discounts, and refunds. | Real-time floor visibility, kitchen SLA monitoring, exception approvals, daily close |
| **Inventory Manager** | Staff member responsible for ingredient tracking, stock counts, procurement, and wastage management. Works from a backoffice interface. | Accurate stock levels, timely procurement, low-stock prevention, variance accountability |
| **Delivery Staff** | Staff member responsible for packing delivery orders, coordinating with aggregator drivers, and managing delivery dispatch from the restaurant. | Clear packing lists, real-time driver status, accurate delivery time estimates |
| **System Administrator** | Technical or senior management role responsible for platform configuration, role management, integration setup, and audit oversight. | Secure access control, stable integrations, audit compliance, multi-branch governance |

---

## Epic 1: Reservation and Seating Management

**US-01: Make a Table Reservation**
As a **Guest**, I want to book a table online for a specific date, time, and party size, so that I can guarantee seating without waiting in line when I arrive.
- Acceptance Criteria:
  - Guest can select branch, date, time slot, and party size from available options
  - System rejects the booking if no suitable table is available for the requested time
  - Guest receives a confirmation via SMS and/or email with booking reference, date, time, and branch address
  - Reservation appears on the host dashboard immediately after confirmation
- Priority: High
- Story Points: 8

**US-02: Manage Waitlist for Walk-In Guests**
As a **Host**, I want to add walk-in guests to a digital waitlist with an estimated wait time, so that they can wait comfortably without crowding the entrance.
- Acceptance Criteria:
  - Host can add guest name, party size, contact number, and seating preference to the waitlist
  - System calculates and displays estimated wait time based on current table occupancy and average turn times
  - Guest receives an SMS notification when their table is ready
  - Host can remove guests from the waitlist if they choose to leave
- Priority: High
- Story Points: 5

**US-03: View and Manage the Reservation Timeline**
As a **Host**, I want to see a consolidated 4-hour reservation timeline alongside the live floor map, so that I can proactively plan seating assignments before guests arrive.
- Acceptance Criteria:
  - Timeline shows confirmed reservations, walk-in queue positions, and projected table availability for the next 4 hours
  - Clicking a reservation shows guest details, party size, notes, and contact information
  - Host can reassign a reservation to a different table without losing the original booking reference
  - Overbooking attempt triggers a clear warning before the host can override
- Priority: High
- Story Points: 8

**US-04: Modify or Cancel a Reservation**
As a **Guest**, I want to modify the time or party size of my reservation, or cancel it entirely, so that I can adapt to changes in my plans without penalty within the allowed window.
- Acceptance Criteria:
  - Guest can modify date, time, or party size up to the configurable cancellation cutoff time
  - Cancellation within the allowed window releases the table slot and sends a confirmation notification
  - Late cancellation or no-show triggers a configurable penalty workflow
  - Modified reservation is reflected on the host dashboard within 30 seconds
- Priority: High
- Story Points: 5

**US-05: Seat a Guest and Assign a Waiter**
As a **Host**, I want to seat an arriving guest by assigning them to a specific table and notifying the assigned waiter, so that service begins immediately without communication delays.
- Acceptance Criteria:
  - Host can assign a guest to any available table from the floor map
  - System validates that the selected table has sufficient capacity for the party size
  - Assigned waiter receives a notification on their POS tablet showing the table and party details
  - Table status changes to "Occupied" on the floor map within 1 second of assignment
- Priority: High
- Story Points: 5

**US-06: Handle No-Show Reservations**
As a **Host**, I want the system to alert me when a reserved guest has not arrived within the grace period, so that I can reclaim the table for walk-in guests.
- Acceptance Criteria:
  - System triggers a no-show alert after the configurable grace period (default: 15 minutes)
  - Host can mark the reservation as "No-Show" with one action, releasing the table
  - No-show event is logged in guest history and triggers any applicable penalty policy
  - Table returns to "Available" status on the floor map immediately after no-show confirmation
- Priority: Medium
- Story Points: 3

---

## Epic 2: Menu Browsing and Order Placement

**US-07: Browse Menu and Place a Dine-In Order**
As a **Waiter**, I want to browse the full menu with categories, items, and modifiers on my tablet POS, so that I can capture a guest's order accurately and quickly during table service.
- Acceptance Criteria:
  - Menu displays categories, items, descriptions, prices, and allergen tags
  - Waiter can add items to the order, select modifiers, and add special notes
  - System shows unavailable items in a visually distinct way and prevents adding them
  - Order draft is auto-saved every 30 seconds to prevent data loss
- Priority: High
- Story Points: 8

**US-08: Assign Items to Specific Seats**
As a **Waiter**, I want to assign each ordered item to a specific seat number at the table, so that split billing by seat is accurate and delivery to the correct guest is straightforward.
- Acceptance Criteria:
  - Waiter can select a seat number for each item during order entry
  - Seat assignments are visible on the kitchen ticket and the bill
  - Items without a seat assignment default to "shared"
  - Seat assignment can be changed before order submission without losing other order data
- Priority: High
- Story Points: 5

**US-09: Fire Courses at the Right Time**
As a **Waiter**, I want to control when each course is sent to the kitchen, so that the guest's dining pace is respected.
- Acceptance Criteria:
  - Order entry separates items into courses (appetizer, main, dessert) during capture
  - Waiter can hold mains and desserts and manually fire them when ready
  - System can be configured to auto-fire the next course when preceding course is marked "served"
  - Course fire action is logged with timestamp and actor
- Priority: High
- Story Points: 5

**US-10: Modify or Add to an Existing Order**
As a **Waiter**, I want to add new items to a table's order or modify quantities after submission, so that I can accommodate guest requests without creating a new order.
- Acceptance Criteria:
  - Waiter can add new items to an open check at any point before bill closure
  - New items are sent to the kitchen as a supplementary ticket immediately
  - Quantity decreases require manager approval and reason code
  - All modifications are visible in order history with actor, timestamp, and description
- Priority: High
- Story Points: 5

**US-11: Apply Discounts and Promotions**
As a **Waiter**, I want to apply a pre-configured discount or promotion code to an order, so that I can honor guest vouchers or manager-approved concessions.
- Acceptance Criteria:
  - Waiter can select from a list of active discounts applicable to the current order
  - Discounts requiring manager authorization prompt for approval before being applied
  - Applied discount is itemized on the bill with name, type, and value
  - System prevents stacking incompatible discounts with a clear error message
- Priority: Medium
- Story Points: 5

**US-12: Place a Takeaway Order**
As a **Waiter or Cashier**, I want to create a takeaway order with a collection time, so that the kitchen can prepare the order for pick-up at the right time.
- Acceptance Criteria:
  - Staff can create a new order in Takeaway mode without assigning a table
  - Takeaway order includes customer name, contact number, and requested collection time
  - Kitchen receives the takeaway ticket with a TAKEAWAY label and collection time
  - Tickets fire automatically at the appropriate lead time before collection
- Priority: High
- Story Points: 5

---

## Epic 3: Kitchen Operations

**US-13: View Station-Specific Ticket Queue on KDS**
As a **Chef**, I want to see only the tickets routed to my station on the Kitchen Display System, so that my display is uncluttered and I can focus on my station's work.
- Acceptance Criteria:
  - KDS displays only tickets assigned to the logged-in station
  - Tickets are displayed in priority order (VIP/expedite first, then chronological)
  - Each ticket shows table number, order time, item names, modifiers, and special notes
  - New tickets appear on the KDS within 3 seconds of order submission
- Priority: High
- Story Points: 8

**US-14: Update Ticket Preparation Status**
As a **Kitchen Staff Member**, I want to update a ticket's status using the KDS touchscreen, so that front-of-house staff know when food is ready.
- Acceptance Criteria:
  - KDS provides large, touch-optimized status buttons for each state transition
  - Status update propagates to the waiter's POS within 2 seconds
  - Ticket changes color coding to indicate current state
  - Overdue tickets are highlighted in red with an elapsed time indicator
- Priority: High
- Story Points: 5

**US-15: Flag a Stock Shortage During Service**
As a **Chef**, I want to flag an ingredient shortage directly from the KDS, so that waiters can inform guests and offer alternatives.
- Acceptance Criteria:
  - Chef can tap an item on the KDS and select "Flag as Out of Stock"
  - Flag immediately marks the menu item as unavailable on all POS terminals branch-wide
  - Affected in-flight orders show a warning on waiter tablets
  - Inventory manager receives a real-time low-stock alert
- Priority: High
- Story Points: 5

**US-16: Manage Ticket Refire for Quality Issues**
As a **Chef**, I want to initiate a refire for a ticket when a dish needs to be re-prepared, so that guest satisfaction is maintained and waste is tracked.
- Acceptance Criteria:
  - Chef can select a reason for refire (quality issue, preparation error, guest request)
  - Refire creates a new ticket in the queue while original is marked "Voided - Refire"
  - Refire event logs reason, original ticket ID, chef ID, and timestamp
  - Waiter receives a notification that the item is being refired with updated ready time
- Priority: Medium
- Story Points: 3

**US-17: View Table Order Completion Progress**
As a **Restaurant Manager**, I want a real-time overview of all active kitchen tickets grouped by table, so that I can identify tables at risk of long delays.
- Acceptance Criteria:
  - Manager dashboard shows tables grouped by service progress (on-track, at-risk, overdue)
  - At-risk threshold is configurable per branch
  - Manager can send an expedite signal to a specific station ticket from the dashboard
  - Dashboard refreshes automatically every 15 seconds
- Priority: High
- Story Points: 8

**US-18: Coordinate Pass and Multi-Station Dish Dispatch**
As an **Expediter**, I want to see all items for a table across all stations and only release when all items for a course are simultaneously ready.
- Acceptance Criteria:
  - Pass view shows all tickets for each table grouped by course with per-station status
  - Table is only flagged "Ready to Serve" when all course items show "Ready at Pass"
  - Expediter can hold a table's "Ready" status if the service floor is not ready
  - Pass coordination events are logged with actor and timestamp
- Priority: Medium
- Story Points: 5

---

## Epic 4: Billing and Payment

**US-19: Generate and Review a Bill**
As a **Cashier**, I want to generate a bill for a table showing all items, taxes, charges, and discounts, so that the guest can review the total before payment.
- Acceptance Criteria:
  - Bill shows each item with quantity, unit price, modifier details, and subtotal
  - Tax breakdown shows each applicable tax type and amount separately
  - Service charge and discounts are shown as separate line items
  - Bill total is computed with zero rounding inconsistencies
- Priority: High
- Story Points: 5

**US-20: Split a Bill by Seat or Item**
As a **Waiter**, I want to split the bill by individual seat or by specific items, so that groups of guests can pay their own shares.
- Acceptance Criteria:
  - Waiter can choose to split by equal shares, by seat assignment, or by item selection
  - Each split produces an independent sub-check that can be settled separately
  - Shared items can be divided equally or assigned manually
  - All sub-checks remain linked to the original table order for audit
- Priority: High
- Story Points: 8

**US-21: Process Multi-Tender Payment**
As a **Cashier**, I want to accept multiple payment methods for a single bill, so that guests can pay in whatever combination is convenient.
- Acceptance Criteria:
  - Cashier can apply partial payment by cash, card, digital wallet, or QR code in sequence
  - System tracks the remaining balance after each tender
  - Final tender must cover at least the remaining balance; change calculation shown for cash
  - Each tender is recorded as a separate line in the drawer session
- Priority: High
- Story Points: 5

**US-22: Process a Void or Refund**
As a **Cashier**, I want to void an incorrect item or process a refund on a settled check with manager authorization.
- Acceptance Criteria:
  - Void of an unsettled item requires a reason code; manager approval required post-fire
  - Refund on a settled check requires manager PIN or approval acknowledgment
  - Refund creates a negative ledger entry linked to the original transaction
  - Refund receipt is automatically printed and cashier session totals are updated
- Priority: High
- Story Points: 8

**US-23: Open and Close a Cashier Drawer Session**
As a **Cashier**, I want to open a drawer session with a declared opening balance and close it with a physical cash count, so that my session totals are auditable.
- Acceptance Criteria:
  - Drawer open requires entry of opening cash balance before any transactions
  - Drawer close requires physical count entry for each cash denomination
  - System calculates expected cash total and flags variance above threshold
  - Variance requires manager acknowledgment before session can be closed
- Priority: High
- Story Points: 5

**US-24: Apply Loyalty Points Redemption at Checkout**
As a **Cashier**, I want to look up a guest's loyalty balance and apply points as a discount at checkout.
- Acceptance Criteria:
  - Cashier can search for guest by phone number or loyalty card ID
  - System shows current point balance and maximum applicable discount value
  - Cashier can apply full or partial redemption; system deducts applied points immediately
  - Redemption is shown as a discount line item on the bill and receipt
- Priority: Medium
- Story Points: 5

---

## Epic 5: Table and Floor Management

**US-25: View Real-Time Floor Map**
As a **Host**, I want a real-time visual floor map showing every table's status, occupancy, elapsed time, and assigned server.
- Acceptance Criteria:
  - Floor map renders all tables with color-coded status indicators
  - Each table tile shows party size, elapsed time, server name, and open check count
  - Floor map updates in real-time; changes appear within 1 second
  - Host can filter view by section, zone, or server assignment
- Priority: High
- Story Points: 8

**US-26: Merge Tables for Large Parties**
As a **Host**, I want to merge two or more adjacent tables into a single combined seating for a large party.
- Acceptance Criteria:
  - Host can select two or more adjacent tables and merge them
  - Merged table group shows combined capacity and a single unified check
  - Any existing orders on individual tables are consolidated into the merged check
  - Merge action is logged with host ID, table IDs, and timestamp
- Priority: Medium
- Story Points: 5

**US-27: Split a Table Back to Individual Tables**
As a **Host**, I want to split a merged table back into individual tables when a party reduces in size.
- Acceptance Criteria:
  - Host can initiate split on a merged table, reassigning order items to correct individual tables
  - System prevents split if there are unresolved payment intents on the shared check
  - Split creates separate independent checks for each resulting table
  - Resulting individual table statuses are immediately updated on the floor map
- Priority: Medium
- Story Points: 5

**US-28: Transfer a Table to a Different Server**
As a **Restaurant Manager**, I want to transfer a table's active order from one server to another for workload rebalancing.
- Acceptance Criteria:
  - Manager can select a table and reassign it to any active server on the floor
  - Previous server's table count decreases and new server's count increases on floor map
  - All order history and notes are preserved after the transfer
  - Both old and new server receive a transfer notification
- Priority: Medium
- Story Points: 3

**US-29: Mark a Table as Cleaning and Release**
As a **Waiter or Host**, I want to mark a table as "Cleaning" after guests leave and "Available" once it is reset.
- Acceptance Criteria:
  - Waiter or host can mark a settled table as "Cleaning" from the floor map or POS
  - Table tile shows "Cleaning" status with a timestamp
  - Authorized staff can mark the table "Available" once physically ready
  - System optionally notifies the next waitlisted guest when a table becomes available
- Priority: High
- Story Points: 3

---

## Epic 6: Inventory Management

**US-30: Track Ingredient Stock Levels**
As an **Inventory Manager**, I want to see current stock levels alongside reorder thresholds and usage rates, so that I can anticipate shortages before they impact service.
- Acceptance Criteria:
  - Inventory dashboard shows each ingredient with quantity, unit, threshold, and last-updated timestamp
  - Ingredients below reorder threshold are highlighted; stockouts are highlighted in red
  - Usage rate (last 7 days average) is displayed next to each ingredient
  - Inventory manager can filter by category and branch
- Priority: High
- Story Points: 5

**US-31: Conduct a Periodic Stock Count**
As an **Inventory Manager**, I want to submit a physical stock count for all ingredients to identify variances.
- Acceptance Criteria:
  - Inventory manager can open a stock count session and enter physical quantities
  - System calculates variance (physical minus theoretical) per ingredient
  - Variances outside tolerance require a reason code and supervisor acknowledgment
  - Completed stock count is saved as an immutable record
- Priority: High
- Story Points: 8

**US-32: Create and Track a Purchase Order**
As an **Inventory Manager**, I want to create purchase orders for low-stock ingredients and track them through receipt.
- Acceptance Criteria:
  - Inventory manager can create a PO with vendor, delivery date, and line items
  - PO routes to branch manager for approval before being sent to vendor
  - Received quantities update stock levels immediately; discrepancies are flagged
  - PO history is searchable with filter by vendor, status, and date range
- Priority: High
- Story Points: 8

**US-33: Log Wastage and Spillage**
As a **Chef or Inventory Manager**, I want to log ingredient waste events with reason and quantity.
- Acceptance Criteria:
  - Staff can create a wastage entry specifying ingredient, quantity, reason, and date
  - Wastage quantity is deducted from theoretical stock immediately
  - Wastage events appear in inventory variance report as auditable adjustments
  - Manager receives daily wastage summary when above configurable threshold
- Priority: Medium
- Story Points: 3

---

## Epic 7: Staff Management

**US-34: Create and Publish a Shift Schedule**
As a **Branch Manager**, I want to create weekly shift schedules for all roles and publish them to staff.
- Acceptance Criteria:
  - Manager can assign staff members to shifts by role, start time, end time, and station
  - System warns if a staff member is scheduled for overlapping shifts
  - Published schedule is visible to each staff member on their dashboard
  - Manager can duplicate last week's schedule as a starting template
- Priority: High
- Story Points: 8

**US-35: Record Staff Clock-In and Clock-Out**
As a **Staff Member**, I want to clock in at the start of my shift and clock out at the end.
- Acceptance Criteria:
  - Staff can clock in using their staff PIN at the branch terminal
  - System cross-references clock-in time against the scheduled shift and flags early/late arrivals
  - Clock-out records end time and calculates total hours
  - Branch manager can view real-time attendance coverage
- Priority: High
- Story Points: 5

**US-36: Manage Role-Based Access Permissions**
As a **System Administrator**, I want to configure role templates with granular feature permissions.
- Acceptance Criteria:
  - Admin can create, edit, and clone role templates with per-feature permission toggles
  - Role assignment to a staff member takes effect immediately
  - Access attempts outside a staff member's permissions are logged as security events
  - Admin can view audit trail of all role changes with before/after state
- Priority: High
- Story Points: 8

**US-37: Approve or Reject Shift Swap Requests**
As a **Branch Manager**, I want to review and approve or reject shift swap requests between staff members.
- Acceptance Criteria:
  - Staff member can submit a swap request specifying the shift and colleague accepting
  - Manager receives a notification with both staff members' details and the affected shift
  - Approved swap updates the schedule for both staff members immediately
  - Rejected swap notifies the requesting staff member with reason
- Priority: Low
- Story Points: 3

---

## Epic 8: Delivery Management

**US-38: Receive Orders from Delivery Aggregators**
As a **Restaurant Manager**, I want incoming delivery orders from Uber Eats, DoorDash, and Zomato to appear automatically in the POS and kitchen systems.
- Acceptance Criteria:
  - Orders from connected aggregators appear in POS order queue within 30 seconds
  - Delivery orders are clearly labeled with aggregator name and external order ID
  - Kitchen receives the delivery ticket routed to correct station(s)
  - Manager can view a combined feed showing dine-in, takeaway, and delivery orders
- Priority: High
- Story Points: 13

**US-39: Track Delivery Driver Assignment and Status**
As a **Delivery Staff Member**, I want to see driver assignment status and estimated pickup time for each delivery order.
- Acceptance Criteria:
  - Delivery dispatch screen shows each active order with driver name, estimated pickup time, and packing status
  - Staff can update packing status (packing, ready for pickup, handed to driver) with one tap
  - Manager receives an alert if a driver arrives and the order is not yet ready
  - Delivery status is synced from aggregator API in real-time
- Priority: Medium
- Story Points: 8

**US-40: Handle Delivery Order Cancellation or Modification**
As a **Restaurant Manager**, I want to process delivery cancellations and modifications without losing kitchen queue integrity.
- Acceptance Criteria:
  - Aggregator cancellation triggers immediate kitchen ticket void for unstarted items
  - For in-progress items, manager receives alert to decide whether to proceed or cancel
  - Modified orders re-route corrected kitchen tickets within 30 seconds
  - Cancelled orders are excluded from sales totals but retained in audit log
- Priority: Medium
- Story Points: 5

**US-41: Separate Delivery Sales Reporting**
As a **Branch Manager**, I want to view sales broken down by channel (dine-in, takeaway, delivery).
- Acceptance Criteria:
  - Daily sales dashboard shows revenue, order count, and average order value by channel
  - Delivery channel report includes gross sales, aggregator commission, and net revenue
  - Manager can export channel-level sales data for any date range as CSV
  - Historical comparison shows week-over-week and month-over-month channel trends
- Priority: Medium
- Story Points: 5

---

## Epic 9: Loyalty Program

**US-42: Earn Loyalty Points on Every Purchase**
As a **Guest**, I want loyalty points to be automatically credited to my account when I settle a bill.
- Acceptance Criteria:
  - Points are calculated based on net bill amount at the configured earn rate
  - Points are credited to the guest's account within 5 minutes of bill settlement
  - Guest receives an SMS or notification showing points earned and new balance
  - Points are not awarded on voided or fully refunded transactions
- Priority: Medium
- Story Points: 5

**US-43: View Loyalty Balance and Transaction History**
As a **Guest**, I want to view my current loyalty point balance and a history of all earn and redeem transactions.
- Acceptance Criteria:
  - Guest can access their loyalty balance via the restaurant web portal
  - Transaction history shows date, branch, points earned/redeemed, and bill reference
  - Balance is shown in both points and equivalent monetary value
  - History can be filtered by date range and branch
- Priority: Low
- Story Points: 3

**US-44: Configure Loyalty Earn and Redeem Rules**
As a **System Administrator**, I want to configure loyalty earn rate, redemption value, and minimum threshold.
- Acceptance Criteria:
  - Admin can set earn rate as points per currency unit
  - Admin can configure category-specific earn rate multipliers
  - Admin can set minimum redemption threshold
  - Rule changes take effect from the next transaction after the effective date
- Priority: Low
- Story Points: 5

---

## Epic 10: Reporting and Analytics

**US-45: View Real-Time Sales Dashboard**
As a **Branch Manager**, I want a real-time sales dashboard showing today's revenue, order count, and average bill value.
- Acceptance Criteria:
  - Dashboard shows gross revenue, order count, average order value, and net revenue
  - Metrics update in near-real-time (under 2 minutes lag)
  - Manager can toggle between daily, weekly, and monthly views
  - Dashboard is accessible on mobile browser without full admin login
- Priority: High
- Story Points: 8

**US-46: Generate End-of-Day Settlement Report**
As a **Restaurant Manager or Cashier**, I want to generate a day-end settlement report summarizing all transactions and payment methods.
- Acceptance Criteria:
  - Report includes total sales, total refunds, net revenue, tax collected, and service charges
  - Payment method breakdown shows cash, card, wallet, and other tender totals
  - Report is generated within 30 seconds of day-close sign-off
  - Report is exportable as PDF and CSV
- Priority: High
- Story Points: 5

**US-47: Monitor Kitchen SLA Performance**
As a **Restaurant Manager**, I want to view a kitchen performance report showing average preparation times per station and SLA breach counts per shift.
- Acceptance Criteria:
  - Report shows average, p75, and p95 preparation time per station and menu category
  - SLA breach count shows tickets that exceeded the target preparation time
  - Manager can drill down into specific shift or date range
  - Report highlights stations with breach rates above 10%
- Priority: Medium
- Story Points: 8
