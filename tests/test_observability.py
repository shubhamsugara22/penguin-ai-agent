"""Tests for observability infrastructure."""

import pytest
import time
from src.observability import (
    MetricsCollector,
    get_metrics_collector,
    reset_metrics_collector,
    APICallMetric,
    AnalysisMetric,
    SuggestionMetric,
    TokenUsageMetric
)


class TestMetricsCollector:
    """Test suite for MetricsCollector class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_metrics_collector()
        self.collector = get_metrics_collector()
    
    def teardown_method(self):
        """Clean up after tests."""
        reset_metrics_collector()
    
    def test_start_session(self):
        """Test session start tracking."""
        self.collector.start_session()
        duration = self.collector.get_session_duration_seconds()
        assert duration >= 0
    
    def test_record_analysis_duration(self):
        """Test recording analysis duration."""
        self.collector.record_analysis_duration('test/repo', 1500.0, success=True)
        
        assert self.collector._repos_analyzed == 1
        assert len(self.collector._analysis_metrics) == 1
        assert self.collector._analysis_metrics[0].repository == 'test/repo'
        assert self.collector._analysis_metrics[0].duration_ms == 1500.0
        assert self.collector._analysis_metrics[0].success is True
    
    def test_record_analysis_duration_failure(self):
        """Test recording failed analysis."""
        self.collector.record_analysis_duration('test/repo', 500.0, success=False, error='API error')
        
        assert self.collector._repos_analyzed == 0  # Failed analyses don't count
        assert len(self.collector._analysis_metrics) == 1
        assert self.collector._analysis_metrics[0].success is False
        assert self.collector._analysis_metrics[0].error == 'API error'
    
    def test_record_suggestion_generated(self):
        """Test recording suggestion generation."""
        self.collector.record_suggestion_generated('test/repo', 'bug', 'high')
        
        assert self.collector._suggestions_generated == 1
        assert len(self.collector._suggestion_metrics) == 1
        assert self.collector._suggestion_metrics[0].category == 'bug'
        assert self.collector._suggestion_metrics[0].priority == 'high'
    
    def test_record_issue_created(self):
        """Test recording issue creation."""
        self.collector.record_issue_created()
        assert self.collector._issues_created == 1
        
        self.collector.record_issue_created()
        assert self.collector._issues_created == 2
    
    def test_record_user_approval(self):
        """Test recording user approvals and rejections."""
        self.collector.record_user_approval(True)
        self.collector.record_user_approval(True)
        self.collector.record_user_approval(False)
        
        assert self.collector._user_approvals == 2
        assert self.collector._user_rejections == 1
    
    def test_record_api_call(self):
        """Test recording API calls."""
        self.collector.record_api_call('github', 'list_repos', 250.0, success=True)
        self.collector.record_api_call('gemini', 'generate_content', 1500.0, success=True)
        
        assert len(self.collector._api_call_metrics) == 2
        assert self.collector._github_api_calls == 1
        assert self.collector._gemini_api_calls == 1
    
    def test_record_api_call_failure(self):
        """Test recording failed API calls."""
        self.collector.record_api_call('github', 'get_repo', 100.0, success=False, error='404')
        
        assert len(self.collector._api_call_metrics) == 1
        assert self.collector._api_call_metrics[0].success is False
        assert self.collector._api_call_metrics[0].error == '404'
    
    def test_record_token_usage(self):
        """Test recording token usage."""
        self.collector.record_token_usage('gemini-1.5-flash', 1000, 500)
        
        assert len(self.collector._token_usage_metrics) == 1
        assert self.collector._token_usage_metrics[0].prompt_tokens == 1000
        assert self.collector._token_usage_metrics[0].completion_tokens == 500
        assert self.collector._token_usage_metrics[0].total_tokens == 1500
    
    def test_record_error(self):
        """Test recording errors."""
        self.collector.record_error('github_api_error')
        self.collector.record_error('github_api_error')
        self.collector.record_error('llm_error')
        
        assert self.collector._error_counts['github_api_error'] == 2
        assert self.collector._error_counts['llm_error'] == 1
    
    def test_record_recovery(self):
        """Test recording error recoveries."""
        self.collector.record_recovery('fallback_health_assessment')
        self.collector.record_recovery('retry_api_call')
        
        assert self.collector._recovery_counts['fallback_health_assessment'] == 1
        assert self.collector._recovery_counts['retry_api_call'] == 1
    
    def test_get_average_analysis_duration(self):
        """Test calculating average analysis duration."""
        self.collector.record_analysis_duration('repo1', 1000.0, success=True)
        self.collector.record_analysis_duration('repo2', 2000.0, success=True)
        self.collector.record_analysis_duration('repo3', 500.0, success=False)  # Should be excluded
        
        avg = self.collector.get_average_analysis_duration()
        assert avg == 1500.0
    
    def test_get_average_api_latency(self):
        """Test calculating average API latency."""
        self.collector.record_api_call('github', 'endpoint1', 100.0, success=True)
        self.collector.record_api_call('github', 'endpoint2', 200.0, success=True)
        self.collector.record_api_call('gemini', 'endpoint3', 1000.0, success=True)
        
        # All services
        avg_all = self.collector.get_average_api_latency()
        assert avg_all == pytest.approx(433.33, rel=0.01)
        
        # GitHub only
        avg_github = self.collector.get_average_api_latency('github')
        assert avg_github == 150.0
        
        # Gemini only
        avg_gemini = self.collector.get_average_api_latency('gemini')
        assert avg_gemini == 1000.0
    
    def test_get_error_rate(self):
        """Test calculating error rate."""
        # Add some successful operations
        self.collector.record_analysis_duration('repo1', 1000.0, success=True)
        self.collector.record_api_call('github', 'endpoint', 100.0, success=True)
        
        # Add some errors
        self.collector.record_error('error1')
        
        # Error rate = 1 error / 2 operations = 50%
        error_rate = self.collector.get_error_rate()
        assert error_rate == 50.0
    
    def test_get_recovery_success_rate(self):
        """Test calculating recovery success rate."""
        self.collector.record_error('error1')
        self.collector.record_error('error2')
        self.collector.record_error('error3')
        
        self.collector.record_recovery('recovery1')
        self.collector.record_recovery('recovery2')
        
        # Recovery rate = 2 recoveries / 3 errors = 66.67%
        recovery_rate = self.collector.get_recovery_success_rate()
        assert recovery_rate == pytest.approx(66.67, rel=0.01)
    
    def test_get_user_approval_rate(self):
        """Test calculating user approval rate."""
        self.collector.record_user_approval(True)
        self.collector.record_user_approval(True)
        self.collector.record_user_approval(True)
        self.collector.record_user_approval(False)
        
        # Approval rate = 3 approvals / 4 decisions = 75%
        approval_rate = self.collector.get_user_approval_rate()
        assert approval_rate == 75.0
    
    def test_get_total_tokens_used(self):
        """Test calculating total tokens used."""
        self.collector.record_token_usage('model1', 1000, 500)
        self.collector.record_token_usage('model2', 2000, 1000)
        
        total = self.collector.get_total_tokens_used()
        assert total == 4500
    
    def test_get_estimated_cost(self):
        """Test calculating estimated cost."""
        self.collector.record_token_usage('model1', 1000, 500)  # 1500 tokens
        
        # Default cost: $0.001 per 1k tokens
        cost = self.collector.get_estimated_cost()
        assert cost == pytest.approx(0.0015, rel=0.01)
        
        # Custom cost: $0.002 per 1k tokens
        cost_custom = self.collector.get_estimated_cost(cost_per_1k_tokens=0.002)
        assert cost_custom == pytest.approx(0.003, rel=0.01)
    
    def test_get_suggestions_by_category(self):
        """Test getting suggestion counts by category."""
        self.collector.record_suggestion_generated('repo1', 'bug', 'high')
        self.collector.record_suggestion_generated('repo2', 'bug', 'medium')
        self.collector.record_suggestion_generated('repo3', 'documentation', 'low')
        
        by_category = self.collector.get_suggestions_by_category()
        assert by_category['bug'] == 2
        assert by_category['documentation'] == 1
    
    def test_get_suggestions_by_priority(self):
        """Test getting suggestion counts by priority."""
        self.collector.record_suggestion_generated('repo1', 'bug', 'high')
        self.collector.record_suggestion_generated('repo2', 'enhancement', 'high')
        self.collector.record_suggestion_generated('repo3', 'documentation', 'low')
        
        by_priority = self.collector.get_suggestions_by_priority()
        assert by_priority['high'] == 2
        assert by_priority['low'] == 1
    
    def test_get_session_summary(self):
        """Test getting complete session summary."""
        self.collector.start_session()
        
        # Add various metrics
        self.collector.record_analysis_duration('repo1', 1000.0, success=True)
        self.collector.record_suggestion_generated('repo1', 'bug', 'high')
        self.collector.record_issue_created()
        self.collector.record_api_call('github', 'endpoint', 100.0, success=True)
        self.collector.record_token_usage('gemini', 1000, 500)
        self.collector.record_user_approval(True)
        
        summary = self.collector.get_session_summary()
        
        # Check structure
        assert 'performance' in summary
        assert 'usage' in summary
        assert 'quality' in summary
        assert 'cost' in summary
        assert 'breakdown' in summary
        
        # Check values
        assert summary['usage']['repos_analyzed'] == 1
        assert summary['usage']['suggestions_generated'] == 1
        assert summary['usage']['issues_created'] == 1
        assert summary['cost']['total_tokens_used'] == 1500
        assert summary['cost']['github_api_calls'] == 1
    
    def test_reset(self):
        """Test resetting metrics."""
        # Add some metrics
        self.collector.record_analysis_duration('repo1', 1000.0, success=True)
        self.collector.record_suggestion_generated('repo1', 'bug', 'high')
        self.collector.record_issue_created()
        
        # Reset
        self.collector.reset()
        
        # Verify everything is cleared
        assert self.collector._repos_analyzed == 0
        assert self.collector._suggestions_generated == 0
        assert self.collector._issues_created == 0
        assert len(self.collector._analysis_metrics) == 0
        assert len(self.collector._suggestion_metrics) == 0
        assert len(self.collector._api_call_metrics) == 0
    
    def test_thread_safety(self):
        """Test that metrics collector is thread-safe."""
        import threading
        
        def record_metrics():
            for _ in range(100):
                self.collector.record_suggestion_generated('repo', 'bug', 'high')
        
        threads = [threading.Thread(target=record_metrics) for _ in range(10)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have exactly 1000 suggestions (10 threads * 100 each)
        assert self.collector._suggestions_generated == 1000
    
    def test_global_metrics_collector(self):
        """Test global metrics collector instance."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        
        # Should be the same instance
        assert collector1 is collector2
        
        # Reset and get new instance
        reset_metrics_collector()
        collector3 = get_metrics_collector()
        
        # Should be a different instance
        assert collector1 is not collector3


class TestDataClasses:
    """Test suite for metric data classes."""
    
    def test_api_call_metric(self):
        """Test APICallMetric data class."""
        metric = APICallMetric(
            service='github',
            endpoint='list_repos',
            duration_ms=250.0,
            success=True
        )
        
        assert metric.service == 'github'
        assert metric.endpoint == 'list_repos'
        assert metric.duration_ms == 250.0
        assert metric.success is True
        assert metric.error is None
        
        # Test to_dict
        data = metric.to_dict()
        assert data['service'] == 'github'
        assert data['endpoint'] == 'list_repos'
        assert 'timestamp' in data
    
    def test_analysis_metric(self):
        """Test AnalysisMetric data class."""
        metric = AnalysisMetric(
            repository='test/repo',
            duration_ms=1500.0,
            success=True
        )
        
        assert metric.repository == 'test/repo'
        assert metric.duration_ms == 1500.0
        assert metric.success is True
        
        # Test to_dict
        data = metric.to_dict()
        assert data['repository'] == 'test/repo'
        assert 'timestamp' in data
    
    def test_suggestion_metric(self):
        """Test SuggestionMetric data class."""
        metric = SuggestionMetric(
            repository='test/repo',
            category='bug',
            priority='high'
        )
        
        assert metric.repository == 'test/repo'
        assert metric.category == 'bug'
        assert metric.priority == 'high'
        
        # Test to_dict
        data = metric.to_dict()
        assert data['category'] == 'bug'
        assert 'timestamp' in data
    
    def test_token_usage_metric(self):
        """Test TokenUsageMetric data class."""
        metric = TokenUsageMetric(
            model='gemini-1.5-flash',
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500
        )
        
        assert metric.model == 'gemini-1.5-flash'
        assert metric.prompt_tokens == 1000
        assert metric.completion_tokens == 500
        assert metric.total_tokens == 1500
        
        # Test to_dict
        data = metric.to_dict()
        assert data['model'] == 'gemini-1.5-flash'
        assert data['total_tokens'] == 1500
        assert 'timestamp' in data
