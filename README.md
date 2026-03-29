# GitHub Contributor Enrichment Take-Home

This repository contains an automated pipeline for the take-home task: estimate internal vs external contribution share for two repositories and enrich top contributors with LinkedIn URL, employer, and tenure signals.

Repositories analyzed:
- `openai/codex`
- `google-gemini/gemini-cli`

## Task Coverage

The project addresses both parts of the assignment:

1. Internal vs external contribution analysis
   - estimates internal vs external contributor counts
   - estimates internal vs external contribution share
   - uses commit count as the primary contribution metric

2. Contributor enrichment
   - finds LinkedIn profile URLs for top contributors
   - infers current employer
   - estimates tenure at current employer
   - preserves confidence fields for classification and tenure quality

The checked-in outputs are:
- `dataset.csv`
- `report.md`

## Approach

The pipeline is fully automated and uses multiple APIs/tools:

1. GitHub API
   - fetches contributors and merged pull request counts
   - collects GitHub profile metadata such as login, name, email, and company
   - classifies contributors as likely internal or external

2. Apify Google Search actor
   - searches for LinkedIn profile URLs using queries like `"{name} {company} site:linkedin.com/in"`
   - resolves contributor identity without manual lookup

3. Scrapin.io profile enrichment API
   - fetches structured LinkedIn profile data
   - extracts current employer and start date
   - computes tenure in years

Current implementation note:
- The assignment mentions Bright Data as a possible web scraping tool. The checked-in implementation uses GitHub API + Apify + Scrapin.io instead.
- No Anthropic API key is required by the current codebase.

## Internal vs External Logic

Internal contributors are contributors who likely work at the company behind the repository:
- OpenAI for `openai/codex`
- Google for `google-gemini/gemini-cli`

Classification signals include:
- public email domain
- GitHub username patterns
- GitHub `company` field
- GitHub organization membership
- known internal account hints

## Top Contributor Selection

The pipeline selects the top `20` contributors per repository by commit count before enrichment.

Why 20:
- it captures the main contributors driving repository activity
- it keeps LinkedIn enrichment costs manageable
- it provides a reasonable tradeoff between signal quality and API usage

## Project Structure

- `analysis_code/`: main pipeline source code
- `dataset.csv`: final enriched dataset
- `report.md`: submission report
- `cache/`: cached intermediate API results and helper scripts
- `backups/`: backup helper scripts

## Output Dataset

The final dataset includes at least these fields:

- `repo`
- `github_login`
- `github_id`
- `name`
- `contribution_metric`
- `internal_or_external`
- `employer_inferred`
- `employer_confidence`
- `linkedin_url`
- `tenure_current_employer_years`
- `tenure_confidence`

The checked-in dataset also includes:
- `classification_confidence`

## Required API Keys

Copy `.env.example` to `.env` and provide the following values:

```bash
cp .env.example .env
```

Required by the current implementation:
- `GITHUB_TOKEN`
- `APIFY_API_TOKEN`
- `SCRAPIN_API_KEY`

Optional/configurable:
- `APIFY_ACTOR`
- `SCRAPIN_ENDPOINT`

Not required by the current code:
- `ANTHROPIC_API_KEY`
- Bright Data credentials

## How to Run

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Configure environment variables

```bash
cp .env.example .env
```

3. Run the pipeline

```bash
python3 analysis_code/main.py
```

4. Review generated artifacts

- `dataset.csv`
- `report.md`

## Methodology Summary

1. Fetch repository contributors from GitHub.
2. Compute a contribution metric using commit counts and capture merged PR counts for reference.
3. Classify contributors as internal or external using public GitHub signals.
4. Select the top 20 contributors per repository.
5. Resolve LinkedIn profile URLs using Apify search.
6. Enrich profile data using Scrapin.io.
7. Build the final dataset and markdown report.

## Handling Missing or Uncertain Data

The pipeline is designed to avoid manual lookups and handle incomplete data gracefully:

- missing LinkedIn URLs are left empty
- missing employer data falls back to `Unknown` or a low-confidence internal estimate
- tenure uses `0` or `unknown` confidence when a reliable start date is unavailable

## Bonus Extensibility

The current code is partially structured for reuse across repositories, but it is still configured around the two repositories in this assignment. To make it fully generic for arbitrary repositories, the next step would be to parameterize:

- repository inputs
- company-specific internal classification rules
- employer bucket mappings
