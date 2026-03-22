"""
ADLYTICS v5.0 - STRICT VALIDATION ENGINE
No fallbacks. No auto-fill. Force AI to do the work.
"""

import os
import json
import logging
from typing import Dict, Any
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIEngineStrictV5:
    """Strict engine - no fallbacks, forces quality through validation"""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "anthropic/claude-3.5-sonnet"

    async def analyze_ad(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main analysis with STRICT validation - NO FALLBACKS"""

        prompt = self._build_strict_prompt(request_data)
        last_error = None

        # Try up to 3 times with escalating pressure
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
                                {
                                    "role": "system",
                                    "content": self._get_elite_system_prompt()
                                },
                                {
                                    "role": "user", 
                                    "content": prompt
                                }
                            ],
                            "temperature": 0.4,  # LOWER for consistency
                            "max_tokens": 7000,  # HIGHER for depth
                            "response_format": { "type": "json_object" }
                        }
                    )

                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    analysis = json.loads(content)

                    # STRICT VALIDATION - NO MERCY
                    validated = self._validate_strict_output(analysis)

                    logger.info("✅ AI output passed strict validation")
                    return validated

            except Exception as e:
                last_error = str(e)
                logger.warning(f"❌ Validation failed (attempt {attempt+1}): {e}")

                # Add pressure for next attempt
                prompt += f"

⚠️ CRITICAL: Your previous response failed validation: {e}
"
                prompt += "You MUST expand ALL sections significantly. Do NOT return shallow output.
"
                prompt += "Every field must have detailed content. Arrays must have 3+ items.
"

        # All retries failed - RETURN ERROR (don't fake it)
        logger.error(f"AI failed after 3 attempts: {last_error}")
        raise ValueError(f"AI unable to produce valid deep output: {last_error}")

    def _get_elite_system_prompt(self) -> str:
        """ELITE STRATEGIST - NO EXCUSES"""
        return """You are an elite performance marketing strategist + behavioral psychologist + media buyer.

Your task: Return DEEP, MULTI-LAYERED, PRODUCTION-GRADE JSON.

⚠️ CRITICAL RULES (VIOLATION = REJECTION):

1. NEVER return shallow output
2. NEVER return short answers
3. NEVER skip fields
4. EVERY section must have reasoning + breakdown + multiple data points
5. If output feels "simple" → EXPAND IT
6. You are SIMULATING real ad performance, not describing

STRICT REQUIREMENTS:
- All scores must be realistic (0-100)
- All explanations must be 100+ characters
- All arrays must have 3+ items
- All objects must have nested details
- Use specific numbers, not vague terms

You are a $10,000/month strategist. Act like it."""

    def _build_strict_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt WITHOUT example JSON trap"""
        return f"""Analyze this ad and return STRICT JSON with MAXIMUM DEPTH.

AD INPUT:
- Platform: {data.get('platform', 'unknown')}
- Industry: {data.get('industry', 'unknown')}
- Target: {data.get('audience_age', '')} in {data.get('audience_country', '')}
- Copy: {data.get('ad_copy', '')[0:1000]}

REQUIRED JSON STRUCTURE (EXPAND EVERY FIELD):

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

  "behavior_summary": "DETAILED step-by-step user reaction flow (200+ chars)",

  "critical_weaknesses": [
    {{"issue": "...", "severity": "High/Medium/Low", "impact": "...", "fix": "..."}},
    {{"issue": "...", "severity": "High/Medium/Low", "impact": "...", "fix": "..."}}
  ],

  "decision_engine": {{
    "should_run": true/false,
    "confidence": "0-100%",
    "reasoning": "DETAILED explanation (200+ chars)",
    "expected_profit": number,
    "roi_prediction": "X.Xx",
    "profit_scenarios": {{"low_case": number, "base_case": number, "high_case": number}},
    "kill_threshold": "specific condition",
    "scale_threshold": "specific condition",
    "confidence_breakdown": {{"hook": 0-100, "offer": 0-100, "audience": 0-100}}
  }},

  "budget_optimization": {{
    "break_even_cpc": number,
    "safe_test_budget": number,
    "budget_phases": ["phase 1", "phase 2", "phase 3"],
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
    "emotional_triggers": ["trigger 1", "trigger 2", "trigger 3"],
    "psychological_gaps": ["gap 1", "gap 2"]
  }},

  "ad_variants": [
    {{
      "id": 1,
      "angle": "Fear/Curiosity/Authority",
      "hook": "...",
      "body": "...",
      "cta": "...",
      "predicted_score": 0-100,
      "why_it_works": "DETAILED psychology (150+ chars)"
    }},
    {{"id": 2, ...}},
    {{"id": 3, ...}}
  ],

  "winner_prediction": {{
    "winner_id": number,
    "angle": "...",
    "confidence": "0-100%",
    "reasoning": "..."
  }},

  "objection_detection": {{
    "scam_triggers": [{{"trigger": "...", "severity": "High/Medium/Low"}}],
    "trust_gaps": [{{"gap": "...", "severity": "High/Medium/Low"}}],
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
    {{
      "name": "...",
      "demographic": "...",
      "reaction": "...",
      "pain_points": ["...", "..."],
      "objections": ["...", "..."],
      "conversion_likelihood": "0-100%"
    }},
    {{...}},
    {{...}}
  ],

  "line_by_line_analysis": [
    {{"line_number": 1, "text": "...", "strength": 0-10, "assessment": "strong/weak/neutral", "issue": "...", "suggestion": "..."}},
    {{...}},
    {{...}}
  ],

  "phase_breakdown": {{
    "hook_phase": "...",
    "body_phase": "...",
    "cta_phase": "..."
  }},

  "roi_comparison": "text (100+ chars)",
  "competitor_advantage": "text (100+ chars)"
}}

⚠️ VALIDATION RULES:
1. ALL 8 scores must be 0-100 (no zeros unless truly terrible)
2. ALL arrays must have 3+ items
3. ALL text fields must be detailed (not single words)
4. behavior_summary must be 200+ characters
5. reasoning fields must be 150+ characters
6. why_it_works must explain PSYCHOLOGY

DO NOT RETURN SHALLOW OUTPUT. YOU WILL FAIL VALIDATION."""

    def _validate_strict_output(self, data: Dict) -> Dict:
        """STRICT VALIDATION - NO MERCY, NO FALLBACK"""

        # 1. Check required sections exist
        required_sections = [
            "scores", "behavior_summary", "critical_weaknesses", "decision_engine",
            "budget_optimization", "neuro_response", "ad_variants", "winner_prediction",
            "objection_detection", "creative_fatigue", "cross_platform", 
            "persona_reactions", "line_by_line_analysis", "phase_breakdown",
            "roi_comparison", "competitor_advantage"
        ]

        for section in required_sections:
            if section not in data:
                raise ValueError(f"Missing required section: {section}")

        # 2. Validate scores
        scores = data.get("scores", {})
        required_scores = ["overall", "hook_strength", "clarity", "credibility", 
                          "emotional_pull", "cta_strength", "audience_match", "platform_fit"]
        for score_key in required_scores:
            if score_key not in scores or scores[score_key] == 0:
                raise ValueError(f"Score '{score_key}' missing or zero")
            if not isinstance(scores[score_key], (int, float)):
                raise ValueError(f"Score '{score_key}' must be a number")

        # 3. Validate array lengths (MUST have 3+ items)
        if len(data.get("ad_variants", [])) < 3:
            raise ValueError(f"ad_variants must have 3+ items, got {len(data.get('ad_variants', []))}")

        if len(data.get("persona_reactions", [])) < 3:
            raise ValueError(f"persona_reactions must have 3+ items, got {len(data.get('persona_reactions', []))}")

        neuro = data.get("neuro_response", {})
        if len(neuro.get("emotional_triggers", [])) < 3:
            raise ValueError("neuro_response.emotional_triggers must have 3+ items")
        if len(neuro.get("psychological_gaps", [])) < 2:
            raise ValueError("neuro_response.psychological_gaps must have 2+ items")

        budget = data.get("budget_optimization", {})
        if len(budget.get("budget_phases", [])) < 3:
            raise ValueError("budget_optimization.budget_phases must have 3+ items")

        fatigue = data.get("creative_fatigue", {})
        if len(fatigue.get("refresh_recommendations", [])) < 3:
            raise ValueError("creative_fatigue.refresh_recommendations must have 3+ items")

        # 4. Validate decision engine has nested objects
        decision = data.get("decision_engine", {})
        if "profit_scenarios" not in decision:
            raise ValueError("decision_engine missing profit_scenarios")
        if "confidence_breakdown" not in decision:
            raise ValueError("decision_engine missing confidence_breakdown")
        if "kill_threshold" not in decision or "scale_threshold" not in decision:
            raise ValueError("decision_engine missing thresholds")

        # 5. Validate text field lengths (MUST be detailed)
        behavior = data.get("behavior_summary", "")
        if len(behavior) < 100:
            raise ValueError(f"behavior_summary too short ({len(behavior)} chars), need 100+")

        reasoning = decision.get("reasoning", "")
        if len(reasoning) < 100:
            raise ValueError(f"decision_engine.reasoning too short ({len(reasoning)} chars), need 100+")

        # 6. Validate variants have required fields
        for i, variant in enumerate(data.get("ad_variants", [])):
            required_variant_fields = ["id", "angle", "hook", "body", "cta", "predicted_score", "why_it_works"]
            for field in required_variant_fields:
                if field not in variant or not variant[field]:
                    raise ValueError(f"ad_variants[{i}] missing field: {field}")
            if len(variant.get("why_it_works", "")) < 50:
                raise ValueError(f"ad_variants[{i}].why_it_works too short, need 50+ chars")

        # 7. Validate personas have required fields
        for i, persona in enumerate(data.get("persona_reactions", [])):
            required_persona_fields = ["name", "demographic", "reaction", "pain_points", "objections", "conversion_likelihood"]
            for field in required_persona_fields:
                if field not in persona:
                    raise ValueError(f"persona_reactions[{i}] missing field: {field}")
            if len(persona.get("pain_points", [])) < 2:
                raise ValueError(f"persona_reactions[{i}] needs 2+ pain_points")
            if len(persona.get("objections", [])) < 2:
                raise ValueError(f"persona_reactions[{i}] needs 2+ objections")

        # 8. Validate line_by_line_analysis
        lines = data.get("line_by_line_analysis", [])
        if len(lines) < 3:
            raise ValueError(f"line_by_line_analysis must have 3+ items, got {len(lines)}")
        for i, line in enumerate(lines):
            if "line_number" not in line or "text" not in line or "strength" not in line:
                raise ValueError(f"line_by_line_analysis[{i}] missing required fields")

        # 9. Validate phase_breakdown has all phases
        phases = data.get("phase_breakdown", {})
        required_phases = ["hook_phase", "body_phase", "cta_phase"]
        for phase in required_phases:
            if phase not in phases or len(phases.get(phase, "")) < 20:
                raise ValueError(f"phase_breakdown.{phase} missing or too short")

        # 10. Validate cross_platform has all platforms
        platforms = data.get("cross_platform", {})
        required_platforms = ["facebook", "tiktok", "youtube"]
        for platform in required_platforms:
            if platform not in platforms:
                raise ValueError(f"cross_platform missing {platform}")
            plat = platforms[platform]
            if "score" not in plat or "adapted_copy" not in plat or "changes_needed" not in plat:
                raise ValueError(f"cross_platform.{platform} missing required fields")

        # All validations passed
        return data

# Singleton
_engine_instance = None

def get_ai_engine():
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AIEngineStrictV5()
    return _engine_instance

class AIValidationError(Exception):
    pass
