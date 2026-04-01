# Edge Cases — Content Ingestion

> **Scope:** Covers course publication validation, version management, media uploads, SCORM compatibility, deduplication, external resource availability, CDN integrity, lesson deletion, transcoding pipelines, and prerequisite graph integrity.

---

## 1. Author Publishes Course with Missing Required Lesson Metadata

**Failure Mode:** Author calls `POST /courses/{id}/publish` while one or more lessons have `completion_threshold = null` or missing `estimated_duration`. The publish API does not validate nested lesson fields; the course is marked `LIVE` but learners encounter null-pointer errors when the completion evaluator reads the threshold.

**Impact:** All learners enrolled in the course cannot trigger completion for affected lessons. Progress bars freeze; certificates cannot be issued. Requires course to be unpublished, fixed, and re-published — interrupting active learners.

**Detection:**
- Pre-publish validation endpoint: `POST /courses/{id}/validate` must return `200 OK` with empty `errors[]` before `publish` is accepted.
- Alert on `completion_evaluator_error` events where `reason = NULL_THRESHOLD`; correlate to `course_id`.
- Daily scan: `SELECT lesson_id FROM lessons WHERE course_id IN (SELECT id FROM courses WHERE state = 'LIVE') AND completion_threshold IS NULL`.

**Mitigation/Recovery:**
- Block publish at API layer if validation fails; return `422 Unprocessable Entity` with field-level error list.
- Surface validation errors in authoring UI before the publish button becomes active.
- Emergency fix path: allow admin to patch `completion_threshold` on a live lesson without full republish, with change recorded in audit log.

---

## 2. Course Version Updated While Learners Are Mid-Course

**Failure Mode:** Author releases `v2` of a course (restructured modules, removed lessons) while 400 learners are actively progressing through `v1`. Progress records reference `lesson_id` values that no longer exist in `v2`, causing 404s in the progress API and broken resume links.

**Impact:** Up to 400 learners lose their resume-from position; some may be incorrectly shown as incomplete even if they finished the affected lessons under `v1`. Completion certificates already earned may appear to be missing prerequisites.

**Detection:**
- On course version publish: compare new lesson inventory against `progress_records` referencing the previous version; emit `orphaned_progress_count` metric.
- Alert if `orphaned_progress_count > 0` within 5 minutes of a version publish event.
- Monitor 404 rate on `/lessons/{id}/progress` endpoint for lessons belonging to superseded course versions.

**Mitigation/Recovery:**
- Learners who started `v1` remain pinned to `v1` until they explicitly choose to migrate or until the enrollment policy specifies otherwise.
- `course_version_id` is stored on each `enrollment` record; all progress reads and lesson resolution are scoped to that version.
- Provide admin migration tool to move learner progress from `v1` to nearest-equivalent `v2` lesson, with learner notification.

---

## 3. Large Video Upload (>2 GB) Fails or Stalls Mid-Transfer

**Failure Mode:** Author uploads a 3.8 GB lecture video. The HTTP connection times out at the load balancer (default 60 s idle timeout) after 2.1 GB is transferred. The upload service marks the object as incomplete, but the UI shows a spinner indefinitely; the partial upload is never cleaned up.

**Impact:** Author must restart the upload from scratch; wasted storage for the partial object; course publication delayed. Repeated failures block content launch schedules.

**Detection:**
- Track `upload.state` transitions; alert if any upload remains in `IN_PROGRESS` for >30 minutes without a `bytes_received` increment.
- Monitor `upload_failed` events segmented by file size; alert if failure rate for files >1 GB exceeds 5%.
- S3/blob storage lifecycle rule: tag incomplete multipart uploads older than 24 h for cleanup.

**Mitigation/Recovery:**
- Use resumable multipart upload (e.g., S3 Multipart Upload / TUS protocol): split file into 100 MB chunks; each chunk has an independent retry.
- Client retries individual failed chunks up to 3 times with exponential backoff before surfacing an error.
- Provide authors with a "Resume Upload" button that restarts from the last successfully uploaded chunk.
- Run daily cleanup job to abort and delete multipart uploads older than 48 h.

---

## 4. SCORM Package Imports with Incompatible Manifest Version

**Failure Mode:** Author uploads a SCORM 2004 4th Edition package. The import pipeline only supports SCORM 1.2; it parses the manifest partially, creates a course record, but sets incorrect `completion_criterion` and `score_range` values. The course appears imported but completion tracking is broken.

**Impact:** All learners who complete the SCORM activity do not receive credit; the SCORM runtime sends `cmi.completion_status = "completed"` but the LMS ignores it due to mismatched data model field names.

**Detection:**
- Parse `imsmanifest.xml` `schemaversion` attribute on ingest; reject with `400 Bad Request` if version is outside supported range.
- Alert on `scorm_runtime_error` events where `field = "cmi.completion_status"` and `error = "UNKNOWN_FIELD"`.
- Post-import smoke test: simulate completion event and verify `progress_record.state` transitions to `COMPLETED`.

**Mitigation/Recovery:**
- Return clear error on import: `SCORM version '2004 4th Ed' is not supported. Supported versions: SCORM 1.2, SCORM 2004 3rd Ed.`
- For packages that pass import but fail at runtime: expose a manual "Mark Complete" override for instructors per learner.
- Roadmap: add SCORM 2004 4th Edition support behind feature flag; enable per-tenant on request.

---

## 5. Imported Course Duplicates Existing Modules (Deduplication Failure)

**Failure Mode:** A course is imported twice (e.g., from a backup restore and a fresh import). The deduplication logic checks `title` only, missing `external_id` parity checks. Two sets of modules with identical names but different UUIDs are created; learners who completed the first set have no progress credit on the second set.

**Impact:** Catalog becomes polluted with duplicate modules; progress records are fragmented across two sets; reporting shows incorrect completion rates.

**Detection:**
- On import: compute content hash of each module (title + content checksum); warn if hash matches an existing module in the same tenant.
- Post-import report: flag any `module.title` that appears more than once within a course.
- Alert on `duplicate_module_detected` events in the ingestion pipeline.

**Mitigation/Recovery:**
- Import pipeline checks `(course_id, external_id)` uniqueness; if duplicate found, updates existing record rather than creating a new one (upsert semantics).
- Admin deduplication tool: merges two module records, migrating progress records to the canonical module and tombstoning the duplicate.
- Learner notifications sent if their progress was reassigned to the canonical module.

---

## 6. Embedded External Resource Becomes Unavailable Mid-Course

**Failure Mode:** A lesson embeds a YouTube video via `<iframe>`. YouTube removes the video for copyright violation. Learners see "Video unavailable" inside the lesson; if the lesson has `completion_type = MEDIA_WATCH`, they cannot mark it complete.

**Impact:** Affected lesson is permanently blocked for all learners; course completion rates drop; instructor is unaware until learner reports the issue.

**Detection:**
- Nightly external link health check: `HEAD` request to all embedded URLs; alert if status is `404`, `403`, or connection refused.
- Monitor `lesson_completion_error` events with `reason = EXTERNAL_MEDIA_UNAVAILABLE`.
- Alert if the same `lesson_id` generates >10 unique learner error reports within 1 hour.

**Mitigation/Recovery:**
- On link failure detected, set `lesson.external_resource_state = BROKEN`; surface warning to instructors via dashboard.
- Allow instructor to substitute the broken embed with a replacement URL without triggering a full course republish.
- Fallback policy: if `completion_type = MEDIA_WATCH` and external resource is broken, allow learner to self-attest completion pending instructor review.

---

## 7. Content Checksum Mismatch After CDN Distribution

**Failure Mode:** A lesson file (PDF, video) is uploaded with `SHA-256 = abc123`. After CDN edge propagation, a periodic integrity check computes `SHA-256 = def456` for the cached file at one edge node. The corruption may be silent — learners at that edge receive corrupted content.

**Impact:** Learners may download corrupted PDFs or video files; video may not play or show artifacts; quiz content embedded in PDFs may be unreadable.

**Detection:**
- CDN distribution pipeline: compute and store `expected_checksum` at upload time; edge nodes report their stored checksum on cache warm events.
- Scheduled integrity job: sample 5% of edge-served files per hour; alert if `actual_checksum != expected_checksum`.
- Monitor `content_integrity_failure` metric by CDN region and `content_type`.

**Mitigation/Recovery:**
- On mismatch detected, immediately purge CDN cache for the affected asset; force re-fetch from origin.
- Serve affected learners from origin directly while CDN re-propagates (temporary origin-direct header).
- If origin object is also corrupted, restore from versioned blob storage backup.

---

## 8. Author Deletes a Lesson with Existing Learner Progress Records

**Failure Mode:** Author soft-deletes a lesson (`DELETE /lessons/{id}`). The lesson is removed from the course outline, but 120 learners have `progress_records` referencing the deleted `lesson_id`. Their overall course completion percentage drops unexpectedly because the progress records now point to a non-existent lesson.

**Impact:** Learners lose visible progress; course completion percentage decreases; certificates may be revoked if the lesson counted toward completion requirements.

**Detection:**
- Pre-delete check: query `progress_records` for the `lesson_id`; return `409 Conflict` if any records exist with `state != NOT_STARTED`.
- Alert on orphaned progress records: `SELECT COUNT(*) FROM progress_records pr LEFT JOIN lessons l ON pr.lesson_id = l.id WHERE l.id IS NULL AND l.deleted_at IS NULL`.

**Mitigation/Recovery:**
- Block hard deletion of lessons with active progress records; require admin override with explicit acknowledgment.
- On soft-delete: migrate progress records to a `LESSON_DELETED` tombstone state; retain the records for completion calculation continuity.
- Recalculate course completion after deletion, preserving existing learner completion statuses where the deleted lesson was already marked complete.

---

## 9. Media Transcoding Pipeline Failure Causes Lesson to Render Blank

**Failure Mode:** A video is uploaded successfully and stored in origin storage. The transcoding job (HLS/DASH conversion) fails silently — the job is marked `COMPLETE` due to a misconfigured success check, but no output files are produced. The lesson player fetches the (non-existent) HLS manifest and renders a blank player.

**Impact:** All learners accessing the lesson see a blank video player; if the lesson requires media completion, the entire course is blocked for all enrolled learners.

**Detection:**
- Transcoding job completion check: verify output manifest file exists in storage before marking job `COMPLETE`; treat absent manifest as `FAILED`.
- Alert on `video_play_error` events where `error = MANIFEST_NOT_FOUND` affecting more than 2 unique learners within 5 minutes.
- Monitor `transcoding_job.state = COMPLETE AND output_file_count = 0` as a critical alert.

**Mitigation/Recovery:**
- Implement transcoding result validator: check output manifest + at least one segment file exist before publishing lesson as playable.
- Auto-retry transcoding pipeline up to 3 times with exponential backoff on failure.
- Show "Video processing — please check back shortly" placeholder to learners while transcoding is pending or being retried; do not block lesson access.
- Alert content team within 15 minutes of transcoding failure so the video can be re-uploaded if needed.

---

## 10. Course Import Creates Circular Prerequisite Chain

**Failure Mode:** A course import defines module prerequisites: Module A requires Module B, Module B requires Module C, Module C requires Module A. The import pipeline accepts the graph without cycle detection. Learners cannot start any module because each is blocked waiting on another.

**Impact:** The entire imported course is inaccessible to all enrolled learners; no learner can satisfy any prerequisite and thus cannot begin the course.

**Detection:**
- Import pipeline: run topological sort (Kahn's algorithm) on the prerequisite graph; reject import with `422` if a cycle is detected.
- Alert if `prerequisite_graph.has_cycle = true` during post-import validation job.
- Monitor `module_unlock_error` events with `reason = CIRCULAR_PREREQUISITE`.

**Mitigation/Recovery:**
- Reject the import with a descriptive error listing the cycle path: `Circular prerequisite detected: Module A → Module B → Module C → Module A`.
- Provide a prerequisite graph visualizer in the authoring UI so authors can detect cycles before import.
- If a cycle is found in a live course: temporarily mark all modules in the cycle as `PREREQUISITE_OVERRIDE` (unlocked) to unblock learners while instructor resolves the configuration.
| Course content is updated while learners are mid-course | Historical learner state becomes inconsistent | Version courses and pin active learners to stable content snapshots |
| Large media upload stalls or fails | Authoring workflow degrades | Support resumable uploads and background processing states |
| Imported content duplicates existing modules or assessments | Catalog confusion and duplicate grading logic | Provide import deduplication and review workflows |
| Embedded external resource becomes unavailable | Lesson completion becomes blocked | Detect failed embeds and allow fallback links or replacement assets |


## Implementation Details: Ingestion Failure Handling

- Validate package schema, media integrity, and accessibility metadata before publish eligibility.
- Quarantine malformed assets and provide author-facing remediation report.
- Use checksum deduplication for repeated uploads to reduce storage churn.
