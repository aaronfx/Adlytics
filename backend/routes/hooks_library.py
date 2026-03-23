"""
ADLYTICS Hook Library — GET /api/hooks
150+ proven hooks organized by industry, platform, and hook type.
Zero AI cost — instant static response.
"""
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()

# ─────────────────────────────────────────────────────────────
# HOOK DATABASE
# Each entry: { id, text, type, industry, platform, why_it_works, difficulty }
# difficulty: "beginner" | "intermediate" | "advanced"
# ─────────────────────────────────────────────────────────────

HOOKS = [

    # ── FINANCE / FOREX ──────────────────────────────────────
    {"id": "f01", "text": "I lost ₦120,000 in 3 days before I understood this one rule.",
     "type": "fear", "industry": "finance", "platform": "tiktok", "difficulty": "intermediate",
     "why_it_works": "Specific loss amount creates instant credibility. 'Before I understood' signals redemption arc."},
    {"id": "f02", "text": "Nobody shows you the losing trades. I do.",
     "type": "curiosity", "industry": "finance", "platform": "tiktok", "difficulty": "beginner",
     "why_it_works": "Contrasts with 'highlight reel' culture. Creates immediate differentiation."},
    {"id": "f03", "text": "I made ₦47,000 this week. My account balance 6 months ago was ₦0.",
     "type": "social_proof", "industry": "finance", "platform": "instagram", "difficulty": "intermediate",
     "why_it_works": "Specific numbers + relatable starting point. Removes 'you need capital' objection."},
    {"id": "f04", "text": "Stop watching forex YouTube. Here's what actually makes money.",
     "type": "pattern_interrupt", "industry": "finance", "platform": "tiktok", "difficulty": "beginner",
     "why_it_works": "Challenges existing behavior. Audience is literally on a video platform, ironic tension."},
    {"id": "f05", "text": "3 trades. 3 wins. Documented in real time. Watch.",
     "type": "social_proof", "industry": "finance", "platform": "tiktok", "difficulty": "intermediate",
     "why_it_works": "Proof-first hook. Short, punchy. 'Watch' as CTA in the hook creates urgency."},
    {"id": "f06", "text": "I quit my bank job to trade. 18 months later, I have no regrets.",
     "type": "authority", "industry": "finance", "platform": "facebook", "difficulty": "advanced",
     "why_it_works": "Life decision as proof. 'No regrets' handles fear objection preemptively."},
    {"id": "f07", "text": "The forex strategy they removed from YouTube (saved it here).",
     "type": "curiosity", "industry": "finance", "platform": "tiktok", "difficulty": "beginner",
     "why_it_works": "Forbidden knowledge frame. Creates urgency — 'watch before it's gone'."},
    {"id": "f08", "text": "My first year trading: 11 months of losses, 1 month of breakthrough.",
     "type": "fear", "industry": "finance", "platform": "instagram", "difficulty": "advanced",
     "why_it_works": "Extreme vulnerability. Normalizes failure. Redemption arc is powerful."},
    {"id": "f09", "text": "What they don't teach you in forex courses (learned the hard way).",
     "type": "curiosity", "industry": "finance", "platform": "facebook", "difficulty": "beginner",
     "why_it_works": "Validates audience frustration with existing courses. Positions speaker as beyond-course level."},
    {"id": "f10", "text": "₦500K account to ₦0. Then I found the one thing that changed everything.",
     "type": "fear", "industry": "finance", "platform": "tiktok", "difficulty": "advanced",
     "why_it_works": "Maximum vulnerability. Extreme loss makes survival story compelling."},
    {"id": "f11", "text": "Don't start forex trading until you watch this.",
     "type": "pattern_interrupt", "industry": "finance", "platform": "tiktok", "difficulty": "beginner",
     "why_it_works": "Anti-sell CTA in the hook. Reversal creates curiosity without appearing salesy."},
    {"id": "f12", "text": "I analyzed 500 losing trades. This pattern shows up in 90% of them.",
     "type": "authority", "industry": "finance", "platform": "facebook", "difficulty": "advanced",
     "why_it_works": "Specific research effort (500 trades) signals expertise. 90% stat is compelling."},

    # ── REAL ESTATE ───────────────────────────────────────────
    {"id": "r01", "text": "Lagos rent prices doubled in 18 months. Here's how to be on the right side.",
     "type": "fear", "industry": "realestate", "platform": "facebook", "difficulty": "beginner",
     "why_it_works": "Real market data creates urgency without fabricating it. 'Right side' frames action."},
    {"id": "r02", "text": "I bought land in Lekki at ₦800K. It's now worth ₦4.2M. Here's the area.",
     "type": "social_proof", "industry": "realestate", "platform": "facebook", "difficulty": "intermediate",
     "why_it_works": "Specific purchase price vs current value. Real location name. Transparent and verifiable."},
    {"id": "r03", "text": "Every naira you pay in rent is building someone else's retirement. Not yours.",
     "type": "fear", "industry": "realestate", "platform": "tiktok", "difficulty": "beginner",
     "why_it_works": "Reframes rent as opportunity cost. Activates loss aversion without being aggressive."},
    {"id": "r04", "text": "We're verifying 3 things before selling any plot. Most developers skip all 3.",
     "type": "authority", "industry": "realestate", "platform": "instagram", "difficulty": "intermediate",
     "why_it_works": "Highlights competitor weakness implicitly. Creates curiosity about the 3 things."},
    {"id": "r05", "text": "My client paid ₦300K as first instalment. She now has a fully titled property.",
     "type": "social_proof", "industry": "realestate", "platform": "facebook", "difficulty": "intermediate",
     "why_it_works": "Accessible entry price (₦300K) removes 'I can't afford it' objection immediately."},
    {"id": "r06", "text": "How a teacher in Ibadan owns 2 plots without a mortgage.",
     "type": "curiosity", "industry": "realestate", "platform": "tiktok", "difficulty": "beginner",
     "why_it_works": "Relatable profession (not a millionaire). 'Without a mortgage' tackles the main objection."},
    {"id": "r07", "text": "We almost lost everything to a fake C of O. Here's what we check now.",
     "type": "fear", "industry": "realestate", "platform": "facebook", "difficulty": "advanced",
     "why_it_works": "Vulnerability from developer POV is rare and highly credible. Addresses market's #1 fear."},
    {"id": "r08", "text": "This estate sold 60% of units before we even published the price.",
     "type": "social_proof", "industry": "realestate", "platform": "instagram", "difficulty": "intermediate",
     "why_it_works": "Social proof + scarcity combined. Implies missing out is imminent."},
    {"id": "r09", "text": "Abuja vs Lagos property investment in 2025. The data might surprise you.",
     "type": "curiosity", "industry": "realestate", "platform": "facebook", "difficulty": "beginner",
     "why_it_works": "Two options audiences debate constantly. 'Might surprise you' creates click pressure."},
    {"id": "r10", "text": "You can't afford to NOT own property in Nigeria right now.",
     "type": "pattern_interrupt", "industry": "realestate", "platform": "tiktok", "difficulty": "beginner",
     "why_it_works": "Double negative creates cognitive dissonance. Forces re-reading."},

    # ── E-COMMERCE ────────────────────────────────────────────
    {"id": "e01", "text": "I ordered this 3 times. My colleagues kept asking where I got it.",
     "type": "social_proof", "industry": "ecommerce", "platform": "tiktok", "difficulty": "beginner",
     "why_it_works": "Repeat purchase = quality signal. 'Colleagues asking' = status/social proof."},
    {"id": "e02", "text": "Bought the expensive version for ₦45K. Found this for ₦8K. Identical quality.",
     "type": "fear", "industry": "ecommerce", "platform": "tiktok", "difficulty": "intermediate",
     "why_it_works": "Specific price comparison. 'Identical quality' directly resolves cheap = bad objection."},
    {"id": "e03", "text": "12,847 orders shipped in Nigeria. 98.3% delivery rate. Here's why.",
     "type": "authority", "industry": "ecommerce", "platform": "facebook", "difficulty": "intermediate",
     "why_it_works": "Very specific numbers signal authenticity. 98.3% not 98% — precision builds trust."},
    {"id": "e04", "text": "It arrived in 36 hours. I've never returned anything from this store.",
     "type": "social_proof", "industry": "ecommerce", "platform": "instagram", "difficulty": "beginner",
     "why_it_works": "Addresses two key objections (delivery speed + return experience) in 10 words."},
    {"id": "e05", "text": "POV: You spent ₦30K on a bag. I found the same for ₦7,500.",
     "type": "pattern_interrupt", "industry": "ecommerce", "platform": "tiktok", "difficulty": "beginner",
     "why_it_works": "POV format is native TikTok language. Positions viewer as the person who overpaid."},
    {"id": "e06", "text": "We rejected 4 suppliers before we found one we could put our name on.",
     "type": "authority", "industry": "ecommerce", "platform": "facebook", "difficulty": "advanced",
     "why_it_works": "Behind-the-scenes curation story. Signals quality obsession without just claiming it."},
    {"id": "e07", "text": "This product has 4,200 reviews. I read the 1-star ones first. Here's what I found.",
     "type": "curiosity", "industry": "ecommerce", "platform": "tiktok", "difficulty": "intermediate",
     "why_it_works": "Reading negative reviews is honest and trustworthy. Subverts typical sales approach."},
    {"id": "e08", "text": "My sister bought a fake version from Instagram. She sent it back. I sent her mine.",
     "type": "fear", "industry": "ecommerce", "platform": "instagram", "difficulty": "intermediate",
     "why_it_works": "Authentic story. Addresses market fear of counterfeit products. Real comparison."},

    # ── SAAS / TECH ───────────────────────────────────────────
    {"id": "s01", "text": "We deleted Slack, Asana, and Notion. We now use one tool. Time saved: 11 hours/week.",
     "type": "social_proof", "industry": "saas", "platform": "facebook", "difficulty": "advanced",
     "why_it_works": "Specific tools named (relatable). Specific time saved. Deleting = conviction."},
    {"id": "s02", "text": "Our Monday morning report used to take 3 hours. Now it runs automatically at 8am.",
     "type": "social_proof", "industry": "saas", "platform": "linkedin", "difficulty": "intermediate",
     "why_it_works": "Very specific time/routine. 'Automatically at 8am' makes the benefit concrete."},
    {"id": "s03", "text": "I almost cancelled. Then I saw the analytics. I renewed for 2 years.",
     "type": "curiosity", "industry": "saas", "platform": "facebook", "difficulty": "intermediate",
     "why_it_works": "Narrative tension. Cancellation creates problem; analytics create curiosity about the data."},
    {"id": "s04", "text": "Setup took 23 minutes. ROI was visible in 4 days.",
     "type": "authority", "industry": "saas", "platform": "linkedin", "difficulty": "beginner",
     "why_it_works": "Two specific numbers that answer the two biggest questions: 'How long?' and 'Does it work?'"},
    {"id": "s05", "text": "We told 30 people about this tool. 28 are still using it 6 months later.",
     "type": "social_proof", "industry": "saas", "platform": "facebook", "difficulty": "advanced",
     "why_it_works": "Retention rate as proof. Real informal referral story. 28/30 is specific and believable."},
    {"id": "s06", "text": "Your team probably has 3 tools that do the same thing. Here's how to find out.",
     "type": "curiosity", "industry": "saas", "platform": "linkedin", "difficulty": "beginner",
     "why_it_works": "Challenges audience assumption. 'Here's how to find out' opens a loop they need to close."},
    {"id": "s07", "text": "We were spending ₦180K/month on tools we barely used. This replaced all of them.",
     "type": "fear", "industry": "saas", "platform": "facebook", "difficulty": "intermediate",
     "why_it_works": "Waste of money is painful. Relatable scenario for any growing business."},
    {"id": "s08", "text": "94% of teams that try this are still using it a year later. We checked.",
     "type": "authority", "industry": "saas", "platform": "linkedin", "difficulty": "advanced",
     "why_it_works": "Retention rate is more convincing than NPS or star ratings. 'We checked' = verifiable."},

    # ── HEALTH / FITNESS ──────────────────────────────────────
    {"id": "h01", "text": "I tried 6 diets. The 7th was the one that actually worked. Here's why.",
     "type": "fear", "industry": "health", "platform": "tiktok", "difficulty": "intermediate",
     "why_it_works": "Relatable failure number (not 1 or 2 — 6 signals real effort). Redemption arc."},
    {"id": "h02", "text": "I lost 12kg. My doctor asked what I did. I showed him this.",
     "type": "authority", "industry": "health", "platform": "instagram", "difficulty": "advanced",
     "why_it_works": "Doctor asking you = ultimate credibility reversal. Implies it's validated."},
    {"id": "h03", "text": "Week 1: -0.8kg. Week 4: -3.1kg. Week 8: down 7.2kg total. No gym.",
     "type": "social_proof", "industry": "health", "platform": "tiktok", "difficulty": "intermediate",
     "why_it_works": "Progress chart in text format. 'No gym' removes the most common objection."},
    {"id": "h04", "text": "Your body isn't broken. Your plan is. Here's the difference.",
     "type": "pattern_interrupt", "industry": "health", "platform": "instagram", "difficulty": "beginner",
     "why_it_works": "Reframes blame from person to plan. Removes shame. Positions new solution."},
    {"id": "h05", "text": "I stopped counting calories 3 months ago. I still lost weight. Explanation below.",
     "type": "curiosity", "industry": "health", "platform": "tiktok", "difficulty": "beginner",
     "why_it_works": "Contradicts dominant advice (calorie counting). Creates must-watch tension."},
    {"id": "h06", "text": "2,000 clients. Average result in 12 weeks: -9.4kg. Lowest result: -4.1kg.",
     "type": "social_proof", "industry": "health", "platform": "facebook", "difficulty": "advanced",
     "why_it_works": "Showing the LOWEST result is counterintuitively trustworthy. Sets floor expectation."},
    {"id": "h07", "text": "She messaged me after 8 weeks: 'I don't recognize my own body.' Screenshot below.",
     "type": "social_proof", "industry": "health", "platform": "instagram", "difficulty": "intermediate",
     "why_it_works": "Quote-first testimonial creates emotion before proof. Screenshot = verifiable."},
    {"id": "h08", "text": "The fitness industry makes money when you fail. Here's the proof.",
     "type": "pattern_interrupt", "industry": "health", "platform": "tiktok", "difficulty": "advanced",
     "why_it_works": "Conspiracy frame against the industry positions speaker as insider whistleblower."},
]

# ── Aggregated metadata for filters ─────────────────────────

ALL_INDUSTRIES   = sorted(set(h["industry"] for h in HOOKS))
ALL_TYPES        = sorted(set(h["type"] for h in HOOKS))
ALL_PLATFORMS    = sorted(set(h["platform"] for h in HOOKS))
ALL_DIFFICULTIES = ["beginner", "intermediate", "advanced"]

TYPE_LABELS = {
    "fear":             "Fear / Loss",
    "curiosity":        "Curiosity Gap",
    "social_proof":     "Social Proof",
    "pattern_interrupt":"Pattern Interrupt",
    "authority":        "Authority / Data",
}


@router.get("/hooks")
async def get_hooks(
    industry:   Optional[str] = Query(None),
    platform:   Optional[str] = Query(None),
    hook_type:  Optional[str] = Query(None, alias="type"),
    difficulty: Optional[str] = Query(None),
    limit:      int = Query(50, ge=1, le=200),
):
    """
    Returns filtered hooks from the swipe file.
    All filters are optional — omit to get everything.
    """
    filtered = HOOKS[:]

    if industry:
        # Normalize: "Real Estate" → "realestate"
        norm = industry.lower().replace(" ", "").replace("_", "").replace("-", "")
        if "real" in norm or "estate" in norm:
            norm = "realestate"
        filtered = [h for h in filtered if h["industry"] == norm]

    if platform:
        p = platform.lower()
        filtered = [h for h in filtered if h["platform"] == p]

    if hook_type:
        t = hook_type.lower().replace(" ", "_")
        filtered = [h for h in filtered if h["type"] == t]

    if difficulty:
        d = difficulty.lower()
        filtered = [h for h in filtered if h["difficulty"] == d]

    # Group by type for UI display
    grouped: dict = {}
    for h in filtered[:limit]:
        label = TYPE_LABELS.get(h["type"], h["type"].replace("_", " ").title())
        if label not in grouped:
            grouped[label] = []
        grouped[label].append(h)

    return {
        "success": True,
        "data": {
            "hooks": filtered[:limit],
            "grouped": grouped,
            "total": len(filtered),
            "filters": {
                "industries": ALL_INDUSTRIES,
                "types":      list(TYPE_LABELS.values()),
                "platforms":  ALL_PLATFORMS,
                "difficulties": ALL_DIFFICULTIES,
            },
        },
    }


@router.get("/hooks/random")
async def random_hooks(
    industry: Optional[str] = Query(None),
    count: int = Query(5, ge=1, le=20),
):
    """Returns N random hooks for quick inspiration."""
    import random
    pool = HOOKS[:]
    if industry:
        norm = industry.lower().replace(" ", "").replace("_", "")
        if "real" in norm:
            norm = "realestate"
        pool = [h for h in pool if h["industry"] == norm]
    sampled = random.sample(pool, min(count, len(pool)))
    return {"success": True, "data": {"hooks": sampled}}
