# Class Diagram - Anomaly Detection System

## Python ML Classes

```mermaid
classDiagram
    class AnomalyDetector {
        <<interface>>
        +train(data) void
        +score(data_point) float
        +detect(data_point) bool
    }
    
    class IsolationForestDetector {
        -model IsolationForest
        -contamination float
        -threshold float
        +train(data) void
        +score(data_point) float
        +detect(data_point) bool
    }
    
    class AutoencoderDetector {
        -model Sequential
        -threshold float
        +train(data) void
        +score(data_point) float
        +detect(data_point) bool
        -computeReconstructionError(data) float
    }
    
    class StatisticalDetector {
        -mean float
        -std float
        -n_sigma int
        +train(data) void
        +score(data_point) float
        +detect(data_point) bool
    }
    
    class EnsembleDetector {
        -detectors List~AnomalyDetector~
        -weights List~float~
        +train(data) void
        +score(data_point) float
        +detect(data_point) bool
        -aggregateScores(scores) float
    }
    
    class FeatureEngine {
        -windowSize int
        -features List~str~
        +extractFeatures(data_point) Dict
        +computeRollingStats(window) Dict
        +normalize(features) Dict
    }
    
    class AlertService {
        -channels List~AlertChannel~
        -rules List~AlertRule~
        +sendAlert(anomaly) void
        +checkRules(anomaly) List~AlertRule~
        +routeToChannels(alert, rules) void
    }

    class AlertRule {
        +id str
        +severity str
        +conditions Dict
        +channels List~str~
        +active bool
    }

    class WebhookEndpoint {
        +id str
        +name str
        +url str
        +events List~str~
        +status str
    }

    class FeedbackService {
        +saveFeedback(anomalyId, label, notes) void
    }

    class AuditLogger {
        +record(action, entityId, metadata) void
    }
    
    class DetectionPipeline {
        -featureEngine FeatureEngine
        -detector AnomalyDetector
        -alertService AlertService
        +process(data_point) AnomalyResult
    }
    
    AnomalyDetector <|-- IsolationForestDetector
    AnomalyDetector <|-- AutoencoderDetector
    AnomalyDetector <|-- StatisticalDetector
    AnomalyDetector <|-- EnsembleDetector
    EnsembleDetector o-- AnomalyDetector
    DetectionPipeline --> FeatureEngine
    DetectionPipeline --> AnomalyDetector
    DetectionPipeline --> AlertService
    AlertService --> AlertRule
    AlertService --> WebhookEndpoint
    FeedbackService --> AuditLogger
```

## Data Classes

```mermaid
classDiagram
    class DataPoint {
        +str sourceId
        +Dict values
        +DateTime timestamp
        +Dict metadata
    }
    
    class Features {
        +str dataPointId
        +Dict computed
        +Dict normalized
    }
    
    class AnomalyResult {
        +str dataPointId
        +float score
        +bool isAnomaly
        +str severity
        +Dict explanation
    }
    
    class Alert {
        +str alertId
        +str anomalyId
        +str severity
        +str channel
        +str status
        +DateTime sentAt
    }

    class Feedback {
        +str feedbackId
        +str anomalyId
        +str userId
        +str label
        +str notes
        +DateTime createdAt
    }

    class AuditLog {
        +str auditId
        +str actorId
        +str action
        +Dict metadata
        +DateTime createdAt
    }
    
    class TrainingConfig {
        +str algorithm
        +Dict hyperparameters
        +str dataRange
        +float testSplit
    }
```

## Purpose and Scope
Details class-level responsibilities, composition, and invariants inside core scoring and policy modules.

## Assumptions and Constraints
- Domain classes are immutable where possible.
- Service classes coordinate, domain classes decide.
- No cyclic dependencies across packages.

### End-to-End Example with Realistic Data
`AnomalyScorer` composes `FeatureAssembler` and `PolicyEvaluator`; `ScoreResult` value object carries normalized score, reasons, and confidence; `CaseCommandFactory` translates decision to workflow action.

## Decision Rationale and Alternatives Considered
- Used value objects for score/reason payload to reduce primitive obsession.
- Rejected inheritance-heavy hierarchy; favored composition for maintainability.
- Kept policy evaluation separate to allow independent testing and versioning.

## Failure Modes and Recovery Behaviors
- Null/invalid feature set -> `FeatureAssembler` emits typed validation error.
- Rule-policy mismatch -> `PolicyEvaluator` returns deterministic fallback action.

## Security and Compliance Implications
- Class design restricts exposure of sensitive fields via typed wrappers.
- Audit event classes are append-only and signed before persistence.

## Operational Runbooks and Observability Notes
- Coverage report requires branch coverage on policy decision classes.
- Runbook for class-level bugs references owning package and rollback strategy.
