# Edge Cases - Change Management and Replanning

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Client raises a new issue during release freeze | Delivery decision becomes ambiguous | Route through a hotfix vs backlog decision workflow |
| Closed ticket is reopened after milestone sign-off | Completion metrics become stale | Reopen linked verification status and milestone health automatically |
| Scope increase is accepted informally in comments | Baseline changes are not auditable | Require a formal change-request record for committed milestone changes |
| Multiple PMs edit the same milestone plan concurrently | Data races and communication gaps | Use optimistic locking and visible change history |
| Replanning removes tasks still in active development | Orphaned work and confusion | Force task migration or cancellation decisions before save |
