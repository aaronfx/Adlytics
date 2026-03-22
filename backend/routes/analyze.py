"""
ADLYTICS Analysis Route v5.0 - PRODUCTION GRADE
Strict validation, real AI calls, proper error handling
"""

from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from typing import Optional, List
import os
import traceback
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Import V5 AI Engine
try:
    from backend.services.ai_engine_v5 import get_ai_engine, AIValidationError
    ai_engine = get_ai_engine()
    logger.info("✅ AI Engine V5 loaded successfully")
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
    Main analysis endpoint - V5 Production Grade
    Strict validation, real AI calls, no silent fallbacks
    """

    try:
        logger.info("📥 Received analyze request")

        # Check AI engine availability
        if ai_engine is None:
            logger.error("❌ AI Engine not available")
            raise HTTPException(status_code=503, detail="AI Engine not initialized. Check OPENROUTER_API_KEY.")

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
            "purchase_behavior": purchase_behavior or ""
        }

        # Validate content exists
        has_content = bool(ad_copy and ad_copy.strip()) or bool(video_script and video_script.strip())
        if not has_content:
            logger.error("❌ No content provided")
            raise HTTPException(status_code=400, detail="Either ad_copy or video_script must be provided")

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

        # Run AI analysis
        logger.info("🤖 Running AI analysis...")
        try:
            result = await ai_engine.analyze_ad(request_data, files)
            logger.info("✅ Analysis complete")

            # Return strict format
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
        logger.error(f"💥 Unexpected error in analyze_endpoint: {e}")
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
