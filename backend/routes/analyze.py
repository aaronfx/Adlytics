"""
ADLYTICS Analysis Route v5.9 - COMPLETE DATA BRIDGE
All tabs populated, no N/A, no empty sections
"""

from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from typing import Optional, List, Dict, Any
import os
import traceback
import logging
import json
import re
from dataclasses import dataclass

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
    ai_engine = None

# Import media processor
try:
    from backend.services.media_processor import process_media
    logger.info("✅ Media processor loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load media processor: {e}")
    async def process_media(file: UploadFile, media_type: str = "image"):
        return {"type": media_type, "filename": file.filename if file else "unknown", "note": "Processing not available"}

# Import complete data bridge
try:
    from backend.services.data_bridge_complete import ensure_complete_response
    logger.info("✅ Complete data bridge loaded")
except ImportError:
    logger.warning("⚠️ Data bridge not found, using inline version")
    # Inline minimal version if import fails
    def ensure_complete_response(analysis, content, scores):
        if "strategic_summary" not in analysis or not analysis["strategic_summary"]:
            analysis["strategic_summary"] = f"Analysis complete. Overall score: {scores.get('overall', 0)}/100"
        return analysis

# ============================================================================
# CONTENT METRICS & VALIDATION
# ============================================================================

@dataclass
class ContentMetrics:
    word_count: int
    max_score: int
    content_type: str
    hook_source: str
    primary_content: str

SCAM_PATTERNS = [
    r"turn\s*\d+\s*(k|000)?\s*(into|to)\s*\d+",
    r"\d+\s*days?",
    r"no\s*experience\s*needed",
    r"guarantee\d*%?",
]

def calculate_metrics(ad_copy: Optional[str], video_script: Optional[str]) -> ContentMetrics:
    """Calculate content metrics"""
    if video_script and ad_copy:
        primary = f"{ad_copy}

{video_script}"
        content_type = "both"
        hook_source = "video_script" if len(video_script) > len(ad_copy) else "ad_copy"
    elif video_script:
        primary = video_script
        content_type = "video_script"
        hook_source = "video_script"
    elif ad_copy:
        primary = ad_copy
        content_type = "ad_copy"
        hook_source = "ad_copy"
    else:
        primary = ""
        content_type = "empty"
        hook_source = "none"

    words = len(primary.split())
    max_score = 10 if words < 5 else 25 if words < 15 else 50 if words < 30 else 75 if words < 50 else 100

    return ContentMetrics(words, max_score, content_type, hook_source, primary)

def detect_scam(content: str) -> tuple:
    """Detect scam patterns"""
    content_lower = content.lower()
    detected = []
    for pattern in SCAM_PATTERNS:
        if re.search(pattern, content_lower):
            detected.append(pattern)
    return len(detected) > 0, detected

# ============================================================================
# MAIN ENDPOINT
# ============================================================================

@router.post("/analyze")
async def analyze_endpoint(
    ad_copy: Optional[str] = Form(None),
    video_script: Optional[str] = Form(None),
    platform: str = Form(...),
    industry: str = Form(...),
    objective: str = Form("conversions"),
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
    image: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None)
):
    """
    Main analysis endpoint - v5.9 Complete Data Bridge
    Ensures ALL frontend tabs have data
    """

    try:
        logger.info("📥 V5.9 Analysis Request - Complete Bridge")

        if ai_engine is None:
            raise HTTPException(status_code=503, detail="AI Engine not initialized")

        # Calculate metrics
        metrics = calculate_metrics(ad_copy, video_script)
        is_scam, scam_patterns = detect_scam(metrics.primary_content)

        logger.info(f"📊 Content: {metrics.word_count} words, type: {metrics.content_type}")

        if metrics.word_count == 0:
            raise HTTPException(status_code=400, detail="No content provided")

        # Build request
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
            "content_metrics": {
                "word_count": metrics.word_count,
                "content_type": metrics.content_type,
                "hook_source": metrics.hook_source,
                "scam_detected": is_scam
            }
        }

        # Process media
        files = []
        if image:
            try: files.append(await process_media(image, "image"))
            except Exception as e: logger.error(f"Image error: {e}")
        if video:
            try: files.append(await process_media(video, "video"))
            except Exception as e: logger.error(f"Video error: {e}")

        # Run AI analysis
        logger.info("🤖 Running AI analysis...")
        try:
            result = await ai_engine.analyze_ad(request_data, files)

            # Extract scores for data bridge
            scores = result.get("scores", {
                "overall": 50, "hook_strength": 50, "clarity": 50, "credibility": 50,
                "emotional_pull": 50, "cta_strength": 50, "audience_match": 50, "platform_fit": 50
            })

            # CRITICAL: Apply complete data bridge to ensure ALL fields exist
            logger.info("🔧 Applying complete data bridge...")
            result = ensure_complete_response(result, metrics.primary_content, scores)

            # Add metadata
            result["_metadata"] = {
                "version": "5.9",
                "complete_bridge": True,
                "content_metrics": {
                    "word_count": metrics.word_count,
                    "content_type": metrics.content_type,
                    "hook_source": metrics.hook_source
                },
                "scam_check": {"detected": is_scam, "patterns": scam_patterns}
            }

            return {
                "success": True,
                "data": result
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
        logger.error(f"💥 Unexpected error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@router.get("/audience-config")
async def get_audience_config():
    """Return audience targeting configuration"""
    return {
        "success": True,
        "data": {
            "countries": [
                {"code": "nigeria", "name": "Nigeria", "currency": "₦", "regions": ["Lagos", "Abuja", "Kano", "Ibadan", "Port Harcourt"]},
                {"code": "us", "name": "United States", "currency": "$", "regions": ["California", "Texas", "New York"]},
                {"code": "uk", "name": "United Kingdom", "currency": "£", "regions": ["London", "Manchester", "Birmingham"]},
                {"code": "ghana", "name": "Ghana", "currency": "₵", "regions": ["Accra", "Kumasi", "Tamale"]},
                {"code": "kenya", "name": "Kenya", "currency": "KSh", "regions": ["Nairobi", "Mombasa", "Kisumu"]}
            ],
            "age_brackets": [
                {"value": "18-24", "label": "18-24", "traits": "Digital natives, TikTok heavy"},
                {"value": "25-34", "label": "25-34", "traits": "Career focused, mobile-first"},
                {"value": "35-44", "label": "35-44", "traits": "Family oriented, research heavy"},
                {"value": "45-54", "label": "45-54", "traits": "Gen X, skeptical"},
                {"value": "55-64", "label": "55-64", "traits": "Pre-retirement, security focused"},
                {"value": "65+", "label": "65+", "traits": "Seniors, trust critical"}
            ],
            "income_levels": [
                {"value": "low", "label": "Low Income", "description": "< $30k/year - Price sensitive"},
                {"value": "lower-middle", "label": "Lower Middle", "description": "$30k-$50k - Value seekers"},
                {"value": "middle", "label": "Middle Income", "description": "$50k-$75k - Balanced"},
                {"value": "upper-middle", "label": "Upper Middle", "description": "$75k-$100k - Quality focused"},
                {"value": "high", "label": "High Income", "description": "$100k+ - Premium preference"}
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
                {"value": "professional", "label": "Professional/White Collar", "pain_points": "Career growth, work-life balance"},
                {"value": "entrepreneur", "label": "Entrepreneur/Business Owner", "pain_points": "Cash flow, scaling"},
                {"value": "student", "label": "Student", "pain_points": "Financial pressure, career uncertainty"},
                {"value": "retired", "label": "Retired", "pain_points": "Health, fixed income"},
                {"value": "homemaker", "label": "Homemaker", "pain_points": "Time scarcity, financial dependence"},
                {"value": "freelancer", "label": "Freelancer/Creator", "pain_points": "Income inconsistency, client acquisition"},
                {"value": "trades", "label": "Trades/Blue Collar", "pain_points": "Physical demands, job security"},
                {"value": "unemployed", "label": "Unemployed/Looking for Work", "pain_points": "Financial stress, confidence"}
            ],
            "psychographics": [
                {"value": "value-seeker", "label": "Value Seeker", "traits": "Deals, comparisons, ROI focused"},
                {"value": "quality-focused", "label": "Quality Focused", "traits": "Premium, durability, reviews"},
                {"value": "innovator", "label": "Innovator", "traits": "Early adopter, tech forward"},
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
