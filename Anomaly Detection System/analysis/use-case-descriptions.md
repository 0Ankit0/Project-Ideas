# Use Case Descriptions - Anomaly Detection System

## UC-01: Detect Anomaly (System)
**Trigger**: New data point received  
**Description**: System analyzes data and flags anomalies

**Main Flow**:
1. Data point ingested from stream
2. Feature engineering applied
3. ML model scores data point
4. If score > threshold, flag as anomaly
5. Calculate severity level
6. Store anomaly record
7. Trigger alert if configured

**Success**: Anomaly detected within 1 second

---

## UC-02: Investigate Anomaly
**Actor**: Operator  
**Description**: Deep dive into detected anomaly

**Main Flow**:
1. Operator clicks anomaly in feed
2. System shows data point details
3. System displays historical context (graph)
4. System explains why flagged
5. Operator marks as true/false positive
6. Feedback stored for model improvement

**Success**: Operator understands root cause

---

## UC-03: Train Detection Model
**Actor**: Data Scientist  
**Description**: Train new ML model for detection

**Main Flow**:
1. Select algorithm (Isolation Forest, Autoencoder, etc.)
2. Configure hyperparameters
3. Select training data range
4. System trains model
5. System evaluates on validation set
6. Review metrics (precision, recall, F1)
7. Save model to registry

**Success**: Model trained with acceptable metrics

---

## UC-04: Configure Alert Rules
**Actor**: System Admin  
**Description**: Set up alert routing

**Main Flow**:
1. Admin accesses configuration
2. Define alert severity levels
3. Map severity to channels (email, Slack)
4. Set escalation policies
5. Configure quiet hours
6. Save and activate rules

**Success**: Alerts routed to correct channels
