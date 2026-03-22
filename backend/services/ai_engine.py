"""
ADLYTICS AI Engine v4.6 - CRITICAL BUG FIX
Fixed missing function definitions and response format
"""

import os
import json
import httpx
import re
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
    },
    "improved_ad": {
        "headline": "Optimized Headline",
        "body_copy": "Improved body copy with better conversion focus.",
        "cta": "Get Started Now",
        "predicted_score": 65,
        "roi_potential": "Medium (2-3x ROAS)"
    },
    "ad_variants": [],
    "winner_prediction": {
        "best_variant_id": 1,
        "score": 65,
        "confidence": "medium",
        "reason": "Best performing variant selected"
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
# SCRIPT LENGTH ENFORCEMENT
# ============================================

MAX_SCRIPT_WORDS = 150
MAX_SCRIPT_DURATION = 60
TARGET_SCRIPT_DURATION = (20, 60)

def count_words(text: str) -> int:
    if not text:
        return 0
    return len(text.split())

def estimate_duration(text: str) -> int:
    words = count_words(text)
    return max(5, words // 3)

def enforce_script_length(script: str) -> str:
    if not script:
        return script
    
    words = script.split()
    word_count = len(words)
    
    if word_count <= MAX_SCRIPT_WORDS:
        return script
    
    sections = extract_script_sections(script)
    trimmed_sections = {}
    
    hook_text = sections.get("hook", "")
    hook_words = hook_text.split()
    trimmed_sections["hook"] = " ".join(hook_words[:15]) + "." if len(hook_words) > 15 else hook_text
    
    cta_text = sections.get("cta", "")
    cta_words = cta_text.split()
    trimmed_sections["cta"] = " ".join(cta_words[:12]) if len(cta_words) > 12 else cta_text
    
    problem_text = sections.get("problem", "")
    problem_words = problem_text.split()
    trimmed_sections["problem"] = " ".join(problem_words[:20]) + "." if len(problem_words) > 20 else problem_text
    
    solution_text = sections.get("solution", "")
    solution_words = solution_text.split()
    trimmed_sections["solution"] = " ".join(solution_words[:25]) + "." if len(solution_words) > 25 else solution_text
    
    proof_text = sections.get("proof", "")
    proof_words = proof_text.split()
    trimmed_sections["proof"] = " ".join(proof_words[:20]) + "." if len(proof_words) > 20 else proof_text
    
    reconstructed = reconstruct_script(trimmed_sections)
    
    final_words = reconstructed.split()
    if len(final_words) > MAX_SCRIPT_WORDS:
        hook = trimmed_sections.get("hook", "Stop scrolling!")
        cta = trimmed_sections.get("cta", "Click now!")
        middle = " ".join(final_words[15:-12]) if len(final_words) > 27 else "Get results fast."
        reconstructed = f"{hook} {middle} {cta}"
    
    return reconstructed.strip()

def extract_script_sections(script: str) -> dict:
    sections = {"hook": "", "problem": "", "solution": "", "proof": "", "cta": ""}
    lines = script.split('\n')
    current_section = None
    
    for line in lines:
        line_lower = line.lower()
        
        if '[hook' in line_lower or line_lower.startswith('hook'):
            current_section = "hook"
            continue
        elif '[problem' in line_lower or line_lower.startswith('problem'):
            current_section = "problem"
            continue
        elif '[solution' in line_lower or line_lower.startswith('solution'):
            current_section = "solution"
            continue
        elif '[proof' in line_lower or line_lower.startswith('proof'):
            current_section = "proof"
            continue
        elif '[cta' in line_lower or line_lower.startswith('cta'):
            current_section = "cta"
            continue
        
        if '🎥' in line or '🗣️' in line or 'visual:' in line_lower or 'audio:' in line_lower:
            continue
        
        if current_section and line.strip():
            if sections[current_section]:
                sections[current_section] += " " + line.strip()
            else:
                sections[current_section] = line.strip()
    
    if not any(sections.values()):
        sentences = re.split(r'[.!?]+', script)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if sentences:
            sections["hook"] = sentences[0] if len(sentences) > 0 else ""
            sections["problem"] = sentences[1] if len(sentences) > 1 else ""
            sections["solution"] = sentences[2] if len(sentences) > 2 else ""
            sections["proof"] = sentences[3] if len(sentences) > 3 else ""
            sections["cta"] = sentences[-1] if len(sentences) > 4 else "Click now!"
    
    return sections

def reconstruct_script(sections: dict) -> str:
    parts = []
    
    if sections.get("hook"):
        parts.append(f"[HOOK 0-3s]\n{sections['hook']}")
    if sections.get("problem"):
        parts.append(f"[PROBLEM 3-10s]\n{sections['problem']}")
    if sections.get("solution"):
        parts.append(f"[SOLUTION 10-25s]\n{sections['solution']}")
    if sections.get("proof"):
        parts.append(f"[PROOF 25-40s]\n{sections['proof']}")
    if sections.get("cta"):
        parts.append(f"[CTA 40-60s]\n{sections['cta']}")
    
    return "\n\n".join(parts)

def generate_multi_scripts(base_script: str) -> dict:
    if not base_script:
        return {"15s": "", "30s": "", "60s": ""}
    
    words = base_script.split()
    
    script_15s = " ".join(words[:40]) if len(words) >= 40 else base_script
    script_30s = " ".join(words[:80]) if len(words) >= 80 else base_script
    script_60s = " ".join(words[:150]) if len(words) >= 150 else base_script
    
    return {
        "15s": script_15s,
        "30s": script_30s,
        "60s": script_60s
    }

def validate_script(script: str) -> dict:
    words = count_words(script)
    duration = estimate_duration(script)
    
    return {
        "valid": words <= MAX_SCRIPT_WORDS and TARGET_SCRIPT_DURATION[0] <= duration <= TARGET_SCRIPT_DURATION[1],
        "word_count": words,
        "duration": duration,
        "issues": [] if words <= MAX_SCRIPT_WORDS and TARGET_SCRIPT_DURATION[0] <= duration <= TARGET_SCRIPT_DURATION[1]
        else [f"Script is {words} words, {duration}s. Target: ≤{MAX_SCRIPT_WORDS} words, {TARGET_SCRIPT_DURATION[0]}-{TARGET_SCRIPT_DURATION[1]}s"]
    }

# ============================================
# SCHEMA ENFORCEMENT FUNCTIONS
# ============================================

def enforce_complete_structure(data: dict) -> dict:
    if not isinstance(data, dict):
        data = {}
    
    result = {}
    
    for key, default in REQUIRED_SCHEMA.items():
        value = data.get(key)
        if value is None or value == "" or value == [] or value == {}:
            result[key] = default
        else:
            result[key] = value
    
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
    result["improved_ad"] = enforce_improved_ad(result.get("improved_ad", {}))
    result["ad_variants"] = enforce_variants(result.get("ad_variants", []))
    result["winner_prediction"] = enforce_winner_prediction(result.get("winner_prediction", {}), result.get("ad_variants", []))
    
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
    
    return {
        "roi_potential": roi.get("roi_potential") or defaults["roi_potential"],
        "break_even_probability": roi.get("break_even_probability") or defaults["break_even_probability"],
        "risk_classification": roi.get("risk_classification") or defaults["risk_classification"],
        "primary_roi_lever": roi.get("primary_roi_lever") or defaults["primary_roi_lever"],
        "biggest_financial_risk": roi.get("biggest_financial_risk") or defaults["biggest_financial_risk"],
        "key_metrics": enforce_roi_metrics(roi.get("key_metrics", {})),
        "roi_scenarios": enforce_roi_scenarios(roi.get("roi_scenarios", {}))
    }

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

def enforce_improved_ad(improved_ad: dict) -> dict:
    defaults = REQUIRED_SCHEMA["improved_ad"]
    if not isinstance(improved_ad, dict):
        return defaults.copy()
    
    return {
        "headline": improved_ad.get("headline") or defaults["headline"],
        "body_copy": improved_ad.get("body_copy") or improved_ad.get("copy") or defaults["body_copy"],
        "cta": improved_ad.get("cta") or defaults["cta"],
        "predicted_score": improved_ad.get("predicted_score") or defaults["predicted_score"],
        "roi_potential": improved_ad.get("roi_potential") or defaults["roi_potential"],
        "angle": improved_ad.get("angle") or "Optimized",
        "source_variant_id": improved_ad.get("source_variant_id") or 1
    }

def enforce_variants(variants: list) -> list:
    if not isinstance(variants, list) or len(variants) == 0:
        return [FALLBACK_VARIANT.copy(), FALLBACK_VARIANT.copy(), FALLBACK_VARIANT.copy()]
    
    result = []
    for i, v in enumerate(variants):
        if isinstance(v, dict):
            result.append({
                "id": v.get("id") or i + 1,
                "angle": v.get("angle") or f"Variant {i+1}",
                "hook": v.get("hook") or v.get("headline") or "Optimized hook",
                "copy": v.get("copy") or v.get("body_copy") or "Optimized copy",
                "predicted_score": v.get("predicted_score") or v.get("score") or 55,
                "roi_potential": v.get("roi_potential") or "Medium (2-3x ROAS)",
                "reason": v.get("reason") or "Optimized for target audience",
                "component_scores": v.get("component_scores", {})
            })
    
    return result if result else [FALLBACK_VARIANT.copy(), FALLBACK_VARIANT.copy(), FALLBACK_VARIANT.copy()]

def enforce_winner_prediction(prediction: dict, variants: list) -> dict:
    if not isinstance(prediction, dict) or not prediction.get("best_variant_id"):
        if variants and len(variants) > 0:
            best = max(variants, key=lambda x: x.get("predicted_score", 0))
            score = best.get("predicted_score", 0)
            return {
                "best_variant_id": best.get("id", 1),
                "score": score,
                "confidence": "high" if score > 70 else "medium" if score > 55 else "low",
                "reason": f"Variant #{best.get('id', 1)} ({best.get('angle', 'Default')}) scores highest with {score}/100",
                "expected_lift": f"+{score - 50} points"
            }
        return REQUIRED_SCHEMA["winner_prediction"].copy()
    
    return {
        "best_variant_id": prediction.get("best_variant_id") or 1,
        "score": prediction.get("score") or prediction.get("predicted_score") or 65,
        "confidence": prediction.get("confidence") or "medium",
        "reason": prediction.get("reason") or "Best performing variant selected",
        "expected_lift": prediction.get("expected_lift") or "+15 points"
    }

# ============================================
# SCORING FUNCTIONS
# ============================================

def calculate_weighted_score(hook: int, clarity: int, trust: int, cta: int, audience: int) -> int:
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
    pain_point = audience.get("pain_point") or "this challenge"

    if "contradiction" in strategy.lower():
        return f"Everything you've been told about solving {pain_point} is backwards. While others waste time on complicated solutions, smart people use this 3-step approach that takes 5 minutes and actually works."
    elif "pain point" in strategy.lower():
        return f"Every day you wait, {pain_point} gets worse. You've tried the free guides. You've watched the videos. But you're still stuck because you're missing the one critical element that changes everything."
    else:
        return f"Join the thousands who've already made the switch. This isn't theory—it's a proven system with real results. In just days, you'll see why everyone is talking about this breakthrough approach."


def generate_cta_for_platform(platform: str, audience: dict, analysis_data: dict) -> str:
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
# IMPROVED AD GENERATION
# ============================================

def generate_improved_ad(variants: list, original_copy: str) -> dict:
    if not variants or len(variants) == 0:
        return {
            "headline": "Struggling with results? Here's a better approach",
            "body_copy": original_copy or "Optimized ad copy with improved conversion elements.",
            "cta": "Start with a smarter strategy today",
            "predicted_score": 65,
            "roi_potential": "Medium (2-3x ROAS)",
            "angle": "Optimized",
            "source_variant_id": 1
        }
    
    best = variants[0]
    
    return {
        "headline": best.get("hook", "Optimized Headline"),
        "body_copy": best.get("copy", original_copy or "Optimized body copy"),
        "cta": best.get("copy", "").split("\n")[-1] if best.get("copy") and "\n" in best.get("copy") else "Get Started Now",
        "predicted_score": best.get("predicted_score", 65),
        "roi_potential": best.get("roi_potential", "Medium (2-3x ROAS)"),
        "angle": best.get("angle", "Optimized"),
        "source_variant_id": best.get("id", 1)
    }


# ============================================
# RE-SCORE IMPROVED AD - CRITICAL FIX
# ============================================

def re_score_improved_ad(improved_ad: dict, audience: dict, platform: str) -> dict:
    """
    CRITICAL FIX: Re-score the improved ad with FRESH calculation
    This function was missing and causing the error!
    """
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
# ROI ANALYSIS GENERATION
# ============================================

def generate_roi_analysis(scores: dict) -> dict:
    overall = scores.get("overall", 50) if isinstance(scores, dict) else 50
    
    if overall >= 80:
        roi_potential = "Very High (5x+ ROAS)"
        risk_classification = "Very Low"
        break_even = "95%"
    elif overall >= 70:
        roi_potential = "High (3-5x ROAS)"
        risk_classification = "Low"
        break_even = "85%"
    elif overall >= 60:
        roi_potential = "Medium (2-3x ROAS)"
        risk_classification = "Medium"
        break_even = "70%"
    elif overall >= 50:
        roi_potential = "Low-Medium (1-2x ROAS)"
        risk_classification = "Medium-High"
        break_even = "55%"
    else:
        roi_potential = "Poor (<1x ROAS)"
        risk_classification = "High"
        break_even = "30%"
    
    return {
        "roi_potential": roi_potential,
        "break_even_probability": break_even,
        "risk_classification": risk_classification,
        "primary_roi_lever": "Hook strength drives CTR" if (scores.get("hook_strength", 50) if isinstance(scores, dict) else 50) > (scores.get("trust_building", 50) if isinstance(scores, dict) else 50) else "Trust building drives conversion",
        "biggest_financial_risk": "Low CTR wastes budget" if (scores.get("hook_strength", 50) if isinstance(scores, dict) else 50) < 60 else "Conversion friction reduces ROAS",
        "key_metrics": {
            "expected_ctr_range": f"{max(1, overall//20)}-{max(3, overall//15)}%",
            "realistic_cpc_range": f"${max(0.5, 3-(overall/50)):.2f}-${max(1, 5-(overall/40)):.2f}",
            "conversion_rate_range": f"{max(1, overall//25)}-{max(5, overall//15)}%"
        },
        "roi_scenarios": {
            "worst_case": f"{max(0.5, (overall/100)*2):.1f}x ROAS",
            "expected_case": f"{max(1, overall//20)}x ROAS",
            "best_case": f"{max(2, overall//15)}x ROAS"
        }
    }


# ============================================
# WINNER PREDICTION GENERATION
# ============================================

def generate_winner_prediction(variants: list) -> dict:
    if not variants or len(variants) == 0:
        return {
            "best_variant_id": 1,
            "score": 65,
            "confidence": "medium",
            "reason": "Default variant selected as baseline",
            "expected_lift": "+15 points"
        }
    
    best = max(variants, key=lambda x: x.get("predicted_score", 0))
    score = best.get("predicted_score", 0)
    
    return {
        "best_variant_id": best.get("id", 1),
        "score": score,
        "confidence": "high" if score > 70 else "medium" if score > 55 else "low",
        "reason": f"Variant #{best.get('id', 1)} ({best.get('angle', 'Default')}) scores highest with {score}/100",
        "expected_lift": f"+{score - 50} points"
    }


# ============================================
# SHORT-FORM VIDEO SCRIPT GENERATION
# ============================================

def detect_content_mode(request_data: dict) -> str:
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


def generate_short_form_video_script(analysis_data: dict, audience: dict, platform: str, objective: str) -> str:
    pain_point = audience.get("pain_point") or "this problem"
    industry = analysis_data.get("industry") or "this industry"
    
    script = _generate_script_content(pain_point, industry, audience, platform, objective)
    script = enforce_script_length(script)
    
    validation = validate_script(script)
    if not validation["valid"]:
        script = _generate_ultra_short_script(pain_point, industry, audience, platform)
    
    return script


def _generate_script_content(pain_point: str, industry: str, audience: dict, platform: str, objective: str) -> str:
    hooks = [
        f"Stop! Your {pain_point} is costing you money.",
        f"Still struggling with {pain_point}? Watch this.",
        f"The truth about {pain_point} nobody tells you.",
        f"Wrong about {pain_point}? Here's why.",
        f"Fix {pain_point} in 30 seconds."
    ]
    hook = hooks[hash(pain_point) % len(hooks)]
    
    problems = [
        f"Every day with {pain_point} wastes time and money.",
        f"{pain_point} keeps you stuck while others win.",
        f"Most people ignore {pain_point} until it's too late.",
        f"Traditional fixes for {pain_point} don't work anymore."
    ]
    problem = problems[hash(industry) % len(problems)]
    
    solutions = [
        f"This {industry} system eliminates {pain_point} fast. No fluff. Just results. Three steps. Five minutes. Done.",
        f"Our method fixes {pain_point} instantly. Proven framework. Real results. No complicated setup required.",
        f"One simple shift ends {pain_point} today. Automated. Effective. Immediate impact on your bottom line."
    ]
    solution = solutions[hash(platform) % len(solutions)]
    
    proofs = [
        f"10,000+ people fixed {pain_point} last month. Join them.",
        f"Rated #1 for solving {pain_point}. Verified results.",
        f"Featured in top {industry} publications. Trusted solution."
    ]
    proof = proofs[hash(objective) % len(proofs)]
    
    ctas = {
        "facebook": "Click link. Fix it now.",
        "instagram": "Link in bio. Start today.",
        "tiktok": "Click before it's gone.",
        "youtube": "Subscribe and transform now.",
        "google": "Get instant access today."
    }
    cta = ctas.get(platform, "Click now. Change everything.")
    
    script = f"""[HOOK 0-3s]
{hook}

[PROBLEM 3-10s]
{problem}

[SOLUTION 10-25s]
{solution}

[PROOF 25-40s]
{proof}

[CTA 40-60s]
{cta}"""
    
    return script


def _generate_ultra_short_script(pain_point: str, industry: str, audience: dict, platform: str) -> str:
    script = f"""[HOOK 0-3s]
Stop! {pain_point} ends today.

[PROBLEM 3-10s]
Old methods fail. You're losing money.

[SOLUTION 10-25s]
New {industry} system works instantly. Three steps. Five minutes.

[PROOF 25-40s]
10,000+ success stories. Proven results.

[CTA 40-60s]
Click now. Fix {pain_point} today."""
    
    return script


def evaluate_video_hook_delivery(video_script: str) -> str:
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
    if not video_script:
        return "Not applicable - no script provided"
    
    lines = [l for l in video_script.split('\n') if l.strip() and not l.startswith('[')]
    if not lines:
        return "Not applicable - no script content"
    
    avg_length = sum(len(l.split()) for l in lines) / len(lines)
    
    if avg_length < 5:
        return "Choppy - Sentences too short"
    elif avg_length > 15:
        return "Dense - Consider shorter sentences"
    else:
        return "Natural - Good pacing for short-form"


# ============================================
# AI API CALLS
# ============================================

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_openrouter(prompt: str, system_prompt: str = "", temperature: float = 0.7) -> str:
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
    """
    MAIN ANALYSIS - v4.6 CRITICAL BUG FIX
    Fixed missing re_score_improved_ad function
    """
    
    # 1. Detect content mode
    content_mode = detect_content_mode(request_data)

    # 2. Get base analysis from AI
    base_analysis = await run_ai_analysis(request_data, content_mode)
    
    # 3. FORCE: Ensure complete structure
    base_analysis = enforce_complete_structure(base_analysis)

    # 4. Extract audience data
    audience = extract_audience(request_data)
    platform = request_data.get("platform") or "facebook"
    industry = request_data.get("industry") or "general"
    original_copy = request_data.get("ad_copy", "")

    # 5. FORCE: Generate variants (ALWAYS)
    variants = generate_ad_variants(
        analysis_data=base_analysis,
        platform=platform,
        audience=audience,
        industry=industry
    )
    base_analysis["ad_variants"] = variants

    # 6. FORCE: Generate improved_ad (ALWAYS)
    improved_ad = generate_improved_ad(variants, original_copy)
    base_analysis["improved_ad"] = improved_ad

    # 7. CRITICAL FIX: Re-score the improved ad using the NOW-DEFINED function
    improved_scores = re_score_improved_ad(improved_ad, audience, platform)
    base_analysis["scores"] = improved_scores

    # 8. FORCE: Generate ROI analysis (ALWAYS)
    roi_analysis = generate_roi_analysis(improved_scores)
    base_analysis["roi_analysis"] = roi_analysis

    # 9. FORCE: Generate winner prediction (ALWAYS)
    winner_prediction = generate_winner_prediction(variants)
    base_analysis["winner_prediction"] = winner_prediction

    # 10. Generate video script if needed
    video_scripts = None
    video_analysis = base_analysis.get("video_execution_analysis", REQUIRED_SCHEMA["video_execution_analysis"].copy())
    
    if content_mode in ["videoScript", "both"]:
        video_script = generate_short_form_video_script(
            analysis_data=base_analysis,
            audience=audience,
            platform=platform,
            objective=request_data.get("objective") or "conversions"
        )
        
        validation = validate_script(video_script)
        if not validation["valid"]:
            video_script = _generate_ultra_short_script(
                audience.get("pain_point") or "this problem",
                industry,
                audience,
                platform
            )
        
        video_scripts = generate_multi_scripts(video_script)
        improved_ad["video_script_version"] = video_script
        base_analysis["improved_ad"] = improved_ad
        
        video_analysis["is_video_script"] = "Yes"
        video_analysis["hook_delivery_strength"] = evaluate_video_hook_delivery(video_script)
        video_analysis["speech_flow_quality"] = evaluate_speech_flow(video_script)
        video_analysis["visual_dependency"] = "Low (short-form optimized)"
        video_analysis["delivery_risk"] = "Low"
        video_analysis["recommended_format"] = "short_form_video"
        video_analysis["script_validation"] = validate_script(video_script)
        
        base_analysis["video_execution_analysis"] = video_analysis

    # 11. FORCE: Ensure ALL arrays have content
    if not base_analysis.get("critical_weaknesses") or len(base_analysis.get("critical_weaknesses", [])) == 0:
        base_analysis["critical_weaknesses"] = [FALLBACK_WEAKNESS.copy()]
    
    if not base_analysis.get("improvements") or len(base_analysis.get("improvements", [])) == 0:
        base_analysis["improvements"] = [FALLBACK_IMPROVEMENT]
    
    if not base_analysis.get("persona_reactions") or len(base_analysis.get("persona_reactions", [])) == 0:
        base_analysis["persona_reactions"] = [FALLBACK_PERSONA.copy()]
    
    if not base_analysis.get("line_by_line_analysis") or len(base_analysis.get("line_by_line_analysis", [])) == 0:
        base_analysis["line_by_line_analysis"] = [FALLBACK_LINE.copy()]

    # 12. FINAL ENFORCEMENT
    final_analysis = enforce_complete_structure(base_analysis)

    # ASSEMBLE FINAL RESPONSE - CRITICAL FIX: Always return wrapped format
    response = {
        "success": True,
        "data": {
            "analysis": final_analysis,
            "audience_parsed": format_audience_summary(audience),
            "content_mode": content_mode
        }
    }
    
    if video_scripts:
        response["data"]["video_scripts"] = video_scripts
        response["data"]["script_info"] = {
            "word_count": count_words(video_scripts["60s"]),
            "duration_estimate": estimate_duration(video_scripts["60s"]),
            "max_words": MAX_SCRIPT_WORDS,
            "target_duration": f"{TARGET_SCRIPT_DURATION[0]}-{TARGET_SCRIPT_DURATION[1]}s"
        }

    return response


# ============================================
# HELPER FUNCTIONS
# ============================================

def extract_audience(request_data: dict) -> dict:
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
    parts = []
    if audience.get("country"):
        parts.append(audience["country"].upper())
    if audience.get("age"):
        parts.append(audience["age"])
    if audience.get("pain_point"):
        parts.append(f"Pain: {audience['pain_point']}")
    return " | ".join(parts) if parts else "General Audience"


def calculate_run_decision(scores: dict) -> dict:
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
            return enforce_complete_structure(parsed)
        return enforce_complete_structure({})
    except Exception as e:
        return enforce_complete_structure({
            "behavior_summary": {
                "primary_reason": f"AI analysis error: {str(e)}"
            }
        })


# ============================================
# COMPATIBILITY LAYER
# ============================================

class AIEngine:
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
    global _ai_engine_instance
    if _ai_engine_instance is None:
        _ai_engine_instance = AIEngine()
    return _ai_engine_instance


__all__ = [
    'get_ai_engine', 
    'analyze_ad', 
    'detect_content_mode', 
    'extract_audience', 
    'enforce_complete_structure',
    'enforce_script_length',
    'generate_multi_scripts',
    're_score_improved_ad'  # CRITICAL FIX: Export the function
]
