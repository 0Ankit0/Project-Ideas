# Detailed Component Diagrams

## Build Service Components

The Build Service is responsible for detecting application language, compiling code, running tests, and creating container images.

### Internal Architecture

```mermaid
graph TB
    Input["Build Job Input<br/>- Repository URL<br/>- Commit SHA<br/>- Branch"]
    
    Clone["Git Clone<br/>Clone repo at SHA<br/>Store in workspace"]
    
    Detect["Language Detector<br/>Analyze package.json<br/>Analyze requirements.txt<br/>Analyze go.mod<br/>Determine runtime type"]
    
    Pack["Buildpack Selector<br/>Select appropriate buildpack<br/>nodejs-20.x<br/>python-3.12<br/>go-1.21"]
    
    Exec["Build Executor<br/>Run buildpack<br/>Execute commands<br/>npm install<br/>npm run build<br/>go build"]
    
    Test["Test Runner<br/>Run tests<br/>Capture output<br/>Fail if tests fail"]
    
    Image["Docker Builder<br/>FROM base image<br/>Copy artifacts<br/>Set entrypoint<br/>docker build"]
    
    Scan["Security Scanner<br/>Scan for vulnerabilities<br/>CVE database check<br/>Generate report"]
    
    Push["Registry Push<br/>Tag image<br/>Push to registry<br/>Generate digest"]
    
    Output["Build Complete<br/>- Image URI<br/>- Image Digest<br/>- Duration<br/>- Status"]
    
    Input --> Clone
    Clone --> Detect
    Detect --> Pack
    Pack --> Exec
    Exec --> Test
    Test --> Image
    Image --> Scan
    Scan --> Push
    Push --> Output
    
    style Input fill:#4A90E2
    style Output fill:#90EE90
    style Exec fill:#FFD700
    style Image fill:#FF6B6B
```

## Deploy Service Components

The Deploy Service orchestrates Kubernetes deployments, health checks, and traffic routing.

```mermaid
graph TB
    Input["Deployment Request<br/>- Application ID<br/>- Image URI<br/>- Env Variables<br/>- Instance Count"]
    
    Validate["Input Validation<br/>- Check quota<br/>- Verify image exists<br/>- Validate config"]
    
    K8sManifest["Generate K8s Manifest<br/>- Create Deployment spec<br/>- Set resource limits<br/>- Inject env vars<br/>- Set health probes"]
    
    Schedule["Kubernetes Scheduler<br/>- Schedule pods<br/>- Select nodes<br/>- Reserve resources"]
    
    ImagePull["Image Pull<br/>- Pull image from registry<br/>- Verify digest<br/>- Cache locally"]
    
    ContainerStart["Container Start<br/>- Create container<br/>- Mount volumes<br/>- Configure networking<br/>- Start process"]
    
    HealthCheck["Health Check Loop<br/>- Poll /health endpoint<br/>- Timeout: 30s<br/>- Retries: 3<br/>- Backoff: exponential"]
    
    HealthDecision{Health<br/>Status?}
    
    Healthy["Mark Healthy<br/>- Add to load balancer<br/>- Start serving traffic<br/>- Update status DB"]
    
    Unhealthy["Mark Unhealthy<br/>- Remove from LB<br/>- Stop container<br/>- Log error<br/>- Alert operators"]
    
    Drain["Graceful Drain<br/>- Close new connections<br/>- Wait for in-flight<br/>- Timeout: 30s<br/>- Force terminate"]
    
    Complete["Deployment Complete<br/>- New version live<br/>- Old version draining<br/>- Metrics collected"]
    
    Input --> Validate
    Validate --> K8sManifest
    K8sManifest --> Schedule
    Schedule --> ImagePull
    ImagePull --> ContainerStart
    ContainerStart --> HealthCheck
    HealthCheck --> HealthDecision
    
    HealthDecision -->|Healthy| Healthy
    HealthDecision -->|Unhealthy| Unhealthy
    
    Healthy --> Drain
    Drain --> Complete
    
    style Input fill:#4A90E2
    style Healthy fill:#90EE90
    style Complete fill:#90EE90
    style Unhealthy fill:#FFB6C6
    style HealthCheck fill:#FFD700
```

---

**Document Version**: 1.0
**Last Updated**: 2024
