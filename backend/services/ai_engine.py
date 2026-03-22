"""
ADLYTICS v5.0 - AI Engine with Real Content Analysis
"""

import os
import json
import logging
from typing import Dict, Any
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIEngineV5:
    """V5 AI Engine - Real content analysis"""

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
                            "max_tokens": 7000
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
        return """You are an elite performance marketing strategist. 

CRITICAL: Analyze the ACTUAL content provided. Do not use templates.

RULES:
1. Read the specific text provided
2. If content is weak/empty/gibberish, scores MUST be low (10-40)
3. Reference specific phrases in your analysis
4. Empty fields = score 0-15
5. Gibberish = scores 5-20
6. Only scores 70+ if content demonstrates quality

You will be verified - fake high scores will be rejected."""

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

        return f"""Analyze this ad content:

{quality_note}

AD COPY:
```
{ad_copy or "[EMPTY]"}
```

VIDEO SCRIPT:
```
{video_script or "[EMPTY]"}
```

PLATFORM: {data.get('platform', 'unknown')}
INDUSTRY: {data.get('industry', 'unknown')}

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
    {{"id": 1, "angle": "...", "hook": "...", "body": "...", "cta": "...", "predicted_score": 0-100, "why_it_works": "..."}},
    {{"id": 2, ...}},
    {{"id": 3, ...}}
  ],
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
  "roi_comparison": "...",
  "competitor_advantage": "..."
}}

Analyze the ACTUAL text above."""

    def _verify_analysis(self, analysis: Dict, ad_copy: str, video_script: str) -> None:
        """Verify real analysis"""
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

        logger.info(f"Verified: {content_len} chars, score: {scores.get('overall')}")


_engine_instance = None

def get_ai_engine():
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AIEngineV5()
    return _engine_instance


class AIValidationError(Exception):
    pass
