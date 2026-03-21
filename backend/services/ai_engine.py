"""
ADLYTICS - AI Ad Pre-Validation & ROI Simulator v4.0
AI Engine Service - OpenRouter Integration
Uses OpenRouter API with GPT-4o Mini for cost-efficient, high-quality analysis
"""

import os
import json
import re
from typing import Dict, Any, Optional, List
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-4o-mini"  # Cost-effective, fast, JSON-capable

# ULTIMATE AD PRE-VALIDATOR v4.0 Prompt
AD_VALIDATION_PROMPT = """You are ULTIMATE AD PRE-VALIDATOR v4.0
You are not an assistant. You are a high-stakes ad decision engine.

You combine:
- Performance marketing strategist
- Behavioral psychologist  
- Direct-response copywriter
- Video ad strategist
- Real-user reaction simulator
- ROI forecaster
- Ad generator and ranking system

Your mission:
Simulate real human behavior, predict ad performance, generate better ads, rank them, and determine what should or should NOT be run — BEFORE money is spent.

---

# 🧠 PERSONA SIMULATION (MANDATORY)

You simultaneously think as:
- 19-year-old Lagos TikTok user on slow data (impatient, skeptical)
- 38-year-old Abuja professional burned by scams
- 52-year-old UK compliance-focused user
- US performance marketer optimizing ROI

---

# ⚠️ CORE REALITY RULES

1. Assume users are skeptical
2. Assume fast scrolling
3. Assume zero intent to buy
4. Trust must be earned instantly
5. Be brutally honest
6. No generic advice
7. Every issue must include a fix
8. ROI must be conservative
9. Do NOT reward hype unless justified

---

# 🎯 PLATFORM BEHAVIOR

TikTok:
- 1–2 second hook determines survival
- Must feel native and fast

Facebook:
- Trust + proof required

Instagram:
- Visual emotional appeal

YouTube:
- First 5 seconds determines skip

---

# 🌍 LOCATION INTELLIGENCE

Nigeria:
- High scam awareness
- Requires proof
- WhatsApp-style CTA works

US:
- Emotional + urgency driven

UK:
- Compliance + structured trust

---

# 🎬 VIDEO STRATEGIST ENGINE

If input is a video script:

Evaluate:
- Hook delivery (first 2 seconds)
- Speech flow (natural vs robotic)
- Pattern interrupt strength
- Visual dependency (Low | Medium | High)
- Delivery risk (confidence, pacing)
- Execution gaps
- Best format: talking head | UGC | screen recording | mixed

Key truth:
Good script + bad delivery = failure
Simple script + strong delivery = success

---

# 🧠 BEHAVIOR SIMULATION (MANDATORY)

Simulate:
1. MICRO-STOP (0–1s)
2. SCROLL STOP (1–2s)
3. ATTENTION (2–5s)
4. TRUST (5–15s)
5. CLICK + POST-CLICK

---

# 🔍 LINE-BY-LINE ANALYSIS (MANDATORY)

Break script into lines.

For EACH line:
- Identify issue
- Explain why it fails
- Provide precise fix
- Estimate impact

---

# 💰 ROI ENGINE (MANDATORY)

Estimate:
- CTR
- CPC
- Conversion rate
- Break-even probability
- Risk level

Provide:
- worst_case
- expected_case
- best_case

Be realistic, not optimistic.

---

# 🚀 v4 GENERATION ENGINE (MANDATORY)

You MUST generate 5–10 ad variants.

Each must include:
- Different angle
- Different hook
- Different positioning

---

# 🏆 RANKING ENGINE

Rank all variants based on:
- Hook strength
- Trust
- Conversion likelihood
- ROI potential

---

# 🚫 RUN DECISION ENGINE

Determine:
- Should user run this ad?
- Should they fix first?
- Should they avoid entirely?

---

# ⚔️ COMPETITOR THINKING

Explain:
- Why competitor ads win instead
- What they are doing better
- How to outperform them

---

# 🚨 STRICT OUTPUT RULES

You MUST return VALID JSON ONLY.
NO explanations
NO markdown
NO missing keys
NO partial output
If unsure → still return full structure.

---

INPUT TO ANALYZE:
- Ad Content: {ad_copy}
- Platform: {platform}
- Target Audience: {audience_description}
- Industry: {industry}
- Objective: {objective}
- Media Analysis: {media_context}

---

# 📊 REQUIRED OUTPUT STRUCTURE (STRICT JSON)

{{
  "behavior_summary": {{
    "micro_stop_rate": "UltraLow|Low|Medium|High|ViralPotential",
    "scroll_stop_rate": "Low|Medium|High",
    "attention_retention": "Low|Medium|High",
    "trust_level": "Low|Medium|High",
    "click_probability": "Low|Medium|High",
    "post_click_bounce_risk": "VeryHigh|High|Medium|Low",
    "failure_risk": "XX%",
    "verdict": "One sentence brutal truth",
    "primary_reason": "Why it succeeds or fails",
    "launch_readiness": "XX%"
  }},
  "platform_specific": {{
    "platform": "...",
    "core_behavior": "...",
    "fatal_flaw": "...",
    "platform_specific_fix": "..."
  }},
  "scores": {{
    "overall": 0-100,
    "hook_strength": 0-100,
    "clarity": 0-100,
    "trust_building": 0-100,
    "cta_power": 0-100,
    "audience_alignment": 0-100,
    "cultural_resonance": 0-100,
    "decision_friction": 0-100,
    "predicted_lift_if_fixed": "+XX%"
  }},
  "phase_breakdown": {{
    "micro_stop_0_1s": "...",
    "scroll_stop_1_2s": "...",
    "attention_2_5s": "...",
    "trust_evaluation": "...",
    "click_and_post_click": "..."
  }},
  "line_by_line_analysis": [
    {{
      "line": "...",
      "issue": "...",
      "why_it_fails": "...",
      "precise_fix": "...",
      "impact": "+XX%"
    }}
  ],
  "critical_weaknesses": [
    {{
      "issue": "...",
      "behavior_impact": "...",
      "precise_fix": "...",
      "estimated_lift": "+XX%"
    }}
  ],
  "improvements": ["..."],
  "improved_ad": {{
    "headline": "...",
    "body_copy": "...",
    "cta": "...",
    "video_script_version": "Full optimized script"
  }},
  "variations": {{
    "power_hooks": ["..."],
    "high_conversion_ctas": ["..."],
    "strongest_angles": ["..."]
  }},
  "persona_reactions": [
    {{
      "persona": "...",
      "reaction": "...",
      "exact_quote": "..."
    }}
  ],
  "video_execution_analysis": {{
    "hook_delivery_strength": "...",
    "speech_flow_quality": "...",
    "pattern_interrupt_strength": "...",
    "visual_dependency": "Low|Medium|High",
    "delivery_risk": "...",
    "recommended_format": "talking head|UGC|screen recording|mixed",
    "execution_gaps": ["..."],
    "exact_fix_direction": "..."
  }},
  "post_click_prediction": "...",
  "roi_analysis": {{
    "roi_potential": "Low|Medium|High|Very High",
    "break_even_probability": "XX%",
    "risk_classification": "High|Medium|Low",
    "confidence_level": "Low|Medium|High",
    "confidence_reason": "...",
    "key_metrics": {{
      "expected_ctr_range": "X.X% - X.X%",
      "realistic_cpc_range": "$X.XX - $X.XX",
      "conversion_rate_range": "X% - X%"
    }},
    "roi_scenarios": {{
      "worst_case": "...",
      "expected_case": "...",
      "best_case": "..."
    }},
    "primary_roi_lever": "...",
    "biggest_financial_risk": "...",
    "optimization_priority": "..."
  }},
  "ad_variants": [
    {{
      "id": 1,
      "angle": "...",
      "hook": "...",
      "copy": "...",
      "predicted_score": 0-100,
      "roi_potential": "Low|Medium|High|Very High",
      "reason": "..."
    }}
  ],
  "winner_prediction": {{
    "best_variant_id": 1,
    "reason": "...",
    "expected_lift": "+XX%",
    "confidence": "Low|Medium|High"
  }},
  "roi_comparison": [
    {{
      "variant_id": 1,
      "roi_potential": "...",
      "risk": "...",
      "summary": "..."
    }}
  ],
  "run_decision": {{
    "should_run": "Yes|No|Only after fixes",
    "reason": "...",
    "risk_level": "High|Medium|Low"
  }},
  "competitor_advantage": {{
    "why_user_might_choose_competitor": "...",
    "what_competitor_is_doing_better": "...",
    "execution_difference": "...",
    "how_to_outperform": "..."
  }}
}}

RULES:
1. Return ONLY valid JSON - no markdown, no explanations, no code blocks
2. Ensure all JSON keys and values are properly quoted
3. Numbers must be integers without quotes, strings must be in quotes
4. Arrays must contain at least one item (use placeholders if needed)
5. ad_variants MUST contain 5-10 variants with different angles
6. line_by_line_analysis MUST break the script into individual lines
7. Be brutally honest - sugarcoating kills campaigns
8. Conservative ROI estimates - better to under-promise
9. Every weakness MUST have a precise fix
10. Video scripts: Evaluate spoken delivery, not just text quality

Respond with ONLY the JSON object."""


# PATCH: Lightweight prompt for re-analyzing improved ad (faster, focused on key metrics)
IMPROVED_AD_REANALYSIS_PROMPT = """You are AD PRE-VALIDATOR v4.0 - Quick Re-analysis Mode.
Analyze this IMPROVED ad version and return ONLY the essential metrics.

INPUT:
- Ad Content: {ad_copy}
- Platform: {platform}
- Target Audience: {audience_description}
- Industry: {industry}
- Objective: {objective}

OUTPUT FORMAT (STRICT JSON):
{{
  "scores": {{
    "overall": 0-100
  }},
  "roi_analysis": {{
    "roi_potential": "Low|Medium|High|Very High",
    "break_even_probability": "XX%",
    "risk_classification": "High|Medium|Low"
  }},
  "run_decision": {{
    "should_run": "Yes|No|Only after fixes",
    "reason": "One sentence explanation",
    "risk_level": "High|Medium|Low"
  }},
  "behavior_summary": {{
    "verdict": "One sentence assessment",
    "launch_readiness": "XX%"
  }}
}}

Return ONLY valid JSON. Be brutally honest."""


def safe_json_parse(content: str) -> Dict[str, Any]:
    """
    Safely parse JSON from AI response with multiple fallback strategies
    """
    content = content.strip()
    
    # Strategy 1: Direct JSON parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Extract JSON from markdown code blocks
    patterns = [
        r"```json\s*\n(.*?)\n```",
        r"```\s*\n(.*?)\n```",
        r"```json(.*?)```",
        r"```(.*?)```"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                continue
    
    # Strategy 3: Find JSON object boundaries
    try:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start:end+1])
    except json.JSONDecodeError:
        pass
    
    # Strategy 4: Fix common JSON issues and retry
    try:
        # Remove trailing commas before closing brackets
        fixed = re.sub(r",(\s*[}\]])", r"\1", content)
        # Fix single quotes to double quotes
        fixed = fixed.replace("'", '"')
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass
    
    raise ValueError(f"Could not parse JSON from response: {content[:500]}")


class AIEngine:
    """OpenRouter-powered AI analysis engine for ad validation v4.0"""

    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.base_url = OPENROUTER_BASE_URL
        self.model = DEFAULT_MODEL
        self.timeout = 90.0  # Increased for v4 generation complexity

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def analyze_ad(
        self,
        ad_copy: str,
        platform: str,
        audience_description: str,
        industry: str,
        objective: str,
        media_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze ad using OpenRouter API with retry logic (v4.0)

        Args:
            ad_copy: The ad content to analyze (truncated to 4000 chars)
            platform: Target platform (TikTok, Facebook, etc.)
            audience_description: Rich audience targeting description
            industry: Industry vertical
            objective: Campaign objective
            media_context: Optional media analysis results

        Returns:
            Dict containing full v4.0 analysis results including:
            - line_by_line_analysis
            - ad_variants (5-10 items)
            - winner_prediction
            - roi_comparison
            - run_decision
            - improved_ad_analysis (NEW - re-analysis of improved version)
        """

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")

        # Truncate ad copy to prevent token overflow
        ad_copy_truncated = ad_copy[:4000] if len(ad_copy) > 4000 else ad_copy
        
        # Format media context
        media_str = json.dumps(media_context) if media_context else "No media uploaded"

        # Build the prompt
        prompt = AD_VALIDATION_PROMPT.format(
            ad_copy=ad_copy_truncated,
            platform=platform,
            audience_description=audience_description,
            industry=industry,
            objective=objective,
            media_context=media_str
        )

        # OpenRouter API request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://adlytics.app",
            "X-Title": "ADLYTICS"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert ad validation system v4.0. Always respond with valid JSON only. Generate 5-10 ad variants with line-by-line analysis."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 6000  # Increased for v4 generation
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )

                response.raise_for_status()
                data = response.json()

                # Extract content from OpenRouter response
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]

                    # Parse JSON response using safe parser
                    try:
                        result = safe_json_parse(content)
                        
                        # Validate required v4 fields exist
                        required_v4_fields = [
                            "line_by_line_analysis",
                            "ad_variants", 
                            "winner_prediction",
                            "roi_comparison",
                            "run_decision"
                        ]
                        
                        for field in required_v4_fields:
                            if field not in result:
                                result[field] = self._get_default_v4_field(field)
                        
                        # ===================================================================
                        # PATCH: Re-analyze the improved ad version
                        # ===================================================================
                        improved_ad = result.get("improved_ad", {})
                        if improved_ad and (improved_ad.get("headline") or improved_ad.get("body_copy")):
                            try:
                                # Build improved ad content
                                improved_content = f"{improved_ad.get('headline', '')}\n\n{improved_ad.get('body_copy', '')}\n\nCTA: {improved_ad.get('cta', '')}"
                                
                                # Build lightweight re-analysis prompt
                                improved_prompt = IMPROVED_AD_REANALYSIS_PROMPT.format(
                                    ad_copy=improved_content[:2000],  # Shorter for speed
                                    platform=platform,
                                    audience_description=audience_description,
                                    industry=industry,
                                    objective=objective
                                )
                                
                                # Call AI for improved ad analysis (lighter weight)
                                improved_payload = {
                                    "model": self.model,
                                    "messages": [
                                        {
                                            "role": "system",
                                            "content": "You are a fast ad evaluator. Return only JSON."
                                        },
                                        {
                                            "role": "user",
                                            "content": improved_prompt
                                        }
                                    ],
                                    "temperature": 0.3,
                                    "max_tokens": 800  # Much smaller for speed
                                }
                                
                                improved_response = await client.post(
                                    f"{self.base_url}/chat/completions",
                                    headers=headers,
                                    json=improved_payload
                                )
                                improved_response.raise_for_status()
                                improved_data = improved_response.json()
                                
                                if "choices" in improved_data and len(improved_data["choices"]) > 0:
                                    improved_content_raw = improved_data["choices"][0]["message"]["content"]
                                    improved_analysis = safe_json_parse(improved_content_raw)
                                    
                                    # Ensure structure is valid
                                    result["improved_ad_analysis"] = {
                                        "scores": improved_analysis.get("scores", {"overall": 0}),
                                        "roi_analysis": improved_analysis.get("roi_analysis", {
                                            "roi_potential": "Unknown",
                                            "break_even_probability": "0%",
                                            "risk_classification": "High"
                                        }),
                                        "run_decision": improved_analysis.get("run_decision", {
                                            "should_run": "Unknown",
                                            "reason": "Analysis incomplete",
                                            "risk_level": "High"
                                        }),
                                        "behavior_summary": improved_analysis.get("behavior_summary", {
                                            "verdict": "Unknown",
                                            "launch_readiness": "0%"
                                        })
                                    }
                                else:
                                    raise ValueError("No choices in improved ad response")
                                    
                            except Exception as improved_err:
                                # Fallback: use original analysis with note
                                print(f"Improved ad re-analysis failed: {improved_err}")
                                result["improved_ad_analysis"] = {
                                    "scores": result.get("scores", {"overall": 0}),
                                    "roi_analysis": result.get("roi_analysis", {
                                        "roi_potential": "Unknown",
                                        "break_even_probability": "0%",
                                        "risk_classification": "High"
                                    }),
                                    "run_decision": {
                                        "should_run": "Unknown",
                                        "reason": f"Re-analysis failed: {str(improved_err)[:50]}",
                                        "risk_level": "High"
                                    },
                                    "behavior_summary": {
                                        "verdict": "Re-analysis unavailable",
                                        "launch_readiness": "0%"
                                    },
                                    "_fallback": True
                                }
                        else:
                            # No improved_ad generated, set empty analysis
                            result["improved_ad_analysis"] = {
                                "scores": {"overall": 0},
                                "roi_analysis": {
                                    "roi_potential": "N/A",
                                    "break_even_probability": "0%",
                                    "risk_classification": "High"
                                },
                                "run_decision": {
                                    "should_run": "N/A",
                                    "reason": "No improved version generated",
                                    "risk_level": "High"
                                },
                                "behavior_summary": {
                                    "verdict": "No improved version",
                                    "launch_readiness": "0%"
                                }
                            }
                        # ===================================================================
                        
                        return result
                    except ValueError as parse_err:
                        raise ValueError(f"JSON parsing failed: {parse_err}")
                else:
                    raise ValueError("No choices in OpenRouter response")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid OpenRouter API key")
            elif e.response.status_code == 429:
                raise ValueError("Rate limit exceeded. Please try again.")
            elif e.response.status_code >= 500:
                raise ValueError("OpenRouter service error. Please retry.")
            else:
                raise ValueError(f"OpenRouter API error: {e.response.status_code}")

        except httpx.TimeoutException:
            raise ValueError("Analysis timed out. Please retry or simplify request.")

        except Exception as e:
            raise ValueError(f"Analysis failed: {str(e)}")
    
    def _get_default_v4_field(self, field: str) -> Any:
        """Provide default values for missing v4 fields"""
        defaults = {
            "line_by_line_analysis": [],
            "ad_variants": [],
            "winner_prediction": {
                "best_variant_id": 1,
                "reason": "Analysis unavailable",
                "expected_lift": "+0%",
                "confidence": "Low"
            },
            "roi_comparison": [],
            "run_decision": {
                "should_run": "Only after fixes",
                "reason": "AI analysis incomplete - review required",
                "risk_level": "High"
            }
        }
        return defaults.get(field, [])

    async def analyze_with_fallback(
        self,
        ad_copy: str,
        platform: str,
        audience_description: str,
        industry: str,
        objective: str,
        media_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze with fallback to default values if AI fails
        """
        try:
            return await self.analyze_ad(
                ad_copy, platform, audience_description, 
                industry, objective, media_context
            )
        except Exception as e:
            # Return structured fallback with error info and v4 structure
            return {
                "behavior_summary": {
                    "micro_stop_rate": "Medium",
                    "scroll_stop_rate": "Medium",
                    "attention_retention": "Medium",
                    "trust_level": "Medium",
                    "click_probability": "Medium",
                    "post_click_bounce_risk": "Medium",
                    "failure_risk": "50%",
                    "verdict": "Analysis temporarily unavailable - manual review recommended",
                    "primary_reason": str(e)[:200],
                    "launch_readiness": "50%"
                },
                "platform_specific": {
                    "platform": platform,
                    "core_behavior": "Unable to analyze",
                    "fatal_flaw": "AI service unavailable",
                    "platform_specific_fix": "Retry analysis"
                },
                "scores": {
                    "overall": 50,
                    "hook_strength": 50,
                    "clarity": 50,
                    "trust_building": 50,
                    "cta_power": 50,
                    "audience_alignment": 50,
                    "cultural_resonance": 50,
                    "decision_friction": 50,
                    "predicted_lift_if_fixed": "+20%"
                },
                "phase_breakdown": {
                    "micro_stop_0_1s": "Unable to assess",
                    "scroll_stop_1_2s": "Unable to assess",
                    "attention_2_5s": "Unable to assess",
                    "trust_evaluation": "Unable to assess",
                    "click_and_post_click": "Unable to assess"
                },
                "line_by_line_analysis": [{
                    "line": "Full script",
                    "issue": "AI analysis failed",
                    "why_it_fails": str(e)[:100],
                    "precise_fix": "Retry analysis",
                    "impact": "+0%"
                }],
                "critical_weaknesses": [{
                    "issue": "AI analysis failed - please retry",
                    "behavior_impact": "Unable to assess",
                    "precise_fix": "Check API key or retry in 30 seconds",
                    "estimated_lift": "+0%"
                }],
                "improvements": ["Retry analysis for full evaluation"],
                "improved_ad": {
                    "headline": "[Analysis unavailable]",
                    "body_copy": ad_copy[:200] if ad_copy else "",
                    "cta": "[Please retry]",
                    "video_script_version": "[Please retry]"
                },
                "variations": {
                    "power_hooks": [],
                    "high_conversion_ctas": [],
                    "strongest_angles": []
                },
                "video_execution_analysis": {
                    "hook_delivery_strength": "Unable to assess",
                    "speech_flow_quality": "Unable to assess",
                    "pattern_interrupt_strength": "Unable to assess",
                    "visual_dependency": "Medium",
                    "delivery_risk": "Unable to assess",
                    "recommended_format": "talking head",
                    "execution_gaps": ["Analysis failed"],
                    "exact_fix_direction": "Retry analysis"
                },
                "persona_reactions": [{
                    "persona": "General User",
                    "reaction": "Unable to simulate",
                    "exact_quote": "..."
                }],
                "post_click_prediction": "Unable to predict",
                "roi_analysis": {
                    "roi_potential": "Medium",
                    "break_even_probability": "50%",
                    "risk_classification": "Medium",
                    "confidence_level": "Low",
                    "confidence_reason": "AI analysis failed",
                    "key_metrics": {
                        "expected_ctr_range": "1.0% - 2.0%",
                        "realistic_cpc_range": "$1.00 - $3.00",
                        "conversion_rate_range": "2% - 5%"
                    },
                    "roi_scenarios": {
                        "worst_case": "Unable to calculate",
                        "expected_case": "Unable to calculate",
                        "best_case": "Unable to calculate"
                    },
                    "primary_roi_lever": "Retry analysis",
                    "biggest_financial_risk": "Unknown - analysis failed",
                    "optimization_priority": "Fix AI connection"
                },
                "ad_variants": [],
                "winner_prediction": {
                    "best_variant_id": 1,
                    "reason": "Analysis failed",
                    "expected_lift": "+0%",
                    "confidence": "Low"
                },
                "roi_comparison": [],
                "run_decision": {
                    "should_run": "Only after fixes",
                    "reason": f"AI error: {str(e)[:100]}",
                    "risk_level": "High"
                },
                "competitor_advantage": {
                    "why_user_might_choose_competitor": "Unable to analyze",
                    "what_competitor_is_doing_better": "Unable to analyze",
                    "execution_difference": "Unable to analyze",
                    "how_to_outperform": "Retry analysis"
                },
                # PATCH: Add improved_ad_analysis to fallback
                "improved_ad_analysis": {
                    "scores": {"overall": 0},
                    "roi_analysis": {
                        "roi_potential": "Unknown",
                        "break_even_probability": "0%",
                        "risk_classification": "High"
                    },
                    "run_decision": {
                        "should_run": "Unknown",
                        "reason": "Analysis failed",
                        "risk_level": "High"
                    },
                    "behavior_summary": {
                        "verdict": "Analysis failed",
                        "launch_readiness": "0%"
                    }
                },
                "_error": str(e),
                "_fallback": True
            }


# Singleton instance
_ai_engine: Optional[AIEngine] = None


def get_ai_engine() -> AIEngine:
    """Get or create AI engine singleton"""
    global _ai_engine
    if _ai_engine is None:
        _ai_engine = AIEngine()
    return _ai_engine
