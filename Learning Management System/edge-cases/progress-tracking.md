# Edge Cases — Progress Tracking

> **Scope:** Covers offline sync ordering, event queue backlogs, concurrent device completion, content restructuring, evaluator/UI disagreement, late attendance data, false completion, accidental resets, integer overflow, and nightly reconciliation gaps.

---

## 1. Offline Video Progress Syncs Out of Order

**Failure Mode:** A learner watches 80% of a video on a mobile device while offline. The device reconnects and POSTs progress events with stale timestamps. The event projector receives events in the order: `[95%, 80%, 60%, 40%]` because network retry batches are sent newest-first. The projector applies each event sequentially, leaving the progress record at `60%`.

**Impact:** Learner's progress is understated; if `60% < completion_threshold (70%)`, the lesson is not marked complete and the learner is required to re-watch. Frustration and support tickets follow.

**Detection:**
- Monitor `progress_event_out_of_order` counter; alert if rate exceeds 50/min per tenant.
- Track `progress_record.last_position < progress_event.position` for events applied on top of a higher existing value.
- Learner support ticket keyword cluster: "already watched", "shows incomplete".

**Mitigation/Recovery:**
- Progress projector uses `MAX` semantics: apply an event only if `event.position > current_record.position`; never move progress backward.
- Events include a `device_timestamp` and a `sequence_number`; projector orders events by `sequence_number ASC` before applying.
- Sync endpoint accepts a batch payload sorted by the client; server sorts again by `sequence_number` before projection.

---

## 2. Progress Event Queue Backlog During Peak Hours

**Failure Mode:** At 9:00 AM on a Monday (corporate learning platform), 8,000 learners simultaneously start assigned courses. The progress event queue receives 40,000 events/minute against a worker capacity of 15,000 events/minute. The queue depth grows; events are processed 8–12 minutes late. Completion evaluator reads stale progress and denies certificates.

**Impact:** Completion checks run on stale data; learners who finished a course may be blocked from the next step (e.g., locked module, blocked checkout) for up to 15 minutes. During that window, up to 500 support tickets may be opened.

**Detection:**
- Alert: `progress_queue.lag_seconds > 120` (2-minute SLO breach).
- Dashboard metric: `queue.consumer_lag` per partition graphed against `enrolled_active_users` for correlation.
- Completion evaluation service: log `evaluation_ran_on_stale_data` when the most recent event processed is >120 s old.

**Mitigation/Recovery:**
- Autoscale worker pool based on `queue.lag_seconds`; add workers when lag > 30 s, remove when lag < 10 s.
- Completion evaluation has a "soft re-evaluate" trigger: if a learner requests access to a locked module, re-evaluate their progress in real-time, bypassing the queue lag.
- Apply read-your-writes consistency for the learner's own progress view using a direct DB read rather than the projected store.

---

## 3. Same Lesson Completed Simultaneously on Two Devices

**Failure Mode:** A learner has the same course open on a laptop and a tablet. Both devices hit `POST /progress/lesson/{id}/complete` within 200 ms of each other. Without concurrency control, two `COMPLETED` records are created, and the completion evaluator fires twice, potentially issuing two certificates or two downstream unlock events.

**Impact:** Duplicate certificate records, duplicate grade book entries, duplicate notifications. Cleaning up requires manual deduplication.

**Detection:**
- Alert on `lesson_completion` events where the same `(learner_id, lesson_id)` appears twice within a 5-second window.
- Monitor `duplicate_completion_event` metric; alert on any non-zero count.
- Integrity check: `SELECT learner_id, lesson_id, COUNT(*) FROM lesson_completions GROUP BY 1,2 HAVING COUNT(*) > 1`.

**Mitigation/Recovery:**
- Database unique constraint: `UNIQUE (learner_id, lesson_id, course_version_id)` on `lesson_completions`; second insert returns `409 Conflict`.
- API returns `200 OK` with existing completion record for idempotent duplicate requests.
- Completion evaluator is idempotent: checks `completion_record.id` existence before triggering downstream events (certificate issuance, module unlock).

---

## 4. Course Content Restructure Invalidates Progress Percentages

**Failure Mode:** A course is restructured from 10 lessons to 15 lessons (5 new lessons added). A learner who completed 8/10 lessons (80%) now shows 8/15 (53%) after the restructure, even though their prior work is unchanged. If they need 70% to unlock the next module, they are now blocked.

**Impact:** Learners who were on track for completion may now appear behind; completion-gated modules become inaccessible. Learner confusion and trust erosion.

**Detection:**
- On course version publish: compute `new_completion_pct` for all active learners; alert if `COUNT(*) WHERE new_pct < unlock_threshold AND old_pct >= unlock_threshold > 0`.
- Monitor `module_access_denied` events that spike immediately after a course publish event.

**Mitigation/Recovery:**
- Learners are pinned to the course version they enrolled in; restructuring applies only to new enrollments unless explicitly migrated.
- If migration is required: grandfather existing progress — mark new lessons as `NOT_REQUIRED_FOR_LEGACY_ENROLLMENTS` for learners who enrolled before the restructure.
- Provide admin tool to bulk-grant lesson completion credits for newly added lessons to affected learners, with audit trail.

---

## 5. Completion Evaluator and UI Progress Bar Disagree

**Failure Mode:** The UI progress bar reads from a real-time projection service (Redis) showing 68%. The completion evaluator reads from the authoritative PostgreSQL store and sees 72%, which exceeds the 70% threshold. The learner's module is unlocked in the backend but the UI still shows a locked padlock because the cache has not refreshed.

**Impact:** Learner is confused: they can navigate to the next module via direct URL but the UI shows it as locked. Support tickets around "broken lock" UI are common. Learner may re-do lessons unnecessarily.

**Detection:**
- Monitor `completion_state_mismatch` events: fired when backend state is `UNLOCKED` but UI cache returns `LOCKED` for the same learner+module.
- Alert on `cache_staleness_seconds > 30` for progress projection cache.

**Mitigation/Recovery:**
- On successful completion evaluation, invalidate the learner's progress cache entry immediately (cache-aside invalidation).
- UI polls for progress state with a short TTL (10 s) after any lesson completion event.
- Backend provides `X-Progress-Version` header; UI compares version on each poll and triggers a force refresh on mismatch.

---

## 6. Live Session Attendance Arrives 24 Hours Late

**Failure Mode:** A third-party webinar platform reports attendance data via webhook. Due to a webhook processing delay, attendance records for a 2 PM live session arrive at 2 PM the next day. The certificate issuance job ran at midnight and evaluated completion without the attendance record, so the certificate was not issued.

**Impact:** All learners who attended the live session did not receive their certificate. Certificate issuance must be re-triggered manually for affected learners.

**Detection:**
- Alert if `attendance_record.created_at - session.ended_at > 3600` (attendance arriving >1 h after session end).
- Certificate evaluation job: log `missing_attendance_component` for courses requiring live attendance; set cert status to `PENDING_ATTENDANCE` rather than `FAILED`.

**Mitigation/Recovery:**
- Certificate evaluation uses a `PENDING_ATTENDANCE` state for attendance-dependent courses; re-evaluates when late attendance records arrive.
- Attendance ingestion pipeline: on any new `attendance_record` write, re-trigger completion evaluation for all learners in the associated session.
- Provide instructor the ability to manually confirm attendance for late-arriving or missing records within a 7-day window.

---

## 7. Progress Shows 100% Complete but Required Assessment Not Passed

**Failure Mode:** A learner completes all video lessons (contributing 100% to the progress bar calculation) but has not passed the required end-of-course assessment. The UI shows a green "100% Complete" badge, but the certificate is not issued. The learner believes they have completed the course.

**Impact:** Learner confusion and support escalations. The learner may report a "bug" with certificate issuance when the actual issue is an incomplete assessment requirement.

**Detection:**
- Integrity check: `SELECT enrollment_id FROM enrollments WHERE progress_pct = 100 AND assessment_passed = false AND certificate_issued = false`.
- Alert on `completion_display_mismatch`: `progress_pct = 100` but `course_completion_state != COMPLETE`.

**Mitigation/Recovery:**
- Decouple "lesson progress %" from "course completion status" in the UI: show both a progress bar and a separate "Requirements checklist" showing assessment pass status.
- Progress bar should reflect completion of all required components (lessons + assessments), not just lesson watch percentage.
- Tooltip on the completion badge: "Video lessons complete. Pass the final assessment to earn your certificate."

---

## 8. Learner Progress Reset Accidentally During Admin Migration

**Failure Mode:** During a tenant data migration, an admin script runs `UPDATE progress_records SET completed_lessons = 0 WHERE tenant_id = 'X'` with a typo in the WHERE clause, affecting all tenants. Progress records are zeroed out for 3,200 learners across 15 tenants.

**Impact:** All affected learners lose their progress; course completions are revoked; certificates may be invalidated. Recovery requires restoring from backup, which takes 2–4 hours.

**Detection:**
- Alert on `progress_record.completed_lessons` aggregate dropping by >10% within a 5-minute window (anomalous bulk decrease).
- Audit log alert: `UPDATE` statements on `progress_records` table without a corresponding migration job ID.
- Automated backup integrity check: compare row counts and sum of `completed_lessons` before and after any bulk operation.

**Mitigation/Recovery:**
- All bulk data operations must be run in a transaction with a dry-run mode first; require human review of affected row count before committing.
- Point-in-time recovery (PITR) enabled on progress database; RTO = 4 h, RPO = 5 min.
- After restore, re-apply any progress events from the event log that occurred between the backup timestamp and the incident to minimize data loss.

---

## 9. Time-Spent Counter Wraps on Integer Overflow

**Failure Mode:** The `time_spent_seconds` column in `lesson_progress` is an `INT` (max 2,147,483,647 seconds ≈ 68 years). An automated bot or a learner with an open browser tab for an extremely long session increments the counter past the max, causing it to wrap to a negative value. Downstream duration reports show negative time spent.

**Impact:** Reporting dashboards show negative or nonsensical time-spent values; time-based completion rules (`minimum_time_seconds`) may fire incorrectly.

**Detection:**
- Alert on any `time_spent_seconds < 0` in `lesson_progress`.
- Daily anomaly check: flag any `time_spent_seconds > 86400` (more than 24 hours on a single lesson in a single session) as suspicious.

**Mitigation/Recovery:**
- Change column type to `BIGINT` to push overflow boundary to ~292 billion years.
- Apply a per-session cap: a single progress event cannot contribute more than `max_session_duration_seconds` (configurable, default 8 h) to `time_spent_seconds`.
- Bot detection: flag learner sessions with `time_spent_seconds > 43200` (12 h) for review; suspend automated accounts.

---

## 10. Nightly Reconciliation Finds Gaps Between Event Log and Projection

**Failure Mode:** The nightly progress reconciliation job compares the event log (source of truth) against the progress projection store. It finds 87 learners whose `projection.completed_lessons` is lower than what the event log indicates — events were successfully written to the log but the projection worker crashed before applying them.

**Impact:** 87 learners appear to be incomplete in the projection store; if they need to unlock a module, they may be denied access even though they have actually completed the prerequisites.

**Detection:**
- Nightly reconciliation job: `SELECT learner_id WHERE event_log.max_lesson_count > projection.completed_lessons` — alert if count > 0.
- Monitor `projection_worker_crash` metric; alert on any crash during event application.
- Projection consumer lag: alert if any event is older than 60 s without being applied.

**Mitigation/Recovery:**
- Reconciliation job is a scheduled healer: for each discrepant learner, replay missing events from the log to bring the projection up to date.
- Projection worker uses a checkpoint offset per learner; on restart, replays from the last confirmed checkpoint.
- After reconciliation, re-run completion evaluation for all affected learners to unlock any modules that should have been unlocked.
| Completion rules depend on multiple content types | Learner dashboard may misreport status | Centralize completion evaluation in policy services |
| Learner completes content in multiple tabs or devices | Double-counted or conflicting state | Use versioned progress checkpoints and latest-valid event reconciliation |
| Course content changes after partial completion | Progress percentages drift | Bind progress to course version and translate only through explicit migration rules |
| Attendance data for live sessions arrives late | Certification timing becomes incorrect | Support pending-attendance state before final completion evaluation |


## Implementation Details: Progress Consistency Controls

- Monotonic progress enforced unless corrective admin action is recorded.
- Nightly reconciliation compares activity logs vs projected progress.
- Learner UI displays "processing" state while projection lag exceeds threshold.
