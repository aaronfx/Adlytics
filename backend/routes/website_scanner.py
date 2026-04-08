"""
Website Scanner — extracts business info from any URL.

Fetches a website, extracts key content (title, meta description, headings,
body text, products/services), then uses GPT-4o to create a structured
business profile that other Adlytics features can use to auto-generate
ad copy, creatives, and video ads.
"""

import os
import re
import json
import httpx
from typing import Optional
from fastapi import APIRouter, HTTPException, Form

router = APIRouter(prefix="/scanner", tags=["website-scanner"])

OPENROUTER_API = "https://openrouter.ai/api/v1/chat/completions"
GPT4O_MODEL = "openai/gpt-4o"


def get_openrouter_key():
    return os.getenv("OPENROUTER_API_KEY")


def clean_html_to_text(html: str) -> dict:
    """Extract meaningful text content from raw HTML."""

    # Extract title
    title = ""
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = title_match.group(1).strip()

    # Extract meta description
    meta_desc = ""
    meta_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']', html, re.IGNORECASE)
    if not meta_match:
        meta_match = re.search(r'<meta[^>]*content=["\'](.*?)["\'][^>]*name=["\']description["\']', html, re.IGNORECASE)
    if meta_match:
        meta_desc = meta_match.group(1).strip()

    # Extract OG tags
    og_data = {}
    for og_match in re.finditer(r'<meta[^>]*property=["\']og:(\w+)["\'][^>]*content=["\'](.*?)["\']', html, re.IGNORECASE):
        og_data[og_match.group(1)] = og_match.group(2).strip()

    # Extract headings
    headings = []
    for h_match in re.finditer(r'<h[1-3][^>]*>(.*?)</h[1-3]>', html, re.IGNORECASE | re.DOTALL):
        text = re.sub(r'<[^>]+>', '', h_match.group(1)).strip()
        if text and len(text) > 2 and len(text) < 200:
            headings.append(text)

    # Remove script, style, nav, footer, header tags
    clean = html
    for tag in ['script', 'style', 'nav', 'footer', 'noscript', 'svg', 'iframe']:
        clean = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', clean, flags=re.IGNORECASE | re.DOTALL)

    # Remove all HTML tags
    text = re.sub(r'<[^>]+>', ' ', clean)
    # Clean whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove common junk
    text = re.sub(r'(cookie|privacy policy|terms of service|all rights reserved|©).*?\.', '', text, flags=re.IGNORECASE)

    # Truncate to reasonable length for AI processing
    body_text = text[:4000] if len(text) > 4000 else text

    return {
        "title": title,
        "meta_description": meta_desc,
        "og_data": og_data,
        "headings": headings[:15],
        "body_text": body_text,
    }


async def fetch_website(url: str) -> str:
    """Fetch website HTML content."""
    # Normalize URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Adlytics/1.0; +https://adlytics.ai)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, verify=False) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Could not fetch website (HTTP {response.status_code}). Check the URL and try again."
            )
        return response.text


async def analyze_with_ai(extracted: dict, url: str) -> dict:
    """Use GPT-4o to create a structured business profile from website content."""

    if not get_openrouter_key():
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")

    prompt = f"""Analyze this website content and extract a detailed business profile.

URL: {url}
Page Title: {extracted['title']}
Meta Description: {extracted['meta_description']}
Key Headings: {json.dumps(extracted['headings'][:10])}
OG Data: {json.dumps(extracted.get('og_data', {}))}
Page Content (excerpt): {extracted['body_text'][:3000]}

Return a JSON object with these fields:
1. "business_name" - the company/brand name
2. "industry" - the industry category (e.g., "Real Estate", "Finance", "E-commerce", "SaaS", "Health & Wellness")
3. "description" - a 2-3 sentence description of what the business does
4. "products_services" - array of 3-5 main products or services offered
5. "target_audience" - who their ideal customer is (1-2 sentences)
6. "unique_selling_points" - array of 2-4 key differentiators or USPs
7. "tone" - the brand's communication tone (e.g., "Professional", "Friendly", "Luxurious", "Urgent")
8. "key_benefits" - array of 3-5 customer benefits
9. "call_to_action" - the primary CTA they use (e.g., "Sign Up", "Buy Now", "Get Started")
10. "ad_copy_suggestion" - a ready-to-use ad copy paragraph (3-4 sentences) based on the business
11. "image_keywords" - array of 3-5 keywords for finding relevant stock images
12. "color_mood" - suggested color mood for ads (e.g., "dark professional", "bright energetic", "warm luxury")

Return ONLY valid JSON, no additional text or markdown."""

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            OPENROUTER_API,
            headers={
                "Authorization": f"Bearer {get_openrouter_key()}",
                "HTTP-Referer": "https://adlytics.ai",
                "X-Title": "Adlytics Website Scanner",
            },
            json={
                "model": GPT4O_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.5,
                "max_tokens": 2000,
            },
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"AI analysis failed: {response.text[:200]}")

        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Strip markdown code blocks
        md_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if md_match:
            content = md_match.group(1)

        content = content.strip()
        if not content.startswith('{'):
            obj_match = re.search(r'\{[\s\S]*\}', content)
            if obj_match:
                content = obj_match.group(0)

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"[scanner] JSON parse error: {content[:300]}")
            raise HTTPException(status_code=500, detail=f"Failed to parse business profile: {str(e)}")


@router.post("/scan")
async def scan_website(
    url: str = Form(...),
):
    """Scan a website and return a structured business profile."""

    if not url or len(url.strip()) < 4:
        raise HTTPException(status_code=400, detail="Please provide a valid website URL")

    url = url.strip()
    print(f"[scanner] Scanning website: {url}")

    try:
        # Step 1: Fetch the website
        html = await fetch_website(url)
        print(f"[scanner] Fetched {len(html)} bytes from {url}")

        # Step 2: Extract text content
        extracted = clean_html_to_text(html)
        print(f"[scanner] Extracted: title='{extracted['title']}', {len(extracted['headings'])} headings, {len(extracted['body_text'])} chars body")

        # Step 3: Analyze with AI
        profile = await analyze_with_ai(extracted, url)
        print(f"[scanner] AI profile generated for: {profile.get('business_name', 'unknown')}")

        return {
            "success": True,
            "data": {
                "url": url,
                "profile": profile,
                "raw_meta": {
                    "title": extracted["title"],
                    "meta_description": extracted["meta_description"],
                    "headings_count": len(extracted["headings"]),
                },
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Website scan failed: {type(e).__name__}: {str(e)}")
