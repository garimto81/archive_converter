# Archive Converter API Architecture

**Version**: 1.0.0
**Updated**: 2025-12-11

---

## 1. System Architecture (Mermaid)

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Dashboard]
        CLI[CLI Tools]
        EXT[External Services]
    end

    subgraph "API Gateway"
        LB[Load Balancer<br/>Nginx]
    end

    subgraph "FastAPI Layer"
        API1[FastAPI Instance 1]
        API2[FastAPI Instance 2]
        API3[FastAPI Instance N]
    end

    subgraph "Service Layer"
        AS[AssetService]
        SS[SegmentService]
        XS[ExportService]
        SES[SearchService]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL<br/>Primary)]
        PGR[(PostgreSQL<br/>Read Replica)]
        ES[(Elasticsearch<br/>Search Index)]
        REDIS[(Redis<br/>Cache/Session)]
    end

    WEB --> LB
    CLI --> LB
    EXT --> LB

    LB --> API1
    LB --> API2
    LB --> API3

    API1 --> AS
    API1 --> SS
    API1 --> XS
    API1 --> SES

    API2 --> AS
    API2 --> SS
    API2 --> XS
    API2 --> SES

    API3 --> AS
    API3 --> SS
    API3 --> XS
    API3 --> SES

    AS --> PG
    AS --> REDIS
    SS --> PG
    SS --> REDIS
    XS --> PGR
    SES --> ES
    SES --> REDIS
```

---

## 2. API Request Flow

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant Middleware
    participant Router
    participant Service
    participant Repository
    participant Database

    Client->>FastAPI: HTTP Request
    FastAPI->>Middleware: CORS, Auth, Rate Limit
    Middleware->>Router: Route to handler
    Router->>Service: Business logic
    Service->>Repository: Data access
    Repository->>Database: SQL Query
    Database-->>Repository: Result
    Repository-->>Service: Domain Model
    Service-->>Router: Business Result
    Router-->>Middleware: Response DTO
    Middleware-->>FastAPI: Serialized JSON
    FastAPI-->>Client: HTTP Response
```

---

## 3. Data Model Conversion Flow

```mermaid
graph LR
    subgraph "Request"
        REQ[Client JSON]
        DTO_REQ[Request DTO<br/>Pydantic]
    end

    subgraph "Business Logic"
        UDM[UDM Model<br/>Asset/Segment]
    end

    subgraph "Persistence"
        ORM[SQLAlchemy ORM]
        DB[(Database)]
    end

    subgraph "Response"
        DTO_RES[Response DTO<br/>Pydantic]
        RES[Client JSON]
    end

    REQ --> DTO_REQ
    DTO_REQ --> UDM
    UDM --> ORM
    ORM --> DB
    DB --> ORM
    ORM --> UDM
    UDM --> DTO_RES
    DTO_RES --> RES
```

---

## 4. Export Pipeline Architecture

```mermaid
graph TB
    subgraph "Export Request"
        USER[Client Request]
        REQ[ExportRequest<br/>JSON/CSV]
    end

    subgraph "Export Service"
        ROUTER[Target Router]
        JSON_EXP[JSON Exporter]
        CSV_EXP[CSV Exporter]
        STREAM[Streaming Handler]
    end

    subgraph "Data Processing"
        FETCH[Fetch Data<br/>from DB]
        TRANSFORM[Transform<br/>UDM → Target Format]
        BUFFER[Stream Buffer]
    end

    subgraph "Output"
        FILE[File Storage]
        DOWNLOAD[Download URL]
    end

    USER --> REQ
    REQ --> ROUTER

    ROUTER --> JSON_EXP
    ROUTER --> CSV_EXP

    JSON_EXP --> FETCH
    CSV_EXP --> FETCH

    FETCH --> TRANSFORM
    TRANSFORM --> BUFFER
    BUFFER --> STREAM

    STREAM --> FILE
    FILE --> DOWNLOAD
    DOWNLOAD --> USER
```

---

## 5. Search Architecture

```mermaid
graph TB
    subgraph "Search Request"
        CLIENT[Client]
        PARAMS[SearchParams<br/>q, filters, tags]
    end

    subgraph "Search Service"
        PARSER[Query Parser]
        BUILDER[Query Builder]
    end

    subgraph "Search Engine"
        ES[(Elasticsearch)]
        PG[(PostgreSQL<br/>Fallback)]
    end

    subgraph "Result Processing"
        SCORE[Relevance Scoring]
        PAGE[Pagination]
        RESULT[SearchResponse]
    end

    CLIENT --> PARAMS
    PARAMS --> PARSER
    PARSER --> BUILDER

    BUILDER --> ES
    BUILDER --> PG

    ES --> SCORE
    PG --> SCORE

    SCORE --> PAGE
    PAGE --> RESULT
    RESULT --> CLIENT
```

---

## 6. Database Schema (ER Diagram)

```mermaid
erDiagram
    ASSET ||--o{ SEGMENT : contains
    ASSET {
        uuid asset_uuid PK
        string file_name
        string file_path_rel
        enum asset_type
        jsonb event_context
        jsonb tech_spec
        string source_origin
        timestamp created_at
    }

    SEGMENT {
        uuid segment_uuid PK
        uuid parent_asset_uuid FK
        enum segment_type
        float time_in_sec
        float time_out_sec
        enum game_type
        int rating
        string winner
        jsonb players
        jsonb tags_action
        jsonb tags_emotion
        jsonb situation_flags
    }

    EVENT_CONTEXT {
        int year
        enum brand
        enum event_type
        enum location
        string venue
        int event_number
        int buyin_usd
    }

    ASSET ||--|| EVENT_CONTEXT : has
```

---

## 7. Caching Strategy

```mermaid
graph TB
    subgraph "Client Request"
        REQ[GET /api/v1/stats]
    end

    subgraph "Cache Layer"
        REDIS[(Redis Cache)]
    end

    subgraph "API Handler"
        CHECK{Cache Hit?}
        FETCH[Fetch from DB]
        STORE[Store to Cache]
    end

    subgraph "Database"
        DB[(PostgreSQL)]
    end

    REQ --> CHECK

    CHECK -->|YES| REDIS
    CHECK -->|NO| FETCH

    FETCH --> DB
    DB --> STORE
    STORE --> REDIS

    REDIS --> REQ
```

**Cache TTL**:
- 통계 (stats): 5분
- Asset 목록: 1분
- Search 결과: 30초
- Asset 상세: 10분 (rarely changes)

---

## 8. Rate Limiting Strategy

```mermaid
graph LR
    subgraph "Request"
        CLIENT[Client IP/Token]
    end

    subgraph "Rate Limiter"
        REDIS[(Redis Counter)]
        CHECK{Limit Exceeded?}
    end

    subgraph "Response"
        OK[200 OK]
        LIMIT[429 Too Many Requests]
    end

    CLIENT --> REDIS
    REDIS --> CHECK

    CHECK -->|NO| OK
    CHECK -->|YES| LIMIT

    OK --> CLIENT
    LIMIT --> CLIENT
```

**Rate Limits**:
- 익명: 100 req/min
- 인증: 1000 req/min
- Export: 10 req/hour

---

## 9. Scaling Architecture

### Horizontal Scaling (Load Balancer)

```mermaid
graph TB
    subgraph "External"
        USERS[Users]
    end

    subgraph "Load Balancer"
        NGINX[Nginx<br/>Round Robin]
    end

    subgraph "FastAPI Cluster"
        API1[Instance 1<br/>:8001]
        API2[Instance 2<br/>:8002]
        API3[Instance 3<br/>:8003]
    end

    subgraph "Shared State"
        REDIS[(Redis<br/>Session Store)]
        PG[(PostgreSQL<br/>Primary)]
    end

    USERS --> NGINX

    NGINX -->|33%| API1
    NGINX -->|33%| API2
    NGINX -->|34%| API3

    API1 --> REDIS
    API2 --> REDIS
    API3 --> REDIS

    API1 --> PG
    API2 --> PG
    API3 --> PG
```

### Read/Write Splitting

```mermaid
graph TB
    subgraph "API Layer"
        WRITE[Write Operations<br/>POST/PUT/DELETE]
        READ[Read Operations<br/>GET]
    end

    subgraph "Database Cluster"
        PRIMARY[(Primary<br/>Read/Write)]
        REPLICA1[(Replica 1<br/>Read Only)]
        REPLICA2[(Replica 2<br/>Read Only)]
    end

    WRITE --> PRIMARY
    PRIMARY -.Replication.-> REPLICA1
    PRIMARY -.Replication.-> REPLICA2

    READ -->|Round Robin| REPLICA1
    READ -->|Round Robin| REPLICA2
```

---

## 10. Security Layers

```mermaid
graph TB
    subgraph "Client"
        USER[User Request]
    end

    subgraph "Security Layers"
        WAF[WAF<br/>SQL Injection, XSS]
        HTTPS[HTTPS/TLS]
        AUTH[JWT Authentication]
        AUTHZ[Authorization<br/>RBAC]
        RATE[Rate Limiting]
        INPUT[Input Validation<br/>Pydantic]
    end

    subgraph "API"
        HANDLER[API Handler]
    end

    USER --> WAF
    WAF --> HTTPS
    HTTPS --> AUTH
    AUTH --> AUTHZ
    AUTHZ --> RATE
    RATE --> INPUT
    INPUT --> HANDLER
```

---

## 11. Monitoring & Observability

```mermaid
graph TB
    subgraph "Application"
        API[FastAPI App]
    end

    subgraph "Metrics"
        PROM[Prometheus<br/>Metrics]
        GRAF[Grafana<br/>Dashboard]
    end

    subgraph "Logs"
        LOG[Structured Logs<br/>JSON]
        ELK[ELK Stack]
    end

    subgraph "Tracing"
        TRACE[OpenTelemetry]
        JAEGER[Jaeger UI]
    end

    subgraph "Alerts"
        ALERT[Alertmanager]
        SLACK[Slack/Email]
    end

    API --> PROM
    API --> LOG
    API --> TRACE

    PROM --> GRAF
    LOG --> ELK
    TRACE --> JAEGER

    PROM --> ALERT
    ALERT --> SLACK
```

**Key Metrics**:
- Request rate (req/sec)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Database connection pool
- Cache hit rate

---

## 12. Deployment Architecture

```mermaid
graph TB
    subgraph "Development"
        DEV[Dev Environment<br/>Local Docker]
    end

    subgraph "CI/CD"
        GH[GitHub Actions]
        TEST[Unit/Integration Tests]
        BUILD[Docker Build]
    end

    subgraph "Staging"
        STAGE[Staging Environment<br/>K8s Cluster]
    end

    subgraph "Production"
        PROD[Production<br/>K8s Cluster]
        CANARY[Canary Deployment]
    end

    DEV --> GH
    GH --> TEST
    TEST --> BUILD
    BUILD --> STAGE
    STAGE --> CANARY
    CANARY --> PROD
```

---

## 13. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Framework** | FastAPI 0.104+ | Async REST API |
| **Validation** | Pydantic 2.5+ | Type safety, validation |
| **Server** | Uvicorn 0.24+ | ASGI server |
| **Database** | PostgreSQL 15+ | Primary data store |
| **Search** | Elasticsearch 8.0+ | Full-text search |
| **Cache** | Redis 7.0+ | Session, statistics |
| **ORM** | SQLAlchemy 2.0+ | Async ORM |
| **Migration** | Alembic 1.12+ | Schema migration |
| **Auth** | JWT + PassLib | Authentication |
| **Rate Limit** | Redis + FastAPI | Request throttling |
| **Monitoring** | Prometheus + Grafana | Metrics |
| **Logging** | Structlog | Structured logging |
| **Container** | Docker + K8s | Deployment |

---

## 14. Related Documents

- **API Design**: `D:\AI\claude01\Archive_Converter\docs\API_DESIGN.md`
- **UDM Schema**: `D:\AI\claude01\Archive_Converter\src\models\udm.py`
- **Export PRD**: `D:\AI\claude01\Archive_Converter\prds\PRD-0005-EXPORT-AGENT.md`
