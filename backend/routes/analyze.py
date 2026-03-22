"""
ADLYTICS Analysis Route v5.9
Strict validation, real AI calls, no fake scores
"""

from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from typing import Optional, List, Dict, Any
import os
import traceback
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Import AI Engine
try:
    from backend.services.ai_engine import get_ai_engine, AIValidationError
    ai_engine = get_ai_engine()
    logger.info("✅ AI Engine v5.9 loaded successfully")
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
    Main analysis endpoint - V5.9 Real Scoring
    """

    try:
        logger.info("📥 Received analyze request - V5.9")

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

        # Run AI analysis - V5.9
        logger.info("🤖 Running AI analysis (v5.9)...")
        try:
            result = await ai_engine.analyze_ad(request_data, files)
            logger.info("✅ Analysis complete")

            # Return strict format
            return {
                "success": True,
                "data": result,
                "version": "5.9"
            }

        except AIValidationError as e:
            logger.error(f"❌ AI Validation Error: {e}")
            raise HTTPException(status_code=502, detail=f"AI Analysis failed - generic scores detected: {str(e)}")
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
                {"code": "us", "name": "United States", "currency": "$", "regions": ["California", "Texas", "New York"]},
                {"code": "uk", "name": "United Kingdom", "currency": "£", "regions": ["London", "Manchester"]},
                {"code": "ghana", "name": "Ghana", "currency": "₵", "regions": ["Accra", "Kumasi"]},
                {"code": "kenya", "name": "Kenya", "currency": "KSh", "regions": ["Nairobi", "Mombasa"]}
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
                {"id": "youtube", "name": "YouTube"}
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
                {"id": "finance", "name": "Finance"}
            ]
        }
    }
