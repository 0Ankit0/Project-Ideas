# Operations

## Purpose
Capture day-2 operations guidance for the **Hospital Information System**, with emphasis on clinical safety, incident response, replay, and service ownership.

## SLO and Alerting Model

| Capability | SLI | Target | Page Threshold |
|---|---|---|---|
| Patient search | successful search latency | P95 under 2 seconds | 15 minutes above threshold |
| Admission commit | success rate | 99.95 percent | 5 failed admissions in 5 minutes |
| Medication administration | write success plus queue freshness | 99.95 percent and lag under 30 seconds | lag over 5 minutes |
| Critical result escalation | time to first alert | under 5 minutes | any breach |
| HL7 or FHIR delivery | successful delivery rate | 99.9 percent | retry queue over threshold |
| Audit ingestion | accepted audit events | 100 percent for PHI access | any drop or fail-secure event |

## Operational Roles
- **Platform SRE** owns cluster, network, observability, secret rotation, and deployment health.
- **Clinical Ops Liaison** interprets patient impact, downtime activation, and operational communication.
- **Integration Engineer** owns HL7, FHIR, payer, LIS, and PACS replay or mapping issues.
- **Application On-Call** owns service-specific defects, replay approval, and schema rollback support.
- **Compliance Officer** is notified for break-glass anomalies, PHI access incidents, and audit evidence requests.

## Incident Command Workflow
1. Classify incident severity and impacted workflows.
2. Determine whether downtime mode or feature freeze is required.
3. Contain blast radius by pausing risky jobs, replay loops, or external connectors.
4. Restore service availability.
5. Reconcile data correctness using workflow-specific dashboards.
6. Publish post-incident corrective actions mapped to services and control gaps.

## Replay and Reconciliation Operations
- Provide tooling to replay events by topic, patient, encounter, message control ID, or outage window.
- Replays must be dry-runnable to show expected writes before execution.
- Each replay run stores operator, reason, input filters, records touched, and verification outcome.
- Reconciliation dashboards must exist for MPI merges, ADT census, active orders, MAR, critical alerts, and claim transmission.

## Common Operational Playbooks

| Playbook | Trigger | First Check |
|---|---|---|
| EMPI duplicate spike | duplicate queue growth or MRN collision alert | recent registration source, matching thresholds, feed quality |
| Bed board inconsistency | census mismatch or occupied dirty bed | ADT events vs occupancy segments |
| Critical result backlog | unacknowledged critical alert over SLA | notification channel health and provider roster |
| Medication admin lag | MAR write lag or barcode service failure | pharmacy queue and bedside network |
| Interface outage | ACK timeout or HTTP 5xx from partner | connector logs, retry queue depth, partner status |
| Claim submission backlog | claim queue growth or payer outage | insurance adapter health, bill holds, discharge completeness |

## Evidence and Audit Readiness
- Runbooks must include exact dashboards, saved searches, and replay commands.
- Production incidents touching PHI or patient safety require evidence package creation within 24 hours.
- Postmortems must state patient impact, data integrity impact, and whether manual chart review was required.
- Quarterly game days cover identity merge failure, ADT outage, critical result escalation failure, and regional failover.

