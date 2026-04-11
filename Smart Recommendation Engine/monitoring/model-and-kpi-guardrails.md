# Monitoring Guardrails: Model Quality + Business KPIs

## 1) Monitoring Objectives
- Detect model quality regressions before broad user impact.
- Protect core business KPIs during model/index/config rollouts.
- Enable deterministic, fast rollback with low operator ambiguity.

## 2) Guardrail Layers

## 2.1 Model quality guardrails
| Metric | Scope | Trigger |
|---|---|---|
| NDCG@10 delta vs baseline | shadow + canary | < -3% for 30m |
| Recall@50 delta | shadow + canary | < -4% for 30m |
| Calibration error (ECE) | slice/global | > +15% from baseline |
| Cold-start cohort CTR delta | canary | < -5% |
| Long-tail exposure share | global | drops below policy floor |

## 2.2 Business KPI guardrails
| KPI | Trigger | Severity |
|---|---|---|
| CTR | -4% vs control for 20m | High |
| CVR | -3% vs control for 30m | Critical |
| Revenue/session | -2.5% vs control for 30m | Critical |
| Session length | -5% vs trailing 7-day baseline | Medium |
| Unsubscribe/hide rate | +15% vs baseline | High |

## 2.3 Reliability guardrails
| SLI | Trigger |
|---|---|
| Recommendation API p95 | > 120ms for 10m |
| Error rate | > 1% for 5m |
| Degraded mode ratio | > 5% for 10m |
| Feature timeout rate | > 2% for 10m |

## 3) Rollback Triggers

Automatic rollback should execute when **any critical condition** is met:
1. CVR or revenue/session breach persists for configured window.
2. Error rate or availability SLO breach crosses incident threshold.
3. Feature/model contract mismatch detected at runtime.
4. Fairness/compliance hard policy violation triggered.

Manual rollback (on-call decision) when:
- medium/high guardrails persist but do not cross critical thresholds,
- anomaly confidence is low and requires human validation,
- concurrent external events could confound metrics.

## 4) Rollback Execution Policy
- Roll back in this order:
  1. latest config change,
  2. latest model version,
  3. latest index version,
  4. traffic split to stable cell/region.
- Keep `last_known_good` pointers in model registry and index control plane.
- Post-rollback: hold for 30 minutes, verify KPI recovery, then close incident or escalate.

## 5) Dashboard & Alerting Requirements
- Dashboards must segment by:
  - user lifecycle (cold/warm),
  - tenant,
  - locale,
  - device,
  - traffic cohort (control/canary/treatment).
- Every alert must include:
  - current value,
  - baseline/control value,
  - suggested runbook link,
  - rollback recommendation (`yes/no`).

## 6) Release Guardrail Workflow
1. Shadow monitoring (0% user impact) for at least 24 hours.
2. Canary (1-5%) with live KPI comparison.
3. Progressive ramp (25%, 50%, 100%) only if no guardrail breach.
4. Auto-freeze release if warning alerts repeat 3 times within 24 hours.

## 7) Runbook Attachments (Required)
- `RB-MODEL-ROLLBACK`
- `RB-INDEX-ROLLBACK`
- `RB-FEATURE-STORE-DEGRADED`
- `RB-DEGRADED-MODE-RECOVERY`
