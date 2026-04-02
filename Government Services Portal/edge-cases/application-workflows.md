# Edge Cases: Application Workflows — Government Services Portal

## Overview

This document covers **10 edge cases** in the Application Workflows domain. Application workflows are the core function of the Government Services Portal — they represent the end-to-end journey of a citizen submitting a request (birth certificate, trade license, building permit, etc.) through review, approval, and certificate issuance. Failures in this domain directly obstruct entitlement delivery, create SLA breaches, and may have legal consequences (e.g., missed court deadlines, expired permit applications). The workflows involve citizens, field officers, department heads, and multi-department coordination, making them inherently complex and failure-prone.

---

## EC-WORKFLOW-001: Partial Form Submission Loss

**Failure Mode:**
A citizen is filling a long, multi-section application form (e.g., a permanent resident certificate application with 12 sections requiring personal details, address history, family details, and 8 document attachments). The browser crashes, the mobile goes offline, or the user accidentally closes the tab at section 8 before the 60-second auto-save timer fires. The auto-save has not yet persisted section 8's data. The citizen reopens the portal and finds their draft saved only through section 7, losing all data entered in section 8.

**Impact:**
- **Severity: High**
- Citizens lose data they have spent significant time entering. Re-entering income details, family member information, or property survey numbers can take 20–30 minutes per lost section.
- Citizens with low digital literacy may not understand why data was lost and may incorrectly believe the form itself is broken, abandoning the application entirely.
- Repeated data loss on the same form triggers support calls and public complaints, damaging the portal's reputation as a reliable service delivery platform.
- For citizens using shared devices (common in rural areas), session loss is permanent — the next user of the device may have cleared the browser session before the citizen could return.

**Detection:**
- **Client-Side Unload Detection:** The Next.js frontend uses the `beforeunload` and `visibilitychange` browser events to trigger a synchronous (or beacon-based) save attempt when the page is being closed or hidden.
- **Auto-Save Gap Metric:** The frontend publishes a metric `AutoSave_Gap_Seconds` — the time since the last successful server-side save. A CloudWatch alarm fires if this exceeds 120 seconds for any active session.
- **Draft Inconsistency Check:** A background Celery task runs every 10 minutes, comparing server-side draft province with expected section completion counts. Drafts with detected province gaps (e.g., section 8 form data missing but section 9 started) generate a `DRAFT_STATE_INCONSISTENCY` log event.
- **Abandoned Draft Tracking:** Drafts that have been inactive for more than 30 minutes but are in an incomplete province are flagged as `POTENTIALLY_ABANDONED` and contribute to an analytics dashboard for product improvement.

**Mitigation/Recovery:**
1. **Aggressive Auto-Save (Debounced):** Auto-save fires on every field change after a 5-second debounce (not just every 60 seconds). The `PATCH /api/v1/applications/{draft_id}/draft/` endpoint accepts partial section data, storing it in JSONB format in PostgreSQL. The save is acknowledged with a visual "Saving..." → "Saved" indicator.
2. **Beacon-Based Emergency Save:** On `beforeunload` and `visibilitychange` (tab switch, browser minimize), the frontend fires a `navigator.sendBeacon()` call to `POST /api/v1/applications/{draft_id}/beacon-save/` with the current form province serialized as JSON. Beacon-based requests are not canceled when the page unloads, unlike XHR/fetch.
3. **localStorage Redundancy:** In addition to server-side saves, the form province is stored in `localStorage` under a key `draft_{draft_id}`. On returning to the form page, the frontend compares the localStorage timestamp with the server draft timestamp and uses whichever is more recent.
4. **Draft Recovery Prompt:** When a citizen opens a form that has an incomplete draft, the portal shows: "You have an unsaved draft from [timestamp]. Would you like to resume where you left off?" with a preview of the last saved section.
5. **Section-Level Save Checkpoints:** Each form section has an explicit "Save Section" button in addition to the auto-save. Completing a section and clicking this button triggers an immediate server save and updates a `sections_completed` bitmask on the draft record.

**Prevention:**
- **Server-Side Draft Architecture:** All form province lives on the server (PostgreSQL JSONB). The browser is only a rendering layer, not the source of truth. This architectural choice prevents any browser crash from causing permanent data loss.
- **Progressive Form Design:** Forms are split into logical sections of 5–7 fields each, with a section saved before advancing to the next. Citizens cannot advance to section N+1 without section N being saved.
- **Connection Status Banner:** The frontend monitors network connectivity using the `online`/`offline` browser events. During offline periods, a banner reads: "You are offline. Changes are queued and will be saved when connection is restored."
- **Session Recovery Testing:** Automated E2E tests (Playwright) simulate mid-form browser crashes and validate that draft recovery works correctly across all major form types.

---

## EC-WORKFLOW-002: Document Upload Timeout for Large Files

**Failure Mode:**
A citizen is required to upload a property survey document that is a 50MB scanned PDF (high-resolution scan of a large plot map). The portal provides an S3 pre-signed URL for direct browser-to-S3 upload. The citizen's home broadband connection is a 2 Mbps BSNL line. At 2 Mbps, a 50MB file takes approximately 200 seconds to upload. The pre-signed URL has a 15-minute TTL, so the upload should succeed. However, the Django API sets a 30-second proxy timeout on the upload endpoint (left over from a misconfiguration), causing the request to timeout at the API gateway level. The citizen's browser shows a spinner for 30 seconds, then a generic network error. The partially uploaded file is in S3 as an incomplete multipart upload. The citizen believes the upload succeeded (the error message is not clear) or is confused about what happened.

**Impact:**
- **Severity: High**
- Citizens with slow connections (rural areas, mobile hotspots) are systematically blocked from uploading required documents, even when their connection is adequate.
- Incomplete multipart uploads accumulate in S3, incurring storage costs until cleaned up by lifecycle policy.
- If the citizen retries and the portal creates a new S3 key for each attempt, multiple incomplete uploads accumulate and none complete.
- Applications cannot progress without the required document — the citizen is stuck at the upload step indefinitely without understanding why.
- Citizens who complete all other sections and then fail at document upload face maximum frustration as they have invested the most time.

**Detection:**
- **S3 Incomplete Multipart Upload Alert:** An S3 lifecycle rule generates a CloudWatch metric when incomplete multipart uploads older than 24 hours exist in the document bucket. An alarm `S3_IncompleteMPU_Old` fires when count > 0.
- **Upload Failure Rate Metric:** The frontend publishes `DocumentUpload_Failure_Rate` per document type and file size bucket. A spike in failure rate for files >20MB indicates a timeout configuration issue.
- **Browser-Side Error Tracking:** Frontend error boundary captures upload failures with file size, upload duration, and error type. Sentry (or equivalent) reports aggregate upload failure rates.
- **API Gateway Timeout Log:** CloudWatch Logs captures all requests that are terminated by the ALB due to timeout. Log Insights query identifies upload endpoint timeouts.

**Mitigation/Recovery:**
1. **Direct S3 Multipart Upload (No API Proxy):** Document uploads use direct browser-to-S3 pre-signed multipart upload, completely bypassing the Django API server for the actual file transfer. The API only provides pre-signed URLs and receives the completion notification. This removes any server-side timeout from the upload path.
2. **Chunked Multipart Upload:** For files >5MB, the frontend uses S3 multipart upload API, splitting the file into 5MB chunks. Each chunk is uploaded sequentially with retry on failure (3 retries per chunk with exponential backoff). Partial chunk uploads are resumable if the browser refreshes.
3. **Upload Progress UI:** A progress bar shows upload progress in real time (using `XHR`'s `progress` event). Each chunk completion updates the progress. The citizen can clearly see "Upload in progress: 14 of 50 MB uploaded."
4. **Pre-Signed URL TTL Alignment:** Pre-signed URLs for uploads are generated with a 60-minute TTL (configurable via `S3_PRESIGNED_URL_UPLOAD_TTL`), generous enough for very slow connections. For files >100MB (exceptional case), a 4-hour TTL is used.
5. **Post-Upload Verification:** After the frontend reports upload completion, a Lambda function triggered by the S3 `s3:ObjectCreated:*` event verifies the file integrity (SHA-256 checksum comparison), records the final S3 key in the application draft, and updates the document status from `UPLOADING` to `UPLOADED_PENDING_SCAN`.

**Prevention:**
- **File Size Validation:** Before generating a pre-signed URL, the API checks the declared file size. Files exceeding 100MB are rejected with a clear message: "The maximum file size is 100MB. Please compress your document." Files between 20–100MB are accepted with a warning about expected upload time.
- **File Format Validation:** Accept lists restrict uploads to PDF, JPEG, PNG, and TIFF. The frontend validates MIME type and the backend re-validates on the S3 event notification.
- **Timeout Configuration Audit:** All ALB, API Gateway, Nginx/Gunicorn, and Django REST Framework timeout settings are documented in `infrastructure/timeouts.md` and reviewed in every infrastructure change review.
- **S3 Lifecycle Policy for Incomplete MPUs:** An S3 lifecycle rule automatically aborts incomplete multipart uploads after 7 days, preventing storage cost accumulation.

---

## EC-WORKFLOW-003: Simultaneous Application Edit Conflict

**Failure Mode:**
A citizen submits a trade license application. It enters the `UNDER_REVIEW` province and is assigned to Field Officer Priya Sharma. Officer Priya opens the application in her review dashboard and begins typing review notes. At the same time, the citizen realizes they entered the wrong business address and opens the application to edit it (the portal allows edits to `UNDER_REVIEW` applications for minor corrections, with officer notification). Both the officer and the citizen are now editing the same application record simultaneously. Officer Priya submits her review notes (UPDATE sets `officer_notes = "..."`). Then the citizen submits their address correction (UPDATE sets `business_address = "..."` but uses the old record province — which does not include the officer's notes). The citizen's update overwrites the officer's notes with an empty string, and the business address is updated. The officer's review work is silently lost.

**Impact:**
- **Severity: High**
- Officer's review notes are silently overwritten, causing the officer to re-read the application and re-enter notes — wasting review time and potentially causing inconsistent review decisions.
- If the officer has marked the application for rejection in their notes and the notes are lost, the application may incorrectly advance to approval.
- Citizens and officers operating on stale data may make contradictory decisions that are difficult to untangle in audit trails.
- Legal challenge: if a rejection decision was based on officer notes that were subsequently overwritten, the audit trail is incomplete and the decision may not be defensible.

**Detection:**
- **Version Conflict Log:** Every application update request includes `expected_version`. A mismatch triggers a `CONCURRENT_EDIT_CONFLICT` log entry with `application_id`, `actor_type` (citizen/officer), `expected_version`, and `current_version`.
- **CloudWatch Metric:** `ConcurrentEditConflict_Count` — alarm fires if > 20 conflicts per hour (may indicate UI auto-refresh not working or a high-volume batch update running).
- **Audit Trail Completeness Check:** A daily Celery task checks application records where `updated_at` timestamps from citizen and officer match within 60 seconds (a heuristic for detecting missed conflicts).

**Mitigation/Recovery:**
1. **Optimistic Locking:** The `Application` Django model includes a `version` integer field (auto-incremented on every update). The serializer validates that the submitted `version` matches the database `version`. If not, HTTP 409 is returned with the current state of the conflicting fields.
2. **Field-Level Merge:** The conflict resolution service implements field-level merge logic: citizen edits only affect `application_data` fields (form fields the citizen owns); officer edits only affect `officer_notes`, `review_status`, `clarification_requests`. Citizen updates use `UPDATE ... SET application_data = %s WHERE id = %s` without touching officer fields, and vice versa. True conflicts occur only when both parties edit the same field.
3. **Edit Lock Notification:** When an officer opens an application for review, the frontend establishes a WebSocket connection that publishes an `APPLICATION_LOCKED_BY_OFFICER` event to the citizen's active session (if any). The citizen sees a banner: "A field officer is currently reviewing this application. Edits are temporarily restricted to prevent conflicts."
4. **Soft Edit Lock (Advisory):** A Redis key `app_edit_lock:{application_id}` is set for 10 minutes when any actor begins editing. A second actor receives a warning: "This application is being edited by [role] since [timestamp]. Proceed with caution."
5. **Conflict Resolution UI:** If a true conflict occurs despite the above measures, both parties are shown a diff view: "Your version" vs. "Current version" with the ability to select which fields to keep from each version. All resolution choices are logged in the audit trail.

**Prevention:**
- **Role-Based Field Partitioning:** Application models are designed with clear field ownership: `application_data` (citizen-owned), `officer_fields` (officer-owned), `system_fields` (system-managed). No role can write to another role's field partition.
- **Application Status Edit Rules:** Citizens can only edit `application_data` when the application is in `DRAFT` or `CORRECTION_REQUIRED` province. Once in `UNDER_REVIEW`, citizen edits require an explicit "Request Correction" workflow that temporarily moves the application back to `DRAFT` — ensuring the officer is notified and review pauses.
- **Load Testing for Concurrency:** Load tests simulate 100 concurrent edit conflicts on the same application to validate that optimistic locking holds under pressure.

---

## EC-WORKFLOW-004: Service Eligibility Changes After Application Submitted

**Failure Mode:**
The Department of Social Welfare runs a scheme providing free electricity connections to households below the poverty line (BPL). On January 1st, the eligibility criteria changes: the income threshold is reduced from रू1,20,000/year to रू90,000/year. There are 3,200 applications in `UNDER_REVIEW` province that were submitted under the old criteria (applicant's income: रू95,000–रू1,20,000/year). These applicants were validly eligible at submission time but no longer meet the new criteria. The portal's eligibility check runs on every application access and now flags these 3,200 applications as ineligible, causing officers to reject them — even though the applicants had a legitimate expectation of being reviewed under the rules at submission time.

**Impact:**
- **Severity: Medium**
- Legally, applicants are generally entitled to be evaluated under the rules in force at the time of submission. Retroactive application of new criteria is likely illegal and may be challenged in courts or ombudsman complaints.
- Mass rejection of 3,200 applications triggers 3,200 rejection notifications, potentially causing public outcry and media coverage.
- The portal team and department must undertake a manual review to identify affected applications — a significant operational burden.
- Citizens who receive rejection letters based on new criteria they were not subject to at submission time suffer real harm: they may have turned down other opportunities or prepared for the benefit.

**Detection:**
- **Eligibility Criteria Change Log:** Every change to `ServiceEligibilityCriteria` records is logged with `changed_by`, `changed_at`, `old_value`, `new_value`, and `effective_date`.
- **Retroactive Impact Analysis:** When eligibility criteria are updated, an immediate impact analysis job runs: `count applications in UNDER_REVIEW/PENDING_APPROVAL provinces that would become ineligible under the new criteria`. This count is displayed to the admin who made the change, requiring confirmation.
- **CloudWatch Alert:** If the retroactive impact count > 0, a `EligibilityCriteriaChange_Retroactive_Impact` alert fires to the department head and portal admin.

**Mitigation/Recovery:**
1. **Eligibility Snapshot at Submission:** At the moment of application submission, the applicable eligibility criteria version (with a `criteria_version_id` foreign key) is snapped onto the application record. Eligibility checks for this application always use the snapshot, not the live criteria. This is the correct legal model.
2. **Grandfathering Workflow:** For any batch of applications affected by a retroactive criteria change, the department head can invoke the `grandfather_applications` management command that marks affected applications with `eligibility_snapshot_locked = True`, preventing re-evaluation under new criteria.
3. **Transition Period Policy:** New eligibility criteria can be set with an `effective_date` in the future (minimum 30-day notice for active applications). Applications submitted before the effective date are evaluated under old criteria; applications submitted after the effective date use new criteria.
4. **Bulk Re-Review Workflow:** If retroactive application is legally required (e.g., court order or department directive), a supervised bulk re-review workflow is provided. Officers are presented with a queue of affected applications, each showing the new eligibility gap, and must individually confirm rejection with a mandatory reason field.
5. **Citizen Notification for Affected Applications:** Citizens whose applications are affected by a criteria change receive a proactive notification: "Eligibility criteria for [scheme] have been updated. Your application submitted on [date] will be evaluated under the criteria applicable at submission time."

**Prevention:**
- **Immutable Criteria Versioning:** The `ServiceEligibilityCriteria` model uses a versioning pattern (never mutates in-place, always creates new version records). Applications always reference a specific version, not the "current" criteria.
- **Admin UI Warning:** The admin interface that manages eligibility criteria displays a live count of applications that would be affected by a retroactive change before the admin can save it, requiring a two-step confirmation.
- **Legal Review Gate:** Changes to eligibility criteria with retroactive impact > 100 applications require a secondary approval from the department legal officer before activation.

---

## EC-WORKFLOW-005: Field Officer Inactivity / Unassigned Queue

**Failure Mode:**
A batch of 80 applications is assigned to Field Officer Rajesh Mehta on a Friday afternoon. Officer Mehta goes on unexpected medical leave starting Saturday and is absent for 12 days. The applications sit in his queue without any system-level timeout or escalation. Eleven days pass. Citizens with applications in `ASSIGNED_TO_OFFICER` province receive no updates. The 15-day statutory SLA for initial review (mandated by the province Right to Service Act) expires for all 80 applications. Citizens begin filing RTI applications and service delivery complaints. The portal's SLA dashboard shows a 100% SLA breach for this officer's queue.

**Impact:**
- **Severity: High**
- Statutory SLA breach for each application is a legal violation under the province's Right to Service Act, potentially attracting fines and departmental action against the department head.
- Citizens with urgent applications (property mutation for a property sale closing, income certificate for a loan application) suffer real financial harm from the delay.
- SLA breach metrics reported in periodic government dashboard reviews damage the portal's performance rating.
- Resolving a 12-day backlog for a single officer requires emergency escalation and reallocation, disrupting other officers' queues.

**Detection:**
- **SLA Monitoring Job:** A Celery Beat task runs every 30 minutes and calculates the time since each application entered `ASSIGNED_TO_OFFICER` province. Applications approaching 70% of their SLA deadline (e.g., 10.5 days for a 15-day SLA) trigger a `SLA_WARNING` notification to the supervisor.
- **CloudWatch Alarm:** `ApplicationUnassigned_Duration_Hours` alarm fires when any application in `ASSIGNED_TO_OFFICER` or `PENDING_REVIEW` province has been in that province for > 72 hours without officer action.
- **Officer Activity Metric:** Each officer's last-active timestamp is updated on every portal login and every application action. An alert fires to the supervisor if an officer's last_active is > 2 business days in the past.
- **Queue Depth Monitoring:** Department-level CloudWatch dashboard shows queue depth per officer. Sudden large increases in one officer's queue (without proportional processing) trigger an alert.

**Mitigation/Recovery:**
1. **Automatic SLA-Based Escalation:** Applications that have been in `ASSIGNED_TO_OFFICER` province for > 50% of their SLA deadline without officer action are automatically escalated to the officer's supervisor. The supervisor receives an email and in-portal notification listing all affected applications.
2. **Queue Reallocation Tool:** The department supervisor has a "Reallocate Queue" tool that allows bulk reassignment of all applications from one officer to another (or to a shared queue). This can be done in a single action, with all affected citizens notified of the change in their assigned officer.
3. **Shared Department Queue:** As a fallback, if an officer is absent and no substitute is assigned within 24 hours of escalation, the applications are moved to a `DEPARTMENT_SHARED_QUEUE` visible to all officers in the department, ensuring work can be picked up voluntarily.
4. **Breach Notification to Citizens:** When an SLA deadline is breached, the citizen automatically receives: "We regret that your application [ID] has exceeded the expected review period. It has been escalated to a senior officer. You will receive an update within [X] days."
5. **Officer Absence Management:** The HR/admin panel allows supervisors to mark officers as "on leave" — this automatically triggers queue reassignment for unreviewed applications assigned to the officer, preventing the 12-day gap scenario entirely.

**Prevention:**
- **Mandatory Backup Assignment:** When an application is assigned to an officer, the assignment logic also designates a backup officer (the supervisor or a peer) who receives read access to the application and can act if the primary officer is inactive for > 48 hours.
- **Daily SLA Dashboard Email:** Each department head receives a daily automated email with: applications by SLA status (on track, warning, breached), officer queue depths, and officer last-active times.
- **SLA Alerts Are Non-Dismissible:** SLA breach alerts in the officer's notification panel cannot be marked as read without the officer taking an action on each flagged application — preventing silent dismissal.
- **Leave Integration:** Integration with the HR leave management system (or a simple leave calendar in the portal admin) allows automatic queue reassignment trigger when an officer's leave is recorded.

---

## EC-WORKFLOW-006: Infinite Clarification Loop

**Failure Mode:**
Field Officer Kavita Reddy reviews a caste certificate application and requests clarification: "Please provide your father's caste certificate." The citizen uploads their father's caste certificate. Officer Kavita reviews the response and again requests clarification: "Please provide the original, not a photocopy." The citizen re-uploads a high-resolution scan. Officer Kavita requests clarification again: "Document is not in the required format." The citizen, confused about what format is required, uploads in multiple formats. Each clarification request resets the SLA clock (in a misconfigured system), allowing the application to remain in `PENDING_CLARIFICATION` province indefinitely while the officer avoids making a decision.

**Impact:**
- **Severity: Medium**
- The application remains in an unresolved province for weeks or months, denying the citizen their entitled certificate.
- If SLA is reset on each clarification request, the statutory Right to Service Act protections are effectively nullified for this application.
- Repeated clarification requests for the same information indicate either officer non-performance or a systemic documentation requirements gap that affects many citizens.
- Citizens who engage in multiple rounds of clarification often give up and seek the service through informal channels (corruption risk).

**Detection:**
- **Clarification Loop Counter:** The `ApplicationClarification` model tracks `clarification_count` per application. A CloudWatch metric `ClarificationCount_High` fires when any application reaches 3 clarification requests.
- **Repeated Clarification Type Detection:** Application logic checks if the new clarification request text is semantically similar to a previous request (cosine similarity on document type keywords). Duplicate requests trigger a `REPEATED_CLARIFICATION_WARNING` log and notify the supervisor.
- **SLA Audit:** A monthly report flags all applications that have had SLA reset > 2 times due to clarification requests. These are reviewed by the department head for officer performance evaluation.
- **Citizen Complaint Correlation:** High clarification count applications are correlated with citizen complaint tickets. A pattern of high clarification counts for a specific officer drives a performance review.

**Mitigation/Recovery:**
1. **Clarification Limit Enforcement:** Applications are limited to a maximum of 3 clarification rounds. After the 3rd clarification request, the officer must either approve or reject the application — no further clarification is permitted. A 4th attempt to request clarification is rejected by the system with a message: "Maximum clarification rounds reached. Please make a final decision."
2. **SLA Continuity:** Clarification requests do NOT reset the SLA clock. The time spent in `PENDING_CLARIFICATION` province still counts against the total SLA. The SLA timer pauses only for the period the application is waiting for the citizen's response (not for the officer's time).
3. **Supervisor Notification at 2nd Clarification:** When a second clarification is requested on the same application, the officer's supervisor is automatically notified. The supervisor can review both clarification requests and the citizen's responses to ensure the requests are legitimate.
4. **Structured Clarification Requests:** Officers must select from a pre-defined list of document/information requirements when raising a clarification. Free-text clarification is limited to 250 characters, appended to the structured selection. This prevents vague, unactionable requests.
5. **Citizen Escalation Right:** After 2 clarification rounds, the citizen portal displays an option: "I believe I have provided all required information. Escalate to supervisor." This moves the application to the supervisor's review queue, bypassing the original officer.

**Prevention:**
- **Pre-Application Document Checklist:** Before submitting the application, citizens are shown an exact list of required documents (pulled from the service configuration). Documents are validated at submission time against this list. This eliminates the majority of legitimate clarification needs.
- **Officer Clarification Training:** Officers are trained on structured clarification templates. All valid clarification reasons are documented in the knowledge base. Vague or repeated requests are an officer performance issue tracked in quarterly appraisals.
- **Clarification Metrics in Officer Dashboard:** Each officer's dashboard shows their average clarification requests per application and the percentage of applications resolved in ≤1 clarification round. These metrics are visible to supervisors.

---

## EC-WORKFLOW-007: Multi-Department Approval Dependency

**Failure Mode:**
A fire safety NOC application requires approval from both the Municipality (for structural compliance) and the Fire Department (for fire safety compliance). The portal routes the application to both departments simultaneously (parallel approval). The Municipality approves after 10 days. The Fire Department rejects the application for insufficient fire exits after 12 days. The application is now in a partially-decided province: one department approved and one rejected. The citizen's portal dashboard shows a confusing status. The workflow engine does not have a defined resolution policy for this split-decision scenario and leaves the application in `PARTIAL_APPROVAL` status indefinitely.

**Impact:**
- **Severity: High**
- The application is in a workflow deadlock — no further automated action is possible without a defined resolution policy.
- The citizen is unable to proceed with their construction or business opening, causing real financial harm (construction delay, missed business opening).
- The approved department (Municipality) may expire the approval if not acted upon within a set time (e.g., 6 months), creating a second approval that also needs renewal.
- Without a clear final status, the citizen cannot apply for a fresh application (the portal blocks re-submission if an active application exists) and cannot formally appeal the rejection (no final decision exists to appeal).

**Detection:**
- **Split-Decision Detector:** After each departmental decision, the workflow engine evaluates the overall application status. A `SPLIT_DECISION_DETECTED` event is logged and a CloudWatch alarm fires when any application reaches this province.
- **CloudWatch Alarm:** `SplitDecision_Application_Count` — fires when count > 0. This province should never be a steady province; it requires resolution.
- **Department Head Notification:** Automated email to both department heads and the portal admin team immediately upon split-decision detection, with the application ID and the individual decisions.
- **Dashboard Alert:** The portal admin dashboard highlights all applications in `PARTIAL_APPROVAL` province with a red badge, as these require manual intervention.

**Mitigation/Recovery:**
1. **Precedence Policy Configuration:** Each multi-department workflow defines a rejection precedence policy at service configuration time: `ANY_REJECTION_FAILS` (one rejection fails the whole application) or `MAJORITY_APPROVAL_PASSES` or `WEIGHTED_APPROVAL`. For fire safety NOCs, the policy is `ANY_REJECTION_FAILS` — one department's rejection is final.
2. **Automatic Resolution via Policy:** With `ANY_REJECTION_FAILS`, the workflow engine automatically resolves the split decision: the application status is set to `REJECTED`, and the approved department's approval is automatically revoked. The citizen is notified with the rejection reason from the Fire Department.
3. **Escalation to Coordinating Authority:** For workflows with `ESCALATE_ON_SPLIT` policy, the split decision is escalated to a designated coordinating authority (e.g., the Chief District Officer (CDO)'s office) that has override power to accept or reject, with full audit logging.
4. **Appeal Pathway:** Once a final decision is reached (even via policy resolution), the citizen has a 30-day window to file an appeal, specifying which department's decision they are challenging and providing additional evidence. Appeals are routed to a senior officer in the rejecting department.
5. **Approval Expiry Pause:** Departmental approvals issued as part of a multi-department workflow do not expire while the application is in a split-decision or escalation province. Expiry timers are paused until the final status is determined.

**Prevention:**
- **Pre-Configured Resolution Policies:** Every multi-department service has a mandatory `rejection_policy` field configured before the service goes live. Services with an undefined policy cannot accept applications — the portal admin UI enforces this at service creation time.
- **Sequential vs. Parallel Routing Selection:** Service configurations differentiate between sequential approval (Dept A must approve before Dept B sees the application) and parallel approval. Sequential routing eliminates the split-decision problem but increases processing time. The choice is made deliberately per service type.
- **Multi-Approver Simulation in Staging:** All new multi-department workflows are tested in staging with simulated split-decision scenarios before production launch.

---

## EC-WORKFLOW-008: Application Submitted to Wrong Department

**Failure Mode:**
The portal offers 47 service types across 12 departments. The service listing page has a text search and category filter. A small business owner searching for "trade license" finds both "Trade License (New) — Commerce Department" and "Trade and Food License — Health Department." They mistake the Health Department option for the Commerce Department trade license and submit a full application (with documents uploaded and fee paid) to the Health Department. The Health Department processes commercial food establishment licenses, not general trade licenses. The Health Department officer, after reviewing, marks the application as "Wrong Department" but the portal has no workflow for inter-department transfer — it can only reject the application. The citizen receives a rejection, must reapply to the correct department, and faces uncertainty about their already-paid fee.

**Impact:**
- **Severity: Medium**
- Citizen wastes time and must re-submit to the correct department. End-to-end delay can be 15–30 days for the misrouted application plus the full processing time for the correct one.
- Fee paid for the wrong department application creates a refund workflow. If the two services have different fees, a fresh payment is required for the correct department application.
- Health Department queue is cluttered with incorrectly routed applications, reducing throughput for legitimate applications.
- Repeated misrouting for certain service pairs indicates a UX design problem that affects many citizens.

**Detection:**
- **Wrong-Department Rejection Rate:** A CloudWatch metric tracks the count of applications rejected with reason code `WRONG_DEPARTMENT`. A spike indicates a confusing service listing UI issue.
- **Service Confusion Heatmap:** Analytics track which services are most frequently confused (users viewing both services before applying). This drives UI improvements.
- **Officer Misrouting Flag:** When an officer selects `WRONG_DEPARTMENT` as a rejection reason, the system prompts: "Which department should this application have been sent to?" The officer's selection is logged for routing improvement analysis.

**Mitigation/Recovery:**
1. **Inter-Department Transfer Workflow:** Instead of simple rejection, officers have an "Transfer to Correct Department" action. This moves the application to the target department's incoming queue with the original submission date preserved (SLA continues from original submission). All documents and data are carried over without the citizen needing to resubmit.
2. **Fee Reconciliation on Transfer:** If the target department's service has a different fee, the system automatically calculates the difference. If the citizen overpaid, the excess is refunded. If underpaid, the citizen is notified to pay the remaining amount before the target department begins review.
3. **Citizen Notification on Transfer:** "Your application has been transferred to the [Target Department] for processing, as it falls under their jurisdiction. Your original submission date is preserved. No action is required from you unless you receive a payment request."
4. **Application Data Mapping:** A `service_data_mapping` configuration maps fields from the wrong service's form to the correct service's form where data is compatible. Fields that cannot be mapped are flagged for the citizen to fill in after the transfer.
5. **Search UI Enhancement:** Based on misrouting analytics, service descriptions are updated to clearly differentiate commonly confused services. Prominent "Is this the right service?" disambiguation banners are added to services with high misrouting rates.

**Prevention:**
- **Guided Service Selection:** Before displaying a service's application form, the portal shows a 3-question eligibility wizard ("What type of business?", "Are you a new establishment?", "Do you prepare/serve food?") that routes the citizen to the correct specific service.
- **Service Similarity Warning:** When a citizen begins filling an application form, the system checks if there are similar services in other departments and displays a brief disambiguation note: "Note: If your business serves food, you may need the Health Department Food License instead."
- **Department Confirmation Step:** The form's first page explicitly provinces: "You are applying for [Service Name] with [Department Name]. This service is for [one-line description]." The citizen must tick a confirmation checkbox before proceeding.

---

## EC-WORKFLOW-009: Workflow Province Corruption

**Failure Mode:**
A building permit application is being processed by the workflow engine. During the state transition from `APPROVED` to `CERTIFICATE_GENERATING`, the Django service initiates a database transaction: it updates the application status, writes a certificate record, and enqueues a Celery task to generate the PDF. At the moment between the application status update and the certificate record creation, the RDS database connection is lost (due to a brief network partition). The transaction is partially committed by the database before the connection drop (status updated to `APPROVED` but certificate record not created), despite the application code using `transaction.atomic()` (the connection drop prevents the rollback from completing). The application now shows `APPROVED` in the database but has no certificate record. The citizen's portal shows "Approved" but no download link. Subsequent queries fail with foreign key errors. The workflow engine is stuck.

**Impact:**
- **Severity: Critical**
- A corrupted workflow state is invisible to the citizen (who sees "Approved" and waits for a download link) while system state is actually broken.
- Officers who attempt to review the record encounter database errors that crash the review page.
- Automated certificate generation Celery tasks may retry indefinitely, clogging the queue.
- Manual recovery requires direct database intervention, which carries its own risk if done incorrectly.
- If the certificate is legally required for business operation (e.g., fire safety NOC for a restaurant to open), the corruption causes real business harm.

**Detection:**
- **Integrity Check Job:** A Celery Beat task (`workflow_integrity_checker`) runs every 15 minutes. It queries for applications where `status = APPROVED AND NOT EXISTS (SELECT 1 FROM certificates WHERE application_id = applications.id)`. Any such record is flagged as `INTEGRITY_VIOLATION`.
- **CloudWatch Alarm:** `WorkflowStateInconsistency_Count` — fires immediately when any application enters an inconsistent province, with PagerDuty alert to the on-call engineer.
- **Transaction Failure Log:** Database transaction failures (including partial commits due to connection drops) are logged with the application ID, transition attempted, and error details.
- **Certificate Generation Task Failure Alert:** Celery task `generate_certificate` that fails with `IntegrityError` or `ObjectDoesNotExist` publishes a `CERTIFICATE_GENERATION_FAILED` event, distinct from normal failure modes.

**Mitigation/Recovery:**
1. **Saga Pattern for Workflow Transitions:** Critical workflow state transitions (APPROVED → CERTIFICATE_GENERATING) use a saga pattern: (a) Write a `pending_transition` record to the DB (marks intent), (b) Execute the transition within `transaction.atomic()`, (c) On success, delete the `pending_transition` record. On startup and on every `workflow_integrity_checker` run, incomplete sagas are detected and either completed or rolled back.
2. **Idempotent Celery Tasks:** The `generate_certificate` Celery task is idempotent: if the certificate record already exists for the application, it returns the existing record instead of creating a duplicate. If it does not exist, it creates it. This allows safe retries.
3. **Manual Recovery Runbook:** A management command `fix_corrupted_workflow --application-id {id}` is provided for SREs. It diagnoses the inconsistency, creates the missing certificate record with placeholder data, and re-queues the certificate generation task. The runbook documents every corruption pattern and its recovery command.
4. **Alert → Recovery SLA:** The on-call engineer must acknowledge and resolve `WorkflowStateInconsistency_Count > 0` alerts within 30 minutes, regardless of business hours. This is defined in the on-call runbook.
5. **Citizen Communication:** During the period of province corruption, the citizen sees: "Your application has been approved. Certificate generation is in progress and will be available shortly." This message is automatically set for any `APPROVED` application without a certificate, preventing confusing UI provinces.

**Prevention:**
- **Transactional Outbox Pattern:** Instead of directly calling Celery from within a database transaction, all Celery task enqueues happen via the Transactional Outbox pattern: the task parameters are written to an `outbox` DB table within the same transaction. A separate process reads the outbox and enqueues Celery tasks, ensuring DB province and task queue are always consistent.
- **Database Connection Resilience:** The Django database connection is configured with `CONN_MAX_AGE=60` and automatic reconnection. SQLAlchemy/Django uses `autocommit=False` with explicit transaction boundaries.
- **Staging Chaos Test:** Monthly chaos injection test kills the RDS connection mid-transaction on the state transition path, validating that the saga pattern correctly handles partial commits.

---

## EC-WORKFLOW-010: Batch Application Deadline Surge

**Failure Mode:**
A government scheme for farmer subsidy applications has a hard closing date of March 31st at 11:59 PM IST. The portal has been accepting applications all month with a steady load of 200 applications per hour. On March 31st at 11 PM, 10,000 applications are submitted in the final hour as procrastinating applicants rush to beat the deadline. The portal's auto-scaling is configured with a 5-minute scale-out delay. In the first 5 minutes of the surge, the 4 ECS tasks handling API requests are overwhelmed. The request queue backs up. Timeouts occur. Some application submissions appear to succeed (HTTP 200 from the load balancer's cached response or a premature ACK) but are not actually persisted to the database. Other submissions receive HTTP 503 errors. Citizens who receive HTTP 503 retry, causing duplicate submission attempts. The scheme portal later shows applications missing from the database that citizens claim to have submitted.

**Impact:**
- **Severity: High**
- Citizens who submitted applications in good faith before the deadline find their applications not recorded — they are denied a government benefit they were entitled to.
- This is legally and politically extremely sensitive: deadline-missed applications for agricultural subsidies, scholarship schemes, or welfare benefits directly affect livelihoods.
- Duplicate submission attempts from retrying citizens (who got HTTP 503 on first try) create duplicate draft records that must be manually de-duplicated.
- Post-deadline, 10,000 applications must be processed in the normal review SLA — the system is stressed even after the submission surge passes.

**Detection:**
- **Application Submission Rate Alarm:** `ApplicationSubmission_Rate_1Min` CloudWatch alarm fires when the per-minute submission rate exceeds 150% of the 1-hour rolling average. This provides early surge warning.
- **ECS CPU/Memory Utilization:** ECS cluster CPU utilization > 80% for > 2 minutes triggers immediate scale-out (pre-configured auto-scaling policy).
- **ALB Request Queue Depth:** ALB `RequestCountPerTarget` and `TargetResponseTime` CloudWatch metrics alarm when response time exceeds 10 seconds — 10 seconds is the threshold before citizens start experiencing timeouts.
- **Database Connection Wait Time:** If application writes are taking > 2 seconds (P95), a database bottleneck alarm fires.
- **Submission Failure Rate:** `ApplicationSubmission_Failure_Rate` metric (HTTP 4xx/5xx on submission endpoint) alarm fires if failure rate exceeds 1% during peak.

**Mitigation/Recovery:**
1. **Pre-Deadline Scaling:** For all services with a known hard deadline, SREs pre-scale the ECS service (minimum task count × 4) 2 hours before the deadline and maintain that scale for 1 hour after. This is tracked in the `Scheduled Scaling Events` calendar. The pre-scaling is automated via AWS Application Auto Scaling scheduled actions.
2. **Application Queue Buffer:** Application submissions are accepted by a thin "intake API" (separate ECS service with higher max task count) that writes submission requests to an SQS queue and immediately returns a `202 Accepted` with a `submission_receipt_id`. A backend worker processes the SQS queue and persists to PostgreSQL. The citizen's application status starts as `RECEIVED` and transitions to `SUBMITTED_CONFIRMED` once persisted.
3. **Idempotency on Submission:** The submission endpoint accepts a client-generated `idempotency_key` (UUID generated by the frontend on form load). If the same key is submitted twice (citizen retry), the second request returns the result of the first, preventing duplicates even under retry conditions.
4. **Deadline Extension Protocol:** For documented system overload events occurring within 30 minutes of a scheme deadline, the department has a pre-approved protocol to extend the scheme deadline by 24 hours. The extension is activated by the department head via a protected admin API endpoint, immediately updating the deadline displayed on the portal.
5. **SQS Dead Letter Queue Recovery:** Submissions that fail processing (after 3 SQS retries) go to a Dead Letter Queue (DLQ). The on-call engineer monitors the DLQ in real time during surge events. Failing submissions in the DLQ are manually reviewed and re-queued if the failure is transient (e.g., brief DB overload).

**Prevention:**
- **Capacity Planning for Known Deadlines:** All services with government-mandated deadlines are cataloged in a `Deadline Calendar`. SREs run load tests simulating 10× expected peak traffic before each major deadline. Infrastructure is scaled to handle 5× historical peak.
- **Pre-Deadline Reminders:** Citizens are proactively notified 7 days and 1 day before a scheme deadline to submit early. This reminder campaign has historically reduced last-minute surge by 30–40% in similar portals.
- **Gradual Deadline Communication:** The portal messaging for deadline-approaching schemes reads: "Application window closes March 31st. We recommend submitting by March 28th to avoid last-minute delays."
- **Database Write Optimization:** High-volume write paths use PostgreSQL COPY for batch inserts, connection pooling via PgBouncer, and prepared statements to minimize per-insert overhead during surges.

---

## Operational Policy Addendum

### Citizen Data Privacy Policies

- **Draft Data Retention Limit:** Application drafts that have been inactive for 90 days are automatically deleted, with a 7-day warning notification to the citizen before deletion. Citizens are not required to complete applications they no longer need.
- **Application Data Access:** Only the submitting citizen, the assigned field officer, the department head, and the portal administrator can access a specific application's full data. Cross-departmental access requires an explicit transfer record.
- **Document Storage Isolation:** Documents uploaded for one application are not accessible to officers reviewing a different application, even if from the same citizen. Each document access is scoped to the specific application context.
- **Audit Trail Immutability:** All application workflow state transitions, officer actions, citizen edits, and decision records are written to an immutable audit log (INSERT-only, no UPDATE/DELETE). This log is preserved for 7 years per e-governance data retention requirements.

### Service Delivery SLA Policies

- **Initial Review SLA:** Field officers must complete initial review (approve, reject, or request clarification) within 15 business days for standard services, 5 business days for urgent services (as defined per service configuration).
- **Clarification Response Window:** Citizens have 15 calendar days to respond to a clarification request. After 15 days without response, the application is automatically moved to `PENDING_CLOSURE` with a 7-day grace period before auto-closure.
- **SLA Breach Escalation:** Applications breaching SLA are automatically escalated: first to the direct supervisor (day 1 of breach), then to the department head (day 3 of breach), then to the portal administrator (day 7 of breach).
- **SLA Reporting:** Monthly SLA compliance reports per department are generated automatically and submitted to the Province IT Department. Reports include breach counts, average resolution time, and top failure categories.

### Fee and Payment Policies

- **Fee Lock on Submission:** The fee applicable to an application is locked at the moment the application is formally submitted (not at draft creation). Citizens who hold drafts while fees change will see the updated fee when they go to submit.
- **Rejected Application Refunds:** Fees for applications rejected due to system errors, wrong routing, or administrative reasons are refunded within 7 business days. Fees for applications rejected due to ineligibility or incomplete documentation are governed by the department's published refund policy.
- **Transfer Fee Handling:** Applications transferred between departments retain their original payment record. Fee differences are handled by targeted refund or supplementary payment requests, not by requiring a fresh full payment.

### System Availability Policies

- **Deadline Proximity Maintenance Freeze:** No planned maintenance, deployments, or configuration changes are permitted within 48 hours of a published scheme deadline, unless to resolve a critical security vulnerability.
- **Workflow Engine Availability:** The application workflow engine must maintain 99.9% availability on a rolling monthly basis. Workflow processing delays > 60 seconds must be treated as incidents.
- **Database Backup Before Deadline:** Full PostgreSQL snapshots are taken 6 hours and 1 hour before major scheme deadlines, enabling point-in-time recovery to any minute of the deadline day if needed.
- **Post-Surge Audit:** After any identified submission surge event, a data integrity audit runs within 24 hours to identify and recover any missing submissions, with results reported to the department head.
