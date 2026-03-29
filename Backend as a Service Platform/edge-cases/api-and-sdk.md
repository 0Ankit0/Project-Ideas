# Edge Cases - API and SDK

| Scenario | Risk | Mitigation |
|----------|------|------------|
| SDK version expects newer facade semantics than deployed platform | Client breakage | Version APIs and ship SDK compatibility matrices |
| Provider exposes feature not represented in facade | Pressure for contract leakage | Add optional capability flags rather than raw provider passthrough by default |
| Pagination or filtering semantics vary underneath | Inconsistent client behavior | Canonicalize pagination and filtering at facade layer |
| Long-running provisioning call retried by client | Duplicate resources | Use idempotency tokens on provisioning APIs |
| Error formats differ per adapter | Hard-to-handle client responses | Map adapter failures into stable platform error taxonomy |

## Deep Edge Cases: API and SDK

### Contract-focused scenarios
| Scenario | Expected API behavior |
|---|---|
| SDK ahead of platform minor | server returns compatibility warning metadata |
| Missing idempotency key on mutation | `VAL_IDEMPOTENCY_REQUIRED` |
| Deprecated field used post-sunset | `VAL_FIELD_DEPRECATED` + migration hint |

### Versioning strategy
- SDKs embed supported API major/minor list.
- Platform publishes compatibility endpoint for startup checks.
