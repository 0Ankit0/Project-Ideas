# Edge Cases - Assessment and Grading

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| Learner loses connectivity during timed assessment | Attempt integrity becomes unclear | Autosave progress and define timeout/recovery rules |
| Auto-grading differs from instructor override | Score disputes and confusion | Preserve original score, override reason, and final published grade clearly |
| Reviewer publishes grade to wrong learner context | Privacy and correctness risk | Use strong submission identity checks and confirmation steps |
| Attempt limit changes after learners already started | Fairness and audit concerns | Version assessment rules and apply effective-date behavior explicitly |
| Rubric edited during active grading cycle | Inconsistent scores across learners | Lock rubric versions for active review sessions |


## Implementation Details: Grading Integrity Controls

- Persist rubric snapshot at submission start and grading completion.
- Support moderation workflows with first/second reviewer and tie-break policy.
- Record score provenance (`auto`, `manual`, `override`) per criterion.
