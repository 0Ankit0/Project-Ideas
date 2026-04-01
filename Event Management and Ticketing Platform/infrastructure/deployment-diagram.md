# Deployment Diagram - Event Ticketing Platform

This document provides a comprehensive Kubernetes deployment architecture for the Event Management and Ticketing Platform, designed to handle 100K concurrent users during high-demand onsale events.

---

## Architecture Overview

The platform follows a microservices architecture deployed on AWS EKS (Kubernetes) with supporting managed services for data storage, caching, and external integrations.

---

## Layer 1: Client Tier

### Web Application
- **Technology:** React.js with TypeScript
- **Deployment:** S3 + CloudFront CDN
- **Features:**
  - Event browsing and search
  - Ticket selection and checkout
  - Account management
  - Admin dashboard for organizers
- **Optimization:** Code splitting, lazy loading, service worker for offline capability

### Mobile Applications
- **iOS:** React Native
- **Android:** React Native
- **Deployment:** App Store, Google Play
- **Features:**
  - Event discovery
  - Ticket purchase
  - Check-in QR scanning
  - Push notifications for reminders
  - Mobile wallet integration (Apple Wallet, Google Pay)

---

## Layer 2: CDN and Static Asset Delivery

### CloudFront Distribution
- **Origin 1:** S3 bucket (static React app, JavaScript bundles, CSS)
- **Origin 2:** API Gateway (for dynamic API requests)
- **Origin 3:** S3 bucket for ticket PDFs and event media
- **Caching Rules:**
  - HTML: Cache-Control: max-age=0 (no-cache, always fetch fresh)
  - JavaScript/CSS: max-age=31536000 (1 year, immutable with versioning)
  - Images: max-age=2592000 (30 days)
  - Ticket PDFs: max-age=86400 (1 day, time-sensitive)
- **Compression:** Enable gzip/brotli for text content
- **Security:**
  - HTTPS only (redirect HTTP to HTTPS)
  - WAF attached for DDoS/bot protection
  - Signed URLs for time-limited ticket access

### WAF (Web Application Firewall)
- **Rules:**
  - OWASP Top 10 protection (SQL injection, XSS, CSRF)
  - Rate limiting: 10 requests/second per user (authenticated), 1000 req/s per IP (global)
  - Bot protection: Challenge suspicious requests (high request velocity from single IP)
  - Geographic blocking: Block traffic from high-risk jurisdictions (if applicable)
  - Custom rules:
    - Block requests with suspicious User-Agent
    - Block requests with excessive POST data (likely bot attack)
    - Challenge requests during peak traffic (onsale events)
- **CAPTCHA:** Enable for high-demand onsales
  - reCAPTCHA v3 challenge for requests exceeding rate limit
  - Separates legitimate users from bots

---

## Layer 3: API Gateway and Load Balancing

### Kong API Gateway
- **Deployment:** EKS pods (horizontal auto-scaling)
- **Replicas:** 3-10 pods (scaled based on traffic)
- **Rate Limiting:** Kong rate-limiting plugin
  - Per-user limit: 10 req/s (authenticated)
  - Per-IP limit: 1000 req/s (global limit, prevents DDoS)
  - Per-endpoint limit: Custom limits for expensive operations
    - Search: 20 req/s per user (read-heavy, acceptable)
    - Checkout: 2 req/s per user (write-heavy, limited)
- **Authentication:** 
  - JWT token validation
  - OAuth 2.0 for third-party integrations
  - API key for mobile apps
- **Request Routing:**
  - `/events/*` → EventService
  - `/tickets/*` → TicketService
  - `/orders/*` → OrderService
  - `/payments/*` → PaymentService
  - `/search/*` → Elasticsearch (via search proxy)
  - `/check-in/*` → CheckInService
- **Request Transformation:**
  - Add request ID header (for tracing)
  - Add auth context (user ID, scopes)
  - Log all requests (rate, latency, errors)
- **Circuit Breaker:** Detect downstream service failure, return 503
- **Caching:** Cache GET responses (5-60 minutes depending on endpoint)
  - Event listing: 5-minute cache
  - Ticket availability: 30-second cache
  - User profile: 1-hour cache
- **Load Balancing:** Round-robin across Kong pods

### ALB (Application Load Balancer)
- **Deployment:** AWS managed service
- **Listeners:**
  - Port 80 (HTTP): Redirect to HTTPS
  - Port 443 (HTTPS): TLS termination
- **Target Group:** Kong pods in EKS
- **Health Check:**
  - Path: `/health`
  - Interval: 30 seconds
  - Healthy threshold: 2 (min healthy targets to be considered healthy)
  - Unhealthy threshold: 3 (max unhealthy targets before marking down)
- **Sticky Sessions:** Disabled (stateless API)
- **Access Logs:** Send to S3 for analysis

---

## Layer 4: Microservices (EKS Deployment)

All microservices run on AWS EKS (Managed Kubernetes). Each service has horizontal auto-scaling based on CPU/memory.

### EventService
- **Responsibility:** Event creation, updating, publishing
- **API Endpoints:**
  - `GET /events` - List events with pagination/filtering
  - `POST /events` - Create new event (organizers only)
  - `GET /events/{id}` - Get event details
  - `PUT /events/{id}` - Update event (organizers only)
  - `DELETE /events/{id}` - Delete event
  - `GET /events/{id}/venue` - Get venue seating map
- **Database:** PostgreSQL (RDS Aurora)
- **Cache:** Redis (event details, seating maps)
- **Auto-scaling:** HPA (Horizontal Pod Autoscaler)
  - Min replicas: 2
  - Max replicas: 20
  - Scale up: CPU > 70%
  - Scale down: CPU < 30% for 5 minutes
- **Deployment:** Blue-green (zero-downtime deployments)

### InventoryService
- **Responsibility:** Ticket holds, seat availability, dynamic pricing
- **API Endpoints:**
  - `POST /holds` - Create ticket hold (reserve tickets for 10 minutes)
  - `GET /holds/{id}` - Get hold status
  - `DELETE /holds/{id}` - Release hold (cancel reservation)
  - `POST /holds/{id}/convert` - Convert hold to order (purchase)
  - `GET /seats` - Get available seats for event
  - `GET /pricing` - Get current ticket pricing (dynamic)
- **Database:** PostgreSQL (for persistent state)
- **Cache:** Redis Cluster (holds, seat maps, pricing)
  - Ticket holds: stored with 10-minute TTL
  - Seat availability: cached with 30-second TTL
  - Dynamic pricing: cached with 1-minute TTL
- **Critical Path:** All holds managed in Redis (fast, low-latency)
- **Persistence:** Holds synced to PostgreSQL asynchronously (eventual consistency)
- **Auto-scaling:** HPA based on ticket hold queue depth
  - Custom metric: hold_queue_depth
  - Min replicas: 3
  - Max replicas: 50 (during peak onsales)
  - Scale up: hold_queue_depth > 10K

### TicketService
- **Responsibility:** Ticket generation, QR codes, PDF, distribution
- **API Endpoints:**
  - `POST /tickets` - Generate ticket PDF (async, returns job ID)
  - `GET /tickets/{id}` - Get ticket details
  - `GET /tickets/{id}/pdf` - Download ticket PDF
  - `POST /tickets/{id}/validate` - Validate ticket QR code (check-in)
  - `GET /tickets/{id}/transfer` - Enable ticket transfer
- **Database:** PostgreSQL (ticket records)
- **Storage:** S3 (ticket PDFs, QR codes)
- **Processing:**
  - Ticket PDF generation: async (background job)
  - QR code generation: inline (fast)
  - File storage: upload to S3, return presigned URL (valid for 24 hours)
- **Auto-scaling:** HPA
  - Min replicas: 2
  - Max replicas: 10
  - Scale on CPU usage

### PaymentService
- **Responsibility:** Payment processing via Stripe
- **API Endpoints:**
  - `POST /payments` - Initiate payment (create Stripe payment intent)
  - `GET /payments/{id}` - Get payment status
  - `POST /payments/{id}/confirm` - Confirm payment (after customer authorization)
  - `POST /webhooks/stripe` - Webhook for payment status updates
- **Integration:** Stripe API
  - Uses Stripe Payment Intents API (most secure)
  - Handles 3D Secure authentication
  - Supports multiple payment methods (cards, Apple Pay, Google Pay)
- **Idempotency:** All requests include idempotency key
  - Prevents duplicate charges on retries
  - Stripe stores idempotency keys for 24 hours
- **Database:** PostgreSQL (payment records, transaction history)
- **Auto-scaling:** HPA
  - Min replicas: 3 (payment is critical)
  - Max replicas: 20
  - Scale on CPU/memory usage

### OrderService
- **Responsibility:** Order creation, order management, fulfillment
- **API Endpoints:**
  - `POST /orders` - Create order from hold (checkout)
  - `GET /orders/{id}` - Get order details
  - `GET /orders/my-orders` - List customer's orders
  - `POST /orders/{id}/cancel` - Cancel order (refund initiated)
- **Workflow:**
  1. Customer selects tickets (InventoryService creates hold)
  2. Customer enters payment info (PaymentService processes)
  3. OrderService creates order record
  4. OrderService publishes "order.created" event
  5. TicketService generates tickets (async)
  6. NotificationService sends confirmation email
- **Database:** PostgreSQL (order records)
- **Event Publishing:** Publishes to Kafka/SNS:
  - order.created
  - order.confirmed
  - order.cancelled
- **Auto-scaling:** HPA
  - Min replicas: 2
  - Max replicas: 15

### CheckInService
- **Responsibility:** Event check-in, QR code validation, attendance tracking
- **API Endpoints:**
  - `POST /check-in` - Scan ticket QR code, mark attendee
  - `GET /check-in/stats` - Get event attendance stats
  - `POST /check-in/offline-mode` - Support offline check-in (local database sync)
- **Database:** PostgreSQL (check-in records, offline cache)
- **Cache:** Redis (recent check-ins for deduplication)
  - QR code scanned in last 30 seconds: skip duplicate
- **Offline Mode:** Mobile app can check in without internet
  - Downloads QR code list before event
  - Syncs check-in records after event (or when internet available)
- **Auto-scaling:** HPA
  - Min replicas: 2
  - Max replicas: 10
  - During event: scale up (many check-ins happening)

### NotificationService
- **Responsibility:** Email, SMS, push notifications
- **Integration:** SNS (SMS), SES (email), mobile push (APNs/FCM)
- **Events Consumed from Kafka/SNS:**
  - order.created → Send order confirmation email
  - ticket.generated → Send ticket attached to email
  - order.cancelled → Send cancellation email with refund info
  - event.date_approaching → Send reminder SMS (1 day before)
- **Queue Processing:** Async processing with retry logic
  - Max retries: 3
  - Backoff: exponential (1s, 5s, 30s)
  - Dead letter queue: manually retry failed notifications
- **Rate limiting:** 100 notifications/second per customer
- **Auto-scaling:** HPA based on queue depth
  - Min replicas: 2
  - Max replicas: 10

---

## Layer 5: Data Layer

### PostgreSQL Database (RDS Aurora)
- **Instance Type:** db.r6g.2xlarge (production), db.t3.medium (dev/staging)
- **Storage:** Aurora storage (auto-scaling, max 128 TB)
- **Backup:** Automated daily backups, retained 35 days
- **High Availability:** Multi-AZ deployment (automatic failover in 30 seconds)
- **Read Replicas:** 2-3 replicas for read-heavy operations (reporting, analytics)
- **Databases:**
  - `events_db` - Events, venues, seating maps
  - `orders_db` - Orders, payments, transactions
  - `users_db` - Customer profiles, authentication
- **Connection Pooling:** PgBouncer on EKS (connection pool to prevent exhaustion)
- **Performance:**
  - p95 query latency: <50ms (tuning required for large datasets)
  - Connection pool size: 100-500 (depends on service density)
  - Slow query log: log queries >1 second, monitor and optimize

### Redis Cluster (ElastiCache)
- **Node Type:** cache.r6g.xlarge (production), cache.t3.small (dev)
- **Cluster Mode:** Enabled (horizontal scaling)
- **Nodes:** 6 shards, 2 replicas per shard (12 nodes total)
- **Multi-AZ:** Enabled (automatic failover if primary fails)
- **Data Structures:**
  - Strings: ticket holds (JSON serialized)
  - Sorted Sets: seat availability (score = seat number)
  - Hashes: pricing variants (event ID → pricing data)
  - Lists: event notifications queue
- **TTL Policy:**
  - Ticket holds: 10 minutes (evict after customer has reservation)
  - Seat maps: 30 seconds (reload frequently)
  - Session data: 1 hour
- **Persistence:** RDB snapshots (hourly), AOF disabled (prioritize speed)
- **Monitoring:** Track hit rate (>95% expected), eviction rate (<5%)

### Elasticsearch Cluster (for event search)
- **Deployment:** Amazon Elasticsearch Service
- **Instance Type:** t3.small (dev), r6g.xlarge (production)
- **Nodes:** 3 (minimum for production, ensures quorum)
- **Storage:** 100 GB (production), 10 GB (dev)
- **Indices:**
  - `events` - Event documents (indexed for full-text search)
- **Mapping:** Event fields indexed for search:
  - Event name (text, analyzer: standard)
  - Category (keyword)
  - Location (geo_point for geographic search)
  - Date (date)
  - Price range (numeric)
- **Queries Supported:**
  - Full-text search: event name, description
  - Filters: category, date range, price range, location (radius)
  - Aggregations: price histogram, category distribution
- **Refresh interval:** 30 seconds (balance between freshness and performance)
- **Replicas:** 1 replica (ensure availability if primary fails)

### S3 Buckets
- **Bucket 1: Event Assets**
  - Event images, videos, promotional materials
  - Versioning: enabled
  - Encryption: AES-256
  - Lifecycle: older versions deleted after 90 days
- **Bucket 2: Ticket PDFs**
  - Generated ticket PDF files
  - Encryption: AES-256
  - Lifecycle: delete after 90 days (tickets archived in database)
  - Presigned URLs: valid for 24 hours
- **Bucket 3: Application Code**
  - React app builds, deployed to CloudFront
  - Versioning: enabled
  - Lifecycle: keep latest 10 builds

---

## Layer 6: Asynchronous Processing

### SQS (Simple Queue Service)
- **Queue 1: Email Notifications**
  - Messages: order confirmations, ticket delivery, reminders
  - Batch size: 10 messages
  - Visibility timeout: 30 seconds
  - Retention: 4 days
  - DLQ: messages failing after 3 retries sent to DLQ
- **Queue 2: PDF Generation**
  - Messages: ticket PDF generation requests
  - Batch size: 5 messages
  - Workers: auto-scaling Lambda functions

### SNS (Simple Notification Service)
- **Topics:**
  - `OrderTopic` - Published when order created
  - `PaymentTopic` - Published when payment completed
  - `TicketTopic` - Published when ticket generated
  - `EventTopic` - Published when event updated
- **Subscriptions:**
  - OrderTopic → Email Service, Notification Service
  - PaymentTopic → Order Service, Accounting Service
  - TicketTopic → Email Service, Archive Service
  - EventTopic → Search Index Service, Cache Invalidation

### EventBridge
- **Rules:**
  - Event date approaches (1 day before): trigger reminder notifications
  - End-of-day batch (11:00 PM): trigger daily reporting job
  - Weekly sales report (Monday 8:00 AM): trigger analytics job
- **Targets:** Lambda functions, SQS queues, SNS topics

---

## Layer 7: Monitoring and Observability

### CloudWatch
- **Metrics:**
  - Application metrics: ticket hold queue depth, payment success rate, checkout duration
  - Infrastructure metrics: CPU, memory, network I/O per pod
  - API metrics: request rate, latency (p50/p95/p99), error rate
  - Database metrics: query latency, connection count, slow query log
- **Dashboards:**
  - Real-time traffic dashboard (requests/sec, error rate, latency)
  - Service health dashboard (uptime, error rate per service)
  - Business metrics dashboard (orders, revenue, refunds)
- **Alarms:**
  - High error rate (>1% for 5 minutes): page on-call
  - High latency (p95 >1 second for 10 minutes): investigate
  - High CPU (>80% for 10 minutes): consider scaling
  - Database connection pool exhaustion: immediate alert
  - Ticket hold queue depth (>50K): during onsale, expected; >100K: scale inventory service
- **Log Aggregation:**
  - CloudWatch Logs for all services
  - Log groups by service (EventService, TicketService, etc.)
  - Log retention: 30 days (production), 7 days (staging)
  - Log streaming: real-time to S3 for archival

### X-Ray
- **Tracing:** End-to-end request tracing across services
- **Sampling:** Sample 1% of requests in production, 10% in dev
- **Insights:** Identify bottlenecks, latency spikes
- **Service Map:** Visualize service dependencies and communication

---

## Layer 8: Scaling Strategy

### Horizontal Scaling (During Onsale Events)
- **Trigger:** Traffic spike detected (request rate >1000 req/s)
- **Scaling Sequence:**
  1. API Gateway (Kong): scale to 10 pods
  2. Inventory Service: scale to 50 pods (most critical for ticket holds)
  3. Order Service: scale to 15 pods
  4. Payment Service: scale to 20 pods
  5. Notification Service: scale to 10 pods
- **Time to Scale:** 2-5 minutes (HPA reacts to CPU/memory metrics)
- **Cost:** Auto-scaling maintains cost efficiency (scale down after onsale)

### Database Scaling
- **Aurora Auto-scaling:** Read replicas auto-add if CPU >70% (max 15 replicas)
- **Connection pooling:** Ensure connection pool doesn't exhaust (max 500 connections)
- **Query optimization:** Monitor slow queries, optimize (add indexes, rewrite)

### Cache Scaling
- **Redis Cluster:** Auto-scaling shards if memory >90% (max 500 GB)
- **Eviction policy:** allkeys-lru (evict least recently used keys)

---

## Traffic Flow During High-Demand Onsale

**Scenario: 100K concurrent users all trying to buy tickets**

1. **Request arrives** → CloudFront (geographically distributed)
2. **CDN cache hit?** → Return cached static assets (90% of requests are JS/CSS)
3. **API request** → Route to Kong API Gateway
4. **Rate limit check** → 1000 req/s per IP (bot protection)
5. **CAPTCHA challenge** (if suspicious) → User proves human, requests proceed
6. **Authenticated request** → JWT validation
7. **Route to service** → Based on endpoint
8. **Inventory Service** → Request ticket hold
9. **Redis lookup** → Check seat availability (cache hit)
10. **Create hold** → Store in Redis with 10-min TTL
11. **Return to user** → Hold reserved, user proceeds to payment
12. **Payment Service** → Process via Stripe
13. **Order Service** → Create order record
14. **Event published** → SNS/Kafka (order.created)
15. **Notification Service** → Queue email, SMS
16. **Ticket Service** → Async PDF generation
17. **Response to user** → "Order confirmed! Check your email."

**Metrics during peak:**
- Requests/sec: 50,000 (spike to 100,000)
- API latency: p95 < 500ms
- Error rate: <0.5%
- Ticket hold success rate: >99%
- Pod count: 150+ across all services
- Database connections: 400-500 (at limit of pool)
- Redis memory: 50 GB (30% of cluster capacity)

---

## Security Considerations

- **Network:** Kubernetes Network Policy restricts pod-to-pod communication
- **TLS:** All communication encrypted (in-transit)
- **Secrets Management:** AWS Secrets Manager for API keys, database passwords
- **IAM:** Pod roles restrict S3, SQS, database access (principle of least privilege)
- **Authentication:** JWT tokens (issued by auth service)
- **Authorization:** RBAC (role-based access control) for organizers/admin

---

## Disaster Recovery

- **RPO (Recovery Point Objective):** 1 hour (acceptable for non-financial critical data)
- **RTO (Recovery Time Objective):** 4 hours (restore service in case of region failure)
- **Backup Strategy:**
  - Database: automated daily backups, cross-region replication
  - Elasticsearch: snapshot daily
  - Application: container images in ECR, can redeploy within minutes
- **Failover:** Multi-region deployment (active-active) for future expansion

---

## Cost Optimization

- **Reserved instances:** For baseline load (80% of expected traffic)
- **Spot instances:** For auto-scaling burst capacity (30-40% cost savings)
- **Caching:** Reduce database queries by 80% via Redis (cost savings in Aurora)
- **CDN:** Offload static content delivery to CloudFront (lower ALB costs)
- **Right-sizing:** Monitor actual CPU/memory, adjust instance types quarterly

---

This architecture supports 100K concurrent users during onsale events with <500ms latency and >99% uptime. The emphasis on caching, horizontal scaling, and asynchronous processing ensures resilience and cost-effectiveness.
