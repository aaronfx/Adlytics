"""
ADLYTICS Analysis Route - DIAGNOSTIC VERSION
Shows exact error details in response
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

# Try to import AI engine with error handling
try:
    from backend.services.ai_engine import get_ai_engine
    ai_engine = get_ai_engine()
    logger.info("✅ AI Engine loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load AI Engine: {e}")
    logger.error(traceback.format_exc())
    ai_engine = None

# Try to import media processor with error handling
try:
    from backend.services.media_processor import process_media
    logger.info("✅ Media processor loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load media processor: {e}")
    logger.error(traceback.format_exc())
    process_media = None


@router.post("/analyze")
async def analyze_endpoint(
    ad_copy: Optional[str] = Form(None),
    video_script: Optional[str] = Form(None),
    platform: str = Form(...),
    audience_country: str = Form(...),
    audience_age: str = Form(...),
    industry: str = Form(...),
    objective: str = Form("conversions"),
    audience_region: Optional[str] = Form(None),
    audience_gender: Optional[str] = Form(None),
    audience_income: Optional[str] = Form(None),
    audience_education: Optional[str] = Form(None),
    audience_occupation: Optional[str] = Form(None),
    audience_psychographic: Optional[str] = Form(None),
    audience_pain_point: Optional[str] = Form(None),
    tech_savviness: Optional[str] = Form(None),
    purchase_behavior: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None)
):
    """
    Main analysis endpoint - DIAGNOSTIC VERSION
    """

    try:
        logger.info("📥 Received analyze request")

        # Check if AI engine loaded
        if ai_engine is None:
            logger.error("❌ AI Engine not available")
            return {
                "success": False,
                "error": "AI Engine failed to load",
                "detail": "Check server logs for import errors"
            }

        # Build request data
        request_data = {
            "ad_copy": ad_copy or "",
            "video_script": video_script or "",
            "platform": platform,
            "audience_country": audience_country,
            "audience_age": audience_age,
            "industry": industry,
            "objective": objective,
            "audience_region": audience_region,
            "audience_gender": audience_gender,
            "audience_income": audience_income,
            "audience_education": audience_education,
            "audience_occupation": audience_occupation,
            "audience_psychographic": audience_psychographic,
            "audience_pain_point": audience_pain_point,
            "tech_savviness": tech_savviness,
            "purchase_behavior": purchase_behavior
        }

        logger.info(f"📊 Request data: {request_data}")

        # Detect content mode
        try:
            content_mode = ai_engine.detect_content_mode(request_data)
            logger.info(f"📋 Content mode: {content_mode}")
        except Exception as e:
            logger.error(f"❌ Error detecting content mode: {e}")
            return {
                "success": False,
                "error": "Failed to detect content mode",
                "detail": str(e),
                "traceback": traceback.format_exc()
            }

        # Validate at least one content type is provided
        if content_mode == "adCopy" and not ad_copy:
            return {
                "success": False,
                "error": "Ad copy is required for ad copy mode"
            }
        if content_mode == "videoScript" and not video_script:
            return {
                "success": False,
                "error": "Video script is required for video script mode"
            }

        # Process media files if provided
        files = []
        if process_media:
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

        # Run analysis
        logger.info("🤖 Running AI analysis...")
        try:
            result = await ai_engine.analyze(request_data, files)
            logger.info("✅ Analysis complete")
            return result
        except Exception as e:
            logger.error(f"❌ Error during analysis: {e}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": "Analysis failed",
                "detail": str(e),
                "traceback": traceback.format_exc()
            }

    except Exception as e:
        logger.error(f"💥 Unexpected error in analyze_endpoint: {e}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": "Unexpected server error",
            "detail": str(e),
            "traceback": traceback.format_exc()
        }


@router.get("/audience-config")
async def get_audience_config():
    """Return audience targeting configuration"""
    return {
        "countries": [
            {"code": "nigeria", "name": "Nigeria", "currency": "₦", "regions": ["Lagos", "Abuja", "Port Harcourt"]},
            {"code": "us", "name": "United States", "currency": "$", "regions": ["New York", "California", "Texas"]},
            {"code": "uk", "name": "United Kingdom", "currency": "£", "regions": ["London", "Manchester"]}
        ],
        "age_brackets": [
            {"value": "18-24", "label": "18-24", "traits": "Digital natives"},
            {"value": "25-34", "label": "25-34", "traits": "Career focused"},
            {"value": "35-44", "label": "35-44", "traits": "Family oriented"}
        ],
        "income_levels": [
            {"value": "low", "label": "Low Income"},
            {"value": "middle", "label": "Middle Income"},
            {"value": "high", "label": "High Income"}
        ],
        "education_levels": [
            {"value": "high_school", "label": "High School"},
            {"value": "bachelors", "label": "Bachelor's"},
            {"value": "graduate", "label": "Graduate"}
        ],
        "occupations": [
            {"value": "student", "label": "Student"},
            {"value": "professional", "label": "Professional"},
            {"value": "entrepreneur", "label": "Entrepreneur"}
        ],
        "psychographics": [
            {"value": "value_seeker", "label": "Value Seeker"},
            {"value": "quality_focused", "label": "Quality Focused"}
        ],
        "pain_points": [
            {"value": "financial_stress", "label": "Financial Stress"},
            {"value": "time_scarcity", "label": "Time Scarcity"}
        ]
    }


@router.get("/platforms")
async def get_platforms():
    """Return supported platforms"""
    return {
        "platforms": [
            {"id": "facebook", "name": "Facebook"},
            {"id": "instagram", "name": "Instagram"},
            {"id": "tiktok", "name": "TikTok"},
            {"id": "google", "name": "Google Ads"},
            {"id": "linkedin", "name": "LinkedIn"}
        ]
    }


@router.get("/industries")
async def get_industries():
    """Return supported industries"""
    return {
        "industries": [
            {"id": "ecommerce", "name": "E-commerce"},
            {"id": "saas", "name": "SaaS"},
            {"id": "finance", "name": "Finance"},
            {"id": "health", "name": "Health"},
            {"id": "education", "name": "Education"}
        ]
    }
