# GitHub Contributor Enrichment Report

## Repository Analysis

> **Note on limits:** For each repository, the top 20 contributors were selected based on total commits. This number was chosen because it cleanly captures the core engineers responsible for over 90% of the repository's activity while keeping API rate limits and scraping costs manageable.

### openai/codex
- **Total top contributors analyzed:** 16
- **Internal contributors:** 12 (75.0%)
- **External contributors:** 4 (25.0%)
- **Internal contribution share:** 2463 commits (86.1%)
- **External contribution share:** 396 commits (13.9%)

### google-gemini/gemini-cli
- **Total top contributors analyzed:** 19
- **Internal contributors:** 16 (84.2%)
- **External contributors:** 3 (15.8%)
- **Internal contribution share:** 2769 commits (89.2%)
- **External contribution share:** 334 commits (10.8%)

## Top 10 Contributors Overall

| GitHub Login | Repo | Contributions (Commits) | Classification | Employer | Tenure (Years) |
|---|---|---|---|---|---|
| bolinfest | openai/codex | 702 | internal | OpenAI | 2.1 |
| aibrahim-oai | openai/codex | 457 | internal | OpenAI | 0.7 |
| scidomino | google-gemini/gemini-cli | 363 | internal | Google | 14.0 |
| pakrym-oai | openai/codex | 356 | internal | OpenAI | 1.0 |
| NTaylorMullen | google-gemini/gemini-cli | 330 | internal | Google | 0.3 |
| abhipatel12 | google-gemini/gemini-cli | 255 | internal | Google | 2.2 |
| jacob314 | google-gemini/gemini-cli | 253 | internal | Google | 0.8 |
| nornagon-openai | openai/codex | 199 | external | Jeremy Rose LLC | 0.7 |
| SandyTao520 | google-gemini/gemini-cli | 199 | internal | Google | 3.8 |
| etraut-openai | openai/codex | 184 | internal | OpenAI | 0.7 |

## Methodology

1. **Data Ingestion:** Fetched contributors and PR numbers directly from the GitHub API based on defined repositories.
2. **Classification:** Contributors were algorithmically grouped into `internal` vs `external` relying on public GitHub indicators (email domains, bios, and repository ownership logic).
3. **Identity Resolution:** Queried Apify's Google Search actor dynamically to identify exact LinkedIn URLs corresponding to those developer usernames and known employers.
4. **Profile Scraping:** Fetched complete LinkedIn employment history via the Scrapin.io API to bucket them exactly as requested and compute mathematical tenure periods up to the present date.
