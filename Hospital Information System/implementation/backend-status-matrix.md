# Backend Status Matrix

## Purpose
Track delivery readiness of the **Hospital Information System** backend domains so release managers know what is build-ready, what still needs design work, and what evidence is required before go-live.

## Maturity Scale
- **L0 Planned**: scope identified, no stable contracts.
- **L1 Designed**: state model, APIs, events, and security expectations documented.
- **L2 Build Ready**: contracts frozen, migration plan approved, test plan defined.
- **L3 Feature Complete**: implementation, automated tests, and observability complete in staging.
- **L4 Go-Live Ready**: operational runbooks, support ownership, drill evidence, and compliance sign-off complete.

## Domain Status Matrix

| Service Domain | Capability Highlights | Current Target | Blocking Work | Go-Live Evidence |
|---|---|---|---|---|
| Patient Identity | EMPI, MRN, aliases, merge or unmerge, consent registry, deceased handling | L2 Build Ready | finalize probabilistic match tuning, FHIR patient mapping, dual-approval merge UX | duplicate test suite, merge replay drill, consent audit report |
| ADT and Bed Management | admission, transfer, discharge, bed board, room cleaning, census | L2 Build Ready | ward rule catalog, environmental services integration, boarding queue logic | admit and transfer workflow test, capacity alert dashboard |
| Clinical | encounters, notes, diagnoses, problem list, shared order shell, discharge summary | L2 Build Ready | encounter template config, signature workflow, addendum model | signed note immutability tests, discharge journey test |
| Pharmacy | formulary, verification queue, dispense, MAR, controlled substance log | L1 Designed | formulary source integration, barcode workflow, witness capture | med admin journey test, controlled substance audit export |
| Lab | specimen tracking, result versioning, critical alerts, analyzer interfaces | L1 Designed | specimen label workflow, analyzer connector, escalation policy matrix | critical result drill, ORU mapping verification |
| Radiology | modality worklist, accession, report lifecycle, PACS links | L1 Designed | PACS connector, report correction model, image reference policy | radiology order to report test, PACS outage replay test |
| Billing | charge rules, claim work queue, invoice and remittance, denial handling | L1 Designed | charge description master mapping, coding handoff, denial reason catalog | clean claim test, remittance replay evidence |
| Insurance | eligibility, pre-auth, claim submit, claim status, payer exception handling | L1 Designed | payer adapter library, timeout policy, auth response normalization | payer sandbox test, outage retry drill |
| Staff | provider directory, departments, privileges, roster lookup | L3 Feature Complete | finalize HR sync error handling | privilege sync alerts, stale roster test |
| OT | booking, surgical checklist, post-op note hooks | L1 Designed | surgical workflow integration with ADT and Clinical | surgery booking test, checklist audit trail |
| FHIR Adapter | Patient, Encounter, Observation, DiagnosticReport, MedicationRequest, Coverage, Consent | L1 Designed | profile definitions, compartment filtering, SMART scopes | FHIR conformance test pack |
| HL7 Integration Engine | ADT, ORM, ORU, ACK, replay, dead-letter operations | L2 Build Ready | partner endpoint configs, ACK timeout tuning | interface replay drill, ACK reconciliation report |
| Audit and Notification | PHI access evidence, break-glass, critical alerts, outage notices | L2 Build Ready | retrospective review queue, notification channel failover | audit fail-secure test, critical alert delivery test |

## Release Gates by Wave

| Wave | Services Required at L4 | Notes |
|---|---|---|
| Wave 1 | Patient Identity, Staff, Audit and Notification | foundation for identity, consent, and access controls |
| Wave 2 | ADT and Bed Management | enables inpatient operations and bed board |
| Wave 3 | Clinical, FHIR Adapter | encounter record becomes usable for care documentation |
| Wave 4 | Pharmacy, Lab, Radiology, HL7 Integration Engine | closed-loop clinical operations |
| Wave 5 | Billing, Insurance | revenue cycle and payer workflows |
| Wave 6 | OT plus all prior domains with DR evidence | full operational hardening |

## Readiness Review Questions
1. Are APIs, event schemas, and migrations compatible with previous release versions.
2. Can the team replay duplicate or failed events without manual database edits.
3. Does the service have on-call ownership and alert thresholds tuned for production.
4. Is PHI access audited for every sensitive operation.
5. Has the service passed downtime and recovery scenarios relevant to its domain.

