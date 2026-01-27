# Edge Cases - Cancellations & Refunds

### 3.1. Late Cancellation
* **Scenario**: User cancels within the penalty window.
* **Impact**: Revenue loss and policy disputes.
* **Solution**:
    * **Validation**: Enforce cancellation cutoffs.
    * **UI**: Show penalty amount before confirmation.

### 3.2. No-Show Dispute
* **Scenario**: User disputes a no-show charge.
* **Impact**: Support load and chargebacks.
* **Solution**:
    * **Evidence**: Capture check-in logs and timestamps.
    * **Workflow**: Dispute resolution process with audit trail.

### 3.3. Refund Failure
* **Scenario**: Refund fails at the payment provider.
* **Impact**: Customer dissatisfaction.
* **Solution**:
    * **Retry**: Automated retry with backoff.
    * **Fallback**: Issue credits with customer approval.