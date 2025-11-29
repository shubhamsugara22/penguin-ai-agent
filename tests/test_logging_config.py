"""Tests for logging configuration and credential sanitization."""

import json
import logging
import pytest
from src.logging_config import (
    CredentialSanitizer,
    StructuredFormatter,
    setup_logging,
    get_logger,
    get_context_logger,
)


class TestCredentialSanitizer:
    """Test credential sanitization functionality."""
    
    def test_sanitize_github_personal_token(self):
        """Test sanitization of GitHub personal access tokens."""
        text = "Using token ghp_1234567890abcdefghijklmnopqrstuvwxyz for auth"
        sanitized = CredentialSanitizer.sanitize(text)
        assert "ghp_" not in sanitized
        assert "[REDACTED]" in sanitized
    
    def test_sanitize_github_oauth_token(self):
        """Test sanitization of GitHub OAuth tokens."""
        text = "OAuth token: gho_1234567890abcdefghijklmnopqrstuvwxyz"
        sanitized = CredentialSanitizer.sanitize(text)
        assert "gho_" not in sanitized
        assert "[REDACTED]" in sanitized
    
    def test_sanitize_google_api_key(self):
        """Test sanitization of Google API keys."""
        text = "API key: AIzaSyD1234567890abcdefghijklmnopqrstuvwxyz"
        sanitized = CredentialSanitizer.sanitize(text)
        assert "AIza" not in sanitized
        assert "[REDACTED]" in sanitized
    
    def test_sanitize_bearer_token(self):
        """Test sanitization of Bearer tokens."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        sanitized = CredentialSanitizer.sanitize(text)
        assert "Bearer" not in sanitized or "eyJ" not in sanitized
        assert "[REDACTED]" in sanitized
    
    def test_sanitize_multiple_tokens(self):
        """Test sanitization of multiple tokens in same text."""
        text = "GitHub: ghp_abc123 and Google: AIzaSyD123"
        sanitized = CredentialSanitizer.sanitize(text)
        assert "ghp_" not in sanitized
        assert "AIza" not in sanitized
        assert sanitized.count("[REDACTED]") >= 2
    
    def test_sanitize_dict_with_token_key(self):
        """Test sanitization of dictionary with token key."""
        data = {
            "token": "ghp_secret123",
            "api_key": "AIzaSyD123",
            "username": "testuser"
        }
        sanitized = CredentialSanitizer.sanitize_dict(data)
        assert sanitized["token"] == "[REDACTED]"
        assert sanitized["api_key"] == "[REDACTED]"
        assert sanitized["username"] == "testuser"
    
    def test_sanitize_dict_with_token_in_value(self):
        """Test sanitization of dictionary with token in string value."""
        data = {
            "message": "Using token ghp_1234567890abcdefghijklmnopqrstuvwxyz",
            "count": 42
        }
        sanitized = CredentialSanitizer.sanitize_dict(data)
        assert "ghp_" not in sanitized["message"]
        assert "[REDACTED]" in sanitized["message"]
        assert sanitized["count"] == 42
    
    def test_sanitize_nested_dict(self):
        """Test sanitization of nested dictionaries."""
        data = {
            "config": {
                "token": "secret123",
                "nested": {
                    "api_key": "AIzaSyD123"
                }
            }
        }
        sanitized = CredentialSanitizer.sanitize_dict(data)
        assert sanitized["config"]["token"] == "[REDACTED]"
        assert sanitized["config"]["nested"]["api_key"] == "[REDACTED]"
    
    def test_sanitize_list_in_dict(self):
        """Test sanitization of lists within dictionaries."""
        data = {
            "tokens": ["ghp_abc123", "ghp_def456"],
            "messages": [
                {"text": "Token: ghp_xyz789"}
            ]
        }
        sanitized = CredentialSanitizer.sanitize_dict(data)
        assert all("[REDACTED]" in token for token in sanitized["tokens"])
        assert "[REDACTED]" in sanitized["messages"][0]["text"]


class TestStructuredFormatter:
    """Test structured JSON logging formatter."""
    
    def test_format_basic_record(self):
        """Test formatting of basic log record."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test"
        assert log_data["message"] == "Test message"
        assert "timestamp" in log_data
    
    def test_format_with_extra_fields(self):
        """Test formatting with extra context fields."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.agent = "TestAgent"
        record.session_id = "session123"
        record.repository = "user/repo"
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["agent"] == "TestAgent"
        assert log_data["session_id"] == "session123"
        assert log_data["repository"] == "user/repo"
    
    def test_format_sanitizes_tokens(self):
        """Test that formatter sanitizes tokens in messages."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Using token ghp_1234567890abcdefghijklmnopqrstuvwxyz",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert "ghp_" not in log_data["message"]
        assert "[REDACTED]" in log_data["message"]


class TestLoggingSetup:
    """Test logging setup and configuration."""
    
    def test_setup_logging_default(self):
        """Test default logging setup."""
        setup_logging()
        logger = get_logger("test")
        assert logger.level <= logging.INFO
    
    def test_setup_logging_debug(self):
        """Test logging setup with DEBUG level."""
        setup_logging("DEBUG")
        logger = get_logger("test")
        assert logger.level <= logging.DEBUG
    
    def test_get_context_logger(self):
        """Test context logger creation."""
        logger = get_context_logger(
            "test",
            session_id="session123",
            agent="TestAgent",
            repository="user/repo"
        )
        assert logger.extra["session_id"] == "session123"
        assert logger.extra["agent"] == "TestAgent"
        assert logger.extra["repository"] == "user/repo"
