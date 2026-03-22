"""
ADLYTICS Analysis Route v5.8 - PRODUCTION GRADE + STRICT SCORING
Strict validation, real AI calls, proper error handling, honest scores
"""

from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from typing import Optional, List, Dict, Any
import os
import traceback
import logging
import json
import re
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Import AI Engine
try:
    from backend.services.ai_engine import get_ai_engine, AIValidationError
    ai_engine = get_ai_engine()
    logger.info("✅ AI Engine loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load AI Engine: {e}")
    logger.error(traceback.format_exc())
    ai_engine = None

# Import media processor
try:
    from backend.services.media_processor import process_media
    logger.info("✅ Media processor loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load media processor: {e}")
    async def process_media(file: UploadFile, media_type: str = "image"):
        return {"type": media_type, "filename": file.filename if file else "unknown", "note": "Processing not available"}

# ============================================================================
# V5.8 STRICT SCORING IMPLEMENTATION
# ============================================================================

@dataclass
class ContentMetrics:
    """Pre-calculated content quality metrics"""
    word_count: int
    max_possible_score: int
    content_quality_flag: Optional[str]
    hook_source: str
    cta_source: str
    primary_content: str
    content_type: str

@dataclass
class ScoringCaps:
    """Enforced score caps based on content quality"""
    overall_cap: int
    hook_cap: int
    cta_cap: int
    scam_detected: bool
    scam_patterns_found: List[str]

# Scam pattern detection
SCAM_PATTERNS = [
    r"turn\s*\d+\s*(k|000)?\s*(into|to)\s*\d+",
    r"\d+\s*days?",
    r"no\s*experience\s*needed",
    r"guarantee\d*%?",
    r"risk[-\s]?free",
    r"make\s*\d+\s*daily",
    r"quit\s*your\s*job",
    r"financial\s*freedom",
    r"\d+x\s*returns?",
    r"secret\s*(system|method)",
]

def calculate_content_metrics(ad_copy: Optional[str], video_script: Optional[str]) -> ContentMetrics:
    """
    V5.8: Pre-calculate objective metrics before AI scoring
    This prevents fake high scores for low-quality content
    """
    # Determine primary content source
    if video_script and ad_copy:
        primary_content = f"{ad_copy}\n\n{video_script}"
        content_type = "both"
        # V5.8 FIX: Video script gets priority for hook/cta if it's the main content
        hook_source = "video_script" if len(video_script) > len(ad_copy) else "ad_copy"
        cta_source = "video_script" if len(video_script) > len(ad_copy) else "ad_copy"
    elif video_script:
        primary_content = video_script
        content_type = "video_script"
        hook_source = "video_script"
        cta_source = "video_script"
    elif ad_copy:
        primary_content = ad_copy
        content_type = "ad_copy"
        hook_source = "ad_copy"
        cta_source = "ad_copy"
    else:
        primary_content = ""
        content_type = "empty"
        hook_source = "none"
        cta_source = "none"

    words = len(primary_content.split())

    # STRICT Content length caps
    if words < 5:
        max_score = 10
        quality_flag = "CRITICAL: Content insufficient (<5 words). Score capped at 10."
    elif words < 15:
        max_score = 25
        quality_flag = "WARNING: Minimal content (15-30 words). Scores capped."
    elif words < 30:
        max_score = 50
        quality_flag = "NOTE: Short content (15-30 words). Hook/CTA heavily weighted."
    elif words < 50:
        max_score = 75
        quality_flag = None
    else:
        max_score = 100
        quality_flag = None

    return ContentMetrics(
        word_count=words,
        max_possible_score=max_score,
        content_quality_flag=quality_flag,
        hook_source=hook_source,
        cta_source=cta_source,
        primary_content=primary_content,
        content_type=content_type
    )

def detect_scam_patterns(content: str) -> ScoringCaps:
    """V5.8: Auto-detect scam language and cap scores"""
    content_lower = content.lower()
    detected = []

    for pattern in SCAM_PATTERNS:
        if re.search(pattern, content_lower):
            detected.append(pattern)

    is_scam = len(detected) > 0

    if is_scam:
        return ScoringCaps(
            overall_cap=20,
            hook_cap=15,
            cta_cap=25,
            scam_detected=True,
            scam_patterns_found=detected
        )
    return ScoringCaps(
        overall_cap=100, hook_cap=100, cta_cap=100,
        scam_detected=False, scam_patterns_found=[]
    )

def enforce_score_caps(analysis: Dict[str, Any], 
                      content_metrics: ContentMetrics,
                      scam_caps: ScoringCaps) -> Dict[str, Any]:
    """
    V5.8: Post-processing - Force scores down if AI was too generous
    This is the "no fake scores" layer
    """
    scores = analysis.get("scores", {})
    original_scores = scores.copy()
    enforcement_notes = []

    # Cap 1: Content length
    if scores.get("overall", 100) > content_metrics.max_possible_score:
        scores["overall"] = content_metrics.max_possible_score
        enforcement_notes.append(f"Overall capped at {content_metrics.max_possible_score} (content length)")

    # Cap 2: Scam patterns
    if scam_caps.scam_detected:
        if scores.get("hook_strength", 100) > scam_caps.hook_cap:
            scores["hook_strength"] = scam_caps.hook_cap
            enforcement_notes.append(f"Hook capped at {scam_caps.hook_cap} (scam pattern)")
        if scores.get("overall", 100) > scam_caps.overall_cap:
            scores["overall"] = scam_caps.overall_cap
            enforcement_notes.append(f"Overall capped at {scam_caps.overall_cap} (scam pattern)")

        # Add scam warning to analysis
        analysis["scam_warning"] = {
            "detected": True,
            "patterns": scam_caps.scam_patterns_found,
            "message": "Content triggers scam detection. Scores heavily penalized."
        }

    # Cap 3: Video script hook validation
    # If video_script is primary but hook scored high on generic filler, penalize
    if content_metrics.hook_source == "video_script":
        hook_text = analysis.get("content_analysis", {}).get("hook_text", "").lower()
        if any(x in hook_text for x in ["wait", "stop", "dont skip", "before you"]) and scores.get("hook_strength", 0) > 60:
            scores["hook_strength"] = 60
            enforcement_notes.append("Hook adjusted (generic filler words)")

    # Cap 4: Empty/short content
    if content_metrics.word_count < 5:
        scores["hook_strength"] = min(scores.get("hook_strength", 0), 5)
        scores["cta_strength"] = min(scores.get("cta_strength", 0), 5)
        enforcement_notes.append("Minimal content - all scores minimized")

    if enforcement_notes:
        analysis["score_enforcement"] = {
            "applied": True,
            "notes": enforcement_notes,
            "original_scores": original_scores,
            "adjusted_scores": scores
        }
        analysis["scores"] = scores

    return analysis

def build_strict_prompt(content_metrics: ContentMetrics, 
                       request_data: Dict[str, Any]) -> str:
    """
    V5.8: Build prompt with strict rubric and content source priority
    """
    country = request_data.get("audience_country", "nigeria")
    platform = request_data.get("platform", "tiktok")

    prompt = f"""You are ADLYTICS v5.8, a ruthless advertising analyst. Tell the brutal truth.

CONTENT TO ANALYZE:
---
{content_metrics.primary_content}
---

CONTENT META:
- Type: {content_metrics.content_type}
- Word Count: {content_metrics.word_count}
- MAXIMUM POSSIBLE SCORE: {content_metrics.max_possible_score}/100 (ENFORCED - cannot exceed)
- Hook Source: {content_metrics.hook_source}
- CTA Source: {content_metrics.cta_source}
- Platform: {platform}
- Target Country: {country}

STRICT SCORING RUBRIC (Most ads score 40-60. Be harsh):

1. hook_strength (0-100) - First 3 seconds ONLY
   90-100: Specific trauma ("I lost ₦120K"), provocation ("Stop"), pattern interrupt
   80-89: Strong curiosity gap
   70-79: Clear but generic
   60-69: Weak, boring, feature-focused
   40-59: Confusing or scam-pattern ("Turn 50K to 500K")
   20-39: No hook, starts with filler
   0-19: Empty or nonsense
   CURRENT MAX: {content_metrics.max_possible_score if content_metrics.word_count < 20 else 100}

2. clarity (0-100) - Can viewer understand in 3 seconds?
   90-100: One sentence explains it
   70-89: Clear after brief attention
   50-69: Confusing value prop
   30-49: Multiple competing ideas
   0-29: Incomprehensible

3. credibility (0-100) - Trust signals
   90-100: Shows losses, specific proof, vulnerability
   70-89: Social proof
   50-69: Claims without proof
   30-49: Hype language only
   0-29: Scam markers

4. emotional_pull (0-100)
   90-100: Specific trauma or deep desire
   70-89: Clear pain point
   50-69: Generic motivation
   30-49: No emotional resonance
   0-29: Off-putting

5. cta_strength (0-100)
   90-100: Anti-CTA ("Don't join yet") or urgent specific action
   70-89: Clear benefit-driven CTA
   50-69: Generic "Click here"
   30-49: Weak or vague
   0-29: No CTA

6. audience_match (0-100) - Fit for {country} market
   90-100: Perfect cultural/linguistic fit
   70-89: Good fit
   50-69: Generic
   30-49: Mismatched
   0-29: Alienating

7. platform_fit (0-100) - Right for {platform}
   90-100: Perfect format
   70-89: Good fit
   50-69: Acceptable
   30-49: Wrong format
   0-29: Will fail

8. overall (0-100)
   Formula: (Hook×0.25 + Credibility×0.25 + Clarity×0.15 + Emotional×0.15 + CTA×0.10 + Audience×0.10)
   HARD RULES:
   - If word count < 10, maximum overall is 15
   - If scam patterns detected, maximum overall is 20
   - If video_script is primary source, score hook/cta from video script

Extract and return:
- hook_text: First 10-15 words (the actual hook used for scoring)
- cta_text: Last 10-15 words (the actual CTA used for scoring)

OUTPUT STRICT JSON:
{{
  "scores": {{
    "overall": 0,
    "hook_strength": 0,
    "clarity": 0,
    "credibility": 0,
    "emotional_pull": 0,
    "cta_strength": 0,
    "audience_match": 0,
    "platform_fit": 0
  }},
  "content_analysis": {{
    "hook_text": "extracted hook",
    "cta_text": "extracted cta",
    "word_count": {content_metrics.word_count},
    "primary_type": "{content_metrics.content_type}",
    "hook_source": "{content_metrics.hook_source}"
  }},
  "strategic_summary": "Detailed explanation of why these scores were given. Be specific about failures.",
  "critical_weaknesses": [
    {{
      "issue": "Specific problem",
      "impact": "What this costs you",
      "precise_fix": "Exactly how to fix it",
      "estimated_lift": "+X%"
    }}
  ],
  "behavioral_prediction": {{
    "micro_stop_rate": "High/Medium/Low",
    "scroll_stop_rate": "High/Medium/Low",
    "click_probability": "High/Medium/Low",
    "verdict": "One sentence brutal truth"
  }}
}}"""
    return prompt

# ============================================================================
# MAIN ENDPOINT
# ============================================================================

@router.post("/analyze")
async def analyze_endpoint(
    # Content fields
    ad_copy: Optional[str] = Form(None),
    video_script: Optional[str] = Form(None),

    # Platform & Industry (required)
    platform: str = Form(...),
    industry: str = Form(...),

    # Campaign objective
    objective: str = Form("conversions"),

    # Audience targeting fields
    audience_country: str = Form(...),
    audience_region: Optional[str] = Form(None),
    audience_age: str = Form(...),
    audience_gender: Optional[str] = Form("all"),
    audience_income: Optional[str] = Form(None),
    audience_education: Optional[str] = Form(None),
    audience_occupation: Optional[str] = Form(None),
    audience_psychographic: Optional[str] = Form(None),
    audience_pain_point: Optional[str] = Form(None),
    tech_savviness: Optional[str] = Form("medium"),
    purchase_behavior: Optional[str] = Form(None),

    # Media files
    image: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None)
):
    """
    Main analysis endpoint - V5.8 with Strict Scoring
    Fixes: Video script hook/cta properly weighted, no fake high scores
    """

    try:
        logger.info("📥 Received analyze request - V5.8 Strict Mode")

        # Check AI engine availability
        if ai_engine is None:
            logger.error("❌ AI Engine not available")
            raise HTTPException(status_code=503, detail="AI Engine not initialized.")

        # V5.8: Calculate content metrics FIRST (before AI call)
        content_metrics = calculate_content_metrics(ad_copy, video_script)
        scam_caps = detect_scam_patterns(content_metrics.primary_content)

        logger.info(f"📊 Content metrics: {content_metrics.word_count} words, "
                   f"max_score: {content_metrics.max_possible_score}, "
                   f"type: {content_metrics.content_type}, "
                   f"scam_detected: {scam_caps.scam_detected}")

        # Validate content exists
        has_content = content_metrics.word_count > 0
        if not has_content:
            logger.error("❌ No content provided")
            raise HTTPException(status_code=400, detail="Either ad_copy or video_script must be provided")

        # Build request data
        request_data = {
            "ad_copy": ad_copy or "",
            "video_script": video_script or "",
            "platform": platform,
            "industry": industry,
            "objective": objective,
            "audience_country": audience_country,
            "audience_region": audience_region or "",
            "audience_age": audience_age,
            "audience_gender": audience_gender or "all",
            "audience_income": audience_income or "",
            "audience_education": audience_education or "",
            "audience_occupation": audience_occupation or "",
            "audience_psychographic": audience_psychographic or "",
            "audience_pain_point": audience_pain_point or "",
            "tech_savviness": tech_savviness or "medium",
            "purchase_behavior": purchase_behavior or "",
            # V5.8 metadata for AI
            "content_metrics": {
                "word_count": content_metrics.word_count,
                "max_possible_score": content_metrics.max_possible_score,
                "content_type": content_metrics.content_type,
                "hook_source": content_metrics.hook_source,
                "cta_source": content_metrics.cta_source
            }
        }

        # Process media files
        files = []
        if image:
            try:
                image_data = await process_media(image, "image")
                files.append(image_data)
                logger.info("✅ Image processed")
            except Exception as e:
                logger.error(f"❌ Error processing image: {e}")

        if video:
            try:
                video_data = await process_media(video, "video")
                files.append(video_data)
                logger.info("✅ Video processed")
            except Exception as e:
                logger.error(f"❌ Error processing video: {e}")

        # V5.8: Build strict prompt
        strict_prompt = build_strict_prompt(content_metrics, request_data)

        # Run AI analysis
        logger.info("🤖 Running AI analysis with strict scoring...")
        try:
            # Check if ai_engine supports custom prompts
            if hasattr(ai_engine, 'analyze_ad_with_prompt'):
                result = await ai_engine.analyze_ad_with_prompt(
                    request_data, 
                    files, 
                    custom_prompt=strict_prompt
                )
            else:
                # Fallback: modify request to include strict context
                result = await ai_engine.analyze_ad(request_data, files)

            logger.info("✅ Analysis complete, applying post-processing...")

            # V5.8: Post-processing enforcement (critical fix)
            result = enforce_score_caps(result, content_metrics, scam_caps)

            # Add V5.8 metadata
            result["analysis_metadata"] = {
                "engine_version": "5.8",
                "strict_scoring": True,
                "content_metrics": {
                    "word_count": content_metrics.word_count,
                    "max_possible_score": content_metrics.max_possible_score,
                    "content_type": content_metrics.content_type,
                    "hook_source": content_metrics.hook_source,
                    "cta_source": content_metrics.cta_source
                },
                "scam_check": {
                    "detected": scam_caps.scam_detected,
                    "patterns": scam_caps.scam_patterns_found
                }
            }

            # Return strict format
            return {
                "success": True,
                "data": result,
                "v58_note": "Strict scoring applied - video script hook properly weighted"
            }

        except AIValidationError as e:
            logger.error(f"❌ AI Validation Error: {e}")
            raise HTTPException(status_code=502, detail=f"AI Analysis failed: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Analysis error: {e}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Unexpected error in analyze_endpoint: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

# Keep all your existing endpoints (audience-config, platforms, industries) exactly as they are

@router.get("/audience-config")
async def get_audience_config():
    """Return audience targeting configuration"""
    return {
        "success": True,
        "data": {
            "countries": [
                {"code": "nigeria", "name": "Nigeria", "currency": "₦", "regions": ["Lagos", "Abuja", "Kano", "Ibadan", "Port Harcourt"]},
                {"code": "us", "name": "United States", "currency": "$", "regions": ["California", "Texas", "New York", "Florida", "Illinois"]},
                {"code": "uk", "name": "United Kingdom", "currency": "£", "regions": ["London", "Manchester", "Birmingham"]},
                {"code": "canada", "name": "Canada", "currency": "$", "regions": ["Ontario", "Quebec", "British Columbia"]},
                {"code": "australia", "name": "Australia", "currency": "$", "regions": ["New South Wales", "Victoria", "Queensland"]},
                {"code": "ghana", "name": "Ghana", "currency": "₵", "regions": ["Accra", "Kumasi", "Tamale"]},
                {"code": "kenya", "name": "Kenya", "currency": "KSh", "regions": ["Nairobi", "Mombasa", "Kisumu"]},
                {"code": "south_africa", "name": "South Africa", "currency": "R", "regions": ["Gauteng", "Western Cape", "KwaZulu-Natal"]},
                {"code": "india", "name": "India", "currency": "₹", "regions": ["Maharashtra", "Karnataka", "Delhi"]},
                {"code": "germany", "name": "Germany", "currency": "€", "regions": ["Bavaria", "North Rhine-Westphalia", "Baden-Württemberg"]}
            ],
            "age_brackets": [
                {"value": "18-24", "label": "18-24", "traits": "Digital natives, TikTok heavy, price sensitive"},
                {"value": "25-34", "label": "25-34", "traits": "Career focused, mobile-first, value conscious"},
                {"value": "35-44", "label": "35-44", "traits": "Family oriented, research heavy, quality focused"},
                {"value": "45-54", "label": "45-54", "traits": "Gen X, skeptical, loyalty driven"},
                {"value": "55-64", "label": "55-64", "traits": "Pre-retirement, security focused, slower adoption"},
                {"value": "65+", "label": "65+", "traits": "Seniors, simple UX needed, trust critical"}
            ],
            "income_levels": [
                {"value": "low", "label": "Low Income", "description": "< $30k/year - Price sensitive, deals critical"},
                {"value": "lower-middle", "label": "Lower Middle", "description": "$30k-$50k - Value seekers, budget conscious"},
                {"value": "middle", "label": "Middle Income", "description": "$50k-$75k - Balanced, quality matters"},
                {"value": "upper-middle", "label": "Upper Middle", "description": "$75k-$100k - Quality focused, time poor"},
                {"value": "high", "label": "High Income", "description": "$100k+ - Premium preference, convenience"}
            ],
            "education_levels": [
                {"value": "high-school", "label": "High School"},
                {"value": "some-college", "label": "Some College"},
                {"value": "bachelors", "label": "Bachelor's Degree"},
                {"value": "masters", "label": "Master's Degree"},
                {"value": "doctorate", "label": "Doctorate"},
                {"value": "professional", "label": "Professional Degree"}
            ],
            "occupations": [
                {"value": "professional", "label": "Professional/White Collar", "pain_points": "Career growth, work-life balance, imposter syndrome"},
                {"value": "entrepreneur", "label": "Entrepreneur/Business Owner", "pain_points": "Cash flow, scaling, decision fatigue"},
                {"value": "student", "label": "Student", "pain_points": "Financial pressure, career uncertainty, time management"},
                {"value": "retired", "label": "Retired", "pain_points": "Health, fixed income, legacy planning"},
                {"value": "homemaker", "label": "Homemaker", "pain_points": "Time scarcity, financial dependence, identity"},
                {"value": "freelancer", "label": "Freelancer/Creator", "pain_points": "Income inconsistency, client acquisition, burnout"},
                {"value": "trades", "label": "Trades/Blue Collar", "pain_points": "Physical demands, job security, upskilling"},
                {"value": "unemployed", "label": "Unemployed/Looking for Work", "pain_points": "Financial stress, confidence, skill gaps"}
            ],
            "psychographics": [
                {"value": "value-seeker", "label": "Value Seeker", "traits": "Deals, comparisons, ROI focused"},
                {"value": "quality-focused", "label": "Quality Focused", "traits": "Premium, durability, reviews"},
                {"value": "innovator", "label": "Innovator", "traits": "Early adopter, tech forward, risk taker"},
                {"value": "pragmatist", "label": "Pragmatist", "traits": "Practical, proven, testimonials"},
                {"value": "aspirational", "label": "Aspirational", "traits": "Status, transformation, social proof"}
            ],
            "pain_points": [
                {"value": "saving-time", "label": "Saving Time"},
                {"value": "saving-money", "label": "Saving Money"},
                {"value": "reducing-stress", "label": "Reducing Stress"},
                {"value": "improving-health", "label": "Improving Health"},
                {"value": "growing-income", "label": "Growing Income"},
                {"value": "learning-skills", "label": "Learning New Skills"},
                {"value": "social-status", "label": "Social Status"}
            ]
        }
    }

@router.get("/platforms")
async def get_platforms():
    """Return supported platforms"""
    return {
        "success": True,
        "data": {
            "platforms": [
                {"id": "facebook", "name": "Facebook"},
                {"id": "instagram", "name": "Instagram"},
                {"id": "tiktok", "name": "TikTok"},
                {"id": "youtube", "name": "YouTube"},
                {"id": "google", "name": "Google Ads"},
                {"id": "linkedin", "name": "LinkedIn"},
                {"id": "twitter", "name": "Twitter/X"}
            ]
        }
    }

@router.get("/industries")
async def get_industries():
    """Return supported industries"""
    return {
        "success": True,
        "data": {
            "industries": [
                {"id": "ecommerce", "name": "E-commerce"},
                {"id": "saas", "name": "SaaS"},
                {"id": "finance", "name": "Finance"},
                {"id": "health", "name": "Health"},
                {"id": "education", "name": "Education"},
                {"id": "realestate", "name": "Real Estate"},
                {"id": "travel", "name": "Travel"},
                {"id": "food", "name": "Food & Beverage"},
                {"id": "fashion", "name": "Fashion"},
                {"id": "technology", "name": "Technology"},
                {"id": "consulting", "name": "Consulting"},
                {"id": "other", "name": "Other"}
            ]
        }
    }
