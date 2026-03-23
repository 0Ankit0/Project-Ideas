# Edge Cases - Acquisitions and Inventory

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Vendor ships fewer items than ordered | Receiving mismatch | Record discrepancy and partial receipt states |
| Received items are damaged | Copy availability and financial records diverge | Capture damaged-on-receipt workflow and supplier follow-up |
| Inter-branch transfer never arrives | Inventory appears lost | Use dispatch, in-transit, received, and exception states with alerts |
| Shelf audit finds ghost items in system | Trust in inventory drops | Support discrepancy reconciliation with manager approval |
| Repair workflow lasts longer than expected | Holds and availability become misleading | Keep repair status visible and exclude from circulation eligibility |
