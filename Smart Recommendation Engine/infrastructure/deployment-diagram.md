# Deployment Diagram - Smart Recommendation Engine

```mermaid
graph TB
    subgraph "Application Tier"
        API1[API Server<br/>FastAPI]
        API2[API Server<br/>FastAPI]
        WORKER[Training Worker<br/>Python]
    end
    
    subgraph "ML Infrastructure"
        FEATURE[Feature Store<br/>Feast]
        REGISTRY[Model Registry<br/>MLflow]
        SERVING[Model Serving<br/>TensorFlow Serving]
        VECTOR[Vector DB<br/>Milvus]
    end
    
    subgraph "Data & Messaging"
        DB[(PostgreSQL)]
        REDIS[(Redis)]
        KAFKA[Kafka]
    end
    
    subgraph "Monitoring"
        PROM[Prometheus]
        GRAF[Grafana]
    end
    
    LB[Load Balancer] --> API1
    LB --> API2
    
    API1 --> SERVING
    API1 --> FEATURE
    API1 --> REDIS
    API1 --> DB
    
    WORKER --> FEATURE
    WORKER --> REGISTRY
    WORKER --> DB
    
    SERVING --> REGISTRY
    SERVING --> VECTOR
    
    KAFKA --> WORKER
    
    API1 --> PROM
    PROM --> GRAF
```

## Kubernetes Deployment

```yaml
# API Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: recommendation-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: rec-api:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

## Node Specifications

| Service | CPU | RAM | GPU | Purpose |
|---------|-----|-----|-----|---------|
| API Server | 2 vCPU | 4GB | - | Serve requests |
| Training Worker | 8 vCPU | 32GB | Optional | Train models |
| Model Serving | 4 vCPU | 8GB | Optional | ML inference |
| Feature Store | 4 vCPU | 16GB | - | Feature management |

## Infrastructure Deployment Notes
- Bind each infrastructure component to IaC modules, environment promotion strategy, and blast-radius boundaries.
- Document subnet, IAM, secret rotation, and data encryption controls directly in deployment checklists.

## Mermaid Operations Path: Deployment Diagram
```mermaid
flowchart TB
    A[Commit IaC change] --> B[Plan + policy checks]
    B --> C[Security review]
    C --> D[Apply to staging]
    D --> E[Resilience tests]
    E --> F{Healthy?}
    F -- No --> G[Rollback and incident ticket]
    F -- Yes --> H[Promote to production]
```

## Capacity & Reliability Requirements
- Forecast capacity for peak events and retraining windows.
- Validate AZ/zone failure behavior and recovery-time objective (RTO).
- Ensure observability endpoints and synthetic probes are deployed with the stack.
