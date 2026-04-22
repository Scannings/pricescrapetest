# Competitor Price Scraper

Self-hosted competitor price monitoring — scrapes live prices daily using sitemap-based URL discovery and fuzzy title matching. Built as an internal alternative to third-party pricing subscription services.

## What it does

1. **Discovery** (`competitor_discovery.py`) — one-off / weekly: probes competitor domains, finds product sitemaps, counts products, writes `competitor_config.json`
2. **Scraping** (`price_scraper.py`) — daily: loads our product catalogue, fetches top N products by revenue, fuzzy-matches each against competitor sitemaps via Jina Reader, outputs Excel price matrix

## How matching works

Each product in our catalogue carries three fields used in the process:

| Field | Source | Role |
|-------|--------|------|
| MPN | Catalogue export | Unique identifier — joins catalogue to competitor match list |
| Title | Catalogue export | Fuzzy-matched (token-based, threshold 72%) against competitor URL slugs — primary matching signal |
| Cost | Catalogue export (WeightedAverageCost) | Validation floor — rejects matches where scraped price is >10% below our unit cost (catches false positives) |

Matching goes directly to competitor sitemaps — no dependency on Google product IDs or third-party catalogues.

## External services

| Service | Purpose | Cost |
|---------|---------|------|
| [Jina Reader](https://r.jina.ai) | Reads public competitor pages, handles Cloudflare | Free |
| thefuzz | Fuzzy title matching | Open source |
| openpyxl | Excel report generation | Open source |

No API keys. No subscriptions. Product data never leaves the local environment.

## Usage

```bash
# Install dependencies
pip install requests openpyxl thefuzz python-Levenshtein pandas

# Scrape top 50 products (default)
python price_scraper.py

# Scrape top N products
python price_scraper.py 100

# Scrape all products
python price_scraper.py 0

# Re-discover all competitors
python competitor_discovery.py --all

# Test a single competitor
python competitor_discovery.py --name "Wickes"
```

## Input files

Update the paths in `price_scraper.py` to point at your local Tableau exports:

| Constant | File | Purpose |
|----------|------|---------|
| `CATALOG_PATH` | Price Vs Cost export (.xlsx) | Catalogue: MPN, title, cost, revenue |
| `MATCHES_PATH` | Competitor Matching export (.xlsx) | MPN → competitor name list |

## Coverage

- 163 competitors with working sitemaps (~47% of match volume)
- ~19% WAF-blocked (B&Q, Screwfix, Amazon) — skipped; can be addressed via ScrapingBee
- ~14% dead sites — out of scope for any service
- ~21% no sitemap — lower priority, smaller players

## Output

Excel report with three sheets:
- **All Results** — every scrape job with status, match score, and price
- **Price Matrix** — MPN × Competitor grid
- **Summary** — match rate per competitor
