"""
ADLYTICS AI Engine v5.8
Strict Scoring Implementation with Content-Aware Analysis
Based on behavioral simulation framework from analysis document
"""

import json
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import httpx
import os
from tenacity import retry, stop_after_attempt, wait_exponential

@dataclass
class ContentMetrics:
    """Pre-calculated content quality metrics"""
    word_count: int
    max_possible_score: int
    content_quality_flag: Optional[str]
    hook_source: str
    cta_source: str
    primary_content: str
    content_type: str

@dataclass
class ScoringCaps:
    """Enforced score caps based on content quality"""
    overall_cap: int
    hook_cap: int
    cta_cap: int
    scam_detected: bool
    scam_patterns_found: List[str]

class AIEngineV58:
    """
    Strict AI Ad Analysis Engine with honest scoring
    No more fake 85s for 4-word content
    """

    # Scam pattern detection - Nigerian market focus (raw strings fixed)
    SCAM_PATTERNS = [
        r"turn\s*\₦?\$?\d+\s*(k|000)?\s*(into|to)\s*\₦?\$?\d+",
        r"\d+\s*days?",
        r"no\s*experience\s*needed",
        r"guarantee\d*%?",
        r"risk[- ]?free",
        r"make\s*\₦?\$?\d+\s*daily",
        r"quit\s*your\s*job",
        r"financial\s*freedom",
        r"\d+x\s*returns?",
        r"secret\s*(system|method)",
        r"limited\s*spots",
        r"act\s*now"
    ]

    # Country-specific behavioral contexts
    COUNTRY_CONTEXTS = {
        "nigeria": {
            "currency": "₦",
            "scam_trauma": "High (MMM, LOOM, fake forex)",
            "trust_signals": ["CAC registration", "physical address", "WhatsApp availability"],
            "neuro_triggers": ["fear of scams", "community proof", "hustle culture"],
            "suspicious_phrases": ["turn 50k to 500k", "7 days", "no experience"]
        },
        "united_states": {
            "currency": "$",
            "scam_trauma": "Medium (MLM fatigue)",
            "trust_signals": ["BBB rating", "money-back guarantee", "social proof"],
            "neuro_triggers": ["FOMO", "status", "convenience"]
        },
        "united_kingdom": {
            "currency": "£",
            "scam_trauma": "Low but compliance-sensitive",
            "trust_signals": ["FCA regulation", "transparency", "risk warnings"],
            "neuro_triggers": ["security", "compliance", "education"]
        }
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"

    def calculate_content_metrics(self, ad_copy: Optional[str], video_script: Optional[str]) -> ContentMetrics:
        """
        Pre-calculate objective metrics before AI scoring
        This prevents fake high scores for low-quality content
        """
        # Determine primary content source
        if video_script and ad_copy:
            primary_content = f"{ad_copy}\n\n{video_script}"
            content_type = "both"
            hook_source = "video_script"  # Video script gets priority for hook
            cta_source = "video_script"   # Video script gets priority for CTA
        elif video_script:
            primary_content = video_script
            content_type = "video_script"
            hook_source = "video_script"
            cta_source = "video_script"
        elif ad_copy:
            primary_content = ad_copy
            content_type = "ad_copy"
            hook_source = "ad_copy"
            cta_source = "ad_copy"
        else:
            primary_content = ""
            content_type = "empty"
            hook_source = "none"
            cta_source = "none"

        words = len(primary_content.split())

        # STRICT Content length caps - enforce maximum possible scores
        if words < 5:
            max_score = 10
            quality_flag = "CRITICAL: Content insufficient (<5 words). Maximum score capped at 10."
        elif words < 15:
            max_score = 25
            quality_flag = "WARNING: Minimal content (15-50 words). Scores capped accordingly."
        elif words < 30:
            max_score = 50
            quality_flag = "NOTE: Short content (15-30 words). Hook and CTA heavily weighted."
        elif words < 50:
            max_score = 75
            quality_flag = None
        else:
            max_score = 100
            quality_flag = None

        return ContentMetrics(
            word_count=words,
            max_possible_score=max_score,
            content_quality_flag=quality_flag,
            hook_source=hook_source,
            cta_source=cta_source,
            primary_content=primary_content,
            content_type=content_type
        )

    def detect_scam_patterns(self, content: str) -> ScoringCaps:
        """
        Auto-detect scam language and cap scores accordingly
        """
        content_lower = content.lower()
        detected_patterns = []

        for pattern in self.SCAM_PATTERNS:
            if re.search(pattern, content_lower):
                detected_patterns.append(pattern)

        is_scam = len(detected_patterns) > 0

        if is_scam:
            return ScoringCaps(
                overall_cap=20,
                hook_cap=15,
                cta_cap=25,
                scam_detected=True,
                scam_patterns_found=detected_patterns
            )
        else:
            return ScoringCaps(
                overall_cap=100,
                hook_cap=100,
                cta_cap=100,
                scam_detected=False,
                scam_patterns_found=[]
            )

    def prepare_analysis_prompt(self, 
                               content_metrics: ContentMetrics,
                               audience_data: Dict[str, Any],
                               platform: str) -> str:
        """
        Build the strict scoring prompt with explicit rubrics
        """

        country = audience_data.get("country", "nigeria").lower()
        country_context = self.COUNTRY_CONTEXTS.get(country, self.COUNTRY_CONTEXTS["nigeria"])

        prompt = f"""You are ADLYTICS v5.8, a ruthless advertising analyst. Your job is to tell the brutal truth about whether this ad will make or lose money.

CONTENT TO ANALYZE:
---
{content_metrics.primary_content}
---

CONTENT META:
- Type: {content_metrics.content_type}
- Word Count: {content_metrics.word_count}
- Maximum Possible Score: {content_metrics.max_possible_score}/100 (ENFORCED - you cannot exceed this)
- Hook Source: {content_metrics.hook_source}
- CTA Source: {content_metrics.cta_source}
- Platform: {platform}
- Target Country: {country}

STRICT SCORING RUBRIC (Most ads score 40-60. Be harsh.):

1. hook_strength (0-100) - First 3 seconds ONLY
   90-100: Specific trauma ("I lost ₦120K"), provocation ("Stop"), or pattern interrupt
   80-89: Strong curiosity gap with clear benefit
   70-79: Clear value prop but generic
   60-69: Weak, boring, or feature-focused
   40-59: Confusing or scam-pattern ("Turn 50K to 500K")
   20-39: No hook, starts with filler ("Hey guys", "Wait...")
   0-19: No hook exists or empty

   CURRENT MAX: {content_metrics.max_possible_score if content_metrics.word_count < 20 else 100}

2. clarity (0-100) - Can viewer understand in 3 seconds?
   90-100: One sentence explains it perfectly
   70-89: Clear after brief attention
   50-69: Confusing value proposition
   30-49: Multiple competing ideas
   0-29: Incomprehensible

3. credibility (0-100) - Trust signals
   90-100: Shows losses, specific proof, vulnerability (V4 style)
   70-89: Social proof, testimonials
   50-69: Claims without proof
   30-49: Hype language only
   0-29: Scam markers, unrealistic promises

4. emotional_pull (0-100) - Pain/aspiration connection
   90-100: Addresses specific trauma or deep desire
   70-89: Clear pain point
   50-69: Generic motivation
   30-49: No emotional resonance
   0-29: Off-putting

5. cta_strength (0-100) - Call to action power
   90-100: Anti-CTA ("Don't join yet") or urgent specific action
   70-89: Clear benefit-driven CTA
   50-69: Generic "Click here"
   30-49: Weak or vague
   0-29: No CTA

6. audience_match (0-100) - Fit for {country} market
   90-100: Perfect cultural/linguistic fit (uses {country_context["currency"]}, addresses local pain points)
   70-89: Good fit
   50-69: Generic
   30-49: Mismatched
   0-29: Alienating or offensive

7. platform_fit (0-100) - Right for {platform}
   90-100: Perfect format and length
   70-89: Good fit
   50-69: Acceptable
   30-49: Wrong format
   0-29: Will fail on this platform

8. overall (0-100) - Weighted calculation
   Formula: (Hook×0.25 + Credibility×0.25 + Clarity×0.15 + Emotional×0.15 + CTA×0.10 + Audience×0.10)

   IMPORTANT: If word count < 10, maximum overall is 15 regardless of formula result.
   If scam patterns detected, maximum overall is 20.

SCORING RULES:
1. If content_metrics.word_count < 10, you MUST give overall <= 15
2. If hook contains "turn X into Y" or "10x returns", hook_strength MUST be <= 20
3. Be honest - most content is mediocre (40-60 range)
4. If video_script is primary source, score hook/cta based on video script opening/closing
5. Nigerian market context: {country_context["scam_trauma"]} - adjust credibility expectations accordingly

Extract and return:
- hook_text: First 10-15 words (the actual hook)
- cta_text: Last 10-15 words (the actual CTA)
- word_count: {content_metrics.word_count}

OUTPUT STRICT JSON:
{{
  "scores": {{
    "overall": 0,
    "hook_strength": 0,
    "clarity": 0,
    "credibility": 0,
    "emotional_pull": 0,
    "cta_strength": 0,
    "audience_match": 0,
    "platform_fit": 0
  }},
  "content_analysis": {{
    "hook_text": "extracted hook",
    "cta_text": "extracted cta",
    "word_count": {content_metrics.word_count},
    "primary_type": "{content_metrics.content_type}"
  }},
  "strategic_summary": "Detailed 200-char explanation of why these scores were given. Be specific about failures.",
  "critical_weaknesses": [
    {{
      "issue": "Specific problem",
      "impact": "What this costs you",
      "precise_fix": "Exactly how to fix it",
      "estimated_lift": "+X%"
    }}
  ],
  "behavioral_prediction": {{
    "micro_stop_rate": "High/Medium/Low",
    "scroll_stop_rate": "High/Medium/Low",
    "click_probability": "High/Medium/Low",
    "verdict": "One sentence brutal truth"
  }}
}}"""

        return prompt

    def enforce_score_caps(self, 
                          analysis: Dict[str, Any], 
                          content_metrics: ContentMetrics,
                          scam_caps: ScoringCaps) -> Dict[str, Any]:
        """
        Post-processing: Force scores down if AI was too generous
        This is the "no fake scores" layer
        """
        scores = analysis.get("scores", {})
        original_scores = scores.copy()

        # Cap 1: Content length cap
        if scores.get("overall", 100) > content_metrics.max_possible_score:
            scores["overall"] = content_metrics.max_possible_score
            analysis["enforcement_note"] = f"Score capped at {content_metrics.max_possible_score} due to insufficient content ({content_metrics.word_count} words)"

        # Cap 2: Scam pattern cap
        if scam_caps.scam_detected:
            if scores.get("hook_strength", 100) > scam_caps.hook_cap:
                scores["hook_strength"] = scam_caps.hook_cap
            if scores.get("overall", 100) > scam_caps.overall_cap:
                scores["overall"] = scam_caps.overall_cap

            analysis["scam_warning"] = "SCAM PATTERNS DETECTED: " + ", ".join(scam_caps.scam_patterns_found)
            analysis["critical_weaknesses"].insert(0, {
                "issue": "Content triggers scam detection patterns",
                "impact": "Immediate scroll/ignore in Nigerian market. High risk of report/ban.",
                "precise_fix": "Remove income claims. Show losses first. Be specific but honest.",
                "estimated_lift": "+400% if fixed"
            })

        # Cap 3: Hook quality check
        hook_text = analysis.get("content_analysis", {}).get("hook_text", "").lower()
        if any(x in hook_text for x in ["wait", "stop", "dont skip", "before you"]):
            if scores.get("hook_strength", 0) > 80:
                # If hook starts with generic filler but scored high, force it down
                scores["hook_strength"] = min(scores["hook_strength"], 60)
                analysis["hook_adjustment"] = "Hook starts with generic filler words ('wait', 'stop'). Score adjusted."

        # Cap 4: Empty content check
        if content_metrics.word_count < 5:
            scores["overall"] = min(scores.get("overall", 0), 10)
            scores["hook_strength"] = min(scores.get("hook_strength", 0), 5)
            scores["cta_strength"] = min(scores.get("cta_strength", 0), 5)

        # Log changes
        if scores != original_scores:
            analysis["score_enforcement"] = {
                "original_scores": original_scores,
                "adjusted_scores": scores,
                "reason": "Strict validation rules enforced"
            }

        analysis["scores"] = scores
        return analysis

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def analyze_ad(self, 
                        ad_copy: Optional[str] = None,
                        video_script: Optional[str] = None,
                        audience_data: Optional[Dict[str, Any]] = None,
                        platform: str = "tiktok") -> Dict[str, Any]:
        """
        Main analysis method with strict scoring
        """
        audience_data = audience_data or {}

        # Step 1: Pre-calculation
        content_metrics = self.calculate_content_metrics(ad_copy, video_script)
        scam_caps = self.detect_scam_patterns(content_metrics.primary_content)

        # Step 2: Prepare prompt
        prompt = self.prepare_analysis_prompt(content_metrics, audience_data, platform)

        # Step 3: AI Analysis
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://adlytics.ai",
                        "X-Title": "ADLYTICS"
                    },
                    json={
                        "model": "openai/gpt-4o",
                        "messages": [{"role": "system", "content": prompt}],
                        "response_format": {"type": "json_object"},
                        "max_tokens": 4000,
                        "temperature": 0.2  # Low temp for consistent scoring
                    }
                )

            response.raise_for_status()
            result = response.json()
            analysis = json.loads(result["choices"][0]["message"]["content"])

        except Exception as e:
            # Fallback with strict low scores if AI fails
            analysis = {
                "scores": {
                    "overall": 10,
                    "hook_strength": 5,
                    "clarity": 15,
                    "credibility": 5,
                    "emotional_pull": 10,
                    "cta_strength": 5,
                    "audience_match": 20,
                    "platform_fit": 15
                },
                "error": f"AI analysis failed: {str(e)}",
                "content_analysis": {
                    "hook_text": "error",
                    "cta_text": "error",
                    "word_count": content_metrics.word_count,
                    "primary_type": content_metrics.content_type
                },
                "strategic_summary": "Analysis failed. Content scored as low quality by default.",
                "critical_weaknesses": [{"issue": "Analysis error", "impact": "Unable to verify quality", "precise_fix": "Try again", "estimated_lift": "0%"}],
                "behavioral_prediction": {"verdict": "Analysis failed - assume low performance"}
            }

        # Step 4: Post-processing enforcement
        analysis = self.enforce_score_caps(analysis, content_metrics, scam_caps)

        # Step 5: Add metadata
        analysis["analysis_metadata"] = {
            "engine_version": "5.8",
            "content_metrics": {
                "word_count": content_metrics.word_count,
                "max_possible_score": content_metrics.max_possible_score,
                "quality_flag": content_metrics.content_quality_flag,
                "content_type": content_metrics.content_type
            },
            "scam_check": {
                "detected": scam_caps.scam_detected,
                "patterns": scam_caps.scam_patterns_found
            },
            "enforcement_applied": True
        }

        return analysis

    def generate_improved_version(self, 
                                 original_analysis: Dict[str, Any],
                                 content_type: str) -> Dict[str, Any]:
        """
        Generate improved ad based on weaknesses identified
        Only generates if original scored < 80
        """
        if original_analysis["scores"]["overall"] >= 80:
            return {
                "improvement_needed": False,
                "message": "Ad already scores 80+. Minor optimizations only.",
                "suggested_tweaks": ["A/B test hook variants", "Add specific numbers"]
            }

        # Template improvements based on score
        weaknesses = original_analysis.get("critical_weaknesses", [])

        improvements = {
            "improvement_needed": True,
            "original_score": original_analysis["scores"]["overall"],
            "target_score": min(85, original_analysis["scores"]["overall"] + 30),
            "priority_fixes": [w["precise_fix"] for w in weaknesses[:3]],
            "strategy": "Radical transparency" if original_analysis["scores"]["credibility"] < 50 else "Optimization"
        }

        return improvements


# Singleton instance
def get_ai_engine():
    return AIEngineV58()
