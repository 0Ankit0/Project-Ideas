# API Design — Learning Management System

**Base URL:** `https://api.lms.example.com/v1`

All endpoints are versioned under `/v1`. Future breaking changes will be introduced under `/v2` with a deprecation notice and a minimum 90-day parallel-run window.

---

## Authentication

### JWT Bearer Tokens

All requests (except `GET /certificates/verify/{serial}`) require a valid JWT in the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

Tokens are issued by the Identity Service and must be signed with RS256. The API gateway validates the signature, expiry, and `tenant_id` claim on every request.

#### Token Structure

```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "lms-key-2026-01"
  },
  "payload": {
    "sub": "usr_2001",
    "email": "learner@example.com",
    "tenant_id": "ten_01",
    "roles": ["learner"],
    "scopes": ["enrollments:read", "progress:write", "assessments:write"],
    "iss": "https://auth.lms.example.com",
    "aud": "https://api.lms.example.com",
    "iat": 1700000000,
    "exp": 1700003600,
    "jti": "tok_abc123"
  }
}
```

#### Role Hierarchy

| Role | Description |
|---|---|
| `learner` | Enrolled learner; read own data, submit progress and attempts. |
| `instructor` | Course instructor; grade attempts, post overrides, view cohort data. |
| `author` | Content author; create and edit courses, modules, lessons. |
| `staff` | Administrative staff; manage enrollments, cohorts, certificates. |
| `admin` | Tenant administrator; full access within tenant scope. |
| `platform_admin` | Cross-tenant platform administrator. |

#### Common Scope Tokens

| Scope | Description |
|---|---|
| `courses:read` | List and view courses. |
| `courses:write` | Create, update, publish, archive courses. |
| `enrollments:read` | View enrollment records. |
| `enrollments:write` | Create, drop, reactivate enrollments. |
| `progress:read` | View progress data. |
| `progress:write` | Post progress events. |
| `assessments:read` | View assessments and attempts. |
| `assessments:write` | Start and submit attempts. |
| `grades:read` | View grades. |
| `grades:write` | Post and override grades. |
| `certificates:read` | View certificates. |
| `certificates:write` | Issue and revoke certificates. |
| `reports:read` | Access reporting endpoints. |

---

## Common Headers

### Request Headers

| Header | Required | Description |
|---|---|---|
| `Authorization` | Yes | `Bearer <jwt_token>` |
| `Content-Type` | Yes (writes) | `application/json` |
| `Accept` | No | `application/json` (default) |
| `Idempotency-Key` | Conditional | Required for `POST` operations that create resources. UUID v4. |
| `X-Request-ID` | No | Client-generated trace ID propagated in responses. |
| `X-Tenant-ID` | No | Override tenant context (platform admin only). |

### Response Headers

| Header | Description |
|---|---|
| `X-Request-ID` | Echoed or generated request trace ID. |
| `X-RateLimit-Limit` | Maximum requests allowed in the current window. |
| `X-RateLimit-Remaining` | Requests remaining in the current window. |
| `X-RateLimit-Reset` | Unix timestamp when the rate limit window resets. |
| `Retry-After` | Seconds to wait before retrying (present on 429 responses). |
| `ETag` | Entity tag for optimistic concurrency on mutable resources. |

### Rate Limiting

Rate limits are enforced per `(tenant_id, user_id)` pair using a sliding window algorithm.

| Tier | Limit | Window |
|---|---|---|
| Standard (learner/instructor) | 600 requests | 60 seconds |
| Author/Staff | 1,200 requests | 60 seconds |
| Admin | 3,000 requests | 60 seconds |
| Reporting endpoints | 30 requests | 60 seconds |

When the limit is exceeded the API returns `429 Too Many Requests` with a `Retry-After` header.

### Idempotency Keys

All `POST` endpoints that create or mutate persistent state require an `Idempotency-Key` header. The key must be a client-generated UUID v4 and must be unique per logical operation.

- The server stores idempotency results for **24 hours**.
- A repeated request with the same key within the window returns the cached response without re-executing the operation.
- A repeated request with the same key but a different body returns `422 Unprocessable Entity`.

```
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

---

## Pagination, Filtering, and Sorting

### Cursor-Based Pagination

Collections use cursor-based pagination for consistency across high-volume resources.

**Request parameters:**

| Parameter | Type | Description |
|---|---|---|
| `limit` | integer | Page size. Default `20`, max `100`. |
| `after` | string | Cursor pointing to the last item of the previous page. |
| `before` | string | Cursor pointing to the first item of the next page (backward). |

**Response envelope:**

```json
{
  "data": [ ],
  "pagination": {
    "limit": 20,
    "has_next_page": true,
    "has_previous_page": false,
    "start_cursor": "eyJpZCI6ImVucl8wMSJ9",
    "end_cursor": "eyJpZCI6ImVucl8yMCJ9"
  }
}
```

### Filtering

Filters are passed as query parameters. Multi-value filters use comma-separated lists.

**Example:** `GET /enrollments?status=active,completed&course_id=course_44`

### Sorting

Use `sort` (field name) and `order` (`asc` or `desc`) query parameters.

**Example:** `GET /enrollments?sort=created_at&order=desc`

---

## Error Response Format

All error responses follow a consistent envelope:

```json
{
  "error": {
    "code": "LMS_002",
    "message": "The course section has reached its seat limit.",
    "detail": "Course course_44 cohort cohort_2026_spring has a seat limit of 200 with 0 seats remaining.",
    "request_id": "req_abc123",
    "documentation_url": "https://docs.lms.example.com/errors/LMS_002"
  }
}
```

### LMS-Specific Error Codes

| Code | HTTP Status | Description |
|---|---|---|
| `LMS_001` | 422 | **Enrollment prerequisite not met.** Learner has not completed the required prerequisite courses or assessments. |
| `LMS_002` | 409 | **Seat limit reached.** The cohort or course section has no remaining seats. |
| `LMS_003` | 422 | **Enrollment window closed.** The enrollment open/close window for this cohort has passed. |
| `LMS_004` | 422 | **Attempt limit exceeded.** The learner has exhausted all allowed attempts for this assessment. |
| `LMS_005` | 422 | **Assessment timer expired.** The attempt was submitted after the allowed time window closed. |
| `LMS_006` | 409 | **Course version mismatch.** The requested operation targets a course version that is no longer active. |
| `LMS_007` | 409 | **Certificate already issued.** A certificate has already been issued for this enrollment; use revoke + reissue flow. |
| `LMS_008` | 409 | **Grade already published.** The grade is locked; use the grade override endpoint to modify it. |

### Standard HTTP Error Codes

| HTTP Status | Meaning |
|---|---|
| `400 Bad Request` | Malformed request syntax or missing required fields. |
| `401 Unauthorized` | Missing or invalid JWT token. |
| `403 Forbidden` | Valid token but insufficient role or scope for this operation. |
| `404 Not Found` | Resource does not exist or is not accessible to this tenant. |
| `409 Conflict` | Business rule conflict (see LMS-specific codes above). |
| `422 Unprocessable Entity` | Request is syntactically valid but violates domain rules. |
| `429 Too Many Requests` | Rate limit exceeded. |
| `500 Internal Server Error` | Unexpected server-side failure; a `request_id` is always included. |

---

## Endpoint Groups

---

### 1. Courses

#### `GET /courses`

List published courses available to the caller's tenant.

**Required roles/scopes:** Any authenticated user (`courses:read`)

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `status` | string | Filter by `draft`, `published`, `archived`. Default `published`. |
| `q` | string | Full-text search on title and description. |
| `limit` | integer | Page size (default 20, max 100). |
| `after` | string | Pagination cursor. |
| `sort` | string | `title`, `created_at`, `updated_at`. Default `created_at`. |
| `order` | string | `asc` or `desc`. Default `desc`. |

**Response `200 OK`:**

```json
{
  "data": [
    {
      "course_id": "course_44",
      "title": "Introduction to Machine Learning",
      "slug": "intro-to-ml",
      "status": "published",
      "version": "4",
      "description": "A hands-on introduction to supervised and unsupervised learning.",
      "thumbnail_url": "https://cdn.lms.example.com/courses/course_44/thumb.jpg",
      "duration_hours": 18,
      "level": "beginner",
      "tags": ["ml", "python", "data-science"],
      "created_at": "2025-06-01T00:00:00Z",
      "published_at": "2026-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "limit": 20,
    "has_next_page": false,
    "end_cursor": "eyJjb3Vyc2VfaWQiOiJjb3Vyc2VfNDQifQ"
  }
}
```

---

#### `POST /courses`

Create a new course draft.

**Required roles/scopes:** `author`, `admin` (`courses:write`)  
**Idempotency-Key:** Required

**Request body:**

```json
{
  "title": "Introduction to Machine Learning",
  "slug": "intro-to-ml",
  "description": "A hands-on introduction to supervised and unsupervised learning.",
  "level": "beginner",
  "thumbnail_url": "https://cdn.lms.example.com/courses/draft/thumb.jpg",
  "duration_hours": 18,
  "tags": ["ml", "python"],
  "prerequisite_course_ids": [],
  "settings": {
    "allow_self_enrollment": true,
    "certificate_enabled": true,
    "passing_grade_pct": 70
  }
}
```

**Response `201 Created`:**

```json
{
  "course_id": "course_44",
  "status": "draft",
  "version": "1",
  "created_at": "2026-01-01T00:00:00Z",
  "created_by": "usr_author_3"
}
```

**Possible errors:** `400`, `401`, `403`, `409` (slug conflict)

---

#### `GET /courses/{id}`

Retrieve full course details by ID.

**Required roles/scopes:** Any authenticated user (`courses:read`)

**Response `200 OK`:**

```json
{
  "course_id": "course_44",
  "title": "Introduction to Machine Learning",
  "slug": "intro-to-ml",
  "status": "published",
  "version": "4",
  "description": "A hands-on introduction...",
  "level": "beginner",
  "tags": ["ml", "python"],
  "prerequisite_course_ids": [],
  "settings": {
    "allow_self_enrollment": true,
    "certificate_enabled": true,
    "passing_grade_pct": 70
  },
  "module_count": 6,
  "lesson_count": 20,
  "duration_hours": 18,
  "created_at": "2025-06-01T00:00:00Z",
  "published_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

**Possible errors:** `401`, `403`, `404`

---

#### `PATCH /courses/{id}`

Update mutable fields on a draft or published course.

**Required roles/scopes:** `author`, `admin` (`courses:write`)  
**Concurrency:** Requires `If-Match: <etag>` header.

**Request body (partial update — all fields optional):**

```json
{
  "title": "Introduction to ML — Revised",
  "description": "Updated description.",
  "tags": ["ml", "python", "data-science"],
  "settings": {
    "passing_grade_pct": 75
  }
}
```

**Response `200 OK`:** Full updated course object (same schema as `GET /courses/{id}`).

**Possible errors:** `400`, `401`, `403`, `404`, `409` (ETag mismatch → `412 Precondition Failed`)

---

#### `DELETE /courses/{id}`

Soft-delete a draft course. Published or archived courses cannot be deleted; use archive instead.

**Required roles/scopes:** `admin` (`courses:write`)

**Response `204 No Content`**

**Possible errors:** `401`, `403`, `404`, `409` (course has active enrollments)

---

#### `PATCH /courses/{id}/publish`

Publish a draft course version, making it visible in the catalog.

**Required roles/scopes:** `admin` (`courses:write`)

**Request body:**

```json
{
  "change_summary": "Added Module 6: Transformers and fixed quiz errors."
}
```

**Response `200 OK`:**

```json
{
  "course_id": "course_44",
  "status": "published",
  "version": "4",
  "published_at": "2026-01-01T00:00:00Z"
}
```

**Emits:** `lms.course.published.v1`  
**Possible errors:** `401`, `403`, `404`, `422` (incomplete content), `LMS_006`

---

#### `PATCH /courses/{id}/archive`

Archive a published course version.

**Required roles/scopes:** `admin` (`courses:write`)

**Request body:**

```json
{
  "archive_reason": "superseded_by_new_version",
  "migration_target_course_id": "course_44",
  "migration_target_version": "5"
}
```

**Response `200 OK`:**

```json
{
  "course_id": "course_44",
  "status": "archived",
  "archived_at": "2026-06-01T00:00:00Z",
  "active_enrollments_affected": 12
}
```

**Emits:** `lms.course.archived.v1`  
**Possible errors:** `401`, `403`, `404`, `409`

---

### 2. Modules

#### `GET /courses/{id}/modules`

List all modules for a course in display order.

**Required roles/scopes:** Any authenticated user (`courses:read`)

**Response `200 OK`:**

```json
{
  "data": [
    {
      "module_id": "mod_210",
      "course_id": "course_44",
      "title": "Module 1: Foundations",
      "description": "Core concepts of supervised learning.",
      "position": 1,
      "lesson_count": 4,
      "is_published": true
    }
  ]
}
```

---

#### `POST /courses/{id}/modules`

Add a new module to a course.

**Required roles/scopes:** `author`, `admin` (`courses:write`)  
**Idempotency-Key:** Required

**Request body:**

```json
{
  "title": "Module 7: Reinforcement Learning",
  "description": "Basics of reward-based learning algorithms.",
  "position": 7
}
```

**Response `201 Created`:**

```json
{
  "module_id": "mod_270",
  "course_id": "course_44",
  "position": 7,
  "created_at": "2026-03-01T00:00:00Z"
}
```

**Possible errors:** `400`, `401`, `403`, `404`, `LMS_006`

---

#### `PATCH /modules/{id}`

Update a module's title, description, or position.

**Required roles/scopes:** `author`, `admin` (`courses:write`)

**Request body (all fields optional):**

```json
{
  "title": "Module 7: Reinforcement Learning — Updated",
  "position": 6
}
```

**Response `200 OK`:** Full updated module object.

**Possible errors:** `400`, `401`, `403`, `404`

---

#### `DELETE /modules/{id}`

Delete a module. Only allowed if the module has no lessons.

**Required roles/scopes:** `admin` (`courses:write`)

**Response `204 No Content`**

**Possible errors:** `401`, `403`, `404`, `409` (module has lessons)

---

### 3. Lessons

#### `GET /modules/{id}/lessons`

List all lessons within a module in display order.

**Required roles/scopes:** Any authenticated user (`courses:read`)

**Response `200 OK`:**

```json
{
  "data": [
    {
      "lesson_id": "lesson_900",
      "module_id": "mod_210",
      "title": "What is Supervised Learning?",
      "lesson_type": "video | text | interactive | scorm",
      "position": 1,
      "duration_seconds": 720,
      "is_published": true,
      "is_preview": false
    }
  ]
}
```

---

#### `POST /modules/{id}/lessons`

Create a new lesson in a module.

**Required roles/scopes:** `author`, `admin` (`courses:write`)  
**Idempotency-Key:** Required

**Request body:**

```json
{
  "title": "Linear Regression Deep Dive",
  "lesson_type": "video",
  "position": 2,
  "content_url": "https://cdn.lms.example.com/lessons/lesson_901/video.mp4",
  "duration_seconds": 900,
  "is_preview": false,
  "transcript_url": "https://cdn.lms.example.com/lessons/lesson_901/transcript.pdf"
}
```

**Response `201 Created`:**

```json
{
  "lesson_id": "lesson_901",
  "module_id": "mod_210",
  "position": 2,
  "created_at": "2026-03-05T00:00:00Z"
}
```

**Possible errors:** `400`, `401`, `403`, `404`

---

#### `GET /lessons/{id}`

Retrieve full lesson content for a learner. Access is validated against an active enrollment.

**Required roles/scopes:** `learner` with active enrollment, or `author`/`admin` (`courses:read`)

**Response `200 OK`:**

```json
{
  "lesson_id": "lesson_900",
  "module_id": "mod_210",
  "course_id": "course_44",
  "title": "What is Supervised Learning?",
  "lesson_type": "video",
  "content_url": "https://cdn.lms.example.com/lessons/lesson_900/video.mp4",
  "duration_seconds": 720,
  "transcript_url": "https://cdn.lms.example.com/lessons/lesson_900/transcript.pdf",
  "next_lesson_id": "lesson_901",
  "previous_lesson_id": null,
  "completion_status": "completed"
}
```

**Possible errors:** `401`, `403`, `404`

---

#### `PATCH /lessons/{id}`

Update lesson metadata or content URL.

**Required roles/scopes:** `author`, `admin` (`courses:write`)

**Request body (all fields optional):**

```json
{
  "title": "What is Supervised Learning? (Revised)",
  "content_url": "https://cdn.lms.example.com/lessons/lesson_900/video_v2.mp4",
  "duration_seconds": 780
}
```

**Response `200 OK`:** Full updated lesson object.

**Possible errors:** `400`, `401`, `403`, `404`

---

### 4. Enrollments

#### `GET /enrollments`

List enrollments. Learners see only their own; staff/admin can filter by learner or course.

**Required roles/scopes:** `enrollments:read`

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `learner_id` | string | Filter by learner (staff/admin only). |
| `course_id` | string | Filter by course. |
| `cohort_id` | string | Filter by cohort. |
| `status` | string | `active`, `completed`, `expired`, `dropped`. |
| `limit` | integer | Default 20, max 100. |
| `after` | string | Pagination cursor. |

**Response `200 OK`:**

```json
{
  "data": [
    {
      "enrollment_id": "enr_01J1ABCDEF",
      "learner_id": "usr_2001",
      "course_id": "course_44",
      "cohort_id": "cohort_2026_spring",
      "status": "active",
      "progress_pct": 75.0,
      "enrolled_at": "2026-01-15T00:00:00Z",
      "access_expires_at": "2026-07-15T00:00:00Z"
    }
  ],
  "pagination": { "limit": 20, "has_next_page": false }
}
```

---

#### `POST /enrollments`

Enroll a learner in a course.

**Required roles/scopes:** `learner` (self-enrollment), `staff`/`admin` (manual enrollment) (`enrollments:write`)  
**Idempotency-Key:** Required

**Request body:**

```json
{
  "learner_id": "usr_2001",
  "course_id": "course_44",
  "cohort_id": "cohort_2026_spring",
  "seat_type": "paid",
  "enrolled_by": "usr_admin_7",
  "access_expires_at": "2026-07-15T00:00:00Z",
  "prerequisites_waived": false
}
```

**Response `201 Created`:**

```json
{
  "enrollment_id": "enr_01J1ABCDEF",
  "learner_id": "usr_2001",
  "course_id": "course_44",
  "cohort_id": "cohort_2026_spring",
  "status": "active",
  "enrolled_at": "2026-01-15T09:00:00Z",
  "access_expires_at": "2026-07-15T00:00:00Z"
}
```

**Emits:** `lms.enrollment.created.v1`  
**Possible errors:** `400`, `401`, `403`, `LMS_001`, `LMS_002`, `LMS_003`

---

#### `GET /enrollments/{id}`

Get full detail for a single enrollment.

**Required roles/scopes:** Learner (own only), `staff`/`admin` (`enrollments:read`)

**Response `200 OK`:**

```json
{
  "enrollment_id": "enr_01J1ABCDEF",
  "learner_id": "usr_2001",
  "course_id": "course_44",
  "cohort_id": "cohort_2026_spring",
  "status": "active",
  "seat_type": "paid",
  "progress_pct": 75.0,
  "final_grade": null,
  "enrolled_at": "2026-01-15T09:00:00Z",
  "access_expires_at": "2026-07-15T00:00:00Z",
  "completed_at": null,
  "certificate_id": null
}
```

**Possible errors:** `401`, `403`, `404`

---

#### `PATCH /enrollments/{id}/drop`

Drop (withdraw) an active enrollment.

**Required roles/scopes:** Learner (self-drop), `staff`/`admin` (`enrollments:write`)

**Request body:**

```json
{
  "reason": "learner_request | administrative | non_payment",
  "notes": "Learner requested withdrawal for personal reasons."
}
```

**Response `200 OK`:**

```json
{
  "enrollment_id": "enr_01J1ABCDEF",
  "status": "dropped",
  "dropped_at": "2026-02-01T00:00:00Z"
}
```

**Possible errors:** `401`, `403`, `404`, `409` (already completed or dropped)

---

#### `PATCH /enrollments/{id}/reactivate`

Reactivate a dropped or expired enrollment.

**Required roles/scopes:** `staff`, `admin` (`enrollments:write`)  
**Idempotency-Key:** Required

**Request body:**

```json
{
  "new_access_expires_at": "2026-10-01T00:00:00Z",
  "reason": "Extension approved by department head."
}
```

**Response `200 OK`:**

```json
{
  "enrollment_id": "enr_01J1ABCDEF",
  "status": "active",
  "access_expires_at": "2026-10-01T00:00:00Z",
  "reactivated_at": "2026-07-16T00:00:00Z"
}
```

**Emits:** `lms.enrollment.created.v1` (type: `reactivation`)  
**Possible errors:** `401`, `403`, `404`, `409`

---

### 5. Assessments

#### `GET /assessments/{id}`

Retrieve assessment metadata and question structure (without revealing answers).

**Required roles/scopes:** Any authenticated user with course access (`assessments:read`)

**Response `200 OK`:**

```json
{
  "assessment_id": "asmt_320",
  "course_id": "course_44",
  "module_id": "mod_210",
  "title": "Module 1 Quiz",
  "type": "quiz | exam | assignment",
  "question_count": 40,
  "time_limit_seconds": 3600,
  "max_attempts": 3,
  "passing_score_pct": 70,
  "randomize_questions": true,
  "show_correct_answers_after_submission": false
}
```

---

#### `POST /assessments/{id}/attempts`

Start a new assessment attempt. Validates attempt count and enrollment status.

**Required roles/scopes:** `learner` (`assessments:write`)  
**Idempotency-Key:** Required

**Request body:**

```json
{
  "enrollment_id": "enr_01J1ABCDEF"
}
```

**Response `201 Created`:**

```json
{
  "attempt_id": "att_77MNOPQRST",
  "assessment_id": "asmt_320",
  "attempt_number": 2,
  "started_at": "2026-03-25T09:00:00Z",
  "deadline_at": "2026-03-25T10:00:00Z",
  "questions": [
    {
      "question_id": "q_01",
      "position": 1,
      "text": "What is overfitting?",
      "type": "multiple_choice",
      "options": [
        { "option_id": "opt_a", "text": "When a model trains too slowly." },
        { "option_id": "opt_b", "text": "When a model memorizes training data." },
        { "option_id": "opt_c", "text": "When the learning rate is too high." }
      ]
    }
  ]
}
```

**Emits:** `lms.assessment.attempt_started.v1`  
**Possible errors:** `401`, `403`, `404`, `LMS_004`

---

#### `GET /attempts/{id}`

Retrieve attempt details. Learners see their own attempt; instructors can see any.

**Required roles/scopes:** Learner (own only), `instructor`/`admin` (`assessments:read`)

**Response `200 OK`:**

```json
{
  "attempt_id": "att_77MNOPQRST",
  "assessment_id": "asmt_320",
  "enrollment_id": "enr_01J1ABCDEF",
  "learner_id": "usr_2001",
  "attempt_number": 2,
  "status": "in_progress | submitted | graded",
  "started_at": "2026-03-25T09:00:00Z",
  "deadline_at": "2026-03-25T10:00:00Z",
  "submitted_at": null,
  "score": null
}
```

---

#### `POST /attempts/{id}/submit`

Submit an assessment attempt for grading.

**Required roles/scopes:** `learner` (`assessments:write`)  
**Idempotency-Key:** Required

**Request body:**

```json
{
  "answers": [
    { "question_id": "q_01", "selected_option_id": "opt_b" },
    { "question_id": "q_02", "text_response": "Gradient descent minimizes the loss function." }
  ]
}
```

**Response `200 OK`:**

```json
{
  "attempt_id": "att_77MNOPQRST",
  "status": "submitted",
  "submitted_at": "2026-03-25T09:47:00Z",
  "grading_type": "auto",
  "estimated_grading_at": "2026-03-25T09:47:30Z"
}
```

**Emits:** `lms.assessment.submitted.v1`  
**Possible errors:** `401`, `403`, `404`, `409` (already submitted), `LMS_005`

---

#### `POST /attempts/{id}/grade`

Post or update grade for an attempt (manual or auto-grading system).

**Required roles/scopes:** `instructor`, `admin`, or grading system service account (`grades:write`)  
**Idempotency-Key:** Required

**Request body:**

```json
{
  "raw_score": 85.0,
  "max_score": 100.0,
  "graded_by": "usr_instructor_12",
  "feedback": "Good work overall. Review question 7 on regularization.",
  "release_to_learner": true
}
```

**Response `200 OK`:**

```json
{
  "grade_id": "grd_55ABCDE",
  "attempt_id": "att_77MNOPQRST",
  "raw_score": 85.0,
  "percentage": 85.0,
  "grade_band": "B",
  "passing": true,
  "released_at": "2026-03-25T11:00:00Z"
}
```

**Emits:** `lms.grade.posted.v1`  
**Possible errors:** `401`, `403`, `404`, `LMS_008`

---

### 6. Progress

#### `GET /enrollments/{id}/progress`

Get the full progress breakdown for an enrollment.

**Required roles/scopes:** Learner (own only), `instructor`/`staff`/`admin` (`progress:read`)

**Response `200 OK`:**

```json
{
  "enrollment_id": "enr_01J1ABCDEF",
  "learner_id": "usr_2001",
  "course_id": "course_44",
  "overall_progress_pct": 75.0,
  "lessons_completed": 15,
  "lessons_total": 20,
  "assessments_passed": 3,
  "assessments_total": 4,
  "last_active_at": "2026-03-23T10:00:00Z",
  "module_progress": [
    {
      "module_id": "mod_210",
      "title": "Module 1: Foundations",
      "progress_pct": 100.0,
      "lessons_completed": 4,
      "lessons_total": 4
    }
  ]
}
```

---

#### `POST /progress/events`

Record a learner progress checkpoint (e.g., lesson viewed, video watched to N%).

**Required roles/scopes:** `learner` (`progress:write`)  
**Idempotency-Key:** Required

**Request body:**

```json
{
  "enrollment_id": "enr_01J1ABCDEF",
  "lesson_id": "lesson_900",
  "event_type": "lesson_completed | video_progress | page_view",
  "percent_complete": 100,
  "time_spent_seconds": 720,
  "recorded_at": "2026-03-23T10:00:00Z"
}
```

**Response `202 Accepted`:**

```json
{
  "progress_event_id": "pe_99ABCDEF",
  "status": "accepted",
  "enrollment_progress_pct": 75.0
}
```

**Emits:** `lms.lesson.completed.v1`, `lms.progress.updated.v1` (conditional)  
**Possible errors:** `400`, `401`, `403`, `404`

---

### 7. Certificates

#### `GET /certificates`

List certificates for the caller. Learners see their own; admin can filter by course or learner.

**Required roles/scopes:** `certificates:read`

**Query parameters:** `learner_id`, `course_id`, `status` (`active`, `revoked`), `limit`, `after`

**Response `200 OK`:**

```json
{
  "data": [
    {
      "certificate_id": "cert_ABCD1234",
      "serial_number": "LMS-2026-0042-ABCD",
      "learner_id": "usr_2001",
      "course_id": "course_44",
      "status": "active",
      "issued_at": "2026-04-11T08:00:00Z",
      "expires_at": null,
      "verification_url": "https://verify.lms.example.com/cert/LMS-2026-0042-ABCD"
    }
  ],
  "pagination": { "limit": 20, "has_next_page": false }
}
```

---

#### `GET /certificates/{id}`

Retrieve full certificate metadata.

**Required roles/scopes:** Learner (own), `staff`/`admin` (`certificates:read`)

**Response `200 OK`:**

```json
{
  "certificate_id": "cert_ABCD1234",
  "serial_number": "LMS-2026-0042-ABCD",
  "learner_id": "usr_2001",
  "learner_name": "Alex Johnson",
  "course_id": "course_44",
  "course_title": "Introduction to Machine Learning",
  "course_version": "4",
  "status": "active",
  "issued_at": "2026-04-11T08:00:00Z",
  "expires_at": null,
  "issuer": "lms-certificate-service",
  "verification_url": "https://verify.lms.example.com/cert/LMS-2026-0042-ABCD",
  "pdf_url": "https://cdn.lms.example.com/certificates/cert_ABCD1234.pdf"
}
```

**Possible errors:** `401`, `403`, `404`

---

#### `POST /certificates/{id}/revoke`

Revoke an active certificate.

**Required roles/scopes:** `admin` (`certificates:write`)  
**Idempotency-Key:** Required

**Request body:**

```json
{
  "revocation_reason": "academic_integrity_violation | data_correction | learner_request",
  "revocation_notes": "Academic integrity policy violation confirmed by committee.",
  "notify_learner": true
}
```

**Response `200 OK`:**

```json
{
  "certificate_id": "cert_ABCD1234",
  "status": "revoked",
  "revoked_at": "2026-05-01T10:00:00Z"
}
```

**Emits:** `lms.certificate.revoked.v1`  
**Possible errors:** `401`, `403`, `404`, `409` (already revoked)

---

#### `GET /certificates/verify/{serial}`

Public endpoint to verify a certificate by serial number. No authentication required.

**Response `200 OK` (valid):**

```json
{
  "valid": true,
  "serial_number": "LMS-2026-0042-ABCD",
  "learner_name": "Alex Johnson",
  "course_title": "Introduction to Machine Learning",
  "issued_at": "2026-04-11T08:00:00Z",
  "expires_at": null,
  "status": "active"
}
```

**Response `200 OK` (revoked):**

```json
{
  "valid": false,
  "serial_number": "LMS-2026-0042-ABCD",
  "status": "revoked",
  "revoked_at": "2026-05-01T10:00:00Z"
}
```

**Possible errors:** `404` (serial not found)

---

### 8. Reports

#### `GET /reports/cohort-performance`

Aggregate performance metrics for a cohort.

**Required roles/scopes:** `instructor`, `staff`, `admin` (`reports:read`)

**Query parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `cohort_id` | string | Yes | Target cohort. |
| `course_id` | string | Yes | Target course. |
| `as_of` | ISO 8601 | No | Snapshot date; defaults to now. |

**Response `200 OK`:**

```json
{
  "cohort_id": "cohort_2026_spring",
  "course_id": "course_44",
  "as_of": "2026-04-15T00:00:00Z",
  "total_enrollments": 198,
  "active": 120,
  "completed": 60,
  "dropped": 10,
  "expired": 8,
  "average_progress_pct": 68.4,
  "average_grade": 78.2,
  "pass_rate_pct": 85.0,
  "certificate_issued_count": 58,
  "assessment_summary": [
    {
      "assessment_id": "asmt_320",
      "title": "Module 1 Quiz",
      "average_score": 82.1,
      "pass_rate_pct": 91.0,
      "attempts_per_learner_avg": 1.3
    }
  ]
}
```

**Possible errors:** `400`, `401`, `403`, `404`

---

#### `GET /reports/learner-activity`

Detailed activity log for a specific learner within a course or across all courses.

**Required roles/scopes:** `instructor`, `staff`, `admin` (`reports:read`); Learner (own data only)

**Query parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `learner_id` | string | Yes | Target learner. |
| `course_id` | string | No | Scope to a specific course. |
| `from` | ISO 8601 | No | Activity start date. |
| `to` | ISO 8601 | No | Activity end date. |
| `limit` | integer | No | Default 50, max 200. |
| `after` | string | No | Pagination cursor. |

**Response `200 OK`:**

```json
{
  "learner_id": "usr_2001",
  "data": [
    {
      "event_type": "lesson_completed",
      "resource_id": "lesson_900",
      "resource_title": "What is Supervised Learning?",
      "course_id": "course_44",
      "occurred_at": "2026-03-23T10:00:00Z",
      "time_spent_seconds": 720
    },
    {
      "event_type": "assessment_submitted",
      "resource_id": "att_77MNOPQRST",
      "resource_title": "Module 1 Quiz — Attempt 2",
      "course_id": "course_44",
      "occurred_at": "2026-03-25T09:47:00Z",
      "score": 85.0
    }
  ],
  "pagination": { "limit": 50, "has_next_page": false }
}
```

**Possible errors:** `400`, `401`, `403`, `404`
