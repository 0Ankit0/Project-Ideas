# C4 Code Diagram

This document expands the **code-level C4 map** for the Smart Recommendation Engine with explicit module responsibilities and execution flow.

## Code-Level Structure
```mermaid
flowchart TB
  subgraph Interface[Interface Layer]
    RecommendationController
    FeedbackController
    ExperimentController
  end

  subgraph Application[Application Layer]
    RecommendationAppService
    CandidateGenerationService
    RankingService
    FeedbackIngestionService
    ExperimentAppService
  end

  subgraph Domain[Domain Layer]
    RecommendationAggregate
    CandidateSetEntity
    RankingPolicy
    ExperimentAssignment
  end

  subgraph Infrastructure[Infrastructure Layer]
    CandidateRepository
    InteractionRepository
    ModelAdapter
    FeatureStoreAdapter
    EventPublisher
    MetricsAdapter
  end

  RecommendationController --> RecommendationAppService --> RecommendationAggregate
  FeedbackController --> FeedbackIngestionService --> InteractionRepository
  ExperimentController --> ExperimentAppService --> ExperimentAssignment

  RecommendationAppService --> CandidateGenerationService --> CandidateSetEntity
  RecommendationAppService --> RankingService --> RankingPolicy
  RankingService --> ModelAdapter
  CandidateGenerationService --> FeatureStoreAdapter
  RecommendationAppService --> CandidateRepository
  RecommendationAppService --> EventPublisher
  RecommendationAppService --> MetricsAdapter
```

## Critical Runtime Sequence: Recommendation Request
```mermaid
sequenceDiagram
  autonumber
  participant API as RecommendationController
  participant APP as RecommendationAppService
  participant CAND as CandidateGenerationService
  participant RANK as RankingService
  participant MODEL as ModelAdapter
  participant EXP as ExperimentAppService
  participant PUB as EventPublisher

  API->>APP: getRecommendations(userId, context)
  APP->>EXP: assign variant
  EXP-->>APP: experiment assignment
  APP->>CAND: build candidate set
  CAND-->>APP: candidates
  APP->>RANK: rank(candidates, context)
  RANK->>MODEL: score batch
  MODEL-->>RANK: relevance scores
  RANK-->>APP: ranked list
  APP->>PUB: emit recommendation served event
  APP-->>API: top-N recommendations
```

## Module Responsibilities
- **Candidate generation**: recall-focused, high coverage, low latency.
- **Ranking**: precision-focused ordering using model scores + policy constraints.
- **Experiment service**: deterministic bucketing and variant guardrails.
- **Feedback ingestion**: captures click/view/conversion signals for retraining.

## Implementation Notes
- Version recommendation payloads to avoid client breakage when features evolve.
- Track `model version`, `feature snapshot`, and `experiment variant` per response.
- Separate online ranking latency budget from offline training pipelines.

## Code Realization Guidance
- Ensure package boundaries mirror architectural boundaries and avoid cyclic dependencies.
- Capture module-level observability conventions (structured logging, tracing spans, metric naming).

## Mermaid CI Flow
```mermaid
flowchart LR
    A[PR opened] --> B[Unit + contract tests]
    B --> C[Static analysis]
    C --> D[Build artifact + SBOM]
    D --> E[Staging deploy]
    E --> F[Canary rollout]
```
