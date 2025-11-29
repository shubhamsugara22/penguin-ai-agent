"""Verify observability infrastructure works."""

import sys
sys.path.insert(0, 'src')

from observability import MetricsCollector

print("Testing MetricsCollector...")

# Create collector
m = MetricsCollector()
m.start_session()

# Record some metrics
m.record_analysis_duration('test/repo', 1000.0, success=True)
m.record_suggestion_generated('test/repo', 'bug', 'high')
m.record_issue_created()
m.record_api_call('github', 'test', 100.0, success=True)
m.record_token_usage('gemini', 1000, 500)

# Get summary
summary = m.get_session_summary()

print("SUCCESS: MetricsCollector is working!")
print(f"  Repos analyzed: {summary['usage']['repos_analyzed']}")
print(f"  Suggestions: {summary['usage']['suggestions_generated']}")
print(f"  Issues created: {summary['usage']['issues_created']}")
print(f"  Total tokens: {summary['cost']['total_tokens_used']}")
print(f"  GitHub API calls: {summary['cost']['github_api_calls']}")
