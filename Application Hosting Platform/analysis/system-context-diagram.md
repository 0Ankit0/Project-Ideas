# System Context Diagram

The System Context diagram shows how the Application Hosting Platform (AHP) interacts with external actors and systems from a high level. This diagram establishes boundaries and integrations.

## High-Level System Context

```mermaid
graph TB
    Developer["👨‍💻 Developer"]
    Owner["👤 Team Owner"]
    OpsEng["⚙️ Operations Engineer"]
    
    AHP["Application Hosting Platform<br/>(AHP)"]
    
    GitHub["🐙 GitHub/GitLab<br/>Version Control"]
    Cloud["☁️ Cloud Provider<br/>(AWS/GCP/Azure)"]
    DNS["🌐 DNS Provider"]
    SSL["🔒 Let's Encrypt<br/>SSL Authority"]
    
    AddOns["📦 Add-on Providers<br/>(AWS RDS, Redis Cloud,<br/>SendGrid, Stripe)"]
    
    Email["📧 Email Service<br/>(for notifications)"]
    Slack["💬 Slack"]
    Payment["💳 Payment Processor<br/>(Stripe)"]
    
    Developer -->|Deploy, Scale, Manage| AHP
    Owner -->|Billing, Team Access| AHP
    OpsEng -->|Monitor, Alert| AHP
    
    AHP -->|Push/Pull Code<br/>Webhooks| GitHub
    AHP -->|Provision Compute<br/>Storage, Load Balancer| Cloud
    AHP -->|Verify DNS<br/>Manage Records| DNS
    AHP -->|Request Certificates<br/>Renewal| SSL
    
    AHP -->|Provision Services<br/>Get Credentials| AddOns
    AHP -->|Send Notifications<br/>Alerts| Email
    AHP -->|Send Notifications<br/>Post Messages| Slack
    AHP -->|Process Payments<br/>Billing| Payment
    
    Cloud -->|Collect Metrics<br/>Logs| AHP
    
    style AHP fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style Developer fill:#50C878,stroke:#2D7A4A,color:#fff
    style Owner fill:#FFB81C,stroke:#9A6E1A,color:#000
    style OpsEng fill:#FF6B6B,stroke:#9A2E2E,color:#fff
    style GitHub fill:#333,stroke:#000,color:#fff
    style Cloud fill:#FF9900,stroke:#9A5A00,color:#fff
    style DNS fill:#1E90FF,stroke:#0A4A8C,color:#fff
    style SSL fill:#27AE60,stroke:#155D2D,color:#fff
    style AddOns fill:#9B59B6,stroke:#5D2E7D,color:#fff
    style Email fill:#E74C3C,stroke:#8B251C,color:#fff
    style Slack fill:#36C5F0,stroke:#1F6F8F,color:#fff
    style Payment fill:#F39C12,stroke:#934F0A,color:#fff
```

## External System Integrations

### Version Control: GitHub & GitLab
- **Direction**: Bidirectional
- **Connection**: HTTPS webhooks + REST API
- **Purpose**: 
  - AHP receives webhook on push/PR
  - AHP clones repo for building
  - AHP posts deployment status on PR/commit
- **Failure Handling**: If GitHub is down, pending deployments queue and retry
- **Credentials**: OAuth token (scoped to repos only)

### Cloud Infrastructure Provider
- **Vendors**: AWS, Google Cloud, Azure
- **Direction**: Bidirectional
- **Connection**: Cloud provider APIs + direct resource access
- **Purpose**:
  - AHP provisions EC2/Compute instances for applications
  - AHP provisions managed services (RDS for databases, S3 for storage)
  - AHP configures load balancers, auto-scaling groups
  - AHP collects metrics via CloudWatch/Stackdriver
- **Failure Handling**: If cloud provider is down, running apps continue; new deployments queue
- **Credentials**: IAM role (AHP's deployment service)

### DNS Provider
- **Support**: Route 53 (AWS), Cloud DNS (GCP), Azure DNS, Cloudflare, etc.
- **Direction**: Bidirectional
- **Connection**: DNS API + DNS lookups
- **Purpose**:
  - AHP verifies DNS CNAME records (domain validation)
  - AHP may auto-manage DNS records (premium feature)
- **Failure Handling**: If DNS verification fails, domain activation is delayed

### SSL Certificate Authority: Let's Encrypt
- **Direction**: Bidirectional (ACME protocol)
- **Connection**: HTTPS API
- **Purpose**:
  - AHP requests certificates for custom domains
  - AHP handles automatic renewal 30 days before expiration
  - AHP verifies domain ownership via DNS-01 challenge
- **Failure Handling**: If LE is down, certificate renewal retries hourly; alerts sent if renewal fails

### Add-on Providers
- **Vendors**: AWS RDS (Postgres, MySQL), Redis Cloud, MongoDB Atlas, SendGrid, Stripe, AWS S3
- **Direction**: Bidirectional
- **Connection**: Provider's REST API
- **Purpose**:
  - AHP provisions managed services (databases, caches, email, payment processing)
  - AHP obtains connection credentials
  - AHP collects metrics and backups
- **Credentials**: Provider API keys (scoped per customer)

### Email Notification Service
- **Purpose**: Send deployment notifications, alerts, billing emails
- **Vendor**: AWS SES, SendGrid, or internal SMTP
- **Direction**: Unidirectional (AHP → email service)
- **Failure Handling**: If email service down, notifications are queued for retry

### Slack Integration
- **Purpose**: Real-time deployment, error, and alert notifications to Slack channels
- **Direction**: Unidirectional (AHP → Slack webhooks)
- **Connection**: Slack incoming webhooks + Slack API
- **Failure Handling**: If Slack unavailable, notification is logged as failed

### Payment Processor: Stripe
- **Purpose**: Process credit card payments for billing
- **Direction**: Bidirectional (AHP initiates charges, receives payment status)
- **Connection**: Stripe API
- **Credentials**: Stripe API key (restricted to charges and customers)
- **Failure Handling**: Failed payments retry with exponential backoff

## Data Flow Summary

### Inbound Data
- **Git Webhooks**: New commits trigger deployments (repo owner → GitHub → AHP)
- **Cloud Metrics**: CPU, memory, network metrics streamed from cloud provider
- **Health Checks**: Application health status from running containers
- **User Interactions**: API requests from web UI and CLI

### Outbound Data
- **Build Commands**: AHP instructs cloud provider to execute build steps
- **Deployment Artifacts**: Container images pushed to registry
- **Configuration**: AHP writes environment variables and configuration to deployed apps
- **Notifications**: Emails, Slack messages, webhooks to users
- **Billing Events**: Usage records sent to billing system

## Security Considerations

### Authentication
- Developer ↔ AHP: OAuth/JWT tokens
- AHP ↔ GitHub: OAuth tokens (repo access only)
- AHP ↔ Cloud Provider: IAM service account (least privilege)
- AHP ↔ Add-on Providers: API keys (scoped per service)

### Encryption
- All external communication over TLS 1.2+
- Credentials stored encrypted in database
- Secrets injected at runtime, never logged
- Add-on credentials rotated automatically every 90 days

### Isolation
- Applications in isolated containers with network policies
- Multi-tenant databases with row-level security
- Team-level resource quotas prevent resource hogging

---

**Document Version**: 1.0
**Last Updated**: 2024
