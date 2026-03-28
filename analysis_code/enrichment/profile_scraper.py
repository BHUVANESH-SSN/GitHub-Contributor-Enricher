"""
Purpose: Scrapes LinkedIn profiles to extract current employer and calculate tenure.
Input: List of contributors with a 'linkedin_url'.
Output: List of contributors enriched with employer and tenure estimates.
"""
import json
import requests
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from analysis_code.utils.logger import logger
from analysis_code.utils.config import SCRAPIN_ENDPOINT
from tqdm import tqdm

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True, parents=True)


def bucket_employer(company: str) -> str:
    if not company:
        return "Unknown"
    c = company.lower()
    
    if "openai" in c: return "OpenAI"
    if "google" in c or "alphabet" in c or "deepmind" in c: return "Google"
    if "anthropic" in c: return "Anthropic"
    if "xai" in c or "x.ai" in c: return "xAI"
    
    return company

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


def scrape_profile(linkedin_url: str) -> dict:
    api_key = os.environ.get("SCRAPIN_API_KEY", "")
    if not api_key:
        logger.warning("SCRAPIN_API_KEY not set in .env")
        return {}

    try:
        response = requests.get(
            SCRAPIN_ENDPOINT,
            params={
                "apikey":      api_key,
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
        "current_company":   "",
        "current_title":     "",
        "tenure_years":      None,
        "tenure_confidence": "unknown",
    }

    person = profile.get("person") or profile

    result["current_company"] = (
        person.get("currentCompanyName")
        or person.get("current_company")
        or ""
    )
    result["current_title"] = (
        person.get("headline")
        or person.get("title")
        or person.get("occupation")
        or ""
    )

    positions = (
        person.get("positions", {}).get("positionHistory")
        or person.get("experience")
        or []
    )

    current = next(
        (p for p in positions if not p.get("endEndDate") and not p.get("end_date")),
        positions[0] if positions else None
    )

    if current:
        if not result["current_company"]:
            result["current_company"] = (
                current.get("companyName")
                or current.get("company", "")
            )
        if not result["current_title"]:
            result["current_title"] = current.get("title", "")

        start = (
            current.get("startEndDate")
            or current.get("start_date")
        )
        if isinstance(start, dict):
            year  = start.get("year")
            month = start.get("month", 1)
            start = f"{year}-{str(month).zfill(2)}" if year else None

        if start:
            tenure = calculate_tenure(str(start))
            if tenure is not None:
                result["tenure_years"]      = tenure
                result["tenure_confidence"] = "high"

    return result


def enrich_profiles(contributors: list) -> list:
    cache_file = CACHE_DIR / "enriched_profiles.json"

    if cache_file.exists():
        logger.info("Loading enriched profiles from cache")
        with open(cache_file) as f:
            return json.load(f)

    enriched = []

    for contributor in tqdm(contributors, desc="Scraping LinkedIn Profiles"):
        url = contributor.get("linkedin_url", "")

        if not url.startswith("http"):
            contributor.update({
                "current_company":               "",
                "current_title":                 "",
                "employer_inferred":             "Unknown",
                "employer_confidence":           "unknown",
                "tenure_current_employer_years": 0,
                "tenure_confidence":             "unknown",
            })
            enriched.append(contributor)
            continue

        profile  = scrape_profile(url)
        position = extract_current_position(profile)
        employer = bucket_employer(position["current_company"])

        time.sleep(6.1)

        if employer in ("Unknown", "Other", ""):
            if contributor.get("internal_or_external") == "internal":
                repo = contributor.get("repo", "")
                employer = "OpenAI" if "openai" in repo else "Google"

        contributor.update({
            "current_company":               position["current_company"],
            "current_title":                 position["current_title"],
            "employer_inferred":             employer,
            "employer_confidence":           "high" if position["tenure_years"] else contributor.get("classification_confidence", "low"),
            "tenure_current_employer_years": position["tenure_years"] or 0,
            "tenure_confidence":             position["tenure_confidence"],
        })
        enriched.append(contributor)

    with open(cache_file, "w") as f:
        json.dump(enriched, f, indent=2)

    found = sum(1 for c in enriched if c.get("employer_inferred") not in ("Unknown", "Bot", ""))
    logger.success(f"Enriched {len(enriched)} — {found} employers identified")
    return enriched