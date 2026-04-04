# Edge Cases — Delivery and Proof

## EC-DEL-001: Customer Unavailable at Delivery Location

**Scenario:** Delivery staff arrives but no one is available to receive the package.

**Trigger:** Customer is not home or unreachable.

**Expected Behaviour:**
- Staff selects failure reason: "Customer Unavailable"
- System logs attempt with timestamp and notes
- Customer notified via push + SMS with reschedule options
- After 3 attempts → order transitions to `ReturnedToWarehouse`
- Customer can contact support to arrange a specific delivery time

**Severity:** Medium

---

## EC-DEL-002: POD Upload Failure — Network Error

**Scenario:** Delivery staff captures POD (signature + photo) but upload to S3 fails due to poor connectivity.

**Trigger:** Staff is in an area with weak mobile data.

**Expected Behaviour:**
- Mobile app stores POD artifacts locally (encrypted on device)
- App retries upload every 30 seconds when connectivity resumes
- Order stays in `OutForDelivery` until POD is successfully uploaded
- If app is closed before upload, local queue persists across app restarts
- After 3 failed upload attempts → alert sent to operations
- Operations can manually trigger POD upload from staff's device later

**Severity:** High

---

## EC-DEL-003: Staff Reassignment Mid-Delivery

**Scenario:** Operations manager reassigns a delivery from Staff A to Staff B while Staff A is already en route.

**Trigger:** Staff A reports vehicle breakdown or becomes unavailable.

**Expected Behaviour:**
- Reassignment allowed only if status is `ReadyForDispatch` or `PickedUp`
- Staff A receives push notification: "Assignment reassigned — return package to warehouse if not yet delivered"
- Staff B receives new assignment with full delivery details
- If status is `OutForDelivery` → reassignment blocked; manager must contact Staff A directly
- Reassignment logged in audit trail with both staff identities

**Severity:** Medium

---

## EC-DEL-004: Delivery to Wrong Address

**Scenario:** Delivery staff delivers to the address on record, but the customer moved or provided incorrect address.

**Trigger:** Customer entered wrong address; didn't update before pickup.

**Expected Behaviour:**
- If recipient is different person and signs POD → delivery is considered successful; customer must contact support for redelivery
- If no one at the address → standard "Customer Unavailable" flow
- Customer can dispute delivery via support; admin reviews POD photo for verification
- If confirmed wrong address → return pickup scheduled; address correction required for redelivery

**Severity:** Medium

---

## EC-DEL-005: Maximum Delivery Capacity Exceeded

**Scenario:** More orders are ready for dispatch than available delivery staff can handle in a single day.

**Trigger:** High order volume or staff shortages.

**Expected Behaviour:**
- Assignment engine checks staff capacity (max 20 orders per run)
- Excess orders remain in `ReadyForDispatch` queue
- System extends estimated delivery window for queued orders
- Operations manager receives alert: "Delivery backlog: X orders awaiting assignment"
- Manager can temporarily increase per-staff capacity or request additional staff

**Severity:** High

---

## EC-DEL-006: Duplicate POD Submission

**Scenario:** Staff's app retries POD submission due to timeout, resulting in duplicate upload.

**Trigger:** Network latency causes client-side retry before server response.

**Expected Behaviour:**
- POD submission uses idempotency key (assignment_id + "pod")
- Duplicate upload returns cached first response
- S3 versioning prevents data loss but no duplicate records in database
- Order transitions to `Delivered` only once (state machine guard)

**Severity:** Medium
