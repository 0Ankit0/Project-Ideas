# Operations Edge Cases

## Incident Playbook by Scenario

| Scenario | Detect | Contain | Recover | Verify |
|---|---|---|---|---|
| Carrier outage | shipping retry spikes + circuit open | pause release on impacted carriers | reroute or queued retry | no pending aged shipments |
| Queue backlog | lag > SLO threshold | scale workers + throttle wave release | drain queue with priority policy | lag returns to normal |
| Reconciliation drift | ledger/balance mismatch alert | freeze adjustments for affected scope | replay + compensating ledger entries | invariants green |

## Operational Command Chain
1. Incident commander assigned automatically by domain ownership.
2. Communications update every 15 minutes for Sev-1/2 incidents.
3. Recovery completion requires explicit data-consistency verification query.

## Post-Incident Requirements
- Create corrective action with owner and due date.
- Add/adjust synthetic alert to detect earlier.
- Link incident to business rule if policy gap discovered.
