"""Evaluation runner for executing evaluation suite.

This module provides the main evaluation runner that executes
all evaluations and generates reports.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import json

from src.agents.analyzer import AnalyzerAgent
from src.agents.maintainer import MaintainerAgent
from src.models.repository import Repository
from src.models.health import RepositoryProfile
from src.models.maintenance import MaintenanceSuggestion
from src.models.session import UserPreferences
from src.tools.github_client import GitHubClient
from src.memory.memory_bank import MemoryBank
from evaluation.test_dataset import get_test_repositories, TestRepository
from evaluation.evaluators import (
    SuggestionQualityEvaluator,
    DeduplicationEvaluator,
    AnalysisCompletenessEvaluator,
    EvaluationResult
)

logger = logging.getLogger(__name__)


@dataclass
class RepositoryEvaluationResult:
    """Evaluation results for a single repository."""
    
    repository: str
    test_repo: TestRepository
    profile: Optional[RepositoryProfile]
    suggestions: List[MaintenanceSuggestion]
    quality_result: Optional[EvaluationResult]
    completeness_result: Optional[EvaluationResult]
    deduplication_result: Optional[EvaluationResult]
    execution_time_seconds: float
    errors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'repository': self.repository,
            'test_repo': self.test_repo.to_dict(),
            'profile': {
                'purpose': self.profile.purpose if self.profile else None,
                'tech_stack': self.profile.tech_stack if self.profile else [],
                'health_score': self.profile.health.overall_health_score if self.profile else 0.0,
                'activity_level': self.profile.health.activity_level if self.profile else 'unknown'
            } if self.profile else None,
            'suggestions_count': len(self.suggestions),
            'quality_result': self.quality_result.to_dict() if self.quality_result else None,
            'completeness_result': self.completeness_result.to_dict() if self.completeness_result else None,
            'deduplication_result': self.deduplication_result.to_dict() if self.deduplication_result else None,
            'execution_time_seconds': self.execution_time_seconds,
            'errors': self.errors
        }


@dataclass
class EvaluationSummary:
    """Summary of evaluation results."""
    
    total_repositories: int
    successful_evaluations: int
    failed_evaluations: int
    average_quality_score: float
    average_completeness_score: float
    average_deduplication_score: float
    total_execution_time_seconds: float
    timestamp: datetime
    repository_results: List[RepositoryEvaluationResult]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_repositories': self.total_repositories,
            'successful_evaluations': self.successful_evaluations,
            'failed_evaluations': self.failed_evaluations,
            'average_quality_score': self.average_quality_score,
            'average_completeness_score': self.average_completeness_score,
            'average_deduplication_score': self.average_deduplication_score,
            'total_execution_time_seconds': self.total_execution_time_seconds,
            'timestamp': self.timestamp.isoformat(),
            'repository_results': [r.to_dict() for r in self.repository_results]
        }


class EvaluationRunner:
    """Runner for executing evaluation suite."""
    
    def __init__(
        self,
        github_client: Optional[GitHubClient] = None,
        memory_bank: Optional[MemoryBank] = None
    ):
        """Initialize the evaluation runner.
        
        Args:
            github_client: Optional GitHub client instance
            memory_bank: Optional memory bank instance
        """
        self.github_client = github_client or GitHubClient()
        self.memory_bank = memory_bank or MemoryBank()
        
        # Initialize agents
        self.analyzer_agent = AnalyzerAgent(self.github_client)
        self.maintainer_agent = MaintainerAgent(self.memory_bank, self.github_client)
        
        # Initialize evaluators
        self.quality_evaluator = SuggestionQualityEvaluator()
        self.deduplication_evaluator = DeduplicationEvaluator()
        self.completeness_evaluator = AnalysisCompletenessEvaluator()
        
        logger.info("EvaluationRunner initialized")
    
    def run_evaluation(
        self,
        test_repos: Optional[List[TestRepository]] = None,
        run_deduplication_test: bool = True
    ) -> EvaluationSummary:
        """Run complete evaluation suite.
        
        Args:
            test_repos: Optional list of test repositories (uses default if None)
            run_deduplication_test: Whether to run deduplication test
            
        Returns:
            EvaluationSummary with results
        """
        start_time = time.time()
        
        # Get test repositories
        if test_repos is None:
            test_repos = get_test_repositories()
        
        logger.info(f"Starting evaluation with {len(test_repos)} test repositories")
        
        # Evaluate each repository
        results = []
        for test_repo in test_repos:
            result = self._evaluate_repository(test_repo, run_deduplication_test)
            results.append(result)
        
        # Calculate summary statistics
        successful = sum(1 for r in results if not r.errors)
        failed = len(results) - successful
        
        # Calculate average scores
        quality_scores = [
            r.quality_result.score
            for r in results
            if r.quality_result is not None
        ]
        completeness_scores = [
            r.completeness_result.score
            for r in results
            if r.completeness_result is not None
        ]
        deduplication_scores = [
            r.deduplication_result.score
            for r in results
            if r.deduplication_result is not None
        ]
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0.0
        avg_deduplication = sum(deduplication_scores) / len(deduplication_scores) if deduplication_scores else 0.0
        
        total_time = time.time() - start_time
        
        summary = EvaluationSummary(
            total_repositories=len(test_repos),
            successful_evaluations=successful,
            failed_evaluations=failed,
            average_quality_score=avg_quality,
            average_completeness_score=avg_completeness,
            average_deduplication_score=avg_deduplication,
            total_execution_time_seconds=total_time,
            timestamp=datetime.now(),
            repository_results=results
        )
        
        logger.info(
            f"Evaluation complete: {successful}/{len(test_repos)} successful, "
            f"avg quality={avg_quality:.2f}, avg completeness={avg_completeness:.2f}, "
            f"avg deduplication={avg_deduplication:.2f}"
        )
        
        return summary
    
    def _evaluate_repository(
        self,
        test_repo: TestRepository,
        run_deduplication_test: bool
    ) -> RepositoryEvaluationResult:
        """Evaluate a single repository.
        
        Args:
            test_repo: Test repository to evaluate
            run_deduplication_test: Whether to run deduplication test
            
        Returns:
            RepositoryEvaluationResult
        """
        start_time = time.time()
        errors = []
        
        logger.info(f"Evaluating repository: {test_repo.full_name}")
        
        # Create Repository object
        repo = Repository(
            name=test_repo.full_name.split('/')[-1],
            full_name=test_repo.full_name,
            owner=test_repo.full_name.split('/')[0],
            url=f"https://github.com/{test_repo.full_name}",
            default_branch='main',
            visibility='public',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Analyze repository
        profile = None
        suggestions = []
        quality_result = None
        completeness_result = None
        deduplication_result = None
        
        try:
            # Run analysis
            analysis = self.analyzer_agent.analyze_repository(repo)
            profile = analysis.profile
            
            # Evaluate completeness
            completeness_result = self.completeness_evaluator.evaluate(
                profile,
                test_repo
            )
            
            # Generate suggestions
            suggestions = self.maintainer_agent.generate_suggestions(
                [profile],
                user_preferences=None
            )
            
            # Evaluate suggestion quality
            quality_result = self.quality_evaluator.evaluate(
                suggestions,
                test_repo,
                profile
            )
            
            # Run deduplication test if requested
            if run_deduplication_test:
                # Generate suggestions again (simulating second run)
                suggestions_run2 = self.maintainer_agent.generate_suggestions(
                    [profile],
                    user_preferences=None
                )
                
                deduplication_result = self.deduplication_evaluator.evaluate(
                    suggestions,
                    suggestions_run2,
                    repo_changed=False
                )
            
        except Exception as e:
            error_msg = f"Evaluation failed: {e}"
            logger.error(f"Failed to evaluate {test_repo.full_name}: {e}", exc_info=True)
            errors.append(error_msg)
        
        execution_time = time.time() - start_time
        
        return RepositoryEvaluationResult(
            repository=test_repo.full_name,
            test_repo=test_repo,
            profile=profile,
            suggestions=suggestions,
            quality_result=quality_result,
            completeness_result=completeness_result,
            deduplication_result=deduplication_result,
            execution_time_seconds=execution_time,
            errors=errors
        )
    
    def generate_report(
        self,
        summary: EvaluationSummary,
        output_file: Optional[str] = None
    ) -> str:
        """Generate evaluation report.
        
        Args:
            summary: Evaluation summary
            output_file: Optional output file path
            
        Returns:
            Report text
        """
        logger.info("Generating evaluation report")
        
        # Generate report text
        report_lines = [
            "=" * 80,
            "EVALUATION REPORT",
            "=" * 80,
            f"Timestamp: {summary.timestamp.isoformat()}",
            f"Total Repositories: {summary.total_repositories}",
            f"Successful Evaluations: {summary.successful_evaluations}",
            f"Failed Evaluations: {summary.failed_evaluations}",
            f"Total Execution Time: {summary.total_execution_time_seconds:.2f}s",
            "",
            "AVERAGE SCORES",
            "-" * 80,
            f"Suggestion Quality: {summary.average_quality_score:.2f} / 1.00",
            f"Analysis Completeness: {summary.average_completeness_score:.2f} / 1.00",
            f"Deduplication Accuracy: {summary.average_deduplication_score:.2f} / 1.00",
            "",
            "REPOSITORY RESULTS",
            "-" * 80
        ]
        
        # Add results for each repository
        for result in summary.repository_results:
            report_lines.extend([
                "",
                f"Repository: {result.repository}",
                f"  Execution Time: {result.execution_time_seconds:.2f}s",
                f"  Suggestions Generated: {len(result.suggestions)}"
            ])
            
            if result.errors:
                report_lines.append(f"  Errors: {', '.join(result.errors)}")
            
            if result.quality_result:
                status = "PASS" if result.quality_result.passed else "FAIL"
                report_lines.append(
                    f"  Quality Score: {result.quality_result.score:.2f} [{status}]"
                )
            
            if result.completeness_result:
                status = "PASS" if result.completeness_result.passed else "FAIL"
                report_lines.append(
                    f"  Completeness Score: {result.completeness_result.score:.2f} [{status}]"
                )
            
            if result.deduplication_result:
                status = "PASS" if result.deduplication_result.passed else "FAIL"
                report_lines.append(
                    f"  Deduplication Score: {result.deduplication_result.score:.2f} [{status}]"
                )
        
        report_lines.extend([
            "",
            "=" * 80,
            "END OF REPORT",
            "=" * 80
        ])
        
        report_text = "\n".join(report_lines)
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            logger.info(f"Report saved to {output_file}")
        
        return report_text
    
    def save_results_json(
        self,
        summary: EvaluationSummary,
        output_file: str
    ) -> None:
        """Save evaluation results as JSON.
        
        Args:
            summary: Evaluation summary
            output_file: Output file path
        """
        logger.info(f"Saving results to {output_file}")
        
        with open(output_file, 'w') as f:
            json.dump(summary.to_dict(), f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
