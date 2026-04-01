# API and UI Edge Cases - Event Ticketing Platform

This document outlines critical edge cases in API functionality and user interface interactions for the Event Ticketing Platform.

---

## 1. Redis Hold Lock Expires During Checkout (Race Condition)

### Scenario
A customer selects 4 seats and creates a ticket hold (10-minute TTL). After 9 minutes, the customer begins checkout (payment). At 10:01 minutes, the hold expires automatically. The customer completes payment, but the seats are no longer reserved and have been sold to another customer. The order creation fails because the seats are no longer available.

### Failure Mode
- Customer creates hold at T=0
- Hold TTL = 10 minutes, expires at T=10
- Customer starts checkout at T=9
- Hold expires at T=10:01
- Customer completes payment at T=10:30
- Seats no longer reserved (another customer purchased them)
- Order creation fails: "Seats no longer available"

### Impact
- **Customers:** Payment processed but no seats allocated, poor experience
- **Business:** Customer churn, support cost, refund needed
- **Operational:** Edge case handling required

### Detection
- Order creation fails: "Seats not available"
- Check hold status: EXPIRED
- Identify: payment succeeded but seats unavailable

### Mitigation
- **Extended TTL:** Increase hold TTL to accommodate checkout process
  - Current: 10 minutes
  - Recommendation: 15-20 minutes
  - Trade-off: less seats available for other customers
- **Dynamic TTL:** Extend TTL on user interaction
  - Reset timer when user views checkout
  - Reset timer when user enters payment info
  - Keeps hold alive as long as customer is active
- **Hold-to-Order Conversion:** Atomic operation
  - Convert hold to order immediately after payment authorization
  - Don't wait for order to be fully created
  - This prevents race condition
- **Retry Logic:** Auto-retry if hold expired
  - Customer completes payment with expired hold
  - System retries: find new available seats
  - Offer customer: "Seats unavailable. Rebooking similar seats"
  - If successful: fulfill order
  - If unsuccessful: full refund + apology

### Recovery Steps
1. Payment completed successfully
2. Order creation attempts
3. Check hold status: EXPIRED
4. Handle gracefully:
   - Option A: Find alternative seats (if available)
     - Notify customer: "Your seats unavailable, similar seats assigned"
     - Update order with new seats
     - Proceed with order creation
   - Option B: Issue refund
     - Refund payment to customer
     - Send apology + offer discount on future purchase
     - Create incident ticket to improve UX
5. Prevent recurrence:
   - Review hold TTL setting
   - Implement extended TTL or dynamic refresh
   - Improve checkout flow to be faster

### Related Systems
- Inventory Service (hold management)
- Order Service (order creation)
- Payment Service (payment processing)
- Seat management

---

## 2. Stripe Payment Webhook Delivery Failure

### Scenario
A customer completes payment. Stripe charges the customer and publishes a "payment.succeeded" webhook event. The webhook delivery to the platform's order service fails (network timeout, platform temporarily down). The webhook is retried by Stripe (default: 5 retries over 24 hours), but the order is never created. The customer has been charged but has no order/ticket.

### Failure Mode
- Payment completed → Stripe charges customer
- Webhook published: "charge.completed"
- Webhook delivery fails (platform offline, network error)
- Stripe retries: still failing after 5 attempts
- Order creation never happens
- Customer charged, no tickets allocated

### Impact
- **Customers:** Payment charged, no order confirmation, frustrated
- **Business:** Manual order creation required, support cost
- **Compliance:** Financial reconciliation issues

### Detection
- Customer calls support: "I paid but got no ticket"
- Monitor webhook delivery: failed events in Stripe dashboard
- Alert on failed webhooks (>10 failed in 1 hour)
- Reconciliation: compare payments in Stripe vs orders in database

### Mitigation
- **Webhook Reliability:**
  - Implement webhook endpoint with HTTP 200 response quickly
  - Process webhook asynchronously (return 200, process in background)
  - Idempotent processing: safe to process same webhook twice
- **Webhook Retry Monitoring:**
  - Monitor Stripe dashboard for failed webhooks
  - Alert on failures (can be automated via Stripe API)
  - Manual investigation if failures exceed threshold
- **Duplicate Detection:**
  - Track processed webhook IDs (in database)
  - Before processing: check if already processed
  - If duplicate: skip processing (idempotent)
- **Fallback Processing:**
  - Scheduled job: query Stripe for recent payments
  - Compare against orders in database
  - Create missing orders for successful payments
  - Alert if discrepancy detected

### Recovery Steps
1. Failed webhook detected (either via Stripe alert or customer complaint)
2. Investigation:
   - Check Stripe dashboard: find payment record
   - Verify payment status: succeeded
   - Check orders database: order exists?
3. If order missing:
   - Manually create order from payment details
   - Generate and send ticket
   - Send apology + refund stripe fee (if applicable)
4. Prevention:
   - Improve webhook endpoint robustness
   - Add monitoring for webhook failures
   - Implement scheduled reconciliation job
5. Stripe configuration:
   - Adjust retry settings if needed
   - Test webhook endpoint availability before deployment

### Related Systems
- Payment Service (webhook endpoint)
- Order Service (order creation)
- Stripe integration
- Database (idempotency tracking)
- Monitoring system

---

## 3. QR Code Validation API Rate Limit Hit During Mass Check-In

### Scenario
A large event (50K attendees) begins check-in. Hundreds of check-in scanners (mobile devices) attempt to validate QR codes simultaneously. The QR code validation API has a rate limit of 100 req/s. The system is overwhelmed, and check-in requests are throttled (HTTP 429). Physical lines at venue gates are delayed, frustrating attendees.

### Failure Mode
- Event check-in begins: 500+ concurrent check-in attempts
- API rate limit: 100 req/s
- Excess requests: queued or rejected (HTTP 429)
- Physical check-in lines: long delays
- User experience: frustrating, negative reviews

### Impact
- **Customers:** Long lines, frustration, poor experience
- **Operations:** Check-in delays, venue congestion
- **Reputation:** Negative social media posts

### Detection
- QR validation API error rate increases
- Rate limit errors (HTTP 429) increase
- Check-in latency increases
- Physical lines reported too long

### Mitigation
- **Rate Limit Increase:** Higher limit during check-in period
  - Baseline: 100 req/s
  - During check-in: 500-1000 req/s
  - Infrastructure scaling to support
- **Batch Processing:** Scanners can validate multiple QR codes
  - Send batch of 10 QR codes in single request
  - Reduces API calls by 10x
  - Requires scanner app update
- **Offline Check-in:** Scanners pre-download QR database
  - Download all event QR codes before event
  - Validate locally (no API call)
  - Sync results after event (when network less congested)
  - Works even if internet down
- **Graceful Degradation:** Manual fallback
  - If API unavailable, scanners fall back to manual lookup
  - Scan QR, check against printed list
  - Manual mark as checked-in
- **Queue System:** Manage traffic intelligently
  - Rate limit at API Gateway
  - Queue excess requests
  - Process queued requests when capacity available
  - Return estimated wait time to scanner

### Recovery Steps
1. Rate limit errors detected during check-in
2. Immediate action:
   - Alert ops team
   - Check API capacity
   - Trigger auto-scaling if configured
3. Decision:
   - If offline mode available: activate it
   - If server capacity sufficient: increase rate limit
   - Otherwise: activate manual fallback
4. Communication:
   - Update scanners: "Using offline mode" or "Manual check-in"
   - Alert venue staff about check-in process change
5. Post-event:
   - Analyze check-in volume and timing
   - Update rate limits based on actual usage
   - Plan for next event: pre-scale infrastructure
   - Consider offline mode for future events

### Related Systems
- Check-In Service (QR validation)
- API Gateway (rate limiting)
- Mobile scanner app
- Event management

---

## 4. Seat Map Rendering Failure for Large Venue (20K Seats)

### Scenario
A large venue with 20K seats (e.g., stadium). Customer tries to select seats in the web browser. The seating map is rendered as SVG with 20K seat elements. The browser struggles to render all seats, becoming slow and unresponsive. Customer cannot complete their selection.

### Failure Mode
- Seating map with 20K SVG elements
- Browser rendering: very slow (several seconds)
- User interaction (click seats): laggy, unresponsive
- Mobile browser: more severe (less memory)
- Customer abandons purchase, lost revenue

### Impact
- **Customers:** Poor UX, cannot complete purchase
- **Business:** Lost revenue, customer churn
- **Operational:** Support complaints

### Detection
- Monitor page load time for seating map (separate metric)
- Alert if load time > 3 seconds
- Monitor user interactions: click responsiveness
- User feedback: complaints about slowness

### Mitigation
- **Lazy Rendering:** Render only visible seats
  - Render entire section, but only visible portion
  - As user scrolls, render new portions
  - Reduces DOM elements significantly
  - Uses virtual scrolling (React-window, etc.)
- **Section-Based View:** Instead of full seating map
  - Show list of sections
  - User selects section
  - Render only that section (e.g., 500 seats)
  - Much faster
- **Canvas Rendering:** Instead of SVG
  - Use HTML5 Canvas for rendering
  - More efficient for large datasets
  - Allows custom interactions (click detection)
- **Clustering:** Group adjacent seats
  - Group by section or row
  - Show aggregate (e.g., "Row A: 50 available")
  - User expands section to see individual seats
- **Server-Side Rendering:** Generate seating map on server
  - Server-side rendering avoids browser overhead
  - Send pre-rendered HTML or image
  - User can still interact (click to select)

### Recovery Steps
1. User reports slow seating map
2. Investigate:
   - Check event size (number of seats)
   - Check browser rendering performance
   - Identify bottleneck (rendering, interaction, etc.)
3. Implement solution:
   - Lazy rendering (immediate improvement)
   - Or: Canvas rendering
   - Or: Section-based view
4. Test:
   - Load time should be <1 second
   - Interaction should be responsive (<100ms)
5. Deploy and monitor:
   - Measure improvement
   - Track page load time
   - Monitor user feedback

### Related Systems
- Frontend (React/Vue)
- Seat Management Service (backend API)
- Event Management

---

## 5. Mobile App Deep Link Failure for Ticket Transfer

### Scenario
A customer transferred their ticket to a friend via link (deep link). The friend receives the link in SMS: "myapp://tickets/ABC123DEF456". The friend doesn't have the app installed. They click the link, which opens the app store, but after installing and launching the app, the deep link doesn't work (app doesn't navigate to the ticket). The friend cannot access the transferred ticket.

### Failure Mode
- Customer sends deep link to friend
- Friend clicks link, app not installed
- Redirected to app store
- After installation, friend launches app
- Deep link context lost (app doesn't know which ticket to show)
- Friend cannot access transferred ticket

### Impact
- **Customers:** Ticket transfer feature broken, friends cannot access ticket
- **Business:** Feature not working as expected, poor reputation
- **Operational:** Support issues

### Detection
- Mobile app analytics: track deep link failure
- Broken universal links reported by Apple/Google
- User complaints: "Cannot open transferred ticket"

### Mitigation
- **Universal Links:** Implement deep linking properly
  - iOS: Universal Links (.well-known/apple-app-site-association)
  - Android: App Links (assetlinks.json)
  - Allows seamless app opening after install
- **Fall Back to Web:** If app not installed
  - Deep link to web version: myapp.com/tickets/ABC123
  - Web version can download ticket PDF
  - Opens app if installed
- **QR Code Alternative:** Instead of deep link
  - Send QR code in SMS or email
  - Friend scans QR code
  - Opens ticket directly
  - More reliable than deep links
- **Tokenized Links:** Include auth token in link
  - Link format: myapp://tickets/ABC123?token=XYZ
  - Token grants access to specific ticket
  - Works even if app reinstalled

### Recovery Steps
1. Deep link failure reported by user
2. Investigate:
   - Check universal link configuration
   - Test deep link on multiple devices
   - Check app store configuration
3. User assistance:
   - Alternative: send QR code instead
   - Or: send web link that opens in browser
   - Friend can view ticket in browser
4. Fix:
   - Implement proper universal links
   - Test across platforms (iOS, Android)
   - Update app distribution
5. Communicate:
   - Explain to customers: "Share via QR code for best experience"
   - Update ticket transfer documentation

### Related Systems
- Mobile app (React Native)
- Frontend web app
- Ticket Service (ticket access)
- Deep linking infrastructure

---

## 6. Search Index Stale After Event Date Change

### Scenario
An event is scheduled for June 1, 2024. The event is indexed in Elasticsearch with date field = "2024-06-01". The organizer reschedules the event to July 15, 2024. The date is updated in the database and in the event details, but the Elasticsearch index is not updated. Customers searching for June events still see this event (stale data). The event appears in wrong search results.

### Failure Mode
- Event date changed in database: June 1 → July 15
- Event Service API returns correct date
- Elasticsearch index not updated (still shows June 1)
- Search for June events returns event that's now in July
- Customers confused, negative reviews

### Impact
- **Customers:** Stale search results, confusion
- **Business:** Poor search experience, customer churn
- **Operational:** Data inconsistency

### Detection
- Search result inconsistency detected
- Event date mismatch: database vs. search index
- User reports: "Event showing wrong date in search"
- Periodic audit: compare database and search index

### Mitigation
- **Event Streaming:** Publish events to Elasticsearch immediately
  - When event updated: publish "event.updated" event
  - Elasticsearch consumer subscribes and updates index
  - Near real-time updates (within seconds)
- **Scheduled Reindexing:** Periodic full refresh
  - Nightly reindex of all events
  - Catch any missed updates
- **Dual Write:** Write to database and Elasticsearch simultaneously
  - Ensure both are updated atomically
  - Handle failures gracefully
- **Cache Invalidation:** Invalidate search cache
  - When event updated, invalidate any cached search results
  - Force re-query from fresh index

### Recovery Steps
1. Stale search results detected
2. Immediate fix:
   - Reindex affected events in Elasticsearch
   - Update search index mapping if needed
3. Verify:
   - Search for June events: confirm event no longer appears
   - Search for July events: confirm event now appears
4. Prevention:
   - Implement event streaming to Elasticsearch
   - Set up scheduled reindexing job
   - Add monitoring to detect index staleness

### Related Systems
- Event Service (event updates)
- Elasticsearch (search index)
- Message queue (event streaming)
- Frontend search

---

## Summary

These API and UI edge cases highlight the importance of:
1. **Thoughtful timeouts and TTLs**
2. **Asynchronous processing and retry logic**
3. **Proper deep linking and mobile app handling**
4. **Search index consistency**
5. **Rate limiting and capacity planning**
6. **Graceful degradation and fallbacks**

All edge cases require monitoring, alerting, and clear communication with customers when issues occur.
