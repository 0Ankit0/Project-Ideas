# Edge Cases - Reservations and Waitlists

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Patron places hold on a title with many branch-specific copies | Queue fairness becomes unclear | Separate title-level request logic from fulfillment-copy selection |
| Returned item should satisfy a hold at another branch | Delays and misrouting | Auto-create transfer workflow with chain-of-custody states |
| Patron misses pickup window | Queue stalls | Auto-expire hold and advance next eligible request |
| Patron becomes blocked after hold placement but before pickup | Hold fairness conflict | Revalidate eligibility at fulfillment time and pause or skip appropriately |
| High-demand title receives hundreds of holds | Performance and transparency issues | Provide queue-position visibility with bounded recalculation cost |
