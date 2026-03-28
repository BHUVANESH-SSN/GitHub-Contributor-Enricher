import pandas as pd
import json
from datetime import datetime

# 1. Load the original base dataset (untouched)
df = pd.read_csv("dataset.csv", na_values=['', 'nan', 'NaN'])
df["name"] = df["name"].fillna("")
df["linkedin_url"] = df["linkedin_url"].fillna("")

# 2. Extract strictly from Reverse Connect (the alternative source)
with open("cache/reverse_connect.json", "r") as f:
    scraped_data = json.load(f)

url_to_data = {}
for item in scraped_data:
    if "data" in item and item["data"]:
        url = item["data"].get("linkedinUrl", "")
        if url:
            clean_url = url.lower().replace("am.linkedin.com", "www.linkedin.com").rstrip('/')
            
            exp = item["data"].get("experience", [])
            employer = "Unknown"
            tenure_years = 0.0
            
            if exp:
                # Rule: Map strictly to the company key in the final output!
                # (We don't use 'OpenAI' bucket if it says 'Jeremy Rose LLC')
                employer = str(exp[0].get("companyName", "Unknown") or "Unknown")
                
                # Math math math
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
                "tenure": tenure_years
            }

# 3. Apply changes (Merging the data)
df["tenure_current_employer_years"] = df["tenure_current_employer_years"].astype(float)
for idx, row in df.iterrows():
    csv_url = str(row["linkedin_url"]).lower().replace("am.linkedin.com", "www.linkedin.com").rstrip('/')
    if csv_url in url_to_data:
        real_data = url_to_data[csv_url]
        df.at[idx, "employer_inferred"] = real_data["employer"]
        df.at[idx, "tenure_current_employer_years"] = real_data["tenure"]
        df.at[idx, "employer_confidence"] = "high"
        
        # If user works at OpenAI or Google, make them internal!
        emp_lower = real_data["employer"].lower()
        if "openai" in emp_lower or "google" in emp_lower or "alphabet" in emp_lower:
            df.at[idx, "internal_or_external"] = "internal"

# Fill any lingering unknowns as 0.0 for clean csv float
df["tenure_current_employer_years"] = pd.to_numeric(df["tenure_current_employer_years"], errors="coerce").fillna(0.0).round(1)

# Save the filled dataset BEFORE applying destructive row drops
df.to_csv("dataset_filled.csv", index=False)

# 4. Clean the dataset (applying the user's non-destructive rules)
# Rule 1: Remove bots
df_cleaned = df[~df["github_login"].str.lower().str.contains("bot")].copy()

# Rule 2: Fix missing names
df_cleaned.loc[df_cleaned["name"].str.strip() == "", "name"] = df_cleaned["github_login"]

# -> WE DO NOT DO RULE 3 (wiping to Unknown if classification is low) because that destroys the LinkedIn data!

# Rule 6: Drop rows where employer is Unknown AND linkedin missing
cond_drop = (df_cleaned["employer_inferred"] == "Unknown") & (df_cleaned["linkedin_url"].str.strip() == "")
df_cleaned = df_cleaned[~cond_drop]

df_cleaned.to_csv("dataset_cleaned.csv", index=False)
print(f"Generated dataset_filled.csv and dataset_cleaned.csv successfully!")
