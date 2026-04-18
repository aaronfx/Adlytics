import logging
import os
import json
import httpx
import re
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Form, HTTPException

from backend.services.benchmarks import get_benchmarks, calculate_percentile, build_benchmark_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rewrite", tags=["rewrite"])

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = "https://api.openai.com/v1"
MODEL_ID = "gpt-4o"

# ─── REWRITE MODES ────────────────────────────────────────────────────────
# Full-ad rewrite modes
REWRITE_MODE_MODES = {
    "engaging": {
        "label": "More Engaging",
        "description": "Increase emotional hooks, relatability, conversational tone"
    },
    "hard_sell": {
        "label": "Hard Sell",
        "description": "Direct, benefit-heavy, urgency, scarcity tactics"
    },
    "social_proof": {
        "label": "Social Proof Heavy",
        "description": "Testimonials, numbers, trust signals, authority markers"
    },
    "urgency": {
        "label": "Urgency/Scarcity",
        "description": "Time limits, limited availability, FOMO triggers"
    },
    "storytelling": {
        "label": "Storytelling",
        "description": "Narrative arc, relatable character, problem-solution journey"
    },
    "playful": {
        "label": "Playful/Casual",
        "description": "Fun tone, humor, Gen-Z/millennial friendly, informal"
    }
}

# Element-level rewrite modes
ELEMENT_MODES = {
    "hook_only": {
        "label": "Hook/Opening Only",
        "description": "Rewrite just the hook/opening for attention"
    },
    "cta_only": {
        "label": "CTA Only",
        "description": "Rewrite just the Call-To-Action"
    },
    "body_only": {
        "label": "Body/Middle Only",
        "description": "Rewrite just the body/middle section"
    }
}

# All valid modes
ALL_REWRITE_MODES = {**REWRITE_MODE_MODES, **ELEMENT_MODES}


def _build_rewrite_prompt(
    original_ad: str,
    platform: str,
    industry: str,
    audience_country: str,
    original_scores_dict: Dict[str, Any],
    weaknesses_list: List[str],
    rewrite_mode: str,
    target_age: Optional[str],
    target_tone: Optional[str],
    brand_voice_context: str,
    benchmark_context: str,
    scanner_context: str = ""
) -> str:
    """Build the prompt for GPT-4o to rewrite the ad."""

    weaknesses_text = "\n".join(f"- {w}" for w in weaknesses_list) if weaknesses_list else "None identified"

    # Determine mode-specific instruction
    if rewrite_mode in ELEMENT_MODES:
        if rewrite_mode == "hook_only":
            mode_instruction = """REWRITE FOCUS: Hook/Opening Only
Rewrite ONLY the opening hook/headline to make it more attention-grabbing and relevant to the target audience. Keep the rest of the ad body and CTA unchanged."""
        elif rewrite_mode == "cta_only":
            mode_instruction = """REWRITE FOCUS: CTA Only
Rewrite ONLY the Call-To-Action to make it more compelling, urgent, and conversion-focused. Keep the hook and body unchanged."""
        else:  # body_only
            mode_instruction = """REWRITE FOCUS: Body/Middle Only
Rewrite ONLY the body/middle section of the ad. Keep the hook and CTA unchanged."""
    else:
        # Full-ad rewrite mode
        mode_data = REWRITE_MODE_MODES[rewrite_mode]
        mode_instruction = f"""REWRITE MODE: {mode_data['label'].upper()}
{mode_data['description']}

Apply this mode throughout the entire ad copy."""

    # Demographic targeting
    demographic_context = ""
    if target_age or target_tone:
        demographic_context = "\nTARGET DEMOGRAPHICS:"
        if target_age:
            demographic_context += f"\n- Age Group: {target_age}"
        if target_tone:
            demographic_context += f"\n- Preferred Tone: {target_tone}"
        demographic_context += "\n\nEnsure the rewrite resonates with this demographic profile."

    prompt = f"""You are an expert ad copywriter specializing in high-converting ads for {platform.upper()} platform in the {industry.upper()} industry.

ORIGINAL AD:
{original_ad}

CONTEXT:
- Platform: {platform.upper()}
- Industry: {industry.upper()}
- Target Audience: {audience_country.upper()}
- Current Scores: {json.dumps(original_scores_dict)}
- Identified Weaknesses:
{weaknesses_text}{demographic_context}

{benchmark_context}
{scanner_context}
{mode_instruction}{brand_voice_context}

You will provide TWO rewrite variants. For each variant, respond with PURE JSON (no markdown, no extra text) in this exact format:

{{
  "variants": [
    {{
      "rewritten_ad": "...",
      "changes_summary": ["change1", "change2", "change3"],
      "why_it_works": "Explanation of why this rewrite works...",
      "scores": {{
        "overall_score": 75,
        "emotion_score": 80,
        "clarity_score": 76,
        "cta_strength": 78,
        "platform_fit": 74,
        "pain_point_score": 72
      }},
      "predicted_ctr": 1.2
    }},
    {{
      "rewritten_ad": "...",
      "changes_summary": ["change1", "change2", "change3"],
      "why_it_works": "Explanation of why this rewrite works...",
      "scores": {{
        "overall_score": 73,
        "emotion_score": 78,
        "clarity_score": 74,
        "cta_strength": 75,
        "platform_fit": 72,
        "pain_point_score": 70
      }},
      "predicted_ctr": 1.1
    }}
  ]
}}

SCORING GUIDANCE:
- overall_score (0-100): Combined quality of all factors
- emotion_score (0-100): Emotional impact and resonance
- clarity_score (0-100): Message clarity and comprehension
- cta_strength (0-100): Call-to-action effectiveness
- platform_fit (0-100): Optimization for {platform} platform
- pain_point_score (0-100): How well it targets audience pain points
- predicted_ctr: Estimated click-through rate based on quality

IMPORTANT REQUIREMENTS:
1. Each variant must be meaningfully different (different angle, tone, or focus)
2. Scores must be realistic and based on industry benchmarks
3. Respond with VALID JSON only — no markdown code blocks, no extra text
4. Each score should be 0-100 inclusive
5. predicted_ctr should be a realistic decimal (e.g., 0.8, 1.2, 2.5)"""

    return prompt


async def _call_gpt4o(prompt: str) -> str:
    """Call OpenAI GPT-4o API with the provided prompt."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 4000,
        "top_p": 0.9
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OPENAI_BASE_URL}/chat/completions",
                json=payload,
                headers=headers
            )

            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to call GPT-4o: {response.status_code}"
                )

            result = response.json()
            return result["choices"][0]["message"]["content"]

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI service timeout - please try again")
    except Exception as e:
        logger.error(f"Error calling OpenRouter API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calling AI service: {str(e)}")


def _extract_json_from_response(response_text: str) -> Dict[str, Any]:
    """Extract JSON from GPT-4o response, handling markdown code blocks."""
    response_text = response_text.strip()

    # Try to find JSON code block
    json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*\})\s*```', response_text)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try direct JSON parsing (no code block)
        json_str = response_text

    try:
        data = json.loads(json_str)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {str(e)}\nResponse: {response_text[:500]}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse AI response as JSON: {str(e)}"
        )


def _normalize_scores(scores: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all scores are in valid 0-100 range."""
    normalized = {}
    for key, value in scores.items():
        if isinstance(value, (int, float)):
            # Clamp to 0-100
            normalized[key] = max(0, min(100, int(value)))
        else:
            normalized[key] = 0
    return normalized


def _prepare_voiceover_script(rewritten_ad: str, voice_style: str = "professional") -> Dict[str, Any]:
    """Prepare a voiceover script from the rewritten ad."""
    voice_styles = {
        "professional": "Use a clear, authoritative tone. Pace: moderate. Emphasis on key benefits.",
        "friendly": "Use a warm, conversational tone. Pace: natural and engaging. Sound approachable.",
        "urgent": "Use an energetic, fast-paced delivery. Emphasis on scarcity and time-sensitivity.",
        "casual": "Use a relaxed, conversational tone. Pace: natural. Sound like a friend talking."
    }

    delivery_notes = voice_styles.get(voice_style, voice_styles["professional"])

    return {
        "script": rewritten_ad,
        "voice_style": voice_style,
        "delivery_notes": delivery_notes,
        "duration_estimate_seconds": max(len(rewritten_ad.split()) // 2.5, 5)
    }


def _calculate_original_scores(original_scores_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate normalized original scores."""
    if not original_scores_dict:
        return {"overall": 50}

    scores = {}
    for key, value in original_scores_dict.items():
        if isinstance(value, (int, float)):
            scores[key] = max(0, min(100, int(value)))
        else:
            scores[key] = 50

    return scores


@router.post("")
async def rewrite_ad(
    original_ad: str = Form(..., description="The original ad copy to rewrite"),
    platform: str = Form("tiktok", description="Platform: tiktok, facebook, instagram, youtube, google"),
    industry: str = Form("finance", description="Industry for benchmarking"),
    audience_country: str = Form("nigeria", description="Target audience country"),
    original_scores: Optional[str] = Form('{"overall": 50}', description="JSON string of original ad scores"),
    weaknesses: Optional[str] = Form('["General improvement needed"]', description="JSON string of weaknesses"),
    rewrite_mode: str = Form("engaging", description="Rewrite mode or element to focus on"),
    target_age: Optional[str] = Form(None, description="Target age group (e.g., '18-24', '25-34')"),
    target_tone: Optional[str] = Form(None, description="Target tone (e.g., 'authoritative', 'friendly')"),
    prepare_voiceover: str = Form("false", description="Generate voiceover script"),
    voice_style: str = Form("professional", description="Voice style for voiceover"),
    brand_voice: Optional[str] = Form(None, description="JSON string with brand voice guidelines"),
    scanner_brief: Optional[str] = Form(None, description="JSON string with scanner intelligence data"),
):
    """
    Rewrite ad copy with multiple variants and AI-powered scoring.

    Returns 2 rewrite variants with detailed score breakdown, predicted CTR, and benchmarking.
    """
    try:
        logger.info(f"Starting ad rewrite with mode: {rewrite_mode}")

        # Validate rewrite mode
        if rewrite_mode not in ALL_REWRITE_MODES:
            valid_modes = ", ".join(sorted(ALL_REWRITE_MODES.keys()))
            raise HTTPException(
                status_code=400,
                detail=f"Invalid rewrite_mode. Must be one of: {valid_modes}"
            )

        # Parse JSON inputs
        try:
            original_scores_dict = json.loads(original_scores)
            weaknesses_list = json.loads(weaknesses)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON in scores or weaknesses: {str(e)}"
            )

        if not original_ad or not original_ad.strip():
            raise HTTPException(status_code=400, detail="original_ad is required and cannot be empty")

        # Normalize original scores
        original_scores_dict = _calculate_original_scores(original_scores_dict)

        prepare_vo = prepare_voiceover.lower() == "true"

        # Build brand voice context
        brand_voice_context = ""
        if brand_voice and brand_voice.strip():
            try:
                brand_voice_data = json.loads(brand_voice)
                brand_name = brand_voice_data.get("brand_name", "Unknown Brand")
                tone_attributes = brand_voice_data.get("tone_attributes", [])
                words_to_use = brand_voice_data.get("words_to_use", [])
                words_to_avoid = brand_voice_data.get("words_to_avoid", [])
                brand_guidelines = brand_voice_data.get("brand_guidelines", "")

                tone_lines = "\n".join(f"  - {t}" for t in tone_attributes) if tone_attributes else "  - Not specified"
                use_lines = "\n".join(f"  - {w}" for w in words_to_use) if words_to_use else "  - Not specified"
                avoid_lines = "\n".join(f"  - {w}" for w in words_to_avoid) if words_to_avoid else "  - Not specified"

                brand_voice_context = f"""

BRAND VOICE GUIDELINES:
Brand Name: {brand_name}
Tone Attributes:
{tone_lines}
Words to Use:
{use_lines}
Words to Avoid:
{avoid_lines}
Brand Guidelines:
{brand_guidelines if brand_guidelines else "Not specified"}

IMPORTANT: The rewritten ad MUST match this brand voice. Use the preferred tone and vocabulary."""
                logger.info(f"Brand voice included in rewrite: {brand_name}")
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid brand_voice JSON: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Invalid brand_voice JSON: {str(e)}")

        # Get benchmark context
        benchmark_context = build_benchmark_context(platform, industry)
        benchmarks = get_benchmarks(platform, industry)

        # Parse COMPLETE scanner intelligence for maximum rewrite quality
        scanner_context = ""
        if scanner_brief:
            try:
                sb = json.loads(scanner_brief)
                sections = []

                # ── Business identity ──
                biz_parts = []
                if sb.get("business_name"):
                    biz_parts.append(f"Business: {sb['business_name']}")
                if sb.get("tagline"):
                    biz_parts.append(f"Tagline: \"{sb['tagline']}\"")
                if sb.get("description"):
                    biz_parts.append(f"About: {sb['description'][:200]}")
                if biz_parts:
                    sections.append("BUSINESS:\n" + "\n".join(f"  - {p}" for p in biz_parts))

                # ── Products & features (full details, not just names) ──
                prod_parts = []
                for p in (sb.get("products") or [])[:5]:
                    name = p.get("name", "")
                    desc = p.get("description", "")
                    benefit = p.get("key_benefit", "")
                    line = f"{name}"
                    if desc:
                        line += f" — {desc}"
                    if benefit:
                        line += f" (Key benefit: {benefit})"
                    prod_parts.append(line)
                features = sb.get("all_features") or []
                if prod_parts or features:
                    feat_section = "PRODUCTS & FEATURES:"
                    if prod_parts:
                        feat_section += "\n  Products:\n" + "\n".join(f"    • {p}" for p in prod_parts)
                    if features:
                        feat_section += f"\n  All features: {', '.join(str(f) if isinstance(f, str) else (f.get('name', str(f)) if isinstance(f, dict) else str(f)) for f in features[:15])}"
                    if sb.get("pricing_model"):
                        feat_section += f"\n  Pricing: {sb['pricing_model']}"
                    sections.append(feat_section)

                # ── Target audience (full persona) ──
                persona = (sb.get("target_audience") or {}).get("primary_persona") or {}
                if persona:
                    aud_section = "TARGET AUDIENCE:"
                    if persona.get("description"):
                        aud_section += f"\n  Who: {persona['description']}"
                    if persona.get("demographics"):
                        aud_section += f"\n  Demographics: {persona['demographics']}"
                    if persona.get("pain_points"):
                        aud_section += f"\n  Pain points: {', '.join(_to_str(p) for p in persona['pain_points'])}"
                    if persona.get("desires"):
                        aud_section += f"\n  Desires: {', '.join(_to_str(d) for d in persona['desires'])}"
                    if persona.get("objections"):
                        aud_section += f"\n  Objections: {', '.join(_to_str(o) for o in persona['objections'])}"
                    sections.append(aud_section)

                # ── Brand analysis ──
                ba = sb.get("brand_analysis") or {}
                if ba:
                    brand_section = "BRAND:"
                    if ba.get("brand_voice"):
                        brand_section += f"\n  Voice: {ba['brand_voice']}"
                    if ba.get("tone"):
                        brand_section += f" / Tone: {ba['tone']}"
                    if ba.get("unique_positioning"):
                        brand_section += f"\n  Positioning: {ba['unique_positioning']}"
                    if ba.get("trust_signals"):
                        brand_section += f"\n  Trust signals: {', '.join(_to_str(s) for s in ba['trust_signals'])}"
                    sections.append(brand_section)

                # ── Competitive landscape (competitors, advantages, gaps) ──
                def _to_str(item):
                    """Safely convert any item (str, dict, etc.) to a display string."""
                    if isinstance(item, str):
                        return item
                    if isinstance(item, dict):
                        return item.get("name") or item.get("platform") or item.get("label") or str(item)
                    return str(item)

                comp = sb.get("competitive_landscape") or {}
                if comp:
                    comp_section = "COMPETITIVE LANDSCAPE:"
                    if comp.get("likely_competitors"):
                        comp_section += f"\n  Competitors: {', '.join(_to_str(c) for c in comp['likely_competitors'])}"
                    if comp.get("competitive_advantages"):
                        comp_section += f"\n  Our advantages over them: {', '.join(_to_str(a) for a in comp['competitive_advantages'])}"
                    if comp.get("market_gaps"):
                        comp_section += f"\n  Market gaps to exploit: {', '.join(_to_str(g) for g in comp['market_gaps'])}"
                    sections.append(comp_section)

                # ── Ad strategy ──
                strat = sb.get("ad_strategy") or {}
                if strat:
                    strat_section = "AD STRATEGY:"
                    if strat.get("recommended_funnel_stage"):
                        strat_section += f"\n  Funnel stage: {strat['recommended_funnel_stage']}"
                    if strat.get("emotional_trigger"):
                        strat_section += f"\n  Emotional trigger: {strat['emotional_trigger']}"
                    if strat.get("best_platform"):
                        strat_section += f"\n  Best platform: {strat['best_platform']}"
                    sections.append(strat_section)

                # ── All 4 ad angles (so rewrite can draw from any angle) ──
                angles = sb.get("ad_angles") or []
                if angles:
                    rec = sb.get("recommended_angle") or angles[0]
                    angles_section = f"AD ANGLES ({len(angles)} ranked — recommended: \"{rec.get('angle_name', '')}\"):"
                    for i, a in enumerate(angles):
                        eff = a.get("predicted_effectiveness", 0)
                        angles_section += f"\n  {i+1}. {a.get('angle_name', '')} ({a.get('strategy', '')}) — {eff}% effectiveness"
                        if a.get("hook_line"):
                            angles_section += f"\n     Hook: \"{a['hook_line']}\""
                        if a.get("headline"):
                            angles_section += f"\n     Headline: \"{a['headline']}\""
                        if a.get("cta"):
                            angles_section += f"\n     CTA: \"{a['cta']}\""
                    sections.append(angles_section)

                # ── Funnel intelligence (conversion blockers, retargeting) ──
                funnel = sb.get("funnel_intelligence") or {}
                if funnel:
                    funnel_section = "FUNNEL INTELLIGENCE:"
                    if funnel.get("landing_page_assessment"):
                        funnel_section += f"\n  Landing page: {funnel['landing_page_assessment']}"
                    if funnel.get("conversion_blockers"):
                        funnel_section += f"\n  Conversion blockers: {', '.join(_to_str(b) for b in funnel['conversion_blockers'])}"
                    if funnel.get("retargeting_angle"):
                        funnel_section += f"\n  Retargeting angle: {funnel['retargeting_angle']}"
                    sections.append(funnel_section)

                if sections:
                    scanner_context = "\n\n═══ COMPLETE SCANNER INTELLIGENCE REPORT ═══\n" + "\n\n".join(sections)
                    scanner_context += """

═══ REWRITE DIRECTIVES ═══
Use the scanner intelligence above to make the rewrite SPECIFIC and POWERFUL:
- Reference ACTUAL product names and features — never use generic placeholders
- Address the audience's real pain points and desires identified above
- Leverage competitive advantages and market gaps to differentiate
- Match the brand voice and tone
- Use the strongest hooks and emotional triggers from the ad angles
- Address conversion blockers identified in funnel intelligence
- Position against named competitors where relevant"""
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse scanner_brief: {e}")

        # Build and call prompt
        prompt = _build_rewrite_prompt(
            original_ad=original_ad,
            platform=platform,
            industry=industry,
            audience_country=audience_country,
            original_scores_dict=original_scores_dict,
            weaknesses_list=weaknesses_list,
            rewrite_mode=rewrite_mode,
            target_age=target_age,
            target_tone=target_tone,
            brand_voice_context=brand_voice_context,
            benchmark_context=benchmark_context,
            scanner_context=scanner_context
        )

        gpt_response = await _call_gpt4o(prompt)
        logger.info("GPT-4o rewrite completed")

        # Extract and parse JSON response
        parsed_data = _extract_json_from_response(gpt_response)

        if "variants" not in parsed_data or not parsed_data["variants"]:
            raise HTTPException(
                status_code=500,
                detail="AI response did not include variants"
            )

        # Process variants
        processed_variants = []
        for variant in parsed_data["variants"]:
            # Normalize and validate scores
            if "scores" not in variant:
                variant["scores"] = {}

            variant["scores"] = _normalize_scores(variant["scores"])

            # Ensure all required score fields exist
            required_scores = [
                "overall_score", "emotion_score", "clarity_score",
                "cta_strength", "platform_fit", "pain_point_score"
            ]
            for score_key in required_scores:
                if score_key not in variant["scores"]:
                    variant["scores"][score_key] = 50

            # Calculate percentile
            overall = variant["scores"].get("overall_score", 50)
            percentile = calculate_percentile(overall, platform, industry)

            # Validate predicted_ctr
            if "predicted_ctr" not in variant:
                variant["predicted_ctr"] = benchmarks.get("ctr", 1.0)
            else:
                try:
                    variant["predicted_ctr"] = float(variant["predicted_ctr"])
                except (ValueError, TypeError):
                    variant["predicted_ctr"] = benchmarks.get("ctr", 1.0)

            # Build processed variant
            processed_variant = {
                "rewritten_ad": variant.get("rewritten_ad", ""),
                "changes_summary": variant.get("changes_summary", []),
                "why_it_works": variant.get("why_it_works", ""),
                "scores": variant["scores"],
                "predicted_ctr": variant["predicted_ctr"],
                "predicted_percentile": percentile
            }

            processed_variants.append(processed_variant)

        # Build response
        response_data = {
            "variants": processed_variants,
            "original_scores": original_scores_dict,
            "rewrite_mode": rewrite_mode,
            "platform": platform,
            "industry": industry,
            "benchmarks": {
                "avg_ctr": benchmarks.get("ctr"),
                "avg_score": benchmarks.get("avg_score")
            },
            "voiceover": None
        }

        if prepare_vo and processed_variants:
            # Use first variant for voiceover
            response_data["voiceover"] = _prepare_voiceover_script(
                processed_variants[0]["rewritten_ad"],
                voice_style
            )

        logger.info("Ad rewrite completed successfully")
        return {"success": True, "data": response_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rewriting ad: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error rewriting ad: {str(e)}")
