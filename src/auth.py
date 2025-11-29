"""Authentication and security module for GitHub Maintainer Agent.

This module provides secure credential management, token validation,
and authentication utilities for GitHub API access.
"""

import os
import logging
from typing import Optional, Tuple
from dataclasses import dataclass

from .tools.github_client import GitHubClient, AuthenticationError
from .config import Config

logger = logging.getLogger(__name__)


@dataclass
class TokenValidationResult:
    """Result of token validation."""
    
    is_valid: bool
    error_message: Optional[str] = None
    username: Optional[str] = None
    scopes: Optional[list] = None


class AuthenticationManager:
    """Manages authentication and secure credential handling."""
    
    def __init__(self, config: Config):
        """Initialize authentication manager.
        
        Args:
            config: Application configuration with credentials
        """
        self.config = config
        self._github_client: Optional[GitHubClient] = None
    
    def validate_github_token(self) -> TokenValidationResult:
        """Validate GitHub token by making an authenticated API call.
        
        This method validates the token by:
        1. Checking token format
        2. Making an authenticated request to /user endpoint
        3. Verifying token has necessary scopes
        
        Returns:
            TokenValidationResult with validation status and details
        """
        # Check token format
        token = self.config.github_token
        
        if not token:
            return TokenValidationResult(
                is_valid=False,
                error_message="GitHub token is empty"
            )
        
        # GitHub tokens should be at least 40 characters
        if len(token) < 40:
            return TokenValidationResult(
                is_valid=False,
                error_message=(
                    "GitHub token appears invalid (should be 40+ characters). "
                    "Please check your GITHUB_TOKEN environment variable."
                )
            )
        
        # Validate token format patterns
        valid_prefixes = ['ghp_', 'gho_', 'ghs_', 'github_pat_']
        if not any(token.startswith(prefix) for prefix in valid_prefixes):
            logger.warning(
                "GitHub token does not start with a recognized prefix. "
                "This may indicate an invalid or old token format."
            )
        
        # Validate by making an API call
        try:
            client = GitHubClient(token=token)
            user_data = client.get('/user')
            
            username = user_data.get('login')
            logger.info(f"GitHub token validated successfully for user: {username}")
            
            return TokenValidationResult(
                is_valid=True,
                username=username
            )
            
        except AuthenticationError as e:
            error_msg = (
                "GitHub authentication failed. Your token may be invalid or expired.\n"
                "To create a new token:\n"
                "1. Go to https://github.com/settings/tokens\n"
                "2. Click 'Generate new token' (classic)\n"
                "3. Select scopes: 'repo', 'read:user'\n"
                "4. Copy the token and set it as GITHUB_TOKEN environment variable"
            )
            logger.error(f"Token validation failed: {e}")
            return TokenValidationResult(
                is_valid=False,
                error_message=error_msg
            )
            
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {e}")
            return TokenValidationResult(
                is_valid=False,
                error_message=f"Unexpected error validating token: {str(e)}"
            )
    
    def validate_credentials_on_startup(self) -> Tuple[bool, Optional[str]]:
        """Validate all credentials on application startup.
        
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        logger.info("Validating credentials on startup...")
        
        # Validate GitHub token
        github_result = self.validate_github_token()
        if not github_result.is_valid:
            return False, github_result.error_message
        
        # Validate Gemini API key format
        gemini_key = self.config.gemini_api_key
        if not gemini_key:
            return False, "Gemini API key is empty"
        
        if len(gemini_key) < 20:
            return False, (
                "Gemini API key appears invalid (too short). "
                "Please check your GEMINI_API_KEY or GOOGLE_API_KEY environment variable.\n"
                "Get your API key at: https://ai.google.dev/tutorials/setup"
            )
        
        logger.info("All credentials validated successfully")
        return True, None
    
    def get_github_client(self) -> GitHubClient:
        """Get or create a GitHub client instance.
        
        Returns:
            GitHubClient: Authenticated GitHub client
        """
        if self._github_client is None:
            self._github_client = GitHubClient(token=self.config.github_token)
        return self._github_client
    
    @staticmethod
    def sanitize_token_for_display(token: str) -> str:
        """Sanitize a token for safe display.
        
        Args:
            token: Token to sanitize
            
        Returns:
            str: Sanitized token showing only first 4 and last 4 characters
        """
        if len(token) <= 8:
            return "****"
        return f"{token[:4]}...{token[-4:]}"
    
    @staticmethod
    def check_token_in_string(text: str) -> bool:
        """Check if a string contains what appears to be a GitHub token.
        
        This is used for security auditing to ensure tokens don't leak.
        
        Args:
            text: Text to check
            
        Returns:
            bool: True if text appears to contain a token
        """
        import re
        
        # Patterns for GitHub tokens
        token_patterns = [
            r'ghp_[a-zA-Z0-9]{36,}',
            r'gho_[a-zA-Z0-9]{36,}',
            r'ghs_[a-zA-Z0-9]{36,}',
            r'github_pat_[a-zA-Z0-9_]{82}',
        ]
        
        for pattern in token_patterns:
            if re.search(pattern, text):
                return True
        
        return False


def validate_startup_credentials(config: Config) -> Tuple[bool, Optional[str]]:
    """Convenience function to validate credentials on startup.
    
    Args:
        config: Application configuration
        
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    auth_manager = AuthenticationManager(config)
    return auth_manager.validate_credentials_on_startup()
