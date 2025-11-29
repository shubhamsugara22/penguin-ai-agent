"""GitHub API client wrapper with authentication and rate limit handling."""

import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import requests

from ..config import get_config

logger = logging.getLogger(__name__)


class GitHubAPIError(Exception):
    """Base exception for GitHub API errors."""
    pass


class AuthenticationError(GitHubAPIError):
    """Raised when GitHub authentication fails."""
    pass


class RateLimitError(GitHubAPIError):
    """Raised when GitHub API rate limit is exceeded."""
    
    def __init__(self, message: str, reset_time: Optional[datetime] = None):
        super().__init__(message)
        self.reset_time = reset_time


class RepositoryNotFoundError(GitHubAPIError):
    """Raised when a repository is not found."""
    pass


class GitHubClient:
    """GitHub API client with authentication and error handling."""
    
    def __init__(self, token: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize GitHub client.
        
        Args:
            token: GitHub personal access token (defaults to config)
            base_url: GitHub API base URL (defaults to config)
        """
        config = get_config()
        self.token = token or config.github_token
        self.base_url = (base_url or config.github_api_base_url).rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Maintainer-Agent/1.0'
        })
        
        # Rate limit tracking
        self._rate_limit_remaining: Optional[int] = None
        self._rate_limit_reset: Optional[datetime] = None
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> requests.Response:
        """Make an authenticated request to GitHub API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            json_data: JSON body for POST/PATCH requests
            max_retries: Maximum number of retry attempts
            
        Returns:
            Response object
            
        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit is exceeded
            RepositoryNotFoundError: If repository is not found
            GitHubAPIError: For other API errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    timeout=30
                )
                
                # Update rate limit tracking
                self._update_rate_limit_info(response)
                
                # Handle different status codes
                if response.status_code == 200 or response.status_code == 201:
                    return response
                elif response.status_code == 401 or response.status_code == 403:
                    if 'rate limit' in response.text.lower():
                        reset_time = self._get_rate_limit_reset(response)
                        raise RateLimitError(
                            f"GitHub API rate limit exceeded. Resets at {reset_time}",
                            reset_time=reset_time
                        )
                    else:
                        raise AuthenticationError(
                            "GitHub authentication failed. Please check your token. "
                            "See: https://docs.github.com/en/authentication"
                        )
                elif response.status_code == 404:
                    raise RepositoryNotFoundError(f"Resource not found: {url}")
                elif response.status_code >= 500:
                    # Server error - retry with backoff
                    if attempt < max_retries - 1:
                        delay = 2 ** attempt
                        logger.warning(
                            f"GitHub API server error (attempt {attempt + 1}/{max_retries}). "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                        continue
                    else:
                        raise GitHubAPIError(
                            f"GitHub API server error: {response.status_code} - {response.text}"
                        )
                else:
                    raise GitHubAPIError(
                        f"GitHub API error: {response.status_code} - {response.text}"
                    )
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    delay = 2 ** attempt
                    logger.warning(
                        f"Request timeout (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    continue
                else:
                    raise GitHubAPIError("Request timed out after multiple retries")
                    
            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries - 1:
                    delay = 2 ** attempt
                    logger.warning(
                        f"Connection error (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    continue
                else:
                    raise GitHubAPIError(f"Connection error: {str(e)}")
        
        raise GitHubAPIError("Max retries exceeded")
    
    def _update_rate_limit_info(self, response: requests.Response) -> None:
        """Update rate limit information from response headers.
        
        Args:
            response: Response object with rate limit headers
        """
        if 'X-RateLimit-Remaining' in response.headers:
            self._rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
        
        if 'X-RateLimit-Reset' in response.headers:
            reset_timestamp = int(response.headers['X-RateLimit-Reset'])
            self._rate_limit_reset = datetime.fromtimestamp(reset_timestamp)
            
        # Log warning if rate limit is low
        if self._rate_limit_remaining is not None and self._rate_limit_remaining < 100:
            logger.warning(
                f"GitHub API rate limit low: {self._rate_limit_remaining} requests remaining. "
                f"Resets at {self._rate_limit_reset}"
            )
    
    def _get_rate_limit_reset(self, response: requests.Response) -> Optional[datetime]:
        """Extract rate limit reset time from response.
        
        Args:
            response: Response object
            
        Returns:
            Reset time or None if not available
        """
        if 'X-RateLimit-Reset' in response.headers:
            reset_timestamp = int(response.headers['X-RateLimit-Reset'])
            return datetime.fromtimestamp(reset_timestamp)
        return None
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request to GitHub API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        response = self._make_request('GET', endpoint, params=params)
        return response.json()
    
    def post(self, endpoint: str, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to GitHub API.
        
        Args:
            endpoint: API endpoint
            json_data: JSON body
            
        Returns:
            JSON response as dictionary
        """
        response = self._make_request('POST', endpoint, json_data=json_data)
        return response.json()
    
    def get_paginated(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        max_pages: int = 10
    ) -> List[Dict[str, Any]]:
        """Make a paginated GET request to GitHub API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            max_pages: Maximum number of pages to fetch
            
        Returns:
            List of all items from all pages
        """
        params = params or {}
        params.setdefault('per_page', 100)
        
        all_items = []
        page = 1
        
        while page <= max_pages:
            params['page'] = page
            response = self._make_request('GET', endpoint, params=params)
            items = response.json()
            
            if not items:
                break
            
            all_items.extend(items)
            
            # Check if there are more pages
            if 'Link' not in response.headers or 'rel="next"' not in response.headers['Link']:
                break
            
            page += 1
        
        return all_items
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status.
        
        Returns:
            Dictionary with rate limit information
        """
        return {
            'remaining': self._rate_limit_remaining,
            'reset_time': self._rate_limit_reset
        }
    
    def validate_token(self) -> bool:
        """Validate that the GitHub token is valid.
        
        Returns:
            True if token is valid, False otherwise
        """
        try:
            self.get('/user')
            return True
        except AuthenticationError:
            return False
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return False
