# Event Catalog - Anomaly Detection System

| Event | Producer | Consumers | Description |
|-------|----------|-----------|-------------|
| data.ingested | Ingestion Service | Feature Engine | Data point accepted and validated |
| features.computed | Feature Engine | Scoring Service | Feature vector generated |
| anomaly.detected | Scoring Service | Alert Router, Storage | Anomaly scored above threshold |
| alert.created | Alert Router | Notification Channels | Alert emitted to channels |
| alert.acknowledged | UI/API | Audit Log | Alert acknowledged by operator |
| alert.resolved | UI/API | Audit Log | Alert resolved |
| model.trained | Training Service | Model Registry | Model training completed |
| model.deployed | Model Registry | Scoring Service | New model version activated |
| feedback.submitted | UI/API | Training Pipeline | Human feedback stored |