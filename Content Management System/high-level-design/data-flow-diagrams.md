# Data Flow Diagrams

## Overview
Data flow diagrams show how data moves through the CMS platform from external actors through the system processes to data stores.

---

## Level 0: Context DFD

```mermaid
graph LR
    Reader((Reader))
    Author((Author))
    Editor((Editor))
    Admin((Admin))
    SuperAdmin((Super Admin))

    CMS[CMS Platform]

    EmailSvc((Email Provider))
    SpamSvc((Spam Filter))
    MediaStore((Media Storage))
    SearchIdx((Search Index))

    Reader -->|"browse, comment, subscribe requests"| CMS
    Author -->|"post drafts, media uploads"| CMS
    Editor -->|"review decisions, taxonomy changes"| CMS
    Admin -->|"config, widget, user management"| CMS
    SuperAdmin -->|"site provisioning, global updates"| CMS

    CMS -->|"rendered pages, feeds, search results"| Reader
    CMS -->|"draft state, revision history, analytics"| Author
    CMS -->|"submission queue, moderation tools"| Editor
    CMS -->|"site config, reports, moderation"| Admin

    CMS -->|"transactional & digest emails"| EmailSvc
    CMS -->|"comment text for scoring"| SpamSvc
    SpamSvc -->|"spam score"| CMS
    CMS -->|"upload/retrieve media"| MediaStore
    CMS -->|"index post content"| SearchIdx
    SearchIdx -->|"search results"| CMS
```

---

## Level 1: Content Publishing DFD

```mermaid
graph TB
    Author((Author))
    Editor((Editor))
    Reader((Reader))
    Subscriber((Subscriber))
    EmailSvc((Email Provider))

    P1[1.0 Content Authoring]
    P2[2.0 Editorial Workflow]
    P3[3.0 Publishing & Distribution]
    P4[4.0 Feed & Sitemap Generation]
    P5[5.0 Notification Dispatch]

    DS1[(Posts / Pages Store)]
    DS2[(Revisions Store)]
    DS3[(Taxonomy Store)]
    DS4[(Media Library)]
    DS5[(Subscription Store)]

    Author -->|"write post content"| P1
    P1 -->|"save draft"| DS1
    P1 -->|"save revision snapshot"| DS2
    P1 -->|"resolve taxonomy"| DS3
    P1 -->|"upload media"| DS4
    DS4 -->|"media URLs"| P1
    P1 -->|"submit for review"| P2

    P2 -->|"fetch draft"| DS1
    P2 -.->|"review decisions"| Editor
    Editor -->|"approve / return / schedule"| P2
    P2 -->|"update post status"| DS1
    P2 -->|"trigger publish"| P3

    P3 -->|"mark as published"| DS1
    P3 -->|"trigger feed update"| P4
    P3 -->|"trigger notifications"| P5

    P4 -->|"fetch recent posts"| DS1
    P4 -->|"render RSS/Atom"| Reader
    P4 -->|"render sitemap.xml"| Reader

    P5 -->|"fetch subscribers"| DS5
    P5 -->|"dispatch digest"| EmailSvc
    EmailSvc -->|"email delivered"| Subscriber
```

---

## Level 1: Layout & Widget DFD

```mermaid
graph TB
    Admin((Admin))
    Visitor((Site Visitor))

    P1[1.0 Theme Management]
    P2[2.0 Widget Configuration]
    P3[3.0 Layout Rendering]
    P4[4.0 Cache Management]

    DS1[(Theme Store)]
    DS2[(Widget Registry)]
    DS3[(Widget Placement Store)]
    DS4[(Page / Post Store)]
    DS5[(CDN Cache)]

    Admin -->|"install / activate theme"| P1
    P1 -->|"store theme metadata & zones"| DS1
    P1 -->|"trigger zone migration"| P2

    Admin -->|"place / configure widget"| P2
    P2 -->|"read available widgets"| DS2
    P2 -->|"read theme zones"| DS1
    P2 -->|"save widget placement & config"| DS3
    P2 -->|"trigger cache invalidation"| P4

    Visitor -->|"request page"| P3
    P3 -->|"fetch post / page content"| DS4
    P3 -->|"fetch widget placements for zones"| DS3
    P3 -->|"fetch widget configs"| DS3
    P3 -->|"resolve widget data"| DS2
    P3 -->|"render HTML response"| Visitor
    P3 -->|"cache rendered output"| DS5

    P4 -->|"invalidate stale entries"| DS5
```

---

## Level 1: Comment Moderation DFD

```mermaid
graph TB
    Reader((Reader))
    Moderator((Editor / Admin))
    SpamSvc((Spam Filter))
    Author((Post Author))
    EmailSvc((Email Provider))

    P1[1.0 Comment Submission]
    P2[2.0 Spam Detection]
    P3[3.0 Moderation Queue]
    P4[4.0 Notification Dispatch]

    DS1[(Comment Store)]
    DS2[(Spam List Store)]
    DS3[(User Store)]

    Reader -->|"submit comment text"| P1
    P1 -->|"submit for scoring"| P2
    P2 -->|"check spam score"| SpamSvc
    SpamSvc -->|"score result"| P2
    P2 -->|"high score: discard"| DS2
    P2 -->|"medium score: queue"| DS1
    P2 -->|"low score: auto-approve"| DS1

    DS1 -->|"pending comments"| P3
    P3 -.->|"review comment"| Moderator
    Moderator -->|"approve / reject / spam"| P3
    P3 -->|"update comment status"| DS1
    P3 -->|"add to spam list"| DS2
    P3 -->|"trigger notification"| P4

    P4 -->|"fetch author email"| DS3
    P4 -->|"send comment notification"| EmailSvc
    EmailSvc -->|"email delivered"| Author
```
