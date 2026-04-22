"""
Competitor Auto-Discovery Pipeline

For every competitor in the PriceAPI matches file:
  1. Guess domain from name (heuristic + known overrides)
  2. Fetch robots.txt -> find sitemap URL
  3. Probe common sitemap paths if not in robots.txt
  4. Count indexed product URLs
  5. Write results to competitor_config.json

Run this periodically (weekly) to pick up new competitors.
The main scraper loads competitor_config.json at runtime.

Usage:
  python competitor_discovery.py              # process all unknown/untested
  python competitor_discovery.py --all        # re-test everything
  python competitor_discovery.py --name "Wickes"  # test single competitor
"""

import argparse
import json
import os
import re
import time
from collections import Counter
from datetime import datetime

import openpyxl
import requests

MATCHES_PATH   = r"C:\Users\Simon\Downloads\Competitor Matching_Full Data_data (9).xlsx"
CONFIG_PATH    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "competitor_config.json")
REQUEST_DELAY  = 0.4   # seconds between requests
TIMEOUT        = 8

# ── Known domain overrides ────────────────────────────────────────────────────
# Competitor name exactly as in PriceAPI -> domain
KNOWN_DOMAINS = {
    "Trading Depot":                    "www.tradingdepot.co.uk",
    "HeatandPlumb.com":                 "www.heatandplumb.com",
    "BHL.co.uk":                        "www.bhl.co.uk",
    "City Plumbing":                    "www.cityplumbing.co.uk",
    "Plumb2u":                          "www.plumb2u.com",
    "Taps UK":                          "www.tapsuk.com",
    "mrcentralheating.co.uk dy":        "www.mrcentralheating.co.uk",
    "Mr Central Heating":               "www.mrcentralheating.co.uk",
    "Discount Heating":                 "www.discountheating.co.uk",
    "Croxley Plumbing Supplies":        "www.croxleyplumbing.co.uk",
    "Toolstation":                      "www.toolstation.com",
    "Victorian Plumbing":               "www.victorianplumbing.co.uk",
    "Radiators.co.uk":                  "www.radiators.co.uk",
    "QS Bathroom Supplies":             "www.qssupplies.co.uk",
    "MBD Bathrooms":                    "www.mbdbathrooms.co.uk",
    "Stelrad":                          "www.stelrad.com",
    "Electrical Deals Direct":          "www.electricaldealsdirect.co.uk",
    "PlumbArena.co.uk":                 "www.plumbarena.co.uk",
    "Unbeatable Bathrooms":             "www.unbeatbathrooms.co.uk",
    "Robert Dyas":                      "www.robertdyas.co.uk",
    "Taps Empire":                      "www.tapsempire.co.uk",
    "B&Q":                              "www.diy.com",
    "TradePoint":                       "www.diy.com",
    "Screwfix.com":                     "www.screwfix.com",
    "Amazon.co.uk":                     "www.amazon.co.uk",
    "Amazon.co.uk - Amazon.co.uk-Seller": "www.amazon.co.uk",
    "Plumb Centre":                     "www.plumbcentre.co.uk",
    "golita.co.uk":                     "www.golita.co.uk",
    "showerstoyou.co.uk":               "www.showerstoyou.co.uk",
    "Bathrooms and Showers Direct":     "www.bathroomsandshowersdirect.co.uk",
    "Bathroom Planet":                  "www.bathroomplanet.co.uk",
    "Envy Bathrooms UK":                "www.envybathrooms.co.uk",
    "Ergonomic Designs Bathrooms":      "www.ergonomicdesigns.co.uk",
    "MP Moran & Sons":                  "www.mpmoran.co.uk",
    "JT Atkinson Builders Merchant":    "www.jtatkinson.co.uk",
    "Macdonald Plumbing Supplies":      "www.macdonaldps.co.uk",
    "TDL Online":                       "www.tdlonline.co.uk",
    "HVAC Sanitary":                    "www.hvacsanitary.co.uk",
    "Plumbing Superstore":              "www.plumbing-superstore.co.uk",
    "Bathroom Supplies Online":         "www.bathroomsuppliesonline.co.uk",
    "Wickes":                           "www.wickes.co.uk",
    "Wayfair.co.uk":                    "www.wayfair.co.uk",
    "Vaillant":                         "www.vaillant.co.uk",
    "Worcester Bosch":                  "www.worcester-bosch.co.uk",
    "Ideal Heating":                    "www.idealheating.com",
    "Plumbsave":                        "www.plumbsave.co.uk",
    "British Bathroom Company":         "www.britishbathroomcompany.co.uk",
    "Pump Sales Direct":                "www.pumpsalesdirect.co.uk",
    "Plumb-Warehouse.co.uk":            "www.plumb-warehouse.co.uk",
    "AQVA Bathrooms":                   "www.aqva.co.uk",
    "Wholesale Domestic":               "www.wholesaledomestic.com",
    "SuperBath.co.uk":                  "www.superbath.co.uk",
    "Anchor Pumps":                     "www.anchorpumps.com",
    "Heater Shop":                      "www.heatershop.co.uk",
    "Eco Wizard":                       "www.ecowizard.co.uk",
    "BES":                              "www.bes.co.uk",
    "Builder Depot":                    "www.builderdepot.co.uk",
    "Electrical2go":                    "www.electrical2go.co.uk",
    "Superlec Direct":                  "www.superlecdirect.co.uk",
    "JT Dove":                          "www.jtdove.co.uk",
    "Bathroom & Tile Centre":           "www.bathroomandtilecentre.co.uk",
    "The Shower Doctor":                "www.theshowerdoctor.co.uk",
    "Plumbing World":                   "www.plumbingworld.co.uk",
    "VPS Hot Water Cylinders":          "www.vpshotwater.co.uk",
    "Warmflow":                         "www.warmflow.co.uk",
    "Innovate Electrical":              "www.innovateelectrical.co.uk",
    "Inspired Heating":                 "www.inspiredheating.co.uk",
    "Gledhill":                         "www.gledhillwater.com",
    "Fuel Tank Shop":                   "www.fueltankshop.co.uk",
    "Mastertrade":                      "www.mastertrade.co.uk",
    # Newly resolved domains
    "Puffin Bathrooms":                 "www.puffinbathrooms.co.uk",
    "Empire Electro":                   "www.empireelectro.co.uk",
    "The Panel Company":                "www.panelcompany.co.uk",
    "Advanced Water Company":           "www.advancedwater.co.uk",
    "TLC Electrical":                   "www.tlc-direct.co.uk",
    "Tap Warehouse":                    "www.tapwarehouse.com",
    "Grant":                            "www.grantuk.com",
    "Heatrae Sadia":                    "www.heatraesadia.com",
    "Luxury Plumbing":                  "www.luxuryplumbing.co.uk",
    "Build & Plumb":                    "www.buildandplumb.co.uk",
    "Paton Of Walton":                  "www.patonofwalton.co.uk",
    "Long Eaton Appliance Company":     "www.longeatonappliances.co.uk",
    "Beacon Electrical":                "www.beaconelectrical.co.uk",
    "Appliance Shop":                   "www.theapplianceshop.co.uk",
    "HomeSupply":                       "www.homesupplies.co.uk",
    "Complete Pump Supplies":           "www.completepumpsupplies.co.uk",
    "CNM Online":                       "www.cnmonline.co.uk",
    # Big retailers — domain override (heuristic was guessing wrong)
    "Currys":                           "www.currys.co.uk",
    "Currys Business":                  "www.currys.co.uk",
    "John Lewis & Partners":            "www.johnlewis.com",
    "Travis Perkins":                   "www.travisperkins.co.uk",
    "ManoMano.co.uk":                   "www.manomano.co.uk",
    "AO.com":                           "www.ao.com",
    "Wilko":                            "www.wilko.com",
    "Dunelm":                           "www.dunelm.com",
    "Triton Showers":                   "www.tritonshowers.co.uk",
    "CEF":                              "www.cef.co.uk",
    "Tesco":                            "www.tesco.com",
    "Stelrad Radiators":                "www.stelrad.com",
    "OnBuy.com":                        "www.onbuy.com",
    "NWT Direct":                       "www.nwt.co.uk",
    "snh.co.uk":                        "www.snhtradecentre.co.uk",
    "Columnrads.co.uk":                 "www.mrcentralheating.co.uk",
    "Worcester-Bosch":                  "www.worcester-bosch.co.uk",
    "Glow-Worm":                        "www.glow-worm.co.uk",
    "Glow-worm":                        "www.glow-worm.co.uk",
    "GlowWorm":                         "www.glow-worm.co.uk",
    "Glowworm":                         "www.glow-worm.co.uk",
    "Underfloor Heating Direct":        "www.brandwise.co.uk",
    "Underfloor Heating UK":            "www.brandwise.co.uk",
    "Paul Davies Appliances":           "www.pauldavieskitchensandappliances.co.uk",
    "WarmFlow":                         "www.warmflow.co.uk",
    "MonsterPlumb":                     "www.monsterplumbing.co.uk",
    "IronmongeryDirect":                "www.ironmongerydirect.co.uk",
    "Bathroom House":                   "www.bathroom-house.co.uk",
    "Drench":                           "www.drench.co.uk",
    "yesss.co.uk":                      "www.yesss.co.uk",
    "WestsideBathrooms":                "www.westsidebathrooms.co.uk",
    "Tradeplumbing.co.uk":              "www.tradeplumbing.co.uk",
}

# Competitors to skip entirely (WAF-blocked, dead, or impractical)
SKIP = {
    "B&Q", "TradePoint", "Screwfix.com", "Amazon.co.uk",
    "Amazon.co.uk - Amazon.co.uk-Seller", "Plumb Centre",
    "Taps Empire",   # blocks all scraping
}

# Common sitemap paths to probe (in order)
SITEMAP_PROBES = [
    "/sitemap.xml",
    "/sitemap_index.xml",
    "/sitemap/sitemap.xml",
    "/sitemap/google-sitemap-products.xml",
    "/wp-sitemap.xml",
    "/sitemap_products.xml",
    "/sitemap-products.xml",
    "/feed",
]


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _get(url: str, timeout: int = TIMEOUT) -> requests.Response | None:
    try:
        return requests.get(url, headers={"User-Agent": "Mozilla/5.0"},
                            timeout=timeout, allow_redirects=True)
    except Exception:
        return None


# ── Domain discovery ──────────────────────────────────────────────────────────

def _name_to_domain_candidates(name: str) -> list[str]:
    """Generate likely domain candidates from a competitor name."""
    # Already looks like a domain
    if re.search(r"\.(co\.uk|com|net|org)$", name, re.IGNORECASE):
        clean = name.lower().strip()
        return [f"www.{clean}" if not clean.startswith("www.") else clean]

    # Clean the name
    slug = name.lower()
    slug = re.sub(r"\s*(ltd|limited|uk|plc|group|direct|online|store|shop|supplies|co)\s*$", "", slug)
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = slug.strip().replace(" ", "-").replace("--", "-")

    return [
        f"www.{slug}.co.uk",
        f"www.{slug}.com",
        f"www.{slug}-online.co.uk",
        f"www.{slug}online.co.uk",
    ]


def discover_domain(name: str) -> str | None:
    """Return the live domain for a competitor, or None if not found."""
    if name in KNOWN_DOMAINS:
        return KNOWN_DOMAINS[name]

    for candidate in _name_to_domain_candidates(name):
        r = _get(f"https://{candidate}/", timeout=6)
        if r and r.status_code < 400:
            # Use the final domain after any redirects
            final = re.sub(r"https?://", "", r.url).split("/")[0]
            return final
        time.sleep(0.2)
    return None


# ── Sitemap discovery ─────────────────────────────────────────────────────────

def discover_sitemap(domain: str) -> str | None:
    """Find sitemap URL from robots.txt or common paths. Returns URL or None."""
    # Try robots.txt first
    r = _get(f"https://{domain}/robots.txt")
    if r and r.status_code == 200:
        sitemaps = re.findall(r"(?i)sitemap:\s*(\S+)", r.text)
        if sitemaps:
            return sitemaps[0].strip()

    # Probe common paths
    for path in SITEMAP_PROBES:
        r = _get(f"https://{domain}{path}", timeout=6)
        if r and r.status_code == 200 and "<loc>" in r.text:
            return f"https://{domain}{path}"
        time.sleep(0.1)

    return None


def _count_product_urls(sitemap_url: str, domain: str, max_depth: int = 2) -> tuple[int, str]:
    """
    Count product URLs in a sitemap (recursively for indexes).
    Returns (count, canonical_sitemap_url_to_store).
    Always returns the root index URL so the scraper can load all sub-sitemaps.
    """
    r = _get(sitemap_url, timeout=12)
    if not r or r.status_code != 200 or "<loc>" not in r.text:
        return 0, sitemap_url

    # Check if it's an index
    sub_sitemaps = re.findall(r"<sitemap>\s*<loc>([^<]+)</loc>", r.text)
    if sub_sitemaps and max_depth > 0:
        # Find product-specific sub-sitemaps to count (for scoring only)
        product_subs = [s for s in sub_sitemaps if any(
            x in s.lower() for x in ["product", "catalog", "acatalog", "sitemap-1-"]
        )]
        targets = product_subs if product_subs else sub_sitemaps

        total_count = 0
        for sub in targets[:10]:
            count, _ = _count_product_urls(sub.strip(), domain, max_depth - 1)
            total_count += count
            time.sleep(0.2)
        # Always return the INDEX URL so the scraper loads everything
        return total_count, sitemap_url

    # Regular sitemap — count domain URLs only
    all_locs = re.findall(r"<loc>([^<]+)</loc>", r.text)
    product_locs = [u for u in all_locs if domain.replace("www.", "") in u
                    and not any(x in u.lower() for x in ["/blog/", "/news/", "/page/", "/category/", "/tag/"])]
    return len(product_locs), sitemap_url


# ── Config persistence ────────────────────────────────────────────────────────

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(config: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# ── Main discovery loop ───────────────────────────────────────────────────────

def get_all_competitors() -> Counter:
    wb = openpyxl.load_workbook(MATCHES_PATH)
    ws = wb.active
    comps = Counter()
    for row in ws.iter_rows(values_only=True, min_row=2):
        if row[1]:
            comps[str(row[1])] += 1
    return comps


def process_competitor(name: str, config: dict, force: bool = False) -> dict:
    """
    Discover and test a single competitor. Returns updated config entry.
    Skips if already tested and force=False.
    """
    existing = config.get(name, {})

    if not force and existing.get("status") in ("ok", "no_sitemap", "blocked", "dead"):
        return existing

    if name in SKIP:
        return {"status": "skipped", "reason": "WAF/blocked/impractical", "last_checked": str(datetime.now().date())}

    print(f"  Testing: {name}")

    # 1. Domain
    domain = discover_domain(name)
    if not domain:
        print(f"    -> domain not found")
        return {"status": "domain_not_found", "last_checked": str(datetime.now().date())}

    # 2. Accessibility check
    r = _get(f"https://{domain}/", timeout=6)
    if not r or r.status_code >= 400:
        print(f"    -> {domain} not accessible ({r.status_code if r else 'timeout'})")
        return {"domain": domain, "status": "dead", "last_checked": str(datetime.now().date())}

    time.sleep(REQUEST_DELAY)

    # 3. Sitemap
    sitemap_url = discover_sitemap(domain)
    if not sitemap_url:
        print(f"    -> {domain}: no sitemap found")
        return {"domain": domain, "sitemap": None, "product_count": 0,
                "status": "no_sitemap", "last_checked": str(datetime.now().date())}

    time.sleep(REQUEST_DELAY)

    # 4. Product count
    count, best_sitemap = _count_product_urls(sitemap_url, domain)
    print(f"    -> {domain} | sitemap: {best_sitemap} | {count:,} products")

    status = "ok" if count >= 10 else "no_sitemap" if count == 0 else "low_count"
    return {
        "domain": domain,
        "sitemap": best_sitemap,
        "product_count": count,
        "status": status,
        "last_checked": str(datetime.now().date()),
    }


def run_discovery(names: list[str], force: bool = False):
    config = load_config()
    all_comps = get_all_competitors()

    # Filter to requested names, sorted by match count descending
    to_process = sorted(
        [n for n in names if n in all_comps],
        key=lambda x: -all_comps[x]
    )

    print(f"\nAuto-Discovery Pipeline — {len(to_process)} competitors to process\n")

    ok = skipped = errors = 0
    for i, name in enumerate(to_process, 1):
        match_count = all_comps.get(name, 0)
        print(f"[{i}/{len(to_process)}] {name} ({match_count:,} matches)")
        try:
            result = process_competitor(name, config, force=force)
            config[name] = result
            status = result.get("status", "?")
            if status == "ok":
                ok += 1
            elif status == "skipped":
                skipped += 1
            else:
                errors += 1
        except Exception as e:
            print(f"    ERROR: {e}")
            config[name] = {"status": "error", "error": str(e),
                            "last_checked": str(datetime.now().date())}
            errors += 1

        save_config(config)
        time.sleep(REQUEST_DELAY)

    print(f"\nDone: {ok} ok | {skipped} skipped | {errors} no sitemap/blocked")
    print(f"Config saved to: {CONFIG_PATH}")
    _print_summary(config, all_comps)


def _print_summary(config: dict, all_comps: Counter):
    by_status = {}
    for name, entry in config.items():
        s = entry.get("status", "unknown")
        by_status.setdefault(s, []).append((name, all_comps.get(name, 0)))

    print("\n=== Coverage Summary ===")
    total_matches = sum(all_comps.values())
    for status in ["ok", "skipped", "no_sitemap", "dead", "domain_not_found", "error", "low_count"]:
        entries = by_status.get(status, [])
        if not entries:
            continue
        matches = sum(n for _, n in entries)
        pct = matches / total_matches * 100
        print(f"  {status:20s}: {len(entries):3d} competitors | {matches:6,} matches ({pct:.1f}%)")

    covered = sum(n for _, n in by_status.get("ok", []))
    print(f"\n  TOTAL COVERABLE   : {covered:6,} matches ({covered/total_matches*100:.1f}%)")
    print(f"  TOTAL MATCHES     : {total_matches:6,}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--all",  action="store_true", help="Re-test all competitors")
    parser.add_argument("--name", type=str,            help="Test a single competitor by name")
    parser.add_argument("--top",  type=int, default=0, help="Only process top N by match count")
    args = parser.parse_args()

    all_comps = get_all_competitors()

    if args.name:
        names = [args.name]
    else:
        names = list(all_comps.keys())
        if args.top:
            names = [n for n, _ in all_comps.most_common(args.top)]

    run_discovery(names, force=args.all)
