# Edge Cases - Operations

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Queue backlog delays malware scan or notifications | Intake appears broken | Expose queue depth metrics and auto-scale workers |
| Database failover occurs during milestone update | Partial writes or retries | Use transactional boundaries and idempotent commands |
| Object storage outage blocks screenshot retrieval | Investigation slows | Cache critical metadata and surface degraded-mode messaging |
| Notification provider outage hides SLA escalations | Teams miss response targets | Retry through secondary channels and alert ops immediately |
| Clock skew breaks SLA timers | False breach signals | Standardize on NTP-synced infrastructure and server-side deadline calculations |
