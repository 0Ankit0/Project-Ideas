# API Design — Job Board and Recruitment Platform

## Overview

This document provides the full REST API specification for the Job Board and Recruitment Platform. All endpoints are versioned under `/v1`. The API follows REST conventions, uses JSON for request and response bodies, and returns standard HTTP status codes.

---

## Base URL

```
https://api.recruitplatform.io/v1
```

---

## Authentication

All protected endpoints require a Bearer JWT in the `Authorization` header.

```
Authorization: Bearer <jwt_token>
```

Tokens are issued by `POST /auth/login` and carry the following claims:

| Claim        | Type     | Description                                    |
|--------------|----------|------------------------------------------------|
| `sub`        | UUID     | `recruiter_user.id` or `applicant_profile.id`  |
| `company_id` | UUID     | Present for recruiter tokens                   |
| `scope`      | string   | `recruiter` \| `hiring_manager` \| `hr_admin` \| `executive` \| `candidate` |
| `exp`        | integer  | Unix timestamp, 8-hour TTL for recruiters; 24-hour for candidates |

Refresh tokens are issued as `HttpOnly` cookies with 30-day TTL. Use `POST /auth/refresh` to obtain a new access token.

### Scopes and Permission Matrix

| Action                        | recruiter | hiring_manager | hr_admin | executive | candidate |
|-------------------------------|-----------|----------------|----------|-----------|-----------|
| Create / edit job             | ✓         | ✓              | ✓        | ✓         |           |
| Approve / reject job          |           |                | ✓        | ✓         |           |
| View all applications         | ✓         | ✓              | ✓        | ✓         |           |
| Move pipeline stage           | ✓         | ✓              | ✓        | ✓         |           |
| Submit interview feedback     | ✓         | ✓              | ✓        | ✓         |           |
| Generate / approve offer      |           | ✓              | ✓        | ✓         |           |
| GDPR erase candidate          |           |                | ✓        |           |           |
| View analytics                | ✓ (own)   | ✓ (team)       | ✓ (all)  | ✓ (all)   |           |
| Submit application            |           |                |          |           | ✓         |
| Withdraw application          |           |                |          |           | ✓         |

---

## Common Request Headers

```
Authorization: Bearer <token>
Content-Type: application/json
Accept: application/json
X-Request-ID: <uuid>        (optional, for idempotency and tracing)
```

---

## Common Response Envelope

All responses follow this envelope:

```json
{
  "data": { ... },
  "meta": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

Paginated list responses add a `pagination` key:

```json
{
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 342,
    "total_pages": 14,
    "has_next": true,
    "has_prev": false
  },
  "meta": { ... }
}
```

---

## Standard Error Codes

| HTTP Status | Error Code                  | Meaning                                      |
|-------------|-----------------------------|----------------------------------------------|
| 400         | `validation_error`          | Request body failed schema validation         |
| 401         | `unauthenticated`           | Missing or expired JWT                        |
| 403         | `forbidden`                 | Insufficient scope/role                       |
| 404         | `not_found`                 | Resource does not exist                       |
| 409         | `conflict`                  | Unique constraint violation                   |
| 422         | `unprocessable_entity`      | Business rule violation                       |
| 429         | `rate_limit_exceeded`       | Too many requests                             |
| 500         | `internal_error`            | Unexpected server error                       |

Error response body:

```json
{
  "error": {
    "code": "validation_error",
    "message": "salary_min must be less than or equal to salary_max",
    "details": [
      { "field": "salary_min", "issue": "must be <= salary_max" }
    ]
  },
  "meta": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

---

## Rate Limiting

All endpoints enforce rate limits per API token. Limit headers are returned on every response:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1705317600
```

| Endpoint Group                | Limit (per minute) |
|-------------------------------|--------------------|
| Public job search             | 120 req/min        |
| Application submission        | 10 req/min         |
| Analytics endpoints           | 30 req/min         |
| All other authenticated       | 300 req/min        |

---

---

# JOBS API

## `GET /jobs`

List published jobs with rich filtering. Public endpoint; no auth required for basic listing. Auth required to filter by `status=draft` or `status=pending_approval`.

**Query Parameters**

| Parameter        | Type    | Description                                             |
|------------------|---------|---------------------------------------------------------|
| `search`         | string  | Full-text search over title, description, summary       |
| `status`         | string  | `draft`, `published`, `paused`, `closed`, `archived`    |
| `location`       | string  | City, state, or country string match                    |
| `remote_policy`  | string  | `onsite`, `hybrid`, `remote`                            |
| `job_type`       | string  | `full_time`, `part_time`, `contract`, `internship`      |
| `department`     | string  | Exact department string                                 |
| `company_id`     | UUID    | Filter to specific company                              |
| `salary_min`     | number  | Minimum salary (filters jobs where `salary_max >= value`) |
| `salary_max`     | number  | Maximum salary (filters jobs where `salary_min <= value`) |
| `currency`       | string  | ISO 4217 currency code, default `USD`                   |
| `is_featured`    | boolean | Return only featured jobs                               |
| `page`           | integer | Page number, default 1                                  |
| `per_page`       | integer | Results per page, default 25, max 100                   |
| `sort`           | string  | `published_at_desc` (default), `salary_desc`, `relevance` |

**Response 200**

```json
{
  "data": [
    {
      "id": "3f7b2a91-4c5d-4e8f-b123-7a9c1e2d3f40",
      "company_id": "1a2b3c4d-5e6f-7890-abcd-ef1234567890",
      "title": "Senior Backend Engineer",
      "slug": "senior-backend-engineer-2025",
      "summary": "Join our platform team building the next generation of fintech infrastructure.",
      "department": "Engineering",
      "job_type": "full_time",
      "remote_policy": "hybrid",
      "location": "San Francisco, CA",
      "city": "San Francisco",
      "state": "CA",
      "country": "US",
      "salary_min": 160000.00,
      "salary_max": 200000.00,
      "currency": "USD",
      "salary_display_type": "range",
      "status": "published",
      "is_featured": false,
      "published_at": "2025-01-10T09:00:00Z",
      "expires_at": "2025-03-10T09:00:00Z",
      "application_count": 47,
      "view_count": 1283,
      "company": {
        "id": "1a2b3c4d-5e6f-7890-abcd-ef1234567890",
        "name": "Acme Financial",
        "slug": "acme-financial",
        "logo_url": "https://cdn.recruitplatform.io/logos/acme-financial.png",
        "industry": "Fintech"
      }
    }
  ],
  "pagination": { "page": 1, "per_page": 25, "total": 342, "total_pages": 14, "has_next": true, "has_prev": false },
  "meta": { "request_id": "abc123", "timestamp": "2025-01-15T10:30:00Z" }
}
```

---

## `POST /jobs`

Create a new job posting. Requires scope: `recruiter`, `hiring_manager`, or `hr_admin`.

**Request Body**

```json
{
  "title": "Senior Backend Engineer",
  "description": "<p>We are looking for a Senior Backend Engineer...</p>",
  "summary": "Join our platform team building next-gen fintech infrastructure.",
  "department": "Engineering",
  "job_type": "full_time",
  "remote_policy": "hybrid",
  "location": "San Francisco, CA",
  "city": "San Francisco",
  "state": "CA",
  "country": "US",
  "salary_min": 160000.00,
  "salary_max": 200000.00,
  "currency": "USD",
  "salary_display_type": "range",
  "expires_at": "2025-03-10T09:00:00Z",
  "pipeline_id": "7c8d9e0f-1a2b-3c4d-5e6f-7a8b9c0d1e2f",
  "requirements": [
    {
      "requirement_type": "required",
      "category": "technical",
      "description": "5+ years of Go or Rust backend experience",
      "years_experience": 5
    }
  ],
  "questions": [
    {
      "question_text": "Are you authorised to work in the US?",
      "question_type": "yes_no",
      "is_required": true,
      "sort_order": 1
    }
  ]
}
```

**Response 201**

```json
{
  "data": {
    "id": "3f7b2a91-4c5d-4e8f-b123-7a9c1e2d3f40",
    "status": "draft",
    "created_at": "2025-01-15T10:30:00Z"
  },
  "meta": { "request_id": "abc123", "timestamp": "2025-01-15T10:30:00Z" }
}
```

**Error Responses**

| Status | Code                   | Condition                                   |
|--------|------------------------|---------------------------------------------|
| 400    | `validation_error`     | Missing required field or type mismatch     |
| 422    | `unprocessable_entity` | `salary_min` > `salary_max`                 |
| 403    | `forbidden`            | Token does not belong to the company        |

---

## `GET /jobs/:id`

Fetch full job details including requirements and questions.

**Response 200**

```json
{
  "data": {
    "id": "3f7b2a91-4c5d-4e8f-b123-7a9c1e2d3f40",
    "company_id": "1a2b3c4d-5e6f-7890-abcd-ef1234567890",
    "title": "Senior Backend Engineer",
    "slug": "senior-backend-engineer-2025",
    "description": "<p>We are looking for...</p>",
    "summary": "Join our platform team...",
    "department": "Engineering",
    "job_type": "full_time",
    "remote_policy": "hybrid",
    "location": "San Francisco, CA",
    "salary_min": 160000.00,
    "salary_max": 200000.00,
    "currency": "USD",
    "salary_display_type": "range",
    "status": "published",
    "approval_status": "approved",
    "published_at": "2025-01-10T09:00:00Z",
    "expires_at": "2025-03-10T09:00:00Z",
    "application_count": 47,
    "view_count": 1283,
    "is_featured": false,
    "distribution_status": {
      "linkedin": "published",
      "indeed": "published",
      "glassdoor": "pending"
    },
    "requirements": [
      {
        "id": "req-uuid",
        "requirement_type": "required",
        "category": "technical",
        "description": "5+ years Go or Rust",
        "years_experience": 5
      }
    ],
    "questions": [
      {
        "id": "q-uuid",
        "question_text": "Are you authorised to work in the US?",
        "question_type": "yes_no",
        "is_required": true,
        "sort_order": 1
      }
    ],
    "created_at": "2025-01-08T14:00:00Z",
    "updated_at": "2025-01-10T09:00:00Z"
  },
  "meta": { "request_id": "abc123", "timestamp": "2025-01-15T10:30:00Z" }
}
```

---

## `PUT /jobs/:id`

Update job fields. Partial updates accepted (only provided fields are updated). Cannot update `status` directly — use lifecycle action endpoints instead.

**Request Body** (all fields optional)

```json
{
  "title": "Staff Backend Engineer",
  "salary_min": 180000.00,
  "salary_max": 220000.00,
  "expires_at": "2025-04-01T00:00:00Z"
}
```

**Response 200** — Returns full updated job object (same schema as `GET /jobs/:id`).

---

## `DELETE /jobs/:id`

Soft-delete (archive) a job. Sets `status = 'archived'`. Requires `hr_admin` or `executive` scope.

**Response 204** — No content.

---

## `POST /jobs/:id/submit-approval`

Submit a draft job for HR approval. Transitions `status` from `draft` → `pending_approval`. Requires `recruiter` or `hiring_manager` scope.

**Request Body** — Empty `{}` or optional note.

```json
{ "note": "Ready for review — all requirements confirmed with hiring manager." }
```

**Response 200**

```json
{
  "data": { "id": "3f7b...", "status": "pending_approval", "submitted_at": "2025-01-15T11:00:00Z" },
  "meta": { ... }
}
```

**Error Responses**

| Status | Code                   | Condition                                 |
|--------|------------------------|-------------------------------------------|
| 422    | `unprocessable_entity` | Job is not in `draft` status              |

---

## `POST /jobs/:id/approve`

Approve a pending job. Transitions `status` → `published` (or `approved` if manual publish is required). Requires `hr_admin` or `executive` scope.

**Request Body**

```json
{ "note": "Approved. Publish immediately." }
```

**Response 200** — Returns updated job with `approval_status: "approved"`.

---

## `POST /jobs/:id/reject`

Reject a pending job with a reason. Returns status to `draft`. Requires `hr_admin` or `executive` scope.

**Request Body**

```json
{ "reason": "Salary range exceeds budget. Please revise and resubmit." }
```

**Response 200** — Returns updated job with `approval_status: "rejected"`.

---

## `POST /jobs/:id/publish`

Publish an approved job. Sets `status = 'published'` and `published_at = NOW()`. Triggers distribution to configured job boards.

**Response 200**

```json
{
  "data": {
    "id": "3f7b...",
    "status": "published",
    "published_at": "2025-01-15T11:05:00Z",
    "distribution_status": { "linkedin": "queued", "indeed": "queued" }
  },
  "meta": { ... }
}
```

---

## `POST /jobs/:id/pause`

Pause a published job — stops new applications. Sets `status = 'paused'`.

**Response 200** — Returns updated job object.

---

## `POST /jobs/:id/close`

Close a job — permanently stops new applications. Sets `status = 'closed'` and `closed_at = NOW()`.

**Response 200** — Returns updated job object.

---

## `GET /jobs/:id/applications`

List all applications for a specific job with filtering and sorting.

**Query Parameters**

| Parameter       | Type    | Description                                         |
|-----------------|---------|-----------------------------------------------------|
| `status`        | string  | Filter by application status                        |
| `stage_id`      | UUID    | Filter by current pipeline stage                    |
| `ai_score_min`  | number  | Minimum AI score (0–100)                            |
| `source`        | string  | Application source filter                           |
| `search`        | string  | Search candidate name or email                      |
| `sort`          | string  | `applied_at_desc` (default), `ai_score_desc`, `name_asc` |
| `page`          | integer | Page number                                         |
| `per_page`      | integer | Default 25, max 100                                 |

**Response 200** — Returns paginated list of application objects with candidate summary embedded.

---

## `GET /jobs/:id/distribution-status`

Get real-time distribution status across all configured job boards.

**Response 200**

```json
{
  "data": {
    "job_id": "3f7b...",
    "distribution": {
      "linkedin": { "status": "published", "url": "https://linkedin.com/jobs/view/12345", "posted_at": "2025-01-10T09:05:00Z" },
      "indeed": { "status": "published", "url": "https://indeed.com/viewjob?jk=abc123", "posted_at": "2025-01-10T09:07:00Z" },
      "glassdoor": { "status": "failed", "error": "Account not connected", "last_attempted_at": "2025-01-10T09:05:00Z" }
    }
  },
  "meta": { ... }
}
```

---

---

# APPLICATIONS API

## `POST /applications`

Submit a job application. Requires candidate scope or unauthenticated (creates profile on first apply).

**Request Body**

```json
{
  "job_id": "3f7b2a91-4c5d-4e8f-b123-7a9c1e2d3f40",
  "applicant": {
    "email": "jane.doe@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "phone": "+14155551234",
    "location": "San Francisco, CA",
    "linkedin_url": "https://linkedin.com/in/janedoe",
    "consent_given": true
  },
  "resume_id": "r-uuid-existing",
  "resume_upload": null,
  "cover_letter": {
    "content": "I am excited to apply for this position because..."
  },
  "answers": {
    "q-uuid-1": "yes",
    "q-uuid-2": "I have 7 years of Go experience."
  },
  "source": "linkedin",
  "utm_source": "linkedin",
  "utm_medium": "social",
  "utm_campaign": "q1-2025-eng-hiring"
}
```

**Response 201**

```json
{
  "data": {
    "id": "app-uuid",
    "job_id": "3f7b...",
    "applicant_id": "profile-uuid",
    "status": "applied",
    "applied_at": "2025-01-15T14:22:00Z",
    "ai_score": null,
    "current_stage": {
      "id": "stage-uuid",
      "name": "Applied",
      "stage_type": "applied"
    }
  },
  "meta": { ... }
}
```

**Error Responses**

| Status | Code             | Condition                                          |
|--------|------------------|----------------------------------------------------|
| 409    | `conflict`       | Candidate already applied to this job              |
| 422    | `unprocessable_entity` | Job is not in `published` status            |
| 400    | `validation_error` | Required screening question not answered         |

---

## `GET /applications/:id`

Fetch full application details. Recruiters see AI scores and parsed data. Candidate tokens only see their own application.

**Response 200**

```json
{
  "data": {
    "id": "app-uuid",
    "job_id": "3f7b...",
    "applicant": {
      "id": "profile-uuid",
      "first_name": "Jane",
      "last_name": "Doe",
      "email": "jane.doe@example.com",
      "headline": "Senior Backend Engineer",
      "linkedin_url": "https://linkedin.com/in/janedoe"
    },
    "status": "shortlisted",
    "current_stage": { "id": "stage-uuid", "name": "Phone Screen", "stage_type": "phone_screen" },
    "ai_score": 87.4,
    "ai_match_percentage": 91.0,
    "ai_extracted_skills": ["Go", "PostgreSQL", "Kubernetes", "gRPC"],
    "source": "linkedin",
    "resume": {
      "id": "r-uuid",
      "file_url": "https://cdn.recruitplatform.io/resumes/r-uuid.pdf",
      "file_name": "jane_doe_resume.pdf",
      "parsing_status": "completed"
    },
    "answers": {
      "q-uuid-1": "yes",
      "q-uuid-2": "I have 7 years of Go experience."
    },
    "applied_at": "2025-01-15T14:22:00Z",
    "created_at": "2025-01-15T14:22:00Z",
    "updated_at": "2025-01-15T16:00:00Z"
  },
  "meta": { ... }
}
```

---

## `PUT /applications/:id`

Update mutable application fields (e.g., notes added by recruiter, manual source correction). Requires recruiter scope.

**Request Body**

```json
{
  "source": "referral",
  "is_anonymous": false
}
```

**Response 200** — Returns updated application object.

---

## `POST /applications/:id/withdraw`

Candidate withdraws their own application. Sets `status = 'withdrawn'`. Only the owning candidate or `hr_admin` may call this.

**Request Body**

```json
{ "reason": "I have accepted another offer." }
```

**Response 200**

```json
{
  "data": { "id": "app-uuid", "status": "withdrawn", "withdrawn_at": "2025-01-16T09:00:00Z" },
  "meta": { ... }
}
```

---

## `GET /applications/:id/timeline`

Returns a chronological activity log for the application.

**Response 200**

```json
{
  "data": [
    { "event": "applied", "actor": "candidate", "timestamp": "2025-01-15T14:22:00Z", "note": null },
    { "event": "stage_moved", "actor": "recruiter:uuid", "timestamp": "2025-01-15T16:00:00Z", "note": "Moving to phone screen", "from_stage": "Applied", "to_stage": "Phone Screen" },
    { "event": "interview_scheduled", "actor": "recruiter:uuid", "timestamp": "2025-01-16T10:00:00Z", "note": null },
    { "event": "feedback_submitted", "actor": "recruiter:uuid", "timestamp": "2025-01-17T15:30:00Z", "note": "Strong candidate" }
  ],
  "meta": { ... }
}
```

---

## `GET /applications/search`

Boolean candidate search across applications company-wide.

**Query Parameters**

| Parameter       | Type    | Description                                                  |
|-----------------|---------|--------------------------------------------------------------|
| `q`             | string  | Boolean query e.g. `"Go AND (Kubernetes OR Docker) NOT Java"` |
| `job_id`        | UUID    | Scope to a specific job                                      |
| `stage_type`    | string  | Filter by pipeline stage type                                |
| `status`        | string  | Application status filter                                    |
| `ai_score_min`  | number  | Minimum AI score                                             |
| `skills`        | string  | Comma-separated skill names                                  |
| `experience_min`| integer | Minimum years of experience                                  |
| `page`          | integer | Page number                                                  |
| `per_page`      | integer | Default 25                                                   |

**Response 200** — Returns paginated list of application objects matching the query.

---

---

# CANDIDATES API

## `GET /candidates`

Search candidate profiles across all applications for the company.

**Query Parameters**

| Parameter        | Type    | Description                                                |
|------------------|---------|------------------------------------------------------------|
| `search`         | string  | Full-text search: name, email, headline                    |
| `skills`         | string  | Comma-separated skills (AND logic by default)              |
| `location`       | string  | Location string                                            |
| `experience_min` | integer | Minimum total years experience (from parsed resume)        |
| `applied_after`  | string  | ISO 8601 date — only candidates who applied after this date |
| `page`           | integer | Page number                                                |
| `per_page`       | integer | Default 25, max 100                                        |

**Response 200** — Paginated list of `applicant_profiles` with application counts.

---

## `GET /candidates/:id`

Fetch a candidate's full profile with resume data and application history for the authenticated company.

**Response 200**

```json
{
  "data": {
    "id": "profile-uuid",
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane.doe@example.com",
    "phone": "+14155551234",
    "location": "San Francisco, CA",
    "headline": "Senior Backend Engineer",
    "bio": "10 years building distributed systems...",
    "linkedin_url": "https://linkedin.com/in/janedoe",
    "github_url": "https://github.com/janedoe",
    "primary_resume": {
      "id": "r-uuid",
      "file_url": "https://cdn.recruitplatform.io/resumes/r-uuid.pdf",
      "parsed_skills": ["Go", "PostgreSQL", "Kubernetes"],
      "parsing_status": "completed"
    },
    "application_count": 2,
    "created_at": "2025-01-15T14:22:00Z"
  },
  "meta": { ... }
}
```

---

## `GET /candidates/:id/applications`

List all applications by a candidate within the authenticated company.

**Response 200** — Paginated list of application summaries with job title and current stage.

---

## `POST /candidates/:id/gdpr-export`

Generate a GDPR data export for the candidate. Queues an async job; sends download link by email. Requires `hr_admin` scope.

**Response 202**

```json
{
  "data": { "job_id": "export-job-uuid", "status": "queued", "estimated_ready_at": "2025-01-15T11:10:00Z" },
  "meta": { ... }
}
```

---

## `DELETE /candidates/:id/gdpr-erase`

Erase all PII for a candidate. Sets `is_gdpr_erased = TRUE` and nullifies all personal fields. Audit record is retained. Requires `hr_admin` scope.

**Request Body**

```json
{ "reason": "Candidate requested erasure per GDPR Article 17." }
```

**Response 200**

```json
{
  "data": { "id": "profile-uuid", "is_gdpr_erased": true, "erased_at": "2025-01-15T11:05:00Z" },
  "meta": { ... }
}
```

**Error Responses**

| Status | Code                   | Condition                                              |
|--------|------------------------|--------------------------------------------------------|
| 422    | `unprocessable_entity` | Candidate has an active open offer — cannot erase yet  |

---

---

# PIPELINES API

## `GET /pipelines`

List all pipelines for the authenticated company.

**Query Parameters**

| Parameter  | Type    | Description                       |
|------------|---------|-----------------------------------|
| `job_id`   | UUID    | Filter to pipelines for a job     |
| `is_default` | boolean | Return only default pipeline     |

**Response 200** — List of pipeline objects with stage counts.

---

## `POST /pipelines`

Create a new pipeline. Requires `hr_admin` scope.

**Request Body**

```json
{
  "name": "Engineering Hiring Pipeline",
  "job_id": null,
  "is_default": false,
  "stages": [
    { "name": "Applied",              "stage_type": "applied",              "sort_order": 1, "color": "#6B7280" },
    { "name": "Phone Screen",         "stage_type": "phone_screen",         "sort_order": 2, "color": "#3B82F6" },
    { "name": "Technical Assessment", "stage_type": "technical_assessment",  "sort_order": 3, "color": "#8B5CF6" },
    { "name": "Final Interview",      "stage_type": "interview",            "sort_order": 4, "color": "#F59E0B" },
    { "name": "Offer",                "stage_type": "offer",                "sort_order": 5, "color": "#10B981" },
    { "name": "Hired",                "stage_type": "hired",                "sort_order": 6, "color": "#059669" },
    { "name": "Rejected",             "stage_type": "rejected",             "sort_order": 7, "color": "#EF4444" }
  ]
}
```

**Response 201** — Returns full pipeline object with created stages.

---

## `GET /pipelines/:id`

Fetch a pipeline with all its stages and per-stage application counts.

**Response 200**

```json
{
  "data": {
    "id": "pipeline-uuid",
    "name": "Engineering Hiring Pipeline",
    "is_default": false,
    "stages": [
      { "id": "s1", "name": "Applied",      "stage_type": "applied",      "sort_order": 1, "color": "#6B7280", "application_count": 47 },
      { "id": "s2", "name": "Phone Screen", "stage_type": "phone_screen", "sort_order": 2, "color": "#3B82F6", "application_count": 12 }
    ],
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-10T00:00:00Z"
  },
  "meta": { ... }
}
```

---

## `PUT /pipelines/:id`

Update pipeline name or `is_default` flag. Requires `hr_admin`.

---

## `GET /pipelines/:id/stages`

List all stages for a pipeline ordered by `sort_order`.

**Response 200** — Ordered list of stage objects.

---

## `POST /pipelines/:id/stages`

Add a new stage to an existing pipeline.

**Request Body**

```json
{
  "name": "Culture Fit Interview",
  "stage_type": "interview",
  "sort_order": 5,
  "color": "#F97316",
  "email_template_id": "template-uuid"
}
```

**Response 201** — Returns created stage object.

---

## `PUT /pipelines/:id/stages/:stageId`

Update stage properties including `auto_move_rules`.

**Request Body**

```json
{
  "name": "Culture & Values Interview",
  "color": "#EA580C",
  "auto_move_rules": {
    "on_ai_score_below": { "threshold": 40, "move_to_stage_id": "rejected-stage-uuid" }
  }
}
```

**Response 200** — Returns updated stage object.

---

## `DELETE /pipelines/:id/stages/:stageId`

Delete a stage. Will fail if any applications are currently in this stage.

**Response 204** — No content.

**Error Responses**

| Status | Code                   | Condition                                          |
|--------|------------------------|----------------------------------------------------|
| 422    | `unprocessable_entity` | Applications exist in this stage — cannot delete   |

---

## `POST /applications/:id/move-stage`

Move an application to a different pipeline stage. Triggers configured `email_template_id` on the target stage if set.

**Request Body**

```json
{
  "stage_id": "s2-uuid",
  "note": "Strong phone screen. Moving to technical.",
  "send_notification": true
}
```

**Response 200**

```json
{
  "data": {
    "application_id": "app-uuid",
    "previous_stage": { "id": "s1", "name": "Applied" },
    "current_stage":  { "id": "s2", "name": "Phone Screen" },
    "moved_at": "2025-01-16T10:00:00Z"
  },
  "meta": { ... }
}
```

---

## `POST /applications/bulk-move`

Move multiple applications to a stage in a single request. Useful for batch rejection or shortlisting.

**Request Body**

```json
{
  "application_ids": ["app-uuid-1", "app-uuid-2", "app-uuid-3"],
  "stage_id": "rejected-stage-uuid",
  "note": "Did not meet minimum experience threshold.",
  "send_notifications": true
}
```

**Response 200**

```json
{
  "data": {
    "moved_count": 3,
    "failed_ids": [],
    "moved_at": "2025-01-16T11:00:00Z"
  },
  "meta": { ... }
}
```

---

---

# INTERVIEWS API

## `POST /interviews`

Schedule an interview for an application. Optionally adds calendar events via OAuth-connected calendars.

**Request Body**

```json
{
  "application_id": "app-uuid",
  "title": "Technical Interview — Round 1",
  "interview_type": "video",
  "scheduled_at": "2025-01-22T14:00:00Z",
  "duration_minutes": 90,
  "video_platform": "zoom",
  "rounds": [
    {
      "round_number": 1,
      "title": "System Design",
      "interviewer_id": "recruiter-uuid-1",
      "scheduled_at": "2025-01-22T14:00:00Z",
      "duration_minutes": 60
    },
    {
      "round_number": 2,
      "title": "Coding Challenge",
      "interviewer_id": "recruiter-uuid-2",
      "scheduled_at": "2025-01-22T15:00:00Z",
      "duration_minutes": 60
    }
  ],
  "add_to_calendar": true,
  "send_invite_to_candidate": true
}
```

**Response 201**

```json
{
  "data": {
    "id": "interview-uuid",
    "status": "scheduled",
    "video_link": "https://zoom.us/j/98765432100",
    "meeting_id": "98765432100",
    "calendar_event_ids": {
      "recruiter-uuid-1": { "google": "event_abc123" },
      "recruiter-uuid-2": { "google": "event_def456" }
    },
    "rounds": [
      { "id": "round-uuid-1", "round_number": 1, "status": "scheduled" },
      { "id": "round-uuid-2", "round_number": 2, "status": "scheduled" }
    ],
    "created_at": "2025-01-16T10:00:00Z"
  },
  "meta": { ... }
}
```

---

## `GET /interviews/:id`

Fetch full interview details including rounds and feedback status.

**Response 200** — Full interview object with embedded rounds and per-round feedback submission status.

---

## `PUT /interviews/:id`

Reschedule or update interview details. Sends reschedule notifications if `send_notifications: true`.

**Request Body**

```json
{
  "scheduled_at": "2025-01-23T14:00:00Z",
  "send_notifications": true,
  "reschedule_reason": "Interviewer availability conflict"
}
```

**Response 200** — Returns updated interview object.

---

## `DELETE /interviews/:id`

Cancel an interview. Triggers `POST /interviews/:id/cancel` internally.

**Response 204**

---

## `POST /interviews/:id/rounds`

Add an additional round to an existing interview.

**Request Body**

```json
{
  "round_number": 3,
  "title": "Executive Conversation",
  "interviewer_id": "exec-recruiter-uuid",
  "scheduled_at": "2025-01-22T16:00:00Z",
  "duration_minutes": 30
}
```

**Response 201** — Returns created round object.

---

## `PUT /interviews/:id/rounds/:roundId`

Update a specific round (reschedule, reassign interviewer).

**Request Body**

```json
{
  "interviewer_id": "new-recruiter-uuid",
  "scheduled_at": "2025-01-22T16:30:00Z"
}
```

**Response 200** — Returns updated round object.

---

## `POST /interviews/:id/confirm`

Candidate confirms attendance. Transitions interview status from `scheduled` → `confirmed`.

**Response 200**

```json
{
  "data": { "id": "interview-uuid", "status": "confirmed", "confirmed_at": "2025-01-18T09:00:00Z" },
  "meta": { ... }
}
```

---

## `POST /interviews/:id/complete`

Mark interview as completed. Transitions status → `completed`. Triggers feedback request emails to all interviewers with pending feedback.

**Response 200**

```json
{
  "data": { "id": "interview-uuid", "status": "completed", "completed_at": "2025-01-22T15:45:00Z" },
  "meta": { ... }
}
```

---

## `POST /interviews/:id/cancel`

Cancel an interview. Optionally sends cancellation notifications.

**Request Body**

```json
{
  "reason": "Candidate withdrew application.",
  "send_notifications": true
}
```

**Response 200**

```json
{
  "data": { "id": "interview-uuid", "status": "cancelled", "cancelled_at": "2025-01-20T08:00:00Z" },
  "meta": { ... }
}
```

---

## `GET /calendar-slots`

Retrieve available calendar slots for one or more recruiters.

**Query Parameters**

| Parameter         | Type    | Description                                        |
|-------------------|---------|----------------------------------------------------|
| `recruiter_ids`   | string  | Comma-separated UUID list                          |
| `date_from`       | string  | ISO 8601 date-time — start of search window        |
| `date_to`         | string  | ISO 8601 date-time — end of search window          |
| `duration_minutes`| integer | Minimum slot duration required                     |

**Response 200**

```json
{
  "data": [
    { "recruiter_id": "r-uuid-1", "start_at": "2025-01-22T13:00:00Z", "end_at": "2025-01-22T14:00:00Z", "is_available": true },
    { "recruiter_id": "r-uuid-1", "start_at": "2025-01-22T15:00:00Z", "end_at": "2025-01-22T16:00:00Z", "is_available": true }
  ],
  "meta": { ... }
}
```

---

## `POST /calendar-slots/check-availability`

Check whether multiple interviewers are all free at a specific time.

**Request Body**

```json
{
  "recruiter_ids": ["r-uuid-1", "r-uuid-2"],
  "proposed_start_at": "2025-01-22T14:00:00Z",
  "duration_minutes": 60
}
```

**Response 200**

```json
{
  "data": {
    "all_available": false,
    "results": [
      { "recruiter_id": "r-uuid-1", "available": true },
      { "recruiter_id": "r-uuid-2", "available": false, "conflict": { "start_at": "2025-01-22T13:30:00Z", "end_at": "2025-01-22T14:30:00Z" } }
    ],
    "next_available_window": "2025-01-22T16:00:00Z"
  },
  "meta": { ... }
}
```

---

---

# FEEDBACK API

## `POST /feedback`

Submit interview feedback for a completed round. Requires the interviewer's recruiter token.

**Request Body**

```json
{
  "interview_round_id": "round-uuid",
  "application_id": "app-uuid",
  "overall_rating": "yes",
  "technical_score": 4.5,
  "communication_score": 4.0,
  "culture_fit_score": 4.5,
  "problem_solving_score": 4.0,
  "scorecard": {
    "distributed_systems": { "score": 5, "notes": "Excellent understanding of CAP theorem" },
    "code_quality": { "score": 4, "notes": "Clean code, good test coverage" }
  },
  "strengths": "Deep expertise in distributed systems. Clear communicator. Asked insightful questions.",
  "concerns": "Limited experience with our specific tech stack (Rust). Would need ramp-up time.",
  "recommendation": "advance",
  "notes": "Recommend advancing to final round with VP Engineering."
}
```

**Response 201**

```json
{
  "data": {
    "id": "feedback-uuid",
    "overall_rating": "yes",
    "submitted_at": "2025-01-22T16:30:00Z",
    "is_late": false
  },
  "meta": { ... }
}
```

---

## `GET /feedback/:id`

Fetch a specific feedback record. Only the submitting interviewer and `hr_admin` may view raw feedback.

**Response 200** — Full feedback object including scorecard.

---

## `PUT /feedback/:id`

Update feedback before the deadline. Not allowed after `deadline_at` has passed.

**Request Body** — Any subset of feedback fields.

**Response 200** — Returns updated feedback object.

---

## `GET /interviews/:id/feedback`

Retrieve all feedback submissions for all rounds of an interview.

**Response 200**

```json
{
  "data": [
    {
      "round_id": "round-uuid-1",
      "round_title": "System Design",
      "interviewer": { "id": "r-uuid-1", "name": "Alice Chen" },
      "overall_rating": "strong_yes",
      "submitted_at": "2025-01-22T16:00:00Z",
      "is_late": false
    },
    {
      "round_id": "round-uuid-2",
      "round_title": "Coding Challenge",
      "interviewer": { "id": "r-uuid-2", "name": "Bob Kumar" },
      "overall_rating": "yes",
      "submitted_at": "2025-01-22T17:00:00Z",
      "is_late": false
    }
  ],
  "meta": { ... }
}
```

---

## `GET /applications/:id/feedback-summary`

Aggregated feedback summary across all interview rounds for an application.

**Response 200**

```json
{
  "data": {
    "application_id": "app-uuid",
    "total_rounds": 2,
    "feedback_submitted": 2,
    "feedback_pending": 0,
    "average_scores": {
      "technical": 4.25,
      "communication": 4.0,
      "culture_fit": 4.5,
      "problem_solving": 4.0
    },
    "rating_breakdown": {
      "strong_yes": 1,
      "yes": 1,
      "neutral": 0,
      "no": 0,
      "strong_no": 0
    },
    "recommendation_breakdown": {
      "advance": 2,
      "hold": 0,
      "reject": 0
    },
    "consensus": "advance"
  },
  "meta": { ... }
}
```

---

---

# OFFERS API

## `POST /offers`

Generate an offer letter for an application. Requires `hiring_manager` or `hr_admin` scope.

**Request Body**

```json
{
  "application_id": "app-uuid",
  "template_id": "template-uuid",
  "salary": 190000.00,
  "currency": "USD",
  "start_date": "2025-03-01",
  "position_title": "Senior Backend Engineer",
  "department": "Engineering",
  "reporting_to": "Director of Engineering",
  "benefits_package": {
    "health_insurance": "Full coverage (medical, dental, vision)",
    "401k_match": "4% employer match",
    "pto_days": 20,
    "remote_days_per_week": 3
  },
  "equity_details": {
    "stock_options": 10000,
    "vesting_schedule": "4 years with 1-year cliff",
    "strike_price": 2.50
  },
  "signing_bonus": 15000.00
}
```

**Response 201**

```json
{
  "data": {
    "id": "offer-uuid",
    "status": "draft",
    "salary": 190000.00,
    "currency": "USD",
    "start_date": "2025-03-01",
    "approved_by_hm": false,
    "approved_by_hr": false,
    "created_at": "2025-01-24T09:00:00Z"
  },
  "meta": { ... }
}
```

---

## `GET /offers/:id`

Fetch full offer letter details. Candidate token returns a redacted view without internal approval fields.

**Response 200** — Full offer object matching the `offer_letters` schema.

---

## `PUT /offers/:id`

Update offer fields while in `draft` status.

**Request Body** — Any subset of offer fields.

**Response 200** — Returns updated offer object.

---

## `POST /offers/:id/submit-approval`

Submit offer for approval workflow. Transitions `status` → `pending_approval`. Sends approval request to hiring manager and HR.

**Response 200**

```json
{
  "data": { "id": "offer-uuid", "status": "pending_approval", "submitted_at": "2025-01-24T09:30:00Z" },
  "meta": { ... }
}
```

---

## `POST /offers/:id/approve`

Approve the offer. Sets `approved_by_hm` or `approved_by_hr` based on the approver's role. When both are `true`, transitions status → `approved`.

**Request Body**

```json
{ "note": "Approved. Compensation is within budget for this level." }
```

**Response 200**

```json
{
  "data": {
    "id": "offer-uuid",
    "status": "approved",
    "approved_by_hm": true,
    "approved_by_hr": true
  },
  "meta": { ... }
}
```

---

## `POST /offers/:id/send`

Send the offer to the candidate via email with a DocuSign envelope. Transitions status → `sent`.

**Request Body**

```json
{
  "message": "We are thrilled to extend this offer to you. Please review and sign by the expiry date.",
  "expires_at": "2025-02-07T23:59:59Z"
}
```

**Response 200**

```json
{
  "data": {
    "id": "offer-uuid",
    "status": "sent",
    "docusign_envelope_id": "envelope-abc123",
    "sent_at": "2025-01-24T10:00:00Z",
    "expires_at": "2025-02-07T23:59:59Z"
  },
  "meta": { ... }
}
```

---

## `POST /offers/:id/resend`

Resend the offer email to the candidate. Does not generate a new DocuSign envelope.

**Response 200** — Returns offer with updated `sent_at`.

---

## `POST /offers/:id/rescind`

Rescind a sent offer. Transitions status → `rescinded`. Voids the DocuSign envelope.

**Request Body**

```json
{ "reason": "Position has been put on hold due to budget freeze." }
```

**Response 200**

```json
{
  "data": { "id": "offer-uuid", "status": "rescinded", "rescinded_at": "2025-01-28T08:00:00Z" },
  "meta": { ... }
}
```

---

## `GET /offers/:id/negotiations`

List all counter-offer messages for an offer.

**Response 200**

```json
{
  "data": [
    {
      "id": "neg-uuid-1",
      "initiated_by": "candidate",
      "requested_salary": 205000.00,
      "requested_start_date": null,
      "message": "I am very excited about this opportunity. Given my experience, I was hoping we could discuss a base of $205k.",
      "status": "pending",
      "created_at": "2025-01-25T14:00:00Z"
    }
  ],
  "meta": { ... }
}
```

---

## `POST /offers/:id/negotiations`

Submit a counter-offer (candidate or recruiter).

**Request Body**

```json
{
  "requested_salary": 205000.00,
  "requested_start_date": null,
  "message": "I am very excited about this opportunity. Given my experience, I was hoping we could discuss a base of $205k."
}
```

**Response 201** — Returns created negotiation object.

---

## `POST /offers/:id/negotiations/:negId/accept`

Accept a counter-offer. Requires recruiter scope. Updates offer salary accordingly.

**Response 200**

```json
{
  "data": {
    "negotiation_id": "neg-uuid-1",
    "status": "accepted",
    "responded_at": "2025-01-26T09:00:00Z",
    "offer": { "id": "offer-uuid", "salary": 205000.00 }
  },
  "meta": { ... }
}
```

---

## `POST /offers/:id/negotiations/:negId/reject`

Reject a counter-offer with an explanation.

**Request Body**

```json
{ "message": "We are not able to move on base salary, but we can increase the signing bonus to $25,000." }
```

**Response 200** — Returns updated negotiation with `status: "rejected"`.

---

---

# ANALYTICS API

All analytics endpoints require `recruiter` scope or higher. Recruiters see only their own data unless `hr_admin` or `executive` scope is present.

## `GET /analytics/hiring-funnel`

Pipeline conversion rates across all stages.

**Query Parameters**

| Parameter    | Type    | Description                          |
|--------------|---------|--------------------------------------|
| `job_id`     | UUID    | Filter to specific job               |
| `date_from`  | string  | ISO 8601 date                        |
| `date_to`    | string  | ISO 8601 date                        |
| `department` | string  | Department filter                    |

**Response 200**

```json
{
  "data": {
    "period": { "from": "2025-01-01", "to": "2025-01-31" },
    "total_applications": 342,
    "funnel": [
      { "stage": "Applied",              "count": 342, "conversion_rate": null },
      { "stage": "Phone Screen",         "count": 89,  "conversion_rate": 26.0 },
      { "stage": "Technical Assessment", "count": 41,  "conversion_rate": 46.1 },
      { "stage": "Final Interview",      "count": 18,  "conversion_rate": 43.9 },
      { "stage": "Offer Extended",       "count": 9,   "conversion_rate": 50.0 },
      { "stage": "Hired",                "count": 7,   "conversion_rate": 77.8 }
    ],
    "overall_conversion_rate": 2.05
  },
  "meta": { ... }
}
```

---

## `GET /analytics/time-to-hire`

Average days from `applied_at` to `hired_at`.

**Query Parameters** — `date_from`, `date_to`, `department`, `recruiter_id`, `job_id`

**Response 200**

```json
{
  "data": {
    "average_days_to_hire": 28.4,
    "median_days_to_hire": 24.0,
    "by_department": [
      { "department": "Engineering", "average_days": 32.1 },
      { "department": "Sales",       "average_days": 21.5 }
    ],
    "by_recruiter": [
      { "recruiter_id": "r-uuid-1", "name": "Alice Chen", "average_days": 26.3, "hires": 4 }
    ]
  },
  "meta": { ... }
}
```

---

## `GET /analytics/source-roi`

Application volume and hire rate broken down by source.

**Response 200**

```json
{
  "data": [
    { "source": "linkedin",  "applications": 148, "hires": 3, "hire_rate": 2.03, "cost_per_hire": 850.00 },
    { "source": "indeed",    "applications": 97,  "hires": 2, "hire_rate": 2.06, "cost_per_hire": 620.00 },
    { "source": "referral",  "applications": 31,  "hires": 2, "hire_rate": 6.45, "cost_per_hire": 0.00 },
    { "source": "direct",    "applications": 66,  "hires": 0, "hire_rate": 0.0,  "cost_per_hire": null }
  ],
  "meta": { ... }
}
```

---

## `GET /analytics/diversity`

EEO breakdown of candidates by pipeline stage.

**Query Parameters** — `date_from`, `date_to`, `job_id`, `department`

**Response 200**

```json
{
  "data": {
    "period": { "from": "2025-01-01", "to": "2025-01-31" },
    "gender": { "male": 58, "female": 36, "non_binary": 4, "prefer_not_to_say": 12, "not_provided": 232 },
    "by_stage": [
      {
        "stage": "Applied",
        "gender": { "male": 58, "female": 36, "non_binary": 4 }
      },
      {
        "stage": "Hired",
        "gender": { "male": 5, "female": 2, "non_binary": 0 }
      }
    ]
  },
  "meta": { ... }
}
```

---

## `GET /analytics/recruiter-performance`

Per-recruiter productivity metrics. Requires `hr_admin` or `executive` scope.

**Response 200**

```json
{
  "data": [
    {
      "recruiter_id": "r-uuid-1",
      "name": "Alice Chen",
      "open_jobs": 5,
      "applications_reviewed": 87,
      "interviews_scheduled": 24,
      "offers_sent": 6,
      "hires": 4,
      "avg_time_to_hire_days": 26.3,
      "offer_acceptance_rate": 66.7
    }
  ],
  "meta": { ... }
}
```

---

## `GET /analytics/job-board-performance`

Breakdown of applications, views, and hires per external job board.

**Response 200**

```json
{
  "data": [
    { "board": "linkedin",  "views": 4820, "applications": 148, "apply_rate": 3.07, "hires": 3 },
    { "board": "indeed",    "views": 3210, "applications": 97,  "apply_rate": 3.02, "hires": 2 },
    { "board": "glassdoor", "views": 980,  "applications": 31,  "apply_rate": 3.16, "hires": 1 }
  ],
  "meta": { ... }
}
```

---

---

# EMAIL TEMPLATES API

## `GET /email-templates`

List all email templates for the authenticated company.

**Query Parameters** — `template_type`, `is_active`, `page`, `per_page`

**Response 200** — Paginated list of template objects.

---

## `POST /email-templates`

Create a new email template.

**Request Body**

```json
{
  "name": "Technical Assessment Invitation",
  "subject": "Next Steps: Technical Assessment for {{job_title}} at {{company_name}}",
  "body_html": "<p>Hi {{candidate_first_name}},</p><p>Thank you for your application...</p>",
  "body_text": "Hi {{candidate_first_name}}, Thank you for your application...",
  "template_type": "interview_invitation",
  "variables": ["{{candidate_first_name}}", "{{job_title}}", "{{company_name}}", "{{assessment_link}}"]
}
```

**Response 201** — Returns created template object.

---

## `GET /email-templates/:id`

Fetch a single template.

**Response 200** — Full template object.

---

## `PUT /email-templates/:id`

Update template content.

**Request Body** — Any subset of template fields.

**Response 200** — Returns updated template.

---

## `DELETE /email-templates/:id`

Soft-delete a template (`is_active = FALSE`). Templates in use by pipeline stages cannot be deleted.

**Response 204** — No content.

**Error Responses**

| Status | Code                   | Condition                                               |
|--------|------------------------|---------------------------------------------------------|
| 422    | `unprocessable_entity` | Template is referenced by one or more pipeline stages   |

---

## `POST /email-templates/:id/preview`

Render template with sample merge data.

**Request Body**

```json
{
  "variables": {
    "candidate_first_name": "Jane",
    "job_title": "Senior Backend Engineer",
    "company_name": "Acme Financial",
    "assessment_link": "https://assessments.example.com/token-123"
  }
}
```

**Response 200**

```json
{
  "data": {
    "subject": "Next Steps: Technical Assessment for Senior Backend Engineer at Acme Financial",
    "body_html": "<p>Hi Jane,</p><p>Thank you for your application...</p>",
    "body_text": "Hi Jane, Thank you for your application..."
  },
  "meta": { ... }
}
```

---

---

# CAMPAIGNS API

## `GET /campaigns`

List email campaigns for the authenticated company.

**Query Parameters** — `status`, `page`, `per_page`

**Response 200** — Paginated list of campaign objects with engagement stats.

---

## `POST /campaigns`

Create a new outbound email campaign.

**Request Body**

```json
{
  "name": "Q1 2025 — Engineering Talent Pipeline",
  "subject": "Exciting Engineering Opportunities at Acme Financial",
  "body_html": "<p>Hi {{first_name}},</p><p>We have exciting openings...</p>",
  "recipient_criteria": {
    "skills": ["Go", "Rust", "Kubernetes"],
    "location_country": "US",
    "applied_before": "2024-06-01",
    "not_hired": true,
    "not_opted_out": true
  }
}
```

**Response 201** — Returns created campaign object.

---

## `GET /campaigns/:id`

Fetch campaign details with live engagement stats.

**Response 200**

```json
{
  "data": {
    "id": "campaign-uuid",
    "name": "Q1 2025 — Engineering Talent Pipeline",
    "status": "sent",
    "recipient_count": 248,
    "open_count": 91,
    "click_count": 34,
    "open_rate": 36.7,
    "click_rate": 13.7,
    "sent_at": "2025-01-20T09:00:00Z"
  },
  "meta": { ... }
}
```

---

## `PUT /campaigns/:id`

Update a draft campaign before sending.

**Response 200** — Returns updated campaign object.

---

## `POST /campaigns/:id/schedule`

Schedule a campaign for future delivery.

**Request Body**

```json
{ "scheduled_at": "2025-01-20T09:00:00Z" }
```

**Response 200**

```json
{
  "data": { "id": "campaign-uuid", "status": "scheduled", "scheduled_at": "2025-01-20T09:00:00Z", "estimated_recipients": 248 },
  "meta": { ... }
}
```

---

## `POST /campaigns/:id/send-now`

Send a campaign immediately, bypassing the scheduled time. Requires `hr_admin` scope.

**Response 200**

```json
{
  "data": { "id": "campaign-uuid", "status": "sending", "initiated_at": "2025-01-20T10:05:00Z" },
  "meta": { ... }
}
```

---

## `GET /campaigns/:id/stats`

Detailed engagement statistics for a sent campaign.

**Response 200**

```json
{
  "data": {
    "campaign_id": "campaign-uuid",
    "sent": 248,
    "delivered": 245,
    "bounced": 3,
    "opened": 91,
    "clicked": 34,
    "unsubscribed": 2,
    "open_rate": 37.1,
    "click_rate": 13.9,
    "click_to_open_rate": 37.4,
    "top_links": [
      { "url": "https://recruitplatform.io/jobs/senior-backend-engineer", "clicks": 28 }
    ]
  },
  "meta": { ... }
}
```

---

---

# COMPANIES API

## `GET /companies/:id`

Fetch company profile. Recruiter tokens may only access their own company.

**Response 200** — Full company object matching the `companies` schema.

---

## `PUT /companies/:id`

Update company profile. Requires `hr_admin` or `executive` scope.

**Request Body**

```json
{
  "name": "Acme Financial Inc.",
  "description": "Acme Financial is a leading fintech company...",
  "website_url": "https://acmefinancial.com",
  "industry": "Fintech",
  "company_size": "201-500",
  "hq_location": "San Francisco, CA",
  "ats_settings": {
    "default_pipeline_id": "pipeline-uuid",
    "auto_reject_below_ai_score": 35,
    "require_approval_for_jobs": true,
    "offer_approval_required_roles": ["hiring_manager", "hr_admin"]
  }
}
```

**Response 200** — Returns updated company object.

---

## `GET /companies/:id/users`

List all recruiter users for a company. Requires `hr_admin` or `executive` scope.

**Query Parameters** — `role`, `is_active`, `page`, `per_page`

**Response 200**

```json
{
  "data": [
    {
      "id": "user-uuid",
      "first_name": "Alice",
      "last_name": "Chen",
      "email": "alice@acmefinancial.com",
      "role": "hr_admin",
      "is_active": true,
      "last_login_at": "2025-01-14T08:30:00Z",
      "created_at": "2024-06-01T00:00:00Z"
    }
  ],
  "pagination": { ... },
  "meta": { ... }
}
```

---

## `POST /companies/:id/users`

Invite a new recruiter to the company. Sends an invitation email with a signup link. Requires `hr_admin` or `executive` scope.

**Request Body**

```json
{
  "email": "bob@acmefinancial.com",
  "first_name": "Bob",
  "last_name": "Kumar",
  "role": "hiring_manager"
}
```

**Response 201**

```json
{
  "data": {
    "id": "user-uuid",
    "email": "bob@acmefinancial.com",
    "role": "hiring_manager",
    "invite_sent_at": "2025-01-15T11:00:00Z",
    "invite_expires_at": "2025-01-22T11:00:00Z"
  },
  "meta": { ... }
}
```

**Error Responses**

| Status | Code        | Condition                                        |
|--------|-------------|--------------------------------------------------|
| 409    | `conflict`  | Email already registered at this company         |

---

## `PUT /companies/:id/users/:userId`

Update a recruiter's role or active status. Requires `hr_admin` or `executive` scope.

**Request Body**

```json
{
  "role": "hr_admin",
  "is_active": true
}
```

**Response 200** — Returns updated recruiter user object.

---

## `DELETE /companies/:id/users/:userId`

Deactivate a recruiter account (`is_active = FALSE`). Hard deletion is not supported for audit compliance. Requires `hr_admin` or `executive` scope. Cannot deactivate the last active `hr_admin`.

**Response 200**

```json
{
  "data": { "id": "user-uuid", "is_active": false, "deactivated_at": "2025-01-15T12:00:00Z" },
  "meta": { ... }
}
```

**Error Responses**

| Status | Code                   | Condition                                                   |
|--------|------------------------|-------------------------------------------------------------|
| 422    | `unprocessable_entity` | Cannot deactivate the last active `hr_admin` for the company |

---

## Webhook Events

The platform emits webhook events to a company-configured HTTPS endpoint. Each event is signed with an HMAC-SHA256 signature in the `X-Webhook-Signature` header.

| Event                          | Trigger                                      |
|--------------------------------|----------------------------------------------|
| `application.received`         | New application submitted                    |
| `application.stage_moved`      | Application moved to a new pipeline stage    |
| `application.withdrawn`        | Candidate withdrew application               |
| `interview.scheduled`          | Interview created                            |
| `interview.completed`          | Interview marked as completed                |
| `feedback.submitted`           | Interview feedback submitted                 |
| `offer.sent`                   | Offer letter sent to candidate               |
| `offer.accepted`               | Candidate accepted offer                     |
| `offer.declined`               | Candidate declined offer                     |
| `background_check.completed`   | Background check result received             |

**Webhook Payload Structure**

```json
{
  "event": "application.stage_moved",
  "event_id": "evt-uuid",
  "company_id": "company-uuid",
  "timestamp": "2025-01-16T10:00:00Z",
  "data": {
    "application_id": "app-uuid",
    "job_id": "job-uuid",
    "from_stage": "Applied",
    "to_stage": "Phone Screen"
  }
}
```
