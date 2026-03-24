"""
ADLYTICS AI Engine v7.0
Three accuracy upgrades:
  1. Chain-of-thought scoring — model reasons line-by-line before scoring
  2. Full audience context injection — age, income, occupation, country shape every score
  3. Two-pass critic — a second call challenges inflated scores before returning
"""

import json
import re
import hashlib
import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Content fingerprint (unchanged — keeps existing validation)
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
# Audience context builder (Fix 2)
# ─────────────────────────────────────────────────────────────

AUDIENCE_PROFILES = {
    # country → typical ad-viewer psychology
    "nigeria": {
        "skepticism":  "Very high — scam fatigue from endless 'make money' ads. Needs specific proof.",
        "trust_cues":  "Track record screenshots, C of O documents, specific naira amounts, known landmarks.",
        "cta_style":   "WhatsApp DM or 'Comment INFO' — not 'click here'. Low-friction next step.",
        "taboos":      "Guaranteed returns, unrealistic income claims, foreign currency emphasis.",
        "currency":    "₦",
    },
    "ghana": {
        "skepticism":  "High — similar to Nigeria but more receptive to fintech/crypto messaging.",
        "trust_cues":  "GH₵ amounts, local bank names, Accra/Kumasi references.",
        "cta_style":   "WhatsApp or direct call. Mobile-first audience.",
        "taboos":      "Dollar-dominated copy, unrealistic promises.",
        "currency":    "GH₵",
    },
    "uk": {
        "skepticism":  "Moderate — FCA-trained audience expects regulatory disclosure.",
        "trust_cues":  "FCA registration numbers, FSCS protection mention, named reviews.",
        "cta_style":   "Website link with clear privacy policy. Email capture.",
        "taboos":      "Guarantees, non-FCA claims, pressure tactics.",
        "currency":    "£",
    },
    "us": {
        "skepticism":  "Moderate — SEC-aware for finance. Reviews and social proof convert well.",
        "trust_cues":  "BBB rating, verified reviews, SEC/FINRA mentions for finance.",
        "cta_style":   "Clear CTA button, free trial or lead magnet.",
        "taboos":      "Unsubstantiated income claims (FTC), testimonials without disclaimer.",
        "currency":    "$",
    },
}

OCCUPATION_PSYCHOLOGY = {
    "entrepreneur": "Busy, result-oriented. Responds to ROI and time-saving. Ignores generic motivational content.",
    "professional": "Risk-averse, credentials matter. Needs social proof from peers. Long decision cycle.",
    "student":      "Budget-conscious, aspirational. Responds to 'start small' messaging. Short attention span.",
    "trader":       "Highly skeptical of claims. Wants specific data, not stories. Will fact-check claims.",
    "blue_collar":  "Values simplicity, directness. Responds to family/security framing. Distrusts complexity.",
    "creative":     "Trend-aware, aesthetic-sensitive. Needs to see the 'cool factor'. Responds to community.",
}

INCOME_PSYCHOLOGY = {
    "low":      "Price-sensitive. Must see clear ROI before any spend. 'Free to start' messaging essential.",
    "middle":   "Aspirational. Wants quality but watches price. Responds to 'value for money' framing.",
    "high":     "Quality-first. Price secondary. Exclusivity and expertise matter more than discounts.",
    "affluent": "Time is priority. Concierge-level trust. Peer validation from other affluents.",
}

AGE_PSYCHOLOGY = {
    "18-24": "Short attention span, trend-driven, sceptical of 'old' methods. Hook must land in 1 second.",
    "25-34": "Career-driven, comparing options. Responds to specificity and peer validation.",
    "35-44": "Family-focused, stability-seeking. Trust and track record outweigh hype.",
    "45-54": "Established, cautious. Prefers detailed information. Long-form converts better.",
    "55+":   "Security-focused, brand-loyal. Needs clarity, no jargon, clear disclaimers.",
}


def build_audience_context(request_data: Dict[str, Any]) -> str:
    """Build a rich audience psychology block for the prompt."""
    country     = request_data.get("audience_country", "nigeria").lower()
    age         = request_data.get("audience_age", "25-34")
    income      = request_data.get("audience_income", "middle")
    occupation  = request_data.get("audience_occupation", "")
    platform    = request_data.get("platform", "tiktok")
    industry    = request_data.get("industry", "finance")

    country_ctx = AUDIENCE_PROFILES.get(country, AUDIENCE_PROFILES["nigeria"])

    # Age: may be comma-separated multi-select
    primary_age = age.split(",")[0].strip()
    age_ctx = AGE_PSYCHOLOGY.get(primary_age, AGE_PSYCHOLOGY["25-34"])

    # Income
    income_ctx = INCOME_PSYCHOLOGY.get(income, INCOME_PSYCHOLOGY["middle"])

    # Occupation: may be comma-separated
    occ_parts = [o.strip() for o in occupation.split(",") if o.strip()] if occupation else []
    occ_lines = "\n".join(
        f"  • {o}: {OCCUPATION_PSYCHOLOGY.get(o, 'General audience.')}" for o in occ_parts[:3]
    ) if occ_parts else "  • General mixed audience"

    platform_notes = {
        "tiktok":    "Videos 15–60s. Hook must land in 0–2s. Casual, authentic tone converts. Text overlays essential.",
        "facebook":  "Longer copy tolerated. Social proof + clear CTA. Cold audiences need trust-building.",
        "instagram": "Visual-first. Aspirational framing. Story format preferred. Link-in-bio friction.",
        "youtube":   "Pre-roll: hook in 5s before skip. In-feed: thumbnail + first line must compel click.",
        "google":    "Search intent. User is already looking — match their exact language. CTA must solve immediately.",
    }.get(platform.lower(), "General digital ad.")

    return f"""
TARGET AUDIENCE PROFILE (use this to score audience_match and adjust ALL scores):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Country:    {country.title()} | Currency: {country_ctx['currency']}
Age group:  {age} → {age_ctx}
Income:     {income or 'middle'} → {income_ctx}
Occupation: 
{occ_lines}

Country-specific psychology:
  • Skepticism level: {country_ctx['skepticism']}
  • Trust signals:    {country_ctx['trust_cues']}
  • CTA style:        {country_ctx['cta_style']}
  • Avoid:            {country_ctx['taboos']}

Platform: {platform.upper()} → {platform_notes}
Industry: {industry}

SCORING IMPACT: If the ad ignores these audience realities → audience_match ≤ 45.
If the ad speaks their exact language and addresses their specific fears → audience_match ≥ 80.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""


# ─────────────────────────────────────────────────────────────
# Chain-of-thought prompt builder (Fix 1)
# ─────────────────────────────────────────────────────────────

def build_cot_prompt(content: str, fingerprint: ContentFingerprint,
                     request_data: Dict[str, Any]) -> str:
    """Chain-of-thought: model reasons before scoring."""

    audience_block = build_audience_context(request_data)

    return f"""You are ADLYTICS v7.0 — the most rigorous ad scoring system for West African markets.

CONTENT FINGERPRINT: {fingerprint.content_hash}
FIRST WORDS: "{fingerprint.first_20_chars}"
LAST WORDS:  "{fingerprint.last_20_chars}"
WORD COUNT:  {fingerprint.word_count}
HAS TRAUMA PATTERN:  {fingerprint.has_trauma_pattern}
HAS SCAM PATTERN:    {fingerprint.has_scam_pattern}
HAS SPECIFIC NUMBERS:{fingerprint.has_specific_numbers}
HAS SOCIAL PROOF:    {fingerprint.has_social_proof}
HAS CTA:             {fingerprint.has_cta}
{audience_block}

AD CONTENT TO ANALYSE:
━━━━━━━━━━━━━━━━━━━━━━
{content}
━━━━━━━━━━━━━━━━━━━━━━

STEP 1 — LINE-BY-LINE REASONING (do this BEFORE scoring):
Read every sentence. For each, identify:
  a) What psychological trigger it activates (or fails to activate)
  b) Whether it would make this SPECIFIC audience stop scrolling, trust, or click
  c) Any weakness, vague claim, or missing proof element

Only after completing this reasoning, move to Step 2.

STEP 2 — SCORE EACH DIMENSION (0–100):

hook_strength — First 1–2 sentences only. Does "{fingerprint.first_20_chars[:45]}..." stop THIS audience?
  90–100: Specific loss/number/pattern interrupt that speaks THIS audience's fear
  70–89:  Strong curiosity gap but generic — works on most audiences
  50–69:  Clear opening but no emotional trigger
  30–49:  Weak opener — audience scrolls past
  0–29:   No hook. Pure label or filler.

credibility — Does the ad PROVE its claims?
  90–100: Shows specific losses, documents, named results, exact amounts
  70–89:  Some proof (testimonial, screenshot reference) but unverified
  50–69:  Claims without proof ("we've helped thousands") 
  30–49:  Zero proof — pure assertion
  0–29:   Active scam signals (guarantee, risk-free, 10x)
  IMPORTANT: {fingerprint.has_scam_pattern} scam detected → cap at 35 max

emotional_pull — Does it create visceral feeling?
  90–100: Personal trauma story with specific detail ("I lost ₦300K in 6 weeks")
  70–89:  Clear relatable pain point without personal story
  50–69:  Generic emotional language ("change your life")
  30–49:  Informational only — no emotion
  0–29:   Cold and transactional
  IMPORTANT: {fingerprint.has_trauma_pattern} trauma pattern → minimum 70

clarity — Can THIS audience understand it instantly?
  90–100: Crystal clear in one read, no jargon
  50–69:  Requires effort or has confusing sections
  0–29:   Confusing, overcrowded, or contradictory

cta_strength — The final action request:
  90–100: Specific, low-friction, benefit-driven ("DM 'TRADE' for free analysis")
  70–89:  Clear action but generic ("click here", "learn more")
  50–69:  Vague ("find out more", "visit us")
  0–29:   No CTA or buried CTA
  NOTE: {fingerprint.has_cta} CTA detected in content

audience_match — Does it speak THIS specific audience's language?
  Score based on the audience profile above. Generic copy that could target anyone → max 50.
  Copy that addresses THIS country's specific fears/trust signals → 75+.

platform_fit — Is the format and tone native to the platform?
  Score based on platform notes above.

overall — Weighted: hook(25%) + credibility(20%) + emotional(20%) + cta(15%) + clarity(10%) + audience(5%) + platform(5%)

SCORING RULES:
1. Scores MUST reflect the reasoning — no lazy 70s across the board
2. Diversity required: scores should span at least 30 points range
3. Every score must be justified by something specific in the content
4. Reference fingerprint {fingerprint.content_hash} in verification
5. Be HARDER on weak ads. Most ads score 35–65. Only exceptional ads hit 80+.

OUTPUT STRICT JSON (no markdown, no preamble):
{{
  "reasoning": {{
    "line_by_line": "Your sentence-by-sentence analysis here (2–4 sentences per main section)",
    "hook_verdict": "Why the hook earns/loses its score",
    "credibility_verdict": "Specific proof elements found or missing",
    "audience_verdict": "How well it matches the {request_data.get('audience_country','nigeria')} {request_data.get('audience_age','25-34')} profile",
    "biggest_weakness": "The single change that would most improve performance"
  }},
  "content_verification": {{
    "fingerprint": "{fingerprint.content_hash}",
    "first_10_words": "...",
    "last_10_words": "..."
  }},
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
  "strategic_summary": "2–3 sentence summary specific to THIS content and audience",
  "critical_weaknesses": [
    {{"issue": "...", "severity": "High|Medium|Low", "impact": "...", "precise_fix": "..."}},
    {{"issue": "...", "severity": "High|Medium|Low", "impact": "...", "precise_fix": "..."}}
  ]
}}"""


# ─────────────────────────────────────────────────────────────
# Critic prompt builder (Fix 3 — two-pass)
# ─────────────────────────────────────────────────────────────

def build_critic_prompt(content: str, first_pass: Dict[str, Any],
                        fingerprint: ContentFingerprint,
                        request_data: Dict[str, Any]) -> str:
    """Second-pass critic that challenges inflated scores."""

    scores = first_pass.get("scores", {})
    reasoning = first_pass.get("reasoning", {})
    audience_block = build_audience_context(request_data)

    # Identify suspiciously high scores to challenge
    flags = []
    if scores.get("credibility", 0) > 65 and not fingerprint.has_specific_numbers and not fingerprint.has_social_proof:
        flags.append(f"credibility={scores['credibility']} but NO specific numbers or social proof found in content")
    if scores.get("hook_strength", 0) > 75 and not fingerprint.has_trauma_pattern and not fingerprint.has_specific_numbers:
        flags.append(f"hook_strength={scores['hook_strength']} but hook has no trauma pattern or specific number")
    if scores.get("emotional_pull", 0) > 70 and not fingerprint.has_trauma_pattern and not fingerprint.emotional_keywords:
        flags.append(f"emotional_pull={scores['emotional_pull']} but no trauma pattern or emotional keywords detected")
    if scores.get("audience_match", 0) > 70 and not any(
        kw in content.lower() for kw in ["nigeria", "naira", "₦", "lagos", "abuja", "ghana", "accra", "uk", "london", "£"]
    ):
        flags.append(f"audience_match={scores['audience_match']} but no market-specific language found")
    if max(scores.values() or [0]) - min(scores.values() or [0]) < 20:
        flags.append(f"Score spread is only {max(scores.values() or [0]) - min(scores.values() or [0])} points — suspiciously uniform")

    flags_text = "\n".join(f"  ⚠️  {f}" for f in flags) if flags else "  ✅ No obvious inflation flags"

    return f"""You are ADLYTICS Critic — a strict second reviewer who challenges over-generous scoring.

ORIGINAL SCORES TO REVIEW:
{json.dumps(scores, indent=2)}

ORIGINAL REASONING:
{reasoning.get('line_by_line', 'Not provided')[:600]}

INFLATION FLAGS DETECTED:
{flags_text}

AD CONTENT:
━━━━━━━━━━━━━━━━━━━━━━
{content}
━━━━━━━━━━━━━━━━━━━━━━

FINGERPRINT FACTS (ground truth):
- Has specific numbers: {fingerprint.has_specific_numbers}
- Has social proof:     {fingerprint.has_social_proof}
- Has CTA:             {fingerprint.has_cta}
- Has trauma pattern:  {fingerprint.has_trauma_pattern}
- Has scam pattern:    {fingerprint.has_scam_pattern}
- Word count:          {fingerprint.word_count}
{build_audience_context(request_data)}

YOUR JOB:
Review each score. For each inflation flag above, decide:
  A) The score is justified — explain why the fingerprint facts are wrong
  B) The score is inflated — provide the corrected, lower score

CRITIC RULES:
1. You may LOWER scores — you may NOT raise them (raising is the analyst's job)
2. A claim without proof cannot score above 60 on credibility
3. A hook without a specific number, loss, or pattern interrupt cannot score above 72 on hook_strength
4. audience_match above 70 requires market-specific language (local currency, city, cultural reference)
5. If spread < 20 points, you MUST widen it — real ads always have strong and weak dimensions
6. Be merciful on 1–2 genuinely strong dimensions. Only penalise the inflated ones.

OUTPUT STRICT JSON:
{{
  "critic_notes": "2–3 sentences explaining what you changed and why",
  "scores_adjusted": true,
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
  "adjustments_made": [
    {{"dimension": "credibility", "from": 72, "to": 45, "reason": "No proof elements found"}}
  ]
}}"""


# ─────────────────────────────────────────────────────────────
# Enhanced fingerprint
# ─────────────────────────────────────────────────────────────

def fingerprint_content(content: str) -> ContentFingerprint:
    cl = content.lower()

    emotional_words = [
        "lost", "pain", "struggle", "truth", "honest", "transparent",
        "scam", "fear", "worry", "stress", "failed", "quit", "stop",
        "burned", "cheated", "mistake", "regret", "frustrated"
    ]
    trauma_patterns = ["i lost", "i failed", "i quit", "i stopped", "burned", "scammed",
                       "lost ₦", "lost $", "lost £", "wasted", "threw away"]
    scam_patterns   = ["guarantee", "guaranteed", "no experience needed", "risk free",
                       "risk-free", "10x your", "100% profit", "get rich", "overnight"]
    number_patterns = [r'\d+[%xX]', r'₦\d', r'\$\d', r'£\d', r'\d+k', r'\d+,\d{3}',
                       r'\d+ days', r'\d+ weeks', r'\d+ months']
    proof_patterns  = ["testimonial", "screenshot", "verified", "track record", "client",
                       "student", "member", "case study", "results", "proof"]
    cta_patterns    = ["dm", "whatsapp", "click", "call", "comment", "sign up", "register",
                       "join", "get started", "book", "apply", "download", "tap"]

    return ContentFingerprint(
        content_hash        = hashlib.md5(content.encode()).hexdigest()[:8],
        word_count          = len(content.split()),
        first_20_chars      = content[:20].strip(),
        last_20_chars       = content[-20:].strip() if len(content) >= 20 else content.strip(),
        has_trauma_pattern  = any(p in cl for p in trauma_patterns),
        has_scam_pattern    = any(p in cl for p in scam_patterns),
        emotional_keywords  = [w for w in emotional_words if w in cl],
        sentence_count      = len(re.split(r'[.!?]+', content.strip())),
        has_specific_numbers= any(re.search(p, content) for p in number_patterns),
        has_social_proof    = any(p in cl for p in proof_patterns),
        has_cta             = any(p in cl for p in cta_patterns),
    )


# ─────────────────────────────────────────────────────────────
# Score validation (updated for new dimensions)
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
# Main AI Engine class
# ─────────────────────────────────────────────────────────────

class AIEngine:
    """v7.0 — Chain-of-thought + audience injection + two-pass critic"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key  = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"

    def _clean_json(self, raw: str) -> str:
        return re.sub(r"```json|```", "", raw).strip()

    async def _call_ai(self, prompt: str, max_tokens: int = 4000,
                       temperature: float = 0.25) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type":  "application/json",
                    "HTTP-Referer":  "https://adlytics.ai",
                },
                json={
                    "model":           "openai/gpt-4o",
                    "messages":        [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "max_tokens":      max_tokens,
                    "temperature":     temperature,
                }
            )
        resp.raise_for_status()
        raw = self._clean_json(resp.json()["choices"][0]["message"]["content"])
        return json.loads(raw)

    def _recalc_overall(self, scores: Dict[str, int]) -> int:
        weights = {
            "hook_strength":  0.25,
            "credibility":    0.20,
            "emotional_pull": 0.20,
            "cta_strength":   0.15,
            "clarity":        0.10,
            "audience_match": 0.05,
            "platform_fit":   0.05,
        }
        total = sum(scores.get(k, 50) * w for k, w in weights.items())
        return min(98, max(1, round(total)))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def analyze_ad(self, request_data: Dict[str, Any],
                         files: List = None) -> Dict[str, Any]:
        """
        v7.0 three-stage pipeline:
          Stage 1 — Chain-of-thought scoring with full audience context
          Stage 2 — Critic pass to challenge inflated scores
          Stage 3 — Merge, recompute overall, return
        """
        content = request_data.get("video_script", "") or request_data.get("ad_copy", "")
        if not content.strip():
            raise AIValidationError("No content provided")

        fp = fingerprint_content(content)
        logger.info(f"🔬 Fingerprint: {fp.content_hash} | words={fp.word_count} "
                    f"| trauma={fp.has_trauma_pattern} | scam={fp.has_scam_pattern} "
                    f"| numbers={fp.has_specific_numbers} | proof={fp.has_social_proof}")

        # ── STAGE 1: Chain-of-thought scoring ────────────────
        logger.info("🧠 Stage 1 — chain-of-thought analysis...")
        cot_prompt    = build_cot_prompt(content, fp, request_data)
        first_pass    = await self._call_ai(cot_prompt, max_tokens=4500, temperature=0.25)
        first_scores  = first_pass.get("scores", {})

        logger.info(f"📊 Stage 1 scores: {first_scores}")

        # Validate first pass
        is_valid, msg = validate_scores(first_scores, fp)
        if not is_valid:
            logger.warning(f"⚠️ Stage 1 validation failed: {msg} — retrying raises exception")
            raise AIValidationError(f"Stage 1 invalid: {msg}")

        # ── STAGE 2: Critic pass ──────────────────────────────
        logger.info("🔍 Stage 2 — critic review...")
        critic_prompt = build_critic_prompt(content, first_pass, fp, request_data)
        try:
            critic_result = await self._call_ai(critic_prompt, max_tokens=1500, temperature=0.15)
            critic_scores = critic_result.get("scores", {})
            adjustments   = critic_result.get("adjustments_made", [])
            critic_notes  = critic_result.get("critic_notes", "")

            # Merge: critic can only lower scores, not raise them
            final_scores = {}
            for dim in first_scores:
                orig = first_scores.get(dim, 50)
                crit = critic_scores.get(dim, orig)
                final_scores[dim] = min(orig, crit)  # take the lower (critic's job is to penalise)

            if adjustments:
                logger.info(f"✏️  Critic adjusted {len(adjustments)} dimension(s): "
                            f"{[a.get('dimension') for a in adjustments]}")
            logger.info(f"📊 Stage 2 scores: {final_scores}")

        except Exception as e:
            logger.warning(f"⚠️ Critic pass failed ({e}) — using Stage 1 scores")
            final_scores  = first_scores
            critic_notes  = "Critic pass unavailable"
            adjustments   = []

        # ── STAGE 3: Recompute overall + assemble response ────
        final_scores["overall"] = self._recalc_overall(final_scores)

        # Pull reasoning and weaknesses from Stage 1
        reasoning  = first_pass.get("reasoning", {})
        weaknesses = first_pass.get("critical_weaknesses", [])
        summary    = first_pass.get("strategic_summary", "")
        verification = first_pass.get("content_verification", {})

        # Enrich summary with critic note if meaningful
        if critic_notes and critic_notes != "Critic pass unavailable" and adjustments:
            dims_adjusted = ", ".join(a.get("dimension","") for a in adjustments[:2])
            summary += f" (Critic adjusted {dims_adjusted} for accuracy.)"

        analysis = {
            "scores":               final_scores,
            "strategic_summary":    summary,
            "critical_weaknesses":  weaknesses,
            "content_verification": verification,
            "_engine_metadata": {
                "version":          "7.0",
                "fingerprint":      fp.content_hash,
                "stage1_scores":    first_scores,
                "critic_notes":     critic_notes,
                "adjustments":      adjustments,
                "has_trauma":       fp.has_trauma_pattern,
                "has_scam":         fp.has_scam_pattern,
                "has_numbers":      fp.has_specific_numbers,
                "has_proof":        fp.has_social_proof,
            }
        }

        logger.info(f"✅ v7.0 complete — overall: {final_scores['overall']} "
                    f"| critic adjusted: {len(adjustments)} dims")
        return analysis


def get_ai_engine():
    return AIEngine()
