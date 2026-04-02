# Edge Cases: Form Builder — Survey and Feedback Platform

**Domain:** `FORM` | **File:** `form-builder.md` | **EC IDs:** EC-FORM-001 through EC-FORM-008

This file documents edge cases encountered in the survey form builder module, which handles question
creation, conditional logic, team collaboration, media attachments, and survey publication. The form
builder is implemented as a FastAPI service backed by PostgreSQL 15 (primary store), Redis 7 (draft
locking and OCC tokens), and S3 (media attachments).

---

## Edge Cases

### EC-FORM-001: Circular Conditional Logic Reference

| Field | Details |
|-------|---------|
| **Failure Mode** | A survey creator builds a conditional logic chain where Question A shows if Question B is answered "Yes", and Question B shows if Question A is answered "Yes". The DFS cycle-detection algorithm fails to run on save (e.g., skipped due to a feature flag misconfiguration), allowing the circular reference to persist. When a respondent encounters the survey, the frontend renderer enters an infinite loop evaluating logic rules, causing the browser tab to hang or crash. |
| **Impact** | High. All respondents accessing the affected survey experience a non-functional form. Survey responses drop to zero for the affected survey. If the survey is part of an active distribution campaign, customer-facing data collection is completely blocked. No data loss occurs (no responses are recorded), but business continuity for that survey is lost until resolved. |
| **Detection** | `LogicValidator.detect_cycles()` raises `CyclicLogicError` and logs to CloudWatch Logs group `/survey-platform/survey-service` with log level ERROR and field `ec_id=EC-FORM-001`. A CloudWatch Metric Filter on this log group emits `CyclicLogicDetected` metric. A CloudWatch Alarm triggers SNS notification to the on-call channel if this metric is > 0 in any 5-minute window. Frontend JS also emits a `logic_loop_detected` analytics event after 50 re-evaluations of the same rule set, visible in CloudWatch RUM. |
| **Mitigation / Recovery** | 1. Identify affected surveys: `SELECT id, title FROM surveys WHERE status = 'published' AND id IN (SELECT DISTINCT survey_id FROM conditional_rules WHERE id IN (SELECT rule_id FROM logic_cycle_audit_log WHERE detected_at > NOW() - INTERVAL '1 hour'));` 2. Auto-pause affected surveys by setting `status = 'paused'` — prevents new respondents from accessing the broken form. 3. Alert the survey creator via email with a link to the logic editor and a description of the cycle. 4. Provide a "Fix Logic Wizard" in the UI that visualises the cycle in a directed graph and suggests which rule to remove. 5. Re-run `LogicValidator.detect_cycles()` after creator fix and re-publish only if no cycles are detected. |
| **Prevention** | (1) **Code-level:** Run DFS cycle detection on every conditional rule save — O(n) where n = number of rules per survey, enforced in `LogicValidator.validate()` before any DB write. (2) **API-level:** The `POST /surveys/{id}/rules` endpoint calls `validate_logic_graph()` as a Pydantic v2 `model_validator`. If a cycle is detected, the API returns HTTP 422 with error code `CYCLIC_LOGIC`. (3) **Infrastructure-level:** Feature flags controlling the logic validator must require explicit approval to disable in production. The flag `logic_cycle_detection_enabled` defaults to `true` and can only be set to `false` via a change-control ticket. (4) **Testing:** A chaos test in the QA suite deliberately introduces a 3-node cycle and asserts that the API returns 422 and no DB write occurs. |

---

### EC-FORM-002: Maximum Question Limit Exceeded During Bulk Import

| Field | Details |
|-------|---------|
| **Failure Mode** | A workspace admin uses the CSV/Excel bulk import feature to add questions to a survey. The import file contains 250 questions but the current plan allows a maximum of 100 questions per survey. The import worker processes all 250 rows, writing them to the database before the constraint check runs (off-by-one in the pre-import validation loop). The survey ends up with 250 questions, violating the plan limit and potentially causing downstream rendering timeouts. |
| **Impact** | Medium. The over-limit survey may render slowly for respondents and trigger OOM in the PDF export worker. Plan enforcement is bypassed, constituting a billing integrity issue. Other surveys in the workspace are unaffected. |
| **Detection** | `POST /surveys/{id}/questions/bulk-import` returns HTTP 201 but the response body includes `questions_imported: 250` while the plan limit is 100. A `PlanLimitExceeded` CloudWatch Metric is emitted with dimensions `survey_id` and `workspace_id`. A nightly audit Lambda (`audit-plan-limits`) queries `SELECT survey_id, COUNT(*) FROM questions GROUP BY survey_id HAVING COUNT(*) > (SELECT question_limit FROM plans WHERE plan_id = (SELECT plan_id FROM workspaces WHERE id = ws_id))` and logs violations to `/survey-platform/audit`. |
| **Mitigation / Recovery** | 1. Immediately set the survey `status = 'draft'` to prevent distribution while over-limit. 2. Notify the workspace admin: "Your survey exceeds the 100-question limit. Please remove X questions or upgrade your plan." 3. Provide a UI tool to bulk-select and delete excess questions. 4. If the workspace upgrades, re-enable the survey after confirming the limit is valid for the new plan. 5. For the DB consistency fix: `DELETE FROM questions WHERE survey_id = $1 AND position > 100 ORDER BY position DESC` (only if admin has not modified questions after import). |
| **Prevention** | (1) **Code-level:** Pre-import validation counts existing questions + import batch size before any DB write: `if existing_count + import_count > plan_limit: raise PlanLimitError(...)`. (2) **API-level:** Add a PostgreSQL check constraint `question_count_within_plan_limit` as a deferred constraint that fires at transaction commit — the DB-level guard is the authoritative enforcement, not the application layer. (3) **Process-level:** The bulk import endpoint enforces chunked processing: it processes up to `plan_limit - existing_count` rows and returns a 400 with `import_truncated: true` if more rows are present. |

---

### EC-FORM-003: Survey Published with Orphaned Logic Rules (Deleted Question Referenced)

| Field | Details |
|-------|---------|
| **Failure Mode** | A survey creator deletes Question 5 from a survey but forgets that a conditional rule references Question 5 as its trigger (`if Q5 == "Yes" then show Q8`). The delete endpoint removes the question record but does not cascade-delete dependent logic rules. When the survey is published and a respondent completes it, the logic engine attempts to evaluate the rule for the deleted question, throws a `KeyError` or `NullReferenceError`, and crashes — the respondent sees an HTTP 500 and cannot submit. |
| **Impact** | High. Respondents in the conditional branch that references the deleted question cannot submit their responses. Depending on how many respondents hit the orphaned rule, this could affect a large percentage of submissions. Survey creators may not notice unless they test all logic paths after editing. |
| **Detection** | The `LogicEngine.evaluate(rules, answers)` method catches `OrphanedRuleError` and logs to `/survey-platform/survey-service` with `ec_id=EC-FORM-003`. The survey service emits a `OrphanedRuleEncountered` custom metric. On publication, the `SurveyPublishValidator` runs `detect_orphaned_rules()` which queries `SELECT cr.id FROM conditional_rules cr LEFT JOIN questions q ON cr.trigger_question_id = q.id WHERE cr.survey_id = $1 AND q.id IS NULL`. |
| **Mitigation / Recovery** | 1. Identify affected surveys with orphaned rules: `SELECT DISTINCT cr.survey_id FROM conditional_rules cr LEFT JOIN questions q ON cr.trigger_question_id = q.id WHERE q.id IS NULL;` 2. Auto-pause active surveys with orphaned rules. 3. Email the creator a list of orphaned rules with their trigger question IDs (even though the question is deleted, the rule's `trigger_question_id` is preserved and can be shown). 4. Delete orphaned rules automatically if the referenced question no longer exists (safe cleanup). 5. Re-run publish validation and restore survey to active. |
| **Prevention** | (1) **Code-level:** The question delete endpoint performs a soft delete first (sets `deleted_at`), then runs `OrphanedRuleDetector.check(survey_id)`. If orphaned rules are found, it returns HTTP 409 with the list of affected rules and requires the creator to confirm deletion or reassign the rules. (2) **DB-level:** Add a `ON DELETE RESTRICT` foreign key from `conditional_rules.trigger_question_id` → `questions.id`, enforced in the migration. If a question deletion would orphan a rule, the DB rejects it. (3) **Publish gate:** The publish API endpoint runs `detect_orphaned_rules()` as a pre-publish check and blocks publication if any orphaned rules exist. |

---

### EC-FORM-004: Concurrent Team Member Edits Race Condition (OCC Conflict)

| Field | Details |
|-------|---------|
| **Failure Mode** | Two team members (Alice and Bob) open the same survey for editing simultaneously. Alice adds Question 6 and saves. Bob, who loaded the survey before Alice's save, also adds a Question 6 with a different title and saves. Bob's save overwrites Alice's Question 6 because the optimistic concurrency control (OCC) version check is implemented incorrectly — it checks the survey-level `updated_at` but not the question-level `version`. Alice's question is silently lost. |
| **Impact** | High. Silent data loss of survey edits. Team members are not notified of the conflict and may not notice until they review the survey. If the lost question was critical (e.g., a mandatory compliance question), the survey may go live with missing content. |
| **Detection** | The OCC conflict is detected at the API layer when `UPDATE surveys SET ... WHERE id = $1 AND version = $2` returns `rowcount = 0` — no row was updated because the version has changed. The API returns HTTP 409 Conflict with `conflict_type: OPTIMISTIC_LOCK_CONFLICT`. If this event is not properly handled by the frontend (e.g., it silently retries), a `SilentOCCBypass` metric is emitted and triggers a CloudWatch alarm. |
| **Mitigation / Recovery** | 1. When HTTP 409 is returned, the frontend fetches the latest survey state from the server. 2. The UI presents a three-way diff: "Your changes", "Their changes", "Original". 3. The user is prompted to merge, discard their changes, or overwrite. 4. If a silent overwrite is detected post-hoc (via audit log), restore the lost version from the survey version history table (`survey_versions`). 5. Send a notification to all collaborators that a conflict occurred and was resolved. |
| **Prevention** | (1) **Code-level:** Implement per-question versioning with ETag headers. Every question has an `etag` field (UUID v4, regenerated on each save). Updates must include `If-Match: <etag>` header; mismatches return 412 Precondition Failed. (2) **Architecture-level:** Use Redis distributed locks (`SET survey:{id}:edit_lock {user_id} NX EX 30`) to warn collaborators when another user is editing. Show "Alice is editing" indicator in the UI. (3) **DB-level:** The `survey_versions` table stores a full JSON snapshot of the survey on every save, enabling rollback. Retain last 50 versions per survey. |

---

### EC-FORM-005: File Upload Question with Malicious MIME Type Bypass

| Field | Details |
|-------|---------|
| **Failure Mode** | A survey includes a file upload question that is configured to accept only images (MIME type `image/jpeg`, `image/png`). An attacker submits a response with a file named `malware.jpg` that is actually a PHP script (content begins with `<?php`). The server-side MIME check reads only the `Content-Type` header from the multipart upload request, which the attacker has set to `image/jpeg`. The actual file content is not inspected. The file is stored in S3 and the pre-signed URL is distributed to the survey creator, who downloads and executes the file. |
| **Impact** | Critical. Malicious file execution risk for survey creators. If the S3 bucket or the file-serving Lambda does not enforce content-type from the stored metadata, and if the creator's machine executes the file, this is a supply-chain attack vector. Additionally, if the uploaded file is an HTML/SVG with embedded JavaScript, it could result in XSS when rendered in-browser via a pre-signed URL. |
| **Detection** | AWS WAF body inspection rule `BlockMaliciousFileUploads` checks the first 8KB of uploaded file content against known magic byte signatures. A `MaliciousUploadAttempt` WAF metric is emitted. Server-side, `magic` library (`python-magic`) inspects the first 1024 bytes of every uploaded file — mismatches between declared MIME and detected MIME are logged to `/survey-platform/api-service` with severity CRITICAL and `ec_id=EC-FORM-005`. |
| **Mitigation / Recovery** | 1. Quarantine the uploaded file: move it from `s3://survey-platform-uploads/responses/` to `s3://survey-platform-quarantine/` using `aws s3 mv`. 2. Mark the response record with `quarantine_reason = 'MIME_TYPE_MISMATCH'` and `status = 'quarantined'`. 3. Alert the security team via PagerDuty P1. 4. Do not distribute the pre-signed URL to the survey creator until the file passes manual review. 5. Scan quarantined files using AWS GuardDuty Malware Protection. 6. If confirmed malicious, delete the file and notify the survey creator that a malicious upload was blocked. |
| **Prevention** | (1) **Code-level:** Use `python-magic` to inspect actual file content bytes, not just the declared MIME type. Reject files where `magic.from_buffer(file_bytes, mime=True)` does not match the allowed MIME list. (2) **S3-level:** Apply S3 Object Lambda to scan every uploaded file with ClamAV (via Lambda function `scan-uploaded-file`) before it is accessible. Files that fail the scan are moved to quarantine and the S3 key is deleted from the primary bucket. (3) **Pre-signed URL policy:** Pre-signed URLs for file upload questions have a 15-minute expiry and include a `Content-Type` condition that must exactly match the allowed MIME type. (4) **Infrastructure-level:** WAF rule with managed rule group `AWSManagedRulesKnownBadInputsRuleSet` blocks known malicious file upload patterns. |

---

### EC-FORM-006: Matrix Question with 50+ Row/Column Combinations (Render Timeout)

| Field | Details |
|-------|---------|
| **Failure Mode** | A survey creator adds a matrix/grid question with 60 rows and 8 columns (480 cells). When a respondent loads the survey on a low-powered mobile device, the React component attempts to render all 480 cells synchronously during the initial paint. On a Snapdragon 450 chipset, this takes 4.8 seconds — the browser's "slow script" dialog appears and the page becomes non-interactive. The respondent abandons the survey. On the server side, the survey JSON serialisation of 480 matrix cells for a large response export also causes a Celery worker to take 45 seconds processing a single response record. |
| **Impact** | Medium. High abandonment rate for surveys containing large matrix questions, specifically on mobile devices (typically 40–60% of respondents). The survey is still functional on desktop. Server-side export latency increases proportionally with matrix size. |
| **Detection** | Frontend: `PerformanceObserver` emits a `long-task` entry (duration > 50ms) to CloudWatch RUM with metric `MatrixRenderLongTask`. If a matrix question renders in > 100ms (measured by `performance.mark()`), the `slow_matrix_render` event is logged. Backend: Celery task duration metric `celery.task.runtime` for `export_survey_responses` exceeds 30 seconds. CloudWatch alarm `CeleryExportTimeout` triggers when P95 task duration > 30s. |
| **Mitigation / Recovery** | 1. For respondents: Implement virtual scrolling for matrix questions (`react-virtual`) — render only visible rows (typically 5–8 at a time). 2. Add a hard limit of 20 rows × 10 columns (200 cells) per matrix question enforced at save time. 3. For existing over-limit surveys: auto-convert them to multiple smaller matrix questions (split at 20-row boundaries) and notify the creator. 4. For the export worker: stream matrix cell data in chunks rather than loading all cells into memory at once. |
| **Prevention** | (1) **API-level:** Enforce `max_rows=20` and `max_columns=10` per matrix question in the Pydantic v2 model `MatrixQuestionCreate`. The API returns HTTP 422 if these limits are exceeded. (2) **UI-level:** The form builder shows a live counter for matrix dimensions and disables the "add row" button when 20 rows are reached, with a tooltip explaining the limit. (3) **Performance testing:** Load test matrix question rendering with 20×10 configuration on a simulated Moto G5 device (Chrome DevTools throttling) in the CI pipeline — assert initial render < 100ms. |

---

### EC-FORM-007: Survey Duplication with Broken S3 Media Attachments

| Field | Details |
|-------|---------|
| **Failure Mode** | A survey creator duplicates an existing survey that contains image attachments on several questions. The duplication endpoint copies the survey metadata and question records in PostgreSQL but copies only the S3 object keys (string references) rather than duplicating the actual S3 objects. When the creator edits the duplicate and deletes an image from a question, the delete operation removes the S3 object at the shared key — also breaking the original survey's image display. Respondents on the original survey then see broken image placeholders. |
| **Impact** | Medium. Image attachments on the original survey are broken, degrading the respondent experience. If the images contain essential question context (e.g., product images in a product feedback survey), responses may be invalid or incomplete because respondents cannot see what they are rating. No data loss of response records, but survey content integrity is compromised. |
| **Detection** | When a response is submitted without viewing an image (tracked via `image_loaded` frontend event), the completion rate for image-bearing questions drops significantly. A CloudWatch custom metric `ImageLoadFailure404` is emitted when the CloudFront distribution returns 404 for any `cdn.surveyplatform.com/media/` path. An alarm fires if this rate exceeds 1% of image requests in a 5-minute window. |
| **Mitigation / Recovery** | 1. Identify surveys with broken image references: `SELECT q.id, q.survey_id, q.image_s3_key FROM questions q WHERE q.image_s3_key IS NOT NULL AND NOT EXISTS (SELECT 1 FROM s3_object_registry WHERE s3_key = q.image_s3_key AND deleted_at IS NULL);` 2. For each broken reference, check if the S3 object still exists via `aws s3 ls s3://survey-platform-media/<key>`. 3. If the original S3 object still exists (not yet deleted), copy it to a new unique key and update the survey's question record. 4. If the S3 object is gone, notify the survey creator to re-upload the image. 5. Place a "missing image" placeholder at the CDN level via a CloudFront Function that returns a 200 with a placeholder image for 404s on `/media/`. |
| **Prevention** | (1) **Code-level:** The survey duplication endpoint performs a deep copy: for each question with an `image_s3_key`, call `s3.copy_object(CopySource=original_key, Bucket=..., Key=new_unique_key)` and stores the new key in the duplicated question. Original and duplicate surveys never share S3 object keys. (2) **S3-level:** Enable S3 Object Versioning on the media bucket. Even if a key is deleted, the version history allows recovery. (3) **DB-level:** Maintain an `s3_object_registry` table that tracks reference counts per S3 key. The delete endpoint decrements the reference count and only issues the S3 delete when `reference_count = 0`. |

---

### EC-FORM-008: Question Position Reorder Collision (Two Users Reorder Simultaneously)

| Field | Details |
|-------|---------|
| **Failure Mode** | Two team members (Alice and Bob) simultaneously drag-and-drop questions in the same survey's form builder. Alice moves Question 3 to position 1. Bob moves Question 1 to position 3. Both clients send `PATCH /surveys/{id}/questions/reorder` with their respective new position arrays within 200ms of each other. The server processes both requests sequentially but without a lock. The last write wins, resulting in a position array that reflects only one user's intent and potentially duplicating position values in the database (`positions = [1, 1, 2, 3, 4]` instead of unique integers). |
| **Impact** | Medium. The survey question order is corrupted — duplicate position values cause non-deterministic question ordering in the respondent view. The creator must manually re-sort questions to fix the order. If not caught before distribution, respondents receive questions in an unintended sequence, which can bias survey responses (question order effect). |
| **Detection** | A unique constraint violation on `(survey_id, position)` in the `questions` table causes a `UniqueConstraintViolation` exception in SQLAlchemy, logged to `/survey-platform/survey-service`. A `PositionReorderConflict` CloudWatch metric is emitted. Additionally, the response validation step for `PATCH /questions/reorder` checks that the submitted position array is a valid permutation of `[1..n]` (no duplicates, no gaps). |
| **Mitigation / Recovery** | 1. When a position collision is detected, the second write is rejected with HTTP 409. 2. The API returns the current authoritative position array in the 409 response body. 3. The frontend merges the current state into its local view and prompts the user: "The question order was updated by another team member. Here is the latest order." 4. To fix corrupted position arrays in the DB: `WITH ranked AS (SELECT id, ROW_NUMBER() OVER (PARTITION BY survey_id ORDER BY position, updated_at) AS new_pos FROM questions WHERE survey_id = $1) UPDATE questions q SET position = r.new_pos FROM ranked r WHERE q.id = r.id;` |
| **Prevention** | (1) **Code-level:** The reorder endpoint acquires a Redis distributed lock (`SET survey:{id}:reorder_lock {request_id} NX EX 5`) before writing position updates. If the lock cannot be acquired within 500ms, return HTTP 423 Locked. (2) **DB-level:** Unique constraint on `(survey_id, position)` ensures the database rejects duplicate positions at the storage layer regardless of application logic. (3) **API design:** The reorder endpoint accepts a full position array (not a delta) and uses a single `UPDATE ... CASE WHEN` query wrapped in a transaction, making the operation atomic. |

---

## Testing Scenarios

The following QA test scenarios can be used to reproduce each edge case in a staging environment:

### EC-FORM-001 Reproduction
1. Create a survey with questions Q1, Q2, Q3.
2. Add rule: "Show Q2 if Q1 answer = Yes".
3. Add rule: "Show Q1 if Q2 answer = Yes".
4. Attempt to save the second rule.
5. **Expected:** API returns HTTP 422 with `error_code: CYCLIC_LOGIC`. Rule is not saved.
6. **Failure indicator:** Rule saves successfully and respondent browser hangs.

### EC-FORM-002 Reproduction
1. Create a workspace on the Free plan (100-question limit).
2. Prepare a CSV import file with 150 rows.
3. POST the file to `POST /surveys/{id}/questions/bulk-import`.
4. **Expected:** API returns HTTP 400 with `import_truncated: true` and imports only 100 questions.
5. **Failure indicator:** All 150 questions are imported.

### EC-FORM-003 Reproduction
1. Create a survey with Q1, Q2, Q3.
2. Add rule: "Show Q3 if Q1 = Yes".
3. Delete Q1 from the survey.
4. **Expected:** API returns HTTP 409 warning about orphaned rule. User must confirm deletion.
5. Attempt to publish the survey after deleting Q1 without removing the rule.
6. **Expected:** Publish blocked with `orphaned_rules_detected` error.

### EC-FORM-004 Reproduction
1. Open the same survey in two browser tabs logged in as different team members.
2. Both click "Add Question" and add a question with the same position.
3. Both click "Save" within 1 second of each other.
4. **Expected:** Second save returns HTTP 409 with diff. No silent overwrite occurs.

### EC-FORM-005 Reproduction
1. Create a survey with a file upload question (allowed types: image/jpeg).
2. Rename a PHP script to `test.jpg`.
3. Submit a response with the renamed file.
4. **Expected:** API returns HTTP 422 with `MIME_TYPE_MISMATCH`. File is not stored in S3.

### EC-FORM-006 Reproduction
1. Create a matrix question with 25 rows and 10 columns.
2. **Expected:** API returns HTTP 422 with `exceeds_matrix_limits`.
3. Create a valid matrix (20 rows × 10 columns) and render on simulated mobile device.
4. **Expected:** Initial render completes in < 100ms using virtual scrolling.

### EC-FORM-007 Reproduction
1. Create a survey with an image attachment on Q1 (`image_s3_key = "media/abc123.jpg"`).
2. Duplicate the survey.
3. On the duplicate, delete the image from Q1.
4. Check the original survey's Q1 image.
5. **Expected:** Original survey image still loads from a different S3 key.
6. **Failure indicator:** Original survey's image returns 404.

### EC-FORM-008 Reproduction
1. Open the same survey form builder in two browser tabs.
2. In Tab 1, drag Q3 to position 1 and click Save.
3. Within 200ms, in Tab 2, drag Q1 to position 3 and click Save.
4. **Expected:** Tab 2 receives HTTP 409 Locked or HTTP 423. No duplicate positions in DB.
5. Verify: `SELECT position, COUNT(*) FROM questions WHERE survey_id = $1 GROUP BY position HAVING COUNT(*) > 1` returns no rows.

---

## Operational Policy Addendum

### 1. Response Data Privacy Policies

Form builder content (question text, logic rules, answer options) is classified as customer content
owned by the workspace. It is not personal data unless the creator deliberately includes PII in
question text (e.g., pre-filled names). PII in question defaults (e.g., hidden fields pre-populated
with respondent email) is encrypted at rest (AES-256-GCM via AWS KMS, key `survey-platform/form-content`).

GDPR Article 25 (Data Protection by Design): The form builder enforces data minimisation by default —
file upload questions show a warning if the creator enables "collect file metadata including device info"
and requires explicit opt-in. CCPA: Survey content is not shared with third parties for advertising purposes.

### 2. Survey Distribution Policies

Surveys created in the form builder are not distributed until explicitly sent by the workspace owner.
Draft surveys are not publicly accessible; all draft endpoints require authentication. Published surveys
with password protection use bcrypt-hashed passwords stored in the `survey_access_controls` table.
Survey links shared externally use short tokens (8-character base62) that do not expose internal UUIDs.

### 3. Analytics and Retention Policies

Form builder audit logs (question added/deleted/reordered, logic rules changed) are retained for 12
months and stored in PostgreSQL `survey_audit_log` table with `actor_id`, `action`, `diff_json`, and
`timestamp`. These logs are available to workspace admins via the audit log API. Audit logs older than
12 months are archived to S3 Glacier. Form builder activity is not included in response analytics.

### 4. System Availability Policies

The survey creation and editing endpoints target 99.9% monthly uptime. Form builder edits are
auto-saved to a Redis draft store every 30 seconds (`survey:{id}:draft:{user_id}`) with a 24-hour TTL,
ensuring at most 30 seconds of unsaved work is lost on unexpected session termination. RTO for form
builder service: 15 minutes. RPO: 30 seconds (Redis draft auto-save interval).
