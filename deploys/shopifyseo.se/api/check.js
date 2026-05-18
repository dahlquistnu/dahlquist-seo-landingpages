/**
 * Shopify SEO Checker — Vercel Function
 * Fetches a Shopify (or any) URL and runs 15 SEO checks.
 *
 * GET /api/check?url=https://example.com/
 *
 * Returns: { url, score, checks: [{id, name, status, value, details}] }
 */

const TIMEOUT_MS = 8000;
const USER_AGENT = "Mozilla/5.0 (compatible; ShopifySEOChecker/1.0; +https://shopifyseo.se/)";

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Cache-Control", "public, max-age=300, s-maxage=900, stale-while-revalidate=3600");

  let target;
  try {
    target = new URL(req.query.url || "");
    if (!/^https?:$/.test(target.protocol)) throw new Error("Only http(s) URLs are accepted");
  } catch {
    return res.status(400).json({ error: "Invalid URL. Provide ?url=https://your-shop.com/" });
  }

  const origin = `${target.protocol}//${target.host}`;
  const checks = [];

  // Fetch page HTML
  let html = "";
  let status = 0;
  let headers = {};
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
    const r = await fetch(target.href, {
      headers: { "User-Agent": USER_AGENT },
      signal: ctrl.signal,
      redirect: "follow",
    });
    clearTimeout(t);
    status = r.status;
    headers = Object.fromEntries(r.headers);
    html = await r.text();
  } catch (e) {
    return res.status(502).json({ error: `Could not fetch URL: ${e.message}` });
  }

  if (status >= 400) {
    return res.status(200).json({
      url: target.href,
      score: 0,
      summary: `Page returned HTTP ${status}. Cannot run SEO checks on a non-200 page.`,
      checks: [{ id: "http-status", name: "HTTP Status", status: "fail", value: String(status), details: "Page must return 200 for SEO checks." }],
    });
  }

  const M = (re, def = null) => { const m = html.match(re); return m ? m[1] : def; };
  const ALL = (re) => { const out = []; let m; const r2 = new RegExp(re.source, re.flags.includes("g") ? re.flags : re.flags + "g"); while ((m = r2.exec(html)) !== null) out.push(m); return out; };

  // 1. HTTPS
  checks.push({
    id: "https",
    name: "HTTPS",
    status: target.protocol === "https:" ? "pass" : "fail",
    value: target.protocol,
    details: target.protocol === "https:" ? "Page served over HTTPS." : "Page uses HTTP — Google requires HTTPS for indexation and treats HTTP as a soft demote signal.",
  });

  // 2. Title
  const title = M(/<title[^>]*>([^<]*)<\/title>/i, "");
  const titleLen = title.trim().length;
  checks.push({
    id: "title",
    name: "Title tag",
    status: !title ? "fail" : titleLen < 30 || titleLen > 65 ? "warn" : "pass",
    value: title ? `${titleLen} chars` : "missing",
    details: !title ? "No <title> found." : titleLen < 30 ? "Title is short. Google typically displays 50–60 chars." : titleLen > 65 ? "Title may be truncated in SERPs (target ≤60 chars for desktop, ≤78 for mobile)." : `"${title}"`,
  });

  // 3. Meta description
  const desc = M(/<meta\s+[^>]*name=["']description["'][^>]*content=["']([^"']+)["'][^>]*>/i, "")
    || M(/<meta\s+[^>]*content=["']([^"']+)["'][^>]*name=["']description["'][^>]*>/i, "");
  const descLen = desc.trim().length;
  checks.push({
    id: "description",
    name: "Meta description",
    status: !desc ? "fail" : descLen < 100 || descLen > 165 ? "warn" : "pass",
    value: desc ? `${descLen} chars` : "missing",
    details: !desc ? "No meta description found. Google generates a snippet from page text — write your own for control." : descLen < 100 ? "Description is short. Target 120–155 chars to use the available SERP space." : descLen > 165 ? "Description likely truncated in SERPs. Target 120–160 chars." : "",
  });

  // 4. Canonical
  const canonical = M(/<link\s+[^>]*rel=["']canonical["'][^>]*href=["']([^"']+)["'][^>]*>/i, "")
    || M(/<link\s+[^>]*href=["']([^"']+)["'][^>]*rel=["']canonical["'][^>]*>/i, "");
  const canonicalSelf = canonical && (canonical === target.href || canonical === target.href.replace(/\/$/, "") || new URL(canonical, target.href).href === target.href);
  checks.push({
    id: "canonical",
    name: "Canonical tag",
    status: !canonical ? "fail" : canonicalSelf ? "pass" : "warn",
    value: canonical || "missing",
    details: !canonical ? "No canonical link found. Add <link rel='canonical' href='...'> to consolidate duplicate-URL signals." : canonicalSelf ? "Self-referencing canonical (correct)." : `Canonical points to ${canonical} — verify this is intentional. Cross-canonicals can deindex pages.`,
  });

  // 5. H1 count
  const h1s = ALL(/<h1\b[^>]*>([\s\S]*?)<\/h1>/i);
  checks.push({
    id: "h1",
    name: "H1 heading",
    status: h1s.length === 1 ? "pass" : h1s.length === 0 ? "fail" : "warn",
    value: `${h1s.length} found`,
    details: h1s.length === 0 ? "No H1 on the page. Add one descriptive H1 per page." : h1s.length > 1 ? `${h1s.length} H1 tags found. Best practice is exactly one H1.` : "Exactly one H1 (correct).",
  });

  // 6. Open Graph
  const og = {
    title: M(/<meta\s+[^>]*property=["']og:title["'][^>]*content=["']([^"']+)["']/i, ""),
    description: M(/<meta\s+[^>]*property=["']og:description["'][^>]*content=["']([^"']+)["']/i, ""),
    image: M(/<meta\s+[^>]*property=["']og:image["'][^>]*content=["']([^"']+)["']/i, ""),
    type: M(/<meta\s+[^>]*property=["']og:type["'][^>]*content=["']([^"']+)["']/i, ""),
  };
  const ogMissing = Object.entries(og).filter(([_, v]) => !v).map(([k]) => k);
  checks.push({
    id: "og",
    name: "Open Graph tags",
    status: ogMissing.length === 0 ? "pass" : ogMissing.length <= 2 ? "warn" : "fail",
    value: ogMissing.length === 0 ? "complete" : `missing: ${ogMissing.join(", ")}`,
    details: ogMissing.length === 0 ? "All key OG tags present (title, description, image, type)." : `Add og:${ogMissing.join(", og:")} to control how Facebook/LinkedIn/Slack render link previews.`,
  });

  // 7. Twitter Card
  const tw = M(/<meta\s+[^>]*name=["']twitter:card["'][^>]*content=["']([^"']+)["']/i, "");
  checks.push({
    id: "twitter",
    name: "Twitter Card",
    status: tw ? "pass" : "warn",
    value: tw || "missing",
    details: tw ? `twitter:card="${tw}"` : "Add twitter:card='summary_large_image' for richer X/Twitter previews.",
  });

  // 8. Viewport
  const viewport = M(/<meta\s+[^>]*name=["']viewport["'][^>]*content=["']([^"']+)["']/i, "");
  checks.push({
    id: "viewport",
    name: "Viewport meta",
    status: viewport ? "pass" : "fail",
    value: viewport ? "present" : "missing",
    details: viewport ? `"${viewport}"` : "Mobile viewport missing. Google uses mobile-first indexing — add <meta name='viewport' content='width=device-width, initial-scale=1'>.",
  });

  // 9. HTML lang
  const lang = M(/<html\s+[^>]*lang=["']([^"']+)["']/i, "")
    || M(/<html\s+[^>]*lang=([a-z-]+)/i, "");
  checks.push({
    id: "lang",
    name: "HTML lang",
    status: lang ? "pass" : "warn",
    value: lang || "missing",
    details: lang ? `<html lang="${lang}">` : "Add lang attribute to <html> tag (e.g. lang='sv' for Swedish) for screen readers and Google language detection.",
  });

  // 10. JSON-LD schema
  const schemaBlocks = ALL(/<script\s+[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/i);
  const schemaTypes = [];
  let invalidSchema = 0;
  for (const m of schemaBlocks) {
    try {
      const data = JSON.parse(m[1].trim());
      const collect = (d) => {
        if (Array.isArray(d)) d.forEach(collect);
        else if (d && typeof d === "object") {
          if (d["@type"]) schemaTypes.push(Array.isArray(d["@type"]) ? d["@type"].join("+") : d["@type"]);
          for (const k of ["mainEntity", "itemListElement", "review", "publisher", "author", "@graph"]) if (d[k]) collect(d[k]);
        }
      };
      collect(data);
    } catch { invalidSchema++; }
  }
  const uniqTypes = [...new Set(schemaTypes)];
  checks.push({
    id: "schema-presence",
    name: "JSON-LD schema",
    status: schemaBlocks.length === 0 ? "fail" : invalidSchema > 0 ? "warn" : "pass",
    value: `${schemaBlocks.length} block${schemaBlocks.length === 1 ? "" : "s"}`,
    details: schemaBlocks.length === 0 ? "No JSON-LD found. Add Product, Organization, BreadcrumbList schemas for rich results." : invalidSchema > 0 ? `${invalidSchema} schema block(s) failed to parse — check JSON syntax.` : `Types found: ${uniqTypes.join(", ")}`,
  });

  // 11. Product schema (Shopify-specific)
  const hasProduct = uniqTypes.some((t) => /Product/i.test(t));
  const hasOrg = uniqTypes.some((t) => /Organization/i.test(t));
  const hasBreadcrumb = uniqTypes.some((t) => /BreadcrumbList/i.test(t));
  checks.push({
    id: "schema-coverage",
    name: "Schema coverage",
    status: hasOrg && (hasProduct || hasBreadcrumb) ? "pass" : (hasOrg || hasProduct || hasBreadcrumb) ? "warn" : "fail",
    value: [hasOrg && "Organization", hasProduct && "Product", hasBreadcrumb && "BreadcrumbList"].filter(Boolean).join(" + ") || "none",
    details: !hasOrg && !hasProduct ? "Missing the core schemas for a Shopify store. Add Organization (site-wide) and Product (per product page) at minimum." : "",
  });

  // 12. Image alt coverage
  const imgs = ALL(/<img\s+([^>]+)>/i);
  const imgsWithAlt = imgs.filter((m) => /\salt=/.test(m[1]));
  const imgCovPct = imgs.length ? Math.round((imgsWithAlt.length / imgs.length) * 100) : 100;
  checks.push({
    id: "image-alt",
    name: "Image alt text",
    status: imgs.length === 0 ? "pass" : imgCovPct >= 95 ? "pass" : imgCovPct >= 75 ? "warn" : "fail",
    value: `${imgsWithAlt.length}/${imgs.length} (${imgCovPct}%)`,
    details: imgs.length === 0 ? "No images detected on this page." : imgCovPct < 100 ? `${imgs.length - imgsWithAlt.length} image(s) lack alt attribute. Required for accessibility AND image search.` : "All images have alt attributes.",
  });

  // 13. Hreflang
  const hreflangs = ALL(/<link\s+[^>]*hreflang=["']([^"']+)["']/i);
  const hreflangCount = hreflangs.length;
  checks.push({
    id: "hreflang",
    name: "Hreflang tags",
    status: hreflangCount === 0 ? "warn" : "pass",
    value: hreflangCount === 0 ? "none" : `${hreflangCount} tag${hreflangCount === 1 ? "" : "s"}`,
    details: hreflangCount === 0 ? "No hreflang tags. Add them if you serve multiple languages/regions (sv, en, x-default for Swedish stores expanding internationally)." : `Found: ${hreflangs.map((m) => m[1]).join(", ")}`,
  });

  // 14. Robots.txt
  let robotsAllowsGooglebot = null;
  try {
    const r = await fetch(`${origin}/robots.txt`, { headers: { "User-Agent": USER_AGENT }, signal: AbortSignal.timeout(4000) });
    if (r.ok) {
      const txt = await r.text();
      robotsAllowsGooglebot = !/Disallow:\s*\/\s*$/m.test(txt.split(/User-agent:\s*\*/i).pop() || "");
    }
  } catch {}
  checks.push({
    id: "robots",
    name: "robots.txt",
    status: robotsAllowsGooglebot === null ? "warn" : robotsAllowsGooglebot ? "pass" : "fail",
    value: robotsAllowsGooglebot === null ? "not found" : robotsAllowsGooglebot ? "allows crawlers" : "blocks crawlers",
    details: robotsAllowsGooglebot === null ? `No robots.txt at ${origin}/robots.txt. Shopify generates one by default — check your store.` : robotsAllowsGooglebot ? "" : "Your robots.txt blocks crawlers from the site root. Fix immediately or you won't be indexed.",
  });

  // 15. Sitemap
  let sitemapFound = false;
  let sitemapIncludesUrl = false;
  try {
    const r = await fetch(`${origin}/sitemap.xml`, { headers: { "User-Agent": USER_AGENT }, signal: AbortSignal.timeout(4000) });
    if (r.ok) {
      sitemapFound = true;
      const txt = await r.text();
      sitemapIncludesUrl = txt.includes(target.href) || txt.includes(target.href.replace(/\/$/, ""));
    }
  } catch {}
  checks.push({
    id: "sitemap",
    name: "sitemap.xml",
    status: !sitemapFound ? "fail" : sitemapIncludesUrl ? "pass" : "warn",
    value: !sitemapFound ? "not found" : sitemapIncludesUrl ? "URL included" : "URL not in sitemap",
    details: !sitemapFound ? `No sitemap at ${origin}/sitemap.xml. Shopify auto-generates one — check your store.` : sitemapIncludesUrl ? "" : "Sitemap exists but the URL you tested isn't in it. Submit the sitemap in Google Search Console.",
  });

  // Score
  const weights = { pass: 1, warn: 0.5, fail: 0 };
  const score = Math.round((checks.reduce((s, c) => s + weights[c.status], 0) / checks.length) * 100);

  const summary = score >= 85 ? "Strong SEO foundation — focus on content and links." : score >= 65 ? "Solid baseline with notable gaps. Address the failed checks below first." : "Significant SEO issues to fix before this page can compete in search.";

  return res.status(200).json({
    url: target.href,
    score,
    summary,
    checked_at: new Date().toISOString(),
    checks,
  });
}
