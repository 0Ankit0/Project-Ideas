# Edge Cases - Notifications

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Learner receives duplicate reminders | Noise and reduced trust | Use deduplication keys and send-history checks |
| Grade published before feedback artifacts are ready | Learner sees incomplete outcome | Delay learner notification until publication bundle is complete |
| Tenant disables some channels mid-course | Message delivery becomes inconsistent | Respect tenant-level preferences with fallback-channel rules |
| Live session rescheduled close to start time | Learners miss session | Escalate urgent schedule-change notifications across multiple channels |
| Certificate issued but notification provider fails | Learner unaware of completion | Retry asynchronously and surface in-app status regardless of email delivery |


## Implementation Details: Notification Reliability

- Notification intent is written transactionally before provider dispatch.
- Deduplicate sends by recipient+template+context hash over policy window.
- For provider outages, show in-app fallback notices for critical events.
