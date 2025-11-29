"""Demo script for Analyzer Agent.

This script demonstrates the Analyzer Agent's capabilities by analyzing
a sample repository.
"""

import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents import AnalyzerAgent
from src.models.repository import Repository
from src.config import get_config
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run analyzer demo."""
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = get_config()
        logger.info(f"Configuration loaded: {config.get_sanitized_config()}")
        
        # Create analyzer agent
        logger.info("Initializing Analyzer Agent...")
        analyzer = AnalyzerAgent()
        
        # Create a sample repository (using a well-known public repo)
        sample_repo = Repository(
            name="requests",
            full_name="psf/requests",
            owner="psf",
            url="https://github.com/psf/requests",
            default_branch="main",
            visibility="public",
            created_at=datetime(2011, 2, 13),
            updated_at=datetime.now()
        )
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Analyzing repository: {sample_repo.full_name}")
        logger.info(f"{'='*60}\n")
        
        # Analyze the repository
        analysis = analyzer.analyze_repository(sample_repo)
        
        # Display results
        logger.info(f"\n{'='*60}")
        logger.info("ANALYSIS RESULTS")
        logger.info(f"{'='*60}\n")
        
        logger.info(f"Repository: {analysis.repository.full_name}")
        logger.info(f"Owner: {analysis.repository.owner}")
        logger.info(f"URL: {analysis.repository.url}")
        logger.info(f"Visibility: {analysis.repository.visibility}")
        
        logger.info(f"\n--- Overview ---")
        logger.info(f"Has README: {analysis.overview.readme_content is not None}")
        logger.info(f"Has Tests: {analysis.overview.has_tests}")
        logger.info(f"Has CI/CD: {analysis.overview.has_ci_config}")
        logger.info(f"Has CONTRIBUTING: {analysis.overview.has_contributing}")
        logger.info(f"Languages: {', '.join(analysis.overview.languages.keys())}")
        logger.info(f"File count: {len(analysis.overview.file_structure)}")
        
        logger.info(f"\n--- History ---")
        logger.info(f"Commit count: {analysis.history.commit_count}")
        logger.info(f"Last commit: {analysis.history.last_commit_date}")
        logger.info(f"Contributors: {analysis.history.contributors_count}")
        logger.info(f"Open issues: {analysis.history.open_issues_count}")
        logger.info(f"Open PRs: {analysis.history.open_prs_count}")
        
        logger.info(f"\n--- Health Snapshot ---")
        logger.info(f"Activity level: {analysis.health.activity_level}")
        logger.info(f"Test coverage: {analysis.health.test_coverage}")
        logger.info(f"Documentation quality: {analysis.health.documentation_quality}")
        logger.info(f"CI/CD status: {analysis.health.ci_cd_status}")
        logger.info(f"Dependency status: {analysis.health.dependency_status}")
        logger.info(f"Overall health score: {analysis.health.overall_health_score:.2f}")
        logger.info(f"Issues identified: {len(analysis.health.issues_identified)}")
        for issue in analysis.health.issues_identified:
            logger.info(f"  - {issue}")
        
        logger.info(f"\n--- Repository Profile ---")
        logger.info(f"Purpose: {analysis.profile.purpose}")
        logger.info(f"Tech stack: {', '.join(analysis.profile.tech_stack)}")
        logger.info(f"Key files: {', '.join(analysis.profile.key_files[:5])}")
        logger.info(f"Last analyzed: {analysis.profile.last_analyzed}")
        logger.info(f"Analysis version: {analysis.profile.analysis_version}")
        
        logger.info(f"\n{'='*60}")
        logger.info("Analysis complete!")
        logger.info(f"{'='*60}\n")
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
