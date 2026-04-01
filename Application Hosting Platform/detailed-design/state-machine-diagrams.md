# State Machine Diagrams

## Deployment State Machine

```mermaid
stateDiagram-v2
    [*] --> Queued: trigger deploy
    
    Queued --> Building: start build
    Queued --> Failed: queue timeout
    
    Building --> Deploying: build success
    Building --> Failed: build error
    Building --> Failed: build timeout > 10min
    
    Deploying --> Running: health check pass
    Deploying --> Failed: health check fail
    Deploying --> Failed: orchestration error
    
    Running --> Running: active serving traffic
    Running --> RolledBack: user triggers rollback
    Running --> RolledBack: auto-rollback (error rate spike)
    
    Failed --> [*]: cleanup
    RolledBack --> [*]: previous version now running
    Running --> [*]: superseded by new deployment
    
    note right of Queued
        Waiting in build queue
        Max wait: 1 hour
    end note
    
    note right of Building
        Timeout: 10 minutes
        Can retry on failure
    end note
    
    note right of Deploying
        Health checks: 3 retries
        Timeout: 30 seconds
    end note
    
    note right of Running
        Actively serving traffic
        Can be rolled back
    end note
```

## Application Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> Active: create app
    
    Active --> Active: deploy new version
    Active --> Active: scale instances
    Active --> Active: add domains/addons
    
    Active --> Suspended: billing overdue > 30 days
    Active --> Suspended: user manually suspends
    
    Suspended --> Active: pay invoice
    Suspended --> Suspended: still overdue
    Suspended --> Deleted: user deletes (soft delete)
    
    Deleted --> [*]: hard delete after retention
    
    note right of Active
        Application running
        Serving user traffic
        Full functionality
    end note
    
    note right of Suspended
        No traffic accepted
        Config accessible
        Can be reactivated
    end note
    
    note right of Deleted
        Soft-deleted (7 day grace)
        Can be restored
        After grace → hard delete
    end note
```

## Custom Domain SSL Certificate Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Pending: user adds domain
    
    Pending --> DNSVerified: CNAME verified
    Pending --> Failed: DNS verification timeout
    
    DNSVerified --> CertIssued: SSL cert issued
    DNSVerified --> Failed: Let's Encrypt fails
    
    CertIssued --> Active: cert installed on LB
    CertIssued --> Failed: installation error
    
    Active --> Active: cert valid (0-30 days before expiry)
    Active --> NeedRenewal: cert < 30 days to expiry
    
    NeedRenewal --> Renewing: auto-renewal triggered
    Renewing --> Active: renewal successful
    Renewing --> Expired: renewal failed
    
    Expired --> Deleted: user removes domain
    Active --> Deleted: user removes domain
    Failed --> Deleted: user removes domain after error
    
    Deleted --> [*]: domain/cert cleaned up
    
    note right of Pending
        Awaiting DNS propagation
        Timeout: 48 hours
    end note
    
    note right of DNSVerified
        DNS verified, cert requested
        Let's Encrypt ACME process
    end note
    
    note right of Active
        Certificate installed
        HTTPS working
        Zero-downtime renewals
    end note
    
    note right of NeedRenewal
        Auto-renewal in progress
        Maintain service continuity
    end note
```

## Add-on Instance Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Provisioning: user creates addon
    
    Provisioning --> Provisioning: polling provider
    Provisioning --> Active: provider ready
    Provisioning --> Failed: provider error
    Provisioning --> Failed: quota exceeded
    
    Active --> Active: in use
    Active --> Scaling: user requests scale
    Active --> Deprovisioning: user deletes
    
    Scaling --> Scaling: migration in progress
    Scaling --> Active: scaling complete
    Scaling --> Failed: scaling timeout
    
    Failed --> Deprovisioning: user retries or deletes
    Deprovisioning --> Deprovisioning: provider cleanup
    Deprovisioning --> [*]: removed
    
    note right of Provisioning
        Creating managed service
        Wait for provider response
        Timeout: 5 minutes
    end note
    
    note right of Active
        Fully operational
        Connection available
        Metrics/backups enabled
    end note
    
    note right of Scaling
        Plan tier change
        Zero-downtime if possible
        Data migration
    end note
```

---

**Document Version**: 1.0
**Last Updated**: 2024
