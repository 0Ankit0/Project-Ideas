# BPMN Swimlane Diagrams — Job Board and Recruitment Platform

## Overview

Swimlane (pool-and-lane) diagrams extend activity diagrams by making the responsible party for each task explicit. Each horizontal lane represents a distinct actor or system; tasks in a lane belong exclusively to that actor. Handoffs between lanes represent process boundary crossings — precisely the points where failures, delays, and miscommunications most commonly occur in hiring workflows.

This document models four cross-functional processes using flowchart-based BPMN swimlane notation:

- **Job Posting Approval and Publication Process** — from requisition draft to live posting across job boards
- **Candidate Application Review Process** — from application receipt to pipeline advancement or rejection
- **Interview Coordination and Feedback Process** — from interview scheduling to scorecard consolidation
- **Offer Management and HRIS Handoff Process** — from offer preparation to new-hire record creation

For each process, lanes represent: **Job Seeker / Candidate**, **Recruiter**, **Hiring Manager**, **HR Admin**, **Platform (System)**, and **Email / Notification System**. External third-party systems appear as collapsed pools where relevant.

---

## Job Posting Approval and Publication Process

This process begins when a recruiter creates a new job requisition draft and ends when the posting is live on the internal job board and all external job boards. It crosses four internal actors and two external systems (job board APIs and the email provider).

```mermaid
flowchart TB
    subgraph Recruiter["🧑‍💼 Recruiter"]
        R1([Start:\nNew Requisition])
        R2[Fill requisition form:\ntitle · dept · location\nsalary · description]
        R3[Configure pipeline\ntemplate and\nscreening questions]
        R4[Select external\njob boards]
        R5[Submit for approval]
        R6[Receive rejection\ncomments]
        R7[Revise and\nresubmit]
        R8[Monitor syndication\nstatus dashboard]
        R9[Manually retry\nfailed syndicates]
    end

    subgraph HiringManager["👤 Hiring Manager"]
        HM1[Receive approval\nnotification]
        HM2{Review\nrequisition}
        HM3[Approve]
        HM4[Reject with\nrequired changes]
    end

    subgraph HRAdmin["🏛️ HR Admin"]
        HR1[Receive approval\nnotification]
        HR2{Review for\ncompliance:\nEEO · salary band\njob title taxonomy}
        HR3[Approve]
        HR4[Reject with\ncompliance notes]
    end

    subgraph Platform["🖥️ Platform System"]
        P1[Create job draft\nin DRAFT status]
        P2[Auto-save draft\nevery 30 seconds]
        P3[Transition status:\nDRAFT → PENDING_APPROVAL]
        P4[Route to HM if\napproval chain configured]
        P5[Transition status:\nPENDING_APPROVAL → APPROVED]
        P6[Publish to internal\njob board\nstatus → ACTIVE]
        P7[Dispatch syndication\ntasks to board workers]
        P8[Poll boards every 4h\nto confirm live status]
        P9[Update syndication\nstatus per board:\nPENDING · LIVE · FAILED]
        P10[Set SYNDICATION_FAILED\nstatus on failed boards]
    end

    subgraph Notifications["✉️ Email / Notification System"]
        N1[Send HM approval\nrequest email]
        N2[Send HR Admin approval\nrequest email]
        N3[Send publication\nconfirmation to recruiter and HM]
        N4[Send syndication\nfailure alert to recruiter]
    end

    subgraph JobBoards["🌐 External Job Boards\nLinkedIn · Indeed · Glassdoor · ZipRecruiter"]
        JB1[Receive job post\nvia API]
        JB2{Post accepted?}
        JB3[Return LIVE status]
        JB4[Return error response]
    end

    R1 --> P1
    P1 --> R2
    R2 --> P2
    R2 --> R3
    R3 --> R4
    R4 --> R5
    R5 --> P3

    P3 --> P4
    P4 --> N1
    N1 --> HM1
    HM1 --> HM2
    HM2 -->|Approve| HM3
    HM2 -->|Reject| HM4
    HM4 --> N2b[Send rejection\nto recruiter]
    N2b --> R6
    R6 --> R7
    R7 --> R5

    HM3 --> N2
    N2 --> HR1
    HR1 --> HR2
    HR2 -->|Approve| HR3
    HR2 -->|Reject| HR4
    HR4 --> N2c[Send rejection\nto recruiter]
    N2c --> R6

    HR3 --> P5
    P5 --> P6
    P6 --> N3
    N3 --> R8
    P6 --> P7

    P7 --> JB1
    JB1 --> JB2
    JB2 -->|Success| JB3
    JB3 --> P9
    P9 --> P8
    JB2 -->|Error| JB4
    JB4 --> P10
    P10 --> N4
    N4 --> R8
    R8 --> R9
    R9 --> P7
```

---

## Candidate Application Review Process

This process begins when a new application is received and ends when the candidate is either advanced to the interview stage or formally rejected. It shows how AI scoring, recruiter review, and communication flow through the system lanes.

```mermaid
flowchart TB
    subgraph Candidate["👤 Job Seeker / Candidate"]
        C1([Start: Submit\napplication])
        C2[Receive confirmation\nemail]
        C3[Check status in\ncandidate portal]
        C4[Receive rejection\nemail]
        C5[Receive advancement\nnotification]
        C6[Respond to phone\nscreen request]
    end

    subgraph Recruiter["🧑‍💼 Recruiter"]
        R1[Open application\ninbox]
        R2[Review AI-ranked\ncandidate list]
        R3[Open candidate\nprofile and resume]
        R4{Review decision}
        R5[Set disposition:\nREJECTED]
        R6[Set disposition:\nON_HOLD]
        R7[Set disposition:\nADVANCE to Phone Screen]
        R8[Add private\nrecruiter note]
        R9[Send phone screen\nscheduling request]
    end

    subgraph Platform["🖥️ Platform System"]
        P1[Create application record\nstatus: SUBMITTED]
        P2[Store resume in S3\nQueue parse job]
        P3[Run resume parser:\nskills · experience · education\nextracted]
        P4{Parse\nsucceeded?}
        P5[Compute AI\nsimilarity score\nresume vs job embedding]
        P6[Rank candidate\nin pipeline list]
        P7[Flag PARSE_FAILED\nstatus]
        P8[Queue rejection\nemail to candidate]
        P9[Update application\nstatus to SCREENING]
        P10[Log disposition event\nto audit trail]
        P11[Duplicate\ndetection check]
        P12{Duplicate\nfound?}
        P13[Flag PENDING_DEDUP\nnotify recruiter]
    end

    subgraph Notifications["✉️ Email / Notification System"]
        N1[Send application\nconfirmation to candidate]
        N2[Send in-app notification\nto recruiter: new application]
        N3[Send rejection email\nwith optional feedback]
        N4[Send parse failure\nre-upload request to candidate]
        N5[Send phone screen\nscheduling email to candidate]
    end

    C1 --> P1
    P1 --> P2
    P2 --> N1
    N1 --> C2
    C2 --> C3

    P2 --> P11
    P11 --> P12
    P12 -->|Duplicate detected| P13
    P13 --> R1
    P12 -->|No duplicate| P3

    P3 --> P4
    P4 -->|Parse failed| P7
    P7 --> N4
    N4 --> C1

    P4 -->|Parse succeeded| P5
    P5 --> P6
    P6 --> N2
    N2 --> R1

    R1 --> R2
    R2 --> R3
    R3 --> R4

    R4 -->|Reject| R5
    R5 --> P10
    P10 --> P8
    P8 --> N3
    N3 --> C4

    R4 -->|Hold| R6
    R6 --> P10
    R6 --> R8

    R4 -->|Advance| R7
    R7 --> P9
    P9 --> P10
    R7 --> R8
    R7 --> R9
    R9 --> N5
    N5 --> C5
    C5 --> C6
```

---

## Interview Coordination and Feedback Process

This process begins when a recruiter triggers interview scheduling and ends when all scorecards are submitted and the hiring debrief decision is recorded. It is the most multi-actor process: it involves the candidate, recruiter, hiring manager, multiple interviewers, the platform, calendar APIs, and the video conferencing system.

```mermaid
flowchart TB
    subgraph Candidate["👤 Candidate"]
        C1[Receive scheduling\nrequest email]
        C2[Select availability\nslot via self-select link]
        C3[Receive confirmation\nwith calendar invite]
        C4[Attend interview\nvia Zoom / Teams]
        C5([Candidate flow ends])
    end

    subgraph Recruiter["🧑‍💼 Recruiter"]
        R1([Start:\nTrigger interview\nscheduling])
        R2[Select interviewers\nand interview format]
        R3[Review computed\nslot options]
        R4{Slots\nvalid?}
        R5[Manual override:\nenter slots]
        R6[Confirm scheduling\nrequest sent]
        R7[Review all\nscorecard submissions]
        R8[Facilitate debrief\ndiscussion]
        R9{Hiring\ndecision}
        R10[Advance to\noffer stage]
        R11[Reject candidate\nwith disposition]
        R12[Schedule additional\nround]
    end

    subgraph InterviewerPanel["👥 Interviewer Panel\nHiring Manager + Interviewers"]
        I1[Receive calendar\nevent notification]
        I2[Attend interview]
        I3[Receive scorecard\nassignment notification]
        I4[Complete and submit\nstructured scorecard]
        I5[Receive 24h reminder\nif scorecard pending]
    end

    subgraph Platform["🖥️ Platform System"]
        P1[Fetch free/busy\nfor all interviewers\nvia Calendar API]
        P2{Calendar API\nsuccess?}
        P3[Fall back to\nmanual scheduling form]
        P4[Compute intersection\nof free slots]
        P5{Slots found?}
        P6[Notify recruiter:\nno availability]
        P7[Present top 5 slots\nto candidate]
        P8[Monitor candidate\nresponse – 72h window]
        P9{Response\nreceived?}
        P10[Send 24h reminder]
        P11[Send 48h reminder\nvia SMS if opted in]
        P12[Notify recruiter:\nunresponsive candidate]
        P13[Validate slot\nstill available]
        P14{Slot still\nfree?}
        P15[Remove conflicted\nslot – re-present]
        P16[Generate Zoom /\nTeams meeting link]
        P17[Create calendar events\nfor all parties]
        P18[Send confirmations\nand reminders]
        P19[Assign scorecard\nto each interviewer\npost-interview]
        P20[Aggregate scores\nafter all submitted]
    end

    subgraph CalendarExternal["📅 Google Calendar / Microsoft Graph"]
        CAL1[Return free/busy data]
        CAL2[Create calendar events]
    end

    subgraph VideoExternal["🎥 Zoom / Microsoft Teams"]
        VID1[Generate meeting link]
    end

    subgraph Notifications["✉️ Email / Notification System"]
        N1[Send scheduling request\nto candidate]
        N2[Send 24h reminder\nto candidate]
        N3[Send 48h SMS reminder]
        N4[Send interview confirmation\nto candidate and panel]
        N5[Send scorecard\nassignment to interviewers]
        N6[Send 24h scorecard\nreminder to pending reviewers]
        N7[Send scoring complete\nnotification to recruiter]
    end

    R1 --> R2
    R2 --> P1
    P1 --> CAL1
    CAL1 --> P2
    P2 -->|API error| P3
    P3 --> R3
    P2 -->|Success| P4
    P4 --> P5
    P5 -->|No slots| P6
    P6 --> R3
    R3 --> R4
    R4 -->|No valid slots| R5
    R5 --> N1
    P5 -->|Slots found| P7
    P7 --> N1

    N1 --> C1
    C1 --> P8
    P8 --> P9
    P9 -->|After 24h| P10
    P10 --> N2
    N2 --> C1
    P9 -->|After 48h| P11
    P11 --> N3
    N3 --> C1
    P9 -->|After 72h| P12
    P12 --> R6

    P9 -->|Candidate selects slot| P13
    P13 --> P14
    P14 -->|Conflict| P15
    P15 --> P7
    P14 -->|Free| P16
    P16 --> VID1
    VID1 --> P17
    P17 --> CAL2
    CAL2 --> P18
    P18 --> N4
    N4 --> C3
    N4 --> I1

    C3 --> C4
    I1 --> I2
    C4 --> P19
    I2 --> P19
    P19 --> N5
    N5 --> I3
    I3 --> I4
    I4 --> P20
    I5 --> I4

    P20 --> P9b{All scorecards\nsubmitted?}
    P9b -->|Pending after 24h| N6
    N6 --> I5
    P9b -->|All submitted| N7
    N7 --> R7
    R7 --> R8
    R8 --> R9
    R9 -->|Advance| R10
    R9 -->|Reject| R11
    R9 -->|More rounds| R12
    R12 --> R2
    C4 --> C5
```

---

## Offer Management and HRIS Handoff Process

This process begins when the recruiter initiates offer creation after a hire decision and ends with either the candidate starting at the company (HRIS record created) or the offer being formally declined, expired, or rescinded.

```mermaid
flowchart TB
    subgraph Candidate["👤 Candidate"]
        C1[Receive offer letter\nvia DocuSign email]
        C2[Review offer terms\nin DocuSign portal\nor candidate portal]
        C3{Candidate\ndecision}
        C4[Sign offer letter\nelectronically]
        C5[Decline with\nreason and optional\ncounter-offer]
        C6[Receive background\ncheck consent request]
        C7[Provide consent\nand complete forms]
        C8[Receive welcome email\nwith start date]
    end

    subgraph Recruiter["🧑‍💼 Recruiter"]
        R1([Start:\nHiring decision\nmade])
        R2[Create offer:\nsalary · equity\nstart date · benefits]
        R3[Attach offer\nletter template]
        R4[Review declined\noffer and reason]
        R5{Re-extend or\nwithdraw?}
        R6[Revise offer terms\nfor negotiation]
        R7[Review adverse\nbackground check result]
        R8{Proceed or\nrescind offer?}
        R9[Send formal rescission\nletter with legal notice]
        R10[Activate runner-up\ncandidate]
    end

    subgraph HRAdmin["🏛️ HR Admin"]
        HR1[Receive offer\napproval request]
        HR2{Review offer:\nsalary vs band\ncompliance check}
        HR3[Approve offer]
        HR4[Reject with required\nadjustments]
    end

    subgraph Platform["🖥️ Platform System"]
        P1[Generate offer letter PDF\nusing company template]
        P2[Route for HR Admin\napproval if required]
        P3[Create DocuSign\nenvelope with offer PDF]
        P4[Track offer status:\nSENT · VIEWED · SIGNED · DECLINED]
        P5[Set expiry timer:\n5 business days]
        P6{Timer\nexpired?}
        P7[Mark offer EXPIRED]
        P8[Check runner-up\ncandidate on hold]
        P9[Receive DocuSign\nsigned webhook]
        P10[Store signed PDF\nin S3]
        P11[Update offer status\nto ACCEPTED]
        P12[Initiate Checkr\nbackground check package]
        P13[Receive Checkr\nresult webhook]
        P14{Result\nclassification}
        P15[POST new-hire record\nto Workday / BambooHR]
        P16[Mark application HIRED\nClose job if headcount met]
        P17[Record decline reason\nin audit trail]
        P18[Trigger runner-up\nre-activation flow]
    end

    subgraph DocuSign["✍️ DocuSign eSignature"]
        DS1[Deliver offer envelope\nto candidate email]
        DS2[Candidate signs\nin DocuSign UI]
        DS3[Send signed webhook\ncallback to platform]
    end

    subgraph Checkr["🔍 Checkr Background Check"]
        CHK1[Initiate background\ncheck package]
        CHK2[Return result:\nCLEAR · CONSIDER · ADVERSE]
    end

    subgraph HRIS["🏗️ Workday / BambooHR"]
        H1[Accept new-hire\nPOST request]
        H2[Create employee\nrecord]
        H3[Trigger IT provisioning\nand onboarding]
    end

    subgraph Notifications["✉️ Email / Notification System"]
        N1[Send offer email\nwith DocuSign link]
        N2[Send Day-3 reminder\nto candidate]
        N3[Send expiry notice\nto recruiter]
        N4[Send decline notification\nto recruiter and HM]
        N5[Send background check\nconsent request to candidate]
        N6[Send adverse result\nalert to recruiter]
        N7[Send welcome email\nwith start date to candidate]
        N8[Send rescission notice\nwith legal context]
    end

    R1 --> R2
    R2 --> R3
    R3 --> P1
    P1 --> P2
    P2 --> HR1
    HR1 --> HR2
    HR2 -->|Reject| HR4
    HR4 --> R2
    HR2 -->|Approve| HR3
    HR3 --> P3
    P3 --> DS1
    DS1 --> N1
    N1 --> C1
    C1 --> P4
    P4 --> P5
    P5 --> C2

    P5 --> P6
    P6 -->|Day 3 no action| N2
    N2 --> C2
    P6 -->|Day 5 no action| P7
    P7 --> N3
    N3 --> R4
    P7 --> P8
    P8 -->|Runner-up available| P18
    P18 --> R10

    C2 --> C3
    C3 -->|Decline| C5
    C5 --> P17
    P17 --> N4
    N4 --> R4
    R4 --> R5
    R5 -->|Withdraw| P8
    R5 -->|Re-negotiate| R6
    R6 --> P1

    C3 -->|Sign| C4
    C4 --> DS2
    DS2 --> DS3
    DS3 --> P9
    P9 --> P10
    P10 --> P11
    P11 --> P12
    P12 --> CHK1
    CHK1 --> N5
    N5 --> C6
    C6 --> C7
    C7 --> CHK2
    CHK2 --> P13
    P13 --> P14
    P14 -->|Clear| P15
    P14 -->|Adverse| N6
    N6 --> R7
    R7 --> R8
    R8 -->|Proceed despite adverse| P15
    R8 -->|Rescind| R9
    R9 --> N8
    N8 --> C1
    R9 --> P8

    P15 --> H1
    H1 --> H2
    H2 --> H3
    P15 --> P16
    P16 --> N7
    N7 --> C8
```

---

*Last updated: 2025-01-01 | Owner: Platform Engineering — Process Architecture Team*
