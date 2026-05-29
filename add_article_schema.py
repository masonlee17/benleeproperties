#!/usr/bin/env python3
"""Add NewsArticle schema + fix canonical/OG URLs on all market-updates pages."""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
MU_DIR = os.path.join(BASE, 'market-updates')

MONTH_MAP = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
}

with open(os.path.join(BASE, 'data', 'newsletters.json')) as f:
    newsletters = json.load(f)

cover_map = {}
for n in newsletters:
    if n.get('cover'):
        cover_map[(n['year'], n['month'])] = n['cover']

def make_schema(title, description, url, date_published, cover_url):
    image = f"https://www.benleeproperties.com/{cover_url}" if cover_url else "https://www.benleeproperties.com/images/BLK-09766.jpg"
    return f'''  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": "{title}",
    "description": "{description}",
    "datePublished": "{date_published}",
    "dateModified": "{date_published}",
    "url": "{url}",
    "image": "{image}",
    "author": {{
      "@type": "Person",
      "name": "Ben Lee",
      "url": "https://www.benleeproperties.com/about"
    }},
    "publisher": {{
      "@type": "Organization",
      "name": "Ben Lee Properties",
      "url": "https://www.benleeproperties.com",
      "logo": {{
        "@type": "ImageObject",
        "url": "https://www.benleeproperties.com/images/favicon.png"
      }}
    }},
    "isPartOf": {{
      "@type": "Periodical",
      "name": "Ben Lee Real Estate Newsletter",
      "url": "https://www.benleeproperties.com/blog"
    }}
  }}
  </script>'''

files = sorted(os.listdir(MU_DIR))
patched = 0

for fname in files:
    if not fname.endswith('.html'):
        continue
    slug = fname[:-5]  # e.g. "may-2026"
    parts = slug.rsplit('-', 1)
    if len(parts) != 2:
        print(f"  SKIP (bad slug): {fname}")
        continue
    month_name, year_str = parts
    month_num = MONTH_MAP.get(month_name)
    if not month_num or not year_str.isdigit():
        print(f"  SKIP (parse error): {fname}")
        continue
    year = int(year_str)
    date_published = f"{year}-{month_num:02d}-01"
    correct_url = f"https://www.benleeproperties.com/market-updates/{slug}"
    cover_url = cover_map.get((year, month_num), '')

    fpath = os.path.join(MU_DIR, fname)
    with open(fpath) as f:
        html = f.read()

    # Skip if NewsArticle schema already present
    if '"@type": "NewsArticle"' in html:
        print(f"  SKIP (already has NewsArticle): {fname}")
        continue

    # Fix canonical and OG URL (replace /newsletters/ with /market-updates/)
    html = html.replace(
        f'href="https://www.benleeproperties.com/newsletters/{slug}"',
        f'href="{correct_url}"'
    )
    html = html.replace(
        f'content="https://www.benleeproperties.com/newsletters/{slug}"',
        f'content="{correct_url}"'
    )

    # Extract title and description for schema
    title_match = re.search(r'<title>(.*?)</title>', html)
    desc_match = re.search(r'<meta name="description" content="(.*?)"', html)
    title = title_match.group(1) if title_match else f"{month_name.title()} {year} | Ben Lee Properties"
    description = desc_match.group(1) if desc_match else ""
    # Escape quotes in description
    description = description.replace('"', '\\"').replace("'", "\\'")

    schema = make_schema(title, description, correct_url, date_published, cover_url)

    # Insert schema before </head>
    html = html.replace('</head>', f'{schema}\n</head>', 1)

    with open(fpath, 'w') as f:
        f.write(html)
    print(f"  PATCHED: {fname}")
    patched += 1

print(f"\nDone. Patched {patched} files.")
