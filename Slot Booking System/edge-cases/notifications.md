# Edge Cases - Notifications

### 4.1. Missed Reminder Notifications
* **Scenario**: Reminder emails/SMS fail to deliver.
* **Impact**: Higher no-show rates.
* **Solution**:
    * **Monitoring**: Track delivery failures per channel.
    * **Fallback**: Send via secondary channel.

### 4.2. Duplicate Notifications
* **Scenario**: Users receive multiple reminders for one booking.
* **Impact**: User annoyance and confusion.
* **Solution**:
    * **Idempotency**: Store notification send keys.
    * **Scheduling**: Deduplicate jobs in the queue.