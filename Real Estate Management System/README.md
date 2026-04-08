# Real Estate Management System

A comprehensive, production-grade platform for managing the full lifecycle of real estate operations — from property listing and tenant onboarding through lease management, rent collection, maintenance coordination, and owner financial reporting.

## Overview

The Real Estate Management System (REMS) serves property management companies, independent landlords, real estate agencies, and property owners who need a unified platform to manage residential, commercial, and mixed-use properties at scale. The system supports multi-tenancy, multi-currency operations, and integrates with industry-standard third-party services including Stripe for payments, Checkr/Experian for background checks, DocuSign for e-signatures, and major listing portals such as Zillow and Apartments.com.

### Target Audience

| Role | Primary Use Cases |
|------|-------------------|
| Property Manager | Property setup, listing management, tenant screening, lease administration, maintenance coordination |
| Tenant | Online applications, lease signing, rent payments, maintenance requests |
| Owner/Landlord | Portfolio overview, financial statements, occupancy reporting |
| Contractor | Work order management, photo documentation, invoice submission |
| System Administrator | User management, integrations, audit logs, compliance reporting |

## Key Features

### Property & Unit Management
- Multi-type property support: residential (single-family, multi-family, condo), commercial (office, retail, industrial), and mixed-use
- Hierarchical organization: Company → Agency → Property → Floor → Unit → Room
- Flexible amenity and feature tagging
- Occupancy tracking with vacancy rate analytics
- Bulk property import via CSV/API

### Online Listing & Marketing
- Rich listing creation with photo management (CDN-backed, multi-angle uploads)
- Automated syndication to Zillow, Apartments.com, and Trulia
- Pricing history tracking with market comparison
- Listing lifecycle management (draft, active, under application, rented, inactive)

### Tenant Application & Screening
- Online application portal with document upload
- Integrated background check via Checkr API
- Credit check integration via Experian
- Multi-applicant household applications
- Automated approval scoring with configurable thresholds
- Fair Housing Act compliance controls

### Lease Creation & Digital Signing
- Template-based lease generation with custom clause support
- DocuSign integration for legally binding e-signatures
- Lease versioning and amendment tracking
- Auto-renewal workflows with configurable notice periods
- Lease termination with prorated rent calculation

### Rent & Payment Management
- Automated monthly rent invoice generation
- Online payment collection: ACH, credit/debit card via Stripe
- Late fee calculation with configurable grace periods (jurisdictional)
- Security deposit collection, holding, and itemized refund processing
- Partial payment handling and payment plan support
- NSF/returned payment processing

### Maintenance Management
- Tenant-facing maintenance request portal (web and mobile)
- Priority classification: Emergency, Urgent, Routine, Preventive
- Contractor assignment and scheduling
- Work order tracking with photo documentation
- Contractor invoice management and payment
- Maintenance history per unit

### Property Inspections
- Digital inspection checklists per property type
- Move-in, move-out, mid-lease, and periodic inspection support
- Photo evidence capture per inspection item
- Automated reports with issue flagging
- Integration with security deposit deduction workflow

### Owner Portal & Reporting
- Real-time occupancy and revenue dashboards
- Monthly/quarterly owner financial statements
- Maintenance expense summaries per property
- Year-end tax reports (1099-MISC for contractors)
- Equity and ROI analysis

### Utility Billing
- Utility account tracking per unit (electricity, water, gas, internet)
- Sub-meter reading ingestion and bill-back calculation
- Utility records reconciliation

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API Gateway | Kong / AWS API Gateway |
| Backend Services | Node.js 20 (TypeScript) with NestJS |
| Database | PostgreSQL 16 with read replicas |
| Cache | Redis 7.2 |
| Message Broker | Apache Kafka 3.6 |
| Object Storage | AWS S3 with CloudFront CDN |
| Search | Elasticsearch 8 |
| Container Orchestration | Kubernetes (EKS) |
| CI/CD | GitHub Actions + ArgoCD |
| Observability | Prometheus, Grafana, OpenTelemetry, Datadog |
| Payments | Stripe (cards + ACH) |
| E-Signatures | DocuSign eSignature API |
| Background Checks | Checkr API |
| Credit Checks | Experian Connect API |
| Email/SMS | SendGrid + Twilio |
| Accounting Export | QuickBooks Online API |

## Documentation Structure

Project root artifact: [`traceability-matrix.md`](./traceability-matrix.md) provides cross-phase requirement-to-implementation linkage.


```
Real Estate Management System/
├── README.md                          ← This file
├── traceability-matrix.md
├── requirements/
│   ├── requirements-document.md       ← Functional & non-functional requirements (FR-01–FR-55+, NFR-01–NFR-22)
│   └── user-stories.md                ← 45+ user stories with acceptance criteria
├── analysis/
│   ├── use-case-diagram.md            ← Mermaid actor/use-case diagrams
│   ├── use-case-descriptions.md       ← Detailed UC-01 through UC-08 descriptions
│   ├── system-context-diagram.md      ← C4 context with all external integrations
│   ├── activity-diagram.md            ← Process flow diagrams
│   ├── bpmn-swimlane-diagram.md       ← BPMN swimlane process diagrams
│   ├── data-dictionary.md             ← Entity definitions, ER diagram, data quality rules
│   ├── business-rules.md              ← BR-01–BR-20 enforceable rules with evaluation pipeline
│   └── event-catalog.md               ← Domain events, producers, consumers, SLOs
├── high-level-design/
│   ├── system-sequence-diagram.md     ← End-to-end sequence diagrams
│   ├── domain-model.md                ← Domain entity relationships
│   ├── data-flow-diagram.md           ← Data flow across services
│   ├── architecture-diagram.md        ← Microservices architecture
│   └── c4-context-container.md        ← C4 context and container diagrams
├── detailed-design/
│   ├── class-diagram.md               ← Full class definitions with attributes and methods
│   ├── sequence-diagram.md            ← Detailed interaction sequences
│   ├── state-machine-diagram.md       ← State machines for Lease, Application, Unit, Maintenance
│   ├── erd-database-schema.md         ← Full SQL DDL with all tables
│   ├── component-diagram.md           ← Component breakdown per service
│   ├── api-design.md                  ← REST API spec with request/response schemas
│   └── c4-component.md                ← C4 component drill-down diagrams
├── infrastructure/
│   ├── deployment-diagram.md          ← Kubernetes deployment topology
│   ├── network-infrastructure.md      ← VPC, subnets, security groups
│   └── cloud-architecture.md          ← Full AWS production architecture
├── implementation/
│   ├── code-guidelines.md             ← Coding standards, security practices, folder structure
│   ├── c4-code-diagram.md             ← Code-level C4 diagrams
│   └── implementation-playbook.md     ← Phased rollout plan, migration strategy
└── edge-cases/
    ├── README.md                      ← Risk matrix and priority classification
    ├── property-listings.md           ← Listing failures and syndication edge cases
    ├── tenant-management.md           ← Screening and PII edge cases
    ├── lease-lifecycle.md             ← DocuSign, proration, renewal edge cases
    ├── maintenance-requests.md        ← Emergency, contractor, and workflow edge cases
    ├── api-and-ui.md                  ← Webhook, offline, and bulk operation edge cases
    ├── security-and-compliance.md     ← Fair Housing, GDPR, PCI DSS edge cases
    └── operations.md                  ← Infrastructure and batch job edge cases
```

## Getting Started

- Review [`traceability-matrix.md`](./traceability-matrix.md) first to navigate requirement-to-implementation coverage across phases.
### Prerequisites
- Node.js 20+, Docker Desktop, PostgreSQL 16, Redis 7.2
- AWS CLI v2 configured with appropriate IAM permissions
- Kubernetes cluster (local: minikube or kind for development)

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/your-org/real-estate-management-system.git
cd real-estate-management-system

# Install dependencies (monorepo with Turborepo)
npm install

# Copy environment templates
cp .env.example .env.local
# Edit .env.local with your API keys (Stripe, DocuSign, Checkr, Experian)

# Start infrastructure services
docker compose up -d postgres redis kafka zookeeper elasticsearch

# Run database migrations
npm run db:migrate

# Seed development data
npm run db:seed

# Start all microservices
npm run dev
```

### Service Endpoints (Development)
| Service | Port | URL |
|---------|------|-----|
| API Gateway | 3000 | http://localhost:3000 |
| Property Service | 3001 | http://localhost:3001 |
| Tenant Service | 3002 | http://localhost:3002 |
| Lease Service | 3003 | http://localhost:3003 |
| Payment Service | 3004 | http://localhost:3004 |
| Maintenance Service | 3005 | http://localhost:3005 |
| Inspection Service | 3006 | http://localhost:3006 |
| Reporting Service | 3007 | http://localhost:3007 |
| Notification Service | 3008 | http://localhost:3008 |
| Document Service | 3009 | http://localhost:3009 |

### Running Tests
```bash
npm run test              # Unit tests across all services
npm run test:integration  # Integration tests (requires running infrastructure)
npm run test:e2e          # End-to-end tests
npm run test:coverage     # Coverage report
```

## Documentation Status

- ✅ Traceability coverage is available via [`traceability-matrix.md`](./traceability-matrix.md).
| Document | Status | Last Updated | Owner |
|----------|--------|-------------|-------|
| Requirements Document | ✅ Complete | 2025-01 | Product Team |
| User Stories | ✅ Complete | 2025-01 | Product Team |
| Use Case Diagrams | ✅ Complete | 2025-01 | Architecture Team |
| Use Case Descriptions | ✅ Complete | 2025-01 | Architecture Team |
| System Context Diagram | ✅ Complete | 2025-01 | Architecture Team |
| Activity Diagrams | ✅ Complete | 2025-01 | Architecture Team |
| BPMN Swimlane Diagrams | ✅ Complete | 2025-01 | Architecture Team |
| Data Dictionary | ✅ Complete | 2025-01 | Data Team |
| Business Rules | ✅ Complete | 2025-01 | Product + Legal |
| Event Catalog | ✅ Complete | 2025-01 | Platform Team |
| System Sequence Diagram | ✅ Complete | 2025-01 | Architecture Team |
| Domain Model | ✅ Complete | 2025-01 | Architecture Team |
| Data Flow Diagram | ✅ Complete | 2025-01 | Architecture Team |
| Architecture Diagram | ✅ Complete | 2025-01 | Infrastructure Team |
| C4 Context & Container | ✅ Complete | 2025-01 | Architecture Team |
| Class Diagram | ✅ Complete | 2025-01 | Engineering Team |
| Sequence Diagram | ✅ Complete | 2025-01 | Engineering Team |
| State Machine Diagram | ✅ Complete | 2025-01 | Engineering Team |
| ERD & Database Schema | ✅ Complete | 2025-01 | Data Team |
| Component Diagram | ✅ Complete | 2025-01 | Engineering Team |
| API Design | ✅ Complete | 2025-01 | API Team |
| C4 Component Diagram | ✅ Complete | 2025-01 | Architecture Team |
| Deployment Diagram | ✅ Complete | 2025-01 | DevOps Team |
| Network Infrastructure | ✅ Complete | 2025-01 | DevOps Team |
| Cloud Architecture | ✅ Complete | 2025-01 | DevOps Team |
| Code Guidelines | ✅ Complete | 2025-01 | Engineering Team |
| C4 Code Diagram | ✅ Complete | 2025-01 | Engineering Team |
| Implementation Playbook | ✅ Complete | 2025-01 | Engineering Team |
| Edge Cases: Overview | ✅ Complete | 2025-01 | QA Team |
| Edge Cases: Property Listings | ✅ Complete | 2025-01 | QA Team |
| Edge Cases: Tenant Management | ✅ Complete | 2025-01 | QA Team |
| Edge Cases: Lease Lifecycle | ✅ Complete | 2025-01 | QA Team |
| Edge Cases: Maintenance | ✅ Complete | 2025-01 | QA Team |
| Edge Cases: API & UI | ✅ Complete | 2025-01 | QA Team |
| Edge Cases: Security & Compliance | ✅ Complete | 2025-01 | QA + Legal |
| Edge Cases: Operations | ✅ Complete | 2025-01 | DevOps + QA |

## Contributing

See `implementation/code-guidelines.md` for coding standards, branch naming conventions, and PR requirements. All changes must pass the CI pipeline including unit tests, integration tests, and the documentation validation gate.

## License

Proprietary — All rights reserved. Real Estate Management System is internal commercial software.
