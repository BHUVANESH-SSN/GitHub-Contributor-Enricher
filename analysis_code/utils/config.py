"""
Purpose: Load environment variables and shared pipeline constants.
Input: Values from `.env` and default repository settings defined in this module.
Output: Exposes configuration constants and raises validation errors for missing keys.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
APIFY_ACTOR = os.getenv("APIFY_ACTOR", "apify/google-search-scraper")
SCRAPIN_API_KEY = os.getenv("SCRAPIN_API_KEY")
SCRAPIN_ENDPOINT = os.getenv("SCRAPIN_ENDPOINT", "https://api.scrapin.io/enrichment/profile")

REPOS = ["openai/codex", "google-gemini/gemini-cli"]
TOP_N_CONTRIBUTORS = 20
CACHE_DIR = Path("cache")


def _has_github_cache() -> bool:
    return all(
        (CACHE_DIR / f"contributors_{repo.replace('/', '_')}.json").exists()
        and (CACHE_DIR / f"prs_{repo.replace('/', '_')}.json").exists()
        for repo in REPOS
    )


def _has_linkedin_cache() -> bool:
    return (CACHE_DIR / "linkedin_urls.json").exists()


def _has_profile_cache() -> bool:
    return (CACHE_DIR / "enriched_profiles.json").exists() or (CACHE_DIR / "reverse_connect.json").exists()


def validate_config() -> None:
    if not GITHUB_TOKEN and not _has_github_cache():
        raise ValueError("GITHUB_TOKEN is missing from .env file.")
    if not APIFY_API_TOKEN and not _has_linkedin_cache():
        raise ValueError("APIFY_API_TOKEN is missing from .env file.")
    if not SCRAPIN_API_KEY and not _has_profile_cache():
        raise ValueError("SCRAPIN_API_KEY is missing from .env file.")
