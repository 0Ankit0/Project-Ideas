# System Sequence Diagram - Slot Booking System

> **Platform Independence**: Diagrams show black-box system interactions applicable to any booking domain.

---

## Overview

System Sequence Diagrams show the system as a black box, focusing on interactions between external actors and the system boundary without revealing internal implementation.

---

## SSD-01: User Registration

```mermaid
sequenceDiagram
    actor User
    participant System as Slot Booking System
    participant Email as Email Service
    
    User->>+System: register(email, password, name)
    System-->>System: Validate input
    System-->>System: Check duplicate email
    System-->>System: Create inactive account
    System->>Email: sendVerificationEmail(email, token)
    System-->>-User: registrationPending(message)
    
    Note over User,Email: User checks email
    
    User->>+System: verifyEmail(token)
    System-->>System: Validate token
    System-->>System: Activate account
    System-->>-User: registrationComplete(userId)
```

---

## SSD-02: User Login

```mermaid
sequenceDiagram
    actor User
    participant System as Slot Booking System
    
    User->>+System: login(email, password)
    System-->>System: Validate credentials
    alt Valid credentials
        System-->>System: Create session
        System-->>-User: loginSuccess(token, user)
    else Invalid credentials
        System-->>User: loginFailed(error)
    else Account locked
        System-->>User: accountLocked(unlockTime)
    end
```

---

## SSD-03: Browse and View Resources

```mermaid
sequenceDiagram
    actor User
    participant System as Slot Booking System
    
    User->>+System: browseResources(filters, page)
    System-->>System: Query resources
    System-->>-User: resourceList(resources, pagination)
    
    User->>+System: getResourceDetails(resourceId)
    System-->>-User: resourceDetails(resource, reviews, availability)
    
    User->>+System: getAvailableSlots(resourceId, date)
    System-->>System: Calculate available slots
    System-->>-User: slotList(slots)
```

---

## SSD-04: Complete Booking Flow

```mermaid
sequenceDiagram
    actor User
    participant System as Slot Booking System
    participant Payment as Payment Gateway
    participant Notify as Notification Service
    
    User->>+System: selectSlots(resourceId, slotIds)
    System-->>System: Validate slots available
    System-->>-User: bookingSummary(price, slots)
    
    opt Apply Promo Code
        User->>+System: applyPromoCode(code)
        System-->>System: Validate promo
        System-->>-User: updatedSummary(discountedPrice)
    end
    
    User->>+System: confirmBooking(bookingDetails)
    System-->>System: Lock slots temporarily
    System-->>-User: paymentRequired(orderId, amount)
    
    User->>+System: processPayment(orderId, paymentMethod)
    System->>+Payment: charge(amount, paymentDetails)
    Payment-->>-System: paymentResult(success/failure)
    
    alt Payment Success
        System-->>System: Create booking record
        System-->>System: Release lock, mark booked
        System->>Notify: sendConfirmation(userId, booking)
        System-->>-User: bookingConfirmed(bookingId, details)
    else Payment Failed
        System-->>System: Release slot lock
        System-->>User: paymentFailed(error)
    end
```

---

## SSD-05: Cancel Booking

```mermaid
sequenceDiagram
    actor User
    participant System as Slot Booking System
    participant Payment as Payment Gateway
    participant Notify as Notification Service
    
    User->>+System: requestCancellation(bookingId)
    System-->>System: Validate cancellation eligibility
    System-->>-User: cancellationPolicy(refundAmount, policy)
    
    User->>+System: confirmCancellation(bookingId, reason)
    System-->>System: Update booking status
    System-->>System: Release slot
    
    alt Refund Applicable
        System->>+Payment: refund(transactionId, amount)
        Payment-->>-System: refundResult(success)
    end
    
    System->>Notify: sendCancellationNotice(userId, booking)
    System-->>-User: cancellationConfirmed(refundDetails)
```

---

## SSD-06: Provider Adds Resource

```mermaid
sequenceDiagram
    actor Provider
    participant System as Slot Booking System
    participant Storage as File Storage
    participant Maps as Maps Service
    
    Provider->>+System: createResource(basicInfo)
    System-->>-Provider: resourceDraft(draftId)
    
    Provider->>+System: uploadImages(draftId, images)
    System->>+Storage: store(images)
    Storage-->>-System: imageUrls
    System-->>-Provider: imagesAdded(urls)
    
    Provider->>+System: setLocation(draftId, address)
    System->>+Maps: geocode(address)
    Maps-->>-System: coordinates
    System-->>-Provider: locationSet(mapPreview)
    
    Provider->>+System: configurePricing(draftId, pricingRules)
    System-->>-Provider: pricingConfigured()
    
    Provider->>+System: setAvailability(draftId, schedule)
    System-->>System: Generate slot template
    System-->>-Provider: availabilitySet()
    
    Provider->>+System: publishResource(draftId)
    System-->>System: Validate completeness
    alt Auto-Approved
        System-->>System: Activate resource
        System-->>-Provider: resourceLive(resourceId)
    else Needs Approval
        System-->>Provider: pendingApproval(message)
    end
```

---

## SSD-07: Provider Views Bookings

```mermaid
sequenceDiagram
    actor Provider
    participant System as Slot Booking System
    
    Provider->>+System: getMyResources()
    System-->>-Provider: resourceList(resources)
    
    Provider->>+System: getBookingsCalendar(resourceId, dateRange)
    System-->>-Provider: calendarData(bookings)
    
    Provider->>+System: getBookingDetails(bookingId)
    System-->>-Provider: bookingDetails(user, slot, payment)
    
    opt Contact User
        Provider->>+System: sendMessage(bookingId, message)
        System-->>System: Send to user
        System-->>-Provider: messageSent()
    end
```

---

## SSD-08: Admin Approves Provider

```mermaid
sequenceDiagram
    actor Admin
    participant System as Slot Booking System
    participant Notify as Notification Service
    
    Admin->>+System: getPendingProviders()
    System-->>-Admin: providerList(applications)
    
    Admin->>+System: getProviderDetails(providerId)
    System-->>-Admin: applicationDetails(docs, info)
    
    alt Approve
        Admin->>+System: approveProvider(providerId)
        System-->>System: Activate provider account
        System->>Notify: sendApprovalNotice(providerId)
        System-->>-Admin: providerApproved()
    else Reject
        Admin->>+System: rejectProvider(providerId, reason)
        System-->>System: Mark rejected
        System->>Notify: sendRejectionNotice(providerId, reason)
        System-->>-Admin: providerRejected()
    end
```

---

## SSD-09: Receive Notification Flow

```mermaid
sequenceDiagram
    participant System as Slot Booking System
    participant Notify as Notification Service
    participant Push as Push Service
    participant Email as Email Service
    participant SMS as SMS Service
    actor User
    
    Note over System: Event Triggered (e.g., booking created)
    
    System->>+Notify: notify(userId, eventType, data)
    Notify-->>Notify: Get user preferences
    
    par Email Channel
        Notify->>Email: sendEmail(email, template, data)
        Email-->>User: Email Delivered
    and Push Channel
        Notify->>Push: sendPush(deviceToken, message)
        Push-->>User: Push Received
    and SMS Channel
        Notify->>SMS: sendSMS(phone, message)
        SMS-->>User: SMS Received
    end
    
    Notify-->>-System: notificationSent()
```

---

## SSD-10: Search Resources

```mermaid
sequenceDiagram
    actor User
    participant System as Slot Booking System
    participant Maps as Maps Service
    
    User->>+System: searchResources(query, filters)
    
    opt Location-based search
        System->>+Maps: geocode(location)
        Maps-->>-System: coordinates
        System-->>System: Filter by distance
    end
    
    System-->>System: Apply filters (category, price, rating)
    System-->>System: Rank results
    System-->>-User: searchResults(resources, facets)
```

---

## Summary of System Operations

| SSD | Primary Operation | Actors | External Systems |
|-----|-------------------|--------|------------------|
| 01 | Registration | User | Email Service |
| 02 | Login | User | - |
| 03 | Browse Resources | User | - |
| 04 | Complete Booking | User | Payment, Notification |
| 05 | Cancel Booking | User | Payment, Notification |
| 06 | Add Resource | Provider | Storage, Maps |
| 07 | View Bookings | Provider | - |
| 08 | Approve Provider | Admin | Notification |
| 09 | Send Notification | System | Push, Email, SMS |
| 10 | Search Resources | User | Maps |
