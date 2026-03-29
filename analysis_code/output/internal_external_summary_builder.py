"""
Purpose: Build a repository-wide internal vs external contribution summary on an all-contributors basis.
Input: Full contributor, classification, and merged PR cache files under `cache/`.
Output: Writes `internal_vs_external_commits_pr.md` in the project root and returns the markdown text.
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from analysis_code.utils.config import REPOS
from analysis_code.utils.logger import logger


CACHE_DIR = Path("cache")
OUTPUT_PATH = Path("internal_vs_external_commits_pr.md")


@dataclass
class RepoSummary:
    repo: str
    total_contributors: int
    internal_contributors: int
    external_contributors: int
    bot_accounts: int
    total_commits: int
    internal_commits: int
    external_commits: int
    total_attributable_prs: int
    internal_prs: int
    external_prs: int
    missing_pr_authors: int
    missing_pr_count: int


def load_json_file(path: Path) -> list | dict:
    with open(path, "r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def get_repo_cache_slug(repo_name: str) -> str:
    return repo_name.replace("/", "_")


def is_bot_account(contributor: Dict) -> bool:
    login = str(contributor.get("github_login", "")).lower()
    return bool(
        contributor.get("is_bot")
        or "[bot]" in login
        or "robot" in login
    )


def load_classified_contributors(repo_name: str) -> List[Dict]:
    """
    Purpose: Load the full contributor list and merge in cached internal/external classification data.
    Input: A repository slug from `REPOS`.
    Output: Returns contributor dictionaries for every contributor account in the cache.
    """
    repo_slug = get_repo_cache_slug(repo_name)
    contributors_path = CACHE_DIR / f"contributors_{repo_slug}.json"
    classified_path = CACHE_DIR / f"classified_users_{repo_slug}.json"

    if not contributors_path.exists():
        raise FileNotFoundError(f"Missing contributor cache: {contributors_path}")
    if not classified_path.exists():
        raise FileNotFoundError(f"Missing classified cache: {classified_path}")

    contributors = load_json_file(contributors_path)
    classified_rows = load_json_file(classified_path)
    classified_map = {row.get("github_login"): row for row in classified_rows}

    merged_rows: List[Dict] = []
    for contributor in contributors:
        merged = contributor.copy()
        classified = classified_map.get(contributor.get("github_login"), {})
        merged["internal_or_external"] = classified.get("internal_or_external", "unknown")
        merged["classification_confidence"] = classified.get("classification_confidence", "unknown")
        if "is_bot" in classified:
            merged["is_bot"] = classified["is_bot"]
        merged_rows.append(merged)

    return merged_rows


def summarize_repo(repo_name: str) -> RepoSummary:
    """
    Purpose: Compute contributor counts and contribution-share metrics for one repository.
    Input: A repository slug from `REPOS`.
    Output: Returns a `RepoSummary` with counts for contributors, commits, and merged PRs.
    """
    repo_slug = get_repo_cache_slug(repo_name)
    contributors = load_classified_contributors(repo_name)
    prs_path = CACHE_DIR / f"prs_{repo_slug}.json"

    if not prs_path.exists():
        raise FileNotFoundError(f"Missing PR cache: {prs_path}")

    prs_by_login: Dict[str, int] = load_json_file(prs_path)
    contributor_logins = {row["github_login"] for row in contributors}

    internal_rows = [row for row in contributors if row.get("internal_or_external") == "internal"]
    external_rows = [row for row in contributors if row.get("internal_or_external") == "external"]

    missing_pr_authors = {
        login: count for login, count in prs_by_login.items() if login not in contributor_logins
    }

    return RepoSummary(
        repo=repo_name,
        total_contributors=len(contributors),
        internal_contributors=len(internal_rows),
        external_contributors=len(external_rows),
        bot_accounts=sum(1 for row in contributors if is_bot_account(row)),
        total_commits=sum(int(row.get("commit_count", 0)) for row in contributors),
        internal_commits=sum(int(row.get("commit_count", 0)) for row in internal_rows),
        external_commits=sum(int(row.get("commit_count", 0)) for row in external_rows),
        total_attributable_prs=sum(
            count for login, count in prs_by_login.items() if login in contributor_logins
        ),
        internal_prs=sum(prs_by_login.get(row["github_login"], 0) for row in internal_rows),
        external_prs=sum(prs_by_login.get(row["github_login"], 0) for row in external_rows),
        missing_pr_authors=len(missing_pr_authors),
        missing_pr_count=sum(missing_pr_authors.values()),
    )


def pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator * 100


def build_internal_external_summary(repo_names: List[str] | None = None) -> str:
    """
    Purpose: Generate the standalone markdown summary for Part 1 of the take-home task.
    Input: An optional list of repository slugs. Defaults to `REPOS`.
    Output: Returns the markdown text and writes `internal_vs_external_commits_pr.md`.
    """
    selected_repos = repo_names or REPOS
    summaries = [summarize_repo(repo_name) for repo_name in selected_repos]

    report: List[str] = [
        "# Internal vs External Contributions on All-Contributors Basis",
        "",
        "This file summarizes Part 1 of the take-home task using the full contributor lists returned by the GitHub contributors API for each repository.",
        "",
        "Scope used for this calculation:",
        "- all contributor accounts in the cached GitHub contributors files",
        "- internal vs external labels from the full classified contributor caches",
        "",
        "Notes:",
        "- Bot and automation accounts are included in the all-contributors totals because this file is based on the full contributor lists.",
        "- Bot accounts are classified as `external` by the current pipeline.",
        "- Commit share uses total commit counts from the GitHub contributors API.",
        "- Merged PR share uses merged PRs attributable to contributor accounts present in the contributors cache.",
        "",
    ]

    for summary in summaries:
        report.extend([
            f"## {summary.repo}",
            "",
            "### Contributor Count",
            "",
            f"- Total contributor accounts analyzed: {summary.total_contributors}",
            f"- Internal contributors: {summary.internal_contributors}",
            f"- External contributors: {summary.external_contributors}",
            f"- Internal contributor share: {pct(summary.internal_contributors, summary.total_contributors):.1f}%",
            f"- External contributor share: {pct(summary.external_contributors, summary.total_contributors):.1f}%",
            f"- Bot or automation accounts included in total: {summary.bot_accounts}",
            "",
            "### Commit Share",
            "",
            f"- Total commits: {summary.total_commits}",
            f"- Internal commits: {summary.internal_commits}",
            f"- External commits: {summary.external_commits}",
            f"- Internal commit share: {pct(summary.internal_commits, summary.total_commits):.1f}%",
            f"- External commit share: {pct(summary.external_commits, summary.total_commits):.1f}%",
            "",
            "### Merged PR Share",
            "",
            f"- Total merged PRs attributable to contributor accounts: {summary.total_attributable_prs}",
            f"- Internal merged PRs: {summary.internal_prs}",
            f"- External merged PRs: {summary.external_prs}",
            f"- Internal merged PR share: {pct(summary.internal_prs, summary.total_attributable_prs):.1f}%",
            f"- External merged PR share: {pct(summary.external_prs, summary.total_attributable_prs):.1f}%",
            f"- Merged PR authors missing from the contributor cache: {summary.missing_pr_authors}",
            f"- Merged PRs not attributable to accounts in the contributor cache: {summary.missing_pr_count}",
            "",
        ])

    report_text = "\n".join(report)
    logger.info(f"Saving internal vs external summary to {OUTPUT_PATH}")
    OUTPUT_PATH.write_text(report_text, encoding="utf-8")
    return report_text


if __name__ == "__main__":
    build_internal_external_summary()
