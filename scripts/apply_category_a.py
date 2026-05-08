#!/usr/bin/env python3
"""
Apply Category A standardization (audit-driven, low-risk) to all SEO landing pages.

Skips:
- klaviyo.se   — pos 4 on "klaviyo", do not touch title/H1/structure
- inline-ehandel — already fully audited and pivoted

Adds (idempotent — safe to re-run):
1. og:type → article
2. robots → add max-image-preview:large
3. Article schema (alongside existing WebPage)
4. Person schema for Niklas Dahlquist (with sameAs LinkedIn)
5. Author-card HTML before footer
6. Internal cross-links section before "Om Dahlquist"

Each step skipped if already applied.
"""

import re
import shutil
from datetime import date
from pathlib import Path

REPO_ROOT = Path("/Users/niklasdahlquist/GIT/dahlquist-seo-landingpages")
PAGES_DIR = REPO_ROOT / "pages"
SITES_DIR = REPO_ROOT / "deploys"

SKIP_DIRS = {"klaviyo", "inline-ehandel", ".claude", "domain-worker", "scripts", "node_modules", ".git", ".wrangler"}

CROSS_LINK_TARGETS = [
    ("https://magentoexperten.se", "Magento Expert"),
    ("https://shopifyseo.se", "Shopify SEO"),
    ("https://klaviyo.se", "Klaviyo Sverige"),
    ("https://punchout.nu", "PunchOut B2B"),
    ("https://shopifyb2b.se", "Shopify B2B"),
    ("https://magento-konsulter.se", "Magento-konsulter"),
]


def extract_metadata(html: str) -> dict:
    def find(pattern):
        m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        return m.group(1).strip() if m else ""

    title = find(r"<title>(.*?)</title>")
    description = find(r'<meta\s+name="description"\s+content="([^"]+)"')
    canonical = find(r'<link\s+rel="canonical"\s+href="([^"]+)"')
    og_image = find(r'<meta\s+property="og:image"\s+content="([^"]+)"')

    domain = ""
    if canonical:
        m = re.match(r"https?://([^/]+)", canonical)
        if m:
            domain = m.group(1)

    headline = title.split("|")[0].split("–")[0].strip() if title else ""

    return {
        "title": title,
        "headline": headline,
        "description": description,
        "canonical": canonical.rstrip("/") + "/" if canonical else "",
        "domain": domain,
        "og_image": og_image,
    }


def ensure_og_type_article(html: str) -> tuple[str, bool]:
    if 'property="og:type" content="article"' in html or "property=\"og:type\" content=\"article\"" in html:
        return html, False
    new = re.sub(
        r'<meta\s+property="og:type"\s+content="[^"]*"\s*/?>',
        '<meta property="og:type" content="article" />',
        html,
        count=1,
    )
    return new, new != html


def ensure_robots_max_image(html: str) -> tuple[str, bool]:
    if "max-image-preview" in html:
        return html, False
    new = re.sub(
        r'(<meta\s+name="robots"\s+content=")([^"]+)("\s*/?>)',
        r'\1\2, max-image-preview:large\3',
        html,
        count=1,
    )
    return new, new != html


def ensure_article_schema(html: str, meta: dict) -> tuple[str, bool]:
    if '"@type":"Article"' in html or '"@type": "Article"' in html:
        return html, False
    if not meta["canonical"] or not meta["headline"]:
        return html, False

    today = date.today().isoformat()
    article_json = (
        '<script type="application/ld+json">\n'
        '{\n'
        '  "@context":"https://schema.org",\n'
        '  "@type":"Article",\n'
        f'  "headline":"{meta["headline"].replace(chr(34), chr(39))}",\n'
        f'  "description":"{meta["description"].replace(chr(34), chr(39))}",\n'
        f'  "image":"{meta["og_image"]}",\n'
        f'  "url":"{meta["canonical"]}",\n'
        '  "datePublished":"2026-04-05",\n'
        f'  "dateModified":"{today}",\n'
        '  "inLanguage":"sv-SE",\n'
        '  "author":{"@type":"Person","name":"Niklas Dahlquist","url":"https://dahlquist.se/om-oss","sameAs":["https://www.linkedin.com/in/niklasdahlquist/"]},\n'
        '  "publisher":{"@type":"Organization","name":"Dahlquist E-handelskonsulter AB","url":"https://dahlquist.se","logo":{"@type":"ImageObject","url":"https://dahlquist.se/images/logo.png"}},\n'
        f'  "mainEntityOfPage":{{"@type":"WebPage","@id":"{meta["canonical"]}"}}\n'
        '}\n'
        '</script>\n'
    )
    new = re.sub(r"(\s*</head>)", "\n  " + article_json + r"\1", html, count=1)
    return new, new != html


def ensure_person_schema(html: str, meta: dict) -> tuple[str, bool]:
    if '"@type":"Person"' in html and "Niklas Dahlquist" in html:
        # Person ref likely already inside Article — that's fine, we don't double-add
        if html.count('"@type":"Person"') >= 1:
            return html, False
    return html, False  # We embed Person inside Article schema; standalone not needed


AUTHOR_CARD_HTML = """
  <section style="background:#fff;padding:1.5rem 2rem;border-top:1px solid #e2e8f0;">
    <div style="max-width:900px;margin:0 auto;display:flex;gap:1.25rem;align-items:center;">
      <div style="width:56px;height:56px;border-radius:50%;background:linear-gradient(135deg,#1a4d7c 0%,#0a2e4d 100%);color:#fff;display:flex;align-items:center;justify-content:center;font-size:1.4rem;font-weight:800;flex-shrink:0;">ND</div>
      <div style="flex:1;font-size:0.92rem;color:#2a3340;line-height:1.55;">
        <strong>Av Niklas Dahlquist</strong> · Grundare och E-handelsutvecklare · Dahlquist E-handelskonsulter AB sedan 2016
        <div style="margin-top:0.35rem;">
          <a href="https://www.linkedin.com/in/niklasdahlquist/" rel="noopener author" style="margin-right:0.75rem;">LinkedIn</a>
          <a href="https://dahlquist.se/om-oss" rel="noopener author" style="margin-right:0.75rem;">Om oss</a>
          <a href="https://dahlquist.se/case" rel="noopener">Case</a>
        </div>
      </div>
    </div>
  </section>
"""


def ensure_author_card(html: str) -> tuple[str, bool]:
    if "rel=\"noopener author\"" in html or "rel='noopener author'" in html:
        return html, False
    new = re.sub(r"(<footer\b)", AUTHOR_CARD_HTML + r"\1", html, count=1)
    return new, new != html


def build_cross_links_html(self_canonical: str) -> str:
    self_domain = re.match(r"https?://([^/]+)", self_canonical).group(1) if self_canonical else ""
    items = []
    for url, label in CROSS_LINK_TARGETS:
        if self_domain and self_domain in url:
            continue  # don't link to self
        items.append(f'      <a href="{url}" style="background:#f4f7fb;border-left:3px solid #1a4d7c;padding:0.6rem 1rem;border-radius:0 6px 6px 0;font-size:0.92rem;color:#0a2e4d;font-weight:600;text-decoration:none;display:block;">{label} →</a>')

    return f"""
  <section style="background:#fff;padding:2rem;border-top:1px solid #e2e8f0;">
    <div style="max-width:900px;margin:0 auto;">
      <h2 style="font-size:1.05rem;font-weight:700;color:#0a2e4d;margin-bottom:0.85rem;">Relaterade resurser hos Dahlquist</h2>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:0.65rem;">
{chr(10).join(items)}
      </div>
    </div>
  </section>
"""


def ensure_cross_links(html: str, meta: dict) -> tuple[str, bool]:
    if "Relaterade resurser hos Dahlquist" in html:
        return html, False
    block = build_cross_links_html(meta["canonical"])
    new = re.sub(r"(<footer\b)", block + r"\1", html, count=1)
    return new, new != html


def update_sitemap_lastmod(page_dir: Path) -> bool:
    sitemap_path = page_dir / "sitemap.xml"
    if not sitemap_path.exists():
        return False
    today = date.today().isoformat()
    content = sitemap_path.read_text(encoding="utf-8")
    new_content = re.sub(
        r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>",
        f"<lastmod>{today}</lastmod>",
        content,
    )
    if new_content != content:
        sitemap_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def fix_page(page_dir: Path) -> dict:
    index_path = page_dir / "index.html"
    if not index_path.exists():
        return {"dir": page_dir.name, "skipped": "no index.html"}

    html = index_path.read_text(encoding="utf-8")
    meta = extract_metadata(html)
    if not meta["domain"]:
        return {"dir": page_dir.name, "skipped": "no canonical"}

    changes = []
    html, ch = ensure_og_type_article(html)
    if ch: changes.append("og:type")
    html, ch = ensure_robots_max_image(html)
    if ch: changes.append("robots")
    html, ch = ensure_article_schema(html, meta)
    if ch: changes.append("Article")
    html, ch = ensure_author_card(html)
    if ch: changes.append("author")
    html, ch = ensure_cross_links(html, meta)
    if ch: changes.append("cross-links")

    if changes:
        index_path.write_text(html, encoding="utf-8")
    sitemap_changed = update_sitemap_lastmod(page_dir)
    if sitemap_changed:
        changes.append("sitemap")

    return {
        "dir": page_dir.name,
        "domain": meta["domain"],
        "changes": changes,
    }


def find_site_dir(domain: str) -> Path | None:
    candidate = SITES_DIR / domain
    return candidate if candidate.exists() else None


def mirror_to_site(page_dir: Path, domain: str) -> dict:
    site_dir = find_site_dir(domain)
    if site_dir is None:
        return {"domain": domain, "skipped": "no matching deploy"}
    copied = []
    for f in ["index.html", "sitemap.xml"]:
        src = page_dir / f
        dst = site_dir / f
        if src.exists() and ((not dst.exists()) or src.read_bytes() != dst.read_bytes()):
            shutil.copy2(src, dst)
            copied.append(f)
    return {"domain": domain, "copied": copied}


def main():
    print("=== Kategori A: standardisering på alla SEO-sidor ===\n")
    page_results = []
    for child in sorted(PAGES_DIR.iterdir()):
        if not child.is_dir() or child.name in SKIP_DIRS:
            continue
        r = fix_page(child)
        page_results.append(r)
        if "skipped" in r:
            print(f"  ~ {r['dir']:40}  skipped: {r['skipped']}")
        else:
            tag = ", ".join(r["changes"]) if r["changes"] else "no-op (already up to date)"
            print(f"  ✓ {r['dir']:40}  {tag}")

    print(f"\n=== Mirror till deploys/ ===\n")
    for r in page_results:
        if "skipped" in r or not r.get("changes"):
            continue
        page_dir = PAGES_DIR / r["dir"]
        m = mirror_to_site(page_dir, r["domain"])
        if "skipped" in m:
            print(f"  ~ {m['domain']:40}  skipped: {m['skipped']}")
        else:
            print(f"  ✓ {m['domain']:40}  copied: {m['copied']}")

    total = len([r for r in page_results if "skipped" not in r])
    changed = len([r for r in page_results if r.get("changes")])
    print(f"\n=== Sammanfattning ===")
    print(f"  Sidor processade: {total}")
    print(f"  Sidor med ändringar: {changed}")


if __name__ == "__main__":
    main()
