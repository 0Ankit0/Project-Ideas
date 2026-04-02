# Edge Cases — Payments & Fees

This document catalogues edge cases specific to the payment and fee-collection subsystem of the Nepal Government Services Portal. The portal integrates with **ConnectIPS**, **eSewa**, and **Khalti** as online payment gateways, and supports offline bank challan payments for citizens without internet banking. Fees are denominated in Nepalese Rupees (NPR / रू) and VAT at 13% is applied where mandated. Nepal's fiscal year ends on the last day of Ashadh (mid-July), which is the highest-traffic period for fee-based government service applications. Each edge case below describes a concrete failure scenario, its citizen and revenue impact, and the controls required to prevent and recover from it.

---

## Summary Table

| ID | Title | Component | Severity |
|---|---|---|---|
| EC-PAY-001 | ConnectIPS payment initiated but callback never received | Payment / Webhook Handler | Critical |
| EC-PAY-002 | Double payment via eSewa/Khalti due to browser refresh | Payment / Idempotency | High |
| EC-PAY-003 | Fee structure updated mid-application (NPR amount mismatch) | Fee Service / Cache | High |
| EC-PAY-004 | Khalti/eSewa partial refund after application rejection | Refund Service | High |
| EC-PAY-005 | Payment recorded in ConnectIPS but not reflected in portal | Webhook Handler / DB | Critical |
| EC-PAY-006 | Payment link expired before citizen completes payment | Payment / Link Expiry | Medium |
| EC-PAY-007 | Bank/eSewa/Khalti downtime during peak period (Ashadh) | Payment / Gateway | High |
| EC-PAY-008 | Currency/amount mismatch in ConnectIPS callback validation | Webhook Validation | Critical |

---

## Edge Cases

---

### EC-PAY-001: ConnectIPS Payment Initiated but Callback Never Received

| Field | Details |
|---|---|
| **Failure Mode** | A citizen clicks "Pay Now" on an application that requires a fee (e.g., passport renewal at NPR 5,000). The portal creates a `PaymentTransaction` record with status `INITIATED` and redirects the citizen to the ConnectIPS payment gateway. The citizen completes the payment on ConnectIPS successfully (money is debited from their bank account). ConnectIPS attempts to send the payment result webhook to `https://govportal.gov.np/api/v1/payments/webhook/connectips/`, but the portal is temporarily unreachable (e.g., ALB maintenance, ECS deployment, or a brief network outage). ConnectIPS retries the webhook 3 times over 30 minutes; all attempts fail. The citizen is redirected to the portal's return URL with a `SUCCESS` status in the query parameter, but the portal's application remains in `PENDING_PAYMENT` because the database was never updated. |
| **Impact** | The citizen's bank account has been debited (NPR 5,000) but the application remains unpaid in the portal. The citizen cannot proceed with their application. The citizen contacts support believing the payment failed. Manual reconciliation is required. If the SLA clock is running, the application may miss its processing deadline while stuck in `PENDING_PAYMENT`. |
| **Detection** | `PaymentTransaction` records in `INITIATED` status for more than 30 minutes trigger a CloudWatch alarm. Celery Beat `poll_unresolved_payments` task runs every 15 minutes and queries the ConnectIPS transaction status API for all `INITIATED` payments older than 20 minutes. Sentry alert on repeated webhook delivery failures in ALB access logs (HTTP 5xx to `/webhook/connectips/`). |
| **Mitigation / Recovery** | 1. The `poll_unresolved_payments` Celery task calls `ConnectIPS.get_transaction_status(gateway_txn_id)` for each stale `INITIATED` payment. 2. If the ConnectIPS API returns `SUCCESS`: update `PaymentTransaction.status = 'COMPLETED'`, trigger the application state transition to `PAYMENT_VERIFIED`, and notify the citizen via SMS ("Your payment of रू5,000 has been confirmed"). 3. If the ConnectIPS API returns `FAILED`: update `PaymentTransaction.status = 'FAILED'` and notify the citizen. 4. If the portal's webhook endpoint was down: review ALB access logs for the webhook path; confirm the downtime window; re-trigger the polling task for all payments created during the window. |
| **Prevention** | 1. Configure ConnectIPS webhook with a public-facing HTTPS endpoint protected by AWS WAF (not behind the ECS deployment target group): use a Lambda function as the webhook receiver, which writes to SQS and returns HTTP 200 immediately. The SQS consumer updates the DB asynchronously. This decouples webhook receipt from portal availability. 2. Implement the `poll_unresolved_payments` polling task as a safety net running every 15 minutes. 3. Set ConnectIPS webhook retry policy to 10 attempts over 4 hours. 4. Verify webhook endpoint health independently in the monitoring dashboard. |

---

### EC-PAY-002: Double Payment via eSewa/Khalti Due to Browser Refresh

| Field | Details |
|---|---|
| **Failure Mode** | A citizen is on the application payment page and clicks "Pay with eSewa". The portal creates a payment order and redirects the citizen to eSewa. The citizen completes the payment. eSewa redirects the citizen back to the portal's return URL (`/applications/{id}/payment/success/`). The citizen's browser shows the success page, but they click the browser "Back" button and then "Refresh", re-submitting the return URL with the same eSewa transaction reference. The portal's payment callback view creates a second `PaymentTransaction` record for the same eSewa transaction ID, resulting in a duplicate payment record and potentially double-updating the application status (triggering duplicate notifications). |
| **Impact** | The citizen's application receives two `PaymentTransaction` records, both marked `COMPLETED`. The application workflow is triggered twice (double state transition attempt). The second transition fails gracefully (state machine rejects a duplicate `SUBMITTED → PAYMENT_VERIFIED` transition), but the citizen receives duplicate SMS and email notifications ("Your payment has been received"), causing confusion. Revenue reconciliation shows a discrepancy. |
| **Detection** | Duplicate `gateway_txn_id` constraint violation in the `payment_transactions` table (unique constraint on `gateway_txn_id`). Sentry `IntegrityError` alert. Duplicate notification alert: the notification deduplication service detects two notifications of the same type for the same application within 60 seconds. |
| **Mitigation / Recovery** | 1. The unique constraint on `gateway_txn_id` prevents the duplicate record from being inserted. The callback view catches the `IntegrityError`, queries the existing transaction, and returns HTTP 200 (idempotent response) without re-processing. 2. Cancel any duplicate notifications in the notification queue that match the same `(application_id, notification_type, deduplication_window)`. |
| **Prevention** | 1. Add a `UNIQUE` database constraint on `payment_transactions.gateway_txn_id`. The callback view uses `PaymentTransaction.objects.get_or_create(gateway_txn_id=txn_id, ...)` — if the record already exists, skip processing and return HTTP 200. 2. Implement a Redis idempotency key: `SET payment_processing:{gateway_txn_id} "1" NX EX 300` before processing the callback. If the key already exists, return HTTP 200 immediately without processing. 3. On the frontend, disable the "Pay" button immediately after the first click to prevent double-submission. 4. Use `Post/Redirect/Get` pattern for the payment return URL: after processing the callback, redirect to a read-only success page (HTTP 303), so browser refresh does not re-POST. |

---

### EC-PAY-003: Fee Structure Updated Mid-Application (NPR Amount Mismatch)

| Field | Details |
|---|---|
| **Failure Mode** | The Government of Nepal revises the fee for a land registration service from NPR 2,500 to NPR 3,000 via gazette notification, effective immediately. The portal's Super Admin updates the fee schedule in the Admin panel at 10:00 AM. A citizen who began filling their application at 9:45 AM (before the update) reaches the payment page at 10:05 AM (after the update). The portal's payment initiation service fetches the current fee (NPR 3,000) for the payment order. However, the citizen's application form still displays "NPR 2,500" (cached from the pre-update fee calculation). The citizen initiates payment for NPR 3,000 (the current fee) but expects to pay NPR 2,500. The citizen is confused and may abandon the application. |
| **Impact** | Citizen abandonment on the payment page. Support burden from citizens who received an incorrect fee estimate. Trust erosion in the portal's transparency. Additionally, if a citizen initiated payment at NPR 2,500 via eSewa (from a cached payment link) while the portal updated the fee to NPR 3,000, the ConnectIPS/eSewa callback arrives with NPR 2,500, which the portal's payment validator rejects as `AMOUNT_MISMATCH`, leaving the citizen's payment unprocessed despite a successful deduction. |
| **Detection** | Payment amount mismatch errors spike in Sentry (`PaymentAmountMismatchError`). Fee update audit log entry followed by a surge in payment page abandonment rate (tracked via the portal's analytics). |
| **Mitigation / Recovery** | 1. For the `AMOUNT_MISMATCH` case: identify the citizen's payment via the `gateway_txn_id`, confirm the payment was successful with the gateway, and manually reconcile: either accept the NPR 2,500 payment (if the old fee was valid at the time of initiation) or refund and ask the citizen to pay again. 2. Update the portal's fee schedule change process to always include a 24-hour grace period for in-progress applications (applications already in `DRAFT` or `SUBMITTED` state at the time of the fee update retain the old fee). |
| **Prevention** | 1. Implement **fee snapshot at submission time** (FR-FEE-003): the fee amount and fee schedule version are stored in the `ServiceApplication` record at the moment the citizen submits. All subsequent payment validation uses the snapshot amount, not the current fee schedule. 2. The payment order creation service always reads `application.fee_snapshot_amount` (not `service.current_fee`). 3. When a fee update is published: cache-bust immediately and show an in-portal banner: "Service fee for [Land Registration] has been updated to NPR 3,000, effective today." 4. Set the minimum cache TTL for fee data to 15 minutes (not longer), and trigger an explicit cache invalidation on fee schedule update. |

---

### EC-PAY-004: Khalti/eSewa Partial Refund After Application Rejection

| Field | Details |
|---|---|
| **Failure Mode** | A citizen pays NPR 1,500 for a business registration application via Khalti. The officer reviews the application and rejects it (reason: incomplete documents). The system triggers the automatic refund workflow: `initiateRefund(payment_id, amount=1500, reason='APPLICATION_REJECTED')`. The portal calls the Khalti refund API. Khalti's refund API returns HTTP 200 but with `refunded_amount=500` (a partial refund due to Khalti processing fees being non-refundable per Khalti's merchant agreement). The portal's refund handler expects the full NPR 1,500 to be refunded and treats the partial refund as a failure, setting `RefundTransaction.status='FAILED'` and triggering repeated automatic retry attempts. Each retry further charges Khalti processing fees. |
| **Impact** | The citizen receives only NPR 500 of their NPR 1,500 refund. The portal's refund status shows `FAILED`, causing duplicate retry attempts. The citizen contacts support reporting a missing refund. The portal may be charged additional Khalti processing fees for each retry. Trust in the portal's refund reliability is damaged. |
| **Detection** | Refund amount mismatch logged in Sentry: `RefundAmountMismatch: expected=1500 actual=500`. Celery retry exhaustion alert for the `process_refund` task. Citizen support ticket spike for "missing refund". |
| **Mitigation / Recovery** | 1. Update the `process_refund` task to handle partial refunds: if `refunded_amount < expected_amount`, set `RefundTransaction.status='PARTIAL'` (not `FAILED`) and stop automatic retries. 2. Enqueue a manual review task: the support team reviews the partial refund, contacts Khalti/eSewa merchant support for the remaining amount, and either arranges a top-up refund or contacts the citizen. 3. Notify the citizen via SMS: "A partial refund of रू{partial_amount} has been processed. We are working with the payment provider to refund the remaining रू{remaining_amount}. You will be notified within 3 working days." |
| **Prevention** | 1. Review Khalti, eSewa, and ConnectIPS merchant agreements to understand refund policies: some gateways do not refund their processing fees. Update the portal's refund amount calculation to account for non-refundable gateway fees: `refund_amount = paid_amount - gateway_processing_fee`. 2. Update the portal's Terms of Service to inform citizens of any non-refundable fees. 3. Add `PARTIAL` as a valid `RefundTransaction.status` value and handle it explicitly in the refund state machine. 4. Add acceptance tests for partial refund scenarios in the payment integration test suite. |

---

### EC-PAY-005: Payment Recorded in ConnectIPS but Not Reflected in Portal

| Field | Details |
|---|---|
| **Failure Mode** | A citizen pays NPR 800 for a driving licence renewal via ConnectIPS. ConnectIPS processes the payment successfully and sends the webhook to the portal. The portal's webhook handler receives the webhook, validates the HMAC-SHA256 signature, deserialises the payload, and begins the database update. However, the Django database transaction is rolled back due to a transient `OperationalError` (e.g., database connection dropped mid-transaction). The webhook handler returns HTTP 500. ConnectIPS marks the webhook delivery as failed after 3 retries (all return 500 due to the ongoing DB issue). The citizen's `PaymentTransaction` remains in `INITIATED` status. ConnectIPS has the payment as `SUCCESS`; the portal has it as `INITIATED`. |
| **Impact** | The citizen has paid NPR 800 but their application is stuck in `PENDING_PAYMENT`. The citizen cannot proceed. The portal's `poll_unresolved_payments` Celery task (if running) will eventually reconcile this, but until it does, the citizen experiences a broken journey. If the citizen retries payment thinking the first attempt failed, a double-payment scenario (EC-PAY-002) may occur. |
| **Detection** | ConnectIPS webhook delivery failure recorded in the portal's webhook log. CloudWatch alarm: webhook handler HTTP 5xx rate. `poll_unresolved_payments` Celery task will detect this in its next run (15-minute cycle) and reconcile via the ConnectIPS status API. |
| **Mitigation / Recovery** | 1. The `poll_unresolved_payments` task queries ConnectIPS for the status of all `INITIATED` payments older than 20 minutes. For confirmed `SUCCESS` payments: update the DB and continue the workflow. 2. If the DB is recovered before the next polling cycle, the on-call engineer can manually trigger the polling task: `python manage.py poll_payment_status --payment-id={id}`. 3. Notify the citizen via SMS once the reconciliation confirms payment success. |
| **Prevention** | 1. Implement the webhook handler as a two-phase operation: (a) write the raw webhook payload to a `raw_webhooks` table with a simple INSERT (highly reliable, no business logic); return HTTP 200 immediately. (b) A Celery consumer processes the `raw_webhooks` table entries asynchronously with retry logic. This ensures ConnectIPS always receives HTTP 200 and no webhook is lost. 2. Use `transaction.on_commit()` to trigger the application state transition only after the DB transaction for the payment update has successfully committed. 3. Implement the `poll_unresolved_payments` task as a safety net. |

---

### EC-PAY-006: Payment Link Expired Before Citizen Completes Payment

| Field | Details |
|---|---|
| **Failure Mode** | The portal generates a ConnectIPS payment order with a 30-minute expiry (the maximum allowed by ConnectIPS for certain merchant configurations). The citizen is redirected to ConnectIPS but is interrupted (e.g., needs to top up their account, phone battery dies, or Internet drops). When the citizen returns after 45 minutes, the ConnectIPS payment page shows "Payment link expired". The citizen clicks the browser back button and returns to the portal, which still shows the "Pay Now" button. The citizen clicks "Pay Now" again. The portal's payment service attempts to reuse the existing `PaymentTransaction` record (still in `INITIATED` state) and re-submits the same expired order ID to ConnectIPS, which rejects it. |
| **Impact** | The citizen cannot complete their payment. They are confused about whether they need to start over or whether their application is still valid. If the application has an SLA deadline, the failed payment attempt wastes time. Support team receives a "Why can't I pay?" ticket. |
| **Detection** | ConnectIPS order creation API returns a `PAYMENT_LINK_EXPIRED` or `ORDER_NOT_FOUND` error. This error is caught and logged in Sentry. The portal's "Pay Now" button failure rate increases. |
| **Mitigation / Recovery** | 1. When ConnectIPS returns `ORDER_NOT_FOUND` or `PAYMENT_LINK_EXPIRED` on a "Pay Now" attempt that reuses an old order: automatically create a new ConnectIPS payment order, create a new `PaymentTransaction` record (marking the old one `EXPIRED`), and redirect the citizen to the new payment URL. 2. The citizen is shown a user-friendly message: "Your previous payment session expired. A new payment link has been generated." |
| **Prevention** | 1. Store the `payment_link_expiry` timestamp on each `PaymentTransaction` record. 2. When the citizen clicks "Pay Now", check if the existing payment link has expired (or will expire in < 5 minutes). If so, create a new payment order automatically before redirecting. 3. Set the `payment_deadline` to be the shorter of: (a) ConnectIPS order expiry (30 minutes) or (b) the application-level payment deadline (24–72 hours). 4. Show a countdown timer on the payment page: "This payment link expires in {minutes} minutes". Use a JavaScript timer that triggers a warning at 5 minutes remaining and auto-refreshes the payment link at expiry. |

---

### EC-PAY-007: Bank/eSewa/Khalti Downtime During Peak Period (Ashadh)

| Field | Details |
|---|---|
| **Failure Mode** | On the last working day of Ashadh (the Nepal fiscal year deadline), all three primary payment gateways — ConnectIPS, eSewa, and Khalti — experience degraded performance or full outages due to the extraordinary volume of transactions across all financial services (not just the government portal). Citizens who attempt to pay for applications (which must be submitted before the fiscal year deadline for certain services) cannot complete payment. The portal's payment initiation API returns errors as all gateways time out or return HTTP 503. |
| **Impact** | Citizens with applications in `PENDING_PAYMENT` cannot advance their application before the fiscal year deadline. For time-sensitive services (e.g., VAT registration, business renewal), missing the Ashadh deadline may result in penalties or the need to re-apply in the new fiscal year. High support volume, frustrated citizens, and potential legal/regulatory complications for the Government of Nepal if services are unavailable during a statutory deadline. |
| **Detection** | All three gateway health-check endpoints (`connectips_health`, `esewa_health`, `khalti_health`) return non-200 responses. CloudWatch synthetic monitors for all three gateways report failure. Operations dashboard shows `payment_success_rate < 20%` for more than 5 minutes. |
| **Mitigation / Recovery** | 1. Immediately activate the **offline challan payment** pathway for all pending applications: the portal generates a bank challan (printable payment slip with a unique reference number) that the citizen can pay at any commercial bank counter. The SLA clock is paused for applications in `PENDING_PAYMENT` during the gateway downtime event. 2. Extend the payment deadline for all `PENDING_PAYMENT` applications by 72 hours via an emergency admin action. 3. Publish a notice on the portal's home page and send SMS to all affected citizens: "Online payment services are experiencing high load. Please use the bank challan option or try again after [time]." 4. Post a status update on `status.govportal.gov.np`. |
| **Prevention** | 1. Pre-announce the Ashadh deadline surge to ConnectIPS, eSewa, and Khalti 4 weeks in advance, requesting dedicated throughput quotas. 2. During the 2-week pre-Ashadh period: lower the default payment timeout from 30 seconds to 10 seconds and implement a fast-fail with immediate retry on a different gateway (gateway fallback order: ConnectIPS → eSewa → Khalti → offline challan). 3. Implement a "payment retry with alternate gateway" UX: if the citizen's first gateway choice fails, show alternatives: "ConnectIPS is currently busy. Try eSewa or Khalti?" 4. Ensure offline challan is always available as a fallback and that the challan verification workflow (manually verified by a government cashier) is operational. |

---

### EC-PAY-008: Currency/Amount Mismatch in ConnectIPS Callback Validation

| Field | Details |
|---|---|
| **Failure Mode** | The portal creates a ConnectIPS payment order for NPR 1,200 (NPR 1,062 + VAT 13% = NPR 1,200, rounded). ConnectIPS's webhook callback sends `amount=120000` (amount in paisa — Nepal's subunit, 100 paisa = 1 rupee). The portal's webhook handler expects the amount in rupees and compares `120000 != 1200`, flagging the payment as `AMOUNT_MISMATCH` and rejecting it. The citizen has paid but the portal refuses to accept the payment. Alternatively: floating-point comparison of `1200.00 != 1200.0000001` (rounding difference) causes a false rejection. |
| **Impact** | Valid payments are rejected by the portal's amount validator. The citizen's application remains in `PENDING_PAYMENT`. If the citizen has already been debited, this is functionally identical to EC-PAY-005 from the citizen's perspective. The issue may affect all payments if ConnectIPS changes their API response format (e.g., from rupees to paisa), causing a system-wide payment failure. |
| **Detection** | `PaymentAmountMismatchError` spike in Sentry (100% of payments failing with the same error pattern). Payment success rate drops to 0% on the CloudWatch dashboard. On-call engineer receives PagerDuty P1 alert. |
| **Mitigation / Recovery** | 1. Identify the unit used by the ConnectIPS callback: check the ConnectIPS API documentation for the current API version and confirm the amount unit. 2. Apply an emergency fix: if the unit is paisa, divide the callback amount by 100 before comparison. Deploy via hotfix branch with zero-downtime ECS rolling deployment. 3. For all payments rejected during the mismatch window: re-process using the `poll_unresolved_payments` Celery task which queries ConnectIPS directly for the authoritative status. |
| **Prevention** | 1. In the payment order creation and validation code, always be explicit about the currency unit: use a `Money` value object (`amount: Decimal, currency: str = 'NPR', unit: str = 'rupees'`). 2. Store the original callback payload verbatim in `PaymentTransaction.raw_callback` (JSONB field) so the exact amount and unit can always be retrieved for debugging. 3. In unit tests: test the amount validator with amounts in both paisa and rupees formats, and with floating-point values that differ by < 0.01%. 4. Subscribe to ConnectIPS API changelog notifications and schedule a review of amount units on every API version bump. |

---

## Appendix: Code Snippets

### Idempotent Payment Webhook Handler

```python
# apps/payments/views.py
import hashlib
import hmac
import json
from django.db import transaction, IntegrityError
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class ConnectIPSWebhookView(APIView):
    """
    Two-phase webhook handler:
    Phase 1: Validate signature and store raw payload (must be fast and reliable).
    Phase 2: Process payload asynchronously via Celery (idempotent).
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        # Phase 1: Validate HMAC-SHA256 signature
        payload_bytes = request.body
        received_sig = request.headers.get('X-ConnectIPS-Signature', '')
        expected_sig = hmac.new(
            settings.CONNECTIPS_WEBHOOK_SECRET.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(received_sig, expected_sig):
            return Response(
                {'error': 'Invalid signature'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Phase 2: Store raw payload and enqueue processing
        try:
            with transaction.atomic():
                raw_webhook, created = RawWebhook.objects.get_or_create(
                    gateway='connectips',
                    idempotency_key=request.headers.get('X-ConnectIPS-Idempotency-Key', ''),
                    defaults={
                        'payload': payload_bytes.decode(),
                        'received_at': timezone.now(),
                        'status': 'PENDING',
                    }
                )
                if created:
                    process_payment_webhook.delay(raw_webhook.id)
        except Exception as e:
            # Always return 200 to prevent ConnectIPS retries on transient errors
            logger.error("Webhook storage failed: %s", e, exc_info=True)

        return Response({'status': 'received'}, status=status.HTTP_200_OK)
```

### Webhook Signature Verification (all gateways)

```python
# apps/payments/gateway_clients.py
import hashlib
import hmac
from decimal import Decimal, ROUND_HALF_UP

class PaymentAmountValidator:
    """
    Validates payment amount from gateway callback against expected amount.
    Handles unit differences (paisa vs. rupees) and floating-point tolerances.
    """
    PAISA_GATEWAYS = {'connectips'}  # gateways that send amount in paisa
    TOLERANCE_NPR = Decimal('0.01')  # NPR tolerance for floating-point comparison

    @classmethod
    def validate(cls, gateway: str, callback_amount: int | float, expected_npr: Decimal) -> bool:
        """
        Returns True if the callback amount matches the expected NPR amount.
        """
        if gateway in cls.PAISA_GATEWAYS:
            # Convert paisa to rupees
            received_npr = Decimal(str(callback_amount)) / 100
        else:
            received_npr = Decimal(str(callback_amount))

        received_npr = received_npr.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        expected_npr = expected_npr.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return abs(received_npr - expected_npr) <= cls.TOLERANCE_NPR
```

### Fee Snapshot Model

```python
# apps/fees/models.py
from django.db import models
from decimal import Decimal

class ApplicationFeeSnapshot(models.Model):
    """
    Immutable record of the fee applicable to an application at submission time.
    Once created, this record is never updated. It protects citizens from
    mid-process fee changes and provides an audit trail of what was charged.
    """
    application = models.OneToOneField(
        'applications.ServiceApplication',
        on_delete=models.CASCADE,
        related_name='fee_snapshot',
    )
    service_fee_schedule = models.ForeignKey(
        'fees.FeeSchedule',
        on_delete=models.PROTECT,
    )
    base_amount_npr = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(
        max_digits=5, decimal_places=4,
        default=Decimal('0.13'),  # 13% VAT per Nepal tax law
    )
    vat_amount_npr = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount_npr = models.DecimalField(max_digits=10, decimal_places=2)
    discount_reason = models.CharField(max_length=100, blank=True)
    discount_amount_npr = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'application_fee_snapshots'
        indexes = [
            models.Index(fields=['application']),
        ]

    def __str__(self):
        return f"Fee Snapshot: NPR {self.total_amount_npr} for {self.application_id}"
```

### Poll Unresolved Payments Celery Task

```python
# apps/payments/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

@shared_task(
    bind=True, max_retries=3, default_retry_delay=60,
    queue='payments', name='payments.poll_unresolved_payments'
)
def poll_unresolved_payments(self):
    """
    Safety net: queries each gateway for the status of all INITIATED payments
    older than 20 minutes. Reconciles any payments that succeeded at the gateway
    but were not recorded in the portal due to webhook delivery failure.

    Runs every 15 minutes via Celery Beat.
    """
    from apps.payments.models import PaymentTransaction
    from apps.payments.gateway_clients import get_gateway_client

    cutoff = timezone.now() - timedelta(minutes=20)
    stale = PaymentTransaction.objects.filter(
        status='INITIATED',
        created_at__lt=cutoff,
    ).select_related('application')

    resolved = failed = 0
    for txn in stale:
        try:
            client = get_gateway_client(txn.gateway)
            gateway_status = client.get_transaction_status(txn.gateway_txn_id)
            if gateway_status == 'SUCCESS':
                txn.mark_completed(source='poll')
                resolved += 1
            elif gateway_status in ('FAILED', 'CANCELLED', 'EXPIRED'):
                txn.mark_failed(reason=gateway_status, source='poll')
                failed += 1
        except Exception as exc:
            logger.error("Failed to poll payment %s: %s", txn.id, exc)

    logger.info("poll_unresolved_payments: resolved=%d failed=%d", resolved, failed)
    return {'resolved': resolved, 'failed': failed}
```

---

## Operational Policy Addendum

### 1. Citizen Data Privacy Policy

- Payment data collected by the Nepal Government Services Portal — including bank account details, wallet identifiers, and transaction amounts — is processed solely for the purpose of fee collection for government services and is not retained beyond the statutory audit retention period of 7 years.
- Card numbers and wallet credentials are never stored on portal servers; all payment data is tokenised by ConnectIPS, eSewa, or Khalti on their respective PCI-DSS-compliant infrastructure. The portal stores only the gateway-assigned `transaction_id` and the payment status.
- Payment transaction records are governed by the Nepal Privacy Act 2018. Citizens may request a copy of their payment history from the portal's "My Payments" section.
- Payment-related PII (name, phone, amount) is never included in application or error logs.

### 2. Service Delivery SLA Policy

- For paid services, the SLA clock starts from the time the payment is confirmed (`PAYMENT_VERIFIED` status), not from the time of application submission.
- If a payment gateway outage (EC-PAY-007) prevents payment completion, the SLA clock is paused for the affected applications during the outage window. Affected citizens are notified and their payment deadline is extended by a minimum of 72 hours.
- Refund processing for rejected applications must be initiated within 3 working days of the rejection decision and completed within 7 working days, subject to the gateway's refund processing timeline.
- Payment reconciliation reports are generated daily and reviewed by the Finance Section of the relevant ministry. Discrepancies are escalated for manual reconciliation within 24 hours.

### 3. Fee and Payment Policy

- Service fees are denominated in Nepalese Rupees (NPR / रू). VAT at **13%** is applied as mandated by the Inland Revenue Department of Nepal, and is itemised on the payment receipt.
- Payments are accepted via: **ConnectIPS** (bank transfers), **eSewa** (digital wallet), **Khalti** (digital wallet), and **offline bank challan** (for citizens without internet banking access).
- The fee schedule for each service is published on the portal and updated within 1 working day of any gazette notification changing the fee.
- Fee amounts are **frozen at submission time**: a citizen who has already submitted their application will not be charged more even if the fee increases during processing.
- Successful payments are non-refundable except in cases of: (a) government-initiated rejection of the application, (b) duplicate/double charge, or (c) system failure preventing service delivery.
- Approved refunds are processed via the original payment channel within **7 working days**.

### 4. System Availability Policy

- The payment processing subsystem targets **99.9% monthly uptime** for payment initiation and webhook receipt endpoints, measured independently of the broader portal availability.
- The `poll_unresolved_payments` safety-net task must always be running (monitored via Celery worker health check). Its absence for more than 30 minutes triggers a P2 alert.
- Gateway outage events are communicated on `status.govportal.gov.np` within 15 minutes of detection. The offline challan pathway must remain operational at all times as a fallback.
- Annual load tests simulating Ashadh peak payment volumes (50× normal) are conducted each Jestha (two months before fiscal year end) to validate payment throughput capacity.
