#!/usr/bin/env python3
"""Generate sitemap.xml from the live pages. Run after adding pages/listings:
    python3 generate_sitemap.py
Enumerates root pages, city/neighborhood pages, newsletter pages, and property
detail pages (only those with has_detail_page). Uses clean (extensionless) URLs
to match the canonical tags."""
import os, json, glob, datetime

BASE = "https://www.benleeproperties.com"
ROOT = os.path.dirname(os.path.abspath(__file__))
TODAY = datetime.date.today().isoformat()

# (clean path, changefreq, priority) — indexable root pages only
ROOT_PAGES = [
    ("/",                        "weekly",  "1.0"),
    ("/current-listings",        "weekly",  "0.9"),
    ("/for-buyers-3",            "weekly",  "0.9"),
    ("/ben-lee-sold-properties", "weekly",  "0.9"),
    ("/deals",                   "weekly",  "0.9"),
    ("/neighborhoods",           "monthly", "0.9"),
    ("/for-sellers",             "monthly", "0.8"),
    ("/valuation",               "monthly", "0.8"),
    ("/about",                   "monthly", "0.8"),
    ("/contact",                 "monthly", "0.8"),
    ("/testimonials",            "monthly", "0.6"),
    ("/social-media",            "monthly", "0.5"),
    ("/blog",                    "weekly",  "0.6"),
    ("/summer-2026-photo-contest", "monthly", "0.5"),
    ("/amenities",               "monthly", "0.5"),
    ("/realtors",                "monthly", "0.5"),
    ("/states",                  "monthly", "0.5"),
]

def city_slugs():
    return sorted(os.path.basename(f)[:-5] for f in glob.glob(os.path.join(ROOT, "cities", "*.html")))

def newsletter_slugs():
    return sorted(os.path.basename(f)[:-5] for f in glob.glob(os.path.join(ROOT, "market-updates", "*.html")))

def property_ids():
    for base in (os.environ.get("DATA_DIR", os.path.join(ROOT, "data")), os.path.join(ROOT, "data")):
        p = os.path.join(base, "properties.json")
        if os.path.isfile(p):
            try:
                return [x["id"] for x in json.load(open(p)) if x.get("has_detail_page") and x.get("id")]
            except Exception:
                pass
    return []

def url(loc, freq, pri):
    return (f"  <url>\n    <loc>{BASE}{loc}</loc>\n    <lastmod>{TODAY}</lastmod>\n"
            f"    <changefreq>{freq}</changefreq>\n    <priority>{pri}</priority>\n  </url>")

def build():
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', ""]
    out.append("  <!-- Core pages -->")
    for loc, freq, pri in ROOT_PAGES:
        out.append(url(loc, freq, pri))
    out.append("\n  <!-- Neighborhood / city pages -->")
    for s in city_slugs():
        out.append(url(f"/cities/{s}", "monthly", "0.8"))
    out.append("\n  <!-- Property detail pages -->")
    for pid in property_ids():
        out.append(url(f"/property/{pid}", "monthly", "0.7"))
    out.append("\n  <!-- Newsletters -->")
    for s in newsletter_slugs():
        out.append(url(f"/market-updates/{s}", "monthly", "0.5"))
    out.append("\n</urlset>\n")
    return "\n".join(out)

if __name__ == "__main__":
    xml = build()
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"Wrote sitemap.xml — {xml.count('<loc>')} URLs (lastmod {TODAY})")
