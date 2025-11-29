"""Evaluators for assessing agent performance.

This module provides evaluators for:
- Suggestion quality (LLM-as-judge)
- Deduplication accuracy
- Analysis completeness
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

import google.generativeai as genai

from src.models.health import RepositoryProfile, HealthSnapshot
from src.models.maintenance import MaintenanceSuggestion
from src.config import get_config
from evaluation.test_dataset import TestRepository, ExpectedSuggestion

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Result of an evaluation."""
    
    metric_name: str
    score: float  # 0.0 to 1.0
    details: Dict[str, Any]
    passed: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'metric_name': self.metric_name,
            'score': self.score,
            'details': self.details,
            'passed': self.passed
        }


class SuggestionQualityEvaluator:
    """Evaluator for suggestion quality using LLM-as-judge."""
    
    def __init__(self):
        """Initialize the evaluator."""
        config = get_config()
        genai.configure(api_key=config.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("SuggestionQualityEvaluator initialized")
    
    def evaluate(
        self,
        suggestions: List[MaintenanceSuggestion],
        test_repo: TestRepository,
        profile: RepositoryProfile
    ) -> EvaluationResult:
        """Evaluate suggestion quality using LLM-as-judge.
        
        Args:
            suggestions: Generated suggestions to evaluate
            test_repo: Test repository with expected characteristics
            profile: Repository profile from analysis
            
        Returns:
            EvaluationResult with quality score
        """
        logger.info(f"Evaluating {len(suggestions)} suggestions for {test_repo.full_name}")
        
        if not suggestions:
            # No suggestions generated
            if len(test_repo.expected_suggestions) == 0:
                # Expected no suggestions - perfect score
                return EvaluationResult(
                    metric_name='suggestion_quality',
                    score=1.0,
                    details={
                        'reason': 'No suggestions expected or generated',
                        'suggestions_count': 0
                    },
                    passed=True
                )
            else:
                # Expected suggestions but got none - low score
                return EvaluationResult(
                    metric_name='suggestion_quality',
                    score=0.0,
                    details={
                        'reason': 'Expected suggestions but none generated',
                        'expected_count': len(test_repo.expected_suggestions),
                        'actual_count': 0
                    },
                    passed=False
                )
        
        # Evaluate each suggestion using LLM
        scores = []
        details = []
        
        for suggestion in suggestions:
            score, detail = self._evaluate_single_suggestion(
                suggestion,
                test_repo,
                profile
            )
            scores.append(score)
            details.append(detail)
        
        # Calculate average score
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        # Check if suggestions match expected suggestions
        expected_match_score = self._check_expected_suggestions(
            suggestions,
            test_repo.expected_suggestions
        )
        
        # Combine scores (70% LLM quality, 30% expected match)
        final_score = (avg_score * 0.7) + (expected_match_score * 0.3)
        
        return EvaluationResult(
            metric_name='suggestion_quality',
            score=final_score,
            details={
                'llm_quality_score': avg_score,
                'expected_match_score': expected_match_score,
                'suggestions_evaluated': len(suggestions),
                'individual_scores': scores,
                'individual_details': details
            },
            passed=final_score >= 0.7  # Pass threshold
        )
    
    def _evaluate_single_suggestion(
        self,
        suggestion: MaintenanceSuggestion,
        test_repo: TestRepository,
        profile: RepositoryProfile
    ) -> tuple:
        """Evaluate a single suggestion using LLM-as-judge.
        
        Args:
            suggestion: Suggestion to evaluate
            test_repo: Test repository
            profile: Repository profile
            
        Returns:
            Tuple of (score, details)
        """
        # Create evaluation prompt
        prompt = self._create_evaluation_prompt(suggestion, test_repo, profile)
        
        try:
            # Call LLM for evaluation
            response = self.model.generate_content(prompt)
            
            # Parse response
            score, reasoning = self._parse_evaluation_response(response.text)
            
            return score, {
                'suggestion_title': suggestion.title,
                'score': score,
                'reasoning': reasoning
            }
            
        except Exception as e:
            logger.error(f"Failed to evaluate suggestion: {e}")
            # Fallback to basic scoring
            return 0.5, {
                'suggestion_title': suggestion.title,
                'score': 0.5,
                'reasoning': f'Evaluation failed: {e}',
                'fallback': True
            }
    
    def _create_evaluation_prompt(
        self,
        suggestion: MaintenanceSuggestion,
        test_repo: TestRepository,
        profile: RepositoryProfile
    ) -> str:
        """Create evaluation prompt for LLM-as-judge.
        
        Args:
            suggestion: Suggestion to evaluate
            test_repo: Test repository
            profile: Repository profile
            
        Returns:
            Evaluation prompt
        """
        return f"""Evaluate the quality of this maintenance suggestion for a GitHub repository.

Repository: {test_repo.full_name}
Repository Description: {test_repo.description}
Repository Purpose: {profile.purpose}
Tech Stack: {', '.join(profile.tech_stack)}

Health Assessment:
- Activity Level: {profile.health.activity_level}
- Test Coverage: {profile.health.test_coverage}
- Documentation Quality: {profile.health.documentation_quality}
- CI/CD Status: {profile.health.ci_cd_status}
- Overall Health Score: {profile.health.overall_health_score:.2f}

Suggestion to Evaluate:
- Category: {suggestion.category}
- Priority: {suggestion.priority}
- Title: {suggestion.title}
- Description: {suggestion.description}
- Rationale: {suggestion.rationale}
- Estimated Effort: {suggestion.estimated_effort}

Evaluate this suggestion on the following criteria:
1. Relevance: Is it relevant to the repository's health issues?
2. Actionability: Is it specific and actionable?
3. Impact: Would it meaningfully improve the repository?
4. Appropriateness: Is the priority and effort estimate reasonable?
5. Clarity: Is the description clear and helpful?

Provide a score from 0.0 (poor) to 1.0 (excellent) and brief reasoning.

Respond in the following JSON format:
{{
  "score": 0.0-1.0,
  "reasoning": "Brief explanation of the score"
}}

Respond with ONLY the JSON object, no additional text."""
    
    def _parse_evaluation_response(self, response_text: str) -> tuple:
        """Parse LLM evaluation response.
        
        Args:
            response_text: LLM response text
            
        Returns:
            Tuple of (score, reasoning)
        """
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)
            
            score = float(data['score'])
            reasoning = data['reasoning']
            
            # Clamp score to [0.0, 1.0]
            score = max(0.0, min(1.0, score))
            
            return score, reasoning
            
        except Exception as e:
            logger.warning(f"Failed to parse evaluation response: {e}")
            return 0.5, "Failed to parse evaluation response"
    
    def _check_expected_suggestions(
        self,
        suggestions: List[MaintenanceSuggestion],
        expected: List[ExpectedSuggestion]
    ) -> float:
        """Check if suggestions match expected suggestions.
        
        Args:
            suggestions: Generated suggestions
            expected: Expected suggestions
            
        Returns:
            Match score (0.0 to 1.0)
        """
        if not expected:
            # No expected suggestions - perfect match
            return 1.0
        
        # Count how many expected suggestions are matched
        matched = 0
        for exp in expected:
            if any(exp.matches(sug) for sug in suggestions):
                matched += 1
        
        # Calculate match ratio
        match_score = matched / len(expected) if expected else 1.0
        
        return match_score


class DeduplicationEvaluator:
    """Evaluator for deduplication accuracy."""
    
    def evaluate(
        self,
        suggestions_run1: List[MaintenanceSuggestion],
        suggestions_run2: List[MaintenanceSuggestion],
        repo_changed: bool = False
    ) -> EvaluationResult:
        """Evaluate deduplication accuracy.
        
        Args:
            suggestions_run1: Suggestions from first run
            suggestions_run2: Suggestions from second run
            repo_changed: Whether repository changed between runs
            
        Returns:
            EvaluationResult with deduplication accuracy
        """
        logger.info("Evaluating deduplication accuracy")
        
        if repo_changed:
            # Repository changed, duplicates are acceptable
            return EvaluationResult(
                metric_name='deduplication_accuracy',
                score=1.0,
                details={
                    'reason': 'Repository changed between runs',
                    'run1_count': len(suggestions_run1),
                    'run2_count': len(suggestions_run2)
                },
                passed=True
            )
        
        # Find duplicates (same title)
        titles_run1 = {s.title.lower() for s in suggestions_run1}
        titles_run2 = {s.title.lower() for s in suggestions_run2}
        
        duplicates = titles_run1.intersection(titles_run2)
        
        # Calculate deduplication accuracy
        total_suggestions = len(titles_run1) + len(titles_run2)
        if total_suggestions == 0:
            accuracy = 1.0
        else:
            # Accuracy = 1 - (duplicates / total)
            accuracy = 1.0 - (len(duplicates) / total_suggestions)
        
        return EvaluationResult(
            metric_name='deduplication_accuracy',
            score=accuracy,
            details={
                'run1_count': len(suggestions_run1),
                'run2_count': len(suggestions_run2),
                'duplicate_count': len(duplicates),
                'duplicate_titles': list(duplicates),
                'total_suggestions': total_suggestions
            },
            passed=accuracy >= 0.9  # Pass threshold: <10% duplicates
        )


class AnalysisCompletenessEvaluator:
    """Evaluator for analysis completeness."""
    
    def evaluate(
        self,
        profile: RepositoryProfile,
        test_repo: TestRepository
    ) -> EvaluationResult:
        """Evaluate analysis completeness.
        
        Args:
            profile: Repository profile from analysis
            test_repo: Test repository with expected characteristics
            
        Returns:
            EvaluationResult with completeness score
        """
        logger.info(f"Evaluating analysis completeness for {test_repo.full_name}")
        
        # Check required fields in profile
        required_fields = {
            'purpose': profile.purpose,
            'tech_stack': profile.tech_stack,
            'key_files': profile.key_files,
            'health': profile.health
        }
        
        # Check required fields in health snapshot
        health_fields = {
            'activity_level': profile.health.activity_level,
            'test_coverage': profile.health.test_coverage,
            'documentation_quality': profile.health.documentation_quality,
            'ci_cd_status': profile.health.ci_cd_status,
            'dependency_status': profile.health.dependency_status,
            'overall_health_score': profile.health.overall_health_score,
            'issues_identified': profile.health.issues_identified
        }
        
        # Count present fields
        profile_present = sum(1 for v in required_fields.values() if v)
        health_present = sum(1 for v in health_fields.values() if v is not None)
        
        total_fields = len(required_fields) + len(health_fields)
        present_fields = profile_present + health_present
        
        # Calculate completeness score
        completeness_score = present_fields / total_fields if total_fields > 0 else 0.0
        
        # Check health score range
        expected_min, expected_max = test_repo.expected_health_score_range
        health_score_in_range = (
            expected_min <= profile.health.overall_health_score <= expected_max
        )
        
        # Check activity level
        activity_level_correct = (
            profile.health.activity_level == test_repo.expected_activity_level
        )
        
        # Combine scores
        final_score = (
            completeness_score * 0.6 +
            (1.0 if health_score_in_range else 0.0) * 0.2 +
            (1.0 if activity_level_correct else 0.0) * 0.2
        )
        
        return EvaluationResult(
            metric_name='analysis_completeness',
            score=final_score,
            details={
                'completeness_score': completeness_score,
                'present_fields': present_fields,
                'total_fields': total_fields,
                'health_score': profile.health.overall_health_score,
                'expected_health_range': test_repo.expected_health_score_range,
                'health_score_in_range': health_score_in_range,
                'activity_level': profile.health.activity_level,
                'expected_activity_level': test_repo.expected_activity_level,
                'activity_level_correct': activity_level_correct
            },
            passed=final_score >= 0.8  # Pass threshold
        )
