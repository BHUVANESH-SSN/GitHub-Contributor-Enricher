"""
Purpose: Loads and validates environment variables and project constants.
Input: .env file containing API tokens.
Output: Exported configuration variables for the application.
"""
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
APIFY_ACTOR = os.getenv("APIFY_ACTOR", "apify/google-search-scraper")
SCRAPIN_API_KEY = os.getenv("SCRAPIN_API_KEY")
SCRAPIN_ENDPOINT = os.getenv("SCRAPIN_ENDPOINT", "https://api.scrapin.io/enrichment/profile")

REPOS = ["openai/codex", "google-gemini/gemini-cli"]
TOP_N_CONTRIBUTORS = 20

def validate_config() -> None:
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN is missing from .env file.")
    if not APIFY_API_TOKEN:
        raise ValueError("APIFY_API_TOKEN is missing from .env file.")
