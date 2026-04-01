# AWS Cloud Architecture for High-Demand Ticket Sales

This document details the complete AWS cloud architecture for the Event Ticketing Platform, designed to handle 100K concurrent users during peak onsale events with <500ms latency and >99% uptime.

---

## Architecture Principles

1. **Scalability:** Auto-scaling based on demand (cost-efficient)
2. **Resilience:** Multi-AZ, automatic failover, graceful degradation
3. **Security:** Encryption, least-privilege IAM, network isolation
4. **Cost-efficiency:** Right-sizing, reserved instances, spot instances for burst
5. **Observability:** Comprehensive monitoring, real-time dashboards, alerting

---

## Compute Layer (EKS - Elastic Kubernetes Service)

### EKS Cluster Configuration
- **Kubernetes Version:** 1.27+ (latest stable)
- **Availability Zones:** 3 (us-east-1a, 1b, 1c)
- **Network:** VPC with public/private/data subnets

### Node Groups

#### On-Demand Nodes (Baseline Load)
- **Instance Type:** t3.xlarge (4 vCPU, 16 GB RAM)
- **Desired Count:** 20 nodes
- **Min Count:** 10 (always running)
- **Max Count:** 50 (scale during peak)
- **Cost:** ~$500/month (baseline)
- **Purpose:** Reliable core workload (APIs, databases)

#### Spot Instances (Burst Capacity)
- **Instance Type:** c5.2xlarge (8 vCPU, 16 GB RAM)
- **Desired Count:** 0 (scale up on demand)
- **Max Count:** 200 (burst capacity)
- **Cost:** ~$0.20/hour vs $0.35/hour on-demand (40% savings)
- **Purpose:** Temporary capacity during onsales, can be interrupted
- **Interruption Handling:** Pod disruption budgets (PDB) ensure graceful eviction

### Auto-Scaling Configuration

#### Cluster Auto-Scaler
- **Min Nodes:** 10 (minimum to serve base traffic)
- **Max Nodes:** 250 (max capacity during extreme load)
- **Scale-Up Trigger:** Pod pending due to insufficient resources
- **Scale-Down:** Node utilization <50% for 10 minutes
- **Metrics to Scale:** CPU, memory, custom metrics

#### Horizontal Pod Autoscaler (HPA)

| Service | Min Pods | Max Pods | Scale Trigger | Target |
|---|---|---|---|---|
| Kong (API GW) | 3 | 20 | CPU >70%, Latency >1s | 1000 req/s per pod |
| InventoryService | 5 | 100 | Hold queue >10K, CPU >80% | Ticket holds |
| OrderService | 3 | 30 | Error rate >1%, Latency >500ms | Order creation |
| PaymentService | 5 | 50 | Payment queue >100, CPU >70% | Payment throughput |
| TicketService | 2 | 20 | PDF generation queue >50 | PDF generation jobs |
| NotificationService | 2 | 15 | Email queue >1000 | Notification delivery |
| CheckInService | 2 | 10 | Check-in requests >100/s | Event attendance |

### Container Image Registry

#### Amazon ECR (Elastic Container Registry)
- **Repositories:** One per service (event-service, inventory-service, etc.)
- **Image Tagging:** 
  - `latest` (development)
  - `v1.0.0` (semantic versioning)
  - `prod-stable` (production approved)
  - `staging-latest` (staging environment)
- **Scan on Push:** Vulnerability scanning enabled
- **Retention Policy:** Keep 10 latest images, delete older (cost optimization)
- **Replication:** Cross-region replication for disaster recovery

---

## Data Layer

### RDS Aurora (PostgreSQL)

#### Primary Instance
- **Instance Type:** db.r6g.2xlarge (8 vCPU, 64 GB RAM, Graviton2)
- **Storage:** Aurora storage (auto-scaling, 10 GB - 128 TB)
- **Multi-AZ:** Enabled (automatic failover in 30 seconds)
- **Backup:** Daily automated backups, 35-day retention
- **Performance:** 
  - IOPS: 6,000 (scales with storage)
  - Throughput: 300 MB/s
  - p95 latency: <50ms
- **Cost:** ~$1,500/month

#### Read Replicas
- **Count:** 2-3 read replicas in different AZs
- **Purpose:** Distribute read-heavy queries (reporting, search)
- **Auto-scaling:** Add replicas if CPU >70%
- **Max Replicas:** 15 (cross-region included)

#### Database Instances
| Database | Tables | Primary Use |
|---|---|---|
| events_db | events, venues, seating_maps | Event data |
| orders_db | orders, order_items, payments | Transaction data |
| users_db | customers, accounts, preferences | Customer data |

#### Connection Pooling
- **PgBouncer:** Deployed on EKS for connection pooling
- **Max Connections:** 500 (application limit)
- **Idle Connection Timeout:** 60 seconds
- **Mode:** Transaction pooling (connection released after query)

### Elasticache Redis Cluster

#### Cluster Configuration
- **Cluster Mode:** Enabled (16 shards, 2 replicas per shard = 32 nodes)
- **Node Type:** cache.r6g.xlarge (26 GB memory)
- **Total Capacity:** 832 GB
- **Multi-AZ:** Enabled (automatic failover)
- **Subnet Group:** Private data subnets

#### Data Structures
- **Strings:** Ticket holds (JSON serialized)
- **Sorted Sets:** Seat maps (score = seat availability)
- **Hashes:** Event pricing data
- **Lists:** Notification queues
- **Keys with TTL:** Automatic expiration (holds expire after 10 minutes)

#### Caching Strategy
| Key | Type | TTL | Size Est. |
|---|---|---|---|
| event:{id}:seats | Sorted set | 30s | 100 KB |
| hold:{id} | String | 10m | 1 KB |
| pricing:{event-id} | Hash | 1m | 10 KB |
| session:{user-id} | String | 1h | 2 KB |

#### Performance
- **Hit Rate:** >95% (excellent cache efficiency)
- **Eviction Rate:** <1% (minimal key eviction)
- **Latency:** <5ms (in-memory access)

### Elasticsearch (OpenSearch)

#### Cluster Configuration
- **Nodes:** 3 data nodes (t3.medium dev, r6g.xlarge prod)
- **Storage:** 100 GB (production), 20 GB (staging)
- **Replicas:** 1 (high availability)

#### Indices
- **events**: Full-text search of event names, descriptions
- **Mapping:**
  - name (text): full-text searchable
  - category (keyword): faceted search
  - location (geo_point): geographic search
  - date (date): date range filtering
  - price (numeric): price range filtering

#### Search Capabilities
- **Full-text:** Event name contains "Summer Festival"
- **Facets:** Show category, date, price distribution
- **Geo-search:** Events within 50 miles of user location
- **Combined:** Category = Concert, Date >= 2024-06-01, Price < $100

#### Refresh Interval
- **30 seconds:** Balance between freshness and performance
- **Bulk operations:** Temporarily disable refresh, bulk index, re-enable

---

## Storage

### S3 Buckets

#### Static Assets (Website)
- **Bucket:** `ticketing-static-assets`
- **Contents:** React app builds, JavaScript bundles, CSS
- **Versioning:** Enabled
- **Lifecycle:** Delete previous versions after 90 days
- **CDN:** CloudFront distribution (served from edge locations)

#### Ticket PDFs
- **Bucket:** `ticketing-ticket-pdfs`
- **Contents:** Generated ticket PDFs, QR codes
- **Versioning:** Disabled (immutable after creation)
- **Lifecycle:** Delete after 90 days (tickets archived in database)
- **Encryption:** AES-256
- **Access:** Presigned URLs (valid 24 hours)
- **Cost:** ~$50/month (1,000 events × 500 tickets × 50 KB = 25 GB)

#### Event Media
- **Bucket:** `ticketing-event-media`
- **Contents:** Event images, posters, promotional videos
- **Versioning:** Enabled
- **Lifecycle:** Keep current + 2 previous versions
- **CDN:** CloudFront distribution

#### Application Logs
- **Bucket:** `ticketing-application-logs`
- **Contents:** CloudWatch logs, ALB access logs, CloudFront logs
- **Lifecycle:** Move to Glacier after 90 days (cold storage)
- **Retention:** 7 years (compliance requirement)

---

## Messaging and Events

### SQS (Simple Queue Service)

#### Email Queue
- **Queue Name:** `ticketing-email-notifications`
- **Message Retention:** 4 days
- **Visibility Timeout:** 30 seconds (time to process message)
- **Message Size:** Up to 256 KB
- **Throughput:** 300 messages/second (production average), 1000/s peak
- **Batch Processing:** Receive 10 messages per call
- **Dead Letter Queue (DLQ):** Messages failing 3 retries move here

#### PDF Generation Queue
- **Queue Name:** `ticketing-pdf-generation`
- **Throughput:** 100 messages/second
- **Workers:** Lambda functions (auto-scaling)
- **Timeout:** 60 seconds (time to generate PDF)

### SNS (Simple Notification Service)

#### Topics
1. **OrderTopic** (`order-created`, `order-confirmed`, `order-cancelled`)
2. **PaymentTopic** (`payment-processed`, `payment-failed`)
3. **TicketTopic** (`ticket-generated`, `ticket-transferred`)
4. **EventTopic** (`event-updated`, `event-cancelled`)

#### Subscriptions
- **OrderTopic → Email Queue:** Send order confirmations
- **OrderTopic → Order Service:** Update internal state
- **PaymentTopic → Accounting:** Record financial transactions
- **TicketTopic → Notification Service:** Send ticket delivery emails
- **EventTopic → Cache Invalidation:** Update cached event data

### EventBridge

#### Rules

| Rule | Schedule | Target | Purpose |
|---|---|---|---|
| reminder-notification | 24h before event | SNS | Send reminder SMS |
| daily-report | 11:00 PM | Lambda | Generate daily sales report |
| weekly-analytics | Monday 8:00 AM | SQS | Weekly analytics job |
| cleanup-expired-holds | Every 10 minutes | Lambda | Cleanup expired ticket holds |

---

## Monitoring and Observability

### CloudWatch Metrics

#### Application Metrics
- **Requests/Second:** Track API request volume
- **Error Rate:** HTTP 4xx, 5xx errors
- **Latency (p50, p95, p99):** Response time percentiles
- **Payment Success Rate:** % of successful payments
- **Ticket Hold Success Rate:** % of successful hold creations

#### Infrastructure Metrics
- **CPU Utilization:** Per pod, per node
- **Memory Utilization:** Available memory
- **Network I/O:** Bytes in/out per node
- **Storage:** Disk usage percentage
- **Database:** Connections, query latency, slow queries

#### Business Metrics
- **Orders Created:** Count per hour
- **Revenue:** Sum of successful payments
- **Refunds:** Count and amount per hour
- **Customer Retention:** DAU (Daily Active Users)

### CloudWatch Dashboards

#### Real-Time Traffic Dashboard
- **Widgets:**
  - Requests/sec (line chart)
  - Error rate (bar chart)
  - Latency p95 (gauge)
  - Ticket hold queue depth (number)
  - Active connections (number)

#### Service Health Dashboard
- **Services:** Kong, EventService, OrderService, PaymentService, etc.
- **Metrics per service:** Error rate, latency, CPU
- **Status:** Green (healthy), Yellow (degraded), Red (critical)

#### Business Metrics Dashboard
- **Revenue:** Cumulative by day/week
- **Orders:** Count by status (pending, confirmed, refunded)
- **Refunds:** Count and rate
- **Customer acquisition:** New customers per day

### CloudWatch Alarms

#### Critical Alarms (Page on-call immediately)
- Error rate >1% for 5 minutes
- Payment service latency >2 seconds
- Database connection exhaustion (>90% of pool)
- Ticket hold success rate <95%

#### Warning Alarms (Create incident ticket)
- Error rate >0.5% for 10 minutes
- API latency p95 >1 second for 10 minutes
- Memory utilization >80%
- Disk utilization >85%

#### Info Alarms (Log for analysis)
- Node auto-scaling event
- Deployment completed successfully
- Health check failed but recovered

### X-Ray Distributed Tracing

#### Sampling
- **Production:** Sample 1% of requests (cost optimization)
- **Staging:** Sample 10% (better visibility in testing)
- **Exceptions:** Always sample errors (100% of 5xx errors)

#### Trace Analysis
- **Service Map:** Visualize service dependencies
- **Latency Analysis:** Identify bottlenecks
- **Error Analysis:** Track error location and root cause

### Logging (CloudWatch Logs)

#### Log Groups
- `/aws/eks/cluster/ticketing-platform`: EKS cluster logs
- `/aws/lambda/pdf-generation`: Lambda function logs
- `/aws/rds/instance/ticketing-db`: Database logs
- `ticketing-application/kong`: Kong API Gateway logs
- `ticketing-application/event-service`: Application logs

#### Log Retention
- **Production:** 30 days (CloudWatch), archive to Glacier after 30 days
- **Staging:** 7 days
- **Development:** 1 day

---

## Capacity Planning for 100K Concurrent Users

### Traffic Assumptions
- **Peak Load:** 100K concurrent users during onsale event
- **Request Rate:** 50,000 req/s (typical), 100,000 req/s (spike)
- **P95 Latency Target:** <500ms
- **Error Rate Target:** <0.5%

### Resource Sizing

| Component | Baseline | Peak | Scaling Factor |
|---|---|---|---|
| Kong Pods | 5 | 20 | 4x |
| InventoryService Pods | 10 | 100 | 10x |
| OrderService Pods | 5 | 30 | 6x |
| PaymentService Pods | 10 | 50 | 5x |
| EKS Nodes | 20 | 250 | 12x |
| Database Connections | 100 | 400 | 4x |
| Redis Memory | 100 GB | 300 GB | 3x |

### Cost Estimation

#### Hourly Cost Breakdown
| Component | Baseline | Peak | 1-Hour Peak Cost |
|---|---|---|---|
| EKS (EC2) | $10 | $80 | $80 |
| RDS Aurora | $8 | $8 | $8 |
| ElastiCache Redis | $5 | $15 | $15 |
| S3 | $1 | $1 | $1 |
| Data Transfer | $2 | $50 | $50 |
| **Total Hourly** | **$26** | **$154** | **$154** |

#### Monthly Cost (Sample)
- **Baseline:** 30 × 24 × $26 = $18,720
- **Peak days:** 4 onsale events × 2 hours × $154 = $1,232
- **Monthly total:** ~$20,000 (production)

---

## Disaster Recovery

### RPO (Recovery Point Objective)
- **Acceptable Data Loss:** 1 hour
- **Approach:** Hourly snapshots of critical data

### RTO (Recovery Time Objective)
- **Acceptable Downtime:** 4 hours
- **Approach:** Automated failover in standby region

### Backup Strategy
- **Database:** Automated daily snapshots, cross-region replication
- **Elasticsearch:** Daily snapshots (S3 repository)
- **Configuration:** Stored in git (infrastructure-as-code)
- **Container Images:** Stored in ECR (retrievable within minutes)

### Failover Process
1. **Detection:** Health check failure in primary region
2. **Decision:** Incident commander initiates failover
3. **DNS Update:** Route53 updates to secondary region (~30 seconds)
4. **Database Promotion:** Standby RDS promoted to primary (~2 minutes)
5. **EKS Scaling:** Standby region EKS scales up (~5 minutes)
6. **Verification:** Health checks pass, traffic flowing to secondary
7. **RTO Total:** ~10-15 minutes (acceptable for non-financial transaction)

---

## Cost Optimization Strategies

1. **Reserved Instances:** 50% discount for 1-year commitment
   - Core baseline load: purchase reserved instances
   - Burst load: use spot instances
   - Mix: 70% reserved + 30% spot/on-demand

2. **Spot Instances:** 60-70% discount vs on-demand
   - Suitable for stateless services (pods can be evicted)
   - Unsuitable for databases (not offered as spot)

3. **RDS Savings Plan:** 40% discount for database
   - Commit to 1 year of database capacity
   - Flexibility to change instance type

4. **Data Transfer Optimization:**
   - CloudFront caching: reduces ALB/NAT data transfer
   - VPC Endpoints for S3: free S3 access (avoid NAT charges)
   - Cross-AZ data transfer: $0.01 per GB (charge between AZs)

5. **Storage Optimization:**
   - S3 Intelligent-Tiering: auto-moves cold data to Glacier
   - Compression: gzip reduces data size by 70%
   - Lifecycle policies: delete unnecessary logs after retention

6. **Right-Sizing:**
   - Monitor actual CPU/memory utilization
   - Quarterly review of instance types
   - Adjust based on usage patterns

---

This AWS architecture supports the Event Ticketing Platform's requirement of handling 100K concurrent users with <500ms latency and >99% uptime, while maintaining cost-efficiency through auto-scaling and optimization strategies.
