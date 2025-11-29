# LLM Integration Module

This module provides a robust interface to the Gemini LLM API with comprehensive error handling, retry logic, and token tracking.

## Features

- **Structured Output Parsing**: Automatic JSON extraction and validation from LLM responses
- **Retry Logic**: Exponential backoff for transient failures (rate limits, service unavailable)
- **Token Tracking**: Automatic tracking of prompt and completion tokens for cost monitoring
- **Error Handling**: Comprehensive exception hierarchy for different error types
- **Fallback Strategies**: Support for fallback functions when LLM calls fail
- **API Key Validation**: Built-in validation to check if API key is working

## Usage

### Basic Text Generation

```python
from src.llm import GeminiClient

# Initialize client
client = GeminiClient()

# Generate text
response = client.generate(
    prompt="Explain what a repository health check is.",
    temperature=0.7,
    max_output_tokens=500
)

print(response.text)
print(f"Tokens used: {response.total_tokens}")
```

### JSON Generation

```python
from src.llm import GeminiClient

client = GeminiClient()

prompt = """Generate a health assessment in JSON format:
{
  "activity_level": "active|moderate|stale|abandoned",
  "test_coverage": "good|partial|none|unknown",
  "overall_health_score": 0.0-1.0
}

Respond with ONLY the JSON object."""

# Parse JSON automatically
json_data = client.generate_json(prompt, temperature=0.0)
print(json_data['activity_level'])
```

### With Fallback

```python
from src.llm import GeminiClient

client = GeminiClient()

def fallback_health_assessment():
    return {
        "activity_level": "unknown",
        "test_coverage": "unknown",
        "overall_health_score": 0.5
    }

# Will use fallback if LLM fails
result = client.generate_with_fallback(
    prompt="Assess repository health...",
    fallback_fn=fallback_health_assessment
)
```

### Error Handling

```python
from src.llm import (
    GeminiClient,
    LLMError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMContextLengthError
)

client = GeminiClient()

try:
    response = client.generate(prompt="...")
except LLMAuthenticationError:
    print("Invalid API key")
except LLMRateLimitError:
    print("Rate limit exceeded, try again later")
except LLMContextLengthError:
    print("Prompt too long, reduce context size")
except LLMError as e:
    print(f"LLM error: {e}")
```

### Using the Singleton

```python
from src.llm import get_gemini_client

# Get or create singleton instance
client = get_gemini_client()

# All subsequent calls use the same instance
client2 = get_gemini_client()
assert client is client2
```

## Configuration

The client uses configuration from `src/config.py`:

- `GEMINI_API_KEY` or `GOOGLE_API_KEY`: Your Google AI Studio API key
- Model: `gemini-1.5-flash` (default, can be changed in constructor)

## Exception Hierarchy

```
LLMError (base)
├── LLMRateLimitError (rate limit exceeded, retryable)
├── LLMAuthenticationError (invalid API key, not retryable)
├── LLMContextLengthError (prompt too long, not retryable)
├── LLMResponseParsingError (failed to parse response)
└── LLMServiceUnavailableError (service down, retryable)
```

## Retry Behavior

The client automatically retries on:
- Rate limit errors (429)
- Service unavailable errors (503)

Retry configuration:
- Max retries: 3 (configurable)
- Base delay: 1 second (configurable)
- Max delay: 60 seconds (configurable)
- Backoff: Exponential (2^attempt * base_delay)

Non-retryable errors:
- Authentication failures
- Invalid arguments (e.g., context length exceeded)

## Token Tracking

Token usage is automatically tracked and recorded via the observability module:

```python
response = client.generate(prompt="...")

# Token counts are in the response
print(f"Prompt tokens: {response.prompt_tokens}")
print(f"Completion tokens: {response.completion_tokens}")
print(f"Total tokens: {response.total_tokens}")

# Also recorded in metrics collector
from src.observability import get_metrics_collector
metrics = get_metrics_collector()
summary = metrics.get_session_summary()
print(summary['tokens']['total_tokens'])
```

## Integration with Agents

The LLM client is used by the Analyzer and Maintainer agents:

```python
# In analyzer.py
from src.llm import GeminiClient

class AnalyzerAgent:
    def __init__(self):
        self.llm_client = GeminiClient()
    
    def generate_health_snapshot(self, repo_data):
        prompt = self._create_health_prompt(repo_data)
        try:
            json_data = self.llm_client.generate_json(prompt)
            return self._parse_health_data(json_data)
        except LLMError:
            # Fallback to rule-based assessment
            return self._fallback_health_assessment(repo_data)
```

## Best Practices

1. **Always handle exceptions**: LLM calls can fail for various reasons
2. **Provide fallbacks**: Have rule-based alternatives for critical functionality
3. **Use structured prompts**: Request JSON output for easier parsing
4. **Set temperature appropriately**: Use 0.0 for deterministic outputs, 0.7+ for creative tasks
5. **Monitor token usage**: Track costs via the metrics collector
6. **Validate responses**: Check that parsed JSON has expected structure
7. **Keep prompts concise**: Reduce token usage and improve response quality

## Testing

To test the LLM client:

1. Set up your API key in `.env`:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

2. Run the verification script:
   ```bash
   python verify_llm_client.py
   ```

3. Or use in your own tests:
   ```python
   from src.llm import GeminiClient
   
   def test_llm_generation():
       client = GeminiClient()
       response = client.generate("Say hello", temperature=0.0)
       assert "hello" in response.text.lower()
   ```

## Troubleshooting

### "Authentication failed"
- Check that `GEMINI_API_KEY` is set in your `.env` file
- Verify the API key is valid at https://ai.google.dev/

### "Rate limit exceeded"
- Wait for the rate limit to reset (usually 1 minute)
- Consider using a different API key
- Reduce the frequency of API calls

### "Context length exceeded"
- Reduce the prompt size
- Use context compaction strategies (see `analyzer.py` for examples)
- Split large prompts into smaller chunks

### "Service unavailable"
- The Gemini API may be temporarily down
- The client will automatically retry with exponential backoff
- If persistent, check https://status.cloud.google.com/

## API Reference

### GeminiClient

#### `__init__(api_key, model_name, max_retries, base_delay, max_delay)`
Initialize the Gemini client.

#### `generate(prompt, temperature, max_output_tokens, top_p, top_k) -> LLMResponse`
Generate text from a prompt with retry logic.

#### `generate_json(prompt, temperature, max_output_tokens, validator) -> Dict`
Generate and parse JSON output from a prompt.

#### `generate_with_fallback(prompt, fallback_fn, temperature, max_output_tokens) -> T`
Generate with a fallback function if LLM fails.

#### `validate_api_key() -> bool`
Validate that the API key is working.

### LLMResponse

Dataclass containing:
- `text`: Generated text
- `prompt_tokens`: Number of tokens in prompt
- `completion_tokens`: Number of tokens in completion
- `total_tokens`: Total tokens used
- `model`: Model name used
- `finish_reason`: Reason generation stopped
- `raw_response`: Raw API response object

### Helper Functions

#### `get_gemini_client(api_key, model_name) -> GeminiClient`
Get or create a singleton Gemini client instance.

#### `retry_with_backoff(max_retries, base_delay, max_delay, retryable_exceptions)`
Decorator for retrying functions with exponential backoff.
