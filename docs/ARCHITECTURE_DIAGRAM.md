# Penguin AI Agent - Architecture Diagrams

## System Architecture

```mermaid
graph TB
    subgraph "User Interface"
        CLI[CLI Interface<br/>main.py]
    end
    
    subgraph "Agent Layer"
        COORD[Coordinator Agent<br/>Orchestrates workflow]
        ANALYZER[Analyzer Agent<br/>Repository analysis]
        MAINTAINER[Maintainer Agent<br/>Suggestion generation]
    end
    
    subgraph "AI/LLM Layer"
        GEMINI[Google Gemini<br/>gemini-2.0-flash-exp]
    end
    
    subgraph "Memory & State"
        SESSION[Session Service<br/>InMemorySessionService]
        MEMORY[Memory Bank<br/>Long-term storage]
        PROFILES[Repository Profiles]
        SUGGESTIONS[Suggestion History]
    end
    
    subgraph "External APIs"
        GITHUB[GitHub API<br/>Repository data]
    end
    
    subgraph "Observability"
        METRICS[Metrics Collector<br/>Performance tracking]
        LOGS[Structured Logging<br/>Event tracking]
    end
    
    CLI --> COORD
    COORD --> ANALYZER
    COORD --> MAINTAINER
    
    ANALYZER --> GEMINI
    MAINTAINER --> GEMINI
    
    ANALYZER --> GITHUB
    MAINTAINER --> GITHUB
    
    ANALYZER --> MEMORY
    MAINTAINER --> MEMORY
    
    COORD --> SESSION
    SESSION --> PROFILES
    SESSION --> SUGGESTIONS
    
    ANALYZER --> METRICS
    MAINTAINER --> METRICS
    COORD --> LOGS
    
    style COORD fill:#4CAF50
    style ANALYZER fill:#2196F3
    style MAINTAINER fill:#FF9800
    style GEMINI fill:#9C27B0
    style GITHUB fill:#000000,color:#fff
```

## Agent Workflow

```mermaid
sequenceDiagram
    participant User
    participant Coordinator
    participant Analyzer
    participant Maintainer
    participant Gemini
    participant GitHub
    participant Memory
    
    User->>Coordinator: analyze_repositories(username, filters)
    
    Coordinator->>GitHub: Fetch user repositories
    GitHub-->>Coordinator: Repository list
    
    loop For each repository
        Coordinator->>Analyzer: analyze_repository(repo)
        
        Analyzer->>GitHub: Get repo overview & history
        GitHub-->>Analyzer: Repository data
        
        Analyzer->>Gemini: Generate health snapshot
        Gemini-->>Analyzer: Health assessment
        
        Analyzer->>Gemini: Create repository profile
        Gemini-->>Analyzer: Repository profile
        
        Analyzer->>Memory: Save profile
        Analyzer-->>Coordinator: Analysis complete
    end
    
    Coordinator->>Maintainer: generate_suggestions(profiles)
    
    loop For each profile
        Maintainer->>Memory: Check for duplicates
        Memory-->>Maintainer: Existing suggestions
        
        Maintainer->>Gemini: Generate suggestions
        Gemini-->>Maintainer: New suggestions
        
        Maintainer->>Maintainer: Deduplicate & prioritize
    end
    
    Maintainer-->>Coordinator: Prioritized suggestions
    
    Coordinator->>User: Request approval
    User-->>Coordinator: Approved suggestions
    
    loop For each approved suggestion
        Coordinator->>Maintainer: create_github_issue(suggestion)
        Maintainer->>GitHub: Create issue
        GitHub-->>Maintainer: Issue URL
        Maintainer->>Memory: Save suggestion
        Maintainer-->>Coordinator: Issue created
    end
    
    Coordinator-->>User: Analysis results
```

## Data Flow Architecture

```mermaid
graph LR
    subgraph "Input"
        A[GitHub Username]
        B[Repository Filters]
        C[User Preferences]
    end
    
    subgraph "Processing Pipeline"
        D[Repository Discovery]
        E[Parallel Analysis]
        F[Health Assessment]
        G[Profile Generation]
        H[Suggestion Generation]
        I[Deduplication]
        J[Prioritization]
        K[Approval]
        L[Issue Creation]
    end
    
    subgraph "Output"
        M[GitHub Issues]
        N[Analysis Report]
        O[Metrics]
    end
    
    A --> D
    B --> D
    C --> D
    
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    J --> K
    K --> L
    
    L --> M
    L --> N
    L --> O
    
    style D fill:#E3F2FD
    style E fill:#E3F2FD
    style F fill:#FFF3E0
    style G fill:#FFF3E0
    style H fill:#F3E5F5
    style I fill:#F3E5F5
    style J fill:#F3E5F5
    style K fill:#E8F5E9
    style L fill:#E8F5E9
```

## Multi-Agent System Components

```mermaid
graph TB
    subgraph "Coordinator Agent"
        C1[Workflow Orchestration]
        C2[Progress Tracking]
        C3[Error Handling]
        C4[Session Management]
    end
    
    subgraph "Analyzer Agent"
        A1[Repository Fetching]
        A2[Health Assessment<br/>LLM-powered]
        A3[Profile Creation<br/>LLM-powered]
        A4[Context Compaction]
    end
    
    subgraph "Maintainer Agent"
        M1[Suggestion Generation<br/>LLM-powered]
        M2[Deduplication]
        M3[Prioritization]
        M4[Issue Creation]
    end
    
    subgraph "Supporting Systems"
        S1[Memory Bank]
        S2[GitHub Client]
        S3[Metrics Collector]
        S4[Logging System]
    end
    
    C1 --> A1
    C1 --> M1
    C2 --> S3
    C3 --> S4
    C4 --> S1
    
    A1 --> S2
    A2 --> A3
    A3 --> A4
    A4 --> S1
    
    M1 --> M2
    M2 --> M3
    M3 --> M4
    M4 --> S2
    
    style C1 fill:#4CAF50
    style A2 fill:#2196F3
    style A3 fill:#2196F3
    style M1 fill:#FF9800
```

## Technology Stack

```mermaid
graph TB
    subgraph "Core Technologies"
        PYTHON[Python 3.11+]
        LANGGRAPH[LangGraph<br/>Agent Framework]
        GOOGLE_ADK[Google ADK<br/>Agent Development Kit]
    end
    
    subgraph "AI/ML"
        GEMINI_MODEL[Gemini 2.0 Flash<br/>LLM Model]
        GENAI[Google GenerativeAI SDK]
    end
    
    subgraph "APIs & Tools"
        GITHUB_API[GitHub REST API]
        GITHUB_CLIENT[Custom GitHub Client]
    end
    
    subgraph "Storage & Memory"
        JSON_STORAGE[JSON File Storage]
        IN_MEMORY[In-Memory Sessions]
    end
    
    subgraph "Observability"
        LOGGING[Structured Logging]
        METRICS_SYS[Custom Metrics]
    end
    
    PYTHON --> LANGGRAPH
    PYTHON --> GOOGLE_ADK
    LANGGRAPH --> GEMINI_MODEL
    GOOGLE_ADK --> GENAI
    GENAI --> GEMINI_MODEL
    
    PYTHON --> GITHUB_CLIENT
    GITHUB_CLIENT --> GITHUB_API
    
    PYTHON --> JSON_STORAGE
    PYTHON --> IN_MEMORY
    
    PYTHON --> LOGGING
    PYTHON --> METRICS_SYS
    
    style PYTHON fill:#3776AB,color:#fff
    style GEMINI_MODEL fill:#9C27B0,color:#fff
    style GITHUB_API fill:#000000,color:#fff
```

## Key Features Implementation

| Feature | Implementation | Agent Responsible |
|---------|---------------|-------------------|
| Multi-Agent System | LangGraph + Google ADK | Coordinator |
| Repository Analysis | GitHub API + LLM reasoning | Analyzer |
| Health Assessment | Gemini-powered evaluation | Analyzer |
| Smart Suggestions | LLM-generated recommendations | Maintainer |
| Memory & Deduplication | JSON-based Memory Bank | Maintainer |
| Session Management | InMemorySessionService | Coordinator |
| Observability | Structured logging + metrics | All agents |
| Context Engineering | Token-aware compaction | Analyzer |
| Parallel Processing | ThreadPoolExecutor | Analyzer |
| Issue Automation | GitHub API integration | Maintainer |

## Deployment Options

```mermaid
graph TB
    subgraph "Local Development"
        LOCAL[Local CLI<br/>python main.py]
    end
    
    subgraph "Cloud Deployment Options"
        CLOUD_RUN[Google Cloud Run<br/>Containerized service]
        VERTEX[Vertex AI<br/>Managed agents]
    end
    
    subgraph "CI/CD"
        GITHUB_ACTIONS[GitHub Actions<br/>Automated workflows]
    end
    
    LOCAL --> CLOUD_RUN
    LOCAL --> VERTEX
    GITHUB_ACTIONS --> CLOUD_RUN
    GITHUB_ACTIONS --> VERTEX
    
    style LOCAL fill:#4CAF50
    style CLOUD_RUN fill:#4285F4,color:#fff
    style VERTEX fill:#4285F4,color:#fff
```
