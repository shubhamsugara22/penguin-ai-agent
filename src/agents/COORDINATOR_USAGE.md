# Coordinator Agent Usage Guide

## Overview

The Coordinator Agent is the main orchestration component of the GitHub Maintainer system. It manages the complete workflow for analyzing repositories, generating maintenance suggestions, and creating GitHub issues.

## Architecture

The Coordinator Agent implements a sequential workflow with the following stages:

1. **Initialize Session** - Create a new analysis session
2. **Fetch Repositories** - Retrieve repositories for the specified user
3. **Analyze Repositories** - Analyze each repository in parallel using the Analyzer Agent
4. **Generate Suggestions** - Create maintenance suggestions using the Maintainer Agent
5. **Request Approvals** - Get user approval for suggestions (manual/auto/ask)
6. **Create Issues** - Create GitHub issues for approved suggestions
7. **Finalize Session** - Calculate metrics and complete the session

## Basic Usage

```python
from src.agents import CoordinatorAgent
from src.tools.github_tools import RepositoryFilters
from src.models.session import UserPreferences
from datetime import datetime, timedelta

# Create coordinator
coordinator = CoordinatorAgent()

# Define filters (optional)
filters = RepositoryFilters(
    updated_after=datetime.now() - timedelta(days=365),
    archived=False
)

# Define user preferences (optional)
preferences = UserPreferences(
    user_id="username",
    automation_level="manual",  # auto, manual, or ask
    focus_areas=["tests", "documentation", "ci-cd"]
)

# Run analysis
result = coordinator.analyze_repositories(
    username="octocat",
    filters=filters,
    user_preferences=preferences
)

# Access results
print(f"Analyzed {len(result.repositories_analyzed)} repositories")
print(f"Generated {len(result.suggestions)} suggestions")
print(f"Created {len(result.issues_created)} issues")
```

## Progress Tracking

You can track workflow progress by providing a progress callback:

```python
from src.agents import ProgressEvent

def progress_callback(event: ProgressEvent):
    """Handle progress updates."""
    if event.total > 0:
        print(f"[{event.stage}] {event.message} ({event.current}/{event.total})")
    else:
        print(f"[{event.stage}] {event.message}")

result = coordinator.analyze_repositories(
    username="octocat",
    progress_callback=progress_callback
)
```

Progress stages include:
- `initialization` - Session setup
- `fetching` - Fetching repositories
- `analyzing` - Analyzing repositories
- `generating_suggestions` - Creating suggestions
- `requesting_approvals` - Waiting for approvals
- `creating_issues` - Creating GitHub issues
- `finalizing` - Completing session
- `complete` - Workflow finished

## User Approval

Control how suggestions are approved using the `automation_level` preference:

### Auto Mode
```python
preferences = UserPreferences(
    user_id="username",
    automation_level="auto"  # Auto-approve all suggestions
)
```

### Manual Mode with Callback
```python
def approval_callback(suggestions):
    """Custom approval logic."""
    approved = []
    for suggestion in suggestions:
        if suggestion.priority == "high":
            approved.append(suggestion)
    return approved

result = coordinator.analyze_repositories(
    username="octocat",
    user_preferences=preferences,
    approval_callback=approval_callback
)
```

### Interactive Approval
```python
def interactive_approval(suggestions):
    """Interactive approval prompt."""
    approved = []
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n{i}. {suggestion.title}")
        print(f"   Priority: {suggestion.priority}")
        print(f"   Description: {suggestion.description[:100]}...")
        
        response = input("Approve? (y/n): ")
        if response.lower() == 'y':
            approved.append(suggestion)
    
    return approved
```

## Session Management

Access session state during or after analysis:

```python
# Get current session
session = coordinator.get_session_state()

print(f"Session ID: {session.session_id}")
print(f"Repositories: {session.repositories_analyzed}")
print(f"Metrics: {session.metrics.to_dict()}")

# Get specific session by ID
session = coordinator.get_session_state(session_id="abc123")
```

## Error Handling

The Coordinator Agent handles errors gracefully and continues processing:

```python
result = coordinator.analyze_repositories(username="octocat")

# Check for errors
if result.errors:
    print("Errors encountered:")
    for repo, error in result.errors:
        print(f"  - {repo}: {error}")

# Check metrics
print(f"Errors: {result.metrics.errors_encountered}")
```

## Analysis Results

The `AnalysisResult` object contains:

```python
result = coordinator.analyze_repositories(username="octocat")

# Session information
print(f"Session ID: {result.session_id}")
print(f"Username: {result.username}")

# Repositories
print(f"Repositories analyzed: {len(result.repositories_analyzed)}")
for repo in result.repositories_analyzed:
    print(f"  - {repo}")

# Suggestions
print(f"Suggestions generated: {len(result.suggestions)}")
for suggestion in result.suggestions:
    print(f"  - [{suggestion.priority}] {suggestion.title}")

# Issues
print(f"Issues created: {len(result.issues_created)}")
for issue in result.issues_created:
    if issue.success:
        print(f"  ✓ {issue.issue_url}")
    else:
        print(f"  ✗ Failed: {issue.error_message}")

# Metrics
print(f"\nMetrics:")
print(f"  Execution time: {result.metrics.execution_time_seconds:.2f}s")
print(f"  API calls: {result.metrics.api_calls_made}")
print(f"  Tokens used: {result.metrics.tokens_used}")
print(f"  Errors: {result.metrics.errors_encountered}")

# Convert to dictionary
result_dict = result.to_dict()
```

## Workflow Customization

The Coordinator Agent uses dependency injection for flexibility:

```python
from src.memory import SessionService, MemoryBank
from src.tools import GitHubClient
from src.agents import AnalyzerAgent, MaintainerAgent

# Create custom components
session_service = SessionService()
memory_bank = MemoryBank(storage_dir="./custom_memory")
github_client = GitHubClient()
analyzer = AnalyzerAgent(github_client)
maintainer = MaintainerAgent(memory_bank, github_client)

# Create coordinator with custom components
coordinator = CoordinatorAgent(
    session_service=session_service,
    memory_bank=memory_bank,
    github_client=github_client,
    analyzer_agent=analyzer,
    maintainer_agent=maintainer
)
```

## Complete Example

```python
from src.agents import CoordinatorAgent, ProgressEvent
from src.tools.github_tools import RepositoryFilters
from src.models.session import UserPreferences
from datetime import datetime, timedelta

def main():
    # Setup
    username = "octocat"
    
    # Progress callback
    def progress_callback(event: ProgressEvent):
        print(f"[{event.stage}] {event.message}")
    
    # Approval callback
    def approval_callback(suggestions):
        print(f"\nReceived {len(suggestions)} suggestions")
        # Auto-approve high priority
        approved = [s for s in suggestions if s.priority == "high"]
        print(f"Approved {len(approved)} high-priority suggestions")
        return approved
    
    # Filters
    filters = RepositoryFilters(
        updated_after=datetime.now() - timedelta(days=365),
        archived=False
    )
    
    # Preferences
    preferences = UserPreferences(
        user_id=username,
        automation_level="manual",
        focus_areas=["tests", "documentation"]
    )
    
    # Create coordinator and run analysis
    coordinator = CoordinatorAgent()
    
    result = coordinator.analyze_repositories(
        username=username,
        filters=filters,
        user_preferences=preferences,
        progress_callback=progress_callback,
        approval_callback=approval_callback
    )
    
    # Display results
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print(f"Repositories: {len(result.repositories_analyzed)}")
    print(f"Suggestions: {len(result.suggestions)}")
    print(f"Issues Created: {len([i for i in result.issues_created if i.success])}")
    print(f"Execution Time: {result.metrics.execution_time_seconds:.2f}s")
    
    if result.errors:
        print(f"\nErrors: {len(result.errors)}")
        for repo, error in result.errors:
            print(f"  - {repo}: {error}")

if __name__ == "__main__":
    main()
```

## Requirements

The Coordinator Agent requires:
- Valid `GITHUB_TOKEN` environment variable
- Valid `GEMINI_API_KEY` or `GOOGLE_API_KEY` environment variable
- Network access to GitHub API and Google AI Studio

## Workflow Sequencing

The workflow follows this sequence (as specified in Requirements 10.1-10.5):

1. **Coordinator receives request** → Creates session (Req 10.1)
2. **Coordinator delegates to Analyzer** → Passes repository info (Req 10.2)
3. **Analyzer completes** → Returns health snapshots (Req 10.3)
4. **Coordinator delegates to Maintainer** → Passes analysis results (Req 10.3)
5. **Maintainer generates suggestions** → Returns maintenance tasks (Req 10.4)
6. **Coordinator presents to user** → Requests approvals (Req 10.4)
7. **User approves** → Coordinator instructs Maintainer to create issues (Req 10.5)

## Parallel Processing

The Coordinator Agent leverages parallel processing for repository analysis:

```python
# Analyzer Agent processes multiple repositories in parallel
# Default: 5 parallel workers (configurable via MAX_PARALLEL_REPOS env var)

# The coordinator automatically uses parallel processing
result = coordinator.analyze_repositories(username="octocat")
# Repositories are analyzed concurrently for better performance
```

## Observability

The Coordinator Agent emits structured logs and tracks metrics:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Run analysis
result = coordinator.analyze_repositories(username="octocat")

# Access metrics
print(f"Repos analyzed: {result.metrics.repos_analyzed}")
print(f"Suggestions generated: {result.metrics.suggestions_generated}")
print(f"Issues created: {result.metrics.issues_created}")
print(f"API calls: {result.metrics.api_calls_made}")
print(f"Tokens used: {result.metrics.tokens_used}")
print(f"Execution time: {result.metrics.execution_time_seconds}s")
print(f"Errors: {result.metrics.errors_encountered}")
```

## Testing

See `verify_coordinator.py` for verification tests and `examples/coordinator_demo.py` for a complete demo.
