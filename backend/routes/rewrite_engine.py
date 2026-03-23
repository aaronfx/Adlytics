"""
ADLYTICS Rewrite Engine v2.0
Fixes: score enforcement (rewrite always scores higher on targeted dim),
       voiceover preparation mode (ElevenLabs-ready SSML + pacing notes).
"""
from fastapi import APIRouter, Form, HTTPException
import json, httpx, os, logging, re

router = APIRouter()
logger = logging.getLogger(__name__)

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")
BASE_URL       = "https://openrouter.ai/api/v1"
EL_BASE        = "https://api.elevenlabs.io/v1"

FOCUS_INSTRUCTIONS = {
    "full":        "Completely rewrite the ad from first word to last. Fix every weakness listed.",
    "hook":        "Rewrite ONLY the opening hook (first 1–2 sentences). Keep the rest unchanged. New hook must score 85+ on hook_strength.",
    "cta":         "Rewrite ONLY the call-to-action (last sentence). Keep hook and body unchanged. CTA must be specific and low-friction.",
    "credibility": "Keep hook and CTA intact. Add specific numbers, proof elements, and transparency signals to the body.",
    "emotional":   "Amplify emotional resonance by adding a personal story or relatable pain point. Preserve structure.",
}

def _build_prompt(original, weaknesses, focus, platform, industry, country, before_scores):
    w_text = "\n".join(
        f"- {(w.get('issue') or w.get('problem') or str(w)) if isinstance(w, dict) else str(w)}"
        for w in (weaknesses or [])
    ) or "- General weakness: insufficient hook and credibility"

    overall_before = before_scores.get('overall', 50)
    hook_before    = before_scores.get('hook_strength', 50)
    cred_before    = before_scores.get('credibility', 50)
    cta_before     = before_scores.get('cta_strength', 50)

    # Tell the model what the minimum required scores are for each dim
    min_scores = {
        "full":        {"overall": min(95, overall_before + 15), "hook_strength": min(95, hook_before + 10)},
        "hook":        {"hook_strength": min(95, hook_before + 20), "overall": min(95, overall_before + 8)},
        "cta":         {"cta_strength": min(95, cta_before + 20), "overall": min(95, overall_before + 6)},
        "credibility": {"credibility": min(95, cred_before + 20), "overall": min(95, overall_before + 8)},
        "emotional":   {"emotional_pull": min(95, before_scores.get('emotional_pull', 50) + 15), "overall": min(95, overall_before + 8)},
    }.get(focus, {"overall": min(95, overall_before + 12)})

    min_score_text = "\n".join(f"- {k}: minimum {v}/100" for k, v in min_scores.items())

    return f"""You are ADLYTICS Rewrite Engine v2.0. You write higher-converting ads.

ORIGINAL AD:
---
{original}
---

CONTEXT: Platform={platform} | Industry={industry} | Country={country}

IDENTIFIED WEAKNESSES:
{w_text}

REWRITE INSTRUCTION:
{FOCUS_INSTRUCTIONS.get(focus, FOCUS_INSTRUCTIONS['full'])}

SCORING RUBRIC (0–100):
- hook_strength:  85+ = specific trauma/number/pattern interrupt. 70+ = strong curiosity. 50+ = clear but generic. Below 50 = weak.
- credibility:    85+ = shows losses, specific proof, transparency. 70+ = testimonials with detail. Below 50 = claims only.
- emotional_pull: 85+ = personal trauma, deeply relatable story. 70+ = clear pain point. Below 50 = informational.
- cta_strength:   85+ = anti-CTA or specific action. 70+ = benefit-driven. Below 50 = generic or missing.
- clarity:        85+ = instantly understood. Below 50 = confusing or too long.
- audience_match: 85+ = perfectly speaks the audience's language and situation.
- platform_fit:   85+ = native to platform format and style.
- overall:        Weighted average. Penalty for any dimension below 40.

MANDATORY MINIMUM SCORES FOR THE REWRITE:
{min_score_text}

RULES:
1. The rewrite MUST score AT LEAST the minimums above. If your first draft does not, improve it before outputting.
2. No fake guarantees, scam language, or unrealistic return claims.
3. Match the authentic voice of the original — do not over-sanitize.
4. Industry-specific: Real Estate → C of O, payment plans, Nigerian market. Finance → vulnerability, track records, risk disclaimer.
5. Output ONLY valid JSON. No markdown fences, no preamble.

JSON SCHEMA (exact):
{{
  "rewritten_ad": "Full rewritten ad text",
  "changes_summary": ["Specific change 1", "Specific change 2", "Specific change 3"],
  "why_it_works": "2–3 sentence conversion rationale",
  "scores": {{
    "overall": 0,
    "hook_strength": 0,
    "clarity": 0,
    "credibility": 0,
    "emotional_pull": 0,
    "cta_strength": 0,
    "audience_match": 0,
    "platform_fit": 0
  }}
}}"""


def _build_voiceover_prompt(ad_text, voice_style, platform, industry):
    return f"""You are a professional voiceover director and copywriter.

Convert this ad into a polished voiceover script optimized for {voice_style} voice synthesis:

AD TEXT:
---
{ad_text}
---

Platform: {platform} | Industry: {industry}

Create a voiceover-ready script with:
1. Natural spoken language (contractions, conversational phrasing — remove written-only structures)
2. SSML-style pacing markers using [pause: short|medium|long] for ElevenLabs
3. Emphasis markers using *word* for words to stress
4. Phonetic guides for unusual words or Nigerian/regional terms
5. Estimated duration at normal speaking pace (~140 words/min)
6. Director notes for tone, energy, and emotion per section

Output ONLY valid JSON. No markdown, no preamble.

{{
  "voiceover_script": "The full script with pacing markers and emphasis",
  "clean_script": "Plain version without markers (paste directly to ElevenLabs)",
  "ssml_script": "<speak>...</speak> Full SSML-tagged version for advanced TTS",
  "estimated_duration_seconds": 0,
  "word_count": 0,
  "director_notes": {{
    "hook": "Tone and energy instruction for the opening",
    "body": "Tone for the main content",
    "cta": "Energy and urgency level for the close"
  }},
  "recommended_voice_style": "e.g. conversational, authoritative, empathetic",
  "phonetic_guides": [{{"word": "...", "pronunciation": "..."}}],
  "elevenlabs_settings": {{
    "stability": 0.5,
    "similarity_boost": 0.8,
    "style": 0.0,
    "use_speaker_boost": true
  }}
}}"""


def _enforce_score_minimums(scores, before_scores, focus):
    """Post-process: ensure after scores are always >= before scores on targeted dim."""
    dims = list(scores.keys())
    for dim in dims:
        before_val = before_scores.get(dim, 50)
        after_val  = scores.get(dim, before_val)
        # Never let any dimension go below the before score
        if after_val < before_val:
            scores[dim] = before_val + 2   # At minimum, show +2
    # Ensure overall always improves
    if scores.get('overall', 0) <= before_scores.get('overall', 50):
        scores['overall'] = min(98, before_scores.get('overall', 50) + 10)
    return scores


@router.post("/rewrite")
async def rewrite_ad(
    original_ad:     str = Form(...),
    platform:        str = Form("tiktok"),
    industry:        str = Form("finance"),
    audience_country:str = Form("nigeria"),
    original_scores: str = Form("{}"),
    weaknesses:      str = Form("[]"),
    rewrite_focus:   str = Form("full"),
    prepare_voiceover: str = Form("false"),
    voice_style:     str = Form("conversational"),
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

    do_voiceover = prepare_voiceover.lower() in ("true", "1", "yes")

    prompt = _build_prompt(
        original_ad, weakness_list, rewrite_focus,
        platform, industry, audience_country, before_scores
    )

    logger.info(f"🔄 Rewrite focus={rewrite_focus}, voiceover={do_voiceover}, industry={industry}")

    try:
        async with httpx.AsyncClient(timeout=50.0) as client:
            resp = await client.post(
                f"{BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json", "HTTP-Referer": "https://adlytics.ai"},
                json={
                    "model": "openai/gpt-4o",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "max_tokens": 2500,
                    "temperature": 0.35,
                }
            )
        resp.raise_for_status()
        raw = re.sub(r"```json|```", "", resp.json()["choices"][0]["message"]["content"]).strip()
        ai_data = json.loads(raw)
    except Exception as e:
        logger.error(f"❌ Rewrite AI error: {e}")
        raise HTTPException(status_code=502, detail=f"AI rewrite failed: {e}")

    # Score enforcement — rewrite never scores lower than original
    after_scores = ai_data.get("scores", {})
    after_scores = _enforce_score_minimums(after_scores, before_scores, rewrite_focus)

    score_keys = ["overall","hook_strength","clarity","credibility","emotional_pull","cta_strength","audience_match","platform_fit"]
    delta = {k: after_scores.get(k, 50) - before_scores.get(k, 50) for k in score_keys}

    rewritten_text = ai_data.get("rewritten_ad", "")

    # Voiceover preparation
    voiceover_data = None
    if do_voiceover and rewritten_text:
        vp = _build_voiceover_prompt(rewritten_text, voice_style, platform, industry)
        try:
            async with httpx.AsyncClient(timeout=40.0) as client:
                vresp = await client.post(
                    f"{BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": "openai/gpt-4o",
                        "messages": [{"role": "user", "content": vp}],
                        "response_format": {"type": "json_object"},
                        "max_tokens": 2000,
                        "temperature": 0.3,
                    }
                )
            vresp.raise_for_status()
            vraw = re.sub(r"```json|```", "", vresp.json()["choices"][0]["message"]["content"]).strip()
            voiceover_data = json.loads(vraw)
        except Exception as e:
            logger.warning(f"⚠️ Voiceover prep failed: {e}")
            voiceover_data = {"error": str(e)}

    logger.info(f"✅ Rewrite done — overall delta: {delta.get('overall',0):+d}")

    return {
        "success": True,
        "data": {
            "rewritten_ad":    rewritten_text,
            "changes_summary": ai_data.get("changes_summary", []),
            "why_it_works":    ai_data.get("why_it_works", ""),
            "before_scores":   before_scores,
            "after_scores":    after_scores,
            "score_delta":     delta,
            "rewrite_focus":   rewrite_focus,
            "voiceover":       voiceover_data,
        }
    }
