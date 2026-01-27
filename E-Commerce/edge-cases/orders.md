# Edge Cases - Orders

### 1.1. Concurrent Checkout on Low Stock
* **Scenario**: Multiple customers checkout the last unit at the same time.
* **Impact**: Overselling and backorders.
* **Solution**:
    * **Validation**: Atomic inventory reservation at checkout.
    * **UI**: Show “only X left” and clear out-of-stock messages.

### 1.2. Price Changes During Checkout
* **Scenario**: A price update occurs after items are in cart.
* **Impact**: Mismatched totals and customer disputes.
* **Solution**:
    * **Policy**: Lock price for a short TTL once checkout starts.
    * **UI**: Prompt user if price changes beyond the TTL.

### 1.3. Duplicate Order Submission
* **Scenario**: User double-clicks “Place Order” or retries due to timeout.
* **Impact**: Duplicate orders and charges.
* **Solution**:
    * **Idempotency**: Require an idempotency key on order creation.
    * **UI**: Disable submit button and show progress state.