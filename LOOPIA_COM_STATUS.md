# Loopia .com NS-låsning - status
Senast kontrollerad: 2026-05-09 08:11 UTC

## Mail-svar från Loopia/Ascio

| Datum | Avsändare | Ärende-ID | Sammanfattning |
|-------|-----------|-----------|----------------|
| 2026-05-08 16:24 UTC | support@loopia.se | #146646 | Automatisk bekräftelse: ärendet mottaget och tilldelat ID 146646. Loopia anger att de har högre belastning än vanligt och att svar kan dröja. Inget mänskligt svar ännu. |

**Action items för Niklas:** Invänta mänskligt svar från Loopia på ärende #146646. Om inget svar inom 2–3 arbetsdagar, följ upp via telefon 046-21 12 82 22 eller svara på ärendetråden.

## DNS-status per domän

| Domän | NS (via Verisign/TLD) | A-record (Google 8.8.8.8) | HTTP-status | Kommentar |
|-------|----------------------|---------------------------|-------------|----------|
| aiutvecklare.com | Ej verifierbar från miljön* | 212.123.41.108 | 403 | Fortfarande låst — A-record är INTE 76.76.21.21 (Vercel) |
| aiutveckling.com | Ej verifierbar från miljön* | 212.123.41.108 | 403 | Fortfarande låst |
| b2b-today.com | Ej verifierbar från miljön* | 212.123.41.108 | 403 | Fortfarande låst |
| orionheadless.com | Ej verifierbar från miljön* | 212.123.41.108 | 403 | Fortfarande låst |
| wunderwerk-b2b.com | Ej verifierbar från miljön* | 212.123.41.108 | 403 | Fortfarande låst |

*NS-poster via UDP/TCP port 53 och DNS-over-HTTPS är blockerade i körmiljön. A-record och HTTP-status bekräftar ändå att domänerna fortfarande pekar på registrant-verification.com (212.123.41.108) — INTE på Vercel (76.76.21.21).

**Förväntad status när löst:** A-record = 76.76.21.21, HTTP = 200

## Förändring sedan förra körningen

**NYTT SVAR** — Loopia bekräftade ärende #146646 (auto-svar 2026-05-08 16:24 UTC). Inget mänskligt svar ännu. DNS-status oförändrat låst.
