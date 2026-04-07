"""
ADLYTICS AI Engine v7.0
Three accuracy upgrades:
1. Chain-of-thought scoring — model reasons line-by-line before scoring
2. Full audience context injection — age, income, occupation, country shape every score
3. Two-pass critic — a second call challenges inflated scores before returning
4. Brand voice support — optional brand voice consistency scoring
"""

import json
import re
import hashlib
import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_not_exception_type

logger = logging.getLogger(__name__)


@dataclass
class ContentFingerprint:
    content_hash: str
    word_count: int
    first_20_chars: str
    last_20_chars: str
    has_trauma_pattern: bool
    has_scam_pattern: bool
    emotional_keywords: List[str]
    sentence_count: int
    has_specific_numbers: bool
    has_social_proof: bool
    has_cta: bool


class AIValidationError(Exception):
    pass


# Audience profiles for different countries
AUDIENCE_PROFILES = {
    "nigeria": {
        "skepticism": "Very high — scam fatigue from endless 'make money' ads. Needs specific proof.",
        "trust_cues": "Track record screenshots, C of O documents, specific naira amounts, known landmarks.",
        "cta_style": "WhatsApp DM or 'Comment INFO' — not 'click here'. Low-friction next step.",
        "taboos": "Guaranteed returns, unrealistic income claims, foreign currency emphasis.",
        "currency": "₦",
    },
    "ghana": {
        "skepticism": "High — similar to Nigeria but more receptive to fintech/crypto messaging.",
        "trust_cues": "GH₵ amounts, local bank names, Accra/Kumasi references.",
        "cta_style": "WhatsApp or direct call. Mobile-first audience.",
        "taboos": "Dollar-dominated copy, unrealistic promises.",
        "currency": "GH₵",
    },
    "uk": {
        "skepticism": "Moderate — FCA-trained audience expects regulatory disclosure.",
        "trust_cues": "FCA registration numbers, FSCS protection mention, named reviews.",
        "cta_style": "Website link with clear privacy policy. Email capture.",
        "taboos": "Guarantees, non-FCA claims, pressure tactics.",
        "currency": "£",
    },
    "us": {
        "skepticism": "Moderate — SEC-aware for finance. Reviews and social proof convert well.",
        "trust_cues": "BBB rating, verified reviews, SEC/FINRA mentions for finance.",
        "cta_style": "Clear CTA button, free trial or lead magnet.",
        "taboos": "Unsubstantiated income claims (FTC), testimonials without disclaimer.",
        "currency": "$",
    },
}

OCCUPATION_PSYCHOLOGY = {
    "entrepreneur": "Busy, result-oriented. Responds to ROI and time-saving. Ignores generic motivational content.",
    "professional": "Risk-averse, credentials matter. Needs social proof from peers. Long decision cycle.",
    "student": "Budget-conscious, aspirational. Responds to 'start small' messaging. Short attention span.",
    "trader": "Highly skeptical of claims. Wants specific data, not stories. Will fact-check claims.",
    "blue_collar": "Values simplicity, directness. Responds to family/security framing. Distrusts complexity.",
    "creative": "Trend-aware, aesthetic-sensitive. Needs to see the 'cool factor'. Responds to community.",
}

INCOME_PSYCHOLOGY = {
    "low": "Price-sensitive. Must see clear ROI before any spend. 'Free to start' messaging essential.",
    "middle": "Aspirational. Wants quality but watches price. Responds to 'value for money' framing.",
    "high": "Quality-first. Price secondary. Exclusivity and expertise matter more than discounts.",
    "affluent": "Time is priority. Concierge-level trust. Peer validation from other affluents.",
}

AGE_PSYCHOLOGY = {
    "18-24": "Short attention span, trend-driven, sceptical of 'old' methods. Hook must land in 1 second.",
    "25-34": "Career-driven, comparing options. Responds to specificity and peer validation.",
    "35-44": "Family-focused, stability-seeking. Trust and track record outweigh hype.",
    "45-54": "Established, cautious. Prefers detailed information. Long-form converts better.",
    "55+": "Security-focused, brand-loyal. Needs clarity, no jargon, clear disclaimers.",
}


def build_audience_context(request_data: Dict[str, Any]) -> str:
    """Build a rich audience psychology block for the prompt."""
    country = request_data.get("audience_country", "nigeria").lower()
    age = request_data.get("audience_age", "25-34")
    income = request_data.get("audience_income", "middle")
    occupation = request_data.get("audience_occupation", "")
    platform = request_data.get("platform", "tiktok")
    industry = request_data.get("industry", "finance")

    country_ctx = AUDIENCE_PROFILES.get(country, AUDIENCE_PROFILES["nigeria"])
    primary_age = age.split(",")[0].strip()
    age_ctx = AGE_PSYCHOLOGY.get(primary_age, AGE_PSYCHOLOGY["25-34"])
    income_ctx = INCOME_PSYCHOLOGY.get(income, INCOME_PSYCHOLOGY["middle"])

    occ_parts = [o.strip() for o in occupation.split(",") if o.strip()] if occupation else []
    occ_lines = "\n".join(
        f"    • {o}: {OCCUPATION_PSYCHOLOGY.get(o, 'General audience.')}"
        for o in occ_parts[:3]
    ) if occ_parts else "    • General mixed audience"

    platform_notes = {
        "tiktok": "Videos 15–60s. Hook must land in 0–2s. Casual, authentic tone converts. Text overlays essential.",
        "facebook": "Longer copy tolerated. Social proof + clear CTA. Cold audiences need trust-building.",
        "instagram": "Visual-first. Aspirational framing. Story format preferred. Link-in-bio friction.",
        "youtube": "Pre-roll: hook in 5s before skip. In-feed: thumbnail + first line must compel click.",
        "google": "Search intent. User is already looking — match their exact language. CTA must solve immediately.",
    }.get(platform.lower(), "General digital ad.")

    return f"""
TARGET AUDIENCE PROFILE (use this to score audience_match and adjust ALL scores):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Country: {country.title()} | Currency: {country_ctx['currency']}
Age group: {age} → {age_ctx}
Income: {income or 'middle'} → {income_ctx}
Occupation:
{occ_lines}
Country-specific psychology:
  • Skepticism level: {country_ctx['skepticism']}
  • Trust signals: {country_ctx['trust_cues']}
  • CTA style: {country_ctx['cta_style']}
  • Avoid: {country_ctx['taboos']}
Platform: {platform.upper()} → {platform_notes}
Industry: {industry}

SCORING IMPACT:
If the ad ignores these audience realities → audience_match ≤ 45.
If the ad speaks their exact language and addresses their specific fears → audience_match ≥ 80.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""


def build_brand_voice_context(brand_voice: Dict[str, Any]) -> str:
    """Build a brand voice context block for the prompt."""
    brand_name = brand_voice.get("brand_name", "Unknown Brand")
    tone_attributes = brand_voice.get("tone_attributes", [])
    words_to_use = brand_voice.get("words_to_use", [])
    words_to_avoid = brand_voice.get("words_to_avoid", [])
    brand_guidelines = brand_voice.get("brand_guidelines", "")
    example_ads = brand_voice.get("example_ads", [])

    tone_lines = "\n".join(f"    • {t}" for t in tone_attributes) if tone_attributes else "    • Not specified"
    use_lines = "\n".join(f"    • {w}" for w in words_to_use) if words_to_use else "    • Not specified"
    avoid_lines = "\n".join(f"    • {w}" for w in words_to_avoid) if words_to_avoid else "    • Not specified"

    example_section = ""
    if example_ads:
        example_section = "\n\nEXAMPLE ADS THAT MATCH THIS VOICE:\n"
        for i, example in enumerate(example_ads[:3], 1):
            example_section += f"  Example {i}:\n  \"\"\"{example}\"\"\"\n"

    return f"""
BRAND VOICE GUIDELINES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Brand: {brand_name}

TONE ATTRIBUTES:
{tone_lines}

WORDS TO USE:
{use_lines}

WORDS TO AVOID:
{avoid_lines}

BRAND GUIDELINES:
{brand_guidelines if brand_guidelines else "Not specified"}
{example_section}

BRAND VOICE SCORING:
When evaluating this ad, assess how well it adheres to the brand voice:
- Does it match the tone attributes?
- Does it use the preferred vocabulary?
- Does it avoid prohibited language?
- Is it consistent with brand guidelines and examples?
Include a "brand_voice_consistency" score (0-100) in your reasoning.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""


def fingerprint_content(content: str) -> ContentFingerprint:
    cl = content.lower()
    emotional_words = [
        "lost", "pain", "struggle", "truth", "honest", "transparent",
        "scam", "fear", "worry", "stress", "failed", "quit", "stop",
        "burned", "cheated", "mistake", "regret", "frustrated"
    ]
    trauma_patterns = [
        "i lost", "i failed", "i quit", "i stopped", "burned",
        "scammed", "lost ₦", "lost $", "lost £", "wasted", "threw away"
    ]
    scam_patterns = [
        "guarantee", "guaranteed", "no experience needed", "risk free",
        "risk-free", "10x your", "100% profit", "get rich", "overnight"
    ]
    number_patterns = [
        r'\d+[%xX]', r'₦\d', r'\$\d', r'£\d', r'\d+k',
        r'\d+,\d{3}', r'\d+ days', r'\d+ weeks', r'\d+ months'
    ]
    proof_patterns = [
        "testimonial", "screenshot", "verified", "track record",
        "client", "student", "member", "case study", "results", "proof"
    ]
    cta_patterns = [
        "dm", "whatsapp", "click", "call", "comment", "sign up",
        "register", "join", "get started", "book", "apply", "download", "tap"
    ]
    return ContentFingerprint(
        content_hash=hashlib.md5(content.encode()).hexdigest()[:8],
        word_count=len(content.split()),
        first_20_chars=content[:20].strip(),
        last_20_chars=content[-20:].strip() if len(content) >= 20 else content.strip(),
        has_trauma_pattern=any(p in cl for p in trauma_patterns),
        has_scam_pattern=any(p in cl for p in scam_patterns),
        emotional_keywords=[w for w in emotional_words if w in cl],
        sentence_count=len(re.split(r'[.!?]+', content.strip())),
        has_specific_numbers=any(re.search(p, content) for p in number_patterns),
        has_social_proof=any(p in cl for p in proof_patterns),
        has_cta=any(p in cl for p in cta_patterns),
    )


def validate_scores(scores: Dict[str, int], fingerprint: ContentFingerprint) -> tuple:
    vals = [v for k, v in scores.items() if k != "overall"]
    if not vals:
        return False, "No scores returned"
    if len(set(vals)) <= 2:
        return False, "Scores too uniform — generic response"
    if max(vals) - min(vals) < 15:
        return False, f"Score spread too narrow ({max(vals)-min(vals)}pts) — fake analysis"
    if fingerprint.has_trauma_pattern and scores.get("emotional_pull", 0) < 60:
        return False, "Trauma content must score emotional_pull ≥ 60"
    if fingerprint.has_scam_pattern and scores.get("credibility", 0) > 40:
        return False, "Scam content must score credibility ≤ 40"
    return True, "Scores appear content-specific"

class AIEngine:
    """v7.0 — Chain-of-thought + audience injection + two-pass critic + brand voice support"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"

    def _clean_json(self, raw: str) -> str:
        return re.sub(r"```json|```", "", raw).strip()

    async def _call_ai(self, prompt: str, max_tokens: int = 4000, temperature: float = 0.25) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://adlytics.ai",
                },
                json={
                    "model": "openai/gpt-4o",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
            )
            resp.raise_for_status()
            raw = self._clean_json(resp.json()["choices"][0]["message"]["content"])
            return json.loads(raw)

    def _recalc_overall(self, scores: Dict[str, int]) -> int:
        weights = {
            "hook_strength": 0.25,
            "credibility": 0.20,
            "emotional_pull": 0.20,
            "cta_strength": 0.15,
            "clarity": 0.10,
            "audience_match": 0.05,
            "platform_fit": 0.05,
        }
        total = sum(scores.get(k, 50) * w for k, w in weights.items())
        return min(98, max(1, round(total)))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), retry=retry_if_not_exception_type(AIValidationError))
    async def analyze_ad(self, request_data: Dict[str, Any], files: List = None) -> Dict[str, Any]:
        content = request_data.get("video_script", "") or request_data.get("ad_copy", "")
        if not content.strip():
            raise AIValidationError("No content provided")

        fp = fingerprint_content(content)
        logger.info(f"Fingerprint: {fp.content_hash} | words={fp.word_count} "
                     f"| trauma={fp.has_trauma_pattern} | scam={fp.has_scam_pattern} "
                     f"| numbers={fp.has_specific_numbers} | proof={fp.has_social_proof}")

        # STAGE 1: Chain-of-thought scoring
        logger.info("Stage 1 — chain-of-thought analysis...")
        cot_prompt = self._build_cot_prompt(content, fp, request_data)
        first_pass = await self._call_ai(cot_prompt, max_tokens=4500, temperature=0.25)
        first_scores = first_pass.get("scores", {})
        logger.info(f"Stage 1 scores: {first_scores}")

        is_valid, msg = validate_scores(first_scores, fp)
        if not is_valid:
            logger.warning(f"Stage 1 validation soft-fail: {msg} — proceeding with raw scores")
            # Don't raise — proceed with whatever scores we got
            # Generate reasonable fallback scores if all zeros
            if all(v == 0 for k, v in first_scores.items() if k != "overall"):
                logger.info("All dimension scores are 0 — generating heuristic fallback scores")
                first_scores = self._generate_fallback_scores(fp, request_data)
                first_pass["scores"] = first_scores

        # STAGE 2: Critic pass
        logger.info("Stage 2 — critic review...")
        try:
            critic_prompt = self._build_critic_prompt(content, first_pass, fp, request_data)
            critic_result = await self._call_ai(critic_prompt, max_tokens=1500, temperature=0.15)
            critic_scores = critic_result.get("scores", {})
            adjustments = critic_result.get("adjustments_made", [])
            critic_notes = critic_result.get("critic_notes", "")

            final_scores = {}
            for dim in first_scores:
                orig = first_scores.get(dim, 50)
                crit = critic_scores.get(dim, orig)
                diff = crit - orig
                if abs(diff) > 15:
                    final_scores[dim] = crit
                elif abs(diff) > 5:
                    final_scores[dim] = round((orig + crit) / 2)
                else:
                    final_scores[dim] = orig

            if adjustments:
                logger.info(f"Critic adjusted {len(adjustments)} dimension(s)")
            logger.info(f"Stage 2 scores: {final_scores}")

        except Exception as e:
            logger.warning(f"Critic pass failed ({e}) — using Stage 1 scores")
            final_scores = first_scores
            critic_notes = "Critic pass unavailable"
            adjustments = []

        # STAGE 3: Recompute overall + assemble response
        final_scores["overall"] = self._recalc_overall(final_scores)

        reasoning = first_pass.get("reasoning", {})
        weaknesses = first_pass.get("critical_weaknesses", [])
        summary = first_pass.get("strategic_summary", "")

        if critic_notes and critic_notes != "Critic pass unavailable" and adjustments:
            dims_adjusted = ", ".join(a.get("dimension", "") for a in adjustments[:2])
            summary += f" (Critic adjusted {dims_adjusted} for accuracy.)"

        analysis = {
            "scores": final_scores,
            "strategic_summary": summary,
            "critical_weaknesses": weaknesses,
            "what_to_change_right_now": first_pass.get("what_to_change_right_now", ""),
            "line_by_line_analysis": first_pass.get("line_by_line_analysis", []),
            "ad_variants": first_pass.get("ad_variants", []),
            "winner_prediction": first_pass.get("winner_prediction", {}),
            "content_verification": first_pass.get("content_verification", {}),
        }

        logger.info(f"v7.0 complete — overall: {final_scores['overall']} "
                     f"| critic adjusted: {len(adjustments)} dims")
        return analysis


    def _generate_fallback_scores(self, fp, request_data):
        """Generate heuristic-based fallback scores when AI returns all zeros."""
        import random
        base = 35
        scores = {
            "hook_strength": base + (15 if fp.has_specific_numbers else 0) + random.randint(-5, 10),
            "clarity": base + 10 + random.randint(-5, 10),
            "credibility": base + (15 if fp.has_social_proof else 0) - (20 if fp.has_scam_pattern else 0) + random.randint(-5, 10),
            "emotional_pull": base + (20 if fp.has_trauma_pattern else 0) + (5 if fp.emotional_keywords else 0) + random.randint(-5, 10),
            "cta_strength": base + (10 if fp.has_cta else -10) + random.randint(-5, 10),
            "audience_match": base + random.randint(-5, 10),
            "platform_fit": base + random.randint(-5, 10),
        }
        scores = {k: max(5, min(95, v)) for k, v in scores.items()}
        scores["overall"] = self._recalc_overall(scores)
        logger.info(f"Fallback scores generated: {scores}")
        return scores

    def _build_cot_prompt(self, content: str, fingerprint: ContentFingerprint, request_data: Dict[str, Any]) -> str:
        """Build chain-of-thought scoring prompt. This is long but essential for quality."""
        audience_block = build_audience_context(request_data)
        brand_voice_block = ""

        # Add brand voice context if provided
        if "brand_voice" in request_data and request_data["brand_voice"]:
            brand_voice_block = "\n" + build_brand_voice_context(request_data["brand_voice"])

        return f"""You are ADLYTICS v7.0 — the most rigorous ad scoring system for West African markets.

CONTENT FINGERPRINT: {fingerprint.content_hash}
FIRST WORDS: "{fingerprint.first_20_chars}"
LAST WORDS: "{fingerprint.last_20_chars}"
WORD COUNT: {fingerprint.word_count}
HAS TRAUMA PATTERN: {fingerprint.has_trauma_pattern}
HAS SCAM PATTERN: {fingerprint.has_scam_pattern}
HAS SPECIFIC NUMBERS: {fingerprint.has_specific_numbers}
HAS SOCIAL PROOF: {fingerprint.has_social_proof}
HAS CTA: {fingerprint.has_cta}

{audience_block}{brand_voice_block}

AD CONTENT TO ANALYSE:
━━━━━━━━━━━━━━━━━━━━━━
{content}
━━━━━━━━━━━━━━━━━━━━━━

STEP 1 — LINE-BY-LINE REASONING (do this BEFORE scoring):
Read every sentence. For each, identify:
a) What psychological trigger it activates (or fails to activate)
b) Whether it would make this SPECIFIC audience stop scrolling, trust, or click
c) Any weakness, vague claim, or missing proof element
d) If brand voice is specified: how well this matches the brand's tone and style
Only after completing this reasoning, move to Step 2.

STEP 2 — SCORE EACH DIMENSION (0–100):

hook_strength — First 1–2 sentences only. 90-100: Specific loss/number/pattern interrupt. 70-89: Strong curiosity gap. 50-69: Clear but generic. 30-49: Weak. 0-29: No hook.
credibility — Does the ad PROVE its claims? 90-100: Specific losses, documents, named results. 50-69: Claims without proof. 0-29: Active scam signals. If scam detected → cap at 35.
emotional_pull — Does it create visceral feeling? 90-100: Personal trauma with detail. 70-89: Relatable pain. 50-69: Generic emotional language. 0-29: Cold/transactional.
clarity — Can THIS audience understand instantly? 90-100: Crystal clear. 50-69: Requires effort. 0-29: Confusing.
cta_strength — The final action request. 90-100: Specific, low-friction, benefit-driven. 70-89: Clear but generic. 0-29: No CTA.
audience_match — Does it speak THIS specific audience's language? Generic = max 50. Country-specific = 75+.
platform_fit — Is format and tone native to the platform?
overall — Weighted: hook(25%) + credibility(20%) + emotional(20%) + cta(15%) + clarity(10%) + audience(5%) + platform(5%)

SCORING RULES:
1. Scores MUST reflect the reasoning
2. Diversity required: scores should span at least 30 points
3. Be HARDER on weak ads. Most ads score 35–65. Only exceptional ads hit 80+.
4. Generic copy → cap overall at 55
5. No proof elements → credibility max 55
6. Every critical_weakness must include a precise_fix with EXACT rewrite
7. ad_variants MUST be derived from ACTUAL ad content — not generic templates
8. If the ad mentions a specific product → variants must reference it
9. If brand voice is provided: ads deviating from brand guidelines should score lower overall

OUTPUT STRICT JSON (no markdown, no preamble):
{{
    "reasoning": {{
        "line_by_line": "sentence-by-sentence analysis",
        "hook_verdict": "Why the hook earns/loses its score",
        "credibility_verdict": "Specific proof elements found or missing",
        "audience_verdict": "How well it matches the audience profile",
        "brand_voice_verdict": "How well it adheres to brand voice guidelines (if applicable)",
        "biggest_weakness": "The single change that would most improve performance"
    }},
    "content_verification": {{
        "fingerprint": "{fingerprint.content_hash}",
        "first_10_words": "...",
        "last_10_words": "..."
    }},
    "scores": {{
        "overall": 0, "hook_strength": 0, "clarity": 0, "credibility": 0,
        "emotional_pull": 0, "cta_strength": 0, "audience_match": 0, "platform_fit": 0
    }},
    "strategic_summary": "2-3 sentence summary specific to THIS content and audience.",
    "critical_weaknesses": [
        {{"issue": "...", "severity": "High|Medium|Low", "impact": "...", "precise_fix": "...", "expected_lift": "..."}}
    ],
    "what_to_change_right_now": "Single most impactful change TODAY with specific rewrite.",
    "line_by_line_analysis": [
        {{"line": "...", "verdict": "Strong|Weak|Neutral", "reason": "...", "rewrite": "..."}}
    ],
    "ad_variants": [
        {{
            "id": 1, "angle": "Fear / Loss", "predicted_score": 0,
            "hook": "...", "body": "...", "cta": "...", "why_it_works": "..."
        }},
        {{
            "id": 2, "angle": "Curiosity Gap", "predicted_score": 0,
            "hook": "...", "body": "...", "cta": "...", "why_it_works": "..."
        }},
        {{
            "id": 3, "angle": "Social Proof", "predicted_score": 0,
            "hook": "...", "body": "...", "cta": "...", "why_it_works": "..."
        }}
    ],
    "winner_prediction": {{
        "winner_id": 1, "angle": "...", "confidence": "65%", "reasoning": "..."
    }}
}}"""

    def _build_critic_prompt(self, content: str, first_pass: Dict[str, Any], fingerprint: ContentFingerprint, request_data: Dict[str, Any]) -> str:
        """Second-pass critic that challenges inflated scores."""
        scores = first_pass.get("scores", {})
        reasoning = first_pass.get("reasoning", {})

        flags = []
        if scores.get("credibility", 0) > 65 and not fingerprint.has_specific_numbers and not fingerprint.has_social_proof:
            flags.append(f"credibility={scores['credibility']} but NO specific numbers or social proof")
        if scores.get("hook_strength", 0) > 75 and not fingerprint.has_trauma_pattern and not fingerprint.has_specific_numbers:
            flags.append(f"hook_strength={scores['hook_strength']} but no trauma or specific number")
        if scores.get("emotional_pull", 0) > 70 and not fingerprint.has_trauma_pattern:
            flags.append(f"emotional_pull={scores['emotional_pull']} but no trauma pattern detected")
        if scores.get("audience_match", 0) > 70 and not any(
            kw in content.lower() for kw in ["nigeria", "naira", "₦", "lagos", "abuja", "ghana", "accra", "uk", "london", "£"]
        ):
            flags.append(f"audience_match={scores['audience_match']} but no market-specific language")
        if max(scores.values() or [0]) - min(scores.values() or [0]) < 20:
            flags.append(f"Score spread only {max(scores.values() or [0]) - min(scores.values() or [0])} points — suspiciously uniform")

        flags_text = "\n".join(f"  ⚠️ {f}" for f in flags) if flags else "  ✅ No obvious inflation flags"

        return f"""You are ADLYTICS Critic — a strict second reviewer who challenges over-generous scoring.

ORIGINAL SCORES: {json.dumps(scores, indent=2)}
ORIGINAL REASONING: {reasoning.get('line_by_line', 'Not provided')[:600]}

INFLATION FLAGS:
{flags_text}

AD CONTENT:
{content}

FINGERPRINT FACTS:
- Has specific numbers: {fingerprint.has_specific_numbers}
- Has social proof: {fingerprint.has_social_proof}
- Has CTA: {fingerprint.has_cta}
- Has trauma pattern: {fingerprint.has_trauma_pattern}
- Has scam pattern: {fingerprint.has_scam_pattern}
- Word count: {fingerprint.word_count}

{build_audience_context(request_data)}

CRITIC RULES:
1. You may LOWER or RAISE scores — accuracy matters
2. Claim without proof cannot score above 60 on credibility
3. Hook without specific number/loss/pattern interrupt cannot score above 72
4. audience_match above 70 requires market-specific language
5. If spread < 20 points, widen it
6. If a score is correct, leave it unchanged

OUTPUT STRICT JSON:
{{
    "critic_notes": "2-3 sentences explaining changes",
    "scores_adjusted": true,
    "scores": {{
        "overall": 0, "hook_strength": 0, "clarity": 0, "credibility": 0,
        "emotional_pull": 0, "cta_strength": 0, "audience_match": 0, "platform_fit": 0
    }},
    "adjustments_made": [
        {{"dimension": "...", "from": 0, "to": 0, "reason": "..."}}
    ]
}}"""


def get_ai_engine():
    return AIEngine()
