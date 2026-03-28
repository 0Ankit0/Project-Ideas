# C4 Code Diagram

This implementation view maps appointment scheduling code modules, dependencies, and the runtime booking path.

## Code-Level Structure
```mermaid
flowchart TB
  subgraph Interface
    AppointmentController
    AvailabilityController
    CheckinController
  end

  subgraph Application
    AppointmentAppService
    AvailabilityAppService
    ReminderAppService
    CheckinAppService
  end

  subgraph Domain
    AppointmentAggregate
    SlotAggregate
    ReminderPolicy
  end

  subgraph Infrastructure
    AppointmentRepository
    SlotRepository
    ReminderAdapter
    EHRAdapter
    EventPublisher
  end

  AppointmentController --> AppointmentAppService --> AppointmentAggregate
  AvailabilityController --> AvailabilityAppService --> SlotAggregate
  CheckinController --> CheckinAppService --> AppointmentAggregate
  AppointmentAppService --> ReminderAppService --> ReminderPolicy
  AppointmentAppService --> AppointmentRepository
  AvailabilityAppService --> SlotRepository
  ReminderAppService --> ReminderAdapter
  CheckinAppService --> EHRAdapter
  AppointmentAppService --> EventPublisher
```

## Critical Runtime Sequence: Book Appointment
```mermaid
sequenceDiagram
  autonumber
  actor Patient
  participant API as AppointmentController
  participant APP as AppointmentAppService
  participant SLOTS as SlotRepository
  participant REM as ReminderAdapter

  Patient->>API: book appointment
  API->>APP: validate + reserve
  APP->>SLOTS: lock slot
  SLOTS-->>APP: reservation confirmed
  APP->>REM: schedule reminders
  APP-->>API: appointment created
```

## Notes
- Keep slot reservation transactional to avoid double-booking.
- Persist reminder scheduling metadata for reconciliation and retries.
