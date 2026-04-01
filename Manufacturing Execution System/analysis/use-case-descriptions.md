# Use-Case Descriptions

## Overview

This document provides full structured specifications for nine high-priority use cases of the Manufacturing Execution System (MES). Each specification follows the Cockburn-style template extended with business rules, non-functional requirements, and UX notes. Use-case IDs align with `use-case-diagram.md`.

---

## UC-001: Create Production Order

| Field | Value |
|---|---|
| **Use Case ID** | UC-001 |
| **Name** | Create Production Order |
| **Version** | 1.2 |
| **Status** | Approved |
| **Author** | MES Business Analyst Team |
| **Last Revised** | 2025-01-15 |

### Actors
- **Primary:** Production Supervisor
- **Secondary:** ERP System (SAP) — provides order data via integration; MES System — validates and persists data

### Preconditions
1. The user is authenticated and holds the `PROD_SUPERVISOR` or `PROD_PLANNER` role.
2. A valid product master record exists in MES with an approved BOM revision and routing.
3. All required work centers are defined and capacity is available (or capacity override is permitted).
4. The SAP ERP interface connection is active (for auto-creation via sync).

### Postconditions
1. A production order record exists in MES with status `CREATED`.
2. The order is linked to the correct BOM version and routing version.
3. Required components are reserved (soft reservation) in the MES material ledger.
4. An audit log entry is created recording the creator, timestamp, and order parameters.
5. The production order appears in the scheduling board for the target work centers.

### Main Success Scenario
1. Production Supervisor navigates to **Production Orders → New Order**.
2. System displays the Create Production Order form with fields: Material Number, Order Quantity, Unit of Measure, Target Work Center, Planned Start Date, Planned End Date, Priority (1–5), and Notes.
3. Supervisor enters the material number; system auto-populates the material description, unit of measure, and default work center.
4. Supervisor enters order quantity and planned start/end dates.
5. System validates the requested quantity against minimum and maximum batch size rules (BR-011).
6. System retrieves the current approved BOM revision and routing from the MES master data repository.
7. System calculates the scheduled duration using standard operation times from the routing and available capacity on the target work center (finite scheduling algorithm).
8. System displays a capacity conflict warning if the planned window overlaps with committed orders; Supervisor may adjust dates or override (with justification).
9. Supervisor confirms and submits.
10. System assigns a unique Production Order Number (format: `PO-YYYYMMDD-NNNN`), sets status to `CREATED`, and persists the record.
11. System sends an acknowledgement notification to the Supervisor's dashboard.
12. If the order originated via ERP sync (UC-018), the SAP order number is stored as a cross-reference.

### Alternative Flows

**A1 – Manual creation with BOM override**
- At step 6, if no approved BOM exists, Supervisor may manually specify components (requires `BOM_OVERRIDE` permission).
- System flags the order with a `NON-STANDARD BOM` warning and requires a secondary approval before release.

**A2 – Copy from existing order**
- At step 2, Supervisor selects **Copy From Order**, enters a source order number.
- System pre-fills all fields from the source order; Supervisor modifies quantity and dates.
- Resumes at step 5.

**A3 – ERP-driven automatic creation (UC-018 trigger)**
- ERP System posts a production order payload via REST API `/api/v1/production-orders`.
- System validates the payload schema and business rules automatically.
- On success, order is created with status `CREATED` and `ERP_SYNCED` flag set; no human interaction required.
- Error payloads are written to the integration error queue and alerted to the integration admin.

### Exception Flows

**E1 – BOM not found**
- At step 6, if no BOM revision exists for the material, system displays error: *"No approved BOM found for material [number]. Contact Master Data team."*
- Order creation is blocked. System logs the event and sends an alert to the master data administrator.

**E2 – Capacity overload (hard limit)**
- At step 8, if the work center is at 100% capacity with no override permission, system blocks submission and displays: *"Work center [WC] is fully loaded for the selected window. Select a different date range."*

**E3 – Session timeout during entry**
- If the session expires mid-form, system auto-saves a draft. On re-login the Supervisor is prompted to resume the draft order.

**E4 – ERP integration payload schema error**
- In A3, if the ERP payload fails JSON schema validation, system returns HTTP 422 with a structured error body listing each failing field. No partial record is created.

### Business Rules Referenced
- **BR-001:** BOM and routing must exist and be in `APPROVED` status before a production order can be created.
- **BR-011:** Order quantity must be within the material's minimum batch size (MBS) and maximum batch size (MXBS) unless a capacity override is approved by Plant Manager.
- **BR-012:** Production orders inherit the BOM and routing version that is `APPROVED` at the time of creation; subsequent master data changes do not retroactively affect created orders.

### Non-Functional Requirements
- **Performance:** Form submission must complete and return order number within **2 seconds** for 95th percentile under normal load (≤500 concurrent users).
- **Availability:** The Create Order function must be available 99.5% of scheduled production hours.
- **Security:** Role-based access control enforced at API level. All form inputs are sanitized against SQL injection and XSS. Order data is encrypted at rest (AES-256).
- **Audit:** Every create/update event is written to an immutable audit log with user ID, timestamp (UTC), and change delta.

### UI/UX Notes
- The form uses a two-panel layout: input fields on the left, Gantt capacity preview on the right (live-updating as dates change).
- Material number field supports barcode scanner input and typeahead search (minimum 3 characters).
- Capacity preview highlights conflicts in amber (soft) and red (hard).
- After successful creation, the system navigates to the Order Detail view with a success toast notification.

---

## UC-002: Release Production Order

| Field | Value |
|---|---|
| **Use Case ID** | UC-002 |
| **Name** | Release Production Order |
| **Version** | 1.1 |

### Actors
- **Primary:** Production Supervisor
- **Secondary:** MES System (triggers work order generation and scheduling)

### Preconditions
1. The production order exists in status `CREATED` or `SCHEDULED`.
2. The Supervisor holds the `RELEASE_ORDER` permission.
3. All mandatory fields on the order are populated (BOM reference, routing reference, planned start date).
4. No active quality holds exist on the materials specified in the BOM (BR-006).
5. Required work centers have confirmed capacity for the planned window.

### Postconditions
1. Production order status transitions to `RELEASED`.
2. Individual operation work orders are generated for each routing step and assigned to the appropriate work centers.
3. Work orders appear in the operator queue on the relevant HMI terminals.
4. Component stock is hard-reserved in the MES material ledger.
5. A release timestamp and releasing user ID are recorded.
6. Scheduling board is refreshed to reflect the released order.
7. SAP ERP is notified of the release via the confirmation interface (status update only).

### Main Success Scenario
1. Supervisor opens the Production Order list, applies filter `Status = CREATED`.
2. Supervisor selects one or more orders and clicks **Release**.
3. System performs pre-release validation checks (BOM integrity, routing completeness, material availability, work center capacity).
4. System displays validation summary: green checks for passed rules, amber warnings for non-critical issues, red errors for blocking issues.
5. If no blocking errors, the **Confirm Release** button is enabled.
6. Supervisor reviews warnings (if any) and clicks **Confirm Release**.
7. System sets order status to `RELEASED`, generates work orders for each operation in the routing sequence.
8. System hard-reserves materials from available stock; triggers replenishment request if stock is insufficient (BR-013).
9. System pushes work orders to the HMI operator queues for the assigned work centers.
10. System sends a status-update notification to SAP ERP.
11. Supervisor sees the released orders highlighted in the scheduling Gantt chart.

### Alternative Flows

**A1 – Bulk release**
- At step 2, Supervisor selects multiple orders (up to 50).
- System validates each individually; displays a summary table of per-order validation results.
- Supervisor may proceed to release all valid orders while deferring failed ones.

**A2 – Release with date override**
- At step 3, if capacity conflict exists, Supervisor with `CAPACITY_OVERRIDE` permission may proceed.
- System records the override reason and requires a comment of ≥20 characters.

### Exception Flows

**E1 – Material stock insufficient**
- System marks the order with a `MATERIAL SHORTAGE` warning. Supervisor may release to shop floor but the work order is flagged; operator will be prompted to confirm material availability before starting.

**E2 – Routing step missing work center assignment**
- System blocks release with error: *"Operation [Op#] has no work center assigned. Update routing before release."*

### Business Rules Referenced
- **BR-001, BR-002, BR-006, BR-013**

### Non-Functional Requirements
- **Performance:** Single order release must complete within **3 seconds**. Bulk release of 50 orders must complete within **15 seconds**.
- **Security:** Release action is an audited, role-gated operation. Dual authorization required for orders with quantity > 10,000 units.

### UI/UX Notes
- Validation results are shown in a modal with collapsible sections for each check category.
- Batch release progress is shown via a progress bar with per-order status indicators.

---

## UC-003: Execute Work Order (Start / Complete Operations)

| Field | Value |
|---|---|
| **Use Case ID** | UC-003 |
| **Name** | Execute Work Order — Start and Complete Operations |
| **Version** | 2.0 |

### Actors
- **Primary:** Machine Operator
- **Secondary:** MES System, Quality Inspector (triggered on completion), ERP System (triggered on final completion)

### Preconditions
1. The operator is logged in at an HMI terminal assigned to the target work center.
2. A released work order exists in the operator's queue for that work center.
3. The operator has acknowledged all work instructions associated with the operation (UC-010 / BR-002).
4. No active quality holds are on the materials to be consumed.
5. The work center status is `AVAILABLE` (not in downtime or maintenance).

### Postconditions
1. Work order status is updated: `IN_PROGRESS` on start, `COMPLETED` on completion.
2. Actual start time and end time are recorded against the operation.
3. Actual quantity produced (yield and scrap) is recorded.
4. Material consumption is recorded against the BOM (UC-008).
5. If the operation is the last in the routing, the production order progresses to `PENDING QUALITY` or `COMPLETED` status.
6. OEE metrics are updated: runtime is attributed to the work center's availability and performance counters.
7. A quality inspection is automatically triggered if the operation has an associated inspection characteristic (BR-004 check).

### Main Success Scenario

**Phase 1 – Start Operation**
1. Operator arrives at work center, logs into HMI using badge scan or PIN.
2. HMI displays the operator's work queue showing pending work orders sorted by priority and planned start time.
3. Operator selects the work order, reviews order details: material, quantity, operation description, standard time, work instructions link.
4. Operator clicks **Start Operation**.
5. System records actual start time (UTC), transitions work order status to `IN_PROGRESS`, and begins accumulating machine runtime (from SCADA telemetry).
6. System starts a countdown timer on the HMI showing elapsed vs. standard time.
7. Operator executes the physical manufacturing operation.

**Phase 2 – Complete Operation**
8. Operator clicks **Complete Operation**.
9. System prompts for actual yield quantity and scrap quantity. Both fields are mandatory.
10. Operator enters quantities.
11. System validates: yield + scrap ≤ order quantity + allowed tolerance (BR-014).
12. System records completion timestamp, calculates actual cycle time.
13. System auto-calculates material consumption based on yield and BOM coefficients.
14. System prompts operator to confirm goods issue for consumed materials (or auto-confirms if configured per work center).
15. If operation is intermediate (not last in routing): status set to `COMPLETED`, next operation's work order becomes `READY` in the next work center's queue.
16. If operation is final: production order transitions to `PENDING QUALITY RELEASE` or `COMPLETED` (if no final inspection is defined).
17. System updates OEE dashboard with actual production data.

### Alternative Flows

**A1 – Partial completion (split lot)**
- At step 9, Operator enters a quantity less than the full order quantity.
- System sets work order to `PARTIAL` status, creates a continuation work order for the remaining quantity.
- Original work order is retained with its actual quantities for traceability.

**A2 – Scrap only**
- At step 9, Operator enters yield = 0, scrap = order quantity.
- System triggers automatic quality hold and notifies Quality Inspector and Production Supervisor.
- Work order marked `SCRAPPED`; ERP is notified to reverse the component reservation.

**A3 – Machine downtime during operation**
- Operator clicks **Report Downtime** (triggers UC-009).
- Work order status switches to `INTERRUPTED`; elapsed time accumulates in downtime bucket.
- When machine is restored, Operator resumes operation; downtime duration is recorded.

### Exception Flows

**E1 – SCADA connection lost during operation**
- System continues recording elapsed time using a local buffer.
- On SCADA reconnect, system reconciles buffered data. If gap > 5 minutes, system flags the operation for manual review.

**E2 – Quantity validation fails**
- System displays error: *"Yield + scrap ([n]) exceeds order quantity + tolerance ([m]). Verify entry."*
- Operator cannot complete until quantities are corrected.

**E3 – Mandatory quality inspection not completed**
- At step 16, if a mandatory final inspection has not been recorded, system blocks status transition to `COMPLETED` and displays: *"Final inspection for operation [Op#] has not been recorded. Contact Quality Inspector."*

### Business Rules Referenced
- **BR-002, BR-004, BR-014, BR-015**

### Non-Functional Requirements
- **Performance:** HMI response for Start/Complete button actions must be < **1 second** (critical for operator workflow continuity).
- **Offline resilience:** HMI must function in offline mode for up to **30 minutes** during network outages, buffering transactions locally and syncing on reconnection.
- **Security:** Operator ID is stamped on every transaction; shared login is prohibited. Session automatically locks after 5 minutes of inactivity.

### UI/UX Notes
- HMI designed for gloved-hand operation: large touch targets (minimum 44×44 px), high-contrast display.
- Current operation is prominently displayed with a traffic-light indicator (green = on time, amber = approaching standard time, red = overtime).
- Work instructions are accessible via a **View Instructions** button that opens a full-screen document viewer (PDF/HTML).

---

## UC-004: Record Quality Inspection

| Field | Value |
|---|---|
| **Use Case ID** | UC-004 |
| **Name** | Record Quality Inspection |
| **Version** | 1.3 |

### Actors
- **Primary:** Quality Inspector
- **Secondary:** MES System (SPC analysis), Production Supervisor (notified on fails)

### Preconditions
1. An operation has been completed and an inspection trigger has been generated by the MES (or a scheduled periodic inspection is due).
2. An inspection plan exists for the material/process/operation combination with defined characteristics, measurement methods, and specification limits.
3. The Quality Inspector is logged in with the `QA_INSPECTOR` role.
4. Measuring equipment is calibrated (calibration certificate is current — checked via equipment master).

### Postconditions
1. Inspection results are recorded against the inspection lot with individual measurement values per characteristic.
2. The inspection lot status is set to `PASSED`, `FAILED`, or `CONDITIONALLY RELEASED`.
3. SPC control charts are updated with the new measurement data points.
4. If the lot fails, a quality hold is automatically initiated on the affected material (UC-009 trigger).
5. Results are stored in the MES quality database and replicated to the LIMS system if configured.
6. If SPC detects an out-of-control condition, an automatic alert is sent to the Production Supervisor.

### Main Success Scenario
1. Inspector opens the **Quality Inspection** module; system displays the pending inspection queue sorted by urgency.
2. Inspector selects an inspection lot; system loads the inspection plan showing all characteristics to be measured: characteristic name, specification type (variable/attribute), unit of measure, lower spec limit (LSL), upper spec limit (USL), target value, measurement method, sample size.
3. For each characteristic, Inspector enters the measured value(s) using a form or by scanning data from a connected measurement device.
4. System immediately validates each entry against specification limits and displays an in/out indicator.
5. System runs SPC analysis: plots the value on the control chart and checks Western Electric rules for out-of-control patterns.
6. Inspector records observations and notes if required by the inspection plan.
7. After all mandatory characteristics are measured, the system evaluates overall lot disposition: `PASS` (all in spec), `FAIL` (any critical characteristic out of spec), `CONDITIONAL` (non-critical out of spec pending review).
8. Inspector confirms the results and submits the inspection record.
9. System updates the inspection lot and linked work order status.
10. System sends disposition notification to Production Supervisor.
11. For `FAIL` disposition: system automatically triggers a quality hold on the affected production lot (UC-009/UC-015 integration).

### Alternative Flows

**A1 – Re-inspection after initial failure**
- At step 7, if the lot is `FAIL` and the inspection plan permits re-inspection, Inspector may request a second sample.
- System creates a re-inspection lot linked to the original; increases sample size per AQL table.
- Re-inspection follows the same steps; only one re-inspection is allowed by default (BR-016).

**A2 – Skip non-critical characteristic**
- Inspector marks a non-critical characteristic as `SKIPPED` with a mandatory reason code.
- System logs the skip. Lot may still reach `PASS` status if all critical characteristics are within spec.

### Exception Flows

**E1 – Measurement device communication error**
- If the laboratory instrument interface fails, Inspector manually enters values.
- System flags the results as `MANUAL ENTRY` for audit purposes.

**E2 – Inspection plan not found**
- System displays warning: *"No active inspection plan found for material [X] at operation [Y]. Proceeding without inspection plan — use free-form entry."*
- Inspector must enter at least one measurement characteristic manually; a supervisor must co-sign the record.

### Business Rules Referenced
- **BR-004, BR-006, BR-008, BR-016**

### Non-Functional Requirements
- **Performance:** SPC chart update must render within **2 seconds** of submitting a measurement.
- **Data integrity:** Measurement values are immutable once submitted; corrections require a formal change record with reason and dual authorization.

### UI/UX Notes
- Measurement entry uses a tablet-optimized layout; numeric keypad overlay for variable measurements.
- Control charts are rendered as interactive SVG; Inspector can hover to see historical data points.
- Out-of-spec values are highlighted in red with the deviation amount shown.

---

## UC-005: Report Machine Downtime

| Field | Value |
|---|---|
| **Use Case ID** | UC-005 |
| **Name** | Report Machine Downtime |
| **Version** | 1.1 |

### Actors
- **Primary:** Machine Operator
- **Secondary:** Maintenance Technician (notified and responds), Production Supervisor (informed), MES System (OEE update)

### Preconditions
1. Operator is logged in at the relevant work center HMI.
2. The work center is active (has a running or assigned work order, or is in an available state).
3. The machine has stopped or a downtime condition has been identified.

### Postconditions
1. A downtime event record is created with start time, work center, operator, and downtime classification.
2. Work center status changes to `DOWNTIME`.
3. OEE availability loss is attributed to the downtime event.
4. The Maintenance Technician is notified if the downtime type requires maintenance intervention.
5. If downtime duration exceeds 30 minutes, a maintenance work order is automatically created (BR-010).
6. On machine restart, the downtime event is closed with actual duration recorded.

### Main Success Scenario
1. Machine stops. Operator clicks **Report Downtime** on the HMI.
2. System records the downtime start time and changes work center status to `DOWNTIME`.
3. System displays the downtime classification screen: Planned / Unplanned selection, downtime code picker (hierarchical: category → sub-category → specific code).
4. Operator selects the appropriate downtime code (e.g., `MECH > DRIVE > BELT_FAILURE`).
5. Operator optionally adds a free-text description.
6. System sends notification to the Maintenance Technician queue and to the Production Supervisor dashboard.
7. Maintenance Technician acknowledges the notification and proceeds to the work center.
8. Technician performs diagnosis and repair.
9. Operator (or Technician) clicks **Machine Ready** on the HMI.
10. System records the downtime end time; calculates actual downtime duration.
11. System updates OEE: availability loss = downtime duration / total planned production time.
12. System prompts: if downtime ≥ 30 minutes, automatically creates a Maintenance Work Order (UC-016).
13. Work order execution resumes from the interrupted state (A3 in UC-003).

### Alternative Flows

**A1 – SCADA-detected downtime (automatic)**
- SCADA detects machine stop signal (PLC fault code) and automatically creates a downtime event.
- Operator receives a pop-up on HMI: *"Downtime detected by SCADA. Please classify."*
- Operator classifies the code; steps 4–13 follow.

**A2 – Planned downtime (scheduled maintenance, changeover)**
- Operator selects `PLANNED` at step 3.
- System does not raise a maintenance alert; the event is attributed to `Planned Downtime` OEE category.
- Changeover times are tracked for SMED improvement analysis.

### Exception Flows

**E1 – Downtime classification not entered within 10 minutes**
- System sends escalation alert to Production Supervisor: *"Unclassified downtime at [WC] for >10 min."*
- Downtime event remains open; OEE loss continues to accumulate under `UNCLASSIFIED`.

### Business Rules Referenced
- **BR-005, BR-010, BR-017**

### Non-Functional Requirements
- **Response time:** Downtime start must be recorded within **500 ms** of button press to ensure accurate OEE data.
- **Reliability:** Downtime events must be persisted even during server outages (buffered locally at HMI).

---

## UC-006: Complete Production Run and ERP Confirmation

| Field | Value |
|---|---|
| **Use Case ID** | UC-006 |
| **Name** | Complete Production Run and ERP Confirmation |
| **Version** | 1.2 |

### Actors
- **Primary:** Production Supervisor
- **Secondary:** ERP System (SAP — receives confirmation), MES System

### Preconditions
1. All operations in the production order routing are in `COMPLETED` status.
2. All mandatory quality inspections have passed or conditional release has been granted (BR-004).
3. No open quality holds exist on any lot from the production order.
4. The Production Supervisor holds the `COMPLETE_ORDER` permission.

### Postconditions
1. Production order status transitions to `TECHNICALLY COMPLETE`.
2. ERP System receives a production order confirmation via the MES-ERP integration interface.
3. ERP posts a goods receipt for the finished product quantity.
4. ERP posts goods issues for all consumed components (actual vs. planned variance is visible).
5. Actual costs are transferred to the ERP cost collector for the production order.
6. MES production order is archived with all associated data (work orders, quality records, downtime events, material consumption).

### Main Success Scenario
1. Supervisor opens the Production Order and reviews the completion checklist: all operations complete, quality results passed, no open holds.
2. Supervisor clicks **Complete Order**.
3. System performs a final validation: checks all operations completed, all quality inspections resolved, no unclassified downtime events.
4. System calculates final production summary: actual yield vs. planned, scrap %, actual cycle time vs. standard, material consumption variance.
5. System displays the summary for Supervisor review.
6. Supervisor confirms completion.
7. System transitions production order to `TECHNICALLY COMPLETE`.
8. System constructs the ERP confirmation payload: order number, confirmed quantity, yield, scrap, actual activity times, component consumption with quantities.
9. System posts the confirmation to SAP ERP via RFC BAPI `CO_SE_BACKFLUSH_GOODSMOV` (or equivalent REST endpoint in newer SAP versions).
10. ERP acknowledges the posting; MES records the ERP document numbers (goods receipt document, goods issue document).
11. MES archives the production order record.
12. Supervisor receives confirmation notification with ERP document numbers.

### Alternative Flows

**A1 – ERP posting failure (temporary)**
- At step 9, if ERP returns a transient error, MES queues the confirmation for automatic retry (up to 3 retries at 5-minute intervals).
- If all retries fail, the integration admin and Supervisor are alerted; manual re-posting is available.

### Exception Flows

**E1 – Open quality inspection blocks completion**
- System displays: *"Production order cannot be completed. Open inspection lot [ID] must be resolved."*
- Supervisor is directed to the Quality module.

### Business Rules Referenced
- **BR-004, BR-007, BR-018**

---

## UC-007: ERP Material Reconciliation

| Field | Value |
|---|---|
| **Use Case ID** | UC-007 |
| **Name** | ERP Material Reconciliation |
| **Version** | 1.0 |

### Actors
- **Primary:** ERP System (SAP) — initiates and receives
- **Secondary:** Production Supervisor (reviews discrepancies), MES System

### Preconditions
1. At least one production order has been technically completed in MES within the reconciliation period.
2. The ERP-MES interface connection is operational.
3. MES material consumption records are locked (no further changes after order completion).

### Postconditions
1. ERP material documents are posted for all component goods issues.
2. Any consumption variances (actual vs. BOM standard) are visible in ERP variance reporting.
3. Reconciliation report is generated and available in MES for audit purposes.
4. Discrepancies > configured tolerance trigger a workflow notification to the Production Supervisor.

### Main Success Scenario
1. Scheduled reconciliation job executes (typically every 15 minutes or on-demand).
2. System retrieves all completed production orders since the last reconciliation run.
3. For each order: system compares MES actual component consumption quantities against ERP BOM standard quantities.
4. System calculates variance: `(Actual - Standard) / Standard × 100%`.
5. Variances within tolerance (configurable per material class, typically ±5%) are posted automatically.
6. Variances outside tolerance are flagged for supervisor review.
7. System constructs BAPI call with component consumption movements and posts to ERP.
8. ERP returns document numbers; MES stores the cross-reference.
9. Reconciliation report is generated and stored.

### Exception Flows

**E1 – ERP duplicate posting detected**
- ERP returns error code indicating a duplicate production order confirmation.
- MES logs the error, marks the order as `RECONCILIATION_ERROR`, and alerts the integration admin.
- No double-posting occurs; manual investigation required.

### Business Rules Referenced
- **BR-007, BR-018, BR-019**

---

## UC-008: Perform Shift Handover

| Field | Value |
|---|---|
| **Use Case ID** | UC-008 |
| **Name** | Perform Shift Handover |
| **Version** | 1.1 |

### Actors
- **Primary:** Production Supervisor (Outgoing), Production Supervisor (Incoming)
- **Secondary:** MES System (generates summary), Machine Operators (briefed by incoming supervisor)

### Preconditions
1. The current shift is within 30 minutes of its scheduled end time.
2. Both outgoing and incoming supervisors are logged in.
3. The MES shift configuration defines shift schedules and work center assignments.

### Postconditions
1. A shift handover record is created and co-signed by both supervisors.
2. The incoming shift is formally opened in MES; all subsequent transactions are attributed to the new shift.
3. Open work orders, quality holds, and downtime events are formally transferred to the incoming shift.
4. Machine operators receive a briefing notification on their HMI terminals.
5. OEE and production KPIs for the outgoing shift are locked and reported.

### Main Success Scenario
1. System automatically generates a shift handover summary 30 minutes before shift end.
2. Outgoing Supervisor reviews the auto-generated summary on the Shift Handover screen.
3. Summary includes: production order status (completed, in progress, pending), OEE for the shift, downtime events with classification, quality inspection results, open quality holds, material shortages, and pending work orders.
4. Outgoing Supervisor adds manual notes: issues encountered, priority items for incoming shift, safety observations.
5. Outgoing Supervisor clicks **Submit Handover Report**.
6. System sends a notification to the Incoming Supervisor's dashboard.
7. Incoming Supervisor logs in, opens the handover report, reviews all sections.
8. Incoming Supervisor adds acknowledgement notes and any additional context.
9. Both supervisors' digital signatures are recorded (timestamp + user ID).
10. System closes the outgoing shift: locks KPIs, transfers open orders to incoming shift context.
11. New shift begins; all subsequent operator transactions are tagged to the new shift.
12. Operators at all work centers receive a HMI notification: *"Shift [X] has started. Review any updated instructions."*

### Alternative Flows

**A1 – Remote handover (incoming supervisor not on site)**
- Incoming Supervisor completes the handover review and acknowledgement via mobile MES app.
- Dual signature requirement is still enforced; mobile signature is timestamped and geo-tagged.

### Exception Flows

**E1 – Incoming supervisor does not acknowledge within 15 minutes of shift start**
- System escalates to Plant Manager with alert: *"Shift handover acknowledgement overdue for [Shift]."*

### Business Rules Referenced
- **BR-009, BR-020**

### Non-Functional Requirements
- **Availability:** Shift handover must be available at shift-change times even during peak system load.
- **Data completeness:** The auto-generated summary must include 100% of open transactions — no manual data gathering required.

---

## UC-009: Manage Quality Hold

| Field | Value |
|---|---|
| **Use Case ID** | UC-009 |
| **Name** | Manage Quality Hold |
| **Version** | 1.2 |

### Actors
- **Primary:** Quality Inspector
- **Secondary:** Production Supervisor (approves disposition), ERP System (notified of held stock)

### Preconditions
1. A quality deficiency has been identified: inspection failure, operator-reported defect, or SPC out-of-control signal.
2. The affected production lot or material batch is identifiable by lot number or batch number.
3. Quality Inspector holds the `QA_HOLD` permission.

### Postconditions
1. The affected lot is placed on hold in MES with status `QUALITY HOLD`.
2. ERP is notified to block the corresponding stock batch from further movement.
3. A quality hold record is created documenting the reason, date/time, and responsible inspector.
4. The affected work centers are notified to stop processing material from the held lot.
5. A disposition decision (Release / Rework / Scrap) is recorded and formally approved.
6. ERP stock is unblocked or scrapped based on the final disposition.
7. A CAPA record is created if the hold is related to a systemic issue (BR-021).

### Main Success Scenario
1. Quality Inspector identifies a deficiency and navigates to **Quality → Initiate Hold**.
2. Inspector enters the lot/batch number(s) to be placed on hold (supports barcode scan input).
3. System retrieves lot details: material, quantity, production order, work center, current location.
4. Inspector selects hold reason from a controlled vocabulary (Critical Defect, Dimensional Non-conformance, Documentation Issue, etc.) and adds descriptive notes.
5. Inspector confirms; system immediately sets lot status to `QUALITY HOLD`.
6. System sends a block-stock message to ERP (SAP QM movement type 344 or REST equivalent).
7. System sends notifications to: Production Supervisor (dashboard alert), affected work center HMIs (pop-up warning), Maintenance if equipment-related.
8. Inspector creates or links a Non-Conformance Report (NCR).
9. Disposition review meeting is held (off-system); decision is recorded in MES.
10. Quality Inspector or Supervisor records the disposition decision: `RELEASE AS-IS`, `REWORK`, or `SCRAP`.
11. For `RELEASE`: Inspector records waiver justification and approving authority; ERP stock is unblocked.
12. For `REWORK`: A rework work order is created; material re-inspected after rework.
13. For `SCRAP`: Inspector confirms scrap quantity; ERP posts a scrap movement; MES marks lot as `SCRAPPED`.
14. Hold record is closed with all disposition details; CAPA record is linked.

### Alternative Flows

**A1 – System-initiated hold (SPC trigger)**
- SPC detects an out-of-control pattern and automatically initiates a hold on the last produced lot.
- Inspector receives a notification and must review and confirm or release the automatic hold within 2 hours.

### Exception Flows

**E1 – ERP block-stock message fails**
- System retries ERP notification 3 times. If all fail: critical alert to integration admin; hold remains in MES; manual ERP intervention required.
- Hold remains active in MES regardless of ERP communication status (safety-first principle).

**E2 – Lot partially consumed before hold is applied**
- System identifies any work orders that consumed material from the held lot.
- Inspector is presented with a list of affected downstream production for review.

### Business Rules Referenced
- **BR-006, BR-008, BR-016, BR-021**

### Non-Functional Requirements
- **Response time:** Hold status must be applied and propagated to all HMIs within **5 seconds** of Inspector confirmation (safety-critical).
- **Traceability:** Full audit trail from deficiency identification through final disposition must be maintained for a minimum of 10 years.

### UI/UX Notes
- Hold initiation uses a red-themed warning UI to emphasize the severity of the action.
- Lot search supports scanning of physical lot labels; confirmation dialog requires deliberate double-confirmation click.
- The disposition workflow uses a guided wizard with mandatory fields at each step.
