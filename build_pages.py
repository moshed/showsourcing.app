#!/usr/bin/env python3
"""Build the search / AI discoverability files for showsourcing.app.

Writes (from help/help.json + the facts below):
  llms.txt                         short plain-text summary (llmstxt.org)
  llms-full.txt                    the whole Help FAQ as plain text
  trade-show-sourcing-app/index.html
  vendor-price-tracking/index.html
  compare/index.html

Run by build_help.sh on every deploy, so the FAQ text never drifts from the app.
Facts only: prices and features come from the app and help.json. No ratings,
user counts or testimonials. No competitor names on THIS page (Moshe, 2026-10-17). Named, sourced
"Show Sourcing vs X" pages live in content/ (build_blog.py, Moshe 2026-10-20).
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HELP = json.loads((ROOT / "help" / "help.json").read_text())
FAQ = {e["id"]: e for s in HELP["sections"] for e in s["entries"]}

SITE = "https://showsourcing.app"
APPSTORE = "https://apps.apple.com/us/app/show-sourcing-manager/id6758863749"
BETA = "https://testflight.apple.com/join/Sy1eYzcp"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


# ---------------------------------------------------------------- JSON-LD
def software_ld(page_url: str) -> dict:
    return {
        "@type": "SoftwareApplication",
        "name": "Show Sourcing",
        "url": SITE,
        "mainEntityOfPage": page_url,
        "operatingSystem": "iOS, iPadOS, macOS",
        "applicationCategory": "BusinessApplication",
        "applicationSubCategory": "Product Sourcing CRM",
        "description": (
            "A CRM for buyers who source products at trade shows. Capture products with photos, "
            "vendors from business cards, FOB prices and price breaks, and see landed cost (LDP) "
            "with US tariffs. Teams share everything live. Every plan starts with a 7-day free trial."
        ),
        "downloadUrl": APPSTORE,
        "image": f"{SITE}/app-icon.png",
        "offers": [
            {
                "@type": "Offer", "name": "6 months, per seat", "price": "60.00", "priceCurrency": "USD",
                "priceSpecification": {"@type": "UnitPriceSpecification", "price": "60.00", "priceCurrency": "USD",
                                       "billingDuration": "P6M", "unitText": "seat"},
            },
            {
                "@type": "Offer", "name": "Yearly, per seat", "price": "102.00", "priceCurrency": "USD",
                "priceSpecification": {"@type": "UnitPriceSpecification", "price": "102.00", "priceCurrency": "USD",
                                       "billingDuration": "P1Y", "unitText": "seat"},
            },
        ],
    }


def faq_ld(ids: list[str]) -> dict:
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": FAQ[i]["question"],
             "acceptedAnswer": {"@type": "Answer", "text": FAQ[i]["answer"]}}
            for i in ids
        ],
    }


# ---------------------------------------------------------------- page shell
STYLE = """
    :root { --bg:#060a18; --accent:#f97316; --accent2:#38bdf8; --text:#f1f5f9; --muted:#94a3b8; --dim:#64748b;
            --border:rgba(255,255,255,0.07); --card:rgba(255,255,255,0.025); }
    *,*::before,*::after { margin:0; padding:0; box-sizing:border-box; }
    body { font-family:'Plus Jakarta Sans',sans-serif; background:var(--bg); color:var(--text); min-height:100vh; line-height:1.6; }
    header { position:fixed; top:0; left:0; right:0; z-index:100; display:flex; align-items:center; justify-content:space-between;
             padding:16px clamp(20px,4vw,40px); background:rgba(6,10,24,0.88); backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px);
             border-bottom:1px solid var(--border); }
    header .logo { font-weight:800; font-size:0.95rem; color:var(--text); text-decoration:none; white-space:nowrap; }
    header nav { display:flex; gap:clamp(14px,2.5vw,24px); align-items:center; }
    header nav a { color:var(--dim); text-decoration:none; font-size:0.8rem; font-weight:500; white-space:nowrap; }
    header nav a:hover, header nav a.active { color:var(--text); }
    .page { max-width:860px; margin:0 auto; padding:110px 24px 80px; }
    .eyebrow { color:var(--accent); font-weight:700; font-size:0.78rem; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:10px; }
    h1 { font-size:clamp(1.8rem,4.5vw,2.7rem); font-weight:800; letter-spacing:-0.02em; line-height:1.15; margin-bottom:14px;
         background:linear-gradient(135deg,var(--text),var(--accent2)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
    .lead { color:var(--muted); font-size:1.05rem; margin-bottom:24px; max-width:680px; }
    .bar { width:40px; height:3px; border-radius:2px; margin:0 0 28px; background:linear-gradient(90deg,var(--accent),var(--accent2)); }
    h2 { font-size:1.3rem; font-weight:800; margin:44px 0 14px; letter-spacing:-0.01em; }
    h3 { font-size:1rem; font-weight:700; margin-bottom:6px; }
    p { margin-bottom:12px; }
    .muted { color:var(--muted); }
    .actions { display:flex; flex-wrap:wrap; gap:10px; margin:6px 0 10px; }
    .btn { display:inline-flex; align-items:center; gap:8px; font-weight:700; font-size:0.88rem; padding:11px 18px; border-radius:12px;
           text-decoration:none; border:1px solid var(--border); color:var(--text); background:var(--card); }
    .btn:hover { border-color:var(--accent2); }
    .btn.primary { background:var(--accent); color:#111; border-color:transparent; }
    .fine { color:var(--dim); font-size:0.82rem; }
    .steps { display:grid; gap:12px; counter-reset:s; }
    .step { border:1px solid var(--border); background:var(--card); border-radius:14px; padding:16px 18px 14px 56px; position:relative; }
    .step::before { counter-increment:s; content:counter(s); position:absolute; left:16px; top:15px; width:26px; height:26px; border-radius:50%;
                    display:grid; place-items:center; font-weight:800; font-size:0.82rem; background:var(--accent); color:#111; }
    .step p { color:var(--muted); margin:0; font-size:0.93rem; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:12px; }
    .card { border:1px solid var(--border); background:var(--card); border-radius:14px; padding:16px 18px; }
    .card p { color:var(--muted); font-size:0.92rem; margin:0; }
    .shots { display:flex; gap:12px; overflow-x:auto; padding:4px 2px 12px; scroll-snap-type:x mandatory; }
    .shots img { height:420px; width:auto; border-radius:22px; border:1px solid var(--border); scroll-snap-align:start; flex:0 0 auto; }
    table { width:100%; border-collapse:collapse; font-size:0.9rem; margin:8px 0 8px; }
    th, td { text-align:left; padding:10px 10px; border-bottom:1px solid var(--border); vertical-align:top; }
    th { font-size:0.78rem; color:var(--dim); text-transform:uppercase; letter-spacing:0.05em; }
    td:first-child { font-weight:600; min-width:190px; }
    table { min-width:640px; }
    .steps + .fine { margin-top:10px; }
    .yes { color:#22c55e; font-weight:700; } .part { color:#eab308; font-weight:600; } .no { color:var(--dim); }
    .tablewrap { overflow-x:auto; border:1px solid var(--border); border-radius:14px; background:var(--card); }
    details { border:1px solid var(--border); background:var(--card); border-radius:12px; padding:13px 16px; margin-bottom:8px; }
    summary { cursor:pointer; font-weight:700; font-size:0.95rem; }
    details p { color:var(--muted); margin:8px 0 0; font-size:0.92rem; }
    .cta { margin-top:48px; border:1px solid var(--border); border-radius:18px; padding:26px; background:linear-gradient(135deg,rgba(249,115,22,0.10),rgba(56,189,248,0.08)); }
    .cta h2 { margin-top:0; }
    footer { border-top:1px solid var(--border); padding:28px clamp(20px,4vw,40px); color:var(--dim); font-size:0.8rem; }
    footer .wrap { max-width:860px; margin:0 auto; display:flex; flex-wrap:wrap; gap:14px; justify-content:space-between; }
    footer nav { display:flex; flex-wrap:wrap; gap:14px; }
    footer a { color:var(--dim); text-decoration:none; } footer a:hover { color:var(--text); }
    a { color:var(--accent2); }
    @media (max-width:600px) { header nav a.hide-sm { display:none; } .shots img { height:360px; } }
    html.light { --bg:#f6f7fb; --accent2:#0369a1; --text:#0f172a; --muted:#475569; --dim:#5b6779; --border:rgba(15,23,42,0.10); --card:#fff; }
    html.light header { background:rgba(246,247,251,0.88); }
    html.light .btn.primary { background:#ea580c; color:#fff; }
    html.light .step::before { background:#ea580c; color:#fff; }
    html.light .card, html.light details, html.light .step, html.light .tablewrap { box-shadow:0 1px 2px rgba(15,23,42,0.04),0 8px 24px rgba(15,23,42,0.04); }
"""

THEME_BTN = ('<button class="theme-toggle" type="button" data-theme-toggle aria-label="Switch between light and dark mode" '
             'title="Switch between light and dark mode"><svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
             'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/>'
             '<path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>'
             '</svg><svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg></button>')

USE_CASES = [
    ("/trade-show-sourcing-app/", "Trade show sourcing app"),
    ("/vendor-price-tracking/", "Track vendor prices"),
    ("/compare/", "Compare"),
]


def shell(slug: str, title: str, description: str, body: str, faq_ids: list[str]) -> str:
    url = f"{SITE}/{slug}/"
    ld = {"@context": "https://schema.org", "@graph": [software_ld(url), faq_ld(faq_ids)] if faq_ids else [software_ld(url)]}
    footer_links = "".join(f'<a href="{h}">{esc(t)}</a>' for h, t in USE_CASES)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="/theme.js"></script>
    <link rel="stylesheet" href="/theme.css">
    <title>{esc(title)}</title>
    <meta name="description" content="{esc(description)}">
    <meta name="theme-color" content="#060a18" data-dark="#060a18" data-light="#f6f7fb">
    <meta name="robots" content="index,follow">
    <link rel="canonical" href="{url}">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Show Sourcing">
    <meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(description)}">
    <meta property="og:url" content="{url}">
    <meta property="og:image" content="{SITE}/images/ss-products-grid.webp">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:site" content="@ShowSourcingApp">
    <link rel="icon" type="image/png" href="/favicon.png">
    <link rel="apple-touch-icon" href="/app-icon.png">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script type="application/ld+json">
{json.dumps(ld, indent=2, ensure_ascii=False)}
    </script>
    <style>{STYLE}    </style>
</head>
<body>
<header>
    <a class="logo" href="/">Show Sourcing</a>
    <nav>
        <a href="/trade-show-sourcing-app/" class="hide-sm{' active' if slug != 'compare' else ''}">Use cases</a>
        <a href="/pricing">Pricing</a>
        <a href="/help">Help</a>
        <a href="/blog/" class="hide-sm">Blog</a>
        {THEME_BTN}
    </nav>
</header>
<main class="page">
{body}
{cta()}
</main>
<footer>
    <div class="wrap">
        <span>&copy; 2026 DNZ · Show Sourcing</span>
        <nav>
            {footer_links}
            <a href="/pricing">Pricing</a>
            <a href="/help">Help &amp; FAQ</a>
            <a href="/blog/">Blog</a>
            <a href="/privacy.html">Privacy Policy</a>
            <a href="/terms.html">Terms of Service</a>
            <a href="mailto:general@showsourcing.app">Support</a>
            <a href="https://x.com/ShowSourcingApp" target="_blank" rel="noopener">X @ShowSourcingApp</a>
        </nav>
    </div>
</footer>
</body>
</html>
"""


def cta() -> str:
    return f"""<section class="cta">
    <h2>Try it at your next show</h2>
    <p class="muted">Every plan starts with a 7-day free trial. Then $10 a seat a month on the 6-month plan, or $8.50 a seat a month billed yearly. Teams of 10, 15 and 20 seats get 5%, 10% and 15% off.</p>
    <div class="actions">
        <a class="btn primary" href="{APPSTORE}" target="_blank" rel="noopener">Download on the App Store</a>
        <a class="btn" href="/pricing">See pricing</a>
        <a class="btn" href="/help">Help &amp; FAQ</a>
    </div>
    <p class="fine">iPhone, iPad and Mac. Web portal at app.showsourcing.app.</p>
</section>"""


def faq_block(ids: list[str]) -> str:
    items = "\n".join(
        f'<details><summary>{esc(FAQ[i]["question"])}</summary><p>{esc(FAQ[i]["answer"])}</p></details>' for i in ids)
    return f'<h2>Questions</h2>\n{items}\n<p class="fine">More answers in <a href="/help">Help &amp; FAQ</a>.</p>'


def shots(names: list[tuple[str, str]]) -> str:
    imgs = "".join(f'<img src="/images/{n}" alt="{esc(a)}" loading="lazy">' for n, a in names)
    return f'<div class="shots">{imgs}</div>'


# ---------------------------------------------------------------- pages
def page_trade_show() -> str:
    faq = ["what-is", "offline", "venue", "scan-card", "ldp", "team-products", "devices", "price"]
    body = f"""
<p class="eyebrow">For trade show buyers</p>
<h1>An app to record vendors, products and prices at trade shows</h1>
<p class="lead">Show Sourcing is a CRM built for the booth. At Canton Fair, Global Sources, the Hong Kong fairs or a factory visit, you photograph a product, add the vendor and the price, and the app works out the landed cost. Your team sees it on their phones a few seconds later.</p>
<div class="bar"></div>
<div class="actions">
    <a class="btn primary" href="{APPSTORE}" target="_blank" rel="noopener">Start the 7-day free trial</a>
    <a class="btn" href="/help">How it works</a>
</div>

<h2>At the booth, in under a minute</h2>
<div class="steps">
    <div class="step"><h3>Photograph the product</h3><p>Take photos or a short video, add a voice note, and draw on a photo to mark a detail. It works without internet; the app uploads when you are back online.</p></div>
    <div class="step"><h3>Add the vendor</h3><p>Scan the business card. The app reads the name, company, phones, emails, WeChat, website and address. Or tap a vendor you already have.</p></div>
    <div class="step"><h3>Enter the price</h3><p>FOB (or CIF, EXW, DDP) in any currency, price breaks for bigger orders, MOQ, packaging and units per container.</p></div>
    <div class="step"><h3>See the landed cost</h3><p>The app adds packaging, US tariff (HTS with Section 301) and the freight share of one unit, so you see LDP before you leave the booth.</p></div>
</div>
<p class="fine">At the big shows the app fills in the venue for you.</p>

{shots([("ss-create-sm.webp", "Create screen: photos, vendor and price"),
        ("ss-vendor-card-sm.webp", "Vendor from a scanned business card"),
        ("ss-product-sm.webp", "Product page with landed cost"),
        ("ss-products-grid-sm.webp", "All products from the show in a grid")])}

<h2>After the show</h2>
<div class="grid">
    <div class="card"><h3>Find anything</h3><p>Search vendor, category, notes, venue and even the words printed on the box in your photos. Filter by FOB, LDP, MOQ, status, show or teammate.</p></div>
    <div class="card"><h3>Follow up</h3><p>Mark each product's status, such as Sample Requested, and email the vendor from a template filled with the product details.</p></div>
    <div class="card"><h3>Work as a team</h3><p>Everyone on the team sees new products in seconds, comments with @mentions, and can see teammates on the Team Map during the show.</p></div>
    <div class="card"><h3>Ask your AI</h3><p>Connect ChatGPT or Claude to your catalog and ask, for example, "show me all speakers under $5".</p></div>
</div>

{faq_block(faq)}
"""
    return shell("trade-show-sourcing-app",
                 "Trade show sourcing app: record vendors, products and prices | Show Sourcing",
                 "An iPhone, iPad and Mac app for buyers at trade shows: photograph products, scan vendor business cards, record FOB prices and price breaks, and see landed cost with US tariffs. 7-day free trial.",
                 body, faq)


def page_price_tracking() -> str:
    faq = ["price-breaks", "display-cost", "price-terms", "currency", "ldp", "tariffs", "sort", "filters"]
    body = f"""
<p class="eyebrow">Quotes, MOQ and price breaks</p>
<h1>Track supplier quotes, MOQ and price breaks across trade shows</h1>
<p class="lead">Vendors quote in different currencies, on different terms, with different minimums. Show Sourcing keeps every quote on the product it belongs to, turns it into a landed cost you can compare, and keeps it next to the vendor and the photos.</p>
<div class="bar"></div>

<h2>What you record for each quote</h2>
<div class="grid">
    <div class="card"><h3>Price and terms</h3><p>FOB, CIF, EXW or DDP. The app knows what each one includes, so LDP leaves out freight on CIF and adds the factory cost on EXW.</p></div>
    <div class="card"><h3>Any currency</h3><p>Enter RMB, euros or any other currency. The app converts to US dollars for LDP with daily rates.</p></div>
    <div class="card"><h3>Price breaks</h3><p>A row per quantity, such as 1,000 at $2.40 and 5,000 at $2.15, in the order you choose. The smallest quantity's price is the FOB.</p></div>
    <div class="card"><h3>MOQ and packaging</h3><p>Minimum order, package cost and units per container, which set each unit's share of the freight.</p></div>
</div>

<h2>How you compare them</h2>
<div class="steps">
    <div class="step"><h3>One number to compare</h3><p>LDP puts every quote on the same footing: price, packaging, tariff and freight for one unit at your door.</p></div>
    <div class="step"><h3>Sort and filter</h3><p>Sort products by LDP, FOB, MOQ or vendor. Filter by an LDP or FOB range, a category group, a show or a status.</p></div>
    <div class="step"><h3>Per vendor</h3><p>A vendor's page lists every product and quote from that vendor, with their contacts and card photo.</p></div>
    <div class="step"><h3>Pick which break counts</h3><p>Choose whether the list and LDP use the lowest or the highest quantity of each price ladder.</p></div>
</div>

{shots([("ss-product-sm.webp", "Product page with price and landed cost"),
        ("ss-products-list-sm.webp", "Products list sorted by price"),
        ("ss-filters-sm.webp", "Filters for LDP, FOB and MOQ")])}

{faq_block(faq)}
"""
    return shell("vendor-price-tracking",
                 "Track supplier quotes, MOQ and price breaks | Show Sourcing",
                 "Record supplier quotes from trade shows with price terms, currency, price breaks and MOQ, and compare them by landed cost (LDP) with US tariffs. iPhone, iPad and Mac.",
                 body, faq)


def page_compare() -> str:
    faq = ["what-is", "offline", "export", "team-products", "price"]
    Y, P, N = '<span class="yes">Yes</span>', '<span class="part">With work</span>', '<span class="no">No</span>'
    rows = [
        ("Photos and video on each product", Y, P, P, P),
        ("Works offline on the show floor", Y, P, Y, P),
        ("Business card scan into vendor contacts", Y, N, N, P),
        ("FOB, price terms and price breaks per product", Y, P, N, N),
        ("Landed cost with US tariffs and freight", Y, P, N, N),
        ("Search words printed on the box in photos", Y, N, P, N),
        ("Team sees new products in seconds", Y, P, P, Y),
        ("Contacts, deals and sales pipeline", N, P, N, Y),
        ("Cost", "From $8.50 a seat a month", "Often free", "Often free", "Varies"),
    ]
    trs = "\n".join(f"<tr><td>{esc(r[0])}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td></tr>" for r in rows)
    body = f"""
<p class="eyebrow">Honest comparison</p>
<h1>Show Sourcing vs spreadsheets, notes apps and general CRMs</h1>
<p class="lead">Most buyers start with a spreadsheet, the notes app and a pile of business cards. That works for a few booths. Show Sourcing is for when a show means hundreds of products, several buyers and quotes you need to compare.</p>
<div class="bar"></div>

<div class="tablewrap">
<table>
<thead><tr><th></th><th>Show Sourcing</th><th>Spreadsheet</th><th>Notes app</th><th>General CRM</th></tr></thead>
<tbody>
{trs}
</tbody>
</table>
</div>
<p class="fine">"With work" means you can get there with your own columns, formulas, folders or add-ons.</p>

<h2>Show Sourcing vs other tools, one by one</h2>
<ul class="muted"><!-- AUTO:vs --><!-- /AUTO:vs --></ul>

<h2>When a spreadsheet is enough</h2>
<p class="muted">If you visit a handful of booths, buy alone, and only need a price list, a spreadsheet is fine and free. Show Sourcing earns its place when photos, vendors, price breaks and landed cost all need to stay together, and when a team works the same show.</p>

<h2>When a general CRM fits better</h2>
<p class="muted">General CRMs are built around contacts, deals and a sales pipeline. Show Sourcing is built around products: photos, quotes, MOQ, tariffs and landed cost, linked to the vendor who quoted them. It is not a sales CRM.</p>

{faq_block(faq)}
"""
    return shell("compare",
                 "Show Sourcing vs spreadsheets, notes apps and general CRMs",
                 "An honest comparison of Show Sourcing with spreadsheets, notes apps and general CRMs for recording products, vendors and prices at trade shows.",
                 body, faq)


# ---------------------------------------------------------------- llms.txt
def complete_features() -> str:
    """Every Help topic, grouped by section: '- question: first sentence'."""
    import re as _re
    out = []
    for sec in HELP["sections"]:
        out.append(f"### {sec['title']}")
        for e in sec["entries"]:
            parts = _re.split(r"(?<=[.!?])\s+", e["answer"].strip())
            first = parts[0]
            # "Yes." or "Open the Create tab." alone says nothing to an AI reader.
            if len(first) < 40 and len(parts) > 1:
                first = first + " " + parts[1]
            out.append(f"- {e['question']} {first}")
        out.append("")
    return "\n".join(out).strip()


def llms_txt() -> str:
    FEATURES = complete_features()
    return f"""# Show Sourcing

> Show Sourcing is a CRM for buyers who source products at trade shows. On iPhone, iPad and Mac, buyers photograph products, add vendors from business cards, record FOB prices, price breaks and MOQ, and see landed cost (LDP) with US tariffs. Teams share every product live. Every plan starts with a 7-day free trial.

## Who it is for

- Buyers, importers and sourcing agents at trade shows such as Canton Fair, Global Sources and the Hong Kong fairs, and on factory visits
- Small teams that work a show together and need one shared catalog
- Anyone who now uses a spreadsheet, the notes app and a stack of business cards

## New in version 1.1

- Custom fields for anything your team tracks, in search and filters
- Price breaks (a price per quantity) and price terms FOB, CIF, EXW or DDP
- Excel export of products and vendors with photos in the cells and live landed-cost formulas (paid plans)
- Mac and iPad: list and details side by side, keyboard shortcuts
- AI Connection: connect Claude or ChatGPT to your catalog
- US shipping records on vendor pages
- Searchable Help & FAQ and a What's New list in the app
- Redesigned Team Map, AI photo descriptions, a faster camera, numbers in your region's format

## Key features

- Product capture: photos, video, voice notes (transcribed on the device), markup on photos; works offline
- Vendors: business card scan (name, company, phones, emails, WeChat, website, address), duplicate check, vendor pages with all their products, factory on a map, US shipping records
- Prices: FOB, CIF, EXW or DDP; any currency converted to USD with daily rates; price breaks per quantity; MOQ, packaging, units per container
- Landed cost (LDP): price + packaging + US tariff (HTS with Section 301) + freight share per unit; tariff codes linked to categories
- Search: vendor, category, tags, notes, venue, status, custom fields, words printed in photos (on-device OCR), photo descriptions
- Filters and sorting by FOB, LDP, MOQ, status, show, teammate, category groups
- Follow up: statuses (e.g. Sample Requested), vendor email templates
- Teams: live sync, comments and @mentions, team statuses, Team Map at the show, export permissions
- Export to Excel: products and vendors, photos in the cells, every field and custom field, live LDP formulas, emailed as a link (paid plans)
- Custom fields (text, number, currency, toggle); Siri and Spotlight search
- AI Connection: connect ChatGPT or Claude (MCP) to ask questions about your catalog
- Show detection: knows which trade show you are at (by location) and tags products with it
- Hide Vendor Names: blur vendors so you can show products and prices to anyone
- Vendor tools: merge duplicate vendors, find duplicate photos, vendor email templates
- Quick selections: your own lists for categories, tags, packaging, venues, MOQ, country of origin, statuses
- Tariff codes: HTS codes with nicknames, linked to categories
- Data: JSON backup and export, sync across iPhone, iPad, Mac and the web portal; sign in with Apple or email
- Mac and iPad: two-pane layout (list and details side by side), keyboard shortcuts
- Numbers and prices in your region's format
- In-app Help with search, and a What's New list

## Complete feature list

Generated from the app's own Help, one line per topic. Details: {SITE}/llms-full.txt

{FEATURES}

## Pricing

- Per seat (one seat per person); 7-day free trial on every plan
- 6 months: $10 a seat a month ($60 a seat per 6 months)
- Yearly: $8.50 a seat a month ($102 a seat per year)
- Team discounts: 5% at 10 seats, 10% at 15, 15% at 20

## Platforms

- iPhone, iPad and Mac (App Store), plus a web portal at app.showsourcing.app

## Links

- Home: {SITE}/
- Trade show sourcing app: {SITE}/trade-show-sourcing-app/
- Track vendor prices and price breaks: {SITE}/vendor-price-tracking/
- Compare with spreadsheets and CRMs: {SITE}/compare/
- Pricing: {SITE}/pricing
- Help and FAQ: {SITE}/help
- Full FAQ as text: {SITE}/llms-full.txt
- App Store: {APPSTORE}
- Beta (TestFlight): {BETA}
- Support: general@showsourcing.app
"""


def llms_full() -> str:
    out = ["# Show Sourcing: Help and FAQ", "",
           f"> The full Help text from the app, as plain text. Source of truth: {SITE}/help. Updated {HELP.get('updated', '')}.", ""]
    for s in HELP["sections"]:
        out.append(f"## {s['title']}")
        out.append("")
        for e in s["entries"]:
            out.append(f"### {e['question']}")
            out.append(e["answer"])
            out.append("")
    return "\n".join(out)


def main() -> None:
    (ROOT / "llms.txt").write_text(llms_txt())
    (ROOT / "llms-full.txt").write_text(llms_full())
    for slug, builder in [("trade-show-sourcing-app", page_trade_show),
                          ("vendor-price-tracking", page_price_tracking),
                          ("compare", page_compare)]:
        d = ROOT / slug
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(builder())
    print("Built llms.txt, llms-full.txt and 3 use-case pages")


if __name__ == "__main__":
    main()
