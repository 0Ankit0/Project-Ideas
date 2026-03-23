# Edge Cases - Operations

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Background jobs lag, delaying overdue notices or hold notifications | Patron communication becomes unreliable | Monitor queue depth, freshness, and retry rates |
| Branch loses connectivity during checkout | Staff cannot serve patrons | Provide degraded offline transaction buffering or documented fallback process |
| Search cluster outage occurs | Discovery slows or fails | Fallback to database-backed minimal search for staff-critical flows |
| Clock skew across services affects due dates and fines | Policy errors accumulate | Standardize time sources and centralize deadline calculations |
| Bulk import or reindex floods reporting systems | Operational instability | Use backpressure, staged rollouts, and observable reprocessing workflows |
