# Business Rules - Anomaly Detection System

## Severity Mapping
- If score $\ge 0.95$ → **critical**
- If score 0.90–0.95 → **high**
- If score 0.75–0.90 → **medium**
- Else → **low**

## Alert Deduplication
- Duplicate alerts are suppressed within a configurable window (default 10 minutes) for the same source, metric, and severity.

## Suppression Rules
- Quiet hours are applied per tenant.
- Suppressed alerts are still stored for auditing.

## Model Eligibility
- A model must meet minimum precision and recall thresholds before deployment.

## Feedback Handling
- Feedback labels are required before closing high or critical alerts.

## Retention Policy
- Raw data retention default: 90 days.
- Aggregated features retention default: 12 months.