# REST API Design — Subscription Billing and Entitlements Platform

## Overview

This document specifies the complete REST API surface for the Subscription Billing and Entitlements Platform.

- **Base URL:** `https://api.billing.example.com/v1`
- **Protocol:** HTTPS only; HTTP redirects to HTTPS
- **Data Format:** JSON (`Content-Type: application/json`)
- **Timestamps:** ISO 8601 UTC (e.g., `2024-03-15T10:30:00Z`)
- **Amounts:** Integer cents in the specified currency (e.g., `4999` = $49.99 USD)
- **Currencies:** ISO 4217 three-letter codes (e.g., `USD`, `EUR`, `GBP`)

---

## Authentication

All endpoints require both authentication mechanisms:

| Header | Format | Description |
|--------|--------|-------------|
| `Authorization` | `Bearer {jwt_token}` | Short-lived JWT issued by the auth service. |
| `X-API-Key` | `{api_key}` | Long-lived API key scoped to an account or organization. |

**JWT Claims Required:**
```json
{
  "sub": "account_01HX3B9J4K",
  "org_id": "org_01HX3B9J4K",
  "scopes": ["billing:read", "billing:write"],
  "exp": 1711451400
}
```

---

## Idempotency

All `POST` requests that create or mutate resources **must** include an idempotency key:

```
Idempotency-Key: {unique_uuid_v4}
```

The platform caches idempotency keys for 24 hours. Replaying a request with the same key returns the original response without re-executing the operation.

---

## Rate Limiting

Every response includes rate-limiting headers:

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed per minute for this API key. |
| `X-RateLimit-Remaining` | Requests remaining in the current window. |
| `X-RateLimit-Reset` | Unix timestamp when the window resets. |

Rate limit exceeded returns `429 Too Many Requests` with a `Retry-After` header.

---

## Pagination

All list endpoints use cursor-based offset pagination:

**Query Parameters:** `?page=1&limit=20`

**Response Envelope:**
```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 143,
    "hasNext": true
  }
}
```

---

## Standard Error Format

```json
{
  "error": {
    "code": "SUBSCRIPTION_NOT_FOUND",
    "message": "No subscription found with id sub_01HX3B9J4K.",
    "details": {},
    "request_id": "req_9f3a2c1d"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_PLAN` | 422 | Referenced plan does not exist or is archived. |
| `PLAN_VERSION_NOT_PUBLISHED` | 422 | Plan version is not in Published state. |
| `SUBSCRIPTION_NOT_FOUND` | 404 | Subscription with given ID does not exist. |
| `SUBSCRIPTION_INVALID_STATE` | 422 | Requested operation is not valid for the current subscription state. |
| `PAYMENT_DECLINED` | 402 | Payment gateway declined the charge. |
| `PAYMENT_METHOD_NOT_FOUND` | 404 | Payment method with given ID does not exist. |
| `INSUFFICIENT_CREDIT` | 422 | Account has insufficient credit balance. |
| `COUPON_EXPIRED` | 422 | Coupon redemption window has passed. |
| `COUPON_REDEMPTION_LIMIT_REACHED` | 422 | Coupon has been redeemed the maximum number of times. |
| `ENTITLEMENT_EXCEEDED` | 429 | Feature usage limit reached. |
| `INVOICE_NOT_FOUND` | 404 | Invoice with given ID does not exist. |
| `INVOICE_ALREADY_FINALIZED` | 422 | Invoice is already in FINALIZED state and cannot be modified. |
| `INVOICE_ALREADY_VOIDED` | 422 | Invoice is already voided. |
| `DUPLICATE_IDEMPOTENCY_KEY` | 409 | A different request was made with this idempotency key. |
| `VALIDATION_ERROR` | 400 | Request body failed schema validation. |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication credentials. |
| `FORBIDDEN` | 403 | Authenticated user lacks required scope. |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests. |
| `INTERNAL_ERROR` | 500 | Unexpected server error. |

---

## Plans

### GET /plans

List all plans with optional filtering.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number (default: 1). |
| `limit` | integer | Records per page (default: 20, max: 100). |
| `status` | string | Filter by status: `active`, `archived`. |

**Response 200:**
```json
{
  "data": [
    {
      "id": "plan_01HX3B9J4K",
      "name": "Pro",
      "slug": "pro",
      "status": "active",
      "currency": "USD",
      "billing_interval": "monthly",
      "trial_days": 14,
      "current_version_id": "planver_01HX3B9J4K",
      "created_at": "2024-01-10T09:00:00Z",
      "updated_at": "2024-03-01T12:00:00Z"
    }
  ],
  "pagination": { "page": 1, "limit": 20, "total": 5, "hasNext": false }
}
```

---

### POST /plans

Create a new plan. The first version is created automatically in `Draft` state.

**Request:**
```json
{
  "name": "Pro",
  "slug": "pro",
  "currency": "USD",
  "billing_interval": "monthly",
  "trial_days": 14,
  "description": "Best for growing teams",
  "metadata": { "tier": "mid" }
}
```

**Response 201:**
```json
{
  "id": "plan_01HX3B9J4K",
  "name": "Pro",
  "slug": "pro",
  "status": "active",
  "currency": "USD",
  "billing_interval": "monthly",
  "trial_days": 14,
  "current_version_id": "planver_01HX3B9J4K",
  "created_at": "2024-03-15T10:30:00Z",
  "updated_at": "2024-03-15T10:30:00Z"
}
```

---

### GET /plans/{planId}

**Response 200:** Single plan object (same schema as list item).

---

### PUT /plans/{planId}

Update plan metadata. Does not modify prices or features (use plan versions for that).

**Request:**
```json
{
  "name": "Pro Plus",
  "description": "Expanded features for growing teams",
  "trial_days": 30
}
```

**Response 200:** Updated plan object.

---

### POST /plans/{planId}/archive

Archive a plan. Existing subscriptions on this plan are unaffected.

**Response 200:**
```json
{ "id": "plan_01HX3B9J4K", "status": "archived" }
```

---

### GET /plans/{planId}/versions

**Response 200:**
```json
{
  "data": [
    {
      "id": "planver_01HX3B9J4K",
      "plan_id": "plan_01HX3B9J4K",
      "version_number": 2,
      "status": "published",
      "prices": [
        {
          "id": "price_01HX3B9J4K",
          "billing_interval": "monthly",
          "amount": 4999,
          "currency": "USD",
          "pricing_model": "flat",
          "metric_name": null
        }
      ],
      "features": [
        { "key": "api_calls", "limit": 100000, "overage_policy": "metered" },
        { "key": "seats", "limit": 10, "overage_policy": "hard_cap" }
      ],
      "published_at": "2024-02-01T00:00:00Z",
      "deprecated_at": null,
      "created_at": "2024-01-28T14:00:00Z"
    }
  ],
  "pagination": { "page": 1, "limit": 20, "total": 2, "hasNext": false }
}
```

---

### POST /plans/{planId}/versions

Create a new draft version for the plan.

**Request:**
```json
{
  "prices": [
    {
      "billing_interval": "monthly",
      "amount": 5999,
      "currency": "USD",
      "pricing_model": "flat"
    },
    {
      "billing_interval": "monthly",
      "metric_name": "api_calls",
      "pricing_model": "tiered",
      "tiers": [
        { "up_to": 10000, "unit_amount": 0 },
        { "up_to": 100000, "unit_amount": 2 },
        { "up_to": null, "unit_amount": 1 }
      ]
    }
  ],
  "features": [
    { "key": "api_calls", "limit": 200000, "overage_policy": "metered" },
    { "key": "seats", "limit": 20, "overage_policy": "hard_cap" }
  ]
}
```

**Response 201:** New plan version object in `draft` status.

---

### GET /plans/{planId}/versions/{versionId}

**Response 200:** Single plan version object.

---

## Subscriptions

### POST /subscriptions

Create a new subscription. If the plan has trial days configured, the subscription starts in `TRIALING` state.

**Request:**
```json
{
  "account_id": "acct_01HX3B9J4K",
  "plan_id": "plan_01HX3B9J4K",
  "plan_version_id": "planver_01HX3B9J4K",
  "payment_method_id": "pm_01HX3B9J4K",
  "coupon_code": "SUMMER20",
  "billing_anchor_day": 1,
  "metadata": { "salesforce_opportunity_id": "SF-123" }
}
```

**Response 201:**
```json
{
  "id": "sub_01HX3B9J4K",
  "account_id": "acct_01HX3B9J4K",
  "plan_id": "plan_01HX3B9J4K",
  "plan_version_id": "planver_01HX3B9J4K",
  "status": "trialing",
  "current_period_start": "2024-03-15T00:00:00Z",
  "current_period_end": "2024-03-29T00:00:00Z",
  "trial_end": "2024-03-29T00:00:00Z",
  "cancel_at_period_end": false,
  "payment_method_id": "pm_01HX3B9J4K",
  "created_at": "2024-03-15T10:30:00Z"
}
```

---

### GET /subscriptions/{subscriptionId}

**Response 200:** Full subscription object.

---

### GET /subscriptions

**Query Parameters:** `?accountId`, `?status` (trialing/active/paused/past_due/cancelled), `?page`, `?limit`

**Response 200:** Paginated list of subscription objects.

---

### PATCH /subscriptions/{subscriptionId}

Update subscription (plan upgrade/downgrade, payment method change, billing anchor).

**Request:**
```json
{
  "plan_version_id": "planver_02HX3B9J4K",
  "payment_method_id": "pm_02HX3B9J4K",
  "proration_behavior": "create_prorations"
}
```

`proration_behavior` values: `create_prorations` | `none` | `always_invoice`

**Response 200:** Updated subscription object.

---

### POST /subscriptions/{subscriptionId}/cancel

**Request:**
```json
{
  "cancel_at_period_end": true,
  "cancellation_reason": "too_expensive",
  "cancellation_comment": "Budget constraints for Q2"
}
```

**Response 200:**
```json
{
  "id": "sub_01HX3B9J4K",
  "status": "active",
  "cancel_at_period_end": true,
  "cancelled_at": null,
  "current_period_end": "2024-04-15T00:00:00Z"
}
```

---

### POST /subscriptions/{subscriptionId}/pause

**Request:**
```json
{
  "pause_until": "2024-06-01T00:00:00Z",
  "behavior": "void_open_invoices"
}
```

`behavior` values: `void_open_invoices` | `mark_uncollectible`

**Response 200:**
```json
{ "id": "sub_01HX3B9J4K", "status": "paused", "pause_until": "2024-06-01T00:00:00Z" }
```

---

### POST /subscriptions/{subscriptionId}/resume

**Response 200:**
```json
{ "id": "sub_01HX3B9J4K", "status": "active", "pause_until": null }
```

---

### GET /subscriptions/{subscriptionId}/preview-invoice

Preview the proration invoice that would be generated for a pending plan change.

**Query Parameters:** `?newPlanVersionId=planver_02HX3B9J4K`

**Response 200:**
```json
{
  "preview": true,
  "subscription_id": "sub_01HX3B9J4K",
  "currency": "USD",
  "subtotal": 1666,
  "tax": 133,
  "total": 1799,
  "line_items": [
    {
      "description": "Remaining time on Pro (15 days)",
      "amount": -2499,
      "type": "proration_credit"
    },
    {
      "description": "Time on Enterprise (15 days)",
      "amount": 4165,
      "type": "proration_charge"
    }
  ]
}
```

---

## Usage

### POST /usage

Record a usage event.

**Request:**
```json
{
  "event_id": "evt_01HX3B9J4K",
  "subscription_id": "sub_01HX3B9J4K",
  "metric_name": "api_calls",
  "quantity": 25,
  "timestamp": "2024-03-15T10:30:00Z",
  "properties": {
    "endpoint": "/v1/completions",
    "model": "gpt-4"
  }
}
```

**Headers:** `Idempotency-Key: {event_id}` (recommended to match event_id)

**Response 202:**
```json
{
  "event_id": "evt_01HX3B9J4K",
  "status": "accepted",
  "duplicate": false
}
```

If duplicate: `status: "accepted"`, `duplicate: true` — same 202 response, no double-billing.

---

### GET /usage

**Query Parameters:** `?subscriptionId`, `?from` (ISO8601), `?to` (ISO8601), `?metric`, `?page`, `?limit`

**Response 200:** Paginated list of raw usage event records.

---

### GET /usage/aggregate

**Query Parameters:** `?subscriptionId` (required), `?from`, `?to`, `?metric`

**Response 200:**
```json
{
  "subscription_id": "sub_01HX3B9J4K",
  "period_start": "2024-03-01T00:00:00Z",
  "period_end": "2024-03-31T23:59:59Z",
  "aggregates": [
    {
      "metric_name": "api_calls",
      "aggregation": "SUM",
      "value": 87432,
      "unit": "calls"
    },
    {
      "metric_name": "storage_gb",
      "aggregation": "MAX",
      "value": 12,
      "unit": "GB"
    }
  ]
}
```

---

## Invoices

### GET /invoices

**Query Parameters:** `?accountId`, `?status` (draft/open/paid/void/uncollectible), `?from`, `?to`, `?page`, `?limit`

**Response 200:** Paginated list of invoice summaries.

---

### GET /invoices/{invoiceId}

**Response 200:**
```json
{
  "id": "inv_01HX3B9J4K",
  "account_id": "acct_01HX3B9J4K",
  "subscription_id": "sub_01HX3B9J4K",
  "status": "open",
  "currency": "USD",
  "subtotal": 4999,
  "discount_amount": 500,
  "credit_applied": 0,
  "tax_amount": 360,
  "total": 4859,
  "amount_due": 4859,
  "amount_paid": 0,
  "due_date": "2024-04-01T00:00:00Z",
  "period_start": "2024-03-15T00:00:00Z",
  "period_end": "2024-04-14T23:59:59Z",
  "pdf_url": "https://cdn.billing.example.com/invoices/inv_01HX3B9J4K.pdf",
  "created_at": "2024-03-15T10:30:00Z",
  "finalized_at": null
}
```

---

### POST /invoices/{invoiceId}/finalize

Lock an invoice and trigger payment collection.

**Response 200:**
```json
{ "id": "inv_01HX3B9J4K", "status": "open", "finalized_at": "2024-03-15T11:00:00Z" }
```

---

### POST /invoices/{invoiceId}/void

Void an open or uncollectible invoice.

**Request:**
```json
{ "reason": "duplicate_invoice" }
```

**Response 200:**
```json
{ "id": "inv_01HX3B9J4K", "status": "void", "voided_at": "2024-03-15T11:05:00Z" }
```

---

### GET /invoices/{invoiceId}/line-items

**Response 200:**
```json
{
  "data": [
    {
      "id": "li_01HX3B9J4K",
      "invoice_id": "inv_01HX3B9J4K",
      "type": "subscription",
      "description": "Pro Plan — March 2024",
      "quantity": 1,
      "unit_amount": 4999,
      "amount": 4999,
      "currency": "USD",
      "period_start": "2024-03-15T00:00:00Z",
      "period_end": "2024-04-14T23:59:59Z"
    },
    {
      "id": "li_02HX3B9J4K",
      "invoice_id": "inv_01HX3B9J4K",
      "type": "usage",
      "description": "API Calls — 87,432 calls",
      "quantity": 87432,
      "unit_amount": 1,
      "amount": 874,
      "currency": "USD",
      "metric_name": "api_calls"
    }
  ]
}
```

---

## Payments

### GET /payments

**Query Parameters:** `?invoiceId`, `?subscriptionId`, `?status`, `?page`, `?limit`

**Response 200:** Paginated list of payment attempts.

---

### GET /payments/{attemptId}

**Response 200:**
```json
{
  "id": "pay_01HX3B9J4K",
  "invoice_id": "inv_01HX3B9J4K",
  "subscription_id": "sub_01HX3B9J4K",
  "status": "failed",
  "gateway": "stripe",
  "gateway_payment_id": "pi_3MXkVz2eZvKYlo2C1234ABCD",
  "amount": 4859,
  "currency": "USD",
  "failure_code": "card_declined",
  "failure_message": "Your card was declined.",
  "attempted_at": "2024-03-15T11:30:00Z"
}
```

---

### POST /payments/{attemptId}/retry

Manually trigger a retry for a failed payment attempt.

**Response 202:**
```json
{ "id": "pay_02HX3B9J4K", "status": "pending", "invoice_id": "inv_01HX3B9J4K" }
```

---

## Payment Methods

### POST /payment-methods

Add a payment method via a gateway token.

**Request:**
```json
{
  "account_id": "acct_01HX3B9J4K",
  "gateway": "stripe",
  "gateway_token": "pm_1MXkVz2eZvKYlo2C1234ABCD",
  "set_as_default": true
}
```

**Response 201:**
```json
{
  "id": "pm_01HX3B9J4K",
  "account_id": "acct_01HX3B9J4K",
  "gateway": "stripe",
  "type": "card",
  "last_four": "4242",
  "brand": "visa",
  "exp_month": 12,
  "exp_year": 2026,
  "is_default": true,
  "created_at": "2024-03-15T10:30:00Z"
}
```

---

### GET /payment-methods

**Query Parameters:** `?accountId` (required), `?page`, `?limit`

**Response 200:** Paginated list of payment method objects.

---

### DELETE /payment-methods/{paymentMethodId}

**Response 204:** No content. Cannot delete a payment method that is the default on an active subscription unless another method is set as default first.

---

### POST /payment-methods/{paymentMethodId}/set-default

**Response 200:**
```json
{ "id": "pm_01HX3B9J4K", "is_default": true }
```

---

## Credits

### GET /credits

**Query Parameters:** `?accountId` (required), `?status` (active/expired/consumed), `?page`, `?limit`

**Response 200:**
```json
{
  "data": [
    {
      "id": "crd_01HX3B9J4K",
      "account_id": "acct_01HX3B9J4K",
      "amount": 5000,
      "currency": "USD",
      "remaining": 3200,
      "status": "active",
      "expires_at": "2024-12-31T23:59:59Z",
      "reason": "refund_credit",
      "created_at": "2024-03-15T10:30:00Z"
    }
  ],
  "pagination": { "page": 1, "limit": 20, "total": 1, "hasNext": false }
}
```

---

### POST /credits/apply

Apply credit to a specific invoice.

**Request:**
```json
{
  "account_id": "acct_01HX3B9J4K",
  "invoice_id": "inv_01HX3B9J4K",
  "amount": 3200
}
```

**Response 200:**
```json
{
  "invoice_id": "inv_01HX3B9J4K",
  "credit_applied": 3200,
  "remaining_balance": 0,
  "new_amount_due": 1659
}
```

---

## Credit Notes

### POST /credit-notes

Issue a credit note against a finalized invoice.

**Request:**
```json
{
  "invoice_id": "inv_01HX3B9J4K",
  "lines": [
    {
      "line_item_id": "li_01HX3B9J4K",
      "quantity": 1,
      "amount": 4999,
      "reason": "service_disruption"
    }
  ],
  "memo": "Downtime credit for March 10 outage"
}
```

**Response 201:**
```json
{
  "id": "cn_01HX3B9J4K",
  "invoice_id": "inv_01HX3B9J4K",
  "account_id": "acct_01HX3B9J4K",
  "status": "issued",
  "total": 4999,
  "currency": "USD",
  "memo": "Downtime credit for March 10 outage",
  "created_at": "2024-03-15T10:30:00Z"
}
```

---

### GET /credit-notes

**Query Parameters:** `?accountId`, `?invoiceId`, `?page`, `?limit`

**Response 200:** Paginated list of credit note objects.

---

### GET /credit-notes/{creditNoteId}

**Response 200:** Single credit note object with full line-item breakdown.

---

## Entitlements

### POST /entitlements/check

Check whether a subscription has access to a feature.

**Request:**
```json
{
  "subscription_id": "sub_01HX3B9J4K",
  "feature_key": "api_calls",
  "requested_quantity": 100
}
```

**Response 200:**
```json
{
  "subscription_id": "sub_01HX3B9J4K",
  "feature_key": "api_calls",
  "decision": "allowed",
  "limit": 100000,
  "used": 87432,
  "remaining": 12568,
  "overage_policy": "metered"
}
```

`decision` values: `allowed` | `denied` | `overage_allowed`

When denied:
```json
{
  "decision": "denied",
  "limit": 100000,
  "used": 100000,
  "remaining": 0,
  "overage_policy": "hard_cap"
}
```

---

### GET /entitlements

**Query Parameters:** `?subscriptionId` (required)

**Response 200:**
```json
{
  "data": [
    {
      "id": "ent_01HX3B9J4K",
      "subscription_id": "sub_01HX3B9J4K",
      "feature_key": "api_calls",
      "limit": 100000,
      "overage_policy": "metered",
      "status": "active",
      "granted_at": "2024-03-01T00:00:00Z",
      "revoked_at": null
    }
  ]
}
```

---

### POST /entitlements/grant

Manually grant an entitlement (e.g., for promotional access).

**Request:**
```json
{
  "subscription_id": "sub_01HX3B9J4K",
  "feature_key": "advanced_analytics",
  "limit": null,
  "overage_policy": "hard_cap",
  "expires_at": "2024-06-30T23:59:59Z"
}
```

**Response 201:** Created entitlement object.

---

### POST /entitlements/revoke

**Request:**
```json
{
  "subscription_id": "sub_01HX3B9J4K",
  "feature_key": "advanced_analytics"
}
```

**Response 200:**
```json
{ "feature_key": "advanced_analytics", "revoked_at": "2024-03-15T10:30:00Z" }
```

---

## Coupons

### POST /coupons

**Request:**
```json
{
  "code": "SUMMER20",
  "name": "Summer 2024 Promotion",
  "discount_type": "percentage",
  "discount_value": 20,
  "currency": null,
  "duration": "repeating",
  "duration_in_months": 3,
  "max_redemptions": 500,
  "applies_to_plan_ids": ["plan_01HX3B9J4K"],
  "valid_from": "2024-06-01T00:00:00Z",
  "valid_until": "2024-08-31T23:59:59Z"
}
```

`discount_type`: `percentage` | `fixed_amount`
`duration`: `once` | `forever` | `repeating`

**Response 201:** Created coupon object.

---

### GET /coupons

**Query Parameters:** `?status` (active/expired/archived), `?page`, `?limit`

**Response 200:** Paginated list of coupon objects.

---

### POST /coupons/validate

**Request:**
```json
{
  "code": "SUMMER20",
  "plan_id": "plan_01HX3B9J4K",
  "account_id": "acct_01HX3B9J4K"
}
```

**Response 200:**
```json
{
  "valid": true,
  "coupon": {
    "code": "SUMMER20",
    "discount_type": "percentage",
    "discount_value": 20,
    "duration": "repeating",
    "duration_in_months": 3,
    "redemptions_remaining": 487
  }
}
```

---

### POST /coupons/apply

**Request:**
```json
{
  "code": "SUMMER20",
  "subscription_id": "sub_01HX3B9J4K"
}
```

**Response 200:**
```json
{
  "subscription_id": "sub_01HX3B9J4K",
  "coupon_code": "SUMMER20",
  "applied_at": "2024-03-15T10:30:00Z",
  "discount_applies_until": "2024-06-15T00:00:00Z"
}
```

---

## Tax Rates

### GET /tax-rates

**Query Parameters:** `?jurisdictionId`, `?page`, `?limit`

**Response 200:**
```json
{
  "data": [
    {
      "id": "txr_01HX3B9J4K",
      "jurisdiction_id": "US-CA",
      "jurisdiction_name": "California, US",
      "rate": 0.0725,
      "tax_type": "sales_tax",
      "product_tax_code": "SW054111",
      "is_active": true,
      "effective_from": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

### POST /tax-rates

**Request:**
```json
{
  "jurisdiction_id": "US-CA",
  "jurisdiction_name": "California, US",
  "rate": 0.0725,
  "tax_type": "sales_tax",
  "product_tax_code": "SW054111",
  "effective_from": "2024-01-01T00:00:00Z"
}
```

**Response 201:** Created tax rate object.

---

## Dunning

### GET /dunning

**Query Parameters:** `?subscriptionId`, `?status` (active/resolved/exhausted), `?page`, `?limit`

**Response 200:**
```json
{
  "data": [
    {
      "id": "dun_01HX3B9J4K",
      "subscription_id": "sub_01HX3B9J4K",
      "invoice_id": "inv_01HX3B9J4K",
      "status": "active",
      "current_step": 2,
      "total_steps": 4,
      "next_retry_at": "2024-03-22T09:00:00Z",
      "started_at": "2024-03-15T11:30:00Z",
      "resolved_at": null
    }
  ]
}
```

---

### GET /dunning/{dunningCycleId}

**Response 200:** Full dunning cycle with step history:
```json
{
  "id": "dun_01HX3B9J4K",
  "subscription_id": "sub_01HX3B9J4K",
  "status": "active",
  "steps": [
    { "step": 1, "executed_at": "2024-03-15T11:30:00Z", "action": "retry_payment", "outcome": "failed" },
    { "step": 2, "scheduled_at": "2024-03-22T09:00:00Z", "action": "retry_payment", "outcome": null }
  ]
}
```

---

### POST /dunning/{dunningCycleId}/retry

Trigger an immediate manual retry outside the scheduled cadence.

**Response 202:**
```json
{ "dunning_cycle_id": "dun_01HX3B9J4K", "retry_triggered_at": "2024-03-16T10:00:00Z" }
```
