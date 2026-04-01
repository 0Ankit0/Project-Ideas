# ERD & Database Schema — Job Board and Recruitment Platform

## Overview

This document defines the complete relational database schema for the Job Board and Recruitment Platform. The database is PostgreSQL 15+ and leverages native features including UUID generation (`gen_random_uuid()`), JSONB columns, `TIMESTAMPTZ`, partial indexes, and row-level triggers for `updated_at` maintenance.

All monetary values use `DECIMAL(12,2)`. All timestamps are stored in UTC (`TIMESTAMPTZ`). Soft deletes are preferred over hard deletes for audit compliance. GDPR-erasure fields are explicitly modelled on the `applicant_profiles` table.

---

## ENUM Type Definitions

```sql
-- Recruiter role enum
CREATE TYPE recruiter_role AS ENUM (
    'recruiter',
    'hiring_manager',
    'hr_admin',
    'executive'
);

-- Job type enum
CREATE TYPE job_type AS ENUM (
    'full_time',
    'part_time',
    'contract',
    'internship',
    'temporary'
);

-- Remote policy enum
CREATE TYPE remote_policy AS ENUM (
    'onsite',
    'hybrid',
    'remote'
);

-- Salary display type enum
CREATE TYPE salary_display_type AS ENUM (
    'range',
    'exact',
    'hidden'
);

-- Job status enum
CREATE TYPE job_status AS ENUM (
    'draft',
    'pending_approval',
    'published',
    'paused',
    'closed',
    'archived'
);

-- Application status enum
CREATE TYPE application_status AS ENUM (
    'applied',
    'under_review',
    'shortlisted',
    'interviewing',
    'offer_extended',
    'hired',
    'rejected',
    'withdrawn'
);

-- Resume parsing status enum
CREATE TYPE parsing_status AS ENUM (
    'pending',
    'processing',
    'completed',
    'failed'
);

-- Pipeline stage type enum
CREATE TYPE stage_type AS ENUM (
    'sourced',
    'applied',
    'screening',
    'phone_screen',
    'technical_assessment',
    'interview',
    'offer',
    'hired',
    'rejected'
);

-- Interview type enum
CREATE TYPE interview_type AS ENUM (
    'phone',
    'video',
    'onsite',
    'panel',
    'technical',
    'behavioral',
    'final'
);

-- Interview status enum
CREATE TYPE interview_status AS ENUM (
    'scheduled',
    'confirmed',
    'completed',
    'cancelled',
    'no_show'
);

-- Overall rating enum
CREATE TYPE overall_rating AS ENUM (
    'strong_yes',
    'yes',
    'neutral',
    'no',
    'strong_no'
);

-- Offer status enum
CREATE TYPE offer_status AS ENUM (
    'draft',
    'pending_approval',
    'approved',
    'sent',
    'accepted',
    'declined',
    'rescinded',
    'expired'
);

-- Negotiation initiator enum
CREATE TYPE negotiation_initiator AS ENUM (
    'candidate',
    'recruiter'
);

-- Negotiation status enum
CREATE TYPE negotiation_status AS ENUM (
    'pending',
    'accepted',
    'rejected'
);

-- Background check status enum
CREATE TYPE bgcheck_status AS ENUM (
    'pending_consent',
    'initiated',
    'in_progress',
    'completed',
    'failed',
    'dispute'
);

-- Background check result enum
CREATE TYPE bgcheck_result AS ENUM (
    'clear',
    'consider',
    'suspended'
);

-- Email template type enum
CREATE TYPE email_template_type AS ENUM (
    'application_confirmation',
    'shortlist_notification',
    'interview_invitation',
    'rejection',
    'offer',
    'custom'
);

-- Campaign status enum
CREATE TYPE campaign_status AS ENUM (
    'draft',
    'scheduled',
    'sending',
    'sent',
    'failed'
);

-- Job requirement type enum
CREATE TYPE requirement_type AS ENUM (
    'required',
    'preferred',
    'nice_to_have'
);

-- Requirement category enum
CREATE TYPE requirement_category AS ENUM (
    'technical',
    'soft_skill',
    'education',
    'experience',
    'certification'
);

-- Question type enum
CREATE TYPE question_type AS ENUM (
    'text',
    'multiple_choice',
    'yes_no',
    'file_upload'
);
```

---

## Utility: updated_at Trigger Function

```sql
-- Reusable trigger function to auto-update updated_at on every row update.
-- Applied to all tables that have an updated_at column.
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

## Table 1: companies

Stores employer/company accounts. Each company is an independent tenant. `ats_settings` stores configurable ATS behaviour (e.g., custom rejection reasons, pipeline defaults). `subscription_tier` drives feature gating.

```sql
CREATE TABLE companies (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(255)    NOT NULL,
    slug                VARCHAR(100)    NOT NULL,
    website_url         VARCHAR(500),
    logo_url            VARCHAR(500),
    description         TEXT,
    industry            VARCHAR(100),
    company_size        VARCHAR(50),    -- e.g. '1-10', '11-50', '51-200', '201-500', '500+'
    hq_location         VARCHAR(255),
    founded_year        INTEGER,
    ats_settings        JSONB           NOT NULL DEFAULT '{}',
    subscription_tier   VARCHAR(50)     NOT NULL DEFAULT 'basic',
    is_active           BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT companies_slug_unique        UNIQUE (slug),
    CONSTRAINT companies_founded_year_check CHECK (founded_year >= 1800 AND founded_year <= EXTRACT(YEAR FROM NOW())),
    CONSTRAINT companies_subscription_tier_check
        CHECK (subscription_tier IN ('basic', 'growth', 'enterprise', 'trial'))
);

CREATE UNIQUE INDEX idx_companies_slug        ON companies (slug);
CREATE INDEX        idx_companies_is_active   ON companies (is_active);
CREATE INDEX        idx_companies_industry    ON companies (industry);
CREATE INDEX        idx_companies_created_at  ON companies (created_at DESC);

-- TRIGGER: auto-update updated_at
CREATE TRIGGER trg_companies_updated_at
    BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

---

## Table 2: recruiter_users

Internal users (recruiters, hiring managers, HR admins, executives) belonging to a company. Passwords are stored as bcrypt hashes. `calendar_oauth_token` holds encrypted OAuth tokens for Google Calendar / Outlook integration. `notification_preferences` is a JSONB map of event-type → delivery channel preferences.

```sql
CREATE TABLE recruiter_users (
    id                          UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id                  UUID            NOT NULL,
    first_name                  VARCHAR(100)    NOT NULL,
    last_name                   VARCHAR(100)    NOT NULL,
    email                       VARCHAR(255)    NOT NULL,
    password_hash               VARCHAR(255)    NOT NULL,
    role                        recruiter_role  NOT NULL DEFAULT 'recruiter',
    is_active                   BOOLEAN         NOT NULL DEFAULT TRUE,
    avatar_url                  VARCHAR(500),
    phone                       VARCHAR(50),
    timezone                    VARCHAR(100)    NOT NULL DEFAULT 'UTC',
    last_login_at               TIMESTAMPTZ,
    email_verified_at           TIMESTAMPTZ,
    mfa_enabled                 BOOLEAN         NOT NULL DEFAULT FALSE,
    mfa_secret                  VARCHAR(255),   -- encrypted TOTP secret
    calendar_oauth_token        JSONB           NOT NULL DEFAULT '{}',  -- encrypted at app layer
    notification_preferences    JSONB           NOT NULL DEFAULT '{
        "application_received": ["email", "in_app"],
        "stage_changed": ["in_app"],
        "interview_reminder": ["email", "in_app"],
        "offer_accepted": ["email", "in_app"],
        "feedback_due": ["email"]
    }',
    created_at                  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_recruiter_users_company
        FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE RESTRICT,
    CONSTRAINT recruiter_users_email_company_unique
        UNIQUE (email, company_id),
    CONSTRAINT recruiter_users_email_format_check
        CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE UNIQUE INDEX idx_recruiter_users_email           ON recruiter_users (email);
CREATE INDEX        idx_recruiter_users_company_id      ON recruiter_users (company_id);
CREATE INDEX        idx_recruiter_users_role            ON recruiter_users (role);
CREATE INDEX        idx_recruiter_users_is_active       ON recruiter_users (is_active) WHERE is_active = TRUE;

CREATE TRIGGER trg_recruiter_users_updated_at
    BEFORE UPDATE ON recruiter_users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

---

## Table 3: jobs

Core job postings. Supports full approval workflow (`status`, `approval_status`). `external_ids` stores third-party job board IDs (LinkedIn, Indeed, etc.). `distribution_status` tracks publish state on each external board. `application_count` and `view_count` are denormalised counters updated via triggers.

```sql
CREATE TABLE jobs (
    id                      UUID                PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id              UUID                NOT NULL,
    created_by              UUID                NOT NULL,
    title                   VARCHAR(255)        NOT NULL,
    slug                    VARCHAR(300)        NOT NULL,
    description             TEXT                NOT NULL,
    summary                 VARCHAR(500),
    department              VARCHAR(100),
    job_type                job_type            NOT NULL DEFAULT 'full_time',
    remote_policy           remote_policy       NOT NULL DEFAULT 'onsite',
    location                VARCHAR(255),
    city                    VARCHAR(100),
    state                   VARCHAR(100),
    country                 CHAR(2),            -- ISO 3166-1 alpha-2
    salary_min              DECIMAL(12,2),
    salary_max              DECIMAL(12,2),
    currency                CHAR(3)             NOT NULL DEFAULT 'USD',
    salary_display_type     salary_display_type NOT NULL DEFAULT 'range',
    status                  job_status          NOT NULL DEFAULT 'draft',
    approval_status         VARCHAR(50),        -- 'pending', 'approved', 'rejected'
    approved_by             UUID,
    approved_at             TIMESTAMPTZ,
    published_at            TIMESTAMPTZ,
    closed_at               TIMESTAMPTZ,
    expires_at              TIMESTAMPTZ,
    application_count       INTEGER             NOT NULL DEFAULT 0,
    view_count              INTEGER             NOT NULL DEFAULT 0,
    external_ids            JSONB               NOT NULL DEFAULT '{}',
    distribution_status     JSONB               NOT NULL DEFAULT '{}',
    is_featured             BOOLEAN             NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ         NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_jobs_company
        FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE RESTRICT,
    CONSTRAINT fk_jobs_created_by
        FOREIGN KEY (created_by) REFERENCES recruiter_users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_jobs_approved_by
        FOREIGN KEY (approved_by) REFERENCES recruiter_users (id) ON DELETE SET NULL,
    CONSTRAINT jobs_company_slug_unique
        UNIQUE (company_id, slug),
    CONSTRAINT jobs_salary_range_check
        CHECK (salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max),
    CONSTRAINT jobs_salary_positive_check
        CHECK (salary_min IS NULL OR salary_min >= 0),
    CONSTRAINT jobs_application_count_check
        CHECK (application_count >= 0),
    CONSTRAINT jobs_view_count_check
        CHECK (view_count >= 0),
    CONSTRAINT jobs_expires_after_published_check
        CHECK (expires_at IS NULL OR published_at IS NULL OR expires_at > published_at)
);

CREATE INDEX idx_jobs_company_id          ON jobs (company_id);
CREATE INDEX idx_jobs_status              ON jobs (status);
CREATE INDEX idx_jobs_created_by          ON jobs (created_by);
CREATE INDEX idx_jobs_location            ON jobs (location);
CREATE INDEX idx_jobs_published_at        ON jobs (published_at DESC) WHERE status = 'published';
CREATE INDEX idx_jobs_expires_at          ON jobs (expires_at)        WHERE expires_at IS NOT NULL;
CREATE INDEX idx_jobs_is_featured         ON jobs (is_featured)       WHERE is_featured = TRUE;
CREATE INDEX idx_jobs_job_type            ON jobs (job_type);
CREATE INDEX idx_jobs_remote_policy       ON jobs (remote_policy);
CREATE INDEX idx_jobs_department          ON jobs (department);
CREATE INDEX idx_jobs_full_text           ON jobs USING GIN (to_tsvector('english', title || ' ' || COALESCE(summary, '') || ' ' || description));

CREATE TRIGGER trg_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

---

## Table 4: job_requirements

Individual skill/experience requirements attached to a job. A single job can have multiple requirements of different types and categories.

```sql
CREATE TABLE job_requirements (
    id                  UUID                    PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id              UUID                    NOT NULL,
    requirement_type    requirement_type        NOT NULL DEFAULT 'required',
    category            requirement_category    NOT NULL,
    description         TEXT                    NOT NULL,
    years_experience    INTEGER,
    created_at          TIMESTAMPTZ             NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_job_requirements_job
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE,
    CONSTRAINT job_requirements_years_check
        CHECK (years_experience IS NULL OR years_experience >= 0)
);

CREATE INDEX idx_job_requirements_job_id  ON job_requirements (job_id);
CREATE INDEX idx_job_requirements_type    ON job_requirements (requirement_type);
```

---

## Table 5: job_questions

Custom screening questions that applicants must answer when applying for a specific job. `options` is a JSON array of strings for `multiple_choice` questions.

```sql
CREATE TABLE job_questions (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id          UUID            NOT NULL,
    question_text   TEXT            NOT NULL,
    question_type   question_type   NOT NULL DEFAULT 'text',
    options         JSONB,          -- ["Option A", "Option B"] for multiple_choice
    is_required     BOOLEAN         NOT NULL DEFAULT TRUE,
    sort_order      INTEGER         NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_job_questions_job
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE,
    CONSTRAINT job_questions_sort_order_check
        CHECK (sort_order >= 0)
);

CREATE INDEX idx_job_questions_job_id     ON job_questions (job_id);
CREATE INDEX idx_job_questions_sort_order ON job_questions (job_id, sort_order);
```

---

## Table 6: applicant_profiles

Candidate identity record. One profile per email address across the entire platform. Contains GDPR fields: `is_gdpr_erased` flags that PII has been wiped, `data_retention_expires_at` drives automated deletion jobs.

```sql
CREATE TABLE applicant_profiles (
    id                          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email                       VARCHAR(255) NOT NULL,
    first_name                  VARCHAR(100),
    last_name                   VARCHAR(100),
    phone                       VARCHAR(50),
    linkedin_url                VARCHAR(500),
    github_url                  VARCHAR(500),
    portfolio_url               VARCHAR(500),
    location                    VARCHAR(255),
    headline                    VARCHAR(255),
    bio                         TEXT,
    is_gdpr_erased              BOOLEAN     NOT NULL DEFAULT FALSE,
    consent_given_at            TIMESTAMPTZ,
    data_retention_expires_at   TIMESTAMPTZ,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT applicant_profiles_email_unique
        UNIQUE (email),
    CONSTRAINT applicant_profiles_email_format_check
        CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT applicant_profiles_retention_after_consent_check
        CHECK (data_retention_expires_at IS NULL OR consent_given_at IS NULL
               OR data_retention_expires_at > consent_given_at)
);

CREATE UNIQUE INDEX idx_applicant_profiles_email       ON applicant_profiles (email);
CREATE INDEX        idx_applicant_profiles_is_erased   ON applicant_profiles (is_gdpr_erased);
CREATE INDEX        idx_applicant_profiles_retention   ON applicant_profiles (data_retention_expires_at)
    WHERE data_retention_expires_at IS NOT NULL AND is_gdpr_erased = FALSE;

CREATE TRIGGER trg_applicant_profiles_updated_at
    BEFORE UPDATE ON applicant_profiles
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

---

## Table 7: resumes

Uploaded resume files with AI-parsed structured data. `parsed_skills`, `parsed_education`, and `parsed_experience` store structured JSON extracted by the resume parser service. `is_primary` designates the default resume shown to recruiters.

```sql
CREATE TABLE resumes (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    applicant_id        UUID            NOT NULL,
    file_url            VARCHAR(500)    NOT NULL,
    file_name           VARCHAR(255)    NOT NULL,
    file_size_bytes     INTEGER,
    file_type           VARCHAR(50),    -- 'application/pdf', 'application/docx'
    parsed_text         TEXT,
    parsed_skills       JSONB,          -- [{"name": "Python", "confidence": 0.97}]
    parsed_education    JSONB,          -- [{"institution": "MIT", "degree": "BS CS", "year": 2019}]
    parsed_experience   JSONB,          -- [{"company": "Google", "title": "SWE", "years": 3}]
    parsing_status      parsing_status  NOT NULL DEFAULT 'pending',
    parsing_error       TEXT,
    parsed_at           TIMESTAMPTZ,
    is_primary          BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_resumes_applicant
        FOREIGN KEY (applicant_id) REFERENCES applicant_profiles (id) ON DELETE CASCADE,
    CONSTRAINT resumes_file_size_check
        CHECK (file_size_bytes IS NULL OR file_size_bytes > 0)
);

CREATE INDEX idx_resumes_applicant_id     ON resumes (applicant_id);
CREATE INDEX idx_resumes_is_primary       ON resumes (applicant_id, is_primary) WHERE is_primary = TRUE;
CREATE INDEX idx_resumes_parsing_status   ON resumes (parsing_status) WHERE parsing_status IN ('pending', 'processing');
CREATE INDEX idx_resumes_parsed_skills    ON resumes USING GIN (parsed_skills);

CREATE TRIGGER trg_resumes_updated_at
    BEFORE UPDATE ON resumes
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

---

## Table 8: cover_letters

Optional cover letters submitted by candidates. May be either a text body or an uploaded file; at least one of `content` or `file_url` must be present.

```sql
CREATE TABLE cover_letters (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    applicant_id    UUID        NOT NULL,
    job_id          UUID,       -- nullable: generic letters not tied to a job
    content         TEXT,
    file_url        VARCHAR(500),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_cover_letters_applicant
        FOREIGN KEY (applicant_id) REFERENCES applicant_profiles (id) ON DELETE CASCADE,
    CONSTRAINT fk_cover_letters_job
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE SET NULL,
    CONSTRAINT cover_letters_content_or_file_check
        CHECK (content IS NOT NULL OR file_url IS NOT NULL)
);

CREATE INDEX idx_cover_letters_applicant_id ON cover_letters (applicant_id);
CREATE INDEX idx_cover_letters_job_id       ON cover_letters (job_id) WHERE job_id IS NOT NULL;
```

---

## Table 9: skill_tags

Normalised skill taxonomy. `usage_count` is updated by trigger whenever a skill is attached to a job requirement or parsed from a resume. `is_verified` marks canonical/curated skills.

```sql
CREATE TABLE skill_tags (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,
    category        VARCHAR(100),
    is_verified     BOOLEAN     NOT NULL DEFAULT FALSE,
    usage_count     INTEGER     NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT skill_tags_name_unique   UNIQUE (name),
    CONSTRAINT skill_tags_usage_check   CHECK (usage_count >= 0)
);

CREATE UNIQUE INDEX idx_skill_tags_name         ON skill_tags (name);
CREATE INDEX        idx_skill_tags_category     ON skill_tags (category);
CREATE INDEX        idx_skill_tags_usage_count  ON skill_tags (usage_count DESC);
CREATE INDEX        idx_skill_tags_is_verified  ON skill_tags (is_verified) WHERE is_verified = TRUE;
```

---

## Table 10: email_templates

Reusable email templates scoped to a company. `variables` is a JSONB array listing the merge-tag names supported by this template (e.g., `["{{candidate_name}}", "{{job_title}}"]`).

```sql
CREATE TABLE email_templates (
    id              UUID                PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      UUID                NOT NULL,
    name            VARCHAR(255)        NOT NULL,
    subject         VARCHAR(500)        NOT NULL,
    body_html       TEXT                NOT NULL,
    body_text       TEXT,
    template_type   email_template_type NOT NULL DEFAULT 'custom',
    variables       JSONB               NOT NULL DEFAULT '[]',
    is_active       BOOLEAN             NOT NULL DEFAULT TRUE,
    created_by      UUID                NOT NULL,
    created_at      TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ         NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_email_templates_company
        FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE,
    CONSTRAINT fk_email_templates_created_by
        FOREIGN KEY (created_by) REFERENCES recruiter_users (id) ON DELETE RESTRICT,
    CONSTRAINT email_templates_name_company_unique
        UNIQUE (company_id, name)
);

CREATE INDEX idx_email_templates_company_id     ON email_templates (company_id);
CREATE INDEX idx_email_templates_template_type  ON email_templates (template_type);
CREATE INDEX idx_email_templates_is_active      ON email_templates (company_id, is_active) WHERE is_active = TRUE;

CREATE TRIGGER trg_email_templates_updated_at
    BEFORE UPDATE ON email_templates
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

---

## Table 11: pipelines

Hiring pipeline definitions. A company can have a default pipeline reused across jobs or create job-specific pipelines. `is_default` must be unique per company (enforced via partial unique index).

```sql
CREATE TABLE pipelines (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id  UUID        NOT NULL,
    job_id      UUID,       -- NULL = company default pipeline
    name        VARCHAR(255) NOT NULL,
    is_default  BOOLEAN     NOT NULL DEFAULT FALSE,
    created_by  UUID        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_pipelines_company
        FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE,
    CONSTRAINT fk_pipelines_job
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE,
    CONSTRAINT fk_pipelines_created_by
        FOREIGN KEY (created_by) REFERENCES recruiter_users (id) ON DELETE RESTRICT
);

-- Only one default pipeline per company
CREATE UNIQUE INDEX idx_pipelines_company_default
    ON pipelines (company_id) WHERE is_default = TRUE;

CREATE INDEX idx_pipelines_company_id   ON pipelines (company_id);
CREATE INDEX idx_pipelines_job_id       ON pipelines (job_id) WHERE job_id IS NOT NULL;

CREATE TRIGGER trg_pipelines_updated_at
    BEFORE UPDATE ON pipelines
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

---

## Table 12: pipeline_stages

Individual stages within a pipeline. `auto_move_rules` stores trigger conditions for automatic stage transitions (e.g., move to `rejected` if AI score < 40). `email_template_id` links the template auto-sent when an application enters this stage.

```sql
CREATE TABLE pipeline_stages (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_id         UUID        NOT NULL,
    name                VARCHAR(100) NOT NULL,
    stage_type          stage_type  NOT NULL,
    sort_order          INTEGER     NOT NULL DEFAULT 0,
    color               CHAR(7),    -- hex color e.g. '#3B82F6'
    auto_move_rules     JSONB       NOT NULL DEFAULT '{}',
    email_template_id   UUID,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_pipeline_stages_pipeline
        FOREIGN KEY (pipeline_id) REFERENCES pipelines (id) ON DELETE CASCADE,
    CONSTRAINT fk_pipeline_stages_email_template
        FOREIGN KEY (email_template_id) REFERENCES email_templates (id) ON DELETE SET NULL,
    CONSTRAINT pipeline_stages_sort_order_check
        CHECK (sort_order >= 0),
    CONSTRAINT pipeline_stages_color_check
        CHECK (color IS NULL OR color ~* '^#[0-9A-Fa-f]{6}$')
);

CREATE INDEX idx_pipeline_stages_pipeline_id    ON pipeline_stages (pipeline_id);
CREATE INDEX idx_pipeline_stages_sort_order     ON pipeline_stages (pipeline_id, sort_order);
CREATE INDEX idx_pipeline_stages_stage_type     ON pipeline_stages (stage_type);

CREATE TRIGGER trg_pipeline_stages_updated_at
    BEFORE UPDATE ON pipeline_stages
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

---

## Table 13: candidate_applications

Central application record linking a candidate to a job. Contains AI scoring fields populated by the resume-matching service, UTM attribution fields for source tracking, and GDPR-safe anonymisation flag.

```sql
CREATE TABLE candidate_applications (
    id                      UUID                PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id                  UUID                NOT NULL,
    applicant_id            UUID                NOT NULL,
    pipeline_id             UUID                NOT NULL,
    current_stage_id        UUID,
    status                  application_status  NOT NULL DEFAULT 'applied',
    resume_id               UUID,
    cover_letter_id         UUID,
    ai_score                DECIMAL(5,2),       -- 0.00 – 100.00
    ai_match_percentage     DECIMAL(5,2),       -- 0.00 – 100.00
    ai_extracted_skills     JSONB,              -- skills identified in resume
    ai_parsed_data          JSONB,              -- full AI analysis payload
    source                  VARCHAR(100),       -- 'linkedin', 'indeed', 'direct', 'referral'
    utm_source              VARCHAR(255),
    utm_medium              VARCHAR(255),
    utm_campaign            VARCHAR(255),
    answers                 JSONB               NOT NULL DEFAULT '{}',
    is_anonymous            BOOLEAN             NOT NULL DEFAULT FALSE,
    rejection_reason_id     UUID,               -- FK to rejection_reasons (future table)
    rejected_at             TIMESTAMPTZ,
    withdrawn_at            TIMESTAMPTZ,
    hired_at                TIMESTAMPTZ,
    applied_at              TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
    created_at              TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ         NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_applications_job
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE RESTRICT,
    CONSTRAINT fk_applications_applicant
        FOREIGN KEY (applicant_id) REFERENCES applicant_profiles (id) ON DELETE RESTRICT,
    CONSTRAINT fk_applications_pipeline
        FOREIGN KEY (pipeline_id) REFERENCES pipelines (id) ON DELETE RESTRICT,
    CONSTRAINT fk_applications_stage
        FOREIGN KEY (current_stage_id) REFERENCES pipeline_stages (id) ON DELETE SET NULL,
    CONSTRAINT fk_applications_resume
        FOREIGN KEY (resume_id) REFERENCES resumes (id) ON DELETE SET NULL,
    CONSTRAINT fk_applications_cover_letter
        FOREIGN KEY (cover_letter_id) REFERENCES cover_letters (id) ON DELETE SET NULL,
    CONSTRAINT applications_job_applicant_unique
        UNIQUE (job_id, applicant_id),
    CONSTRAINT applications_ai_score_range_check
        CHECK (ai_score IS NULL OR (ai_score >= 0 AND ai_score <= 100)),
    CONSTRAINT applications_ai_match_range_check
        CHECK (ai_match_percentage IS NULL OR (ai_match_percentage >= 0 AND ai_match_percentage <= 100))
);

CREATE INDEX idx_applications_job_id            ON candidate_applications (job_id);
CREATE INDEX idx_applications_applicant_id      ON candidate_applications (applicant_id);
CREATE INDEX idx_applications_status            ON candidate_applications (status);
CREATE INDEX idx_applications_current_stage_id  ON candidate_applications (current_stage_id);
CREATE INDEX idx_applications_ai_score          ON candidate_applications (ai_score DESC NULLS LAST);
CREATE INDEX idx_applications_applied_at        ON candidate_applications (applied_at DESC);
CREATE INDEX idx_applications_source            ON candidate_applications (source);
CREATE INDEX idx_applications_pipeline_id       ON candidate_applications (pipeline_id);
-- Composite for recruiter kanban board
CREATE INDEX idx_applications_job_stage         ON candidate_applications (job_id, current_stage_id, applied_at DESC);

CREATE TRIGGER trg_applications_updated_at
    BEFORE UPDATE ON candidate_applications
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

---

## Table 14: interviews

Top-level interview record for an application. A single interview entity can have multiple rounds (see `interview_rounds`). `calendar_event_ids` is a JSONB map of `{google: "event_id", outlook: "event_id"}` per participant.

```sql
CREATE TABLE interviews (
    id                  UUID                PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id      UUID                NOT NULL,
    job_id              UUID                NOT NULL,
    company_id          UUID                NOT NULL,
    title               VARCHAR(255)        NOT NULL,
    interview_type      interview_type      NOT NULL DEFAULT 'video',
    status              interview_status    NOT NULL DEFAULT 'scheduled',
    scheduled_at        TIMESTAMPTZ         NOT NULL,
    duration_minutes    INTEGER             NOT NULL DEFAULT 60,
    location            TEXT,
    video_link          VARCHAR(500),
    video_platform      VARCHAR(50),        -- 'zoom', 'google_meet', 'teams', 'custom'
    meeting_id          VARCHAR(255),
    calendar_event_ids  JSONB               NOT NULL DEFAULT '{}',
    notes               TEXT,
    created_by          UUID                NOT NULL,
    created_at          TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ         NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_interviews_application
        FOREIGN KEY (application_id) REFERENCES candidate_applications (id) ON DELETE CASCADE,
    CONSTRAINT fk_interviews_job
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE RESTRICT,
    CONSTRAINT fk_interviews_company
        FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE RESTRICT,
    CONSTRAINT fk_interviews_created_by
        FOREIGN KEY (created_by) REFERENCES recruiter_users (id) ON DELETE RESTRICT,
    CONSTRAINT interviews_duration_check
        CHECK (duration_minutes > 0 AND duration_minutes <= 480)
);

CREATE INDEX idx_interviews_application_id  ON interviews (application_id);
CREATE INDEX idx_interviews_company_id      ON interviews (company_id);
CREATE INDEX idx_interviews_scheduled_at    ON interviews (scheduled_at);
CREATE INDEX idx_interviews_status          ON interviews (status);
CREATE INDEX idx_interviews_created_by      ON interviews (created_by);

CREATE TRIGGER trg_interviews_updated_at
    BEFORE UPDATE ON interviews
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

---

## Table 15: interview_rounds

Individual rounds within an interview. Each round is assigned to a specific interviewer. `status` mirrors `interview_status` allowing per-round tracking independent of the parent interview.

```sql
CREATE TABLE interview_rounds (
    id                  UUID                PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id        UUID                NOT NULL,
    round_number        INTEGER             NOT NULL,
    title               VARCHAR(255)        NOT NULL,
    interviewer_id      UUID                NOT NULL,
    scheduled_at        TIMESTAMPTZ         NOT NULL,
    duration_minutes    INTEGER             NOT NULL DEFAULT 60,
    status              interview_status    NOT NULL DEFAULT 'scheduled',
    completed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ         NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_interview_rounds_interview
        FOREIGN KEY (interview_id) REFERENCES interviews (id) ON DELETE CASCADE,
    CONSTRAINT fk_interview_rounds_interviewer
        FOREIGN KEY (interviewer_id) REFERENCES recruiter_users (id) ON DELETE RESTRICT,
    CONSTRAINT interview_rounds_number_unique
        UNIQUE (interview_id, round_number),
    CONSTRAINT interview_rounds_duration_check
        CHECK (duration_minutes > 0)
);

CREATE INDEX idx_interview_rounds_interview_id   ON interview_rounds (interview_id);
CREATE INDEX idx_interview_rounds_interviewer_id ON interview_rounds (interviewer_id);
CREATE INDEX idx_interview_rounds_scheduled_at   ON interview_rounds (scheduled_at);
```

---

## Table 16: interview_feedback

Structured scorecard submitted by an interviewer after completing a round. All score fields use `DECIMAL(3,1)` with a 1.0–5.0 scale. `scorecard` stores per-competency ratings as JSONB for flexible assessment frameworks.

```sql
CREATE TABLE interview_feedback (
    id                      UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_round_id      UUID            NOT NULL,
    interviewer_id          UUID            NOT NULL,
    application_id          UUID            NOT NULL,
    overall_rating          overall_rating  NOT NULL,
    technical_score         DECIMAL(3,1),
    communication_score     DECIMAL(3,1),
    culture_fit_score       DECIMAL(3,1),
    problem_solving_score   DECIMAL(3,1),
    scorecard               JSONB           NOT NULL DEFAULT '{}',
    strengths               TEXT,
    concerns                TEXT,
    recommendation          VARCHAR(50),    -- 'advance', 'hold', 'reject'
    notes                   TEXT,
    submitted_at            TIMESTAMPTZ,
    deadline_at             TIMESTAMPTZ,
    is_late                 BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_feedback_round
        FOREIGN KEY (interview_round_id) REFERENCES interview_rounds (id) ON DELETE CASCADE,
    CONSTRAINT fk_feedback_interviewer
        FOREIGN KEY (interviewer_id) REFERENCES recruiter_users (id) ON DELETE RESTRICT,
    CONSTRAINT fk_feedback_application
        FOREIGN KEY (application_id) REFERENCES candidate_applications (id) ON DELETE CASCADE,
    CONSTRAINT feedback_round_interviewer_unique
        UNIQUE (interview_round_id, interviewer_id),
    CONSTRAINT feedback_technical_score_check
        CHECK (technical_score IS NULL OR (technical_score >= 1.0 AND technical_score <= 5.0)),
    CONSTRAINT feedback_communication_score_check
        CHECK (communication_score IS NULL OR (communication_score >= 1.0 AND communication_score <= 5.0)),
    CONSTRAINT feedback_culture_score_check
        CHECK (culture_fit_score IS NULL OR (culture_fit_score >= 1.0 AND culture_fit_score <= 5.0)),
    CONSTRAINT feedback_problem_solving_score_check
        CHECK (problem_solving_score IS NULL OR (problem_solving_score >= 1.0 AND problem_solving_score <= 5.0))
);

CREATE INDEX idx_feedback_round_id         ON interview_feedback (interview_round_id);
CREATE INDEX idx_feedback_interviewer_id   ON interview_feedback (interviewer_id);
CREATE INDEX idx_feedback_application_id   ON interview_feedback (application_id);
CREATE INDEX idx_feedback_submitted_at     ON interview_feedback (submitted_at DESC NULLS LAST);
CREATE INDEX idx_feedback_is_late          ON interview_feedback (is_late) WHERE is_late = TRUE;
```

---

## Table 17: calendar_slots

Recruiter availability windows synced from external calendars or manually set. `interview_id` is set when a slot is booked, transitioning `is_available` to FALSE.

```sql
CREATE TABLE calendar_slots (
    id                          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id                UUID        NOT NULL,
    start_at                    TIMESTAMPTZ NOT NULL,
    end_at                      TIMESTAMPTZ NOT NULL,
    is_available                BOOLEAN     NOT NULL DEFAULT TRUE,
    interview_id                UUID,
    source                      VARCHAR(50) NOT NULL DEFAULT 'manual', -- 'google', 'outlook', 'manual'
    external_calendar_event_id  VARCHAR(255),
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_calendar_slots_recruiter
        FOREIGN KEY (recruiter_id) REFERENCES recruiter_users (id) ON DELETE CASCADE,
    CONSTRAINT fk_calendar_slots_interview
        FOREIGN KEY (interview_id) REFERENCES interviews (id) ON DELETE SET NULL,
    CONSTRAINT calendar_slots_time_order_check
        CHECK (end_at > start_at)
);

CREATE INDEX idx_calendar_slots_recruiter_id    ON calendar_slots (recruiter_id);
CREATE INDEX idx_calendar_slots_start_at        ON calendar_slots (start_at);
CREATE INDEX idx_calendar_slots_available       ON calendar_slots (recruiter_id, start_at, end_at)
    WHERE is_available = TRUE;

CREATE TRIGGER trg_calendar_slots_updated_at
    BEFORE UPDATE ON calendar_slots
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

---

## Table 18: offer_letters

Full offer letter record including compensation, benefits, equity, and DocuSign integration. Dual approval flags (`approved_by_hm`, `approved_by_hr`) support the standard two-gate approval workflow.

```sql
CREATE TABLE offer_letters (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id      UUID            NOT NULL,
    job_id              UUID            NOT NULL,
    company_id          UUID            NOT NULL,
    candidate_id        UUID            NOT NULL,
    template_id         UUID,
    status              offer_status    NOT NULL DEFAULT 'draft',
    salary              DECIMAL(12,2)   NOT NULL,
    currency            CHAR(3)         NOT NULL DEFAULT 'USD',
    start_date          DATE,
    position_title      VARCHAR(255)    NOT NULL,
    department          VARCHAR(100),
    reporting_to        VARCHAR(255),
    benefits_package    JSONB           NOT NULL DEFAULT '{}',
    equity_details      JSONB           NOT NULL DEFAULT '{}',
    signing_bonus       DECIMAL(12,2),
    document_url        VARCHAR(500),
    docusign_envelope_id VARCHAR(255),
    sent_at             TIMESTAMPTZ,
    accepted_at         TIMESTAMPTZ,
    declined_at         TIMESTAMPTZ,
    expires_at          TIMESTAMPTZ,
    approved_by_hm      BOOLEAN         NOT NULL DEFAULT FALSE,
    approved_by_hr      BOOLEAN         NOT NULL DEFAULT FALSE,
    created_by          UUID            NOT NULL,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_offer_letters_application
        FOREIGN KEY (application_id) REFERENCES candidate_applications (id) ON DELETE RESTRICT,
    CONSTRAINT fk_offer_letters_job
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE RESTRICT,
    CONSTRAINT fk_offer_letters_company
        FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE RESTRICT,
    CONSTRAINT fk_offer_letters_candidate
        FOREIGN KEY (candidate_id) REFERENCES applicant_profiles (id) ON DELETE RESTRICT,
    CONSTRAINT fk_offer_letters_template
        FOREIGN KEY (template_id) REFERENCES email_templates (id) ON DELETE SET NULL,
    CONSTRAINT fk_offer_letters_created_by
        FOREIGN KEY (created_by) REFERENCES recruiter_users (id) ON DELETE RESTRICT,
    CONSTRAINT offer_letters_salary_positive_check
        CHECK (salary > 0),
    CONSTRAINT offer_letters_signing_bonus_check
        CHECK (signing_bonus IS NULL OR signing_bonus >= 0),
    CONSTRAINT offer_letters_expires_after_sent_check
        CHECK (expires_at IS NULL OR sent_at IS NULL OR expires_at > sent_at)
);

CREATE INDEX idx_offer_letters_application_id   ON offer_letters (application_id);
CREATE INDEX idx_offer_letters_company_id       ON offer_letters (company_id);
CREATE INDEX idx_offer_letters_status           ON offer_letters (status);
CREATE INDEX idx_offer_letters_candidate_id     ON offer_letters (candidate_id);
CREATE INDEX idx_offer_letters_expires_at       ON offer_letters (expires_at)
    WHERE expires_at IS NOT NULL AND status = 'sent';

CREATE TRIGGER trg_offer_letters_updated_at
    BEFORE UPDATE ON offer_letters
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

---

## Table 19: offer_negotiations

Counter-offer exchange thread linked to an offer letter. Each row is one message in the negotiation. `status` transitions to `accepted` or `rejected` when the other party responds.

```sql
CREATE TABLE offer_negotiations (
    id                      UUID                    PRIMARY KEY DEFAULT gen_random_uuid(),
    offer_id                UUID                    NOT NULL,
    initiated_by            negotiation_initiator   NOT NULL,
    requested_salary        DECIMAL(12,2),
    requested_start_date    DATE,
    message                 TEXT                    NOT NULL,
    status                  negotiation_status      NOT NULL DEFAULT 'pending',
    responded_at            TIMESTAMPTZ,
    created_at              TIMESTAMPTZ             NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_offer_negotiations_offer
        FOREIGN KEY (offer_id) REFERENCES offer_letters (id) ON DELETE CASCADE,
    CONSTRAINT offer_negotiations_salary_positive_check
        CHECK (requested_salary IS NULL OR requested_salary > 0)
);

CREATE INDEX idx_offer_negotiations_offer_id    ON offer_negotiations (offer_id);
CREATE INDEX idx_offer_negotiations_status      ON offer_negotiations (status);
```

---

## Table 20: background_check_requests

Background check lifecycle tracking, integrated with providers such as Checkr. `check_types` is a JSONB array (e.g., `["criminal", "employment_verification", "education_verification"]`). `result_details` stores the raw provider response.

```sql
CREATE TABLE background_check_requests (
    id                      UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    offer_id                UUID            NOT NULL,
    application_id          UUID            NOT NULL,
    candidate_id            UUID            NOT NULL,
    provider                VARCHAR(50)     NOT NULL DEFAULT 'checkr',
    check_types             JSONB           NOT NULL DEFAULT '["criminal"]',
    candidate_consent_at    TIMESTAMPTZ,
    status                  bgcheck_status  NOT NULL DEFAULT 'pending_consent',
    external_check_id       VARCHAR(255),
    result                  bgcheck_result,
    result_details          JSONB,
    completed_at            TIMESTAMPTZ,
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_bgcheck_offer
        FOREIGN KEY (offer_id) REFERENCES offer_letters (id) ON DELETE RESTRICT,
    CONSTRAINT fk_bgcheck_application
        FOREIGN KEY (application_id) REFERENCES candidate_applications (id) ON DELETE RESTRICT,
    CONSTRAINT fk_bgcheck_candidate
        FOREIGN KEY (candidate_id) REFERENCES applicant_profiles (id) ON DELETE RESTRICT
);

CREATE INDEX idx_bgcheck_offer_id           ON background_check_requests (offer_id);
CREATE INDEX idx_bgcheck_application_id     ON background_check_requests (application_id);
CREATE INDEX idx_bgcheck_status             ON background_check_requests (status);
CREATE INDEX idx_bgcheck_external_check_id  ON background_check_requests (external_check_id)
    WHERE external_check_id IS NOT NULL;

CREATE TRIGGER trg_bgcheck_updated_at
    BEFORE UPDATE ON background_check_requests
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

---

## Table 21: campaign_messages

Outbound bulk email campaigns targeting candidate segments. `recipient_criteria` is a JSONB query spec describing the target audience (skills, location, application history). Engagement metrics (`open_count`, `click_count`) are incremented via webhook.

```sql
CREATE TABLE campaign_messages (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id          UUID            NOT NULL,
    name                VARCHAR(255)    NOT NULL,
    subject             VARCHAR(500)    NOT NULL,
    body_html           TEXT            NOT NULL,
    recipient_criteria  JSONB           NOT NULL DEFAULT '{}',
    status              campaign_status NOT NULL DEFAULT 'draft',
    scheduled_at        TIMESTAMPTZ,
    sent_at             TIMESTAMPTZ,
    recipient_count     INTEGER         NOT NULL DEFAULT 0,
    open_count          INTEGER         NOT NULL DEFAULT 0,
    click_count         INTEGER         NOT NULL DEFAULT 0,
    created_by          UUID            NOT NULL,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_campaigns_company
        FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE,
    CONSTRAINT fk_campaigns_created_by
        FOREIGN KEY (created_by) REFERENCES recruiter_users (id) ON DELETE RESTRICT,
    CONSTRAINT campaigns_recipient_count_check
        CHECK (recipient_count >= 0),
    CONSTRAINT campaigns_open_count_check
        CHECK (open_count >= 0),
    CONSTRAINT campaigns_click_count_check
        CHECK (click_count >= 0)
);

CREATE INDEX idx_campaigns_company_id   ON campaign_messages (company_id);
CREATE INDEX idx_campaigns_status       ON campaign_messages (status);
CREATE INDEX idx_campaigns_scheduled_at ON campaign_messages (scheduled_at)
    WHERE status = 'scheduled';
```

---

## Table 22: diversity_reports

Pre-aggregated EEO diversity statistics. Rows with `job_id IS NULL` represent company-wide reports. All distribution fields are JSONB maps of category label → count.

```sql
CREATE TABLE diversity_reports (
    id                          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id                  UUID        NOT NULL,
    job_id                      UUID,       -- NULL = company-wide
    report_period_start         DATE        NOT NULL,
    report_period_end           DATE        NOT NULL,
    gender_distribution         JSONB       NOT NULL DEFAULT '{}',
    race_ethnicity_distribution JSONB       NOT NULL DEFAULT '{}',
    age_distribution            JSONB       NOT NULL DEFAULT '{}',
    disability_status           JSONB       NOT NULL DEFAULT '{}',
    veteran_status              JSONB       NOT NULL DEFAULT '{}',
    pipeline_stage_distribution JSONB       NOT NULL DEFAULT '{}',
    generated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    generated_by                UUID        NOT NULL,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_diversity_reports_company
        FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE,
    CONSTRAINT fk_diversity_reports_job
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE SET NULL,
    CONSTRAINT fk_diversity_reports_generated_by
        FOREIGN KEY (generated_by) REFERENCES recruiter_users (id) ON DELETE RESTRICT,
    CONSTRAINT diversity_reports_period_check
        CHECK (report_period_end > report_period_start)
);

CREATE INDEX idx_diversity_reports_company_id       ON diversity_reports (company_id);
CREATE INDEX idx_diversity_reports_job_id           ON diversity_reports (job_id) WHERE job_id IS NOT NULL;
CREATE INDEX idx_diversity_reports_period_start     ON diversity_reports (report_period_start DESC);
```

---

## Table 23: hiring_analytics

Time-series metrics table for dashboard aggregation. `metric_type` is a string key (e.g., `'time_to_hire'`, `'applications_received'`, `'offer_acceptance_rate'`). `dimensions` carries additional breakdown dimensions as JSONB (e.g., `{"department": "Engineering", "recruiter_id": "..."}`).

```sql
CREATE TABLE hiring_analytics (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      UUID            NOT NULL,
    job_id          UUID,           -- NULL = company-level aggregation
    metric_date     DATE            NOT NULL,
    metric_type     VARCHAR(100)    NOT NULL,
    metric_value    DECIMAL(12,4)   NOT NULL,
    dimensions      JSONB           NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_analytics_company
        FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE,
    CONSTRAINT fk_analytics_job
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE SET NULL
);

CREATE INDEX idx_analytics_company_id       ON hiring_analytics (company_id);
CREATE INDEX idx_analytics_metric_date      ON hiring_analytics (company_id, metric_date DESC);
CREATE INDEX idx_analytics_metric_type      ON hiring_analytics (company_id, metric_type, metric_date DESC);
CREATE INDEX idx_analytics_job_id           ON hiring_analytics (job_id) WHERE job_id IS NOT NULL;
CREATE INDEX idx_analytics_dimensions       ON hiring_analytics USING GIN (dimensions);
```

---

## ERD Relationships Summary

```
companies          ──< recruiter_users      (company_id)
companies          ──< jobs                 (company_id)
companies          ──< pipelines            (company_id)
companies          ──< email_templates      (company_id)
companies          ──< campaign_messages    (company_id)
companies          ──< diversity_reports    (company_id)
companies          ──< hiring_analytics     (company_id)

recruiter_users    ──< jobs                 (created_by)
recruiter_users    ──< interview_rounds     (interviewer_id)
recruiter_users    ──< interview_feedback   (interviewer_id)
recruiter_users    ──< calendar_slots       (recruiter_id)

jobs               ──< job_requirements     (job_id)
jobs               ──< job_questions        (job_id)
jobs               ──< candidate_applications (job_id)
jobs               ──< interviews           (job_id)

applicant_profiles ──< resumes              (applicant_id)
applicant_profiles ──< cover_letters        (applicant_id)
applicant_profiles ──< candidate_applications (applicant_id)
applicant_profiles ──< offer_letters        (candidate_id)
applicant_profiles ──< background_check_requests (candidate_id)

pipelines          ──< pipeline_stages      (pipeline_id)
pipelines          ──< candidate_applications (pipeline_id)

pipeline_stages    ──< candidate_applications (current_stage_id)

candidate_applications ──< interviews       (application_id)
candidate_applications ──< offer_letters    (application_id)
candidate_applications ──< interview_feedback (application_id)

interviews         ──< interview_rounds     (interview_id)
interview_rounds   ──< interview_feedback   (interview_round_id)

offer_letters      ──< offer_negotiations   (offer_id)
offer_letters      ──< background_check_requests (offer_id)
```
