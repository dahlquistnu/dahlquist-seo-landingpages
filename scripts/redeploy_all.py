#!/usr/bin/env python3
"""
Redeploy all 39 site dirs that have updated index.html + vercel.json.
Runs sequentially to avoid Vercel CLI rate-limits.
"""

import subprocess
import os
import json
import time
from pathlib import Path

SITES_DIR = Path("/Users/niklasdahlquist/GIT/dahlquist-seo-landingpages/deploys")


def deploy(site_dir: Path) -> dict:
    proj_json = site_dir / ".vercel" / "project.json"
    if not proj_json.exists():
        return {"domain": site_dir.name, "status": "skipped", "reason": "no .vercel/project.json"}

    result = subprocess.run(
        ["vercel", "deploy", "--prod", "--yes"],
        capture_output=True, text=True,
        cwd=str(site_dir),
        timeout=120,
    )
    out = result.stdout + result.stderr
    if result.returncode == 0:
        url = result.stdout.strip().split("\n")[-1].strip()
        return {"domain": site_dir.name, "status": "ok", "url": url}
    return {"domain": site_dir.name, "status": "fail", "error": out[:300]}


def main():
    all_dirs = sorted([d for d in SITES_DIR.iterdir() if d.is_dir()])
    print(f"Deployar {len(all_dirs)} sites...\n")

    ok, fail, skip = [], [], []
    for i, d in enumerate(all_dirs, 1):
        print(f"  [{i:2}/{len(all_dirs)}] {d.name:35}", end="", flush=True)
        r = deploy(d)
        if r["status"] == "ok":
            print(f"  ✓ {r['url']}")
            ok.append(r)
        elif r["status"] == "skipped":
            print(f"  ~ {r['reason']}")
            skip.append(r)
        else:
            print(f"  ✗ {r['error'][:120]}")
            fail.append(r)
        # Small delay to be polite
        time.sleep(1)

    print(f"\n=== Sammanfattning ===")
    print(f"  ✓ OK: {len(ok)}")
    print(f"  ~ Skipped: {len(skip)}")
    print(f"  ✗ Failed: {len(fail)}")
    if fail:
        print("\nFelade:")
        for f in fail:
            print(f"  {f['domain']}: {f['error'][:200]}")


if __name__ == "__main__":
    main()
