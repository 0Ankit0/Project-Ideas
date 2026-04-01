# Network Infrastructure and Security Architecture

This document details the network infrastructure, security groups, and DDoS protection for the Event Ticketing Platform deployed on AWS.

---

## VPC Design

The platform runs in a single VPC (Virtual Private Cloud) with three subnet tiers: public, private, and data. This design provides security isolation while maintaining performance.

### VPC Configuration
- **CIDR Block:** 10.0.0.0/16 (65K addresses)
- **Availability Zones:** 3 (us-east-1a, us-east-1b, us-east-1c)
- **DNS Hostname:** Enabled
- **DNS Resolution:** Enabled

---

## Subnet Tiers

### Public Subnet (NAT Gateway, ALB)
- **CIDR Blocks:**
  - AZ-1a: 10.0.1.0/24 (256 addresses)
  - AZ-1b: 10.0.2.0/24 (256 addresses)
  - AZ-1c: 10.0.3.0/24 (256 addresses)
- **Route Table:**
  - Local traffic: 10.0.0.0/16 → Local
  - Internet traffic: 0.0.0.0/0 → Internet Gateway
- **Resources:**
  - Application Load Balancer (ALB)
  - NAT Gateway (one per AZ for HA)
- **Auto-assigned Public IP:** Enabled (hosts get public IPs)
- **Security:** Accessed only by load balancer traffic (port 443 from internet)

### Private Subnet (EKS Worker Nodes)
- **CIDR Blocks:**
  - AZ-1a: 10.0.11.0/24 (256 addresses)
  - AZ-1b: 10.0.12.0/24 (256 addresses)
  - AZ-1c: 10.0.13.0/24 (256 addresses)
- **Route Table:**
  - Local traffic: 10.0.0.0/16 → Local
  - Internet traffic: 0.0.0.0/0 → NAT Gateway (from corresponding AZ)
- **Resources:**
  - EKS worker nodes (EC2 instances)
  - Kubernetes pods (microservices)
- **Auto-assigned Public IP:** Disabled (no direct internet access)
- **Outbound Traffic:** Routes through NAT Gateway in public subnet
- **Security:** Isolated from direct internet access

### Data Subnet (RDS, Elasticsearch, ElastiCache)
- **CIDR Blocks:**
  - AZ-1a: 10.0.21.0/24 (256 addresses)
  - AZ-1b: 10.0.22.0/24 (256 addresses)
  - AZ-1c: 10.0.23.0/24 (256 addresses)
- **Route Table:**
  - Local traffic: 10.0.0.0/16 → Local
  - No internet route (no internet access)
- **Resources:**
  - RDS Aurora database (primary + replicas)
  - Elasticsearch cluster
  - ElastiCache Redis cluster
- **Auto-assigned Public IP:** Disabled
- **Security:** No internet access, accessible only from private subnet (EKS)

---

## Network Address Translation (NAT)

### NAT Gateway
- **Deployment:** One per AZ (3 total) in public subnets
- **Elastic IP:** One per NAT Gateway
- **Purpose:** Allow outbound internet traffic from private/data subnets
- **High Availability:** Automatic failover within AZ (if gateway fails, AWS creates replacement)
- **Cross-AZ Failover:** Each AZ's private subnet uses its own NAT (not cross-AZ)
- **Cost:** $32/month per gateway + data transfer charges

### NAT Behavior
- **Outbound:** Private subnet traffic (EKS) exiting to internet routes through NAT
  - Source IP: EKS pod IP → destination IP: NAT Gateway elastic IP
  - Allows outbound connections (API calls to Stripe, etc.)
  - Inbound unsolicited traffic: blocked (stateless-like behavior)
- **Inbound:** Traffic initiated from internet cannot reach private subnets
  - Ensures EKS pods not directly exposed to internet

---

## Security Groups (Layer 4 - Transport)

Security groups act as virtual firewalls, controlling inbound/outbound traffic by protocol and port.

### SG-ALB (Application Load Balancer)
- **Inbound Rules:**
  - Port 80/TCP (HTTP): from 0.0.0.0/0
    - Redirect to HTTPS
  - Port 443/TCP (HTTPS): from 0.0.0.0/0(Cloudflare IPs if using Cloudflare)
    - TLS termination
    - Rate limiting by WAF
- **Outbound Rules:**
  - Port 8080/TCP to SG-Kong (EKS pods)
  - Port 443/TCP to internet (for health checks, outbound APIs)
- **Purpose:** Accept internet traffic, forward to Kong API Gateway

### SG-Kong (API Gateway)
- **Inbound Rules:**
  - Port 8080/TCP: from SG-ALB
    - API Gateway receives requests from ALB
  - Port 8081/TCP: from SG-EKS (internal health checks)
    - Health check port
- **Outbound Rules:**
  - Port 5432/TCP to SG-RDS (PostgreSQL)
  - Port 6379/TCP to SG-Redis (Redis)
  - Port 9200/TCP to SG-Elasticsearch (Elasticsearch)
  - Port 443/TCP to internet (external API calls: Stripe, etc.)
- **Purpose:** API gateway pod security

### SG-EKS (Kubernetes Worker Nodes)
- **Inbound Rules:**
  - Port 10250/TCP: from SG-EKS (kubelet API, pod-to-pod communication)
    - Allows inter-pod communication
  - Port 8080/TCP: from SG-ALB (traffic from load balancer)
  - Port 443/TCP: from SG-EKS (internal HTTPS communication)
  - Port 53/TCP,UDP: from SG-EKS (DNS queries between pods)
  - Port 30000-32767/TCP: from SG-ALB (NodePort services, if using them)
- **Outbound Rules:**
  - Port 443/TCP to internet (pull container images from ECR, external APIs)
  - Port 5432/TCP to SG-RDS (database access)
  - Port 6379/TCP to SG-Redis (cache access)
  - Port 9200/TCP to SG-Elasticsearch (search access)
  - Port 53/UDP to internet (DNS resolution)
- **Purpose:** Control pod-to-pod and pod-to-service communication

### SG-RDS (PostgreSQL Database)
- **Inbound Rules:**
  - Port 5432/TCP: from SG-EKS (application pods)
  - Port 5432/TCP: from SG-DataServices (if using separate data service cluster)
- **Outbound Rules:**
  - None (databases don't typically initiate outbound connections)
- **Purpose:** Restrict database access to application layer only

### SG-Redis (ElastiCache)
- **Inbound Rules:**
  - Port 6379/TCP: from SG-EKS (application pods)
  - Port 6380/TCP: from SG-EKS (cluster mode enabled)
- **Outbound Rules:**
  - None
- **Purpose:** Restrict Redis access to application layer

### SG-Elasticsearch (Search Engine)
- **Inbound Rules:**
  - Port 9200/TCP: from SG-EKS (application pods)
  - Port 9300/TCP: from SG-Elasticsearch (cluster communication)
- **Outbound Rules:**
  - None
- **Purpose:** Restrict Elasticsearch access

---

## Network Policies (Layer 3 - Kubernetes)

Kubernetes Network Policies provide fine-grained pod-to-pod communication control.

### Deny All Ingress (Default Deny)
```
All pods: Deny all inbound traffic by default
Exception: Explicitly allow specific sources
```

### Allow ALB → Kong
```
Kong pods accept traffic from ALB (ingress controller)
Port: 8080
Protocol: TCP
```

### Allow Kong → Microservices
```
Kong routes traffic to:
- EventService: port 3000
- InventoryService: port 3001
- TicketService: port 3002
- PaymentService: port 3003
- OrderService: port 3004
- CheckInService: port 3005
- NotificationService: port 3006
```

### Allow Microservices → Data Services
```
EventService → RDS (port 5432)
InventoryService → RDS + Redis (port 5432, 6379)
PaymentService → RDS (port 5432)
OrderService → RDS (port 5432)
TicketService → RDS + S3 (port 5432, 443)
```

### Allow Inter-Service Communication
```
OrderService → InventoryService (port 3001, for hold conversion)
OrderService → PaymentService (port 3003, for payment status)
TicketService → OrderService (port 3004, for order details)
```

---

## DDoS Protection Strategy

### Layer 3/4 Protection (Network-Level)

#### AWS Shield Standard (Free)
- **Automatic Protection:**
  - Protects against most common DDoS attacks
  - Volumetric attacks (UDP floods, DNS amplification)
  - Protocol attacks (SYN floods, Ping of death)
  - Application layer attacks (HTTP floods, partial requests)
- **Limitation:** Limited to passive protection, no active rate limiting

#### AWS Shield Advanced ($3K/month)
- **Enhanced Protection:**
  - DDoS Response Team (DRT) support
  - Financial guarantee (refund for DDoS-related cost spikes)
  - Advanced attack analytics
- **Consideration:** For ticketing, may be justified during major onsales

#### AWS WAF (Web Application Firewall)
- **Integration:** Attached to CloudFront and ALB
- **Rules:**

  1. **Rate Limiting** (Layer 7)
     - Per-IP rate limit: 1000 requests per 5 minutes (excessive = DDoS)
     - Per-user rate limit: 100 requests per minute (authenticated)
     - Endpoint-specific: `/search` 500 req/min, `/checkout` 50 req/min
     - Action: Block with HTTP 429 (Too Many Requests)

  2. **AWS Managed Rule Groups**
     - SQLi Protection: block requests with SQL injection patterns
     - XSS Protection: block requests with XSS payloads
     - Bot Control: identify and block suspicious bots
     - Common Rule Set: OWASP Top 10 coverage

  3. **Geographic Blocking** (if applicable)
     - Whitelist: allow only traffic from expected countries (US, EU, etc.)
     - Blacklist: block traffic from high-risk countries

  4. **Signature-based Detection**
     - Detect large request bodies (likely exploit attempt)
     - Detect HTTP methods (block unusual methods like CONNECT)
     - Detect User-Agent (block bad bots)

  5. **Captcha Challenge** (during peak load)
     - Trigger: request rate > 500 req/s from single IP
     - Challenge: reCAPTCHA v3 (invisible, user doesn't notice)
     - Action: require CAPTCHA proof before serving requests
     - Effectiveness: blocks bot traffic, allows legitimate users

### Layer 7 Protection (Application-Level)

#### Kong Rate Limiting Plugin
- **Per-User Limit:** 10 requests/second (authenticated users)
- **Per-IP Limit:** 1000 requests/second (unauthenticated)
- **Per-Endpoint Limit:**
  - `/search`: 20 req/s (read-heavy, acceptable)
  - `/checkout`: 2 req/s (write-heavy, limited)
  - `/payments`: 1 req/s (critical, strictly limited)
- **Action on Breach:** Return HTTP 429 with Retry-After header

#### Circuit Breaker (Kong)
- **Purpose:** Prevent cascading failures
- **Trigger:** If downstream service fails >10 times in 30 seconds
- **Action:** Stop routing requests, return HTTP 503 from Kong
- **Recovery:** Gradually re-enable (send 50% of traffic, then 100%)

#### Request Validation
- **Content-Type Validation:** Only accept application/json
- **Content-Length Limit:** 1 MB max (prevent buffer overflow)
- **Field Validation:** Validate JSON fields (type, length, range)

### Botnet and Scalper Protection

#### CAPTCHA During Onsales
- **Trigger:** Traffic spike detected (request rate > 1000 req/s)
- **Challenge:** reCAPTCHA v3 (invisible)
- **Effectiveness:** ~95% bot traffic blocked
- **User Impact:** Minimal (fast, invisible for legitimate users)

#### Device Fingerprinting
- **Browser Fingerprinting:** Track browser characteristics (user agent, canvas fingerprint)
- **Purpose:** Detect bots using same fingerprint from different IPs
- **Action:** Challenge suspicious fingerprints

#### Queue System (Virtual Waiting Room)
- **High-Demand Events:** During peak, route customers to waiting room
- **Queue Position:** Show estimated wait time
- **Fair Access:** Serve customers FIFO (not random)
- **Prevention:** Prevents concurrent requests from single user (bot behavior)

---

## CDN Configuration (CloudFront)

### Origin Configuration
- **Origin 1: S3 (Static Assets)**
  - Origin domain: `myapp-static.s3.amazonaws.com`
  - Protocol: HTTPS only
  - Origin access identity (OAI): restricts direct S3 access
- **Origin 2: ALB (API Requests)**
  - Origin domain: `api.ticketing.example.com`
  - Protocol: HTTPS
  - Origin path: `/api` (route API traffic here)

### Caching Rules

| Path Pattern | TTL | Cache Policy |
|---|---|---|
| `/index.html` | 0 (no-cache) | Always fetch fresh |
| `/static/js/*.js` | 31536000 (1 year) | Cache forever (versioned filenames) |
| `/static/css/*.css` | 31536000 | Cache forever |
| `/static/images/*` | 2592000 (30 days) | Long cache |
| `/api/*` | 0 (no-cache) | Always fetch fresh (dynamic) |
| `/api/events` | 300 (5 min) | Cache list (eventual consistency) |
| `/tickets/pdf/*` | 86400 (1 day) | Cache PDF short-term |

### Security Headers
```
Strict-Transport-Security: max-age=31536000 (enforce HTTPS)
X-Content-Type-Options: nosniff (prevent MIME type sniffing)
X-Frame-Options: DENY (prevent clickjacking)
X-XSS-Protection: 1; mode=block (legacy XSS protection)
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' (prevent inline script injection)
```

### Compression
- **Gzip:** Enable for text content (HTML, JSON, JavaScript, CSS)
- **Brotli:** Enable for browsers supporting it (smaller compression)
- **Compression Ratio:** ~70% reduction for text (3 MB → 900 KB)

### Access Logs
- **S3 Destination:** `cloudfront-logs-bucket`
- **Prefix:** `logs/` (organized by date)
- **Retention:** 90 days
- **Analysis:** Identify traffic patterns, attack vectors

---

## NAT Gateway and Egress Control

### Egress IP Whitelisting (for Stripe, etc.)
- **Stripe IP Whitelist:** Configure to accept requests from NAT Gateway elastic IPs
- **Known IPs:** NAT Gateway provides static IPs (can be whitelisted)
- **Benefits:** Allows Stripe to whitelist banking platform IPs

### Egress Monitoring
- **CloudWatch:** Track outbound data from NAT
- **Alert:** Unusual egress (potential data exfiltration)
- **Cost:** Charge for data transfer through NAT (typical: $0.045/GB)

---

## Compliance and Audit

### Network Documentation
- **VPC Diagram:** Document subnets, routes, security groups
- **Traffic Flow:** Document communication between services
- **Audit Trail:** Log all security group changes

### Compliance Standards
- **PCI-DSS (Payment Card Industry):**
  - Network segmentation: payment services isolated from other services
  - Firewall rules: restrict access to payment systems
  - Encryption: TLS for data in transit
- **GDPR (if applicable):**
  - Data residency: ensure data stays in compliant region
  - Encryption: encrypt customer data at rest

---

## Cost Optimization

- **NAT Gateway:** Most expensive component ($32/month each + egress charges)
  - Alternative: NAT Instance (cheaper but more management)
  - VPC Endpoint for S3: free, reduces NAT traffic
- **Data Transfer:** Charge $0.02 per GB out of VPC
  - Optimize: cache at CloudFront, reduce API calls
- **Security Groups:** No cost (management task)

---

This network architecture provides security isolation, high availability, and DDoS protection suitable for a ticketing platform handling 100K+ concurrent users.
