# Edge Cases - Provider Selection and Provisioning

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| User selects provider combination with incompatible capability assumptions | Project setup fails later at runtime | Validate compatibility profiles during binding creation |
| Certified adapter version is deprecated after many projects adopt it | Operational risk spreads | Support adapter deprecation states and phased replacement workflows |
| Required provider secret is missing or malformed | Binding activation fails | Keep bindings in pending-validation state with explicit readiness diagnostics |
| Provider available in one region but not another | Environment portability breaks | Model regional compatibility as part of provider catalog metadata |
| Owner changes provider without migration planning | Facade breaks or data loss risk rises | Require switchover plan generation before production cutover |

## Deep Edge Cases: Provider Selection and Provisioning

| Scenario | Contract concern | Migration/versioning response |
|---|---|---|
| provider lacks optional feature | contract parity | expose capability flag, not contract break |
| adapter version mismatch | runtime incompatibility | block bind with `VAL_ADAPTER_INCOMPATIBLE` |
| region unsupported | residency breach risk | preflight deny with remediation choices |

Lifecycle note: provisioning can transition `validating -> failed` without reaching `active`.
