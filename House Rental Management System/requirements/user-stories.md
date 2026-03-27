# User Stories

## Owner / Landlord User Stories

### Account & Portfolio Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| OWN-001 | As an owner, I want to register my account so that I can manage my properties | - Email/phone validation<br>- OTP verification<br>- Profile created |
| OWN-002 | As an owner, I want to upload my identity documents so that the platform can verify me | - Document upload form<br>- Verification status shown<br>- Rejection with reason |
| OWN-003 | As an owner, I want to add a property so that I can list units for rent | - Property form with address<br>- Photo upload<br>- Amenities tagging |
| OWN-004 | As an owner, I want to add multiple units to a property so that each unit is managed separately | - Unit form per floor/number<br>- Base rent configured<br>- Status set to vacant |
| OWN-005 | As an owner, I want to publish a unit listing so that prospective tenants can view it | - Toggle publish/unpublish<br>- Listing visible to tenants<br>- Listing removed when occupied |

### Tenant & Lease Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| OWN-006 | As an owner, I want to review tenant applications so that I can select the right tenant | - Application list per unit<br>- Applicant details visible<br>- Approve/reject with reason |
| OWN-007 | As an owner, I want to create a lease agreement so that the rental terms are formalised | - Lease template selected<br>- Terms configured<br>- Sent for tenant signature |
| OWN-008 | As an owner, I want to receive notification when a tenant signs the lease so that I can countersign | - Sign notification sent<br>- Countersign action available<br>- Signed PDF stored |
| OWN-009 | As an owner, I want to renew a lease before it expires so that I avoid vacancy | - Renewal alert X days before expiry<br>- Updated terms set<br>- Renewal offer sent to tenant |
| OWN-010 | As an owner, I want to terminate a lease so that I can reclaim the unit | - Termination reason recorded<br>- Notice period enforced<br>- Move-out inspection scheduled |

### Rent Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| OWN-011 | As an owner, I want rent invoices generated automatically so that I don't miss billing | - Invoice on billing cycle date<br>- Correct amount including fees<br>- Tenant notified |
| OWN-012 | As an owner, I want to set late fee rules so that tenants are incentivised to pay on time | - Grace period configurable<br>- Fee type (flat/percent) set<br>- Auto-applied after grace |
| OWN-013 | As an owner, I want to view overdue payments so that I can take action | - Overdue list with days past due<br>- Escalation action available<br>- Export to CSV |
| OWN-014 | As an owner, I want to record offline rent payments so that the ledger stays accurate | - Manual payment entry<br>- Reference number recorded<br>- Tenant notified |

### Bills & Utilities

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| OWN-015 | As an owner, I want to add utility bills per unit so that tenants can pay them | - Bill form with utility type<br>- Amount and due date set<br>- Tenant notified |
| OWN-016 | As an owner, I want to split a common utility bill across tenants so that costs are shared fairly | - Split method selected (equal/proportional)<br>- Individual amounts calculated<br>- Bills assigned to tenants |
| OWN-017 | As an owner, I want to attach a scanned copy of the utility bill so that tenants can verify the charge | - File attachment upload<br>- Tenant can download scan<br>- Stored securely |

### Maintenance

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| OWN-018 | As an owner, I want to receive maintenance requests from tenants so that I can manage repairs | - Request notification sent<br>- Request visible in dashboard<br>- Priority indicated |
| OWN-019 | As an owner, I want to assign a maintenance request to staff so that it is resolved promptly | - Staff selection available<br>- Assignee notified<br>- Status updates visible |
| OWN-020 | As an owner, I want to approve completed maintenance so that requests are formally closed | - Completion notes reviewed<br>- Approve or reopen action<br>- Tenant notified of closure |
| OWN-021 | As an owner, I want to schedule preventive maintenance so that property condition is maintained | - Task type and recurrence set<br>- Assigned to staff<br>- Reminder sent before due date |
| OWN-022 | As an owner, I want to log the cost of maintenance work so that expenses are tracked | - Cost amount and category entered<br>- Linked to request<br>- Included in expense report |

### Reporting & Analytics

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| OWN-023 | As an owner, I want to see a financial dashboard so that I understand my portfolio performance | - Total income shown<br>- Outstanding balances shown<br>- Occupancy rate shown |
| OWN-024 | As an owner, I want to generate a rent roll so that I know the status of all units | - All units listed<br>- Tenant and rent status shown<br>- Exportable to CSV/PDF |
| OWN-025 | As an owner, I want to generate a tax summary report so that I can file taxes correctly | - Annual income totals<br>- Deductible expenses listed<br>- Export to PDF |

---

## Tenant User Stories

### Account Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| TEN-001 | As a tenant, I want to register an account so that I can apply for properties | - Email/phone validation<br>- OTP verification<br>- Profile created |
| TEN-002 | As a tenant, I want to upload my ID and employment documents so that my application is complete | - Document upload form<br>- Upload confirmation<br>- Visible to owner on application |
| TEN-003 | As a tenant, I want to manage my profile so that my contact info stays current | - Edit name/phone/email<br>- Emergency contact update<br>- Save confirmed |

### Property Search & Application

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| TEN-004 | As a tenant, I want to browse available units so that I can find a suitable home | - Unit listing with photos<br>- Filters (rent, bedrooms, area)<br>- Map view option |
| TEN-005 | As a tenant, I want to view unit details so that I can make an informed decision | - Full photo gallery<br>- Amenities list<br>- Lease terms and policies shown |
| TEN-006 | As a tenant, I want to submit a rental application so that the owner can review me | - Application form submitted<br>- Documents attached<br>- Confirmation receipt |
| TEN-007 | As a tenant, I want to track my application status so that I know if I'm approved | - Status visible (pending, approved, rejected)<br>- Rejection reason shown<br>- Approval notification sent |

### Lease

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| TEN-008 | As a tenant, I want to review and sign the lease digitally so that I can move in | - Lease document readable<br>- E-sign action available<br>- Signed copy emailed |
| TEN-009 | As a tenant, I want to view my active lease so that I know my obligations | - Lease terms visible<br>- Key dates highlighted<br>- Download as PDF |
| TEN-010 | As a tenant, I want to receive renewal notifications so that I can plan ahead | - Renewal alert before expiry<br>- New terms visible<br>- Accept/decline action |

### Rent & Bills

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| TEN-011 | As a tenant, I want to view my current rent invoice so that I know what is due | - Invoice amount and due date shown<br>- Breakdown of charges<br>- Pay now button |
| TEN-012 | As a tenant, I want to pay rent online so that I can pay conveniently | - Payment method selection<br>- Payment confirmation screen<br>- Receipt emailed |
| TEN-013 | As a tenant, I want to view my rent payment history so that I have a record | - All past payments listed<br>- Receipts downloadable<br>- Ledger balance shown |
| TEN-014 | As a tenant, I want to view my utility bills so that I understand my charges | - Bills listed with type and amount<br>- Scanned bill downloadable<br>- Pay action available |
| TEN-015 | As a tenant, I want to dispute a bill so that incorrect charges are corrected | - Dispute reason submitted<br>- Owner notified<br>- Resolution tracked |

### Maintenance

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| TEN-016 | As a tenant, I want to submit a maintenance request so that repairs are done | - Request form with description<br>- Photo upload<br>- Priority selection |
| TEN-017 | As a tenant, I want to track my maintenance request so that I know the progress | - Status visible (open, assigned, in-progress, resolved)<br>- Timeline of updates shown<br>- Completion notification |
| TEN-018 | As a tenant, I want to rate a resolved maintenance request so that quality is recorded | - Star rating after resolution<br>- Optional comment<br>- Feedback saved |

---

## Maintenance Staff User Stories

### Daily Operations

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| MNT-001 | As maintenance staff, I want to view my assigned tasks so that I know my workload | - Task list with priority<br>- Property and unit address shown<br>- Due date visible |
| MNT-002 | As maintenance staff, I want to accept or decline an assignment so that my availability is managed | - Accept/decline action<br>- Decline reason recorded<br>- Owner notified |
| MNT-003 | As maintenance staff, I want to update task status so that the owner and tenant are informed | - Status update buttons (in-progress, completed)<br>- Notes and photos attached<br>- Timestamp logged |
| MNT-004 | As maintenance staff, I want to log materials used so that costs are tracked | - Material name and cost entered<br>- Linked to task<br>- Saved to maintenance record |
| MNT-005 | As maintenance staff, I want to view my task history so that I can reference past work | - Completed tasks listed<br>- Notes and photos accessible<br>- Filterable by property |

---

## Admin User Stories

### Dashboard & Oversight

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ADM-001 | As an admin, I want to view platform metrics so that I can monitor system health | - Total owners, tenants, properties shown<br>- Recent transactions visible<br>- Alert indicators |
| ADM-002 | As an admin, I want to generate platform reports so that usage is analysed | - Custom date range<br>- Export to CSV<br>- Scheduled reports |

### User Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ADM-003 | As an admin, I want to verify owner identity documents so that the platform is trustworthy | - Document review interface<br>- Approve/reject with reason<br>- Owner notified |
| ADM-004 | As an admin, I want to suspend or deactivate user accounts so that violations are enforced | - Account action with reason<br>- User notified<br>- Audit log entry created |
| ADM-005 | As an admin, I want to manage admin roles so that access is controlled | - Role creation<br>- Permission matrix<br>- Assign to admin users |

### Dispute Resolution

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ADM-006 | As an admin, I want to view and resolve disputes between owners and tenants so that conflicts are mediated | - Dispute list with details<br>- Messaging thread visible<br>- Resolution recorded |
| ADM-007 | As an admin, I want to override a payment status in exceptional cases so that records are corrected | - Override action with reason<br>- Audit log entry<br>- Parties notified |

### Platform Configuration

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ADM-008 | As an admin, I want to manage lease templates so that owners can use standardised agreements | - Template editor<br>- Version control<br>- Publish/unpublish |
| ADM-009 | As an admin, I want to configure notification templates so that communications are consistent | - Template editor per event type<br>- Preview function<br>- Save and publish |
| ADM-010 | As an admin, I want to view audit logs so that all platform actions are traceable | - Filterable by user, action, date<br>- Immutable log entries<br>- Export to CSV |
