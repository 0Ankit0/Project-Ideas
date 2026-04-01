# Code Guidelines — Legal Case Management System

## General Principles

### Clean Code & Readability

Every module in this system handles sensitive legal data — privileged communications, financial trust accounts, and court-deadline-critical workflows. Code must be readable, intentional, and auditable by a third party (including bar counsel, auditors, and regulators).

- Name classes, methods, and variables after the **domain concept** they represent, not the technical operation they perform. Prefer `openMatter()` over `createRecord()`, `recordTimeEntry()` over `insertRow()`.
- Keep methods focused on a single responsibility. If a method name requires the word "and", split it.
- Avoid boolean parameter flags. Use named factory methods or separate methods per intent.
- Prefer explicit over implicit — no magic strings, no silent defaults on financial or privilege-tagged fields.

```java
// BAD — implicit default, magic string
matter.setStatus("active");

// GOOD — domain enum, explicit intent
matter.transition(MatterStatus.ACTIVE, auditContext);
```

### SOLID in a Legal Domain Context

| Principle | Domain Application |
|---|---|
| Single Responsibility | `MatterDomainService` handles business rules; `MatterRepository` handles persistence only |
| Open/Closed | Add new billing codes by extending `UTBMSCodeRegistry`, not modifying invoice logic |
| Liskov Substitution | All `LedgerEntry` subtypes (trust, operating) must honour debit/credit invariants |
| Interface Segregation | `IPrivilegeFilter` is separate from `IDocumentStore` — callers should not depend on both |
| Dependency Inversion | Services depend on repository interfaces, not concrete ORM classes |

### Domain-Driven Design

The system is organised into bounded contexts. Each context owns its data and exposes a published API to other contexts. Cross-context reads go through anti-corruption layer adapters — never direct database joins.

```
Bounded Contexts:
├── Matter Management       (core)
├── Document Management     (core)
├── Time & Billing          (core)
├── IOLTA Trust Accounting  (supporting — highest compliance risk)
├── Court Calendar          (supporting)
├── Client Portal           (generic)
└── Identity & Access       (generic)
```

Aggregates enforce invariants. Only the aggregate root may be referenced by other aggregates. Use domain events to communicate across bounded contexts.

---

## Attorney-Client Privilege Data Handling

### PrivilegeClassification Enum

Every document, note, communication, and email stored in the system must carry a `PrivilegeClassification`. This is set at creation time and is **immutable after assignment** except by a privileged role with an explicit justification recorded in the audit log.

```java
public enum PrivilegeClassification {
    NOT_PRIVILEGED,          // Publicly shareable, no restriction
    WORK_PRODUCT,            // Attorney work product doctrine
    ATTORNEY_CLIENT,         // Full AC privilege, client + attorney only
    JOINT_DEFENCE,           // Shared privilege among co-defendants/co-plaintiffs
    COMMON_INTEREST,         // Common interest doctrine
    HIGHLY_CONFIDENTIAL      // Trade secrets or sensitive business info on top of privilege
}
```

Tag every document entity at the domain level:

```java
@Entity
public class MatterDocument {
    @Id private UUID id;
    private UUID matterId;
    private String title;

    @Column(nullable = false)
    @Enumerated(EnumType.STRING)
    private PrivilegeClassification privilegeClassification;

    @Column(nullable = false)
    private boolean markedForPrivilegeLog;

    // Never expose raw bytes through this entity — use DocumentContentService
}
```

### Privilege-Aware Query Filters

Query methods **must never** return privileged documents to roles that lack privilege access. This is enforced at the repository layer, not the controller layer, so that programmatic callers cannot bypass the restriction.

```java
public interface MatterDocumentRepository {

    // Privilege filter is mandatory — compiler enforces it
    List<MatterDocument> findByMatter(
        UUID matterId,
        PrivilegeFilter privilegeFilter
    );
}

public class PrivilegeFilter {
    private final Set<PrivilegeClassification> allowedClassifications;

    public static PrivilegeFilter forRole(UserRole role) {
        return switch (role) {
            case CLIENT        -> new PrivilegeFilter(Set.of(PrivilegeClassification.NOT_PRIVILEGED));
            case PARALEGAL     -> new PrivilegeFilter(Set.of(
                                    PrivilegeClassification.NOT_PRIVILEGED,
                                    PrivilegeClassification.WORK_PRODUCT));
            case ATTORNEY      -> new PrivilegeFilter(EnumSet.allOf(PrivilegeClassification.class));
            case OPPOSING_COUNSEL -> new PrivilegeFilter(Set.of(PrivilegeClassification.NOT_PRIVILEGED));
        };
    }
}
```

Repository implementation applies the filter as a SQL `WHERE` clause predicate — never filtered in memory after a full fetch:

```java
@Override
public List<MatterDocument> findByMatter(UUID matterId, PrivilegeFilter filter) {
    return em.createQuery("""
        SELECT d FROM MatterDocument d
        WHERE d.matterId = :matterId
          AND d.privilegeClassification IN :allowed
        ORDER BY d.createdAt DESC
        """, MatterDocument.class)
        .setParameter("matterId", matterId)
        .setParameter("allowed", filter.getAllowedClassifications())
        .getResultList();
}
```

### Privilege Log Auto-Generation

Federal and state courts require a privilege log listing every withheld document when privilege is asserted. Generate this automatically at discovery-request time by querying documents tagged `markedForPrivilegeLog = true`.

```java
@Service
public class PrivilegeLogService {

    public PrivilegeLog generateForMatter(UUID matterId, LocalDate asOfDate) {
        List<MatterDocument> withheld = documentRepository.findPrivilegeLogCandidates(
            matterId, asOfDate
        );

        List<PrivilegeLogEntry> entries = withheld.stream()
            .map(doc -> PrivilegeLogEntry.builder()
                .documentId(doc.getId())
                .title(doc.getTitle())                        // not content
                .classification(doc.getPrivilegeClassification())
                .authorRole(doc.getAuthorRole())
                .createdDate(doc.getCreatedAt().toLocalDate())
                .basisForPrivilege(narrativeBasis(doc.getPrivilegeClassification()))
                .build())
            .toList();

        auditService.record(AuditEventType.PRIVILEGE_LOG_GENERATED,
            Map.of("matterId", matterId, "entryCount", entries.size()));

        return new PrivilegeLog(matterId, asOfDate, entries);
    }

    private String narrativeBasis(PrivilegeClassification c) {
        return switch (c) {
            case ATTORNEY_CLIENT  -> "Communication made in confidence between attorney and client for purpose of legal advice.";
            case WORK_PRODUCT     -> "Document prepared by or at direction of counsel in anticipation of litigation.";
            case JOINT_DEFENCE    -> "Communication shared under joint defence agreement among co-parties.";
            default               -> "Withheld on applicable privilege grounds.";
        };
    }
}
```

---

## Audit Trail Implementation

### Event Sourcing for Matter and TimeEntry Aggregates

Matters and time entries are audit-sensitive aggregates. Rather than updating rows in place, all state changes are stored as an immutable sequence of domain events. The current state is derived by replaying events (or from a snapshot cache).

```java
public sealed interface MatterEvent permits
    MatterOpened, MatterStatusChanged, MatterClientAssigned,
    MatterClosedWithReason, MatterReopened, ConflictCheckRecorded {

    UUID matterId();
    Instant occurredAt();
    String performedByUserId();
}

public record MatterStatusChanged(
    UUID matterId,
    MatterStatus from,
    MatterStatus to,
    String reason,
    Instant occurredAt,
    String performedByUserId
) implements MatterEvent {}
```

### AuditEntry Schema and Interceptor

All domain events are persisted to a dedicated `audit_log` table via an `AuditInterceptor` that fires on every command handler completion. The table is append-only — no `UPDATE` or `DELETE` statements are ever issued against it.

```sql
CREATE TABLE audit_log (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type    TEXT        NOT NULL,
    aggregate_id  UUID        NOT NULL,
    aggregate_type TEXT       NOT NULL,
    performed_by  TEXT        NOT NULL,
    occurred_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload       JSONB       NOT NULL,
    ip_address    INET,
    session_id    TEXT
);

-- Prevent any modification after insert
CREATE RULE no_update_audit AS ON UPDATE TO audit_log DO INSTEAD NOTHING;
CREATE RULE no_delete_audit AS ON DELETE TO audit_log DO INSTEAD NOTHING;
```

```java
@Aspect
@Component
public class AuditInterceptor {

    @AfterReturning(pointcut = "@annotation(Audited)", returning = "result")
    public void captureAuditEvent(JoinPoint joinPoint, Object result) {
        AuditContext ctx = AuditContextHolder.current();
        auditRepository.append(AuditEntry.builder()
            .eventType(ctx.getEventType())
            .aggregateId(ctx.getAggregateId())
            .aggregateType(ctx.getAggregateType())
            .performedBy(ctx.getUserId())
            .occurredAt(Instant.now())
            .payload(ctx.getPayload())
            .ipAddress(ctx.getIpAddress())
            .build());
    }
}
```

### Immutable Audit Log Storage

- The `audit_log` table must have `NO INHERITS`, no foreign keys that cascade deletes, and no triggers that modify rows.
- Grant `INSERT` only to the application role on `audit_log`. Revoke `UPDATE` and `DELETE`.
- Rotate to cold storage (S3 Glacier) after 90 days using a read-only archival job — never truncate.
- For compliance with 7-year retention requirements, write an annual hash manifest of all audit entries to a write-once S3 bucket with Object Lock.

---

## IOLTA Trust Accounting Compliance Patterns

IOLTA (Interest on Lawyer Trust Accounts) accounts are regulated by state bars. Commingling firm funds with client funds is professional misconduct. Every financial operation must be traceable, reversible only by a correcting journal entry, and subject to three-way reconciliation.

### Double-Entry Ledger Pattern

Every financial transaction posts two ledger entries — a debit and a credit — that must net to zero. This is enforced at the domain layer before persistence.

```java
public class IOLTATransaction {

    public static IOLTATransaction clientDeposit(
        UUID clientId, UUID matterId, Money amount, String description
    ) {
        var debit  = LedgerEntry.debit(Account.IOLTA_BANK, amount);
        var credit = LedgerEntry.credit(Account.clientLiability(clientId), amount);
        validateBalance(debit, credit);
        return new IOLTATransaction(clientId, matterId, List.of(debit, credit), description);
    }

    public static IOLTATransaction disbursementToFirm(
        UUID clientId, UUID matterId, Money earnedAmount, String description
    ) {
        var debit  = LedgerEntry.debit(Account.clientLiability(clientId), earnedAmount);
        var credit = LedgerEntry.credit(Account.OPERATING_REVENUE, earnedAmount);
        validateBalance(debit, credit);
        return new IOLTATransaction(clientId, matterId, List.of(debit, credit), description);
    }

    private static void validateBalance(LedgerEntry debit, LedgerEntry credit) {
        if (!debit.amount().equals(credit.amount()))
            throw new LedgerImbalanceException("Debit and credit amounts must match.");
    }
}
```

### Three-Way Reconciliation

State bar rules require monthly three-way reconciliation: bank statement balance must equal total client ledger balances must equal trust ledger balance.

```java
public record ThreeWayReconciliation(
    YearMonth period,
    Money bankStatementBalance,
    Money totalClientLedgerBalance,
    Money trustLedgerBalance,
    boolean isBalanced,
    List<ReconciliationDiscrepancy> discrepancies
) {
    public static ThreeWayReconciliation compute(
        BankStatementService bank,
        ClientLedgerService clientLedger,
        TrustLedgerService trustLedger,
        YearMonth period
    ) {
        var bankBal   = bank.endingBalance(period);
        var clientBal = clientLedger.totalAllClients(period);
        var trustBal  = trustLedger.endingBalance(period);
        var balanced  = bankBal.equals(clientBal) && clientBal.equals(trustBal);
        return new ThreeWayReconciliation(period, bankBal, clientBal, trustBal,
            balanced, balanced ? List.of() : detectDiscrepancies(bank, clientLedger, period));
    }
}
```

### Overdraft Prevention with Optimistic Locking

A client's IOLTA sub-account **must never go negative**. Enforce this with a database-level check constraint and application-level optimistic locking.

```java
@Entity
public class ClientTrustBalance {
    @Id private UUID clientId;
    @Version private long version;   // optimistic lock

    @Column(nullable = false)
    private Money balance;

    public void debit(Money amount) {
        if (balance.isLessThan(amount))
            throw new IOLTAOverdraftException(
                "Disbursement of %s would overdraft trust balance of %s for client %s"
                .formatted(amount, balance, clientId));
        this.balance = balance.subtract(amount);
    }
}
```

```sql
ALTER TABLE client_trust_balance
  ADD CONSTRAINT chk_no_overdraft CHECK (balance_cents >= 0);
```

If an `OptimisticLockException` is caught, the operation must **fail and surface an error** — never silently retry, as a concurrent disbursement may have legitimately consumed the funds.

---

## API Design Standards

### RESTful Resource Naming

| Resource | Endpoint Pattern |
|---|---|
| Matters | `GET /api/v1/matters`, `POST /api/v1/matters` |
| Single matter | `GET /api/v1/matters/{matterId}` |
| Matter documents | `GET /api/v1/matters/{matterId}/documents` |
| Time entries | `POST /api/v1/matters/{matterId}/time-entries` |
| Trust ledger | `GET /api/v1/trust/clients/{clientId}/ledger` |

### Versioning

Version via URI path prefix (`/api/v1/`). Maintain at least one prior version during deprecation windows (minimum 90 days notice). Breaking changes require a new major version.

### Standard Error Response Format

All errors return a consistent envelope:

```json
{
  "error": {
    "code": "MATTER_NOT_FOUND",
    "message": "Matter with ID abc-123 does not exist or you lack access.",
    "traceId": "7f3a2b19-...",
    "timestamp": "2025-01-15T10:30:00Z",
    "details": []
  }
}
```

Never expose stack traces, internal class names, or SQL in error responses.

---

## Security Coding Standards

### Input Validation

Use a validation library (Bean Validation / Hibernate Validator) declared on the DTO, not inside service methods:

```java
public record OpenMatterRequest(
    @NotBlank @Size(max = 255) String matterName,
    @NotNull UUID clientId,
    @NotNull @Valid PracticeArea practiceArea,
    @DecimalMin("0.00") @Digits(integer=8, fraction=2) BigDecimal estimatedValue
) {}
```

### SQL Injection Prevention

- Always use parameterised queries or the JPA criteria API.
- Ban `String.format()` or concatenation in any method that constructs a query string. Enforce with an ArchUnit rule.
- Never build dynamic `ORDER BY` columns from user input without an allowlist.

```java
// BANNED — string interpolation in query
String q = "SELECT * FROM matters WHERE client_name = '" + name + "'";

// REQUIRED — named parameter binding
em.createQuery("SELECT m FROM Matter m WHERE m.clientName = :name")
  .setParameter("name", name);
```

### Secrets Management

- All secrets (DB passwords, API keys for Stripe, DocuSign, court e-filing APIs) are stored in AWS Secrets Manager or HashiCorp Vault.
- No secrets in environment variables, application properties files, or code.
- Rotate credentials automatically; the application retrieves secrets at startup and re-fetches on `SecretRotationEvent`.
- Fail-fast at boot if any required secret is missing — do not start with degraded security.

---

## Testing Standards

### Unit Tests

Test domain logic in isolation. No Spring context, no database, no HTTP calls.

```java
@Test
void should_reject_disbursement_exceeding_trust_balance() {
    var balance = new ClientTrustBalance(CLIENT_ID, Money.of(500, USD));
    assertThrows(IOLTAOverdraftException.class,
        () -> balance.debit(Money.of(600, USD)));
}
```

Coverage target: **≥ 90%** on all domain aggregate and service classes.

### Integration Tests

Use Testcontainers for PostgreSQL and LocalStack for AWS services. Each test class owns its data setup and tears down after itself.

```java
@SpringBootTest
@Testcontainers
class MatterRepositoryIntegrationTest {
    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16");
    // ...
}
```

### Contract Tests

Use Pact for consumer-driven contract testing between bounded contexts. The `BillingService` consuming `MatterService` events must publish and verify a Pact contract before any `MatterEvent` schema change is merged.

```
contracts/
├── billing-consumer-matter-provider.json
├── portal-consumer-matter-provider.json
└── calendar-consumer-matter-provider.json
```

All three contract types (unit, integration, contract) must pass in CI before a PR is mergeable. No exceptions for "minor" changes to financial or privilege-handling code.
