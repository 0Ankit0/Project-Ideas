# C4 Context and Container Diagrams - Library Management System

## C4 Context

```mermaid
flowchart LR
    patrons[Patrons]
    staff[Library Staff]
    vendors[Vendors and Suppliers]
    payment[Payment Provider]
    digital[Digital Content Provider]
    notify[Notification Services]

    system[Library Management System]

    patrons --> system
    staff --> system
    system --> vendors
    system --> payment
    system --> digital
    system --> notify
```

## C4 Container

```mermaid
flowchart TB
    subgraph users[Users]
        patronWeb[Patron Portal Web App]
        staffWeb[Staff Workspace Web App]
    end

    subgraph app[Application Containers]
        api[REST API]
        workers[Background Workers]
        projector[Search and Reporting Projector]
    end

    subgraph stores[Data Stores]
        db[(PostgreSQL)]
        idx[(Search Index)]
        queue[(Message Bus)]
        blob[(Object Storage)]
    end

    patronWeb --> api
    staffWeb --> api
    api --> db
    api --> blob
    api --> queue
    workers --> db
    workers --> queue
    projector --> db
    projector --> idx
    queue --> workers
    queue --> projector
```
