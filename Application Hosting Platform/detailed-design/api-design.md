# REST API Specification

## Base URL
```
https://api.ahp.io/v1
Authentication: Bearer {JWT_TOKEN}
```

## Applications API

### List Applications
```http
GET /applications
Query Params:
  - team_id: UUID (required)
  - status: active|archived (optional)
  - limit: 50 (default)
  - offset: 0 (default)

Response: 200 OK
{
  "applications": [
    {
      "application_id": "uuid",
      "name": "my-app",
      "git_repo_url": "https://github.com/acme/my-app",
      "runtime_type": "nodejs",
      "is_active": true,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "total": 25,
  "limit": 50,
  "offset": 0
}
```

### Create Application
```http
POST /applications
{
  "team_id": "uuid",
  "name": "my-app",
  "description": "My awesome app",
  "git_repo_url": "https://github.com/acme/my-app",
  "git_branch_default": "main"
}

Response: 201 Created
{
  "application_id": "uuid",
  "name": "my-app",
  "ahp_domain": "my-app-{random}.ahp.io",
  "created_at": "2024-01-15T10:00:00Z"
}
```

### Get Application
```http
GET /applications/{application_id}

Response: 200 OK
{
  "application_id": "uuid",
  "team_id": "uuid",
  "name": "my-app",
  "git_repo_url": "https://github.com/acme/my-app",
  "runtime_type": "nodejs",
  "current_deployment": { ... },
  "custom_domains": [ ... ],
  "addon_instances": [ ... ],
  "environments": { ... },
  "created_at": "2024-01-15T10:00:00Z"
}
```

### Update Application
```http
PATCH /applications/{application_id}
{
  "name": "my-app-v2",
  "description": "Updated description"
}

Response: 200 OK
```

### Delete Application
```http
DELETE /applications/{application_id}

Response: 204 No Content
```

## Deployments API

### Trigger Deployment
```http
POST /applications/{application_id}/deployments
{
  "branch": "main",
  "commit_sha": "abc123def456" (optional)
}

Response: 202 Accepted
{
  "deployment_id": "uuid",
  "status": "queued",
  "created_at": "2024-01-15T10:00:00Z",
  "estimated_completion": "2024-01-15T10:02:00Z"
}
```

### Get Deployment
```http
GET /deployments/{deployment_id}

Response: 200 OK
{
  "deployment_id": "uuid",
  "application_id": "uuid",
  "status": "running",
  "commit_sha": "abc123",
  "branch_name": "main",
  "build_duration_seconds": 45,
  "total_duration_seconds": 95,
  "image_uri": "registry.ahp.io/app:v1.2.3",
  "created_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:01:35Z"
}
```

### Get Deployment Logs (Server-Sent Events)
```http
GET /deployments/{deployment_id}/logs?stream=true&follow=true

Response: 200 OK (text/event-stream)
data: {"level": "info", "message": "Starting build...", "timestamp": "2024-01-15T10:00:00Z"}
data: {"level": "info", "message": "npm install...", "timestamp": "2024-01-15T10:00:05Z"}
data: {"level": "error", "message": "Module not found", "timestamp": "2024-01-15T10:00:10Z"}
```

### Rollback Deployment
```http
POST /deployments/{deployment_id}/rollback
{
  "reason": "Error rate spike detected"
}

Response: 202 Accepted
{
  "new_deployment_id": "uuid",
  "status": "deploying",
  "rolled_back_to": "previous-deployment-id"
}
```

## Scaling API

### Get Application Scaling Config
```http
GET /applications/{application_id}/scaling

Response: 200 OK
{
  "current_instance_count": 3,
  "min_instances": 1,
  "max_instances": 10,
  "auto_scale_enabled": true,
  "auto_scale_rules": [
    {
      "rule_id": "uuid",
      "metric": "cpu_usage",
      "operator": "greater_than",
      "threshold": 70,
      "duration_minutes": 2,
      "scale_action": "add_2_instances",
      "cooldown_minutes": 5
    }
  ],
  "scaling_history": [
    {
      "timestamp": "2024-01-15T11:30:00Z",
      "old_count": 1,
      "new_count": 3,
      "reason": "cpu_threshold_exceeded",
      "duration_seconds": 95
    }
  ]
}
```

### Update Scaling
```http
PUT /applications/{application_id}/scaling
{
  "current_instance_count": 5,
  "min_instances": 1,
  "max_instances": 20,
  "auto_scale_enabled": true,
  "rules": [
    {
      "metric": "cpu_usage",
      "operator": "greater_than",
      "threshold": 70,
      "duration_minutes": 2,
      "scale_action": "add_2_instances",
      "cooldown_minutes": 5
    }
  ]
}

Response: 200 OK
```

## Environment Variables API

### List Env Variables
```http
GET /applications/{application_id}/env-vars?environment=production

Response: 200 OK
{
  "env_variables": [
    {
      "key": "DATABASE_URL",
      "is_secret": true,
      "source_type": "addon",
      "value": "***hidden***",
      "last_rotated_at": "2024-01-01T00:00:00Z"
    },
    {
      "key": "API_KEY",
      "is_secret": true,
      "source_type": "manual",
      "value": "***hidden***"
    }
  ]
}
```

### Set Env Variable
```http
POST /applications/{application_id}/env-vars
{
  "key": "LOG_LEVEL",
  "value": "debug",
  "is_secret": false,
  "environment": "staging"
}

Response: 201 Created
```

### Delete Env Variable
```http
DELETE /applications/{application_id}/env-vars/{key}

Response: 204 No Content
```

## Custom Domains API

### Add Custom Domain
```http
POST /applications/{application_id}/domains
{
  "domain_name": "myapp.com",
  "is_primary": true
}

Response: 201 Created
{
  "domain_id": "uuid",
  "domain_name": "myapp.com",
  "status": "pending",
  "cname_target": "myapp-{id}.ahp.io",
  "instructions": "Create CNAME record: myapp.com → myapp-{id}.ahp.io",
  "created_at": "2024-01-15T10:00:00Z"
}
```

### Get Domain Status
```http
GET /applications/{application_id}/domains/{domain_id}

Response: 200 OK
{
  "domain_id": "uuid",
  "domain_name": "myapp.com",
  "status": "active",
  "cname_target": "myapp-{id}.ahp.io",
  "ssl_certificate": {
    "issued_at": "2024-01-15T10:00:00Z",
    "expires_at": "2025-04-15T23:59:59Z",
    "issuer": "letsencrypt",
    "renewal_scheduled_at": "2025-03-16T00:00:00Z"
  },
  "verified_at": "2024-01-15T10:15:00Z"
}
```

### Verify Domain DNS
```http
POST /applications/{application_id}/domains/{domain_id}/verify

Response: 200 OK
{
  "status": "dns_verified",
  "verified_at": "2024-01-15T10:15:00Z"
}
```

## Add-ons API

### List Available Add-ons
```http
GET /addons

Response: 200 OK
{
  "addons": [
    {
      "addon_id": "uuid",
      "name": "postgresql",
      "display_name": "PostgreSQL Database",
      "category": "database",
      "plans": [
        {
          "tier": "1gb",
          "pricing_per_month": 9.99,
          "description": "1GB storage"
        }
      ]
    }
  ]
}
```

### Provision Add-on
```http
POST /applications/{application_id}/addons
{
  "addon_id": "uuid",
  "instance_name": "mydb",
  "plan_tier": "1gb",
  "region": "us-east-1"
}

Response: 202 Accepted
{
  "addon_instance_id": "uuid",
  "status": "provisioning",
  "progress": "45%",
  "estimated_completion": "2024-01-15T10:05:00Z"
}
```

### Deprovision Add-on
```http
DELETE /applications/{application_id}/addons/{addon_instance_id}
{
  "backup_first": true
}

Response: 202 Accepted
{
  "status": "deprovisioning"
}
```

## Logs API

### Stream Application Logs
```http
GET /applications/{application_id}/logs?follow=true&level=warn,error&limit=100

Response: 200 OK (text/event-stream)
data: {"timestamp": "2024-01-15T11:30:00Z", "level": "warn", "message": "High memory usage", "instance_id": "pod-1"}
data: {"timestamp": "2024-01-15T11:30:05Z", "level": "error", "message": "Connection timeout", "instance_id": "pod-2"}
```

## Metrics API

### Get Metrics
```http
GET /applications/{application_id}/metrics?metric=cpu_usage,memory_usage,request_count&time_range=24h

Response: 200 OK
{
  "metrics": {
    "cpu_usage": [
      {"timestamp": "2024-01-15T10:00:00Z", "value": 45.2, "unit": "%"},
      {"timestamp": "2024-01-15T10:01:00Z", "value": 48.7, "unit": "%"}
    ],
    "memory_usage": [...],
    "request_count": [...]
  }
}
```

## Billing API

### Get Usage
```http
GET /billing/usage?team_id=uuid&month=2024-01

Response: 200 OK
{
  "period": "2024-01",
  "usage": [
    {
      "application_id": "uuid",
      "resource_type": "compute_instance_hours",
      "quantity": 360,
      "unit_price": 0.05,
      "total": 18.00
    },
    {
      "application_id": "uuid",
      "resource_type": "bandwidth_gb",
      "quantity": 50,
      "unit_price": 0.10,
      "total": 5.00
    }
  ],
  "total_amount": 23.00,
  "currency": "USD"
}
```

### Get Invoices
```http
GET /billing/invoices?team_id=uuid&limit=12

Response: 200 OK
{
  "invoices": [
    {
      "invoice_id": "uuid",
      "period": "2024-01",
      "total_amount": 23.00,
      "status": "paid",
      "created_at": "2024-02-01T00:00:00Z",
      "due_date": "2024-02-15T00:00:00Z",
      "pdf_url": "https://api.ahp.io/invoices/uuid.pdf"
    }
  ]
}
```

---

**Document Version**: 1.0
**Last Updated**: 2024
