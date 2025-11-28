# Semantic Search Architecture Diagrams

## 1. System Architecture

```mermaid
graph TB
    User[👤 User] -->|/search| Bot[🤖 Telegram Bot]
    Bot -->|Query| SearchHandler[Search Handler]
    SearchHandler -->|Text| SearchEngine[Semantic Search Engine]
    SearchEngine -->|Embedding| Model[Sentence Transformer Model]
    Model -->|Vector 384d| SearchEngine
    SearchEngine -->|Compare| Storage[(SQLite Database)]
    Storage -->|Questions + Embeddings| SearchEngine
    SearchEngine -->|Ranked Results| SearchHandler
    SearchHandler -->|Formatted Response| Bot
    Bot -->|Results| User

    style Model fill:#e1f5ff
    style SearchEngine fill:#fff4e1
    style Storage fill:#e8f5e9
    style SearchHandler fill:#fce4ec
```

## 2. Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant B as Bot
    participant H as Search Handler
    participant E as Search Engine
    participant M as Model
    participant D as Database

    U->>B: /search
    B->>H: Start search conversation
    H->>U: Request query
    U->>B: "как установить python"
    B->>H: Process query
    H->>E: search(query)
    E->>M: encode(query)
    M-->>E: query_embedding [384d]
    E->>D: get_all_questions_with_embeddings()
    D-->>E: questions + embeddings
    E->>E: compute_similarity()
    E->>E: rank_by_score()
    E->>E: filter_by_threshold()
    E-->>H: top_k results with scores
    H->>H: format_results()
    H->>U: Display ranked results
```

## 3. Component Architecture

```mermaid
graph LR
    subgraph "Bot Layer"
        Bot[bot.py]
        Handlers[handlers/]
    end

    subgraph "Business Logic"
        SearchHandler[search.py]
        SearchEngine[semantic_search.py]
    end

    subgraph "Data Layer"
        Storage[sqlite.py]
        DB[(SQLite DB)]
    end

    subgraph "ML Layer"
        Model[Sentence Transformer]
        Cache[Model Cache]
    end

    Bot --> Handlers
    Handlers --> SearchHandler
    SearchHandler --> SearchEngine
    SearchEngine --> Model
    SearchEngine --> Storage
    Storage --> DB
    Model --> Cache

    style Bot fill:#e3f2fd
    style SearchHandler fill:#fff3e0
    style SearchEngine fill:#f3e5f5
    style Storage fill:#e8f5e9
    style Model fill:#fce4ec
```

## 4. Embedding Storage

```mermaid
graph TB
    subgraph "Question Record"
        ID[id: UUID]
        Q[question: TEXT]
        A[answer: TEXT]
        E[embedding: BLOB]
        Meta[metadata...]
    end

    subgraph "Embedding Format"
        NP[NumPy Array]
        F32[384 × float32]
        Bytes[1,536 bytes]
    end

    Q -->|encode| NP
    NP -->|serialize| F32
    F32 -->|tobytes| Bytes
    Bytes --> E

    style Q fill:#e1f5ff
    style E fill:#fff4e1
    style NP fill:#e8f5e9
```

## 5. Search Process

```mermaid
flowchart TD
    Start([User Query]) --> Validate{Valid Query?}
    Validate -->|No| Error[Show Error]
    Validate -->|Yes| Encode[Generate Query Embedding]
    Encode --> Load[Load All Question Embeddings]
    Load --> Compute[Compute Cosine Similarity]
    Compute --> Rank[Rank by Similarity Score]
    Rank --> Filter{Score > Threshold?}
    Filter -->|Yes| Keep[Keep Result]
    Filter -->|No| Discard[Discard Result]
    Keep --> TopK[Select Top K Results]
    Discard --> TopK
    TopK --> HasResults{Has Results?}
    HasResults -->|Yes| Display[Display Results]
    HasResults -->|No| NoResults[Show No Results Message]
    Display --> End([Done])
    NoResults --> End
    Error --> End

    style Start fill:#e8f5e9
    style Encode fill:#fff4e1
    style Compute fill:#e1f5ff
    style Display fill:#f3e5f5
    style End fill:#e8f5e9
```

## 6. Model Loading Strategy

```mermaid
stateDiagram-v2
    [*] --> Uninitialized
    Uninitialized --> Loading: First Search Request
    Loading --> Loaded: Success
    Loading --> Error: Failure
    Error --> Loading: Retry
    Loaded --> Cached: Subsequent Requests
    Cached --> Cached: Reuse Model

    note right of Loaded
        Model in Memory
        ~500MB RAM
    end note

    note right of Cached
        Singleton Pattern
        No Reload Needed
    end note
```

## 7. Database Schema Evolution

```mermaid
graph LR
    subgraph "Before Migration"
        T1[questions table]
        C1[id, question, answer, created_at, created_by, updated_at]
    end

    subgraph "After Migration"
        T2[questions table]
        C2[id, question, answer, created_at, created_by, updated_at, embedding]
    end

    T1 -->|ALTER TABLE ADD COLUMN| T2

    subgraph "Migration Process"
        M1[Read all questions]
        M2[Generate embeddings]
        M3[Update records]
    end

    T1 --> M1
    M1 --> M2
    M2 --> M3
    M3 --> T2

    style T1 fill:#ffebee
    style T2 fill:#e8f5e9
    style M2 fill:#fff4e1
```

## 8. Similarity Computation

```mermaid
graph TB
    subgraph "Input"
        Q[Query Embedding<br/>384 dimensions]
        D1[Doc 1 Embedding<br/>384 dimensions]
        D2[Doc 2 Embedding<br/>384 dimensions]
        D3[Doc N Embedding<br/>384 dimensions]
    end

    subgraph "Computation"
        Dot[Dot Product]
        Norm[Normalize]
        Cos[Cosine Similarity]
    end

    subgraph "Output"
        S1[Score 1: 0.95]
        S2[Score 2: 0.78]
        S3[Score N: 0.45]
    end

    Q --> Dot
    D1 --> Dot
    D2 --> Dot
    D3 --> Dot
    Dot --> Norm
    Norm --> Cos
    Cos --> S1
    Cos --> S2
    Cos --> S3

    style Q fill:#e1f5ff
    style Cos fill:#fff4e1
    style S1 fill:#e8f5e9
```

## 9. Error Handling Flow

```mermaid
flowchart TD
    Start([Search Request]) --> Try{Try Search}
    Try -->|Success| Results[Return Results]
    Try -->|Model Error| LoadFail[Model Load Failed]
    Try -->|Embedding Error| EmbedFail[Embedding Generation Failed]
    Try -->|DB Error| DBFail[Database Error]

    LoadFail --> Fallback1{Fallback Available?}
    EmbedFail --> Fallback2{Fallback Available?}
    DBFail --> Fallback3{Fallback Available?}

    Fallback1 -->|Yes| Keyword[Keyword Search]
    Fallback2 -->|Yes| Keyword
    Fallback3 -->|Yes| Keyword

    Fallback1 -->|No| Error[Show Error Message]
    Fallback2 -->|No| Error
    Fallback3 -->|No| Error

    Keyword --> KeyResults{Has Results?}
    KeyResults -->|Yes| Results
    KeyResults -->|No| ShowAll[Show All Questions]

    Results --> End([Done])
    ShowAll --> End
    Error --> End

    style Try fill:#e1f5ff
    style Keyword fill:#fff4e1
    style Error fill:#ffebee
    style Results fill:#e8f5e9
```

## 10. Performance Optimization

```mermaid
graph TB
    subgraph "Optimization Strategies"
        S1[Singleton Pattern<br/>One Model Instance]
        S2[Lazy Loading<br/>Load on First Use]
        S3[Batch Processing<br/>Migration in Batches]
        S4[Caching<br/>Keep Model in Memory]
    end

    subgraph "Performance Metrics"
        M1[Model Load: < 5s]
        M2[Search Time: < 500ms]
        M3[Memory: ~500MB]
        M4[Disk: ~670MB]
    end

    S1 --> M1
    S2 --> M1
    S3 --> M2
    S4 --> M3

    style S1 fill:#e8f5e9
    style S2 fill:#e8f5e9
    style S3 fill:#e8f5e9
    style S4 fill:#e8f5e9
    style M1 fill:#e1f5ff
    style M2 fill:#e1f5ff
    style M3 fill:#e1f5ff
    style M4 fill:#e1f5ff
```

## 11. User Experience Flow

```mermaid
journey
    title Semantic Search User Journey
    section Discovery
      User needs answer: 5: User
      Remembers bot has search: 4: User
    section Search
      Types /search command: 5: User
      Enters natural language query: 5: User
      Bot processes query: 3: Bot
    section Results
      Receives ranked results: 5: User
      Sees similarity scores: 4: User
      Finds relevant answer: 5: User
    section Action
      Clicks to view full answer: 5: User
      Problem solved: 5: User
```

## 12. Deployment Pipeline

```mermaid
flowchart LR
    Dev[Development] --> Test[Testing]
    Test --> Deps[Install Dependencies]
    Deps --> Download[Download Model]
    Download --> Migrate[Run Migration]
    Migrate --> Start[Start Bot]
    Start --> Verify[Verify Search]
    Verify --> Monitor[Monitor Performance]
    Monitor --> Prod[Production]

    style Dev fill:#e3f2fd
    style Download fill:#fff3e0
    style Migrate fill:#f3e5f5
    style Verify fill:#e8f5e9
    style Prod fill:#c8e6c9
```

---

## Legend

- 🤖 Bot Components
- 💾 Storage/Database
- 🧠 ML/AI Components
- 👤 User Interactions
- ⚙️ Processing Steps
- 📊 Data Flow
- ✅ Success States
- ❌ Error States

## Notes

All diagrams use Mermaid syntax and can be rendered in:
- GitHub
- GitLab
- VS Code (with Mermaid extension)
- Documentation sites
- Markdown viewers

These diagrams provide visual representation of:
1. Overall system architecture
2. Data flow between components
3. Search process step-by-step
4. Database schema changes
5. Error handling strategies
6. Performance optimization
7. User experience journey
8. Deployment process
