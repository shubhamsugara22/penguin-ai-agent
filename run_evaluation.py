#!/usr/bin/env python3
"""Main script for running the evaluation framework.

This script runs the complete evaluation suite and generates reports.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from evaluation.runner import EvaluationRunner
from evaluation.test_dataset import get_test_repositories
from src.logging_config import setup_logging


def main():
    """Main entry point for evaluation."""
    parser = argparse.ArgumentParser(
        description='Run evaluation suite for GitHub Maintainer Agent'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='evaluation_results',
        help='Directory for output files (default: evaluation_results)'
    )
    parser.add_argument(
        '--skip-deduplication',
        action='store_true',
        help='Skip deduplication test'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--repos',
        type=str,
        nargs='+',
        help='Specific repositories to evaluate (e.g., octocat/Hello-World)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting evaluation suite")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get test repositories
    if args.repos:
        from evaluation.test_dataset import get_test_repository
        test_repos = []
        for repo_name in args.repos:
            try:
                test_repos.append(get_test_repository(repo_name))
            except ValueError as e:
                logger.error(f"Repository not found: {repo_name}")
                continue
        
        if not test_repos:
            logger.error("No valid repositories specified")
            return 1
    else:
        test_repos = get_test_repositories()
    
    logger.info(f"Evaluating {len(test_repos)} repositories")
    
    # Run evaluation
    try:
        runner = EvaluationRunner()
        summary = runner.run_evaluation(
            test_repos=test_repos,
            run_deduplication_test=not args.skip_deduplication
        )
        
        # Generate report
        report_file = output_dir / 'evaluation_report.txt'
        report_text = runner.generate_report(summary, str(report_file))
        
        # Print report to console
        print("\n" + report_text)
        
        # Save JSON results
        json_file = output_dir / 'evaluation_results.json'
        runner.save_results_json(summary, str(json_file))
        
        logger.info(f"Evaluation complete. Results saved to {output_dir}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total Repositories: {summary.total_repositories}")
        print(f"Successful: {summary.successful_evaluations}")
        print(f"Failed: {summary.failed_evaluations}")
        print(f"Average Quality Score: {summary.average_quality_score:.2f}")
        print(f"Average Completeness Score: {summary.average_completeness_score:.2f}")
        print(f"Average Deduplication Score: {summary.average_deduplication_score:.2f}")
        print(f"Total Time: {summary.total_execution_time_seconds:.2f}s")
        print("=" * 80)
        
        # Return exit code based on results
        if summary.failed_evaluations > 0:
            return 1
        
        # Check if any scores are below threshold
        if (summary.average_quality_score < 0.7 or
            summary.average_completeness_score < 0.8 or
            summary.average_deduplication_score < 0.9):
            logger.warning("Some scores are below threshold")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
