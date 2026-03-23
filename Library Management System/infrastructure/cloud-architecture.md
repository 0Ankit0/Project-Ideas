# Cloud Architecture - Library Management System

## Reference Cloud Mapping (AWS Example)

| Capability | Reference Service |
|------------|-------------------|
| Patron and staff frontend hosting | CloudFront + S3 / Amplify |
| Public protection | AWS WAF |
| API and workers | ECS/Fargate or EKS |
| Database | Amazon RDS for PostgreSQL |
| Search | Amazon OpenSearch |
| Messaging | Amazon SQS / EventBridge |
| Object storage | Amazon S3 |
| Notifications | Amazon SES / SNS |
| Monitoring | CloudWatch + OpenTelemetry |
| Identity federation | IAM Identity Center / external IdP |

## Architecture Notes
- Separate production and non-production environments to protect patron data and operational integrity.
- Retain backups and recovery procedures for circulation records, hold queues, and financial events.
- Keep search indexing asynchronous but monitor freshness to avoid stale availability information.
