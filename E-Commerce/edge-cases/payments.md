# Edge Cases - Payments

### 2.1. Payment Authorized but Not Captured
* **Scenario**: Authorization succeeds but capture fails or times out.
* **Impact**: Order stuck in pending state.
* **Solution**:
    * **Retry**: Automated capture retries within authorization window.
    * **Fallback**: Cancel and release inventory after TTL.

### 2.2. Duplicate Charges
* **Scenario**: Payment gateway retry charges the customer twice.
* **Impact**: Refunds and trust issues.
* **Solution**:
    * **Idempotency**: Use gateway idempotency keys.
    * **Reconciliation**: Daily charge reconciliation and auto-refunds.

### 2.3. Chargeback/Dispute
* **Scenario**: Customer files a chargeback.
* **Impact**: Financial loss and admin workload.
* **Solution**:
    * **Evidence**: Store delivery proof and order details.
    * **Workflow**: Automated dispute handling with SLAs.