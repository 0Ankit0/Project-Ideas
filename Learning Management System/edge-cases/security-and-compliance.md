# Edge Cases - Security and Compliance

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Instructor accesses a cohort outside authorized tenant scope | Cross-tenant data exposure | Enforce tenant and cohort scope checks in every service path |
| Grade override occurs without reason capture | Audit weakness and dispute risk | Require mandatory reason and immutable audit history |
| Certificate verification endpoint leaks learner data | Privacy violation | Expose only minimal public verification metadata |
| Downloadable course assets contain sensitive content | Unauthorized redistribution risk | Use signed URLs, scoped access, and watermarking where needed |
| Export includes more learner data than allowed by policy | Compliance issue | Apply role-scoped export templates and approval flows |
