# C4 Code Diagram

```mermaid
flowchart TB
  AppointmentController --> AppointmentAppService --> AppointmentAggregate
  AvailabilityController --> AvailabilityAppService --> SlotAggregate
  AppointmentAppService --> ReminderAdapter
  AppointmentAppService --> AppointmentRepository
```
