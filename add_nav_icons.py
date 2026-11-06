"""Add a small icon before each link in the top menu of every page.

Runs from build_help.sh after the page builders, so generated pages get icons too.
Safe to run again: a link that already has an icon is skipped.
"""
import pathlib
import re

ICONS = {
    'Use cases': '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    'Pricing': '<path d="M20.6 13.4l-7.2 7.2a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z"/><circle cx="8" cy="8" r="1.5"/>',
    'Help': '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 0 1 4.9.8c0 1.7-2.4 2.2-2.4 3.7"/><path d="M12 17h.01"/>',
    'Blog': '<path d="M4 20l1-4L16 5l3 3L8 19z"/><path d="M14 7l3 3"/>',
    'Compare': '<path d="M8 3v18M16 3v18"/><path d="M3 8h5M16 16h5"/>',
    'FAQ': '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/>',
    'Privacy Policy': '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
    'Terms of Service': '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/><path d="M8 13h8M8 17h8"/>',
    'Web Portal': '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 0 1 0 18a14 14 0 0 1 0-18z"/>',
    'Download': '<path d="M12 3v12"/><path d="M7 11l5 5 5-5"/><path d="M4 21h16"/>',
}
SVG = ('<svg class="nav-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
       'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" '
       'style="vertical-align:-3px;margin-right:5px">{}</svg>')
LINK = re.compile(r'(<a\b[^>]*>)(' + '|'.join(map(re.escape, ICONS)) + r')(</a>)')


def add(html: str) -> str:
    m = re.search(r'<header\b.*?</header>', html, re.S)
    if not m:
        return html
    head = LINK.sub(lambda l: l.group(1) + SVG.format(ICONS[l.group(2)]) + l.group(2) + l.group(3), m.group(0))
    return html[:m.start()] + head + html[m.end():]


root = pathlib.Path(__file__).parent
changed = 0
for f in root.rglob('*.html'):
    if any(p in f.parts for p in ('ocr', 'supabase', 'lib', 'node_modules')):
        continue
    old = f.read_text(encoding='utf-8')
    new = add(old)
    if new != old:
        f.write_text(new, encoding='utf-8')
        changed += 1
print(f'Nav icons: added to {changed} pages')
