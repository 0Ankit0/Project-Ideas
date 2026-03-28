# C4 Code Diagram

This document provides a **code-level C4 view** of the Anomaly Detection System so engineers can map runtime behavior to concrete implementation modules.

## Code-Level Structure
```mermaid
flowchart TB
  subgraph Interface[Interface Layer]
    IngestionController
    FeatureController
    DetectionController
    AlertController
  end

  subgraph Application[Application Layer]
    IngestionAppService
    FeatureAppService
    DetectionAppService
    AlertAppService
  end

  subgraph Domain[Domain Layer]
    EventAggregate
    FeatureSetEntity
    DetectionPolicy
    AnomalyAggregate
    AlertRule
  end

  subgraph Infrastructure[Infrastructure Layer]
    EventRepository
    FeatureRepository
    DetectionRepository
    ModelScoringAdapter
    AlertPublisher
    MetricsAdapter
  end

  IngestionController --> IngestionAppService --> EventAggregate
  FeatureController --> FeatureAppService --> FeatureSetEntity
  DetectionController --> DetectionAppService --> AnomalyAggregate
  AlertController --> AlertAppService --> AlertRule

  DetectionAppService --> DetectionPolicy
  DetectionAppService --> ModelScoringAdapter
  DetectionAppService --> DetectionRepository
  DetectionAppService --> MetricsAdapter

  IngestionAppService --> EventRepository
  FeatureAppService --> FeatureRepository
  AlertAppService --> AlertPublisher
```

## Critical Runtime Sequence: Online Detection
```mermaid
sequenceDiagram
  autonumber
  participant API as DetectionController
  participant APP as DetectionAppService
  participant FEAT as FeatureRepository
  participant MODEL as ModelScoringAdapter
  participant RULE as DetectionPolicy
  participant REPO as DetectionRepository
  participant ALERT as AlertPublisher

  API->>APP: detect(eventId)
  APP->>FEAT: load feature vector
  FEAT-->>APP: feature set
  APP->>MODEL: score(features)
  MODEL-->>APP: score + metadata
  APP->>RULE: evaluate thresholds/policies
  RULE-->>APP: anomaly decision
  APP->>REPO: persist result
  alt anomaly=true
    APP->>ALERT: publish alert event
  end
  APP-->>API: detection response
```

## Module Responsibilities
- **Controllers**: transport mapping, input validation, and request context propagation.
- **Application services**: orchestration boundaries, transaction scope, idempotency handling.
- **Domain types**: decision invariants (thresholds, suppression windows, severity mapping).
- **Infrastructure adapters**: model invocation, persistence, telemetry, and outbound alert delivery.

## Implementation Notes
- Keep model-scoring adapter stateless; cache only immutable model metadata.
- Persist decision artifacts (`features hash`, `model version`, `policy version`) for auditability.
- Prefer event-driven alert fanout so downstream consumers can evolve independently.
