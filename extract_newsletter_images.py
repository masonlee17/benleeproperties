#!/usr/bin/env python3
"""
Extract property images from H1 2025 newsletter PDFs (Jan–Jun 2025).
Saves sizeable images to images/newsletter-extracts/ and prints a summary.

Usage:  python3 extract_newsletter_images.py
"""
import os, json
import fitz  # PyMuPDF

BASE      = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR  = os.path.join(BASE, 'documents')
OUT_DIR   = os.path.join(BASE, 'images', 'newsletter-extracts')
MIN_PX    = 250   # skip images smaller than this in either dimension (logos, icons)
MIN_RATIO = 0.3   # skip images with extreme aspect ratio (e.g. thin horizontal banners)

H1_PDFS = [
    ('2025', '01', '01-2025.pdf'),
    ('2025', '02', '02-2025.pdf'),
    ('2025', '03', '03-2025.pdf'),
    ('2025', '04', '04-2025.pdf'),
    ('2025', '05', '05-2025.pdf'),
    ('2025', '06', '06-2025.pdf'),
]

os.makedirs(OUT_DIR, exist_ok=True)

saved = []   # list of relative paths we write

for year, month, pdf_name in H1_PDFS:
    pdf_path = os.path.join(DOCS_DIR, pdf_name)
    if not os.path.exists(pdf_path):
        print(f'  SKIP (missing): {pdf_name}')
        continue

    doc     = fitz.open(pdf_path)
    seen    = set()   # dedup by xref
    img_idx = 0

    for page_num, page in enumerate(doc, start=1):
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            if xref in seen:
                continue
            seen.add(xref)

            try:
                pix = fitz.Pixmap(doc, xref)
            except Exception:
                continue

            w, h = pix.width, pix.height

            # Size filter
            if w < MIN_PX or h < MIN_PX:
                pix = None
                continue

            # Aspect ratio filter (skip very long thin banners)
            ratio = min(w, h) / max(w, h)
            if ratio < MIN_RATIO:
                pix = None
                continue

            # Convert CMYK / DeviceN → RGB so JPEG export works
            if pix.colorspace and pix.colorspace.n > 3:
                pix = fitz.Pixmap(fitz.csRGB, pix)

            img_idx += 1
            fname    = f'nl-{year}-{month}-p{page_num:02d}-i{img_idx:02d}.jpg'
            out_path = os.path.join(OUT_DIR, fname)
            pix.save(out_path)
            rel_path = f'images/newsletter-extracts/{fname}'
            saved.append({'file': fname, 'path': rel_path,
                          'pdf': pdf_name, 'page': page_num,
                          'w': w, 'h': h})
            print(f'  Saved {fname}  ({w}x{h})')
            pix = None

    doc.close()

print(f'\n{len(saved)} images extracted to {OUT_DIR}')

# Write a manifest so you can reference paths later
manifest_path = os.path.join(OUT_DIR, 'manifest.json')
with open(manifest_path, 'w') as f:
    json.dump(saved, f, indent=2)
print(f'Manifest: {manifest_path}')
