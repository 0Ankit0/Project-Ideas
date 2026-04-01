# Telemedicine Platform: API & UI Integration Edge Cases

This document covers critical failure scenarios in API integrations, SDK failures, and user interface issues that degrade service or block patient/clinician workflows.

---

## Scenario 1: AWS Chime SDK Regional Outage

**Failure Mode**: AWS Chime service in patient's or clinician's region becomes unavailable. Video SDK cannot initialize; peer connection fails.

**Symptoms**:
- Patient opens consultation; video area blank
- Error: "Chime service unavailable in your region"
- No video stream possible; audio may fallback to phone

**Impact** (Critical):
- All video consultations in affected region blocked
- Fallback to audio-only (reduced revenue, poor UX)
- Potential appointment cancellations

**Detection**:
```javascript
async function detectChimeOutage() {
    const chimeRegions = ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1'];
    const downRegions = [];
    
    for (const region of chimeRegions) {
        try {
            const response = await chimeSDK.createMeeting({region, timeout: 5000});
            
            if (!response.success) {
                downRegions.push(region);
            }
        } catch (error) {
            downRegions.push(region);
            logger.error('Chime region down', {region, error});
        }
    }
    
    if (downRegions.length > 0) {
        publishEvent('chime_outage', {
            downRegions,
            severity: downRegions.length > 2 ? 'CRITICAL' : 'HIGH'
        }, downRegions.length > 2 ? 'CRITICAL' : 'HIGH');
        
        // Activate regional failover
        await activateChimeFailover(downRegions);
    }
}

async function activateChimeFailover(downRegions) {
    // Route all new appointments to healthy region
    // Reschedule appointments in down region
    logger.warn('Chime failover activated', {downRegions});
    
    const appointmentsAffected = await getAppointmentsInRegions(downRegions, {
        status: 'confirmed',
        scheduledFor: 'next_7_days'
    });
    
    for (const appointment of appointmentsAffected) {
        await notifyAppointmentAffected({
            appointmentId: appointment.id,
            patientId: appointment.patientId,
            clinicianId: appointment.clinicianId,
            reason: 'regional_infrastructure_outage',
            actionRequired: 'reschedule_to_healthy_region'
        });
    }
}
```

---

## Scenario 2: EHR Integration Timeout

**Failure Mode**: Epic FHIR API call to retrieve patient demographics times out (>30 seconds). Appointment cannot proceed without EHR data.

**Symptoms**:
- Clinician clicks "Load Patient Chart"
- Spinner rotates for 30+ seconds
- Error: "EHR system not responding"

**Impact** (High):
- Consultation delayed
- Clinician waiting; frustration
- Time-sensitive consultations may be cancelled

**Detection & Mitigation**:
```javascript
async function queryEHRWithTimeout(patientMRN, timeout = 30000) {
    try {
        const response = await ehrFhirClient.searchPatient({
            mrn: patientMRN,
            includeResources: ['medication', 'condition', 'observation'],
            timeout
        });
        
        return response;
        
    } catch (error) {
        if (error.code === 'TIMEOUT') {
            logger.error('EHR query timeout', {patientMRN});
            
            // Fallback: use cached EHR data
            const cachedData = await cacheLayer.get(`ehr:${patientMRN}`);
            
            if (cachedData && daysBetween(cachedData.cachedAt, now()) < 7) {
                logger.warn('Using cached EHR data due to timeout', {
                    patientMRN,
                    cacheAge: daysBetween(cachedData.cachedAt, now())
                });
                
                return {
                    success: true,
                    data: cachedData.data,
                    warning: 'Data may be stale (cache age: ' + daysBetween(cachedData.cachedAt, now()) + ' days)'
                };
            }
            
            // No cache; allow consultation to proceed without EHR data
            logger.warn('EHR unavailable; consultation proceeding without chart', {
                patientMRN
            });
            
            return {
                success: false,
                reason: 'ehr_timeout',
                fallback: true,
                message: 'EHR data unavailable. Consultation may proceed without chart.'
            };
        }
        
        throw error;
    }
}
```

**Mitigation Options**:
1. Cache EHR data after every successful query (TTL: 7 days)
2. Increase timeout incrementally (30s → 45s → 60s with exponential backoff)
3. Allow consultation to proceed without EHR chart (risky; flag clinician)
4. Offer offline mode: clinician uses last-known EHR data

---

## Scenario 3: Insurance Eligibility API Failure

**Failure Mode**: Real-time insurance eligibility verification API is unavailable or returns errors. Cannot verify patient coverage before consultation.

**Symptoms**:
- Patient starts appointment
- System unable to verify insurance
- Error: "Cannot verify coverage"

**Impact** (Medium-High):
- Patient may be unable to confirm if visit is covered
- Billing issues if coverage not properly documented
- Patient anxiety; may postpone appointment

**Mitigation**:
```javascript
async function verifyInsuranceEligibilityWithFallback(patientId) {
    const patient = await getPatient(patientId);
    
    try {
        // Attempt real-time verification
        const eligibility = await insuranceEligibilityAPI.verify({
            memberId: patient.insuranceMemberId,
            groupNumber: patient.insuranceGroupNumber,
            timeout: 10000
        });
        
        return {
            eligible: eligibility.eligible,
            coverage: eligibility.coverage,
            deductible: eligibility.deductible,
            copay: eligibility.copay,
            verified: true,
            verificationTime: now()
        };
        
    } catch (error) {
        // Fallback: check cached eligibility from last 30 days
        const cachedEligibility = await getLastVerifiedEligibility(patientId);
        
        if (cachedEligibility && daysBetween(cachedEligibility.verifiedAt, now()) < 30) {
            logger.warn('Using cached eligibility due to API failure', {
                patientId,
                cacheAge: daysBetween(cachedEligibility.verifiedAt, now())
            });
            
            return {
                ...cachedEligibility,
                verified: false,
                warning: 'Eligibility may have changed (using cached data from ' + daysBetween(cachedEligibility.verifiedAt, now()) + ' days ago)',
                recommendedAction: 'Ask patient to verify coverage'
            };
        }
        
        // No cached data; allow consultation but flag for manual verification
        return {
            eligible: null,
            verified: false,
            warning: 'Insurance eligibility could not be verified. Patient may be responsible for cost.',
            recommendedAction: 'Ask patient to confirm coverage with insurance company'
        };
    }
}
```

---

## Scenario 4: Pharmacy API Rate Limit Exceeded

**Failure Mode**: Surescripts/pharmacy lookup API rate-limited. Prescription pharmacy search blocked.

**Symptoms**:
- Clinician enters patient's zip code
- "Search for nearby pharmacies" request fails
- Error: "Service temporarily unavailable"

**Impact** (Medium):
- Clinician cannot look up pharmacies
- Must manually enter pharmacy address
- Minor inconvenience; not blocking

**Mitigation**:
- Implement client-side rate limiting (don't allow >1 search/second)
- Queue excess requests; retry with exponential backoff
- Cache pharmacy list results (most pharmacies don't change hourly)
- Allow manual pharmacy entry as fallback

---

## Scenario 5: Patient Portal Session Timeout

**Failure Mode**: Patient filling out intake form; session times out after inactivity (typically 30 min). Form data lost.

**Symptoms**:
- Patient typing in form
- Browser goes idle for 30 minutes
- Session expires; redirected to login
- Form data lost; patient frustrated

**Impact** (Medium):
- Poor UX; patient loses 20-30 minutes work
- Patient may abandon portal

**Mitigation**:
```javascript
// Auto-save form every 30 seconds
setInterval(() => {
    if (formHasChanges()) {
        saveFormDraft({
            patientId,
            formId,
            data: getCurrentFormData()
        });
    }
}, 30 * 1000);

// Extend session on form activity
document.addEventListener('input', () => {
    extendSessionTimeout(30 * 60 * 1000);  // Reset 30-min timeout
});

// Before logout: restore draft
window.addEventListener('beforeunload', () => {
    const unsavedDraft = getFormDraft(formId);
    if (unsavedDraft && daysSinceSaved(unsavedDraft) < 1) {
        showMessage('Your form will be restored when you log back in.');
    }
});
```

---

## Scenario 6: Mobile App WebRTC Drop

**Failure Mode**: Patient using mobile app; app backgrounded or network changes. WebRTC connection lost.

**Symptoms**:
- Patient receives call; switches to take it (app backgrounded)
- Returns to app
- Video frozen; no audio

**Impact** (High):
- Consultation interrupted
- Loss of time; patient frustration

**Mitigation**:
```javascript
// Detect app backgrounding (iOS/Android)
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // App backgrounded
        pauseWebRTC();
        showNotification('Consultation paused. Tap to resume.');
        
    } else {
        // App resumed
        resumeWebRTC();  // Re-establish connection
    }
});

// Handle network change (mobile switches from WiFi to LTE)
window.addEventListener('online', () => {
    logger.info('Network restored');
    attemptWebRTCReconnection();
});

window.addEventListener('offline', () => {
    logger.warn('Network lost');
    pauseWebRTC();
    showOfflineNotification();
});
```

---

## Scenario 7: Lab Results Data Mapping Error

**Failure Mode**: Lab system returns results in unexpected format. System cannot parse; results appear incorrect or missing.

**Symptoms**:
- Lab results retrieved but display as "N/A"
- Value shows as string instead of number (e.g., "140 mg/dL" displayed as "140")
- Unit missing (shows "140" instead of "140 mg/dL")

**Impact** (Medium-High):
- Clinician cannot interpret results correctly
- Potential misdiagnosis if wrong value shown
- May require manual lookup at external lab portal

**Mitigation**:
```javascript
async function parseLabResults(labSystem, rawResults) {
    // Detect lab system type and apply correct parser
    const parser = getLabParser(labSystem.type);  // LabCorp, Quest, Mayo, etc.
    
    try {
        const parsedResults = parser.parse(rawResults);
        
        // Validate parsed values
        const validationResult = validateLabValues(parsedResults);
        
        if (!validationResult.valid) {
            logger.error('Lab result validation failed', {
                labSystem: labSystem.type,
                errors: validationResult.errors,
                rawResults
            });
            
            // Fallback: show raw results; ask clinician to verify
            return {
                success: false,
                fallback: true,
                rawResults,
                warning: 'Lab results could not be automatically parsed. Please review directly with lab or portal.'
            };
        }
        
        return {
            success: true,
            results: parsedResults,
            validated: true
        };
        
    } catch (error) {
        logger.error('Lab result parsing failed', {
            labSystem: labSystem.type,
            error: error.message
        });
        
        return {
            success: false,
            fallback: true,
            rawResults,
            warning: 'Unable to parse lab results. Contact lab for verification.'
        };
    }
}

// Schema validation (ensures unit, value, ref range present)
function validateLabValues(results) {
    const required = ['testName', 'value', 'unit', 'referenceRange'];
    const errors = [];
    
    results.forEach((result, idx) => {
        required.forEach(field => {
            if (!result[field]) {
                errors.push(`Result ${idx}: missing "${field}"`);
            }
        });
        
        // Validate value is numeric
        if (isNaN(result.value)) {
            errors.push(`Result ${idx}: value not numeric (${result.value})`);
        }
    });
    
    return {valid: errors.length === 0, errors};
}
```

---

## Summary Table

| Scenario | Root Cause | Fallback | Impact | Recovery |
|----------|---|---|---|---|
| Chime Outage | AWS regional failure | Audio-only or reschedule | CRITICAL | Multi-region failover |
| EHR Timeout | Epic API slow | Cached data or offline | HIGH | Exponential backoff + cache |
| Insurance Eligibility | API down | Cached or ask patient | MEDIUM | Manual verification |
| Pharmacy Rate Limit | Too many requests | Client-side throttle | MEDIUM | Queue + retry |
| Portal Session Timeout | Inactivity | Auto-save + restore draft | MEDIUM | Resume form |
| Mobile WebRTC Drop | App backgrounding | Pause + resume | HIGH | Graceful pause/resume |
| Lab Data Mapping | Unexpected format | Show raw + manual review | MEDIUM-HIGH | Schema validation |
