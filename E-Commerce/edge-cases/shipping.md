# Edge Cases - Shipping & Delivery

### 4.1. Address Validation Failure
* **Scenario**: Customer enters an invalid or incomplete address.
* **Impact**: Failed deliveries and extra costs.
* **Solution**:
    * **Validation**: Use address verification APIs at checkout.
    * **UI**: Suggest corrections and confirm before order placement.

### 4.2. Lost in Transit
* **Scenario**: Shipment is lost or stalled with carrier.
* **Impact**: Customer dissatisfaction and refunds.
* **Solution**:
    * **Monitoring**: Trigger exceptions on tracking inactivity.
    * **Process**: Replacement or refund workflows.

### 4.3. Partial Delivery
* **Scenario**: Multi-item order ships in multiple packages.
* **Impact**: Confusion and early returns.
* **Solution**:
    * **Tracking**: Provide per-package tracking and ETA.
    * **UI**: Show partial shipment status clearly.