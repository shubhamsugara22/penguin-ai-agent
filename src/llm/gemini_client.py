"""Gemini LLM client with error handling, retry logic, and token tracking.

This module provides a robust interface to the Gemini API with:
- Structured output parsing and validation
- Automatic retry logic with exponential backoff
- Token usage tracking
- Fallback strategies for failures
- Comprehensive error handling
"""

import logging
import time
import json
from typing import Optional, Dict, Any, Callable, TypeVar, Generic
from dataclasses import dataclass
import functools

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from ..config import get_config
from ..observability import get_metrics_collector

logger = logging.getLogger(__name__)


# Custom exceptions
class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class LLMRateLimitError(LLMError):
    """Exception raised when rate limit is exceeded."""
    pass


class LLMAuthenticationError(LLMError):
    """Exception raised when authentication fails."""
    pass


class LLMContextLengthError(LLMError):
    """Exception raised when context length is exceeded."""
    pass


class LLMResponseParsingError(LLMError):
    """Exception raised when response cannot be parsed."""
    pass


class LLMServiceUnavailableError(LLMError):
    """Exception raised when service is unavailable."""
    pass


@dataclass
class LLMResponse:
    """Response from LLM API call."""
    
    text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    finish_reason: Optional[str] = None
    raw_response: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'text': self.text,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens,
            'model': self.model,
            'finish_reason': self.finish_reason
        }


T = TypeVar('T')


class GeminiClient:
    """Client for interacting with Gemini LLM API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = 'gemini-1.5-flash',
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0
    ):
        """Initialize Gemini client.
        
        Args:
            api_key: Optional API key (uses config if not provided)
            model_name: Name of the Gemini model to use
            max_retries: Maximum number of retry attempts
            base_delay: Base delay for exponential backoff (seconds)
            max_delay: Maximum delay between retries (seconds)
        """
        config = get_config()
        self.api_key = api_key or config.gemini_api_key
        self.model_name = model_name
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        
        logger.info(f"Gemini client initialized with model: {model_name}")
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None
    ) -> LLMResponse:
        """Generate text from a prompt with retry logic.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0.0-1.0)
            max_output_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            
        Returns:
            LLMResponse with generated text and metadata
            
        Raises:
            LLMError: If generation fails after retries
        """
        metrics = get_metrics_collector()
        start_time = time.time()
        
        # Prepare generation config
        generation_config = {
            'temperature': temperature,
        }
        if max_output_tokens:
            generation_config['max_output_tokens'] = max_output_tokens
        if top_p is not None:
            generation_config['top_p'] = top_p
        if top_k is not None:
            generation_config['top_k'] = top_k
        
        logger.debug(
            f"Generating with Gemini: prompt_length={len(prompt)}, "
            f"temperature={temperature}",
            extra={
                'event': 'llm_generate_start',
                'extra_data': {
                    'model': self.model_name,
                    'prompt_length': len(prompt),
                    'temperature': temperature
                }
            }
        )
        
        # Retry with exponential backoff
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                # Call Gemini API
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                # Extract token usage
                prompt_tokens = 0
                completion_tokens = 0
                if hasattr(response, 'usage_metadata'):
                    usage = response.usage_metadata
                    prompt_tokens = usage.prompt_token_count
                    completion_tokens = usage.candidates_token_count
                
                # Record metrics
                duration_ms = (time.time() - start_time) * 1000
                metrics.record_api_call('gemini', 'generate', duration_ms, success=True)
                metrics.record_token_usage(
                    self.model_name,
                    prompt_tokens,
                    completion_tokens
                )
                
                # Build response
                llm_response = LLMResponse(
                    text=response.text,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    model=self.model_name,
                    finish_reason=response.candidates[0].finish_reason.name if response.candidates else None,
                    raw_response=response
                )
                
                logger.debug(
                    f"Generation successful: tokens={llm_response.total_tokens}",
                    extra={
                        'event': 'llm_generate_success',
                        'extra_data': {
                            'model': self.model_name,
                            'prompt_tokens': prompt_tokens,
                            'completion_tokens': completion_tokens,
                            'duration_ms': duration_ms
                        }
                    }
                )
                
                return llm_response
                
            except google_exceptions.ResourceExhausted as e:
                # Rate limit exceeded
                last_exception = LLMRateLimitError(f"Rate limit exceeded: {e}")
                logger.warning(
                    f"Rate limit exceeded (attempt {attempt + 1}/{self.max_retries})",
                    extra={
                        'event': 'llm_rate_limit',
                        'extra_data': {'attempt': attempt + 1, 'max_retries': self.max_retries}
                    }
                )
                
            except google_exceptions.Unauthenticated as e:
                # Authentication failed - don't retry
                duration_ms = (time.time() - start_time) * 1000
                metrics.record_api_call('gemini', 'generate', duration_ms, success=False, error='auth_failed')
                metrics.record_error('llm_auth_error')
                raise LLMAuthenticationError(f"Authentication failed: {e}")
                
            except google_exceptions.InvalidArgument as e:
                # Invalid argument (possibly context length) - don't retry
                duration_ms = (time.time() - start_time) * 1000
                metrics.record_api_call('gemini', 'generate', duration_ms, success=False, error='invalid_argument')
                metrics.record_error('llm_context_length_error')
                
                # Check if it's a context length error
                error_msg = str(e).lower()
                if 'token' in error_msg or 'length' in error_msg or 'context' in error_msg:
                    raise LLMContextLengthError(f"Context length exceeded: {e}")
                else:
                    raise LLMError(f"Invalid argument: {e}")
                    
            except google_exceptions.ServiceUnavailable as e:
                # Service unavailable - retry
                last_exception = LLMServiceUnavailableError(f"Service unavailable: {e}")
                logger.warning(
                    f"Service unavailable (attempt {attempt + 1}/{self.max_retries})",
                    extra={
                        'event': 'llm_service_unavailable',
                        'extra_data': {'attempt': attempt + 1, 'max_retries': self.max_retries}
                    }
                )
                
            except Exception as e:
                # Unknown error
                last_exception = LLMError(f"Unexpected error: {e}")
                logger.error(
                    f"Unexpected error during generation (attempt {attempt + 1}/{self.max_retries}): {e}",
                    extra={
                        'event': 'llm_unexpected_error',
                        'extra_data': {
                            'attempt': attempt + 1,
                            'max_retries': self.max_retries,
                            'error': str(e)
                        }
                    },
                    exc_info=True
                )
            
            # Calculate delay for next retry
            if attempt < self.max_retries - 1:
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                logger.info(f"Retrying in {delay:.1f} seconds...")
                time.sleep(delay)
        
        # All retries failed
        duration_ms = (time.time() - start_time) * 1000
        metrics.record_api_call('gemini', 'generate', duration_ms, success=False, error='max_retries_exceeded')
        metrics.record_error('llm_max_retries_exceeded')
        
        logger.error(
            f"Generation failed after {self.max_retries} attempts",
            extra={
                'event': 'llm_generate_failed',
                'extra_data': {'max_retries': self.max_retries}
            }
        )
        
        raise last_exception or LLMError("Generation failed after max retries")
    
    def generate_json(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        validator: Optional[Callable[[Dict[str, Any]], bool]] = None
    ) -> Dict[str, Any]:
        """Generate JSON output from a prompt.
        
        Args:
            prompt: Input prompt (should request JSON output)
            temperature: Sampling temperature
            max_output_tokens: Maximum tokens to generate
            validator: Optional function to validate parsed JSON
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            LLMResponseParsingError: If response cannot be parsed as JSON
            LLMError: If generation fails
        """
        logger.debug("Generating JSON response")
        
        # Generate response
        response = self.generate(
            prompt=prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens
        )
        
        # Parse JSON from response
        try:
            json_data = self._extract_json(response.text)
            
            # Validate if validator provided
            if validator and not validator(json_data):
                raise LLMResponseParsingError("JSON validation failed")
            
            logger.debug("Successfully parsed JSON response")
            return json_data
            
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse JSON response: {e}",
                extra={
                    'event': 'llm_json_parse_error',
                    'extra_data': {'error': str(e), 'response_text': response.text[:500]}
                }
            )
            raise LLMResponseParsingError(f"Failed to parse JSON: {e}")
    
    def generate_with_fallback(
        self,
        prompt: str,
        fallback_fn: Callable[[], T],
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None
    ) -> T:
        """Generate with a fallback function if LLM fails.
        
        Args:
            prompt: Input prompt
            fallback_fn: Function to call if LLM fails
            temperature: Sampling temperature
            max_output_tokens: Maximum tokens to generate
            
        Returns:
            LLM response or fallback result
        """
        metrics = get_metrics_collector()
        
        try:
            response = self.generate(
                prompt=prompt,
                temperature=temperature,
                max_output_tokens=max_output_tokens
            )
            return response.text
            
        except Exception as e:
            logger.warning(
                f"LLM generation failed, using fallback: {e}",
                extra={
                    'event': 'llm_fallback_used',
                    'extra_data': {'error': str(e)}
                }
            )
            metrics.record_recovery('llm_fallback')
            return fallback_fn()
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response.
        
        Handles cases where LLM includes extra text around JSON.
        
        Args:
            text: Response text
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            json.JSONDecodeError: If JSON cannot be extracted
        """
        # Try to find JSON object in text
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            # Try to find JSON array
            json_start = text.find('[')
            json_end = text.rfind(']') + 1
        
        if json_start == -1 or json_end == 0:
            raise json.JSONDecodeError("No JSON found in response", text, 0)
        
        json_str = text[json_start:json_end]
        return json.loads(json_str)
    
    def validate_api_key(self) -> bool:
        """Validate that the API key is working.
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Try a simple generation
            response = self.generate(
                prompt="Say 'OK' if you can read this.",
                temperature=0.0,
                max_output_tokens=10
            )
            return True
        except LLMAuthenticationError:
            return False
        except Exception as e:
            logger.warning(f"API key validation failed with unexpected error: {e}")
            return False


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: tuple = (LLMRateLimitError, LLMServiceUnavailableError)
):
    """Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay for exponential backoff (seconds)
        max_delay: Maximum delay between retries (seconds)
        retryable_exceptions: Tuple of exceptions to retry on
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.info(
                            f"Retrying {func.__name__} in {delay:.1f}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


# Singleton instance
_client_instance: Optional[GeminiClient] = None


def get_gemini_client(
    api_key: Optional[str] = None,
    model_name: str = 'gemini-1.5-flash'
) -> GeminiClient:
    """Get or create a Gemini client instance.
    
    Args:
        api_key: Optional API key
        model_name: Model name to use
        
    Returns:
        GeminiClient instance
    """
    global _client_instance
    
    if _client_instance is None:
        _client_instance = GeminiClient(api_key=api_key, model_name=model_name)
    
    return _client_instance
