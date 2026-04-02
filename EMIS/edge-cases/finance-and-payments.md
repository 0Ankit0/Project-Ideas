# Edge Cases — Finance and Payments

Domain-specific failure modes, impact assessments, and mitigation strategies for fee invoicing, payment processing, refunds, and scholarship management.

Edge case IDs in this file are permanent: **EC-FIN-001 through EC-FIN-010**.

---

## EC-FIN-001 — Duplicate Payment Due to Double Webhook Delivery

| Field | Detail |
|---|---|
| **Failure Mode** | Payment gateway (Razorpay/Stripe) delivers the `payment.captured` webhook twice (common for HTTP retry on timeout). EMIS processes both, crediting the invoice twice and creating two `PaymentTransaction` records for the same gateway transaction. |
| **Impact** | Invoice status shows PAID twice. Ledger is double-credited. Refund calculations are incorrect. Manual reconciliation required. |
| **Detection** | Unique constraint on `(gateway_transaction_id, gateway)` in the `PaymentTransaction` table. Second insert raises IntegrityError → API returns 200 OK idempotently (webhook endpoint must always return 200 to stop retries). |
| **Mitigation / Recovery** | (1) Webhook handler checks for existing `PaymentTransaction` with same `gateway_transaction_id` before processing. If found, returns 200 without double-processing. (2) If a duplicate is discovered post-reconciliation, Finance staff can mark the duplicate transaction `VOID` and adjust the ledger via a manual ledger entry with `reason_code='DUPLICATE_GATEWAY_EVENT'`. |
| **Prevention** | Idempotency enforced at both application layer (check before insert) and database layer (unique constraint). All webhook payloads are logged to the `WebhookEventLog` table before processing to enable replay auditing. |

---

## EC-FIN-002 — Payment Initiated but Webhook Never Received

| Field | Detail |
|---|---|
| **Failure Mode** | Student completes payment on the gateway UI. The gateway processes the payment successfully. However, the EMIS webhook endpoint is temporarily unreachable (e.g., brief ALB restart), so the `payment.captured` webhook is never delivered and the invoice remains in PENDING status. |
| **Impact** | Student has paid but EMIS shows outstanding balance. Student is denied enrollment or access. Student contacts support. Manual reconciliation required. |
| **Detection** | Celery Beat job runs hourly: queries all `PaymentTransaction` records in `INITIATED` status older than 30 minutes, polls gateway status API to verify actual transaction state. |
| **Mitigation / Recovery** | (1) Hourly reconciliation job calls `razorpay.payment.fetch(gateway_transaction_id)` and if status = `captured`, triggers the same confirmation workflow as a webhook. (2) Finance staff can also manually trigger reconciliation for a specific invoice from the admin panel. (3) Student can refresh payment status from the portal, which triggers an immediate gateway status poll. |
| **Prevention** | Webhook endpoint is highly available (ALB + multi-task ECS). Gateway webhook retry policy is configured to retry for 72 hours with exponential back-off. |

---

## EC-FIN-003 — Partial Payment Leaving Invoice Incorrectly Marked PAID

| Field | Detail |
|---|---|
| **Failure Mode** | A gateway webhook delivers a partial payment amount (e.g., student pays in two instalments using gateway split functionality). The first webhook sets `invoice.status = PAID` because it matches `total_amount` due to a rounding error in the comparison. |
| **Impact** | Student owes an outstanding balance but is treated as fully paid. Financial reports are understated. Year-end reconciliation discovers the shortfall. |
| **Detection** | Invoice status is computed as: `PAID` only if `amount_paid >= total_amount` (using `Decimal` comparison with 2 dp precision, not floating point). `PARTIALLY_PAID` if `0 < amount_paid < total_amount`. |
| **Mitigation / Recovery** | (1) All monetary comparisons use Python `Decimal` with `ROUND_HALF_UP` and consistent 2 decimal places. (2) If a misclassification is discovered, Finance staff corrects `invoice.status` and creates an AuditLog entry. |
| **Prevention** | All `amount` fields are stored as `DECIMAL(15, 2)` in PostgreSQL. Monetary arithmetic is performed exclusively in Python `Decimal` (never `float`). Unit tests cover rounding edge cases (e.g., amounts like 999.999). |

---

## EC-FIN-004 — Refund Processed After Invoice Re-Opening

| Field | Detail |
|---|---|
| **Failure Mode** | A refund is initiated for invoice INV-001. While the refund is in `PROCESSING` status at the gateway, admin re-opens the invoice and applies additional charges. The refund completes and refunds the full original amount, but the re-opened invoice now has a higher total. |
| **Impact** | Student receives a full refund but still owes the additional charges. Financial records are inconsistent. |
| **Detection** | Refund engine checks invoice status before and after gateway API call within an atomic transaction. |
| **Mitigation / Recovery** | (1) Once a `Refund` record is created with any terminal status, the parent invoice is locked (`invoice.refund_lock = True`): no additional charges can be added to a locked invoice. (2) If additional charges are needed, a new invoice must be created. (3) If conflict is discovered, Finance staff creates a corrective invoice for the delta. |
| **Prevention** | Invoice state machine disallows transition back to DRAFT once a refund has been initiated. The `refund_lock` flag is checked on all invoice-modification endpoints. |

---

## EC-FIN-005 — Scholarship Applied After Invoice Already Paid

| Field | Detail |
|---|---|
| **Failure Mode** | A scholarship is awarded to a student after they have already paid their full fee invoice. The scholarship discount should apply, but the invoice is already marked PAID and the system does not retroactively adjust. |
| **Impact** | Student paid more than they should. No refund is triggered. Student has to contact Finance staff. |
| **Detection** | Scholarship Manager checks `invoice.status` before applying discount. If PAID, marks the scholarship as `PENDING_RETROACTIVE_REFUND`. |
| **Mitigation / Recovery** | (1) Scholarship Manager creates a `ScholarshipCreditNote` record representing the refund owed. (2) Finance staff reviews credit notes in a dedicated queue and initiates the refund via the Refund Engine. (3) Student is notified: "A scholarship has been applied to your account. A refund of INR X will be processed within 5 business days." |
| **Prevention** | Scholarship award workflow includes a step that checks for already-paid invoices and prompts Finance staff to initiate refunds. Scholarships should ideally be awarded before invoice generation. |

---

## EC-FIN-006 — Fee Structure Version Change Mid-Semester

| Field | Detail |
|---|---|
| **Failure Mode** | Admin updates the fee structure (e.g., corrects a lab fee amount) after some invoices for the current semester have already been issued and some students have already paid. |
| **Impact** | Different students are billed different amounts for the same fee head. Students who paid early may have overpaid or underpaid relative to the corrected structure. |
| **Detection** | Fee Structure versioning system: each update creates a new `FeeStructureVersion` record. Existing invoices retain a `fee_structure_version_id` foreign key to their original version. |
| **Mitigation / Recovery** | (1) Version-controlled: already-issued invoices are not retroactively changed. (2) Finance staff can run a "fee revision report" to identify and re-issue invoices for students not yet billed, using the new version. (3) For overpaid/underpaid students, a manual adjustment invoice is created with `reason_code='FEE_STRUCTURE_CORRECTION'`. |
| **Prevention** | Fee structure changes during an active semester require SUPER_ADMIN approval and generate an automatic impact report showing affected uninvoiced students. Fee structure is locked once the first invoice is generated for a semester (changeable only by SUPER_ADMIN with override reason). |

---

## EC-FIN-007 — Payment Gateway Timeout During High Traffic

| Field | Detail |
|---|---|
| **Failure Mode** | During the fee payment deadline day, concurrent gateway API calls exceed Razorpay's rate limit, resulting in timeout errors. `PaymentTransaction` records are left in `INITIATED` state. |
| **Impact** | Students cannot pay on deadline day. If the deadline passes without payment, students incur late fees or academic holds, despite having attempted to pay. |
| **Detection** | Gateway client tracks HTTP 429 and timeout errors in CloudWatch metric `gateway.request.errors`. Alert triggers at > 5% error rate. |
| **Mitigation / Recovery** | (1) Celery worker retries failed gateway calls with exponential back-off (1s, 2s, 4s, 8s, max 5 retries). (2) If all retries fail, `PaymentTransaction.status` is set to `FAILED` and student is notified with a retry prompt. (3) Finance staff can extend payment deadlines by adding grace period days to the invoice due date from the admin panel. |
| **Prevention** | Gateway client implements a circuit breaker pattern (fails fast after 5 consecutive errors, opens for 60 seconds). Fee deadlines are staggered by program to distribute payment traffic. Razorpay rate limits are monitored and account limits increased before semester fee deadlines. |

---

## EC-FIN-008 — Invoice Generated with Incorrect Student Program Year

| Field | Detail |
|---|---|
| **Failure Mode** | Fee structure is program- and year-specific (Year 1 vs Year 4 have different fees). A bulk invoice generation job uses the wrong year (e.g., creates Year-1 invoices for Year-4 students) due to a data mapping error. |
| **Impact** | Students are billed incorrect amounts. Year-4 students may be underbilled (institutional loss) or overbilled (student dispute). |
| **Detection** | Invoice generation job includes a pre-run validation step that prints a fee comparison table (program + year + fee_structure_version + expected_total) for admin review before committing. |
| **Mitigation / Recovery** | (1) Pre-run validation step (dry-run mode) is mandatory before committing bulk invoices. (2) If incorrect invoices are already issued, Finance staff can bulk-void and regenerate using the admin "invoice revision" tool. Void + new invoice notifications are sent to affected students. |
| **Prevention** | `FeeEngine.calculate_total_for_student(student)` derives the student's academic year from `Student.admission_date` and `current_semester_number()`, not from a manually specified parameter. Unit tests cover year-boundary cases. |

---

## EC-FIN-009 — Refund to Closed Bank Account

| Field | Detail |
|---|---|
| **Failure Mode** | Student drops out and requests a refund. The refund is processed to the original bank account / card used for payment, but that account has been closed. Gateway returns a refund failure error. |
| **Impact** | Refund is not delivered. Student's money is in limbo. Student disputes the charge with their bank, potentially triggering a chargeback. |
| **Detection** | Gateway webhook delivers `refund.failed` event. Refund Engine sets `Refund.status = FAILED` and creates a `RefundException` task for Finance staff. |
| **Mitigation / Recovery** | (1) `refund.failed` webhook triggers a Finance staff task: "Contact student for alternate bank details." (2) Student provides new bank account details. (3) Refund is reprocessed via bank transfer (manual gateway action or NEFT). |
| **Prevention** | Refund gateway webhook handlers cover all terminal states: `failed`, `processed`, `pending`. Finance staff are alerted on any `refund.failed` event within 5 minutes via PagerDuty. |

---

## EC-FIN-010 — Financial Hold Not Released After Full Payment

| Field | Detail |
|---|---|
| **Failure Mode** | Student pays the full outstanding invoice. The `payment.confirmed` webhook updates the `PaymentTransaction` and `FeeInvoice` correctly. However, the financial hold on the student's account is not lifted due to a Celery task failure in the `HoldEnforcer.release_hold()` step. |
| **Impact** | Student is still blocked from enrolling even though they have paid in full. Student contacts support. Trust in the payment system is eroded. |
| **Detection** | `HoldEnforcer` task is monitored. Task failure is logged to CloudWatch and triggers an alert. Additionally, the enrollment API's hold-check queries invoice status in real time (not a cached hold flag), so a correctly marked PAID invoice means no hold. |
| **Mitigation / Recovery** | (1) The enrollment service's hold check is the authoritative check: it queries `FeeInvoice.objects.filter(student=student, status=OVERDUE).exists()` in real time. Even if the `hold_flag` is stale, the live invoice query correctly shows no overdue invoices and allows enrollment. (2) Failed hold-release tasks are retried automatically. |
| **Prevention** | Financial hold is not a separate persisted flag — it is derived from live invoice status queries. This eliminates the possibility of a stale hold. Celery task for hold release is idempotent and retried with back-off. |

---

## Operational Policy Addendum

### Academic Integrity Policies
All fee waivers, scholarship applications, and invoice adjustments require Finance Staff or Admin approval and are permanently recorded in AuditLog. No automated job may write off or reduce an invoice amount without human approval via the admin panel.

### Student Data Privacy Policies
Payment details (card numbers, bank account numbers) are never stored in EMIS. Only gateway-assigned tokens and transaction IDs are persisted. PCI DSS compliance is delegated entirely to the payment gateways (Razorpay/Stripe). Refund bank details collected from students are encrypted at rest using KMS and deleted within 30 days of refund completion.

### Fee Collection Policies
Late payment penalties (if applicable) are defined in the FeeStructure as a `LATE_FEE` head and are auto-applied by the Invoice Service on overdue invoices based on the academic calendar. A maximum late-fee cap is configured per program. Waiving late fees requires Finance Staff approval with a documented reason.

### System Availability During Academic Calendar
The Finance and Payment API is classified as Mission-Critical during the 14-day window before and during each semester's fee payment deadline. ECS task counts are pre-scaled. Gateway API rate limits are reviewed and escalated with gateway account managers before every fee deadline period.
