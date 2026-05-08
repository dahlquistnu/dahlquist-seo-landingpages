#!/usr/bin/env python3
"""
Diagnose Loopia zone status for the broken Vercel sites.
Read-only — does not modify anything.
"""

import xmlrpc.client
import time
import sys

LOOPIA_USER = "dahlquistclaude@loopiaapi"
LOOPIA_PASS = "Dalapass123!"
LOOPIA_API = "https://api.loopia.se/RPCSERV"

BROKEN_NO_DNS = [
    "ai-utvecklare.se", "b2behandel.se", "centrumhandel.se", "digitalhandel.nu",
    "ecomeagency.se", "ehandelinstitutet.se", "inline-ehandel.se", "klaviyo.se",
    "magento-ehandel.se", "magento-pwa.se", "magento-webshop.se", "magentocommerce.se",
    "pimsystem.se", "shopifybyrå.se", "shopifybyråer.se", "shopifyexperts.se",
    "shopifypro.se", "shopifyseo.se", "starta-ehandel.se", "x-konsult.se",
]

PARKED_ON_LOOPIA = [
    "aiutvecklare.com", "aiutveckling.com", "b2b-today.com",
    "orionheadless.com", "wunderwerk-b2b.com",
]

ALL_DOMAINS = BROKEN_NO_DNS + PARKED_ON_LOOPIA

client = xmlrpc.client.ServerProxy(LOOPIA_API, allow_none=True)


def safe_call(func, *args):
    """Wrap an RPC call so we get diagnostic strings, not crashes."""
    try:
        return func(LOOPIA_USER, LOOPIA_PASS, *args)
    except xmlrpc.client.Fault as e:
        return f"FAULT: {e.faultString}"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def diagnose(domain):
    """Return a dict describing what Loopia knows about this domain."""
    info = {"domain": domain}

    # Does the domain exist in our Loopia account?
    dom = safe_call(client.getDomain, domain)
    if isinstance(dom, str):
        info["loopia_domain"] = dom
        info["zone_in_loopia"] = False
        return info

    info["loopia_domain"] = "OK"
    info["loopia_domain_data"] = dom

    # List all subdomains/zones
    subs = safe_call(client.getSubdomains, domain)
    if isinstance(subs, str):
        info["subdomains"] = subs
        info["zone_in_loopia"] = False
        return info

    info["subdomains"] = subs
    info["zone_in_loopia"] = True

    # Records at root (@)
    if "@" in subs:
        recs = safe_call(client.getZoneRecords, domain, "@")
        info["root_records"] = recs

    # Records at www
    if "www" in subs:
        recs = safe_call(client.getZoneRecords, domain, "www")
        info["www_records"] = recs

    return info


def main():
    print(f"Diagnoserar {len(ALL_DOMAINS)} domäner mot Loopia...\n")
    results = []
    call_count = 0
    for d in ALL_DOMAINS:
        # rate limit: ~18 calls per minute is safe
        if call_count and call_count % 16 == 0:
            print(f"  ⏳ paus 65s (rate limit)...", flush=True)
            time.sleep(65)
        call_count += 3  # getDomain + getSubdomains + 1-2 getZoneRecords

        info = diagnose(d)
        results.append(info)

        zone = info.get("zone_in_loopia")
        subs = info.get("subdomains", [])
        root = info.get("root_records", [])
        if zone is False:
            status = f"NO_ZONE  ({info.get('loopia_domain')})"
        elif not root:
            status = f"ZONE_OK  subs={subs}  root=EMPTY"
        else:
            types = [r.get("type") for r in root if isinstance(r, dict)]
            status = f"ZONE_OK  subs={subs}  root={types}"
        print(f"  {d:30}  {status}", flush=True)

    print("\n=== Sammanfattning ===")
    no_zone = [r["domain"] for r in results if not r.get("zone_in_loopia")]
    has_zone = [r for r in results if r.get("zone_in_loopia")]
    needs_record = [r["domain"] for r in has_zone if not r.get("root_records")]
    has_records = [r for r in has_zone if r.get("root_records")]

    print(f"  Saknar zon i Loopia ({len(no_zone)}): {no_zone}")
    print(f"  Zon finns men root saknar records ({len(needs_record)}): {needs_record}")
    print(f"  Har records vid root ({len(has_records)}): {[r['domain'] for r in has_records]}")
    for r in has_records:
        print(f"    {r['domain']} root: {r.get('root_records')}")

    return results


if __name__ == "__main__":
    main()
