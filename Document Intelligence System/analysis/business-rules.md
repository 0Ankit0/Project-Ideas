# Business Rules - Document Intelligence System

## Confidence Thresholds
- OCR confidence $< 0.85$ triggers review.
- Classification confidence $< 0.80$ triggers manual document type selection.
- Entity confidence $< 0.75$ is flagged for review.

## Review Assignment
- Documents with low-confidence fields are auto-assigned to the review queue.
- High-priority document types are routed to senior reviewers.

## Validation Rules
- Dates must be in ISO 8601 or known locale formats.
- Amounts must match currency format and totals must reconcile.
- Mandatory fields depend on document type.

## Duplicate Handling
- A document hash is used to detect duplicates within a configurable window.
- Duplicates are marked but retained for audit.

## Retention Policy
- Original documents retained for 180 days by default.
- Extracted structured data retained for 2 years by default.