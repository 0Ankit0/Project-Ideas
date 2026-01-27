# Sequence Diagram - Slot Booking System

> **Platform Independence**: Shows internal object interactions applicable to any implementation.

---

## Overview

Sequence diagrams show detailed interactions between objects within the system, revealing internal implementation flow.

---

## SD-01: User Registration

```mermaid
sequenceDiagram
    participant C as Client
    participant AC as AuthController
    participant UV as UserValidator
    participant US as UserService
    participant UR as UserRepository
    participant PS as PasswordService
    participant ES as EmailService
    participant DB as Database
    
    C->>+AC: POST /register {email, password, name}
    AC->>+UV: validate(registrationDTO)
    UV-->>-AC: validationResult
    
    alt Validation Failed
        AC-->>C: 400 Bad Request (errors)
    else Validation Passed
        AC->>+US: registerUser(dto)
        US->>+UR: findByEmail(email)
        UR->>+DB: SELECT * FROM users WHERE email = ?
        DB-->>-UR: result
        UR-->>-US: existingUser
        
        alt Email Exists
            US-->>AC: EmailAlreadyExistsException
            AC-->>C: 409 Conflict
        else Email Available
            US->>+PS: hashPassword(password)
            PS-->>-US: hashedPassword
            
            US->>+UR: save(newUser)
            UR->>+DB: INSERT INTO users...
            DB-->>-UR: userId
            UR-->>-US: savedUser
            
            US->>+ES: sendVerificationEmail(user, token)
            ES-->>-US: emailQueued
            
            US-->>-AC: userCreated(userId)
            AC-->>-C: 201 Created {userId, message}
        end
    end
```

---

## SD-02: Complete Booking Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant BC as BookingController
    participant BS as BookingService
    participant SS as SlotService
    participant CS as CacheService
    participant PS as PricingService
    participant PCS as PromoCodeService
    participant PAY as PaymentService
    participant PG as PaymentGateway
    participant NS as NotificationService
    participant IDS as IdempotencyService
    participant AUD as AuditLogger
    participant BR as BookingRepository
    participant DB as Database
    
    C->>+BC: POST /bookings {resourceId, slotIds, promoCode}
    BC->>+IDS: verify(Idempotency-Key, requestHash)
    IDS-->>-BC: ok|replayResponse
    BC->>+BS: createBooking(userId, dto)
    
    %% Validate and lock slots
    loop For each slotId
        BS->>+SS: validateAndLockSlot(slotId, userId)
        SS->>+CS: get("slot_lock:" + slotId)
        CS-->>-SS: lockStatus
        
        alt Slot Locked by Another
            SS-->>BS: SlotUnavailableException
            BS-->>BC: SlotUnavailableException
            BC-->>C: 409 Conflict
        else Slot Available
            SS->>+CS: setex("slot_lock:" + slotId, userId, 300)
            CS-->>-SS: OK
            SS-->>-BS: slotLocked
        end
    end
    
    %% Calculate pricing
    BS->>+PS: calculateTotal(resourceId, slots)
    PS-->>-BS: baseAmount
    
    %% Apply promo if present
    opt Promo Code Provided
        BS->>+PCS: validateAndApply(promoCode, booking)
        PCS-->>-BS: discountAmount
    end
    
    %% Create pending booking
    BS->>+BR: save(pendingBooking)
    BR->>+DB: INSERT INTO bookings...
    DB-->>-BR: bookingId
    BR-->>-BS: savedBooking

    BS->>+AUD: record("booking.created", bookingId)
    AUD-->>-BS: logged
    
    BS-->>-BC: bookingCreated(bookingId, amount, lockExpiresAt)
    BC-->>-C: 201 {bookingId, amount, paymentUrl}
    
    %% Payment Flow
    C->>+BC: POST /payments {bookingId, method, details}
    BC->>+PAY: processPayment(bookingId, paymentDTO)
    
    PAY->>+PG: charge(amount, paymentDetails)
    PG-->>-PAY: gatewayResponse
    
    alt Payment Success
        PAY->>+BR: updateBookingStatus(bookingId, CONFIRMED)
        BR->>+DB: UPDATE bookings SET status = 'CONFIRMED'
        DB-->>-BR: updated
        BR-->>-PAY: booking
        
        PAY->>+NS: sendBookingConfirmation(booking)
        NS-->>-PAY: queued
        
        %% Release lock and mark slots as booked
        loop For each slot
            PAY->>+SS: confirmSlotBooking(slotId, bookingId)
            SS->>+CS: del("slot_lock:" + slotId)
            CS-->>-SS: OK
            SS->>+DB: UPDATE slots SET status = 'BOOKED'
            DB-->>-SS: updated
            SS-->>-PAY: confirmed
        end
        
        PAY-->>-BC: paymentSuccess(transactionId)
        BC-->>-C: 200 {status: confirmed, bookingDetails}
        
    else Payment Failed
        %% Release locks
        loop For each slot
            PAY->>+SS: releaseSlotLock(slotId)
            SS->>+CS: del("slot_lock:" + slotId)
            CS-->>-SS: OK
            SS-->>-PAY: released
        end
        
        PAY->>+BR: updateBookingStatus(bookingId, FAILED)
        BR-->>-PAY: updated
        
        PAY-->>BC: paymentFailed(error)
        BC-->>C: 402 Payment Required {error}
    end
```

---

## SD-03: Cancel Booking with Refund

```mermaid
sequenceDiagram
    participant C as Client
    participant BC as BookingController
    participant BS as BookingService
    participant RS as RefundService
    participant PS as PaymentService
    participant PG as PaymentGateway
    participant SS as SlotService
    participant NS as NotificationService
    participant AUD as AuditLogger
    participant BR as BookingRepository
    participant DB as Database
    
    C->>+BC: DELETE /bookings/{bookingId}
    BC->>+BS: cancelBooking(bookingId, userId, reason)
    
    BS->>+BR: findById(bookingId)
    BR->>+DB: SELECT * FROM bookings WHERE id = ?
    DB-->>-BR: booking
    BR-->>-BS: booking
    
    %% Validate cancellation
    BS->>BS: validateCancellation(booking, userId)
    
    alt Cannot Cancel
        BS-->>BC: CancellationNotAllowedException
        BC-->>C: 400 Bad Request
    else Can Cancel
        %% Calculate refund amount
        BS->>+RS: calculateRefund(booking)
        RS-->>-BS: refundAmount
        
        %% Update booking status
        BS->>+BR: updateStatus(bookingId, CANCELLED)
        BR->>+DB: UPDATE bookings SET status = 'CANCELLED'
        DB-->>-BR: updated
        BR-->>-BS: updatedBooking

        BS->>+AUD: record("booking.cancelled", bookingId)
        AUD-->>-BS: logged
        
        %% Release slots
        loop For each slot in booking
            BS->>+SS: releaseSlot(slotId)
            SS->>+DB: UPDATE slots SET status = 'AVAILABLE'
            DB-->>-SS: updated
            SS-->>-BS: released
        end
        
        %% Process refund if applicable
        alt Refund Amount > 0
            BS->>+PS: initiateRefund(paymentId, refundAmount)
            PS->>+PG: refund(transactionId, amount)
            PG-->>-PS: refundResult
            
            alt Refund Success
                PS->>+DB: INSERT INTO refunds...
                DB-->>-PS: refundId
                PS-->>-BS: refundProcessed
            else Refund Failed
                PS-->>BS: refundFailed(queued for retry)
                BS->>+AUD: record("refund.failed", bookingId)
                AUD-->>-BS: logged
            end
        end
        
        %% Send notifications
        BS->>+NS: sendCancellationNotification(booking, refundAmount)
        NS-->>-BS: queued
        
        BS-->>-BC: cancellationResult
        BC-->>-C: 200 {status: cancelled, refundAmount}
    end
```

---

## SD-04: Resource Search

```mermaid
sequenceDiagram
    participant C as Client
    participant RC as ResourceController
    participant SS as SearchService
    participant ES as Elasticsearch
    participant CS as CacheService
    participant RS as ResourceService
    participant DB as Database
    
    C->>+RC: GET /resources/search?q=...&filters=...
    RC->>+SS: search(query, filters)
    
    %% Check cache first
    SS->>+CS: get(cacheKey)
    CS-->>-SS: cachedResult
    
    alt Cache Hit
        SS-->>RC: cachedResult
    else Cache Miss
        %% Build search query
        SS->>SS: buildSearchQuery(query, filters)
        
        SS->>+ES: search(searchQuery)
        ES-->>-SS: searchResults
        
        %% Get full resource details for top results
        loop For each result (top N)
            SS->>+RS: getResourceById(resourceId)
            RS->>+DB: SELECT * FROM resources WHERE id = ?
            DB-->>-RS: resource
            RS-->>-SS: resourceDetails
        end
        
        %% Cache results
        SS->>+CS: setex(cacheKey, results, TTL)
        CS-->>-SS: OK
        
        SS-->>-RC: searchResults
    end
    
    RC-->>-C: 200 {resources, total, facets}
```

---

## SD-05: Provider Creates Resource

```mermaid
sequenceDiagram
    participant C as Client
    participant RC as ResourceController
    participant RV as ResourceValidator
    participant RS as ResourceService
    participant FS as FileService
    participant GS as GeocodingService
    participant SS as SearchService
    participant RR as ResourceRepository
    participant DB as Database
    
    C->>+RC: POST /resources {name, description, location, images...}
    RC->>+RV: validate(resourceDTO)
    RV-->>-RC: validationResult
    
    RC->>+RS: createResource(providerId, dto)
    
    %% Upload images
    loop For each image
        RS->>+FS: uploadImage(imageData)
        FS-->>-RS: imageUrl
    end
    
    %% Geocode address
    RS->>+GS: geocode(address)
    GS-->>-RS: coordinates
    
    %% Save resource
    RS->>+RR: save(resource)
    RR->>+DB: INSERT INTO resources...
    DB-->>-RR: resourceId
    RR-->>-RS: savedResource
    
    %% Generate initial slots
    RS->>RS: generateSlots(resource, defaultSchedule)
    RS->>+DB: INSERT INTO slots... (batch)
    DB-->>-RS: slotsCreated
    
    %% Index for search
    RS->>+SS: indexResource(resource)
    SS-->>-RS: indexed
    
    alt Auto-Approve Enabled
        RS->>+RR: updateStatus(resourceId, ACTIVE)
        RR-->>-RS: activated
        RS-->>RC: resourceCreated(resourceId, status: ACTIVE)
    else Manual Approval Required
        RS-->>RC: resourceCreated(resourceId, status: PENDING_REVIEW)
    end
    
    RC-->>-C: 201 {resourceId, status}
```

---

## SD-06: Send Booking Reminder

```mermaid
sequenceDiagram
    participant SC as Scheduler
    participant NS as NotificationService
    participant BR as BookingRepository
    participant NR as NotificationRepository
    participant UP as UserPreferencesService
    participant EP as EmailProvider
    participant PP as PushProvider
    participant SP as SMSProvider
    participant DB as Database
    
    SC->>+NS: processReminders()
    
    NS->>+BR: getBookingsForReminder(reminderTime)
    BR->>+DB: SELECT * FROM bookings WHERE start_time BETWEEN...
    DB-->>-BR: bookings
    BR-->>-NS: upcomingBookings
    
    loop For each booking
        NS->>+UP: getPreferences(userId)
        UP->>+DB: SELECT * FROM notification_preferences...
        DB-->>-UP: preferences
        UP-->>-NS: userPrefs
        
        NS->>NS: buildNotificationContent(booking)
        
        par Send via Email
            opt Email Enabled
                NS->>+EP: send(email, subject, body)
                EP-->>-NS: emailResult
            end
        and Send via Push
            opt Push Enabled
                NS->>+PP: send(deviceTokens, payload)
                PP-->>-NS: pushResult
            end
        and Send via SMS
            opt SMS Enabled
                NS->>+SP: send(phone, message)
                SP-->>-NS: smsResult
            end
        end
        
        NS->>+NR: save(notificationLog)
        NR->>+DB: INSERT INTO notifications...
        DB-->>-NR: saved
        NR-->>-NS: logged
    end
    
    NS-->>-SC: remindersProcessed(count)
```

---

## SD-07: Handle Payment Webhook

```mermaid
sequenceDiagram
    participant PG as Payment Gateway
    participant WC as WebhookController
    participant WV as WebhookValidator
    participant PS as PaymentService
    participant BS as BookingService
    participant NS as NotificationService
    participant PR as PaymentRepository
    participant DB as Database
    participant WHR as WebhookRepository
    participant AUD as AuditLogger
    
    PG->>+WC: POST /webhooks/payment {event, data, signature}
    
    WC->>+WV: verifySignature(payload, signature, secret)
    WV-->>-WC: isValid
    
    alt Invalid Signature
        WC-->>PG: 401 Unauthorized
    else Valid Signature
        WC->>WC: parseEvent(payload)
            WC->>+WHR: upsert(providerEventId, payload)
            WHR->>+DB: INSERT ... ON CONFLICT DO NOTHING
            DB-->>-WHR: stored|duplicate
            WHR-->>-WC: status
        
        alt Event: payment.success
            WC->>+PS: handlePaymentSuccess(data)
            PS->>+PR: findByGatewayTxnId(txnId)
            PR-->>-PS: payment
            
            PS->>+PR: updateStatus(paymentId, COMPLETED)
            PR->>+DB: UPDATE payments SET status = 'COMPLETED'
            DB-->>-PR: updated
            PR-->>-PS: payment
            
            PS->>+BS: confirmBooking(bookingId)
            BS-->>-PS: confirmed
            
            PS->>+NS: sendPaymentConfirmation(payment)
            NS-->>-PS: queued
            PS->>+AUD: record("payment.success", paymentId)
            AUD-->>-PS: logged
            
            PS-->>-WC: handled
            
        else Event: payment.failed
            WC->>+PS: handlePaymentFailure(data)
            PS->>+PR: updateStatus(paymentId, FAILED)
            PR-->>-PS: updated
            
            PS->>+BS: cancelPendingBooking(bookingId)
            BS-->>-PS: cancelled
            
            PS->>+NS: sendPaymentFailedNotification(payment)
            NS-->>-PS: queued
            PS->>+AUD: record("payment.failed", paymentId)
            AUD-->>-PS: logged
            
            PS-->>-WC: handled
            
        else Event: refund.processed
            WC->>+PS: handleRefundProcessed(data)
            PS->>+PR: updateRefundStatus(refundId, COMPLETED)
            PR-->>-PS: updated
            
            PS->>+NS: sendRefundConfirmation(refund)
            NS-->>-PS: queued
            PS->>+AUD: record("refund.processed", refundId)
            AUD-->>-PS: logged
            
            PS-->>-WC: handled
        end
        
        WC-->>-PG: 200 OK
    end
```

---

## Sequence Diagram Summary

| Diagram | Primary Flow | Key Components |
|---------|--------------|----------------|
| SD-01 | User Registration | AuthController, UserService, EmailService |
| SD-02 | Complete Booking | BookingService, SlotService, PaymentService, Cache |
| SD-03 | Cancel with Refund | BookingService, RefundService, SlotService |
| SD-04 | Resource Search | SearchService, Elasticsearch, Cache |
| SD-05 | Provider Creates Resource | ResourceService, FileService, GeocodingService |
| SD-06 | Booking Reminder | NotificationService, Scheduler, Providers |
| SD-07 | Payment Webhook | WebhookController, PaymentService, BookingService |
