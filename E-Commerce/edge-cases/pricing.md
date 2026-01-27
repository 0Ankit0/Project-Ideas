# Edge Cases - Pricing & Promotions

### 6.1. Stacked Discounts
* **Scenario**: Multiple promotions apply unexpectedly.
* **Impact**: Margin loss.
* **Solution**:
    * **Rules**: Enforce promotion stacking rules.
    * **Validation**: Reject invalid combinations at checkout.

### 6.2. Currency Mismatch
* **Scenario**: User’s currency differs from catalog pricing.
* **Impact**: Incorrect totals and confusion.
* **Solution**:
    * **Conversion**: Use real-time FX rates with rounding rules.
    * **UI**: Show base and converted prices.

### 6.3. Tax Calculation Errors
* **Scenario**: Taxes are calculated incorrectly for a region.
* **Impact**: Compliance issues and refunds.
* **Solution**:
    * **Validation**: Use tax provider with region updates.
    * **Monitoring**: Alert on anomalous tax totals.