"""
ADLYTICS v5.5 - AI Engine with Full Production Copy & Country Intelligence (CLEAN)
Fixes: Proper prompt formatting, correct scoring logic, validation balance
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
            "Reliance on social proof and peer validation",
            "Mobile-first digital access",
            "Trust in video over text claims",
            "Entrepreneurial hustle culture",
            "Installment payment preference",
            "Voice note trust preference"
        ],
        "scam_triggers": [
            "Get rich quick without substance",
            "Vague income claims",
            "No verifiable contact",
            "International transfer requests"
        ],
        "trust_builders": [
            "Local testimonials with faces",
            "Community validation",
            "Video testimonials",
            "Domestic currency",
            "Official registration",
            "Physical location"
        ],
        "neuro_triggers": {
            "dopamine": "Financial freedom",
            "fear": "Scam avoidance",
            "trust": "Community proof",
            "urgency": "Economic pressure"
        }
    },
    "kenya": {
        "currency": "KSh",
        "currency_name": "Shilling",
        "behavioral_traits": [
            "Mobile money integration",
            "Community decision making",
            "Educational value emphasis"
        ],
        "trust_builders": [
            "Mobile payment",
            "Community endorsement",
            "Local presence"
        ],
        "neuro_triggers": {
            "trust": "Community leader",
            "urgency": "Seasonal cycles"
        }
    },
    "united_states": {
        "currency": "$",
        "currency_name": "USD",
        "behavioral_traits": [
            "Individual achievement focus",
            "Privacy awareness",
            "Influencer skepticism"
        ],
        "trust_builders": [
            "Money-back guarantee",
            "Third-party reviews"
        ],
        "neuro_triggers": {
            "dopamine": "Side hustle",
            "fear": "Job security",
            "trust": "Accreditation"
        }
    },
    "united_kingdom": {
        "currency": "£",
        "currency_name": "Pound",
        "behavioral_traits": [
            "Reserved skepticism",
            "Understated communication",
            "Regulation awareness"
        ],
        "trust_builders": [
            "Official registration",
            "Transparent terms"
        ],
        "neuro_triggers": {
            "trust": "Verification",
            "fear": "Uncertainty"
        }
    },
    "india": {
        "currency": "₹",
        "currency_name": "Rupee",
        "behavioral_traits": [
            "Family decision dynamics",
            "Regional diversity",
            "Value-conscious"
        ],
        "trust_builders": [
            "Tax transparency",
            "Regional language",
            "Flexible payment"
        ],
        "neuro_triggers": {
            "trust": "Family approval",
            "dopamine": "Status"
        }
    }
}

DEFAULT_PROFILE = {
    "currency": "$",
    "currency_name": "USD",
    "behavioral_traits": ["General best practices"],
    "scam_triggers": ["Unrealistic promises"],
    "trust_builders": ["Testimonials"],
    "neuro_triggers": {"dopamine": "Success", "trust": "Social proof"}
}


class AIEngineV5:
    """V5.5 AI Engine - Clean implementation with proper scoring"""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
        self.base_url = "https://openrouter.ai/api/v1"

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set")

        logger.info(f"🤖 Using model: {self.model}")

    def _get_country_profile(self, country: str) -> Dict[str, Any]:
        """Get behavioral profile for selected country"""
        country_lower = country.lower().replace(" ", "_")
        profile = COUNTRY_PROFILES.get(country_lower, DEFAULT_PROFILE)
        logger.info(f"🌍 Loaded profile: {country} ({profile['currency']})")
        return profile

    async def analyze_ad(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze ad with proper content handling"""
        ad_copy = request_data.get('ad_copy', '').strip()
        video_script = request_data.get('video_script', '').strip()
        country = request_data.get('country', 'united_states')

        if not ad_copy and not video_script:
            raise ValueError("No content provided")

        country_profile = self._get_country_profile(country)

        # Log input for debugging
        content_preview = (ad_copy + video_script)[:100] + "..." if len(ad_copy + video_script) > 100 else (ad_copy + video_script)
        logger.info(f"📄 Input content: {content_preview}")
        logger.info(f"📊 Content length: {len(ad_copy + video_script)} chars")

        prompt = self._build_prompt(request_data, ad_copy, video_script, country_profile)

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
                                {"role": "system", "content": self._get_system_prompt(country_profile)},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.3,
                            "max_tokens": 8000
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

                    # Verification (balanced - not too strict)
                    self._verify_analysis(analysis, ad_copy, video_script, country_profile)

                    logger.info(f"✅ Analysis complete: {analysis.get('scores', {}).get('overall', 'N/A')} overall")
                    return analysis

            except Exception as e:
                logger.warning(f"Attempt {attempt+1} failed: {str(e)}")
                if attempt == 2:
                    raise

        raise ValueError("Analysis failed after 3 attempts")

    def _get_system_prompt(self, country_profile: Dict) -> str:
        """Clean system prompt without formatting issues"""
        currency = country_profile['currency']

        lines = [
            f"You are an elite performance marketing strategist for {currency} markets.",
            "",
            "BEHAVIORAL PROFILE:",
        ]

        for trait in country_profile['behavioral_traits']:
            lines.append(f"- {trait}")

        lines.extend([
            "",
            "CRITICAL RULES:",
            f"1. Use {currency} for ALL monetary amounts",
            "2. NO specific brand names (banks, apps, companies)",
            "3. Use generic terms: 'mobile payment', 'official registration'",
            "4. Generate FULL production copy (100-200 words per variant)",
            "5. Hook: 15-30 words, Body: 100-200 words, CTA: 5-10 words",
            "6. Score ACTUAL content provided - if content is strong, score 70+",
            "7. If content is weak/empty, score 10-40 honestly",
            "8. Reference specific phrases from input in your analysis",
            "9. improved_ad: 200+ words combining best elements",
            "10. 5 variants targeting different psychological angles",
            "",
            "SCORING GUIDE:",
            "- 80-100: Excellent, ready to run",
            "- 60-79: Good, minor improvements needed",
            "- 40-59: Fair, significant issues",
            "- 20-39: Poor, major overhaul needed",
            "- 0-19: Critical problems or empty",
            "",
            "The user will copy-paste your output into ad platforms. Make it complete and ready to use."
        ])

        return "\n".join(lines)

    def _build_prompt(self, data: Dict, ad_copy: str, video_script: str, country_profile: Dict) -> str:
        """Clean prompt builder"""
        content = ad_copy + video_script
        is_short = len(content) < 50
        has_gibberish = len([w for w in content.split() if len(w) > 2 and w.isalpha()]) < 3

        country = data.get('country', 'united_states')
        currency = country_profile['currency']

        quality_note = ""
        if not ad_copy:
            quality_note = "⚠️ NO AD COPY PROVIDED"
        elif has_gibberish:
            quality_note = "⚠️ GIBBERISH CONTENT DETECTED"
        elif is_short:
            quality_note = "⚠️ SHORT CONTENT"

        # Build variant instructions based on country
        variant_instructions = self._get_variant_instructions(country)

        prompt_parts = [
            f"TARGET MARKET: {country} ({currency})",
            f"PLATFORM: {data.get('platform', 'unknown')}",
            f"INDUSTRY: {data.get('industry', 'unknown')}",
            "",
            f"{quality_note}",
            "",
            "AD COPY TO ANALYZE:",
            "```",
            ad_copy if ad_copy else "[EMPTY - NO AD COPY PROVIDED]",
            "```",
            "",
            "VIDEO SCRIPT:",
            "```",
            video_script if video_script else "[EMPTY - NO VIDEO SCRIPT]",
            "```",
            "",
            variant_instructions,
            "",
            "OUTPUT REQUIREMENTS:",
            "1. Score based on ACTUAL content quality (don't default to low scores)",
            "2. If content is good, give high scores (70-90)",
            "3. If content is bad, give low scores (10-40) and explain why",
            "4. behavior_summary: Reference specific phrases from input",
            "5. critical_weaknesses: Specific issues with fixes",
            "6. Generate 5 complete variants (100-200 words each)",
            "7. improved_ad: 200+ words, production-ready",
            "8. video_execution_analysis: Full details if video provided",
            "9. roi_comparison: Structured object with your_projection/industry_average/top_performer",
            "10. competitor_advantage: Structured object with unique_angles/defensible_moat/vulnerability",
            "",
            "Return valid JSON matching the expected schema."
        ]

        return "\n".join(prompt_parts)

    def _get_variant_instructions(self, country: str) -> str:
        """Get variant instructions by country"""
        country_lower = country.lower().replace(" ", "_")

        if country_lower == "nigeria":
            return """VARIANT ANGLES FOR NIGERIA:
1. Trust Builder: Address scam fears directly ("I know you've been burned...")
2. Hustle Culture: Appeal to entrepreneurial spirit
3. Community: Social proof ("Join hundreds...")
4. Values: Cultural alignment
5. Accessibility: Local payment methods, no foreign accounts"""

        elif country_lower == "kenya":
            return """VARIANT ANGLES FOR KENYA:
1. Mobile Money: Emphasize mobile payment integration
2. Community: Harambee/community effort angle
3. Education: Family value and education focus
4. Side Hustle: For employed professionals
5. Youth: Opportunity for young people"""

        elif country_lower == "united_states":
            return """VARIANT ANGLES FOR US:
1. Individual Success: Personal achievement
2. Side Hustle: Extra income stream
3. Financial Independence: FIRE movement
4. Recession Proof: Economic security
5. Flexibility: Work from anywhere"""

        elif country_lower == "india":
            return """VARIANT ANGLES FOR INDIA:
1. Family: Decision consideration
2. Value: Quality at good price
3. Regional: Local language comfort
4. Digital: Payment convenience
5. Career: Educational advancement"""

        else:
            return """VARIANT ANGLES:
1. Problem/Solution: Direct pain point addressing
2. Social Proof: Testimonials and results
3. Urgency: Time-sensitive opportunity
4. Educational: Teaching angle
5. Community: Group belonging"""

    def _verify_analysis(self, analysis: Dict, ad_copy: str, video_script: str, country_profile: Dict) -> None:
        """Balanced verification - catches major issues without being too strict"""
        scores = analysis.get("scores", {})
        content = (ad_copy + video_script).strip()
        content_len = len(content)
        currency = country_profile['currency']

        # Only verify extreme cases
        if content_len < 10 and scores.get("overall", 0) > 50:
            raise ValueError(f"Empty content got high score: {scores.get('overall')}")

        if content_len > 100 and scores.get("overall", 100) < 20:
            logger.warning(f"Substantial content got very low score - may be correct if quality is poor")

        # Check structure exists
        if not analysis.get("improved_ad"):
            raise ValueError("Missing improved_ad")

        if not analysis.get("ad_variants"):
            raise ValueError("Missing ad_variants")

        if len(analysis.get("ad_variants", [])) < 3:
            raise ValueError(f"Only {len(analysis.get('ad_variants', []))} variants, need at least 3")

        # Check for currency usage (warn but don't fail)
        improved_body = analysis.get("improved_ad", {}).get("final_body", "").lower()
        if currency != "$" and currency.lower() not in improved_body:
            logger.warning(f"Currency {currency} not found in improved_ad - may need retry")

        logger.info(f"✅ Verified: {len(analysis.get('ad_variants', []))} variants, score: {scores.get('overall', 'N/A')}")


_engine_instance = None

def get_ai_engine():
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AIEngineV5()
    return _engine_instance


class AIValidationError(Exception):
    pass
