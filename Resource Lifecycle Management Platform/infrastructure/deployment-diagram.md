# Deployment Diagram

## Topology
- Multi-AZ compute clusters for API and worker services
- Managed relational database with replicas
- Managed message broker for event distribution
- Object storage for evidence artifacts

## Release Strategy
- Blue/green or canary deploy for write-critical services
- Schema migrations with backward-compatible phases
