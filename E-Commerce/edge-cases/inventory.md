# Edge Cases - Inventory

### 3.1. Inventory Drift
* **Scenario**: Inventory counts differ between warehouse and system.
* **Impact**: Overselling or lost sales.
* **Solution**:
    * **Reconciliation**: Scheduled stock audits and adjustments.
    * **Buffers**: Safety stock thresholds to reduce oversell.

### 3.2. Negative Stock
* **Scenario**: Stock drops below zero due to race conditions.
* **Impact**: Invalid inventory state.
* **Solution**:
    * **Constraints**: Enforce non-negative stock at DB level.
    * **Transactions**: Atomic updates with locking.

### 3.3. Vendor-Managed Inventory Delays
* **Scenario**: Vendor inventory updates arrive late.
* **Impact**: Outdated availability shown to customers.
* **Solution**:
    * **SLA**: Enforce vendor update SLAs.
    * **UX**: Show “availability subject to confirmation.”