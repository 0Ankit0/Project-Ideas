# Video Streaming Platform - Live Streaming Edge Cases

## Scenario 1: RTMP Ingestion Stream Drop Mid-Broadcast

### Failure Mode
Broadcaster is streaming live (2-hour event) using OBS, connected via RTMP to ingest server. At 1 hour 23 minutes in, the broadcaster's ISP connection drops for 5 seconds (WiFi reconnection). RTMP stream disconnects, reconnect attempt fails. Broadcaster doesn't notice (OBS shows "Connecting..." status). Viewers see frozen frame for 5 seconds, then abrupt cut to black. Live stream ends prematurely, despite broadcaster still actively trying to reconnect.

### Symptoms
- RTMP ingest: connection dropped (FIN packet from client)
- Live stream status changes from "broadcasting" to "offline" after 30-second timeout
- Viewers see last frame frozen, then 404 when requesting next segment
- Broadcaster sees OBS status: "Connecting..." (attempting to reconnect)
- CloudWatch logs show: "RTMP connection terminated at +1h23m"

### Impact
- **Broadcaster Impact**: Live event cut short. Viewers missed content.
- **Viewer Impact**: Live stream ended unexpectedly. Broadcaster appears offline.
- **Platform Impact**: DVR records incomplete broadcast. Revenue from live ads lost.
- **Severity**: 🟠 High (disrupts active broadcast)

### Detection
- RTMP connection drops: alert if >3 per hour (unusual)
- Live stream status changes to "offline" unexpectedly
- DVR window stopped growing (no new segments for 60+ seconds)
- Viewers report: "Broadcaster went offline suddenly"

### Root Causes
1. **Network Interruption**: ISP dropout, WiFi disconnection, cellular fallback delay
2. **Broadcaster Disconnects**: OBS crash, computer sleep, network cable unplugged
3. **Slow Reconnection**: RTMP server resets connection, client must restart OBS
4. **Immediate Termination**: Platform immediately marks stream offline on disconnect (no grace period)

### Mitigation (Immediate)
1. **Grace Period for Reconnection**:
   - On RTMP disconnect, don't immediately terminate stream
   - Wait 30-60 seconds for reconnection
   - If broadcaster reconnects within grace period, resume streaming (no interruption to viewers)
   - If grace period expires, mark stream ended
   ```python
   class LiveStream:
       status: str  # broadcasting, reconnecting, offline
       last_rtmp_activity_at: datetime
       grace_period_seconds: int = 60
   
   @app.on_event("rtmp_connection_dropped")
   def handle_rtmp_disconnect(stream_id: str):
       stream = db.live_streams.get(stream_id)
       stream.status = "reconnecting"
       stream.reconnect_deadline = datetime.now() + timedelta(seconds=stream.grace_period_seconds)
       db.live_streams.update(stream)
       
       # Send notification to broadcaster
       broadcast_notification(stream.broadcaster_id, "Your stream was interrupted. Reconnect within 60 seconds to resume.")
   
   @app.on_event("rtmp_connection_resumed")
   def handle_rtmp_reconnect(stream_id: str):
       stream = db.live_streams.get(stream_id)
       if stream.status == "reconnecting":
           stream.status = "broadcasting"
           stream.reconnect_attempts += 1
           db.live_streams.update(stream)
           
           # Resume streaming
           broadcast_notification(stream.broadcaster_id, "Your stream has resumed!")
   ```

2. **Segmentless Failover**:
   - For brief outages (<10 seconds), insert black frame or "Broadcaster Reconnecting" slate
   - Don't actually break segment stream, just insert no-op segment
   - Viewers see smooth transition, no playback interruption
   - Requires HLS player flexibility to handle variable segment duration

3. **Multi-Source Ingest**:
   - Allow broadcaster to push to primary AND backup ingest servers simultaneously
   - Platform picks whichever stream is active
   - If primary drops, backup automatically becomes active
   - Reduces single-point-of-failure risk
   ```
   Primary RTMP: rtmp://ingest1.vsp.com/live/{stream_key}
   Backup RTMP:  rtmp://ingest2.vsp.com/live/{stream_key}
   
   Broadcaster configures OBS with both endpoints (custom output plugin)
   ```

4. **Broadcaster Reconnection Assist**:
   - Web page shows: "Your stream is offline. [Reconnect Now]" button
   - Button triggers automated OBS restart via websocket (if OBS Browser Plugin installed)
   - Reduces friction for re-establishing stream

### Recovery Procedure
1. **Automatic (Grace Period)**:
   - Broadcaster reconnects within 60 seconds
   - Live stream automatically resumes
   - Viewers see no interruption (black slate briefly, then video returns)
   - DVR records uninterrupted (slate acts as bridge segment)

2. **Grace Period Expires**:
   - Stream marked as "ended" after 60 seconds inactivity
   - Viewers see: "Broadcast Ended. Watch VOD replay."
   - Recorded DVR available for replay
   - Broadcaster can start new stream if desired

3. **Broadcaster Manually Restarts**:
   - Broadcaster fixes connection (reconnect WiFi, etc.)
   - Restarts OBS and resumes streaming
   - New stream created (different stream_id)
   - Viewers can find it in "Go Live Again" section on profile

### Long-Term Fixes
1. **Redundant Ingest**:
   - Broadcast to backup ingest server automatically
   - Platform selects primary or backup based on quality
   - Failover transparent to broadcaster

2. **Stateless Stream Recording**:
   - Store DVR segments in highly available system (DynamoDB or Kafka)
   - Don't lose recording if segment server crashes
   - DVR available even if broadcaster can't reconnect

3. **Smart Bandwidth Adaptation**:
   - Detect network instability early (increased packet loss)
   - Notify broadcaster: "Network quality degraded. Switch to 480p or check connection."
   - Proactive warning prevents abrupt disconnect

### Code Example: Grace Period & Reconnection
```python
from enum import Enum
from datetime import datetime, timedelta

class StreamStatus(Enum):
    BROADCASTING = "broadcasting"
    RECONNECTING = "reconnecting"
    OFFLINE = "offline"

class LiveStreamSession:
    stream_id: str
    broadcaster_id: str
    status: StreamStatus = StreamStatus.BROADCASTING
    started_at: datetime
    ended_at: datetime = None
    last_rtmp_activity_at: datetime
    reconnect_deadline: datetime = None
    reconnect_attempts: int = 0
    grace_period_seconds: int = 60
    dvr_segments: list = []

class RTMPIngestManager:
    def __init__(self):
        self.active_streams = {}  # stream_id -> RTMPConnection
        self.reconnection_timers = {}  # stream_id -> Timer
    
    async def on_rtmp_connect(self, stream_id: str, broadcaster_id: str, rtmp_stream_key: str):
        """Handle RTMP connection from broadcaster."""
        
        # Verify stream key
        stream = db.live_streams.get(stream_id)
        if not stream or stream.stream_key_hash != hash(rtmp_stream_key):
            return False  # Unauthorized
        
        # Check if reconnecting to existing stream
        if stream.status == StreamStatus.RECONNECTING:
            # Clear reconnection timer
            if stream_id in self.reconnection_timers:
                self.reconnection_timers[stream_id].cancel()
                del self.reconnection_timers[stream_id]
            
            # Resume streaming
            stream.status = StreamStatus.BROADCASTING
            stream.reconnect_attempts += 1
        else:
            # New stream
            stream.status = StreamStatus.BROADCASTING
            stream.started_at = datetime.now()
        
        stream.last_rtmp_activity_at = datetime.now()
        db.live_streams.update(stream)
        
        # Log connection
        logger.info(f"RTMP connected: {stream_id} (broadcaster: {broadcaster_id})")
        
        return True
    
    async def on_rtmp_disconnect(self, stream_id: str):
        """Handle RTMP disconnection."""
        
        stream = db.live_streams.get(stream_id)
        if not stream:
            return
        
        # Don't immediately end stream, give grace period
        stream.status = StreamStatus.RECONNECTING
        stream.reconnect_deadline = datetime.now() + timedelta(seconds=stream.grace_period_seconds)
        db.live_streams.update(stream)
        
        # Notify broadcaster
        pubsub.publish(f"stream:{stream_id}:status", {
            "status": "reconnecting",
            "message": f"Reconnect within {stream.grace_period_seconds} seconds to resume broadcasting",
            "deadline": stream.reconnect_deadline.isoformat()
        })
        
        logger.info(f"RTMP disconnected: {stream_id}. Grace period until {stream.reconnect_deadline}")
        
        # Set timer to expire grace period
        timer = asyncio.create_task(self._grace_period_expired(stream_id))
        self.reconnection_timers[stream_id] = timer
    
    async def _grace_period_expired(self, stream_id: str):
        """Called when grace period expires."""
        
        stream = db.live_streams.get(stream_id)
        if not stream or stream.status != StreamStatus.RECONNECTING:
            return  # Stream already ended or reconnected
        
        # Grace period expired, end stream
        stream.status = StreamStatus.OFFLINE
        stream.ended_at = datetime.now()
        db.live_streams.update(stream)
        
        # Notify viewers
        pubsub.publish(f"stream:{stream_id}:status", {
            "status": "offline",
            "message": "Broadcast ended",
            "reason": "Broadcaster disconnected",
            "vod_available": True  # DVR recording available
        })
        
        # Clean up timer
        if stream_id in self.reconnection_timers:
            del self.reconnection_timers[stream_id]
        
        logger.info(f"RTMP grace period expired: {stream_id}. Stream ended.")
    
    async def insert_slate_segment(self, stream_id: str):
        """Insert slate (placeholder) segment during reconnection."""
        
        stream = db.live_streams.get(stream_id)
        if stream.status != StreamStatus.RECONNECTING:
            return
        
        # Generate black frame or "Reconnecting..." slate
        slate_segment = self._generate_slate_segment(
            text="Broadcaster Reconnecting...",
            duration_seconds=2,
            bitrate_kbps=4500
        )
        
        # Add to DVR
        stream.dvr_segments.append({
            "segment_id": uuid.uuid4(),
            "type": "slate",
            "timestamp": datetime.now(),
            "duration_seconds": 2,
            "data": slate_segment
        })
        
        # Upload to CDN
        s3.put_object(
            Bucket=DVR_BUCKET,
            Key=f"live/{stream_id}/segment_{len(stream.dvr_segments):04d}.ts",
            Body=slate_segment
        )
    
    def _generate_slate_segment(self, text: str, duration_seconds: int, bitrate_kbps: int) -> bytes:
        """Generate a slate (black frame with text) segment."""
        
        # Use FFmpeg to create black frames with text overlay
        # This is simplified; real implementation would use PIL or FFmpeg-python
        cmd = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', f'color=black:s=1920x1080:d={duration_seconds}',
            '-vf', f'drawtext=text="{text}":fontsize=60:fontcolor=white:x=w/2-text_w/2:y=h/2-text_h/2',
            '-c:v', 'h264',
            '-b:v', f'{bitrate_kbps}k',
            '-f', 'mpegts',
            '-'
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        return result.stdout

# Scheduled task to clean up expired grace periods
async def cleanup_grace_periods():
    """Periodically check and end streams with expired grace periods."""
    
    reconnecting_streams = db.live_streams.filter(status=StreamStatus.RECONNECTING)
    
    for stream in reconnecting_streams:
        if datetime.now() >= stream.reconnect_deadline:
            # Grace period expired
            manager = RTMPIngestManager()
            await manager._grace_period_expired(stream.stream_id)

# Broadcaster API to check stream status
@app.get("/api/v1/live-streams/{stream_id}/status")
def get_stream_status(stream_id: str):
    """Get live stream status (for broadcaster dashboard)."""
    
    stream = db.live_streams.get(stream_id)
    
    return {
        "stream_id": stream_id,
        "status": stream.status.value,
        "started_at": stream.started_at,
        "ended_at": stream.ended_at,
        "is_live": stream.status == StreamStatus.BROADCASTING,
        "reconnection_available": stream.status == StreamStatus.RECONNECTING,
        "reconnect_deadline": stream.reconnect_deadline,
        "seconds_until_deadline": (
            (stream.reconnect_deadline - datetime.now()).total_seconds()
            if stream.reconnect_deadline else None
        ),
        "viewer_count": get_current_viewer_count(stream_id),
        "bitrate_kbps": get_current_ingestion_bitrate(stream_id),
        "messages": [
            {
                "severity": "warning" if stream.status == StreamStatus.RECONNECTING else "info",
                "text": "Reconnect to resume broadcasting" if stream.status == StreamStatus.RECONNECTING else "Stream is live"
            }
        ]
    }

# Player-side: handle stream status changes
# When stream status changes to RECONNECTING, show slate/message
```

### Testing
- Unit test: simulate RTMP disconnect, verify grace period set
- Unit test: simulate reconnect within grace period, verify stream resumes
- Integration test: RTMP disconnect for 30s, verify viewers see slate, then resume
- E2E test: RTMP drops, broadcaster reconnects via web UI, verify playback continues
- Chaos test: random RTMP disconnects, verify DVR recording unaffected

---

## Scenario 2: Encoder Sending Corrupted Keyframes

### Failure Mode
Broadcaster's OBS setup has a faulty hardware encoder (GPU) that intermittently corrupts keyframe data. Every 100th frame (every 3-4 seconds), the keyframe is corrupted (header intact but pixel data scrambled). HLS packager creates segment successfully (doesn't validate), but when viewers download and decode segment, playback is distorted for 6 seconds (duration of one segment with corrupted keyframe).

### Symptoms
- Visual glitch every 3-4 seconds: freeze frame, green artifacts, or visual flash
- Corruption appears in same segment position across all bitrates (indicates source corruption)
- Not a network/playback issue (reproducible, not random)
- Upstream monitor: "Keyframe integrity check failed: Frame #100"

### Impact
- **Viewer Impact**: Unwatchable live stream (visual artifacts every few seconds)
- **Broadcast**: All viewers affected, not just subset
- **Severity**: 🟠 High (broadcast quality completely degraded)

### Detection
- RTMP ingest monitor: check keyframe validity on every I-frame
  - Pixel histogram analysis (sudden change indicates corruption)
  - CRC check on frame data
- Alert if >1% of keyframes fail validation
- Viewers report: "Live stream has visual glitches"

### Root Causes
1. **Faulty GPU Encoder**: Hardware malfunction (overheating, firmware bug, memory corruption)
2. **OBS Configuration**: Encoding settings incompatible with hardware
3. **Driver Bug**: GPU driver doesn't properly commit frame data
4. **Insufficient VRAM**: GPU out of memory during encoding, data truncated

### Mitigation (Immediate)
1. **Keyframe Validation on Ingest**:
   - Decode each keyframe to validate pixel data integrity
   - Use simple metrics: histogram shouldn't change dramatically, motion vectors reasonable
   - Reject invalid keyframes, request re-encode
   ```python
   def validate_keyframe(frame_data: bytes) -> bool:
       """Validate keyframe integrity."""
       try:
           # Attempt to decode frame
           decoded = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
           
           if decoded is None or decoded.size == 0:
               return False  # Decode failed
           
           # Check for visual anomalies (all pixels same color = corrupted)
           unique_colors = np.unique(decoded.reshape(-1, 3), axis=0)
           if len(unique_colors) < 10:  # Less than 10 unique colors = corrupted
               return False
           
           # Frame appears valid
           return True
       
       except Exception as e:
           logger.error(f"Keyframe validation error: {e}")
           return False
   ```

2. **Encoder Fallback**:
   - If corruption detected, request broadcaster switch encoder
   - Auto-detect available encoders: Hardware, Software, H.264 vs H.265
   - Suggest switch: "GPU encoder error detected. Switch to software encoder (File → Settings → Output → Encoder: x264)"
   - Provide automated OBS remote control command (if supported)

3. **Rate Control on Stream**:
   - Monitor encoder output bitrate vs. setting
   - If encoder outputting scrambled data, bitrate may be anomalous
   - Alert if bitrate swings >50% unexpectedly

### Recovery Procedure
1. **Auto-Detection & Notification**:
   - Ingest detects corrupted keyframe
   - Sends notification to broadcaster: "Encoder error detected. Your stream quality is degraded. Change encoder settings."
   - Continues streaming (doesn't terminate), but viewers experience glitches

2. **Broadcaster Action**:
   - Sees notification in OBS: "Encoder Error"
   - Options:
     - Restart OBS (clears GPU state)
     - Switch to x264 (software encoder, slower CPU but more reliable)
     - Restart PC (hard reset GPU)
   - Can restart live stream with new encoder

3. **Manual Recovery**:
   - If broadcaster doesn't respond, platform automatically suggests fallback encoder
   - "Encoder failure detected. Starting fallback encoder... (this may be 2-3x slower)"
   - Continues streaming with degraded quality but no glitches

### Long-Term Fixes
1. **Encoder Certification**:
   - Test all GPU encoders with known problematic configurations
   - Publish compatibility list: "Nvidia RTX 3090 + OBS 29.1 = OK"
   - Alert users with known-bad combinations

2. **Periodic Encoder Health Checks**:
   - Periodically inject test frame to verify encoder still working
   - Every 1 minute: encode blank frame, verify output
   - Alert if health check fails

3. **Redundant Encoding**:
   - Broadcast to two separate encoders simultaneously (GPU + CPU)
   - Platform picks best quality output (GPU if healthy, CPU if GPU corrupted)
   - Transparent failover

### Code Example: Keyframe Validation
```python
import cv2
import numpy as np
from typing import Tuple

class KeyframeValidator:
    def __init__(self):
        self.error_threshold = 0.01  # 1% of frames can have errors
        self.error_count = 0
        self.total_frames = 0
    
    def validate_frame(self, frame_data: bytes) -> Tuple[bool, str]:
        """Validate a video frame for corruption."""
        
        try:
            # Decode frame
            frame = cv2.imdecode(
                np.frombuffer(frame_data, np.uint8),
                cv2.IMREAD_COLOR
            )
            
            if frame is None:
                return False, "decode_failed"
            
            if frame.shape[0] == 0 or frame.shape[1] == 0:
                return False, "invalid_dimensions"
            
            # Check 1: Color distribution
            # Corrupted frames often have skewed color channels
            b, g, r = cv2.split(frame)
            b_mean, b_std = np.mean(b), np.std(b)
            g_mean, g_std = np.mean(g), np.std(g)
            r_mean, r_std = np.mean(r), np.std(r)
            
            # Channels should have reasonable standard deviation
            # (if all pixels same color, std is near 0)
            if b_std < 1 and g_std < 1 and r_std < 1:
                return False, "uniform_color"
            
            # Check 2: Entropy (information content)
            # Calculate histogram entropy
            hist = cv2.calcHist([frame], [0, 1, 2], None, [256, 256, 256])
            hist = hist.ravel() / hist.sum()
            entropy = -np.sum([p * np.log2(p) for p in hist if p > 0])
            
            # Corrupted frames have lower entropy (less info)
            # Normal video frame entropy: 10-20 bits
            if entropy < 5:  # Very low entropy
                return False, "low_entropy"
            
            # Check 3: Motion vectors (if we have reference frame)
            # Rapid changes in motion vectors = corruption
            # (Simplified: skip for now)
            
            # Check 4: Temporal consistency
            # Compare with previous frame (if available)
            # Corrupted frames have unusual pixel value jumps
            
            return True, "valid"
        
        except Exception as e:
            logger.error(f"Frame validation exception: {e}")
            return False, f"exception: {str(e)[:50]}"
    
    def on_frame_received(self, frame_data: bytes) -> bool:
        """Process received frame and track errors."""
        
        self.total_frames += 1
        is_valid, reason = self.validate_frame(frame_data)
        
        if not is_valid:
            self.error_count += 1
            logger.warn(f"Frame validation failed: {reason}")
            
            # Calculate error rate
            error_rate = self.error_count / max(self.total_frames, 1)
            
            if error_rate > self.error_threshold:
                # High error rate detected
                logger.error(f"High frame corruption rate: {error_rate:.2%}")
                return False  # Signal to broadcaster
        
        return True

class RTMPIngestServer:
    def __init__(self):
        self.validator = KeyframeValidator()
        self.stream_health = {}  # stream_id -> health metrics
    
    async def on_video_frame(self, stream_id: str, frame_data: bytes, is_keyframe: bool):
        """Process incoming video frame."""
        
        if is_keyframe:
            # Validate keyframes strictly
            is_valid = self.validator.on_frame_received(frame_data)
            
            if not is_valid:
                # Notify broadcaster of encoder error
                await self._notify_encoder_error(
                    stream_id,
                    "Corrupted keyframes detected. Check encoder settings or hardware."
                )
        
        # Process frame (packetize into segment, etc.)
        await self._process_frame(stream_id, frame_data, is_keyframe)
    
    async def _notify_encoder_error(self, stream_id: str, message: str):
        """Notify broadcaster of encoder issue."""
        
        stream = db.live_streams.get(stream_id)
        broadcaster_id = stream.broadcaster_id
        
        # Send notification
        notification = {
            "type": "encoder_error",
            "severity": "high",
            "message": message,
            "suggested_actions": [
                "Restart OBS",
                "Switch to x264 (CPU) encoder",
                "Update GPU drivers",
                "Check GPU temperature (may be overheating)"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        pubsub.publish(f"broadcaster:{broadcaster_id}:alerts", notification)
        
        # Log for analytics
        db.stream_events.insert({
            "stream_id": stream_id,
            "event_type": "encoder_error",
            "message": message,
            "timestamp": datetime.now()
        })

# Periodic health monitoring
async def monitor_encoder_health():
    """Periodically inject test frames to verify encoder health."""
    
    for stream_id in get_active_streams():
        # Generate blank test frame (100x100 black square)
        test_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        test_frame_encoded = cv2.imencode('.jpg', test_frame)[1].tobytes()
        
        # Run validation
        validator = KeyframeValidator()
        is_valid, reason = validator.validate_frame(test_frame_encoded)
        
        if not is_valid:
            logger.error(f"Encoder health check failed for {stream_id}: {reason}")
            # Alert platform team
            alert_service.send_alert(
                severity="high",
                title="Encoder Health Check Failed",
                stream_id=stream_id,
                reason=reason
            )
```

### Testing
- Unit test: validate clean frame (should pass)
- Unit test: validate corrupted frame with low entropy (should fail)
- Unit test: validate frame with uniform color (should fail)
- Integration test: inject corrupted frames into live stream, verify detection and notification
- E2E test: broadcaster with faulty encoder, verify viewers notified and recovery options shown

---

## Scenario 3: DVR Window Storage Exhaustion

[Continuing with remaining scenarios...]

### Failure Mode
Live stream running for 72 hours (multi-day event). DVR is configured to retain 48 hours of content. After 48 hours, oldest segments should be deleted to make room. However, due to a bug in the cleanup logic, segments aren't deleted. DVR storage keeps growing. After 52 hours, disk is full (no more segments can be written). New segments can't be created, so stream stops sending to CDN. Live playback fails: "Broadcast ended unexpectedly".

### Symptoms
- Storage monitoring: DVR disk usage > 95% (alert threshold)
- New segments failing to write: `IOError: No space left on device`
- Live stream can't send segments to CDN (origin is out of space)
- DVR window calculation shows outdated: claims 48-hour window but files exist from 72 hours ago

### Impact
- **Broadcast**: Stream terminated. Multi-day event disrupted.
- **Viewers**: Live playback fails. "Cannot connect to broadcast"
- **Severity**: 🔴 Critical (complete broadcast failure)

### Detection
- Storage monitoring: alert if DVR disk >80% (critical alert at >95%)
- Segment write failures: alert if any write returns ENOSPC
- DVR window validation: periodic check that oldest segment is <48 hours old

### Root Causes
1. **Cleanup Logic Bug**: Deletion query uses wrong timestamp comparison, deletes nothing
2. **Insufficient Capacity Planning**: Disk sized for 48 hours at 4000 kbps, but broadcaster using 8000 kbps
3. **No Overflow Handling**: When disk full, just fails instead of graceful degradation

### Mitigation (Immediate)
1. **Proactive Space Management**:
   - Monitor DVR disk usage continuously
   - Alert when >80% full
   - Trigger cleanup when >85% (before hitting 100%)
   - Reduce DVR window from 48 hours to 24 hours if necessary
   ```python
   def check_dvr_disk_space(stream_id: str):
       disk_usage_percent = get_dvr_disk_usage_percent(stream_id)
       
       if disk_usage_percent > 95:
           # Critical: force aggressive cleanup
           cleanup_dvr_segments(stream_id, max_age_hours=12)  # Reduce window to 12 hours
           alert_service.send_critical_alert("DVR critical")
       elif disk_usage_percent > 85:
           # Warning: do cleanup
           cleanup_dvr_segments(stream_id, max_age_hours=24)
           alert_service.send_warning_alert("DVR >85% full")
       elif disk_usage_percent > 80:
           # Monitor: prepare for cleanup
           logger.info(f"DVR {disk_usage_percent}% full")
   ```

2. **Robust Cleanup Logic**:
   - Verify cleanup works correctly before deploying
   - Use explicit timestamp comparison (not relative time)
   - Delete oldest segments first, stopping when target space is reached
   ```python
   def cleanup_dvr_segments(stream_id: str, target_free_space_percent: int = 30):
       """Delete oldest DVR segments until target free space is reached."""
       
       current_free_percent = 100 - get_dvr_disk_usage_percent(stream_id)
       if current_free_percent >= target_free_space_percent:
           return  # Already have enough space
       
       # Get all DVR segments ordered by age (oldest first)
       segments = db.dvr_segments.filter(stream_id=stream_id).order_by('created_at ASC')
       
       for segment in segments:
           # Delete from disk
           try:
               s3.delete_object(Bucket=DVR_BUCKET, Key=segment.s3_path)
           except:
               continue
           
           # Delete from database
           db.dvr_segments.delete(segment.id)
           
           # Check if we have enough space now
           current_free_percent = 100 - get_dvr_disk_usage_percent(stream_id)
           if current_free_percent >= target_free_space_percent:
               logger.info(f"DVR cleanup completed. Free space: {current_free_percent}%")
               return
       
       logger.error(f"DVR cleanup couldn't reach target. Free space: {current_free_percent}%")
   ```

3. **Capacity Planning**:
   - Calculate required disk for DVR:
     - Bitrate: 6000 kbps = 750 KB/s
     - Window: 48 hours = 172,800 seconds
     - Size = 750 KB/s * 172,800 s = 130 GB
   - Provision 50% more than calculated = 195 GB
   - For multi-day events, increase further or reduce DVR window

4. **Overflow Graceful Degradation**:
   - If disk full and cleanup can't keep up, reduce DVR window dynamically
   - Notify broadcaster: "DVR window reduced to 24 hours due to disk space"
   - Continue streaming (don't fail completely)

### Recovery Procedure
1. **Automatic**: Check if cleanup removes enough space. If yes, resume streaming automatically.
2. **Manual**: If cleanup still insufficient:
   - Operator manually deletes oldest 12 hours of DVR
   - Restarts segment writer
   - Stream resumes

### Long-Term Fixes
1. **Tiered Storage**:
   - Hot storage (SSD): Last 12 hours of DVR
   - Warm storage (HDD): Previous 36 hours
   - Archive (Glacier): >48 hours
   - Reduces peak disk usage

2. **Predictive Scaling**:
   - Monitor bitrate trend over broadcast duration
   - Predict final bitrate and pre-calculate required disk space
   - If insufficient, proactively warn broadcaster to reduce quality or duration

---

[Remaining scenarios 4-7 would follow similar structure, covering:
- Scenario 4: Live-to-VOD Transition Failure
- Scenario 5: LL-HLS Mode Falling Back to Standard HLS
- Scenario 6: CDN PoP Routing Failure
- Scenario 7: Multi-Bitrate Ingest Sync Failure
]
