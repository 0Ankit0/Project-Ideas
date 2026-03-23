# Activity Diagram - Library Management System

## Borrow-to-Return Lifecycle

```mermaid
flowchart TD
    start([Patron needs item]) --> search[Search catalog]
    search --> available{Item available?}
    available -- Yes --> checkout[Issue item to patron]
    available -- No --> hold[Place hold / join waitlist]
    hold --> wait[Wait for return or transfer]
    wait --> notify[Notify patron when ready]
    notify --> pickup[Patron collects item]
    pickup --> checkout
    checkout --> due[Loan active until due date]
    due --> renewable{Renewal allowed?}
    renewable -- Yes --> renew[Renew loan]
    renew --> due
    renewable -- No --> return[Return item]
    due --> overdue{Overdue?}
    overdue -- Yes --> fine[Assess overdue fine or block]
    fine --> return
    overdue -- No --> return
    return --> nextHold{Pending hold queue?}
    nextHold -- Yes --> holdShelf[Move to hold shelf or transfer branch]
    nextHold -- No --> shelf[Reshelve item]
    holdShelf --> end([Availability updated])
    shelf --> end
```
