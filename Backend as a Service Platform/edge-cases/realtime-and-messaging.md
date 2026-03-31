# Edge Cases – Realtime and Messaging

## Scenarios

| # | Scenario | Severity | Risk | Mitigation |
|---|----------|----------|------|-----------|
| 1 | Event provider guarantees only at-least-once delivery | High | Duplicate consumer processing | Require consumer idempotency; every message carries a unique `messageId`; consumers deduplicate using Redis set |
| 2 | WebSocket client disconnects during message fan-out | Medium | Message lost for that subscriber | In-flight messages buffered per subscription for 30 seconds; client re-subscribes and requests replay from `lastMessageId` |
| 3 | Kafka consumer group rebalance during active processing | Medium | Messages re-processed or temporarily delayed | Workers use Kafka transactions with `read_committed` isolation; rebalance triggers graceful drain before partition handoff |
| 4 | Webhook endpoint unavailable at delivery time | Medium | Webhook message lost silently | Exponential retry: 1m, 5m, 30m, 2h, 24h; after 5 failures move to dead-letter queue; owner notified |
| 5 | Channel subscription authorization bypass | Critical | Subscriber receives messages for unauthorized channels | JWT channel claim validated on every WebSocket frame, not just at connect time |
| 6 | Message bus throughput spike exceeds partition count | High | Consumer lag grows; message delivery delayed | Auto-create partitions policy; alert on consumer lag > 10,000 messages; scale workers via HPA |
| 7 | Realtime gateway pod crashes with active WebSocket connections | High | All connected clients lose subscriptions | Clients implement exponential backoff reconnect; events facade assigns `sessionToken` allowing state resume |

## Deep Edge Cases

### At-Least-Once Deduplication
```typescript
async function processMessage(msg: KafkaMessage): Promise<void> {
  const dedupKey = `dedup:${msg.headers['messageId']}`;
  const isNew = await redis.set(dedupKey, '1', 'EX', 3600, 'NX');
  if (!isNew) return; // already processed
  await handleMessage(msg);
}
```

### WebSocket Replay on Reconnect
Client sends on reconnect:
```json
{ "type": "subscribe", "channelId": "ch_abc", "lastMessageId": "msg_xyz" }
```
Events facade queries Kafka offset corresponding to `msg_xyz` and replays messages from that point, subject to a 24-hour replay window.

### Webhook Retry Dead-Letter
After 5 failed delivery attempts:
1. `delivery_records` entry marked `dead-lettered`.
2. `WebhookDeadLettered` event emitted.
3. Project Owner receives notification with last error response.
4. Owner can inspect dead-letter queue via `GET /api/v1/events/subscriptions/{id}/dead-letters` and trigger manual re-delivery.

## State Impact Summary

| Scenario | Subscription / Delivery State |
|----------|------------------------------|
| Successful delivery | `pending` → `delivered` |
| Provider unavailable | `pending` → `retrying` (up to 5 times) → `dead-lettered` |
| Duplicate message | Second processing skipped; no state change |
| WebSocket reconnect | Subscription `active`; replayed from last offset |
| Authorization failure | WebSocket connection closed; `UnauthorizedChannelAccess` event emitted |
