# Edge Cases - API & UI

### 7.1. Checkout Session Expired
* **Scenario**: User attempts to pay after checkout session expires.
* **Impact**: Payment failures and abandoned carts.
* **Solution**:
    * **Auth**: Extend session or refresh with cart validation.
    * **UI**: Prompt user to re-confirm checkout.

### 7.2. Pagination Drift
* **Scenario**: Items change between pages due to updates.
* **Impact**: Duplicate or missing products.
* **Solution**:
    * **Pagination**: Cursor-based pagination with stable sort.
    * **Consistency**: Snapshot search results when needed.

### 7.3. Stale Product Details
* **Scenario**: User sees outdated stock or price in UI cache.
* **Impact**: Mismatched expectations and failed checkout.
* **Solution**:
    * **Caching**: Short TTL and cache invalidation on updates.
    * **UI**: Re-validate price and stock at checkout.