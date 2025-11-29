"""Demo script to test observability infrastructure."""

import json
from src.observability import get_metrics_collector, reset_metrics_collector
from src.logging_config import setup_logging, get_logger

# Setup logging
setup_logging('INFO')
logger = get_logger(__name__)

# Reset and get metrics collector
reset_metrics_collector()
metrics = get_metrics_collector()

# Start a session
metrics.start_session()
logger.info("Starting observability demo")

# Simulate repository analysis
logger.info("Simulating repository analysis", extra={
    'agent': 'AnalyzerAgent',
    'event': 'analyze_start',
    'repository': 'test/repo1'
})
metrics.record_analysis_duration('test/repo1', 1500.0, success=True)

logger.info("Simulating repository analysis", extra={
    'agent': 'AnalyzerAgent',
    'event': 'analyze_start',
    'repository': 'test/repo2'
})
metrics.record_analysis_duration('test/repo2', 2000.0, success=True)

# Simulate API calls
metrics.record_api_call('github', 'list_repos', 250.0, success=True)
metrics.record_api_call('github', 'get_repo_overview', 300.0, success=True)
metrics.record_api_call('gemini', 'generate_health_snapshot', 1500.0, success=True)

# Simulate token usage
metrics.record_token_usage('gemini-1.5-flash', 1000, 500)
metrics.record_token_usage('gemini-1.5-flash', 2000, 800)

# Simulate suggestion generation
logger.info("Generating suggestions", extra={
    'agent': 'MaintainerAgent',
    'event': 'generate_suggestions'
})
metrics.record_suggestion_generated('test/repo1', 'bug', 'high')
metrics.record_suggestion_generated('test/repo1', 'documentation', 'medium')
metrics.record_suggestion_generated('test/repo2', 'enhancement', 'low')

# Simulate user approvals
metrics.record_user_approval(True)
metrics.record_user_approval(True)
metrics.record_user_approval(False)

# Simulate issue creation
logger.info("Creating GitHub issues", extra={
    'agent': 'MaintainerAgent',
    'event': 'create_issues'
})
metrics.record_issue_created()
metrics.record_issue_created()

# Simulate an error and recovery
metrics.record_error('github_api_error')
metrics.record_recovery('retry_api_call')

# Get session summary
summary = metrics.get_session_summary()

# Print results
print("\n" + "="*60)
print("OBSERVABILITY INFRASTRUCTURE DEMO")
print("="*60)

print("\n📊 PERFORMANCE METRICS:")
print(f"  Session Duration: {summary['performance']['session_duration_seconds']:.2f}s")
print(f"  Avg Analysis Duration: {summary['performance']['average_analysis_duration_ms']:.2f}ms")
print(f"  Avg GitHub API Latency: {summary['performance']['average_github_api_latency_ms']:.2f}ms")
print(f"  Avg Gemini API Latency: {summary['performance']['average_gemini_api_latency_ms']:.2f}ms")

print("\n📈 USAGE METRICS:")
print(f"  Repositories Analyzed: {summary['usage']['repos_analyzed']}")
print(f"  Suggestions Generated: {summary['usage']['suggestions_generated']}")
print(f"  Issues Created: {summary['usage']['issues_created']}")
print(f"  User Approvals: {summary['usage']['user_approvals']}")
print(f"  User Rejections: {summary['usage']['user_rejections']}")
print(f"  Approval Rate: {summary['usage']['approval_rate_percent']:.1f}%")

print("\n✅ QUALITY METRICS:")
print(f"  Error Rate: {summary['quality']['error_rate_percent']:.1f}%")
print(f"  Recovery Success Rate: {summary['quality']['recovery_success_rate_percent']:.1f}%")
print(f"  Errors by Type: {summary['quality']['error_counts_by_type']}")
print(f"  Recoveries by Type: {summary['quality']['recovery_counts_by_type']}")

print("\n💰 COST METRICS:")
print(f"  Total Tokens Used: {summary['cost']['total_tokens_used']:,}")
print(f"  GitHub API Calls: {summary['cost']['github_api_calls']}")
print(f"  Gemini API Calls: {summary['cost']['gemini_api_calls']}")
print(f"  Estimated Cost: ${summary['cost']['estimated_cost_usd']:.4f}")

print("\n📋 BREAKDOWN:")
print(f"  Suggestions by Category: {summary['breakdown']['suggestions_by_category']}")
print(f"  Suggestions by Priority: {summary['breakdown']['suggestions_by_priority']}")

print("\n" + "="*60)
print("✅ Observability infrastructure is working correctly!")
print("="*60)

logger.info("Observability demo complete", extra={
    'event': 'demo_complete',
    'metrics': summary
})
