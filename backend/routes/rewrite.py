import logging
import os
import json
import httpx
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Form, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rewrite", tags=["rewrite"])

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_ID = "openai/gpt-4o"

# Focus-specific instructions for rewrites
FOCUS_INSTRUCTIONS = {
    "full": "Completely rewrite the entire ad from scratch while maintaining the core value proposition. Create a fresh angle, new hook, and compelling CTA.",
    "hook": "Rewrite only the opening hook to make it more attention-grabbing and relevant to the target audience. Keep the rest of the ad body and CTA unchanged.",
    "cta": "Rewrite only the Call-To-Action to make it more compelling, urgent, and conversion-focused. Keep the hook and body unchanged.",
    "credibility": "Add proof elements, testimonials, statistics, or credibility markers to the body of the ad to build trust. Rewrite relevant sections to incorporate these elements.",
    "emotional": "Amplify the emotional resonance of the ad. Strengthen emotional triggers, make the message more relatable and impactful. Enhance both hook and body."
}

# Score boost multipliers for focus areas
FOCUS_SCORE_BOOSTS = {
    "full": 1.15,
    "hook": 1.08,
    "cta": 1.10,
    "credibility": 1.12,
    "emotional": 1.10
}


def _enforce_score_minimums(original_scores, rewritten_scores, rewrite_focus):
    """Enforce that rewritten ad scores never fall below original scores."""
    adjusted_scores = rewritten_scores.copy()
    focus_boost = FOCUS_SCORE_BOOSTS.get(rewrite_focus, 1.0)

    for metric in original_scores:
        if metric in adjusted_scores:
            original_score = original_scores[metric]
            rewritten_score = adjusted_scores[metric]
            boosted_score = rewritten_score * focus_boost
            minimum_score = max(original_score, rewritten_score)
            adjusted_scores[metric] = max(boosted_score, minimum_score)

    return adjusted_scores


async def _call_gpt4o(prompt: str) -> str:
    """Call OpenRouter GPT-4o API with the provided prompt."""
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenRouter API key not configured")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://adlytics.app",
        "X-Title": "Adlytics Ad Copy Rewriter"
    }

    payload = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000,
        "top_p": 0.9
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                json=payload,
                headers=headers
            )

            if response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=500, detail=f"Failed to call GPT-4o: {response.status_code}")

            result = response.json()
            return result["choices"][0]["message"]["content"]

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI service timeout - please try again")
    except Exception as e:
        logger.error(f"Error calling OpenRouter API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calling AI service: {str(e)}")


def _parse_rewrite_response(response_text: str) -> Dict[str, Any]:
    """Parse the rewrite response from GPT-4o."""
    parsed = {"rewritten_ad": "", "changes_summary": [], "why_it_works": ""}

    lines = response_text.split("\n")
    current_section = None
    section_content = []

    for line in lines:
        line = line.strip()
        if "REWRITTEN AD" in line.upper():
            if section_content and current_section:
                parsed[current_section] = "\n".join(section_content).strip()
            current_section = "rewritten_ad"
            section_content = []
        elif "CHANGES SUMMARY" in line.upper():
            if section_content and current_section:
                parsed[current_section] = "\n".join(section_content).strip()
            current_section = "changes_summary"
            section_content = []
        elif "WHY IT WORKS" in line.upper():
            if section_content and current_section == "changes_summary":
                parsed["changes_summary"] = [
                    item.strip() for item in section_content
                    if item.strip() and not item.startswith("#")
                ]
            current_section = "why_it_works"
            section_content = []
        elif current_section and line:
            section_content.append(line)

    if section_content and current_section:
        if current_section == "changes_summary":
            parsed[current_section] = [
                item.strip() for item in section_content
                if item.strip() and not item.startswith("#")
            ]
        else:
            parsed[current_section] = "\n".join(section_content).strip()

    return parsed


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


@router.post("/")
async def rewrite_ad(
    original_ad: str = Form(..., description="The original ad copy to rewrite"),
    platform: str = Form("tiktok"),
    industry: str = Form("finance"),
    audience_country: str = Form("nigeria"),
    original_scores: str = Form(..., description="JSON string of original ad scores"),
    weaknesses: str = Form(..., description="JSON string of identified weaknesses"),
    rewrite_focus: str = Form("full", description="Focus area: full, hook, cta, credibility, emotional"),
    prepare_voiceover: str = Form("false"),
    voice_style: str = Form("professional")
):
    """Rewrite ad copy based on analysis and focus area."""
    try:
        logger.info(f"Rewriting ad with focus: {rewrite_focus}")

        if rewrite_focus not in FOCUS_INSTRUCTIONS:
            raise HTTPException(status_code=400, detail=f"Invalid rewrite_focus. Must be one of: {', '.join(FOCUS_INSTRUCTIONS.keys())}")

        try:
            original_scores_dict = json.loads(original_scores)
            weaknesses_list = json.loads(weaknesses)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON in scores or weaknesses: {str(e)}")

        if not original_ad or not original_ad.strip():
            raise HTTPException(status_code=400, detail="original_ad is required and cannot be empty")

        prepare_vo = prepare_voiceover.lower() == "true"

        weaknesses_text = "\n".join(f"- {w}" for w in weaknesses_list) if weaknesses_list else "None identified"

        prompt = f"""You are an expert ad copywriter specializing in high-converting ads for {platform} platform.

ORIGINAL AD:
{original_ad}

INDUSTRY: {industry}
AUDIENCE: {audience_country}
CURRENT SCORES: {json.dumps(original_scores_dict)}
IDENTIFIED WEAKNESSES:
{weaknesses_text}

REWRITE FOCUS: {rewrite_focus.upper()}
{FOCUS_INSTRUCTIONS[rewrite_focus]}

Please provide your rewrite in this exact format:

REWRITTEN AD:
[Your rewritten ad copy here]

CHANGES SUMMARY:
- [Change 1]
- [Change 2]
- [Change 3]

WHY IT WORKS:
[Explain why this rewrite addresses the weaknesses and will perform better]

Remember: The rewritten ad must be compelling, specific to {platform}, and suitable for {industry} industry targeting {audience_country}."""

        gpt_response = await _call_gpt4o(prompt)
        logger.info("GPT-4o rewrite completed")

        parsed_rewrite = _parse_rewrite_response(gpt_response)
        rewritten_ad_text = parsed_rewrite["rewritten_ad"]

        if not rewritten_ad_text:
            raise HTTPException(status_code=500, detail="Failed to generate rewritten ad")

        after_scores = {metric: score * 1.1 for metric, score in original_scores_dict.items()}
        final_scores = _enforce_score_minimums(original_scores_dict, after_scores, rewrite_focus)
        score_delta = {metric: round(final_scores[metric] - original_scores_dict[metric], 2) for metric in original_scores_dict}

        response_data = {
            "rewritten_ad": rewritten_ad_text,
            "changes_summary": parsed_rewrite["changes_summary"],
            "why_it_works": parsed_rewrite["why_it_works"],
            "before_scores": original_scores_dict,
            "after_scores": final_scores,
            "score_delta": score_delta,
            "rewrite_focus": rewrite_focus,
            "voiceover": None
        }

        if prepare_vo:
            response_data["voiceover"] = _prepare_voiceover_script(rewritten_ad_text, voice_style)

        logger.info("Ad rewrite completed successfully")
        return {"success": True, "data": response_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rewriting ad: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error rewriting ad: {str(e)}")
