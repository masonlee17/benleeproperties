#!/usr/bin/env python3
"""
Generate market-updates HTML pages for all newsletters that have a PDF but no html_url.
Extracts article text from each PDF, generates SEO meta, prev/next nav, and
the nl-text-body article tag that powers BM25 search.

Push to GitHub every 3 pages.

Usage:  python3 generate_newsletter_pages.py
Resume: python3 generate_newsletter_pages.py --start 2019-03
"""
import os, sys, re, json, calendar, html as _html, subprocess
import fitz  # PyMuPDF

BASE    = os.path.dirname(os.path.abspath(__file__))
MU_DIR  = os.path.join(BASE, 'market-updates')
DOCS_DIR = os.path.join(BASE, 'documents')
DATA_FILE = os.path.join(BASE, 'data', 'newsletters.json')
DOMAIN   = 'https://www.benleeproperties.com'

os.makedirs(MU_DIR, exist_ok=True)

MONTH_NAMES = [
    '', 'January','February','March','April','May','June',
    'July','August','September','October','November','December'
]

# ── Text extraction ───────────────────────────────────────────────────────────

def clean_text(raw: str) -> str:
    """Fix hyphenated line breaks, collapse whitespace, strip junk."""
    # Join soft-hyphen line breaks: "neigh-\nborhood" → "neighborhood"
    text = re.sub(r'-\s*\n\s*', '', raw)
    # Collapse newlines to spaces
    text = re.sub(r'\n+', ' ', text)
    # Collapse multiple spaces
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def extract_pdf_text(pdf_path: str) -> dict:
    """Return {page_num: cleaned_text} for each page."""
    pages = {}
    try:
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):
            raw = page.get_text('text')
            pages[i + 1] = clean_text(raw)
        doc.close()
    except Exception as e:
        print(f'    PDF read error: {e}')
    return pages


def split_paragraphs(text: str, min_len: int = 40) -> list[str]:
    """Split cleaned text into meaningful paragraph-sized chunks."""
    # Split on sentence ends followed by capital letters (rough paragraph detection)
    chunks = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    paras = []
    buf = ''
    for c in chunks:
        buf = (buf + ' ' + c).strip() if buf else c
        if len(buf) >= min_len:
            paras.append(buf)
            buf = ''
    if buf and len(buf) > 10:
        paras.append(buf)
    return paras


JUNK_PATTERNS = [
    r'PRSRT STD', r'ECRWSS', r'U\.S\. POSTAGE', r'EDDM Retail',
    r'Residential Postal Customer', r'BRE #', r'CalRE #',
    r'Coldwell Banker', r'©20\d\d', r'NRT LLC', r'Fair Housing',
    r'Equal Opportunity', r'registered service marks',
    r'www\.BenLeeProperties\.com', r'Ben Lee Properties\.com',
    r'\(310\)\s*\d{3}-\d{4}', r'\(310\)\s*858', r'\(310\)\s*704',
    r'BEN LEE PROPERTIES', r'Ben Lee Properties\s*–\s*Real Estate',
    r'Real Estate Broker\s*•\s*Licensed Attorney',
    r'Broker Associate',
    r'Licensed Attorney',
    r'CalBRE', r'DRE #', r'intended as a solicitation',
    r'^\s*no\.\s*\d+\s*$',  # issue number lines
]
JUNK_RE = re.compile('|'.join(JUNK_PATTERNS), re.IGNORECASE)


def is_junk(para: str) -> bool:
    return bool(JUNK_RE.search(para)) or len(para.strip()) < 25


def _clean_paras(text: str, max_chars: int) -> list[str]:
    paras = split_paragraphs(text)
    clean = [p for p in paras if not is_junk(p)]
    result, total = [], 0
    for p in clean:
        if total + len(p) > max_chars:
            break
        result.append(p)
        total += len(p)
    return result


def extract_article_paragraphs(pages: dict, max_chars: int = 15000) -> tuple[list[str], list[str]]:
    """Return (main_paras, community_paras) from pages 2 and 4 respectively.
    Page 3 (listings) is handled separately by extract_listings."""
    main      = _clean_paras(pages.get(2, ''), max_chars)
    community = _clean_paras(pages.get(4, ''), max_chars)
    return main, community


# Status keywords that mark a property listing
_STATUS_KW = (
    r'SOLD OVER ASKING|SOLD AT ASKING|SOLD|FOR SALE OR LEASE|FOR SALE|'
    r'IN ESCROW|FOR LEASE|NEW LISTING|NEW PRICE|GREAT NEW PRICE|'
    r'BACK ON MARKET|JUST LISTED|PRICE REDUCED|COMING SOON'
)
_STATUS_RE = re.compile(r'(?:' + _STATUS_KW + r')', re.IGNORECASE)
# Matches TitleCase neighborhood name immediately before a dash (at end of lookback string)
_NBHD_RE = re.compile(r'([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s*[-–]\s*$')
# Real-estate words that look like neighborhood names but aren't
_NON_NBHD = frozenset({'Lot', 'Lots', 'Sq', 'Bath', 'Baths', 'Bed', 'Beds',
                       'Floor', 'Floors', 'Unit', 'Units', 'Garage', 'Story', 'Stories', 'Ft'})
# Header boilerplate to strip before parsing listings
_LISTING_HEADER_RE = re.compile(
    r'^.*?(?:My featured listings|BEN LEE\s*[-–]|Broker Associate).*?(?=\b[A-Z])',
    re.IGNORECASE | re.DOTALL
)


def extract_listings(pages: dict) -> list[str]:
    """Split page 3 into individual property listing entries.
    Finds STATUS keyword positions, looks back for 'Neighborhood –' to get true listing start."""
    if 3 not in pages:
        return []
    text = pages[3]

    # Strip header boilerplate
    header_m = _LISTING_HEADER_RE.match(text)
    if header_m:
        text = text[header_m.end():]

    # Find the true start of each listing by looking back from each status keyword
    split_positions = []
    for m in _STATUS_RE.finditer(text):
        prefix = text[max(0, m.start() - 80):m.start()]
        nb_m = _NBHD_RE.search(prefix)
        if nb_m:
            # Strip leading non-neighborhood words (e.g. "Lot" from "Lot Beverlywood")
            nbhd_words = nb_m.group(1).split()
            while nbhd_words and nbhd_words[0] in _NON_NBHD:
                nbhd_words.pop(0)
            if not nbhd_words:
                continue
            # Find the position of the first (cleaned) neighborhood word in the original text
            search_from = max(0, m.start() - 80)
            idx = text.rfind(nbhd_words[0], search_from, m.start())
            if idx != -1:
                split_positions.append(idx)

    # Fallback: double-space splitting if no status markers found
    if not split_positions:
        lines = [l.strip() for l in text.split('  ') if l.strip()]
        return [l for l in lines
                if re.search(r'\$[\d,]+', l) or
                re.search(r'\d+\s+\w+\s+(?:Ave|Dr|Pl|St|Blvd|Rd|Way|Ct)\b', l, re.I)][:25]

    split_positions = sorted(set(split_positions))
    split_positions.append(len(text))
    listings = []
    for i, pos in enumerate(split_positions[:-1]):
        seg = re.sub(r'\s+', ' ', text[pos:split_positions[i + 1]]).strip()
        if len(seg) > 20 and (re.search(r'\$[\d,]+', seg) or
                              re.search(r'\d+\s+\w+\s+(?:Ave|Dr|Pl|St|Blvd|Rd|Way|Ct|Ln|Canyon|Circle|Ter|Place|Street)\b', seg, re.I)):
            listings.append(seg)
    return listings[:25]


def make_description(paras: list[str], label: str) -> str:
    """Generate a ~155-char SEO description from article text."""
    for p in paras:
        if len(p) > 60:
            desc = re.sub(r'\s+', ' ', p[:160]).strip()
            if len(desc) > 155:
                desc = desc[:152] + '...'
            return desc
    return f"Read Ben Lee's {label} real estate newsletter — market analysis and neighborhood insights for Cheviot Hills, Beverlywood, and West LA."


def make_keywords(label: str, listings: list[str]) -> str:
    base = f'Ben Lee newsletter {label}, Los Angeles real estate, Cheviot Hills market update, Beverlywood home values, West LA real estate trends'
    # Add a few address mentions if available
    addrs = []
    for l in listings[:4]:
        m = re.search(r'(\d+\s+[\w\s]+(?:Ave|Dr|Pl|St|Blvd|Rd|Way|Canyon|Ct|Ln|Circle|Ter|Place|Street))',
                      l, re.I)
        if m:
            addrs.append(m.group(1).strip())
    if addrs:
        base += ', ' + ', '.join(addrs)
    return base


# ── HTML template ─────────────────────────────────────────────────────────────

NAV_HTML = open(os.path.join(MU_DIR, 'january-2025.html')).read()
# Extract the nav/footer/header boilerplate (everything outside the unique content)
# We'll use sections of january-2025.html as our base

def slug_for(year, month):
    return f'{MONTH_NAMES[month].lower()}-{year}'

def prev_next(nl_list, idx):
    """Return (prev_slug, next_slug) or None."""
    prev_nl = nl_list[idx - 1] if idx > 0 else None
    next_nl = nl_list[idx + 1] if idx < len(nl_list) - 1 else None
    return (
        slug_for(prev_nl['year'], prev_nl['month']) if prev_nl else None,
        slug_for(next_nl['year'], next_nl['month']) if next_nl else None,
    )


def generate_html(nl, main_paras, community_paras, listings, prev_slug, next_slug):
    year, month = nl['year'], nl['month']
    label    = nl['label']
    nid      = nl['id']
    pdf_rel  = nl.get('pdf', '')
    cover    = nl.get('cover', '')
    slug     = slug_for(year, month)
    url      = f'{DOMAIN}/market-updates/{slug}'
    cover_url = f'{DOMAIN}/{cover}' if cover else f'{DOMAIN}/images/BLK-09766.jpg'
    pdf_path_rel = f'../{pdf_rel}' if pdf_rel else '#'

    all_paras = main_paras + community_paras
    desc     = make_description(all_paras, label)
    kw       = make_keywords(label, listings)
    safe_desc = _html.escape(desc)

    # Main article (page 2)
    main_html = ''
    if main_paras:
        body = '\n'.join(f'  <p>{_html.escape(p)}</p>' for p in main_paras)
        main_html = f'  <p class="nl-text-section-title">This Month&#x27;s Article</p>\n{body}'

    # Featured listings (page 3)
    listings_section = ''
    if listings:
        cards_html = '\n'.join(
            f'  <div class="nl-listing-card"><p>{_html.escape(l)}</p></div>'
            for l in listings
        )
        listings_section = f'\n  <p class="nl-text-section-title">Featured Listings</p>\n{cards_html}'

    # Community / secondary articles (page 4)
    community_html = ''
    if community_paras:
        body = '\n'.join(f'  <p>{_html.escape(p)}</p>' for p in community_paras)
        community_html = f'\n  <p class="nl-text-section-title">Community &amp; More</p>\n{body}'

    # Prev/Next nav
    prev_link = (f'<a href="{prev_slug}.html" class="nl-nav-link">'
                 f'<img src="../images/arrow_right_black_24dp.svg" loading="lazy" alt="" '
                 f'style="transform:rotate(180deg);width:18px;height:18px;"> Prev Issue</a>'
                 if prev_slug else '<span></span>')
    next_link = (f'<a href="{next_slug}.html" class="nl-nav-link">Next Issue '
                 f'<img src="../images/arrow_right_black_24dp.svg" loading="lazy" alt="" '
                 f'style="width:18px;height:18px;"></a>'
                 if next_slug else '<span></span>')
    dl_link = (f'<a href="{pdf_path_rel}" class="nl-download-btn" download>'
               f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">'
               f'<path d="M19 9h-4V3H9v6H5l7 7 7-7zm-8 2V5h2v6h1.17L12 13.17 9.83 11H11zm-6 7h14v2H5z"/></svg>'
               f' Download PDF</a>' if pdf_rel else '')

    schema_date = f'{year}-{month:02d}-01'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{_html.escape(label)} | Ben Lee Properties — LA Real Estate Newsletter</title>
  <meta name="description" content="{safe_desc}">
  <meta name="keywords" content="{_html.escape(kw)}">
  <meta name="robots" content="index, follow">
  <meta name="author" content="Ben Lee Properties">
  <link rel="canonical" href="{url}">

  <!-- Open Graph -->
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Ben Lee Properties">
  <meta property="og:title" content="{_html.escape(label)} | Ben Lee Properties — LA Real Estate Newsletter">
  <meta property="og:description" content="Read Ben Lee&#39;s {_html.escape(label)} real estate newsletter — market analysis, neighborhood guides, and expert advice for buyers and sellers in Cheviot Hills, Beverlywood, and West LA.">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{cover_url}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:locale" content="en_US">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{_html.escape(label)} | Ben Lee Properties — LA Real Estate Newsletter">
  <meta name="twitter:description" content="Read Ben Lee&#39;s {_html.escape(label)} real estate newsletter — market analysis, neighborhood guides, and expert advice for Cheviot Hills, Beverlywood, and West LA.">
  <meta name="twitter:image" content="{cover_url}">

  <!-- Geo -->
  <meta name="geo.region" content="US-CA">
  <meta name="geo.placename" content="Cheviot Hills &amp; Beverlywood, Los Angeles, CA">
  <meta name="geo.position" content="34.0400;-118.4080">
  <meta name="ICBM" content="34.0400, -118.4080">

  <meta content="width=device-width, initial-scale=1" name="viewport">
  <meta name="author" content="Ben Lee Properties">
  <link href="../css/normalize.css" rel="stylesheet" type="text/css">
  <link href="../css/webflow.css" rel="stylesheet" type="text/css">
  <link href="../css/ben-lee-properties.webflow.css" rel="stylesheet" type="text/css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <script type="text/javascript">!function(o,c){{var n=c.documentElement,t=" w-mod-";n.className+=t+"js",("ontouchstart"in o||o.DocumentTouch&&c instanceof DocumentTouch)&&(n.className+=t+"touch")}}(window,document);</script>
  <link href="../images/favicon.png" rel="shortcut icon" type="image/x-icon">
  <link href="../images/webclip.png" rel="apple-touch-icon">
  <style>
    .nl-viewer {{width:100%;background:#f5f5f5;padding:2em 0;}}
    .nl-viewer-inner {{max-width:900px;margin:0 auto;padding:0 1em;}}
    .nl-viewer iframe {{width:100%;height:85vh;min-height:600px;border:none;border-radius:4px;box-shadow:0 4px 24px rgba(0,0,0,0.12);display:block;}}
    .nl-nav {{display:flex;justify-content:space-between;align-items:center;padding:1.5em 0 0.5em;gap:1em;}}
    .nl-nav-link {{display:inline-flex;align-items:center;gap:0.4em;font-family:'Montserrat',sans-serif;font-weight:600;font-size:0.85em;letter-spacing:0.05em;text-transform:uppercase;color:#1a1a2e;text-decoration:none;transition:opacity 0.2s;}}
    .nl-nav-link:hover {{opacity:0.6;}}
    .nl-nav-link.disabled {{opacity:0.3;pointer-events:none;}}
    .nl-download-btn {{display:inline-flex;align-items:center;gap:0.5em;background:#1a1a2e;color:#fff;font-family:'Montserrat',sans-serif;font-weight:600;font-size:0.8em;letter-spacing:0.08em;text-transform:uppercase;padding:0.7em 1.4em;border-radius:2px;text-decoration:none;transition:opacity 0.2s;}}
    .nl-download-btn:hover {{opacity:0.8;}}
    .nl-fallback {{text-align:center;padding:3em 1em;font-family:'Montserrat',sans-serif;}}
    .nl-fallback p {{margin-bottom:1em;color:#555;}}
    .nl-text-body {{max-width:860px;margin:0 auto;padding:48px 24px 64px;font-family:'Montserrat',sans-serif;}}
    .nl-text-body h2 {{font-size:1.1em;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:#07264b;margin:0 0 4px;}}
    .nl-text-body .nl-text-meta {{font-size:0.78em;color:#888;letter-spacing:.06em;margin-bottom:28px;text-transform:uppercase;}}
    .nl-text-section-title {{font-size:0.72em;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#1d3fa0;border-bottom:1px solid #e0e6f0;padding-bottom:4px;margin:32px 0 12px;}}
    .nl-text-body p {{font-size:0.88em;line-height:1.85;color:#333;margin:0 0 10px;}}
    .nl-listing-card {{background:#f6f8ff;border-left:3px solid #1d3fa0;padding:10px 14px;margin:10px 0;border-radius:0 4px 4px 0;}}
    .nl-listing-card p {{font-size:0.84em !important;line-height:1.65 !important;color:#222 !important;margin:0 !important;}}
  </style>

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": "{_html.escape(label)} | Ben Lee Properties Newsletter",
    "description": "{safe_desc}",
    "datePublished": "{schema_date}",
    "author": {{"@type": "Person", "name": "Ben Lee"}},
    "publisher": {{"@type": "Organization", "name": "Ben Lee Properties", "url": "https://www.benleeproperties.com"}},
    "url": "{url}",
    "image": "{cover_url}",
    "isPartOf": {{"@type": "Periodical", "name": "Ben Lee Real Estate Newsletter", "url": "https://www.benleeproperties.com/blog"}}
  }}
  </script>
</head>
<body>
  <div class="page-wrapper">
    <div class="aside-menu">
      <div class="menu-inner">
        <div class="menu-nav">
          <div class="menu-close"><img src="../images/close_white_24dp.svg" loading="lazy" alt="" class="menu-close-icon"></div>
        </div>
        <div class="menu-content">
          <div class="menu-column-left">
            <div class="menu-office-wrap">
              <div class="office-block"><p class="menu-office-title">Beverly Hills Office</p><p class="menu-office-address">9454 Wilshire Blvd, Beverly Hills, CA 90212</p></div>
              <div class="office-block"><p class="menu-office-title">West Los Angeles Office</p><p class="menu-office-address">11500 W Olympic Blvd, Los Angeles, CA 90064</p></div>
              <div class="menu-office-contacts">
                <a href="mailto:ben@benleeproperties.com" class="menu-contact-link">ben@benleeproperties.com</a>
                <a href="tel:+13107046580" class="menu-contact-link">(310) 704-6580</a>
              </div>
            </div>
            <a href="../index.html" class="menu-brand w-inline-block"><img src="../images/alley-template-real-estates-vertical-logo-white.svg" loading="lazy" alt="Ben Lee Properties logo" class="menu-brand-logo"></a>
          </div>
          <div class="menu-column-right">
            <div class="menu-main-links">
              <a href="../index.html" class="menu-link w-inline-block"><p class="menu-link-paragraph">Home</p></a>
              <a href="../about.html" class="menu-link w-inline-block"><p class="menu-link-paragraph">About</p></a>
              <a href="../current-listings.html" class="menu-link w-inline-block"><p class="menu-link-paragraph">For buyers</p></a>
              <a href="../neighborhoods.html" class="menu-link w-inline-block"><p class="menu-link-paragraph">Neighborhoods</p></a>
              <a href="../for-sellers.html" class="menu-link w-inline-block"><p class="menu-link-paragraph">For sellers</p></a>
              <a href="../blog.html" class="menu-link w-inline-block w--current"><p class="menu-link-paragraph">Newsletter</p></a>
              <a href="../contact.html" class="menu-link w-inline-block"><p class="menu-link-paragraph">Contact</p></a>
            </div>
          </div>
        </div>
      </div>
      <div class="menu-background"></div>
    </div>
    <div data-animation="default" data-collapse="none" data-duration="400" role="banner" class="navbar-2 w-nav">
      <div class="navbar-container-2">
        <div class="nav-left-2">
          <a href="../index.html" class="brand is-2nd w-nav-brand">
            <div class="text-block _2 name">BEN LEE</div>
            <img src="../images/the-agency-logo-white.png" loading="lazy" alt="The Agency" class="image-2" style="height:40px;width:auto;object-fit:contain;">
          </a>
        </div>
        <nav role="navigation" class="nav-menu-2 w-nav-menu">
          <a href="../index.html" class="nav-link-2 w-nav-link">Home</a>
          <div data-hover="false" data-delay="0" class="dropdown-4 w-dropdown">
            <div class="dropdown-toggle-2 w-dropdown-toggle"><div class="icon-4 w-icon-dropdown-toggle"></div><div class="text-block-6">ALL PROPERTIES</div></div>
            <nav class="dropdown-list-4 w-dropdown-list">
              <a href="../for-buyers-3.html" class="dropdown-link w-dropdown-link">LIVE LISTINGS</a>
              <a href="../ben-lee-sold-properties.html" class="dropdown-link-2 w-dropdown-link">RECENT TRANSACTIONS</a>
              <a href="../current-listings.html" class="dropdown-link w-dropdown-link">BUILT BY BEN</a>
              <a href="/deals" class="dropdown-link w-dropdown-link">FORMER DEALS</a>
            </nav>
          </div>
          <a href="../about.html" class="nav-link-2 w-nav-link">Our team</a>
          <a href="../valuation.html" class="nav-link-2 w-nav-link">Valuation</a>
          <a href="../blog.html" class="nav-link-2 w-nav-link w--current">Newsletter</a>
          <a href="../social-media.html" class="nav-link-2 w-nav-link">Social Media</a>
          <a href="../contact.html" class="nav-link-2 w-nav-link">Contact</a>
        </nav>
        <div class="menu-button w-nav-button">
          <div class="menu-button-flex">
            <div class="menu-text-block">Menu</div>
            <div class="burger-icon in-menu-button">
              <div class="burger-icon-line"></div><div class="burger-icon-line"></div><div class="burger-icon-line"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <main class="main">
      <section class="section blue-gradient-background">
        <div class="padding-8em _2 news">
          <div class="call-to-action-wrap value">
            <p class="toptitle-paragraph white-color">KEEP UP WITH BEN LEE</p>
            <h3 class="motion-heading white-color news">BEN LEE NEWSLETTERS</h3>
            <div class="buttons-wrap">
              <a href="../for-buyers-3.html" class="button _2 w-inline-block">
                <p class="button-paragraph">VIEW CURRENT LISTINGS</p>
                <img src="../images/arrow_right_white_24dp.svg" loading="lazy" alt="" class="button-arrow-right">
                <div class="button-background"></div>
              </a>
            </div>
          </div>
        </div>
      </section>
      <div class="nl-viewer">
        <div class="nl-viewer-inner">
          <div class="breadcrumbs" style="margin-bottom:1.2em;">
            <a href="../index.html" class="breadcrumb-link w-inline-block"><img src="../images/home_black_24dp.svg" loading="lazy" alt="" class="breadcrumbs-home-icon"><div>Home</div></a>
            <img src="../images/arrow_right_black_24dp.svg" loading="lazy" alt="" class="breadcrumb-icon-right">
            <a href="../blog.html" class="breadcrumb-link w-inline-block"><div>Newsletter</div></a>
            <img src="../images/arrow_right_black_24dp.svg" loading="lazy" alt="" class="breadcrumb-icon-right">
            <span style="font-family:'Montserrat',sans-serif;font-size:0.85em;color:#555;">{_html.escape(label)}</span>
          </div>
          <iframe src="{pdf_path_rel}" title="{_html.escape(label)} Newsletter — Ben Lee Properties" loading="lazy">
            <div class="nl-fallback">
              <p>Your browser does not support embedded PDFs.</p>
              {dl_link}
            </div>
          </iframe>
          <div class="nl-nav">
            {prev_link}
            {dl_link}
            {next_link}
          </div>
        </div>
      </div>

<article class="nl-text-body" aria-label="Newsletter text content">
  <h2>Ben Lee Properties — {_html.escape(label)} Newsletter</h2>
  <p class="nl-text-meta">Issue: {_html.escape(label)} &nbsp;|&nbsp; Cheviot Hills &amp; Beverlywood, Los Angeles</p>
{main_html}{listings_section}{community_html}
</article>

      <section class="section grey-background">
        <div class="container w-container">
          <div class="padding-inner">
            <div class="flex-vertical">
              <h2>All Newsletters</h2>
              <a href="../blog.html" class="button w-inline-block">
                <p class="button-paragraph">View all issues</p>
                <img src="../images/arrow_right_white_24dp.svg" loading="lazy" alt="" class="button-arrow-right">
                <div class="button-background"></div>
              </a>
            </div>
          </div>
        </div>
      </section>
      <footer id="footer" class="footer blp-footer">
        <div class="blp-footer-inner">
          <div class="blp-footer-top">
            <div class="blp-footer-brand"><div class="blp-footer-name">Ben Lee</div><div class="blp-footer-tagline">Commercial Real Estate</div></div>
            <nav class="blp-footer-nav">
              <a href="../for-buyers-3.html" class="blp-footer-link">Buyer</a>
              <a href="../for-sellers.html" class="blp-footer-link">Seller</a>
              <a href="../about.html" class="blp-footer-link">About</a>
              <a href="../blog.html" class="blp-footer-link">Blog</a>
              <a href="../contact.html" class="blp-footer-link">Contact</a>
            </nav>
          </div>
          <div class="blp-footer-bottom">
            <span class="blp-footer-copy">&copy; 2026 Ben Lee Properties. All rights reserved.</span>
            <div class="blp-footer-contact-info">
              <a href="tel:+13107046580" class="blp-footer-contact-link">(310) 704-6580</a>
              <a href="mailto:ben@benleeproperties.com" class="blp-footer-contact-link">ben@benleeproperties.com</a>
            </div>
          </div>
        </div>
      </footer>
    </main>
    <div class="section-10">
      <div class="div-block-28">
        <a href="../contact.html" class="div-block-29 w-inline-block"><img width="45" height="45" alt="Contact" src="../images/pen.svg" loading="lazy" class="image-13"></a>
        <a href="tel:+13107046580" class="div-block-29 w-inline-block"><img width="45" height="45" alt="Call" src="../images/call-1.svg" loading="lazy" class="image-13"></a>
        <a href="mailto:ben@benleeproperties.com?subject=Email%20from%20website%20" class="div-block-29 right a w-inline-block"><img width="45" height="45" alt="Email" src="../images/email-1.svg" loading="lazy" class="image-13"></a>
      </div>
    </div>
  </div>
  <script src="https://d3e54v103j8qbb.cloudfront.net/js/jquery-3.5.1.min.dc5e7f18c8.js?site=68edca0dd75d0e01f9bfe38d" type="text/javascript" integrity="sha256-9/aliU8dGd2tb6OSsuzixeV4y/faTqgFtohetphbbj0=" crossorigin="anonymous"></script>
  <script src="../js/webflow.js" type="text/javascript"></script>
  <script src="../js/custom.js" type="text/javascript"></script>
</body>
</html>"""


# ── Load and sort newsletters ─────────────────────────────────────────────────

def load_newsletters():
    return json.load(open(DATA_FILE)) if os.path.exists(DATA_FILE) else []

def save_newsletters(data):
    tmp = DATA_FILE + '.tmp'
    json.dump(data, open(tmp, 'w'), indent=2)
    os.replace(tmp, DATA_FILE)

def git_commit_push(slugs):
    files = ['data/newsletters.json'] + [f'market-updates/{s}.html' for s in slugs]
    subprocess.run(['git', 'add'] + files, cwd=BASE, check=True)
    result = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=BASE)
    if result.returncode == 0:
        print('  (nothing to commit)')
        return
    msg = f'Add newsletter pages: {slugs[0]} – {slugs[-1]}'
    subprocess.run(['git', 'commit', '-m', msg], cwd=BASE, check=True)
    subprocess.run(['git', 'push', 'origin', 'main'], cwd=BASE, check=True)
    print(f'  Pushed: {msg}')


# ── Main ──────────────────────────────────────────────────────────────────────

start_key = None
force_regen = '--force' in sys.argv
if force_regen:
    print('Force mode: regenerating all pages with PDFs.')

if len(sys.argv) > 1 and '--start' in sys.argv[1]:
    val = sys.argv[1].split('=')[-1] if '=' in sys.argv[1] else (sys.argv[2] if len(sys.argv) > 2 else '')
    m = re.match(r'(\d{4})-(\d{2})', val)
    if m:
        start_key = (int(m.group(1)), int(m.group(2)))
        print(f'Resuming from {val}')

newsletters = load_newsletters()
# Build chronological list of ALL newsletters with a pdf
nl_with_pdf = sorted(
    [n for n in newsletters if n.get('pdf')],
    key=lambda n: (n['year'], n['month'])
)
# Index for prev/next lookup
nl_by_key = {(n['year'], n['month']): n for n in nl_with_pdf}
nl_sorted_keys = [(n['year'], n['month']) for n in nl_with_pdf]

# Also include newsletters that already have html_url in the prev/next chain
all_nl_sorted = sorted(newsletters, key=lambda n: (n['year'], n['month']))
all_nl_keys = [(n['year'], n['month']) for n in all_nl_sorted if n.get('html_url') or n.get('pdf')]

# Find newsletters needing HTML pages (or all, if --force)
to_process = nl_with_pdf if force_regen else [n for n in nl_with_pdf if not n.get('html_url')]

processed = 0
batch_slugs = []

for nl in to_process:
    year, month = nl['year'], nl['month']
    key = (year, month)

    if start_key and key < start_key:
        continue

    slug     = slug_for(year, month)
    html_out = os.path.join(MU_DIR, f'{slug}.html')
    html_url = f'/market-updates/{slug}'

    label = nl.get('label', f'{MONTH_NAMES[month]} {year}')
    pdf_name = nl.get('pdf', '').replace('documents/', '', 1)
    pdf_path = os.path.join(DOCS_DIR, pdf_name) if pdf_name else None

    print(f'\n{nl["id"]}  {label}')

    # Extract text
    main_paras, community_paras, listings = [], [], []
    if pdf_path and os.path.exists(pdf_path):
        pages = extract_pdf_text(pdf_path)
        main_paras, community_paras = extract_article_paragraphs(pages)
        listings = extract_listings(pages)
        print(f'  Text: {len(main_paras)} article / {len(community_paras)} community / {len(listings)} listings')
    else:
        print(f'  PDF not found: {pdf_path}')

    # Prev/next: look up position in full sorted newsletter list
    all_keys_with_url = [(n['year'], n['month']) for n in all_nl_sorted if n.get('html_url') or n.get('pdf')]
    try:
        pos = all_keys_with_url.index(key)
        prev_key = all_keys_with_url[pos - 1] if pos > 0 else None
        next_key = all_keys_with_url[pos + 1] if pos < len(all_keys_with_url) - 1 else None
    except ValueError:
        prev_key = next_key = None

    # Only link to neighbors that have html_url (or will have one)
    def has_or_will_have_url(k):
        if k is None: return False
        n = nl_by_key.get(k) or next((x for x in all_nl_sorted if (x['year'], x['month']) == k), None)
        return bool(n and (n.get('html_url') or n.get('pdf')))

    prev_slug_val = slug_for(*prev_key) if prev_key and has_or_will_have_url(prev_key) else None
    next_slug_val = slug_for(*next_key) if next_key and has_or_will_have_url(next_key) else None

    # Generate and write HTML
    html_content = generate_html(nl, main_paras, community_paras, listings, prev_slug_val, next_slug_val)
    with open(html_out, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f'  Written → {slug}.html')

    # Update json
    nl['html_url'] = html_url
    save_newsletters(newsletters)

    processed += 1
    batch_slugs.append(slug)

    if len(batch_slugs) >= 3:
        git_commit_push(batch_slugs)
        batch_slugs = []

if batch_slugs:
    git_commit_push(batch_slugs)

print(f'\nDone. Generated {processed} newsletter pages.')
print('Rebuild search index by restarting the server (build_newsletter_search_index runs at startup).')
