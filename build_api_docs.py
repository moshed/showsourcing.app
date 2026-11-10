#!/usr/bin/env python3
"""Builds /docs/api/ (people) from docs/api.md (agents read the .md itself, 2026-11-10).

docs/api.md is the one source. The spec for tools is openapi.json (hand-kept, same facts).
Uses build_blog's markdown subset and the guide template's style; adds code blocks and #### headings.
Run by build_help.sh on every deploy.
"""
import html, json, re
from pathlib import Path
import build_blog as bb

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "docs" / "api.md"
OUT = ROOT / "docs" / "api" / "index.html"
URL = bb.SITE + "/docs/api/"
TITLE = "Show Sourcing API"
DESC = ("REST API and MCP server for Show Sourcing: read and add your team's products and vendors from code, "
        "Claude, ChatGPT or Claude Code. One token, made in the app.")


def body_html(md: str) -> str:
    md = re.sub(r"^# .*\n", "", md, count=1)              # the title is the page's h1
    blocks = []
    def keep(m):
        blocks.append(m.group(2))
        return f"\n@@CODE{len(blocks) - 1}@@\n"
    md = re.sub(r"```(\w*)\n(.*?)```", keep, md, flags=re.S)
    md = re.sub(r"^#### ", "### ", md, flags=re.M)
    out = bb.md_to_html(md)
    for i, code in enumerate(blocks):
        pre = f'<pre><code>{html.escape(code.rstrip())}</code></pre>'
        out = out.replace(f"<p>@@CODE{i}@@</p>", pre).replace(f"@@CODE{i}@@", pre)
    return out


def main():
    tpl = bb.TEMPLATE.read_text()
    css = re.search(r"<style>(.*?)</style>", tpl, re.S).group(1)
    header = re.search(r'<header id="site-header">.*?</header>', tpl, re.S).group(0)
    footer = re.search(r'<footer id="site-footer">.*?</footer>', tpl, re.S).group(0)
    ld = json.dumps({"@context": "https://schema.org", "@type": "TechArticle", "headline": TITLE, "description": DESC,
                     "url": URL, "author": {"@type": "Organization", "name": "DNZ", "url": bb.SITE},
                     "about": {"@type": "SoftwareApplication", "name": "Show Sourcing", "url": bb.SITE}}, indent=2)
    e = lambda s: html.escape(s, quote=True)
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="/theme.js"></script>
    <link rel="stylesheet" href="/theme.css">
    <title>{e(TITLE)} &mdash; Show Sourcing</title>
    <meta name="description" content="{e(DESC)}">
    <meta name="robots" content="index,follow">
    <meta name="theme-color" content="#060a18" data-dark="#060a18" data-light="#f6f7fb">
    <link rel="canonical" href="{URL}">
    <link rel="alternate" type="text/markdown" href="/docs/api.md" title="This page as plain text">
    <link rel="service-desc" type="application/json" href="/openapi.json" title="OpenAPI spec">
    <meta property="og:title" content="{e(TITLE)}">
    <meta property="og:description" content="{e(DESC)}">
    <meta property="og:url" content="{URL}">
    <link rel="icon" type="image/png" href="/favicon.png">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <script type="application/ld+json">
{ld}
    </script>
    <style>{css}
        .table-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
        article h3 {{ margin-top: 1.6em; }}
        article pre {{ overflow-x: auto; padding: 14px 16px; border-radius: 12px; margin: 1em 0;
            background: rgba(127,127,127,0.12); font: 13px/1.5 'JetBrains Mono', ui-monospace, monospace; }}
        article pre code {{ background: none; padding: 0; white-space: pre; }}
        .doc-links {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 1em 0 2em; }}
        .doc-links a {{ padding: 6px 12px; border-radius: 999px; border: 1px solid rgba(127,127,127,0.35); text-decoration: none; font-size: 14px; }}
    </style>
</head>
<body>

{header}

<article>
    <span class="article-eyebrow">Developers</span>
    <h1>{e(TITLE)}</h1>
    <div class="doc-links"><a href="/docs/api.md">Plain text for AI agents</a><a href="/openapi.json">OpenAPI spec</a></div>

    {body_html(SRC.read_text())}
</article>

{footer}

</body>
</html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page)
    print(f"Built {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
