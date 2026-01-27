# Event Catalog - Slot Booking System

| Event | Producer | Consumers | Description |
|-------|----------|-----------|-------------|
| slot.created | Provider Portal | Availability Service | New slot added |
| slot.reserved | Booking Service | Payment Service | Slot held for checkout |
| booking.confirmed | Booking Service | Notification Service | Booking finalized |
| payment.captured | Payment Service | Booking Service | Payment completed |
| booking.cancelled | Booking Service | Notification Service | Booking cancelled |
| refund.processed | Payment Service | Booking Service | Refund completed |
| no_show.marked | Provider Portal | Analytics | No-show recorded |