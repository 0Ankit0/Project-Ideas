# State Machine Diagrams

## Overview
State machine diagrams model the lifecycle and valid state transitions for key entities in the CMS.

---

## 1. Post Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Draft : Author creates new post

    Draft --> Draft : Author saves draft / auto-save
    Draft --> PendingReview : Author submits for review

    PendingReview --> Draft : Editor returns with feedback
    PendingReview --> Published : Editor publishes immediately
    PendingReview --> Scheduled : Editor sets scheduled datetime

    Scheduled --> Published : System auto-publishes at scheduled time
    Scheduled --> Draft : Admin or Editor cancels schedule

    Published --> Archived : Editor or Admin archives post
    Published --> Draft : Admin reverts to draft (unpublish)

    Archived --> Published : Admin restores post
    Archived --> Trashed : Admin moves to trash

    Draft --> Trashed : Author or Admin trashes draft

    Trashed --> Draft : Admin restores within retention window
    Trashed --> [*] : System permanently deletes after retention period
```

---

## 2. Comment Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Submitted : Reader submits comment

    Submitted --> SpamChecking : System submits to spam filter
    SpamChecking --> Spam : High spam score
    SpamChecking --> AutoApproved : Low score + trusted reader
    SpamChecking --> Pending : Medium score or new reader

    Pending --> Approved : Moderator approves
    Pending --> Rejected : Moderator rejects
    Pending --> Spam : Moderator marks as spam

    AutoApproved --> Approved : State normalised

    Approved --> Rejected : Moderator later removes approved comment
    Approved --> Spam : Moderator escalates to spam

    Spam --> [*] : Periodically purged
    Rejected --> [*] : Deleted immediately
    Approved --> [*] : Post is deleted (cascade)
```

---

## 3. Widget Placement Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Unplaced : Widget type registered in library

    Unplaced --> Placed : Admin drags widget into a zone
    Placed --> Configured : Admin opens and saves configuration form
    Configured --> Placed : Admin clears configuration (resets to defaults)
    Configured --> Reordered : Admin changes position within zone
    Reordered --> Configured : Stable position

    Configured --> MovedZone : Admin moves widget to different zone
    MovedZone --> Configured : Stable in new zone

    Placed --> Removed : Admin removes widget from zone
    Configured --> Removed : Admin removes widget from zone
    Removed --> Unplaced : Widget type still available in library

    note right of Configured
        Layout cache invalidated
        on every configuration save
    end note
```

---

## 4. Theme Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Installed : Admin installs from marketplace or upload

    Installed --> Previewing : Admin triggers live preview
    Previewing --> Installed : Admin cancels preview
    Previewing --> Activating : Admin confirms activation

    Installed --> Activating : Admin activates directly (skipping preview)

    Activating --> Active : Widget zones migrated; cache invalidated
    Active --> Deactivated : Admin activates a different theme

    Deactivated --> Activating : Admin re-activates this theme
    Deactivated --> [*] : Admin uninstalls theme

    Active --> [*] : Cannot uninstall the active theme directly
```

---

## 5. User / Site Membership Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Invited : Admin sends invitation

    Invited --> Invitation_Expired : Invitation token expires (24 h)
    Invitation_Expired --> [*] : Invitation purged

    Invited --> Active : User accepts invitation and sets password

    Active --> Suspended : Admin suspends user
    Suspended --> Active : Admin reinstates user
    Suspended --> Deactivated : Admin deactivates permanently

    Active --> Deactivated : User requests account deletion (GDPR erasure)
    Deactivated --> [*] : Data erased after retention period
```

---

## 6. Plugin Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Downloaded : Admin initiates install from marketplace or upload

    Downloaded --> CompatibilityCheck : System validates against CMS version and hook API

    CompatibilityCheck --> Installed : Compatibility passed
    CompatibilityCheck --> IncompatibleWarning : Compatibility failed
    IncompatibleWarning --> Installed : Admin overrides and proceeds
    IncompatibleWarning --> [*] : Admin cancels install

    Installed --> Active : Admin activates plugin
    Active --> Inactive : Admin deactivates plugin

    Inactive --> Active : Admin re-activates plugin
    Inactive --> [*] : Admin uninstalls (files removed)

    Active --> Updating : Admin triggers update
    Updating --> Active : Update successful
    Updating --> Active : Update failed, rollback applied
```
