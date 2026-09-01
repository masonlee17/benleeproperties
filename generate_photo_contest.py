#!/usr/bin/env python3
"""Generate the Summer 2026 Photo Contest showcase page (root: summer-2026-photo-contest.html).

Reader submissions are shown by name only — personal emails from the source PDF are
deliberately never published. Winner: Craig Silvers (Egypt), featured prominently.
"""
import os, html

BASE = os.path.dirname(os.path.abspath(__file__))
from generate_city_pages import NAVBAR, FOOTER, FLOATING_BTNS

# Page lives at site root, so use absolute-root asset paths (same transform the
# city generator applies when it writes files).
NAV   = NAVBAR.replace('../', '/')
FOOT  = FOOTER.replace('../', '/')
FLOAT = FLOATING_BTNS.replace('../', '/')

CANONICAL = "https://www.benleeproperties.com/summer-2026-photo-contest"

WINNER = {
    "name": "Craig Silvers",
    "location": "The Pyramids of Giza, Egypt",
    "img": "images/photo-contest/01-craig-silvers.jpg",
    "copy": ("Craig carried the Ben Lee newsletter all the way to the Pyramids of Giza. "
             "A worthy winner of the Summer 2026 contest — congratulations, Craig!"),
}

# name only — no emails, ever. (order follows the submission PDF)
SUBMISSIONS = [
    {"name": "Scot Ganulin",        "imgs": ["images/photo-contest/02-scot-ganulin.jpg"]},
    {"name": "Lynn Lempert",        "imgs": ["images/photo-contest/03-lynn-lempert.jpg"]},
    {"name": "Jacqueline Shulman",  "imgs": ["images/photo-contest/04-jacqueline-shulman-0.jpg",
                                             "images/photo-contest/04-jacqueline-shulman-1.jpg"]},
    {"name": "Ben Adler",           "imgs": ["images/photo-contest/05-ben-adler.jpg"]},
    {"name": "Christina Hufnagel",  "imgs": ["images/photo-contest/06-christina-hufnagel-0.jpg",
                                             "images/photo-contest/06-christina-hufnagel-1.jpg"]},
    {"name": "Dan Sherkow",         "imgs": ["images/photo-contest/07-dan-sherkow.jpg"]},
    {"name": "Sylvia Ortiz",        "imgs": ["images/photo-contest/08-sylvia-ortiz-0.jpg",
                                             "images/photo-contest/08-sylvia-ortiz-1.jpg"]},
    {"name": "Jamie Thai",          "imgs": ["images/photo-contest/09-jamie-thai.jpg"]},
    {"name": "Judy & Gary Bratman", "imgs": ["images/photo-contest/10-judy-bratman-gary-bratman.jpg"]},
    {"name": "Jillian Harris",      "imgs": ["images/photo-contest/11-jillian-harris.jpg"]},
    {"name": "Katariina Kiuru",     "imgs": ["images/photo-contest/12-katariina-kiuru.jpg"]},
    {"name": "Brenda Johnson",      "imgs": ["images/photo-contest/13-brenda-johnson.jpg"]},
]


def gallery_tiles():
    out = []
    for s in SUBMISSIONS:
        name = html.escape(s["name"])
        for src in s["imgs"]:
            out.append(
                f'''          <figure class="pc-item">
            <img src="{src}" loading="lazy" alt="Photo contest submission by {name}">
            <figcaption class="pc-cap">{name}</figcaption>
          </figure>''')
    return "\n".join(out)


PAGE = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Summer 2026 Photo Contest | Ben Lee Properties</title>
  <meta name="description" content="See the winners and all reader submissions from the Ben Lee Properties Summer 2026 Photo Contest — the newsletter travels from the Pyramids of Egypt to the beaches of California.">
  <meta name="robots" content="index, follow">
  <meta name="author" content="Ben Lee Properties">
  <link rel="canonical" href="{CANONICAL}">

  <!-- Open Graph -->
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Ben Lee Properties">
  <meta property="og:title" content="Summer 2026 Photo Contest | Ben Lee Properties">
  <meta property="og:description" content="The winners and all reader submissions from the Ben Lee Properties Summer 2026 Photo Contest.">
  <meta property="og:url" content="{CANONICAL}">
  <meta property="og:image" content="https://www.benleeproperties.com/{WINNER['img']}">
  <meta property="og:locale" content="en_US">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Summer 2026 Photo Contest | Ben Lee Properties">
  <meta name="twitter:image" content="https://www.benleeproperties.com/{WINNER['img']}">

  <meta content="width=device-width, initial-scale=1" name="viewport">
  <link href="/css/normalize.css" rel="stylesheet" type="text/css">
  <link href="/css/webflow.css" rel="stylesheet" type="text/css">
  <link href="/css/ben-lee-properties.webflow.css" rel="stylesheet" type="text/css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
  <script type="text/javascript">!function(o,c){{var n=c.documentElement,t=" w-mod-";n.className+=t+"js",("ontouchstart"in o||o.DocumentTouch&&c instanceof DocumentTouch)&&(n.className+=t+"touch")}}(window,document);</script>
  <link href="/images/favicon.png" rel="shortcut icon" type="image/x-icon">
  <link href="/images/webclip.png" rel="apple-touch-icon">
  <style>
    .pc-hero {{background:linear-gradient(135deg,#07264b 0%,#1d3fa0 100%);color:#fff;padding:96px 24px 88px;text-align:center;}}
    .pc-hero-inner {{max-width:820px;margin:0 auto;}}
    .pc-eyebrow {{font-family:'Montserrat',sans-serif;font-weight:700;letter-spacing:.18em;text-transform:uppercase;font-size:.72em;color:#c8a24a;margin:0 0 14px;}}
    .pc-title {{font-family:'Montserrat',sans-serif;font-weight:800;font-size:2.9em;line-height:1.08;margin:0 0 18px;letter-spacing:-.01em;}}
    .pc-sub {{font-family:'Montserrat',sans-serif;font-weight:400;font-size:1.02em;line-height:1.7;color:#dbe4f5;margin:0;}}

    .pc-winner-section {{background:#f5f7fb;padding:64px 24px;}}
    .pc-winner-card {{max-width:1040px;margin:0 auto;background:#fff;border:1px solid #ecebe4;border-radius:10px;overflow:hidden;box-shadow:0 12px 40px rgba(7,38,75,.10);display:grid;grid-template-columns:1.15fr .85fr;}}
    .pc-winner-photo {{position:relative;min-height:340px;background:#07264b;}}
    .pc-winner-photo img {{width:100%;height:100%;object-fit:cover;display:block;}}
    .pc-winner-badge {{position:absolute;top:18px;left:18px;background:#c8a24a;color:#1a1305;font-family:'Montserrat',sans-serif;font-weight:800;font-size:.74em;letter-spacing:.12em;text-transform:uppercase;padding:8px 16px;border-radius:2px;box-shadow:0 3px 12px rgba(0,0,0,.25);}}
    .pc-winner-info {{padding:44px 40px;display:flex;flex-direction:column;justify-content:center;font-family:'Montserrat',sans-serif;}}
    .pc-winner-label {{font-weight:700;letter-spacing:.14em;text-transform:uppercase;font-size:.72em;color:#1d3fa0;margin:0 0 10px;}}
    .pc-winner-name {{font-weight:800;font-size:2em;color:#07264b;margin:0 0 6px;line-height:1.1;}}
    .pc-winner-loc {{font-weight:600;font-size:1em;color:#c8a24a;margin:0 0 18px;}}
    .pc-winner-copy {{font-weight:400;font-size:.95em;line-height:1.7;color:#444;margin:0;}}

    .pc-gallery-section {{max-width:1160px;margin:0 auto;padding:72px 24px 40px;font-family:'Montserrat',sans-serif;}}
    .pc-gallery-title {{text-align:center;font-weight:800;font-size:1.7em;color:#07264b;margin:0 0 8px;}}
    .pc-gallery-sub {{text-align:center;font-weight:400;font-size:.95em;color:#777;margin:0 0 44px;}}
    .pc-gallery {{column-count:3;column-gap:18px;}}
    .pc-item {{break-inside:avoid;margin:0 0 18px;border-radius:8px;overflow:hidden;background:#fff;border:1px solid #ecebe4;box-shadow:0 4px 16px rgba(7,38,75,.07);}}
    .pc-item img {{width:100%;display:block;}}
    .pc-cap {{font-family:'Montserrat',sans-serif;font-weight:600;font-size:.82em;color:#07264b;padding:12px 14px;letter-spacing:.02em;}}

    @media (max-width:900px) {{
      .pc-winner-card {{grid-template-columns:1fr;}}
      .pc-winner-photo {{min-height:300px;}}
      .pc-gallery {{column-count:2;}}
      .pc-title {{font-size:2.2em;}}
    }}
    @media (max-width:560px) {{
      .pc-gallery {{column-count:1;}}
      .pc-hero {{padding:72px 20px 64px;}}
      .pc-winner-info {{padding:32px 26px;}}
    }}
  </style>
</head>
<body>
  <div class="page-wrapper">
{NAV}
    <main class="main">
      <section class="pc-hero">
        <div class="pc-hero-inner">
          <p class="pc-eyebrow">Ben Lee Properties &middot; Reader Photo Contest</p>
          <h1 class="pc-title">Summer 2026 Photo Contest</h1>
          <p class="pc-sub">Every summer, our readers take the Ben Lee newsletter with them wherever they go and send us the proof. Here are this year&#39;s submissions &mdash; from the Pyramids of Egypt to the beaches of California.</p>
        </div>
      </section>

      <section class="pc-winner-section">
        <div class="pc-winner-card">
          <div class="pc-winner-photo">
            <img src="{WINNER['img']}" alt="Winning photo by {html.escape(WINNER['name'])} at {html.escape(WINNER['location'])}">
            <span class="pc-winner-badge">&#9733; Winner</span>
          </div>
          <div class="pc-winner-info">
            <p class="pc-winner-label">This Year&#39;s Winner</p>
            <h2 class="pc-winner-name">{html.escape(WINNER['name'])}</h2>
            <p class="pc-winner-loc">{html.escape(WINNER['location'])}</p>
            <p class="pc-winner-copy">{html.escape(WINNER['copy'])}</p>
          </div>
        </div>
      </section>

      <section class="pc-gallery-section">
        <h2 class="pc-gallery-title">All Submissions</h2>
        <p class="pc-gallery-sub">Thank you to everyone who entered this summer.</p>
        <div class="pc-gallery">
{gallery_tiles()}
        </div>
      </section>

      <div class="inquiry-call-to-action">
        <div class="container w-container">
          <div class="footer-contact">
            <p class="footer-contact-title">Want to be in next year&#39;s contest?</p>
            <a href="/blog.html" class="button w-inline-block">
              <p class="button-paragraph">Read the Newsletter</p>
              <img src="/images/arrow_right_white_24dp.svg" loading="lazy" alt="" class="button-arrow-right">
              <div class="button-background dark-blue-color"></div>
            </a>
          </div>
        </div>
      </div>

{FOOT}
    </main>
{FLOAT}
  </div>
  <script src="https://d3e54v103j8qbb.cloudfront.net/js/jquery-3.5.1.min.dc5e7f18c8.js?site=68edca0dd75d0e01f9bfe38d" type="text/javascript" integrity="sha256-9/aliU8dGd2tb6OSsuzixeV4y/faTqgFtohetphbbj0=" crossorigin="anonymous"></script>
  <script src="/js/webflow.js" type="text/javascript"></script>
  <script src="/js/custom.js" type="text/javascript"></script>
</body>
</html>"""


if __name__ == '__main__':
    out = os.path.join(BASE, 'summer-2026-photo-contest.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(PAGE)
    print(f"WROTE: summer-2026-photo-contest.html ({len(PAGE)} bytes, {len(SUBMISSIONS)} submitters + winner)")
