"""Observability infrastructure for tracking metrics and performance.

This module provides the MetricsCollector class for tracking various metrics
throughout the agent workflow, including performance, usage, quality, and cost metrics.
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import threading


@dataclass
class APICallMetric:
    """Metric for a single API call."""
    service: str  # 'github' or 'gemini'
    endpoint: str
    duration_ms: float
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'service': self.service,
            'endpoint': self.endpoint,
            'duration_ms': self.duration_ms,
            'success': self.success,
            'timestamp': self.timestamp.isoformat(),
            'error': self.error
        }


@dataclass
class AnalysisMetric:
    """Metric for repository analysis."""
    repository: str
    duration_ms: float
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'repository': self.repository,
            'duration_ms': self.duration_ms,
            'success': self.success,
            'timestamp': self.timestamp.isoformat(),
            'error': self.error
        }


@dataclass
class SuggestionMetric:
    """Metric for suggestion generation."""
    repository: str
    category: str
    priority: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'repository': self.repository,
            'category': self.category,
            'priority': self.priority,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class TokenUsageMetric:
    """Metric for LLM token usage."""
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'model': self.model,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens,
            'timestamp': self.timestamp.isoformat()
        }


class MetricsCollector:
    """Collector for tracking metrics throughout the agent workflow.
    
    This class is thread-safe and can be used across multiple agents
    and concurrent operations.
    """
    
    def __init__(self):
        """Initialize the metrics collector."""
        self._lock = threading.RLock()  # Use RLock for reentrant locking
        
        # Performance metrics
        self._analysis_metrics: List[AnalysisMetric] = []
        self._api_call_metrics: List[APICallMetric] = []
        
        # Usage metrics
        self._suggestion_metrics: List[SuggestionMetric] = []
        self._repos_analyzed: int = 0
        self._suggestions_generated: int = 0
        self._issues_created: int = 0
        self._user_approvals: int = 0
        self._user_rejections: int = 0
        
        # Quality metrics
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._recovery_counts: Dict[str, int] = defaultdict(int)
        
        # Cost metrics
        self._token_usage_metrics: List[TokenUsageMetric] = []
        self._github_api_calls: int = 0
        self._gemini_api_calls: int = 0
        
        # Session tracking
        self._session_start_time: Optional[float] = None
    
    def start_session(self) -> None:
        """Mark the start of a session."""
        with self._lock:
            self._session_start_time = time.time()
    
    def record_analysis_duration(self, repo: str, duration_ms: float, success: bool = True, error: Optional[str] = None) -> None:
        """Record time taken to analyze a repository.
        
        Args:
            repo: Repository full name
            duration_ms: Duration in milliseconds
            success: Whether analysis succeeded
            error: Optional error message if failed
        """
        with self._lock:
            metric = AnalysisMetric(
                repository=repo,
                duration_ms=duration_ms,
                success=success,
                error=error
            )
            self._analysis_metrics.append(metric)
            
            if success:
                self._repos_analyzed += 1
    
    def record_suggestion_generated(self, repo: str, category: str, priority: str) -> None:
        """Record a generated suggestion.
        
        Args:
            repo: Repository full name
            category: Suggestion category
            priority: Suggestion priority
        """
        with self._lock:
            metric = SuggestionMetric(
                repository=repo,
                category=category,
                priority=priority
            )
            self._suggestion_metrics.append(metric)
            self._suggestions_generated += 1
    
    def record_issue_created(self) -> None:
        """Record a created GitHub issue."""
        with self._lock:
            self._issues_created += 1
    
    def record_user_approval(self, approved: bool) -> None:
        """Record user approval or rejection of a suggestion.
        
        Args:
            approved: True if approved, False if rejected
        """
        with self._lock:
            if approved:
                self._user_approvals += 1
            else:
                self._user_rejections += 1
    
    def record_api_call(
        self,
        service: str,
        endpoint: str,
        duration_ms: float,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """Record an API call.
        
        Args:
            service: Service name ('github' or 'gemini')
            endpoint: API endpoint
            duration_ms: Duration in milliseconds
            success: Whether call succeeded
            error: Optional error message if failed
        """
        with self._lock:
            metric = APICallMetric(
                service=service,
                endpoint=endpoint,
                duration_ms=duration_ms,
                success=success,
                error=error
            )
            self._api_call_metrics.append(metric)
            
            # Track API call counts
            if service == 'github':
                self._github_api_calls += 1
            elif service == 'gemini':
                self._gemini_api_calls += 1
    
    def record_token_usage(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> None:
        """Record LLM token usage.
        
        Args:
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
        """
        with self._lock:
            metric = TokenUsageMetric(
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            )
            self._token_usage_metrics.append(metric)
    
    def record_error(self, error_type: str) -> None:
        """Record an error occurrence.
        
        Args:
            error_type: Type/category of error
        """
        with self._lock:
            self._error_counts[error_type] += 1
    
    def record_recovery(self, recovery_type: str) -> None:
        """Record a successful error recovery.
        
        Args:
            recovery_type: Type of recovery performed
        """
        with self._lock:
            self._recovery_counts[recovery_type] += 1
    
    def get_session_duration_seconds(self) -> float:
        """Get the current session duration in seconds.
        
        Returns:
            Duration in seconds, or 0 if session not started
        """
        with self._lock:
            if self._session_start_time is None:
                return 0.0
            return time.time() - self._session_start_time
    
    def get_average_analysis_duration(self) -> float:
        """Get average repository analysis duration in milliseconds.
        
        Returns:
            Average duration in milliseconds, or 0 if no analyses
        """
        with self._lock:
            if not self._analysis_metrics:
                return 0.0
            
            successful_analyses = [m for m in self._analysis_metrics if m.success]
            if not successful_analyses:
                return 0.0
            
            total_duration = sum(m.duration_ms for m in successful_analyses)
            return total_duration / len(successful_analyses)
    
    def get_average_api_latency(self, service: Optional[str] = None) -> float:
        """Get average API call latency in milliseconds.
        
        Args:
            service: Optional service filter ('github' or 'gemini')
            
        Returns:
            Average latency in milliseconds, or 0 if no calls
        """
        with self._lock:
            metrics = self._api_call_metrics
            
            if service:
                metrics = [m for m in metrics if m.service == service]
            
            if not metrics:
                return 0.0
            
            successful_calls = [m for m in metrics if m.success]
            if not successful_calls:
                return 0.0
            
            total_duration = sum(m.duration_ms for m in successful_calls)
            return total_duration / len(successful_calls)
    
    def get_error_rate(self) -> float:
        """Get overall error rate as a percentage.
        
        Returns:
            Error rate (0.0 to 100.0)
        """
        with self._lock:
            total_operations = (
                len(self._analysis_metrics) +
                len(self._api_call_metrics)
            )
            
            if total_operations == 0:
                return 0.0
            
            total_errors = sum(self._error_counts.values())
            return (total_errors / total_operations) * 100.0
    
    def get_recovery_success_rate(self) -> float:
        """Get error recovery success rate as a percentage.
        
        Returns:
            Recovery success rate (0.0 to 100.0)
        """
        with self._lock:
            total_errors = sum(self._error_counts.values())
            
            if total_errors == 0:
                return 100.0  # No errors means 100% success
            
            total_recoveries = sum(self._recovery_counts.values())
            return (total_recoveries / total_errors) * 100.0
    
    def get_user_approval_rate(self) -> float:
        """Get user approval rate as a percentage.
        
        Returns:
            Approval rate (0.0 to 100.0)
        """
        with self._lock:
            total_decisions = self._user_approvals + self._user_rejections
            
            if total_decisions == 0:
                return 0.0
            
            return (self._user_approvals / total_decisions) * 100.0
    
    def get_total_tokens_used(self) -> int:
        """Get total LLM tokens used.
        
        Returns:
            Total token count
        """
        with self._lock:
            return sum(m.total_tokens for m in self._token_usage_metrics)
    
    def get_estimated_cost(self, cost_per_1k_tokens: float = 0.001) -> float:
        """Get estimated cost based on token usage.
        
        Args:
            cost_per_1k_tokens: Cost per 1000 tokens (default: $0.001)
            
        Returns:
            Estimated cost in dollars
        """
        total_tokens = self.get_total_tokens_used()
        return (total_tokens / 1000.0) * cost_per_1k_tokens
    
    def get_suggestions_by_category(self) -> Dict[str, int]:
        """Get suggestion counts by category.
        
        Returns:
            Dictionary mapping category to count
        """
        with self._lock:
            counts: Dict[str, int] = defaultdict(int)
            for metric in self._suggestion_metrics:
                counts[metric.category] += 1
            return dict(counts)
    
    def get_suggestions_by_priority(self) -> Dict[str, int]:
        """Get suggestion counts by priority.
        
        Returns:
            Dictionary mapping priority to count
        """
        with self._lock:
            counts: Dict[str, int] = defaultdict(int)
            for metric in self._suggestion_metrics:
                counts[metric.priority] += 1
            return dict(counts)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get aggregated metrics for current session.
        
        Returns:
            Dictionary containing session metrics summary
        """
        with self._lock:
            return {
                # Performance metrics
                'performance': {
                    'session_duration_seconds': self.get_session_duration_seconds(),
                    'average_analysis_duration_ms': self.get_average_analysis_duration(),
                    'average_github_api_latency_ms': self.get_average_api_latency('github'),
                    'average_gemini_api_latency_ms': self.get_average_api_latency('gemini'),
                },
                
                # Usage metrics
                'usage': {
                    'repos_analyzed': self._repos_analyzed,
                    'suggestions_generated': self._suggestions_generated,
                    'issues_created': self._issues_created,
                    'user_approvals': self._user_approvals,
                    'user_rejections': self._user_rejections,
                    'approval_rate_percent': self.get_user_approval_rate(),
                },
                
                # Quality metrics
                'quality': {
                    'error_rate_percent': self.get_error_rate(),
                    'recovery_success_rate_percent': self.get_recovery_success_rate(),
                    'error_counts_by_type': dict(self._error_counts),
                    'recovery_counts_by_type': dict(self._recovery_counts),
                },
                
                # Cost metrics
                'cost': {
                    'total_tokens_used': self.get_total_tokens_used(),
                    'github_api_calls': self._github_api_calls,
                    'gemini_api_calls': self._gemini_api_calls,
                    'estimated_cost_usd': self.get_estimated_cost(),
                },
                
                # Breakdown metrics
                'breakdown': {
                    'suggestions_by_category': self.get_suggestions_by_category(),
                    'suggestions_by_priority': self.get_suggestions_by_priority(),
                }
            }
    
    def reset(self) -> None:
        """Reset all metrics (useful for testing or new sessions)."""
        with self._lock:
            self._analysis_metrics.clear()
            self._api_call_metrics.clear()
            self._suggestion_metrics.clear()
            self._token_usage_metrics.clear()
            
            self._repos_analyzed = 0
            self._suggestions_generated = 0
            self._issues_created = 0
            self._user_approvals = 0
            self._user_rejections = 0
            
            self._error_counts.clear()
            self._recovery_counts.clear()
            
            self._github_api_calls = 0
            self._gemini_api_calls = 0
            
            self._session_start_time = None


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance.
    
    Returns:
        MetricsCollector: The global metrics collector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def reset_metrics_collector() -> None:
    """Reset the global metrics collector instance (useful for testing)."""
    global _metrics_collector
    if _metrics_collector is not None:
        _metrics_collector.reset()
    _metrics_collector = None
