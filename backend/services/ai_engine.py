"""
ADLYTICS v5.4.1 - AI Engine with Generalized Country Behavioral Intelligence (BUG FIXES)
"""

import os
import json
import logging
from typing import Dict, Any
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Country-specific behavioral profiles - GENERALIZED
COUNTRY_PROFILES = {
    "nigeria": {
        "currency": "₦",
        "currency_name": "Naira",
        "behavioral_traits": [
            "Extremely high scam sensitivity due to Ponzi scheme history",
            "Heavy reliance on social proof and peer validation",
            "Mobile-first digital access",
            "Instant messaging apps are primary business channels",
            "Trust in video proof over text claims",
            "Cultural language and local expressions resonate",
            "Hustle culture and entrepreneurial pride",
            "Installment payment preference for high-ticket items",
            "Physical location proof required for legitimacy",
            "Voice notes convey more trust than text"
        ],
        "scam_triggers": [
            "Get rich quick phrases without substance",
            "Vague income claims without proof",
            "No verifiable contact information",
            "International money transfer requests",
            "Urgency without transparency"
        ],
        "trust_builders": [
            "Local testimonials with real faces and names",
            "Community group validation",
            "Video testimonials in local languages",
            "Domestic currency transactions",
            "Official business registration mentions",
            "Physical office location verification",
            "Local customer service availability"
        ],
        "neuro_triggers": {
            "dopamine": "Financial freedom from entrepreneurial success",
            "fear": "Missing out on legitimate opportunity combined with scam fear",
            "trust": "Community validation and cultural alignment",
            "urgency": "Seasonal opportunities and economic pressures"
        }
    },
    "kenya": {
        "currency": "KSh",
        "currency_name": "Shilling",
        "behavioral_traits": [
            "Mobile money integration expectation",
            "Community-focused decision making",
            "Educational value emphasis",
            "Regional trust considerations",
            "Local language integration preference"
        ],
        "trust_builders": [
            "Mobile payment integration",
            "Local community endorsements",
            "Telecommunications partnerships",
            "Physical presence verification"
        ],
        "neuro_triggers": {
            "trust": "Community leader endorsements",
            "urgency": "Seasonal economic cycles"
        }
    },
    "south_africa": {
        "currency": "R",
        "currency_name": "Rand",
        "behavioral_traits": [
            "Diverse cultural segmentation important",
            "Infrastructure resilience appeals",
            "Multiple language localization",
            "Formal business structure preference"
        ],
        "trust_builders": [
            "Official registration mentions",
            "Compliance certifications",
            "Local case studies by region"
        ],
        "neuro_triggers": {
            "trust": "Formal structure and accreditation",
            "fear": "Economic instability"
        }
    },
    "united_states": {
        "currency": "$",
        "currency_name": "USD",
        "behavioral_traits": [
            "Individual achievement focus",
            "Privacy protection awareness",
            "Credit card protection familiarity",
            "Influencer skepticism"
        ],
        "trust_builders": [
            "Money-back guarantees",
            "Third-party reviews",
            "Privacy policy transparency"
        ],
        "neuro_triggers": {
            "dopamine": "Side hustle and entrepreneurship culture",
            "fear": "Economic uncertainty and job security",
            "trust": "Third-party accreditation and reviews"
        }
    },
    "united_kingdom": {
        "currency": "£",
        "currency_name": "Pound",
        "behavioral_traits": [
            "Reserved skepticism with thorough research",
            "Understated communication preference",
            "Financial regulation awareness",
            "Subtle humor appreciation"
        ],
        "trust_builders": [
            "Official business registration",
            "Transparent terms and conditions",
            "Professional accreditation"
        ],
        "neuro_triggers": {
            "trust": "Official verification",
            "fear": "Brexit/economic uncertainty"
        }
    },
    "india": {
        "currency": "₹",
        "currency_name": "Rupee",
        "behavioral_traits": [
            "Cash on delivery preference for physical goods",
            "Family decision-making dynamics",
            "Regional language diversity",
            "Value-conscious purchasing",
            "Digital payment adoption"
        ],
        "trust_builders": [
            "Tax registration transparency",
            "Regional language support",
            "Flexible payment options",
            "Local testimonial validation"
        ],
        "neuro_triggers": {
            "trust": "Family approval and social validation",
            "dopamine": "Career advancement and status"
        }
    },
    "ghana": {
        "currency": "GH₵",
        "currency_name": "Cedi",
        "behavioral_traits": [
            "Mobile money adoption",
            "Similar behavioral patterns to Nigeria with lower scam sensitivity",
            "Local transport and culture references",
            "Strong educational value emphasis"
        ],
        "trust_builders": [
            "Mobile payment options",
            "Community validation",
            "Educational credentials"
        ],
        "neuro_triggers": {
            "trust": "Community endorsement",
            "dopamine": "Educational achievement"
        }
    }
}

DEFAULT_PROFILE = {
    "currency": "$",
    "currency_name": "USD",
    "behavioral_traits": ["General international best practices"],
    "scam_triggers": ["Unrealistic promises", "No contact info"],
    "trust_builders": ["Testimonials", "Money-back guarantee"],
    "neuro_triggers": {"dopamine": "Success", "trust": "Social proof"}
}


class AIEngineV5:
    """V5.4.1 AI Engine - Fixed syntax issues"""

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
        logger.info(f"🌍 Loaded profile for: {country} (Currency: {profile['currency']})")
        return profile

    async def analyze_ad(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze ad with country-specific behavioral adaptation"""
        ad_copy = request_data.get('ad_copy', '').strip()
        video_script = request_data.get('video_script', '').strip()
        country = request_data.get('country', 'united_states')

        if not ad_copy and not video_script:
            raise ValueError("No content provided")

        country_profile = self._get_country_profile(country)
        request_data['country_profile'] = country_profile

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

                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]

                    analysis = json.loads(content.strip())
                    self._verify_analysis(analysis, ad_copy, video_script, country_profile)

                    return analysis

            except Exception as e:
                logger.warning(f"Attempt {attempt+1} failed: {e}")
                if attempt == 2:
                    raise

        raise ValueError("Analysis failed")

    def _get_system_prompt(self, country_profile: Dict) -> str:
        """Generate system prompt - FIXED"""
        currency = country_profile['currency']
        currency_name = country_profile['currency_name']

        behavioral_text = "\n".join([f"- {trait}" for trait in country_profile['behavioral_traits']])
        scam_text = "\n".join([f"- {trigger}" for trigger in country_profile['scam_triggers']])
        trust_text = "\n".join([f"- {builder}" for builder in country_profile['trust_builders']])
        neuro_keys = ", ".join(country_profile['neuro_triggers'].keys())

        return f"""You are an elite performance marketing strategist specializing in {currency_name} ({currency}) markets.

COUNTRY-SPECIFIC BEHAVIORAL PROFILE:

Behavioral Traits:
{behavioral_text}

AVOID THESE SCAM TRIGGERS:
{scam_text}

USE THESE TRUST BUILDERS (General concepts, NOT specific brand names):
{trust_text}

CRITICAL RULES:
1. Use {currency} for ALL monetary amounts - NEVER use $
2. Adapt hook/body/CTA to local behavioral patterns above
3. DO NOT mention specific banks, telecom companies, or regulatory bodies by name
4. DO NOT mention specific payment apps or platforms by name
5. Use general terms like 'mobile payment,' 'official registration,' 'local currency,' 'domestic banks'
6. Generate COMPLETE, READY-TO-RUN ad copy (100-200 words per variant)
7. Hook: 15-30 words adapted to local attention spans
8. Body: Full persuasion structure with LOCAL pain points (economic struggles, trust issues)
9. Each variant targets different neuro triggers: {neuro_keys}
10. improved_ad must be 200+ words with local trust signals (generic, not specific brands)
11. Persona reactions must reflect local demographic behaviors
12. Objection detection must include country-specific concerns (generic references to past scams, not specific names)
13. Focus on BEHAVIORAL PSYCHOLOGY, not specific infrastructure

The user will COPY-PASTE your output directly into advertising platforms. Make it complete and culturally resonant WITHOUT mentioning specific companies, banks, or regulatory codes."""

    def _build_prompt(self, data: Dict, ad_copy: str, video_script: str, country_profile: Dict) -> str:
        """Build prompt with country context - FIXED"""
        content = ad_copy + video_script
        is_short = len(content) < 50
        is_gibberish = len([w for w in content.split() if len(w) > 2 and w.isalpha()]) < 2
        country = data.get('country', 'united_states')
        currency = country_profile['currency']

        quality_note = ""
        if not ad_copy:
            quality_note = "⚠️ NO AD COPY - All scores should be 10-25"
        elif is_gibberish:
            quality_note = "⚠️ GIBBERISH CONTENT - Clarity/Credibility 5-20"
        elif is_short:
            quality_note = "⚠️ SHORT CONTENT - Scores 20-40"

        # Build instructions
        if country.lower().replace(" ", "_") == "nigeria":
            country_instructions = """NIGERIA-SPECIFIC INSTRUCTIONS (Generalized):
- Variant 1 (Trust Builder): Address scam fear directly WITHOUT naming specific schemes. Use "I know you've been burned before..."
- Variant 2 (Hustle Culture): Appeal to entrepreneurial spirit and local work ethic
- Variant 3 (Community): Use "Join hundreds already earning" social proof (specific numbers, not brands)
- Variant 4 (Values): Align with cultural values and community mindset
- Variant 5 (Accessibility): Emphasize "local payment methods" and "domestic support"
- improved_ad: MUST use ₦, mention "official registration" (not specific codes), "local customer service"
- NEVER mention: specific banks, specific regulatory bodies, specific telecom companies"""
        elif country.lower().replace(" ", "_") == "kenya":
            country_instructions = """KENYA-SPECIFIC INSTRUCTIONS (Generalized):
- Variant 1: Emphasize mobile money integration (generic term)
- Variant 2: Community/harambee (community effort) angle
- Variant 3: Educational value for family
- Variant 4: Side hustle for employed professionals
- Variant 5: Youth opportunity focus
- Use KSh exclusively, emphasize community validation"""
        elif country.lower().replace(" ", "_") == "united_states":
            country_instructions = """US-SPECIFIC INSTRUCTIONS:
- Variant 1: Individual achievement/entrepreneurship
- Variant 2: Side hustle culture
- Variant 3: Financial independence
- Variant 4: Recession-proof income
- Variant 5: Work flexibility
- Use $, focus on individual success"""
        elif country.lower().replace(" ", "_") == "india":
            country_instructions = """INDIA-SPECIFIC INSTRUCTIONS (Generalized):
- Variant 1: Family decision consideration
- Variant 2: Value-conscious with quality emphasis
- Variant 3: Regional language comfort
- Variant 4: Digital payment convenience
- Variant 5: Educational career advancement
- Use ₹, emphasize "official tax registration" (not GST specifically), family approval"""
        else:
            country_instructions = "Create 5 diverse angles targeting different psychological triggers appropriate for this market."

        prompt_text = f"""Analyze this ad content for {country} market ({currency}):

{quality_note}

ORIGINAL AD COPY:
```
{ad_copy or "[EMPTY]"}
```

ORIGINAL VIDEO SCRIPT:
```
{video_script or "[EMPTY]"}
```

PLATFORM: {data.get('platform', 'unknown')}
INDUSTRY: {data.get('industry', 'unknown')}
TARGET COUNTRY: {country}
CURRENCY: {currency}

{country_instructions}

Return JSON with this structure:
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
  "behavior_summary": "Detailed analysis referencing {country} behavioral patterns (150+ chars). Focus on psychology, not infrastructure.",
  "critical_weaknesses": [{{"issue": "...", "severity": "High/Medium/Low", "impact": "...", "fix": "..."}}],
  "decision_engine": {{
    "should_run": true/false,
    "confidence": "0-100%",
    "reasoning": "Detailed {country}-specific reasoning (150+ chars)",
    "expected_profit": number,
    "roi_prediction": "X.Xx",
    "profit_scenarios": {{"low_case": number, "base_case": number, "high_case": number}},
    "kill_threshold": "...",
    "scale_threshold": "...",
    "confidence_breakdown": {{"hook": 0-100, "offer": 0-100, "audience": 0-100}}
  }},
  "budget_optimization": {{
    "break_even_cpc": number,
    "safe_test_budget": number,
    "budget_phases": ["...", "...", "..."],
    "risk_level": "Low/Medium/High",
    "worst_case_loss": number,
    "scaling_rule": "...",
    "scaling_risk": "...",
    "budget_tip": "..."
  }},
  "neuro_response": {{
    "dopamine": 0-100,
    "fear": 0-100,
    "curiosity": 0-100,
    "urgency": 0-100,
    "trust": 0-100,
    "primary_driver": "Which neuro trigger is strongest for {country} market",
    "emotional_triggers": ["Trigger 1 specific to {country} psychology", "Trigger 2", "Trigger 3"],
    "psychological_gaps": ["Missing behavioral element 1", "Missing element 2"]
  }},
  "ad_variants": [
    {{
      "id": 1,
      "angle": "Name of approach specific to {country} psychology",
      "hook": "15-30 word scroll-stopper using {currency} and local behavioral insights",
      "body": "100-200 words. Address {country}-specific trust issues (generic, no brand names). Use local context and pain points.",
      "cta": "5-10 words with local behavioral insight",
      "predicted_score": 0-100,
      "why_it_works": "Psychological explanation for {country} audience"
    }},
    {{"id": 2, "angle": "...", "hook": "...", "body": "100-200 words...", "cta": "...", "predicted_score": 0-100, "why_it_works": "..."}},
    {{"id": 3, "angle": "...", "hook": "...", "body": "100-200 words...", "cta": "...", "predicted_score": 0-100, "why_it_works": "..."}},
    {{"id": 4, "angle": "...", "hook": "...", "body": "100-200 words...", "cta": "...", "predicted_score": 0-100, "why_it_works": "..."}},
    {{"id": 5, "angle": "...", "hook": "...", "body": "100-200 words...", "cta": "...", "predicted_score": 0-100, "why_it_works": "..."}}
  ],
  "improved_ad": {{
    "final_hook": "Optimized 15-30 words for {country}",
    "final_body": "200+ words addressing {country}-specific trust issues. Use general terms like 'officially registered' (not specific codes), 'local support' (not specific platforms). Paragraph breaks. NO SPECIFIC BRAND NAMES.",
    "final_cta": "Optimized for {country} market behavior",
    "video_script_ready": "Full script with visual directions and audio cues. Generic terms only.",
    "key_changes_made": [
      "Added {country} trust signals (generic credibility markers)",
      "Changed currency to {currency}",
      "Addressed local objection: [behavioral, not brand-specific]",
      "Used local neuro trigger: [psychological pattern]"
    ]
  }},
  "winner_prediction": {{"winner_id": number, "angle": "...", "confidence": "...", "reasoning": "..."}},
  "objection_detection": {{
    "scam_triggers": [{{"trigger": "{country}-specific behavioral red flag (generic)", "severity": "High/Medium/Low"}}],
    "trust_gaps": [{{"gap": "Missing trust element for {country} (generalized)", "severity": "..."}}],
    "compliance_risks": [{{"risk": "...", "platform": "..."}}]
  }},
  "creative_fatigue": {{
    "fatigue_level": "Low/Medium/High",
    "estimated_decline_days": number,
    "explanation": "...",
    "refresh_needed": true/false,
    "refresh_recommendations": ["...", "...", "..."]
  }},
  "cross_platform": {{
    "facebook": {{"score": 0-100, "adapted_copy": "For {country} Facebook users...", "changes_needed": "..."}},
    "tiktok": {{"score": 0-100, "adapted_copy": "For {country} TikTok users...", "changes_needed": "..."}},
    "youtube": {{"score": 0-100, "adapted_copy": "For {country} YouTube users...", "changes_needed": "..."}}
  }},
  "video_execution_analysis": {{
    "hook_delivery": "Analysis for {country} attention spans (60+ words)",
    "speech_flow": "Pacing for {country} audience (40+ words)",
    "visual_dependency": "Visual cues that build trust in {country} (40+ words)",
    "delivery_risk": "Execution challenges in {country} context (40+ words)",
    "format_recommendation": "talking_head/UGC/screen_recording/mixed adapted for {country}",
    "competitor_advantage": "How to beat {country} competitors (50+ words)",
    "timecode_breakdown": [
      {{"segment": "HOOK 0-3s", "content": "{country}-specific psychological opening", "effectiveness": 0-100}},
      {{"segment": "BODY 3-15s", "content": "Trust building for {country}", "effectiveness": 0-100}},
      {{"segment": "CTA 15-30s", "content": "Local payment CTA", "effectiveness": 0-100}}
    ]
  }},
  "persona_reactions": [
    {{"name": "Typical {country} User 1", "demographic": "{country}-specific demographic", "reaction": "...", "pain_points": ["{country} pain 1", "{country} pain 2"], "objections": ["{country} objection (generic)"], "conversion_likelihood": "..."}}
  ],
  "line_by_line_analysis": [
    {{"line_number": 1, "text": "...", "strength": 0-10, "assessment": "...", "issue": "...", "suggestion": "..."}}
  ],
  "phase_breakdown": {{
    "hook_phase": "...",
    "body_phase": "...",
    "cta_phase": "..."
  }},
  "roi_comparison": {{
    "your_projection": "X.Xx",
    "industry_average": "X.Xx",
    "top_performer": "X.Xx",
    "gap_analysis": "Detailed for {country} market (100+ words)"
  }},
  "competitor_advantage": {{
    "unique_angles": ["Angle 1 for {country}", "Angle 2", "Angle 3"],
    "defensible_moat": "Hard to copy in {country} because... (80+ words)",
    "vulnerability": "Risk in {country} market... (60+ words)"
  }}
}}

CRITICAL: 
- All copy must feel native to {country}
- Use {currency} exclusively
- Address local trust barriers using GENERAL terms ("officially registered", "local support", "mobile payment")
- NO specific brand names (banks, telecoms, apps)
- NO specific regulatory codes
- Focus on BEHAVIORAL PSYCHOLOGY and cultural patterns
"""
        return prompt_text

    def _verify_analysis(self, analysis: Dict, ad_copy: str, video_script: str, country_profile: Dict) -> None:
        """Verify analysis includes country-specific elements"""
        scores = analysis.get("scores", {})
        content = (ad_copy + video_script).strip()
        content_len = len(content)
        currency = country_profile['currency']

        if content_len < 10 and scores.get("overall", 100) > 30:
            raise ValueError(f"Empty content got high score: {scores.get('overall')}")

        real_words = len([w for w in content.split() if len(w) > 2 and w.isalpha()])
        if real_words < 2 and content_len > 5:
            if scores.get("clarity", 100) > 30:
                raise ValueError("Gibberish got good clarity score")

        if content_len < 50 and scores.get("overall", 100) > 50:
            raise ValueError(f"Short content got high score: {scores.get('overall')}")

        improved = analysis.get("improved_ad", {})
        if not improved.get("final_hook") or not improved.get("final_body"):
            raise ValueError("Missing improved_ad production fields")

        body_words = len(improved.get("final_body", "").split())
        if body_words < 50:
            raise ValueError(f"improved_ad.body too short: {body_words} words")

        variants = analysis.get("ad_variants", [])
        if len(variants) < 5:
            raise ValueError(f"Expected 5 variants, got {len(variants)}")

        for i, variant in enumerate(variants):
            var_body_words = len(variant.get("body", "").split())
            if var_body_words < 30:
                raise ValueError(f"Variant {i+1} body too short: {var_body_words} words")

        improved_body = improved.get("final_body", "").lower()
        if currency != "$" and currency.lower() not in improved_body and country_profile['currency_name'].lower() not in improved_body:
            logger.warning(f"Currency {currency} not found in improved_ad body")

        logger.info(f"✅ Verified: {country_profile.get('currency_name', 'Unknown')} market, {len(variants)} variants, {body_words} words")


_engine_instance = None

def get_ai_engine():
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AIEngineV5()
    return _engine_instance


class AIValidationError(Exception):
    pass
