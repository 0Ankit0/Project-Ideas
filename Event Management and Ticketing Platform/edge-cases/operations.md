# Operations Edge Cases - Event Ticketing Platform

This document outlines critical edge cases in operational management for the Event Ticketing Platform.

---

## 1. Onsale Traffic Spike Overwhelming Ticket Hold System

### Scenario
A high-demand event (e.g., major artist) goes on sale. 100K users hit the platform simultaneously. The ticket hold system (Redis) is designed to handle 10K concurrent holds. The system becomes CPU-bound, hold creation latency spikes to 5+ seconds. Some customers get timeout errors. Customer experience degrades, conversion rate drops.

### Failure Mode
- Event on-sale: 100K concurrent users
- System capacity: 10K concurrent holds
- Traffic surge: 10x expected capacity
- Redis CPU: 100%, requests queued
- Latency: normal 50ms → 5+ seconds
- Timeouts: HTTP 504 errors returned to customers

### Impact
- **Customers:** Slow experience, timeouts, frustration
- **Business:** Lost revenue (failed conversions)
- **Reputation:** Poor onsale experience

### Detection
- API latency dashboard: p95 latency >1 second
- Error rate: >0.1% receiving HTTP 504
- Redis metrics: CPU >90%, queue depth increasing
- Customer complaints: "Page is slow" during onsale

### Mitigation
- **Capacity Planning:** Size infrastructure for peak
  - Estimate peak capacity (e.g., 100K concurrent)
  - Provision infrastructure for 1.5x peak (safety margin)
  - Test under load before major onsales
- **Auto-Scaling:** Auto-scale components
  - API Gateway (Kong): scale to handle request volume
  - InventoryService: scale to handle hold creation
  - Database: read replicas for queries, connection pooling
- **Queue System:** Virtual waiting room
  - During peak, route customers to queue instead of direct hold
  - Serve customers FIFO from queue
  - Prevents overwhelming system
- **Caching:** Reduce database load
  - Cache frequently accessed data (event details, pricing)
  - 30-second cache TTL for seat maps
  - Reduces database queries by 80%
- **Load Testing:** Validate before onsale
  - Simulate 100K concurrent users
  - Measure latency, throughput, error rate
  - Identify and fix bottlenecks
- **Graceful Degradation:** Reduce functionality under load
  - Complex queries (filters): disabled
  - Simple operations (holds): prioritized
  - Inform customers: "System at capacity, using simplified mode"

### Recovery Steps
1. Onsale begins, traffic surge detected
2. Alert ops team immediately
3. Monitoring:
   - Real-time dashboard showing latency, errors, queue depth
   - Escalate if latency >1 second
4. Response:
   - Trigger auto-scaling (if configured)
   - Manually scale (if auto-scaling not fast enough)
   - Activate queue system if capacity exceeded
5. Communication:
   - Status page: "High demand, may experience slow load"
   - SMS to customers: "Long wait expected, check back later"
6. Post-onsale:
   - Analyze traffic patterns
   - Update capacity planning
   - Plan infrastructure upgrades if needed

### Related Systems
- API Gateway, InventoryService, Redis
- Auto-scaling configuration
- Queue management
- Monitoring and alerting

---

## 2. Redis Cluster Failure During Active Onsale Event

### Scenario
During an active onsale (10K concurrent holds), the Redis cluster experiences a failure: one shard goes down due to hardware failure. The cluster loses quorum and cannot accept new writes. Ticket hold creation fails. Customers cannot complete purchases.

### Failure Mode
- Redis cluster: 3 shards, 2 replicas per shard = 6 nodes
- One shard primary goes down (hardware failure)
- Failover mechanism fails (replica not promoting)
- Cluster loses quorum (cannot commit writes)
- Hold creation fails, customers receive errors

### Impact
- **Customers:** Cannot buy tickets, onsale fails
- **Business:** Revenue loss, reputation damage

### Detection
- Redis cluster health monitoring
- Alert on node failure
- Alert on cluster quorum loss
- Hold creation errors increase to 100%

### Mitigation
- **Redis Cluster Setup:** Multi-AZ, multiple nodes
  - Minimum 3 shards, 2 replicas each (6 nodes total)
  - Across 3 different AZs (automatic failover between AZs)
- **Monitoring & Alerting:** Continuous health check
  - Monitor node health (CPU, memory, responsiveness)
  - Alert on node failure
  - Alert on cluster quorum loss
- **Failover Strategy:** Automatic promotion of replicas
  - AWS ElastiCache handles automatic failover (within 30 seconds)
  - Manual failover if automatic fails
- **Fallback Mode:** If Redis unavailable
  - Option 1: Operate in degraded mode (no holds, direct to payment)
  - Option 2: Use secondary data store (PostgreSQL for holds)
  - Option 3: Queue all orders, process offline (not ideal)
- **Redundancy:** Multiple Redis clusters
  - Primary cluster for low latency
  - Standby cluster for failover
  - Requires cross-cluster replication (complex)

### Recovery Steps
1. Redis cluster failure detected
2. Immediate diagnosis:
   - Check node status in AWS console
   - Identify failed node(s)
   - Check cluster quorum status
3. Response:
   - If automatic failover not triggered: manually trigger
   - Or: switch to fallback mode if recovery will take time
4. During outage:
   - Activate fallback mode (degraded functionality)
   - Queue ticket hold requests
   - Process holds once Redis recovered
   - Communicate to customers: "Hold system temporarily unavailable"
5. Post-recovery:
   - Verify all holds processed correctly
   - Check for data consistency
   - Investigate root cause of failure
   - Update runbooks based on incident

### Related Systems
- Redis cluster (ElastiCache)
- InventoryService
- Fallback data store (PostgreSQL)
- Monitoring system

---

## 3. Database Deadlock During High-Concurrency Ticket Checkout

### Scenario
During high-volume ticket checkout, multiple concurrent transactions attempt to update the same database records (order, payment, inventory). Transaction A locks order table, waits for payment table. Transaction B locks payment table, waits for order table. Deadlock occurs. PostgreSQL detects deadlock, cancels one transaction. Customer receives error: "Transaction failed, please try again."

### Failure Mode
- High-concurrency checkout (1000+ concurrent)
- Transactions locking tables in different order
- Deadlock: Transaction A ← Transaction B ← Transaction A
- Database cancels one transaction
- Customer error: "Transaction failed"

### Impact
- **Customers:** Checkout fails, must retry
- **Operational:** Transaction retry overhead, slower throughput

### Detection
- Database logs: deadlock errors
- Alert on deadlock frequency (>1 per minute = problem)
- Monitor transaction latency: if p95 > 5 seconds = possible deadlocks

### Mitigation
- **Lock Ordering:** Ensure consistent lock acquisition order
  - All transactions lock in same order (e.g., order → payment → inventory)
  - Prevents circular wait condition
  - Reduces deadlock probability
- **Transaction Isolation:** Use appropriate isolation level
  - READ_COMMITTED: lower isolation, fewer locks, more deadlocks
  - SERIALIZABLE: highest isolation, more locks, more deadlocks
  - REPEATABLE_READ: middle ground
- **Row-Level Locking:** Instead of table locks
  - Lock only affected rows
  - Multiple transactions can work on different rows
  - Reduces lock contention
- **Deadlock Detection & Retry:**
  - Application catches deadlock error
  - Automatically retries transaction
  - Exponential backoff (1s, 2s, 4s, 8s)
  - Max 3 retries
- **Connection Pooling:** Limit concurrent connections
  - Too many connections = too many concurrent locks
  - Use connection pool to limit (100-200 connections)
- **Query Optimization:** Minimize transaction time
  - Reduce query time → shorter locks → fewer deadlocks
  - Add indexes, optimize queries
  - Move long-running operations outside transaction

### Recovery Steps
1. High deadlock rate detected
2. Investigation:
   - Review database logs for deadlock patterns
   - Identify which tables/rows involved
   - Analyze transaction locking order
3. Fix:
   - Implement lock ordering consistency
   - Optimize queries to reduce transaction time
   - Adjust isolation level if appropriate
4. Testing:
   - Load test with 1000+ concurrent transactions
   - Verify deadlock rate reduced
5. Monitoring:
   - Continue monitoring deadlock rate
   - Alert if rate increases again

### Related Systems
- PostgreSQL database
- Order Service, Payment Service
- Application transaction management
- Monitoring system

---

## 4. PDF Ticket Generation Service Failure (Email Queue Backed Up)

### Scenario
A spike in ticket orders causes the PDF generation service to become overwhelmed. PDFs queue up faster than they can be generated. The queue grows to 10K pending PDFs. Customers are not receiving their tickets for hours. Meanwhile, customers call support complaining about missing tickets.

### Failure Mode
- Ticket orders spike: 1000 orders/min
- PDF generation rate: 100 PDFs/min
- Queue growth: (1000 - 100) = 900 per minute
- After 10 minutes: 9000 pending PDFs
- Customers: no ticket for hours
- Support: overwhelmed with complaints

### Impact
- **Customers:** No ticket, cannot access event
- **Business:** Support cost, customer churn
- **Operational:** System overload

### Detection
- PDF generation queue depth: monitor
- Alert if queue depth >1000
- Alert if SLA missed (ticket not delivered within 5 minutes)
- Customer support tickets: complaints about missing tickets

### Mitigation
- **Auto-Scaling:** Scale PDF workers based on queue
  - Monitor queue depth
  - If queue >1000: spin up additional PDF workers
  - Max workers: 10-20 (based on server capacity)
- **Batch Processing:** Generate PDFs in parallel
  - Instead of sequential: PDF 1, PDF 2, PDF 3...
  - Do parallel: PDF 1-10 at same time
  - Increases throughput by 10x
- **Caching:** Cache frequently accessed components
  - Event logo, template: cache (don't regenerate)
  - Customer logo/branding: cache
  - QR code: generate once, reuse
- **Async Processing:** Don't block on PDF generation
  - Customer completes order
  - System queues PDF generation
  - Return "Order confirmed, ticket will be sent shortly"
  - Generate PDF asynchronously
  - Email ticket when ready
- **Fallback:** If generation takes >30 seconds
  - Send email immediately: "Ticket generating, download in 5 minutes"
  - Include direct link to ticket (on web, not PDF)
  - Generate PDF in background, email when ready
- **SLA Monitoring:** Ensure tickets delivered timely
  - Target: ticket delivered within 5 minutes
  - Alert if SLA missed
  - Track SLA compliance

### Recovery Steps
1. PDF queue backed up detected
2. Immediate action:
   - Trigger auto-scaling (scale up workers)
   - Monitor queue depth (should decrease)
3. If still backed up:
   - Investigate generation bottleneck
   - Check CPU, memory, disk I/O
   - Identify slow step (rendering, encryption, upload)
4. Temporary fix:
   - Send customers link to temporary ticket (not PDF)
   - Tell them PDF will be ready soon
   - Generate PDFs in background
5. Long-term fix:
   - Optimize PDF generation (faster library, better server)
   - Batch generation
   - Increase baseline worker count

### Related Systems
- Ticket Service (PDF generation)
- Background job queue
- Email service
- Monitoring system

---

## 5. Check-In Scanner App Offline During Large Event

### Scenario
A large event with 50K attendees begins check-in. The mobile check-in scanner app is offline (no internet connection at venue). Check-in scanners attempt to connect to the backend to validate QR codes, but network is unavailable. Check-in comes to a halt. Attendees cannot enter the venue.

### Failure Mode
- Event begins, check-in starts
- 500+ check-in scanners (mobile devices) attempt API calls
- Network unavailable (WiFi down, cellular network congested)
- QR code validation API calls fail
- Check-in process halts
- Attendees stuck in line, cannot enter

### Impact
- **Venues:** Cannot process attendees, safety/compliance issue
- **Customers:** Cannot enter event, frustrated
- **Business:** Poor event experience, reputation damage

### Detection
- Check-in API: network errors increase
- Scanner apps: report network unavailable
- Venue staff: report long lines

### Mitigation
- **Offline Mode:** Scanners work without network
  - Pre-download QR code database before event
  - Validate QR codes locally (no API call needed)
  - Sync results after event (when network available)
  - Process:
    1. Download all event QR codes to device (100MB for 50K tickets)
    2. Scan QR code, validate locally against database
    3. Mark attendee locally (in app database)
    4. After event, sync with backend
- **Fallback:** Manual check-in process
  - Print attendee list
  - Check off names as attendees arrive
  - Manual scanning as backup
- **Network Redundancy:** Multiple connectivity options
  - Cellular network (as backup to WiFi)
  - WiFi mesh network (extended coverage at venue)
  - Satellite connectivity (extreme backup)
- **Graceful Degradation:** Prioritize critical functions
  - If network slow: cache results locally, sync when available
  - If network unavailable: use offline mode
  - Clear communication: "Offline mode enabled, check-in via local database"

### Recovery Steps
1. Network unavailable during check-in
2. Immediate action:
   - Alert venue staff
   - Switch to offline mode (if available)
   - Activate manual fallback process
3. Investigation:
   - Check WiFi network status
   - Check cellular coverage
   - Identify network outage root cause
4. Remediation:
   - Restart WiFi (if needed)
   - Switch to cellular network
   - Activate satellite connectivity (if extreme)
5. Communication:
   - Inform venue staff: "Using offline mode"
   - Inform attendees: "Slight delay in check-in, but moving forward"
6. Post-event:
   - Sync check-in data from all offline scanners
   - Verify data consistency
   - Review network performance
   - Plan for future (better network planning)

### Related Systems
- Check-In Service (mobile app)
- Mobile device storage (for offline database)
- Network/WiFi infrastructure
- Backend sync service

---

## 6. Mass Email Notification Failure (Ticket Confirmation Emails)

### Scenario
An order confirmation email should be sent to 10K customers after their ticket purchase during a large onsale. The email service (SES) is throttled or temporarily unavailable. Only 1000 confirmation emails are sent. 9000 customers don't receive confirmation. Customers don't know if purchase succeeded. Support is flooded with inquiries.

### Failure Mode
- 10K orders completed
- Email service should send 10K confirmations
- Email service unavailable or throttled
- Only 1000 emails sent
- 9000 customers don't receive confirmation
- Uncertainty, support cost, customer churn

### Impact
- **Customers:** No confirmation, uncertainty
- **Business:** Support overhead, lost trust
- **Operational:** Manual email sending required

### Detection
- Email service error monitoring
- Alert on SES throttling or failures
- Monitor email send rate vs. expected
- Alert if <90% of emails sent
- Customer support complaints: "I didn't receive confirmation"

### Mitigation
- **Email Queue:** Queue emails for retry
  - SES API failure → queue email
  - Retry with exponential backoff (1s, 5s, 30s, 5min, 1hour, 1day)
  - Max 5 retries
  - Dead letter queue if all retries fail
- **Multiple Providers:** Failover to backup
  - Primary: AWS SES
  - Secondary: SendGrid or Mailgun
  - If primary fails, automatically use secondary
  - Requires dual account setup
- **SLA Monitoring:** Ensure emails delivered
  - Target: 95%+ delivery rate
  - Alert if below threshold
  - Investigate failures
- **Fallback Notification:** If email fails
  - Send SMS if phone available
  - Or: in-app notification
  - Or: display confirmation on web (customer downloads)
- **Pre-confirmation:** Immediate confirmation
  - Show order confirmation on-screen immediately
  - Email as secondary confirmation
  - Prevents "order uncertainty" if email fails

### Recovery Steps
1. Email service failure detected
2. Investigation:
   - Check SES status page
   - Check email provider status
   - Check bounce/rejection rates
3. If SES unavailable:
   - Switch to backup provider (SendGrid/Mailgun)
   - Continue sending emails
4. Retry failed emails:
   - Queue contains failed emails from outage
   - Retry queue with exponential backoff
   - Monitor retry success rate
5. Manual fallback (if needed):
   - Manually send emails to customers missing confirmation
   - Or: direct customers to web to view order
6. Communication:
   - Transparency: "Email service experienced outage"
   - Provide alternative: "View order on web"
   - Follow-up: "Confirmation email sent"

### Related Systems
- Email service (SES, SendGrid)
- Email queue (SQS/Kafka)
- Notification preferences (SMS, email, in-app)
- Order management (confirmation display)

---

## 7. Event Search Elasticsearch Downtime Before Major Announcement

### Scenario
Before a major event announcement (e.g., Taylor Swift tour announcement), the Elasticsearch cluster goes down for maintenance. Customers cannot search for events. Traffic surge hits immediately after announcement, but search is not available. Customers cannot discover the new event. Revenue opportunity lost.

### Failure Mode
- Elasticsearch maintenance scheduled
- Event search disabled during maintenance
- Major event announced (goes viral)
- Traffic surge arrives
- Search not available
- Customers cannot find event
- Lost sales opportunity

### Impact
- **Business:** Lost revenue from missed onsale surge
- **Operational:** Poor timing of maintenance

### Detection
- Elasticsearch health monitoring
- Alert on cluster unavailability
- Monitor search API: error rate increases

### Mitigation
- **Maintenance Scheduling:** Avoid high-demand periods
  - Don't schedule maintenance before major announcements
  - Coordinate with marketing team
  - Use off-peak windows (e.g., 3 AM)
- **Zero-Downtime Reindex:** Minimize downtime
  - Use rolling restart (one node at a time)
  - Cluster remains operational during maintenance
  - Or: blue-green deployment (standby cluster, switch over)
- **Search Fallback:** If search unavailable
  - Fall back to database query (slower, but works)
  - Or: pre-build event listings (static HTML)
  - Or: feature event on homepage (no search needed)
- **Monitoring:** Know about issues early
  - Monitor cluster health continuously
  - Alert on degradation (latency, error rate)
  - Plan maintenance before issues become critical

### Recovery Steps
1. Elasticsearch downtime planned
2. Pre-planning:
   - Coordinate with marketing (avoid major launches)
   - Schedule for off-peak time
   - Prepare fallback (database search, static page)
3. During maintenance:
   - Monitor cluster recovery
   - Test search functionality once ready
   - Verify index consistency
4. Post-maintenance:
   - Reindex if needed
   - Verify all events searchable
   - Performance testing (no degradation)
5. Communication:
   - Inform customers: "Search temporarily unavailable"
   - Provide fallback: "Browse event categories"

### Related Systems
- Elasticsearch cluster
- Search API
- Event listing database
- Monitoring system

---

## Summary

Operational edge cases require:
1. **Proper capacity planning and load testing**
2. **High availability: redundancy, failover, auto-scaling**
3. **Graceful degradation: fallback modes, prioritization**
4. **Continuous monitoring and alerting**
5. **Clear communication and incident response**
6. **Operational runbooks and team training**

Success during high-demand onsales requires meticulous preparation and continuous improvement based on incident analysis.
