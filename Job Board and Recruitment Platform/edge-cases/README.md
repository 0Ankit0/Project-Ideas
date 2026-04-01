# Edge Case Documentation — Job Board and Recruitment Platform

## Purpose and Scope

This document serves as the master index for all edge case scenarios identified across the Job Board and Recruitment Platform. Each edge case captures a failure mode that has either occurred in production, been identified through design review, or surfaced during load and chaos testing. The goal is to give every engineering, product, and support team member a single reference point for understanding what can go wrong, how to detect it, and how to recover — before an incident becomes a crisis.

This documentation covers the full candidate and recruiter lifecycle: from job creation and external distribution, through application ingestion and ATS pipeline management, into interview scheduling, offer generation, and final hire. It also covers cross-cutting concerns including API reliability, UI data-integrity, security, compliance (GDPR, EEO, pay transparency), and infrastructure operations.

**Out of scope:** General platform architecture, runbooks for routine deployments, and feature specifications. Those live in their respective repos and wikis.

---

## How to Use This Documentation for Incident Response

When an alert fires or a user reports unexpected behaviour:

1. **Identify the category** — Use the category overview table below to narrow down which file applies.
2. **Find the edge case** — Each EC is numbered sequentially (EC-01 through EC-56). Search the relevant file by EC number or keyword.
3. **Follow Mitigation steps first** — Mitigation is the immediate, time-sensitive action to stop blast radius from expanding.
4. **Execute Recovery** — Once the immediate threat is contained, follow the Recovery steps to restore normal service.
5. **File a post-mortem** — Reference the EC number in the post-mortem title so future searches surface it immediately.
6. **Apply Prevention** — Every Prevention section includes design or process changes. Assign these as follow-up tickets before closing the incident.

---

## Edge Case Classification

Each edge case is assigned a severity level based on its impact to candidates, recruiters, data integrity, legal obligations, or revenue.

| Severity | Definition |
|----------|-----------|
| **Critical** | Data loss, data breach, legal violation, or complete loss of a core workflow. Requires immediate on-call escalation. |
| **High** | Significant feature degradation, incorrect data presented to users, or SLA breach imminent. Requires same-day response. |
| **Medium** | Partial feature loss with a viable workaround available. Response required within one business day. |
| **Low** | Cosmetic, minor UX friction, or edge condition that affects fewer than 0.1% of users. Scheduled fix acceptable. |

---

## Risk Matrix — Severity vs. Probability

The following matrix maps each severity level against the likelihood of occurrence to guide prioritisation of prevention work.

```
                  PROBABILITY
                  Rare      Unlikely   Possible   Likely    Almost Certain
               ┌─────────┬──────────┬──────────┬─────────┬───────────────┐
  Critical     │  EC-43  │  EC-41   │  EC-45   │  EC-27  │     EC-03     │
               ├─────────┼──────────┼──────────┼─────────┼───────────────┤
  High         │  EC-07  │  EC-06   │  EC-02   │  EC-08  │     EC-01     │
               ├─────────┼──────────┼──────────┼─────────┼───────────────┤
  Medium       │  EC-31  │  EC-24   │  EC-21   │  EC-13  │     EC-09     │
               ├─────────┼──────────┼──────────┼─────────┼───────────────┤
  Low          │  EC-47  │  EC-48   │  EC-38   │  EC-40  │     EC-10     │
               └─────────┴──────────┴──────────┴─────────┴───────────────┘
```

---

## Edge Case Category Overview

### Category 1 — Job Posting and Matching
**File:** `job-posting-and-matching.md`
**EC Range:** EC-01 through EC-08
**Description:** Covers failures in the job creation workflow, external job board distribution (LinkedIn, Indeed), AI resume matching, pay transparency compliance, and search cache invalidation.

| EC | Title | Severity |
|----|-------|----------|
| EC-01 | Job posted without required approval | High |
| EC-02 | Job distribution to Indeed API fails silently | High |
| EC-03 | AI resume matching returns incorrect skills | Critical |
| EC-04 | Duplicate job posting created | Medium |
| EC-05 | Job board API quota exhausted | High |
| EC-06 | Job posted with salary violating pay transparency law | High |
| EC-07 | Job with HTML injection reaches external boards | High |
| EC-08 | Job expires but still appears active in search | Medium |

---

### Category 2 — Application Tracking
**File:** `application-tracking.md`
**EC Range:** EC-09 through EC-16
**Description:** Covers duplicate application detection, corrupt file handling, race conditions on job close, pipeline integrity, bulk import failures, candidate deduplication, and AI parsing gaps.

| EC | Title | Severity |
|----|-------|----------|
| EC-09 | Candidate applies to the same job twice | Medium |
| EC-10 | Resume file is corrupt | Medium |
| EC-11 | Application submitted after job officially closed | High |
| EC-12 | ATS pipeline stage deleted while candidates are in it | High |
| EC-13 | Bulk application import partial failure | High |
| EC-14 | Candidate profile merge conflict | Medium |
| EC-15 | AI parsing service returns empty result for valid resume | High |
| EC-16 | Stage auto-move rule creates infinite loop | Critical |

---

### Category 3 — Interview Scheduling
**File:** `interview-scheduling.md`
**EC Range:** EC-17 through EC-24
**Description:** Covers OAuth token expiry, interviewer cancellations, timezone bugs, Zoom rate limits, double-booking races, multi-round availability, lost feedback triggers, and video platform outages.

| EC | Title | Severity |
|----|-------|----------|
| EC-17 | Google Calendar OAuth token expired during sync | High |
| EC-18 | Interviewer declines after candidate confirmation sent | Medium |
| EC-19 | Timezone mismatch causes meeting at wrong time | High |
| EC-20 | Zoom API rate limit hit during bulk creation | Medium |
| EC-21 | Same calendar slot double-booked concurrently | High |
| EC-22 | Interviewer unavailable for multi-round interview | Medium |
| EC-23 | Feedback deadline not triggered after interview | High |
| EC-24 | Video link active but platform down at meeting time | High |

---

### Category 4 — Offer Management
**File:** `offer-management.md`
**EC Range:** EC-25 through EC-32
**Description:** Covers mis-addressed offer letters, DocuSign countersignature gaps, dual-acceptance races, expiry enforcement failures, off-band salary approvals, conditional background check results, currency errors, and DocuSign envelope expiry.

| EC | Title | Severity |
|----|-------|----------|
| EC-25 | Offer letter sent to wrong candidate | Critical |
| EC-26 | Candidate accepts in portal, DocuSign unsigned | High |
| EC-27 | Two offers generated for same role simultaneously | Critical |
| EC-28 | Offer expiry deadline not enforced | High |
| EC-29 | Salary above approved band without HR approval | High |
| EC-30 | Background check "consider" after offer accepted | High |
| EC-31 | Offer generated in wrong currency | Medium |
| EC-32 | DocuSign envelope expires before candidate signs | Medium |

---

### Category 5 — API and UI
**File:** `api-and-ui.md`
**EC Range:** EC-33 through EC-40
**Description:** Covers LinkedIn distribution rate limits, webhook loss from Indeed, oversized resume uploads, analytics query timeouts, GDPR export size limits, silent API failures, drag-and-drop pipeline corruption, and Elasticsearch index lag.

| EC | Title | Severity |
|----|-------|----------|
| EC-33 | LinkedIn API rate limit during bulk distribution | High |
| EC-34 | Webhook delivery failure from Indeed | High |
| EC-35 | Large resume file causes timeout/memory spike | Medium |
| EC-36 | Analytics query timeout on large date range | Medium |
| EC-37 | GDPR bulk data export exceeds 1 GB | High |
| EC-38 | API gateway 200 with empty body | Medium |
| EC-39 | React DnD corrupts stage order in database | High |
| EC-40 | Job search returns stale results from ES index lag | Medium |

---

### Category 6 — Security and Compliance
**File:** `security-and-compliance.md`
**EC Range:** EC-41 through EC-48
**Description:** Covers GDPR erasure for hired employees, EEO data leaking into AI scoring, tenant isolation failures, medical PII on shared storage, S3 misconfiguration breach, background check ID mismatch, pay transparency multi-jurisdiction failures, and consent timestamping errors.

| EC | Title | Severity |
|----|-------|----------|
| EC-41 | GDPR erasure for already-hired employee | Critical |
| EC-42 | EEO data used in AI scoring model | Critical |
| EC-43 | Recruiter accesses other company's candidate pool | Critical |
| EC-44 | Resume contains medical PII on shared storage | High |
| EC-45 | Candidate PII exposed via S3 misconfiguration | Critical |
| EC-46 | Background check result sent for wrong candidate | Critical |
| EC-47 | Pay transparency failure for multi-jurisdiction remote jobs | High |
| EC-48 | Background check consent not timestamped correctly | High |

---

### Category 7 — Operations
**File:** `operations.md`
**EC Range:** EC-49 through EC-56
**Description:** Covers AI parser outages, email campaign spam classification, database slow queries during peak load, job board sync lag, Kafka consumer OOM, Elasticsearch cluster degradation, notification backlog, and RDS storage exhaustion.

| EC | Title | Severity |
|----|-------|----------|
| EC-49 | AI resume parser service completely down | High |
| EC-50 | Bulk email triggers spam classification | High |
| EC-51 | Database slow query during Monday morning surge | High |
| EC-52 | Job board sync falls behind > 2 hours | High |
| EC-53 | Kafka consumer OOM on large analytics batch | High |
| EC-54 | Elasticsearch cluster goes yellow during peak search | Critical |
| EC-55 | Kafka consumer lag exceeds 10,000 messages | High |
| EC-56 | RDS storage 95% full during resume import | Critical |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-01 | Platform Engineering | Initial release covering EC-01 through EC-56 |

---

*This documentation is owned by the Platform Engineering team. All engineers are expected to contribute updates after every post-mortem where a new or modified edge case is identified.*
