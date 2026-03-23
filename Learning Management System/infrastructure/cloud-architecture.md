# Cloud Architecture - Learning Management System

## Reference Cloud Mapping (AWS Example)

| Capability | Reference Service |
|------------|-------------------|
| Frontend hosting | CloudFront + S3 / Amplify |
| Public protection | AWS WAF |
| API and workers | ECS/Fargate or EKS |
| Database | Amazon RDS for PostgreSQL |
| Search / analytics projection | Amazon OpenSearch |
| Messaging | Amazon SQS / EventBridge |
| Media and assets | Amazon S3 |
| Notifications | Amazon SES / SNS |
| Monitoring | CloudWatch + OpenTelemetry |
| Identity federation | IAM Identity Center / external IdP |

## Architecture Notes

- Separate production and non-production environments to protect tenant data and grading records.
- Maintain backups and recovery procedures for enrollments, assessments, grades, and certificate history.
- Use asynchronous projection and analytics pipelines but monitor freshness for learner-facing progress and staff dashboards.
