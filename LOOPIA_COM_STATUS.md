# Loopia .com NS-låsning - status
Senast kontrollerad: 2026-05-10 08:15 UTC

## Mail-svar från Loopia/Ascio

| Datum | Avsändare | Ärende-ID | Sammanfattning |
|-------|-----------|-----------|----------------|
| 2026-05-08 16:24 UTC | support@loopia.se | #146646 | Automatisk bekräftelse: ärendet mottaget och tilldelat ID 146646. |
| 2026-05-09 09:49 UTC | Jacob S, support@loopia.se | #146646 | **Mänskligt svar:** Jacob S (Customer Success Advisor) frågar om Niklas vill behålla Loopias namnservrar. Han ser att NS-ändringen inte propagerar men att domänerna "ligger mot oss (Loopia) idag". Rådet är att **spara om konfigurationen** för varje domän i Loopias kundzon och sedan vänta 48 timmar. Om det fortfarande inte propagerar efter 48h, återkommer Niklas. |

**Action items för Niklas:**
1. **Logga in i Loopias kundzon** och spara om NS-inställningarna (ns1.loopia.se / ns2.loopia.se) för samtliga 5 domäner på nytt — använd "Tvinga ändring" om alternativet finns.
2. **Vänta 48 timmar** efter ändringen.
3. **Om NS fortfarande inte propagerar efter 48h** — svara på ärende #146646 och eskalera: Verisign visar fortfarande NS1/NS2.REGISTRANT-VERIFICATION.COM trots Ascios interna data säger ns1/ns2.loopia.se. Det är ett Ascio→Verisign EPP-problem som kräver manuell åtgärd från Loopia/Ascio.

> OBS: Niklas är sjuk (auto-svar aktivt). Kontakta fredrik@dahlquist.se eller mattias@dahlquist.se vid akuta ärenden.

## DNS-status per domän

| Domän | NS (via Verisign/TLD) | A-record | HTTP-status | Kommentar |
|-------|----------------------|----------|-------------|----------|
| aiutvecklare.com | Ej verifierbar från miljön* | 212.123.41.108 | 403 | Fortfarande låst — INTE 76.76.21.21 (Vercel) |
| aiutveckling.com | Ej verifierbar från miljön* | 212.123.41.108 | 403 | Fortfarande låst |
| b2b-today.com | Ej verifierbar från miljön* | 212.123.41.108 | 403 | Fortfarande låst |
| orionheadless.com | Ej verifierbar från miljön* | 212.123.41.108 | 403 | Fortfarande låst |
| wunderwerk-b2b.com | Ej verifierbar från miljön* | 212.123.41.108 | 403 | Fortfarande låst |

*NS-queries via UDP/TCP port 53 och DNS-over-HTTPS är blockerade i körmiljön. A-record (via Python socket) och HTTP-status bekräftar att domänerna fortfarande pekar på registrant-verification.com (212.123.41.108) — INTE på Vercel (76.76.21.21).

**Förväntad status när löst:** A-record = 76.76.21.21, HTTP = 200

## Förändring sedan förra körningen

**NYTT SVAR** — Jacob S på Loopia svarade 2026-05-09 09:49 UTC med råd att spara om NS-konfigurationen i Loopias kundzon och invänta 48h. DNS-status fortfarande oförändrat låst (alla 5 domäner pekar på 212.123.41.108, HTTP 403).
