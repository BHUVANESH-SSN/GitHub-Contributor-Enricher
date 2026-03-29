"""
Purpose: Enrich contributor records with employer and tenure data from LinkedIn profile APIs.
Input: Contributor records that may include a `linkedin_url`.
Output: Returns contributor records with employer, title, and tenure fields populated.
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import requests
from tqdm import tqdm

from analysis_code.utils.config import SCRAPIN_ENDPOINT
from analysis_code.utils.logger import logger

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True, parents=True)
ENRICHED_CACHE_PATH = CACHE_DIR / "enriched_profiles.json"


def normalize_linkedin_url(linkedin_url: str) -> str:
    return str(linkedin_url).lower().replace("am.linkedin.com", "www.linkedin.com").rstrip("/")


def load_local_profile_cache() -> dict[str, dict]:
    cache_file = CACHE_DIR / "reverse_connect.json"
    if not cache_file.exists():
        return {}

    with open(cache_file, "r", encoding="utf-8") as f:
        rows = json.load(f)

    cache: dict[str, dict] = {}
    for item in rows:
        profile = item.get("data") or {}
        linkedin_url = normalize_linkedin_url(profile.get("linkedinUrl", ""))
        if linkedin_url:
            cache[linkedin_url] = profile
    return cache


LOCAL_PROFILE_CACHE = load_local_profile_cache()

ENRICHMENT_FIELDS = (
    "linkedin_url",
    "current_company",
    "current_title",
    "employer_inferred",
    "employer_confidence",
    "tenure_current_employer_years",
    "tenure_confidence",
    "internal_or_external",
    "classification_confidence",
)


def bucket_employer(company: str) -> str:
    if not company:
        return "Unknown"
    c = company.lower()

    if "openai" in c:
        return "OpenAI"
    if "google" in c or "alphabet" in c or "deepmind" in c:
        return "Google"
    if "anthropic" in c:
        return "Anthropic"
    if "xai" in c or "x.ai" in c:
        return "xAI"

    return "Unknown"


def calculate_tenure(start_date_str: str) -> Optional[float]:
    if not start_date_str:
        return None
    try:
        s = str(start_date_str).strip()[:10]
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                start = datetime.strptime(s[:len(fmt.replace("%Y","0000").replace("%m","00").replace("%d","00"))], fmt)
                return round((datetime.now() - start).days / 365.25, 1)
            except ValueError:
                continue
    except Exception:
        pass
    return None


def extract_start_date(position: dict) -> Optional[str]:
    start = position.get("startEndDate") or position.get("start_date")
    if isinstance(start, dict):
        if start.get("start"):
            return start["start"]
        year = start.get("year")
        month = start.get("month", 1)
        return f"{year}-{str(month).zfill(2)}" if year else None
    return str(start) if start else None


def is_current_position(position: dict) -> bool:
    if position.get("endEndDate") or position.get("end_date"):
        return False

    date_range = position.get("startEndDate")
    if isinstance(date_range, dict) and date_range.get("end"):
        return False

    return True


def infer_internal_or_external(contributor: dict, raw_company: str, bucketed_employer: str) -> tuple[str, str]:
    repo = contributor.get("repo", "")
    repo_company = "OpenAI" if "openai" in repo else "Google" if "google" in repo else ""
    raw_company_lower = raw_company.lower()

    if repo_company and bucketed_employer == repo_company:
        return "internal", "high"

    if repo_company and raw_company:
        if repo_company == "OpenAI" and "openai" not in raw_company_lower:
            return "external", "high"
        if repo_company == "Google" and not any(token in raw_company_lower for token in ("google", "alphabet", "deepmind")):
            return "external", "high"

    return (
        contributor.get("internal_or_external", "external"),
        contributor.get("classification_confidence", "low"),
    )


def get_repo_company(repo_name: str) -> str:
    if "openai" in repo_name:
        return "OpenAI"
    if "google" in repo_name:
        return "Google"
    return "Unknown"


def load_enriched_cache() -> tuple[list[dict], dict[tuple[str, str], dict], dict[str, dict]]:
    """
    Purpose: Load previously enriched contributors so the pipeline can reuse successful results.
    Input: The `cache/enriched_profiles.json` file when it exists.
    Output: Returns the raw cached rows plus lookup maps by `(repo, github_login)` and normalized LinkedIn URL.
    """
    if not ENRICHED_CACHE_PATH.exists():
        return [], {}, {}

    with open(ENRICHED_CACHE_PATH, "r", encoding="utf-8") as file_handle:
        cached_rows = json.load(file_handle)

    by_identity: dict[tuple[str, str], dict] = {}
    by_url: dict[str, dict] = {}

    for row in cached_rows:
        repo = row.get("repo", "")
        login = row.get("github_login", "")
        if repo and login:
            by_identity[(repo, login)] = row

        normalized_url = normalize_linkedin_url(row.get("linkedin_url", ""))
        if normalized_url:
            by_url[normalized_url] = row

    return cached_rows, by_identity, by_url


def get_cached_enrichment(
    contributor: dict,
    by_identity: dict[tuple[str, str], dict],
    by_url: dict[str, dict],
) -> Optional[dict]:
    """
    Purpose: Find a previously enriched record for a contributor.
    Input: The current contributor plus enrichment cache maps.
    Output: Returns the cached contributor row when a match is found, otherwise `None`.
    """
    repo = contributor.get("repo", "")
    login = contributor.get("github_login", "")
    identity_key = (repo, login)

    if identity_key in by_identity:
        return by_identity[identity_key]

    normalized_url = normalize_linkedin_url(contributor.get("linkedin_url", ""))
    if normalized_url and normalized_url in by_url:
        return by_url[normalized_url]

    return None


def merge_cached_enrichment(contributor: dict, cached_enrichment: dict) -> dict:
    """
    Purpose: Merge stable enrichment fields from cache into the current contributor row.
    Input: The current contributor and its cached enrichment row.
    Output: Returns a contributor row that keeps current pipeline metadata while reusing cached enrichment fields.
    """
    merged = contributor.copy()

    for field in ENRICHMENT_FIELDS:
        cached_value = cached_enrichment.get(field)
        if field == "linkedin_url":
            if cached_value and not merged.get(field):
                merged[field] = cached_value
            continue

        if cached_value not in (None, ""):
            merged[field] = cached_value

    merged["tenure_current_employer_years"] = merged.get("tenure_current_employer_years", 0) or 0
    merged["employer_inferred"] = merged.get("employer_inferred") or "Unknown"
    merged["employer_confidence"] = merged.get("employer_confidence") or "low"
    merged["tenure_confidence"] = merged.get("tenure_confidence") or "unknown"
    merged["classification_confidence"] = merged.get("classification_confidence") or "low"
    return merged


def build_fallback_enrichment(contributor: dict) -> dict:
    """
    Purpose: Create a safe enrichment fallback when no LinkedIn data can be parsed.
    Input: A contributor row with repo and internal/external classification.
    Output: Returns a contributor row with conservative employer and tenure defaults.
    """
    repo_company = get_repo_company(contributor.get("repo", ""))
    fallback_employer = "Unknown"
    if contributor.get("internal_or_external") == "internal":
        fallback_employer = repo_company

    fallback = contributor.copy()
    fallback.update({
        "current_company": "",
        "current_title": "",
        "employer_inferred": fallback_employer,
        "employer_confidence": "low",
        "tenure_current_employer_years": 0,
        "tenure_confidence": "unknown",
        "classification_confidence": fallback.get("classification_confidence", "low"),
    })
    return fallback


def scrape_profile(linkedin_url: str) -> dict:
    normalized_url = normalize_linkedin_url(linkedin_url)
    if normalized_url in LOCAL_PROFILE_CACHE:
        return LOCAL_PROFILE_CACHE[normalized_url]

    api_key = os.environ.get("SCRAPIN_API_KEY", "")
    if not api_key:
        logger.warning("SCRAPIN_API_KEY not set in .env")
        return {}

    try:
        response = requests.get(
            SCRAPIN_ENDPOINT,
            params={
                "apikey": api_key,
                "linkedInUrl": linkedin_url,
            },
            timeout=30,
        )

        if response.status_code != 200:
            logger.warning(f"Scrapin returned {response.status_code} for {linkedin_url}")
            return {}

        data = response.json()

        sample_path = CACHE_DIR / "sample_profile_raw.json"
        if not sample_path.exists():
            with open(sample_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved raw sample → {sample_path}")

        return data

    except Exception as e:
        logger.fail(f"Error scraping {linkedin_url}: {e}")
        return {}


def extract_current_position(profile: dict) -> dict:
    result = {
        "current_company": "",
        "current_title": "",
        "tenure_years": None,
        "tenure_confidence": "unknown",
    }

    person = profile.get("person") or profile.get("data") or profile

    result["current_company"] = (
        person.get("currentCompanyName")
        or person.get("current_company")
        or (person.get("currentPosition") or {}).get("companyName", "")
        or ""
    )
    result["current_title"] = (
        person.get("headline")
        or person.get("title")
        or person.get("occupation")
        or (person.get("currentPosition") or {}).get("title", "")
        or ""
    )

    positions = (
        person.get("positions", {}).get("positionHistory")
        or person.get("experience")
        or []
    )

    current = next(
        (p for p in positions if is_current_position(p)),
        positions[0] if positions else None,
    )

    if current:
        if not result["current_company"]:
            result["current_company"] = (
                current.get("companyName")
                or current.get("company", "")
            )
        if not result["current_title"]:
            result["current_title"] = current.get("title", "")

        start = extract_start_date(current)
        if start:
            tenure = calculate_tenure(str(start))
            if tenure is not None:
                result["tenure_years"] = tenure
                result["tenure_confidence"] = "high"

    return result


def enrich_profiles(contributors: list) -> list:
    cached_rows, cached_by_identity, cached_by_url = load_enriched_cache()
    if cached_rows:
        logger.info("Loading enriched profiles from cache")

    enriched = []
    stats = {
        "cache_hits": 0,
        "local_profile_hits": 0,
        "api_attempts": 0,
        "fallbacks": 0,
    }

    for contributor in tqdm(contributors, desc="Scraping LinkedIn Profiles"):
        cached_enrichment = get_cached_enrichment(contributor, cached_by_identity, cached_by_url)
        if cached_enrichment:
            stats["cache_hits"] += 1
            enriched.append(merge_cached_enrichment(contributor, cached_enrichment))
            continue

        url = contributor.get("linkedin_url", "")
        repo_company = get_repo_company(contributor.get("repo", ""))

        if not url.startswith("http"):
            stats["fallbacks"] += 1
            enriched.append(build_fallback_enrichment(contributor))
            continue

        try:
            normalized_url = normalize_linkedin_url(url)
            if normalized_url in LOCAL_PROFILE_CACHE:
                stats["local_profile_hits"] += 1
            else:
                stats["api_attempts"] += 1

            profile = scrape_profile(url)
            if not profile:
                raise ValueError(f"No profile data available for {url}")

            position = extract_current_position(profile)
            employer = bucket_employer(position["current_company"])
            refined_status, refined_confidence = infer_internal_or_external(
                contributor,
                position["current_company"],
                employer,
            )

            if normalized_url not in LOCAL_PROFILE_CACHE and os.environ.get("SCRAPIN_API_KEY", ""):
                time.sleep(6.1)

            if employer == "Unknown" and refined_status == "internal" and not position["current_company"]:
                employer = repo_company

            enriched_contributor = contributor.copy()
            enriched_contributor.update({
                "current_company": position["current_company"],
                "current_title": position["current_title"],
                "employer_inferred": employer,
                "employer_confidence": "high" if employer != "Unknown" and position["current_company"] else "low",
                "tenure_current_employer_years": position["tenure_years"] or 0,
                "tenure_confidence": position["tenure_confidence"],
                "internal_or_external": refined_status,
                "classification_confidence": refined_confidence,
            })
            enriched.append(enriched_contributor)
        except Exception as exc:
            logger.warning(
                f"Falling back to non-API enrichment for {contributor.get('github_login', '')}: {exc}"
            )
            stats["fallbacks"] += 1
            enriched.append(build_fallback_enrichment(contributor))

    combined_cache = {
        (row.get("repo", ""), row.get("github_login", "")): row
        for row in cached_rows
        if row.get("repo") and row.get("github_login")
    }
    for row in enriched:
        combined_cache[(row.get("repo", ""), row.get("github_login", ""))] = row

    with open(ENRICHED_CACHE_PATH, "w", encoding="utf-8") as file_handle:
        json.dump(list(combined_cache.values()), file_handle, indent=2)

    found = sum(1 for c in enriched if c.get("employer_inferred") not in ("Unknown", "Bot", ""))
    logger.success(f"Enriched {len(enriched)} — {found} employers identified")
    logger.info(
        "Enrichment sources: "
        f"{stats['cache_hits']} cached, "
        f"{stats['local_profile_hits']} local-profile, "
        f"{stats['api_attempts']} api-attempted, "
        f"{stats['fallbacks']} fallback"
    )
    return enriched
