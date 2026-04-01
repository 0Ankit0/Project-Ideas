# Security and Compliance Edge Cases

This document outlines critical edge cases in security, compliance, and data protection for the Digital Banking Platform. Each scenario covers failure modes, detection mechanisms, mitigation strategies, and recovery procedures.

---

## 1. PCI-DSS SAQ-D Scope Reduction via Tokenization

### Scenario
The platform processes payment card information directly (captures PAN, CVV, expiration date from customer input). This requires PCI-DSS Service Provider Assessment Questionnaire D (SAQ-D), the most stringent compliance level. Implementing tokenization (issuing unique tokens instead of storing raw card data) can reduce scope to SAQ-A-EP (simplified), saving $50K-$100K annually in compliance audits and reducing audit burden.

### Failure Mode
- Current architecture: cards stored in Stripe's encrypted vault via API
- Compliance assessment: requires SAQ-D due to card data handling in checkout flow
- Business goal: reduce to SAQ-A-EP by implementing tokenization
- Implementation challenge: complex integration, high risk of cardholder data leakage during migration

### Impact
- **Compliance:** Failing to reduce scope means unnecessary SAQ-D compliance burden
- **Financial:** Higher audit costs, larger PCI scope requires more security controls
- **Operational:** Complex audit requirements, security assessments, penetration testing

### Detection
- SAQ assessment: regular PCI compliance assessment to identify scope
- Cardholder data inventory: map all systems handling payment card information
- Scope analysis: determine if tokenization is feasible without compromising functionality

### Mitigation
- **Stripe Payment Intents:** Use Stripe's Payment Intents API with automatic tokenization
  - Customer enters card data into Stripe-hosted form (iframes)
  - No raw card data touches platform servers
  - Stripe returns card token instead of raw card data
  - Platform stores token, not card data
- **PCI Scope Reduction:** This architecture reduces scope to SAQ-A-EP
- **Security Enhancement:** Improves security by reducing cardholder data exposure
- **Implementation Steps:**
  1. Migrate existing card storage to tokenized approach
  2. Update payment processing to use card tokens
  3. Ensure no raw card data logged in system
  4. Implement monitoring to detect accidental card data logging
  5. Update security documentation
  6. Conduct gap assessment for SAQ-A-EP compliance
  7. Perform penetration testing to validate no card data exposure
  8. Obtain SAQ-A-EP compliance certification

### Recovery / Implementation Steps
1. Define tokenization architecture (Stripe Payment Intents)
2. Create parallel payment flow for new customers (legacy + new)
3. Test new flow thoroughly (unit tests, integration tests, penetration testing)
4. Gradually migrate legacy card data:
   - For existing stored cards: re-tokenize using Stripe API
   - For new payment methods: use tokenized approach
5. Audit logs: verify no raw card data appears anywhere
6. Compliance documentation: update to reflect new architecture
7. Security assessment: external auditor verifies SAQ-A-EP scope reduction
8. Certification: obtain updated PCI compliance certification

### Related Systems
- Payment processing (Stripe)
- Card tokenization service
- Customer payment profile management
- Audit logging system
- Security monitoring and alerting
- Compliance documentation system

---

## 2. GDPR Right-to-Erasure vs. 7-Year Retention

### Scenario
A customer exercises their GDPR "right to be forgotten" and requests complete erasure of their personal data from the platform. However, banking regulations (e.g., Anti-Money Laundering rules) require retention of transaction records for 7 years for audit and compliance purposes. These two requirements conflict: GDPR demands erasure, regulations demand retention.

### Failure Mode
- Customer requests right-to-erasure under GDPR Article 17
- Platform identifies conflicting retention requirement (AML 7-year rule)
- Uncertainty: erase data (violate regulations) or keep data (violate GDPR)
- Potential regulatory fine regardless of choice

### Impact
- **Legal:** Risk of GDPR fine (€10-20M or 2-4% revenue) or AML fine
- **Operational:** Unclear how to handle conflicting requirements
- **Customer:** Expectation not met if data not erased

### Detection
- Erasure request tracking: monitor all right-to-erasure requests
- Compliance review: assess retention obligations for each data type
- Legal review: identify conflicts between privacy and regulatory requirements

### Mitigation
- **Tiered erasure approach:**
  1. **Customer-facing data:** Erase immediately (name, contact, profile)
  2. **Transaction records:** Anonymize instead of erase
     - Remove customer name and contact information
     - Retain transaction amount, date, counterparty for regulatory purposes
     - Link anonymized records via hash of customer ID (not stored plaintext)
  3. **Compliance data:** Retain per regulatory requirement (7 years for AML)
  4. **Purpose limiting:** Restrict access to anonymized data to compliance team only
- **Documentation:** Maintain clear record of what was erased, what was anonymized, and why
- **Technical implementation:**
  - Soft-delete approach: mark customer as "erased" but retain necessary transaction data
  - Anonymization: hash customer identifiers, remove personal identifiers
  - Access control: restrict erased customer data access to compliance-only roles
  - Encryption: encrypt anonymized transaction data with separate key

### Recovery / Implementation Steps
1. Customer submits right-to-erasure request
2. Compliance review: identify what data must be erased vs. retained
3. Data erasure:
   - Customer name, address, contact info: deleted
   - Payment methods: deleted
   - Transaction history (personal details): anonymized (remove names, keep amounts/dates)
   - AML screening records: retained per 7-year rule
4. System implementation:
   - Mark customer record as "erased"
   - Remove customer from searchable indexes
   - Anonymize all customer identifiers
5. Verification: confirm personal identifiers removed from all systems
6. Customer notification: confirm erasure completed, explain retained data
7. Documentation: maintain record of erasure action and rationale

### Related Systems
- Customer profile management
- Data anonymization service
- Access control and role-based security
- Transaction data storage
- GDPR compliance tracking system
- Audit logging system

---

## 3. SOX Controls and Financial Reporting Accuracy

### Scenario
Sarbanes-Oxley (SOX) requires that publicly-traded companies maintain effective internal controls over financial reporting. The banking platform processes customer deposits and transfers, which directly affect the company's balance sheet. A control gap is discovered: transaction amounts can be modified in the database by privileged users without audit trail. This violates SOX control requirements.

### Failure Mode
- Transaction amount modification: admin users can update transaction amount in database
- Audit trail missing: no log of who modified, when, or why
- Control gap: violates SOX requirement for change control
- Risk: transaction amounts could be modified to hide fraud or reporting errors

### Impact
- **Regulatory:** SOX violation, potential SEC enforcement
- **Financial:** Unreliable financial statements if transactions can be modified
- **Operational:** Loss of audit trail for transaction history

### Detection
- SOX control assessment: annual review of internal controls
- Audit trail review: examine transaction modification logs
- Gap analysis: identify systems/data without adequate change control

### Mitigation
- **Immutable transaction records:**
  - All completed transactions: immutable (read-only)
  - Only metadata can be changed (description, category)
  - Transaction amount/date/parties: never modifiable
- **Audit trail for all changes:**
  - Every modification logged: user ID, timestamp, old value, new value, reason
  - Logs stored separately and protected (read-only)
  - Compliance team can review audit trail for any change
- **Privileged access controls:**
  - Separate approval required for any transaction correction
  - Manual review and documentation of correction reason
  - Approver must be senior team member (not transaction initiator)
- **Reconciliation controls:**
  - Daily reconciliation of transaction records to general ledger
  - Investigation of any discrepancies
  - Monthly SOX control testing

### Recovery / Implementation Steps
1. Audit identifies transaction modification gap
2. Implement immutable transaction design:
   - Transaction status transitions (pending → completed → settled)
   - Completed transactions locked from modification
   - Only metadata editable (tags, notes, not amounts)
3. Implement audit logging:
   - Log all transaction changes with user, timestamp, before/after values
   - Protect logs from modification (append-only)
4. Exception handling:
   - If transaction correction needed: create journal entry instead of modifying transaction
   - Requires approval from finance team lead
   - Documented in audit trail
5. Testing and validation:
   - Verify transactions cannot be modified post-completion
   - Verify all changes are logged
6. SOX certification:
   - Update control documentation
   - Conduct control testing and certification
   - Obtain compliance certification

### Related Systems
- Transaction processing system
- General ledger system
- Audit logging system
- Access control system
- SOX compliance tracking
- Financial reporting system

---

## 4. MFA Bypass (SIM Swap and SS7 Attacks)

### Scenario
A customer enables two-factor authentication (2FA) using SMS OTP to their registered phone number. A bad actor performs a SIM swap attack: calls the mobile carrier, claims to be the customer, and requests the SIM card to be transferred to a new device controlled by the attacker. The attacker now receives SMS messages intended for the customer, including 2FA OTPs. The attacker logs into the customer's account and transfers all funds.

### Failure Mode
- Customer uses SMS-based 2FA (OTP sent to phone)
- Attacker performs SIM swap attack (impersonates customer to carrier)
- Attacker receives SMS messages (including 2FA OTP)
- Attacker logs in and drains account
- Customer's 2FA mechanism bypassed by SIM swap

### Impact
- **Customers:** Account compromised, funds stolen
- **Business:** Fraud loss, customer churn, regulatory exposure
- **Reputational:** High-profile fraud case

### Detection
- Unusual login patterns: flag login from new device/location
- High-velocity transactions: flag large/multiple transfers post-login
- Carrier notification: some carriers notify customer of SIM changes (via email)
- Fraud detection: ML model flags suspicious activity post-login

### Mitigation
- **Hardware security keys:** Support hardware MFA (FIDO2/U2F keys) as alternative to SMS
  - More secure than SMS OTP
  - Resistant to SIM swap attacks
  - Encourage adoption for high-value accounts
- **SIM swap monitoring:**
  - Detect unusual phone number changes on account
  - If phone number changed: require verification via old phone before activating
  - Notify customer of phone number changes
- **Login notifications:** Send email notification of login from new device
  - Include device info (IP, location, device type)
  - Allow customer to "approve" or "deny" login
  - Block login if customer denies within 10 minutes
- **Velocity limits:** Limit high-value transactions (>$1000) in first 24 hours post-login
- **Device binding:** Bind 2FA to specific device (phone + app installation)
  - Require re-verification if device changes
  - SIM swap alone doesn't grant access
- **Biometric backup:** Support biometric authentication as 2FA fallback

### Recovery Steps
1. Unauthorized login detected (flagged by fraud detection)
2. Account immediately locked
3. Customer notified: "Unusual login activity detected"
4. Verification required: customer must verify via backup method:
   - Security questions
   - Account recovery email
   - Calling customer service
5. If customer verifies compromise: account locked, password reset required
6. Investigation:
   - Identify fraudulent transactions
   - Reverse transactions (if possible)
   - Contact police to file report
7. SIM swap prevention:
   - Customer contacts carrier: add PIN/password to account
   - Request that carrier no longer accept phone changes via phone call (require in-person)
8. Account recovery:
   - New 2FA method setup (hardware key recommended)
   - Password change
   - Device re-verification
   - Login audit trail reviewed

### Related Systems
- 2FA/MFA service
- Login authentication service
- Fraud detection engine
- Customer communication service
- Account management service
- Device management system

---

## 5. Privileged Access Management and Insider Threat

### Scenario
A disgruntled database administrator (DBA) with production database access plans to extract customer data and sell it to a competitor. The DBA has legitimate access to customer tables for backup and maintenance purposes. However, there are no detection mechanisms to flag unusual database queries (e.g., bulk export of all customer emails and phone numbers).

### Failure Mode
- DBA has production database access for legitimate operational purposes
- DBA executes query: SELECT email, phone FROM customers (all 500K customers)
- Query exports to CSV file on DBA's personal laptop
- No audit trail, no detection of unusual access pattern
- Data breach discovered months later when competitor misuses data

### Impact
- **Security:** Insider threat, data exfiltration
- **Regulatory:** Data breach notification required (GDPR, CCPA, etc.)
- **Financial:** Fine, credit monitoring for affected customers
- **Reputational:** Loss of customer trust

### Detection
- Database activity monitoring: track all queries, identify unusual access patterns
- Baseline behavior: establish normal queries for each user role
- Anomaly detection: flag queries that deviate from baseline (bulk exports, unusual tables)
- File transfer monitoring: detect large data transfers from production servers
- Device monitoring: track USB drives, external devices connected to production servers

### Mitigation
- **Principle of least privilege:**
  - DBA access scoped to minimum required tables
  - Production database access: only on need-to-know basis
  - Separate read-only access for reports (no ability to export all data)
- **Database Activity Monitoring (DAM):**
  - Log all queries: user, timestamp, query text, affected rows
  - Real-time alerts on suspicious patterns:
    - Bulk SELECT without WHERE clause (all rows)
    - SELECT from customer PII tables by non-analytics roles
    - Large exports to external systems
- **Access approval:**
  - All production database access: requires manager approval
  - Approval documents purpose and duration
  - Access expires after N days (require re-approval)
- **Separation of duties:**
  - Database administration: separate from data access
  - Data export: requires approval from data governance team
  - Audit of who approved each export
- **Encryption and masking:**
  - Customer PII encrypted in database (not plaintext)
  - Encryption keys stored separately (not accessible to DBA)
  - DBA cannot read unencrypted customer data even with database access
- **Physical and network security:**
  - Production servers: restricted network access
  - USB drives: disabled on production systems
  - VPN/bastion host: all production access via secure channel

### Recovery Steps
1. Insider threat or data exfiltration detected
2. Immediate action:
   - Revoke user access to all systems
   - Secure all user devices (laptop, phone, etc.)
   - Preserve audit logs and forensic evidence
3. Investigation:
   - Review database activity logs for past 12 months
   - Identify what data was accessed
   - Determine if data was exfiltrated
   - Identify destination of data
4. Response:
   - If data exfiltrated: breach notification to affected customers
   - Law enforcement: file criminal complaint
   - Prevent further exfiltration: change database passwords, revoke access
5. Remediation:
   - Audit all privileged users (HR, IT, Finance, DBA)
   - Implement enhanced monitoring for all privileged access
   - Require hardware security keys for all privileged user logins
   - Mandatory training on data protection and insider threat

### Related Systems
- Database access control and monitoring
- Database activity monitoring (DAM) tool
- Encryption and key management
- Access approval and provisioning system
- Audit logging system
- Incident management system

---

## 6. Cloud Provider Security Incident

### Scenario
The platform runs on AWS (EKS for compute, RDS for database, S3 for storage). A critical vulnerability is discovered in AWS infrastructure (e.g., EC2 hypervisor vulnerability). Amazon notifies AWS customers that they must patch or migrate workloads by a deadline. The platform must execute emergency migration within 48 hours to avoid exposure.

### Failure Mode
- AWS announces critical security vulnerability in hypervisor
- Affected: all EC2 instances (including EKS worker nodes)
- Fix: requires restarting instances (automatic patching)
- Customer data risk: potential memory leakage between VMs on same host
- Deadline: AWS requires remediation within 48 hours

### Impact
- **Security:** Potential exposure of customer data to other AWS customers
- **Business:** Emergency operational response required, service disruption risk
- **Compliance:** Need to document remediation and notify regulators if applicable

### Detection
- AWS notifications: security advisories from AWS
- Vulnerability scanning: identify affected resources
- Patch management system: track which systems are patched

### Mitigation
- **Rapid patch deployment:**
  - AWS provides automated patching (usually)
  - Platform can schedule patching during maintenance window
  - For high-availability: rolling restart (some instances down, not all)
- **Disaster recovery procedures:**
  - Documented runbook for emergency patching
  - Testing: perform regular DR drills
  - Team training: ensure ops team can execute runbook
- **High availability:**
  - Multi-AZ deployment: database replicated across AZs
  - Load balancer: traffic distributed across healthy instances
  - Graceful degradation: service continues with reduced capacity during patching
- **Communication:**
  - Notify customers before maintenance (status page update)
  - Provide maintenance window and expected duration
  - Post-maintenance: confirm no data loss or corruption

### Recovery / Implementation Steps
1. AWS announces security advisory requiring urgent patching
2. Impact assessment: identify affected resources (EKS nodes, RDS, etc.)
3. Patch plan:
   - Check AWS patch status (usually automatic)
   - Schedule maintenance window (off-peak hours)
   - For rolling restart: update pod disruption budgets to ensure service availability
4. Pre-maintenance checklist:
   - Backup database
   - Verify backup restorability
   - Prepare rollback plan
   - Notify customer support team
5. Maintenance execution:
   - Restart instances in rolling fashion (not all at once)
   - Monitor service health during restarts
   - Verify no data loss
6. Post-maintenance:
   - Verify patched status (AWS reports patch status)
   - Database integrity check
   - Full regression test
   - Customer notification: patching complete, service normal

### Related Systems
- Cloud infrastructure (AWS EKS, RDS, S3)
- Patch management system
- Backup and disaster recovery system
- Status page / incident management
- Customer communication system
- Monitoring and alerting

---

## 7. Penetration Test CVSS ≥9.0 Remediation SLA

### Scenario
An annual security assessment (penetration test) discovers a critical vulnerability: unauthenticated SQL injection in the transaction search API (CVSS 9.2 - critical severity). The vulnerability allows an attacker to query all customer transactions without authentication. Regulatory requirements mandate that critical vulnerabilities be remediated within 30 days. The platform must develop and deploy a fix within this SLA while maintaining service availability.

### Failure Mode
- Pen test discovers SQL injection vulnerability (CVSS 9.2)
- Vulnerability allows unauthenticated data access
- 30-day regulatory SLA to remediate
- Fix development and testing must complete quickly without introducing new bugs
- Pressure to deploy quickly increases risk of incomplete fix or new regressions

### Impact
- **Security:** Critical vulnerability exposes customer data
- **Regulatory:** Compliance violation if not remediated within SLA
- **Business:** Reputation risk, potential regulatory enforcement

### Detection
- Penetration testing: regular security assessments identify vulnerabilities
- Vulnerability scanning: automated scanning for known vulnerabilities
- Code review: identify injection points in code

### Mitigation
- **Root cause:** SQL injection vulnerability in search API
  - Problem: concatenating user input into SQL query without parameterization
  - Solution: use parameterized queries (prepared statements)
- **Remediation steps:**
  1. Code review: identify all injection points in codebase
  2. Implement parameterized queries: replace string concatenation with prepared statements
  3. Input validation: validate search parameters (length, allowed characters)
  4. Authentication: require authentication for all API endpoints
  5. Authorization: verify user can only access their own transactions
- **Testing:**
  - Unit tests: verify parameterized queries execute correctly
  - Integration tests: verify API returns correct results
  - Penetration testing: confirm vulnerability is fixed
  - Regression testing: verify other features still work
- **Rollout:**
  - Staged rollout: deploy to 10% of users first, monitor for errors
  - Full rollout: once 10% deployment stable (24 hours), deploy to all users
  - Rollback plan: if issues, can rollback to previous version within 30 minutes
- **Timeline:**
  - Day 1-2: Root cause analysis and fix development
  - Day 3: Testing and validation
  - Day 4: Staged deployment
  - Day 5: Full deployment
  - Day 6-30: Continued monitoring and penetration test confirmation

### Recovery / Implementation Steps
1. Critical vulnerability discovered: SQL injection in search API
2. Severity assessment: CVSS 9.2, must remediate within 30 days
3. Immediate action: disable vulnerable API endpoint (customer communication)
4. Root cause analysis: identify all SQL injection points
5. Remediation:
   - Rewrite vulnerable queries using parameterized statements
   - Add input validation
   - Add authentication and authorization checks
6. Testing:
   - Unit test: verify parameterized queries work
   - Integration test: verify API behavior unchanged
   - Penetration test: confirm vulnerability fixed
   - Load test: verify performance not degraded
7. Deployment:
   - Staged rollout to 10% users
   - Monitor for errors (logs, error rate, user feedback)
   - Full rollout after 24 hours if stable
8. Verification:
   - Penetration tester confirms fix
   - Document remediation in audit trail
   - Update vulnerability status to "resolved"
9. Process improvement:
   - Code review: add SAST scanning for SQL injection
   - Training: team training on secure coding practices
   - Testing: add injection attack tests to test suite

### Related Systems
- Source code repository
- Continuous integration / continuous deployment (CI/CD)
- Application security testing tools (SAST, DAST)
- Penetration testing tools
- Monitoring and alerting
- Incident management system

---

## Summary

These security and compliance edge cases represent real challenges in maintaining a secure, compliant banking platform. Key principles for handling these scenarios:

1. **Prevention:** Build security and compliance into architecture from the start
2. **Detection:** Monitor for security incidents and compliance violations
3. **Response:** Have documented processes for responding to security issues
4. **Remediation:** Fix vulnerabilities within regulatory SLAs
5. **Documentation:** Maintain audit trail of all security decisions and actions
6. **Continuous Improvement:** Learn from incidents and update processes

Security and compliance must be balanced with business needs. Regular assessments, testing, and team training are essential to maintaining a secure banking platform.
