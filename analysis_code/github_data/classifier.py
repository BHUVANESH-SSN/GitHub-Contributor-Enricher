"""
Purpose: Classify contributors as internal or external using GitHub profile signals.
Input: Contributor dictionaries plus the repository slug being evaluated.
Output: Returns contributor records enriched with classification labels and confidence.
"""
import json
from pathlib import Path
from typing import Dict, List

from github import Github, GithubException

from analysis_code.utils.config import GITHUB_TOKEN
from analysis_code.utils.logger import logger

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True, parents=True)

g = Github(GITHUB_TOKEN)

OPENAI_USERNAME_PATTERNS = ['-oai', '_oai', '-openai', '_openai']
GOOGLE_USERNAME_PATTERNS = ['-google', '_google', '-googler', '_googler']

BOTS = {'dependabot[bot]', 'gemini-cli-robot', 'github-actions[bot]'}

KNOWN_INTERNALS = {
    "openai/codex": ["gregbrockman", "sama"],
    "google-gemini/gemini-cli": ["sundarpichai", "jeffdean"],
}


def classify_contributor(contributor: Dict, repo_name: str) -> Dict:
    login = contributor.get("github_login", "")
    login_lower = login.lower()
    email = (contributor.get("email") or "").lower()
    company = (contributor.get("company") or "").lower()

    if login in BOTS or "[bot]" in login_lower or "robot" in login_lower:
        contributor["internal_or_external"] = "external"
        contributor["classification_confidence"] = "low"
        contributor["is_bot"] = True
        return contributor

    if repo_name == "openai/codex" and "@openai.com" in email:
        contributor["internal_or_external"] = "internal"
        contributor["classification_confidence"] = "high"
        return contributor

    if repo_name == "google-gemini/gemini-cli" and (
        "@google.com" in email or "@googlers.com" in email
    ):
        contributor["internal_or_external"] = "internal"
        contributor["classification_confidence"] = "high"
        return contributor

    if repo_name == "openai/codex":
        if any(p in login_lower for p in OPENAI_USERNAME_PATTERNS):
            contributor["internal_or_external"] = "internal"
            contributor["classification_confidence"] = "medium"
            return contributor

    if repo_name == "google-gemini/gemini-cli":
        if any(p in login_lower for p in GOOGLE_USERNAME_PATTERNS):
            contributor["internal_or_external"] = "internal"
            contributor["classification_confidence"] = "medium"
            return contributor

    if repo_name == "openai/codex" and "openai" in company:
        contributor["internal_or_external"] = "internal"
        contributor["classification_confidence"] = "medium"
        return contributor

    if repo_name == "google-gemini/gemini-cli" and (
        "google" in company or "alphabet" in company
    ):
        contributor["internal_or_external"] = "internal"
        contributor["classification_confidence"] = "medium"
        return contributor

    if login_lower in [u.lower() for u in KNOWN_INTERNALS.get(repo_name, [])]:
        contributor["internal_or_external"] = "internal"
        contributor["classification_confidence"] = "medium"
        return contributor

    try:
        user = g.get_user(login)
        org_logins = [org.login.lower() for org in user.get_orgs()]

        if repo_name == "openai/codex" and "openai" in org_logins:
            contributor["internal_or_external"] = "internal"
            contributor["classification_confidence"] = "low"
            return contributor

        if repo_name == "google-gemini/gemini-cli" and (
            "google" in org_logins or "google-deepmind" in org_logins
        ):
            contributor["internal_or_external"] = "internal"
            contributor["classification_confidence"] = "low"
            return contributor

    except GithubException:
        pass

    contributor["internal_or_external"] = "external"
    contributor["classification_confidence"] = "low"
    return contributor


def classify_all(contributors: List[Dict], repo_name: str) -> List[Dict]:
    repo_slug = repo_name.replace("/", "_")
    cache_file = CACHE_DIR / f"classified_users_{repo_slug}.json"

    if cache_file.exists():
        logger.info(f"Loading classified users for {repo_name} from cache")
        with open(cache_file, "r", encoding="utf-8") as f:
            cached_results = json.load(f)

        if isinstance(cached_results, list):
            cached_map = {item.get("github_login"): item for item in cached_results}
            merged_results = []
            for contributor in contributors:
                merged = contributor.copy()
                cached = cached_map.get(contributor.get("github_login"))
                if cached:
                    for key in ("internal_or_external", "classification_confidence", "is_bot"):
                        if key in cached:
                            merged[key] = cached[key]
                else:
                    merged = classify_contributor(merged, repo_name)
                merged_results.append(merged)
            return merged_results

    logger.info(f"Classifying {len(contributors)} contributors...")
    results = []
    counts: Dict[str, int] = {"internal": 0, "external": 0, "unknown": 0}

    from tqdm import tqdm

    for contributor in tqdm(contributors, desc=f"Classifying ({repo_name})"):
        classified = classify_contributor(contributor, repo_name)
        status = classified.get("internal_or_external", "unknown")
        counts[status] = counts.get(status, 0) + 1
        results.append(classified)

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    logger.info(
        f"Classification for {repo_name}: "
        f"{counts['internal']} internal, "
        f"{counts['external']} external, "
        f"{counts.get('unknown', 0)} unknown"
    )
    return results
