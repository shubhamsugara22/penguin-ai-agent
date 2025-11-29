"""Configuration management for GitHub Maintainer Agent.

This module handles loading and validating environment variables
for GitHub API authentication and Gemini LLM integration.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration loaded from environment variables."""
    
    github_token: str
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash-exp"
    log_level: str = "INFO"
    max_parallel_repos: int = 5
    github_api_base_url: str = "https://api.github.com"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables.
        
        Returns:
            Config: Configuration instance with values from environment
            
        Raises:
            ValueError: If required environment variables are missing
        """
        load_dotenv()
        
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError(
                "GITHUB_TOKEN environment variable is required. "
                "Please set it to your GitHub personal access token. "
                "See: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token"
            )
        
        gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required. "
                "Please set it to your Google AI Studio API key. "
                "See: https://ai.google.dev/tutorials/setup"
            )
        
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        max_parallel_repos = int(os.getenv("MAX_PARALLEL_REPOS", "5"))
        github_api_base_url = os.getenv("GITHUB_API_BASE_URL", "https://api.github.com")
        
        return cls(
            github_token=github_token,
            gemini_api_key=gemini_api_key,
            gemini_model=gemini_model,
            log_level=log_level,
            max_parallel_repos=max_parallel_repos,
            github_api_base_url=github_api_base_url,
        )
    
    def validate_github_token(self) -> bool:
        """Validate that the GitHub token is properly formatted.
        
        Returns:
            bool: True if token appears valid, False otherwise
        """
        # GitHub tokens are typically 40+ characters
        return len(self.github_token) >= 40
    
    def get_sanitized_config(self) -> dict:
        """Get configuration with sensitive values masked for logging.
        
        Returns:
            dict: Configuration dictionary with tokens masked
        """
        return {
            "github_token": self._mask_token(self.github_token),
            "gemini_api_key": self._mask_token(self.gemini_api_key),
            "gemini_model": self.gemini_model,
            "log_level": self.log_level,
            "max_parallel_repos": self.max_parallel_repos,
            "github_api_base_url": self.github_api_base_url,
        }
    
    @staticmethod
    def _mask_token(token: str) -> str:
        """Mask a token for safe logging.
        
        Args:
            token: The token to mask
            
        Returns:
            str: Masked token showing only first 4 and last 4 characters
        """
        if len(token) <= 8:
            return "****"
        return f"{token[:4]}...{token[-4:]}"


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance.
    
    Returns:
        Config: The global configuration instance
        
    Raises:
        ValueError: If configuration has not been initialized
    """
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def reset_config() -> None:
    """Reset the global configuration instance (useful for testing)."""
    global _config
    _config = None
