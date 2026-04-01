# Use Case Detailed Descriptions

## UC1: Deploy Application from Git Repository

### Overview
This is the core use case that enables developers to deploy their applications without interacting with cloud infrastructure directly. The developer pushes code to their Git repository, and AHP automatically builds, tests, and deploys the application.

### Stakeholders
- **Primary**: Developer (indie or team member)
- **Secondary**: DevOps engineer, Application owner (for monitoring)

### Preconditions
- Developer has created an AHP account
- Developer has created an application in AHP
- GitHub/GitLab account is connected to AHP with appropriate permissions
- Application repository exists and contains application code

### Main Success Scenario

1. **Trigger Event**: Developer pushes code to main branch (auto-deploy) or manually triggers deployment via UI
   
2. **Repository Analysis**: AHP receives webhook or API request
   - Clones repository at specific commit/branch
   - Analyzes project structure and files
   - Detects language (Node.js, Python, Go, Ruby, Java, PHP, static)
   - Determines framework and required buildpack

3. **Build Phase** (typically 30-120 seconds)
   - Selects appropriate buildpack (Node.js, Python, etc.)
   - Creates build container with necessary tools
   - Executes build commands: `npm install`, `go build`, `pip install`, etc.
   - Runs tests if Procfile or build config specifies test command
   - Generates final application image/artifact

4. **Registry Push**: Built image is pushed to AHP's container registry
   - Image is tagged with deployment ID and timestamp
   - Previous image is retained for rollback
   - Image scanning occurs (vulnerability check)

5. **Deployment**: New image is deployed to cloud infrastructure
   - New container is created and started
   - Environment variables are injected
   - Application connects to add-ons (databases, caches, etc.)

6. **Health Checking**: AHP verifies application is healthy
   - HTTP GET on /health endpoint (configurable)
   - Timeout: 30 seconds, retries: 3
   - If health check passes, deployment succeeds
   - If health check fails, previous version continues serving traffic, new version is stopped

7. **Traffic Routing**: Load balancer routes traffic to new instance
   - Existing connections are gracefully drained from old instance
   - New requests go to new instance
   - Previous instance is stopped

8. **Notification**: Developer is notified of deployment status
   - Success: "Deployed commit abc123 to production"
   - Failure: "Deployment failed: health check timeout. See logs: [link]"

### Postconditions
- New version serving 100% of traffic (on success)
- Previous version still available for immediate rollback
- Deployment history updated
- Build logs retained for 7 days

### Alternative Flows

**A1: Build Fails**
- At step 3, build process returns error (e.g., npm install fails due to missing package)
- Build logs captured with full error message and context
- Deployment aborted, previous version continues serving traffic
- Developer notified with: error message, failing command, build log link
- Developer fixes issue in code and redeploys

**A2: Health Check Fails**
- At step 6, container starts but health endpoint returns non-200 status
- After 3 retries (90 seconds total), health check considered failed
- New container is stopped, previous version continues serving traffic
- Developer notified with: health check error, container logs, suggested debugging steps
- Developer can view container logs to diagnose issue

**A3: Image Push Fails**
- At step 4, pushing image to registry fails (registry unreachable, quota exceeded)
- Deployment aborted, previous version continues serving traffic
- Developer notified with: error message, status page link
- AHP infrastructure team is alerted to investigate registry issue
- Deployment can be retried manually once issue is resolved

**A4: Manual Deployment from Specific Commit**
- Instead of webhooks, developer manually triggers via UI
- Developer selects: repository, branch, or specific commit hash
- Deployment proceeds as per main scenario with selected commit

### Business Rules
- Only authenticated users with "Developer" role or higher can deploy
- Deployments are queued if multiple happen simultaneously (FIFO)
- Build timeout: 10 minutes; exceeding this fails the deployment
- Previous 10 deployments are retained in history for rollback capability
- Health check timeout: 30 seconds before considering deployment failed

### Data Requirements
- Deployment record: application ID, commit hash, timestamp, status, duration, deployer user ID
- Build logs: full container output (retained 7 days)
- Image reference: registry path, tag, image ID for rollback

### Performance Requirements
- Time from git push to health check: < 2 minutes (95th percentile)
- Build logs streamed to UI in real-time (< 1 second latency)
- Health check response time: < 5 seconds
- Rollback to previous version: < 30 seconds

---

## UC2: Configure Auto-Scaling Rules

### Overview
Auto-scaling allows applications to automatically increase capacity during traffic spikes and reduce capacity during low-traffic periods, optimizing cost and performance.

### Stakeholders
- **Primary**: Operations engineer, Application owner
- **Secondary**: Developer (for monitoring), Finance team (cost implications)

### Preconditions
- Application is deployed with multiple instances (minimum 2)
- Metrics (CPU, memory) are being collected and available
- User has Admin role or higher

### Main Success Scenario

1. **Configure Scaling Rules**: User navigates to Scaling settings
   
2. **Define Scale-Up Rule**:
   - Metric: CPU usage
   - Threshold: > 70%
   - Duration: for 2 consecutive minutes
   - Action: add 2 instances
   - Max instances: 10 (quota limit)

3. **Define Scale-Down Rule**:
   - Metric: CPU usage
   - Threshold: < 30%
   - Duration: for 5 consecutive minutes
   - Action: remove 1 instance
   - Min instances: 2 (maintain redundancy)

4. **Cooldown Period**: Set cooldown = 5 minutes
   - After scaling action, wait 5 minutes before next scaling decision
   - Prevents rapid scaling oscillations

5. **Validation**: AHP validates configuration
   - Max instances ≤ team quota
   - Min instances ≥ 1
   - Scale-up and scale-down thresholds don't conflict
   - Duration values are reasonable (1-60 minutes)

6. **Enable Rules**: User clicks "Save and Enable"
   - Rules are saved in database
   - Rules become active immediately
   - Metrics evaluation begins

7. **Continuous Evaluation**: AHP evaluates rules every minute
   - Collects CPU metrics from all instances
   - Calculates average across instances
   - If average CPU > 70% for 2 minutes → trigger scale-up
   - If average CPU < 30% for 5 minutes → trigger scale-down

8. **Scale-Up Execution** (when triggered):
   - Provision 2 new instances
   - Deploy same image to new instances
   - Inject same environment variables
   - Wait for health checks to pass (< 1 minute)
   - Register with load balancer
   - Start routing traffic to new instances
   - Notification sent: "Auto-scaled from 3 to 5 instances (CPU > 70%)"

9. **Cooldown**: AHP waits 5 minutes before evaluating scale-down
   - During cooldown, scale-up rules can still trigger
   - Scale-down rules are suppressed

10. **Scale-Down Execution** (when triggered):
    - Remove 1 instance (gracefully drain connections)
    - Wait for in-flight requests to complete (< 30 seconds timeout)
    - Stop instance
    - Deregister from load balancer
    - Notification sent: "Auto-scaled down from 5 to 4 instances (CPU < 30%)"

### Postconditions
- Auto-scaling rules active and continuously evaluated
- Scaling history updated with each scale action
- Metrics graph shows correlation between scaling events and traffic

### Alternative Flows

**A1: Multiple Rules Trigger Simultaneously**
- If both scale-up and scale-down conditions are true (e.g., traffic has high variance)
- Scale-up takes precedence
- After scale-up completes, scale-down is reconsidered after cooldown

**A2: Resource Quota Exceeded**
- During scale-up, if max instances quota is reached
- Scaling stops at quota limit (e.g., stops at 10 instances if quota is 10)
- Alert sent to owner: "Auto-scaling capped at quota limit"

**A3: Scaling Fails**
- If new instances fail to start (e.g., image registry unreachable)
- Scaling operation is aborted
- Alert sent: "Auto-scaling failed: unable to provision instances"
- Previous instance count maintained

**A4: Disable Auto-Scaling**
- User can disable rules anytime
- Rules no longer evaluated
- Current instance count maintained
- Rules can be re-enabled later

### Business Rules
- Auto-scaling requires minimum 2 instances (redundancy)
- Scaling operations are atomic (all-or-nothing)
- Cooldown period prevents rapid oscillations
- Scale-down does not reduce below minimum instances
- Scale-up does not increase beyond quota limit

### Data Requirements
- Scaling rule: application ID, metric type, threshold, duration, action (add/remove N), min/max instances, cooldown
- Scaling event: timestamp, action (up/down), old count, new count, reason (rule name)

### Performance Requirements
- Metric collection: every 10 seconds per instance
- Rule evaluation: every 60 seconds
- Scale-up time: < 2 minutes from trigger to instances serving traffic
- Scale-down time: < 1 minute from trigger to graceful shutdown

---

## UC3: Add Custom Domain and Provision SSL

### Overview
Custom domains allow applications to be accessible via user-owned domain names instead of AHP-generated domains. Automatic SSL provisioning via Let's Encrypt provides HTTPS security.

### Stakeholders
- **Primary**: Application owner, Developer
- **Secondary**: DevOps (DNS configuration)

### Preconditions
- Application is deployed
- User owns the domain or has DNS management access
- Domain's registrar supports CNAME records

### Main Success Scenario

1. **User Initiates Domain Addition**: User navigates to application domains, clicks "Add Domain"

2. **Domain Entry**: User enters domain (e.g., myapp.com)
   - AHP validates format
   - AHP checks if domain is already in use by another team

3. **CNAME Target Generated**: AHP generates CNAME target
   - Target: myapp.ahp.io (platform-managed DNS)
   - User is instructed: "Create CNAME record: myapp.com → myapp.ahp.io"

4. **User Updates DNS**: User logs into domain registrar
   - Creates CNAME record pointing to AHP's load balancer
   - Propagation takes 5-48 hours globally

5. **AHP Verifies DNS**: User confirms DNS update in AHP UI
   - AHP queries DNS servers for CNAME record
   - Verifies CNAME points to correct target
   - Once verified, AHP proceeds with SSL provisioning

6. **SSL Certificate Request**: AHP requests certificate from Let's Encrypt
   - Uses ACME protocol with DNS-01 challenge
   - AHP adds TXT record to domain (automatic via DNS API or manual)
   - Let's Encrypt verifies domain ownership via TXT record

7. **Certificate Issuance**: Let's Encrypt issues 90-day SSL certificate
   - Certificate covers myapp.com (and www.myapp.com if configured)
   - AHP receives certificate and private key

8. **Certificate Installation**: AHP installs certificate on load balancer
   - TLS configuration updated
   - HTTPS traffic on myapp.com now served via new certificate

9. **Verification & Notification**: AHP verifies HTTPS is working
   - Tests HTTPS connection to myapp.com
   - Confirms certificate is valid
   - User receives notification: "Domain myapp.com is active and HTTPS-enabled"

10. **Auto-Renewal Configuration**: AHP schedules automatic renewal
    - Certificate renews 30 days before expiration
    - Automatic process, no user action required
    - User receives renewal confirmation email

### Postconditions
- Custom domain resolves to application
- HTTPS enabled with valid certificate
- Certificate auto-renews every 90 days
- Domain can be used immediately for production traffic

### Alternative Flows

**A1: Wildcard Domain (*.myapp.com)**
- User requests wildcard certificate during domain setup
- Certificate covers all subdomains (api.myapp.com, admin.myapp.com, etc.)
- Same SSL provisioning flow but certificate is issued for *.myapp.com

**A2: Multiple Domains Same App**
- User can add multiple domains to single application
- Each gets its own SSL certificate
- All route to same application
- Useful for www and non-www variants (myapp.com, www.myapp.com)

**A3: DNS Verification Takes Time**
- If DNS hasn't propagated after domain addition, AHP shows: "DNS not yet propagated, checking every 5 minutes"
- AHP continues polling until DNS is verified (up to 48 hours)
- Once verified, SSL provisioning begins automatically

**A4: Bring Your Own Certificate**
- Enterprise feature: user can upload custom certificate and key
- AHP installs uploaded certificate instead of requesting from Let's Encrypt
- Certificate expiration monitoring still applies
- User must manage renewal and re-upload before expiration

**A5: Certificate Renewal Failure**
- If Let's Encrypt renewal fails (e.g., DNS challenge fails)
- AHP retries renewal automatically 7 days before expiration
- If still failing 3 days before expiration, user receives urgent notification
- User can manually renew or update DNS configuration

### Business Rules
- Each domain can only be assigned to one application per team
- Domain must be verified via DNS before SSL provisioning
- SSL certificates are 90 days validity (Let's Encrypt standard)
- Renewal begins 30 days before expiration
- Certificate includes domain and www.domain variants by default
- Unused domains can be removed, freeing HTTPS provisioning quota

### Data Requirements
- Domain record: application ID, domain name, status (pending/verified/active), certificate expiration, renewal date
- Domain verification: TXT record value, verification timestamp

### Performance Requirements
- DNS verification: < 5 minutes after CNAME is set
- SSL provisioning: < 2 minutes after DNS verified
- Certificate renewal: automatic, zero-downtime

---

## UC4: Provision Managed Add-on (PostgreSQL Example)

### Overview
Add-ons provide managed database and cache services seamlessly integrated with applications. Provisioning is one-click, with connection details automatically injected as environment variables.

### Stakeholders
- **Primary**: Developer, Application owner
- **Secondary**: DevOps (for quota management), Finance (cost impact)

### Preconditions
- Application is deployed
- User has "Admin" or "Developer" role
- Team has quota for additional add-ons (storage, instance count)
- Selected add-on provider is available in team's region

### Main Success Scenario

1. **Browse Add-ons**: User navigates to application → Add-ons section
   - Shows available add-ons: PostgreSQL, MySQL, Redis, Memcached, MongoDB, S3, etc.
   - Shows provisioned add-ons with current usage

2. **Select PostgreSQL**: User clicks "Add PostgreSQL"
   - Presented with configuration form

3. **Configure Parameters**:
   - Add-on name: "myapp-db" (identifier for this instance)
   - Size: 1GB (tier: 1GB, 10GB, 50GB, 100GB, etc.)
   - Region: same as application (or different for resilience)
   - Version: PostgreSQL 13 (or latest)
   - Backup retention: 7 days (or 30 days for premium)

4. **Validate & Quote**: AHP shows estimated cost
   - PostgreSQL 1GB in us-east-1: $9.99/month
   - Backup storage: $0.50/month
   - Total: $10.49/month
   - User confirms

5. **Provision Add-on**: User clicks "Provision"
   - AHP requests add-on from provider (AWS RDS, Google Cloud SQL, etc.)
   - Provider allocates and configures PostgreSQL instance
   - Typical provisioning time: 2-5 minutes

6. **Await Completion**: AHP polls add-on provider for status
   - Shows "Creating... 45% complete"
   - Once ready, AHP receives connection details: hostname, port, database name, username, password

7. **Generate Connection String**: AHP generates PostgreSQL URI
   - Format: `psql://user:pass@host:5432/db`
   - Format: `DATABASE_URL=postgresql://user:pass@host:5432/db`

8. **Inject Environment Variable**: AHP adds environment variable to application config
   - Variable name: DATABASE_URL
   - Variable value: full connection URI
   - AHP marks variable as type: "add-on credential" (hidden in UI, encrypted)

9. **Redeploy Application**: AHP triggers a redeployment with new environment variable
   - Application is rebuilt and redeployed
   - New environment variable injected
   - Application can now connect to database

10. **Verification**: AHP verifies connectivity
    - Tests connection to database from application (optional)
    - If test fails, user receives error message with debugging tips

11. **Notification**: User receives notification
    - "PostgreSQL 'myapp-db' is ready. DATABASE_URL is available to your application."
    - Shows connection details in dashboard (obscured password)

12. **Automated Setup**: AHP configures automated backup and monitoring
    - Daily backups scheduled
    - Metrics enabled: storage used, active connections, queries per second
    - Alerts configured for high storage usage

### Postconditions
- PostgreSQL instance is running and accessible
- Connection string available as environment variable
- Application can connect and use database
- Automated backups running daily
- Metrics visible in AHP dashboard
- Monthly billing reflects add-on cost

### Alternative Flows

**A1: Provision Fails**
- If provider fails to create instance (quota exceeded, region unavailable)
- AHP shows error message with reason
- No charge incurred
- User can retry with different configuration

**A2: Restore from Backup**
- User can request restore to specific point-in-time
- Restoration creates new database instance (point-in-time-recovery)
- User can switch application to restored instance
- Original instance can be deleted if no longer needed

**A3: Scale Add-on Size**
- User can upgrade PostgreSQL from 1GB to 10GB
- Migration occurs with brief downtime (configurable)
- New size provisioned, data migrated, old instance terminated
- Billing updated for new size

**A4: Deprovision Add-on**
- User clicks "Delete Add-on" on myapp-db
- AHP shows warning: "This will permanently delete the database. Create a backup first?"
- User can optionally trigger backup before deletion
- User must confirm by typing "myapp-db"
- Once deleted, environment variable is removed from application config
- If application references DATABASE_URL, next deployment may fail until handled

### Business Rules
- Add-on credentials are never shown in logs or UI (except obscured in settings)
- Add-on credentials are automatically rotated every 90 days
- Backups are retained per plan (free: 7 days, paid: 30 days)
- Add-ons cannot be accessed directly (only via connection string)
- VPC peering required for enterprise on-premises access

### Data Requirements
- Add-on instance record: application ID, add-on type (Postgres), provider, provider ID, credentials (encrypted), connection string
- Backup records: timestamp, size, backup ID (for restore)

### Performance Requirements
- Provisioning time: < 5 minutes (cloud provider dependent)
- Connection latency: < 10ms (same region)
- Backup completion: < 1 hour (depends on database size)

---

**Document Version**: 1.0
**Last Updated**: 2024
