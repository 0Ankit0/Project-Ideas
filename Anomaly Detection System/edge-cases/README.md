# Edge Cases & Mitigations - Anomaly Detection System

This folder captures cross-cutting edge cases across ingestion, modeling, alerting, storage, and operations. Each file includes detection strategies, mitigations, and fallback behavior.

## Contents

- Data ingestion and schema drift: see [edge-cases/data-ingestion.md](edge-cases/data-ingestion.md)
- Feature engineering and windowing: see [edge-cases/feature-engineering.md](edge-cases/feature-engineering.md)
- Model scoring and drift: see [edge-cases/model-scoring.md](edge-cases/model-scoring.md)
- Alerting and notification: see [edge-cases/alerting.md](edge-cases/alerting.md)
- Storage and retention: see [edge-cases/storage.md](edge-cases/storage.md)
- API/UI issues: see [edge-cases/api-and-ui.md](edge-cases/api-and-ui.md)
- Security and compliance: see [edge-cases/security-and-compliance.md](edge-cases/security-and-compliance.md)
- Operations and deployment: see [edge-cases/operations.md](edge-cases/operations.md)

## How to Use

1. Review edge cases during design and implementation.
2. Map each edge case to tests and runbooks.
3. Update as new data sources, models, or alert channels are added.