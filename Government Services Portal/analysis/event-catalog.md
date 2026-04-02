# Event Catalog — Government Services Portal

## Overview

This catalog defines all domain events published and consumed within the Government Services Portal. Events follow the format `{domain}.{event_name}` and use a consistent payload schema. The system uses Celery + Redis as the event bus; events are persisted in the `DomainEvent` table before dispatch.

**Event Envelope (all events):**
```json
{
  "event_id": "uuid",
  "event_type": "citizen.registered",
  "schema_version": "1.0",
  "occurred_at": "2024-07-15T10:30:00Z",
  "correlation_id": "uuid",
  "actor_id": "citizen-uuid or system",
  "actor_role": "CITIZEN | SYSTEM | FIELD_OFFICER | ...",
  "payload": { ... }
}
```

---

## Domain: Citizen (citizen.*)

### citizen.registered
- **Description:** A new citizen account has been successfully created after NID OTP verification.
- **Producer:** CitizenAuthService
- **Consumers:** NotificationWorker (send welcome SMS + email), AuditLogService
- **Payload:**
  ```json
  { "citizen_id": "uuid", "full_name": "John Doe", "phone_masked": "XXXXXX1234", "email_masked": "j***@example.com", "aadhaar_last_four": "5678", "registration_channel": "web" }
  ```
- **Side Effects:** Welcome SMS/email dispatched; audit log entry created.

### citizen.profile_updated
- **Description:** Citizen has updated one or more profile fields.
- **Producer:** CitizenProfileService
- **Consumers:** AuditLogService, EligibilityService (re-evaluate active applications)
- **Payload:**
  ```json
  { "citizen_id": "uuid", "changed_fields": ["phone_number", "address_line1"], "update_source": "self_service" }
  ```

### citizen.account_suspended
- **Description:** A citizen's account has been suspended by an admin.
- **Producer:** CitizenAdminService (Super Admin action)
- **Consumers:** NotificationWorker, SessionService (invalidate active sessions), AuditLogService
- **Payload:**
  ```json
  { "citizen_id": "uuid", "reason": "Suspected fraud", "suspended_by": "admin-uuid", "suspension_reference": "SUSP-2024-001" }
  ```

### citizen.account_restored
- **Description:** A suspended citizen account has been restored.
- **Producer:** CitizenAdminService
- **Consumers:** NotificationWorker, AuditLogService
- **Payload:**
  ```json
  { "citizen_id": "uuid", "restored_by": "admin-uuid" }
  ```

### citizen.deletion_requested
- **Description:** Citizen has submitted a PDPA data erasure request.
- **Producer:** CitizenProfileService
- **Consumers:** DataErasureOrchestrator, AuditLogService
- **Payload:**
  ```json
  { "citizen_id": "uuid", "request_reference": "ERASURE-2024-005", "requested_at": "2024-07-15T10:30:00Z" }
  ```

---

## Domain: Identity (identity.*)

### identity.verified
- **Description:** Citizen's NID identity has been successfully verified via NASC (National Identity Management Centre) OTP.
- **Producer:** NIDGatewayClient
- **Consumers:** CitizenAuthService (activate account), AuditLogService
- **Payload:**
  ```json
  { "citizen_id": "uuid", "aadhaar_last_four": "5678", "uidai_transaction_id": "TX123456789", "verification_method": "OTP", "verified_at": "2024-07-15T10:29:00Z" }
  ```
- **Regulatory Note:** NASC (National Identity Management Centre) transaction ID retained for 7 years per NID Act.

### identity.verification_failed
- **Description:** NID OTP verification failed (wrong OTP or service error).
- **Producer:** NIDGatewayClient
- **Consumers:** AuditLogService, SecurityMonitor (count failures for brute-force detection)
- **Payload:**
  ```json
  { "citizen_id": "uuid", "failure_reason": "INVALID_OTP | OTP_EXPIRED | NASC (National Identity Management Centre)_ERROR", "attempt_number": 2, "ip_address_masked": "192.168.x.x" }
  ```

### identity.account_locked
- **Description:** Account locked after exceeding OTP failure threshold.
- **Producer:** NIDGatewayClient
- **Consumers:** NotificationWorker, AuditLogService
- **Payload:**
  ```json
  { "citizen_id": "uuid", "locked_until": "2024-07-15T11:00:00Z", "lock_reason": "MAX_OTP_FAILURES" }
  ```

### identity.digilocker_linked
- **Description:** Citizen has successfully linked their Nepal Document Wallet (NDW) account.
- **Producer:** Nepal Document Wallet (NDW)Client
- **Consumers:** CitizenProfileService (set digilocker_linked=true), AuditLogService
- **Payload:**
  ```json
  { "citizen_id": "uuid", "digilocker_user_id": "DL-USER-123", "linked_at": "2024-07-15T10:35:00Z" }
  ```

---

## Domain: Application (application.*)

### application.draft_created
- **Description:** Citizen has started filling an application (saved as DRAFT).
- **Producer:** ApplicationService
- **Consumers:** AuditLogService
- **Payload:**
  ```json
  { "application_id": "uuid", "arn": null, "citizen_id": "uuid", "service_id": "uuid", "service_name": "Driving Licence Renewal" }
  ```

### application.submitted
- **Description:** Citizen has submitted the application (moved from DRAFT to SUBMITTED after payment if required).
- **Producer:** ApplicationService
- **Consumers:** WorkflowEngine (trigger assignment), NotificationWorker (ARN confirmation), AuditLogService
- **Payload:**
  ```json
  { "application_id": "uuid", "arn": "MH/RTO/2024/0012345", "citizen_id": "uuid", "service_id": "uuid", "submitted_at": "2024-07-15T10:40:00Z" }
  ```

### application.assigned_to_officer
- **Description:** Application auto-assigned to a field officer.
- **Producer:** OfficerQueueManager
- **Consumers:** NotificationWorker (officer alert), AuditLogService
- **Payload:**
  ```json
  { "application_id": "uuid", "arn": "MH/RTO/2024/0012345", "officer_id": "uuid", "officer_name": "Jane Doe", "assigned_at": "2024-07-15T11:00:00Z", "sla_deadline": "2024-07-22" }
  ```

### application.under_review
- **Description:** Officer has opened the application and begun review.
- **Producer:** ApplicationService (officer action)
- **Consumers:** AuditLogService
- **Payload:**
  ```json
  { "application_id": "uuid", "arn": "MH/RTO/2024/0012345", "officer_id": "uuid", "review_started_at": "2024-07-16T09:00:00Z" }
  ```

### application.pending_info_requested
- **Description:** Officer has requested additional information from the citizen.
- **Producer:** ApplicationService
- **Consumers:** NotificationWorker (citizen alert with details), AuditLogService
- **Payload:**
  ```json
  { "application_id": "uuid", "arn": "MH/RTO/2024/0012345", "requested_items": ["Proof of address (< 3 months)", "Income certificate"], "response_deadline": "2024-07-31", "officer_id": "uuid" }
  ```

### application.info_submitted
- **Description:** Citizen has responded to the pending info request.
- **Producer:** ApplicationService
- **Consumers:** WorkflowEngine (re-assign for review), NotificationWorker (officer alert), AuditLogService
- **Payload:**
  ```json
  { "application_id": "uuid", "arn": "MH/RTO/2024/0012345", "citizen_id": "uuid", "submitted_at": "2024-07-20T14:00:00Z" }
  ```

### application.approved
- **Description:** Application has been approved by the field officer or department head.
- **Producer:** ApplicationService
- **Consumers:** CertificateIssuanceService (trigger generation), NotificationWorker, AuditLogService
- **Payload:**
  ```json
  { "application_id": "uuid", "arn": "MH/RTO/2024/0012345", "approved_by": "uuid", "approver_role": "FIELD_OFFICER", "approved_at": "2024-07-17T15:00:00Z" }
  ```

### application.rejected
- **Description:** Application has been rejected.
- **Producer:** ApplicationService
- **Consumers:** NotificationWorker (citizen rejection notice with reason), AuditLogService
- **Payload:**
  ```json
  { "application_id": "uuid", "arn": "MH/RTO/2024/0012345", "rejection_reason_code": "INELIGIBLE_AGE", "rejection_remarks": "Applicant does not meet minimum age requirement of 18 years.", "rejected_by": "uuid" }
  ```

### application.auto_closed
- **Description:** Application automatically closed because citizen did not respond to pending info request within 15 days.
- **Producer:** Celery Beat (SLA monitor)
- **Consumers:** NotificationWorker, AuditLogService
- **Payload:**
  ```json
  { "application_id": "uuid", "arn": "MH/RTO/2024/0012345", "citizen_id": "uuid", "pending_info_deadline_missed": "2024-07-31" }
  ```

### application.sla_breach_imminent
- **Description:** SLA deadline is within 48 hours for an application still under review.
- **Producer:** Celery Beat (SLA monitor)
- **Consumers:** NotificationWorker (officer alert), DepartmentMonitor
- **Payload:**
  ```json
  { "application_id": "uuid", "arn": "MH/RTO/2024/0012345", "officer_id": "uuid", "sla_deadline": "2024-07-18", "hours_remaining": 36 }
  ```

### application.sla_breached
- **Description:** SLA deadline has passed without a final decision.
- **Producer:** Celery Beat
- **Consumers:** EscalationService, DepartmentMonitor, AuditLogService
- **Payload:**
  ```json
  { "application_id": "uuid", "arn": "MH/RTO/2024/0012345", "officer_id": "uuid", "breached_at": "2024-07-18T23:59:59Z" }
  ```

### application.escalated_to_dept_head
- **Description:** Officer has escalated application to department head.
- **Producer:** ApplicationService
- **Consumers:** NotificationWorker (dept head alert), AuditLogService
- **Payload:**
  ```json
  { "application_id": "uuid", "arn": "MH/RTO/2024/0012345", "escalated_by": "officer-uuid", "escalation_note": "Complex eligibility case requiring senior review.", "escalated_at": "2024-07-17T11:00:00Z" }
  ```

---

## Domain: Document (document.*)

### document.uploaded
- **Description:** Citizen has uploaded a document.
- **Producer:** DocumentService
- **Consumers:** VirusScanService (async scan), AuditLogService
- **Payload:**
  ```json
  { "document_id": "uuid", "application_id": "uuid", "document_type": "INCOME_CERT", "file_size_bytes": 204800, "source": "UPLOAD", "uploaded_at": "2024-07-15T10:42:00Z" }
  ```

### document.scan_completed
- **Description:** Antivirus scan has completed for an uploaded document.
- **Producer:** VirusScanService
- **Consumers:** DocumentService (update status), AuditLogService, NotificationWorker (if infected)
- **Payload:**
  ```json
  { "document_id": "uuid", "scan_result": "CLEAN | INFECTED", "threat_name": null, "scan_completed_at": "2024-07-15T10:42:30Z" }
  ```

### document.verified_by_officer
- **Description:** Field officer has physically verified a document.
- **Producer:** DocumentService (officer action)
- **Consumers:** ApplicationService (update checklist), AuditLogService
- **Payload:**
  ```json
  { "document_id": "uuid", "application_id": "uuid", "verified_by": "officer-uuid", "verification_method": "PHYSICAL | DIGILOCKER", "verified_at": "2024-07-16T10:00:00Z" }
  ```

### document.pulled_from_digilocker
- **Description:** Document was successfully pulled from Nepal Document Wallet (NDW).
- **Producer:** Nepal Document Wallet (NDW)Client
- **Consumers:** DocumentService, AuditLogService
- **Payload:**
  ```json
  { "document_id": "uuid", "application_id": "uuid", "digilocker_doc_id": "DL-DOC-456", "document_type": "DRIVING_LICENCE", "issue_date": "2022-03-15", "issuer": "MH Transport Dept" }
  ```

---

## Domain: Fee (fee.*)

### fee.invoice_generated
- **Description:** A fee invoice has been created for an application.
- **Producer:** FinanceService
- **Consumers:** NotificationWorker (payment reminder), AuditLogService
- **Payload:**
  ```json
  { "invoice_id": "uuid", "invoice_number": "INV/2024-07/001234", "application_id": "uuid", "citizen_id": "uuid", "total_amount": 590.00, "payment_deadline": "2024-07-22" }
  ```

### fee.payment_initiated
- **Description:** Citizen has clicked "Pay Now" and been redirected to ConnectIPS.
- **Producer:** FinanceService
- **Consumers:** AuditLogService
- **Payload:**
  ```json
  { "invoice_id": "uuid", "paygov_order_id": "PG-ORDER-789", "payment_mode": "eSewa/Khalti/ConnectIPS", "initiated_at": "2024-07-15T10:45:00Z" }
  ```

### fee.paid
- **Description:** Payment has been confirmed via ConnectIPS webhook.
- **Producer:** PaymentWebhookHandler
- **Consumers:** ApplicationService (advance to SUBMITTED), ReceiptGenerationService, AuditLogService
- **Payload:**
  ```json
  { "invoice_id": "uuid", "paygov_transaction_id": "TXN-987654", "amount_paid": 590.00, "payment_mode": "eSewa/Khalti/ConnectIPS", "paid_at": "2024-07-15T10:46:00Z" }
  ```

### fee.payment_failed
- **Description:** Payment attempt failed at ConnectIPS.
- **Producer:** PaymentWebhookHandler
- **Consumers:** NotificationWorker (failure alert to citizen), AuditLogService
- **Payload:**
  ```json
  { "invoice_id": "uuid", "paygov_order_id": "PG-ORDER-789", "failure_code": "INSUFFICIENT_FUNDS", "failed_at": "2024-07-15T10:47:00Z" }
  ```

### fee.waiver_approved
- **Description:** Fee waiver has been approved by the department head.
- **Producer:** FinanceService
- **Consumers:** ApplicationService (set invoice = WAIVED), NotificationWorker, AuditLogService
- **Payload:**
  ```json
  { "invoice_id": "uuid", "waiver_approved_by": "dept-head-uuid", "waiver_reason": "BPL_CATEGORY", "approved_at": "2024-07-16T09:00:00Z" }
  ```

### fee.refund_initiated
- **Description:** Refund has been initiated (duplicate payment or system error).
- **Producer:** FinanceService
- **Consumers:** AuditLogService, NotificationWorker
- **Payload:**
  ```json
  { "invoice_id": "uuid", "refund_amount": 590.00, "refund_reference": "REFUND-2024-003", "initiated_at": "2024-07-15T11:00:00Z" }
  ```

---

## Domain: Certificate (certificate.*)

### certificate.generation_started
- **Description:** Certificate generation pipeline has been triggered.
- **Producer:** CertificateIssuanceService
- **Consumers:** AuditLogService
- **Payload:**
  ```json
  { "application_id": "uuid", "triggered_at": "2024-07-17T15:01:00Z", "template_version": 3 }
  ```

### certificate.issued
- **Description:** Certificate has been successfully generated, signed, and stored.
- **Producer:** CertificateIssuanceService
- **Consumers:** NotificationWorker (citizen download alert), AuditLogService, AnalyticsService
- **Payload:**
  ```json
  { "certificate_id": "uuid", "certificate_number": "RTO/2024/DL/00012345", "application_id": "uuid", "citizen_id": "uuid", "s3_key": "certs/2024/07/cert_uuid.pdf", "qr_url": "https://portal.gov.in/verify/cert/uuid", "issued_at": "2024-07-17T15:05:00Z", "expiry_date": "2029-07-17" }
  ```

### certificate.dsc_signing_failed
- **Description:** Digital signature application failed during certificate generation.
- **Producer:** DSCSigningService
- **Consumers:** AlertService (dept head + super admin), AuditLogService
- **Payload:**
  ```json
  { "application_id": "uuid", "officer_id": "uuid", "failure_reason": "DSC_EXPIRED | HSM_UNAVAILABLE | SIGNING_ERROR", "attempt_number": 1, "failed_at": "2024-07-17T15:02:00Z" }
  ```

### certificate.revoked
- **Description:** Certificate has been revoked by the department head.
- **Producer:** CertificateAdminService
- **Consumers:** NotificationWorker, VerificationService (invalidate QR response), AuditLogService
- **Payload:**
  ```json
  { "certificate_id": "uuid", "revocation_reason": "Issued in error — ineligible applicant", "revoked_by": "dept-head-uuid", "revoked_at": "2024-07-20T09:00:00Z" }
  ```

### certificate.download_requested
- **Description:** Citizen has downloaded their certificate.
- **Producer:** CertificateService
- **Consumers:** AuditLogService, DownloadCountService
- **Payload:**
  ```json
  { "certificate_id": "uuid", "citizen_id": "uuid", "ip_address_masked": "192.168.x.x", "downloaded_at": "2024-07-18T10:00:00Z" }
  ```

---

## Domain: Grievance (grievance.*)

### grievance.filed
- **Description:** Citizen has filed a new grievance.
- **Producer:** GrievanceService
- **Consumers:** GrievanceRouter (assignment), NotificationWorker (GRN to citizen), AuditLogService
- **Payload:**
  ```json
  { "grievance_id": "uuid", "grn": "GRN/2024/005678", "citizen_id": "uuid", "application_id": "uuid", "category": "REJECTION_DISPUTE", "filed_at": "2024-07-18T10:00:00Z" }
  ```

### grievance.assigned
- **Description:** Grievance assigned to a handler.
- **Producer:** GrievanceRouter
- **Consumers:** NotificationWorker (handler alert), AuditLogService
- **Payload:**
  ```json
  { "grievance_id": "uuid", "assigned_to": "dept-head-uuid", "assigned_at": "2024-07-18T11:00:00Z" }
  ```

### grievance.escalated
- **Description:** Grievance escalated to senior authority (SLA breach or citizen request).
- **Producer:** GrievanceEscalationService
- **Consumers:** NotificationWorker, AuditLogService
- **Payload:**
  ```json
  { "grievance_id": "uuid", "grn": "GRN/2024/005678", "escalation_reason": "SLA_BREACH | CITIZEN_REQUEST", "escalated_to": "ministry-uuid", "escalated_at": "2024-07-18T11:00:00Z" }
  ```

### grievance.resolved
- **Description:** Grievance has been resolved.
- **Producer:** GrievanceService
- **Consumers:** NotificationWorker, AuditLogService
- **Payload:**
  ```json
  { "grievance_id": "uuid", "grn": "GRN/2024/005678", "resolved_by": "uuid", "resolution_summary": "Application reprocessed; eligibility verified. Certificate issued.", "resolved_at": "2024-07-28T14:00:00Z" }
  ```

### grievance.sla_warning
- **Description:** Grievance SLA deadline is within 5 days.
- **Producer:** Celery Beat
- **Consumers:** NotificationWorker (handler alert), DepartmentMonitor
- **Payload:**
  ```json
  { "grievance_id": "uuid", "grn": "GRN/2024/005678", "sla_deadline": "2024-08-17", "days_remaining": 5 }
  ```

---

## Domain: Service (service.*)

### service.published
- **Description:** A service definition has been published by the department head and is visible in the citizen catalog.
- **Producer:** ServiceCatalogService
- **Consumers:** CacheInvalidationService (catalog cache), AuditLogService
- **Payload:**
  ```json
  { "service_id": "uuid", "service_code": "MH_RTO_DL_RENEWAL", "service_name": "Driving Licence Renewal", "published_by": "dept-head-uuid", "published_at": "2024-07-01T09:00:00Z" }
  ```

### service.suspended
- **Description:** A published service has been suspended (e.g., for policy change or system maintenance).
- **Producer:** ServiceCatalogService
- **Consumers:** CacheInvalidationService, NotificationWorker (active applicants), AuditLogService
- **Payload:**
  ```json
  { "service_id": "uuid", "service_code": "MH_RTO_DL_RENEWAL", "suspension_reason": "Fee revision in progress", "suspended_by": "dept-head-uuid" }
  ```

### service.form_updated
- **Description:** A service's form schema has been updated (new version created).
- **Producer:** ServiceCatalogService
- **Consumers:** ApplicationService (future applications use new version), AuditLogService
- **Payload:**
  ```json
  { "service_id": "uuid", "old_version": 2, "new_version": 3, "changed_fields": ["income_field_added"], "updated_by": "dept-head-uuid" }
  ```

---

## Domain: System (system.*)

### system.maintenance_scheduled
- **Description:** Platform maintenance window scheduled.
- **Producer:** SuperAdminConfigService
- **Consumers:** NotificationWorker (broadcast banner), AuditLogService
- **Payload:**
  ```json
  { "start_time": "2024-07-28T02:00:00+05:30", "end_time": "2024-07-28T04:00:00+05:30", "affected_services": ["ALL"], "scheduled_by": "super-admin-uuid" }
  ```

### system.integration_health_degraded
- **Description:** An external integration (NID, Nepal Document Wallet (NDW), ConnectIPS) health check has failed.
- **Producer:** IntegrationHealthMonitor
- **Consumers:** AlertService, CircuitBreakerManager
- **Payload:**
  ```json
  { "integration": "AADHAAR | DIGILOCKER | PAYGOV | SMS_GATEWAY", "failure_count": 3, "last_success": "2024-07-15T09:00:00Z", "circuit_state": "HALF_OPEN" }
  ```

---

## Event Catalog Summary

| Domain | Events | Total |
|--------|--------|-------|
| citizen.* | registered, profile_updated, account_suspended, account_restored, deletion_requested | 5 |
| identity.* | verified, verification_failed, account_locked, digilocker_linked | 4 |
| application.* | draft_created, submitted, assigned_to_officer, under_review, pending_info_requested, info_submitted, approved, rejected, auto_closed, sla_breach_imminent, sla_breached, escalated_to_dept_head | 12 |
| document.* | uploaded, scan_completed, verified_by_officer, pulled_from_digilocker | 4 |
| fee.* | invoice_generated, payment_initiated, paid, payment_failed, waiver_approved, refund_initiated | 6 |
| certificate.* | generation_started, issued, dsc_signing_failed, revoked, download_requested | 5 |
| grievance.* | filed, assigned, escalated, resolved, sla_warning | 5 |
| service.* | published, suspended, form_updated | 3 |
| system.* | maintenance_scheduled, integration_health_degraded | 2 |
| **Total** | | **46** |

---

## Operational Policy Addendum

### Section 1 — Event Retention
All domain events are stored in the `DomainEvent` table for 7 years (aligned with IT Act 2000 audit trail requirements). Events older than 1 year are moved to S3 Glacier cold storage but remain queryable via Athena for compliance queries.

### Section 2 — Event Schema Versioning
Each event carries a `schema_version` field. Breaking schema changes increment the major version; additive changes increment the minor version. Consumers must handle minor version increments gracefully (ignore unknown fields).

### Section 3 — Idempotent Consumers
All event consumers are idempotent. Duplicate event delivery (at-least-once delivery from Celery) is handled by checking the `event_id` against a processed-events set in Redis (TTL 24 hours).

### Section 4 — PII in Event Payloads
Event payloads must not include raw NID numbers, PAN, or full bank account numbers. All sensitive identifiers are masked (`phone_masked`, `email_masked`) or referenced by UUID. The `AuditLogService` consumer may access the full entity record via UUID for internal logging purposes.
