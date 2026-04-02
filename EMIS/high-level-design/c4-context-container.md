# EMIS - C4 Model Diagrams

## Overview

The C4 model provides a hierarchical set of architecture diagrams for EMIS, showing the system at different levels of abstraction: Context, Containers, Components, and Code.

## Level 1: System Context Diagram

Shows how EMIS fits into the wider ecosystem and its interactions with users and external systems.

```mermaid
graph TB
    Student["Student<br/>[Person]<br/><br/>Enrolled learner accessing<br/>academic services"]
    Faculty["Faculty<br/>[Person]<br/><br/>Teaching staff managing<br/>courses and students"]
    Admin["Administrator<br/>[Person]<br/><br/>System administrator<br/>managing operations"]
    Parent["Parent/Guardian<br/>[Person]<br/><br/>Monitors student progress<br/>and pays fees"]
    
    EMIS["EMIS<br/>[Software System]<br/><br/>Education Management Information System<br/>Manages all aspects of educational institution"]
    
    PaymentGW["Payment Gateway<br/>[External System]<br/><br/>Processes online payments<br/>(Stripe, Razorpay, PayPal)"]
    EmailSystem["Email Service<br/>[External System]<br/><br/>Sends notifications<br/>via SMTP"]
   SMSSystems["SMS Gateway<br/>[External System]<br/><br/>Sends text messages"]
    
    Student -->|"Registers courses,<br/>submits assignments,<br/>views grades,<br/>pays fees"| EMIS
    Faculty -->|"Uploads content,<br/>marks attendance,<br/>enters grades"| EMIS
    Admin -->|"Manages users,<br/>configures system,<br/>generates reports"| EMIS
    Parent -->|"Views progress,<br/>pays fees"| EMIS
    
    EMIS -->|"Sends learning materials,<br/>grades, notifications"| Student
    EMIS -->|"Provides schedules,<br/>student rosters"| Faculty
    EMIS -->|"Delivers reports,<br/>analytics"| Admin
    EMIS -->|"Sends progress reports,<br/>fee statements"| Parent
    
    EMIS -->|"Initiates payment<br/>[HTTPS/JSON]"| PaymentGW
    PaymentGW -->|"Returns confirmation<br/>[HTTPS/JSON]"| EMIS
    
    EMIS -->|"Sends emails<br/>[SMTP]"| EmailSystem
    EMIS -->|"Sends SMS<br/>[HTTP API]"| SMSSystem
    
    style EMIS fill:#2C3E50,color:#fff,stroke:#34495E,stroke-width:4px
    style Student fill:#4A90E2,color:#fff
    style Faculty fill:#7B68EE,color:#fff
    style Admin fill:#E74C3C,color:#fff
    style Parent fill:#F39C12,color:#fff
    style PaymentGW fill:#95A5A6,stroke:#7F8C8D,stroke-width:2px
    style EmailSystem fill:#95A5A6,stroke:#7F8C8D,stroke-width:2px
    style SMSSystem fill:#95A5A6,stroke:#7F8C8D,stroke-width:2px
```

## Level 2: Container Diagram

Shows the high-level technology choices and how containers communicate.

```mermaid
graph TB
    User["System User<br/>[Person]"]
    
    subgraph EMIS_Boundary["EMIS System"]
        WebApp["Web Application<br/>[Container: Django + HTMX]<br/><br/>Delivers HTML pages,<br/>handles user interactions,<br/>server-side rendering"]
        
        API["REST API<br/>[Container: Django REST Framework]<br/><br/>Provides JSON/HTTP API<br/>for mobile and integrations,<br/>JWT authentication"]
        
        AsyncWorker["Background Worker<br/>[Container: Celery]<br/><br/>Processes async tasks:<br/>emails, reports,<br/>scheduled jobs"]
        
        Database["Database<br/>[Container: PostgreSQL]<br/><br/>Stores user data,<br/>academic records,<br/>transactions"]
        
        Cache["Cache<br/>[Container: Redis]<br/><br/>Session storage,<br/>application caching,<br/>task queue broker"]
        
        FileStorage["File Storage<br/>[Container: Local FS / S3]<br/><br/>Uploaded documents,<br/>course materials,<br/>generated reports"]
        
        StaticServer["Static Files<br/>[Container: WhiteNoise/CDN]<br/><br/>CSS, JavaScript,<br/>images, fonts"]
    end
    
    EmailSvc["Email Service<br/>[External: SMTP]"]
    PaymentSvc["Payment Gateway<br/>[External: API]"]
    SMSSvc["SMS Gateway<br/>[External: API]"]
    
    User -->|"HTTPS"| WebApp
    User -->|"HTTPS/JSON"| API
    
    WebApp -->|"Reads/Writes<br/>[SQLAlchemy/Django ORM]"| Database
    API -->|"Reads/Writes<br/>[Django ORM]"| Database
    
    WebApp -->|"Get/Set cache<br/>[Redis Client]"| Cache
    API -->|"Get/Set cache<br/>[Redis Client]"| Cache
    
    WebApp -->|"Enqueue task<br/>[Celery]"| AsyncWorker
    API -->|"Enqueue task<br/>[Celery]"| AsyncWorker
    AsyncWorker -->|"Uses broker<br/>[Redis]"| Cache
    AsyncWorker -->|"Reads/Writes<br/>[Django ORM]"| Database
    
    WebApp -->|"Upload/Download<br/>[File API]"| FileStorage
    API -->|"Upload/Download<br/>[File API]"| FileStorage
    AsyncWorker -->|"Write files<br/>[File API]"| FileStorage
    
    WebApp -->|"Serves<br/>[HTTP]"| StaticServer
    
    AsyncWorker -->|"SMTP"| EmailSvc
    WebApp -->|"HTTPS/JSON"| PaymentSvc
    AsyncWorker -->|"HTTP API"| SMSSvc
    
    style WebApp fill:#2C3E50,color:#fff
    style API fill:#2C3E50,color:#fff
    style AsyncWorker fill:#27AE60,color:#fff
    style Database fill:#E67E22,color:#fff
    style Cache fill:#E74C3C,color:#fff
    style FileStorage fill:#F39C12,color:#fff
    style StaticServer fill:#9B59B6,color:#fff
    style EmailSvc fill:#95A5A6
    style PaymentSvc fill:#95A5A6
    style SMSSvc fill:#95A5A6
```

## Level 3: Component Diagram - Web Application

Shows the major components within the Web Application container.

```mermaid
graph TB
    Browser["Web Browser"]
    
    subgraph WebApp_Container["Web Application Container"]
        direction TB
        
        subgraph Presentation["Presentation Components"]
            Templates["Django Templates<br/>[Component]<br/><br/>HTML rendering with<br/>template inheritance"]
            HTMX["HTMX Components<br/>[Component]<br/><br/>Dynamic page updates<br/>without full reload"]
            Forms["Django Forms<br/>[Component]<br/><br/>Form rendering and<br/>validation"]
        end
        
        subgraph Routing["Routing & Views"]
            URLRouter["URL Router<br/>[Component]<br/><br/>Maps URLs to views"]
            Views["View Functions<br/>[Component]<br/><br/>Request handlers,<br/>business logic"]
            ClassViews["Class-Based Views<br/>[Component]<br/><br/>CRUD operations,<br/>generic views"]
        end
        
        subgraph Middleware_Layer["Middleware"]
            AuthMiddleware["Auth Middleware<br/>[Component]<br/><br/>Session & JWT<br/>authentication"]
            SecurityMiddleware["Security Middleware<br/>[Component]<br/><br/>CSRF, XSS protection,<br/>security headers"]
            RateLimitMiddleware["Rate Limit Middleware<br/>[Component]<br/><br/>API throttling,<br/>DDoS protection"]
        end
        
        subgraph Business_Logic["Business Logic"]
            Models["Django Models<br/>[Component]<br/><br/>ORM models,<br/>business entities"]
            Managers["Model Managers<br/>[Component]<br/><br/>Custom query logic"]
            Services["Service Layer<br/>[Component]<br/><br/>Complex business<br/>operations"]
        end
        
        subgraph Module_Apps["Django Apps (25 modules)"]
            CoreApp["Core App<br/>[Component]"]
            UserMgmt["User Management<br/>[Component]"]
            Students["Students App<br/>[Component]"]
            Courses["Courses App<br/>[Component]"]
            Finance["Finance App<br/>[Component]"]
            LMS["LMS App<br/>[Component]"]
            Others["... 19 more apps"]
        end
    end
    
    Database[(PostgreSQL)]
    Cache[(Redis)]
    
    Browser -->|HTTP Request| URLRouter
    URLRouter -->|Route| AuthMiddleware
    AuthMiddleware --> SecurityMiddleware
    SecurityMiddleware --> RateLimitMiddleware
    RateLimitMiddleware --> Views
    RateLimitMiddleware --> ClassViews
    
    Views --> Services
    ClassViews --> Services
    Services --> Models
    Models --> Managers
    
    Views --> Templates
    ClassViews --> Templates
    Templates --> HTMX
    Templates --> Forms
    
    CoreApp --> Models
    UserMgmt --> Models
    Students --> Models
    Courses --> Models
    Finance --> Models
    LMS --> Models
    
    Models --> Database
    Managers --> Database
    Services --> Cache
    
    Templates -->|HTML| Browser
    
    style URLRouter fill:#3498DB,color:#fff
    style Views fill:#9B59B6,color:#fff
    style ClassViews fill:#9B59B6,color:#fff
    style AuthMiddleware fill:#E74C3C,color:#fff
    style SecurityMiddleware fill:#E74C3C,color:#fff
    style RateLimitMiddleware fill:#E74C3C,color:#fff
    style Models fill:#F39C12,color:#fff
    style Services fill:#27AE60,color:#fff
    style CoreApp fill:#1ABC9C,color:#fff
    style UserMgmt fill:#1ABC9C,color:#fff
    style Students fill:#1ABC9C,color:#fff
```

## Level 3: Component Diagram - REST API

Shows components within the REST API container.

```mermaid
graph TB
    Client["API Client<br/>(Mobile/External)"]
    
    subgraph API_Container["REST API Container"]
        direction TB
        
        subgraph API_Layer["API Layer"]
            APIRouter["API Router<br/>[Component]<br/><br/>URL routing for<br/>API endpoints"]
            ViewSets["DRF ViewSets<br/>[Component]<br/><br/>CRUD API views"]
            APIViews["API Views<br/>[Component]<br/><br/>Custom endpoints"]
        end
        
        subgraph Serialization["Serialization"]
            Serializers["Serializers<br/>[Component]<br/><br/>JSON serialization,<br/>validation"]
            Pagination["Pagination<br/>[Component]<br/><br/>Paginated responses"]
            Filtering["Filters<br/>[Component]<br/><br/>Query filtering,<br/>search, ordering"]
        end
        
        subgraph API_Auth["Authentication & Authorization"]
            JWTAuth["JWT Authentication<br/>[Component]<br/><br/>Token validation"]
            Permissions["Permission Classes<br/>[Component]<br/><br/>RBAC enforcement"]
            Throttling["Throttling<br/>[Component]<br/><br/>Rate limiting"]
        end
        
        subgraph Business["Business Logic"]
            APIModels["Models<br/>[Component]<br/><br/>Shared with Web App"]
            APIServices["Services<br/>[Component]<br/><br/>Business operations"]
        end
        
        subgraph Documentation["Documentation"]
            OpenAPI["OpenAPI Schema<br/>[Component]<br/><br/>API specification"]
            SwaggerUI["Swagger UI<br/>[Component]<br/><br/>Interactive docs"]
        end
    end
    
    Database[(PostgreSQL)]
    Cache[(Redis)]
    
    Client -->|"HTTP + JWT"| APIRouter
    APIRouter --> JWTAuth
    JWTAuth --> Permissions
    Permissions --> Throttling
    Throttling --> ViewSets
    Throttling --> APIViews
    
    ViewSets --> Serializers
    APIViews --> Serializers
    Serializers --> Filtering
    Serializers --> Pagination
    
    ViewSets --> APIServices
    APIViews --> APIServices
    APIServices --> APIModels
    
    APIModels --> Database
    APIServices --> Cache
    
    ViewSets -->|"JSON"| Client
    APIViews -->|"JSON"| Client
    
    APIRouter --> OpenAPI
    OpenAPI --> SwaggerUI
    SwaggerUI -->|"HTML"| Client
    
    style APIRouter fill:#3498DB,color:#fff
    style ViewSets fill:#9B59B6,color:#fff
    style Serializers fill:#F39C12,color:#fff
    style JWTAuth fill:#E74C3C,color:#fff
    style Permissions fill:#E74C3C,color:#fff
    style APIModels fill:#27AE60,color:#fff
    style OpenAPI fill:#16A085,color:#fff
```

## Level 4: Code Diagram - Student Model (Example)

Shows classes and their relationships for a specific component.

```mermaid
classDiagram
    class BaseModel {
        <<abstract>>
        +UUID id
        +DateTime created_at
        +DateTime updated_at
        +Boolean is_active
        +save()
        +delete()
    }
    
    class User {
        +String username
        +String email
        +String password_hash
        +String role
        +get_full_name()
        +check_password()
        +set_password()
    }
    
    class Student {
        +String student_id
        +ForeignKey user
        +ForeignKey program
        +String batch
        +String section
        +String status
        +Date date_of_birth
        +update_current_enrollment()
        +graduate()
        +withdraw()
        +is_currently_enrolled()
    }
    
    class Program {
        +String code
        +String name
        +String degree_type
        +Integer duration_semesters
        +get_total_credits()
    }
    
    class SemesterEnrollment {
        +ForeignKey student
        +ForeignKey academic_semester
        +Boolean is_active
        +Decimal gpa
        +Integer credits_enrolled
        +complete_semester()
        +withdraw()
        +calculate_gpa()
    }
    
    class CourseEnrollment {
        +ForeignKey semester_enrollment
        +ForeignKey course_section
        +String status
        +String letter_grade
        +Decimal grade_points
        +get_numeric_grade()
    }
    
    class StudentManager {
        <<Manager>>
        +get_active_students()
        +get_by_student_id()
        +get_by_program()
        +get_graduated_students()
    }
    
    class StudentSerializer {
        <<Serializer>>
        +serialize()
        +deserialize()
        +validate()
        +to_representation()
    }
    
    class StudentViewSet {
        <<ViewSet>>
        +list()
        +retrieve()
        +create()
        +update()
        +destroy()
        +enroll()
        +graduate()
    }
    
    BaseModel <|-- Student
    User "1" -- "1" Student : extends
    Program "1" -- "*" Student : enrolled_in
    Student "1" -- "*" SemesterEnrollment : has
    SemesterEnrollment "1" -- "*" CourseEnrollment : contains
    
    Student ..> StudentManager : uses
    StudentViewSet ..> Student : manages
    StudentViewSet ..> StudentSerializer : uses
    StudentSerializer ..> Student : serializes
```

## Deployment View

Shows how the system is deployed in production.

```mermaid
graph TB
    subgraph Internet["Internet"]
        Users[Users]
    end
    
    subgraph DMZ["DMZ / Cloud"]
        LB["Load Balancer<br/>[Nginx/ALB]"]
        CDN["CDN<br/>[CloudFront]"]
    end
    
    subgraph App_Tier["Application Tier"]
        Web1["Web Server 1<br/>[Gunicorn + Django]"]
        Web2["Web Server 2<br/>[Gunicorn + Django]"]
        Web3["Web Server N<br/>[Gunicorn + Django]"]
        
        Worker1["Celery Worker 1"]
        Worker2["Celery Worker 2"]
    end
    
    subgraph Data_Tier["Data Tier"]
        DB_Primary["PostgreSQL<br/>Primary"]
        DB_Replica["PostgreSQL<br/>Replica"]
        Redis_Cache["Redis<br/>Cache"]
        Redis_Broker["Redis<br/>Task Broker"]
    end
    
    subgraph Storage_Tier["Storage"]
        FileStore["File Storage<br/>[S3/NFS]"]
    end
    
    Users -->|HTTPS| CDN
    Users -->|HTTPS| LB
    CDN --> LB
    
    LB --> Web1
    LB --> Web2
    LB --> Web3
    
    Web1 --> DB_Primary
    Web2 --> DB_Primary
    Web3 --> DB_Primary
    
    Web1 --> DB_Replica
    Web2 --> DB_Replica
    Web3 --> DB_Replica
    
    Web1 --> Redis_Cache
    Web2 --> Redis_Cache
    Web3 --> Redis_Cache
    
    Web1 -.->|Enqueue| Redis_Broker
    Web2 -.->|Enqueue| Redis_Broker
    Web3 -.->|Enqueue| Redis_Broker
    
    Worker1 --> Redis_Broker
    Worker2 --> Redis_Broker
    
    Worker1 --> DB_Primary
    Worker2 --> DB_Primary
    
    Web1 --> FileStore
    Web2 --> FileStore
    Web3 --> FileStore
    Worker1 --> FileStore
    Worker2 --> FileStore
    
    DB_Primary -.->|Replication| DB_Replica
    
    style LB fill:#3498DB,color:#fff
    style Web1 fill:#2C3E50,color:#fff
    style Web2 fill:#2C3E50,color:#fff
    style Web3 fill:#2C3E50,color:#fff
    style Worker1 fill:#27AE60,color:#fff
    style Worker2 fill:#27AE60,color:#fff
    style DB_Primary fill:#E67E22,color:#fff
    style DB_Replica fill:#D35400,color:#fff
    style Redis_Cache fill:#E74C3C,color:#fff
    style Redis_Broker fill:#C0392B,color:#fff
    style FileStore fill:#F39C12,color:#fff
```

## Summary

The C4 model provides comprehensive architecture documentation at 4 levels:

1. **Context (Level 1)**: System boundary and external dependencies
2. **Containers (Level 2)**: Major runtime components and their interactions
3. **Components (Level 3)**: Internal structure of containers
4. **Code (Level 4)**: Class-level design (example provided)

Additional views:
- **Deployment**: Physical/cloud infrastructure layout

This hierarchical approach allows stakeholders at different levels to understand the architecture at appropriate levels of detail:
- **Executives**: Context diagram
- **Technical Managers**: Container diagram
- **Architects**: Component diagram
- **Developers**: Code diagram
