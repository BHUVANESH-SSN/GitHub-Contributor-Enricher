import pandas as pd
import json
from datetime import datetime

# 1. Load your existing imperfect CSV
df = pd.read_csv("dataset.csv")

# 2. Load your newly scraped JSON data
# (Change this filename to "final_output.json" if that's what you named it)
with open("cache/reverse_connect.json", "r") as f:
    scraped_data = json.load(f)

# 3. Build a dictionary mapping URLs to the new data
enrichment_map = {}
for item in scraped_data:
    # Ensure this index actually succeeded
    if "data" in item and item["data"]:
        data = item["data"]
        
        # Normalize URL to match the ones in CSV safely
        url = data.get("linkedinUrl", "")
        if not url:
            continue
            
        clean_url = url.lower().replace("am.linkedin.com", "www.linkedin.com").rstrip('/')

        # Extract Current Company
        employer = "Unknown"
        experience = data.get("experience", [])
        if experience:
            # Usually the first object is the current job
            employer = str(experience[0].get("companyName", "Unknown") or "Unknown")
            
            # Simple matching for our buckets
            emp_lower = employer.lower()
            if "openai" in emp_lower: employer = "OpenAI"
            elif "google" in emp_lower or "alphabet" in emp_lower: employer = "Google"

        # Extract Tenure (Calculate strictly relative to the year 2026)
        tenure_years = 0
        if experience:
            start_date_dict = experience[0].get("startEndDate", {})
            if start_date_dict and "start" in start_date_dict and start_date_dict["start"]:
                try:
                    # Scrapin formats dates like "2025-12-01T00:00:00.000Z"
                    start_str = start_date_dict["start"]
                    start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    year = start_dt.year
                    month = start_dt.month
                    
                    # Math: Calculate exact decimal years relative to March 2026
                    # (2026 minus their start year, plus the fractional month difference)
                    current_year = 2026
                    current_month = 3
                    
                    # Calculate total months difference
                    total_months = ((current_year - year) * 12) + (current_month - month)
                    
                    # Convert total months to decimal years
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

# 4. Loop through the rows of the CSV and merge in the scraped data!
df["tenure_current_employer_years"] = df["tenure_current_employer_years"].astype(float)

for index, row in df.iterrows():
    csv_url = str(row["linkedin_url"]).lower().replace("am.linkedin.com", "www.linkedin.com").rstrip('/')
    
    if csv_url in enrichment_map:
        new_data = enrichment_map[csv_url]
        df.at[index, "employer_inferred"] = new_data["employer_inferred"]
        df.at[index, "employer_confidence"] = new_data["employer_confidence"]
        df.at[index, "tenure_current_employer_years"] = new_data["tenure_current_employer_years"]
        df.at[index, "tenure_confidence"] = new_data["tenure_confidence"]

# 5. Save the perfectly filled out CSV!
df.to_csv("dataset_filled.csv", index=False)
print("Successfully merged scraped data into dataset_filled.csv!")