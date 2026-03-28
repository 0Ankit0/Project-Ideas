# System Context Diagram

This diagram shows the CRM system boundary, primary users, and external systems.

```mermaid
flowchart LR
    subgraph Actors[Internal Actors]
      Rep[Sales Rep]
      Mgr[Sales Manager]
      Ops[Revenue Operations]
      Admin[CRM Admin]
    end

    CRM[Customer Relationship Management Platform]

    subgraph External[External Systems]
      MAP[Marketing Automation]
      Mail[Email Provider]
      Cal[Calendar Provider]
      ERP[ERP / Billing]
      SSO[Identity Provider]
      BI[BI & Data Warehouse]
    end

    Rep --> CRM
    Mgr --> CRM
    Ops --> CRM
    Admin --> CRM

    MAP --> CRM
    CRM --> MAP
    CRM --> Mail
    CRM --> Cal
    CRM --> ERP
    CRM --> BI
    SSO --> CRM
```

## Notes
- CRM is the source of truth for lead, account, contact, and opportunity lifecycle state.
- Identity and access are delegated to enterprise SSO/IdP.
- Downstream analytics consume event/data exports from CRM.
