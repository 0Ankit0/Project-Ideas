# Network Infrastructure - Library Management System

## Network Zones

| Zone | Purpose | Key Controls |
|------|---------|--------------|
| Public Edge | Patron discovery and account access | TLS, WAF, rate limiting |
| Staff Access | Branch or internal operations access | SSO, private network or zero-trust gateway |
| Application Zone | API and worker services | Private subnets, service auth, secrets management |
| Data Zone | Database, search, queue, object storage | No direct public access, encrypted storage |
| Integration Zone | Vendors, notifications, payment, digital providers | Outbound allow-list, credential rotation |

## Traffic Principles
- Patron traffic enters only through the public edge.
- Staff access should traverse managed internal access controls.
- Search and reporting reads should not bypass application-level authorization for protected account data.
- Integrations should use rotated secrets and explicit retry/failure monitoring.
