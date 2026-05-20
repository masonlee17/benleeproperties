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

import json, os, re, uuid, calendar
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
    repo_data = json.load(open(repo_path))
    needs_seed = False
    if not os.path.exists(vol_path):
        needs_seed = True
    else:
        vol_data = json.load(open(vol_path))
        # Seed if the volume has no entry with a 'sections' key — old format
        if isinstance(vol_data, list) and vol_data and not any('sections' in p for p in vol_data):
            needs_seed = True
    if needs_seed:
        save('properties.json', repo_data)

def load(name):
    # Volume takes priority; repo is the read-only fallback (or seed source)
    for base in (DATA_DIR, REPO_DATA_DIR):
        p = os.path.join(base, name)
        if os.path.exists(p):
            return json.load(open(p))
    return []

def save(name, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    json.dump(data, open(os.path.join(DATA_DIR, name), 'w'), indent=2)

# Run at import time (works for both `python admin.py` and gunicorn)
seed_volume_if_needed()

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
    images   = [p[k] for k in [f'image{i}' for i in range(1, 21)] if p.get(k)]

    title    = f'{addr} | Ben Lee Properties'
    og_img   = images[0] if images else ''

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


# ── Dynamic pages ──────────────────────────────────────────────────────────────
# These two pages are rendered live so admin edits are instant without redeploying.

@app.route('/market-updates/<slug>')
def market_update(slug):
    path = os.path.join(BASE_DIR, 'market-updates', f'{slug}.html')
    if os.path.exists(path):
        return open(path, encoding='utf-8').read()
    return 'Not found', 404

@app.route('/blog')
@app.route('/blog.html')
def blog():
    return render_dynamic('blog.html', 'NEWSLETTERS',
                          build_newsletter_sections(load('newsletters.json')))

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

@app.route('/valuation')
@app.route('/valuation.html')
def valuation():
    return render_dynamic('valuation.html', 'VAL_LISTINGS',
                          build_index_listing_items([p for p in load('properties.json') if 'live_listings' in p.get('sections', [])]))

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
                          build_index_listing_items([p for p in load('properties.json') if 'live_listings' in p.get('sections', [])]))

# ── Contact form submission ────────────────────────────────────────────────────

@app.route('/contact-submit', methods=['POST'])
def contact_submit():
    source = request.form.get('_source', 'contact')
    entry = {
        'id': str(uuid.uuid4()),
        'timestamp': datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
        'source': source,
        'name': (request.form.get('Your-Name', '') + ' ' + request.form.get('Your-Surname', '')).strip(),
        'phone': request.form.get('Your-Phone', ''),
        'email': request.form.get('Your-Email', ''),
        'message': request.form.get('Message', ''),
    }
    contacts_path = os.path.join(DATA_DIR, 'contacts.json')
    try:
        contacts = json.load(open(contacts_path)) if os.path.exists(contacts_path) else []
    except Exception:
        contacts = []
    contacts.insert(0, entry)
    os.makedirs(DATA_DIR, exist_ok=True)
    json.dump(contacts, open(contacts_path, 'w'), indent=2)

    back = '/contact-2.html?sent=1' if source == 'contact-2' else ('/detail_property.html?sent=1' if source == 'tour' else '/contact.html?sent=1')
    return redirect(back)


@app.route('/api/contacts', methods=['GET'])
@login_required
def get_contacts():
    contacts_path = os.path.join(DATA_DIR, 'contacts.json')
    try:
        return jsonify(json.load(open(contacts_path)) if os.path.exists(contacts_path) else [])
    except Exception:
        return jsonify([])


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
          </div>
          <div class="hint">Controls which pages this property appears on.</div>
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
            ${p.has_detail_page ? '<span style="display:inline-block;font-size:9px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;background:#7c3aed;color:#fff;padding:1px 7px;border-radius:2em">Detail Page</span>' : ''}
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
  $('#p-section-live').checked = (p.sections || []).includes('live_listings');
  $('#p-section-bbb').checked  = (p.sections || []).includes('built_by_ben');
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
  $('#p-section-live').checked = false;
  $('#p-section-bbb').checked  = false;
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
      ...($('#p-section-live').checked ? ['live_listings'] : []),
      ...($('#p-section-bbb').checked  ? ['built_by_ben']  : []),
    ],
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
