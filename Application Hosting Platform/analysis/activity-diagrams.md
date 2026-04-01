# Activity Diagrams & Business Process Flows

This document contains Mermaid flowchart representations of key business processes in the Application Hosting Platform.

## 1. Application Deployment Flow

```mermaid
flowchart TD
    Start([Developer Pushes Code]) --> GitHub["GitHub Webhook<br/>Triggers"]
    GitHub --> AHPReceive["AHP Receives<br/>Webhook"]
    AHPReceive --> Verify{Valid<br/>Webhook?}
    Verify -->|No| Discard["Discard Event"]
    Discard --> End1([End])
    
    Verify -->|Yes| Clone["Clone Repository<br/>at Commit SHA"]
    Clone --> Analyze["Analyze Project<br/>Detect Language"]
    Analyze --> DetectLang{Language<br/>Detected?}
    
    DetectLang -->|Node.js| SelectNPM["Select Node.js<br/>Buildpack"]
    DetectLang -->|Python| SelectPython["Select Python<br/>Buildpack"]
    DetectLang -->|Go| SelectGo["Select Go<br/>Buildpack"]
    DetectLang -->|Unknown| Alert["Alert Developer:<br/>Unsupported Language"]
    Alert --> End2([End])
    
    SelectNPM --> Build["Execute Build:<br/>npm install, npm run build"]
    SelectPython --> Build
    SelectGo --> Build
    
    Build --> BuildOK{Build<br/>Success?}
    BuildOK -->|No| BuildFail["Capture Error Logs"]
    BuildFail --> NotifyFail["Notify Developer:<br/>Build Failed"]
    NotifyFail --> Rollback["Keep Previous<br/>Version Running"]
    Rollback --> End3([End])
    
    BuildOK -->|Yes| CreateImage["Create Container<br/>Image"]
    CreateImage --> PushReg["Push Image to<br/>Container Registry"]
    PushReg --> ScanVuln["Scan Image for<br/>Vulnerabilities"]
    
    ScanVuln --> Deploy["Deploy Container<br/>to Cluster"]
    Deploy --> InjectEnv["Inject Environment<br/>Variables"]
    InjectEnv --> HealthCheck["Run Health Check<br/>GET /health"]
    
    HealthCheck --> HealthOK{Health<br/>Check<br/>Pass?}
    HealthOK -->|No| HealthFail["Stop New Container"]
    HealthFail --> NotifyHealthFail["Notify Developer:<br/>Health Check Failed"]
    NotifyHealthFail --> Rollback2["Keep Previous<br/>Version Running"]
    Rollback2 --> End4([End])
    
    HealthOK -->|Yes| RouteTraffic["Route Traffic to<br/>New Version"]
    RouteTraffic --> GracefulDrain["Gracefully Drain<br/>Old Version"]
    GracefulDrain --> StopOld["Stop Old<br/>Container"]
    StopOld --> Success["✓ Deployment<br/>Success"]
    Success --> NotifySuccess["Notify Developer:<br/>Deployed Successfully"]
    NotifySuccess --> UpdateHistory["Update Deployment<br/>History"]
    UpdateHistory --> End5([End])
    
    style Start fill:#90EE90
    style End1 fill:#FFB6C6
    style End2 fill:#FFB6C6
    style End3 fill:#FFB6C6
    style End4 fill:#FFB6C6
    style End5 fill:#90EE90
    style Success fill:#90EE90
    style BuildFail fill:#FFB6C6
    style HealthFail fill:#FFB6C6
```

**Key Decision Points:**
- Valid webhook signature verification
- Language detection (fallback to Dockerfile if unknown)
- Build success/failure
- Health check pass/fail
- Traffic routing to new version

---

## 2. Pull Request Preview Deployment Flow

```mermaid
flowchart TD
    Start([Developer Creates PR]) --> Webhook["GitHub Webhook:<br/>PR Created Event"]
    Webhook --> AHPReceive["AHP Receives<br/>PR Event"]
    
    AHPReceive --> GetBranch["Get PR Branch<br/>Name"]
    GetBranch --> CheckBuild["Check if Build<br/>Already Running"]
    
    CheckBuild -->|Already Building| Wait["Wait for<br/>Build"]
    Wait --> CheckBuildAgain{Build<br/>Done?}
    CheckBuildAgain -->|No| Wait
    CheckBuildAgain -->|Yes| Proceed["Proceed with Deploy"]
    
    CheckBuild -->|Not Building| Proceed
    
    Proceed --> BuildPreview["Build from<br/>PR Branch"]
    BuildPreview --> BuildOK{Build<br/>Success?}
    
    BuildOK -->|No| NotifyFail["Comment on PR:<br/>Build Failed"]
    NotifyFail --> End1([End])
    
    BuildOK -->|Yes| AllocDomain["Allocate Preview<br/>Domain"]
    AllocDomain --> GenDomain["Generate Domain:<br/>pr-{PR_ID}-app.ahp.io"]
    GenDomain --> DeployPreview["Deploy Preview<br/>Container"]
    DeployPreview --> HealthCheck["Health Check<br/>Preview App"]
    
    HealthCheck --> HealthOK{Healthy?}
    HealthOK -->|No| NotifyHealthFail["Comment on PR:<br/>Preview Deploy Failed"]
    NotifyHealthFail --> End2([End])
    
    HealthOK -->|Yes| Comment["Comment on PR:<br/>Preview Ready"]
    Comment --> PostLink["Post Preview Link:<br/>https://pr-{ID}-app.ahp.io"]
    PostLink --> Success["✓ Preview Available"]
    Success --> Await["Await PR Event"]
    
    Await --> EventCheck{PR Event?}
    EventCheck -->|PR Merged| Cleanup["Delete Preview<br/>Deployment"]
    EventCheck -->|PR Closed| Cleanup
    EventCheck -->|New Commit| Redeploy["Rebuild & Redeploy<br/>Preview"]
    Redeploy --> Await
    
    Cleanup --> CleanupDomain["Release Domain"]
    CleanupDomain --> End3([End])
    
    style Start fill:#90EE90
    style Success fill:#90EE90
    style End1 fill:#FFB6C6
    style End2 fill:#FFB6C6
    style End3 fill:#90EE90
    style Comment fill:#FFD700
    style PostLink fill:#FFD700
```

**Key Features:**
- Auto-trigger on PR creation
- Unique preview domain per PR
- Auto-cleanup when PR merged/closed
- Rebuild on new commits to PR branch

---

## 3. Auto-Scaling Decision Flow

```mermaid
flowchart TD
    Start([Scaling Evaluation<br/>Every 60s]) --> CollectMetrics["Collect CPU Metrics<br/>from All Instances"]
    CollectMetrics --> CalcAvg["Calculate Average<br/>CPU Usage"]
    CalcAvg --> CheckRules["Check Scaling<br/>Rules"]
    
    CheckRules --> RuleLoop{"Rule<br/>Matches?"}
    RuleLoop -->|No Rules Match| NoAction["No Action"]
    NoAction --> End1([End Evaluation])
    
    RuleLoop -->|Rule Matches| GetRule["Get Rule:<br/>Condition, Duration,<br/>Action"]
    GetRule --> CheckDuration["Has Condition Been<br/>True for N Minutes?"]
    
    CheckDuration -->|No| NoAction
    
    CheckDuration -->|Yes| CheckCooldown["In Cooldown<br/>Period?"}
    CheckCooldown -->|Yes| Postpone["Postpone Decision<br/>until Cooldown Ends"]
    Postpone --> End2([End Evaluation])
    
    CheckCooldown -->|No| CheckQuota["Check Resource<br/>Quota"]
    CheckQuota --> QuotaOK{Quota<br/>Available?}
    
    QuotaOK -->|No| Alert["Alert Owner:<br/>Quota Exceeded"]
    Alert --> End3([End])
    
    QuotaOK -->|Yes| DecideAction{Action:<br/>Scale Up<br/>or Down?}
    
    DecideAction -->|Scale Up| Prov["Provision New<br/>Instances"]
    Prov --> Deploy["Deploy Containers"]
    Deploy --> HealthCheck["Health Check<br/>New Instances"]
    HealthCheck --> Register["Register with<br/>Load Balancer"]
    Register --> StartCooldown["Start Cooldown<br/>Period"]
    
    DecideAction -->|Scale Down| Drain["Gracefully Drain<br/>Connections"]
    Drain --> Stop["Stop Instance"]
    Stop --> Deregister["Deregister from<br/>Load Balancer"]
    Deregister --> StartCooldown
    
    StartCooldown --> LogEvent["Log Scaling Event"]
    LogEvent --> Notify["Notify Owner:<br/>Scaled to N Instances"]
    Notify --> End4([End Evaluation])
    
    style Start fill:#90EE90
    style End1 fill:#FFD700
    style End2 fill:#FFD700
    style End3 fill:#FFB6C6
    style End4 fill:#90EE90
    style Alert fill:#FFB6C6
    style CheckCooldown fill:#FFD700
```

**Key Control Points:**
- Metric evaluation every 60 seconds
- Duration check (condition must be true for N minutes)
- Cooldown period prevents rapid oscillations
- Quota enforcement
- Graceful drain on scale-down

---

## 4. Add-on Provisioning Flow

```mermaid
flowchart TD
    Start([Developer Selects<br/>Add-on: PostgreSQL]) --> Config["Configure:<br/>Name, Size, Region<br/>Version"]
    Config --> ShowQuote["Show Cost Quote:<br/>$9.99/month"]
    ShowQuote --> Confirm{User<br/>Confirms?}
    
    Confirm -->|No| Cancel["User Cancels"]
    Cancel --> End1([End])
    
    Confirm -->|Yes| Validate["Validate Configuration"]
    Validate --> ValidOK{Config<br/>Valid?}
    
    ValidOK -->|No| Error["Show Error:<br/>Insufficient Quota"]
    Error --> End2([End])
    
    ValidOK -->|Yes| CheckQuota["Check Team Quota:<br/>Add-ons, Storage"]
    CheckQuota --> QuotaOK{Quota<br/>OK?}
    
    QuotaOK -->|No| QuotaError["Show Quota<br/>Exceeded Error"]
    QuotaError --> End3([End])
    
    QuotaOK -->|Yes| CallProvider["Call Add-on Provider<br/>API to Create"]
    CallProvider --> ProviderCreate["Provider Creates<br/>PostgreSQL Instance"]
    ProviderCreate --> Monitor["Monitor Creation<br/>Status"]
    Monitor --> MonitorLoop{Creation<br/>Complete?}
    
    MonitorLoop -->|No| Wait["Wait 30s"]
    Wait --> Monitor
    
    MonitorLoop -->|Yes| ProviderOK{Provider<br/>Success?}
    
    ProviderOK -->|Failed| ProviderError["Show Error:<br/>Provider Failure"]
    ProviderError --> End4([End])
    
    ProviderOK -->|Success| GetCreds["Get Connection<br/>Credentials"]
    GetCreds --> GenConnStr["Generate Connection<br/>String"]
    GenConnStr --> EncryptCreds["Encrypt & Store<br/>Credentials"]
    EncryptCreds --> CreateEnvVar["Create Environment<br/>Variable"]
    CreateEnvVar --> InjectApp["Inject into<br/>Application Config"]
    InjectApp --> RedeplApp["Redeploy Application<br/>with New Env Var"]
    RedeplApp --> VerifyConn["Verify Database<br/>Connection"]
    
    VerifyConn --> ConnOK{Connection<br/>OK?}
    ConnOK -->|No| ConnError["Warn User:<br/>Connection Failed"]
    ConnError --> End5([End])
    
    ConnOK -->|Yes| ConfigBackup["Configure Automated<br/>Backups"]
    ConfigBackup --> ConfigMetrics["Enable Metrics<br/>Collection"]
    ConfigMetrics --> Notify["Notify User:<br/>Add-on Ready"]
    Notify --> Success["✓ Add-on Provisioned"]
    Success --> End6([End])
    
    style Start fill:#90EE90
    style Success fill:#90EE90
    style End1 fill:#FFB6C6
    style End2 fill:#FFB6C6
    style End3 fill:#FFB6C6
    style End4 fill:#FFB6C6
    style End5 fill:#FFB6C6
    style End6 fill:#90EE90
    style CallProvider fill:#4A90E2
    style GetCreds fill:#4A90E2
    style ProviderCreate fill:#4A90E2
```

**Key Steps:**
- Configuration and cost estimation
- Quota validation
- Provider API call to create service
- Polling for completion
- Credential generation and injection
- Environment variable configuration
- Application redeployment
- Automated backup and metrics setup

---

## 5. Billing & Invoice Generation Flow

```mermaid
flowchart TD
    Start([Daily Usage<br/>Collection]) --> CollectUsage["Aggregate Resource<br/>Usage Metrics"]
    CollectUsage --> LogUsage["Log Usage Records:<br/>Compute Hours<br/>Bandwidth GB<br/>Storage GB"]
    LogUsage --> Accumulate["Accumulate to<br/>Current Month Total"]
    Accumulate --> Store["Store in<br/>Billing DB"]
    Store --> Daily["(Repeat Daily)")
    Daily --> End1["Continue"]
    
    Start2([First Day of<br/>Month]) --> CalcTotal["Calculate Total<br/>Month Charges"]
    CalcTotal --> ApplyDisc["Apply Discounts<br/>Credits"]
    ApplyDisc --> CalcTax["Calculate Tax<br/>by Region"]
    CalcTax --> GenInvoice["Generate Invoice<br/>Document"]
    GenInvoice --> InvoiceLogo["Add Logo, Terms<br/>Terms of Service"]
    InvoiceLogo --> SaveInvoice["Save Invoice<br/>to Database"]
    SaveInvoice --> SendEmail["Send Invoice<br/>Email to Owner"]
    SendEmail --> UpdateBilling["Update Billing<br/>Account"]
    UpdateBilling --> CheckAutoPay{AutoPay<br/>Enabled?}
    
    CheckAutoPay -->|No| AwaitPayment["Await Manual<br/>Payment"]
    AwaitPayment --> PaymentReceived["Payment Received<br/>Event"]
    
    CheckAutoPay -->|Yes| ChargeCard["Charge Credit<br/>Card via Stripe"]
    ChargeCard --> PaymentOK{Payment<br/>Success?}
    
    PaymentOK -->|No| PaymentFail["Payment Failed"]
    PaymentFail --> Retry["Retry Payment<br/>7 Days Later"]
    Retry --> End2([End])
    
    PaymentOK -->|Yes| PaymentReceived
    PaymentReceived --> RecordPayment["Record Payment<br/>on Invoice"]
    RecordPayment --> MarkPaid["Mark Invoice<br/>Paid"]
    MarkPaid --> SendReceipt["Send Receipt<br/>Email"]
    SendReceipt --> End3([End])
    
    style Start fill:#90EE90
    style Start2 fill:#FFD700
    style End1 fill:#FFD700
    style End2 fill:#FFB6C6
    style End3 fill:#90EE90
    style ChargeCard fill:#FF6B6B
    style PaymentFail fill:#FFB6C6
    style MarkPaid fill:#90EE90
```

**Process Tiers:**
- **Hourly**: Collect usage metrics (compute minutes, bandwidth, storage)
- **Daily**: Accumulate to running total
- **Monthly**: Generate invoice, apply discounts/tax, send to owner, attempt charge
- **Post-Payment**: Record payment, send receipt

---

**Document Version**: 1.0
**Last Updated**: 2024
