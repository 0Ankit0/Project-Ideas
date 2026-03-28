# C4 Code Diagram

```mermaid
flowchart TB
  IngestionController --> IngestionAppService --> EventAggregate
  FeatureController --> FeatureAppService --> FeatureSetEntity
  DetectionController --> DetectionAppService --> AnomalyAggregate
  DetectionAppService --> ModelScoringAdapter
  DetectionAppService --> AlertPublisher
```
