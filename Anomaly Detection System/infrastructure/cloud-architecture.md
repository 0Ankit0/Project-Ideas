# Cloud Architecture - Anomaly Detection System

## AWS Architecture

```mermaid
graph TB
    subgraph "AWS Cloud"
        subgraph "Stream Processing"
            MSK[Amazon MSK<br/>Managed Kafka]
            KINESIS[Kinesis Data<br/>Analytics]
        end
        
        subgraph "Compute"
            EKS[EKS<br/>Kubernetes]
            EC2_GPU[EC2 p3/g4<br/>GPU Instances]
        end
        
        subgraph "ML"
            SAGEMAKER[SageMaker<br/>Training]
            ECR[ECR<br/>Container Registry]
        end
        
        subgraph "Data"
            TIMESTREAM[(Timestream<br/>Time-Series)]
            RDS[(RDS PostgreSQL)]
            ELASTICACHE[(ElastiCache)]
        end
        
        subgraph "Monitoring"
            CLOUDWATCH[CloudWatch]
            SNS[SNS<br/>Alerts]
        end
    end
    
    MSK --> KINESIS
    KINESIS --> EC2_GPU
    EC2_GPU --> TIMESTREAM
    EC2_GPU --> SNS
    SAGEMAKER --> ECR
```

## GCP Architecture

```mermaid
graph TB
    subgraph "Google Cloud"
        subgraph "Stream Processing"
            PUBSUB[Pub/Sub]
            DATAFLOW[Dataflow]
        end
        
        subgraph "Compute"
            GKE[GKE<br/>Kubernetes]
            COMPUTE_GPU[Compute Engine<br/>GPU]
        end
        
        subgraph "ML"
            VERTEX[Vertex AI]
            ARTIFACT[Artifact Registry]
        end
        
        subgraph "Data"
            BIGTABLE[(Bigtable<br/>Time-Series)]
            CLOUD_SQL[(Cloud SQL)]
            MEMORYSTORE[(Memorystore)]
        end
    end
    
    PUBSUB --> DATAFLOW
    DATAFLOW --> COMPUTE_GPU
    COMPUTE_GPU --> BIGTABLE
    VERTEX --> ARTIFACT
```

## Provider Mapping

| Component | AWS | GCP | Azure |
|-----------|-----|-----|-------|
| Kafka | MSK | Pub/Sub | Event Hubs |
| Stream Processing | Kinesis Analytics | Dataflow | Stream Analytics |
| Kubernetes | EKS | GKE | AKS |
| GPU Compute | EC2 p3/g4 | Compute Engine GPU | NC-series |
| Time-Series DB | Timestream | Bigtable | Time Series Insights |
| ML Platform | SageMaker | Vertex AI | Azure ML |
| Alerting | SNS | Cloud Monitoring | Azure Monitor |

## Cost Estimation (AWS)

| Tier | Monthly Cost | Specs |
|------|--------------|-------|
| **Starter** | ~$1500 | MSK 3-node, g4dn.xlarge x2, Timestream |
| **Growth** | ~$5000 | MSK 6-node, p3.2xlarge x4, Multi-AZ |
| **Enterprise** | ~$15000+ | Multi-region, SageMaker, 24/7 GPU |

**Key Cost Drivers**:
- GPU instances for ML inference
- Kafka/MSK cluster size
- Time-series data retention
- Data transfer volume
