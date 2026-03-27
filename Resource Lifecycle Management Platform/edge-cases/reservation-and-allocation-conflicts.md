# Reservation and Allocation Conflicts

## Failure Mode
Concurrent reservation requests allocate the same resource instance due to delayed lock release propagation.

## Impact
Double-bookings, manual reallocations, and service-level breaches.

## Detection
Conflict detector flags overlapping active allocations for identical resource/time windows.

## Recovery / Mitigation
Use strict reservation tokens, hold-expiry sweeps, and policy-driven priority resolution with customer rebooking automation.
