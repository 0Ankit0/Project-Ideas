# State Machine Diagrams — Social Networking Platform

## 1. Overview

This document specifies the finite state machines that govern the lifecycle of the platform's core entities. Each `stateDiagram-v2` block defines all valid states, the transitions between them, the events that trigger those transitions, and any guard conditions. These models drive validation logic in service layers and database check constraints.

---

## 2. Post Lifecycle

A post progresses from initial drafting through publication and can be flagged, removed, or restored at any point. Scheduled posts introduce a time-delayed transition to published.

```mermaid
stateDiagram-v2
    [*] --> Draft : author creates post

    Draft --> Published : author submits\n[no active account suspension]
    Draft --> Scheduled : author sets future publishedAt\n[scheduledAt > now]
    Draft --> Deleted : author hard-deletes draft

    Scheduled --> Published : scheduler fires at scheduledAt
    Scheduled --> Draft : author unschedules\n[scheduledAt not yet reached]
    Scheduled --> Deleted : author deletes before publish

    Published --> Edited : author edits body or media\n[within edit window: 30 min]
    Edited --> Published : edit saved successfully
    Published --> Pinned : author/moderator pins post\n[max 3 pinned per profile]
    Pinned --> Published : author/moderator unpins

    Published --> FlaggedPendingReview : AI screener confidence ≥ 0.7\nOR report count threshold exceeded
    Edited --> FlaggedPendingReview : re-screen after edit detects violation
    Pinned --> FlaggedPendingReview : report received on pinned post

    FlaggedPendingReview --> Published : moderator clears — no violation found
    FlaggedPendingReview --> HiddenFromFeed : moderator issues soft-hide pending appeal
    FlaggedPendingReview --> Removed : moderator confirms policy violation

    HiddenFromFeed --> Removed : appeal period (7 days) expires with no appeal\nOR appeal denied by senior moderator
    HiddenFromFeed --> Published : author appeal upheld

    Removed --> Restored : successful appeal reviewed by senior moderator\n[within 30-day restore window]
    Removed --> PermanentlyDeleted : 30-day restore window expires\nOR author account permanently banned

    Published --> SoftDeleted : author soft-deletes\n[retains reactions & comment count in analytics]
    SoftDeleted --> Published : author restores within 30 days
    SoftDeleted --> PermanentlyDeleted : 30-day window expires

    Restored --> Published : restore completes
    PermanentlyDeleted --> [*]
    Deleted --> [*]
```

**State Descriptions:**

| State | Description |
|---|---|
| `Draft` | Post is being composed; visible only to the author. |
| `Scheduled` | Post is ready but will auto-publish at a future time. |
| `Published` | Post is visible to the audience defined by its visibility setting. |
| `Edited` | Transient state while an edit is being saved; reverts to Published. |
| `Pinned` | Publicly visible and surfaced at the top of the author's profile. |
| `FlaggedPendingReview` | Temporarily visible but queued for moderator review. |
| `HiddenFromFeed` | Removed from all feeds and search; author notified and appeal window open. |
| `Removed` | Taken down for policy violation; no longer publicly accessible. |
| `Restored` | Moderator overturned removal; transitioning back to Published. |
| `SoftDeleted` | Author-initiated removal; data retained for 30 days. |
| `PermanentlyDeleted` | Data purged from primary store; only anonymised analytics retained. |

---

## 3. User Account Status

User accounts move through states driven by verification events, terms-of-service violations, and voluntary deactivation.

```mermaid
stateDiagram-v2
    [*] --> PendingVerification : user completes registration

    PendingVerification --> Active : email verified within 72 hours
    PendingVerification --> Expired : verification link not used within 72 hours\n[account purged after 7 days]

    Active --> EmailUnverified : user changes email address\n[new verification email sent]
    EmailUnverified --> Active : new email verified within 72 hours
    EmailUnverified --> Active : user reverts to previous email

    Active --> TemporarilySuspended : moderator issues time-limited suspension\n(1 day – 90 days)
    TemporarilySuspended --> Active : suspension period expires automatically
    TemporarilySuspended --> PermanentlyBanned : user violates terms again during suspension\nOR appeal denied after escalation

    Active --> UnderInvestigation : severe report received\n[account restricted pending review]
    UnderInvestigation --> Active : investigation cleared — no violation
    UnderInvestigation --> TemporarilySuspended : violation confirmed, proportionate suspension applied
    UnderInvestigation --> PermanentlyBanned : egregious violation confirmed\n(CSAM, terrorism, doxing)

    Active --> Deactivated : user voluntarily deactivates account\n[30-day grace period; login resumes reactivation]
    Deactivated --> Active : user logs in within 30-day window
    Deactivated --> ScheduledForDeletion : 30-day window expires without reactivation

    ScheduledForDeletion --> Active : user logs in before deletion job runs\n[up to 14-day buffer]
    ScheduledForDeletion --> Deleted : deletion job completes\n[GDPR-compliant data erasure]

    PermanentlyBanned --> BanAppealed : user submits appeal within 60 days
    BanAppealed --> PermanentlyBanned : appeal denied by Trust & Safety team
    BanAppealed --> Active : appeal upheld — ban overturned with review notes

    PermanentlyBanned --> Deleted : ban remains unchallenged for 1 year\nOR user requests account deletion

    Expired --> [*]
    Deleted --> [*]
```

**State Descriptions:**

| State | Description |
|---|---|
| `PendingVerification` | Account created; awaiting email confirmation. |
| `Active` | Fully operational; all features available. |
| `EmailUnverified` | Account active but new email address awaiting confirmation. |
| `UnderInvestigation` | Account restricted; reduced posting and messaging capabilities. |
| `TemporarilySuspended` | Login blocked for a defined period; content hidden from public. |
| `PermanentlyBanned` | Login permanently blocked; public content removed. |
| `BanAppealed` | Ban under review by Trust & Safety team. |
| `Deactivated` | User-initiated dormancy; profile hidden but data retained. |
| `ScheduledForDeletion` | Irreversible deletion queued; GDPR erasure pipeline initiated. |
| `Deleted` | All PII erased; anonymised records retained for legal compliance. |
| `Expired` | Unverified account automatically purged. |

---

## 4. Content Report Status

A report moves through a structured moderation pipeline from submission to final resolution, with an optional appeal stage.

```mermaid
stateDiagram-v2
    [*] --> Submitted : reporter submits report via UI or API

    Submitted --> DuplicateClosedNoAction : system detects identical open report\nfrom same reporter on same target
    Submitted --> AutoScreening : AI screener picks up report\n[within 30 seconds SLA]

    AutoScreening --> AutoResolved : AI confidence ≥ 0.95 AND policy = CLEAR_VIOLATION\n[action applied automatically — CSAM / spam]
    AutoScreening --> UnderReview : AI confidence 0.4–0.95 — human review required
    AutoScreening --> AutoDismissed : AI confidence < 0.4 AND no prior reports on target\n[reporter notified, no action]

    UnderReview --> Escalated : content involves potential illegal activity\nOR high-profile account involved\nOR 50+ reports on same target in 1 hour
    UnderReview --> ActionTaken : moderator confirms violation\n[post removed / user suspended / content labelled]
    UnderReview --> Dismissed : moderator finds no violation after review

    Escalated --> ActionTaken : senior moderator or legal team applies action
    Escalated --> Dismissed : senior review finds no violation

    ActionTaken --> Appealed : target user (author) files appeal within 30 days
    Dismissed --> Appealed : reporter disputes dismissal within 14 days

    Appealed --> AppealUnderReview : Trust & Safety team claims appeal
    AppealUnderReview --> AppealUpheld : appeal upheld — original decision reversed
    AppealUnderReview --> AppealDenied : appeal denied — original decision stands

    AppealUpheld --> Resolved : content restored / suspension lifted\n[both parties notified]
    AppealDenied --> Resolved : no further recourse within platform\n[both parties notified]
    ActionTaken --> Resolved : appeal period expires with no appeal filed
    Dismissed --> Resolved : appeal period expires with no appeal filed
    AutoResolved --> [*]
    AutoDismissed --> [*]
    DuplicateClosedNoAction --> [*]
    Resolved --> [*]
```

**State Descriptions:**

| State | Description |
|---|---|
| `Submitted` | Report received and persisted; awaiting AI triage. |
| `AutoScreening` | AI classifier is evaluating the reported content. |
| `UnderReview` | Assigned to a human moderator in the moderation queue. |
| `Escalated` | Forwarded to senior moderation or legal team. |
| `ActionTaken` | Moderation action applied; subject and reporter notified. |
| `Dismissed` | Report reviewed; no policy violation found. |
| `AutoResolved` | AI applied action autonomously (high-confidence violations only). |
| `AutoDismissed` | AI determined no violation; report closed without human review. |
| `Appealed` | Target or reporter has filed a formal appeal. |
| `AppealUnderReview` | Appeal is being reviewed by Trust & Safety team. |
| `AppealUpheld` | Appeal succeeded; original decision reversed. |
| `AppealDenied` | Appeal rejected; original decision maintained. |
| `Resolved` | Report lifecycle complete; record retained for audit. |

---

## 5. Ad Campaign Status

An ad campaign moves from advertiser creation through platform approval, live delivery, and post-completion archival.

```mermaid
stateDiagram-v2
    [*] --> Draft : advertiser creates campaign

    Draft --> ReadyToSubmit : all required fields complete\n[name, budget, targeting, ≥1 creative]
    ReadyToSubmit --> Draft : advertiser continues editing

    ReadyToSubmit --> PendingReview : advertiser submits for approval
    Draft --> PendingReview : advertiser force-submits\n[validation warnings accepted]

    PendingReview --> UnderAdReview : ad reviewer claims campaign\n[SLA: 24 hours]
    UnderAdReview --> Approved : reviewer confirms policy compliance
    UnderAdReview --> Rejected : reviewer finds policy violation\n[rejection reason recorded]

    Rejected --> Draft : advertiser edits and resubmits
    Rejected --> [*] : advertiser abandons campaign after 60 days

    Approved --> Scheduled : startDate > now at time of approval
    Approved --> Active : startDate ≤ now — campaign launches immediately

    Scheduled --> Active : scheduler activates at startDate
    Scheduled --> Paused : advertiser pauses before start

    Active --> Paused : advertiser manually pauses\nOR daily budget exhausted (auto-pause until next day)\nOR payment failure detected
    Paused --> Active : advertiser resumes\nOR new day starts (budget reset)\nOR payment resolved

    Active --> BudgetExhausted : total budget fully spent
    BudgetExhausted --> Completed : campaign end date reached OR no budget left

    Active --> Completed : campaign endDate reached with budget remaining
    Active --> Cancelled : advertiser cancels mid-flight\n[prorated refund issued for unused budget]

    Paused --> Cancelled : advertiser cancels while paused
    Scheduled --> Cancelled : advertiser cancels before start\n[full refund]
    Approved --> Cancelled : advertiser cancels before start\n[full refund]

    Completed --> Archived : 90 days after completion\n[analytics retained indefinitely]
    Cancelled --> Archived : 30 days after cancellation
    Archived --> [*]
```

**State Descriptions:**

| State | Description |
|---|---|
| `Draft` | Campaign being configured; no ad serving. |
| `ReadyToSubmit` | All required fields complete; awaiting advertiser submission. |
| `PendingReview` | Submitted for platform policy review; no serving. |
| `UnderAdReview` | Assigned to a reviewer; active review in progress. |
| `Approved` | Cleared for delivery; waiting for startDate or launching. |
| `Rejected` | Policy violation found; advertiser must revise. |
| `Scheduled` | Approved and waiting for future startDate. |
| `Active` | Actively serving ads; impressions and clicks being recorded. |
| `Paused` | Serving halted (manually or due to budget/payment). |
| `BudgetExhausted` | Total budget consumed; serving stops. |
| `Completed` | Campaign finished; final billing reconciliation runs. |
| `Cancelled` | Advertiser terminated campaign early. |
| `Archived` | Historical record; read-only access for reporting. |
