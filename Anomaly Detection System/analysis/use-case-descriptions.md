# Use Case Descriptions - Anomaly Detection System

## UC-01: Detect Anomaly (System)
**Primary Actor**: System  
**Trigger**: New data point received  
**Description**: System analyzes data and flags anomalies

**Preconditions**:
- Data source is registered and active
- A detection model and thresholds exist for the metric

**Main Flow**:
1. Data point ingested from stream
2. Schema validation passes
3. Feature engineering applied
4. ML model scores data point
5. If score > threshold, flag as anomaly
6. Compute severity level and explainability summary
7. Store anomaly record
8. Trigger alert if configured

**Alternate Flows**:
- A1: Missing fields → apply defaults or drop with reason
- A2: Model unavailable → fallback to rule-based threshold

**Exceptions**:
- E1: Schema invalid → reject event and log error
- E2: Storage unavailable → buffer and retry

**Postconditions**:
- Anomaly record persisted with model version and score
- Alert emitted (if rules match)

**Success Criteria**: Anomaly detected within 1 second (p95)

---

## UC-02: Investigate Anomaly
**Primary Actor**: Operator  
**Description**: Deep dive into detected anomaly

**Preconditions**:
- Operator is authenticated and authorized
- Anomaly exists and is accessible

**Main Flow**:
1. Operator opens anomaly in feed
2. System shows data point details and metadata
3. System displays historical context and baselines
4. System explains why flagged
5. Operator marks as true/false positive
6. Feedback stored for model improvement

**Alternate Flows**:
- A1: Anomaly already resolved → show resolution details
- A2: Insufficient context → show partial graph and note

**Exceptions**:
- E1: Access denied → show authorization error

**Postconditions**:
- Feedback recorded and linked to anomaly

**Success Criteria**: Operator understands root cause and classifies outcome

---

## UC-03: Train Detection Model
**Primary Actor**: Data Scientist  
**Description**: Train new ML model for detection

**Preconditions**:
- Training data available in storage
- Feature pipeline version selected

**Main Flow**:
1. Select algorithm (Isolation Forest, Autoencoder, etc.)
2. Configure hyperparameters
3. Select training data range
4. System trains model
5. System evaluates on validation set
6. Review metrics (precision, recall, F1)
7. Save model to registry
8. Optionally run shadow deployment

**Alternate Flows**:
- A1: Training fails → record error and notify
- A2: Metrics below threshold → mark as rejected

**Exceptions**:
- E1: Training data missing → block job
- E2: GPU unavailable → queue job

**Postconditions**:
- Model version stored with metadata and lineage

**Success Criteria**: Model meets acceptance thresholds

---

## UC-04: Configure Alert Rules
**Primary Actor**: System Admin  
**Description**: Set up alert routing

**Preconditions**:
- Admin has configuration permissions
- Alert channels are configured

**Main Flow**:
1. Admin accesses configuration
2. Define alert severity levels
3. Map severity to channels (email, Slack)
4. Set escalation policies
5. Configure quiet hours and suppression
6. Save and activate rules

**Alternate Flows**:
- A1: Channel unavailable → save in draft

**Exceptions**:
- E1: Validation error in rule → reject and show errors

**Postconditions**:
- Rules stored and effective immediately

**Success Criteria**: Alerts routed to correct channels

---

## UC-05: Manage Data Sources
**Primary Actor**: System Admin  
**Description**: Register and maintain data sources

**Preconditions**:
- Admin has configuration permissions

**Main Flow**:
1. Admin creates a data source record
2. System validates schema and credentials
3. Admin enables source
4. System starts ingestion and monitoring

**Postconditions**:
- Source is active and producing data

**Success Criteria**: Data ingestion starts with no validation errors

---

## UC-06: Resolve Alert
**Primary Actor**: Operator  
**Description**: Resolve anomaly alert and record resolution

**Preconditions**:
- Alert exists and is assigned or unassigned

**Main Flow**:
1. Operator opens alert
2. Adds resolution notes
3. Marks as resolved or suppressed
4. System updates status and audit log

**Postconditions**:
- Alert closed with resolution metadata

**Success Criteria**: Resolution is visible in audit trail
