# BPMN Swimlane Diagrams — Backend as a Service (BaaS) Platform

**Version:** 1.0  
**Status:** Approved  
**Last Updated:** 2025-01-01  

These diagrams represent the process flows using swimlane-style Mermaid flowcharts. Each lane represents an actor or system component participating in the process.

---

## 1. Project Setup Swimlane

**Participants:** Project Owner | Control Plane Service | Adapter Registry | PostgreSQL

```mermaid
flowchart TD
    subgraph Owner["👤 Project Owner"]
        O1([Start])
        O2[Fill sign-up form:\nname, email, org, slug]
        O3[Verify email via\nlink in inbox]
        O4[Login to console]
        O5[Enter project name + slug]
        O6[Review environments\n+ API keys]
        O7([End: Project Ready])
    end

    subgraph CP["⚙️ Control Plane Service"]
        CP1{Validate registration:\nslug unique?\nemail valid?}
        CP2[Create Tenant record\nCreate admin AuthUser\nEmit TenantCreated]
        CP3[Send verification email\nvia Notification Service]
        CP4[Validate email token\nActivate AuthUser]
        CP5[Issue JWT\nfor admin session]
        CP6{Validate project slug:\nunique in tenant?\nQuota OK?}
        CP7[Create Project record\nEmit ProjectCreated]
        CP8[Provision Environment: dev\nGenerate API key\nInit UsageMeter]
        CP9[Provision Environment: staging\nGenerate API key\nInit UsageMeter]
        CP10[Provision Environment: prod\nGenerate API key\nInit UsageMeter]
        CP11[Emit 3x EnvironmentProvisioned\nWrite Audit Log entries]
    end

    subgraph AR["🔌 Adapter Registry"]
        AR1[Initialize default\ncapability placeholders\nfor new environments]
    end

    subgraph PG["🐘 PostgreSQL"]
        PG1[(INSERT tenant\n+ admin user)]
        PG2[(UPDATE user:\nstatus=active)]
        PG3[(INSERT project\n+ 3 environments\n+ 3 usage meters)]
        PG4[(INSERT audit\nlog entries)]
    end

    %% Flow
    O1 --> O2 --> CP1
    CP1 -->|Invalid| CP1
    CP1 -->|Valid| CP2
    CP2 --> PG1
    CP2 --> CP3
    CP3 --> O3
    O3 --> CP4
    CP4 --> PG2
    CP4 --> CP5
    CP5 --> O4
    O4 --> O5 --> CP6
    CP6 -->|Invalid| CP6
    CP6 -->|Valid| CP7
    CP7 --> PG3
    CP7 --> CP8
    CP8 --> CP9
    CP9 --> CP10
    CP10 --> CP11
    CP11 --> AR1
    CP11 --> PG4
    CP11 --> O6
    O6 --> O7
```

---

## 2. File Upload Swimlane

**Participants:** App Developer / End User | API Gateway | Storage Facade Service | Provider Adapter | PostgreSQL

```mermaid
flowchart TD
    subgraph Client["👤 App Developer / End User"]
        C1([Start: User selects file])
        C2[POST /storage/buckets/bucketId/files\nMultipart body + JWT/API key]
        C3[Client receives file metadata\n+ upload confirmation]
        C4[Request signed URL\nPOST /storage/files/fileId/signed-url]
        C5[Use signed URL to\naccess/download file]
        C6([End])
    end

    subgraph GW["🌐 API Gateway"]
        GW1{Authenticate:\nJWT or API key valid?\nEnvironment scope OK?}
        GW2[Route to\nStorage Facade]
        GW3[Route signed-URL\nrequest to Storage Facade]
    end

    subgraph SF["📁 Storage Facade Service"]
        SF1{Validate request:\nBucket exists?\nMIME type allowed?\nFile size ≤ limit?\nQuota OK?}
        SF2[Generate file_id UUID\nCompute SHA-256 checksum\nStream to provider adapter]
        SF3{Virus scan\nenabled on bucket?}
        SF4[Insert FileObject record\nstatus = scan_pending]
        SF5[Insert FileObject record\nstatus = active]
        SF6[Emit FileUploaded event]
        SF7{Check access policy:\nUser is owner\nor has admin role?}
        SF8[Generate HMAC-SHA256\nsigned URL\nexpiry = requested TTL]
        SF9[Validate signature\n+ expiry on access]
        SF10[Proxy file stream\nfrom provider]
    end

    subgraph PA["☁️ Provider Adapter\n(AWS S3 / GCS / MinIO)"]
        PA1[Receive streamed\nfile data]
        PA2[Write object to\nprovider storage\nunder file_id key]
        PA3[Confirm successful\nwrite + ETag]
        PA4[Receive read request\nfor object key]
        PA5[Stream object\nbytes back]
    end

    subgraph DB["🐘 PostgreSQL"]
        DB1[(INSERT FileObject\nbucket_id, name, size,\nchecksum, status)]
        DB2[(UPDATE FileObject\nstatus, scan_result)]
        DB3[(INSERT AuditLog\nFileUploaded entry)]
    end

    %% Upload flow
    C1 --> C2 --> GW1
    GW1 -->|Auth fail| AuthFail([HTTP 401/403])
    GW1 -->|Auth OK| GW2 --> SF1
    SF1 -->|Validation fail| ValFail([HTTP 413/415/429\nwith error details])
    SF1 -->|Valid| SF2
    SF2 --> PA1 --> PA2 --> PA3
    PA3 --> SF3
    SF3 -->|Scan enabled| SF4
    SF3 -->|No scan| SF5
    SF4 --> DB1
    SF5 --> DB1
    SF6 --> DB3
    DB1 --> SF6
    SF6 --> C3

    %% Signed URL flow
    C3 --> C4 --> GW3 --> SF7
    SF7 -->|Unauthorized| UnAuth([HTTP 403])
    SF7 -->|Authorized| SF8
    SF8 --> C5

    %% File access via signed URL
    C5 --> SF9
    SF9 -->|Invalid/expired| Expired([HTTP 403])
    SF9 -->|Valid| PA4 --> PA5 --> SF10 --> C5
    C5 --> C6
```

---

## 3. Function Execution Swimlane

**Participants:** App Developer / End User | API Gateway | Functions Service | Worker | Provider | PostgreSQL

```mermaid
flowchart TD
    subgraph Client["👤 App Developer / End User"]
        C1([Start: Invoke function])
        C2[POST /functions/fnId/invoke\nwith JWT or API key\n+ optional request body]
        C3[Receive HTTP response\nfrom function]
        C4([End])
    end

    subgraph GW["🌐 API Gateway"]
        GW1{Authenticate:\nJWT/API key valid?\nscope includes\nfunctions capability?}
        GW2[Route to\nFunctions Service]
    end

    subgraph FnSvc["⚡ Functions Service"]
        FN1{Function status\n= active?\nBinding healthy?}
        FN2{Concurrency check:\nRedis semaphore\n< max_concurrency?}
        FN3[Increment semaphore\nCreate ExecutionRecord\nstatus = queued]
        FN4[Emit ExecutionTriggered event\ntrigger_type = http]
        FN5[Wait for worker\ncompletion signal]
        FN6[Return worker response\nto API Gateway]
    end

    subgraph Worker["🔧 Worker Process"]
        W1[Receive ExecutionTriggered\nfrom event bus]
        W2[Set ExecutionRecord\nstatus = running]
        W3[Resolve SecretRefs:\nfetch values from\nexternal secret store]
        W4{All secrets\nresolved OK?}
        W5[Build execution env:\nstatic vars + secrets\n+ BAAS_EXECUTION_ID]
        W6[Start timeout timer\nT = timeout_seconds]
        W7[Invoke function\nin provider]
        W8[Stream stdout/stderr\nto log aggregator]
        W9{Execution\noutcome?}
        W10[Upload logs to\nobject storage]
        W11[Set status = completed\nduration_ms, exit_code]
        W12[Decrement semaphore]
        W13[Set status = failed/timeout\nDecrement semaphore]
        W14[Emit ExecutionCompleted\nor ExecutionFailed]
    end

    subgraph Provider["☁️ Provider\n(Lambda / Cloud Functions)"]
        P1[Cold-start or\nwarm container]
        P2[Execute function\ncode with env vars]
        P3[Return response\n+ exit code]
    end

    subgraph DB["🐘 PostgreSQL"]
        DB1[(INSERT ExecutionRecord\nstatus = queued)]
        DB2[(UPDATE ExecutionRecord\nstatus = running\nstarted_at)]
        DB3[(UPDATE ExecutionRecord\nstatus = completed/failed\nduration, exit_code, log_key)]
        DB4[(INSERT AuditLog)]
    end

    %% Flow
    C1 --> C2 --> GW1
    GW1 -->|Fail| AuthFail([HTTP 401/403])
    GW1 -->|OK| GW2 --> FN1
    FN1 -->|Not active| FnNotActive([HTTP 404/503])
    FN1 -->|Active| FN2
    FN2 -->|Exceeded - reject| RateLimit([HTTP 429])
    FN2 -->|OK| FN3
    FN3 --> DB1
    FN3 --> FN4
    FN4 --> W1
    W1 --> W2 --> DB2
    W2 --> W3
    W3 --> W4
    W4 -->|Fail| SecretFail[Emit ExecutionFailed\nsecret_resolution_failed]
    SecretFail --> W13
    W4 -->|OK| W5 --> W6 --> W7
    W7 --> P1 --> P2 --> P3
    P2 --> W8
    P3 --> W9
    W9 -->|Timeout| TimeoutKill[SIGTERM/SIGKILL\nprocess]
    TimeoutKill --> W13
    W9 -->|Error| W13
    W9 -->|Success| W11
    W11 --> W10
    W10 --> W12
    W12 --> W14
    W13 --> W14
    W14 --> DB3
    W14 --> DB4
    W14 --> FN5
    FN5 --> FN6 --> GW2 --> C3 --> C4
```

---

## 4. Provider Switchover Swimlane

**Participants:** Project Owner | Migration Orchestrator | Old Provider Adapter | New Provider Adapter | PostgreSQL

```mermaid
flowchart TD
    subgraph Owner["👤 Project Owner"]
        O1([Start: Owner decides to switch providers])
        O2[POST /switchover-plans\nsource_binding_id\ntarget_binding_id\ncapability=storage]
        O3[Review safety gate\nresults in console]
        O4[PATCH status=ready\nto begin pre-flight]
        O5{Monitor progress\ndashboard}
        O6[Optional: PATCH\nstatus=rolled_back\nif manual abort needed]
        O7([End: Switchover complete\nor rolled back])
    end

    subgraph Orch["🔄 Migration Orchestrator"]
        OR1{Validate:\nboth bindings active?\nsame capability?}
        OR2[Create SwitchoverPlan\nstatus = draft]
        OR3[Run pre-flight gates:\n1. Quiesce check\n2. Target connectivity]
        OR4{All gates\npassed?}
        OR5[Transition to IN_PROGRESS\nEmit SwitchoverStarted]
        OR6[Enable write-through mode:\nwrites go to both providers]
        OR7[Copy objects from source\nto target in batches\nUpdate progress_pct]
        OR8[Compute source checksum\nCompute target checksum]
        OR9{Checksums\nmatch?}
        OR10[Promote target to PRIMARY\nDemote source to SECONDARY\nDisable write-through]
        OR11[Transition to COMPLETED\nEmit SwitchoverCompleted]
        OR12[Trigger rollback:\nRestore source as PRIMARY\nDisable write-through]
        OR13[Transition to ROLLED_BACK\nEmit SwitchoverRolledBack]
    end

    subgraph OldProv["📦 Old Provider Adapter\n(Source: e.g., AWS S3)"]
        OP1[Quiesce check:\nQuery in-flight operations]
        OP2[Accept write-through\nnew writes]
        OP3[Serve read requests\nfor object keys during copy]
        OP4[Return checksums\nfor all objects]
        OP5[Transition to read-only\nfallback mode]
    end

    subgraph NewProv["📦 New Provider Adapter\n(Target: e.g., GCS)"]
        NP1[Connectivity check:\nvalidate credentials + bucket]
        NP2[Accept incoming\nobject writes from copy]
        NP3[Accept write-through\nnew writes]
        NP4[Return checksums\nfor all received objects]
        NP5[Become PRIMARY:\naccept all new writes]
    end

    subgraph DB["🐘 PostgreSQL"]
        DB1[(INSERT SwitchoverPlan\nstatus = draft)]
        DB2[(UPDATE SwitchoverPlan\nsafety_gates results)]
        DB3[(UPDATE SwitchoverPlan\nstatus = in_progress\nstarted_at)]
        DB4[(UPDATE SwitchoverPlan\nprogress_pct periodically)]
        DB5[(UPDATE CapabilityBindings\nis_primary flags)]
        DB6[(UPDATE SwitchoverPlan\nstatus = completed/rolled_back)]
        DB7[(INSERT AuditLog entries\nfor all transitions)]
    end

    %% Start flow
    O1 --> O2 --> OR1
    OR1 -->|Invalid| PlanError([HTTP 422 error])
    OR1 -->|Valid| OR2
    OR2 --> DB1
    OR2 --> O3

    %% Pre-flight
    O3 --> O4 --> OR3
    OR3 --> OP1
    OR3 --> NP1
    OP1 -->|In-flight ops| WaitDrain[Wait up to 5 min\nfor drain]
    WaitDrain -->|Timeout| OR4
    OP1 -->|Clear| OR4
    NP1 -->|Fail| OR4
    NP1 -->|Pass| OR4
    OR4 -->|Fail| GateFail[Return gate failure\ndetails to owner]
    GateFail --> DB2
    GateFail --> O3
    OR4 -->|Pass| OR5
    OR5 --> DB3

    %% Copy phase
    OR5 --> OR6
    OR6 --> OP2
    OR6 --> NP3
    OR6 --> OR7
    OR7 --> OP3
    OP3 --> NP2
    OR7 --> DB4
    OR7 --> O5
    O5 --> O6
    O6 -->|Manual abort| OR12

    %% Checksum phase
    OR7 --> OR8
    OR8 --> OP4
    OR8 --> NP4
    OP4 --> OR9
    NP4 --> OR9
    OR9 -->|Mismatch| OR12
    OR9 -->|Match| OR10

    %% Completion
    OR10 --> NP5
    OR10 --> OP5
    OR10 --> DB5
    OR10 --> OR11
    OR11 --> DB6
    OR11 --> DB7
    OR11 --> O7

    %% Rollback
    OR12 --> DB5
    OR12 --> OR13
    OR13 --> DB6
    OR13 --> DB7
    OR13 --> O7
```
