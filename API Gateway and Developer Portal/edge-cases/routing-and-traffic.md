# Edge Cases: Routing and Traffic — API Gateway and Developer Portal

## Overview

This file documents ten edge cases covering the routing and traffic-management layer of the API Gateway. The gateway is implemented in **Node.js 20 + Fastify** running on **AWS ECS Fargate**, with upstream service discovery registered in **PostgreSQL 15** and health state cached in **Redis 7**. Load balancing across multiple upstream instances is performed internally by the gateway's Fastify plugin layer, not by an external load balancer between gateway and upstream.

The edge cases below represent scenarios where the routing path deviates from normal operation due to infrastructure failures, misconfiguration, adversarial input, or unexpected traffic patterns. Each case uses the standard five-section analysis template and is accompanied by a summary table at the end of the file.

**Scope**: These edge cases apply to the gateway's request-forwarding path only. Authentication, rate-limiting, and portal edge cases are documented in their respective files.

---

## EC-ROUTE-001 — All Upstream Instances Simultaneously Unhealthy

| Field | Detail |
|-------|--------|
| **Failure Mode** | All registered upstream instances for a given route fail their active health checks at roughly the same time. This can occur during a bad deployment that crashes all pods simultaneously, a downstream database failure that causes every upstream instance to start returning 500s, or an AWS AZ-level networking event affecting all instances in the same placement group. The gateway's health-check poller marks every instance as `UNHEALTHY` within its polling interval (default 10 seconds), and the circuit breaker trips to the `OPEN` state. No valid upstream exists to forward the request. |
| **Impact** | 100% of requests to the affected route receive a `503 Service Unavailable` response with a `Retry-After: 15` header. Clients that do not honour `Retry-After` will generate a retry storm, amplifying load on the gateway itself. Dependent downstream services that call this route will cascade into their own failure modes. Revenue and SLA impact begins immediately; for payment or authentication routes this is a P0 incident. |
| **Detection** | Prometheus gauge `upstream_healthy_instances{route="<route_id>"}` drops to `0`; a Grafana alert rule fires within 15 seconds. The circuit breaker state change is logged as a structured JSON event (`circuit_breaker_state_change: OPEN`) with route ID and timestamp, forwarded to CloudWatch Logs. A PagerDuty high-urgency incident is created automatically via the Alertmanager webhook. The gateway's own `/healthz` endpoint continues returning `200` (it reflects gateway process health, not upstream health), so ALB health checks do not remove gateway instances—this is intentional. |
| **Mitigation / Recovery** | The gateway returns `503` with `Retry-After: 15` and a JSON error body `{"error":"upstream_unavailable","route":"<route_id>","traceId":"<id>"}`. The circuit breaker enters a `HALF_OPEN` probe every 10 seconds: it sends a single test request to each known upstream instance. On first successful probe, the circuit breaker closes and normal traffic resumes. On-call engineer verifies upstream deployment logs, rolls back if a bad deployment is identified, or escalates to the upstream team. If the upstream cannot recover within 30 minutes, the fallback static error page (served from CloudFront + S3) is activated for affected public-facing routes. |
| **Prevention** | Enforce a rolling-deployment strategy on upstream services with a `maxUnavailable: 0` policy so at least one healthy instance always exists during deploys. Add minimum-healthy-instance guards in the gateway's route configuration schema (minimum `1` required before a route is considered `ACTIVE`). Require upstream services to implement a `/healthz` endpoint that reflects true readiness (including database connectivity) rather than just process liveness. Conduct chaos engineering drills quarterly to verify circuit breaker behaviour under full-upstream failure. |

---

## EC-ROUTE-002 — Infinite Routing Loop via X-Forwarded-For

| Field | Detail |
|-------|--------|
| **Failure Mode** | A misconfigured upstream service re-routes requests back to the API gateway, either through an incorrect reverse-proxy rule or a misconfigured service mesh entry. The gateway forwards the request to upstream, upstream forwards it back to the gateway's public ingress URL, the gateway matches the route again and forwards again, creating an infinite loop. Because the gateway adds its own IP to the `X-Forwarded-For` header on each hop, the header grows with each iteration, but without loop detection the goroutine/connection chain grows until resources are exhausted. |
| **Impact** | CPU and memory spike rapidly as each loop iteration allocates new connection state and header buffers. Without mitigation, the gateway exhausts its connection pool and begins refusing all incoming requests, causing a service-wide outage rather than isolating the faulty route. Looping requests never return a response to the original client, causing client-side timeouts (typically 30 seconds) and user-visible failures. |
| **Detection** | On every inbound request, the gateway Fastify middleware inspects the `X-Forwarded-For` header. If the header contains more than **10 distinct hops**, or if any hop matches the gateway's own known ECS task IP range (loaded from the ECS task metadata endpoint at startup), the loop is detected. A counter `routing_loop_detected_total` is incremented and the request is immediately terminated. An `alert: routing_loop_detected` structured log entry is emitted containing the full `X-Forwarded-For` chain, the source IP, and the matched route ID. Grafana alert fires if the counter exceeds `1` in any 5-minute window. |
| **Mitigation / Recovery** | The gateway terminates the request immediately and returns `508 Loop Detected` to the caller. The specific route responsible for generating the loop is identified from the structured log (route ID is included in the log). The route is temporarily suspended via the admin API (`PATCH /admin/routes/{id}` with `{"status":"suspended"}`), which updates the route record in PostgreSQL and invalidates the Redis route cache within 1 second across all gateway instances. The upstream team is notified to fix their reverse-proxy configuration before the route is re-enabled. |
| **Prevention** | Enforce a hard cap of **10 hops** in `X-Forwarded-For` at the gateway level as a Fastify plugin applied globally. Add gateway IP self-detection at startup using the ECS task metadata endpoint. Require integration tests for any route that involves a reverse-proxy configuration to include a loop-detection assertion. Include `X-Gateway-Version` as a custom header; if the gateway receives its own version header on an inbound request, it is a definitive loop signal. Document this constraint in the upstream integration guide. |

---

## EC-ROUTE-003 — Upstream Returns Malformed or Truncated Response Body

| Field | Detail |
|-------|--------|
| **Failure Mode** | An upstream service closes its TCP connection before completing the response body (network interruption, upstream crash mid-serialisation, or a buggy serialiser that emits invalid JSON). The gateway receives a partial response: the `Content-Length` header may indicate 8 KB but only 3 KB was transmitted before the connection dropped, or the upstream sent chunked transfer encoding and never sent the terminal `0\r\n\r\n` chunk. Fastify's undici HTTP client detects the premature close and raises a `UND_ERR_SOCKET` or `UND_ERR_DESTROYED` error. |
| **Impact** | The client receives a `502 Bad Gateway` response with a structured error body rather than the intended upstream data. If the client retries immediately without backoff, a retry storm compounds the upstream instability. For routes that return large streaming responses (e.g., log export, analytics CSV), partial data may have already been streamed to the client before the truncation is detected, leaving the client in an ambiguous state regarding data completeness. |
| **Detection** | The undici HTTP client error is caught in the Fastify route handler and mapped to a `502` response. An `upstream_response_error` structured log event is emitted with fields: `route_id`, `upstream_host`, `error_type` (`truncated_body` or `connection_reset`), and `trace_id`. The Prometheus counter `upstream_response_errors_total{error_type="truncated_body"}` is incremented. A Grafana alert fires when this counter's rate exceeds `0.5%` of total requests for a given route over a 5-minute window. Jaeger spans for affected requests are marked with `error=true` and `upstream.error=truncated_body`. |
| **Mitigation / Recovery** | The gateway discards all bytes received from the partial response and returns `{"error":"upstream_error","code":"RESPONSE_TRUNCATED","traceId":"<id>"}` to the client with status `502`. For streaming routes, the gateway sends an HTTP `500` trailer (for HTTP/2 streams) or closes the chunked connection with an error indicator. The on-call engineer reviews the Jaeger trace to identify the specific upstream host responsible and checks its deployment logs and memory/CPU metrics for the root cause. If the upstream error rate exceeds the circuit breaker threshold (5% error rate over 30 seconds), the circuit breaker opens automatically. |
| **Prevention** | Configure undici with strict `bodyTimeout` (30 seconds) and `headersTimeout` (10 seconds) to prevent hanging connections. Implement response body length validation for routes where `Content-Length` is provided: abort and log if bytes received differ from declared length. Apply contract testing (using Pact) between the gateway and upstream services to detect serialisation regressions before production deployment. Add upstream memory and CPU alarms to catch resource exhaustion before it manifests as truncated responses. |

---

## EC-ROUTE-004 — Slow Upstream Causes Connection Pool Exhaustion (Timeout Cascade)

| Field | Detail |
|-------|--------|
| **Failure Mode** | An upstream service begins responding slowly—P99 latency climbs from a normal 200 ms to 15–30 seconds due to a slow database query, GC pause, or memory pressure. Because each in-flight request holds one connection from the gateway's undici connection pool (default pool size: 100 connections per upstream host), the pool fills within seconds. New requests to the same upstream cannot acquire a connection and queue in memory. If the upstream hosts connections for multiple routes, all routes sharing that upstream are affected simultaneously, turning a single upstream slowdown into a full gateway degradation. |
| **Impact** | All traffic to routes backed by the slow upstream begins accumulating in the connection wait queue. Queue memory grows, gateway heap usage rises, and eventually requests begin timing out waiting for a pool slot rather than waiting for the upstream. Under severe conditions, the Node.js event loop stalls processing the backlog of timed-out requests, and the gateway's own response latency to all routes (including healthy ones) degrades. The ECS task may be marked unhealthy by ALB health checks and restarted, causing a brief additional outage. |
| **Detection** | Prometheus gauge `connection_pool_waiting{upstream="<host>"}` exceeding `80` (80% of pool capacity) triggers a `warning` alert. If it reaches `95`, a `critical` alert fires. Upstream response time histogram `upstream_response_duration_seconds{quantile="0.99"}` exceeding 10 seconds triggers a separate high-latency alert. Both alerts include the upstream host and route IDs to facilitate rapid diagnosis. Jaeger traces for slow requests show the upstream span duration clearly. |
| **Mitigation / Recovery** | Per-route undici connection pools are configured with a `pipelining: 0` (one request per connection) and a hard `requestTimeout: 30000` ms. When the timeout fires, the gateway returns `504 Gateway Timeout` to the client and releases the connection slot. The circuit breaker monitors error rate: if more than `10%` of requests to an upstream time out within any 20-second window, the circuit breaker trips open and the gateway stops sending new requests to that upstream for 30 seconds, allowing the upstream to recover. Load shedding (`429 Too Many Requests`) is applied to new requests that would exceed the queue depth limit of 50. |
| **Prevention** | Isolate connection pools per route rather than sharing a pool per upstream host; this prevents a single slow route from exhausting capacity for other routes on the same upstream. Set aggressive per-route timeouts proportional to that route's expected P95 latency (not a global 30-second default). Instrument upstream services with database query timeout limits. Conduct load tests with artificial upstream latency injection to verify circuit breaker trip thresholds. Review and right-size connection pool sizes quarterly based on traffic growth. |

---

## EC-ROUTE-005 — Sudden 10x Traffic Spike Within 60 Seconds

| Field | Detail |
|-------|--------|
| **Failure Mode** | A viral event (product launch, media mention, mass email campaign) or the onset of a volumetric DDoS attack drives request rate from a baseline of, say, 500 RPS to 5,000 RPS within 60 seconds. ECS Fargate auto-scaling has a minimum 2–3 minute response time to register the CloudWatch alarm, provision new tasks, and pass ALB health checks. During this window, existing gateway tasks are CPU-throttled by ECS, the Node.js event loop queue grows, and latency for all requests rises sharply. The WAF rate-based rules may not yet have activated if the per-IP rate is below their threshold (the attack is distributed). |
| **Impact** | CPU throttling causes event loop delays, pushing P99 latency from under 100 ms to several seconds. Memory pressure from queued requests may trigger Node.js GC thrashing. If the spike is sustained, ECS tasks may crash due to memory exhaustion. Clients that receive high latency may open additional connections, further compounding the load. Legitimate users experience slow or failed requests. Revenue impact is direct and begins within 30 seconds of the spike onset. |
| **Detection** | Prometheus `rate(http_requests_total[30s])` rising above `5x` the 24-hour rolling baseline triggers a `critical` spike alert. CloudWatch ECS CPU utilisation alarm (`> 80% for 60 seconds`) fires independently. AWS WAF rate-based rules activate at the edge when any single IP exceeds 2,000 requests per 5-minute window, dropping excess requests before they reach the gateway. Synthetic canary latency (checked every 30 seconds) rising above `2000 ms` triggers a Grafana alert. |
| **Mitigation / Recovery** | AWS CloudFront absorbs cacheable requests at the edge, reducing load reaching the gateway for GET routes with appropriate `Cache-Control` headers. The global rate limiter (Redis sliding-window counter) enforces a per-API-key and per-IP ceiling, issuing `429 Too Many Requests` with `Retry-After` to callers exceeding their limit. ECS auto-scaling triggers additional gateway tasks; pre-warmed task definitions minimise cold-start time to under 45 seconds. If the spike is confirmed as a DDoS, AWS Shield Advanced is engaged and WAF rules are tightened. Traffic is manually load-shed via the admin API to non-critical routes if resource utilisation exceeds `90%`. |
| **Prevention** | Establish a documented pre-scaling playbook that can be triggered manually 30 minutes before known high-traffic events (product launches, scheduled campaigns). Run quarterly load tests at `10x` normal peak to validate auto-scaling response time and circuit breaker behaviour. Enable CloudFront caching for all read-only routes with TTLs appropriate to data freshness requirements. Configure WAF rate-based rules as the first line of defence at the CDN edge. Tune ECS auto-scaling target tracking to CPU `60%` (not `80%`) to maintain headroom during spikes. |

---

## EC-ROUTE-006 — Route Config Update Causes Propagation Inconsistency Across Gateway Instances

| Field | Detail |
|-------|--------|
| **Failure Mode** | An operator updates a route definition (changes upstream host, modifies path pattern, or toggles a plugin) via the admin API. The update is written to PostgreSQL and an invalidation message is published to the Redis `config:routes` pub/sub channel. However, one or more ECS Fargate task instances miss the pub/sub notification (Redis pub/sub is fire-and-forget; if a subscriber is momentarily disconnected or processing a CPU-heavy request, the message is lost). Those instances continue serving the old route configuration for up to the config polling interval (default: 30 seconds), while other instances serve the new configuration. |
| **Impact** | During the propagation window (typically 10–30 seconds), requests are non-deterministically routed to either the old or new upstream depending on which gateway instance the ALB round-robins the request to. For route deletions, some instances return `404` while others still serve the route, creating confusing inconsistencies for API consumers. For upstream URL changes, some requests go to the old upstream (possibly returning different data or being unavailable), creating a split-brain data state. |
| **Detection** | Each gateway instance stamps its response with an `X-Config-Version` response header reflecting the config hash it used to serve the request. Synthetic monitors that send probe requests to all gateway instances and compare `X-Config-Version` values detect inconsistency within one probe cycle (30 seconds). An alert fires when two or more consecutive probes to the same route return different `X-Config-Version` values from different instances. Structured logs include `config_version` on every request for post-hoc analysis. |
| **Mitigation / Recovery** | If inconsistency is detected by the synthetic monitor, the admin API offers a `POST /admin/config/sync` endpoint that triggers an immediate config reload on all instances by publishing a high-priority `config:force-reload` pub/sub message with a monotonically increasing version counter. Instances that receive this message reload their route table from PostgreSQL synchronously before processing the next request. In the worst case, waiting for the 30-second polling interval to expire resolves the inconsistency automatically. |
| **Prevention** | Switch from fire-and-forget Redis pub/sub to a Redis Streams consumer group for config change notifications: each gateway instance maintains a consumer group offset, ensuring missed messages are replayed on reconnection. Implement a config version check on every request (comparing the instance's loaded version against the version in Redis): if diverged, trigger a background reload without blocking the request. Stamp all route config changes with a version counter in PostgreSQL so instances can detect staleness proactively. |

---

## EC-ROUTE-007 — Client Sends Oversized Request Body Exceeding 10 MB

| Field | Detail |
|-------|--------|
| **Failure Mode** | A client (malicious or misconfigured) sends a request with a body exceeding the gateway's configured 10 MB `bodyLimit`. This could be a large JSON payload, a file upload sent to the wrong endpoint, or a deliberate attempt to exhaust gateway memory by sending many concurrent oversized requests. Fastify's built-in `bodyLimit` option handles this, but the failure mode emerges if `Content-Length` is omitted (chunked transfer), forcing the gateway to buffer the body until the limit is reached before it can reject the request. |
| **Impact** | Each oversized request in flight consumes up to 10 MB of gateway heap memory during buffering. If a client sends 50 concurrent oversized requests, the gateway may face up to 500 MB of additional heap pressure, potentially triggering GC thrashing or OOM. The Node.js process may be killed by the ECS container memory limit, causing a task restart and a brief availability gap. Legitimate small requests are unaffected unless the OOM crash occurs. |
| **Detection** | Fastify emits a `PayloadTooLargeError` when the body limit is exceeded; this is mapped to a `413 Request Entity Too Large` response and counted in the Prometheus counter `http_errors_total{status="413"}`. A Grafana alert fires when the `413` rate from a single IP or API key exceeds `10 per minute`. The request source IP, API key (if present), and route are logged with the error. CloudWatch Container Insights memory metrics for the ECS task are monitored separately to detect memory pressure caused by concurrent oversized requests before OOM occurs. |
| **Mitigation / Recovery** | Fastify's `bodyLimit: 10485760` (10 MB in bytes) is set globally and cannot be overridden per route without explicit allow-listing. Requests exceeding the limit receive `413` with the response body `{"error":"payload_too_large","maxBytes":10485760}` before the body is fully buffered (Fastify checks `Content-Length` first if present). For chunked requests without `Content-Length`, Fastify streams the body and aborts when the limit is hit, releasing the buffer. The WAF additionally enforces a body size limit at the CloudFront edge (`8192 KB` AWS WAF body inspection limit) to reject most oversized requests before they reach the ECS layer. |
| **Prevention** | Document the 10 MB body size limit in the developer portal API reference and return the limit value in the `413` response. For routes legitimately requiring large uploads (e.g., document ingestion), provision a dedicated pre-signed S3 upload URL flow that bypasses the gateway body limit entirely—the client uploads directly to S3 and the gateway receives only the S3 object key. Set the AWS WAF `Body` inspection size to the maximum (8 KB for inspection; full 10 MB hard block) to catch oversized payloads at the edge. Add a rate-limit rule on `413` responses per IP to automatically block clients triggering repeated oversized requests. |

---

## EC-ROUTE-008 — Upstream SSL Certificate Expiry Causes TLS Handshake Failure

| Field | Detail |
|-------|--------|
| **Failure Mode** | An upstream service's TLS certificate reaches its expiry date without being renewed. When the gateway (undici HTTP client) attempts to open a new TLS connection to the upstream, the TLS handshake fails with a `CERT_HAS_EXPIRED` error. Existing keep-alive connections to the upstream are unaffected until they are recycled (typically within minutes due to idle timeout). Once all keep-alive connections to the expired-cert upstream are recycled, all new connections fail and the route goes fully dark. This can happen silently at 2 AM if certificate monitoring is absent. |
| **Impact** | All traffic to the affected upstream returns `502 Bad Gateway` from the moment TLS handshake failures dominate. For services without a secondary upstream or failover route, this is equivalent to EC-ROUTE-001 in impact: 100% of affected route traffic fails. The incident is particularly damaging if it occurs for a critical route (authentication, payment) and no on-call engineer is immediately available to renew the certificate. Recovery requires the upstream team to renew and deploy the certificate before traffic can be restored. |
| **Detection** | The undici TLS error (`ERR_TLS_CERT_EXPIRED`) is caught, logged as a structured event `upstream_tls_error{reason="cert_expired"}`, and counted in `upstream_tls_errors_total`. Separately, a certificate expiry monitoring job (Lambda function running nightly) queries each registered upstream's TLS certificate expiry date and fires CloudWatch alarms at **30 days**, **14 days**, **7 days**, and **1 day** before expiry. Each alarm notifies the upstream team's Slack channel and creates a Jira ticket. The 1-day alarm also pages on-call. |
| **Mitigation / Recovery** | On detection of TLS handshake failures for an upstream, the circuit breaker trips open within 20 seconds (5% error rate threshold). If a secondary upstream or a fallback route is registered in the route configuration, traffic is automatically shifted to the secondary. If no failover is configured, `502` is returned to clients with a `Retry-After: 300` header. The on-call engineer triggers the upstream team's certificate renewal runbook. If the upstream uses AWS ACM, ACM auto-renewal is re-enabled; if it uses Let's Encrypt, `certbot renew` is run manually. Route traffic is re-enabled once a probe to the upstream returns a valid TLS handshake. |
| **Prevention** | Require all upstream services registered in the gateway to use AWS Certificate Manager (ACM) with automatic renewal enabled. ACM certificates renew automatically 60 days before expiry with no manual intervention. For upstreams not using ACM, mandate integration with a certificate lifecycle tool (cert-manager for Kubernetes upstreams, certbot with auto-renewal cron for VMs). The nightly expiry monitor and the 30/14/7/1-day alarm ladder ensure no expiry goes undetected. Add certificate validation to the route registration API: reject routes pointing to upstreams with certificates expiring within 7 days unless a renewal exemption is approved. |

---

## EC-ROUTE-009 — Partial Network Partition Isolates One Gateway Instance from Upstream

| Field | Detail |
|-------|--------|
| **Failure Mode** | An AWS Availability Zone networking issue, a misconfigured security group rule, or a transient VPC routing anomaly causes one specific ECS Fargate task to lose connectivity to the upstream's VPC endpoint or private IP, while all other gateway tasks in other AZs continue to function normally. From the affected task's perspective, TCP connections to the upstream time out rather than being refused (no RST), so the failure manifests as extremely slow requests (waiting for connection timeout) rather than immediate errors. |
| **Impact** | Because the ALB uses round-robin across all healthy gateway tasks, approximately one-third of requests (for a 3-task deployment) are routed to the affected task and experience multi-second timeouts before receiving a `504`. Two-thirds of requests are routed to healthy tasks and respond normally. The mixed success/failure pattern is confusing for clients that retry: they may succeed on retry (hitting a healthy task) but the overall error rate rises. The affected task's `connection_pool_waiting` gauge climbs as connections queue waiting for timeouts. |
| **Detection** | Per-instance Prometheus metrics (scraped via the ECS Service Discovery integration) show `upstream_connection_timeout_total` spiking on a single task IP while remaining near zero on other tasks. A Grafana panel comparing per-instance upstream error rates detects the asymmetry. Separately, the ALB target group health check (`/healthz`) continues returning `200` from the affected task (process is healthy; only upstream connectivity is broken), so the ALB does not automatically remove it—this is the critical subtlety. A dedicated upstream connectivity probe (a lightweight background job on each gateway task that pings upstream every 5 seconds) detects the failure and marks the task as degraded, enabling the task to return `503` from its ALB health check. |
| **Mitigation / Recovery** | The upstream connectivity probe detects failure within 10 seconds. The task updates its ALB health check response from `/healthz` to return `503`, causing the ALB to deregister it within two consecutive failed health checks (default: 2 checks × 5-second interval = 10 seconds). The remaining two healthy tasks absorb the full traffic load. The on-call engineer investigates the VPC/security group configuration, verifies the AZ routing table, and restarts the affected ECS task (which typically gets a new ENI and recovers connectivity). The task is re-registered to the ALB target group after passing two consecutive health checks. |
| **Prevention** | Enable cross-zone load balancing on the ALB to distribute traffic more evenly and reduce the blast radius of single-AZ connectivity issues. Implement the upstream connectivity probe as a first-class Fastify plugin that runs on every gateway task and integrates with the `/healthz` response. Ensure security group rules are managed via Infrastructure as Code (Terraform) with drift detection enabled so manual rule changes are detected immediately. Run quarterly GameDay exercises simulating AZ-level connectivity loss to validate the probe-and-deregister flow. |

---

## EC-ROUTE-010 — Path Parameter Injection in Route Matching Causes Incorrect Upstream Routing

| Field | Detail |
|-------|--------|
| **Failure Mode** | A malicious client sends a request with a crafted path parameter containing path traversal sequences (e.g., `GET /api/v1/users/../../admin/secrets` or URL-encoded equivalents `%2F..%2F..%2Fadmin`). If the gateway's route-matching logic performs URL decoding before normalisation, or if the upstream routing is constructed via string concatenation of path parameters, the decoded path may match an unintended route—potentially an internal admin endpoint, a different tenant's resource, or a system-level path on the upstream host. Fastify's router performs this decode-before-match by default for path parameters bound with `:param` syntax. |
| **Impact** | In the worst case, the attacker successfully routes to an internal administrative endpoint that was not intended to be externally accessible, bypassing route-level access control. Even if the upstream rejects the request at its own auth layer, the routing mismatch may expose the internal URL structure of upstream services to the attacker (via error messages or response timing differences). This constitutes both a security vulnerability and an availability concern (incorrect routing wastes upstream capacity). |
| **Detection** | AWS WAF has a managed rule group (`AWSManagedRulesCommonRuleSet`) that detects path traversal patterns (`../`, `%2F..%2F`, `..%2F`, `%252F`) and blocks them at the CloudFront edge before the request reaches the gateway. Gateway-level middleware logs and counts `security_events_total{type="path_traversal_attempt"}`. A Grafana alert fires if this counter exceeds `5` in any 1-minute window from a single IP. The access log includes the raw (pre-normalisation) request path alongside the matched route ID for forensic comparison. |
| **Mitigation / Recovery** | The WAF blocks known path traversal patterns at the CDN edge, returning `403 Forbidden` before the request reaches the gateway. At the gateway layer, a Fastify `onRequest` hook normalises all path parameters by percent-decoding, then re-encoding any decoded characters that are not valid in a path segment (effectively neutralising `../` and `./` sequences). If the normalised path no longer matches any registered route, a `400 Bad Request` is returned with `{"error":"invalid_path","detail":"path_traversal_detected"}`. The source IP is flagged in the WAF for enhanced monitoring and blocked if the pattern repeats within 5 minutes. |
| **Prevention** | Declare all route path parameters with explicit regex constraints in Fastify's route definition (e.g., `:userId([0-9a-f]{8}-[0-9a-f]{4}-...)` for UUIDs) so the router rejects any parameter value that does not match the expected format before executing route handler logic. Enable the AWS WAF `AWSManagedRulesCommonRuleSet` and `AWSManagedRulesSQLiRuleSet` rule groups. Add an integration test suite that sends common path traversal payloads to every registered route and asserts `400` or `403` responses. Conduct semi-annual penetration testing with a focus on gateway routing and input validation. |

---

## Summary Table

| ID | Name | Severity | Detection Method | Recovery Time |
|----|------|----------|-----------------|---------------|
| EC-ROUTE-001 | All Upstream Instances Simultaneously Unhealthy | Critical | Prometheus `upstream_healthy_instances` = 0; PagerDuty alert | 15–30 minutes (circuit breaker + upstream restart) |
| EC-ROUTE-002 | Infinite Routing Loop via X-Forwarded-For | High | `X-Forwarded-For` hop count > 10; self-IP detection; structured log alert | < 1 minute (automatic route suspension) |
| EC-ROUTE-003 | Upstream Returns Malformed or Truncated Response | High | `upstream_response_errors_total` rate alert; Jaeger span error tag | 5–15 minutes (circuit breaker + upstream fix) |
| EC-ROUTE-004 | Slow Upstream Causes Connection Pool Exhaustion | Critical | `connection_pool_waiting` > 80%; P99 latency alert | 30–60 seconds (circuit breaker trips; auto-scale) |
| EC-ROUTE-005 | Sudden 10x Traffic Spike Within 60 Seconds | Critical | RPS rate alert > 5x baseline; CloudWatch CPU alarm; WAF rate rule | 2–4 minutes (auto-scale + rate limiting) |
| EC-ROUTE-006 | Route Config Propagation Inconsistency | Medium | `X-Config-Version` mismatch in synthetic monitor | < 30 seconds (force-reload admin API) |
| EC-ROUTE-007 | Client Sends Oversized Request Body (> 10 MB) | Medium | `http_errors_total{status="413"}` rate alert | Immediate (Fastify bodyLimit; WAF block) |
| EC-ROUTE-008 | Upstream SSL Certificate Expiry | High | `upstream_tls_errors_total`; nightly cert expiry monitor | 15–60 minutes (cert renewal + route re-enable) |
| EC-ROUTE-009 | Partial Network Partition Isolates One Gateway Instance | High | Per-instance upstream connectivity probe; asymmetric error rate | 20–30 seconds (ALB deregisters affected task) |
| EC-ROUTE-010 | Path Parameter Injection in Route Matching | High | WAF path traversal rule; `security_events_total` counter | Immediate (WAF block + gateway normalisation) |

---

## Appendix A: Fastify Gateway Configuration Reference

The following configuration values correspond directly to the mitigation and prevention measures described in the edge cases above. These values are managed in `src/config/gateway.ts` and overridden via environment variables injected into the ECS task definition at deploy time.

```typescript
// src/config/gateway.ts
export const gatewayConfig = {
  server: {
    // EC-ROUTE-007: reject bodies larger than 10 MB before buffering
    bodyLimit: 10_485_760,
    // EC-ROUTE-004: hard wall-clock timeout per outbound request
    requestTimeout: 30_000,
    keepAliveTimeout: 5_000,
    connectionTimeout: 3_000,
  },
  upstreamPool: {
    // EC-ROUTE-004: max concurrent connections per upstream host
    connections: 100,
    // one request per connection — prevents head-of-line blocking
    pipelining: 0,
    keepAliveMaxTimeout: 10_000,
    keepAliveTimeout: 5_000,
    // EC-ROUTE-003: abort if upstream body takes > 30 s to stream
    bodyTimeout: 30_000,
    // EC-ROUTE-003: abort if upstream headers take > 10 s to arrive
    headersTimeout: 10_000,
  },
  healthCheck: {
    // EC-ROUTE-001: how often to probe each upstream instance
    intervalMs: 5_000,
    // EC-ROUTE-001: consecutive failures before marking UNHEALTHY
    unhealthyThreshold: 2,
    // EC-ROUTE-001: consecutive successes before marking HEALTHY
    healthyThreshold: 1,
    // EC-ROUTE-009: connectivity probe interval per gateway task
    connectivityProbeIntervalMs: 5_000,
  },
  circuitBreaker: {
    // EC-ROUTE-001, EC-ROUTE-004: % error rate to trip the breaker
    errorThresholdPercentage: 5,
    // EC-ROUTE-001: how long before attempting a half-open probe
    resetTimeoutMs: 30_000,
    // minimum request volume before error rate is evaluated
    volumeThreshold: 10,
    // maximum in-flight requests allowed when pool is near full
    maxConcurrent: 100,
  },
  routing: {
    // EC-ROUTE-002: maximum hops tolerated in X-Forwarded-For
    maxXForwardedForHops: 10,
    // EC-ROUTE-006: how often gateway instances reload route config
    configPollIntervalMs: 30_000,
    // EC-ROUTE-004: max requests queued waiting for a pool slot
    poolQueueDepthLimit: 50,
  },
  waf: {
    // EC-ROUTE-005: per-IP rate limit (requests per 5-minute window)
    ipRateLimitWindow: 300,
    ipRateLimitMax: 2_000,
  },
};
```

---

## Appendix B: Circuit Breaker State Transitions

The gateway uses the `opossum` library for circuit breaker state management. The state machine below applies per upstream host. Instances are scoped per upstream to prevent a failing upstream from tripping the breaker for unrelated upstreams that share the same gateway process.

| State | Entered When | Exited When | Request Behaviour |
|-------|-------------|-------------|-------------------|
| **CLOSED** | Initial state; after successful HALF_OPEN probe | Error rate ≥ 5% over last 20 s with ≥ 10 requests | Forward request to upstream normally |
| **OPEN** | Error rate threshold breached | After `resetTimeoutMs` (30 s) elapses | Return `503 Service Unavailable` immediately; no upstream contact |
| **HALF_OPEN** | After OPEN reset timeout | One success → CLOSED; one failure → back to OPEN | Forward exactly one probe request; evaluate result |

When the breaker trips to OPEN, a `circuit_breaker_state_change{state="open", upstream="<host>", route="<id>"}` structured log event is emitted and the counter `circuit_breaker_open_total` is incremented. These events are forwarded to CloudWatch Logs and trigger a Grafana annotation on the affected route's traffic dashboard, making it easy to correlate circuit-breaker events with latency and error-rate changes.

---

## Appendix C: Prometheus Alert Rule Definitions

The following PromQL alert expressions correspond to the detection methods described in the edge cases. These rules are deployed via the Prometheus Operator `PrometheusRule` custom resource in the `monitoring` namespace.

```yaml
# k8s/monitoring/routing-alerts.yaml
groups:
  - name: gateway.routing
    interval: 15s
    rules:

      - alert: UpstreamAllInstancesUnhealthy
        expr: upstream_healthy_instances{job="api-gateway"} == 0
        for: 15s
        labels:
          severity: critical
        annotations:
          summary: "Route {{ $labels.route_id }} has zero healthy upstream instances"
          runbook: "https://runbooks.internal/ec-route-001"

      - alert: ConnectionPoolNearExhaustion
        expr: >
          connection_pool_waiting{job="api-gateway"}
          / connection_pool_size{job="api-gateway"} > 0.80
        for: 10s
        labels:
          severity: critical
        annotations:
          summary: "Pool for {{ $labels.upstream }} is {{ $value | humanizePercentage }} utilised"
          runbook: "https://runbooks.internal/ec-route-004"

      - alert: TrafficSpikeDetected
        expr: >
          rate(http_requests_total{job="api-gateway"}[30s])
          > 5 * avg_over_time(
              rate(http_requests_total{job="api-gateway"}[30s])[24h:5m]
            )
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "Request rate is {{ $value | humanize }}x the 24 h baseline"
          runbook: "https://runbooks.internal/ec-route-005"

      - alert: UpstreamTLSError
        expr: >
          rate(upstream_tls_errors_total{job="api-gateway"}[1m]) > 0
        for: 30s
        labels:
          severity: high
        annotations:
          summary: "TLS handshake errors on {{ $labels.upstream_host }}"
          runbook: "https://runbooks.internal/ec-route-008"

      - alert: RoutingLoopDetected
        expr: increase(routing_loop_detected_total{job="api-gateway"}[5m]) > 0
        labels:
          severity: high
        annotations:
          summary: "Routing loop on route {{ $labels.route_id }}"
          runbook: "https://runbooks.internal/ec-route-002"

      - alert: ConfigVersionInconsistency
        expr: count(count by (config_version)(gateway_config_version)) > 1
        for: 60s
        labels:
          severity: medium
        annotations:
          summary: "Gateway instances are running different config versions"
          runbook: "https://runbooks.internal/ec-route-006"
```

---

## Appendix D: Automated Test Coverage Matrix

Each edge case must have corresponding automated test coverage before it is considered fully mitigated. The table below maps each edge case to its test suite, type, and the CI/CD gate at which it runs.

| ID | Test File | Test Type | CI Gate | Environment |
|----|-----------|-----------|---------|-------------|
| EC-ROUTE-001 | `upstream-health.test.ts` | Integration | PR merge gate | Staging |
| EC-ROUTE-002 | `loop-detection.test.ts` | Unit + Integration | PR merge gate | Local + Staging |
| EC-ROUTE-003 | `malformed-response.test.ts` | Integration | PR merge gate | Staging |
| EC-ROUTE-004 | `pool-exhaustion.k6.js` | Load (k6) | Weekly scheduled | Staging |
| EC-ROUTE-005 | `traffic-spike.k6.js` | Load (k6) | Weekly scheduled | Staging |
| EC-ROUTE-006 | `config-propagation.test.ts` | Integration | PR merge gate | Staging |
| EC-ROUTE-007 | `body-limit.test.ts` | Unit + Integration | PR merge gate | Local + Staging |
| EC-ROUTE-008 | `tls-cert-expiry.test.ts` | Integration | PR merge gate | Staging |
| EC-ROUTE-009 | `network-partition.fis.json` | Chaos (AWS FIS) | Monthly scheduled | Staging |
| EC-ROUTE-010 | `path-injection.test.ts` | Security | PR merge gate | Local + Staging |

Load tests (`*.k6.js`) run in the staging environment using k6 with a dedicated VPC. Chaos tests use AWS Fault Injection Simulator (FIS) experiment templates stored in `infrastructure/fis/`. Security tests are also run as part of the nightly DAST scan using OWASP ZAP against the staging gateway.

---

## Appendix E: On-Call Incident Response Quick Reference

The following checklists are designed for on-call engineers responding to routing and traffic incidents. Each checklist corresponds to the most common paging scenarios.

**EC-ROUTE-001 — All Upstreams Unhealthy**

- [ ] Open Grafana → `API Gateway / Upstream Health` dashboard; confirm `upstream_healthy_instances == 0` for affected route
- [ ] Check ECS console for recent task stop events on the upstream service
- [ ] Review upstream CloudWatch log group for application errors in the last 15 minutes
- [ ] If a bad deployment caused the failure, trigger the upstream team's rollback runbook
- [ ] If recovery will exceed 30 minutes, activate the static fallback page via the admin API
- [ ] Update the PagerDuty incident timeline with findings at each step

**EC-ROUTE-004 — Connection Pool Exhaustion**

- [ ] Open Grafana → `API Gateway / Connection Pools` panel; identify the upstream host with the highest `connection_pool_waiting`
- [ ] Check `upstream_response_duration_seconds{quantile="0.99"}` for the identified upstream
- [ ] Verify the circuit breaker has tripped (`circuit_breaker_open_total` counter incremented in Jaeger)
- [ ] Inspect the upstream's RDS slow-query log for long-running queries causing the latency spike
- [ ] If the query cannot be fixed immediately, scale the upstream service horizontally to spread load
- [ ] Reduce `poolQueueDepthLimit` temporarily via admin API to prevent queue memory growth

**EC-ROUTE-005 — Traffic Spike**

- [ ] Check CloudFront access logs for referrer distribution to determine if spike is organic or adversarial
- [ ] Verify ECS auto-scaling has triggered additional gateway tasks (ECS console → service events)
- [ ] Check WAF `BlockedRequests` metric: if high, a DDoS mitigation is already in progress
- [ ] If spike is a DDoS, open an AWS Shield Advanced support case immediately
- [ ] Enable manual traffic shedding on non-critical routes via the admin API if CPU > 90%
- [ ] Post a status page update within 15 minutes of incident declaration

**EC-ROUTE-008 — TLS Certificate Expiry**

- [ ] Identify the affected upstream from `upstream_tls_errors_total{reason="cert_expired"}` labels
- [ ] Determine if the upstream uses ACM (check Route 53 / ECS task definition) or a manually managed cert
- [ ] For ACM: verify auto-renewal is enabled in the ACM console; trigger manual renewal if the auto-renewal failed
- [ ] For non-ACM: page the upstream team's cert rotation contact immediately
- [ ] If a secondary upstream is registered for the route, enable failover via the admin API
- [ ] Re-enable the primary route only after confirming a successful TLS handshake probe

---

## Appendix F: Cross-Category Edge Case Dependencies

Routing and traffic edge cases frequently interact with failures in other categories. The table below documents the most significant cross-category dependencies to assist engineers in correlating multi-system incidents.

| Routing EC | Related EC | Interaction |
|-----------|-----------|-------------|
| EC-ROUTE-001 | EC-OPS-001 | RDS failover can cause upstream instances to become unhealthy if they share the same RDS primary |
| EC-ROUTE-004 | EC-RATELIMIT-007 | Pool exhaustion and retry storms can compound into a full cascading failure within 60 seconds |
| EC-ROUTE-005 | EC-RATELIMIT-001 | During a severe traffic spike, the Redis cluster serving rate-limit counters may also become overloaded |
| EC-ROUTE-006 | EC-AUTH-006 | Config propagation lag and auth cache staleness can both occur during the same rolling deployment |
| EC-ROUTE-008 | EC-AUTH-007 | Upstream TLS cert expiry and mTLS CA cert revocation are monitored by the same certificate expiry Lambda |
| EC-ROUTE-009 | EC-OPS-002 | A partial network partition can resemble a task health failure; distinguish by checking the connectivity probe status vs. ECS task state |
| EC-ROUTE-010 | EC-SEC-002 | Path injection and SSRF share WAF rule coverage; a WAF misconfiguration (EC-SEC-001) disables both defences simultaneously |
