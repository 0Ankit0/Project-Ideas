# Use Case Descriptions

## UC-01 Reserve Resource
- **Actors:** Consumer, Booking Service
- **Preconditions:** Resource exists; policy allows reservation.
- **Main Flow:** search availability -> place hold -> confirm reservation.
- **Alternates:** hold expires; conflict on allocation; payment authorization fails.
- **Postconditions:** reservation in `CONFIRMED` or terminal failure reason recorded.

## UC-02 Fulfill and Return
- **Actors:** Fulfillment Agent, Operations Service
- **Preconditions:** reservation confirmed and within fulfillment window.
- **Main Flow:** check-out -> in-use -> check-in -> inspection.
- **Alternates:** partial return; incident reported; offline event sync conflict.
- **Postconditions:** fulfillment closed and settlement inputs captured.

## UC-03 Settle Account
- **Actors:** Settlement Service, Finance Analyst
- **Preconditions:** usage/inspection events finalized.
- **Main Flow:** compute charges -> apply adjustments -> post ledger entries -> close.
- **Alternates:** dispute opened; gateway mismatch; manual review required.
- **Postconditions:** settlement posted with reconciliation status.
