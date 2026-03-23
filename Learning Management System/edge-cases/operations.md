# Edge Cases - Operations

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Progress event queue lags during peak learning hours | Dashboards and completion logic go stale | Monitor queue freshness and autoscale worker pools |
| Search or analytics cluster outage occurs | Reporting and discovery degrade | Fallback to core transactional reads for critical flows |
| Certificate issuance worker retries repeatedly | Duplicate certificates or confusion | Use idempotent issuance keys and issuance-state guards |
| Media CDN outage affects lessons | Learner experience collapses | Provide degraded mode messaging and retry policies |
| Tenant bulk import floods downstream systems | Operational instability | Stage imports with backpressure and observable job control |
