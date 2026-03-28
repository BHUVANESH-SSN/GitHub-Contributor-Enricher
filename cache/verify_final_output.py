import pandas as pd
import json

df_cleaned = pd.read_csv("dataset_cleaned.csv")

with open("cache/final_output.json", "r") as f:
    final_output = json.load(f)

# normalize urls
def normalize_url(url):
    if not isinstance(url, str): return ""
    return url.lower().replace("am.linkedin.com", "www.linkedin.com").rstrip('/')

# Create dictionary based on linkedin URLs
json_data_map = {normalize_url(item.get("linkedin_url", "")): item for item in final_output if item.get("linkedin_url")}

mismatches = []
matches = 0

for idx, row in df_cleaned.iterrows():
    csv_url = normalize_url(row["linkedin_url"])
    if csv_url in json_data_map:
        json_company = json_data_map[csv_url].get("company")
        csv_company = row["employer_inferred"]
        
        # simple check. note json_company might be null/None
        if json_company is None:
            json_company = "Unknown"
            
        if pd.isna(csv_company):
            csv_company = "Unknown"
            
        if str(json_company).lower() != str(csv_company).lower():
            # Sometimes openai / google normalization happened.
            mismatches.append(f"{row['github_login']}: CSV says '{csv_company}', JSON says '{json_company}'")
        else:
            matches += 1

print(f"Total rows in dataset_cleaned.csv: {len(df_cleaned)}")
print(f"Total matching URLs from final_output.json: {matches + len(mismatches)}")
print(f"Exact company matches: {matches}")
print(f"Mismatches or overrides (like converting 'OpenAI' string): {len(mismatches)}")
for m in mismatches[:10]:
    print("  -", m)

