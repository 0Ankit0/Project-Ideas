# C4 Code Diagram

```mermaid
flowchart TB
  RecommendationController --> RecommendationAppService --> RecommendationAggregate
  CandidateGenService --> CandidateRepository
  RankingService --> ModelAdapter
  RecommendationAppService --> RankingService
  RecommendationAppService --> EventPublisher
```
