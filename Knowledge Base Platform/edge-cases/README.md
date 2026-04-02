# Knowledge Base Platform — Edge Cases Catalog

## Overview

This catalog documents known and anticipated edge cases for the Knowledge Base Platform, a production-grade SaaS system built on Node.js 20 + NestJS, Next.js 14 with TipTap, PostgreSQL 15, Redis 7, Elasticsearch 8 (Amazon OpenSearch Service), pgvector, OpenAI GPT-4o, LangChain.js, BullMQ, AWS S3, CloudFront, ECS Fargate, RDS PostgreSQL, and ElastiCache Redis.

Each edge case is catalogued with a structured five-section format covering failure modes, impact, detection, mitigation, and prevention. This catalog is intended for use by engineering, SRE, product, and security teams.

---

## Why Edge Cases Matter for a Knowledge Base Platform

A knowledge base platform occupies a uniquely sensitive position in the software ecosystem. It serves as the authoritative source of truth for internal documentation, customer-facing help content, and AI-assisted knowledge retrieval. Failures in this system cascade in ways that are disproportionate to the underlying technical fault:

- **Trust erosion**: When a knowledge base returns wrong, stale, or inaccessible content, users stop trusting it and seek information through less reliable channels (Slack, email, verbal communication).
- **Compliance risk**: Article histories, authorship metadata, and AI-generated outputs are subject to GDPR, CCPA, and internal governance policies. Handling failures incorrectly can create legal liability.
- **AI amplification of errors**: The integration of GPT-4o and vector-based retrieval means that a single corrupted article or index inconsistency can silently pollute answers delivered to hundreds of users.
- **Multi-tenancy blast radius**: A single permission bug or tenant isolation failure can expose confidential content from one workspace to another, constituting a data breach.
- **Operational dependencies**: The platform depends on six external services (OpenAI, AWS S3, CloudFront, RDS, ElastiCache, OpenSearch). Any one of them failing can trigger cascading failures across seemingly unrelated features.

Documenting edge cases systematically ensures that incidents are resolved faster, post-mortems drive lasting fixes, and new engineers can understand the system's known failure modes before they encounter them in production.

---

## Edge Case Files

| ID Prefix    | File Name                    | Domain                                               |
|--------------|------------------------------|------------------------------------------------------|
| EC-AUTHOR    | content-authoring.md         | TipTap editor, version history, attachments, S3      |
| EC-SEARCH    | search-and-retrieval.md      | Elasticsearch, pgvector, Redis cache, query security |
| EC-AI        | ai-assistant.md              | OpenAI GPT-4o, LangChain, RAG, embeddings, BullMQ   |
| EC-ACCESS    | access-and-permissions.md    | RBAC, SSO, JWT, guest links, tenant isolation        |
| EC-SEC       | security-and-compliance.md   | XSS, injection, GDPR, CCPA, supply chain, audit logs |
| EC-OPS       | operations.md                | RDS, BullMQ, ECS, CloudFront, S3, ElastiCache        |

---

## Edge Case Severity Matrix

The matrix below plots each edge case domain by **Likelihood** (how often it is expected to occur in production) vs **Impact** (the severity of the outcome when it does occur).

```
                        IMPACT
                 Low         High
               +------------+------------+
  High         |            |            |
  Likelihood   | EC-SEARCH  | EC-OPS     |
               | EC-AUTHOR  | EC-ACCESS  |
               +------------+------------+
  Low          |            |            |
  Likelihood   | (minor UX  | EC-AI      |
               |  glitches) | EC-SEC     |
               +------------+------------+
```

**Quadrant Guidance:**

- **High Likelihood / High Impact (EC-OPS, EC-ACCESS):** Invest in automated detection, runbooks, and circuit breakers. These should be in on-call rotation.
- **High Likelihood / Low Impact (EC-SEARCH, EC-AUTHOR):** Automate recovery where possible. Monitor with dashboards; no immediate pager required unless SLO breached.
- **Low Likelihood / High Impact (EC-AI, EC-SEC):** Invest heavily in prevention and testing. Incidents here create regulatory and reputational consequences.
- **Low Likelihood / Low Impact:** Accept residual risk; document and re-evaluate quarterly.

---

## How to Use This Catalog

### Triage Process

1. **Identify the edge case ID** from logs, alerts, or incident description (e.g., "Search results missing after publish" → EC-SEARCH-001).
2. **Open the relevant file** in this directory and locate the matching edge case section.
3. **Execute the Detection checklist** first — confirm you are actually seeing this failure mode and not a similar one.
4. **Apply Mitigation/Recovery steps** in order. Do not skip steps even if the issue appears minor.
5. **Assign a severity** using the Impact section's rating (Critical / High / Medium / Low).

### Escalation Path

| Severity | Response Time | Escalation             |
|----------|---------------|------------------------|
| Critical | 15 minutes    | Page on-call engineer + Engineering Lead + VP Engineering |
| High     | 1 hour        | Page on-call engineer + Team Lead                         |
| Medium   | 4 hours       | Slack alert to #incidents channel                         |
| Low      | Next business day | Create ticket in backlog                             |

### Post-Incident Process

1. Complete all **Mitigation/Recovery** steps and confirm system is stable.
2. Create a post-mortem document within 48 hours of Critical/High incidents.
3. Add any new failure modes discovered to this catalog within 1 sprint.
4. Review the **Prevention** section and file tickets for any measures not yet implemented.
5. Update this README's severity matrix if the incident changes your likelihood/impact assessment.

---

## Monitoring Dashboards and Runbooks

| Resource                        | Location / URL                                      |
|---------------------------------|-----------------------------------------------------|
| Application Performance (APM)   | `https://monitoring.internal/apm/kb-platform`       |
| RDS / Database Metrics          | `https://monitoring.internal/rds/kb-prod`           |
| OpenSearch Cluster Health       | `https://monitoring.internal/opensearch/kb-prod`    |
| BullMQ Queue Depth              | `https://monitoring.internal/bullmq/kb-prod`        |
| ECS Service Health              | `https://monitoring.internal/ecs/kb-api`            |
| CloudFront Cache Hit Ratio      | `https://monitoring.internal/cloudfront/kb-cdn`     |
| OpenAI API Usage & Costs        | `https://platform.openai.com/usage`                 |
| Error Tracking (Sentry)         | `https://sentry.internal/projects/kb-platform`      |
| Runbook: Database Failover      | `https://runbooks.internal/kb/db-failover`          |
| Runbook: OpenSearch Recovery    | `https://runbooks.internal/kb/opensearch-recovery`  |
| Runbook: Redis Failover         | `https://runbooks.internal/kb/redis-failover`       |
| Runbook: ECS Task OOM Recovery  | `https://runbooks.internal/kb/ecs-oom`              |
| Runbook: AI API Outage          | `https://runbooks.internal/kb/ai-outage`            |
| Runbook: Security Incident      | `https://runbooks.internal/kb/security-incident`    |

---

## Operational Policy Addendum

### 1. Content Governance Policies

**Content Lifecycle Policy**
All published articles must pass through a structured lifecycle: Draft → Review → Approved → Published → Archived. Automated transitions are permitted only from Draft to Review (auto-save). All other transitions require explicit human action. Articles that have been published for more than 12 months without modification must be flagged for review. Articles that remain in Draft for more than 90 days must be auto-archived with a notification to the author.

**Version Retention Policy**
Article version history must be retained for a minimum of 24 months for compliance purposes. Version history may not be deleted by Workspace Admins; deletion requests must be routed through the Data Governance team. In the event of version history corruption (see EC-AUTHOR-003), recovery must be attempted from database backups before any purge is authorized.

**Template Governance Policy**
Article templates must be validated against the canonical TipTap JSON schema before being saved to the template library. Template authors must have at minimum the Editor role. Templates may not be marked as default workspace templates without approval from a Workspace Admin. Corrupted templates (see EC-AUTHOR-008) must be quarantined immediately and not available for selection by authors.

**Attachment and Media Policy**
All file attachments must be scanned for malware upon upload before being made available. Attachment metadata records must be reconciled against S3 weekly; orphaned records older than 48 hours must be cleaned up. Embedded external media URLs must be validated at publish time and flagged if the URL returns a non-2xx status.

---

### 2. Reader Data Privacy Policies

**Anonymous Reader Tracking**
Readers of public knowledge base articles may be tracked only via anonymized session identifiers. No personally identifiable information may be stored in analytics events without explicit consent. IP addresses must be truncated to /24 subnet before storage. Heatmaps and scroll-depth analytics are permitted only for logged-in users who have accepted the platform's analytics terms.

**Search Query Privacy**
All user search queries are stored for analytics and model improvement purposes. Queries containing apparent PII (email addresses, phone numbers matching regex patterns) must be redacted before storage. Users may request deletion of their search history via the Privacy Settings page. Search query logs older than 13 months must be purged automatically.

**Content Access Logs**
Per-user article access logs (who read which article and when) are retained for 90 days for security investigation purposes. Access logs older than 90 days must be aggregated into anonymous view-count statistics and the per-user records deleted. Access logs may be reviewed by Workspace Admins only for articles within their workspace. Cross-workspace access log queries are prohibited except by the Security team during active incident investigation.

---

### 3. AI Usage Policies

**Prompt Content Policy**
The AI assistant must not receive user inputs or article content that has not been pre-screened for PII. The PII screening filter (see EC-AI-003) must be active in all production environments. Prompts sent to OpenAI must include a system-level instruction that prohibits the model from reproducing personally identifiable information even if present in retrieved context.

**AI Response Disclosure**
All AI-generated answers displayed to users must be clearly labeled with an "AI-generated" indicator. The source articles used for retrieval must be listed alongside the AI answer, enabling users to verify the basis of the response. AI answers must never be presented as authoritative without a human review flag in regulated content categories (legal, medical, financial).

**Model Change Policy**
Any change to the embedding model (e.g., from text-embedding-3-small to a successor) requires a full re-embedding of all articles before the new model is used for retrieval. Model changes must be scheduled during low-traffic maintenance windows. The previous model's vectors must be retained in a separate column during the transition period (minimum 7 days) to allow rollback.

**Cost Control Policy**
OpenAI API spending must be monitored against a monthly budget. Automated alerts must fire when spending reaches 70% and 90% of the monthly budget. Bulk operations (article imports, re-indexing) that generate embedding requests must use the BullMQ rate-limited queue and must not bypass queue concurrency limits. Emergency suspension of AI features is authorized for any on-call engineer when cost spikes exceed 2x the daily average.

---

### 4. System Availability Policies

**SLA Targets**
The Knowledge Base Platform targets 99.9% monthly uptime for the article reading experience (search, view, AI Q&A) and 99.5% for the authoring experience (create, edit, publish). The AI assistant feature is considered non-critical and has a 99.0% SLA. Planned maintenance windows must be communicated to users at least 24 hours in advance and are capped at 4 hours per month.

**Dependency Degradation Policy**
When a critical external dependency (OpenAI, OpenSearch, ElastiCache) becomes unavailable, the platform must degrade gracefully to a reduced-functionality mode rather than presenting a total outage. Specific degradation behaviors: (1) OpenAI outage → disable AI Q&A, surface cached answers where available; (2) OpenSearch outage → fall back to PostgreSQL full-text search; (3) ElastiCache outage → bypass cache, serve directly from database with rate limiting.

**Backup and Recovery Policy**
RDS PostgreSQL must be backed up via automated daily snapshots with 35-day retention. Point-in-time recovery must be tested monthly. ElastiCache Redis must use AOF persistence enabled. S3 attachment buckets must have versioning enabled and cross-region replication to a secondary region. OpenSearch index snapshots must be taken daily to S3. Recovery time objective (RTO) is 4 hours for Critical services and 24 hours for non-critical services.

**Change Management Policy**
All production deployments must pass automated tests in a staging environment first. Database migrations must be reviewed by a second engineer. Migrations that add new columns to high-traffic tables must be deployed in two phases: (1) add nullable column, (2) backfill data in a separate maintenance window. Emergency hotfixes may bypass staging review with Engineering Lead approval but must be followed by a post-deployment review within 24 hours.
