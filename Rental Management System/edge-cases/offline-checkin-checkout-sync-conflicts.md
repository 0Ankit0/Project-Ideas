# Offline Check-in/Check-out Sync Conflicts

## Failure Modes
- Staff device records events offline with stale contract version
- Duplicate sync on reconnect produces double transitions
- Clock skew causes out-of-order event application

## Controls
- Event versioning and conflict resolution by authoritative timeline
- Idempotent event keys and sync acknowledgements
- Manual reconciliation queue for unresolved conflicts
