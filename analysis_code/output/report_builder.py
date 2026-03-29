"""
Purpose: Build the markdown report that summarizes repository contribution metrics.
Input: The cleaned contributor dataset as a pandas DataFrame.
Output: Returns the markdown text and writes `report.md` to the project root.
"""
import pandas as pd

from analysis_code.output.internal_external_summary_builder import summarize_repo
from analysis_code.utils.logger import logger


def build_report(df: pd.DataFrame) -> str:
    logger.info("Generating markdown report")

    report = ["# GitHub Contributor Enrichment Report\n"]

    report.append("## Scope\n")
    report.append("This report summarizes the contributor analysis for `openai/codex` and `google-gemini/gemini-cli`.\n")
    report.append("- Contribution metric: commit count")
    report.append("- Top contributor cutoff: top 20 contributors per repository")
    report.append("- Bot accounts are excluded from the final analyzed dataset\n")

    report.append("## All-Contributors Internal vs External Summary\n")
    report.append("The section below summarizes internal vs external contribution on the full contributor lists returned by the GitHub contributors API, including bot and automation accounts.\n")
    repos = df["repo"].unique()
    for repo in repos:
        summary = summarize_repo(repo)

        report.append(f"### {repo}")
        report.append(f"- Total contributor accounts analyzed: {summary.total_contributors}")
        report.append(f"- Internal contributors: {summary.internal_contributors}")
        report.append(f"- External contributors: {summary.external_contributors}")
        report.append(f"- Internal contributor share: {(summary.internal_contributors / summary.total_contributors * 100) if summary.total_contributors else 0:.1f}%")
        report.append(f"- External contributor share: {(summary.external_contributors / summary.total_contributors * 100) if summary.total_contributors else 0:.1f}%")
        report.append(f"- Internal commit share: {summary.internal_commits} commits ({(summary.internal_commits / summary.total_commits * 100) if summary.total_commits else 0:.1f}%)")
        report.append(f"- External commit share: {summary.external_commits} commits ({(summary.external_commits / summary.total_commits * 100) if summary.total_commits else 0:.1f}%)")
        report.append(f"- Internal merged PR share: {summary.internal_prs} PRs ({(summary.internal_prs / summary.total_attributable_prs * 100) if summary.total_attributable_prs else 0:.1f}%)")
        report.append(f"- External merged PR share: {summary.external_prs} PRs ({(summary.external_prs / summary.total_attributable_prs * 100) if summary.total_attributable_prs else 0:.1f}%)")
        report.append(f"- Bot or automation accounts included in all-contributors totals: {summary.bot_accounts}\n")

    report.append("## Enriched Contributor Breakdown\n")
    report.append("The section below summarizes the final enriched contributor dataset used for LinkedIn URL, employer, and tenure output.\n")

    for repo in repos:
        repo_df = df[df["repo"] == repo]
        total_contributors = len(repo_df)

        internal_df = repo_df[repo_df["internal_or_external"] == "internal"]
        external_df = repo_df[repo_df["internal_or_external"] == "external"]

        internal_count = len(internal_df)
        external_count = len(external_df)

        internal_pct = (internal_count / total_contributors * 100) if total_contributors > 0 else 0
        external_pct = (external_count / total_contributors * 100) if total_contributors > 0 else 0

        total_commits = pd.to_numeric(repo_df["contribution_metric"], errors="coerce").sum()
        internal_commits = pd.to_numeric(internal_df["contribution_metric"], errors="coerce").sum()
        external_commits = pd.to_numeric(external_df["contribution_metric"], errors="coerce").sum()

        internal_commit_pct = (internal_commits / total_commits * 100) if total_commits > 0 else 0
        external_commit_pct = (external_commits / total_commits * 100) if total_commits > 0 else 0

        report.append(f"### {repo}")
        report.append(f"- Total enriched contributors analyzed: {total_contributors}")
        report.append(f"- Internal contributors: {internal_count}")
        report.append(f"- External contributors: {external_count}")
        report.append(f"- Internal contributor share: {internal_pct:.1f}%")
        report.append(f"- External contributor share: {external_pct:.1f}%")
        report.append(f"- Internal contribution share: {internal_commits:.0f} commits ({internal_commit_pct:.1f}%)")
        report.append(f"- External contribution share: {external_commits:.0f} commits ({external_commit_pct:.1f}%)\n")

    report.append("## Contributors\n")
    df["contribution_metric_num"] = pd.to_numeric(df["contribution_metric"], errors="coerce")
    report.append("The tables below list all analyzed contributors per repository from the final dataset.\n")

    for repo in repos:
        repo_df = df[df["repo"] == repo].sort_values("contribution_metric_num", ascending=False)
        report.append(f"### {repo}")
        report.append("| GitHub Login | Contribution Metric | Internal or External | Employer Inferred | Employer Confidence | LinkedIn URL | Tenure at Current Employer (Years) | Tenure Confidence |")
        report.append("|---|---:|---|---|---|---|---:|---|")

        for _, row in repo_df.iterrows():
            tenure = pd.to_numeric(row["tenure_current_employer_years"], errors="coerce")
            tenure_str = f"{tenure:.1f}" if pd.notnull(tenure) else "0.0"
            linkedin_url = ""
            if pd.notna(row["linkedin_url"]):
                linkedin_url = str(row["linkedin_url"])
            report.append(
                f"| {row['github_login']} | {row['contribution_metric']} | {row['internal_or_external']} | "
                f"{row['employer_inferred']} | {row['employer_confidence']} | {linkedin_url} | "
                f"{tenure_str} | {row['tenure_confidence']} |"
            )
        report.append("")

    report.append("\n## Methodology\n")
    report.append("1. Contributor data was collected from the GitHub API.")
    report.append("2. Contributors were initially classified as internal or external using public GitHub metadata.")
    report.append("3. LinkedIn URLs were resolved using an Apify search workflow.")
    report.append("4. LinkedIn profile data was enriched from local cache and profile scraping results to infer employer and tenure.")
    report.append("5. Employer values were bucketed to the target set: `OpenAI`, `Google`, `Anthropic`, `xAI`, or `Unknown`.\n")

    report.append("## Notes and Assumptions\n")
    report.append("- The process is automated and avoids manual profile lookups.")
    report.append("- Rows with incomplete enrichment are retained with `Unknown`, empty URLs, or lower-confidence values where needed.")
    report.append("- Internal vs external status may be refined after enrichment when employment data provides a stronger signal than GitHub metadata.")

    report_text = "\n".join(report)

    output_path = "report.md"
    logger.info(f"Saving report to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    return report_text
