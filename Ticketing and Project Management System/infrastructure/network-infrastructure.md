# Network Infrastructure - Ticketing and Project Management System

## Network Zones

| Zone | Purpose | Key Controls |
|------|---------|--------------|
| Public Edge | Client portal entry, CDN, WAF | TLS termination, bot protection, rate limits |
| Internal Access | Employee workspace and admin access | SSO, VPN or zero-trust policies |
| Application Zone | API and worker services | Service-to-service auth, private subnets |
| Data Zone | Database, search, queue, object storage | No direct public access, KMS encryption |
| Integration Zone | Email, chat, SCM, malware scan | Outbound allow-list, secrets rotation |

## Traffic Principles
- Client traffic enters only through the public edge.
- Internal users access the workspace through corporate network controls or zero-trust gateways.
- Data stores remain private and reachable only from approved application services.
- Attachment download URLs are time-limited and scoped to the requesting principal.
