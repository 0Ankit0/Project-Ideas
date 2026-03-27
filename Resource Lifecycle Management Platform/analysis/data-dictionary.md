# Data Dictionary

| Entity | Purpose | Key Fields |
|---|---|---|
| Resource | Catalog item or assignable unit | `resource_id`, `type`, `status`, `tenant_id` |
| AvailabilityWindow | Time-bounded usable interval | `window_id`, `resource_id`, `start_at`, `end_at`, `buffer_rules` |
| Reservation | User commitment to consume resource | `reservation_id`, `state`, `policy_snapshot`, `hold_expires_at` |
| Fulfillment | Check-out/check-in execution record | `fulfillment_id`, `reservation_id`, `checkout_at`, `checkin_at` |
| Settlement | Financial close package | `settlement_id`, `charges_total`, `adjustments_total`, `recon_status` |
| IncidentClaim | Dispute or damage case | `claim_id`, `severity`, `evidence_refs`, `resolution_status` |
