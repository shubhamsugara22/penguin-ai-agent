# Observability Infrastructure

This document describes the observability infrastructure implemented for the GitHub Maintainer Agent.

## Overview

The observability infrastructure provides comprehensive tracking of metrics, structured logging with credential sanitization, and session monitoring capabilities. It enables developers to understand system behavior, track performance, identify issues, and optimize costs.

## Components

### 1. MetricsCollector

The `MetricsCollector` class is the core component for tracking metrics throughout the agent workflow.

**Location**: `src/observability.py`

**Features**:
- Thread-safe metric collection using RLock
- Performance metrics (analysis duration, API latency)
- Usage metrics (repos analyzed, suggestions generated, issues created)
- Quality metrics (error rates, recovery rates)
- Cost metrics (token usage, API calls, estimated costs)
- Session tracking and aggregation

**Usage**:
```python
from src.observability import get_metrics_collector

# Get the global metrics collector
metrics = get_metrics_collector()

# Start a session
metrics.start_session()

# Record metrics
metrics.record_analysis_duration('owner/repo', 1500.0, success=True)
metrics.record_suggestion_generated('owner/repo', 'bug', 'high')
metrics.record_issue_created()
metrics.record_api_call('github', 'list_repos', 250.0, success=True)
metrics.record_token_usage('gemini-1.5-flash', 1000, 500)

# Get session summary
summary = metrics.get_session_summary()
print(f"Repos analyzed: {summary['usage']['repos_analyzed']}")
print(f"Total cost: ${summary['cost']['estimated_cost_usd']:.4f}")
```

### 2. Structured Logging

The logging infrastructure provides JSON-formatted logs with automatic credential sanitization.

**Location**: `src/logging_config.py`

**Features**:
- JSON-formatted structured logs
- Automatic credential sanitization (GitHub tokens, API keys)
- Context-aware logging with agent, event, and repository information
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Sanitization of sensitive data in log messages and exceptions

**Usage**:
```python
from src.logging_config import setup_logging, get_logger

# Setup logging (typically done once at application start)
setup_logging('INFO')

# Get a logger
logger = get_logger(__name__)

# Log with structured data
logger.info(
    "Analyzing repository",
    extra={
        'agent': 'AnalyzerAgent',
        'event': 'analyze_start',
        'repository': 'owner/repo',
        'extra_data': {'health_score': 0.85}
    }
)

# Credentials are automatically sanitized
logger.info(f"Using token: {token}")  # Token will be [REDACTED] in logs
```

### 3. Credential Sanitization

The `CredentialSanitizer` class ensures sensitive information never appears in logs.

**Patterns Detected**:
- GitHub personal access tokens (ghp_*)
- GitHub OAuth tokens (gho_*)
- GitHub server tokens (ghs_*)
- GitHub fine-grained tokens (github_pat_*)
- Google API keys (AIza*)
- Bearer tokens
- Common credential field names (token, api_key, password, secret, authorization)

**Usage**:
```python
from src.logging_config import CredentialSanitizer

# Sanitize a string
sanitized = CredentialSanitizer.sanitize("Token: ghp_1234567890abcdef")
# Result: "Token: [REDACTED]"

# Sanitize a dictionary
data = {
    'token': 'ghp_secret',
    'repo': 'owner/repo',
    'api_key': 'AIza1234'
}
sanitized_data = CredentialSanitizer.sanitize_dict(data)
# Result: {'token': '[REDACTED]', 'repo': 'owner/repo', 'api_key': '[REDACTED]'}
```

## Integration with Agents

### GitHub Tools

All GitHub API tools (`list_repos`, `get_repo_overview`, `get_repo_history`, `create_issue`) include:
- Structured logging with event tracking
- API call duration metrics
- Success/failure tracking
- Error recording and recovery metrics

### Analyzer Agent

The Analyzer Agent includes:
- Repository analysis duration tracking
- LLM API call metrics
- Token usage tracking
- Health snapshot generation metrics
- Fallback recovery tracking

### Maintainer Agent

The Maintainer Agent includes:
- Suggestion generation metrics
- Category and priority tracking
- Deduplication metrics
- Issue creation tracking
- LLM API call and token usage metrics

### Coordinator Agent

The Coordinator Agent includes:
- Workflow orchestration metrics
- Session lifecycle tracking
- Progress event emission
- End-to-end workflow metrics
- Error aggregation

## Metrics Summary Structure

The `get_session_summary()` method returns a comprehensive dictionary with the following structure:

```python
{
    'performance': {
        'session_duration_seconds': float,
        'average_analysis_duration_ms': float,
        'average_github_api_latency_ms': float,
        'average_gemini_api_latency_ms': float,
    },
    'usage': {
        'repos_analyzed': int,
        'suggestions_generated': int,
        'issues_created': int,
        'user_approvals': int,
        'user_rejections': int,
        'approval_rate_percent': float,
    },
    'quality': {
        'error_rate_percent': float,
        'recovery_success_rate_percent': float,
        'error_counts_by_type': Dict[str, int],
        'recovery_counts_by_type': Dict[str, int],
    },
    'cost': {
        'total_tokens_used': int,
        'github_api_calls': int,
        'gemini_api_calls': int,
        'estimated_cost_usd': float,
    },
    'breakdown': {
        'suggestions_by_category': Dict[str, int],
        'suggestions_by_priority': Dict[str, int],
    }
}
```

## Log Format

Logs are output in JSON format with the following structure:

```json
{
    "timestamp": "2025-11-29T12:00:00.000000Z",
    "level": "INFO",
    "logger": "src.agents.analyzer",
    "message": "Analyzing repository: owner/repo",
    "agent": "AnalyzerAgent",
    "event": "analyze_repository_start",
    "repository": "owner/repo",
    "metrics": {
        "duration_ms": 1500.0,
        "health_score": 0.85
    }
}
```

## Best Practices

### 1. Always Use Structured Logging

Instead of:
```python
logger.info(f"Analyzed {repo} in {duration}ms")
```

Use:
```python
logger.info(
    f"Analyzed {repo}",
    extra={
        'event': 'analysis_complete',
        'repository': repo,
        'metrics': {'duration_ms': duration}
    }
)
```

### 2. Record Metrics at Key Points

- Start of operations (for timing)
- End of operations (for success/failure)
- API calls (for latency and cost tracking)
- User interactions (for approval rates)
- Errors and recoveries (for quality metrics)

### 3. Use Appropriate Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General informational messages about workflow progress
- **WARNING**: Recoverable errors or degraded functionality
- **ERROR**: Unrecoverable errors that prevent operation completion
- **CRITICAL**: System-level failures

### 4. Include Context in Logs

Always include:
- Agent name (which agent is logging)
- Event type (what is happening)
- Repository name (if applicable)
- Relevant metrics or data

### 5. Never Log Sensitive Data

The sanitizer will catch most cases, but avoid logging:
- Full tokens or API keys
- User passwords
- Personal information
- Internal system details that could be security risks

## Testing

Run the verification script to test the observability infrastructure:

```bash
python verify_observability.py
```

Or run the comprehensive test:

```bash
python test_observability_simple.py
cat observability_test_results.txt
```

## Monitoring and Dashboards

The metrics collected can be used to build monitoring dashboards that track:

1. **Performance Dashboard**
   - Average analysis time per repository
   - API latency trends
   - Throughput (repos/minute)

2. **Quality Dashboard**
   - Error rates by type
   - Recovery success rates
   - User approval rates

3. **Cost Dashboard**
   - Token usage trends
   - API call volumes
   - Estimated costs over time

4. **Usage Dashboard**
   - Repositories analyzed
   - Suggestions generated
   - Issues created
   - Active sessions

## Future Enhancements

Potential improvements to the observability infrastructure:

1. **Persistent Metrics Storage**: Store metrics in a database for historical analysis
2. **Real-time Monitoring**: Stream metrics to monitoring services (Prometheus, Datadog)
3. **Alerting**: Set up alerts for error rates, high costs, or performance degradation
4. **Distributed Tracing**: Add trace IDs for tracking requests across services
5. **Custom Metrics**: Allow agents to define custom metrics for specific use cases
6. **Metrics Visualization**: Build web-based dashboards for real-time monitoring

## Requirements Validation

This implementation satisfies the following requirements:

- **8.1**: Agents log decisions and tool calls with structured logging
- **8.2**: Tools log invocations with parameters and results
- **8.3**: Session metrics are recorded and aggregated
- **8.4**: Detailed error information is logged for debugging
- **11.4**: Credentials are sanitized in all logs using pattern matching

## Conclusion

The observability infrastructure provides comprehensive visibility into the GitHub Maintainer Agent's behavior, performance, and costs. It enables developers to monitor, debug, and optimize the system effectively while ensuring security through automatic credential sanitization.
