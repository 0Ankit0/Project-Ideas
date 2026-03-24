# Swimlane Diagrams

## Overview
Swimlane (BPMN-style) diagrams show cross-role workflows and responsibilities within the CMS platform.

---

## 1. End-to-End Post Publishing Workflow

```mermaid
sequenceDiagram
    box Author
        participant A as Author
    end
    box Editor
        participant E as Editor
    end
    box System
        participant S as CMS System
    end
    box Readers & Subscribers
        participant R as Reader / Subscriber
    end

    A->>S: Create new post (Draft)
    S-->>A: Editor opens, auto-save enabled
    A->>S: Write content, upload media, assign taxonomy
    A->>S: Submit for Review
    S->>S: Transition post → Pending Review
    S-->>E: Notify: new submission pending

    E->>S: Open submission queue
    S-->>E: Display pending posts
    E->>S: Preview post
    S-->>E: Render in active theme

    alt Editor approves
        E->>S: Click Publish
        S->>S: Transition post → Published
        S-->>A: Notify: post published
        S->>S: Update RSS/Atom feed
        S->>S: Rebuild sitemap.xml
        S-->>R: Dispatch newsletter digest
    else Editor returns to draft
        E->>S: Return to Draft with feedback
        S->>S: Transition post → Draft
        S-->>A: Notify: feedback provided
        A->>S: Revise and re-submit
    else Editor schedules
        E->>S: Set scheduled datetime
        S->>S: Transition post → Scheduled
        S-->>A: Notify: post scheduled
        S->>S: Wait for scheduled time
        S->>S: Auto-publish at scheduled time
        S-->>R: Dispatch newsletter digest
    end
```

---

## 2. Comment Submission and Moderation

```mermaid
sequenceDiagram
    box Reader
        participant R as Reader
    end
    box System
        participant S as CMS System
        participant SP as Spam Filter
    end
    box Moderator
        participant M as Editor / Admin
    end
    box Author
        participant A as Post Author
    end

    R->>S: Submit comment on post
    S->>SP: Check comment for spam
    SP-->>S: Return spam score

    alt High spam score
        S->>S: Discard comment silently
    else Low score + trusted reader
        S->>S: Auto-approve comment
        S-->>A: Notify: new comment on your post
        S-->>R: Notify: reply received (if applicable)
    else Medium score or new reader
        S->>S: Queue for moderation
        S-->>M: Notify: comment awaiting moderation

        M->>S: Open moderation queue
        S-->>M: Display pending comments

        alt Approve
            M->>S: Approve comment
            S->>S: Comment published
            S-->>A: Notify: new approved comment
        else Reject
            M->>S: Reject comment
            S->>S: Comment deleted
        else Mark as Spam
            M->>S: Mark as spam
            S->>S: Add to spam list
        end
    end
```

---

## 3. Theme Activation with Widget Migration

```mermaid
sequenceDiagram
    box Admin
        participant ADM as Admin
    end
    box System
        participant S as CMS System
        participant CDN as CDN
    end

    ADM->>S: Install new theme
    S-->>ADM: Theme installed (inactive)
    ADM->>S: Request live preview
    S-->>ADM: Preview rendered in isolated session

    ADM->>S: Confirm activation
    S->>S: Compare new theme zones vs. existing widget placements
    S-->>ADM: Show unmapped widget zones (if any)

    ADM->>S: Map old zones to new zones
    S->>S: Migrate widget instances to new zones
    S->>S: Activate theme
    S->>CDN: Invalidate site-wide cache
    CDN-->>S: Cache cleared
    S-->>ADM: Activation confirmed
```

---

## 4. Plugin Installation and Hook Registration

```mermaid
sequenceDiagram
    box Admin
        participant ADM as Admin
    end
    box System
        participant S as CMS System
    end
    box Plugin
        participant P as Plugin Package
    end

    ADM->>S: Upload or select plugin from marketplace
    S->>P: Download and extract plugin
    S->>P: Validate API version and hook compatibility
    P-->>S: Compatibility report

    alt Compatible
        S-->>ADM: Show Activate button
        ADM->>S: Click Activate
        S->>P: Call plugin.install() hook
        P->>S: Register widget types
        P->>S: Register admin menu items
        P->>S: Register API route extensions
        S-->>ADM: Plugin active, settings page available
    else Incompatible
        S-->>ADM: Show warning with details
        ADM->>S: Proceed anyway (or cancel)
    end
```

---

## 5. Subscriber Newsletter Dispatch

```mermaid
sequenceDiagram
    box System
        participant S as CMS System
        participant Q as Notification Queue
        participant EM as Email Provider
    end
    box Subscriber
        participant SUB as Subscriber
    end

    S->>S: Post published (or scheduled time reached)
    S->>Q: Enqueue newsletter dispatch job

    Q->>S: Process job: fetch subscriber list
    S-->>Q: Return confirmed subscriber emails

    loop For each subscriber batch
        Q->>EM: Send digest email (post title, excerpt, link)
        EM-->>Q: Delivery status (delivered / bounced)
        Q->>S: Store delivery event (or unsubscribe on hard bounce)
    end

    S-->>SUB: Newsletter email received
    SUB->>S: Click unsubscribe link (optional)
    S->>S: Remove subscription, confirm page shown
```

---

## 6. Media Upload and Processing

```mermaid
sequenceDiagram
    box Author / Editor
        participant U as Author / Editor
    end
    box System
        participant S as CMS System
        participant MS as Media Storage
    end

    U->>S: Upload image file
    S->>S: Validate file type and size
    S->>MS: Store original file
    MS-->>S: Return storage URL

    S->>S: Generate thumbnail (150×150)
    S->>S: Generate medium size (640×480)
    S->>S: Generate large size (1280×960)
    S->>MS: Store all image size variants
    S->>S: Create media library record with all variant URLs
    S-->>U: Upload complete, media available in library

    U->>S: Insert image into post editor
    S-->>U: Embed responsive image HTML with srcset
```
