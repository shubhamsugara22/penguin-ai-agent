"""Tests for authentication and security module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.auth import (
    AuthenticationManager,
    TokenValidationResult,
    validate_startup_credentials
)
from src.config import Config
from src.tools.github_client import AuthenticationError, GitHubAPIError


class TestTokenValidationResult:
    """Test TokenValidationResult dataclass."""
    
    def test_valid_result(self):
        """Test creating a valid result."""
        result = TokenValidationResult(
            is_valid=True,
            username="testuser",
            scopes=["repo", "read:user"]
        )
        assert result.is_valid is True
        assert result.username == "testuser"
        assert result.error_message is None
    
    def test_invalid_result(self):
        """Test creating an invalid result."""
        result = TokenValidationResult(
            is_valid=False,
            error_message="Token is invalid"
        )
        assert result.is_valid is False
        assert result.error_message == "Token is invalid"
        assert result.username is None


class TestAuthenticationManager:
    """Test AuthenticationManager class."""
    
    def test_init(self):
        """Test initialization of AuthenticationManager."""
        config = Config(
            github_token="ghp_" + "x" * 36,
            gemini_api_key="test_key"
        )
        auth_manager = AuthenticationManager(config)
        assert auth_manager.config == config
        assert auth_manager._github_client is None
    
    def test_validate_github_token_empty(self):
        """Test validation with empty token."""
        config = Config(
            github_token="",
            gemini_api_key="test_key"
        )
        auth_manager = AuthenticationManager(config)
        result = auth_manager.validate_github_token()
        
        assert result.is_valid is False
        assert "empty" in result.error_message.lower()
    
    def test_validate_github_token_too_short(self):
        """Test validation with token that's too short."""
        config = Config(
            github_token="short_token",
            gemini_api_key="test_key"
        )
        auth_manager = AuthenticationManager(config)
        result = auth_manager.validate_github_token()
        
        assert result.is_valid is False
        assert "40+ characters" in result.error_message
    
    @patch('src.auth.GitHubClient')
    def test_validate_github_token_success(self, mock_client_class):
        """Test successful token validation."""
        # Setup mock
        mock_client = Mock()
        mock_client.get.return_value = {'login': 'testuser'}
        mock_client_class.return_value = mock_client
        
        config = Config(
            github_token="ghp_" + "x" * 36,
            gemini_api_key="test_key"
        )
        auth_manager = AuthenticationManager(config)
        result = auth_manager.validate_github_token()
        
        assert result.is_valid is True
        assert result.username == "testuser"
        assert result.error_message is None
        mock_client.get.assert_called_once_with('/user')
    
    @patch('src.auth.GitHubClient')
    def test_validate_github_token_auth_failure(self, mock_client_class):
        """Test token validation with authentication failure."""
        # Setup mock to raise AuthenticationError
        mock_client = Mock()
        mock_client.get.side_effect = AuthenticationError("Invalid token")
        mock_client_class.return_value = mock_client
        
        config = Config(
            github_token="ghp_" + "x" * 36,
            gemini_api_key="test_key"
        )
        auth_manager = AuthenticationManager(config)
        result = auth_manager.validate_github_token()
        
        assert result.is_valid is False
        assert "authentication failed" in result.error_message.lower()
        assert "https://github.com/settings/tokens" in result.error_message
    
    @patch('src.auth.GitHubClient')
    def test_validate_github_token_unexpected_error(self, mock_client_class):
        """Test token validation with unexpected error."""
        # Setup mock to raise unexpected error
        mock_client = Mock()
        mock_client.get.side_effect = Exception("Network error")
        mock_client_class.return_value = mock_client
        
        config = Config(
            github_token="ghp_" + "x" * 36,
            gemini_api_key="test_key"
        )
        auth_manager = AuthenticationManager(config)
        result = auth_manager.validate_github_token()
        
        assert result.is_valid is False
        assert "unexpected error" in result.error_message.lower()
    
    @patch('src.auth.GitHubClient')
    def test_validate_credentials_on_startup_success(self, mock_client_class):
        """Test successful credential validation on startup."""
        # Setup mock
        mock_client = Mock()
        mock_client.get.return_value = {'login': 'testuser'}
        mock_client_class.return_value = mock_client
        
        config = Config(
            github_token="ghp_" + "x" * 36,
            gemini_api_key="AIzaSyD" + "x" * 32
        )
        auth_manager = AuthenticationManager(config)
        success, error_msg = auth_manager.validate_credentials_on_startup()
        
        assert success is True
        assert error_msg is None
    
    @patch('src.auth.GitHubClient')
    def test_validate_credentials_on_startup_github_failure(self, mock_client_class):
        """Test credential validation with GitHub token failure."""
        # Setup mock to fail
        mock_client = Mock()
        mock_client.get.side_effect = AuthenticationError("Invalid token")
        mock_client_class.return_value = mock_client
        
        config = Config(
            github_token="ghp_" + "x" * 36,
            gemini_api_key="AIzaSyD" + "x" * 32
        )
        auth_manager = AuthenticationManager(config)
        success, error_msg = auth_manager.validate_credentials_on_startup()
        
        assert success is False
        assert error_msg is not None
        assert "authentication failed" in error_msg.lower()
    
    @patch('src.auth.GitHubClient')
    def test_validate_credentials_on_startup_gemini_empty(self, mock_client_class):
        """Test credential validation with empty Gemini key."""
        # Setup mock for GitHub validation
        mock_client = Mock()
        mock_client.get.return_value = {'login': 'testuser'}
        mock_client_class.return_value = mock_client
        
        config = Config(
            github_token="ghp_" + "x" * 36,
            gemini_api_key=""
        )
        auth_manager = AuthenticationManager(config)
        success, error_msg = auth_manager.validate_credentials_on_startup()
        
        assert success is False
        assert "gemini api key is empty" in error_msg.lower()
    
    @patch('src.auth.GitHubClient')
    def test_validate_credentials_on_startup_gemini_too_short(self, mock_client_class):
        """Test credential validation with Gemini key that's too short."""
        # Setup mock for GitHub validation
        mock_client = Mock()
        mock_client.get.return_value = {'login': 'testuser'}
        mock_client_class.return_value = mock_client
        
        config = Config(
            github_token="ghp_" + "x" * 36,
            gemini_api_key="short"
        )
        auth_manager = AuthenticationManager(config)
        success, error_msg = auth_manager.validate_credentials_on_startup()
        
        assert success is False
        assert "gemini api key appears invalid" in error_msg.lower()
        assert "https://ai.google.dev/tutorials/setup" in error_msg
    
    @patch('src.auth.GitHubClient')
    def test_get_github_client(self, mock_client_class):
        """Test getting GitHub client instance."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        config = Config(
            github_token="ghp_" + "x" * 36,
            gemini_api_key="test_key"
        )
        auth_manager = AuthenticationManager(config)
        
        # First call should create client
        client1 = auth_manager.get_github_client()
        assert client1 == mock_client
        mock_client_class.assert_called_once_with(token=config.github_token)
        
        # Second call should return same instance
        client2 = auth_manager.get_github_client()
        assert client2 == client1
        # Should still only be called once
        assert mock_client_class.call_count == 1
    
    def test_sanitize_token_for_display_long(self):
        """Test token sanitization for long tokens."""
        token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        sanitized = AuthenticationManager.sanitize_token_for_display(token)
        
        assert sanitized.startswith("ghp_")
        assert sanitized.endswith("wxyz")
        assert "..." in sanitized
        assert len(sanitized) < len(token)
    
    def test_sanitize_token_for_display_short(self):
        """Test token sanitization for short tokens."""
        token = "short"
        sanitized = AuthenticationManager.sanitize_token_for_display(token)
        assert sanitized == "****"
    
    def test_check_token_in_string_ghp(self):
        """Test detecting GitHub personal access token in string."""
        text = "My token is ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        assert AuthenticationManager.check_token_in_string(text) is True
    
    def test_check_token_in_string_gho(self):
        """Test detecting GitHub OAuth token in string."""
        text = "OAuth token: gho_1234567890abcdefghijklmnopqrstuvwxyz"
        assert AuthenticationManager.check_token_in_string(text) is True
    
    def test_check_token_in_string_ghs(self):
        """Test detecting GitHub server token in string."""
        text = "Server token: ghs_1234567890abcdefghijklmnopqrstuvwxyz"
        assert AuthenticationManager.check_token_in_string(text) is True
    
    def test_check_token_in_string_fine_grained(self):
        """Test detecting GitHub fine-grained token in string."""
        token = "github_pat_" + "x" * 82
        text = f"Fine-grained token: {token}"
        assert AuthenticationManager.check_token_in_string(text) is True
    
    def test_check_token_in_string_no_token(self):
        """Test that normal text doesn't trigger false positive."""
        text = "This is just normal text without any tokens"
        assert AuthenticationManager.check_token_in_string(text) is False
    
    def test_check_token_in_string_partial_match(self):
        """Test that partial token patterns don't match."""
        text = "ghp_short"  # Too short to be a real token
        assert AuthenticationManager.check_token_in_string(text) is False


class TestValidateStartupCredentials:
    """Test validate_startup_credentials convenience function."""
    
    @patch('src.auth.AuthenticationManager')
    def test_validate_startup_credentials(self, mock_auth_manager_class):
        """Test the convenience function."""
        # Setup mock
        mock_auth_manager = Mock()
        mock_auth_manager.validate_credentials_on_startup.return_value = (True, None)
        mock_auth_manager_class.return_value = mock_auth_manager
        
        config = Config(
            github_token="ghp_" + "x" * 36,
            gemini_api_key="test_key"
        )
        
        success, error_msg = validate_startup_credentials(config)
        
        assert success is True
        assert error_msg is None
        mock_auth_manager_class.assert_called_once_with(config)
        mock_auth_manager.validate_credentials_on_startup.assert_called_once()


class TestTokenSecurityAudit:
    """Test security features to ensure tokens don't leak."""
    
    def test_token_not_in_error_messages(self):
        """Test that tokens don't appear in error messages."""
        config = Config(
            github_token="ghp_1234567890abcdefghijklmnopqrstuvwxyz",
            gemini_api_key="test_key"
        )
        auth_manager = AuthenticationManager(config)
        
        # Test with short token (should fail validation)
        config.github_token = "short"
        result = auth_manager.validate_github_token()
        
        # Error message should not contain the actual token
        assert "short" not in result.error_message
    
    @patch('src.auth.GitHubClient')
    def test_token_not_logged_on_validation(self, mock_client_class):
        """Test that tokens are not logged during validation."""
        mock_client = Mock()
        mock_client.get.return_value = {'login': 'testuser'}
        mock_client_class.return_value = mock_client
        
        token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        config = Config(
            github_token=token,
            gemini_api_key="test_key"
        )
        
        auth_manager = AuthenticationManager(config)
        
        # Capture log output
        with patch('src.auth.logger') as mock_logger:
            result = auth_manager.validate_github_token()
            
            # Check that no log call contains the full token
            for call in mock_logger.info.call_args_list:
                args = str(call)
                assert token not in args
            
            for call in mock_logger.error.call_args_list:
                args = str(call)
                assert token not in args
