# BPMN / Swimlane Diagram - Anomaly Detection System

## End-to-End Anomaly Handling

```mermaid
flowchart TB
    subgraph Source["📊 Data Source"]
        S1[Emit Data Point]
    end
    
    subgraph System["🤖 Detection Engine"]
        SYS1[Ingest Data]
        SYS2[Feature Engineering]
        SYS3[ML Scoring]
        SYS4[Threshold Check]
        SYS5[Generate Alert]
    end
    
    subgraph Operator["👤 Operator Lane"]
        OP1[Receive Alert]
        OP2[View Dashboard]
        OP3[Investigate]
        OP4{True<br/>Positive?}
        OP5[Acknowledge]
        OP6[Mark False Positive]
    end
    
    subgraph Feedback["🔄 Learning Loop"]
        FB1[Store Feedback]
        FB2[Queue for Retraining]
    end
    
    S1 --> SYS1
    SYS1 --> SYS2
    SYS2 --> SYS3
    SYS3 --> SYS4
    SYS4 -->|Anomaly| SYS5
    SYS5 --> OP1
    
    OP1 --> OP2
    OP2 --> OP3
    OP3 --> OP4
    OP4 -->|Yes| OP5
    OP4 -->|No| OP6
    
    OP5 --> FB1
    OP6 --> FB1
    FB1 --> FB2
```

---

## Model Training & Deployment

```mermaid
flowchart LR
    subgraph DS["👨‍💻 Data Scientist"]
        DS1[Select Algorithm]
        DS2[Configure Params]
        DS3[Review Metrics]
        DS4[Approve Deploy]
    end
    
    subgraph Train["⚙️ Training"]
        T1[Load Data]
        T2[Train Model]
        T3[Evaluate]
        T4[Register]
    end
    
    subgraph Deploy["🚀 Deploy"]
        D1[A/B Test]
        D2[Canary]
        D3[Full Rollout]
    end
    
    DS1 --> DS2
    DS2 --> T1
    T1 --> T2
    T2 --> T3
    T3 --> T4
    T4 --> DS3
    DS3 --> DS4
    DS4 --> D1
    D1 --> D2
    D2 --> D3
```

## Purpose and Scope
Defines cross-team handoffs across automation, analyst operations, compliance, and customer communication.

## Assumptions and Constraints
- Swimlanes map to real teams with 24x7 ownership routing.
- Handoff timers are contractual and alertable.
- Compensation steps are required for partial failures.

### End-to-End Example with Realistic Data
For high-value transfer `TR-5541`, automation lane applies hold, analyst lane verifies identity, compliance lane approves/denies release, and customer ops lane sends notification. If compliance unavailable >15 min, escalation lane pages duty manager.

## Decision Rationale and Alternatives Considered
- Used BPMN events for timer/escalation clarity across teams.
- Rejected informal checklist because it lacked handoff observability.
- Included compensation path for mistaken holds to minimize customer harm.

## Failure Modes and Recovery Behaviors
- Analyst queue saturation -> overflow routing to secondary region team.
- Compliance API unavailable -> queue decision task with SLA countdown visible to ops.

## Security and Compliance Implications
- Inter-lane artifacts include least-privilege evidence views by lane.
- Customer notifications avoid sensitive reason-code disclosure.

## Operational Runbooks and Observability Notes
- Lane SLA dashboard highlights bottleneck owner in real time.
- Runbook specifies manual continuity mode per lane during tool outages.
