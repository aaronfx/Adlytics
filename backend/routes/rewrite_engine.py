"""
ADLYTICS Rewrite Engine — POST /api/rewrite
Rewrites an ad using AI, returns before/after scores + delta.
"""
from fastapi import APIRouter, Form, HTTPException
import json, httpx, os, logging, re

router = APIRouter()
logger = logging.getLogger(__name__)

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

FOCUS_INSTRUCTIONS = {
    "full": (
        "Completely rewrite the ad from first word to last, fixing every weakness listed. "
        "Keep the same industry, platform, and audience context."
    ),
    "hook": (
        "Rewrite ONLY the opening hook (first 1–2 sentences). "
        "Leave the rest of the ad body and CTA unchanged. "
        "The new hook must score 85+ on hook_strength based on the scoring rubric."
    ),
    "cta": (
        "Rewrite ONLY the call-to-action (last sentence or phrase). "
        "Leave hook and body unchanged. "
        "The new CTA must be specific, low-friction, and action-driving."
    ),
    "credibility": (
        "Keep the hook and CTA. Strengthen the body by adding: "
        "specific numbers, proof elements, transparency, and trust signals. "
        "Do not make claims that cannot be substantiated."
    ),
    "emotional": (
        "Keep structure intact. Amplify the emotional resonance by adding a personal story, "
        "specific pain point, or relatable moment. Do NOT add scam-pattern language."
    ),
}

SCORE_RUBRIC = """
SCORING RUBRIC (0-100 for each dimension):

hook_strength: Does it stop the scroll in 0-3 seconds?
- 85-100: Specific trauma/number/pattern interrupt ("I lost ₦120K", "Stop doing X")
- 70-84:  Strong curiosity or clear benefit
- 50-69:  Clear but generic
- 30-49:  Weak, boring, feature-focused
- 0-29:   No hook, filler, scam language

credibility: Trust level of the content
- 85-100: Shows losses/vulnerability, specific proof, transparency
- 70-84:  Social proof, testimonials with detail
- 50-69:  Claims only, no proof
- 30-49:  Hype language
- 0-29:   Scam markers, guarantees, unrealistic returns

emotional_pull: Emotional connection
- 85-100: Personal trauma, deeply relatable story
- 70-84:  Clear pain point addressed
- 50-69:  Mentions audience but generic
- 0-49:   Informational, no emotion

cta_strength: Quality of call-to-action
- 85-100: Anti-CTA ("Don't join yet"), specific next step, urgent
- 70-84:  Clear benefit-driven action
- 50-69:  Generic "click here" / "join now"
- 0-49:   Missing, vague, or scam CTA

clarity: Comprehension and flow
credibility, audience_match, platform_fit: 0-100 as above
"""


def _build_rewrite_prompt(
    original: str, weaknesses: list, focus: str,
    platform: str, industry: str, country: str
) -> str:
    weakness_text = "\n".join(
        f"- {w.get('issue', w) if isinstance(w, dict) else w}"
        for w in (weaknesses or [])
    ) or "- No specific weaknesses provided"

    return f"""You are ADLYTICS Rewrite Engine v1.0. Your job is to write a better-performing ad.

ORIGINAL AD:
---
{original}
---

CONTEXT:
- Platform: {platform}
- Industry: {industry}
- Target Country: {country}

IDENTIFIED WEAKNESSES:
{weakness_text}

REWRITE INSTRUCTION:
{FOCUS_INSTRUCTIONS.get(focus, FOCUS_INSTRUCTIONS['full'])}

SCORING RUBRIC:
{SCORE_RUBRIC}

RULES:
1. The rewrite must score AT LEAST 15 points higher on overall than the original's weakest dimension.
2. No fake guarantees, no scam language, no unrealistic returns.
3. Match the voice and language level of the original — do not over-polish.
4. If the industry is Real Estate: reference Nigerian property market, title documents (C of O), or payment plans.
5. If Finance/Forex: vulnerability framing, track records, risk disclaimers.
6. Output ONLY valid JSON. No markdown. No preamble.

OUTPUT JSON (exact schema):
{{
  "rewritten_ad": "The full rewritten ad text here",
  "changes_summary": ["Change 1 in plain English", "Change 2", "Change 3"],
  "scores": {{
    "overall": 0,
    "hook_strength": 0,
    "clarity": 0,
    "credibility": 0,
    "emotional_pull": 0,
    "cta_strength": 0,
    "audience_match": 0,
    "platform_fit": 0
  }},
  "why_it_works": "2-3 sentence explanation of why the rewritten version converts better"
}}"""


@router.post("/rewrite")
async def rewrite_ad(
    original_ad: str = Form(...),
    platform: str = Form("tiktok"),
    industry: str = Form("finance"),
    audience_country: str = Form("nigeria"),
    original_scores: str = Form("{}"),
    weaknesses: str = Form("[]"),
    rewrite_focus: str = Form("full"),
):
    if not original_ad.strip():
        raise HTTPException(status_code=400, detail="No ad content provided")

    if not OPENROUTER_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    try:
        before_scores = json.loads(original_scores)
    except Exception:
        before_scores = {}

    try:
        weakness_list = json.loads(weaknesses)
    except Exception:
        weakness_list = []

    prompt = _build_rewrite_prompt(
        original_ad, weakness_list, rewrite_focus,
        platform, industry, audience_country
    )

    logger.info(f"🔄 Rewrite request — focus={rewrite_focus}, industry={industry}")

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://adlytics.ai",
                },
                json={
                    "model": "openai/gpt-4o",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "max_tokens": 2000,
                    "temperature": 0.4,
                },
            )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        # Strip markdown fences if model ignores format instruction
        raw = re.sub(r"```json|```", "", raw).strip()
        ai_data = json.loads(raw)
    except Exception as e:
        logger.error(f"❌ Rewrite AI error: {e}")
        raise HTTPException(status_code=502, detail=f"AI rewrite failed: {e}")

    after_scores = ai_data.get("scores", {})

    # Compute delta for every score dimension
    score_keys = ["overall", "hook_strength", "clarity", "credibility",
                  "emotional_pull", "cta_strength", "audience_match", "platform_fit"]
    delta = {}
    for k in score_keys:
        before_val = before_scores.get(k, 50)
        after_val  = after_scores.get(k, 50)
        delta[k] = after_val - before_val

    logger.info(f"✅ Rewrite complete — overall delta: {delta.get('overall', 0):+d}")

    return {
        "success": True,
        "data": {
            "rewritten_ad":    ai_data.get("rewritten_ad", ""),
            "changes_summary": ai_data.get("changes_summary", []),
            "why_it_works":    ai_data.get("why_it_works", ""),
            "before_scores":   before_scores,
            "after_scores":    after_scores,
            "score_delta":     delta,
            "rewrite_focus":   rewrite_focus,
        },
    }
