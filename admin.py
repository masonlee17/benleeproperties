"""
Ben Lee Properties — Admin Server
Local:   python3 admin.py  →  http://localhost:2004/admin
Railway: gunicorn admin:app --bind 0.0.0.0:$PORT

Env vars:
  ADMIN_PASSWORD  login password (default: benlee2024)
  SECRET_KEY      Flask session secret
  DATA_DIR        Railway Volume mount path for persistent data (default: ./data)
  PORT            port to bind (set automatically by Railway)
"""

import json, os, re, uuid, calendar, glob
import html as _html
from functools import wraps
from werkzeug.utils import secure_filename
import datetime
from flask import Flask, request, jsonify, session, send_from_directory, Response, redirect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# On Railway: set DATA_DIR to your Volume mount path (e.g. /data)
# Locally:    falls back to ./data (the seeded JSON lives there)
DATA_DIR      = os.environ.get('DATA_DIR', os.path.join(BASE_DIR, 'data'))
REPO_DATA_DIR = os.path.join(BASE_DIR, 'data')   # seeded fallback (read-only)

# Uploaded files land on the Volume; repo copies remain for existing assets
VOL_DOCS_DIR  = os.path.join(DATA_DIR, 'documents')
VOL_IMGS_DIR  = os.path.join(DATA_DIR, 'images')
REPO_DOCS_DIR = os.path.join(BASE_DIR, 'documents')
REPO_IMGS_DIR = os.path.join(BASE_DIR, 'images')

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'benlee2024')
ALLOWED_PDF    = {'pdf'}
ALLOWED_IMG    = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

app = Flask(__name__, static_folder=None)
app.secret_key = os.environ.get('SECRET_KEY', 'bl-dev-secret-change-in-prod')
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64 MB


# ── Helpers ────────────────────────────────────────────────────────────────────

def allowed(filename, exts):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in exts

def seed_volume_if_needed():
    """Seed volume from repo on first deploy or after a format upgrade.

    Runs once at startup. After seeding, the volume is fully authoritative —
    all fields (including sections and has_detail_page) are owned by the volume
    and editable through the admin panel.
    """
    vol_path  = os.path.join(DATA_DIR, 'properties.json')
    repo_path = os.path.join(REPO_DATA_DIR, 'properties.json')
    if not os.path.exists(repo_path):
        return
    try:
        repo_data = json.load(open(repo_path))
    except (json.JSONDecodeError, ValueError):
        return  # repo copy is also unreadable — nothing to seed with; skip gracefully
    needs_seed = False
    if not os.path.exists(vol_path):
        needs_seed = True
    elif vol_path == repo_path:
        pass  # no separate volume; in-image copy is authoritative, no seed needed
    else:
        try:
            vol_data = json.load(open(vol_path))
            # Seed if the volume has no entry with a 'sections' key — old format
            if isinstance(vol_data, list) and vol_data and not any('sections' in p for p in vol_data):
                needs_seed = True
        except (json.JSONDecodeError, ValueError):
            # Volume file is empty or corrupt (e.g. write was interrupted) — re-seed
            needs_seed = True
    if needs_seed:
        save('properties.json', repo_data)

def load(name):
    # Volume takes priority; repo is the read-only fallback (or seed source)
    seen = set()
    for base in (DATA_DIR, REPO_DATA_DIR):
        p = os.path.join(base, name)
        if p in seen or not os.path.exists(p):
            continue
        seen.add(p)
        try:
            return json.load(open(p))
        except (json.JSONDecodeError, ValueError):
            continue  # file is empty or corrupt — try next location
    return []

def save(name, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, name)
    tmp  = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)  # atomic: never leaves a partial/empty file

# Run at import time (works for both `python admin.py` and gunicorn)
try:
    seed_volume_if_needed()
except OSError:
    pass  # volume not mounted yet; load() falls back to repo data

def migrate_homepage_section():
    """One-time migration: give every live_listings property the homepage section tag."""
    vol_path = os.path.join(DATA_DIR, 'properties.json')
    if not os.path.exists(vol_path):
        return
    try:
        props = json.load(open(vol_path))
        changed = False
        for p in props:
            secs = p.get('sections', [])
            if 'live_listings' in secs and 'homepage' not in secs:
                secs.append('homepage')
                p['sections'] = secs
                changed = True
        if changed:
            save('properties.json', props)
    except Exception:
        pass

migrate_homepage_section()

def render_dynamic(filename, marker, section_html):
    """Return an HTML file with the admin-managed section replaced live."""
    path = os.path.join(BASE_DIR, filename)
    text = open(path, encoding='utf-8').read()
    pattern     = rf'<!-- ADMIN:{re.escape(marker)}:START -->.*?<!-- ADMIN:{re.escape(marker)}:END -->'
    replacement = f'<!-- ADMIN:{marker}:START -->\n{section_html}\n<!-- ADMIN:{marker}:END -->'
    return Response(re.sub(pattern, replacement, text, flags=re.DOTALL),
                    mimetype='text/html')


# ── HTML generation ────────────────────────────────────────────────────────────

def price_block_html(status, price, rent, indent):
    """Return property-detail-block-2 HTML line(s) for the status+price row."""
    sold    = 'SOLD' in status.upper()
    is_dual = not sold and 'LEASE' in status.upper() and 'SALE' in status.upper()
    if sold:
        ps = f'${price}' if price else ''
        return (f'{indent}<div class="property-detail-block-2">'
                f'<div class="property-status-2 is-sold">{status}</div>'
                f'<div class="text-block-12">{ps}</div></div>')
    if is_dual:
        sale_str  = f'${price}' if price else ''
        lease_str = f'${rent}/mo' if rent else ''
        r1 = (f'{indent}<div class="property-detail-block-2">'
              f'<div class="property-status-2">FOR SALE</div>'
              f'<div class="text-block-12">{sale_str}</div></div>')
        r2 = (f'{indent}<div class="property-detail-block-2 blp-lease-row">'
              f'<div class="property-status-2">FOR LEASE</div>'
              f'<div class="text-block-12">{lease_str}</div></div>')
        return r1 + '\n' + r2
    if 'LEASE' in status.upper():
        ps = f'${rent}/mo' if rent else ''
    else:
        ps = f'${price}' if price else ''
    return (f'{indent}<div class="property-detail-block-2">'
            f'<div class="property-status-2">{status}</div>'
            f'<div class="text-block-12">{ps}</div></div>')


def build_newsletter_sections(newsletters):
    by_year = {}
    for n in sorted(newsletters, key=lambda x: (x['year'], x['month']), reverse=True):
        by_year.setdefault(n['year'], []).append(n)

    sections = []
    for idx, year in enumerate(sorted(by_year, reverse=True)):
        items = by_year[year]
        lines = [
            '      <section id="read" class="section white-border-bottom">',
            '        <div class="container w-container">',
            '          <div class="padding-8em">',
        ]
        lines.append(f'            <div class="text-block-10">{year}</div>')
        lines.append('            <div class="w-layout-grid grid">')

        img_box  = 'position:relative;width:100%;padding-bottom:75%;height:0;overflow:hidden;margin:0 0 0.75em 0;flex-shrink:0;display:block;'
        img_self = 'position:absolute;top:0;left:0;width:100%;height:118%;object-fit:cover;object-position:top center;display:block;'
        card_box = 'display:flex;flex-direction:column;align-items:flex-start;width:100%;max-width:100%;box-sizing:border-box;text-decoration:none;'

        for j, n in enumerate(items):
            pdf   = n.get('pdf') or '#'
            if pdf == '#':
                continue  # skip empty slots on public blog
            html_url = n.get('html_url', '')
            href  = html_url if html_url else ('/' + pdf if pdf != '#' else '#')
            cover = n.get('cover', '')
            raw_label = n.get('label', '')
            label = raw_label.replace(str(year), '').strip()
            target = ' target="_blank"' if (not html_url and pdf != '#') else ''
            img_tag = f'<img src="{cover}" loading="lazy" alt="" style="{img_self}">' if cover else ''

            lines += [
                f'              <a href="{href}"{target} class="blog-link-block w-inline-block" style="{card_box}">',
                f'                <div class="blog-image" style="{img_box}">{img_tag}</div>',
                f'                <h2 class="blog-heading" style="text-align:left;width:100%;margin:0;">{label}</h2>',
                '              </a>',
            ]

        lines += ['            </div>', '          </div>', '        </div>', '      </section>']
        sections.append('\n'.join(lines))

    return '\n'.join(sections)


# ── Newsletter search index (BM25) ────────────────────────────────────────────

_nl_docs   = []   # [{slug, label, url, cover, text, paragraphs}, ...]
_bm25      = None # BM25Plus instance (None if rank_bm25 not installed)
_sold_docs = []   # [{type:'sale', address, city, price, beds, baths, sqft, text}, ...]

def build_newsletter_search_index():
    """Scan market-updates/*.html, extract nl-text-body text, build BM25 index.
    Called once at startup. Re-call after adding new newsletter HTML files."""
    global _nl_docs, _bm25
    docs = []
    mu_dir = os.path.join(BASE_DIR, 'market-updates')
    if not os.path.isdir(mu_dir):
        return

    # Pull metadata (label, cover, html_url) from newsletters.json
    nl_meta = {}
    for n in load('newsletters.json'):
        url = n.get('html_url', '')
        if url:
            slug = url.replace('/market-updates/', '').strip('/')
            nl_meta[slug] = {
                'label': n.get('label', ''),
                'cover': n.get('cover', ''),
                'url':   url,
            }

    for html_file in sorted(glob.glob(os.path.join(mu_dir, '*.html'))):
        slug = os.path.basename(html_file).replace('.html', '')
        try:
            content = open(html_file, encoding='utf-8').read()
        except Exception:
            continue
        # Extract nl-text-body article
        m = re.search(r'<article[^>]*nl-text-body[^>]*>(.*?)</article>', content, re.DOTALL)
        if not m:
            continue
        article_html = m.group(1)
        # Extract paragraph text, strip inner tags, unescape HTML entities
        paras_raw = re.findall(r'<p[^>]*>(.*?)</p>', article_html, re.DOTALL)
        paras = [_html.unescape(re.sub(r'<[^>]+>', '', p)).strip() for p in paras_raw]
        paras = [p for p in paras if len(p) > 12]  # drop very short / boilerplate lines
        # Short property listing lines like "10422 Lorenzo Pl." (18 chars) are valuable —
        # keep them so address searches find all newsletter mentions.
        if not paras:
            continue

        meta  = nl_meta.get(slug, {})
        label = meta.get('label') or slug.replace('-', ' ').title()
        url   = meta.get('url')   or f'/market-updates/{slug}'
        cover = meta.get('cover', '')

        docs.append({
            'slug':       slug,
            'label':      label,
            'url':        url,
            'cover':      cover,
            'text':       ' '.join(paras),
            'paragraphs': paras,
        })

    _nl_docs = docs
    if not docs:
        return

    try:
        from rank_bm25 import BM25Plus
        # BM25Plus uses IDF = log((N+1)/df) which is always positive.
        # BM25Okapi's IDF can go negative when a term appears in >50% of docs
        # (e.g. Ben's office address "10422 Lorenzo" which is in ~20/34 newsletters).
        # BM25Plus ensures high-frequency terms still score positively.
        tokenized = [_tokenize(doc['text']) for doc in docs]
        _bm25 = BM25Plus(tokenized)
    except ImportError:
        _bm25 = None  # graceful fallback to keyword search

    # Load sold-history addresses into a parallel searchable list
    global _sold_docs
    sold_path = os.path.join(DATA_DIR, 'sold-history.json')
    if not os.path.exists(sold_path):
        sold_path = os.path.join(BASE_DIR, 'data', 'sold-history.json')
    if os.path.exists(sold_path):
        try:
            sold_raw = json.load(open(sold_path, encoding='utf-8'))
            sdocs = []
            for s in sold_raw:
                addr  = s.get('address', '').strip()
                city  = s.get('city', '').strip()
                if not addr:
                    continue
                price = s.get('price', '').strip()
                beds  = s.get('beds', '').strip()
                baths = s.get('baths', '').strip()
                sqft  = s.get('sqft', '').strip()
                nbhds = s.get('neighborhoods', [])
                nbhd_names = {
                    'santa-monica': 'Santa Monica', 'brentwood': 'Brentwood',
                    'westwood': 'Westwood', 'bel-air': 'Bel Air',
                    'beverly-hills': 'Beverly Hills', 'beverlywood': 'Beverlywood',
                    'cheviot-hills': 'Cheviot Hills',
                }
                text_parts = [addr, city, 'CA', 'sold']
                if beds:  text_parts.append(f'{beds} bedroom')
                if baths: text_parts.append(f'{baths} bath')
                if price: text_parts.append(price.replace(',', ''))
                for n in nbhds:
                    label = nbhd_names.get(n, '')
                    if label and label.lower() not in ' '.join(text_parts).lower():
                        text_parts.append(label)
                sdocs.append({
                    'type':          'sale',
                    'address':       addr,
                    'city':          city,
                    'price':         price,
                    'beds':          beds,
                    'baths':         baths,
                    'sqft':          sqft,
                    'neighborhoods': nbhds,
                    'text':          ' '.join(text_parts),
                })
            _sold_docs = sdocs
        except Exception:
            pass


def _tokenize(text):
    """Split text into lowercase alphanumeric tokens, stripping punctuation.
    Keeps numbers so street addresses like '16879 Glenbarr' are fully searchable.
    '16879 Glenbarr Ave' -> ['16879', 'glenbarr', 'ave']
    'ice cream!'         -> ['ice', 'cream']
    Single-character tokens are dropped to avoid noise."""
    return [t for t in re.findall(r'[a-z0-9]+', text.lower()) if len(t) > 1]


def _best_snippet(paragraphs, tokens, max_len=220):
    """Return (best_paragraph, hit_count).
    Scoring priority:
      1. Most distinct query tokens present (paragraph containing all tokens beats one with one)
      2. Highest token density (hits / paragraph length) — prefers focused over sprawling text
    Then centers the excerpt around the first match so the highlighted term is always visible."""
    best_para    = paragraphs[0] if paragraphs else ''
    best_score   = (-1, -1.0)
    best_count   = 0
    for para in paragraphs:
        pl     = para.lower()
        counts = [len(re.findall(r'\b' + re.escape(t) + r'\b', pl)) for t in tokens]
        total  = sum(counts)
        if total == 0:
            continue
        distinct = sum(1 for c in counts if c > 0)
        density  = total / max(len(para), 1)
        score    = (distinct, density)
        if score > best_score:
            best_score = score
            best_count = total
            best_para  = para
    if len(best_para) > max_len:
        # Find the earliest token match so we can center the excerpt on it
        first_pos = len(best_para)
        for t in tokens:
            m = re.search(r'\b' + re.escape(t) + r'\b', best_para, re.IGNORECASE)
            if m:
                first_pos = min(first_pos, m.start())
        start = max(0, first_pos - 60)
        if start > 0:
            snap  = best_para.rfind(' ', 0, start + 1)
            start = snap + 1 if snap >= 0 else start
        excerpt = best_para[start : start + max_len]
        prefix  = '...' if start > 0 else ''
        has_more = start + max_len < len(best_para)
        if prefix:
            excerpt = prefix + excerpt.lstrip()
        if has_more:
            cut     = excerpt.rfind(' ')
            excerpt = (excerpt[:cut] if cut > 0 else excerpt) + '...'
        best_para = excerpt
    return best_para, best_count


def _highlight_snippet(snippet, tokens):
    """Escape HTML entities in snippet and bold whole-word matches in brand red.
    Uses word boundaries so 'ice' never highlights inside 'nice' or 'license'."""
    safe = _html.escape(snippet)
    for tok in sorted(tokens, key=len, reverse=True):
        if len(tok) < 3:
            continue
        safe = re.sub(
            r'\b' + re.escape(_html.escape(tok)) + r'\b',
            lambda m: f'<strong class="blp-hl">{m.group()}</strong>',
            safe, flags=re.IGNORECASE
        )
    return safe


def newsletter_search(q, top_n=12):
    """Return top_n newsletter dicts matching query q, each with a 'snippet' key.
    Results are filtered to only include newsletters where the best paragraph
    actually contains at least one query term (whole-word match)."""
    if not _nl_docs or not q.strip():
        return []
    tokens = _tokenize(q)
    if not tokens:
        return []

    def _all_tokens_present(doc_text, toks):
        """Return True only if every query token appears as a whole word in doc_text."""
        dl = doc_text.lower()
        return all(re.search(r'\b' + re.escape(t) + r'\b', dl) for t in toks)

    if _bm25 is not None:
        scores = _bm25.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in ranked:
            if len(results) >= top_n:
                break
            doc = _nl_docs[idx]
            # Hard filter: every query token must be present somewhere in the doc.
            # This prevents "2765 anchor" returning all newsletters that mention
            # "anchor" without the specific street number.
            if not _all_tokens_present(doc['text'], tokens):
                continue
            snippet, hit_count = _best_snippet(doc['paragraphs'], tokens)
            if hit_count == 0:
                continue  # no paragraph contains any token; skip
            results.append({**doc, 'score': round(score, 3), 'snippet': snippet})
        return results
    else:
        # Simple keyword fallback: all tokens must appear as whole words
        results = []
        for doc in _nl_docs:
            if _all_tokens_present(doc['text'], tokens):
                snippet, _ = _best_snippet(doc['paragraphs'], tokens)
                results.append({**doc, 'score': 1, 'snippet': snippet})
        return results[:top_n]


def sold_search(q, max_n=8):
    """Return up to max_n sold properties whose text contains all query tokens (whole-word).
    Simple linear scan over _sold_docs — fast enough for 404 short docs."""
    if not _sold_docs or not q.strip():
        return []
    tokens = _tokenize(q)
    if not tokens:
        return []
    results = []
    for doc in _sold_docs:
        text = doc['text']
        if all(re.search(r'\b' + re.escape(t) + r'\b', text, re.IGNORECASE) for t in tokens):
            results.append(doc)
    return results[:max_n]


def build_search_bar_html(q=''):
    """Render the search bar form with optional pre-filled query."""
    safe_q = _html.escape(q)
    return (
        '      <section class="section blp-nl-search-wrap">\n'
        '        <div class="container w-container">\n'
        f'          <form action="/blog" method="GET" class="blp-nl-search-form" role="search" aria-label="Search newsletters">\n'
        f'            <input type="search" name="q" value="{safe_q}" placeholder="Search all newsletters..." '
        'class="blp-nl-search-input" aria-label="Search newsletters" autocomplete="off">\n'
        '            <button type="submit" class="blp-nl-search-btn" aria-label="Search">'
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>'
        '</svg></button>\n'
        '          </form>\n'
        '        </div>\n'
        '      </section>'
    )


def _sale_card_html(s, tokens):
    """Render a single sold-property search result card."""
    addr  = _highlight_snippet(s.get('address', ''), tokens)
    city  = _html.escape(s.get('city', ''))
    price = s.get('price', '')
    beds  = s.get('beds', '')
    baths = s.get('baths', '').rstrip('0').rstrip('.')
    sqft  = s.get('sqft', '')
    meta_parts = []
    if price: meta_parts.append(f'Sold ${price}')
    if beds:  meta_parts.append(f'{beds} bd')
    if baths: meta_parts.append(f'{baths} ba')
    if sqft:  meta_parts.append(f'{sqft} sf')
    meta = ' &nbsp;·&nbsp; '.join(meta_parts)
    meta_line = f'<div style="font-size:0.82em;color:#27ae60;font-weight:600;margin-top:0.4em;">{meta}</div>' if meta else ''
    return (
        '              <div class="blp-sale-card" style="display:flex;flex-direction:column;'
        'background:#f4f9f4;border:1px solid #cce5cc;border-radius:6px;padding:1em 1.25em;box-sizing:border-box;">\n'
        '                <div style="font-size:0.63em;font-weight:700;letter-spacing:0.09em;'
        'text-transform:uppercase;color:#27ae60;margin-bottom:0.35em;">Sold</div>\n'
        f'                <div style="font-size:0.95em;font-weight:600;color:#1a1a1a;margin-bottom:0.1em;">{addr}</div>\n'
        f'                <div style="font-size:0.82em;color:#666;">{city}, CA</div>\n'
        f'                {meta_line}\n'
        '              </div>'
    )


def build_search_results_html(q):
    """Render search results: sold property cards (green) then newsletter cards."""
    nl_results   = newsletter_search(q)
    sale_results = sold_search(q)
    tokens       = _tokenize(q)

    if not nl_results and not sale_results:
        safe_q = _html.escape(q)
        return (
            '      <section class="section white-border-bottom">\n'
            '        <div class="container w-container">\n'
            '          <div class="padding-8em">\n'
            f'            <p class="toptitle-paragraph">No results found for <em>{safe_q}</em>'
            ' &nbsp;<a href="/blog" style="color:#ed2227;font-size:0.85em;text-decoration:underline;">clear</a></p>\n'
            '          </div>\n'
            '        </div>\n'
            '      </section>'
        )

    img_box  = 'position:relative;width:100%;padding-bottom:75%;height:0;overflow:hidden;margin:0 0 0.75em 0;flex-shrink:0;display:block;'
    img_self = 'position:absolute;top:0;left:0;width:100%;height:118%;object-fit:cover;object-position:top center;display:block;'
    card_box = 'display:flex;flex-direction:column;align-items:flex-start;width:100%;max-width:100%;box-sizing:border-box;text-decoration:none;'

    cards = []

    # Sold property cards come first (green badge, distinct style)
    for s in sale_results:
        cards.append(_sale_card_html(s, tokens))

    # Newsletter cards follow
    for r in nl_results:
        cover   = r.get('cover', '')
        label   = _html.escape(r.get('label', r['slug']))
        url     = r.get('url', '#')
        snippet = _highlight_snippet(r.get('snippet', ''), tokens)
        img_tag = f'<img src="{cover}" loading="lazy" alt="" style="{img_self}">' if cover else ''
        cards.append(
            f'              <a href="{url}" class="blog-link-block w-inline-block blp-search-card" style="{card_box}">\n'
            f'                <div class="blog-image" style="{img_box}">{img_tag}</div>\n'
            f'                <h2 class="blog-heading" style="text-align:left;width:100%;margin:0 0 0.4em 0;">{label}</h2>\n'
            f'                <p class="blp-search-snippet">{snippet}</p>\n'
            '              </a>'
        )

    count  = len(nl_results) + len(sale_results)
    word   = 'result' if count == 1 else 'results'
    safe_q = _html.escape(q)

    lines = [
        '      <section class="section white-border-bottom">',
        '        <div class="container w-container">',
        '          <div class="padding-8em">',
        f'            <p class="toptitle-paragraph" style="margin-bottom:1.5em;">'
        f'{count} {word} for <em>{safe_q}</em>'
        ' &nbsp;<a href="/blog" style="color:#ed2227;font-size:0.85em;text-decoration:underline;">clear</a></p>',
        '            <div class="w-layout-grid grid">',
    ] + cards + [
        '            </div>',
        '          </div>',
        '        </div>',
        '      </section>',
    ]
    return '\n'.join(lines)


# Build newsletter search index at startup (< 1s for 34 issues; ~2-3s at 200)
# Re-call or restart after adding new market-updates/*.html files.
build_newsletter_search_index()


def build_property_items(properties):
    """Card generator for current-listings.html — standard template matching all other listing pages."""
    cards = []
    for p in sorted(properties, key=lambda x: x.get('order', 999)):
        addr   = p.get('address', '')
        city   = p.get('city', 'Los Angeles')
        state  = p.get('state', 'CA')
        price  = p.get('price', '')
        rent   = p.get('rent', '')
        beds   = p.get('beds', '')
        baths  = p.get('baths', '')
        sqft   = p.get('sqft', '')
        status = p.get('status', 'FOR SALE')
        img1   = p.get('image1', '')
        img2   = p.get('image2', '')
        detail_url = f'/property/{p["id"]}' if p.get('has_detail_page') else 'contact.html'

        card = [
            '                      <div role="listitem" class="property-grid-item-2 w-dyn-item">',
            '                        <div class="property-link with-radius">',
            '                          <div class="property-image-grid">',
            f'                            <a href="{detail_url}" aria-label="Contact Ben" class="circle-button in-property-2 w-inline-block">',
            '                              <div class="ciricle-outline is-white"></div>'
            '<img loading="lazy" src="images/arrow_forward_white_24dp.svg" alt="Contact" class="ciricle-icon">',
            '                            </a>',
        ]
        if img1:
            card.append(f'                            <img alt="{addr}" loading="lazy" src="{img1}" class="property-image is-1st">')
        if img2:
            card.append(f'                            <img alt="{addr}" loading="lazy" src="{img2}" class="property-image is-2nd">')
        card += [
            '                          </div>',
            f'                          <a href="{detail_url}" class="property-inner w-inline-block">',
            f'                            <div class="property-address"><p class="property-address-title">{addr}, {city}, {state}</p></div>',
            '                          </a>',
            '                          <div class="property-details">',
            price_block_html(status, price, rent, '                            '),
            '                          </div>',
            '                          <div class="property-details">',
            '                            <div class="property-detail-block-3">',
        ]
        if beds:
            card.append(f'                              <div class="property-detail-amenity with-tooltip">'
                        f'<img alt="" loading="lazy" src="images/bed_black_24dp.svg" class="property-detail-amenity-icon">'
                        f'<div>{beds}</div><p class="tooltip">Bedrooms</p></div>')
        if baths:
            card.append(f'                              <div class="property-detail-amenity with-tooltip">'
                        f'<img alt="" loading="lazy" src="images/shower_black_24dp.svg" class="property-detail-amenity-icon">'
                        f'<div>{baths}</div><p class="tooltip">Bathrooms</p></div>')
        if sqft:
            card.append(f'                              <div class="property-detail-amenity with-tooltip">'
                        f'<img alt="" loading="lazy" src="images/select_all_black_24dp.svg" class="property-detail-amenity-icon">'
                        f'<div>{sqft} sqft</div><p class="tooltip">Interior size</p></div>')
        card += [
            '                            </div>',
            '                          </div>',
            '                        </div>',
            '                      </div>',
        ]
        cards.append('\n'.join(card))
    return '\n'.join(cards)


def build_listing_items(listings):
    """HTML generator for for-buyers-3.html — different card structure from Built by Ben."""
    cards = []
    for p in sorted(listings, key=lambda x: x.get('order', 999)):
        addr   = p.get('address', '')
        city   = p.get('city', 'Los Angeles')
        price  = p.get('price', '')
        rent   = p.get('rent', '')
        beds   = p.get('beds', '')
        baths  = p.get('baths', '')
        sqft   = p.get('sqft', '')
        status = p.get('status', 'FOR SALE')
        img1   = p.get('image1', '')
        img2   = p.get('image2', '')

        detail_url = f'/property/{p["id"]}' if p.get('has_detail_page') else 'contact.html'

        card = [
            '                        <div role="listitem" class="property-grid-item w-dyn-item">',
            '                          <div class="property-link with-radius">',
            '                            <div class="property-image-grid">',
            f'                              <a href="{detail_url}" aria-label="Contact Ben" class="circle-button in-property-2 w-inline-block">',
            '                                <div class="ciricle-outline is-white"></div>'
            '<img loading="lazy" src="images/arrow_right_white_24dp.svg" alt="Contact" class="ciricle-icon">',
            '                              </a>',
        ]
        if img1:
            card.append(f'                              <img alt="{addr}" loading="lazy" src="{img1}" class="property-image is-1st">')
        if img2:
            card.append(f'                              <img alt="{addr}" loading="lazy" src="{img2}" class="property-image is-2nd">')
        card += [
            '                            </div>',
            f'                            <a href="{detail_url}" class="property-inner w-inline-block">',
            f'                              <div class="property-address"><p class="property-address-title">{addr}, {city}</p></div>',
            '                            </a>',
            '                            <div class="property-details">',
            price_block_html(status, price, rent, '                              '),
            '                            </div>',
            '                            <div class="property-details">',
            '                              <div class="property-detail-block-3">',
        ]
        if beds:
            card.append(f'                                <div class="property-detail-amenity with-tooltip">'
                        f'<img alt="" loading="lazy" src="images/bed_black_24dp.svg" class="property-detail-amenity-icon">'
                        f'<div>{beds}</div><p class="tooltip">Bedrooms</p></div>')
        if baths:
            card.append(f'                                <div class="property-detail-amenity with-tooltip">'
                        f'<img alt="" loading="lazy" src="images/shower_black_24dp.svg" class="property-detail-amenity-icon">'
                        f'<div>{baths}</div><p class="tooltip">Bathrooms</p></div>')
        if sqft:
            card.append(f'                                <div class="property-detail-amenity with-tooltip">'
                        f'<img alt="" loading="lazy" src="images/select_all_black_24dp.svg" class="property-detail-amenity-icon">'
                        f'<div>{sqft} sqft</div><p class="tooltip">Interior size</p></div>')
        card += [
            '                              </div>',
            '                            </div>',
            '                          </div>',
            '                        </div>',
        ]
        cards.append('\n'.join(card))
    return '\n'.join(cards)


def build_deals_items(listings):
    """HTML generator for deals.html — identical card structure to build_listing_items."""
    cards = []
    for p in sorted(listings, key=lambda x: x.get('order', 999)):
        addr   = p.get('address', '')
        city   = p.get('city', 'Los Angeles')
        price  = p.get('price', '')
        rent   = p.get('rent', '')
        beds   = p.get('beds', '')
        baths  = p.get('baths', '')
        sqft   = p.get('sqft', '')
        status = p.get('status', 'FOR SALE')
        img1   = p.get('image1', '')
        img2   = p.get('image2', '')

        detail_url = f'/property/{p["id"]}' if p.get('has_detail_page') else 'contact.html'

        card = [
            '                        <div role="listitem" class="property-grid-item w-dyn-item">',
            '                          <div class="property-link with-radius">',
            '                            <div class="property-image-grid">',
            f'                              <a href="{detail_url}" aria-label="Contact Ben" class="circle-button in-property-2 w-inline-block">',
            '                                <div class="ciricle-outline is-white"></div>'
            '<img loading="lazy" src="images/arrow_right_white_24dp.svg" alt="Contact" class="ciricle-icon">',
            '                              </a>',
        ]
        if img1:
            card.append(f'                              <img alt="{addr}" loading="lazy" src="{img1}" class="property-image is-1st">')
        if img2:
            card.append(f'                              <img alt="{addr}" loading="lazy" src="{img2}" class="property-image is-2nd">')
        card += [
            '                            </div>',
            f'                            <a href="{detail_url}" class="property-inner w-inline-block">',
            f'                              <div class="property-address"><p class="property-address-title">{addr}, {city}</p></div>',
            '                            </a>',
            '                            <div class="property-details">',
            price_block_html(status, price, rent, '                              '),
            '                            </div>',
            '                            <div class="property-details">',
            '                              <div class="property-detail-block-3">',
        ]
        if beds:
            card.append(f'                                <div class="property-detail-amenity with-tooltip">'
                        f'<img alt="" loading="lazy" src="images/bed_black_24dp.svg" class="property-detail-amenity-icon">'
                        f'<div>{beds}</div><p class="tooltip">Bedrooms</p></div>')
        if baths:
            card.append(f'                                <div class="property-detail-amenity with-tooltip">'
                        f'<img alt="" loading="lazy" src="images/shower_black_24dp.svg" class="property-detail-amenity-icon">'
                        f'<div>{baths}</div><p class="tooltip">Bathrooms</p></div>')
        if sqft:
            card.append(f'                                <div class="property-detail-amenity with-tooltip">'
                        f'<img alt="" loading="lazy" src="images/select_all_black_24dp.svg" class="property-detail-amenity-icon">'
                        f'<div>{sqft} sqft</div><p class="tooltip">Interior size</p></div>')
        card += [
            '                              </div>',
            '                            </div>',
            '                          </div>',
            '                        </div>',
        ]
        cards.append('\n'.join(card))
    return '\n'.join(cards)


def build_deals_map_html(listings):
    """Build a Leaflet.js map showing featured former deals + full sold history.
    Featured deals (properties.json former_deals) get large markers with detail popups.
    Historical sales (sold-history.json) get small dots with price only."""
    import json as _json
    markers = []

    # Layer 1: historical sold properties (small dots, no detail page)
    hist_path = os.path.join(DATA_DIR, 'sold-history.json')
    if not os.path.exists(hist_path):
        hist_path = os.path.join(BASE_DIR, 'data', 'sold-history.json')
    if os.path.exists(hist_path):
        try:
            hist = json.load(open(hist_path, encoding='utf-8'))
            for h in hist:
                lat, lng = h.get('lat'), h.get('lng')
                if not lat or not lng: continue
                addr  = h.get('address', '')
                city  = h.get('city', '')
                price = h.get('price', '')
                beds  = h.get('beds', '')
                popup = (f'<strong style="font-size:0.85em;">{addr}</strong><br>'
                         f'<span style="font-size:0.78em;color:#555;">{city}, CA</span><br>'
                         + (f'<span style="color:#27ae60;font-weight:600;font-size:0.82em;">Sold ${price}</span>' if price else '')
                         + (f'<br><span style="font-size:0.76em;color:#888;">{beds} bd</span>' if beds else ''))
                markers.append({'lat': lat, 'lng': lng, 'popup': popup,
                                'status': 'SOLD', 'layer': 'hist'})
        except Exception:
            pass

    # Layer 2: featured former deals (large markers with full detail)
    for p in listings:
        lat = p.get('lat')
        lng = p.get('lng')
        if not lat or not lng:
            continue
        addr   = p.get('address', '')
        city   = p.get('city', 'Los Angeles')
        status = p.get('status', '')
        price  = p.get('price', '')
        rent   = p.get('rent', '')
        prop_id = p.get('id', '')
        has_detail = p.get('has_detail_page', False)
        detail_url = f'/property/{prop_id}' if has_detail else '/contact.html'
        img    = p.get('image1', '')
        img_src = img if img.startswith('http') else f'/{img}'
        img_tag = f'<img src="{img_src}" style="width:100%;height:80px;object-fit:cover;border-radius:4px;margin-bottom:6px;" alt="">' if img else ''
        if price:
            price_str = f'${price}'
        elif rent:
            price_str = f'${rent}/mo'
        else:
            price_str = ''
        status_color = '#27ae60' if status in ('SOLD','LEASED') else '#e74c3c' if 'ESCROW' in status else '#2980b9'
        popup_html = (
            f'{img_tag}'
            f'<strong style="font-size:0.9em;">{addr}</strong><br>'
            f'<span style="color:{status_color};font-weight:600;">{status}</span>'
            + (f' &nbsp;·&nbsp; {price_str}' if price_str else '') +
            f'<br><a href="{detail_url}" style="color:#e74c3c;font-size:0.8em;">View details →</a>'
        )
        markers.append({'lat': lat, 'lng': lng, 'popup': popup_html, 'status': status})

    if not markers:
        return ''

    markers_js = _json.dumps(markers)
    return f"""      <section class="section" style="background:#f5f5f5;padding:2em 0;">
        <div class="container w-container">
          <h2 style="font-family:'Cormorant Garamond',serif;font-size:2em;text-align:center;margin-bottom:0.3em;">404 Transactions — Map View</h2>
          <p style="text-align:center;color:#777;font-size:0.85em;margin-bottom:1em;">Every single-family property Ben Lee has sold, mapped.</p>
          <div id="blp-deals-map" style="width:100%;height:520px;border-radius:8px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.12);"></div>
        </div>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
        <script>
        (function(){{
          var map = L.map('blp-deals-map').setView([34.04, -118.42], 11);
          L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            maxZoom: 18
          }}).addTo(map);

          // Small dot for historical sales
          var histIcon = L.divIcon({{
            className: '',
            html: '<div style="background:#27ae60;border:1.5px solid rgba(255,255,255,.8);width:8px;height:8px;border-radius:50%;box-shadow:0 1px 3px rgba(0,0,0,.35);opacity:0.85;"></div>',
            iconSize: [8, 8], iconAnchor: [4, 4]
          }});
          // Larger icons for featured former deals
          var soldIcon = L.divIcon({{
            className: '',
            html: '<div style="background:#27ae60;border:2px solid #fff;width:16px;height:16px;border-radius:50%;box-shadow:0 1px 5px rgba(0,0,0,.45);"></div>',
            iconSize: [16, 16], iconAnchor: [8, 8]
          }});
          var activeIcon = L.divIcon({{
            className: '',
            html: '<div style="background:#e74c3c;border:2px solid #fff;width:16px;height:16px;border-radius:50%;box-shadow:0 1px 5px rgba(0,0,0,.45);"></div>',
            iconSize: [16, 16], iconAnchor: [8, 8]
          }});
          var escrowIcon = L.divIcon({{
            className: '',
            html: '<div style="background:#2980b9;border:2px solid #fff;width:16px;height:16px;border-radius:50%;box-shadow:0 1px 5px rgba(0,0,0,.45);"></div>',
            iconSize: [16, 16], iconAnchor: [8, 8]
          }});

          var markers = {markers_js};
          markers.forEach(function(m) {{
            var icon;
            if (m.layer === 'hist') {{
              icon = histIcon;
            }} else if (m.status === 'SOLD' || m.status === 'LEASED') {{
              icon = soldIcon;
            }} else if (m.status.indexOf('ESCROW') >= 0) {{
              icon = escrowIcon;
            }} else {{
              icon = activeIcon;
            }}
            L.marker([m.lat, m.lng], {{icon: icon}})
              .bindPopup(m.popup, {{maxWidth: 240}})
              .addTo(map);
          }});

          // Legend
          var legend = L.control({{position: 'bottomright'}});
          legend.onAdd = function() {{
            var d = L.DomUtil.create('div');
            d.style.cssText = 'background:#fff;padding:8px 12px;border-radius:6px;font-size:0.78em;line-height:1.9;box-shadow:0 1px 6px rgba(0,0,0,.2);';
            d.innerHTML = '<span style="display:inline-block;background:#27ae60;width:8px;height:8px;border-radius:50%;margin-right:5px;opacity:.85;"></span>Historical sale<br>'
                        + '<span style="display:inline-block;background:#27ae60;width:12px;height:12px;border-radius:50%;margin-right:5px;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.3);"></span>Featured sold / leased<br>'
                        + '<span style="display:inline-block;background:#2980b9;width:12px;height:12px;border-radius:50%;margin-right:5px;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.3);"></span>In escrow<br>'
                        + '<span style="display:inline-block;background:#e74c3c;width:12px;height:12px;border-radius:50%;margin-right:5px;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.3);"></span>Active listing';
            return d;
          }};
          legend.addTo(map);
        }})();
        </script>
      </section>"""


def build_property_detail_html(p):
    """Generate a complete detail page HTML string for a property."""
    prop_id  = p.get('id', '')
    addr     = p.get('address', '')
    city     = p.get('city', 'Los Angeles')
    state    = p.get('state', 'CA')
    status   = p.get('status', 'FOR SALE')
    price    = p.get('price', '')
    rent     = p.get('rent', '')
    beds     = p.get('beds', '')
    baths    = p.get('baths', '')
    sqft     = p.get('sqft', '')
    desc     = p.get('description', '')
    def _abs(path):
        if not path: return path
        return path if path.startswith(('/', 'http')) else '/' + path
    images   = [_abs(p[k]) for k in [f'image{i}' for i in range(1, 21)] if p.get(k)]

    title    = f'{addr} | Ben Lee Properties'
    og_img   = ('https://www.benleeproperties.com' + images[0]) if images else ''

    slides_html = '\n'.join(
        f'            <div class="blp-pd-slide"><img src="{img}" alt="{addr}" loading="lazy"></div>'
        for img in images
    ) or f'            <div class="blp-pd-slide" style="background:#07264b;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,.4);font-size:1.2em">No photos yet</div>'

    slide_count = max(len(images), 1)

    # Stats
    is_sold  = 'SOLD' in status.upper()
    is_lease = 'LEASE' in status.upper() and 'SALE' not in status.upper()
    is_dual  = 'LEASE' in status.upper() and 'SALE' in status.upper()
    stats_parts = []
    if price and not is_lease:
        label = 'Sold' if is_sold else 'Sale'
        stats_parts.append(f'<div class="blp-pd-stat"><div class="blp-pd-stat-val">${price}</div><div class="blp-pd-stat-lbl">{label}</div></div>')
    if rent and not is_sold:
        stats_parts.append('<div class="blp-pd-stat-divider"></div>' if stats_parts else '')
        stats_parts.append(f'<div class="blp-pd-stat"><div class="blp-pd-stat-val">${rent}/mo</div><div class="blp-pd-stat-lbl">Lease</div></div>')
    if beds:
        stats_parts.append('<div class="blp-pd-stat-divider"></div>' if stats_parts else '')
        stats_parts.append(f'<div class="blp-pd-stat"><div class="blp-pd-stat-val">{beds}</div><div class="blp-pd-stat-lbl">Beds</div></div>')
    if baths:
        stats_parts.append('<div class="blp-pd-stat-divider"></div>' if stats_parts else '')
        stats_parts.append(f'<div class="blp-pd-stat"><div class="blp-pd-stat-val">{baths}</div><div class="blp-pd-stat-lbl">Baths</div></div>')
    if sqft:
        stats_parts.append('<div class="blp-pd-stat-divider"></div>' if stats_parts else '')
        stats_parts.append(f'<div class="blp-pd-stat"><div class="blp-pd-stat-val">{sqft}</div><div class="blp-pd-stat-lbl">Sq Ft</div></div>')
    stats_html = '\n'.join(s for s in stats_parts if s)

    # Description paragraphs
    desc_html = ''.join(f'<p>{para.strip()}</p>' for para in desc.split('\n') if para.strip()) if desc else '<p><em>Description coming soon.</em></p>'

    # Fact rows
    fact_rows = []
    fact_rows.append(f'<div class="blp-pd-fact-row"><span class="blp-pd-fact-label">Status</span><span class="blp-pd-fact-value">{status}</span></div>')
    if price and not is_lease:
        fact_rows.append(f'<div class="blp-pd-fact-row"><span class="blp-pd-fact-label">{"Sold Price" if is_sold else "Sale Price"}</span><span class="blp-pd-fact-value">${price}</span></div>')
    if rent and not is_sold:
        fact_rows.append(f'<div class="blp-pd-fact-row"><span class="blp-pd-fact-label">Monthly Lease</span><span class="blp-pd-fact-value">${rent}/mo</span></div>')
    if beds:
        fact_rows.append(f'<div class="blp-pd-fact-row"><span class="blp-pd-fact-label">Bedrooms</span><span class="blp-pd-fact-value">{beds}</span></div>')
    if baths:
        fact_rows.append(f'<div class="blp-pd-fact-row"><span class="blp-pd-fact-label">Bathrooms</span><span class="blp-pd-fact-value">{baths}</span></div>')
    if sqft:
        fact_rows.append(f'<div class="blp-pd-fact-row"><span class="blp-pd-fact-label">Interior</span><span class="blp-pd-fact-value">{sqft} sq ft</span></div>')
    facts_html = '\n'.join(fact_rows)

    # Read the template file
    tpl_path = os.path.join(BASE_DIR, 'property_detail_template.html')
    tpl = open(tpl_path, encoding='utf-8').read()

    return (tpl
        .replace('BLPTOKEN_TITLE',       title)
        .replace('BLPTOKEN_OG_IMAGE',    og_img)
        .replace('BLPTOKEN_SLIDES_HTML', slides_html)
        .replace('BLPTOKEN_SLIDE_COUNT', str(slide_count))
        .replace('BLPTOKEN_STATUS',      status)
        .replace('BLPTOKEN_ADDRESS',     addr)
        .replace('BLPTOKEN_CITY_STATE',  f'{city}, {state}')
        .replace('BLPTOKEN_STATS_HTML',  stats_html)
        .replace('BLPTOKEN_DESC_HTML',   desc_html)
        .replace('BLPTOKEN_FACTS_HTML',  facts_html)
        .replace('BLPTOKEN_PROP_ID',     prop_id)
    )


def build_index_listing_items(listings):
    """Homepage Current Properties card generator — standard template, links to for-buyers-3.html."""
    cards = []
    for p in sorted(listings, key=lambda x: x.get('order', 999)):
        addr   = p.get('address', '')
        city   = p.get('city', 'Los Angeles')
        state  = p.get('state', 'CA')
        price  = p.get('price', '')
        rent   = p.get('rent', '')
        beds   = p.get('beds', '')
        baths  = p.get('baths', '')
        sqft   = p.get('sqft', '')
        status = p.get('status', 'FOR SALE')
        img1   = p.get('image1', '')
        img2   = p.get('image2', '')

        detail_url = f'/property/{p["id"]}' if p.get('has_detail_page') else 'contact.html'

        card = [
            '                    <div role="listitem" class="property-grid-item-2 w-dyn-item">',
            '                      <div class="property-link with-radius">',
            '                        <div class="property-image-grid">',
            f'                          <a href="{detail_url}" aria-label="View listing" class="circle-button in-property-2 w-inline-block">',
            '                            <div class="ciricle-outline is-white"></div>'
            '<img loading="lazy" src="images/arrow_forward_white_24dp.svg" alt="" class="ciricle-icon">',
            '                          </a>',
        ]
        if img1:
            card.append(f'                          <img alt="{addr}" loading="lazy" src="{img1}" class="property-image is-1st">')
        if img2:
            card.append(f'                          <img alt="{addr}" loading="lazy" src="{img2}" class="property-image is-2nd">')
        card += [
            '                        </div>',
            f'                        <a href="{detail_url}" class="property-inner w-inline-block">',
            f'                          <div class="property-address"><p class="property-address-title">{addr}, {city}, {state}</p></div>',
            '                        </a>',
            '                        <div class="property-details">',
            price_block_html(status, price, rent, '                          '),
            '                        </div>',
            '                        <div class="property-details">',
            '                          <div class="property-detail-block-3">',
        ]
        if beds:
            card.append(f'                            <div class="property-detail-amenity with-tooltip">'
                        f'<img alt="" loading="lazy" src="images/bed_black_24dp.svg" class="property-detail-amenity-icon">'
                        f'<div>{beds}</div><p class="tooltip">Bedrooms</p></div>')
        if baths:
            card.append(f'                            <div class="property-detail-amenity with-tooltip">'
                        f'<img alt="" loading="lazy" src="images/shower_black_24dp.svg" class="property-detail-amenity-icon">'
                        f'<div>{baths}</div><p class="tooltip">Bathrooms</p></div>')
        if sqft:
            card.append(f'                            <div class="property-detail-amenity with-tooltip">'
                        f'<img alt="" loading="lazy" src="images/select_all_black_24dp.svg" class="property-detail-amenity-icon">'
                        f'<div>{sqft} sqft</div><p class="tooltip">Interior size</p></div>')
        card += [
            '                          </div>',
            '                        </div>',
            '                      </div>',
            '                    </div>',
        ]
        cards.append('\n'.join(card))
    return '\n'.join(cards)


# ── Auth ───────────────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/admin/login', methods=['POST'])
def login():
    if (request.json or {}).get('password') == ADMIN_PASSWORD:
        session['logged_in'] = True
        return jsonify({'ok': True})
    return jsonify({'error': 'Wrong password'}), 401

@app.route('/admin/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'ok': True})

@app.route('/admin/check')
def check_auth():
    return jsonify({'loggedIn': bool(session.get('logged_in'))})


# ── Newsletter API ─────────────────────────────────────────────────────────────

def extract_pdf_cover(pdf_rel, nid):
    """Render first PDF page as JPEG, save to images/nl-covers/{nid}.jpg.
    Returns relative path on success, '' on failure."""
    try:
        import fitz
    except ImportError:
        return ''
    pdf_name = pdf_rel.replace('documents/', '', 1)
    pdf_abs = None
    for d in [VOL_DOCS_DIR, REPO_DOCS_DIR]:
        c = os.path.join(d, pdf_name)
        if os.path.exists(c):
            pdf_abs = c
            break
    if not pdf_abs:
        return ''
    cover_dir = os.path.join(VOL_IMGS_DIR, 'nl-covers')
    os.makedirs(cover_dir, exist_ok=True)
    cover_abs = os.path.join(cover_dir, f'{nid}.jpg')
    try:
        doc = fitz.open(pdf_abs)
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        pix.save(cover_abs)
        doc.close()
        return f'images/nl-covers/{nid}.jpg'
    except Exception:
        return ''


@app.route('/api/newsletters', methods=['GET'])
@login_required
def get_newsletters():
    return jsonify(load('newsletters.json'))

@app.route('/api/newsletters', methods=['POST'])
@login_required
def add_newsletter():
    year  = int(request.form.get('year', datetime.date.today().year))
    month = int(request.form.get('month', 1))
    nid   = f'nl-{year}-{month:02d}'

    pdf_url  = ''
    pdf_file = request.files.get('pdf')
    if pdf_file and pdf_file.filename and allowed(pdf_file.filename, ALLOWED_PDF):
        fn = secure_filename(pdf_file.filename)
        os.makedirs(VOL_DOCS_DIR, exist_ok=True)
        pdf_file.save(os.path.join(VOL_DOCS_DIR, fn))
        pdf_url = f'documents/{fn}'

    cover_url = extract_pdf_cover(pdf_url, nid) if pdf_url else ''
    label     = f'{calendar.month_name[month]} {year}'

    newsletters = load('newsletters.json')
    existing = next((n for n in newsletters if n['id'] == nid), None)
    if existing:
        if pdf_url:
            existing['pdf'] = pdf_url
        if cover_url:
            existing['cover'] = cover_url
        existing['label'] = label
        entry = existing
    else:
        entry = {
            'id': nid,
            'label': label, 'year': year, 'month': month,
            'pdf': pdf_url, 'cover': cover_url,
        }
        newsletters.append(entry)
    save('newsletters.json', newsletters)
    return jsonify(entry), 201

@app.route('/api/newsletters/<nid>', methods=['DELETE'])
@login_required
def delete_newsletter(nid):
    newsletters = load('newsletters.json')
    entry = next((n for n in newsletters if n['id'] == nid), None)
    if entry:
        cover = entry.get('cover', '')
        if cover and 'nl-covers' in cover:
            cover_abs = os.path.join(VOL_IMGS_DIR, 'nl-covers', os.path.basename(cover))
            if os.path.exists(cover_abs):
                os.remove(cover_abs)
    save('newsletters.json', [n for n in newsletters if n['id'] != nid])
    return jsonify({'ok': True})


@app.route('/api/newsletters/sync-covers', methods=['POST'])
@login_required
def sync_covers():
    """Update cover paths in the live data to point at extracted nl-covers images.
    Needed when the Railway volume has a stale newsletters.json from before extraction."""
    newsletters = load('newsletters.json')
    updated = 0
    for n in newsletters:
        nid = n.get('id', '')
        expected = f'images/nl-covers/{nid}.jpg'
        # Check if the extracted cover exists in the repo
        if os.path.exists(os.path.join(REPO_IMGS_DIR, 'nl-covers', f'{nid}.jpg')):
            if n.get('cover') != expected:
                n['cover'] = expected
                updated += 1
    save('newsletters.json', newsletters)
    return jsonify({'ok': True, 'updated': updated})


# ── Property API ───────────────────────────────────────────────────────────────

@app.route('/api/properties', methods=['GET'])
@login_required
def get_properties():
    return jsonify(load('properties.json'))

@app.route('/api/properties', methods=['POST'])
@login_required
def add_property():
    data  = request.json or {}
    props = load('properties.json')
    max_order = max((p.get('order', 0) for p in props), default=0)
    entry = {'id': str(uuid.uuid4()), 'order': max_order + 1, **data}
    props.append(entry)
    save('properties.json', props)
    return jsonify(entry), 201

@app.route('/api/properties/<pid>', methods=['PUT'])
@login_required
def update_property(pid):
    data  = request.json or {}
    props = load('properties.json')
    for i, p in enumerate(props):
        if p['id'] == pid:
            props[i] = {**p, **data}
            break
    save('properties.json', props)
    return jsonify({'ok': True})

@app.route('/api/properties/<pid>', methods=['DELETE'])
@login_required
def delete_property(pid):
    props = [p for p in load('properties.json') if p['id'] != pid]
    for i, p in enumerate(props):
        p['order'] = i + 1
    save('properties.json', props)
    return jsonify({'ok': True})


# ── Image upload ───────────────────────────────────────────────────────────────

@app.route('/api/upload/image', methods=['POST'])
@login_required
def upload_image():
    f = request.files.get('image')
    if not f or not f.filename:
        return jsonify({'error': 'No file'}), 400
    if not allowed(f.filename, ALLOWED_IMG):
        return jsonify({'error': 'Invalid file type'}), 400
    fn = secure_filename(f.filename)
    os.makedirs(VOL_IMGS_DIR, exist_ok=True)
    f.save(os.path.join(VOL_IMGS_DIR, fn))
    return jsonify({'path': f'images/{fn}'})


# ── Listings API (redirected to properties.json) ───────────────────────────────

@app.route('/api/listings', methods=['GET'])
@login_required
def get_listings():
    return jsonify([p for p in load('properties.json') if 'live_listings' in p.get('sections', [])])

@app.route('/api/listings', methods=['POST'])
@login_required
def add_listing():
    data  = request.json or {}
    props = load('properties.json')
    max_order = max((p.get('order', 0) for p in props), default=0)
    entry = {'id': str(uuid.uuid4()), 'order': max_order + 1, 'sections': ['live_listings'], **data}
    props.append(entry)
    save('properties.json', props)
    return jsonify(entry), 201

@app.route('/api/listings/<lid>', methods=['PUT'])
@login_required
def update_listing(lid):
    data  = request.json or {}
    props = load('properties.json')
    for i, p in enumerate(props):
        if p['id'] == lid:
            props[i] = {**p, **data}
            break
    save('properties.json', props)
    return jsonify({'ok': True})

@app.route('/api/listings/<lid>', methods=['DELETE'])
@login_required
def delete_listing(lid):
    props = [p for p in load('properties.json') if p['id'] != lid]
    for i, p in enumerate(props):
        p['order'] = i + 1
    save('properties.json', props)
    return jsonify({'ok': True})


def build_city_listing_items(listings):
    """Return a full <section> of property cards for a city page, or '' if no listings."""
    if not listings:
        return ''
    cards = []
    for p in sorted(listings, key=lambda x: x.get('order', 999)):
        addr       = p.get('address', '')
        city       = p.get('city', 'Los Angeles')
        price      = p.get('price', '')
        rent       = p.get('rent', '')
        beds       = p.get('beds', '')
        baths      = p.get('baths', '')
        sqft       = p.get('sqft', '')
        status     = p.get('status', 'FOR SALE')
        img1       = p.get('image1', '')
        img2       = p.get('image2', '')
        detail_url = f'/property/{p["id"]}' if p.get('has_detail_page') else '/contact.html'

        card = [
            '                        <div role="listitem" class="property-grid-item w-dyn-item">',
            '                          <div class="property-link with-radius">',
            '                            <div class="property-image-grid">',
            f'                              <a href="{detail_url}" aria-label="Contact Ben" class="circle-button in-property-2 w-inline-block">',
            '                                <div class="ciricle-outline is-white"></div>'
            '<img loading="lazy" src="/images/arrow_right_white_24dp.svg" alt="Contact" class="ciricle-icon">',
            '                              </a>',
        ]
        if img1:
            card.append(f'                              <img alt="{addr}" loading="lazy" src="/{img1}" class="property-image is-1st">')
        if img2:
            card.append(f'                              <img alt="{addr}" loading="lazy" src="/{img2}" class="property-image is-2nd">')
        card += [
            '                            </div>',
            f'                            <a href="{detail_url}" class="property-inner w-inline-block">',
            f'                              <div class="property-address"><p class="property-address-title">{addr}, {city}</p></div>',
            '                            </a>',
            '                            <div class="property-details">',
            price_block_html(status, price, rent, '                              '),
            '                            </div>',
            '                            <div class="property-details">',
            '                              <div class="property-detail-block-3">',
        ]
        if beds:
            card.append(f'                                <div class="property-detail-amenity with-tooltip">'
                        f'<img alt="" loading="lazy" src="/images/bed_black_24dp.svg" class="property-detail-amenity-icon">'
                        f'<div>{beds}</div><p class="tooltip">Bedrooms</p></div>')
        if baths:
            card.append(f'                                <div class="property-detail-amenity with-tooltip">'
                        f'<img alt="" loading="lazy" src="/images/shower_black_24dp.svg" class="property-detail-amenity-icon">'
                        f'<div>{baths}</div><p class="tooltip">Bathrooms</p></div>')
        if sqft:
            card.append(f'                                <div class="property-detail-amenity with-tooltip">'
                        f'<img alt="" loading="lazy" src="/images/select_all_black_24dp.svg" class="property-detail-amenity-icon">'
                        f'<div>{sqft} sqft</div><p class="tooltip">Interior size</p></div>')
        card += [
            '                              </div>',
            '                            </div>',
            '                          </div>',
            '                        </div>',
        ]
        cards.append('\n'.join(card))

    cards_html = '\n'.join(cards)
    return (
        '      <section class="section white-border-bottom">\n'
        '        <div class="container w-container">\n'
        '          <div class="padding-8em">\n'
        '            <p class="city-section-label" style="text-align:center;">Active Listings</p>\n'
        '            <h2 class="heading-sellers-process" style="opacity:1;">Currently Listed in This Neighborhood</h2>\n'
        '            <div class="grid-listing-symbol" style="margin-top:2.5em;">\n'
        '              <div class="property-grid-2 current w-dyn-list">\n'
        '                <div role="list" class="property-grid-list-2 w-dyn-items">\n'
        f'{cards_html}\n'
        '                </div>\n'
        '              </div>\n'
        '            </div>\n'
        '          </div>\n'
        '        </div>\n'
        '      </section>'
    )


# ── Dynamic pages ──────────────────────────────────────────────────────────────
# These two pages are rendered live so admin edits are instant without redeploying.

@app.route('/neighborhoods')
@app.route('/neighborhoods.html')
def neighborhoods():
    path = os.path.join(BASE_DIR, 'neighborhoods.html')
    return open(path, encoding='utf-8').read()

@app.route('/cities')
@app.route('/cities.html')
def cities_redirect():
    return redirect('/neighborhoods', code=301)

@app.route('/cities/<slug>')
def city_page(slug):
    path = os.path.join(BASE_DIR, 'cities', f'{slug}.html')
    if not os.path.exists(path):
        return 'Not found', 404
    html = open(path, encoding='utf-8').read()
    city_listings = [
        p for p in load('properties.json')
        if slug in p.get('neighborhoods', [])
        and 'former_deals' not in p.get('sections', [])
    ]
    html = html.replace('<!-- CITY_LISTINGS_PLACEHOLDER -->', build_city_listing_items(city_listings))
    return Response(html, mimetype='text/html')

@app.route('/market-updates/<slug>')
def market_update(slug):
    path = os.path.join(BASE_DIR, 'market-updates', f'{slug}.html')
    if os.path.exists(path):
        return open(path, encoding='utf-8').read()
    return 'Not found', 404

@app.route('/blog')
@app.route('/blog.html')
def blog():
    q = request.args.get('q', '').strip()
    path = os.path.join(BASE_DIR, 'blog.html')
    text = open(path, encoding='utf-8').read()

    # Replace search bar (pre-fill value when query is present)
    bar_html = build_search_bar_html(q)
    text = re.sub(
        r'<!-- ADMIN:SEARCH_BAR:START -->.*?<!-- ADMIN:SEARCH_BAR:END -->',
        f'<!-- ADMIN:SEARCH_BAR:START -->\n{bar_html}\n<!-- ADMIN:SEARCH_BAR:END -->',
        text, flags=re.DOTALL
    )

    # Replace newsletter grid with search results or full archive
    if q:
        grid_html = build_search_results_html(q)
    else:
        grid_html = build_newsletter_sections(load('newsletters.json'))
    text = re.sub(
        r'<!-- ADMIN:NEWSLETTERS:START -->.*?<!-- ADMIN:NEWSLETTERS:END -->',
        f'<!-- ADMIN:NEWSLETTERS:START -->\n{grid_html}\n<!-- ADMIN:NEWSLETTERS:END -->',
        text, flags=re.DOTALL
    )

    return Response(text, mimetype='text/html')

@app.route('/current-listings')
@app.route('/current-listings.html')
def current_listings():
    return render_dynamic('current-listings.html', 'PROPERTIES',
                          build_property_items([p for p in load('properties.json') if 'built_by_ben' in p.get('sections', [])]))

@app.route('/for-buyers-3')
@app.route('/for-buyers-3.html')
def for_buyers():
    return render_dynamic('for-buyers-3.html', 'LISTINGS',
                          build_listing_items([p for p in load('properties.json') if 'live_listings' in p.get('sections', [])]))

@app.route('/deals')
@app.route('/deals.html')
def deals_page():
    former = [p for p in load('properties.json') if 'former_deals' in p.get('sections', [])]
    path   = os.path.join(BASE_DIR, 'deals.html')
    text   = open(path, encoding='utf-8').read()
    for marker, html in (
        ('DEALS',     build_deals_items(former)),
        ('DEALS_MAP', build_deals_map_html(former)),
    ):
        pat = rf'<!-- ADMIN:{re.escape(marker)}:START -->.*?<!-- ADMIN:{re.escape(marker)}:END -->'
        rep = f'<!-- ADMIN:{marker}:START -->\n{html}\n<!-- ADMIN:{marker}:END -->'
        text = re.sub(pat, lambda _: rep, text, flags=re.DOTALL)
    return Response(text, mimetype='text/html')

@app.route('/valuation')
@app.route('/valuation.html')
def valuation():
    path = os.path.join(BASE_DIR, 'valuation.html')
    return open(path, encoding='utf-8').read()

@app.route('/property/<prop_id>')
@app.route('/property/<prop_id>.html')
def property_detail(prop_id):
    props = load('properties.json')
    p = next((x for x in props if x['id'] == prop_id), None)
    if not p or not p.get('has_detail_page'):
        from flask import redirect
        return redirect('/contact.html')
    return Response(build_property_detail_html(p), mimetype='text/html')

# ── File serving — Volume takes priority over repo copies ──────────────────────

@app.route('/documents/<path:filename>')
def serve_document(filename):
    vol = os.path.join(VOL_DOCS_DIR, filename)
    if os.path.exists(vol):
        return send_from_directory(VOL_DOCS_DIR, filename)
    return send_from_directory(REPO_DOCS_DIR, filename)

@app.route('/images/<path:filename>')
def serve_image(filename):
    vol = os.path.join(VOL_IMGS_DIR, filename)
    if os.path.exists(vol):
        return send_from_directory(VOL_IMGS_DIR, filename)
    return send_from_directory(REPO_IMGS_DIR, filename)

# ── Admin UI ───────────────────────────────────────────────────────────────────

@app.route('/admin')
@app.route('/admin/')
def admin_ui():
    return ADMIN_HTML, 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/')
@app.route('/index.html')
def homepage():
    return render_dynamic('index.html', 'INDEX_LISTINGS',
                          build_index_listing_items([p for p in load('properties.json') if 'homepage' in p.get('sections', [])]))

# ── Contacts ──────────────────────────────────────────────────────────────────

_SOURCE_LABELS = {
    'contact':          'Contact Page',
    'contact-2':        'Contact Page (alt)',
    'tour':             'Property Tour Request',
    'valuation':        'Valuation Page',
    'current-listings': 'Current Listings Page',
    'for-sellers':      'For Sellers Page',
    'homepage':         'Homepage',
    'about':            'About Page',
    'sold-properties':  'Sold Properties',
    'for-buyers':       'For Buyers Page',
}

def _load_contacts():
    p = os.path.join(DATA_DIR, 'contacts.json')
    try:
        return json.load(open(p)) if os.path.exists(p) else []
    except Exception:
        return []

def _save_contacts(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, 'contacts.json')
    tmp  = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)

@app.route('/contact-submit', methods=['POST'])
def contact_submit():
    is_ajax = request.headers.get('X-Requested-With') == 'fetch'
    try:
        source = request.form.get('_source', 'contact')
        entry = {
            'id':           str(uuid.uuid4()),
            'timestamp':    datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
            'source':       source,
            'source_label': _SOURCE_LABELS.get(source, source),
            'name':         (request.form.get('Your-Name', '') + ' ' + request.form.get('Your-Surname', '')).strip(),
            'phone':        request.form.get('Your-Phone', ''),
            'email':        request.form.get('Your-Email', ''),
            'inquiry_type':      request.form.get('Inquiry-Type', request.form.get('Inquiry-type', '')),
            'message':           request.form.get('Message', ''),
            'property_address':  request.form.get('Property-Address', ''),
            'read':              False,
        }
        contacts = _load_contacts()
        contacts.insert(0, entry)
        _save_contacts(contacts)
    except Exception as e:
        print(f'[contact] save error: {e}', flush=True)
        if is_ajax:
            return jsonify({'ok': False}), 500
        return redirect('/contact.html')

    if is_ajax:
        return jsonify({'ok': True})
    return redirect('/contact-2.html' if source == 'contact-2' else '/contact.html')


@app.route('/api/contacts', methods=['GET'])
@login_required
def api_contacts_get():
    return jsonify(_load_contacts())

@app.route('/api/contacts/<cid>/read', methods=['PATCH'])
@login_required
def api_contacts_read(cid):
    contacts = _load_contacts()
    entry = next((c for c in contacts if c['id'] == cid), None)
    if not entry:
        return jsonify({'ok': False}), 404
    entry['read'] = (request.json or {}).get('read', True)
    _save_contacts(contacts)
    return jsonify({'ok': True})

@app.route('/api/contacts/read-all', methods=['PATCH'])
@login_required
def api_contacts_read_all():
    contacts = _load_contacts()
    for c in contacts:
        c['read'] = True
    _save_contacts(contacts)
    return jsonify({'ok': True})

@app.route('/api/contacts/<cid>', methods=['DELETE'])
@login_required
def api_contacts_delete(cid):
    _save_contacts([c for c in _load_contacts() if c['id'] != cid])
    return jsonify({'ok': True})


# ── Catch-all static ───────────────────────────────────────────────────────────

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(BASE_DIR, filename)


# ── Embedded Admin UI ──────────────────────────────────────────────────────────

ADMIN_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ben Lee Properties — Admin</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f0f2f5;color:#1a2332;min-height:100vh}

/* ── Login ── */
#login-screen{display:flex;align-items:center;justify-content:center;min-height:100vh;background:linear-gradient(135deg,#0a223f 0%,#13355f 100%)}
.login-card{background:#fff;border-radius:16px;padding:48px 40px;width:400px;box-shadow:0 24px 80px rgba(0,0,0,.35)}
.login-brand{font-size:10px;letter-spacing:3px;color:#be591f;font-weight:800;text-transform:uppercase;margin-bottom:6px}
.login-title{font-size:26px;font-weight:700;color:#0a223f;margin-bottom:6px}
.login-sub{font-size:13px;color:#8a9bb0;margin-bottom:32px}
.login-label{font-size:11px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:#4b5563;margin-bottom:6px;display:block}
.login-input{width:100%;padding:13px 16px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:15px;outline:none;transition:border-color .2s;margin-bottom:20px}
.login-input:focus{border-color:#0a223f}
.login-btn{width:100%;padding:14px;background:#0a223f;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:700;letter-spacing:.5px;cursor:pointer;transition:background .2s}
.login-btn:hover{background:#13355f}
.login-error{color:#dc2626;font-size:13px;margin-top:10px;display:none;text-align:center}

/* ── App shell ── */
#app{display:none;flex-direction:column;min-height:100vh}
.header{background:#0a223f;color:#fff;padding:0 28px;display:flex;align-items:center;height:60px;gap:20px;flex-shrink:0}
.header-brand{font-size:10px;letter-spacing:3px;font-weight:800;text-transform:uppercase;color:#be591f}
.header-sep{width:1px;height:20px;background:rgba(255,255,255,.15)}
.header-title{font-size:14px;font-weight:600;flex:1;color:rgba(255,255,255,.85)}
.logout-btn{background:none;border:1px solid rgba(255,255,255,.25);color:rgba(255,255,255,.8);padding:7px 14px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:600;letter-spacing:.3px;transition:all .2s}
.logout-btn:hover{background:rgba(255,255,255,.1);border-color:rgba(255,255,255,.4)}

/* ── Tabs ── */
.tabs{background:#fff;border-bottom:1px solid #e5e7eb;padding:0 28px;display:flex;gap:4px;flex-shrink:0}
.tab-btn{padding:15px 20px;border:none;background:none;cursor:pointer;font-size:13px;font-weight:700;color:#9ca3af;border-bottom:3px solid transparent;margin-bottom:-1px;transition:all .2s;letter-spacing:.3px}
.tab-btn.active{color:#0a223f;border-bottom-color:#be591f}
.tab-btn:hover:not(.active){color:#374151}

/* ── Main content ── */
.main{flex:1;padding:28px;max-width:1280px;margin:0 auto;width:100%}

/* ── Section header ── */
.section-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:24px}
.section-title{font-size:18px;font-weight:700;color:#0a223f}
.section-meta{font-size:13px;color:#9ca3af;margin-left:10px;font-weight:400}
.add-btn{display:flex;align-items:center;gap:8px;background:#0a223f;color:#fff;border:none;padding:10px 20px;border-radius:8px;font-size:13px;font-weight:700;letter-spacing:.3px;cursor:pointer;transition:background .2s}
.add-btn:hover{background:#13355f}
.add-btn svg{width:16px;height:16px}

/* ── Newsletter grid ── */
.nl-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:18px}
.nl-card{background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 6px rgba(0,0,0,.08);transition:box-shadow .2s;position:relative}
.nl-card:hover{box-shadow:0 4px 20px rgba(0,0,0,.12)}
.nl-cover{width:100%;aspect-ratio:8.5/11;object-fit:cover;display:block;background:#f5f6f8}
.nl-cover-placeholder{width:100%;aspect-ratio:8.5/11;background:#f5f6f8;display:flex;align-items:center;justify-content:center;color:#c0c9d4;font-size:12px;flex-direction:column;gap:8px}
.nl-cover-placeholder svg{width:32px;height:32px;opacity:.4}
.nl-body{padding:14px}
.nl-label{font-size:14px;font-weight:700;color:#0a223f;margin-bottom:4px}
.nl-pdf-name{font-size:11px;color:#9ca3af;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:12px}
.nl-actions{display:flex;gap:8px}
.nl-btn{flex:1;padding:7px 6px;border:none;border-radius:6px;font-size:11px;font-weight:700;cursor:pointer;transition:background .2s;letter-spacing:.3px}
.nl-btn-view{background:#f0f4f8;color:#374151}
.nl-btn-view:hover{background:#e2e8f0}
.nl-btn-delete{background:#fef2f2;color:#dc2626}
.nl-btn-delete:hover{background:#fee2e2}
.badge-feat{position:absolute;top:10px;left:10px;background:#be591f;color:#fff;font-size:9px;font-weight:800;letter-spacing:1.5px;padding:4px 9px;border-radius:4px;text-transform:uppercase}

/* ── Properties table ── */
.prop-table{background:#fff;border-radius:12px;box-shadow:0 1px 6px rgba(0,0,0,.08);overflow:hidden}
.prop-thead{display:grid;grid-template-columns:2.2fr 1.2fr 1fr 1fr 1.1fr 80px;gap:12px;padding:12px 20px;background:#f9fafb;border-bottom:1px solid #e5e7eb;font-size:10px;font-weight:800;letter-spacing:1px;color:#9ca3af;text-transform:uppercase}
.prop-row{display:grid;grid-template-columns:2.2fr 1.2fr 1fr 1fr 1.1fr 80px;gap:12px;padding:15px 20px;border-bottom:1px solid #f3f4f6;align-items:center;transition:background .15s}
.prop-row:last-child{border-bottom:none}
.prop-row:hover{background:#fafbfc}
.prop-addr{font-weight:700;color:#0a223f;font-size:14px;line-height:1.3}
.prop-city{font-size:12px;color:#9ca3af;margin-top:2px}
.prop-price{font-size:13px;font-weight:700;color:#0a223f}
.prop-detail{font-size:13px;color:#4b5563}
.status-badge{display:inline-block;padding:4px 10px;border-radius:20px;font-size:10px;font-weight:800;letter-spacing:.5px;text-transform:uppercase}
.s-sale{background:#dcfce7;color:#15803d}
.s-lease{background:#dbeafe;color:#1d4ed8}
.s-both{background:#fef3c7;color:#92400e}
.s-sold{background:#fef2f2;color:#dc2626}
.row-actions{display:flex;gap:6px;justify-content:flex-end}
.icon-btn{width:32px;height:32px;border:none;border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .2s;flex-shrink:0}
.icon-btn svg{width:15px;height:15px}
.btn-edit{background:#f0f9ff;color:#0369a1}
.btn-edit:hover{background:#e0f2fe}
.btn-del{background:#fef2f2;color:#dc2626}
.btn-del:hover{background:#fee2e2}

/* ── Modal ── */
.modal-overlay{position:fixed;inset:0;background:rgba(10,34,63,.5);display:flex;align-items:center;justify-content:center;z-index:100;backdrop-filter:blur(3px)}
.modal{background:#fff;border-radius:16px;width:100%;max-width:580px;max-height:92vh;overflow-y:auto;box-shadow:0 30px 100px rgba(0,0,0,.35)}
.modal-hd{padding:22px 26px 18px;border-bottom:1px solid #f3f4f6;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;background:#fff;z-index:1;border-radius:16px 16px 0 0}
.modal-title{font-size:17px;font-weight:700;color:#0a223f}
.modal-close{width:30px;height:30px;border:none;background:#f5f6f8;border-radius:7px;cursor:pointer;color:#6b7280;display:flex;align-items:center;justify-content:center;font-size:16px;transition:background .2s}
.modal-close:hover{background:#e5e7eb}
.modal-body{padding:22px 26px}
.modal-ft{padding:14px 26px 22px;display:flex;gap:10px;justify-content:flex-end}

/* ── Form ── */
.frow{margin-bottom:16px}
.frow-2{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:16px}
.frow-3{display:grid;grid-template-columns:2fr 1fr 1fr;gap:14px;margin-bottom:16px}
label{display:block;font-size:11px;font-weight:700;color:#4b5563;letter-spacing:.5px;text-transform:uppercase;margin-bottom:6px}
input[type=text],input[type=number],select,textarea{width:100%;padding:10px 13px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:14px;color:#1a2332;outline:none;transition:border-color .2s;background:#fff;font-family:inherit}
input:focus,select:focus,textarea:focus{border-color:#0a223f}
.hint{font-size:11px;color:#9ca3af;margin-top:4px}

/* ── Drop zone ── */
.dropzone{border:2px dashed #d1d5db;border-radius:10px;padding:24px 16px;text-align:center;cursor:pointer;transition:all .2s;position:relative;overflow:hidden}
.dropzone:hover,.dropzone.over{border-color:#0a223f;background:#f0f4f8}
.dropzone input{position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%}
.dz-icon{font-size:24px;margin-bottom:6px}
.dz-text{font-size:12px;color:#9ca3af}
.dz-text strong{color:#0a223f}
.dz-file{margin-top:8px;font-size:12px;color:#0369a1;font-weight:600;min-height:16px}

/* ── Buttons ── */
.btn-primary{background:#0a223f;color:#fff;border:none;padding:10px 22px;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer;transition:background .2s}
.btn-primary:hover{background:#13355f}
.btn-secondary{background:#f5f6f8;color:#374151;border:none;padding:10px 22px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;transition:background .2s}
.btn-secondary:hover{background:#e5e7eb}

/* ── Empty state ── */
.empty{text-align:center;padding:60px 20px;color:#c0c9d4}
.empty svg{width:48px;height:48px;margin-bottom:12px;opacity:.4}
.empty p{font-size:14px}

/* ── Toast ── */
.toast{position:fixed;bottom:24px;right:24px;background:#0a223f;color:#fff;padding:13px 20px;border-radius:10px;font-size:14px;font-weight:600;z-index:999;transform:translateY(80px);opacity:0;transition:all .3s cubic-bezier(.175,.885,.32,1.275);box-shadow:0 8px 32px rgba(0,0,0,.25);pointer-events:none}
.toast.show{transform:translateY(0);opacity:1}
.toast.err{background:#dc2626}

.tab-pane{display:none}
.tab-pane.active{display:block}

/* ── Inbox ── */
.inbox-badge{display:inline-flex;align-items:center;justify-content:center;background:#dc2626;color:#fff;font-size:10px;font-weight:700;min-width:17px;height:17px;border-radius:99px;padding:0 4px;margin-left:6px;vertical-align:middle;line-height:1}
.inbox-list-wrap{display:flex;flex-direction:column;gap:10px}
.inbox-empty{text-align:center;padding:60px 20px;color:#9ca3af;font-size:14px}
.inbox-card{background:#fff;border:1.5px solid #e5e9f0;border-radius:10px;overflow:hidden;transition:border-color .15s}
.inbox-card.is-unread{border-color:#3b5fc0;background:#f5f8ff}
.inbox-card-hd{display:flex;align-items:center;gap:12px;padding:14px 18px;cursor:pointer;user-select:none}
.inbox-dot{width:9px;height:9px;border-radius:50%;background:#3b5fc0;flex-shrink:0}
.inbox-card.is-read .inbox-dot{background:#d1d5db}
.inbox-from{font-weight:700;font-size:14px;color:#0a223f;flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.inbox-chip{background:#e8edf7;color:#3b5fc0;font-size:10px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;padding:2px 8px;border-radius:99px;flex-shrink:0}
.inbox-ts{font-size:12px;color:#9ca3af;white-space:nowrap;flex-shrink:0}
.inbox-card-body{display:none;padding:4px 18px 16px;border-top:1px solid #e5e9f0}
.inbox-card.is-open .inbox-card-body{display:block}
.inbox-field{margin-top:10px;font-size:13px;color:#374151;line-height:1.6}
.inbox-field strong{display:block;font-size:10px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:#9ca3af;margin-bottom:2px}
.inbox-field a{color:#3b5fc0;text-decoration:none}
.inbox-card-actions{display:flex;gap:8px;margin-top:14px}
.inbox-act-btn{padding:5px 14px;border-radius:6px;font-size:12px;font-weight:600;border:none;cursor:pointer}
.inbox-act-read{background:#eef2ff;color:#3b5fc0}
.inbox-act-del{background:#fef2f2;color:#dc2626}
</style>
</head>
<body>

<!-- ════════ LOGIN ════════ -->
<div id="login-screen">
  <div class="login-card">
    <div class="login-brand">Ben Lee Properties</div>
    <div class="login-title">Admin Panel</div>
    <div class="login-sub">Sign in to manage newsletters and listings</div>
    <form id="login-form">
      <label class="login-label" for="login-pw">Password</label>
      <input id="login-pw" class="login-input" type="password" placeholder="Enter admin password" autocomplete="current-password">
      <button class="login-btn" type="submit">Sign In</button>
      <div id="login-error" class="login-error">Incorrect password — try again.</div>
    </form>
  </div>
</div>

<!-- ════════ APP ════════ -->
<div id="app">
  <div class="header">
    <span class="header-brand">Ben Lee Properties</span>
    <div class="header-sep"></div>
    <span class="header-title">Content Admin</span>
    <button class="logout-btn" id="logout-btn">Sign Out</button>
  </div>

  <div class="tabs">
    <button class="tab-btn active" data-tab="newsletters">Newsletters</button>
    <button class="tab-btn" data-tab="properties">Properties</button>
    <button class="tab-btn" data-tab="inbox">Inbox <span id="inbox-badge" class="inbox-badge" style="display:none"></span></button>
  </div>

  <div class="main">
    <!-- Newsletters tab -->
    <div id="tab-newsletters" class="tab-pane active">
      <div class="section-header">
        <div>
          <span class="section-title">Newsletters</span>
          <span class="section-meta" id="nl-count"></span>
        </div>
        <div style="display:flex;gap:8px">
          <button class="btn-secondary" id="sync-covers-btn" style="font-size:12px;padding:6px 12px">Sync Covers</button>
          <button class="add-btn" id="add-nl-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            Add Newsletter
          </button>
        </div>
      </div>
      <div id="nl-grid" class="nl-grid"></div>
    </div>

    <!-- Properties tab -->
    <div id="tab-properties" class="tab-pane">
      <div class="section-header">
        <div>
          <span class="section-title">Properties</span>
          <span class="section-meta" id="prop-count"></span>
        </div>
        <button class="add-btn" id="add-prop-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          Add Property
        </button>
      </div>
      <div id="prop-table" class="prop-table"></div>
    </div>

    <!-- Inbox tab -->
    <div id="tab-inbox" class="tab-pane">
      <div class="section-header">
        <div>
          <span class="section-title">Inbox</span>
          <span class="section-meta" id="inbox-count"></span>
        </div>
        <button class="btn-secondary" id="mark-all-btn" style="font-size:12px;padding:6px 14px">Mark all read</button>
      </div>
      <div id="inbox-list" class="inbox-list-wrap"></div>
    </div>
  </div>
</div>

<!-- ════════ NEWSLETTER MODAL ════════ -->
<div id="nl-modal" class="modal-overlay" style="display:none">
  <div class="modal">
    <div class="modal-hd">
      <span class="modal-title">Add Newsletter</span>
      <button class="modal-close" id="close-nl-modal">✕</button>
    </div>
    <div class="modal-body">
      <form id="nl-form" enctype="multipart/form-data">
        <div class="frow-2">
          <div>
            <label for="nl-month">Month <span style="color:#dc2626">*</span></label>
            <select id="nl-month" name="month" required>
              <option value="1">January</option><option value="2">February</option>
              <option value="3">March</option><option value="4">April</option>
              <option value="5">May</option><option value="6">June</option>
              <option value="7">July</option><option value="8">August</option>
              <option value="9">September</option><option value="10">October</option>
              <option value="11">November</option><option value="12">December</option>
            </select>
          </div>
          <div>
            <label for="nl-year">Year <span style="color:#dc2626">*</span></label>
            <select id="nl-year" name="year" required></select>
          </div>
        </div>

        <div class="frow">
          <label>Newsletter PDF <span style="color:#dc2626">*</span></label>
          <div class="dropzone" id="dz-pdf">
            <input type="file" name="pdf" id="nl-pdf" accept=".pdf">
            <div class="dz-icon">📄</div>
            <div class="dz-text">Drop PDF here or <strong>click to browse</strong></div>
            <div class="dz-file" id="pdf-file-name"></div>
          </div>
          <div class="hint">Cover image is automatically extracted from the first page of the PDF.</div>
        </div>
      </form>
    </div>
    <div class="modal-ft">
      <button class="btn-secondary" id="cancel-nl">Cancel</button>
      <button class="btn-primary" id="save-nl">Save &amp; Publish</button>
    </div>
  </div>
</div>

<!-- ════════ PROPERTY MODAL ════════ -->
<div id="prop-modal" class="modal-overlay" style="display:none">
  <div class="modal">
    <div class="modal-hd">
      <span class="modal-title" id="prop-modal-title">Add Property</span>
      <button class="modal-close" id="close-prop-modal">✕</button>
    </div>
    <div class="modal-body">
      <form id="prop-form">
        <div class="frow">
          <label for="p-address">Street Address <span style="color:#dc2626">*</span></label>
          <input id="p-address" type="text" placeholder="e.g. 123 Maple Dr" required>
        </div>
        <div class="frow-3">
          <div>
            <label for="p-city">City</label>
            <input id="p-city" type="text" placeholder="Los Angeles">
          </div>
          <div>
            <label for="p-state">State</label>
            <input id="p-state" type="text" placeholder="CA" maxlength="2">
          </div>
          <div>
            <label for="p-status">Status</label>
            <select id="p-status">
              <option>FOR SALE</option>
              <option>FOR LEASE</option>
              <option>FOR SALE / LEASE</option>
              <option>SOLD</option>
            </select>
          </div>
        </div>
        <div class="frow-2">
          <div id="p-price-wrap">
            <label for="p-price" id="p-price-label">Sale Price</label>
            <input id="p-price" type="text" placeholder="4,825,000">
            <div class="hint">Numbers only, no $ sign (e.g. 4,825,000)</div>
          </div>
          <div id="p-rent-wrap">
            <label for="p-rent">Monthly Rent</label>
            <input id="p-rent" type="text" placeholder="20,500">
            <div class="hint">Numbers only, no $ sign (e.g. 20,500)</div>
          </div>
        </div>
        <div class="frow-3">
          <div>
            <label for="p-beds">Bedrooms</label>
            <input id="p-beds" type="text" placeholder="5">
          </div>
          <div>
            <label for="p-baths">Bathrooms</label>
            <input id="p-baths" type="text" placeholder="7">
          </div>
          <div>
            <label for="p-sqft">Square Feet</label>
            <input id="p-sqft" type="text" placeholder="5,900">
          </div>
        </div>
        <div class="frow">
          <label>Primary Photo <span style="color:#dc2626">*</span></label>
          <div class="dropzone" id="dz-p-img1">
            <input type="file" id="p-img1-file" accept="image/*">
            <div class="dz-icon">📷</div>
            <div class="dz-text">Drop photo here or <strong>click to browse</strong></div>
          </div>
          <div id="p-img1-preview" style="margin-top:10px;min-height:20px"></div>
          <input type="hidden" id="p-image1">
        </div>
        <div class="frow">
          <label>Secondary Photo <span style="color:#9ca3af;font-weight:500;text-transform:none;letter-spacing:0">(optional — shows on hover)</span></label>
          <div class="dropzone" id="dz-p-img2">
            <input type="file" id="p-img2-file" accept="image/*">
            <div class="dz-icon">📷</div>
            <div class="dz-text">Drop photo here or <strong>click to browse</strong></div>
          </div>
          <div id="p-img2-preview" style="margin-top:10px;min-height:20px"></div>
          <input type="hidden" id="p-image2">
        </div>
        <div class="frow">
          <label>Additional Photos <span style="color:#9ca3af;font-weight:500;text-transform:none;letter-spacing:0">(optional — for detail page gallery)</span></label>
          <div id="p-extra-imgs"></div>
          <button type="button" onclick="addPhotoSlot()" style="margin-top:8px;background:#f0f4ff;border:1.5px dashed #c7d6f5;border-radius:8px;padding:10px 18px;color:#07264b;font-size:13px;font-weight:700;cursor:pointer;width:100%">+ Add Photo</button>
          <div class="hint" style="margin-top:6px">Up to 20 photos total (including primary and secondary).</div>
        </div>
        <div class="frow">
          <label>Property Description <span style="color:#9ca3af;font-weight:500;text-transform:none;letter-spacing:0">(for detail page)</span></label>
          <textarea id="p-desc" rows="5" placeholder="Describe the property for the detail page..."></textarea>
        </div>
        <div class="frow" style="margin-top:4px">
          <label>Display on Site <span style="color:#dc2626">*</span></label>
          <div style="display:flex;gap:1.8em;flex-wrap:wrap;margin-top:6px">
            <label style="display:flex;align-items:center;gap:8px;font-size:13px;font-weight:500;cursor:pointer;color:#374151">
              <input type="checkbox" id="p-section-live" style="width:16px;height:16px;cursor:pointer;accent-color:#07264b"> Live Listings
            </label>
            <label style="display:flex;align-items:center;gap:8px;font-size:13px;font-weight:500;cursor:pointer;color:#374151">
              <input type="checkbox" id="p-section-bbb" style="width:16px;height:16px;cursor:pointer;accent-color:#07264b"> Built by Ben
            </label>
            <label style="display:flex;align-items:center;gap:8px;font-size:13px;font-weight:500;cursor:pointer;color:#374151">
              <input type="checkbox" id="p-section-home" style="width:16px;height:16px;cursor:pointer;accent-color:#be591f"> Homepage
            </label>
            <label style="display:flex;align-items:center;gap:8px;font-size:13px;font-weight:500;cursor:pointer;color:#374151">
              <input type="checkbox" id="p-section-deals" style="width:16px;height:16px;cursor:pointer;accent-color:#ed2227"> Former Deals
            </label>
          </div>
          <div class="hint">Controls which pages this property appears on. Homepage shows it in the featured section on the front page.</div>
        </div>
        <div class="frow" style="margin-top:4px">
          <label>City Pages <span style="color:#9ca3af;font-weight:500;text-transform:none;letter-spacing:0">(optional)</span></label>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px 1.8em;margin-top:6px">
            <label style="display:flex;align-items:center;gap:8px;font-size:13px;font-weight:500;cursor:pointer;color:#374151">
              <input type="checkbox" id="p-nbhd-cheviot-hills" style="width:16px;height:16px;cursor:pointer;accent-color:#be591f"> Cheviot Hills
            </label>
            <label style="display:flex;align-items:center;gap:8px;font-size:13px;font-weight:500;cursor:pointer;color:#374151">
              <input type="checkbox" id="p-nbhd-beverlywood" style="width:16px;height:16px;cursor:pointer;accent-color:#be591f"> Beverlywood
            </label>
            <label style="display:flex;align-items:center;gap:8px;font-size:13px;font-weight:500;cursor:pointer;color:#374151">
              <input type="checkbox" id="p-nbhd-beverly-hills" style="width:16px;height:16px;cursor:pointer;accent-color:#be591f"> Beverly Hills
            </label>
            <label style="display:flex;align-items:center;gap:8px;font-size:13px;font-weight:500;cursor:pointer;color:#374151">
              <input type="checkbox" id="p-nbhd-westwood" style="width:16px;height:16px;cursor:pointer;accent-color:#be591f"> Westwood
            </label>
            <label style="display:flex;align-items:center;gap:8px;font-size:13px;font-weight:500;cursor:pointer;color:#374151">
              <input type="checkbox" id="p-nbhd-bel-air" style="width:16px;height:16px;cursor:pointer;accent-color:#be591f"> Bel Air
            </label>
            <label style="display:flex;align-items:center;gap:8px;font-size:13px;font-weight:500;cursor:pointer;color:#374151">
              <input type="checkbox" id="p-nbhd-brentwood" style="width:16px;height:16px;cursor:pointer;accent-color:#be591f"> Brentwood
            </label>
            <label style="display:flex;align-items:center;gap:8px;font-size:13px;font-weight:500;cursor:pointer;color:#374151">
              <input type="checkbox" id="p-nbhd-santa-monica" style="width:16px;height:16px;cursor:pointer;accent-color:#be591f"> Santa Monica
            </label>
          </div>
          <div class="hint">Also show this listing on specific neighborhood pages. A property can appear on multiple city pages.</div>
        </div>
        <div class="frow" style="background:#f0f4ff;border-radius:6px;padding:14px 16px;border:1px solid #c7d6f5;margin-top:4px">
          <label style="display:flex;align-items:center;gap:10px;cursor:pointer;font-size:13px;font-weight:700;color:#07264b;letter-spacing:.04em;text-transform:uppercase">
            <input type="checkbox" id="p-has-detail" style="width:17px;height:17px;cursor:pointer;accent-color:#07264b">
            Enable Detail Page
          </label>
          <div class="hint" style="margin-top:6px">When enabled, clicking this property card opens a dedicated detail page instead of the contact form.</div>
        </div>
      </form>
    </div>
    <div class="modal-ft">
      <button class="btn-secondary" id="cancel-prop">Cancel</button>
      <button type="button" id="move-to-deals-btn" style="padding:0.55em 1.2em;background:#0a223f;color:#fff;border:none;border-radius:4px;font-family:Montserrat,sans-serif;font-size:0.8em;font-weight:600;cursor:pointer;letter-spacing:.05em">MOVE TO DEALS</button>
      <button class="btn-primary" id="save-prop">Save &amp; Publish</button>
    </div>
  </div>
</div>

<!-- Toast -->
<div id="toast" class="toast"></div>

<script>
// ── Utils ──────────────────────────────────────────────────────────────────────
const $ = (s, ctx) => (ctx || document).querySelector(s);
const $$ = (s, ctx) => [...(ctx || document).querySelectorAll(s)];

async function api(method, path, body, isForm) {
  const opts = { method, credentials: 'same-origin', headers: {} };
  if (body) {
    if (isForm) { opts.body = body; }
    else { opts.body = JSON.stringify(body); opts.headers['Content-Type'] = 'application/json'; }
  }
  try {
    const res = await fetch(path, opts);
    if (res.status === 401) { showLogin(); return null; }
    return await res.json();
  } catch(e) {
    toast('Network error', true);
    return null;
  }
}

let toastTimer;
function toast(msg, err) {
  const t = $('#toast');
  t.textContent = msg;
  t.className = 'toast' + (err ? ' err' : '');
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 3200);
}

// ── Auth ───────────────────────────────────────────────────────────────────────
async function init() {
  const r = await fetch('/admin/check', { credentials: 'same-origin' });
  const d = await r.json();
  if (d.loggedIn) showApp();
  else showLogin();
}

function showLogin() {
  $('#login-screen').style.display = 'flex';
  $('#app').style.display = 'none';
}

function showApp() {
  $('#login-screen').style.display = 'none';
  $('#app').style.display = 'flex';
  loadNewsletters();
  loadProperties();
  loadInboxBadge();
}

$('#login-form').addEventListener('submit', async e => {
  e.preventDefault();
  const r = await fetch('/admin/login', {
    method: 'POST', credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password: $('#login-pw').value })
  });
  const d = await r.json();
  if (d.ok) showApp();
  else {
    $('#login-error').style.display = 'block';
    $('#login-pw').value = '';
    $('#login-pw').focus();
  }
});

$('#logout-btn').addEventListener('click', async () => {
  await fetch('/admin/logout', { method: 'POST', credentials: 'same-origin' });
  showLogin();
});

// ── Tabs ───────────────────────────────────────────────────────────────────────
$$('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    $$('.tab-btn').forEach(b => b.classList.remove('active'));
    $$('.tab-pane').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    $('#tab-' + btn.dataset.tab).classList.add('active');
    if (btn.dataset.tab === 'newsletters') loadNewsletters();
    else if (btn.dataset.tab === 'inbox') loadInbox();
    else loadProperties();
  });
});

// ── Newsletters ────────────────────────────────────────────────────────────────
let newsletters = [];

async function loadNewsletters() {
  newsletters = await api('GET', '/api/newsletters') || [];
  newsletters.sort((a, b) => b.year !== a.year ? b.year - a.year : b.month - a.month);
  renderNewsletters();
}

function renderNewsletters() {
  $('#nl-count').textContent = `· ${newsletters.length} total`;
  const grid = $('#nl-grid');
  if (!newsletters.length) {
    grid.innerHTML = `<div class="empty" style="grid-column:1/-1">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
      <p>No newsletters yet — add the first one above.</p></div>`;
    return;
  }
  grid.innerHTML = newsletters.map((n, i) => `
    <div class="nl-card">
      ${i === 0 ? '<div class="badge-feat">Featured</div>' : ''}
      ${n.cover
        ? `<img class="nl-cover" src="/${n.cover}" alt="${n.label}" loading="lazy">`
        : `<div class="nl-cover-placeholder">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
            No cover image
           </div>`}
      <div class="nl-body">
        <div class="nl-label">${n.label}</div>
        <div class="nl-pdf-name">${n.pdf ? n.pdf.split('/').pop() : 'No PDF linked'}</div>
        <div class="nl-actions">
          ${n.pdf ? `<button class="nl-btn nl-btn-view" onclick="window.open('/${n.pdf}','_blank')">View PDF</button>` : '<button class="nl-btn nl-btn-view" disabled style="opacity:.4">No PDF</button>'}
          <button class="nl-btn nl-btn-delete" onclick="deleteNewsletter('${n.id}','${n.label}')">Delete</button>
        </div>
      </div>
    </div>`).join('');
}

function deleteNewsletter(id, label) {
  if (!confirm(`Delete "${label}"?\n\nThis will remove it from the website immediately. The PDF file on disk will not be deleted.`)) return;
  api('DELETE', `/api/newsletters/${id}`).then(r => {
    if (r && r.ok) { toast('Newsletter deleted — site updated'); loadNewsletters(); }
    else toast('Failed to delete', true);
  });
}

// Newsletter modal
$('#sync-covers-btn').addEventListener('click', async () => {
  const btn = $('#sync-covers-btn');
  btn.textContent = 'Syncing…';
  btn.disabled = true;
  const r = await api('POST', '/api/newsletters/sync-covers');
  btn.textContent = 'Sync Covers';
  btn.disabled = false;
  if (r && r.ok) {
    toast(`Covers synced — ${r.updated} updated`);
    loadNewsletters();
  } else {
    toast('Sync failed', true);
  }
});

$('#add-nl-btn').addEventListener('click', () => {
  $('#nl-form').reset();
  $('#pdf-file-name').textContent = '';
  const now = new Date();
  $('#nl-month').value = now.getMonth() + 1;
  populateYears(now.getFullYear());
  $('#nl-modal').style.display = 'flex';
});

function populateYears(current) {
  const sel = $('#nl-year');
  sel.innerHTML = '';
  for (let y = current + 1; y >= 2012; y--) {
    const opt = document.createElement('option');
    opt.value = y;
    opt.textContent = y;
    if (y === current) opt.selected = true;
    sel.appendChild(opt);
  }
}

function closeNlModal() { $('#nl-modal').style.display = 'none'; }
$('#close-nl-modal').addEventListener('click', closeNlModal);
$('#cancel-nl').addEventListener('click', closeNlModal);
$('#nl-modal').addEventListener('click', e => { if (e.target === $('#nl-modal')) closeNlModal(); });

// Drag & drop file zones
function setupDZ(dzId, inputId, previewId) {
  const dz = $('#' + dzId), input = $('#' + inputId), preview = $('#' + previewId);
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('over'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('over'));
  dz.addEventListener('drop', e => {
    e.preventDefault(); dz.classList.remove('over');
    if (e.dataTransfer.files.length) {
      const dt = e.dataTransfer;
      // Clone the file list onto the input via a DataTransfer trick
      try {
        const transfer = new DataTransfer();
        transfer.items.add(dt.files[0]);
        input.files = transfer.files;
      } catch(_) {}
      preview.textContent = '✓ ' + dt.files[0].name;
    }
  });
  input.addEventListener('change', () => {
    preview.textContent = input.files.length ? '✓ ' + input.files[0].name : '';
  });
}

setupDZ('dz-pdf', 'nl-pdf', 'pdf-file-name');

$('#save-nl').addEventListener('click', async () => {
  const form = $('#nl-form');
  if (!form.checkValidity()) { form.reportValidity(); return; }
  if (!$('#nl-pdf').files.length) { toast('Please select a PDF file', true); return; }

  const fd = new FormData(form);
  const btn = $('#save-nl');
  btn.textContent = 'Uploading & extracting cover…';
  btn.disabled = true;

  const r = await api('POST', '/api/newsletters', fd, true);
  btn.textContent = 'Save & Publish';
  btn.disabled = false;

  if (r && r.id) {
    toast('Newsletter added — site updated! ✓');
    closeNlModal();
    loadNewsletters();
  } else {
    toast('Error saving newsletter', true);
  }
});

// ── Properties ─────────────────────────────────────────────────────────────────
const CITY_SLUGS = ['cheviot-hills','beverlywood','beverly-hills','westwood','bel-air','brentwood','santa-monica'];
let properties = [];
let editingPropId = null;

async function loadProperties() {
  properties = await api('GET', '/api/properties') || [];
  properties.sort((a, b) => (a.order || 0) - (b.order || 0));
  renderProperties();
}

function statusBadge(status) {
  const s = (status || '').toUpperCase();
  if (s === 'SOLD') return `<span class="status-badge s-sold">Sold</span>`;
  if (s.includes('SALE') && s.includes('LEASE')) return `<span class="status-badge s-both">Sale / Lease</span>`;
  if (s.includes('LEASE')) return `<span class="status-badge s-lease">For Lease</span>`;
  return `<span class="status-badge s-sale">For Sale</span>`;
}

function renderProperties() {
  $('#prop-count').textContent = `· ${properties.length} total`;
  const table = $('#prop-table');
  if (!properties.length) {
    table.innerHTML = `<div class="empty">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
      <p>No properties yet — add the first one above.</p></div>`;
    return;
  }
  table.innerHTML = `
    <div class="prop-thead">
      <div>Property</div><div>Price</div><div>Beds / Baths</div><div>Sqft</div><div>Status</div><div></div>
    </div>
    ${properties.map(p => `
      <div class="prop-row">
        <div>
          <div class="prop-addr">${p.address || '—'}</div>
          <div class="prop-city">${p.city || 'Los Angeles'}, ${p.state || 'CA'}</div>
          <div style="margin-top:5px">
            ${(p.sections||[]).includes('live_listings') ? '<span style="display:inline-block;font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;background:#059669;color:#fff;padding:1px 7px;border-radius:2em;margin-right:4px">Live</span>' : ''}
            ${(p.sections||[]).includes('built_by_ben') ? '<span style="display:inline-block;font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;background:#07264b;color:#fff;padding:1px 7px;border-radius:2em;margin-right:4px">Built by Ben</span>' : ''}
            ${(p.sections||[]).includes('homepage') ? '<span style="display:inline-block;font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;background:#be591f;color:#fff;padding:1px 7px;border-radius:2em;margin-right:4px">Homepage</span>' : ''}
            ${(p.sections||[]).includes('former_deals') ? '<span style="display:inline-block;font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;background:#ed2227;color:#fff;padding:1px 7px;border-radius:2em;margin-right:4px">Deals</span>' : ''}
            ${p.has_detail_page ? '<span style="display:inline-block;font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;background:#7c3aed;color:#fff;padding:1px 7px;border-radius:2em;margin-right:4px">Detail Page</span>' : ''}
            ${(p.neighborhoods||[]).length ? `<span style="display:inline-block;font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;background:#0891b2;color:#fff;padding:1px 7px;border-radius:2em">${p.neighborhoods.length} City Page${p.neighborhoods.length>1?'s':''}</span>` : ''}
            ${!p.image1 ? '<span style="display:inline-block;font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;background:#f59e0b;color:#fff;padding:1px 7px;border-radius:2em;margin-right:4px" title="No image uploaded">⚠ No Image</span>' : ''}
            ${(!p.description || p.description.trim().length < 30 || ['details','tbd','n/a','none','description'].includes(p.description.trim().toLowerCase())) ? '<span style="display:inline-block;font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;background:#f59e0b;color:#fff;padding:1px 7px;border-radius:2em" title="Description missing or too short">⚠ No Description</span>' : ''}
          </div>
        </div>
        <div class="prop-price">${p.price ? '$' + p.price : '—'}${p.rent && p.status !== 'SOLD' ? '<br><span style="font-size:11px;color:#9ca3af;font-weight:500">$' + p.rent + ' /mo</span>' : ''}</div>
        <div class="prop-detail">${p.beds || '—'} bd &nbsp;/&nbsp; ${p.baths || '—'} ba</div>
        <div class="prop-detail">${p.sqft ? p.sqft + ' sqft' : '—'}</div>
        <div>${statusBadge(p.status)}</div>
        <div class="row-actions">
          <button class="icon-btn btn-edit" onclick="openEditProp('${p.id}')" title="Edit">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          </button>
          <button class="icon-btn btn-del" onclick="deleteProp('${p.id}','${(p.address||'').replace(/'/g,"\\'")}')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/></svg>
          </button>
        </div>
      </div>`).join('')}`;
}

function openEditProp(id) {
  const p = properties.find(x => x.id === id);
  if (!p) return;
  editingPropId = id;
  $('#prop-modal-title').textContent = 'Edit Property';
  $('#p-address').value  = p.address  || '';
  $('#p-city').value     = p.city     || 'Los Angeles';
  $('#p-state').value    = p.state    || 'CA';
  $('#p-price').value    = p.price    || '';
  $('#p-rent').value     = p.rent     || '';
  $('#p-beds').value     = p.beds     || '';
  $('#p-baths').value    = p.baths    || '';
  $('#p-sqft').value     = p.sqft     || '';
  $('#p-status').value   = p.status   || 'FOR SALE';
  $('#p-image1').value = p.image1 || '';
  $('#p-image2').value = p.image2 || '';
  showImgPreview('p-img1-preview', p.image1);
  showImgPreview('p-img2-preview', p.image2);
  clearExtraImgs();
  for (let i = 3; i <= 20; i++) {
    const val = p[`image${i}`] || '';
    if (val) addPhotoSlot(val);
  }
  $('#p-desc').value   = p.description || '';
  $('#p-has-detail').checked = !!p.has_detail_page;
  $('#p-section-live').checked  = (p.sections || []).includes('live_listings');
  $('#p-section-bbb').checked   = (p.sections || []).includes('built_by_ben');
  $('#p-section-home').checked  = (p.sections || []).includes('homepage');
  $('#p-section-deals').checked = (p.sections || []).includes('former_deals');
  CITY_SLUGS.forEach(slug => {
    const el = $(`#p-nbhd-${slug}`);
    if (el) el.checked = (p.neighborhoods || []).includes(slug);
  });
  syncPriceFields();
  $('#prop-modal').style.display = 'flex';
  setTimeout(() => $('#p-address').focus(), 80);
}

$('#add-prop-btn').addEventListener('click', () => {
  editingPropId = null;
  $('#prop-modal-title').textContent = 'Add Property';
  $('#prop-form').reset();
  $('#p-city').value = 'Los Angeles'; $('#p-state').value = 'CA'; $('#p-status').value = 'FOR SALE';
  $('#p-image1').value = ''; $('#p-image2').value = '';
  $('#p-img1-preview').innerHTML = ''; $('#p-img2-preview').innerHTML = '';
  clearExtraImgs();
  $('#p-desc').value = ''; $('#p-has-detail').checked = false;
  $('#p-section-live').checked  = false;
  $('#p-section-bbb').checked   = false;
  $('#p-section-home').checked  = false;
  $('#p-section-deals').checked = false;
  CITY_SLUGS.forEach(slug => { const el = $(`#p-nbhd-${slug}`); if (el) el.checked = false; });
  syncPriceFields();
  $('#prop-modal').style.display = 'flex';
  setTimeout(() => $('#p-address').focus(), 80);
});

function syncPriceFields() {
  const s = $('#p-status').value;
  const priceWrap = $('#p-price-wrap');
  const rentWrap  = $('#p-rent-wrap');
  const priceLabel = $('#p-price-label');
  const forLease = s === 'FOR LEASE';
  const forSale  = s === 'FOR SALE' || s === 'SOLD';
  const dual     = s === 'FOR SALE / LEASE';
  priceWrap.style.display = forLease ? 'none' : '';
  rentWrap.style.display  = forSale  ? 'none' : '';
  if (priceLabel) priceLabel.textContent = s === 'SOLD' ? 'Sold Price' : 'Sale Price';
  if (forLease) { $('#p-price').value = ''; }
  if (forSale)  { $('#p-rent').value  = ''; }
}
$('#p-status').addEventListener('change', syncPriceFields);

function closePropModal() { $('#prop-modal').style.display = 'none'; editingPropId = null; }
$('#close-prop-modal').addEventListener('click', closePropModal);
$('#cancel-prop').addEventListener('click', closePropModal);
$('#prop-modal').addEventListener('click', e => { if (e.target === $('#prop-modal')) closePropModal(); });

$('#move-to-deals-btn').addEventListener('click', () => {
  $('#p-section-deals').checked = true;
  $('#p-section-live').checked  = false;
  $('#p-section-home').checked  = false;
  $('#save-prop').click();
});

$('#save-prop').addEventListener('click', async () => {
  if (!$('#p-address').value.trim()) { toast('Address is required', true); return; }
  if (!$('#p-image1').value.trim()) { toast('Please upload a primary photo first', true); return; }

  const data = {
    address: $('#p-address').value.trim(),
    city:    $('#p-city').value.trim()    || 'Los Angeles',
    state:   $('#p-state').value.trim()   || 'CA',
    price:   $('#p-price').value.trim(),
    rent:    $('#p-rent').value.trim(),
    beds:    $('#p-beds').value.trim(),
    baths:   $('#p-baths').value.trim(),
    sqft:    $('#p-sqft').value.trim(),
    status:  $('#p-status').value,
    image1:  $('#p-image1').value.trim(),
    image2:  $('#p-image2').value.trim(),
    description:     $('#p-desc').value.trim(),
    has_detail_page: $('#p-has-detail').checked,
    sections: [
      ...($('#p-section-live').checked  ? ['live_listings'] : []),
      ...($('#p-section-bbb').checked   ? ['built_by_ben']  : []),
      ...($('#p-section-home').checked  ? ['homepage']      : []),
      ...($('#p-section-deals').checked ? ['former_deals']  : []),
    ],
    neighborhoods: CITY_SLUGS.filter(slug => { const el = $(`#p-nbhd-${slug}`); return el && el.checked; }),
  };
  // Collect extra photos (slot 3 onward)
  document.querySelectorAll('#p-extra-imgs .p-extra-image').forEach((inp, idx) => {
    const val = inp.value.trim();
    if (val) data[`image${idx + 3}`] = val;
  });

  const btn = $('#save-prop');
  btn.textContent = 'Saving…';
  btn.disabled = true;

  let r;
  if (editingPropId) {
    r = await api('PUT', `/api/properties/${editingPropId}`, data);
  } else {
    r = await api('POST', '/api/properties', data);
  }

  btn.textContent = 'Save & Publish';
  btn.disabled = false;

  if (r && (r.ok || r.id)) {
    const verb = editingPropId ? 'updated' : 'added';
    toast(`Property ${verb} — site updated! ✓`);
    closePropModal();
    loadProperties();
  } else {
    toast('Error saving', true);
  }
});

function deleteProp(id, addr) {
  if (!confirm(`Delete "${addr}"?\n\nThis will remove it from the website immediately.`)) return;
  api('DELETE', `/api/properties/${id}`).then(r => {
    if (r && r.ok) { toast('Property deleted — site updated'); loadProperties(); }
    else toast('Failed to delete', true);
  });
}

// ── Property / Listing image uploads ──────────────────────────────────────────

function showImgPreview(previewId, path) {
  const el = $('#' + previewId);
  if (!path) { el.innerHTML = ''; return; }
  el.innerHTML = `<div style="display:flex;align-items:center;gap:10px;background:#f0f4f8;border-radius:8px;padding:8px 12px">
    <img src="/${path}" style="height:56px;width:72px;object-fit:cover;border-radius:5px;flex-shrink:0">
    <div>
      <div style="font-size:12px;font-weight:700;color:#0a223f">Photo uploaded</div>
      <div style="font-size:11px;color:#9ca3af;margin-top:2px">${path.split('/').pop()}</div>
    </div>
    <button onclick="clearImg('${previewId}','')"
      style="margin-left:auto;background:#fee2e2;border:none;border-radius:6px;padding:5px 10px;color:#dc2626;font-size:11px;font-weight:700;cursor:pointer">Remove</button>
  </div>`;
}

function clearImg(previewId, hiddenId) {
  // map previewId back to hidden input id
  const m = previewId.match(/img(\d+)/);
  const num = m ? m[1] : '1';
  $('#p-image' + num).value = '';
  $('#' + previewId).innerHTML = '';
}

async function uploadPropertyImage(file, num) {
  showImgPreview(`p-img${num}-preview`, null);
  $('#p-img' + num + '-preview').innerHTML = `<div style="padding:8px 12px;font-size:12px;color:#9ca3af">Uploading…</div>`;
  const fd = new FormData(); fd.append('image', file);
  const r = await api('POST', '/api/upload/image', fd, true);
  if (r?.path) {
    $('#p-image' + num).value = r.path;
    showImgPreview(`p-img${num}-preview`, r.path);
  } else {
    $('#p-img' + num + '-preview').innerHTML = `<div style="padding:8px;color:#dc2626;font-size:12px">Upload failed — try again</div>`;
  }
}

function setupPropImgDZ(dzId, fileInputId, num) {
  const dz = $('#' + dzId), input = $('#' + fileInputId);
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('over'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('over'));
  dz.addEventListener('drop', e => {
    e.preventDefault(); dz.classList.remove('over');
    if (e.dataTransfer.files.length) uploadPropertyImage(e.dataTransfer.files[0], num);
  });
  input.addEventListener('change', () => {
    if (input.files.length) uploadPropertyImage(input.files[0], num);
  });
}

setupPropImgDZ('dz-p-img1', 'p-img1-file', 1);
setupPropImgDZ('dz-p-img2', 'p-img2-file', 2);

let nextImgSlot = 3;

function clearExtraImgs() {
  document.getElementById('p-extra-imgs').innerHTML = '';
  nextImgSlot = 3;
}

function addPhotoSlot(existingVal) {
  if (nextImgSlot > 20) { toast('Maximum 20 photos reached', true); return; }
  const num = nextImgSlot++;
  const container = document.getElementById('p-extra-imgs');
  const wrap = document.createElement('div');
  wrap.id = `p-img${num}-wrap`;
  wrap.style.cssText = 'margin-bottom:12px;';
  wrap.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">
      <span style="font-size:12px;color:#6b7280;font-weight:600">Photo ${num}</span>
      <button type="button" onclick="removePhotoSlot(${num})" style="background:#fee2e2;border:none;border-radius:5px;padding:3px 9px;color:#dc2626;font-size:11px;font-weight:700;cursor:pointer">Remove</button>
    </div>
    <div class="dropzone" id="dz-p-img${num}">
      <input type="file" id="p-img${num}-file" accept="image/*">
      <div class="dz-icon">📷</div>
      <div class="dz-text"><strong>Click to browse</strong></div>
    </div>
    <div id="p-img${num}-preview" style="margin-top:8px;min-height:20px"></div>
    <input type="hidden" id="p-image${num}" class="p-extra-image" value="">
  `;
  container.appendChild(wrap);
  setupPropImgDZ(`dz-p-img${num}`, `p-img${num}-file`, num);
  if (existingVal) {
    document.getElementById(`p-image${num}`).value = existingVal;
    showImgPreview(`p-img${num}-preview`, existingVal);
  }
}

function removePhotoSlot(num) {
  const wrap = document.getElementById(`p-img${num}-wrap`);
  if (wrap) wrap.remove();
}

// ── Inbox ─────────────────────────────────────────────────────────────────────
let contacts = [];

async function loadInbox() {
  contacts = await api('GET', '/api/contacts') || [];
  renderInbox();
}

async function loadInboxBadge() {
  const data = await api('GET', '/api/contacts') || [];
  updateBadge(data.filter(c => !c.read).length);
}

function updateBadge(count) {
  const badge = $('#inbox-badge');
  badge.textContent = count;
  badge.style.display = count > 0 ? 'inline-flex' : 'none';
}

function esc(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function renderInbox() {
  const unread = contacts.filter(c => !c.read).length;
  updateBadge(unread);
  $('#inbox-count').textContent = `· ${contacts.length} total, ${unread} unread`;

  const list = $('#inbox-list');
  if (!contacts.length) {
    list.innerHTML = '<div class="inbox-empty">No messages yet.</div>';
    return;
  }

  list.innerHTML = contacts.map(c => `
    <div class="inbox-card ${c.read ? 'is-read' : 'is-unread'}" id="msg-${c.id}">
      <div class="inbox-card-hd" onclick="openMsg('${c.id}')">
        <div class="inbox-dot"></div>
        <div class="inbox-from">${esc(c.name || c.email || 'Anonymous')}</div>
        <div class="inbox-chip">${esc(c.source_label || c.source || 'Contact')}</div>
        <div class="inbox-ts">${esc(c.timestamp)}</div>
      </div>
      <div class="inbox-card-body">
        ${c.name    ? `<div class="inbox-field"><strong>Name</strong>${esc(c.name)}</div>` : ''}
        ${c.email   ? `<div class="inbox-field"><strong>Email</strong><a href="mailto:${esc(c.email)}">${esc(c.email)}</a></div>` : ''}
        ${c.phone   ? `<div class="inbox-field"><strong>Phone</strong><a href="tel:${esc(c.phone.replace(/\D/g,''))}">${esc(c.phone)}</a></div>` : ''}
        ${c.property_address ? `<div class="inbox-field"><strong>Property</strong>${esc(c.property_address)}</div>` : ''}
        ${c.inquiry_type ? `<div class="inbox-field"><strong>Inquiry</strong>${esc(c.inquiry_type)}</div>` : ''}
        ${c.message ? `<div class="inbox-field"><strong>Message</strong>${esc(c.message)}</div>` : ''}
        <div class="inbox-field"><strong>Source</strong>${esc(c.source_label || c.source)}</div>
        <div class="inbox-card-actions">
          <button class="inbox-act-btn inbox-act-read" onclick="toggleRead('${c.id}',${c.read})">${c.read ? 'Mark unread' : 'Mark read'}</button>
          <button class="inbox-act-btn inbox-act-del" onclick="deleteMsg('${c.id}')">Delete</button>
        </div>
      </div>
    </div>`).join('');
}

function openMsg(id) {
  const el = document.getElementById('msg-' + id);
  const isOpen = el.classList.contains('is-open');
  $$('.inbox-card.is-open').forEach(e => e.classList.remove('is-open'));
  if (!isOpen) {
    el.classList.add('is-open');
    const c = contacts.find(x => x.id === id);
    if (c && !c.read) toggleRead(id, false);
  }
}

async function toggleRead(id, currentlyRead) {
  const r = await api('PATCH', `/api/contacts/${id}/read`, { read: !currentlyRead });
  if (!r?.ok) return;
  const c = contacts.find(x => x.id === id);
  if (c) c.read = !currentlyRead;
  renderInbox();
  const el = document.getElementById('msg-' + id);
  if (el) el.classList.add('is-open');
}

async function deleteMsg(id) {
  const c = contacts.find(x => x.id === id);
  if (!confirm(`Delete message from ${c ? esc(c.name || c.email || 'this sender') : 'this sender'}?`)) return;
  const r = await api('DELETE', `/api/contacts/${id}`);
  if (r?.ok) {
    contacts = contacts.filter(x => x.id !== id);
    renderInbox();
    toast('Message deleted');
  }
}

$('#mark-all-btn').addEventListener('click', async () => {
  const r = await api('PATCH', '/api/contacts/read-all');
  if (r?.ok) {
    contacts.forEach(c => c.read = true);
    renderInbox();
    toast('All marked read');
  }
});

// Boot
init();
</script>
</body>
</html>"""


if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    port = int(os.environ.get('PORT', 2004))
    print('\n  Ben Lee Properties Admin Server')
    print('  ─────────────────────────────────')
    print(f'  Admin panel : http://localhost:{port}/admin')
    print(f'  Password    : {ADMIN_PASSWORD}')
    print(f'  Data dir    : {DATA_DIR}')
    print('  Press Ctrl+C to stop\n')
    app.run(debug=False, host='0.0.0.0', port=port)
