# Edge Cases - Digital Lending and Access

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Digital provider reports fewer licenses than local system expects | Access denial or oversubscription | Reconcile provider entitlements regularly and prefer provider truth |
| Patron account expires during active digital loan | Access-control ambiguity | Define whether active access continues until expiry or is revoked immediately |
| Provider outage blocks content delivery | Patron sees broken experience | Surface degraded-mode messaging and retry or fallback guidance |
| Same title exists in physical and digital forms | Hold and availability UX becomes confusing | Distinguish fulfillment format clearly in discovery and account views |
| License expires while hold queue exists | Patron dissatisfaction | Notify affected patrons and cancel or re-route demand based on policy |
