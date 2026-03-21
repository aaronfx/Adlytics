"""
ADLYTICS - AI Engine Service
Handles OpenAI API calls for ad analysis with retry logic and error handling
"""

import os
import json
import time
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

class AIEngine:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4o-mini"  # Cost-effective, fast, JSON-capable
        self.timeout = 30
        self.max_retries = 1

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

    def _build_system_prompt(self) -> str:
        """Build the ULTIMATE AD PRE-VALIDATOR system prompt"""
        return """You are ULTIMATE AD PRE-VALIDATOR v3.2  
Elite fusion of: performance marketing strategist • behavioral psychologist • direct-response copywriter • real-user reaction simulator • conservative ROI forecaster.

Your single mission:  
Simulate what ACTUALLY happens when real people see this ad — then tell the brutal truth about whether it will make or lose money.

PERSONA SIMULATION:

You simultaneously embody:
- 19-year-old Lagos TikTok scroller on slow mobile data
- 38-year-old Abuja professional who lost money to scams
- 52-year-old UK compliance-aware user
- US direct-response buyer optimizing ROI

CORE RULES:
- Assume skepticism
- Assume fast scrolling
- Be brutally honest but professional
- ROI must be conservative
- Output STRICT JSON ONLY
- Use correct currency based on location

PLATFORM:
TikTok → fast hook
Facebook → trust + proof
Instagram → visuals
YouTube → first 5 seconds

LOCATION:
Nigeria → proof + WhatsApp + skepticism
US → urgency + emotion
UK → compliance + structure

TASK:
Simulate:
- Micro-stop
- Scroll stop
- Attention
- Trust
- Click + post-click

Then:
- Diagnose
- Fix
- Rewrite
- Predict ROI

OUTPUT JSON ONLY. No markdown, no explanation outside JSON."""

    def _build_user_prompt(self, data: Dict[str, Any]) -> str:
        """Build user prompt from input data"""
        platform = data.get("platform", "Unknown")
        audience = data.get("audience", "Unknown")
        industry = data.get("industry", "Unknown")
        objective = data.get("objective", "Unknown")
        ad_copy = data.get("ad_copy", "")
        image_analysis = data.get("image_analysis", "")
        video_analysis = data.get("video_analysis", "")

        prompt = f"""Analyze this ad:

AD COPY:
{ad_copy}

PLATFORM: {platform}
TARGET AUDIENCE: {audience}
INDUSTRY: {industry}
OBJECTIVE: {objective}
"""

        if image_analysis:
            prompt += f"
IMAGE ANALYSIS: {image_analysis}
"
        if video_analysis:
            prompt += f"
VIDEO ANALYSIS: {video_analysis}
"

        prompt += """
Return complete JSON analysis with all fields populated. Be specific and actionable."""

        return prompt

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze ad using OpenAI API
        Returns parsed JSON or error structure
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": self._build_user_prompt(data)}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7,
            "max_tokens": 4000
        }

        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()

                result = response.json()
                content = result["choices"][0]["message"]["content"]

                # Parse JSON response
                parsed = json.loads(content)
                return self._validate_response(parsed)

            except requests.exceptions.Timeout:
                if attempt < self.max_retries:
                    time.sleep(2)
                    continue
                return self._error_response("Analysis timeout - please try again")

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    time.sleep(2)
                    continue
                return self._error_response(f"API error: {str(e)}")

            except json.JSONDecodeError:
                return self._error_response("Invalid response format from AI")

            except Exception as e:
                return self._error_response(f"Unexpected error: {str(e)}")

        return self._error_response("Max retries exceeded")

    def _validate_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure response has required structure"""
        required_sections = [
            "behavior_summary",
            "platform_specific", 
            "scores",
            "phase_breakdown",
            "critical_weaknesses",
            "improvements",
            "improved_ad",
            "variations",
            "persona_reactions",
            "roi_analysis"
        ]

        for section in required_sections:
            if section not in data:
                data[section] = self._default_section(section)

        return data

    def _default_section(self, section: str) -> Any:
        """Provide default values for missing sections"""
        defaults = {
            "behavior_summary": {
                "micro_stop_rate": "Medium",
                "scroll_stop_rate": "Medium",
                "verdict": "Analysis incomplete",
                "primary_reason": "Insufficient data"
            },
            "platform_specific": {
                "platform": "Unknown",
                "fatal_flaw": "Unable to determine"
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
                "predicted_lift_if_fixed": "+0%"
            },
            "phase_breakdown": {
                "micro_stop_0_1s": "Unable to analyze",
                "scroll_stop_1_2s": "Unable to analyze",
                "attention_2_5s": "Unable to analyze",
                "trust_evaluation": "Unable to analyze",
                "click_and_post_click": "Unable to analyze"
            },
            "critical_weaknesses": [],
            "improvements": [],
            "improved_ad": {
                "headline": "",
                "body_copy": "",
                "cta": ""
            },
            "variations": {
                "power_hooks": [],
                "high_conversion_ctas": [],
                "strongest_angles": []
            },
            "persona_reactions": [],
            "roi_analysis": {
                "roi_potential": "Unknown",
                "break_even_probability": "0%",
                "risk_classification": "High"
            }
        }
        return defaults.get(section, {})

    def _error_response(self, message: str) -> Dict[str, Any]:
        """Return structured error response"""
        return {
            "error": True,
            "error_message": message,
            "behavior_summary": {
                "verdict": "Analysis failed",
                "primary_reason": message,
                "launch_readiness": "0%"
            },
            "scores": {"overall": 0},
            "critical_weaknesses": [{"issue": "System error", "behavior_impact": message}]
        }
