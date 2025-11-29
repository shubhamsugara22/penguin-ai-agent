"""Structured logging configuration for GitHub Maintainer Agent.

This module sets up structured logging with JSON formatting and
credential sanitization to ensure secure logging practices.
"""

import logging
import json
import re
from datetime import datetime
from typing import Any, Dict, Optional
from logging import LogRecord


class CredentialSanitizer:
    """Sanitizes sensitive information from log messages."""
    
    # Patterns for common token formats
    TOKEN_PATTERNS = [
        re.compile(r'ghp_[a-zA-Z0-9]{6,}'),  # GitHub personal access tokens
        re.compile(r'gho_[a-zA-Z0-9]{6,}'),  # GitHub OAuth tokens
        re.compile(r'ghs_[a-zA-Z0-9]{6,}'),  # GitHub server tokens
        re.compile(r'github_pat_[a-zA-Z0-9_]{22,}'),  # GitHub fine-grained tokens
        re.compile(r'AIza[a-zA-Z0-9_-]{6,}'),  # Google API keys
        re.compile(r'Bearer\s+[a-zA-Z0-9\-._~+/]+=*'),  # Bearer tokens
    ]
    
    @classmethod
    def sanitize(cls, text: str) -> str:
        """Remove sensitive tokens from text.
        
        Args:
            text: Text that may contain sensitive information
            
        Returns:
            str: Text with tokens replaced by [REDACTED]
        """
        if not isinstance(text, str):
            return text
        sanitized = text
        for pattern in cls.TOKEN_PATTERNS:
            sanitized = pattern.sub('[REDACTED]', sanitized)
        return sanitized
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize a dictionary.
        
        Args:
            data: Dictionary that may contain sensitive information
            
        Returns:
            dict: Dictionary with sensitive values redacted
        """
        sanitized = {}
        for key, value in data.items():
            # Redact known sensitive keys
            if key.lower() in ('token', 'api_key', 'password', 'secret', 'authorization'):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, str):
                sanitized[key] = cls.sanitize(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    cls.sanitize_dict(item) if isinstance(item, dict)
                    else cls.sanitize(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: LogRecord) -> str:
        """Format log record as JSON with credential sanitization.
        
        Args:
            record: Log record to format
            
        Returns:
            str: JSON-formatted log entry
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': CredentialSanitizer.sanitize(record.getMessage()),
        }
        
        # Add extra fields if present
        if hasattr(record, 'agent'):
            log_data['agent'] = record.agent
        if hasattr(record, 'event'):
            log_data['event'] = record.event
        if hasattr(record, 'session_id'):
            log_data['session_id'] = record.session_id
        if hasattr(record, 'repository'):
            log_data['repository'] = record.repository
        if hasattr(record, 'metrics'):
            log_data['metrics'] = CredentialSanitizer.sanitize_dict(record.metrics)
        if hasattr(record, 'extra_data'):
            log_data['data'] = CredentialSanitizer.sanitize_dict(record.extra_data)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            log_data['exception'] = CredentialSanitizer.sanitize(log_data['exception'])
        
        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with structured formatter
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(StructuredFormatter())
    
    root_logger.addHandler(console_handler)
    
    # Set level for third-party loggers to reduce noise
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__ of the module)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds context to log records."""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process log message and add extra context.
        
        Args:
            msg: Log message
            kwargs: Additional keyword arguments
            
        Returns:
            tuple: Processed message and kwargs
        """
        # Add context from adapter to extra
        extra = kwargs.get('extra', {})
        extra.update(self.extra)
        kwargs['extra'] = extra
        return msg, kwargs


def get_context_logger(
    name: str,
    session_id: Optional[str] = None,
    agent: Optional[str] = None,
    repository: Optional[str] = None,
) -> LoggerAdapter:
    """Get a logger with context information.
    
    Args:
        name: Logger name
        session_id: Optional session ID
        agent: Optional agent name
        repository: Optional repository name
        
    Returns:
        LoggerAdapter: Logger with context
    """
    logger = get_logger(name)
    context = {}
    if session_id:
        context['session_id'] = session_id
    if agent:
        context['agent'] = agent
    if repository:
        context['repository'] = repository
    
    return LoggerAdapter(logger, context)
