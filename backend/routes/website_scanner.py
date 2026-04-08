"""
Adlytics Deep Website Scanner — Professional Marketing Intelligence Engine

Multi-page crawling, structured data extraction (JSON-LD, Schema.org, OG),
competitor detection, and a GPT-4o marketing strategist brain that:
  - Identifies the strongest selling angles
  - Generates ranked ad copy variants per angle
  - Creates a creative brief for video + ad generation
  - Detects brand voice, colors, trust signals, and testimonials
  - Maps customer journey stage recommendations
"""

import os
import re
import json
import asyncio
import httpx
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin, urlparse
from fastapi import APIRouter, HTTPException, Form

router = APIRouter(prefix="/scanner", tags=["website-scanner"])

OPENROUTER_API = "https://openrouter.ai/api/v1/chat/completions"
GPT4O_MODEL = "openai/gpt-4o"

# ─── Helpers ──────────────────────────────────────────────────────────

def get_openrouter_key():
    return os.getenv("OPENROUTER_API_KEY")


def _headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }


# ─── Multi-page crawler ──────────────────────────────────────────────

async def _fetch_page(client: httpx.AsyncClient, url: str) -> Optional[str]:
    """Fetch a single page HTML. Returns None on failure."""
    try:
        resp = await client.get(url, headers=_headers(), follow_redirects=True, timeout=12.0)
        if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", ""):
            return resp.text
    except Exception:
        pass
    return None


def _discover_subpages(html: str, base_url: str) -> List[str]:
    """Find internal links from HTML + brute-force common paths for JS-heavy sites."""
    keywords = [
        "about", "service", "product", "feature", "pricing",
        "solution", "how-it-work", "why-", "benefit", "faq",
        "testimonial", "case-stud", "review", "client", "partner",
        "what-we-do", "our-story", "who-we-are", "offer",
        "tool", "signal", "academ", "blog", "plan", "contact",
        "demo", "portfolio", "team", "mission", "platform",
    ]
    found = set()
    parsed_base = urlparse(base_url)
    base_clean = f"{parsed_base.scheme}://{parsed_base.netloc}"

    # Method 1: Discover from HTML links
    for match in re.finditer(r'<a[^>]+href=["\']([^"\'#]+)["\']', html, re.I):
        href = match.group(1).strip()
        if href.startswith("javascript:") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        full = urljoin(base_url, href)
        parsed = urlparse(full)
        if parsed.netloc != parsed_base.netloc:
            continue
        path_lower = parsed.path.lower()
        for kw in keywords:
            if kw in path_lower:
                found.add(full.split("?")[0].split("#")[0])
                break

    # Method 2: Also scan JavaScript/JSON for route definitions (SPA sites)
    # Look for route paths in scripts like "/about", "/features", "/pricing"
    for match in re.finditer(r'["\']/(about|features?|pricing|services?|products?|blog|tools?|academy|signals?|contact|demo|platform|faq|team)["\'/]', html, re.I):
        path = match.group(1)
        found.add(f"{base_clean}/{path}")

    # Method 3: Brute-force common subpage paths (critical for JS-rendered sites)
    # These are the most common paths that contain valuable marketing content
    common_paths = [
        "/about", "/about-us", "/features", "/pricing",
        "/services", "/products", "/blog", "/contact",
        "/how-it-works", "/why-us", "/faq", "/testimonials",
        "/tools", "/platform", "/solutions", "/plans",
    ]
    for path in common_paths:
        found.add(f"{base_clean}{path}")

    # Remove the base URL itself
    found.discard(base_url.rstrip("/"))
    found.discard(base_url)

    return list(found)[:12]  # cap at 12 subpages


async def _fetch_text(client: httpx.AsyncClient, url: str) -> Optional[str]:
    """Fetch raw text content (for sitemap, robots.txt, etc.)."""
    try:
        resp = await client.get(url, headers=_headers(), follow_redirects=True, timeout=8.0)
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return None


async def crawl_website(url: str) -> Dict[str, Any]:
    """Crawl homepage + key subpages + sitemap + robots.txt. Returns all extracted content."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    async with httpx.AsyncClient(timeout=20.0, verify=False) as client:
        # Fetch homepage, sitemap.xml, and robots.txt in parallel
        hp_task = _fetch_page(client, url)
        sitemap_task = _fetch_text(client, f"{base}/sitemap.xml")
        robots_task = _fetch_text(client, f"{base}/robots.txt")

        homepage_html, sitemap_text, robots_text = await asyncio.gather(
            hp_task, sitemap_task, robots_task, return_exceptions=True
        )

        # Fallback: try www. prefix if bare domain failed
        if not isinstance(homepage_html, str) or not homepage_html:
            if not parsed.netloc.startswith("www."):
                www_url = f"{parsed.scheme}://www.{parsed.netloc}{parsed.path}"
                print(f"[scanner] Bare domain failed, trying www: {www_url}")
                homepage_html = await _fetch_page(client, www_url)
                if isinstance(homepage_html, str) and homepage_html:
                    url = www_url
                    parsed = urlparse(url)
                    base = f"{parsed.scheme}://{parsed.netloc}"
                    # Also re-fetch sitemap/robots from www domain
                    sitemap_text, robots_text = await asyncio.gather(
                        _fetch_text(client, f"{base}/sitemap.xml"),
                        _fetch_text(client, f"{base}/robots.txt"),
                        return_exceptions=True,
                    )

        if not isinstance(homepage_html, str) or not homepage_html:
            raise HTTPException(status_code=400, detail="Could not fetch website. Check the URL and try again.")

        # Extract URLs from sitemap.xml
        sitemap_urls = []
        if isinstance(sitemap_text, str) and sitemap_text:
            sitemap_urls = re.findall(r'<loc>(.*?)</loc>', sitemap_text, re.I)
            print(f"[scanner] Found {len(sitemap_urls)} URLs in sitemap.xml")

        # Discover subpages from HTML links + brute-force + sitemap
        subpage_urls = _discover_subpages(homepage_html, url)

        # Add relevant sitemap URLs
        relevance_keywords = ["about", "feature", "pricing", "service", "product", "tool",
                              "blog", "faq", "contact", "team", "platform", "signal",
                              "academy", "solution", "plan", "offer", "how"]
        for surl in sitemap_urls:
            if any(kw in surl.lower() for kw in relevance_keywords):
                subpage_urls.append(surl)

        # Deduplicate
        subpage_urls = list(set(subpage_urls))[:12]
        print(f"[scanner] Will try {len(subpage_urls)} subpages: {subpage_urls}")

        # Fetch subpages in parallel
        subpage_htmls = {}
        homepage_body_len = len(re.sub(r'<[^>]+>', '', homepage_html))

        tasks = [_fetch_page(client, sp_url) for sp_url in subpage_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for sp_url, result in zip(subpage_urls, results):
            if isinstance(result, str) and result:
                # Skip pages that are identical to homepage (SPA shell)
                result_body_len = len(re.sub(r'<[^>]+>', '', result))
                # If content length differs by >10%, it's likely a different page
                if homepage_body_len == 0 or abs(result_body_len - homepage_body_len) / max(homepage_body_len, 1) > 0.10:
                    subpage_htmls[sp_url] = result

        print(f"[scanner] Got {len(subpage_htmls)} unique subpages (filtered SPA duplicates)")

    # Extract content from all pages
    homepage_data = extract_page_content(homepage_html, is_homepage=True)

    # Store sitemap and robots for AI context
    homepage_data["sitemap_urls"] = sitemap_urls[:30]
    homepage_data["robots_txt"] = (robots_text if isinstance(robots_text, str) else "")[:1000]

    all_subpage_content = []
    for sp_url, sp_html in subpage_htmls.items():
        sp_data = extract_page_content(sp_html, is_homepage=False)
        sp_data["url"] = sp_url
        all_subpage_content.append(sp_data)

    return {
        "url": url,
        "homepage": homepage_data,
        "subpages": all_subpage_content,
        "pages_crawled": 1 + len(subpage_htmls),
    }


# ─── Content extraction ──────────────────────────────────────────────

def extract_page_content(html: str, is_homepage: bool = True) -> Dict[str, Any]:
    """Extract rich structured content from a single page."""

    data: Dict[str, Any] = {}

    # 1. Title
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    data["title"] = m.group(1).strip() if m else ""

    # 2. Meta tags
    data["meta_description"] = _extract_meta(html, "description")
    data["meta_keywords"] = _extract_meta(html, "keywords")

    # 3. Open Graph
    og = {}
    for m in re.finditer(r'<meta[^>]*property=["\']og:(\w+)["\'][^>]*content=["\'](.*?)["\']', html, re.I):
        og[m.group(1)] = m.group(2).strip()
    # Also check reverse attribute order
    for m in re.finditer(r'<meta[^>]*content=["\'](.*?)["\'][^>]*property=["\']og:(\w+)["\']', html, re.I):
        og[m.group(2)] = m.group(1).strip()
    data["og_data"] = og

    # 4. JSON-LD structured data (Schema.org)
    jsonld_blocks = []
    for m in re.finditer(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.S):
        try:
            parsed = json.loads(m.group(1).strip())
            jsonld_blocks.append(parsed)
        except json.JSONDecodeError:
            pass
    data["jsonld"] = jsonld_blocks

    # 5. Headings (h1-h3)
    headings = []
    for m in re.finditer(r"<h([1-3])[^>]*>(.*?)</h\1>", html, re.I | re.S):
        text = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if text and 3 < len(text) < 300:
            headings.append({"level": int(m.group(1)), "text": text})
    data["headings"] = headings[:30]

    # 6. Testimonials / reviews
    testimonials = _extract_testimonials(html)
    data["testimonials"] = testimonials

    # 7. Pricing signals
    prices = list(set(re.findall(r'[\$\£\€\₦][\d,]+(?:\.\d{2})?', html)))
    data["pricing_signals"] = prices[:10]

    # 8. Contact info
    emails = list(set(re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', html)))
    phones = list(set(re.findall(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]{7,15}', html)))
    data["contact"] = {"emails": emails[:5], "phones": phones[:5]}

    # 9. Social media links
    socials = {}
    for platform in ["facebook", "twitter", "instagram", "linkedin", "youtube", "tiktok", "x.com"]:
        m = re.search(rf'href=["\']([^"\']*{platform}[^"\']*)["\']', html, re.I)
        if m:
            socials[platform.replace("x.com", "twitter")] = m.group(1)
    data["social_links"] = socials

    # 10. Trust badges / certifications
    trust_terms = ["certified", "accredited", "licensed", "award", "partner", "trusted by", "as seen", "featured in", "clients include", "used by"]
    trust_signals = []
    body_lower = html.lower()
    for term in trust_terms:
        if term in body_lower:
            trust_signals.append(term)
    data["trust_signals"] = trust_signals

    # 11. CTA buttons (text)
    ctas = []
    for m in re.finditer(r'<(?:button|a)[^>]*class=["\'][^"\']*(?:btn|button|cta)[^"\']*["\'][^>]*>(.*?)</(?:button|a)>', html, re.I | re.S):
        text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if text and len(text) < 50:
            ctas.append(text)
    # Also look for common CTA patterns
    for m in re.finditer(r'<a[^>]+>(Sign Up|Get Started|Buy Now|Learn More|Start Free|Try Free|Contact Us|Book a Demo|Request Demo|Join Now|Subscribe|Download|Start Trial)[^<]*</a>', html, re.I):
        ctas.append(m.group(1).strip())
    data["cta_buttons"] = list(set(ctas))[:10]

    # 12. Images with alt text (product/hero images)
    images = []
    for m in re.finditer(r'<img[^>]+(?:alt=["\']([^"\']+)["\'])?[^>]*(?:src=["\']([^"\']+)["\'])?', html, re.I):
        alt = m.group(1) or ""
        src = m.group(2) or ""
        if alt and len(alt) > 5 and not any(skip in alt.lower() for skip in ["logo", "icon", "arrow", "close", "menu", "pixel"]):
            images.append({"alt": alt, "src": src})
    data["key_images"] = images[:10]

    # 13. Embedded app data (Next.js __NEXT_DATA__, Nuxt __NUXT__, generic window.__APP_STATE__)
    embedded_data = []
    for pattern in [
        r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
        r'window\.__NEXT_DATA__\s*=\s*(\{.*?\});',
        r'window\.__NUXT__\s*=\s*(\{.*?\});',
        r'window\.__APP_STATE__\s*=\s*(\{.*?\});',
        r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});',
    ]:
        m = re.search(pattern, html, re.I | re.S)
        if m:
            try:
                raw = m.group(1).strip()[:5000]
                embedded_data.append(raw)
            except Exception:
                pass

    # Also extract ALL visible text from script-embedded content strings
    # Many SPAs have readable text in their JS bundles
    for m in re.finditer(r'"((?:[^"\\]|\\.){50,500})"', html):
        text_chunk = m.group(1)
        # Filter for actual readable content (has spaces, lowercase words)
        if re.search(r'[a-z]{3,}\s+[a-z]{3,}\s+[a-z]{3,}', text_chunk) and '<' not in text_chunk[:20]:
            embedded_data.append(text_chunk)
    data["embedded_app_data"] = embedded_data[:5]

    # 14. Body text (cleaned, generous limit)
    clean = html
    for tag in ["script", "style", "nav", "footer", "noscript", "svg", "iframe", "header"]:
        clean = re.sub(f"<{tag}[^>]*>.*?</{tag}>", "", clean, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", clean)
    text = re.sub(r"\s+", " ", text).strip()
    # Remove common boilerplate
    text = re.sub(r"(cookie|privacy policy|terms of service|all rights reserved|©)[^.]*\.", "", text, flags=re.I)
    data["body_text"] = text[:8000]

    # 15. Navigation menu items (reveals site structure)
    nav_items = []
    nav_html = re.search(r"<nav[^>]*>(.*?)</nav>", html, re.I | re.S)
    if nav_html:
        for m in re.finditer(r"<a[^>]*>(.*?)</a>", nav_html.group(1), re.I | re.S):
            item = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            if item and 2 < len(item) < 40:
                nav_items.append(item)
    data["navigation"] = nav_items[:20]

    # 16. Copyright / brand name from footer
    footer_match = re.search(r"<footer[^>]*>(.*?)</footer>", html, re.I | re.S)
    if footer_match:
        footer_text = re.sub(r"<[^>]+>", " ", footer_match.group(1)).strip()
        copyright_match = re.search(r"©\s*\d{0,4}\s*(.*?)(?:\.|All|$)", footer_text, re.I)
        data["copyright_name"] = copyright_match.group(1).strip() if copyright_match else ""
    else:
        data["copyright_name"] = ""

    return data


def _extract_meta(html: str, name: str) -> str:
    patterns = [
        rf'<meta[^>]*name=["\']' + name + r'["\'][^>]*content=["\'](.*?)["\']',
        rf'<meta[^>]*content=["\'](.*?)["\'][^>]*name=["\']' + name + r'["\']',
    ]
    for p in patterns:
        m = re.search(p, html, re.I)
        if m:
            return m.group(1).strip()
    return ""


def _extract_testimonials(html: str) -> List[str]:
    """Extract testimonial/review text from common patterns."""
    testimonials = []

    # Look for blockquote or elements with testimonial classes
    for m in re.finditer(r'<blockquote[^>]*>(.*?)</blockquote>', html, re.I | re.S):
        text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if 20 < len(text) < 500:
            testimonials.append(text)

    # Look for elements with review/testimonial in class
    for m in re.finditer(r'<(?:div|p|span)[^>]*class=["\'][^"\']*(?:testimonial|review|quote|feedback)[^"\']*["\'][^>]*>(.*?)</(?:div|p|span)>', html, re.I | re.S):
        text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if 20 < len(text) < 500:
            testimonials.append(text)

    return testimonials[:5]


# ─── Build unified content package for AI ─────────────────────────────

def build_ai_content_package(crawl_data: Dict[str, Any]) -> str:
    """Compile all crawled data into a rich text package for GPT-4o."""
    parts = []
    hp = crawl_data["homepage"]

    parts.append(f"=== WEBSITE: {crawl_data['url']} ===")
    parts.append(f"Pages crawled: {crawl_data['pages_crawled']}")

    # Homepage
    parts.append(f"\n--- HOMEPAGE ---")
    parts.append(f"Title: {hp.get('title', '')}")
    parts.append(f"Meta Description: {hp.get('meta_description', '')}")
    parts.append(f"Meta Keywords: {hp.get('meta_keywords', '')}")

    if hp.get("og_data"):
        parts.append(f"Open Graph: {json.dumps(hp['og_data'])}")

    if hp.get("jsonld"):
        # Truncate JSON-LD to avoid token explosion
        jsonld_str = json.dumps(hp["jsonld"], indent=None)[:2000]
        parts.append(f"Structured Data (JSON-LD): {jsonld_str}")

    if hp.get("navigation"):
        parts.append(f"Navigation Menu: {', '.join(hp['navigation'])}")

    if hp.get("headings"):
        headings_text = "\n".join([f"  H{h['level']}: {h['text']}" for h in hp["headings"][:20]])
        parts.append(f"Headings:\n{headings_text}")

    if hp.get("cta_buttons"):
        parts.append(f"CTA Buttons: {', '.join(hp['cta_buttons'])}")

    if hp.get("testimonials"):
        parts.append("Testimonials Found:")
        for t in hp["testimonials"]:
            parts.append(f'  "{t}"')

    if hp.get("trust_signals"):
        parts.append(f"Trust Signals: {', '.join(hp['trust_signals'])}")

    if hp.get("pricing_signals"):
        parts.append(f"Pricing Signals: {', '.join(hp['pricing_signals'])}")

    if hp.get("social_links"):
        parts.append(f"Social Media: {json.dumps(hp['social_links'])}")

    if hp.get("contact"):
        if hp["contact"]["emails"]:
            parts.append(f"Contact Emails: {', '.join(hp['contact']['emails'])}")
        if hp["contact"]["phones"]:
            parts.append(f"Contact Phones: {', '.join(hp['contact']['phones'])}")

    if hp.get("copyright_name"):
        parts.append(f"Copyright Name: {hp['copyright_name']}")

    if hp.get("key_images"):
        img_alts = [img["alt"] for img in hp["key_images"] if img["alt"]]
        if img_alts:
            parts.append(f"Image Descriptions: {', '.join(img_alts)}")

    if hp.get("embedded_app_data"):
        parts.append("Embedded App/SPA Data (extracted from JavaScript):")
        for chunk in hp["embedded_app_data"][:3]:
            parts.append(f"  {chunk[:1000]}")

    # Sitemap URLs (reveals site structure even when JS-rendered)
    if hp.get("sitemap_urls"):
        parts.append(f"\nSitemap URLs (reveals full site structure):")
        for surl in hp["sitemap_urls"][:20]:
            parts.append(f"  {surl}")

    # Robots.txt
    if hp.get("robots_txt") and len(hp["robots_txt"]) > 20:
        parts.append(f"\nRobots.txt:\n{hp['robots_txt'][:500]}")

    parts.append(f"\nHomepage Body Text (first 4000 chars):\n{hp.get('body_text', '')[:4000]}")

    # Subpages
    for sp in crawl_data.get("subpages", []):
        parts.append(f"\n--- SUBPAGE: {sp.get('url', '')} ---")
        parts.append(f"Title: {sp.get('title', '')}")
        if sp.get("headings"):
            headings_text = "\n".join([f"  H{h['level']}: {h['text']}" for h in sp["headings"][:10]])
            parts.append(f"Headings:\n{headings_text}")
        if sp.get("testimonials"):
            for t in sp["testimonials"]:
                parts.append(f'  Testimonial: "{t}"')
        if sp.get("pricing_signals"):
            parts.append(f"Pricing: {', '.join(sp['pricing_signals'])}")
        # Subpage body text (shorter limit per page)
        if sp.get("body_text"):
            parts.append(f"Content:\n{sp['body_text'][:2500]}")

    full = "\n".join(parts)
    # Final safety cap — leave room for the system prompt
    return full[:12000]


# ─── GPT-4o Marketing Strategist ──────────────────────────────────────

async def analyze_with_ai(content_package: str, url: str) -> Dict[str, Any]:
    """
    GPT-4o acts as a senior marketing strategist analyzing the business.
    Returns a comprehensive business intelligence + creative strategy report.
    """
    if not get_openrouter_key():
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")

    prompt = f"""You are ADLYTICS — a senior performance marketing strategist with 15 years experience in digital advertising, brand positioning, and conversion optimization. You've been hired to analyze a business from their website and produce a comprehensive marketing intelligence report.

WEBSITE CONTENT (crawled from multiple pages):
{content_package}

YOUR MISSION: Analyze this business deeply and produce a JSON report. DO NOT give shallow generic info — dig into what makes this business specific. If the website content is limited, make strategic inferences from the industry, positioning, and any signals you can find.

Return ONLY valid JSON with this structure (keep values concise to fit within token limits):

{{
  "business_profile": {{
    "business_name": "Brand name",
    "tagline": "Tagline or crafted slogan",
    "industry": "Specific industry niche",
    "business_model": "Revenue model",
    "description": "4-5 sentence description of business, audience, and differentiator"
  }},
  "products_and_features": {{
    "main_products": [
      {{"name": "Product name", "description": "1-2 sentences", "key_benefit": "Top benefit"}}
    ],
    "all_features": ["feature1", "feature2", "...at least 10 items"],
    "pricing_model": "Pricing approach"
  }},
  "target_audience": {{
    "primary_persona": {{
      "description": "2-3 sentences about ideal customer",
      "demographics": "Age, income, location",
      "pain_points": ["point1", "point2", "point3", "point4"],
      "desires": ["desire1", "desire2", "desire3"],
      "objections": ["objection1", "objection2", "objection3"]
    }}
  }},
  "brand_analysis": {{
    "brand_voice": "Communication style",
    "tone": "Emotional tone",
    "trust_signals": ["signal1", "signal2", "signal3"],
    "unique_positioning": "2 sentence differentiator",
    "color_mood": "Visual brand feel"
  }},
  "competitive_landscape": {{
    "likely_competitors": ["competitor1", "competitor2", "competitor3"],
    "competitive_advantages": ["advantage1", "advantage2"],
    "market_gaps": ["gap1", "gap2"]
  }},
  "ad_strategy": {{
    "recommended_funnel_stage": "Stage + why",
    "emotional_trigger": "Strongest emotional trigger",
    "best_platform": "Platform + why"
  }},
  "ad_angles": [
    {{
      "angle_name": "Short name",
      "strategy": "Marketing principle",
      "headline": "Ad headline (max 10 words)",
      "body_copy": "4-6 sentence ad copy. SPECIFIC to this business with actual feature names.",
      "cta": "CTA text",
      "hook_line": "Opening scroll-stopper line",
      "predicted_effectiveness": 85,
      "best_platform": "Platform"
    }}
  ],
  "creative_brief": {{
    "recommended_angle_index": 0,
    "video_direction": "Video style direction for this business",
    "image_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "color_palette": ["#hex1", "#hex2", "#hex3"],
    "voiceover_style": "Voice direction"
  }},
  "funnel_intelligence": {{
    "landing_page_assessment": "2 sentence assessment",
    "conversion_blockers": ["blocker1", "blocker2"],
    "retargeting_angle": "Retargeting message"
  }}
}}

RULES:
- EXACTLY 4 ad_angles, ranked by effectiveness. Each body_copy: 4-6 sentences referencing REAL features.
- AT LEAST 3 main_products, 10 all_features, 4 pain_points, 3 competitors.
- If website content is thin (JS-rendered site), use your training knowledge of the industry to fill in features, products, and competitors. A forex platform MUST list features like signals, chart analysis, risk calculator, copy trading, education, etc.
- Each ad angle uses a DIFFERENT strategy: Benefit-Led, Pain-Agitate-Solution, Social Proof, Scarcity.
- Return ONLY valid JSON, no markdown fences, no text outside the JSON."""

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            OPENROUTER_API,
            headers={
                "Authorization": f"Bearer {get_openrouter_key()}",
                "HTTP-Referer": "https://adlytics.ai",
                "X-Title": "Adlytics Deep Scanner",
            },
            json={
                "model": GPT4O_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.6,
                "max_tokens": 6000,
            },
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"AI analysis failed: {response.text[:300]}")

        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Strip markdown code fences
        md_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
        if md_match:
            content = md_match.group(1)

        content = content.strip()
        if not content.startswith("{"):
            obj_match = re.search(r"\{[\s\S]*\}", content)
            if obj_match:
                content = obj_match.group(0)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to repair truncated JSON
            try:
                open_braces = content.count("{") - content.count("}")
                open_brackets = content.count("[") - content.count("]")
                repaired = content
                if repaired.rstrip()[-1] not in ']},"':
                    repaired += '"'
                repaired += "]" * max(0, open_brackets)
                repaired += "}" * max(0, open_braces)
                return json.loads(repaired)
            except Exception:
                print(f"[scanner] JSON parse failed. Content preview: {content[:500]}")
                raise HTTPException(status_code=500, detail="Failed to parse AI marketing analysis. Try again.")


# ─── API Endpoint ─────────────────────────────────────────────────────

@router.post("/scan")
async def scan_website(url: str = Form(...)):
    """
    Deep-scan a website and return comprehensive marketing intelligence.
    Crawls multiple pages, extracts structured data, and generates
    a full strategic analysis with ranked ad angles.
    """
    if not url or len(url.strip()) < 4:
        raise HTTPException(status_code=400, detail="Please provide a valid website URL")

    url = url.strip()
    print(f"[scanner] Deep scanning: {url}")

    try:
        # Step 1: Multi-page crawl
        crawl_data = await crawl_website(url)
        print(f"[scanner] Crawled {crawl_data['pages_crawled']} pages from {url}")

        # Step 2: Build content package
        content_package = build_ai_content_package(crawl_data)
        print(f"[scanner] Content package: {len(content_package)} chars")

        # Step 3: AI marketing strategist analysis
        analysis = await analyze_with_ai(content_package, url)
        print(f"[scanner] Analysis complete for: {analysis.get('business_profile', {}).get('business_name', 'unknown')}")

        return {
            "success": True,
            "data": {
                "url": url,
                "pages_crawled": crawl_data["pages_crawled"],
                "profile": analysis.get("business_profile", {}),
                "products_and_features": analysis.get("products_and_features", {}),
                "target_audience": analysis.get("target_audience", {}),
                "brand_analysis": analysis.get("brand_analysis", {}),
                "competitive_landscape": analysis.get("competitive_landscape", {}),
                "ad_strategy": analysis.get("ad_strategy", {}),
                "ad_angles": analysis.get("ad_angles", []),
                "creative_brief": analysis.get("creative_brief", {}),
                "funnel_intelligence": analysis.get("funnel_intelligence", {}),
                "raw_meta": {
                    "title": crawl_data["homepage"].get("title", ""),
                    "meta_description": crawl_data["homepage"].get("meta_description", ""),
                    "headings_count": len(crawl_data["homepage"].get("headings", [])),
                    "subpages_found": len(crawl_data.get("subpages", [])),
                    "testimonials_found": len(crawl_data["homepage"].get("testimonials", [])),
                    "trust_signals": crawl_data["homepage"].get("trust_signals", []),
                },
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Deep scan failed: {type(e).__name__}: {str(e)}")
