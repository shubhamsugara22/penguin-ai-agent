"""Tests for configuration management."""

import os
import pytest
from src.config import Config, get_config, reset_config


class TestConfig:
    """Test configuration loading and validation."""
    
    def setup_method(self):
        """Reset config before each test."""
        reset_config()
    
    def test_config_from_env_success(self, monkeypatch):
        """Test successful configuration loading from environment."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_" + "x" * 36)
        monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key_1234567890")
        
        config = Config.from_env()
        
        assert config.github_token.startswith("ghp_")
        assert config.gemini_api_key == "test_gemini_key_1234567890"
        assert config.log_level == "INFO"
        assert config.max_parallel_repos == 5
    
    def test_config_missing_github_token(self, monkeypatch):
        """Test error when GitHub token is missing."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")
        
        with pytest.raises(ValueError, match="GITHUB_TOKEN"):
            Config.from_env()
    
    def test_config_missing_gemini_key(self, monkeypatch):
        """Test error when Gemini API key is missing."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_" + "x" * 36)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            Config.from_env()
    
    def test_config_accepts_google_api_key(self, monkeypatch):
        """Test that GOOGLE_API_KEY is accepted as alternative."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_" + "x" * 36)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.setenv("GOOGLE_API_KEY", "test_google_key")
        
        config = Config.from_env()
        assert config.gemini_api_key == "test_google_key"
    
    def test_config_custom_values(self, monkeypatch):
        """Test configuration with custom environment values."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_" + "x" * 36)
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("MAX_PARALLEL_REPOS", "10")
        
        config = Config.from_env()
        
        assert config.log_level == "DEBUG"
        assert config.max_parallel_repos == 10
    
    def test_validate_github_token(self):
        """Test GitHub token validation."""
        valid_token = "ghp_" + "x" * 36
        config = Config(
            github_token=valid_token,
            gemini_api_key="test_key"
        )
        assert config.validate_github_token() is True
        
        invalid_config = Config(
            github_token="short",
            gemini_api_key="test_key"
        )
        assert invalid_config.validate_github_token() is False
    
    def test_get_sanitized_config(self):
        """Test that sensitive values are masked in sanitized config."""
        config = Config(
            github_token="ghp_1234567890abcdefghijklmnopqrstuvwxyz",
            gemini_api_key="AIzaSyD1234567890abcdefghijklmnopqrstuvwxyz"
        )
        
        sanitized = config.get_sanitized_config()
        
        assert "ghp_" in sanitized["github_token"]
        assert "..." in sanitized["github_token"]
        assert len(sanitized["github_token"]) < len(config.github_token)
        
        assert "AIza" in sanitized["gemini_api_key"]
        assert "..." in sanitized["gemini_api_key"]
        assert len(sanitized["gemini_api_key"]) < len(config.gemini_api_key)
    
    def test_mask_token(self):
        """Test token masking function."""
        long_token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        masked = Config._mask_token(long_token)
        assert masked.startswith("ghp_")
        assert masked.endswith("wxyz")
        assert "..." in masked
        
        short_token = "short"
        masked_short = Config._mask_token(short_token)
        assert masked_short == "****"
