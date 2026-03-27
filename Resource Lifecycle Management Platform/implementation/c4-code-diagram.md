# C4 Code Diagram

The code-level view maps each domain service to packages/modules:
- API layer (commands/queries)
- Domain layer (aggregates, policies, invariants)
- Infrastructure layer (repositories, adapters, messaging)

Ownership boundaries align to Reservation, Fulfillment, Settlement, and Governance contexts.
