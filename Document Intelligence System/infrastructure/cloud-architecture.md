# Cloud Architecture - Document Intelligence System

## AWS Architecture

```mermaid
graph TB
    subgraph "AWS Cloud"
        subgraph "Compute"
            ECS[ECS Fargate<br/>API Servers]
            EC2[EC2 GPU<br/>Workers]
        end
        
        subgraph "AI Services"
            TEXTRACT[AWS Textract<br/>OCR]
            COMPREHEND[Amazon Comprehend<br/>NER Optional]
        end
        
        subgraph "Data"
            RDS[(RDS PostgreSQL)]
            S3[S3 Buckets<br/>Documents]
            SQS[SQS<br/>Job Queue]
            ELASTICACHE[(ElastiCache)]
        end
        
        subgraph "Monitoring"
            CLOUDWATCH[CloudWatch]
        end
    end
    
    ALB[Application LB] --> ECS
    ECS --> S3
    ECS --> RDS
    ECS --> SQS
    
    SQS --> EC2
    EC2 --> TEXTRACT
    EC2 --> RDS
    EC2 --> S3
```

## GCP Architecture

```mermaid
graph TB
    subgraph "Google Cloud"
        subgraph "Compute"
            GKE[GKE<br/>Kubernetes]
            COMPUTE[Compute Engine<br/>GPU Nodes]
        end
        
        subgraph "AI Services"
            VISION[Vision AI<br/>OCR]
            NL[Natural Language AI<br/>NER Optional]
        end
        
        subgraph "Data"
            CLOUD_SQL[(Cloud SQL)]
            GCS[Cloud Storage]
            PUB_SUB[Pub/Sub]
        end
    end
    
    LB[Cloud Load Balancing] --> GKE
    GKE --> GCS
    GKE --> CLOUD_SQL
    GKE --> PUB_SUB
    
    PUB_SUB --> COMPUTE
    COMPUTE --> VISION
    COMPUTE --> GCS
```

## Provider Mapping

| Component | AWS | GCP | Azure |
|-----------|-----|-----|-------|
| Container Runtime | ECS/EKS | GKE | AKS |
| OCR Service | Textract | Vision AI | Form Recognizer |
| NER (Optional) | Comprehend | Natural Language AI | Text Analytics |
| GPU Compute | EC2 P3/G4 | Compute Engine GPU | NC-series VMs |
| Database | RDS PostgreSQL | Cloud SQL | Azure PostgreSQL |
| Storage | S3 | Cloud Storage | Blob Storage |
| Queue | SQS | Pub/Sub | Service Bus |
| Cache | ElastiCache | Memorystore | Azure Cache |

## Cost Estimation (AWS)

| Tier | Monthly Cost | Specs |
|------|--------------|-------|
| **Starter** | ~$800 | API: t3.medium x2, Workers: CPU-only, Textract API |
| **Growth** | ~$2500 | Auto-scaling, g4dn.xlarge GPU x2, RDS Multi-AZ |
| **Enterprise** | ~$8000+ | Multi-region, p3.2xlarge GPU x4, HA |

**Key Cost Drivers**:
- GPU instances for AI models
- Cloud OCR API usage (pay per page)
- Document storage (S3)
- Data transfer (outbound)
