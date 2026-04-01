# Security and Compliance Edge Cases - Event Ticketing Platform

This document outlines critical edge cases in security, compliance, and fraud prevention for the Event Ticketing Platform.

---

## Bot and Scalper Protection

### Scenario
A high-demand event (e.g., Taylor Swift concert) goes on sale. Within seconds, bots (automated scripts) purchase thousands of tickets. Real customers trying to buy tickets encounter: "Sold Out" message. The bots then resell tickets on secondary markets at 10x markup. Real fans are unable to purchase at face value.

### Failure Mode
- Event on-sale begins
- Bots: automated requests to create holds and complete purchases
- Bots purchase 80% of inventory within 5 minutes
- Real customers: see "sold out" message
- Secondary market: tickets selling at premium prices
- Legitimacy question: are these real bots or just high demand?

### Impact
- **Customers:** Cannot buy tickets at face value
- **Organizers:** Lose ability to control pricing, audience demographics
- **Business:** Reputation damage, regulatory pressure
- **Regulatory:** Lawmaker pressure (BOTS Act, Stop Scalping Act)

### Detection
- Monitor purchase patterns:
  - High velocity from single IP (100+ orders in 1 minute)
  - High velocity from single device (same device fingerprint)
  - Patterns: rapid holds followed by rapid conversions
  - Geographic anomalies: purchases from VPN/proxy IPs
- Behavioral signals:
  - No browsing before purchase (bot goes straight to checkout)
  - Mouse movement patterns (bots don't move mouse like humans)
  - Form fill speed (bots fill forms instantly, humans take time)

### Mitigation
- **Rate Limiting:** Strict per-user limits
  - Hold creation: 5 holds per minute per user
  - Orders: 1 order per minute per user
- **CAPTCHA:** Require human verification
  - reCAPTCHA v3 (invisible)
  - Triggered during high-demand events or unusual patterns
  - Challenge-response: require user action (click, type)
- **Device Fingerprinting:** Track device characteristics
  - Browser user agent, screen resolution, canvas fingerprint
  - Flag suspicious devices (no mouse movement, strange characteristics)
  - Require additional verification
- **Queue System:** Fair access during high demand
  - Virtual waiting room during peak demand
  - Serve customers FIFO
  - Prevents rapid-fire bot purchases
- **IP Whitelisting:** For trusted partners
  - Allow authorized resellers/aggregators
  - Require API key authentication
  - Rate limits still apply
- **Behavioral Verification:** Monitor for bot patterns
  - ML model detects bot-like purchase patterns
  - Flag suspicious purchases for manual review
- **Secondary Market Restrictions:** Limit resale
  - Require ticket buyer name match attendee
  - Restrict resale on secondary markets
  - Ticket transfer only to authenticated users

### Recovery Steps
1. Bot activity detected during on-sale
2. Immediate actions:
   - Activate CAPTCHA challenge for subsequent orders
   - Activate queue system for fair access
   - Alert ops team
3. Investigation:
   - Analyze purchase patterns
   - Identify bot IP ranges, device fingerprints
   - Block known bot IPs
4. Reverse bot purchases:
   - Identify orders that are clearly bot-driven
   - Cancel orders, refund customers
   - Require bot operators to accept refunds
5. Communication:
   - Transparency to customers: "Implementing anti-bot measures"
   - Guidance: "CAPTCHA required during peak demand"
6. Long-term:
   - Implement stronger bot detection
   - Partner with anti-bot services
   - Monitor secondary market prices

### Related Systems
- Rate limiting (API Gateway)
- CAPTCHA service (reCAPTCHA)
- Device fingerprinting
- Fraud detection system
- Queue management
- Monitoring and alerting

---

## PCI-DSS Compliance for Card Payments

### Scenario
The platform processes payment card information (PAN, CVV, expiration date). To be PCI-DSS compliant, the platform must follow strict requirements: encryption, access controls, and audit trails. Failure to comply results in fines ($100K-$300K), loss of payment processing ability, and reputational damage.

### Failure Mode
- Platform stores raw card data (non-compliance)
- Or: insufficient encryption
- Or: inadequate access controls
- Or: no audit trail of card data access
- PCI audit discovers violations
- Fines and forced remediation

### Mitigation
- **PCI-Compliant Architecture:**
  - Never handle raw card data (use Stripe, not direct API)
  - Use Stripe Payment Intents: card data entered in Stripe-hosted form
  - Platform receives token instead of card data
  - This reduces scope to SAQ-A-EP (minimal compliance)
- **Encryption:** All card data encrypted at rest and in transit
  - TLS 1.2+ for data in transit
  - AES-256 for data at rest
  - Key rotation every 90 days
- **Access Controls:** Restrict card data access
  - Only payment service has access
  - Principle of least privilege
  - No developer direct access to production card data
- **Audit Trail:** Log all access to card data
  - Who accessed, when, what was accessed
  - Retention: 1 year
  - Protection: logs stored separately, not modifiable

### Recovery Steps
1. PCI audit scheduled
2. Pre-audit preparation:
   - Document architecture (Stripe Payment Intents)
   - Document encryption (TLS, AES-256)
   - Document access controls (IAM policies)
   - Gather audit logs
3. Audit process:
   - Review documented controls
   - Verify encryption
   - Validate access controls
   - Check audit logs
4. If violations found:
   - Remediate immediately
   - Re-test compliance
   - Document remediation
5. Certification:
   - Obtain PCI compliance certification
   - SAQ-A-EP attestation
   - Annual re-certification

### Related Systems
- Payment processing (Stripe)
- Encryption and key management
- Access control (IAM)
- Audit logging

---

## Ticket Fraud (Counterfeit QR Codes, Duplicate Claims)

### Scenario
A customer screenshot their ticket QR code and shares it on social media. Multiple people download the image and attempt to check-in with the same QR code at the event. The check-in system validates the QR code multiple times and marks attendance for all "duplicate" entries, creating fake attendance records.

### Failure Mode
- Customer shares screenshot of QR code
- Multiple people download and use same QR
- Check-in system validates same QR code multiple times
- Multiple attendance records created for single ticket
- Venue overcrowded with fraudulent attendees

### Impact
- **Venue:** Overcapacity, safety issue
- **Organizer:** Revenue loss (refunds for duplicate entrants)
- **Reputation:** Negative experience for real attendees

### Detection
- Duplicate check-in attempts detected
  - Same QR code checked-in multiple times
  - Multiple different device IDs for same ticket
  - Time-of-check anomalies (checked in at different gates simultaneously)
- Analytics: attendance > expected capacity

### Mitigation
- **One-Time Use QR Code:** QR code can only be scanned once
  - After first check-in, QR code marked as "used"
  - Subsequent scan-attempts rejected
  - Database tracks check-in status
- **Dynamic QR Codes:** QR code changes frequently
  - QR code regenerated every 10 seconds
  - Old QR code becomes invalid
  - Requires active ticket holder to access current QR
  - Prevents screenshot reuse
- **Biometric Verification:** Require ID scan + QR scan
  - Customer ID matched to ticket holder name
  - Prevents ticket sharing
  - Privacy consideration: opt-in for events
- **Device Binding:** Ticket tied to specific device
  - Ticket accessible only from device that purchased
  - Attempted access from other device blocked
  - Prevents transfer/sharing
- **Duplicate Detection:** Monitor for suspicious patterns
  - Alert on same QR code scanned multiple times
  - Alert on same ticket holder multiple check-ins
  - Investigate before marking as attended

### Recovery Steps
1. Duplicate check-in attempt detected
2. Immediate action:
   - Block subsequent check-ins for that QR code
   - Alert venue staff
3. Investigation:
   - Review check-in timestamps and locations
   - Identify legitimate attendee (first check-in)
   - Identify fraudulent attempts
4. Resolution:
   - Mark legitimate check-in as valid
   - Block fraudulent attendees at gate
   - Ask for photo ID verification
5. Prevention:
   - Implement one-time QR codes
   - Or: implement dynamic QR codes
   - Or: require ID verification at check-in

### Related Systems
- Ticket Service (QR generation)
- Check-In Service (validation)
- Identity verification (if required)
- Monitoring and alerting

---

## GDPR Attendee Data Rights

### Scenario
An attendee requests their data under GDPR Article 15 (right of access). They want to know what personal data is stored. The platform must provide a complete export within 30 days. Additionally, the attendee requests deletion (Article 17). The platform must balance privacy rights with regulatory requirements to retain transaction data for 7 years (AML/tax).

### Failure Mode
- Attendee requests data export (GDPR Article 15)
- Platform has 30 days to respond
- System cannot easily export all personal data
- Attendee requests deletion (Article 17)
- Conflict: GDPR deletion vs. AML 7-year retention requirement
- Regulatory violation if either requirement missed

### Impact
- **Regulatory:** GDPR fines ($10-20M or 2-4% revenue)
- **Customer:** Data rights not respected
- **Compliance:** Conflicting obligations

### Mitigation
- **Data Inventory:** Know all personal data collected
  - Name, email, phone, address, payment method
  - Attendance history, preferences, interactions
  - Document: what data, why collected, retention period
- **Data Export:** Implement automated export
  - Query all customer data
  - Format as CSV or JSON
  - Include clear explanations of each data field
  - Return within 30 days
- **Deletion vs. Retention:** Implement tiered approach
  - Customer identifiers: delete on request (no longer needed)
  - Transaction data: anonymize on request
    - Replace name with hash
    - Retain amount, date for financial records
    - Purpose limitation: use only for compliance
  - Compliance data: retain per regulation (AML 7 years)
    - Cannot be deleted, but limited access
    - Not used for marketing or service improvement
- **Audit Trail:** Document all requests and actions
  - Track deletion requests
  - Document what was deleted, what was retained and why
  - Maintain for audit

### Recovery Steps
1. GDPR rights request received
2. Classification: what type of request?
   - Access (Article 15): provide data export
   - Deletion (Article 17): evaluate if applicable
   - Portability (Article 20): export in standard format
3. For access request:
   - Query all customer data
   - Format as export (CSV/JSON)
   - Include data dictionary explaining each field
   - Send to customer within 30 days
4. For deletion request:
   - Determine applicable data:
     - Personal data: delete immediately
     - Transaction data: anonymize (no PII)
     - Compliance data: check if retention required
   - Execute deletion/anonymization
   - Document action and retention rationale
5. Verification:
   - Confirm customer data deleted/anonymized
   - Verify across all systems (database, backups, logs)
6. Documentation:
   - Log request and action taken
   - Retain audit trail (6 years for regulatory compliance)

### Related Systems
- Customer database
- Transaction data storage
- Data anonymization service
- GDPR compliance tracking
- Audit logging

---

## Account Takeover Protection

### Scenario
An attacker gains access to a customer's account (via phishing, credential stuffing, or social engineering). The attacker views the customer's orders, transfers tickets, or modifies payment methods. The legitimate customer doesn't notice until they try to access their account and find it compromised.

### Failure Mode
- Attacker accesses customer account
- Actions: view orders, transfer tickets, modify payment method
- Legitimate customer unaware until discovering unauthorized changes
- Financial loss or inconvenience

### Impact
- **Customers:** Account compromise, potential fraud
- **Business:** Reputation damage, customer churn
- **Regulatory:** Potential data breach notification requirement

### Detection
- Login anomaly: login from new device/location
- Action anomaly: unusual behavior (new beneficiary, large transfer)
- Customer report: "Account compromised"
- Failed login attempts: multiple failures from same IP

### Mitigation
- **MFA (Multi-Factor Authentication):** Require second factor
  - SMS OTP, authenticator app, hardware key
  - Prevents account access even with correct password
- **Suspicious Login Detection:** Alert on unusual patterns
  - Login from new device: require verification
  - Login from new location: require verification
  - Login at unusual time: alert customer
- **Session Management:**
  - Idle timeout: 30 minutes
  - Concurrent login limit: only 1 active session
  - Kill old sessions when login from new device
- **Credential Strength:** Enforce strong passwords
  - Minimum length: 12 characters
  - Require mix of characters (uppercase, lowercase, numbers, symbols)
  - Check against known compromised passwords (Have I Been Pwned)
- **Email Verification:** Verify email changes
  - Email change request: send verification to old email
  - Require confirmation before email change takes effect
  - Delays account takeover via email change

### Recovery Steps
1. Account compromise detected (by customer or system)
2. Immediate action:
   - Lock account (prevent further unauthorized access)
   - Invalidate all sessions
   - Notify customer
3. Investigation:
   - Review recent account activity
   - Identify unauthorized actions
   - Determine attack vector
4. Remediation:
   - Customer password reset
   - Enable MFA
   - Review and confirm payment methods
   - Verify pending/recent orders
5. Reversal:
   - Reverse unauthorized ticket transfers
   - Reverse unauthorized payment method changes
   - Refund fraudulent orders if applicable
6. Customer support:
   - Detailed explanation of what happened
   - Steps to prevent future compromise
   - Offer credit if customer lost money

### Related Systems
- Authentication service
- MFA service
- Login monitoring
- Account management
- Audit logging

---

## Insider Threat (Employee Creating Fake Orders)

### Scenario
A platform employee with database access creates fake orders in the system, allocating free tickets to themselves or selling them. The orders appear legitimate (valid customer, valid event, marked as paid) but were created without actual payment. The fraud is discovered during monthly reconciliation when payment total doesn't match order total.

### Failure Mode
- Employee creates fake order records in database
- Order appears paid but no actual Stripe charge
- Monthly reconciliation: Payment total ≠ Order total
- Fraud detected

### Impact
- **Financial:** Platform loss (refunds or write-offs)
- **Trust:** Employee breach of trust
- **Operational:** Investigation, remediation

### Detection
- Reconciliation: payment amount vs. order amount mismatch
- Audit logs: suspicious database modifications
- Employee pattern analysis: unusual orders traced to same employee

### Mitigation
- **Access Control:** Principle of least privilege
  - Employees access only required data
  - Database access logs: track all modifications
  - Payment data: no direct access to sensitive fields
- **Separation of Duties:**
  - Order creation and payment processing by different systems/people
  - Reconciliation by third party (not same person who created orders)
- **Audit Trails:** Log all data modifications
  - Who modified, what was modified, when, why
  - Logs stored separately, protected from modification
  - Regular audit of logs for suspicious activity
- **Background Checks:** Screen employees before hiring
  - Verify employment history
  - Criminal background check
  - Reference checks
- **Monitoring:**
  - Alert on database modifications to sensitive tables
  - Monitor payment vs. order mismatches
  - Monthly reconciliation with automated checks

### Recovery Steps
1. Fraud detected during reconciliation
2. Investigation:
   - Identify discrepancy amount
   - Identify orders not backed by payments
   - Trace orders to creator (database logs)
3. Determination:
   - Is this deliberate fraud or honest mistake?
   - Document evidence
4. Action:
   - If fraud: terminate employee, report to law enforcement
   - If mistake: correct database, retrain employee
5. Remediation:
   - Refund customers for fraudulent orders
   - Correct financial records
   - Strengthen controls to prevent recurrence

### Related Systems
- Database access control
- Audit logging
- Payment reconciliation
- Financial reporting

---

## Summary

Security and compliance for a ticketing platform requires:
1. **Strong authentication and access control**
2. **Fraud prevention (bots, scalpers, counterfeits)**
3. **Compliance with regulations (PCI-DSS, GDPR, AML)**
4. **Account security and insider threat protection**
5. **Audit trails and reconciliation**
6. **Continuous monitoring and incident response**

All edge cases require clear policies, technical controls, and team training.
