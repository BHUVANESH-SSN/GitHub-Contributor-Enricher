"""
Purpose: Convert enriched contributor records into the final dataset table.
Input: A list of contributor dictionaries produced by the enrichment pipeline.
Output: Returns a pandas DataFrame and writes `dataset.csv` to the project root.
"""
import pandas as pd
from typing import Dict, List

from analysis_code.utils.logger import logger


def build_dataset(all_contributors: List[Dict]) -> pd.DataFrame:
    logger.info("Building dataset DataFrame")

    columns = [
        "repo", "github_login", "github_id", "name", "contribution_metric",
        "internal_or_external", "classification_confidence",
        "employer_inferred", "employer_confidence", "linkedin_url",
        "tenure_current_employer_years", "tenure_confidence"
    ]

    df = pd.DataFrame(all_contributors)

    for col in columns:
        if col not in df.columns:
            df[col] = ""

    df = df[columns].copy()

    df["linkedin_url"] = df["linkedin_url"].fillna("")
    df["employer_inferred"] = df["employer_inferred"].replace("", "Unknown").fillna("Unknown")
    df["employer_confidence"] = df["employer_confidence"].replace("", "unknown").fillna("unknown")

    pd.set_option("future.no_silent_downcasting", True)
    df["tenure_current_employer_years"] = df["tenure_current_employer_years"].fillna(0).infer_objects(copy=False)

    df = df.fillna("")

    df = df[~df["github_login"].astype(str).str.lower().str.contains("bot|robot", regex=True)].copy()

    df.loc[df["name"].astype(str).str.strip() == "", "name"] = df["github_login"]

    output_path = "dataset.csv"
    logger.info(f"Saving dataset to {output_path}")
    df.to_csv(output_path, index=False)

    return df
