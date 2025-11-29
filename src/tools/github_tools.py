"""GitHub API tools for repository analysis and issue management."""

import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import re

from .github_client import GitHubClient, RepositoryNotFoundError, GitHubAPIError
from ..models.repository import Repository, RepositoryOverview, RepositoryHistory, CommitSummary
from ..models.maintenance import IssueResult
from ..observability import get_metrics_collector

logger = logging.getLogger(__name__)


class RepositoryFilters:
    """Filters for repository listing."""
    
    def __init__(
        self,
        updated_after: Optional[str] = None,
        language: Optional[str] = None,
        visibility: Optional[str] = None,
        archived: bool = False
    ):
        """Initialize repository filters.
        
        Args:
            updated_after: Only include repos updated after this date (YYYY-MM-DD string or datetime)
            language: Filter by primary language
            visibility: Filter by visibility (public, private, all)
            archived: Include archived repositories
        """
        # Convert string date to datetime if needed
        if isinstance(updated_after, str):
            try:
                # Parse date and make it timezone-aware (UTC) to match GitHub API dates
                naive_dt = datetime.fromisoformat(updated_after)
                # If no timezone info, assume UTC
                if naive_dt.tzinfo is None:
                    self.updated_after = naive_dt.replace(tzinfo=timezone.utc)
                else:
                    self.updated_after = naive_dt
            except (ValueError, TypeError):
                logger.warning(f"Invalid date format for updated_after: {updated_after}")
                self.updated_after = None
        elif isinstance(updated_after, datetime):
            # Make sure datetime is timezone-aware
            if updated_after.tzinfo is None:
                self.updated_after = updated_after.replace(tzinfo=timezone.utc)
            else:
                self.updated_after = updated_after
        else:
            self.updated_after = updated_after
            
        self.language = language
        self.visibility = visibility
        self.archived = archived


def list_repos(
    username: str,
    filters: Optional[RepositoryFilters] = None,
    client: Optional[GitHubClient] = None
) -> List[Repository]:
    """Fetch all repositories for a GitHub user.
    
    Args:
        username: GitHub username
        filters: Optional filters to apply
        client: Optional GitHub client (creates new one if not provided)
        
    Returns:
        List of Repository objects
        
    Raises:
        GitHubAPIError: If API request fails
    """
    if client is None:
        client = GitHubClient()
    
    metrics = get_metrics_collector()
    start_time = time.time()
    
    logger.info(
        f"Fetching repositories for user: {username}",
        extra={
            'event': 'list_repos_start',
            'extra_data': {'username': username, 'has_filters': filters is not None}
        }
    )
    
    try:
        # Fetch repositories
        params: Dict[str, Any] = {
            'type': 'all',
            'sort': 'updated',
            'direction': 'desc'
        }
        
        repos_data = client.get_paginated(f'/users/{username}/repos', params=params)
        
        # Record API call
        duration_ms = (time.time() - start_time) * 1000
        metrics.record_api_call('github', 'list_repos', duration_ms, success=True)
        
        # Convert to Repository objects
        repositories = []
        for repo_data in repos_data:
            try:
                repo = _parse_repository(repo_data)
                
                # Apply filters
                if filters and not _matches_filters(repo, repo_data, filters):
                    continue
                
                repositories.append(repo)
            except Exception as e:
                logger.warning(f"Failed to parse repository {repo_data.get('full_name')}: {e}")
                continue
        
        logger.info(
            f"Found {len(repositories)} repositories for {username}",
            extra={
                'event': 'list_repos_complete',
                'extra_data': {
                    'username': username,
                    'repo_count': len(repositories),
                    'duration_ms': duration_ms
                }
            }
        )
        return repositories
        
    except GitHubAPIError as e:
        duration_ms = (time.time() - start_time) * 1000
        metrics.record_api_call('github', 'list_repos', duration_ms, success=False, error=str(e))
        metrics.record_error('github_api_error')
        
        logger.error(
            f"Failed to fetch repositories for {username}: {e}",
            extra={
                'event': 'list_repos_error',
                'extra_data': {'username': username, 'error': str(e)}
            }
        )
        raise


def get_repo_overview(
    repo_full_name: str,
    client: Optional[GitHubClient] = None
) -> RepositoryOverview:
    """Fetch repository metadata and content overview.
    
    Args:
        repo_full_name: Full repository name (owner/repo)
        client: Optional GitHub client
        
    Returns:
        RepositoryOverview object
        
    Raises:
        RepositoryNotFoundError: If repository doesn't exist
        GitHubAPIError: If API request fails
    """
    if client is None:
        client = GitHubClient()
    
    metrics = get_metrics_collector()
    start_time = time.time()
    
    logger.info(
        f"Fetching overview for repository: {repo_full_name}",
        extra={'event': 'get_repo_overview_start', 'repository': repo_full_name}
    )
    
    try:
        # Fetch basic repository info
        repo_data = client.get(f'/repos/{repo_full_name}')
        repository = _parse_repository(repo_data)
        
        # Fetch README
        readme_content = _fetch_readme(repo_full_name, client)
        
        # Fetch file structure (top-level only)
        file_structure = _fetch_file_structure(repo_full_name, client)
        
        # Get language statistics
        languages = client.get(f'/repos/{repo_full_name}/languages')
        
        # Detect CI/CD configuration
        has_ci_config = _detect_ci_config(file_structure)
        
        # Detect tests
        has_tests = _detect_tests(file_structure)
        
        # Detect CONTRIBUTING file
        has_contributing = _detect_contributing(file_structure)
        
        overview = RepositoryOverview(
            repository=repository,
            readme_content=readme_content,
            file_structure=file_structure,
            languages=languages,
            has_ci_config=has_ci_config,
            has_tests=has_tests,
            has_contributing=has_contributing
        )
        
        duration_ms = (time.time() - start_time) * 1000
        metrics.record_api_call('github', 'get_repo_overview', duration_ms, success=True)
        
        logger.info(
            f"Successfully fetched overview for {repo_full_name}",
            extra={
                'event': 'get_repo_overview_complete',
                'repository': repo_full_name,
                'extra_data': {
                    'has_readme': readme_content is not None,
                    'has_tests': has_tests,
                    'has_ci': has_ci_config,
                    'duration_ms': duration_ms
                }
            }
        )
        return overview
        
    except RepositoryNotFoundError:
        duration_ms = (time.time() - start_time) * 1000
        metrics.record_api_call('github', 'get_repo_overview', duration_ms, success=False, error='not_found')
        metrics.record_error('repository_not_found')
        
        logger.error(
            f"Repository not found: {repo_full_name}",
            extra={'event': 'get_repo_overview_error', 'repository': repo_full_name}
        )
        raise
    except GitHubAPIError as e:
        duration_ms = (time.time() - start_time) * 1000
        metrics.record_api_call('github', 'get_repo_overview', duration_ms, success=False, error=str(e))
        metrics.record_error('github_api_error')
        
        logger.error(
            f"Failed to fetch overview for {repo_full_name}: {e}",
            extra={'event': 'get_repo_overview_error', 'repository': repo_full_name, 'extra_data': {'error': str(e)}}
        )
        raise


def get_repo_history(
    repo_full_name: str,
    limit: int = 100,
    client: Optional[GitHubClient] = None
) -> RepositoryHistory:
    """Fetch repository activity and history data.
    
    Args:
        repo_full_name: Full repository name (owner/repo)
        limit: Maximum number of recent commits to fetch
        client: Optional GitHub client
        
    Returns:
        RepositoryHistory object
        
    Raises:
        RepositoryNotFoundError: If repository doesn't exist
        GitHubAPIError: If API request fails
    """
    if client is None:
        client = GitHubClient()
    
    logger.info(f"Fetching history for repository: {repo_full_name}")
    
    try:
        # Fetch commits
        commits_data = client.get_paginated(
            f'/repos/{repo_full_name}/commits',
            params={'per_page': min(limit, 100)},
            max_pages=1
        )
        
        recent_commits = []
        for commit_data in commits_data[:limit]:
            try:
                commit = _parse_commit(commit_data)
                recent_commits.append(commit)
            except Exception as e:
                logger.warning(f"Failed to parse commit: {e}")
                continue
        
        # Get total commit count (approximate from first commit)
        commit_count = len(commits_data)
        last_commit_date = recent_commits[0].date if recent_commits else datetime.now()
        
        # Fetch issues statistics
        issues_data = client.get(f'/repos/{repo_full_name}/issues', params={'state': 'all', 'per_page': 1})
        open_issues = client.get(f'/repos/{repo_full_name}/issues', params={'state': 'open', 'per_page': 1})
        
        # Get issue counts from repository data
        repo_data = client.get(f'/repos/{repo_full_name}')
        open_issues_count = repo_data.get('open_issues_count', 0)
        
        # Fetch pull requests statistics
        prs_data = client.get(f'/repos/{repo_full_name}/pulls', params={'state': 'all', 'per_page': 1})
        open_prs = client.get(f'/repos/{repo_full_name}/pulls', params={'state': 'open', 'per_page': 1})
        open_prs_count = len(open_prs) if isinstance(open_prs, list) else 0
        
        # Fetch contributors
        contributors_data = client.get_paginated(
            f'/repos/{repo_full_name}/contributors',
            params={'per_page': 100},
            max_pages=1
        )
        contributors_count = len(contributors_data)
        
        # Note: We can't easily get closed issues count without pagination
        # Using a heuristic: assume some issues are closed
        closed_issues_count = max(0, open_issues_count // 2)
        merged_prs_count = max(0, len(contributors_data) * 2)
        
        history = RepositoryHistory(
            commit_count=commit_count,
            last_commit_date=last_commit_date,
            recent_commits=recent_commits,
            open_issues_count=open_issues_count,
            closed_issues_count=closed_issues_count,
            open_prs_count=open_prs_count,
            merged_prs_count=merged_prs_count,
            contributors_count=contributors_count
        )
        
        logger.info(f"Successfully fetched history for {repo_full_name}")
        return history
        
    except RepositoryNotFoundError:
        logger.error(f"Repository not found: {repo_full_name}")
        raise
    except GitHubAPIError as e:
        logger.error(f"Failed to fetch history for {repo_full_name}: {e}")
        raise


def create_issue(
    repo_full_name: str,
    title: str,
    body: str,
    labels: List[str],
    client: Optional[GitHubClient] = None
) -> IssueResult:
    """Create a GitHub issue in the specified repository.
    
    Args:
        repo_full_name: Full repository name (owner/repo)
        title: Issue title
        body: Issue description
        labels: List of label names
        client: Optional GitHub client
        
    Returns:
        IssueResult object with creation status
    """
    if client is None:
        client = GitHubClient()
    
    metrics = get_metrics_collector()
    start_time = time.time()
    
    logger.info(
        f"Creating issue in {repo_full_name}: {title}",
        extra={
            'event': 'create_issue_start',
            'repository': repo_full_name,
            'extra_data': {'title': title, 'labels': labels}
        }
    )
    
    try:
        issue_data = {
            'title': title,
            'body': body,
            'labels': labels
        }
        
        response = client.post(f'/repos/{repo_full_name}/issues', json_data=issue_data)
        
        issue_url = response.get('html_url', '')
        issue_number = response.get('number', 0)
        
        result = IssueResult(
            success=True,
            issue_url=issue_url,
            issue_number=issue_number
        )
        
        duration_ms = (time.time() - start_time) * 1000
        metrics.record_api_call('github', 'create_issue', duration_ms, success=True)
        metrics.record_issue_created()
        
        logger.info(
            f"Successfully created issue #{issue_number} in {repo_full_name}",
            extra={
                'event': 'create_issue_complete',
                'repository': repo_full_name,
                'extra_data': {
                    'issue_number': issue_number,
                    'issue_url': issue_url,
                    'duration_ms': duration_ms
                }
            }
        )
        return result
        
    except GitHubAPIError as e:
        duration_ms = (time.time() - start_time) * 1000
        metrics.record_api_call('github', 'create_issue', duration_ms, success=False, error=str(e))
        metrics.record_error('github_api_error')
        
        logger.error(
            f"Failed to create issue in {repo_full_name}: {e}",
            extra={
                'event': 'create_issue_error',
                'repository': repo_full_name,
                'extra_data': {'title': title, 'error': str(e)}
            }
        )
        return IssueResult(
            success=False,
            issue_url='',
            issue_number=0,
            error_message=str(e)
        )


# Helper functions

def _parse_repository(repo_data: Dict[str, Any]) -> Repository:
    """Parse repository data from GitHub API response.
    
    Args:
        repo_data: Raw repository data from API
        
    Returns:
        Repository object
    """
    return Repository(
        name=repo_data['name'],
        full_name=repo_data['full_name'],
        owner=repo_data['owner']['login'],
        url=repo_data['html_url'],
        default_branch=repo_data.get('default_branch', 'main'),
        visibility='public' if not repo_data.get('private', False) else 'private',
        created_at=datetime.fromisoformat(repo_data['created_at'].replace('Z', '+00:00')),
        updated_at=datetime.fromisoformat(repo_data['updated_at'].replace('Z', '+00:00'))
    )


def _parse_commit(commit_data: Dict[str, Any]) -> CommitSummary:
    """Parse commit data from GitHub API response.
    
    Args:
        commit_data: Raw commit data from API
        
    Returns:
        CommitSummary object
    """
    commit_info = commit_data['commit']
    author_info = commit_info['author']
    
    return CommitSummary(
        sha=commit_data['sha'],
        message=commit_info['message'].split('\n')[0],  # First line only
        author=author_info['name'],
        date=datetime.fromisoformat(author_info['date'].replace('Z', '+00:00'))
    )


def _matches_filters(
    repo: Repository,
    repo_data: Dict[str, Any],
    filters: RepositoryFilters
) -> bool:
    """Check if repository matches the given filters.
    
    Args:
        repo: Repository object
        repo_data: Raw repository data
        filters: Filters to apply
        
    Returns:
        True if repository matches all filters
    """
    # Check updated_after filter
    if filters.updated_after and repo.updated_at < filters.updated_after:
        return False
    
    # Check language filter
    if filters.language:
        repo_language = repo_data.get('language', '')
        if repo_language and repo_language.lower() != filters.language.lower():
            return False
    
    # Check visibility filter
    if filters.visibility and filters.visibility != 'all':
        if repo.visibility != filters.visibility:
            return False
    
    # Check archived filter
    if not filters.archived and repo_data.get('archived', False):
        return False
    
    return True


def _fetch_readme(repo_full_name: str, client: GitHubClient) -> Optional[str]:
    """Fetch README content for a repository.
    
    Args:
        repo_full_name: Full repository name
        client: GitHub client
        
    Returns:
        README content or None if not found
    """
    try:
        readme_data = client.get(f'/repos/{repo_full_name}/readme')
        
        # README content is base64 encoded
        import base64
        content = readme_data.get('content', '')
        if content:
            decoded = base64.b64decode(content).decode('utf-8')
            # Limit README size to avoid token issues
            return decoded[:10000] if len(decoded) > 10000 else decoded
        return None
    except Exception as e:
        logger.debug(f"No README found for {repo_full_name}: {e}")
        return None


def _fetch_file_structure(repo_full_name: str, client: GitHubClient) -> List[str]:
    """Fetch top-level file structure for a repository.
    
    Args:
        repo_full_name: Full repository name
        client: GitHub client
        
    Returns:
        List of file and directory names
    """
    try:
        contents = client.get(f'/repos/{repo_full_name}/contents/')
        return [item['name'] for item in contents if isinstance(contents, list)]
    except Exception as e:
        logger.warning(f"Failed to fetch file structure for {repo_full_name}: {e}")
        return []


def _detect_ci_config(file_structure: List[str]) -> bool:
    """Detect if repository has CI/CD configuration.
    
    Args:
        file_structure: List of top-level files/directories
        
    Returns:
        True if CI/CD config detected
    """
    ci_indicators = [
        '.github',
        '.gitlab-ci.yml',
        '.travis.yml',
        'circle.yml',
        '.circleci',
        'Jenkinsfile',
        '.drone.yml',
        'azure-pipelines.yml'
    ]
    
    return any(indicator in file_structure for indicator in ci_indicators)


def _detect_tests(file_structure: List[str]) -> bool:
    """Detect if repository has test files/directories.
    
    Args:
        file_structure: List of top-level files/directories
        
    Returns:
        True if tests detected
    """
    test_indicators = [
        'test',
        'tests',
        '__tests__',
        'spec',
        'specs',
        'test_',
        'tests_'
    ]
    
    return any(
        any(indicator in name.lower() for indicator in test_indicators)
        for name in file_structure
    )


def _detect_contributing(file_structure: List[str]) -> bool:
    """Detect if repository has CONTRIBUTING file.
    
    Args:
        file_structure: List of top-level files/directories
        
    Returns:
        True if CONTRIBUTING file detected
    """
    return any(
        'contributing' in name.lower()
        for name in file_structure
    )
