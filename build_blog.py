#!/usr/bin/env python3
"""Build blog guides and "Show Sourcing vs X" pages from content/*.md.

Each content file:

    ---
    url: /blog/how-to-source-products-at-trade-shows/
    title: How to source products at a trade show
    description: One or two sentences for search results.
    date: 2026-10-20
    eyebrow: Guide
    read: 12
    card: Text for the card on /blog/ (optional, else description)
    cta_title: ...
    cta_text: ...
    ---
    Markdown body. A section "## Frequently asked questions" with "### Question"
    headings becomes FAQPage JSON-LD, which search engines and AI answer
    engines read (Moshe, 2026-10-20: "we need to work on SEO and AEO").

Writes each page, the cards on blog/index.html and compare/index.html (between
the AUTO markers), sitemap.xml entries and the llms.txt link list.
Run by build_help.sh on every deploy.

The markdown here is a small subset: #/##/### headings, paragraphs, - and 1.
lists, > quotes, | tables |, **bold**, *italic*, `code`, [links](url).
"""
import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = "https://showsourcing.app"
APPSTORE = "https://apps.apple.com/us/app/show-sourcing-manager/id6758863749"
TEMPLATE = ROOT / "blog" / "landed-cost-fob-to-ldp" / "index.html"


# ------------------------------------------------------------- markdown
def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![*\w])\*([^*]+)\*(?!\w)", r"<em>\1</em>", s)

    def link(m):
        text, url = m.group(1), m.group(2)
        ext = url.startswith("http") and not url.startswith(SITE)
        rel = ' rel="noopener"' if ext else ""
        return f'<a href="{url}"{rel}>{text}</a>'
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def md_to_html(md: str) -> str:
    out, lines, i = [], md.strip("\n").split("\n"), 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = re.match(r"^(#{2,3}) (.+)$", line)
        if m:
            tag = "h2" if len(m.group(1)) == 2 else "h3"
            out.append(f'<{tag} id="{slugify(m.group(2))}">{inline(m.group(2))}</{tag}>')
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            head, body = rows[0], rows[1:]
            t = ['<div class="table-wrap"><table class="cost-table"><thead><tr>']
            t += [f"<th>{inline(c)}</th>" for c in head]
            t.append("</tr></thead><tbody>")
            for r in body:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue
        if re.match(r"^(- |\d+\. )", line):
            ordered = bool(re.match(r"^\d+\. ", line))
            items = []
            while i < len(lines) and re.match(r"^(- |\d+\. )", lines[i]):
                text = re.sub(r"^(- |\d+\. )", "", lines[i])
                i += 1
                while i < len(lines) and lines[i].startswith("  ") and lines[i].strip():
                    text += " " + lines[i].strip()
                    i += 1
                items.append(f"<li>{inline(text)}</li>")
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
            continue
        if line.startswith("> "):
            q = []
            while i < len(lines) and lines[i].startswith(">"):
                q.append(lines[i].lstrip("> ").strip())
                i += 1
            out.append(f"<blockquote><p>{inline(' '.join(q))}</p></blockquote>")
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{2,3} |\||- |\d+\. |> )", lines[i]):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")
    return "\n\n    ".join(out)


def strip_tags(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


# ------------------------------------------------------------- content
def load(path: Path) -> dict:
    text = path.read_text()
    _, front, body = text.split("---\n", 2)
    meta = {}
    for line in front.strip().split("\n"):
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    meta["body_md"] = body
    meta["read"] = meta.get("read") or str(max(3, round(len(body.split()) / 230)))
    return meta


def faqs(body_md: str) -> list[tuple[str, str]]:
    m = re.search(r"^## Frequently asked questions\n(.*?)(?=^## |\Z)", body_md, re.M | re.S)
    if not m:
        return []
    out = []
    for block in re.split(r"^### ", m.group(1), flags=re.M)[1:]:
        q, _, a = block.partition("\n")
        out.append((q.strip(), strip_tags(md_to_html(a))))
    return out


# ------------------------------------------------------------- page
def nice_date(d: str) -> str:
    y, m, dd = map(int, d.split("-"))
    return date(y, m, dd).strftime("%b %-d, %Y")


def page(meta: dict, css: str, header: str, footer: str) -> str:
    url = SITE + meta["url"]
    title, desc = meta["title"], meta["description"]
    is_compare = meta["url"].startswith("/compare/")
    crumbs = [("Home", SITE + "/"),
              ("Compare", SITE + "/compare/") if is_compare else ("Blog", SITE + "/blog/"),
              (title, url)]
    graph = [
        {
            "@type": "BlogPosting" if not is_compare else "Article",
            "headline": title,
            "description": desc,
            "image": SITE + "/app-icon.png",
            "datePublished": meta["date"],
            "dateModified": meta.get("modified", meta["date"]),
            "author": {"@type": "Organization", "name": "DNZ", "url": SITE},
            "publisher": {"@type": "Organization", "name": "DNZ",
                          "logo": {"@type": "ImageObject", "url": SITE + "/app-icon.png"}},
            "mainEntityOfPage": {"@type": "WebPage", "@id": url},
            "about": {"@type": "SoftwareApplication", "name": "Show Sourcing", "url": SITE,
                      "operatingSystem": "iOS, iPadOS, macOS", "applicationCategory": "BusinessApplication"},
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": n + 1, "name": name, "item": item}
                                for n, (name, item) in enumerate(crumbs)],
        },
    ]
    qa = faqs(meta["body_md"])
    if qa:
        graph.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]})
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, indent=2, ensure_ascii=False)
    e = lambda s: html.escape(s, quote=True)
    cta = ""
    if meta.get("cta_title"):
        cta = f"""
    <aside class="cta">
        <h3>{e(meta['cta_title'])}</h3>
        <p>{e(meta['cta_text'])}</p>
        <a class="button" href="{APPSTORE}">Try it free for 7 days &rarr;</a>
    </aside>"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="/theme.js"></script>
    <link rel="stylesheet" href="/theme.css">
    <title>{e(title)} &mdash; Show Sourcing</title>
    <meta name="description" content="{e(desc)}">
    <meta name="author" content="DNZ">
    <meta name="robots" content="index,follow,max-image-preview:large">
    <meta name="theme-color" content="#060a18" data-dark="#060a18" data-light="#f6f7fb">
    <link rel="canonical" href="{url}">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="Show Sourcing">
    <meta property="og:url" content="{url}">
    <meta property="og:title" content="{e(title)}">
    <meta property="og:description" content="{e(desc)}">
    <meta property="og:image" content="{SITE}/app-icon.png">
    <meta property="article:published_time" content="{meta['date']}">
    <meta property="article:modified_time" content="{meta.get('modified', meta['date'])}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{e(title)}">
    <meta name="twitter:description" content="{e(desc)}">
    <meta name="twitter:image" content="{SITE}/app-icon.png">
    <link rel="icon" type="image/png" href="/favicon.png">
    <link rel="apple-touch-icon" href="/app-icon.png">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <script type="application/ld+json">
{ld}
    </script>
    <style>{css}
        .table-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
        article h3 {{ margin-top: 1.6em; }}
    </style>
</head>
<body>

{header}

<article>
    <span class="article-eyebrow">{e(meta.get('eyebrow', 'Guide'))}</span>
    <h1>{e(title)}</h1>
    <div class="article-meta">
        <span>{nice_date(meta.get('modified', meta['date']))}</span>
        <span class="dot"></span>
        <span>{meta['read']} min read</span>
        <span class="dot"></span>
        <span>By DNZ</span>
    </div>

    {md_to_html(meta['body_md'])}
{cta}
</article>

{footer}

</body>
</html>
"""


def card(meta: dict) -> str:
    e = lambda s: html.escape(s, quote=True)
    return f"""        <a class="post-card" href="{meta['url']}">
            <span class="meta">{nice_date(meta['date'])} &middot; {meta['read']} min read</span>
            <h2>{e(meta['title'])}</h2>
            <p>{e(meta.get('card') or meta['description'])}</p>
            <span class="read-more">Read &rarr;</span>
        </a>
"""


def replace_between(text: str, start: str, end: str, new: str) -> str:
    a, b = text.index(start) + len(start), text.index(end)
    return text[:a] + "\n" + new + text[b:]


def main():
    tpl = TEMPLATE.read_text()
    css = re.search(r"<style>(.*?)</style>", tpl, re.S).group(1)
    header = re.search(r'<header id="site-header">.*?</header>', tpl, re.S).group(0)
    header = header.replace('<a href="/blog/">Blog</a>', '<a href="/blog/">Blog</a>\n        <a href="/compare/">Compare</a>', 1)
    footer = re.search(r'<footer id="site-footer">.*?</footer>', tpl, re.S).group(0)

    posts = sorted((load(p) for p in (ROOT / "content").glob("*.md")),
                   key=lambda m: (m["date"], m.get("order", "0")), reverse=True)
    for m in posts:
        out = ROOT / m["url"].strip("/") / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page(m, css, header, footer))

    guides = [m for m in posts if m["url"].startswith("/blog/")]
    vs = [m for m in posts if m["url"].startswith("/compare/")]

    blog = ROOT / "blog" / "index.html"
    blog.write_text(replace_between(blog.read_text(), "<!-- AUTO:guides -->", "<!-- /AUTO:guides -->",
                                    "".join(card(m) for m in guides) + "        "))
    cmp_ = ROOT / "compare" / "index.html"
    if "<!-- AUTO:vs -->" in cmp_.read_text():
        items = "".join(f'<li><a href="{m["url"]}">{html.escape(m["title"])}</a></li>' for m in vs)
        cmp_.write_text(replace_between(cmp_.read_text(), "<!-- AUTO:vs -->", "<!-- /AUTO:vs -->", items))

    sm = ROOT / "sitemap.xml"
    urls = "".join(f'  <url><loc>{SITE}{m["url"]}</loc><lastmod>{m.get("modified", m["date"])}</lastmod>'
                   f'<changefreq>monthly</changefreq><priority>0.7</priority></url>\n' for m in posts)
    sm.write_text(replace_between(sm.read_text(), "<!-- AUTO:content -->", "<!-- /AUTO:content -->", urls + "  "))

    for name in ("llms.txt", "llms-full.txt"):
        f = ROOT / name
        lines = "".join(f"- [{m['title']}]({SITE}{m['url']}): {m['description']}\n" for m in posts)
        txt = f.read_text()
        block = f"<!-- AUTO:content -->\n## Guides and comparisons\n\n{lines}<!-- /AUTO:content -->"
        if "<!-- AUTO:content -->" in txt:
            txt = re.sub(r"<!-- AUTO:content -->.*?<!-- /AUTO:content -->", block, txt, flags=re.S)
        else:
            txt = txt.rstrip("\n") + "\n\n" + block + "\n"
        f.write_text(txt)
    print(f"built {len(guides)} guides, {len(vs)} comparisons")


if __name__ == "__main__":
    main()
