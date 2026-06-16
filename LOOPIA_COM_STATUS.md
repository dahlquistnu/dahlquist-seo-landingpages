# Loopia .com NS-låsning - status
Senast kontrollerad: 2026-06-16 07:00 UTC

## Mail-svar från Loopia/Ascio

| Datum | Avsändare | Ärende-ID | Sammanfattning |
|-------|-----------|-----------|----------------|
| 2026-05-08 16:24 UTC | support@loopia.se | #146646 | Automatisk bekräftelse: ärendet mottaget och tilldelat ID 146646. |
| 2026-05-09 09:49 UTC | Jacob S, support@loopia.se | #146646 | **Mänskligt svar:** Jacob S (Customer Success Advisor) frågar om Niklas vill behålla Loopias namnservrar. Han ser att NS-ändringen inte propagerar men att domänerna "ligger mot oss (Loopia) idag". Rådet är att **spara om konfigurationen** för varje domän i Loopias kundzon och sedan vänta 48 timmar. Om det fortfarande inte propagerar efter 48h, återkommer Niklas. |

**Inget nytt svar från Loopia/Ascio sedan 2026-05-09. Ärendet har nu pågått i >38 dagar utan lösning.**

**Action items för Niklas:**
1. **Eskalera ärende #146646** — Loopias råd att "spara om" löste inte problemet. Kräv manuell Ascio→Verisign EPP-åtgärd. Om Loopia inte agerar, kontakta Ascio direkt eller initiera en EPP-flytt till en annan registrar.
2. **Ny Vercel-varning 2026-06-15** bekräftar att alla 5 .com-domäner fortfarande är felkonfigurerade — nu 39 dagar efter anmälan.
3. **prntr.dahlquist.se** är nu också flaggad som felkonfigurerad av Vercel (ny sedan föregående körning).

> OBS: Niklas är sjuk (auto-svar aktivt). Kontakta fredrik@dahlquist.se eller mattias@dahlquist.se vid akuta ärenden.

## Relaterade notiser

| Datum | Avsändare | Innehåll |
|-------|-----------|----------|
| 2026-05-13 02:39 UTC | notifications@vercel.com | **Vercel-varning:** "5 domains need configuration on team 'Dahlquist Vercel'" — alla 5 .com-domäner flaggas som felkonfigurerade. |
| 2026-05-30 05:17 UTC | notifications@vercel.com | **Vercel-varning:** "5 domains need configuration on team 'Dahlquist Vercel'" — alla 5 domäner fortfarande felkonfigurerade, >21 dagar efter anmälan. |
| 2026-06-15 20:15 UTC | notifications@vercel.com | **NY Vercel-varning:** "6 domains need configuration on team 'Dahlquist Vercel'" — alla 5 .com-domäner fortfarande felkonfigurerade (39 dagar). Nu även prntr.dahlquist.se flaggad som felkonfigurerad (ny). |

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

## Förändring sedan förra körningen (2026-05-30)

**NY VERCEL-VARNING + ESKALERING KRÄVS** — Vercel skickade 2026-06-15 20:15 UTC en ny automatisk varning. Nu rapporteras **6** felkonfigurerade domäner (upp från 5): de 5 låsta .com-domänerna är fortfarande olösta, och prntr.dahlquist.se är nu också flaggad. Ingen ny kontakt från Loopia/Ascio sedan 2026-05-09 (38 dagar sedan). DNS oförändrat låst (alla 5 → 212.123.41.108, HTTP 403). Ärendet är nu >38 dagar gammalt utan lösning.

**Rekommenderad åtgärd:** Omedelbar eskalering — kontakta Ascio direkt eller byt registrar. Loopia har inte levererat en lösning på >38 dagar.
