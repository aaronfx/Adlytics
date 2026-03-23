"""
ADLYTICS v6.1 - INDUSTRY-AWARE analyze.py
Fixes: industry-blind generators, timecode placeholders, demographic duplication,
CTA extraction bug, neuro tie-break, uniform persona pain points.
"""

from fastapi import APIRouter, Form, HTTPException
from typing import Optional
import traceback
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

try:
    from backend.services.ai_engine import get_ai_engine, AIValidationError
    ai_engine = get_ai_engine()
    logger.info("✅ AI Engine loaded")
except Exception as e:
    logger.error(f"❌ AI Engine error: {e}")
    ai_engine = None


# ─────────────────────────────────────────────
# INDUSTRY CONFIGURATION — the single source of truth
# for all industry-specific text throughout the file
# ─────────────────────────────────────────────

INDUSTRY_CONFIG = {
    "realestate": {
        "label": "Real Estate",
        "proof_type": "verified title documents, site photos, completed project images, floor plan",
        "proof_example": "Show C of O, survey plan, and a completed unit photo with price breakdown",
        "compliance_risk": "Real estate promotion without registered agent / developer disclosure",
        "compliance_platform": "TikTok / Instagram / Facebook",
        "compliance_fix": (
            "Add ESVARBON or LASRERA registration number. "
            "Include 'Subject to availability. Terms & Conditions apply.'"
        ),
        "variant_hooks": [
            "Most people rent for 20 years and never own anything. Here's what changes that...",
            "Lagos property prices increased 300% in 10 years. Are you on the wrong side?",
            "I bought my first property at 28 with a ₦500K down payment. Here's exactly how...",
        ],
        "variant_bodies": [
            (
                "Rent is dead money. Every payment funds your landlord's retirement, not yours. "
                "We have verified properties in [location] with flexible payment plans starting from ₦X. "
                "Full documentation included — C of O, survey plan, approved building plan."
            ),
            (
                "While inflation erodes bank savings, Lagos real estate has consistently outpaced it. "
                "Our properties come with verified title, no hidden fees, and a dedicated after-sales team."
            ),
            (
                "You don't need millions upfront. Our instalment plan lets you secure your plot today "
                "and pay over 12–36 months. Fully documented, government-approved location."
            ),
        ],
        "variant_ctas": [
            "Book a free site inspection this weekend — no pressure, just clarity.",
            "DM 'PROPERTY' and we'll send the full price list, payment plan, and documents.",
            "Tap the link in bio for the full breakdown. No commitment required.",
        ],
        "persona_pain": {
            "young":      ["Can't afford rent in Lagos", "Dreams of owning before 30", "Worried about land fraud"],
            "professional":["Wants property that beats inflation", "Unsure which areas have strong ROI", "Needs trusted developer"],
            "core":       ["Rising rent is draining savings", "Has been shown fake land documents before", "Needs flexible payment plan"],
            "compliance": ["Undisclosed agent fees", "Off-plan completion risk", "Title verification gaps"],
            "buyer":      ["Wants verified C of O before committing", "Needs clear exit strategy", "Compares yield across developers"],
        },
        "persona_obj": {
            "young":      ["I can't afford the down payment yet", "What if it's land fraud?"],
            "professional":["Is the title fully registered?", "What's the 5-year ROI projection?"],
            "core":       ["How do I know the documents are real?", "What are the full payment terms?"],
            "compliance": ["Is this registered with LASRERA/CAC?", "Are agency fees disclosed upfront?"],
            "buyer":      ["Show me the C of O first", "What happens if the project isn't completed?"],
        },
    },

    "finance": {
        "label": "Finance / Forex",
        "proof_type": "live trade screenshots, account P&L statements, recorded trade walkthroughs",
        "proof_example": "Show a specific trade: 'EUR/USD, 14 March, +12.4% in 4 hours' with account screenshot",
        "compliance_risk": "Financial promotion without risk disclaimer",
        "compliance_platform": "TikTok / Meta",
        "compliance_fix": "Add 'Trading involves risk. Capital at risk.' to caption and on end card.",
        "variant_hooks": [
            "I lost ₦120,000 in 3 days before I discovered this one rule...",
            "Nobody shows you the losing trades. I do. Here's why that matters...",
            "Stop following random signals. Here's the framework that actually works...",
        ],
        "variant_bodies": [
            (
                "Most traders blow their account in the first 3 months — not because the market is hard, "
                "but because they skip risk management. I track every trade, win or loss. "
                "The pattern became obvious after month 2."
            ),
            (
                "Gurus show you the wins. They hide the failed setups and bad days. "
                "I started recording both — and the strategy that emerged is consistent and repeatable."
            ),
            (
                "I've documented 6 months of live trades. When you follow the rules strictly, "
                "the results are predictable. No prediction, no gambling — just a documented process."
            ),
        ],
        "variant_ctas": [
            "Watch how I analyse trades BEFORE entering. No sales pitch.",
            "See the pattern they don't want you to notice. Free walkthrough inside.",
            "Don't sign up for anything yet. Just watch this first.",
        ],
        "persona_pain": {
            "young":      ["Lost money on random signals", "Wants income from phone", "Distrusts online 'gurus'"],
            "professional":["Salary not keeping up with inflation", "Wants passive income stream", "Skeptical of online finance"],
            "core":       ["Has tried other courses that didn't work", "Needs proof before paying", "Wants a repeatable system"],
            "compliance": ["Regulatory compliance", "Consumer protection concerns"],
            "buyer":      ["Wants verified track record", "Values ROI over inspiration", "Compares against other programmes"],
        },
        "persona_obj": {
            "young":      ["Is this another scam?", "I have nothing to invest with yet"],
            "professional":["Where is the documented proof?", "Is this FCA/SEC regulated?"],
            "core":       ["I've bought courses before and failed", "How long until I see results?"],
            "compliance": ["No FCA disclaimer visible", "Profit claims are unverified"],
            "buyer":      ["What is the all-in cost?", "Can I see 3 months of verified results?"],
        },
    },

    "ecommerce": {
        "label": "E-commerce",
        "proof_type": "real customer reviews, unboxing videos, before/after photos, delivery proof",
        "proof_example": "Show 3 genuine customer reviews with photos and a delivery confirmation screenshot",
        "compliance_risk": "Product claims without substantiation or missing return policy",
        "compliance_platform": "TikTok / Instagram",
        "compliance_fix": "Add 'Results may vary. T&Cs apply.' Ensure return/refund policy is linked.",
        "variant_hooks": [
            "I ordered this 3 times because people kept asking where I got it...",
            "Why are 10,000 Nigerians buying this every week? I found out...",
            "This changed my daily routine — and it costs less than your lunch...",
        ],
        "variant_bodies": [
            (
                "Premium quality delivered to your door in 48 hours. "
                "Over 50,000 customers across Nigeria with a 4.8-star rating. "
                "Every order ships with a 30-day satisfaction guarantee."
            ),
            (
                "No middlemen. No fake products. We import directly so you get authentic quality at a fair price. "
                "Secure payment, tracked delivery, and easy returns if anything goes wrong."
            ),
            (
                "Limited stock — once it's gone, it's gone. "
                "Thousands of verified reviews from real customers who reorder every month."
            ),
        ],
        "variant_ctas": [
            "Order now — free delivery on orders over ₦15,000. Stock is limited.",
            "DM 'ORDER' to reserve yours before it sells out today.",
            "Tap the link in bio. Checkout takes under 2 minutes.",
        ],
        "persona_pain": {
            "young":      ["Tired of low-quality products", "Wants fast, reliable delivery", "Price-conscious but quality-aware"],
            "professional":["Needs reliable supplier for regular orders", "Wants authentic products, not replicas", "Values convenience and speed"],
            "core":       ["Has been sent wrong/fake products before", "Wants value for money, not just cheap price", "Compares across multiple vendors"],
            "compliance": ["Return policy unclear", "Consumer protection rights not stated"],
            "buyer":      ["Wants detailed product specs before buying", "Needs verified reviews, not planted ones", "Checks for warranty information"],
        },
        "persona_obj": {
            "young":      ["Will it actually arrive?", "Is this the real version or a fake?"],
            "professional":["What is the return policy if it's wrong?", "How long does shipping take?"],
            "core":       ["I've been scammed by online shops before", "Is the price too low to be real?"],
            "compliance": ["Are consumer rights protected here?", "Is there a warranty?"],
            "buyer":      ["Show me real customer reviews with photos", "What if the size / spec doesn't match?"],
        },
    },

    "saas": {
        "label": "SaaS / Tech",
        "proof_type": "metrics dashboards, customer case studies, before/after workflow screenshots",
        "proof_example": "Show a specific result: 'Team X reduced reporting time from 4 hours to 12 minutes'",
        "compliance_risk": "Software performance claims without supporting data",
        "compliance_platform": "LinkedIn / Google Ads",
        "compliance_fix": "Add 'Results based on customer data. Individual results may vary.'",
        "variant_hooks": [
            "Our team saved 15 hours per week after switching to this — here's how...",
            "I almost cancelled the subscription until I saw what this tool actually does...",
            "The spreadsheet era is over. Here's what 10,000 teams use instead...",
        ],
        "variant_bodies": [
            (
                "Manual reporting was costing us 3 hours every Monday morning. "
                "Now it runs automatically at 8am with zero configuration after setup."
            ),
            (
                "We integrated with Slack, Notion, and our CRM in under 30 minutes. "
                "Full team adoption in under a week. ROI visible by day 10."
            ),
            (
                "1,200 companies switched in the last 6 months. "
                "Average time-to-value: 4 days. Average team adoption rate: 94%."
            ),
        ],
        "variant_ctas": [
            "Start free — no credit card required. See results in 10 minutes.",
            "Book a 15-min demo. We'll show you exactly what it saves you.",
            "Try free for 14 days. Cancel any time, no questions asked.",
        ],
        "persona_pain": {
            "young":      ["Wasting hours on manual tasks", "Can't afford enterprise tools yet", "Wants automation without coding"],
            "professional":["Team collaboration is chaotic", "Current tools don't integrate", "Admin is eating billable hours"],
            "core":       ["Has tried 3 tools that didn't stick", "Needs clear ROI before committing", "Worried about onboarding complexity"],
            "compliance": ["Data privacy and sovereignty concerns", "GDPR / SOC2 requirements"],
            "buyer":      ["Needs to justify cost to management", "Wants enterprise security", "Compares feature lists obsessively"],
        },
        "persona_obj": {
            "young":      ["Is there a free plan?", "How long does setup take?"],
            "professional":["Will my team actually use this?", "Does it integrate with our existing stack?"],
            "core":       ["We tried something similar before and it failed", "What does onboarding support look like?"],
            "compliance": ["Where is our data stored?", "Is this GDPR / SOC2 compliant?"],
            "buyer":      ["What is the total cost of ownership?", "Can I see a relevant case study?"],
        },
    },

    "health": {
        "label": "Health / Fitness",
        "proof_type": "before/after photos with dates, progress measurements, client testimonials",
        "proof_example": "Show a real transformation: 'Client A, -12kg in 8 weeks' with dated photo",
        "compliance_risk": "Health / weight loss claims without clinical disclaimer",
        "compliance_platform": "TikTok / Instagram / Facebook",
        "compliance_fix": "Add 'Results not typical. Consult a health professional before starting any programme.'",
        "variant_hooks": [
            "I tried 6 diets before this one actually worked. Here's the difference...",
            "Nobody talks about why most fitness plans fail by week 3...",
            "I lost 15kg in 10 weeks without cutting out my favourite foods. Here's how...",
        ],
        "variant_bodies": [
            (
                "Most plans fail because they're built for ideal conditions, not real life. "
                "This programme adapts to your schedule, your food preferences, and your starting point."
            ),
            (
                "We've helped 2,000 people in Nigeria achieve sustainable weight loss without crash diets. "
                "No supplements, no expensive equipment — just a repeatable daily system."
            ),
            (
                "The results come from understanding why your body holds onto weight — not just cutting calories. "
                "Once you fix the root cause, the results are consistent and lasting."
            ),
        ],
        "variant_ctas": [
            "Get your free personalised plan — takes 2 minutes to complete.",
            "DM 'START' and we'll send your assessment today.",
            "Join 2,000 others who transformed in 90 days. Free trial available.",
        ],
        "persona_pain": {
            "young":      ["Tried multiple diets with no lasting results", "Self-conscious about body", "Wants quick visible changes"],
            "professional":["No time for long gym sessions", "Stress eating from work pressure", "Wants sustainable, low-effort approach"],
            "core":       ["Failed programmes before due to unrealistic demands", "Needs accountability and community", "Wants to see results within 4 weeks"],
            "compliance": ["Misleading before/after imagery", "Unrealistic weight loss timelines"],
            "buyer":      ["Wants clinical or scientific backing", "Needs customised approach, not generic", "Compares testimonials carefully"],
        },
        "persona_obj": {
            "young":      ["I've tried this type of thing before", "Can I actually see results that fast?"],
            "professional":["I don't have time for a complex programme", "Is this actually sustainable long-term?"],
            "core":       ["I've been disappointed by programmes like this before", "What makes this different from the others?"],
            "compliance": ["Are the before/after photos real and unedited?", "Is this medically safe?"],
            "buyer":      ["Show me peer-reviewed evidence or clinical data", "What is the refund policy if it doesn't work?"],
        },
    },
}

def _resolve_industry(industry: str) -> dict:
    """Map any industry string to its config dict."""
    s = industry.lower().replace(" ", "").replace("-", "").replace("_", "")
    if any(x in s for x in ["real", "estate", "property", "propert", "housing"]):
        return INDUSTRY_CONFIG["realestate"]
    if any(x in s for x in ["ecom", "shop", "retail", "commerce", "store"]):
        return INDUSTRY_CONFIG["ecommerce"]
    if any(x in s for x in ["saas", "software", "tech", "app", "platform"]):
        return INDUSTRY_CONFIG["saas"]
    if any(x in s for x in ["health", "fit", "wellness", "nutrition", "gym", "weight"]):
        return INDUSTRY_CONFIG["health"]
    return INDUSTRY_CONFIG["finance"]


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def safe_score(scores: dict, key: str, default: int = 50) -> int:
    v = scores.get(key, default)
    return default if (v is None or v == 0) else int(v)


def _split_sentences(text: str) -> list:
    """Split text into sentences, stripping empties."""
    import re
    parts = re.split(r'[.!?]+', text)
    return [p.strip() for p in parts if p.strip() and len(p.strip()) > 3]


def _extract_cta(content: str) -> str:
    """
    Extract the CTA from the last sentence.
    Falls back to a clear message rather than a single word.
    """
    sentences = _split_sentences(content)
    if not sentences:
        return "No explicit CTA detected"
    last = sentences[-1]
    # If the last sentence is only 1–2 words it's not a real CTA
    if len(last.split()) <= 2:
        return f"Implicit ending: '{last}' — no dedicated CTA"
    return last[:100]


# ─────────────────────────────────────────────
# GENERATORS (all receive industry config)
# ─────────────────────────────────────────────

def gen_decision_engine(scores: dict, summary: str) -> dict:
    overall = safe_score(scores, "overall")
    should_run = overall >= 60
    confidence = min(95, overall + 10)
    return {
        "should_run": should_run,
        "reasoning": summary or (
            f"Score of {overall}/100. " +
            ("Strong enough to deploy with a small test budget." if should_run
             else "Needs revision before spending on media.")
        ),
        "confidence": f"{confidence}%",
        "expected_profit": overall * 180,
        "roi_prediction": f"{overall / 35:.1f}x",
        "profit_scenarios": {
            "low_case": max(0, overall * 40),
            "base_case": overall * 130,
            "high_case": overall * 280,
        },
        "kill_threshold": (
            f"Kill if CPM exceeds ${round(overall * 0.3, 2)} after 48 hours with no conversions."
        ),
        "scale_threshold": (
            f"Scale to 2× budget when ROAS ≥ {round(overall / 35, 1)}× and CPA is below target."
        ),
        "confidence_breakdown": {
            "data_confidence": min(95, overall + 20),
            "market_fit": safe_score(scores, "audience_match"),
            "execution": safe_score(scores, "platform_fit"),
        },
    }


def gen_budget_optimization(scores: dict) -> dict:
    overall = safe_score(scores, "overall")
    if overall >= 70:
        phases = [
            "Phase 1 (Days 1–3) – Validation: $50/day. Goal: confirm CTR & CPM.",
            "Phase 2 (Days 4–10) – Learning: $100/day. Goal: lower CPA via optimisation.",
            "Phase 3 (Days 11–24) – Scaling: $300/day. Goal: maximise ROAS.",
        ]
        risk, worst = "Low", 500
    else:
        phases = [
            "Phase 1 (Days 1–5) – Validation: $30/day. Goal: identify weak points.",
            "Phase 2 (Days 6–12) – Optimisation: $50/day. Goal: fix identified gaps.",
        ]
        risk = "Medium" if overall >= 55 else "High"
        worst = 1200 if overall >= 50 else 2500

    tip = (
        "Start with a 3-day $30/day test. Kill if CPA exceeds your target by day 2."
        if overall < 60 else
        "Strong score — run $100/day for 7 days to build algorithm confidence before scaling."
    )
    return {
        "break_even_cpc": round(overall * 0.035, 2),
        "safe_test_budget": 1500 if overall >= 70 else 800,
        "days_to_profit": 5 if overall >= 70 else 10,
        "scaling_rule": f"Double budget every 7 days when ROAS ≥ {round(overall / 35, 1)}×.",
        "risk_level": risk,
        "worst_case_loss": worst,
        "budget_tip": tip,
        "budget_phases": phases,
    }


def gen_neuro_response(scores: dict, content: str, ind: dict) -> dict:
    hook = safe_score(scores, "hook_strength")
    cred = safe_score(scores, "credibility")
    emo = safe_score(scores, "emotional_pull")
    content_lower = content.lower()

    dopamine = min(100, hook + 10)
    fear = max(10, 100 - cred)
    curiosity = min(100, hook + 5)

    # Proper tie-breaking: if all within 5, primary = curiosity (most commonly actionable)
    drivers = {"dopamine": dopamine, "fear": fear, "curiosity": curiosity}
    spread = max(drivers.values()) - min(drivers.values())
    if spread <= 5:
        primary = "curiosity"
    else:
        primary = max(drivers, key=drivers.get)

    # Industry-aware triggers
    triggers = []
    label = ind["label"].lower()
    if "real estate" in label or "property" in label:
        if "rent" in content_lower or "buy" in content_lower or "house" in content_lower:
            triggers.append("Ownership aspiration — desire to escape the rental cycle")
        if emo >= 60:
            triggers.append("Fear of missing appreciation window — FOMO on property value growth")
        if not triggers:
            triggers = ["Aspiration trigger — desire for stable asset ownership",
                        "Status signal — homeownership as life milestone"]
    elif "finance" in label or "forex" in label:
        if "lost" in content_lower or "fail" in content_lower:
            triggers.append("Fear of loss (FOMO) — very high activation in Nigerian market")
        if "truth" in content_lower or "honest" in content_lower:
            triggers.append("Curiosity gap — 'what are they hiding from me?'")
        if not triggers:
            triggers = ["Financial aspiration — desire for income beyond salary",
                        "Social proof potential — others achieving similar results"]
    elif "ecom" in label:
        triggers = ["Desire trigger — product as identity/status expression",
                    "FOMO — limited stock urgency"]
    elif "saas" in label or "tech" in label:
        triggers = ["Efficiency aspiration — desire to reclaim wasted hours",
                    "Fear of falling behind competitors who use better tools"]
    else:
        triggers = ["Aspiration trigger detected", "Social proof potential identified"]

    # Psychological gaps
    gaps = []
    if cred < 60:
        gaps.append("Credibility gap — no proof or social validation shown")
    if emo < 50:
        gaps.append("Emotional distance — content feels informational, not personal")
    if hook < 55:
        gaps.append("Pattern interrupt missing — content blends in with feed noise")
    if not gaps:
        gaps = ["Minor authority gap — one more credibility signal would strengthen trust"]

    return {
        "dopamine": dopamine,
        "fear": fear,
        "curiosity": curiosity,
        "primary_driver": primary,
        "emotional_triggers": triggers,
        "psychological_gaps": gaps,
    }


def gen_ad_variants(content: str, scores: dict, ind: dict) -> list:
    """Industry-aware variants."""
    overall = safe_score(scores, "overall")
    hooks = ind["variant_hooks"]
    bodies = ind["variant_bodies"]
    ctas = ind["variant_ctas"]

    return [
        {
            "id": 1,
            "angle": "Fear / Loss",
            "hook": hooks[0],
            "body": bodies[0],
            "cta": ctas[0],
            "why_it_works": (
                f"Loss/risk framing activates fear of missing out. "
                f"For {ind['label']} ads, this is the highest-converting emotional driver."
            ),
            "predicted_score": min(100, overall + 12),
        },
        {
            "id": 2,
            "angle": "Curiosity Gap",
            "hook": hooks[1],
            "body": bodies[1],
            "cta": ctas[1],
            "why_it_works": (
                "Open loop creates irresistible need to close the information gap. "
                "Audience must click to resolve the tension."
            ),
            "predicted_score": min(100, overall + 8),
        },
        {
            "id": 3,
            "angle": "Social Proof",
            "hook": hooks[2],
            "body": bodies[2],
            "cta": ctas[2],
            "why_it_works": (
                "Third-party validation reduces purchase anxiety. "
                "Specificity (numbers, names, dates) amplifies believability."
            ),
            "predicted_score": min(100, overall + 5),
        },
    ]


def gen_winner_prediction(scores: dict, ind: dict) -> dict:
    overall = safe_score(scores, "overall")
    label = ind["label"]
    if overall >= 70:
        return {
            "winner_id": 2,
            "angle": "Curiosity Gap",
            "confidence": "72%",
            "reasoning": (
                f"Curiosity gap consistently outperforms fear framing in "
                f"{label} markets with educated 25–34 audiences. "
                "It avoids alarm-fatigue while maintaining emotional tension."
            ),
        }
    return {
        "winner_id": 1,
        "angle": "Fear / Loss",
        "confidence": "65%",
        "reasoning": (
            f"Current {label} ad needs a stronger hook. "
            "Fear/loss framing is most likely to stop the scroll "
            "and drive click-through for this audience and score range."
        ),
    }


def gen_objection_detection(scores: dict, content: str, ind: dict) -> dict:
    cred = safe_score(scores, "credibility")
    content_lower = content.lower()
    proof_example = ind["proof_example"]

    scam_triggers = []
    if any(p in content_lower for p in ["guarantee", "guaranteed", "risk free", "no experience"]):
        scam_triggers.append({
            "severity": "High",
            "trigger": "Guarantee language detected — raises 'too good to be true' alarm",
            "fix": "Replace with 'track record' or 'documented results' framing",
        })
    if any(p in content_lower for p in ["10x", "500k", "turn", "into", "overnight"]):
        scam_triggers.append({
            "severity": "High",
            "trigger": "Unrealistic return / transformation claim detected",
            "fix": f"Show a realistic, specific result with context. {proof_example}",
        })
    if not scam_triggers:
        scam_triggers.append({
            "severity": "Low",
            "trigger": "No obvious scam triggers — maintain this clarity",
            "fix": "Continue leading with transparency and specific proof",
        })

    trust_gaps = []
    if cred < 70:
        trust_gaps.append({
            "severity": "High",
            "gap": "No proof shown — verification or results evidence missing",
            "impact": f"Reduces conversion by up to 60% in skeptical markets",
            "fix": proof_example,
        })
    trust_gaps.append({
        "severity": "Medium",
        "gap": "No social proof or third-party validation mentioned",
        "impact": "Audience relies heavily on trust signals — missing testimonials reduce confidence",
        "fix": "Add one real customer result or testimonial with name, date, and specific outcome",
    })

    compliance_risks = [
        {
            "risk": ind["compliance_risk"],
            "platform": ind["compliance_platform"],
            "fix": ind["compliance_fix"],
        }
    ]

    return {
        "scam_triggers": scam_triggers,
        "trust_gaps": trust_gaps,
        "compliance_risks": compliance_risks,
    }


def gen_creative_fatigue(scores: dict) -> dict:
    overall = safe_score(scores, "overall")
    if overall >= 75:
        level, days, refresh = "Low", 21, False
        explanation = (
            "High-quality content with strong hook novelty. "
            "Expect stable CTR for 3+ weeks before needing a refresh."
        )
        recs = [
            "Monitor frequency cap — pause if any user sees the ad more than 4× per week",
            "At day 14, test a new hook while keeping the body identical",
            "Rotate thumbnail or opening frame at day 21 to reset fatigue clock",
        ]
    elif overall >= 55:
        level, days, refresh = "Medium", 12, True
        explanation = (
            "Moderate novelty score. Audience will begin pattern-matching "
            "this style within 1–2 weeks. Plan a hook refresh before that."
        )
        recs = [
            "Prepare 2 alternate hooks now — swap at day 7",
            "Test a different opening emotion (curiosity vs fear)",
            "Change thumbnail colour or text overlay at day 10",
        ]
    else:
        level, days, refresh = "High", 5, True
        explanation = (
            "Weak hook makes the ad feel identical to dozens of others in this niche. "
            "Audience will scroll past rapidly — fatigue accelerates."
        )
        recs = [
            "Rebuild hook before launch — current version will fatigue in under a week",
            "Use a pattern interrupt: start mid-sentence or with a direct question",
            "Test UGC format instead of polished video — feels more authentic",
        ]
    return {
        "fatigue_level": level,
        "estimated_decline_days": days,
        "explanation": explanation,
        "refresh_needed": refresh,
        "refresh_recommendations": recs,
    }


def gen_cross_platform(scores: dict, content: str) -> dict:
    overall = safe_score(scores, "overall")
    words = content.split()
    short_hook = " ".join(words[:10]) + "..." if len(words) >= 10 else content[:60]
    return {
        "tiktok": {
            "score": overall,
            "adapted_copy": f"{short_hook} [Add text overlay at 0–3s for silent viewers]",
            "changes_needed": "Add captions. Keep under 45s. Hook must land in first 2s.",
        },
        "instagram": {
            "score": max(0, overall - 3),
            "adapted_copy": f"{short_hook} [Reformat for 9:16 Reels. Add trending audio bed.]",
            "changes_needed": "Increase visual quality. Add trending audio. Caption in first comment.",
        },
        "facebook": {
            "score": min(100, overall + 5),
            "adapted_copy": (
                f"{short_hook}\n\n"
                "Here's what most people in this space won't tell you... [expand for News Feed]"
            ),
            "changes_needed": "Longer copy works well on Facebook. Add 'Learn More' button. Target 30–50 age group.",
        },
        "youtube": {
            "score": min(100, overall + 8),
            "adapted_copy": f"[YouTube Shorts] {short_hook} — full breakdown in comments.",
            "changes_needed": "Extend to 60s for Shorts. Pin comment with link. Use chapter markers.",
        },
    }


def gen_video_execution(scores: dict, content: str) -> dict:
    hook = safe_score(scores, "hook_strength")
    clarity = safe_score(scores, "clarity")

    sentences = _split_sentences(content)
    total = len(sentences)

    def _seg_text(idx: int, fallback_note: str) -> str:
        """Return actual sentence or a directive note — never a raw placeholder."""
        if idx < total:
            return sentences[idx][:100]
        return fallback_note

    timecodes = [
        {
            "segment": "Hook",
            "timestamp": "0–3s",
            "content": _seg_text(0, "⚠ No hook content provided — write a pattern interrupt here"),
            "quality": "strong" if hook >= 70 else "neutral",
        },
        {
            "segment": "Body / Story",
            "timestamp": "3–15s",
            "content": _seg_text(1, "⚠ No body content provided — add your story or key benefit here"),
            "quality": "neutral",
        },
        {
            "segment": "Proof / Credibility",
            "timestamp": "15–28s",
            "content": _seg_text(2, "⚠ No proof section provided — insert testimonial or result here"),
            "quality": "neutral",
        },
        {
            "segment": "CTA",
            "timestamp": "28–35s",
            "content": _seg_text(3, "⚠ No CTA provided — tell viewer exactly what to do next"),
            "quality": "strong",
        },
    ]

    return {
        "hook_delivery": min(100, hook + 5),
        "speech_flow": max(0, clarity - 5),
        "visual_dependency": 55,
        "recommended_format": (
            "Talking head with text overlays"
            if hook >= 70 else "UGC / phone-recorded for authenticity"
        ),
        "delivery_risk": (
            "Low — script flows naturally"
            if clarity >= 65 else "Medium — pacing needs to be tighter in editing"
        ),
        "timecode_breakdown": timecodes,
    }


def gen_persona_reactions(scores: dict, content: str, ind: dict) -> list:
    """Industry-aware personas with unique pain points and objections per card."""
    overall = safe_score(scores, "overall")
    high = overall >= 70
    pp = ind["persona_pain"]
    ob = ind["persona_obj"]

    def conv(base_high, base_low):
        return base_high if high else base_low

    return [
        {
            "name": "19yo Lagos Scroller",
            "demographic": "Male, Lagos Island, Student / side-hustler",
            "conversion_likelihood": conv("65%", "25%"),
            "reaction": conv(
                "Stops scrolling and watches the full video",
                "Scrolls past — doesn't feel personally relevant yet"
            ),
            "pain_points": pp["young"],
            "objections": ob["young"],
        },
        {
            "name": "38yo Abuja Professional",
            "demographic": "Female, Abuja, Civil servant / SME owner",
            "conversion_likelihood": conv("52%", "18%"),
            "reaction": conv(
                "Reads carefully, checks profile before clicking",
                "Dismisses quickly — needs more credibility signals"
            ),
            "pain_points": pp["professional"],
            "objections": ob["professional"],
        },
        {
            "name": "25–34 Core Target",
            "demographic": "Mixed gender, educated, income-frustrated",
            "conversion_likelihood": conv("70%", "30%"),
            "reaction": conv(
                "Resonates immediately. Clicks to learn more.",
                "Interested but unconvinced — needs one more trust signal"
            ),
            "pain_points": pp["core"],
            "objections": ob["core"],
        },
        {
            "name": "UK Compliance Officer",
            "demographic": "52yo male, London, Financial services background",
            "conversion_likelihood": conv("14%", "4%"),
            "reaction": conv(
                "Notes good disclosure practices — cautiously interested",
                "Flags regulatory concerns — would not click without disclaimers"
            ),
            "pain_points": pp["compliance"],
            "objections": ob["compliance"],
        },
        {
            "name": "US Direct-Response Buyer",
            "demographic": "35–45, online business owner, high purchase intent",
            "conversion_likelihood": conv("45%", "20%"),
            "reaction": conv(
                "Evaluates CTA carefully. Clicks if offer is clear.",
                "Drops off — CTA is too vague for action"
            ),
            "pain_points": pp["buyer"],
            "objections": ob["buyer"],
        },
    ]


def gen_line_by_line(content: str, scores: dict) -> list:
    sentences = _split_sentences(content)
    if not sentences:
        return []

    hook_score = safe_score(scores, "hook_strength")
    clarity = safe_score(scores, "clarity")
    cta_score = safe_score(scores, "cta_strength")
    results = []

    for i, sentence in enumerate(sentences[:8]):
        if i == 0:
            strength = round(hook_score / 10)
            issue = "Weak hook — no pattern interrupt" if hook_score < 60 else None
            suggestion = "Open with a specific number, loss, or question for +40% hook rate" if hook_score < 60 else None
        elif i == len(sentences) - 1:
            strength = round(cta_score / 10)
            issue = "CTA is vague — doesn't specify the next step" if cta_score < 60 else None
            suggestion = "End with a specific action: 'DM us X' or 'Tap the link in bio'" if cta_score < 60 else None
        else:
            strength = min(9, max(3, round(clarity / 10) + (i % 3 - 1)))
            issue = None
            suggestion = None

        results.append({
            "line_number": i + 1,
            "text": sentence[:120],
            "strength": strength,
            "assessment": "strong" if strength >= 7 else "weak" if strength <= 4 else "neutral",
            "issue": issue,
            "suggestion": suggestion,
        })
    return results


def gen_phase_breakdown(content: str, scores: dict) -> dict:
    """
    Split content into phases. Never shows '...' or single-word CTA.
    Uses directive text when content is too short to fill a phase.
    """
    sentences = _split_sentences(content)
    total = len(sentences)
    hook_score = safe_score(scores, "hook_strength")
    clarity = safe_score(scores, "clarity")
    cta_score = safe_score(scores, "cta_strength")

    # Hook = first sentence
    hook_text = sentences[0][:60] if total >= 1 else "⚠ No hook content"
    hook_verdict = "Strong opening — stops the scroll." if hook_score >= 70 else "Weak opening — needs pattern interrupt."

    # Body = middle sentence(s)
    if total >= 3:
        body_text = sentences[1][:60]
        body_verdict = "Clear delivery with logical flow." if clarity >= 65 else "Body is unclear or too long — tighten."
    elif total == 2:
        body_text = sentences[1][:60]
        body_verdict = "Content is too short to have a proper body section. Add 2–3 sentences explaining the benefit."
    else:
        body_text = "⚠ No body content"
        body_verdict = "No body content provided. Add a story, proof point, or benefit statement."

    # CTA = last sentence (only if it's genuinely a CTA, not a 1-word tail)
    cta_raw = _extract_cta(content)
    cta_verdict = "Compelling close." if cta_score >= 65 else "Weak CTA — be specific about the next step."

    return {
        "hook_phase": f"[Score: {hook_score}/100] \"{hook_text}...\" {hook_verdict}",
        "body_phase": f"[Score: {clarity}/100] \"{body_text}...\" {body_verdict}",
        "cta_phase": f"[Score: {cta_score}/100] \"{cta_raw}\" {cta_verdict}",
    }


def gen_improvements(scores: dict, ind: dict) -> list:
    """Industry-aware improvement suggestions."""
    items = []
    proof_example = ind["proof_example"]
    hooks = ind["variant_hooks"]

    if safe_score(scores, "hook_strength") < 70:
        items.append({
            "priority": "HIGH",
            "change": "Rewrite hook with a specific result or pattern interrupt",
            "expected_impact": "+35–45% watch time in first 3 seconds",
            "implementation": f"Try: '{hooks[0]}'",
        })
    if safe_score(scores, "credibility") < 65:
        items.append({
            "priority": "HIGH",
            "change": "Add one piece of verifiable proof",
            "expected_impact": "+25–40% conversion rate",
            "implementation": proof_example,
        })
    if safe_score(scores, "cta_strength") < 65:
        items.append({
            "priority": "MEDIUM",
            "change": "Replace generic or missing CTA with a specific action",
            "expected_impact": "+15% click-through rate",
            "implementation": f"End with: '{ind['variant_ctas'][0]}'",
        })
    if safe_score(scores, "emotional_pull") < 55:
        items.append({
            "priority": "MEDIUM",
            "change": "Add a personal story or relatable pain point",
            "expected_impact": "+20% audience retention past the 5-second mark",
            "implementation": f"Lead with the audience's frustration before presenting the solution.",
        })
    if not items:
        items.append({
            "priority": "LOW",
            "change": "A/B test hook phrasing with one alternate opening",
            "expected_impact": "+8–12% overall performance",
            "implementation": f"Test: '{hooks[1]}' against current hook over 3 days",
        })
    return items


def gen_roi_comparison(scores: dict) -> dict:
    overall = safe_score(scores, "overall")
    roas = round(overall / 35, 1)
    return {
        "current_projection": f"{roas}× ROAS",
        "industry_average": "1.5× ROAS",
        "top_performer_benchmark": "4.2× ROAS",
        "gap_analysis": (
            f"Projected {roas}× ROAS is "
            + ("above industry average — good foundation for scaling." if roas >= 1.5
               else "below industry average — needs optimisation before media spend increases.")
            + " Top performers in this category average 4× ROAS with strong hook + credibility scores."
        ),
    }


def gen_competitor_advantage(scores: dict, content: str, ind: dict) -> dict:
    cred = safe_score(scores, "credibility")
    content_lower = content.lower()
    label = ind["label"]

    unique_angles = []
    if cred >= 70:
        unique_angles.append(f"Transparency-first positioning — rare in the {label} niche")
    if len(content.split()) > 30:
        unique_angles.append("Detailed content signals depth of expertise vs surface-level competitors")
    if not unique_angles:
        unique_angles = [f"Educational angle differentiates from pure 'buy now' offers in {label}"]

    return {
        "unique_angles": unique_angles,
        "defensible_moat": (
            "Authentic voice + specific proof is hard to copy quickly. "
            "If real results are shown and documented, this becomes a durable competitive advantage."
        ),
        "vulnerability": (
            f"Any competitor who shows a more transparent and specific {label} story "
            "with verified proof will immediately challenge this positioning."
        ),
    }


def gen_behavior_summary(scores: dict, ai_summary: str) -> str:
    if ai_summary and len(ai_summary) > 20:
        return ai_summary
    overall = safe_score(scores, "overall")
    hook = safe_score(scores, "hook_strength")
    cred = safe_score(scores, "credibility")
    return (
        f"This ad scores {overall}/100 overall. "
        f"Hook strength is {hook}/100 — "
        + ("strong enough to stop the scroll. " if hook >= 70 else "not strong enough to stop the scroll. ")
        + f"Credibility is {cred}/100 — "
        + ("audience is likely to trust the message. " if cred >= 65
           else "audience will be skeptical without more proof. ")
        + ("Overall, this ad is ready for a test budget." if overall >= 65
           else "Revisions are recommended before spending on media.")
    )


# ─────────────────────────────────────────────
# MAIN ENDPOINT
# ─────────────────────────────────────────────

@router.post("/analyze")
async def analyze_endpoint(
    ad_copy: Optional[str] = Form(None),
    video_script: Optional[str] = Form(None),
    platform: str = Form("tiktok"),
    industry: str = Form("finance"),
    audience_country: str = Form("nigeria"),
    audience_age: str = Form("25-34"),
    audience_region: str = Form(""),
    audience_income: str = Form(""),
    audience_occupation: str = Form(""),
):
    try:
        logger.info(f"📥 v6.1 Analysis — industry={industry}, platform={platform}")

        if ai_engine is None:
            raise HTTPException(status_code=503, detail="AI Engine not available")

        content = video_script if video_script and video_script.strip() else ad_copy
        if not content or not content.strip():
            raise HTTPException(status_code=400, detail="No content provided")

        # Resolve industry config once — used by every generator
        ind = _resolve_industry(industry)

        request_data = {
            "ad_copy": ad_copy or "",
            "video_script": video_script or "",
            "platform": platform,
            "industry": industry,
            "audience_country": audience_country,
            "audience_age": audience_age,
        }

        # ── AI call ────────────────────────────────────
        logger.info("🤖 Calling AI engine...")
        ai_result = {}
        try:
            ai_result = await ai_engine.analyze_ad(request_data, [])
            logger.info(f"✅ AI returned keys: {list(ai_result.keys())}")
        except Exception as e:
            logger.warning(f"⚠️ AI engine failed ({e}) — using generated data only")

        # ── Scores ─────────────────────────────────────
        scores = ai_result.get("scores", {})
        defaults = {
            "overall": 50, "hook_strength": 50, "clarity": 50, "credibility": 50,
            "emotional_pull": 50, "cta_strength": 50, "audience_match": 50, "platform_fit": 50,
        }
        for k, v in defaults.items():
            if k not in scores or scores[k] in (None, 0):
                scores[k] = v

        ai_summary = ai_result.get("strategic_summary", "")

        # ── Weaknesses — remap AI format to frontend format ──
        ai_weaknesses = ai_result.get("critical_weaknesses", []) or []
        weaknesses = []
        for w in ai_weaknesses:
            weaknesses.append({
                "severity": w.get("severity", "High"),
                "issue": w.get("issue", "Unknown issue"),
                "impact": w.get("impact", "Reduces ad performance"),
                "fix": w.get("precise_fix") or w.get("fix") or "See analysis above",
            })
        if not weaknesses:
            for imp in gen_improvements(scores, ind):
                weaknesses.append({
                    "severity": imp["priority"],
                    "issue": imp["change"],
                    "impact": imp["expected_impact"],
                    "fix": imp["implementation"],
                })

        # ── Always generate personas from our templates ──
        # (AI persona schema is inconsistent — always use the generator)
        personas = gen_persona_reactions(scores, content, ind)

        # ── Assemble complete response ──────────────────
        complete = {
            "scores": scores,

            # Overview
            "behavior_summary": gen_behavior_summary(scores, ai_summary),
            "critical_weaknesses": weaknesses,
            "improvements": gen_improvements(scores, ind),

            # Decision
            "decision_engine": gen_decision_engine(scores, ai_summary),

            # Budget
            "budget_optimization": gen_budget_optimization(scores),

            # Neuro
            "neuro_response": gen_neuro_response(scores, content, ind),

            # Variants
            "ad_variants": gen_ad_variants(content, scores, ind),
            "winner_prediction": gen_winner_prediction(scores, ind),

            # Objections
            "objection_detection": gen_objection_detection(scores, content, ind),

            # Fatigue
            "creative_fatigue": gen_creative_fatigue(scores),

            # Cross-platform
            "cross_platform": gen_cross_platform(scores, content),

            # Video
            "video_execution_analysis": gen_video_execution(scores, content),

            # Personas
            "persona_reactions": personas,

            # Analysis
            "line_by_line_analysis": gen_line_by_line(content, scores),
            "phase_breakdown": gen_phase_breakdown(content, scores),

            # Comparison
            "roi_comparison": gen_roi_comparison(scores),
            "competitor_advantage": gen_competitor_advantage(scores, content, ind),

            "_metadata": {
                "version": "6.1",
                "industry_resolved": ind["label"],
                "content_words": len(content.split()),
            },
        }

        logger.info(f"✅ v6.1 response built — industry: {ind['label']}")
        return {"success": True, "data": complete}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Unhandled error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Auxiliary endpoints ────────────────────────────────────────────────────

@router.get("/audience-config")
async def get_audience_config():
    return {"success": True, "data": {
        "countries": [
            {"code": "nigeria", "name": "Nigeria", "currency": "₦"},
            {"code": "ghana", "name": "Ghana", "currency": "GH₵"},
            {"code": "uk", "name": "United Kingdom", "currency": "£"},
            {"code": "us", "name": "United States", "currency": "$"},
        ]
    }}

@router.get("/platforms")
async def get_platforms():
    return {"success": True, "data": {
        "platforms": [
            {"id": "tiktok", "name": "TikTok"},
            {"id": "instagram", "name": "Instagram"},
            {"id": "facebook", "name": "Facebook"},
            {"id": "youtube", "name": "YouTube"},
        ]
    }}

@router.get("/industries")
async def get_industries():
    return {"success": True, "data": {
        "industries": [
            {"id": "finance", "name": "Finance / Forex"},
            {"id": "realestate", "name": "Real Estate"},
            {"id": "ecommerce", "name": "E-commerce"},
            {"id": "saas", "name": "SaaS / Tech"},
            {"id": "health", "name": "Health / Fitness"},
        ]
    }}
