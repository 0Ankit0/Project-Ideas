# Edge Cases - Progress Tracking

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Learner watches media offline and syncs later | Progress ordering becomes inconsistent | Accept delayed events with idempotent sequence handling |
| Completion rules depend on multiple content types | Learner dashboard may misreport status | Centralize completion evaluation in policy services |
| Learner completes content in multiple tabs or devices | Double-counted or conflicting state | Use versioned progress checkpoints and latest-valid event reconciliation |
| Course content changes after partial completion | Progress percentages drift | Bind progress to course version and translate only through explicit migration rules |
| Attendance data for live sessions arrives late | Certification timing becomes incorrect | Support pending-attendance state before final completion evaluation |


## Implementation Details: Progress Consistency Controls

- Monotonic progress enforced unless corrective admin action is recorded.
- Nightly reconciliation compares activity logs vs projected progress.
- Learner UI displays "processing" state while projection lag exceeds threshold.
