# GitHub Contributor Enrichment Pipeline

This project analyzes open-source repositories to estimate how much of their development is driven by internal employees versus external community members. It enriches the top contributors by automatically discovering their LinkedIn profiles, inferring their current employers (such as OpenAI, Google, Anthropic, or xAI), and calculating their employment tenure.

## Objectives Handled
* **Internal vs External Analysis:** Categorizes contributors automatically based on corporate emails, GitHub organizations, and domain names.
* **Identity Enrichment:** Discovers LinkedIn URLs of contributors using intelligent search scraping.
* **Employment Data:** Scrapes profile histories to isolate employers and compute tenure math up to the current date.

## Approach & Methodology
This pipeline chains together 3 distinct tools to solve the problem without manual lookups:
1. **GitHub API (Data Collection):** Extracts contributors, handles pagination, and fetches merged pull request/commit counts to identify the highest-impact developers. It classifies users internally or externally based on GitHub metadata (company tags, emails).
2. **Apify Google Search Actor (Identity Resolution):** Automatically queries Google using the format `"{Name} {Company} site:linkedin.com/in"` to reliably discover accurate LinkedIn URLs for the top contributors.
3. **Scrapin.io API (Profile Extraction):** Pulls structured JSON representations of the target LinkedIn URLs. To respect rate limits, requests are gracefully paced (`sleep`). The tool then applies custom matching to bucket employers strictly according to prompt criteria (`OpenAI`, `Google`, `Anthropic`, `xAI`), dynamically calculating exact years of tenure based on start dates.

## Required API Keys
You will need three free-tier keys to run this pipeline end-to-end. Copy the `.env.example` file to `.env` and fill them in:

1. **`GITHUB_TOKEN`**: A GitHub Personal Access Token (classic or fine-grained) to fetch repo data.
2. **`APIFY_API_TOKEN`**: Register at [Apify](https://apify.com) to use the `apify/google-search-scraper` for resolving URLs.
3. **`SCRAPIN_API_KEY`**: Register at [Scrapin.io](https://scrapin.io) to fetch structured LinkedIn profile JSONs.

## How to Run

1. **Install Dependencies:**
   Ensure you have Python 3.10+ installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   ```bash
   cp .env.example .env
   # Open .env and add your API keys
   ```

3. **Run the Pipeline:**
   Execute the orchestrator script:
   ```bash
   python3 analysis_code/main.py
   ```

4. **View Outputs:**
   The process will generate two files in the root directory:
   * `dataset.csv`: The structured matrix of contributors, metrics, URLs, companies, and tenure.
   * `report.md`: A highly readable markdown breakdown summarizing internal vs external shares and the top 10 individual contributors.
