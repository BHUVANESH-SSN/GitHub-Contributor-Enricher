"""
Purpose: Clean an intermediate enriched CSV before final export.
Input: Reads `dataset_filled.csv` from the project root.
Output: Writes `dataset_cleaned.csv` with bots and low-value rows removed.
"""
import pandas as pd

df = pd.read_csv("dataset_filled.csv", na_values=["", "nan", "NaN"])
df["name"] = df["name"].fillna("")
df["linkedin_url"] = df["linkedin_url"].fillna("")

df = df[~df["github_login"].str.lower().str.contains("bot")]

df.loc[df["name"].str.strip() == "", "name"] = df["github_login"]

df.loc[df["classification_confidence"].str.lower() == "low", "employer_inferred"] = "Unknown"
df.loc[df["employer_confidence"].str.lower() == "unknown", "employer_inferred"] = "Unknown"

df.loc[df["employer_inferred"].isin(["OpenAI", "Google"]), "internal_or_external"] = "internal"
df.loc[(df["employer_inferred"].isin(["OpenAI", "Google"])) & (df["internal_or_external"] == "external"), "internal_or_external"] = "internal"

df["tenure_current_employer_years"] = pd.to_numeric(df["tenure_current_employer_years"], errors="coerce").fillna(0).round(1)

condition_drop = (df["employer_inferred"] == "Unknown") & (df["linkedin_url"].str.strip() == "")
df = df[~condition_drop]

df.to_csv("dataset_cleaned.csv", index=False)
print("Saved to dataset_cleaned.csv")
print(f"Final Row Count: {len(df)}")
