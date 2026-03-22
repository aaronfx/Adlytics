"""
ADLYTICS v5.7 - AI Engine with Detailed Scoring Rubrics
"""

import os
import json
import logging
from typing import Dict, Any
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COUNTRY_PROFILES = {
    "nigeria": {
        "currency": "₦",
        "currency_name": "Naira",
        "behavioral_traits": [
            "High scam sensitivity from Ponzi history",
            "Reliance on social proof and peer validation",
            "Mobile-first digital access"
        ],
        "trust_builders": [
            "Local testimonials with faces",
            "Community validation",
            "Official registration"
        ]
    },
    "kenya": {
        "currency": "KSh",
        "currency_name": "Shilling",
        "behavioral_traits": [
            "Mobile money integration",
            "Community decision making"
        ],
        "trust_builders": [
            "Mobile payment",
            "Community endorsement"
        ]
    },
    "united_states": {
        "currency": "$",
        "currency_name": "USD",
        "behavioral_traits": [
            "Individual achievement focus",
            "Privacy awareness"
        ],
        "trust_builders": [
            "Money-back guarantee",
            "Third-party reviews"
        ]
    },
    "united_kingdom": {
        "currency": "£",
        "currency_name": "Pound",
        "behavioral_traits": [
            "Reserved skepticism",
            "Understated communication"
        ],
        "trust_builders": [
            "Official registration",
            "Transparent terms"
        ]
    },
    "india": {
        "currency": "₹",
        "currency_name": "Rupee",
        "behavioral_traits": [
            "Family decision dynamics",
            "Value-conscious"
        ],
        "trust_builders": [
            "Tax transparency",
            "Regional language"
        ]
    }
}

DEFAULT_PROFILE = {
    "currency": "$",
    "currency_name": "USD",
    "behavioral_traits": ["General best practices"],
    "trust_builders": ["Testimonials"]
}


class AIEngineV5:
    """V5.7 AI Engine - Detailed scoring rubrics"""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
        self.base_url = "https://openrouter.ai/api/v1"

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set")

        logger.info(f"🤖 Using model: {self.model}")

    def _get_country_profile(self, country: str) -> Dict[str, Any]:
        country_lower = country.lower().replace(" ", "_")
        return COUNTRY_PROFILES.get(country_lower, DEFAULT_PROFILE)

    def _analyze_content_quality(self, ad_copy: str, video_script: str) -> Dict[str, Any]:
        """Pre-analyze content"""
        content = (ad_copy + " " + video_script).strip()
        words = content.split()
        real_words = [w for w in words if len(w) > 2 and w.isalpha()]

        return {
            "total_chars": len(content),
            "total_words": len(words),
            "real_words": len(real_words),
            "is_empty": len(content) < 5,
            "is_short": len(real_words) < 10,
            "has_ad_copy": len(ad_copy.strip()) > 0,
            "has_video": len(video_script.strip()) > 0
        }

    async def analyze_ad(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze with detailed rubrics"""
        ad_copy = request_data.get('ad_copy', '').strip()
        video_script = request_data.get('video_script', '').strip()
        country = request_data.get('country', 'united_states')

        content_analysis = self._analyze_content_quality(ad_copy, video_script)

        if content_analysis["is_empty"]:
            raise ValueError("No content provided")

        country_profile = self._get_country_profile(country)
        prompt = self._build_prompt(request_data, ad_copy, video_script, country_profile, content_analysis)

        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=90.0) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://adlytics.ai",
                            "X-Title": "ADLYTICS"
                        },
                        json={
                            "model": self.model,
                            "messages": [
                                {"role": "system", "content": self._get_system_prompt(content_analysis)},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.2,
                            "max_tokens": 8000
                        }
                    )

                    result = response.json()
                    content = result["choices"][0]["message"]["content"]

                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]

                    analysis = json.loads(content.strip())
                    return self._enforce_score_limits(analysis, content_analysis)

            except Exception as e:
                logger.warning(f"Attempt {attempt+1} failed: {e}")
                if attempt == 2:
                    raise

        raise ValueError("Analysis failed")

    def _get_system_prompt(self, content_analysis: Dict) -> str:
        """Detailed scoring rubrics"""
        max_score = 15 if content_analysis["real_words"] < 10 else (35 if content_analysis["real_words"] < 20 else (50 if content_analysis["real_words"] < 30 else 100))

        return f"""You are a STRICT performance marketing analyst using DETAILED RUBRICS.

CONTENT METRICS:
- Real words: {content_analysis['real_words']}
- Max allowable score: {max_score}

SCORING RUBRICS - Use these EXACT criteria:

=== HOOK STRENGTH (0-100) ===
90-100: Stops scroll in 0-3s, specific numbers, curiosity gap, emotional trigger, clear value in first 15 words
80-89: Strong opening, clear benefit, some curiosity, professional tone
70-79: Decent hook, clear but generic, minor improvements needed
60-69: Weak hook, boring opening, vague benefit
40-59: Poor hook, feature-focused not benefit-focused, no curiosity
20-39: Terrible hook, confusing opening, no value proposition
0-19: No hook exists, starts with filler, random words

=== CLARITY (0-100) ===
90-100: Understood in 3 seconds, one clear message, no jargon, logical flow
80-89: Very clear, easy to understand, minimal cognitive load
70-79: Mostly clear, one minor confusion point
60-69: Somewhat clear, requires re-reading, minor ambiguity
40-59: Confusing, multiple messages competing, jargon present
20-39: Very unclear, reader confused about offer
0-19: Gibberish, no discernible message, random text

=== CREDIBILITY (0-100) ===
90-100: Specific proof (numbers, testimonials, results), guarantees, trust signals, transparency
80-89: Good credibility markers, some social proof, professional presentation
70-79: Basic credibility, mentions results but vague
60-69: Weak credibility, claims without proof
40-59: Poor credibility, exaggerated claims, no proof
20-39: No credibility, sounds like scam, unrealistic promises
0-19: Active red flags, obvious deception, Nigerian prince vibes

=== EMOTIONAL PULL (0-100) ===
90-100: Addresses deep pain point, creates urgency, aspiration trigger, fear of loss, strong desire
80-89: Good emotional connection, clear pain/pleasure dynamic
70-79: Some emotional appeal, but surface level
60-69: Weak emotion, mostly logical, boring
40-59: No emotional hook, dry facts only
20-39: Wrong emotion, tone-deaf, offensive
0-19: Confusing emotional signals, contradictory

=== CTA STRENGTH (0-100) ===
90-100: Clear action, specific benefit, urgency, low friction, one step only
80-89: Strong CTA, clear what to do, good motivation
70-79: Decent CTA, clear action but weak motivation
60-69: Weak CTA, vague action, no urgency
40-59: Poor CTA, multiple choices, high friction
20-39: Terrible CTA, confusing action, hidden button
0-19: No CTA, or CTA is broken/missing

=== AUDIENCE MATCH (0-100) ===
90-100: Perfect language for demographic, addresses specific pain points, resonates deeply
80-89: Good match, appropriate tone and vocabulary
70-79: Decent match, minor mismatches
60-69: Generic, could be for anyone, not targeted
40-59: Poor match, wrong language level, tone-deaf
20-39: Completely wrong audience, alienating
0-19: Insulting or offensive to target demographic

=== PLATFORM FIT (0-100) ===
90-100: Perfect for platform (TikTok=short/native, FB=story/community, IG=visual/lifestyle)
80-89: Good fit, follows platform conventions
70-79: Decent fit, minor platform violations
60-69: Poor fit, wrong format for platform
40-59: Very poor fit, ignores platform culture
20-39: Completely wrong platform
0-19: Violates platform policies

=== OVERALL (0-100) ===
Calculate as weighted average:
- Hook: 20%, Clarity: 15%, Credibility: 15%, Emotional: 20%, CTA: 15%, Audience: 10%, Platform: 5%

SCORING RULES:
1. Content with < 10 words cannot score above 15 in ANY category
2. Empty ad_copy = Hook and CTA max 20
3. Score step-by-step using rubrics above
4. Be CRITICAL - most ads score 40-60, not 80+
"""

    def _build_prompt(self, data: Dict, ad_copy: str, video_script: str, country_profile: Dict, content_analysis: Dict) -> str:
        """Build prompt with rubric instructions"""
        currency = country_profile['currency']
        country = data.get('country', 'united_states')
        max_score = 15 if content_analysis["real_words"] < 10 else (35 if content_analysis["real_words"] < 20 else (50 if content_analysis["real_words"] < 30 else 100))

        warnings = []
        if not content_analysis["has_ad_copy"]:
            warnings.append("⚠️ CRITICAL: Ad Copy field is EMPTY")
        if content_analysis["is_short"]:
            warnings.append(f"⚠️ CRITICAL: Content too short ({content_analysis['real_words']} words)")
        warning_text = "\n".join(warnings) if warnings else "Content meets minimum requirements."

        return f"""STRICT ANALYSIS REQUEST - Use Detailed Rubrics

TARGET: {country} ({currency})
PLATFORM: {data.get('platform', 'unknown')}
INDUSTRY: {data.get('industry', 'unknown')}

CONTENT METRICS:
- Ad Copy: {len(ad_copy.strip())} chars
- Video Script: {len(video_script.strip())} chars
- Real Words: {content_analysis['real_words']}
- Maximum Score Allowed: {max_score}

WARNINGS:
{warning_text}

CONTENT TO ANALYZE:
[AD COPY START]
{ad_copy if ad_copy else "[EMPTY]"}
[AD COPY END]

[VIDEO SCRIPT START]
{video_script if video_script else "[EMPTY]"}
[VIDEO SCRIPT END]

INSTRUCTIONS:
1. Score each category using the DETAILED RUBRICS in system prompt
2. For each score, briefly justify in your reasoning (one sentence)
3. If content < 10 words, all scores max 15
4. If ad_copy empty, Hook and CTA max 20
5. Calculate Overall as weighted average
6. critical_weaknesses: List specific issues with severity
7. behavior_summary: Explain scores referencing actual content phrases

Return JSON."""

    def _enforce_score_limits(self, analysis: Dict, content_analysis: Dict) -> Dict:
        """Enforce limits"""
        scores = analysis.get("scores", {})
        max_score = 15 if content_analysis["real_words"] < 10 else (35 if content_analysis["real_words"] < 20 else (50 if content_analysis["real_words"] < 30 else 100))

        # Cap individual scores
        for key in scores:
            if scores[key] > max_score:
                scores[key] = max_score

        # Force critical weaknesses
        if content_analysis["is_short"] and not analysis.get("critical_weaknesses"):
            analysis["critical_weaknesses"] = [{
                "issue": "Content too short for effective advertising",
                "severity": "High",
                "impact": "Cannot convey value proposition or build trust",
                "fix": "Expand to minimum 50 words with clear value proposition"
            }]

        # Force behavior summary
        if len(analysis.get("behavior_summary", "")) < 20:
            analysis["behavior_summary"] = f"Content critically short ({content_analysis['real_words']} words). Insufficient for engagement or conversions. Requires substantial expansion with specific value propositions, proof, and clear CTA."

        analysis["scores"] = scores
        return analysis


def get_ai_engine():
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AIEngineV5()
    return _engine_instance


_engine_instance = None


class AIValidationError(Exception):
    pass
