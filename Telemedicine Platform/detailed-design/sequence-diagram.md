# Sequence Diagrams — Telemedicine Platform

This document contains three detailed sequence diagrams covering the most complex technical workflows in the Telemedicine Platform: WebRTC video consultation setup, DEA EPCS e-prescription compliance, and insurance claims processing.

---

## WebRTC Video Consultation Setup

This sequence covers the complete signaling and media establishment flow from a patient joining a scheduled consultation through to a stable bidirectional audio/video stream with the clinician. It includes Chime session creation, ICE negotiation (STUN/TURN), and the event trail published for downstream services.

```mermaid
sequenceDiagram
    autonumber
    participant PA as Patient App\n(Browser/Mobile)
    participant SS as SchedulingService
    participant VS as VideoService
    participant CHIME as AWS Chime SDK\n(Control Plane)
    participant STUN as STUN Server\n(AWS Global)
    participant TURN as TURN Server\n(AWS Regional)
    participant DA as Doctor App\n(Browser)
    participant SQS as SQS FIFO\n(Events)
    participant NS as NotificationService
    participant EHR as EHRService

    Note over PA,EHR: T-5 min: Patient is reminded and joins waiting room

    PA->>SS: GET /appointments/{id}/join-token
    SS->>SS: Validate appointment status == CONFIRMED
    SS->>SS: Validate patient identity matches appointment
    SS-->>PA: { appointmentId, joinToken, videoRoomId }

    PA->>VS: POST /video-rooms/{roomId}/attendees\nAuthorization: Bearer {joinToken}
    VS->>VS: Validate joinToken (JWT signature + expiry)
    VS->>VS: Check room exists or needs creation

    alt Room not yet created (first joiner)
        VS->>CHIME: CreateMeeting({ externalMeetingId: appointmentId, mediaRegion: "us-east-1", meetingFeatures: { audio: { echoReduction: "AVAILABLE" } } })
        CHIME-->>VS: { Meeting: { MeetingId, MediaPlacement: { AudioHostUrl, SignalingUrl, TurnControlUrl } } }
        VS->>VS: Persist meeting metadata to VideoSessionDB
    end

    VS->>CHIME: CreateAttendee({ MeetingId, ExternalUserId: patientId })
    CHIME-->>VS: { Attendee: { AttendeeId, JoinToken } }
    VS->>VS: Store attendee record, set patientJoinedAt = now()
    VS-->>PA: { chimeMeetingId, attendee: { attendeeId, joinToken }, iceServers, signalingUrl }

    Note over PA,STUN: WebRTC peer connection initialisation

    PA->>PA: new RTCPeerConnection({ iceServers: [stun:, turn:] })
    PA->>STUN: STUN Binding Request (discover public IP/port)
    STUN-->>PA: STUN Binding Response (reflexive candidate)

    PA->>PA: createOffer() → SDP offer (audio+video codec negotiation)
    PA->>CHIME: Send SDP offer via Chime Signaling WebSocket
    CHIME-->>PA: SDP answer (server-side codec selection)
    PA->>PA: setRemoteDescription(answer)

    Note over PA,TURN: ICE candidate gathering and exchange

    PA->>CHIME: GET /turn-credentials (short-lived TURN username/credential)
    CHIME-->>PA: { username, password, ttl: 300, uris: ["turn:us-east-1.turn.chime.aws"] }
    PA->>TURN: TURN Allocate Request (authenticate with credential)
    TURN-->>PA: TURN Relayed candidate (server-reflexive relay address)
    PA->>CHIME: Trickle ICE candidate (relay) via signaling WebSocket

    Note over DA,CHIME: Doctor joins ~1 minute later

    DA->>SS: GET /appointments/{id}/join-token (doctor role)
    SS-->>DA: { appointmentId, joinToken, videoRoomId }
    DA->>VS: POST /video-rooms/{roomId}/attendees\nAuthorization: Bearer {doctorJoinToken}
    VS->>CHIME: CreateAttendee({ MeetingId, ExternalUserId: doctorId })
    CHIME-->>VS: { Attendee: { AttendeeId, JoinToken } }
    VS->>VS: Set doctorJoinedAt = now()
    VS-->>DA: { chimeMeetingId, attendee, iceServers, signalingUrl }

    DA->>DA: new RTCPeerConnection({ iceServers })
    DA->>STUN: STUN Binding Request
    STUN-->>DA: Reflexive candidate
    DA->>CHIME: Send SDP offer via signaling WebSocket
    CHIME-->>DA: SDP answer

    Note over PA,DA: ICE connectivity checks between participants

    CHIME->>PA: ICE candidate from doctor (via signaling)
    CHIME->>DA: ICE candidate from patient (via signaling)
    PA->>DA: ICE connectivity check (STUN Binding Request peer-to-peer)

    alt P2P path succeeds (both on same network or STUN works)
        DA-->>PA: ICE connectivity check response
        PA->>PA: Nominate host/srflx candidate pair
    else P2P fails (symmetric NAT) — relay via TURN
        PA->>TURN: TURN ChannelBind (bind channel to doctor's relay address)
        TURN-->>PA: Channel bound
        PA->>TURN: Send media via TURN relay channel
        TURN->>DA: Forward relayed media
    end

    Note over PA,DA: Media streams established — session is ACTIVE

    VS->>VS: Detect both attendees have media (Chime webhook: AttendeePresence)
    VS->>SQS: Publish ConsultationStarted event
    SQS-->>EHR: ConsultationStarted → open encounter in EHR
    SQS-->>NS: ConsultationStarted → suppress further reminders

    VS->>VS: Start BandwidthMonitor (poll Chime metrics every 5s)

    loop Every 5 seconds during session
        VS->>CHIME: GetAttendee (network quality stats)
        CHIME-->>VS: { audioPacketLossPercent, audioDecoderLoss, videoSendBitrate }
        alt packet loss > 15% or bitrate < 200Kbps
            VS->>SQS: Publish Video.QualityDegraded event
            VS->>PA: WebSocket push: { type: "QUALITY_WARNING", suggestion: "reduce_video_quality" }
        end
    end

    Note over PA,DA: Doctor ends session

    DA->>VS: DELETE /video-rooms/{roomId} (or participant leaves)
    VS->>CHIME: DeleteAttendee({ MeetingId, AttendeeId: doctorAttendeeId })
    VS->>CHIME: DeleteMeeting({ MeetingId }) — if no other attendees
    VS->>VS: Set endedAt = now(), calculate durationSeconds
    VS->>VS: Update VideoSession status to ENDED

    alt recordingEnabled == true
        VS->>VS: Trigger recording finalisation (Chime MediaCapture pipeline)
        VS->>VS: Upload encrypted recording to S3 (SSE-KMS)
        VS->>VS: Set recordingS3Uri
    end

    VS->>SQS: Publish ConsultationEnded event\n{ consultationId, durationSeconds, terminatedBy: "DOCTOR", recordingUri }
    SQS-->>EHR: Close encounter, attach recording URI
    SQS-->>NS: Send post-consultation follow-up to patient
```

---

## E-Prescription DEA EPCS Compliance

This sequence covers the full e-prescribing workflow for a Schedule II controlled substance, including DEA EPCS two-factor authentication, PDMP query, Surescripts routing, and pharmacy confirmation.

```mermaid
sequenceDiagram
    autonumber
    participant DA as Doctor App
    participant RXS as PrescriptionService
    participant EPCS as DEA EPCS Provider\n(identity proofing)
    participant HSM as Hardware Security Module\n(signing key)
    participant PDMP as State PDMP\n(PMP InterConnect)
    participant SURES as Surescripts Network
    participant PHARM as Pharmacy System\n(NCPDP SCRIPT)
    participant EHR as EHRService
    participant SQS as SQS / EventBridge
    participant AUDIT as AuditService

    Note over DA,AUDIT: Clinician initiates prescription during active consultation

    DA->>RXS: POST /prescriptions\n{ consultationId, medication: { name, ndc, schedule: "II", qty: 30, directions }, pharmacyNcpdpId }
    RXS->>RXS: Validate consultation is IN_SESSION or COMPLETED
    RXS->>RXS: Validate doctor.epcsEnabled == true
    RXS->>RXS: Validate doctor.deaCredential is valid and not expired
    RXS->>RXS: Validate doctor is licensed in patient's state

    RXS->>EPCS: POST /identity/verify\n{ doctorId, deaNumber }
    EPCS-->>RXS: { verified: true, identityProofingLevel: "IAL2", expiresAt }

    Note over RXS,PDMP: PDMP query mandatory for Schedule II–V

    RXS->>PDMP: POST /query\n{ patientId, dob, state, deaNumber }
    PDMP-->>RXS: { pdmpQueryId, prescriptionHistory: [...], alerts: [] }

    RXS->>RXS: Evaluate PDMP alerts
    alt Opioid overuse alert detected
        RXS->>DA: { alert: "PDMP_HIGH_RISK", prescriptionHistory, requiresOverride: true }
        DA->>RXS: POST /prescriptions/{id}/override\n{ clinicalJustification: "...", overrideBy: doctorId }
        RXS->>AUDIT: Log override with justification
    end

    RXS->>RXS: Check drug-drug interactions (against patient medication list in EHR)
    RXS->>EHR: GET /patients/{id}/medications (active list)
    EHR-->>RXS: [ { medicationName, ndc, startDate } ]
    RXS->>RXS: Run interaction check (local formulary DB)
    alt Interaction found
        RXS->>DA: { alert: "DRUG_INTERACTION", severity: "MAJOR", interactingDrug, recommendation }
        DA->>RXS: POST /prescriptions/{id}/acknowledge-interaction\n{ acknowledged: true, clinicalReason }
    end

    RXS->>RXS: Create Prescription record with status = DRAFT
    RXS->>RXS: Set pdmpQueryId, save prescription

    Note over DA,HSM: Two-factor authentication required for Schedule II signing (DEA 21 CFR 1311.120)

    RXS->>DA: Challenge: { prescriptionId, challengeType: "TOTP_PLUS_HARDWAREKEY" }
    DA->>DA: Generate TOTP code from authenticator app
    DA->>DA: Sign challenge with hardware security key (FIDO2)
    DA->>RXS: POST /prescriptions/{id}/sign\n{ totpCode: "123456", hardwareKeyAssertion: "..." }

    RXS->>EPCS: POST /mfa/verify\n{ doctorId, totpCode, hardwareKeyAssertion }
    EPCS-->>RXS: { mfaVerified: true, auditToken: "..." }

    RXS->>HSM: Sign prescription payload (SHA-256 + RSA-2048)\n{ prescriptionId, ndc, qty, directions, deaNumber, timestamp }
    HSM-->>RXS: { signature, signingKeyId, signedAt }

    RXS->>RXS: Update status = SIGNED, store signature, set signedAt
    RXS->>AUDIT: Log prescription signed\n{ prescriptionId, doctorId, mfaMethod, signingKeyId, timestamp }

    Note over RXS,SURES: Route prescription to pharmacy via Surescripts

    RXS->>SURES: POST /newrx (NCPDP SCRIPT 2017071 NewRx message)\n{ prescriptionId, patient: { name, dob, address }, doctor: { npi, dea, address }, medication, pharmacy: { ncpdpId } }
    SURES->>SURES: Validate NCPDP message format
    SURES->>SURES: Look up pharmacy routing table by NCPDP ID
    SURES-->>RXS: { surescriptsMessageId, status: "ACCEPTED", timestamp }

    RXS->>RXS: Update status = TRANSMITTED, set transmittedAt, surescriptsMessageId
    RXS->>SQS: Publish PrescriptionIssued event
    SQS-->>EHR: Attach prescription to encounter
    SQS-->>NS: Notify patient "Your prescription has been sent to [pharmacy]"

    Note over SURES,PHARM: Surescripts routes to pharmacy system

    SURES->>PHARM: Forward NewRx message (NCPDP SCRIPT)
    PHARM->>PHARM: Adjudicate with insurance (real-time benefit check)

    alt Pharmacy sends RxChangeRequest (quantity/substitution)
        PHARM->>SURES: RxChangeRequest
        SURES->>RXS: POST /prescriptions/{id}/change-request\n{ changeType: "SUBSTITUTION", proposedNdc }
        RXS->>DA: Notify of change request, await approval
        DA->>RXS: POST /prescriptions/{id}/change-request/approve
        RXS->>SURES: RxChangeResponse (Approved)
        SURES->>PHARM: Forward approval
    end

    PHARM->>SURES: RxFill (dispense confirmation)
    SURES->>RXS: POST /webhook/rxfill\n{ surescriptsMessageId, dispensedAt, dispensedQty, pharmacistId }
    RXS->>RXS: Update status = DISPENSED, set dispensedAt
    RXS->>SQS: Publish Prescription.Dispensed event
    SQS-->>NS: Notify patient "Prescription ready for pickup"
    RXS->>AUDIT: Log dispense confirmation
```

---

## Insurance Claims Processing

This sequence covers the complete revenue cycle from consultation completion through claim generation, eligibility verification, 837P submission, 835 remittance, and payment posting.

```mermaid
sequenceDiagram
    autonumber
    participant BS as BillingService
    participant EHR as EHRService
    participant PVERIFY as pVerify\n(Eligibility API)
    participant CHANGE as Change Healthcare\n(Clearinghouse)
    participant PAYER as Insurance Payer\n(Adjudication System)
    participant SQS as SQS / EventBridge
    participant NS as NotificationService
    participant PP as PatientPortalService
    participant AUDIT as AuditService

    Note over BS,AUDIT: Triggered by ConsultationEnded event

    SQS->>BS: Consume ConsultationEnded\n{ consultationId, appointmentId, durationSeconds }
    BS->>EHR: GET /consultations/{id}/billing-codes\n{ cptCodes, icd10Codes, modifiers, placeOfService }
    EHR-->>BS: { cptCodes: ["99213", "G2012"], icd10Codes: ["J06.9"], placeOfService: "02", soapNoteHash }

    BS->>BS: Validate CPT/ICD-10 code pairing (NCCI edits)
    BS->>BS: Apply place of service code 02 (telehealth)
    BS->>BS: Calculate initial billed amount (fee schedule lookup)

    Note over BS,PVERIFY: Real-time eligibility verification

    BS->>EHR: GET /patients/{id}/insurance (primary + secondary)
    EHR-->>BS: { memberId, payerId, groupNumber, planName }
    BS->>PVERIFY: POST /eligibility\n{ payerId, memberId, serviceDate, serviceType: "telehealth" }
    PVERIFY-->>BS: { eligible: true, copay: 25.00, deductible: { met: 800, remaining: 200 }, priorAuthRequired: false, planType: "PPO" }

    alt Prior auth required
        BS->>BS: Flag claim for prior auth workflow
        BS->>NS: Notify care team to obtain prior auth
        Note over BS: Claim held in DRAFT until PA approved
    end

    BS->>BS: Create InsuranceClaim record with status = DRAFT
    BS->>BS: Calculate expected allowed amount from fee schedule

    Note over BS,CHANGE: Generate and submit 837P professional claim

    BS->>BS: Build X12 837P transaction set\n{ ISA, GS, ST segments, CLM01=claimId, CLM05=02 (telehealth), NM1*85=billing provider NPI, SV1=CPT codes+charges }
    BS->>CHANGE: POST /claims/837p\n(X12 EDI 837P payload)
    CHANGE->>CHANGE: Validate X12 format (ISA/GS/ST segments)
    CHANGE->>CHANGE: Apply payer-specific edits (formulary, referral requirements)

    alt X12 validation failure (TA1 / 999 rejection)
        CHANGE-->>BS: 999 Functional Acknowledgement\n{ ackCode: "R", errorCode: "004010X098A1", errorSegment }
        BS->>BS: Parse rejection reason
        BS->>BS: Correct claim (flag for billing specialist if complex)
        BS->>CHANGE: Resubmit corrected 837P
    end

    CHANGE-->>BS: 999 Acknowledgement (accepted)\n{ clearinghouseTrackingId, receivedAt }
    BS->>BS: Update claim status = SUBMITTED, store trackingId
    BS->>SQS: Publish InsuranceClaimSubmitted event
    BS->>AUDIT: Log claim submission

    Note over CHANGE,PAYER: Clearinghouse routes to payer

    CHANGE->>PAYER: Route 837P to payer adjudication system
    PAYER->>PAYER: Adjudicate claim (member lookup, benefit check, NCCI, LCD/NCD edits)

    alt Claim adjudicated — approved
        PAYER-->>CHANGE: 835 Remittance Advice\n{ claimId, allowedAmount: 95.00, paidAmount: 70.00, adjustmentCodes: ["CO45","PR2"], checkEftNumber }
    else Claim denied
        PAYER-->>CHANGE: 835 with denial\n{ claimId, adjudicationStatus: "DENIED", adjustmentReason: "CO4 - deductible not met", paidAmount: 0 }
    end

    CHANGE->>BS: POST /webhook/835\n(X12 835 ERA payload)

    Note over BS: Process 835 Electronic Remittance Advice

    BS->>BS: Parse X12 835 (CLP, SVC, CAS segments)
    BS->>BS: Match ERA to claim by clearinghouseTrackingId
    BS->>BS: Apply payment: paidAmount = 70.00
    BS->>BS: Apply adjustments: CO45 (contractual) = 25.00, PR2 (coinsurance) = 0
    BS->>BS: Calculate patientResponsibility = 25.00 (copay)
    BS->>BS: Update claim status = PAID, set remittanceId, paidAt

    alt Claim denied
        BS->>BS: Update claim status = DENIED
        BS->>BS: Evaluate appeal eligibility (timely filing window, denial reason)
        alt Appealable denial
            BS->>BS: Create appeal record, status = DRAFT
            BS->>NS: Notify billing team of denial with recommended action
            Note over BS: Appeal workflow initiated separately
        else Non-appealable
            BS->>BS: Write off balance, apply CO adjustment
            BS->>BS: Update claim status = WRITTEN_OFF
        end
    end

    BS->>BS: Post payment to patient account
    BS->>SQS: Publish BillingCompleted event\n{ billingEventId, claimId, patientId, paidAmount, patientResponsibility, remittanceId }
    SQS-->>PP: PatientPortalService updates patient statement
    SQS-->>NS: Send EOB summary to patient (email/in-app, no PHI in SMS)
    BS->>AUDIT: Log payment posting with ERA reference
```

---

## Sequence Diagram Cross-References

| Sequence | Key SLO | Failure Modes Covered |
|---|---|---|
| WebRTC Video Consultation | Session established < 8 s; ICE completion < 3 s | STUN failure (fallback to TURN), bandwidth degradation, packet loss > 15% |
| E-Prescription DEA EPCS | Prescription transmitted < 30 s of clinician signature | PDMP timeout, EPCS outage, Surescripts rejection, pharmacy change request |
| Insurance Claims Processing | 837P submitted < 5 min of consultation end; ERA processed < 24 h | X12 validation failure, payer denial, clearinghouse downtime, ERA parsing error |

Detailed failure mode handling for each of these flows is documented in the `edge-cases/` directory.
