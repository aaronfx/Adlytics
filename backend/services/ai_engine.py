"""
ADLYTICS AI Engine v5.0 - PRODUCTION GRADE
- Strict validation (no silent fallbacks)
- Full v5 feature set
- Long script support (20s to 60min)
- Decision Engine
- Budget Optimization
- Neuro Response Scoring
"""

import os
import json
import httpx
import re
import logging
from typing import Dict, List, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

class AIValidationError(Exception):
    """Raised when AI response is invalid"""
    pass

class AIEngineV5:
    """V5 Engine with strict validation and real AI calls"""

    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.model = OPENROUTER_MODEL
        if not self.api_key:
            logger.error("❌ OPENROUTER_API_KEY not configured")
            raise ValueError("OPENROUTER_API_KEY environment variable required")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def call_llm(self, prompt: str, system_prompt: str, temperature: float = 0.7) -> Dict:
        """Call LLM with strict validation - no silent fallbacks"""

        logger.info("🤖 Calling LLM API...")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": "https://adlytics.app",
                        "X-Title": "ADLYTICS"
                    },
                    json={
                        "model": self.model,
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
                    raise AIValidationError(f"LLM API returned {response.status_code}: {error_text}")

                data = response.json()

                if "choices" not in data or not data["choices"]:
                    logger.error(f"❌ Empty choices in response: {data}")
                    raise AIValidationError("LLM returned empty choices")

                content = data["choices"][0]["message"]["content"]
                logger.info(f"✅ Raw response length: {len(content)}")

                # Parse JSON strictly
                try:
                    parsed = json.loads(content)
                    logger.info("✅ JSON parsed successfully")
                    return parsed
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON parse error: {e}")
                    logger.error(f"Content: {content[:500]}")
                    raise AIValidationError(f"Invalid JSON from LLM: {e}")

        except httpx.TimeoutException:
            logger.error("❌ LLM API timeout")
            raise AIValidationError("LLM API timeout after 60s")
        except Exception as e:
            logger.error(f"❌ LLM call failed: {e}")
            raise AIValidationError(f"LLM call failed: {str(e)}")

    def validate_analysis_response(self, data: Dict) -> Dict:
        """Strict validation - ensures all required fields exist with real values"""

        required_sections = [
            "scores", "behavior_summary", "phase_breakdown", 
            "critical_weaknesses", "improvements", "persona_reactions",
            "roi_analysis", "line_by_line_analysis", "video_execution_analysis",
            "run_decision", "platform_specific", "competitor_advantage",
            "improved_ad", "ad_variants", "winner_prediction",
            # v5 additions
            "decision_engine", "budget_optimization", "objection_detection",
            "creative_fatigue", "neuro_response", "cross_platform"
        ]

        # Check for empty/None values
        for section in required_sections:
            if section not in data or data[section] is None:
                logger.error(f"❌ Missing required section: {section}")
                raise AIValidationError(f"LLM response missing {section}")

            if isinstance(data[section], list) and len(data[section]) == 0:
                logger.warning(f"⚠️ Empty array for {section} - may indicate incomplete analysis")

            if isinstance(data[section], dict) and len(data[section]) == 0:
                logger.error(f"❌ Empty object for {section}")
                raise AIValidationError(f"Section {section} is empty")

        # Validate scores are realistic (not all 50s)
        scores = data.get("scores", {})
        if all(score == 50 for score in scores.values() if isinstance(score, (int, float))):
            logger.error("❌ All scores are 50 - indicates fallback/default data")
            raise AIValidationError("AI returned default scores (all 50s)")

        logger.info("✅ All sections validated")
        return data

    async def analyze_ad(self, request_data: dict, files: list = None) -> Dict:
        """Main analysis with strict validation"""

        logger.info("🚀 Starting V5 Analysis")

        # 1. Build prompt
        prompt = self._build_analysis_prompt(request_data)
        system_prompt = self._get_system_prompt()

        # 2. Call LLM (with retries)
        try:
            raw_result = await self.call_llm(prompt, system_prompt, 0.7)
        except AIValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error in LLM call: {e}")
            raise AIValidationError(f"Analysis failed: {str(e)}")

        # 3. Validate response (STRICT - no fallbacks)
        validated = self.validate_analysis_response(raw_result)

        # 4. Add metadata
        validated["_metadata"] = {
            "version": "5.0",
            "model": self.model,
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

        # Build rich audience context
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
        "verdict": "<specific verdict: "Strong", "Weak", "Dies in <1s", "Moderate">",
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
    "improvements": ["<specific actionable fix 1>", "<fix 2>"],
    "persona_reactions": [
        {{
            "persona": "<Lagos Scroller|Abuja Professional|UK Compliance|US Buyer|Skeptical Beginner>",
            "reaction": "<specific response>",
            "objection": "<their specific objection>",
            "behavior": "<what they do: scroll|report|click|convert>"
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
        "scam_triggers": ["<trigger 1>", "<trigger 2>"],
        "trust_gaps": ["<gap 1>"],
        "unrealistic_claims": ["<claim 1>"],
        "compliance_risks": ["<risk 1>"]
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


# Backward compatibility
def get_ai_engine() -> AIEngineV5:
    return AIEngineV5()

__all__ = ['get_ai_engine', 'AIEngineV5', 'AIValidationError']
