# Edge Cases — API Gateway and Developer Portal

## Overview

This directory catalogues every known and anticipated edge case for the **API Gateway and Developer Portal** system. An edge case, in this context, is any scenario that falls outside the happy-path execution of the system and that—if unhandled—would result in degraded availability, incorrect behaviour, a security vulnerability, or a violation of an SLA.

Each edge case is assigned a unique identifier, a severity rating, and a structured five-section analysis covering the failure mode, its business and technical impact, how it is detected, how it is mitigated or recovered from, and how it is prevented from recurring. The goal is to make the system's failure surface fully explicit so that on-call engineers, architects, and security reviewers share a common vocabulary and a concrete playbook.

The tech stack under analysis is:

- **Gateway**: Node.js 20 + Fastify running on AWS ECS Fargate
- **Developer Portal**: Next.js 14 + TypeScript
- **Data stores**: PostgreSQL 15 (RDS) + Redis 7 (ElastiCache)
- **Queue**: BullMQ (backed by Redis)
- **Auth**: API Key HMAC-SHA256 + OAuth 2.0 + JWT
- **Infrastructure**: AWS ECS Fargate, RDS, ElastiCache, CloudFront, Route 53, WAF, S3
- **Observability**: OpenTelemetry, Prometheus, Grafana, Jaeger

---

## Table of Contents

1. [Edge Case ID Registry](#edge-case-id-registry)
2. [Severity Classification](#severity-classification)
3. [Detection Taxonomy](#detection-taxonomy)
4. [Resolution SLA](#resolution-sla)
5. [Edge Case Review Process](#edge-case-review-process)
6. **Edge Case Files**
   - [routing-and-traffic.md](./routing-and-traffic.md) — EC-ROUTE-001 through EC-ROUTE-010
   - [authentication-and-keys.md](./authentication-and-keys.md) — EC-AUTH-001 through EC-AUTH-008
   - [rate-limiting-and-quotas.md](./rate-limiting-and-quotas.md) — EC-RATELIMIT-001 through EC-RATELIMIT-008
   - [developer-portal.md](./developer-portal.md) — EC-PORTAL-001 through EC-PORTAL-006
   - [security-and-compliance.md](./security-and-compliance.md) — EC-SEC-001 through EC-SEC-008
   - [operations.md](./operations.md) — EC-OPS-001 through EC-OPS-008

---

## Edge Case ID Registry

All 48 documented edge cases across all six files are listed below. IDs are stable — they must never be reassigned, even if the edge case is superseded or resolved. Resolved cases are marked in their respective files but remain in this registry for historical traceability.

| ID | Name | Severity | Category | File |
|----|------|----------|----------|------|
| EC-ROUTE-001 | All Upstream Instances Simultaneously Unhealthy | Critical | Routing & Traffic | routing-and-traffic.md |
| EC-ROUTE-002 | Infinite Routing Loop via X-Forwarded-For | High | Routing & Traffic | routing-and-traffic.md |
| EC-ROUTE-003 | Upstream Returns Malformed or Truncated Response | High | Routing & Traffic | routing-and-traffic.md |
| EC-ROUTE-004 | Slow Upstream Causes Connection Pool Exhaustion | Critical | Routing & Traffic | routing-and-traffic.md |
| EC-ROUTE-005 | Sudden 10x Traffic Spike Within 60 Seconds | Critical | Routing & Traffic | routing-and-traffic.md |
| EC-ROUTE-006 | Route Config Update Causes Propagation Inconsistency | Medium | Routing & Traffic | routing-and-traffic.md |
| EC-ROUTE-007 | Client Sends Oversized Request Body (>10 MB) | Medium | Routing & Traffic | routing-and-traffic.md |
| EC-ROUTE-008 | Upstream SSL Certificate Expiry Breaks TLS Handshake | High | Routing & Traffic | routing-and-traffic.md |
| EC-ROUTE-009 | Partial Network Partition Isolates One Gateway Instance | High | Routing & Traffic | routing-and-traffic.md |
| EC-ROUTE-010 | Path Parameter Injection in Route Matching | High | Routing & Traffic | routing-and-traffic.md |
| EC-AUTH-001 | Redis Unavailable During HMAC Key Validation | High | Authentication & Keys | authentication-and-keys.md |
| EC-AUTH-002 | API Key Brute-Force Enumeration Attack | Critical | Authentication & Keys | authentication-and-keys.md |
| EC-AUTH-003 | JWT with Future iat Claim Due to Clock Skew | Medium | Authentication & Keys | authentication-and-keys.md |
| EC-AUTH-004 | OAuth Authorization Code Reuse Attempt | High | Authentication & Keys | authentication-and-keys.md |
| EC-AUTH-005 | API Key Accidentally Committed to Public Repository | Critical | Authentication & Keys | authentication-and-keys.md |
| EC-AUTH-006 | Revoked API Key Still Cached in Redis | High | Authentication & Keys | authentication-and-keys.md |
| EC-AUTH-007 | mTLS Client Certificate with Revoked CA | High | Authentication & Keys | authentication-and-keys.md |
| EC-AUTH-008 | OAuth Refresh Token Has Expired | Medium | Authentication & Keys | authentication-and-keys.md |
| EC-RATELIMIT-001 | Redis Failure Causes Rate Limit Bypass | Critical | Rate Limiting & Quotas | rate-limiting-and-quotas.md |
| EC-RATELIMIT-002 | Distributed Counter Drift Across Gateway Instances | High | Rate Limiting & Quotas | rate-limiting-and-quotas.md |
| EC-RATELIMIT-003 | Quota Reset Race Condition at Window Boundary | Medium | Rate Limiting & Quotas | rate-limiting-and-quotas.md |
| EC-RATELIMIT-004 | Negative Quota Balance After Concurrent Burst Requests | High | Rate Limiting & Quotas | rate-limiting-and-quotas.md |
| EC-RATELIMIT-005 | Tenant Quota Exhausted Mid-Batch-Job | Medium | Rate Limiting & Quotas | rate-limiting-and-quotas.md |
| EC-RATELIMIT-006 | Shared-IP Clients Falsely Throttled (NAT Gateway) | Medium | Rate Limiting & Quotas | rate-limiting-and-quotas.md |
| EC-RATELIMIT-007 | Burst Allowance Consumed by Retry Storm | High | Rate Limiting & Quotas | rate-limiting-and-quotas.md |
| EC-RATELIMIT-008 | Rate Limit Headers Returning Incorrect Remaining Count | Low | Rate Limiting & Quotas | rate-limiting-and-quotas.md |
| EC-PORTAL-001 | Portal Build Deploys with Broken API Base URL | High | Developer Portal | developer-portal.md |
| EC-PORTAL-002 | API Key Display Race Condition on First Create | High | Developer Portal | developer-portal.md |
| EC-PORTAL-003 | Developer Account Email Verification Link Expired | Low | Developer Portal | developer-portal.md |
| EC-PORTAL-004 | Interactive API Console Leaks Auth Token in Browser History | High | Developer Portal | developer-portal.md |
| EC-PORTAL-005 | Documentation Out of Sync with Gateway Schema | Medium | Developer Portal | developer-portal.md |
| EC-PORTAL-006 | Portal SSR Crashes Under High Concurrency | High | Developer Portal | developer-portal.md |
| EC-SEC-001 | WAF Rule Misconfiguration Blocks Legitimate Traffic | High | Security & Compliance | security-and-compliance.md |
| EC-SEC-002 | SSRF via Upstream URL Parameter in Proxy Route | Critical | Security & Compliance | security-and-compliance.md |
| EC-SEC-003 | Log Injection via Malformed Request Headers | Medium | Security & Compliance | security-and-compliance.md |
| EC-SEC-004 | TLS 1.0/1.1 Negotiated Due to Misconfigured Policy | High | Security & Compliance | security-and-compliance.md |
| EC-SEC-005 | CORS Wildcard Misconfiguration Exposes Credentials | Critical | Security & Compliance | security-and-compliance.md |
| EC-SEC-006 | Sensitive Data Exposed in OpenTelemetry Span Attributes | High | Security & Compliance | security-and-compliance.md |
| EC-SEC-007 | Dependency with Known CVE Deployed to Production | High | Security & Compliance | security-and-compliance.md |
| EC-SEC-008 | Audit Log Tampering or Gap During Incident | Critical | Security & Compliance | security-and-compliance.md |
| EC-OPS-001 | RDS Failover Causes Sustained Write Unavailability | Critical | Operations | operations.md |
| EC-OPS-002 | ECS Task Stops Mid-Request During Deployment | High | Operations | operations.md |
| EC-OPS-003 | Prometheus Scrape Target Goes Stale | Medium | Operations | operations.md |
| EC-OPS-004 | S3 Bucket Policy Change Breaks Asset Delivery | High | Operations | operations.md |
| EC-OPS-005 | BullMQ Worker Crashes Leaving Jobs in Active State | High | Operations | operations.md |
| EC-OPS-006 | CloudFront Cache Serves Stale API Response | Medium | Operations | operations.md |
| EC-OPS-007 | ElastiCache Eviction Under Memory Pressure | High | Operations | operations.md |
| EC-OPS-008 | Jaeger Collector Drops Spans Under Trace Volume Spike | Medium | Operations | operations.md |

---

## Severity Classification

| Severity | Definition | Example |
|----------|------------|---------|
| **Critical** | System-wide or customer-facing data loss, full service outage, or active security breach. Requires immediate escalation and 24/7 on-call response. Business impact is severe and time-sensitive. | All upstream instances unhealthy; active API key brute-force attack; SSRF exploitation. |
| **High** | Significant degradation of a core feature for a subset of users, or a security vulnerability that is not yet actively exploited but has a clear exploitation path. Requires resolution within the current business day. | Redis unavailable during auth; partial network partition; revoked key still cached. |
| **Medium** | Non-critical feature degraded, minor data inconsistency, or a security hardening gap with no direct exploitation path. Requires resolution within the current sprint. | JWT clock skew beyond tolerance; route config propagation lag; log injection vector. |
| **Low** | Cosmetic issues, minor UX friction, or informational security observations with negligible real-world impact. Scheduled for the next available sprint. | Rate limit headers returning incorrect remaining count; developer email verification link expired. |

---

## Detection Taxonomy

Each category of edge case is surfaced through a combination of metrics, structured logs, distributed traces, and synthetic monitoring. The table below describes the primary detection channel per category.

| Category | Primary Detection Channel | Key Metrics / Signals | Tooling |
|----------|--------------------------|----------------------|---------|
| Routing & Traffic | Prometheus alert rules on upstream health and error rate | `upstream_healthy_instances`, `http_requests_total{status=~"5.."}`, `connection_pool_waiting` | Prometheus + Grafana |
| Authentication & Keys | Structured JSON logs parsed for auth error codes; metric counters | `auth_failures_total`, `cache_miss_total`, `jwt_validation_errors_total` | OpenTelemetry + Loki/CloudWatch |
| Rate Limiting & Quotas | Redis counter anomalies; 429 error rate spikes | `rate_limit_exceeded_total`, `quota_remaining_gauge`, Redis keyspace notifications | Prometheus + Grafana |
| Developer Portal | Synthetic end-to-end tests; Next.js error boundary logs | Portal health check endpoint; SSR error rate; Sentry error events | Grafana + Sentry |
| Security & Compliance | WAF rule matches; audit log gaps; CVE scanner | AWS WAF metric `BlockedRequests`; `security_events_total`; Trivy CVE report | AWS Security Hub + WAF |
| Operations | CloudWatch alarms; ECS service health; Jaeger trace gaps | `ecs_task_stopped_total`, `rds_failover_events`, `bullmq_stalled_jobs_total` | CloudWatch + Jaeger + PagerDuty |

---

## Resolution SLA

| Severity | Time to Acknowledge | Time to Mitigate | Time to Full Resolution | Escalation Path |
|----------|-------------------|-----------------|------------------------|-----------------|
| Critical | 5 minutes | 30 minutes | 4 hours | On-call engineer → Engineering Lead → CTO |
| High | 15 minutes | 2 hours | 1 business day | On-call engineer → Engineering Lead |
| Medium | 1 business day | 3 business days | Current sprint | Assigned engineer → Tech Lead review |
| Low | 1 sprint | Next sprint | Backlog grooming priority | Assigned engineer |

All SLAs are measured from the time the alert fires or the edge case is first reported. Breaches are tracked in the incident post-mortem system and reviewed in the monthly reliability review.

---

## Edge Case Review Process

Edge cases in this registry are living documents. The following process governs how they are created, updated, and retired.

**Creation**: Any engineer, security researcher, or QA analyst may propose a new edge case by opening a pull request that adds the structured five-section template to the appropriate file and adds a row to the registry table above. The PR must include evidence (a test, a production incident reference, a threat model finding, or a security audit report).

**Review**: All new edge cases require review by at least one senior engineer from the gateway team and, for security-categorised cases, one member of the security team. The reviewer verifies that the detection method is actionable, the mitigation is technically correct, and the severity classification is appropriate.

**Update**: When a system change alters the failure mode, detection, or mitigation for an existing edge case, the corresponding file must be updated in the same PR as the code change. This ensures the edge case documentation never drifts from the implementation.

**Retirement**: An edge case may be marked `[RESOLVED]` in its file when the prevention measure has been fully implemented and verified by at least two production release cycles. The ID is never deleted from this registry.

**Quarterly Review**: The entire registry is reviewed quarterly by the engineering leads to ensure severity classifications remain accurate, SLA targets are being met, and no new edge cases have been discovered but not yet documented.

**Tooling**: Each edge case ID is also tracked in the issue tracker with the label `edge-case`. The issue contains a link to this registry and the relevant file so that implementation tasks can be traced back to the documented analysis.

**Coverage Gap Detection**: During quarterly reviews, the registry is compared against the most recent threat model and the most recent penetration test report. Any finding in those documents that does not map to an existing edge case ID must be documented as a new edge case within one sprint of the review.
