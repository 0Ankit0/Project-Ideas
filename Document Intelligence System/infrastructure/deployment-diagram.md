# Deployment Diagram - Document Intelligence System

```mermaid
graph TB
    subgraph "Application Tier"
        API1[API Server<br/>FastAPI]
        API2[API Server<br/>FastAPI]
        WORKER1[Worker<br/>Python/Celery]
        WORKER2[Worker<br/>Python/Celery]
    end
    
    subgraph "AI Services"
        OCR[OCR Service<br/>Tesseract/GPU]
        NER[NER Service<br/>spaCy/GPU]
        CLS[Classifier<br/>TensorFlow]
    end
    
    subgraph "Data & Storage"
        DB[(PostgreSQL)]
        S3[S3 Bucket]
        QUEUE[RabbitMQ]
        REDIS[(Redis)]
    end
    
    subgraph "Monitoring"
        PROM[Prometheus]
        GRAF[Grafana]
    end
    
    LB[Load Balancer] --> API1
    LB --> API2
    
    API1 --> S3
    API1 --> DB
    API1 --> QUEUE
    API1 --> REDIS
    
    QUEUE --> WORKER1
    QUEUE --> WORKER2
    
    WORKER1 --> OCR
    WORKER1 --> NER
    WORKER1 --> CLS
    WORKER1 --> DB
    
    API1 --> PROM
    PROM --> GRAF
```

## Kubernetes Deployment

```yaml
# API Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: document-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: doc-intelligence-api:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url

---
# Worker Deployment with GPU
apiVersion: apps/v1
kind: Deployment
metadata:
  name: processing-worker
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: worker
        image: doc-intelligence-worker:latest
        resources:
          requests:
            memory: "8Gi"
            cpu: "4"
            nvidia.com/gpu: 1
          limits:
            memory: "16Gi"
            cpu: "8"
            nvidia.com/gpu: 1
```

## Node Specifications

| Service | CPU | RAM | GPU | Purpose |
|---------|-----|-----|-----|---------|
| API Server | 2 vCPU | 4GB | - | Handle HTTP requests |
| Processing Worker | 4 vCPU | 8GB | T4/V100 | AI processing |
| OCR Service | 4 vCPU | 8GB | Optional | Text extraction |
| NER Service | 4 vCPU | 8GB | T4 | Entity extraction |
| Database | 4 vCPU | 16GB | - | PostgreSQL |
| RabbitMQ | 2 vCPU | 4GB | - | Message queue |
