# Data Dictionary - Slot Booking System

## Core Entities

### User
- **id**: UUID
- **role**: customer | provider | admin
- **status**: active | suspended

### Resource
- **id**: UUID
- **name**: string
- **type**: room | court | professional | equipment
- **ownerId**: UUID

### Slot
- **id**: UUID
- **resourceId**: UUID
- **startTime**: ISO 8601
- **endTime**: ISO 8601
- **status**: available | reserved | booked | blocked

### Booking
- **id**: UUID
- **userId**: UUID
- **slotId**: UUID
- **status**: pending | confirmed | cancelled | completed | no_show
- **createdAt**: ISO 8601

### Payment
- **id**: UUID
- **bookingId**: UUID
- **status**: authorized | captured | failed | refunded
- **amount**: decimal

### Notification
- **id**: UUID
- **bookingId**: UUID
- **channel**: email | sms | push
- **status**: sent | failed