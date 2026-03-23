# Edge Cases - API and UI

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Search index lags after course publication | Learners cannot find new content | Show publication freshness and reconcile critical catalog reads |
| Learner opens assessment in multiple windows | Attempt collisions occur | Lock active attempts or define deterministic continuation behavior |
| Large cohort dashboard becomes slow | Staff lose operational visibility | Use projection-based summaries and paginated drill-downs |
| Staff workspace leaks learner data across tenants | Severe isolation breach | Enforce tenant scoping before query and render on every route |
| Lesson player fails to render embedded content | Progress flow breaks | Provide graceful fallback with retry and support messaging |
