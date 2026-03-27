# Booking Extensions and Partial Returns

## Failure Modes
- Extension approved despite conflicting future reservation
- Partial return billed as full return or vice versa
- Asset state split across units/components not reflected in contract

## Controls
- Extension pre-check against dependent reservations and buffers
- Unit-level return events and pro-rated billing adjustments
- Explicit partial-fulfillment/partial-return state model
