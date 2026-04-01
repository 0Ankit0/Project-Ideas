# Domain Model

The domain model represents the core business entities and their relationships in the Application Hosting Platform.

## Class Diagram

```mermaid
classDiagram
    class Team {
        +UUID team_id
        +String name
        +UUID owner_id
        +UUID billing_account_id
        +Timestamp created_at
        +createApplication(name, repo)
        +inviteMember(email, role)
        +removeMember(user_id)
        +getBillingAccount()
    }
    
    class Application {
        +UUID application_id
        +UUID team_id
        +String name
        +String git_repo_url
        +String git_branch_default
        +Enum runtime_type
        +Boolean is_active
        +deploy(commit_sha, branch)
        +addCustomDomain(domain)
        +scale(instance_count)
        +provisionAddOn(addon_type, plan)
        +getMetrics(time_range)
        +getLogs(filters)
    }
    
    class Deployment {
        +UUID deployment_id
        +UUID application_id
        +String commit_sha
        +String branch_name
        +Enum status
        +Integer build_duration_seconds
        +String image_uri
        +Timestamp created_at
        +getRollbackTarget()
        +getBuildLogs()
        +healthCheck()
    }
    
    class Environment {
        +UUID environment_id
        +UUID application_id
        +Enum environment_name
        +Integer instance_count
        +Integer min_instances
        +Integer max_instances
        +Boolean auto_scale_enabled
        +UUID current_deployment_id
        +setAutoScalingRules(rules)
        +scale(new_count)
    }
    
    class CustomDomain {
        +UUID domain_id
        +UUID application_id
        +String domain_name
        +Enum status
        +String cname_target
        +Timestamp verified_at
        +isPrimary()
        +verifyDNS()
    }
    
    class SSLCertificate {
        +UUID ssl_cert_id
        +UUID domain_id
        +String certificate_pem
        +String private_key_pem
        +Timestamp issued_at
        +Timestamp expires_at
        +Boolean needsRenewal()
        +renew()
    }
    
    class AddOn {
        +UUID addon_id
        +String name
        +Enum category
        +String provider
        +String pricing_per_month
        +getAvailablePlans()
    }
    
    class AddOnInstance {
        +UUID addon_instance_id
        +UUID addon_id
        +UUID application_id
        +String instance_name
        +String plan_tier
        +Enum status
        +String connection_string
        +scale(new_plan)
        +backup()
        +restore(backup_id)
    }
    
    class EnvVariable {
        +UUID env_var_id
        +UUID application_id
        +UUID environment_id
        +String key
        +String value
        +Boolean is_secret
        +Timestamp last_rotated_at
        +rotate()
    }
    
    class MetricDatapoint {
        +UUID metric_id
        +UUID application_id
        +String metric_name
        +Decimal value
        +String unit
        +Timestamp timestamp
        +String instance_id
    }
    
    class LogEntry {
        +UUID log_id
        +UUID application_id
        +Enum log_level
        +String message
        +Timestamp timestamp
        +String instance_id
    }
    
    class AlertRule {
        +UUID alert_rule_id
        +UUID application_id
        +String name
        +String condition
        +Integer duration_minutes
        +JSON notification_channels
        +Boolean is_enabled
        +evaluate()
        +fire()
    }
    
    class BillingAccount {
        +UUID billing_account_id
        +UUID team_id
        +String billing_email
        +Enum subscription_tier
        +Enum status
        +Date next_billing_date
        +getUsageMetrics()
        +generateInvoice()
    }
    
    class UsageRecord {
        +UUID usage_record_id
        +UUID billing_account_id
        +UUID application_id
        +Enum resource_type
        +Decimal quantity
        +Decimal unit_price
        +Timestamp recorded_at
    }

    %% Relationships
    Team "1" --o "*" Application : contains
    Team "1" --o "*" TeamMember : has
    Team "1" -- "1" BillingAccount : uses
    
    Application "1" --o "*" Deployment : generates
    Application "1" --o "*" Environment : defines
    Application "1" --o "*" CustomDomain : has
    Application "1" --o "*" EnvVariable : stores
    Application "1" --o "*" AddOnInstance : uses
    Application "1" --o "*" AlertRule : defines
    Application "1" --o "*" MetricDatapoint : emits
    Application "1" --o "*" LogEntry : generates
    
    Deployment "1" --o "*" LogEntry : produces
    
    Environment "1" -- "1" Deployment : runs
    
    CustomDomain "1" -- "1" SSLCertificate : has
    
    AddOn "1" --o "*" AddOnInstance : provides
    
    BillingAccount "1" --o "*" UsageRecord : tracks
```

## Entity Responsibilities

### Team
- **Responsibility**: Group users and manage shared access to applications
- **State**: Name, owner, billing account
- **Behaviors**: Member management, application CRUD, billing configuration

### Application
- **Responsibility**: Represent deployable artifact; orchestrate deployments, scaling, monitoring
- **State**: Name, Git repo, current deployments, connected add-ons, custom domains
- **Behaviors**: Deploy, scale, configure domains, manage secrets, collect metrics

### Deployment
- **Responsibility**: Track specific deployment instance with full lifecycle
- **State**: Status (queued, building, deploying, running, failed), build/deploy duration, image reference
- **Behaviors**: Health check, rollback, stream logs, get metrics

### Environment
- **Responsibility**: Represent logical environment (staging, production, preview) with scaling config
- **State**: Instance count, min/max limits, current running deployment, auto-scale rules
- **Behaviors**: Manual scale, auto-scale, update rules

### CustomDomain
- **Responsibility**: Map user domain to application, track verification status
- **State**: Domain name, CNAME target, verification token, status
- **Behaviors**: Verify DNS, issue SSL cert, display status

### SSLCertificate
- **Responsibility**: Manage TLS certificate lifecycle
- **State**: Certificate PEM, private key (encrypted), issuance/expiration dates
- **Behaviors**: Check renewal needed, renew automatically, install on LB

### AddOn & AddOnInstance
- **Responsibility**: Add-on catalog and provisioned instances
- **State**: Add-on type, plan tier, status, provider ID, connection credentials
- **Behaviors**: Provision, scale, backup, restore, connect (inject env var)

### EnvVariable
- **Responsibility**: Store and manage configuration/secrets
- **State**: Key-value pair, encryption flag, source (manual/addon/system)
- **Behaviors**: Rotate (especially for add-on credentials), inject at deploy time

### MetricDatapoint & LogEntry
- **Responsibility**: Store observability data
- **State**: Metric/log value, timestamp, instance source
- **Behaviors**: Query by time range, filter by instance, aggregate

### AlertRule
- **Responsibility**: Define alerting conditions and notifications
- **State**: Condition formula, duration, notification channels, enabled status
- **Behaviors**: Evaluate metrics, fire alert, send notifications

### BillingAccount & UsageRecord
- **Responsibility**: Track resource consumption and generate invoices
- **State**: Billing tier, payment method, usage records per resource type
- **Behaviors**: Record usage hourly, generate monthly invoices, process payments

---

**Document Version**: 1.0
**Last Updated**: 2024
