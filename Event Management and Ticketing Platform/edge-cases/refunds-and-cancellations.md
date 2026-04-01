# Refunds and Cancellations Edge Cases

This document outlines critical edge cases in refund processing and cancellation handling for the Event Ticketing Platform.

---

## 1. Event Cancelled by Organiser — Mass Refund Processing

### Scenario
An organizer cancels an event (due to weather, safety, artist unavailability). The event had 5,000 tickets sold generating $500K in revenue. The platform must refund all customers within Stripe's refund window (typically 90 days) and provide clear communication about the cancellation and refund status.

### Failure Mode
- Event cancellation triggered by organizer
- 5,000 refund requests queued simultaneously
- Stripe API rate limiting: 100 requests/second (would take 50 seconds minimum)
- Customers flood support inquiring about refunds
- Manual refund processing too slow, misses Stripe refund window

### Impact
- **Customers:** Uncertain about refund status, poor communication
- **Business:** Support cost, potential regulatory violation if refunds not processed
- **Compliance:** Stripe requires refunds within 90 days or transaction becomes unreturnable

### Detection
- Event cancellation triggered in system
- Batch refund process initiated
- Monitor refund success rate, track failed refunds

### Mitigation
- **Batch Processing:** Queue all refunds asynchronously (not sequentially)
  - Stripe allows 100 req/s, process in batches of 100
  - Process entire batch within 1 minute
- **Transparency:** Immediate communication to customers
  - Email: "Your event was cancelled. Refund initiated."
  - Include refund amount, timeline (5-10 business days)
  - Provide refund status tracking link
- **Monitoring:** Track refund processing
  - Alert if any refund fails
  - Retry failed refunds automatically
  - Manual review of failed refunds
- **Partial Refunds:** Handle different scenarios
  - Full cancellation: 100% refund
  - Postponement: offer credit or full refund
  - Force majeure: offer credit or refund per cancellation policy

### Recovery Steps
1. Event cancellation initiated by organizer
2. System identifies all orders for event
3. Customer notifications sent immediately
4. Batch refund processing:
   - Query all orders: status = confirmed, payment_status = succeeded
   - For each order: create refund request in queue
   - Process refunds in parallel batches (100 req/s)
5. Tracking:
   - Track refund status per order
   - Alert on any failures
   - Retry failed refunds (exponential backoff)
6. Reconciliation:
   - Verify all refunds processed within 3 business days
   - Manual intervention for failed refunds
7. Customer communication:
   - Email: refund status updates (initiated, pending, completed)
   - Dashboard: refund status tracker

### Related Systems
- Order management
- Payment processing (Stripe)
- Email notification service
- Batch job scheduling
- Refund tracking system

---

## 2. Refund Requested After Transfer to Third Party

### Scenario
A customer purchased tickets for $100. The platform transferred funds to the event organizer immediately after payment (less transaction fees). 2 weeks later, the customer requests a refund (changed mind about attending). The original payment processor (Stripe) can still process the refund within 90 days, but the funds have already been transferred to the organizer. The platform must refund the customer from the organizer's balance or negotiate with the organizer.

### Failure Mode
- Customer requests refund 2 weeks post-purchase
- Funds already transferred to organizer
- Platform has limited options:
  1. Refund from platform account (cash outlay)
  2. Request organizer to refund
  3. Deny refund (poor customer service)

### Impact
- **Customers:** Unclear refund policy, frustration
- **Business:** Cash flow impact if refunding from platform
- **Organizers:** Unexpected request to return funds

### Detection
- Refund request submitted
- Check payment date vs. refund request date
- Verify if funds transferred to organizer

### Mitigation
- **Clear Refund Policy:** Communicated at purchase
  - Full refund if requested within 7 days
  - 50% refund if requested 7-14 days before event
  - No refund within 48 hours of event
- **Settlement Delay:** Hold funds for 72 hours before organizer transfer
  - Provides window for refunds
  - Requires liquidity management by platform
- **Escrow Account:** Keep funds in escrow until after event
  - More expensive (reduces organizer payout speed)
  - Eliminates refund conflicts
- **Insurance:** Purchase refund insurance policy
  - Covers refunds for covered reasons (illness, emergency)
  - Excludes change of mind

### Recovery Steps
1. Refund request submitted outside normal window
2. Check refund policy: applies to customer's scenario?
3. If policy allows:
   - Option A: Process refund from platform account (absorb cost)
   - Option B: Request organizer to fund refund
4. Communication:
   - Explain refund timeline
   - Confirm original payment method for refund
5. Process refund:
   - Create refund in Stripe
   - Issue refund to customer payment method
6. Settlement:
   - Adjust next payout to organizer (if organizer funded refund)
   - Document refund reason

### Related Systems
- Order management
- Refund policy engine
- Payment processing
- Payout/settlement system
- Organizer account management

---

## 3. Partial Refund for Multi-Ticket Order

### Scenario
A customer purchased 4 tickets for $400 ($100 each). 2 attendees will still attend, but 2 cannot make it. The customer requests a partial refund for 2 tickets ($200). The platform must handle splitting the order, issuing partial refund, and adjusting the ticket allocation.

### Failure Mode
- Multi-ticket order: 4 tickets, 1 payment
- Partial refund request: return 2 tickets
- System challenges:
  - Original payment is atomic (one transaction)
  - Partial refund creates two separate ticket allocations
  - Seats reserved under single order
  - Refund creates separate refund transaction

### Impact
- **Customers:** Cannot split order (all-or-nothing)
- **Business:** Lost revenue opportunity (customer might refund entire order instead)
- **Operational:** Manual intervention required

### Detection
- Refund request submitted with specific quantity
- Check order line items
- Verify refund eligibility

### Mitigation
- **Split Order at Checkout:** Allow customers to purchase separate orders
  - Buy 2 tickets in order A, 2 tickets in order B
  - Enables independent refund management
- **Order Modifications:** Allow customers to change quantity within window
  - Within 7 days: upgrade/downgrade quantity
  - System handles refund/charge
- **Ticket Transfers:** Instead of refund, allow transfer to another person
  - Original customer keeps tickets
  - Can transfer tickets to someone else
  - Other person can pick up or download
- **Partial Refund Processing:**
  - Create refund in Stripe for $200
  - Stripe processes partial refund to original payment method
  - Remove 2 seats from customer allocation
  - Update order status: original 4 tickets → 2 confirmed tickets

### Recovery Steps
1. Partial refund request submitted
2. Verify customer eligibility:
   - Within refund window
   - Requested quantity valid
3. Calculate refund amount:
   - 2 tickets × $100 = $200
   - Check for applied discounts
   - Subtract Stripe fee (if applicable)
4. Processing:
   - Create partial refund in Stripe
   - Update order: quantity from 4 to 2
   - Release 2 seats back to inventory
   - Generate new ticket for remaining 2 attendees
5. Communication:
   - Confirm refund amount and timeline
   - Send updated ticket PDF with remaining 2 seats
   - Explain transfer option for attendee changes

### Related Systems
- Order management
- Ticket allocation
- Payment processing
- Seat management
- Ticket generation

---

## 4. Payment Gateway Dispute (Chargeback) After Ticket Used

### Scenario
A customer attended an event (ticket was validated at check-in). 3 weeks later, the customer files a chargeback with their credit card company, claiming they didn't authorize the purchase. The platform has evidence the customer attended (check-in record), but the chargeback process gives the customer's bank the benefit of the doubt.

### Failure Mode
- Ticket validated at check-in (proof of use)
- Customer files chargeback anyway
- Credit card company refunds customer
- Platform loses both the payment and the ticket revenue
- Multiple scenarios possible:
  - Customer disputes as "unauthorized"
  - Customer claims "service not rendered"
  - Customer claims "didn't receive ticket"

### Impact
- **Financial:** Platform refunded by card company, loses revenue
- **Business:** Chargeback ratio affects Stripe processing agreement
- **Legal:** Limited recourse (chargeback favors consumer)

### Detection
- Stripe notifies of chargeback
- Customer check-in records show attendance
- Order status shows ticket used

### Mitigation
- **Clear Documentation:** Maintain proof of delivery and use
  - Email confirmation with QR code (sent immediately)
  - PDF download record (track download attempts)
  - Check-in record (time, venue, gate)
- **Chargeback Prevention:** Provide excellent UX
  - Clear cancellation/refund policy (reduce buyer's remorse)
  - Easy refund process within window
- **Chargeback Defense:** Contest fraudulent chargebacks
  - Present evidence to card company:
    - Email receipt
    - Check-in log with timestamp/location
    - Customer IP address
  - Response within 7 days (Stripe handles)
- **Fraud Monitoring:** Detect suspicious patterns
  - Multiple chargebacks from same customer
  - Multiple chargebacks using same card
  - Chargebacks from high-risk countries

### Recovery Steps
1. Chargeback filed by customer
2. Stripe notifies platform of chargeback
3. Evidence gathering:
   - Retrieve email receipt (with timestamp)
   - Retrieve check-in record (date, time, location, gate)
   - Retrieve customer IP from purchase
4. Chargeback response:
   - Prepare detailed response with evidence
   - Submit to Stripe within deadline
5. Outcome:
   - **Won:** Funds returned to platform
   - **Lost:** Funds debited, chargeback fee charged
6. Pattern monitoring:
   - If customer has multiple chargebacks: flag as high-risk
   - Block future purchases, require phone verification

### Related Systems
- Order management
- Payment processing (Stripe)
- Email delivery system
- Check-in service
- Fraud detection system

---

## 5. Refund Processing Delay Exceeding Stripe Refund Window

### Scenario
A customer requests a refund 80 days after purchase. The platform attempts to process the refund in Stripe, but the transaction is outside the 90-day refund window that Stripe enforces. The refund fails, and the platform must now offer alternative refund methods (ACH, check) or deny the refund.

### Failure Mode
- Refund request submitted 80+ days post-purchase
- Stripe refund API returns error: "Refund window exceeded"
- Original payment method unavailable for refund
- Customer cannot receive refund via original card
- Manual refund processing required

### Impact
- **Customers:** Cannot receive refund via credit card
- **Business:** Must find alternative payment method
- **Operational:** Manual refund handling

### Detection
- Refund request submitted
- Check payment date vs. request date
- Verify time difference >90 days

### Mitigation
- **Refund Policy with Timeline:** Clearly state refund window
  - "Refunds available within 90 days of purchase"
  - "After 90 days, refunds cannot be processed via card"
- **Late Refund Options:** For refunds outside normal window
  - Issue credit to customer account (can be used for future purchase)
  - Send ACH transfer to customer's bank account
  - Send check (slow, not ideal)
- **Communication:** Educate customers about window
  - Email receipt: include refund policy
  - Customer dashboard: show refund deadline
  - Support documentation: explain options

### Recovery Steps
1. Refund request submitted 80+ days post-purchase
2. Check refund eligibility:
   - Payment date: 80+ days ago
   - Refund window: 90 days
   - Options: credit account or ACH
3. Customer choice:
   - Option A: $100 credit to customer account (future ticket purchase)
   - Option B: ACH transfer to bank account (5-7 business days)
   - Option C: Check by mail (7-10 business days)
4. Processing:
   - If credit: add to account balance, email confirmation
   - If ACH: capture bank account, initiate transfer, send confirmation
   - If check: generate check, mail, send tracking
5. Follow-up:
   - Email confirmation with expected timeline
   - Update order status: refund_processed

### Related Systems
- Refund policy engine
- Order management
- Payment processing
- ACH/banking integration
- Customer account management

---

## 6. Resale Platform Arbitrage During Refund Window

### Scenario
A customer purchases 4 tickets for $100 each ($400 total). They immediately list the tickets for sale on a resale platform (like StubHub) at $150 each ($600 total). Before the resale payment clears, the customer requests a refund from the original platform, intending to profit from the arbitrage. If both transactions succeed, the customer nets $200 in profit.

### Failure Mode
- Customer exploits refund window + resale market
- Purchases tickets, immediately lists on resale
- Requests refund before resale payment settles
- Platform processes refund, customer keeps resale revenue
- Platform loses original sale, customer gains arbitrage profit

### Impact
- **Financial:** Platform loses ticket sale revenue
- **Fairness:** Customer exploits system unfairly
- **Organizer:** Loses revenue, loses audience (refund likely means unused ticket)

### Detection
- Monitor customers for patterns:
  - Same customer refunding orders frequently
  - Refund requests within 24 hours of purchase
  - Tickets listed on resale platforms coinciding with refund requests
- Cross-check with resale platforms (if possible)

### Mitigation
- **Refund Policy:** No refund if ticket transferred/listed
  - Require declaration at refund request: "Have you listed this ticket for resale?"
  - Violation results in chargeback/legal action
- **Smart Refund Window:** Shorter window reduces arbitrage
  - 24-48 hours instead of 7 days
  - Limits arbitrage opportunity
- **Fraud Detection:** Monitor for abuse
  - Customer has multiple refunds: flag as high-risk
  - Require escalated review for subsequent refunds
- **Resale Integration:** Partner with resale platforms
  - API integration to check if ticket listed
  - Block refund if ticket listed on resale site

### Recovery Steps
1. Refund request submitted
2. Check for abuse:
   - Customer refund history (repeated refunds)
   - Cross-check with resale platforms (if integrated)
   - Check time between purchase and refund request
3. If abuse detected:
   - Require manual review
   - Contact customer: ask about resale listing
   - Document conversation
4. If confirmed abuse:
   - Deny refund (cite policy)
   - Or: process refund but investigate further
5. If legitimate:
   - Process refund normally

### Related Systems
- Refund policy engine
- Order management
- Fraud detection system
- Resale platform integration (optional)
- Support/escalation system

---

## 7. Force Majeure Cancellation (Weather, Safety)

### Scenario
An outdoor event is scheduled. 1 week before, a severe weather forecast emerges. The organizer cancels the event citing force majeure (an unforeseeable circumstance beyond parties' control). The organizer's force majeure clause says they have no refund obligation. However, customers expect refunds. The platform must balance organizer protection with customer fairness.

### Failure Mode
- Event cancelled due to force majeure
- Organizer claims no refund obligation
- Customers demand refunds (paid for cancelled event)
- Platform caught between organizer and customers
- Legal dispute likely

### Impact
- **Customers:** Cannot get refund, out of pocket
- **Organizer:** Avoids refund liability
- **Platform:** Loses customer trust, faces complaints/legal claims
- **Reputation:** Negative reviews, social media backlash

### Detection
- Event cancellation triggered
- Check cancellation reason (force majeure)
- Review organizer's contract terms
- Monitor customer complaints

### Mitigation
- **Clear Contract:** Define force majeure refund policy
  - Option 1: Organizer offers rescheduled date or credit
  - Option 2: Full refund to customers (organizer absorbs)
  - Option 3: Partial refund (shared cost)
- **Insurance:** Recommend event cancellation insurance
  - Covers force majeure scenarios
  - Enables refunds without organizer loss
- **Public Policy:** Override contract terms
  - Force majeure without organizer insurance → full customer refund
  - Platform covers cost (negotiated with organizer)
- **Communication:** Be transparent
  - Explain refund policy to customers
  - Offer alternatives (rescheduled date, credit)
- **No-Show Policy:** Distinguish from cancellation
  - Cancellation: force majeure, organizer discretion
  - No-show: event happens but organizer doesn't perform (customer entitled to refund)

### Recovery Steps
1. Event cancelled due to force majeure
2. Determine refund policy:
   - Check organizer contract
   - Check event cancellation insurance
   - Apply platform policy
3. Decision:
   - Option A: Full refund to customers
   - Option B: Rescheduled date offered
   - Option C: Credit for future purchase
4. Communication:
   - Email to all customers explaining decision and timeline
   - Clear explanation of reason for cancellation
   - Refund/alternative options
5. Processing:
   - If refund: process batch refunds (all orders)
   - If rescheduled: send new event details, update orders
   - If credit: add to customer account
6. Organizer settlement:
   - Deduct refund cost from organizer payout
   - Or: negotiate refund contribution
   - Document decision and rationale

### Related Systems
- Event management
- Refund processing
- Customer communication
- Contract management
- Organizer settlement

---

## Summary

Refund and cancellation edge cases require clear policies, transparent communication, and flexibility to handle unexpected scenarios. The goal is to balance fairness to customers, protection for organizers, and sustainability for the platform.
