import pandas as pd
import numpy as np

# Load data
df = pd.read_csv("dataset_filled.csv", na_values=['', 'nan', 'NaN'])
df["name"] = df["name"].fillna("")
df["linkedin_url"] = df["linkedin_url"].fillna("")

# 1. Remove all bot accounts
# Filter out rows where github_login contains "bot" (case insensitive)
df = df[~df["github_login"].str.lower().str.contains("bot")]

# 2. Fix missing names
# If name is empty, replace with github_login
df.loc[df["name"].str.strip() == "", "name"] = df["github_login"]

# 3. Correct employer mapping
# If classification_confidence is "low", set employer_inferred to "Unknown"
# If employer_confidence is "unknown", set employer_inferred to "Unknown"
df.loc[df["classification_confidence"].str.lower() == "low", "employer_inferred"] = "Unknown"
df.loc[df["employer_confidence"].str.lower() == "unknown", "employer_inferred"] = "Unknown"

# 4. Fix internal vs external classification
# If employer is OpenAI or Google, internal_or_external = "internal"
df.loc[df["employer_inferred"].isin(["OpenAI", "Google"]), "internal_or_external"] = "internal"

# 7. Ensure consistency
# Ensure "internal" implies a known internal employer (if internal but employer is Unknown, must revert to external or maintain logic - as per instructions, only enforce the OpenAI/Google -> internal rule). But to avoid conflicting values (e.g. external + OpenAI), the rule above fixes it. If internal but employer is Unknown, keep it but ensure no external+OpenAI exists.
df.loc[(df["employer_inferred"].isin(["OpenAI", "Google"])) & (df["internal_or_external"] == "external"), "internal_or_external"] = "internal"


# 5. Clean tenure values
# Round to 1 decimal place. 
df["tenure_current_employer_years"] = pd.to_numeric(df["tenure_current_employer_years"], errors="coerce").fillna(0).round(1)

# If tenure is 0 or null, set it to 0 (leaving as 0 to preserve structure, or Nan if preferred by CSV, will export clean blanks)
# Will leave physical 0s for float consistency.

# 6. Remove low-quality rows
# Drop rows where employer_inferred = "Unknown" AND linkedin_url is missing
condition_drop = (df["employer_inferred"] == "Unknown") & (df["linkedin_url"].str.strip() == "")
df = df[~condition_drop]

# Export
df.to_csv("dataset_cleaned.csv", index=False)
print("Saved to dataset_cleaned.csv")
print(f"Final Row Count: {len(df)}")
