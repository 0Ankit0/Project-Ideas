# API Design — Customer Support and Contact Center Platform

## 1. Design Principles

| Principle | Implementation |
|-----------|----------------|
| REST Semantics | Resources are nouns; HTTP verbs (GET, POST, PATCH, DELETE) express intent. POST creates, PATCH applies partial updates, DELETE soft-deletes. |
| Versioning | URI-based major versioning (`/v1/`). Minor, non-breaking changes are additive and unversioned. Breaking changes increment the version with a 90-day migration window. |
| Idempotency | All mutating endpoints accept an `Idempotency-Key` header (UUID v4). Server stores results keyed by `(client_id, idempotency_key)` for 24 hours and returns the cached response on replay. |
| Error Envelope | All errors return a consistent JSON envelope with `error.code`, `error.message`, `error.details[]`, and `doc_url`. HTTP status codes align with RFC 9110. |
| Pagination | List endpoints support cursor-based pagination by default; page-based available for exports. Cursor is opaque and stable within a result set for 10 minutes. |
| Rate Limiting | Token-bucket per `(client_id, endpoint_group)`. Headers `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` returned on every response. |
| Content Negotiation | `Accept: application/json` required. `Content-Type: application/json` required for request bodies. Attachment uploads use `multipart/form-data`. |
| Distributed Tracing | Every request accepts `X-Request-ID` and `X-Correlation-ID`; both are echoed in the response and propagated to downstream services via OpenTelemetry context propagation. |
| Deprecation | Deprecated endpoints include `Deprecation` and `Sunset` response headers (RFC 8594). Removal notices published 90 days in advance via changelog and email to registered developers. |

---

## 2. Base URL and Versioning

```
Production:  https://api.support.example.com/v1/
Staging:     https://api-staging.support.example.com/v1/
Sandbox:     https://api-sandbox.support.example.com/v1/
```

All endpoints are relative to the base URL. The version segment (`v1`) is mandatory. Requests to the non-versioned root (`/`) return `301 Moved Permanently` to the latest stable version.

### 2.1 Version Lifecycle

| Version | Status | Sunset Date |
|---------|--------|-------------|
| v1 | Current — GA | — |
| v0 | Deprecated | 2025-06-30 |

---

## 3. Request / Response Envelope

### 3.1 Success — Single Resource

```json
{
  "data": {
    "id": "tkt_01HXZ8K3P2V6F4RJQM7NGBD5W",
    "type": "ticket",
    "attributes": {
      "subject": "Cannot reset password",
      "status": "open"
    }
  },
  "_links": {
    "self": "https://api.support.example.com/v1/tickets/tkt_01HXZ8K3P2V6F4RJQM7NGBD5W",
    "assignee": "https://api.support.example.com/v1/agents/agt_02ABC",
    "queue": "https://api.support.example.com/v1/queues/que_03DEF"
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2024-07-01T10:23:45Z"
  }
}
```

### 3.2 Success — List Resource

```json
{
  "data": [
    { "id": "tkt_01HXZ8K3P2V6F4RJQM7NGBD5W", "type": "ticket", "attributes": {} },
    { "id": "tkt_01HXZ8K3P2V6F4RJQM7NGBD5X", "type": "ticket", "attributes": {} }
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6InRrdF8wMUhYWjhLM1AyVjZGNFJKUU03TkdCRDVXIn0",
    "prev_cursor": null,
    "has_more": true,
    "total_count": 1842
  },
  "meta": {
    "request_id": "req_abc124",
    "timestamp": "2024-07-01T10:23:45Z",
    "filter_applied": { "status": "open", "priority": "high" }
  }
}
```

### 3.3 Error Envelope

```json
{
  "error": {
    "code": "TICKET_NOT_FOUND",
    "message": "No ticket was found with the supplied identifier.",
    "details": [
      {
        "field": "ticketId",
        "issue": "Resource tkt_00NONEXISTENT does not exist or has been deleted.",
        "location": "path"
      }
    ],
    "doc_url": "https://docs.support.example.com/errors/TICKET_NOT_FOUND"
  },
  "meta": {
    "request_id": "req_abc125",
    "timestamp": "2024-07-01T10:23:46Z"
  }
}
```

---

## 4. Authentication

The API supports three authentication schemes. All requests must use HTTPS. Plaintext HTTP returns `301 Moved Permanently`.

| Scheme | Header | Format | Use Case |
|--------|--------|--------|----------|
| Bearer Token (OAuth 2.0 / OIDC) | `Authorization` | `Bearer <access_token>` | Interactive agent/admin UIs |
| API Key | `X-Api-Key` | `<api_key>` | Server-to-server / integrations |
| Session Token | `X-Session-Token` | `<session_token>` | Widget / customer-facing portals |

### 4.1 OAuth 2.0 Scopes

| Scope | Description |
|-------|-------------|
| `tickets:read` | Read ticket data |
| `tickets:write` | Create and mutate tickets |
| `tickets:delete` | Soft-delete tickets |
| `contacts:read` | Read contact data |
| `contacts:write` | Create and mutate contacts |
| `contacts:gdpr` | Initiate GDPR erasure workflows |
| `agents:read` | Read agent profiles |
| `agents:write` | Manage agent configuration |
| `kb:read` | Read knowledge base articles |
| `kb:write` | Author and publish KB articles |
| `analytics:read` | Access reporting and analytics |
| `workforce:read` | Read schedules and shifts |
| `workforce:write` | Manage schedules and shifts |
| `admin` | Unrestricted access (super-admin only) |

---

## 5. Pagination

### 5.1 Cursor-Based Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cursor` | string | — | Opaque cursor from previous response `pagination.next_cursor` |
| `limit` | integer | 25 | Records per page. Max: 100 |
| `direction` | string | `next` | `next` or `prev` |

### 5.2 Page-Based Parameters (Export / Batch)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | 1-indexed page number |
| `per_page` | integer | 25 | Records per page. Max: 500 |

Cursors are stable for 10 minutes after generation. Stale cursors return `410 Gone`.

---

## 6. Rate Limiting

### 6.1 Response Headers

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Total requests allowed in the current window |
| `X-RateLimit-Remaining` | Requests remaining in the current window |
| `X-RateLimit-Reset` | Unix timestamp when the window resets |
| `X-RateLimit-Retry-After` | Seconds to wait before retrying (only on 429) |

### 6.2 Limits by Endpoint Group

| Endpoint Group | Limit | Window |
|----------------|-------|--------|
| Tickets (read) | 600 req | 1 min |
| Tickets (write) | 120 req | 1 min |
| Messages (read) | 600 req | 1 min |
| Messages (write) | 300 req | 1 min |
| Contacts | 300 req | 1 min |
| Agents | 300 req | 1 min |
| Analytics | 60 req | 1 min |
| Attachments upload | 60 req | 1 min |
| Knowledge Base | 300 req | 1 min |
| Webhooks / Events | 120 req | 1 min |
| Workforce | 120 req | 1 min |
| Bot Sessions | 600 req | 1 min |

---

## 7. Complete Endpoint Reference

---

### 7.1 Tickets API

**Base path:** `/v1/tickets`

| Method | Path | Description | Required Scope |
|--------|------|-------------|----------------|
| GET | `/v1/tickets` | List / search tickets with filters | `tickets:read` |
| POST | `/v1/tickets` | Create a new ticket | `tickets:write` |
| GET | `/v1/tickets/{ticketId}` | Get a single ticket | `tickets:read` |
| PATCH | `/v1/tickets/{ticketId}` | Partially update a ticket | `tickets:write` |
| DELETE | `/v1/tickets/{ticketId}` | Soft-delete a ticket | `tickets:delete` |
| POST | `/v1/tickets/{ticketId}/assign` | Assign ticket to an agent | `tickets:write` |
| POST | `/v1/tickets/{ticketId}/unassign` | Remove current assignee | `tickets:write` |
| POST | `/v1/tickets/{ticketId}/escalate` | Escalate ticket | `tickets:write` |
| POST | `/v1/tickets/{ticketId}/merge` | Merge another ticket into this one | `tickets:write` |
| POST | `/v1/tickets/{ticketId}/split` | Split selected messages into a new ticket | `tickets:write` |
| GET | `/v1/tickets/{ticketId}/timeline` | Full chronological activity feed | `tickets:read` |
| POST | `/v1/tickets/{ticketId}/tags` | Add tags to a ticket | `tickets:write` |

#### GET /v1/tickets — Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string (csv) | Filter: `new`, `open`, `pending`, `on_hold`, `resolved`, `closed` |
| `priority` | string (csv) | `low`, `medium`, `high`, `urgent`, `critical` |
| `queue_id` | string (csv) | One or more queue IDs |
| `assignee_id` | string | Agent ID of current assignee |
| `channel_id` | string (csv) | Channel IDs |
| `contact_id` | string | Filter by contact |
| `tags` | string (csv) | Must include ALL listed tags |
| `created_after` | ISO 8601 | Lower bound on `created_at` |
| `created_before` | ISO 8601 | Upper bound on `created_at` |
| `sort` | string | `created_at:asc`, `created_at:desc`, `priority:desc`, `updated_at:desc` |
| `cursor` | string | Pagination cursor |
| `limit` | integer | Page size (default 25, max 100) |

#### POST /v1/tickets — Request Schema

```json
{
  "subject": "Cannot reset password — locked out",
  "channel_id": "chn_email_01",
  "contact_id": "cnt_01HXZ9A1B2C3D4E5F6G7H8I9J",
  "queue_id": "que_01HXZ9A1B2C3D4E5F6G7H8I9K",
  "priority": "high",
  "tags": ["billing", "urgent"],
  "custom_fields": {
    "account_tier": "enterprise",
    "product_area": "authentication"
  },
  "first_message": {
    "body_html": "<p>I have been unable to reset my password for the last 24 hours.</p>",
    "body_text": "I have been unable to reset my password for the last 24 hours.",
    "attachments": ["att_01HXZ9A1B2C3D4E5F6"]
  },
  "source_metadata": {
    "external_id": "ZD-12345",
    "source_system": "zendesk_migration"
  }
}
```

**Field Definitions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subject` | string | Yes | Ticket subject (max 500 chars) |
| `channel_id` | string | Yes | Channel the ticket originated from |
| `contact_id` | string | Yes | Contact who raised the ticket |
| `queue_id` | string | No | Target queue; routing rules apply if omitted |
| `priority` | enum | No | Default: `medium` |
| `tags` | string[] | No | Tag slugs to attach |
| `custom_fields` | object | No | Tenant-defined field values |
| `first_message.body_html` | string | No | HTML body of the opening message |
| `first_message.body_text` | string | No | Plain-text body of the opening message |
| `first_message.attachments` | string[] | No | Pre-uploaded attachment IDs |
| `source_metadata.external_id` | string | No | ID in originating external system |
| `source_metadata.source_system` | string | No | Name of originating system |

#### POST /v1/tickets — Response (201 Created)

```json
{
  "data": {
    "id": "tkt_01HXZ8K3P2V6F4RJQM7NGBD5W",
    "type": "ticket",
    "attributes": {
      "subject": "Cannot reset password — locked out",
      "status": "new",
      "priority": "high",
      "channel_id": "chn_email_01",
      "queue_id": "que_01HXZ9A1B2C3D4E5F6G7H8I9K",
      "contact_id": "cnt_01HXZ9A1B2C3D4E5F6G7H8I9J",
      "assignee_id": null,
      "tags": ["billing", "urgent"],
      "custom_fields": {
        "account_tier": "enterprise",
        "product_area": "authentication"
      },
      "sla_policy_id": "sla_01HXZ9A1B2C3D4E5F6",
      "first_response_due_at": "2024-07-01T14:23:45Z",
      "resolution_due_at": "2024-07-02T10:23:45Z",
      "created_at": "2024-07-01T10:23:45Z",
      "updated_at": "2024-07-01T10:23:45Z",
      "deleted_at": null
    }
  },
  "_links": {
    "self": "https://api.support.example.com/v1/tickets/tkt_01HXZ8K3P2V6F4RJQM7NGBD5W",
    "threads": "https://api.support.example.com/v1/tickets/tkt_01HXZ8K3P2V6F4RJQM7NGBD5W/threads",
    "timeline": "https://api.support.example.com/v1/tickets/tkt_01HXZ8K3P2V6F4RJQM7NGBD5W/timeline",
    "sla_status": "https://api.support.example.com/v1/tickets/tkt_01HXZ8K3P2V6F4RJQM7NGBD5W/sla-status"
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2024-07-01T10:23:45Z"
  }
}
```

#### PATCH /v1/tickets/{ticketId} — Request Schema

```json
{
  "status": "pending",
  "priority": "urgent",
  "assignee_id": "agt_01HXZ9A1B2C3D4E5F6G7H8I9L",
  "queue_id": "que_01HXZ9A1B2C3D4E5F6G7H8I9K",
  "tags": ["billing", "urgent", "escalated"],
  "custom_fields": {
    "account_tier": "enterprise_plus"
  }
}
```

**Valid `status` transitions:**

| From | To (allowed) |
|------|-------------|
| `new` | `open`, `closed` |
| `open` | `pending`, `on_hold`, `resolved` |
| `pending` | `open`, `resolved` |
| `on_hold` | `open` |
| `resolved` | `closed`, `open` (re-open) |
| `closed` | `open` (re-open) |

#### POST /v1/tickets/{ticketId}/assign — Request Schema

```json
{
  "agent_id": "agt_01HXZ9A1B2C3D4E5F6G7H8I9L",
  "reason": "skill_match",
  "notify_agent": true
}
```

#### POST /v1/tickets/{ticketId}/escalate — Request Schema

```json
{
  "reason_code": "sla_breach_imminent",
  "severity": "critical",
  "target_queue_id": "que_escalation_01",
  "target_agent_id": "agt_senior_01",
  "notes": "Customer is enterprise-tier; SLA breach in 15 minutes."
}
```

#### POST /v1/tickets/{ticketId}/merge — Request Schema

```json
{
  "source_ticket_id": "tkt_01HXZ8K3P2V6F4RJQM7NGBD5X",
  "strategy": "keep_target_thread_order"
}
```

---

### 7.2 Threads & Messages API

**Base path:** `/v1/tickets/{ticketId}/threads`

| Method | Path | Description | Required Scope |
|--------|------|-------------|----------------|
| GET | `/v1/tickets/{ticketId}/threads` | List threads in a ticket | `tickets:read` |
| POST | `/v1/tickets/{ticketId}/threads` | Create a new thread (reply, note, system) | `tickets:write` |
| GET | `/v1/tickets/{ticketId}/threads/{threadId}/messages` | List messages in a thread | `tickets:read` |
| POST | `/v1/tickets/{ticketId}/threads/{threadId}/messages` | Add a message to thread | `tickets:write` |
| GET | `/v1/tickets/{ticketId}/messages/{messageId}/attachments` | List attachments on a message | `tickets:read` |
| POST | `/v1/attachments` | Upload attachment (multipart/form-data) | `tickets:write` |

#### POST /v1/tickets/{ticketId}/threads — Request Schema

```json
{
  "type": "reply",
  "channel_id": "chn_email_01",
  "from": {
    "agent_id": "agt_01HXZ9A1B2C3D4E5F6G7H8I9L"
  },
  "recipients": {
    "to": ["customer@example.com"],
    "cc": ["manager@example.com"],
    "bcc": []
  },
  "subject": "Re: Cannot reset password — locked out",
  "body_html": "<p>We have reset your password. Please check your inbox.</p>",
  "body_text": "We have reset your password. Please check your inbox.",
  "attachments": ["att_01HXZ9A1B2C3D4E5F6"],
  "canned_response_id": "cr_01HXZ9A1B2C3D4E5F6G7H8I9M",
  "send_immediately": true
}
```

**Thread types:**

| Type | Description |
|------|-------------|
| `reply` | Outbound customer-facing response |
| `note` | Internal agent note (not sent to customer) |
| `system` | Automated system event (status change, routing, SLA alert) |
| `forward` | Forward thread content to an external party |
| `bot` | Message authored by a bot session |

#### POST /v1/tickets/{ticketId}/threads — Response (201 Created)

```json
{
  "data": {
    "id": "thr_01HXZ9A1B2C3D4E5F6G7H8I9R",
    "type": "ticket_thread",
    "attributes": {
      "ticket_id": "tkt_01HXZ8K3P2V6F4RJQM7NGBD5W",
      "thread_type": "reply",
      "author_type": "agent",
      "author_id": "agt_01HXZ9A1B2C3D4E5F6G7H8I9L",
      "subject": "Re: Cannot reset password — locked out",
      "created_at": "2024-07-01T10:45:00Z"
    }
  },
  "_links": {
    "self": "https://api.support.example.com/v1/tickets/tkt_.../threads/thr_01HXZ9A1B2C3D4E5F6G7H8I9R",
    "messages": "https://api.support.example.com/v1/tickets/tkt_.../threads/thr_.../messages"
  }
}
```

#### POST /v1/attachments — Request (multipart/form-data)

```
POST /v1/attachments
Content-Type: multipart/form-data; boundary=----boundary

------boundary
Content-Disposition: form-data; name="file"; filename="invoice.pdf"
Content-Type: application/pdf

<binary data>
------boundary
Content-Disposition: form-data; name="ticket_id"

tkt_01HXZ8K3P2V6F4RJQM7NGBD5W
------boundary--
```

**Response (201):**

```json
{
  "data": {
    "id": "att_01HXZ9A1B2C3D4E5F6",
    "filename": "invoice.pdf",
    "mime_type": "application/pdf",
    "size_bytes": 204800,
    "url": "https://cdn.support.example.com/attachments/att_01HXZ9A1B2C3D4E5F6",
    "expires_at": "2024-07-08T10:23:45Z",
    "created_at": "2024-07-01T10:23:45Z"
  }
}
```

**Allowed MIME types:** `image/png`, `image/jpeg`, `image/gif`, `image/webp`, `application/pdf`, `text/plain`, `text/csv`, `application/zip`, `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.

**Maximum file size:** 25 MB per file, 100 MB per ticket total.

---

### 7.3 Contacts API

**Base path:** `/v1/contacts`

| Method | Path | Description | Required Scope |
|--------|------|-------------|----------------|
| GET | `/v1/contacts` | Search / list contacts | `contacts:read` |
| POST | `/v1/contacts` | Create a contact | `contacts:write` |
| GET | `/v1/contacts/{contactId}` | Get single contact | `contacts:read` |
| PATCH | `/v1/contacts/{contactId}` | Update contact fields | `contacts:write` |
| GET | `/v1/contacts/{contactId}/tickets` | Tickets linked to this contact | `contacts:read` |
| GET | `/v1/contacts/{contactId}/timeline` | Full interaction history | `contacts:read` |
| POST | `/v1/contacts/{contactId}/merge` | Merge a duplicate contact into this one | `contacts:write` |
| POST | `/v1/contacts/{contactId}/gdpr-delete` | Initiate GDPR erasure | `contacts:gdpr` |

#### GET /v1/contacts — Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Full-text search across name, email, phone, company |
| `email` | string | Exact email match |
| `phone` | string | Exact phone match |
| `external_id` | string | External CRM ID |
| `tags` | string (csv) | Must include all listed tags |
| `created_after` | ISO 8601 | Lower bound on `created_at` |
| `cursor` | string | Pagination cursor |
| `limit` | integer | Page size (default 25, max 100) |

#### POST /v1/contacts — Request Schema

```json
{
  "name": "Alice Johnson",
  "email": "alice@example.com",
  "phone": "+14155550100",
  "company": "Acme Corp",
  "external_id": "crm_000123",
  "tags": ["vip", "enterprise"],
  "custom_fields": {
    "account_number": "ACC-9988",
    "region": "us-west"
  },
  "locale": "en-US",
  "timezone": "America/Los_Angeles"
}
```

#### POST /v1/contacts/{contactId}/merge — Request Schema

```json
{
  "source_contact_id": "cnt_01HXZ9DUPLICATE",
  "strategy": "keep_target_fields"
}
```

Merge strategies: `keep_target_fields` (target contact's data wins), `keep_source_fields` (source data overrides), `merge_fields` (non-null source fields fill empty target fields). All tickets, threads, and history from the source contact are re-parented to the target. The source contact is soft-deleted.

#### POST /v1/contacts/{contactId}/gdpr-delete — Response (202 Accepted)

```json
{
  "data": {
    "job_id": "gdpr_job_01HXZ9A1B2C3D4E5",
    "status": "queued",
    "contact_id": "cnt_01HXZ9A1B2C3D4E5F6G7H8I9J",
    "estimated_completion_at": "2024-07-01T12:23:45Z"
  },
  "meta": {
    "request_id": "req_abc128",
    "timestamp": "2024-07-01T10:23:45Z"
  }
}
```

GDPR delete pseudonymises PII fields (`name`, `email`, `phone`), nullifies message content bodies, and retains anonymised audit records (required by law for up to 7 years).

---

### 7.4 Agents API

**Base path:** `/v1/agents`

| Method | Path | Description | Required Scope |
|--------|------|-------------|----------------|
| GET | `/v1/agents` | List agents | `agents:read` |
| POST | `/v1/agents` | Create agent account | `agents:write` |
| GET | `/v1/agents/{agentId}` | Get agent profile | `agents:read` |
| PATCH | `/v1/agents/{agentId}` | Update agent profile | `agents:write` |
| GET | `/v1/agents/{agentId}/skills` | List agent skills with proficiency | `agents:read` |
| POST | `/v1/agents/{agentId}/skills` | Add or update agent skills | `agents:write` |
| DELETE | `/v1/agents/{agentId}/skills/{skillId}` | Remove a skill from an agent | `agents:write` |
| PATCH | `/v1/agents/{agentId}/status` | Update availability status | `agents:write` |
| GET | `/v1/agents/{agentId}/metrics` | Performance metrics for a date range | `analytics:read` |

#### POST /v1/agents — Request Schema

```json
{
  "email": "bob.smith@support.example.com",
  "name": "Bob Smith",
  "role": "agent",
  "team_id": "team_01HXZ9A1B2C3D4E5F6G7H8",
  "skills": [
    { "skill_id": "skl_billing", "proficiency": 4 },
    { "skill_id": "skl_technical", "proficiency": 3 }
  ],
  "max_concurrent_tickets": 10,
  "timezone": "Europe/London",
  "locale": "en-GB"
}
```

Agent roles: `agent`, `team_lead`, `supervisor`, `admin`.

#### PATCH /v1/agents/{agentId}/status — Request Schema

```json
{
  "status": "away",
  "reason": "lunch_break",
  "until": "2024-07-01T13:00:00Z"
}
```

Valid statuses: `online`, `away`, `busy`, `offline`, `break`. Changing to `offline` reassigns in-flight tickets according to the queue's routing strategy.

#### GET /v1/agents/{agentId}/metrics — Response

```json
{
  "data": {
    "agent_id": "agt_01HXZ9A1B2C3D4E5F6G7H8I9L",
    "period": { "start": "2024-07-01T00:00:00Z", "end": "2024-07-31T23:59:59Z" },
    "metrics": {
      "tickets_handled": 312,
      "avg_first_response_minutes": 12.4,
      "avg_resolution_minutes": 248.7,
      "sla_compliance_rate": 0.972,
      "csat_average": 4.6,
      "reopen_rate": 0.032,
      "avg_handle_time_minutes": 18.3,
      "online_hours": 164.5
    }
  }
}
```

---

### 7.5 Queues & Routing API

**Base path:** `/v1/queues`

| Method | Path | Description | Required Scope |
|--------|------|-------------|----------------|
| GET | `/v1/queues` | List all queues | `agents:read` |
| POST | `/v1/queues` | Create a queue | `admin` |
| GET | `/v1/queues/{queueId}` | Get queue detail | `agents:read` |
| PATCH | `/v1/queues/{queueId}` | Update queue configuration | `admin` |
| GET | `/v1/queues/{queueId}/tickets` | Tickets currently in this queue | `tickets:read` |
| GET | `/v1/queues/{queueId}/agents` | Agents assigned to this queue | `agents:read` |
| POST | `/v1/routing-rules` | Create a routing rule | `admin` |
| GET | `/v1/routing-rules` | List routing rules ordered by priority | `agents:read` |
| PATCH | `/v1/routing-rules/{ruleId}` | Update a routing rule | `admin` |

#### POST /v1/queues — Request Schema

```json
{
  "name": "Billing Support",
  "description": "Handles all billing and payment enquiries",
  "sla_policy_id": "sla_01HXZ9A1B2C3D4E5F6",
  "routing_strategy": "skill_based",
  "max_capacity": 500,
  "overflow_queue_id": "que_overflow_01",
  "skills_required": ["skl_billing"],
  "business_hours_id": "bh_01HXZ9A1B2C3D4E5F6"
}
```

Routing strategies: `round_robin`, `least_active`, `skill_based`, `manual`.

#### POST /v1/routing-rules — Request Schema

```json
{
  "name": "VIP contact routes to Priority queue",
  "priority_order": 10,
  "conditions": [
    { "field": "contact.tags", "operator": "contains", "value": "vip" },
    { "field": "ticket.channel_id", "operator": "eq", "value": "chn_email_01" }
  ],
  "condition_logic": "ALL",
  "actions": [
    { "type": "set_queue", "value": "que_vip_01" },
    { "type": "set_priority", "value": "high" },
    { "type": "assign_agent", "value": "agt_dedicated_01" }
  ],
  "enabled": true
}
```

Supported condition operators: `eq`, `neq`, `contains`, `not_contains`, `starts_with`, `in`, `not_in`, `gt`, `lt`.

Supported action types: `set_queue`, `set_priority`, `assign_agent`, `assign_team`, `add_tag`, `set_sla_policy`, `send_auto_reply`.

---

### 7.6 SLA Policies API

**Base path:** `/v1/sla-policies`

| Method | Path | Description | Required Scope |
|--------|------|-------------|----------------|
| GET | `/v1/sla-policies` | List SLA policies | `agents:read` |
| POST | `/v1/sla-policies` | Create an SLA policy | `admin` |
| GET | `/v1/sla-policies/{policyId}` | Get SLA policy detail | `agents:read` |
| PATCH | `/v1/sla-policies/{policyId}` | Update SLA policy | `admin` |
| GET | `/v1/tickets/{ticketId}/sla-status` | Real-time SLA clock status for a ticket | `tickets:read` |

#### POST /v1/sla-policies — Request Schema

```json
{
  "name": "Enterprise SLA",
  "description": "For enterprise-tier customers — 24x5 coverage",
  "targets": [
    {
      "priority": "critical",
      "first_response_minutes": 15,
      "next_response_minutes": 60,
      "resolution_minutes": 240
    },
    {
      "priority": "high",
      "first_response_minutes": 60,
      "next_response_minutes": 240,
      "resolution_minutes": 480
    },
    {
      "priority": "medium",
      "first_response_minutes": 240,
      "next_response_minutes": 480,
      "resolution_minutes": 1440
    },
    {
      "priority": "low",
      "first_response_minutes": 480,
      "next_response_minutes": 960,
      "resolution_minutes": 2880
    }
  ],
  "business_hours_only": true,
  "business_hours_id": "bh_01HXZ9A1B2C3D4E5F6"
}
```

#### GET /v1/tickets/{ticketId}/sla-status — Response Schema

```json
{
  "data": {
    "ticket_id": "tkt_01HXZ8K3P2V6F4RJQM7NGBD5W",
    "policy_id": "sla_01HXZ9A1B2C3D4E5F6",
    "policy_name": "Enterprise SLA",
    "clocks": [
      {
        "type": "first_response",
        "status": "active",
        "target_at": "2024-07-01T11:23:45Z",
        "remaining_seconds": 3600,
        "elapsed_seconds": 0,
        "breached": false,
        "paused": false,
        "pause_reason": null,
        "warning_threshold_pct": 80,
        "in_warning": false
      },
      {
        "type": "resolution",
        "status": "active",
        "target_at": "2024-07-01T14:23:45Z",
        "remaining_seconds": 14400,
        "elapsed_seconds": 0,
        "breached": false,
        "paused": false,
        "pause_reason": null,
        "warning_threshold_pct": 80,
        "in_warning": false
      }
    ],
    "overall_status": "on_track"
  },
  "meta": {
    "evaluated_at": "2024-07-01T10:23:45Z",
    "request_id": "req_abc126"
  }
}
```

---

### 7.7 Knowledge Base API

**Base path:** `/v1/knowledge-base`

| Method | Path | Description | Required Scope |
|--------|------|-------------|----------------|
| GET | `/v1/knowledge-base/articles` | Search / list articles | `kb:read` |
| POST | `/v1/knowledge-base/articles` | Create a new article draft | `kb:write` |
| GET | `/v1/knowledge-base/articles/{articleId}` | Get single article | `kb:read` |
| PATCH | `/v1/knowledge-base/articles/{articleId}` | Update article draft | `kb:write` |
| POST | `/v1/knowledge-base/articles/{articleId}/publish` | Publish article | `kb:write` |
| POST | `/v1/knowledge-base/articles/{articleId}/feedback` | Submit helpfulness feedback | `kb:read` |
| GET | `/v1/knowledge-base/suggest` | AI article suggestions for a ticket | `kb:read` |

#### GET /v1/knowledge-base/articles — Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Full-text / semantic search query |
| `category_id` | string | Filter by category |
| `locale` | string | Language filter (e.g., `en-US`) |
| `status` | string | `draft`, `published`, `archived` |
| `sort` | string | `relevance`, `views:desc`, `updated_at:desc` |
| `cursor` | string | Pagination cursor |
| `limit` | integer | Page size (max 50) |

#### POST /v1/knowledge-base/articles — Request Schema

```json
{
  "kb_id": "kb_01HXZ9A1B2C3D4E5F6",
  "title": "How to Reset Your Password",
  "slug": "how-to-reset-password",
  "body_html": "<h2>Steps to reset your password</h2><ol><li>...</li></ol>",
  "body_text": "Steps to reset your password: 1. Navigate to the login page...",
  "locale": "en-US",
  "category_id": "cat_account_management",
  "keywords": ["password", "reset", "locked out", "forgotten"],
  "meta_description": "Step-by-step guide to resetting your account password."
}
```

#### GET /v1/knowledge-base/suggest — Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `ticket_id` | string | **Required.** Ticket ID to suggest articles for |
| `limit` | integer | Max suggestions (default 5, max 20) |

**Response (AI-powered article suggestion):**

```json
{
  "data": [
    {
      "article_id": "kba_01HXZ9A1B2C3D4E5",
      "title": "How to Reset Your Password",
      "relevance_score": 0.97,
      "excerpt": "To reset your password, navigate to the login page and click 'Forgot Password'...",
      "url": "https://help.example.com/articles/how-to-reset-password"
    },
    {
      "article_id": "kba_01HXZ9A1B2C3D4E6",
      "title": "Account Locked After Too Many Failed Attempts",
      "relevance_score": 0.89,
      "excerpt": "If your account is locked, please contact support or wait 30 minutes...",
      "url": "https://help.example.com/articles/account-locked"
    }
  ],
  "meta": {
    "model": "support-embedding-v2",
    "ticket_summary": "Customer cannot reset password and is locked out",
    "request_id": "req_abc127"
  }
}
```

---

### 7.8 Bots API

**Base path:** `/v1/bots`

| Method | Path | Description | Required Scope |
|--------|------|-------------|----------------|
| GET | `/v1/bots` | List bot configurations | `admin` |
| POST | `/v1/bots` | Create a bot configuration | `admin` |
| GET | `/v1/bots/{botId}` | Get bot detail | `admin` |
| GET | `/v1/bots/{botId}/flows` | List conversation flows | `admin` |
| POST | `/v1/bots/{botId}/flows` | Create a conversation flow | `admin` |
| POST | `/v1/bots/{botId}/sessions` | Start a new bot session | `tickets:write` |
| GET | `/v1/bots/{botId}/sessions/{sessionId}` | Get session state and transcript | `tickets:read` |
| POST | `/v1/bots/{botId}/sessions/{sessionId}/handoff` | Transfer to human agent | `tickets:write` |

#### POST /v1/bots/{botId}/sessions — Request Schema

```json
{
  "contact_id": "cnt_01HXZ9A1B2C3D4E5F6G7H8I9J",
  "channel_id": "chn_chat_widget_01",
  "initial_context": {
    "page_url": "https://example.com/pricing",
    "locale": "en-US",
    "custom_attrs": { "account_id": "ACC-9988" }
  },
  "flow_id": "flow_01HXZ9A1B2C3D4E5F6"
}
```

#### POST /v1/bots/{botId}/sessions/{sessionId}/handoff — Request Schema

```json
{
  "reason": "customer_requested",
  "target_queue_id": "que_01HXZ9A1B2C3D4E5F6G7H8I9K",
  "transcript_summary": "Customer asked about billing cycle change. Bot could not resolve the issue.",
  "context_payload": {
    "intent_detected": "billing_inquiry",
    "entities": { "billing_period": "monthly" },
    "confidence": 0.84
  }
}
```

Handoff reasons: `customer_requested`, `intent_not_recognised`, `max_turns_exceeded`, `sensitive_topic_detected`, `escalation_rule_triggered`.

---

### 7.9 Surveys API

**Base path:** `/v1/surveys`

| Method | Path | Description | Required Scope |
|--------|------|-------------|----------------|
| GET | `/v1/surveys` | List survey templates | `analytics:read` |
| POST | `/v1/surveys` | Create a survey template | `admin` |
| POST | `/v1/surveys/{surveyId}/dispatch` | Send survey to a list of tickets/contacts | `tickets:write` |
| GET | `/v1/surveys/{surveyId}/responses` | Paginated list of survey responses | `analytics:read` |
| POST | `/v1/survey-responses/{responseId}` | Submit survey answers (public endpoint, token-gated) | none |

#### POST /v1/surveys — Request Schema

```json
{
  "name": "Post-Resolution CSAT Survey",
  "type": "csat",
  "trigger_event": "ticket_closed",
  "delay_minutes": 30,
  "questions": [
    {
      "id": "q_csat",
      "type": "rating",
      "scale": 5,
      "text": "How satisfied were you with the support you received?"
    },
    {
      "id": "q_comment",
      "type": "text",
      "text": "Is there anything we could have done better?",
      "optional": true
    }
  ],
  "locale": "en-US",
  "expires_after_hours": 168
}
```

#### POST /v1/surveys/{surveyId}/dispatch — Request Schema

```json
{
  "ticket_ids": ["tkt_01HXZ8K3P2V6F4RJQM7NGBD5W"],
  "delay_minutes": 30,
  "channel": "email",
  "locale": "en-US"
}
```

#### POST /v1/survey-responses/{responseId} — Request Schema (Public)

```json
{
  "token": "srv_token_eyJhbGciOiJIUzI1NiJ9...",
  "answers": [
    { "question_id": "q_csat", "value": 5 },
    { "question_id": "q_comment", "value": "Great support, resolved very quickly!" }
  ]
}
```

---

### 7.10 Analytics API

**Base path:** `/v1/analytics`

| Method | Path | Description | Required Scope |
|--------|------|-------------|----------------|
| GET | `/v1/analytics/tickets/summary` | Aggregate ticket counts and averages | `analytics:read` |
| GET | `/v1/analytics/tickets/volume` | Time-series ticket volume | `analytics:read` |
| GET | `/v1/analytics/agents/performance` | Per-agent performance metrics | `analytics:read` |
| GET | `/v1/analytics/sla/compliance` | SLA compliance rates by queue / channel | `analytics:read` |
| GET | `/v1/analytics/csat/scores` | CSAT and NPS score trends | `analytics:read` |
| GET | `/v1/analytics/queues/real-time` | Live queue depth and agent availability snapshot | `analytics:read` |

#### GET /v1/analytics/tickets/summary — Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | ISO 8601 | Start of reporting window |
| `end_date` | ISO 8601 | End of reporting window |
| `queue_id` | string (csv) | Filter by queue(s) |
| `channel_id` | string (csv) | Filter by channel(s) |
| `group_by` | string | `queue`, `channel`, `priority`, `agent` |

**Response:**

```json
{
  "data": {
    "period": {
      "start": "2024-07-01T00:00:00Z",
      "end": "2024-07-31T23:59:59Z"
    },
    "summary": {
      "total_tickets": 4821,
      "tickets_opened": 1523,
      "tickets_closed": 1498,
      "avg_first_response_minutes": 18.4,
      "avg_resolution_minutes": 312.7,
      "sla_compliance_rate": 0.961,
      "csat_average": 4.3,
      "nps_score": 47,
      "reopen_rate": 0.041,
      "escalation_rate": 0.089
    },
    "breakdown": [
      {
        "group": "queue",
        "id": "que_billing_01",
        "name": "Billing Support",
        "tickets_opened": 412,
        "avg_first_response_minutes": 14.2,
        "sla_compliance_rate": 0.981
      }
    ]
  }
}
```

#### GET /v1/analytics/queues/real-time — Response

```json
{
  "data": [
    {
      "queue_id": "que_01HXZ9A1B2C3D4E5F6G7H8I9K",
      "queue_name": "Billing Support",
      "depth": 14,
      "agents_online": 5,
      "agents_busy": 4,
      "agents_available": 1,
      "oldest_ticket_age_minutes": 23,
      "avg_wait_minutes": 8.2,
      "tickets_breaching_sla": 2,
      "tickets_in_warning": 3
    }
  ],
  "meta": {
    "snapshot_at": "2024-07-01T10:23:45Z",
    "request_id": "req_abc130"
  }
}
```

---

### 7.11 Workforce Management API

**Base path:** `/v1/workforce`

| Method | Path | Description | Required Scope |
|--------|------|-------------|----------------|
| GET | `/v1/workforce/schedules` | List workforce schedules | `workforce:read` |
| POST | `/v1/workforce/schedules` | Create a schedule | `workforce:write` |
| GET | `/v1/workforce/schedules/{scheduleId}/shifts` | List shifts in a schedule | `workforce:read` |
| POST | `/v1/workforce/shifts` | Create a shift | `workforce:write` |
| PATCH | `/v1/workforce/shifts/{shiftId}` | Update a shift | `workforce:write` |
| GET | `/v1/workforce/agents/availability` | Real-time agent availability across queues | `workforce:read` |

#### POST /v1/workforce/schedules — Request Schema

```json
{
  "name": "EMEA Q3 2024 Schedule",
  "timezone": "Europe/London",
  "effective_from": "2024-07-01",
  "effective_to": "2024-09-30",
  "team_id": "team_01HXZ9A1B2C3D4E5F6G7H8"
}
```

#### POST /v1/workforce/shifts — Request Schema

```json
{
  "schedule_id": "sch_01HXZ9A1B2C3D4E5F6",
  "agent_id": "agt_01HXZ9A1B2C3D4E5F6G7H8I9L",
  "start_at": "2024-07-15T09:00:00Z",
  "end_at": "2024-07-15T17:00:00Z",
  "break_minutes": 60,
  "type": "regular"
}
```

Shift types: `regular`, `overtime`, `training`, `on_call`.

#### GET /v1/workforce/agents/availability — Response

```json
{
  "data": [
    {
      "agent_id": "agt_01HXZ9A1B2C3D4E5F6G7H8I9L",
      "name": "Bob Smith",
      "status": "online",
      "current_ticket_count": 6,
      "max_concurrent_tickets": 10,
      "capacity_pct": 0.60,
      "queues": ["que_billing_01", "que_general_01"],
      "skills": ["skl_billing", "skl_technical"],
      "shift_ends_at": "2024-07-01T17:00:00Z"
    }
  ],
  "meta": {
    "snapshot_at": "2024-07-01T10:23:45Z",
    "request_id": "req_abc131"
  }
}
```

---

## 8. Error Code Catalogue

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 404 | `TICKET_NOT_FOUND` | Ticket with given ID does not exist or was deleted |
| 422 | `TICKET_CLOSED_IMMUTABLE` | Closed tickets cannot be mutated; re-open first |
| 422 | `INVALID_STATUS_TRANSITION` | Requested status transition is not permitted by the state machine |
| 422 | `AGENT_NOT_AVAILABLE` | Agent is offline or at maximum concurrent ticket capacity |
| 422 | `QUEUE_CAPACITY_EXCEEDED` | Target queue has reached its maximum ticket capacity |
| 404 | `SLA_POLICY_NOT_FOUND` | SLA policy with given ID does not exist |
| 409 | `CONTACT_DUPLICATE_EMAIL` | A contact with this email address already exists in this organisation |
| 413 | `ATTACHMENT_TOO_LARGE` | Attachment exceeds the 25 MB maximum allowed size |
| 415 | `ATTACHMENT_MIME_NOT_ALLOWED` | MIME type is not in the allowed list for attachments |
| 409 | `SURVEY_ALREADY_DISPATCHED` | A survey has already been dispatched for this ticket |
| 410 | `BOT_SESSION_EXPIRED` | Bot session has expired; start a new session |
| 422 | `ROUTING_NO_AVAILABLE_AGENT` | No agents with required skills are currently online |
| 409 | `SLA_BREACH_ACKNOWLEDGED` | SLA breach has already been acknowledged |
| 202 | `GDPR_DELETE_IN_PROGRESS` | GDPR deletion job is already queued or running for this contact |
| 422 | `MERGE_SAME_TICKET` | Source and target ticket IDs must be different |
| 429 | `RATE_LIMIT_EXCEEDED` | Request rate limit exceeded; see `X-RateLimit-Retry-After` |
| 401 | `AUTHENTICATION_REQUIRED` | No valid authentication credential was provided |
| 403 | `INSUFFICIENT_SCOPE` | OAuth token lacks the required scope for this operation |
| 403 | `FORBIDDEN_RESOURCE` | Caller does not have permission to access this resource |
| 404 | `CONTACT_NOT_FOUND` | Contact with given ID does not exist |
| 404 | `AGENT_NOT_FOUND` | Agent with given ID does not exist |
| 404 | `QUEUE_NOT_FOUND` | Queue with given ID does not exist |
| 422 | `IDEMPOTENCY_KEY_CONFLICT` | Idempotency key reused with a different request payload |
| 422 | `SKILL_NOT_FOUND` | Skill with given ID does not exist |
| 422 | `THREAD_TYPE_INVALID` | Thread type not permitted for this ticket's channel |
| 422 | `KB_ARTICLE_ALREADY_PUBLISHED` | Article is already in published state; archive it before re-publishing |
| 422 | `SHIFT_OVERLAP` | This shift overlaps with an existing shift for the same agent |
| 422 | `ROUTING_RULE_CYCLE_DETECTED` | Routing rule actions would create a circular queue assignment |
| 503 | `SERVICE_UNAVAILABLE` | Downstream service is temporarily unavailable; retry with back-off |
| 504 | `UPSTREAM_TIMEOUT` | Upstream dependency did not respond within the timeout threshold |

---

## 9. Authorization Matrix

| Endpoint Group | Customer (Portal) | Agent | Team Lead | Supervisor | Admin |
|----------------|:-----------------:|:-----:|:---------:|:----------:|:-----:|
| Tickets — read own | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tickets — read all | ❌ | ✅ | ✅ | ✅ | ✅ |
| Tickets — create | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tickets — update | ❌ | ✅ | ✅ | ✅ | ✅ |
| Tickets — delete | ❌ | ❌ | ✅ | ✅ | ✅ |
| Tickets — escalate | ❌ | ✅ | ✅ | ✅ | ✅ |
| Contacts — read | ❌ | ✅ | ✅ | ✅ | ✅ |
| Contacts — write | ✅ (own) | ✅ | ✅ | ✅ | ✅ |
| Contacts — GDPR delete | ❌ | ❌ | ❌ | ✅ | ✅ |
| Agents — read | ❌ | ✅ (self) | ✅ (team) | ✅ | ✅ |
| Agents — write | ❌ | ✅ (self) | ✅ (team) | ✅ | ✅ |
| Queues — read | ❌ | ✅ | ✅ | ✅ | ✅ |
| Queues — write | ❌ | ❌ | ❌ | ✅ | ✅ |
| Routing Rules — read | ❌ | ✅ | ✅ | ✅ | ✅ |
| Routing Rules — write | ❌ | ❌ | ❌ | ✅ | ✅ |
| SLA Policies — read | ❌ | ✅ | ✅ | ✅ | ✅ |
| SLA Policies — write | ❌ | ❌ | ❌ | ✅ | ✅ |
| Knowledge Base — read | ✅ | ✅ | ✅ | ✅ | ✅ |
| Knowledge Base — write | ❌ | ✅ (draft) | ✅ | ✅ | ✅ |
| Knowledge Base — publish | ❌ | ❌ | ✅ | ✅ | ✅ |
| Analytics — read (own) | ❌ | ✅ | ✅ | ✅ | ✅ |
| Analytics — read (all) | ❌ | ❌ | ✅ (team) | ✅ | ✅ |
| Analytics — real-time queues | ❌ | ✅ | ✅ | ✅ | ✅ |
| Workforce — read (self) | ❌ | ✅ | ✅ | ✅ | ✅ |
| Workforce — read (team) | ❌ | ❌ | ✅ | ✅ | ✅ |
| Workforce — write | ❌ | ❌ | ✅ (team) | ✅ | ✅ |
| Bots — manage | ❌ | ❌ | ❌ | ❌ | ✅ |
| Bot Sessions — start | ✅ | ✅ | ✅ | ✅ | ✅ |
| Surveys — manage | ❌ | ❌ | ❌ | ✅ | ✅ |

---

## 10. Webhook Payload Contract

Webhooks are delivered via HTTP POST to a registered endpoint URL with `Content-Type: application/json`. Delivery is retried up to 5 times with exponential back-off (1s, 5s, 25s, 125s, 625s). After 5 failures, the webhook is disabled and the registered admin is notified.

Receivers must respond with HTTP `200` within 10 seconds. Non-200 responses or timeouts are treated as failures.

### 10.1 Standard Webhook Envelope

```json
{
  "event_id": "evt_01HXZ9A1B2C3D4E5F6G7H8I9N",
  "event_type": "ticket.created",
  "api_version": "v1",
  "org_id": "org_01HXZ9A1B2C3D4E5F6",
  "timestamp": "2024-07-01T10:23:45Z",
  "signature": "sha256=abc123def456ghi789jkl012mno345pqr678stu901",
  "data": {}
}
```

The `signature` is HMAC-SHA256 of the raw request body, keyed by the webhook secret. Receivers **must** verify this before processing. Example verification (Node.js):

```javascript
const crypto = require('crypto');
const expectedSig = 'sha256=' + crypto
  .createHmac('sha256', webhookSecret)
  .update(rawBody)
  .digest('hex');
if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expectedSig))) {
  return res.status(401).send('Invalid signature');
}
```

### 10.2 ticket.created

```json
{
  "event_id": "evt_01HXZ9A1B2C3D4E5F6G7H8I9N",
  "event_type": "ticket.created",
  "api_version": "v1",
  "org_id": "org_01HXZ9A1B2C3D4E5F6",
  "timestamp": "2024-07-01T10:23:45Z",
  "signature": "sha256=abc123def456...",
  "data": {
    "ticket": {
      "id": "tkt_01HXZ8K3P2V6F4RJQM7NGBD5W",
      "subject": "Cannot reset password — locked out",
      "status": "new",
      "priority": "high",
      "channel_id": "chn_email_01",
      "queue_id": "que_01HXZ9A1B2C3D4E5F6G7H8I9K",
      "contact_id": "cnt_01HXZ9A1B2C3D4E5F6G7H8I9J",
      "assignee_id": null,
      "tags": ["billing", "urgent"],
      "created_at": "2024-07-01T10:23:45Z"
    }
  }
}
```

### 10.3 ticket.status_changed

```json
{
  "event_id": "evt_01HXZ9A1B2C3D4E5F6G7H8I9P",
  "event_type": "ticket.status_changed",
  "api_version": "v1",
  "org_id": "org_01HXZ9A1B2C3D4E5F6",
  "timestamp": "2024-07-01T10:45:00Z",
  "signature": "sha256=def789ghi012...",
  "data": {
    "ticket_id": "tkt_01HXZ8K3P2V6F4RJQM7NGBD5W",
    "previous_status": "open",
    "new_status": "resolved",
    "changed_by": {
      "type": "agent",
      "id": "agt_01HXZ9A1B2C3D4E5F6G7H8I9L"
    },
    "changed_at": "2024-07-01T10:45:00Z"
  }
}
```

### 10.4 sla.breached

```json
{
  "event_id": "evt_01HXZ9A1B2C3D4E5F6G7H8I9Q",
  "event_type": "sla.breached",
  "api_version": "v1",
  "org_id": "org_01HXZ9A1B2C3D4E5F6",
  "timestamp": "2024-07-01T11:23:46Z",
  "signature": "sha256=ghi345jkl678...",
  "data": {
    "ticket_id": "tkt_01HXZ8K3P2V6F4RJQM7NGBD5W",
    "sla_policy_id": "sla_01HXZ9A1B2C3D4E5F6",
    "clock_type": "first_response",
    "target_at": "2024-07-01T11:23:45Z",
    "breached_at": "2024-07-01T11:23:46Z",
    "breach_duration_seconds": 1,
    "assignee_id": null,
    "queue_id": "que_01HXZ9A1B2C3D4E5F6G7H8I9K"
  }
}
```

### 10.5 Supported Event Types

| Event Type | Description |
|------------|-------------|
| `ticket.created` | New ticket created |
| `ticket.updated` | One or more ticket fields changed |
| `ticket.status_changed` | Ticket status transitioned |
| `ticket.assigned` | Ticket assigned to an agent |
| `ticket.unassigned` | Ticket assignee removed |
| `ticket.escalated` | Ticket escalated |
| `ticket.merged` | Two tickets merged |
| `ticket.deleted` | Ticket soft-deleted |
| `message.created` | New message added to a thread |
| `sla.warning` | SLA clock entered the warning threshold (configurable, default 80%) |
| `sla.breached` | SLA clock breached its target |
| `contact.created` | New contact created |
| `contact.updated` | Contact fields changed |
| `contact.gdpr_deleted` | Contact GDPR deletion completed |
| `agent.status_changed` | Agent availability status changed |
| `bot.session_started` | Bot session initiated on a channel |
| `bot.handoff_requested` | Bot-to-human handoff triggered |
| `survey.dispatched` | CSAT/NPS survey dispatched |
| `survey.response_received` | Customer submitted a survey response |
