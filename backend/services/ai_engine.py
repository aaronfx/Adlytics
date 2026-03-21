"""
ADLYTICS - AI Ad Pre-Validation & ROI Simulator
AI Engine Service - OpenRouter Integration
Uses OpenRouter API with GPT-4o Mini for cost-efficient, high-quality analysis
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-4o-mini"  # Cost-effective, fast, JSON-capable

# ULTIMATE AD PRE-VALIDATOR v3.3 Prompt
AD_VALIDATION_PROMPT = """You are ULTIMATE AD PRE-VALIDATOR v3.3
Elite fusion of: performance marketing strategist • behavioral psychologist • direct-response copywriter • real-user reaction simulator • conservative ROI forecaster • video ad strategist

Your single mission: Simulate what ACTUALLY happens when real people see this ad — then tell the brutal truth about whether it will make or lose money.

INPUT TO ANALYZE:
- Ad Content: {ad_copy}
- Platform: {platform}
- Target Audience: {audience_description}
- Industry: {industry}
- Objective: {objective}
- Media Analysis: {media_context}

BEHAVIORAL SIMULATION FRAMEWORK (5 Personas):
1. 19yo Lagos Scroller (low data, high skepticism, 0.8s attention)
2. 38yo Abuja Professional (scam-burned, compliance-aware)
3. 25-34 Target Demo (entry-level, financial pressure, wants to believe)
4. 52yo UK Compliance Officer (regulatory strict, risk-averse)
5. US Direct-Response Buyer ($5K/day spend, pattern recognition)

VIDEO SCRIPT ANALYSIS (if applicable):
- Is this a video script? Detect spoken-word format, time markers, visual cues
- Hook Delivery (0-2s): Will the opening words STOP the scroll?
- Speech Flow Quality: Natural, conversational vs robotic/awkward
- Visual Dependency: What visuals REQUIRED for script to work?
- Delivery Risk: Confidence, pacing, clarity issues for creator
- Biggest Execution Gap: Why a good script might fail in real video
- Recommended Format: talking head | UGC | screen recording | mixed

OUTPUT FORMAT (STRICT JSON):
{...}  # Full JSON structure as before

RULES:
1. Be brutally honest — sugarcoating kills campaigns
2. Conservative ROI estimates — better to under-promise
3. Specific fixes — no generic advice
4. Cultural context matters — Nigerian market sophistication is HIGH
5. Video scripts: Evaluate spoken delivery, not just text quality
6. If video script detected, analyze execution feasibility rigorously

Respond with ONLY the JSON object. No markdown, no explanations."""

class AIEngine:
    """OpenRouter-powered AI analysis engine for ad validation"""
    
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.base_url = OPENROUTER_BASE_URL
        self.model = DEFAULT_MODEL
        self.timeout = 60.0
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def analyze_ad(self, ad_copy: str, platform: str, audience_description: str,
                         industry: str, objective: str, media_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze ad using OpenRouter API with retry logic"""
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")
        
        media_str = json.dumps(media_context) if media_context else "No media uploaded"
        
        prompt = AD_VALIDATION_PROMPT.format(
            ad_copy=ad_copy[:4000],
            platform=platform,
            audience_description=audience_description,
            industry=industry,
            objective=objective,
            media_context=media_str
        )
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://adlytics.app",
            "X-Title": "ADLYTICS"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert ad validation system. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 4000,
            "response_format": {"type": "json_object"}
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
            else:
                raise ValueError("No choices in OpenRouter response")
    
    async def analyze_with_fallback(self, ad_copy: str, platform: str, 
                                    audience_description: str, industry: str,
                                    objective: str, media_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze with fallback to default values if AI fails"""
        try:
            return await self.analyze_ad(ad_copy, platform, audience_description, 
                                         industry, objective, media_context)
        except Exception as e:
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
                    "primary_reason": str(e),
                    "launch_readiness": "50%"
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
                "critical_weaknesses": [{
                    "issue": "AI analysis failed - please retry",
                    "behavior_impact": "Unable to assess",
                    "precise_fix": "Check API key or retry in 30 seconds",
                    "estimated_lift": "+0%"
                }],
                "improvements": ["Retry analysis for full evaluation"],
                "improved_ad": {
                    "headline": "[Analysis unavailable]",
                    "body_copy": ad_copy[:200],
                    "cta": "[Please retry]",
                    "video_script_version": "[Please retry]"
                },
                "video_execution_analysis": {
                    "is_video_script": "Unknown",
                    "hook_delivery_strength": "Unable to assess",
                    "speech_flow_quality": "Unable to assess",
                    "visual_dependency": "Unable to assess",
                    "delivery_risk": "Unable to assess",
                    "biggest_execution_gap": "Analysis failed",
                    "recommended_format": "talking head"
                },
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
                    "biggest_financial_risk": "Unknown - analysis failed"
                },
                "_error": str(e),
                "_fallback": True
            }

_ai_engine: Optional[AIEngine] = None

def get_ai_engine() -> AIEngine:
    """Get or create AI engine singleton"""
    global _ai_engine
    if _ai_engine is None:
        _ai_engine = AIEngine()
    return _ai_engine
