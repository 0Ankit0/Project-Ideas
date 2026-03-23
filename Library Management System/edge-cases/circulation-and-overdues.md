# Edge Cases - Circulation and Overdues

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Patron attempts checkout while account is just over fine threshold | Desk workflow ambiguity | Show hard block with override policy and reason capture |
| Item marked returned but physically missing | Inventory and patron history diverge | Use claimed-returned and search workflows before closing discrepancy |
| Holiday calendar changes after loan issued | Due dates and overdue logic shift | Version policies and preserve original calculated due dates unless explicit recalculation is allowed |
| Same item scanned twice during checkout or return | Duplicate transactions | Make circulation commands idempotent and display latest authoritative state |
| Lost item later reappears | Financial status and catalog state conflict | Allow reversal workflow with audit trail and conditional fee adjustments |
