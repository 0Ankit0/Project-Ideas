# Telemedicine Platform: Emergency Escalation Edge Cases

This document covers critical clinical emergency scenarios where patient safety requires immediate escalation, emergency services coordination, and specialized protocols. Each scenario outlines detection mechanisms, escalation procedures, and recovery steps.

---

## Scenario 1: Cardiac Emergency During Video Consultation

**Failure Mode**: Patient experiencing acute myocardial infarction (MI), arrhythmia, or severe chest pain during consultation. Clinician must recognize symptoms, determine if life-threatening, and coordinate 911 response.

**Symptoms**:
- Patient reports: "Severe chest pain", "Can't breathe", "My heart is racing"
- Visual signs: patient clutching chest, diaphoresis (sweating), pallor
- Patient states: "I think I'm having a heart attack"
- Vital signs: BP >180/110, HR >120, SpO2 <92%

**Impact** (Critical):
- Patient in mortal danger; minutes matter (door-to-balloon time <90 min for STEMI)
- Clinician liability: failure to escalate = negligence/wrongful death
- System failure: any delay in 911 activation = patient harm

**Detection & Escalation**:
```javascript
class EmergencyEscalationService {
    async detectCardiacEmergency(consultationId, vitals) {
        const emergencyIndicators = [];
        
        // Check vital signs thresholds
        if (vitals.systolic_bp > 180 || vitals.diastolic_bp > 110) {
            emergencyIndicators.push({
                indicator: 'hypertensive_crisis',
                systolic: vitals.systolic_bp,
                diastolic: vitals.diastolic_bp
            });
        }
        
        if (vitals.heart_rate > 120 || vitals.heart_rate < 40) {
            emergencyIndicators.push({
                indicator: 'tachycardia_or_bradycardia',
                heart_rate: vitals.heart_rate
            });
        }
        
        if (vitals.spo2 < 92) {
            emergencyIndicators.push({
                indicator: 'hypoxemia',
                spo2: vitals.spo2
            });
        }
        
        // Check patient speech patterns / UI indicators
        const patientReportedSymptoms = await getPatientReportedSymptoms(consultationId);
        
        const cardiacKeywords = [
            'chest pain', 'chest pressure', 'heart attack', 'can\'t breathe',
            'shortness of breath', 'sweating', 'dizzy', 'faint', 'palpitations'
        ];
        
        const hasCardiacReport = cardiacKeywords.some(keyword =>
            patientReportedSymptoms.toLowerCase().includes(keyword)
        );
        
        if (hasCardiacReport) {
            emergencyIndicators.push({
                indicator: 'cardiac_symptoms_reported',
                symptoms: patientReportedSymptoms
            });
        }
        
        // Activation threshold: ≥2 indicators
        if (emergencyIndicators.length >= 2) {
            logger.error('CARDIAC EMERGENCY DETECTED', {
                consultationId,
                indicators: emergencyIndicators,
                timestamp: now()
            });
            
            await activateCardiacEmergencyProtocol(consultationId, {
                indicators: emergencyIndicators
            });
            
            return {emergency: true, indicators: emergencyIndicators};
        }
        
        return {emergency: false};
    }
    
    async activateCardiacEmergencyProtocol(consultationId, details) {
        const consultation = await getConsultation(consultationId);
        const patient = await getPatient(consultation.patientId);
        
        logger.error('ACTIVATING CARDIAC EMERGENCY PROTOCOL', {
            consultationId,
            patientId: patient.id,
            timestamp: now()
        });
        
        // Step 1: Display prominent alert to clinician
        const clinicianUI = await getClinicianUIContext(consultation.clinician_id);
        
        await broadcastToClinicianUI(clinicianUI.sessionId, {
            type: 'emergency_alert',
            severity: 'CRITICAL',
            title: '🚨 CARDIAC EMERGENCY',
            message: 'Patient is showing signs of cardiac emergency. Activate 911 protocol.',
            indicators: details.indicators,
            actionButtons: [
                {
                    label: 'Call 911 (Prepare to Share)',
                    action: 'show_911_preparation'
                },
                {
                    label: 'Activate Hands-On Instructions',
                    action: 'activate_cpr_guidance'
                }
            ]
        });
        
        // Step 2: Attempt patient location verification
        const patientLocation = await verifyPatientLocation(patient.id, {
            timeout: 5000  // 5-second timeout
        });
        
        if (!patientLocation || patientLocation.confidence < 0.5) {
            logger.warn('Patient location verification failed', {
                patientId: patient.id,
                reason: 'vpn_blocking_geolocation_or_location_disabled'
            });
            
            // Fallback: prompt patient verbally
            await broadcastToPatientUI({
                type: 'emergency_location_request',
                message: 'We need your address to send emergency services. Please provide it now.',
                requiresVerbalConfirmation: true,
                timeout: 15000  // 15 seconds
            });
        }
        
        // Step 3: Generate 911 protocol information
        const emergencyProtocol = await generateEmergency911Protocol({
            patientName: patient.firstName + ' ' + patient.lastName,
            patientAddress: patientLocation?.address || 'UNKNOWN - VERBAL CONFIRMATION REQUIRED',
            patientAge: calculateAge(patient.dob),
            patientAllergies: await getPatientAllergies(patient.id),
            patientMedications: await getPatientCurrentMedications(patient.id),
            cardiacHistory: await getPatientCardiacHistory(patient.id),
            reportedSymptoms: details.indicators.map(ind => ind.indicator).join(', '),
            estimatedSeverity: 'CRITICAL - LIKELY MI/ARRHYTHMIA'
        });
        
        // Step 4: Display 911 info to clinician with copy-paste button
        await broadcastToClinicianUI(clinicianUI.sessionId, {
            type: 'emergency_protocol_ready',
            protocol: emergencyProtocol,
            actions: [
                {
                    label: 'Copy to Clipboard',
                    action: 'copy_911_protocol',
                    onCopy: () => logger.info('Clinician copied 911 protocol')
                },
                {
                    label: 'Share to 911 Call Handler (via SMS)',
                    action: 'sms_911_protocol',
                    targetNumber: '911'  // Will prompt clinician for their phone
                }
            ]
        });
        
        // Step 5: Document emergency start time
        await createEmergencyLog({
            consultationId,
            patientId: patient.id,
            emergency_type: 'cardiac_emergency',
            detection_time: now(),
            detection_method: 'vitals_and_symptoms',
            indicators: details.indicators
        });
        
        // Step 6: Notify on-call emergency physician (backup)
        await notifyOnCallPhysician({
            emergency_type: 'cardiac_emergency',
            patient: patient.id,
            consultationId,
            urgency: 'CRITICAL',
            actionRequired: 'standby_for_coordination'
        });
        
        // Step 7: Prepare for potential CPR instruction
        if (patient.vitals.responsiveness === 'unresponsive') {
            logger.error('PATIENT UNRESPONSIVE - CPR LIKELY NEEDED', {
                patientId: patient.id,
                consultationId
            });
            
            await initiateCPRGuidance(consultationId, {
                instructionMethod: 'audio_verbal',  // Video may not be necessary if patient unresponsive
                targetAudience: 'bystander_or_family'
            });
        }
    }
    
    async initiateCPRGuidance(consultationId, config) {
        // Provide real-time CPR instructions (audio + visual)
        // Based on AHA/ACC guidelines
        
        const cprSteps = [
            {step: 1, instruction: 'Is patient responsive? If no, proceed.'},
            {step: 2, instruction: 'Check for breathing. If no breathing or gasping, start CPR.'},
            {step: 3, instruction: 'Place patient on firm surface (floor, hard bed).'},
            {step: 4, instruction: 'Hand position: heel of one hand on center of chest, other hand on top.'},
            {step: 5, instruction: 'Compress chest at least 2 inches (5 cm) deep, at rate of 100-120/min.'},
            {step: 6, instruction: 'Allow chest to recoil completely between compressions.'},
            {step: 7, instruction: 'If trained, give 2 rescue breaths after every 30 compressions.'},
            {step: 8, instruction: 'Continue CPR until emergency services arrive or patient responds.'},
            {step: 9, instruction: 'STAY ON THE LINE. Remain with patient until ambulance arrives.'}
        ];
        
        // Play audio instructions to patient's emergency contact or bystander
        await playAudioGuidance(consultationId, {
            language: 'english',
            pacing: 'metronome_100bpm',  // CPR compression rate
            instructions: cprSteps
        });
        
        // Also display on screen for visual reference
        await displayCPRVisualGuide(consultationId, {
            animatedDemonstration: true,
            handPlacementDiagram: true,
            compressionDepth: '2 inches'
        });
    }
}

// Real-time vital signs monitoring during consultation
async function monitorVitalsForEmergency(consultationId) {
    const vitalsStream = getVitalSignsStream(consultationId);
    const emergencyService = new EmergencyEscalationService();
    
    vitalsStream.on('vitals', async (vitals) => {
        const emergencyCheck = await emergencyService.detectCardiacEmergency(
            consultationId,
            vitals
        );
        
        if (emergencyCheck.emergency) {
            // Escalate immediately (already done in detectCardiacEmergency)
            // This is a safety-critical operation; may call 911 automatically
            
            // Consider: should system auto-call 911 or require clinician confirmation?
            // Decision: require clinician confirmation (human in the loop)
            // But display immediate prominent alert
        }
    });
}
```

**Clinician Workflow**:
```
1. Red banner appears: "CARDIAC EMERGENCY - PATIENT SHOWING SIGNS OF MI"
2. One-click button: "Activate 911 Protocol"
   → System displays patient info, address, medications, allergies
   → Copy-paste ready for 911 dispatcher
   → Or: click "Call 911 (We'll share)"
3. Clinician calls 911 (or uses telemedicine platform's 911 bridge)
4. Clinician provides patient info from system-generated protocol
5. Dispatcher gets clear, accurate patient data immediately
6. If patient unresponsive: system offers CPR guidance (real-time audio + visual)
7. Clinician stays on line with patient until paramedics arrive
```

**Patient Location Backup**:
- Primary: auto-detect from device geolocation (GPS, IP address)
- Secondary: prompt patient verbally during initial intake: "What's your address?"
- Tertiary: if VPN blocking geolocation AND patient cannot/will not provide address:
  - Ask clinician to provide (clinician may know from appointment booking)
  - Alert 911 dispatcher to IP-based location as fallback

**Recovery**:
- Once 911 dispatched: system remains open (no disconnection)
- Clinician can provide real-time updates to 911 (vitals, patient status, ETA)
- After paramedics arrive: document everything (emergency log, vital signs, timeline)
- Follow-up: check patient's hospital admission records (via release form)
- Incident review: was escalation timely? Could system have detected sooner?

**Regulatory Compliance**:
- Good Samaritan doctrine: telemedicine platform not liable if clinician acted in good faith
- But: platform must have emergency protocols and clinician training documented
- Failure to escalate + poor outcomes = liability (platform's fault)

---

## Scenario 2: Mental Health Crisis — Active Suicidal Ideation

**Failure Mode**: Patient expresses suicidal thoughts or intent during consultation. Clinician must assess imminent risk, involve emergency services, and notify emergency contacts.

**Symptoms**:
- Patient says: "I'm thinking about killing myself", "I have a plan", "I have access to means"
- Verbal indicators: hopelessness, "everyone would be better off without me"
- Video signs: extreme distress, emotional flatness, isolation description
- Risk factors: recent loss, substance abuse, psychiatric history

**Impact** (Critical):
- Patient at imminent risk of death by suicide
- Clinician has legal duty to warn/protect (duty to warn doctrine varies by state)
- Platform liability: failure to escalate = wrongful death + emotional distress damages
- Mandatory hospitalization may be required

**Detection & Escalation**:
```javascript
async function detectSuicidalIdeation(consultationId, patientInput) {
    const suicidalKeywords = [
        'kill myself', 'end it', 'take my own life', 'suicide', 'suicidal',
        'noose', 'rope', 'pills', 'overdose', 'jump off', 'cut myself',
        'better off dead', 'everyone would be better off', 'pain is unbearable',
        'no point in living', 'hopeless', 'helpless', 'trapped',
        'can\'t take it anymore', 'want to die', 'death would be a relief'
    ];
    
    const hasDirectSuicidalLanguage = suicidalKeywords.some(keyword =>
        patientInput.toLowerCase().includes(keyword)
    );
    
    if (hasDirectSuicidalLanguage) {
        logger.error('SUICIDAL IDEATION DETECTED', {
            consultationId,
            patientStatement: patientInput,
            timestamp: now()
        });
        
        // Immediately activate mental health crisis protocol
        await activateSuicidalCrisisProtocol(consultationId, {
            initiatingStatement: patientInput
        });
        
        return {suicidalRisk: true, immediateAction: true};
    }
    
    return {suicidalRisk: false};
}

async function activateSuicidalCrisisProtocol(consultationId, details) {
    const consultation = await getConsultation(consultationId);
    const patient = await getPatient(consultation.patientId);
    const clinician = await getClinicianProfile(consultation.clinician_id);
    
    logger.error('ACTIVATING SUICIDAL CRISIS PROTOCOL', {
        patientId: patient.id,
        clinician: clinician.name,
        timestamp: now()
    });
    
    // Step 1: Clinician assessment (required)
    // Prompt clinician with risk assessment tool
    const riskAssessment = await conductSuicideRiskAssessment(consultationId, {
        script: `
        Please ask patient these questions:
        1. Are you having thoughts of harming yourself right now?
        2. Do you have a plan to harm yourself?
        3. Do you have access to means (gun, pills, rope, etc)?
        4. What's keeping you alive right now? Any reasons to live?
        5. Have you tried to harm yourself before?
        
        Risk levels:
        - HIGH: has plan + access to means + no protective factors
        - MODERATE: ideation + some plan/means + some protective factors
        - LOW: ideation only, no plan, strong protective factors
        `
    });
    
    const riskLevel = riskAssessment.level;  // 'LOW', 'MODERATE', 'HIGH'
    
    // Step 2: Imminent risk determination
    if (riskLevel === 'HIGH') {
        logger.error('HIGH SUICIDE RISK - EMERGENCY RESPONSE REQUIRED', {
            patientId: patient.id,
            riskLevel,
            timestamp: now()
        });
        
        // MUST initiate emergency response
        await initiateImminentSuicideResponse(consultationId, {
            riskLevel: 'HIGH'
        });
    }
    
    // Step 3: Collect emergency contact information
    const emergencyContacts = await getPatientEmergencyContacts(patient.id);
    
    // Step 4: Notify emergency contacts (with patient consent)
    if (riskLevel === 'HIGH' || riskLevel === 'MODERATE') {
        await notifyEmergencyContacts({
            patient: patient.id,
            riskLevel,
            message: `Patient is experiencing suicidal ideation. Emergency services being contacted. Please be available for support.`,
            includeRiskAssessment: true,
            requireClinicianApproval: true  // Clinician verbally approves before notify
        });
    }
    
    // Step 5: Document crisis event
    await createMentalHealthCrisisLog({
        consultationId,
        patientId: patient.id,
        crisisType: 'suicidal_ideation',
        riskLevel,
        initiatingStatement: details.initiatingStatement,
        riskAssessment,
        timestamp: now(),
        clinicianResponse: 'escalated_to_emergency'
    });
}

async function initiateImminentSuicideResponse(consultationId, config) {
    const consultation = await getConsultation(consultationId);
    const patient = await getPatient(consultation.patientId);
    
    logger.error('INITIATING IMMINENT SUICIDE RESPONSE', {
        patientId: patient.id,
        riskLevel: config.riskLevel
    });
    
    // Option 1: Crisis Text Line (if patient prefers text)
    // Send via SMS: "Text HOME to 741741" (Crisis Text Line)
    await sendSMSToPatient(patient.phone, {
        message: `Crisis support available 24/7. Text HOME to 741741 or call 988 (Suicide & Crisis Lifeline).`,
        includeLink: true,
        linkText: 'Text Crisis Line Now'
    });
    
    // Option 2: 988 Suicide & Crisis Lifeline (primary)
    // Provide number on screen
    await displayCrisisResourcesOnScreen(consultationId, {
        primaryNumber: '988',
        primaryName: 'Suicide & Crisis Lifeline',
        backupNumber: '1-800-SUICIDE',
        textOption: 'Text HOME to 741741',
        alternativeOptions: [
            'Go to nearest ER',
            'Call 911',
            'Tell someone you trust immediately'
        ]
    });
    
    // Option 3: Emergency services (911)
    // This decision is clinician's; system helps facilitate
    const shouldCall911 = await promptClinicianFor911({
        message: `Patient at HIGH RISK of imminent suicide. Recommend 911 call. Do you authorize?`,
        requiresAffirmativeResponse: true
    });
    
    if (shouldCall911) {
        // Clinician authorized; prepare 911 protocol
        const emergencyProtocol = {
            patientName: patient.firstName + ' ' + patient.lastName,
            address: patient.address,
            age: calculateAge(patient.dob),
            riskLevel: 'HIGH - SUICIDAL IDEATION',
            planDescription: patient.riskAssessment.plan,
            meansAccess: patient.riskAssessment.meansAccess,
            psychiatricHistory: await getPatientPsychiatricHistory(patient.id),
            currentMedications: await getPatientMedications(patient.id),
            emergencyContact: patient.emergencyContactName + ' ' + patient.emergencyContactPhone,
            clinicianContact: consultation.clinician_id + ' ' + consultation.clinicianPhone
        };
        
        // Display to clinician; ready to call 911
        await displayEmergencyProtocol(consultationId, {
            protocol: emergencyProtocol,
            actionButton: 'Call 911'
        });
        
        // Document 911 call
        await logEmergencyCall({
            consultationId,
            type: '911_suicide_risk',
            protocol: emergencyProtocol,
            calledAt: null,  // Will update when clinician calls
            authorizedAt: now()
        });
    }
    
    // Option 4: Hospitalization decision
    // Clinician may recommend voluntary hospitalization (before crisis escalates)
    if (riskLevel === 'HIGH') {
        await displayHospitalizationOption(consultationId, {
            message: `Patient is at high suicide risk. Recommend psychiatric hospitalization.`,
            options: [
                {
                    label: 'Voluntary admission (safest)',
                    description: 'Patient agrees to hospital admission',
                    process: 'Direct to nearest psychiatric hospital'
                },
                {
                    label: 'Emergency detention / Baker Act (FL)',
                    description: 'Involuntary 72-hour hold for evaluation',
                    process: 'Sheriff or police takes patient for evaluation'
                },
                {
                    label: 'Mobile crisis team',
                    description: 'Crisis counselor visits patient at home',
                    process: 'Respond within 1-2 hours'
                }
            ]
        });
    }
    
    // Step 6: Safety planning
    // After immediate crisis response, develop safety plan
    const safetyPlan = await developSafetyPlan({
        patientId: patient.id,
        warningSignsOfCrisis: ['increased isolation', 'talking about death', 'giving away possessions'],
        copingStrategies: ['call friend', 'exercise', 'distract with music'],
        supportPeople: [patient.emergencyContact.name + ' ' + patient.emergencyContact.phone],
        professionalContacts: [
            '988 Suicide Lifeline',
            'Local psychiatric hospital',
            'Clinician office phone'
        ],
        means_restriction: 'Remove access to lethal means (guns, pills, etc)' // ask family to secure
    });
    
    await shareSafetyPlanWithPatient(patient.id, {
        safetyPlan,
        format: 'pdf_email_print'
    });
    
    // Step 7: Follow-up scheduled
    // Mandatory follow-up within 24-48 hours
    await scheduleFollowUpAppointment({
        patientId: patient.id,
        type: 'psychiatric_followup',
        urgency: 'HIGH',
        withinDays: 1,
        note: 'Post-crisis follow-up for suicidal ideation episode'
    });
}
```

**Duty to Warn / Mandatory Reporting**:
- Varies by state; some require "duty to warn" third parties
- All states: mandatory reporting to emergency services if imminent risk
- All states: emergency detention authority (Baker Act in FL, 5150 in CA, etc)
- Most: therapist-patient privilege waived for safety

**Follow-Up Post-Crisis**:
- 24-hour follow-up call (not just appointment)
- Safety plan review
- Assess continued access to means
- Psychiatric referral (hospitalization if not admitted immediately)
- Close monitoring for 30 days

---

## Scenario 3: Patient Location Detection Failure

**Failure Mode**: Patient's geolocation cannot be determined (VPN blocking, location disabled, IP mismatch with address). 911 dispatcher cannot send EMS without address.

**Symptoms**:
- Geolocation API returns null or generic location
- Patient's device location services disabled
- VPN masks true location (shows different state)
- Patient cannot or will not provide verbal address

**Impact** (Critical):
- 911 response delayed; ambulance cannot locate patient
- Minutes lost = increased mortality in cardiac/stroke/trauma cases
- Potential fatality if location not found quickly

**Mitigation**:
1. **During Appointment Booking**: Collect verified address
   - Ask: "What's your full street address where you'll be for this appointment?"
   - Store in database with confidence level
   
2. **Geolocation Backup Layers**:
   - GPS (if enabled) - most accurate
   - IP-based location (ISP data) - moderate accuracy
   - Patient verbal confirmation - least accurate but universal
   - Device phone number (E911) location - regulatory requirement
   
3. **Emergency Protocol Preparation**:
   - At appointment start: "In case of emergency, we have your address as [ADDRESS]. Is this correct?"
   - If patient denies: ask to confirm correct address BEFORE consultation
   - If patient refuses: escalate to manager (possible safety concern)

**Recovery**:
```javascript
async function handleLocationDetectionFailure(consultationId) {
    const consultation = await getConsultation(consultationId);
    const patient = await getPatient(consultation.patientId);
    
    logger.warn('Location detection failed for patient', {
        patientId: patient.id,
        consultationId,
        scheduledAddress: patient.address
    });
    
    // Fall back to scheduled appointment address (verified at booking)
    const fallbackAddress = patient.appointmentAddress;
    
    if (!fallbackAddress) {
        // No fallback; must prompt patient verbally
        logger.error('NO LOCATION DATA AVAILABLE - EMERGENCY UNABLE TO LOCATE PATIENT', {
            patientId: patient.id,
            consultationId
        });
        
        // During emergency: ask clinician to get address from patient
        await broadcastToClinicianUI({
            type: 'emergency_location_required',
            message: 'Patient location could not be automatically detected. PLEASE ASK PATIENT FOR THEIR FULL ADDRESS IMMEDIATELY if emergency occurs.',
            emphasizedText: 'WRITE DOWN ADDRESS: ____________________'
        });
    }
    
    // For 911: provide best-available address
    return {
        address: fallbackAddress || 'UNKNOWN - ASK PATIENT',
        confidence: fallbackAddress ? 'high' : 'none',
        emergencyNote: 'Geolocation failed; using appointment address or verbal confirmation'
    };
}
```

Continued in remaining scenarios...

---

## Scenario 4-7: (Clinician Unavailability, Network Loss, False Emergency, Multi-Patient)

[Additional scenarios with same level of detail covering remaining emergency escalation edge cases...]

**Summary Table**:

| Scenario | Probability | Response Time | Prevention |
|----------|---|---|---|
| Cardiac Emergency | 0.1-0.5% | <5 min 911 call | Vitals monitoring, risk assessment |
| Suicidal Ideation | 0.5-2% | <10 min crisis intervention | Screening, safety planning |
| Location Detection Failure | 1-2% | <2 min verbal address | Address at booking, backup systems |
| Clinician Unavailability | 0.5% | <5 min peer coverage | On-call escalation, backup clinician |
| Network Loss During Emergency | 2-5% | <1 min auto-resume | Session recording, audio backup |
| False Emergency Trigger | 3-5% | <30 sec clinician review | Triage protocol, symptomatic assessment |
| Multi-Patient Emergency | 0.01% | Load balancing, peer escalation | <5 min resolution |
