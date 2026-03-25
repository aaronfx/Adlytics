"""
ADLYTICS Tier 2 Features
- POST /api/compliance          — multi-platform compliance scan
- POST /api/psychographic       — deep audience profiler
- POST /api/storyboard          — video storyboard generator
- GET  /api/benchmarks          — NGX + West Africa market data
- POST /api/ab-result           — store real A/B test result
- GET  /api/ab-results          — retrieve stored A/B results
- POST /api/landing-page        — analyze a landing page URL
- POST /api/generate-variants   — generate content-specific A/B variants
"""
from fastapi import APIRouter, Form, Query, HTTPException
from typing import Optional
import json, httpx, os, logging, re, hashlib
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

# In-memory AB store (replace with DB in production)
_ab_store: list = []


# ══════════════════════════════════════════════════════════════
# COMPLIANCE ENGINE
# ══════════════════════════════════════════════════════════════

PLATFORM_RULES = {
    "tiktok": {
        "name": "TikTok",
        "forbidden_phrases": [
            "guaranteed profit", "no risk", "100% success", "get rich",
            "earn daily", "guaranteed returns", "risk-free investment",
        ],
        "required_disclaimers": {
            "finance": "Trading involves significant risk. Capital at risk.",
            "health":  "Results not typical. Consult a healthcare professional.",
            "realestate": "Subject to availability. Terms & conditions apply.",
        },
        "age_restriction_industries": ["finance", "gambling", "alcohol"],
        "rules": [
            {"id": "tt01", "rule": "No guaranteed financial returns claims", "severity": "critical"},
            {"id": "tt02", "rule": "Health claims must include medical disclaimer", "severity": "high"},
            {"id": "tt03", "rule": "Real estate must include agent/developer disclosure", "severity": "high"},
            {"id": "tt04", "rule": "No misleading before/after health images", "severity": "high"},
            {"id": "tt05", "rule": "Financial promotions require risk warning", "severity": "critical"},
            {"id": "tt06", "rule": "No targeting of minors for finance/health products", "severity": "critical"},
        ],
    },
    "facebook": {
        "name": "Facebook / Meta",
        "forbidden_phrases": [
            "guaranteed income", "work from home guaranteed", "limited time scarcity",
            "secret method", "hack", "loophole",
        ],
        "required_disclaimers": {
            "finance": "Past performance is not indicative of future results. Capital at risk.",
            "health":  "Individual results may vary. This is not medical advice.",
            "realestate": "Subject to availability and survey. T&Cs apply.",
        },
        "age_restriction_industries": ["finance", "gambling", "alcohol", "dating"],
        "rules": [
            {"id": "fb01", "rule": "No personal attribute targeting (health, finance status)", "severity": "critical"},
            {"id": "fb02", "rule": "Before/after health images require approval", "severity": "high"},
            {"id": "fb03", "rule": "Financial services require pre-approval for ads", "severity": "critical"},
            {"id": "fb04", "rule": "No exaggerated earnings claims", "severity": "critical"},
            {"id": "fb05", "rule": "Real estate cannot discriminate by protected characteristics", "severity": "critical"},
            {"id": "fb06", "rule": "Subscription products must show total cost clearly", "severity": "high"},
        ],
    },
    "instagram": {
        "name": "Instagram",
        "forbidden_phrases": [
            "dm for price", "results guaranteed", "quick money",
        ],
        "required_disclaimers": {
            "finance": "#ad or #sponsored required for paid partnerships. Capital at risk.",
            "health":  "Results not typical. #ad if sponsored.",
            "realestate": "Licensed agent required for property ads.",
        },
        "age_restriction_industries": ["finance", "gambling"],
        "rules": [
            {"id": "ig01", "rule": "#ad disclosure required for paid partnerships", "severity": "high"},
            {"id": "ig02", "rule": "No misleading follower count / engagement metrics claims", "severity": "medium"},
            {"id": "ig03", "rule": "Finance content requires risk disclaimer in caption", "severity": "critical"},
            {"id": "ig04", "rule": "Health supplements cannot claim to diagnose/treat disease", "severity": "critical"},
        ],
    },
    "youtube": {
        "name": "YouTube",
        "forbidden_phrases": [
            "subscribe or else", "turn off adblock",
        ],
        "required_disclaimers": {
            "finance": "This video is for educational purposes only. Not financial advice. Capital at risk.",
            "health":  "Consult a healthcare professional before making health decisions.",
        },
        "age_restriction_industries": ["finance"],
        "rules": [
            {"id": "yt01", "rule": "Sponsored content must be disclosed with built-in disclosure tool", "severity": "high"},
            {"id": "yt02", "rule": "Financial advice must include 'not financial advice' disclaimer", "severity": "critical"},
            {"id": "yt03", "rule": "No misleading thumbnails that don't match video content", "severity": "medium"},
            {"id": "yt04", "rule": "Health misinformation policy — no anti-vaccine or dangerous remedy claims", "severity": "critical"},
        ],
    },
    "google": {
        "name": "Google Ads",
        "forbidden_phrases": [
            "guaranteed #1 ranking", "cure", "miracle",
        ],
        "required_disclaimers": {
            "finance": "Risk warning required. FCA / SEC reference number if regulated.",
            "health":  "FDA approval status must be accurate.",
        },
        "age_restriction_industries": ["finance", "gambling", "alcohol"],
        "rules": [
            {"id": "go01", "rule": "Financial products require certification and licensed entity", "severity": "critical"},
            {"id": "go02", "rule": "Healthcare and medicine require pre-approval", "severity": "critical"},
            {"id": "go03", "rule": "Real estate must include all fees and costs", "severity": "high"},
            {"id": "go04", "rule": "No trademark infringement in ad copy or URLs", "severity": "high"},
        ],
    },
}

NIGERIAN_COMPLIANCE = {
    "finance": [
        {"rule": "SEC Nigeria registration or disclaimer required for investment products", "severity": "critical"},
        {"rule": "CBN regulated services must display licence number", "severity": "high"},
        {"rule": "Crypto ads must include 'not backed by CBN' disclaimer", "severity": "critical"},
    ],
    "realestate": [
        {"rule": "LASRERA registration number required for Lagos property ads", "severity": "high"},
        {"rule": "FAAN / FCDA approval required for Abuja property ads", "severity": "high"},
        {"rule": "Off-plan sales must disclose estimated completion date", "severity": "medium"},
    ],
    "health": [
        {"rule": "NAFDAC registration number required for health product claims", "severity": "critical"},
        {"rule": "No claims of treating or curing named diseases without NAFDAC approval", "severity": "critical"},
    ],
}


@router.post("/compliance")
async def check_compliance(
    ad_copy: Optional[str] = Form(None),
    video_script: Optional[str] = Form(None),
    platform: str = Form("tiktok"),
    industry: str = Form("finance"),
    target_country: str = Form("nigeria"),
):
    content = video_script or ad_copy or ""
    if not content.strip():
        raise HTTPException(status_code=400, detail="No content to check")

    content_lower = content.lower()
    platform_key = platform.lower()
    industry_key = industry.lower().replace(" ", "").replace("_", "").replace("-", "")
    if "real" in industry_key:
        industry_key = "realestate"

    rules_db = PLATFORM_RULES.get(platform_key, PLATFORM_RULES["tiktok"])
    violations = []
    risk_level = "Low"

    # 1. Forbidden phrase scan
    for phrase in rules_db.get("forbidden_phrases", []):
        if phrase in content_lower:
            violations.append({
                "rule": f"Forbidden phrase detected: '{phrase}'",
                "severity": "critical",
                "platform": rules_db["name"],
                "fix": f"Remove or replace '{phrase}' — this phrase triggers automatic rejection.",
                "source": "phrase_scan",
            })

    # 2. Platform rule checks
    for rule in rules_db.get("rules", []):
        if "financial" in rule["rule"].lower() and industry_key == "finance":
            violations.append({
                "rule": rule["rule"],
                "severity": rule["severity"],
                "platform": rules_db["name"],
                "fix": "Add required financial risk disclaimer to caption and/or end card.",
                "source": "platform_rules",
            })
            break
        if "health" in rule["rule"].lower() and industry_key == "health":
            violations.append({
                "rule": rule["rule"],
                "severity": rule["severity"],
                "platform": rules_db["name"],
                "fix": "Add 'Results not typical. Consult a healthcare professional.'",
                "source": "platform_rules",
            })
            break
        if "real estate" in rule["rule"].lower() and industry_key == "realestate":
            violations.append({
                "rule": rule["rule"],
                "severity": rule["severity"],
                "platform": rules_db["name"],
                "fix": "Include developer registration number and licensed agent disclosure.",
                "source": "platform_rules",
            })
            break

    # 3. Nigerian-specific rules
    if "nigeria" in target_country.lower():
        nigerian_rules = NIGERIAN_COMPLIANCE.get(industry_key, [])
        for rule in nigerian_rules:
            violations.append({
                "rule": rule["rule"],
                "severity": rule["severity"],
                "platform": "Nigeria (All Platforms)",
                "fix": f"Ensure compliance with Nigerian regulatory body for {industry_key}.",
                "source": "nigerian_compliance",
            })

    # 4. Required disclaimer check
    disclaimer = rules_db.get("required_disclaimers", {}).get(industry_key)
    disclaimer_present = False
    if disclaimer:
        keywords = [w.lower() for w in disclaimer.split()[:3]]
        disclaimer_present = any(kw in content_lower for kw in keywords)
        if not disclaimer_present:
            violations.append({
                "rule": f"Required disclaimer missing for {industry_key}",
                "severity": "high",
                "platform": rules_db["name"],
                "fix": f"Add to caption or end card: '{disclaimer}'",
                "source": "disclaimer_check",
            })

    # 5. Determine overall risk
    if any(v["severity"] == "critical" for v in violations):
        risk_level = "Critical"
    elif any(v["severity"] == "high" for v in violations):
        risk_level = "High"
    elif any(v["severity"] == "medium" for v in violations):
        risk_level = "Medium"

    approval_pct = max(10, 95 - (len(violations) * 15))

    return {
        "success": True,
        "data": {
            "overall_risk": risk_level,
            "approval_likelihood": f"{approval_pct}%",
            "violations": violations,
            "required_disclaimer": disclaimer or "None required for this industry/platform combination.",
            "disclaimer_found": disclaimer_present,
            "violation_count": len(violations),
            "critical_count": sum(1 for v in violations if v["severity"] == "critical"),
            "platform_checked": rules_db["name"],
            "country_checked": target_country,
        },
    }


# ══════════════════════════════════════════════════════════════
# PSYCHOGRAPHIC PROFILER
# ══════════════════════════════════════════════════════════════

@router.post("/psychographic")
async def psychographic_profile(
    niche: str = Form(...),
    country: str = Form("nigeria"),
    age_range: str = Form("25-34"),
    income_level: str = Form("middle"),
    platform: str = Form("tiktok"),
):
    if not OPENROUTER_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    prompt = f"""You are a market research expert specializing in {country} consumer psychology.

Create 5 deep psychographic audience profiles for:
- Niche: {niche}
- Country: {country}
- Age: {age_range}
- Income: {income_level}
- Primary Platform: {platform}

For each profile provide:
1. A specific name, age, city, occupation
2. Their deepest fear related to {niche}
3. Their ultimate dream outcome
4. Top 3 objections to buying
5. The exact words they use to describe their problem (in their own language/slang)
6. The ONE thing that would make them buy instantly
7. Platforms they trust most for this type of decision
8. Estimated willingness to pay (₦ range)

Be specific to {country} culture, not generic. Reference real places, real concerns, real language.

OUTPUT ONLY valid JSON. No markdown, no preamble.

{{
  "profiles": [
    {{
      "name": "...",
      "age": 0,
      "city": "...",
      "occupation": "...",
      "deepest_fear": "...",
      "dream_outcome": "...",
      "top_objections": ["...", "...", "..."],
      "their_exact_words": "Quote how they'd describe their problem in their own voice",
      "instant_buy_trigger": "...",
      "trusted_platforms": ["..."],
      "willingness_to_pay": "₦X,000 – ₦X,000"
    }}
  ],
  "market_insight": "1-2 sentence summary of this audience segment's shared psychology"
}}"""

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                f"{BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "openai/gpt-4o",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "max_tokens": 3000,
                    "temperature": 0.5,
                },
            )
        resp.raise_for_status()
        raw = re.sub(r"```json|```", "", resp.json()["choices"][0]["message"]["content"]).strip()
        data = json.loads(raw)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Psychographic AI error: {e}")

    return {"success": True, "data": data}


# ══════════════════════════════════════════════════════════════
# VIDEO STORYBOARD GENERATOR
# ══════════════════════════════════════════════════════════════

@router.post("/storyboard")
async def generate_storyboard(
    script: str = Form(...),
    platform: str = Form("tiktok"),
    style: str = Form("ugc"),   # ugc | talking_head | broll | animation
    duration_seconds: int = Form(30),
):
    if not script.strip():
        raise HTTPException(status_code=400, detail="No script provided")
    if not OPENROUTER_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    prompt = f"""You are a professional video director specializing in {platform} ads.

Script to storyboard:
---
{script}
---

Video specs:
- Platform: {platform}
- Style: {style}
- Target duration: {duration_seconds} seconds

Create a professional shot-by-shot storyboard. For each shot provide:
- Timecode
- Shot type (close-up, wide, medium, POV, screen recording, text overlay, etc.)
- What is happening visually on screen
- What is being said (exact script segment)
- On-screen text / graphics to display
- B-roll suggestions (if any)
- Directorial note (tone, energy, pacing)

OUTPUT ONLY valid JSON. No markdown, no preamble.

{{
  "total_shots": 0,
  "estimated_duration": "Xs",
  "opening_direction": "Overall tone and energy directive for the shoot",
  "shots": [
    {{
      "shot_number": 1,
      "timecode": "0:00–0:03",
      "shot_type": "...",
      "visual_description": "Exactly what the viewer sees",
      "script_line": "Exact words spoken",
      "on_screen_text": "Text overlay or caption to show (or null)",
      "broll": "B-roll suggestion or null",
      "director_note": "Tone / energy note for the creator"
    }}
  ],
  "equipment_needed": ["..."],
  "editing_notes": "Post-production guidance",
  "caption_strategy": "How to write the caption for {platform}"
}}"""

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                f"{BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "openai/gpt-4o",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "max_tokens": 3000,
                    "temperature": 0.4,
                },
            )
        resp.raise_for_status()
        raw = re.sub(r"```json|```", "", resp.json()["choices"][0]["message"]["content"]).strip()
        data = json.loads(raw)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Storyboard AI error: {e}")

    return {"success": True, "data": data}


# ══════════════════════════════════════════════════════════════
# NGX MARKET BENCHMARKS
# ══════════════════════════════════════════════════════════════

BENCHMARKS = {
    "nigeria": {
        "finance": {
            "avg_ctr":         "2.1%",
            "avg_cpm":         "₦1,200",
            "avg_cpa":         "₦4,500",
            "avg_roas":        "1.8×",
            "top_performer_roas": "4.2×",
            "hook_stop_rate":  "31%",
            "avg_watch_time":  "8.4s",
            "best_day":        "Tuesday",
            "best_time":       "7–9pm WAT",
            "audience_size_estimate": "2.1M (finance interest, NG, 22–45)",
            "notes": "Forex content peaks Monday and Tuesday evenings. Vulnerability hooks outperform 3× vs generic tips content.",
        },
        "realestate": {
            "avg_ctr":         "1.4%",
            "avg_cpm":         "₦950",
            "avg_cpa":         "₦12,000",
            "avg_roas":        "2.3×",
            "top_performer_roas": "5.1×",
            "hook_stop_rate":  "24%",
            "avg_watch_time":  "11.2s",
            "best_day":        "Saturday",
            "best_time":       "10am–12pm WAT",
            "audience_size_estimate": "800K (property, Lagos + Abuja, 28–55)",
            "notes": "Saturday morning is peak browsing for property. Title/C of O mentions in first 3s increase CTR by 42%.",
        },
        "ecommerce": {
            "avg_ctr":         "3.2%",
            "avg_cpm":         "₦700",
            "avg_cpa":         "₦2,200",
            "avg_roas":        "2.9×",
            "top_performer_roas": "6.0×",
            "hook_stop_rate":  "38%",
            "avg_watch_time":  "6.1s",
            "best_day":        "Friday",
            "best_time":       "6–10pm WAT",
            "audience_size_estimate": "5.4M (online shoppers, NG, 18–45)",
            "notes": "Product reveals within first 2s outperform story-first by 2.1×. Price transparency increases CVR 35%.",
        },
        "health": {
            "avg_ctr":         "1.9%",
            "avg_cpm":         "₦850",
            "avg_cpa":         "₦3,800",
            "avg_roas":        "2.1×",
            "top_performer_roas": "4.8×",
            "hook_stop_rate":  "29%",
            "avg_watch_time":  "9.8s",
            "best_day":        "Sunday",
            "best_time":       "8–10am WAT",
            "audience_size_estimate": "1.8M (health/fitness, NG, 25–45)",
            "notes": "Before/after with dates and specific measurements outperform generic results by 3.7×.",
        },
        "saas": {
            "avg_ctr":         "0.9%",
            "avg_cpm":         "₦1,600",
            "avg_cpa":         "₦8,500",
            "avg_roas":        "3.5×",
            "top_performer_roas": "7.2×",
            "hook_stop_rate":  "18%",
            "avg_watch_time":  "14.2s",
            "best_day":        "Wednesday",
            "best_time":       "9–11am WAT",
            "audience_size_estimate": "280K (tech decision makers, NG, 28–50)",
            "notes": "Specific time-saved metrics ('saved 11 hours/week') outperform feature lists by 4×.",
        },
    },
    "ghana": {
        "finance": {
            "avg_ctr": "1.7%", "avg_cpm": "GH₵ 8.50", "avg_cpa": "GH₵ 32",
            "avg_roas": "1.5×", "top_performer_roas": "3.8×",
            "notes": "Similar patterns to Nigeria but smaller audience. Cedi reference builds local trust.",
        },
    },
}


@router.get("/benchmarks")
async def get_benchmarks(
    country:  str = Query("nigeria"),
    industry: str = Query("finance"),
):
    country_key  = country.lower()
    industry_key = industry.lower().replace(" ", "").replace("_", "")
    if "real" in industry_key:
        industry_key = "realestate"

    country_data = BENCHMARKS.get(country_key)
    if not country_data:
        return {"success": False, "error": f"No benchmark data for {country}"}

    industry_data = country_data.get(industry_key)
    if not industry_data:
        return {"success": False, "error": f"No benchmark data for {industry} in {country}"}

    return {
        "success": True,
        "data": {
            "country":  country_key,
            "industry": industry_key,
            "benchmarks": industry_data,
            "available_countries":  list(BENCHMARKS.keys()),
            "available_industries": list(BENCHMARKS.get(country_key, {}).keys()),
        },
    }


# ══════════════════════════════════════════════════════════════
# A/B RESULT TRACKER
# ══════════════════════════════════════════════════════════════

@router.post("/ab-result")
async def save_ab_result(
    ad_content:     str = Form(...),
    platform:       str = Form("tiktok"),
    industry:       str = Form("finance"),
    predicted_score: int = Form(50),
    actual_ctr:     Optional[float] = Form(None),
    actual_cpm:     Optional[float] = Form(None),
    actual_cpa:     Optional[float] = Form(None),
    actual_roas:    Optional[float] = Form(None),
    spend_amount:   Optional[float] = Form(None),
    result_label:   Optional[str] = Form(None),   # "winner" | "loser" | "testing"
    notes:          Optional[str] = Form(None),
):
    entry = {
        "id":              hashlib.md5(f"{ad_content}{datetime.now().isoformat()}".encode()).hexdigest()[:10],
        "created_at":      datetime.now().isoformat(),
        "platform":        platform,
        "industry":        industry,
        "ad_snippet":      ad_content[:100] + ("..." if len(ad_content) > 100 else ""),
        "predicted_score": predicted_score,
        "actual_ctr":      actual_ctr,
        "actual_cpm":      actual_cpm,
        "actual_cpa":      actual_cpa,
        "actual_roas":     actual_roas,
        "spend_amount":    spend_amount,
        "result_label":    result_label or "testing",
        "notes":           notes,
        "prediction_accuracy": None,
    }

    # Calculate prediction accuracy if we have ROAS
    if actual_roas is not None:
        expected_roas = predicted_score / 35
        accuracy_delta = abs(actual_roas - expected_roas)
        entry["prediction_accuracy"] = "high" if accuracy_delta < 0.5 else "medium" if accuracy_delta < 1.5 else "low"

    _ab_store.append(entry)
    logger.info(f"📊 AB result saved: id={entry['id']}, score={predicted_score}, roas={actual_roas}")

    return {"success": True, "data": {"saved": True, "entry_id": entry["id"], "total_stored": len(_ab_store)}}


@router.get("/ab-results")
async def get_ab_results(
    platform: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    limit:    int = Query(50, ge=1, le=200),
):
    results = list(reversed(_ab_store))   # newest first

    if platform:
        results = [r for r in results if r["platform"] == platform.lower()]
    if industry:
        results = [r for r in results if r["industry"] == industry.lower()]

    results = results[:limit]

    with_roas = [r for r in results if r["actual_roas"] is not None]
    avg_roas = round(sum(r["actual_roas"] for r in with_roas) / len(with_roas), 2) if with_roas else None

    score_vs_roas = [
        {"score": r["predicted_score"], "roas": r["actual_roas"]}
        for r in with_roas
    ]

    return {
        "success": True,
        "data": {
            "results": results,
            "total": len(results),
            "stats": {
                "entries_with_roas": len(with_roas),
                "avg_actual_roas":   avg_roas,
                "winners":           sum(1 for r in results if r["result_label"] == "winner"),
                "losers":            sum(1 for r in results if r["result_label"] == "loser"),
                "testing":           sum(1 for r in results if r["result_label"] == "testing"),
                "score_vs_roas":     score_vs_roas,
            },
        },
    }


# ══════════════════════════════════════════════════════════════
# LANDING PAGE ANALYZER
# ══════════════════════════════════════════════════════════════

@router.post("/landing-page")
async def analyze_landing_page(
    url: str = Form(...),
    industry: str = Form("finance"),
    audience_country: str = Form("nigeria"),
):
    if not url.strip():
        raise HTTPException(status_code=400, detail="URL required")
    if not url.startswith("http"):
        url = "https://" + url
    if not OPENROUTER_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    # Fetch page content
    html_content = ""
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "ADLYTICS/1.0 (analysis bot)"})
            resp.raise_for_status()
            html_content = resp.text[:8000]
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not fetch page: {e}")

    # Strip tags for text extraction
    text_content = re.sub(r"<[^>]+>", " ", html_content)
    text_content = re.sub(r"\s+", " ", text_content).strip()[:3000]

    prompt = f"""You are a conversion rate optimization expert analyzing a landing page.

URL: {url}
Industry: {industry}
Target Audience Country: {audience_country}

PAGE CONTENT (extracted):
---
{text_content}
---

Analyze this landing page for ad-to-page congruence and conversion effectiveness.

OUTPUT ONLY valid JSON. No markdown, no preamble.

{{
  "headline_score": 0,
  "headline_text": "Extracted headline text",
  "cta_score": 0,
  "cta_text": "Extracted CTA button text",
  "above_fold_score": 0,
  "trust_signal_score": 0,
  "ad_congruence_score": 0,
  "overall_score": 0,
  "trust_signals_found": ["e.g. testimonials", "security badges"],
  "trust_signals_missing": ["e.g. no refund policy", "no contact info"],
  "conversion_blockers": [
    {{"issue": "...", "severity": "high|medium|low", "fix": "..."}}
  ],
  "headline_verdict": "Is the headline strong enough to retain ad traffic?",
  "cta_verdict": "Is the CTA specific and friction-free?",
  "congruence_verdict": "Does the page match what the ad promises?",
  "quick_wins": ["3 specific changes to implement in under 24 hours"]
}}"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "openai/gpt-4o",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "max_tokens": 2000,
                    "temperature": 0.3,
                },
            )
        resp.raise_for_status()
        raw = re.sub(r"```json|```", "", resp.json()["choices"][0]["message"]["content"]).strip()
        data = json.loads(raw)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Landing page AI error: {e}")

    data["url_analyzed"] = url
    return {"success": True, "data": data}


# ══════════════════════════════════════════════════════════════
# GENERATE VARIANTS
# ══════════════════════════════════════════════════════════════

# Country currency + CTA style lookup
_COUNTRY_PROFILES = {
    "nigeria":      {"currency": "₦",   "cta_style": "DM 'INFO' or Comment below"},
    "ghana":        {"currency": "GH₵", "cta_style": "DM or WhatsApp"},
    "kenya":        {"currency": "KSh", "cta_style": "DM or Comment"},
    "south_africa": {"currency": "R",   "cta_style": "Click the link or DM"},
    "uk":           {"currency": "£",   "cta_style": "Click the link below"},
    "us":           {"currency": "$",   "cta_style": "Click the link or DM"},
    "canada":       {"currency": "CA$", "cta_style": "Click the link below"},
    "australia":    {"currency": "A$",  "cta_style": "Click the link or DM"},
    "india":        {"currency": "₹",   "cta_style": "DM or WhatsApp"},
    "germany":      {"currency": "€",   "cta_style": "Click the link below"},
}

def _resolve_profile(country: str) -> dict:
    c = country.lower()
    return (
        _COUNTRY_PROFILES.get(c)
        or next((v for k, v in _COUNTRY_PROFILES.items() if k in c), None)
        or {"currency": "$", "cta_style": "Click or DM"}
    )


@router.post("/generate-variants")
async def generate_variants(
    ad_copy:          str   = Form(...),
    platform:         str   = Form("tiktok"),
    industry:         str   = Form("finance"),
    audience_country: str   = Form("nigeria"),
    overall_score:    str   = Form("50"),
    currency_symbol:  str   = Form(""),
    current_scores:   str   = Form("{}"),
):
    """
    Generate 3 content-specific A/B variants for the submitted ad copy.
    Called by the "Regenerate Variants" button in the frontend.
    """
    if not ad_copy.strip():
        raise HTTPException(status_code=422, detail="ad_copy is required")
    if not OPENROUTER_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    # Resolve context
    profile   = _resolve_profile(audience_country)
    currency  = currency_symbol.strip() or profile["currency"]
    cta_style = profile["cta_style"]
    score     = int(overall_score) if overall_score.isdigit() else 50

    platform_clean  = platform.strip().lower()
    industry_clean  = industry.strip().lower()
    country_clean   = audience_country.strip().lower()

    prompt = f"""You are an expert performance marketing copywriter specialising in {country_clean.upper()} {industry_clean} ads on {platform_clean.upper()}.

The advertiser submitted this ad (overall score: {score}/100):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{ad_copy.strip()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YOUR TASK: Write 3 A/B test variants completely derived from the ad above.

STRICT RULES — follow every rule before writing:
1. Every hook MUST reference the specific product, service, topic, or mechanism in the ad above.
2. Do NOT use generic hooks (e.g. "I lost {currency}120,000") unless the ad literally mentions that loss.
3. Do NOT write "Nobody shows you the losing trades" unless the ad specifically covers trade transparency.
4. Each variant body must expand on what THIS ad is actually offering — not a generic industry pitch.
5. Use {currency} for any currency amounts.
6. CTAs must suit {platform_clean.upper()} — preferred style: {cta_style}
7. Score guidance: Fear/Loss angle typically adds 10–15 pts; Curiosity Gap 7–12; Social Proof 4–9.
8. winner_prediction reasoning must explain why that angle wins FOR THIS specific ad and {country_clean} audience.

OUTPUT STRICT JSON ONLY — no markdown, no preamble:
{{
  "variants": [
    {{
      "id": 1,
      "angle": "Fear / Loss",
      "predicted_score": {min(98, score + 13)},
      "hook": "fear/loss opening derived from THIS ad's specific topic/product",
      "body": "2–3 sentences expanding the problem then pivoting to THIS ad's actual solution",
      "cta": "{platform_clean} CTA",
      "why_it_works": "why fear/loss works for {country_clean} {industry_clean} audience with THIS content"
    }},
    {{
      "id": 2,
      "angle": "Curiosity Gap",
      "predicted_score": {min(98, score + 9)},
      "hook": "open-loop hook withholding a key insight from THIS ad's topic",
      "body": "deepen curiosity, hint at the mechanism THIS ad offers",
      "cta": "CTA that resolves the loop",
      "why_it_works": "why curiosity gap converts for this specific content and audience"
    }},
    {{
      "id": 3,
      "angle": "Social Proof",
      "predicted_score": {min(98, score + 6)},
      "hook": "result/transformation hook specific to THIS ad's core promise",
      "body": "credibility with specifics — numbers, timeframes, outcomes from THIS topic",
      "cta": "trust-building {platform_clean} CTA",
      "why_it_works": "why proof-first converts for {country_clean} {industry_clean} with this content"
    }}
  ],
  "winner_prediction": {{
    "winner_id": 1,
    "angle": "Fear / Loss",
    "confidence": "65%",
    "reasoning": "why this angle beats the others for THIS ad, THIS audience, and {platform_clean.upper()}"
  }}
}}"""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_KEY}",
                    "Content-Type":  "application/json",
                    "HTTP-Referer":  "https://adlytics.ai",
                },
                json={
                    "model":           "openai/gpt-4o",
                    "messages":        [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "max_tokens":      1800,
                    "temperature":     0.3,
                },
            )
        resp.raise_for_status()
        raw     = resp.json()["choices"][0]["message"]["content"]
        clean   = re.sub(r"```json|```", "", raw).strip()
        parsed  = json.loads(clean)

    except json.JSONDecodeError as e:
        logger.error(f"❌ generate-variants JSON parse error: {e}")
        raise HTTPException(status_code=500, detail="AI returned malformed JSON — try again")
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ generate-variants OpenRouter error: {e.response.status_code}")
        raise HTTPException(status_code=502, detail=f"AI API error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"❌ generate-variants unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    variants = parsed.get("variants", [])
    winner   = parsed.get("winner_prediction", {})

    if not variants:
        raise HTTPException(status_code=500, detail="AI returned no variants — try again")

    logger.info(
        f"✅ generate-variants: {len(variants)} variants | "
        f"{industry_clean}/{platform_clean}/{country_clean} | score={score}"
    )

    return {
        "success": True,
        "data": {
            "variants":          variants,
            "winner_prediction": winner,
            "context": {
                "platform": platform_clean,
                "industry": industry_clean,
                "country":  country_clean,
                "score":    score,
            },
        },
    }
