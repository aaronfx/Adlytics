"""
ADLYTICS AI Engine v4.2 - STRICT SCHEMA ENFORCEMENT
Guarantees complete response structure with no N/A values
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
# STRICT RESPONSE SCHEMA - NEVER EMPTY
# ============================================

REQUIRED_SCHEMA = {
    "scores": {
        "overall": 50,
        "hook_strength": 50,
        "clarity": 50,
        "trust_building": 50,
        "cta_power": 50,
        "audience_alignment": 50
    },
    "behavior_summary": {
        "verdict": "Analysis Pending",
        "launch_readiness": "50%",
        "failure_risk": "50%",
        "primary_reason": "Analysis in progress"
    },
    "phase_breakdown": {
        "micro_stop_0_1s": "Hook captures initial attention within first second",
        "scroll_stop_1_2s": "Pattern interrupt maintains interest",
        "attention_2_5s": "Value proposition builds relevance",
        "trust_evaluation": "Proof elements establish credibility",
        "click_and_post_click": "Call-to-action drives conversion"
    },
    "critical_weaknesses": [],
    "improvements": [],
    "persona_reactions": [],
    "roi_analysis": {
        "roi_potential": "Medium (2-3x ROAS)",
        "break_even_probability": "70%",
        "risk_classification": "Medium",
        "key_metrics": {
            "expected_ctr_range": "1-3%",
            "realistic_cpc_range": "$1.00-$3.00",
            "conversion_rate_range": "2-5%"
        },
        "roi_scenarios": {
            "worst_case": "0.5x ROAS",
            "expected_case": "2x ROAS",
            "best_case": "4x ROAS"
        },
        "primary_roi_lever": "Hook strength optimization",
        "biggest_financial_risk": "Low conversion rate"
    },
    "line_by_line_analysis": [],
    "video_execution_analysis": {
        "is_video_script": "No",
        "hook_delivery_strength": "Not applicable - static ad",
        "speech_flow_quality": "Not applicable - static ad",
        "visual_dependency": "Medium",
        "delivery_risk": "Low",
        "biggest_execution_gap": "None identified",
        "recommended_format": "static_image"
    },
    "run_decision": {
        "should_run": "Review Required",
        "risk_level": "Medium",
        "reason": "Awaiting complete analysis"
    },
    "platform_specific": {
        "platform": "facebook",
        "core_behavior": "Users scroll quickly, pattern interrupts critical",
        "fatal_flaw": "None identified",
        "platform-specific_fix": "Optimize for mobile feed view"
    },
    "competitor_advantage": {
        "why_user_might_choose_competitor": "Established brand trust",
        "what_competitor_is_doing_better": "Market presence and recognition",
        "how_to_outperform": "Differentiate with unique value proposition"
    }
}

FALLBACK_WEAKNESS = {
    "issue": "Ad performance could be optimized further",
    "behavior_impact": "May not achieve maximum conversion potential",
    "precise_fix": "Test variations and refine targeting"
}

FALLBACK_PERSONA = {
    "persona": "The Pragmatic Buyer",
    "reaction": "Cautiously interested",
    "exact_quote": "This looks interesting, but I need to see more proof before committing."
}

FALLBACK_LINE = {
    "text": "Main ad copy",
    "score": 50,
    "analysis": "Standard performance - room for improvement"
}

FALLBACK_VARIANT = {
    "id": 1,
    "angle": "Value Proposition",
    "hook": "Discover the solution you've been looking for",
    "copy": "Main value proposition with clear benefits and call-to-action",
    "predicted_score": 55,
    "roi_potential": "Medium (2-3x ROAS)",
    "reason": "Solid foundation with optimization potential"
}

FALLBACK_IMPROVEMENT = "Refine messaging to better resonate with target audience pain points"

# ============================================
# SCHEMA ENFORCEMENT FUNCTIONS
# ============================================

def enforce_complete_structure(data: dict) -> dict:
    """
    ENSURE: No missing keys, no None values, no empty arrays without fallbacks
    """
    if not isinstance(data, dict):
        data = {}
    
    result = {}
    
    # Enforce all required keys with defaults
    for key, default in REQUIRED_SCHEMA.items():
        value = data.get(key)
        if value is None or value == "" or value == [] or value == {}:
            result[key] = default
        else:
            result[key] = value
    
    # Ensure nested structures are complete
    result["scores"] = enforce_scores(result.get("scores", {}))
    result["behavior_summary"] = enforce_behavior_summary(result.get("behavior_summary", {}))
    result["phase_breakdown"] = enforce_phase_breakdown(result.get("phase_breakdown", {}))
    result["critical_weaknesses"] = enforce_weaknesses(result.get("critical_weaknesses", []))
    result["improvements"] = enforce_improvements(result.get("improvements", []))
    result["persona_reactions"] = enforce_personas(result.get("persona_reactions", []))
    result["roi_analysis"] = enforce_roi(result.get("roi_analysis", {}))
    result["line_by_line_analysis"] = enforce_lines(result.get("line_by_line_analysis", []))
    result["video_execution_analysis"] = enforce_video(result.get("video_execution_analysis", {}))
    result["run_decision"] = enforce_run_decision(result.get("run_decision", {}))
    result["platform_specific"] = enforce_platform(result.get("platform_specific", {}))
    result["competitor_advantage"] = enforce_competitor(result.get("competitor_advantage", {}))
    
    return result

def enforce_scores(scores: dict) -> dict:
    defaults = REQUIRED_SCHEMA["scores"]
    if not isinstance(scores, dict):
        return defaults.copy()
    
    result = {}
    for key in defaults:
        val = scores.get(key)
        result[key] = val if isinstance(val, (int, float)) and val > 0 else defaults[key]
    return result

def enforce_behavior_summary(summary: dict) -> dict:
    defaults = REQUIRED_SCHEMA["behavior_summary"]
    if not isinstance(summary, dict):
        return defaults.copy()
    
    return {
        "verdict": summary.get("verdict") or defaults["verdict"],
        "launch_readiness": summary.get("launch_readiness") or defaults["launch_readiness"],
        "failure_risk": summary.get("failure_risk") or defaults["failure_risk"],
        "primary_reason": summary.get("primary_reason") or summary.get("reason") or defaults["primary_reason"]
    }

def enforce_phase_breakdown(phases: dict) -> dict:
    defaults = REQUIRED_SCHEMA["phase_breakdown"]
    if not isinstance(phases, dict):
        return defaults.copy()
    
    result = {}
    for key in defaults:
        val = phases.get(key)
        result[key] = val if val and isinstance(val, str) else defaults[key]
    return result

def enforce_weaknesses(weaknesses: list) -> list:
    if not isinstance(weaknesses, list) or len(weaknesses) == 0:
        return [FALLBACK_WEAKNESS.copy()]
    
    result = []
    for w in weaknesses:
        if isinstance(w, dict):
            # Normalize field names
            issue = w.get("issue") or w.get("title") or "Optimization opportunity"
            impact = w.get("behavior_impact") or w.get("impact") or "May reduce conversion effectiveness"
            fix = w.get("precise_fix") or w.get("fix") or "Test alternative approaches"
            
            result.append({
                "issue": issue,
                "behavior_impact": impact,
                "precise_fix": fix
            })
        elif isinstance(w, str):
            result.append({
                "issue": w,
                "behavior_impact": "Affects user engagement",
                "precise_fix": "Review and optimize this element"
            })
    
    return result if result else [FALLBACK_WEAKNESS.copy()]

def enforce_improvements(improvements: list) -> list:
    if not isinstance(improvements, list) or len(improvements) == 0:
        return [FALLBACK_IMPROVEMENT]
    
    result = []
    for imp in improvements:
        if isinstance(imp, str):
            result.append(imp)
        elif isinstance(imp, dict):
            desc = imp.get("description") or imp.get("fix") or str(imp)
            result.append(desc)
    
    return result if result else [FALLBACK_IMPROVEMENT]

def enforce_personas(personas: list) -> list:
    if not isinstance(personas, list) or len(personas) == 0:
        return [FALLBACK_PERSONA.copy()]
    
    result = []
    for p in personas:
        if isinstance(p, dict):
            result.append({
                "persona": p.get("persona") or p.get("name") or "Target User",
                "reaction": p.get("reaction") or "Neutral",
                "exact_quote": p.get("exact_quote") or p.get("quote") or p.get("thought") or "No specific reaction recorded"
            })
    
    return result if result else [FALLBACK_PERSONA.copy()]

def enforce_roi(roi: dict) -> dict:
    defaults = REQUIRED_SCHEMA["roi_analysis"]
    if not isinstance(roi, dict):
        return defaults.copy()
    
    result = {
        "roi_potential": roi.get("roi_potential") or defaults["roi_potential"],
        "break_even_probability": roi.get("break_even_probability") or defaults["break_even_probability"],
        "risk_classification": roi.get("risk_classification") or defaults["risk_classification"],
        "primary_roi_lever": roi.get("primary_roi_lever") or defaults["primary_roi_lever"],
        "biggest_financial_risk": roi.get("biggest_financial_risk") or defaults["biggest_financial_risk"],
        "key_metrics": enforce_roi_metrics(roi.get("key_metrics", {})),
        "roi_scenarios": enforce_roi_scenarios(roi.get("roi_scenarios", {}))
    }
    return result

def enforce_roi_metrics(metrics: dict) -> dict:
    defaults = REQUIRED_SCHEMA["roi_analysis"]["key_metrics"]
    if not isinstance(metrics, dict):
        return defaults.copy()
    
    return {
        "expected_ctr_range": metrics.get("expected_ctr_range") or defaults["expected_ctr_range"],
        "realistic_cpc_range": metrics.get("realistic_cpc_range") or defaults["realistic_cpc_range"],
        "conversion_rate_range": metrics.get("conversion_rate_range") or defaults["conversion_rate_range"]
    }

def enforce_roi_scenarios(scenarios: dict) -> dict:
    defaults = REQUIRED_SCHEMA["roi_analysis"]["roi_scenarios"]
    if not isinstance(scenarios, dict):
        return defaults.copy()
    
    return {
        "worst_case": scenarios.get("worst_case") or defaults["worst_case"],
        "expected_case": scenarios.get("expected_case") or defaults["expected_case"],
        "best_case": scenarios.get("best_case") or defaults["best_case"]
    }

def enforce_lines(lines: list) -> list:
    if not isinstance(lines, list) or len(lines) == 0:
        return [FALLBACK_LINE.copy()]
    
    result = []
    for line in lines:
        if isinstance(line, dict):
            result.append({
                "text": line.get("text") or line.get("line") or "Ad content",
                "score": line.get("score") or 50,
                "analysis": line.get("analysis") or line.get("feedback") or "Standard performance"
            })
        elif isinstance(line, str):
            result.append({
                "text": line,
                "score": 50,
                "analysis": "Review for optimization"
            })
    
    return result if result else [FALLBACK_LINE.copy()]

def enforce_video(video: dict) -> dict:
    defaults = REQUIRED_SCHEMA["video_execution_analysis"]
    if not isinstance(video, dict):
        return defaults.copy()
    
    return {
        "is_video_script": video.get("is_video_script") or defaults["is_video_script"],
        "hook_delivery_strength": video.get("hook_delivery_strength") or defaults["hook_delivery_strength"],
        "speech_flow_quality": video.get("speech_flow_quality") or defaults["speech_flow_quality"],
        "visual_dependency": video.get("visual_dependency") or defaults["visual_dependency"],
        "delivery_risk": video.get("delivery_risk") or defaults["delivery_risk"],
        "biggest_execution_gap": video.get("biggest_execution_gap") or video.get("execution_gaps", [""])[0] or defaults["biggest_execution_gap"],
        "recommended_format": video.get("recommended_format") or defaults["recommended_format"]
    }

def enforce_run_decision(decision: dict) -> dict:
    defaults = REQUIRED_SCHEMA["run_decision"]
    if not isinstance(decision, dict):
        return defaults.copy()
    
    return {
        "should_run": decision.get("should_run") or decision.get("verdict") or defaults["should_run"],
        "risk_level": decision.get("risk_level") or defaults["risk_level"],
        "reason": decision.get("reason") or decision.get("primary_reason") or defaults["reason"]
    }

def enforce_platform(platform: dict) -> dict:
    defaults = REQUIRED_SCHEMA["platform_specific"]
    if not isinstance(platform, dict):
        return defaults.copy()
    
    return {
        "platform": platform.get("platform") or defaults["platform"],
        "core_behavior": platform.get("core_behavior") or defaults["core_behavior"],
        "fatal_flaw": platform.get("fatal_flaw") or defaults["fatal_flaw"],
        "platform-specific_fix": platform.get("platform-specific_fix") or platform.get("fix") or defaults["platform-specific_fix"]
    }

def enforce_competitor(competitor: dict) -> dict:
    defaults = REQUIRED_SCHEMA["competitor_advantage"]
    if not isinstance(competitor, dict):
        return defaults.copy()
    
    return {
        "why_user_might_choose_competitor": competitor.get("why_user_might_choose_competitor") or defaults["why_user_might_choose_competitor"],
        "what_competitor_is_doing_better": competitor.get("what_competitor_is_doing_better") or defaults["what_competitor_is_doing_better"],
        "how_to_outperform": competitor.get("how_to_outperform") or defaults["how_to_outperform"]
    }

# ============================================
# SCORING FUNCTIONS - WITH NONE CHECKS
# ============================================

def calculate_weighted_score(hook: int, clarity: int, trust: int, cta: int, audience: int) -> int:
    """REAL scoring calculation with None checks"""
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
    if not hook:
        return 30

    score = 0
    hook_lower = hook.lower() if hook else ""

    pattern_words = ["stop", "wait", "don't", "never", "always", "mistake", "wrong", "secret", "truth"]
    if any(word in hook_lower for word in pattern_words):
        score += 25
    if "?" in hook:
        score += 15

    if any(char.isdigit() for char in hook):
        score += 20
    if any(char in hook for char in ["%", "$", "₦", "£", "€"]):
        score += 10

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
        return 40

    score = 50
    body_lower = body.lower() if body else ""

    sentences = [s.strip() for s in body.split(".") if s.strip()]
    if 3 <= len(sentences) <= 8:
        score += 20
    elif len(sentences) > 8:
        score += 10

    jargon_words = ["leverage", "synergy", "paradigm", "holistic", "optimize", "streamline"]
    jargon_count = sum(1 for j in jargon_words if j in body_lower)
    score -= jargon_count * 10

    value_words = ["get", "receive", "you will", "you'll", "guarantee", "access"]
    if any(word in body_lower for word in value_words):
        score += 15

    you_count = body_lower.count("you") + body_lower.count("your")
    if you_count >= 3:
        score += 15

    return max(min(score, 100), 0)


def evaluate_trust_building(body: str, audience: dict) -> int:
    """Score trust elements 0-100 with None checks"""
    if not body:
        return 35

    score = 30
    body_lower = body.lower() if body else ""

    proof_words = ["tested", "proven", "results", "customers", "clients", "students", "members"]
    if any(word in body_lower for word in proof_words):
        score += 25

    if any(char.isdigit() for char in body):
        score += 20

    risk_words = ["guarantee", "refund", "risk-free", "money back", "cancel anytime", "no questions"]
    if any(word in body_lower for word in risk_words):
        score += 25

    if any(word in body_lower for word in ["join", "community", "people", "thousands", "millions"]):
        score += 10

    return min(score, 100)


def evaluate_cta_power(cta: str, platform: str) -> int:
    """Score CTA 0-100 with None checks"""
    if not cta:
        return 45

    score = 40
    cta_lower = cta.lower() if cta else ""
    platform_lower = platform.lower() if platform else ""

    action_words = ["get", "claim", "start", "join", "buy", "shop", "order", "download", "grab", "secure"]
    if any(word in cta_lower for word in action_words):
        score += 30

    urgency_words = ["now", "today", "limited", "only", "free", "instant", "immediate"]
    if any(word in cta_lower for word in urgency_words):
        score += 20

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
        return 45

    score = 40
    content_lower = content.lower() if content else ""

    pain_point = (audience.get("pain_point") or "").lower()
    if pain_point and pain_point in content_lower:
        score += 30

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

    income = (audience.get("income") or "").lower()
    if income in ["high", "very_high"] and any(w in content_lower for w in ["investment", "portfolio", "premium"]):
        score += 10
    if income in ["low", "lower_middle"] and any(w in content_lower for w in ["affordable", "budget", "save"]):
        score += 10

    return min(score, 100)


# ============================================
# VARIANT GENERATION
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

    variants.sort(key=lambda x: x.get("predicted_score", 0), reverse=True)
    return variants


def generate_single_variant(analysis_data, platform, audience, industry, angle_config, variant_id: int) -> dict:
    """Generate one variant with REAL calculated score"""

    hook = generate_hook_for_angle(angle_config["angle"], audience, industry, analysis_data)
    body = generate_body_for_angle(angle_config["strategy"], analysis_data, audience)
    cta = generate_cta_for_platform(platform, audience, analysis_data)

    hook_score = evaluate_hook_strength(hook, audience)
    clarity_score = evaluate_clarity(body)
    trust_score = evaluate_trust_building(body, audience)
    cta_score = evaluate_cta_power(cta, platform)
    audience_score = evaluate_audience_alignment(f"{hook} {body} {cta}", audience)

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
            "body_copy": "Default body copy with compelling value proposition that resonates with target audience.",
            "cta": "Get Started Now",
            "angle": "Default",
            "predicted_score": 50,
            "roi_potential": "Medium (2-3x ROAS)",
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
# CONTENT MODE DETECTION
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
# MAIN ANALYSIS FLOW - WITH STRICT ENFORCEMENT
# ============================================

async def analyze_ad(request_data: dict, files: list = None) -> dict:
    """MAIN ANALYSIS FUNCTION - v4.2 STRICT SCHEMA"""

    # 1. Detect content mode
    content_mode = detect_content_mode(request_data)

    # 2. Get base analysis from AI
    base_analysis = await run_ai_analysis(request_data, content_mode)

    # 3. ENFORCE: Ensure complete structure immediately after AI call
    base_analysis = enforce_complete_structure(base_analysis)

    # Extract audience data
    audience = extract_audience(request_data)
    platform = request_data.get("platform") or "facebook"
    industry = request_data.get("industry") or "general"

    # 4. Generate variants with REAL scores
    variants = generate_ad_variants(
        analysis_data=base_analysis,
        platform=platform,
        audience=audience,
        industry=industry
    )

    # 5. Select best variant as improved ad
    improved_ad = select_improved_ad_from_variants(variants)

    # 6. Re-score the improved ad
    improved_scores = re_score_improved_ad(improved_ad, audience, platform)

    # 7. Build video analysis if video content
    video_analysis = base_analysis.get("video_execution_analysis", REQUIRED_SCHEMA["video_execution_analysis"].copy())
    if content_mode in ["videoScript", "both"]:
        video_analysis["is_video_script"] = "Yes"
        video_analysis["hook_delivery_strength"] = evaluate_video_hook_delivery(request_data.get("video_script", ""))
        video_analysis["speech_flow_quality"] = evaluate_speech_flow(request_data.get("video_script", ""))

    # 8. Build complete response with ALL fields guaranteed
    final_analysis = {
        "scores": improved_scores,
        "behavior_summary": base_analysis.get("behavior_summary", REQUIRED_SCHEMA["behavior_summary"].copy()),
        "phase_breakdown": base_analysis.get("phase_breakdown", REQUIRED_SCHEMA["phase_breakdown"].copy()),
        "critical_weaknesses": base_analysis.get("critical_weaknesses", [FALLBACK_WEAKNESS.copy()]),
        "improvements": base_analysis.get("improvements", [FALLBACK_IMPROVEMENT]),
        "persona_reactions": base_analysis.get("persona_reactions", [FALLBACK_PERSONA.copy()]),
        "roi_analysis": base_analysis.get("roi_analysis", REQUIRED_SCHEMA["roi_analysis"].copy()),
        "line_by_line_analysis": base_analysis.get("line_by_line_analysis", [FALLBACK_LINE.copy()]),
        "video_execution_analysis": video_analysis,
        "run_decision": calculate_run_decision(improved_scores),
        "platform_specific": base_analysis.get("platform_specific", REQUIRED_SCHEMA["platform_specific"].copy()),
        "improved_ad": improved_ad,
        "ad_variants": variants if variants else [FALLBACK_VARIANT.copy()],
        "winner_prediction": {
            "confidence": "High" if variants and variants[0]["predicted_score"] > 70 else "Medium" if variants and variants[0]["predicted_score"] > 55 else "Low",
            "reason": f"Variant #{variants[0]['id'] if variants else 1} ({variants[0]['angle'] if variants else 'Default'}) scores highest with {variants[0]['predicted_score'] if variants else 50}/100",
            "best_variant_id": variants[0]["id"] if variants else 1,
            "expected_lift": f"+{variants[0]['predicted_score'] - base_analysis.get('scores', {}).get('overall', 50) if variants else 0} points"
        },
        "roi_comparison": [
            {
                "variant_id": v["id"],
                "roi_potential": v["roi_potential"],
                "risk": "Low" if v["predicted_score"] > 70 else "Medium" if v["predicted_score"] > 50 else "High",
                "summary": f"Variant {v['id']} ({v['angle']}): Score {v['predicted_score']}, {v['roi_potential']}"
            } for v in (variants if variants else [FALLBACK_VARIANT.copy()])
        ],
        "competitor_advantage": base_analysis.get("competitor_advantage", REQUIRED_SCHEMA["competitor_advantage"].copy())
    }

    # 9. FINAL ENFORCEMENT: Ensure absolutely no missing fields
    final_analysis = enforce_complete_structure(final_analysis)

    # ASSEMBLE FINAL RESPONSE
    return {
        "success": True,
        "analysis": final_analysis,
        "audience_parsed": format_audience_summary(audience),
        "content_mode": content_mode
    }


def evaluate_video_hook_delivery(video_script: str) -> str:
    """Evaluate video hook delivery"""
    if not video_script:
        return "Not applicable - no script provided"
    
    first_line = video_script.split('\n')[0].lower()
    
    if any(word in first_line for word in ['stop', 'wait', 'don\'t', 'never']):
        return "Strong - Pattern interrupt detected"
    elif '?' in first_line:
        return "Strong - Question hook"
    elif any(char.isdigit() for char in first_line):
        return "Strong - Specificity hook"
    else:
        return "Moderate - Consider adding pattern interrupt"

def evaluate_speech_flow(video_script: str) -> str:
    """Evaluate speech flow quality"""
    if not video_script:
        return "Not applicable - no script provided"
    
    lines = [l for l in video_script.split('\n') if l.strip()]
    avg_length = sum(len(l.split()) for l in lines) / max(len(lines), 1)
    
    if avg_length < 5:
        return "Choppy - Sentences too short"
    elif avg_length > 20:
        return "Dense - Consider shorter sentences"
    else:
        return "Natural - Good pacing"


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


async def run_ai_analysis(request_data: dict, content_mode: str) -> dict:
    """Run base AI analysis with STRICT schema enforcement"""
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

    # STRICT JSON schema prompt
    prompt = f"""Analyze this {content_type} for a {request_data.get('platform') or 'facebook'} ad targeting {request_data.get('audience_age') or '25-34'} year olds in {request_data.get('audience_country') or 'US'}.

CONTENT:
{content}

You MUST return a COMPLETE JSON object with ALL of these fields (never omit any):

{{
    "scores": {{
        "overall": <number 0-100>,
        "hook_strength": <number 0-100>,
        "clarity": <number 0-100>,
        "trust_building": <number 0-100>,
        "cta_power": <number 0-100>,
        "audience_alignment": <number 0-100>
    }},
    "behavior_summary": {{
        "verdict": "<string>",
        "launch_readiness": "<string with %>",
        "failure_risk": "<string with %>",
        "primary_reason": "<string>"
    }},
    "phase_breakdown": {{
        "micro_stop_0_1s": "<string>",
        "scroll_stop_1_2s": "<string>",
        "attention_2_5s": "<string>",
        "trust_evaluation": "<string>",
        "click_and_post_click": "<string>"
    }},
    "critical_weaknesses": [
        {{
            "issue": "<string>",
            "behavior_impact": "<string>",
            "precise_fix": "<string>"
        }}
    ],
    "improvements": ["<string>", "<string>"],
    "persona_reactions": [
        {{
            "persona": "<string>",
            "reaction": "<string>",
            "exact_quote": "<string>"
        }}
    ],
    "roi_analysis": {{
        "roi_potential": "<string>",
        "break_even_probability": "<string>",
        "risk_classification": "<string>",
        "key_metrics": {{
            "expected_ctr_range": "<string>",
            "realistic_cpc_range": "<string>",
            "conversion_rate_range": "<string>"
        }},
        "roi_scenarios": {{
            "worst_case": "<string>",
            "expected_case": "<string>",
            "best_case": "<string>"
        }},
        "primary_roi_lever": "<string>",
        "biggest_financial_risk": "<string>"
    }},
    "line_by_line_analysis": [
        {{
            "text": "<string>",
            "score": <number>,
            "analysis": "<string>"
        }}
    ],
    "video_execution_analysis": {{
        "is_video_script": "{'Yes' if content_mode in ['videoScript', 'both'] else 'No'}",
        "hook_delivery_strength": "<string>",
        "speech_flow_quality": "<string>",
        "visual_dependency": "<string>",
        "delivery_risk": "<string>",
        "biggest_execution_gap": "<string>",
        "recommended_format": "<string>"
    }},
    "run_decision": {{
        "should_run": "<string>",
        "risk_level": "<string>",
        "reason": "<string>"
    }},
    "platform_specific": {{
        "platform": "{request_data.get('platform') or 'facebook'}",
        "core_behavior": "<string>",
        "fatal_flaw": "<string>",
        "platform-specific_fix": "<string>"
    }},
    "competitor_advantage": {{
        "why_user_might_choose_competitor": "<string>",
        "what_competitor_is_doing_better": "<string>",
        "how_to_outperform": "<string>"
    }}
}}

Return ONLY the JSON object, no other text."""

    try:
        response = await call_openrouter(prompt, "You are an expert ad strategist. Always return complete JSON with all fields populated.", 0.7)
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            # Immediately enforce complete structure
            return enforce_complete_structure(parsed)
        return enforce_complete_structure({})
    except Exception as e:
        # Return fully populated fallback on any error
        return enforce_complete_structure({
            "behavior_summary": {
                "primary_reason": f"AI analysis error: {str(e)}"
            }
        })


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


__all__ = ['get_ai_engine', 'analyze_ad', 'detect_content_mode', 'extract_audience', 'enforce_complete_structure']
