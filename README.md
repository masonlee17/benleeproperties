# Ben Lee Properties — Developer Reference

**Live site:** https://benleeproperties.onrender.com  
**Canonical domain:** https://www.benleeproperties.com  
**Admin panel:** `/admin` (password in `ADMIN_PASSWORD` env var, default `benlee2024`)  
**Stack:** Python 3.11 / Flask / Gunicorn / Docker / Render  
**Owner:** Lilli Lee, CMO — mason@benleeproperties.com

---

## Critical house rules

- **Never use em dashes** (`—`) in any copy, HTML, or generated content. Use commas, colons, or rewrite.
- Brand red for highlights: `#ed2227`. Orange accent (`#be591f`, CSS var `--chocolate`) is for admin UI only.
- Footer tagline must read **"Real Estate"** not "Commercial Real Estate".
- Nav labels are **"For Buyers"** and **"For Sellers"** (capitalized).

---

## Directory structure

```
admin.py                     Main Flask app — serves all routes, admin panel HTML
generate_city_pages.py       Generates cities/*.html from NEIGHBORHOODS data array
update_meta.py               One-shot script: injects SEO meta into root-level HTML pages
add_article_schema.py        One-shot script: adds NewsArticle schema to market-updates pages

neighborhoods.html           Neighborhoods index page (URL: /neighborhoods)
valuation.html               Valuation page (URL: /valuation)
index.html                   Homepage
for-buyers-3.html            Live listings page
cities/                      7 generated neighborhood pages (cheviot-hills, beverlywood, etc.)
market-updates/              34 newsletter HTML wrapper pages (april-2023.html ... may-2026.html)

data/
  properties.json            All property listings (source of truth for admin edits)
  newsletters.json           Newsletter metadata (year, month, pdf path, cover path, html_url)
  images/                    Uploaded property images (volume-aware)
  documents/                 Uploaded newsletter PDFs (volume-aware)

images/                      Repo-bundled static images (icons, logos, hero images)
documents/                   Repo-bundled PDFs (newsletters that existed before volume setup)
css/                         Webflow CSS (do not edit)
```

---

## Flask routes

| URL pattern | Behavior |
|---|---|
| `/` `/index.html` | Homepage — dynamic: injects `live_listings+homepage` properties |
| `/neighborhoods` `/neighborhoods.html` | Neighborhoods index page (static serve) |
| `/cities` `/cities.html` | 301 redirect to `/neighborhoods` |
| `/cities/<slug>` | City page — dynamic: injects active listings for that neighborhood |
| `/for-buyers-3` | Live listings — dynamic: injects all `live_listings` properties |
| `/current-listings` | Built by Ben page — dynamic |
| `/blog` | Newsletter index — dynamic |
| `/market-updates/<slug>` | Newsletter page — static serve from `market-updates/<slug>.html` |
| `/valuation` | Valuation page — static serve |
| `/property/<id>` | Property detail page — dynamic, built from properties.json |
| `/admin` | Admin panel (login required) |
| `/api/properties` | GET/POST properties |
| `/api/properties/<pid>` | PUT/DELETE a property |
| `/api/listings` | Alias for live_listings subset (GET/POST/PUT/DELETE) |
| `/api/newsletters` | GET/POST newsletters |
| `/api/newsletters/<nid>` | DELETE a newsletter |
| `/api/upload/image` | POST multipart image upload |
| `/images/<path>` | Serve images — checks volume first, falls back to repo copy |
| `/documents/<path>` | Serve PDFs — checks volume first, falls back to repo copy |
| `/<path>` | Catch-all static file serve from BASE_DIR |

---

## Data persistence and volumes

**Without a volume (current state):** `DATA_DIR` defaults to `./data` inside the container. All data is ephemeral — lost on redeploy. Works fine for staging/testing.

**When volumes are ready:**
1. Create a Render disk, mount at `/data`
2. Set env var `DATA_DIR=/data`
3. On first boot, `seed_volume_if_needed()` detects the volume is empty and copies `data/properties.json` from the repo image into the volume. After that the volume is authoritative.

**File paths for uploaded images:** stored as `images/filename.jpg` (no leading slash). Served at `/images/filename.jpg`. Always prefix with `/` when writing src attributes in HTML.

**Atomic writes:** `save()` writes to a `.tmp` file then `os.replace()` so an interrupted write never leaves a zero-byte JSON file (which would crash gunicorn on startup).

---

## Property data model

```json
{
  "id": "prop-1",
  "order": 1,
  "address": "123 Main St",
  "city": "Los Angeles",
  "state": "CA",
  "price": "1,500,000",
  "rent": "8,000",
  "beds": "4",
  "baths": "3",
  "sqft": "2,400",
  "status": "FOR SALE",
  "image1": "images/photo1.jpg",
  "image2": "images/photo2.jpg",
  "has_detail_page": true,
  "description": "Full listing description...",
  "sections": ["live_listings", "homepage"],
  "neighborhoods": ["cheviot-hills", "beverlywood"]
}
```

**`sections` values:**
- `live_listings` — appears on the For Buyers page
- `homepage` — appears on the homepage featured grid
- `built_by_ben` — appears on the Built by Ben page

**`neighborhoods` array:** slugs of city pages where this listing should appear. A property must have BOTH `live_listings` in sections AND the matching slug in neighborhoods to show on a city page. Supports multiple neighborhoods per listing.

**Valid neighborhood slugs:** `cheviot-hills`, `beverlywood`, `beverly-hills`, `westwood`, `bel-air`, `brentwood`, `santa-monica`

---

## Newsletter system

### Data model (`data/newsletters.json`)

```json
{
  "id": "nl-2026-05",
  "label": "May 2026",
  "year": 2026,
  "month": 5,
  "pdf": "documents/Ben-Lee-050126-BEVERLYWOOD_8.5x11-digital.pdf",
  "cover": "images/nl-covers/nl-2026-05.jpg",
  "html_url": "/market-updates/may-2026"
}
```

### Adding a new newsletter (admin flow)

1. Go to `/admin` → Newsletters tab
2. Select year and month, upload the PDF
3. Admin saves the PDF to `DATA_DIR/documents/`, extracts the cover image using PyMuPDF (saved to `DATA_DIR/images/nl-covers/nl-YYYY-MM.jpg`), and saves the entry to `newsletters.json`
4. **The HTML wrapper page in `market-updates/` is NOT auto-generated by the admin.** It must be created manually or by script (see below).

### Generating the HTML wrapper page

Each newsletter needs a `market-updates/<month>-<year>.html` file that:
- Has full SEO meta (title, description, canonical, OG, Twitter, NewsArticle schema)
- Has geo tags (see SEO section below)
- Embeds the PDF in an `<iframe>`
- Has an `<article class="nl-text-body">` with clean extracted text for indexing

To regenerate text for existing pages or create new ones, use PyMuPDF:

```python
import fitz
doc = fitz.open('documents/my-newsletter.pdf')
for page in doc:
    print(page.get_text('text'))
```

The `nl-text-body` article pattern used in all existing pages:
```html
<article class="nl-text-body" aria-label="Newsletter text content">
  <h2>Ben Lee Properties — May 2026 Newsletter</h2>
  <p class="nl-text-meta">Issue: May 2026 &nbsp;|&nbsp; Cheviot Hills &amp; Beverlywood, Los Angeles</p>
  <p>Extracted paragraph one...</p>
  <p>Extracted paragraph two...</p>
  ...
</article>
```

**PDF text extraction tips:**
- Use `page.get_text('text')` — the `blocks` and `words` modes produce raw coordinate data
- Drop caps: PDFs often encode a large decorative first letter as a separate text run. Detect with `re.match(r'^[A-Z]$', line)` and merge with the next line
- Filter boilerplate: CalRE numbers, Coldwell Banker disclaimers, fair housing text, license numbers
- The newsletter cover page (page 1) is mostly header/title text — include it but expect it to be short

---

## City / neighborhood pages

### How they work

1. Static HTML files in `cities/` are generated by `generate_city_pages.py`
2. Each page has a `<!-- CITY_LISTINGS_PLACEHOLDER -->` comment between the Ben callout and FAQ sections
3. At request time, `/cities/<slug>` reads the HTML, filters `properties.json` for listings matching that slug, builds card HTML via `build_city_listing_items()`, and replaces the placeholder

### Adding or editing a city page

1. Edit `NEIGHBORHOODS` list in `generate_city_pages.py` — add or modify the dict for the city
2. Run: `python3 generate_city_pages.py`
3. If adding a new city, also:
   - Add the slug to `CITY_SLUGS` in `admin.py`
   - Add a checkbox to the "City Pages" group in the admin modal HTML
   - Add a card to `neighborhoods.html`

### City data fields

```python
{
    "slug": "westwood",           # URL path: /cities/westwood
    "name": "Westwood",           # Display name
    "tagline": "...",             # Hero subheading
    "zip": "90024",
    "geo_lat": 34.0619,
    "geo_lon": -118.4426,
    "hero_img": "https://...",    # Pexels or similar full URL
    "hero_img_alt": "...",
    "meta_desc": "...",           # 140-160 chars, includes neighborhood + real estate + Ben Lee
    "og_desc": "...",             # OG/Twitter description
    "median_price": "$1,650,000",
    "price_trend": "Up 5% YoY",
    "avg_dom": "32 days",
    "price_note": "...",          # Shown in stats bar
    "about": "HTML string...",    # Can include <br><br> for paragraph breaks
    "schools": [("Name", "Desc"), ...],
    "features": ["bullet 1", ...],
    "ben_note": "...",            # Ben's personal note in the callout section
    "faqs": [("Question?", "Answer."), ...]
}
```

---

## Dynamic page injection pattern

Pages that need live data use one of two patterns:

**Pattern A — admin-marker replacement** (homepage, for-buyers, built-by-ben):
```html
<!-- ADMIN:MARKER_NAME:START -->
  ...static fallback content...
<!-- ADMIN:MARKER_NAME:END -->
```
Flask calls `render_dynamic(filename, 'MARKER_NAME', new_html)` which regex-replaces the block at request time.

**Pattern B — placeholder comment** (city pages):
```html
<!-- CITY_LISTINGS_PLACEHOLDER -->
```
Flask calls `html.replace('<!-- CITY_LISTINGS_PLACEHOLDER -->', build_city_listing_items(listings))`.

---

## SEO and GEO — what has been done

### Root-level pages
`update_meta.py` injects optimized meta blocks into all root-level pages. Run it again after adding new root pages or updating titles/descriptions.

### City / neighborhood pages
All 7 city pages and `neighborhoods.html` have:
- Unique title tags (under 60 chars)
- Meta descriptions (140-165 chars, include neighborhood + "real estate" + "Ben Lee Properties")
- Canonical URLs (`https://www.benleeproperties.com/cities/<slug>`)
- Full OG set (title, description, URL, image with dimensions)
- Twitter card
- `robots: index, follow`
- **Geo meta tags** (added May 2026):
  ```html
  <meta name="geo.region" content="US-CA">
  <meta name="geo.placename" content="Cheviot Hills, Los Angeles, CA">
  <meta name="geo.position" content="34.0333;-118.4167">
  <meta name="ICBM" content="34.0333, -118.4167">
  ```
- **Schema markup** — each city page has three `@type` blocks:
  - `Place` with PostalAddress and GeoCoordinates
  - `FAQPage` with Question/Answer pairs from the faqs array
  - `RealEstateAgent` linking Ben Lee to the neighborhood
- `neighborhoods.html` has an `ItemList` schema listing all 7 neighborhoods as `Place` items

### Newsletter pages
All 34 `market-updates/*.html` pages have (as of May 2026):
- Title: `"Month YYYY | Ben Lee Properties — LA Real Estate Newsletter"`
- Meta description: sourced from beginning of newsletter text
- Canonical URL: `https://www.benleeproperties.com/market-updates/month-yyyy`
- Full OG set with newsletter cover image
- Twitter card
- `NewsArticle` schema (added by `add_article_schema.py`) with datePublished, author, publisher, isPartOf (Periodical)
- **Geo meta tags** (added May 2026): all pointing to `Cheviot Hills & Beverlywood, Los Angeles, CA`, coordinates `34.0400, -118.4080`
- **`<article class="nl-text-body">`** — clean readable text extracted from each PDF using PyMuPDF (30-55 paragraphs per issue). This is the indexable text content Google sees. Previously this was garbled fragments; it was re-extracted in May 2026 using `page.get_text('text')` with boilerplate filtering and drop-cap merging.

### When adding a new newsletter HTML page
Make sure it includes all of the above. Copy an existing page (e.g. `may-2026.html`) as the template and update:
1. All title/meta/OG/Twitter tags with the new month/year
2. The canonical URL and schema `url`/`datePublished`
3. The iframe `src` pointing to the new PDF
4. The `nl-text-body` article with freshly extracted text
5. The `geo.placename` stays the same for all newsletters (Cheviot Hills & Beverlywood)

---

## Deployment

**Platform:** Render.com  
**Service name:** benleeproperties  
**Runtime:** Docker (`render.yaml` → `runtime: docker`)  
**Health check:** `GET /`  

**Dockerfile summary:**
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn", "admin:app", "--config", "gunicorn.conf.py"]
```

**requirements.txt:**
```
flask>=3.0
werkzeug>=3.0
gunicorn>=21.0
PyMuPDF>=1.24
```

**Env vars:**
| Var | Default | Notes |
|---|---|---|
| `ADMIN_PASSWORD` | `benlee2024` | Change in production |
| `SECRET_KEY` | `bl-dev-secret-change-in-prod` | Auto-generated by Render if set to `generateValue` |
| `DATA_DIR` | `./data` | Set to `/data` when volume is mounted |
| `PORT` | `8080` | Set automatically by Render |

**Gunicorn config** (`gunicorn.conf.py`): 2 workers, 120s timeout, binds to `0.0.0.0:$PORT`.

---

## One-shot maintenance scripts

These are run locally, not by the server:

| Script | Purpose | When to run |
|---|---|---|
| `python3 generate_city_pages.py` | Regenerates all 7 `cities/*.html` | After any edit to `generate_city_pages.py` NEIGHBORHOODS data |
| `python3 update_meta.py` | Re-injects SEO meta into root-level HTML | After adding new root pages or changing titles |
| `python3 add_article_schema.py` | Adds/updates NewsArticle schema on newsletter pages | After adding new newsletter pages |

---

## Common tasks

### Add a new property listing
1. Go to `/admin` → Properties → Add Property
2. Fill in address, price/rent, beds/baths/sqft, status, upload images
3. Check sections: **Live Listings** (For Buyers page), **Homepage** (featured on homepage), **Built by Ben** (custom builds page)
4. Check **City Pages** boxes for any neighborhoods where this listing should appear (requires Live Listings to also be checked)
5. Check **Enable Detail Page** if a full detail page should exist at `/property/<id>`

### Add a new neighborhood city page
1. Add a new dict to `NEIGHBORHOODS` in `generate_city_pages.py` following the existing pattern
2. Run `python3 generate_city_pages.py`
3. Add the new slug to `CITY_SLUGS` in `admin.py`
4. Add a new checkbox `<input type="checkbox" id="p-nbhd-<slug>">` to the City Pages group in the admin modal HTML in `admin.py`
5. Add a card `<div role="listitem">` to the grid in `neighborhoods.html`
6. Update the `ItemList` schema in `neighborhoods.html` with the new Place entry

### Add a new newsletter
1. `/admin` → Newsletters tab → select month/year → upload PDF → Save
2. This creates the entry in `newsletters.json` and extracts the cover image
3. Manually create `market-updates/<month>-<year>.html` (copy an existing file, update all metadata and iframe src)
4. Extract clean text from the PDF using PyMuPDF and populate the `nl-text-body` article
5. Set `html_url` in `newsletters.json` to `/market-updates/<month>-<year>` so the blog page links to the HTML page instead of opening the PDF directly

### Deploy changes
```bash
git add -A
git commit -m "Description of changes"
git push origin main
```
Render auto-deploys on push to `main`.

---

## Known issues and future work

- **Volumes not yet set up on Render** — all admin changes (new listings, newsletters) are lost on redeploy until a Render disk is mounted at `/data` and `DATA_DIR=/data` is set
- **Newsletter HTML pages are manually created** — there is no admin UI to auto-generate `market-updates/*.html`. This should eventually be automated in `add_newsletter()` in `admin.py`
- **`/cities/<slug>` URLs** — individual city pages still live under `/cities/` even though the index moved to `/neighborhoods`. This is intentional; the old `/cities` and `/cities.html` URLs 301-redirect to `/neighborhoods`
- **`footer tagline`** — a few pages may still say "Commercial Real Estate" in the footer; search for it if found
