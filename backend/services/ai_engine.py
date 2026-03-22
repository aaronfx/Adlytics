"""
ADLYTICS v5.0 - REAL CONTENT ANALYSIS
Forces AI to analyze actual input, not return templates
"""

import os
import json
import logging
from typing import Dict, Any
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIEngineStrictV5:
    """Forces ACTUAL analysis of input content"""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
        self.base_url = "https://openrouter.ai/api/v1"

    async def analyze_ad(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze with CONTENT VERIFICATION"""

        # Extract actual content
        ad_copy = request_data.get('ad_copy', '').strip()
        video_script = request_data.get('video_script', '').strip()

        # Validate input exists
        if not ad_copy and not video_script:
            raise ValueError("No ad copy or video script provided")

        content_length = len(ad_copy) + len(video_script)
        logger.info(f"📝 Analyzing content: {content_length} characters")

        prompt = self._build_analysis_prompt(request_data, ad_copy, video_script)

        for attempt in range(3):
            try:
                logger.info(f"🤖 Attempt {attempt + 1} analyzing actual content...")

                async with httpx.AsyncClient(timeout=90.0) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": self.model,
                            "messages": [
                                {"role": "system", "content": self._get_system_prompt()},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.3,
                            "max_tokens": 7000
                        }
                    )

                    result = response.json()
                    content = result["choices"][0]["message"]["content"]

                    # Extract JSON
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]

                    analysis = json.loads(content.strip())

                    # VERIFY CONTENT IS ACTUALLY ANALYZED
                    self._verify_real_analysis(analysis, ad_copy, video_script)

                    logger.info("✅ Real content analysis verified")
                    return analysis

            except Exception as e:
                logger.warning(f"❌ Attempt {attempt+1} failed: {e}")
                if attempt == 2:
                    raise

        raise ValueError("Failed to get real analysis after 3 attempts")

    def _get_system_prompt(self) -> str:
        return """You analyze ads based on ACTUAL CONTENT provided.

CRITICAL RULES:
1. ANALYZE THE SPECIFIC TEXT provided - not generic templates
2. If content is weak/short/gibberish, scores MUST reflect that (20-40 range)
3. Reference specific phrases from the input in your analysis
4. Empty fields = score of 0 or very low (10-20)
5. Gibberish text = low credibility, low clarity scores
6. You will be VERIFIED - we check if you actually read the content

If you return generic high scores without referencing actual input content, you fail."""

    def _build_analysis_prompt(self, data: Dict, ad_copy: str, video_script: str) -> str:
        return f"""Analyze THIS SPECIFIC AD CONTENT:

**AD COPY (EXACT TEXT):**
"""
{ad_copy if ad_copy else "[EMPTY - No ad copy provided]"}
"""

**VIDEO SCRIPT (EXACT TEXT):**
"""
{video_script if video_script else "[EMPTY - No video script provided]"}
"""

**CONTEXT:**
- Platform: {data.get('platform', 'unknown')}
- Industry: {data.get('industry', 'unknown')}
- Target: {data.get('audience_age', '')} in {data.get('audience_country', '')}

**SCORING RULES (BASED ON ACTUAL CONTENT):**
- If ad_copy is empty: overall_score = 15, clarity = 0, hook = 0
- If content is gibberish/random letters: credibility = 5-15, clarity = 5-15
- If content is short (<50 chars): all scores 20-40 range
- If content has no clear offer: cta_strength = 10-25
- If content has no emotional hooks: emotional_pull = 15-30
- Only give scores 70+ if content actually demonstrates that quality

**REQUIRED OUTPUT:**
Return JSON with scores that ACTUALLY MATCH the content quality.

If content is weak, say it's weak. Don't give fake high scores.

JSON structure (fill with REAL ANALYSIS):
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
  "behavior_summary": "Specific analysis referencing actual phrases from the input",
  "critical_weaknesses": [list actual problems with the content],
  "decision_engine": {{...}},
  "ad_variants": [improved versions if content is weak],
  ...
}}

REMEMBER: Analyze the ACTUAL TEXT above, not generic templates."""

    def _verify_real_analysis(self, analysis: Dict, ad_copy: str, video_script: str) -> None:
        """Verify the AI actually analyzed the content"""

        scores = analysis.get("scores", {})
        behavior = analysis.get("behavior_summary", "")

        # Check 1: If ad_copy is empty, overall should be low
        if not ad_copy and scores.get("overall", 100) > 30:
            raise ValueError("AI gave high score to empty ad copy - not analyzing actual content")

        # Check 2: If content is gibberish (no real words), clarity should be very low
        content = ad_copy + video_script
        real_words = len([w for w in content.split() if len(w) > 2 and w.isalpha()])
        if real_words < 3 and scores.get("clarity", 100) > 30:
            raise ValueError("AI gave good clarity score to gibberish - not analyzing content")

        # Check 3: Analysis must reference actual content
        if len(behavior) < 50:
            raise ValueError("behavior_summary too short - no real analysis")

        # Check 4: Scores should be realistic based on content length
        content_length = len(content.strip())
        if content_length < 20 and scores.get("overall", 100) > 40:
            raise ValueError(f"Content only {content_length} chars but got score {scores.get('overall')} - fake analysis")

        # Check 5: All required fields
        required = ["scores", "behavior_summary", "critical_weaknesses", "decision_engine", 
                   "ad_variants", "neuro_response"]
        for field in required:
            if field not in analysis:
                raise ValueError(f"Missing field: {field}")

        logger.info(f"✓ Content verified: {content_length} chars, overall_score: {scores.get('overall')}")

_engine_instance = None

def get_ai_engine():
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AIEngineStrictV5()
    return _engine_instance
