#!/usr/bin/env python3
"""
Injects fully-optimized SEO meta blocks into every Ben Lee Properties HTML page.
Run once: python3 update_meta.py
"""
import re, os

BASE = os.path.dirname(os.path.abspath(__file__))
DOMAIN = "https://www.benleeproperties.com"
OG_IMAGE = f"{DOMAIN}/images/BLK-09766.jpg"

# ── Per-page configuration ───────────────────────────────────────────────────
PAGES = {
    "index.html": {
        "title": "Ben Lee Properties | #1 Cheviot Hills & Beverlywood Real Estate Agent in LA",
        "description": "Ben Lee is Beverly Hills' top-ranked real estate broker and licensed attorney. Serving Cheviot Hills, Beverlywood, and West LA with over $100M in closed transactions. Call (310) 704-6580.",
        "keywords": "Cheviot Hills real estate agent, Beverlywood realtor, Beverly Hills broker, Los Angeles luxury homes, top real estate agent LA, Ben Lee Properties, homes for sale Cheviot Hills",
        "canonical": f"{DOMAIN}/",
        "h1": None,
        "schema": """  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": ["RealEstateAgent", "LocalBusiness"],
    "name": "Ben Lee Properties",
    "description": "Ben Lee is the #1 real estate broker in Cheviot Hills and Beverlywood, Los Angeles. Principal Realtor and licensed attorney with over $100M in closed transactions.",
    "url": "https://www.benleeproperties.com",
    "logo": "https://www.benleeproperties.com/images/favicon.png",
    "image": "https://www.benleeproperties.com/images/BLK-09766.jpg",
    "telephone": "+13107046580",
    "email": "ben@benleeproperties.com",
    "address": {"@type": "PostalAddress", "streetAddress": "9454 Wilshire Blvd", "addressLocality": "Beverly Hills", "addressRegion": "CA", "postalCode": "90212", "addressCountry": "US"},
    "areaServed": [
      {"@type": "Place", "name": "Cheviot Hills, Los Angeles"},
      {"@type": "Place", "name": "Beverlywood, Los Angeles"},
      {"@type": "Place", "name": "Beverly Hills"},
      {"@type": "Place", "name": "West Los Angeles"},
      {"@type": "Place", "name": "Bel Air"},
      {"@type": "Place", "name": "Brentwood"}
    ],
    "sameAs": ["https://www.instagram.com/benleerealestate", "https://www.linkedin.com/in/benlee"],
    "priceRange": "$$$",
    "openingHours": "Mo-Fr 09:00-18:00",
    "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Real Estate Services", "itemListElement": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Home Buying"}}, {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Home Selling"}}, {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Custom Home Development"}}]}
  }
  </script>""",
    },
    "for-buyers-3.html": {
        "title": "Homes for Sale & Lease in Los Angeles | Ben Lee Properties – Current Listings",
        "description": "Browse Ben Lee's current Los Angeles property listings — from luxury estates in Cheviot Hills to beachfront leases in Oxnard. Expert buyer representation from LA's top broker-attorney. Call (310) 704-6580.",
        "keywords": "homes for sale Los Angeles, Cheviot Hills homes, Beverlywood real estate, luxury homes LA, properties for sale West LA, Ben Lee listings, homes for lease Los Angeles",
        "canonical": f"{DOMAIN}/for-buyers-3",
        "h1": "Ben Lee Current Listings",
        "schema": """  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"ItemList","name":"Ben Lee Properties – Current Listings","description":"Current homes for sale and lease represented by Ben Lee, Beverly Hills' #1 real estate broker.","url":"https://www.benleeproperties.com/for-buyers-3","numberOfItems":5,"itemListElement":[{"@type":"ListItem","position":1,"name":"16879 Mooncrest Dr – $4,825,000","url":"https://www.benleeproperties.com/for-buyers-3"},{"@type":"ListItem","position":2,"name":"16485 El Hito Place – $2,895,000","url":"https://www.benleeproperties.com/for-buyers-3"},{"@type":"ListItem","position":3,"name":"1921 6th Street – $1,525,000","url":"https://www.benleeproperties.com/for-buyers-3"},{"@type":"ListItem","position":4,"name":"2890 Forrester Dr – $21,000/mo","url":"https://www.benleeproperties.com/for-buyers-3"},{"@type":"ListItem","position":5,"name":"1005 Ocean Dr Oxnard – $25,000/mo","url":"https://www.benleeproperties.com/for-buyers-3"}]}
  </script>""",
    },
    "current-listings.html": {
        "title": "Built by Ben | Custom Luxury Homes Designed & Developed by Ben Lee in Los Angeles",
        "description": "Every Built by Ben home is personally conceived, designed, and overseen by Ben Lee — from lot selection to final walkthrough. Luxury custom construction in Cheviot Hills, Beverlywood, and West LA. Call (310) 704-6580.",
        "keywords": "Built by Ben, custom homes Los Angeles, luxury home builder LA, Ben Lee custom development, Cheviot Hills new construction, Beverlywood new homes, luxury real estate developer LA",
        "canonical": f"{DOMAIN}/current-listings",
        "h1": "BUILT BY BEN",
        "schema": """  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"ItemList","name":"Built by Ben – Custom Luxury Homes","description":"Homes personally designed, developed, and built under the supervision of Ben Lee, Beverly Hills' top broker-developer.","url":"https://www.benleeproperties.com/current-listings","numberOfItems":7}
  </script>""",
    },
    "ben-lee-sold-properties.html": {
        "title": "Ben Lee's Sold Properties | Over $100M in Closed LA Real Estate Transactions",
        "description": "A track record that speaks for itself. Ben Lee has closed over $100M in Los Angeles real estate, including properties at $15.25M, $8.5M, and $8.17M. The most trusted name in Cheviot Hills and Beverlywood. (310) 704-6580.",
        "keywords": "Ben Lee sold properties, Los Angeles real estate sold, Cheviot Hills sold homes, Beverlywood sold listings, top producing real estate agent LA, luxury home sales Beverly Hills",
        "canonical": f"{DOMAIN}/ben-lee-sold-properties",
        "h1": "Ben Lee Recent Transactions",
        "schema": None,
    },
    "about.html": {
        "title": "About Ben Lee | Beverly Hills' Top Real Estate Broker, Licensed Attorney & Developer",
        "description": "Ben Lee is a second-generation LA native, licensed attorney, and the top-producing broker at Beverly Hills' #1 office. His team — including Chief Marketing Writer Lilli Lee and transaction manager Joanna Sanchez — delivers an unmatched real estate experience.",
        "keywords": "Ben Lee realtor biography, Beverly Hills real estate broker, licensed attorney realtor LA, top producing agent Beverly Hills, Ben Lee Properties team, Lilli Lee, Joanna Sanchez, Cheviot Hills agent",
        "canonical": f"{DOMAIN}/about",
        "h1": "Meet the Team Behind LA's Most Trusted Real Estate Firm",
        "schema": """  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"Person","name":"Ben Lee","jobTitle":"Principal Broker & Licensed Attorney","worksFor":{"@type":"Organization","name":"Ben Lee Properties"},"description":"Beverly Hills' top-producing real estate broker and licensed attorney, specializing in Cheviot Hills, Beverlywood, and West Los Angeles luxury properties.","telephone":"+13107046580","email":"ben@benleeproperties.com","url":"https://www.benleeproperties.com/about","address":{"@type":"PostalAddress","addressLocality":"Beverly Hills","addressRegion":"CA","addressCountry":"US"},"knowsAbout":["Cheviot Hills real estate","Beverlywood real estate","luxury home development","real estate law","West Los Angeles property market"]}
  </script>""",
    },
    "blog.html": {
        "title": "Ben Lee's Real Estate Newsletter | Monthly Market Insights for Cheviot Hills & Beverlywood",
        "description": "Stay ahead of the LA real estate market with Ben Lee's monthly newsletter — delivered to over 9,000 Westside residences. In-depth analysis of Cheviot Hills, Beverlywood, and West LA home values, trends, and opportunities.",
        "keywords": "Los Angeles real estate newsletter, Cheviot Hills market report, Beverlywood home values, West LA real estate trends, Ben Lee newsletter, monthly market update LA, real estate insights Beverly Hills",
        "canonical": f"{DOMAIN}/blog",
        "h1": None,
        "schema": """  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"Blog","name":"Ben Lee Real Estate Newsletter","description":"Monthly Los Angeles real estate market analysis by top broker Ben Lee, covering Cheviot Hills, Beverlywood, and the greater Westside.","url":"https://www.benleeproperties.com/blog","publisher":{"@type":"Person","name":"Ben Lee","url":"https://www.benleeproperties.com/about"}}
  </script>""",
    },
    "bens-video-library.html": {
        "title": "Ben Lee's Video Library | LA Real Estate Market Updates, Property Tours & Expert Insights",
        "description": "Watch Ben Lee's video series covering the Los Angeles real estate market — neighborhood deep-dives, property walkthroughs, buyer and seller tips, and monthly market updates for Cheviot Hills and Beverlywood.",
        "keywords": "Ben Lee real estate videos, Los Angeles real estate market update video, Cheviot Hills property tour, Beverlywood real estate, real estate tips LA, Ben Lee YouTube, property walkthrough",
        "canonical": f"{DOMAIN}/bens-video-library",
        "h1": None,
        "schema": None,
    },
    "for-sellers.html": {
        "title": "Sell Your Home with Ben Lee | LA's Highest-Selling Real Estate Broker Nets You More",
        "description": "When you sell with Ben Lee, you get a licensed attorney, master negotiator, and LA's top-producing broker in your corner. Homes listed by Ben Lee sell faster and for more. Call (310) 704-6580 for a free consultation.",
        "keywords": "sell your home Los Angeles, top listing agent LA, best real estate agent to sell home Beverly Hills, Cheviot Hills home seller, Beverlywood listing agent, Ben Lee seller agent",
        "canonical": f"{DOMAIN}/for-sellers",
        "h1": None,
        "schema": """  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"Service","name":"Home Selling with Ben Lee Properties","provider":{"@type":"RealEstateAgent","name":"Ben Lee Properties","telephone":"+13107046580"},"description":"Full-service luxury home selling in Cheviot Hills, Beverlywood, and greater West Los Angeles. Ben Lee's attorney background and market expertise consistently delivers above-asking results.","areaServed":[{"@type":"Place","name":"Cheviot Hills"},{"@type":"Place","name":"Beverlywood"},{"@type":"Place","name":"Beverly Hills"},{"@type":"Place","name":"West Los Angeles"}]}
  </script>""",
    },
    "valuation.html": {
        "title": "Free Home Valuation | What Is Your Los Angeles Home Worth? — Ben Lee Properties",
        "description": "Get an expert home valuation from Ben Lee — Beverly Hills' top broker and licensed attorney. With decades of Westside market data and hundreds of closed transactions, Ben delivers the most accurate pricing in Cheviot Hills, Beverlywood, and West LA.",
        "keywords": "home valuation Los Angeles, what is my home worth LA, Cheviot Hills home value, Beverlywood property value, free home valuation Beverly Hills, real estate appraisal West LA, Ben Lee valuation",
        "canonical": f"{DOMAIN}/valuation",
        "h1": None,
        "schema": """  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"Service","name":"Free Home Valuation — Ben Lee Properties","provider":{"@type":"RealEstateAgent","name":"Ben Lee Properties","telephone":"+13107046580"},"description":"Accurate, data-driven home valuations for Cheviot Hills, Beverlywood, and West Los Angeles, provided by top broker and licensed attorney Ben Lee.","offers":{"@type":"Offer","price":"0","priceCurrency":"USD","description":"Free home valuation consultation"}}
  </script>""",
    },
    "testimonials.html": {
        "title": "Client Testimonials | What Clients Say About Ben Lee — LA's Most Trusted Broker",
        "description": "Hear from buyers and sellers who trusted Ben Lee Properties with their most important transactions. Five-star service, above-asking results, and stress-free closings — every time. Read real client stories.",
        "keywords": "Ben Lee Properties reviews, real estate agent testimonials Los Angeles, Cheviot Hills realtor reviews, best real estate agent Beverly Hills reviews, Ben Lee client stories, trusted LA broker",
        "canonical": f"{DOMAIN}/testimonials",
        "h1": None,
        "schema": """  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":"Why is Ben Lee considered the top real estate agent in Cheviot Hills?","acceptedAnswer":{"@type":"Answer","text":"Ben Lee is a licensed attorney with decades of Westside market experience and over $100M in closed transactions. His legal background gives buyers and sellers a significant negotiating advantage."}},{"@type":"Question","name":"What areas does Ben Lee specialize in?","acceptedAnswer":{"@type":"Answer","text":"Ben Lee specializes in Cheviot Hills, Beverlywood, Bel Air, Brentwood, and greater West Los Angeles luxury real estate."}}]}
  </script>""",
    },
    "contact.html": {
        "title": "Contact Ben Lee | Beverly Hills' #1 Real Estate Broker — (310) 704-6580",
        "description": "Ready to buy, sell, or build in Los Angeles? Contact Ben Lee directly at (310) 704-6580 or ben@benleeproperties.com. Offices in Beverly Hills and West LA. Response within 24 hours guaranteed.",
        "keywords": "contact Ben Lee Properties, real estate agent phone number LA, Beverly Hills realtor contact, (310) 704-6580, ben@benleeproperties.com, meet Ben Lee, schedule real estate consultation LA",
        "canonical": f"{DOMAIN}/contact",
        "h1": None,
        "schema": """  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"ContactPage","name":"Contact Ben Lee Properties","url":"https://www.benleeproperties.com/contact","mainEntity":{"@type":"RealEstateAgent","name":"Ben Lee Properties","telephone":"+13107046580","email":"ben@benleeproperties.com","address":{"@type":"PostalAddress","streetAddress":"9454 Wilshire Blvd","addressLocality":"Beverly Hills","addressRegion":"CA","postalCode":"90212","addressCountry":"US"}}}
  </script>""",
    },
    "contact-2.html": {
        "title": "Contact Ben Lee | Beverly Hills' #1 Real Estate Broker — (310) 704-6580",
        "description": "Get in touch with Ben Lee Properties — Beverly Hills' top-ranked real estate team. Call (310) 704-6580 or email ben@benleeproperties.com. Serving Cheviot Hills, Beverlywood, and all of West LA.",
        "keywords": "contact Ben Lee, real estate agent Los Angeles, Beverly Hills broker phone, schedule home showing LA",
        "canonical": f"{DOMAIN}/contact",
        "h1": None,
        "schema": None,
    },
    "social-media.html": {
        "title": "Follow Ben Lee Properties | Real Estate Insights on Instagram, LinkedIn & More",
        "description": "Follow Ben Lee for daily Cheviot Hills and Beverlywood real estate updates, off-market property previews, market analysis, and behind-the-scenes looks at Built by Ben custom homes.",
        "keywords": "Ben Lee Properties Instagram, real estate social media LA, follow Ben Lee realtor, Cheviot Hills real estate Instagram, Ben Lee LinkedIn, Los Angeles luxury real estate social media",
        "canonical": f"{DOMAIN}/social-media",
        "h1": None,
        "schema": None,
    },
    "old-home.html": {
        "title": "Ben Lee Properties | #1 Real Estate Broker in Cheviot Hills & Beverlywood, Los Angeles",
        "description": "Ben Lee — Beverly Hills' top-ranked real estate broker and licensed attorney. Specializing in Cheviot Hills, Beverlywood, and West LA luxury properties. Over $100M in closed transactions.",
        "keywords": "Cheviot Hills real estate, Beverlywood homes, Ben Lee Properties, top LA broker, luxury real estate West LA",
        "canonical": f"{DOMAIN}/",
        "h1": None,
        "schema": None,
    },
    "neighborhoods.html": {
        "title": "Neighborhoods We Serve | Cheviot Hills, Beverlywood, Bel Air & West LA — Ben Lee Properties",
        "description": "Ben Lee Properties serves the finest neighborhoods on LA's Westside — Cheviot Hills, Beverlywood, Bel Air, Brentwood, Santa Monica, and beyond. Hyper-local expertise that no national firm can match.",
        "keywords": "Cheviot Hills real estate, Beverlywood homes for sale, Bel Air realtor, Brentwood real estate agent, Santa Monica broker, West LA neighborhoods, Ben Lee Properties service area",
        "canonical": f"{DOMAIN}/neighborhoods",
        "h1": None,
        "schema": None,
    },
    "states.html": {
        "title": "California Luxury Real Estate | Ben Lee Properties — Expert Guidance Across the State",
        "description": "From the Westside of Los Angeles to the California coast, Ben Lee brings his attorney's precision and decades of market expertise to every transaction statewide.",
        "keywords": "California luxury real estate, LA luxury homes, California real estate agent, Ben Lee Properties California",
        "canonical": f"{DOMAIN}/states",
        "h1": None,
        "schema": None,
    },
    "amenities.html": {
        "title": "Luxury Home Amenities in Los Angeles | Ben Lee Properties — Pools, Views & More",
        "description": "Explore premium property amenities in Cheviot Hills and Beverlywood — infinity pools, panoramic views, home theaters, chef kitchens, and smart-home systems. Ben Lee knows where to find them.",
        "keywords": "luxury home amenities Los Angeles, pool homes Cheviot Hills, smart home Beverly Hills, luxury real estate features LA, premium amenities Beverlywood",
        "canonical": f"{DOMAIN}/amenities",
        "h1": None,
        "schema": None,
    },
    "realtors.html": {
        "title": "Our Real Estate Team | Ben Lee Properties — Beverly Hills' Most Decorated Agents",
        "description": "Meet the full Ben Lee Properties team — award-winning agents, licensed professionals, and marketing experts united by one mission: delivering the best real estate outcome in Los Angeles.",
        "keywords": "Ben Lee Properties team, Beverly Hills real estate agents, top realtors Los Angeles, licensed real estate team LA",
        "canonical": f"{DOMAIN}/realtors",
        "h1": None,
        "schema": None,
    },
    "404.html": {
        "title": "Page Not Found | Ben Lee Properties",
        "description": "The page you're looking for isn't here, but Ben Lee is. Call (310) 704-6580 or return to benleeproperties.com to find your dream home in Cheviot Hills, Beverlywood, or West LA.",
        "keywords": "Ben Lee Properties",
        "canonical": f"{DOMAIN}/",
        "h1": None,
        "schema": None,
    },
    "401.html": {
        "title": "Access Restricted | Ben Lee Properties",
        "description": "This page is restricted. Return to the Ben Lee Properties homepage to browse current listings in Cheviot Hills, Beverlywood, and Los Angeles.",
        "keywords": "Ben Lee Properties",
        "canonical": f"{DOMAIN}/",
        "h1": None,
        "schema": None,
    },
    # ── Detail templates ─────────────────────────────────────────────────────
    "detail_property.html": {
        "title": "Property Detail | Ben Lee Properties — Luxury Real Estate Los Angeles",
        "description": "Detailed listing information for a Ben Lee Properties home. Ben Lee is LA's top broker-attorney — call (310) 704-6580 to schedule a showing in Cheviot Hills, Beverlywood, or West LA.",
        "keywords": "property listing Los Angeles, Ben Lee Properties home, luxury real estate detail, Cheviot Hills home for sale",
        "canonical": f"{DOMAIN}/",
        "h1": None,
        "schema": None,
    },
    "detail_blog.html": {
        "title": "Newsletter Article | Ben Lee Properties — LA Real Estate Insights",
        "description": "Read Ben Lee's latest real estate insights — market analysis, neighborhood guides, and expert advice for buyers and sellers in Cheviot Hills, Beverlywood, and West LA.",
        "keywords": "Ben Lee newsletter article, Los Angeles real estate insight, Cheviot Hills market update",
        "canonical": f"{DOMAIN}/blog",
        "h1": None,
        "schema": None,
    },
    "detail_city.html": {
        "title": "Neighborhood Guide | Ben Lee Properties — Los Angeles Real Estate by Neighborhood",
        "description": "Discover what makes each Westside neighborhood unique — schools, walkability, market trends, and property values — from Ben Lee, LA's most trusted real estate authority.",
        "keywords": "Los Angeles neighborhood guide, Cheviot Hills community, Beverlywood neighborhood, West LA area guide, Ben Lee Properties",
        "canonical": f"{DOMAIN}/neighborhoods",
        "h1": None,
        "schema": None,
    },
    "detail_state.html": {
        "title": "California Real Estate Guide | Ben Lee Properties",
        "description": "Comprehensive California real estate information from Ben Lee Properties — the Westside's top-ranked broker and licensed attorney.",
        "keywords": "California real estate, Los Angeles property guide, Ben Lee Properties",
        "canonical": f"{DOMAIN}/",
        "h1": None,
        "schema": None,
    },
    "detail_realtor.html": {
        "title": "Agent Profile | Ben Lee Properties — Beverly Hills' Award-Winning Real Estate Team",
        "description": "Meet a member of the Ben Lee Properties team. Every agent on our roster shares Ben's commitment to exceptional service, market expertise, and client-first results.",
        "keywords": "Ben Lee Properties agent, Beverly Hills realtor profile, top real estate agent LA",
        "canonical": f"{DOMAIN}/realtors",
        "h1": None,
        "schema": None,
    },
    "detail_testimonial.html": {
        "title": "Client Story | Ben Lee Properties — Real Experiences, Real Results",
        "description": "Read a real client story from Ben Lee Properties. From first-time buyers to seasoned investors, every client receives the same five-star service in Cheviot Hills, Beverlywood, and West LA.",
        "keywords": "Ben Lee Properties client review, real estate testimonial Los Angeles, Cheviot Hills realtor review",
        "canonical": f"{DOMAIN}/testimonials",
        "h1": None,
        "schema": None,
    },
    "detail_amenity.html": {
        "title": "Luxury Amenity Guide | Ben Lee Properties — Premium Features in LA Homes",
        "description": "Explore the premium amenities found in Ben Lee Properties listings — from resort-style pools to city-view terraces and state-of-the-art smart home systems across the LA Westside.",
        "keywords": "luxury home amenity Los Angeles, premium property features LA, pool home Cheviot Hills",
        "canonical": f"{DOMAIN}/amenities",
        "h1": None,
        "schema": None,
    },
    "detail_lifestyle.html": {
        "title": "LA Lifestyle Guide | Ben Lee Properties — Live the Best of Westside Los Angeles",
        "description": "Discover the LA lifestyle that comes with living in a Ben Lee Properties neighborhood — from Cheviot Hills' quiet streets to the restaurants, parks, and culture of the Westside.",
        "keywords": "Los Angeles lifestyle, Cheviot Hills living, Beverlywood neighborhood lifestyle, West LA lifestyle, Ben Lee Properties",
        "canonical": f"{DOMAIN}/",
        "h1": None,
        "schema": None,
    },
    "detail_term.html": {
        "title": "Real Estate Glossary | Ben Lee Properties — Know the Terms Before You Sign",
        "description": "Ben Lee's real estate glossary explains every term you'll encounter when buying or selling in Los Angeles. Knowledge is leverage — and with a licensed attorney as your broker, you'll have both.",
        "keywords": "real estate terms glossary, real estate definitions Los Angeles, buyer seller terms explained, Ben Lee Properties",
        "canonical": f"{DOMAIN}/",
        "h1": None,
        "schema": None,
    },
    "detail_social.html": {
        "title": "Social Post | Ben Lee Properties — LA Real Estate on Social Media",
        "description": "Follow Ben Lee for real-time Cheviot Hills and Beverlywood market updates, exclusive property previews, and expert commentary on Los Angeles luxury real estate.",
        "keywords": "Ben Lee Properties social media, LA real estate Instagram, Cheviot Hills property updates",
        "canonical": f"{DOMAIN}/social-media",
        "h1": None,
        "schema": None,
    },
}

# ── Build the replacement meta block ─────────────────────────────────────────
def build_meta_block(cfg):
    title = cfg["title"]
    desc  = cfg["description"]
    kw    = cfg["keywords"]
    can   = cfg["canonical"]
    schema = cfg.get("schema") or ""
    img   = OG_IMAGE

    return f"""  <meta charset="utf-8">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <meta name="keywords" content="{kw}">
  <meta name="robots" content="index, follow">
  <meta name="author" content="Ben Lee Properties">
  <link rel="canonical" href="{can}">

  <!-- Open Graph -->
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Ben Lee Properties">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="{can}">
  <meta property="og:image" content="{img}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:locale" content="en_US">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{desc}">
  <meta name="twitter:image" content="{img}">

  <meta content="width=device-width, initial-scale=1" name="viewport">
{schema}"""

# ── Pattern that matches everything from <meta charset> to </meta viewport> ──
# We replace the entire existing meta block in the <head>
META_RE = re.compile(
    r'<meta charset=[^>]+>.*?<meta content="width=device-width[^>]+>',
    re.DOTALL
)

def process(fname, cfg):
    path = os.path.join(BASE, fname)
    if not os.path.exists(path):
        print(f"  SKIP (not found): {fname}")
        return

    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    new_block = build_meta_block(cfg)
    new_html, n = META_RE.subn(new_block, html, count=1)

    if n == 0:
        print(f"  WARN (no match):  {fname}")
        return

    # Optional: update H1 if specified
    if cfg.get("h1"):
        new_html = re.sub(
            r'(<h1[^>]*>)(.*?)(</h1>)',
            lambda m: m.group(1) + cfg["h1"] + m.group(3),
            new_html, count=1, flags=re.DOTALL
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"  OK: {fname}")

print("Updating meta tags across all pages...")
for fname, cfg in PAGES.items():
    process(fname, cfg)
print("Done.")
