# Edge Cases - API and UI

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Search index is stale after recent returns | Patron sees incorrect availability | Display freshness indicators and reconcile from authoritative store when needed |
| Staff and patron edit account preferences concurrently | Lost updates | Use optimistic concurrency and explicit conflict messaging |
| Very large hold queues slow item-detail pages | UX degradation | Cache queue summaries and paginate administrative detail views |
| Staff workspace leaks patron borrowing history across branches | Privacy breach | Enforce branch and role scopes before query and render |
| Barcode scanner sends malformed input bursts | Desk workflow breaks | Normalize input and validate scan patterns before transaction execution |
