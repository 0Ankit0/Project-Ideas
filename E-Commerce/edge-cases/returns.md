# Edge Cases - Returns & Refunds

### 5.1. Return Window Expired
* **Scenario**: Customer requests a return after the allowed period.
* **Impact**: Disputes and support load.
* **Solution**:
    * **Validation**: Enforce return window with clear policy display.
    * **Exceptions**: Allow admin override with audit log.

### 5.2. Partial Refund on Bundle
* **Scenario**: A bundle item is returned partially.
* **Impact**: Incorrect refund calculation.
* **Solution**:
    * **Rules**: Define refund allocation per bundle item.
    * **UI**: Show itemized refund breakdown.

### 5.3. Refund Failure
* **Scenario**: Payment provider refund fails.
* **Impact**: Customer dissatisfaction and financial risk.
* **Solution**:
    * **Retry**: Automated refund retries.
    * **Fallback**: Issue store credit with customer approval.