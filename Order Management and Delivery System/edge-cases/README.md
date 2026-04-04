# Edge Cases — Overview

## Scenario-to-Response Matrix

This directory contains detailed edge case analysis organised by domain area. Each document catalogues failure scenarios, boundary conditions, and the system's expected response.

| Document | Domain Area | Scenarios |
|---|---|---|
| [order-lifecycle-and-payment.md](order-lifecycle-and-payment.md) | Order state transitions, payment edge cases | Concurrent orders, payment failures, partial captures, modification after payment |
| [inventory-and-fulfillment.md](inventory-and-fulfillment.md) | Stock management, warehouse operations | Oversell prevention, split shipments, partial picks, reservation expiry |
| [delivery-and-proof.md](delivery-and-proof.md) | Delivery execution, POD capture | Failed attempts, POD upload failures, staff reassignment, customer unavailable |
| [returns-and-refunds.md](returns-and-refunds.md) | Return processing, refund edge cases | Return window boundaries, damaged goods, partial returns, refund failures |
| [api-and-ui.md](api-and-ui.md) | API behaviour, client handling | Rate limiting, pagination, timeout handling, concurrent mutations |
| [security-and-compliance.md](security-and-compliance.md) | Security threats, compliance | Token expiry, privilege escalation, PCI scope, data leaks |
| [operations.md](operations.md) | Operational failures, infrastructure | Service outages, DLQ overflow, database failover, capacity limits |

## Severity Classification

| Level | Definition | Response Time |
|---|---|---|
| **Critical** | Data loss, payment corruption, service down | Immediate (< 5 min) |
| **High** | Feature broken for many users, SLA breach | < 15 min |
| **Medium** | Degraded experience, workaround available | < 1 hour |
| **Low** | Cosmetic or rare edge case | Next business day |
