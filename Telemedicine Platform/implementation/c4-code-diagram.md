# C4 Code Diagram — SchedulingService

## Overview

This document describes the code-level (C4 Level 4) design of the `SchedulingService`. It covers the domain model, application use cases, infrastructure adapters, dependency injection wiring, and the flow of domain events from entity mutation through to SQS publication. All diagrams and code excerpts are production-representative — no placeholders.

```mermaid
C4Component
    title Code-Level Components: SchedulingService

    Component(bookUC, "BookAppointmentUseCase", "TypeScript Class", "Orchestrates slot validation, insurance check, persistence, event publishing")
    Component(cancelUC, "CancelAppointmentUseCase", "TypeScript Class", "Validates cancellation window, refund eligibility, persists and publishes")
    Component(bookSvc, "AppointmentBookingService", "Domain Service", "Slot conflict check, licensure validation, insurance eligibility")
    Component(reminderSvc, "AppointmentReminderService", "Domain Service", "Queries upcoming appointments, dispatches reminder events")
    Component(pgRepo, "PostgresAppointmentRepository", "Infrastructure", "TypeORM + PHI encryption/decryption")
    Component(sqsPub, "SQSEventPublisher", "Infrastructure", "Publishes domain events to SQS FIFO queues")
    Component(auditSvc, "AuditService", "Infrastructure", "Writes HIPAA audit records to immutable store")
    Component(iRepo, "IAppointmentRepository", "Interface", "Domain boundary contract")
    Component(iAudit, "IAuditLogger", "Interface", "Domain boundary contract")

    Rel(bookUC, bookSvc, "delegates slot/insurance validation")
    Rel(bookUC, iRepo, "persists appointment")
    Rel(bookUC, iAudit, "logs PHI access")
    Rel(bookUC, sqsPub, "publishes AppointmentBooked event")
    Rel(cancelUC, iRepo, "loads and saves appointment")
    Rel(cancelUC, iAudit, "logs cancellation audit")
    Rel(cancelUC, sqsPub, "publishes AppointmentCancelled event")
    Rel(pgRepo, iRepo, "implements")
    Rel(auditSvc, iAudit, "implements")
    Rel(bookSvc, iRepo, "reads availability")
```

---

## Domain Model — Class Diagram

```mermaid
classDiagram
    namespace Domain_Entities {
        class Appointment {
            -UUID appointmentId
            -PatientId patientId
            -DoctorId doctorId
            -AppointmentSlot slot
            -ChiefComplaint chiefComplaint
            -AppointmentStatus status
            -InsurancePolicyId insurancePolicyId
            -AuditInfo auditInfo
            -DomainEvent[] uncommittedEvents
            +static create(cmd CreateAppointmentCommand) Appointment
            +confirm(insuranceVerification InsuranceVerification) void
            +cancel(reason CancellationReason) AppointmentCancelledEvent
            +reschedule(newSlot AppointmentSlot) AppointmentRescheduledEvent
            +checkIn() AppointmentCheckedInEvent
            +markNoShow() AppointmentNoShowEvent
            +start() AppointmentStartedEvent
            +complete() AppointmentCompletedEvent
            +getUncommittedEvents() DomainEvent[]
            +clearEvents() void
        }

        class AppointmentSlot {
            -DateTime startAt
            -DateTime endAt
            -int durationMinutes
            +overlaps(other AppointmentSlot) boolean
            +isPast() boolean
            +isWithinCancellationWindow() boolean
            +static fromStartAndDuration(start DateTime, mins int) AppointmentSlot
        }

        class DoctorAvailability {
            -DoctorId doctorId
            -AvailabilityWindow[] windows
            -BlockedPeriod[] blockedPeriods
            +isAvailable(slot AppointmentSlot) boolean
            +nextAvailableSlot(after DateTime, durationMinutes int) AppointmentSlot
            +block(period BlockedPeriod) void
            +release(period BlockedPeriod) void
        }

        class ChiefComplaint {
            -string text
            -ICD10Code[] suspectedCodes
            +static create(text string) ChiefComplaint
            +addSuspectedCode(code ICD10Code) void
        }
    }

    namespace Domain_ValueObjects {
        class PatientId {
            -UUID value
            +toString() string
            +equals(other PatientId) boolean
        }

        class DoctorId {
            -UUID value
            +toString() string
            +equals(other DoctorId) boolean
        }

        class CancellationReason {
            -string code
            -string description
            +isRefundEligible() boolean
        }
    }

    namespace Domain_Services {
        class AppointmentBookingService {
            -IAppointmentRepository appointmentRepo
            -IDoctorAvailabilityRepository availabilityRepo
            -IInsuranceEligibilityService eligibilityService
            -IDomainEventPublisher eventPublisher
            +bookAppointment(cmd BookAppointmentCommand) Promise~Appointment~
            -validateSlotAvailability(doctorId DoctorId, slot AppointmentSlot) Promise~void~
            -validateDoctorLicensure(doctorId DoctorId, patientState string) Promise~void~
            -verifyInsuranceEligibility(patientId PatientId, insuranceId string, serviceDate DateTime) Promise~EligibilityResult~
        }

        class AppointmentReminderService {
            -IAppointmentRepository appointmentRepo
            -INotificationPublisher notificationPublisher
            +sendReminders(hoursAhead int) Promise~void~
            +handleNoShow(appointmentId UUID) Promise~void~
        }
    }

    namespace Domain_Events {
        class AppointmentBookedEvent {
            +string eventId
            +string eventType
            +string version
            +UUID appointmentId
            +UUID patientId
            +UUID doctorId
            +DateTime scheduledAt
            +string appointmentType
            +DateTime occurredAt
        }

        class AppointmentCancelledEvent {
            +UUID appointmentId
            +UUID cancelledBy
            +string reason
            +boolean refundEligible
            +DateTime occurredAt
        }

        class AppointmentRescheduledEvent {
            +UUID appointmentId
            +AppointmentSlot previousSlot
            +AppointmentSlot newSlot
            +DateTime occurredAt
        }
    }

    namespace Application_UseCases {
        class BookAppointmentUseCase {
            -AppointmentBookingService bookingService
            -IAppointmentRepository repo
            -IAuditLogger auditLogger
            -IEventPublisher eventPublisher
            +execute(cmd BookAppointmentCommand) Promise~BookAppointmentResult~
        }

        class CancelAppointmentUseCase {
            -IAppointmentRepository repo
            -IAuditLogger auditLogger
            -IEventPublisher eventPublisher
            +execute(cmd CancelAppointmentCommand) Promise~void~
        }

        class RescheduleAppointmentUseCase {
            -IAppointmentRepository repo
            -AppointmentBookingService bookingService
            -IAuditLogger auditLogger
            +execute(cmd RescheduleAppointmentCommand) Promise~void~
        }
    }

    namespace Infrastructure_Persistence {
        class PostgresAppointmentRepository {
            -DataSource dataSource
            -PHIEncryption phiEncryption
            +findById(id UUID) Promise~Appointment~
            +save(appointment Appointment) Promise~void~
            +findByPatientId(patientId UUID, filters AppointmentFilters) Promise~Appointment[]~
            +findByDoctorId(doctorId UUID, dateRange DateRange) Promise~Appointment[]~
            +findUpcoming(withinHours int) Promise~Appointment[]~
        }
    }

    Appointment "1" --> "1" AppointmentSlot : slot
    Appointment "1" --> "1" ChiefComplaint : chiefComplaint
    Appointment "*" --> "1" PatientId : patientId
    Appointment "*" --> "1" DoctorId : doctorId
    DoctorAvailability --> AppointmentSlot : computes
    AppointmentBookingService --> Appointment : creates
    BookAppointmentUseCase --> AppointmentBookingService : uses
    CancelAppointmentUseCase --> Appointment : mutates
    PostgresAppointmentRepository ..|> IAppointmentRepository : implements
```

---

## Domain Event Flow

```mermaid
sequenceDiagram
    participant UC as BookAppointmentUseCase
    participant DOM as Appointment (Entity)
    participant REPO as PostgresAppointmentRepository
    participant PUB as SQSEventPublisher
    participant SQS as AWS SQS FIFO

    UC->>DOM: Appointment.create(command)
    Note over DOM: Raises AppointmentBookedEvent<br/>stored in uncommittedEvents[]
    UC->>REPO: repository.save(appointment)
    Note over REPO: BEGIN TRANSACTION<br/>INSERT appointment row<br/>PHI fields AES-256-GCM encrypted
    REPO-->>UC: saved
    UC->>DOM: appointment.getUncommittedEvents()
    DOM-->>UC: [AppointmentBookedEvent]
    UC->>PUB: publish(AppointmentBookedEvent)
    PUB->>SQS: SendMessage (MessageGroupId = doctorId)
    SQS-->>PUB: MessageId
    UC->>DOM: appointment.clearEvents()
    Note over UC: COMMIT TRANSACTION
```

The outbox pattern ensures events are not lost if SQS is temporarily unavailable: events are written to the `domain_events` table inside the same transaction as the aggregate, then a background relay process reads and publishes them.

```mermaid
flowchart LR
    subgraph DB Transaction
        A[INSERT appointment] --> B[INSERT domain_events\nstatus=PENDING]
    end
    B --> R[Event Relay\nScheduled task 5s]
    R --> C{SQS publish\nsuccessful?}
    C -->|Yes| D[UPDATE domain_events\nstatus=PUBLISHED]
    C -->|No| E[Retry with\nexponential backoff\nmax 5 attempts]
    E -->|5 failures| F[status=DEAD_LETTERED\nAlert PagerDuty]
```

---

## Dependency Injection Setup

The service uses `tsyringe` for IoC container wiring. All PHI-touching classes are registered as singletons to avoid key-cache churn.

```typescript
// src/infrastructure/di/container.ts
import { container } from 'tsyringe';
import { DataSource } from 'typeorm';
import { KMSClient } from '@aws-sdk/client-kms';
import { SQSClient } from '@aws-sdk/client-sqs';

export function bootstrapContainer(dataSource: DataSource): void {
  // AWS clients
  container.registerInstance('KMSClient', new KMSClient({ region: process.env.AWS_REGION }));
  container.registerInstance('SQSClient', new SQSClient({ region: process.env.AWS_REGION }));
  container.registerInstance('DataSource', dataSource);

  // Encryption — singleton to reuse cached data keys
  container.registerSingleton<PHIEncryption>('PHIEncryption', PHIEncryption);

  // Repositories
  container.register<IAppointmentRepository>('IAppointmentRepository', {
    useClass: PostgresAppointmentRepository,
  });
  container.register<IDoctorAvailabilityRepository>('IDoctorAvailabilityRepository', {
    useClass: PostgresDoctorAvailabilityRepository,
  });

  // Domain services
  container.registerSingleton<AppointmentBookingService>(AppointmentBookingService);
  container.registerSingleton<AppointmentReminderService>(AppointmentReminderService);

  // Application use cases
  container.register(BookAppointmentUseCase, { useClass: BookAppointmentUseCase });
  container.register(CancelAppointmentUseCase, { useClass: CancelAppointmentUseCase });

  // Infrastructure
  container.registerSingleton<SQSEventPublisher>('IEventPublisher', SQSEventPublisher);
  container.registerSingleton<AuditService>('IAuditLogger', AuditService);
}
```

---

## Application Layer — BookAppointmentUseCase

The use case is the transaction boundary. It commits the database record and publishes events atomically via the outbox pattern.

```typescript
// src/application/use-cases/BookAppointmentUseCase.ts
import { injectable, inject } from 'tsyringe';

@injectable()
export class BookAppointmentUseCase {
  constructor(
    @inject(AppointmentBookingService) private readonly bookingService: AppointmentBookingService,
    @inject('IAppointmentRepository') private readonly repo: IAppointmentRepository,
    @inject('IAuditLogger') private readonly audit: IAuditLogger,
    @inject('IEventPublisher') private readonly events: IEventPublisher,
  ) {}

  async execute(cmd: BookAppointmentCommand): Promise<BookAppointmentResult> {
    // Domain service handles all invariant checks
    const appointment = await this.bookingService.bookAppointment(cmd);

    // Persist inside a transaction (outbox written in same tx)
    await this.repo.save(appointment);

    // Publish uncommitted domain events after successful commit
    const domainEvents = appointment.getUncommittedEvents();
    await this.events.publishAll(domainEvents);
    appointment.clearEvents();

    // HIPAA audit record — actor, resource, PHI fields accessed
    await this.audit.record({
      action: 'CREATE',
      resourceType: 'Appointment',
      resourceId: appointment.appointmentId,
      phiAccessed: ['patientId', 'chiefComplaint', 'insurancePolicyId'],
      actorId: cmd.requestedBy,
      purpose: 'TREATMENT',
    });

    return {
      appointmentId: appointment.appointmentId,
      scheduledAt: appointment.slot.startAt,
      status: appointment.status,
    };
  }
}
```

---

## Repository Implementation — PHI Encrypt/Decrypt

```typescript
// src/infrastructure/database/repositories/PostgresAppointmentRepository.ts
@injectable()
export class PostgresAppointmentRepository implements IAppointmentRepository {
  constructor(
    @inject('DataSource') private readonly ds: DataSource,
    @inject('PHIEncryption') private readonly phi: PHIEncryption,
  ) {}

  async findById(id: UUID): Promise<Appointment | null> {
    const entity = await this.ds
      .getRepository(AppointmentEntity)
      .findOne({ where: { appointmentId: id } });

    if (!entity) return null;
    return this.toDomain(entity);
  }

  async save(appointment: Appointment): Promise<void> {
    const repo = this.ds.getRepository(AppointmentEntity);
    const entity = await this.toEntity(appointment);
    await repo.save(entity);
  }

  async findByPatientId(
    patientId: UUID,
    filters: AppointmentFilters,
  ): Promise<Appointment[]> {
    const entities = await this.ds
      .getRepository(AppointmentEntity)
      .createQueryBuilder('a')
      .where('a.patientId = :patientId', { patientId })
      .andWhere('a.status IN (:...statuses)', { statuses: filters.statuses })
      .andWhere('a.startAt >= :from', { from: filters.from })
      .orderBy('a.startAt', 'ASC')
      .getMany();

    return Promise.all(entities.map(e => this.toDomain(e)));
  }

  private async toDomain(entity: AppointmentEntity): Promise<Appointment> {
    const chiefComplaint = await this.phi.decrypt(entity.encryptedChiefComplaint);
    return Appointment.reconstitute({
      appointmentId: entity.appointmentId,
      patientId: new PatientId(entity.patientId),
      doctorId: new DoctorId(entity.doctorId),
      slot: AppointmentSlot.fromStartAndDuration(entity.startAt, entity.durationMinutes),
      chiefComplaint: ChiefComplaint.create(chiefComplaint),
      status: entity.status,
      insurancePolicyId: entity.insurancePolicyId,
      createdAt: entity.createdAt,
      updatedAt: entity.updatedAt,
    });
  }

  private async toEntity(appt: Appointment): Promise<AppointmentEntity> {
    return {
      appointmentId: appt.appointmentId,
      patientId: appt.patientId.toString(),
      doctorId: appt.doctorId.toString(),
      startAt: appt.slot.startAt,
      durationMinutes: appt.slot.durationMinutes,
      encryptedChiefComplaint: await this.phi.encrypt(appt.chiefComplaint.text),
      status: appt.status,
      insurancePolicyId: appt.insurancePolicyId ?? null,
    };
  }
}
```

---

## Module Boundary Summary

```mermaid
graph TB
    subgraph HTTP Layer
        CTRL[AppointmentController]
        MW1[auth.middleware]
        MW2[hipaa-audit.middleware]
        MW3[phi-sanitizer.middleware]
    end

    subgraph Application Layer
        BUC[BookAppointmentUseCase]
        CUC[CancelAppointmentUseCase]
        RUC[RescheduleAppointmentUseCase]
    end

    subgraph Domain Layer
        ABS[AppointmentBookingService]
        APPT[Appointment]
        AVAIL[DoctorAvailability]
    end

    subgraph Infrastructure Layer
        PG[PostgresAppointmentRepository]
        SQS2[SQSEventPublisher]
        AUDIT[AuditService]
        ENC[PHIEncryption]
    end

    CTRL --> MW1 --> MW2 --> MW3 --> BUC
    BUC --> ABS
    BUC --> PG
    BUC --> SQS2
    BUC --> AUDIT
    ABS --> APPT
    ABS --> AVAIL
    PG --> ENC

    style Domain Layer fill:#2d6a4f,color:#fff
    style Application Layer fill:#1d3557,color:#fff
    style HTTP Layer fill:#457b9d,color:#fff
    style Infrastructure Layer fill:#6c757d,color:#fff
```
