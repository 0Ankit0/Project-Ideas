# Edge Cases: OTA Firmware Updates

This document catalogs edge cases specific to the over-the-air firmware update subsystem of the IoT Device Management Platform. Each case describes a realistic failure scenario, assesses the risk it poses to device availability and data integrity, explains how the platform detects the condition, defines the handling behavior, and specifies the recovery path.

---

## Device Loses Connectivity Mid-Download

**Scenario**

A device begins downloading a 50 MB firmware binary from the CDN and loses its network connection at 62% progress. The download state is partially written to the device's flash storage staging area. When the device reconnects, the platform has no record of the partial download state.

**Risk**

Without resume capability, the device must re-download the full binary on every connection drop. On constrained cellular links with metered data, repeated full re-downloads waste bandwidth, increase costs, and can exceed device data quotas. Repeated failed downloads can cause a device to remain on outdated firmware indefinitely.

**Detection**

The OTA Deployment Service tracks per-device download state as a state machine: `Notified → Downloading → Downloaded → Validating → Installing → Succeeded/Failed`. When a device reconnects after a connectivity loss, it reports its current download offset in the reconnect payload. The platform detects the discrepancy between the expected `Downloading` state and the device-reported resume offset.

**Handling**

The platform implements HTTP Range request support on the firmware download endpoint. Devices include a `Range: bytes=N-` header in their download request, where N is the last successfully written byte offset stored in non-volatile memory. The CDN serves the remaining bytes from the specified offset. The device appends the received bytes to its partial staging file rather than overwriting it.

The device SDK maintains a download manifest in non-volatile storage containing: firmware URL, expected total size, expected SHA-256 checksum, and last verified byte offset. The manifest is updated atomically (write to shadow + fsync) after each successfully received and written chunk.

**Recovery**

If the device's stored resume offset is invalid (e.g., non-volatile storage was corrupted), the device detects this by verifying the checksum of bytes already written. If the partial data is corrupt, the device resets its download offset to zero and starts a fresh download, reporting the reset to the platform. The platform logs the resume failure and increments the device's download retry counter. After three failed resume attempts, the platform escalates to an operator alert.

---

## Firmware Checksum Mismatch

**Scenario**

A device completes downloading a firmware binary but the computed SHA-256 checksum of the downloaded file does not match the expected checksum published in the firmware metadata. The mismatch could result from network-level data corruption, a CDN cache poisoning incident, or a firmware packaging error by the engineering team.

**Risk**

Installing a firmware binary with a checksum mismatch could result in unpredictable device behavior, ranging from non-boot (corrupted executable code) to security vulnerabilities if an attacker managed to substitute a malicious binary. This is a safety-critical failure for devices in industrial or medical contexts.

**Detection**

The device SDK performs a SHA-256 checksum verification of the complete downloaded binary before passing it to the firmware update handler. The checksum is computed on the staging partition in a streaming manner to avoid requiring the full binary in RAM. The computed checksum is compared against the `expectedChecksum` value from the firmware notification message, which itself was signed by the platform as part of the notification payload.

**Handling**

On checksum mismatch, the device:
1. Discards the downloaded binary from the staging partition (overwrites with zeros or marks the partition as invalid).
2. Reports the checksum failure to the platform with the computed checksum value and the expected checksum.
3. Does not attempt installation.
4. Waits for the platform to re-send the firmware notification with corrected metadata or a re-signed notification.

The platform receives the checksum failure report and:
1. Marks the device's update attempt as failed with reason `CHECKSUM_MISMATCH`.
2. Checks whether other devices in the same deployment batch have reported the same mismatch.
3. If more than 5% of a batch reports checksum mismatches, the deployment is automatically paused and an operator alert is raised to investigate whether the firmware binary is corrupt at the source.
4. If the issue is isolated to a single device, the platform re-queues the firmware notification for that device.

**Recovery**

If the root cause is a corrupt firmware binary in the repository, the engineer must re-upload a valid binary. The deployment is updated to reference the new binary, and affected devices are re-notified. All affected device download attempts are logged in the deployment audit trail.

If the root cause is network corruption, the device retries the download. The CDN's Content-MD5 header at the HTTP response level provides an additional layer of per-chunk integrity verification to catch network corruption early during the download rather than only at the end.

---

## Device Battery Critically Low During Update

**Scenario**

A battery-powered IoT device receives a firmware update notification while its battery level is at 18%. The device begins the download process before the battery threshold check is enforced, draining the battery further. If the battery depletes during the installation phase, the device may be left with a half-installed firmware and no power to complete the rollback.

**Risk**

A device bricked mid-firmware-install due to power loss is one of the most severe failure modes in OTA updates. It requires physical intervention for recovery and is especially costly for devices deployed in remote or inaccessible locations. This is a critical risk for battery-powered field sensors and wearable devices.

**Detection**

The device SDK checks battery level before beginning the firmware download. If battery level is below the configured minimum threshold (default: 25% for download, 40% for installation), the SDK defers the update and reports the deferral reason to the platform. The battery level is checked again at the installation phase even if it passed the download phase check.

**Handling**

1. The device reports `UPDATE_DEFERRED: BATTERY_CRITICAL` to the platform with the current battery level.
2. The platform marks the device's deployment status as `Deferred` with the deferral reason.
3. The platform schedules a deferred retry: the device will retry the update check when it next reports battery level above the minimum threshold.
4. The device SDK monitors battery level and re-evaluates the update eligibility when the battery level crosses back above the minimum threshold (charging detected).
5. For devices with no battery management feedback, the platform applies a time-based retry after a configurable deferral window (default: 4 hours).

For devices in contexts where powering down would cause operational risk (e.g., a medical device on battery backup), the device can report `UPDATE_DEFERRED: OPERATIONAL_LOCK` which requires a human operator to explicitly authorize the update window.

**Recovery**

If a device fails mid-install due to unexpected power loss (the battery level dropped faster than expected during installation), the device's hardware watchdog timer expires after a boot timeout and triggers a reset. The bootloader is responsible for detecting the incomplete installation and reverting to the last known good partition. The device reports `UPDATE_FAILED: POWER_LOSS_DURING_INSTALL` upon its next successful boot.

---

## Firmware Installs but Device Fails to Boot

**Scenario**

A device successfully downloads and validates a firmware binary, installs it to the staging partition, and reboots. The new firmware has a critical bug—a null pointer dereference in the early initialization code—that causes a panic before the MQTT stack initializes. The device enters a reboot loop.

**Risk**

A non-booting device is effectively offline and cannot receive any further commands or corrections from the platform. If the device is a sensor in a critical monitoring loop (e.g., pipeline pressure monitoring), its absence creates a gap in safety coverage. At scale, a buggy firmware released to thousands of devices simultaneously could cause a mass outage.

**Detection**

The platform detects non-boot by the absence of a boot confirmation message. After the device reboots following firmware installation, the platform expects a `DeviceFirmwareUpdateResult` message within a configurable boot confirmation window (default: 5 minutes). If no confirmation is received within the window, the platform marks the device as potentially failed and starts the watchdog escalation process.

On the device side, the firmware bootloader implements a boot counter mechanism: if the device reboots more than N times (default: 3) without successfully reaching the application initialization checkpoint, the bootloader automatically selects the previous firmware partition for the next boot.

**Handling**

1. Device-side watchdog timer expires (typically 60–120 seconds) and triggers a reset.
2. Bootloader increments the boot attempt counter.
3. After the configured maximum boot attempts, the bootloader activates the previous firmware partition.
4. Device boots into the previous firmware successfully and sends `UPDATE_FAILED: BOOT_FAILURE_ROLLBACK` with the new firmware version and boot attempt count.
5. The platform records the rollback event and marks the device's firmware version as the previous version.
6. The platform's Rollback Controller evaluates the failure rate across the deployment batch. If the failure rate exceeds the threshold, the entire deployment is paused.

**Recovery**

The engineering team must diagnose the boot failure from device diagnostic logs (if the device can upload them before the panic) and crash dump data (if the device has a dedicated crash log partition). A corrected firmware version must be released and a new deployment campaign created. The failed deployment is closed with a `FAILED` status and an incident ticket is created referencing the affected firmware version and the deployment ID.

---

## Mass Rollout Causing Thundering Herd on Download Servers

**Scenario**

A firmware deployment targets 500,000 devices simultaneously. The deployment notification is broadcast to all devices at the same time, and all devices begin downloading the 80 MB binary simultaneously, creating a 40 TB download burst that saturates the CDN edge capacity and causes download failures for many devices.

**Risk**

CDN saturation degrades download performance across all devices, causes timeouts and retry storms, and can spill over to affect other platform services if shared infrastructure is involved. Cascading retries from failed downloads amplify the initial burst, creating a self-reinforcing load spike.

**Detection**

The platform monitors CDN bandwidth utilization and download error rate via CDN analytics APIs. A sudden spike in 503 or 504 responses from the CDN triggers an automated deployment rate limiter alert. The Deployment Orchestrator also monitors the ratio of `Downloading` to `Notified` state transitions; a high rate of transitions back to `NotificationQueued` indicates download failures.

**Handling**

The platform implements a staggered notification strategy:
1. Devices are notified in waves, with each wave representing a configurable percentage of the target fleet (default: 5% per wave, 10-minute intervals between waves).
2. The OTA notification includes a randomized `downloadDelay` parameter (0–300 seconds) instructing the device to wait a random duration before initiating the download, distributing the download start times.
3. The CDN pre-warms targeted edge regions before large deployments by pre-populating the firmware binary to regional edge nodes during the deployment scheduling phase.
4. Per-device download bandwidth is rate-limited by the CDN (configurable per firmware version) to prevent any single device from monopolizing edge capacity.

**Recovery**

For an active thundering herd event, the platform pauses new wave notifications until the CDN error rate drops below the threshold. Devices that failed their initial download are re-queued with an increased randomized delay. The incident is recorded, and the deployment's wave size and inter-wave interval are adjusted for the remainder of the rollout.

---

## Incompatible Firmware Version for Device Hardware Variant

**Scenario**

A fleet contains three hardware variants of the same device model (rev A, rev B, rev C) that share the same `deviceType` but have different peripheral configurations—rev C has an additional sensor module that requires different driver code. A firmware binary compiled for rev A/B is inadvertently deployed to rev C devices, causing hardware initialization failures on the additional sensor module.

**Risk**

Hardware-incompatible firmware can cause devices to enter error states, lose functionality of specific sensors, or in extreme cases (for devices with hardware-specific power management code) cause hardware damage. Diagnosis is difficult because the device may partially function, providing misleading telemetry.

**Detection**

The firmware metadata schema includes a `hardwareVariants` field listing the specific hardware revision identifiers the binary is compatible with. The device reports its `hardwareRevision` identifier (read from device non-volatile storage or hardware fuses) in its provisioning payload and in firmware update precondition checks. The Deployment Service validates hardware variant compatibility before adding a device to a deployment batch.

**Handling**

1. The Batch Selector queries device hardware revision from the Device Registry before adding each device to a batch.
2. Devices not matching the firmware's `hardwareVariants` list are excluded from the batch and their status is set to `Skipped: HardwareIncompatible`.
3. If a device with an incompatible hardware revision somehow receives a notification (e.g., due to a stale hardware revision record in the registry), the device performs a local compatibility check by comparing its hardware revision against the compatibility list in the notification payload.
4. The device reports `UPDATE_REJECTED: HARDWARE_INCOMPATIBLE` and the platform logs the mismatch, flagging the device's hardware revision record for review.

**Recovery**

The engineering team must release a separate firmware binary compiled for the incompatible hardware variants and create a new deployment campaign targeting those variants specifically. The hardware revision records in the Device Registry should be audited to ensure all devices are correctly classified before the new deployment.

---

## Firmware Update During Active Critical Operation

**Scenario**

An industrial IoT device controlling a manufacturing line conveyor belt receives a firmware update notification while it is actively executing a conveyor movement sequence. Interrupting the firmware update process or rebooting mid-sequence could cause physical damage to goods on the belt or trigger a safety interlock.

**Risk**

For devices in safety-critical or operationally critical contexts, an unplanned reboot is not merely inconvenient—it can cause physical damage, safety incidents, or costly production downtime. This is especially relevant for medical devices, industrial controllers, and transportation systems.

**Detection**

Devices can assert an operational lock by publishing an `operationLock` status to their device shadow with a lock type and expected duration. The Deployment Orchestrator checks the device shadow for active operational locks before queuing a firmware notification. The platform respects the lock and defers the notification until the lock is released.

**Handling**

1. The device SDK exposes an `assertOperationLock(lockType, maxDurationSeconds)` API for application code to call when entering a critical operation.
2. The Deployment Orchestrator checks the device's `reported.operationLock` shadow field before adding the device to a notification batch.
3. If an operational lock is present, the device is moved to a `LockedDeferred` state and re-evaluated after the lock's `maxDuration` expires.
4. If the lock's max duration is exceeded without release (suggesting the device is stuck), the platform alerts an operator rather than forcing the update.
5. Deployment policies can be configured with a `respectOperationLocks` flag; for non-critical deployments, the lock is overridden after the maximum deferral window.

**Recovery**

For devices that fail to release operational locks (e.g., the application code has a bug that prevents lock release), a platform administrator can force-clear the operational lock via the Device Management API. This action is recorded in the audit trail with the administrator's identity and the justification field they must provide.

---

## Rollback Fails and Device Is Bricked

**Scenario**

The firmware watchdog triggers a rollback after the new firmware fails to boot, but the rollback itself fails because the previous firmware partition has been corrupted (e.g., a power loss occurred during the previous firmware write, silently corrupting the partition). The device cannot boot into either firmware and enters a continuous boot loop.

**Risk**

A bricked device is completely non-functional and requires physical recovery intervention. At scale, a scenario that bricks a significant percentage of a fleet (e.g., due to a storage driver bug that corrupts the backup partition on all devices of a certain hardware revision) could cause widespread service disruption and require costly field service operations.

**Detection**

The platform detects a bricked state by the absence of any device communication after a rollback window. If neither an update success nor a rollback report is received within the combined boot confirmation and rollback timeout window, the device is flagged as `StatusUnknown: PossiblyBricked`. Long-term absence from telemetry (configurable, e.g., 30 minutes for normally heartbeat-active devices) escalates to `Bricked` status.

**Handling**

1. The platform marks the device status as `Bricked` and raises an operator alert with high severity.
2. The platform checks whether other devices of the same hardware revision in the same deployment batch have entered the same state, which would indicate a systemic issue requiring deployment-wide action.
3. The deployment is paused immediately if more than the configured threshold of devices enter bricked state.
4. For devices with an out-of-band recovery interface (USB, JTAG, cellular fallback modem), the platform publishes recovery instructions and a known-good recovery firmware to the device's out-of-band channel if configured.

**Recovery**

Physical intervention is required. The recovery procedure depends on the device's hardware capabilities:
- **Recovery mode via physical button**: The device supports a hardware factory reset via a button held during power-on. This boots a minimal recovery firmware from a protected ROM partition that can receive a firmware image via USB or a dedicated recovery protocol.
- **Out-of-band modem**: Devices with a secondary low-bandwidth modem (e.g., NB-IoT for recovery) can receive a recovery firmware image over the secondary channel.
- **Field replacement**: If no recovery mechanism exists, the device must be returned for re-flashing at a service depot.

All bricked devices are tracked in a recovery campaign with their device IDs, affected firmware versions, and recovery status, enabling fleet-wide tracking of the recovery effort.

---

## Version Pinning Conflict Between Group Policy and Individual Device Override

**Scenario**

A device group policy pins all devices in the "production-floor-sensors" group to firmware version 4.2.1. An operator previously set an individual device override on device `sensor-0034` pinning it to version 4.1.8 for testing. A new deployment campaign targets the group with version 4.3.0. The platform must resolve the conflict between the group policy and the individual override.

**Risk**

Unresolved policy conflicts can result in devices receiving incorrect firmware versions, either preventing a critical security patch from being applied or unintentionally overriding a device-specific configuration required for a custom hardware variant.

**Detection**

The Batch Selector evaluates firmware version eligibility for each device individually by resolving the effective firmware policy from the device's policy inheritance chain. The resolution algorithm applies the most specific policy (individual device override > device group policy > platform default policy).

**Handling**

1. The Batch Selector detects the conflict for `sensor-0034` and applies the most-specific policy: the individual device override wins.
2. `sensor-0034` is excluded from the 4.3.0 deployment batch with status `Skipped: PolicyConflict: IndividualOverride`.
3. The conflict is logged and surfaced in the deployment report with the conflicting policies listed.
4. The operator who created the deployment receives an in-app notification listing all devices excluded due to policy conflicts.
5. To override the individual override and include the device in the group deployment, the operator must explicitly remove the device-level firmware pin before re-queuing the device.

**Recovery**

Operators can resolve policy conflicts through the Policy Management API. An explicit `override-all` flag can be passed when creating a deployment to force the deployment to supersede all individual device overrides, but this action requires elevated permissions and generates an audit trail entry.

---

## Concurrent Update Campaigns Targeting Same Device From Different Groups

**Scenario**

Device `gateway-0091` is a member of both the "building-automation" group and the "emergency-systems" group. Two separate deployment campaigns are created simultaneously: one targeting "building-automation" with firmware 3.5.0 and one targeting "emergency-systems" with firmware 3.4.2-emergency-patch. Both campaigns select the device and attempt to notify it concurrently.

**Risk**

Without conflict detection, the device could receive two competing firmware notifications, apply the first one, then receive the second notification and overwrite the newly installed firmware—potentially removing the emergency patch or installing the wrong firmware version for the device's primary operational role.

**Detection**

The Deployment Orchestrator uses a distributed lock per device ID when creating deployment batches. Before adding a device to a deployment batch, it checks whether the device already has an active deployment in progress. If a device is already in an active deployment, the second deployment attempt is rejected for that specific device.

**Handling**

1. The first deployment campaign to claim the device (earlier `scheduledAt` timestamp wins) locks the device for the duration of its deployment.
2. The second campaign logs `DeviceSkipped: ActiveDeploymentConflict` for the contested device.
3. The second campaign operator is notified of the conflict with the conflicting campaign ID and the locked device list.
4. After the first campaign completes (success or failure), the device lock is released.
5. The second campaign operator can then re-queue the skipped devices for inclusion in a new deployment or amendment to the existing campaign.

**Recovery**

For emergency patches (such as the "emergency-systems" campaign in this scenario), the platform supports a `priorityOverride` flag that allows the emergency campaign to preempt an in-progress non-emergency deployment. The device is instructed to abort its current download (if in progress), and the emergency firmware notification is sent with elevated priority. This flag requires the `deployment:emergency-override` permission and generates a mandatory audit log entry with a required justification field.

---

## Summary Table

| Edge Case | Severity | Primary Mitigation | Recovery Path |
|---|---|---|---|
| Connectivity lost mid-download | Medium | HTTP Range resume, download manifest | Device reset offset and restart |
| Checksum mismatch | High | SHA-256 + code signature validation | Re-download, investigate CDN integrity |
| Low battery during update | High | Battery threshold check before install phase | Defer until charged, watchdog rollback |
| New firmware fails to boot | Critical | Boot counter watchdog, dual partition | Automatic rollback, deployment pause |
| Thundering herd on CDN | Medium | Staggered waves, randomized delay, CDN pre-warm | Pause waves, re-queue with higher delay |
| Incompatible hardware variant | High | Hardware variant filtering in batch selection | Separate deployment per variant |
| Update during critical operation | High | Operational lock assertion, deferral | Force-clear by admin with audit trail |
| Rollback fails, device bricked | Critical | Out-of-band recovery, protected bootloader | Physical field recovery |
| Version pinning conflict | Medium | Policy inheritance resolution, most-specific wins | Operator explicitly removes override |
| Concurrent campaign conflict | Medium | Per-device deployment lock | Priority override for emergencies |
