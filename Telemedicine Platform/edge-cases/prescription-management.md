# Telemedicine Platform: Prescription Management Edge Cases

This document describes critical failure scenarios for electronic prescription handling, pharmacy routing, DEA compliance, and PDMP integration. Scenarios cover system outages, data integrity issues, and regulatory violations.

---

## Scenario 1: DEA EPCS System Outage

**Failure Mode**: DEA's EPCS (Electronic Prescriptions for Controlled Substances) system is unavailable or returns errors. Clinician cannot digitally sign or transmit controlled substance (Schedule II-V) prescriptions electronically.

**Symptoms**:
- Clinician clicks "Sign Prescription" for Schedule II controlled substance (e.g., oxycodone)
- Error: "DEA EPCS system unavailable. Cannot sign controlled substance prescriptions."
- Digital signature button disabled
- Prescription stuck in "Draft" status

**Impact** (Critical):
- No electronic prescriptions for Schedules II-V (opioids, benzodiazepines, stimulants)
- Clinician forced to print + fax (HIPAA-compliant but labor-intensive)
- Patient cannot pick up medication immediately; must wait for fax delivery
- Insurance may deny claim for non-electronic Rx submission
- Potential patient harm if medication time-sensitive

**Detection**:
```javascript
class DEAVerifier {
    async verifyDEAAvailability() {
        try {
            // Health check: attempt simple DEA CSOS query
            const testResponse = await dea_csos_client.ping({
                timeout: 5000,
                retries: 2
            });
            
            if (!testResponse.ok) {
                logger.error('DEA EPCS system unhealthy', {
                    status: testResponse.status,
                    timestamp: now()
                });
                
                publishEvent('dea_epcs_unavailable', {
                    reason: 'health_check_failed',
                    lastHealthyAt: await getLastHealthyTimestamp()
                }, 'CRITICAL');
                
                return { available: false, reason: 'unavailable' };
            }
            
            return { available: true };
            
        } catch (error) {
            logger.error('DEA availability check failed', {
                error: error.message,
                timestamp: now()
            });
            
            publishEvent('dea_epcs_check_error', {
                error: error.message
            }, 'CRITICAL');
            
            return { available: false, reason: 'connection_error' };
        }
    }
}

// Health check every 60 seconds
setInterval(async () => {
    const status = await new DEAVerifier().verifyDEAAvailability();
    
    if (!status.available) {
        logger.error('DEA EPCS DOWN', {status, timestamp: now()});
        
        // Notify all active clinicians
        broadcastNotification({
            type: 'dea_epcs_down',
            message: 'DEA EPCS system is unavailable. Controlled substance Rx must be printed and faxed.',
            severity: 'CRITICAL',
            targetRole: 'clinician'
        });
        
        // Activate incident response
        activateIncidentResponse('DEA_EPCS_OUTAGE');
    }
}, 60 * 1000);
```

**Root Causes**:
1. **DEA CSOS maintenance** (30% of cases)
   - Planned maintenance window (announced in advance)
   - Unplanned system updates
   - Database migration
   
2. **DEA infrastructure failure** (40% of cases)
   - Server crash or restart
   - Network connectivity issue at DEA data center
   - Database unavailable
   
3. **Network connectivity** (20% of cases)
   - BGP route failure to DEA servers
   - Firewall rule blocking telemedicine platform to DEA
   - ISP connectivity loss
   
4. **Authentication failure** (10% of cases)
   - Platform's DEA credentials expired
   - Certificate validation failure
   - API key revoked

**Mitigation**:
1. **Dual Redundancy**
   - Primary DEA CSOS endpoint (csos.dea.gov)
   - Fallback CSOS mirror/cache (maintained by HHS)
   - Regular (every 1 hour) cache sync with DEA
   
2. **Graceful Degradation for Non-Emergency Rx**
   - Non-controlled substances: immediate electronic transmission (no DEA required)
   - Schedule II-V (controlled): print + fax fallback
   - Patient notified: "Rx will be transmitted to pharmacy by fax (slower)"
   
3. **Fax Fallback Workflow**
   ```
   1. Clinician clicks "Sign & Fax" button
   2. System generates prescription document with digital signature image
   3. Document automatically faxed to patient's pharmacy of choice
   4. Patient receives SMS: "Your prescription has been sent to [Pharmacy]. It will be ready in 1-2 hours."
   5. Pharmacy staff call clinician to verbally confirm prescription if needed
   6. Prescription status tracked: "Sent (Fax)"
   ```
   
4. **Circuit Breaker Pattern**
   - If DEA EPCS down for >30 minutes, automatically switch all Rx to fax
   - Re-enable EPCS when health check passes 3 consecutive times
   - No clinician action required; transparent to user

**Recovery** (Semi-Automatic):
```javascript
async function handleDEAEPCSOutage() {
    logger.error('DEA EPCS outage detected', {timestamp: now()});
    
    // Step 1: Notify all stakeholders
    await broadcastNotification({
        type: 'dea_epcs_outage',
        title: 'DEA EPCS Unavailable',
        message: 'Controlled substance prescriptions will be transmitted by fax.',
        targetRole: ['clinician', 'pharmacist'],
        severity: 'CRITICAL'
    });
    
    // Step 2: Set system flag: use fax fallback for all Rx
    await setSystemFlag('DEA_EPCS_FALLBACK_MODE', {
        enabled: true,
        reason: 'DEA_EPCS_UNAVAILABLE',
        timestamp: now(),
        expectedRecoveryTime: null
    });
    
    // Step 3: Update UI: hide digital signature button, show fax button
    updatePrescriptionUI({
        showDigitalSign: false,
        showFaxFallback: true,
        warningBanner: 'DEA system down. Using fax transmission.'
    });
    
    // Step 4: Start recovery loop (check every 2 minutes)
    const recoveryInterval = setInterval(async () => {
        const dea_available = await verifyDEAEPCS();
        
        if (dea_available) {
            logger.info('DEA EPCS recovered', {timestamp: now()});
            
            // Clear fallback mode
            await setSystemFlag('DEA_EPCS_FALLBACK_MODE', {enabled: false});
            
            // Restore UI
            updatePrescriptionUI({
                showDigitalSign: true,
                showFaxFallback: false,
                successMessage: 'DEA system restored. EPCS now available.'
            });
            
            // Notify users
            broadcastNotification({
                type: 'dea_epcs_recovered',
                message: 'DEA EPCS system is now available.',
                severity: 'INFO'
            });
            
            clearInterval(recoveryInterval);
        }
    }, 2 * 60 * 1000);  // Check every 2 minutes
    
    // Timeout: if not recovered after 4 hours, escalate to incident commander
    setTimeout(async () => {
        const is_still_down = !(await verifyDEAEPCS());
        
        if (is_still_down) {
            logger.error('DEA EPCS outage >4 hours; escalating', {timestamp: now()});
            
            await escalateIncident({
                severity: 'CRITICAL',
                title: 'DEA EPCS Extended Outage (>4 hours)',
                assignee: 'incident-commander@telemedicine.local',
                message: 'DEA EPCS has been unavailable for >4 hours. Manual intervention may be required.'
            });
        }
    }, 4 * 60 * 60 * 1000);  // 4 hours
}

// Automatic fax transmission when DEA down
async function handlePrescriptionSignWhenDEADown(prescriptionId) {
    const fallbackEnabled = await getSystemFlag('DEA_EPCS_FALLBACK_MODE');
    
    if (fallbackEnabled.enabled) {
        logger.info('DEA down; using fax fallback', {prescriptionId});
        
        // Generate prescription document
        const prescriptionDoc = await generatePrescriptionDocument(prescriptionId, {
            format: 'pdf',
            includingSignature: true
        });
        
        // Sign prescription in fallback mode
        await signPrescriptionFallback(prescriptionId, {
            signature_method: 'fax_based',
            signed_at: now()
        });
        
        // Get patient's preferred pharmacy
        const pharmacy = await getPatientPreferredPharmacy(prescriptionId);
        
        // Send to fax service
        const faxResult = await faxService.sendPrescription({
            documentPath: prescriptionDoc.path,
            recipientFaxNumber: pharmacy.fax_number,
            recipientName: pharmacy.name,
            prescriptionId
        });
        
        logger.info('Prescription faxed successfully', {
            prescriptionId,
            pharmacy: pharmacy.name,
            faxJobId: faxResult.jobId
        });
        
        // Update prescription status
        await updatePrescriptionStatus(prescriptionId, {
            status: 'transmitted',
            transmitted_at: now(),
            transmission_method: 'fax',
            transmission_id: faxResult.jobId
        });
        
        // Notify patient and pharmacist
        await notifyPatient(prescriptionId, {
            message: `Your prescription has been sent to ${pharmacy.name} by fax. It will be ready in 1-2 hours.`,
            actionLink: 'view_rx_status'
        });
        
        await notifyPharmacy(prescriptionId, {
            message: `Prescription received by fax from ${clinic_name}. Please contact clinician to confirm if needed.`,
            pharmacy_phone: pharmacy.phone
        });
        
        return {success: true, method: 'fax', pharmacy: pharmacy.name};
    }
}
```

**Clinician Experience During Outage**:
- Warning banner: "DEA system unavailable. Rx will be sent by fax."
- Sign button replaced with "Send by Fax" button
- Workflow same, but fax icon instead of "e-sign"
- Pharmacy receives fax within 5 minutes

**Patient Experience**:
- SMS: "Your prescription has been sent to [Pharmacy Name] by fax. It will be ready in 1-2 hours."
- Can still view Rx in patient portal
- Status shows "Sent (Fax)" instead of "Transmitted (EPCS)"
- Faster than verbal Rx, but slower than instant e-Rx

**Recovery Time**: 5-30 minutes average DEA EPCS outage; system auto-recovers

---

## Scenario 2: Pharmacy Routing Failure (Surescripts Network Down)

**Failure Mode**: Surescripts network (NCPDP hub for pharmacy e-Rx routing) is unavailable or unreachable. Prescription cannot be transmitted to pharmacy electronically.

**Symptoms**:
- Clinician sends EPCS prescription
- Transmission fails: "Pharmacy network unreachable"
- Prescription status: "Transmitted - Failed"
- Pharmacy never receives electronic Rx

**Impact** (High):
- E-Rx not delivered to pharmacy
- Patient must visit pharmacy for manual Rx or call clinician for verbal Rx
- Patient experience: "My prescription didn't come through"
- Billing delay if manual Rx printed instead of electronic

**Detection**:
```javascript
class SurescriptsClient {
    async checkSurescriptsHealth() {
        try {
            const response = await surescripts_api.ping({
                timeout: 5000
            });
            
            if (response.status === 200) {
                return {healthy: true};
            } else {
                logger.warn('Surescripts not responding normally', {
                    status: response.status
                });
                return {healthy: false, reason: 'bad_status'};
            }
        } catch (error) {
            logger.error('Surescripts unreachable', {
                error: error.message,
                timestamp: now()
            });
            
            publishEvent('surescripts_unreachable', {
                error: error.message
            }, 'HIGH');
            
            return {healthy: false, reason: 'network_error'};
        }
    }
}

// Monitor Surescripts every 30 seconds
setInterval(async () => {
    const health = await new SurescriptsClient().checkSurescriptsHealth();
    
    if (!health.healthy) {
        logger.error('Surescripts DOWN', {health, timestamp: now()});
        
        publishEvent('surescripts_outage', {
            reason: health.reason
        }, 'HIGH');
        
        broadcastNotification({
            type: 'surescripts_down',
            message: 'Pharmacy network unavailable. E-prescriptions will retry automatically.',
            severity: 'HIGH',
            targetRole: 'clinician'
        });
    }
}, 30 * 1000);
```

**Root Causes**:
1. **Surescripts infrastructure failure** (40% of cases)
   - Server outage (restart, hardware failure)
   - Database connectivity lost
   - Load balancer failure
   
2. **Network connectivity** (35% of cases)
   - BGP route failure
   - ISP connectivity between telemedicine platform and Surescripts
   - Firewall rule blocking traffic
   
3. **NCPDP protocol error** (15% of cases)
   - Malformed NCPDP D0 message (pharmacy not accepting format)
   - Wrong NCPDP header version
   - Invalid pharmacy NCPDP ID
   
4. **Rate limiting** (10% of cases)
   - Surescripts rate limit exceeded (too many Rx/min)
   - IP address temporarily throttled

**Mitigation**:
1. **Automatic Retry with Exponential Backoff**
   - Attempt 1: immediate
   - Attempt 2: 2 minutes later
   - Attempt 3: 5 minutes later
   - Attempt 4: 15 minutes later
   - Attempt 5: 1 hour later
   - Continue retrying for 24 hours
   
2. **Fax Fallback** (if EPCS retry fails after 1 hour)
   - Clinician notified: "Pharmacy network unreachable. Rx will be sent by fax instead."
   - User accepts: system initiates fax to pharmacy
   - Patient notified: status changes to "Sent (Fax)"
   
3. **Local Retry Queue**
   - Failed Rx stored in local PostgreSQL queue
   - Async worker periodically attempts retransmission
   - Exponential backoff: every 2 min, then 5 min, then 15 min, etc.

**Recovery** (Semi-Automatic):
```javascript
async function handleSurescriptsFailure(prescriptionId) {
    logger.warn('Surescripts transmission failed', {prescriptionId});
    
    // Step 1: Queue for retry
    await addToRetryQueue(prescriptionId, {
        maxRetries: 288,  // 24 hours @ 5-min interval
        nextRetryAt: now() + 2 * 60 * 1000,  // 2 minutes
        retryCount: 0,
        reason: 'surescripts_unreachable'
    });
    
    // Step 2: Notify clinician
    await publishNotification({
        type: 'prescription_transmission_failed',
        prescriptionId,
        message: 'Pharmacy network temporarily unavailable. Prescription will retry automatically.',
        actionButton: {
            label: 'Send by Fax Now',
            onClick: () => initiateFaxFallback(prescriptionId)
        }
    });
    
    // Step 3: Return to clinician with option to fax
    return {
        status: 'failed',
        retrying: true,
        suggestedAction: 'send_by_fax',
        message: 'If you want to send immediately, use the Fax button below.'
    };
}

// Async job: retry failed prescriptions
async function retryFailedPrescriptions() {
    const failedRxList = await getRetryQueue({
        status: 'pending',
        nextRetryAt_lt: now()  // Due for retry
    });
    
    for (const rx of failedRxList) {
        try {
            // Attempt transmission
            const result = await surescriptsClient.transmitPrescription(rx.id);
            
            if (result.success) {
                logger.info('Prescription retry succeeded', {
                    prescriptionId: rx.id,
                    attemptNumber: rx.retryCount + 1
                });
                
                // Mark as completed
                await removeFromRetryQueue(rx.id);
                await updatePrescriptionStatus(rx.id, {
                    status: 'transmitted',
                    transmitted_at: now()
                });
                
                // Notify clinician
                await publishNotification({
                    type: 'prescription_transmission_success',
                    prescriptionId: rx.id,
                    message: 'Prescription successfully delivered to pharmacy.'
                });
            } else {
                // Still failing; schedule next retry
                const nextBackoff = getExponentialBackoff(rx.retryCount + 1);
                
                await updateRetryQueue(rx.id, {
                    retryCount: rx.retryCount + 1,
                    nextRetryAt: now() + nextBackoff,
                    lastError: result.error
                });
                
                logger.warn('Prescription retry failed; scheduling next attempt', {
                    prescriptionId: rx.id,
                    retryCount: rx.retryCount + 1,
                    nextRetryMinutes: nextBackoff / 60000
                });
            }
        } catch (error) {
            logger.error('Prescription retry threw error', {
                prescriptionId: rx.id,
                error: error.message
            });
            
            // Increment retry count and continue
            await updateRetryQueue(rx.id, {
                retryCount: rx.retryCount + 1,
                nextRetryAt: now() + getExponentialBackoff(rx.retryCount + 1)
            });
        }
    }
}

function getExponentialBackoff(attemptNumber) {
    const backoffs = [
        2 * 60 * 1000,      // Attempt 2: 2 min
        5 * 60 * 1000,      // Attempt 3: 5 min
        15 * 60 * 1000,     // Attempt 4: 15 min
        60 * 60 * 1000,     // Attempt 5: 1 hour
        2 * 60 * 60 * 1000, // Attempt 6+: 2 hours
    ];
    
    return backoffs[Math.min(attemptNumber - 2, backoffs.length - 1)];
}

// Run retry job every 5 minutes
setInterval(retryFailedPrescriptions, 5 * 60 * 1000);
```

**Clinician Experience**:
- Transmission failure shows with "Retry" status
- Option to immediately fax if urgent
- Or wait for automatic retry (transparent)
- Status updates when Surescripts recovers

**Patient Experience**:
- If automatic retry succeeds: SMS "Your prescription is ready at [Pharmacy]"
- If manual fax needed: SMS "Your prescription was sent by fax to [Pharmacy]"
- No negative experience if retry succeeds within 30 minutes

**Recovery Time**: Automatic retries within 24 hours; or manual fax within 5 minutes

---

## Scenario 3: PDMP Query Timeout

**Failure Mode**: State PDMP (Prescription Drug Monitoring Program) database is slow or unresponsive. PDMP query times out (>30 seconds) and cannot complete before prescription signing deadline.

**Symptoms**:
- Clinician attempts to sign controlled substance Rx
- PDMP check in progress... (spinner)
- After 30 seconds: timeout
- Error: "Unable to verify patient prescription history. Please try again."

**Impact** (High):
- Controlled substance Rx cannot be signed
- Clinician must manually verify PDMP (phone call to state agency) or wait
- Delays prescription signing by 5-30 minutes
- Patient waits for medication

**Detection**:
```javascript
class PDMPQueryService {
    async queryPatientHistoryWithTimeout(patientId, state) {
        return new Promise((resolve, reject) => {
            const timeoutHandle = setTimeout(() => {
                logger.warn('PDMP query timeout', {
                    patientId,
                    state,
                    timestamp: now()
                });
                
                publishEvent('pdmp_query_timeout', {
                    patientId,
                    state
                }, 'HIGH');
                
                reject(new Error('PDMP_QUERY_TIMEOUT'));
            }, 30 * 1000);  // 30-second timeout
            
            this.queryStateDatabase(patientId, state)
                .then(result => {
                    clearTimeout(timeoutHandle);
                    resolve(result);
                })
                .catch(error => {
                    clearTimeout(timeoutHandle);
                    reject(error);
                });
        });
    }
}
```

**Root Causes**:
1. **State PDMP database slow** (50% of cases)
   - High query volume
   - Database query plan inefficiency
   - Indexing issue
   - Disk I/O bottleneck
   
2. **Network latency** (30% of cases)
   - State agency network congestion
   - BGP routing inefficiency
   - Geographic distance (NY querying CA PDMP)
   
3. **State PDMP API maintenance** (15% of cases)
   - Scheduled downtime
   - Database maintenance window
   - Version rollout
   
4. **Authentication failure** (5% of cases)
   - DEA credentials expired
   - API key revoked
   - Certificate validation failure

**Mitigation**:
1. **PDMP Result Caching** (48-hour TTL)
   - Cache PDMP result after successful query
   - Reuse cache for same patient within 48 hours (state-dependent)
   - Refresh cache on next prescription for same patient
   
2. **Query Timeout Handling**
   - Timeout: 30 seconds (strict)
   - Return cached result if <48h old
   - If no cache: allow clinician manual override (requires documentation)
   
3. **Fallback Verification**
   - If PDMP times out: offer manual verification options
     - Phone call to state PDMP agency (5-10 min)
     - Use PDMP portal (web) directly (5-15 min)
   - Clinician documents reason for delay

```javascript
async function handlePDMPTimeout(patientId, state) {
    logger.warn('PDMP query timed out', {patientId, state});
    
    // Step 1: Check cache
    const cachedResult = await pdmpCache.get(`pdmp:${state}:${patientId}`);
    
    if (cachedResult && cachedResult.age_hours < 48) {
        logger.info('Using cached PDMP result', {
            patientId,
            state,
            cacheAge: cachedResult.age_hours
        });
        
        // Use cached result with warning
        return {
            result: cachedResult,
            source: 'cache',
            warning: `PDMP check used cached result (${Math.round(cachedResult.age_hours)} hours old). Recent changes may not be reflected.`,
            requiresManualRefresh: cachedResult.age_hours > 24
        };
    }
    
    // Step 2: No cache; show manual verification options
    return {
        error: 'PDMP_TIMEOUT',
        fallbackOptions: [
            {
                method: 'manual_phone',
                description: 'Call state PDMP agency directly',
                phoneNumber: getPDMPPhoneNumber(state),
                estimatedTime: '5-10 minutes',
                requiresDocumentation: true
            },
            {
                method: 'web_portal',
                description: 'Use state PDMP web portal',
                url: getPDMPWebPortal(state),
                estimatedTime: '5-15 minutes',
                requiresDocumentation: true
            },
            {
                method: 'retry_query',
                description: 'Retry PDMP query',
                estimatedTime: '30 seconds',
                requiresDocumentation: false
            }
        ],
        message: 'PDMP check timed out. Please verify patient history using one of the options above before signing controlled substance prescription.'
    };
}
```

**Clinician Experience**:
- If cache available: "Using cached check (1 hour old). Warnings displayed."
- If no cache: options to retry, call state PDMP, or use web portal
- Clinician documents choice in prescription notes
- Continues after verification selected

**Patient Experience**:
- No direct impact; happens behind scenes
- Possible 5-15 minute delay if manual verification needed

**Recovery Time**: 30 seconds (cached); or 5-15 minutes (manual verification)

---

## Scenario 4: Drug-Drug Interaction Alert Dismissed by Clinician

**Failure Mode**: System detects severe drug-drug interaction (e.g., opioid + benzodiazepine = respiratory depression risk). Clinician reviews alert and clicks "Override - I am aware of interaction" without documented clinical justification.

**Symptoms**:
- Drug interaction alert displays
- Alert severity: "SEVERE - Respiratory depression risk"
- Clinician clicks "Override"
- Prescription signed and transmitted despite interaction

**Impact** (Critical):
- Patient receives potentially harmful medication combination
- Risk of overdose, respiratory depression, death
- Liability: malpractice claim if adverse event occurs
- Regulatory: HIPAA violation if alert not properly documented
- Compliance: state pharmacy board violation

**Detection & Prevention**:
```javascript
async function checkDrugInteractions(
    newMedicationRxNormCode,
    patientId,
    consultationId
) {
    // Get patient's current medications from EHR
    const currentMedications = await getPatientMedications(patientId, {
        active: true
    });
    
    // Query RxNorm interaction API
    const interactions = await rxNormClient.checkInteractions({
        drugCode: newMedicationRxNormCode,
        otherDrugs: currentMedications.map(m => m.rxnormCode)
    });
    
    // Filter by severity
    const severeInteractions = interactions.filter(i => 
        ['SEVERE', 'MAJOR'].includes(i.severity)
    );
    
    if (severeInteractions.length > 0) {
        logger.warn('Severe drug interaction detected', {
            patientId,
            newMedication: newMedicationRxNormCode,
            interactions: severeInteractions,
            timestamp: now()
        });
        
        // Display alert and require explicit override
        return {
            hasInteraction: true,
            severity: 'SEVERE',
            interactions: severeInteractions,
            requiresOverride: true,
            requiresDocumentation: true
        };
    }
    
    return {hasInteraction: false};
}

async function overrideDrugInteractionAlert(
    prescriptionId,
    clinicianId,
    clinicianJustification
) {
    // MANDATORY: Clinician must provide clinical justification
    if (!clinicianJustification || clinicianJustification.trim().length < 50) {
        throw new Error(
            'Justification required (minimum 50 characters). ' +
            'Example: "Patient requires opioid for severe pain; closely monitoring; ' +
            'will schedule 48-hour follow-up call"'
        );
    }
    
    logger.warn('Drug interaction override', {
        prescriptionId,
        clinicianId,
        justification: clinicianJustification,
        timestamp: now()
    });
    
    // Mandatory audit log
    await auditLog('drug_interaction_override', {
        prescriptionId,
        clinicianId,
        justification: clinicianJustification,
        timestamp: now(),
        phi_accessed: false,  // Non-PHI event
        action: 'override_interaction_alert'
    });
    
    // Alert compliance team if severe interaction
    await publishEvent('drug_interaction_override', {
        prescriptionId,
        severity: 'SEVERE',
        clinician: clinicianId,
        requiresReview: true
    }, 'HIGH');
    
    // Add note to patient chart
    await addChartNote({
        patientId: prescription.patientId,
        type: 'clinical_alert_override',
        text: `Clinician overrode drug-drug interaction alert: ${clinicianJustification}`,
        createdBy: clinicianId
    });
}
```

**Mitigation**:
1. **Mandatory Justification** (≥50 characters)
   - Free-form clinical notes required
   - Examples provided: "Patient monitoring plan", "Benefit outweighs risk", etc.
   
2. **Compliance Review** (asynchronous)
   - All severe overrides reviewed within 24 hours by compliance officer
   - Red flags: no justification, suspicious pattern, repeated overrides
   - Flag for peer review if >5 overrides per week
   
3. **Patient Safety Alert** (optional)
   - System can notify patient: "Your medications may interact"
   - Include pharmacy contact info for verification
   
4. **Pharmacist Review** (at point of dispensing)
   - Pharmacy receives alert about overridden interaction
   - Pharmacist contacts clinician if concerned
   - Second-opinion check before dispensing

**Recovery**:
```javascript
async function reviewDrugInteractionOverride(prescriptionId) {
    const prescription = await getPrescription(prescriptionId);
    const override = await getOverrideJustification(prescriptionId);
    
    // Assess clinician's justification quality
    const assessmentScore = assessJustificationQuality({
        text: override.justification,
        length: override.justification.length,
        keywords: [
            'monitoring', 'follow-up', 'benefit', 'risk', 'contraindication',
            'adjusted dose', 'alternative', 'patient aware'
        ]
    });
    
    if (assessmentScore < 5) {
        // Poor justification; flag for investigation
        logger.warn('Poor drug interaction override justification', {
            prescriptionId,
            clinicianId: prescription.clinicianId,
            score: assessmentScore,
            justification: override.justification
        });
        
        await createComplianceTicket({
            type: 'poor_drug_interaction_justification',
            prescriptionId,
            priority: 'medium',
            assignee: 'compliance-officer',
            description: `Clinician override of drug-drug interaction with weak justification: "${override.justification}"`
        });
    }
    
    // Check for pattern of overrides by same clinician
    const recentOverrides = await getRecentOverridesByclinician(
        prescription.clinicianId,
        {days: 7}
    );
    
    if (recentOverrides.length > 5) {
        logger.error('Clinician overriding interactions too frequently', {
            clinicianId: prescription.clinicianId,
            overrideCount: recentOverrides.length,
            period: '7 days'
        });
        
        await createComplianceTicket({
            type: 'excessive_interaction_overrides',
            clinicianId: prescription.clinicianId,
            priority: 'high',
            assignee: 'chief-medical-officer',
            description: `Clinician ${prescription.clinicianId} has overridden drug-drug interactions ${recentOverrides.length} times in 7 days. Pattern review recommended.`
        });
    }
}

// Daily compliance review job
async function reviewDrugInteractionOverridesDaily() {
    const overridesFrom24hAgo = await getRecentOverrides({
        days: 1
    });
    
    for (const override of overridesFrom24hAgo) {
        await reviewDrugInteractionOverride(override.prescriptionId);
    }
}
```

**Regulatory Compliance**:
- Override justification stored indefinitely (HIPAA record retention)
- Accessible to pharmacy boards, DEA audits, malpractice defense
- Patient can access justification via right-of-access request

**Patient Safety Culture**:
- Goal: NOT to block care, but to ensure thoughtful clinical decision-making
- Override available when clinically appropriate
- Proper documentation creates safety net and legal protection

---

## Scenario 5: Duplicate Prescription Across Platforms

**Failure Mode**: Patient receives the same prescription twice from two different telemedicine platforms or clinicians (e.g., different clinics offering telehealth). Prescription transmitted to same pharmacy twice; patient picks up two supplies (potential opioid diversion, adverse outcomes).

**Symptoms**:
- Patient uses Telemedicine Platform A on Monday (gets opioid Rx)
- Patient uses different provider via Telemedicine Platform B on Tuesday (gets same opioid Rx)
- Both transmitted to same pharmacy
- Pharmacy fills both; patient receives 2x medication

**Impact** (Critical):
- Patient safety: opioid overdose risk if patient takes both supplies
- Fraud: potential controlled substance diversion
- Regulatory: PDMP violation (duplicate prescriptions not detected)
- Pharmacy liability: filled duplicate Rx without catching error

**Detection**:
```javascript
async function detectDuplicatePrescription(prescriptionData) {
    // Check patient's recent Rx history (all platforms)
    const recentRxs = await queryPatientRxHistory(prescriptionData.patientId, {
        days: 30,
        medications: [prescriptionData.medication_name],
        status: ['transmitted', 'dispensed']
    });
    
    // Check for exact duplicates
    const exactDuplicates = recentRxs.filter(rx =>
        rx.medication_name === prescriptionData.medication_name &&
        rx.dosage === prescriptionData.dosage &&
        rx.quantity === prescriptionData.quantity &&
        rx.prescriber_dea !== prescriptionData.prescriber_dea &&  // Different prescriber
        daysBetween(rx.transmitted_at, now()) < 7  // Within 7 days
    );
    
    if (exactDuplicates.length > 0) {
        logger.error('Duplicate prescription detected', {
            patientId: prescriptionData.patientId,
            medication: prescriptionData.medication_name,
            duplicateCount: exactDuplicates.length,
            recentRx: exactDuplicates[0]
        });
        
        publishEvent('duplicate_prescription_detected', {
            patientId: prescriptionData.patientId,
            prescriptionId: prescriptionData.id,
            duplicateRxId: exactDuplicates[0].id,
            severity: 'CRITICAL'
        }, 'CRITICAL');
        
        return {
            isDuplicate: true,
            duplicateRxId: exactDuplicates[0].id,
            duplicatePrescriber: exactDuplicates[0].prescriber_name,
            duplicateDate: exactDuplicates[0].transmitted_at
        };
    }
    
    // Check for similar (same medication, same quantity, different dosage)
    const similarRxs = recentRxs.filter(rx =>
        rx.medication_name === prescriptionData.medication_name &&
        rx.quantity === prescriptionData.quantity &&
        daysBetween(rx.transmitted_at, now()) < 7
    );
    
    if (similarRxs.length > 0) {
        logger.warn('Similar prescription detected', {
            patientId: prescriptionData.patientId,
            medication: prescriptionData.medication_name,
            similarCount: similarRxs.length
        });
        
        publishEvent('similar_prescription_detected', {
            patientId: prescriptionData.patientId,
            prescriptionId: prescriptionData.id,
            severity: 'MEDIUM'
        }, 'MEDIUM');
        
        return {
            isDuplicate: false,
            isSimilar: true,
            similarRxs: similarRxs
        };
    }
    
    return {isDuplicate: false, isSimilar: false};
}

// Run check before transmission
async function transmitPrescriptionWithDupCheck(prescriptionId) {
    const prescription = await getPrescription(prescriptionId);
    
    // Check for duplicates
    const dupCheck = await detectDuplicatePrescription(prescription);
    
    if (dupCheck.isDuplicate) {
        // Block transmission
        logger.error('Prescription transmission blocked - duplicate detected', {
            prescriptionId,
            duplicateRx: dupCheck.duplicateRxId
        });
        
        return {
            status: 'failed',
            reason: 'duplicate_prescription',
            message: `A similar prescription for ${prescription.medication_name} was issued to this patient on ${formatDate(dupCheck.duplicateDate)} by Dr. ${dupCheck.duplicatePrescriber}. Please verify with patient before transmitting.`,
            actionRequired: true,
            suggestedActions: [
                'Contact patient to confirm need for duplicate',
                'Contact previous prescriber to verify',
                'Cancel duplicate and use existing Rx'
            ]
        };
    }
    
    if (dupCheck.isSimilar) {
        // Warn clinician but allow override
        return {
            status: 'warning',
            reason: 'similar_prescription',
            message: `Similar prescriptions exist for ${prescription.medication_name}:
                ${dupCheck.similarRxs.map(rx => `• ${rx.dosage} on ${formatDate(rx.transmitted_at)}`).join('\n')}
            Please confirm this prescription is not a duplicate.`,
            requiresConfirmation: true,
            showConfirmationDialog: {
                title: 'Confirm Prescription',
                message: 'This prescription is similar to recent ones. Proceed anyway?',
                buttons: ['Cancel', 'Confirm & Transmit']
            }
        };
    }
    
    // No duplicates; proceed with transmission
    return await transmitToPharmacy(prescriptionId);
}
```

**Pharmacy-Side Detection**:
```javascript
// Pharmacy Point of Dispensing (integrated with pharmacy system)
async function checkPharmacyForDuplicates(rxNumber, patientId, medication) {
    // Query pharmacy's recent fills
    const recentFills = await pharmacyDB.query(
        `SELECT * FROM fills WHERE patient_id = $1 AND medication_name = $2
         AND fill_date > NOW() - INTERVAL '14 days'`,
        [patientId, medication]
    );
    
    if (recentFills.length > 0) {
        logger.warn('Duplicate Rx filled at pharmacy', {
            rxNumber,
            patientId,
            medication,
            previousFillDate: recentFills[0].fill_date,
            pharmacyId: recentFills[0].pharmacy_id
        });
        
        // Flag for pharmacist review
        return {
            isDuplicate: true,
            previousFill: recentFills[0],
            requiresPharmacistApproval: true
        };
    }
    
    return {isDuplicate: false};
}
```

**Prevention Mitigation**:
1. **Clinician check before transmission** (automated)
   - Query patient's recent Rx history across platform
   - Block exact duplicates with strong warning
   - Allow similar with confirmation
   
2. **Pharmacy check at dispensing** (manual gate)
   - Pharmacist reviews Rx for known duplicates
   - Calls patient if duplicate found
   - Verifies medical necessity
   
3. **Cross-Platform Sharing** (future)
   - PDMP integration (some states track all Rx)
   - Universal patient ID (eventual solution)
   - Interoperability standards (FHIR)

**Recovery**:
- If duplicate already dispensed: contact patient immediately
- Verify patient has not taken duplicate medication
- If taken: emergency room assessment for overdose
- Report incident to state pharmacy board
- Insurance claim reversal for duplicate fill

---

## Scenario 6: Prescription Expiry During Pharmacy Queue Delay

**Failure Mode**: Prescription issued and transmitted to pharmacy, but pharmacy's queue is backed up. Prescription reaches top of queue after it expires (usually 365 days from signing, or state-specific shorter period). Pharmacy cannot fill expired Rx.

**Symptoms**:
- Prescription transmitted: "Successfully sent to pharmacy"
- Pharmacy queue backed up (waiting 3-7 days to fill Rx)
- After 6-7 days: prescription expires
- Patient calls pharmacy: "Your prescription expired. Contact your doctor for new one."

**Impact** (Medium-High):
- Patient must contact clinician for new Rx
- Delays medication pickup by 1-2 days
- Patient frustration; perception of system failure
- More likely to occur with non-urgent chronic Rx (lower pharmacy priority)

**Detection & Prevention**:
```javascript
async function calculatePrescriptionExpiry(prescriptionSignedAt, state) {
    // Default: 365 days from signing
    let expiryDays = 365;
    
    // State-specific expirations (some states shorter)
    const stateExpirations = {
        'CA': 180,  // California: 180 days
        'NY': 365,  // New York: 1 year
        'TX': 365,  // Texas: 1 year
        'MA': 365   // Massachusetts: 1 year
    };
    
    expiryDays = stateExpirations[state] || 365;
    
    const expiryDate = addDays(prescriptionSignedAt, expiryDays);
    const daysRemaining = daysBetween(now(), expiryDate);
    
    return {
        expiryDate,
        daysRemaining,
        expirationWarning: daysRemaining < 7
    };
}

async function monitorPrescriptionExpiryRisk(prescriptionId) {
    const prescription = await getPrescription(prescriptionId);
    const {expiryDate, daysRemaining} = await calculatePrescriptionExpiry(
        prescription.signed_at,
        prescription.patientState
    );
    
    if (daysRemaining < 7 && prescription.status === 'transmitted') {
        logger.warn('Prescription near expiry', {
            prescriptionId,
            daysRemaining,
            expiryDate,
            pharmacy: prescription.pharmacy_name
        });
        
        // Notify pharmacy to prioritize filling
        await notifyPharmacy(prescriptionId, {
            type: 'urgent_fill_request',
            message: `Prescription expiring in ${daysRemaining} days. Please prioritize filling.`,
            expiryDate
        });
        
        // Notify patient
        await notifyPatient(prescriptionId, {
            type: 'prescription_expiry_warning',
            message: `Your prescription expires in ${daysRemaining} days. Pick it up soon!`,
            expiryDate
        });
        
        publishEvent('prescription_expiry_risk', {
            prescriptionId,
            daysRemaining,
            severity: 'MEDIUM'
        }, 'MEDIUM');
    }
}

// Scheduled job: check prescriptions daily
async function checkPrescriptionExpiries() {
    const transmittedRxs = await getPrescriptions({
        status: 'transmitted',
        expiry_check_pending: true
    });
    
    for (const rx of transmittedRxs) {
        await monitorPrescriptionExpiryRisk(rx.id);
    }
}
```

**Mitigation**:
1. **Pharmacy Prioritization**
   - System alerts pharmacy when Rx issued
   - Priority indicator: normal, high, urgent
   - Flag Rx expiring soon for faster processing
   
2. **Automatic Re-Sign**
   - If Rx expires before filled, automatically route renewal to clinician
   - One-click renewal available to clinician
   - Patient notified: "New prescription sent to pharmacy"
   
3. **Extended Validity for Certain Meds**
   - Chronic medications (blood pressure, diabetes): 2-3 year validity
   - Acute (antibiotics): standard 365 days
   - Controlled substances: always 365 days max

**Recovery**:
```javascript
async function handleExpiredPrescription(prescriptionId) {
    const prescription = await getPrescription(prescriptionId);
    
    logger.warn('Prescription expired before dispensing', {
        prescriptionId,
        medication: prescription.medication_name,
        patientId: prescription.patientId,
        expiryDate: prescription.expiry_date
    });
    
    // Step 1: Check if auto-renewal possible
    const isAutoRenewable = prescription.refills_allowed > 0 && 
                           !prescription.dea_schedule;  // No auto-renew for controlled
    
    if (isAutoRenewable) {
        // Create renewal prescription automatically
        const renewalRx = await createRenewalPrescription(prescriptionId);
        
        // Transmit immediately
        await transmitToPharmacy(renewalRx.id);
        
        logger.info('Prescription auto-renewed', {
            originalId: prescriptionId,
            renewalId: renewalRx.id
        });
        
        // Notify parties
        await notifyPatient(prescriptionId, {
            message: 'Your expired prescription was automatically renewed and sent to pharmacy.'
        });
        
        await notifyPharmacy(renewalRx.id, {
            message: 'Auto-renewal of expired prescription. Patient can pick up immediately.'
        });
        
    } else {
        // Manual renewal required
        logger.info('Prescription renewal required (manual)', {
            prescriptionId,
            reason: isAutoRenewable ? 'refills_exhausted' : 'controlled_substance'
        });
        
        // Create pending renewal for clinician
        await createPendingRenewalRequest(prescriptionId, {
            reason: 'prescription_expired',
            patient_notification_sent: false,
            clinician_notification_sent: false
        });
        
        // Notify patient
        await notifyPatient(prescriptionId, {
            type: 'prescription_needs_renewal',
            message: `Your prescription expired. Contact your clinician for a new one. We'll notify them now.`,
            actionLink: 'request_renewal'
        });
        
        // Notify clinician
        await notifyClinicianWithRenewalRequest(prescription.clinician_id, {
            patientId: prescription.patientId,
            medication: prescription.medication_name,
            reason: 'expired_before_dispensing',
            patientAlreadyNotified: true
        });
    }
}
```

---

## Scenario 7: Fax Fallback Failure for Non-EPCS Pharmacy

**Failure Mode**: Prescription cannot be sent via EPCS (e.g., DEA down, pharmacy not EPCS-equipped). System attempts fax fallback, but fax transmission fails (number invalid, line busy, document unreadable).

**Symptoms**:
- Clinician clicks "Send by Fax"
- Fax attempts to send
- After 3 minutes: "Fax failed to send"
- Error: "Unable to deliver. Check pharmacy fax number."

**Impact** (High):
- Prescription stuck; cannot be filled
- Patient waiting at pharmacy or without medication
- Requires clinician to manually intervene (call pharmacy, resend fax)
- More common with small, rural pharmacies (older fax systems)

**Detection**:
```javascript
async function sendPrescriptionByFax(prescriptionId, pharmacyFaxNumber) {
    const prescription = await getPrescription(prescriptionId);
    
    // Generate prescription document (PDF with signature)
    const pdfDocument = await generatePrescriptionPDF(prescriptionId, {
        signatureFormat: 'image',
        watermark: 'TRANSMITTED BY FAX'
    });
    
    logger.info('Sending prescription by fax', {
        prescriptionId,
        pharmacyFax: maskFaxNumber(pharmacyFaxNumber),
        documentPages: pdfDocument.pageCount
    });
    
    try {
        // Send via fax service (Twilio, RightFax, etc.)
        const faxResult = await faxService.send({
            toNumber: pharmacyFaxNumber,
            documentPath: pdfDocument.path,
            accountCode: prescription.clinician_id,
            metadata: {
                prescriptionId,
                patientName: prescription.patientName,
                medication: prescription.medication_name
            },
            maxRetries: 3,
            retryDelaySeconds: 300  // 5 minutes between retries
        });
        
        if (faxResult.status === 'success') {
            logger.info('Prescription fax transmitted successfully', {
                prescriptionId,
                faxJobId: faxResult.jobId,
                pages: faxResult.pagesTransmitted
            });
            
            // Update prescription
            await updatePrescriptionStatus(prescriptionId, {
                status: 'transmitted',
                transmitted_at: now(),
                transmission_method: 'fax',
                transmission_id: faxResult.jobId,
                fax_number: pharmacyFaxNumber
            });
            
            // Notify parties
            await notifyPharmacy(prescriptionId, {
                type: 'fax_received',
                message: `Prescription received by fax. Patient: ${prescription.patientName}`,
                contactInfo: prescription.clinician_phone
            });
            
            return {status: 'success', jobId: faxResult.jobId};
            
        } else {
            // Fax transmission failed
            logger.error('Prescription fax transmission failed', {
                prescriptionId,
                reason: faxResult.reason,
                errorCode: faxResult.errorCode,
                retryCount: faxResult.retryCount
            });
            
            publishEvent('fax_transmission_failed', {
                prescriptionId,
                pharmacy: prescription.pharmacy_name,
                errorCode: faxResult.errorCode
            }, 'HIGH');
            
            return {
                status: 'failed',
                reason: faxResult.reason,
                errorCode: faxResult.errorCode,
                suggestedActions: [
                    'Verify pharmacy fax number',
                    'Call pharmacy to confirm fax receipt',
                    'Manually print and fax from office',
                    'Contact fax service support'
                ]
            };
        }
        
    } catch (error) {
        logger.error('Fax service error', {
            prescriptionId,
            error: error.message,
            errorCode: error.code
        });
        
        return {
            status: 'error',
            error: error.message,
            suggestedAction: 'contact_support'
        };
    }
}
```

**Root Causes**:
1. **Invalid fax number** (30% of cases)
   - Pharmacy changed number; database not updated
   - Typo in fax number
   - Number disconnected
   
2. **Fax line busy** (25% of cases)
   - Pharmacy receiving other faxes
   - Old fax machine (no queuing)
   - Pharmacy closed (no fax server)
   
3. **Document quality** (20% of cases)
   - PDF too large or corrupted
   - Image quality poor; fax cannot read
   - Signature image not visible
   
4. **Fax service failure** (15% of cases)
   - Twilio/RightFax service down
   - Rate limiting
   - Account issue (insufficient credits)
   
5. **Other** (10% of cases)
   - Pharmacy fax machine broken
   - Pharmacy fax paper out
   - Network connectivity at pharmacy

**Mitigation**:
1. **Fax Number Validation**
   - Verify pharmacy fax number before sending
   - Prompt clinician if number seems unusual
   - Maintain pharmacy directory with verified numbers
   
2. **Retry Logic**
   - Automatic retry (Attempt 1: immediate, Attempt 2: 5 min, Attempt 3: 10 min)
   - Alert clinician after 3 failed attempts
   
3. **Fallback Options**
   - If fax fails: offer phone call option
   - Clinician verbally reads Rx to pharmacy
   - Pharmacy confirms and documents verbal Rx
   
4. **Pharmacy Confirmation**
   - Ask clinician to call pharmacy to confirm receipt
   - 2-factor verification for critical Rx

```javascript
async function handleFaxTransmissionFailure(prescriptionId, faxResult) {
    const prescription = await getPrescription(prescriptionId);
    
    logger.error('Fax transmission failed; initiating recovery', {
        prescriptionId,
        reason: faxResult.reason,
        errorCode: faxResult.errorCode
    });
    
    // Step 1: Show clinician action items
    const actionItems = [];
    
    if (faxResult.errorCode === 'INVALID_FAXNUMBER') {
        actionItems.push({
            action: 'verify_fax',
            title: 'Verify Pharmacy Fax Number',
            description: `The fax number ${maskFaxNumber(prescription.fax_number)} may be incorrect. Please verify with pharmacy.`,
            input: 'new_fax_number',
            onConfirm: async (newNumber) => {
                prescription.fax_number = newNumber;
                await retryFaxTransmission(prescriptionId);
            }
        });
    }
    
    if (faxResult.errorCode === 'FAX_BUSY' || faxResult.errorCode === 'NO_ANSWER') {
        actionItems.push({
            action: 'retry_fax',
            title: 'Retry Fax Transmission',
            description: 'The pharmacy fax line was busy. Retry in 5 minutes.',
            button: {label: 'Retry Now', onClick: () => retryFaxTransmission(prescriptionId)},
            autoRetry: {after: 5 * 60 * 1000}
        });
    }
    
    actionItems.push({
        action: 'call_pharmacy',
        title: 'Call Pharmacy',
        description: `Call ${prescription.pharmacy_name} at ${prescription.pharmacy_phone} to confirm verbal Rx transmission.`,
        button: {
            label: 'Call Now',
            onClick: () => initiatePhoneCall(prescription.pharmacy_phone)
        }
    });
    
    actionItems.push({
        action: 'manual_print_fax',
        title: 'Manual Print & Fax',
        description: 'Print prescription and manually fax from office.',
        button: {label: 'Print', onClick: () => printPrescription(prescriptionId)}
    });
    
    // Show clinician action panel
    showPrescriptionActionPanel({
        prescriptionId,
        title: 'Fax Transmission Failed',
        message: `Failed to fax ${prescription.medication_name} to ${prescription.pharmacy_name}. Please take action below.`,
        actions: actionItems,
        priorityBadge: 'urgent'
    });
    
    // Step 2: Notify patient
    await notifyPatient(prescriptionId, {
        type: 'prescription_transmission_issue',
        message: `There was an issue sending your prescription to the pharmacy. Your clinician has been notified and will resolve it shortly.`,
        estimatedResolution: '5-15 minutes'
    });
    
    // Step 3: Set timeout for escalation
    setTimeout(async () => {
        const latestStatus = await getPrescriptionStatus(prescriptionId);
        
        if (latestStatus.status !== 'transmitted') {
            logger.error('Fax failure unresolved after 30 minutes; escalating', {
                prescriptionId
            });
            
            await publishEvent('fax_failure_escalated', {
                prescriptionId,
                actionTimeoutMinutes: 30
            }, 'CRITICAL');
            
            // Alert support team
            await sendAlert({
                to: 'support@telemedicine.local',
                subject: `FAX FAILURE: ${prescription.medication_name} for ${prescription.patientName}`,
                body: `Prescription fax transmission failed and has not been manually resolved for 30 minutes. Manual intervention may be needed.`,
                severity: 'CRITICAL'
            });
        }
    }, 30 * 60 * 1000);  // 30 minutes
}

async function retryFaxTransmission(prescriptionId, maxRetries = 3) {
    const prescription = await getPrescription(prescriptionId);
    let attempt = prescription.fax_retry_count || 0;
    
    if (attempt >= maxRetries) {
        logger.error('Max fax retries exceeded', {prescriptionId, attempt});
        return {
            status: 'failed',
            message: 'Maximum fax retry attempts exceeded. Please contact pharmacy or use alternate method.'
        };
    }
    
    attempt++;
    logger.info('Retrying fax transmission', {prescriptionId, attempt});
    
    const faxResult = await sendPrescriptionByFax(
        prescriptionId,
        prescription.fax_number
    );
    
    // Update retry count
    await updatePrescription(prescriptionId, {
        fax_retry_count: attempt,
        last_fax_attempt_at: now()
    });
    
    return faxResult;
}
```

**Clinician Experience**:
- After fax failure: modal with action items
- Quick links to call pharmacy, print, retry
- 5-minute auto-retry with progress update
- Escalation alert if unresolved after 30 minutes

**Patient Experience**:
- SMS notification: "There was an issue sending your prescription. Your clinician is working on it."
- Estimated resolution: 5-15 minutes
- Follow-up SMS when resolved

**Recovery Time**: 5-30 minutes (with clinician action); escalation at 30 min
