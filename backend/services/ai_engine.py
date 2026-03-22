"""
ADLYTICS AI Engine v5.9 - REAL SCORING ONLY
No fake fallbacks. No generic scores. Every analysis is unique.
"""

import json
import re
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import httpx
import os
from tenacity import retry, stop_after_attempt, wait_exponential

@dataclass
class ContentFingerprint:
    """Unique identifier for content to prevent duplicate scoring"""
    content_hash: str
    word_count: int
    first_20_chars: str
    last_20_chars: str
    has_trauma_pattern: bool
    has_scam_pattern: bool
    emotional_keywords: List[str]

class AIEngineV59:
    """
    Strict AI Analysis - Every Score Must Be Content-Specific
    If AI returns generic scores, we retry or fail - never fake it.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"

    def fingerprint_content(self, content: str) -> ContentFingerprint:
        """Create unique fingerprint to verify AI is analyzing actual content"""
        content_lower = content.lower()

        # Extract emotional keywords present
        emotional_words = ["lost", "pain", "struggle", "truth", "honest", "transparent", 
                          "scam", "fear", "worry", "stress", "failed", "quit", "stop"]
        found_emotional = [w for w in emotional_words if w in content_lower]

        # Check for trauma patterns
        trauma_patterns = ["i lost", "i failed", "i quit", "i stopped", "burned", "scammed"]
        has_trauma = any(p in content_lower for p in trauma_patterns)

        # Check for scam patterns
        scam_patterns = ["turn", "into", "guarantee", "no experience", "risk free"]
        has_scam = any(p in content_lower for p in scam_patterns)

        return ContentFingerprint(
            content_hash=hashlib.md5(content.encode()).hexdigest()[:8],
            word_count=len(content.split()),
            first_20_chars=content[:20].strip(),
            last_20_chars=content[-20:].strip(),
            has_trauma_pattern=has_trauma,
            has_scam_pattern=has_scam,
            emotional_keywords=found_emotional
        )

    def build_strict_prompt_v59(self, content: str, fingerprint: ContentFingerprint, 
                               request_data: Dict[str, Any]) -> str:
        """
        v5.9: Bulletproof prompt that forces content-specific analysis
        Includes content fingerprint to prevent generic responses
        """

        country = request_data.get("audience_country", "nigeria")
        platform = request_data.get("platform", "tiktok")

        prompt = f"""You are ADLYTICS v5.9 - World's Strictest Ad Analyzer.

YOUR RULE: Every score MUST be uniquely derived from the SPECIFIC content below. 
If you give generic scores (e.g., all 70s), your response will be rejected.

CONTENT TO ANALYZE (Fingerprint: {fingerprint.content_hash}):
---
{content}
---

CONTENT FINGERPRINT (Verify you're analyzing THIS content):
- First 20 chars: "{fingerprint.first_20_chars}"
- Last 20 chars: "{fingerprint.last_20_chars}"
- Word count: {fingerprint.word_count}
- Trauma pattern detected: {fingerprint.has_trauma_pattern}
- Scam pattern detected: {fingerprint.has_scam_pattern}
- Emotional keywords: {fingerprint.emotional_keywords}

STRICT SCORING INSTRUCTIONS:

1. EXTRACT THE ACTUAL HOOK (first 10 words):
   What are the EXACT first 10 words? Write them out.

2. EXTRACT THE ACTUAL CTA (last 10 words):
   What are the EXACT last 10 words? Write them out.

3. SCORE BASED ON SPECIFIC CONTENT (0-100):

   hook_strength: Does "{fingerprint.first_20_chars[:30]}..." stop the scroll?
   - 90-100 ONLY if: Specific trauma ("I lost ₦120K"), provocation ("Stop"), unique pattern
   - 70-80 if: Clear but generic
   - 40-60 if: Boring or unclear
   - 10-30 if: Starts with filler ("Hey", "Wait", "Before you")

   credibility: Does it show losses/proof or make empty promises?
   - 90-100: Shows specific losses, transparency
   - 70-80: Some proof
   - 40-60: Claims without proof
   - 10-30: Scam patterns detected

   emotional_pull: Does "{fingerprint.first_20_chars[:30]}..." trigger emotion?
   - 90-100: Personal trauma/story
   - 70-80: Clear pain point
   - 40-60: Generic motivation
   - 10-30: No emotion

   clarity: Can someone understand the offer in 3 seconds?

   cta_strength: Does it end with a strong specific action?

   audience_match: Does the language fit {country} market?

   platform_fit: Is it right for {platform}?

4. CRITICAL: Your scores must be DIVERSE based on the content:
   - If content has "I lost ₦120K" → hook_strength should be 90+
   - If content has "Turn 50K to 500K" → hook_strength should be 10-20
   - If content has trauma → emotional_pull should be 80+
   - If content is generic → scores should be 40-60 range

5. NEVER give these fake patterns:
   ❌ All scores between 70-80 (fake uniform)
   ❌ Overall = average of others exactly (fake formula)
   ❌ Hook = 70 for every ad (lazy analysis)

OUTPUT STRICT JSON:
{{
  "content_verification": {{
    "fingerprint_hash": "{fingerprint.content_hash}",
    "first_10_words": "EXACT FIRST 10 WORDS HERE",
    "last_10_words": "EXACT LAST 10 WORDS HERE",
    "content_specific_notes": "What makes THIS ad unique vs generic"
  }},
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
  "score_justification": {{
    "hook_why": "SPECIFIC reason based on first 10 words",
    "credibility_why": "SPECIFIC reason based on proof/claims",
    "emotional_why": "SPECIFIC reason based on emotional keywords found"
  }},
  "strategic_summary": "SPECIFIC analysis of THIS content - mention actual phrases used",
  "critical_weaknesses": [
    {{
      "issue": "Specific problem with THIS ad",
      "precise_fix": "Specific fix based on content"
    }}
  ],
  "persona_reactions": [
    {{
      "persona": "19yo Lagos Scroller",
      "reaction": "SPECIFIC reaction to THIS hook",
      "exact_quote": "What they would say"
    }}
  ],
  "is_generic_response": false  // You will be rejected if this is true
}}

REMEMBER: Analyze the SPECIFIC content with fingerprint {fingerprint.content_hash}. 
Generic scores will be detected and rejected."""

        return prompt

    def validate_scores_are_content_specific(self, scores: Dict[str, int], 
                                           fingerprint: ContentFingerprint) -> tuple:
        """
        Check if scores are actually unique or generic fake scores
        Returns: (is_valid, reason_if_invalid)
        """
        score_values = list(scores.values())

        # Check 1: All scores are identical (e.g., all 70s)
        if len(set(score_values)) == 1:
            return False, "All scores identical - generic response detected"

        # Check 2: All scores within 10-point range (suspicious uniformity)
        if max(score_values) - min(score_values) < 15:
            return False, "Scores too uniform - fake analysis detected"

        # Check 3: Hook score doesn't match content pattern
        if fingerprint.has_trauma_pattern and scores.get("hook_strength", 0) < 70:
            return False, "Trauma pattern in content but hook scored low - mismatch"

        if fingerprint.has_scam_pattern and scores.get("hook_strength", 0) > 50:
            return False, "Scam pattern detected but hook scored high - mismatch"

        if fingerprint.has_trauma_pattern and scores.get("emotional_pull", 0) < 70:
            return False, "Trauma content but low emotional score - mismatch"

        # Check 4: All scores are multiples of 5 (suspicious rounding)
        if all(s % 5 == 0 for s in score_values):
            return False, "All scores end in 0/5 - suspicious rounding"

        # Check 5: Overall is exact mathematical average (too perfect)
        calculated_avg = sum(score_values[1:]) / len(score_values[1:])  # Exclude overall
        if abs(scores.get("overall", 0) - calculated_avg) < 2:
            return False, "Overall is exact average - formulaic fake score"

        return True, "Scores appear content-specific"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def analyze_ad_v59(self, request_data: Dict[str, Any], files: List = None) -> Dict[str, Any]:
        """
        v5.9: Real analysis only - no fake scores, retry if generic
        """

        # Extract content
        ad_copy = request_data.get("ad_copy", "")
        video_script = request_data.get("video_script", "")
        content = video_script if video_script else ad_copy

        if not content.strip():
            raise ValueError("No content provided for analysis")

        # Create fingerprint
        fingerprint = self.fingerprint_content(content)

        # Build strict prompt
        prompt = self.build_strict_prompt_v59(content, fingerprint, request_data)

        # Call AI
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openai/gpt-4o",
                    "messages": [{"role": "system", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "max_tokens": 4000,
                    "temperature": 0.3  # Slight creativity but focused
                }
            )

        response.raise_for_status()
        result = response.json()
        analysis = json.loads(result["choices"][0]["message"]["content"])

        # Validate scores are content-specific
        scores = analysis.get("scores", {})
        is_valid, validation_msg = self.validate_scores_are_content_specific(scores, fingerprint)

        if not is_valid:
            # Retry with stronger warning
            raise ValueError(f"Generic score detected: {validation_msg}. Retrying...")

        # Add metadata
        analysis["analysis_metadata"] = {
            "engine_version": "5.9",
            "fingerprint": {
                "hash": fingerprint.content_hash,
                "word_count": fingerprint.word_count,
                "trauma_detected": fingerprint.has_trauma_pattern,
                "scam_detected": fingerprint.has_scam_pattern
            },
            "validation": {
                "passed": True,
                "message": validation_msg
            }
        }

        return analysis


def get_ai_engine():
    return AIEngineV59()
