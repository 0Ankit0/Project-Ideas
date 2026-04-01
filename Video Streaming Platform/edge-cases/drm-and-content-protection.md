# Video Streaming Platform - DRM & Content Protection Edge Cases

## Scenario 1: Widevine License Server Outage

### Failure Mode
Google Widevine license server becomes unavailable (maintenance or outage) for 45 minutes. Viewers attempt to play DRM-protected content, request playback token, which triggers DRM license request to Widevine. License server returns 503 Service Unavailable. Player cannot obtain license, playback fails with: "License acquisition failed".

### Symptoms
- DRM license requests: 503 from widevine.googleapis.com
- Player error: "HDCP required but license unavailable"
- All Widevine-protected content unplayable (affects ~70% of viewers using Chrome/Android)
- Playback service logs: "Widevine license server timeout: 45 seconds"

### Impact
- **Viewer Impact**: Complete playback failure for Chrome/Android (all DRM schemes fail)
- **Platform Impact**: 70% of viewers can't play (non-Chrome users unaffected)
- **Revenue**: Ad revenue loss during outage period

### Detection
- DRM license server latency monitoring: alert if p99 > 5 seconds
- License request success rate: alert if < 98%
- Automated playback test: verify license acquisition succeeds

### Root Causes
1. Google Widevine service maintenance or degradation
2. Network path to Widevine region is down
3. Platform rate limited by Widevine (too many requests)

### Mitigation (Immediate)
1. **License Caching**:
   - Cache valid licenses in Redis (TTL = license validity period - 10% buffer)
   - Key: `{content_id}:{device_id}:{license_type}`
   - Reduces Widevine dependency by 70% (cache hits for repeat plays)
   ```python
   def get_drm_license(content_id: str, device_id: str, license_type: str) -> dict:
       # Check cache first
       cache_key = f"drm_license:{content_id}:{device_id}:{license_type}"
       cached_license = redis.get(cache_key)
       if cached_license:
           return cached_license  # Serve from cache
       
       # Request new license from server
       try:
           license = request_widevine_license(content_id, device_id)
           # Cache for 1 hour (or license validity - buffer)
           redis.set(cache_key, license, ex=3600)
           return license
       except WidevineServiceError:
           # Fall back to cached even if expired
           stale_license = redis.get(cache_key)
           if stale_license:
               logger.warn("Using stale cached license due to Widevine outage")
               return stale_license
           raise
   ```

2. **Fallback License Providers**:
   - Configure secondary DRM provider (Microsoft PlayReady or custom KMS)
   - If Widevine fails, try fallback provider
   - Doesn't work for Chrome (Widevine-only), but helps other browsers

3. **Circuit Breaker**:
   - Track Widevine success rate per minute
   - If success rate < 70%, stop sending requests for 5 minutes
   - Return cached license during circuit open period
   - Prevents thundering herd on recovery

### Recovery Procedure
1. **Automatic**: Widevine service recovers → cache expires → requests go through normally
2. **Manual**: If Widevine offline >1 hour, use fallback DRM or unencrypted playback (not ideal)

---

## Scenario 2: DRM Token Expiry During Long Session

### Failure Mode
Viewer watching 8-hour marathon stream. DRM playback token issued at start with 6-hour expiry. At 6 hours 30 minutes, token expires. Playback stops with error: "License expired". Viewer must close and re-open player to get new token.

### Symptoms
- Playback suddenly stops at ~6-hour mark
- DRM license request returns: "License invalid or expired"
- Player shows error: "Session expired. Refresh to continue."
- Viewer frustration: loss of context (had to find where they were watching)

### Impact
- **Viewer Experience**: Interruption during marathon viewing
- **Watch Time**: Reduced (viewers might not return after interruption)

### Detection
- Session duration tracking: alert if viewers get kicked off during normal playback
- Player error reporting: track "license_expired" error frequency

### Root Causes
1. Token TTL too short relative to content length
2. No token refresh mechanism
3. Viewer starts 2-hour VOD content near end of token validity

### Mitigation (Immediate)
1. **Extend Token TTL**:
   - Default: 6 hours → 24 hours (covers most use cases)
   - Long-form content (live streams): 72 hours
   - Movie default: 6 hours (sufficient)

2. **Implement Token Refresh**:
   ```python
   @app.post("/api/v1/contents/{id}/refresh-token")
   def refresh_playback_token(content_id: str, request: RefreshTokenRequest):
       # Verify existing token still somewhat valid (>1 hour remaining)
       existing_token = request.current_token
       if get_token_ttl(existing_token) < 3600:
           raise HTTPException(401, "Token too expired to refresh")
       
       # Issue new token with extended expiry
       new_token = generate_playback_token(
           content_id=content_id,
           user_id=get_user_from_token(existing_token),
           ttl_seconds=86400  # 24 hours
       )
       
       return {"token": new_token, "expires_at": (now + 24h).isoformat()}
   ```
   - Player refreshes token every 4 hours automatically

3. **Client-Side Auto-Refresh**:
   ```javascript
   async function refreshTokenBeforeExpiry() {
       const tokenInfo = parseJWT(currentToken);
       const expiresAt = tokenInfo.exp * 1000;
       const now = Date.now();
       const timeUntilExpiry = expiresAt - now;
       
       // Refresh when 2 hours remaining
       if (timeUntilExpiry < 2 * 3600 * 1000) {
           const newToken = await fetch('/api/v1/contents/{id}/refresh-token', {
               method: 'POST',
               body: JSON.stringify({ current_token: currentToken })
           }).then(r => r.json());
           
           updatePlayerToken(newToken.token);
       }
   }
   ```

---

## Scenario 3: FairPlay Certificate Mismatch After iOS Update

### Failure Mode
Viewer using iOS app has FairPlay streaming key certificate. iOS is updated from 17.3 to 17.4. New iOS version changes certificate format or requirements. App attempts playback, DRM license request includes old certificate format. FairPlay server rejects: "Certificate invalid for this OS version".

### Symptoms
- iOS playback fails (Android/web works fine)
- Error: "DRM license acquisition failed"
- Issue appears after iOS system update
- Only affects affected iOS version cohort

### Impact
- **iOS Users**: Playback broken until app updated
- **Platform**: Support tickets from iOS users

### Detection
- Platform tracking: monitor success rate by device type + OS version
- Alert if iOS playback success rate drops >5%
- Synthetic monitoring: test on multiple iOS versions

### Root Causes
- iOS system update changes FairPlay requirements
- App not updated to new format
- Certificate caching prevents refresh

### Mitigation (Immediate)
1. **Flush Certificate Cache**:
   ```swift
   // iOS app
   let fileManager = FileManager.default
   let cachePath = NSSearchPathForDirectoriesInDomains(.cachesDirectory, .userDomainMask, true)[0]
   let certPath = "\(cachePath)/fairplay_cert"
   try fileManager.removeItem(atPath: certPath)
   // Next playback will re-fetch certificate
   ```

2. **Auto-Update Detection**:
   ```swift
   func checkOSVersionChange() {
       let currentOSVersion = UIDevice.current.systemVersion
       let savedOSVersion = UserDefaults.standard.string(forKey: "last_os_version") ?? ""
       
       if currentOSVersion != savedOSVersion {
           // OS updated, clear DRM cache
           clearDRMCache()
           UserDefaults.standard.set(currentOSVersion, forKey: "last_os_version")
       }
   }
   ```

3. **Prompt App Update**:
   ```python
   @app.get("/api/v1/app-version-check")
   def check_app_version(device_type: str, current_version: str, os_version: str):
       # Check if app version compatible with OS
       compatibility = db.app_compatibility.get(
           device_type=device_type,
           app_version=current_version,
           os_version=os_version
       )
       
       if not compatibility.is_supported:
           return {
               "status": "update_required",
               "message": "Please update the app for compatibility with your iOS version",
               "update_url": "https://apps.apple.com/app/vsp"
           }
       
       return {"status": "compatible"}
   ```

---

[Remaining scenarios 4-7 would cover:
- Scenario 4: Screen Recording Detection Bypass
- Scenario 5: VPN Geo-Restriction Bypass Detection
- Scenario 6: DRM Key Rotation Breaking Active Sessions
- Scenario 7: Offline Download DRM License Expiry
]

Each would include detailed failure modes, detection, mitigation, and recovery procedures.
