# System Context Diagram

## External Systems
- Identity Provider (authentication and authorization context)
- Payment Gateway (authorization, capture, refunds)
- Notification Providers (email, SMS, push)
- ERP/Accounting Platform (journal export and close)
- BI/Warehouse (analytics and forecasting)
- Compliance Archive (immutable retention policies)

## Context Boundary
The platform owns lifecycle orchestration and domain state;
external systems are integrated through adapter interfaces and event contracts.
