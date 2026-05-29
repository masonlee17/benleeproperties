#!/usr/bin/env python3
"""
Import newsletter PDFs from desktop into the project chronologically.
For each newsletter: copy PDF → documents/, extract cover → images/nl-covers/,
update newsletters.json. Git commit + push every 3 newsletters.

Usage:  python3 import_newsletters.py
Resume: python3 import_newsletters.py --start 2019-03
"""
import os, sys, re, json, shutil, subprocess, calendar
import fitz  # PyMuPDF

BASE      = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR  = os.path.join(BASE, 'documents')
IMGS_DIR  = os.path.join(BASE, 'images', 'nl-covers')
DATA_FILE = os.path.join(BASE, 'data', 'newsletters.json')

DESKTOPS = [
    '/Users/lillilee/Desktop/Ben Lee Properties 2/Ben Lee Properties',
    '/Users/lillilee/Desktop/Ben Lee Properties/Ben Lee Properties',
]

MONTHS = {
    'January':1,'February':2,'March':3,'April':4,'May':5,'June':6,
    'July':7,'August':8,'September':9,'October':10,'November':11,'December':12
}

os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(IMGS_DIR, exist_ok=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def parse_month_folder(name):
    m = re.match(r'(\w+)\s+(\d{4})', name.strip())
    if m and m.group(1) in MONTHS:
        return int(m.group(2)), MONTHS[m.group(1)]
    return None

def find_first_pdf(folder):
    """Return the first PDF alphabetically (recursive, prefer Digital/ subfolders)."""
    pdfs = []
    for root, dirs, files in os.walk(folder):
        dirs.sort()
        for f in sorted(files):
            if f.lower().endswith('.pdf'):
                pdfs.append(os.path.join(root, f))
    return pdfs[0] if pdfs else None

def extract_cover(pdf_path, cover_path):
    """Render page 1 of pdf as JPEG to cover_path. Return True on success."""
    try:
        doc = fitz.open(pdf_path)
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        # Convert CMYK → RGB if needed
        if pix.colorspace and pix.colorspace.n > 3:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        pix.save(cover_path)
        doc.close()
        return True
    except Exception as e:
        print(f'    cover extract error: {e}')
        return False

def load_newsletters():
    return json.load(open(DATA_FILE)) if os.path.exists(DATA_FILE) else []

def save_newsletters(data):
    tmp = DATA_FILE + '.tmp'
    json.dump(data, open(tmp, 'w'), indent=2)
    os.replace(tmp, DATA_FILE)

def git_commit_push(msg):
    subprocess.run(['git', 'add', 'documents/', 'images/nl-covers/', 'data/newsletters.json'],
                   cwd=BASE, check=True)
    result = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=BASE)
    if result.returncode == 0:
        print('  (nothing to commit, skipping push)')
        return
    subprocess.run(['git', 'commit', '-m', msg], cwd=BASE, check=True)
    subprocess.run(['git', 'push', 'origin', 'main'], cwd=BASE, check=True)
    print(f'  Pushed: {msg}')


# ── Build the chronological list of desktop newsletters ──────────────────────

desktop_map = {}   # (year, month) → folder_path
for base in DESKTOPS:
    if not os.path.isdir(base):
        continue
    for name in sorted(os.listdir(base)):
        key = parse_month_folder(name)
        if not key:
            continue
        folder = os.path.join(base, name)
        if not os.path.isdir(folder):
            continue
        if key not in desktop_map:   # first-found wins (Ben Lee Properties 2 listed first)
            desktop_map[key] = folder

# ── Determine start point from CLI arg ───────────────────────────────────────

start_key = None
if len(sys.argv) > 1 and sys.argv[1].startswith('--start'):
    val = sys.argv[1].split('=')[-1] if '=' in sys.argv[1] else (sys.argv[2] if len(sys.argv) > 2 else '')
    m = re.match(r'(\d{4})-(\d{2})', val)
    if m:
        start_key = (int(m.group(1)), int(m.group(2)))
        print(f'Resuming from {val}')

# ── Process newsletters chronologically ─────────────────────────────────────

newsletters = load_newsletters()
nl_index = {n['id']: n for n in newsletters}

processed = 0
batch     = []

for key in sorted(desktop_map):
    year, month = key

    if start_key and key < start_key:
        continue

    nid = f'nl-{year}-{month:02d}'

    # Skip if already has both pdf and cover
    existing = nl_index.get(nid, {})
    if existing.get('pdf') and existing.get('cover'):
        continue

    folder = desktop_map[key]
    pdf_src = find_first_pdf(folder)
    if not pdf_src:
        print(f'  SKIP {nid}: no PDF found in {folder}')
        continue

    # Destination paths
    pdf_dst_name = f'{month:02d}-{year}.pdf'
    pdf_dst      = os.path.join(DOCS_DIR, pdf_dst_name)
    cover_name   = f'{nid}.jpg'
    cover_dst    = os.path.join(IMGS_DIR, cover_name)
    pdf_rel      = f'documents/{pdf_dst_name}'
    cover_rel    = f'images/nl-covers/{cover_name}'

    print(f'\n{nid}  {os.path.basename(pdf_src)}')

    # Copy PDF (skip if already in documents/)
    if not os.path.exists(pdf_dst):
        shutil.copy2(pdf_src, pdf_dst)
        print(f'  Copied PDF → {pdf_dst_name}')
    else:
        print(f'  PDF already exists: {pdf_dst_name}')
        pdf_rel = f'documents/{pdf_dst_name}'

    # Extract cover image
    if not os.path.exists(cover_dst):
        ok = extract_cover(pdf_dst, cover_dst)
        print(f'  Cover {"extracted" if ok else "FAILED"} → {cover_name}')
        if not ok:
            cover_rel = ''
    else:
        print(f'  Cover already exists: {cover_name}')

    # Update newsletters.json entry
    label = f'{calendar.month_name[month]} {year}'
    if nid in nl_index:
        nl_index[nid]['pdf']   = pdf_rel
        nl_index[nid]['label'] = label
        if cover_rel:
            nl_index[nid]['cover'] = cover_rel
    else:
        entry = {'id': nid, 'label': label, 'year': year, 'month': month,
                 'pdf': pdf_rel, 'cover': cover_rel, 'html_url': ''}
        nl_index[nid] = entry
        newsletters.append(entry)

    save_newsletters(sorted(newsletters, key=lambda n: (n['year'], n['month']), reverse=True))
    processed += 1
    batch.append(nid)

    # Push every 3
    if len(batch) >= 3:
        git_commit_push(f'Add newsletter PDFs and covers: {batch[0]} – {batch[-1]}')
        batch = []

# Final push if remainder
if batch:
    git_commit_push(f'Add newsletter PDFs and covers: {batch[0]} – {batch[-1]}')

print(f'\nDone. Processed {processed} newsletters.')
