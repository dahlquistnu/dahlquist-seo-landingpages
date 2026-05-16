# Loopia .com NS-låsning - status
Senast kontrollerad: 2026-05-16 08:00 UTC

## Mail-svar från Loopia/Ascio

| Datum | Avsändare | Ärende-ID | Sammanfattning |
|-------|-----------|-----------|----------------|
| 2026-05-08 16:24 UTC | support@loopia.se | #146646 | Automatisk bekräftelse: ärendet mottaget och tilldelat ID 146646. |
| 2026-05-09 09:49 UTC | Jacob S, support@loopia.se | #146646 | **Mänskligt svar:** Jacob S (Customer Success Advisor) frågar om Niklas vill behålla Loopias namnservrar. Han ser att NS-ändringen inte propagerar men att domänerna "ligger mot oss (Loopia) idag". Rådet är att **spara om konfigurationen** för varje domän i Loopias kundzon och sedan vänta 48 timmar. Om det fortfarande inte propagerar efter 48h, återkommer Niklas. |

**Inget nytt svar från Loopia/Ascio sedan 2026-05-09.**

**Action items för Niklas:**
1. **Eskalera ärende #146646** — 48h-fristen (räknat från 2026-05-09) har passerats. Svara på ärendet och kräv manuell Ascio→Verisign EPP-åtgärd. Loopias råd att "spara om" har inte löst problemet.
2. **Hänvisa till Vercel-notisen** (2026-05-13): Vercel bekräftar att alla 5 domäner fortfarande är felkonfigurerade (DNS pekar inte på Vercel).

> OBS: Niklas är sjuk (auto-svar aktivt). Kontakta fredrik@dahlquist.se eller mattias@dahlquist.se vid akuta ärenden.

## Relaterade notiser

| Datum | Avsändare | Innehåll |
|-------|-----------|----------|
| 2026-05-13 02:39 UTC | notifications@vercel.com | **Vercel-varning:** "5 domains need configuration on team 'Dahlquist Vercel'" — alla 5 domäner (aiutveckling.com, aiutvecklare.com, wunderwerk-b2b.com, orionheadless.com, b2b-today.com) flaggas som felkonfigurerade i Vercel-dashboarden. Bekräftar att DNS-låsningen fortfarande är aktiv. |

## DNS-status per domän

| Domän | NS (via Verisign/TLD) | A-record | HTTP-status | Kommentar |
|-------|----------------------|----------|-------------|----------|
| aiutvecklare.com | Ej verifierbar från miljön* | 212.123.41.108 | 403 | Fortfarande låst — INTE 76.76.21.21 (Vercel) |
| aiutveckling.com | Ej verifierbar från miljön* | 212.123.41.108 | 403 | Fortfarande låst |
| b2b-today.com | Ej verifierbar från miljön* | 212.123.41.108 | 403 | Fortfarande låst |
| orionheadless.com | Ej verifierbar från miljön* | 212.123.41.108 | 403 | Fortfarande låst |
| wunderwerk-b2b.com | Ej verifierbar från miljön* | 212.123.41.108 | 403 | Fortfarande låst |

*NS-queries via UDP/TCP port 53 är blockerade i körmiljön. A-record (via Python socket) bekräftar att domänerna fortfarande pekar på registrant-verification.com (212.123.41.108) — INTE på Vercel (76.76.21.21).

**Förväntad status när löst:** A-record = 76.76.21.21, HTTP = 200

## Förändring sedan förra körningen (2026-05-10)

**NY INFO** — Vercel skickade 2026-05-13 en automatisk varning om att alla 5 domäner är felkonfigurerade i Vercel-dashboarden, vilket bekräftar att NS-låsningen fortfarande är aktiv. Inget nytt svar från Loopia/Ascio. DNS-status oförändrat låst (alla 5 → 212.123.41.108, HTTP 403).

**Rekommenderad åtgärd:** 48h-fristen har löpt ut — eskalera ärende #146646 och begär manuell EPP-korrigering från Ascio.
