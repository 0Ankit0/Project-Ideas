# Edge Cases — Offer Management

## Overview

This document captures critical edge cases in the Offer Management domain, covering the full lifecycle of an employment offer from creation and multi-step approval through DocuSign e-signature, background checks, and final acceptance. The `offer-service` integrates with DocuSign, Checkr, and the ATS pipeline, creating multiple failure surfaces where correctness, timing, and external API reliability can diverge.

---

### EC-OM-01: DocuSign Envelope Delivery Failure

**Failure Mode:** A candidate's corporate or personal email server rejects the DocuSign envelope delivery email due to a spam filter classification, a full inbox, or a corporate email security policy that blocks links from DocuSign's sending domain (`docusign.net`). The DocuSign API returns a `201 Created` response when the envelope is created and reports the envelope status as `sent`. From the `offer-service` perspective, the offer transitions to `SENT` state successfully. However, the candidate never receives the email. The offer letter sits unseen in a DocuSign-managed envelope. If the candidate does not take action, the 5-day signing window configured in the `Offer` record's `signingDeadlineAt` field closes. The offer transitions to `EXPIRED` via the nightly `OfferExpiryJob` (a NestJS cron using `@nestjs/schedule`). The candidate remains unaware that they received and lost an offer. Recruiters may interpret the non-response as candidate disinterest and close the pipeline. In senior or highly competitive roles, this results in a lost placement and restart of the hiring process, at significant cost in recruiter time and delay in filling the role.

**Impact:** **High.** The business consequence is a failed hire despite a completed approval process. Time-to-fill metrics increase. Candidate experience is severely damaged — they may receive an automatic rejection email after the expiry job runs. If the candidate is actively employed, they may have already given notice to their current employer based on a verbal offer. Reputational damage to the hiring company and potential legal exposure if the verbal offer was made prior to the written offer.

**Detection:**
- DocuSign `envelope.recipient.delivery_failed` webhook event — monitor for delivery failure payloads at the `/webhooks/docusign` endpoint; fire a `PagerDuty` alert if the failure rate exceeds 2% in any 1-hour window
- CloudWatch custom metric: `OfferEnvelopeDeliveryFailureRate` (count of delivery failure webhooks / total envelopes sent) — alarm at > 1%
- Offer record stays in `SENT` state with zero `viewedAt` timestamp for > 48 hours — daily CloudWatch Metrics Insights query alerts recruiter via in-app notification
- Candidate support ticket or inbound email referencing "did not receive offer" — tracked in `customer-support` system, manually triaged

**Mitigation:**
1. On receipt of `envelope.recipient.delivery_failed` DocuSign webhook, immediately update the `Offer` record state to `DELIVERY_FAILED` and fire a `Kafka` event `offer.delivery.failed` consumed by `notification-service`.
2. `notification-service` sends an internal alert to the recruiter's email and in-app notification: "Offer envelope for [Candidate Name] could not be delivered. Action required."
3. Recruiter is presented with three resolution options in the UI: (a) resend to the same email, (b) update candidate email address and resend, (c) generate a PDF link to share via an alternative channel (LinkedIn InMail, phone follow-up with link).
4. Pause the 5-day expiry timer via a `signingDeadlineExtendedAt` flag on the `Offer` record for up to 48 hours to allow recruiter to intervene before expiry.
5. Attempt automated resend after 2 hours if the failure was a temporary SMTP error (retry classification based on DocuSign webhook `deliveryFailedReason` field).

**Recovery:**
1. Recruiter updates candidate email address in the candidate profile (with audit log entry) and triggers a re-envelope via the "Resend Offer" UI action, which calls `offer-service` `POST /offers/:id/resend`.
2. The offer-service voids the original DocuSign envelope (via `PUT /envelopes/:envelopeId` with `status: voided`), creates a new envelope with the updated email, resets `signingDeadlineAt` to 5 days from the new send time, and transitions the offer back to `SENT`.
3. Recruiter places a call or sends a LinkedIn message to inform the candidate to expect the new email and check their spam folder.

**Prevention:**
- Validate candidate email deliverability at application submission time using an email validation API (e.g., ZeroBounce or Hunter.io) — flag disposable, role-based (`hr@company.com`), or recently bounced addresses before the offer stage.
- Display a prominent warning in the offer creation UI if the candidate's email domain is known to block DocuSign (maintain a list of historically problematic domains in a `BlockedEmailDomainConfig` table, updated from Checkr/DocuSign delivery reports).
- Implement DocuSign embedded signing as a fallback: generate a signed URL that allows the candidate to sign directly in the platform without relying on email delivery.
- Configure DocuSign to send reminder emails at D+2 and D+4 of the signing window, increasing the probability that a delayed email is seen before expiry.

---

### EC-OM-02: Offer Approved and Sent Before Compensation Approval

**Failure Mode:** The offer approval workflow in `offer-service` is implemented as a sequential state machine requiring sign-off from three roles: `RECRUITER` → `HR_ADMIN` → `DIRECTOR_OF_HR`. Each approval is recorded in the `OfferApproval` table with a `userId`, `role`, `approvedAt` timestamp, and `status`. The transition from `PENDING_APPROVAL` to `APPROVED` requires all three approvals to be present. However, a race condition exists in the approval check logic: two concurrent API calls from the HR_ADMIN and DIRECTOR_OF_HR arrive within milliseconds of each other. Both read the `OfferApproval` table before either write is committed, both see that only 1 of 3 required approvals is recorded, both record their approval, and both increment an in-memory counter to 3. The Node.js event loop processes both completion checks concurrently (in separate async contexts), and both checks independently conclude that all approvals are satisfied. As a result, the `offer-service` transitions the offer to `APPROVED` twice in rapid succession, and the second transition triggers the DocuSign envelope creation and the state transition to `SENT`. The offer is sent to the candidate with compensation figures that the DIRECTOR_OF_HR had not yet reviewed — because the HR_ADMIN's approval triggered the send before the Director could review the final compensation amount (which was modified by the HR_ADMIN as part of their approval action).

**Impact:** **Critical.** The candidate receives an offer letter with an incorrect (non-authorised) salary figure. If the candidate signs the DocuSign envelope, the company may be legally bound to honor the incorrect salary under employment contract law in many jurisdictions. Correcting the error requires voiding the signed offer, explaining the error to the candidate, and re-issuing — damaging candidate trust and potentially losing the candidate to a competing offer. HR and legal review time is significant. In executive offers, the difference can be tens of thousands of dollars.

**Detection:**
- Database constraint: unique index on `(offerId, status='APPROVED')` in the `Offer` table prevents duplicate `APPROVED` records, surfacing a `UniqueConstraintViolationError` as a detectable signal
- CloudWatch Logs Insights alert: query for `OfferService: duplicate approval transition attempted` log entries — alarm if any occur
- DocuSign envelope creation audit log: if two envelopes are created for the same `offerId` within 60 seconds, fire a critical `PagerDuty` alert
- Monitor `offer.sent` Kafka events — deduplicate consumer in `notification-service` logs a warning if two `offer.sent` events arrive for the same `offerId` within 5 minutes

**Mitigation:**
1. Immediately upon detecting a duplicate approval transition (via `UniqueConstraintViolationError` or duplicate Kafka event), automatically void the second DocuSign envelope via `PUT /envelopes/:envelopeId` with `status: voided` before the candidate can open it.
2. Set the offer record to an `APPROVAL_ERROR` state and lock it from further transitions until manual review.
3. Alert the recruiter and HR Director via PagerDuty + email: "Offer for [Candidate Name] was sent prematurely due to an approval workflow error. The envelope has been voided. No action needed from the candidate."
4. If the candidate has already opened or signed the envelope before voiding is possible, escalate immediately to HR Legal.

**Recovery:**
1. Engineering team reviews the audit log to identify which compensation figure was authorised vs. which was sent. The DIRECTOR_OF_HR confirms the correct package.
2. HR manually re-initiates the full approval workflow with the correct compensation figures in a new `Offer` record, ensuring the Director explicitly approves the correct salary amount before any envelope is created.
3. Candidate is contacted by the recruiter (phone, not email) to explain that the previous offer contained an administrative error and a corrected offer will arrive within 24 hours. Offer the candidate an extended consideration window.
4. Legal counsel reviews the signed envelope (if applicable) to determine contractual exposure.

**Prevention:**
- Implement a distributed lock using **Redis `SET NX PX`** keyed on `offer:{offerId}:approval-lock` with a 5-second TTL. Every approval transition must acquire this lock before reading the approval count and making a state transition. Concurrent requests queue; the second read reflects the first write.
- Add a **database-level check constraint**: `CHECK (status != 'APPROVED' OR (SELECT COUNT(*) FROM offer_approvals WHERE offer_id = id AND status = 'APPROVED') = required_approvals_count)`.
- Separate the "final approval check" from the "send trigger" into distinct atomic operations with a mandatory 30-second delay between the last approval being recorded and the envelope creation — providing a human-review window for high-value offers (> $150K).
- Unit test the concurrent approval scenario using Jest's `Promise.all` + transaction isolation simulation; add this as a required passing test in the CI/CD pipeline before any `offer-service` deployment.

---

### EC-OM-03: Candidate Negotiates After Signing

**Failure Mode:** A candidate completes the DocuSign signing process for their offer letter at 2:47 PM on a Tuesday. The `offer-service` receives the `envelope.completed` DocuSign webhook at 2:48 PM and transitions the offer to `FULLY_EXECUTED`. The `offer.accepted` Kafka event is published, triggering a congratulations email, HRIS onboarding initiation, and IT equipment provisioning request. At 3:15 PM (27 minutes after signing), the candidate emails the recruiter directly (outside the platform) requesting a $15,000 salary increase, citing a competing offer they received that morning. The recruiter, seeing the offer as `FULLY_EXECUTED` in the ATS, is uncertain whether the offer can be legally rescinded. The recruiter attempts to use the "Rescind Offer" button in the UI but receives an error: `Cannot rescind an offer in FULLY_EXECUTED state`. The recruiter contacts the engineering team for a manual database update, which the engineering team is reluctant to perform without a formal process. Meanwhile, the HRIS system (Workday) has already created an employee record for the candidate with the original salary.

**Impact:** **High.** Legal complexity: a `FULLY_EXECUTED` DocuSign envelope constitutes a binding employment contract in most jurisdictions. Unilateral rescission by the employer may constitute breach of contract. The technical system correctly reflects legal reality, but the recruiter's attempt to bypass the state creates audit trail confusion. If not handled correctly, the company risks: (a) paying the negotiated salary without a proper amendment process, (b) the candidate joining at a salary that is not reflected in payroll/HRIS, or (c) the candidate withdrawing after the rescission attempt, triggering wrongful offer claims.

**Detection:**
- No automated detection possible for post-signing negotiation (it occurs off-platform via email). Detection relies on the recruiter manually logging the negotiation event in the candidate's ATS profile notes within 1 hour of receipt.
- Monitor for "rescind attempt on FULLY_EXECUTED" API errors: CloudWatch Logs Insights alert on `OfferService: rescind_blocked, reason=FULLY_EXECUTED` — high frequency of this event pattern warrants a process review.
- Recruiter inactivity signal: if an offer enters `FULLY_EXECUTED` but no onboarding task is created within 48 hours (via `integration-service` HRIS push), alert HR Admin.

**Mitigation:**
1. The `offer-service` UI must provide a clear in-app workflow for **post-signing negotiation** distinct from rescission: "Candidate requested amendment" → creates a new `OfferAmendment` record linked to the original `Offer`, entering `AMENDMENT_PENDING` state.
2. The `OfferAmendment` workflow routes through the same multi-step approval process (RECRUITER → HR_ADMIN → DIRECTOR_OF_HR) for the delta amount.
3. Upon approval, a **letter of amendment** (separate DocuSign envelope, short-form document referencing the original offer) is generated and sent to the candidate for counter-signature.
4. Downstream systems (HRIS, payroll) are updated only when the `OfferAmendment` reaches `AMENDMENT_FULLY_EXECUTED` state via the `offer.amendment.accepted` Kafka event.
5. If the amendment is rejected by approvers, the original offer stands at the original salary and the candidate is notified by the recruiter.

**Recovery:**
1. HR Legal team reviews the situation to determine if rescission is warranted or if an amendment process is the correct approach.
2. If a clean rescission is ultimately required (e.g., candidate is no longer acceptable), the recruiter creates a formal `RescissionRequest` record (new entity, requires DIRECTOR_OF_HR + Legal approval) which, upon approval, voids the original envelope in DocuSign and updates the offer to `RESCINDED` with a legal justification field.
3. HRIS integration-service publishes `offer.rescinded` event, triggering cancellation of the employee record in Workday and halting IT provisioning.
4. A legal notice is generated (via the offer-service letter template engine) and sent to the candidate informing them of the rescission with the stated reason.

**Prevention:**
- Clearly display in the offer creation UI: "Once a candidate signs this offer, it constitutes a binding agreement. Amendment requires a formal amendment letter process." — ensuring recruiters understand the legal weight before sending.
- Build the `OfferAmendment` workflow as a first-class feature in Phase 5 (not a workaround), so recruiters have a legitimate in-platform path that does not require database intervention.
- Add a mandatory 24-hour "counter-offer window" configuration option at the job level, allowing recruiters to specify that the offer remains in a `NEGOTIATION_OPEN` state for 24 hours after signing, during which amendments can be requested in-platform before the offer fully executes in downstream systems.
- Educate recruiters during platform onboarding that verbal or written commitments made outside the platform do not update the `offer-service` state and should always be logged as notes immediately.

---

### EC-OM-04: Offer Letter Template Contains Stale Compensation Data

**Failure Mode:** The offer letter generation process in `offer-service` works as follows: a recruiter creates an offer using the `POST /offers` endpoint, populating `annualSalary`, `bonusTarget`, `startDate`, and other fields. These are stored in the `offers` table. The recruiter then requests a PDF preview via `GET /offers/:id/preview`, which calls the Puppeteer-based PDF generator. The generator fetches the current `Offer` record, injects merge fields into an HTML template (`{{ANNUAL_SALARY}}`, `{{BONUS_TARGET}}`), and renders the PDF. The recruiter notices the salary is $95,000 but intended $97,500 (a last-minute adjustment). The recruiter returns to the offer editing screen, updates `annualSalary` to $97,500, and saves. Due to a caching bug in the offer-service (the `OfferRepository.findById` is cached in Redis for 2 minutes after the first PDF preview fetch), the next call to the PDF generator — triggered when the recruiter clicks "Send Offer" — still retrieves the cached `Offer` record with `annualSalary = 95000`. The PDF is generated with the old salary. The DocuSign envelope is created with the stale PDF. The candidate receives and signs an offer for $95,000. The recruiter only discovers the error when reviewing the `FULLY_EXECUTED` envelope PDF days later.

**Impact:** **High.** The candidate has a signed offer at $95,000 when $97,500 was intended and verbally communicated. The company must either honour $95,000 (financial disadvantage to candidate, potential candidate attrition if they discover the discrepancy), initiate an amendment process (time-consuming, trust-damaging), or rescind the offer (highest risk). Additionally, if the HRIS system is populated with $95,000, payroll will be incorrect from day one of employment, triggering a payroll correction process with tax implications.

**Detection:**
- Add a **PDF generation audit hash**: after generating the offer PDF, compute a SHA-256 hash of the merged data fields and store it alongside the `envelopeId` in the `OfferEnvelope` table. On envelope creation, re-verify the hash against the current database state — if they diverge, block the send and raise an alert.
- CloudWatch custom metric: `OfferSalaryMismatch` — triggered when the salary in the generated PDF (extracted via regex from PDF text after generation) does not match `offers.annualSalary`. Alert if > 0 mismatches per day.
- Recruiter confirmation step before send: a "Review and Confirm" modal shows the key offer terms (salary, bonus, start date) pulled directly from the database (not from cache) with a mandatory checkbox: "I confirm these details are correct."

**Mitigation:**
1. On detection of a salary mismatch (via hash verification or recruiter complaint), immediately void the DocuSign envelope via the DocuSign API before the candidate views it.
2. Regenerate the offer PDF from the current (non-cached) database record with a forced cache bypass (`BYPASS_CACHE=true` flag on the repository call).
3. Create a new DocuSign envelope with the corrected PDF and resend to the candidate.
4. Notify the recruiter and HR Admin via in-app alert that the original envelope was voided due to a data issue and the corrected offer has been resent.

**Recovery:**
1. If the candidate has already viewed or signed the stale PDF before voiding was possible, initiate the `OfferAmendment` workflow (as defined in EC-OM-03) to issue a corrective amendment.
2. Purge the specific Redis cache key for the affected `offerId` and audit the cache invalidation logic to identify why the update did not invalidate the cache.
3. Review all offers sent in the last 24 hours to check if the caching bug affected other offers (cross-check PDF hash against current database records for all `SENT` offers).

**Prevention:**
- **Never cache `Offer` records that are in a mutable state** (`DRAFT`, `PENDING_APPROVAL`). Redis caching should only be applied to `APPROVED` and later states, where the data should not change. The cache key must be invalidated on any `UPDATE` to the `offers` table row using Prisma's `$transaction` with a Redis `DEL` within the same atomic scope.
- Implement a **two-phase offer send process**: (1) "Lock Offer" action that freezes the offer record (sets `lockedAt` timestamp) and generates the PDF for final review, (2) "Confirm and Send" action that uses the locked data to create the DocuSign envelope. Once locked, any further edits require an explicit "Unlock and Re-draft" action. This eliminates the race condition between edit and send.
- Add a server-side validation in the `sendOffer` handler that queries the database with `SELECT ... FOR SHARE` to get the current salary and compares it with the salary in the PDF metadata before creating the DocuSign envelope.
- Implement PDF text extraction in CI: render the offer template with known test values and verify the extracted PDF text matches expected values — catching merge field rendering bugs before production deployment.

---

### EC-OM-05: Multiple Active Offers for the Same Candidate

**Failure Mode:** A candidate named Jordan Chen applies independently to two open positions at the same company: "Senior Backend Engineer" (Job ID 1042, managed by Recruiter Alice) and "Staff Engineer" (Job ID 1078, managed by Recruiter Bob). Both pipelines progress independently without cross-pipeline visibility. Recruiter Alice's pipeline for Job 1042 reaches the offer stage first; Alice creates and sends an offer for $145,000. Three days later, Recruiter Bob's pipeline for Job 1078 also reaches the offer stage. Bob is unaware that Jordan already has an active offer. Bob creates and sends a second offer for $162,000. Jordan now has two active DocuSign envelopes from the same company. Jordan signs the $162,000 offer (Job 1078) and declines the $145,000 offer (Job 1042) by simply not signing it. However, Alice's pipeline auto-expires the $145,000 offer after 5 days, and Alice closes Job 1042 assuming Jordan was not interested. The `application-service` records two applications for Jordan: one `HIRED` (Job 1078) and one `EXPIRED` (Job 1042). The HRIS receives a `new.hire` event for Job 1078 with a $162,000 salary. Alice later discovers Jordan's name in the Job 1078 onboarding list and is confused about why her candidate was "poached" internally, creating team friction.

**Impact:** **Medium.** No legal risk if both offers were legitimately extended and the candidate accepted one. However: internal team conflict between recruiters, potential salary equity issues if the two offers had different compensation packages that were not reviewed holistically by HR, double onboarding costs, and a confusing application history that makes analytics (source attribution, time-to-hire) unreliable. If the candidate signed both offers before either could be voided, there is a legal complexity about which offer constitutes the employment contract.

**Detection:**
- Database constraint: enforce a soft uniqueness check at offer creation time — `SELECT COUNT(*) FROM offers WHERE candidate_id = ? AND status IN ('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'SENT', 'SIGNED')` — alert if > 0 and prevent creation without HR Admin override.
- CloudWatch metric: `MultipleActiveOffersPerCandidate` count — alert if > 0 per day.
- In the offer creation UI, display a banner: "⚠️ This candidate has an active offer for [Job Title] from [Recruiter Name]. Proceed with awareness." — shown whenever a recruiter creates an offer for a candidate with an existing active offer.

**Mitigation:**
1. When a second offer is created for a candidate with an existing active offer, require an explicit HR Admin confirmation with a justification field (e.g., "Internal transfer, different team, compensation reviewed holistically").
2. Automatically notify both recruiters and their HR Admin when the second offer is created: "Candidate Jordan Chen has active offers for two positions. HR review required."
3. Create a cross-pipeline coordination record in the `offer-service` (`OfferConflict` table) that HR Admin must resolve before either offer can proceed to `SENT` state.
4. If both offers have already been sent (as in the failure scenario), trigger a `CONFLICT_REVIEW` state on the earlier offer, pausing its expiry clock until HR resolves the conflict.

**Recovery:**
1. HR Admin reviews both offers, determines the preferred position and compensation package, and officially approves one offer while withdrawing the other via the `OfferConflict` resolution UI.
2. The withdrawn offer is formally voided in DocuSign (even if unsigned) with a polite candidate-facing message explaining the company wants to focus on the better-fit role.
3. Analytics records are updated with a `conflict_resolved` flag to exclude the withdrawn offer from standard funnel metrics.
4. A process retrospective is conducted between the two recruiting teams to improve cross-pipeline candidate visibility.

**Prevention:**
- Build a **candidate cross-pipeline view** visible to all recruiters at the same company: "Jordan Chen is currently active in 3 pipelines." This is a first-class feature in the ATS candidate profile page.
- Enforce a company-wide configuration: `allow_concurrent_offers` (default: `false`) — when disabled, the system blocks creation of a second active offer for the same candidate and routes the recruiter to a collaboration workflow with the other pipeline's recruiter.
- HR Admin role receives a weekly "Multi-pipeline Candidates" digest email listing all candidates active in more than one open pipeline, enabling proactive coordination before the offer stage.
- Add a `candidate_offer_lock` distributed lock in Redis: when an offer enters `APPROVED` state, a Redis key `candidate:{candidateId}:active-offer` is set with a TTL equal to the signing deadline, blocking other offers from entering `APPROVED` for the same candidate without an explicit override.

---

### EC-OM-06: Background Check Returns 'Consider' Status

**Failure Mode:** A candidate named Marcus Williams signs an offer letter for a Senior Financial Analyst position. The offer enters `FULLY_EXECUTED` state at 9:15 AM on Monday. The `offer.accepted` Kafka event triggers the `integration-service` to initiate a Checkr background check. At 3:40 PM on Wednesday, Checkr returns a webhook with `status: "consider"` (not `"clear"` or `"adverse_action"`) for the report. The `CONSIDER` status means Checkr has found items in the candidate's history that require human review by the employer before a final decision — in this case, a 7-year-old misdemeanour that may or may not be relevant to a financial analyst role. Critically, the offer is already `FULLY_EXECUTED`. The candidate has given notice to their current employer (start date is in 3 weeks). The `offer-service` state machine has no defined transition from `FULLY_EXECUTED` for a background check `CONSIDER` result — the `FULLY_EXECUTED` state was designed as a terminal state. The recruiter has no in-platform mechanism to pause onboarding or flag the hire for legal review.

**Impact:** **High.** Employment law in most US states requires that an adverse action process (under FCRA) be followed before rescinding an offer based on a background check result. The `CONSIDER` status creates a mandatory review period during which the employer must: (1) provide the candidate with a copy of the Checkr report, (2) wait at least 5 business days for a response, (3) make a final decision. Without a platform-supported workflow for this process, the company is at risk of FCRA non-compliance. In parallel, IT provisioning and HRIS onboarding that started when the offer was accepted must be paused, but there is no mechanism in the current `offer-service` to signal downstream services to pause.

**Detection:**
- `integration-service` Checkr webhook handler: on receipt of `status: "consider"` payload, publish a `background-check.consider.received` Kafka event immediately. This event should be consumed by `offer-service`, `notification-service`, and `analytics-service`.
- CloudWatch alarm: monitor the `background-check.consider.received` event count — any occurrence triggers a `PagerDuty` **P2** alert to the HR Admin and Legal team within 5 minutes of webhook receipt.
- `offer-service` monitor: daily scan of all `FULLY_EXECUTED` offers where the associated background check has not reached `CLEAR` status within 3 business days — alert HR Admin.

**Mitigation:**
1. Add a `BACKGROUND_CHECK_HOLD` sub-state to the `offer-service` state machine that can be applied to offers in `FULLY_EXECUTED` state without revoking the offer. This state flags the offer for HR review without rescinding it.
2. On receipt of `background-check.consider.received` event, `offer-service` transitions the offer to `FULLY_EXECUTED/BACKGROUND_CHECK_HOLD` (stored as a separate `offerHold` record linked to the `Offer`, preserving the terminal `FULLY_EXECUTED` state for the core offer while capturing the hold context).
3. Publish `onboarding.pause.requested` Kafka event consumed by `integration-service`, which sends pause signals to HRIS (Workday) and IT provisioning systems.
4. Generate FCRA-mandated pre-adverse-action notice (PDF) via offer-service template engine and queue it for delivery to the candidate via DocuSign within 2 business days of the `CONSIDER` result.
5. HR Legal team receives an in-platform task: "Background Check Review Required — Marcus Williams — Due [5 business days from today]."

**Recovery:**
1. If HR Legal reviews and determines the `CONSIDER` item is not disqualifying for the role, they mark the review as "Approved to Proceed" in the platform. The hold is lifted, `onboarding.resume.requested` is published, and all downstream systems (HRIS, IT provisioning) resume.
2. If HR Legal determines the `CONSIDER` item requires an adverse action, they initiate the FCRA adverse action process (individualised assessment, 5-day waiting period, final decision). If the decision is to rescind, the offer is moved to `RESCINDED` with `reason: BACKGROUND_CHECK_ADVERSE_ACTION` and the HRIS employee record is cancelled.
3. Candidate communications throughout are managed by HR Legal (not automated) to ensure FCRA compliance.

**Prevention:**
- Design the offer state machine from the beginning to include **post-execution hold states**: `FULLY_EXECUTED` is not a true terminal state — it should support `FULLY_EXECUTED → ONBOARDING_HOLD → ONBOARDING_ACTIVE` or `FULLY_EXECUTED → RESCINDED` transitions.
- Establish a company policy (encoded in `offer-service` configuration) that background checks are initiated **before** the offer is sent (`APPROVED` state), not after. For time-sensitive hires, a conditional offer letter can be used that explicitly states it is contingent on a satisfactory background check, handled via a `CONDITIONAL_OFFER` state variant.
- Build FCRA pre-adverse-action and adverse-action notice templates directly into the `offer-service` template engine during Phase 5, ensuring legal compliance is built-in rather than bolted on.
- Integrate Checkr's **Assess** product to automate adjudication rules (e.g., "financial crimes disqualify for financial analyst roles") to reduce manual review burden and ensure consistent application of standards.

---

### EC-OM-07: Offer Sent to Wrong Candidate Email

**Failure Mode:** A recruiter named Sarah is processing offers for three candidates in the final stages simultaneously. In the offer management UI, she selects what she believes is the profile for "Alex Patel (Senior DevOps Engineer)" but due to a UI autocomplete bug in the candidate dropdown, the dropdown populates with "Alexandra Patel (Junior QA Engineer)" — a different person whose name closely matches. The names appear identical in the truncated dropdown list. Sarah completes the offer details ($135,000 salary, start date, benefits summary) and clicks "Generate and Send Offer". The offer-service generates a DocuSign envelope and sends it to Alexandra Patel's email (alex.patel.qa@email.com) instead of Alex Patel (a.patel.devops@gmail.com). Alexandra Patel receives an offer letter with full compensation details — $135,000 salary, equity vesting schedule, detailed benefits information — for a role she did not apply to, and for compensation that is significantly different from her own active offer ($72,000 for the QA role). Alexandra is confused and emails the company asking for clarification. Meanwhile, Alex Patel has not received his offer. The offer has been sent to the wrong person, exposing confidential compensation data for a senior role to a junior candidate.

**Impact:** **Critical.** Three simultaneous harms: (1) **Privacy breach** — confidential compensation data for a senior-level offer is disclosed to an unintended recipient who is also a current candidate. (2) **Candidate experience failure** — the actual intended recipient has not received their offer, causing delay and potentially causing Alex Patel to accept a competing offer while waiting. (3) **Internal equity exposure** — Alexandra Patel now knows the company is offering the DevOps role at $135,000 and her own offer is at $72,000. This creates internal equity tension, potential NLRA considerations (right to discuss wages), and a difficult conversation for HR. DocuSign will show the envelope as "sent" but the wrong person has received it.

**Detection:**
- **Pre-send confirmation screen**: before any offer envelope is created, display a mandatory confirmation dialog showing candidate full name, email address, role applied to, and a photo/avatar of the selected candidate. Require the recruiter to type the candidate's full name in a confirmation text field before proceeding.
- Automated mismatch detection: validate that the `candidateId` on the offer record has an active application for the `jobId` on the offer record — if no active application exists, block the send with error `CANDIDATE_JOB_MISMATCH` and require HR Admin override.
- Monitor DocuSign webhook: `envelope.sent` events where `recipient_email` does not match the email on the `Application` record for the associated `applicationId` — alert immediately.
- Alexandra Patel's inbound support ticket / confused email flagged in customer support system within hours of the incorrect send.

**Mitigation:**
1. Immediately void the incorrectly addressed DocuSign envelope via the DocuSign API (`status: voided`) to prevent Alexandra Patel from signing the wrong offer.
2. Send Alexandra Patel an immediate apology email acknowledging the error, stating clearly that the offer was sent in error, the envelope has been voided, and she should disregard it. Do not provide any information about what the correct compensation was.
3. Contact Alexandra Patel's recruiter to inform them of the accidental disclosure so they can proactively manage any compensation conversation with Alexandra.
4. Correct the offer record to reference the correct candidate (Alex Patel) and resend the offer envelope to the correct email address.
5. Notify Alex Patel with an apology for the delay: "We apologise for the slight delay in sending your formal offer letter. You will receive it within the next 30 minutes."

**Recovery:**
1. Conduct a privacy incident review per the company's data breach response policy. Depending on jurisdiction (GDPR, CCPA), a disclosure of salary information to an unintended recipient may constitute a personal data breach requiring regulatory notification within 72 hours.
2. HR legal reviews whether the inadvertent salary disclosure to Alexandra Patel creates any legal obligation (e.g., pay equity discussion rights under NLRA).
3. Log the incident in the `SecurityIncident` table with full details, resolution steps, and a link to the engineering post-mortem.
4. The dropdown autocomplete bug is escalated as a **P1 bug** to the frontend engineering team with a hotfix deployment prioritised within 24 hours.

**Prevention:**
- **Redesign the candidate selector in the offer UI**: replace the autocomplete text field with a modal search that shows full name, email, role applied to, and avatar image simultaneously. Require the recruiter to explicitly click "Confirm this is the correct candidate" after reviewing all three identifiers.
- Add a server-side validation guard in the `POST /offers` handler: `candidateId` must have an active (non-rejected, non-withdrawn) application for the specified `jobId`. Reject with `400 CANDIDATE_JOB_MISMATCH` if not.
- Implement an **offer send delay** (configurable, default 10 minutes) during which the offer is in `PENDING_SEND` state. The recruiter receives an "Offer will be sent in 10 minutes — click to cancel" notification, providing a human cancellation window. Enterprise email services (Google Workspace "Undo Send") use this pattern effectively.
- Introduce UI-level fuzzy name collision warnings: if the autocomplete finds two candidates whose names have edit-distance ≤ 3 characters, display a warning: "Multiple candidates with similar names exist. Please verify you have selected the correct person."
- Conduct quarterly privacy training for all users of the offer management system, specifically covering the consequences of sending offers to incorrect recipients and the correct escalation procedure.
