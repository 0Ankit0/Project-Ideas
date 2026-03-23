# User Stories - Ticketing and Project Management System

## Client Requester

- **US-CR-001**: As a client requester, I want to submit a ticket with screenshots so the internal team can understand the issue quickly.
  - Acceptance: title and description are mandatory; image uploads are validated and previewable.
- **US-CR-002**: As a client requester, I want to see ticket status and latest comments so I know whether I need to provide more information.
- **US-CR-003**: As a client requester, I want to link a ticket to my project or module so it reaches the correct delivery team.
- **US-CR-004**: As a client requester, I want to confirm whether a fix solved my problem so the team can close the issue with confidence.

## Support / Triage

- **US-ST-001**: As a triage agent, I want a queue of newly created tickets so I can validate and prioritize them consistently.
- **US-ST-002**: As a triage agent, I want suggested duplicates and similar recent incidents so I can avoid fragmented work.
- **US-ST-003**: As a triage agent, I want SLA timers and escalation flags so urgent issues are not missed.
- **US-ST-004**: As a triage agent, I want to request clarification from the client without losing ticket ownership or history.

## Project Manager

- **US-PM-001**: As a project manager, I want to create projects and milestones so delivery planning happens in the same tool as issue handling.
- **US-PM-002**: As a project manager, I want to associate tickets with milestones, releases, and risks so scope is visible end to end.
- **US-PM-003**: As a project manager, I want dependency tracking between milestones and tasks so I can forecast delays.
- **US-PM-004**: As a project manager, I want change requests and re-baselining history so schedule changes are transparent.

## Developer

- **US-DEV-001**: As a developer, I want clear assignment details, reproduction evidence, and target milestone information so I can start work quickly.
- **US-DEV-002**: As a developer, I want to update progress and log technical notes so others can follow the investigation.
- **US-DEV-003**: As a developer, I want to link work items to pull requests and releases so delivery traceability is preserved.
- **US-DEV-004**: As a developer, I want to flag blocked work with external dependencies so project managers can react before dates slip.

## QA / Reviewer

- **US-QA-001**: As a QA reviewer, I want a verification queue grouped by release and milestone so I can validate fixes efficiently.
- **US-QA-002**: As a QA reviewer, I want to reopen failed tickets and record rejection reasons so the team can iterate with evidence.
- **US-QA-003**: As a QA reviewer, I want acceptance criteria and expected environment details on every ticket so testing is unambiguous.

## Admin

- **US-ADM-001**: As an admin, I want to manage role templates and access policies so the right users see the right data.
- **US-ADM-002**: As an admin, I want configurable categories, priorities, SLA policies, and workflow rules so the system fits different teams.
- **US-ADM-003**: As an admin, I want immutable audit logs and export capability so operational and compliance reviews are possible.
