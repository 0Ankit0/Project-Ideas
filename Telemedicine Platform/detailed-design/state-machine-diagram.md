# Telemedicine Platform State Machine Diagrams

This document defines the formal state machines for critical telemedicine workflows: appointment lifecycle, prescription management, insurance claims processing, and video consultation sessions. Each state transition is guarded by business rules and HIPAA compliance requirements.

## 1. Appointment Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> Scheduled: create_appointment()
    
    Scheduled --> Confirmed: confirm_appointment()\n[doctor_accepted == true]
    Scheduled --> Cancelled: cancel_appointment()\n[cancellation_reason provided]
    Scheduled --> [*]: appointment_window_expired\n[>24h before scheduled_at]
    
    Confirmed --> WaitingRoom: patient_joins_session()\n[within 10min of start_time]
    Confirmed --> NoShow: start_time_passed\n[no join within 15min]
    Confirmed --> Cancelled: clinician_cancels()\n[emergency or patient_request]
    
    WaitingRoom --> InSession: clinician_joins()\n[video_session.status == active]
    WaitingRoom --> Cancelled: cancel_appointment()\n[patient initiates]
    WaitingRoom --> NoShow: wait_timeout_reached\n[>30min idle]
    
    InSession --> OnHold: hold_session()\n[clinician_initiated or technical_issue]
    InSession --> Completed: end_session()\n[soap_note_signed == true &&\nduration >= 10min]
    InSession --> Abandoned: patient_disconnect()\n[>5min idle without response]
    
    OnHold --> InSession: resume_session()\n[technical_issue_resolved]
    OnHold --> Completed: end_session_from_hold()\n[clinician_confirms]
    OnHold --> Abandoned: hold_timeout\n[>20min on hold]
    
    Completed --> [*]: finalize_appointment()\n[claim_submitted &&\naudit_log_recorded]
    
    Cancelled --> [*]: cancel_finalized()\n[refund_processed ||
refund_not_applicable]
    
    NoShow --> [*]: noshow_recorded()\n[patient_notification_sent]
    
    Abandoned --> [*]: abandoned_recorded()\n[automatic_noshow]\n[clinician_notified]
    
    note right of Scheduled
        Patient/clinician initiates
        No-show if not confirmed
        within 24 hours
    end note
    
    note right of WaitingRoom
        10-min early join window
        30-min total wait timeout
        RTCPeerConnection established
    end note
    
    note right of InSession
        SOAP note drafted in real-time
        Audio/video streaming active
        Vital signs may be monitored
        PHI is encrypted at rest
    end note
    
    note right of Completed
        Prescription/lab orders
        created if applicable
        Insurance claim submission
        Appointment archive finalized
    end note
```

### Appointment State Transition Details

- **Scheduled → Confirmed**: Triggered when doctor accepts appointment via mobile app or portal. Email confirmation sent to patient.
- **Scheduled → Cancelled**: Patient or doctor initiates cancellation before appointment window. Refund issued per telehealth provider policy.
- **Scheduled → NoShow**: Appointment start time passed and patient did not join within 15 minutes. Notification emails sent to both parties. Insurance may not reimburse.
- **Confirmed → WaitingRoom**: Patient joins video session URL 10 minutes before scheduled time. WebRTC connection initialized.
- **WaitingRoom → InSession**: Clinician joins session and SOAP note creation begins. Start time officially recorded.
- **InSession → OnHold**: Clinician pauses consultation for technical troubleshooting or brief interruption. Patient notified.
- **InSession → Completed**: Clinician signs off SOAP note, prescriptions finalized, consultation duration ≥10 minutes. Insurance claim created.
- **OnHold → InSession**: Technical issue resolved, clinician resumes consultation.
- **Completed/Cancelled/NoShow/Abandoned → [*]**: Final state where audit logs are committed, patient portal updated, and archive created.

---

## 2. Prescription State Machine

```mermaid
stateDiagram-v2
    [*] --> Draft: create_prescription()\n[consultation_id provided]
    
    Draft --> Signed: clinician_signs_rx()\n[dea_number_verified == true &&\npdmp_check_clear == true]
    Draft --> Voided: void_draft_prescription()\n[clinician decision or\nerror correction]
    
    Signed --> Transmitted: send_to_pharmacy()\n[epcs_eligible == true &&\nstun_turnserver_available == true]
    Signed --> Voided: clinician_voids_prescription()\n[patient request or\nmedication interaction detected]
    
    Transmitted --> Dispensed: pharmacy_dispenses_rx()\n[confirmation_received from\npharmacy system or NCPDP]
    Transmitted --> Failed: transmission_failed()\n[epcs_outage or\npharmacy_routing_failure]
    Transmitted --> Voided: prescription_voided_at_pharmacy()\n[clinician revokes via DEA]
    
    Failed --> Transmitted: retry_transmission()\n[manual_retry_by_clinician &&\nservice_recovered == true]
    Failed --> FailedFaxFallback: initiate_fax_fallback()\n[non_epcs_pharmacy or\nno_electronic_option]
    
    FailedFaxFallback --> Dispensed: pharmacy_confirms_fax_receipt()\n[manual_confirmation via phone]
    FailedFaxFallback --> Voided: fax_delivery_failed()\n[fax_undeliverable]
    
    Dispensed --> Expired: rx_expiration_date_reached()\n[365 days from signed_at\nor state-specific limit]
    Dispensed --> Refilled: pharmacy_dispenses_refill()\n[refills_remaining > 0]
    
    Refilled --> Dispensed: refill_dispensed()\n[new_dispense_record created]
    
    Voided --> [*]: void_finalized()\n[audit_log_recorded]\n[patient_notified]
    
    Expired --> [*]: expiry_finalized()\n[patient_notified]
    
    note right of Draft
        Prescription not yet valid
        Medication interaction checks
        DEA scheduling rules applied
    end note
    
    note right of Signed
        Clinician digital signature
        (EPCS for Schedules II-V)
        PDMP query completed
        DEA registration verified
    end note
    
    note right of Transmitted
        EPCS transmission to pharmacy
        via Surescripts NCPDP
        or fax fallback
        Delivery confirmation logged
    end note
    
    note right of Dispensed
        Pharmacy confirms dispensing
        Patient can pick up/delivery
        365-day expiration (unless shorter)
        Refill requests tracked
    end note
```

### Prescription State Transition Details

- **Draft → Signed**: Clinician verifies patient PDMP history is clear (no doctor shopping), confirms DEA number, and applies digital signature. Controlled substance prescriptions require EPCS compliance.
- **Draft → Voided**: Corrects medication errors or patient-requested changes before signing.
- **Signed → Transmitted**: For EPCS-eligible controlled substances (Schedules II-V), prescription routed via Surescripts to patient's preferred pharmacy. Non-controlled medications may be transmitted or printed.
- **Signed → Voided**: Clinician revokes after signing (e.g., patient allergy discovered) and notifies pharmacy via DEA revocation system.
- **Transmitted → Dispensed**: Pharmacy NCPDP system confirms receipt and dispensing. Patient notification sent.
- **Transmitted → Failed**: EPCS outage, Surescripts unavailable, or pharmacy routing error. Clinician may retry or initiate fax fallback.
- **Failed → FailedFaxFallback**: For non-EPCS pharmacies, prescription sent via fax with clinician signature image. Manual confirmation required.
- **FailedFaxFallback → Dispensed**: Pharmacy calls clinic to verbally confirm fax receipt and dispenses medication.
- **Dispensed → Expired**: Prescription valid for 365 days or state-specific shorter period. After expiration, no refills allowed.
- **Dispensed → Refilled**: Patient requests refill within refills_remaining count. New dispense record created per pharmacy, original prescription remains active.

---

## 3. Insurance Claim State Machine

```mermaid
stateDiagram-v2
    [*] --> Draft: create_claim()\n[consultation_id && cpt_codes provided]
    
    Draft --> Submitted: submit_claim()\n[eligibility_verified == true &&\nphysician_npi_valid == true &&\nmodifiers_applied == true]
    Draft --> Voided: cancel_draft_claim()\n[billing error identified]
    
    Submitted --> PendingReview: edi_transmission_ack()\n[claim_received_by_payer]
    Submitted --> Rejected: immediate_rejection()\n[invalid_npi or inactive_provider]
    
    PendingReview --> Approved: payer_approves_claim()\n[coverage_verified &&\nmedical_necessity_confirmed]
    PendingReview --> Denied: payer_denies_claim()\n[not_medically_necessary or\nnot_covered_service]
    PendingReview --> PendingReview: payer_requests_additional_info()\n[missing_documentation or\nclinical_justification]
    
    Approved --> Paid: payer_processes_payment()\n[eob_received &&\nallowed_amount > 0]
    Approved --> PartiallyPaid: payer_partial_denial()\n[coinsurance_applies or\ndeductible_applies]
    
    PartiallyPaid --> Paid: patient_payment_received()\n[patient_coinsurance_paid]
    
    Denied --> Appealed: submit_appeal()\n[clinician_submits_appeal &&\nmedical_record_attached]
    Denied --> Voided: write_off_claim()\n[no appeal submitted]
    
    Appealed --> AppealReview: appeal_acknowledgment_received()\n[payer_review_in_progress]
    AppealReview --> Approved: appeal_overturned()\n[new evidence convincing]
    AppealReview --> Denied: appeal_upheld()\n[denial confirmed final]
    
    Paid --> [*]: claim_finalized()\n[eob_archived]\n[patient_balance_calculated]
    
    Voided --> [*]: void_finalized()\n[write_off_recorded]
    
    Rejected --> [*]: rejection_logged()\n[provider_corrective_action]
    
    note right of Draft
        Claim line items created
        CPT & ICD-10 codes assigned
        Billing modifiers applied
        (e.g., 25 for separate eval)
    end note
    
    note right of Submitted
        Claim transmission via
        EDI 837 format (CMS-approved)
        to insurance clearinghouse
        or payer directly
    end note
    
    note right of PendingReview
        Payer processes claim
        Utilization review (UR) may apply
        Additional documentation
        requests sent to provider
    end note
    
    note right of Approved
        Payer determined covered service
        Allowed amount calculated
        EOB (Explanation of Benefits)
        will be sent to patient/provider
    end note
    
    note right of Paid
        Remittance advice (RA) received
        from payer via EDI 835 format
        Payment posted to provider
        Patient balance finalized
    end note
```

### Insurance Claim State Transition Details

- **Draft → Submitted**: Clinician finalizes claim with ICD-10 diagnosis codes, CPT procedure codes, and billing modifiers. Eligibility verification completed. Claim converted to EDI 837 format and transmitted to insurance clearinghouse.
- **Draft → Voided**: Billing department identifies error (wrong patient, duplicate) and cancels before submission.
- **Submitted → PendingReview**: Clearinghouse acknowledges receipt and forwards to payer. Payer begins claim adjudication.
- **Submitted → Rejected**: Immediate rejection if NPI invalid or provider not in-network. No appeal process available; must correct and resubmit.
- **PendingReview → Approved**: Payer confirms coverage, verifies medical necessity, and approves payment. EOB generated.
- **PendingReview → Denied**: Service not covered per patient's plan, medical necessity not met, or out-of-network. Denial reason code recorded.
- **PendingReview → PendingReview**: Payer requests additional clinical documentation or medical record excerpts to complete review.
- **Approved → Paid**: Payer submits payment to provider bank account. Remittance advice (RA) includes line-item adjustments and patient balance.
- **Approved → PartiallyPaid**: Coinsurance applies (patient owes 20%), or deductible not yet met. Patient balance calculated.
- **PartiallyPaid → Paid**: Patient pays coinsurance or deductible. Claim fully resolved.
- **Denied → Appealed**: Clinician submits appeal with supporting clinical documentation within 30-180 days (varies by payer).
- **Appealed → AppealReview**: Payer acknowledges appeal and conducts independent review.
- **AppealReview → Approved**: Appeal evidence convinces payer; original denial overturned and claim paid.
- **AppealReview → Denied**: Payer upholds original denial; final determination.

---

## 4. Consultation Session State Machine

```mermaid
stateDiagram-v2
    [*] --> Initializing: session_created()\n[webrtc_peer_connection_init]
    
    Initializing --> WaitingRoom: ice_candidates_exchanged\n[stun_turn_servers_responsive]
    Initializing --> Failed: ice_negotiation_timeout\n[>15s without ICE_CONNECTED]
    
    WaitingRoom --> InSession: clinician_joins()\n[both_audio_video_tracks_active]
    WaitingRoom --> FailedWaitTimeout: wait_timeout\n[>30min idle]
    
    InSession --> InSession: audio_video_stream_active\n[quality_monitoring_ongoing]
    InSession --> OnHold: clinician_pauses_session()\n[technical_diagnostic or\ninternal_call_needed]
    InSession --> DowngradeToAudio: video_link_failure\n[vp9_decode_error or\nbandwidth_dropped_below_200kbps]
    
    DowngradeToAudio --> InSession: video_recovered()\n[bandwidth_restored &&\nwebrtc_codec_negotiated]
    DowngradeToAudio --> Completed: end_session()\n[clinician_confirms_end]
    
    OnHold --> InSession: session_resumed()\n[clinician_confirms]
    OnHold --> Completed: end_from_hold()\n[clinician_concludes]
    OnHold --> OnHoldTimeout: hold_timeout\n[>20min idle]
    
    OnHoldTimeout --> Completed: session_force_ended()\n[safety_protocol]
    
    InSession --> NetworkDropped: network_disconnection\n[rtc_connection_lost]
    NetworkDropped --> InSession: patient_reconnects()\n[within 5min &&\nnew_peer_connection_established]
    NetworkDropped --> Abandoned: reconnect_timeout\n[>5min offline]
    
    Completed --> SessionArchived: archive_session_recording()\n[s3_upload_successful &&\nencryption_verified]
    Abandoned --> SessionArchived: abandon_recorded()\n[notification_sent_to_clinician]
    Failed --> SessionArchived: session_failed_logged()\n[error_code_recorded]
    FailedWaitTimeout --> SessionArchived: timeout_logged()
    
    SessionArchived --> [*]: session_finalized()\n[hipaa_retention_initiated]
    
    note right of Initializing
        WebRTC signaling established
        SDP offer/answer exchanged
        ICE candidate gathering
        STUN/TURN server queries
    end note
    
    note right of WaitingRoom
        Awaiting clinician entry
        Patient audio/video enabled
        Bandwidth monitoring begins
        Jitter buffer configured
    end note
    
    note right of InSession
        Bilateral encrypted media streams
        SOAP note text entry active
        Vital signs may be transmitted
        Screen sharing available
    end note
    
    note right of DowngradeToAudio
        Video disabled due to network
        Audio stream continues
        Bandwidth constraint detected
        VP9 codec downgrade attempted
    end note
    
    note right of NetworkDropped
        RTCPeerConnection closed
        5-minute grace period
        Automatic reconnection attempted
        Clinician notified of drop
    end note
    
    note right of SessionArchived
        Video recording S3 storage
        Encryption at rest (AES-256)
        HIPAA audit trail complete
        Session metadata finalized
    end note
```

### Consultation Session State Transition Details

- **Initializing → WaitingRoom**: WebRTC peer connection successfully negotiates ICE candidates with STUN/TURN servers. Both patient and clinician audio/video tracks are configured.
- **Initializing → Failed**: ICE negotiation timeout (>15 seconds) without establishing connected state. Common cause: STUN/TURN server unreachable, firewall blocking UDP.
- **WaitingRoom → InSession**: Clinician successfully joins session. Audio and video streams become active. SOAP note creation begins. Bandwidth monitoring initialized.
- **WaitingRoom → FailedWaitTimeout**: Clinician does not join within 30 minutes. Patient kept waiting, automatic timeout for safety.
- **InSession → OnHold**: Clinician pauses consultation for brief internal call or technical troubleshooting. Audio/video remains but streaming halted.
- **InSession → DowngradeToAudio**: Video stream degradation detected (VP9 decoder error or bandwidth <200 Kbps). Audio continues while video disabled.
- **DowngradeToAudio → InSession**: Network bandwidth recovers; video codec re-negotiated and restored.
- **InSession → NetworkDropped**: Patient's network connection lost (RTCPeerConnection state changes to disconnected/failed). 5-minute grace period for automatic reconnection.
- **NetworkDropped → InSession**: Patient reconnects within 5 minutes and new WebRTC session established with same consultation context.
- **NetworkDropped → Abandoned**: Reconnection not attempted or fails after 5 minutes. Session ends with abandon status.
- **OnHold → InSession**: Clinician resumes session after technical issue resolved.
- **OnHold → OnHoldTimeout**: Consultation held >20 minutes without activity; automatic timeout triggers for patient safety.
- **Completed → SessionArchived**: Clinician confirms session end. Video recording uploaded to S3 with AES-256 encryption. Audit log committed.
- **SessionArchived → [*]**: Final state. HIPAA retention policy applied; session may be auto-deleted after 6 years (or per state regulation).

---

## 5. Summary of Guard Conditions

All state transitions are guarded by conditions that enforce HIPAA compliance, data integrity, and clinical safety:

| Guard Condition | Purpose | Enforced By |
|---|---|---|
| `hipaa_retention_initiated` | Ensures records kept per 45 CFR 164.530(j) (6-year minimum) | Compliance controller |
| `phi_encrypted_at_rest` | All PHI encrypted before storage (AES-256) | Data encryption service |
| `audit_log_recorded` | Action logged with user ID, timestamp, action code, PHI access flag | Audit logging middleware |
| `dea_number_verified` | NPI/DEA number valid and active in NPI Registry or DEA CSOS | External DEA verification API |
| `pdmp_check_clear` | Patient's PDMP report shows no opioid prescriptions from other doctors | PDMP Query Service (per state) |
| `ice_candidates_exchanged` | WebRTC ICE negotiation successful (candidates gathered) | RoomManager (AWS Chime SDK) |
| `video_session.status == active` | Peer connection in CONNECTED state; media flowing | WebRTC adapter |
| `soap_note_signed` | Clinician applied digital signature to clinical note | SOAP note signer service |
| `claim_submitted` | EDI 837 claim transmission acknowledged by clearinghouse | Claims API |
| `epcs_eligible` | Medication schedule and DEA verification support electronic prescribing | DEA schedules database |
| `stun_turnserver_available` | STUN/TURN servers responding within SLA | ICE server provider |
| `eob_received` | Payer EOB (EDI 835) received and parsed successfully | Claims API |
| `s3_upload_successful` | Video recording persisted to S3 with redundancy | Session recording service |

All transitions are also subject to HIPAA audit logging: every state change is recorded with actor, timestamp, resource ID, and PHI access indicator.
