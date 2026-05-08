#!/usr/bin/env python3
"""
Deploy new Vercel sites, add custom domains, and set CNAME in Loopia.
"""

import subprocess
import os
import shutil
import time
import xmlrpc.client
import sys

SITES_DIR = "/Users/niklasdahlquist/GIT/dahlquist-seo-landingpages/deploys"
PAGES_DIR = "/Users/niklasdahlquist/GIT/dahlquist-seo-landingpages/pages"

LOOPIA_USER = "dahlquistclaude@loopiaapi"
LOOPIA_PASS = "Dalapass123!"
LOOPIA_API = "https://api.loopia.se/RPCSERV"

# New pages to deploy: (source_dir, target_domain, project_name)
NEW_PAGES = [
    ("adobecommercealt", "adobe-commerce.se",   "adobe-commerce-se"),
    ("aiengineer",       "aiengineer.se",        "aiengineer-se"),
    ("aiutvecklare",     "aiutvecklare.com",     "aiutvecklare-com"),
    ("aiutveckling",     "aiutveckling.com",     "aiutveckling-com"),
    ("magento360",       "magento360.se",        "magento360-se"),
    ("magentopwa",       "magentopwa.se",        "magentopwa-se"),
    ("shopify360",       "shopify360.se",        "shopify360-se"),
    ("shopifybyra",      "shopifybyrå.se",       "shopifybyra-se"),
    ("shopifybyraer",    "shopifybyråer.se",     "shopifybyraer-se"),
    ("shopifysverige",   "shopifysverige.com",   "shopifysverige-com"),
]

# Existing projects that need custom domains assigned + CNAME verified
EXISTING_DOMAINS = [
    ("x-konsult.se",        "x-konsult.se"),
    ("wunderwerk-b2b.com",  "wunderwerk-b2b.com"),
    ("starta-ehandel.se",   "starta-ehandel.se"),
    ("shopifyseo.se",       "shopifyseo.se"),
    ("shopifypro.se",       "shopifypro.se"),
    ("shopifykonsulter.se", "shopifykonsulter.se"),
    ("shopifyexperter.se",  "shopifyexperter.se"),
    ("shopifyexperts.se",   "shopifyexperts.se"),
    ("shopifyb2b.se",       "shopifyb2b.se"),
    ("shopify-sverige.se",  "shopify-sverige.se"),
    ("punchout.nu",         "punchout.nu"),
    ("pimsystem.se",        "pimsystem.se"),
    ("orionheadless.com",   "orionheadless.com"),
    ("magentoexperten.se",  "magentoexperten.se"),
    ("magentocommerce.se",  "magentocommerce.se"),
    ("magento-webshop.se",  "magento-webshop.se"),
    ("magento-sverige.se",  "magento-sverige.se"),
    ("magento-pwa.se",      "magento-pwa.se"),
    ("magento-konsulter.se","magento-konsulter.se"),
    ("magento-ehandel.se",  "magento-ehandel.se"),
    ("klaviyo.se",          "klaviyo.se"),
    ("inline-ehandel.se",   "inline-ehandel.se"),
    ("ehandelkonsult.se",   "ehandelkonsult.se"),
    ("ehandelinstitutet.se","ehandelinstitutet.se"),
    ("ecomeagency.se",      "ecomeagency.se"),
    ("e-handelsystem.se",   "e-handelsystem.se"),
    ("digitalhandel.nu",    "digitalhandel.nu"),
    ("centrumhandel.se",    "centrumhandel.se"),
    ("b2behandel.se",       "b2behandel.se"),
    ("b2b-today.com",       "b2b-today.com"),
    ("ai-utvecklare.se",    "ai-utvecklare.se"),
    ("adobecommerce.se",    "adobecommerce.se"),
]


def check_cname_exists(client, domain):
    """Check if CNAME already exists for root of this domain."""
    try:
        records = client.getZoneRecords(LOOPIA_USER, LOOPIA_PASS, domain, "@")
        for r in records:
            if isinstance(r, dict) and r.get("type") == "CNAME":
                return True
        return False
    except Exception as e:
        print(f"    Loopia check error for {domain}: {e}")
        return False


def loopia_add_cname(client, domain):
    """Add CNAME → cname.vercel-dns.com at root of domain."""
    record = {
        "type": "CNAME",
        "ttl": 300,
        "priority": 0,
        "rdata": "cname.vercel-dns.com.",
    }
    resp = client.addZoneRecord(LOOPIA_USER, LOOPIA_PASS, domain, "@", record)
    return resp


def assign_domain_to_project(project_dir, domain, prod_url):
    """Assign custom domain to Vercel project via alias."""
    result = subprocess.run(
        ["vercel", "alias", "set", prod_url, domain],
        capture_output=True, text=True,
        cwd=project_dir
    )
    if result.returncode == 0:
        print(f"    ✓ Alias set: {domain} → {prod_url}")
        return True
    else:
        out = result.stdout + result.stderr
        if "already assigned" in out.lower() or "already exists" in out.lower():
            print(f"    ~ Alias already set for {domain}")
            return True
        # SSL cert error is expected before DNS propagates - alias may still be set
        if "certificate" in out.lower() or "generating" in out.lower():
            print(f"    ~ Alias set (cert pending DNS propagation): {domain}")
            return True
        print(f"    ✗ Alias failed for {domain}: {out[:200]}")
        return False


def get_prod_url(project_dir):
    """Get the .vercel.app production URL for this project."""
    proj_json = os.path.join(project_dir, ".vercel", "project.json")
    if os.path.exists(proj_json):
        import json
        with open(proj_json) as f:
            data = json.load(f)
        proj_name = data.get("projectName", "")
        if proj_name:
            return f"https://{proj_name}.vercel.app"
    return None


def deploy_new_site(source_dir, domain, project_name):
    """Copy HTML to sites dir and deploy to Vercel."""
    site_dir = os.path.join(SITES_DIR, domain)
    os.makedirs(site_dir, exist_ok=True)

    src = os.path.join(PAGES_DIR, source_dir, "index.html")
    dst = os.path.join(site_dir, "index.html")
    shutil.copy2(src, dst)
    print(f"    Copied HTML from {source_dir}/")

    result = subprocess.run(
        ["vercel", "deploy", "--yes", "--prod", "--name", project_name],
        capture_output=True, text=True,
        cwd=site_dir
    )
    if result.returncode == 0:
        url = result.stdout.strip().split("\n")[-1].strip()
        print(f"    ✓ Deployed: {url}")
        return site_dir, True
    else:
        print(f"    ✗ Deploy failed: {result.stderr[:300]}")
        return site_dir, False


loopia_call_count = 0
loopia_client = xmlrpc.client.ServerProxy(LOOPIA_API, allow_none=True)


def handle_loopia(domain):
    """Add CNAME in Loopia if not already present, with rate limit handling."""
    global loopia_call_count
    loopia_call_count += 1
    if loopia_call_count % 18 == 0:
        print("    ⏳ Loopia rate limit pause (65s)...")
        time.sleep(65)

    if check_cname_exists(loopia_client, domain):
        print(f"    ~ CNAME already in Loopia")
    else:
        loopia_call_count += 1
        try:
            resp = loopia_add_cname(loopia_client, domain)
            print(f"    ✓ CNAME added in Loopia: {resp}")
        except Exception as e:
            print(f"    ✗ Loopia CNAME error: {e}")


def main():
    # Phase 1: Deploy new sites
    print("\n=== PHASE 1: Deploy new sites ===")
    for source_dir, domain, project_name in NEW_PAGES:
        print(f"\n→ {domain} (from {source_dir}/)")
        src_path = os.path.join(PAGES_DIR, source_dir, "index.html")
        if not os.path.exists(src_path):
            print(f"    ✗ Source not found: {src_path}")
            continue

        site_dir, ok = deploy_new_site(source_dir, domain, project_name)
        if ok:
            # Add domain to account
            subprocess.run(
                ["vercel", "domains", "add", domain, "--yes"],
                capture_output=True, text=True,
                cwd=site_dir
            )

            # Assign alias
            prod_url = get_prod_url(site_dir)
            if not prod_url:
                prod_url = f"https://{project_name}.vercel.app"
            assign_domain_to_project(site_dir, domain, prod_url)

            # Loopia CNAME
            handle_loopia(domain)

        time.sleep(1)

    # Phase 2: Assign domains + add CNAME for existing projects
    print("\n=== PHASE 2: Assign domains to existing projects ===")
    for dir_name, domain in EXISTING_DOMAINS:
        print(f"\n→ {domain}")
        project_dir = os.path.join(SITES_DIR, dir_name)
        if not os.path.exists(project_dir):
            print(f"    ✗ Not found: {project_dir}")
            continue

        prod_url = get_prod_url(project_dir)
        if not prod_url:
            print(f"    ✗ No .vercel/project.json found")
            continue

        assign_domain_to_project(project_dir, domain, prod_url)
        handle_loopia(domain)
        time.sleep(0.5)

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
