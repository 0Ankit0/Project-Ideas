# Business Rules - Ticketing and Project Management System

## Access and Data Isolation
- Client users may only view tickets and project summaries for their own organization.
- Internal users require explicit project membership or elevated operational roles to access delivery records.
- Admin-only actions such as policy edits and audit exports require privileged roles and logging.

## Priority and SLA Matrix

| Priority | Typical Meaning | First Response Target | Resolution Target |
|----------|-----------------|-----------------------|-------------------|
| P1 | Service outage / critical blocker | 15 minutes | 4 hours or approved workaround |
| P2 | Major function degraded | 1 hour | 1 business day |
| P3 | Normal defect / planned fix | 4 business hours | 5 business days |
| P4 | Minor improvement / low impact | 1 business day | Managed through backlog or next milestone |

## Assignment Rules
- Every open ticket must have either a named assignee or an accountable queue.
- Reassignment must preserve prior ownership history.
- Tickets linked to committed milestones require PM notification when ownership changes.

## Milestone Governance
- A milestone cannot be marked complete while linked blocking tickets remain open.
- Scope additions after milestone approval require change-request tracking.
- Forecast dates may change, but baseline dates must remain historically visible.

## Closure and Reopen Rules
- Only QA reviewers, project managers, or authorized support agents may close tickets.
- Reopened tickets inherit the prior history and create a new verification cycle.
- Ticket closure requires either client confirmation or documented internal acceptance criteria.

## Attachment Controls
- Unsupported file types are rejected before storage.
- Malware-positive uploads remain quarantined and inaccessible to other users.
- Attachment metadata must include uploader, timestamp, and scan outcome.
