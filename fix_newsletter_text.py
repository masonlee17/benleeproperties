#!/usr/bin/env python3
"""Reflow newsletter text-version article bodies (This Month's Article +
Community & More) from the source PDFs into clean, multi-sentence paragraphs.

Fixes drop-cap artifacts (W hen -> When), stray single-letter merges, line-break
de-hyphenation, and mis-extracted em-dashes; groups sentences into real paragraphs
instead of one line per sentence.

Reusable:
    python3 fix_newsletter_text.py 2025 2026     # specific years
    python3 fix_newsletter_text.py               # all newsletters with a local PDF
"""
import fitz, re, json, html as H, os, sys, subprocess

def flowing(pdf, page_index):
    """Return the page's text as one clean flowing string (or '' if page absent)."""
    d = fitz.open(pdf)
    if page_index >= len(d):
        return ''
    raw = []
    for blk in d[page_index].get_text('dict')['blocks']:
        if blk.get('type') != 0:
            continue
        for ln in blk['lines']:
            t = ''.join(s['text'] for s in ln['spans'])
            # skip the footer boilerplate line wherever it appears (top or bottom)
            if t.strip() and not re.match(r'BEN LEE\s*[–—-]', t.strip()):
                raw.append(t)
    if not raw:
        return ''
    # drop-cap: a lone uppercase letter line -> prefix onto the next line
    merged = []; i = 0
    while i < len(raw):
        st = raw[i].strip()
        if len(st) == 1 and st.isalpha() and st.isupper() and i + 1 < len(raw):
            merged.append(st + raw[i + 1].lstrip()); i += 2
        else:
            merged.append(raw[i]); i += 1
    # join lines: de-hyphenate genuine lowercase word splits, else join with a space
    p = merged[0]
    for seg in merged[1:]:
        m = re.search(r'([A-Za-z]+)-$', p)
        p = p[:-1] + seg.lstrip() if (m and m.group(1).islower()) else p.rstrip() + ' ' + seg.lstrip()
    p = re.sub(r'\s+', ' ', p).strip()
    p = re.sub(r'(\w)- (\w)', r'\1—\2', p)          # mis-extracted em-dash
    p = re.sub(r'^By Ben Lee\s+', '', p)             # drop byline
    return p

def paragraphs(text, min_sentences=4, min_chars=300):
    if not text:
        return []
    sents = re.split(r'(?<=[.!?])\s+(?=[A-Z“‘"])', text)
    out, cur = [], []
    for s in sents:
        cur.append(s)
        if len(cur) >= min_sentences and len(' '.join(cur)) > min_chars:
            out.append(' '.join(cur)); cur = []
    if cur:
        out.append(' '.join(cur))
    return out

def body_html(ps):
    return '\n'.join(f'  <p>{H.escape(x)}</p>' for x in ps)

SECTION = lambda title: re.compile(
    r'(<p class="nl-text-section-title">' + title +
    r'</p>\n)(.*?)(?=\n  <p class="nl-text-section-title">|\n</article>)', re.DOTALL)
MAIN_RE = SECTION(r"This Month(?:&#x27;|')s Article")
COMM_RE = SECTION(r"Community &amp; More")

def _push(files):
    """Commit + push a batch of fixed files so progress is saved incrementally."""
    if not files:
        return
    subprocess.run(['git', 'add', *files], check=True)
    msg = (f"Newsletter text: reflow batch of {len(files)}\n\n"
           "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>")
    subprocess.run(['git', 'commit', '-q', '-m', msg], check=True)
    subprocess.run(['git', 'push', 'origin', 'main'], check=True)
    print(f"  >>> pushed {len(files)} files")

def run(years, push_every=0):
    nls = json.load(open('data/newsletters.json'))
    fixed = 0
    batch = []
    for n in sorted(nls, key=lambda x: (x.get('year', 0), x.get('month', 0))):
        if years and n.get('year') not in years:
            continue
        pdf, url = n.get('pdf', ''), n.get('html_url', '')
        if not (pdf and os.path.isfile(pdf) and url):
            continue
        slug = url.rstrip('/').split('/')[-1]
        f = f'market-updates/{slug}.html'
        if not os.path.isfile(f):
            continue
        s = orig = open(f, encoding='utf-8').read()
        mp = paragraphs(flowing(pdf, 1))          # page 2 = main article
        cp = paragraphs(flowing(pdf, 3))          # page 4 = community
        if mp and MAIN_RE.search(s):
            s = MAIN_RE.sub(lambda m: m.group(1) + body_html(mp), s, count=1)
        if cp and COMM_RE.search(s):
            s = COMM_RE.sub(lambda m: m.group(1) + body_html(cp), s, count=1)
        if s != orig:
            open(f, 'w', encoding='utf-8').write(s)
            fixed += 1
            batch.append(f)
            print(f"  {slug}: main={len(mp)}p  community={len(cp)}p")
            if push_every and len(batch) >= push_every:
                _push(batch); batch = []
    if push_every:
        _push(batch)
    print(f"Reflowed {fixed} newsletters.")

if __name__ == '__main__':
    args = sys.argv[1:]
    push_every = 10 if '--push' in args else 0
    years = set(int(a) for a in args if a.isdigit()) or None
    run(years, push_every)
