import logging
import os
from typing import Optional, Dict, Any

from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from backend.services.ai_engine import AIEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["analyze"])

# Constants for available options
PLATFORMS = ["facebook", "tiktok", "instagram", "youtube", "google"]
INDUSTRIES = ["finance", "forex", "crypto", "real_estate", "ecommerce", "saas", "health", "education", "fashion", "food", "tech", "other"]


@router.get("/platforms")
async def get_platforms():
    """Get list of available ad platforms."""
    return {"success": True, "platforms": PLATFORMS}


@router.get("/industries")
async def get_industries():
    """Get list of available industries."""
    return {"success": True, "industries": INDUSTRIES}


@router.post("")
async def analyze_ad(
    ad_copy: str = Form(..., description="The ad text to analyze"),
    video_script: Optional[str] = Form(None),
    platform: str = Form("tiktok"),
    industry: str = Form("finance"),
    objective: str = Form("conversions"),
    audience: Optional[str] = Form(None),
    audience_country: str = Form("nigeria"),
    audience_age: str = Form("25-34"),
    audience_income: str = Form("middle"),
    audience_occupation: Optional[str] = Form(None),
    media_file: Optional[UploadFile] = File(None),
):
    """Analyze ad copy text for performance potential."""
    try:
        logger.info(f"Analyzing ad for platform: {platform}, industry: {industry}")

        if platform not in PLATFORMS:
            raise HTTPException(status_code=400, detail=f"Invalid platform. Must be one of: {', '.join(PLATFORMS)}")

        if industry not in INDUSTRIES:
            raise HTTPException(status_code=400, detail=f"Invalid industry. Must be one of: {', '.join(INDUSTRIES)}")

        if not ad_copy or not ad_copy.strip():
            raise HTTPException(status_code=400, detail="ad_copy is required and cannot be empty")

        request_data = {
            "ad_copy": ad_copy.strip(),
            "platform": platform,
            "industry": industry,
            "objective": objective,
            "audience_country": audience_country,
            "audience_age": audience_age,
            "audience_income": audience_income,
        }

        if video_script and video_script.strip():
            request_data["video_script"] = video_script.strip()
        if audience and audience.strip():
            request_data["audience"] = audience.strip()
        if audience_occupation and audience_occupation.strip():
            request_data["audience_occupation"] = audience_occupation.strip()

        if media_file:
            try:
                media_content = await media_file.read()
                request_data["media_file"] = {
                    "filename": media_file.filename,
                    "content": media_content,
                    "content_type": media_file.content_type
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error processing media file: {str(e)}")

        engine = AIEngine()
        analysis_result = await engine.analyze_ad(request_data)

        return {"success": True, "analysis": analysis_result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing ad: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error analyzing ad: {str(e)}")
