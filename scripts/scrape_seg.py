#!/usr/bin/env python3
"""
Refresh the LTM market layer from the SEG SaaS Index, then re-join the sticky
judgment layer (data/tags.json) and rebuild data/companies.json.

The market table lives in the page HTML (server-rendered), so requests + a parse
is enough — no headless browser. tags.json is never overwritten; any newly added
SEG constituent is reported so you can tag it.

Run:  python3 scripts/scrape_seg.py
Deps: requests, pandas, lxml   (pip install requests pandas lxml)
"""
import json, os, re, sys, datetime
import requests, pandas as pd

URL = "https://softwareequity.com/saas-index"
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")

def num(x):
    """'$ 4.3B' / '32.7 %' / '0.8 x' / 'N/A' -> float | None"""
    if x is None: return None
    s = str(x).strip().replace("$", "").replace(",", "").replace("%", "").replace("x", "").strip()
    if s in ("", "N/A", "NA", "-", "—"): return None
    mult = 1.0
    if s.endswith("B"): mult, s = 1000.0, s[:-1]      # -> $M
    elif s.endswith("M"): mult, s = 1.0, s[:-1]
    elif s.endswith("K"): mult, s = 0.001, s[:-1]
    try: return round(float(s) * mult, 2)
    except ValueError: return None

def size_bucket(m):
    if m is None: return "n/a"
    if m >= 50000: return "Mega (>$50B)"
    if m >= 10000: return "Large ($10-50B)"
    if m >= 2000:  return "Mid ($2-10B)"
    return "Small (<$2B)"

def growth_bucket(g):
    if g is None: return "n/a"
    if g < 10: return "<10%"
    if g < 20: return "10-20%"
    if g < 30: return "20-30%"
    return "30%+"

def fetch_table():
    r = requests.get(URL, headers={"User-Agent": "saas-tracker/1.0 (private research)"}, timeout=30)
    r.raise_for_status()
    # the constituents table is the one carrying these column headers
    tables = pd.read_html(r.text)
    for t in tables:
        cols = [str(c).lower() for c in t.columns]
        if any("ticker" in c for c in cols) and any("ev/revenue" in c or "ev / revenue" in c for c in cols):
            return t
    raise RuntimeError("Constituents table not found — SEG may have changed the page layout.")

def colpick(df, *needles):
    for c in df.columns:
        cl = str(c).lower()
        if all(n in cl for n in needles): return c
    return None

def main():
    df = fetch_table()
    C = {
        "ticker": colpick(df, "ticker"), "name": colpick(df, "name"),
        "ev_rev": colpick(df, "ev/revenue") or colpick(df, "ev", "revenue"),
        "rev_growth": colpick(df, "revenue growth"), "gross_margin": colpick(df, "gross margin"),
        "ebitda_margin": colpick(df, "ebitda margin"), "nrr": colpick(df, "retention"),
        "ytd": colpick(df, "ytd"), "mcap": colpick(df, "market cap"),
    }
    if not C["ticker"]:
        sys.exit("Could not locate ticker column.")

    tags = json.load(open(os.path.join(DATA, "tags.json")))["tags"]
    out, untagged = [], []
    for _, row in df.iterrows():
        tk = str(row[C["ticker"]]).strip().upper()
        if not tk or tk in ("NAN", "MEDIAN", "AVERAGE"): continue
        g  = num(row[C["rev_growth"]]); eb = num(row[C["ebitda_margin"]]); mc = num(row[C["mcap"]])
        t = tags.get(tk)
        if t is None:
            untagged.append(tk)
            t = {"vh_class": "untagged", "model_purity": "untagged", "review": True}
        rec = {
            "ticker": tk, "name": str(row[C["name"]]).strip(),
            "ev_rev": num(row[C["ev_rev"]]), "rev_growth": g,
            "gross_margin": num(row[C["gross_margin"]]), "ebitda_margin": eb,
            "nrr": num(row[C["nrr"]]) if C["nrr"] else None,
            "ytd_change": num(row[C["ytd"]]) if C["ytd"] else None, "mcap_m": mc,
            "vh_class": t["vh_class"], "model_purity": t["model_purity"], "review": t["review"],
            "size_bucket": size_bucket(mc), "growth_bucket": growth_bucket(g),
            "r40_ebitda": round((g or 0) + (eb or 0), 1),
            "clean_comp": t["model_purity"] == "pure-saas",
        }
        out.append(rec)

    payload = {
        "as_of": datetime.date.today().isoformat(),
        "source": "SEG SaaS Index (softwareequity.com) / Tiingo — TTM basis",
        "basis": "LTM/TTM", "n": len(out),
        "companies": sorted(out, key=lambda x: x["name"].lower()),
    }
    json.dump(payload, open(os.path.join(DATA, "companies.json"), "w"), indent=2)
    print(f"Refreshed {len(out)} companies @ {payload['as_of']}")
    if untagged:
        print(f"  ⚠ {len(untagged)} new constituent(s) need tagging in tags.json: {', '.join(untagged)}")

if __name__ == "__main__":
    main()
