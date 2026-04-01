# BPMN Swimlane Diagram — Real Estate Management System

## Overview

This document presents two BPMN-style swimlane process diagrams for the Real Estate Management System. Each process is decomposed by participant lane to clarify which actor or system is responsible for each step, making handoff points and integration touchpoints explicit. The diagrams use Mermaid flowchart syntax with subgraph blocks to represent swimlanes.

---

## Process 1: Lease Signing Process

This process covers the complete lifecycle of lease execution: from the Property Manager initiating the lease document, through DocuSign orchestration, to final activation in the REMS database. Four lanes participate: Tenant, Property Manager, DocuSign, and the REMS System (automated steps).

```mermaid
flowchart TD
    subgraph PM_LANE["🧑‍💼 Property Manager"]
        PM1[Review approved\ntenant application]
        PM2[Open lease creation\nworkflow in REMS]
        PM3[Select lease template\nfor property type and jurisdiction]
        PM4[Review pre-filled lease terms:\nunit, dates, rent, deposit]
        PM5[Add custom lease clauses:\npet addendum, parking, utilities]
        PM6[Set co-signer requirements\nif applicable]
        PM7[Click 'Send for Signature']
        PM8[Receive notification:\nlease sent to tenant]
        PM9[Monitor signing status\nin REMS dashboard]
        PM10[Receive signed lease\ncompletion notification]
        PM11[Review executed lease PDF\nin REMS document library]
    end

    subgraph SYS_LANE["⚙️ REMS System"]
        SYS1[Generate lease PDF\nfrom template + tenant data]
        SYS2[Upload PDF to DocuSign\nCreate envelope via API]
        SYS3[Configure signing fields:\nsignature, initials, date blocks\nfor each recipient]
        SYS4[Set envelope expiry: 48 hours]
        SYS5[Receive DocuSign webhook\nenvelope.created]
        SYS6[Log: envelope sent to tenant]
        SYS7[Monitor envelope status\nvia webhook subscription]
        SYS8{Envelope status?}
        SYS9[Receive webhook:\nenvelope.completed]
        SYS10[Download signed PDF\nfrom DocuSign via API]
        SYS11[Store PDF as Document record\nlinked to Lease]
        SYS12[Set Lease.status = active]
        SYS13[Set PropertyUnit.status = occupied]
        SYS14[Generate first RentInvoice\nper RentSchedule]
        SYS15[Trigger security deposit\ncollection via Stripe]
        SYS16[Send confirmation emails\nto tenant and PM]
        SYS_REMIND[Send reminder email/SMS\nto tenant at 24h mark]
        SYS_EXPIRE[Expire envelope\nSet Lease.status = void\nNotify PM]
        SYS_DECLINE[Receive webhook:\nenvelope.declined\nSet Lease.status = draft\nNotify PM]
    end

    subgraph DS_LANE["📝 DocuSign"]
        DS1[Receive envelope creation\nrequest from REMS]
        DS2[Host lease document\nwith signing fields]
        DS3[Send signing email\nto tenant with link]
        DS4[Present lease document\nto tenant for review]
        DS5[Capture electronic signature\nwith IP and timestamp audit trail]
        DS6[Send confirmation email\nto tenant with signed copy]
        DS7[Fire webhook:\nenvelope.completed]
        DS8[Fire webhook:\nenvelope.declined]
        DS9[Fire reminder at 24h\nif not signed]
        DS_EXPIRE[Expire envelope at 48h\nfire envelope.voided webhook]
    end

    subgraph TN_LANE["👤 Tenant"]
        TN1[Receive email:\n'Your lease is ready to sign']
        TN2[Click signing link\nin email]
        TN3[Review full lease document\nin DocuSign viewer]
        TN4[Read all clauses\nincluding custom addenda]
        TN5{Decision:\nAccept terms?}
        TN6[Click 'Finish' to sign\nall required fields]
        TN7[Receive signed lease\ncopy via email]
        TN8[Receive REMS notification:\nlease active]
        TN_DECLINE[Click 'Decline to Sign'\nEnter reason]
    end

    %% Flow connections
    PM1 --> PM2 --> PM3 --> PM4 --> PM5 --> PM6 --> PM7
    PM7 --> SYS1
    SYS1 --> SYS2 --> SYS3 --> SYS4
    SYS4 --> DS1
    DS1 --> DS2 --> DS3
    DS3 --> SYS5 --> SYS6
    SYS6 --> PM8
    DS3 --> TN1
    TN1 --> TN2 --> TN3 --> TN4 --> TN5
    TN5 -- Yes --> TN6
    TN5 -- No --> TN_DECLINE
    TN_DECLINE --> DS8
    DS8 --> SYS_DECLINE
    SYS_DECLINE --> PM9
    TN6 --> DS5 --> DS6 --> DS7
    DS7 --> SYS9 --> SYS10 --> SYS11 --> SYS12 --> SYS13 --> SYS14 --> SYS15 --> SYS16
    SYS16 --> TN7
    SYS16 --> TN8
    SYS16 --> PM10 --> PM11
    DS9 --> SYS_REMIND
    SYS_REMIND --> TN1
    DS_EXPIRE --> SYS_EXPIRE
    SYS7 --> SYS8
    SYS8 -- completed --> SYS9
    SYS8 -- declined --> SYS_DECLINE
    SYS8 -- voided --> SYS_EXPIRE
```

---

## Process 2: Maintenance Request Process

This process covers the end-to-end maintenance workflow from tenant submission to closure, with a focus on the handoffs between Tenant, Property Manager, Contractor, and the REMS System. Decision points for priority escalation, contractor assignment, and work approval are explicitly modelled.

```mermaid
flowchart TD
    subgraph TN_LANE2["👤 Tenant"]
        TN2_1[Identify maintenance issue\nin unit]
        TN2_2[Log into tenant portal]
        TN2_3[Navigate to\n'New Maintenance Request']
        TN2_4[Select issue category\ne.g. plumbing, electrical, HVAC]
        TN2_5[Enter description\nand upload photos\nup to 5 images]
        TN2_6[Set priority:\nroutine / urgent / emergency]
        TN2_7[Submit request]
        TN2_8[Receive confirmation:\nrequest submitted, reference number]
        TN2_9[Receive notification:\ncontractor assigned, scheduled date]
        TN2_10[Provide property access\nfor contractor visit]
        TN2_11[Receive closure notification]
        TN2_12[Optionally submit\nsatisfaction rating 1–5]
    end

    subgraph PM_LANE2["🧑‍💼 Property Manager"]
        PM2_1[Receive new request\nnotification]
        PM2_2[Review request details:\ndescription, photos, priority]
        PM2_3{Assess scope}
        PM2_4[Minor repair:\nAssign to on-call contractor]
        PM2_5[Major repair:\nRequest cost estimate first]
        PM2_6[Select contractor\nfrom Contractor registry]
        PM2_7[Set estimated completion date]
        PM2_8[Create MaintenanceAssignment\nin REMS]
        PM2_9[Monitor assignment status\nvia PM dashboard]
        PM2_10{Contractor\ndeclines?}
        PM2_11[Reassign to\nalternate contractor]
        PM2_12[Review completion report\nand photos]
        PM2_13{Approve\ncompletion?}
        PM2_14[Request rework\nwith notes]
        PM2_15[Approve and close request\nRecord cost in expense ledger]
        PM2_16[Mark expense billable\nto owner if applicable]
    end

    subgraph CT_LANE["🔧 Contractor"]
        CT2_1[Receive work order\nvia email + SMS]
        CT2_2[Review work order:\nunit address, issue, photos\naccess instructions]
        CT2_3{Accept work order?}
        CT2_4[Confirm acceptance\nin REMS mobile app]
        CT2_5[Decline with reason\nin REMS mobile app]
        CT2_6[Travel to property\non scheduled date]
        CT2_7[Assess issue on-site\nupdate status: in_progress]
        CT2_8[Perform repair or\nschedule follow-up visit]
        CT2_9[Upload before/after photos\nvia REMS mobile app]
        CT2_10[Log materials used\nand labor hours]
        CT2_11[Mark job complete\nin REMS mobile app\nAdd completion notes]
    end

    subgraph SYS_LANE2["⚙️ REMS System"]
        SYS2_1[Create MaintenanceRequest record\nstatus = submitted\nLink to Lease and Unit]
        SYS2_2{Priority = emergency?}
        SYS2_3[Immediately send\nSMS alert to PM\nand on-call contractor]
        SYS2_4[Add to standard\nPM notification queue]
        SYS2_5[Create MaintenanceAssignment\nstatus = pending_acceptance]
        SYS2_6[Send work order\nnotification to contractor]
        SYS2_7[Start 24h acceptance\ntimer]
        SYS2_8{24h no response?}
        SYS2_9[Auto-escalate to PM\nfor manual follow-up]
        SYS2_10[Update assignment status:\naccepted]
        SYS2_11[Notify tenant:\ncontractor assigned + date]
        SYS2_12[Update assignment status:\nin_progress]
        SYS2_13[Update assignment status:\ncompleted]
        SYS2_14[Notify PM:\nwork completed, review required]
        SYS2_15[Set MaintenanceRequest.status\n= closed\nRecord final cost]
        SYS2_16[Update property expense ledger]
        SYS2_17[Send tenant closure\nnotification + rating prompt]
        SYS2_18[Store satisfaction rating\nUpdate contractor score]
    end

    %% Tenant to System
    TN2_1 --> TN2_2 --> TN2_3 --> TN2_4 --> TN2_5 --> TN2_6 --> TN2_7
    TN2_7 --> SYS2_1
    SYS2_1 --> TN2_8
    SYS2_1 --> SYS2_2
    SYS2_2 -- Yes --> SYS2_3
    SYS2_2 -- No --> SYS2_4
    SYS2_3 --> PM2_1
    SYS2_4 --> PM2_1

    %% PM assessment and assignment
    PM2_1 --> PM2_2 --> PM2_3
    PM2_3 -- Minor --> PM2_4
    PM2_3 -- Major --> PM2_5
    PM2_5 --> PM2_6
    PM2_4 --> PM2_6
    PM2_6 --> PM2_7 --> PM2_8
    PM2_8 --> SYS2_5 --> SYS2_6
    SYS2_6 --> CT2_1

    %% Contractor acceptance
    CT2_1 --> CT2_2 --> CT2_3
    CT2_3 -- Yes --> CT2_4
    CT2_3 -- No --> CT2_5
    CT2_4 --> SYS2_10
    CT2_5 --> SYS2_9
    SYS2_9 --> PM2_10
    PM2_10 -- Yes --> PM2_11
    PM2_11 --> PM2_6
    SYS2_6 --> SYS2_7 --> SYS2_8
    SYS2_8 -- Yes --> SYS2_9
    SYS2_10 --> SYS2_11
    SYS2_11 --> TN2_9
    PM2_9 --> PM2_10

    %% Field work
    TN2_9 --> TN2_10
    CT2_4 --> CT2_6 --> CT2_7 --> SYS2_12
    CT2_7 --> CT2_8 --> CT2_9 --> CT2_10 --> CT2_11
    CT2_11 --> SYS2_13 --> SYS2_14

    %% PM completion review
    SYS2_14 --> PM2_12 --> PM2_13
    PM2_13 -- No --> PM2_14
    PM2_14 --> CT2_7
    PM2_13 -- Yes --> PM2_15 --> PM2_16
    PM2_15 --> SYS2_15 --> SYS2_16 --> SYS2_17
    SYS2_17 --> TN2_11 --> TN2_12
    TN2_12 --> SYS2_18
```
