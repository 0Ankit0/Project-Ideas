# Operations Edge Cases

This document outlines critical edge cases in operational management and incident response for the Digital Banking Platform. Each scenario covers failure modes, detection mechanisms, mitigation strategies, and recovery procedures.

---

## 1. Core Banking System Sync Failure (Mambu Unavailable)

### Scenario
The platform uses Mambu as the core banking system for account management, transaction settlement, and compliance reporting. At 2:00 PM EST (peak usage time), Mambu API becomes unavailable due to a service outage. The platform is unable to process new account openings, transfers, or loan applications. Thousands of customer requests queue up with no way to complete them. The outage lasts 3 hours.

### Failure Mode
- Mambu API returns 503 Service Unavailable
- All account management operations fail (create account, transfer funds, apply for loan)
- Request queue grows: customers cannot complete operations
- Platform decision: (A) return error to customers, (B) queue requests and retry, (C) operate in degraded mode
- Outage impacts revenue (failed payments, failed transfers) and customer satisfaction

### Impact
- **Customers:** Cannot complete transactions, poor experience
- **Business:** Revenue loss (failed payments, transfers), customer churn
- **Operational:** High support volume, reputation damage

### Detection
- Mambu API health check: ping API endpoint every 30 seconds
- Alert on failure: trigger alert when >1% of Mambu requests fail
- Error rate tracking: dashboard showing Mambu request success rate
- Customer impact monitoring: detect when customers cannot complete operations
- SLA monitoring: track Mambu uptime SLA (99.5% typically)

### Mitigation
- **API retry logic:** Implement exponential backoff for Mambu requests
  - Retry 1: 1 second delay
  - Retry 2: 2 seconds delay
  - Retry 3: 4 seconds delay
  - Retry 4: 8 seconds delay
  - Max 4 retries, then fail with customer notification
- **Request queuing:** Queue failed requests for async retry
  - Store request in database with retry count
  - Async job retries queued requests every 60 seconds
  - Alert if queue depth exceeds threshold
- **Circuit breaker:** Stop calling Mambu API if failure rate >10%
  - Prevents cascading failures
  - Provide cached/fallback response instead
- **Local account cache:** Cache frequently accessed account data
  - Read-through cache: fetch from Mambu, cache for 5 minutes
  - Serve read requests from cache if Mambu unavailable
  - Write requests fail with customer notification (require Mambu availability)
- **Fallback mode:** For simple operations (balance check), serve from cache
  - For complex operations (transfer), require Mambu availability
  - Clear communication to customers: "Transfer service temporarily unavailable"
- **Mambu redundancy:** If possible, use Mambu multi-region setup
  - Route requests to backup region if primary unavailable
  - Requires data replication and failover setup

### Recovery Steps
1. Mambu API outage detected (alert triggered)
2. Incident commander notified, team assembled
3. Investigation: confirm Mambu is down, check Mambu status page
4. Decision: operate in degraded mode (read-only) or wait for recovery
5. Customer communication: status page updated, email notification sent
6. Queue processing:
   - Mambu recovery begins: queue processing resumes
   - Async job retries all queued requests
   - Monitor queue depth: should decrease as requests succeed
7. Post-outage:
   - Verify all queued requests processed successfully
   - Reconcile any transactions that failed partially (debit succeeded, credit failed)
   - Customer notification: outage resolved, service normal
8. Root cause analysis: engage Mambu support to understand cause
9. Process improvement:
   - Evaluate Mambu redundancy options
   - Improve local caching strategy
   - Review incident response process

### Related Systems
- Core banking system (Mambu)
- API gateway and retry logic
- Request queue (Kafka/SQS)
- Local cache (Redis)
- Circuit breaker (Resilience4j)
- Health check and monitoring system
- Incident management system

---

## 2. Kafka Consumer Lag During End-of-Day Batch

### Scenario
The platform uses Kafka for asynchronous processing: customers deposit checks, transfer funds, which publish events. A consumer processes these events to update account balances, trigger notifications, and prepare end-of-day reports. At 11:00 PM (end-of-day cutoff), a high-volume day causes consumer lag. The consumer is 30 minutes behind in processing events. By midnight, end-of-day batch reports must be generated, but events are still being processed, causing reports to be incomplete or delayed.

### Failure Mode
- High transaction volume during day → many Kafka events published
- Consumer processes events slower than they're produced
- Consumer lag grows: 30 minutes behind by 11:00 PM
- End-of-day batch (midnight) needs all events processed
- Reports generated with incomplete data (missing recent transactions)
- Regulatory reporting deadline miss if reports incomplete

### Impact
- **Regulatory:** Incomplete daily reports may violate regulatory reporting requirements
- **Customers:** Transaction confirmations delayed
- **Operational:** End-of-day batch fails, manual recovery required

### Detection
- Kafka consumer lag monitoring: track lag per consumer group
- Alert on threshold: trigger alert when lag > 15 minutes
- Batch job monitoring: track end-of-day batch job progress
- Consumer health dashboard: show processing rate, lag trend

### Mitigation
- **Consumer scaling:** Increase number of consumer instances during peak hours
  - Partition Kafka topics by transaction type (deposits, transfers, etc.)
  - Scale consumers independently: more consumers for high-volume partitions
  - Elastic scaling: increase consumers at 9:00 AM, decrease at 7:00 PM
- **Performance optimization:** Optimize consumer processing
  - Batch processing: process 100 events per loop instead of 1
  - Database batch operations: INSERT 100 rows in 1 query instead of 100 queries
  - Async processing: avoid blocking I/O calls
- **Prioritization:** Prioritize critical events (transactions over notifications)
  - High-priority queue: account balance updates
  - Low-priority queue: email notifications
  - Process high-priority first, low-priority if capacity available
- **Pre-processing:** Process critical events synchronously
  - Balance updates: process in request path (ensure consistency)
  - Notifications: queue for async processing
  - This way, account state is consistent, notifications may be delayed but data is accurate
- **End-of-day cutoff:** Set cutoff time earlier than midnight
  - Cutoff at 11:00 PM instead of midnight
  - 1-hour window to process remaining events before reporting
  - Transactions after 11:00 PM included in next day's report
- **Backpressure handling:** If consumer lag too high
  - Pause accepting new requests at 11:00 PM
  - Complete processing of queued events
  - Resume at midnight after reports generated

### Recovery Steps
1. Consumer lag detected: >15 minutes behind
2. Monitoring dashboard shows trend: lag increasing
3. Incident commander alerted
4. Immediate action:
   - Increase number of consumer instances (scale out)
   - Monitor lag: should decrease as more instances added
5. If lag not improving:
   - Pause accepting new transactions
   - Complete processing of queued events
   - Resume once lag < 5 minutes
6. End-of-day batch:
   - Wait until consumer catches up (lag = 0)
   - Verify all events processed
   - Run end-of-day batch job
   - Generate daily reports
7. Customer communication: if transactions paused
   - Status page: "High volume, brief pause in transactions"
   - Email: "Resume transaction processing in 30 minutes"
8. Post-incident:
   - Analyze peak volume pattern
   - Increase consumer capacity (add more instances)
   - Optimize processing performance
   - Test batch job under peak load

### Related Systems
- Message queue (Kafka)
- Consumer service
- End-of-day batch job
- Database (for bulk operations)
- Monitoring and alerting
- Incident management system
- Customer communication service

---

## 3. Database Failover During Peak Transaction Volume

### Scenario
The platform runs on AWS RDS Aurora with Multi-AZ setup: primary database in us-east-1a, standby replica in us-east-1b. At 3:00 PM EST (peak transaction time), the primary database becomes unresponsive due to a network partition. RDS automatically failover to the standby in 30 seconds. However, during failover, there's a 30-second window where database is unavailable. Thousands of concurrent transactions timeout.

### Failure Mode
- Primary database becomes unavailable (network partition, instance failure)
- RDS detects unavailability, initiates automatic failover
- Failover duration: 30 seconds (RDS standard)
- During failover: all database connections reset, in-flight transactions fail
- Thousands of concurrent transactions timeout at HTTP layer
- Customer experience: "Database unavailable" error messages

### Impact
- **Customers:** Transaction failures, retry required
- **Business:** Service degradation, customer frustration
- **Operational:** Support volume increase, incident response required

### Detection
- Database connection monitoring: track active connections, failed connections
- Query latency monitoring: alert when p95 latency > 1 second
- Failover detection: RDS sends notification when failover occurs
- Error rate monitoring: alert when error rate > 0.1%
- Customer impact: requests timeout, errors returned

### Mitigation
- **Connection pooling:** Implement connection pool (HikariCP, PgBouncer)
  - Reuse connections instead of creating new for each request
  - Pool handles connection reset during failover
  - Retry logic: auto-reconnect on connection failure
- **Retry logic:** Implement application-level retry
  - On database connection failure: retry up to 3 times with exponential backoff
  - Retry 1: 100ms delay
  - Retry 2: 500ms delay
  - Retry 3: 1 second delay
  - After 3 retries: return error to customer
- **Transaction timeout:** Set reasonable timeout (30 seconds)
  - Shorter timeout detects failures faster
  - Longer timeout allows failover to complete (30 seconds)
  - Balance: 5-10 second timeout, allow 2-3 retries
- **Read replicas:** For read-heavy queries, route to read replica
  - Read replicas survive primary failure
  - Reads can continue even if primary unavailable
  - Writes still need primary (can fail back after failover)
- **Circuit breaker:** Stop trying to write if primary unavailable
  - Track write failures
  - If failure rate >10%, stop writing, return error
  - Prevents overwhelming database during recovery
- **Graceful degradation:** Read-only mode if primary unavailable
  - Serve recent data from cache
  - Allow reads, block writes
  - Resume writes after failover

### Recovery Steps
1. Primary database becomes unavailable
2. RDS detects unavailability, initiates failover
3. Application detects database connection failures
4. Retry logic engages: retries connections with backoff
5. After 30 seconds: RDS failover complete, standby promoted
6. Connection pool reconnects to new primary
7. In-flight transactions: some retry successfully, some fail
8. Customer experience:
   - Some transactions fail (require retry)
   - After 30 seconds: new transactions succeed
   - Most customers experience brief delay, not outage
9. Post-incident:
   - Verify failover completed successfully
   - Database status: new primary healthy, old primary recovered separately
   - Replication status: verify no data loss
   - Customer notification: explain brief outage

### Related Systems
- Relational database (AWS RDS Aurora)
- Connection pooling
- Application retry logic
- Circuit breaker pattern
- Monitoring and alerting
- Incident management system
- Customer communication service

---

## 4. Payment Rail Outage (ACH/Fedwire Down)

### Scenario
The platform supports domestic transfers via ACH (Automated Clearing House) for small transfers and Fedwire for large/urgent transfers. Both are operated by the Federal Reserve. On a Monday morning, the Federal Reserve announces a maintenance window: Fedwire will be unavailable 8:00 AM - 10:00 AM EST. ACH is also affected (slower processing). Customers cannot process urgent transfers during this window. The platform must route transfers appropriately or queue them for later processing.

### Failure Mode
- Federal Reserve maintenance: ACH/Fedwire unavailable
- Customers try to initiate transfers during maintenance window
- Transfer routing service cannot reach ACH/Fedwire
- Transfers fail with error: "Unable to process transfer. Try again later."
- Large-value transfers cannot be processed via Fedwire (only option for urgent)

### Impact
- **Customers:** Cannot process transfers, poor experience
- **Business:** Customer frustration, regulatory compliance (transfer timing)
- **Operational:** May need to process deferred transfers after maintenance

### Detection
- Payment rail health monitoring: ping ACH/Fedwire API before routing
- Outage notification: Federal Reserve publishes maintenance schedule
- Error rate monitoring: detect when >10% of transfers fail
- Customer feedback: support tickets about transfer failures

### Mitigation
- **Maintenance planning:** Subscribe to Federal Reserve outage notifications
  - Plan ahead: communicate to customers about scheduled maintenance
  - Schedule customer communications: "Transfers unavailable 8-10 AM EST"
  - In-app notification: "Fedwire temporarily unavailable, use ACH instead"
- **Transfer routing logic:**
  - Check payment rail availability before routing
  - If Fedwire unavailable: route to ACH instead
  - If ACH also unavailable: queue for later (with estimated completion time)
  - Clear communication: "Transfer will be processed after 10:00 AM EST"
- **Queuing strategy:** For deferred transfers
  - Store transfer request in database with "scheduled" status
  - Async job processes queued transfers once payment rail available
  - Resume processing immediately after maintenance window
  - Prioritize queued transfers (FIFO order)
- **Fallback options:**
  - For urgent large transfers during outage: offer alternative (wire via bank partnership)
  - For non-urgent: queue for next business day
  - Clear customer expectations upfront
- **Communication:** Proactive notification to users
  - Email: "Scheduled maintenance Tuesday 8-10 AM EST"
  - In-app banner: "Transfers temporarily unavailable"
  - Status page: detailed information about outage duration

### Recovery Steps
1. Scheduled maintenance announced by Federal Reserve
2. Customer communication: email/SMS notifying of maintenance window
3. In-app UI: show "Fedwire unavailable, use ACH" during maintenance
4. Transfer requests during maintenance:
   - Block Fedwire transfers
   - Route to ACH or queue for later
   - Inform customer: "Transfer will complete after 10:00 AM EST"
5. Maintenance ends: payment rails resume
6. Queued transfer processing:
   - Async job resumes processing
   - Monitor: ensure queued transfers process quickly
   - Alert if queue has >100 items (indicates slow processing)
7. Post-maintenance:
   - Verify all queued transfers processed
   - Customer notification: maintenance complete, service normal
   - Report: document transfers processed, completion time

### Related Systems
- Payment rail integration (ACH/Fedwire)
- Transfer routing service
- Transfer queue (database/message queue)
- Health check and monitoring
- Customer communication service
- Status page

---

## 5. Regulatory Report Deadline Miss (CTR Filing)

### Scenario
Currency Transaction Report (CTR) must be filed with FinCEN by the 15th of the month following the transaction. A customer deposits $15,000 cash on March 1st. The platform's CTR generation batch job runs on the 10th of April but encounters a bug: CTR is generated but not filed. The batch job exits with error, and no one notices until April 16th (after the 15th deadline). The platform has missed the regulatory deadline for CTR filing.

### Failure Mode
- Customer cash deposit triggers CTR requirement
- CTR batch job on April 10: generates CTR but encounters error filing
- Batch job fails silently (no alert triggered)
- April 15 deadline passes without filing
- April 16: manual review discovers missed filing
- Regulatory violation: FinCEN filing deadline missed

### Impact
- **Regulatory:** Penalty for missed CTR filing (civil, possible criminal)
- **Reputational:** Regulatory non-compliance issue
- **Operational:** Manual filing required, investigation needed

### Detection
- Batch job monitoring: alert on batch job failure
- Completion verification: confirm batch job completed successfully
- Filing status tracking: verify CTR filed with FinCEN
- Deadline monitoring: alert 3 days before deadline if not filed
- Audit: monthly review of filed CTRs

### Mitigation
- **Batch job robustness:**
  - Structured error handling: distinguish recoverable vs. fatal errors
  - Logging: detailed logs of batch job progress
  - Alerting: alert on job failure (not silent failure)
  - Retry logic: retry transient errors (network, timeouts)
- **Filing status tracking:**
  - Confirm CTR filed with FinCEN (check filing status via API)
  - Database record: store filing status (pending, filed, confirmed)
  - Verification: verify each CTR filed before considering complete
- **Deadline management:**
  - Calendar alert: 10 days before deadline
  - Dashboard: show pending CTRs by deadline
  - Alert: 3 days before deadline if not filed
  - Escalation: 1 day before deadline, escalate to senior compliance
- **Batch job testing:**
  - Unit tests: verify CTR generation logic
  - Integration tests: verify end-to-end filing flow
  - Dry run: run batch on non-production data before production run
- **Manual fallback:**
  - If automated filing fails: manual filing as backup
  - Checklist: ensure manual filing completed by deadline
  - Documentation: record reason for manual filing

### Recovery Steps
1. Missed CTR filing discovered on April 16
2. Immediate action:
   - File CTR manually with FinCEN (even though late)
   - Include explanation letter: technical error caused delay
3. Investigation:
   - Root cause analysis: why did batch job fail silently?
   - Review logs: identify where failure occurred
   - Determine if other CTRs missed
4. Remediation:
   - Enhance batch job monitoring (add alerting)
   - Improve error handling and retry logic
   - Add filing status verification
5. Regulatory disclosure:
   - Assess if regulatory notification required
   - Consult legal on penalty exposure
   - Prepare explanation for regulators if required
6. Process improvement:
   - Implement deadline tracking system
   - Add compliance team calendar alerts
   - Require manual verification of filings
   - Test batch job monthly

### Related Systems
- CTR generation service
- Batch job scheduler and monitoring
- FinCEN filing integration
- Compliance case management
- Alert and notification system
- Regulatory reporting platform

---

## 6. Full Region DR Failover Drill

### Scenario
As part of disaster recovery preparedness, the platform conducts a quarterly DR drill: failover the entire system from primary region (us-east-1) to backup region (us-west-2). The drill is scheduled for Sunday at 2:00 AM with customer notification. During the drill, the system failovers to the backup region, but DNS propagation is slow. Some customers connect to the old region (now offline) and experience errors. The drill takes 4 hours instead of planned 1 hour.

### Failure Mode
- DR drill begins: failover primary → backup region
- DNS failover to backup region initiated
- DNS propagation delay: takes 2 hours (expected <30 minutes)
- Some customers still connecting to primary region
- Primary region is offline, customers experience errors
- Drill extended: troubleshooting DNS propagation issue

### Impact
- **Customers:** Service interruption during drill (planned, but longer than expected)
- **Operational:** DR drill longer than planned, impacts team, reveals DNS weaknesses
- **Learning:** Identify DNS propagation as bottleneck for future failovers

### Detection
- DNS propagation monitoring: track DNS query resolution
- Regional health check: verify both regions healthy
- Customer routing: track which region customers connecting to
- Drill monitoring: real-time dashboard of failover progress

### Mitigation
- **Faster DNS failover:**
  - Use health-check based routing (Route53 in AWS)
  - Health check: ping endpoint in each region every 10 seconds
  - TTL: set low (30 seconds) for critical DNS records
  - Automatic failover: if primary region fails health check, switch to backup
- **Multi-region setup:**
  - Both regions active-active (not active-passive)
  - Customers in us-east route to us-east, customers in us-west route to us-west
  - On regional failure: traffic gradually shifts to healthy region
  - Eliminates failover bottleneck
- **Database replication:**
  - Active-active replication: both regions can write
  - Conflict resolution: application handles concurrent writes to same record
  - Or: active-passive with fast promotion (write to backup when primary fails)
- **DR drill checklist:**
  - Pre-drill: notify customers, set expectations
  - Drill phases:
    1. Health check: verify both regions healthy
    2. DNS failover: initiate failover
    3. Monitor: track health, error rates
    4. Validation: verify data consistency
    5. Failback: switch back to primary
  - Post-drill: document lessons learned
- **Incident command:**
  - Assign drill lead to manage and monitor
  - Communication: update team regularly on progress
  - Decision point: if drill takes >2 hours, escalate to decision
  - Continue or abort: decide whether to continue or abort drill

### Recovery / Execution Steps
1. DR drill scheduled for Sunday 2:00 AM EST
2. Customer notification: email sent 1 week before
3. Drill preparation:
   - Backup databases verified
   - Both regions verified healthy
   - DNS failover config verified
4. Drill begins: failover initiated
5. Phase 1 (Health check): confirm both regions operational
6. Phase 2 (DNS failover): update DNS to point to us-west-2
7. Monitoring:
   - Track DNS propagation: query resolution time
   - Monitor error rates in both regions
   - Customer connectivity: which region customers connecting to
8. Issue detected: DNS propagation slow (2 hours)
9. Troubleshooting:
   - Check TTL: if TTL too high, clients cache old DNS
   - Update TTL on critical records to 30 seconds
   - Monitor propagation: should improve
10. Validation:
    - All customers now connecting to us-west-2
    - Error rates: normal in backup region
    - Data consistency: verify no data loss
11. Drill completion:
    - Decision: failover successful despite DNS delays
    - Failback: switch DNS back to us-east-1
    - Verify primary region recovered
12. Post-drill:
    - Document lessons learned: DNS propagation too slow
    - Action items: reduce TTL on critical records
    - Next drill: test DNS failover specifically
    - Team training: review incident

### Related Systems
- Cloud infrastructure (multi-region deployment)
- DNS service (Route53)
- Database replication
- Monitoring and alerting
- Incident management system
- Customer communication service
- Status page

---

## 7. HSM Certificate Rotation for Card Crypto

### Scenario
The platform uses a Hardware Security Module (HSM) to encrypt and decrypt cardholder data (card tokens, PIN blocks). HSM certificates are valid for 1 year and must be rotated before expiration. The platform has scheduled certificate rotation maintenance window (midnight Sunday). During rotation, HSM will be temporarily unavailable (5-10 minutes). Any payment operations requiring HSM will fail during this window.

### Failure Mode
- HSM certificate rotation scheduled for Sunday midnight
- Maintenance window: 5-10 minutes
- During window: HSM unavailable, card operations blocked
- Customers attempting to pay during window: error "Payment temporarily unavailable"
- Customer experience: brief service disruption

### Impact
- **Customers:** Brief payment unavailability (expected and communicated)
- **Business:** Brief revenue impact (low at midnight)
- **Operational:** Planned maintenance, manageable if communicated

### Detection
- HSM health monitoring: track HSM status
- Certificate expiration tracking: alert 30 days before expiration
- Maintenance scheduling: calendar alert for rotation dates
- Payment success rate: monitor during rotation window

### Mitigation
- **Scheduling:** Schedule maintenance during low-traffic period
  - Midnight or early morning (low payment volume)
  - Avoid business hours
  - Avoid end-of-month/quarter (higher volume)
- **Process documentation:**
  - Detailed runbook for certificate rotation
  - Step-by-step procedures
  - Rollback steps if rotation fails
  - Team training: ensure operators know process
- **Redundancy:** If possible, dual HSM setup
  - Primary HSM: rotate while secondary online
  - Secondary HSM: continue handling traffic during rotation
  - Zero downtime: switch traffic to secondary during primary rotation
- **Customer communication:**
  - Email: 1 week before: "Scheduled maintenance Sunday 12:30-12:40 AM EST"
  - In-app notification: "Brief payment interruption expected"
  - Status page: real-time update of maintenance progress
- **Monitoring during rotation:**
  - Team on-call: monitors HSM during rotation
  - Alert on failure: if rotation takes >15 minutes, escalate
  - Verification: after rotation, verify certificate valid, HSM healthy
- **Testing:** Before production rotation
  - Test rotation on staging HSM
  - Verify all payment operations work post-rotation
  - Document any issues

### Recovery / Execution Steps
1. HSM certificate rotation scheduled
2. Pre-rotation checklist (1 week before):
   - Verify certificate expiration date
   - Backup current HSM configuration
   - Test rotation on staging HSM
   - Coordinate with security team
3. Customer notification:
   - Email sent: describe maintenance window and impact
   - Status page: mark "Scheduled Maintenance"
   - In-app banner: "Brief payment interruption expected"
4. Rotation day:
   - Team assembled 15 minutes before maintenance window
   - Incident command: lead coordinates rotation
   - Pre-rotation: verify HSM health, backup configuration
5. Certificate rotation:
   - Step 1: Connect to HSM
   - Step 2: Generate new certificate signing request
   - Step 3: Install new certificate
   - Step 4: Verify new certificate installed
   - Step 5: HSM health check
6. Monitoring:
   - During rotation: monitor payment error rates
   - Post-rotation: verify payment operations succeed
   - HSM status: confirm healthy and responsive
7. Verification:
   - Certificate validity: confirm new certificate valid for 1 year
   - Operations test: process test card transactions
   - Data integrity: verify card data still encrypted/decrypted correctly
8. Notification:
   - Customer notification: maintenance complete, service normal
   - Status page: update to "All Systems Operational"
9. Post-rotation:
   - Document rotation: certificate dates, changes made
   - Team debrief: discuss any issues or improvements
   - Schedule next rotation (1 year from now)

### Related Systems
- Hardware Security Module (HSM)
- Card encryption service
- Payment processing
- Certificate management
- Monitoring and alerting
- Incident management system
- Customer communication service

---

## Summary

These operational edge cases represent real challenges in managing a production banking platform. Key principles for handling these scenarios:

1. **Monitoring:** Track system health, alert on issues
2. **Automation:** Automate failover, retries, recovery steps
3. **Planning:** Schedule maintenance during low-traffic periods, have detailed runbooks
4. **Communication:** Keep customers informed of maintenance and issues
5. **Testing:** Regularly test failover, disaster recovery, and maintenance procedures
6. **Documentation:** Maintain detailed runbooks and post-incident documentation
7. **Continuous Improvement:** Learn from incidents and improve processes

Operational excellence requires constant vigilance, proactive planning, and team training.
