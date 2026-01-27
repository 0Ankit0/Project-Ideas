# Edge Cases - Booking & Payments

### 2.1. Double Booking Due to Race Conditions
* **Scenario**: Two users try to book the same slot simultaneously.
* **Impact**: Duplicate confirmations and disputes.
* **Solution**:
    * **Locking**: Use atomic reservation with short TTL.
    * **Idempotency**: Enforce idempotency keys on booking creation.

### 2.2. Payment Authorized but Booking Not Confirmed
* **Scenario**: Payment succeeds but booking confirmation fails.
* **Impact**: Customer charged without a booking.
* **Solution**:
    * **Transactions**: Use outbox pattern for booking/payment consistency.
    * **Recovery**: Auto-refund if confirmation fails.

### 2.3. Price Changes After Reservation
* **Scenario**: Provider updates price after slot is reserved.
* **Impact**: Mismatched totals.
* **Solution**:
    * **Policy**: Lock price for reservation TTL.
    * **UI**: Prompt user if price changes after TTL.