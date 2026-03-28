"""
Purpose: Discovers LinkedIn profile URLs for GitHub contributors using Google Search.
Input: List of contributor dictionaries (name, github_login, company).
Output: List of contributors enriched with a 'linkedin_url'.
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from tqdm import tqdm
from apify_client import ApifyClient
from analysis_code.utils.config import APIFY_API_TOKEN, APIFY_ACTOR
from analysis_code.utils.logger import logger

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True, parents=True)

apify_client = ApifyClient(APIFY_API_TOKEN)

def find_linkedin_url(name: str, github_login: str, company: str = "") -> Optional[str]:
    search_term = name if name else github_login
    
    company_term = company if company else ""
    
    search_query = f"{search_term} {company_term} site:linkedin.com/in"
    
    try:
        run_input = { "queries": search_query }
        run = apify_client.actor(APIFY_ACTOR).call(run_input=run_input)
        
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            results = item.get("organicResults", [])
            for res in results:
                url = res.get("url", "")
                if "linkedin.com/in/" in url:
                    return url
    except Exception as e:
        logger.warning(f"Error finding LinkedIn URL for {github_login}: {e}")
        
    return None

def find_linkedin_urls_bulk(contributors: List[Dict]) -> List[Dict]:
    cache_file = CACHE_DIR / "linkedin_urls.json"
    
    if cache_file.exists():
        logger.info("Loading LinkedIn URLs from cache")
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    logger.info("Finding LinkedIn URLs in bulk using Apify")
    
    for contributor in tqdm(contributors, desc="Finding LinkedIn URLs"):
        name = contributor.get("name", "")
        login = contributor.get("github_login", "")
        company = contributor.get("company", "")
        
        if company.startswith("@"):
            company = company[1:]
            
        url = find_linkedin_url(name, login, company)
        contributor["linkedin_url"] = url or ""
        time.sleep(2)
        
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(contributors, f, indent=4)
        
    return contributors
