"""
ADLYTICS AI Engine v5.0 - ENHANCED PRODUCTION GRADE
- Strict validation (no silent fallbacks)
- Model fallback strategy
- Enhanced error handling
- Long script support (20s to 60min)
"""

import os
import json
import httpx
import logging
from typing import Dict, List, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# ISSUE 5 FIX: Model fallback strategy
FALLBACK_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3.5-haiku",
    "openai/gpt-4o-mini",
    "google/gemini-flash-1.5"
]

class AIValidationError(Exception):
    """Raised when AI response is invalid"""
    pass

class AIEngineV5:
    """V5 Engine with strict validation and fallback support"""

    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        if not self.api_key:
            logger.error("❌ OPENROUTER_API_KEY not configured")
            raise ValueError("OPENROUTER_API_KEY environment variable required")

        self.current_model_index = 0

    async def call_llm_with_fallback(self, prompt: str, system_prompt: str, temperature: float = 0.7) -> Dict:
        """Call LLM with automatic model fallback"""

        last_error = None

        # ISSUE 5 FIX: Try each model in sequence
        for model in FALLBACK_MODELS[self.current_model_index:]:
            try:
                logger.info(f"🤖 Trying model: {model}")
                result = await self._call_single_model(model, prompt, system_prompt, temperature)

                # If successful, remember this model for next time
                self.current_model_index = FALLBACK_MODELS.index(model)
                logger.info(f"✅ Success with {model}")
                return result

            except Exception as e:
                logger.warning(f"⚠️ Model {model} failed: {e}")
                last_error = e
                continue

        # All models failed
        logger.error("❌ All models failed")
        raise AIValidationError(f"All models exhausted. Last error: {last_error}")

    async def _call_single_model(self, model: str, prompt: str, system_prompt: str, temperature: float) -> Dict:
        """Call a single model"""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://adlytics.app",
                    "X-Title": "ADLYTICS"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": 4000,
                    "response_format": {"type": "json_object"}
                }
            )

            if response.status_code != 200:
                error_text = response.text
                logger.error(f"❌ API error {response.status_code}: {error_text}")
                raise AIValidationError(f"Model {model} returned {response.status_code}")

            data = response.json()

            if "choices" not in data or not data["choices"]:
                raise AIValidationError(f"Model {model} returned empty choices")

            content = data["choices"][0]["message"]["content"]
            logger.info(f"✅ Response from {model}, length: {len(content)}")

            try:
                parsed = json.loads(content)
                return parsed
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parse error from {model}: {e}")
                raise AIValidationError(f"Invalid JSON from {model}")

    def validate_analysis_response(self, data: Dict) -> Dict:
        """ISSUE 4 FIX: Strict validation with better error messages"""

        if not isinstance(data, dict):
            raise AIValidationError(f"AI response is not a dict, got: {type(data)}")

        required_sections = [
            "scores", "behavior_summary", "phase_breakdown", 
            "critical_weaknesses", "improvements", "persona_reactions",
            "roi_analysis", "line_by_line_analysis", "video_execution_analysis",
            "run_decision", "platform_specific", "competitor_advantage",
            "improved_ad", "ad_variants", "winner_prediction",
            "decision_engine", "budget_optimization", "objection_detection",
            "creative_fatigue", "neuro_response", "cross_platform"
        ]

        missing_sections = []
        empty_sections = []

        for section in required_sections:
            if section not in data:
                missing_sections.append(section)
            elif data[section] is None:
                missing_sections.append(f"{section} (null)")
            elif isinstance(data[section], dict) and len(data[section]) == 0:
                empty_sections.append(section)
            elif isinstance(data[section], list) and len(data[section]) == 0 and section in ['critical_weaknesses', 'improvements', 'ad_variants']:
                # These can be empty but we should warn
                logger.warning(f"⚠️ Empty array for {section}")

        if missing_sections:
            error_msg = f"LLM response missing sections: {', '.join(missing_sections)}"
            logger.error(f"❌ {error_msg}")
            raise AIValidationError(error_msg)

        if empty_sections:
            logger.warning(f"⚠️ Empty sections: {', '.join(empty_sections)}")

        # Validate scores are realistic
        scores = data.get("scores", {})
        if isinstance(scores, dict):
            score_values = [v for v in scores.values() if isinstance(v, (int, float))]
            if score_values and all(score == 50 for score in score_values):
                raise AIValidationError("AI returned default scores (all 50s)")
            if score_values and all(score == 0 for score in score_values):
                raise AIValidationError("AI returned all zeros")

        logger.info("✅ All sections validated successfully")
        return data

    async def analyze_ad(self, request_data: dict, files: list = None) -> Dict:
        """Main analysis with enhanced error handling"""

        logger.info("🚀 Starting V5 Analysis with Fallback")

        # 1. Build prompt
        prompt = self._build_analysis_prompt(request_data)
        system_prompt = self._get_system_prompt()

        # 2. Call LLM with fallback (ISSUE 5)
        try:
            raw_result = await self.call_llm_with_fallback(prompt, system_prompt, 0.7)
        except AIValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ LLM call failed: {e}")
            logger.error(traceback.format_exc())
            raise AIValidationError(f"Analysis failed: {str(e)}")

        # 3. ISSUE 4 FIX: Enhanced validation with detailed errors
        try:
            validated = self.validate_analysis_response(raw_result)
        except AIValidationError:
            # Re-raise with context
            raise
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            raise AIValidationError(f"Response validation failed: {str(e)}")

        # 4. Add metadata
        validated["_metadata"] = {
            "version": "5.0",
            "model_used": FALLBACK_MODELS[self.current_model_index],
            "content_mode": self._detect_content_mode(request_data)
        }

        logger.info("✅ Analysis complete and validated")
        return validated

    def _detect_content_mode(self, request_data: dict) -> str:
        has_ad = bool(request_data.get("ad_copy", "").strip())
        has_video = bool(request_data.get("video_script", "").strip())

        if has_video and not has_ad:
            return "videoScript"
        elif has_ad and has_video:
            return "both"
        else:
            return "adCopy"

    def _get_system_prompt(self) -> str:
        return """You are ADLYTICS V5 - the ultimate ad pre-validation engine.

You embody 6 expert personas simultaneously:
1. Performance Marketing Strategist (ROI optimization)
2. Behavioral Psychologist (cognitive biases, decision making)
3. Direct-Response Copywriter (conversion optimization)
4. Video Ad Strategist (execution feasibility, speech flow)
5. Conservative Risk Analyst (compliance, realistic forecasting)
6. Cross-Platform Media Buyer (Facebook, TikTok, YouTube specifics)

CRITICAL RULES:
- Return ONLY valid JSON
- NO placeholder values (no "Analysis Pending", no "50/100" defaults)
- ALL fields must contain specific, computed analysis
- If you cannot analyze, return an error message, not fake data
- Scores must vary (0-100) based on actual quality

SCORING RUBRIC:
- 0-20: Fatal flaws, guaranteed failure
- 21-40: Critical issues, unlikely to profit
- 41-60: Marginal, needs fixes to break even
- 61-80: Good, likely profitable with optimization
- 81-100: Excellent, high probability of strong ROAS"""

    def _build_analysis_prompt(self, data: dict) -> str:
        ad_copy = data.get("ad_copy", "")
        video_script = data.get("video_script", "")
        platform = data.get("platform", "facebook")
        industry = data.get("industry", "general")

        audience_context = self._build_audience_context(data)

        content_section = ""
        if ad_copy and video_script:
            content_section = f"""
AD COPY (Static):
{ad_copy}

VIDEO SCRIPT (Spoken):
{video_script}
"""
        elif video_script:
            content_section = f"""
VIDEO SCRIPT (Spoken Content):
{video_script}
"""
        else:
            content_section = f"""
AD COPY:
{ad_copy}
"""

        return f"""Analyze this ad for {platform.upper()} targeting {audience_context}.

{content_section}

Return COMPLETE JSON with ALL fields populated:

{{
    "scores": {{
        "overall": <0-100>,
        "hook_strength": <0-100>,
        "clarity": <0-100>,
        "trust_building": <0-100>,
        "cta_power": <0-100>,
        "audience_alignment": <0-100>
    }},
    "behavior_summary": {{
        "verdict": "<specific verdict>",
        "launch_readiness": "<%>",
        "failure_risk": "<%>",
        "primary_reason": "<specific behavioral reason>"
    }},
    "phase_breakdown": {{
        "micro_stop_0_1s": "<what happens in first second>",
        "scroll_stop_1_2s": "<why they stop or scroll>",
        "attention_2_5s": "<engagement or bounce>",
        "trust_evaluation": "<credibility check>",
        "click_and_post_click": "<conversion likelihood>"
    }},
    "critical_weaknesses": [
        {{
            "issue": "<specific problem>",
            "behavior_impact": "<how it hurts performance>",
            "precise_fix": "<exact fix>",
            "severity": "<critical|high|medium|low>"
        }}
    ],
    "improvements": ["<specific actionable fix>"],
    "persona_reactions": [
        {{
            "persona": "<Lagos Scroller|Abuja Professional|UK Compliance|US Buyer|Skeptical Beginner>",
            "reaction": "<specific response>",
            "objection": "<their specific objection>",
            "behavior": "<what they do: scroll|report|click|convert>",
            "likelihood_to_convert": <0.0-1.0>
        }}
    ],
    "roi_analysis": {{
        "roi_potential": "<Ultra Low|Low|Medium|High|Very High>",
        "break_even_probability": "<%>",
        "risk_classification": "<Ultra High|High|Medium|Low>",
        "key_metrics": {{
            "expected_ctr_range": "<X%-Y%>",
            "realistic_cpc_range": "<$X-$Y>",
            "conversion_rate_range": "<X%-Y%>"
        }},
        "roi_scenarios": {{
            "worst_case": "<ROAS>",
            "expected_case": "<ROAS>",
            "best_case": "<ROAS>"
        }}
    }},
    "video_execution_analysis": {{
        "is_video_script": "<Yes|No>",
        "hook_delivery_strength": "<Weak|Moderate|Strong>",
        "speech_flow_quality": "<Choppy|Natural|Excellent>",
        "visual_dependency": "<Low|Medium|High>",
        "delivery_risk": "<Low|Medium|High>",
        "recommended_format": "<talking head|UGC|screen recording|mixed>",
        "biggest_execution_gap": "<specific issue>"
    }},
    "run_decision": {{
        "should_run": <true|false>,
        "risk_level": "<Ultra High|High|Medium|Low>",
        "reason": "<specific reason>",
        "confidence": "<%>"
    }},
    "platform_specific": {{
        "platform": "{platform}",
        "core_behavior": "<platform user behavior>",
        "fatal_flaw": "<platform-specific killer>",
        "platform_specific_fix": "<fix>"
    }},
    "competitor_advantage": {{
        "why_user_might_choose_competitor": "<reason>",
        "what_competitor_is_doing_better": "<specific advantage>",
        "how_to_outperform": "<strategy>"
    }},
    "improved_ad": {{
        "headline": "<optimized headline>",
        "body_copy": "<optimized body>",
        "cta": "<optimized CTA>",
        "predicted_score": <number>,
        "angle": "<psychological angle used>"
    }},
    "ad_variants": [
        {{
            "id": 1,
            "angle": "<Fear|Curiosity|Authority|Urgency|Exclusivity>",
            "hook": "<variant hook>",
            "copy": "<full variant copy>",
            "predicted_score": <number>,
            "psychological_trigger": "<specific trigger>"
        }}
    ],
    "winner_prediction": {{
        "best_variant_id": <number>,
        "score": <number>,
        "confidence": "<low|medium|high>",
        "reason": "<why this wins>"
    }},
    "decision_engine": {{
        "should_run": <true|false>,
        "confidence": "<%>",
        "expected_profit": <number>,
        "recommended_budget": <number>,
        "kill_threshold": "<specific metric that kills the ad>",
        "go_threshold": "<specific metric for scaling>"
    }},
    "budget_optimization": {{
        "break_even_cpc": <number>,
        "safe_test_budget": <number>,
        "scaling_rule": "<when to scale>",
        "daily_budget_cap": <number>,
        "expected_cpa": <number>
    }},
    "objection_detection": {{
        "scam_triggers": ["<trigger>"],
        "trust_gaps": ["<gap>"],
        "unrealistic_claims": ["<claim>"],
        "compliance_risks": ["<risk>"]
    }},
    "creative_fatigue": {{
        "fatigue_level": "<Low|Medium|High>",
        "estimated_decline_time": "<X days/weeks>",
        "refresh_needed": <true|false>,
        "variation_recommendation": "<when to rotate>"
    }},
    "neuro_response": {{
        "dopamine": <0-100>,
        "fear": <0-100>,
        "curiosity": <0-100>,
        "urgency": <0-100>,
        "trust": <0-100>,
        "primary_driver": "<dopamine|fear|curiosity|trust>"
    }},
    "cross_platform": {{
        "facebook": {{
            "adapted_copy": "<Facebook version>",
            "score": <number>,
            "changes": "<what changed>"
        }},
        "tiktok": {{
            "adapted_copy": "<TikTok version>",
            "score": <number>,
            "changes": "<what changed>"
        }},
        "youtube_shorts": {{
            "adapted_copy": "<YouTube version>",
            "score": <number>,
            "changes": "<what changed>"
        }}
    }}
}}

CRITICAL: Return ONLY the JSON. No markdown, no explanation."""

    def _build_audience_context(self, data: dict) -> str:
        parts = []
        if data.get("audience_country"):
            parts.append(data["audience_country"].upper())
        if data.get("audience_age"):
            parts.append(data["audience_age"])
        if data.get("audience_occupation"):
            parts.append(data["audience_occupation"].replace("-", " ").title())
        if data.get("audience_income"):
            parts.append(f"{data['audience_income']} income")
        if data.get("audience_pain_point"):
            parts.append(f"Pain: {data['audience_pain_point']}")

        return " | ".join(parts) if parts else "General Audience"


# Singleton instance
_engine_instance = None

def get_ai_engine() -> AIEngineV5:
    """Get or create AI Engine singleton instance"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AIEngineV5()
    return _engine_instance

__all__ = ['get_ai_engine', 'AIEngineV5', 'AIValidationError']
