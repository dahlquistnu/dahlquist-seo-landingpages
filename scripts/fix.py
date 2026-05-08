#!/usr/bin/env python3
"""
Fix the 25 broken Vercel domains by:
  1. Updating registry-side nameservers to Loopia DNS (where Loopia already has the correct A records).
  2. Adding the missing A record on ai-utvecklare.se.
  3. Trying punycode for the å-domains (shopifybyrå.se, shopifybyråer.se).

Read-once, write-once — idempotent: re-running just re-asserts current state.
"""

import xmlrpc.client
import time
import sys

LOOPIA_USER = "dahlquistclaude@loopiaapi"
LOOPIA_PASS = "Dalapass123!"
LOOPIA_API = "https://api.loopia.se/RPCSERV"
LOOPIA_NS = ["ns1.loopia.se", "ns2.loopia.se"]
VERCEL_IP = "76.76.21.21"

# All 25 originally broken — Loopia diagnose showed 22 + 1 + 2 split:
# 22 have zone with A=Vercel + Loopia NS records, just need registry NS update.
# 1 (ai-utvecklare.se) has zone but no A record at root.
# 2 (shopifybyrå.se, shopifybyråer.se) — Loopia rejects "Domain name not valid" — try punycode.

NEEDS_NS_UPDATE = [
    "b2behandel.se", "centrumhandel.se", "digitalhandel.nu", "ecomeagency.se",
    "ehandelinstitutet.se", "inline-ehandel.se", "klaviyo.se", "magento-ehandel.se",
    "magento-pwa.se", "magento-webshop.se", "magentocommerce.se", "pimsystem.se",
    "shopifyexperts.se", "shopifypro.se", "shopifyseo.se", "starta-ehandel.se",
    "x-konsult.se",
    # .com domains (also missing registry delegation)
    "aiutvecklare.com", "aiutveckling.com", "b2b-today.com",
    "orionheadless.com", "wunderwerk-b2b.com",
]

NEEDS_A_RECORD = [
    "ai-utvecklare.se",  # also needs NS update via registry, but registry is already OK there
]

# å-domains — Loopia API expects ASCII; pass punycode form.
PUNYCODE_DOMAINS = [
    ("shopifybyrå.se",   "xn--shopifybyr-b6a.se"),
    ("shopifybyråer.se", "xn--shopifybyrer-3za.se"),
]

client = xmlrpc.client.ServerProxy(LOOPIA_API, allow_none=True)
call_count = 0


def rate_limit_pause():
    global call_count
    call_count += 1
    if call_count % 14 == 0:
        print(f"  ⏳ rate-limit paus 65s (efter {call_count} anrop)...", flush=True)
        time.sleep(65)


def safe(func, *args, label=""):
    rate_limit_pause()
    try:
        return func(LOOPIA_USER, LOOPIA_PASS, *args)
    except xmlrpc.client.Fault as e:
        return f"FAULT: {e.faultString}"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def update_nameservers(domain):
    """Set registry-side NS delegation to Loopia."""
    return safe(client.updateDNSServers, domain, LOOPIA_NS, label=f"updateNS:{domain}")


def add_a_record(domain, sub="@"):
    """Add an A record at the given subdomain (creates subdomain if missing)."""
    # Make sure subdomain exists
    subs = safe(client.getSubdomains, domain)
    if isinstance(subs, list) and sub not in subs:
        safe(client.addSubdomain, domain, sub)

    record = {
        "type": "A",
        "ttl": 3600,
        "priority": 0,
        "rdata": VERCEL_IP,
    }
    return safe(client.addZoneRecord, domain, sub, record)


def main():
    results = {"ns_ok": [], "ns_fail": [], "a_ok": [], "a_fail": [], "puny_ok": [], "puny_fail": []}

    print(f"\n=== FAS 1: Uppdatera NS-delegation hos registry för {len(NEEDS_NS_UPDATE)} domäner ===\n")
    for d in NEEDS_NS_UPDATE:
        resp = update_nameservers(d)
        ok = resp == "OK"
        marker = "✓" if ok else "✗"
        print(f"  {marker} {d:30}  {resp}")
        (results["ns_ok"] if ok else results["ns_fail"]).append((d, resp))

    print(f"\n=== FAS 2: Lägg A-record på {len(NEEDS_A_RECORD)} domäner ===\n")
    for d in NEEDS_A_RECORD:
        # First update NS to be safe
        ns_resp = update_nameservers(d)
        print(f"    NS-update {d}: {ns_resp}")

        a_resp_root = add_a_record(d, "@")
        print(f"    A @ {d}: {a_resp_root}")
        a_resp_www = add_a_record(d, "www")
        print(f"    A www.{d}: {a_resp_www}")

        ok = a_resp_root == "OK"
        marker = "✓" if ok else "✗"
        print(f"  {marker} {d}")
        (results["a_ok"] if ok else results["a_fail"]).append((d, a_resp_root))

    print(f"\n=== FAS 3: ÅÄÖ-domäner via punycode ===\n")
    for orig, puny in PUNYCODE_DOMAINS:
        # First check zone status under punycode
        sub_resp = safe(client.getSubdomains, puny)
        print(f"  {orig} ({puny}) subdomains: {sub_resp}")

        if isinstance(sub_resp, str) and "FAULT" in sub_resp:
            print(f"  ✗ {orig}: zonen finns inte ens under punycode")
            results["puny_fail"].append((orig, sub_resp))
            continue

        # Update NS
        ns_resp = update_nameservers(puny)
        print(f"    NS-update: {ns_resp}")

        # Add A record root + www if missing
        if "@" not in sub_resp:
            safe(client.addSubdomain, puny, "@")
        a_root = add_a_record(puny, "@")
        if "www" not in sub_resp:
            safe(client.addSubdomain, puny, "www")
        a_www = add_a_record(puny, "www")

        print(f"    A @: {a_root}")
        print(f"    A www: {a_www}")

        ok = ns_resp == "OK"
        marker = "✓" if ok else "✗"
        print(f"  {marker} {orig}")
        (results["puny_ok"] if ok else results["puny_fail"]).append((orig, ns_resp))

    print(f"\n=== Sammanfattning ===")
    print(f"  NS-update ✓ ({len(results['ns_ok'])}): {[d for d,_ in results['ns_ok']]}")
    print(f"  NS-update ✗ ({len(results['ns_fail'])}): {results['ns_fail']}")
    print(f"  A-record ✓ ({len(results['a_ok'])}): {[d for d,_ in results['a_ok']]}")
    print(f"  A-record ✗ ({len(results['a_fail'])}): {results['a_fail']}")
    print(f"  Punycode ✓ ({len(results['puny_ok'])}): {[d for d,_ in results['puny_ok']]}")
    print(f"  Punycode ✗ ({len(results['puny_fail'])}): {results['puny_fail']}")
    print(f"\nKör nu och vänta ~5–60 min för DNS-propagation, sen verifiera HTTP.")


if __name__ == "__main__":
    main()
