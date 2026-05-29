#!/usr/bin/env python3
"""Swap OG/Twitter images on market-update pages to use newsletter covers."""
import json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
MU_DIR = os.path.join(BASE, 'market-updates')

with open(os.path.join(BASE, 'data', 'newsletters.json')) as f:
    newsletters = json.load(f)

# slug → cover URL
cover_map = {}
for n in newsletters:
    if n.get('cover') and n.get('html_url'):
        slug = n['html_url'].replace('/market-updates/', '')
        cover_map[slug] = f"https://www.benleeproperties.com/{n['cover']}"

patched = 0
for fname in sorted(os.listdir(MU_DIR)):
    if not fname.endswith('.html'):
        continue
    slug = fname[:-5]
    cover_url = cover_map.get(slug)
    if not cover_url:
        print(f"  SKIP (no cover): {fname}")
        continue

    fpath = os.path.join(MU_DIR, fname)
    with open(fpath) as f:
        html = f.read()

    # Only replace if still pointing at the generic headshot
    generic = 'https://www.benleeproperties.com/images/BLK-09766.jpg'
    if generic not in html:
        print(f"  SKIP (already updated): {fname}")
        continue

    html = html.replace(generic, cover_url)

    with open(fpath, 'w') as f:
        f.write(html)
    print(f"  PATCHED: {fname}  →  {cover_url}")
    patched += 1

print(f"\nDone. Patched {patched} files.")
