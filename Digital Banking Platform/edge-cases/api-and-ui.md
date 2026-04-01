# API and UI Edge Cases

This document outlines critical edge cases in API functionality and user interface interactions for the Digital Banking Platform. Each scenario covers failure modes, detection mechanisms, mitigation strategies, and recovery procedures.

---

## 1. Open Banking (PSD2) TPP Unauthorized Access

### Scenario
A Third-Party Provider (TPP) for open banking (e.g., a fintech app that aggregates accounts) receives authorization from a customer to access their account data via PSD2 API (OAuth 2.0 + FAPI profile). However, the TPP's client secret is compromised. A bad actor uses the compromised credentials to access customer accounts without authorization. The incident is discovered 48 hours later during audit.

### Failure Mode
- TPP client secret is compromised (exposed in GitHub, intercepted, etc.)
- Bad actor uses TPP credentials to make API calls on behalf of legitimate TPP
- API access logs show requests from legitimate TPP, but from unauthorized user
- Customer account data accessed by bad actor without customer authorization
- Incident discovered during security audit or customer complaint

### Impact
- **Customers:** Unauthorized account access, potential fraud
- **Regulatory:** PSD2 violation (customer authentication and authorization)
- **Reputational:** Data breach notification required

### Detection
- API rate limiting: monitor unusual request patterns (high volume, new IP)
- IP geolocation check: flag if TPP API calls from geographic location inconsistent with TPP
- Device fingerprinting: track authorized devices per TPP, flag new devices
- Anomaly detection: ML model detects unusual query patterns (sudden bulk export of data)
- Customer notification: proactive: "A third-party accessed your account. Do you authorize this?"
- Security audit: regular review of TPP API access logs

### Mitigation
- **OAuth 2.0 security:** Enforce PKCE (Proof Key for Code Exchange) for authorization code grant
- **FAPI profile:** Implement FAPI part 1 & 2 requirements (sender-constrained tokens, TLS binding)
- **Rate limiting:** Implement per-TPP and per-customer rate limits (100 req/min per TPP)
- **Scope limitation:** Restrict TPP to minimum required scopes (e.g., read-only accounts, no transfers)
- **Token expiration:** Short-lived access tokens (15 min) with refresh tokens (90 days)
- **IP whitelisting:** Require TPP to declare IP addresses for API calls; flag requests from other IPs
- **Mutual TLS:** Require client certificate authentication in addition to OAuth credentials
- **Audit logging:** Log all API access with user, TPP, timestamp, and query details

### Recovery Steps
1. Unauthorized API access detected via anomaly detection or customer complaint
2. Immediate action: Revoke all active tokens for compromised TPP
3. Access log analysis: Identify all accounts accessed and all data exposed
4. Incident investigation: Determine scope of compromise and root cause
5. Customer notification: Inform affected customers within 24 hours (regulatory requirement)
6. TPP notification: Contact TPP to inform of compromise, request client secret rotation
7. Law enforcement: File report if personal data was accessed maliciously
8. Process improvement: Require TPP to implement certificate pinning and secret rotation

### Related Systems
- OAuth 2.0 authorization server
- Open Banking API gateway
- API access logging system
- Anomaly detection engine
- Customer communication service
- Incident management system

---

## 2. Mobile App Session Expiry During Payment

### Scenario
A customer is in the middle of completing a payment using the mobile app (has filled in beneficiary details, amount, and is in the confirmation screen). The session timeout is set to 30 minutes of inactivity. The customer steps away to verify some information, resulting in session expiration. When the customer returns 5 minutes later, the session has expired. The app returns them to the login screen, losing all entered payment data.

### Failure Mode
- Customer initiates payment (fills in form)
- Customer steps away, session expires due to 30-minute inactivity
- Session middleware logs customer out, redirects to login screen
- Customer returns to app, must re-authenticate
- All entered payment data is lost
- Customer must re-enter payment details from scratch
- Potential frustration and payment abandonment

### Impact
- **Customer:** Poor experience, payment incomplete, data loss
- **Business:** Reduced conversion rate, potential revenue impact
- **Operational:** Customer support inquiries about lost data

### Detection
- Analytics: track session timeout events and correlation with payment abandonment
- User feedback: support tickets about lost payment data
- Cohort analysis: identify customers who abandon payments after session timeout
- A/B testing: measure impact of different session timeout values

### Mitigation
- **Session persistence:** Store entered payment details in secure local storage (encrypted on device)
- **Increased timeout:** Extend session timeout to 2 hours for logged-in customers
- **Idle warning:** Show warning dialog 5 minutes before timeout: "Your session will expire soon. Click to stay logged in"
- **Touch extension:** Extend session on any user interaction (scroll, form input)
- **Form recovery:** If session expires, attempt to restore form data on next login
- **Save & resume:** Implement "Save Payment Draft" feature, allow customer to resume pending payment
- **Contextual timeout:** Increase timeout during payment workflow (2-hour timeout during payment, 30-min in other areas)

### Recovery Steps
1. Session expires during payment
2. App redirects to login screen
3. On re-login, app checks for pending payment draft
4. If draft exists, display: "You have a pending payment. Resume or discard?"
5. If customer chooses resume: pre-populate payment form with saved data
6. Customer reviews and confirms payment
7. Payment proceeds without re-entering data

### Related Systems
- Session management middleware
- Mobile app local storage
- Authentication service
- Payment processing service
- Customer communication service

---

## 3. Rate Limit Breach by Legitimate Business Customer

### Scenario
A business customer uses the API to manage multiple accounts (e.g., expense management automation). The integration is configured to fetch account balances for 50 accounts every minute. This legitimate use case results in 50 API calls per minute, which exceeds the platform's default rate limit of 10 req/s (600 req/min). The customer's API requests are throttled with HTTP 429 (Too Many Requests) responses, breaking their integration.

### Failure Mode
- Business customer configured legitimate high-volume API usage (50 accounts, 1-min refresh)
- Integration runs successfully for 24 hours (no rate limit exceeded)
- Later, platform implements rate limiting (10 req/s default) without grandfathering existing customers
- Customer's API calls now receive HTTP 429 responses
- Integration fails, customer's automation breaks
- Customer support receives complaints from business partner

### Impact
- **Customers:** Integration breaks, business operations impacted
- **Business:** Upset customer, support cost, potential churn
- **Operational:** Need to manually adjust rate limits for affected customers

### Detection
- Rate limit monitoring: track which customers are hitting rate limits
- Integration health: monitor API integration success rate per customer
- Alert on threshold: flag when customer hits rate limit repeatedly
- Usage analytics: segment customers by API call volume patterns
- Customer feedback: monitor for complaints about HTTP 429 errors

### Mitigation
- **Tiered rate limits:** Implement customer-tier based limits:
  - Freemium: 10 req/s per user
  - Paid: 100 req/s per user
  - Enterprise: unlimited (or 1000 req/s) with SLA
- **Gradual rollout:** Implement rate limiting gradually (monitor, warn, then enforce)
- **Customer communication:** Notify customers 30 days before rate limiting enforcement
- **Quota increase:** Allow customers to request rate limit increase with justification
- **API optimization:** Provide batch endpoints to reduce API calls (e.g., fetch 50 account balances in 1 request)
- **Caching:** Cache frequently accessed data on client side (reduce API calls)
- **Exemptions:** Whitelist critical integrations (payroll, expense management) for higher limits

### Recovery Steps
1. Business customer's integration fails due to rate limiting
2. Customer contacts support with error logs showing HTTP 429
3. Support investigates: identifies legitimate high-volume usage
4. Decision: Customer tier upgraded or rate limit exemption granted
5. Solution: Customer's rate limit increased to 100 req/s or integration switched to batch API
6. Customer notified of increase and integration restored
7. Process improvement: Add pre-integration assessment to identify high-volume use cases

### Related Systems
- API gateway with rate limiting
- Rate limit configuration service
- API usage analytics
- Customer support system
- API documentation and guidance

---

## 4. Webhook Delivery Failure for Transaction Events

### Scenario
The platform sends webhook notifications to third-party integrations (e.g., accounting software) when transactions complete. A customer's accounting integration registered a webhook endpoint. However, the endpoint is temporarily unavailable (server maintenance, network issue). The platform's webhook system attempts delivery 3 times over 1 hour, then gives up. The transaction completion event is lost, and the customer's accounting record is never updated.

### Failure Mode
- Transaction completed: platform publishes "transaction.completed" event
- Webhook endpoint receives delivery attempt (HTTP POST)
- Endpoint returns 500 error (server down)
- Platform retries with exponential backoff (3 retries over 1 hour)
- All retries fail, webhook delivery abandoned
- Customer's accounting system never learns about transaction
- Accounting reconciliation fails, customer must manually investigate

### Impact
- **Customers:** Accounting integration broken, manual reconciliation required
- **Business:** Reduced value of API integration, customer frustration
- **Operational:** Customer support investigates missing transaction

### Detection
- Webhook delivery monitoring: track success/failure rate per endpoint
- Alert on failure: trigger alert when >5% of webhooks to an endpoint fail
- Customer notification: proactive: "Webhook delivery failed. Your integration may be out of sync"
- Retry queue monitoring: track pending retries in queue
- Reconciliation: periodic check of delivered vs. undelivered events

### Mitigation
- **Robust retry logic:** Implement exponential backoff with longer retry window:
  - Retry 1: 1 minute delay
  - Retry 2: 5 minutes delay
  - Retry 3: 1 hour delay
  - Retry 4: 24 hours delay
  - Retry 5: 7 days delay
- **Webhook event storage:** Store all events in database (never discard)
- **Replay capability:** Provide webhook replay API: "Re-send events from time T1 to T2"
- **Acknowledgment:** Require webhook endpoint to return 2xx status within 30 seconds
- **Circuit breaker:** Stop sending webhooks to endpoint that fails >100 times in 24 hours
- **Dead letter queue:** Move failed webhooks to DLQ for manual investigation
- **Customer control:** Allow customer to retry failed webhooks in dashboard

### Recovery Steps
1. Webhook delivery fails due to endpoint unavailability
2. Retries continue over extended window (7 days)
3. Customer realizes transactions are missing from accounting system
4. Customer accesses dashboard: sees "Failed webhook deliveries"
5. Options available:
   - **Self-service:** Click "Retry" to re-attempt delivery
   - **Support:** Contact support, provide time range, request event replay
6. Support can trigger replay: system re-sends all events from specified time period
7. Customer verifies integration is back in sync
8. Endpoint monitoring enabled: alerts on future failures

### Related Systems
- Event streaming platform (Kafka)
- Webhook delivery service (with retry logic)
- Webhook management API
- Event storage (database)
- Customer dashboard
- Analytics and monitoring system

---

## 5. Bank Statement PDF Generation Timeout

### Scenario
A customer requests a monthly bank statement in PDF format. The PDF generation service queries transaction history (100 transactions, 30 pages), adds bank logo and formatting, and generates the PDF. However, the customer has thousands of transactions this month. The PDF generation service takes >30 seconds to render, timing out the HTTP request. The customer receives a 504 Gateway Timeout error and cannot download the statement.

### Failure Mode
- Customer requests bank statement PDF
- PDF generation service queries transaction history
- PDF rendering takes >30 seconds (exceeds HTTP timeout)
- HTTP request times out, returns 504 Gateway Timeout
- Customer receives error: "Unable to generate statement. Please try again later"
- Customer cannot access statement

### Impact
- **Customers:** Cannot access statement, poor experience
- **Business:** Customer frustration, support inquiries
- **Operational:** Potential regulatory issue if customer cannot access required documents

### Detection
- Request timeout monitoring: track requests that exceed timeout threshold
- PDF generation performance: monitor rendering time per statement
- Alert on slow generation: flag when >10% of statements take >20 seconds
- Customer support tickets: complaints about PDF generation failures
- Analytics: segment statements by size/complexity, identify slow ones

### Mitigation
- **Async processing:** Move PDF generation to background job:
  - Customer clicks "Generate Statement"
  - Returns immediately: "Statement generating, we'll email when ready"
  - Background job generates PDF asynchronously
  - Email sent with PDF attached when ready
- **Timeout increase:** Increase HTTP timeout from 30s to 60s (if viable)
- **Pagination:** Limit statement to recent N transactions (30-day window instead of full year)
- **Caching:** Cache monthly statements after first generation (immutable)
- **Performance optimization:** Use streaming PDF generation instead of full buffering
- **Fallback:** If generation takes >20 seconds, automatically switch to async processing

### Recovery Steps
1. Customer requests bank statement PDF
2. Request triggers async PDF generation job
3. Job status returned: "Statement generating. Download link will be sent to your email."
4. Customer receives email within 5 minutes with PDF attachment
5. If generation fails: customer notified via email, can retry or contact support
6. Post-incident: identify which customers generated slow statements, optimize if needed

### Related Systems
- Statement generation service
- Background job queue (Kafka/SQS)
- PDF rendering library (iText, ReportLab)
- Email delivery service
- Customer communication service
- S3 or file storage

---

## 6. Biometric Authentication Failure on New Device

### Scenario
A customer enables biometric authentication (fingerprint or face recognition) on their primary mobile device. Later, they access the app on a new device (same phone model, same OS version). Biometric authentication fails or is not available on the new device. The customer cannot log in and must fall back to password authentication, but cannot remember their password.

### Failure Mode
- Customer enrolls biometric on Device A (fingerprint registered with device)
- Customer installs app on Device B (new device, same phone model)
- Biometric authentication unavailable or fails on Device B (different fingerprint data)
- Customer cannot remember password (was relying on biometric)
- Customer locked out of account, cannot complete login
- Support escalation required for account recovery

### Impact
- **Customers:** Locked out of account, poor experience
- **Business:** Support cost, customer frustration
- **Operational:** Account recovery process requires identity verification

### Detection
- Biometric authentication failure monitoring: track failed biometric attempts
- Alert on repeat failures: flag when user has >3 failed biometric attempts in 10 minutes
- Customer feedback: support tickets about locked accounts on new device
- Device registration tracking: monitor new device registrations per customer

### Mitigation
- **Fallback authentication:** Always provide password or SMS OTP backup even if biometric available
- **Clear UX:** Explain biometric is device-specific, won't work on other devices
- **Device linking:** Allow customer to link multiple devices and manage them in settings
- **Password recovery:** Ensure password recovery flow is simple (email reset link)
- **Biometric re-enrollment:** Guide customer to re-enroll biometric on new device
- **Trusted device:** Remember device for 30 days after successful password login (reduce re-authentication)

### Recovery Steps
1. Customer attempts biometric login on new device, fails
2. App displays: "Biometric not available on this device. Use password or SMS code."
3. Customer chooses SMS code option (or password reset)
4. SMS sent to registered phone number with one-time code
5. Customer enters OTP, gains access to account
6. In account settings, customer can re-enroll biometric on new device
7. Or customer sets up password recovery to prevent future lockouts

### Related Systems
- Biometric authentication service
- Device management and registration service
- Password authentication service
- SMS delivery service
- Account recovery service

---

## Summary

These API and UI edge cases highlight the need for robust error handling, graceful degradation, and clear communication with both customers and external integrations. Key principles for handling these scenarios:

1. **Always Provide Fallback:** Never block critical functionality due to single failure point
2. **Async Processing:** Use background jobs for long-running operations
3. **Customer Communication:** Proactively inform customers about status changes
4. **Monitoring:** Track metrics that matter (timeouts, failures, user impact)
5. **Graceful Degradation:** Reduce functionality rather than blocking entirely
6. **Testing:** Test edge cases (high volume, slow endpoints, network failures)

These edge cases require coordination between backend, frontend, and operations teams to ensure resilient APIs and responsive user interfaces.
