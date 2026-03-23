#!/usr/bin/env python3
"""Validate documentation completeness across all project folders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]

PROJECTS: Dict[str, Dict[str, List[str]]] = {
    "Anomaly Detection System": {
        "requirements": ["requirements-document.md", "user-stories.md"],
        "analysis": [
            "use-case-diagram.md",
            "use-case-descriptions.md",
            "system-context-diagram.md",
            "activity-diagram.md",
            "bpmn-swimlane-diagram.md",
            "data-dictionary.md",
            "business-rules.md",
            "event-catalog.md",
        ],
        "high-level-design": [
            "system-sequence-diagram.md",
            "domain-model.md",
            "data-flow-diagram.md",
            "architecture-diagram.md",
            "c4-context-container.md",
        ],
        "detailed-design": [
            "class-diagram.md",
            "sequence-diagram.md",
            "state-machine-diagram.md",
            "erd-database-schema.md",
            "component-diagram.md",
            "api-design.md",
            "c4-component.md",
        ],
        "infrastructure": [
            "deployment-diagram.md",
            "network-infrastructure.md",
            "cloud-architecture.md",
        ],
        "edge-cases": [
            "README.md",
            "data-ingestion.md",
            "feature-engineering.md",
            "model-scoring.md",
            "alerting.md",
            "storage.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
        "implementation": ["code-guidelines.md", "c4-code-diagram.md", "implementation-playbook.md"],
    },
    "Document Intelligence System": {
        "requirements": ["requirements-document.md", "user-stories.md"],
        "analysis": [
            "use-case-diagram.md",
            "use-case-descriptions.md",
            "system-context-diagram.md",
            "activity-diagram.md",
            "bpmn-swimlane-diagram.md",
            "data-dictionary.md",
            "business-rules.md",
            "event-catalog.md",
        ],
        "high-level-design": [
            "system-sequence-diagram.md",
            "domain-model.md",
            "data-flow-diagram.md",
            "architecture-diagram.md",
            "c4-context-container.md",
        ],
        "detailed-design": [
            "class-diagram.md",
            "sequence-diagram.md",
            "state-machine-diagram.md",
            "erd-database-schema.md",
            "component-diagram.md",
            "api-design.md",
            "c4-component.md",
        ],
        "infrastructure": [
            "deployment-diagram.md",
            "network-infrastructure.md",
            "cloud-architecture.md",
        ],
        "edge-cases": [
            "README.md",
            "document-ingestion.md",
            "ocr.md",
            "classification.md",
            "extraction.md",
            "validation-and-review.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
        "implementation": ["code-guidelines.md", "c4-code-diagram.md", "implementation-playbook.md"],
    },
    "E-Commerce": {
        "requirements": ["requirements.md", "user-stories.md"],
        "analysis": [
            "use-case-diagram.md",
            "use-case-descriptions.md",
            "system-context-diagram.md",
            "activity-diagrams.md",
            "swimlane-diagrams.md",
            "data-dictionary.md",
            "business-rules.md",
            "event-catalog.md",
        ],
        "high-level-design": [
            "system-sequence-diagrams.md",
            "domain-model.md",
            "data-flow-diagrams.md",
            "architecture-diagram.md",
            "c4-diagrams.md",
        ],
        "detailed-design": [
            "class-diagrams.md",
            "state-machine-diagrams.md",
            "erd-database-schema.md",
            "component-diagrams.md",
            "api-design.md",
            "c4-component-diagram.md",
        ],
        "infrastructure": [
            "deployment-diagram.md",
            "network-infrastructure.md",
            "cloud-architecture.md",
        ],
        "edge-cases": [
            "README.md",
            "inventory.md",
            "orders.md",
            "payments.md",
            "shipping.md",
            "returns.md",
            "pricing.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
        "implementation": ["implementation-guidelines.md", "c4-code-diagram.md", "implementation-playbook.md"],
    },
    "Ticketing and Project Management System": {
        "requirements": ["requirements-document.md", "user-stories.md"],
        "analysis": [
            "use-case-diagram.md",
            "use-case-descriptions.md",
            "system-context-diagram.md",
            "activity-diagram.md",
            "bpmn-swimlane-diagram.md",
            "data-dictionary.md",
            "business-rules.md",
            "event-catalog.md",
        ],
        "high-level-design": [
            "system-sequence-diagram.md",
            "domain-model.md",
            "data-flow-diagram.md",
            "architecture-diagram.md",
            "c4-context-container.md",
        ],
        "detailed-design": [
            "class-diagram.md",
            "sequence-diagram.md",
            "state-machine-diagram.md",
            "erd-database-schema.md",
            "component-diagram.md",
            "api-design.md",
            "c4-component.md",
        ],
        "infrastructure": [
            "deployment-diagram.md",
            "network-infrastructure.md",
            "cloud-architecture.md",
        ],
        "edge-cases": [
            "README.md",
            "ticket-intake-and-attachments.md",
            "assignment-and-sla.md",
            "project-planning-and-milestones.md",
            "change-management-and-replanning.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
        "implementation": ["code-guidelines.md", "c4-code-diagram.md", "implementation-playbook.md"],
    },
    "Library Management System": {
        "requirements": ["requirements-document.md", "user-stories.md"],
        "analysis": [
            "use-case-diagram.md",
            "use-case-descriptions.md",
            "system-context-diagram.md",
            "activity-diagram.md",
            "bpmn-swimlane-diagram.md",
            "data-dictionary.md",
            "business-rules.md",
            "event-catalog.md",
        ],
        "high-level-design": [
            "system-sequence-diagram.md",
            "domain-model.md",
            "data-flow-diagram.md",
            "architecture-diagram.md",
            "c4-context-container.md",
        ],
        "detailed-design": [
            "class-diagram.md",
            "sequence-diagram.md",
            "state-machine-diagram.md",
            "erd-database-schema.md",
            "component-diagram.md",
            "api-design.md",
            "c4-component.md",
        ],
        "infrastructure": [
            "deployment-diagram.md",
            "network-infrastructure.md",
            "cloud-architecture.md",
        ],
        "edge-cases": [
            "README.md",
            "catalog-and-metadata.md",
            "circulation-and-overdues.md",
            "reservations-and-waitlists.md",
            "acquisitions-and-inventory.md",
            "digital-lending-and-access.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
        "implementation": ["code-guidelines.md", "c4-code-diagram.md", "implementation-playbook.md"],
    },
    "Restaurant Management System": {
        "requirements": ["requirements-document.md", "user-stories.md"],
        "analysis": [
            "use-case-diagram.md",
            "use-case-descriptions.md",
            "system-context-diagram.md",
            "activity-diagram.md",
            "bpmn-swimlane-diagram.md",
            "data-dictionary.md",
            "business-rules.md",
            "event-catalog.md",
        ],
        "high-level-design": [
            "system-sequence-diagram.md",
            "domain-model.md",
            "data-flow-diagram.md",
            "architecture-diagram.md",
            "c4-context-container.md",
        ],
        "detailed-design": [
            "class-diagram.md",
            "sequence-diagram.md",
            "state-machine-diagram.md",
            "erd-database-schema.md",
            "component-diagram.md",
            "api-design.md",
            "c4-component.md",
        ],
        "infrastructure": [
            "deployment-diagram.md",
            "network-infrastructure.md",
            "cloud-architecture.md",
        ],
        "edge-cases": [
            "README.md",
            "table-service-and-ordering.md",
            "kitchen-and-preparation.md",
            "inventory-and-procurement.md",
            "billing-and-accounting.md",
            "delivery-and-channel-integration.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
        "implementation": ["code-guidelines.md", "c4-code-diagram.md", "implementation-playbook.md"],
    },
    "Slot Booking System": {
        "requirements": ["requirements-document.md", "user-stories.md"],
        "analysis": [
            "use-case-diagram.md",
            "use-case-descriptions.md",
            "system-context-diagram.md",
            "activity-diagram.md",
            "bpmn-swimlane-diagram.md",
            "data-dictionary.md",
            "business-rules.md",
            "event-catalog.md",
        ],
        "high-level-design": [
            "system-sequence-diagram.md",
            "domain-model.md",
            "data-flow-diagram.md",
            "architecture-diagram.md",
            "c4-context-container.md",
        ],
        "detailed-design": [
            "class-diagram.md",
            "sequence-diagram.md",
            "state-machine-diagram.md",
            "erd-database-schema.md",
            "component-diagram.md",
            "api-design.md",
            "c4-component.md",
        ],
        "infrastructure": [
            "deployment-diagram.md",
            "network-infrastructure.md",
            "cloud-architecture.md",
        ],
        "edge-cases": [
            "README.md",
            "slot-availability.md",
            "booking-and-payments.md",
            "cancellations-and-refunds.md",
            "notifications.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
        "implementation": ["code-guidelines.md", "c4-code-diagram.md", "implementation-playbook.md"],
    },
    "Healthcare Appointment System": {
        "requirements": ["requirements-document.md", "user-stories.md"],
        "analysis": [
            "use-case-diagram.md",
            "use-case-descriptions.md",
            "system-context-diagram.md",
            "activity-diagram.md",
            "bpmn-swimlane-diagram.md",
            "data-dictionary.md",
            "business-rules.md",
            "event-catalog.md",
        ],
        "high-level-design": [
            "system-sequence-diagram.md",
            "domain-model.md",
            "data-flow-diagram.md",
            "architecture-diagram.md",
            "c4-context-container.md",
        ],
        "detailed-design": [
            "class-diagram.md",
            "sequence-diagram.md",
            "state-machine-diagram.md",
            "erd-database-schema.md",
            "component-diagram.md",
            "api-design.md",
            "c4-component.md",
        ],
        "infrastructure": [
            "deployment-diagram.md",
            "network-infrastructure.md",
            "cloud-architecture.md",
        ],
        "edge-cases": [
            "README.md",
            "slot-availability.md",
            "booking-and-payments.md",
            "cancellations-and-refunds.md",
            "notifications.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
        "implementation": ["code-guidelines.md", "c4-code-diagram.md", "implementation-playbook.md"],
    },
    "Logistics Tracking System": {
        "requirements": ["requirements-document.md", "user-stories.md"],
        "analysis": [
            "use-case-diagram.md",
            "use-case-descriptions.md",
            "system-context-diagram.md",
            "activity-diagram.md",
            "bpmn-swimlane-diagram.md",
            "data-dictionary.md",
            "business-rules.md",
            "event-catalog.md",
        ],
        "high-level-design": [
            "system-sequence-diagram.md",
            "domain-model.md",
            "data-flow-diagram.md",
            "architecture-diagram.md",
            "c4-context-container.md",
        ],
        "detailed-design": [
            "class-diagram.md",
            "sequence-diagram.md",
            "state-machine-diagram.md",
            "erd-database-schema.md",
            "component-diagram.md",
            "api-design.md",
            "c4-component.md",
        ],
        "infrastructure": [
            "deployment-diagram.md",
            "network-infrastructure.md",
            "cloud-architecture.md",
        ],
        "edge-cases": [
            "README.md",
            "shipment-ingestion.md",
            "route-and-handoffs.md",
            "tracking-and-telemetry.md",
            "delivery-exceptions.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
        "implementation": ["code-guidelines.md", "c4-code-diagram.md", "implementation-playbook.md"],
    },
    "Learning Management System": {
        "requirements": ["requirements-document.md", "user-stories.md"],
        "analysis": [
            "use-case-diagram.md",
            "use-case-descriptions.md",
            "system-context-diagram.md",
            "activity-diagram.md",
            "bpmn-swimlane-diagram.md",
            "data-dictionary.md",
            "business-rules.md",
            "event-catalog.md",
        ],
        "high-level-design": [
            "system-sequence-diagram.md",
            "domain-model.md",
            "data-flow-diagram.md",
            "architecture-diagram.md",
            "c4-context-container.md",
        ],
        "detailed-design": [
            "class-diagram.md",
            "sequence-diagram.md",
            "state-machine-diagram.md",
            "erd-database-schema.md",
            "component-diagram.md",
            "api-design.md",
            "c4-component.md",
        ],
        "infrastructure": [
            "deployment-diagram.md",
            "network-infrastructure.md",
            "cloud-architecture.md",
        ],
        "edge-cases": [
            "README.md",
            "content-ingestion.md",
            "assessment-and-grading.md",
            "progress-tracking.md",
            "notifications.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
        "implementation": ["code-guidelines.md", "c4-code-diagram.md", "implementation-playbook.md"],
    },
    "Smart Recommendation Engine": {
        "requirements": ["requirements-document.md", "user-stories.md"],
        "analysis": [
            "use-case-diagram.md",
            "use-case-descriptions.md",
            "system-context-diagram.md",
            "activity-diagram.md",
            "bpmn-swimlane-diagram.md",
            "data-dictionary.md",
            "business-rules.md",
            "event-catalog.md",
        ],
        "high-level-design": [
            "system-sequence-diagram.md",
            "domain-model.md",
            "data-flow-diagram.md",
            "architecture-diagram.md",
            "c4-context-container.md",
        ],
        "detailed-design": [
            "class-diagram.md",
            "sequence-diagram.md",
            "state-machine-diagram.md",
            "erd-database-schema.md",
            "component-diagram.md",
            "api-design.md",
            "c4-component.md",
        ],
        "infrastructure": [
            "deployment-diagram.md",
            "network-infrastructure.md",
            "cloud-architecture.md",
        ],
        "edge-cases": [
            "README.md",
            "data-ingestion.md",
            "feature-engineering.md",
            "model-serving.md",
            "ranking-and-bias.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
        "implementation": ["code-guidelines.md", "c4-code-diagram.md", "implementation-playbook.md"],
    },
}

README_MUST_INCLUDE = [
    "Documentation Structure",
    "Key Features",
    "Getting Started",
    "Documentation Status",
]


@dataclass
class ValidationError:
    project: str
    issue: str



def validate() -> List[ValidationError]:
    errors: List[ValidationError] = []

    for project_name, expected_map in PROJECTS.items():
        project_dir = REPO_ROOT / project_name
        readme = project_dir / "README.md"

        if not project_dir.exists():
            errors.append(ValidationError(project_name, "Project directory is missing"))
            continue

        if not readme.exists():
            errors.append(ValidationError(project_name, "README.md is missing"))
        else:
            readme_text = readme.read_text(encoding="utf-8")
            for heading in README_MUST_INCLUDE:
                if heading not in readme_text:
                    errors.append(
                        ValidationError(
                            project_name,
                            f"README.md is missing required section heading: '{heading}'",
                        )
                    )

        for folder, expected_files in expected_map.items():
            folder_path = project_dir / folder
            if not folder_path.exists():
                errors.append(
                    ValidationError(project_name, f"Required folder missing: {folder}")
                )
                continue

            for filename in expected_files:
                file_path = folder_path / filename
                if not file_path.exists():
                    errors.append(
                        ValidationError(
                            project_name, f"Missing file: {folder}/{filename}"
                        )
                    )
                    continue

                if file_path.stat().st_size == 0:
                    errors.append(
                        ValidationError(
                            project_name,
                            f"Empty file: {folder}/{filename}",
                        )
                    )

    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        print("❌ Documentation validation failed:\n")
        for f in failures:
            print(f"- [{f.project}] {f.issue}")
        raise SystemExit(1)

    print("✅ Documentation validation passed for all projects.")
    print(f"Validated {len(PROJECTS)} projects against folder/file/README quality gates.")
