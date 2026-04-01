# Edge Cases — Application Tracking

## Overview

This document covers edge cases in the candidate application lifecycle: from submission through ATS pipeline management, resume parsing, candidate deduplication, and bulk import operations. Failures here affect data integrity of the hiring funnel, recruiter workflow continuity, and candidate experience. Some edge cases — particularly pipeline stage deletion and auto-move rule loops — can corrupt large volumes of candidate records if not caught quickly.

---

### EC-09: Candidate Applies to the Same Job Twice

**Failure Mode:** A candidate submits an application for Job ID 4892 and receives a confirmation email. Two weeks later, they create a new account with a different email address and apply to the same job again. Because duplicate detection relies only on `(candidate_email, job_id)` uniqueness, the second application (different email, same job) is accepted and creates a parallel pipeline record for the same physical person. The recruiter inadvertently interviews the same candidate twice at different pipeline stages before the duplication is discovered.

**Impact:** Medium. Wasted recruiter and interviewer time. Candidate history is split across two records, making it impossible to see the full interaction timeline. Reporting metrics are inflated.

**Detection:**
- At application submission, a fuzzy-match check runs against the candidate pool using name + last-4-digits of phone (if provided) + resume fingerprint (SHA-256 of normalised text content). A `potential_duplicate_application` flag is raised if similarity score > 0.85.
- Nightly deduplication job using a Jaccard similarity index on parsed resume content flags candidate pairs with similarity > 0.90 applying to the same job.
- Recruiter UI shows a "Possible Duplicate" banner in the application detail view when the flag is set.

**Mitigation:**
1. Flag both applications as `PENDING_DEDUPLICATION` in the pipeline — neither advances nor is rejected automatically.
2. Notify the recruiter of the suspected duplicate via an in-app notification with a side-by-side comparison view.
3. The recruiter merges or dismisses the duplicate flag within 48 hours; the system does not act autonomously on a potential duplicate to avoid wrongful rejection.

**Recovery:**
1. After recruiter confirms the duplicate: archive the newer application, merge its notes and timeline events into the primary application record.
2. Send a single consolidated status email to the candidate (use the most recently provided email address).
3. Update the merged record to reflect the correct pipeline stage.

**Prevention:**
- Implement a multi-signal deduplication check at submission time: email, phone, resume fingerprint, and LinkedIn profile URL (if provided). Block resubmission with a clear message if the same person is detected.
- Add a unique partial index in PostgreSQL: `CREATE UNIQUE INDEX CONCURRENTLY application_email_job ON applications(candidate_email, job_id) WHERE status != 'WITHDRAWN'`.
- Allow candidates to log in and see their existing application rather than creating a new submission.

---

### EC-10: Resume File is Corrupt

**Failure Mode:** A candidate uploads a PDF resume that is malformed (truncated mid-byte, XFA-form-only PDF that contains no extractable text) or a DOCX file that is password-protected. The file is accepted by the upload endpoint (MIME type check passes because the file header bytes are valid), stored in S3, and queued for parsing. The parsing worker crashes with an unhandled exception, leaving the application in a `PARSING_IN_PROGRESS` state indefinitely.

**Impact:** Medium. Recruiter cannot view the resume; the application appears stuck. If the recruiter doesn't notice, the candidate may never be reviewed. Parsing worker crash may affect the queue for other candidates.

**Detection:**
- Parsing worker wraps the extraction call in a try-catch; on failure, publishes a `resume.parse_failed` event with error classification (`CORRUPT_PDF`, `PASSWORD_PROTECTED`, `UNSUPPORTED_FORMAT`).
- Application status remains `PARSING_IN_PROGRESS` for more than 5 minutes triggers a `stuck_parse` alert in Datadog.
- Dead-letter queue (DLQ) on the resume parsing SQS queue accumulates messages; alert fires when DLQ depth > 10.

**Mitigation:**
1. Move the stuck application to `PARSE_FAILED` status.
2. Notify the candidate via email that their file could not be processed and ask them to re-upload a compatible, unprotected PDF or DOCX.
3. Resume worker processing for other candidates by acknowledging the failed message and moving it to the DLQ.

**Recovery:**
1. Once candidate re-uploads, re-queue the parse job.
2. Implement a grace period: if no re-upload within 5 business days, set application status to `INCOMPLETE` and notify the recruiter.
3. Review DLQ contents weekly; files that consistently fail are inspected manually by the engineering team to identify new failure patterns.

**Prevention:**
- Before queuing the parse job, run a pre-flight file validation step: use `pdfinfo` (from Poppler) to verify the PDF is not encrypted and has at least one extractable text layer; use Apache POI's `OPCPackage.open()` for DOCX to verify it is not password-protected.
- Reject protected or invalid files at the upload endpoint with a user-friendly error message before storage.
- Set a maximum retry count of 3 on the parsing queue; exceeded retries route to DLQ automatically.

---

### EC-11: Application Submitted After Job Officially Closed

**Failure Mode:** Job ID 7103 has `closes_at = 2025-03-15T23:59:59Z`. At 23:59:45Z a candidate begins filling out the application form. At 00:00:14Z (15 seconds after the deadline), they click submit. The API server's clock is 30 seconds ahead of the database server's clock due to NTP drift, causing the server-side validation to read `closes_at` as still in the future. The application is accepted and enters the pipeline.

**Impact:** High. Creates a fairness and legal risk: some candidates were accepted after the published close date while others were not. In government or regulated hiring contexts, this can invalidate the entire requisition.

**Detection:**
- Application submission endpoint logs the server timestamp, database timestamp, and `closes_at` value for every submission; a `post_deadline_submission` event is raised when `submission_time > closes_at` even if the application was accepted.
- Clock drift monitor: a Prometheus alert fires if the difference between application server time and database server time exceeds 5 seconds (`ntp_offset_seconds > 5`).

**Mitigation:**
1. Set the accepted-after-deadline application status to `PENDING_REVIEW` — do not reject automatically as the candidate may have a legitimate case (clock drift is a platform error, not the candidate's fault).
2. Notify the recruiter of the post-deadline submission and the timestamp discrepancy.
3. Fix the NTP drift immediately; investigate and sync all application server clocks.

**Recovery:**
1. Recruiter decides whether to accept or reject the application based on the circumstances; the platform records the decision with a reason code.
2. If the application was accepted due to platform clock drift, consider accepting all such applications for this job in the interest of fairness.
3. Resolve NTP misconfiguration across the application server fleet.

**Prevention:**
- Use the database server timestamp (`NOW()` in PostgreSQL) as the authoritative timestamp for all deadline comparisons — never use the application server's local clock.
- Add a 60-second grace period to `closes_at` enforced server-side, then block submissions; display a countdown timer in the UI so candidates know when time is running out.
- Monitor NTP synchronisation across all servers with an alerting rule in infrastructure monitoring.

---

### EC-12: ATS Pipeline Stage Deleted While Candidates Are In It

**Failure Mode:** A recruiter admin deletes the "Technical Phone Screen" pipeline stage from a job's ATS configuration. At the time of deletion, 47 candidate applications have `current_stage_id` pointing to the deleted stage. The database enforces a `NOT NULL` constraint on `current_stage_id` but uses a `SET NULL ON DELETE` foreign key cascade. All 47 applications now have `current_stage_id = NULL`, making them invisible in the Kanban pipeline view.

**Impact:** High. 47 candidates fall off the pipeline entirely. Recruiters don't see them and they may be forgotten. Timeline events and scheduled interviews for those candidates may also orphan.

**Detection:**
- Before executing a stage deletion, the API performs a pre-flight check: `SELECT COUNT(*) FROM applications WHERE current_stage_id = :stageId AND status = 'ACTIVE'`. If count > 0, deletion is blocked with a `STAGE_IN_USE` error.
- A nightly audit query checks for applications where `current_stage_id IS NULL AND status = 'ACTIVE'`; any results trigger a `orphaned_applications` alert.

**Mitigation:**
1. Identify all affected application IDs using: `SELECT id FROM applications WHERE current_stage_id IS NULL AND status = 'ACTIVE' AND updated_at > :deletionTimestamp`.
2. Restore their `current_stage_id` to the nearest equivalent active stage (use the stage immediately preceding the deleted one in the pipeline order).
3. Notify the recruiter of the affected candidates and their new stage assignment.

**Recovery:**
1. Add a migration to replace the `SET NULL ON DELETE` cascade with `RESTRICT` — preventing stage deletion when candidates are present.
2. Provide a stage archival workflow: instead of hard deletion, stages are marked `ARCHIVED` and candidates are moved to a target stage specified by the admin before archival completes.
3. Backfill any orphaned timeline events to point to the correct stage.

**Prevention:**
- Never allow hard deletion of pipeline stages; replace with soft-archival that requires explicit candidate migration.
- Add a foreign key constraint `ON DELETE RESTRICT` on `applications.current_stage_id` at the database level.
- Display a warning modal listing the number of affected candidates before any stage removal action can be confirmed.

---

### EC-13: Bulk Application Import Partial Failure

**Failure Mode:** A recruiter initiates a bulk import of 1,000 applications from a legacy ATS CSV export. The import service processes records in batches of 100 in a loop. Batch 6 (records 501–600) fails due to a malformed date field (`hire_date = "Jan 32 2024"`). The import job catches the error at the batch level, logs it, and continues to batches 7–10. The recruiter is notified "Import complete: 900 records imported." The 100 failed records are logged but not surfaced clearly. No partial retry mechanism exists.

**Impact:** High. 100 candidates are silently missing from the system. Recruiter believes all 1,000 were imported. Candidates who applied legitimately have no pipeline record. Compliance reporting under-counts.

**Detection:**
- Import service publishes an `import.batch_failed` event for each failed batch with the batch number, record indices, and error reason.
- Import job completion event includes `total_requested`, `total_succeeded`, `total_failed` counters; UI displays these prominently. Any `total_failed > 0` result is highlighted in amber.
- A reconciliation endpoint allows the recruiter to download a CSV of failed records with error details.

**Mitigation:**
1. Surface the failure count immediately in the import status UI; do not report "Import complete" if any records failed.
2. Provide a downloadable error report CSV within 5 minutes of import completion.
3. Allow the recruiter to fix the CSV and re-import only the failed records using the error report as a template.

**Recovery:**
1. Recruiter corrects the malformed data in the error report CSV.
2. Re-import the corrected CSV using a partial import endpoint that accepts a `job_id` and `records_only` flag.
3. Verify the final count: `SELECT COUNT(*) FROM applications WHERE import_batch_id = :importId` matches `total_requested`.

**Prevention:**
- Implement per-record error handling within batches: a single malformed record should fail only itself, not the entire batch.
- Add a pre-import validation pass that scans the entire CSV and reports all errors before a single record is committed; allow the recruiter to fix and re-upload.
- Store import job metadata (`import_id`, `total_requested`, `total_succeeded`, `total_failed`, `error_manifest_s3_key`) in a durable `import_jobs` table for audit.

---

### EC-14: Candidate Profile Merge Conflict

**Failure Mode:** Candidate Jane Doe applies to Job A using `jane.doe@gmail.com` and to Job B three months later using `janedoe.work@gmail.com`. The system creates two separate candidate profiles: Candidate ID 1001 and Candidate ID 1002. A recruiter manually identifies them as the same person and initiates a merge. During the merge, both profiles have conflicting `skills`, `work_history`, and `notes` fields. The merge operation uses a "last write wins" strategy on all fields, overwriting the richer, more complete profile with the less complete one because it has a newer `updated_at` timestamp.

**Impact:** Medium. Loss of candidate history and notes. Recruiter must manually re-enter lost data. Merged candidate's pipeline history is incomplete.

**Detection:**
- Merge operation logs a `profile.merge_conflict` event listing fields where values differ between the two profiles.
- Before committing the merge, the UI presents a field-by-field comparison view, requiring the recruiter to actively choose which value to retain for each conflicting field.

**Mitigation:**
1. Roll back the merge transaction if conflicts were not explicitly resolved.
2. Restore both profiles to `ACTIVE` status from the pre-merge snapshot (use the audit log to reconstruct).
3. Present the recruiter with a manual resolution UI.

**Recovery:**
1. Implement a two-phase merge: Phase 1 — identify and present conflicts; Phase 2 — commit only after all conflicts are resolved.
2. Persist a `merge_snapshot` record before any merge is committed so rollback is possible within 30 days.
3. For structured fields (`work_history`, `education`), use a union strategy by default (retain all entries from both profiles) rather than overwrite.

**Prevention:**
- Never use "last write wins" on structured data during merge; always union list-type fields and flag scalar-type conflicts for human review.
- Surface potential duplicate profiles proactively during application submission so they can be linked before separate records proliferate.
- Store pre-merge snapshots in a `profile_merge_history` table with rollback capability.

---

### EC-15: AI Parsing Service Returns Empty Result for Valid Resume

**Failure Mode:** A candidate uploads a well-formatted, text-rich PDF resume. The AI parsing service (e.g., a custom OpenAI GPT-4-based extractor) is called and returns `{"skills": [], "work_history": [], "education": []}` — an empty but structurally valid JSON response. This occurs due to a prompt timeout on the LLM provider's side where the response was truncated. The platform treats the empty result as a successful parse, stores the empty profile, and the candidate appears in the pipeline with no skills or experience — ranking last in any AI-assisted screening.

**Impact:** High. Qualified candidates appear unqualified in AI-assisted screening. Recruiters relying on AI shortlisting will never see these candidates. Resume preview shows no parsed content.

**Detection:**
- Parsing service validates the output schema post-call: if `skills.length == 0 AND work_history.length == 0 AND education.length == 0`, this is treated as a `PARSE_EMPTY_RESULT` error, not a success.
- A `parse_quality_score` metric (sum of non-empty fields / total expected fields) below 0.3 for a resume longer than 500 words triggers an alert.
- LLM response truncation is detected by checking if the response contains a stop token or was cut off mid-JSON.

**Mitigation:**
1. Mark the application as `PARSE_REVIEW_NEEDED`; do not use empty parse results for ranking.
2. Retry the parse job up to 3 times with exponential backoff.
3. If all retries return empty results, fall back to regex-based keyword extraction as a degraded-mode parser.

**Recovery:**
1. After the LLM provider issue resolves, re-queue all `PARSE_REVIEW_NEEDED` applications for a full parse.
2. Update the parsed profile and recalculate AI ranking for affected candidates.
3. Notify recruiters of any re-ranked candidates who should be reviewed.

**Prevention:**
- Implement a post-parse quality gate: require at least one non-empty field from each of `skills`, `work_history`, and `education` for a resume with more than 300 words before marking parse as complete.
- Use a fallback parser (spaCy NER + regex heuristics) when the primary LLM parser returns an empty result on a file that passes pre-flight size and content checks.
- Set explicit LLM prompt timeout limits and check for truncated responses using a JSON completeness validator.

---

### EC-16: Stage Auto-Move Rule Creates Infinite Loop

**Failure Mode:** A recruiter configures two auto-move rules in the ATS: (1) "When application moves to 'Screening', if score < 50, move to 'Rejected'." (2) A second rule, added by a different admin, reads: "When application moves to 'Rejected', if source = 'auto_move', re-evaluate and move to 'Screening' for manual review." These two rules trigger each other in a cycle. An application enters 'Screening', scores 40, moves to 'Rejected', triggers rule 2, moves back to 'Screening', scores 40 again, moves to 'Rejected' — indefinitely. The event processing loop saturates the stage-transition event queue within minutes.

**Impact:** Critical. Queue saturation blocks stage transitions for all other candidates. Database write throughput is consumed by the looping application. In extreme cases, the auto-move worker crashes due to memory exhaustion from the unbounded event loop.

**Detection:**
- Auto-move rule engine tracks `transition_count` per `application_id` per hour; if count exceeds 10 within a 60-second window, a `rule_loop_detected` alert fires and the rule engine pauses transitions for that application.
- Stage transition event consumer monitors for the same `(application_id, from_stage, to_stage)` tuple appearing more than 3 times in 5 minutes — raises `INFINITE_LOOP_SUSPECTED`.
- SQS queue depth for the stage-transition topic monitored; growth rate > 1,000 messages/minute triggers P1 alert.

**Mitigation:**
1. Immediately halt auto-move processing for the affected `application_id` by setting a `auto_move_locked = true` flag on the application record.
2. Drain the inflated queue by discarding duplicate transition events for the locked application.
3. Identify and disable the conflicting auto-move rules; alert the admin who configured each rule.

**Recovery:**
1. Manually set the application to the correct stage after the loop is broken.
2. Review all auto-move rules for the affected organisation and run a static cycle-detection analysis (graph DFS) across the full rule set.
3. Notify the recruiter of the application's correct status.
4. Restart the auto-move worker after queue depth returns to baseline.

**Prevention:**
- Before saving any new auto-move rule, run a cycle-detection algorithm (DFS on the directed graph of stage → destination stage for all active rules) and reject the rule with an error message if a cycle is detected.
- Implement a circuit breaker on the auto-move engine: any application that triggers more than 5 transitions in 60 seconds is locked and escalated to manual review.
- Add a `max_auto_moves_per_application_per_day` configuration parameter (default: 3) enforced by the rule engine.

---

*Last updated: 2025-01-01 | Owner: Platform Engineering — ATS Squad*
