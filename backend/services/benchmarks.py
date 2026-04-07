"""
ADLYTICS Industry Benchmarks Module
Real-world advertising performance benchmarks by platform and industry.
Sources: WordStream 2025, Triple Whale 2025, Lebesgue 2026, Meta Business Suite.

Used for:
1. Predictive Performance Scoring (percentile ranking)
2. Industry Benchmarking (CTR, CPA, CVR comparison)
3. Element-level scoring calibration
"""

from typing import Dict, Any, Optional

# ─── PLATFORM × INDUSTRY BENCHMARKS ───────────────────────────────────────
# Format: { platform: { industry: { metric: value } } }
# CTR = click-through rate (%), CPA = cost per acquisition ($), CVR = conversion rate (%)
# CPM = cost per mille ($), avg_score = typical ad quality score (0-100)

BENCHMARKS = {
    "facebook": {
        "_default": {"ctr": 1.49, "cpa": 38.17, "cvr": 1.57, "cpm": 13.48, "avg_score": 52},
        "finance": {"ctr": 1.01, "cpa": 52.30, "cvr": 1.20, "cpm": 14.80, "avg_score": 48},
        "forex": {"ctr": 0.85, "cpa": 58.00, "cvr": 0.95, "cpm": 15.20, "avg_score": 42},
        "crypto": {"ctr": 0.78, "cpa": 62.50, "cvr": 0.80, "cpm": 16.00, "avg_score": 40},
        "ecommerce": {"ctr": 1.59, "cpa": 33.21, "cvr": 1.84, "cpm": 12.90, "avg_score": 55},
        "saas": {"ctr": 1.15, "cpa": 48.50, "cvr": 1.35, "cpm": 14.20, "avg_score": 50},
        "health": {"ctr": 1.32, "cpa": 38.55, "cvr": 1.50, "cpm": 12.46, "avg_score": 53},
        "education": {"ctr": 1.45, "cpa": 35.00, "cvr": 1.72, "cpm": 11.50, "avg_score": 54},
        "fashion": {"ctr": 2.84, "cpa": 29.99, "cvr": 2.10, "cpm": 10.80, "avg_score": 58},
        "food": {"ctr": 1.92, "cpa": 30.25, "cvr": 2.02, "cpm": 11.20, "avg_score": 56},
        "tech": {"ctr": 1.25, "cpa": 45.00, "cvr": 1.40, "cpm": 13.80, "avg_score": 51},
        "real_estate": {"ctr": 1.08, "cpa": 55.00, "cvr": 1.10, "cpm": 14.50, "avg_score": 47},
        "other": {"ctr": 1.49, "cpa": 38.17, "cvr": 1.57, "cpm": 13.48, "avg_score": 52},
    },
    "instagram": {
        "_default": {"ctr": 0.98, "cpa": 42.00, "cvr": 1.30, "cpm": 11.50, "avg_score": 50},
        "finance": {"ctr": 0.72, "cpa": 56.00, "cvr": 0.95, "cpm": 13.00, "avg_score": 45},
        "forex": {"ctr": 0.60, "cpa": 64.00, "cvr": 0.80, "cpm": 14.00, "avg_score": 40},
        "crypto": {"ctr": 0.55, "cpa": 68.00, "cvr": 0.70, "cpm": 14.50, "avg_score": 38},
        "ecommerce": {"ctr": 1.25, "cpa": 35.00, "cvr": 1.65, "cpm": 10.50, "avg_score": 55},
        "saas": {"ctr": 0.88, "cpa": 52.00, "cvr": 1.10, "cpm": 12.50, "avg_score": 48},
        "health": {"ctr": 1.05, "cpa": 40.00, "cvr": 1.25, "cpm": 11.00, "avg_score": 52},
        "education": {"ctr": 1.10, "cpa": 38.00, "cvr": 1.45, "cpm": 10.80, "avg_score": 53},
        "fashion": {"ctr": 2.15, "cpa": 28.00, "cvr": 2.30, "cpm": 9.80, "avg_score": 60},
        "food": {"ctr": 1.55, "cpa": 32.00, "cvr": 1.80, "cpm": 10.20, "avg_score": 57},
        "tech": {"ctr": 0.92, "cpa": 48.00, "cvr": 1.15, "cpm": 12.20, "avg_score": 49},
        "real_estate": {"ctr": 0.80, "cpa": 58.00, "cvr": 0.90, "cpm": 13.50, "avg_score": 45},
        "other": {"ctr": 0.98, "cpa": 42.00, "cvr": 1.30, "cpm": 11.50, "avg_score": 50},
    },
    "tiktok": {
        "_default": {"ctr": 0.84, "cpa": 28.00, "cvr": 1.92, "cpm": 4.80, "avg_score": 48},
        "finance": {"ctr": 0.55, "cpa": 38.00, "cvr": 1.20, "cpm": 5.50, "avg_score": 42},
        "forex": {"ctr": 0.48, "cpa": 42.00, "cvr": 1.00, "cpm": 5.80, "avg_score": 38},
        "crypto": {"ctr": 0.62, "cpa": 35.00, "cvr": 1.40, "cpm": 5.20, "avg_score": 45},
        "ecommerce": {"ctr": 1.20, "cpa": 22.00, "cvr": 2.50, "cpm": 4.20, "avg_score": 55},
        "saas": {"ctr": 0.70, "cpa": 35.00, "cvr": 1.50, "cpm": 5.00, "avg_score": 46},
        "health": {"ctr": 0.90, "cpa": 26.00, "cvr": 2.00, "cpm": 4.50, "avg_score": 50},
        "education": {"ctr": 0.95, "cpa": 24.00, "cvr": 2.20, "cpm": 4.30, "avg_score": 52},
        "fashion": {"ctr": 1.50, "cpa": 18.00, "cvr": 3.00, "cpm": 3.80, "avg_score": 58},
        "food": {"ctr": 1.30, "cpa": 20.00, "cvr": 2.60, "cpm": 4.00, "avg_score": 55},
        "tech": {"ctr": 0.75, "cpa": 32.00, "cvr": 1.60, "cpm": 5.10, "avg_score": 47},
        "real_estate": {"ctr": 0.50, "cpa": 45.00, "cvr": 0.85, "cpm": 6.00, "avg_score": 40},
        "other": {"ctr": 0.84, "cpa": 28.00, "cvr": 1.92, "cpm": 4.80, "avg_score": 48},
    },
    "youtube": {
        "_default": {"ctr": 0.65, "cpa": 45.00, "cvr": 1.40, "cpm": 9.50, "avg_score": 50},
        "finance": {"ctr": 0.52, "cpa": 58.00, "cvr": 1.05, "cpm": 11.00, "avg_score": 46},
        "forex": {"ctr": 0.45, "cpa": 65.00, "cvr": 0.90, "cpm": 12.00, "avg_score": 42},
        "crypto": {"ctr": 0.55, "cpa": 55.00, "cvr": 1.10, "cpm": 10.50, "avg_score": 44},
        "ecommerce": {"ctr": 0.80, "cpa": 38.00, "cvr": 1.70, "cpm": 8.50, "avg_score": 54},
        "saas": {"ctr": 0.60, "cpa": 52.00, "cvr": 1.25, "cpm": 10.00, "avg_score": 48},
        "health": {"ctr": 0.70, "cpa": 42.00, "cvr": 1.50, "cpm": 9.00, "avg_score": 51},
        "education": {"ctr": 0.75, "cpa": 35.00, "cvr": 1.80, "cpm": 8.00, "avg_score": 53},
        "fashion": {"ctr": 0.90, "cpa": 32.00, "cvr": 2.00, "cpm": 7.50, "avg_score": 56},
        "food": {"ctr": 0.85, "cpa": 34.00, "cvr": 1.85, "cpm": 7.80, "avg_score": 55},
        "tech": {"ctr": 0.58, "cpa": 50.00, "cvr": 1.30, "cpm": 10.20, "avg_score": 49},
        "real_estate": {"ctr": 0.48, "cpa": 60.00, "cvr": 0.95, "cpm": 11.50, "avg_score": 44},
        "other": {"ctr": 0.65, "cpa": 45.00, "cvr": 1.40, "cpm": 9.50, "avg_score": 50},
    },
    "google": {
        "_default": {"ctr": 6.11, "cpa": 53.52, "cvr": 7.04, "cpm": 15.00, "avg_score": 52},
        "finance": {"ctr": 5.50, "cpa": 65.00, "cvr": 5.80, "cpm": 18.00, "avg_score": 48},
        "forex": {"ctr": 4.20, "cpa": 72.00, "cvr": 4.50, "cpm": 20.00, "avg_score": 42},
        "crypto": {"ctr": 3.80, "cpa": 78.00, "cvr": 3.90, "cpm": 22.00, "avg_score": 40},
        "ecommerce": {"ctr": 6.50, "cpa": 45.27, "cvr": 7.50, "cpm": 14.00, "avg_score": 55},
        "saas": {"ctr": 5.80, "cpa": 55.00, "cvr": 6.50, "cpm": 16.00, "avg_score": 50},
        "health": {"ctr": 6.20, "cpa": 50.00, "cvr": 7.20, "cpm": 14.50, "avg_score": 53},
        "education": {"ctr": 6.80, "cpa": 42.00, "cvr": 8.00, "cpm": 13.00, "avg_score": 55},
        "fashion": {"ctr": 7.50, "cpa": 38.00, "cvr": 8.50, "cpm": 12.00, "avg_score": 57},
        "food": {"ctr": 7.20, "cpa": 40.00, "cvr": 8.20, "cpm": 12.50, "avg_score": 56},
        "tech": {"ctr": 5.60, "cpa": 58.00, "cvr": 6.00, "cpm": 17.00, "avg_score": 49},
        "real_estate": {"ctr": 5.00, "cpa": 68.00, "cvr": 5.20, "cpm": 19.00, "avg_score": 46},
        "other": {"ctr": 6.11, "cpa": 53.52, "cvr": 7.04, "cpm": 15.00, "avg_score": 52},
    },
}

# ─── ELEMENT-LEVEL BENCHMARK WEIGHTS ──────────────────────────────────────
# How much each creative element typically contributes to ad performance
# Based on Meta creative research, VidMob studies, and industry analysis

ELEMENT_WEIGHTS = {
    "headline": {
        "weight": 0.20,
        "description": "First text line or hook text overlay",
        "scoring_criteria": "Specificity, urgency, curiosity gap, number inclusion",
    },
    "color_palette": {
        "weight": 0.08,
        "description": "Dominant colors, contrast, brand consistency",
        "scoring_criteria": "Contrast ratio, emotional color psychology, platform nativeness",
    },
    "logo_placement": {
        "weight": 0.05,
        "description": "Brand logo visibility, timing, and positioning",
        "scoring_criteria": "Visibility within first 3s, size appropriateness, non-intrusive placement",
    },
    "music_audio": {
        "weight": 0.12,
        "description": "Background music, sound effects, audio energy",
        "scoring_criteria": "Trending sounds, energy match with visuals, audio clarity",
    },
    "voiceover": {
        "weight": 0.15,
        "description": "Spoken narration, tone, pacing, persuasion",
        "scoring_criteria": "Clarity, emotional tone, pacing, persuasion techniques, CTA delivery",
    },
    "video_pacing": {
        "weight": 0.10,
        "description": "Cut frequency, scene transitions, visual rhythm",
        "scoring_criteria": "Scene change every 2-3s for social, smooth transitions, energy build",
    },
    "cta_design": {
        "weight": 0.15,
        "description": "Call-to-action button/text design, placement, timing",
        "scoring_criteria": "Contrast, urgency language, benefit-driven, placement in final 20%",
    },
    "text_overlays": {
        "weight": 0.10,
        "description": "On-screen text, captions, subtitle styling",
        "scoring_criteria": "Readability, conciseness, key message highlighting, font choice",
    },
    "social_proof": {
        "weight": 0.05,
        "description": "Testimonials, numbers, trust badges, user content",
        "scoring_criteria": "Specificity, believability, relevance to audience",
    },
}


def get_benchmarks(platform: str, industry: str) -> Dict[str, Any]:
    """Get benchmark data for a specific platform and industry."""
    platform = platform.lower()
    industry = industry.lower()

    platform_data = BENCHMARKS.get(platform, BENCHMARKS.get("facebook"))
    industry_data = platform_data.get(industry, platform_data.get("_default"))

    return industry_data


def calculate_percentile(score: int, platform: str, industry: str) -> int:
    """Calculate what percentile an ad score falls in for its platform/industry.
    Returns 0-100 percentile (e.g., 72 means 'outperforms 72% of ads')."""
    benchmarks = get_benchmarks(platform, industry)
    avg_score = benchmarks.get("avg_score", 50)

    # Map ad score to percentile using sigmoid-like distribution
    # avg_score maps to ~50th percentile
    # Score of 80+ maps to 90th+ percentile
    # Score of 30- maps to 10th- percentile
    diff = score - avg_score
    if diff >= 0:
        # Above average: map to 50-99th percentile
        percentile = 50 + min(49, int(diff * 1.8))
    else:
        # Below average: map to 1-49th percentile
        percentile = 50 + max(-49, int(diff * 1.8))

    return max(1, min(99, percentile))


def build_benchmark_context(platform: str, industry: str) -> str:
    """Build benchmark context string for AI prompts."""
    b = get_benchmarks(platform, industry)

    # Get all platform benchmarks for cross-platform comparison
    cross_platform = {}
    for p in ["facebook", "instagram", "tiktok", "youtube"]:
        pb = get_benchmarks(p, industry)
        cross_platform[p] = pb

    return f"""
INDUSTRY BENCHMARKS (Real {industry.title()} ads on {platform.title()}, 2025-2026 data):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Average CTR: {b['ctr']}% | Average CPA: ${b['cpa']:.2f} | Average CVR: {b['cvr']}%
Average CPM: ${b['cpm']:.2f} | Average Ad Quality Score: {b['avg_score']}/100

CROSS-PLATFORM COMPARISON ({industry.title()}):
  Facebook: CTR {cross_platform['facebook']['ctr']}% | CPA ${cross_platform['facebook']['cpa']:.2f} | CVR {cross_platform['facebook']['cvr']}%
  Instagram: CTR {cross_platform['instagram']['ctr']}% | CPA ${cross_platform['instagram']['cpa']:.2f} | CVR {cross_platform['instagram']['cvr']}%
  TikTok: CTR {cross_platform['tiktok']['ctr']}% | CPA ${cross_platform['tiktok']['cpa']:.2f} | CVR {cross_platform['tiktok']['cvr']}%
  YouTube: CTR {cross_platform['youtube']['ctr']}% | CPA ${cross_platform['youtube']['cpa']:.2f} | CVR {cross_platform['youtube']['cvr']}%

SCORING CALIBRATION:
An ad scoring {b['avg_score']}/100 represents average performance for {industry.title()} on {platform.title()}.
Score 70+ = top 25% of ads. Score 80+ = top 10%. Score 90+ = top 3%.
Score 40- = bottom 25%. Score 30- = bottom 10%.

USE THESE BENCHMARKS TO:
1. Predict realistic CTR, CPA, and CVR ranges for this specific ad
2. Calculate what percentile this ad would rank among {industry.title()} ads
3. Identify which elements would most improve performance relative to benchmarks
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""


def build_element_scoring_context() -> str:
    """Build element-level scoring context for AI prompts."""
    elements = []
    for name, info in ELEMENT_WEIGHTS.items():
        elements.append(
            f"  {name} (weight: {info['weight']*100:.0f}%): {info['description']}\n"
            f"    Score criteria: {info['scoring_criteria']}"
        )

    return f"""
ELEMENT-LEVEL BREAKDOWN — Score each creative element individually (0-100):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{chr(10).join(elements)}

For each element, provide:
- score (0-100)
- observation (what you specifically see/hear)
- impact ("high", "medium", "low") — how much this element affects overall performance
- fix (specific actionable improvement)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
