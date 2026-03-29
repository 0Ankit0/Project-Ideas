# Edge Cases - Data Ingestion

### 1.1. Schema Drift
* **Scenario**: A data source adds/removes fields or changes a field type without notice.
* **Impact**: Ingestion failures, missing features, or incorrect scoring.
* **Solution**:
    * **Validation**: Enforce schema registry compatibility rules and reject breaking changes.
    * **Routing**: Send unknown fields to `metadata.extra` for safe storage.
    * **Ops**: Alert and optionally disable the source until schema is updated.

### 1.2. Late or Out-of-Order Events
* **Scenario**: Events arrive outside expected time windows or in the wrong order.
* **Impact**: Feature windows become inaccurate, causing false anomalies.
* **Solution**:
    * **Processing**: Use event-time processing with watermarks.
    * **Buffering**: Hold events within a configurable lateness window.
    * **Policy**: Tag and exclude stale events from real-time alerting.

### 1.3. Duplicate Events
* **Scenario**: The same event is ingested multiple times due to retries.
* **Impact**: Inflated metrics, duplicate anomalies, alert storms.
* **Solution**:
    * **Idempotency**: Deduplicate using a hash of `sourceId`, `timestamp`, and `values`.
    * **Storage**: Store ingestion checksums to prevent reprocessing.

### 1.4. Missing or Null Values
* **Scenario**: Payloads are incomplete or required fields are null.
* **Impact**: Model scoring errors or misleading features.
* **Solution**:
    * **Validation**: Reject events missing critical fields.
    * **Fallback**: Impute using last-known-good values or sentinel defaults.
    * **Telemetry**: Track missing-rate metrics per source.

### 1.5. Timezone Mismatch
* **Scenario**: Events are sent in local time or without timezone offsets.
* **Impact**: Misaligned time windows and incorrect baselines.
* **Solution**:
    * **Normalization**: Convert all timestamps to UTC at ingest.
    * **Validation**: Reject timestamps without timezone metadata.

### 1.6. Burst Traffic / Backpressure
* **Scenario**: A source emits spikes far above expected throughput.
* **Impact**: Queue lag, delayed scoring, SLA breaches.
* **Solution**:
    * **Scaling**: Autoscale consumers and processing workers.
    * **Throttling**: Apply rate limits and sampling for low-priority sources.
    * **Degradation**: Switch to coarse-grained scoring under heavy load.

### 1.7. Poison Messages
* **Scenario**: Malformed payloads repeatedly fail parsing.
* **Impact**: Pipeline stalls or hot loops on retries.
* **Solution**:
    * **Isolation**: Route to a dead-letter queue with reason and payload.
    * **Recovery**: Provide replay tooling after schema or code fixes.

## Purpose and Scope
Handles ingestion edge conditions: malformed payloads, replay, ordering, and duplicate suppression.

## Assumptions and Constraints
- Ingestion supports both streaming and bulk backfill paths.
- Idempotency key strategy is consistent across producers.
- Malformed data is quarantined, never silently dropped.

### End-to-End Example with Realistic Data
Nightly `batch_2026_02_14` (2M rows): 0.7% malformed rows sent to quarantine with row-level reason; valid rows publish with idempotency keys; replay cursor supports deterministic reprocessing after fix.

## Decision Rationale and Alternatives Considered
- Adopted quarantine-first pattern to preserve raw evidence.
- Rejected “best effort parse” that can corrupt feature distributions.
- Added replay controls keyed by producer and time window.

## Failure Modes and Recovery Behaviors
- Clock skew causes ordering anomalies -> event-time watermarking with late-arrival policy.
- Backfill saturates stream cluster -> separate backfill lane with throttle limits.

## Security and Compliance Implications
- Inbound PII validation and tokenization checks run before persistence.
- Quarantine store access is tightly restricted and audited.

## Operational Runbooks and Observability Notes
- Ingestion lag, quarantine rate, and replay throughput are key signals.
- Runbook covers replay dry-run, cutover, and reconciliation checks.
