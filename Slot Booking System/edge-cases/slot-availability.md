# Edge Cases - Slot Availability

### 1.1. Overlapping Slots
* **Scenario**: Provider creates overlapping time slots for the same resource.
* **Impact**: Double booking or confusing availability.
* **Solution**:
    * **Validation**: Enforce non-overlapping slot constraints at DB and API.
    * **UI**: Highlight conflicting time ranges.

### 1.2. Timezone Mismatch
* **Scenario**: Provider and customer are in different time zones.
* **Impact**: Bookings occur at unintended times.
* **Solution**:
    * **Normalization**: Store times in UTC and display in user locale.
    * **UI**: Show timezone labels clearly.

### 1.3. Provider Blocks Slots After Booking
* **Scenario**: Provider blocks a slot that is already booked.
* **Impact**: Service disruption and refunds.
* **Solution**:
    * **Rules**: Disallow blocking booked slots without override.
    * **Workflow**: Require reschedule or cancellation flow.