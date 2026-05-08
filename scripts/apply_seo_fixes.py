#!/usr/bin/env python3
"""
Apply SEO fixes from audit (magentoexperten.se reference) to all 47 dahlquist domain pages.

Fixes applied:
  #1  Unique llms.txt per domain (rewritten from page metadata)
  #3  Add `image` property to WebPage and ProfessionalService schema
  #4+5  vercel.json per site with security headers + Cache-Control
  #6  ProfessionalService.url consistency (point to canonical, sameAs dahlquist.se)
  #8  <link rel="sitemap"> + <meta name="theme-color">

Skipped (require external work):
  #2  Unique OG image per niche — needs image generation
  #7  Service schema for service cards — needs per-page card parsing
  #9  Hero images — needs image generation

Idempotent: safe to re-run.
"""

import os
import re
import json
import shutil
from pathlib import Path

PAGES_DIR = Path("/Users/niklasdahlquist/GIT/dahlquist-seo-landingpages/pages")
SITES_DIR = Path("/Users/niklasdahlquist/GIT/dahlquist-seo-landingpages/deploys")

SKIP_DIRS = {"domain-worker", "scripts", "node_modules", ".git", ".wrangler"}
SKIP_FILES = {"package.json", ".gitignore"}

THEME_COLOR = "#e8472b"  # The orange used across the brand

VERCEL_HEADERS = {
    "headers": [
        {
            "source": "/(.*)",
            "headers": [
                {"key": "Strict-Transport-Security", "value": "max-age=63072000; includeSubDomains; preload"},
                {"key": "X-Content-Type-Options", "value": "nosniff"},
                {"key": "X-Frame-Options", "value": "SAMEORIGIN"},
                {"key": "Referrer-Policy", "value": "strict-origin-when-cross-origin"},
                {"key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()"},
            ],
        },
        {
            "source": "/",
            "headers": [
                {"key": "Cache-Control", "value": "public, max-age=3600, s-maxage=86400, stale-while-revalidate=604800"},
            ],
        },
        {
            "source": "/index.html",
            "headers": [
                {"key": "Cache-Control", "value": "public, max-age=3600, s-maxage=86400, stale-while-revalidate=604800"},
            ],
        },
        {
            "source": "/sitemap.xml",
            "headers": [
                {"key": "Cache-Control", "value": "public, max-age=3600, s-maxage=86400"},
                {"key": "Content-Type", "value": "application/xml; charset=utf-8"},
            ],
        },
        {
            "source": "/robots.txt",
            "headers": [
                {"key": "Cache-Control", "value": "public, max-age=3600, s-maxage=86400"},
            ],
        },
        {
            "source": "/llms.txt",
            "headers": [
                {"key": "Cache-Control", "value": "public, max-age=3600, s-maxage=86400"},
            ],
        },
    ],
    "cleanUrls": True,
}


def extract_metadata(html: str) -> dict:
    """Pull title, description, canonical from existing HTML head."""
    def find(pattern):
        m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        return m.group(1).strip() if m else ""

    title = find(r"<title>(.*?)</title>")
    description = find(r'<meta\s+name="description"\s+content="([^"]+)"')
    canonical = find(r'<link\s+rel="canonical"\s+href="([^"]+)"')
    og_image = find(r'<meta\s+property="og:image"\s+content="([^"]+)"')
    og_title = find(r'<meta\s+property="og:title"\s+content="([^"]+)"')
    og_desc = find(r'<meta\s+property="og:description"\s+content="([^"]+)"')

    domain = ""
    if canonical:
        m = re.match(r"https?://([^/]+)", canonical)
        if m:
            domain = m.group(1)

    return {
        "title": title,
        "description": description,
        "canonical": canonical.rstrip("/") + "/",
        "domain": domain,
        "og_image": og_image,
        "og_title": og_title,
        "og_description": og_desc,
    }


def detect_niche(meta: dict, dir_name: str) -> str:
    """Infer the niche keyword from title/dir name."""
    text = (meta.get("title", "") + " " + dir_name).lower()
    if "magento" in text or "adobe commerce" in text:
        return "magento"
    if "shopify" in text:
        return "shopify"
    if "klaviyo" in text:
        return "klaviyo"
    if "punchout" in text or "ariba" in text:
        return "punchout"
    if "pim" in text:
        return "pim"
    if "ai" in text or "engineer" in text or "utvecklare" in text:
        return "ai"
    if "ehandel" in text or "e-handel" in text or "handel" in text or "e-handelsystem" in text:
        return "ehandel"
    if "b2b" in text or "wunderwerk" in text or "centrumhandel" in text:
        return "b2b"
    if "konsult" in text or "byrå" in text or "byra" in text or "experter" in text:
        return "konsult"
    if "headless" in text:
        return "headless"
    return "ehandel"


def generate_llms_txt(meta: dict, dir_name: str) -> str:
    """Generate a unique llms.txt for this domain."""
    title = meta["title"].split("|")[0].split("–")[0].strip()
    description = meta["description"]
    domain = meta["domain"]
    canonical = meta["canonical"]
    niche = detect_niche(meta, dir_name)

    # Niche-specific service emphasis
    services_by_niche = {
        "magento": [
            "Magento 2 / Adobe Commerce-utveckling",
            "Hyva Theme-implementation",
            "ERP-integrationer (Business Central, SAP, Visma, Fortnox)",
            "Magento-migration (M1 → M2, eller från andra plattformar)",
            "Adobe Commerce Cloud (ece-tools, Fastly CDN)",
        ],
        "shopify": [
            "Shopify och Shopify Plus-utveckling",
            "Theme-utveckling (Online Store 2.0, Liquid)",
            "Custom Apps med Remix + GraphQL Admin API",
            "Klaviyo-integration och flows",
            "Migration från Magento, WooCommerce, Prestashop till Shopify",
        ],
        "klaviyo": [
            "Klaviyo-flöden (welcome, abandoned cart, post-purchase)",
            "Custom segments med profile properties och events",
            "Klaviyo + Shopify / Magento-integration",
            "API-utveckling för custom events och attribut",
            "A/B-testning och deliverability-optimering",
        ],
        "punchout": [
            "PunchOut-integration mot SAP Ariba, Coupa, Ivalua",
            "B2B-handel på Magento och Shopify",
            "OCI och cXML-protokoll",
            "Kontraktsprislistor och kundspecifika kataloger",
            "EDI-integration",
        ],
        "pim": [
            "Akeneo PIM-implementation",
            "Pimcore PIM-utveckling",
            "PIM → e-handelsplattform-synk (Magento, Shopify)",
            "Datamodellering, attributstrukturer och kategorimapping",
            "Custom connectors mot ERP och DAM",
        ],
        "ai": [
            "AI-driven e-handelsutveckling",
            "LLM-integration mot Shopify och Magento",
            "Embeddings-baserade produktrekommendationer",
            "AI-genererat produktinnehåll",
            "Konsultation kring AI-strategi i e-handel",
        ],
        "ehandel": [
            "E-handelsstrategi och plattformsval",
            "Magento, Shopify, BigCommerce-utveckling",
            "ERP-integration och affärslogik",
            "Konvertering och sökmotoroptimering",
            "Klaviyo, GA4 och tracking-setup",
        ],
        "b2b": [
            "B2B-handel på Magento och Shopify",
            "PunchOut, kontraktsprislistor och kundkataloger",
            "ERP-integration (SAP, Business Central, Visma)",
            "Offer-flöden och godkännandeprocesser",
            "Multi-store och multi-currency",
        ],
        "konsult": [
            "Magento- och Shopify-utveckling",
            "ERP-integration",
            "Klaviyo, PunchOut, B2B-handel",
            "Migration mellan e-handelsplattformar",
            "Teknisk inventering och arkitekturrådgivning",
        ],
        "headless": [
            "Headless e-handel med Magento PWA Studio",
            "Shopify Hydrogen + Oxygen",
            "Storefront API och GraphQL",
            "Next.js / Remix mot e-handels-backend",
            "Performance och Core Web Vitals-optimering",
        ],
    }

    services = services_by_niche.get(niche, services_by_niche["ehandel"])
    services_md = "\n".join(f"- {s}" for s in services)

    return f"""# {title}

> {description}

Sajt: {canonical}
Drivs av: Dahlquist E-handelskonsulter AB (https://dahlquist.se)

## Specialitet

{services_md}

## Om Dahlquist

Dahlquist E-handelskonsulter AB grundades 2016 av Niklas Dahlquist. Vi har genomfört över 150 e-handelsprojekt för svenska och internationella varumärken — bland annat STIHL, SONAX och Arrak Outdoor.

Vi specialiserar oss på Magento/Adobe Commerce, Shopify Plus, ERP-integration, Klaviyo, PunchOut och B2B-handel.

## Kontakt

- Huvudsajt: https://dahlquist.se
- Om oss: https://dahlquist.se/om-oss
- Case: https://dahlquist.se/case
- Kontakt: https://dahlquist.se/kontakt
"""


def update_html(html: str, meta: dict) -> str:
    """Apply HTML mutations: theme-color, sitemap link, schema image, PS.url consistency."""
    canonical = meta["canonical"]
    og_image = meta.get("og_image", "")

    # 1. Add theme-color + link rel=sitemap if missing
    if 'name="theme-color"' not in html:
        insertion = f'  <meta name="theme-color" content="{THEME_COLOR}" />\n  <link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml" />\n'
        # Insert before </head>
        html = re.sub(r"(\s*</head>)", "\n" + insertion + r"\1", html, count=1)

    # 2. Add `image` property to WebPage schema
    if og_image:
        # WebPage block — has "url":"..." matching canonical
        webpage_pattern = r'(\{"@context":"https://schema\.org","@type":"WebPage"[^}]*?"url":"' + re.escape(canonical) + r'")'
        if re.search(webpage_pattern, html) and '"image":"' not in re.search(webpage_pattern, html).group(0):
            html = re.sub(
                webpage_pattern,
                r'\1,"image":"' + og_image + '"',
                html,
                count=1,
            )

        # ProfessionalService block — multi-line JSON, easier to detect by @type
        # Find PS block, add "image" if missing
        ps_match = re.search(r'(\{\s*"@context":\s*"https://schema\.org",\s*"@type":\s*"ProfessionalService"[^}]+\})', html, re.DOTALL)
        if ps_match:
            ps_block = ps_match.group(1)
            if '"image"' not in ps_block:
                # Insert image after url
                new_ps = re.sub(
                    r'("url":\s*"[^"]+",)',
                    r'\1\n    "image": "' + og_image + '",',
                    ps_block,
                    count=1,
                )
                html = html.replace(ps_block, new_ps)

    # 3. Fix ProfessionalService.url to canonical (current points to dahlquist.se subpath)
    # Make `url` = canonical, add `sameAs` keeping existing dahlquist link
    ps_match = re.search(r'(\{\s*"@context":\s*"https://schema\.org",\s*"@type":\s*"ProfessionalService"[^}]+\})', html, re.DOTALL)
    if ps_match:
        ps_block = ps_match.group(1)
        # Detect current url
        url_match = re.search(r'"url":\s*"(https://dahlquist\.se[^"]*)"', ps_block)
        if url_match:
            dahlquist_url = url_match.group(1)
            # Replace url field to canonical
            new_ps = re.sub(
                r'"url":\s*"https://dahlquist\.se[^"]*"',
                f'"url": "{canonical}"',
                ps_block,
                count=1,
            )
            # Update sameAs to point to dahlquist (keep that connection)
            if '"sameAs"' in new_ps:
                # Replace existing sameAs to ensure it has the dahlquist URL
                new_ps = re.sub(
                    r'"sameAs":\s*\[[^\]]*\]',
                    f'"sameAs": ["{dahlquist_url}"]',
                    new_ps,
                    count=1,
                )
            html = html.replace(ps_block, new_ps)

    return html


def fix_page(page_dir: Path) -> dict:
    """Apply all fixes to one page directory. Returns summary."""
    index_path = page_dir / "index.html"
    if not index_path.exists():
        return {"dir": page_dir.name, "skipped": "no index.html"}

    html = index_path.read_text(encoding="utf-8")
    meta = extract_metadata(html)

    if not meta["domain"]:
        return {"dir": page_dir.name, "skipped": "no canonical/domain"}

    # Update HTML
    new_html = update_html(html, meta)
    if new_html != html:
        index_path.write_text(new_html, encoding="utf-8")

    # Generate llms.txt
    llms_path = page_dir / "llms.txt"
    new_llms = generate_llms_txt(meta, page_dir.name)
    llms_changed = (not llms_path.exists()) or (llms_path.read_text(encoding="utf-8") != new_llms)
    if llms_changed:
        llms_path.write_text(new_llms, encoding="utf-8")

    return {
        "dir": page_dir.name,
        "domain": meta["domain"],
        "html_changed": new_html != html,
        "llms_changed": llms_changed,
    }


def find_site_dir(domain: str) -> Path | None:
    """Find the matching Vercel site directory for a domain."""
    candidate = SITES_DIR / domain
    if candidate.exists():
        return candidate
    return None


def mirror_to_site(page_dir: Path, domain: str) -> dict:
    """Copy updated files to the corresponding Vercel site directory and add vercel.json."""
    site_dir = find_site_dir(domain)
    if site_dir is None:
        return {"domain": domain, "skipped": "no matching site dir"}

    # Copy index.html, llms.txt, robots.txt, sitemap.xml
    files_to_mirror = ["index.html", "llms.txt", "robots.txt", "sitemap.xml"]
    copied = []
    for f in files_to_mirror:
        src = page_dir / f
        dst = site_dir / f
        if src.exists():
            if (not dst.exists()) or src.read_bytes() != dst.read_bytes():
                shutil.copy2(src, dst)
                copied.append(f)

    # Write vercel.json
    vercel_path = site_dir / "vercel.json"
    new_vercel = json.dumps(VERCEL_HEADERS, indent=2)
    if (not vercel_path.exists()) or vercel_path.read_text(encoding="utf-8") != new_vercel:
        vercel_path.write_text(new_vercel, encoding="utf-8")
        copied.append("vercel.json")

    return {"domain": domain, "site_dir": site_dir.name, "copied": copied}


def main():
    print("=== STEG 1: Applicera fixar på source-sidor i dahlquist-domain-pages ===\n")
    page_results = []
    for child in sorted(PAGES_DIR.iterdir()):
        if not child.is_dir() or child.name in SKIP_DIRS:
            continue
        r = fix_page(child)
        page_results.append(r)
        if "skipped" in r:
            print(f"  ~ {r['dir']:35}  skipped: {r['skipped']}")
        else:
            changes = []
            if r["html_changed"]:
                changes.append("html")
            if r["llms_changed"]:
                changes.append("llms")
            tag = ", ".join(changes) if changes else "no-op"
            print(f"  ✓ {r['dir']:35}  ({r['domain']:30}) {tag}")

    print(f"\n=== STEG 2: Mirror till vercel-sites + vercel.json ===\n")
    mirror_results = []
    for r in page_results:
        if "skipped" in r or not r.get("domain"):
            continue
        page_dir = PAGES_DIR / r["dir"]
        m = mirror_to_site(page_dir, r["domain"])
        mirror_results.append(m)
        if "skipped" in m:
            print(f"  ~ {m['domain']:30}  skipped: {m['skipped']}")
        else:
            print(f"  ✓ {m['domain']:30}  copied: {m['copied']}")

    # Summary
    print("\n=== Sammanfattning ===")
    print(f"  Sidor processade: {len([r for r in page_results if 'skipped' not in r])}")
    print(f"  HTML uppdaterad: {len([r for r in page_results if r.get('html_changed')])}")
    print(f"  llms.txt uppdaterad: {len([r for r in page_results if r.get('llms_changed')])}")
    print(f"  Mirrored till Vercel-site: {len([m for m in mirror_results if 'skipped' not in m])}")


if __name__ == "__main__":
    main()
