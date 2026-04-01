# Telemedicine Platform: Video Consultation Edge Cases

This document describes critical failure scenarios for WebRTC video consultations, detection mechanisms, and recovery procedures. Each scenario follows the format: Failure Mode → Impact → Detection → Mitigation → Recovery.

---

## Scenario 1: WebRTC ICE Negotiation Failure

**Failure Mode**: STUN/TURN servers are unreachable or return no valid ICE candidates within 15 seconds. Patient and clinician cannot establish peer connection.

**Symptoms**:
- Patient clicks "Join Session" button
- Video area remains blank
- Error message: "Connection failed. Unable to establish video. Please check your network."
- ICE connection state: `failed` (never reaches `connected` or `completed`)

**Impact** (Critical):
- Patient cannot join consultation; appointment unusable
- Clinician waiting indefinitely; resource waste
- Patient frustration; may abandon telehealth platform
- Potential no-show recorded if patient gives up

**Detection**:
```javascript
// RoomManager monitors ICE state
peerConnection.onconnectionstatechange = () => {
    if (peerConnection.connectionState === 'failed') {
        recordMetric('ice_negotiation_failed');
        alert('ICE_FAILURE');
        publishEvent({
            eventType: 'ice_negotiation_failed',
            appointmentId, 
            timestamp: now(),
            iceStats: getRTCStats()
        }, 'CRITICAL');
    }
};

// Timeout guard (15 seconds)
setTimeout(() => {
    if (peerConnection.connectionState !== 'connected' 
        && peerConnection.connectionState !== 'completed') {
        triggerICEFailureRecovery();
    }
}, 15000);
```

**Root Causes**:
1. **STUN server unreachable** (2-5% of cases)
   - Firewall blocks UDP port 3478
   - Regional DNS resolution failure
   - Google STUN server rate-limited
   
2. **TURN server unreachable** (3-5% of cases)
   - Corporate firewall blocks UDP/TCP 443
   - TURN credential expired (TTL > 15 minutes)
   - Coturn server process crashed
   
3. **Network NAT incompatibility** (5-10% of cases)
   - Symmetric NAT blocks peer-to-peer without TURN relay
   - ISP carrier-grade NAT (CGNAT) prevents port mapping

4. **Browser API error** (0.5% of cases)
   - RTCPeerConnection not supported (old browser)
   - Permission denied for getUserMedia

**Mitigation**:
1. **Primary STUN servers** (instant, no relay)
   - Google: stun.l.google.com:19302
   - Mozilla: stun1.l.google.com:19302
   
2. **Fallback TURN servers** (relay, higher latency)
   - AWS TURN: turnserver-us-east-1.chime.aws.com (credentials from ICEServerProvider)
   - Coturn cluster (self-hosted or Twilio): fallback-turn-1.telemedicine.local
   
3. **ICE candidate filtering**
   - Require at least one TURN candidate within 5 seconds
   - If only host candidates gathered (P2P), wait 3 more seconds for SRFLX
   - If no TURN candidates after 8 seconds, skip TURN and attempt P2P
   
4. **Credential refresh**
   - Request fresh TURN credentials every 10 minutes
   - Pre-fetch credentials 2 minutes before session start

**Recovery** (Auto):
```javascript
async function handleICEFailure() {
    // Step 1: Log event
    await auditLog('ice_negotiation_failure', {
        appointmentId,
        patient: patientId,
        clinician: clinicianId,
        timestamp: now()
    });
    
    // Step 2: Notify participant
    showErrorModal({
        title: 'Connection Failed',
        message: 'Attempting audio-only fallback...',
        retryCount: 0
    });
    
    // Step 3: Attempt audio-only fallback
    const audioOnlyConfig = {
        audio: true,
        video: false  // disable video
    };
    
    try {
        const newStream = await navigator.mediaDevices.getUserMedia(audioOnlyConfig);
        replaceTracks(newStream);
        
        // Re-create peer connection without video codecs
        await recreateRoomWithAudioOnly();
        
        showNotification('Video unavailable. Using audio-only mode.');
        
    } catch (audioError) {
        // Step 4: Audio-only also failed
        showErrorModal({
            title: 'Unable to Connect',
            message: 'Consultation cannot proceed. Please check your internet connection.',
            actionButton: 'Reschedule'
        });
        
        // Notify clinician
        publishEvent({
            eventType: 'session_failed_audio_fallback_also_failed',
            appointmentId,
            errorCode: audioError.code
        }, 'CRITICAL');
        
        recordNoShow('network_failure', appointmentId);
    }
}
```

**Clinician Experience**:
- Receive system notification: "Patient unable to connect. Attempting to establish audio-only session..."
- 30-second timer displayed
- Option to "End Consultation" or "Wait for Audio Connection"
- If no connection after 30 seconds, appointment marked `abandoned`, refund triggered

**Patient Experience**:
- "Connecting..." spinner for 8 seconds
- Transition to audio-only mode automatically
- Explanation: "Video is unavailable due to network conditions. You can still consult by audio."
- Continue/Reschedule button

**Recovery Time**: 10-15 seconds (average) to fall back to audio-only

---

## Scenario 2: Network Drop Mid-Consultation

**Failure Mode**: Patient's or clinician's network connection is lost during active video session (e.g., WiFi disconnects, mobile data drops). RTCPeerConnection state changes from `connected` to `disconnected` or `failed`.

**Symptoms**:
- Video/audio stops abruptly
- Frozen video frame for 5+ seconds
- Error: "Connection lost. Reconnecting..." or "Your network is unstable."
- Other participant hears silence or experiences audio/video lag

**Impact** (Critical):
- Active consultation interrupted mid-diagnosis
- Clinical note being typed lost (if not auto-saved)
- Patient/clinician anxiety; perception of poor service
- If reconnection fails after 5 minutes, appointment marked `abandoned`

**Detection**:
```javascript
peerConnection.onconnectionstatechange = () => {
    const state = peerConnection.connectionState;
    
    if (state === 'disconnected') {
        logger.warn('Network disconnected', {appointmentId, timestamp: now()});
        startReconnectTimer();
        publishEvent('network_drop_detected', {
            appointmentId,
            lostParticipant: 'patient' or 'clinician',
            connectionState: state
        }, 'HIGH');
        
    } else if (state === 'failed') {
        logger.error('Network connection failed', {appointmentId});
        cancelReconnectTimer();
        initiateGracefulShutdown();
    }
};

// Monitor network quality degradation (precursor to drop)
function monitorNetworkQuality() {
    const stats = getRTCStats();
    if (stats.inboundVideoLoss > 30% || stats.outboundBitrate < 50_000) {
        logger.warn('Network degraded', {stats, appointmentId});
        publishEvent('network_degradation_warning', {appointmentId, stats}, 'MEDIUM');
    }
}
```

**Root Causes**:
1. **WiFi disconnection** (40% of mobile cases)
   - User walks out of WiFi range
   - Router reboots
   - WiFi router power loss
   - ISP outage
   
2. **Mobile network drop** (30% of mobile cases)
   - Handoff between cell towers fails
   - Network congestion (LTE → 3G fallback)
   - User enters tunnel/elevator (no signal)
   
3. **VPN/Proxy failover** (15% of corporate cases)
   - VPN reconnects to different server
   - Proxy session timeout
   - BGP route flapping
   
4. **Firewall rules** (10% of cases)
   - Session-based firewall closes connection
   - Stateless firewall drops idle traffic
   - Rate limiting trigger

**Mitigation**:
1. **5-Minute Reconnection Grace Period**
   - When RTCPeerConnection enters `disconnected` state, show "Reconnecting..." message
   - Automatically attempt to re-establish peer connection every 2 seconds
   - Max 150 reconnection attempts over 5 minutes
   
2. **Auto-Save Consultation Data** (every 30 seconds)
   - SOAP note text auto-saved to database
   - Vital signs data persisted
   - On reconnect, resume from last save point
   
3. **Participant Notifications**
   - Patient: "Your connection was lost. Attempting to reconnect..." + countdown timer
   - Clinician: "{Patient} connection lost. Will attempt reconnect for 5 minutes. {X} seconds remaining."
   
4. **ICE Candidate Refresh**
   - When disconnect detected, request fresh ICE candidates
   - Try fallback TURN servers not previously used
   
5. **Graceful Degradation**
   - If video drops but audio recovers, disable video and continue audio-only
   - If both drop, wait for reconnection; do not end session immediately

**Recovery** (Semi-Automatic):
```javascript
async function handleNetworkDrop() {
    const startTime = now();
    const maxWaitTime = 5 * 60 * 1000;  // 5 minutes
    let reconnectAttempts = 0;
    
    logger.info('Network drop recovery initiated', {appointmentId, startTime});
    
    // Notify both participants
    publishUIUpdate({
        type: 'network_disconnected',
        message: 'Reconnecting...',
        showCountdown: true,
        maxWaitTime
    });
    
    // Attempt reconnection loop
    const reconnectInterval = setInterval(async () => {
        reconnectAttempts++;
        
        // Check if peer connection has recovered
        if (peerConnection.connectionState === 'connected') {
            logger.info('Network recovered', {
                appointmentId,
                reconnectAttempts,
                elapsedTime: now() - startTime
            });
            clearInterval(reconnectInterval);
            publishUIUpdate({type: 'network_recovered'});
            resumeConsultation();
            return;
        }
        
        // Attempt fresh connection
        try {
            const freshIceServers = await iceServerProvider.getICEServers('primary');
            peerConnection.setConfiguration({iceServers: freshIceServers});
            
            // Restart ICE gathering
            peerConnection.restartIce();
            
            logger.debug('ICE restart initiated', {reconnectAttempts});
            
        } catch (error) {
            logger.warn('Reconnect attempt failed', {reconnectAttempts, error});
        }
        
        // Check timeout
        if (now() - startTime > maxWaitTime) {
            clearInterval(reconnectInterval);
            handleReconnectionTimeout();
        }
    }, 2000);  // Retry every 2 seconds
}

function handleReconnectionTimeout() {
    logger.error('Network recovery timeout', {appointmentId});
    
    // End session gracefully
    publishEvent('session_abandoned_network_timeout', {
        appointmentId,
        reason: 'Network disconnection >5 minutes'
    }, 'HIGH');
    
    // Notify participants
    publishUIUpdate({
        type: 'session_ended',
        title: 'Session Ended',
        message: 'Your connection could not be restored. Please contact support to reschedule.',
        actionButton: 'Reschedule Appointment'
    });
    
    // Mark appointment
    updateAppointmentStatus(appointmentId, 'abandoned');
    
    // Patient refund
    initiateRefund(appointmentId, 'technical_failure');
}

async function resumeConsultation() {
    // Retrieve last saved SOAP note
    const lastSave = await getLastSavedSOAP(consultationId);
    
    // Reload SOAP editor with saved text
    loadSOAPNote(lastSave.content);
    
    // Notify clinician
    showNotification({
        type: 'success',
        message: 'Connection restored. SOAP note restored from last save.',
        autoDismiss: 3000
    });
    
    // Reset quality monitoring
    bandwidthMonitor.reset();
}
```

**User Experience**:
- **During Drop** (first 30 seconds):
  - Video/audio freezes
  - "Reconnecting..." modal appears with 30-second countdown
  - User can see elapsed time
  
- **If Recovered** (before 5 minutes):
  - "Connection restored" toast notification
  - Consultation resumes seamlessly
  - SOAP note pre-filled from auto-save
  
- **If Not Recovered** (after 5 minutes):
  - "Unable to reconnect. Appointment ending." modal
  - Option to reschedule
  - Refund processed automatically

**Packet Loss Threshold**:
- Detect network drop when packet loss > 40% for 2+ consecutive second
- Audio becomes choppy at 5% loss; video freezes at 30%+ loss

**Recovery Time**: Typically <10 seconds if participant's network recovers; max 5 minutes before auto-end

---

## Scenario 3: Audio-Video Desynchronization

**Failure Mode**: Audio and video streams drift out of sync. Patient hears audio >500ms before/after seeing mouth movement. Caused by jitter buffer misalignment or codec latency differences.

**Symptoms**:
- Noticeable lip sync issues ("dubbing" effect)
- Patient/clinician comments: "I can't understand you" or "You're cutting off"
- Quality metrics show jitter >100ms, large variance
- A/V drift detected by browser's AV sync monitor

**Impact** (High):
- Poor user experience; affects communication quality
- Clinician cannot assess patient facial expressions accurately
- Patient anxiety; reduced confidence in diagnosis
- Does not require session termination; workaround available

**Detection**:
```javascript
class AVSyncMonitor {
    monitorAVDrift() {
        setInterval(() => {
            const videoLatency = this.getVideoFrameLatency();  // ms
            const audioLatency = this.getAudioFrameLatency();  // ms
            const drift = Math.abs(videoLatency - audioLatency);
            
            if (drift > 500) {
                logger.warn('A/V drift detected', {
                    drift,
                    videoLatency,
                    audioLatency,
                    appointmentId
                });
                
                publishMetric('av_sync_drift', drift);
                publishEvent('av_desync_high', {
                    drift,
                    appointmentId
                }, 'HIGH');
                
                this.attemptAVSyncRecalibration();
            }
        }, 1000);  // Check every 1 second
    }
    
    getVideoFrameLatency() {
        const stats = this.peerConnection.getStats();
        let latency = 0;
        
        stats.forEach(report => {
            if (report.type === 'inbound-rtp' && report.mediaType === 'video') {
                // Calculate E2E latency from jitterBufferDelay
                latency = report.jitterBufferDelay * 1000;  // Convert to ms
            }
        });
        
        return latency;
    }
    
    getAudioFrameLatency() {
        const stats = this.peerConnection.getStats();
        let latency = 0;
        
        stats.forEach(report => {
            if (report.type === 'inbound-rtp' && report.mediaType === 'audio') {
                latency = report.jitterBufferDelay * 1000;
            }
        });
        
        return latency;
    }
}
```

**Root Causes**:
1. **Jitter buffer misalignment** (50% of cases)
   - Audio jitter buffer set to 100ms, video to 200ms
   - Network packet reordering causes latency variance
   - Browser WebRTC engine underestimates jitter
   
2. **Codec latency difference** (30% of cases)
   - Opus codec (audio) has 20ms frame, VP9 (video) has 33ms frames
   - Platform-specific codec optimization delay
   
3. **Packet loss retransmission** (15% of cases)
   - Audio packet lost, retransmitted, causes audio delay
   - Video I-frame request causes video keyframe latency
   
4. **Device buffer differences** (5% of cases)
   - Mobile phone audio buffer 40ms, video buffer 80ms
   - Microphone hardware latency 10-30ms variance

**Mitigation**:
1. **Adaptive Jitter Buffer Recalibration** (automatic)
   ```javascript
   async function recalibrateJitterBuffer() {
       // Pause media for 2 seconds
       audioTrack.enabled = false;
       videoTrack.enabled = false;
       
       // Reset jitter buffers
       peerConnection.restartIce();
       
       // Wait for buffers to re-equilibrate
       await sleep(2000);
       
       // Re-enable media
       audioTrack.enabled = true;
       videoTrack.enabled = true;
       
       logger.info('Jitter buffer recalibration initiated', {appointmentId});
   }
   ```
   
2. **Manual A/V Sync Adjustment** (if auto fails)
   - UI slider: "Audio Timing" (±500ms adjustment)
   - Clinician can shift audio earlier/later
   - Adjustment persisted for rest of session
   
3. **Codec Adjustment**
   - Prefer Opus (audio) + H.264 (video) for consistent frame timing
   - Avoid VP9 (high latency variance)
   - Set VP8 max frame rate = audio frame rate (50fps = 50fps audio)
   
4. **Network Optimization**
   - Enable FEC (Forward Error Correction) for audio to avoid retransmission
   - Increase video keyframe interval (2-4 seconds) to prevent jitter

**Recovery**:
```javascript
async function handleAVDesync(drift) {
    // Step 1: Notify participants (non-blocking)
    publishUIUpdate({
        type: 'av_sync_adjustment',
        message: 'Synchronizing audio and video...',
        duration: 3000
    });
    
    // Step 2: Attempt automatic recalibration
    try {
        await recalibrateJitterBuffer();
        
        // Re-measure drift after 3 seconds
        await sleep(3000);
        const newDrift = measureAVDrift();
        
        if (newDrift < 300) {
            logger.info('A/V sync recovered', {
                originalDrift: drift,
                newDrift,
                appointmentId
            });
            publishUIUpdate({type: 'av_sync_resolved'});
            return;
        }
    } catch (error) {
        logger.warn('Automatic A/V recalibration failed', {error});
    }
    
    // Step 3: Show manual adjustment UI
    showAVSyncAdjustmentPanel({
        title: 'Audio/Video Out of Sync',
        message: 'Use the slider below to adjust audio timing.',
        sliderRange: [-500, 500],  // milliseconds
        sliderStep: 50,
        onAdjustment: (offsetMs) => {
            applyAudioDelay(offsetMs);
            saveAVSyncOffset(appointmentId, offsetMs);
        }
    });
}

function applyAudioDelay(offsetMs) {
    // Use Web Audio API to introduce delay
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const delayNode = audioContext.createDelay(offsetMs / 1000);
    delayNode.delayTime.value = offsetMs / 1000;
    
    // Route remote audio through delay node
    remoteAudioStream.getAudioTracks().forEach(track => {
        const source = audioContext.createMediaStreamAudioSource(remoteAudioStream);
        source.connect(delayNode);
        delayNode.connect(audioContext.destination);
    });
}
```

**User-Facing Action**:
- Auto-correction attempts silently
- If manual adjustment needed, slider appears on video area
- Preset buttons: "Correct Audio Timing" (auto), "Adjust Manually"
- Adjustment persists for rest of session

**Recovery Time**: 3-5 seconds for automatic recalibration; manual adjustment <1 second

---

## Scenario 4: Severe Bandwidth Degradation

**Failure Mode**: Network bandwidth drops below 200 Kbps (minimum for VP9 video). Video codec cannot maintain frame rate. Bitrate estimation drops from 1 Mbps to 150 Kbps within 10 seconds.

**Symptoms**:
- Video becomes pixelated/blocky
- Frame rate drops to 2-5 fps (very choppy)
- Audio continues (usually)
- Subjective quality: "looks like a 1990s webcam"

**Impact** (High):
- Poor diagnostic capability; clinician cannot see patient clearly
- Delays consultation; frustration on both ends
- Temporary; usually recovers within 1-2 minutes
- Mitigation: automatic video downgrade to QCIF (352x240) or audio-only

**Detection**:
```javascript
class BandwidthMonitor {
    monitorBandwidth() {
        const stats = this.peerConnection.getStats();
        let videoInboundBitrate = 0;
        
        stats.forEach(report => {
            if (report.type === 'inbound-rtp' && report.mediaType === 'video') {
                const bytes = report.bytesReceived;
                const now = report.timestamp;
                
                if (this.lastByteCount !== null) {
                    const bitrate = (bytes - this.lastByteCount) / 
                                   ((now - this.lastTimestamp) / 1000) * 8;
                    videoInboundBitrate = bitrate;
                }
                
                this.lastByteCount = bytes;
                this.lastTimestamp = now;
            }
        });
        
        // Trigger adaptation at 200 Kbps threshold
        if (videoInboundBitrate < 200_000) {
            logger.warn('Bandwidth degraded', {
                bitrate: videoInboundBitrate,
                appointmentId
            });
            
            this.triggerQualityAdaptation('degrade_video');
        } else if (videoInboundBitrate > 500_000 && this.isCurrentlyDegraded) {
            logger.info('Bandwidth recovered', {bitrate: videoInboundBitrate});
            this.triggerQualityAdaptation('upgrade_video');
        }
    }
    
    triggerQualityAdaptation(action) {
        if (action === 'degrade_video') {
            // Reduce resolution to QCIF (352x240)
            this.downgradeVideoResolution('352x240');
            
            // Reduce frame rate to 15fps
            this.downgradeFrameRate(15);
            
            // Switch to more efficient codec (H.264 over VP9)
            this.switchCodec('H264');
            
            publishEvent('video_quality_degraded', {
                action, appointmentId
            }, 'MEDIUM');
            
            showNotification(
                'Video quality reduced due to network conditions. Audio continues normally.'
            );
            
        } else if (action === 'upgrade_video') {
            this.upgradeVideoResolution('640x480');
            this.upgradeFrameRate(30);
            
            publishEvent('video_quality_upgraded', {
                action, appointmentId
            }, 'INFO');
            
            showNotification('Video quality improved.');
        }
    }
}
```

**Root Causes**:
1. **WiFi interference** (40% of cases)
   - Neighboring WiFi networks on same channel
   - Microwave oven interference
   - Metal obstacles (building structure)
   
2. **Network congestion** (30% of cases)
   - ISP shared bandwidth usage spike
   - Other devices on network downloading
   - Mobile network handoff to congested cell tower
   
3. **Distance/Signal Degradation** (20% of cases)
   - Mobile user moves away from WiFi router
   - Mobile signal weakens (distance from tower)
   - Attenuation through walls/doors
   
4. **ISP/Carrier limits** (10% of cases)
   - Throttling triggered (data cap)
   - QoS policy deprioritizes video
   - Peer-to-peer traffic shaping

**Mitigation**:
1. **Automatic Quality Downgrade Ladder**
   ```
   Normal: 640x480 @ 30fps, VP9 codec, 500-1000 Kbps
      ↓ (if <300 Kbps)
   QCIF: 352x240 @ 15fps, H.264 codec, 150-200 Kbps
      ↓ (if <100 Kbps)
   Audio-Only: disable video, audio-only mode
   ```
   
2. **Perceptual Quality Maintenance**
   - Prioritize frame rate over resolution (choppy 640x480 worse than smooth 352x240)
   - Maintain audio quality at all costs
   - Disable screen sharing if bandwidth <300 Kbps
   
3. **User Notification**
   - "Video quality reduced. Network conditions improving..." (transient)
   - "Video disabled. Using audio-only mode." (persistent)
   - Invite user to improve WiFi (move closer to router, switch channel)

**Recovery**:
```javascript
async function handleBandwidthDegradation() {
    logger.warn('Bandwidth degradation detected', {appointmentId});
    
    // Step 1: Auto-degrade to QCIF
    await downgradeVideoToQCIF();
    
    // Show UI notification with bandwidth info
    showBandwidthNotification({
        type: 'degraded',
        currentBitrate: 180,  // Kbps
        suggestedAction: 'Move closer to WiFi router',
        recoveryTime: '1-2 minutes expected'
    });
    
    // Step 2: Monitor for recovery
    const monitorInterval = setInterval(async () => {
        const bitrate = await estimateBitrate();
        
        if (bitrate > 400_000 && isCurrentlyInQCIF) {
            // Bandwidth recovered; upgrade back to normal
            logger.info('Bandwidth recovered', {bitrate, appointmentId});
            await upgradeVideoToNormal();
            
            clearInterval(monitorInterval);
            showNotification('Video quality restored.');
        }
    }, 5000);  // Check every 5 seconds
    
    // Timeout: if not recovered after 5 minutes, switch to audio-only
    setTimeout(() => {
        clearInterval(monitorInterval);
        
        const bitrate = estimateBitrate();
        if (bitrate < 200_000) {
            logger.warn('Persistent low bandwidth; switching to audio-only', {
                bitrate,
                appointmentId
            });
            
            switchToAudioOnly();
            
            showBandwidthNotification({
                type: 'severe',
                message: 'Video disabled due to persistent network issues. You can continue by audio.',
                showNetworkDiagnostics: true
            });
        }
    }, 5 * 60 * 1000);  // 5 minutes
}

async function downgradeVideoToQCIF() {
    const constraints = {
        width: { ideal: 352 },
        height: { ideal: 240 },
        frameRate: { ideal: 15 }
    };
    
    const videoTrack = localStream.getVideoTracks()[0];
    await videoTrack.applyConstraints(constraints);
    
    logger.info('Video downgraded to QCIF', {appointmentId});
}

async function upgradeVideoToNormal() {
    const constraints = {
        width: { ideal: 640 },
        height: { ideal: 480 },
        frameRate: { ideal: 30 }
    };
    
    const videoTrack = localStream.getVideoTracks()[0];
    await videoTrack.applyConstraints(constraints);
    
    logger.info('Video upgraded to normal', {appointmentId});
}

function switchToAudioOnly() {
    localStream.getVideoTracks().forEach(track => {
        track.enabled = false;
    });
    
    // Notify other participant
    publishEvent('switched_to_audio_only', {
        appointmentId,
        reason: 'bandwidth_degradation'
    }, 'HIGH');
}
```

**Clinician Experience**:
- Video quality indicator (1-5 bars) shown on screen
- Auto-downgrade transparent; no action required
- If audio-only mode, clinician notified and can continue exam verbally
- Ability to ask patient to improve WiFi (e.g., "Can you move closer to your router?")

**Recovery Time**: 10-30 seconds for downgrade; 1-2 minutes for upgrade after bandwidth recovers

---

## Scenario 5: Browser WebRTC Incompatibility

**Failure Mode**: Patient uses unsupported/outdated browser version (e.g., Internet Explorer 11, Safari <11) that does not support WebRTC APIs (getUserMedia, RTCPeerConnection).

**Symptoms**:
- "Your browser is not supported" error message
- WebRTC features completely unavailable
- Patient cannot join video session
- No graceful fallback available

**Impact** (Medium):
- Patient cannot use telemedicine platform at all
- User frustration; loss of confidence
- Forces patient to reschedule or use different device
- Mitigation: clear error message with download link for compatible browser

**Detection**:
```javascript
function checkWebRTCSupport() {
    const isChromium = /Chrome|Chromium|CriOS/.test(navigator.userAgent);
    const isFirefox = /Firefox/.test(navigator.userAgent);
    const isSafari = /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent);
    const isEdge = /Edg/.test(navigator.userAgent);
    
    const browserVersion = parseBrowserVersion(navigator.userAgent);
    
    const requirements = {
        'Chrome': { minVersion: 44, supported: isChromium && browserVersion >= 44 },
        'Firefox': { minVersion: 40, supported: isFirefox && browserVersion >= 40 },
        'Safari': { minVersion: 11, supported: isSafari && browserVersion >= 11 },
        'Edge': { minVersion: 79, supported: isEdge && browserVersion >= 79 }
    };
    
    // Check getUserMedia support
    const hasGetUserMedia = !!(
        navigator.mediaDevices && 
        navigator.mediaDevices.getUserMedia
    );
    
    // Check RTCPeerConnection support
    const hasRTCPeerConnection = !!(
        window.RTCPeerConnection || 
        window.webkitRTCPeerConnection || 
        window.mozRTCPeerConnection
    );
    
    if (!hasGetUserMedia || !hasRTCPeerConnection) {
        return {
            supported: false,
            reason: 'WebRTC_NOT_SUPPORTED',
            message: 'Your browser does not support video conferencing.',
            suggestedBrowsers: ['Chrome 44+', 'Firefox 40+', 'Safari 11+', 'Edge 79+']
        };
    }
    
    return {
        supported: true,
        browser: Object.keys(requirements).find(b => requirements[b].supported),
        version: browserVersion
    };
}

// Run check on page load
window.addEventListener('load', () => {
    const support = checkWebRTCSupport();
    
    if (!support.supported) {
        logger.error('WebRTC not supported', {
            userAgent: navigator.userAgent,
            reason: support.reason
        });
        
        showBrowserCompatibilityError({
            title: 'Browser Not Compatible',
            message: support.message,
            suggestedBrowsers: support.suggestedBrowsers,
            downloadLinks: {
                'Chrome': 'https://www.google.com/chrome',
                'Firefox': 'https://www.mozilla.org/firefox',
                'Safari': 'https://www.apple.com/safari',
                'Edge': 'https://www.microsoft.com/edge'
            }
        });
        
        // Disable consultation join button
        document.getElementById('join-video-btn').disabled = true;
    }
});
```

**Root Causes**:
1. **Outdated browser** (80% of cases)
   - Windows 7 users stuck on IE 11 (no WebRTC)
   - Older MacOS with Safari <11
   - Corporate IT security policies prohibiting browser updates
   
2. **Mobile browser issues** (15% of cases)
   - Samsung Internet browser old version
   - In-app browser (Facebook/LinkedIn app) without WebRTC
   - Older Android default browser
   
3. **Accessibility software** (5% of cases)
   - Screen reader interferes with WebRTC
   - Browser extension blocks media APIs

**Mitigation**:
1. **Pre-Appointment Check** (done at registration)
   - Browser compatibility test page before booking
   - Clear messaging: "You need Chrome/Firefox/Safari/Edge for video"
   - Option to download compatible browser
   
2. **Error Page** (if accessed with unsupported browser)
   ```html
   <div class="browser-error">
     <h1>⚠️ Browser Not Compatible</h1>
     <p>Your browser does not support video conferencing.</p>
     <p>Please use one of these browsers:</p>
     <ul>
       <li><a href="https://google.com/chrome">Chrome 44+</a></li>
       <li><a href="https://mozilla.org/firefox">Firefox 40+</a></li>
       <li><a href="https://apple.com/safari">Safari 11+</a></li>
       <li><a href="https://microsoft.com/edge">Edge 79+</a></li>
     </ul>
     <button onclick="rescheduleAppointment()">Reschedule Appointment</button>
   </div>
   ```
   
3. **Support Resources**
   - Link to video tutorial: "How to install Chrome"
   - Help desk contact: "Call us if you need assistance"
   - Alternative: phone consultation option

**Recovery**:
1. User downloads compatible browser (2-10 minutes)
2. User returns to appointment link
3. Page detects browser support and enables consultation
4. Rejoin same appointment session (if within 2-hour window)

**User-Facing Action**:
- Clear error message with download links
- Estimated time to download/install: 3-5 minutes
- No penalty for browser upgrade (appointment rescheduled to same time)
- Clinician notified of patient browser issue; can provide alternative contact

**Recovery Time**: 5-20 minutes (browser download + installation)

---

## Scenario 6: TURN Server Regional Outage

**Failure Mode**: Fallback TURN (Traversal Using Relay NAT) server in patient's geographic region is unreachable or has degraded service. Direct P2P ICE candidates fail; only TURN relay available, and it's down.

**Symptoms**:
- Session stuck in `new` or `checking` ICE state
- Only `prflx` candidates (peer reflexive; failed P2P attempts)
- No TURN relay candidates gathered within 8 seconds
- After 15 seconds, ICE connection times out

**Impact** (Critical):
- Patient cannot join if TURN is required (behind corporate NAT, symmetric NAT)
- Fallback: fail to audio-only or session failure
- Affects regional users disproportionately
- Temporary outage (duration: minutes to hours)

**Detection**:
```javascript
class TURNHealthMonitor {
    async monitorTURNServers() {
        const turnServers = await getConfiguredTURNServers();
        
        for (const server of turnServers) {
            const isHealthy = await checkTURNHealth(server);
            
            if (!isHealthy) {
                logger.error('TURN server unhealthy', {
                    server: server.urls[0],
                    region: server.region,
                    timestamp: now()
                });
                
                publishEvent('turn_server_failure', {
                    server: server.urls[0],
                    region: server.region,
                    fallbackAvailable: turnServers.length > 1
                }, 'CRITICAL');
                
                // Mark server as unhealthy in cache
                markTURNServerUnhealthy(server.urls[0]);
            }
        }
    }
    
    async checkTURNHealth(server) {
        try {
            const testConnection = new RTCPeerConnection({
                iceServers: [server],
                iceTransportPolicy: 'relay'  // Force TURN
            });
            
            // Try to gather TURN candidates within 5 seconds
            const candidates = await gatherCandidatesWithTimeout(testConnection, 5000);
            
            if (candidates.filter(c => c.type === 'relay').length > 0) {
                // TURN relay candidate gathered; server is healthy
                testConnection.close();
                return true;
            } else {
                // No relay candidates; server may be unhealthy
                testConnection.close();
                return false;
            }
        } catch (error) {
            logger.error('TURN health check failed', {server, error});
            return false;
        }
    }
}

// Run health check every 30 seconds
setInterval(() => {
    new TURNHealthMonitor().monitorTURNServers();
}, 30 * 1000);
```

**Root Causes**:
1. **Coturn server crash** (50% of cases)
   - Process terminated (OOM, segfault)
   - Coturn service stopped/restarted
   - Port 3478/3479 (TURN) blocked by firewall misconfiguration
   
2. **AWS infrastructure failure** (30% of cases)
   - AWS TURN service regional outage
   - Network interface down
   - Load balancer unhealthy
   
3. **Network connectivity loss** (15% of cases)
   - BGP route failure to TURN server
   - ISP/CDN routing misconfiguration
   - DDoS attack on TURN server
   
4. **Credential expiry** (5% of cases)
   - TURN credential (username/password) expired
   - TURN credential not yet active (deployment lag)

**Mitigation**:
1. **Multi-Region TURN Cluster**
   - Primary: us-east-1.turn.telemedicine.local (Virginia)
   - Secondary: eu-west-1.turn.telemedicine.local (Ireland)
   - Tertiary: ap-southeast-1.turn.telemedicine.local (Singapore)
   - Quaternary: Twilio/Xirsys TURN as cloud fallback
   
2. **Intelligent Failover**
   ```javascript
   async function getTURNServersWithFailover(region) {
       const servers = [];
       
       // Try primary TURN server for region
       const primaryTURN = await getPrimaryTURNServer(region);
       if (await checkTURNHealth(primaryTURN)) {
           servers.push(primaryTURN);
       }
       
       // Try secondary (different region)
       const secondaryTURN = await getSecondaryTURNServer();
       if (await checkTURNHealth(secondaryTURN)) {
           servers.push(secondaryTURN);
       }
       
       // Try cloud provider TURN fallback
       const cloudTURN = await getCloudProviderTURN();
       if (await checkTURNHealth(cloudTURN)) {
           servers.push(cloudTURN);
       }
       
       if (servers.length === 0) {
           logger.error('All TURN servers unavailable', {region});
           return []  // No TURN; P2P will be attempted
       }
       
       return servers;
   }
   ```
   
3. **Graceful Degradation**
   - Attempt P2P first (host candidates)
   - Fallback to TURN relay if P2P fails
   - If no TURN available and NAT blocks P2P, fallback to audio-only
   
4. **Monitoring & Alerting**
   - TURN health check every 30 seconds
   - Alert when any TURN server fails
   - Auto-switch traffic to healthy server

**Recovery** (Automatic):
```javascript
async function handleTURNOutage() {
    logger.error('TURN server outage detected', {
        appointmentId,
        timestamp: now()
    });
    
    // Step 1: Invalidate unhealthy TURN servers
    const healthyTURNs = await getTURNServersWithFailover(region);
    
    if (healthyTURNs.length === 0) {
        // Step 2: No TURN available; attempt P2P
        logger.warn('No healthy TURN servers; attempting P2P only', {appointmentId});
        
        // Try P2P for 10 seconds
        const p2pSuccess = await attemptP2PWithTimeout(10000);
        
        if (!p2pSuccess) {
            // Step 3: P2P also failed; fallback to audio-only
            logger.info('P2P connection failed; switching to audio-only', {appointmentId});
            
            publishEvent('turn_outage_audio_fallback', {
                appointmentId,
                turnServersDown: true,
                p2pFailed: true
            }, 'CRITICAL');
            
            switchToAudioOnly();
            
            showNotification({
                type: 'warning',
                message: 'Video unavailable due to network configuration. Using audio-only mode.',
                actionButton: 'Reschedule'
            });
        }
    } else {
        // Healthy TURN servers available; refresh peer connection
        peerConnection.setConfiguration({iceServers: healthyTURNs});
        peerConnection.restartIce();
        
        logger.info('TURN servers refreshed with healthy alternatives', {
            appointmentId,
            healthyTURNCount: healthyTURNs.length
        });
    }
}
```

**Clinician & Patient Notification**:
- Automatic: system attempts recovery silently
- If audio-only required: "Video unavailable. You can continue by audio." message
- Appointment can proceed; no cancellation needed

**Recovery Time**: 10-30 seconds for failover; or 5-15 seconds for audio-only fallback

---

## Scenario 7: Session Recording Storage Failure

**Failure Mode**: Video recording cannot be uploaded to S3. Causes: S3 bucket full, KMS key access denied, network timeout, or S3 API error.

**Symptoms**:
- Consultation completes successfully
- Recording upload to S3 fails
- Video file lost permanently
- Compliance violation (no audit trail of consultation)

**Impact** (Critical):
- Regulatory risk: HIPAA requires record of consultation
- Medical-legal risk: no video evidence of what occurred
- Billing risk: cannot verify consultation occurred
- Compliance violation; potential audit finding

**Detection**:
```javascript
class SessionRecordingService {
    async uploadRecordingWithRetry(recordingFile, consultationId) {
        const maxRetries = 5;
        let attempt = 0;
        
        while (attempt < maxRetries) {
            try {
                const uploadResult = await this.uploadToS3(
                    recordingFile,
                    `consultations/${consultationId}.mp4`,
                    {
                        ServerSideEncryption: 'aws:kms',
                        SSEKMSKeyId: process.env.RECORDING_KMS_KEY_ARN
                    }
                );
                
                // Verify encryption
                const metadata = await s3Client.headObject({
                    Bucket: recordingBucketName,
                    Key: `consultations/${consultationId}.mp4`
                });
                
                if (metadata.ServerSideEncryption !== 'aws:kms') {
                    throw new Error('Recording not encrypted with KMS');
                }
                
                logger.info('Recording uploaded successfully', {
                    consultationId,
                    fileSize: uploadResult.fileSize,
                    s3Path: uploadResult.s3Path
                });
                
                // Create audit log entry
                await auditLog('recording_stored', {
                    consultationId,
                    s3Path: uploadResult.s3Path,
                    encrypted: true,
                    timestamp: now()
                });
                
                return uploadResult;
                
            } catch (error) {
                attempt++;
                
                logger.warn('Recording upload failed', {
                    consultationId,
                    attempt,
                    error: error.message,
                    code: error.code
                });
                
                if (error.code === 'AccessDenied') {
                    // KMS key access denied; not retryable
                    logger.error('KMS access denied for recording upload', {
                        consultationId,
                        kmsKeyArn: process.env.RECORDING_KMS_KEY_ARN
                    });
                    
                    publishEvent('recording_kms_access_denied', {
                        consultationId
                    }, 'CRITICAL');
                    
                    throw error;
                }
                
                if (error.code === 'ServiceUnavailable' || 
                    error.code === 'RequestTimeout') {
                    // Retryable; exponential backoff
                    const backoffMs = Math.pow(2, attempt) * 1000;  // 2s, 4s, 8s, 16s, 32s
                    logger.info('Retrying recording upload', {
                        backoffMs,
                        attempt
                    });
                    
                    await sleep(backoffMs);
                    continue;
                }
                
                if (attempt >= maxRetries) {
                    logger.error('Recording upload failed after max retries', {
                        consultationId,
                        maxRetries,
                        finalError: error.message
                    });
                    
                    publishEvent('recording_upload_failure_final', {
                        consultationId,
                        reason: error.message,
                        severity: 'CRITICAL'
                    }, 'CRITICAL');
                    
                    throw error;
                }
            }
        }
    }
}

// Catch unhandled upload failures
process.on('unhandledRejection', async (reason, promise) => {
    if (reason.message && reason.message.includes('recording_upload')) {
        logger.error('Unhandled recording upload error', {
            reason,
            promise
        });
        
        // Alert compliance team
        sendAlert({
            to: 'compliance@telemedicine.local',
            subject: 'CRITICAL: Recording Upload Failure',
            body: `Recording upload failed unexpectedly. Consultation: ${consultationId}. Manual intervention may be required.`,
            severity: 'CRITICAL'
        });
    }
});
```

**Root Causes**:
1. **S3 API errors** (40% of cases)
   - 503 Service Unavailable (S3 degradation)
   - 500 Internal Server Error
   - Rate limiting (SlowDown error)
   
2. **KMS key access** (30% of cases)
   - KMS key disabled or deleted
   - IAM role doesn't have kms:Decrypt permission
   - KMS key policy updated unexpectedly
   
3. **Network failure** (20% of cases)
   - Upload socket timeout (>30 seconds)
   - Network interface down during upload
   - S3 endpoint DNS resolution failure
   
4. **Storage quota** (10% of cases)
   - S3 bucket lifecycle policy deleted recordings prematurely
   - Regional storage quota exceeded
   - Unexpected large number of simultaneous uploads

**Mitigation**:
1. **Exponential Backoff Retry** (with jitter)
   - Attempt 1: immediate
   - Attempt 2: wait 2s + random(0-1s)
   - Attempt 3: wait 4s + random(0-1s)
   - Attempt 4: wait 8s + random(0-1s)
   - Attempt 5: wait 16s + random(0-1s)
   - Max 5 attempts over ~30 seconds
   
2. **Fallback Storage** (if S3 fails)
   - Store recording in PostgreSQL BYTEA column (temporary)
   - Async job retries S3 upload every 5 minutes for 24 hours
   - Alert compliance team if 24-hour retry window passes
   
3. **KMS Key Monitoring**
   - Health check on KMS key every 1 hour
   - Alert if key not available
   - Maintain backup KMS key for emergency failover
   
4. **Circuit Breaker**
   - If 5 consecutive uploads fail, pause recording of new sessions
   - Alert on-call engineer; page if issue not resolved in 1 hour

**Recovery**:
```javascript
async function handleRecordingUploadFailure(consultationId, error) {
    logger.error('Recording upload failure', {
        consultationId,
        error: error.message,
        code: error.code
    });
    
    // Step 1: Attempt immediate retry with fresh KMS credential
    try {
        const freshKmsKey = await kmsClient.describeKey({
            KeyId: process.env.RECORDING_KMS_KEY_ARN
        });
        
        if (freshKmsKey.KeyMetadata.Enabled !== true) {
            logger.error('KMS key is disabled', {consultationId});
            
            // Attempt failover to backup KMS key
            const backupKmsKey = process.env.RECORDING_KMS_KEY_BACKUP_ARN;
            logger.info('Attempting failover to backup KMS key', {backupKmsKey});
            
            await uploadToS3WithKMS(
                recordingFile,
                consultationId,
                backupKmsKey  // Use backup key
            );
        }
    } catch (kmsError) {
        logger.error('KMS key check failed', {kmsError});
    }
    
    // Step 2: Store recording in PostgreSQL temporarily
    if (error.code === 'ServiceUnavailable' || 
        error.code === 'RequestTimeout') {
        
        logger.info('Storing recording in PostgreSQL fallback', {consultationId});
        
        await storeRecordingInPostgres(
            consultationId,
            recordingFile,
            {status: 'pending_s3_upload'}
        );
        
        // Schedule async retry job
        scheduleS3RetryJob(consultationId, {
            maxRetries: 48,  // Retry every 5 min for 24 hours
            backoffMinutes: 5
        });
        
        publishEvent('recording_stored_in_postgres_fallback', {
            consultationId,
            reason: error.code
        }, 'HIGH');
        
        // Alert compliance team (informational)
        sendAlert({
            to: 'compliance-on-call@telemedicine.local',
            subject: 'Recording Fallback Activated',
            body: `Recording for consultation ${consultationId} temporarily stored in database. S3 upload will be retried automatically.`,
            severity: 'MEDIUM'
        });
    }
    
    // Step 3: Create incident ticket for manual investigation
    const ticket = await createIncidentTicket({
        title: `Recording Upload Failure: ${consultationId}`,
        description: `Recording for consultation ${consultationId} failed to upload: ${error.message}`,
        severity: 'CRITICAL',
        assignee: 'on-call-engineer'
    });
    
    logger.info('Incident ticket created', {ticketId: ticket.id});
}

// Async job: retry S3 upload every 5 minutes
async function retryRecordingUploadJob() {
    const pendingRecordings = await getPendingRecordings();
    
    for (const recording of pendingRecordings) {
        if (recording.retryCount >= 48) {
            // 24 hours of retries exhausted; escalate
            logger.error('Recording upload retries exhausted', {
                consultationId: recording.consultationId,
                retryCount: recording.retryCount
            });
            
            await escalateRecordingFailure(recording.consultationId);
            continue;
        }
        
        try {
            const uploadResult = await uploadToS3(
                recording.file,
                recording.consultationId
            );
            
            // Success; remove from fallback storage
            await removeFromPostgresRecordings(recording.consultationId);
            
            logger.info('Recording upload succeeded (retry job)', {
                consultationId: recording.consultationId,
                retryAttempt: recording.retryCount
            });
            
        } catch (error) {
            // Update retry count and try again
            await incrementRetryCount(recording.consultationId);
            
            logger.warn('Recording retry failed', {
                consultationId: recording.consultationId,
                retryCount: recording.retryCount + 1,
                nextRetryAt: getNextRetryTime(recording.retryCount + 1)
            });
        }
    }
}

// Run retry job every 5 minutes
setInterval(retryRecordingUploadJob, 5 * 60 * 1000);
```

**Fallback & Recovery**:
1. Immediate retry with exponential backoff (30s total)
2. If S3 unavailable: store in PostgreSQL BYTEA (1 hour max)
3. Background job retries S3 every 5 minutes for 24 hours
4. If 24-hour window passes: escalate to compliance officer for manual recovery
5. Consultation is marked "Recording - Pending Upload" in patient portal

**Compliance Implication**:
- Consultation still documented (SOAP note stored in PostgreSQL)
- Video recording temporary in PostgreSQL (encrypted)
- Compliance team alerted but no violation (recording not lost)
- Recording must be moved to S3 within 24 hours for compliance

**Recovery Time**: 5-30 seconds for automatic retry; 5-60 minutes for PostgreSQL fallback; 24 hours max before manual escalation
