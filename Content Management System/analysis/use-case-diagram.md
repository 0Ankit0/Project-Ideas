# Use Case Diagram

## Overview
This document contains use case diagrams for all major actors in the CMS: Reader, Author, Editor, Administrator, and Super Admin.

---

## Complete System Use Case Diagram

```mermaid
graph TB
    subgraph Actors
        Reader((Reader))
        Author((Author))
        Editor((Editor))
        Admin((Admin))
        SuperAdmin((Super Admin))
        EmailProvider((Email Provider))
        SpamFilter((Spam Filter))
        SearchEngine((Search Engine))
    end

    subgraph "CMS Platform"
        UC1[Browse & Search Content]
        UC2[Comment on Posts]
        UC3[Subscribe to Newsletter]
        UC4[Manage Reader Profile]

        UC10[Create & Edit Posts]
        UC11[Upload Media]
        UC12[Submit for Review]
        UC13[View Revisions]
        UC14[View Author Analytics]

        UC20[Review Submissions]
        UC21[Publish / Schedule Posts]
        UC22[Return Post to Draft]
        UC23[Manage Taxonomies]

        UC30[Manage Themes & Widgets]
        UC31[Manage Navigation Menus]
        UC32[Manage Users & Roles]
        UC33[Moderate Comments]
        UC34[Manage Plugins]
        UC35[View Site Analytics]
        UC36[Manage Redirects]

        UC40[Manage Sites]
        UC41[View Network Analytics]
        UC42[Push Global Updates]
    end

    Reader --> UC1
    Reader --> UC2
    Reader --> UC3
    Reader --> UC4

    Author --> UC10
    Author --> UC11
    Author --> UC12
    Author --> UC13
    Author --> UC14

    Editor --> UC20
    Editor --> UC21
    Editor --> UC22
    Editor --> UC23
    Editor --> UC10
    Editor --> UC11

    Admin --> UC30
    Admin --> UC31
    Admin --> UC32
    Admin --> UC33
    Admin --> UC34
    Admin --> UC35
    Admin --> UC36
    Admin --> UC20
    Admin --> UC21

    SuperAdmin --> UC40
    SuperAdmin --> UC41
    SuperAdmin --> UC42
    SuperAdmin --> UC32

    UC2 --> SpamFilter
    UC3 --> EmailProvider
    UC1 --> SearchEngine
```

---

## Reader Use Cases

```mermaid
graph LR
    Reader((Reader))

    subgraph "Account"
        UC1[Register]
        UC2[Login / Logout]
        UC3[Reset Password]
        UC4[Manage Profile]
        UC5[Enable 2FA]
    end

    subgraph "Discovery"
        UC6[Browse Posts by Category]
        UC7[Search Posts]
        UC8[View Author Profile]
        UC9[Browse by Tag]
        UC10[Read Post]
    end

    subgraph "Engagement"
        UC11[Leave Comment]
        UC12[Reply to Comment]
        UC13[Subscribe to Newsletter]
        UC14[Subscribe to RSS Feed]
        UC15[Manage Notification Preferences]
    end

    Reader --> UC1
    Reader --> UC2
    Reader --> UC3
    Reader --> UC4
    Reader --> UC5
    Reader --> UC6
    Reader --> UC7
    Reader --> UC8
    Reader --> UC9
    Reader --> UC10
    Reader --> UC11
    Reader --> UC12
    Reader --> UC13
    Reader --> UC14
    Reader --> UC15
```

---

## Author Use Cases

```mermaid
graph LR
    Author((Author))

    subgraph "Account"
        UC1[Accept Invitation]
        UC2[Setup Profile & Bio]
        UC3[Enable 2FA]
    end

    subgraph "Content Creation"
        UC4[Create Post]
        UC5[Edit Post Draft]
        UC6[Upload Media]
        UC7[Embed Media in Post]
        UC8[Assign Categories & Tags]
        UC9[Set SEO Metadata]
        UC10[Preview Post]
        UC11[Set Featured Image]
    end

    subgraph "Publishing"
        UC12[Save as Draft]
        UC13[Submit for Review]
        UC14[Edit Returned Post]
    end

    subgraph "Revisions"
        UC15[View Revision History]
        UC16[Compare Revisions]
        UC17[Restore Revision]
    end

    subgraph "Analytics"
        UC18[View Post Performance]
        UC19[View Comment Notifications]
    end

    Author --> UC1
    Author --> UC2
    Author --> UC3
    Author --> UC4
    Author --> UC5
    Author --> UC6
    Author --> UC7
    Author --> UC8
    Author --> UC9
    Author --> UC10
    Author --> UC11
    Author --> UC12
    Author --> UC13
    Author --> UC14
    Author --> UC15
    Author --> UC16
    Author --> UC17
    Author --> UC18
    Author --> UC19
```

---

## Editor Use Cases

```mermaid
graph LR
    Editor((Editor))

    subgraph "Review Queue"
        UC1[View Pending Submissions]
        UC2[Preview Submitted Post]
        UC3[Add Inline Comments]
        UC4[Approve & Publish Post]
        UC5[Return Post to Draft]
        UC6[Schedule Post]
        UC7[Edit Post Directly]
    end

    subgraph "Taxonomy Management"
        UC8[Create Category]
        UC9[Edit Category]
        UC10[Delete Category]
        UC11[Create Tag]
        UC12[Merge Tags]
    end

    subgraph "Content Management"
        UC13[Archive Post]
        UC14[Trash Post]
        UC15[Restore Trashed Post]
        UC16[Manage Media Library]
    end

    Editor --> UC1
    Editor --> UC2
    Editor --> UC3
    Editor --> UC4
    Editor --> UC5
    Editor --> UC6
    Editor --> UC7
    Editor --> UC8
    Editor --> UC9
    Editor --> UC10
    Editor --> UC11
    Editor --> UC12
    Editor --> UC13
    Editor --> UC14
    Editor --> UC15
    Editor --> UC16
```

---

## Administrator Use Cases

```mermaid
graph LR
    Admin((Admin))

    subgraph "Site Configuration"
        UC1[Configure Site Settings]
        UC2[Install Theme]
        UC3[Activate Theme]
        UC4[Preview Theme]
        UC5[Configure Widget Zones]
        UC6[Add/Remove Widgets]
        UC7[Configure Widget Instance]
        UC8[Build Navigation Menu]
        UC9[Assign Menu to Zone]
        UC10[Manage Redirects]
    end

    subgraph "User Management"
        UC11[Invite Author/Editor]
        UC12[Change User Role]
        UC13[Suspend User]
        UC14[Delete User Account]
        UC15[View Audit Log]
    end

    subgraph "Moderation"
        UC16[Approve Comments]
        UC17[Reject / Spam Comments]
        UC18[Configure Spam Filter]
        UC19[Manage Comment Allowlist/Blocklist]
    end

    subgraph "Plugins"
        UC20[Install Plugin]
        UC21[Activate Plugin]
        UC22[Configure Plugin]
        UC23[Deactivate Plugin]
        UC24[Update Plugin]
        UC25[Uninstall Plugin]
    end

    subgraph "Analytics & Reporting"
        UC26[View Site Dashboard]
        UC27[View Author Performance]
        UC28[Export Subscriber List]
        UC29[Generate Reports]
    end

    Admin --> UC1
    Admin --> UC2
    Admin --> UC3
    Admin --> UC4
    Admin --> UC5
    Admin --> UC6
    Admin --> UC7
    Admin --> UC8
    Admin --> UC9
    Admin --> UC10
    Admin --> UC11
    Admin --> UC12
    Admin --> UC13
    Admin --> UC14
    Admin --> UC15
    Admin --> UC16
    Admin --> UC17
    Admin --> UC18
    Admin --> UC19
    Admin --> UC20
    Admin --> UC21
    Admin --> UC22
    Admin --> UC23
    Admin --> UC24
    Admin --> UC25
    Admin --> UC26
    Admin --> UC27
    Admin --> UC28
    Admin --> UC29
```

---

## Super Admin Use Cases

```mermaid
graph LR
    SuperAdmin((Super Admin))

    subgraph "Multi-Site"
        UC1[Create Site]
        UC2[Configure Site Domain]
        UC3[Assign Site Owner]
        UC4[Deactivate Site]
        UC5[Delete Site]
    end

    subgraph "Network Analytics"
        UC6[View Network Dashboard]
        UC7[View Per-Site Breakdown]
        UC8[Export Network Report]
    end

    subgraph "Global Management"
        UC9[Manage Global Users]
        UC10[Disable Account Globally]
        UC11[Push Plugin Updates to All Sites]
        UC12[Push Theme Updates to All Sites]
        UC13[View Global Audit Log]
    end

    SuperAdmin --> UC1
    SuperAdmin --> UC2
    SuperAdmin --> UC3
    SuperAdmin --> UC4
    SuperAdmin --> UC5
    SuperAdmin --> UC6
    SuperAdmin --> UC7
    SuperAdmin --> UC8
    SuperAdmin --> UC9
    SuperAdmin --> UC10
    SuperAdmin --> UC11
    SuperAdmin --> UC12
    SuperAdmin --> UC13
```

---

## Use Case Relationships

```mermaid
graph TB
    subgraph "Include Relationships"
        SubmitPost[Submit Post for Review] -->|includes| ValidateTaxonomy[Validate Taxonomy Assignment]
        SubmitPost -->|includes| NotifyEditor[Notify Assigned Editor]

        PublishPost[Publish Post] -->|includes| GenerateFeed[Update RSS/Atom Feed]
        PublishPost -->|includes| UpdateSitemap[Update sitemap.xml]
        PublishPost -->|includes| NotifySubscribers[Notify Subscribers]

        PlaceWidget[Place Widget in Zone] -->|includes| ValidateZone[Validate Zone Exists in Theme]
        PlaceWidget -->|includes| SaveLayout[Save Widget Layout]
    end

    subgraph "Extend Relationships"
        CreatePost[Create Post] -.->|extends| SetScheduledDate[Set Scheduled Publish Date]
        CreatePost -.->|extends| SetFeaturedImage[Set Featured Image]

        BrowsePosts[Browse Posts] -.->|extends| FilterByTag[Filter by Tag]
        BrowsePosts -.->|extends| FilterByAuthor[Filter by Author]

        ModerateComment[Moderate Comment] -.->|extends| FlagAsSpam[Flag as Spam]
        ModerateComment -.->|extends| BanCommenter[Ban Commenter IP]
    end
```
