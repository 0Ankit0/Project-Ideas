# C4 Code Diagram

## Overview
C4 Level 4 — Code-level diagram showing key class relationships inside the Booking component of the rental management system.

---

## Booking Component — Code Level

```mermaid
classDiagram
    class BookingRouter {
        +create_booking(data, db, user) BookingResponse
        +confirm_booking(bookingId, db, user) BookingResponse
        +cancel_booking(bookingId, data, db, user) BookingResponse
        +initiate_return(bookingId, data, db, user) BookingResponse
        +get_booking(bookingId, db, user) BookingResponse
        +list_bookings(filters, db, user) BookingListResponse
    }

    class BookingService {
        -db: AsyncSession
        -booking_repo: BookingRepository
        -availability_repo: AvailabilityRepository
        -pricing_engine: PricingEngine
        -deposit_service: DepositService
        -event_publisher: EventPublisher
        +create_booking(customer_id, data) Booking
        +confirm_booking(booking_id, owner_id) Booking
        +cancel_booking(booking_id, actor_id, reason) Booking
        +initiate_return(booking_id, actual_return_at) Booking
        +modify_booking(booking_id, new_start, new_end) Booking
    }

    class PricingEngine {
        -db: AsyncSession
        -rule_repo: PricingRuleRepository
        -tax_service: TaxService
        +calculate(asset_id, start, end) PriceBreakdown
        -select_optimal_rates(duration_hours, rules) RateCombo[]
        -apply_peak_surcharge(base_fee, rules, start, end) Decimal
        -apply_discount(base_fee, rules, duration_hours) Decimal
    }

    class AvailabilityService {
        -db: AsyncSession
        -redis: RedisClient
        -block_repo: AvailabilityBlockRepository
        +is_available(asset_id, start, end) Boolean
        +acquire_lock(asset_id, start, end, ttl_seconds) Boolean
        +release_lock(asset_id, start, end) void
        +create_block(asset_id, start, end, type, ref_id) AvailabilityBlock
        +release_block(block_id) void
    }

    class DepositService {
        -db: AsyncSession
        -payment_gateway: PaymentGatewayAdapter
        -deposit_repo: DepositRepository
        +hold(customer_id, amount, payment_method_id) DepositRef
        +capture(deposit_id) void
        +release(deposit_id) Refund
        +deduct(deposit_id, deductions) DepositSettlement
    }

    class BookingRepository {
        -db: AsyncSession
        +find_by_id(id) Optional[Booking]
        +find_by_owner(owner_id, filters) List[Booking]
        +find_by_customer(customer_id, filters) List[Booking]
        +find_active_past_end_time(current_time) List[Booking]
        +save(booking) Booking
        +update_status(booking_id, status) Booking
    }

    class AvailabilityRepository {
        -db: AsyncSession
        +find_blocks(asset_id, start, end) List[AvailabilityBlock]
        +create_block(block) AvailabilityBlock
        +release_block(block_id) void
    }

    class PricingRuleRepository {
        -db: AsyncSession
        +find_by_asset(asset_id) List[PricingRule]
        +find_active_peak_rules(asset_id, start, end) List[PricingRule]
    }

    class EventPublisher {
        +publish(event_type, payload) void
        +subscribe(event_type, handler) void
    }

    class PaymentGatewayAdapter {
        <<interface>>
        +hold(customer_id, amount, method_id) HoldRef
        +capture(hold_ref) CaptureResult
        +refund(charge_ref, amount) RefundResult
        +payout(owner_bank_ref, amount) PayoutResult
    }

    class StripeGatewayAdapter {
        +hold(customer_id, amount, method_id) HoldRef
        +capture(hold_ref) CaptureResult
        +refund(charge_ref, amount) RefundResult
        +payout(owner_bank_ref, amount) PayoutResult
    }

    BookingRouter --> BookingService
    BookingService --> BookingRepository
    BookingService --> AvailabilityService
    BookingService --> PricingEngine
    BookingService --> DepositService
    BookingService --> EventPublisher

    AvailabilityService --> AvailabilityRepository
    PricingEngine --> PricingRuleRepository

    DepositService --> PaymentGatewayAdapter
    PaymentGatewayAdapter <|.. StripeGatewayAdapter : implements
```

---

## Assessment Component — Code Level

```mermaid
classDiagram
    class AssessmentRouter {
        +create_assessment(data, db, user) AssessmentResponse
        +submit_items(assessment_id, items, db, user) AssessmentResponse
        +upload_photos(assessment_id, photos, db, user) AssessmentResponse
        +submit_assessment(assessment_id, db, user) AssessmentResponse
        +countersign(assessment_id, db, user) AssessmentResponse
        +get_comparison(booking_id, db, user) ComparisonResponse
    }

    class AssessmentService {
        -db: AsyncSession
        -assessment_repo: AssessmentRepository
        -storage_adapter: StorageAdapter
        -comparison_engine: ComparisonEngine
        -report_generator: ReportGenerator
        -event_publisher: EventPublisher
        +create(booking_id, type, staff_id) ConditionAssessment
        +submit_items(assessment_id, items) void
        +upload_photos(assessment_id, photos) List[str]
        +submit(assessment_id) ConditionAssessment
        +customer_countersign(assessment_id, ip) void
        +compare_with_pre_rental(booking_id) ComparisonResult
    }

    class ComparisonEngine {
        +compare(pre, post) ComparisonResult
        +find_discrepancies(pre_items, post_items) List[Discrepancy]
        +calculateSeverity(discrepancies) Severity
    }

    class ReportGenerator {
        -storage_adapter: StorageAdapter
        +generate(assessment) ReportDocument
        +store(report) String
    }

    class StorageAdapter {
        <<interface>>
        +upload(file, key) String
        +download(key) Bytes
        +getSignedUrl(key, expiry_seconds) String
        +delete(key) void
    }

    class S3StorageAdapter {
        -client: S3Client
        -bucket: String
        +upload(file, key) String
        +download(key) Bytes
        +getSignedUrl(key, expiry_seconds) String
        +delete(key) void
    }

    AssessmentRouter --> AssessmentService
    AssessmentService --> ComparisonEngine
    AssessmentService --> ReportGenerator
    AssessmentService --> StorageAdapter
    ReportGenerator --> StorageAdapter
    StorageAdapter <|.. S3StorageAdapter : implements
```

---

## Event Publisher — Code Level

```mermaid
classDiagram
    class EventPublisher {
        -handlers: Dict[str, List[EventHandler]]
        +publish(event_type, payload) void
        +subscribe(event_type, handler) void
    }

    class NotificationEventHandler {
        -notification_service: NotificationService
        +handle(event_type, payload) void
        -map_to_notification(event_type, payload) NotificationRecord
    }

    class NotificationService {
        -db: AsyncSession
        -ws_manager: WebSocketManager
        -messaging_adapter: MessagingAdapter
        +create_notification(user_id, event_type, title, body, payload) void
        +dispatch_push(notification) void
        +dispatch_email(notification) void
        +dispatch_sms(notification) void
    }

    class WebSocketManager {
        -connections: Dict[UUID, WebSocket]
        +connect(user_id, ws) void
        +disconnect(user_id) void
        +send_to_user(user_id, message) void
        +broadcast(user_ids, message) void
    }

    class MessagingAdapter {
        <<interface>>
        +send_email(to, subject, html_body) void
        +send_sms(to, message) void
        +send_push(token, title, body, data) void
    }

    EventPublisher --> NotificationEventHandler
    NotificationEventHandler --> NotificationService
    NotificationService --> WebSocketManager
    NotificationService --> MessagingAdapter
```
