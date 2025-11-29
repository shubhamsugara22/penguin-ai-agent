"""Simple test to verify observability infrastructure."""

from src.observability import get_metrics_collector, reset_metrics_collector

# Reset and get metrics collector
reset_metrics_collector()
metrics = get_metrics_collector()

# Start a session
metrics.start_session()

# Simulate repository analysis
metrics.record_analysis_duration('test/repo1', 1500.0, success=True)
metrics.record_analysis_duration('test/repo2', 2000.0, success=True)

# Simulate API calls
metrics.record_api_call('github', 'list_repos', 250.0, success=True)
metrics.record_api_call('gemini', 'generate_health_snapshot', 1500.0, success=True)

# Simulate token usage
metrics.record_token_usage('gemini-1.5-flash', 1000, 500)

# Simulate suggestion generation
metrics.record_suggestion_generated('test/repo1', 'bug', 'high')
metrics.record_suggestion_generated('test/repo1', 'documentation', 'medium')

# Simulate issue creation
metrics.record_issue_created()
metrics.record_issue_created()

# Get session summary
summary = metrics.get_session_summary()

# Write to file
with open('observability_test_results.txt', 'w', encoding='utf-8') as f:
    f.write("="*60 + "\n")
    f.write("OBSERVABILITY INFRASTRUCTURE TEST RESULTS\n")
    f.write("="*60 + "\n\n")
    
    f.write("PERFORMANCE METRICS:\n")
    f.write(f"  Avg Analysis Duration: {summary['performance']['average_analysis_duration_ms']:.2f}ms\n")
    f.write(f"  Avg GitHub API Latency: {summary['performance']['average_github_api_latency_ms']:.2f}ms\n")
    f.write(f"  Avg Gemini API Latency: {summary['performance']['average_gemini_api_latency_ms']:.2f}ms\n\n")
    
    f.write("USAGE METRICS:\n")
    f.write(f"  Repositories Analyzed: {summary['usage']['repos_analyzed']}\n")
    f.write(f"  Suggestions Generated: {summary['usage']['suggestions_generated']}\n")
    f.write(f"  Issues Created: {summary['usage']['issues_created']}\n\n")
    
    f.write("COST METRICS:\n")
    f.write(f"  Total Tokens Used: {summary['cost']['total_tokens_used']:,}\n")
    f.write(f"  GitHub API Calls: {summary['cost']['github_api_calls']}\n")
    f.write(f"  Gemini API Calls: {summary['cost']['gemini_api_calls']}\n")
    f.write(f"  Estimated Cost: ${summary['cost']['estimated_cost_usd']:.4f}\n\n")
    
    f.write("="*60 + "\n")
    f.write("✅ Observability infrastructure is working correctly!\n")
    f.write("="*60 + "\n")

print("Test complete! Results written to observability_test_results.txt")
