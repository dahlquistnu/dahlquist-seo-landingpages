# Dahlquist SEO Landingpages

47 SEO-optimerade domänsidor för Dahlquist E-handelskonsulter AB. Källkod, deploy-state och drift-scripts samlat på ett ställe.

## Layout

```
.
├── pages/              Källkod för varje domänsida (47 directories)
│   └── <slug>/
│       ├── index.html
│       ├── llms.txt
│       ├── robots.txt
│       └── sitemap.xml
├── deploys/            Vercel-deploy-state (42 directories)
│   └── <domain>/
│       ├── .vercel/project.json
│       ├── index.html        (kopia från pages/)
│       ├── vercel.json       (security headers + cache-control)
│       └── ...
├── scripts/            Drift- och fix-scripts
│   ├── apply_seo_fixes.py    Applicera audit-fixar på alla pages + mirror till deploys
│   ├── deploy_all.py         Deploya nya sites + sätt CNAME via Loopia
│   ├── redeploy_all.py       Redeploy alla 42 sites till Vercel
│   ├── diagnose.py           Loopia DNS-zonstatus per domän
│   ├── fix.py                Fixa NS-delegation + A-records via Loopia API
│   ├── cf_add_custom_domains.py    Cloudflare Pages custom domains (legacy)
│   └── loopia_ns_update.py         Loopia NS → Cloudflare (legacy)
└── cloudflare-worker/  Legacy: Cloudflare Worker som tjänade 9 overflow-domäner
```

## Vanliga kommandon

```bash
# Applicera SEO-fixar på alla sidor + redeploy
python3 scripts/apply_seo_fixes.py
python3 scripts/redeploy_all.py

# Felsöka DNS-zon för domäner i Loopia
python3 scripts/diagnose.py
```

## Status maj 2026

- 17 av 42 sidor live på Vercel sedan tidigare
- 20 sidor fixade via Loopia API (NS-delegation + A-records)
- 5 .com-domäner kräver manuell NS-update i Loopia kundpanel:
  aiutvecklare.com, aiutveckling.com, b2b-today.com, orionheadless.com, wunderwerk-b2b.com
- SEO-audit applicerad på alla 44 källkods-sidor (image schema, theme-color, unik llms.txt)

## Hemligheter

Loopia API-credentials är hårdkodade i `scripts/diagnose.py` och `scripts/fix.py`. Flytta till `.env` när tid finns.
