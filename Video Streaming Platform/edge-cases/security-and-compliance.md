# Video Streaming Platform - Security & Compliance Edge Cases

## Key Scenarios: DMCA, Content ID, GDPR, CSAM, Watermarking, Account Sharing, Age-Gating

Compliance edge cases cover legal/regulatory scenarios where platform must respond correctly within strict timeframes.

## Scenario 1: DMCA Takedown SLA Deadline Expiration

Content flagged for DMCA violation. Complainant submits takedown notice. Legal team has 24 hours to respond (ISP safe harbor requirement). If deadline passes without response, ISP liable for content. If content not removed within 24 hours, creator can claim "notice ignored".

**Failure Mode**: DMCA notice received, but legal team on holiday. Takedown deadline passes without action. Platform liable.

**Symptoms**: DMCA notice timestamp + 24 hours = deadline. No action taken by deadline.

**Detection**: Automated: calendar reminder at T-12h, T-6h, T-1h. Escalation to legal department.

**Mitigation**:
1. Automated workflow: DMCA notice → ticket → legal team → decision (yes/no takedown)
2. Default: assume valid complaint, remove content immediately, notify creator
3. Creator can file counter-notice within 10 days to restore (if they believe fair use applies)
4. Track all deadlines in compliance database with alerts

**Compliance Requirement**: ISP must respond within 24 hours. Platform must remove content within 24 hours.

---

## Scenario 2: Content ID False Positives/Negatives

Content ID system (AudioClaim, ContentID) flags user video as containing copyrighted music. Creator claims original composition, disputes claim. System gives creator 48 hours to dispute. If not disputed, claim stands permanently.

**Failure Mode**: Creator unaware of claim, doesn't dispute within 48h window. Claim becomes final, demonetizes video forever.

**Symptoms**: Content flagged, but creator notification email goes to spam. Deadline passes.

**Detection**: Track notification delivery rates. Alert if creator doesn't dispute within 48h (send reminder at 24h and 40h marks).

**Mitigation**:
1. Multi-channel notification: email, in-app notification, SMS
2. Extend dispute window if creator hasn't seen notification (if email bounced, etc.)
3. Default assume creator dispute valid for original creators (trust but verify)
4. Auto-restore monetization after creator dispute, then manually review

---

## Scenario 3: GDPR Watch History Deletion During Active Session

User exercises "right to be forgotten": requests deletion of all watch history. Platform deletes from database immediately. But user is actively watching video. Recommendations engine needs watch history to make personalized recs. System crashes trying to access deleted history.

**Failure Mode**: GDPR deletion request deletes user's watch history. Active session still running. Real-time recommendation logic fails.

**Symptoms**: Player crashes with: "User data not found" error.

**Detection**: Monitor for crashes accessing user data during active session. Alert if deletion requests aren't coordinated with active sessions.

**Mitigation**:
1. GDPR deletion queued, not immediate. Flag user as "pending deletion" for 30 minutes (grace period)
2. Active sessions get notification: "Account deletion requested. Playback will stop in 30 minutes."
3. After grace period, user logs out, data deleted
4. Or: defer deletion until all active sessions end (soft delete)
5. Alternative: anonymize data instead of deleting (keep for analytics, remove personal identifiers)

**Compliance**: GDPR requires deletion "without undue delay" but doesn't prohibit 30-minute grace period.

---

## Scenario 4: CSAM/NCMEC Detection & Reporting

Content AI detects child sexual abuse material (CSAM) in user upload. Platform must report to NCMEC (National Center for Missing & Exploited Children) within specific timeframe, and remove content. If platform aware of CSAM and doesn't report, platform liable.

**Failure Mode**: CSAM detection triggers, but reporting system broken. Content stays on platform, not reported to authorities.

**Symptoms**: AI flagging system works, but NCMEC report queue not being processed.

**Detection**: Automated: queue monitoring. Alert if any CSAM detection isn't reported within 1 hour.

**Mitigation**:
1. Automated detection + immediate removal + immediate NCMEC reporting
2. Mandatory reporting: can't override, can't delay
3. Separate queue for CSAM (not mixed with regular abuse queue)
4. Webhook to NCMEC API with CyberTipline integration
5. Track all reports with timestamps for legal compliance

**Legal**: Platform immunity requires "expeditious removal" and reporting. Usually <24 hours.

---

## Scenario 5: Watermarking Defeat Attempts & Detection

Platform embeds visible watermark on content: "WATERMARK - PREVIEW ONLY" to prevent unauthorized downloading. User uses FFmpeg or video editor to remove watermark. User re-uploads watermark-free video to platform claiming original ownership.

**Failure Mode**: Watermark removal defeats platform's DRM. No way to detect re-upload of stolen content.

**Symptoms**: Original creator's watermarked video, then later uploaded by different user without watermark. Content ID system doesn't match (removed watermark changes pixel signatures).

**Detection**: 
1. Perceptual hashing: generate hash resistant to minor pixel changes
2. Scene detection: match scenes visually, even if watermark removed
3. Metadata: EXIF, creation date (original has earlier date)
4. Crowd-sourcing: creators flag suspicious uploads

**Mitigation**:
1. Use robust watermarking (invisible, hard to remove)
2. Implement temporal watermarking (watermark appears at random times, harder to edit out)
3. Perceptual matching for duplicate detection
4. Copyright owner can manually flag suspicious uploads

---

## Scenario 6: Account Sharing Detection & Enforcement

User purchases family plan (4 concurrent streams). Shares password with 8 friends. 5 concurrent streams detected (exceeds 4-stream limit). Platform must enforce limit without harming legitimate use (family members in different locations).

**Failure Mode**: Too aggressive enforcement: kicks off family member mid-playback. Family upset.

**Symptoms**: User in New York, wife in Boston, both watching simultaneously. Platform thinks account shared, terminates one stream.

**Detection**: Geographic anomalies (streams from different cities/countries simultaneously). Device fingerprinting (different devices).

**Mitigation**:
1. Grace period: first violation = warning, not termination
2. Device registration: user explicitly lists authorized devices
3. Geofencing: allow concurrent streams in same geographic region
4. PIN-based approval: user approves new devices before use
5. Soft enforcement: continue stream, but show warning "concurrency exceeded, service may degrade"

**Legal**: Copyright law doesn't explicitly ban account sharing, but many platforms' TOS prohibit it.

---

## Scenario 7: Age-Gating Bypass Attempts

Platform requires age verification (18+) for adult content. User enters fake birthdate (1900-01-01) claiming to be 120 years old. System accepts claim without verification. User accesses adult content underage.

**Failure Mode**: Age gate accepts obviously false birthdate. No secondary verification.

**Symptoms**: Young user easily bypasses age check by entering unrealistic age.

**Detection**: Flag suspicious birthdates (>110 years old or <13 years old). Require real ID verification.

**Mitigation**:
1. Require real ID verification (government ID or credit card) for adult content
2. Age validation: reject birthdates that result in age <13 or >120
3. Geographic restrictions: age of digital consent varies by country
4. Parental controls: parents can restrict adult content
5. Device-level gating: no adult content on devices marked "family mode"

**Legal**: COPPA (Children's Online Privacy Protection Act) requires age verification for content if any audience is <13. GDPR requires explicit parental consent if user <16 (varies by country).

---

(Continuing with more comprehensive scenarios covering watermark defeat detection, VPN bypass detection, etc. Total file will be 300+ lines.)
