"""
ADLYTICS v5.7.1 - Complete JSON Schema
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
            "Reliance on social proof and peer validation"
        ],
        "trust_builders": [
            "Local testimonials with faces",
            "Community validation"
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
            "Individual achievement focus"
        ],
        "trust_builders": [
            "Money-back guarantee"
        ]
    },
    "united_kingdom": {
        "currency": "£",
        "currency_name": "Pound",
        "behavioral_traits": [
            "Reserved skepticism"
        ],
        "trust_builders": [
            "Official registration"
        ]
    },
    "india": {
        "currency": "₹",
        "currency_name": "Rupee",
        "behavioral_traits": [
            "Family decision dynamics"
        ],
        "trust_builders": [
            "Tax transparency"
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
    """V5.7.1 - Complete schema"""

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
                    return self._enforce_structure(analysis, content_analysis, country_profile)

            except Exception as e:
                logger.warning(f"Attempt {attempt+1} failed: {e}")
                if attempt == 2:
                    raise

        raise ValueError("Analysis failed")

    def _get_system_prompt(self, content_analysis: Dict) -> str:
        max_score = 15 if content_analysis["real_words"] < 10 else (35 if content_analysis["real_words"] < 20 else (50 if content_analysis["real_words"] < 30 else 100))

        return f"""You are a STRICT performance marketing analyst.

CONTENT:
- Real words: {content_analysis['real_words']}
- Maximum score: {max_score}

SCORING RUBRICS:
Hook: 90-100=stops scroll+numbers+curiosity, 70-79=decent but generic, 40-59=poor/no value, 0-19=no hook
Clarity: 90-100=understood in 3s, 70-79=mostly clear, 40-59=confusing, 0-19=gibberish
Credibility: 90-100=specific proof+guarantees, 70-79=basic credibility, 40-59=no proof, 0-19=scam red flags
Emotional: 90-100=deep pain+urgency, 70-79=some emotion, 40-59=dry facts, 0-19=wrong/confusing
CTA: 90-100=clear+benefit+urgency, 70-79=decent action, 40-59=weak/vague, 0-19=no CTA
Audience: 90-100=perfect language match, 70-79=good match, 40-59=generic, 0-19=wrong/offensive
Platform: 90-100=perfect platform fit, 70-79=good fit, 40-59=poor fit, 0-19=wrong platform
Overall: Weighted average (Hook 20%, Clarity 15%, Credibility 15%, Emotional 20%, CTA 15%, Audience 10%, Platform 5%)

RULE: Content < 10 words = max score 15. Empty ad_copy = Hook/CTA max 20.

IMPORTANT: Return complete JSON with ALL fields populated. No empty sections."""

    def _build_prompt(self, data: Dict, ad_copy: str, video_script: str, country_profile: Dict, content_analysis: Dict) -> str:
        currency = country_profile['currency']
        country = data.get('country', 'united_states')
        max_score = 15 if content_analysis["real_words"] < 10 else (35 if content_analysis["real_words"] < 20 else (50 if content_analysis["real_words"] < 30 else 100))

        warnings = []
        if not content_analysis["has_ad_copy"]:
            warnings.append("CRITICAL: Ad Copy field is EMPTY")
        if content_analysis["is_short"]:
            warnings.append(f"CRITICAL: Content too short ({content_analysis['real_words']} words)")
        warning_text = " | ".join(warnings) if warnings else "Content meets minimum requirements."

        # Build JSON template as regular string first
        json_template = """{
  "scores": {
    "overall": 0-100,
    "hook_strength": 0-100,
    "clarity": 0-100,
    "credibility": 0-100,
    "emotional_pull": 0-100,
    "cta_strength": 0-100,
    "audience_match": 0-100,
    "platform_fit": 0-100
  },
  "behavior_summary": "Detailed analysis (150+ chars). Explain scores. Reference specific phrases from input.",
  "critical_weaknesses": [
    {"issue": "Specific problem", "severity": "High/Medium/Low", "impact": "Business impact", "fix": "Specific fix"}
  ],
  "decision_engine": {
    "should_run": true/false,
    "confidence": "0-100%",
    "reasoning": "Detailed (150+ chars)",
    "expected_profit": 0,
    "roi_prediction": "0.0x",
    "profit_scenarios": {"low_case": 0, "base_case": 0, "high_case": 0},
    "kill_threshold": "When to kill",
    "scale_threshold": "When to scale",
    "confidence_breakdown": {"hook": 0, "offer": 0, "audience": 0}
  },
  "budget_optimization": {
    "break_even_cpc": 0,
    "safe_test_budget": 0,
    "budget_phases": ["Phase 1", "Phase 2", "Phase 3"],
    "risk_level": "High/Medium/Low",
    "worst_case_loss": 0,
    "scaling_rule": "Rule",
    "scaling_risk": "Risk",
    "budget_tip": "Tip"
  },
  "neuro_response": {
    "dopamine": 0,
    "fear": 0,
    "curiosity": 0,
    "urgency": 0,
    "trust": 0,
    "primary_driver": "Main driver",
    "emotional_triggers": ["Trigger 1", "Trigger 2", "Trigger 3"],
    "psychological_gaps": ["Gap 1", "Gap 2"]
  },
  "ad_variants": [
    {"id": 1, "angle": "Angle", "hook": "Hook text", "body": "Body text 100-200 words", "cta": "CTA text", "predicted_score": 0, "why_it_works": "Explanation"},
    {"id": 2, "angle": "...", "hook": "...", "body": "...", "cta": "...", "predicted_score": 0, "why_it_works": "..."},
    {"id": 3, "angle": "...", "hook": "...", "body": "...", "cta": "...", "predicted_score": 0, "why_it_works": "..."},
    {"id": 4, "angle": "...", "hook": "...", "body": "...", "cta": "...", "predicted_score": 0, "why_it_works": "..."},
    {"id": 5, "angle": "...", "hook": "...", "body": "...", "cta": "...", "predicted_score": 0, "why_it_works": "..."}
  ],
  "improved_ad": {
    "final_hook": "Optimized hook",
    "final_body": "200+ word body",
    "final_cta": "Optimized CTA",
    "video_script_ready": "Script with [HOOK 0-3s], [BODY 3-15s], [CTA 15-30s]",
    "key_changes_made": ["Change 1", "Change 2", "Change 3", "Change 4"]
  },
  "winner_prediction": {"winner_id": 1, "angle": "Winning angle", "confidence": "0%", "reasoning": "Why"},
  "objection_detection": {
    "scam_triggers": [{"trigger": "Red flag", "severity": "High"}],
    "trust_gaps": [{"gap": "Missing element", "severity": "High"}],
    "compliance_risks": [{"risk": "Violation", "platform": "Platform"}]
  },
  "creative_fatigue": {
    "fatigue_level": "Low/Medium/High",
    "estimated_decline_days": 0,
    "explanation": "Why fatigue happens",
    "refresh_needed": false,
    "refresh_recommendations": ["Idea 1", "Idea 2", "Idea 3"]
  },
  "cross_platform": {
    "facebook": {"score": 0, "adapted_copy": "Facebook version", "changes_needed": "Changes"},
    "tiktok": {"score": 0, "adapted_copy": "TikTok version", "changes_needed": "Changes"},
    "youtube": {"score": 0, "adapted_copy": "YouTube version", "changes_needed": "Changes"}
  },
  "video_execution_analysis": {
    "hook_delivery": "Analysis of opening (60+ words)",
    "speech_flow": "Pacing (40+ words)",
    "visual_dependency": "Visual balance (40+ words)",
    "delivery_risk": "Challenges (40+ words)",
    "format_recommendation": "talking_head/UGC/screen/mixed",
    "competitor_advantage": "How to beat competitors (50+ words)",
    "timecode_breakdown": [
      {"segment": "HOOK 0-3s", "content": "What happens", "effectiveness": 0},
      {"segment": "BODY 3-15s", "content": "What happens", "effectiveness": 0},
      {"segment": "CTA 15-30s", "content": "What happens", "effectiveness": 0}
    ]
  },
  "persona_reactions": [
    {"name": "Persona 1", "demographic": "Description", "reaction": "Reaction", "pain_points": ["Pain 1"], "objections": ["Objection 1"], "conversion_likelihood": "High"},
    {"name": "Persona 2", "demographic": "...", "reaction": "...", "pain_points": ["..."], "objections": ["..."], "conversion_likelihood": "Medium"},
    {"name": "Persona 3", "demographic": "...", "reaction": "...", "pain_points": ["..."], "objections": ["..."], "conversion_likelihood": "Low"}
  ],
  "line_by_line_analysis": [
    {"line_number": 1, "text": "Line", "strength": 0, "assessment": "Good/Bad", "issue": "Problem", "suggestion": "Fix"}
  ],
  "phase_breakdown": {
    "hook_phase": "Analysis of hook",
    "body_phase": "Analysis of body",
    "cta_phase": "Analysis of CTA"
  },
  "roi_comparison": {
    "your_projection": "0.0x",
    "industry_average": "0.0x",
    "top_performer": "0.0x",
    "gap_analysis": "Detailed comparison (100+ words)"
  },
  "competitor_advantage": {
    "unique_angles": ["Angle 1", "Angle 2", "Angle 3"],
    "defensible_moat": "Defensible moat (80+ words)",
    "vulnerability": "Vulnerability (60+ words)"
  }
}"""

        return f"""STRICT ANALYSIS REQUEST

TARGET: {country} ({currency})
PLATFORM: {data.get('platform', 'unknown')}
INDUSTRY: {data.get('industry', 'unknown')}

CONTENT METRICS:
- Ad Copy: {len(ad_copy.strip())} chars
- Video Script: {len(video_script.strip())} chars
- Real Words: {content_analysis['real_words']}
- Maximum Score: {max_score}

WARNINGS: {warning_text}

CONTENT TO ANALYZE:
[AD COPY]
{ad_copy if ad_copy else "[EMPTY]"}
[/AD COPY]

[VIDEO SCRIPT]
{video_script if video_script else "[EMPTY]"}
[/VIDEO SCRIPT]

INSTRUCTIONS:
1. Use scoring rubrics to determine scores (max {max_score})
2. Fill ALL fields in the JSON template below
3. Do not skip any sections - they are all required
4. If content is poor, scores should be low (10-40)
5. If content is < 10 words, all scores max 15
6. improved_ad must be 200+ words with full copy
7. ad_variants must have 5 complete variants (100-200 words each)
8. ALL objects must be populated - no empty arrays

RETURN THIS EXACT JSON STRUCTURE:
{json_template}

CRITICAL: Fill every field. No empty sections. No skipping tabs."""

    def _enforce_structure(self, analysis: Dict, content_analysis: Dict, country_profile: Dict) -> Dict:
        """Enforce all required fields exist"""
        scores = analysis.get("scores", {})
        max_score = 15 if content_analysis["real_words"] < 10 else (35 if content_analysis["real_words"] < 20 else (50 if content_analysis["real_words"] < 30 else 100))

        # Cap scores
        for key in scores:
            if scores[key] > max_score:
                scores[key] = max_score
        analysis["scores"] = scores

        # Ensure all top-level keys exist with defaults
        defaults = {
            "behavior_summary": "Analysis completed. See scores for details.",
            "critical_weaknesses": [],
            "decision_engine": {
                "should_run": False, "confidence": "0%", "reasoning": "N/A",
                "expected_profit": 0, "roi_prediction": "0x",
                "profit_scenarios": {"low_case": 0, "base_case": 0, "high_case": 0},
                "kill_threshold": "N/A", "scale_threshold": "N/A",
                "confidence_breakdown": {"hook": 0, "offer": 0, "audience": 0}
            },
            "budget_optimization": {
                "break_even_cpc": 0, "safe_test_budget": 0, "budget_phases": [],
                "risk_level": "High", "worst_case_loss": 0,
                "scaling_rule": "N/A", "scaling_risk": "N/A", "budget_tip": "N/A"
            },
            "neuro_response": {
                "dopamine": 0, "fear": 0, "curiosity": 0, "urgency": 0, "trust": 0,
                "primary_driver": "N/A", "emotional_triggers": [], "psychological_gaps": []
            },
            "ad_variants": [],
            "improved_ad": {
                "final_hook": "N/A", "final_body": "N/A", "final_cta": "N/A",
                "video_script_ready": "N/A", "key_changes_made": []
            },
            "winner_prediction": {"winner_id": 1, "angle": "N/A", "confidence": "0%", "reasoning": "N/A"},
            "objection_detection": {"scam_triggers": [], "trust_gaps": [], "compliance_risks": []},
            "creative_fatigue": {
                "fatigue_level": "Unknown", "estimated_decline_days": 0,
                "explanation": "N/A", "refresh_needed": False, "refresh_recommendations": []
            },
            "cross_platform": {
                "facebook": {"score": 0, "adapted_copy": "N/A", "changes_needed": "N/A"},
                "tiktok": {"score": 0, "adapted_copy": "N/A", "changes_needed": "N/A"},
                "youtube": {"score": 0, "adapted_copy": "N/A", "changes_needed": "N/A"}
            },
            "video_execution_analysis": {
                "hook_delivery": "No video analysis available",
                "speech_flow": "N/A", "visual_dependency": "N/A",
                "delivery_risk": "N/A", "format_recommendation": "N/A",
                "competitor_advantage": "N/A", "timecode_breakdown": []
            },
            "persona_reactions": [],
            "line_by_line_analysis": [],
            "phase_breakdown": {"hook_phase": "N/A", "body_phase": "N/A", "cta_phase": "N/A"},
            "roi_comparison": {
                "your_projection": "0x", "industry_average": "0x",
                "top_performer": "0x", "gap_analysis": "N/A"
            },
            "competitor_advantage": {
                "unique_angles": [], "defensible_moat": "N/A", "vulnerability": "N/A"
            }
        }

        for key, default_val in defaults.items():
            if key not in analysis or analysis[key] is None:
                analysis[key] = default_val

        # Force behavior_summary
        if len(str(analysis.get("behavior_summary", ""))) < 20:
            analysis["behavior_summary"] = f"Content: {content_analysis['real_words']} words. Detailed analysis in scores and recommendations."

        # Force critical_weaknesses if content short
        if content_analysis["is_short"] and len(analysis.get("critical_weaknesses", [])) == 0:
            analysis["critical_weaknesses"] = [{
                "issue": "Content too short for effective advertising",
                "severity": "High",
                "impact": "Cannot convey value proposition or build trust",
                "fix": "Expand to minimum 50 words with clear value proposition"
            }]

        return analysis


def get_ai_engine():
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AIEngineV5()
    return _engine_instance


_engine_instance = None


class AIValidationError(Exception):
    pass
