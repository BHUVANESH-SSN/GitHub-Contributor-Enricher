"""
Purpose: Replace unknown employer values in dataset variants using reverse-connect data.
Input: Reads `cache/reverse_connect.json`, `dataset_filled.csv`, and `dataset_cleaned.csv`.
Output: Rewrites the dataset CSV files with updated employer values when matches are found.
"""
import json

import pandas as pd

with open("cache/reverse_connect.json", "r") as f:
    scraped_data = json.load(f)

url_to_company = {}
for item in scraped_data:
    if "data" in item and item["data"]:
        url = item["data"].get("linkedinUrl", "")
        if url:
            clean = url.lower().replace("am.linkedin.com", "www.linkedin.com").rstrip("/")
            exp = item["data"].get("experience", [])
            employer = "Unknown"
            if exp:
                employer = str(exp[0].get("companyName", "Unknown") or "Unknown")

            emp_lower = employer.lower()
            if "openai" in emp_lower:
                employer = "OpenAI"
            elif "google" in emp_lower or "alphabet" in emp_lower:
                employer = "Google"

            url_to_company[clean] = employer


def fix_df(filepath: str) -> None:
    df = pd.read_csv(filepath)
    initial_unknowns = (df["employer_inferred"] == "Unknown").sum()

    for idx, row in df.iterrows():
        csv_url = str(row["linkedin_url"]).lower().replace("am.linkedin.com", "www.linkedin.com").rstrip("/")
        if csv_url in url_to_company:
            real_company = url_to_company[csv_url]
            if df.at[idx, "employer_inferred"] == "Unknown" and real_company != "Unknown":
                df.at[idx, "employer_inferred"] = real_company
                df.at[idx, "employer_confidence"] = "high"

    final_unknowns = (df["employer_inferred"] == "Unknown").sum()
    print(f"{filepath}: Fixed {initial_unknowns - final_unknowns} Unknowns. Now only {final_unknowns} remain.")
    df.to_csv(filepath, index=False)


fix_df("dataset_filled.csv")
fix_df("dataset_cleaned.csv")
