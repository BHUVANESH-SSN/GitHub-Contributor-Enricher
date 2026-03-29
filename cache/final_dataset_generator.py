"""
Purpose: Merge reverse-connect enrichment results into the base dataset and produce cleaned variants.
Input: Reads `dataset.csv` and `cache/reverse_connect.json`.
Output: Writes `dataset_filled.csv` and `dataset_cleaned.csv`.
"""
import json
from datetime import datetime

import pandas as pd


def normalize_url(url: str) -> str:
    return str(url).lower().replace("am.linkedin.com", "www.linkedin.com").rstrip("/")


df = pd.read_csv("dataset.csv", na_values=["", "nan", "NaN"])
df["name"] = df["name"].fillna("")
df["linkedin_url"] = df["linkedin_url"].fillna("")

with open("cache/reverse_connect.json", "r") as f:
    scraped_data = json.load(f)

url_to_data = {}
for item in scraped_data:
    if "data" in item and item["data"]:
        url = item["data"].get("linkedinUrl", "")
        if url:
            clean_url = normalize_url(url)
            exp = item["data"].get("experience", [])
            employer = "Unknown"
            tenure_years = 0.0

            if exp:
                employer = str(exp[0].get("companyName", "Unknown") or "Unknown")

                start_date_dict = exp[0].get("startEndDate", {})
                if start_date_dict and "start" in start_date_dict and start_date_dict["start"]:
                    try:
                        start_dt = datetime.fromisoformat(start_date_dict["start"].replace("Z", "+00:00"))
                        total_months = ((2026 - start_dt.year) * 12) + (3 - start_dt.month)
                        if total_months >= 0:
                            tenure_years = round(total_months / 12.0, 1)
                    except Exception:
                        pass

            url_to_data[clean_url] = {
                "employer": employer,
                "tenure": tenure_years,
            }

df["tenure_current_employer_years"] = df["tenure_current_employer_years"].astype(float)
for idx, row in df.iterrows():
    csv_url = normalize_url(row["linkedin_url"])
    if csv_url in url_to_data:
        real_data = url_to_data[csv_url]
        df.at[idx, "employer_inferred"] = real_data["employer"]
        df.at[idx, "tenure_current_employer_years"] = real_data["tenure"]
        df.at[idx, "employer_confidence"] = "high"

        emp_lower = real_data["employer"].lower()
        if "openai" in emp_lower or "google" in emp_lower or "alphabet" in emp_lower:
            df.at[idx, "internal_or_external"] = "internal"

df["tenure_current_employer_years"] = pd.to_numeric(df["tenure_current_employer_years"], errors="coerce").fillna(0.0).round(1)

df.to_csv("dataset_filled.csv", index=False)

df_cleaned = df[~df["github_login"].str.lower().str.contains("bot")].copy()

df_cleaned.loc[df_cleaned["name"].str.strip() == "", "name"] = df_cleaned["github_login"]

cond_drop = (df_cleaned["employer_inferred"] == "Unknown") & (df_cleaned["linkedin_url"].str.strip() == "")
df_cleaned = df_cleaned[~cond_drop]

df_cleaned.to_csv("dataset_cleaned.csv", index=False)
print(f"Generated dataset_filled.csv and dataset_cleaned.csv successfully!")
