# Shipping and Delivery Exceptions

## Failure Mode
Line-haul handoff is acknowledged but branch delivery status events stop due to partner API outage.

## Impact
Tracking freezes, SLA penalties increase, and customer confidence drops.

## Detection
Transit watchdog alerts when shipment status has no progression beyond expected dwell threshold.

## Recovery / Mitigation
Switch to fallback carrier integration, expose degraded tracking banner, and execute proactive ETA communication.
