"""
Purpose: Run the contributor enrichment pipeline from repository fetch to final outputs.
Input: Environment configuration loaded from `.env` and repository constants from `config.py`.
Output: Writes `dataset.csv` and `report.md` in the project root.
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from analysis_code.utils.config import validate_config, REPOS, TOP_N_CONTRIBUTORS
from analysis_code.utils.logger import logger
from analysis_code.github_data.fetcher import get_contributors, get_merged_prs
from analysis_code.github_data.classifier import classify_all
from analysis_code.enrichment.linkedin_finder import find_linkedin_urls_bulk
from analysis_code.enrichment.profile_scraper import enrich_profiles
from analysis_code.output.dataset_builder import build_dataset
from analysis_code.output.report_builder import build_report


def main() -> None:
    try:
        logger.section("Pipeline Initialization")
        validate_config()
        logger.success("Configuration validated successfully.")
        
        all_top_contributors = []
        
        for repo_name in REPOS:
            logger.section(f"Processing Repository: {repo_name}")
            
            contributors = get_contributors(repo_name)
            
            prs = get_merged_prs(repo_name)
            
            for c in contributors:
                login = c["github_login"]
                c["merged_prs_count"] = prs.get(login, 0)
                
            classified = classify_all(contributors, repo_name)
            
            classified.sort(key=lambda x: x.get("commit_count", 0), reverse=True)
            top_contributors = classified[:TOP_N_CONTRIBUTORS]
            logger.success(f"Selected top {len(top_contributors)} contributors for {repo_name}.")
            
            for c in top_contributors:
                c["repo"] = repo_name
                c["contribution_metric"] = c.get("commit_count", 0)
                
            all_top_contributors.extend(top_contributors)
            
        logger.section("Enrichment Stage")
        
        with_urls = find_linkedin_urls_bulk(all_top_contributors)
        
        enriched = enrich_profiles(with_urls)
        
        logger.section("Output Generation")
        
        df = build_dataset(enriched)
        
        build_report(df)
        
        logger.section("Final Summary")
        
        total_processed = len(enriched)
        urls_found = sum(1 for c in enriched if c.get("linkedin_url"))
        employers_found = sum(1 for c in enriched if c.get("employer_inferred") and c.get("employer_inferred") != "Unknown")
        
        logger.info(f"Total top contributors processed: {total_processed}")
        logger.info(f"Total with LinkedIn URLs found: {urls_found}")
        logger.info(f"Total with employer identified: {employers_found}")
        logger.success("Pipeline completed successfully! Saved dataset.csv and report.md")
        
    except Exception as e:
        logger.fail(f"Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
