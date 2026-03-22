"""
ADLYTICS AI Engine - v5.9 Strict Scoring
Real content-specific analysis, no fake scores
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
    content_hash: str
    word_count: int
    first_20_chars: str
    last_20_chars: str
    has_trauma_pattern: bool
    has_scam_pattern: bool
    emotional_keywords: List[str]

class AIValidationError(Exception):
    """Raised when AI returns invalid/generic scores"""
    pass

class AIEngine:
    """v5.9: Real analysis only - no fake scores"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"

    def fingerprint_content(self, content: str) -> ContentFingerprint:
        """Create unique fingerprint to verify AI analyzes actual content"""
        content_lower = content.lower()

        emotional_words = ["lost", "pain", "struggle", "truth", "honest", "transparent", 
                          "scam", "fear", "worry", "stress", "failed", "quit", "stop",
                          "burned", "cheated", "mistake"]
        found_emotional = [w for w in emotional_words if w in content_lower]

        trauma_patterns = ["i lost", "i failed", "i quit", "i stopped", "burned", "scammed"]
        has_trauma = any(p in content_lower for p in trauma_patterns)

        scam_patterns = ["turn", "into", "guarantee", "no experience", "risk free", "10x"]
        has_scam = any(p in content_lower for p in scam_patterns)

        return ContentFingerprint(
            content_hash=hashlib.md5(content.encode()).hexdigest()[:8],
            word_count=len(content.split()),
            first_20_chars=content[:20].strip(),
            last_20_chars=content[-20:].strip() if len(content) >= 20 else content.strip(),
            has_trauma_pattern=has_trauma,
            has_scam_pattern=has_scam,
            emotional_keywords=found_emotional
        )

    def validate_scores_content_specific(self, scores: Dict[str, int], 
                                        fingerprint: ContentFingerprint) -> tuple:
        """Check if scores are unique or generic"""
        score_values = [v for k, v in scores.items() if k != "overall"]

        # Check 1: All identical
        if len(set(score_values)) <= 2:
            return False, "Scores too similar - generic response"

        # Check 2: All within 15 points
        if max(score_values) - min(score_values) < 15:
            return False, "Scores too uniform - fake analysis"

        # Check 3: Trauma content must score high on emotional
        if fingerprint.has_trauma_pattern and scores.get("emotional_pull", 0) < 60:
            return False, "Trauma content should have high emotional score"

        # Check 4: Scam content must score low
        if fingerprint.has_scam_pattern and scores.get("credibility", 0) > 50:
            return False, "Scam content should have low credibility"

        return True, "Scores appear content-specific"

    def build_prompt(self, content: str, fingerprint: ContentFingerprint, 
                    request_data: Dict[str, Any]) -> str:
        """Build strict v5.9 prompt"""

        country = request_data.get("audience_country", "nigeria")
        platform = request_data.get("platform", "tiktok")

        return f"""You are ADLYTICS v5.9 - Analyze THIS specific content only.

CONTENT FINGERPRINT: {fingerprint.content_hash}
FIRST WORDS: "{fingerprint.first_20_chars}"
LAST WORDS: "{fingerprint.last_20_chars}"
WORDS: {fingerprint.word_count}
TRAUMA DETECTED: {fingerprint.has_trauma_pattern}
SCAM DETECTED: {fingerprint.has_scam_pattern}

CONTENT TO ANALYZE:
---
{content}
---

SCORE THIS SPECIFIC CONTENT (0-100):

hook_strength: Does "{fingerprint.first_20_chars[:40]}" stop the scroll?
- 90-100: Specific trauma/number/provocation
- 70-80: Clear but generic  
- 40-60: Boring/unclear
- 10-30: Filler words

credibility: Trust level?
- 90-100: Shows losses, transparency
- 70-80: Some proof
- 40-60: Claims only
- 10-30: Scam patterns

emotional_pull: Emotional connection?
- 90-100: Personal trauma/story
- 70-80: Clear pain point
- 40-60: Generic
- 10-30: None

clarity, cta_strength, audience_match, platform_fit: Score 0-100

RULES:
1. Scores MUST be diverse (not all 70s)
2. Trauma content → emotional_pull 80+
3. Scam content → credibility 20-
4. Reference fingerprint {fingerprint.content_hash} in response

OUTPUT JSON:
{{
  "content_verification": {{
    "fingerprint": "{fingerprint.content_hash}",
    "first_10_words": "...",
    "last_10_words": "..."
  }},
  "scores": {{
    "overall": 0, "hook_strength": 0, "clarity": 0, "credibility": 0,
    "emotional_pull": 0, "cta_strength": 0, "audience_match": 0, "platform_fit": 0
  }},
  "strategic_summary": "Specific analysis of THIS content",
  "critical_weaknesses": [{{"issue": "...", "precise_fix": "..."}}],
  "persona_reactions": [
    {{"persona": "19yo Lagos", "reaction": "...", "exact_quote": "..."}},
    {{"persona": "38yo Abuja", "reaction": "...", "exact_quote": "..."}},
    {{"persona": "25-34 Target", "reaction": "...", "exact_quote": "..."}},
    {{"persona": "UK Compliance", "reaction": "...", "exact_quote": "..."}},
    {{"persona": "US Buyer", "reaction": "...", "exact_quote": "..."}}
  ]
}}"""

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def analyze_ad(self, request_data: Dict[str, Any], files: List = None) -> Dict[str, Any]:
        """Main analysis - v5.9 strict mode"""

        ad_copy = request_data.get("ad_copy", "")
        video_script = request_data.get("video_script", "")
        content = video_script if video_script else ad_copy

        if not content.strip():
            raise AIValidationError("No content provided")

        fingerprint = self.fingerprint_content(content)
        prompt = self.build_prompt(content, fingerprint, request_data)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://adlytics.ai"
                },
                json={
                    "model": "openai/gpt-4o",
                    "messages": [{"role": "system", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "max_tokens": 4000,
                    "temperature": 0.3
                }
            )

        response.raise_for_status()
        result = response.json()
        analysis = json.loads(result["choices"][0]["message"]["content"])

        # Validate scores are content-specific
        scores = analysis.get("scores", {})
        is_valid, msg = self.validate_scores_content_specific(scores, fingerprint)

        if not is_valid:
            raise AIValidationError(f"Generic scores detected: {msg}")

        # Add metadata
        analysis["_metadata"] = {
            "version": "5.9",
            "fingerprint": fingerprint.content_hash,
            "validation": msg
        }

        return analysis


def get_ai_engine():
    return AIEngine()
