# Edge Cases - Backend as a Service Platform

This folder captures cross-cutting scenarios that can break abstraction stability, tenant isolation, provider portability, migration safety, security, or platform operations if they are not handled deliberately.

## Contents

- `provider-selection-and-provisioning.md`
- `auth-and-tenancy.md`
- `data-api-and-schema.md`
- `storage-and-file-providers.md`
- `functions-and-jobs.md`
- `realtime-and-messaging.md`
- `api-and-sdk.md`
- `security-and-compliance.md`
- `operations.md`

## How to Read These Edge Cases (Expanded)

Each edge-case document now captures six analysis lenses:
1. Explicit API contract details.
2. Tenant/project/environment isolation implications.
3. Lifecycle/state transition impact.
4. Error taxonomy and retry behavior.
5. SLI/SLO observability and alert implications.
6. Migration/versioning strategy when behavior changes.
