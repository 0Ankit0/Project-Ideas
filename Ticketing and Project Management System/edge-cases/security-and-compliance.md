# Edge Cases - Security and Compliance

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Client organization user accesses another client's ticket | Severe tenant isolation breach | Enforce organization scoping in every query path and add audit alarms |
| Sensitive data appears in screenshots | Privacy exposure | Add user guidance, optional redaction workflow, and strict attachment permissions |
| Audit log tampering is attempted | Compliance evidence lost | Use append-only audit storage and privileged access monitoring |
| Retention policy deletes attachments needed for dispute review | Operational and legal risk | Support legal hold and policy exceptions |
| Admin exports too much data | Data minimization failure | Require scoped exports, approvals, and export audit trails |
