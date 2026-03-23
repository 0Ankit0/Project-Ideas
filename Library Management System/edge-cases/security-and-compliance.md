# Edge Cases - Security and Compliance

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Patron reading history exposed to unauthorized staff | Major privacy violation | Limit access by role and mask history unless operationally justified |
| Waivers or fee adjustments performed without traceability | Audit failure | Require reason capture and immutable audit logging |
| Shared staff credentials used at branch desks | Accountability loss | Enforce individual logins, session timeout, and privileged-action attribution |
| Export contains personally identifiable patron data beyond purpose | Privacy and compliance risk | Use scoped exports, data minimization, and approval workflows |
| API keys for digital or payment providers leak | Third-party account compromise | Rotate secrets and isolate integration credentials by environment |
