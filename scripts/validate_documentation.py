#!/usr/bin/env python3
"""Validate documentation completeness across all project folders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]

README_MUST_INCLUDE = [
    "Documentation Structure",
    "Key Features",
    "Getting Started",
    "Documentation Status",
]

ANALYSIS_QUALITY_GATES = {
    "data-dictionary.md": {
        "required_headings": [
            "## Core Entities",
            "## Canonical Relationship Diagram",
            "## Data Quality Controls",
        ],
        "required_mermaid_hint": "erDiagram",
        "minimum_lines": 25,
        "minimum_table_rows": 6,
    },
    "business-rules.md": {
        "required_headings": [
            "## Enforceable Rules",
            "## Rule Evaluation Pipeline",
            "## Exception and Override Handling",
        ],
        "required_mermaid_hint": "flowchart",
        "minimum_lines": 20,
        "minimum_numbered_rules": 5,
    },
    "event-catalog.md": {
        "required_headings": [
            "## Contract Conventions",
            "## Domain Events",
            "## Publish and Consumption Sequence",
            "## Operational SLOs",
        ],
        "required_mermaid_hint": "sequenceDiagram",
        "minimum_lines": 30,
        "minimum_table_rows": 6,
    },
}

PLACEHOLDER_PATTERNS = [
    r"\bTODO\b",
    r"\bTBD\b",
    r"\bplaceholder\b",
    r"\blorem ipsum\b",
]

QUALITY_ENFORCED_PROJECTS = {
    "Customer Relationship Management Platform",
    "Subscription Billing and Entitlements Platform",
    "Payment Orchestration and Wallet Platform",
    "Warehouse Management System",
    "Hospital Information System",
    "Customer Support and Contact Center Platform",
    "Identity and Access Management Platform",
    "Messaging and Notification Platform",
    "Rental Management System",
    "Employee Management System",
    "E-Commerce",
    "Restaurant Management System",
    "Logistics Tracking System",
    "Ticketing and Project Management System",
    "Content Management System",
    "Smart Recommendation Engine",
    "Anomaly Detection System",
    "Document Intelligence System",
    "Healthcare Appointment System",
    "Learning Management System",
    "Library Management System",
    "Finance-Management",
    "Student Information System",
    "Backend as a Service Platform",
    "Resource Lifecycle Management Platform",
    "Slot Booking System",
    # New projects — wave 1
    "Fleet Management System",
    "Real Estate Management System",
    "Job Board and Recruitment Platform",
    "Event Management and Ticketing Platform",
    "Insurance Management System",
    "IoT Device Management Platform",
    "Supply Chain Management Platform",
    "Social Networking Platform",
    # New projects — wave 2
    "Digital Banking Platform",
    "Video Streaming Platform",
    "Hotel Property Management System",
    "Telemedicine Platform",
    "Manufacturing Execution System",
    "Legal Case Management System",
    # New projects — wave 3
    "Application Hosting Platform",
}

SINGULAR_TEMPLATE = {
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
    "implementation": [
        "code-guidelines.md",
        "c4-code-diagram.md",
        "implementation-playbook.md",
    ],
}

PLURAL_TEMPLATE = {
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
        "sequence-diagrams.md",
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
    "implementation": [
        "implementation-guidelines.md",
        "c4-code-diagram.md",
        "backend-status-matrix.md",
    ],
}

PROJECTS: Dict[str, Dict[str, List[str]]] = {
    # Singular-family projects
    "Anomaly Detection System": {
        **SINGULAR_TEMPLATE,
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
    },
    "Backend as a Service Platform": {
        **SINGULAR_TEMPLATE,
        "edge-cases": [
            "README.md",
            "provider-selection-and-provisioning.md",
            "auth-and-tenancy.md",
            "data-api-and-schema.md",
            "storage-and-file-providers.md",
            "functions-and-jobs.md",
            "realtime-and-messaging.md",
            "api-and-sdk.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Document Intelligence System": {
        **SINGULAR_TEMPLATE,
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
    },
    "Healthcare Appointment System": {
        **SINGULAR_TEMPLATE,
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
    },
    "Learning Management System": {
        **SINGULAR_TEMPLATE,
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
    },
    "Library Management System": {
        **SINGULAR_TEMPLATE,
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
    },
    "Logistics Tracking System": {
        **SINGULAR_TEMPLATE,
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
    },
    "Restaurant Management System": {
        **SINGULAR_TEMPLATE,
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
    },
    "Slot Booking System": {
        **SINGULAR_TEMPLATE,
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
    },
    "Smart Recommendation Engine": {
        **SINGULAR_TEMPLATE,
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
    },
    "Ticketing and Project Management System": {
        **SINGULAR_TEMPLATE,
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
    },
    # Plural-family projects
    "E-Commerce": {
        **PLURAL_TEMPLATE,
        "detailed-design": [
            *PLURAL_TEMPLATE["detailed-design"],
            "recommendation-engine.md",
        ],
        "edge-cases": [
            "README.md",
            "cart-checkout-and-payment-failures.md",
            "inventory-allocation-and-oversell.md",
            "shipping-and-delivery-exceptions.md",
            "returns-refunds-and-vendor-reconciliation.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Content Management System": {
        **PLURAL_TEMPLATE,
        "edge-cases": [
            "README.md",
            "content-ingestion-and-versioning.md",
            "workflow-and-approvals.md",
            "publishing-and-rollbacks.md",
            "media-and-asset-processing.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Employee Management System": {
        **PLURAL_TEMPLATE,
        "edge-cases": [
            "README.md",
            "onboarding-and-offboarding.md",
            "attendance-and-leave.md",
            "payroll-and-benefits.md",
            "performance-and-review-cycles.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Finance-Management": {
        **PLURAL_TEMPLATE,
        "detailed-design": [
            *PLURAL_TEMPLATE["detailed-design"],
            "compliance-framework.md",
        ],
        "implementation": [
            "implementation-guidelines.md",
            "c4-code-diagram.md",
            "backend-status-matrix.md",
        ],
        "edge-cases": [
            "README.md",
            "ledger-consistency-and-close.md",
            "reconciliation-and-settlement.md",
            "budgeting-and-forecast-variance.md",
            "tax-and-jurisdiction-rules.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Rental Management System": {
        **PLURAL_TEMPLATE,
        "edge-cases": [
            "README.md",
            "inventory-availability-conflicts.md",
            "booking-extensions-and-partial-returns.md",
            "damage-claims-and-deposit-adjustments.md",
            "offline-checkin-checkout-sync-conflicts.md",
            "payment-reconciliation-across-channels.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Student Information System": {
        **PLURAL_TEMPLATE,
        "edge-cases": [
            "README.md",
            "enrollment-and-seat-allocation.md",
            "grades-and-transcript-corrections.md",
            "attendance-and-term-policies.md",
            "fee-assessment-and-waivers.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },

    "Customer Relationship Management Platform": {
        **PLURAL_TEMPLATE,
        "detailed-design": [
            *PLURAL_TEMPLATE["detailed-design"],
            "lead-scoring-and-deduplication.md",
        ],
        "edge-cases": [
            "README.md",
            "dedupe-merge-conflicts.md",
            "territory-reassignment.md",
            "forecast-integrity.md",
            "email-calendar-sync.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Subscription Billing and Entitlements Platform": {
        **PLURAL_TEMPLATE,
        "detailed-design": [
            *PLURAL_TEMPLATE["detailed-design"],
            "usage-metering-and-entitlements.md",
        ],
        "edge-cases": [
            "README.md",
            "proration.md",
            "dunning-retries.md",
            "credit-notes.md",
            "tax-jurisdiction-rules.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Payment Orchestration and Wallet Platform": {
        **PLURAL_TEMPLATE,
        "detailed-design": [
            *PLURAL_TEMPLATE["detailed-design"],
            "ledger-and-settlement.md",
        ],
        "edge-cases": [
            "README.md",
            "idempotency-double-charge-protection.md",
            "refunds-chargebacks.md",
            "kyc-onboarding.md",
            "payout-reconciliation.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Warehouse Management System": {
        **PLURAL_TEMPLATE,
        "detailed-design": [
            *PLURAL_TEMPLATE["detailed-design"],
            "inventory-allocation-and-wave-planning.md",
        ],
        "edge-cases": [
            "README.md",
            "bin-conflicts.md",
            "partial-picks-backorders.md",
            "cycle-count-adjustments.md",
            "offline-scanner-sync.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Hospital Information System": {
        **PLURAL_TEMPLATE,
        "detailed-design": [
            *PLURAL_TEMPLATE["detailed-design"],
            "clinical-records-and-care-workflows.md",
        ],
        "edge-cases": [
            "README.md",
            "patient-identity-merge.md",
            "clinical-order-correction.md",
            "consent-sensitive-data-access.md",
            "downtime-mode.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Customer Support and Contact Center Platform": {
        **PLURAL_TEMPLATE,
        "detailed-design": [
            *PLURAL_TEMPLATE["detailed-design"],
            "routing-and-workforce-management.md",
        ],
        "edge-cases": [
            "README.md",
            "thread-deduplication.md",
            "sla-escalation.md",
            "bot-human-handoff.md",
            "retention-redaction.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Identity and Access Management Platform": {
        **PLURAL_TEMPLATE,
        "detailed-design": [
            *PLURAL_TEMPLATE["detailed-design"],
            "policy-engine-and-federation.md",
        ],
        "edge-cases": [
            "README.md",
            "token-revocation.md",
            "federation-scim-drift.md",
            "entitlement-conflicts.md",
            "break-glass-recovery.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Messaging and Notification Platform": {
        **PLURAL_TEMPLATE,
        "detailed-design": [
            *PLURAL_TEMPLATE["detailed-design"],
            "delivery-orchestration-and-template-system.md",
        ],
        "edge-cases": [
            "README.md",
            "provider-failover.md",
            "opt-out-compliance.md",
            "rate-limiting.md",
            "delayed-deduplicated-delivery.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Resource Lifecycle Management Platform": {
        **PLURAL_TEMPLATE,
        "detailed-design": [
            *PLURAL_TEMPLATE["detailed-design"],
            "lifecycle-orchestration.md",
        ],
        "edge-cases": [
            "README.md",
            "reservation-and-allocation-conflicts.md",
            "checkout-checkin-and-condition-disputes.md",
            "lifecycle-state-sync-and-overdue-recovery.md",
            "settlement-and-incident-resolution.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    # ── New projects ────────────────────────────────────────────────────────────
    "Fleet Management System": {
        **SINGULAR_TEMPLATE,
        "edge-cases": [
            "README.md",
            "vehicle-tracking.md",
            "maintenance-scheduling.md",
            "driver-management.md",
            "route-optimization.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Real Estate Management System": {
        **SINGULAR_TEMPLATE,
        "edge-cases": [
            "README.md",
            "property-listings.md",
            "tenant-management.md",
            "lease-lifecycle.md",
            "maintenance-requests.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Job Board and Recruitment Platform": {
        **SINGULAR_TEMPLATE,
        "edge-cases": [
            "README.md",
            "job-posting-and-matching.md",
            "application-tracking.md",
            "interview-scheduling.md",
            "offer-management.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Event Management and Ticketing Platform": {
        **SINGULAR_TEMPLATE,
        "edge-cases": [
            "README.md",
            "event-creation-and-publishing.md",
            "ticket-sales-and-allocation.md",
            "check-in-and-access-control.md",
            "refunds-and-cancellations.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Insurance Management System": {
        **PLURAL_TEMPLATE,
        "detailed-design": [
            *PLURAL_TEMPLATE["detailed-design"],
            "underwriting-and-risk-engine.md",
        ],
        "edge-cases": [
            "README.md",
            "policy-issuance-and-underwriting.md",
            "claims-processing.md",
            "premium-collection.md",
            "fraud-detection.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "IoT Device Management Platform": {
        **PLURAL_TEMPLATE,
        "detailed-design": [
            *PLURAL_TEMPLATE["detailed-design"],
            "telemetry-pipeline-and-rules-engine.md",
        ],
        "edge-cases": [
            "README.md",
            "device-provisioning.md",
            "telemetry-ingestion.md",
            "firmware-updates.md",
            "device-offline-recovery.md",
            "api-and-sdk.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Supply Chain Management Platform": {
        **PLURAL_TEMPLATE,
        "detailed-design": [
            *PLURAL_TEMPLATE["detailed-design"],
            "procurement-and-supplier-collaboration.md",
        ],
        "edge-cases": [
            "README.md",
            "supplier-onboarding.md",
            "purchase-order-management.md",
            "goods-receipt.md",
            "supplier-performance.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Social Networking Platform": {
        **PLURAL_TEMPLATE,
        "detailed-design": [
            *PLURAL_TEMPLATE["detailed-design"],
            "feed-ranking-and-recommendation.md",
        ],
        "edge-cases": [
            "README.md",
            "content-moderation.md",
            "feed-ranking.md",
            "notification-storms.md",
            "account-compromise.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    # ── New projects — wave 2 ─────────────────────────────────────────────────
    "Digital Banking Platform": {
        **PLURAL_TEMPLATE,
        "detailed-design": [
            *PLURAL_TEMPLATE["detailed-design"],
            "core-banking-engine.md",
        ],
        "edge-cases": [
            "README.md",
            "account-lifecycle.md",
            "transaction-processing.md",
            "fraud-and-aml-compliance.md",
            "kyc-and-customer-onboarding.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Video Streaming Platform": {
        **PLURAL_TEMPLATE,
        "detailed-design": [
            *PLURAL_TEMPLATE["detailed-design"],
            "transcoding-and-delivery-pipeline.md",
        ],
        "edge-cases": [
            "README.md",
            "content-upload-and-processing.md",
            "adaptive-streaming.md",
            "live-streaming.md",
            "drm-and-content-protection.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Hotel Property Management System": {
        **SINGULAR_TEMPLATE,
        "edge-cases": [
            "README.md",
            "reservation-management.md",
            "check-in-and-check-out.md",
            "room-assignment-and-housekeeping.md",
            "billing-and-invoicing.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Telemedicine Platform": {
        **SINGULAR_TEMPLATE,
        "edge-cases": [
            "README.md",
            "video-consultation.md",
            "prescription-management.md",
            "patient-data-privacy.md",
            "emergency-escalation.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Manufacturing Execution System": {
        **PLURAL_TEMPLATE,
        "detailed-design": [
            *PLURAL_TEMPLATE["detailed-design"],
            "production-scheduling-and-oee.md",
        ],
        "edge-cases": [
            "README.md",
            "production-order-management.md",
            "quality-control.md",
            "machine-downtime.md",
            "material-shortage.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Legal Case Management System": {
        **SINGULAR_TEMPLATE,
        "edge-cases": [
            "README.md",
            "case-lifecycle.md",
            "document-management.md",
            "billing-and-time-tracking.md",
            "court-deadlines.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
    "Application Hosting Platform": {
        **PLURAL_TEMPLATE,
        "detailed-design": [
            "class-diagrams.md",
            "sequence-diagrams.md",
            "state-machine-diagrams.md",
            "erd-database-schema.md",
            "component-diagrams.md",
            "api-design.md",
            "c4-component-diagram.md",
            "deployment-engine-and-build-pipeline.md",
        ],
        "edge-cases": [
            "README.md",
            "deployment-failures.md",
            "scaling-and-resource-limits.md",
            "build-pipeline-errors.md",
            "custom-domains-and-ssl.md",
            "api-and-ui.md",
            "security-and-compliance.md",
            "operations.md",
        ],
    },
}


@dataclass
class ValidationError:
    project: str
    issue: str


def _validate_analysis_quality(
    project_name: str, file_path: Path, filename: str, errors: List[ValidationError]
) -> None:
    gate = ANALYSIS_QUALITY_GATES.get(filename)
    if gate is None:
        return

    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    if len(lines) < gate["minimum_lines"]:
        errors.append(
            ValidationError(
                project_name,
                f"{file_path.parent.name}/{filename} is too short "
                f"({len(lines)} lines, expected at least {gate['minimum_lines']})",
            )
        )

    for heading in gate["required_headings"]:
        if heading not in text:
            errors.append(
                ValidationError(
                    project_name,
                    f"{file_path.parent.name}/{filename} missing heading: '{heading}'",
                )
            )

    if "```mermaid" not in text or gate["required_mermaid_hint"] not in text:
        errors.append(
            ValidationError(
                project_name,
                f"{file_path.parent.name}/{filename} must include Mermaid "
                f"'{gate['required_mermaid_hint']}' diagram",
            )
        )

    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            errors.append(
                ValidationError(
                    project_name,
                    f"{file_path.parent.name}/{filename} contains placeholder text matching '{pattern}'",
                )
            )

    if "minimum_table_rows" in gate:
        table_rows = sum(1 for line in lines if line.startswith("| ") and not line.startswith("|---"))
        if table_rows < gate["minimum_table_rows"]:
            errors.append(
                ValidationError(
                    project_name,
                    f"{file_path.parent.name}/{filename} has insufficient table rows "
                    f"({table_rows}, expected at least {gate['minimum_table_rows']})",
                )
            )

    if "minimum_numbered_rules" in gate:
        numbered_rules = sum(1 for line in lines if re.match(r"^\d+\.\s", line))
        if numbered_rules < gate["minimum_numbered_rules"]:
            errors.append(
                ValidationError(
                    project_name,
                    f"{file_path.parent.name}/{filename} has insufficient numbered rules "
                    f"({numbered_rules}, expected at least {gate['minimum_numbered_rules']})",
                )
            )


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
                        ValidationError(project_name, f"Missing file: {folder}/{filename}")
                    )
                    continue

                if file_path.stat().st_size == 0:
                    errors.append(
                        ValidationError(project_name, f"Empty file: {folder}/{filename}")
                    )
                    continue

                if folder == "analysis" and project_name in QUALITY_ENFORCED_PROJECTS:
                    _validate_analysis_quality(project_name, file_path, filename, errors)

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
