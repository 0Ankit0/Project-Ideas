# Use Case Descriptions - Ticketing and Project Management System

## UC-01: Submit Ticket with Image Evidence
**Primary Actor**: Client Requester  
**Goal**: Report an issue with enough evidence for internal teams to reproduce it.

**Preconditions**:
- Client user belongs to an active organization.
- User has access to at least one project or support context.

**Main Flow**:
1. User opens the client portal and selects the affected project.
2. User enters title, description, category, severity, and environment details.
3. User uploads one or more screenshots.
4. System validates file type, size, and malware scan status.
5. System creates the ticket and activity timeline.
6. System notifies the triage queue.

**Alternate Flows**:
- A1: Similar open ticket exists -> system suggests linking instead of creating a duplicate.
- A2: Attachment scan pending -> ticket is created but evidence remains quarantined until cleared.

**Postconditions**:
- Ticket is visible to the client and internal triage team.
- Initial SLA clock starts according to policy.

---

## UC-02: Triage and Prioritize Ticket
**Primary Actor**: Support / Triage  
**Goal**: Validate intake, classify the issue, and set priority.

**Main Flow**:
1. Triage agent opens the new-ticket queue.
2. Agent reviews description, images, and history.
3. Agent confirms ticket type, impact, urgency, and affected module.
4. System calculates SLA targets.
5. Agent requests clarification or moves the ticket to assignment.

**Exceptions**:
- E1: Client project is inactive -> ticket is routed to admin review.
- E2: Ticket is out of support scope -> agent converts it to a change request or closes with explanation.

---

## UC-03: Assign Developer and Working Queue
**Primary Actor**: Support / Triage or Project Manager

**Main Flow**:
1. Assigner selects a team or individual owner.
2. System shows skill tags, workload, and milestone relevance.
3. Assigner sets due dates or attaches to an existing sprint/milestone.
4. Notification is sent to the assignee and watchers.
5. Ticket state changes to `assigned` or `in_progress`.

**Postconditions**:
- Ownership is explicit and traceable.
- SLA responsibility transfers to the assigned queue.

---

## UC-04: Create Project and Baseline Milestones
**Primary Actor**: Project Manager

**Main Flow**:
1. Project manager creates a project with client, objectives, dates, and owners.
2. Milestones are defined with target dates, dependencies, and completion criteria.
3. Team members are assigned to project roles.
4. System generates the project dashboard and milestone board.

**Success Criteria**:
- Project baseline is published and ready for linked tickets and tasks.

---

## UC-05: Link Ticket to Milestone or Change Request
**Primary Actor**: Project Manager or Support / Triage

**Main Flow**:
1. User selects a ticket and opens planning metadata.
2. User links the ticket to a project, milestone, and optional task.
3. System recalculates milestone progress and risk indicators.
4. Stakeholders are notified if the ticket changes committed scope.

**Alternate Flows**:
- A1: No milestone exists -> user creates a backlog item instead.
- A2: Ticket exceeds current milestone scope -> formal change request approval is required.

---

## UC-06: Implement Fix and Update Work Log
**Primary Actor**: Developer

**Main Flow**:
1. Developer accepts the assignment.
2. Developer reviews evidence, comments, and related tasks.
3. Developer records investigation notes and updates progress.
4. Developer links code review or deployment records.
5. Developer marks the ticket `ready_for_qa`.

**Exceptions**:
- E1: Issue blocked by another team -> developer marks blocker and pause reason.
- E2: Fix requires milestone change -> system creates a PM approval task.

---

## UC-07: Verify Fix and Close or Reopen
**Primary Actor**: QA Reviewer

**Main Flow**:
1. QA reviewer pulls the verification queue.
2. Reviewer validates acceptance criteria in the target environment.
3. Reviewer records pass/fail evidence.
4. If successful, system closes the ticket and updates linked work items.
5. If failed, system reopens the ticket with rejection notes.

**Postconditions**:
- Verification history is immutable.
- Client portal reflects the latest decision.

---

## UC-08: Manage Roles, SLA Rules, and Audit Access
**Primary Actor**: Admin

**Main Flow**:
1. Admin updates role templates, workflow rules, or SLA policies.
2. System validates policy conflicts and approval requirements.
3. Changes are versioned and applied to future records or migrated by policy.
4. Audit trail captures actor, time, previous value, and new value.
