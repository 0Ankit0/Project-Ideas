# User Stories

## Owner / Operator User Stories

### Account & Asset Portfolio

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| OWN-001 | As an owner, I want to register my account so that I can manage my rental assets | - Email/phone validated<br>- OTP verified<br>- Profile created |
| OWN-002 | As an owner, I want to upload my identity and business documents so that the platform can verify me | - Document upload form<br>- Verification status shown<br>- Rejection reason provided |
| OWN-003 | As an owner, I want to create an asset category so that my assets are organised correctly | - Category name and type selected<br>- Custom attribute fields defined<br>- Saved successfully |
| OWN-004 | As an owner, I want to add a new asset so that customers can book it | - Asset form with name, photos, attributes<br>- Pricing rules configured<br>- Asset saved as draft |
| OWN-005 | As an owner, I want to set pricing rules (hourly, daily, weekly) so that customers are billed correctly | - Rate tiers configured<br>- Min/max duration set<br>- Peak pricing windows defined |
| OWN-006 | As an owner, I want to manage the asset's availability calendar so that bookings reflect real availability | - Availability window set<br>- Blocked dates visible<br>- Booked dates locked automatically |
| OWN-007 | As an owner, I want to publish an asset listing so that customers can discover and book it | - Toggle publish/unpublish<br>- Listing visible in search<br>- Draft mode available |

### Booking Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| OWN-008 | As an owner, I want to review and approve booking requests so that I control who rents my assets | - Pending booking list shown<br>- Customer profile and documents visible<br>- Approve/decline with reason |
| OWN-009 | As an owner, I want to enable instant booking so that customers can confirm without waiting | - Instant booking toggle per asset<br>- Auto-confirmed on availability check<br>- Owner notified |
| OWN-010 | As an owner, I want to view all active and upcoming bookings so that I can plan operations | - Booking list with status<br>- Calendar view available<br>- Filterable by asset and status |
| OWN-011 | As an owner, I want to cancel a booking with a reason so that the customer is informed promptly | - Cancellation reason recorded<br>- Refund policy applied<br>- Customer notified |

### Agreements & Deposits

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| OWN-012 | As an owner, I want to generate a rental agreement for a confirmed booking so that terms are formalised | - Template selected<br>- Agreement pre-filled with booking details<br>- Sent to customer for signing |
| OWN-013 | As an owner, I want to countersign the rental agreement so that it becomes binding | - Customer signature confirmed<br>- Countersign action available<br>- Signed PDF stored and emailed |
| OWN-014 | As an owner, I want to configure the security deposit for each asset so that damages are covered | - Deposit amount set per asset<br>- Collected on booking confirmation<br>- Refund window configurable |
| OWN-015 | As an owner, I want to release or partially deduct the security deposit after return so that fair settlement is processed | - Deposit itemisation form<br>- Deduction reasons recorded with evidence<br>- Refund/deduction processed |

### Payments & Charges

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| OWN-016 | As an owner, I want rent invoices generated automatically on booking confirmation so that billing is consistent | - Invoice with period and amount<br>- Customer notified<br>- Tax included |
| OWN-017 | As an owner, I want to add additional charges after a return so that damage or late fees are collected | - Charge type selected (damage, late return, cleaning, etc.)<br>- Customer notified<br>- Evidence attachment supported |
| OWN-018 | As an owner, I want to view my payout history so that I can track my earnings | - Payout list with dates and amounts<br>- Commission deduction visible<br>- Export to CSV |

### Condition Assessments & Maintenance

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| OWN-019 | As an owner, I want staff to complete a pre-rental condition assessment so that the asset's state is recorded before handover | - Checklist form per category<br>- Photos uploaded<br>- Customer countersigns |
| OWN-020 | As an owner, I want staff to complete a post-rental condition assessment so that any damage is documented | - Post-rental checklist filled<br>- Comparison with pre-rental shown<br>- Damage charge prompted if discrepancy |
| OWN-021 | As an owner, I want to log a maintenance request for an asset so that repairs are tracked | - Request created with description<br>- Asset blocked in calendar<br>- Staff assigned |
| OWN-022 | As an owner, I want to schedule preventive servicing for assets so that they remain in good condition | - Service task with recurrence set<br>- Reminder sent before due date<br>- Asset blocked during service |

### Reporting

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| OWN-023 | As an owner, I want to view a financial dashboard so that I understand my portfolio performance | - Total revenue, expenses, and net income shown<br>- Asset utilisation rate shown<br>- Month-over-month comparison |
| OWN-024 | As an owner, I want to generate a utilisation report so that I can identify underperforming assets | - Booked days vs. available days per asset<br>- Exportable to CSV/PDF |
| OWN-025 | As an owner, I want to generate a tax summary report so that I can file taxes correctly | - Annual income totals<br>- Deductible expenses listed<br>- Export to PDF |

---

## Customer / Renter User Stories

### Account Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| CUS-001 | As a customer, I want to register an account so that I can book rental assets | - Email/phone validated<br>- OTP verified<br>- Profile created |
| CUS-002 | As a customer, I want to upload my ID so that owners can verify my identity | - Document upload form<br>- Upload confirmation<br>- Visible to owner on booking |
| CUS-003 | As a customer, I want to manage my profile so that my contact and payment info stays current | - Edit name/phone/email<br>- Saved payment methods manageable<br>- Save confirmed |

### Search & Booking

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| CUS-004 | As a customer, I want to search available assets so that I can find what I need | - Category filter<br>- Date/time range picker<br>- Location filter<br>- Price range filter |
| CUS-005 | As a customer, I want to view an asset's listing so that I can assess it before booking | - Photos gallery<br>- Attributes and specs shown<br>- Pricing breakdown shown<br>- Availability calendar shown |
| CUS-006 | As a customer, I want to submit a booking request so that I can reserve the asset | - Dates and times selected<br>- Pricing summary confirmed<br>- Booking request submitted |
| CUS-007 | As a customer, I want to track my booking status so that I know if it is confirmed | - Status visible (pending, confirmed, declined)<br>- Decline reason shown<br>- Confirmation notification sent |
| CUS-008 | As a customer, I want to modify my booking dates so that I can adjust my plan | - Modification request form<br>- Price difference shown<br>- Owner approval required if manual mode |
| CUS-009 | As a customer, I want to cancel my booking so that I can change my plans | - Cancellation button available<br>- Refund amount calculated and shown<br>- Cancellation confirmed |

### Agreements & Payments

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| CUS-010 | As a customer, I want to review and sign the rental agreement digitally so that I can proceed with the booking | - Agreement document readable<br>- E-sign action available<br>- Signed copy emailed to me |
| CUS-011 | As a customer, I want to pay the rental invoice online so that the booking is confirmed | - Payment method selection<br>- Secure checkout<br>- Receipt emailed |
| CUS-012 | As a customer, I want to view my payment history so that I have records of all transactions | - All past invoices listed<br>- Receipts downloadable<br>- Outstanding balances shown |
| CUS-013 | As a customer, I want to dispute an additional charge so that unfair fees are reviewed | - Dispute reason submitted<br>- Owner notified<br>- Resolution tracked |

### Condition Assessments & Returns

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| CUS-014 | As a customer, I want to countersign the pre-rental condition assessment so that I acknowledge the asset's state | - Pre-rental checklist visible<br>- Photos viewable<br>- Countersign action available |
| CUS-015 | As a customer, I want to initiate a return so that the owner is notified I am handing back the asset | - Return initiation form<br>- Actual return time recorded<br>- Owner and staff notified |
| CUS-016 | As a customer, I want to view the post-rental assessment report so that I know if any charges apply | - Report visible after return<br>- Comparison with pre-rental shown<br>- Damage charges itemised |

### Reviews

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| CUS-017 | As a customer, I want to rate and review an asset after a completed rental so that others can make informed decisions | - Star rating (1–5)<br>- Optional text review<br>- Submitted after rental closes |
| CUS-018 | As a customer, I want to view reviews of an asset so that I can trust the listing | - Reviews visible on listing page<br>- Average rating shown<br>- Sorted by most recent |

---

## Staff User Stories

### Daily Operations

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| STF-001 | As staff, I want to view my assigned tasks so that I know what assessments and maintenance to perform | - Task list with type (pre-rental, post-rental, maintenance)<br>- Asset and booking info shown<br>- Due time visible |
| STF-002 | As staff, I want to complete a pre-rental condition assessment so that the asset's state is captured before handover | - Category-specific checklist<br>- Photo capture per item<br>- Submit assessment |
| STF-003 | As staff, I want to complete a post-rental condition assessment so that any damage is documented | - Post-rental checklist<br>- Photo capture<br>- Comparison summary shown |
| STF-004 | As staff, I want to update a maintenance task status so that the owner knows the progress | - Status update (in-progress, completed)<br>- Work notes and photos added<br>- Completion submitted for approval |
| STF-005 | As staff, I want to log parts and materials used in a maintenance job so that costs are tracked | - Item name and cost entered<br>- Linked to maintenance task<br>- Saved to record |

### Schedule & History

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| STF-006 | As staff, I want to view my work schedule so that I can plan my day | - Upcoming tasks in time order<br>- Asset location shown<br>- Calendar view available |
| STF-007 | As staff, I want to view my completed task history so that I can reference past work | - Completed tasks listed<br>- Notes and photos accessible<br>- Filterable by asset and date |

---

## Admin User Stories

### Dashboard & Oversight

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ADM-001 | As an admin, I want to view platform metrics so that I can monitor system health | - Total owners, customers, bookings, and revenue shown<br>- Recent activity feed<br>- Alert indicators |
| ADM-002 | As an admin, I want to generate platform-wide reports so that usage trends are understood | - Custom date range<br>- Export to CSV<br>- Scheduled reports |
| ADM-003 | As an admin, I want to view audit logs so that all actions are traceable | - Filterable by user, action, date<br>- Immutable entries<br>- Export to CSV |

### User & Content Management

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ADM-004 | As an admin, I want to verify owner identity and business documents so that the platform is trustworthy | - Document review interface<br>- Approve/reject with reason<br>- Owner notified |
| ADM-005 | As an admin, I want to suspend or deactivate user accounts so that policy violations are enforced | - Suspension reason recorded<br>- User notified<br>- Audit log entry created |
| ADM-006 | As an admin, I want to manage asset category templates so that owners create consistent listings | - Category editor<br>- Custom attribute field management<br>- Publish/archive categories |
| ADM-007 | As an admin, I want to manage rental agreement templates so that owners have standardised contracts | - Template editor<br>- Version control<br>- Publish/unpublish |

### Dispute Resolution

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ADM-008 | As an admin, I want to view and mediate disputes between owners and customers so that conflicts are resolved fairly | - Dispute list with context<br>- Messaging thread visible<br>- Binding resolution recorded |
| ADM-009 | As an admin, I want to override a payment or charge status in exceptional cases so that records are corrected | - Override action with justification<br>- Audit log entry<br>- Both parties notified |

### Platform Configuration

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| ADM-010 | As an admin, I want to configure platform commission rates so that owner payouts are correct | - Commission rate set (flat or percentage)<br>- Effective date configured<br>- Changes versioned |
| ADM-011 | As an admin, I want to configure notification templates so that communications are consistent | - Template editor per event type<br>- Preview function<br>- Save and publish |
| ADM-012 | As an admin, I want to manage admin roles and permissions so that access is controlled | - Role creation<br>- Permission matrix<br>- Assign to admin users |
