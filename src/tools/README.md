# GitHub API Tools

This module provides tools for interacting with the GitHub API, including repository analysis and issue management.

## Components

### GitHubClient

The `GitHubClient` class provides a robust wrapper around the GitHub REST API with:

- **Authentication**: Secure token-based authentication
- **Rate Limiting**: Automatic detection and tracking of rate limits
- **Error Handling**: Comprehensive error handling with retries
- **Pagination**: Support for paginated API responses

### Tools

#### list_repos(username, filters=None, client=None)

Fetch all repositories for a GitHub user with optional filtering.

**Parameters:**
- `username` (str): GitHub username
- `filters` (RepositoryFilters, optional): Filters to apply
- `client` (GitHubClient, optional): GitHub client instance

**Returns:** List of `Repository` objects

**Example:**
```python
from src.tools import list_repos, RepositoryFilters
from datetime import datetime, timedelta

# List all repos
repos = list_repos("octocat")

# List with filters
filters = RepositoryFilters(
    updated_after=datetime.now() - timedelta(days=365),
    language="Python",
    visibility="public"
)
filtered_repos = list_repos("octocat", filters=filters)
```

#### get_repo_overview(repo_full_name, client=None)

Fetch detailed repository metadata and content overview.

**Parameters:**
- `repo_full_name` (str): Full repository name (owner/repo)
- `client` (GitHubClient, optional): GitHub client instance

**Returns:** `RepositoryOverview` object

**Example:**
```python
from src.tools import get_repo_overview

overview = get_repo_overview("octocat/Hello-World")
print(f"Languages: {overview.languages}")
print(f"Has tests: {overview.has_tests}")
print(f"Has CI/CD: {overview.has_ci_config}")
```

#### get_repo_history(repo_full_name, limit=100, client=None)

Fetch repository activity and history data.

**Parameters:**
- `repo_full_name` (str): Full repository name (owner/repo)
- `limit` (int): Maximum number of recent commits to fetch
- `client` (GitHubClient, optional): GitHub client instance

**Returns:** `RepositoryHistory` object

**Example:**
```python
from src.tools import get_repo_history

history = get_repo_history("octocat/Hello-World", limit=10)
print(f"Total commits: {history.commit_count}")
print(f"Open issues: {history.open_issues_count}")
print(f"Contributors: {history.contributors_count}")
```

#### create_issue(repo_full_name, title, body, labels, client=None)

Create a GitHub issue in the specified repository.

**Parameters:**
- `repo_full_name` (str): Full repository name (owner/repo)
- `title` (str): Issue title
- `body` (str): Issue description
- `labels` (List[str]): List of label names
- `client` (GitHubClient, optional): GitHub client instance

**Returns:** `IssueResult` object

**Example:**
```python
from src.tools import create_issue

result = create_issue(
    repo_full_name="owner/repo",
    title="Add documentation",
    body="We need to document the new feature...",
    labels=["documentation", "enhancement"]
)

if result.success:
    print(f"Issue created: {result.issue_url}")
else:
    print(f"Failed: {result.error_message}")
```

## Error Handling

The tools provide specific exceptions for different error scenarios:

- `AuthenticationError`: GitHub authentication failed
- `RateLimitError`: API rate limit exceeded (includes reset time)
- `RepositoryNotFoundError`: Repository doesn't exist
- `GitHubAPIError`: General API error

**Example:**
```python
from src.tools import list_repos, AuthenticationError, RateLimitError

try:
    repos = list_repos("octocat")
except AuthenticationError as e:
    print(f"Auth failed: {e}")
    print("Check your GITHUB_TOKEN")
except RateLimitError as e:
    print(f"Rate limit exceeded. Resets at: {e.reset_time}")
```

## Configuration

The tools use configuration from environment variables:

- `GITHUB_TOKEN`: GitHub personal access token (required)
- `GITHUB_API_BASE_URL`: API base URL (optional, defaults to https://api.github.com)

Set these in your `.env` file or environment.

## Rate Limiting

The client automatically tracks rate limit status:

```python
from src.tools import GitHubClient

client = GitHubClient()
client.get('/user')  # Make a request

status = client.get_rate_limit_status()
print(f"Remaining: {status['remaining']}")
print(f"Resets at: {status['reset_time']}")
```

## Retry Logic

All API requests include automatic retry logic:

- **Max retries**: 3 attempts
- **Backoff**: Exponential (1s, 2s, 4s)
- **Retryable errors**: Network errors, timeouts, server errors (5xx)
- **Non-retryable**: Authentication errors, not found errors

## Demo

See `examples/github_tools_demo.py` for a comprehensive demonstration of all features.

Run the demo:
```bash
cd penguin-ai-agent
python examples/github_tools_demo.py
```

## Testing

The tools are designed to work with the existing test suite. See `tests/` directory for unit tests.
