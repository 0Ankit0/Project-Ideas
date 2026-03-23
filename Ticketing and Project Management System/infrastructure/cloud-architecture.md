# Cloud Architecture - Ticketing and Project Management System

## Reference Cloud Mapping (AWS Example)

| Capability | Reference Service |
|------------|-------------------|
| Frontend hosting | CloudFront + S3 or Amplify |
| Public protection | AWS WAF |
| API and workers | ECS/Fargate or EKS |
| Database | Amazon RDS for PostgreSQL |
| Object storage | Amazon S3 |
| Messaging | Amazon SQS / EventBridge |
| Search | Amazon OpenSearch |
| Identity federation | IAM Identity Center / external IdP |
| Malware scanning | Lambda + antivirus pipeline |
| Monitoring | CloudWatch + OpenTelemetry |

## Architecture Notes
- Use separate accounts or projects for production and non-production environments.
- Replicate database backups and object storage policies according to retention requirements.
- Emit workflow and audit events to centralized logging and observability systems.
