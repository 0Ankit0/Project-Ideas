# API Design

## Overview
This document describes the REST API architecture, conventions, and key endpoints for the Finance Management System.

---

## API Conventions

### Base URL and Versioning
All endpoints are versioned under `/api/v1`. Future breaking changes will be introduced under `/api/v2`.

### Authentication
All endpoints require JWT Bearer token authentication:
```
Authorization: Bearer <token>
```

Tokens are issued via `/api/v1/auth/login` and expire after 24 hours. Short-lived access tokens (1 hour) with refresh tokens (7 days) are used in production.

### Public IDs
Entity IDs are encoded as hashids at API boundaries. Internal integer PKs are never exposed.

### Pagination
List endpoints use cursor-based pagination:
```json
{
  "data": [],
  "pagination": {
    "total": 250,
    "page": 1,
    "per_page": 20,
    "has_next": true
  }
}
```

### Error Format
```json
{
  "success": false,
  "error": {
    "code": "PERIOD_CLOSED",
    "message": "Cannot post to a closed accounting period",
    "details": { "period_id": "abc123", "status": "HARD_CLOSED" }
  },
  "request_id": "req-xyz"
}
```

### Idempotency
Mutation endpoints (POST) accept an optional `Idempotency-Key` header. Repeated requests with the same key return the original response without re-processing. This is required for payment run submissions.

---

## Authentication Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Login with email and password; returns access and refresh tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token using refresh token |
| POST | `/api/v1/auth/logout` | Invalidate current session |
| POST | `/api/v1/auth/mfa/enable` | Enable MFA for current user |
| POST | `/api/v1/auth/mfa/verify` | Verify MFA OTP |
| GET | `/api/v1/auth/me` | Get current user profile and permissions |

---

## General Ledger Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/gl/chart-of-accounts` | List all accounts (filterable by type, status) |
| POST | `/api/v1/gl/chart-of-accounts` | Create a new account |
| PUT | `/api/v1/gl/chart-of-accounts/{id}` | Update account details |
| DELETE | `/api/v1/gl/chart-of-accounts/{id}` | Deactivate account (soft delete) |
| GET | `/api/v1/gl/journal-entries` | List journal entries (filterable by period, status) |
| POST | `/api/v1/gl/journal-entries` | Create a journal entry (saved as Draft) |
| GET | `/api/v1/gl/journal-entries/{id}` | Get journal entry detail with lines and attachments |
| POST | `/api/v1/gl/journal-entries/{id}/post` | Post a draft entry to the GL |
| POST | `/api/v1/gl/journal-entries/{id}/reverse` | Reverse a posted entry |
| GET | `/api/v1/gl/trial-balance` | Get trial balance for a period |
| GET | `/api/v1/gl/account-activity` | Get transaction history for a specific account |
| GET | `/api/v1/gl/periods` | List accounting periods |
| POST | `/api/v1/gl/periods/{id}/soft-close` | Initiate soft close |
| POST | `/api/v1/gl/periods/{id}/hard-close` | Hard-close a period (requires CFO approval) |

---

## Accounts Payable Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/ap/vendors` | List vendors (filterable by status) |
| POST | `/api/v1/ap/vendors` | Create vendor |
| PUT | `/api/v1/ap/vendors/{id}` | Update vendor |
| POST | `/api/v1/ap/vendors/{id}/approve` | Approve vendor onboarding |
| GET | `/api/v1/ap/invoices` | List vendor invoices (filterable by status, due date) |
| POST | `/api/v1/ap/invoices` | Record a vendor invoice |
| GET | `/api/v1/ap/invoices/{id}` | Get invoice detail |
| POST | `/api/v1/ap/invoices/{id}/submit` | Submit invoice for approval |
| POST | `/api/v1/ap/invoices/{id}/approve` | Approve invoice for payment |
| POST | `/api/v1/ap/invoices/{id}/reject` | Reject invoice |
| GET | `/api/v1/ap/invoices/aging` | Get AP aging report |
| GET | `/api/v1/ap/payment-runs` | List payment runs |
| POST | `/api/v1/ap/payment-runs` | Create payment run with selected invoices |
| POST | `/api/v1/ap/payment-runs/{id}/approve` | Approve and generate bank file |
| GET | `/api/v1/ap/payment-runs/{id}/bank-file` | Download generated bank file |

---

## Accounts Receivable Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/ar/customers` | List customers |
| POST | `/api/v1/ar/customers` | Create customer |
| GET | `/api/v1/ar/invoices` | List customer invoices |
| POST | `/api/v1/ar/invoices` | Create customer invoice |
| POST | `/api/v1/ar/invoices/{id}/send` | Send invoice to customer via email |
| GET | `/api/v1/ar/invoices/{id}/pdf` | Download invoice PDF |
| GET | `/api/v1/ar/invoices/aging` | Get AR aging report |
| POST | `/api/v1/ar/payments` | Record a customer payment |
| POST | `/api/v1/ar/payments/{id}/allocate` | Allocate payment to invoices |
| POST | `/api/v1/ar/invoices/{id}/write-off` | Write off invoice as bad debt |

---

## Budgeting & Forecasting Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/budgets` | List budgets |
| POST | `/api/v1/budgets` | Create a new budget |
| GET | `/api/v1/budgets/{id}` | Get budget detail with lines |
| PUT | `/api/v1/budgets/{id}/lines` | Update budget lines in bulk |
| POST | `/api/v1/budgets/{id}/submit` | Submit budget for FM approval |
| POST | `/api/v1/budgets/{id}/approve-fm` | Finance Manager approves budget |
| POST | `/api/v1/budgets/{id}/approve-cfo` | CFO approves budget |
| POST | `/api/v1/budgets/{id}/reject` | Return budget with rejection comments |
| GET | `/api/v1/budgets/{id}/variance` | Get budget vs. actuals variance report |
| GET | `/api/v1/budgets/utilization` | Get current budget utilization by cost center |
| GET | `/api/v1/budgets/forecast` | Get rolling forecast for current period |

---

## Expense Management Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/expenses` | List expense claims (own or team, with role filter) |
| POST | `/api/v1/expenses` | Submit a new expense claim |
| GET | `/api/v1/expenses/{id}` | Get expense claim detail |
| POST | `/api/v1/expenses/{id}/approve-dept` | Department Head approves claim |
| POST | `/api/v1/expenses/{id}/approve-fm` | Finance Manager approves claim |
| POST | `/api/v1/expenses/{id}/reject` | Reject expense claim with reason |
| GET | `/api/v1/expenses/policy-config` | Get expense policy limits per category |

---

## Payroll Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/payroll/employees` | List payroll employees |
| POST | `/api/v1/payroll/employees` | Create/import payroll employee |
| PUT | `/api/v1/payroll/employees/{id}` | Update payroll profile |
| GET | `/api/v1/payroll/runs` | List payroll runs |
| POST | `/api/v1/payroll/runs` | Initiate a new payroll run |
| POST | `/api/v1/payroll/runs/{id}/calculate` | Run payroll calculations |
| GET | `/api/v1/payroll/runs/{id}/register` | Get payroll register |
| POST | `/api/v1/payroll/runs/{id}/submit` | Submit for Finance Manager approval |
| POST | `/api/v1/payroll/runs/{id}/approve` | Approve payroll run |
| POST | `/api/v1/payroll/runs/{id}/disburse` | Generate and submit bank file |
| GET | `/api/v1/payroll/runs/{id}/pay-stubs/{employee_id}` | Download individual pay stub PDF |

---

## Fixed Assets Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/assets` | List fixed assets (filterable by category, status) |
| POST | `/api/v1/assets` | Register a new fixed asset |
| GET | `/api/v1/assets/{id}` | Get asset detail with depreciation schedule |
| PUT | `/api/v1/assets/{id}` | Update asset details |
| POST | `/api/v1/assets/{id}/dispose` | Dispose of an asset |
| POST | `/api/v1/assets/{id}/transfer` | Transfer asset to another department |
| GET | `/api/v1/assets/depreciation-schedule` | Get depreciation schedule for all assets |
| POST | `/api/v1/assets/depreciation/post` | Post period depreciation entries for all assets |

---

## Financial Reporting Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/reports/profit-and-loss` | Generate P&L for a period range |
| GET | `/api/v1/reports/balance-sheet` | Generate balance sheet as of a date |
| GET | `/api/v1/reports/cash-flow` | Generate cash flow statement |
| GET | `/api/v1/reports/trial-balance` | Get trial balance |
| GET | `/api/v1/reports/general-ledger` | Get GL detail report with full transaction history |
| POST | `/api/v1/reports/jobs` | Queue an async report job |
| GET | `/api/v1/reports/jobs/{id}` | Poll status of async report job |
| GET | `/api/v1/reports/jobs/{id}/download` | Download completed report artifact |

---

## Tax Management Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/tax/rates` | List configured tax rates |
| POST | `/api/v1/tax/rates` | Create a new tax rate |
| GET | `/api/v1/tax/liability` | Get tax liability report (input vs output) |
| POST | `/api/v1/tax/filings` | Submit a tax filing |
| GET | `/api/v1/tax/filings/{id}` | Get filing status and acknowledgment |
