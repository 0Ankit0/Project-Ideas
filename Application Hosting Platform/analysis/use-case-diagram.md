# Use Case Diagram and Actor Analysis

## Actors

### Primary Actors
1. **Developer** (Indie or Startup)
   - External actor who develops applications
   - Interacts through web UI and CLI
   - Goals: Deploy code quickly, monitor application health

2. **Application Owner / Team Lead**
   - Manages team access, billing, and resource quotas
   - Interacts through web UI
   - Goals: Control team access, manage costs, ensure compliance

3. **Operations Engineer**
   - Monitors application health, troubleshoots issues
   - Interacts through dashboard and alerting systems
   - Goals: Maintain uptime, respond to incidents

4. **DevOps / Platform Engineer**
   - Manages AHP infrastructure, integrations, custom configurations
   - Interacts through admin UI and infrastructure tools
   - Goals: Scale platform, integrate with external services

### Secondary Actors
5. **GitHub/GitLab**
   - Version control system, provides webhooks and repository information
   - Automated interaction via API

6. **Cloud Infrastructure Provider** (AWS, GCP, Azure)
   - Provides compute, storage, networking
   - Automated interaction

7. **Add-on Provider** (Managed Postgres, Redis, S3, Sendgrid, etc.)
   - Provides managed services
   - Automated interaction

8. **DNS Provider**
   - Manages DNS records
   - Automated interaction

9. **SSL Certificate Authority** (Let's Encrypt)
   - Issues and renews SSL certificates
   - Automated interaction

10. **Billing System** (Stripe, payment processor)
    - Processes payments
    - Automated interaction

## Use Cases (Swimlane Diagram Format)

```mermaid
graph TB
    Developer["Developer"]
    Owner["Team Owner"]
    OpsEng["Operations Engineer"]
    GitHub["GitHub/GitLab"]
    Cloud["Cloud Provider"]
    AddOns["Add-on Provider"]
    DNS["DNS Provider"]
    SSL["SSL Authority"]
    Billing["Billing System"]
    
    Developer -->|Deploy| UC1["UC1: Deploy Application"]
    Developer -->|Manage Env| UC2["UC2: Configure Environment Variables"]
    Developer -->|Scale| UC3["UC3: Scale Application"]
    Developer -->|Add Domain| UC4["UC4: Add Custom Domain"]
    
    Owner -->|Manage Access| UC5["UC5: Manage Team Access"]
    Owner -->|View Billing| UC6["UC6: View Billing & Usage"]
    Owner -->|Manage Add-ons| UC7["UC7: Provision Add-on"]
    
    OpsEng -->|Monitor| UC8["UC8: View Logs & Metrics"]
    OpsEng -->|Alert| UC9["UC9: Configure Alert Rules"]
    OpsEng -->|Debug| UC10["UC10: Troubleshoot Issues"]
    
    UC1 -->|Webhook| GitHub
    UC1 -->|Deploy| Cloud
    UC1 -->|SSL| SSL
    
    UC4 -->|Verify| DNS
    UC4 -->|Cert| SSL
    
    UC7 -->|Provision| AddOns
    
    UC6 -->|Process| Billing
```

## Detailed Use Cases

### UC1: Deploy Application from Git Repository

**Primary Actor**: Developer  
**Secondary Actors**: GitHub/GitLab, Cloud Infrastructure, SSL Authority  
**Precondition**: Developer has created an application in AHP, authorized GitHub access  
**Trigger**: Developer pushes code to main branch OR clicks "Deploy" in UI  

**Basic Flow**:
1. Developer pushes code to main branch (or triggers manual deployment)
2. GitHub sends webhook to AHP with repository details
3. AHP clones repository and analyzes codebase
4. AHP detects language/framework and selects buildpack
5. AHP builds application (npm install, go build, etc.)
6. AHP generates container image and pushes to registry
7. AHP deploys container to cloud infrastructure
8. AHP health-checks the new instance
9. AHP routes traffic to new instance (if healthy)
10. Developer receives notification of successful deployment
11. Application is accessible via custom domain or AHP-generated domain

**Alternative Flow (Build Fails)**:
- At step 5, if build fails (missing dependency, syntax error)
- AHP captures error logs and notifies developer
- Previous version continues serving traffic
- Developer fixes code and redeploys

**Alternative Flow (Health Check Fails)**:
- At step 8, if health check fails
- AHP stops deployment, keeps previous version running
- Notifies developer with error details
- Previous version continues serving traffic

**Postcondition**: New version deployed and serving traffic OR previous version still running, developer notified

---

### UC2: Configure Application Scaling

**Primary Actor**: Developer / Operations Engineer  
**Secondary Actors**: Cloud Infrastructure  
**Precondition**: Application is deployed  
**Trigger**: Developer/Ops wants to handle more traffic or optimize costs  

**Basic Flow (Manual Scaling)**:
1. User navigates to application scaling settings
2. User sets desired instance count (e.g., 1 → 5)
3. AHP validates request (within quota limits)
4. AHP provisions new instances
5. AHP registers instances with load balancer
6. AHP performs health checks on new instances
7. AHP routes traffic to all healthy instances
8. User receives confirmation of scale operation
9. Scaling event is recorded in history

**Alternative Flow (Auto-Scaling)**:
1. User enables auto-scaling with rules (CPU > 70% → scale up 2 instances)
2. AHP continuously collects CPU metrics from instances
3. When rule condition is met for specified duration, AHP auto-scales
4. Scaling follows same flow as manual scaling
5. User receives notification of auto-scale event

**Postcondition**: Application now running on desired number of instances, traffic load-balanced

---

### UC3: Add Custom Domain and SSL

**Primary Actor**: Developer / Team Owner  
**Secondary Actors**: DNS Provider, SSL Authority (Let's Encrypt), Cloud Infrastructure  
**Precondition**: Application is deployed  
**Trigger**: User wants to use custom domain (myapp.com) instead of AHP-generated domain  

**Basic Flow**:
1. User navigates to application domains
2. User clicks "Add Custom Domain"
3. User enters domain name (e.g., myapp.com)
4. AHP generates CNAME target (e.g., myapp.ahp.io)
5. User is instructed to update DNS: CNAME myapp.com → myapp.ahp.io
6. User confirms DNS update is complete (or AHP polls DNS)
7. AHP verifies DNS propagation by querying DNS provider
8. Once verified, AHP requests SSL certificate from Let's Encrypt
9. Let's Encrypt issues certificate via ACME protocol
10. AHP installs certificate on load balancer
11. User receives notification: domain is ready
12. HTTPS traffic on custom domain is now served
13. AHP schedules automatic renewal 30 days before expiration

**Alternative Flow (Wildcard Domain)**:
- User can request wildcard certificate (*.myapp.com)
- Requires DNS CNAME verification instead of ACME challenge
- Covers all subdomains

**Postcondition**: Custom domain resolves to application, HTTPS enabled, certificate auto-renews

---

### UC4: Provision Managed Add-on (Database)

**Primary Actor**: Developer / Team Owner  
**Secondary Actors**: Add-on Provider, Cloud Infrastructure  
**Precondition**: Application is deployed  
**Trigger**: Developer wants PostgreSQL database for application  

**Basic Flow**:
1. User navigates to application add-ons
2. User clicks "Browse Add-ons" and selects PostgreSQL
3. User configures: name (mydb), size (1GB), region (same as app)
4. User clicks "Provision"
5. AHP validates add-on compatibility and quota limits
6. AHP requests add-on provision from provider (e.g., AWS RDS)
7. Add-on provider allocates and configures instance
8. Add-on provider provides connection credentials
9. AHP generates connection string (psql://user:pass@host:5432/db)
10. AHP injects connection string as DATABASE_URL environment variable
11. AHP redeploys application with new environment variable
12. Application connects to database and performs migrations (if configured)
13. User receives notification: add-on ready
14. AHP sets up automated backups and monitoring

**Postcondition**: Add-on provisioned, connection credentials available as environment variable, application redeployed

---

### UC5: Manage Team Access Control

**Primary Actor**: Team Owner  
**Secondary Actors**: None (internal system)  
**Precondition**: Team created, user is team owner  
**Trigger**: Owner wants to invite team member or change role  

**Basic Flow (Invite Member)**:
1. Owner navigates to Team Settings → Members
2. Owner clicks "Invite Member"
3. Owner enters team member email (dev@acme.com) and selects role (Developer)
4. AHP validates email format
5. AHP sends invitation email with join link
6. Team member clicks link and is presented with sign-up or login
7. Team member accepts invitation
8. Team member is added to team with specified role
9. Team member now has access to team applications per role permissions

**Basic Flow (Change Role)**:
1. Owner navigates to team members list
2. Owner finds member and clicks "Edit Role"
3. Owner changes role from Developer to Admin
4. Role is updated immediately
5. Member receives notification of role change
6. Member now has admin permissions

**Basic Flow (Remove Member)**:
1. Owner finds member in list
2. Owner clicks "Remove"
3. AHP shows confirmation: "Remove member from team?"
4. Owner confirms
5. Member is removed from team
6. Member loses access to all team resources
7. Member receives notification of removal

**Postcondition**: Team access control updated, member has appropriate permissions

---

### UC6: Configure Monitoring and Alerts

**Primary Actor**: Operations Engineer / Developer  
**Secondary Actors**: Notification System (email, Slack, webhook)  
**Precondition**: Application is deployed  
**Trigger**: Engineer wants to be alerted of high error rates  

**Basic Flow**:
1. Engineer navigates to application alerts
2. Engineer clicks "Create Alert Rule"
3. Engineer configures: condition (error_rate > 5%), duration (for 5 minutes)
4. Engineer selects notification channel (email, Slack webhook)
5. Engineer provides Slack channel (#alerts-acme)
6. AHP validates configuration
7. Alert rule is saved and enabled
8. AHP begins evaluating rule based on incoming metrics
9. When error_rate exceeds 5% for 5 consecutive minutes, alert fires
10. AHP sends notification to #alerts-acme with context (current rate, graph link, affected instances)
11. Engineer acknowledges alert in Slack or AHP UI
12. When error_rate drops below 5%, alert clears and another notification is sent

**Postcondition**: Alert rule active, engineer notified of threshold violations

---

## Use Case Priority Matrix

| Use Case | Frequency | Importance | MVP |
|----------|-----------|-----------|-----|
| UC1: Deploy | Daily | Critical | Yes |
| UC2: Scale | Weekly | High | Yes |
| UC3: Custom Domain | Once per app | High | Yes |
| UC4: Add-on | Weekly | High | Yes |
| UC5: Team Access | Monthly | Medium | Yes |
| UC6: Monitoring | Daily | High | Yes |
| UC7: Preview Deployments | Per PR | Medium | No (Phase 2) |
| UC8: Auto-Scaling | Ongoing | High | No (Phase 2) |
| UC9: Blue-Green Deploy | Per release | Medium | No (Phase 3) |
| UC10: Multi-Region | Rare | Medium | No (Phase 4) |

---

**Document Version**: 1.0
**Last Updated**: 2024
