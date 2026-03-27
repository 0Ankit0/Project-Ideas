# System Sequence Diagrams

## Sequence A: Reserve and Confirm
Client -> API Gateway -> Reservation Service -> Policy Engine -> Reservation Service -> Event Bus -> Notification Service.

## Sequence B: Fulfill and Return
Operations App -> Fulfillment Service -> Event Bus -> Settlement Service -> Incident Service (conditional).

## Sequence C: Finalize Settlement
Finance Console -> Settlement Service -> Payment Adapter -> ERP Adapter -> Event Bus -> Audit Store.
