# Penguin AI Agent - Working Flow Diagrams

## Complete System Flow

```mermaid
flowchart TD
    START([User Starts Analysis]) --> INPUT[Provide GitHub Username<br/>+ Filters + Preferences]
    
    INPUT --> INIT[Initialize System]
    INIT --> VALIDATE{Validate<br/>Credentials}
    
    VALIDATE -->|Invalid| ERROR1[Show Error Message]
    ERROR1 --> END1([Exit])
    
    VALIDATE -->|Valid| CREATE_AGENTS[Create Agent Instances<br/>Coordinator, Analyzer, Maintainer]
    
    CREATE_AGENTS --> FETCH[Fetch User Repositories<br/>from GitHub API]
    
    FETCH --> FILTER{Apply<br/>Filters?}
    FILTER -->|Yes| APPLY_FILTER[Filter by Language,<br/>Date, Visibility]
    FILTER -->|No| REPO_LIST[Repository List]
    APPLY_FILTER --> REPO_LIST
    
    REPO_LIST --> PARALLEL{Parallel<br/>Analysis}
    
    PARALLEL --> ANALYZE1[Analyze Repo 1]
    PARALLEL --> ANALYZE2[Analyze Repo 2]
    PARALLEL --> ANALYZE3[Analyze Repo N]
    
    ANALYZE1 --> HEALTH1[Generate Health Snapshot<br/>using Gemini LLM]
    ANALYZE2 --> HEALTH2[Generate Health Snapshot<br/>using Gemini LLM]
    ANALYZE3 --> HEALTH3[Generate Health Snapshot<br/>using Gemini LLM]
    
    HEALTH1 --> PROFILE1[Create Repository Profile<br/>using Gemini LLM]
    HEALTH2 --> PROFILE2[Create Repository Profile<br/>using Gemini LLM]
    HEALTH3 --> PROFILE3[Create Repository Profile<br/>using Gemini LLM]
    
    PROFILE1 --> SAVE1[Save to Memory Bank]
    PROFILE2 --> SAVE2[Save to Memory Bank]
    PROFILE3 --> SAVE3[Save to Memory Bank]
    
    SAVE1 --> COLLECT[Collect All Profiles]
    SAVE2 --> COLLECT
    SAVE3 --> COLLECT
    
    COLLECT --> GEN_SUGG[Generate Suggestions<br/>using Gemini LLM]
    
    GEN_SUGG --> DEDUP[Deduplicate Against<br/>Memory Bank]
    
    DEDUP --> PRIORITIZE[Prioritize by Impact<br/>& Effort]
    
    PRIORITIZE --> APPROVAL{Request<br/>Approval}
    
    APPROVAL -->|Auto Mode| AUTO_APPROVE[Auto-approve All]
    APPROVAL -->|Manual Mode| SHOW_SUGG[Display Suggestions<br/>to User]
    
    SHOW_SUGG --> USER_CHOICE{User<br/>Choice}
    USER_CHOICE -->|Approve All| APPROVED_ALL[All Suggestions]
    USER_CHOICE -->|Select Some| APPROVED_SOME[Selected Suggestions]
    USER_CHOICE -->|Approve None| APPROVED_NONE[No Suggestions]
    USER_CHOICE -->|Quit| END2([Exit])
    
    AUTO_APPROVE --> CREATE_ISSUES
    APPROVED_ALL --> CREATE_ISSUES
    APPROVED_SOME --> CREATE_ISSUES
    APPROVED_NONE --> RESULTS
    
    CREATE_ISSUES[Create GitHub Issues] --> ISSUE_LOOP{More<br/>Issues?}
    
    ISSUE_LOOP -->|Yes| CREATE_ONE[Create Issue via<br/>GitHub API]
    CREATE_ONE --> SAVE_SUGG[Save Suggestion<br/>to Memory]
    SAVE_SUGG --> ISSUE_LOOP
    
    ISSUE_LOOP -->|No| RESULTS[Display Results<br/>& Metrics]
    
    RESULTS --> END3([Complete])
    
    style START fill:#4CAF50,color:#fff
    style CREATE_AGENTS fill:#2196F3,color:#fff
    style HEALTH1 fill:#9C27B0,color:#fff
    style HEALTH2 fill:#9C27B0,color:#fff
    style HEALTH3 fill:#9C27B0,color:#fff
    style GEN_SUGG fill:#9C27B0,color:#fff
    style CREATE_ISSUES fill:#FF9800,color:#fff
    style END3 fill:#4CAF50,color:#fff
```

## Agent Interaction Flow

```mermaid
sequenceDiagram
    autonumber
    
    actor User
    participant CLI
    participant Coordinator
    participant Analyzer
    participant Maintainer
    participant Gemini
    participant GitHub
    participant Memory
    
    User->>CLI: python main.py analyze username
    CLI->>CLI: Parse arguments & validate
    CLI->>Coordinator: analyze_repositories()
    
    Note over Coordinator: Session Creation
    Coordinator->>Coordinator: Create session with ID
    Coordinator->>Memory: Initialize session state
    
    Note over Coordinator,GitHub: Repository Discovery
    Coordinator->>GitHub: GET /users/{username}/repos
    GitHub-->>Coordinator: Repository list
    Coordinator->>Coordinator: Apply filters
    
    Note over Coordinator,Analyzer: Parallel Analysis Phase
    
    par Repository 1
        Coordinator->>Analyzer: analyze_repository(repo1)
        Analyzer->>GitHub: GET repo overview
        GitHub-->>Analyzer: Repo data
        Analyzer->>Gemini: Generate health snapshot
        Gemini-->>Analyzer: Health assessment JSON
        Analyzer->>Gemini: Create profile
        Gemini-->>Analyzer: Profile JSON
        Analyzer->>Memory: Save profile
        Analyzer-->>Coordinator: Analysis complete
    and Repository 2
        Coordinator->>Analyzer: analyze_repository(repo2)
        Analyzer->>GitHub: GET repo overview
        GitHub-->>Analyzer: Repo data
        Analyzer->>Gemini: Generate health snapshot
        Gemini-->>Analyzer: Health assessment JSON
        Analyzer->>Gemini: Create profile
        Gemini-->>Analyzer: Profile JSON
        Analyzer->>Memory: Save profile
        Analyzer-->>Coordinator: Analysis complete
    end
    
    Note over Coordinator,Maintainer: Suggestion Generation Phase
    
    Coordinator->>Maintainer: generate_suggestions(profiles)
    
    loop For each profile
        Maintainer->>Memory: Load existing suggestions
        Memory-->>Maintainer: Historical suggestions
        Maintainer->>Gemini: Generate new suggestions
        Gemini-->>Maintainer: Suggestions JSON
        Maintainer->>Maintainer: Deduplicate
        Maintainer->>Maintainer: Prioritize
    end
    
    Maintainer-->>Coordinator: All suggestions
    
    Note over Coordinator,User: Approval Phase
    
    Coordinator->>CLI: Request approval
    CLI->>User: Display suggestions
    User-->>CLI: Approve selected
    CLI-->>Coordinator: Approved list
    
    Note over Coordinator,GitHub: Issue Creation Phase
    
    loop For each approved suggestion
        Coordinator->>Maintainer: create_github_issue()
        Maintainer->>GitHub: POST /repos/{owner}/{repo}/issues
        GitHub-->>Maintainer: Issue URL
        Maintainer->>Memory: Save suggestion
        Maintainer-->>Coordinator: Issue created
        Coordinator->>CLI: Progress update
        CLI->>User: Show issue URL
    end
    
    Note over Coordinator: Finalization
    
    Coordinator->>Coordinator: Collect metrics
    Coordinator->>CLI: Return results
    CLI->>User: Display summary
```

## Data Processing Pipeline

```mermaid
flowchart LR
    subgraph "Input Stage"
        A1[GitHub Username]
        A2[Repository Filters]
        A3[User Preferences]
    end
    
    subgraph "Discovery Stage"
        B1[Fetch Repositories]
        B2[Apply Filters]
        B3[Repository List]
    end
    
    subgraph "Analysis Stage"
        C1[Fetch Repo Data]
        C2[LLM Health Assessment]
        C3[LLM Profile Generation]
        C4[Context Compaction]
    end
    
    subgraph "Suggestion Stage"
        D1[Load Memory]
        D2[LLM Suggestion Generation]
        D3[Deduplication]
        D4[Prioritization]
    end
    
    subgraph "Approval Stage"
        E1[Display to User]
        E2[User Selection]
        E3[Approved List]
    end
    
    subgraph "Execution Stage"
        F1[Create GitHub Issues]
        F2[Save to Memory]
        F3[Track Metrics]
    end
    
    subgraph "Output Stage"
        G1[Issue URLs]
        G2[Analysis Report]
        G3[Performance Metrics]
    end
    
    A1 --> B1
    A2 --> B2
    A3 --> B2
    B1 --> B2
    B2 --> B3
    
    B3 --> C1
    C1 --> C2
    C2 --> C3
    C3 --> C4
    
    C4 --> D1
    D1 --> D2
    D2 --> D3
    D3 --> D4
    
    D4 --> E1
    E1 --> E2
    E2 --> E3
    
    E3 --> F1
    F1 --> F2
    F2 --> F3
    
    F1 --> G1
    F3 --> G2
    F3 --> G3
    
    style C2 fill:#9C27B0,color:#fff
    style C3 fill:#9C27B0,color:#fff
    style D2 fill:#9C27B0,color:#fff
```

## Memory & State Management

```mermaid
stateDiagram-v2
    [*] --> SessionCreated: User starts analysis
    
    SessionCreated --> FetchingRepos: Initialize agents
    
    FetchingRepos --> AnalyzingRepos: Repos fetched
    
    state AnalyzingRepos {
        [*] --> AnalyzeRepo1
        [*] --> AnalyzeRepo2
        [*] --> AnalyzeRepoN
        
        AnalyzeRepo1 --> SaveProfile1
        AnalyzeRepo2 --> SaveProfile2
        AnalyzeRepoN --> SaveProfileN
        
        SaveProfile1 --> [*]
        SaveProfile2 --> [*]
        SaveProfileN --> [*]
    }
    
    AnalyzingRepos --> GeneratingSuggestions: All profiles saved
    
    state GeneratingSuggestions {
        [*] --> LoadMemory
        LoadMemory --> GenerateNew
        GenerateNew --> Deduplicate
        Deduplicate --> Prioritize
        Prioritize --> [*]
    }
    
    GeneratingSuggestions --> RequestingApproval: Suggestions ready
    
    RequestingApproval --> CreatingIssues: User approved
    RequestingApproval --> Complete: User declined
    
    state CreatingIssues {
        [*] --> CreateIssue
        CreateIssue --> SaveToMemory
        SaveToMemory --> CreateIssue: More issues
        SaveToMemory --> [*]: All done
    }
    
    CreatingIssues --> Complete: All issues created
    
    Complete --> [*]
    
    note right of SessionCreated
        InMemorySessionService
        - Session ID
        - User preferences
        - Temporary state
    end note
    
    note right of SaveProfile1
        Memory Bank (JSON)
        - Repository profiles
        - Health snapshots
        - Persistent storage
    end note
    
    note right of SaveToMemory
        Memory Bank (JSON)
        - Suggestion history
        - Deduplication data
        - Issue tracking
    end note
```

## Error Handling & Fallback Flow

```mermaid
flowchart TD
    START[Operation Start] --> TRY{Try<br/>Operation}
    
    TRY -->|Success| SUCCESS[Operation Complete]
    TRY -->|Error| ERROR_TYPE{Error<br/>Type}
    
    ERROR_TYPE -->|LLM Failure| FALLBACK_LLM[Use Rule-Based<br/>Fallback Logic]
    ERROR_TYPE -->|API Rate Limit| RETRY[Retry with<br/>Exponential Backoff]
    ERROR_TYPE -->|Network Error| RETRY
    ERROR_TYPE -->|Auth Error| FAIL[Report Error<br/>& Exit]
    ERROR_TYPE -->|Not Found| SKIP[Skip Repository<br/>& Continue]
    
    FALLBACK_LLM --> LOG1[Log Fallback Usage]
    LOG1 --> METRICS1[Record Recovery Metric]
    METRICS1 --> SUCCESS
    
    RETRY --> RETRY_COUNT{Retry<br/>Count < 3}
    RETRY_COUNT -->|Yes| WAIT[Wait & Retry]
    WAIT --> TRY
    RETRY_COUNT -->|No| FALLBACK_LLM
    
    SKIP --> LOG2[Log Skip Event]
    LOG2 --> CONTINUE[Continue with<br/>Next Repository]
    
    SUCCESS --> END([Complete])
    FAIL --> END
    CONTINUE --> END
    
    style FALLBACK_LLM fill:#FF9800
    style RETRY fill:#FFC107
    style SUCCESS fill:#4CAF50,color:#fff
    style FAIL fill:#F44336,color:#fff
```

## Observability & Monitoring Flow

```mermaid
flowchart LR
    subgraph "Agent Operations"
        A1[Coordinator]
        A2[Analyzer]
        A3[Maintainer]
    end
    
    subgraph "Logging System"
        L1[Structured Logger]
        L2[Event Context]
        L3[Log Levels]
    end
    
    subgraph "Metrics System"
        M1[Metrics Collector]
        M2[API Call Tracking]
        M3[Token Usage]
        M4[Performance Timing]
        M5[Error Counting]
    end
    
    subgraph "Output"
        O1[Console Output]
        O2[Log Files]
        O3[Metrics Report]
    end
    
    A1 --> L1
    A2 --> L1
    A3 --> L1
    
    A1 --> M1
    A2 --> M1
    A3 --> M1
    
    L1 --> L2
    L2 --> L3
    
    M1 --> M2
    M1 --> M3
    M1 --> M4
    M1 --> M5
    
    L3 --> O1
    L3 --> O2
    
    M2 --> O3
    M3 --> O3
    M4 --> O3
    M5 --> O3
    
    style L1 fill:#2196F3,color:#fff
    style M1 fill:#FF9800,color:#fff
```

## Token Usage & Cost Optimization

```mermaid
flowchart TD
    START[Repository Data] --> COMPACT[Context Compaction]
    
    COMPACT --> README{README<br/>Size}
    README -->|> 1000 chars| TRUNCATE1[Truncate to 1000 chars]
    README -->|<= 1000 chars| KEEP1[Keep Full Content]
    
    TRUNCATE1 --> LANG[Language Analysis]
    KEEP1 --> LANG
    
    LANG --> TOP_LANG[Keep Top 3-5 Languages]
    
    TOP_LANG --> FILES{File<br/>Count}
    FILES -->|> 20 files| LIMIT_FILES[Limit to 20 files]
    FILES -->|<= 20 files| KEEP_FILES[Keep All Files]
    
    LIMIT_FILES --> STRUCTURE[Structured Context]
    KEEP_FILES --> STRUCTURE
    
    STRUCTURE --> PROMPT[Generate Prompt]
    
    PROMPT --> TOKEN_COUNT{Token<br/>Count}
    TOKEN_COUNT -->|> 4000| REDUCE[Further Reduction]
    TOKEN_COUNT -->|<= 4000| SEND[Send to LLM]
    
    REDUCE --> PROMPT
    
    SEND --> RESPONSE[LLM Response]
    
    RESPONSE --> PARSE[Parse JSON]
    
    PARSE --> VALIDATE{Valid<br/>Response}
    VALIDATE -->|Yes| SUCCESS[Use Response]
    VALIDATE -->|No| FALLBACK[Use Fallback Logic]
    
    SUCCESS --> TRACK[Track Token Usage]
    FALLBACK --> TRACK
    
    TRACK --> END([Complete])
    
    style COMPACT fill:#FFC107
    style SEND fill:#9C27B0,color:#fff
    style TRACK fill:#4CAF50,color:#fff
```

## Parallel Processing Architecture

```mermaid
graph TB
    subgraph "Main Thread"
        MAIN[Coordinator Agent]
    end
    
    subgraph "Thread Pool (5 workers)"
        W1[Worker 1]
        W2[Worker 2]
        W3[Worker 3]
        W4[Worker 4]
        W5[Worker 5]
    end
    
    subgraph "Repository Queue"
        R1[Repo 1]
        R2[Repo 2]
        R3[Repo 3]
        R4[Repo 4]
        R5[Repo 5]
        R6[Repo 6]
        R7[Repo 7]
        R8[Repo 8]
    end
    
    subgraph "Results Collection"
        RESULTS[Analysis Results]
    end
    
    MAIN --> W1
    MAIN --> W2
    MAIN --> W3
    MAIN --> W4
    MAIN --> W5
    
    R1 --> W1
    R2 --> W2
    R3 --> W3
    R4 --> W4
    R5 --> W5
    R6 --> W1
    R7 --> W2
    R8 --> W3
    
    W1 --> RESULTS
    W2 --> RESULTS
    W3 --> RESULTS
    W4 --> RESULTS
    W5 --> RESULTS
    
    RESULTS --> MAIN
    
    style MAIN fill:#4CAF50,color:#fff
    style RESULTS fill:#2196F3,color:#fff
```
