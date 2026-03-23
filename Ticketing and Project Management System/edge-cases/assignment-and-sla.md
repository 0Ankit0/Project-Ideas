# Edge Cases - Assignment and SLA

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| No engineer with the required skill is available | Ticket sits unowned | Allow queue ownership plus escalation to PM or engineering manager |
| Assigned developer goes on leave | SLA breach risk | Support reassignment with preserved ownership history and alerts |
| Client is waiting to provide details | Resolution timer becomes misleading | Support approved SLA pause states with explicit reason codes |
| Priority is set too low during triage | Critical issue misses response window | Require override approval for downgrading incidents after evidence review |
| One ticket blocks multiple milestones | Risk hidden in individual queues | Propagate blocker state to all linked milestones and portfolio reporting |
