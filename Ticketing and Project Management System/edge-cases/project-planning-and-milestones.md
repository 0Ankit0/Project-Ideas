# Edge Cases - Project Planning and Milestones

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Milestone date changes after client communication | Trust and reporting drift | Keep baseline date immutable and expose forecast delta |
| Ticket is linked to the wrong project | Wrong team and metrics | Require project-scope validation and tracked relinking history |
| A milestone is marked complete while linked P1 tickets remain open | False delivery signal | Enforce completion guardrails tied to open blockers and acceptance results |
| Shared dependency slips across several projects | Portfolio view becomes inaccurate | Model milestone dependencies explicitly and compute cascading risk |
| Backlog items grow without milestone ownership | Scope becomes unmanaged | Force backlog aging review and PM assignment thresholds |
