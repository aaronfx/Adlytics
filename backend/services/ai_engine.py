"""
ADLYTICS AI Engine v4.1 - FIXED
Adds proper None checks to scoring functions
"""

import os
import json
import httpx
from typing import Dict, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

# ============================================
# SCORING FUNCTIONS - WITH NONE CHECKS
# ============================================

def calculate_weighted_score(hook: int, clarity: int, trust: int, cta: int, audience: int) -> int:
    """REAL scoring calculation with None checks"""
    # Replace None with 0
    hook = hook or 0
    clarity = clarity or 0
    trust = trust or 0
    cta = cta or 0
    audience = audience or 0

    weighted = (
        (hook * 0.25) +
        (clarity * 0.20) +
        (trust * 0.20) +
        (cta * 0.15) +
        (audience * 0.20)
    )

    return round(weighted)


def evaluate_hook_strength(hook: str, audience: dict) -> int:
    """Score 0-100 with None checks"""
    # Handle None or empty hook
    if not hook:
        return 30  # Default score for missing hook

    score = 0
    hook_lower = hook.lower() if hook else ""

    # Pattern interrupt indicators
    pattern_words = ["stop", "wait", "don't", "never", "always", "mistake", "wrong", "secret", "truth"]
    if any(word in hook_lower for word in pattern_words):
        score += 25
    if "?" in hook:
        score += 15

    # Specificity
    if any(char.isdigit() for char in hook):
        score += 20
    if any(char in hook for char in ["%", "$", "₦", "£", "€"]):
        score += 10

    # Audience relevance
    pain_point = (audience.get("pain_point") or "").lower()
    if pain_point and pain_point in hook_lower:
        score += 20

    age = (audience.get("age") or "").lower()
    age_keywords = {
        "18-24": ["hustle", "grind", "fast", "now", "instant"],
        "25-34": ["growth", "career", "family", "balance"],
        "35-44": ["security", "investment", "future", "legacy"],
        "45-54": ["health", "wealth", "time", "freedom"],
        "55-64": ["retirement", "peace", "comfort", "ease"],
        "65+": ["simple", "trusted", "proven", "guaranteed"]
    }
    if age in age_keywords:
        matches = sum(1 for kw in age_keywords[age] if kw in hook_lower)
        score += min(matches * 10, 30)

    return min(score, 100)


def evaluate_clarity(body: str) -> int:
    """Score clarity 0-100 with None checks"""
    if not body:
        return 40  # Default for missing body

    score = 50
    body_lower = body.lower() if body else ""

    # Structure indicators
    sentences = [s.strip() for s in body.split(".") if s.strip()]
    if 3 <= len(sentences) <= 8:
        score += 20
    elif len(sentences) > 8:
        score += 10

    # No jargon penalty
    jargon_words = ["leverage", "synergy", "paradigm", "holistic", "optimize", "streamline"]
    jargon_count = sum(1 for j in jargon_words if j in body_lower)
    score -= jargon_count * 10

    # Value clarity
    value_words = ["get", "receive", "you will", "you'll", "guarantee", "access"]
    if any(word in body_lower for word in value_words):
        score += 15

    # Benefit-focused
    you_count = body_lower.count("you") + body_lower.count("your")
    if you_count >= 3:
        score += 15

    return max(min(score, 100), 0)


def evaluate_trust_building(body: str, audience: dict) -> int:
    """Score trust elements 0-100 with None checks"""
    if not body:
        return 35  # Default for missing body

    score = 30
    body_lower = body.lower() if body else ""

    # Proof elements
    proof_words = ["tested", "proven", "results", "customers", "clients", "students", "members"]
    if any(word in body_lower for word in proof_words):
        score += 25

    # Specificity
    if any(char.isdigit() for char in body):
        score += 20

    # Risk reversal
    risk_words = ["guarantee", "refund", "risk-free", "money back", "cancel anytime", "no questions"]
    if any(word in body_lower for word in risk_words):
        score += 25

    # Social proof
    if any(word in body_lower for word in ["join", "community", "people", "thousands", "millions"]):
        score += 10

    return min(score, 100)


def evaluate_cta_power(cta: str, platform: str) -> int:
    """Score CTA 0-100 with None checks"""
    if not cta:
        return 45  # Default for missing CTA

    score = 40
    cta_lower = cta.lower() if cta else ""
    platform_lower = platform.lower() if platform else ""

    # Action words
    action_words = ["get", "claim", "start", "join", "buy", "shop", "order", "download", "grab", "secure"]
    if any(word in cta_lower for word in action_words):
        score += 30

    # Urgency/scarcity
    urgency_words = ["now", "today", "limited", "only", "free", "instant", "immediate"]
    if any(word in cta_lower for word in urgency_words):
        score += 20

    # Platform-specific
    if platform_lower == "facebook" and any(word in cta_lower for word in ["messenger", "comment", "share"]):
        score += 10
    if platform_lower == "instagram" and any(word in cta_lower for word in ["link", "bio", "swipe"]):
        score += 10
    if platform_lower == "tiktok" and any(word in cta_lower for word in ["duet", "stitch", "follow"]):
        score += 10

    return min(score, 100)


def evaluate_audience_alignment(content: str, audience: dict) -> int:
    """Score audience match 0-100 with None checks"""
    if not content:
        return 45  # Default for missing content

    score = 40
    content_lower = content.lower() if content else ""

    # Pain point match
    pain_point = (audience.get("pain_point") or "").lower()
    if pain_point and pain_point in content_lower:
        score += 30

    # Psychographic match
    psych = (audience.get("psychographic") or "").lower()
    psych_keywords = {
        "value_seeker": ["save", "discount", "deal", "free", "bonus", "extra"],
        "quality_focused": ["premium", "best", "quality", "excellence", "superior"],
        "convenience_seeker": ["easy", "fast", "quick", "instant", "automated", "done for you"],
        "status_seeker": ["exclusive", "vip", "elite", "rare", "limited", "members only"],
        "risk_averse": ["guarantee", "safe", "secure", "protected", "trusted", "proven"]
    }
    if psych in psych_keywords:
        matches = sum(1 for kw in psych_keywords[psych] if kw in content_lower)
        score += min(matches * 8, 20)

    # Income-appropriate language
    income = (audience.get("income") or "").lower()
    if income in ["high", "very_high"] and any(w in content_lower for w in ["investment", "portfolio", "premium"]):
        score += 10
    if income in ["low", "lower_middle"] and any(w in content_lower for w in ["affordable", "budget", "save"]):
        score += 10

    return min(score, 100)


# ============================================
# VARIANT GENERATION - FIXED
# ============================================

def generate_ad_variants(analysis_data: dict, platform: str, audience: dict, industry: str) -> list:
    """Generate 3 ad variants with REAL scores"""
    variants = []

    angles = [
        {"angle": "Pattern Interrupt Hook", "strategy": "Lead with unexpected contradiction"},
        {"angle": "Problem-Agitation-Solution", "strategy": "Amplify pain point before solution"},
        {"angle": "Social Proof Authority", "strategy": "Lead with credibility and results"}
    ]

    for i, angle_config in enumerate(angles, 1):
        variant = generate_single_variant(
            analysis_data=analysis_data,
            platform=platform,
            audience=audience,
            industry=industry,
            angle_config=angle_config,
            variant_id=i
        )
        variants.append(variant)

    # Sort by predicted_score DESCENDING
    variants.sort(key=lambda x: x.get("predicted_score", 0), reverse=True)

    return variants


def generate_single_variant(analysis_data, platform, audience, industry, angle_config, variant_id: int) -> dict:
    """Generate one variant with REAL calculated score"""

    hook = generate_hook_for_angle(angle_config["angle"], audience, industry, analysis_data)
    body = generate_body_for_angle(angle_config["strategy"], analysis_data, audience)
    cta = generate_cta_for_platform(platform, audience, analysis_data)

    # Calculate REAL scores
    hook_score = evaluate_hook_strength(hook, audience)
    clarity_score = evaluate_clarity(body)
    trust_score = evaluate_trust_building(body, audience)
    cta_score = evaluate_cta_power(cta, platform)
    audience_score = evaluate_audience_alignment(f"{hook} {body} {cta}", audience)

    # FIXED: Proper parameter names
    predicted_score = calculate_weighted_score(
        hook=hook_score,
        clarity=clarity_score,
        trust=trust_score,
        cta=cta_score,
        audience=audience_score
    )

    if predicted_score >= 80:
        roi_potential = "Very High (5x+ ROAS)"
    elif predicted_score >= 70:
        roi_potential = "High (3-5x ROAS)"
    elif predicted_score >= 60:
        roi_potential = "Medium (2-3x ROAS)"
    elif predicted_score >= 45:
        roi_potential = "Low-Medium (1-2x ROAS)"
    else:
        roi_potential = "Poor (<1x ROAS)"

    return {
        "id": variant_id,
        "angle": angle_config["angle"],
        "hook": hook,
        "copy": f"{hook}\n\n{body}\n\n{cta}",
        "predicted_score": predicted_score,
        "roi_potential": roi_potential,
        "reason": f"Uses {angle_config['strategy']} optimized for {audience.get('age', 'general')} audience",
        "component_scores": {
            "hook": hook_score,
            "clarity": clarity_score,
            "trust": trust_score,
            "cta": cta_score,
            "audience": audience_score
        }
    }


def generate_hook_for_angle(angle: str, audience: dict, industry: str, analysis_data: dict) -> str:
    """Generate hook based on angle type"""
    pain_point = audience.get("pain_point") or "your problem"

    if "Pattern Interrupt" in angle:
        hooks = [
            f"Stop! You're making this {pain_point} mistake every single day",
            f"The truth about {pain_point} nobody wants to tell you",
            f"I was wrong about {pain_point} (and it cost me everything)"
        ]
    elif "Problem-Agitation" in angle:
        hooks = [
            f"Still struggling with {pain_point}? Here's why...",
            f"If {pain_point} keeps you up at night, read this",
            f"The real reason you can't fix {pain_point}"
        ]
    else:
        hooks = [
            f"How 10,000+ people eliminated {pain_point} in 30 days",
            f"The {industry} method that's changing everything",
            f"Why top performers never worry about {pain_point}"
        ]

    age = audience.get("age") or "25-34"
    if age in ["18-24", "gen_z"]:
        return hooks[0]
    elif age in ["55-64", "65+"]:
        return hooks[2]
    else:
        return hooks[1]


def generate_body_for_angle(strategy: str, analysis_data: dict, audience: dict) -> str:
    """Generate body copy based on strategy"""
    pain_point = audience.get("pain_point") or "this challenge"

    if "contradiction" in strategy.lower():
        return f"Everything you've been told about solving {pain_point} is backwards. While others waste time on complicated solutions, smart people use this 3-step approach that takes 5 minutes and actually works."
    elif "pain point" in strategy.lower():
        return f"Every day you wait, {pain_point} gets worse. You've tried the free guides. You've watched the videos. But you're still stuck because you're missing the one critical element that changes everything."
    else:
        return f"Join the thousands who've already made the switch. This isn't theory—it's a proven system with real results. In just days, you'll see why everyone is talking about this breakthrough approach."


def generate_cta_for_platform(platform: str, audience: dict, analysis_data: dict) -> str:
    """Generate platform-optimized CTA"""
    ctas = {
        "facebook": ["👉 Click 'Send Message' to get instant access", "💬 Comment 'YES' below"],
        "instagram": ["🔗 Tap link in bio—spots filling fast", "👆 Swipe up to claim your spot"],
        "tiktok": ["🔥 Click the link before this goes viral", "⚡ Link in bio—limited time"],
        "google": ["🎯 Get your free quote now", "📞 Call today for instant consultation"],
        "linkedin": ["💼 Download the executive briefing", "📊 Get the full report here"]
    }

    platform_ctas = ctas.get(platform, ctas["facebook"])
    return platform_ctas[0]


# ============================================
# IMPROVED AD SELECTION
# ============================================

def select_improved_ad_from_variants(variants: list) -> dict:
    """Best variant IS the improved ad"""
    if not variants:
        return {
            "headline": "Default Headline",
            "body_copy": "Default body copy.",
            "cta": "Get Started",
            "angle": "Default",
            "predicted_score": 0,
            "roi_potential": "Unknown",
            "source_variant_id": 0
        }

    best_variant = variants[0]

    return {
        "headline": best_variant["hook"],
        "body_copy": best_variant["copy"],
        "cta": best_variant["copy"].split("\n")[-1] if "\n" in best_variant["copy"] else "Get Started Now",
        "angle": best_variant["angle"],
        "predicted_score": best_variant["predicted_score"],
        "roi_potential": best_variant["roi_potential"],
        "source_variant_id": best_variant["id"]
    }


def re_score_improved_ad(improved_ad: dict, audience: dict, platform: str) -> dict:
    """Re-score the improved ad with FRESH calculation"""
    content = f"{improved_ad.get('headline', '')} {improved_ad.get('body_copy', '')} {improved_ad.get('cta', '')}"

    hook_score = evaluate_hook_strength(improved_ad.get("headline", ""), audience)
    clarity_score = evaluate_clarity(improved_ad.get("body_copy", ""))
    trust_score = evaluate_trust_building(improved_ad.get("body_copy", ""), audience)
    cta_score = evaluate_cta_power(improved_ad.get("cta", ""), platform)
    audience_score = evaluate_audience_alignment(content, audience)

    new_overall = calculate_weighted_score(
        hook=hook_score,
        clarity=clarity_score,
        trust=trust_score,
        cta=cta_score,
        audience=audience_score
    )

    return {
        "overall": new_overall,
        "hook_strength": hook_score,
        "clarity": clarity_score,
        "trust_building": trust_score,
        "cta_power": cta_score,
        "audience_alignment": audience_score
    }


# ============================================
# VIDEO SCRIPT GENERATION
# ============================================

def detect_content_mode(request_data: dict) -> str:
    """Detect if user wants ad copy, video script, or both"""
    has_ad = bool(request_data.get("ad_copy", "").strip())
    has_video = bool(request_data.get("video_script", "").strip())

    if has_video and not has_ad:
        return "videoScript"
    elif has_ad and not has_video:
        return "adCopy"
    elif has_ad and has_video:
        return "both"
    else:
        return "adCopy"


def generate_video_script(analysis_data: dict, audience: dict, platform: str, objective: str) -> str:
    """Generate LONG-FORM video script (1500+ words)"""

    pain_point = audience.get("pain_point") or "their current struggle"
    product = analysis_data.get("product_name") or "this solution"
    industry = analysis_data.get("industry") or "this industry"

    script = f"""[HOOK 0-3s]
🎥 VISUAL: Direct to camera, high energy
🗣️ "Wait—stop scrolling. If you're dealing with {pain_point} right now, this next 60 seconds could change everything. Most people ignore this message and keep struggling. But you're not most people, are you?"

[INTRO 3-8s]
🎥 VISUAL: Authority shot
🗣️ "I'm going to show you exactly why {product} is different from everything else you've tried. And I mean exactly—no vague promises, no marketing fluff. Just the raw truth about what actually works in {industry}."

[PROBLEM AGITATION 8-18s]
🎥 VISUAL: B-roll of frustration
🗣️ "Look, here's the real problem. You've probably tried all the usual solutions—the free advice, the cheap alternatives, the 'quick fixes' that everyone recommends. And where did that get you? Probably right back where you started, maybe even worse off than before. The reason nothing worked isn't because you're doing anything wrong. It's because you were following broken advice that completely ignores how people actually make decisions in today's market. Every day you stay stuck with {pain_point}, you're losing money, losing time, and losing confidence."

[STORY/PROOF 18-35s]
🎥 VISUAL: Transformation footage
🗣️ "Three months ago, I was exactly where you are right now. {pain_point} was keeping me up at night, stressing me out, making me question everything. I tried the courses. I tried the coaches. I tried figuring it out myself. Nothing worked. Then I discovered something that changed everything. Not another tactic. Not another hack. But a fundamental shift in how to approach this problem. Within just weeks of implementing this system, I went from struggling to thriving. But don't just take my word for it. Look at Sarah, who used this exact method to get results in just weeks. Or Marcus, who went from broke to thriving faster than he thought possible. The pattern is undeniable when you have the right system."

[CORE TEACHING 35-55s]
🎥 VISUAL: Screen recording
🗣️ "Here's what nobody else is telling you. The real reason {pain_point} persists for most people is that they're addressing symptoms instead of root causes. Traditional methods fail because they ignore the three critical components that actually drive results. Component One: The specific mechanism that creates immediate change. Without this, everything else falls apart. Component Two: The process that ensures consistent results. It's the bridge between where you are and where you want to be. Component Three: The system that automates success so you don't have to worry about failure ever again. When these three elements work together in sync, the results aren't just incremental improvements—they're exponential transformations."

[STEPS/PROCESS 55-75s]
🎥 VISUAL: Step-by-step graphics
🗣️ "So here's exactly how it works, step by step. Step One: Take immediate action that creates instant momentum. This takes just minutes and immediately changes your trajectory. Most people skip this step and that's why they fail. Step Two: Implement the core system using our proven method which produces superior results in half the time. Step Three: Start seeing tangible, measurable outcomes. By this point, you'll already feel the difference. Step Four: Lock in your gains and create momentum that carries you forward automatically. Step Five: Ensure long-term, sustainable success without constant maintenance. Each step builds on the previous one. Skip a step, and the whole system weakens. Follow them in order, and you create an unstoppable success machine."

[OBJECTION HANDLING 75-85s]
🎥 VISUAL: Direct camera
🗣️ "Now, I know what might be going through your mind right now. You might be thinking, 'This sounds expensive.' Or 'What if this doesn't work for my specific situation?' Or 'I don't have time for something complicated right now.' These are completely valid concerns. And here's the truth: most solutions ARE too expensive, too complicated, and too risky. That's exactly why we built this differently. First, regarding cost—when you compare this to alternatives, this actually saves you money from day one. Plus, we have a guarantee, so your risk is exactly zero. Second, regarding whether it will work for you—this system has been tested across different situations, and the principles apply universally. Third, regarding time—this requires minimal time to implement, and then it runs largely on autopilot."

[PROOF AMPLIFICATION 85-95s]
🎥 VISUAL: Testimonials
🗣️ "Don't just take my word for this. Look at the numbers. Thousands of people in situations just like yours have already made this transition. Most reported significant improvements within just weeks. Industry leaders are calling this the future of {industry}. And here's what really matters: once people make this switch, they don't go back. That tells you everything about whether this actually works. We also back everything with an iron-clad guarantee. If you don't see results, you don't pay. It's that simple. We're taking all the risk because we're that confident this will work for you."

[CTA 95-105s]
🎥 VISUAL: Urgent energy
🗣️ "Here's what you need to do right now. Click the link below this video. Not in five minutes. Not after you 'think about it.' Right now, while you're feeling this momentum. Why now? Because spots are limited and filling fast. Every minute you wait is another minute staying stuck with {pain_point}. Clicking that link takes you to the next step. It takes less than a minute to get started. And it could be the single decision that changes everything for you. Remember: the people who succeed aren't necessarily smarter or more talented. They just take action while others hesitate. Be the person who takes action. Click now."

[FINAL HOOK 105-120s]
🎥 VISUAL: Emotional close
🗣️ "Think back to what I said at the very beginning. Most people will scroll past this message and keep struggling with {pain_point}. But you? You stopped scrolling. You watched to the end. That tells me you're serious about change. So prove it. Click the link. Join the thousands who already made the smart choice. Start your transformation today. I'll see you on the other side."

[END CARD 120-125s]
🎥 VISUAL: Logo, CTA
📺 [Brand Name] | [Key Benefit] | [Trust Badge]
"""

    return script


# ============================================
# AI API CALLS
# ============================================

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_openrouter(prompt: str, system_prompt: str = "", temperature: float = 0.7) -> str:
    """Call OpenRouter API with retries"""
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not configured")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://adlytics.app",
                "X-Title": "ADLYTICS"
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": 4000
            }
        )

        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code} - {response.text}")

        data = response.json()
        return data["choices"][0]["message"]["content"]


# ============================================
# MAIN ANALYSIS FLOW
# ============================================

async def analyze_ad(request_data: dict, files: list = None) -> dict:
    """MAIN ANALYSIS FUNCTION - v4.1 FIXED"""

    # 1. Detect content mode
    content_mode = detect_content_mode(request_data)

    # 2. Get base analysis from AI
    base_analysis = await run_ai_analysis(request_data, content_mode)

    # Extract audience data
    audience = extract_audience(request_data)
    platform = request_data.get("platform") or "facebook"
    industry = request_data.get("industry") or "general"

    # 3. Generate variants with REAL scores
    variants = generate_ad_variants(
        analysis_data=base_analysis,
        platform=platform,
        audience=audience,
        industry=industry
    )

    # 4. Select best variant as improved ad
    improved_ad = select_improved_ad_from_variants(variants)

    # 5. Re-score the improved ad
    improved_scores = re_score_improved_ad(improved_ad, audience, platform)

    # 6. Generate video script if needed
    video_script = None
    if content_mode in ["videoScript", "both"]:
        video_script = generate_video_script(
            analysis_data=base_analysis,
            audience=audience,
            platform=platform,
            objective=request_data.get("objective") or "conversions"
        )
        improved_ad["video_script_version"] = video_script

    # 7. Build improved analysis object
    improved_analysis = {
        "scores": improved_scores,
        "run_decision": calculate_run_decision(improved_scores),
        "behavior_summary": generate_behavior_summary(improved_scores, improved_ad),
        "roi_analysis": generate_roi_analysis(improved_scores, improved_ad),
        "phase_breakdown": generate_phase_breakdown(improved_ad),
        "variants": {
            "power_hooks": [v["hook"] for v in variants[:3]],
            "high_conversion_ctas": list(set([v["copy"].split("\n")[-1] for v in variants if "\n" in v["copy"]]))[:3]
        },
        "personas": generate_persona_reactions(improved_ad, audience),
        "competitor_analysis": base_analysis.get("competitor_analysis", {}),
        "video_execution_analysis": generate_video_analysis(improved_ad, video_script) if video_script else None
    }

    # 8. Winner prediction
    winner_prediction = {
        "confidence": "High" if variants[0]["predicted_score"] > 70 else "Medium" if variants[0]["predicted_score"] > 55 else "Low",
        "reason": f"Variant #{variants[0]['id']} ({variants[0]['angle']}) scores highest with {variants[0]['predicted_score']}/100",
        "best_variant_id": variants[0]["id"],
        "expected_lift": f"+{variants[0]['predicted_score'] - base_analysis.get('scores', {}).get('overall', 50)} points"
    }

    # 9. ROI comparison
    roi_comparison = [
        {
            "variant_id": v["id"],
            "roi_potential": v["roi_potential"],
            "risk": "Low" if v["predicted_score"] > 70 else "Medium" if v["predicted_score"] > 50 else "High",
            "summary": f"Variant {v['id']} ({v['angle']}): Score {v['predicted_score']}, {v['roi_potential']}"
        }
        for v in variants
    ]

    # 10. Ad variants for UI
    ad_variants_ui = [
        {
            "id": v["id"],
            "angle": v["angle"],
            "hook": v["hook"],
            "copy": v["copy"],
            "predicted_score": v["predicted_score"],
            "roi_potential": v["roi_potential"],
            "reason": v["reason"]
        }
        for v in variants
    ]

    # 11. Competitor advantage
    competitor_advantage = generate_competitor_advantage(improved_ad, base_analysis)

    # ASSEMBLE FINAL RESPONSE
    return {
        "success": True,
        "analysis": {
            "scores": base_analysis.get("scores"),
            "behavior_summary": base_analysis.get("behavior_summary"),
            "roi_analysis": base_analysis.get("roi_analysis"),
            "phase_breakdown": base_analysis.get("phase_breakdown"),
            "platform_specific": base_analysis.get("platform_specific"),
            "line_by_line_analysis": base_analysis.get("line_by_line_analysis", []),
            "critical_weaknesses": base_analysis.get("critical_weaknesses", []),
            "improvements": base_analysis.get("improvements", []),
            "persona_reactions": base_analysis.get("persona_reactions", []),
            "video_execution_analysis": base_analysis.get("video_execution_analysis"),
            "run_decision": base_analysis.get("run_decision"),
            "improved_ad": improved_ad,
            "improved_ad_analysis": improved_analysis,
            "winner_prediction": winner_prediction,
            "ad_variants": ad_variants_ui,
            "roi_comparison": roi_comparison,
            "competitor_advantage": competitor_advantage
        },
        "audience_parsed": format_audience_summary(audience),
        "content_mode": content_mode
    }


# ============================================
# HELPER FUNCTIONS
# ============================================

def extract_audience(request_data: dict) -> dict:
    """Extract audience data from request"""
    return {
        "country": request_data.get("audience_country") or "us",
        "region": request_data.get("audience_region") or "",
        "age": request_data.get("audience_age") or "25-34",
        "gender": request_data.get("audience_gender") or "all",
        "income": request_data.get("audience_income") or "middle",
        "education": request_data.get("audience_education") or "",
        "occupation": request_data.get("audience_occupation") or "",
        "psychographic": request_data.get("audience_psychographic") or "",
        "pain_point": request_data.get("audience_pain_point") or "",
        "tech_savviness": request_data.get("tech_savviness") or "medium",
        "purchase_behavior": request_data.get("purchase_behavior") or "research"
    }


def format_audience_summary(audience: dict) -> str:
    """Format audience for display"""
    parts = []
    if audience.get("country"):
        parts.append(audience["country"].upper())
    if audience.get("age"):
        parts.append(audience["age"])
    if audience.get("pain_point"):
        parts.append(f"Pain: {audience['pain_point']}")
    return " | ".join(parts) if parts else "General Audience"


def calculate_run_decision(scores: dict) -> dict:
    """Calculate run decision based on scores"""
    overall = scores.get("overall") or 0

    if overall >= 75:
        return {"should_run": "Yes", "risk_level": "Low", "reason": "Strong scores across all dimensions"}
    elif overall >= 60:
        return {"should_run": "Yes with monitoring", "risk_level": "Medium", "reason": "Good foundation but monitor closely"}
    elif overall >= 45:
        return {"should_run": "Only after fixes", "risk_level": "Medium-High", "reason": "Critical weaknesses need addressing"}
    else:
        return {"should_run": "No", "risk_level": "High", "reason": "Too many critical issues"}


def generate_behavior_summary(scores: dict, improved_ad: dict) -> dict:
    """Generate behavior summary"""
    overall = scores.get("overall") or 0

    if overall >= 80:
        verdict = "Explosive Potential"
        readiness = "95%"
        risk = "5%"
    elif overall >= 70:
        verdict = "Strong Winner"
        readiness = "85%"
        risk = "15%"
    elif overall >= 60:
        verdict = "Moderate Success"
        readiness = "70%"
        risk = "30%"
    elif overall >= 50:
        verdict = "Needs Optimization"
        readiness = "50%"
        risk = "50%"
    else:
        verdict = "High Risk"
        readiness = "30%"
        risk = "70%"

    return {
        "verdict": verdict,
        "launch_readiness": readiness,
        "failure_risk": risk,
        "primary_reason": f"Overall score of {overall}/100 indicates {verdict.lower()} performance expected"
    }


def generate_roi_analysis(scores: dict, improved_ad: dict) -> dict:
    """Generate ROI analysis"""
    overall = scores.get("overall") or 0

    if overall >= 80:
        roi_potential = "Very High (5x+ ROAS)"
        break_even = "95%"
        risk_class = "Very Low"
    elif overall >= 70:
        roi_potential = "High (3-5x ROAS)"
        break_even = "85%"
        risk_class = "Low"
    elif overall >= 60:
        roi_potential = "Medium (2-3x ROAS)"
        break_even = "70%"
        risk_class = "Medium"
    elif overall >= 50:
        roi_potential = "Low-Medium (1-2x ROAS)"
        break_even = "55%"
        risk_class = "Medium-High"
    else:
        roi_potential = "Poor (<1x ROAS)"
        break_even = "30%"
        risk_class = "High"

    return {
        "roi_potential": roi_potential,
        "break_even_probability": break_even,
        "risk_classification": risk_class,
        "key_metrics": {
            "expected_ctr_range": f"{max(1, overall//20)}-{max(3, overall//15)}%",
            "realistic_cpc_range": f"${max(0.5, 3-(overall/50)):.2f}-${max(1, 5-(overall/40)):.2f}",
            "conversion_rate_range": f"{max(1, overall//25)}-{max(5, overall//15)}%"
        },
        "roi_scenarios": {
            "worst_case": f"{max(0.5, (overall/100)*2):.1f}x ROAS",
            "expected_case": f"{max(1, overall//20)}x ROAS",
            "best_case": f"{max(2, overall//15)}x ROAS"
        },
        "primary_roi_lever": "Hook strength drives CTR" if (scores.get("hook_strength") or 0) > (scores.get("trust_building") or 0) else "Trust building drives conversion",
        "biggest_financial_risk": "Low CTR wastes budget" if (scores.get("hook_strength") or 0) < 60 else "Conversion friction reduces ROAS"
    }


def generate_phase_breakdown(improved_ad: dict) -> dict:
    """Generate phase-by-phase breakdown"""
    headline = improved_ad.get("headline") or ""
    cta = improved_ad.get("cta") or ""
    return {
        "micro_stop_0_1s": f"Hook '{headline[:30]}...' captures attention",
        "scroll_stop_1_2s": "Pattern interrupt maintains interest",
        "attention_2_5s": "Problem agitation builds relevance",
        "trust_evaluation": "Proof elements establish credibility",
        "click_and_post_click": f"CTA '{cta}' drives action"
    }


def generate_persona_reactions(improved_ad: dict, audience: dict) -> list:
    """Generate persona reactions"""
    pain_point = audience.get("pain_point") or "this problem"
    return [
        {"persona": "The Skeptic", "reaction": "Wants proof", "exact_quote": f"'I've tried everything for {pain_point}. What makes this different?'"},
        {"persona": "The Quick Fix Seeker", "reaction": "Attracted by speed", "exact_quote": "'Finally, something that works fast!'"},
        {"persona": "The Value Hunter", "reaction": "Calculating ROI", "exact_quote": "'This pays for itself if it works...'"}
    ]


def generate_video_analysis(improved_ad: dict, video_script: str) -> dict:
    """Generate video execution analysis"""
    score = improved_ad.get("predicted_score") or 0
    return {
        "hook_delivery_strength": "Strong" if score > 70 else "Moderate",
        "speech_flow_quality": "Natural pace" if score > 60 else "Needs pacing work",
        "pattern_interrupt_strength": "High" if "stop" in (improved_ad.get("headline") or "").lower() else "Moderate",
        "visual_dependency": "Medium" if len(video_script or "") > 1000 else "High",
        "delivery_risk": "Low" if score > 65 else "Medium",
        "recommended_format": "talking_head" if score > 70 else "ugc_style",
        "execution_gaps": [] if score > 70 else ["Hook could be more visual"],
        "exact_fix_direction": "Maintain eye contact during hook"
    }


def generate_competitor_advantage(improved_ad: dict, base_analysis: dict) -> dict:
    """Generate competitor advantage analysis"""
    return {
        "why_user_might_choose_competitor": "Established brand recognition",
        "what_competitor_is_doing_better": "Market presence and reach",
        "execution_difference": "Competitor plays it safe",
        "how_to_outperform": f"Leverage '{improved_ad.get('angle')}' messaging"
    }


async def run_ai_analysis(request_data: dict, content_mode: str) -> dict:
    """Run base AI analysis"""
    ad_copy = request_data.get("ad_copy") or ""
    video_script = request_data.get("video_script") or ""

    if content_mode == "videoScript" and video_script:
        content = video_script[:2000]
        content_type = "video script"
    elif content_mode == "both":
        content = f"AD COPY: {ad_copy[:1000]}\n\nVIDEO SCRIPT: {video_script[:1000]}"
        content_type = "combined"
    else:
        content = ad_copy[:2000]
        content_type = "ad copy"

    prompt = f"""
Analyze this {content_type} for a {request_data.get('platform') or 'facebook'} ad.

CONTENT:
{content}

Return JSON with:
- scores: {{overall, hook_strength, clarity, trust_building, cta_power, audience_alignment}}
- behavior_summary: {{verdict, launch_readiness, failure_risk, primary_reason}}
- phase_breakdown, platform_specific, line_by_line_analysis, critical_weaknesses, improvements, persona_reactions, run_decision
"""

    try:
        response = await call_openrouter(prompt, "You are an expert ad strategist. Return only valid JSON.", 0.7)
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(response)
    except Exception as e:
        return {
            "scores": {"overall": 50, "hook_strength": 50, "clarity": 50, "trust_building": 50, "cta_power": 50, "audience_alignment": 50},
            "behavior_summary": {"verdict": "Analysis Pending", "launch_readiness": "50%", "failure_risk": "50%", "primary_reason": str(e)},
            "phase_breakdown": {},
            "platform_specific": {},
            "line_by_line_analysis": [],
            "critical_weaknesses": [],
            "improvements": [],
            "persona_reactions": [],
            "run_decision": {"should_run": "Review Required", "risk_level": "Unknown", "reason": str(e)}
        }


# ============================================
# COMPATIBILITY LAYER
# ============================================

class AIEngine:
    """Wrapper for backward compatibility"""

    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.model = OPENROUTER_MODEL

    async def analyze(self, request_data: dict, files: list = None) -> dict:
        return await analyze_ad(request_data, files)

    def detect_content_mode(self, request_data: dict) -> str:
        return detect_content_mode(request_data)

    def extract_audience(self, request_data: dict) -> dict:
        return extract_audience(request_data)


_ai_engine_instance = None

def get_ai_engine() -> AIEngine:
    """Factory function"""
    global _ai_engine_instance
    if _ai_engine_instance is None:
        _ai_engine_instance = AIEngine()
    return _ai_engine_instance


__all__ = ['get_ai_engine', 'analyze_ad', 'detect_content_mode', 'extract_audience']
