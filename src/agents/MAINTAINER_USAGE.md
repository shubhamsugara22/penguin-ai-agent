# Maintainer Agent Usage Guide

## Overview

The Maintainer Agent converts repository health assessments into actionable maintenance suggestions and creates GitHub issues. It uses LLM reasoning for intelligent suggestions and includes fallback rule-based generation.

## Quick Start

```python
from src.agents.maintainer import MaintainerAgent
from src.memory.memory_bank import MemoryBank
from src.models.session import UserPreferences

# Initialize
memory_bank = MemoryBank()
maintainer = MaintainerAgent(memory_bank=memory_bank)

# Create user preferences
preferences = UserPreferences(
    user_id="your-username",
    automation_level="manual",  # auto, manual, or ask
    preferred_labels=["maintenance", "ai-generated"],
    excluded_repos=["username/archived-repo"],
    focus_areas=["tests", "docs", "security"]
)

# Generate suggestions (profiles come from Analyzer Agent)
suggestions = maintainer.generate_suggestions(profiles, preferences)

# Create GitHub issues
for suggestion in suggestions:
    result = maintainer.create_github_issue(suggestion, preferences)
    if result.success:
        print(f"Created: {result.issue_url}")
```

## API Reference

### MaintainerAgent

#### `__init__(memory_bank=None, github_client=None)`

Initialize the Maintainer Agent.

**Parameters:**
- `memory_bank` (MemoryBank, optional): Memory bank for deduplication
- `github_client` (GitHubClient, optional): GitHub API client

**Example:**
```python
from src.memory.memory_bank import MemoryBank
from src.tools.github_client import GitHubClient

memory = MemoryBank(storage_dir=".my_memory")
client = GitHubClient()
agent = MaintainerAgent(memory_bank=memory, github_client=client)
```

#### `generate_suggestions(profiles, user_preferences=None)`

Generate maintenance suggestions from repository profiles.

**Parameters:**
- `profiles` (List[RepositoryProfile]): Repository profiles to analyze
- `user_preferences` (UserPreferences, optional): User preferences for filtering

**Returns:**
- `List[MaintenanceSuggestion]`: Prioritized list of suggestions

**Example:**
```python
suggestions = agent.generate_suggestions(
    profiles=[profile1, profile2],
    user_preferences=preferences
)

for suggestion in suggestions:
    print(f"{suggestion.title} ({suggestion.priority})")
```

#### `prioritize_suggestions(suggestions)`

Prioritize suggestions by impact and effort.

**Parameters:**
- `suggestions` (List[MaintenanceSuggestion]): Suggestions to prioritize

**Returns:**
- `List[MaintenanceSuggestion]`: Sorted suggestions (highest priority first)

**Scoring Formula:**
```
score = (priority * 2 + category) / effort

Where:
- priority: high=3, medium=2, low=1
- category: security=5, bug=4, enhancement=3, documentation=2, refactor=1
- effort: small=3, medium=2, large=1
```

**Example:**
```python
prioritized = agent.prioritize_suggestions(suggestions)
print(f"Top priority: {prioritized[0].title}")
```

#### `create_github_issue(suggestion, user_preferences=None)`

Create a GitHub issue from a maintenance suggestion.

**Parameters:**
- `suggestion` (MaintenanceSuggestion): Suggestion to create issue for
- `user_preferences` (UserPreferences, optional): User preferences for labels

**Returns:**
- `IssueResult`: Result with success status and issue URL

**Example:**
```python
result = agent.create_github_issue(suggestion, preferences)

if result.success:
    print(f"Issue #{result.issue_number}: {result.issue_url}")
else:
    print(f"Failed: {result.error_message}")
```

## Data Models

### MaintenanceSuggestion

```python
@dataclass
class MaintenanceSuggestion:
    id: str                      # Unique identifier
    repository: Repository       # Target repository
    category: str               # bug, enhancement, documentation, refactor, security
    priority: str               # high, medium, low
    title: str                  # Concise, actionable title
    description: str            # Detailed description
    rationale: str              # Why this is important
    estimated_effort: str       # small, medium, large
    labels: List[str]           # GitHub labels
```

### UserPreferences

```python
@dataclass
class UserPreferences:
    user_id: str                    # User identifier
    automation_level: str           # auto, manual, ask
    preferred_labels: List[str]     # Labels to add to all issues
    excluded_repos: List[str]       # Repos to skip
    focus_areas: List[str]          # Priority areas (tests, docs, security, etc.)
```

### IssueResult

```python
@dataclass
class IssueResult:
    success: bool           # Whether issue was created
    issue_url: str         # URL of created issue
    issue_number: int      # Issue number
    error_message: str     # Error message if failed
```

## User Preferences

### Automation Levels

- **`auto`**: Automatically create issues without asking
- **`manual`**: Never create issues automatically (user must approve each)
- **`ask`**: Ask for approval before creating each issue

### Focus Areas

Common focus areas:
- `tests`: Testing and test coverage
- `docs`: Documentation improvements
- `security`: Security vulnerabilities and best practices
- `ci-cd`: CI/CD pipeline setup and improvements
- `dependencies`: Dependency updates and management
- `performance`: Performance optimizations
- `refactor`: Code refactoring and cleanup

### Preferred Labels

Labels to add to all created issues:
```python
preferred_labels = [
    "maintenance",
    "ai-generated",
    "good-first-issue",
    "help-wanted"
]
```

## Suggestion Categories

### bug
Critical issues that need fixing:
- Security vulnerabilities
- Broken functionality
- Error handling issues

### enhancement
Improvements to existing features:
- Add missing tests
- Set up CI/CD
- Improve error messages

### documentation
Documentation improvements:
- Add README
- Improve API docs
- Add code comments

### refactor
Code quality improvements:
- Remove code duplication
- Improve code structure
- Update deprecated APIs

### security
Security-related tasks:
- Fix vulnerabilities
- Update dependencies
- Add security scanning

## Deduplication

The agent automatically deduplicates suggestions:

1. **Within-Session**: Prevents duplicates in the same run
2. **Cross-Session**: Checks memory bank for previous suggestions

Deduplication is based on:
- Repository full name
- Suggestion title (case-insensitive)

To clear suggestion history:
```python
memory_bank.delete_suggestions("username/repo")
```

## Error Handling

The agent handles errors gracefully:

### LLM Failures
If LLM generation fails, the agent falls back to rule-based suggestions:
```python
# Automatic fallback - no action needed
suggestions = agent.generate_suggestions(profiles)
```

### GitHub API Errors
Issue creation failures are returned in the result:
```python
result = agent.create_github_issue(suggestion)
if not result.success:
    print(f"Error: {result.error_message}")
    # Handle error (retry, log, notify user, etc.)
```

### Memory Bank Errors
Memory operations are non-critical and logged:
```python
# Agent continues even if memory operations fail
# Check logs for warnings
```

## Best Practices

### 1. Use User Preferences
Always provide user preferences for better results:
```python
preferences = UserPreferences(
    user_id=username,
    automation_level="manual",
    focus_areas=["tests", "security"]
)
suggestions = agent.generate_suggestions(profiles, preferences)
```

### 2. Review Before Creating Issues
Review suggestions before creating issues:
```python
for suggestion in suggestions:
    print(f"\n{suggestion.title}")
    print(f"Priority: {suggestion.priority}")
    print(f"Description: {suggestion.description}")
    
    if input("Create issue? (y/n): ").lower() == 'y':
        agent.create_github_issue(suggestion, preferences)
```

### 3. Handle Excluded Repositories
Exclude archived or inactive repositories:
```python
preferences.excluded_repos = [
    "username/archived-repo",
    "username/deprecated-project"
]
```

### 4. Customize Labels
Use consistent labels across your organization:
```python
preferences.preferred_labels = [
    "maintenance",
    "automated",
    "needs-review"
]
```

### 5. Monitor Memory Bank
Periodically review stored suggestions:
```python
existing = memory_bank.load_suggestions("username/repo")
print(f"Found {len(existing)} previous suggestions")
```

## Integration Examples

### With Analyzer Agent

```python
from src.agents.analyzer import AnalyzerAgent
from src.agents.maintainer import MaintainerAgent

# Analyze repositories
analyzer = AnalyzerAgent()
analyses = analyzer.analyze_repositories_parallel(repos)

# Generate suggestions
maintainer = MaintainerAgent()
profiles = [a.profile for a in analyses]
suggestions = maintainer.generate_suggestions(profiles, preferences)
```

### With CLI

```python
# Display suggestions
for i, suggestion in enumerate(suggestions, 1):
    print(f"\n{i}. {suggestion.title}")
    print(f"   Repository: {suggestion.repository.full_name}")
    print(f"   Priority: {suggestion.priority}")
    print(f"   Effort: {suggestion.estimated_effort}")

# Get user approval
approved = []
for suggestion in suggestions:
    if input(f"\nApprove '{suggestion.title}'? (y/n): ").lower() == 'y':
        approved.append(suggestion)

# Create issues
for suggestion in approved:
    result = maintainer.create_github_issue(suggestion, preferences)
    print(f"Created: {result.issue_url}")
```

## Troubleshooting

### No Suggestions Generated

**Cause**: Repositories are healthy or excluded

**Solution**:
```python
# Check health scores
for profile in profiles:
    print(f"{profile.repository.full_name}: {profile.health.overall_health_score}")

# Check exclusions
print(f"Excluded: {preferences.excluded_repos}")
```

### Duplicate Suggestions

**Cause**: Memory bank not being used

**Solution**:
```python
# Ensure memory bank is passed to agent
memory_bank = MemoryBank()
agent = MaintainerAgent(memory_bank=memory_bank)
```

### Issue Creation Fails

**Cause**: Invalid GitHub token or permissions

**Solution**:
```python
# Check token permissions
# Token needs: repo (full control)
# See: https://docs.github.com/en/authentication

# Verify token
from src.tools.github_client import GitHubClient
client = GitHubClient()
user = client.get('/user')
print(f"Authenticated as: {user['login']}")
```

### LLM Errors

**Cause**: Invalid API key or rate limits

**Solution**:
```python
# Agent automatically falls back to rule-based suggestions
# Check logs for LLM errors
import logging
logging.basicConfig(level=logging.INFO)

# Verify API key
from src.config import get_config
config = get_config()
print(f"Gemini API key: {config.gemini_api_key[:10]}...")
```

## Advanced Usage

### Custom Prioritization

```python
# Override prioritization logic
def custom_prioritize(suggestions):
    # Your custom logic here
    return sorted(suggestions, key=lambda s: my_score(s), reverse=True)

suggestions = agent.generate_suggestions(profiles)
prioritized = custom_prioritize(suggestions)
```

### Batch Issue Creation

```python
# Create issues in batch with error handling
results = []
for suggestion in suggestions:
    try:
        result = agent.create_github_issue(suggestion, preferences)
        results.append(result)
    except Exception as e:
        print(f"Error creating issue: {e}")
        continue

# Summary
successful = sum(1 for r in results if r.success)
print(f"Created {successful}/{len(suggestions)} issues")
```

### Custom Memory Backend

```python
# Use custom storage directory
memory_bank = MemoryBank(storage_dir="/path/to/memory")
agent = MaintainerAgent(memory_bank=memory_bank)
```

## See Also

- [Analyzer Agent Usage](./ANALYZER_USAGE.md)
- [GitHub Tools Documentation](../tools/README.md)
- [Memory Bank Documentation](../memory/README.md)
- [Design Document](../../.kiro/specs/github-maintainer-agent/design.md)
