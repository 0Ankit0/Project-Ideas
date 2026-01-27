# Edge Cases - API & UI

### 5.1. Booking UI Shows Stale Availability
* **Scenario**: UI cache shows a slot as available after it was booked.
* **Impact**: Failed booking attempts.
* **Solution**:
    * **Cache**: Short TTL and invalidate on booking events.
    * **UI**: Re-check availability at confirmation step.

### 5.2. Session Expired Mid-Checkout
* **Scenario**: User session expires during checkout.
* **Impact**: Abandoned bookings and failed payments.
* **Solution**:
    * **Auth**: Refresh tokens and autosave progress.
    * **UI**: Prompt re-auth without losing context.