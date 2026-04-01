# User Stories — Anomaly Detection System

**Version:** 2.0  
**Status:** Approved  
**Last Updated:** 2025-01-01  
**Format:** As a [role], I want to [goal], so that [benefit]

---

## Table of Contents

1. [Epic 1: Data Ingestion and Source Management](#epic-1-data-ingestion-and-source-management)
2. [Epic 2: Metric Stream Management](#epic-2-metric-stream-management)
3. [Epic 3: Anomaly Model Management](#epic-3-anomaly-model-management)
4. [Epic 4: Training Pipeline](#epic-4-training-pipeline)
5. [Epic 5: Real-Time Detection](#epic-5-real-time-detection)
6. [Epic 6: Alert Rules and Notification](#epic-6-alert-rules-and-notification)
7. [Epic 7: Incident Management](#epic-7-incident-management)
8. [Epic 8: Feedback and Model Improvement](#epic-8-feedback-and-model-improvement)
9. [Epic 9: Dashboards and Reporting](#epic-9-dashboards-and-reporting)
10. [Epic 10: Multi-Tenancy and Administration](#epic-10-multi-tenancy-and-administration)
11. [Epic 11: Integrations](#epic-11-integrations)
12. [Epic 12: API and Developer Experience](#epic-12-api-and-developer-experience)

---

## Epic 1: Data Ingestion and Source Management

### US-ING-001: Connect Prometheus Data Source
**As an** SRE,  
**I want to** connect my Prometheus instance as a data source,  
**so that** ADS can automatically scrape all my infrastructure metrics and start detecting anomalies.

**Acceptance Criteria:**
- [ ] I can create a Prometheus data source with endpoint URL, scrape interval, and optional authentication
- [ ] ADS validates connectivity on save and shows an error if unreachable
- [ ] Discovered metric streams appear in the metric streams list within 1 scrape interval
- [ ] I can test the connection before saving
- [ ] Status shows `active` once first scrape succeeds

**Story Points:** 8  
**Priority:** Must Have

---

### US-ING-002: Push Metrics via REST API
**As a** developer,  
**I want to** push metric data points to ADS via REST API,  
**so that** I can integrate custom application metrics without running a dedicated metrics agent.

**Acceptance Criteria:**
- [ ] POST `/v1/metrics/ingest` accepts single and batch (up to 10,000) data points
- [ ] Request requires stream_id, timestamp (ISO 8601), value (float), and optional labels map
- [ ] Invalid timestamps (>1 hour future, >24 hours past) return 422 with clear error message
- [ ] Rate limit exceeded returns 429 with Retry-After header
- [ ] Successful batch returns 202 with count of accepted points and list of rejected points with reasons

**Story Points:** 5  
**Priority:** Must Have

---

### US-ING-003: Use Prometheus Remote Write
**As a** DevOps engineer,  
**I want to** configure Prometheus to use ADS as a remote_write target,  
**so that** all Prometheus metrics are forwarded to ADS in real time without code changes.

**Acceptance Criteria:**
- [ ] ADS exposes a `/v1/prometheus/remote-write` endpoint compatible with Prometheus remote_write spec
- [ ] Protobuf-encoded snappy-compressed batches are accepted
- [ ] The endpoint returns appropriate HTTP 204 on success and 429 on rate limit
- [ ] Metric labels are preserved as stream labels in ADS
- [ ] Backpressure signals (429) cause Prometheus to respect WAL queue limits

**Story Points:** 8  
**Priority:** Must Have

---

### US-ING-004: Configure StatsD Ingestion
**As a** developer,  
**I want to** send metrics to ADS using the StatsD protocol,  
**so that** legacy applications that already use StatsD require zero code changes.

**Acceptance Criteria:**
- [ ] ADS listens on UDP port 8125 (configurable) for StatsD packets
- [ ] Supports counter, gauge, timer, set metric types
- [ ] Metrics are mapped to metric streams based on name patterns (configurable)
- [ ] Invalid packets are dropped and counted in a `statsd.parse_errors` counter
- [ ] I can view the StatsD packet parse error rate in the data source health dashboard

**Story Points:** 5  
**Priority:** Should Have

---

### US-ING-005: View Data Source Health
**As an** SRE,  
**I want to** see the health status of each data source,  
**so that** I can quickly identify if a metrics pipeline has broken.

**Acceptance Criteria:**
- [ ] Data source list shows status: active, error, degraded, inactive
- [ ] Error status shows the last error message and timestamp
- [ ] Health check runs every 60 seconds for pull-based sources
- [ ] Health history available for last 24 hours
- [ ] Alert can be configured when data source health changes to error

**Story Points:** 3  
**Priority:** Must Have

---

## Epic 2: Metric Stream Management

### US-MS-001: Create Metric Stream
**As an** SRE,  
**I want to** create a metric stream for a specific metric,  
**so that** I can configure anomaly detection parameters independently for each metric.

**Acceptance Criteria:**
- [ ] I can create a metric stream with: name, data source reference, labels, retention policy
- [ ] Stream enters `warming_up` state immediately after creation
- [ ] System begins collecting data and building the baseline
- [ ] Stream transitions to `active` after the configured warm-up period (default 14 days)
- [ ] Stream appears in the metric streams list with status and metadata

**Story Points:** 5  
**Priority:** Must Have

---

### US-MS-002: View Metric Stream Details
**As a** DevOps engineer,  
**I want to** view detailed information about a metric stream,  
**so that** I can understand its characteristics and detection performance.

**Acceptance Criteria:**
- [ ] Details page shows: current value, anomaly rate (7d, 30d), baseline statistics, seasonal patterns
- [ ] Time-series chart shows raw values, expected range (bands), and anomaly markers
- [ ] I can select different time ranges: 1h, 6h, 24h, 7d, 30d, custom
- [ ] Shows current model version active on this stream
- [ ] Shows last 10 anomaly events with scores and types

**Story Points:** 8  
**Priority:** Must Have

---

### US-MS-003: Configure Data Retention
**As a** platform administrator,  
**I want to** configure retention policies per metric stream,  
**so that** I can balance storage costs against historical analysis needs.

**Acceptance Criteria:**
- [ ] I can set raw data retention from 7 days to 2 years per stream
- [ ] I can set aggregated (hourly) retention separately
- [ ] System warns if retention is shorter than the model training window
- [ ] Old data is deleted automatically on schedule (nightly job)
- [ ] Retention changes apply only to data written after the policy change

**Story Points:** 3  
**Priority:** Should Have

---

### US-MS-004: Detect Data Gaps
**As an** SRE,  
**I want to** be notified when a metric stream stops receiving data,  
**so that** I can distinguish between a healthy system and a broken metrics pipeline.

**Acceptance Criteria:**
- [ ] I can configure a gap threshold per stream (default: 5 minutes)
- [ ] When gap is exceeded, a `STREAM_DATA_GAP` event is raised
- [ ] Alert rule can be created on `STREAM_DATA_GAP` event
- [ ] Gap duration is displayed in the stream health panel
- [ ] Gap events are included in the anomaly timeline

**Story Points:** 5  
**Priority:** Must Have

---

## Epic 3: Anomaly Model Management

### US-MOD-001: Select Detection Algorithm
**As a** data scientist,  
**I want to** choose from multiple detection algorithms for a metric stream,  
**so that** I can select the algorithm best suited to the metric's characteristics.

**Acceptance Criteria:**
- [ ] Algorithm selection page shows all 8 supported algorithms with descriptions and use-case guidance
- [ ] Each algorithm shows configurable hyperparameters with validation and defaults
- [ ] I can preview algorithm performance on historical data before committing
- [ ] System recommends an algorithm based on metric seasonality analysis
- [ ] Changes to algorithm create a new model version, preserving history

**Story Points:** 8  
**Priority:** Must Have

---

### US-MOD-002: Configure Ensemble Model
**As a** data scientist,  
**I want to** combine multiple algorithms into an ensemble model,  
**so that** I get more robust anomaly detection that is resilient to the weaknesses of individual algorithms.

**Acceptance Criteria:**
- [ ] I can select 2–8 algorithms and assign weights (0.0–1.0, must sum to 1.0)
- [ ] Ensemble score is computed as weighted average of individual algorithm scores
- [ ] I can override final score using a voting strategy: majority, weighted-avg, max, min
- [ ] Ensemble model shows per-algorithm contribution in anomaly event details
- [ ] A/B comparison view shows ensemble vs. individual algorithm performance

**Story Points:** 13  
**Priority:** Should Have

---

### US-MOD-003: View Model Performance
**As a** data scientist,  
**I want to** view performance metrics for each model version,  
**so that** I can understand whether the model is improving over time.

**Acceptance Criteria:**
- [ ] Model version list shows precision, recall, F1-score, FP rate, TP rate
- [ ] Performance is computed from feedback records and confirmed anomalies
- [ ] Performance trend chart shows metrics over time as feedback accumulates
- [ ] I can compare two model versions side-by-side
- [ ] Confusion matrix visualization available for classification summary

**Story Points:** 8  
**Priority:** Must Have

---

### US-MOD-004: Roll Back Model Version
**As an** SRE,  
**I want to** roll back to a previous model version,  
**so that** if a new model version is producing excessive false positives, I can restore the previous behavior immediately.

**Acceptance Criteria:**
- [ ] I can view all model versions with deployment date and performance stats
- [ ] Rollback takes effect within 30 seconds of confirmation
- [ ] Rollback creates an audit log entry with reason
- [ ] After rollback, new training jobs still target the current (rolled-back) version as baseline
- [ ] I receive a confirmation notification after rollback completes

**Story Points:** 5  
**Priority:** Must Have

---

## Epic 4: Training Pipeline

### US-TRN-001: Trigger Manual Training
**As a** data scientist,  
**I want to** trigger a training job manually,  
**so that** I can force a model update after making changes to training data or hyperparameters.

**Acceptance Criteria:**
- [ ] POST `/v1/training-jobs` accepts model ID and optional overrides (hyperparams, training window)
- [ ] Training job enters `queued` state immediately
- [ ] I can monitor job progress in real time via SSE endpoint
- [ ] Job log includes training metrics at each epoch (for LSTM) or iteration
- [ ] On completion, new model version is created and evaluation report is available

**Story Points:** 8  
**Priority:** Must Have

---

### US-TRN-002: Schedule Automatic Retraining
**As a** data scientist,  
**I want to** schedule automatic model retraining on a regular cadence,  
**so that** the model adapts to evolving metric patterns without manual intervention.

**Acceptance Criteria:**
- [ ] I can set a cron expression for retraining (e.g., `0 2 * * 0` for Sunday 2 AM)
- [ ] System validates cron expression before saving
- [ ] Scheduled jobs appear in a training job queue with next-run-time displayed
- [ ] Failed scheduled jobs generate an alert and are retried once after 30 minutes
- [ ] I can pause scheduling without deleting the job

**Story Points:** 5  
**Priority:** Should Have

---

### US-TRN-003: Monitor Drift Detection
**As an** SRE,  
**I want to** see when a model is drifting from the current data distribution,  
**so that** I know proactively when retraining is needed before detection quality degrades.

**Acceptance Criteria:**
- [ ] Drift score (0.0–1.0) is displayed per model version on the model detail page
- [ ] Drift is computed using KS test between training distribution and recent observations
- [ ] Drift score > 0.7 triggers a `MODEL_DRIFT_DETECTED` event
- [ ] Event can trigger automatic retraining if configured
- [ ] Drift history chart shows trend over 30 days

**Story Points:** 8  
**Priority:** Should Have

---

## Epic 5: Real-Time Detection

### US-DET-001: View Live Anomaly Feed
**As an** SRE,  
**I want to** see anomaly events as they are detected in real time,  
**so that** I can respond to production incidents the moment they begin.

**Acceptance Criteria:**
- [ ] SSE endpoint `/v1/stream/anomaly-events` streams new anomaly events as JSON
- [ ] WebSocket `/v1/ws/alerts` delivers alert notifications in real time
- [ ] Events include: stream name, timestamp, value, expected range, anomaly score, type, severity
- [ ] I can filter the stream by severity, stream ID, or label selector
- [ ] Connection supports heartbeat pings every 30 seconds

**Story Points:** 8  
**Priority:** Must Have

---

### US-DET-002: Investigate Anomaly Event
**As an** SRE,  
**I want to** drill into an anomaly event for full context,  
**so that** I can determine whether it requires action.

**Acceptance Criteria:**
- [ ] Anomaly event detail shows: the anomalous value, expected range, anomaly score, algorithm scores breakdown
- [ ] Time-series chart shows ±2 hours around the anomaly
- [ ] Related anomaly events (same incident) are listed
- [ ] Contributing features (for ML models) are shown with importance scores
- [ ] Quick-action buttons: Mark as FP, Mark as TP, Create Incident, Silence

**Story Points:** 5  
**Priority:** Must Have

---

### US-DET-003: Subscribe to Specific Stream
**As a** developer,  
**I want to** subscribe to anomaly events for a specific metric stream,  
**so that** my application can react programmatically to anomalies in a particular metric.

**Acceptance Criteria:**
- [ ] SSE and WebSocket endpoints accept `stream_id` filter parameter
- [ ] Events are filtered server-side before transmission
- [ ] Re-connection on disconnect resumes from last event_id (SSE Last-Event-ID header)
- [ ] Maximum 1000 concurrent subscriber connections per tenant
- [ ] Connection is closed with status 1008 if auth token expires

**Story Points:** 5  
**Priority:** Should Have

---

## Epic 6: Alert Rules and Notification

### US-ALR-001: Create Alert Rule
**As an** SRE,  
**I want to** create an alert rule that fires when anomaly score exceeds a threshold,  
**so that** my on-call team is notified when a significant anomaly is detected.

**Acceptance Criteria:**
- [ ] I can define: name, stream selector (all, specific, label-based), score threshold, severity filter
- [ ] I can set cooldown period (1 min to 24 hours) to suppress repeat alerts
- [ ] I can choose notification channels (PagerDuty, OpsGenie, Slack, email, webhook)
- [ ] I can test the rule without saving using a dry-run mode
- [ ] Rule becomes active within 5 seconds of creation

**Story Points:** 8  
**Priority:** Must Have

---

### US-ALR-002: Configure Flapping Detection
**As an** SRE,  
**I want to** enable flapping detection for alert rules,  
**so that** oscillating metrics don't generate an endless stream of alert and recovery notifications.

**Acceptance Criteria:**
- [ ] I can enable flapping on any alert rule with: window (minutes), min_changes count
- [ ] When flapping is detected, the alert is suppressed and a single `FLAPPING` event is sent
- [ ] Flapping state is cleared when the metric stabilizes for the window duration
- [ ] Flapping status is visible in the alert list alongside the alert state
- [ ] I can disable flapping detection per rule without affecting other settings

**Story Points:** 5  
**Priority:** Should Have

---

### US-ALR-003: Create Alert Silence
**As an** SRE,  
**I want to** create a maintenance silence window,  
**so that** I don't receive alerts during planned maintenance and deployments.

**Acceptance Criteria:**
- [ ] I can create a silence with: start time, end time, label matcher, optional comment
- [ ] Silences can be one-time or recurring (daily/weekly schedule)
- [ ] Active silences are listed with remaining duration and matching rules
- [ ] Silenced alerts are tracked but marked as suppressed, not lost
- [ ] Silence expiry notifications can be sent 15 minutes before end

**Story Points:** 5  
**Priority:** Must Have

---

### US-ALR-004: Configure PagerDuty Integration
**As an** SRE,  
**I want to** route critical alerts to PagerDuty,  
**so that** on-call engineers are paged via PagerDuty's escalation policies.

**Acceptance Criteria:**
- [ ] Integration config accepts PagerDuty Events API v2 integration key
- [ ] ADS sends trigger events for new alerts and resolve events when anomaly clears
- [ ] PagerDuty incident deduplication key is set to the ADS alert ID
- [ ] I can test the integration by sending a test event from the UI
- [ ] Delivery failures are logged and retried up to 5 times with exponential backoff

**Story Points:** 5  
**Priority:** Must Have

---

## Epic 7: Incident Management

### US-INC-001: View Active Incidents
**As an** SRE,  
**I want to** see all open incidents on a single dashboard,  
**so that** I have situational awareness during a production issue.

**Acceptance Criteria:**
- [ ] Incidents list shows: ID, title, severity, state, start time, affected streams count, assignee
- [ ] Filter by: severity, state, assignee, time range, label selector
- [ ] Sort by: severity, start time, duration, impact score
- [ ] Each incident links to its constituent anomaly events
- [ ] Real-time updates: new incidents appear automatically via WebSocket

**Story Points:** 8  
**Priority:** Must Have

---

### US-INC-002: Acknowledge and Investigate Incident
**As an** on-call engineer,  
**I want to** acknowledge an incident and move it to investigating state,  
**so that** my team knows someone is actively working on the issue.

**Acceptance Criteria:**
- [ ] PATCH `/v1/incidents/{id}` with `{"state": "acknowledged"}` transitions state
- [ ] Acknowledgment records the user and timestamp in the incident timeline
- [ ] Incident list shows acknowledged-by and time-to-acknowledge metric
- [ ] Moving to `investigating` state allows adding a working note
- [ ] Notification is sent to incident subscribers on state changes

**Story Points:** 3  
**Priority:** Must Have

---

### US-INC-003: Resolve Incident and Write Post-Mortem
**As an** SRE,  
**I want to** resolve an incident with a root cause and resolution notes,  
**so that** the team has a record of what happened and how it was fixed.

**Acceptance Criteria:**
- [ ] Resolution requires: root cause (free text), resolution action, optional linked change
- [ ] System pre-populates root cause suggestions based on metric correlation analysis
- [ ] Resolved incident generates a post-mortem template with timeline, impact, and next steps
- [ ] Post-mortem is exportable as PDF and Markdown
- [ ] Resolved incidents are searchable by root cause text

**Story Points:** 8  
**Priority:** Should Have

---

## Epic 8: Feedback and Model Improvement

### US-FBK-001: Mark False Positive
**As an** SRE,  
**I want to** mark a detected anomaly as a false positive,  
**so that** the system learns not to alert on that pattern in the future.

**Acceptance Criteria:**
- [ ] I can mark any anomaly event as FP with an optional reason tag
- [ ] FP mark suppresses similar patterns for 7 days (configurable)
- [ ] FP records are counted and displayed in the model performance dashboard
- [ ] After 50 FP records, a retraining job is automatically scheduled
- [ ] I can view all FP records I've submitted and revoke any of them

**Story Points:** 5  
**Priority:** Must Have

---

### US-FBK-002: Export Labeled Dataset
**As a** data scientist,  
**I want to** export all feedback records as a labeled dataset,  
**so that** I can use them for offline model evaluation or training in a custom environment.

**Acceptance Criteria:**
- [ ] Export available in CSV and JSONL formats
- [ ] Dataset includes: timestamp, value, anomaly score, label (TP/FP), reason, stream metadata
- [ ] Export endpoint supports date range filter and stream filter
- [ ] Large exports are generated asynchronously and available via download link
- [ ] Download link expires after 24 hours

**Story Points:** 3  
**Priority:** Should Have

---

## Epic 9: Dashboards and Reporting

### US-DASH-001: Create Custom Dashboard
**As an** SRE,  
**I want to** create a custom dashboard with multiple metric and anomaly widgets,  
**so that** I have a single view of the metrics that matter most to my team.

**Acceptance Criteria:**
- [ ] I can create a dashboard with a name, description, and layout (grid)
- [ ] Available widget types: time-series chart, anomaly score gauge, alert count, incident list, heatmap
- [ ] Each widget is configured with metric stream, time range, and display options
- [ ] Dashboard auto-refreshes every 30 seconds (configurable: off, 10s, 30s, 1m, 5m)
- [ ] Dashboard can be shared (read-only link) with non-ADS users

**Story Points:** 13  
**Priority:** Should Have

---

### US-DASH-002: Generate Anomaly Report
**As a** team lead,  
**I want to** generate a weekly anomaly summary report,  
**so that** I can share detection performance and trend data with stakeholders.

**Acceptance Criteria:**
- [ ] Report includes: anomaly count by severity, top affected streams, MTTD, MTTR, FP rate
- [ ] Date range is configurable (last 7d, 30d, custom)
- [ ] Available formats: PDF, JSON, CSV
- [ ] Reports can be scheduled for automatic weekly/monthly delivery via email
- [ ] Report generation is asynchronous; notify via webhook when ready

**Story Points:** 8  
**Priority:** Should Have

---

## Epic 10: Multi-Tenancy and Administration

### US-TEN-001: Manage Tenant Quotas
**As a** platform administrator,  
**I want to** configure per-tenant resource quotas,  
**so that** a single tenant cannot consume all platform resources.

**Acceptance Criteria:**
- [ ] Quotas configurable: max metric streams, max models, max alert rules, ingest RPS, retention days
- [ ] Quota usage is visible in the tenant admin panel with percentage used
- [ ] System returns 429 with quota error code when any limit is exceeded
- [ ] Alert is triggered when a tenant exceeds 80% of any quota
- [ ] Quota changes take effect within 60 seconds

**Story Points:** 8  
**Priority:** Must Have

---

### US-TEN-002: Manage User Roles
**As a** tenant administrator,  
**I want to** assign roles to users,  
**so that** I can control who can modify detection configurations vs. who can only view results.

**Acceptance Criteria:**
- [ ] Roles: Admin, Editor, Viewer, API-Only
- [ ] Admin can manage users, billing, and all resources
- [ ] Editor can create/modify detection configs but not manage users or billing
- [ ] Viewer can read all data but cannot modify anything
- [ ] Role assignments are logged in the audit trail

**Story Points:** 5  
**Priority:** Must Have

---

## Epic 11: Integrations

### US-INT-001: Configure Slack Notifications
**As an** SRE,  
**I want to** send alert notifications to a Slack channel,  
**so that** the team is notified in our primary communication tool.

**Acceptance Criteria:**
- [ ] Integration config accepts Slack webhook URL or Bot token + channel ID
- [ ] Alert messages include: severity emoji, stream name, score, timestamp, direct link to anomaly
- [ ] I can configure different channels for different severity levels
- [ ] I can test the integration by sending a test message
- [ ] Slack thread is used for alert updates (acknowledgement, resolution)

**Story Points:** 5  
**Priority:** Must Have

---

### US-INT-002: Configure Microsoft Teams Notifications
**As an** SRE,  
**I want to** receive alerts in Microsoft Teams,  
**so that** teams using Teams as their primary tool get native notification cards.

**Acceptance Criteria:**
- [ ] Integration uses Adaptive Card format for rich notifications
- [ ] Card includes: severity, metric name, value, expected range, trend chart thumbnail
- [ ] Action buttons in card: Acknowledge, View Details, Silence 1h
- [ ] I can configure per-team webhook URLs for different projects
- [ ] Delivery failures are retried and reported in the integration health panel

**Story Points:** 5  
**Priority:** Should Have

---

## Epic 12: API and Developer Experience

### US-API-001: Authenticate with API Key
**As a** developer,  
**I want to** authenticate with an API key,  
**so that** my scripts and automation tools can interact with ADS without user credentials.

**Acceptance Criteria:**
- [ ] I can create API keys scoped to specific permissions (read-only, read-write, admin)
- [ ] API key is shown only once at creation; stored as hash in database
- [ ] API key passed as `Authorization: Bearer <key>` or `X-API-Key: <key>` header
- [ ] I can set expiry date on API key (optional, max 1 year)
- [ ] API key last-used timestamp is tracked and displayed

**Story Points:** 5  
**Priority:** Must Have

---

### US-API-002: Use OpenAPI SDK
**As a** developer,  
**I want to** use a generated SDK in Python/Go/TypeScript,  
**so that** I can integrate ADS into my application without hand-crafting HTTP requests.

**Acceptance Criteria:**
- [ ] OpenAPI 3.1 spec is published at `/v1/openapi.json`
- [ ] Python SDK generated and published to PyPI as `anomaly-detection-client`
- [ ] Go SDK generated and available as Go module
- [ ] TypeScript SDK generated and published to npm as `@ads/client`
- [ ] SDK includes authentication helper, retry logic, and pagination utilities

**Story Points:** 13  
**Priority:** Should Have

---

### US-API-003: Paginate Large Result Sets
**As a** developer,  
**I want to** paginate through large lists of anomaly events,  
**so that** my application can efficiently process historical data without timeout or memory issues.

**Acceptance Criteria:**
- [ ] All list endpoints support cursor-based pagination (`cursor` and `limit` query params)
- [ ] Response includes `next_cursor`, `prev_cursor`, and `total_count`
- [ ] Maximum page size is 500 items; default is 50
- [ ] Cursor is stable for the duration of a paginated request sequence
- [ ] Empty page returns 200 with empty `data` array, not 404

**Story Points:** 3  
**Priority:** Must Have

---

*Total Stories: 40 | Must Have: 24 | Should Have: 14 | Nice to Have: 2*  
*Total Story Points: 252*
