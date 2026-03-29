"""
Purpose: Merge reverse-connect enrichment data into the main dataset CSV.
Input: Reads `dataset.csv` and `cache/reverse_connect.json`.
Output: Writes `dataset_filled.csv` with employer and tenure fields updated.
"""
import json
from datetime import datetime

import pandas as pd


def normalize_url(url: str) -> str:
    return str(url).lower().replace("am.linkedin.com", "www.linkedin.com").rstrip("/")


df = pd.read_csv("dataset.csv")

with open("cache/reverse_connect.json", "r") as f:
    scraped_data = json.load(f)

enrichment_map = {}
for item in scraped_data:
    if "data" in item and item["data"]:
        data = item["data"]
        url = data.get("linkedinUrl", "")
        if not url:
            continue

        clean_url = normalize_url(url)

        employer = "Unknown"
        experience = data.get("experience", [])
        if experience:
            employer = str(experience[0].get("companyName", "Unknown") or "Unknown")

            emp_lower = employer.lower()
            if "openai" in emp_lower:
                employer = "OpenAI"
            elif "google" in emp_lower or "alphabet" in emp_lower:
                employer = "Google"

        tenure_years = 0
        if experience:
            start_date_dict = experience[0].get("startEndDate", {})
            if start_date_dict and "start" in start_date_dict and start_date_dict["start"]:
                try:
                    start_str = start_date_dict["start"]
                    start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    year = start_dt.year
                    month = start_dt.month
                    current_year = 2026
                    current_month = 3
                    total_months = ((current_year - year) * 12) + (current_month - month)
                    if total_months >= 0:
                        tenure_years = round(total_months / 12.0, 1)
                except Exception:
                    pass

        enrichment_map[clean_url] = {
            "employer_inferred": employer,
            "employer_confidence": "high" if employer != "Unknown" else "unknown",
            "tenure_current_employer_years": tenure_years,
            "tenure_confidence": "high" if tenure_years > 0 else "unknown"
        }

df["tenure_current_employer_years"] = df["tenure_current_employer_years"].astype(float)

for index, row in df.iterrows():
    csv_url = normalize_url(row["linkedin_url"])
    if csv_url in enrichment_map:
        new_data = enrichment_map[csv_url]
        df.at[index, "employer_inferred"] = new_data["employer_inferred"]
        df.at[index, "employer_confidence"] = new_data["employer_confidence"]
        df.at[index, "tenure_current_employer_years"] = new_data["tenure_current_employer_years"]
        df.at[index, "tenure_confidence"] = new_data["tenure_confidence"]

df.to_csv("dataset_filled.csv", index=False)
print("Successfully merged scraped data into dataset_filled.csv!")
