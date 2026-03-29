# Cloud Architecture - Backend as a Service Platform

## Reference Cloud Mapping (AWS Example)

| Capability | Reference Service |
|------------|-------------------|
| Public edge | CloudFront / ALB + AWS WAF |
| API and realtime gateway | ECS/Fargate or EKS |
| Worker fleet | ECS/Fargate, EKS jobs, or queue workers |
| PostgreSQL | Amazon RDS for PostgreSQL |
| Messaging / queue | Amazon SQS / EventBridge |
| Secret storage | AWS Secrets Manager / HashiCorp Vault |
| Reporting store | Redshift / RDS replica / analytics warehouse |
| Monitoring | CloudWatch + OpenTelemetry |
| Identity federation | IAM Identity Center / external IdP |

## Architecture Notes

- The control plane can run in one cloud while adapters target multiple supported providers.
- Production environments should isolate secret domains, project metadata, and provider egress policies carefully.
- Switchover workflows may require temporary dual-writes, copy jobs, or migration runners depending on capability type.

## Cloud Controls for Isolation and SLO

| Layer | Design choice |
|---|---|
| API ingress | regional gateways with WAF and per-tenant rate limits |
| compute | dedicated worker pools per environment tier |
| data | PostgreSQL with RLS and encrypted backups |
| secrets | KMS-backed secret stores with scoped access policies |
| observability | centralized metrics/traces/logs with tenant-aware labels |

- Migration cutovers use traffic steering and health gates from observability signals.
