# API Design - Ticketing and Project Management System

## API Style
- RESTful JSON APIs with organization and role-based authorization.
- Cursor pagination for activity-heavy collections.
- Idempotency keys for create operations exposed to client portals.
- Attachment uploads use pre-signed object storage URLs or a direct upload proxy.

## Core Endpoints

| Area | Method | Endpoint | Purpose |
|------|--------|----------|---------|
| Tickets | POST | `/api/v1/tickets` | Create a new ticket |
| Tickets | GET | `/api/v1/tickets/{ticketId}` | Fetch ticket detail |
| Tickets | PATCH | `/api/v1/tickets/{ticketId}` | Update status, fields, or metadata |
| Tickets | POST | `/api/v1/tickets/{ticketId}/comments` | Add comment or clarification |
| Tickets | POST | `/api/v1/tickets/{ticketId}/attachments` | Register attachment upload |
| Tickets | POST | `/api/v1/tickets/{ticketId}/assignments` | Assign or reassign owner |
| Projects | POST | `/api/v1/projects` | Create project |
| Projects | POST | `/api/v1/projects/{projectId}/milestones` | Create milestone |
| Projects | POST | `/api/v1/milestones/{milestoneId}/tasks` | Create task |
| Projects | PATCH | `/api/v1/milestones/{milestoneId}` | Update milestone plan |
| Releases | POST | `/api/v1/releases` | Create release or hotfix |
| Reports | GET | `/api/v1/reports/operational-summary` | Return SLA and project metrics |
| Admin | PATCH | `/api/v1/admin/sla-policies/{policyId}` | Update policy configuration |

## Example: Create Ticket

```json
{
  "projectId": "proj_123",
  "title": "Invoice export fails on mobile layout",
  "description": "Users receive a blank screen when opening exports on Safari.",
  "type": "bug",
  "severity": "high",
  "environment": "production",
  "attachmentIds": ["att_001"]
}
```

## Example: Create Milestone

```json
{
  "name": "Release 2.4 stabilization",
  "plannedDate": "2026-05-12",
  "ownerId": "usr_pm_01",
  "dependencyIds": ["milestone_ux_signoff"],
  "completionCriteria": [
    "All linked P1/P2 tickets closed",
    "Regression suite passed",
    "Client sign-off recorded"
  ]
}
```

## Authorization Notes
- Client tokens can create and read scoped tickets but cannot alter internal assignments or project plans.
- Internal tokens require project or operational scope to edit project, release, or administrative resources.
- Audit metadata is attached to every mutating request.
