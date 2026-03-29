"""
Purpose: Fetch contributor and merged pull request data from the GitHub API with caching.
Input: A repository slug such as `openai/codex`.
Output: Returns contributor records and per-user merged pull request counts.
"""
import json
from pathlib import Path

from github import Github, GithubException
from tqdm import tqdm

from analysis_code.utils.config import GITHUB_TOKEN
from analysis_code.utils.logger import logger

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True, parents=True)

g = Github(GITHUB_TOKEN)


def get_contributors(repo_name: str) -> list[dict]:
    repo_slug = repo_name.replace("/", "_")
    cache_file = CACHE_DIR / f"contributors_{repo_slug}.json"
    
    if cache_file.exists():
        logger.info(f"Loading contributors for {repo_name} from cache")
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    logger.info(f"Fetching contributors for {repo_name} from GitHub API")
    contributors_data = []
    
    try:
        repo = g.get_repo(repo_name)
        contributors = repo.get_contributors()
        
        for author in tqdm(contributors, desc=f"Fetching contributors ({repo_name})"):
            contributors_data.append({
                "github_login": author.login,
                "github_id": author.id,
                "name": author.name or "",
                "email": author.email or "",
                "company": author.company or "",
                "commit_count": author.contributions,
                "avatar_url": author.avatar_url or "",
                "profile_url": author.html_url or ""
            })
            
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(contributors_data, f, indent=4)
        return contributors_data

    except GithubException as e:
        logger.warning(f"GitHub API error fetching contributors for {repo_name}: {e}")
        return []


def get_merged_prs(repo_name: str) -> dict[str, int]:
    repo_slug = repo_name.replace("/", "_")
    cache_file = CACHE_DIR / f"prs_{repo_slug}.json"
    
    if cache_file.exists():
        logger.info(f"Loading PRs for {repo_name} from cache")
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    logger.info(f"Fetching merged PRs for {repo_name} from GitHub API")
    prs_data = {}
    
    try:
        repo = g.get_repo(repo_name)
        pulls = repo.get_pulls(state="closed")
        
        for pull in tqdm(pulls, desc=f"Fetching PRs ({repo_name})"):
            if pull.merged_at and pull.user:
                prs_data[pull.user.login] = prs_data.get(pull.user.login, 0) + 1
                
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(prs_data, f, indent=4)
        return prs_data

    except GithubException as e:
        logger.warning(f"GitHub API error fetching PRs for {repo_name}: {e}")
        return {}
