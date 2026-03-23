# Data Dictionary - Ticketing and Project Management System

| Entity | Key Fields | Description |
|--------|------------|-------------|
| Organization | id, name, status, supportTier | Client company or internal business unit |
| User | id, organizationId, displayName, email, accountType, status | Authenticated person in the platform |
| RoleAssignment | userId, scopeType, scopeId, roleName | Access grant within organization, project, or admin scope |
| Project | id, organizationId, name, ownerId, status, health, targetEndDate | Delivery initiative for a client or internal team |
| Milestone | id, projectId, name, ownerId, status, plannedDate, forecastDate | Time-bound delivery checkpoint |
| Task | id, projectId, milestoneId, parentTaskId, assigneeId, status, dueDate | Executable work item linked to delivery planning |
| Ticket | id, organizationId, projectId, milestoneId, type, priority, status, reporterId | Reported issue, incident, or change request |
| TicketAttachment | id, ticketId, storageKey, mimeType, sizeBytes, scanStatus | Stored evidence such as screenshots |
| TicketComment | id, ticketId, authorId, visibility, body, createdAt | Timeline comment or clarification |
| Assignment | id, ticketId, assigneeId, assignedBy, assignedAt, dueAt | Ownership history for a ticket |
| Release | id, projectId, milestoneId, version, status, plannedAt, deployedAt | Delivery package or hotfix event |
| Notification | id, recipientId, channel, templateKey, status, sentAt | Outbound user communication |
| AuditLog | id, actorId, action, entityType, entityId, before, after, createdAt | Immutable history of changes |
