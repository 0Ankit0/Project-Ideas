# Edge Cases — Social Networking Platform

## Overview

This directory documents edge cases, failure modes, and mitigation strategies for the Social
Networking Platform. Each file targets a specific domain and provides structured failure-mode
analysis, detailed scenarios, severity ratings, and concrete remediation steps. The goal is to
surface rare-but-impactful conditions before they reach production and to give on-call engineers
a reference for triage and recovery.

---

## Edge Case Categories

| File | Domain | Key Risk |
|------|--------|----------|
| `content-moderation.md` | Trust & Safety | AI false positives/negatives, CSAM handling, coordinated inauthentic behavior |
| `feed-ranking.md` | Relevance & ML | Ranking model failures, cold start, echo-chamber feedback loops |
| `notification-storms.md` | Messaging & Delivery | Fan-out storms, push delivery failures, notification floods |
| `account-compromise.md` | Identity & Auth | Credential stuffing, session hijacking, 2FA bypass, account takeover |
| `api-and-ui.md` | Platform Reliability | API abuse, query complexity attacks, UI race conditions |
| `security-and-compliance.md` | Privacy & Legal | GDPR deletion, CSAM reporting pipeline, cross-border data transfer |
| `operations.md` | Infrastructure | DB replication lag, cache stampede, Kafka consumer lag, media pipeline failures |

---

## Severity Levels

| Level | Label | Description | Example SLA |
|-------|-------|-------------|-------------|
| P0 | Critical | Platform-wide outage or active exploitation of a security vulnerability | 15-min page, 1-hr resolution target |
| P1 | High | Significant user-facing degradation or compliance breach risk | 30-min page, 4-hr resolution target |
| P2 | Medium | Partial feature failure affecting a subset of users | Next business day, 24-hr resolution |
| P3 | Low | Minor anomalies with no direct user impact | Backlog, resolved in sprint |

---

## Common Mitigation Patterns

### Circuit Breakers
Services wrap downstream calls with circuit breakers. When error rates exceed a threshold the
circuit opens, requests fail fast, and a fallback (cached response, degraded mode) is served.
This prevents cascading failures across the call graph.

### Idempotent Operations
All write operations — posts, reactions, follows — carry a client-generated idempotency key.
The server deduplicates within a 24-hour window so retries do not produce duplicate records.

### Rate Limiting and Throttling
A multi-layer rate-limiting stack (per-IP, per-user, per-app-token) is enforced at the API
gateway. Limits are tiered by account age and trust score to allow legitimate power users while
blocking abuse.

### Graceful Degradation
Non-critical features (recommendations, trending topics, suggested friends) degrade silently
when their backing services are unavailable. Core features (post creation, messaging) must
remain functional even during partial outages.

### Observability-First Design
Every failure mode in this directory has a corresponding metric, alert, and runbook entry.
Detection latency is treated as a first-class engineering concern alongside MTTR.

### Human-in-the-Loop Escalation
Automated systems handle the majority of moderation, fraud detection, and abuse prevention.
When confidence falls below a configurable threshold, items are routed to a human review queue
with strict SLA targets and escalation paths.

---

## Using These Documents

- **Pre-launch reviews**: Walk through relevant edge-case files during design reviews to surface
  gaps before code is written.
- **Incident triage**: Use the Detection and Recovery columns as a quick-reference checklist
  during active incidents.
- **Runbook cross-references**: Each detailed scenario should link to the corresponding runbook
  or playbook entry in the ops wiki.
- **Postmortems**: After every P0/P1 incident, update the relevant edge-case file with new
  failure modes discovered during the postmortem process.

---

## Maintenance

These files are living documents. They must be reviewed:
- During every major feature launch that touches the relevant domain.
- Quarterly, as part of the risk-review process.
- Immediately following any P0 or P1 incident.

File ownership is tracked in `CODEOWNERS`. The on-call rotation is responsible for keeping
detection and mitigation steps current.
