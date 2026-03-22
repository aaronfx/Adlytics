"""
ADLYTICS v5.2 - AI Engine with Full Production Copy
"""

import os
import json
import logging
from typing import Dict, Any
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIEngineV5:
    """V5.2 AI Engine - Full detailed production copy for immediate use"""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
        self.base_url = "https://openrouter.ai/api/v1"

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set")

        logger.info(f"🤖 Using model: {self.model}")

    async def analyze_ad(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze ad with content verification"""
        ad_copy = request_data.get('ad_copy', '').strip()
        video_script = request_data.get('video_script', '').strip()

        if not ad_copy and not video_script:
            raise ValueError("No content provided")

        prompt = self._build_prompt(request_data, ad_copy, video_script)

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
                                {"role": "system", "content": self._get_system_prompt()},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.3,
                            "max_tokens": 8000
                        }
                    )

                    result = response.json()
                    content = result["choices"][0]["message"]["content"]

                    # Extract JSON
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]

                    analysis = json.loads(content.strip())
                    self._verify_analysis(analysis, ad_copy, video_script)

                    return analysis

            except Exception as e:
                logger.warning(f"Attempt {attempt+1} failed: {e}")
                if attempt == 2:
                    raise

        raise ValueError("Analysis failed")

    def _get_system_prompt(self) -> str:
        return """You are an elite performance marketing strategist creating FULL PRODUCTION ADS.

CRITICAL RULES:
1. Generate COMPLETE, READY-TO-RUN ad copy - not summaries or outlines
2. Hook: 15-30 words that stop the scroll (specific, emotional, curiosity-driven)
3. Body: 100-200 words minimum with full persuasion structure (problem, agitation, solution, proof, offer)
4. CTA: 5-10 words, action-oriented, urgency or benefit-driven
5. Each variant must be different ANGLE but FULL COPY - enough to run A/B test immediately
6. improved_ad must combine the BEST elements into one polished, long-form ad (200+ words)
7. Video scripts must be full 30-60 second read time with specific visual directions [VISUAL: ...]
8. Reference actual content phrases in your analysis - prove you read the input
9. If content is weak/empty, scores 10-40; only 70+ if genuinely strong

The user will COPY-PASTE your output directly into Meta Ads Manager. Make it complete."""

    def _build_prompt(self, data: Dict, ad_copy: str, video_script: str) -> str:
        content = ad_copy + video_script
        is_short = len(content) < 50
        is_gibberish = len([w for w in content.split() if len(w) > 2 and w.isalpha()]) < 2

        quality_note = ""
        if not ad_copy:
            quality_note = "⚠️ NO AD COPY - All scores should be 10-25"
        elif is_gibberish:
            quality_note = "⚠️ GIBBERISH CONTENT - Clarity/Credibility 5-20"
        elif is_short:
            quality_note = "⚠️ SHORT CONTENT - Scores 20-40"

        return f"""Analyze this ad content and generate FULL PRODUCTION-READY variants:

{quality_note}

ORIGINAL AD COPY:
```
{ad_copy or "[EMPTY]"}
```

ORIGINAL VIDEO SCRIPT:
```
{video_script or "[EMPTY]"}
```

PLATFORM: {data.get('platform', 'unknown')}
INDUSTRY: {data.get('industry', 'unknown')}

INSTRUCTIONS:
Create 5 COMPLETE ad variants (100-200 words each) + 1 final improved version (200+ words).
Each variant must be different angle but FULL COPY - ready to paste into Ads Manager.

Return JSON:
{{
  "scores": {{
    "overall": 0-100,
    "hook_strength": 0-100,
    "clarity": 0-100,
    "credibility": 0-100,
    "emotional_pull": 0-100,
    "cta_strength": 0-100,
    "audience_match": 0-100,
    "platform_fit": 0-100
  }},
  "behavior_summary": "Detailed analysis referencing actual content (150+ chars)",
  "critical_weaknesses": [{{"issue": "...", "severity": "High/Medium/Low", "impact": "...", "fix": "..."}}],
  "decision_engine": {{
    "should_run": true/false,
    "confidence": "0-100%",
    "reasoning": "Detailed (150+ chars)",
    "expected_profit": number,
    "roi_prediction": "X.Xx",
    "profit_scenarios": {{"low_case": number, "base_case": number, "high_case": number}},
    "kill_threshold": "...",
    "scale_threshold": "...",
    "confidence_breakdown": {{"hook": 0-100, "offer": 0-100, "audience": 0-100}}
  }},
  "budget_optimization": {{
    "break_even_cpc": number,
    "safe_test_budget": number,
    "budget_phases": ["...", "...", "..."],
    "risk_level": "Low/Medium/High",
    "worst_case_loss": number,
    "scaling_rule": "...",
    "scaling_risk": "...",
    "budget_tip": "..."
  }},
  "neuro_response": {{
    "dopamine": 0-100,
    "fear": 0-100,
    "curiosity": 0-100,
    "urgency": 0-100,
    "trust": 0-100,
    "primary_driver": "...",
    "emotional_triggers": ["...", "...", "..."],
    "psychological_gaps": ["...", "..."]
  }},
  "ad_variants": [
    {{
      "id": 1,
      "angle": "Name of approach (e.g., Success Story, Fear of Loss, Educational)",
      "hook": "15-30 word scroll-stopping headline",
      "body": "100-200 words with full structure: problem -> agitation -> solution -> social proof -> offer. Multiple paragraphs allowed.",
      "cta": "5-10 word action button text",
      "predicted_score": 0-100,
      "why_it_works": "Explanation of psychological triggers used"
    }},
    {{"id": 2, "angle": "...", "hook": "...", "body": "100-200 words...", "cta": "...", "predicted_score": 0-100, "why_it_works": "..."}},
    {{"id": 3, "angle": "...", "hook": "...", "body": "100-200 words...", "cta": "...", "predicted_score": 0-100, "why_it_works": "..."}},
    {{"id": 4, "angle": "...", "hook": "...", "body": "100-200 words...", "cta": "...", "predicted_score": 0-100, "why_it_works": "..."}},
    {{"id": 5, "angle": "...", "hook": "...", "body": "100-200 words...", "cta": "...", "predicted_score": 0-100, "why_it_works": "..."}}
  ],
  "improved_ad": {{
    "final_hook": "Optimized 15-30 word headline combining best elements",
    "final_body": "200+ words polished ad copy with proper flow, transitions, persuasion elements. Ready to paste into Meta Ads. Include paragraph breaks.",
    "final_cta": "Optimized 5-10 word call-to-action",
    "video_script_ready": "Full 30-60 second video script with [VISUAL: camera angle/shot] and [AUDIO: voiceover text] directions. Timecodes [0-3s], [3-15s], [15-30s].",
    "key_changes_made": ["Specific improvement 1", "Specific improvement 2", "Specific improvement 3", "Specific improvement 4"]
  }},
  "winner_prediction": {{"winner_id": number, "angle": "...", "confidence": "...", "reasoning": "..."}},
  "objection_detection": {{
    "scam_triggers": [{{"trigger": "...", "severity": "..."}}],
    "trust_gaps": [{{"gap": "...", "severity": "..."}}],
    "compliance_risks": [{{"risk": "...", "platform": "..."}}]
  }},
  "creative_fatigue": {{
    "fatigue_level": "Low/Medium/High",
    "estimated_decline_days": number,
    "explanation": "...",
    "refresh_needed": true/false,
    "refresh_recommendations": ["...", "...", "..."]
  }},
  "cross_platform": {{
    "facebook": {{"score": 0-100, "adapted_copy": "...", "changes_needed": "..."}},
    "tiktok": {{"score": 0-100, "adapted_copy": "...", "changes_needed": "..."}},
    "youtube": {{"score": 0-100, "adapted_copy": "...", "changes_needed": "..."}}
  }},
  "video_execution_analysis": {{
    "hook_delivery": "Analysis of opening 0-3 seconds (60+ words)",
    "speech_flow": "Pacing and rhythm assessment (40+ words)",
    "visual_dependency": "How much relies on visuals vs audio (40+ words)",
    "delivery_risk": "Potential execution challenges (40+ words)",
    "format_recommendation": "talking_head/UGC/screen_recording/mixed",
    "competitor_advantage": "How to beat competitors with this video (50+ words)",
    "timecode_breakdown": [
      {{"segment": "HOOK 0-3s", "content": "What happens visually and audibly", "effectiveness": 0-100}},
      {{"segment": "BODY 3-15s", "content": "What happens visually and audibly", "effectiveness": 0-100}},
      {{"segment": "CTA 15-30s", "content": "What happens visually and audibly", "effectiveness": 0-100}}
    ]
  }},
  "persona_reactions": [
    {{"name": "...", "demographic": "...", "reaction": "...", "pain_points": ["..."], "objections": ["..."], "conversion_likelihood": "..."}}
  ],
  "line_by_line_analysis": [
    {{"line_number": 1, "text": "...", "strength": 0-10, "assessment": "...", "issue": "...", "suggestion": "..."}}
  ],
  "phase_breakdown": {{
    "hook_phase": "...",
    "body_phase": "...",
    "cta_phase": "..."
  }},
  "roi_comparison": {{
    "your_projection": "X.Xx",
    "industry_average": "X.Xx",
    "top_performer": "X.Xx",
    "gap_analysis": "Detailed comparison of where user stands vs industry (100+ words)"
  }},
  "competitor_advantage": {{
    "unique_angles": ["Angle 1", "Angle 2", "Angle 3"],
    "defensible_moat": "What makes this hard to copy (80+ words)",
    "vulnerability": "Weakness competitors could exploit (60+ words)"
  }}
}}

CRITICAL: 
- Body text in variants MUST be 100-200 words (not 1-2 sentences)
- improved_ad body MUST be 200+ words (production ready)
- Each variant is a COMPLETE ad, not a summary
- Hook must be 15-30 words (specific and emotional)
"""

    def _verify_analysis(self, analysis: Dict, ad_copy: str, video_script: str) -> None:
        """Verify real analysis and content length"""
        scores = analysis.get("scores", {})
        content = (ad_copy + video_script).strip()
        content_len = len(content)

        # Check empty content
        if content_len < 10 and scores.get("overall", 100) > 30:
            raise ValueError(f"Empty content got high score: {scores.get('overall')}")

        # Check gibberish
        real_words = len([w for w in content.split() if len(w) > 2 and w.isalpha()])
        if real_words < 2 and content_len > 5:
            if scores.get("clarity", 100) > 30:
                raise ValueError("Gibberish got good clarity score")

        # Check short content
        if content_len < 50 and scores.get("overall", 100) > 50:
            raise ValueError(f"Short content got high score: {scores.get('overall')}")

        # Verify improved_ad exists and has required fields with length
        improved = analysis.get("improved_ad", {})
        if not improved.get("final_hook") or not improved.get("final_body"):
            raise ValueError("Missing improved_ad production fields")

        # Verify body length (should be substantial, not 1-2 sentences)
        body_words = len(improved.get("final_body", "").split())
        if body_words < 50:
            raise ValueError(f"improved_ad.body too short: {body_words} words (expected 200+)")

        # Verify 5 variants
        variants = analysis.get("ad_variants", [])
        if len(variants) < 5:
            raise ValueError(f"Expected 5 variants, got {len(variants)}")

        # Check variant body lengths
        for i, variant in enumerate(variants):
            var_body_words = len(variant.get("body", "").split())
            if var_body_words < 30:
                raise ValueError(f"Variant {i+1} body too short: {var_body_words} words (expected 100+)")

        logger.info(f"✅ Verified: {content_len} chars, score: {scores.get('overall')}, variants: {len(variants)}, improved_body: {body_words} words")


_engine_instance = None

def get_ai_engine():
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AIEngineV5()
    return _engine_instance


class AIValidationError(Exception):
    pass
