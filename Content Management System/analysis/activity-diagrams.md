# Activity Diagrams

## Overview
Activity diagrams model the key business processes and workflows within the CMS platform.

---

## 1. Post Creation and Publishing Workflow

```mermaid
flowchart TD
    Start([Author clicks New Post]) --> OpenEditor[Open Post Editor]
    OpenEditor --> WriteContent[Write Content]
    WriteContent --> AutoSave{Auto-save timer?}
    AutoSave -->|Yes| SaveRevision[Save Draft Revision]
    SaveRevision --> WriteContent
    AutoSave -->|No| AddMedia{Add Media?}
    AddMedia -->|Yes| UploadMedia[Upload / Select from Library]
    UploadMedia --> AddMedia
    AddMedia -->|No| AssignTaxonomy[Assign Categories & Tags]
    AssignTaxonomy --> SetSEO[Set SEO Metadata]
    SetSEO --> Preview{Preview?}
    Preview -->|Yes| RenderPreview[Render Preview in Active Theme]
    RenderPreview --> ReviewPreview{Satisfied?}
    ReviewPreview -->|No| WriteContent
    ReviewPreview -->|Yes| Submit[Submit for Review]
    Preview -->|No| Submit
    Submit --> NotifyEditor[Notify Assigned Editor]
    NotifyEditor --> EditorReviews[Editor Reviews Post]
    EditorReviews --> Decision{Decision}
    Decision -->|Return with feedback| ReturnDraft[Return to Draft with Feedback]
    ReturnDraft --> NotifyAuthor[Notify Author]
    NotifyAuthor --> WriteContent
    Decision -->|Schedule| SetDatetime[Set Scheduled Datetime]
    SetDatetime --> ScheduledState[Post → Scheduled]
    ScheduledState --> WaitForTime[Wait for Scheduled Time]
    WaitForTime --> PublishPost
    Decision -->|Publish now| PublishPost[Publish Post]
    PublishPost --> UpdateFeed[Update RSS / Atom Feed]
    UpdateFeed --> UpdateSitemap[Rebuild sitemap.xml]
    UpdateSitemap --> NotifySubscribers[Dispatch Subscriber Notifications]
    NotifySubscribers --> End([Post Live])
```

---

## 2. Widget Layout Customization Workflow

```mermaid
flowchart TD
    Start([Admin opens Widget Manager]) --> LoadTheme[Load Active Theme Zone Definitions]
    LoadTheme --> DisplayZones[Display Layout Zones and Current Widgets]
    DisplayZones --> Action{Admin Action}

    Action -->|Add widget| SelectWidget[Select Widget from Library]
    SelectWidget --> DragToZone[Drag Widget into Zone]
    DragToZone --> ValidateZone{Zone compatible?}
    ValidateZone -->|No| ShowWarning[Show Compatibility Warning]
    ShowWarning --> Action
    ValidateZone -->|Yes| OpenConfig[Open Widget Configuration Form]
    OpenConfig --> ConfigureWidget[Set Widget Parameters]
    ConfigureWidget --> SaveWidget[Save Widget Instance]
    SaveWidget --> Action

    Action -->|Reorder| DragReorder[Drag to Reorder Within Zone]
    DragReorder --> Action

    Action -->|Remove| RemoveWidget[Remove Widget from Zone]
    RemoveWidget --> Action

    Action -->|Preview| LivePreview[Show Live Preview in Browser]
    LivePreview --> Action

    Action -->|Save Layout| PersistLayout[Persist Layout to Database]
    PersistLayout --> InvalidateCache[Invalidate CDN Cache for Affected Pages]
    InvalidateCache --> End([Layout Active for All Visitors])
```

---

## 3. Comment Submission and Moderation Workflow

```mermaid
flowchart TD
    Start([Reader Submits Comment]) --> ValidateInput{Input valid?}
    ValidateInput -->|No| ShowError[Show Validation Error]
    ShowError --> Start
    ValidateInput -->|Yes| SpamCheck[Submit to Spam Filter]
    SpamCheck --> SpamScore{Spam score?}

    SpamScore -->|High – Spam| BlockComment[Discard Comment Silently]
    BlockComment --> End1([Done])

    SpamScore -->|Low – Auto-approve| CheckTrustLevel{Reader trust level?}
    CheckTrustLevel -->|Trusted / Registered| AutoApprove[Auto-approve Comment]
    AutoApprove --> PublishComment[Comment Visible on Post]
    PublishComment --> NotifyAuthor[Notify Post Author]
    NotifyAuthor --> NotifyParent{Reply to another comment?}
    NotifyParent -->|Yes| NotifyParentCommenter[Notify Parent Commenter]
    NotifyParent -->|No| End2([Done])
    NotifyParentCommenter --> End2

    CheckTrustLevel -->|Guest / New reader| QueueComment

    SpamScore -->|Medium – Queue| QueueComment[Place in Moderation Queue]
    QueueComment --> NotifyModerator[Notify Moderator]
    NotifyModerator --> ModeratorReviews[Moderator Opens Queue]
    ModeratorReviews --> ModDecision{Decision}
    ModDecision -->|Approve| PublishComment
    ModDecision -->|Reject| DeleteComment[Delete Comment]
    DeleteComment --> End3([Done])
    ModDecision -->|Spam| MarkSpam[Add to Spam List]
    MarkSpam --> End4([Done])
```

---

## 4. Theme Installation and Activation Workflow

```mermaid
flowchart TD
    Start([Admin opens Themes]) --> ChooseSource{Source?}

    ChooseSource -->|Marketplace| SearchMarketplace[Search Theme Marketplace]
    SearchMarketplace --> SelectTheme[Select Theme]
    ChooseSource -->|Upload| UploadPackage[Upload Theme Package]
    UploadPackage --> ValidatePackage{Package valid?}
    ValidatePackage -->|No| ShowUploadError[Show Validation Error]
    ShowUploadError --> Start

    SelectTheme --> InstallTheme[Download and Install Theme]
    ValidatePackage -->|Yes| InstallTheme

    InstallTheme --> CheckCompatibility{Compatible with CMS version?}
    CheckCompatibility -->|No| ShowCompatibilityWarning[Show Warning]
    ShowCompatibilityWarning --> AdminDecision{Proceed?}
    AdminDecision -->|No| End1([Cancelled])
    AdminDecision -->|Yes| ActivateTheme

    CheckCompatibility -->|Yes| PreviewOption{Preview first?}
    PreviewOption -->|Yes| LivePreviewTheme[Live Preview Theme]
    LivePreviewTheme --> ConfirmActivate{Activate?}
    ConfirmActivate -->|No| End2([Theme Installed but Inactive])
    ConfirmActivate -->|Yes| ActivateTheme[Activate Theme]
    PreviewOption -->|No| ActivateTheme

    ActivateTheme --> MigrateWidgets[Migrate Existing Widgets to New Zones]
    MigrateWidgets --> UnmappedZones{Unmapped zones?}
    UnmappedZones -->|Yes| ShowMigrationUI[Show Zone Migration Helper]
    ShowMigrationUI --> MapZones[Admin Maps Old Zones to New Zones]
    MapZones --> SaveActivation

    UnmappedZones -->|No| SaveActivation[Save Activation]
    SaveActivation --> InvalidateCache[Invalidate Full Site Cache]
    InvalidateCache --> End3([New Theme Active])
```

---

## 5. Multi-Site Setup Workflow

```mermaid
flowchart TD
    Start([Super Admin creates new site]) --> EnterDetails[Enter Site Name, Domain, and Slug]
    EnterDetails --> AssignOwner[Assign Site Owner / Admin]
    AssignOwner --> SelectTheme[Select Initial Theme]
    SelectTheme --> SelectPlugins[Select Default Plugins]
    SelectPlugins --> ConfirmCreate[Confirm Site Creation]
    ConfirmCreate --> ProvisionDB[Provision Site Database Schema / Tenant]
    ProvisionDB --> ConfigureDNS[Configure Domain DNS Record]
    ConfigureDNS --> DNSReady{DNS propagated?}
    DNSReady -->|No| WaitDNS[Wait / Show Pending Status]
    WaitDNS --> DNSReady
    DNSReady -->|Yes| SendOwnerInvite[Send Owner Invitation Email]
    SendOwnerInvite --> OwnerAccepts[Owner Accepts and Sets Password]
    OwnerAccepts --> SiteReady([Site Ready for Content])
```
