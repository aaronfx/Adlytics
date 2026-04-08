"""
FastAPI router for AI ad creative generation.

Supports two backends:
1. OpenAI DALL-E 3 for actual image generation (requires OPENAI_API_KEY)
2. Fallback: SVG mockup generation using GPT-4o concept generation (requires OPENROUTER_API_KEY)
"""

import os
import re
import base64
import json
from typing import Optional, List
from datetime import datetime

import httpx
from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel, Field

from backend.services.benchmarks import get_benchmarks, calculate_percentile

router = APIRouter(prefix="/creative", tags=["creative-generation"])

# Environment variables - read at runtime via functions to pick up changes
def get_openai_key():
    return os.getenv("OPENAI_API_KEY")

def get_openrouter_key():
    return os.getenv("OPENROUTER_API_KEY")

# API endpoints
OPENAI_IMAGES_API = "https://api.openai.com/v1/images/generations"
OPENROUTER_API = "https://openrouter.ai/api/v1/chat/completions"

# Constants
DALL_E_MODEL = "dall-e-3"
GPT4O_MODEL = "openai/gpt-4o"
DEFAULT_TEMPERATURE = 0.9
DEFAULT_MAX_TOKENS = 3000
DALL_E_IMAGE_SIZE = "1024x1024"
MAX_VARIANTS = 4

# Platform and format specifications
PLATFORM_SPECS = {
    "facebook": {
        "feed_square": {"width": 1080, "height": 1080, "aspect_ratio": "1:1"},
        "feed_landscape": {"width": 1200, "height": 628, "aspect_ratio": "16:9"},
        "story_vertical": {"width": 1080, "height": 1920, "aspect_ratio": "9:16"},
    },
    "instagram": {
        "feed_square": {"width": 1080, "height": 1080, "aspect_ratio": "1:1"},
        "feed_landscape": {"width": 1080, "height": 566, "aspect_ratio": "16:9"},
        "story_vertical": {"width": 1080, "height": 1920, "aspect_ratio": "9:16"},
    },
    "tiktok": {
        "feed_vertical": {"width": 540, "height": 960, "aspect_ratio": "9:16"},
        "story_vertical": {"width": 1080, "height": 1920, "aspect_ratio": "9:16"},
    },
    "youtube": {
        "banner_horizontal": {"width": 1280, "height": 720, "aspect_ratio": "16:9"},
        "thumbnail": {"width": 1280, "height": 720, "aspect_ratio": "16:9"},
    },
    "google": {
        "banner_horizontal": {"width": 728, "height": 90, "aspect_ratio": "8:1"},
        "search_ad": {"width": 600, "height": 150, "aspect_ratio": "4:1"},
    },
}

STYLE_PRESETS = {
    "modern": "Contemporary design with clean lines, bright colors, and minimalist elements",
    "bold": "Strong, attention-grabbing colors and typography with high contrast",
    "minimal": "Simplistic design with white space, neutral colors, and essential elements only",
    "luxury": "Premium feel with elegant typography, metallic accents, and sophisticated color palettes",
    "playful": "Fun, vibrant colors with rounded elements and casual, friendly typography",
    "corporate": "Professional, trustworthy design with structured layouts and standard business colors",
}

INDUSTRY_VARIANTS = {
    "general": "general consumer product",
    "ecommerce": "e-commerce and retail",
    "saas": "software as a service",
    "finance": "financial services",
    "healthcare": "healthcare and wellness",
    "real_estate": "real estate and property",
    "travel": "travel and hospitality",
    "food": "food and beverage",
}


# Response models
class PlatformSpecs(BaseModel):
    recommended_size: str
    format: str
    max_text_ratio: str


class CreativeScores(BaseModel):
    overall_score: int
    visual_appeal: int
    message_clarity: int
    cta_effectiveness: int
    platform_fit: int
    brand_consistency: int


class CreativeVariant(BaseModel):
    headline: str
    body_copy: str
    cta_text: str
    visual_concept: str
    image_url: Optional[str] = None
    dall_e_prompt: str
    color_palette: List[str]
    scores: CreativeScores
    predicted_ctr: float
    platform_specs: PlatformSpecs


class CreativeGenerationResponse(BaseModel):
    success: bool
    data: dict
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


async def generate_creative_concepts(
    product_description: str,
    platform: str,
    ad_format: str,
    style: str,
    industry: str,
    brand_name: Optional[str],
    headline: Optional[str],
    cta_text: Optional[str],
    primary_color: Optional[str],
    num_variants: int,
) -> dict:
    """
    Use GPT-4o via OpenRouter to generate creative concepts, headlines, copy, and DALL-E prompts.
    """
    if not get_openrouter_key():
        raise HTTPException(
            status_code=500,
            detail="OPENROUTER_API_KEY not configured. Creative generation requires OpenRouter API access.",
        )

    style_description = STYLE_PRESETS.get(style, style)
    industry_description = INDUSTRY_VARIANTS.get(industry, industry)
    color_constraint = (
        f"Primary color should be {primary_color}." if primary_color else ""
    )

    prompt = f"""You are an expert ad creative director. Generate {num_variants} ad creative variants.

Product/Service: {product_description}
Brand: {brand_name or "Not specified"}
Platform: {platform}
Ad Format: {ad_format}
Style: {style_description}
Industry: {industry_description}
{color_constraint}
{'Headline must be: ' + headline if headline else ''}
{'CTA text must be: ' + cta_text if cta_text else 'Suggest compelling CTA text'}

For EACH variant, provide a JSON object with:
1. "headline" - compelling, platform-optimized headline (max 10 words)
2. "body_copy" - persuasive ad copy (2-3 sentences, max 150 words)
3. "cta_text" - call-to-action button text (if not provided)
4. "visual_concept" - detailed description of the visual composition (2-3 sentences)
5. "dall_e_prompt" - detailed DALL-E 3 prompt for image generation (100+ words, very specific)
6. "color_palette" - array of 3 hex colors (e.g., ["#FF6B6B", "#4ECDC4", "#45B7D1"])
7. "key_message" - single most important message

Return ONLY a valid JSON array with {num_variants} objects, no additional text.
"""

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            OPENROUTER_API,
            headers={
                "Authorization": f"Bearer {get_openrouter_key()}",
                "HTTP-Referer": "https://adlytics.ai",
                "X-Title": "Adlytics Creative Generation",
            },
            json={
                "model": GPT4O_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": DEFAULT_TEMPERATURE,
                "max_tokens": DEFAULT_MAX_TOKENS,
            },
        )

        if response.status_code != 200:
            error_detail = response.text
            try:
                error_data = response.json()
                error_detail = error_data.get("error", {}).get("message", error_detail)
            except Exception:
                pass
            raise HTTPException(
                status_code=response.status_code,
                detail=f"OpenRouter API error: {error_detail}",
            )

        result = response.json()

        # Check for API-level errors in response body
        if "error" in result:
            error_msg = result["error"].get("message", str(result["error"]))
            raise HTTPException(
                status_code=500,
                detail=f"OpenRouter API error: {error_msg}",
            )

        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not content or not content.strip():
            print(f"[creative_gen] Empty response from OpenRouter. Full result: {json.dumps(result)[:500]}")
            raise HTTPException(
                status_code=500,
                detail="OpenRouter returned an empty response. Please try again.",
            )

        print(f"[creative_gen] Response preview: {content[:300]}")

        # Strip markdown code blocks if present (GPT-4o often wraps JSON)
        md_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if md_match:
            content = md_match.group(1)

        # Try to find JSON array in content
        content = content.strip()
        if not content.startswith('['):
            # Try to find the array within the text
            array_match = re.search(r'\[[\s\S]*\]', content)
            if array_match:
                content = array_match.group(0)

        # Parse JSON from response
        try:
            concepts = json.loads(content)
            if not isinstance(concepts, list):
                raise ValueError("Expected array of concepts")
            return {"concepts": concepts[:num_variants]}
        except json.JSONDecodeError as e:
            print(f"[creative_gen] JSON parse error. Content: {content[:500]}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse creative concepts from OpenRouter: {str(e)}",
            )


async def fetch_stock_image(query: str, width: int = 1080, height: int = 1080) -> Optional[str]:
    """
    Fetch a relevant stock image using multiple free services.
    Returns a direct image URL.
    """
    try:
        # Clean up query - extract key visual terms
        search_terms = query.lower()
        for word in ["the", "a", "an", "and", "or", "of", "for", "with", "in", "on", "to", "is", "are", "our", "your"]:
            search_terms = search_terms.replace(f" {word} ", " ")
        terms = [t for t in search_terms.strip().split() if len(t) > 2][:4]
        search_query = ",".join(terms)

        # Try loremflickr.com - free, keyword-based, no API key needed
        image_url = f"https://loremflickr.com/{width}/{height}/{search_query}"

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.head(image_url)
            if response.status_code == 200:
                final_url = str(response.url)
                print(f"[creative_gen] Stock image found: {final_url}")
                return final_url

        # Fallback: picsum.photos (random but high quality)
        fallback_url = f"https://picsum.photos/{width}/{height}"
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.head(fallback_url)
            if response.status_code == 200:
                final_url = str(response.url)
                print(f"[creative_gen] Picsum fallback image: {final_url}")
                return final_url

        return None
    except Exception as e:
        print(f"[creative_gen] Stock image fetch failed: {e}")
        return None


async def generate_dalle_image(prompt: str) -> Optional[str]:
    """
    Generate image using DALL-E 3 API. Returns base64-encoded image or None if API key not available.
    """
    api_key = get_openai_key()
    if not api_key:
        print("[creative_gen] No OPENAI_API_KEY set, skipping DALL-E")
        return None

    print(f"[creative_gen] Attempting DALL-E 3 generation with key: {api_key[:8]}...")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                OPENAI_IMAGES_API,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": DALL_E_MODEL,
                    "prompt": prompt,
                    "n": 1,
                    "size": DALL_E_IMAGE_SIZE,
                    "quality": "standard",
                },
            )

            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_data = response.json()
                    error_detail = error_data.get("error", {}).get("message", error_detail)
                except Exception:
                    pass
                raise Exception(f"DALL-E API error: {error_detail}")

            result = response.json()
            image_url = result.get("data", [{}])[0].get("url")

            if image_url:
                # Convert URL to base64 if it's a direct URL
                # For now, return the URL - in production you might download and convert
                img_response = await client.get(image_url, timeout=30.0)
                if img_response.status_code == 200:
                    image_b64 = base64.b64encode(img_response.content).decode()
                    return f"data:image/png;base64,{image_b64}"

            return None
        except Exception as e:
            # Log error but don't fail - fall back to mockup
            print(f"DALL-E generation failed: {str(e)}")
            return None


def generate_svg_mockup(
    headline: str,
    body_copy: str,
    cta_text: str,
    color_palette: List[str],
    width: int = 1080,
    height: int = 1080,
) -> str:
    """
    Generate an SVG mockup ad with headline, body copy, CTA button, and brand colors.
    Returns base64-encoded SVG.
    """
    primary_color = color_palette[0] if color_palette else "#FF6B6B"
    secondary_color = color_palette[1] if len(color_palette) > 1 else "#4ECDC4"
    text_color = "#FFFFFF"

    # Escape HTML special characters
    headline_safe = (
        headline.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    body_safe = (
        body_copy.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    cta_safe = (
        cta_text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <!-- Background gradient -->
  <defs>
    <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{primary_color};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{secondary_color};stop-opacity:0.8" />
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="{width}" height="{height}" fill="url(#bgGradient)"/>

  <!-- Content container -->
  <g id="content">
    <!-- Top spacing -->
    <rect x="40" y="80" width="{width - 80}" height="1" fill="none"/>

    <!-- Headline -->
    <text x="{width // 2}" y="200" font-family="Arial, sans-serif" font-size="52" font-weight="bold"
          text-anchor="middle" fill="{text_color}" word-spacing="9999">
      <tspan x="{width // 2}" dy="0">{headline_safe}</tspan>
    </text>

    <!-- Body copy -->
    <foreignObject x="60" y="320" width="{width - 120}" height="300">
      <body xmlns="http://www.w3.org/1999/xhtml">
        <p style="font-family: Arial, sans-serif; font-size: 24; color: {text_color};
                  line-height: 1.5; text-align: center; margin: 0;">
          {body_safe}
        </p>
      </body>
    </foreignObject>

    <!-- CTA Button -->
    <rect x="{width // 2 - 120}" y="{height - 180}" width="240" height="80"
          rx="8" fill="white" opacity="0.95"/>
    <text x="{width // 2}" y="{height - 130}" font-family="Arial, sans-serif" font-size="32"
          font-weight="bold" text-anchor="middle" fill="{primary_color}">
      {cta_safe}
    </text>
  </g>
</svg>"""

    svg_b64 = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{svg_b64}"


def calculate_creative_scores(
    headline: str,
    body_copy: str,
    cta_text: str,
    platform: str,
    industry: str,
) -> tuple:
    """
    Score the creative variant using benchmarks.
    Returns (scores_dict, predicted_ctr)
    """
    benchmarks = get_benchmarks(platform=platform, industry=industry)

    # Calculate individual scores (0-100)
    visual_appeal = min(95, 70 + len(headline) + (len(body_copy) // 20))
    message_clarity = min(100, 60 + (20 if len(cta_text) > 0 else 0))
    cta_effectiveness = min(100, 50 + (len(cta_text) * 2))

    # calculate_percentile expects (score, platform, industry)
    raw_score = (visual_appeal + message_clarity + cta_effectiveness) // 3
    platform_fit = calculate_percentile(raw_score, platform, industry)
    brand_consistency = 75  # Default for AI-generated

    overall_score = int(
        (visual_appeal + message_clarity + cta_effectiveness + platform_fit + brand_consistency)
        / 5
    )

    # Predicted CTR based on benchmark
    base_ctr = benchmarks.get("avg_ctr", 1.0)
    ctr_multiplier = overall_score / 75  # Normalize around 75 as baseline
    predicted_ctr = round(base_ctr * ctr_multiplier, 2)

    scores = {
        "overall_score": overall_score,
        "visual_appeal": visual_appeal,
        "message_clarity": message_clarity,
        "cta_effectiveness": cta_effectiveness,
        "platform_fit": int(platform_fit),
        "brand_consistency": brand_consistency,
    }

    return scores, predicted_ctr


def get_platform_specs(platform: str, ad_format: str) -> dict:
    """Get platform-specific format specifications."""
    platform_formats = PLATFORM_SPECS.get(platform, {})
    format_spec = platform_formats.get(ad_format, {})

    if not format_spec:
        # Fallback to first available format for platform
        format_spec = next(iter(platform_formats.values()), {})

    width = format_spec.get("width", 1080)
    height = format_spec.get("height", 1080)
    aspect_ratio = format_spec.get("aspect_ratio", "1:1")

    return {
        "recommended_size": f"{width}x{height}",
        "format": ad_format,
        "max_text_ratio": "20%",  # Facebook/Instagram recommendation
    }


@router.post("/generate", response_model=CreativeGenerationResponse)
async def generate_creatives(
    product_description: str = Form(...),
    platform: str = Form(...),
    ad_format: str = Form(...),
    style: str = Form(...),
    primary_color: Optional[str] = Form(None),
    cta_text: Optional[str] = Form(None),
    headline: Optional[str] = Form(None),
    industry: str = Form("general"),
    brand_name: Optional[str] = Form(None),
    num_variants: int = Form(2),
):
    """
    Generate ad creative variants with AI-generated concepts and images.

    Supports two backends:
    - DALL-E 3: Generates actual images (requires OPENAI_API_KEY)
    - Fallback: Generates SVG mockups with GPT-4o concepts (requires OPENROUTER_API_KEY)
    """

    # Validate inputs
    if not product_description or len(product_description.strip()) < 5:
        raise HTTPException(
            status_code=400,
            detail="product_description must be at least 5 characters",
        )

    if num_variants < 1 or num_variants > MAX_VARIANTS:
        raise HTTPException(
            status_code=400,
            detail=f"num_variants must be between 1 and {MAX_VARIANTS}",
        )

    if platform not in PLATFORM_SPECS:
        raise HTTPException(
            status_code=400,
            detail=f"platform must be one of: {list(PLATFORM_SPECS.keys())}",
        )

    if ad_format not in PLATFORM_SPECS.get(platform, {}):
        raise HTTPException(
            status_code=400,
            detail=f"ad_format '{ad_format}' not available for platform '{platform}'",
        )

    if style not in STYLE_PRESETS:
        raise HTTPException(
            status_code=400,
            detail=f"style must be one of: {list(STYLE_PRESETS.keys())}",
        )

    try:
        # Step 1: Generate creative concepts
        concepts_result = await generate_creative_concepts(
            product_description=product_description,
            platform=platform,
            ad_format=ad_format,
            style=style,
            industry=industry,
            brand_name=brand_name,
            headline=headline,
            cta_text=cta_text,
            primary_color=primary_color,
            num_variants=num_variants,
        )

        concepts = concepts_result.get("concepts", [])

        # Step 2: Generate images and score each variant
        # Priority: DALL-E 3 → Stock Photo → SVG Mockup
        variants = []
        has_openai = bool(get_openai_key())
        generation_mode = "dalle3" if has_openai else "stock"

        for concept in concepts:
            # Extract concept data
            variant_headline = concept.get("headline", "Amazing Offer")
            variant_body = concept.get(
                "body_copy", "Discover the difference today."
            )
            variant_cta = concept.get("cta_text", "Learn More")
            visual_concept = concept.get("visual_concept", "")
            dall_e_prompt = concept.get("dall_e_prompt", "")
            color_palette = concept.get(
                "color_palette", ["#FF6B6B", "#4ECDC4", "#45B7D1"]
            )
            key_message = concept.get("key_message", variant_headline)

            # Try DALL-E 3 first
            image_url = None
            if has_openai:
                image_url = await generate_dalle_image(dall_e_prompt)
                if image_url:
                    generation_mode = "dalle3"

            # Fallback: Stock photo from Unsplash
            if not image_url:
                platform_specs = get_platform_specs(platform, ad_format)
                size_str = platform_specs["recommended_size"]
                img_width, img_height = map(int, size_str.split("x"))
                # Build search query from product, industry and visual concept
                stock_query = f"{product_description[:50]} {industry} {visual_concept[:30]}"
                image_url = await fetch_stock_image(stock_query, img_width, img_height)
                if image_url:
                    generation_mode = "stock"

            # Final fallback: SVG mockup
            if not image_url:
                generation_mode = "mockup"
                platform_specs = get_platform_specs(platform, ad_format)
                size_str = platform_specs["recommended_size"]
                img_width, img_height = map(int, size_str.split("x"))
                image_url = generate_svg_mockup(
                    headline=variant_headline,
                    body_copy=variant_body,
                    cta_text=variant_cta,
                    color_palette=color_palette,
                    width=img_width,
                    height=img_height,
                )

            # Calculate scores
            scores_dict, predicted_ctr = calculate_creative_scores(
                headline=variant_headline,
                body_copy=variant_body,
                cta_text=variant_cta,
                platform=platform,
                industry=industry,
            )

            platform_specs = get_platform_specs(platform, ad_format)

            variant = {
                "headline": variant_headline,
                "body_copy": variant_body,
                "cta_text": variant_cta,
                "visual_concept": visual_concept,
                "image_url": image_url,
                "dall_e_prompt": dall_e_prompt,
                "color_palette": color_palette,
                "scores": scores_dict,
                "predicted_ctr": predicted_ctr,
                "platform_specs": platform_specs,
            }

            variants.append(variant)

        # Step 3: Build response
        response_data = {
            "variants": variants,
            "platform": platform,
            "industry": industry,
            "generation_mode": generation_mode,
            "style": style,
            "ad_format": ad_format,
        }

        return CreativeGenerationResponse(success=True, data=response_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Creative generation failed: {str(e)}",
        )


@router.get("/formats")
async def get_available_formats():
    """
    Returns available ad formats with dimensions for each platform.
    """
    formats = {}
    for platform, format_specs in PLATFORM_SPECS.items():
        formats[platform] = [
            {
                "format": format_name,
                "dimensions": f"{spec['width']}x{spec['height']}",
                "aspect_ratio": spec["aspect_ratio"],
            }
            for format_name, spec in format_specs.items()
        ]

    return {
        "success": True,
        "data": formats,
    }


@router.get("/styles")
async def get_available_styles():
    """
    Returns available style presets.
    """
    styles = [
        {"name": style_name, "description": description}
        for style_name, description in STYLE_PRESETS.items()
    ]

    return {
        "success": True,
        "data": {
            "styles": styles,
            "count": len(styles),
        },
    }


@router.get("/status")
async def get_status():
    """Check which generation backends are available."""
    return {
        "dalle3_available": bool(os.getenv("OPENAI_API_KEY")),
        "openrouter_available": bool(os.getenv("OPENROUTER_API_KEY")),
        "dalle3_key_prefix": os.getenv("OPENAI_API_KEY", "")[:8] + "..." if os.getenv("OPENAI_API_KEY") else None,
    }
