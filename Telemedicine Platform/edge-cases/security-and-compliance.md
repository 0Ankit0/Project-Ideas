# Telemedicine Platform: Security & Compliance Edge Cases

This document covers security rule violations, regulatory compliance failures, and authentication/authorization issues that put patient data at risk.

---

## Overview

The telemedicine platform is subject to strict HIPAA Security Rule requirements and state telehealth regulations. This section addresses 7 critical edge cases where security or compliance controls fail, putting PHI (Protected Health Information) at risk or violating legal requirements.

---

## Scenario 1: HIPAA Security Rule — Technical Safeguards Failure

**Failure Mode**: Encryption key management system fails. PHI stored in plaintext briefly before fallback encryption engages. Or: TLS certificate expires, causing unencrypted API traffic.

**Symptoms**:
- Database logs show unencrypted PHI briefly
- API logs show HTTP (non-HTTPS) traffic
- Encryption key unavailable; system reverts to plaintext storage

**Impact** (Critical):
- HIPAA violation: technical safeguard failure per §164.312(a)(2)(ii)
- $100-$50,000 per incident per patient
- Breach notification required if data accessed
- Investigation by HHS OCR

**Detection**:
```javascript
class HIPAASecurityMonitor {
    async monitorEncryptionKeyHealth() {
        // Check KMS key availability
        const kmsKey = await kmsClient.describeKey({
            KeyId: process.env.HIPAA_PHI_KEY_ARN
        });
        
        if (kmsKey.KeyMetadata.Enabled !== true) {
            logger.error('HIPAA VIOLATION: KMS key disabled', {
                keyId: process.env.HIPAA_PHI_KEY_ARN,
                timestamp: now()
            });
            
            await escalateHIPAAViolation('kms_key_disabled', {
                severity: 'CRITICAL',
                actionRequired: 'restore_kms_key_immediately'
            });
        }
    }
    
    async monitorTLSCertificates() {
        const certs = await getCertificateExpiries();
        
        certs.forEach(cert => {
            const daysUntilExpiry = daysBetween(now(), cert.expiryDate);
            
            if (daysUntilExpiry < 0) {
                // Certificate expired!
                logger.error('HIPAA VIOLATION: TLS certificate expired', {
                    domain: cert.domain,
                    expiryDate: cert.expiryDate,
                    timestamp: now()
                });
                
                await escalateHIPAAViolation('tls_cert_expired', {
                    domain: cert.domain,
                    severity: 'CRITICAL'
                });
                
            } else if (daysUntilExpiry < 14) {
                logger.warn('TLS certificate expiring soon', {
                    domain: cert.domain,
                    daysRemaining: daysUntilExpiry
                });
                
                // Trigger renewal
                await renewTLSCertificate(cert.domain);
            }
        });
    }
    
    async monitorUnencryptedPHIAccess() {
        // Query for plaintext PHI fields (should be encrypted)
        const unencryptedAccess = await db.query(`
            SELECT COUNT(*) as count
            FROM audit_logs
            WHERE phi_accessed = true
                AND (
                    data LIKE '%first_name%'
                    OR data LIKE '%last_name%'
                    OR data LIKE '%ssn%'
                    OR data LIKE '%dob%'
                )
                AND timestamp > NOW() - INTERVAL '1 hour'
        `);
        
        if (unencryptedAccess.count > 0) {
            logger.error('HIPAA VIOLATION: Plaintext PHI in logs', {
                count: unencryptedAccess.count,
                timestamp: now()
            });
            
            await escalateHIPAAViolation('plaintext_phi_logged', {
                count: unencryptedAccess.count,
                severity: 'CRITICAL'
            });
        }
    }
}

// Run monitoring every 1 hour
setInterval(() => {
    new HIPAASecurityMonitor().monitorEncryptionKeyHealth();
    new HIPAASecurityMonitor().monitorTLSCertificates();
    new HIPAASecurityMonitor().monitorUnencryptedPHIAccess();
}, 1 * 60 * 60 * 1000);
```

---

## Scenario 2: HITECH Breach Notification — Delayed Beyond 60 Days

**Failure Mode**: Breach discovered; but notification delayed due to investigation complexity or organizational failure. 60-day deadline (per 45 CFR §164.404) passes without notifying patients.

**Symptoms**:
- Breach discovered on Day 0
- Investigation ongoing on Day 45
- Day 60 arrives; notification not sent
- Regulatory violation; HHS fine imminent

**Impact** (Critical):
- HITECH penalty: $100+ per patient per day after deadline
- For 1,000 patients: $100,000+ daily penalties
- State Attorney General enforcement
- Reputational damage; CMS sanctions

**Mitigation**:
```javascript
class BreachNotificationTracker {
    async trackBreachNotificationDeadline(breachId) {
        const breach = await getBreach(breachId);
        const deadline = addDays(breach.discoveredAt, 60);
        
        logger.info('Breach notification deadline tracked', {
            breachId,
            discoveredAt: breach.discoveredAt,
            deadline,
            daysRemaining: daysBetween(now(), deadline)
        });
        
        // Create deadline task with escalation
        await createDeadlineTask({
            breachId,
            deadline,
            escalations: [
                {daysUntilDeadline: 30, action: 'notify_privacy_officer'},
                {daysUntilDeadline: 14, action: 'notify_ceo'},
                {daysUntilDeadline: 7, action: 'critical_alert_all_leadership'},
                {daysUntilDeadline: 1, action: 'send_notifications_or_emergency_board_meeting'},
            ]
        });
    }
    
    async checkBreachNotificationDeadlines() {
        const activeBreach = await getActiveBreach();
        
        const daysUntilDeadline = daysBetween(now(), activeBreach.deadline);
        
        if (daysUntilDeadline === 30) {
            // 30 days left; notify privacy officer
            logger.warn('Breach notification deadline: 30 days remaining', {
                breachId: activeBreach.id
            });
            
            await sendAlert({
                to: 'privacy-officer@company.com',
                subject: 'URGENT: Breach notification deadline in 30 days',
                severity: 'HIGH'
            });
        }
        
        if (daysUntilDeadline === 7) {
            // 1 week left; critical alert
            logger.error('Breach notification deadline: 7 days remaining', {
                breachId: activeBreach.id
            });
            
            await sendAlert({
                to: ['ceo@company.com', 'privacy-officer@company.com', 'general-counsel@company.com'],
                subject: 'CRITICAL: Breach notification deadline in 7 days',
                severity: 'CRITICAL',
                requiresAcknowledgement: true
            });
        }
        
        if (daysUntilDeadline <= 0) {
            // Deadline passed!
            logger.error('REGULATORY VIOLATION: Breach notification deadline PASSED', {
                breachId: activeBreach.id,
                daysOverdue: Math.abs(daysUntilDeadline)
            });
            
            // Emergency response
            await emergencyBreachNotificationSend(activeBreach);
            
            // Notify HHS of late notification (required)
            await notifyHHSOfLateBreachNotification(activeBreach);
        }
    }
}

// Run deadline checks daily
setInterval(() => {
    new BreachNotificationTracker().checkBreachNotificationDeadlines();
}, 1 * 24 * 60 * 60 * 1000);
```

---

## Scenario 3: State Telehealth Prescribing Violations

**Failure Mode**: Clinician prescribes via telemedicine while unlicensed in patient's state. Or: prescribes controlled substance without required state registration. Legal violation.

**Symptoms**:
- Clinician licensed in CA, patient in TX
- Telemedicine Rx issued without TX telehealth registration
- Or: clinician prescribes Schedule II without proper DEA/state credentials
- State board complaint filed

**Impact** (Critical):
- License suspension/revocation for clinician
- Liability for patient harm
- Regulatory fine: $1,000-$50,000 per violation
- Criminal charges (in some states)

**Detection & Prevention**:
```javascript
class TelehealthLicenseValidator {
    async validatePrescribingAuthority(clinicianId, patientState, medicationSchedule) {
        const clinician = await getClinicianProfile(clinicianId);
        
        // Check 1: Clinician licensed in patient's state
        if (!clinician.license_states.includes(patientState)) {
            logger.error('ILLEGAL TELEHEALTH PRESCRIBING: Clinician unlicensed in patient state', {
                clinician: clinicianId,
                state: patientState,
                licensedStates: clinician.license_states
            });
            
            return {
                authorized: false,
                reason: 'clinician_not_licensed_in_state',
                error: `You are not licensed to prescribe in ${patientState}. Only licensed in: ${clinician.license_states.join(', ')}`
            };
        }
        
        // Check 2: If controlled substance, check state telehealth registration
        if (medicationSchedule && ['II', 'III', 'IV', 'V'].includes(medicationSchedule)) {
            const stateRegistration = clinician.state_telehealth_registrations[patientState];
            
            if (!stateRegistration || !stateRegistration.registered) {
                logger.error('ILLEGAL TELEHEALTH CONTROLLED SUBSTANCE PRESCRIBING', {
                    clinician: clinicianId,
                    state: patientState,
                    medicationSchedule,
                    registrationStatus: stateRegistration?.registered || 'not_registered'
                });
                
                return {
                    authorized: false,
                    reason: 'not_registered_for_telehealth_in_state',
                    error: `You are not registered to prescribe controlled substances via telemedicine in ${patientState}`
                };
            }
            
            // Check 3: Telehealth registration not expired
            if (new Date(stateRegistration.expiryDate) < now()) {
                logger.error('EXPIRED TELEHEALTH REGISTRATION', {
                    clinician: clinicianId,
                    state: patientState,
                    expiryDate: stateRegistration.expiryDate
                });
                
                return {
                    authorized: false,
                    reason: 'telehealth_registration_expired',
                    error: `Your telemedicine registration for ${patientState} expired on ${formatDate(stateRegistration.expiryDate)}`
                };
            }
        }
        
        return {authorized: true};
    }
    
    async blockPrescriptionIfUnauthorized(prescriptionId) {
        const prescription = await getPrescription(prescriptionId);
        const clinician = await getClinicianProfile(prescription.clinician_id);
        const patient = await getPatient(prescription.patient_id);
        
        const validation = await this.validatePrescribingAuthority(
            prescription.clinician_id,
            patient.state,
            prescription.dea_schedule
        );
        
        if (!validation.authorized) {
            // Block prescription signing
            logger.error('BLOCKING UNAUTHORIZED PRESCRIPTION', {
                prescriptionId,
                reason: validation.reason,
                clinician: prescription.clinician_id,
                patient_state: patient.state
            });
            
            await updatePrescriptionStatus(prescriptionId, {
                status: 'blocked_authorization_failure',
                reason: validation.reason,
                blockedAt: now(),
                blockedBy: 'system_compliance_check'
            });
            
            // Notify clinician
            await notifyClinicianOfBlockedPrescription(prescription.clinician_id, {
                prescriptionId,
                reason: validation.error
            });
            
            // Create compliance ticket
            await createComplianceTicket({
                type: 'unauthorized_telehealth_prescribing_attempt',
                clinician: prescription.clinician_id,
                patient_state: patient.state,
                medication_schedule: prescription.dea_schedule,
                severity: 'CRITICAL',
                requiresInvestigation: true
            });
            
            // Alert board of medicine
            await reportToStateBoardOfMedicine({
                clinician: clinician.name,
                npi: clinician.npi,
                state: patient.state,
                violationType: 'unauthorized_telehealth_prescribing',
                detail: validation.error
            });
        }
    }
}

// Validate EVERY prescription before signing
async function signPrescriptionWithAuthorityCheck(prescriptionId) {
    const validator = new TelehealthLicenseValidator();
    
    // Validate first
    await validator.blockPrescriptionIfUnauthorized(prescriptionId);
    
    // Check if prescription is still in 'draft' (not blocked)
    const prescription = await getPrescription(prescriptionId);
    
    if (prescription.status !== 'draft') {
        throw new Error('Prescription cannot be signed due to authorization failure');
    }
    
    // Proceed with signing
    await signPrescription(prescriptionId);
}
```

---

## Scenario 4: SOC-2 Type II Control Failure

**Failure Mode**: Quarterly SOC-2 audit detects control failure (e.g., MFA not enforced, access logging disabled). Non-compliance = loss of enterprise customers.

**Symptoms**:
- Auditor finding: "MFA not enforced for clinical staff"
- Finding: "Access logs show gaps; incomplete audit trail"
- Rating: "Non-compliant"

**Impact** (High):
- Customer contracts include "SOC-2 Type II compliance" requirement
- Failure = breach of contract; customer can terminate
- Reputation damage in healthcare IT market

**Mitigation**:
```javascript
class SOC2ComplianceMonitor {
    async enforceAccessControls() {
        // SOC-2 Control: Access Control (CC6)
        // Requirement: MFA enforced for all users accessing PHI
        
        const staffWithoutMFA = await db.query(`
            SELECT id, email, role
            FROM users
            WHERE role IN ('clinician', 'admin', 'clinician')
                AND mfa_enabled = false
                AND created_at < NOW() - INTERVAL '30 days'  // Grace period for new users
        `);
        
        if (staffWithoutMFA.length > 0) {
            logger.error('SOC-2 VIOLATION: Staff without MFA', {
                count: staffWithoutMFA.length,
                users: staffWithoutMFA.map(u => u.email)
            });
            
            // Force MFA enrollment
            staffWithoutMFA.forEach(user => {
                markMFARequired(user.id, {
                    deadline: addDays(now(), 7),
                    note: 'SOC-2 compliance requirement'
                });
            });
        }
    }
    
    async enforceAuditLogging() {
        // SOC-2 Control: Logical and Physical Access Controls (CC7)
        // Requirement: Complete audit trail of all PHI access
        
        // Check for query timeouts / lost logs
        const logGaps = await detectAuditLogGaps();
        
        if (logGaps.length > 0) {
            logger.error('SOC-2 VIOLATION: Audit log gaps detected', {
                gaps: logGaps.length,
                details: logGaps
            });
            
            // Create SOC-2 incident ticket
            await createSOC2IncidentTicket({
                control: 'CC7_Logical_Physical_Access',
                finding: 'Incomplete audit trail / log gaps',
                severity: 'CRITICAL',
                requiresRemediationBefore: addDays(now(), 30)
            });
        }
    }
}

// Run SOC-2 monitoring continuously
setInterval(() => {
    const monitor = new SOC2ComplianceMonitor();
    monitor.enforceAccessControls();
    monitor.enforceAuditLogging();
}, 1 * 60 * 60 * 1000);  // Every hour
```

---

## Scenario 5: Business Associate Agreement (BAA) Lapse

**Failure Mode**: BAA with vendor expires or is not signed. Vendor continues to access PHI without BAA. Legal violation.

**Symptoms**:
- EHR vendor (Epic) continues to access patient data
- BAA expiration notice received; vendor renewal delayed
- PHI being processed without signed agreement

**Impact** (Critical):
- Vendor accessing PHI without BAA = HIPAA violation
- Joint liability: client responsible
- Regulatory fine: $100-$50,000 per patient for each day of non-compliance
- Breach notification may be required

**Detection**:
```javascript
class BAAComplianceTracker {
    async monitorBAAExpirations() {
        const allVendors = await getVendorsWithPHIAccess();
        const expiringBAAa = [];
        
        allVendors.forEach(vendor => {
            const baa = vendor.baa;
            
            if (!baa) {
                logger.error('CRITICAL: Vendor without BAA accessing PHI', {
                    vendor: vendor.name,
                    vendorType: vendor.type,
                    phiAccessLevel: vendor.phiAccessLevel,
                    firstAccessDate: vendor.firstPHIAccessDate
                });
                
                expiringBAAa.push({
                    vendor: vendor.name,
                    status: 'missing_baa',
                    severity: 'CRITICAL'
                });
                
            } else if (new Date(baa.expiryDate) < now()) {
                logger.error('CRITICAL: Vendor BAA EXPIRED', {
                    vendor: vendor.name,
                    expiryDate: baa.expiryDate
                });
                
                expiringBAAa.push({
                    vendor: vendor.name,
                    status: 'expired_baa',
                    severity: 'CRITICAL'
                });
                
            } else {
                const daysUntilExpiry = daysBetween(now(), new Date(baa.expiryDate));
                
                if (daysUntilExpiry < 90) {
                    logger.warn('Vendor BAA expiring soon', {
                        vendor: vendor.name,
                        daysUntilExpiry
                    });
                    
                    expiringBAAa.push({
                        vendor: vendor.name,
                        status: 'expiring_soon',
                        daysRemaining: daysUntilExpiry,
                        severity: 'HIGH'
                    });
                }
            }
        });
        
        if (expiringBAAa.length > 0) {
            // Escalate
            await escalateBAAExpiration(expiringBAAa);
        }
    }
    
    async escalateBAAExpiration(expiringBAAa) {
        logger.error('BAA COMPLIANCE CRISIS', {count: expiringBAAa.length});
        
        // Critical BAAa missing/expired
        const critical = expiringBAAa.filter(b => b.severity === 'CRITICAL');
        
        if (critical.length > 0) {
            // Immediately suspend vendor PHI access
            critical.forEach(async (item) => {
                const vendor = await getVendor(item.vendor);
                
                logger.error('SUSPENDING VENDOR PHI ACCESS - BAA VIOLATION', {
                    vendor: item.vendor
                });
                
                await suspendVendorPHIAccess(vendor.id, {
                    reason: item.status === 'missing_baa' ? 'missing_baa' : 'expired_baa',
                    severity: 'CRITICAL',
                    requiresImmediateRenewal: true
                });
                
                // Notify leadership
                await sendAlert({
                    to: 'ceo@company.com,general-counsel@company.com,privacy-officer@company.com',
                    subject: `CRITICAL: ${vendor.name} PHI access suspended - ${item.status}`,
                    body: `${vendor.name} BAA is ${item.status}. PHI access suspended until BAA renewed. Immediate action required.`,
                    severity: 'CRITICAL'
                });
            });
        }
        
        // High priority: expiring soon
        const expiringSoon = expiringBAAa.filter(b => b.severity === 'HIGH');
        
        expiringSoon.forEach(item => {
            // Notify procurement to renew
            notifyProcurementTeam({
                vendor: item.vendor,
                daysRemaining: item.daysRemaining,
                urgency: 'HIGH'
            });
        });
    }
}

// Check BAA status daily
setInterval(() => {
    new BAAComplianceTracker().monitorBAAExpirations();
}, 1 * 24 * 60 * 60 * 1000);
```

---

## Scenario 6: MFA Bypass for Clinical Staff

**Failure Mode**: Clinician circumvents MFA (shares password, disables 2FA, uses backup code). Unauthorized access risk.

**Symptoms**:
- Audit log shows login without MFA verification
- Or: login from unusual location with MFA disabled
- Or: multiple MFA attempts followed by success (brute force attempt)

**Impact** (Critical):
- Unauthorized access to patient records
- Potential PHI breach
- HIPAA violation; regulatory fine
- Patient notification likely required

**Detection**:
```javascript
class MFABypassDetector {
    async detectMFABypass() {
        // Pattern 1: Login without MFA for user with MFA enabled
        const bypassLogins = await db.query(`
            SELECT user_id, ip_address, timestamp
            FROM login_logs
            WHERE mfa_required = true
                AND mfa_verified = false
                AND login_successful = true
                AND timestamp > NOW() - INTERVAL '24 hours'
        `);
        
        if (bypassLogins.length > 0) {
            logger.error('MFA BYPASS DETECTED', {
                count: bypassLogins.length,
                logins: bypassLogins
            });
            
            // Disable user account immediately
            bypassLogins.forEach(async (login) => {
                const user = await getUser(login.user_id);
                
                await disableUserAccount(user.id, {
                    reason: 'mfa_bypass_attempt',
                    severity: 'CRITICAL',
                    requiresManualReactivation: true
                });
                
                // Alert security
                await sendSecurityAlert({
                    message: `MFA bypass attempt by ${user.email}. Account disabled.`,
                    severity: 'CRITICAL'
                });
            });
        }
        
        // Pattern 2: Backup code usage (should be rare)
        const backupCodeUsage = await db.query(`
            SELECT user_id, backup_code_used_at, ip_address
            FROM mfa_backup_codes
            WHERE used = true
                AND used_at > NOW() - INTERVAL '7 days'
        `);
        
        // One backup code is fine; multiple = suspicious
        const suspiciousUsers = backupCodeUsage.reduce((acc, code) => {
            if (!acc[code.user_id]) acc[code.user_id] = 0;
            acc[code.user_id]++;
            return acc;
        }, {});
        
        Object.entries(suspiciousUsers).forEach(async ([userId, codeCount]) => {
            if (codeCount > 3) {
                // Multiple backup codes used; suspicious
                logger.warn('Suspicious backup code usage', {
                    userId,
                    codeCount
                });
                
                // Re-enroll user in MFA
                const user = await getUser(userId);
                await requireMFAReEnrollment(userId, {
                    reason: 'suspicious_backup_code_usage',
                    message: `Your MFA setup appears compromised. Please re-enroll.`
                });
            }
        });
    }
}
```

---

## Scenario 7: Sensitive Data in Application Logs

**Failure Mode**: PHI (SSN, DOB, MRN, diagnosis) accidentally logged in plaintext. Logs stored unencrypted or accessed by non-authorized personnel.

**Symptoms**:
- Log scanning tool finds: "SSN: 123-45-6789"
- Or: error stack trace includes patient name/MRN
- Or: debug logs show full API payloads with PHI

**Impact** (High):
- PHI exposed in logs (breach risk if logs accessed)
- Regulatory violation; breach notification may be required
- HIPAA fine: $100-$50,000 per incident

**Mitigation**:
```javascript
// Middleware: mask PHI in logs
app.use((req, res, next) => {
    const maskedBody = maskPHIInRequest(req.body);
    req.maskedBody = maskedBody;
    
    logger.debug('Request', {
        method: req.method,
        path: req.path,
        body: maskedBody  // Use masked body for logging
    });
    
    next();
});

function maskPHIInRequest(obj) {
    const phiPatterns = {
        ssn: /\d{3}-\d{2}-\d{4}/g,
        phone: /\d{3}-\d{3}-\d{4}/g,
        email: /[\w\.-]+@[\w\.-]+/g,
        mrn: /MRN[:\s]*([A-Z0-9]+)/gi,
        firstName: /firstName[:\s]*"([^"]+)"/gi,
        lastName: /lastName[:\s]*"([^"]+)"/gi
    };
    
    let masked = JSON.stringify(obj);
    
    Object.entries(phiPatterns).forEach(([pattern, regex]) => {
        masked = masked.replace(regex, `[MASKED_${pattern.toUpperCase()}]`);
    });
    
    return JSON.parse(masked);
}
```

---

## Summary Table

| Scenario | Root Cause | Impact | Prevention |
|----------|---|---|---|
| HIPAA Safeguard Failure | Encryption/TLS issue | CRITICAL | Monitor keys, cert renewal |
| Breach Notification Delay | Slow investigation | CRITICAL | Deadline tracking, escalation |
| Telehealth License Violation | Unlicensed prescribing | CRITICAL | License validation per Rx |
| SOC-2 Failure | Control weakness | HIGH | Continuous compliance monitoring |
| BAA Lapse | Expired/missing agreement | CRITICAL | BAA tracking, auto-renewal |
| MFA Bypass | Weak enforcement | CRITICAL | Detect bypasses, auto-disable |
| PHI in Logs | Logging middleware failure | HIGH | Log masking, scanning |
