# GitHub Contributor Enrichment Report

## Scope

This report summarizes the take-home analysis for:
- `openai/codex`
- `google-gemini/gemini-cli`

Metric used for contribution share:
- commit count from the GitHub contributors API

Top contributor selection:
- top 20 contributors per repository were selected for enrichment
- this cutoff was chosen to capture the main contributors while keeping API usage and scraping cost manageable

Dataset note:
- the exported dataset excludes bot rows and rows with no useful enrichment signal, so the contributor counts below reflect the final checked-in dataset

## Contributor Breakdown

### openai/codex

- Total contributors analyzed: 16
- Internal contributors: 12
- External contributors: 4
- Internal contributor share: 75.0%
- External contributor share: 25.0%
- Internal contribution share: 2463 commits (86.1%)
- External contribution share: 396 commits (13.9%)

### google-gemini/gemini-cli

- Total contributors analyzed: 19
- Internal contributors: 16
- External contributors: 3
- Internal contributor share: 84.2%
- External contributor share: 15.8%
- Internal contribution share: 2769 commits (89.2%)
- External contribution share: 334 commits (10.8%)

## Top Contributors

The table below highlights the top 5 enriched contributors per repository from the current exported dataset.

### openai/codex

| GitHub Login | Contribution Metric | Internal or External | Employer Inferred | Employer Confidence | LinkedIn URL | Tenure at Current Employer (Years) | Tenure Confidence |
|---|---:|---|---|---|---|---:|---|
| bolinfest | 702 | internal | OpenAI | high | https://www.linkedin.com/in/michael-bolin-7632712 | 2.1 | high |
| aibrahim-oai | 457 | internal | OpenAI | high | https://www.linkedin.com/in/ahmedibrhm | 0.7 | high |
| pakrym-oai | 356 | internal | OpenAI | high | https://www.linkedin.com/in/pakrym | 1.0 | high |
| nornagon-openai | 199 | external | Jeremy Rose LLC | high | https://www.linkedin.com/in/jeremyerose | 0.7 | high |
| etraut-openai | 184 | internal | OpenAI | high | https://www.linkedin.com/in/eric-traut-79a815137 | 0.7 | high |

### google-gemini/gemini-cli

| GitHub Login | Contribution Metric | Internal or External | Employer Inferred | Employer Confidence | LinkedIn URL | Tenure at Current Employer (Years) | Tenure Confidence |
|---|---:|---|---|---|---|---:|---|
| scidomino | 363 | internal | Google | high | https://www.linkedin.com/in/tommasosciortino | 14.0 | high |
| NTaylorMullen | 330 | internal | Google | high | https://www.linkedin.com/in/ntaylormullen | 0.3 | high |
| abhipatel12 | 255 | internal | Google | high | https://www.linkedin.com/in/abhiyadav | 2.2 | high |
| jacob314 | 253 | internal | Google | high | https://www.linkedin.com/in/jacob-richman-5634565 | 0.8 | high |
| SandyTao520 | 199 | internal | Google | high | https://www.linkedin.com/in/sandytao520 | 3.8 | high |

## Methodology

1. Contributor data was fetched from the GitHub API.
2. Contributors were classified as internal or external using public GitHub metadata such as email domain, company, username patterns, and organization membership.
3. The top 20 contributors per repository were selected using commit count.
4. LinkedIn URLs were discovered using Apify's Google Search actor.
5. LinkedIn profile data was enriched using Scrapin.io to estimate current employer and tenure.

## Notes and Assumptions

- The process is automated and does not rely on manual profile lookups.
- Confidence fields are preserved in the dataset for downstream review.
- When a LinkedIn URL or reliable employment start date is unavailable, the pipeline falls back to empty fields, `Unknown`, or lower confidence values.
- The current implementation attempts to map target employers such as OpenAI, Google, Anthropic, and xAI, but may also preserve a scraped non-target employer name when one is detected.
