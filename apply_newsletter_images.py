#!/usr/bin/env python3
"""
Map extracted newsletter images to deal properties in properties.json.
Uses position-based matching: sorts properties and images by x within each row,
then assigns them in left-to-right reading order.

Run:  python3 apply_newsletter_images.py
"""
import fitz, re, json, os

BASE     = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE, 'documents')
DATA_DIR = os.path.join(BASE, 'data')
OUT_DIR  = os.path.join(BASE, 'images', 'newsletter-extracts')

MIN_PX    = 250
MIN_RATIO = 0.3
ROW_SNAP  = 80   # images within this many pixels of y are in the same row

H1_PDFS = [
    ('2025', '01', '01-2025.pdf'),
    ('2025', '02', '02-2025.pdf'),
    ('2025', '03', '03-2025.pdf'),
    ('2025', '04', '04-2025.pdf'),
    ('2025', '05', '05-2025.pdf'),
    ('2025', '06', '06-2025.pdf'),
]

ADDR_RE = re.compile(
    r'(\d+\s+[\w.]+(?:\s+[\w.]+){0,4}?\s*'
    r'(?:Ave|Dr|Pl|St|Blvd|Rd|Way|Ct|Ln|Circle|Ter|Place|Street|Cir|Canyon|Drive|Avenue|Boulevard|Road|Court|Lane))'
    r'[\w\s.#-]*',
    re.IGNORECASE
)

def normalize(addr):
    return re.sub(r'\s+', ' ', addr.lower().strip().rstrip('.,- '))


def get_page3_images(doc, year, month):
    """Return list of {file, path, cx, cy} for all qualifying images on page 3."""
    seen = set()
    global_idx = 0
    result = []
    for pg_i, pg in enumerate(doc):
        for img_info in pg.get_images(full=True):
            xref = img_info[0]
            if xref in seen:
                continue
            seen.add(xref)
            pix = fitz.Pixmap(doc, xref)
            w, h = pix.width, pix.height
            pix = None
            if w < MIN_PX or h < MIN_PX or min(w, h) / max(w, h) < MIN_RATIO:
                continue
            global_idx += 1
            fname = f'nl-{year}-{month}-p{pg_i+1:02d}-i{global_idx:02d}.jpg'
            if pg_i == 2:
                rects = pg.get_image_rects(xref)
                for r in rects:
                    result.append({'file': fname,
                                   'path': f'images/newsletter-extracts/{fname}',
                                   'cx': (r.x0 + r.x1) / 2,
                                   'cy': (r.y0 + r.y1) / 2})
    return result


def get_page3_properties(doc):
    """Return list of {addr, x0} for property addresses found on page 3."""
    page = doc[2]
    props = []
    seen_addrs = set()
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines', []):
            full_line = ' '.join(s['text'] for s in line.get('spans', []))
            m = ADDR_RE.search(full_line)
            if not m:
                continue
            raw = m.group(0).strip()
            norm = normalize(raw)
            if norm in seen_addrs or len(norm) < 8:
                continue
            seen_addrs.add(norm)
            x0 = line['spans'][0]['bbox'][0] if line.get('spans') else block['bbox'][0]
            props.append({'addr': norm, 'raw': raw, 'x0': x0})
    return props


def match_by_row(img_list, prop_list):
    """Group images into rows, group properties into matching rows, then match L→R."""
    if not img_list or not prop_list:
        return []

    # Bucket images into rows by cy
    rows = []
    for img in sorted(img_list, key=lambda i: i['cy']):
        placed = False
        for row in rows:
            if abs(img['cy'] - row[0]['cy']) < ROW_SNAP:
                row.append(img)
                placed = True
                break
        if not placed:
            rows.append([img])

    # Sort images within each row by cx (left → right)
    for row in rows:
        row.sort(key=lambda i: i['cx'])

    # Flatten: assign a "slot" index to each image
    flat_imgs = [(slot_i, img) for slot_i, img in enumerate(img for row in rows for img in row)]

    # Sort properties by x0 within each approximate y band, then by y band
    # Bin properties into y bands matching the image rows
    def prop_row(p):
        for ri, row in enumerate(rows):
            if row:
                # rough y midpoint of row (offset by ~150px since text is below image)
                row_cy = row[0]['cy']
                if -50 < (p['x0'] - 0) >= 0:  # any x is ok; check by slot assignment
                    pass
        return 0

    props_sorted = sorted(prop_list, key=lambda p: p['x0'])

    # Simple approach: sort images L→R across the page, sort props by x0, zip
    all_imgs_lr = [img for row in rows for img in row]
    matches = list(zip(props_sorted, all_imgs_lr))
    return matches


def load_json(name):
    for base in (DATA_DIR, BASE):
        p = os.path.join(base, name)
        if os.path.exists(p):
            return json.load(open(p))
    return []


def save_json(name, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, name)
    tmp = path + '.tmp'
    json.dump(data, open(tmp, 'w'), indent=2)
    os.replace(tmp, path)


# ── Build the full mapping: addr_norm → image_path ──────────────────────────

addr_to_img = {}  # addr_norm → first newsletter image found

for year, month, pdf_name in H1_PDFS:
    pdf_path = os.path.join(DOCS_DIR, pdf_name)
    if not os.path.exists(pdf_path):
        print(f'  SKIP (missing): {pdf_name}')
        continue

    doc = fitz.open(pdf_path)
    images = get_page3_images(doc, year, month)
    props  = get_page3_properties(doc)
    doc.close()

    matches = match_by_row(images, props)
    print(f'\n{pdf_name}  ({len(props)} props, {len(images)} images on p3):')
    for prop, img in matches:
        key = prop['addr']
        if key not in addr_to_img:
            addr_to_img[key] = img['path']
        status = '(new)' if key not in addr_to_img else '(already set)'
        print(f'  {prop["raw"]:35} → {img["file"]}')


# ── Update properties.json ───────────────────────────────────────────────────

properties = load_json('properties.json')
updated = 0

def find_img_for_prop(p):
    addr = normalize(p.get('address', ''))
    # Direct match
    if addr in addr_to_img:
        return addr_to_img[addr]
    # Partial: strip unit numbers or abbreviation differences
    addr_num = addr.split()[0] if addr.split() else ''
    for key, img_path in addr_to_img.items():
        key_num = key.split()[0] if key.split() else ''
        if addr_num and addr_num == key_num:
            # Check that street name also overlaps
            addr_words = set(addr.split()[1:])
            key_words  = set(key.split()[1:])
            if addr_words & key_words:
                return img_path
    return None

print('\n── Updating properties.json ──')
for p in properties:
    img_path = find_img_for_prop(p)
    if not img_path:
        continue
    # Only assign if the property has no image OR currently has an external CDN image
    current = p.get('image1', '')
    if current and not current.startswith('http'):
        print(f'  SKIP (already has local image): {p["address"]}')
        continue
    p['image1'] = img_path
    if p.get('image2', '').startswith('http'):
        p['image2'] = ''   # clear the second CDN image; can be reassigned manually
    verb = 'REPLACED CDN' if current.startswith('http') else 'ASSIGNED'
    print(f'  {verb}: {p["address"]:35} → {img_path}')
    updated += 1

save_json('properties.json', properties)
print(f'\nDone. {updated} properties updated.')
