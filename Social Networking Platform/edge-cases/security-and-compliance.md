# Security and Compliance — Edge Cases

## Overview

Compliance failures carry legal, financial, and reputational consequences that technical debt
does not. GDPR fines can reach 4% of global annual revenue; CSAM reporting failures can result
in criminal liability; improper cross-border data transfers can trigger regulatory action in
multiple jurisdictions simultaneously. This file documents the edge cases most likely to
produce compliance incidents and the engineering controls required to prevent them.

---

## Failure Modes

| Failure Mode | Impact | Detection | Mitigation | Recovery | Prevention |
|---|---|---|---|---|---|
| GDPR deletion request not fully honored | Residual PII in backup snapshots, analytics aggregates, or third-party data processors; regulatory fine risk | Deletion audit trail gap; DPA (Data Protection Authority) complaint | Multi-system deletion orchestrator with explicit status tracking per data store; backup tombstoning | Remediate missed stores; document gap in DPA correspondence | Comprehensive data-map maintained in real time; deletion test suite covering all data stores |
| Data export (DSAR) containing another user's data | PII cross-contamination; privacy violation; potential breach notification obligation | Quality assurance on export samples; user complaints about incorrect data | User-scoped export query with strict identity-boundary enforcement; export review checklist | Retract incorrect export; issue breach notification if required; re-run corrected export | Export pipeline integration tests with multi-user isolation assertions |
| Consent management rollback exposes unconsented data processing | Users who withdrew consent continue to have data processed under a prior lawful basis | Consent version audit; processing-activity log vs. consent-state mismatch | Consent state propagated synchronously to all processing systems; processing gated on consent check | Halt processing for affected users; re-obtain consent or cease processing | Consent event bus with guaranteed delivery; processing systems subscribe and enforce locally |
| Cross-border data transfer to non-adequate country without safeguards | GDPR Chapter V violation; data transfer enjoined by DPA; service disruption for EU users | Legal team transfer audit; DPA inquiry | Standard Contractual Clauses (SCCs) in place for all third-country transfers; data residency enforcement | Halt transfer; re-paper contracts with DPAs; implement data residency if SCC insufficient | Data transfer impact assessment (DTIA) for every new third-country vendor; legal review gate |
| CSAM reporting pipeline failure | CyberTipline report not submitted within required window; potential criminal liability under PROTECT Our Children Act | Alert on CSAM detection event without corresponding CyberTipline submission within 24 hours | Dedicated CSAM reporting service with retry and dead-letter queue; legal-hold preservation | Submit overdue report; document delay; notify legal team | End-to-end test of CSAM reporting pipeline monthly; SLA monitoring with automated escalation |
| Age-verification bypass enabling minor access to adult content | Minor exposed to age-gated material; COPPA/KOSA violation | Age-verification conversion drop; account anomalies in age-gated cohort | Multi-signal age inference (declared age + behavioral + device signals); re-verification on suspicious signal | Remove minor from age-gated content; retroactive content restriction | Age-estimation model in onboarding; parental consent flow for under-13 accounts |
| Right-to-erasure conflict with legal hold obligation | Deletion request received for account under active legal hold; cannot comply with both obligations | Legal hold flag in account management system; deletion request against held account | Block deletion for accounts under legal hold; notify requestor of hold obligation; resume deletion when hold lifted | Process deletion immediately upon hold release; document timeline for DPA response | Legal hold management system integrated with deletion pipeline; automated conflict detection |
| Privacy policy version mismatch in cached responses | Users served stale privacy policy version from CDN after update; consent obtained under outdated policy | Privacy policy version header mismatch detection; CDN cache audit | Cache-Control: no-store for privacy policy page; version header validation in consent flow | Purge CDN cache; re-obtain consent if policy material changed | Privacy policy change triggers automated CDN cache purge; version parameter in consent record |

---

## Detailed Scenarios

### Scenario 1: Incomplete GDPR Deletion — Backup Snapshot Gap

**Trigger**: A user submits a GDPR Article 17 erasure request. The deletion orchestrator
successfully removes the user's record from the primary database, object storage, search index,
and analytics pipeline. However, daily backup snapshots taken before the deletion are retained
for 30 days without tombstone markers. A DPA audit 3 weeks later discovers the user's PII in
a restored backup test environment.

**Legal Context**: Recital 65 of the GDPR allows retention in backups where deletion is
"disproportionately difficult," but requires isolation of backups containing the data and
prohibition of further processing of that data. This exception is narrow and requires documentation.

**Mitigation**:
1. **Tombstone records in backups**: Deletion events write a tombstone entry (user ID + deletion
   timestamp + scope) to a deletion-log table that is included in every backup. Restore pipelines
   apply tombstones before making backup data accessible.
2. **Backup isolation**: Backups containing PII for a deletion-request user are tagged and
   restricted; they cannot be used for dev/test environments.
3. **30-day backup purge**: Backup retention policy aligns with erasure SLA; snapshots older
   than 30 days are purged, and users are informed of this timeline in the deletion confirmation.
4. **Audit trail**: Every step in the deletion orchestrator writes a signed audit record to an
   immutable log (WORM storage); completeness can be demonstrated to DPAs.

**Recovery**: Isolate backups containing the user's data; document isolation in DPA response;
accelerate backup purge for affected snapshots.

**Prevention**: Deletion integration tests restore a backup and verify tombstone enforcement;
DPA audit preparedness reviewed quarterly by legal and engineering jointly.

---

### Scenario 2: Consent Withdrawal Propagation Failure

**Trigger**: A user withdraws marketing consent via the consent management platform (CMP) at
T+0. The CMP emits a consent-change event to an event bus. Due to a Kafka consumer lag spike,
the marketing email service does not receive the event for 47 minutes. During that window, a
scheduled marketing email campaign fires and sends 3 emails to the user who withdrew consent.

**Legal Context**: GDPR Article 7(3) requires that withdrawal of consent be as easy as giving
it and that processing must cease "without delay." A 47-minute delay with active sends may
constitute a violation, particularly if the user complains to a DPA.

**Detection**:
- Consent-event delivery latency alert fires at 5-minute lag threshold.
- Post-send audit: cross-reference email send log against consent state at send time; flag
  sends to users whose consent was withdrawn before the send timestamp.

**Mitigation**:
1. **Pre-send consent gate**: Email delivery service performs a real-time consent lookup
   immediately before each send, not only at campaign scheduling time.
2. **Event bus priority**: Consent-change events are published to a high-priority topic with
   dedicated consumers and no shared consumer-lag risk.
3. **Guaranteed delivery**: Consent events use at-least-once delivery with idempotency keys;
   consumer re-processes events on retry without double-applying state changes.

**Recovery**:
- Immediately send an apology email with unsubscribe confirmation.
- Document the incident timeline for potential DPA response.
- Compensate user if requested; review for breach-notification obligation under Art. 33.

**Prevention**: Architectural rule: no marketing send without a synchronous pre-send consent
check against the canonical consent store, regardless of scheduled campaign state.

---

### Scenario 3: Age-Verification Bypass — Minor Access to Adult Content

**Trigger**: A 14-year-old creates an account by declaring age as 18. The platform enables
access to age-gated content (18+ communities, adult creator content). The user's behavioral
signals (device usage patterns, engagement with teen-oriented content) diverge from their
declared age after 2 weeks of activity.

**Legal Context**: COPPA applies to under-13s in the US; KOSA (Kids Online Safety Act, if
enacted) and similar laws in UK/EU impose age-assurance obligations for platforms.

**Detection**:
- Age-signal consistency score: ML model trained on behavioral, device, and engagement signals
  to estimate age bracket. Score diverging >2 standard deviations from declared age triggers review.
- Engagement pattern anomaly: age-gated content interaction ratio inconsistent with declared age.

**Mitigation**:
1. **Multi-signal age verification**: Declared age + payment method age validation + behavioral
   age-estimation model. Discrepancies trigger step-up verification.
2. **Age-estimation model in onboarding**: Run at signup; if model estimates <16, require
   additional verification before proceeding to full account creation.
3. **Parental consent flow**: For users where under-13 is suspected or declared, initiate
   COPPA-compliant parental consent process before account activation.
4. **Age-gated content cooldown**: New accounts cannot access age-gated content for 14 days;
   this window allows behavioral age signals to accumulate.

**Recovery**: Restrict access to age-gated content for flagged accounts; send age-verification
challenge; retain access if verification passes, else permanently restrict.

**Prevention**: Annual third-party audit of age-assurance measures; age-verification
requirements reviewed whenever new age-gated features are launched.
